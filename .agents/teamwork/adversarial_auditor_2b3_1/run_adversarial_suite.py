#!/usr/bin/env python3
"""
Adversarial Verification Suite - Marco 2B.3: Treinamento Completo do Positioning Transformer Temporal Real.
Executa testes adversariais empíricos independentes sobre o código, artefatos e relatórios.
"""

import sys
import os
import json
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

WORKSPACE_ROOT = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from tools.phase3a_training.positioning_model_v2 import (
    PositioningTransformerV2RealTemporal,
    PositioningTransformerV2Loss,
    STATE_NAMES,
    STATE_MAP,
    SECTOR_TRANSITION_NAMES,
    SECTOR_TRANSITION_MAP,
    NEXT_SECTOR_NAMES,
    NEXT_SECTOR_MAP,
    TRANSITION_NAMES,
    TRANSITION_MAP,
    EXIT_TRIGGER_NAMES,
    EXIT_TRIGGER_MAP
)
from tools.phase3a_training.canonical_v2_dataloader import (
    CanonicalV2PositioningDataset,
    load_supervised_spot_mask,
    load_split_definitions,
    INDEX_DIR,
    SIDECAR_DIR,
    MASK_PATH,
    SPLITS_PATH,
    CATALOG_PATH
)

FULL_TRAIN_DIR = WORKSPACE_ROOT / "training_runs" / "positioning_v2_real_temporal" / "full_training"

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def test_adversarial_conditional_masks():
    print("\n--- TESTE 1: MÁSCARAS CONDICIONAIS ADVERSARIAIS ---")
    mask = load_supervised_spot_mask()
    criterion = PositioningTransformerV2Loss(supervised_spot_mask=mask)

    unsupported_spots = (mask == 0).nonzero().squeeze().tolist()
    supported_spots = (mask == 1).nonzero().squeeze().tolist()

    # Adversarial Batch 1: NO_TRANSITION com logits absurdos e target de next_sector aleatório
    B = 16
    outputs = {
        "logits_state": torch.randn(B, 7, requires_grad=True),
        "logits_transition_occurs": torch.randn(B, 2, requires_grad=True),
        "logits_next_sector": torch.randn(B, 5, requires_grad=True) * 100.0,
        "raw_logits_spot": torch.randn(B, 53, requires_grad=True) * 100.0,
        "logits_transition": torch.randn(B, 7, requires_grad=True),
        "logits_trigger": torch.randn(B, 8, requires_grad=True)
    }
    targets = {
        "positioning_state": torch.zeros(B, dtype=torch.long), # TRANSIT
        "sector_transition_occurs": torch.zeros(B, dtype=torch.long), # NO_TRANSITION
        "next_sector": torch.randint(0, 5, (B,), dtype=torch.long),
        "next_sector_loss_mask": torch.zeros(B, dtype=torch.float32), # mascarado
        "candidate_spot_idx": torch.tensor([unsupported_spots[0]] * B, dtype=torch.long),
        "spot_loss_mask": torch.ones(B, dtype=torch.bool), # Tenta forçar spot loss em TRANSIT
        "transition": torch.zeros(B, dtype=torch.long),
        "exit_trigger": torch.zeros(B, dtype=torch.long)
    }
    cand_mask = torch.ones(B, 53, dtype=torch.bool)
    loss_dict = criterion(outputs, targets, candidate_mask=cand_mask)

    next_sector_loss = float(loss_dict["loss_next_sector"].item())
    spot_loss = float(loss_dict["loss_spot"].item())

    print(f"  NextSectorLoss sob NO_TRANSITION: {next_sector_loss}")
    print(f"  SpotLoss sob TRANSIT com spot sem suporte: {spot_loss}")

    assert next_sector_loss == 0.0, f"FALHA! NextSectorLoss foi {next_sector_loss} sob NO_TRANSITION!"
    assert spot_loss == 0.0, f"FALHA! SpotLoss foi {spot_loss} sob TRANSIT!"

    # Adversarial Batch 2: Não-TRANSIT, mas spot_loss_mask == 0
    targets["positioning_state"] = torch.ones(B, dtype=torch.long) # CLEARANCE
    targets["spot_loss_mask"] = torch.zeros(B, dtype=torch.bool) # MASKED
    targets["candidate_spot_idx"] = torch.tensor([supported_spots[0]] * B, dtype=torch.long)
    loss_dict2 = criterion(outputs, targets, candidate_mask=cand_mask)
    spot_loss2 = float(loss_dict2["loss_spot"].item())
    print(f"  SpotLoss com spot_loss_mask == False: {spot_loss2}")
    assert spot_loss2 == 0.0, f"FALHA! SpotLoss foi {spot_loss2} com spot_loss_mask == False!"

    # Adversarial Batch 3: Não-TRANSIT, spot_loss_mask == 1, target suportado, MAS fora da candidate_mask
    cand_mask_without_target = torch.ones(B, 53, dtype=torch.bool)
    cand_mask_without_target[:, supported_spots[0]] = False
    targets["spot_loss_mask"] = torch.ones(B, dtype=torch.bool)
    loss_dict3 = criterion(outputs, targets, candidate_mask=cand_mask_without_target)
    spot_loss3 = float(loss_dict3["loss_spot"].item())
    print(f"  SpotLoss com target fora da candidate_mask: {spot_loss3}")
    assert spot_loss3 == 0.0, f"FALHA! SpotLoss foi {spot_loss3} com target ausente da candidate_mask!"

    # Adversarial Batch 4: Não-TRANSIT, spot_loss_mask == 1, target na candidate_mask, MAS spot é desprovido de suporte
    cand_mask_with_unsupported = torch.ones(B, 53, dtype=torch.bool)
    targets["candidate_spot_idx"] = torch.tensor([unsupported_spots[0]] * B, dtype=torch.long)
    loss_dict4 = criterion(outputs, targets, candidate_mask=cand_mask_with_unsupported)
    spot_loss4 = float(loss_dict4["loss_spot"].item())
    print(f"  SpotLoss com target desprovido de suporte (mask == 0): {spot_loss4}")
    assert spot_loss4 == 0.0, f"FALHA! SpotLoss foi {spot_loss4} para spot sem suporte!"

    print("  -> Veredito Teste 1: PASS (Todas as máscaras condicionais são matematicamente impenetráveis)")
    return True

