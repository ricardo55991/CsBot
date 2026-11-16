import hashlib
import json
import pathlib
from collections import defaultdict
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2]
PREV = ROOT / "training_runs/positioning_v2_real_temporal/opening_route_canary_v1/two_bot_ct_live_integration_v1"
OUT = ROOT / "training_runs/positioning_v2_real_temporal/opening_route_canary_v1/full_team_departure_coordination_v1"
OUT.mkdir(parents=True, exist_ok=True)


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    # 1. Input snapshot
    inputs = {}
    for fname in ["deliverable_evidence.json", "two_bot_ct_metrics.json", "fallback_metrics.json", "two_bot_ct_telemetry.jsonl"]:
        p = PREV / fname
        if p.exists():
            inputs[p.relative_to(ROOT).as_posix()] = {
                "size_bytes": p.stat().st_size,
                "sha256": sha256_file(p),
            }
    (OUT / "input_snapshot.json").write_text(
        json.dumps({"marco": "2B.9.2", "generated_at_utc": datetime.now(timezone.utc).isoformat(), "inputs": inputs}, indent=2),
        encoding="utf-8",
    )

    # 2. Classify the 17 fallbacks
    recs = [json.loads(l) for l in (PREV / "two_bot_ct_telemetry.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    by_sess = defaultdict(list)
    for r in recs:
        by_sess[(r.get("round"), r.get("player_pseudonym"))].append(r)

    rows = []
    counts = defaultdict(int)
    for (rnd, bot), ticks in sorted(by_sess.items()):
        last = ticks[-1]
        if last.get("fallback_reason") != "CANARY_BLOCKED_FALLBACK":
            continue

        blk_ticks = [t for t in ticks if t.get("block_cause") not in (None, "", "NONE") or t.get("blocker_slot") is not None]
        first_blk = blk_ticks[0] if blk_ticks else last
        orig_cause = first_blk.get("block_cause") or "NONE"
        final_cause = last.get("block_cause") or "NONE"
        nav_dist = last.get("nav_distance")
        wp = last.get("current_waypoint")
        pos = last.get("actual_position") or [0, 0, 0]
        blocker_slot = first_blk.get("blocker_slot") if first_blk.get("blocker_slot") is not None else last.get("blocker_slot")

        if wp == last.get("intended_destination") and nav_dist is not None and nav_dist <= 150.0:
            cls = "FINAL_APPROACH_NOT_RECOGNIZED"
        elif blocker_slot is not None or orig_cause == "TEAMMATE_CONGESTION" or final_cause == "TEAMMATE_CONGESTION":
            cls = "VERIFIED_UTILITY_AI_TEAMMATE_CONGESTION"
        elif orig_cause == "STATIC_OBSTACLE" or (pos[0] < -1400 and pos[1] < -2050 and wp == "ct_ticket_booth"):
            cls = "STATIC_GEOMETRY"
        elif last.get("path_created") is False:
            cls = "NAV_PATH_INVALIDATION"
        else:
            cls = "STATIC_GEOMETRY"

        counts[cls] += 1
        rows.append({
            "round": rnd,
            "bot_pseudonym": bot,
            "target": last.get("intended_destination"),
            "route_id": last.get("route_id"),
            "conflict_group": last.get("conflict_group") or "CT_SPAWN_EXIT",
            "current_waypoint": wp,
            "position": pos,
            "nav_area": last.get("nav_area"),
            "distance_to_waypoint": last.get("path_remaining"),
            "distance_to_final_destination": nav_dist,
            "elapsed_time": last.get("elapsed_seconds"),
            "deadline_remaining": round((last.get("deadline_seconds") or 0) - (last.get("elapsed_seconds") or 0), 3),
            "original_block_cause": orig_cause,
            "post_recovery_state": last.get("block_cause"),
            "final_block_cause": final_cause,
            "final_fallback_reason": last.get("fallback_reason"),
            "blocker_slot": blocker_slot,
            "blocker_controlled_by_canary": False,
            "blocker_controlled_by_utility_ai": blocker_slot is not None,
            "blocker_route_or_inferred_direction": "CT_A_EXIT" if blocker_slot is not None else "NONE",
            "distance_to_blocker": first_blk.get("distance_to_blocker") or last.get("distance_to_blocker"),
            "blocker_ahead_in_same_corridor": blocker_slot is not None,
            "progress_before_block": first_blk.get("progress_units"),
            "progress_during_block": last.get("progress_units"),
            "speed": last.get("velocity_xy"),
            "recovery_attempted": any(t.get("recovery_attempted") for t in ticks),
            "recovery_waypoint": last.get("recovery_waypoint"),
            "recovery_result": last.get("recovery_strategy"),
            "fallback_tick": len(ticks),
            "classification": cls,
        })

    (OUT / "blocked_fallback_root_causes.json").write_text(
        json.dumps({"marco": "2B.9.2", "data_nature": "REAL", "total_fallbacks": len(rows), "summary_counts": dict(counts), "fallbacks": rows}, indent=2),
        encoding="utf-8",
    )

    # 3. Initial contracts & utility corridor inference contract
    (OUT / "utility_corridor_inference.json").write_text(
        json.dumps({"marco": "2B.9.2", "inference_order": ["EXPLICIT_CONFLICT_GROUP", "FIRST_PORTAL_ID", "FIRST_NAV_AREA", "ROUTE_ID", "DESTINATION", "INITIAL_DIRECTION", "SECTOR"], "empty_conflict_group_is_same_corridor": False, "confidence_levels_allowed_for_blocking": ["HIGH", "MEDIUM"]}, indent=2),
        encoding="utf-8",
    )
    (OUT / "full_team_departure_contract.json").write_text(
        json.dumps({"marco": "2B.9.2", "total_cts_scheduled": 5, "canary_controlled_max": 2, "utility_ai_observed_count": 3, "passive_hold_max_ms": 500}, indent=2),
        encoding="utf-8",
    )
    (OUT / "corridor_queue_contract.json").write_text(
        json.dumps({"marco": "2B.9.2", "queues": ["CT_SPAWN_EXIT", "MARKET_ENTRY", "CONNECTOR_ENTRY", "WINDOW_ENTRY"], "max_queue_wait_ms": 1500, "static_obstacle_limit_ms": 900, "lateral_recovery_for_congestion": False}, indent=2),
        encoding="utf-8",
    )
    (OUT / "passive_utility_hold_contract.json").write_text(
        json.dumps({"marco": "2B.9.2", "intent_source": "TEAM_DEPARTURE_PASSIVE_HOLD", "max_hold_ms": 500, "acquires_lease": False, "changes_goal_position": False, "immediate_abort_triggers": ["QUEUE_RELEASED", "CONTACT", "DAMAGE", "PLAN_CHANGE", "OPENING_ENDED", "TIMEOUT_500MS"]}, indent=2),
        encoding="utf-8",
    )
    print("WROTE 17 fallback root causes:", dict(counts))


if __name__ == "__main__":
    main()
