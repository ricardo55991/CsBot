# Regra 16: Saídas Cirúrgicas no Terminal (`16-surgical-terminal-output`)

**Política Operacional:** `SURGICAL_TERMINAL_OUTPUT`

**Comandos executados no terminal devem emitir respostas cirúrgicas e compactas, evitando poluição de contexto e consumo desnecessário de tokens.**

---

## 1. Padrões Obrigatórios de Comando
- **Listagens de Diretórios:** Utilizar contagens `($items.Count)` ou filtros cirúrgicos `Select-Object -First N` em vez de listagens recursivas completas.
- **Dumps de Testes:** Executar com filtros de classe ou módulo, redirecionando logs extensos para disco quando necessário.
- **Estrutura de Retorno:** Quando um script ou comando precisa emitir status, fornecer:
  * `exit_code`
  * `status` (PASS/FAIL)
  * `summary` conciso
  * `log_path` relativo ao repositório

É proibido despejar logs brutos com mais de 50 linhas diretamente na saída do terminal sem necessidade estrita de depuração imediata.
