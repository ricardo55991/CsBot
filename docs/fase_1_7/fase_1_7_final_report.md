# Relatório Consolidado de Homologação e Normalização Semântica — Mirage V2 (Fase 1.7)

> **Data:** 05/11/2026  
> **Fase:** 1.7 — Normalização Semântica do Perfil Mirage V2 e Homologação Visual Humana  
> **Mapa:** `de_mirage` (`map_profile_version: 2`)  
> **Hash Canônico SHA-256 de `de_mirage.json`:** `26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1`  
> **Decisão Técnica Formal:** `MIRAGE_SEMANTIC_PROFILE_READY_FOR_PHASE_2_PENDING_HUMAN_REVIEW`  

---

## 1. Resumo Executivo

A **Fase 1.7** conclui o ciclo preparatório espacial e semântico do perfil de mapa Mirage V2 antes do avanço para a Fase 2 (treinamento e datasets do Positioning Transformer e MLMove V2).

Todos os requisitos estritos do plano de implementação foram rigorosamente cumpridos:
1. **Auditoria dos Chokepoints:** Todos os 7 chokepoints legados foram auditados contra 444 demos (13.676 rounds) e malha de navegação. As propostas de ajuste foram catalogadas sem alterar nenhuma coordenada no arquivo canônico.
2. **Normalização do Schema:** Criado contrato semântico uniforme para todos os 45 spots, eliminando deduções baseadas em substrings ou prefixos e formalizando enums tipados (`SpotSide`, `SpotBombsite`, `SpotUsage`, `SpotConfidence`, `SpotValidationStatus`).
3. **Atribuição de Confiança e Status:** 28 spots classificados como `HIGH` (62.2%), 11 como `MEDIUM` (24.4%) e 6 como `LOW` (13.3%). Nenhum dos 19 spots não observados na partida normal foi classificado como `RUNTIME_OBSERVED` (todos receberam `RUNTIME_NOT_OBSERVED` ou `INSUFFICIENT_EVIDENCE`). Nenhum dos 20 spots corrigidos foi pré-aprovado indevidamente como `APPROVED_BY_USER`.
4. **Instrumentação Forense do Salto:** O `JumpExecutionGate` foi instrumentado com os 8 eventos estruturados (`JUMP_REQUESTED`, `JUMP_EXECUTED`, `JUMP_SUPPRESSED_AIRBORNE`, `JUMP_SUPPRESSED_COOLDOWN`, `JUMP_SUPPRESSED_CONTEXT`, `JUMP_SUPPRESSED_NO_JUMP_ZONE`, `JUMP_LANDED`, `REPEATED_JUMP_SEQUENCE_DETECTED`), preenchendo todos os 21 campos forenses e implementando proteção anti-bunny hop sem alterar as janelas de resfriamento ou física existentes.
5. **Evidência Visual no CS2:** Geradas 16 screenshots no CS2 real em `de_mirage` (8 em primeira pessoa e 8 externas/aéreas dos 8 spots mais sensíveis) em `docs/fase_1_7/screenshots/`.
6. **Suíte de Testes Aprovada:** 291 testes unitários C# aprovados com 0 falhas em `CsBot.slnx` (`dotnet test -c Release`), acrescidos dos testes Python da pipeline (8/8 aprovados).

---

## 2. Auditoria dos Chokepoints Legados

| ChokepointId | Posição Atual (V1) | Setor Atual | Posição Proposta (V2) | Valve Place Real | Classificação | Confiança | Evidências / Demos |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `caverna` | `[-250.0, -200.0, -160.0]` | Underpass | `[135.0, -1850.0, -168.0]` | ARamp | `WRONG_SECTOR` | `HIGH` | 4.210 / 432 |
| `palacio` | `[-350.0, -480.0, -90.0]` | Mid | `[250.0, -2150.0, -40.0]` | Palace | `WRONG_SECTOR` | `HIGH` | 3.890 / 428 |
| `janela_meio` | `[-1380.0, -540.0, -120.0]` | SnipersNest | `[-1130.0, -480.0, -168.0]` | SnipersNest | `WRONG_HEIGHT` | `HIGH` | 2.980 / 410 |
| `conector` | `[-820.0, -840.0, -160.0]` | Connector | `[-820.0, -840.0, -160.0]` | Connector | `VALID_REGION_CENTER` | `HIGH` | 4.850 / 438 |
| `catwalk` | `[-950.0, -1050.0, -140.0]` | Connector CT | `[-520.0, -280.0, -140.0]` | Catwalk | `WRONG_SECTOR` | `HIGH` | 3.670 / 420 |
| `tapete_b` | `[-650.0, 650.0, -60.0]` | Apartments | `[-650.0, 650.0, -60.0]` | Apartments | `VALID_REGION_CENTER` | `HIGH` | 4.920 / 440 |
| `underpass` | `[-720.0, -1020.0, -220.0]` | Underpass Sul | `[-750.0, -450.0, -240.0]` | Underpass | `AMBIGUOUS_REGION_CENTER` | `HIGH` | 2.740 / 395 |

> **Nota:** As propostas de alteração dos chokepoints não foram aplicadas nesta fase, respeitando estritamente a baseline.

---

## 3. Matriz de Confiança e Status dos 45 Spots

- **Confiança Geral:**
  - `HIGH`: 28 spots (62.2%)
  - `MEDIUM`: 11 spots (24.4%)
  - `LOW`: 6 spots (13.3%)
- **Status de Validação:**
  - `RUNTIME_OBSERVED`: 16 spots (observados em partida normal sem travamentos)
  - `RUNTIME_NOT_OBSERVED`: 15 spots (não acionados na amostragem da partida normal de 5 rounds)
  - `PENDING_HUMAN_REVIEW`: 8 spots (os 8 spots mais sensíveis aguardando confirmação do usuário)
  - `INSUFFICIENT_EVIDENCE`: 6 spots (preservados intactos como LOW)
  - `APPROVED_BY_USER`: 0 spots (nenhuma promoção artificial)
  - `REJECTED_BY_USER`: 0 spots

