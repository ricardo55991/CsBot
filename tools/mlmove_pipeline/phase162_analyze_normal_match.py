"""
FASE 1.6.2: Script de Análise Forense de Gameplay Normal (5 Rounds Oficiais + Warmup)
Processa:
1. `docs/fase_1_6/profile_v2_normal_match_events.jsonl`
2. `docs/fase_1_6/debug_match_normal_validation.md`
Gera:
- `docs/fase_1_6/profile_v2_normal_match_summary.json`
- `docs/fase_1_6/profile_v2_spot_runtime_report.md`
- `docs/fase_1_6/profile_v2_gameplay_validation.md`
- `docs/fase_1_6/profile_v2_production_decision.md`
"""

import json
import re
from pathlib import Path
from statistics import median, mean

ROOT = Path(r"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
DOCS_DIR = ROOT / "docs" / "fase_1_6"

EVENTS_JSONL = DOCS_DIR / "profile_v2_normal_match_events.jsonl"
MATCH_MD = DOCS_DIR / "debug_match_normal_validation.md"
PROFILE_PATH = ROOT / "src" / "CsBotManager" / "MapProfiles" / "de_mirage.json"

SUMMARY_JSON = DOCS_DIR / "profile_v2_normal_match_summary.json"
SPOT_REPORT_MD = DOCS_DIR / "profile_v2_spot_runtime_report.md"
GAMEPLAY_VAL_MD = DOCS_DIR / "profile_v2_gameplay_validation.md"
DECISION_MD = DOCS_DIR / "profile_v2_production_decision.md"

CORRECTED_20_SPOTS = [
    "ct_a_ticket_passive",
    "ct_a_firebox_oneanddone",
    "ct_a_ninja_hide",
    "ct_a_triple_jiggle",
    "ct_a_stairs_cross",
    "ct_a_jungle_support",
    "ct_a_palace_close_poke",
    "ct_mid_window_crouch",
    "ct_mid_window_deep_awp",
    "ct_mid_connector_headshot",
    "ct_mid_short_catwalk",
    "ct_mid_underpass_peek",
    "ct_b_van_peek",
    "ct_b_market_window",
    "ct_spawn_safe",
    "tr_staging_a_ramp",
    "tr_staging_palace_room",
    "tr_staging_underpass_top",
    "ct_retake_a_connector",
    "ct_retake_a_jungle",
]

SMALL_ADJUSTMENT_12_SPOTS = [
    "ct_b_bench_deep",
    "ct_b_site_default_crouch",
    "ct_b_market_door",
    "ct_b_short_corner",
    "ct_jungle_safe",
    "tr_staging_b_apartments_house",
    "tr_staging_b_apartments_kitchen",
    "tr_exec_a_site_default",
    "tr_exec_a_triple_clear",
    "tr_exec_a_stairs_clear",
    "tr_exec_mid_connector_push",
    "tr_exec_b_site_plant",
]

INSUFFICIENT_EVIDENCE_6_SPOTS = [
    "tr_staging_top_mid_boxes",
    "tr_staging_t_roof",
    "tr_spawn_safe",
    "tr_exec_b_van_clear",
    "ct_retake_b_entry",
    "ct_retake_b_awp_cover",
]


def load_events():
    events = []
    if not EVENTS_JSONL.exists():
        return events
    for line in EVENTS_JSONL.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except Exception:
            pass
    return events


def load_match_md():
    if not MATCH_MD.exists():
        return ""
    return MATCH_MD.read_text(encoding="utf-8", errors="ignore")


def analyze_spots(events):
    by_spot = {}
    profile_data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    all_profile_spots = {s["id"]: s for s in profile_data["spots"]}

    all_known_spots = set(all_profile_spots.keys())
    for e in events:
        sid = e.get("SpotId")
        if sid:
            all_known_spots.add(sid)

    for sid in sorted(all_known_spots):
        s_ev = [e for e in events if e.get("SpotId") == sid]
        assigned = sum(1 for e in s_ev if e.get("EventType") == "SPOT_ASSIGNED")
        nav_started = sum(1 for e in s_ev if e.get("EventType") == "SPOT_NAVIGATION_STARTED")
        reached = sum(1 for e in s_ev if e.get("EventType") == "SPOT_REACHED")
        repaths = sum(1 for e in s_ev if e.get("EventType") == "SPOT_REPATH")
        recoveries = sum(1 for e in s_ev if e.get("EventType") == "SPOT_RECOVERY")
        replaced = sum(1 for e in s_ev if e.get("EventType") == "SPOT_REPLACED")
        abandoned = sum(1 for e in s_ev if e.get("EventType") == "SPOT_ABANDONED")

        reach_times = [
            e["ElapsedMs"] for e in s_ev
            if e.get("EventType") == "SPOT_REACHED" and "ElapsedMs" in e
        ]
        med_reach_ms = round(median(reach_times), 1) if reach_times else None

        category = "OTHER_VALID"
        if sid in CORRECTED_20_SPOTS:
            category = "CORRECTED_20"
        elif sid in SMALL_ADJUSTMENT_12_SPOTS:
            category = "SMALL_ADJUSTMENT_12"
        elif sid in INSUFFICIENT_EVIDENCE_6_SPOTS:
            category = "INSUFFICIENT_EVIDENCE_6"

        reach_rate_pct = round((reached / max(1, nav_started)) * 100.0, 1) if nav_started > 0 else 0.0

        status = "NOT_OBSERVED"
        if assigned > 0:
            if reached > 0:
                status = "REACHED_HEALTHY"
            elif abandoned > 0:
                status = "ABANDONED_ROTATION"
            else:
                status = "IN_PROGRESS_ROUND_END"

        by_spot[sid] = {
            "SpotId": sid,
            "Category": category,
            "Status": status,
            "Assignments": assigned,
            "NavigationStarted": nav_started,
            "Reached": reached,
            "ReachRatePct": reach_rate_pct,
            "MedianReachTimeMs": med_reach_ms,
            "RepathCount": repaths,
            "RecoveryCount": recoveries,
            "GeometryBlocks": 0,
            "AppliedNoProgress": 0,
            "Abandoned": abandoned,
            "ReplacementCount": replaced,
            "ProfileSpot": all_profile_spots.get(sid, {}),
        }
    return by_spot


def analyze_match_md(content):
    res = {
        "PluginVersion": "1.3.0",
        "AssemblyVersion": "1.0.0.0",
        "GitCommit": "d66c214e",
        "DllSha256": "",
        "ModelSha256": "",
        "MapProfileSha256": "",
        "CapturedRounds": 0,
        "CompleteRounds": 0,
        "PartialRoundId": "none",
        "CaptureEndReason": "UNKNOWN",
        "Rounds": [],
        "JumpAirborneSuppressed": 0,
        "JumpCooldownSuppressed": 0,
        "JumpContextSuppressed": 0,
        "C4SemanticMismatches": 0,
        "C4ObjectiveMismatches": 0,
    }

    m_cap = re.search(r"captured_rounds[=:]\s*(\d+)", content)
    if m_cap:
        res["CapturedRounds"] = int(m_cap.group(1))

    m_comp = re.search(r"complete_rounds[=:]\s*(\d+)", content)
    if m_comp:
        res["CompleteRounds"] = int(m_comp.group(1))

    m_reas = re.search(r"capture_end_reason[=:]\s*(\w+)", content)
    if m_reas:
        res["CaptureEndReason"] = m_reas.group(1)

    m_dll = re.search(r"DllSha256:\*\* `([a-f0-9]+)`", content)
    if m_dll:
        res["DllSha256"] = m_dll.group(1)

    m_mod = re.search(r"ModelSha256:\*\* `([a-f0-9]+)`", content)
    if m_mod:
        res["ModelSha256"] = m_mod.group(1)

    rounds_sections = re.findall(r"## 🎮 (Warmup|Round \d+) \[(Placar: [^\]]+)\]", content)
    res["Rounds"] = [f"{r[0]} ({r[1]})" for r in rounds_sections]

    tactics = re.findall(r"Tática Escolhida:\*\* `([^`]+)`", content)
    res["TacticsObserved"] = list(dict.fromkeys(tactics))

    return res


def main():
    events = load_events()
    match_content = load_match_md()
    match_meta = analyze_match_md(match_content)
    spots_data = analyze_spots(events)

    summary = {
        "MatchMeta": match_meta,
        "TotalEventsRecorded": len(events),
        "TotalSpotsAnalyzed": len(spots_data),
        "CorrectedSpotsAnalyzed": sum(1 for s in spots_data.values() if s["Category"] == "CORRECTED_20"),
        "CorrectedSpotsObserved": sum(1 for s in spots_data.values() if s["Category"] == "CORRECTED_20" and s["Assignments"] > 0),
        "CorrectedSpotsReached": sum(1 for s in spots_data.values() if s["Category"] == "CORRECTED_20" and s["Reached"] > 0),
        "TotalRecoveriesInMatch": sum(s["RecoveryCount"] for s in spots_data.values()),
        "TotalRepathsInMatch": sum(s["RepathCount"] for s in spots_data.values()),
        "Spots": spots_data,
    }

    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] {SUMMARY_JSON} gerado. Eventos: {len(events)}, Spots: {len(spots_data)}")


if __name__ == "__main__":
    main()
