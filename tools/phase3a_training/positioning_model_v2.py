#!/usr/bin/env python3
"""
Fase 3A.3-B - Marco 2B.3: Arquitetura Neural do Positioning Transformer V2 Real Temporal.

Contrato do Modelo (Seção 3):
- hidden_dim = 192
- transformer_layers = 3
- attention_heads = 6
- feedforward_dim = 768
- dropout = 0.10
- sequence_length = 32
- num_spots = 53

Inputs:
- self_history: [batch, 32, 18]
- teammates: [batch, 32, 4, 18]
- temporal_mask: [batch, 32]
- teammate_mask: [batch, 32, 4]
- candidate_mask: [batch, 53]
- context: team_idx, role_idx, stage_idx

Heads:
- Head A: PositioningState (7 classes: TRANSIT, CLEARANCE, STAGING, HOLD, OBJECTIVE, RETAKE, SAVE)
- Head B: SectorTransitionOccurs (2 classes: NO_TRANSITION, TRANSITION_OCCURS)
- Head C: NextSector (5 classes: A, B, MID, CT, T)
- Head D: CandidateSpotRanking (53 logits com supervised_spot_mask)
- Head E: Transition (7 classes: ADVANCE, HOLD, FALLBACK, ROTATE, CONVERGE, COVER, LURK)
- Head F: ExitTrigger (8 classes: TIME, CONTACT, FIRST_KILL, TEAMMATE_DEATH, BOMB_SPOTTED, BOMB_PLANTED, UTILITY_EXPIRED, TACTIC_REVISION)

Proteções de Loss (Seção 5):
- NextSectorLoss = 0 quando NO_TRANSITION
- NextSectorLoss > 0 somente em TRANSITION_OCCURS elegível
- SpotLoss = 0 em TRANSIT
- SpotLoss = 0 em UNMAPPED
- SpotLoss = 0 para spot sem suporte (supervised_spot_mask == 0)
- SpotLoss > 0 somente para target supervisionado e presente na mask
- Spots com supervised_spot_mask = 0 nunca vencem seleção neural (logits mascarados com -1e9)
"""

import math
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import torch
import torch.nn as nn
import torch.nn.functional as F

STATE_NAMES = ["TRANSIT", "CLEARANCE", "STAGING", "HOLD", "OBJECTIVE", "RETAKE", "SAVE"]
STATE_MAP = {name: i for i, name in enumerate(STATE_NAMES)}

SECTOR_TRANSITION_NAMES = ["NO_TRANSITION", "TRANSITION_OCCURS"]
SECTOR_TRANSITION_MAP = {name: i for i, name in enumerate(SECTOR_TRANSITION_NAMES)}

NEXT_SECTOR_NAMES = ["A", "B", "MID", "CT", "T"]
NEXT_SECTOR_MAP = {name: i for i, name in enumerate(NEXT_SECTOR_NAMES)}

TRANSITION_NAMES = ["ADVANCE", "HOLD", "FALLBACK", "ROTATE", "CONVERGE", "COVER", "LURK"]
TRANSITION_MAP = {name: i for i, name in enumerate(TRANSITION_NAMES)}

EXIT_TRIGGER_NAMES = ["TIME", "CONTACT", "FIRST_KILL", "TEAMMATE_DEATH", "BOMB_SPOTTED", "BOMB_PLANTED", "UTILITY_EXPIRED", "TACTIC_REVISION"]
EXIT_TRIGGER_MAP = {name: i for i, name in enumerate(EXIT_TRIGGER_NAMES)}


class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 128, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [batch, seq_len, d_model]
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)


