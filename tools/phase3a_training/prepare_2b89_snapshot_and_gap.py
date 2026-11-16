import hashlib
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("training_runs/positioning_v2_real_temporal/opening_route_canary_v1")
SRC_DIAG = BASE / "tr_live_diagnostic_patch_v1"
OUT_DIR = BASE / "tr_canonical_route_runtime_v1"
SNAP_DIR = OUT_DIR / "_snapshot"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SNAP_DIR.mkdir(parents=True, exist_ok=True)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(txt: str) -> str:
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()


FILES_TO_SNAPSHOT = [
    Path("src/CsBotManager/GeometricTransitionPlanner.cs"),
    Path("src/CsBotManager/OpeningRouteCanaryController.cs"),
    Path("src/CsBotManager/OpeningRoutePlanner.cs"),
    Path("src/CsBotManager/BotLocomotionDriver.cs"),
    Path("src/CsBotManager/MovementArbitrator.cs"),
    Path("src/CsBotManager/MovementAuthorityIsolation.cs"),
    Path("src/CsBotManager/NavMeshGraph.cs"),
    SRC_DIAG / "first_failure_tick_analysis.json",
    SRC_DIAG / "failure_coordinate_clusters.json",
    SRC_DIAG / "per_route_patch_manifest.json",
    SRC_DIAG / "solo_confirmation_telemetry.jsonl",
]

now_utc = datetime.now(timezone.utc).isoformat()
snap_entries = []
for p in FILES_TO_SNAPSHOT:
    if p.exists():
        dst = SNAP_DIR / p.name
        if p.stat().st_size <= 150_000_000:
            shutil.copy2(p, dst)
        snap_entries.append({
            "path": str(p).replace("\\", "/"),
            "snapshot_copy": str(dst).replace("\\", "/"),
            "size_bytes": p.stat().st_size,
            "sha256": sha256_file(p),
        })

(OUT_DIR / "canonical_route_input_snapshot.json").write_text(json.dumps({
    "marco": "2B.8.9",
    "data_nature": "REAL_CONTRACT",
    "generated_at_utc": now_utc,
    "files": snap_entries,
}, indent=2), encoding="utf-8")

# Extract protected method blocks from GeometricTransitionPlanner.cs for bitwise regression check
gtp_text = Path("src/CsBotManager/GeometricTransitionPlanner.cs").read_text(encoding="utf-8")
def extract_method(src: str, sig: str) -> str:
    idx = src.find(sig)
    if idx < 0:
        return ""
    brace = src.find("{", idx)
    if brace < 0:
        return ""
    depth = 0
    for i in range(brace, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[idx:i+1]
    return ""

protected = {
    "CT_A": extract_method(gtp_text, "BuildCtATicketTransitions"),
    "CT_WINDOW_VENTS": extract_method(gtp_text, "BuildCtMidWindowTransitions"),
    "CT_MARKET_B": extract_method(gtp_text, "BuildCtBMarketTransitions"),
    "TR_MID_TOP": extract_method(gtp_text, "BuildTrMidTopTransitions"),
    "TR_UNDERPASS": extract_method(gtp_text, "BuildTrUnderpassTransitions"),
}
protected_hashes = {k: {"sha256": sha256_text(v), "length": len(v)} for k, v in protected.items()}
(OUT_DIR / "protected_route_hashes.json").write_text(json.dumps({
    "marco": "2B.8.9",
    "data_nature": "REAL_CONTRACT",
    "generated_at_utc": now_utc,
    "protected_routes": protected_hashes,
}, indent=2), encoding="utf-8")

# Section 3: goal_ownership_gap.json from solo_confirmation_telemetry.jsonl
telem_path = SRC_DIAG / "solo_confirmation_telemetry.jsonl"
total_ticks = 0
divergent_ticks = 0
false_unauth_with_div = 0
sample_gaps = []
with telem_path.open("r", encoding="utf-8", errors="replace") as f:
    for idx, line in enumerate(f):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        ga = r.get("goal_after_canary")
        ge = r.get("goal_end_of_tick")
        if ga and ge and len(ga) == 3 and len(ge) == 3:
            total_ticks += 1
            dxy = math.hypot(ga[0] - ge[0], ga[1] - ge[1])
            dz = abs(ga[2] - ge[2])
            same = (dxy <= 4.0 and dz <= 4.0)
            if not same:
                divergent_ticks += 1
                if not r.get("unauthorized_overwrite", False):
                    false_unauth_with_div += 1
                if len(sample_gaps) < 200:
                    sample_gaps.append({
                        "session_id": f"{r.get('cert_route', '')}_r{r.get('round', 0)}",
                        "round": r.get("round"),
                        "tick": idx,
                        "current_waypoint": r.get("current_waypoint"),
                        "command_id": r.get("command_id"),
                        "dispatch_reason": r.get("dispatch_reason"),
                        "goal_before_canary": r.get("goal_before_canary"),
                        "requested_canary_goal": ga,
                        "goal_after_canary": ga,
                        "goal_end_of_tick": ge,
                        "native_state": r.get("executor_state"),
                        "competing_writers_suppressed": r.get("competing_writers_suppressed", 0),
                        "unauthorized_overwrite": bool(r.get("unauthorized_overwrite", False)),
                        "movement_intent_source": r.get("authority", ""),
                        "movement_intent_priority": 100 if r.get("authority") == "OPENING_ROUTE_PLANNER" else 0,
                        "lease_owner": r.get("authority", ""),
                        "goal_delta": {"xy": round(dxy, 2), "z": round(dz, 2)},
                        "same_goal_within_tolerance": False,
                        "goal_owned_at_end_of_tick": False,
                    })

(OUT_DIR / "goal_ownership_gap.json").write_text(json.dumps({
    "marco": "2B.8.9",
    "data_nature": "REAL",
    "generated_at_utc": now_utc,
    "tolerance": {"xy_max": 4.0, "z_max": 4.0},
    "total_ticks_with_goals": total_ticks,
    "divergent_ticks": divergent_ticks,
    "divergent_with_unauthorized_overwrite_false": false_unauth_with_div,
    "goal_ownership_agreement_rate": round((total_ticks - divergent_ticks) / total_ticks, 4) if total_ticks else 0.0,
    "gaps_sample_first_200": sample_gaps,
}, indent=2), encoding="utf-8")

print(f"PREPARE_2B89_DONE: total_ticks={total_ticks} divergent={divergent_ticks} false_unauth={false_unauth_with_div} protected_keys={list(protected_hashes.keys())}")
