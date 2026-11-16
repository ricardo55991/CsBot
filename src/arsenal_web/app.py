import os
import json
import asyncio
import httpx
from typing import Optional, List, Dict, Any, Union, Tuple
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
import pymysql

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEAPON_PAINTS_DATA = r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\WeaponPaints\data"
DEFAULT_STEAMID = "76561198816182970"
MOCK_STEAMID = "76561198063731155"

def resolve_steamids(steamid: Optional[str] = None) -> List[str]:
    """Retorna lista de SteamIDs para sincronizar, garantindo que o SteamID real do jogador seja sempre contemplado."""
    ids = [DEFAULT_STEAMID]
    if steamid and steamid.strip():
        s = steamid.strip()
        if s not in ids:
            ids.append(s)
    if MOCK_STEAMID not in ids:
        ids.append(MOCK_STEAMID)
    return ids

# Configuração de Conexão MariaDB
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "weaponpaints",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True
}

def get_db():
    return pymysql.connect(**DB_CONFIG)

app = FastAPI(title="CsBot Arsenal Web UI", description="Interface de Arsenal e Skins para CS2")

# ==============================================================================
# Presets de Gemas Doppler e Facas Base
# ==============================================================================
SPECIAL_GEM_PRESETS = [
    {"name": "Padrão / Vanilla", "paint_id": 0, "wear": 0.0001, "seed": 0, "css_class": "vanilla", "badge": "VANILLA"},
    {"name": "Doppler Ruby", "paint_id": 415, "wear": 0.0001, "seed": 0, "css_class": "ruby", "badge": "RUBY"},
    {"name": "Doppler Sapphire", "paint_id": 416, "wear": 0.0001, "seed": 0, "css_class": "sapphire", "badge": "SAPPHIRE"},
    {"name": "Doppler Black Pearl", "paint_id": 417, "wear": 0.0001, "seed": 0, "css_class": "blackpearl", "badge": "BLACK PEARL"},
    {"name": "Gamma Doppler Emerald", "paint_id": 568, "wear": 0.0001, "seed": 0, "css_class": "emerald", "badge": "EMERALD"},
    {"name": "Doppler Phase 2 (Pink)", "paint_id": 419, "wear": 0.0001, "seed": 0, "css_class": "ruby", "badge": "PHASE 2"},
    {"name": "Doppler Phase 4 (Blue)", "paint_id": 421, "wear": 0.0001, "seed": 0, "css_class": "sapphire", "badge": "PHASE 4"},
    {"name": "Fade 100% (Full Fade)", "paint_id": 38, "wear": 0.0001, "seed": 412, "css_class": "fade", "badge": "FADE 100%"},
    {"name": "Marble Fade (Fire & Ice)", "paint_id": 413, "wear": 0.0001, "seed": 412, "css_class": "fade", "badge": "FIRE & ICE"},
    {"name": "Tiger Tooth", "paint_id": 409, "wear": 0.0001, "seed": 0, "css_class": "tiger", "badge": "TIGER TOOTH"},
    {"name": "Case Hardened Blue Gem", "paint_id": 44, "wear": 0.0100, "seed": 661, "css_class": "bluegem", "badge": "BLUE GEM"},
    {"name": "Crimson Web", "paint_id": 12, "wear": 0.0600, "seed": 110, "css_class": "crimson", "badge": "CRIMSON WEB"},
    {"name": "Slaughter", "paint_id": 59, "wear": 0.0100, "seed": 20, "css_class": "slaughter", "badge": "SLAUGHTER"},
    {"name": "Lore (Clean)", "paint_id": 562, "wear": 0.0001, "seed": 0, "css_class": "lore", "badge": "LORE"},
    {"name": "Autotronic", "paint_id": 573, "wear": 0.0001, "seed": 0, "css_class": "autotronic", "badge": "AUTOTRONIC"}
]

