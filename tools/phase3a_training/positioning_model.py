#!/usr/bin/env python3
"""
Fase 3A: Arquitetura Neural do Positioning Transformer V1.

Configuração:
- hidden_dim = 192
- transformer_layers = 3
- attention_heads = 6
- feedforward_dim = 768
- dropout = 0.10
- sequence_length = 32

Inputs:
- history: [batch, 32, 18]
- teammates: [batch, 32, 4, 18]
- candidate_mask: [batch, 53]
- context: team, role, tactic, stage, sector

Heads:
- Head A: PositioningState (7 classes)
- Head B: NextSector (6 classes)
- Head C: CandidateSpotRanking (53 classes com mask e spot_loss_mask)
- Head D: Transition (7 classes)
- Head E: ExitTrigger (8 classes)
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F

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

class PositioningTransformerV1(nn.Module):
    def __init__(
        self,
        input_dim: int = 18,
        hidden_dim: int = 192,
        num_layers: int = 3,
        num_heads: int = 6,
        feedforward_dim: int = 768,
        dropout: float = 0.10,
        seq_len: int = 32,
        num_spots: int = 53
    ):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.seq_len = seq_len
        self.num_spots = num_spots

        # 1. Projeção de Features do Jogador Alvo
        self.player_proj = nn.Linear(input_dim, hidden_dim)

        # 2. Projeção e Agregação de Companheiros de Equipe [32, 4, 18]
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

        # Head B: NextSector (6 classes)
        self.head_sector = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 6)
        )

        # Head C: CandidateSpotRanking (53 classes)
        self.head_spot = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_spots)
        )

        # Head D: Transition (7 classes)
        self.head_transition = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 7)
        )

        # Head E: ExitTrigger (8 classes)
        self.head_exit_trigger = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 8)
        )

    def forward(
        self,
        history: torch.Tensor,                # [B, 32, 18]
        teammates: torch.Tensor,              # [B, 32, 4, 18]
        candidate_mask: torch.Tensor,         # [B, 53] (bool)
        team_idx: torch.Tensor = None,        # [B]
        role_idx: torch.Tensor = None,        # [B]
        stage_idx: torch.Tensor = None        # [B]
    ):
        batch_size, seq_len, _ = history.shape

        # 1. Projeção do Jogador Alvo [B, 32, hidden_dim]
        h_player = self.player_proj(history)

        # 2. Agregação dos 4 Companheiros [B, 32, 4, 18] -> [B, 32, hidden_dim]
        h_tm = self.teammate_proj(teammates)
        h_tm_pooled = torch.mean(h_tm, dim=2) # Mean pooling sobre os 4 aliados
        h_tm_feat = F.gelu(self.teammate_pool(h_tm_pooled))

        # Fusão Jogador + Companheiros
        x_seq = h_player + 0.3 * h_tm_feat

        # 3. Incorporar Contexto Categórico
        if team_idx is None:
            team_idx = torch.zeros(batch_size, dtype=torch.long, device=history.device)
        if role_idx is None:
            role_idx = torch.zeros(batch_size, dtype=torch.long, device=history.device)
        if stage_idx is None:
            stage_idx = torch.zeros(batch_size, dtype=torch.long, device=history.device)

        emb_t = self.team_emb(team_idx).unsqueeze(1).expand(-1, seq_len, -1)
        emb_r = self.role_emb(role_idx).unsqueeze(1).expand(-1, seq_len, -1)
        emb_s = self.stage_emb(stage_idx).unsqueeze(1).expand(-1, seq_len, -1)

        fused_in = torch.cat([x_seq, emb_t, emb_r, emb_s], dim=-1)
        x_emb = self.context_fusion(fused_in)

        # 4. Adicionar Posição e Executar Transformer
        x_pos = self.pos_encoder(x_emb)
        encoded = self.transformer(x_pos)
        encoded = self.norm(encoded)

        # Pooling temporal: representação do último frame (t=32) + média global
        last_step = encoded[:, -1, :]
        mean_step = torch.mean(encoded, dim=1)
        pooled = (last_step + mean_step) * 0.5

        # 5. Predições das Heads
        logits_state = self.head_state(pooled)
        logits_sector = self.head_sector(pooled)
        logits_spot = self.head_spot(pooled)
        logits_transition = self.head_transition(pooled)
        logits_trigger = self.head_exit_trigger(pooled)

        # 6. Mascaramento estrito de logits de spots não-candidatos
        if candidate_mask is not None:
            # Onde candidate_mask é False, logit recebe valor fortemente negativo (-1e9)
            neg_inf = -1e9
            masked_logits_spot = torch.where(candidate_mask, logits_spot, torch.full_like(logits_spot, neg_inf))
        else:
            masked_logits_spot = logits_spot

        return {
            "logits_state": logits_state,
            "logits_sector": logits_sector,
            "logits_spot": masked_logits_spot,
            "raw_logits_spot": logits_spot,
            "logits_transition": logits_transition,
            "logits_trigger": logits_trigger,
            "pooled_features": pooled
        }

class PositioningMultitaskLoss(nn.Module):
    """
    Função de perda multitarefa com:
    - Pesos balanceados para classes raras de PositioningState
    - Mascaramento estrito da perda de SpotId quando em TRANSIT ou sem label elegível
    """
    def __init__(
        self,
        state_weights: torch.Tensor = None,
        w_state: float = 1.0,
        w_sector: float = 0.8,
        w_spot: float = 1.5,
        w_transition: float = 0.6,
        w_trigger: float = 0.5
    ):
        super().__init__()
        self.w_state = w_state
        self.w_sector = w_sector
        self.w_spot = w_spot
        self.w_transition = w_transition
        self.w_trigger = w_trigger

        self.loss_state_fn = nn.CrossEntropyLoss(weight=state_weights)
        self.loss_sector_fn = nn.CrossEntropyLoss()
        self.loss_spot_fn = nn.CrossEntropyLoss(reduction='none')
        self.loss_trans_fn = nn.CrossEntropyLoss()
        self.loss_trig_fn = nn.CrossEntropyLoss()

    def forward(self, outputs, targets):
        """
        outputs: dict de forward
        targets: dict com:
          - positioning_state: [B]
          - next_sector: [B]
          - candidate_spot_idx: [B]
          - spot_loss_mask: [B] (bool)
          - transition: [B]
          - exit_trigger: [B]
        """
        l_state = self.loss_state_fn(outputs["logits_state"], targets["positioning_state"])
        l_sector = self.loss_sector_fn(outputs["logits_sector"], targets["next_sector"])

        # Perda de Spot mascarada
        spot_loss_unreduced = self.loss_spot_fn(outputs["logits_spot"], targets["candidate_spot_idx"])
        spot_mask = targets["spot_loss_mask"].float()
        
        # Zero loss se o batch inteiro for TRANSIT
        valid_spot_samples = torch.sum(spot_mask)
        if valid_spot_samples > 0:
            l_spot = torch.sum(spot_loss_unreduced * spot_mask) / valid_spot_samples
        else:
            l_spot = torch.tensor(0.0, device=outputs["logits_state"].device, requires_grad=True)

        l_trans = self.loss_trans_fn(outputs["logits_transition"], targets["transition"])
        l_trig = self.loss_trig_fn(outputs["logits_trigger"], targets["exit_trigger"])

        l_total = (
            self.w_state * l_state +
            self.w_sector * l_sector +
            self.w_spot * l_spot +
            self.w_transition * l_trans +
            self.w_trigger * l_trig
        )

        return {
            "loss_total": l_total,
            "loss_state": l_state,
            "loss_sector": l_sector,
            "loss_spot": l_spot,
            "loss_transition": l_trans,
            "loss_trigger": l_trig,
            "valid_spot_samples": int(valid_spot_samples.item())
        }
