# Dispatch Record — Dataset Index Implementer
Timestamp: 2026-11-08T16:20:00Z
Role: Dataset Index Implementer (teamwork_worker)
Working Directory: .agents/teamwork/dataset_implementer_1

## 2026-11-08T16:19:34Z
Você é o Dataset Index Implementer da equipe compacta de orquestração do Marco 2B.1 (Fase 3A.3-B).
Seu papel: teamwork_worker
Seu diretório de trabalho: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\dataset_implementer_1
Seu orquestrador (parent): ed708b48-1669-4f65-b810-5bfc8ff522da
Requisição autoritativa imutável: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\ORIGINAL_REQUEST.md (LEIA ESTE ARQUIVO OBRIGATORIAMENTE ANTES DE QUALQUER AÇÃO).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

OBJETIVO DA SUA TAREFA:
Materializar os índices temporais reais e canônicos de posicionamento para o corpus completo de Mirage v2 em shards Parquet versionados para ambiente de produção, cobrindo todas as demos disponíveis em cada split (Train = 311, Validation = 66, Test = 67; excluindo formalmente as 8 demos sem NPZ), integrando sequências de Objective/Save e relabelando NextSector com horizonte futuro real, sem executar treinamento de modelos nem inferência preditiva no split Test.

REQUISITOS E ENTREGÁVEIS:
1. Preservação do Piloto:
   - Preservar intacto o dataset piloto anterior em `datasets/mirage_v2/positioning/positioning_sequences_v1/positioning_sample_sequences.parquet` (calcular e conferir seu hash SHA-256 de 64 caracteres) e catalogá-lo formalmente como `PILOT_SUBSET_25_DEMOS_PER_SPLIT`.
2. Nova Versão sob `datasets/mirage_v2/positioning_v2_full_temporal/`:
   - Consumir estritamente `datasets/mirage_v2/canonical_temporal_splits_v1.json` (311 Train, 66 Validation, 67 Test) e excluir formalmente as 8 demos com status `RAW_DEM_WITHOUT_NPZ`.
   - Registrar para cada demo: `demo_id`, `match_id`, `split`, `npz_path`, `npz_sha256`, `frame_count`, `round_count`, `player slots`, `accepted`, `rejection_reason`.
3. Política Única e Idêntica de Janelas para Todos os Splits:
   - `sample_rate = 16 Hz`, `sequence_length = 32 frames`, `stride = 16 frames`, `overlap = 50%`.
   - Limites de round detectados via resets de round_time_norm (X[:, 0, 17] com diff > 0.15).
   - Início de round: padding com zeros e temporal_mask[:32-k] = 0.0, temporal_mask[32-k:] = 1.0.
   - Aliados reais dos slots autênticos do mesmo time.
   - Posições com coordenadas inválidas [0, 0, 0] devem ser 100% rejeitadas ou mascaradas.
4. Materialização dos Shards Parquet e 21 Campos Canônicos:
   - Shards Parquet versionados contendo ponteiros e labels, sem tensores densos duplicados.
   - Cada registro deve conter no mínimo:
     `sequence_id`, `demo_id`, `match_id`, `round_id`, `player_id`, `slot`, `split`, `window_start_frame`, `window_end_frame`, `label_frame`, `npz_path`, `PositioningState`, `ObjectiveSubtype`, `SaveSubtype`, `NextSector`, `CandidateSpotId`, `SpotLossMask`, `Transition`, `ExitTrigger`, `confidence`, `provenance_type` e `next_sector_source`.
5. Integração de Objective e Save:
   - Integrar registros aprovados de `datasets/mirage_v2/positioning/objective_save_sequences.parquet`.
   - Regras de precedência: `direct plant/defuse > OBJECTIVE`, `confirmed save evidence > SAVE`, `OBJECTIVE/SAVE > generic HOLD ou TRANSIT`.
   - Em caso de substituição de label, registrar `old_label`, `new_label`, `precedence_rule` e `provenance`.
   - Contabilidade de integração: `candidate_windows = integrated + replaced + duplicated + rejected + low_confidence_excluded`.
6. Relabeling de NextSector com Horizonte Futuro Real:
   - `NextSector`: próximo setor semântico efetivamente visitado pelo jogador após o final da janela dentro do horizonte congelado em `datasets/mirage_v2/contracts/mirage_spot_catalog_v3.json`.
   - Classes restritas a {A, B, MID, CT, T, DYNAMIC}.
   - NUNCA usar o setor atual como label futuro se não houver transição de setor no horizonte.
   - Proibido usar target da Utility AI ou candidate spots futuros como entrada da janela.
   - Registrar: `current_sector`, `next_sector`, `transition_tick`, `horizon_frames`, `next_sector_source`, `confidence`.
7. Contabilidade Integral e Auditoria de Duplicatas:
   - Fechamento: `raw_window_candidates = accepted + rejected + explicitly_masked` e `processed_demo_count = expected_demo_count`.
   - Duplicatas: `exact duplicate sequences = 0`, `cross-split duplicates = 0`, `conflicting labels for same window = 0`.
8. Materializar exatamente os 12 artefatos do diretório `datasets/mirage_v2/positioning_v2_full_temporal/`:
   - 6 shards Parquet: `shard_000.parquet` a `shard_005.parquet` particionando o índice temporal integral de todas as demos.
   - 6 companion JSONs:
     `dataset_manifest.json` (resumo de volumes, hashes, políticas e contagens por split)
     `demo_inventory.json` (inventário detalhado das 444 demos + 8 excluídas)
     `excluded_demos_manifest.json` (justificativa formal individual para as 8 demos RAW_DEM_WITHOUT_NPZ)
     `pilot_preservation_catalog.json` (catalogação imutável do dataset piloto anterior com hash SHA-256 e status PILOT_SUBSET_25_DEMOS_PER_SPLIT)
     `objective_save_integration.json` (contabilidade completa de integração, precedência e substituições)
     `next_sector_relabeling.json` (estatísticas de horizontes, transições e distribuição multiclasse por split de NextSector)
9. Suíte de Testes Unitários Obrigatórios:
   - Criar `tests/test_phase3a3_b_milestone2b1_full_index.py` cobrindo rigorosamente os 20 testes especificados nos Critérios de Aceite.
   - Executar os testes via terminal com `pytest` e executar a suíte C# do CsBot (`dotnet test`) garantindo 100% verde sem regressões.
10. Preparação dos Artefatos de Suporte em `training_runs/positioning_v2_real_temporal/`:
   - Gerar os dados e scripts auxiliares para as auditorias (ex: divergência Jensen-Shannon piloto vs full, auditoria de SpotRanking, gates do dataloader).
11. Restrições Estritas:
   - NÃO executar treinamento de modelos nem inferência preditiva no split Test.
   - Operar com streaming, memory mapping e bounded caches na geração dos shards para evitar estouro de RAM.
12. Finalização:
   - Redigir seu `handoff.md` detalhado em `.agents/teamwork/dataset_implementer_1/` e enviar mensagem de conclusão ao orquestrador.
