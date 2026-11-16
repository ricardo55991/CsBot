"""
Fase 1.5 - Auditoria de rotulos de Jump (V1 vs. detector balistico V2).

Parte A (8 .dem brutas, 64 Hz):
  - Mede a confiabilidade dos sinais disponiveis no GOTV: bit IN_JUMP de `buttons`, `is_airborne`.
  - Define o detector de referencia "takeoff balistico 64 Hz":
        vz[t] - vz[t-1] >= 120  E  120 <= vz[t] < 600  E
        inclinacao media de vz em t..t+4 entre -20 e -6 u/s por tick (gravidade 800 u/s^2 = -12.5/tick)
  - Reamostra a 16 Hz (stride 4) e mede precisao/recall do detector 16 Hz contra o de 64 Hz.

Parte B (444 .npz, 16 Hz):
  - Reproduz o rotulo antigo (ActionId >= 49, gerado por |vz| > 45 em contract_spec.velocity_to_action_id).
  - Aplica o detector balistico 16 Hz e os estados fisicos (Grounded / Rising / Falling / Landing).
  - Detecta BunnyHop / salto encadeado (takeoff sem amostra no chao entre a queda anterior e o novo impulso).

Nenhum treinamento e realizado.
"""

from __future__ import annotations

import glob
import json
import sys
import time
from pathlib import Path

import numpy as np
from demoparser2 import DemoParser

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PIPELINE_DIR = Path(r"F:\CS2_MLMove_Pipeline")
NPZ_DIR = PIPELINE_DIR / "extracted_tensors" / "de_mirage"
RAW_DEM_GLOB = str(PIPELINE_DIR / "raw_demos" / "de_mirage" / "demos" / "**" / "*.dem")
OUT_DIR = Path(r"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\docs\fase_1_5")

# Limiares 16 Hz (passo = 62.5 ms; gravidade = -50 u/s por passo)
T16_MIN_VZ = 120.0
T16_MAX_PREV_VZ = 60.0
T16_MIN_DELTA = 100.0
T16_BALLISTIC_MIN = -85.0
T16_BALLISTIC_MAX = -20.0
CHAINED_PREV_VZ = -40.0
STATE_EPS = 40.0
DISCONTINUITY_U = 60.0


