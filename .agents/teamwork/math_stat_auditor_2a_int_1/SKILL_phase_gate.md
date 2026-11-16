---
name: csbot-phase-gate
description: Controla a entrada, execução e encerramento formal de fases do projeto CsBot, gerando snapshots de entrada, matrizes de requisitos/evidências e emitindo veredito canônico (PASS, CONDITIONAL ou FAIL). Use sempre ao iniciar, auditar ou encerrar qualquer fase, subfase, retreinamento ou entrega de engenharia no CsBot.
---

# CsBot Phase Gate

Esta Skill governa o ciclo de vida de qualquer fase ou entrega técnica do projeto CsBot, garantindo conformidade estrita com as 8 diretrizes inegociáveis do `AGENTS.md` (`01-evidence-before-claims` até `08-no-automatic-phase-advance`).

## Artefatos Obrigatórios da Fase

Toda execução de gate produz e valida os quatro artefatos abaixo em `--output-dir`:

1. `phase_input_snapshot.json`: Estado inicial, hashes SHA-256 de artefatos sensíveis de entrada, branch/commit Git e escopo autorizado.
2. `phase_requirement_matrix.md`: Lista rastreável de requisitos técnicos, invariantes metodológicas e critérios de aceite da fase.
3. `phase_evidence_matrix.json`: Mapeamento estrito entre cada requisito e seu artefato bruto verificável (`path`, `sha256`, `command`, `formula`, `data_nature`).
4. `phase_gate_report.md`: Relatório de fechamento contendo auditoria de regras, parecer independente e veredito formal.

Consulte o contrato completo de schemas e regras de bloqueio em [phase_gate_contract.md](./references/phase_gate_contract.md).

## Procedimento Operacional Passo a Passo

### 1. Gate de Entrada (Pre-Flight)
1. Identifique todos os artefatos sensíveis (`*.onnx`, `*.pt`, `MapProfiles/*.json`, `*split*`, `*manifest*`, `*catalog*`, `*contract*`) que serão lidos ou modificados.
2. Registre os hashes SHA-256 originais (64 hex chars), crie backups imutáveis e documente o plano de rollback conforme `06-sensitive-artifact-protection`.

### 2. Rastreabilidade e Governança na Execução
1. Para cada métrica ou afirmação, capture o artefato bruto, o comando exato e a fórmula explícita (`01-evidence-before-claims`).
2. Verifique a ausência de uso do conjunto `Test` em decisões de tuning, arquitetura ou threshold (`02-no-test-contamination`).
3. Garanta que classes com `support = 0` sejam reportadas exclusivamente como `N/A` (`03-zero-support-is-na`).
4. Classifique a natureza de cada dado como `REAL`, `SIMULATED`, `TEMPLATED`, `SYNTHETIC` ou `INFERRED` (`04-synthetic-data-labeling`).
5. Preserve os selos `APPROVED_BY_USER`, `REJECTED_BY_USER` e `HUMAN_CAPTURE_IN_GAME` exclusivamente para ações humanas reais (`05-human-review-integrity`).

### 3. Validação Independente e Execução do Gate
Submeta os artefatos à validação independente (`07-independent-validation`) e execute [run_phase_gate.py](./scripts/run_phase_gate.py) com os argumentos canônicos:

```powershell
python .agents/skills/csbot-phase-gate/scripts/run_phase_gate.py `
  --phase-id PHASE-2A `
  --workspace-root . `
  --input-files src/CsBotManager/MapProfiles/de_mirage.json `
  --requirements-json artifacts/phase_requirements.json `
  --evidences-json artifacts/phase_evidences.json `
  --output-dir artifacts/phase_gate `
  --strict
```

- **Regra de `--dry-run`**: A execução com `--dry-run` realiza autodiagnóstico não-destrutivo e emite veredito máximo **`CONDITIONAL`** com `data_nature: SIMULATED` (em respeito à Regra `01-evidence-before-claims`, pois `PASS` exige execução real sobre artefatos brutos verificáveis).

### 4. Emissão de Veredito e Parada Obrigatória
1. Vereditos permitidos em `phase_gate_report.md`: `PASS`, `CONDITIONAL` ou `FAIL`.
2. **Pare imediatamente** após emitir o veredito (`08-no-automatic-phase-advance`) e aguarde autorização explícita do usuário humano.
