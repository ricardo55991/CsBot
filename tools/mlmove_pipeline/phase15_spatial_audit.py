"""
Fase 1.5 - Validacao espacial do perfil de_mirage.json (SEM alterar o JSON).

Pipeline:
 1. Classificador de place Valve (kNN, k=30) treinado com `last_place_name` das 8 .dem brutas.
 2. Grade de caminhabilidade empirica (voxels 16x16x32u ocupados por pes de jogadores vivos nas 444 demos
    + 8 .dem). Substitui a projecao em NavMesh offline (nao ha parser de .nav do CS2 no pipeline).
 3. Eventos de HOLD: jogador vivo, velocidade 2D < 35 u/s, permanencia continua >= 1.5 s,
    raio <= 64u em torno da mediana. Frames de passagem sao descartados.
 4. Clustering por picos de densidade em 2D por faixa de altura (celula 24u, faixa Z 56u) e atribuicao
    3D (dz com peso 2) a ate 120u do pico. Medoid = posicao REAL observada de um jogador.
 5. Auditoria spot a spot com filtros de lado, fase do round e arma (AWP), escolha de cluster compativel
    e classificacao VALID / SMALL_ADJUSTMENT / WRONG_SECTOR / WRONG_HEIGHT / UNREACHABLE / AMBIGUOUS /
    INSUFFICIENT_EVIDENCE.
"""

from __future__ import annotations

import glob
import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from demoparser2 import DemoParser

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PIPELINE_DIR = Path(r"F:\CS2_MLMove_Pipeline")
NPZ_DIR = PIPELINE_DIR / "extracted_tensors" / "de_mirage"
RAW_DEM_GLOB = str(PIPELINE_DIR / "raw_demos" / "de_mirage" / "demos" / "**" / "*.dem")
MIRAGE_JSON = Path(r"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\src\CsBotManager\MapProfiles\de_mirage.json")
OUT_DIR = Path(r"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\docs\fase_1_5")

HOLD_SPEED = 35.0
HOLD_MIN_STEPS = 24          # 1.5 s a 16 Hz
HOLD_MAX_RADIUS = 64.0
DISCONT_U = 60.0
CELL = 24.0
ZBAND = 56.0
PEAK_MIN = 60                # eventos na janela 5x5 (120u)
ASSIGN_R = 120.0
RNG = np.random.default_rng(1337)

# ------------------------------------------------------------------------------------------------
# Lugares Valve esperados para cada spot (semantica do nome/descricao do de_mirage.json)
# ------------------------------------------------------------------------------------------------
EXPECTED = {
    "ct_a_ticket_passive": ["BombsiteA", "CTSpawn"],
    "ct_a_firebox_oneanddone": ["BombsiteA"],
    "ct_a_ninja_hide": ["BombsiteA"],
    "ct_a_triple_jiggle": ["BombsiteA"],
    "ct_a_stairs_cross": ["Stairs"],
    "ct_a_jungle_support": ["Jungle"],
    "ct_a_palace_close_poke": ["BombsiteA", "Scaffolding"],
    "ct_mid_window_crouch": ["SnipersNest"],
    "ct_mid_window_deep_awp": ["SnipersNest"],
    "ct_mid_connector_headshot": ["Connector"],
    "ct_mid_short_catwalk": ["Catwalk"],
    "ct_mid_underpass_peek": ["Underpass", "Ladder"],
    "ct_b_van_peek": ["Truck"],
    "ct_b_bench_deep": ["BombsiteB"],
    "ct_b_site_default_crouch": ["BombsiteB"],
    "ct_b_market_window": ["Shop"],
    "ct_b_market_door": ["Shop", "BombsiteB"],
    "ct_b_short_corner": ["BombsiteB", "Catwalk"],
    "ct_spawn_safe": ["CTSpawn"],
    "ct_jungle_safe": ["Jungle", "CTSpawn"],
    "tr_staging_a_ramp": ["TRamp"],
    "tr_staging_palace_room": ["PalaceInterior"],
    "tr_staging_top_mid_boxes": ["TopofMid"],
    "tr_staging_underpass_top": ["Middle", "Underpass"],
    "tr_staging_b_apartments_house": ["House", "BackAlley", "Apartments"],
    "tr_staging_b_apartments_kitchen": ["Apartments", "BackAlley"],
    "tr_staging_t_roof": ["PalaceAlley", "TSpawn", "TopofMid"],
    "tr_spawn_safe": ["TSpawn"],
    "tr_exec_a_site_default": ["BombsiteA"],
    "tr_exec_a_triple_clear": ["BombsiteA"],
    "tr_exec_a_stairs_clear": ["BombsiteA", "Stairs", "Jungle"],
    "tr_exec_mid_connector_push": ["Connector", "Middle"],
    "tr_exec_b_site_plant": ["BombsiteB"],
    "tr_exec_b_van_clear": ["BombsiteB", "Truck"],
    "tr_exec_b_market_push": ["BombsiteB", "Shop"],
    "ct_retake_a_connector": ["Connector"],
    "ct_retake_a_stairs": ["Stairs", "BombsiteA"],
    "ct_retake_a_jungle": ["Jungle"],
    "ct_retake_a_ticket": ["BombsiteA", "CTSpawn"],
    "ct_retake_a_defuse_cover": ["BombsiteA"],
    "ct_retake_b_market": ["Shop", "BombsiteB"],
    "ct_retake_b_short": ["Catwalk", "BombsiteB"],
    "ct_retake_b_entry": ["BombsiteB"],
    "ct_retake_b_defuse_cover": ["BombsiteB"],
    "ct_retake_b_awp_cover": ["BombsiteB", "Shop"],
}

