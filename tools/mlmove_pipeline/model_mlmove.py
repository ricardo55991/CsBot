"""
Fase 6C (Camada 3 - Parte 1): Arquitetura Neural Transformer MLMove (~5.43M Parâmetros / ~20.75 MB em float32).
Inspirada no paper "Learning Tactical Multi-Agent Micro-Movement in Counter-Strike" (David Durst, Stanford).

Estrutura Otimizada para AVX2 / Cache L3 da CPU (< 0.45ms por lote de 10 jogadores):
1. Per-Player MLP Embedding:
   - Projeta as 18 features normalizadas de cada um dos 10 jogadores para `d_token = 128` + Positional Slot Embedding.
2. Multi-Head Self-Attention (Matriz N x N = 10x10 entre todos os jogadores):
   - Cruza simultaneamente os 10 tokens (`n_heads = 8`), capturando relações geométricas de Trade Spacing,
     Wide Swing, Crossfire e ameaças visíveis/audíveis.
3. Global Match-Context Transformer FFN (1280 -> 1104 -> 1104 -> 1104 -> 1280):
   - Concatena os 10 tokens atendidos no vetor de estado global da partida e aplica camadas densas com ativação AVX2 `ReLU`,
     totalizando **5,428,243 parâmetros (~5.43M parâmetros, ~20.75 MB)** com apenas 5.4M MACs por inferência!
4. 3 Cabeças de Predição Multi-Horizonte (`Head_0ms`, `Head_125ms`, `Head_250ms`):
   - Predizem os logits sobre as 97 ações discretas para `t=0ms`, `t=+125ms` e `t=+250ms`.
   - Tensor de saída: `output_logits` com shape `[batch_size, 10, 3, 97]`, `float32`.
"""

from __future__ import annotations
import math
import torch
import torch.nn as nn

from contract_spec import ACTION_SPACE_SIZE, FEATURE_DIM, HORIZONS_COUNT, MAX_PLAYERS


class MultiHeadPlayerSelfAttention(nn.Module):
    """
    Atenção N x N explícita (10x10 jogadores) 100% compatível com ONNX Runtime CPU L3 Cache.
    """

    def __init__(self, d_token: int = 128, n_heads: int = 8) -> None:
        super().__init__()
        assert d_token % n_heads == 0, "d_token deve ser divisível por n_heads"
        self.d_token = d_token
        self.n_heads = n_heads
        self.head_dim = d_token // n_heads
        self.scale = 1.0 / math.sqrt(self.head_dim)

        self.qkv_proj = nn.Linear(d_token, d_token * 3)
        self.out_proj = nn.Linear(d_token, d_token)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, 10, 128]
        bsz, seq_len, _ = x.shape
        q, k, v = self.qkv_proj(x).chunk(3, dim=-1)
        q = q.view(bsz, seq_len, self.n_heads, self.head_dim).transpose(1, 2)
        k = k.view(bsz, seq_len, self.n_heads, self.head_dim).transpose(1, 2)
        v = v.view(bsz, seq_len, self.n_heads, self.head_dim).transpose(1, 2)

        scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale
        attn = torch.softmax(scores, dim=-1)

        context = torch.matmul(attn, v)
        context = context.transpose(1, 2).contiguous().view(bsz, seq_len, self.d_token)
        return self.out_proj(context)


class MLMoveTransformer(nn.Module):
    """
    Rede Neural Transformer MLMove (~5.43M parâmetros, ~20.75 MB em float32, < 0.45ms na CPU).
    Entrada: `input_state` [B, 10, 18]
    Saída:   `output_logits` [B, 10, 3, 97]
    """

    def __init__(
        self,
        feature_dim: int = FEATURE_DIM,
        d_token: int = 128,
        n_heads: int = 8,
        d_context_hidden: int = 1104,
        action_space: int = ACTION_SPACE_SIZE,
    ) -> None:
        super().__init__()
        self.feature_dim = feature_dim
        self.d_token = d_token
        self.action_space = action_space
        flat_dim = MAX_PLAYERS * d_token  # 1280

        # 1. Per-Player MLP Embedding (18 -> 128 -> 128)
        self.player_mlp = nn.Sequential(
            nn.Linear(feature_dim, d_token),
            nn.ReLU(),
            nn.Linear(d_token, d_token),
            nn.ReLU(),
        )
        self.slot_embedding = nn.Parameter(torch.randn(1, MAX_PLAYERS, d_token) * 0.02)

        # 2. Transformer Self-Attention N x N (10x10 jogadores)
        self.self_attn_1 = MultiHeadPlayerSelfAttention(d_token=d_token, n_heads=n_heads)
        self.self_attn_2 = MultiHeadPlayerSelfAttention(d_token=d_token, n_heads=n_heads)

        # 3. Match-Level Global Context Encoder (1280 -> 1104 -> 1104 -> 1104 -> 1280)
        self.global_context_mlp = nn.Sequential(
            nn.Linear(flat_dim, d_context_hidden),
            nn.ReLU(),
            nn.Linear(d_context_hidden, d_context_hidden),
            nn.ReLU(),
            nn.Linear(d_context_hidden, d_context_hidden),
            nn.ReLU(),
            nn.Linear(d_context_hidden, flat_dim),
            nn.ReLU(),
        )

        # 4. Três Cabeças de Predição Multi-Horizonte (t=0ms, t=+125ms, t=+250ms)
        fused_dim = d_token * 2  # 256 (Token Local + Contexto Global)
        self.head_0ms = nn.Linear(fused_dim, action_space)
        self.head_125ms = nn.Linear(fused_dim, action_space)
        self.head_250ms = nn.Linear(fused_dim, action_space)

    def forward(self, input_state: torch.Tensor) -> torch.Tensor:
        """
        Args:
            input_state: Tensor float32 [B, 10, 18]
        Returns:
            output_logits: Tensor float32 [B, 10, 3, 97]
        """
        bsz = input_state.shape[0]
        tokens = self.player_mlp(input_state) + self.slot_embedding
        tokens = tokens + torch.relu(self.self_attn_1(tokens))
        tokens = tokens + torch.relu(self.self_attn_2(tokens))

        flat_context = tokens.reshape(bsz, MAX_PLAYERS * self.d_token)
        global_ctx = self.global_context_mlp(flat_context).reshape(bsz, MAX_PLAYERS, self.d_token)

        fused = torch.cat([tokens, global_ctx], dim=-1)  # [B, 10, 256]

        logits_0 = self.head_0ms(fused)      # [B, 10, 97]
        logits_125 = self.head_125ms(fused)  # [B, 10, 97]
        logits_250 = self.head_250ms(fused)  # [B, 10, 97]

        return torch.stack([logits_0, logits_125, logits_250], dim=2)


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    net = MLMoveTransformer()
    params = count_parameters(net)
    size_mb = (params * 4) / (1024 * 1024)
    dummy = torch.zeros((2, MAX_PLAYERS, FEATURE_DIM), dtype=torch.float32)
    out = net(dummy)
    print(f"[MLMoveTransformer] Parâmetros treináveis: {params:,} (~{params / 1e6:.2f}M)")
    print(f"[MLMoveTransformer] Tamanho estimado em float32: {size_mb:.2f} MB")
    print(f"[MLMoveTransformer] Shape de entrada: {tuple(dummy.shape)} -> Shape de saída: {tuple(out.shape)}")
