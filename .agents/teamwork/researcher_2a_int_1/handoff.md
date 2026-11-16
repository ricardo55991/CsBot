# Handoff — researcher_2a_int_1 (Data Acquisition Researcher, FASE 2A-INTERMEDIATE)

**Tipo:** Hard (tarefa concluída dentro do escopo M2)
**Data UTC:** 2026-11-09T01:05Z
**Papel:** papel 2 do §3 — Source Feasibility Research (9 perguntas do §2 + fontes A–D do §5)

---

## 1. Observation

### 1.1 Entregáveis materializados (todos com tamanho > 0)

| # | Caminho relativo | Bytes | Linhas | SHA-256 (64 hex, lido do disco) |
|---|---|---|---|---|
| 1 | `training_runs/intermediate_domain_study/source_feasibility_report.md` | 59871 | 858 | `55f1d9d2cda42297885d2a05471dc651ba63c17e4eabdeecc354d171109f2d4c` |
| 2 | `training_runs/intermediate_domain_study/legal_and_access_constraints.md` | 6439 | 98 | `989ceb724f918da5d298a08452bc8eda6dbfd1d217c1a2cd7720ab7f7a26555a` |
| 3 | `training_runs/intermediate_domain_study/faceit_access_readiness.json` | 15880 | 418 | `26739883cec11877c83ecb33bd821fa9fd478fa84847058d65d4f6e384b20712` |
| 4 | `training_runs/intermediate_domain_study/valve_opt_in_feasibility.md` | 7987 | 113 | `f63ba568aa0fd9de456b7c8fd4ca9fb1b4e1f6e73ae0f91c56a8b60e91f8f61f` |
| 5 | `datasets/mirage_domains/intermediate_competitive/acquisition_source_matrix.json` | 31073 | 659 | `f09ac2a5962bb69fb38361739200b7f656d29e25f0d3c68a2c1b82fde380f3e8` |

Artefatos auxiliares (metadados de agente, não são entregáveis de fase):
- `.agents/teamwork/researcher_2a_int_1/research_log.md` — 38 URLs consultadas (25 recuperadas + 13 falhas)
  e 5 buscas de descoberta, cada uma com UTC e resultado.
- `.agents/teamwork/researcher_2a_int_1/DISPATCH.md`, `BRIEFING.md`, `progress.md`.

### 1.2 Fatos verificados nesta sessão (trecho literal da documentação)

Recuperados de páginas originais (não de resumo de busca):

1. `docs.faceit.com/getting-started/Guides/download-api` — *"Downloadable content on FACEIT's Cloud
   infrastructure is private by default and can only be accessed with a signed URL."*; endpoint
   `POST /download/v2/demos/download`; *"Downloads API requires authentication with an exclusive Access Token
   that has a Downloads API scope"*; *"The expected response time for applications is 30 days"*.
2. `fce.gg/downloads-api-application` — formulário real, título "FACEIT - Downloads API Application",
   criado dentro do ESL FACEIT Group, 3 seções, tiers **"Free tier (Up to 1500 requests or 200GB)"** e
   **"Enterprise"**, contato `partnerships@faceit.com`.
3. `docs.faceit.com/docs/data-api/data` — `GET /matches/{match_id}` documenta `demo_url` (array),
   `instances[].demos[]`, `teams.<faction>.roster[].game_skill_level`,
   `teams.<faction>.stats.skillLevel.{average,range}`; `GET /players/{player_id}/history` devolve
   `teams.<faction>.players[].skill_level` com janela default de **1 mês**; respostas incluem `429`;
   "License: Property of FACEIT LTD"; **0 ocorrências** da palavra "map" no texto renderizado da referência
   OpenAPI v4 e `voting` com schema `null`.
4. `api.steampowered.com/ISteamWebAPIUtil/GetSupportedAPIList/v1/` — retornou **27 interfaces**; a única
   associada ao appid 730 é `IGCVersion_730.GetServerVersion`.
5. `partner.steamgames.com/doc/api/ISteamGameCoordinator` — *"Functions for sending and receiving messages
   from the Game Coordinator. This is largely deprecated..."*, acesso via `ISteamClient::GetISteamGenericInterface`.
6. `steamcommunity.com/dev/apiterms` — *"You will only retrieve Steam Data about a Steam end user as requested
   by the end user."*; *"You are limited to one hundred thousand (100,000) calls to the Steam Web API per day."*.
7. `store.steampowered.com/subscriber_agreement/` — uso *"personal, non-commercial"*; §4.C proíbe
   *"scripts, bots, macros, or other non-human-controlled systems"*.
8. Kaggle `billpureskillgg/cs2-2023-11-23` — ~1.300 partidas CS2, **51.498.527.411 bytes**,
   **CC BY-NC-SA 4.0**; spec em `docs.pureskill.gg/datascience/adx/cs2/csds/spec` documenta
   `header.map_name`, `player_info.rank`, `rank_type`, `game_rank_if_win/loss/tie` (0 fora de Premier)
   e `demo_id`/`sharecode` redigidos.