# Sub-regioes geometricas 3D (xmin, xmax, ymin, ymax, zmin, zmax) para desambiguar landmarks
# dentro de um mesmo last_place_name da Valve (ex: BombsiteA contem Ticket, Firebox, Ninja, Triple, Under-Palace)
SUBREGION_BOX = {
    "ct_a_ticket_passive": (-1150, -780, -2560, -2180, -200, -90),
    "ct_retake_a_ticket": (-1280, -780, -2580, -1480, -200, -30),
    "ct_a_firebox_oneanddone": (-360, -180, -2460, -2100, -195, -140),
    "ct_a_ninja_hide": (-480, -220, -2420, -2120, -195, -140),
    "ct_a_triple_jiggle": (-780, -380, -2200, -1920, -195, -140),
    "ct_a_palace_close_poke": (-80, 260, -2020, -1800, -195, -140),
    "ct_a_stairs_cross": (-600, -400, -1680, -1250, -180, -20),
    "ct_a_jungle_support": (-1100, -720, -1580, -1220, -185, -130),
    "ct_retake_a_jungle": (-1100, -720, -1580, -1220, -185, -130),
    "ct_mid_window_crouch": (-1220, -1050, -620, -380, -190, -140),
    "ct_mid_window_deep_awp": (-1280, -1080, -820, -580, -190, -110),
    "ct_mid_connector_headshot": (-680, -440, -1260, -920, -190, -140),
    "ct_retake_a_connector": (-820, -440, -1280, -920, -190, -140),
    "ct_b_bench_deep": (-2650, -2420, 180, 600, -185, -140),
    "ct_b_site_default_crouch": (-2060, -1820, 120, 480, -185, -140),
    "ct_b_market_door": (-2420, -2150, 50, 420, -185, -140),
    "ct_b_short_corner": (-1500, -1200, 280, 560, -185, -140),
    "tr_staging_top_mid_boxes": (100, 480, -750, -120, -195, -130),
    "tr_staging_t_roof": (680, 1080, -1680, -980, -140, -80),
    "tr_staging_underpass_top": (-1080, -280, -980, -220, -380, -150),
    "tr_exec_a_site_default": (-380, -180, -2250, -1450, -195, -140),
    "tr_exec_a_triple_clear": (-580, -380, -2100, -1920, -195, -140),
}
AWP_SPOTS = {"ct_mid_window_deep_awp", "ct_retake_b_awp_cover"}


def spot_filter(spot_id: str) -> dict:
    sid = spot_id
    if sid.startswith("ct_retake_"):
        return {"side": 0, "tmin": 35.0, "tmax": 1e9, "phase": "late(>=35s)"}
    if sid in ("ct_spawn_safe", "ct_jungle_safe"):
        return {"side": 0, "tmin": 0.0, "tmax": 1e9, "phase": "any"}
    if sid.startswith("ct_"):
        return {"side": 0, "tmin": 0.0, "tmax": 65.0, "phase": "setup/mid(<=65s)"}
    if sid.startswith("tr_staging_"):
        return {"side": 1, "tmin": 0.0, "tmax": 50.0, "phase": "staging(<=50s)"}
    if sid.startswith("tr_exec_"):
        return {"side": 1, "tmin": 18.0, "tmax": 1e9, "phase": "execute(>=18s)"}
    return {"side": 1, "tmin": 0.0, "tmax": 1e9, "phase": "any"}


def spot_usage(spot: dict) -> str:
    if spot.get("usage"):
        return spot["usage"]
    sid = spot["id"]
    for key, val in (("staging", "Staging"), ("exec", "Execute"), ("retake", "Retake"), ("safe", "Fallback/Save")):
        if key in sid:
            return val
    return f"Hold:{spot.get('recommended_stance', '')}"


