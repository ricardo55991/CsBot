# Relatório de Testes: Governança CsBot 1.2 Lean (`governance_1_2_lean_test_report.md`)

**Data:** 2026-11-09  
**Executor:** Agente Principal (Single-Agent First)  
**Suíte Executada:** `tests/test_governance_1_2_lean.py`  
**Resultado Global:** `PASS (30/30 testes aprovados, 100.00%)`  
**Tempo de Execução:** `0.18s`  
**Comando:** `pytest tests/test_governance_1_2_lean.py -v`

---

## 1. Tabela Detalhada de Execução dos 30 Gates

| ID | Nome do Teste | Invariante / Regra Verificada | Veredito |
|---|---|---|---|
| 01 | `test_01_DocumentationTaskCreatesZeroSubagents` | Documentação opera sob Tier 1 com 0 subagentes | **PASS** |
| 02 | `test_02_NestedSubagentIsBlocked` | Regra 11 proíbe subsubagentes (`NESTED_SUBAGENT_BLOCKED`) | **PASS** |
| 03 | `test_03_OnlyMainAgentCanDelegate` | Apenas o agente principal tem autoridade para delegar | **PASS** |
| 04 | `test_04_Tier1AllowsZeroSubagents` | Tier 1 fixa limite máximo de 0 subagentes | **PASS** |
| 05 | `test_05_Tier2AllowsAtMostOneSubagent` | Tier 2 fixa limite máximo de 1 subagente | **PASS** |
| 06 | `test_06_Tier3AllowsAtMostTwoSubagents` | Tier 3 fixa limite máximo de 2 subagentes | **PASS** |
| 07 | `test_07_Tier4AllowsAtMostFourSubagents` | Tier 4 fixa limite máximo de 4 subagentes | **PASS** |
| 08 | `test_08_DelegationRequiresJustification` | Toda delegação exige justificativa formal documentada | **PASS** |
| 09 | `test_09_OverlappingRolesAreRejected` | Papéis duplicados e sobrepostos são terminantemente rejeitados | **PASS** |
| 10 | `test_10_EvidencePacketRespectsLimits` | Evidence Packet v1 impõe <= 8 artefatos e <= 3 leituras | **PASS** |
| 11 | `test_11_UnchangedHashReusesDigest` | Hash inalterado reutiliza digest em cache sem ler bytes | **PASS** |
| 12 | `test_12_ChangedHashInvalidatesDigest` | Alteração de hash invalida o cache antigo imediatamente | **PASS** |
| 13 | `test_13_FullReadRequiresJustification` | Regra 12 proíbe leituras redundantes sem justificativa | **PASS** |
| 14 | `test_14_MarkdownChangeDoesNotRunDotnetTests` | Alterações de Markdown proíbem `dotnet test` e build C# | **PASS** |
| 15 | `test_15_PythonChangeRunsSpecificTest` | Script Python isolado exige apenas `py_compile` e teste alvo | **PASS** |
| 16 | `test_16_CSharpChangeRunsFilteredTests` | Código C# localizado roda apenas testes com filtro | **PASS** |
| 17 | `test_17_SharedContractRequiresExpandedTests` | Contrato compartilhado roda testes dos consumidores diretos | **PASS** |
| 18 | `test_18_DeltaFixDoesNotRepeatFullRedTeam` | Correções localizadas não repetem auditorias integrais | **PASS** |
| 19 | `test_19_WarningDoesNotStartRewriteLoop` | Orçamento de warnings impede loops recursivos de reescrita | **PASS** |
| 20 | `test_20_CriticalViolationStillBlocks` | Violações críticas reais mantêm bloqueio inegociável | **PASS** |
| 21 | `test_21_AuditOnlyHookDoesNotBlockWarning` | `validate-generated-report` opera em audit-only para estilo | **PASS** |
| 22 | `test_22_TestContaminationStillBlocks` | `pre-training-gate` bloqueia contaminação do Test set | **PASS** |
| 23 | `test_23_SecretLeakageStillBlocks` | `secret-leakage-gate` bloqueia vazamento de credenciais | **PASS** |
| 24 | `test_24_PassWithoutEvidenceStillBlocks` | `stop-condition-evidence-gate` bloqueia PASS sem artefato | **PASS** |
| 25 | `test_25_KillAllRunsOnCompletion` | Regra 10 exige encerramento de tarefas idle via `kill_all` | **PASS** |
| 26 | `test_26_ReportingMatchesRiskTier` | Relatórios permitidos estritamente alinhados ao Tier | **PASS** |
| 27 | `test_27_TeamworkIsNotDefault` | Modo Teamwork desativado por padrão (sob demanda apenas) | **PASS** |
| 28 | `test_28_GraphifyReusesExistingGraph` | Graphify opera por delta e reutiliza o grafo existente | **PASS** |
| 29 | `test_29_ExecutionEfficiencyIsRecorded` | Telemetria de eficiência registrada em `execution_efficiency.json` | **PASS** |
| 30 | `test_30_ProductDirectoriesRemainUnchanged` | Zero arquivos de produto em `src/`, `datasets/` ou `models/` alterados | **PASS** |

---

## 2. Compilação de Código Python da Governança

Comando: `python -m py_compile .agents/hooks/common_hook_utils.py .agents/hooks/update_artifact_digest.py tests/test_governance_1_2_lean.py`  
Status: **Código compilado com sucesso (Exit code 0, 0 erros sintáticos)**.
