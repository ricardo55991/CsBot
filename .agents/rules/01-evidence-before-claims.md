# Regra 01: Evidence Before Claims (`01-evidence-before-claims`)

Nenhuma conclusão `PASS` pode ser emitida sem a apresentação explícita de:
- **Artefato bruto materializado** gerado pela execução real (o arquivo DEVE existir no disco com tamanho > 0 bytes e ser carregável);
- **Caminho do artefato**: em relatórios versionados/documentos canônicos, os caminhos devem ser estritamente relativos à raiz do repositório (ex: `tools/...`, `src/...`, `reports/...`). Caminhos absolutos são permitidos apenas em logs temporários/locais de execução não publicados;
- **Hash SHA-256 completo** (exatamente 64 caracteres hexadecimais, sem truncamento, conferido em tempo de execução diretamente no disco);
- **Comando reproduzível** exato executado no terminal;
- **Fórmula de agregação** explícita com numerador e denominador explícitos `(N/D)` para qualquer percentual ou proporção;
- **Classificação de natureza do dado**: `REAL`, `SIMULATED`, `TEMPLATED`, `SYNTHETIC` ou `INFERRED`.

> **Regras de Bloqueio**:
> 1. Relatório executivo em Markdown ou PDF nunca é evidência suficiente por si só. Toda afirmação deve apontar para o artefato bruto verificável que a sustenta.
> 2. Relatórios com tabelas hardcoded sem script gerador e artefato `.json` de telemetria equivalente são sumariamente rejeitados como `FAIL`.
> 3. Datasets ou splits apenas planejados ou declarados sem arquivos físicos `.parquet`/`.npz` materializados no disco não podem compor manifests nem relatórios de prontidão.