def spot_bombsite(spot: dict) -> str:
    if spot.get("associated_bombsite"):
        return spot["associated_bombsite"]
    s = spot.get("sector", "")
    return "A" if "A" in s.split()[-1:] else ("B" if s.endswith("B") else s)


def team_names(stem: str) -> list[str]:
    s = stem.replace("_16hz", "")
    s = re.sub(r"-m\d+-mirage.*$", "", s)
    s = re.sub(r"-mirage.*$", "", s)
    if "-vs-" in s:
        return [t.strip("-") for t in s.split("-vs-", 1)]
    return []


# ------------------------------------------------------------------------------------------------
# 1. Classificador de places a partir das demos brutas
# ------------------------------------------------------------------------------------------------
def load_place_model():
    xs, ys, zs, places, holds = [], [], [], [], []
    for dem in sorted(glob.glob(RAW_DEM_GLOB, recursive=True)):
        p = DemoParser(dem)
        df = p.parse_ticks(["X", "Y", "Z", "velocity_X", "velocity_Y", "last_place_name", "team_num",
                            "is_alive", "is_freeze_period", "is_warmup_period"])
        df = df[(df.is_alive == True) & (df.is_freeze_period == False) & (df.is_warmup_period == False)]  # noqa: E712
        df = df[df.team_num.isin([2, 3])]
        df = df[df.tick % 16 == 0]
        df = df[df.last_place_name.fillna("") != ""]
        xs.append(df.X.to_numpy()); ys.append(df.Y.to_numpy()); zs.append(df.Z.to_numpy())
        places.append(df.last_place_name.to_numpy())
        spd = np.hypot(df.velocity_X.fillna(0).to_numpy(), df.velocity_Y.fillna(0).to_numpy())
        holds.append(np.stack([df.X.to_numpy(), df.Y.to_numpy(), df.Z.to_numpy(),
                               (df.team_num.to_numpy() == 2).astype(float),
                               df.steamid.astype("int64").to_numpy().astype(float), spd], axis=1))
        print(f"[places] {Path(dem).stem}: {len(df)} amostras", flush=True)
    P = np.stack([np.concatenate(xs), np.concatenate(ys), np.concatenate(zs)], axis=1).astype(np.float64)
    L = np.concatenate(places)
    H = np.concatenate(holds)
    return P, L, H


def classify_place(P, L, q, k=30):
    d2 = (P[:, 0] - q[0]) ** 2 + (P[:, 1] - q[1]) ** 2 + (2.0 * (P[:, 2] - q[2])) ** 2
    idx = np.argpartition(d2, k)[:k]
    c = Counter(L[idx])
    top, cnt = c.most_common(1)[0]
    second = c.most_common(2)[1][0] if len(c) > 1 else None
    return {"place": str(top), "purity": round(cnt / k, 2), "second": second,
            "nearest_sample_u": round(float(math.sqrt(d2[idx].min())), 1)}


# ------------------------------------------------------------------------------------------------
# 2. Grade de caminhabilidade + 3. eventos de HOLD (passo unico pelas 444 npz)
# ------------------------------------------------------------------------------------------------
def vkey(x, y, z):
    ix = np.floor(x / 16.0).astype(np.int64) + 512
    iy = np.floor(y / 16.0).astype(np.int64) + 512
    iz = np.floor(z / 32.0).astype(np.int64) + 64
    return (ix * 1024 + iy) * 128 + iz


