#!/usr/bin/env python3
"""
stress_test_math_logic.py
Teste adversarial e stress-test dos scripts da skill csbot-math-logic-auditor.
Garante que os scripts NÃO são fachadas e rejeitam ativamente violações reais.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_SCRIPTS = Path(".agents/skills/csbot-math-logic-auditor/scripts").resolve()

def run_script(script_name: str, args: list) -> tuple:
    cmd = [sys.executable, str(SKILL_SCRIPTS / script_name)] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        data = json.loads(res.stdout)
    except Exception:
        data = None
    return res.returncode, data, res.stderr

def main():
    print("Iniciando Adversarial Stress-Testing da Skill csbot-math-logic-auditor...")
    failures = []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Test Case 1: Matriz de confusão normalizada com Support=0 exibindo valor numérico (Violação Regra 03)
        counts_csv = tmppath / "counts.csv"
        counts_csv.write_text("class,c1,c2\nCLASS_A,10,0\nCLASS_B,0,0\n", encoding="utf-8")
        norm_csv = tmppath / "norm_bad.csv"
        norm_csv.write_text("class,c1,c2\nCLASS_A,1.0,0.0\nCLASS_B,0.0,0.0\n", encoding="utf-8") # CLASS_B deveria ser N/A!
        out_json = tmppath / "out1.json"

        code, report, _ = run_script("audit_confusion_and_calibration.py", [
            "--counts", str(counts_csv),
            "--normalized", str(norm_csv),
            "--out", str(out_json),
            "--strict"
        ])
        if code == 0 or report is None or report.get("verdict") != "FAIL":
            failures.append("Falha em detectar valor numérico em support=0 na matriz normalizada")
        else:
            print("  [PASS] Detecção de valor numérico em support=0 na matriz normalizada.")

        # Test Case 2: Matriz normalizada com soma != 1.0
        norm_sum_bad = tmppath / "norm_sum_bad.csv"
        norm_sum_bad.write_text("class,c1,c2\nCLASS_A,0.6,0.2\nCLASS_B,N/A,N/A\n", encoding="utf-8") # soma = 0.8
        out_json2 = tmppath / "out2.json"
        code, report, _ = run_script("audit_confusion_and_calibration.py", [
            "--counts", str(counts_csv),
            "--normalized", str(norm_sum_bad),
            "--out", str(out_json2),
            "--strict"
        ])
        if code == 0 or report is None or report.get("verdict") != "FAIL":
            failures.append("Falha em detectar soma de linha normalizada != 1.0")
        else:
            print("  [PASS] Detecção de soma de linha normalizada != 1.0.")

        # Test Case 3: Métricas JSON com ECE inválido (> 1.0)
        metrics_bad = tmppath / "metrics_bad.json"
        metrics_bad.write_text(json.dumps({"ece": 1.45, "brier": 0.12}), encoding="utf-8")
        out_json3 = tmppath / "out3.json"
        code, report, _ = run_script("audit_confusion_and_calibration.py", [
            "--metrics", str(metrics_bad),
            "--out", str(out_json3),
            "--strict"
        ])
        if code == 0 or report is None or report.get("verdict") != "FAIL":
            failures.append("Falha em detectar ECE > 1.0")
        else:
            print("  [PASS] Detecção de ECE fora do intervalo permitido [0, 1].")

        # Test Case 4: Transições FSM ilegais (SPAWN -> PLANT_C4)
        trans_bad = tmppath / "trans_bad.json"
        trans_bad.write_text(json.dumps([
            {"from_state": "SPAWN", "to_state": "PLANT_C4", "duration_seconds": 1.0}
        ]), encoding="utf-8")
        out_json4 = tmppath / "out4.json"
        code, report, _ = run_script("audit_temporal_transitions.py", [
            "--transitions", str(trans_bad),
            "--out", str(out_json4),
            "--strict"
        ])
        if code == 0 or report is None or report.get("verdict") != "FAIL":
            failures.append("Falha em detectar transição FSM ilegal SPAWN -> PLANT_C4")
        else:
            print("  [PASS] Detecção de transição ilegal FSM SPAWN -> PLANT_C4.")

        # Test Case 5: Duração de Plant_C4 abaixo do mínimo de motor (< 3.0s)
        trans_timing_bad = tmppath / "trans_timing_bad.json"
        trans_timing_bad.write_text(json.dumps([
            {"from_state": "NAVIGATE", "to_state": "PLANT_C4", "duration_seconds": 5.0},
            {"from_state": "PLANT_C4", "to_state": "HOLD_ANGLE", "duration_seconds": 1.2} # plant < 3.0s!
        ]), encoding="utf-8")
        out_json5 = tmppath / "out5.json"
        code, report, _ = run_script("audit_temporal_transitions.py", [
            "--transitions", str(trans_timing_bad),
            "--out", str(out_json5),
            "--strict"
        ])
        if code == 0 or report is None or report.get("verdict") != "FAIL":
            failures.append("Falha em detectar plant com duração < 3.0s")
        else:
            print("  [PASS] Detecção de tempo físico de plant < 3.0s.")

    if failures:
        print(f"\n[FAIL] {len(failures)} falhas no stress-testing: {failures}")
        sys.exit(1)
    else:
        print("\n[CLEAN] Todos os 5 testes adversariais passaram com sucesso! Scripts comprovadamente genuínos e estritos.")

if __name__ == "__main__":
    main()
