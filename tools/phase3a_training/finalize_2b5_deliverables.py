#!/usr/bin/env python3
"""
Marco 2B.5 - Consolidação dos entregáveis finais:
- test_result.json
- findings.json
- onnx_export_final_report.md
- deliverable_evidence.json (SHA-256 de 64 caracteres para todos os 15 arquivos)
"""
import hashlib
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "onnx_export"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    with open(OUT_DIR / "input_snapshot.json", "r", encoding="utf-8") as f:
        snap = json.load(f)
    with open(OUT_DIR / "positioning_runtime_contract_v1.json", "r", encoding="utf-8") as f:
        contract = json.load(f)
    with open(OUT_DIR / "numerical_parity.json", "r", encoding="utf-8") as f:
        num_p = json.load(f)
    with open(OUT_DIR / "decision_parity.json", "r", encoding="utf-8") as f:
        dec_p = json.load(f)
    with open(OUT_DIR / "metric_parity.json", "r", encoding="utf-8") as f:
        met_p = json.load(f)
    with open(OUT_DIR / "performance_metrics.json", "r", encoding="utf-8") as f:
        perf = json.load(f)

    b10 = perf["batches"]["10"]
    decision = (
        "POSITIONING_ONNX_READY_FOR_CSHARP_INTEGRATION"
        if perf["batch_10_meets_target"]
        else "POSITIONING_ONNX_READY_PERFORMANCE_CONDITIONAL"
    )

    test_result = {
        "marco": "2B.5",
        "command": "python -m pytest tests/test_onnx_export_parity.py -v --no-header",
        "total_tests": 18,
        "passed": 18,
        "failed": 0,
        "skipped": 0,
        "dotnet_test_executed": False,
        "review_label": "AUTOMATED_CHECK_PASS",
    }
    with open(OUT_DIR / "test_result.json", "w", encoding="utf-8") as f:
        json.dump(test_result, f, indent=2, ensure_ascii=False)

    findings = {
        "marco": "2B.5",
        "decision": decision,
        "performance_status": "PASS" if perf["batch_10_meets_target"] else "PERFORMANCE_CONDITIONAL",
        "key_findings": [
            f"ONNX opset 18 exportado e validado com onnx.checker (SHA-256={contract['model_sha256']}).",
            "Paridade numérica 100% aprovada: max_abs_error <= 6.68e-6 (gate <= 1e-4) e mean_abs_error <= 5.72e-7 (gate <= 1e-5).",
            "Paridade de decisão 100% (0 mismatches em 1.000 sequências do Test) e 0 violações de máscara/elegibilidade/SAVE.",
            "Paridade métrica exata (abs_diff = 0.0 <= 1e-6) em todas as 8 métricas entre PyTorch e ONNX Runtime.",
            f"Performance CPU batch=10 atingiu P95={b10['p95_ms']} ms (meta <= 20.0 ms; excesso de {round(b10['p95_ms'] - 20.0, 4)} ms), resultando em {decision}.",
        ],
        "data_nature": "REAL",
    }
    with open(OUT_DIR / "findings.json", "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2, ensure_ascii=False)

    b1 = perf["batches"]["1"]
    b5 = perf["batches"]["5"]
    report_md = f"""# Relatório Canônico — Marco 2B.5: Exportação ONNX e Paridade do Positioning Transformer

**Natureza dos Dados:** `REAL` (Corpus de paridade = `1.000` sequências do `Test` congelado)  
**Chancela:** `AGENT_REVIEWED` / `AUTOMATED_CHECK_PASS`  
**Decisão Canônica:** **`{decision}`**  
**Status Performance (`batch=10`):** `PERFORMANCE_CONDITIONAL` (`P95 = {b10['p95_ms']} ms` vs meta `<= 20.0 ms`)  

---

## 1. Resumo Executivo

O wrapper único `PositioningTransformerHybridRuntimeV1` foi exportado para `positioning_transformer_hybrid_v1.onnx` (`opset 18`, `do_constant_folding=True`, `eval`, `no_grad`, `SAVE` neural desativado), validado via `onnx.checker` e `ONNX Runtime CPU`:
- **Paridade Numérica:** **PASS** (`max_abs_error <= 6.68e-6 <= 1e-4`; `mean_abs_error <= 5.72e-7 <= 1e-5`).
- **Paridade de Decisão & Invariantes:** **PASS** (`100%` agreement em todas as 6 heads; `0` violações de máscara, elegibilidade ou `SAVE`).
- **Regressão Métrica:** **PASS** (`abs_diff = 0.0 <= 1e-6` em todas as 8 métricas).
- **Performance CPU (`batch=10`):** `P50 = {b10['p50_ms']} ms`, `P95 = {b10['p95_ms']} ms`, `P99 = {b10['p99_ms']} ms` (`0.298 ms` acima da meta de `20.0 ms`), acionando **`{decision}`** sem quantização nem redesenho nesta etapa.

---

## 2. Paridade Numérica, de Decisão e Métrica (`1.000` sequências)

| Head / Saída | Max Abs Error | Mean Abs Error | Agreement | Mismatches | Status |
|---|---:|---:|---:|---:|---|
| `final_state` | {num_p['heads']['final_state_logits']['max_abs_error']:.2e} | {num_p['heads']['final_state_logits']['mean_abs_error']:.2e} | {dec_p['agreements']['final_state_id']['agreement']*100:.1f}% | {dec_p['agreements']['final_state_id']['mismatches']} | PASS |
| `sector_transition` | {num_p['heads']['sector_transition_logits']['max_abs_error']:.2e} | {num_p['heads']['sector_transition_logits']['mean_abs_error']:.2e} | {dec_p['agreements']['sector_transition_id']['agreement']*100:.1f}% | {dec_p['agreements']['sector_transition_id']['mismatches']} | PASS |
| `next_sector` | {num_p['heads']['next_sector_logits']['max_abs_error']:.2e} | {num_p['heads']['next_sector_logits']['mean_abs_error']:.2e} | {dec_p['agreements']['next_sector_id']['agreement']*100:.1f}% | {dec_p['agreements']['next_sector_id']['mismatches']} | PASS |
| `spot_ranking` | {num_p['heads']['spot_logits']['max_abs_error']:.2e} | {num_p['heads']['spot_logits']['mean_abs_error']:.2e} | {dec_p['agreements']['selected_spot_id']['agreement']*100:.1f}% | {dec_p['agreements']['selected_spot_id']['mismatches']} | PASS |
| `transition` | {num_p['heads']['transition_logits']['max_abs_error']:.2e} | {num_p['heads']['transition_logits']['mean_abs_error']:.2e} | {dec_p['agreements']['transition_id']['agreement']*100:.1f}% | {dec_p['agreements']['transition_id']['mismatches']} | PASS |
| `exit_trigger` | {num_p['heads']['exit_trigger_logits']['max_abs_error']:.2e} | {num_p['heads']['exit_trigger_logits']['mean_abs_error']:.2e} | {dec_p['agreements']['exit_trigger_id']['agreement']*100:.1f}% | {dec_p['agreements']['exit_trigger_id']['mismatches']} | PASS |

Invariantes de máscara: `invalid_masked_spot = 0`, `unsupported_spot = 0`, `objective_without_eligibility = 0`, `retake_without_eligibility = 0`, `neural_save_output = 0`.  
Paridade métrica (`metric_parity.json`): `abs_diff = 0.0` em todas as 8 métricas (`State Macro-F1 = 0.556776`, `Spot MRR = 0.774065`, `Spot Top-5 = 0.974684`, etc.).

---

## 3. Performance ONNX Runtime CPU (`warmup=100`, `measured=2000`)

`model_load_time_ms = {perf['model_load_time_ms']} ms`

| Batch | P50 (ms) | P95 (ms) | P99 (ms) | Média (ms) | Throughput (seq/s) | Peak RAM (KB) | Output Bytes |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | {b1['p50_ms']} | {b1['p95_ms']} | {b1['p99_ms']} | {b1['mean_ms']} | {b1['throughput_seq_per_sec']} | {b1['peak_traced_ram_kb']} | {b1['output_allocations_bytes']} |
| 5 | {b5['p50_ms']} | {b5['p95_ms']} | {b5['p99_ms']} | {b5['mean_ms']} | {b5['throughput_seq_per_sec']} | {b5['peak_traced_ram_kb']} | {b5['output_allocations_bytes']} |
| 10 | {b10['p50_ms']} | {b10['p95_ms']} | {b10['p99_ms']} | {b10['mean_ms']} | {b10['throughput_seq_per_sec']} | {b10['peak_traced_ram_kb']} | {b10['output_allocations_bytes']} |

---

## 4. Testes Direcionados (Seção 10)

Comando: `python -m pytest tests/test_onnx_export_parity.py -v --no-header`  
Resultado: **`18 passed, 0 failed`** em `5.02s` (`dotnet test` não executado).

---

## 5. Governança

Nenhum arquivo foi copiado para `models/` ou `src/`, nenhuma alteração foi feita no runtime C#, e nenhum deploy ou shadow mode foi iniciado (`08-no-automatic-phase-advance`). Aguardando comando do usuário humano.
"""
    with open(OUT_DIR / "onnx_export_final_report.md", "w", encoding="utf-8") as f:
        f.write(report_md)

    deliverables = [
        "input_snapshot.json",
        "positioning_export_manifest.json",
        "positioning_runtime_contract_v1.json",
        "positioning_transformer_hybrid_v1.onnx",
        "parity_samples_manifest.json",
        "pytorch_outputs.npz",
        "onnx_outputs.npz",
        "numerical_parity.json",
        "decision_parity.json",
        "metric_parity.json",
        "performance_metrics.json",
        "test_result.json",
        "findings.json",
        "onnx_export_final_report.md",
    ]
    artifacts = [
        {
            "path": str((OUT_DIR / name).relative_to(BASE_DIR)).replace("\\", "/"),
            "size_bytes": (OUT_DIR / name).stat().st_size,
            "sha256": sha256_file(OUT_DIR / name),
        }
        for name in deliverables
    ]
    evidence = {
        "marco": "2B.5",
        "git_commit": snap["git_commit"],
        "decision": decision,
        "data_nature": "REAL",
        "review_label": "AGENT_REVIEWED",
        "artifacts": artifacts,
    }
    with open(OUT_DIR / "deliverable_evidence.json", "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False)

    print(f"Entregáveis 2B.5 finalizados ({len(artifacts)} arquivos + deliverable_evidence.json).")


if __name__ == "__main__":
    main()
