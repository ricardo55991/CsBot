# Regra 15: Analytics Script First (`15-analytics-script-first`)

**Política Operacional:** `ANALYTICS_SCRIPT_FIRST`

**Para qualquer análise estatística, contagem, reconciliação ou validação volumosa de dados, é obrigatório utilizar scripts determinísticos locais em vez de despejar dados brutos na janela de contexto.**

---

## 1. Escopo de Aplicação
Aplica-se sempre que a tarefa envolver:
- JSONs grandes (> 100 linhas);
- Shards e arquivos Parquet;
- Dumps e arrays NPZ;
- Manifests e inventários de datasets;
- Verificação em lote de hashes SHA-256;
- Contagens de classes, distribuições e matrizes de confusão;
- Reconciliação cruzada de splits.

---

## 2. Padrão de Execução
1. O agente escreve ou executa um script Python determinístico local;
2. O script processa os arquivos físicos diretamente no disco;
3. O script valida schemas e grava os relatórios detalhados em arquivos JSON em disco;
4. O script imprime no terminal (stdout) exclusivamente um resumo curto (3 a 5 linhas).

Formato padrão de saída no terminal:
```json
{
  "status": "PASS",
  "records_processed": 3411434,
  "violations": 0,
  "detailed_report": "relative/path/audit.json"
}
```

É terminantemente proibido carregar arquivos de dados volumosos via `read_file` para a LLM fazer cálculos cognitivos ou contagens de linhas.