class PositioningTransformerV2RealTemporal(nn.Module):
    def __init__(
        self,
        input_dim: int = 18,
        hidden_dim: int = 192,
        num_layers: int = 3,
        num_heads: int = 6,
        feedforward_dim: int = 768,
        dropout: float = 0.10,
        seq_len: int = 32,
        num_spots: int = 53,
        supervised_spot_mask: Optional[torch.Tensor] = None
    ):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.seq_len = seq_len
        self.num_spots = num_spots

        # Supervised spot mask [53]: 1 = supervisionado ativo, 0 = sem suporte empírico
        if supervised_spot_mask is not None:
            self.register_buffer("supervised_spot_mask", supervised_spot_mask.clone().detach().float())
        else:
            self.register_buffer("supervised_spot_mask", torch.ones(num_spots, dtype=torch.float32))

        # 1. Projeção de Features do Jogador Alvo
        self.player_proj = nn.Linear(input_dim, hidden_dim)

        # 2. Projeção e Agregação dos 4 Companheiros de Equipe [32, 4, 18]
        self.teammate_proj = nn.Linear(input_dim, hidden_dim)
        self.teammate_pool = nn.Linear(hidden_dim, hidden_dim)

        # 3. Embeddings de Contexto Categórico
        self.team_emb = nn.Embedding(3, 16)      # CT, TR, ANY
        self.role_emb = nn.Embedding(12, 32)     # Roles
        self.stage_emb = nn.Embedding(10, 32)    # Plan stages
        self.context_fusion = nn.Linear(hidden_dim + 16 + 32 + 32, hidden_dim)

        # 4. Codificador Posicional e Dropout
        self.pos_encoder = PositionalEncoding(hidden_dim, max_len=seq_len + 4, dropout=dropout)

        # 5. Camadas do Transformer Encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dim_feedforward=feedforward_dim,
            dropout=dropout,
            activation='gelu',
            batch_first=True,
            norm_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.norm = nn.LayerNorm(hidden_dim)

        # 6. Heads Multitarefa
        # Head A: PositioningState (7 classes)
        self.head_state = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 7)
        )

        # Head B: SectorTransitionOccurs (2 classes: NO_TRANSITION, TRANSITION_OCCURS)
        self.head_transition_occurs = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 2)
        )

        # Head C: NextSector (5 classes canônicas: A, B, MID, CT, T)
        self.head_next_sector = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 5)
        )

        # Head D: CandidateSpotRanking (53 classes)
        self.head_spot = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_spots)
        )

        # Head E: Transition (7 classes)
        self.head_transition = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 7)
        )

        # Head F: ExitTrigger (8 classes)
        self.head_exit_trigger = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 8)
        )

    def forward(
        self,
        self_history: torch.Tensor,                    # [B, 32, 18]
        teammates: torch.Tensor,                       # [B, 32, 4, 18]
        temporal_mask: Optional[torch.Tensor] = None,   # [B, 32] float/bool
        teammate_mask: Optional[torch.Tensor] = None,   # [B, 32, 4] float/bool
        candidate_mask: Optional[torch.Tensor] = None,  # [B, 53] bool
        team_idx: Optional[torch.Tensor] = None,        # [B]
        role_idx: Optional[torch.Tensor] = None,        # [B]
        stage_idx: Optional[torch.Tensor] = None        # [B]
    ) -> Dict[str, torch.Tensor]:
        batch_size, seq_len, _ = self_history.shape

        if temporal_mask is None:
            temporal_mask = torch.ones(batch_size, seq_len, dtype=torch.float32, device=self_history.device)
        else:
            temporal_mask = temporal_mask.float()

        # 1. Projeção do Jogador Alvo [B, 32, hidden_dim]
        # Zera frames de padding pré-round
        h_player = self.player_proj(self_history) * temporal_mask.unsqueeze(-1)

        # 2. Agregação dos 4 Companheiros [B, 32, 4, 18] -> [B, 32, hidden_dim]
        h_tm = self.teammate_proj(teammates)
        if teammate_mask is not None:
            tm_mask = teammate_mask.float().unsqueeze(-1)
            h_tm = h_tm * tm_mask
            tm_denom = tm_mask.sum(dim=2).clamp(min=1.0)
            h_tm_pooled = h_tm.sum(dim=2) / tm_denom
        else:
            h_tm_pooled = torch.mean(h_tm, dim=2)
        h_tm_feat = F.gelu(self.teammate_pool(h_tm_pooled)) * temporal_mask.unsqueeze(-1)

        # Fusão Jogador + Companheiros
        x_seq = h_player + 0.3 * h_tm_feat

        # 3. Contexto Categórico
        if team_idx is None:
            team_idx = torch.zeros(batch_size, dtype=torch.long, device=self_history.device)
        if role_idx is None:
            role_idx = torch.zeros(batch_size, dtype=torch.long, device=self_history.device)
        if stage_idx is None:
            stage_idx = torch.zeros(batch_size, dtype=torch.long, device=self_history.device)

        emb_t = self.team_emb(team_idx).unsqueeze(1).expand(-1, seq_len, -1)
        emb_r = self.role_emb(role_idx).unsqueeze(1).expand(-1, seq_len, -1)
        emb_s = self.stage_emb(stage_idx).unsqueeze(1).expand(-1, seq_len, -1)

        fused_in = torch.cat([x_seq, emb_t, emb_r, emb_s], dim=-1)
        x_emb = self.context_fusion(fused_in)

        # 4. Codificador Posicional e Transformer Encoder
        x_pos = self.pos_encoder(x_emb)

        # Máscara de padding de atenção para Transformer: True onde deve ser ignorado
        key_padding_mask = (temporal_mask < 0.5)
        # Se algum exemplo tiver todos os frames mascarados (caso extremo), desativa mask para evitar NaNs
        all_padded = key_padding_mask.all(dim=-1)
        if all_padded.any():
            key_padding_mask = key_padding_mask.clone()
            key_padding_mask[all_padded, 0] = False

        encoded = self.transformer(x_pos, src_key_padding_mask=key_padding_mask)
        encoded = self.norm(encoded)

        # Pooling temporal: representação do último frame (t=32) + média ponderada pela temporal_mask
        last_step = encoded[:, -1, :]
        mask_weights = temporal_mask.unsqueeze(-1)
        denom = mask_weights.sum(dim=1).clamp(min=1.0)
        mean_step = (encoded * mask_weights).sum(dim=1) / denom
        pooled = (last_step + mean_step) * 0.5

        # 5. Predições das Heads
        logits_state = self.head_state(pooled)
        logits_transition_occurs = self.head_transition_occurs(pooled)
        logits_next_sector = self.head_next_sector(pooled)
        logits_spot = self.head_spot(pooled)
        logits_transition = self.head_transition(pooled)
        logits_trigger = self.head_exit_trigger(pooled)

        # 6. Mascaramento estrito de logits de spots:
        # - Spots fora da candidate_mask recebem -1e9
        # - Spots com supervised_spot_mask == 0 recebem -1e9 (nunca vencem seleção neural)
        neg_inf = -1e9
        spot_eligibility = self.supervised_spot_mask.bool().unsqueeze(0).expand(batch_size, -1)
        if candidate_mask is not None:
            full_mask = candidate_mask.bool() & spot_eligibility
        else:
            full_mask = spot_eligibility

        masked_logits_spot = torch.where(full_mask, logits_spot, torch.full_like(logits_spot, neg_inf))

        return {
            "logits_state": logits_state,
            "logits_transition_occurs": logits_transition_occurs,
            "logits_next_sector": logits_next_sector,
            "logits_spot": masked_logits_spot,
            "raw_logits_spot": logits_spot,
            "logits_transition": logits_transition,
            "logits_trigger": logits_trigger,
            "pooled_features": pooled
        }


