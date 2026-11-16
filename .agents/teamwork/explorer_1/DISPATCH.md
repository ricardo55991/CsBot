# Dispatch Task for Explorer 1

**Context**: Milestone 1 - Governance Exploration & Inventory for Patch 1.1 (R1 & R5)
**Role**: Explorer / Codebase Investigator (Read-only)
**Working Directory**: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\explorer_1
**Authoritative Request**: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\ORIGINAL_REQUEST.md

## Objectives
1. Investigate all existing governance files, scripts, hooks, and linters in the workspace:
   - Check `.agents/hooks/`, `tools/`, `scripts/`, `tests/`
   - Locate and analyze `post_test_audit.py`, regex SHA-256 checks, table parsers, and demo catalog cross-references.
   - Analyze `false_positives.json`, `missed_violations.json`, `governance_red_team_report.md`, `hooks_test_report.md`.
2. Locate the specification/proposal for the skill `csbot-math-logic-auditor` across existing reports, docs, and skills.
3. For each of the items in R1:
   - FP-01: SHA-256 regex boundaries (64 hex chars full, reject 4-63 or truncated with ..., ignore code fences). Identify which files perform SHA-256 regex checks.
   - FP-02: `post_test_audit.py` handling of `toolResponse`, `tool_response`, `stdout`, `stderr`, `exitCode`, `exit_code` for `dotnet test`, `pytest`, `unittest`, unknown status when counts missing, prevent PASS on failure exit code.
   - FP-03: Structural distinction in linters between EXECUTIVE_CLAIM, DOCUMENTATION_EXAMPLE, ADVERSARIAL_FIXTURE in fenced code blocks. Identify which linters check executive claims.
   - MISS-S1-02: Markdown table parser for Support=0 rejecting numeric metrics (allowing only N/A or -). Identify where table checks happen.
   - MISS-S4-01: Demo ID pattern detection and cross-reference with formal demo catalog in repo. Locate formal demo catalog and current demo checks.
   - MISS-S3-01: Separation of concerns between Hook (format/relative path) and Phase Gate/Provenance (deterministic SHA-256 hash recalculation against disk).
4. Produce a detailed investigation report at `.agents/teamwork/explorer_1/analysis.md` and a clean `handoff.md`.
Do NOT modify any code. Read-only exploration.


## 2026-11-07T20:52:14Z
Você é o Explorer 1 (Codebase Investigator) na equipe Tier 3 do projeto CsBot.
Seu diretório de trabalho exclusivo é: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\explorer_1
A requisição original imutável do usuário está em: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\ORIGINAL_REQUEST.md
Suas instruções detalhadas de tarefas estão em: c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\explorer_1\DISPATCH.md

Objetivos essenciais (Modo estritamente somente-leitura, não modifique código):
1. Investigar a implementação atual de governança em `.agents/hooks/`, `tools/`, `scripts/`, `tests/` e arquivos na raiz como `hooks_config.json`, `false_positives.json`, `missed_violations.json`, `governance_red_team_report.md`.
2. Para cada item do Requisito R1:
   - FP-01: Identificar onde a regex de SHA-256 está definida (ex: hooks, linters, pre-commit) e como ajustá-la com boundaries `\b[0-9a-fA-F]{64}\b`, rejeitando 4 a 63 chars ou reticências, e pulando code fences.
   - FP-02: Analisar `tools/post_test_audit.py` (ou onde estiver), inspecionar como processa saídas de `dotnet test`, `pytest`, `unittest`, tratamento de campos camelCase/snakeCase (`toolResponse`, `tool_response`, `stdout`, `stderr`, `exitCode`, `exit_code`), geração de `UNKNOWN` quando sem contagem, e bloqueio de `PASS` em caso de exit code != 0.
   - FP-03: Localizar linters que auditam claims executivas e como estruturar a diferenciação entre `EXECUTIVE_CLAIM`, `DOCUMENTATION_EXAMPLE` e `ADVERSARIAL_FIXTURE` em fenced code blocks.
   - MISS-S1-02: Localizar onde tabelas Markdown são validadas e como implementar parser estrutural para coluna `Support` e colunas de métricas, garantindo que `Support = 0` exija `N/A` ou `-` e rejeite números.
   - MISS-S4-01: Localizar o catálogo formal de demos no repositório (ex: `datasets/`, `docs/`, `catalogs/`) e onde é feita a validação de IDs de demos para exigir cross-check com o catálogo, emitindo `UNPROVENANCED_TEMPLATE_ID` se inexistente fora de fixtures/docs.
   - MISS-S3-01: Mapear a separação de responsabilidades entre Hook e Phase Gate/Provenance Skill.
3. Localizar nos relatórios e documentação existentes a especificação técnica formal da skill `csbot-math-logic-auditor` (proposta ou homologada) para guiar o Implementer na sua disponibilização (R5).
4. Gerar relatório detalhado de análise em:
   `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\explorer_1\analysis.md`
   e relatório de handoff em:
   `c:\Users\ricar\OneDrive\Documentos\Dev\CsBot\.agents\teamwork\explorer_1\handoff.md`
