#!/usr/bin/env python3
"""
verify_batch_comparison_math.py
Auditoria Matemática Independente das 200 Amostras e Métricas de pre3a3_npz_batch_comparison.json/.md.
Autor: Mathematical and Statistical Auditor (Tier 3)
"""

import json
import math
import re
from pathlib import Path

def main():
    json_path = Path("pre3a3_npz_batch_comparison.json")
    md_path = Path("pre3a3_npz_batch_comparison.md")

    assert json_path.exists(), f"{json_path} não encontrado!"
    assert md_path.exists(), f"{md_path} não encontrado!"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    samples = data["sample_details"]
    assert len(samples) == 200, f"Total de amostras deve ser 200, obtido {len(samples)}"

    train_samples = [s for s in samples if s["split"] == "train"]
    val_samples = [s for s in samples if s["split"] == "validation"]
    test_samples = [s for s in samples if s["split"] == "test"]

    assert len(train_samples) == 100
    assert len(val_samples) == 50
    assert len(test_samples) == 50

    splits_map = {
        "global": samples,
        "train": train_samples,
        "validation": val_samples,
        "test": test_samples,
    }

    discrepancies = []

    # 1. Checagem de integridade das amostras e invariantes
    for split_name, s_list in splits_map.items():
        n = len(s_list)
        summary = data["metrics_summary"][split_name]

        # Exact match
        exact_c = sum(1 for s in s_list if s["is_exact_match"])
        exact_sp_c = sum(1 for s in s_list if s["is_exact_spatial"])
        
        reported_exact = summary["exact_match"]
        if reported_exact["numerator"] != exact_c or reported_exact["denominator"] != n:
            discrepancies.append(f"[{split_name}] Exact match numerator/denominator incorreto: {reported_exact} vs real {exact_c}/{n}")
        if not math.isclose(reported_exact["rate"], exact_c / n, rel_tol=1e-9):
            discrepancies.append(f"[{split_name}] Exact match rate incorreto: {reported_exact['rate']} vs real {exact_c / n}")

        # Synthetic window
        synth_c = sum(1 for s in s_list if s["is_synthetic_window"])
        reported_synth = summary["synthetic_window"]
        if reported_synth["numerator"] != synth_c or reported_synth["denominator"] != n:
            discrepancies.append(f"[{split_name}] Synthetic window numerator/denominator incorreto: {reported_synth} vs real {synth_c}/{n}")
        if not math.isclose(reported_synth["rate"], synth_c / n, rel_tol=1e-9):
            discrepancies.append(f"[{split_name}] Synthetic window rate incorreto")

        # Static window
        dl_yz_c = sum(1 for s in s_list if s["is_dl_yz_static"])
        dl_f3_17_c = sum(1 for s in s_list if s["is_dl_f3_17_static"])
        npz_sp_static_c = sum(1 for s in s_list if s["is_npz_spatial_static"])
        tm_static_c = sum(1 for s in s_list if s["is_teammates_static"])

        reported_static = summary["static_window"]
        if reported_static["dl_yz_static_numerator"] != dl_yz_c or reported_static["dl_yz_static_rate"] != dl_yz_c / n:
            discrepancies.append(f"[{split_name}] dl_yz_static incorreto")
        if reported_static["dl_features_3_to_17_static_numerator"] != dl_f3_17_c or reported_static["dl_features_3_to_17_static_rate"] != dl_f3_17_c / n:
            discrepancies.append(f"[{split_name}] dl_features_3_to_17_static incorreto")
        if reported_static["npz_spatial_static_numerator"] != npz_sp_static_c or not math.isclose(reported_static["npz_spatial_static_rate"], npz_sp_static_c / n, rel_tol=1e-9):
            discrepancies.append(f"[{split_name}] npz_spatial_static incorreto")
        if reported_static["dl_teammates_static_numerator"] != tm_static_c or reported_static["dl_teammates_static_rate"] != tm_static_c / n:
            discrepancies.append(f"[{split_name}] dl_teammates_static incorreto")

        # Tolerances
        reported_tols = summary["tolerance_matches"]
        for tol_key, tol_dict in reported_tols.items():
            if tol_key.startswith("spatial_tol_"):
                c = sum(1 for s in s_list if s["tolerance_matches"][tol_key])
            else:
                c = sum(1 for s in s_list if s["tolerance_matches"][tol_key])
            if tol_dict["numerator"] != c or tol_dict["denominator"] != n:
                discrepancies.append(f"[{split_name}] {tol_key} num/den incorreto: {tol_dict} vs {c}/{n}")
            if not math.isclose(tol_dict["rate"], c / n, rel_tol=1e-9):
                discrepancies.append(f"[{split_name}] {tol_key} rate incorreto: {tol_dict['rate']} vs {c / n}")

        # Means (variance & displacement)
        mean_var = summary["mean_temporal_variance"]
        calc_dl_sp_var_norm = sum(s["dl_spatial_variance_norm"] for s in s_list) / n
        calc_dl_sp_var_world = sum(s["dl_spatial_variance_world"] for s in s_list) / n
        calc_dl_var_all = sum(s["dl_variance_all"] for s in s_list) / n
        calc_npz_sp_var_norm = sum(s["npz_spatial_variance_norm"] for s in s_list) / n
        calc_npz_sp_var_world = sum(s["npz_spatial_variance_world"] for s in s_list) / n
        calc_npz_var_all = sum(s["npz_variance_all"] for s in s_list) / n

        if not math.isclose(mean_var["dataloader_spatial_variance_norm"], calc_dl_sp_var_norm, rel_tol=1e-6):
            discrepancies.append(f"[{split_name}] dataloader_spatial_variance_norm média diverge")
        if not math.isclose(mean_var["dataloader_spatial_variance_world"], calc_dl_sp_var_world, rel_tol=1e-6):
            discrepancies.append(f"[{split_name}] dataloader_spatial_variance_world média diverge")
        if not math.isclose(mean_var["dataloader_variance_all_features"], calc_dl_var_all, rel_tol=1e-6):
            discrepancies.append(f"[{split_name}] dataloader_variance_all_features média diverge")
        if not math.isclose(mean_var["npz_spatial_variance_norm"], calc_npz_sp_var_norm, rel_tol=1e-6):
            discrepancies.append(f"[{split_name}] npz_spatial_variance_norm média diverge")
        if not math.isclose(mean_var["npz_spatial_variance_world"], calc_npz_sp_var_world, rel_tol=1e-6):
            discrepancies.append(f"[{split_name}] npz_spatial_variance_world média diverge")
        if not math.isclose(mean_var["npz_variance_all_features"], calc_npz_var_all, rel_tol=1e-6):
            discrepancies.append(f"[{split_name}] npz_variance_all_features média diverge")

        # Mean displacement
        mean_disp = summary["mean_spatial_displacement"]
        calc_dl_disp_norm = sum(s["dl_displacement_norm"] for s in s_list) / n
        calc_dl_disp_world = sum(s["dl_displacement_world"] for s in s_list) / n
        calc_npz_disp_norm = sum(s["npz_displacement_norm"] for s in s_list) / n
        calc_npz_disp_world = sum(s["npz_displacement_world"] for s in s_list) / n

        if not math.isclose(mean_disp["dataloader_displacement_norm"], calc_dl_disp_norm, rel_tol=1e-6):
            discrepancies.append(f"[{split_name}] dataloader_displacement_norm média diverge")
        if not math.isclose(mean_disp["dataloader_displacement_world"], calc_dl_disp_world, rel_tol=1e-6):
            discrepancies.append(f"[{split_name}] dataloader_displacement_world média diverge")
        if not math.isclose(mean_disp["npz_displacement_norm"], calc_npz_disp_norm, rel_tol=1e-6):
            discrepancies.append(f"[{split_name}] npz_displacement_norm média diverge")
        if not math.isclose(mean_disp["npz_displacement_world"], calc_npz_disp_world, rel_tol=1e-6):
            discrepancies.append(f"[{split_name}] npz_displacement_world média diverge")

    # 2. Relação Teórica de Drift vs Deslocamento
    theoretical_disp_norm = 0.01
    theoretical_disp_world = 30.00
    # Variância teórica de np.linspace(-0.01, 0.0, 32)
    # N=32, d = 0.01/31. Var(X) = (N^2 - 1)/12 * d^2
    var_X_theoretical = ((32**2 - 1) / 12.0) * ((0.01 / 31.0) ** 2)
    var_spatial_theoretical = var_X_theoretical / 3.0
    var_spatial_world_theoretical = var_spatial_theoretical * (3000.0 ** 2)
    var_all_theoretical = var_X_theoretical / 18.0

    dl_actual_mean_disp_world = data["metrics_summary"]["global"]["mean_spatial_displacement"]["dataloader_displacement_world"]
    dl_actual_mean_var_spatial = data["metrics_summary"]["global"]["mean_temporal_variance"]["dataloader_spatial_variance_norm"]
    dl_actual_mean_var_world = data["metrics_summary"]["global"]["mean_temporal_variance"]["dataloader_spatial_variance_world"]
    dl_actual_mean_var_all = data["metrics_summary"]["global"]["mean_temporal_variance"]["dataloader_variance_all_features"]

    disp_diff = abs(dl_actual_mean_disp_world - theoretical_disp_world)
    var_spatial_diff = abs(dl_actual_mean_var_spatial - var_spatial_theoretical)
    var_world_diff = abs(dl_actual_mean_var_world - var_spatial_world_theoretical)
    var_all_diff = abs(dl_actual_mean_var_all - var_all_theoretical)

    # 3. Conferência de Consistência entre JSON e Markdown
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    md_checks = []
    # ExactMatchRate
    if "0 / 200 (0.00%)" not in md_text:
        md_checks.append("ExactMatchRate 0 / 200 (0.00%) não encontrado no MD")
    # SyntheticWindowRate
    if "200 / 200 (100.00%)" not in md_text:
        md_checks.append("SyntheticWindowRate 200 / 200 (100.00%) não encontrado no MD")
    # Spatial TolMatch tol=0.01
    if "47 / 200 (23.50%)" not in md_text:
        md_checks.append("Spatial TolMatch 47 / 200 (23.50%) não encontrado no MD")
    # Spatial TolMatch tol=0.05
    if "129 / 200 (64.50%)" not in md_text:
        md_checks.append("Spatial TolMatch 129 / 200 (64.50%) não encontrado no MD")
    # NPZ stationary player rate
    if "23 / 200 (11.50%)" not in md_text:
        md_checks.append("NPZ stationary rate 23 / 200 (11.50%) não encontrado no MD")

    results = {
        "discrepancies_count": len(discrepancies),
        "discrepancies": discrepancies,
        "md_discrepancies_count": len(md_checks),
        "md_discrepancies": md_checks,
        "theoretical_validations": {
            "theoretical_displacement_world": theoretical_disp_world,
            "actual_displacement_world": dl_actual_mean_disp_world,
            "displacement_delta": disp_diff,
            "theoretical_spatial_variance_norm": var_spatial_theoretical,
            "actual_spatial_variance_norm": dl_actual_mean_var_spatial,
            "spatial_variance_norm_delta": var_spatial_diff,
            "theoretical_spatial_variance_world": var_spatial_world_theoretical,
            "actual_spatial_variance_world": dl_actual_mean_var_world,
            "spatial_variance_world_delta": var_world_diff,
            "theoretical_all_variance": var_all_theoretical,
            "actual_all_variance": dl_actual_mean_var_all,
            "all_variance_delta": var_all_diff,
        },
        "verdict": "CLEAN" if len(discrepancies) == 0 and len(md_checks) == 0 else "INTEGRITY_VIOLATION"
    }

    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    main()
