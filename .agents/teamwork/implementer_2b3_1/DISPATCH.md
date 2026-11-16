## 2026-11-08T21:22:47Z

Você é o Model and Training Implementer da Fase 3A.3-B, Marco 2B.3: Treinamento Completo do Positioning Transformer Temporal Real.

Seu diretório de trabalho exclusivo para logs e metadados é:
c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\implementer_2b3_1

Você DEVE ler imediatamente o arquivo com o pedido original completo:
c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\ORIGINAL_REQUEST.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Diretrizes Críticas:
1. Regras do AGENTS.md são mandatórias e inegociáveis (01-evidence-before-claims, 02-no-test-contamination, 03-zero-support-is-na, etc.).
2. O conjunto Test (67 demos) e Final Holdout JAMAIS devem ser abertos, lidos ou submetidos a inferência pelo treinador. Apenas seus hashes e metadados de catálogo participam do input_snapshot.json.
3. Classes com support zero devem ser estritamente N/A.
4. Todo percentual deve vir acompanhado de numerador e denominador explícitos (N/D).
5. Trabalhe de forma incremental e metódica:
   - Fase A: Snapshot Imutável (input_snapshot.json) e validação estrita do join 1:1 entre shards temporais base e sidecars de labels v2 (3.411.434 linhas em cada, 0 missing, 0 duplicate, 0 conflict).
   - Fase B: Arquitetura PositioningTransformerV2RealTemporal, máscaras condicionais de loss, cálculo de pesos Train-only (class_weights.json, frozen_training_config.json, frozen_composite_formula.json) e Preflight Computacional de 100 batches train + 20 batches val (compute_preflight.json).
   - Fase C: Treinamento multi-seed (42026, 42027, 42028), salvamento determinístico em seed_42026/, seed_42027/, seed_42028/, monitoramento anti-colapso (collapse_monitoring.json).
   - Fase D: Avaliação de Validation, cálculo de CompositeScore, seleção de candidato (selected_candidate.pt e best_model_selection.json), comparação de seeds (three_seed_comparison.json), comparação com baselines reais (baseline_comparison.json) e relatório de ganho temporal (temporal_gain_report.json).
   - Fase E: Implementação e execução dos 22 testes automatizados mínimos requeridos pela Seção 16 do ORIGINAL_REQUEST.md e validação de que a suíte C# permanece verde.
6. Ao final, escreva um handoff detalhado em c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\implementer_2b3_1\handoff.md documentando todos os comandos executados, hashes SHA-256 de todos os artefatos gerados, métricas e resultados dos testes. Envie uma mensagem ao orquestrador quando concluir.
