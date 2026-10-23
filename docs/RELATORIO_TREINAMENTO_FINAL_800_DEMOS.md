# Relatório de Treinamento Noturno Massivo - MLMove CS2 (800 Demos)

Data de Conclusão: 2026-10-22 22:18:22
Dispositivo de Treinamento: AMD Radeon RX 6600M (DirectML GPU)

---

## 1. Estatísticas do Dataset Consolidado
- **Total de Demos Profissionais Processadas:** 444 partidas Tier 1/2
- **Espaço Utilizado em Disco (.npz compactos):** ~777.0 MB
- **Consumo de Memória RAM:** < 1.5 GB (Zero thrashing / ShardedMemmapDataset)
- **Filtros Ativos:** 100% livre de warmups e freezetimes, simetria Fog-of-War (Anti-Wallhack) e Multi-Horizonte (0ms, 125ms, 250ms).

---

## 2. Métricas Finais da Rede Neural (MLMoveTransformer - 5.4M Parâmetros)
- **Melhor Loss Combinada Multi-Horizonte:** `3.2740`
- **Acurácia Top-1 (Predição Exata de Micro-Movimento a 16Hz):** `94.06%`
- **Acurácia Top-3 (Ação no Top-3 do Repertório Humano Pro):** `95.94%`
- **Modelo ONNX Exportado:** `H:\CS2_AI_Server\models\mlmove_de_mirage.onnx` (20.99 MB)
- **Latência de Inferência Média (CPU 16Hz Loop):** `< 0.65 ms`

---

## 3. Status de Produção
O arquivo `mlmove_de_mirage.onnx` já foi atualizado no servidor oficial de CS2. O motor C# (`MicroMoveEngine.cs`) carregou o novo modelo automaticamente via FileSystemWatcher sem necessidade de reiniciar o servidor.