---

## 4. Instrumentação do JumpExecutionGate e Proteção Anti-Bunny Hop

O subsistema de salto opera com instrumentação completa através da struct/evento `JumpGateEvent`:
1. **Deduplicação de Eventos:** Supressões por airborne e cooldown são registradas por episódio;
2. **Detecção Anti-Bunny Hop:** Requisições emitidas em janela $< 5$ ticks após pouso disparam `REPEATED_JUMP_SEQUENCE_DETECTED`, forçando o rebaixamento da ação para locomoção terrestre (`ConvertedActionId <= 48`);
3. **Auditoria Forense (21 Campos):** `InternalRoundId`, `OfficialRoundNumber`, `Tick`, `Slot`, `Team`, `Role`, `Source`, `JumpReason`, `Grounded`, `Airborne`, `Falling`, `LastJumpTick`, `LastLandingTick`, `CooldownRemaining`, `Allowed`, `SuppressionReason`, `Position`, `Velocity2D`, `VelocityZ`, `TacticId`, `PlanStage`.

---

## 5. Resultados dos Testes Automatizados

### 5.1 Suíte C# (.NET 10.0 Release)
- **Comando:** `dotnet test tests/CsBotManager.Tests/CsBotManager.Tests.csproj -c Release --no-build --nologo`
- **Total Descoberto:** 291
- **Aprovados:** 291 (100%)
- **Com Falha:** 0 (0%)
- **Ignorados:** 0 (0%)
- **Duração:** 3.0 segundos
- **17 Novos Testes da Fase 1.7:**
  1. `AllSpotsHaveUniformSemanticSchema`: Aprovado
  2. `NoSpotInfersSideFromPrefix`: Aprovado
  3. `NoSpotInfersBombsiteFromSubstring`: Aprovado
  4. `AllChokepointsInsidePlayableBounds`: Aprovado
  5. `ChokepointRegionMayDifferFromHoldSpot`: Aprovado
  6. `LowConfidenceSpotCannotBeSoleNeuralTarget`: Aprovado
  7. `RuntimeObservedRequiresTelemetryEvidence`: Aprovado
  8. `JumpRequestProducesOneTerminalEvent`: Aprovado
  9. `AirborneJumpRequestIsSuppressed`: Aprovado
  10. `RepeatedJumpSequenceIsDetected`: Aprovado
  11. `RepeatedJumpSequenceIsNotExecuted`: Aprovado
  12. `VisualEvidencePositionMatchesProfile`: Aprovado
  13. `VisualEvidenceContainsTwoImagesPerSpot`: Aprovado
  14. `PipelineCannotApproveHumanReview`: Aprovado
  15. `HumanDecisionDefaultsToPending`: Aprovado
  16. `InsufficientEvidenceCoordinatesRemainUnchanged`: Aprovado
  17. `SmallAdjustmentCoordinatesRemainUnchanged`: Aprovado

### 5.2 Testes da Pipeline Python
- **Comando:** `python -m unittest discover -s tests -p "*test*.py"`
- **Testes Executados:** 8
- **Resultado:** 8 aprovados (0 falhas)

---

## 6. Inventário de Entregáveis da Fase 1.7

Todos os 11 documentos e 16 imagens obrigatórias foram criados e validados:

1. `docs/fase_1_7/mirage_chokepoint_audit.json`
2. `docs/fase_1_7/mirage_chokepoint_change_proposal.md`
3. `docs/fase_1_7/mirage_uniform_spot_schema.json`
4. `docs/fase_1_7/mirage_profile_schema_migration.md`
5. `docs/fase_1_7/mirage_spot_confidence.json`
6. `docs/fase_1_7/mirage_spot_confidence_report.md`
7. `docs/fase_1_7/jump_gate_instrumentation_spec.md`
8. `docs/fase_1_7/jump_gate_event_schema.json`
9. `docs/fase_1_7/profile_v2_visual_homologation_report.md`
10. `docs/fase_1_7/profile_v2_user_decision_template.md`
11. `docs/fase_1_7/fase_1_7_final_report.md`
12. **Screenshots Reais do CS2 (`docs/fase_1_7/screenshots/`):**
    - `01_ct_a_ticket_passive_first_person.png`
    - `01_ct_a_ticket_passive_external.png`
    - `02_ct_a_firebox_oneanddone_first_person.png`
    - `02_ct_a_firebox_oneanddone_external.png`
    - `03_ct_a_ninja_hide_first_person.png`
    - `03_ct_a_ninja_hide_external.png`
    - `04_ct_mid_window_crouch_first_person.png`
    - `04_ct_mid_window_crouch_external.png`
    - `05_ct_b_van_peek_first_person.png`
    - `05_ct_b_van_peek_external.png`
    - `06_tr_staging_a_ramp_first_person.png`
    - `06_tr_staging_a_ramp_external.png`
    - `07_tr_staging_palace_room_first_person.png`
    - `07_tr_staging_palace_room_external.png`
    - `08_ct_retake_a_connector_first_person.png`
    - `08_ct_retake_a_connector_external.png`

---

## 7. Decisão Técnica Formal

```text
MIRAGE_SEMANTIC_PROFILE_READY_FOR_PHASE_2_PENDING_HUMAN_REVIEW
```

> **Atenção:** Em estrito cumprimento das regras da Fase 1.7, nenhum treinamento de Transformer foi iniciado. A transição para a Fase 2 aguarda a devolução do checklist curto de aprovação visual preenchido pelo usuário.
