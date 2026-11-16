# Decisão de Homologação em Produção — Perfil Mirage V2 (Fase 1.6.2)

> [!IMPORTANT]
> Este documento atesta a aprovação formal do **Perfil Mirage V2** para inclusão definitiva na baseline de produção e para uso como ground truth no dataset de treinamento do Positioning Transformer V2.

---

## 1. Verificação dos 18 Critérios de Aceitação

### 1. Suíte de Testes C# (274/274)
- **Status:** `APPROVED`
- **Evidência:** Aprovado: 274 testes executados em Release com 0 falhas e 0 ignorados.

### 2. Integridade do MapProfileSha256
- **Status:** `APPROVED`
- **Evidência:** Aprovado: SHA256 `26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1` idêntico na fonte e destino de deploy.

### 3. DeployMatch Verificado
- **Status:** `APPROVED`
- **Evidência:** Aprovado: DllSha256 e MapProfileSha256 idênticos entre workspace e H:\CS2_AI_Server.

### 4. Inspeção Visual dos 8 Spots Mais Sensíveis
- **Status:** `APPROVED`
- **Evidência:** Aprovado: 8/8 spots confirmados via setpos com linha de visada, cover e Z correto (docs/fase_1_6/human_visual_spot_confirmation.md).

### 5. 20 Spots Corrigidos Atingíveis e Coerentes
- **Status:** `APPROVED`
- **Evidência:** Aprovado: Comprovados tanto no teste A/B (!spottest) quanto em gameplay real 5v5.

### 6. Execução Completa da Partida Normal
- **Status:** `APPROVED`
- **Evidência:** Aprovado: 5 rounds oficiais completos (captured_rounds=5, complete_rounds=5, capture_end_reason=MATCH_COMPLETED).

### 7. MLMove V1 ONNX Ativo a 16Hz
- **Status:** `APPROVED`
- **Evidência:** Aprovado: Motor ONNX ativo com latência média de 0.68ms (mlmove_de_mirage.onnx).

### 8. Utility AI IGL Orquestrando Táticas
- **Status:** `APPROVED`
- **Evidência:** Aprovado: Táticas ofensivas e defensivas selecionadas deterministicamente sem fallbacks anômalos.

### 9. Formações CT 2-1-2 Validadas
- **Status:** `APPROVED`
- **Evidência:** Aprovado: Padrão 2-1-2 executado com cobertura de A (Ticket+Jungle), Meio (Janela) e B (Banco+Van).

### 10. Retake e Defuse Executados no Bombsite Real
- **Status:** `APPROVED`
- **Evidência:** Aprovado: Retake coordenado com múltiplos defuses bem-sucedidos nos rounds 1 e 2.

### 11. Compras Econômicas Consistentes
- **Status:** `APPROVED`
- **Evidência:** Aprovado: Sanitização rigorosa no frame zero, rifles em full buy e pistola em eco gamble.

### 12. C4 Sem Mismatches Semânticos
- **Status:** `APPROVED`
- **Evidência:** Aprovado: Zero C4 semantic mismatches, zero drops fora de rota e desarmes legítimos.

### 13. Jump Gate Sem Bunny Hop
- **Status:** `APPROVED`
- **Evidência:** Aprovado: Saltos aéreos e fora de contexto suprimidos, 0% de bunny hop executado.

### 14. Recovery Sem Loops Infinitos
- **Status:** `APPROVED`
- **Evidência:** Aprovado: 35 recuperações resolvidas fluidamente com 0 geometry blocks e 0 stucks permanentes.

### 15. Trade Spacing e Adaptações Operantes
- **Status:** `APPROVED`
- **Evidência:** Aprovado: Repulsão mútua >140u ativa e rejeição de falsos positivos de site clear.

### 16. Telemetria Completa Gravada
- **Status:** `APPROVED`
- **Evidência:** Aprovado: 2.288 eventos em profile_v2_normal_match_events.jsonl com todos os 22 campos obrigatórios.

### 17. Auditoria de APIs Restauradas
- **Status:** `APPROVED`
- **Evidência:** Aprovado: Todos os 18 membros auditados e comprovados como seguros sem pipelines concorrentes.

### 18. Estabilidade do Servidor
- **Status:** `APPROVED`
- **Evidência:** Aprovado: Zero crashes, zero memory leaks e encerramento limpo via flag.

---

## 2. Decisões Formais Emitidas

### `MIRAGE_PROFILE_READY_FOR_V2_DATASET`
**Status:** `HOMOLOGADO E APROVADO`
- O arquivo `src/CsBotManager/MapProfiles/de_mirage.json` versão 2 (SHA-256: `26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1`) é declarado como **Ground Truth Oficial** para o mapa de_mirage.
- O pipeline de geração de dataset para o **Positioning Transformer V2** está formalmente liberado para usar este perfil na rotulação e supervisão de âncoras, rotadores e lurkers.

### `MIRAGE_PROFILE_V2_READY_FOR_PRODUCTION`
**Status:** `HOMOLOGADO E APROVADO`
- O perfil V2 foi validado em condições reais de gameplay contra bots com MLMove ativo, sem regressões de navegação, sem quedas através do mapa, e com melhora nítida nas linhas de tiro e posicionamento tático dos defensores.
- A DLL do CsBotManager (versão 1.3.0) e o perfil V2 estão prontos e aprovados para operação em produção.

---

## 3. Próximos Passos (Transição para Fase 2)
1. **Catalogação das 444 Demos Mirage**: Início da extração de features espaciais utilizando os medoids aprovados.
2. **Implementação do Dataset Builder V2**: Rotulação dos tokens de posição utilizando os TacticalSpots V2 como vocabulário de tokens de ancoragem.
3. **Treinamento do Positioning Transformer**: Arquitetura decoder-only autoregressiva para predição da próxima melhor posição tática da equipe.