9. Kaggle `piercehentosh/counter-strike-2-win-prediction-faceit` — 9.651 partidas FACEIT, MIT, apenas médias
   de time.
10. Kaggle `skihikingkevin/csgo-matchmaking-damage` — ~1.400 partidas CS:GO (Source 1), 3.624.699.821 bytes,
    CC BY-NC-SA 4.0.

### 1.3 Falhas de acesso registradas (não preenchidas por invenção)

`developers.faceit.com/terms` = HTTP 403; `faceit.com/en/terms` = HTTP 403; `support.faceit.com/...` = HTTP
403; `help.steampowered.com` wizard = shell sem conteúdo (exige login); `developer.valvesoftware.com` = challenge
Anubis (não contornado); `web.archive.org` = HTTP 498; `partner.steamgames.com/doc/webapi/ICSGOPlayers_730` =
índice genérico, sem conteúdo da interface.

---

## 2. Logic Chain

1. **Existe caminho legal para demo + rank?** Sim, documentado: o `demo_url` sai da Data API (metadados) e a
   assinatura de download sai da Downloads API (Obs. 1.2.1/1.2.3). Esse é o único par documentado que combina
   nível do jogador e acesso a arquivo.
2. **A Data API sozinha autoriza download?** Não. O conteúdo é privado por padrão e só é servido por URL
   assinada emitida pela Downloads API (Obs. 1.2.1) → `demo_accessible = FAIL` para A1.
3. **O que falta para A2?** Um token com escopo de Downloads API, obtido por aplicação (prazo declarado de
   30 dias) que **não foi submetida** (Obs. 1.2.1/1.2.2) → `UNKNOWN_PENDING_HUMAN_APPROVAL` para demo,
   licença e downloader.
4. **FACEIT oferece metadados suficientes?** Parcialmente: nível por jogador e demo por partida estão
   documentados; **mapa não está** (0 ocorrências de "map" e `voting: null`) → a descoberta "só Mirage" não é
   expressável na query (Obs. 1.2.3).
5. **O rank é do momento da partida?** `game_skill_level` está no roster da partida, mas a semântica temporal
   não é declarada; o histórico por partida existe (`skill_level` por item) com janela default de 1 mês →
   `PARTIAL`, com semântica `INFERRED` (Obs. 1.2.3).
6. **Valve permite caminho automático?** Não. A lista pública não tem endpoint de histórico/demo para o appid
   730 (Obs. 1.2.4), o Game Coordinator é interface de cliente autenticado e "largely deprecated"
   (Obs. 1.2.5), e a SSA proíbe automação (Obs. 1.2.7) → `NOT_FEASIBLE_NOW` + `SECURITY_REVIEW_REQUIRED`.
7. **Valve permite caminho manual consentido?** Sim: a ToS autoriza recuperar dados do usuário "as requested by
   the end user" (Obs. 1.2.6) e o jogador pode entregar o próprio arquivo → `FEASIBLE_WITH_HUMAN_CONSENT`.
8. **Datasets públicos resolvem?** Não para o Gate B. O melhor candidato (C1) tem rank e mapa documentados
   (Obs. 1.2.8) mas **não entrega `.dem`** e é **CC BY-NC-SA 4.0** → `demo_accessible = FAIL`, licença
   `NON_COMMERCIAL_ONLY`. C2 tem só médias de time; C3 é CS:GO (Obs. 1.2.9/1.2.10).
9. **Portanto o Gate A fecha?** Não. Dos 6 critérios, nenhuma sub-fonte atinge 6/6 (0/8), e `demo_accessible`
   é `PASS` em 0/8 (contagem na matriz). Mas também não há violação legal consumada: o caminho existe e está
   documentado, apenas não autorizado → o rótulo canônico é `INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING`
   (previsto no §22), não `PASS` nem `FAIL`.
10. **Perguntas 5–8 do §2** dependem de dados materializados; sem corpus, o veredito é
    `UNKNOWN_UNVERIFIED` e a comparação estatística deve ser marcada `NOT_EXECUTABLE_NO_INTERMEDIATE_DATA`
    (proibido fabricar). **Pergunta 9** é `DEFERRED`: as cinco estratégias exigem `.dem`, e a única fonte
    pública com rank/mapa não a fornece — decidir agora seria escolher por preferência narrativa.

---

## 3. Caveats

- **`UNVERIFIED` por bloqueio de acesso:** Termos de Desenvolvedor e Termos da plataforma FACEIT (HTTP 403);
  fluxo oficial de "Game Authentication Code" da Valve (exige login); wiki de desenvolvedores da Valve
  (challenge Anubis, não contornado — contornar seria violar a proibição da fase); faixas de Elo por level da
  FACEIT (HTTP 403). **Nenhuma dessas lacunas foi preenchida com descrição inventada.**
