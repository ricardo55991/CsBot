#!/usr/bin/env python3
"""
Marco 2B.5 - Seção 3: Wrapper ONNX Único `PositioningTransformerHybridRuntimeV1`.

Versão 100% branchless (sem control flow dependente de dados) para exportação ONNX
determinística em opset 18 com paridade exata contra PyTorch.
"""
from typing import Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F

from tools.phase3a_training.positioning_model_v2 import PositioningTransformerV2RealTemporal
from tools.phase3a_training.hierarchical_positioning_model import HierarchicalPositioningModel


def _encode_branchless_contextual(
    bm: PositioningTransformerV2RealTemporal,
    self_history: torch.Tensor,
    teammates: torch.Tensor,
    temporal_mask: torch.Tensor,
    teammate_mask: torch.Tensor,
    team_idx: torch.Tensor,
    role_idx: torch.Tensor,
    stage_idx: torch.Tensor,
) -> torch.Tensor:
    batch_size, seq_len, _ = self_history.shape
    device = self_history.device
    t_mask = temporal_mask.float()

    h_player = bm.player_proj(self_history) * t_mask.unsqueeze(-1)
    h_tm = bm.teammate_proj(teammates)
    tm_mask = teammate_mask.float().unsqueeze(-1)
    h_tm = h_tm * tm_mask
    tm_denom = tm_mask.sum(dim=2).clamp(min=1.0)
    h_tm_pooled = h_tm.sum(dim=2) / tm_denom
    h_tm_feat = F.gelu(bm.teammate_pool(h_tm_pooled)) * t_mask.unsqueeze(-1)
    x_seq = h_player + 0.3 * h_tm_feat

    emb_t = bm.team_emb(team_idx).unsqueeze(1).expand(-1, seq_len, -1)
    emb_r = bm.role_emb(role_idx).unsqueeze(1).expand(-1, seq_len, -1)
    emb_s = bm.stage_emb(stage_idx).unsqueeze(1).expand(-1, seq_len, -1)

    x_emb = bm.context_fusion(torch.cat([x_seq, emb_t, emb_r, emb_s], dim=-1))
    x_pos = bm.pos_encoder(x_emb)

    # Branchless key_padding_mask: se toda a linha estiver True, desmarca apenas posição 0
    key_padding_mask = t_mask < 0.5
    all_padded = key_padding_mask.all(dim=-1, keepdim=True)
    first_col_mask = torch.cat(
        [all_padded, torch.zeros((batch_size, seq_len - 1), dtype=torch.bool, device=device)],
        dim=1,
    )
    key_padding_mask = key_padding_mask & (~first_col_mask)

    encoded = bm.transformer(x_pos, src_key_padding_mask=key_padding_mask)
    encoded = bm.norm(encoded)

    last_step = encoded[:, -1, :]
    mask_weights = t_mask.unsqueeze(-1)
    denom = mask_weights.sum(dim=1).clamp(min=1.0)
    mean_step = (encoded * mask_weights).sum(dim=1) / denom
    return (last_step + mean_step) * 0.5


def _encode_branchless(
    bm: PositioningTransformerV2RealTemporal,
    self_history: torch.Tensor,
    teammates: torch.Tensor,
    temporal_mask: torch.Tensor,
    teammate_mask: torch.Tensor,
) -> torch.Tensor:
    batch_size = self_history.shape[0]
    device = self_history.device
    zeros_idx = torch.zeros(batch_size, dtype=torch.long, device=device)
    return _encode_branchless_contextual(
        bm, self_history, teammates, temporal_mask, teammate_mask, zeros_idx, zeros_idx, zeros_idx
    )


