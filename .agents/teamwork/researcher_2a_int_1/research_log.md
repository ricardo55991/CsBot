# Log Bruto de Pesquisa Web — FASE 2A-INTERMEDIATE (M2 — Source Feasibility Research)

Agente: `researcher_2a_int_1` (Data Acquisition Researcher)
Sessão: 2026-11-09T00:50Z — 2026-11-09T01:00Z (UTC)
Método: `search_web` e `read_url_content` sobre documentação pública oficial. Nenhum download de demo,
nenhum scraping autenticado, nenhuma submissão de formulário, nenhum bypass de challenge anti-bot.

Cada linha: URL | UTC da consulta | resultado | rótulo epistêmico.

## Consultas bem-sucedidas (conteúdo recuperado)

| # | URL | UTC | Resultado | Rótulo |
|---|---|---|---|---|
| 1 | https://docs.faceit.com/ | 2026-11-09T00:51Z | Portal "FACEIT for Developers" (Docusaurus 2.4.1), nav: Getting Started / API / SDK / Game Studio | VERIFIED_ONLINE |
| 2 | https://docs.faceit.com/getting-started/intro/start-here | 2026-11-09T00:51Z | Acesso via developers.faceit.com, login com conta FACEIT, App Studio cria App com múltiplas API Keys, OAuth2 e Webhooks; link de ToS = developers.faceit.com/terms | VERIFIED_ONLINE |
| 3 | https://docs.faceit.com/docs | 2026-11-09T00:51Z | Ferramentas de desenvolvedor; menção a Data APIs, OAuth2, Webhooks, Chat; App Directory | VERIFIED_ONLINE |
| 4 | https://docs.faceit.com/sitemap.xml | 2026-11-09T00:51Z | 23 rotas listadas (usado para descobrir a rota correta do Downloads API) | VERIFIED_ONLINE |
| 5 | https://docs.faceit.com/getting-started/Guides/download-api | 2026-11-09T00:52Z | Conteúdo em cloud é privado por padrão; `POST /download/v2/demos/download` com `{"resource_url": ...}` → `{"payload":{"download_url": "<signed_url>"}}`; exige "exclusive Access Token that has a Downloads API scope" (Bearer); URL de demos aparece nas respostas do endpoint de Matches; webhook "Match Demo Ready"; formulário de aplicação em 3 seções; "expected response time for the application is 30 days" | VERIFIED_ONLINE |
| 6 | https://docs.faceit.com/getting-started/Guides/permissions | 2026-11-09T00:52Z | Tabela de permissões de colaboradores do App (#owner/#admin/#watcher) — não é tabela de scopes de API | VERIFIED_ONLINE |
| 7 | https://docs.faceit.com/getting-started/authentication/oauth2 | 2026-11-09T00:52Z | FACEIT Connect (OAuth2), Authorization Code + PKCE para apps server-side; Client Secret é tratado como senha e invalidado ao regenerar | VERIFIED_ONLINE |
| 8 | https://docs.faceit.com/getting-started/Guides/event-notifications | 2026-11-09T00:52Z | Webhooks por App no Developer Portal; múltiplas subscrições, URLs distintas | VERIFIED_ONLINE |
| 9 | https://docs.faceit.com/docs/data-api/data | 2026-11-09T00:52Z | Referência OpenAPI Data API v4 (`https://open.faceit.com/data/v4`), "License: Property of FACEIT LTD"; `GET /matches/{match_id}` documenta `demo_url` (array), `instances[].demos[]`, `teams.<faction>.roster[].game_skill_level`, `teams.<faction>.stats.skillLevel.{average,range.{min,max}}`, `voting` (schema `null` no sample); `GET /players/{player_id}/history` retorna `teams.<faction>.players[].skill_level` com janela default `from` = 1 mês atrás; respostas documentadas incluem 429 Too many requests; nenhuma política numérica de rate limit publicada | VERIFIED_ONLINE |
| 10 | https://docs.faceit.com/docs/webhooks | 2026-11-09T00:53Z | Lista de eventos inclui `match_demo_ready` para subscription types Organizer / User / Game; callback com autenticação opcional (header ou query) | VERIFIED_ONLINE |
| 11 | https://docs.faceit.com/getting-started/Guides/retreiving-faceit-data | 2026-11-09T00:54Z | Data API como REST/JSON; exemplos incluem "retrieve Player's skill level" | VERIFIED_ONLINE |
| 12 | https://docs.faceit.com/getting-started/authentication/api-keys | 2026-11-09T00:54Z | API Keys criadas no App Studio, revogáveis, server-side vs client-side | VERIFIED_ONLINE |
| 13 | https://docs.faceit.com/getting-started/intro/getting-help | 2026-11-09T00:55Z | Canal de suporte = Discord da comunidade de developers (não há e-mail de suporte técnico publicado nessa página) | VERIFIED_ONLINE |
| 14 | https://fce.gg/downloads-api-application | 2026-11-09T00:56Z | Google Form "FACEIT - Downloads API Application" (criado dentro do ESL FACEIT Group); 3 seções; contato `partnerships@faceit.com`; tiers de acesso: "Free tier (Up to 1500 requests or 200GB)" e "Enterprise" | VERIFIED_ONLINE |
| 15 | https://steamcommunity.com/dev/apiterms | 2026-11-09T00:53Z | Steam Web API Terms of Use (last updated July 2010): apenas recuperar Steam Data "as requested by the end user"; publicar privacy policy; informar o que será armazenado e em qual país; manter a API key confidencial; não interceptar/armazenar a senha Steam; não criar tecnologia que dê vantagem competitiva injusta; limite de 100.000 chamadas/dia | VERIFIED_ONLINE |
| 16 | https://store.steampowered.com/subscriber_agreement/ | 2026-11-09T00:53Z | SSA: "personal, non-commercial use"; proibição de copiar/reproduzir/publicar/distribuir/engenharia reversa sem consentimento prévio por escrito da Valve; §4.B Cheating; §4.C Automation proíbe "scripts, bots, macros, or other non-human-controlled systems" | VERIFIED_ONLINE |
| 17 | https://partner.steamgames.com/doc/api/ISteamGameCoordinator | 2026-11-09T00:55Z | "Functions for sending and receiving messages from the Game Coordinator. This is largely deprecated..."; acesso via `ISteamClient::GetISteamGenericInterface` (contexto de cliente Steam autenticado) | VERIFIED_ONLINE |
| 18 | https://api.steampowered.com/ISteamWebAPIUtil/GetSupportedAPIList/v1/ | 2026-11-09T00:53Z | Retornou 27 interfaces; única interface associada ao appid 730 é `IGCVersion_730.GetServerVersion`. Não há `ICSGOPlayers_730` nem endpoint de demo/match-history na lista pública não autenticada | VERIFIED_ONLINE |
| 19 | https://www.kaggle.com/api/v1/datasets/list?search=counter%20strike&page=1 | 2026-11-09T00:54Z | 20 datasets retornados (ref, título, data, downloads) | VERIFIED_ONLINE |
| 20 | https://www.kaggle.com/api/v1/datasets/view/billpureskillgg/cs2-2023-11-23 | 2026-11-09T00:55Z | "Counter-Strike 2 (CS2) Telemetry/event data CSDS": ~1.300 partidas CS2, 51.498.527.411 bytes, licença CC BY-NC-SA 4.0, 30+ canais, dos usuários do PureSkill.gg | VERIFIED_ONLINE |
| 21 | https://docs.pureskill.gg/datascience/adx/cs2/csds/spec | 2026-11-09T00:55Z | Spec CSDS (CS2): `header.map_name`; `player_info.rank`, `rank_type`, `rank_raw`, `rank_platform`; `game_rank_if_win/loss/tie` (0 fora de Premier, "as on FACEIT and league demos"); `header.platform`, `match_type`, `match_date`; `demo_id`/`sharecode` redigidos por scrubber de PII | VERIFIED_ONLINE |
| 22 | https://docs.pureskill.gg/datascience/adx/csgo/csds/spec | 2026-11-09T00:55Z | Spec arquivada de CS:GO CSDS (canais descontinuados) | VERIFIED_ONLINE |
| 23 | https://www.kaggle.com/api/v1/datasets/view/piercehentosh/counter-strike-2-win-prediction-faceit | 2026-11-09T00:55Z | 9.651 partidas FACEIT, licença MIT, features = avg win%, avg ELO do time, avg K/R; sem demos; sem rank por jogador no momento da partida | VERIFIED_ONLINE |
| 24 | https://www.kaggle.com/api/v1/datasets/view/skihikingkevin/csgo-matchmaking-damage | 2026-11-09T00:56Z | "CS:GO Competitive Matchmaking Data": ~1.400 partidas MM de CS:GO (Source 1), 3.624.699.821 bytes, CC BY-NC-SA 4.0, extraído de replays enviados ao csgo-stats; sem metadado de rank documentado | VERIFIED_ONLINE |
| 25 | https://pureskill.gg/ | 2026-11-09T00:54Z | Site do provedor (não inspecionado em profundidade; usado apenas para confirmar existência) | VERIFIED_ONLINE (existência) |