- **Negativo não absoluto:** a lista `GetSupportedAPIList` foi chamada **sem chave** (27 interfaces). Uma
  chamada autenticada pode devolver mais interfaces; por isso o negativo da Fonte B é forte mas classificado
  como `UNVERIFIED` quanto ao conjunto autenticado.
- **Nenhum tamanho de demo foi medido.** Por isso não existe conversão de "200 GB" para "número de demos": a
  conta está explicitamente `N/A`. Nenhum número de demos, arquivos ou partidas foi estimado.
- **Semântica de `game_skill_level`:** a documentação não declara que o valor é o do instante da partida. A
  leitura "no momento da partida" é `INFERRED`; o relatório rebaixa `metadata_confidence` por isso.
- **Campo de mapa da FACEIT:** a ausência de "map" no documento OpenAPI é fato verificado; a existência de
  `voting.map.pick` em respostas reais é `INFERRED` e **não** foi afirmada como contrato.
- **Licença CC BY-NC-SA 4.0:** a leitura de que restringe uso comercial é a leitura padrão da licença, mas o
  enquadramento do projeto (pesquisa interna vs. produto) é decisão humana, não do agente.
- **Escopo não coberto:** não avaliei custo/qualidade de parsers Source 2, nem latência de download, nem
  disponibilidade regional da FACEIT. Também não verifiquei se a FACEIT mantém demos de matchmaking por tempo
  suficiente para o piloto.
- **Nada foi coletado.** Corpus intermediário = 0 arquivos (0/0). Nenhuma demo baixada, nenhum formulário
  enviado, nenhuma conta criada, nenhuma credencial tocada.

---

## 4. Conclusion

**Veredito recomendado de Gate A: `INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING`.**

Classificação de acessibilidade:
- **FACEIT (A)** — única fonte com rank + demo no mesmo contrato; **bloqueada por autorização**
  (`application_submitted: false`), com caminho claro e prazo declarado de 30 dias.
- **Valve (B)** — **não viável** para coleta automática (`NOT_FEASIBLE_NOW` + `SECURITY_REVIEW_REQUIRED`);
  viável apenas como contribuição manual consentida.
- **Datasets públicos (C)** — **parcial e não substitutivo**: sem `.dem`, licença não comercial; serve apenas
  a análise exploratória, jamais ao Gate B.
- **Contribuições voluntárias (D)** — **único caminho independente de terceiro**, porém sem corpus e pendente
  de instrumento de consentimento aprovado por humano.

Respostas ultra-curtas às 9 perguntas: P1 `PARTIAL`; P2 `PARTIAL`; P3 `PARTIAL`; P4 `PARTIAL` (pendente de
autorização); P5 `UNKNOWN_UNVERIFIED`; P6 `UNKNOWN_UNVERIFIED`; P7 `UNKNOWN_UNVERIFIED`;
P8 `UNKNOWN_UNVERIFIED`; P9 `DEFERRED`. Contagem: 4/9 `PARTIAL`, 4/9 `UNKNOWN_UNVERIFIED`, 1/9 `DEFERRED`,
0/9 `YES`, 0/9 `NO`.

Próximo passo depende exclusivamente de decisão humana (não iniciar coleta, não avançar de fase — Regra 08):
ler os Termos FACEIT e decidir sobre submeter a aplicação do Downloads API; em paralelo, aprovar o
instrumento de consentimento da Fonte D.

### 1.4 Confirma??es de integridade de aquisi??o (exigidas pelo Sentinel)

- **Nenhum formul?rio FACEIT foi enviado** ? em particular, `fce.gg/downloads-api-application` foi apenas
  **lido publicamente** (sem preencher, sem enviar, sem autenticar).
- **Nenhuma conta foi criada** em FACEIT, Kaggle, Steam, Google ou qualquer plataforma.
- **Nenhum termo foi aceito** ? os Termos FACEIT e da plataforma nem sequer puderam ser lidos (HTTP 403).
- **Nenhuma credencial foi tocada**: sem senha Steam, Steam Guard secret, session cookie, `steamLoginSecure`,
  API key, token OAuth2 ou client secret ? n?o solicitadas, n?o recebidas, n?o escritas, n?o logadas.
- **Nenhuma demo foi baixada**: `datasets/mirage_domains/**` cont?m 0 arquivos `.dem` (0/0).
- A via FACEIT permanece bloqueada at? **aprova??o humana expl?cita**; se o Orchestrator solicitar, o texto do
  pedido pode ser preparado para revis?o humana, mas **n?o ser? submetido** por este agente.
---

## 5. Verification Method