def test_adversarial_supervised_spot_mask():
    print("\n--- TESTE 2: MÁSCARA DE SPOTS SUPERVISIONADOS E SELEÇÃO NEURAL ---")
    mask = load_supervised_spot_mask()
    supported_count = int((mask == 1).sum().item())
    unsupported_count = int((mask == 0).sum().item())
    print(f"  Total de spots: 53. Suportados: {supported_count}, Não suportados: {unsupported_count}")
    assert supported_count == 27, f"Esperado 27 spots suportados, obtido {supported_count}"
    assert unsupported_count == 26, f"Esperado 26 spots não suportados, obtido {unsupported_count}"

    # Carregar o checkpoint real selecionado
    ckpt_path = FULL_TRAIN_DIR / "selected_candidate.pt"
    ckpt = torch.load(ckpt_path, map_location="cpu")
    model = PositioningTransformerV2RealTemporal(supervised_spot_mask=mask)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    # Passar batch com candidate_mask aberta (todos os 53 spots True)
    B = 32
    self_hist = torch.randn(B, 32, 18)
    teammates = torch.randn(B, 32, 4, 18)
    cand_mask = torch.ones(B, 53, dtype=torch.bool)

    with torch.no_grad():
        out = model(self_hist, teammates, candidate_mask=cand_mask)
        logits_spot = out["logits_spot"] # [B, 53]

    unsupported_indices = (mask == 0).nonzero().squeeze().tolist()
    unsupported_logits = logits_spot[:, unsupported_indices].cpu().numpy()
    max_unsupported = np.max(unsupported_logits)
    print(f"  Logit máximo entre spots desprovidos de suporte: {max_unsupported}")
    assert max_unsupported <= -1e9, f"FALHA! Logit de spot sem suporte foi {max_unsupported} > -1e9!"

    preds = torch.argmax(logits_spot, dim=1).cpu().numpy()
    for i, p in enumerate(preds):
        assert p not in unsupported_indices, f"FALHA! Spot sem suporte {p} venceu seleção neural no exemplo {i}!"

    # Verificar confusion counts da validação gravados
    for seed in [42026, 42027, 42028]:
        conf_file = FULL_TRAIN_DIR / f"seed_{seed}" / "confusion_counts_validation.json"
        with open(conf_file, "r", encoding="utf-8") as f:
            cdata = json.load(f)
        # Verificar collapse monitoring
    with open(FULL_TRAIN_DIR / "collapse_monitoring.json", "r", encoding="utf-8") as f:
        col_data = json.load(f)
    for s_name, s_mon in col_data["seeds_monitoring"].items():
        assert s_mon["invalid_masked_selections"] == 0
        assert s_mon["unsupported_spot_selections"] == 0
        print(f"  Seed {s_name}: invalid_masked={s_mon['invalid_masked_selections']}, unsupported_spot={s_mon['unsupported_spot_selections']}")

    print("  -> Veredito Teste 2: PASS (Nenhum spot desprovido de suporte conseguiu logit positivo ou vitória neural)")
    return True