## Consultas que FALHARAM (registradas, não preenchidas por invenção)

| # | URL | UTC | Falha | Consequência |
|---|---|---|---|---|
| F1 | https://developers.faceit.com/docs/tutorials/getting-started/ | 2026-11-09T00:51Z | HTTP 403 | rota descartada; descoberta refeita por sitemap |
| F2 | https://docs.faceit.com/docs/tutorials/getting-started | 2026-11-09T00:51Z | HTTP 404 | rota inexistente |
| F3 | https://docs.faceit.com/getting-started/guides/authentication | 2026-11-09T00:51Z | HTTP 404 | slug em caixa alta (`Guides`) é o correto |
| F4 | https://docs.faceit.com/getting-started/guides/partner-integration-guide | 2026-11-09T00:51Z | HTTP 404 | idem |
| F5 | https://developers.faceit.com/terms | 2026-11-09T00:54Z | HTTP 403 | **ToS de FACEIT Developer NÃO lido** → uso para ML fica `UNVERIFIED` |
| F6 | https://www.faceit.com/en/terms | 2026-11-09T00:54Z | HTTP 403 | idem para ToS geral da plataforma |
| F7 | https://support.faceit.com/hc/en-us/articles/202401965-FACEIT-Elo-and-skill-levels | 2026-11-09T00:55Z | HTTP 403 | faixas de Elo por level **não verificadas** (não citadas como fato no relatório) |
| F8 | https://help.steampowered.com/en/wizard/HelpWithGameIssue/?appid=730&issueid=128 | 2026-11-09T00:53Z | shell HTML sem conteúdo (exige login/JS) | fluxo de "Game Authentication Code" **não verificado** |
| F9 | https://developer.valvesoftware.com/wiki/Counter-Strike:_Global_Offensive_Access_Match_History | 2026-11-09T00:53Z | challenge Anubis (proof-of-work JS) — **não contornado** | fluxo GC/share-code documentado pela Valve **não verificado** |
| F10 | https://developer.valvesoftware.com/w/index.php?title=...&action=raw | 2026-11-09T00:53Z | mesmo challenge Anubis | idem |
| F11 | https://web.archive.org/web/2024id_/https://developer.valvesoftware.com/wiki/... | 2026-11-09T00:54Z | HTTP 498 | snapshot histórico não obtido |
| F12 | https://partner.steamgames.com/doc/webapi/ICSGOPlayers_730 | 2026-11-09T00:53Z | serviu o índice genérico de docs (sem conteúdo ICSGO) | página de interface CS:GO não existe publicamente nesse caminho |
| F13 | https://partner.steamgames.com/doc/webapi | 2026-11-09T00:53Z | 0 ocorrências de "icsgo", "csgo" ou "730" no índice | idem |

## Buscas (`search_web`) usadas apenas como pista de descoberta

| UTC | Consulta | Uso |
|---|---|---|
| 2026-11-09T00:51Z | "FACEIT Data API developers documentation OAuth token rate limits demo download" | descoberta (pista para docs.faceit.com e rota do Downloads API) |
| 2026-11-09T00:53Z | "Steam personal game data CS2 match history sharing code official documentation" | descoberta (pistas para SSA/ToS e wiki); **as afirmações do sumário não foram aceitas sem verificação** |
| 2026-11-09T00:54Z | "public dataset Counter-Strike 2 demos .dem de_mirage with player rank skill level research license" | descoberta (pista para PureSkill.gg) |
| 2026-11-09T00:54Z | "Kaggle dataset CS:GO demo files dem download matchmaking rank MM" | descoberta (pistas Kaggle) |
| 2026-11-09T00:55Z | "FACEIT skill level elo ranges official support article level 5 6 7 8 thresholds" | descoberta; **verificação falhou (F7) → não usado como fato** |

## Regra aplicada

Sumários de `search_web` **não** foram tratados como evidência. Toda afirmação do relatório marcada
`VERIFIED_ONLINE` foi lida na página original recuperada nesta sessão e está na tabela acima.
