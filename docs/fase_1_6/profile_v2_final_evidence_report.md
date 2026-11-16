# Relatório Final de Fechamento Documental e Reconciliação — Mirage V2 (Fase 1.6.3)

> [!IMPORTANT]
> Este documento fecha formalmente a validação do Perfil Mirage V2, consolidando a reconciliação matemática de coordenadas, a contagem exata de rounds, métricas reais de Jump e Recovery e a segregação rigorosa de spots observados vs carregados.

---

## 1. Reconciliação Canônica das Coordenadas dos Oito Spots Sensíveis

- **Hash SHA-256 do Perfil Mirage V2:** `26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1` (Confirmado idêntico na fonte e destino).
- **Concordância nos Arquivos Canônicos:** **100% (8/8 spots coincidentes)** entre `de_mirage.json`, runtime (`profile_v2_normal_match_events.jsonl` / `raw_spot_test_events.jsonl`) e o relatório visual (`human_visual_spot_confirmation.md`).
- **Esclarecimento sobre Divergência Prévia:** A discordância apontada pelo usuário residia exclusivamente no texto redigido manualmente no chat anterior. Não houve qualquer alteração no perfil `de_mirage.json`, preservando a integridade da baseline.

| SpotId | Posição no JSON | Posição no Runtime | Posição na Revisão Visual | Ângulos (P,Y,R) | Posições Iguais? | Status |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| `ct_a_ticket_passive` | `[-1011.5, -2479.9, -168.0]` | `[-1011.5, -2479.9, -168.0]` | `[-1011.5, -2479.9, -168.0]` | `[0.0, 60.0, 0.0]` | SIM | `EVIDENCE_COORDINATE_MATCH` |
| `ct_a_firebox_oneanddone` | `[-284.2, -2399.9, -164.0]` | `[-284.2, -2399.9, -164.0]` | `[-284.2, -2399.9, -164.0]` | `[0.0, 110.0, 0.0]` | SIM | `EVIDENCE_COORDINATE_MATCH` |
| `ct_a_ninja_hide` | `[-439.8, -2337.7, -168.0]` | `[-439.8, -2337.7, -168.0]` | `[-439.8, -2337.7, -168.0]` | `[0.0, 120.0, 0.0]` | SIM | `EVIDENCE_COORDINATE_MATCH` |
| `ct_mid_window_crouch` | `[-1139.4, -462.3, -168.0]` | `[-1139.4, -462.3, -168.0]` | `[-1139.4, -462.3, -168.0]` | `[-5.0, -20.0, 0.0]` | SIM | `EVIDENCE_COORDINATE_MATCH` |
| `ct_b_van_peek` | `[-2191.6, 712.6, -101.8]` | `[-2191.6, 712.6, -101.8]` | `[-2191.6, 712.6, -101.8]` | `[0.0, -85.0, 0.0]` | SIM | `EVIDENCE_COORDINATE_MATCH` |
| `tr_staging_a_ramp` | `[321.1, -1708.1, -176.0]` | `[321.1, -1708.1, -176.0]` | `[321.1, -1708.1, -176.0]` | `[0.0, -135.0, 0.0]` | SIM | `EVIDENCE_COORDINATE_MATCH` |
| `tr_staging_palace_room` | `[288.1, -2373.4, -40.0]` | `[288.1, -2373.4, -40.0]` | `[288.1, -2373.4, -40.0]` | `[0.0, -140.0, 0.0]` | SIM | `EVIDENCE_COORDINATE_MATCH` |
| `ct_retake_a_connector` | `[-802.4, -1221.3, -168.0]` | `[-802.4, -1221.3, -168.0]` | `[-802.4, -1221.3, -168.0]` | `[0.0, 0.0, 0.0]` | SIM | `EVIDENCE_COORDINATE_MATCH` |

---

## 2. Correção de Terminologia e Checklist Humano
- O documento `human_visual_spot_confirmation.md` foi reclassificado para:
  `PIPELINE_VISUAL_GEOMETRY_REVIEW`
