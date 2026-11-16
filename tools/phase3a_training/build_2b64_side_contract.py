import json
from pathlib import Path

BASE_DIR = Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
CAT_PATH = BASE_DIR / "datasets" / "mirage_v2" / "contracts" / "mirage_spot_catalog_v3.json"
OUT_DIR = BASE_DIR / "training_runs" / "positioning_v2_real_temporal" / "csharp_shadow_integration" / "side_mask_route_fix"


def classify_spot_side(spot: dict) -> tuple[str, str]:
    sid = str(spot["id"]).lower()
    team_field = str(spot.get("team", spot.get("side", ""))).upper().strip()
    usage = str(spot.get("usage", "")).lower()

    # Checagem semântica + metadado do catálogo (não apenas prefixo)
    if team_field in ("CT", "CT_ONLY"):
        return "CT_ONLY", f"catalog_team={team_field}"
    if team_field in ("T", "TR", "T_ONLY"):
        return "T_ONLY", f"catalog_team={team_field}"
    if team_field in ("BOTH", "SHARED", "ANY"):
        return "SHARED", f"catalog_team={team_field}"

    # Fallback semântico explícito caso algum spot não tenha team preenchido
    if "retake" in sid or "defuse" in sid or sid.startswith("ct_"):
        return "CT_ONLY", "semantic_ct_retake_or_defense"
    if "plant" in sid or "postplant" in sid or "execute" in sid or "lurk" in sid or sid.startswith("tr_") or sid.startswith("t_"):
        return "T_ONLY", "semantic_t_execute_or_postplant"
    return "SHARED", "semantic_shared_map_control"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(CAT_PATH, "r", encoding="utf-8") as f:
        cat = json.load(f)
    spots = cat["spots"]
    assert len(spots) == 53, f"Expected 53 spots, got {len(spots)}"

    entries = []
    ct_mask = []
    t_mask = []
    counts = {"CT_ONLY": 0, "T_ONLY": 0, "SHARED": 0}

    for i, s in enumerate(spots):
        side_class, reason = classify_spot_side(s)
        counts[side_class] += 1
        ct_allowed = side_class in ("CT_ONLY", "SHARED")
        t_allowed = side_class in ("T_ONLY", "SHARED")
        ct_mask.append(ct_allowed)
        t_mask.append(t_allowed)
        entries.append(
            {
                "index": i,
                "spot_id": s["id"],
                "catalog_team": s.get("team", s.get("side", "")),
                "usage": s.get("usage", ""),
                "side_class": side_class,
                "ct_allowed": ct_allowed,
                "t_allowed": t_allowed,
                "radius": float(s.get("radius", 90.0)),
                "reason": reason,
            }
        )

    contract = {
        "contract_version": "spot_side_contract_v1",
        "catalog_version": cat.get("catalog_version", "v3.0.0"),
        "spot_count": len(spots),
        "counts": counts,
        "ct_allowed_mask": ct_mask,
        "t_allowed_mask": t_mask,
        "spots": entries,
    }
    out_path = OUT_DIR / "spot_side_contract_v1.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, ensure_ascii=False)
    print(f"SIDE_CONTRACT_OK counts={counts} ct_allowed={sum(ct_mask)} t_allowed={sum(t_mask)}")


if __name__ == "__main__":
    main()