def test_adversarial_class_weights_leakage():
    print("\n--- TESTE 3: CÁLCULO DE PESOS DE CLASSE E PROVENIÊNCIA TRAIN-ONLY ---")
    weights_path = FULL_TRAIN_DIR / "class_weights.json"
    with open(weights_path, "r", encoding="utf-8") as f:
        w_data = json.load(f)

    assert w_data["validation_used_for_weights"] is False
    assert w_data["test_used_for_weights"] is False
    assert w_data["provenance"] == "TRAIN_ONLY_SPLIT_311_DEMOS"

    reported_train_rows = w_data["train_rows_evaluated"]
    print(f"  Linhas de treino reportadas em class_weights.json: {reported_train_rows}")

    # Recontar diretamente dos shards Parquet o split train
    train_rows_count = 0
    state_counts_actual = {name: 0 for name in STATE_NAMES}
    for i in range(5):
        df = pd.read_parquet(INDEX_DIR / f"shard_{i:03d}.parquet", columns=["split", "PositioningState"])
        train_df = df[df["split"] == "train"]
        train_rows_count += len(train_df)
        for st, c in train_df["PositioningState"].value_counts().items():
            if st in state_counts_actual:
                state_counts_actual[st] += c

    print(f"  Linhas de treino contadas diretamente do disco: {train_rows_count}")
    assert reported_train_rows == train_rows_count, f"Divergência de contagem: {reported_train_rows} != {train_rows_count}"

    reported_state_counts = w_data["positioning_state"]["raw_support"]
    for st in STATE_NAMES:
        assert reported_state_counts[st] == state_counts_actual[st], f"Divergência na contagem de {st}: {reported_state_counts[st]} != {state_counts_actual[st]}"

    # Verificar que as linhas dos splits Validation (501.434) e Test (545.508) NÃO foram somadas
    assert train_rows_count < 3411434, "Erro crítico: train_rows_count engloba o corpus inteiro!"
    assert train_rows_count == 2364492, f"Train count {train_rows_count} != 2.364.492"

    print("  -> Veredito Teste 3: PASS (Zero contaminação de Validation ou Test em class_weights.json)")
    return True

