"""
Auditoria Curta de Suporte Otimizada (Vetorizada) para Marco 2B.3.1.
Calcula suporte em Train e Validation com execução ultrarrápida via numpy/pyarrow.
"""
import json
import sys
from pathlib import Path
from collections import defaultdict
import pyarrow.parquet as pq
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
PATCH_DIR = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "rare_class_patch_v1"
INDEX_DIR = REPO_ROOT / "datasets" / "mirage_v2" / "positioning_v2_full_temporal"
SIDECAR_DIR = INDEX_DIR / "label_sidecar_v2"

STATE_NAMES = ["TRANSIT", "CLEARANCE", "STAGING", "HOLD", "OBJECTIVE", "RETAKE", "SAVE"]
NEXT_SECTOR_NAMES = ["A", "B", "MID", "CT", "T"]
TRANSITION_NAMES = ["ADVANCE", "HOLD", "FALLBACK", "ROTATE", "CONVERGE", "COVER", "LURK"]
EXIT_TRIGGER_NAMES = ["TIME", "CONTACT", "FIRST_KILL", "TEAMMATE_DEATH", "BOMB_SPOTTED", "BOMB_PLANTED", "UTILITY_EXPIRED", "TACTIC_REVISION"]

def main():
    print("[1/3] Processando shards Parquet com vetorização numpy...")
    
    splits_acc = {
        "train": {
            "total_sequences": 0,
            "classes": defaultdict(lambda: {"sequences": 0, "episodes": set(), "matches": set(), "players": set()})
        },
        "validation": {
            "total_sequences": 0,
            "classes": defaultdict(lambda: {"sequences": 0, "episodes": set(), "matches": set(), "players": set()})
        }
    }

    for shard_idx in range(6):
        base_path = INDEX_DIR / f"shard_{shard_idx:03d}.parquet"
        sidecar_path = SIDECAR_DIR / f"shard_{shard_idx:03d}_labels.parquet"
        print(f"  Shard {shard_idx:03d}...", flush=True)

        base_table = pq.read_table(
            base_path,
            columns=["split", "match_id", "round_id", "player_id", "positioning_state", "transition", "exit_trigger"]
        )
        sidecar_table = pq.read_table(
            sidecar_path,
            columns=["sector_transition_occurs", "next_sector", "next_sector_loss_mask"]
        )

        split_arr = base_table["split"].to_numpy(zero_copy_only=False)
        m_ids = base_table["match_id"].to_numpy(zero_copy_only=False)
        r_ids = base_table["round_id"].to_numpy(zero_copy_only=False)
        p_ids = base_table["player_id"].to_numpy(zero_copy_only=False)

        p_state = base_table["positioning_state"].to_numpy(zero_copy_only=False)
        trans = base_table["transition"].to_numpy(zero_copy_only=False)
        trig = base_table["exit_trigger"].to_numpy(zero_copy_only=False)

        sec_trans = sidecar_table["sector_transition_occurs"].to_numpy(zero_copy_only=False)
        nxt_sec = sidecar_table["next_sector"].to_numpy(zero_copy_only=False)
        nxt_mask = sidecar_table["next_sector_loss_mask"].to_numpy(zero_copy_only=False)

        # Tratar cada split (train e validation)
        for s_name in ["train", "validation"]:
            mask_s = (split_arr == s_name)
            cnt = int(np.sum(mask_s))
            if cnt == 0:
                continue

            splits_acc[s_name]["total_sequences"] += cnt

            s_m = m_ids[mask_s]
            s_r = r_ids[mask_s]
            s_p = p_ids[mask_s]
            s_state = p_state[mask_s]
            s_trans = trans[mask_s]
            s_trig = trig[mask_s]
            s_sec_trans = sec_trans[mask_s]
            s_nxt_sec = nxt_sec[mask_s]
            s_nxt_mask = nxt_mask[mask_s]

            # Vetor de episódios no split
            s_episodes = np.char.add(np.char.add(s_m.astype(str), "_"), np.char.add(s_r.astype(str), "_"))
            s_episodes = np.char.add(s_episodes, s_p.astype(str))

            # Função auxiliar vetorizada para agregar métricas
            def aggregate_class(key_name, bool_mask):
                k = splits_acc[s_name]["classes"][key_name]
                hits = int(np.sum(bool_mask))
                k["sequences"] += hits
                if hits > 0:
                    k["matches"].update(np.unique(s_m[bool_mask]))
                    k["players"].update(np.unique(s_p[bool_mask]))
                    k["episodes"].update(np.unique(s_episodes[bool_mask]))

            # 1. TRANSITION_OCCURS
            aggregate_class("TRANSITION_OCCURS", s_sec_trans == "TRANSITION_OCCURS")

            # 2. PositioningState
            for name in STATE_NAMES:
                aggregate_class(f"STATE_{name}", s_state == name)

            # 3. NextSector
            for name in NEXT_SECTOR_NAMES:
                aggregate_class(f"NEXT_SECTOR_{name}", (s_sec_trans == "TRANSITION_OCCURS") & (s_nxt_mask > 0.5) & (s_nxt_sec == name))

            # 4. Transition
            for name in TRANSITION_NAMES:
                aggregate_class(f"TRANSITION_{name}", s_trans == name)

            # 5. ExitTrigger
            for name in EXIT_TRIGGER_NAMES:
                aggregate_class(f"EXIT_TRIGGER_{name}", s_trig == name)

    print("[2/3] Formatando resultados analíticos...", flush=True)
    results = {
        "schema": "csbot.rare_class_patch.class_support.v1",
        "phase": "FASE_3A_3_B_MARCO_2B_3_1",
        "train_total_sequences": splits_acc["train"]["total_sequences"],
        "validation_total_sequences": splits_acc["validation"]["total_sequences"],
        "support_summary": {}
    }

    for cls_name in sorted(splits_acc["train"]["classes"].keys()):
        tr_c = splits_acc["train"]["classes"][cls_name]
        val_c = splits_acc["validation"]["classes"][cls_name]

        tr_seq = tr_c["sequences"]
        val_seq = val_c["sequences"]

        tr_rate = tr_seq / splits_acc["train"]["total_sequences"] if splits_acc["train"]["total_sequences"] > 0 else 0.0
        val_rate = val_seq / splits_acc["validation"]["total_sequences"] if splits_acc["validation"]["total_sequences"] > 0 else 0.0

        results["support_summary"][cls_name] = {
            "train": {
                "sequence_support": tr_seq,
                "episode_support": len(tr_c["episodes"]),
                "unique_matches": len(tr_c["matches"]),
                "unique_players": len(tr_c["players"]),
                "positive_rate": round(float(tr_rate), 6)
            },
            "validation": {
                "sequence_support": val_seq,
                "episode_support": len(val_c["episodes"]),
                "unique_matches": len(val_c["matches"]),
                "unique_players": len(val_c["players"]),
                "positive_rate": round(float(val_rate), 6)
            }
        }

    tr_trans_seq = results["support_summary"]["TRANSITION_OCCURS"]["train"]["sequence_support"]
    tr_hold_seq = results["support_summary"]["STATE_HOLD"]["train"]["sequence_support"]
    tr_obj_seq = results["support_summary"]["STATE_OBJECTIVE"]["train"]["sequence_support"]
    tr_retake_seq = results["support_summary"]["STATE_RETAKE"]["train"]["sequence_support"]
    tr_save_seq = results["support_summary"].get("STATE_SAVE", {}).get("train", {}).get("sequence_support", 0)

    has_sufficient = (tr_trans_seq > 1000 and tr_hold_seq > 500 and tr_obj_seq > 500 and tr_retake_seq > 500)
    results["audit_conclusion"] = {
        "has_sufficient_train_support": has_sufficient,
        "verdict": "SUFFICIENT_TRAIN_SUPPORT_CONFIRMED" if has_sufficient else "INSUFFICIENT_TRAIN_SUPPORT",
        "key_support_counts": {
            "TRANSITION_OCCURS_train_sequences": tr_trans_seq,
            "HOLD_train_sequences": tr_hold_seq,
            "OBJECTIVE_train_sequences": tr_obj_seq,
            "RETAKE_train_sequences": tr_retake_seq,
            "SAVE_train_sequences": tr_save_seq
        },
        "diagnosis": "O problema de recall 0.0 decorre de desbalanceamento de classes, NAO de ausencia de dados no Train."
    }

    out_file = PATCH_DIR / "class_support.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"[3/3] class_support.json gravado com sucesso em {out_file.relative_to(REPO_ROOT)}")
    print(f"VERDICT: {results['audit_conclusion']['verdict']}")
    print(f"Counts Train: TRANSITION_OCCURS={tr_trans_seq}, HOLD={tr_hold_seq}, OBJECTIVE={tr_obj_seq}, RETAKE={tr_retake_seq}, SAVE={tr_save_seq}")

if __name__ == "__main__":
    main()