class PositioningTransformerHybridRuntimeV1(nn.Module):
    def __init__(
        self,
        model_2b34: PositioningTransformerV2RealTemporal,
        model_2b36: HierarchicalPositioningModel,
        sector_transition_threshold: float = 0.525,
    ):
        super().__init__()
        self.model_2b34 = model_2b34
        self.model_2b36 = model_2b36
        self.sector_transition_threshold = float(sector_transition_threshold)
        self.eval()
        for p in self.parameters():
            p.requires_grad = False

    def forward(
        self,
        self_history: torch.Tensor,       # [B, 32, 18] float32
        teammates: torch.Tensor,          # [B, 32, 4, 18] float32
        temporal_mask: torch.Tensor,      # [B, 32] float32
        teammate_mask: torch.Tensor,      # [B, 32, 4] float32
        candidate_mask: torch.Tensor,     # [B, 53] bool
        objective_eligible: torch.Tensor, # [B] bool
        retake_eligible: torch.Tensor,    # [B] bool
    ) -> Tuple[
        torch.Tensor, torch.Tensor,
        torch.Tensor, torch.Tensor,
        torch.Tensor, torch.Tensor,
        torch.Tensor, torch.Tensor,
        torch.Tensor, torch.Tensor,
        torch.Tensor, torch.Tensor,
        torch.Tensor,
    ]:
        batch_size = self_history.shape[0]
        device = self_history.device

        # 1. Pooled do modelo aprovado 2B.3.4
        pooled_34 = _encode_branchless(self.model_2b34, self_history, teammates, temporal_mask, teammate_mask)
        logits_state_34 = self.model_2b34.head_state(pooled_34)
        sector_transition_logits = self.model_2b34.head_transition_occurs(pooled_34)
        next_sector_logits = self.model_2b34.head_next_sector(pooled_34)
        raw_spot_logits = self.model_2b34.head_spot(pooled_34)
        transition_logits = self.model_2b34.head_transition(pooled_34)
        exit_trigger_logits = self.model_2b34.head_exit_trigger(pooled_34)

        spot_elig = self.model_2b34.supervised_spot_mask.bool().unsqueeze(0).expand(batch_size, -1)
        full_spot_mask = candidate_mask.bool() & spot_elig
        spot_logits = torch.where(full_spot_mask, raw_spot_logits, torch.full_like(raw_spot_logits, -1e9))

        # 2. Pooled do modelo hierárquico 2B.3.6 (RareTacticalStateHead)
        pooled_36 = _encode_branchless(self.model_2b36.base_model, self_history, teammates, temporal_mask, teammate_mask)
        raw_rare_logits = self.model_2b36.head_rare_state(pooled_36)

        allow_none = torch.ones((batch_size, 1), dtype=torch.bool, device=device)
        false_save = torch.zeros((batch_size, 1), dtype=torch.bool, device=device)
        rare_allow = torch.cat(
            [allow_none, objective_eligible.bool().unsqueeze(1), retake_eligible.bool().unsqueeze(1), false_save],
            dim=1,
        )
        masked_rare_logits = torch.where(rare_allow, raw_rare_logits, torch.full_like(raw_rare_logits, -1e9))

        # 3. Composição causal sem SAVE
        base_logits = logits_state_34[:, :4]
        base_pred = torch.argmax(base_logits, dim=-1)
        rare_pred = torch.argmax(masked_rare_logits, dim=-1)

        is_obj = (rare_pred == 1) & objective_eligible.bool()
        is_ret = (rare_pred == 2) & retake_eligible.bool() & (~is_obj)

        final_state_id = torch.where(
            is_obj,
            torch.full_like(base_pred, 4),
            torch.where(is_ret, torch.full_like(base_pred, 5), base_pred),
        )

        neg_inf = torch.full((batch_size, 1), -1e4, dtype=base_logits.dtype, device=device)
        max_base = torch.max(base_logits, dim=-1, keepdim=True).values
        obj_logit = torch.where(is_obj.unsqueeze(-1), max_base + 10.0, neg_inf)
        ret_logit = torch.where(is_ret.unsqueeze(-1), max_base + 10.0, neg_inf)
        final_state_logits = torch.cat([base_logits, obj_logit, ret_logit], dim=-1)

        # 4. Decisões das demais heads
        prob_st = F.softmax(sector_transition_logits, dim=-1)[:, 1]
        sector_transition_id = (prob_st >= self.sector_transition_threshold).to(torch.long)
        next_sector_id = torch.argmax(next_sector_logits, dim=-1)
        selected_spot_id = torch.argmax(spot_logits, dim=-1)
        transition_id = torch.argmax(transition_logits, dim=-1)
        exit_trigger_id = torch.argmax(exit_trigger_logits, dim=-1)

        # 5. Confiança por head [B, 6]
        c_state = torch.max(F.softmax(final_state_logits, dim=-1), dim=-1).values
        c_st = torch.max(F.softmax(sector_transition_logits, dim=-1), dim=-1).values
        c_ns = torch.max(F.softmax(next_sector_logits, dim=-1), dim=-1).values
        c_sp = torch.max(F.softmax(spot_logits, dim=-1), dim=-1).values
        c_tr = torch.max(F.softmax(transition_logits, dim=-1), dim=-1).values
        c_ex = torch.max(F.softmax(exit_trigger_logits, dim=-1), dim=-1).values
        confidence_by_head = torch.stack([c_state, c_st, c_ns, c_sp, c_tr, c_ex], dim=-1)

        return (
            final_state_logits,
            final_state_id,
            sector_transition_logits,
            sector_transition_id,
            next_sector_logits,
            next_sector_id,
            spot_logits,
            selected_spot_id,
            transition_logits,
            transition_id,
            exit_trigger_logits,
            exit_trigger_id,
            confidence_by_head,
        )


