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
PLUGIN_LOGS = SERVER_DIR / "game" / "csgo" / "addons" / "counterstrikesharp" / "plugins" / "CsBotManager" / "logs"
SHADOW_JSONL = PLUGIN_LOGS / "positioning_shadow_telemetry.jsonl"
DEBUG_LOGS = SERVER_DIR / "debug_logs"
LIVE_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "live_capture"


CANARY_JSONL = SERVER_DIR / "game" / "csgo" / "addons" / "counterstrikesharp" / "plugins" / "CsBotManager" / "logs" / "opening_canary_telemetry.jsonl"


def read_canary_completed_sessions(path: Path) -> int:
    if not path.exists():
        return 0
    finished_rounds = set()
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("authority_return_tick") is not None:
                    finished_rounds.add(int(rec.get("round", 0)))
            except Exception:
                pass
    return len(finished_rounds)


def read_jsonl_progress(path: Path) -> tuple[int, set[int]]:
    if not path.exists():
        return 0, set()
    lines = 0
    rounds = set()
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            lines += 1
            try:
                rec = json.loads(line)
                rounds.add(int(rec.get("round_id", 0)))
            except Exception:
                pass
    return lines, rounds


def kill_existing_cs2() -> None:
    subprocess.run(["taskkill", "/F", "/IM", "cs2.exe"], capture_output=True)
    time.sleep(2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["smoke", "full_match"], required=True)
    parser.add_argument("--out-dir", type=str, default="")
    parser.add_argument("--target-rounds", type=int, default=0)
    parser.add_argument("--target-canary-sessions", type=int, default=0)
    parser.add_argument("--max-wait-s", type=int, default=0)
    args = parser.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else LIVE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    PLUGIN_LOGS.mkdir(parents=True, exist_ok=True)
    DEBUG_LOGS.mkdir(parents=True, exist_ok=True)

    kill_existing_cs2()
    if SHADOW_JSONL.exists():
        SHADOW_JSONL.unlink()

    console_log = DEBUG_LOGS / f"{args.mode}_2b61_console.log"
    if console_log.exists():
        console_log.unlink()

    match_flag = DEBUG_LOGS / "match_completed.flag"
    utility_jsonl = DEBUG_LOGS / "profile_v2_normal_match_events.jsonl"
    if args.mode == "full_match":
        if match_flag.exists():
            match_flag.unlink()
        if utility_jsonl.exists():
            utility_jsonl.unlink()

    if args.mode == "smoke":
        target_rounds = args.target_rounds if args.target_rounds > 0 else 4  # rounds 1,2,3 completos -> entra no round 4
        max_wait_s = args.max_wait_s if args.max_wait_s > 0 else 630   # até 10.5 min
        dest_jsonl = out_dir / "smoke_shadow_telemetry.jsonl"
        extra_args = ["+mp_warmuptime", "5", "+css_debug", "5"]
    else:
        target_rounds = args.target_rounds if args.target_rounds > 0 else 24 # partida competitiva completa
        max_wait_s = args.max_wait_s if args.max_wait_s > 0 else 3600  # até 60 min
        dest_jsonl = out_dir / "full_match_shadow_telemetry.jsonl"
        extra_args = ["+mp_warmuptime", "5", "+css_debug", "5"]

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
        *extra_args,
    ]

    t0 = time.time()
    crashed = False
    with open(console_log, "w", encoding="utf-8", errors="replace") as log_f:
        proc = subprocess.Popen(
            cmd,
            cwd=str(SERVER_DIR),
            stdout=log_f,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )

        last_report = 0.0
        while True:
            elapsed = time.time() - t0
            rc = proc.poll()
            if rc is not None:
                crashed = True
                print(f"[{args.mode}] CS2 exited early rc={rc} elapsed={elapsed:.1f}s")
                break

            lines, rounds = read_jsonl_progress(SHADOW_JSONL)
            max_round = max(rounds) if rounds else 0

            if elapsed - last_report >= 30.0:
                print(f"[{args.mode}] elapsed={elapsed:.0f}s lines={lines} rounds={sorted(rounds)}", flush=True)
                last_report = elapsed

            # No full_match, também verifica se match_completed ou mp_maxrounds terminou no console
            if args.mode == "smoke":
                canary_sessions = read_canary_completed_sessions(CANARY_JSONL) if args.target_canary_sessions > 0 else 0
                if args.target_canary_sessions > 0 and canary_sessions >= args.target_canary_sessions:
                    print(f"[{args.mode}] Reached target_canary_sessions={args.target_canary_sessions} (observed={canary_sessions}) max_round={max_round} lines={lines}", flush=True)
                    break
                if max_round >= target_rounds and lines >= 100:
                    print(f"[{args.mode}] Reached target_rounds={target_rounds} lines={lines} canary_sessions={canary_sessions}", flush=True)
                    break
            else:
                if match_flag.exists():
                    print(f"[{args.mode}] match_completed.flag detected max_round={max_round} lines={lines}", flush=True)
                    time.sleep(3)
                    break

            if elapsed >= max_wait_s:
                print(f"[{args.mode}] Reached max_wait_s={max_wait_s}s lines={lines} rounds={sorted(rounds)}", flush=True)
                break

            time.sleep(5)

        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)

    kill_existing_cs2()
    if SHADOW_JSONL.exists():
        shutil.copy2(SHADOW_JSONL, dest_jsonl)

    lines, rounds = read_jsonl_progress(dest_jsonl)
    shutil.copy2(console_log, out_dir / f"{args.mode}_console.log")
    if args.mode == "full_match" and utility_jsonl.exists():
        shutil.copy2(utility_jsonl, out_dir / "utility_ai_events.jsonl")
    print(f"CAPTURE_DONE mode={args.mode} crashed={crashed} lines={lines} rounds={sorted(rounds)} dest={dest_jsonl}")


if __name__ == "__main__":
    main()