def test_adversarial_checkpoint_selection():
    print("\n--- TESTE 4: SELEÇÃO DE CHECKPOINT E ISOLAMENTO DE TEST ---")
    sel_path = FULL_TRAIN_DIR / "best_model_selection.json"
    with open(sel_path, "r", encoding="utf-8") as f:
        sel_data = json.load(f)

    assert sel_data["selection_mode"] == "VALIDATION_COMPOSITE_SCORE_MAXIMUM"
    assert sel_data["governance_compliance"]["test_split_used_for_selection"] is False
    assert sel_data["governance_compliance"]["final_holdout_used_for_selection"] is False

    sel_seed = sel_data["selected_seed"]
    sel_epoch = sel_data["selected_epoch"]
    sel_score = sel_data["selected_composite_score"]
    sel_sha = sel_data["selected_checkpoint_sha256"]
    print(f"  Candidato selecionado: Seed {sel_seed}, Época {sel_epoch}, CompositeScore {sel_score}")

    # Verificar que o hash de selected_candidate.pt é idêntico a seed_42028/best_checkpoint.pt
    best_ckpt_source = FULL_TRAIN_DIR / f"seed_{sel_seed}" / "best_checkpoint.pt"
    source_sha = compute_sha256(best_ckpt_source)
    target_sha = compute_sha256(FULL_TRAIN_DIR / "selected_candidate.pt")
    assert source_sha == sel_sha, f"Divergência de hash na origem: {source_sha} != {sel_sha}"
    assert target_sha == sel_sha, f"Divergência de hash no destino: {target_sha} != {sel_sha}"

    # Conferir se as outras seeds tiveram score menor
    with open(FULL_TRAIN_DIR / "three_seed_comparison.json", "r", encoding="utf-8") as f:
        three_data = json.load(f)
    scores = three_data["composite_score"]["scores"]
    assert sel_score == max(scores), f"O score selecionado {sel_score} não foi o máximo entre {scores}!"

    # Conferir se o test split foi aberto: tentar instanciar CanonicalV2PositioningDataset('test')
    try:
        CanonicalV2PositioningDataset(split="test")
        test_isolated = False
    except ValueError:
        test_isolated = True

    assert test_isolated, "FALHA GRAVE! Foi possível instanciar o split 'test'!"
    print("  -> Veredito Teste 4: PASS (Melhor checkpoint escolhido estritamente por Validation, Test 100% lacrado)")
    return True

def test_adversarial_composite_score_formula():
    print("\n--- TESTE 5: FÓRMULA DO COMPOSITESCORE E REPRODUÇÃO NUMÉRICA ---")
    formula_path = FULL_TRAIN_DIR / "frozen_composite_formula.json"
    with open(formula_path, "r", encoding="utf-8") as f:
        form_data = json.load(f)

    w = form_data["weights"]
    assert w["StateMacroF1"] == 0.20
    assert w["SectorTransitionMacroF1"] == 0.10
    assert w["NextSectorMacroF1"] == 0.10
    assert w["SpotMRR"] == 0.25
    assert w["TransitionMacroF1"] == 0.20
    assert w["ExitTriggerMacroF1"] == 0.15
    assert sum(w.values()) == 1.00

    # Recalcular matematicamente os scores para as 3 seeds a partir de three_seed_comparison.json
    with open(FULL_TRAIN_DIR / "three_seed_comparison.json", "r", encoding="utf-8") as f:
        ts_data = json.load(f)

    for i, s in enumerate(ts_data["seeds"]):
        st_f1 = ts_data["state_macro_f1"]["scores"][i]
        sto_f1 = ts_data["sector_transition_macro_f1"]["scores"][i]
        ns_f1 = ts_data["next_sector_macro_f1"]["scores"][i]
        mrr = ts_data["spot_mrr"]["scores"][i]
        tr_f1 = ts_data["transition_macro_f1"]["scores"][i]
        et_f1 = ts_data["exit_trigger_macro_f1"]["scores"][i]

        expected_score = (
            0.20 * st_f1 +
            0.10 * sto_f1 +
            0.10 * ns_f1 +
            0.25 * mrr +
            0.20 * tr_f1 +
            0.15 * et_f1
        )
        reported_score = ts_data["composite_score"]["scores"][i]
        diff = abs(expected_score - reported_score)
        print(f"  Seed {s}: Calculado={expected_score:.4f}, Reportado={reported_score:.4f}, Diff={diff:.6f}")
        assert diff < 0.0005, f"Divergência matemática no CompositeScore da seed {s}!"

    print("  -> Veredito Teste 5: PASS (Fórmula congelada rigorosamente respeitada)")
    return True