def scan_npz():
    files = sorted(NPZ_DIR.glob("*_16hz.npz"))
    keys_acc = []
    ev = []
    stems = []
    rejected_drift = 0
    t0 = time.time()
    for di, f in enumerate(files):
        stems.append(f.stem)
        with np.load(f) as d:
            X = d["X"]
        Xc, Xt = X[0::2], X[1::2]
        T = min(len(Xc), len(Xt))
        full = np.where(Xc[:T, :, 13:14] < 0.5, Xc[:T], Xt[:T])
        alive = full[:, :, 14] > 0.5
        px, py, pz = full[:, :, 0] * 4096.0, full[:, :, 1] * 4096.0, full[:, :, 2] * 1024.0
        vx, vy = full[:, :, 3] * 250.0, full[:, :, 4] * 250.0
        is_tr = full[:, :, 13] > 0.5
        awp = full[:, :, 11] >= 0.99
        spd = np.hypot(vx, vy)

        keys_acc.append(np.unique(vkey(px[alive], py[alive], pz[alive])))

        # inicio de round = teletransporte (> 900u) de jogadores VIVOS em passos consecutivos ou aumento do total de vivos
        alive_both = alive[:-1] & alive[1:]
        dx_a = np.where(alive_both, np.abs(np.diff(px, axis=0)), 0.0)
        dy_a = np.where(alive_both, np.abs(np.diff(py, axis=0)), 0.0)
        jump = np.maximum(dx_a.max(axis=1), dy_a.max(axis=1))
        alive_cnt = alive.sum(axis=1)
        respawn = np.diff(alive_cnt) >= 2
        resets = [0]
        for r in np.where((jump > 900.0) | respawn)[0] + 1:
            if r - resets[-1] >= 80:
                resets.append(int(r))
        rs = np.zeros(T, dtype=np.int64)
        for r in resets:
            rs[r:] = r
        t_rs = (np.arange(T) - rs) / 16.0
        ct_alive = (alive & ~is_tr).sum(axis=1)
        tr_alive = (alive & is_tr).sum(axis=1)

        disp = np.sqrt(np.diff(px, axis=0) ** 2 + np.diff(py, axis=0) ** 2 + np.diff(pz, axis=0) ** 2)
        cont = np.vstack([np.zeros((1, 10), bool), disp <= DISCONT_U])
        hold = alive & (spd < HOLD_SPEED)
        for s in range(10):
            h = hold[:, s] & cont[:, s]
            # run boundaries
            hh = np.r_[False, h, False].astype(np.int8)
            starts = np.where(np.diff(hh) == 1)[0]
            ends = np.where(np.diff(hh) == -1)[0]
            for a, b in zip(starts, ends):
                if b - a < HOLD_MIN_STEPS:
                    continue
                xs, ys, zs = px[a:b, s], py[a:b, s], pz[a:b, s]
                mx, my, mz = float(np.median(xs)), float(np.median(ys)), float(np.median(zs))
                if np.sqrt((xs - mx) ** 2 + (ys - my) ** 2).max() > HOLD_MAX_RADIUS:
                    rejected_drift += 1
                    continue
                ev.append((mx, my, mz, (b - a) / 16.0, float(is_tr[a, s]), di, s, float(t_rs[a]),
                           float(awp[a:b, s].mean() > 0.5), float(ct_alive[a]), float(tr_alive[a])))
        if (di + 1) % 100 == 0 or di + 1 == len(files):
            print(f"[npz] {di + 1}/{len(files)} eventos={len(ev)} ({time.time() - t0:.1f}s)", flush=True)
    keys = np.unique(np.concatenate(keys_acc))
    E = np.array(ev, dtype=np.float64)
    return keys, E, stems, rejected_drift


def walk_query(keys, x, y, z):
    ix0 = int(math.floor(x / 16.0)); iy0 = int(math.floor(y / 16.0)); iz0 = int(math.floor(z / 32.0))
    cand3d, cand_xy = [], []
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            for dz in (-1, 0, 1):
                cand3d.append(((ix0 + dx + 512) * 1024 + (iy0 + dy + 512)) * 128 + (iz0 + dz + 64))
            for iz in range(-20, 10):
                cand_xy.append((((ix0 + dx + 512) * 1024 + (iy0 + dy + 512)) * 128 + (iz + 64), iz))
    w3 = bool(np.isin(np.array(cand3d, dtype=np.int64), keys).any())
    arr = np.array([c for c, _ in cand_xy], dtype=np.int64)
    hit = np.isin(arr, keys)
    zs = sorted({cand_xy[i][1] * 32 + 16 for i in np.where(hit)[0]})
    return w3, bool(hit.any()), zs


# ------------------------------------------------------------------------------------------------
# 4. Clustering por picos de densidade
# ------------------------------------------------------------------------------------------------
def box_sum(a, r):
    k = 2 * r + 1
    p = np.pad(a, r)
    c = p.cumsum(0).cumsum(1)
    c = np.pad(c, ((1, 0), (1, 0)))
    return c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]