KNIVES_BASE = [
    {"name": "Karambit", "model": "weapon_knife_karambit", "defindex": 507, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_karambit.png"},
    {"name": "Butterfly Knife", "model": "weapon_knife_butterfly", "defindex": 515, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_butterfly.png"},
    {"name": "M9 Bayonet", "model": "weapon_knife_m9_bayonet", "defindex": 508, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_m9_bayonet.png"},
    {"name": "Bayonet", "model": "weapon_bayonet", "defindex": 500, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_bayonet.png"},
    {"name": "Talon Knife", "model": "weapon_knife_widowmaker", "defindex": 523, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_widowmaker.png"},
    {"name": "Skeleton Knife", "model": "weapon_knife_skeleton", "defindex": 525, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_skeleton.png"},
    {"name": "Stiletto Knife", "model": "weapon_knife_stiletto", "defindex": 522, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_stiletto.png"},
    {"name": "Nomad Knife", "model": "weapon_knife_outdoor", "defindex": 521, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_outdoor.png"},
    {"name": "Ursus Knife", "model": "weapon_knife_ursus", "defindex": 519, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_ursus.png"},
    {"name": "Kukri Knife", "model": "weapon_knife_kukri", "defindex": 526, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_kukri.png"},
    {"name": "Huntsman Knife", "model": "weapon_knife_tactical", "defindex": 509, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_tactical.png"},
    {"name": "Falchion Knife", "model": "weapon_knife_falchion", "defindex": 512, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_falchion.png"},
    {"name": "Bowie Knife", "model": "weapon_knife_survival_bowie", "defindex": 514, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_survival_bowie.png"},
    {"name": "Flip Knife", "model": "weapon_knife_flip", "defindex": 505, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_flip.png"},
    {"name": "Gut Knife", "model": "weapon_knife_gut", "defindex": 506, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_gut.png"},
    {"name": "Classic Knife", "model": "weapon_knife_css", "defindex": 503, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_css.png"},
    {"name": "Survival Knife", "model": "weapon_knife_canis", "defindex": 518, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_canis.png"},
    {"name": "Paracord Knife", "model": "weapon_knife_cord", "defindex": 517, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_cord.png"},
    {"name": "Navaja Knife", "model": "weapon_knife_gypsy_jackknife", "defindex": 520, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_gypsy_jackknife.png"},
    {"name": "Shadow Daggers", "model": "weapon_knife_push", "defindex": 516, "image_url": "https://raw.githubusercontent.com/Nereziel/cs2-WeaponPaints/main/website/img/skins/weapon_knife_push.png"}
]

WEAPON_DISPLAY_NAMES = {
    "weapon_ak47": ("AK-47", "rifle"),
    "weapon_m4a1": ("M4A4", "rifle"),
    "weapon_m4a1_silencer": ("M4A1-S", "rifle"),
    "weapon_galilar": ("Galil AR", "rifle"),
    "weapon_famas": ("FAMAS", "rifle"),
    "weapon_aug": ("AUG", "rifle"),
    "weapon_sg556": ("SG 553", "rifle"),
    "weapon_awp": ("AWP", "sniper"),
    "weapon_ssg08": ("SSG 08", "sniper"),
    "weapon_scar20": ("SCAR-20", "sniper"),
    "weapon_g3sg1": ("G3SG1", "sniper"),
    "weapon_deagle": ("Desert Eagle", "pistol"),
    "weapon_usp_silencer": ("USP-S", "pistol"),
    "weapon_glock": ("Glock-18", "pistol"),
    "weapon_p250": ("P250", "pistol"),
    "weapon_fiveseven": ("Five-SeveN", "pistol"),
    "weapon_tec9": ("Tec-9", "pistol"),
    "weapon_cz75a": ("CZ75-Auto", "pistol"),
    "weapon_elite": ("Dual Berettas", "pistol"),
    "weapon_revolver": ("R8 Revolver", "pistol"),
    "weapon_hkp2000": ("P2000", "pistol"),
    "weapon_taser": ("Zeus x27", "pistol"),
    "weapon_mac10": ("MAC-10", "smg"),
    "weapon_mp9": ("MP9", "smg"),
    "weapon_mp7": ("MP7", "smg"),
    "weapon_mp5sd": ("MP5-SD", "smg"),
    "weapon_ump45": ("UMP-45", "smg"),
    "weapon_p90": ("P90", "smg"),
    "weapon_bizon": ("PP-Bizon", "smg"),
    "weapon_nova": ("Nova", "heavy"),
    "weapon_xm1014": ("XM1014", "heavy"),
    "weapon_mag7": ("MAG-7", "heavy"),
    "weapon_sawedoff": ("Sawed-Off", "heavy"),
    "weapon_m249": ("M249", "heavy"),
    "weapon_negev": ("Negev", "heavy")
}

CATALOG: Dict[str, Any] = {
    "knives": KNIVES_BASE,
    "gloves": [],
    "weapons": [],
    "gem_presets": SPECIAL_GEM_PRESETS,
    "special_gem_presets": SPECIAL_GEM_PRESETS
}

# Lookups rápidos para enriquecer inventário
LOOKUP_SKIN: Dict[Tuple[int, int], Dict[str, Any]] = {}
LOOKUP_KNIFE_BY_MODEL: Dict[str, Dict[str, Any]] = {k["model"]: k for k in KNIVES_BASE}
LOOKUP_KNIFE_BY_DEFINDEX: Dict[int, Dict[str, Any]] = {k["defindex"]: k for k in KNIVES_BASE}
LOOKUP_GLOVES: Dict[int, Dict[str, Any]] = {}
LOOKUP_DEFINDEX_WEAPON: Dict[int, str] = {}

def load_catalog_data():
    skins_path = os.path.join(WEAPON_PAINTS_DATA, "skins_en.json")
    gloves_path = os.path.join(WEAPON_PAINTS_DATA, "gloves_en.json")

    # Mapeamentos para facas
    knife_skins_map: Dict[str, Dict[str, Dict[str, Any]]] = {k["model"]: {} for k in KNIVES_BASE}
    knife_skins_list: Dict[str, List[Dict[str, Any]]] = {k["model"]: [] for k in KNIVES_BASE}

    # Mapeamentos para armas normais
    weapons_map: Dict[str, Dict[str, Any]] = {}

    if os.path.exists(skins_path):
        try:
            with open(skins_path, "r", encoding="utf-8") as f:
                all_skins = json.load(f)
                for item in all_skins:
                    defindex = item.get("weapon_defindex")
                    wname = item.get("weapon_name", "")
                    pname = item.get("paint_name", "")
                    raw_paint = item.get("paint") or item.get("paint_id") or 0
                    try:
                        pid = int(raw_paint)
                    except:
                        pid = 0
                    img = item.get("image", "")

                    if not defindex or pid == 0:
                        continue

                    # 1. Tratar Facas
                    if "knife" in wname or "bayonet" in wname:
                        if wname in knife_skins_map:
                            clean_pname = pname.replace("★ ", "").replace(wname.replace("weapon_", "").upper(), "").replace("|", "").strip() or pname
                            skin_entry = {
                                "paint_id": pid,
                                "name": clean_pname,
                                "image_url": img
                            }
                            knife_skins_map[wname][str(pid)] = skin_entry
                            knife_skins_list[wname].append(skin_entry)
                        continue

                    # 2. Ignorar Luvas aqui (têm arquivo próprio)
                    if "glove" in wname:
                        continue

                    # 3. Tratar Armas Tradicionais (todas as 35 armas)
                    disp_info = WEAPON_DISPLAY_NAMES.get(wname)
                    if disp_info:
                        clean_name, category = disp_info
                    else:
                        clean_name = wname.replace("weapon_", "").upper()
                        category = "rifle"

                    if wname not in weapons_map:
                        weapons_map[wname] = {
                            "defindex": defindex,
                            "weapon_key": wname,
                            "name": clean_name,
                            "category": category,
                            "skins": []
                        }

                    clean_skin_name = pname.replace(clean_name, "").replace("★ ", "").replace("|", "").strip() or pname
                    weapons_map[wname]["skins"].append({
                        "paint_id": pid,
                        "name": clean_skin_name,
                        "image_url": img
                    })

                    # Registrar no lookup global
                    LOOKUP_SKIN[(defindex, pid)] = {
                        "weapon_name": clean_name,
                        "skin_name": clean_skin_name,
                        "image_url": img
                    }
                    LOOKUP_DEFINDEX_WEAPON[defindex] = clean_name

                # Associar skins completas e lookup por pintura a cada faca
                for k in KNIVES_BASE:
                    m = k["model"]
                    k["skins"] = knife_skins_list.get(m, [])
                    k["skins_by_paint"] = knife_skins_map.get(m, {})
                    LOOKUP_KNIFE_BY_MODEL[m] = k
                    LOOKUP_KNIFE_BY_DEFINDEX[k["defindex"]] = k

                CATALOG["knives"] = KNIVES_BASE
                CATALOG["weapons"] = list(weapons_map.values())
                total_skins_count = sum(len(w["skins"]) for w in CATALOG["weapons"])
                total_knife_skins = sum(len(k["skins"]) for k in CATALOG["knives"])
                print(f"[+] Catalogo carregado: {len(CATALOG['knives'])} modelos de facas ({total_knife_skins} pinturas), {len(CATALOG['weapons'])} armas ({total_skins_count} skins).")
        except Exception as e:
            print(f"[!] Erro ao carregar {skins_path}: {e}")

    if os.path.exists(gloves_path):
        try:
            with open(gloves_path, "r", encoding="utf-8") as f:
                all_gloves = json.load(f)
                gloves_clean = []
                for g in all_gloves:
                    didx = g.get("weapon_defindex", 0)
                    raw_paint = g.get("paint", 0)
                    try:
                        pid = int(raw_paint)
                    except:
                        pid = 0
                    if didx != 0 and pid != 0:
                        glove_entry = {
                            "defindex": didx,
                            "paint_id": pid,
                            "name": g.get("paint_name", "Luvas").replace("★ ", "").strip(),
                            "image_url": g.get("image", "")
                        }
                        gloves_clean.append(glove_entry)
                        LOOKUP_GLOVES[(didx, pid)] = glove_entry
                        if didx not in LOOKUP_GLOVES:
                            LOOKUP_GLOVES[didx] = glove_entry
                CATALOG["gloves"] = gloves_clean
                print(f"[+] Catalogo de luvas carregado: {len(CATALOG['gloves'])} luvas.")
        except Exception as e:
            print(f"[!] Erro ao carregar {gloves_path}: {e}")

load_catalog_data()

# ==============================================================================
# Modelos de Requisição
# ==============================================================================
class KnifeEquipRequest(BaseModel):
    steamid: Optional[str] = DEFAULT_STEAMID
    team: int = 0  # 0 = Ambos (2 e 3), 2 = TR, 3 = CT
    knife: Optional[str] = None
    knife_name: Optional[str] = None
    defindex: Optional[int] = 500
    paint_id: Optional[int] = 0
    wear: Optional[float] = 0.0001
    seed: Optional[int] = 0
    stattrak: Optional[Union[int, bool]] = 0
    stattrak_count: Optional[int] = 0
    nametag: Optional[str] = ""

class SkinEquipRequest(BaseModel):
    steamid: Optional[str] = DEFAULT_STEAMID
    team: int = 0  # 0 = Ambos (2 e 3), 2 = TR, 3 = CT
    defindex: int
    paint_id: int
    wear: Optional[float] = 0.0001
    seed: Optional[int] = 0
    stattrak: Optional[Union[int, bool]] = 0
    stattrak_count: Optional[int] = 0
    nametag: Optional[str] = ""

class GloveEquipRequest(BaseModel):
    steamid: Optional[str] = DEFAULT_STEAMID
    team: int = 0  # 0 = Ambos (2 e 3), 2 = TR, 3 = CT
    defindex: Optional[int] = None
    glove_defindex: Optional[int] = None
    paint_id: Optional[int] = 0
    wear: Optional[float] = 0.0001
    seed: Optional[int] = 0

# ==============================================================================
# Endpoints da API
# ==============================================================================
@app.get("/api/status")
def get_status():
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total_knives FROM wp_player_knife")
            knives = cursor.fetchone()["total_knives"]
            cursor.execute("SELECT COUNT(*) AS total_skins FROM wp_player_skins")
            skins = cursor.fetchone()["total_skins"]
            cursor.execute("SELECT COUNT(*) AS total_gloves FROM wp_player_gloves")
            gloves = cursor.fetchone()["total_gloves"]
        conn.close()
        return {
            "status": "online",
            "database": "weaponpaints",
            "host": "127.0.0.1:3306",
            "default_steamid": DEFAULT_STEAMID,
            "counts": {"knives": knives, "skins": skins, "gloves": gloves}
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/catalog")
def get_catalog():
    return CATALOG

@app.get("/api/inventory")
def get_inventory(steamid: Optional[str] = None):
    target_id = steamid.strip() if (steamid and steamid.strip() and steamid.strip() != MOCK_STEAMID) else DEFAULT_STEAMID
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT weapon_team AS team, knife FROM wp_player_knife WHERE steamid = %s", (target_id,))
        knives = cursor.fetchall()
        cursor.execute("SELECT weapon_team AS team, weapon_defindex AS defindex, weapon_paint_id AS paint_id, weapon_wear AS wear, weapon_seed AS seed, weapon_nametag AS nametag, weapon_stattrak AS stattrak, weapon_stattrak_count AS stattrak_count FROM wp_player_skins WHERE steamid = %s", (target_id,))
        skins = cursor.fetchall()
        cursor.execute("SELECT weapon_team AS team, weapon_defindex AS defindex FROM wp_player_gloves WHERE steamid = %s", (target_id,))
        gloves = cursor.fetchall()
    conn.close()

    equipped_items = []
    skins_by_didx_team = {(s["defindex"], s["team"]): s for s in skins}

    # 1. Facas Equipadas
    for k in knives:
        model = k.get("knife", "weapon_knife_karambit")
        team = k.get("team", 0)
        knife_info = LOOKUP_KNIFE_BY_MODEL.get(model, {"name": model.replace("weapon_knife_", "").upper(), "image_url": "", "defindex": 507})
        knife_name = knife_info.get("name", "Faca")
        knife_defindex = knife_info.get("defindex", 507)

        skin_entry = skins_by_didx_team.get((knife_defindex, team)) or skins_by_didx_team.get((500, team))

        if skin_entry and skin_entry["paint_id"] > 0:
            pid = skin_entry["paint_id"]
            gem_override_name = next((p["name"] for p in SPECIAL_GEM_PRESETS if p["paint_id"] == pid), None)
            skin_obj = (knife_info.get("skins_by_paint") or {}).get(str(pid))
            if gem_override_name:
                skin_name = gem_override_name
                img = skin_obj["image_url"] if skin_obj else knife_info.get("image_url", "")
            elif skin_obj:
                skin_name = skin_obj["name"]
                img = skin_obj["image_url"]
            else:
                skin_name = f"Acabamento (Paint {pid})"
                img = knife_info.get("image_url", "")

            equipped_items.append({
                "type": "knife",
                "team": team,
                "model": model,
                "defindex": knife_defindex,
                "weapon_name": knife_name,
                "skin_name": skin_name,
                "full_name": f"{knife_name} | {skin_name}",
                "image_url": img,
                "paint_id": pid,
                "wear": skin_entry.get("wear") or 0.0001,
                "seed": skin_entry.get("seed") or 0,
                "nametag": skin_entry.get("nametag") or "",
                "stattrak": bool(skin_entry.get("stattrak")),
                "stattrak_count": skin_entry.get("stattrak_count") or 0
            })
        else:
            equipped_items.append({
                "type": "knife",
                "team": team,
                "model": model,
                "defindex": knife_defindex,
                "weapon_name": knife_name,
                "skin_name": "Padrão / Vanilla",
                "full_name": knife_name,
                "image_url": knife_info.get("image_url", ""),
                "paint_id": 0,
                "wear": 0.0001,
                "seed": 0,
                "nametag": "",
                "stattrak": False,
                "stattrak_count": 0
            })

    # 2. Armas Equipadas (Skins tradicionais)
    knife_defindexes = {500, 503, 505, 506, 507, 508, 509, 512, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 525, 526}
    glove_defindexes = {4725, 5027, 5028, 5029, 5030, 5031, 5032, 5033, 5034, 5035, 5036}

    for s in skins:
        didx = s["defindex"]
        pid = s["paint_id"]
        team = s["team"]

        # Ignorar facas e luvas (elas já são processadas nas suas seções dedicadas com imagens e nomes corretos)
        if didx in knife_defindexes or didx in glove_defindexes or didx >= 4000:
            continue

        lookup = LOOKUP_SKIN.get((didx, pid))
        if lookup:
            wname = lookup["weapon_name"]
            sname = lookup["skin_name"]
            img = lookup["image_url"]
        else:
            wname = LOOKUP_DEFINDEX_WEAPON.get(didx, f"Arma (DefIndex {didx})")
            sname = f"Paint ID {pid}"
            img = ""

        equipped_items.append({
            "type": "weapon",
            "team": team,
            "defindex": didx,
            "weapon_name": wname,
            "skin_name": sname,
            "full_name": f"{wname} | {sname}",
            "image_url": img,
            "paint_id": pid,
            "wear": s.get("wear") or 0.0001,
            "seed": s.get("seed") or 0,
            "nametag": s.get("nametag") or "",
            "stattrak": bool(s.get("stattrak")),
            "stattrak_count": s.get("stattrak_count") or 0
        })

    # 3. Luvas Equipadas
    for g in gloves:
        didx = g.get("defindex", 5030)
        team = g.get("team", 0)
        skin_entry = skins_by_didx_team.get((didx, team))
        pid = skin_entry["paint_id"] if skin_entry else 0
        glove_info = LOOKUP_GLOVES.get((didx, pid)) or LOOKUP_GLOVES.get(didx, {"name": f"Luvas (DefIndex {didx})", "image_url": ""})

        equipped_items.append({
            "type": "glove",
            "team": team,
            "defindex": didx,
            "weapon_name": "Luvas",
            "skin_name": glove_info.get("name", "Luvas de Operação"),
            "full_name": glove_info.get("name", "Luvas"),
            "image_url": glove_info.get("image_url", ""),
            "paint_id": pid,
            "wear": skin_entry.get("wear") if skin_entry else 0.0001,
            "seed": skin_entry.get("seed") if skin_entry else 0,
            "nametag": skin_entry.get("nametag") if skin_entry else "",
            "stattrak": bool(skin_entry.get("stattrak")) if skin_entry else False,
            "stattrak_count": skin_entry.get("stattrak_count") if skin_entry else 0
        })

    return {
        "steamid": steamid,
        "knives": knives,
        "skins": skins,
        "gloves": gloves,
        "equipped_items": equipped_items
    }

@app.post("/api/equip/knife")
def equip_knife(req: KnifeEquipRequest):
    steamids = resolve_steamids(req.steamid)
    teams = [2, 3] if req.team == 0 else [req.team]
    knife_model = req.knife or req.knife_name or "weapon_knife_karambit"
    knife_defindex = req.defindex or 500
    st_val = 1 if req.stattrak else 0

    conn = get_db()
    with conn.cursor() as cursor:
        for sid in steamids:
            for t in teams:
                cursor.execute("""
                    INSERT INTO wp_player_knife (steamid, weapon_team, knife)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE knife = VALUES(knife)
                """, (sid, t, knife_model))

                if req.paint_id and req.paint_id > 0:
                    defindexes_to_update = {knife_defindex, 500}
                    for didx in defindexes_to_update:
                        cursor.execute("""
                            INSERT INTO wp_player_skins 
                            (steamid, weapon_team, weapon_defindex, weapon_paint_id, weapon_wear, weapon_seed, weapon_nametag, weapon_stattrak, weapon_stattrak_count)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE 
                                weapon_paint_id = VALUES(weapon_paint_id),
                                weapon_wear = VALUES(weapon_wear),
                                weapon_seed = VALUES(weapon_seed),
                                weapon_nametag = VALUES(weapon_nametag),
                                weapon_stattrak = VALUES(weapon_stattrak),
                                weapon_stattrak_count = VALUES(weapon_stattrak_count)
                        """, (sid, t, didx, req.paint_id, req.wear or 0.0001, req.seed or 0, req.nametag or "", st_val, req.stattrak_count or 0))
    conn.close()

    return {
        "success": True,
        "status": "success",
        "message": f"Faca {knife_model} salva no banco!",
        "steamid": steamids[0],
        "teams": teams
    }

@app.post("/api/equip/skin")
def equip_skin(req: SkinEquipRequest):
    steamids = resolve_steamids(req.steamid)
    teams = [2, 3] if req.team == 0 else [req.team]
    st_val = 1 if req.stattrak else 0

    conn = get_db()
    with conn.cursor() as cursor:
        for sid in steamids:
            for t in teams:
                cursor.execute("""
                    INSERT INTO wp_player_skins 
                    (steamid, weapon_team, weapon_defindex, weapon_paint_id, weapon_wear, weapon_seed, weapon_nametag, weapon_stattrak, weapon_stattrak_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        weapon_paint_id = VALUES(weapon_paint_id),
                        weapon_wear = VALUES(weapon_wear),
                        weapon_seed = VALUES(weapon_seed),
                        weapon_nametag = VALUES(weapon_nametag),
                        weapon_stattrak = VALUES(weapon_stattrak),
                        weapon_stattrak_count = VALUES(weapon_stattrak_count)
                """, (sid, t, req.defindex, req.paint_id, req.wear or 0.0001, req.seed or 0, req.nametag or "", st_val, req.stattrak_count or 0))
    conn.close()

    return {
        "success": True,
        "status": "success",
        "message": f"Skin (defindex {req.defindex}, paint {req.paint_id}) salva no banco!",
        "steamid": steamids[0],
        "teams": teams
    }

@app.post("/api/equip/gloves")
def equip_gloves(req: GloveEquipRequest):
    steamids = resolve_steamids(req.steamid)
    teams = [2, 3] if req.team == 0 else [req.team]
    glove_idx = req.defindex or req.glove_defindex or 5030

    conn = get_db()
    with conn.cursor() as cursor:
        for sid in steamids:
            for t in teams:
                cursor.execute("""
                    INSERT INTO wp_player_gloves (steamid, weapon_team, weapon_defindex)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE weapon_defindex = VALUES(weapon_defindex)
                """, (sid, t, glove_idx))

                if req.paint_id and req.paint_id > 0:
                    cursor.execute("""
                        INSERT INTO wp_player_skins 
                        (steamid, weapon_team, weapon_defindex, weapon_paint_id, weapon_wear, weapon_seed, weapon_nametag, weapon_stattrak, weapon_stattrak_count)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                            weapon_paint_id = VALUES(weapon_paint_id),
                            weapon_wear = VALUES(weapon_wear),
                            weapon_seed = VALUES(weapon_seed)
                    """, (sid, t, glove_idx, req.paint_id, req.wear or 0.0001, req.seed or 0, "", 0, 0))
    conn.close()

    return {
        "success": True,
        "status": "success",
        "message": f"Luvas (defindex {glove_idx}, paint {req.paint_id}) salvas no banco!",
        "steamid": steamids[0],
        "teams": teams
    }

# ==============================================================================
# Endpoint de Inspeção CS2 (Steam Protocol & Web 3D)
# ==============================================================================
class InspectRequest(BaseModel):
    defindex: int
    paint_id: int
    wear: Optional[float] = 0.0001
    seed: Optional[int] = 0
    stattrak: Optional[bool] = False
    stattrak_count: Optional[int] = 0
    nametag: Optional[str] = None
    rarity: Optional[int] = None

def build_inspect_payload(defindex: int, paint_id: int, wear: float = 0.0001, seed: int = 0,
                          stattrak: bool = False, stattrak_count: int = 0, nametag: Optional[str] = None,
                          rarity: Optional[int] = None):
    try:
        import cs2inspect
        if rarity is None:
            rarity = 6 if int(defindex) >= 500 else 5
        st_count = int(stattrak_count) if (stattrak and stattrak_count) else None
        custom_name = nametag.strip() if nametag and nametag.strip() else None

        w = max(0.0001, min(0.9999, float(wear)))
        s = max(0, min(1000, int(seed)))
        p = max(0, int(paint_id))
        d = int(defindex)

        proto = cs2inspect.Builder(
            defindex=d,
            paintindex=p,
            paintseed=s,
            paintwear=w,
            rarity=int(rarity),
            killeatervalue=st_count,
            customname=custom_name
        )
        built = proto.build()
        short_link = cs2inspect.link(built)
        hex_payload = short_link.split("%20")[-1] if "%20" in short_link else ""
        steam_market_link = f"steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20{hex_payload}"
        console_cmd = f"csgo_econ_action_preview {hex_payload}"
        
        return {
            "success": True,
            "steam_link": steam_market_link,
            "short_link": short_link,
            "console_cmd": console_cmd,
            "hex_payload": hex_payload,
            "web_3d_url": f"https://3d.cs.money/?inspect={steam_market_link}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "steam_link": "",
            "console_cmd": "",
            "hex_payload": "",
            "web_3d_url": ""
        }

@app.get("/api/inspect-link")
def get_inspect_link_get(
    defindex: int,
    paint_id: int,
    wear: float = 0.0001,
    seed: int = 0,
    stattrak: bool = False,
    stattrak_count: int = 0,
    nametag: Optional[str] = None,
    rarity: Optional[int] = None
):
    return build_inspect_payload(defindex, paint_id, wear, seed, stattrak, stattrak_count, nametag, rarity)

@app.post("/api/inspect-link")
def get_inspect_link_post(req: InspectRequest):
    return build_inspect_payload(req.defindex, req.paint_id, req.wear or 0.0001, req.seed or 0,
                                 req.stattrak or False, req.stattrak_count or 0, req.nametag, req.rarity)

# ==============================================================================
# Servir Frontend
# ==============================================================================
static_dir = os.path.join(BASE_DIR, "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def index():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    fav_svg = os.path.join(static_dir, "favicon.svg")
    if os.path.exists(fav_svg):
        return FileResponse(fav_svg, media_type="image/svg+xml")
    return Response(status_code=204)

# ==============================================================================
# Rotas e WebSocket da Segunda Tela (Radar 2D & Central Tática)
# ==============================================================================
@app.get("/radar")
def radar_page():
    radar_html = os.path.join(static_dir, "radar.html")
    if os.path.exists(radar_html):
        return FileResponse(radar_html)
    return Response(content="<h1>radar.html em construção</h1>", media_type="text/html")

@app.get("/api/radar/state")
async def get_radar_state():
    try:
        async with httpx.AsyncClient(timeout=0.3) as client:
            resp = await client.get("http://127.0.0.1:27080/radar/state")
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return {"status": "server_offline", "players": [], "c4": {"is_planted": False}}

class RadarCommandRequest(BaseModel):
    command: str

@app.post("/api/radar/command")
async def post_radar_command(req: RadarCommandRequest):
    try:
        async with httpx.AsyncClient(timeout=0.5) as client:
            resp = await client.post("http://127.0.0.1:27080/radar/command", json={"command": req.command})
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}
    return {"status": "ok"}

@app.websocket("/ws/radar")
async def radar_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    async with httpx.AsyncClient(timeout=0.25) as http_client:
        try:
            while True:
                # Recebe comandos da UI sem travar o loop de envio
                try:
                    client_msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.001)
                    if client_msg:
                        data = json.loads(client_msg)
                        cmd = data.get("command")
                        if cmd:
                            await http_client.post("http://127.0.0.1:27080/radar/command", json={"command": cmd})
                except asyncio.TimeoutError:
                    pass
                except Exception:
                    pass

                # Consulta estado atual do C# a 20Hz e transmite ao navegador
                try:
                    resp = await http_client.get("http://127.0.0.1:27080/radar/state")
                    if resp.status_code == 200:
                        await websocket.send_text(resp.text)
                except Exception:
                    await websocket.send_text(json.dumps({"status": "connecting", "players": []}))

                await asyncio.sleep(0.05) # Taxa de atualização estável de 20Hz
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

if __name__ == "__main__":
    import uvicorn
    print("[*] Iniciando CsBot Arsenal Web UI em http://localhost:8080...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
