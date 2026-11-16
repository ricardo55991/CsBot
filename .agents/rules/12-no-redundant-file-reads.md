# Regra 12: Proibição de Leituras Redundantes (`12-no-redundant-file-reads`)

**É proibido reabrir integralmente arquivos extensos já lidos na sessão sem alteração física de hash SHA-256.**

---

## 1. Ordem de Resolução de Contexto
Antes de emitir `read_file` em qualquer arquivo físico do repositório:
1. Verificar se o extrato ou metadado já consta no **Evidence Packet** (`evidence_packet_v1`);
2. Verificar o cache de digest por hash em `.agents/cache/artifact_digest_index.json`;
3. Verificar se a informação já foi carregada em turnos anteriores da sessão;
4. Verificar se a leitura localizada por intervalo restrito de linhas (`StartLine`/`EndLine`) é suficiente.

---

## 2. Práticas Recomendadas
- Utilizar leituras pontuais de linhas específicas;
- Utilizar scripts determinísticos ou regex/grep para extração de campos JSON;
- Proibir que múltiplos agentes leiam o mesmo arquivo integralmente em cascata.

---

## 3. Exceções Permitidas para Releitura Física
Releitura completa só é autorizada quando:
- O arquivo sofreu alteração física (SHA-256 modificado);
- O resultado anterior sofreu truncamento de buffer;
- O auditor independente precisa atestar a prova criptográfica dos bytes brutos em disco;
- O artefato está formalmente sob contestação ou alegação de inconsistência.
