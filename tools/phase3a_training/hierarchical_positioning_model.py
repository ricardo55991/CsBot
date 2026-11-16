#!/usr/bin/env python3
"""
Marco 2B.3.6: Arquitetura Hierárquica para PositioningState.

Preserva integralmente `PositioningTransformerV2RealTemporal` (incluindo `head_state`
como baseline e fallback) e adiciona:
- Head A (`head_base_state`): 4 classes [TRANSIT, CLEARANCE, STAGING, HOLD]
- Head B (`head_rare_state`): 4 classes [NONE, OBJECTIVE, RETAKE, SAVE]

Composição determinística:
    se RareTacticalState != NONE (e elegível contextualmente):
        usar estado raro (OBJECTIVE=4, RETAKE=5, SAVE=6)
    senão:
        usar BasePositioningState (TRANSIT=0, CLEARANCE=1, STAGING=2, HOLD=3)
"""
from typing import Dict, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F

from tools.phase3a_training.positioning_model_v2 import (
    PositioningTransformerV2RealTemporal,
    STATE_NAMES,
)

BASE_STATE_NAMES = ["TRANSIT", "CLEARANCE", "STAGING", "HOLD"]
BASE_STATE_MAP = {name: i for i, name in enumerate(BASE_STATE_NAMES)}

RARE_STATE_NAMES = ["NONE", "OBJECTIVE", "RETAKE", "SAVE"]
RARE_STATE_MAP = {name: i for i, name in enumerate(RARE_STATE_NAMES)}