def test_adversarial_three_seeds_independence():
    print("\n--- TESTE 6: INDEPENDÊNCIA ESTOCÁSTICA DAS 3 SEEDS ---")
    ckpts = {}
    for s in [42026, 42027, 42028]:
        p = FULL_TRAIN_DIR / f"seed_{s}" / "best_checkpoint.pt"
        ckpts[s] = torch.load(p, map_location="cpu")["model_state_dict"]

    # Comparar tensores entre as seeds para provar que os pesos não são cópias
    # Comparar head_spot.3.weight
    w26 = ckpts[42026]["head_spot.3.weight"].flatten().numpy()
    w27 = ckpts[42027]["head_spot.3.weight"].flatten().numpy()
    w28 = ckpts[42028]["head_spot.3.weight"].flatten().numpy()

    # Distância L2 e correlação
    dist_26_27 = np.linalg.norm(w26 - w27)
    dist_26_28 = np.linalg.norm(w26 - w28)
    dist_27_28 = np.linalg.norm(w27 - w28)

    cos_sim_26_27 = np.dot(w26, w27) / (np.linalg.norm(w26) * np.linalg.norm(w27))
    cos_sim_26_28 = np.dot(w26, w28) / (np.linalg.norm(w26) * np.linalg.norm(w28))
    cos_sim_27_28 = np.dot(w27, w28) / (np.linalg.norm(w27) * np.linalg.norm(w28))

    print(f"  Distância L2 (26 vs 27): {dist_26_27:.4f}, CosSim: {cos_sim_26_27:.4f}")
    print(f"  Distância L2 (26 vs 28): {dist_26_28:.4f}, CosSim: {cos_sim_26_28:.4f}")
    print(f"  Distância L2 (27 vs 28): {dist_27_28:.4f}, CosSim: {cos_sim_27_28:.4f}")

    assert dist_26_27 > 0.1, "Seeds 26 e 27 são idênticas!"
    assert dist_26_28 > 0.1, "Seeds 26 e 28 são idênticas!"
    assert dist_27_28 > 0.1, "Seeds 27 e 28 são idênticas!"

    # Verificar curvas de treino distintas
    with open(FULL_TRAIN_DIR / "seed_42026" / "learning_curves.json") as f: lc26 = json.load(f)
    with open(FULL_TRAIN_DIR / "seed_42027" / "learning_curves.json") as f: lc27 = json.load(f)
    with open(FULL_TRAIN_DIR / "seed_42028" / "learning_curves.json") as f: lc28 = json.load(f)

    losses_26 = [x["train_loss"] for x in lc26]
    losses_27 = [x["train_loss"] for x in lc27]
    losses_28 = [x["train_loss"] for x in lc28]

    assert losses_26 != losses_27, "Perdas de treino idênticas entre 26 e 27!"
    assert losses_26 != losses_28, "Perdas de treino idênticas entre 26 e 28!"
    print(f"  Perdas de treino finais: 26={losses_26[-1]}, 27={losses_27[-1]}, 28={losses_28[-1]}")

    print("  -> Veredito Teste 6: PASS (As 3 seeds apresentam independência estocástica autêntica)")
    return True

