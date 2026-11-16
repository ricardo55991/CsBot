# Relatório de Testes de Falsos Positivos dos Hooks (`hooks_false_positive_report.md`)

- **Data de Geração**: `2026-11-07`
- **Artefato Bruto de Resultados**: [hooks_test_results.json](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/.agents/audit/hooks_test_results.json) (SHA-256: `71ecf5676b622090145ad4acd88b9271f9adadfc93a27929bc457e5fafa7e583`)
- **Classificação de Natureza dos Dados**:
  - Execução de processos, tempos e decisões dos hooks: `REAL`
  - Payloads de entrada via `stdin`: `SIMULATED`
- **Status de Revisão**: `AGENT_REVIEWED` (`False-Positive Tester`)
- **Fórmula de Agregação**:
  $$\text{Taxa de Falsos Positivos} = \frac{\text{Operações Legítimas Indevidamente Bloqueadas}}{\text{Total de Operações Legítimas Testadas}} = \frac{0}{8} = 0.0\%$$

---

## 1. Matriz de Cenários de Operações Legítimas (Modo `blocking` Ativo)

Para garantir que os 5 hooks em modo `blocking` não atrapalhem o fluxo diário de engenharia, leitura de arquivos, cálculo de hashes, execução de testes unitários ou documentação comum, foram executados os 8 cenários de falso positivo abaixo:

| ID | Operação Legítima Testada | Hook(s) Acionado(s) | Risco de Falso Positivo Mitigado | Resposta Real no `stdout` | Duração (`ms`) | Falsos Positivos |
|---|---|---|---|---|---:|---:|
| `FP01` | `Get-FileHash models/model.onnx -Algorithm SHA256` | `protect-sensitive-files` | Comando menciona arquivo `.onnx`, mas é estritamente de leitura de hash. | `{"decision": "allow", "reason": "Operação de leitura ou dry-run permitida."}` | `121.44` | `0` |
| `FP02` | `Get-Content src/CsBotManager/MapProfiles/de_mirage.json` | `protect-sensitive-files` | Comando menciona `de_mirage.json`, mas não realiza escrita/redirecionamento. | `{"decision": "allow", "reason": "Operação de leitura ou dry-run permitida."}` | `120.24` | `0` |
| `FP03` | `pytest tests/test_phase3a_positioning_training.py -v` | `pre-training-gate` | Nome do arquivo de teste contém a substring `training`, mas o executável é `pytest`. | `{"decision": "allow", "reason": "Comando não inicia execução de treinamento de modelo."}` | `123.81` | `0` |
| `FP04` | `python train_positioning.py --dry-run` | `pre-training-gate` | Script de treino invocado apenas com flag `--dry-run` para autodiagnóstico. | `{"decision": "allow", "reason": "Comando não inicia execução de treinamento de modelo."}` | `122.69` | `0` |
| `FP05` | `python train_positioning.py --epochs 30` (com `input_snapshot.json` completo e `split_leakage=0`) | `pre-training-gate` | Treinamento real devidamente autorizado com todos os pré-requisitos cumpridos. | `{"decision": "allow", "reason": "Pre-training gate aprovado: input_snapshot.json íntegro, split_leakage=0, hashes SHA-256 válidos e Test set isolado."}` | `124.73` | `0` |
| `FP06` | `git status --short` | `protect-sensitive-files`, `pre-training-gate`, `post-test-audit` | Comando frequente de inspeção Git passando por todos os hooks de `run_command`. | `allow` / `allow` / `{}` | `367.51` | `0` |
| `FP07` | Escrita em arquivo markdown comum (`SIMULATED`) sem semântica de relatório executivo de fase | `validate-generated-report` | Arquivo `.md` comum que não declara veredito de fase nem métricas de avaliação. | `{"decision": "allow", "reason": "Operação não envolve geração de relatório executivo ou de avaliação."}` | `125.43` | `0` |
| `FP08` | `dotnet test CsBot.sln --no-build` (`340/340` aprovados) seguido de `Stop` com `deliverable_evidence.json` válido | `post-test-audit` + `stop-condition-evidence-gate` | Ciclo completo de testes verdes seguido de encerramento legítimo da tarefa. | `post_test`: `{}` (`340/340`)<br>`stop_gate`: `{"decision": "allow", "reason": "Stop condition evidence gate aprovado..."}` | `246.46` | `0` |

---

## 2. Teste de Stress Multi-Violação (`EXT09`)

Além dos 8 testes de falso positivo, foi executado o cenário `EXT09` (`SIMULATED`) submetendo um relatório corrompido contendo simultaneamente 8 violações distintas (classe sem suporte com métrica numérica, `340340` concatenado, identificadores `TEMPLATED`, classe inexistente no contrato, hash truncado, contaminação de tuning, percentual cheio sem razão `8/8` e selo humano indevido). O hook `validate-generated-report` detectou todas as 8 violações (`8/8`) em `128.27 ms` e bloqueou a operação com `"decision": "deny"`.
