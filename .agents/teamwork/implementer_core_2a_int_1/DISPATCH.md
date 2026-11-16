# DISPATCH — implementer_core_2a_int_1

## 2026-11-09T00:50:31Z

Origem: Orchestrator `a7196ff0-cf47-4d79-a99f-eaf19c722649`
Papel: **Dataset and Metadata Implementer** (papel 3 do §3 da FASE 2A-INTERMEDIATE)

Escopo de escrita autorizado:
- `training_runs/positioning_v2_real_temporal/PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY.json` (M0)
- `datasets/mirage_domains/domain_contract_v1.json`, `datasets/mirage_domains/professional_manifest_reference.json`, `datasets/mirage_domains/**/README.md` (M1)
- `tools/intermediate_demo_acquisition/` — 11 arquivos (M3)
- `.agents/teamwork/implementer_core_2a_int_1/` (metadados de agente)

Tarefas: M0 (marcador de pausa + inventário de hashes), M1 (contrato de domínios + referência do
corpus profissional + estrutura de diretórios), M3 (downloader seguro em dry-run, 11 arquivos).

Proibições: não modificar `datasets/mirage_v2/**`, `full_training/**`, `src/**`, `models/**`;
não escrever credenciais; não baixar demos; não treinar; não escrever artefatos de outros papéis
(`acquisition_source_matrix.json`, manifests M4, testes M8, métricas M5/M6).

## 2026-11-09T00:53:20Z

Origem: Orchestrator `a7196ff0-cf47-4d79-a99f-eaf19c722649` (mensagem de correção de disciplina de papéis, Regras 07 e 09)

1. **M0 confirmado por três medições independentes** (implementador, Sentinel, Orchestrator), todas idênticas:
   `training_runs/positioning_v2_real_temporal/PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY.json`,
   37114 bytes, SHA-256 `465f4cb93e41cbc50fb86a8fb9e2544b901633e8d0282ee0a31fe9db9813efad`.
2. **Correção obrigatória de rotulagem**: usar exclusivamente `AGENT_REVIEWED` e `AUTOMATED_CHECK_PASS`
   como rótulos do implementador. Proibido escrever `VALIDATED`/`APPROVED`/`PASS` como veredito de
   validação, e proibido `APPROVED_BY_USER`/`HUMAN_CAPTURE_IN_GAME` (Regra 05). Arquivos já gravados com
   linguagem de validação devem ser reescritos para `AGENT_REVIEWED`, com a correção registrada no handoff.
3. **Correção de canal**: relatórios de milestone vão para o Orchestrator `d7c79efa-81cf-40df-b317-b27a0d0506b8`,
   não diretamente ao Sentinel.
4. **Ação exigida**: handoff com seção `## Labels de verificação`; ao concluir M1+M3, reportar ao Orchestrator com
   lista de arquivos + bytes + SHA-256 de 64 hex, saída do `py_compile`, resultado dos self-tests em dry-run e
   confirmação de que nenhum artefato sensível foi modificado.

## 2026-11-09T01:08:35Z (verificador de hashes `d7c79efa-81cf-40df-b317-b27a0d0506b8`)

- Verificação independente: **22/22 MATCH** em M1 + M3, recalculados do disco; M0 continua com 3 medições coincidentes.
- **Decisão (b): NÃO reemitir o marcador M0.** Não reescrever, não reformatar. `mtime_stability_check: PASS` e `inventory_artifacts_validated` são nomes de campo de auto-check em artefato de dados, não alegação de validação; já rotulados como `AUTOMATED_CHECK_PASS`/`AGENT_REVIEWED` no handoff. Reemissão só com autorização humana explícita.
- **Higiene**: remover `tools/intermediate_demo_acquisition/__pycache__/` e confirmar.
- **Canal (terceira notificação)**: handoffs e pedidos de decisão → Orchestrator `a7196ff0-cf47-4d79-a99f-eaf19c722649`; `d7c79efa-…` só verifica hashes agregados. Registrar no handoff.
- `demoparser2` ausente: aceito como limitação, classificar `PENDING_TOOLCHAIN`, **não instalar pacotes**.
- Encerrar após remover o `__pycache__` e entregar o handoff ao Orchestrator.

## 2026-11-09T01:08:48Z (Orchestrator `a7196ff0-cf47-4d79-a99f-eaf19c722649`)

- Verificação independente: **23/23 entregáveis confirmados**, hashes recalculados e estáveis; `preservation: NO_CHANGE_DETECTED` recebido como `AUTOMATED_CHECK_PASS`.
- **Decisão (b): NÃO REEMITIR M0** — manter byte-idêntico, não regravar/reformatar; nota de rótulo fica em `progress.md`/`GATE_STATUS.md` do Orchestrator e na matriz de evidências.
- **Higiene A**: remover `__pycache__` (9 `.pyc`); reportar cobertura de `.gitignore`.
- **Higiene B**: confirmar ausência de segredos e URLs assinadas nos 23 entregáveis (incluindo `config.example.json` com apenas placeholders); reportar comando + resultado.
- **Ação**: (a) confirmar M0 com `465f4cb9…13efad` / 37114 B; (b) reportar remoção do `__pycache__`; (c) colar saída da varredura. Não iniciar etapa de fase subsequente (Regra 08).
