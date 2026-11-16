import hashlib
import json
import math
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2]
PREV_DIR = ROOT / "training_runs/positioning_v2_real_temporal/opening_route_canary_v1/tr_canonical_route_runtime_v1"
OUT_DIR = ROOT / "training_runs/positioning_v2_real_temporal/opening_route_canary_v1/tr_step_up_stabilization_v1"
TELEMETRY_PATH = PREV_DIR / "solo_route_telemetry.jsonl"


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Input snapshot
    input_files = [
        PREV_DIR / "deliverable_evidence.json",
        PREV_DIR / "palace_certification_metrics.json",
        PREV_DIR / "b_kitchen_certification_metrics.json",
        TELEMETRY_PATH,
    ]
    snapshot = {
        "marco": "2B.8.10",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_dir": PREV_DIR.relative_to(ROOT).as_posix(),
        "inputs": {
            p.relative_to(ROOT).as_posix(): {
                "size_bytes": p.stat().st_size,
                "sha256": sha256_file(p),
            }
            for p in input_files
            if p.exists()
        },
    }
    (OUT_DIR / "input_snapshot.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    # 2. Stream telemetry for Palace (t_palace_box_step_1) and B Kitchen (t_b_apps_kitchen_doorway)
    # Keyed by (route_id, round)
    sessions = {}
    targets = {
        "a_palace_deep_room": "t_palace_box_step_1",
        "tr_b_apps_kitchen_control": "t_b_apps_kitchen_doorway",
    }

    with TELEMETRY_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            raw_route = r.get("route_id") or ""
            route_id = None
            for cand in targets:
                if cand in raw_route:
                    route_id = cand
                    break
            if route_id is None:
                continue
            rnd = r.get("round")
            key = (route_id, rnd)
            sess = sessions.get(key)
            if sess is None:
                sess = {
                    "route_id": route_id,
                    "target_step": targets[route_id],
                    "round": rnd,
                    "session_id": f"{route_id}_r{rnd}",
                    "ticks_total": 0,
                    "step_ticks": [],
                    "last_tick": None,
                    "all_jump_pulse_ticks": [],
                    "arrival_status": None,
                    "fallback_reason": None,
                    "completion_reason": None,
                    "authority_release_tick": None,
                }
                sessions[key] = sess

            sess["ticks_total"] += 1
            sess["last_tick"] = r
            sess["arrival_status"] = r.get("arrival_status")
            sess["fallback_reason"] = r.get("fallback_reason")
            sess["completion_reason"] = r.get("completion_reason")
            if r.get("authority_return_tick"):
                sess["authority_release_tick"] = r.get("authority_return_tick")

            tick_idx = r.get("dispatch_tick") or sess["ticks_total"]
            if r.get("transition_action") == "STEP_UP_JUMP_PULSE" or (r.get("jump_pulses_issued") or 0) > 0:
                pass

            step_name = r.get("canonical_step_name") or r.get("current_waypoint")
            if step_name == targets[route_id]:
                sess["step_ticks"].append(r)

    comparison = {"marco": "2B.8.10", "data_nature": "REAL", "routes": {}}

    for route_id, target_step in targets.items():
        route_entries = []
        route_keys = sorted([k for k in sessions.keys() if k[0] == route_id], key=lambda x: x[1])
        for key in route_keys:
            sess = sessions[key]
            st = sess["step_ticks"]
            if not st:
                route_entries.append({
                    "route_id": route_id,
                    "session_id": sess["session_id"],
                    "round": sess["round"],
                    "step_name": target_step,
                    "arrival_status": sess["arrival_status"],
                    "step_ticks_count": 0,
                    "failure_reason": sess["fallback_reason"] or sess["completion_reason"],
                })
                continue

            z_vals = [t["actual_position"][2] for t in st if t.get("actual_position")]
            z_init = z_vals[0] if z_vals else None
            z_max = max(z_vals) if z_vals else None
            z_final = z_vals[-1] if z_vals else None

            pulse_ticks = []
            prev_pulses = st[0].get("jump_pulses_issued", 0)
            for idx, t in enumerate(st):
                cur_p = t.get("jump_pulses_issued", 0)
                if cur_p > prev_pulses or t.get("transition_event_type") == "JUMP_PULSE_ISSUED":
                    pulse_ticks.append(idx)
                prev_pulses = cur_p

            first_pulse_idx = pulse_ticks[0] if pulse_ticks else None
            z_after_pulse = None
            if first_pulse_idx is not None:
                window = st[first_pulse_idx : min(len(st), first_pulse_idx + 25)]
                z_after_pulse = max(t["actual_position"][2] for t in window if t.get("actual_position"))

            blocked_vals = [t.get("blocked_duration_ms", 0.0) for t in st]
            vel_vals = [t.get("velocity_xy", 0.0) for t in st]
            prog_vals = [t.get("progress_units", 0.0) for t in st]
            in_jump_any = any("IN_JUMP" in str(t.get("native_state", "")) or "JUMP" in str(t.get("transition_event_type", "")) for t in st)
            cmds = sorted({str(t.get("transition_event_type")) for t in st if t.get("transition_event_type")})
            nav_areas = [t.get("current_nav_area") or t.get("nav_area") for t in st]

            entry_pos = st[0].get("actual_position")
            exit_pos = st[-1].get("actual_position")
            forward_progress = None
            if entry_pos and exit_pos:
                forward_progress = round(math.hypot(exit_pos[0] - entry_pos[0], exit_pos[1] - entry_pos[1]), 2)

            route_entries.append({
                "route_id": route_id,
                "session_id": sess["session_id"],
                "round": sess["round"],
                "step_name": target_step,
                "arrival_status": sess["arrival_status"],
                "step_ticks_count": len(st),
                "entry_position": entry_pos,
                "exit_position": exit_pos,
                "z_initial": z_init,
                "z_max": z_max,
                "z_final": z_final,
                "z_gain": round(z_max - z_init, 2) if (z_max is not None and z_init is not None) else None,
                "z_after_pulse": z_after_pulse,
                "nav_area_initial": nav_areas[0] if nav_areas else None,
                "nav_area_final": nav_areas[-1] if nav_areas else None,
                "expected_exit_nav_area": st[0].get("expected_exit_nav_area"),
                "jump_pulses_at_entry": st[0].get("jump_pulses_issued", 0),
                "jump_pulses_at_exit": st[-1].get("jump_pulses_issued", 0),
                "jump_pulses_in_step": st[-1].get("jump_pulses_issued", 0) - st[0].get("jump_pulses_issued", 0),
                "pulse_step_tick_indices": pulse_ticks,
                "in_jump_observed": in_jump_any,
                "transition_events": cmds,
                "velocity_xy_min": min(vel_vals) if vel_vals else None,
                "velocity_xy_max": max(vel_vals) if vel_vals else None,
                "forward_progress_xy": forward_progress,
                "max_blocked_duration_ms": max(blocked_vals) if blocked_vals else 0.0,
                "elapsed_entry_s": st[0].get("elapsed_seconds"),
                "elapsed_exit_s": st[-1].get("elapsed_seconds"),
                "step_duration_s": round((st[-1].get("elapsed_seconds", 0) - st[0].get("elapsed_seconds", 0)), 3),
                "authority_release_tick": sess["authority_release_tick"],
                "failure_reason": sess["fallback_reason"] if sess["arrival_status"] != "ON_TIME" else None,
                "last_executor_state": sess["last_tick"].get("executor_state") if sess["last_tick"] else None,
            })

        successes = [e for e in route_entries if e["arrival_status"] == "ON_TIME"]
        failures = [e for e in route_entries if e["arrival_status"] != "ON_TIME"]
        comparison["routes"][route_id] = {
            "target_step": target_step,
            "success_count": len(successes),
            "failure_count": len(failures),
            "failures": failures,
            "successes": successes,
        }
        print(f"=== {route_id} ({target_step}): {len(successes)} ok / {len(failures)} fail ===")
        for fl in failures:
            print("  FAIL:", {k: fl.get(k) for k in ["round", "step_ticks_count", "z_initial", "z_max", "z_gain", "jump_pulses_in_step", "pulse_step_tick_indices", "max_blocked_duration_ms", "step_duration_s", "transition_events", "entry_position", "exit_position"]})
        if successes:
            s0 = successes[0]
            print("  SAMPLE_OK:", {k: s0.get(k) for k in ["round", "step_ticks_count", "z_initial", "z_max", "z_gain", "jump_pulses_in_step", "pulse_step_tick_indices", "max_blocked_duration_ms", "step_duration_s", "transition_events", "entry_position", "exit_position"]})
            z_gains_ok = [s["z_gain"] for s in successes if s.get("z_gain") is not None]
            pulses_ok = [s["jump_pulses_in_step"] for s in successes]
            print("  OK_SUMMARY: z_gain_min=", min(z_gains_ok) if z_gains_ok else None, "z_gain_max=", max(z_gains_ok) if z_gains_ok else None, "pulses_set=", sorted(set(pulses_ok)))

    (OUT_DIR / "step_up_success_failure_comparison.json").write_text(
        json.dumps(comparison, indent=2), encoding="utf-8"
    )
    print("WROTE:", OUT_DIR / "step_up_success_failure_comparison.json")


if __name__ == "__main__":
    main()
