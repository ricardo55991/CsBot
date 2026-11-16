import hashlib
import json
from pathlib import Path
from typing import Dict

BASE_DIR = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
LIVE_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "live_capture"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    with open(LIVE_DIR / "smoke_runtime_metrics.json", "r", encoding="utf-8") as f:
        smoke = json.load(f)

    findings = {
        "marco": "2B.6.1",
        "provenance": "REAL_LIVE_CS2_SERVER",
        "decision": "POSITIONING_LIVE_SMOKE_FAILED",
        "full_match_executed": False,
        "findings": [
            "Smoke ao vivo executado em de_mirage (5v5 bots, 4 Hz, shadow mode) capturou 9.350 inferências reais ao longo de rounds [1, 2, 3, 4] com 0 crashes.",
            "Gate `timeout rate = 0%` falhou: ocorreram 5 timeouts (0.0535%, índices 0..4 no tick 144, latência 25.5613 ms > timeout 25 ms), correspondentes exatamente ao primeiro batch de warm-up do ONNX Runtime.",
            "Após o warm-up (9.345 inferências seguintes), timeouts = 0, failures = 0, dropped_requests = 0, P50 = 10.4325 ms, P95 = 12.2790 ms (<= 15 ms), P99 = 14.8707 ms (<= 20 ms).",
            "Todos os guardrails de integridade passaram (0 violações de autoridade Utility AI, 0 SAVE neural, 0 spots sem supervisão, 0 OBJECTIVE/RETAKE ilegais, 0 leaks de identificador, 1 load do modelo).",
            "Observação adicional: `neural_state` permaneceu em `TRANSIT` e `neural_sector` em `MID` em todas as 9.345 inferências válidas porque `UpdatePositioningShadowObservation` em `CsBotManagerPlugin.cs` ainda envia tensores zerados (placeholder) em vez do histórico real de 32 frames x 18 features dos bots.",
        ],
        "recommended_fix_before_retry": [
            "Executar 1 inferência dummy de warm-up dentro de `PositioningTransformerService.LoadModel()` para eliminar o cold-start de 25.56 ms no primeiro tick.",
            "Popular o ring buffer temporal real (32 frames x 18 features) por bot em `CsBotManagerPlugin.cs` antes de repetir o smoke e iniciar a partida completa.",
        ],
    }
    with open(LIVE_DIR / "findings.json", "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2, ensure_ascii=False)

    report_md = f"""# Relatório Canônico — Marco 2B.6.1: Captura ao Vivo em Shadow Mode (Smoke)

**Decisão Canônica:** `POSITIONING_LIVE_SMOKE_FAILED`  
**Chancela:** `AGENT_REVIEWED` / `AUTOMATED_CHECK_PASS`  
**Natureza dos Dados:** `REAL_LIVE_CS2_SERVER` (captura real em `H:\\CS2_AI_Server`, `de_mirage`, 5v5 bots, 4 Hz)

---

## 1. Resumo Executivo

A captura curta (**Smoke ao Vivo**) foi executada no servidor CS2 dedicado em `de_mirage` (rounds `1` a `4`, `9.350` inferências registradas em `smoke_shadow_telemetry.jsonl`, `0` crashes).

O smoke foi encerrado como **`POSITIONING_LIVE_SMOKE_FAILED`** porque o gate obrigatório **`timeout rate = 0%`** foi violado na primeira chamada de inferência (warm-up JIT/ONNX Runtime):
- **Timeouts:** `5/9.350` (`0.0535%`), todos no **1º batch** (`tick = 144`, índices `0..4`, `latency_ms = 25.5613 ms > 25 ms`).
- **Demais 9.345 inferências:** `0` timeouts, `0` falhas, `0` dropped requests, `P50 = {smoke["latency_ms"]["p50"]} ms`, **`P95 = {smoke["latency_ms"]["p95"]} ms`** (`<= 15 ms`), **`P99 = {smoke["latency_ms"]["p99"]} ms`** (`<= 20 ms`), `model_load_count = 1`.
- **Integridade & Guardrails:** `0` violações de autoridade da Utility AI, `0` predições `SAVE` neurais, `0` spots sem supervisão, `0` overrides ilegais de `OBJECTIVE`/`RETAKE`, `0` vazamentos de identificador bruto.

Conforme a Seção 3 do Marco 2B.6.1, **a partida completa não foi iniciada**.

---

## 2. Causa Raiz e Próximo Passo Recomendado

1. **Cold-start ONNX no 1º tick (`25.5613 ms`):** adicionar 1 chamada de warm-up síncrona dentro de `PositioningTransformerService.LoadModel()`.
2. **Buffer de Features Placeholder:** nas `9.345` inferências válidas, `neural_state = TRANSIT` e `neural_sector = MID` em `100%` dos casos porque `UpdatePositioningShadowObservation()` em `src/CsBotManager/CsBotManagerPlugin.cs` enviou arrays zerados. Para que a análise tática (Seções 6–8) da partida completa tenha sinal real, é necessário preencher o ring buffer temporal de `32 x 18` features reais por bot antes da nova tentativa.
"""
    with open(LIVE_DIR / "live_shadow_capture_final_report.md", "w", encoding="utf-8") as f:
        f.write(report_md)

    files = [
        "live_capture_input_snapshot.json",
        "smoke_shadow_telemetry.jsonl",
        "smoke_console.log",
        "smoke_runtime_metrics.json",
        "findings.json",
        "live_shadow_capture_final_report.md",
    ]
    evidences: Dict[str, dict] = {}
    for fname in files:
        fp = LIVE_DIR / fname
        assert fp.exists() and fp.stat().st_size > 0, f"Missing {fp}"
        evidences[fname] = {
            "path": str(fp.relative_to(BASE_DIR)).replace("\\", "/"),
            "size_bytes": fp.stat().st_size,
            "sha256": sha256_file(fp),
        }

    with open(LIVE_DIR / "deliverable_evidence.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "marco": "2B.6.1",
                "decision": "POSITIONING_LIVE_SMOKE_FAILED",
                "chancela": "AGENT_REVIEWED",
                "deliverables": evidences,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"FINALIZE_2B61_SMOKE_FAIL_OK count={len(evidences)}")


if __name__ == "__main__":
    main()
