import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

from tools.phase3a_training.run_marco_2b5_onnx_export import load_supervised_spot_mask

BASE_DIR = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
LIVE_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "live_capture"

VALID_STATES = {"TRANSIT", "CLEARANCE", "STAGING", "HOLD", "OBJECTIVE", "RETAKE"}
VALID_SECTORS = {"A", "B", "MID", "CT", "T"}
REQUIRED_FIELDS = [
    "timestamp", "map", "match_id", "round_id", "tick", "player_slot", "team",
    "model_hash", "contract_version", "input_valid", "inference_success", "latency_ms",
    "utility_state", "neural_state", "utility_sector", "neural_sector",
    "utility_spot", "neural_spot", "neural_transition", "neural_exit_trigger",
    "confidence_by_head", "objective_eligible", "retake_eligible",
    "save_fallback_active", "fallback_reason",
]


def percentile(sorted_vals: List[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = min(len(sorted_vals) - 1, max(0, int(math.ceil(q * len(sorted_vals))) - 1))
    return sorted_vals[idx]


def analyze_jsonl(jsonl_path: Path, console_path: Path, sup_mask: List[bool]) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    console_text = console_path.read_text(encoding="utf-8", errors="replace") if console_path.exists() else ""
    load_count = console_text.count("[CsBotManager][PositioningShadow] LoadModel=True")
    load_fail_count = console_text.count("[CsBotManager][PositioningShadow] LoadModel=False")

    total = len(records)
    valid_inputs = sum(1 for r in records if r.get("input_valid") is True)
    successes = sum(1 for r in records if r.get("inference_success") is True)
    timeouts = sum(1 for r in records if "TIMEOUT" in str(r.get("fallback_reason", "")))
    failures = sum(1 for r in records if not r.get("inference_success", False))
    dropped = sum(1 for r in records if "QUEUE" in str(r.get("fallback_reason", "")) or "DROPPED" in str(r.get("fallback_reason", "")))

    missing_fields = 0
    bad_bounds = 0
    unsupervised_spot = 0
    neural_save_count = 0
    illegal_objective = 0
    illegal_retake = 0
    utility_violations = 0
    raw_identifier_leaks = 0

    latencies: List[float] = []
    fallback_reasons = Counter()
    rejection_reasons = Counter()
    neural_state_dist = Counter()
    neural_sector_dist = Counter()
    rounds = set()

    for r in records:
        rounds.add(int(r.get("round_id", 0)))
        for k in REQUIRED_FIELDS:
            if k not in r:
                missing_fields += 1
        if r.get("input_valid"):
            latencies.append(float(r.get("latency_ms", 0.0)))
        else:
            rejection_reasons[str(r.get("fallback_reason", "UNKNOWN"))] += 1

        fallback_reasons[str(r.get("fallback_reason", ""))] += 1

        st = str(r.get("neural_state", ""))
        sec = str(r.get("neural_sector", ""))
        neural_state_dist[st] += 1
        neural_sector_dist[sec] += 1

        if st == "SAVE":
            neural_save_count += 1
        if r.get("save_fallback_active") is not True:
            utility_violations += 1
        if st == "OBJECTIVE" and not r.get("objective_eligible", False):
            illegal_objective += 1
        if st == "RETAKE" and not r.get("retake_eligible", False):
            illegal_retake += 1
        if r.get("inference_success"):
            if st not in VALID_STATES or sec not in VALID_SECTORS:
                bad_bounds += 1
            try:
                spot_idx = int(r.get("neural_spot", -1))
                if not (0 <= spot_idx < len(sup_mask)) or not sup_mask[spot_idx]:
                    unsupervised_spot += 1
            except Exception:
                bad_bounds += 1

        pslot = str(r.get("player_slot", ""))
        if len(pslot) != 12 or "7656119" in pslot:
            raw_identifier_leaks += 1

    latencies.sort()
    p50 = round(percentile(latencies, 0.50), 4)
    p95 = round(percentile(latencies, 0.95), 4)
    p99 = round(percentile(latencies, 0.99), 4)
    mean_ms = round(sum(latencies) / max(1, len(latencies)), 4)

    success_rate = successes / max(1, total)
    timeout_rate = timeouts / max(1, total)
    dropped_rate = dropped / max(1, total)

    gates_pass = (
        total > 0
        and missing_fields == 0
        and bad_bounds == 0
        and unsupervised_spot == 0
        and neural_save_count == 0
        and illegal_objective == 0
        and illegal_retake == 0
        and utility_violations == 0
        and raw_identifier_leaks == 0
        and success_rate >= 0.999
        and timeout_rate == 0.0
        and dropped_rate < 0.001
        and load_count <= 1
        and load_fail_count == 0
        and p95 <= 15.0
        and p99 <= 20.0
    )

    return {
        "provenance": "REAL_LIVE_CS2_SERVER",
        "total_inferences": total,
        "valid_inputs": valid_inputs,
        "rejected_inputs": total - valid_inputs,
        "successful_inferences": successes,
        "inference_success_rate": round(success_rate, 6),
        "failures": failures,
        "timeouts": timeouts,
        "timeout_rate": round(timeout_rate, 6),
        "dropped_requests": dropped,
        "dropped_request_rate": round(dropped_rate, 6),
        "rounds_observed": sorted(rounds),
        "model_load_count_in_log": load_count,
        "model_load_fail_count_in_log": load_fail_count,
        "latency_ms": {"p50": p50, "p95": p95, "p99": p99, "mean": mean_ms},
        "integrity_checks": {
            "missing_fields": missing_fields,
            "bad_bounds": bad_bounds,
            "unsupervised_spot_selections": unsupervised_spot,
            "neural_save_predictions": neural_save_count,
            "illegal_objective": illegal_objective,
            "illegal_retake": illegal_retake,
            "utility_authority_violations": utility_violations,
            "raw_identifier_leaks": raw_identifier_leaks,
        },
        "fallback_by_reason": dict(fallback_reasons),
        "rejection_by_reason": dict(rejection_reasons),
        "neural_state_distribution": dict(neural_state_dist),
        "neural_sector_distribution": dict(neural_sector_dist),
        "gates_pass": gates_pass,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["smoke"], required=True)
    args = parser.parse_args()

    sup_mask = [bool(x > 0.5) for x in load_supervised_spot_mask().tolist()]

    res = analyze_jsonl(
        LIVE_DIR / "smoke_shadow_telemetry.jsonl",
        LIVE_DIR / "smoke_console.log",
        sup_mask,
    )
    out = LIVE_DIR / "smoke_runtime_metrics.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"SMOKE_AUDIT gates_pass={res['gates_pass']} total={res['total_inferences']} success={res['inference_success_rate']} p95={res['latency_ms']['p95']} p99={res['latency_ms']['p99']} rounds={res['rounds_observed']}")


if __name__ == "__main__":
    main()
