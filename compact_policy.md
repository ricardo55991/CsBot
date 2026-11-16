# Política Operacional de Compactação de Contexto (`compact_policy.md`)

**Versão da Governança:** `1.2.0-lean`  
**Escopo:** Uso seguro, econômico e determinístico do comando `/compact` no Antigravity  
**Data:** 2026-11-09

---

## 1. Objetivo

O comando `/compact` é a ferramenta primordial para prevenir a degradação de performance e a explosão de custos de tokens em sessões de desenvolvimento prolongadas. No entanto, sua execução prematura ou em momentos incorretos pode descartar informações transitórias cruciais.
Esta política regulamenta os momentos exatos em que a compactação é autorizada e os momentos em que é expressamente proibida.

---

## 2. Condições Autorizadas para Uso de `/compact`

O uso de `/compact` é autorizado **exclusivamente** quando TODAS as seguintes condições forem satisfeitas:
1. O marco, fase ou tarefa corrente foi formalmente encerrada ou pausada com marcador canônico no disco;
2. Todas as decisões técnicas e arquiteturais foram devidamente persistidas em arquivos versionados;
3. Hashes SHA-256 e inventários de artefatos foram gravados em `deliverable_evidence.json` ou equivalente;
4. Bloqueadores e impedimentos foram documentados em arquivo JSON/Markdown em disco;
5. Próximos passos e backlog de entrada da fase subsequente foram formalizados;
6. O pool de subagentes está completamente limpo (`active_subagents = 0`);
7. Não há nenhuma background task em execução (`background_tasks = 0`).

---

## 3. Momentos de Proibição Estrita (Quando NÃO Usar `/compact`)

É terminantemente proibido disparar `/compact`:
- Durante a execução ativa de treinamentos PyTorch ou pipelines de dados;
- Durante downloads de datasets ou demos em andamento;
- Durante sessões ativas de Teamwork com subagentes em execução;
- No meio de uma investigação forense ou depuração de bug antes de registrar o log da causa raiz;
- Antes de persistir em disco uma decisão tomada na conversa;
- Enquanto houver processos rodando em segundo plano (`manage_task list > 0`);
- Com modificações sensíveis não salvas ou sem backup registrado.

---

## 4. Checklist Pré-Compactação Obrigatório

Antes de disparar `/compact`, o operador ou agente deve verificar a seguinte matriz:

| Item de Verificação | Critério | Status Exigido |
|---|---|---|
| `phase_status_saved` | Status canônico persistido em relatório de fase | **SIM** |
| `canonical_verdict_saved` | Veredito (`PASS`, `CONDITIONAL` ou `PAUSED`) gravado em disco | **SIM** |
| `hashes_saved` | Hashes SHA-256 brutos persistidos em `deliverable_evidence.json` | **SIM** |
| `blockers_saved` | Impedimentos registrados formalmente em disco | **SIM** |
| `next_step_saved` | Escopo da próxima etapa registrado no repositório | **SIM** |
| `active_subagents_zero` | `manage_subagents(Action="list") == []` | **SIM** |
| `background_tasks_zero` | `manage_task(Action="list") == []` | **SIM** |
| `uncommitted_sensitive_changes` | Modificações em contratos/modelos autorizadas e respaldadas | **SIM** |

Se qualquer item acima for **NÃO**, resolva-o e grave os arquivos em disco antes de emitir `/compact`.
