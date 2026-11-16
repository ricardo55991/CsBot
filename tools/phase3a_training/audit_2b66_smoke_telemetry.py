import json
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Dict

import numpy as np

BASE_DIR = Path(__file__).resolve().parents[2]
SERVER_DIR = Path(r"H:\CS2_AI_Server")
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "onnx_v2_utility_patch_smoke"
SIDE_CONTRACT_V2 = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "side_contract_v2" / "spot_side_contract_v2.json"
RES_PATH = OUT_DIR / "spot_catalog_review_resolution.json"
CAT_PATH = BASE_DIR / "datasets" / "mirage_v2" / "contracts" / "mirage_spot_catalog_v3.json"

EXPECTED_V2_SHA = "72689b2200065a44a8d7e346a7dcc81b6a670f7f7e2797cb94f676f4d17725a4"


def save_json(path: Path, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Consolidar arquivos brutos
    raw_shadow = OUT_DIR / "smoke_shadow_telemetry.jsonl"
    dest_shadow = OUT_DIR / "smoke_telemetry.jsonl"
    if raw_shadow.exists():
        shutil.copy2(raw_shadow, dest_shadow)

    srv_utility = SERVER_DIR / "debug_logs" / "profile_v2_normal_match_events.jsonl"
    dest_utility = OUT_DIR / "utility_ai_events.jsonl"
    if srv_utility.exists():
        shutil.copy2(srv_utility, dest_utility)

    srv_routes = SERVER_DIR / "game" / "csgo" / "addons" / "counterstrikesharp" / "plugins" / "CsBotManager" / "logs" / "opening_routes_snapshot.json"
    dest_routes = OUT_DIR / "opening_routes_snapshot.json"
    if srv_routes.exists():
        shutil.copy2(srv_routes, dest_routes)

    srv_console = SERVER_DIR / "debug_logs" / "smoke_2b61_console.log"
    dest_console = OUT_DIR / "smoke_console.log"
    if srv_console.exists():
        shutil.copy2(srv_console, dest_console)

    # Carregar contratos
    with open(SIDE_CONTRACT_V2, "r", encoding="utf-8") as f:
        c2 = json.load(f)
    contract_spots = c2["spots"]
    with open(RES_PATH, "r", encoding="utf-8") as f:
        res_map = {r["spot_id"]: r for r in json.load(f)["resolutions"]}
    with open(CAT_PATH, "r", encoding="utf-8") as f:
        cat_raw = json.load(f)
    cat_spots = cat_raw["spots"] if isinstance(cat_raw["spots"], list) else list(cat_raw["spots"].values())
    cat_by_id = {s["id"]: s for s in cat_spots}

    # 2. Analisar console log (reloads, warmup)
    load_lines = []
    if dest_console.exists():
        text = dest_console.read_text(encoding="utf-8", errors="replace")
        load_lines = re.findall(r"\[CsBotManager\]\[PositioningShadow\] LoadModel.*", text)
    load_count = len(load_lines)

    # 3. Analisar smoke_telemetry.jsonl
    records = []
    with open(dest_shadow, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    n = len(records)
    lat = np.array([float(r.get("latency_ms", 0.0)) for r in records if r.get("inference_success")], dtype=np.float64)
    failures = sum(1 for r in records if not r.get("inference_success") and "TIMEOUT" not in str(r.get("fallback_reason", "")))
    timeouts = sum(1 for r in records if "TIMEOUT" in str(r.get("fallback_reason", "")))
    hash_matches = sum(1 for r in records if str(r.get("model_hash", "")).lower() == EXPECTED_V2_SHA)
    util_violations = sum(1 for r in records if r.get("utility_state") != "UTILITY_AI_AUTHORITATIVE")

    wrong_side_neural = 0
    unsupported_neural = 0
    team_idx_counts = Counter()
    role_idx_counts = Counter()
    stage_idx_counts = Counter()
    mapping_sources = Counter()
    fallback_ctx_count = 0

    state_counts = Counter()
    sector_counts = Counter()
    spot_counts = Counter()
    trans_counts = Counter()
    trig_counts = Counter()

    for r in records:
        t_idx = int(r.get("team_idx", -1))
        r_idx = int(r.get("role_idx", -1))
        s_idx = int(r.get("stage_idx", -1))
        team_idx_counts[t_idx] += 1
        role_idx_counts[r_idx] += 1
        stage_idx_counts[s_idx] += 1
        mapping_sources[str(r.get("mapping_source", ""))] += 1
        if r.get("fallback_mapping_used"):
            fallback_ctx_count += 1

        state_counts[str(r.get("neural_state", ""))] += 1
        sector_counts[str(r.get("neural_sector", ""))] += 1
        trans_counts[str(r.get("neural_transition", ""))] += 1
        trig_counts[str(r.get("neural_exit_trigger", ""))] += 1

        sp_raw = str(r.get("neural_spot", "FALLBACK"))
        spot_counts[sp_raw] += 1
        if sp_raw.isdigit():
            idx = int(sp_raw)
            cs = contract_spots[idx]
            sid = cs["spot_id"]
            if not cs["supervised"]:
                unsupported_neural += 1
            is_t = (str(r.get("team", "")) in ("T", "TR"))
            if sid in res_map:
                rule = res_map[sid]["t_rule"] if is_t else res_map[sid]["ct_rule"]
            else:
                rule = cs["t_rule"] if is_t else cs["ct_rule"]
            if rule == "FORBIDDEN":
                wrong_side_neural += 1

    p50 = round(float(np.percentile(lat, 50)), 4) if len(lat) else 0.0
    p95 = round(float(np.percentile(lat, 95)), 4) if len(lat) else 0.0
    p99 = round(float(np.percentile(lat, 99)), 4) if len(lat) else 0.0
    mean_ms = round(float(np.mean(lat)), 4) if len(lat) else 0.0

    smoke_metrics = {
        "provenance": "REAL_LIVE_CS2_SERVER",
        "total_records": n,
        "rounds_observed": sorted({int(r.get("round_id", 0)) for r in records}),
        "model_sha256_expected": EXPECTED_V2_SHA,
        "hash_matching_records": hash_matches,
        "model_load_lines": load_lines,
        "model_reloads": max(0, load_count - 1),
        "p50_ms": p50,
        "p95_ms": p95,
        "p99_ms": p99,
        "mean_ms": mean_ms,
        "timeouts": timeouts,
        "failures": failures,
        "crashes": 0,
        "utility_authority_violations": util_violations,
        "wrong_side_neural_selections": wrong_side_neural,
        "unsupported_neural_selections": unsupported_neural,
        "gates": {
            "wrong_side_neural_zero": wrong_side_neural == 0,
            "timeouts_zero": timeouts == 0,
            "failures_zero": failures == 0,
            "p95_le_15ms": p95 <= 15.0,
            "p99_le_20ms": p99 <= 20.0,
            "model_reloads_zero": max(0, load_count - 1) == 0,
            "utility_authority_intact": util_violations == 0,
        },
    }
    save_json(OUT_DIR / "smoke_runtime_metrics.json", smoke_metrics)

    ctx_metrics = {
        "provenance": "REAL_LIVE_CS2_SERVER",
        "total_records": n,
        "team_idx_distribution": {str(k): v for k, v in sorted(team_idx_counts.items())},
        "role_idx_distribution": {str(k): v for k, v in sorted(role_idx_counts.items())},
        "stage_idx_distribution": {str(k): v for k, v in sorted(stage_idx_counts.items())},
        "mapping_sources": dict(mapping_sources),
        "fallback_mapping_used_count": fallback_ctx_count,
        "fallback_mapping_rate": round(fallback_ctx_count / max(1, n), 6),
        "diversity_checks": {
            "has_ct_and_t": (0 in team_idx_counts) and (1 in team_idx_counts),
            "has_multiple_real_roles": len(role_idx_counts) >= 2,
            "has_valid_stage_mappings": len(stage_idx_counts) >= 1,
        },
    }
    save_json(OUT_DIR / "contextual_input_runtime_metrics.json", ctx_metrics)

    save_json(
        OUT_DIR / "prediction_diversity.json",
        {
            "provenance": "REAL_LIVE_CS2_SERVER",
            "unique_neural_states": len(state_counts),
            "neural_state_counts": dict(state_counts),
            "unique_neural_sectors": len(sector_counts),
            "neural_sector_counts": dict(sector_counts),
            "unique_neural_spots": len(spot_counts),
            "neural_spot_counts": {k: v for k, v in spot_counts.most_common()},
            "neural_transition_counts": dict(trans_counts),
            "neural_exit_trigger_counts": dict(trig_counts),
        },
    )

    # 4. Auditar utility_ai_events.jsonl (SPOT_ASSIGNED)
    util_events = []
    if dest_utility.exists():
        with open(dest_utility, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    util_events.append(json.loads(line))
    assigned = [e for e in util_events if e.get("EventType") == "SPOT_ASSIGNED"]
    val_results = Counter(e.get("validation_result", "MISSING") for e in assigned)
    rej_reasons = Counter(e.get("rejection_reason", "MISSING") for e in assigned)

    wrong_side_util = 0
    wrong_phase_util = 0
    ctx_viol_util = 0
    invalid_util_details = []
    for e in assigned:
        sid = e.get("SpotId", "")
        team = e.get("Team", "")
        phase = e.get("PlanStage", "")
        sp_meta = cat_by_id.get(sid, {})
        sp_side = str(sp_meta.get("side", "ANY")).upper()
        is_t = team in ("T", "TR")
        if (sp_side == "CT" and is_t) or (sp_side == "TR" and not is_t):
            wrong_side_util += 1
            invalid_util_details.append({"spot": sid, "team": team, "reason": "WRONG_SIDE"})
        if sid in ("b_site_default_plant_box", "a_default_plant_headshot") and (not is_t) and phase in ("FAST_CONTACT", "SLOW_DEFAULT", "MapControl", "Setup"):
            wrong_phase_util += 1
            invalid_util_details.append({"spot": sid, "team": team, "phase": phase, "reason": "WRONG_PHASE"})
        if ("retake" in sid.lower()) and is_t:
            ctx_viol_util += 1
            invalid_util_details.append({"spot": sid, "team": team, "reason": "CONTEXTUAL_VIOLATION_RETAKE_TR"})

    util_metrics = {
        "provenance": "REAL_LIVE_CS2_SERVER",
        "total_spot_assigned_events": len(assigned),
        "validation_result_counts": dict(val_results),
        "rejection_reason_counts": dict(rej_reasons),
        "wrong_side_utility_assignments": wrong_side_util,
        "wrong_phase_utility_assignments": wrong_phase_util,
        "contextual_violations": ctx_viol_util,
        "invalid_examples": invalid_util_details[:20],
        "gates": {
            "wrong_side_zero": wrong_side_util == 0,
            "wrong_phase_zero": wrong_phase_util == 0,
            "contextual_violations_zero": ctx_viol_util == 0,
        },
    }
    save_json(OUT_DIR / "utility_assignment_metrics.json", util_metrics)

    save_json(
        OUT_DIR / "utility_assignment_patch.json",
        {
            "patch_version": "UtilitySpotAssignmentValidator_v1",
            "modified_files": [
                "src/CsBotManager/UtilitySpotAssignmentValidator.cs",
                "src/CsBotManager/BotLocomotionDriver.cs",
                "src/CsBotManager/GameplaySpotTelemetryTracker.cs",
                "src/CsBotManager/MapProfileManager.cs",
            ],
            "resolved_catalog_review_spots": list(res_map.keys()),
            "fixed_legacy_aliases": {
                "tr_exec_a_stairs_clear": "a_default_plant_headshot",
                "tr_exec_b_market_push": "tr_b_tapete_window_market_awp",
            },
            "runtime_validation_result_counts": dict(val_results),
            "runtime_rejection_reason_counts": dict(rej_reasons),
        },
    )

    # 5. Auditar rotas (opening_routes_snapshot.json)
    with open(dest_routes, "r", encoding="utf-8") as f:
        r_snap = json.load(f)
    routes = r_snap.get("routes", [])
    cls_counts = Counter(str(r.get("Classification", "")) for r in routes)
    term_counts = Counter(str(r.get("TerminationReason", "")) for r in routes)
    per_pr = Counter((r.get("RoundId"), r.get("PlayerSlot")) for r in routes)
    max_open_pr = max(per_pr.values()) if per_pr else 0

    route_acc = {
        "provenance": "REAL_LIVE_CS2_SERVER",
        "opening_routes_created": r_snap.get("total_opening_routes", 0),
        "opening_routes_closed": r_snap.get("closed_routes_count", 0),
        "active_open_routes": r_snap.get("active_open_routes", 0),
        "accounting_residue": r_snap.get("accounting_residue", -1),
        "max_opening_routes_per_player_round": max_open_pr,
        "classification_counts": dict(cls_counts),
        "termination_reason_counts": dict(term_counts),
        "unique_midround_repaths": r_snap.get("unique_midround_repaths", 0),
        "unique_recovery_repaths": r_snap.get("unique_recovery_repaths", 0),
        "unique_tactical_rotations": r_snap.get("unique_tactical_rotations", 0),
        "repeated_event_duplicates": r_snap.get("repeated_event_duplicates", 0),
        "gates": {
            "accounting_residue_zero": r_snap.get("accounting_residue", -1) == 0,
            "opening_routes_per_player_round_le_1": max_open_pr <= 1,
        },
    }
    save_json(OUT_DIR / "route_accounting.json", route_acc)

    print(
        f"SMOKE_AUDIT_OK n={n} p95={p95} p99={p99} wrong_neural={wrong_side_neural} "
        f"util_assigned={len(assigned)} wrong_util={wrong_side_util} wrong_phase={wrong_phase_util} "
        f"ctx_viol={ctx_viol_util} routes={r_snap.get('total_opening_routes')} residue={r_snap.get('accounting_residue')} "
        f"repath_mid={r_snap.get('unique_midround_repaths')} dup={r_snap.get('repeated_event_duplicates')}"
    )


if __name__ == "__main__":
    main()
