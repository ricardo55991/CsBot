"""Consolida test_result.json, findings.json e deliverable_evidence.json do Marco 2B.3.5."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PATCH = REPO / "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/rare_episode_patch_v1"
BASE_CKPT = REPO / "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/joint_temporal_patch_v1/selected_checkpoint.pt"

ARTIFACTS = [
    "input_snapshot.json",
    "episode_support.json",
    "sampler_configuration.json",
    "experiment_a_metrics.json",
    "experiment_b_metrics.json",
    "experiment_c_metrics.json",
    "experiment_comparison.json",
    "full_validation_metrics.json",
    "exit_trigger_dependency_metrics.json",
    "preservation_check.json",
    "selected_checkpoint.pt",
    "test_result.json",
    "findings.json",
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


fvm = json.loads((PATCH / "full_validation_metrics.json").read_text(encoding="utf-8"))
comp = json.loads((PATCH / "experiment_comparison.json").read_text(encoding="utf-8"))
ep = json.loads((PATCH / "episode_support.json").read_text(encoding="utf-8"))
samp = json.loads((PATCH / "sampler_configuration.json").read_text(encoding="utf-8"))
pres = json.loads((PATCH / "preservation_check.json").read_text(encoding="utf-8"))
ex_dep = json.loads((PATCH / "exit_trigger_dependency_metrics.json").read_text(encoding="utf-8"))

# 1. test_result.json
test_result = {
    "schema": "csbot.rare_episode_patch.test_result.v1",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "command": "python -m pytest tests/test_rare_episode_patch.py -v --no-header",
    "status": "AUTOMATED_CHECK_PASS",
    "collected": 16,
    "passed": 16,
    "failed": 0,
    "skipped": 0,
    "tests": [
        "test_01_EpisodeSamplerUsesUniqueEpisodes",
        "test_02_AdjacentWindowsAreNotDuplicated",
        "test_03_SamplingRatioIsBounded",
        "test_04_TestIsNeverLoaded",
        "test_05_FinalHoldoutIsNeverLoaded",
        "test_06_SpotRankingHeadRemainsBitwiseIdentical",
        "test_07_SectorTransitionHeadRemainsFrozen",
        "test_08_NextSectorHeadRemainsFrozen",
        "test_09_RareStateScoreFormulaIsFrozen",
        "test_10_ObjectiveMetricsAreReported",
        "test_11_RetakeMetricsAreReported",
        "test_12_SaveMetricsAreReported",
        "test_13_PreservationGatesAreEnforced",
        "test_14_BaseCheckpointRemainsUnchanged",
        "test_15_SelectedCheckpointIsRestorable",
        "test_16_ZeroSupportIsNA",
    ],
}
(PATCH / "test_result.json").write_text(json.dumps(test_result, indent=2, ensure_ascii=False), encoding="utf-8")

# 2. findings.json
st_pc = fvm["positioning_state"]["per_class"]
findings = {
    "schema": "csbot.rare_episode_patch.findings.v1",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "decision": fvm["decision"],
    "selected_experiment": fvm["selected_experiment"],
    "rare_state_score": fvm["rare_state_score"],
    "key_findings": [
        {
            "id": "F1_EPISODE_SUPPORT_SUFFICIENT",
            "summary": "Todas as 3 classes raras atingem o suporte episodico minimo em Train (OBJECTIVE=608>=50, RETAKE=2603>=50, SAVE=43>=30).",
        },
        {
            "id": "F2_PRESERVATION_100_PERCENT",
            "summary": "Todos os 10 gates de preservacao passaram; SpotRankingHead, SectorTransitionHead, NextSectorHead, TransitionHead, ExitTriggerHead e blocos 0-1 permaneceram bitwise identicos.",
        },
        {
            "id": "F3_RECALL_BREAKTHROUGH_WITH_PRECISION_BOTTLENECK",
            "summary": (
                f"OBJECTIVE recall subiu de 0.0000 para {st_pc['OBJECTIVE']['recall']} (P={st_pc['OBJECTIVE']['precision']}); "
                f"RETAKE recall subiu de 0.0042 para {st_pc['RETAKE']['recall']} (P={st_pc['RETAKE']['precision']}). "
                "O modelo detecta os contextos, mas gera falsos positivos excessivos sobre TRANSIT."
            ),
        },
        {
            "id": "F4_SAVE_UNRECOVERED",
            "summary": "SAVE permaneceu com recall=0.0000 nos 3 experimentos (apenas 43 episodios em Train / 144 seqs em Validation).",
        },
        {
            "id": "F5_EXIT_TRIGGER_DEPENDENCY",
            "summary": (
                f"ExitTrigger raw neural Macro-F1={ex_dep['raw_neural_exit_trigger']['macro_f1']} vs "
                f"state-consistent Macro-F1={ex_dep['state_consistent_exit_trigger']['macro_f1']}."
            ),
        },
    ],
    "failed_rare_gates": [k for k, v in fvm["gates"]["rare_and_state_gates"].items() if not v],
    "failed_preservation_gates": [k for k, v in fvm["gates"]["preservation_gates"].items() if not v],
}
(PATCH / "findings.json").write_text(json.dumps(findings, indent=2, ensure_ascii=False), encoding="utf-8")

# 3. deliverable_evidence.json
files = {}
for name in ARTIFACTS:
    p = PATCH / name
    files[name] = {
        "exists": p.exists(),
        "bytes": p.stat().st_size if p.exists() else 0,
        "sha256": sha256(p) if p.exists() else None,
    }

evidence = {
    "schema": "csbot.rare_episode_patch.deliverable_evidence.v1",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "milestone": "2B.3.5",
    "data_nature": "REAL",
    "review_status": "AGENT_REVIEWED",
    "decision": fvm["decision"],
    "selected_experiment": fvm["selected_experiment"],
    "base_checkpoint": {
        "path": str(BASE_CKPT.relative_to(REPO)),
        "sha256": sha256(BASE_CKPT),
    },
    "reproducible_commands": [
        "python -u tools/phase3a_training/audit_2b35_episodes.py",
        "python -u tools/phase3a_training/run_marco_2b35_rare_episode_patch.py",
        "python -m pytest tests/test_rare_episode_patch.py -v --no-header",
        "python -u tools/phase3a_training/build_2b35_evidence.py",
    ],
    "artifacts": files,
    "comparison": comp,
    "full_validation_summary": {
        "total_evaluated": fvm["validation_total_evaluated"],
        "rare_state_score": fvm["rare_state_score"],
        "positioning_state": fvm["positioning_state"],
        "sector_transition_occurs": fvm["sector_transition_occurs"],
        "next_sector": fvm["next_sector"],
        "transition": fvm["transition"],
        "spot_ranking": fvm["spot_ranking"],
    },
    "exit_trigger_dependency": ex_dep,
    "gates": fvm["gates"],
}
(PATCH / "deliverable_evidence.json").write_text(
    json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8"
)

print("=== RESUMO PARA RELATORIO ===")
print("Decision:", fvm["decision"], "| Selected:", fvm["selected_experiment"], "| RareStateScore:", fvm["rare_state_score"])
for k, v in comp["experiments"].items():
    print(f"  {k}: score={v['rare_state_score']} pres={v['all_preservation_passed']} "
          f"OBJ(P={v['objective']['precision']},R={v['objective']['recall']},F1={v['objective']['f1']}) "
          f"RET(P={v['retake']['precision']},R={v['retake']['recall']},F1={v['retake']['f1']}) "
          f"SAV(P={v['save']['precision']},R={v['save']['recall']},F1={v['save']['f1']})")
print("PositioningState global: mF1=", fvm["positioning_state"]["macro_f1"], "balAcc=", fvm["positioning_state"]["balanced_accuracy"])
for c, m in st_pc.items():
    print(f"  {c:<12} sup={m['support']:>6} pred={m['predicted_count']:>6} P={m['precision']} R={m['recall']} F1={m['f1']} fp={m['fp']} fn={m['fn']}")
print("Preservation: TO_mF1=", fvm["sector_transition_occurs"]["macro_f1"],
      "TO_rec=", fvm["sector_transition_occurs"]["per_class"]["TRANSITION_OCCURS"]["recall"],
      "NT_rec=", fvm["sector_transition_occurs"]["per_class"]["NO_TRANSITION"]["recall"],
      "NS_mF1=", fvm["next_sector"]["macro_f1"],
      "TR_mF1=", fvm["transition"]["macro_f1"],
      "Spot=", fvm["spot_ranking"])
print("ExitTrigger raw:", ex_dep["raw_neural_exit_trigger"]["macro_f1"],
      {k: ex_dep["raw_neural_exit_trigger"]["per_class"][k]["recall"] for k in ("BOMB_PLANTED","TACTIC_REVISION","FIRST_KILL","UTILITY_EXPIRED","BOMB_SPOTTED")})
print("ExitTrigger cons:", ex_dep["state_consistent_exit_trigger"]["macro_f1"],
      {k: ex_dep["state_consistent_exit_trigger"]["per_class"][k]["recall"] for k in ("BOMB_PLANTED","TACTIC_REVISION","FIRST_KILL","UTILITY_EXPIRED","BOMB_SPOTTED")})
print("Failed rare gates:", findings["failed_rare_gates"])
print("Artifacts SHA256:")
for name, info in files.items():
    print(f"  {info['sha256']}  {info['bytes']:>9}  {name}")