def cluster_events(E):
    x, y, z = E[:, 0], E[:, 1], E[:, 2]
    x0, y0 = x.min() - 200, y.min() - 200
    nx = int((x.max() + 200 - x0) / CELL) + 1
    ny = int((y.max() + 200 - y0) / CELL) + 1
    zb = np.floor((z + 600.0) / ZBAND).astype(int)
    peaks = []
    for b in np.unique(zb):
        m = zb == b
        if m.sum() < PEAK_MIN:
            continue
        ix = ((x[m] - x0) / CELL).astype(int)
        iy = ((y[m] - y0) / CELL).astype(int)
        H = np.zeros((nx, ny))
        np.add.at(H, (ix, iy), 1)
        S = box_sum(H, 2)
        Mx = S.copy()
        Pd = np.pad(S, 3, constant_values=-1)
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                Mx = np.maximum(Mx, Pd[3 + dx:3 + dx + nx, 3 + dy:3 + dy + ny])
        pk = np.argwhere((S >= Mx) & (S >= PEAK_MIN))
        zm = float(np.median(z[m]))
        for i, j in pk:
            cx, cy = x0 + (i + 0.5) * CELL, y0 + (j + 0.5) * CELL
            near = m & (np.hypot(x - cx, y - cy) <= 60)
            peaks.append((cx, cy, float(np.median(z[near])) if near.any() else zm))
    Pk = np.array(peaks)
    labels = -np.ones(len(E), dtype=int)
    for a in range(0, len(E), 40000):
        sl = slice(a, a + 40000)
        d2 = (x[sl, None] - Pk[None, :, 0]) ** 2 + (y[sl, None] - Pk[None, :, 1]) ** 2 + (2 * (z[sl, None] - Pk[None, :, 2])) ** 2
        j = d2.argmin(axis=1)
        ok = d2[np.arange(len(j)), j] <= ASSIGN_R ** 2
        labels[sl] = np.where(ok, j, -1)
    return Pk, labels


