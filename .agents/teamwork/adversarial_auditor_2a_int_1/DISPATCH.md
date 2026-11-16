# DISPATCH — adversarial_auditor_2a_int_1

## 2026-11-09T01:25:14Z (dispatch inicial, sender=a7196ff0-cf47-4d79-a99f-eaf19c722649)
Sou o **Adversarial Success Auditor** da FASE 2A-INTERMEDIATE (papel 6 do §3). Somente leitura sobre o projeto;
escrita apenas em `.agents/teamwork/adversarial_auditor_2a_int_1/`. Missão: provar ou refutar empiricamente cada
afirmação da fase — recontagem própria de pytest, re-execução do mutation probe, inspeção própria de
`assert True`/skip/`0/0`, prova documental de pré-existência dos 2 erros de coleta, varredura de segredos
autotestada, caça adversarial dos 12 padrões do `csbot-report-skeptic`, verificação de cobertura dos 20 testes
do §20 e avaliação dos Gates C e D. Formato obrigatório de parecer + handoff + mensagem ao Orchestrator
(`d7c79efa-81cf-40df-b317-b27a0d0506b8`).

## 2026-11-09T01:26:41Z (mensagem 2)
Requisitos adicionais: (1) seção `## Isolamento de papel` com `write_scope: OWN_AGENT_DIRECTORY_ONLY`;
(2) recontar enumerações do texto literal do ORIGINAL_REQUEST.md, não ecoar a tabela do Orchestrator;
(3) `tools/intermediate_demo_acquisition/__pycache__/` recriado por importação é `TRANSIENT_CACHE` — não citar
como evidência, não remover; usar `PYTHONPYCACHEPREFIX` em `%TEMP%`; (4) confirmar por conta própria que
`demoparser2` está ausente (`importlib.util.find_spec`) e que o `EVIDENCE_LOSS_EVENT` implica
`REPORT_TO_SOURCE_FIDELITY_UNVERIFIED`, caçando qualquer claim que só se sustente no cache recapturado.

## 2026-11-09T01:27:42Z (mensagem 3)
Evidência obrigatória do mutation probe: (1) comando exato; (2) caminho concreto de `%TEMP%`; (3) contagem de
arquivos em `tools/` e `datasets/` antes/depois com diferença; (4) confirmação de que as violações foram
aplicadas só em cópias temporárias. `<10/10` = FAIL de M8. Exceção: `__pycache__` recriado não conta como
contaminação, mas deve ser declarado separadamente (`.pyc` antes/depois).