class PositioningTransformerHybridRuntimeV2(nn.Module):
    """
    Marco 2B.5.1: Wrapper ONNX V2 com inputs contextuais explícitos
    (team_idx, role_idx, stage_idx) preservando integralmente todos os
    inputs e outputs do V1.
    """

    def __init__(
        self,
        model_2b34: PositioningTransformerV2RealTemporal,
        model_2b36: HierarchicalPositioningModel,
        sector_transition_threshold: float = 0.525,
    ):
        super().__init__()
        self.model_2b34 = model_2b34
        self.model_2b36 = model_2b36
        self.sector_transition_threshold = float(sector_transition_threshold)
        self.eval()
        for p in self.parameters():
            p.requires_grad = False

    def forward(
        self,
        self_history: torch.Tensor,       # [B, 32, 18] float32
        teammates: torch.Tensor,          # [B, 32, 4, 18] float32
        temporal_mask: torch.Tensor,      # [B, 32] float32
        teammate_mask: torch.Tensor,      # [B, 32, 4] float32
        candidate_mask: torch.Tensor,     # [B, 53] bool
        objective_eligible: torch.Tensor, # [B] bool
        retake_eligible: torch.Tensor,    # [B] bool
        team_idx: torch.Tensor,           # [B] int64
        role_idx: torch.Tensor,           # [B] int64
        stage_idx: torch.Tensor,          # [B] int64
    ) -> Tuple[
        torch.Tensor, torch.Tensor,
        torch.Tensor, torch.Tensor,
        torch.Tensor, torch.Tensor,
        torch.Tensor, torch.Tensor,
        torch.Tensor, torch.Tensor,
        torch.Tensor, torch.Tensor,
        torch.Tensor,
    ]:
        batch_size = self_history.shape[0]
        device = self_history.device

        # 1. Pooled do modelo aprovado 2B.3.4 com contexto completo
        pooled_34 = _encode_branchless_contextual(
            self.model_2b34, self_history, teammates, temporal_mask, teammate_mask,
            team_idx, role_idx, stage_idx,
        )
        logits_state_34 = self.model_2b34.head_state(pooled_34)
        sector_transition_logits = self.model_2b34.head_transition_occurs(pooled_34)
        next_sector_logits = self.model_2b34.head_next_sector(pooled_34)
        raw_spot_logits = self.model_2b34.head_spot(pooled_34)
        transition_logits = self.model_2b34.head_transition(pooled_34)
        exit_trigger_logits = self.model_2b34.head_exit_trigger(pooled_34)

        spot_elig = self.model_2b34.supervised_spot_mask.bool().unsqueeze(0).expand(batch_size, -1)
        full_spot_mask = candidate_mask.bool() & spot_elig
        spot_logits = torch.where(full_spot_mask, raw_spot_logits, torch.full_like(raw_spot_logits, -1e9))

        # 2. Pooled do modelo hierárquico 2B.3.6 com contexto completo
        pooled_36 = _encode_branchless_contextual(
            self.model_2b36.base_model, self_history, teammates, temporal_mask, teammate_mask,
            team_idx, role_idx, stage_idx,
        )
        raw_rare_logits = self.model_2b36.head_rare_state(pooled_36)

        allow_none = torch.ones((batch_size, 1), dtype=torch.bool, device=device)
        false_save = torch.zeros((batch_size, 1), dtype=torch.bool, device=device)
        rare_allow = torch.cat(
            [allow_none, objective_eligible.bool().unsqueeze(1), retake_eligible.bool().unsqueeze(1), false_save],
            dim=1,
        )
        masked_rare_logits = torch.where(rare_allow, raw_rare_logits, torch.full_like(raw_rare_logits, -1e9))

        # 3. Composição causal sem SAVE
        base_logits = logits_state_34[:, :4]
        base_pred = torch.argmax(base_logits, dim=-1)
        rare_pred = torch.argmax(masked_rare_logits, dim=-1)

        is_obj = (rare_pred == 1) & objective_eligible.bool()
        is_ret = (rare_pred == 2) & retake_eligible.bool() & (~is_obj)

        final_state_id = torch.where(
            is_obj,
            torch.full_like(base_pred, 4),
            torch.where(is_ret, torch.full_like(base_pred, 5), base_pred),
        )

        neg_inf = torch.full((batch_size, 1), -1e4, dtype=base_logits.dtype, device=device)
        max_base = torch.max(base_logits, dim=-1, keepdim=True).values
        obj_logit = torch.where(is_obj.unsqueeze(-1), max_base + 10.0, neg_inf)
        ret_logit = torch.where(is_ret.unsqueeze(-1), max_base + 10.0, neg_inf)
        final_state_logits = torch.cat([base_logits, obj_logit, ret_logit], dim=-1)

        # 4. Decisões das demais heads
        prob_st = F.softmax(sector_transition_logits, dim=-1)[:, 1]
        sector_transition_id = (prob_st >= self.sector_transition_threshold).to(torch.long)
        next_sector_id = torch.argmax(next_sector_logits, dim=-1)
        selected_spot_id = torch.argmax(spot_logits, dim=-1)
        transition_id = torch.argmax(transition_logits, dim=-1)
        exit_trigger_id = torch.argmax(exit_trigger_logits, dim=-1)

        # 5. Confiança por head [B, 6]
        c_state = torch.max(F.softmax(final_state_logits, dim=-1), dim=-1).values
        c_st = torch.max(F.softmax(sector_transition_logits, dim=-1), dim=-1).values
        c_ns = torch.max(F.softmax(next_sector_logits, dim=-1), dim=-1).values
        c_sp = torch.max(F.softmax(spot_logits, dim=-1), dim=-1).values
        c_tr = torch.max(F.softmax(transition_logits, dim=-1), dim=-1).values
        c_ex = torch.max(F.softmax(exit_trigger_logits, dim=-1), dim=-1).values
        confidence_by_head = torch.stack([c_state, c_st, c_ns, c_sp, c_tr, c_ex], dim=-1)

        return (
            final_state_logits,
            final_state_id,
            sector_transition_logits,
            sector_transition_id,
            next_sector_logits,
            next_sector_id,
            spot_logits,
            selected_spot_id,
            transition_logits,
            transition_id,
            exit_trigger_logits,
            exit_trigger_id,
            confidence_by_head,
        )