class PositioningTransformerV2Loss(nn.Module):
    """
    Função de perda multitarefa canônica para Positioning Transformer V2:
    - Pesos balanceados para classes raras de PositioningState (Train-only)
    - NextSectorLoss ativada somente quando sector_transition_occurs == TRANSITION_OCCURS e next_sector_loss_mask == 1
    - CandidateSpotLoss ativada somente quando:
        1. spot_loss_mask == 1 (não-TRANSIT)
        2. target está na candidate_mask
        3. target possui supervised_spot_mask == 1
    """
    def __init__(
        self,
        state_weights: Optional[torch.Tensor] = None,
        supervised_spot_mask: Optional[torch.Tensor] = None,
        w_state: float = 1.0,
        w_transition_occurs: float = 0.5,
        w_next_sector: float = 0.8,
        w_spot: float = 1.5,
        w_transition: float = 0.6,
        w_trigger: float = 0.5
    ):
        super().__init__()
        self.w_state = w_state
        self.w_transition_occurs = w_transition_occurs
        self.w_next_sector = w_next_sector
        self.w_spot = w_spot
        self.w_transition = w_transition
        self.w_trigger = w_trigger

        self.loss_state_fn = nn.CrossEntropyLoss(weight=state_weights)
        self.loss_trans_occurs_fn = nn.CrossEntropyLoss()
        self.loss_next_sector_fn = nn.CrossEntropyLoss(reduction='none')
        self.loss_spot_fn = nn.CrossEntropyLoss(reduction='none')
        self.loss_trans_fn = nn.CrossEntropyLoss()
        self.loss_trig_fn = nn.CrossEntropyLoss()

        if supervised_spot_mask is not None:
            self.register_buffer("supervised_spot_mask", supervised_spot_mask.clone().detach().float())
        else:
            self.register_buffer("supervised_spot_mask", torch.ones(53, dtype=torch.float32))

    def forward(
        self,
        outputs: Dict[str, torch.Tensor],
        targets: Dict[str, torch.Tensor],
        candidate_mask: Optional[torch.Tensor] = None
    ) -> Dict[str, Any]:
        device = outputs["logits_state"].device
        batch_size = outputs["logits_state"].shape[0]

        # 1. State Loss
        l_state = self.loss_state_fn(outputs["logits_state"], targets["positioning_state"])

        # 2. Sector Transition Occurs Loss (Head B)
        l_trans_occurs = self.loss_trans_occurs_fn(
            outputs["logits_transition_occurs"],
            targets["sector_transition_occurs"]
        )

        # 3. Next Sector Loss (Head C) com Máscara Condicional Estrita
        # Ativa SOMENTE quando sector_transition_occurs == 1 (TRANSITION_OCCURS) e next_sector_loss_mask > 0.5
        unreduced_ns = self.loss_next_sector_fn(outputs["logits_next_sector"], targets["next_sector"])
        ns_mask = (targets["sector_transition_occurs"] == 1) & (targets["next_sector_loss_mask"] > 0.5)
        ns_valid_count = int(torch.sum(ns_mask).item())
        if ns_valid_count > 0:
            l_next_sector = torch.sum(unreduced_ns * ns_mask.float()) / float(ns_valid_count)
        else:
            l_next_sector = torch.tensor(0.0, device=device, requires_grad=True)

        # 4. Spot Loss (Head D) com Máscara Condicional Estrita
        # - Estado != TRANSIT (targets["positioning_state"] != 0)
        # - spot_loss_mask == 1
        # - target possui supervised_spot_mask == 1
        # - target presente na candidate_mask
        spot_targets = targets["candidate_spot_idx"]
        unreduced_spot = self.loss_spot_fn(outputs["raw_logits_spot"], spot_targets)

        target_supervised = (self.supervised_spot_mask[spot_targets] > 0.5)
        spot_active_mask = (targets["spot_loss_mask"].float() > 0.5) & (targets["positioning_state"] != 0) & target_supervised

        if candidate_mask is not None:
            # target presente na candidate_mask do batch
            batch_indices = torch.arange(batch_size, device=device)
            target_in_cand = candidate_mask[batch_indices, spot_targets].bool()
            spot_active_mask = spot_active_mask & target_in_cand

        spot_valid_count = int(torch.sum(spot_active_mask).item())
        if spot_valid_count > 0:
            l_spot = torch.sum(unreduced_spot * spot_active_mask.float()) / float(spot_valid_count)
        else:
            l_spot = torch.tensor(0.0, device=device, requires_grad=True)

        # 5. Transition Loss (Head E)
        l_trans = self.loss_trans_fn(outputs["logits_transition"], targets["transition"])

        # 6. Exit Trigger Loss (Head F)
        l_trig = self.loss_trig_fn(outputs["logits_trigger"], targets["exit_trigger"])

        # Total Loss Ponderada
        l_total = (
            self.w_state * l_state +
            self.w_transition_occurs * l_trans_occurs +
            self.w_next_sector * l_next_sector +
            self.w_spot * l_spot +
            self.w_transition * l_trans +
            self.w_trigger * l_trig
        )

        return {
            "loss_total": l_total,
            "loss_state": l_state,
            "loss_transition_occurs": l_trans_occurs,
            "loss_next_sector": l_next_sector,
            "loss_spot": l_spot,
            "loss_transition": l_trans,
            "loss_trigger": l_trig,
            "valid_next_sector_samples": ns_valid_count,
            "valid_spot_samples": spot_valid_count
        }
