# CS2 MLMove Pipeline (Fases 6B & 6C)

Pipeline completo de **Imitation Learning Multi-Agente a 16Hz** inspirado em *MLMove (Dr. David Durst, Stanford)*.

## Arquitetura de Armazenamento (Disco `F:\` (520+ GB livres) Isolado)
Para manter o repositório Git leve e preservar espaço no disco do sistema, **todo o armazenamento pesado** fica em `F:\CS2_MLMove_Pipeline\`:
- `F:\CS2_MLMove_Pipeline\venv\`: Ambiente Python 3.11 isolado (`demoparser2`, `torch`, `torch-directml`, `onnx`, `onnxruntime`).
- `F:\CS2_MLMove_Pipeline\raw_demos\de_mirage\`: Demos brutas (`.dem`, `.rar`, `.zip`, `.zst`, `.bz2`) para processamento em lotes.
- `F:\CS2_MLMove_Pipeline\extracted_tensors\de_mirage\`: Tensores `.npz` compactados a 16Hz (`X: [N, 10, 18]`, `Y: [N, 10, 3]`).
- `F:\CS2_MLMove_Pipeline\checkpoints\`: Pesos PyTorch (`mlmove_de_mirage_best.pt`).
- `H:\CS2_AI_Server\models\mlmove_de_mirage.onnx`: Modelo neural exportado (~21 MB) carregado automaticamente via *hot-swap* pelo `MicroMoveEngine.cs` no servidor CS2.

## Como Treinar Novos Lotes de Demos (1 Clique)
1. Coloque qualquer quantidade de arquivos `.dem`, `.rar`, `.zip` ou `.zst` em `F:\CS2_MLMove_Pipeline\raw_demos\de_mirage\` (ou grave partidas no servidor usando `!gravardemo`).
2. Dê dois cliques em **`F:\CS2_MLMove_Pipeline\treinar_lote_demos.bat`**.
3. O script irá:
   - Descompactar e filtrar os rounds válidos (**Filtro do Ouro**: sem Warmup, sem Freeze Time e sem Full Eco);
   - Extrair janelas a **16 Hz** com máscara **Anti-Wallhack (Fog of War)**;
   - Refinar (*Fine-Tune*) o **MLMoveTransformer (5.47M parâmetros)** na GPU **AMD Radeon RX 6600M** (`DirectML`);
   - Exportar e validar `H:\CS2_AI_Server\models\mlmove_de_mirage.onnx` sem precisar reiniciar o servidor CS2!