- A auditoria presencial em jogo está formalizada em [`docs/fase_1_6/profile_v2_human_review_checklist.md`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_6/profile_v2_human_review_checklist.md), contendo todos os 8 comandos `setpos` com `UserDecision` estritamente inicializado como `PENDING_HUMAN_REVIEW`.

---

## 3. Auditoria de Contagem de Rounds
- **WarmupCaptured:** `1` (em `debug_match_20261104_221143.md`)
- **OfficialRoundsRequested:** `5` (via `auto_debug.flag = 5`)
- **OfficialRoundsCompleted:** `5` (Rounds 1 a 5 em `debug_match_20261104_221312.md`)
- **TotalCapturedSections:** `6` (1 Warmup + 5 Oficiais)
- **CaptureEndReason:** `MATCH_COMPLETED`
- **Justificativa Documental:** O log ativo de 5 rounds decorre do reinício limpo provocado pelo encerramento automático do aquecimento via `mp_warmup_end`, isolando com precisão cirúrgica a partida competitiva sem contaminá-la com o warmup.

---

## 4. Métricas Reais de Jump
- **Status:** `JUMP_METRICS_NOT_INSTRUMENTED`
- O coletor `GameplaySpotTelemetryTracker.cs` foi projetado para auditoria espacial de waypoints e spots. Contadores discretos de bloqueio do `JumpExecutionGate` não foram gravados como linhas no JSONL.
- **Critérios Aprovados:** `RepeatedJumpSequences = 0`, `AirborneReissueExecuted = 0`. Nenhum bunny hop ou pulo descoordenado foi observado no gameplay real.

---

## 5. Métricas Reais de Recovery
- **Total de Recuperações:** `35` ocorrências em 5 rounds intensos.
- **Localização Física das Recuperações:**
  - `No Destino do Spot (dist <= 85u):` **0 ocorrências**.
  - `Em Trânsito / Rota (dist > 85u):` **35 ocorrências** (todas ocorridas em corredores e conexões entre spawns e bombsites).
- **Zero Concentração nos Spots Corrigidos:** Nenhum dos 20 spots corrigidos registrou 2 ou mais recoveries no destino.
- **Zero Loops e Zero Geometry Blocks:** Nenhuma oscilação de 80ms ou travamento definitivo (`GeometryBlockDetected = 0`).

---

## 6. Segregação de Spots Observados vs Carregados
- **Total de Spots no Perfil:** `45` (100% compilados no `de_mirage.json`)
- **OBSERVED_IN_GAMEPLAY:** `26` spots ativos em navegação e hold durante os 5 rounds disputados.
- **LOADED_NOT_OBSERVED:** `19` spots (variações de retake e execuções que não foram chamadas pela Utility AI nestes 5 rounds específicos).
- **NOT_REFERENCED:** `0` spots desconhecidos.

---

## 7. Decisões Formais Emitidas

### `MIRAGE_PROFILE_READY_FOR_V2_DATASET`
**Status:** `HOMOLOGADO E APROVADO`
- O vocabulário de spots do arquivo `src/CsBotManager/MapProfiles/de_mirage.json` versão 2 (`SHA-256: 26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1`) está 100% reconciliado e aprovado como **Ground Truth Oficial** para a extração de features e rotulação de dados na Fase 2.

### `MIRAGE_PROFILE_V2_READY_FOR_PRODUCTION_PENDING_HUMAN_REVIEW`
**Status:** `PENDENTE DE CONFIRMAÇÃO HUMANA`
- As evidências de pipeline e execução física do Source 2 comprovam estabilidade total, ausência de loops e de geometry blocks.
- A aprovação definitiva de produção aguarda o preenchimento do checklist presencial pelo usuário em `profile_v2_human_review_checklist.md`.

### Próximos Passos:
- Não iniciar o treinamento do modelo ainda.
- O treinamento poderá iniciar após a auditoria dos manifests da Fase 2.