def detect_takeoff_16hz(vz: np.ndarray, cont: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """vz [T]; cont[i] = amostra i-1 -> i e continua. Retorna (takeoff, chained)."""
    T = len(vz)
    prev = np.r_[0.0, vz[:-1]]
    nxt = np.r_[vz[1:], 0.0]
    cont_next = np.r_[cont[1:], False]
    d1 = nxt - vz
    takeoff = (
        cont & cont_next
        & (vz >= T16_MIN_VZ) & (vz < 600.0)
        & (prev <= T16_MAX_PREV_VZ)
        & ((vz - prev) >= T16_MIN_DELTA)
        & (d1 >= T16_BALLISTIC_MIN) & (d1 <= T16_BALLISTIC_MAX)
    )
    chained = takeoff & (prev < CHAINED_PREV_VZ)
    return takeoff, chained


def physical_states_16hz(vz: np.ndarray, cont: np.ndarray) -> dict[str, np.ndarray]:
    grounded = np.abs(vz) <= STATE_EPS
    rising = vz > STATE_EPS
    falling = vz < -STATE_EPS
    prev_falling = np.r_[False, falling[:-1]] & cont
    landing = grounded & prev_falling
    return {"grounded": grounded, "rising": rising, "falling": falling, "landing": landing}


# ----------------------------------------------------------------------------------------------
# Parte A - 8 demos brutas a 64 Hz
# ----------------------------------------------------------------------------------------------
def audit_raw_demos() -> dict:
    dems = sorted(glob.glob(RAW_DEM_GLOB, recursive=True))
    tot = dict(player_ticks=0, takeoff64=0, chained64=0, takeoff64_with_injump=0, injump_edges=0,
               injump_edges_followed_by_takeoff=0, takeoff64_airborne_flag_t2=0,
               t16=0, t16_matched=0, t64_recalled=0, chained16=0)
    per_demo = []
    for dem in dems:
        p = DemoParser(dem)
        df = p.parse_ticks(["velocity_Z", "buttons", "is_airborne", "is_alive", "is_freeze_period", "is_warmup_period"])
        df = df[(df.is_alive == True) & (df.is_freeze_period == False) & (df.is_warmup_period == False)]  # noqa: E712
        df = df.sort_values(["steamid", "tick"])
        d_stats = dict(demo=Path(dem).stem, player_ticks=len(df), takeoff64=0, chained64=0, t16=0, t16_matched=0)
        for _, g in df.groupby("steamid"):
            tk = g.tick.to_numpy()
            vz = g.velocity_Z.fillna(0).to_numpy(dtype=np.float64)
            b = g.buttons.fillna(0).astype("int64").to_numpy()
            air = g.is_airborne.fillna(False).to_numpy(dtype=bool)
            n = len(tk)
            if n < 10:
                continue
            cont = np.r_[False, np.diff(tk) == 1]
            prev = np.r_[0.0, vz[:-1]]
            # inclinacao media t..t+4 com continuidade
            cont4 = np.ones(n, dtype=bool)
            for k in range(1, 5):
                cont4 &= np.r_[cont[k:], np.zeros(k, dtype=bool)]
            vz4 = np.r_[vz[4:], np.zeros(4)]
            slope = (vz4 - vz) / 4.0
            take64 = cont & cont4 & ((vz - prev) >= 120) & (vz >= 120) & (vz < 600) & (slope >= -20) & (slope <= -6)
            idx = np.where(take64)[0]
            chained = np.array([bool((vz[max(0, i - 4):i] < -50).any()) for i in idx], dtype=bool)
            jb = (b & 2) != 0
            edges = np.where(jb & np.r_[True, ~jb[:-1]] & cont)[0]
            tot["takeoff64"] += len(idx)
            tot["chained64"] += int(chained.sum())
            tot["takeoff64_with_injump"] += int(sum(jb[max(0, i - 8):i + 2].any() for i in idx))
            tot["injump_edges"] += len(edges)
            tot["injump_edges_followed_by_takeoff"] += int(sum(take64[i:i + 9].any() for i in edges))
            tot["takeoff64_airborne_flag_t2"] += int(air[np.minimum(idx + 2, n - 1)].sum())
            d_stats["takeoff64"] += len(idx)
            d_stats["chained64"] += int(chained.sum())

            # Reamostragem 16 Hz alinhada em tick % 4 == 0
            m16 = (tk % 4) == 0
            tk16, vz16 = tk[m16], vz[m16]
            cont16 = np.r_[False, np.diff(tk16) == 4]
            t16, ch16 = detect_takeoff_16hz(vz16, cont16)
            t16_ticks = tk16[t16]
            t64_ticks = tk[idx]
            matched = sum(bool(((t64_ticks > t - 8) & (t64_ticks <= t)).any()) for t in t16_ticks)
            recalled = sum(bool(((t16_ticks >= t) & (t16_ticks < t + 8)).any()) for t in t64_ticks)
            tot["t16"] += len(t16_ticks)
            tot["t16_matched"] += int(matched)
            tot["t64_recalled"] += int(recalled)
            tot["chained16"] += int(ch16.sum())
            d_stats["t16"] += len(t16_ticks)
            d_stats["t16_matched"] += int(matched)
        tot["player_ticks"] += d_stats["player_ticks"]
        per_demo.append(d_stats)
        print(f"[A] {Path(dem).stem}: takeoff64={d_stats['takeoff64']} t16={d_stats['t16']}", flush=True)

    t64 = max(1, tot["takeoff64"])
    return {
        "demos": len(dems),
        "totals": tot,
        "signal_reliability": {
            "IN_JUMP_bit_present_near_takeoff_pct": round(100 * tot["takeoff64_with_injump"] / t64, 1),
            "IN_JUMP_edges_followed_by_takeoff_pct": round(100 * tot["injump_edges_followed_by_takeoff"] / max(1, tot["injump_edges"]), 1),
            "is_airborne_true_at_takeoff_plus_2_ticks_pct": round(100 * tot["takeoff64_airborne_flag_t2"] / t64, 1),
            "verdict": "IN_JUMP e is_airborne do GOTV NAO sao confiaveis como ground truth; usar assinatura balistica de vz.",
        },
        "detector_16hz_vs_64hz": {
            "precision_pct": round(100 * tot["t16_matched"] / max(1, tot["t16"]), 1),
            "recall_pct": round(100 * tot["t64_recalled"] / t64, 1),
            "match_window": "takeoff 64Hz em (tau-8, tau] ticks para cada takeoff 16Hz em tau",
        },
        "takeoffs_per_player_minute_64hz": round(tot["takeoff64"] / max(1e-9, tot["player_ticks"] / 64.0 / 60.0), 3),
        "chained_takeoff_pct_64hz": round(100 * tot["chained64"] / t64, 2),
        "per_demo": per_demo,
    }


# ----------------------------------------------------------------------------------------------
# Parte B - 444 npz a 16 Hz
# ----------------------------------------------------------------------------------------------
def audit_npz() -> dict:
    files = sorted(NPZ_DIR.glob("*_16hz.npz"))
    acc = dict(alive_frames=0, old_jump=0, old_jump_rising=0, old_jump_falling=0, old_jump_grounded_small_vz=0,
               takeoff=0, chained=0, grounded=0, rising=0, falling=0, landing=0,
               rising_without_takeoff_window=0, discontinuities=0)
    t0 = time.time()
    for fi, f in enumerate(files, 1):
        with np.load(f) as d:
            X, Y = d["X"], d["Y"]
        X_ct, X_tr, Ys = X[0::2], X[1::2], Y[0::2]
        T = min(len(X_ct), len(X_tr))
        full = np.where(X_ct[:T, :, 13:14] < 0.5, X_ct[:T], X_tr[:T])
        alive = full[:, :, 14] > 0.5
        px, py, pz = full[:, :, 0] * 4096, full[:, :, 1] * 4096, full[:, :, 2] * 1024
        vz = full[:, :, 5] * 250.0
        act = Ys[:T, :, 0]
        disp = np.sqrt(np.diff(px, axis=0) ** 2 + np.diff(py, axis=0) ** 2 + np.diff(pz, axis=0) ** 2)
        cont = np.vstack([np.zeros((1, 10), bool), (disp <= DISCONTINUITY_U) & alive[1:] & alive[:-1]])
        acc["discontinuities"] += int(((disp > DISCONTINUITY_U) & alive[1:] & alive[:-1]).sum())
        acc["alive_frames"] += int(alive.sum())
        old = (act >= 49) & alive
        acc["old_jump"] += int(old.sum())
        acc["old_jump_rising"] += int((old & (vz > STATE_EPS)).sum())
        acc["old_jump_falling"] += int((old & (vz < -STATE_EPS)).sum())
        acc["old_jump_grounded_small_vz"] += int((old & (np.abs(vz) <= STATE_EPS)).sum())
        for s in range(10):
            a = alive[:, s]
            v = vz[:, s]
            c = cont[:, s]
            tk, ch = detect_takeoff_16hz(v, c)
            tk &= a
            ch &= a
            st = physical_states_16hz(v, c)
            acc["takeoff"] += int(tk.sum())
            acc["chained"] += int(ch.sum())
            for k in ("grounded", "rising", "falling", "landing"):
                acc[k] += int((st[k] & a).sum())
            # subida sem takeoff nos 8 passos anteriores (escada, rampa ingreme, boost, ruido)
            recent = np.convolve(tk.astype(int), np.ones(8, int), mode="full")[:len(tk)] > 0
            acc["rising_without_takeoff_window"] += int((st["rising"] & a & ~recent).sum())
        if fi % 100 == 0 or fi == len(files):
            print(f"[B] {fi}/{len(files)} ({time.time() - t0:.1f}s)", flush=True)

    af = max(1, acc["alive_frames"])
    tk = max(1, acc["takeoff"])
    net = acc["takeoff"] - acc["chained"]
    return {
        "files": len(files),
        "counts": acc,
        "rates_pct_of_alive_frames": {
            "old_jump_label": round(100 * acc["old_jump"] / af, 3),
            "ballistic_takeoff_all": round(100 * acc["takeoff"] / af, 4),
            "ballistic_takeoff_net_excluding_chained": round(100 * net / af, 4),
            "grounded": round(100 * acc["grounded"] / af, 2),
            "rising": round(100 * acc["rising"] / af, 2),
            "falling": round(100 * acc["falling"] / af, 2),
            "landing": round(100 * acc["landing"] / af, 3),
        },
        "old_label_breakdown_pct_of_old_jump": {
            "rising_vz_gt_40": round(100 * acc["old_jump_rising"] / max(1, acc["old_jump"]), 1),
            "falling_vz_lt_-40": round(100 * acc["old_jump_falling"] / max(1, acc["old_jump"]), 1),
            "abs_vz_le_40": round(100 * acc["old_jump_grounded_small_vz"] / max(1, acc["old_jump"]), 1),
        },
        "inflation": {
            "formula_all": "old_jump_frames / ballistic_takeoff_events",
            "value_all": round(acc["old_jump"] / tk, 2),
            "formula_net": "old_jump_frames / (ballistic_takeoff_events - chained_takeoff_events)",
            "value_net": round(acc["old_jump"] / max(1, net), 2),
        },
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "previous_phase1_report_correction": {
            "phase1_values": {"old_jump_frames": 2363125, "onset_frames": 131290, "bhop_pairs": 32788, "alive_frames": 29082040},
            "phase1_18x_formula": "2363125 / 131290 = 18.0 (onsets INCLUINDO pares de bhop)",
            "phase1_0_338_pct_formula": "(131290 - 32788) / 29082040 = 0.3387% (subtraiu PARES de onsets, unidade diferente de eventos)",
            "inconsistency": "8.13 / 0.338 = 24.05x; o relatorio misturou dois denominadores. O 'liquido' (98.502) e invalido porque 32.788 conta pares consecutivos de onsets <= 20 passos, nao episodios nem saltos.",
            "phase1_onset_detector": "NAO usou botao IN_JUMP, NAO usou flag grounded. Usou: rotulo antigo (|vz|>45) + vz>=140 + transicao de borda (passo anterior sem rotulo ou vz<50).",
        },
        "detector_v2_definition_16hz": {
            "takeoff": f"vz[t]>={T16_MIN_VZ} E vz[t-1]<={T16_MAX_PREV_VZ} E vz[t]-vz[t-1]>={T16_MIN_DELTA} E {T16_BALLISTIC_MIN}<=vz[t+1]-vz[t]<={T16_BALLISTIC_MAX} (gravidade ~ -50 u/s por passo) E continuidade espacial <= {DISCONTINUITY_U}u",
            "chained_takeoff_bunnyhop": f"takeoff E vz[t-1] < {CHAINED_PREV_VZ} (nenhuma amostra no chao entre a queda anterior e o novo impulso; contato com o solo < 62.5ms)",
            "states": f"Grounded |vz|<={STATE_EPS}; Rising vz>{STATE_EPS}; Falling vz<-{STATE_EPS}; Landing = Grounded apos Falling",
            "uses_button": False,
            "uses_grounded_flag": False,
            "uses_vertical_velocity": True,
            "uses_edge_transition": True,
            "uses_ballistic_confirmation": True,
        },
        "raw_demos_64hz_validation": audit_raw_demos(),
        "npz_16hz_audit": audit_npz(),
    }
    out = OUT_DIR / "jump_label_audit_v2.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    print(json.dumps({k: report[k] for k in ("raw_demos_64hz_validation",)}["raw_demos_64hz_validation"]["signal_reliability"], indent=1))
    print(json.dumps(report["raw_demos_64hz_validation"]["detector_16hz_vs_64hz"], indent=1))
    print(json.dumps(report["npz_16hz_audit"]["rates_pct_of_alive_frames"], indent=1))
    print(json.dumps(report["npz_16hz_audit"]["inflation"], indent=1))
    print(f"[+] {out}")


if __name__ == "__main__":
    main()
