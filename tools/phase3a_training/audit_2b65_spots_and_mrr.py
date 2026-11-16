import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from tools.phase3a_training.run_marco_2b5_onnx_export import (
    BASE_DIR,
    DS_DIR,
    INDEX_DIR,
    load_supervised_spot_mask,
)

OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "side_contract_v2"
CAT_PATH = DS_DIR / "contracts" / "mirage_spot_catalog_v3.json"
UTILITY_EVENTS_PATH = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "full_match_capture" / "utility_ai_events.jsonl"


def infer_side_from_name(sid: str) -> str:
    s = sid.lower()
    if s.startswith("ct_") or "retake" in s or "defuse" in s:
        return "CT"
    if s.startswith("tr_") or s.startswith("t_") or "plant" in s or "lurk" in s:
        return "T"
    return "NEUTRAL"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(CAT_PATH, "r", encoding="utf-8") as f:
        cat = json.load(f)
    spots = cat["spots"]
    sup_mask = load_supervised_spot_mask().numpy() > 0.5

    # Contagens por split x lado x estado
    support = defaultdict(lambda: Counter())
    state_by_spot = defaultdict(Counter)

    cols = ["split", "team", "CandidateSpotId", "SpotLossMask", "PositioningState"]
    for p in sorted(INDEX_DIR.glob("shard_*.parquet")):
        df = pd.read_parquet(p, columns=cols)
        df = df[df["SpotLossMask"].astype(bool)]
        for sp_id, spl, tm, st in zip(df["CandidateSpotId"], df["split"], df["team"], df["PositioningState"]):
            tm_norm = "T" if str(tm).upper() in ("T", "TR") else "CT"
            support[sp_id][(str(spl), tm_norm)] += 1
            state_by_spot[sp_id][str(st)] += 1

    # Contagens de atribuições da Utility AI na partida completa
    util_ct = Counter()
    util_t = Counter()
    util_evs: List[Dict[str, Any]] = []
    if UTILITY_EVENTS_PATH.exists():
        with open(UTILITY_EVENTS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                ev = json.loads(line)
                if ev.get("EventType") == "SPOT_ASSIGNED":
                    util_evs.append(ev)
                    sp = str(ev.get("SpotId", ""))
                    if str(ev.get("Team", "")).upper() in ("TR", "T"):
                        util_t[sp] += 1
                    else:
                        util_ct[sp] += 1

    accounting_rows = []
    conflict_rows = []
    contract_v2_spots = []

    for idx, s in enumerate(spots):
        sid = str(s["id"])
        cat_team = str(s.get("team", s.get("side", "BOTH"))).upper()
        name_side = infer_side_from_name(sid)
        usage = str(s.get("usage", ""))

        tr_ct = int(support[sid][("train", "CT")])
        tr_t = int(support[sid][("train", "T")])
        va_ct = int(support[sid][("validation", "CT")])
        va_t = int(support[sid][("validation", "T")])
        te_ct = int(support[sid][("test", "CT")])
        te_t = int(support[sid][("test", "T")])

        u_ct = int(util_ct[sid])
        u_t = int(util_t[sid])
        tot_ct = tr_ct + va_ct
        tot_t = tr_t + va_t

        # Reconciliação semântica rigorosa (usando apenas catálogo, semântica física, Train/Val — nunca Test!)
        sid_l = sid.lower()
        if "plant" in sid_l:
            rec_cls = "CONTEXTUAL"
            purpose = "Plant / post-plant position (TR OBJECTIVE; CT only in retake/defuse context, never CT opening)"
            ct_rule = "RETAKE_ONLY"
            t_rule = "OBJECTIVE_OR_POSTPLANT"
            conflict = "CT assigned to plant spot in Utility AI" if u_ct > 0 else ("CT label in Train/Val" if tot_ct > 0 else "NONE")
        elif "retake" in sid_l:
            rec_cls = "CONTEXTUAL" if tot_t > 0 else "CT_ONLY"
            purpose = "Retake approach/clear waypoint (CT in RETAKE; physically traversed by TR if map area shared)"
            ct_rule = "RETAKE_OR_HOLD"
            t_rule = "ALLOWED_SHARED_GEOMETRY_ONLY" if tot_t > 0 else "FORBIDDEN"
            conflict = "T_SUPPORT_IN_CT_RETAKE_SPOT" if tot_t > 0 or u_t > 0 else "NONE"
        elif cat_team in ("BOTH", "SHARED", "ANY") or (tot_ct > 0 and tot_t > 0 and min(tot_ct, tot_t) / max(1, tot_ct + tot_t) >= 0.05):
            rec_cls = "SHARED"
            purpose = "Physically shared tactical position occupied by both CT and T"
            ct_rule = "ALWAYS_ALLOWED"
            t_rule = "ALWAYS_ALLOWED"
            conflict = "CATALOG_TEAM_NARROWER_THAN_DATA" if cat_team in ("CT", "T", "TR") else "NONE"
        elif cat_team in ("CT",) and tot_t == 0:
            rec_cls = "CT_ONLY"
            purpose = "CT-exclusive defensive/anchor position"
            ct_rule = "ALWAYS_ALLOWED"
            t_rule = "FORBIDDEN"
            conflict = "T_UTILITY_ASSIGNMENT_CONFLICT" if u_t > 0 else "NONE"
        elif cat_team in ("TR", "T") and tot_ct == 0:
            rec_cls = "T_ONLY"
            purpose = "T-exclusive staging/execute/spawn-side position"
            ct_rule = "FORBIDDEN"
            t_rule = "ALWAYS_ALLOWED"
            conflict = "CT_UTILITY_ASSIGNMENT_CONFLICT" if u_ct > 0 else "NONE"
        else:
            rec_cls = "CATALOG_REVIEW_REQUIRED"
            purpose = f"Mixed/ambiguous support (Train+Val CT={tot_ct}, T={tot_t}, catalog={cat_team})"
            ct_rule = "ALLOWED" if tot_ct > 0 else "FORBIDDEN"
            t_rule = "ALLOWED" if tot_t > 0 else "FORBIDDEN"
            conflict = f"SIDE_SUPPORT_MISMATCH(cat={cat_team}, CT={tot_ct}, T={tot_t})"

        row = {
            "index": idx,
            "spot_id": sid,
            "supervised": bool(sup_mask[idx]),
            "catalog_side": cat_team,
            "inferred_side_from_name": name_side,
            "train_support_ct": tr_ct,
            "train_support_t": tr_t,
            "validation_support_ct": va_ct,
            "validation_support_t": va_t,
            "test_support_ct": te_ct,
            "test_support_t": te_t,
            "assigned_by_utility_ct": u_ct,
            "assigned_by_utility_t": u_t,
            "top_states": dict(state_by_spot[sid].most_common(3)),
            "semantic_purpose": purpose,
            "recommended_classification": rec_cls,
            "conflict_reason": conflict,
        }
        accounting_rows.append(row)
        if conflict != "NONE":
            conflict_rows.append(row)

        contract_v2_spots.append(
            {
                "index": idx,
                "spot_id": sid,
                "supervised": bool(sup_mask[idx]),
                "classification": rec_cls,
                "ct_rule": ct_rule,
                "t_rule": t_rule,
                "semantic_purpose": purpose,
            }
        )

    # Auditar atribuições da Utility AI (Seção 7)
    spot_cls_map = {r["spot_id"]: r["recommended_classification"] for r in accounting_rows}
    spot_cat_map = {r["spot_id"]: r["catalog_side"] for r in accounting_rows}
    util_audit_counts = Counter()
    util_bad_examples = []
    for ev in util_evs:
        sp = str(ev.get("SpotId", ""))
        tm = "T" if str(ev.get("Team", "")).upper() in ("TR", "T") else "CT"
        cat_side = spot_cat_map.get(sp, "UNKNOWN")
        cls = spot_cls_map.get(sp, "UNKNOWN")
        stage = str(ev.get("PlanStage", ""))

        if cls == "UNKNOWN":
            verdict = "UNKNOWN"
        elif "plant" in sp.lower() and tm == "CT" and stage in ("OPENING", "FAST_CONTACT", "SETUP"):
            verdict = "WRONG_PHASE"
        elif cat_side == "CT" and tm == "T" and cls == "CT_ONLY":
            verdict = "WRONG_SIDE"
        elif cat_side in ("TR", "T") and tm == "CT" and cls == "T_ONLY":
            verdict = "WRONG_SIDE"
        elif cls == "CONTEXTUAL":
            verdict = "VALID_CONTEXTUAL"
        elif cls == "CATALOG_REVIEW_REQUIRED":
            verdict = "WRONG_SIDE" if ((cat_side == "CT" and tm == "T") or (cat_side in ("TR", "T") and tm == "CT")) else "VALID_CONTEXTUAL"
        else:
            verdict = "VALID"
        util_audit_counts[verdict] += 1
        if verdict in ("WRONG_SIDE", "WRONG_PHASE") and len(util_bad_examples) < 25:
            util_bad_examples.append(
                {
                    "round": ev.get("InternalRoundId"),
                    "team": tm,
                    "plan_stage": stage,
                    "spot_id": sp,
                    "catalog_side": cat_side,
                    "verdict": verdict,
                }
            )

    with open(OUT_DIR / "spot_side_support_accounting.json", "w", encoding="utf-8") as f:
        json.dump({"provenance": "REAL", "spot_count": len(accounting_rows), "spots": accounting_rows}, f, indent=2, ensure_ascii=False)

    with open(OUT_DIR / "spot_side_conflict_report.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "provenance": "REAL",
                "conflict_count": len(conflict_rows),
                "classification_counts": dict(Counter(r["recommended_classification"] for r in accounting_rows)),
                "conflicts": conflict_rows,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    with open(OUT_DIR / "spot_side_contract_v2.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "contract_version": "spot_side_contract_v2",
                "spot_count": len(contract_v2_spots),
                "classification_counts": dict(Counter(s["classification"] for s in contract_v2_spots)),
                "spots": contract_v2_spots,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    with open(OUT_DIR / "utility_spot_assignment_audit.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "provenance": "REAL_LIVE_CS2_SERVER",
                "total_utility_assignments": len(util_evs),
                "verdict_counts": dict(util_audit_counts),
                "invalid_examples": util_bad_examples,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"AUDIT_2B65_OK conflicts={len(conflict_rows)} "
        f"classes={dict(Counter(r['recommended_classification'] for r in accounting_rows))} "
        f"util_audit={dict(util_audit_counts)}"
    )


if __name__ == "__main__":
    main()
