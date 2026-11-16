import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

BASE_DIR = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
SERVER_DIR = Path(r"H:\CS2_AI_Server")
CS2_EXE = SERVER_DIR / "game" / "bin" / "win64" / "cs2.exe"
PLUGINS_DIR = SERVER_DIR / "game" / "csgo" / "addons" / "counterstrikesharp" / "plugins"
PLUGIN_LOGS = PLUGINS_DIR / "CsBotManager" / "logs"
DEBUG_LOGS = SERVER_DIR / "debug_logs"
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "movement_authority_isolation_v1"

CANARY_JSONL = PLUGIN_LOGS / "opening_canary_telemetry.jsonl"
AUTH_TICKS_JSONL = PLUGIN_LOGS / "canary_authority_ticks.jsonl"
AUTH_ACC_JSON = PLUGIN_LOGS / "canary_authority_accounting.json"
COMP_WRITERS_JSON = PLUGIN_LOGS / "competing_writer_attempts.json"
SHADOW_JSONL = PLUGIN_LOGS / "positioning_shadow_telemetry.jsonl"
ROUTES_SNAP_JSON = PLUGIN_LOGS / "opening_routes_snapshot.json"
NO_ELIGIBLE_JSON = PLUGIN_LOGS / "opening_canary_no_eligible.json"


def kill_existing_cs2() -> None:
    subprocess.run(["taskkill", "/F", "/IM", "cs2.exe"], capture_output=True)
    time.sleep(2)


def restore_external_plugins() -> None:
    for name in ["BotState", "BotRandomizer"]:
        disabled = PLUGINS_DIR / f"{name}.disabled"
        active = PLUGINS_DIR / name
        if disabled.exists() and not active.exists():
            disabled.rename(active)


def disable_external_plugins() -> None:
    for name in ["BotState", "BotRandomizer"]:
        active = PLUGINS_DIR / name
        disabled = PLUGINS_DIR / f"{name}.disabled"
        if active.exists() and not disabled.exists():
            active.rename(disabled)


def clear_plugin_logs() -> None:
    PLUGIN_LOGS.mkdir(parents=True, exist_ok=True)
    for p in [
        CANARY_JSONL,
        AUTH_TICKS_JSONL,
        AUTH_ACC_JSON,
        COMP_WRITERS_JSON,
        SHADOW_JSONL,
        ROUTES_SNAP_JSON,
        NO_ELIGIBLE_JSON,
    ]:
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass


def set_flags(enabled: bool, isolation_mode: str, fast_rounds: bool = True) -> None:
    DEBUG_LOGS.mkdir(parents=True, exist_ok=True)
    (DEBUG_LOGS / "canary_enabled.flag").write_text("true" if enabled else "false", encoding="utf-8")
    (DEBUG_LOGS / "canary_isolation_mode.flag").write_text(isolation_mode, encoding="utf-8")
    fast_flag = DEBUG_LOGS / "canary_fast_rounds.flag"
    if fast_rounds:
        fast_flag.write_text("1", encoding="utf-8")
    elif fast_flag.exists():
        fast_flag.unlink()
    auto_debug = DEBUG_LOGS / "auto_debug.flag"
    if auto_debug.exists():
        try:
            auto_debug.unlink()
        except Exception:
            pass


def read_canary_sessions(path: Path) -> tuple[set[int], dict[int, str]]:
    if not path.exists():
        return set(), {}
    finished_rounds: set[int] = set()
    status_by_round: dict[int, str] = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                r = int(rec.get("round", 0))
                if r > 0:
                    st = str(rec.get("arrival_status", "PENDING"))
                    status_by_round[r] = st
                    if rec.get("authority_return_tick") is not None or st != "PENDING":
                        finished_rounds.add(r)
            except Exception:
                pass
    return finished_rounds, status_by_round


def read_shadow_rounds(path: Path) -> tuple[int, set[int]]:
    if not path.exists():
        return 0, set()
    lines = 0
    rounds: set[int] = set()
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            lines += 1
            try:
                rec = json.loads(line)
                r = int(rec.get("round_id", 0))
                if r > 0:
                    rounds.add(r)
            except Exception:
                pass
    return lines, rounds


