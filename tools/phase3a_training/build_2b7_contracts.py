"""Gera e valida os contratos determinísticos do Marco 2B.7 (Opening Route Planner v1)."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "training_runs/positioning_v2_real_temporal/opening_route_planner_v1"
CATALOG_V3_PATH = REPO_ROOT / "datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json"
SIDE_CONTRACT_V2_PATH = REPO_ROOT / "training_runs/positioning_v2_real_temporal/csharp_shadow_integration/side_contract_v2/spot_side_contract_v2.json"
DE_MIRAGE_PROFILE_PATH = REPO_ROOT / "src/CsBotManager/MapProfiles/de_mirage.json"
ONNX_V2_PATH = REPO_ROOT / "training_runs/positioning_v2_real_temporal/onnx_contextual_v2/positioning_transformer_hybrid_v2.onnx"
SMOKE_2B66_SNAPSHOT_PATH = REPO_ROOT / "training_runs/positioning_v2_real_temporal/csharp_shadow_integration/onnx_v2_utility_patch_smoke/opening_routes_snapshot.json"
SMOKE_2B66_EVENTS_PATH = REPO_ROOT / "training_runs/positioning_v2_real_temporal/csharp_shadow_integration/onnx_v2_utility_patch_smoke/utility_ai_events.jsonl"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dist3(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def polyline_length(pts: list[tuple[float, float, float]]) -> float:
    return sum(dist3(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


# Anchors de corredores principais (de_mirage)
CORRIDOR_ENTRY = {
    "CT": {
        "A": (-1400.0, -2080.0, -195.0),
        "MID": (-1480.0, -1520.0, -200.0),
        "B": (-1760.0, -1420.0, -168.0),
    },
    "T": {
        "A": (780.0, -1100.0, -168.0),
        "MID": (560.0, -260.0, -168.0),
        "B": (-350.0, 480.0, -77.0),
    },
}

FAST_THRESHOLD = {
    "CT": {"A": 510.0, "MID": 520.0, "B": 560.0},
    "T": {"A": 1020.0, "MID": 680.0, "B": 1550.0},
}


def classify_spawn_bucket(team: str, x: float, y: float, z: float) -> tuple[str, dict[str, float]]:
    t = "T" if team.upper() in ("T", "TR") else "CT"
    pt = (x, y, z)
    dists = {corr: round(dist3(pt, anchor), 2) for corr, anchor in CORRIDOR_ENTRY[t].items()}
    best_corr = min(("A", "MID", "B"), key=lambda c: dists[c])
    tier = "FAST" if dists[best_corr] <= FAST_THRESHOLD[t][best_corr] else "STANDARD"
    return f"{t}_{best_corr}_{tier}", dists


# Waypoints intermediários autorizados por corredor
CORRIDOR_WAYPOINTS: dict[tuple[str, str], dict[str, Any]] = {
    ("CT", "A_TICKET"): {
        "corridor": "CT_A_TICKET",
        "forbidden": ["MID_WINDOW", "MID_CONNECTOR", "MID_SHORT", "B_MARKET", "B_APPS"],
        "waypoints": [
            {"name": "ct_spawn_a_exit", "x": -1520.0, "y": -1980.0, "z": -230.0},
            {"name": "ct_ticket_booth", "x": -1140.0, "y": -2360.0, "z": -168.0},
        ],
        "weapon_ready_wp": {"name": "ct_ticket_booth", "x": -1140.0, "y": -2360.0, "z": -168.0},
        "threat_line": {"name": "a_ramp_exit_line", "x": -580.0, "y": -2100.0, "z": -175.0},
        "preaim": "A_RAMP_OR_PALACE",
        "conflict_group": "CT_SPAWN_EXIT",
        "knife_until_frac": 0.62,
        "sector": "A",
    },
    ("CT", "A_JUNGLE"): {
        "corridor": "CT_JUNGLE_STAIRS",
        "forbidden": ["MID_WINDOW", "B_MARKET", "B_APPS", "A_RAMP_TR"],
        "waypoints": [
            {"name": "ct_spawn_mid_exit", "x": -1480.0, "y": -1680.0, "z": -200.0},
            {"name": "ct_jungle_entry", "x": -1250.0, "y": -1380.0, "z": -168.0},
        ],
        "weapon_ready_wp": {"name": "ct_jungle_entry", "x": -1250.0, "y": -1380.0, "z": -168.0},
        "threat_line": {"name": "a_stairs_mid_line", "x": -720.0, "y": -1380.0, "z": -110.0},
        "preaim": "A_RAMP_AND_PALACE",
        "conflict_group": "CONNECTOR_ENTRY",
        "knife_until_frac": 0.58,
        "sector": "A",
    },
    ("CT", "MID_WINDOW"): {
        "corridor": "CT_MID_WINDOW",
        "forbidden": ["B_MARKET", "B_APPS", "A_RAMP", "A_PALACE"],
        "waypoints": [
            {"name": "ct_spawn_mid_exit", "x": -1490.0, "y": -1420.0, "z": -185.0},
            {"name": "ct_window_vents", "x": -1280.0, "y": -840.0, "z": -168.0},
        ],
        "weapon_ready_wp": {"name": "ct_window_vents", "x": -1280.0, "y": -840.0, "z": -168.0},
        "threat_line": {"name": "mid_window_sightline", "x": -1120.0, "y": -640.0, "z": -168.0},
        "preaim": "TOP_MID_BOXES",
        "conflict_group": "WINDOW_ENTRY",
        "knife_until_frac": 0.56,
        "sector": "MID",
    },
    ("CT", "MID_SHORT"): {
        "corridor": "CT_B_SHORT_MID",
        "forbidden": ["A_RAMP", "A_PALACE", "T_SPAWN"],
        "waypoints": [
            {"name": "ct_spawn_b_exit", "x": -1760.0, "y": -1350.0, "z": -168.0},
            {"name": "ct_market_back", "x": -1620.0, "y": -640.0, "z": -168.0},
            {"name": "ct_short_arch", "x": -1450.0, "y": 210.0, "z": -168.0},
        ],
        "weapon_ready_wp": {"name": "ct_short_arch", "x": -1450.0, "y": 210.0, "z": -168.0},
        "threat_line": {"name": "mid_catwalk_sightline", "x": -1020.0, "y": 190.0, "z": -170.0},
        "preaim": "TOP_MID_CATWALK",
        "conflict_group": "MARKET_ENTRY",
        "knife_until_frac": 0.65,
        "sector": "MID",
    },
    ("CT", "B_MARKET"): {
        "corridor": "CT_MARKET_CORRIDOR",
        "forbidden": ["MID_WINDOW", "MID_CONNECTOR", "MID_SHORT", "A_RAMP", "A_JUNGLE"],
        "waypoints": [
            {"name": "ct_spawn_b_exit", "x": -1760.0, "y": -1350.0, "z": -168.0},
            {"name": "ct_market_entry", "x": -1640.0, "y": -680.0, "z": -168.0},
        ],
        "weapon_ready_wp": {"name": "ct_market_entry", "x": -1640.0, "y": -680.0, "z": -168.0},
        "threat_line": {"name": "b_apps_window_line", "x": -1850.0, "y": -250.0, "z": -168.0},
        "preaim": "B_APPS_WINDOW",
        "conflict_group": "MARKET_ENTRY",
        "knife_until_frac": 0.64,
        "sector": "B",
    },
    ("T", "A_RAMP"): {
        "corridor": "T_A_RAMP",
        "forbidden": ["CT_SPAWN", "B_APPS", "B_MARKET", "MID_WINDOW"],
        "waypoints": [
            {"name": "t_spawn_a_exit", "x": 1020.0, "y": -780.0, "z": -168.0},
            {"name": "t_a_ramp_entry", "x": 580.0, "y": -1420.0, "z": -168.0},
        ],
        "weapon_ready_wp": {"name": "t_a_ramp_entry", "x": 580.0, "y": -1420.0, "z": -168.0},
        "threat_line": {"name": "a_ramp_choke", "x": 220.0, "y": -1600.0, "z": -168.0},
        "preaim": "A_STAIRS_OR_TICKET",
        "conflict_group": "A_RAMP_ENTRY",
        "knife_until_frac": 0.55,
        "sector": "A",
    },
    ("T", "A_PALACE"): {
        "corridor": "T_A_PALACE",
        "forbidden": ["CT_SPAWN", "B_APPS", "B_MARKET", "MID_WINDOW"],
        "waypoints": [
            {"name": "t_spawn_a_exit", "x": 960.0, "y": -920.0, "z": -168.0},
            {"name": "t_palace_stairs", "x": 450.0, "y": -1920.0, "z": -80.0},
        ],
        "weapon_ready_wp": {"name": "t_palace_stairs", "x": 450.0, "y": -1920.0, "z": -80.0},
        "threat_line": {"name": "a_palace_exit", "x": -100.0, "y": -2120.0, "z": -120.0},
        "preaim": "A_SITE_AND_JUNGLE",
        "conflict_group": "PALACE_ENTRY",
        "knife_until_frac": 0.54,
        "sector": "A",
    },
    ("T", "MID_TOP"): {
        "corridor": "T_TOP_MID",
        "forbidden": ["CT_SPAWN", "B_MARKET", "A_PALACE"],
        "waypoints": [
            {"name": "t_spawn_mid_exit", "x": 880.0, "y": -240.0, "z": -168.0},
            {"name": "t_top_mid_alley", "x": 560.0, "y": -250.0, "z": -168.0},
        ],
        "weapon_ready_wp": {"name": "t_top_mid_alley", "x": 560.0, "y": -250.0, "z": -168.0},
        "threat_line": {"name": "top_mid_window_line", "x": 360.0, "y": -230.0, "z": -168.0},
        "preaim": "MID_WINDOW_AND_CONNECTOR",
        "conflict_group": "TOP_MID_ENTRY",
        "knife_until_frac": 0.50,
        "sector": "MID",
    },
    ("T", "MID_UNDERPASS"): {
        "corridor": "T_UNDERPASS",
        "forbidden": ["CT_SPAWN", "B_MARKET", "A_RAMP"],
        "waypoints": [
            {"name": "t_spawn_b_mid_split", "x": 650.0, "y": 140.0, "z": -168.0},
            {"name": "t_mid_cat_drop", "x": -480.0, "y": -240.0, "z": -240.0},
        ],
        "weapon_ready_wp": {"name": "t_mid_cat_drop", "x": -480.0, "y": -240.0, "z": -240.0},
        "threat_line": {"name": "underpass_connector_line", "x": -920.0, "y": -420.0, "z": -315.0},
        "preaim": "UNDERPASS_EXIT_OR_SHORT",
        "conflict_group": "TOP_MID_ENTRY",
        "knife_until_frac": 0.56,
        "sector": "MID",
    },
    ("T", "B_APPS"): {
        "corridor": "T_B_APPS",
        "forbidden": ["CT_SPAWN", "CT_MARKET", "A_RAMP", "A_PALACE"],
        "waypoints": [
            {"name": "t_spawn_b_exit", "x": 720.0, "y": 320.0, "z": -168.0},
            {"name": "t_b_house_entry", "x": -280.0, "y": 470.0, "z": -80.0},
        ],
        "weapon_ready_wp": {"name": "t_b_house_entry", "x": -280.0, "y": 470.0, "z": -80.0},
        "threat_line": {"name": "b_apps_tv_choke", "x": -960.0, "y": 620.0, "z": -80.0},
        "preaim": "B_APPS_VAN_AND_MARKET",
        "conflict_group": "B_APPS_ENTRY",
        "knife_until_frac": 0.62,
        "sector": "B",
    },
}


def pick_corridor_key(team: str, spot: dict[str, Any]) -> str:
    sid = spot["id"]
    sec = str(spot.get("sector", ""))
    if team == "CT":
        if "b_short_arch" in sid:
            return "MID_SHORT"
        if "market" in sid or "b_" in sid or "Bombsite B" in sec or "Mercado B" in sec or "Apartamentos B" in sec:
            return "B_MARKET"
        if "window" in sid or "ladder" in sid or "underground" in sid or "chair" in sid or "catwalk" in sid:
            return "MID_WINDOW"
        if "jungle" in sid or "vents" in sid or "stairs" in sid or "connector" in sid:
            return "A_JUNGLE"
        return "A_TICKET"
    else:
        if "palace" in sid:
            return "A_PALACE"
        if "underground" in sid:
            return "MID_UNDERPASS"
        if "mid_" in sid:
            return "MID_TOP"
        if "b_" in sid or "Bombsite B" in sec or "Apartamentos B" in sec or "Mercado B" in sec:
            return "B_APPS"
        return "A_RAMP"


def default_role_for_spot(corridor_key: str) -> str:
    if corridor_key in ("MID_WINDOW", "MID_TOP"):
        return "AWPer"
    if corridor_key in ("B_MARKET", "A_TICKET"):
        return "Anchor"
    if corridor_key in ("A_RAMP", "A_PALACE", "B_APPS"):
        return "EntryFragger"
    return "Rotator"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cat_raw = json.loads(CATALOG_V3_PATH.read_text(encoding="utf-8"))
    spots = cat_raw.get("spots", cat_raw) if isinstance(cat_raw, dict) else cat_raw
    side_contract = json.loads(SIDE_CONTRACT_V2_PATH.read_text(encoding="utf-8"))
    review_res_path = REPO_ROOT / "training_runs/positioning_v2_real_temporal/csharp_shadow_integration/onnx_v2_utility_patch_smoke/spot_catalog_review_resolution.json"
    review_res = {r["spot_id"]: r for r in json.loads(review_res_path.read_text(encoding="utf-8"))["resolutions"]} if review_res_path.exists() else {}
    side_rules = {s["spot_id"]: s for s in side_contract["spots"]}
    ct_mask = []
    t_mask = []
    for sp in spots:
        sid = sp["id"]
        sr = review_res.get(sid) or side_rules[sid]
        ct_mask.append(sr.get("ct_rule", "NEVER") != "NEVER")
        t_mask.append(sr.get("t_rule", "NEVER") != "NEVER")

    # 1. input_snapshot.json
    input_snapshot = {
        "marco": "2B.7",
        "entry_verdict": "POSITIONING_SHADOW_DATA_READY_FOR_ROUTE_PLANNER",
        "training_executed": False,
        "weights_modified": False,
        "neural_control_enabled": False,
        "route_planner_control_enabled": False,
        "mlmove_modified": False,
        "canary_started": False,
        "hashes": {
            "training_runs/positioning_v2_real_temporal/onnx_contextual_v2/positioning_transformer_hybrid_v2.onnx": sha256_file(ONNX_V2_PATH),
            "datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json": sha256_file(CATALOG_V3_PATH),
            "training_runs/positioning_v2_real_temporal/csharp_shadow_integration/side_contract_v2/spot_side_contract_v2.json": sha256_file(SIDE_CONTRACT_V2_PATH),
            "src/CsBotManager/MapProfiles/de_mirage.json": sha256_file(DE_MIRAGE_PROFILE_PATH),
        },
        "observed_2b66_snapshot": {
            "classification_counts_numeric": {"6": 12, "7": 18},
            "termination_reason_counts_numeric": {"4": 12, "6": 18},
        },
    }
    (OUT_DIR / "input_snapshot.json").write_text(json.dumps(input_snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 2. opening_route_event_contract_v2.json
    event_contract = {
        "contract_version": "opening_route_event_contract_v2",
        "source_enum_file": "src/CsBotManager/OpeningRouteTracker.cs",
        "decoded_2b66_counts": {
            "classification_counts": {
                "6": {"name": "PLAYER_DEATH", "count": 12},
                "7": {"name": "NOT_REACHED", "count": 18},
            },
            "termination_reason_counts": {
                "4": {"name": "PLAYER_DEATH", "count": 12},
                "6": {"name": "TIMEOUT", "count": 18},
            },
        },
        "classifications": [
            {"code": 0, "name": "PENDING", "meaning": "Rota inicial aberta em andamento", "emission_condition": "TryRegisterAssignment apos freeze time antes do fechamento"},
            {"code": 1, "name": "ON_TIME", "meaning": "Chegou ao spot dentro do deadline sem bloqueio", "emission_condition": "remDist <= SpotRadius por RequiredDwellTicks com elapsedSec <= DeadlineSeconds e HadTeammateBlock == false"},
            {"code": 2, "name": "LATE", "meaning": "Chegou ao spot apos o deadline sem justificativa excludente", "emission_condition": "remDist <= SpotRadius por RequiredDwellTicks com elapsedSec > DeadlineSeconds e HadTeammateBlock == false"},
            {"code": 3, "name": "TACTICAL_REDIRECT", "meaning": "Redirecionamento tatico antes da chegada inicial", "emission_condition": "PostOpeningRepathKind.TACTICAL_ROTATION para outro spot enquanto rota aberta"},
            {"code": 4, "name": "CONTACT_INTERRUPTION", "meaning": "Rota interrompida por contato inimigo legitimo", "emission_condition": "hasEnemyContact == true em UpdateTick enquanto rota aberta"},
            {"code": 5, "name": "BLOCKED_BY_TEAMMATE", "meaning": "Chegada atrasada ou afetada por bloqueio de aliado", "emission_condition": "TARGET_REACHED com HadTeammateBlock == true"},
            {"code": 6, "name": "PLAYER_DEATH", "meaning": "Jogador morreu durante a rota inicial", "emission_condition": "isAlive == false em UpdateTick enquanto rota aberta"},
            {"code": 7, "name": "NOT_REACHED", "meaning": "Rota encerrada por fim de round ou timeout sem chegada", "emission_condition": "ROUND_END ou elapsedSec > DeadlineSeconds * 2.0 antes da chegada"},
            {"code": 8, "name": "INVALID_ROUTE", "meaning": "Rota invalidada por inconsistencia estrutural/contrato", "emission_condition": "CloseAllOpenRoutes com OpeningRouteTerminationReason.INVALIDATED"},
        ],
        "termination_reasons": [
            {"code": 0, "name": "NONE", "meaning": "Rota ainda nao encerrada", "emission_condition": "Estado inicial enquanto IsClosed == false"},
            {"code": 1, "name": "TARGET_REACHED", "meaning": "Destino alcancado com dwell completo", "emission_condition": "DwellTicks >= RequiredDwellTicks dentro de SpotRadius"},
            {"code": 2, "name": "TACTICAL_REDIRECT", "meaning": "Rotacao tatica assumiu o controle", "emission_condition": "PostOpeningRepathKind.TACTICAL_ROTATION com novo spot"},
            {"code": 3, "name": "CONTACT_INTERRUPTION", "meaning": "Engajamento ou contato inimigo detectado", "emission_condition": "hasEnemyContact == true em UpdateTick"},
            {"code": 4, "name": "PLAYER_DEATH", "meaning": "Abate do jogador antes da conclusao da rota", "emission_condition": "isAlive == false em UpdateTick"},
            {"code": 5, "name": "ROUND_END", "meaning": "Round terminou antes da conclusao da rota", "emission_condition": "OnRoundStart ou CloseAllOpenRoutes(ROUND_END)"},
            {"code": 6, "name": "TIMEOUT", "meaning": "Tempo limite maximo (2x deadline) excedido", "emission_condition": "elapsedSec > DeadlineSeconds * 2.0"},
            {"code": 7, "name": "INVALIDATED", "meaning": "Rota invalidada pelo contrato/validador", "emission_condition": "CloseAllOpenRoutes(INVALIDATED)"},
        ],
        "post_opening_repath_kinds": [
            {"code": 0, "name": "MIDROUND_REPATH"},
            {"code": 1, "name": "RECOVERY_REPATH"},
            {"code": 2, "name": "TACTICAL_ROTATION"},
        ],
    }
    (OUT_DIR / "opening_route_event_contract_v2.json").write_text(json.dumps(event_contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 3. spawn_bucket_contract_v1.json (com exemplos reais extraídos do smoke 2B.6.6)
    real_examples: dict[str, list[dict[str, Any]]] = {}
    if SMOKE_2B66_EVENTS_PATH.exists():
        seen_coords: set[tuple[str, float, float, float]] = set()
        for line in SMOKE_2B66_EVENTS_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            ev = json.loads(line)
            if ev.get("EventType") != "SPOT_ASSIGNED" or ev.get("ElapsedMs", 99) != 0:
                continue
            sp = ev.get("StartPosition")
            team = ev.get("Team")
            if not sp or team not in ("CT", "TR"):
                continue
            sx, sy, sz = round(float(sp[0]), 1), round(float(sp[1]), 1), round(float(sp[2]), 1)
            # Filtrar posicoes dentro das areas reais de spawn (CT Z < -230 ou T X > 950)
            is_ct_spawn = team == "CT" and sx <= -1450 and sy <= -1500 and sz <= -230
            is_t_spawn = team == "TR" and sx >= 950 and sy >= -400
            if not (is_ct_spawn or is_t_spawn):
                continue
            key = (team, sx, sy, sz)
            if key in seen_coords:
                continue
            seen_coords.add(key)
            bkt, dists = classify_spawn_bucket(team, sx, sy, sz)
            real_examples.setdefault(bkt, [])
            if len(real_examples[bkt]) < 3:
                real_examples[bkt].append({"x": sx, "y": sy, "z": sz, "corridor_distances": dists})

    buckets = [
        "CT_A_FAST", "CT_A_STANDARD", "CT_MID_FAST", "CT_MID_STANDARD", "CT_B_FAST", "CT_B_STANDARD",
        "T_A_FAST", "T_A_STANDARD", "T_MID_FAST", "T_MID_STANDARD", "T_B_FAST", "T_B_STANDARD",
    ]
    spawn_contract = {
        "contract_version": "spawn_bucket_contract_v1",
        "map": "de_mirage",
        "classification_method": "navigable_corridor_anchor_distance_plus_side",
        "corridor_entries": CORRIDOR_ENTRY,
        "fast_thresholds_units": FAST_THRESHOLD,
        "buckets": [
            {
                "bucket_id": b,
                "team": "CT" if b.startswith("CT_") else "T",
                "corridor": b.split("_")[1],
                "tier": b.split("_")[2],
                "real_examples_from_2b66": real_examples.get(b, []),
            }
            for b in buckets
        ],
    }
    (OUT_DIR / "spawn_bucket_contract_v1.json").write_text(json.dumps(spawn_contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 4. opening_route_catalog_v1.json
    routes: list[dict[str, Any]] = []
    ct_rep_spawn = {"A": (-1600.0, -1950.0, -264.0), "MID": (-1620.0, -1820.0, -264.0), "B": (-1760.0, -1820.0, -264.0)}
    t_rep_spawn = {"A": (1220.0, -240.0, -168.0), "MID": (1220.0, -60.0, -168.0), "B": (1180.0, 40.0, -168.0)}

    for idx, spot in enumerate(spots):
        sid = spot["id"]
        target_pt = (float(spot["x"]), float(spot["y"]), float(spot["z"]))
        allowed_teams = []
        if ct_mask[idx]:
            allowed_teams.append("CT")
        if t_mask[idx]:
            allowed_teams.append("T")

        for team in allowed_teams:
            ckey = pick_corridor_key(team, spot)
            tpl = CORRIDOR_WAYPOINTS[(team, ckey)]
            corr_letter = "A" if ckey.startswith("A_") else ("MID" if ckey.startswith("MID_") else "B")
            spawn_pt = ct_rep_spawn[corr_letter] if team == "CT" else t_rep_spawn[corr_letter]
            wps = list(tpl["waypoints"]) + [{"name": sid, "x": target_pt[0], "y": target_pt[1], "z": target_pt[2]}]
            pts = [spawn_pt] + [(w["x"], w["y"], w["z"]) for w in wps]
            exp_dist = round(polyline_length(pts), 1)
            # Velocidade media operacional (~235 u/s combinando faca inicial + arma)
            exp_sec = round(max(2.5, exp_dist / 235.0), 2)
            deadline_sec = round(exp_sec * 1.45 + 1.8, 2)
            role = default_role_for_spot(ckey)

            for tier in ("FAST", "STANDARD"):
                sb = f"{team}_{corr_letter}_{tier}"
                tier_bonus = 0.0 if tier == "FAST" else 0.75
                routes.append({
                    "route_id": f"{team.lower()}_{sb.lower()}_to_{sid}_primary",
                    "map": "de_mirage",
                    "team": team,
                    "spawn_bucket": sb,
                    "role": role,
                    "target_spot": sid,
                    "target_sector": tpl["sector"],
                    "route_variant": "PRIMARY",
                    "ordered_waypoints": wps,
                    "allowed_corridor": tpl["corridor"],
                    "forbidden_corridors": tpl["forbidden"],
                    "expected_distance": round(exp_dist + (0.0 if tier == "FAST" else 160.0), 1),
                    "expected_arrival_seconds": round(exp_sec + tier_bonus, 2),
                    "deadline_seconds": round(deadline_sec + tier_bonus, 2),
                    "knife_allowed_until": round((exp_sec + tier_bonus) * tpl["knife_until_frac"], 2),
                    "weapon_ready_waypoint": tpl["weapon_ready_wp"],
                    "first_threat_line": tpl["threat_line"],
                    "first_preaim_target": tpl["preaim"],
                    "fallback_route": f"{team.lower()}_{sb.lower()}_to_{sid}_fallback",
                    "conflict_group": tpl["conflict_group"],
                    "contract_version": "opening_route_catalog_v1",
                })

    catalog_payload = {
        "contract_version": "opening_route_catalog_v1",
        "map": "de_mirage",
        "total_spots_covered": len({r["target_spot"] for r in routes}),
        "total_routes": len(routes),
        "routes": routes,
    }
    (OUT_DIR / "opening_route_catalog_v1.json").write_text(json.dumps(catalog_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 5. conflict_group_contract_v1.json
    conflict_groups = [
        "CT_SPAWN_EXIT",
        "MARKET_ENTRY",
        "CONNECTOR_ENTRY",
        "WINDOW_ENTRY",
        "B_APPS_ENTRY",
        "A_RAMP_ENTRY",
        "PALACE_ENTRY",
        "TOP_MID_ENTRY",
    ]
    conflict_contract = {
        "contract_version": "conflict_group_contract_v1",
        "conflict_groups": [
            {
                "group_id": cg,
                "max_concurrent_lead": 1,
                "priority_rule": "spawn_bucket_fast_first_then_role_priority_then_slot",
                "role_priority_order": ["AWPer", "EntryFragger", "Anchor", "Rotator"],
                "delayed_bot_offset_ms": 450,
                "max_teammate_push_ticks": 8,
            }
            for cg in conflict_groups
        ],
        "telemetry_fields": [
            "conflict_detected",
            "priority_winner",
            "delayed_bot",
            "alternative_route",
            "delay_ms",
            "blocked_duration_ms",
        ],
    }
    (OUT_DIR / "conflict_group_contract_v1.json").write_text(json.dumps(conflict_contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 6. weapon_readiness_policy_v1.json
    weapon_policy = {
        "contract_version": "weapon_readiness_policy_v1",
        "shadow_only": True,
        "knife_allowed_conditions": [
            "no_possible_enemy_contact",
            "corridor_protected",
            "distance_to_threat_line_above_threshold",
            "no_enemy_contact_sound_or_hostile_utility",
            "route_valid",
        ],
        "weapon_switch_triggers": [
            "before_first_possible_angle",
            "before_awp_sightline",
            "before_choke_entry",
            "before_contact_corner",
            "hostile_utility_detected",
            "enemy_contact_detected",
        ],
        "min_distance_to_threat_at_switch_units": 320.0,
        "required_telemetry_fields": [
            "knife_start_tick",
            "weapon_switch_tick",
            "threat_line_tick",
            "first_possible_contact_tick",
            "distance_to_threat_at_switch",
            "weapon_ready_before_contact",
        ],
        "gate": {"weapon_ready_before_contact_rate_required": 1.0},
    }
    (OUT_DIR / "weapon_readiness_policy_v1.json").write_text(json.dumps(weapon_policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 7. route_deadline_contract_v1.json
    deadline_contract = {
        "contract_version": "route_deadline_contract_v1",
        "tick_rate": 64.0,
        "thresholds_formula": {
            "expected_seconds": "expected_distance / 235.0",
            "deadline_seconds": "expected_seconds * 1.45 + 1.8",
            "late_threshold": "deadline_seconds",
            "timeout_threshold": "deadline_seconds * 2.0",
        },
        "non_penalized_terminations": [
            "CONTACT_INTERRUPTION",
            "TACTICAL_REDIRECT",
            "PLAYER_DEATH",
            "BLOCKED_BY_HOSTILE_UTILITY",
        ],
        "valid_classifications": [
            "ON_TIME",
            "LATE",
            "BLOCKED_BY_TEAMMATE",
            "CONTACT_INTERRUPTION",
            "TACTICAL_REDIRECT",
            "PLAYER_DEATH",
            "INVALID_ROUTE",
            "NOT_REACHED",
        ],
    }
    (OUT_DIR / "route_deadline_contract_v1.json").write_text(json.dumps(deadline_contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"BUILT_2B7_CONTRACTS spots={len(spots)} routes={len(routes)} buckets={len(buckets)}")


if __name__ == "__main__":
    main()
