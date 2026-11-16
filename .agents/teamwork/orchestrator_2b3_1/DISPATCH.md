## 2026-11-08T21:21:06Z
# FASE 3A.3-B, MARCO 2B.3: TREINAMENTO COMPLETO DO POSITIONING TRANSFORMER TEMPORAL REAL

## DECISÃO DE ENTRADA
Os marcos anteriores concluíram:
- CANONICAL_TEMPORAL_DATALOADER_READY_FOR_PILOT
- REAL_TEMPORAL_POSITIONING_PILOT_READY_FOR_FULL_TRAINING
- FULL_TEMPORAL_INDEX_READY_FOR_FULL_TRAINING
- LABEL_CONTRACT_V2_READY_FOR_FULL_TRAINING

Esta mensagem autoriza:
1. adaptação do modelo ao label_contract_v2;
2. treinamento completo nas três seeds canônicas (42026, 42027, 42028);
3. seleção de candidato usando exclusivamente Validation;
4. auditoria matemática, estatística e de proveniência;
5. comparação com baselines reais.

Esta mensagem não autoriza:
- inferência no Test;
- inferência no Final Holdout;
- exportação ONNX;
- integração C#;
- shadow mode;
- MLMove V2;
- Jump Head;
- deploy.

Limites:
- max_active_subagents = 6
- nested_subagents = false
- only_orchestrator_can_delegate = true
- reuse_agents_within_milestone = true
- spawn_only_when_required = true
- kill_all_on_completion = true