def medoid(pts):
    if len(pts) > 1500:
        pts = pts[RNG.choice(len(pts), 1500, replace=False)]
    d = np.sqrt(((pts[:, None, :2] - pts[None, :, :2]) ** 2).sum(-1) + (2 * (pts[:, None, 2] - pts[None, :, 2])) ** 2)
    return pts[d.sum(1).argmin()]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    profile = json.load(open(MIRAGE_JSON, encoding="utf-8"))
    spots = profile["spots"]
    P, L, Hdem = load_place_model()
    keys_npz, E, stems, rejected_drift = scan_npz()
    keys = np.unique(np.concatenate([keys_npz, np.unique(vkey(P[:, 0], P[:, 1], P[:, 2]))]))
    n_demos = len(stems)
    demo_teams = [team_names(s) for s in stems]
    print(f"[+] eventos HOLD={len(E)} | rejeitados por deriva={rejected_drift} | voxels={len(keys)}", flush=True)

    place_centroids = {}
    for pl in np.unique(L):
        m = L == pl
        place_centroids[str(pl)] = P[m].mean(0)

    Pk, labels = cluster_events(E)
    clusters = []
    for c in range(len(Pk)):
        m = labels == c
        if m.sum() < 30:
            continue
        ce = E[m]
        md = medoid(ce[:, :3])
        demos = np.unique(ce[:, 5]).astype(int)
        players = len({(int(a), int(b)) for a, b in ce[:, 5:7]})
        teams = {t for d in demos for t in demo_teams[d]}
        std2d = float(np.sqrt(ce[:, 0].var() + ce[:, 1].var()))
        ct_ratio = float((ce[:, 4] < 0.5).mean())
        tq = ce[:, 7]
        conf = 0.5 * min(1.0, len(demos) / 150) + 0.25 * (1 - min(1.0, std2d / 80)) + 0.25 * min(1.0, float(np.median(ce[:, 3])) / 4)
        pl = classify_place(P, L, md)
        w3, wxy, _ = walk_query(keys, *md)
        clusters.append({
            "cluster_id": c,
            "centroid": [round(float(ce[:, 0].mean()), 1), round(float(ce[:, 1].mean()), 1), round(float(ce[:, 2].mean()), 1)],
            "medoid": [round(float(md[0]), 1), round(float(md[1]), 1), round(float(md[2]), 1)],
            "valve_place": pl["place"], "place_purity": pl["purity"],
            "sample_count": int(m.sum()), "unique_demos": int(len(demos)),
            "unique_player_instances": players, "unique_team_names": len(teams),
            "median_dwell_s": round(float(np.median(ce[:, 3])), 2),
            "ct_ratio": round(ct_ratio, 3), "tr_ratio": round(1 - ct_ratio, 3),
            "awp_ratio": round(float(ce[:, 8].mean()), 3),
            "phase_ratio": {"early_le20s": round(float((tq <= 20).mean()), 3),
                            "mid_20_55s": round(float(((tq > 20) & (tq <= 55)).mean()), 3),
                            "late_gt55s": round(float((tq > 55).mean()), 3)},
            "spread_std2d_u": round(std2d, 1),
            "movement_state": "HOLD (v2d<35u/s, permanencia>=1.5s)",
            "medoid_empirically_walkable": w3,
            "cluster_confidence": round(conf, 3),
        })
    clusters.sort(key=lambda c: -c["unique_demos"])
    cl_by_id = {c["cluster_id"]: c for c in clusters}
    print(f"[+] clusters validos={len(clusters)}", flush=True)

    def evidence(mask):
        ce = E[mask]
        if len(ce) == 0:
            return {"count": 0, "demos": 0, "players": 0, "dwell": None}
        return {"count": int(len(ce)), "demos": int(len(np.unique(ce[:, 5]))),
                "players": int(len({(int(a), int(b)) for a, b in ce[:, 5:7]})),
                "dwell": round(float(np.median(ce[:, 3])), 2)}

    audits = []
    used_clusters = {0: set(), 1: set()}
    # ordem: spots com setor correto primeiro (para reservarem seu cluster), depois os demais
    pre = []
    for s in spots:
        sid = s["id"]
        q = np.array([float(s["x"]), float(s["y"]), float(s["z"])])
        f = spot_filter(sid)
        fm = (E[:, 4] == f["side"]) & (E[:, 7] >= f["tmin"]) & (E[:, 7] <= f["tmax"])
        if sid in AWP_SPOTS:
            fm &= E[:, 8] > 0.5
        pl = classify_place(P, L, q)
        w3, wxy, wz = walk_query(keys, *q)
        d_local = np.sqrt((E[:, 0] - q[0]) ** 2 + (E[:, 1] - q[1]) ** 2 + (2 * (E[:, 2] - q[2])) ** 2)
        local = evidence(fm & (d_local <= 96))
        exp = EXPECTED.get(sid, [])
        box = SUBREGION_BOX.get(sid)
        cands = []
        for c in clusters:
            if c["valve_place"] not in exp:
                continue
            cm = (labels == c["cluster_id"]) & fm
            ev = evidence(cm)
            if ev["demos"] < 15:
                continue
            md = np.array(c["medoid"])
            dist = float(np.sqrt(((md[:2] - q[:2]) ** 2).sum() + (2 * (md[2] - q[2])) ** 2))
            score = ev["demos"] * (0.5 + 0.5 * c["cluster_confidence"])
            in_subbox = False
            if box is not None:
                x0, x1, y0, y1, z0, z1 = box
                dx_b = max(0.0, x0 - md[0], md[0] - x1)
                dy_b = max(0.0, y0 - md[1], md[1] - y1)
                dz_b = max(0.0, z0 - md[2], md[2] - z1)
                d_box = math.sqrt(dx_b ** 2 + dy_b ** 2 + (2 * dz_b) ** 2)
                in_subbox = d_box == 0.0
                score *= 2.5 if in_subbox else math.exp(-d_box / 220.0)
            cands.append({"cluster_id": c["cluster_id"], "medoid": c["medoid"], "valve_place": c["valve_place"],
                          "in_subregion": in_subbox,
                          "filtered_evidence": ev, "distance_from_current_u": round(dist, 1),
                          "cluster_confidence": c["cluster_confidence"], "score": round(score, 2)})
        cands.sort(key=lambda c: (-int(c["in_subregion"]), -c["score"]))
        pre.append((s, q, f, pl, w3, wxy, wz, local, exp, cands))

    order = sorted(range(len(pre)), key=lambda i: (pre[i][3]["place"] not in pre[i][8], -(pre[i][9][0]["score"] if pre[i][9] else 0)))
    for i in order:
        s, q, f, pl, w3, wxy, wz, local, exp, cands = pre[i]
        sid = s["id"]
        side = f["side"]
        reason = []
        if not wxy:
            cls = "UNREACHABLE"; reason.append("nenhum pe de jogador observado num raio de 32u em qualquer altura")
        elif not w3:
            cls = "WRONG_HEIGHT"; reason.append(f"XY caminhavel, mas Z={q[2]:.0f} fora das alturas observadas {wz}")
        elif pl["place"] not in exp:
            if pl["purity"] < 0.55 and pl["second"] in exp:
                cls = "AMBIGUOUS"; reason.append(f"place kNN dividido: {pl['place']} vs {pl['second']}")
            else:
                cls = "WRONG_SECTOR"; reason.append(f"place real={pl['place']} (pureza {pl['purity']}), esperado={exp}")
        else:
            near = min(cands, key=lambda c: c["distance_from_current_u"]) if cands else None
            if near and near["distance_from_current_u"] <= 64:
                cls = "VALID"; reason.append(f"cluster profissional {near['cluster_id']} a {near['distance_from_current_u']}u")
            elif local["demos"] >= 40:
                cls = "VALID"; reason.append(f"posicao propria com evidencia ({local['demos']} demos) mesmo fora de pico")
            elif near and near["distance_from_current_u"] <= 260 and near["filtered_evidence"]["demos"] >= 30:
                cls = "SMALL_ADJUSTMENT"; reason.append(f"pico profissional a {near['distance_from_current_u']}u com {near['filtered_evidence']['demos']} demos")
            elif local["demos"] < 15:
                cls = "INSUFFICIENT_EVIDENCE"; reason.append(f"apenas {local['demos']} demos com hold compativel em 96u")
            else:
                cls = "VALID"; reason.append(f"evidencia local moderada ({local['demos']} demos)")

        proposal, resolution, chosen = None, "KEEP", None
        if cls == "SMALL_ADJUSTMENT":
            chosen = min(cands, key=lambda c: c["distance_from_current_u"])
            resolution = "RESOLVED_NEAREST_PEAK"
        elif cls in ("WRONG_SECTOR", "WRONG_HEIGHT", "UNREACHABLE", "AMBIGUOUS", "INSUFFICIENT_EVIDENCE"):
            free = [c for c in cands if c["cluster_id"] not in used_clusters[side]]
            pool = free or cands
            if pool:
                chosen = pool[0]
                if cls == "INSUFFICIENT_EVIDENCE":
                    resolution = "PROPOSED_NEAREST_CLUSTER_FOR_LOW_EVIDENCE"
                elif chosen.get("in_subregion"):
                    resolution = "RESOLVED_LANDMARK_SUBREGION"
                else:
                    multi = sum(1 for x in pre if x[2]["side"] == side and set(x[8]) & set(exp) and x[0]["id"] != sid) > 0
                    close_second = len(pool) > 1 and pool[1]["score"] >= 0.75 * pool[0]["score"]
                    resolution = "NEEDS_VISUAL_CONFIRMATION" if (multi or close_second) else "RESOLVED_UNIQUE_PLACE"
            else:
                resolution = "NO_COMPATIBLE_CLUSTER"
        if chosen:
            used_clusters[side].add(chosen["cluster_id"])
            proposal = chosen["medoid"]
        elif cls == "VALID":
            near = min(cands, key=lambda c: c["distance_from_current_u"]) if cands else None
            if near and near["distance_from_current_u"] <= 64:
                used_clusters[side].add(near["cluster_id"])

        ev_used = chosen["filtered_evidence"] if chosen else local
        cconf = cl_by_id[chosen["cluster_id"]]["cluster_confidence"] if chosen else 0.0
        if cls == "VALID":
            conf = 0.6 + 0.4 * min(1.0, local["demos"] / 200)
        elif chosen:
            conf = 0.5 * min(1.0, ev_used["demos"] / 200) + 0.3 * cconf + (0.2 if resolution.startswith("RESOLVED") else 0.0)
        else:
            conf = 0.1
        yaw = float(s.get("yaw", 0.0))
        audits.append({
            "SpotId": sid,
            "Name": s.get("name"),
            "CurrentPosition": [float(s["x"]), float(s["y"]), float(s["z"])],
            "ExpectedValvePlace": exp,
            "ActualValvePlace": pl["place"],
            "ActualPlacePurity": pl["purity"],
            "TeamSide": s.get("side"),
            "Usage": spot_usage(s),
            "AssociatedBombsite": spot_bombsite(s),
            "NavMeshValid": "UNVERIFIED_RUNTIME",
            "EmpiricallyWalkable3D": w3,
            "EmpiricallyWalkableXYAnyHeight": wxy,
            "ObservedFloorHeightsAtXY": wz,
            "CurrentClassification": cls,
            "ClassificationReason": "; ".join(reason),
            "ProposedPosition": proposal,
            "ProposalResolution": resolution,
            "ProposalShift_u": round(float(np.linalg.norm(np.array(proposal) - q)), 1) if proposal else 0.0,
            "EvidenceCount": ev_used["count"],
            "DemoDiversity": ev_used["demos"],
            "DemoDiversityPct": round(100 * ev_used["demos"] / n_demos, 1),
            "PlayerDiversity": ev_used["players"],
            "PlayerDiversityNote": "instancias (demo,slot); steamid ausente nas npz",
            "HoldDurationMedian": ev_used["dwell"],
            "Confidence": round(conf, 3),
            "FilterApplied": {"side": "CT" if f["side"] == 0 else "TR", "phase": f["phase"], "awp_only": sid in AWP_SPOTS},
            "LocalEvidenceAtCurrent": local,
            "Candidates": cands[:4],
            "SetposCurrent": f"setpos {s['x']} {s['y']} {s['z']}; setang 0 {yaw} 0",
            "SetposProposed": f"setpos {proposal[0]} {proposal[1]} {proposal[2]}; setang 0 {yaw} 0" if proposal else None,
        })
    audits.sort(key=lambda a: [x["id"] for x in spots].index(a["SpotId"]))

    summary = Counter(a["CurrentClassification"] for a in audits)
    meta = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "map_profile_file": str(MIRAGE_JSON),
        "spots": len(audits),
        "classification_counts": dict(summary),
        "method": {
            "place_model": f"kNN k=30 sobre {len(P)} amostras last_place_name (8 .dem), metrica dx^2+dy^2+(2dz)^2",
            "walkability": f"proxy empirico: {len(keys)} voxels 16x16x32u ocupados por pes de jogadores vivos; NAO e projecao em NavMesh",
            "hold_events": f"{len(E)} eventos (v2d<{HOLD_SPEED}, >= {HOLD_MIN_STEPS / 16}s, raio<= {HOLD_MAX_RADIUS}u); {rejected_drift} descartados por deriva",
            "clusters": f"picos de densidade (celula {CELL}u, faixa Z {ZBAND}u, min {PEAK_MIN}), atribuicao <= {ASSIGN_R}u com dz*2",
            "role_filter": "somente AWP (feature arma); papeis reais ausentes nas npz (role_code sintetico)",
            "phase_filter": "tempo desde o reset do round (freeze removido); bomb_planted ausente nas npz",
        },
    }
    json.dump({**meta, "audit": audits}, open(OUT_DIR / "mirage_spot_audit.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump({**meta, "clusters": clusters}, open(OUT_DIR / "mirage_spot_clusters.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    # SVG para inspecao visual
    sub = E[RNG.choice(len(E), min(60000, len(E)), replace=False)]
    xmin, xmax, ymin, ymax = -2900, 1700, -2800, 1200
    W, Hh = 1150, 1000
    sx = lambda v: (v - xmin) / (xmax - xmin) * W
    sy = lambda v: Hh - (v - ymin) / (ymax - ymin) * Hh
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hh}" style="background:#111">']
    for e in sub:
        col = "#3a6ea5" if e[4] < 0.5 else "#a5703a"
        out.append(f'<circle cx="{sx(e[0]):.1f}" cy="{sy(e[1]):.1f}" r="0.8" fill="{col}" opacity="0.35"/>')
    for pl, c in place_centroids.items():
        out.append(f'<text x="{sx(c[0]):.0f}" y="{sy(c[1]):.0f}" fill="#888" font-size="11" font-family="monospace">{pl}</text>')
    colors = {"VALID": "#3cff6e", "SMALL_ADJUSTMENT": "#ffe23c", "WRONG_SECTOR": "#ff3c3c", "WRONG_HEIGHT": "#ff8c3c",
              "UNREACHABLE": "#ff3cf0", "AMBIGUOUS": "#3cf0ff", "INSUFFICIENT_EVIDENCE": "#aaaaaa"}
    for a in audits:
        cx, cy = sx(a["CurrentPosition"][0]), sy(a["CurrentPosition"][1])
        col = colors[a["CurrentClassification"]]
        if a["ProposedPosition"]:
            px_, py_ = sx(a["ProposedPosition"][0]), sy(a["ProposedPosition"][1])
            out.append(f'<line x1="{cx:.0f}" y1="{cy:.0f}" x2="{px_:.0f}" y2="{py_:.0f}" stroke="{col}" stroke-width="1" stroke-dasharray="4,3"/>')
            out.append(f'<circle cx="{px_:.0f}" cy="{py_:.0f}" r="5" fill="none" stroke="#ffffff" stroke-width="1.5"/>')
        out.append(f'<rect x="{cx - 4:.0f}" y="{cy - 4:.0f}" width="8" height="8" fill="{col}"/>')
        out.append(f'<text x="{cx + 6:.0f}" y="{cy - 4:.0f}" fill="{col}" font-size="9" font-family="monospace">{a["SpotId"]}</text>')
    lx = 10
    for k, v in colors.items():
        out.append(f'<rect x="{lx}" y="10" width="10" height="10" fill="{v}"/><text x="{lx + 14}" y="19" fill="#ddd" font-size="11" font-family="monospace">{k}</text>')
        lx += 160 if len(k) > 10 else 90
    out.append('<text x="10" y="40" fill="#ddd" font-size="11" font-family="monospace">pontos: holds CT (azul) / TR (laranja) | quadrado = posicao atual | circulo branco = proposta</text>')
    out.append("</svg>")
    (OUT_DIR / "mirage_spot_audit_map.svg").write_text("\n".join(out), encoding="utf-8")

    print(json.dumps(meta["classification_counts"], indent=1))
    for a in audits:
        print(f"{a['SpotId']:34s} {a['CurrentClassification']:22s} real={a['ActualValvePlace']:15s} exp={','.join(a['ExpectedValvePlace']):28s} -> {a['ProposedPosition']} [{a['ProposalResolution']}] demos={a['DemoDiversity']} conf={a['Confidence']}")


if __name__ == "__main__":
    main()