class HierarchicalPositioningModel(nn.Module):
    def __init__(self, base_model: PositioningTransformerV2RealTemporal, dropout: float = 0.10):
        super().__init__()
        self.base_model = base_model
        h = base_model.hidden_dim

        # Head A: BasePositioningState (4 classes)
        self.head_base_state = nn.Sequential(
            nn.Linear(h, h // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(h // 2, 4),
        )
        # Head B: RareTacticalState (4 classes: NONE, OBJECTIVE, RETAKE, SAVE)
        self.head_rare_state = nn.Sequential(
            nn.Linear(h, h // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(h // 2, 4),
        )
        self._init_base_head_from_flat_head()

    def _init_base_head_from_flat_head(self) -> None:
        """Inicializa Head A a partir das 4 primeiras classes de `base_model.head_state` sem alterá-la."""
        with torch.no_grad():
            src0: nn.Linear = self.base_model.head_state[0]
            dst0: nn.Linear = self.head_base_state[0]
            dst0.weight.copy_(src0.weight)
            dst0.bias.copy_(src0.bias)

            src3: nn.Linear = self.base_model.head_state[3]
            dst3: nn.Linear = self.head_base_state[3]
            dst3.weight.copy_(src3.weight[:4])
            dst3.bias.copy_(src3.bias[:4])

    def freeze_approved_modules(self) -> None:
        """
        Congela bitwise todos os módulos aprovados (Seção 5):
        - input projection (player_proj, teammate_proj, teammate_pool, team_emb, role_emb, stage_emb, context_fusion, pos_encoder)
        - temporal blocks 0 e 1
        - todas as heads originais (incluindo head_state como fallback e head_spot)
        Mantém treináveis apenas:
        - transformer.layers[2] e norm
        - head_base_state e head_rare_state
        """
        for p in self.base_model.parameters():
            p.requires_grad = False

        for p in self.base_model.transformer.layers[2].parameters():
            p.requires_grad = True
        for p in self.base_model.norm.parameters():
            p.requires_grad = True

        for p in self.head_base_state.parameters():
            p.requires_grad = True
        for p in self.head_rare_state.parameters():
            p.requires_grad = True

    def encode_pooled(
        self,
        self_history: torch.Tensor,
        teammates: torch.Tensor,
        temporal_mask: Optional[torch.Tensor] = None,
        teammate_mask: Optional[torch.Tensor] = None,
        team_idx: Optional[torch.Tensor] = None,
        role_idx: Optional[torch.Tensor] = None,
        stage_idx: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        bm = self.base_model
        batch_size, seq_len, _ = self_history.shape
        if temporal_mask is None:
            temporal_mask = torch.ones(batch_size, seq_len, dtype=torch.float32, device=self_history.device)
        else:
            temporal_mask = temporal_mask.float()

        h_player = bm.player_proj(self_history) * temporal_mask.unsqueeze(-1)
        h_tm = bm.teammate_proj(teammates)
        if teammate_mask is not None:
            tm_mask = teammate_mask.float().unsqueeze(-1)
            h_tm = h_tm * tm_mask
            tm_denom = tm_mask.sum(dim=2).clamp(min=1.0)
            h_tm_pooled = h_tm.sum(dim=2) / tm_denom
        else:
            h_tm_pooled = torch.mean(h_tm, dim=2)
        h_tm_feat = F.gelu(bm.teammate_pool(h_tm_pooled)) * temporal_mask.unsqueeze(-1)
        x_seq = h_player + 0.3 * h_tm_feat

        if team_idx is None:
            team_idx = torch.zeros(batch_size, dtype=torch.long, device=self_history.device)
        if role_idx is None:
            role_idx = torch.zeros(batch_size, dtype=torch.long, device=self_history.device)
        if stage_idx is None:
            stage_idx = torch.zeros(batch_size, dtype=torch.long, device=self_history.device)

        emb_t = bm.team_emb(team_idx).unsqueeze(1).expand(-1, seq_len, -1)
        emb_r = bm.role_emb(role_idx).unsqueeze(1).expand(-1, seq_len, -1)
        emb_s = bm.stage_emb(stage_idx).unsqueeze(1).expand(-1, seq_len, -1)
        x_emb = bm.context_fusion(torch.cat([x_seq, emb_t, emb_r, emb_s], dim=-1))
        x_pos = bm.pos_encoder(x_emb)

        key_padding_mask = temporal_mask < 0.5
        all_padded = key_padding_mask.all(dim=-1)
        if all_padded.any():
            key_padding_mask = key_padding_mask.clone()
            key_padding_mask[all_padded, 0] = False

        encoded = bm.transformer(x_pos, src_key_padding_mask=key_padding_mask)
        encoded = bm.norm(encoded)

        last_step = encoded[:, -1, :]
        mask_weights = temporal_mask.unsqueeze(-1)
        denom = mask_weights.sum(dim=1).clamp(min=1.0)
        mean_step = (encoded * mask_weights).sum(dim=1) / denom
        return (last_step + mean_step) * 0.5

    def forward(
        self,
        self_history: torch.Tensor,
        teammates: torch.Tensor,
        temporal_mask: Optional[torch.Tensor] = None,
        teammate_mask: Optional[torch.Tensor] = None,
        candidate_mask: Optional[torch.Tensor] = None,
        team_idx: Optional[torch.Tensor] = None,
        role_idx: Optional[torch.Tensor] = None,
        stage_idx: Optional[torch.Tensor] = None,
        rare_eligibility_mask: Optional[torch.Tensor] = None,  # [B, 3] bool (obj, ret, sav)
    ) -> Dict[str, torch.Tensor]:
        bm = self.base_model
        batch_size = self_history.shape[0]
        pooled = self.encode_pooled(
            self_history, teammates, temporal_mask, teammate_mask, team_idx, role_idx, stage_idx
        )

        # Heads preservadas
        logits_state = bm.head_state(pooled)
        logits_transition_occurs = bm.head_transition_occurs(pooled)
        logits_next_sector = bm.head_next_sector(pooled)
        logits_spot = bm.head_spot(pooled)
        logits_transition = bm.head_transition(pooled)
        logits_trigger = bm.head_exit_trigger(pooled)

        neg_inf = -1e9
        spot_eligibility = bm.supervised_spot_mask.bool().unsqueeze(0).expand(batch_size, -1)
        full_mask = (candidate_mask.bool() & spot_eligibility) if candidate_mask is not None else spot_eligibility
        masked_logits_spot = torch.where(full_mask, logits_spot, torch.full_like(logits_spot, neg_inf))

        # Novas heads hierárquicas
        logits_base_state = self.head_base_state(pooled)
        raw_logits_rare_state = self.head_rare_state(pooled)

        if rare_eligibility_mask is not None:
            # Classe 0 (NONE) sempre permitida; classes 1,2,3 (OBJ, RET, SAV) restritas à elegibilidade
            allow_none = torch.ones((batch_size, 1), dtype=torch.bool, device=raw_logits_rare_state.device)
            rare_allow = torch.cat([allow_none, rare_eligibility_mask.bool()], dim=1)
            logits_rare_state = torch.where(
                rare_allow, raw_logits_rare_state, torch.full_like(raw_logits_rare_state, neg_inf)
            )
        else:
            logits_rare_state = raw_logits_rare_state

        return {
            "logits_state": logits_state,
            "logits_base_state": logits_base_state,
            "logits_rare_state": logits_rare_state,
            "raw_logits_rare_state": raw_logits_rare_state,
            "logits_transition_occurs": logits_transition_occurs,
            "logits_next_sector": logits_next_sector,
            "logits_spot": masked_logits_spot,
            "raw_logits_spot": logits_spot,
            "logits_transition": logits_transition,
            "logits_trigger": logits_trigger,
        }


def compose_composite_predictions(
    logits_base_state: torch.Tensor,
    logits_rare_state: torch.Tensor,
    rare_eligibility_mask: Optional[torch.Tensor] = None,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Retorna (composite_pred [B] em 0..6, base_pred [B] em 0..3, rare_pred [B] em 0..3).
    """
    base_pred = torch.argmax(logits_base_state, dim=-1)  # 0..3
    if rare_eligibility_mask is not None:
        allow_none = torch.ones((logits_rare_state.shape[0], 1), dtype=torch.bool, device=logits_rare_state.device)
        rare_allow = torch.cat([allow_none, rare_eligibility_mask.bool()], dim=1)
        masked_rare = torch.where(rare_allow, logits_rare_state, torch.full_like(logits_rare_state, -1e9))
        rare_pred = torch.argmax(masked_rare, dim=-1)
    else:
        rare_pred = torch.argmax(logits_rare_state, dim=-1)

    # Se rare_pred != 0 (NONE), usar 3 + rare_pred (1->4 OBJECTIVE, 2->5 RETAKE, 3->6 SAVE)
    composite_pred = torch.where(rare_pred > 0, rare_pred + 3, base_pred)
    return composite_pred, base_pred, rare_pred