Comandos executados (PowerShell + Python 3), todos a partir da raiz do repositório
`c:/Users/ricar/OneDrive/Documentos/Dev/CsBot`:

**(a) Existência, tamanho, linhas e SHA-256 lido do disco**

```python
import hashlib, pathlib
root = pathlib.Path(r"c:\Users\ricar\OneDrive\Documentos\Dev\CsBot")
for t in [
 "training_runs/intermediate_domain_study/source_feasibility_report.md",
 "training_runs/intermediate_domain_study/legal_and_access_constraints.md",
 "training_runs/intermediate_domain_study/faceit_access_readiness.json",
 "training_runs/intermediate_domain_study/valve_opt_in_feasibility.md",
 "datasets/mirage_domains/intermediate_competitive/acquisition_source_matrix.json",
]:
    b = (root/t).read_bytes()
    print(t, len(b), hashlib.sha256(b).hexdigest())
```

Saída (resumo): todos `exists=True`, `size_gt_0=True`, `sha_len=64`.

```
training_runs/intermediate_domain_study/source_feasibility_report.md        bytes=59871 lines=858 sha256=55f1d9d2cda42297885d2a05471dc651ba63c17e4eabdeecc354d171109f2d4c
training_runs/intermediate_domain_study/legal_and_access_constraints.md     bytes=6439  lines=98  sha256=989ceb724f918da5d298a08452bc8eda6dbfd1d217c1a2cd7720ab7f7a26555a
training_runs/intermediate_domain_study/faceit_access_readiness.json        bytes=15880 lines=418 sha256=26739883cec11877c83ecb33bd821fa9fd478fa84847058d65d4f6e384b20712
training_runs/intermediate_domain_study/valve_opt_in_feasibility.md         bytes=7987  lines=113 sha256=f63ba568aa0fd9de456b7c8fd4ca9fb1b4e1f6e73ae0f91c56a8b60e91f8f61f
datasets/mirage_domains/intermediate_competitive/acquisition_source_matrix.json bytes=31073 lines=659 sha256=f09ac2a5962bb69fb38361739200b7f656d29e25f0d3c68a2c1b82fde380f3e8
```

**(b) Validação de parse dos JSONs**

```
python -c "import json; json.load(open('training_runs/intermediate_domain_study/faceit_access_readiness.json', encoding='utf-8'))"
python -c "import json; json.load(open('datasets/mirage_domains/intermediate_competitive/acquisition_source_matrix.json', encoding='utf-8'))"
```

Saída: `JSON parse OK` para ambos (28 e 19 chaves de topo, respectivamente).

**(c) Hook de relatório `validate_generated_report` — AUTO-CHECAGEM, NÃO validação independente**

Executado pelo próprio autor via stdin com payload no formato do hook, sobre os 5 entregáveis:

```
python .agents/hooks/validate_generated_report.py   (payload JSON com tool_input.TargetFile + Content)
```

Saída: **5/5 `{"decision": "allow"}` → 0 violações** em todos os alvos
(`source_feasibility_report.md` e `acquisition_source_matrix.json` classificados como relatório;
os demais retornaram "Operação não envolve geração de relatório executivo").

**Rótulo canônico deste item: `AUTOMATED_CHECK_PASS` (auto-checagem do autor).**
Este resultado **não** é validação independente e **não** constitui `VALIDATED`, `APPROVED` nem `PASS` de fase.
O veredito independente cabe ao auditor adversarial / `csbot-report-skeptic` na Wave 3
(`07-independent-validation`: o implementador não é o único validador do próprio trabalho).

**Nota de rotulagem das 9 respostas (§2):** `PARTIAL` e `UNKNOWN_UNVERIFIED` são os rótulos finais e devem
permanecer literais. Este handoff não os converte em `PASS` ou `FAIL`, e não preenche nenhuma lacuna por
inferência — o que não foi verificado está marcado como tal.

**(d) Auditoria de forma do relatório**

- 0 ocorrências de `0.0%` (Regra 03 respeitada).
- Percentuais só aparecem como nome de feature de dataset ("win%") e em URL codificada — nenhum percentual
  sem denominador.
- Headings sequenciais §0 … §13, sem duplicação.

**Como invalidar este handoff:**
1. Recalcular os SHA-256 acima e comparar — qualquer divergência invalida a tabela §1.1.
2. Abrir as URLs da tabela §12 do relatório e confirmar que o texto citado existe — se uma citação não existir,
   a afirmação correspondente é inválida.
3. Verificar que `application_submitted: false` em `faceit_access_readiness.json` corresponde à realidade
   (nenhuma aplicação FACEIT foi submetida em nome do projeto).
4. Verificar que o corpus intermediário permanece com 0 arquivos (0/0) e que nenhum `.dem` existe em
   `datasets/mirage_domains/intermediate_competitive/`.