def run_cs2_until(
    label: str,
    target_canary_sessions: int,
    target_shadow_rounds: int,
    max_wait_s: int,
    min_non_interrupted: int = 0,
) -> dict:
    kill_existing_cs2()
    clear_plugin_logs()

    console_log = DEBUG_LOGS / f"2b83_{label}_console.log"
    if console_log.exists():
        try:
            console_log.unlink()
        except Exception:
            pass

    cmd = [
        str(CS2_EXE),
        "-dedicated",
        "-insecure",
        "+sv_lan", "1",
        "-port", "27016",
        "+game_type", "0",
        "+game_mode", "1",
        "+map", "de_mirage",
        "+bot_quota", "10",
        "+bot_quota_mode", "fill",
        "+exec", "ai_competitive.cfg",
        "+mp_warmuptime", "4",
        "+mp_freezetime", "12",
        "+mp_roundtime", "0.45",
        "+mp_roundtime_defuse", "0.45",
        "+mp_round_restart_delay", "2",
    ]

    env = os.environ.copy()
    env["CSBOT_OPENING_CANARY_MODE"] = "CT"

    t0 = time.time()
    with open(console_log, "w", encoding="utf-8", errors="replace") as log_f:
        proc = subprocess.Popen(
            cmd,
            cwd=str(SERVER_DIR),
            env=env,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )

        last_report = 0.0
        while True:
            elapsed = time.time() - t0
            rc = proc.poll()
            if rc is not None:
                print(f"[{label}] CS2 exited early rc={rc} elapsed={elapsed:.1f}s", flush=True)
                break

            finished_rounds, status_by_round = read_canary_sessions(CANARY_JSONL)
            shadow_lines, shadow_rounds = read_shadow_rounds(SHADOW_JSONL)
            non_interrupted = sum(
                1
                for r in finished_rounds
                if not status_by_round.get(r, "").startswith("INTERRUPTED_")
            )

            if elapsed - last_report >= 15.0:
                print(
                    f"[{label}] elapsed={elapsed:.0f}s canary_done={len(finished_rounds)} "
                    f"(non_int={non_interrupted}) statuses={status_by_round} shadow_rounds={sorted(shadow_rounds)}",
                    flush=True,
                )
                last_report = elapsed

            if target_canary_sessions > 0:
                if len(finished_rounds) >= target_canary_sessions and non_interrupted >= min_non_interrupted:
                    # Wait 4 seconds so the round's post-return utility AI ticks and flush complete
                    time.sleep(4.0)
                    finished_rounds, status_by_round = read_canary_sessions(CANARY_JSONL)
                    print(
                        f"[{label}] Reached target_canary_sessions={target_canary_sessions} "
                        f"done={len(finished_rounds)} statuses={status_by_round} elapsed={elapsed:.1f}s",
                        flush=True,
                    )
                    break
            elif target_shadow_rounds > 0:
                if len(shadow_rounds) >= target_shadow_rounds and shadow_lines >= 60:
                    time.sleep(4.0)
                    print(
                        f"[{label}] Reached target_shadow_rounds={target_shadow_rounds} "
                        f"shadow_rounds={sorted(shadow_rounds)} shadow_lines={shadow_lines} elapsed={elapsed:.1f}s",
                        flush=True,
                    )
                    break

            if elapsed >= max_wait_s:
                print(f"[{label}] Timeout max_wait_s={max_wait_s} reached.", flush=True)
                break

            time.sleep(2.0)

    kill_existing_cs2()
    finished_rounds, status_by_round = read_canary_sessions(CANARY_JSONL)
    shadow_lines, shadow_rounds = read_shadow_rounds(SHADOW_JSONL)
    return {
        "label": label,
        "elapsed_s": round(time.time() - t0, 2),
        "finished_rounds": sorted(finished_rounds),
        "status_by_round": {str(k): v for k, v in sorted(status_by_round.items())},
        "shadow_rounds": sorted(shadow_rounds),
        "shadow_lines": shadow_lines,
    }


def copy_experiment_artifacts(prefix: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mapping = {
        CANARY_JSONL: OUT_DIR / f"{prefix}_canary_telemetry.jsonl",
        AUTH_TICKS_JSONL: OUT_DIR / f"{prefix}_authority_ticks.jsonl",
        AUTH_ACC_JSON: OUT_DIR / f"{prefix}_authority_accounting.json",
        COMP_WRITERS_JSON: OUT_DIR / f"{prefix}_competing_writers.json",
        SHADOW_JSONL: OUT_DIR / f"{prefix}_shadow_telemetry.jsonl",
    }
    for src, dst in mapping.items():
        if src.exists():
            shutil.copy2(src, dst)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["exp_a", "exp_b", "exp_d", "exp_c_smoke", "experiments", "canary10"], required=True)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    restore_external_plugins()

    try:
        if args.phase in ("exp_a", "experiments"):
            set_flags(enabled=True, isolation_mode="BASELINE_NO_ISOLATION", fast_rounds=True)
            run_cs2_until("exp_a", target_canary_sessions=2, target_shadow_rounds=0, max_wait_s=240)
            copy_experiment_artifacts("exp_a")

        if args.phase in ("exp_b", "experiments"):
            try:
                disable_external_plugins()
                set_flags(enabled=True, isolation_mode="EXTERNAL_PLUGINS_DISABLED", fast_rounds=True)
                run_cs2_until("exp_b", target_canary_sessions=2, target_shadow_rounds=0, max_wait_s=240)
                copy_experiment_artifacts("exp_b")
            finally:
                restore_external_plugins()

        if args.phase in ("exp_d", "experiments"):
            restore_external_plugins()
            set_flags(enabled=False, isolation_mode="CANARY_DISABLED", fast_rounds=True)
            run_cs2_until("exp_d", target_canary_sessions=0, target_shadow_rounds=2, max_wait_s=240)
            copy_experiment_artifacts("exp_d")

        if args.phase in ("exp_c_smoke", "experiments"):
            restore_external_plugins()
            set_flags(enabled=True, isolation_mode="LEASE_ISOLATED", fast_rounds=True)
            run_cs2_until("exp_c_smoke", target_canary_sessions=3, target_shadow_rounds=0, max_wait_s=300, min_non_interrupted=3)
            copy_experiment_artifacts("exp_c")
            if CANARY_JSONL.exists():
                shutil.copy2(CANARY_JSONL, OUT_DIR / "three_route_smoke_telemetry.jsonl")

        if args.phase == "canary10":
            restore_external_plugins()
            set_flags(enabled=True, isolation_mode="LEASE_ISOLATED", fast_rounds=True)
            run_cs2_until("canary10", target_canary_sessions=10, target_shadow_rounds=0, max_wait_s=900, min_non_interrupted=8)
            copy_experiment_artifacts("canary10")
            if CANARY_JSONL.exists():
                shutil.copy2(CANARY_JSONL, OUT_DIR / "ct_canary_telemetry.jsonl")
            if ROUTES_SNAP_JSON.exists():
                shutil.copy2(ROUTES_SNAP_JSON, OUT_DIR / "ct_opening_routes_snapshot.json")
    finally:
        restore_external_plugins()
        set_flags(enabled=True, isolation_mode="LEASE_ISOLATED", fast_rounds=False)


if __name__ == "__main__":
    main()