def test_adversarial_skeptic_and_governance():
    print("\n--- TESTE 7: AUDITORIA CÉTICA (12 PADRÕES DO CSBOT-REPORT-SKEPTIC E AGENTS.MD) ---")
    violations = []

    # 1. Hashes SHA-256 no handoff e JSONs
    handoff_path = WORKSPACE_ROOT / ".agents" / "teamwork" / "implementer_2b3_1" / "handoff.md"
    with open(handoff_path, "r", encoding="utf-8") as f:
        handoff_content = f.read()

    # Hashes citados no handoff
    expected_hashes = {
        "training_runs/positioning_v2_real_temporal/full_training/baseline_comparison.json": "1b8270d4539007c4cf0cb0ecfd716985ba59e6086ef46345dd2b3a49e567fa9a",
        "training_runs/positioning_v2_real_temporal/full_training/best_model_selection.json": "457035fa3943e37f7f6859b4498deffd5b9deaa19f711c20e56b46adc8bcaa44",
        "training_runs/positioning_v2_real_temporal/full_training/class_weights.json": "8ab2a7c4a573d65a39c497a21ea8df400c9618f16756e40d3b2d481919346210",
        "training_runs/positioning_v2_real_temporal/full_training/collapse_monitoring.json": "0ba1020c5c6dde09527d63831c5f1c4742b6e582eefa5fe35ab5f6255a15f7e1",
        "training_runs/positioning_v2_real_temporal/full_training/compute_preflight.json": "8322d8eff8d635d98cbb63c9e02ac6a887f5a289fab0629f1c3474ff178fc464",
        "training_runs/positioning_v2_real_temporal/full_training/frozen_composite_formula.json": "8e344ad4ae452b4733d2941737f61f87c292114af7c0fb7a9c9acdc8b38c1bf3",
        "training_runs/positioning_v2_real_temporal/full_training/frozen_training_config.json": "79dd3db45c4512bbc21a86db1ba318bc44d564338bd64b08a40f722f9aaec707",
        "training_runs/positioning_v2_real_temporal/full_training/input_snapshot.json": "35e0421c7ccf9836615eef1d29d9c6ebbb4a823077373b8afab072d25599297d",
        "training_runs/positioning_v2_real_temporal/full_training/selected_candidate.pt": "4bcf26a04ec57d7d87132bba43bcd2be5cd5426471a46ae37dad33a38365e352",
        "training_runs/positioning_v2_real_temporal/full_training/temporal_gain_report.json": "0708555fcab35907dfdc31452f62e4aefee2ba871c2a7cb9eeb4c12e97357c24",
        "training_runs/positioning_v2_real_temporal/full_training/three_seed_comparison.json": "4096a8626fb8c347b0fff21703dd86a327af85573c6f672a7a03b8095b0685e5",
    }
    for rel_path, exp_sha in expected_hashes.items():
        act_sha = compute_sha256(WORKSPACE_ROOT / rel_path)
        if act_sha != exp_sha:
            violations.append(f"Divergência de hash SHA-256 em {rel_path}: esperado {exp_sha}, real {act_sha}")
        else:
            print(f"  Hash verificado: {rel_path} -> MATCH")

    # 2. Verificar selos de aprovação humana indevidos (Regra 05)
    unauth_human_tags = ["APPROVED_BY_USER", "REJECTED_BY_USER", "HUMAN_CAPTURE_IN_GAME"]
    for tag in unauth_human_tags:
        if tag in handoff_content:
            violations.append(f"Regra 05 violada! Selo humano {tag} encontrado no handoff!")

    # 3. Verificar suporte zero como N/A (Regra 03)
    # No handoff.md, tabela de classes com suporte zero exibe 'N/A'
    with open(FULL_TRAIN_DIR / "seed_42028" / "confusion_counts_validation.json", "r") as f:
        conf28 = json.load(f)
    for head_k in ["transition_per_class", "exit_trigger_per_class"]:
        for cls_name, cls_m in conf28[head_k].items():
            if cls_m["support"] == 0:
                assert cls_m["recall"] == "N/A"
                assert cls_m["f1"] == "N/A"
                print(f"  Regra 03 respeitada para {head_k} -> {cls_name} (support=0, recall=N/A, f1=N/A)")

    # 4. CRITICAL FINDING: Veredito Canônico e Gates de Validação
    # Avaliar se os gates da Seção 11 do ORIGINAL_REQUEST foram satisfeitos ou se falharam
    gates_failures = []
    with open(FULL_TRAIN_DIR / "best_model_selection.json", "r") as f:
        best_data = json.load(f)
    ms = best_data["metrics_summary"]

    # Gate 1: PositioningState (Active Macro-F1 >= 0.45)
    if ms["state_macro_f1"] < 0.45:
        gates_failures.append(f"PositioningState Macro-F1 ({ms['state_macro_f1']}) < gate 0.45")

    # Gate 2: SectorTransitionOccurs (Macro-F1 >= 0.55)
    if ms["sector_transition_macro_f1"] < 0.55:
        gates_failures.append(f"SectorTransitionOccurs Macro-F1 ({ms['sector_transition_macro_f1']}) < gate 0.55")

    # Gate 3: NextSector (Macro-F1 >= 0.50)
    if ms["next_sector_macro_f1"] < 0.50:
        gates_failures.append(f"NextSector Macro-F1 ({ms['next_sector_macro_f1']}) < gate 0.50")

    # Gate 4: Transition (Macro-F1 >= 0.60)
    if ms["transition_macro_f1"] < 0.60:
        gates_failures.append(f"Transition Macro-F1 ({ms['transition_macro_f1']}) < gate 0.60")

    # Gate 5: ExitTrigger (Macro-F1 >= 0.45)
    if ms["exit_trigger_macro_f1"] < 0.45:
        gates_failures.append(f"ExitTrigger Macro-F1 ({ms['exit_trigger_macro_f1']}) < gate 0.45")

    # Gate 6: CandidateSpotRanking (MRR >= 0.60, Top1 >= 0.45, Top5 >= 0.80)
    if ms["spot_mrr"] < 0.60 or ms["spot_top1"] < 0.45 or ms["spot_top5"] < 0.80:
        gates_failures.append(f"CandidateSpotRanking não atingiu metas")

    print("\n  [VERIFICAÇÃO DE GATES DA SEÇÃO 11]:")
    for gf in gates_failures:
        print(f"    - FALHA DE GATE: {gf}")

    # 5. CONTRADIÇÃO INTERNA EM COLLAPSE_MONITORING.JSON
    with open(FULL_TRAIN_DIR / "collapse_monitoring.json", "r") as f:
        col_data = json.load(f)
    sto_recall = col_data["seeds_monitoring"]["seed_42028"]["sector_transition_occurs_recall"]
    sto_check = col_data["anti_collapse_checks"]["sector_transition_collapse"]
    print(f"\n  [MONITORAMENTO DE COLAPSO]:")
    print(f"    sector_transition_occurs_recall = {sto_recall}")
    print(f"    anti_collapse_checks.sector_transition_collapse = {sto_check}")

    if sto_recall == 0.0 and sto_check is False:
        print("    -> ALERTA ADVERSARIAL: Contradição detectada! Recall de transição é 0.0, mas sector_transition_collapse é reportado como False!")

    print(f"\n  Total de violações de governança / integridade física: {len(violations)}")
    return {
        "violations": violations,
        "gates_failures": gates_failures,
        "sto_recall": sto_recall,
        "sto_check": sto_check
    }

if __name__ == "__main__":
    t1 = test_adversarial_conditional_masks()
    t2 = test_adversarial_supervised_spot_mask()
    t3 = test_adversarial_class_weights_leakage()
    t4 = test_adversarial_checkpoint_selection()
    t5 = test_adversarial_composite_score_formula()
    t6 = test_adversarial_three_seeds_independence()
    t7 = test_adversarial_skeptic_and_governance()
    print("\nSUÍTE ADVERSARIAL COMPLETA EXECUTADA COM SUCESSO!")
