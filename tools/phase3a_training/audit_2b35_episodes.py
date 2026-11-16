"""Auditoria Episodica do Marco 2B.3.5.

Agrupa sequencias por episodio real:
    (demo_id, round_id, player_id, positioning_state, contiguous_tick_range)

onde contiguous_tick_range separa blocos quando o salto entre label_frame
consecutivos (ordenados) excede CONTIGUOUS_GAP_MAX (32 frames = 1 janela).

Calcula para OBJECTIVE, RETAKE e SAVE (e tambem resume todas as classes):
    - sequence support
    - episode support
    - unique demos
    - unique matches
    - unique players
    - median windows per episode
    - maximum windows per episode
    - provenance distribution
    - subtype distribution

Verifica suporte minimo em Train:
    OBJECTIVE >= 50 episodios
    RETAKE >= 50 episodios
    SAVE >= 30 episodios

Saida: rare_episode_patch_v1/episode_support.json
"""
import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
INDEX_DIR = REPO / "datasets/mirage_v2/positioning_v2_full_temporal"
OUT_DIR = REPO / "training_runs/positioning_v2_real_temporal/rare_class_patch_v1/rare_episode_patch_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CONTIGUOUS_GAP_MAX = 32  # 1 janela (window_end - window_start + 1 = 32 frames)
MIN_EPISODES = {"OBJECTIVE": 50, "RETAKE": 50, "SAVE": 30}
TARGET_CLASSES = ["OBJECTIVE", "RETAKE", "SAVE"]


def assign_contiguous_episodes(df: pd.DataFrame) -> pd.Series:
    """Atribui um episode_uid unico por (demo_id, round_id, player_id, positioning_state, segmento contiguo)."""
    ordered = df.sort_values(
        ["demo_id", "round_id", "player_id", "positioning_state", "label_frame"],
        kind="mergesort",
    )
    same_key = (
        (ordered["demo_id"] == ordered["demo_id"].shift(1))
        & (ordered["round_id"] == ordered["round_id"].shift(1))
        & (ordered["player_id"] == ordered["player_id"].shift(1))
        & (ordered["positioning_state"] == ordered["positioning_state"].shift(1))
    )
    gap = ordered["label_frame"] - ordered["label_frame"].shift(1)
    new_ep = (~same_key) | (gap > CONTIGUOUS_GAP_MAX)
    ep_num = new_ep.cumsum()
    # Devolve alinhado ao indice original
    return ep_num.reindex(df.index)


def summarize_class(df_cls: pd.DataFrame) -> Dict[str, Any]:
    if len(df_cls) == 0:
        return {
            "sequence_support": 0,
            "episode_support": 0,
            "unique_demos": 0,
            "unique_matches": 0,
            "unique_players": 0,
            "median_windows_per_episode": 0.0,
            "maximum_windows_per_episode": 0,
            "provenance_distribution": {},
            "subtype_distribution": {},
        }
    ep_sizes = df_cls.groupby("episode_uid").size().to_numpy()
    prov = df_cls["provenance_type"].fillna("UNKNOWN").value_counts().to_dict()
    prov = {str(k): int(v) for k, v in prov.items()}

    # Subtype combinando objective_subtype / save_subtype conforme a classe
    cls_name = str(df_cls["positioning_state"].iloc[0])
    if cls_name == "OBJECTIVE":
        sub_series = df_cls["objective_subtype"].fillna("NONE")
    elif cls_name == "SAVE":
        sub_series = df_cls["save_subtype"].fillna("NONE")
    else:
        sub_series = df_cls["semantic_type"].fillna("NONE")
    sub_dist = {str(k): int(v) for k, v in sub_series.value_counts().to_dict().items()}

    return {
        "sequence_support": int(len(df_cls)),
        "episode_support": int(len(ep_sizes)),
        "unique_demos": int(df_cls["demo_id"].nunique()),
        "unique_matches": int(df_cls["match_id"].nunique()),
        "unique_players": int(df_cls["player_id"].nunique()),
        "median_windows_per_episode": float(np.median(ep_sizes)),
        "maximum_windows_per_episode": int(np.max(ep_sizes)),
        "provenance_distribution": prov,
        "subtype_distribution": sub_dist,
    }


def main() -> int:
    cols = [
        "sequence_id", "demo_id", "match_id", "round_id", "player_id",
        "split", "window_start_frame", "label_frame", "positioning_state",
        "objective_subtype", "save_subtype", "semantic_type", "provenance_type",
    ]
    shards = sorted(INDEX_DIR.glob("shard_*.parquet"))
    parts: List[pd.DataFrame] = []
    for sh in shards:
        df_s = pd.read_parquet(sh, columns=cols)
        # Estritamente apenas train e validation (nunca ler test / final_holdout)
        df_s = df_s[df_s["split"].isin(["train", "validation"])].copy()
        parts.append(df_s)
    full = pd.concat(parts, ignore_index=True)

    report: Dict[str, Any] = {
        "schema": "csbot.rare_episode_patch.episode_support.v1",
        "grouping_keys": ["demo_id", "round_id", "player_id", "positioning_state", "contiguous_tick_range"],
        "contiguous_gap_max_frames": CONTIGUOUS_GAP_MAX,
        "min_required_train_episodes": MIN_EPISODES,
        "splits": {},
    }

    for split_name in ("train", "validation"):
        sub = full[full["split"] == split_name].copy()
        sub["episode_uid"] = assign_contiguous_episodes(sub)
        cls_out = {}
        for cls_name in TARGET_CLASSES:
            cls_out[cls_name] = summarize_class(sub[sub["positioning_state"] == cls_name])
        all_counts = (
            sub.groupby("positioning_state")
            .agg(sequence_support=("sequence_id", "count"), episode_support=("episode_uid", "nunique"))
            .to_dict(orient="index")
        )
        report["splits"][split_name] = {
            "total_sequences": int(len(sub)),
            "total_episodes": int(sub["episode_uid"].nunique()),
            "target_rare_classes": cls_out,
            "all_states_summary": {
                str(k): {"sequence_support": int(v["sequence_support"]), "episode_support": int(v["episode_support"])}
                for k, v in all_counts.items()
            },
        }

    train_rare = report["splits"]["train"]["target_rare_classes"]
    insufficient = [
        cls for cls, req in MIN_EPISODES.items()
        if train_rare[cls]["episode_support"] < req
    ]
    report["train_minimum_support_satisfied"] = len(insufficient) == 0
    report["insufficient_classes"] = insufficient
    report["status"] = (
        "SUFFICIENT_EPISODE_SUPPORT" if not insufficient else "INSUFFICIENT_EPISODE_SUPPORT"
    )

    out_path = OUT_DIR / "episode_support.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Status suporte episodico (Train): {report['status']}")
    for cls in TARGET_CLASSES:
        m = train_rare[cls]
        print(
            f"  [TRAIN] {cls:<10} seqs={m['sequence_support']:>5}  eps={m['episode_support']:>4} "
            f"(min={MIN_EPISODES[cls]})  demos={m['unique_demos']:>3}  matches={m['unique_matches']:>3} "
            f"players={m['unique_players']:>4}  med_win={m['median_windows_per_episode']:.1f} "
            f"max_win={m['maximum_windows_per_episode']}"
        )
        print(f"    prov={m['provenance_distribution']}  subtypes={m['subtype_distribution']}")
    print(f"Salvo em: {out_path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
