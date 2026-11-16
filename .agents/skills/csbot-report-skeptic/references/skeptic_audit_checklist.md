# Checklist de Auditoria Cética Adversarial (`csbot-report-skeptic`)

Este guia define os procedimentos forenses exatos para verificar e tentar refutar relatórios executivos nos 12 vetores obrigatórios de invalidação.

---

## Procedimento Detalhado por Vetor de Falha

### 1. Números Conflitantes
- **Como auditar**: Extraia todos os números citados na prosa executiva (ex: "Acurácia de 84.2% em 12.450 amostras") e compare com:
  1. As tabelas Markdown do próprio relatório;
  2. Os arquivos `canonical_metrics.json`, `reconcile_dataset_counts.json` e `confusion_counts.csv`.
- **Critério de Rejeição**: Qualquer discrepância numérica não explicada por arredondamento explícito documentado (> `1e-4`) invalida o relatório.

### 2. Métricas sem Origem (`01-evidence-before-claims`)
- **Como auditar**: Para cada métrica no relatório, localize na `phase_evidence_matrix.json`:
  - O arquivo bruto de origem;
  - A chave JSON ou coluna CSV exata;
  - O comando reproduzível e a fórmula (`numerador / denominador`).
- **Critério de Rejeição**: Métrica órfã (presente apenas no texto Markdown sem correspondência em artefato bruto no disco).

### 3. Classes sem Suporte (`03-zero-support-is-na`)
- **Como auditar**: Inspecione o vetor de suporte por classe no split avaliado. Para toda classe com `support == 0`:
  - Verifique se `Recall`, `F1-Score` e `Balanced Accuracy` reportam `N/A`;
  - Verifique se a média macro ignora explicitamente as classes `support == 0` documentando quantas classes válidas entraram no denominador (`K_valid / K_total`).
- **Critério de Rejeição**: Presença de `0.0`, `0.0%`, `1.0` ou `100.0%` para classe com zero amostras reais no split.

### 4. Matriz Incompatível
- **Como auditar**:
  - Some todos os elementos de `confusion_counts.csv` e compare com `total_samples` do split em `canonical_metrics.json`.
  - Verifique se a soma de cada linha $i$ em `confusion_counts.csv` é igual a `support[i]`.
  - Em `confusion_normalized.csv`, verifique se linhas com `support[i] > 0` somam `1.0 ± 1e-5` e linhas com `support[i] == 0` contêm exclusivamente `N/A`.
- **Critério de Rejeição**: Divergência de soma ou normalização por coluna apresentada como recall por classe.

### 5. Hashes Divergentes
- **Como auditar**: Calcule via `Get-FileHash -Algorithm SHA256` ou `hashlib.sha256()` o hash real de todos os arquivos listados no relatório.
- **Critério de Rejeição**: Hash com menos de 64 caracteres hexadecimais (ex: `a1b2c3d...`), placeholder (`TODO`, `0000...`) ou hash que não bate com o byte-stream atual do arquivo.

### 6. Relatório Hardcoded
- **Como auditar**: Inspecione os scripts Python/PowerShell que geraram o relatório ou artefato. Procure por:
  - Literais de dicionário com métricas pré-preenchidas;
  - Strings fixas `"Veredito: PASS"` emitidas sem condicional ligada ao resultado real das asserções;
  - Blocos `try/except` que capturam erros e retornam valores padrão de sucesso.
- **Critério de Rejeição**: Qualquer métrica ou veredito emitido por constante literal em vez de computação sobre dados brutos.

### 7. Dados Templados (`04-synthetic-data-labeling`)
- **Como auditar**: Verifique a entropia, variância de timestamps, repetição exata de coordenadas ou ciclos determinísticos artificiais nos dados avaliados.
- **Critério de Rejeição**: Dados gerados por script mock/template ou interpolação classificados como `REAL` ou omitindo a tag `TEMPLATED`/`SIMULATED`/`SYNTHETIC`.

### 8. Arquivos Declarados que Não Existem
- **Como auditar**: Resolva todos os caminhos relativos e absolutos citados no relatório e em `phase_evidence_matrix.json`.
- **Critério de Rejeição**: Arquivo inexistente (`FileNotFoundError`), diretório vazio ou arquivo truncado com `0 bytes`.

### 9. Testes que Não Foram Descobertos
- **Como auditar**: Inspecione o log bruto de execução do `dotnet test` ou `pytest`.
- **Critério de Rejeição**: Saída contendo `0 passed`, `No test is available`, `collected 0 items`, ou filtros que excluíram a suíte relevante enquanto o relatório afirma que os testes passaram.

### 10. Test Usado em Tuning (`02-no-test-contamination`)
- **Como auditar**: Inspecione logs de treinamento, scripts de avaliação e histórico de commits/comandos para verificar se o split `test` foi avaliado múltiplas vezes para ajuste de hiperparâmetros, escolha de época (`best_epoch`), calibração de temperatura ou definição de thresholds.
- **Critério de Rejeição**: Qualquer decisão de modelagem tomada com base em métricas observadas no split `Test`.

### 11. "100%" sem Denominador
- **Como auditar**: Busque todas as ocorrências de `100%`, `100.0%` ou `1.0` no relatório.
- **Critério de Rejeição**: Ausência da fração exata (`N / N`) e da definição da população filtrada (ex: ocultar que 90% das amostras foram descartadas como inválidas antes de calcular "100% nas válidas").

### 12. "Humano" sem Aprovação Humana (`05-human-review-integrity`)
- **Como auditar**: Busque pelos termos `APPROVED_BY_USER`, `REJECTED_BY_USER`, `HUMAN_CAPTURE_IN_GAME`, "validado manualmente em jogo" ou "aprovado pelo usuário".
- **Critério de Rejeição**: Uso desses termos quando a captura ou revisão foi feita por bot, RCON automatizado, replay sintético ou subagente sem intervenção humana explícita.
