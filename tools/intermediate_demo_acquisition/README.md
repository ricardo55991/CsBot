# `tools/intermediate_demo_acquisition/` — downloader seguro e reprodutível (dry-run)

**Fase**: FASE 2A-INTERMEDIATE · **Papel**: Dataset and Metadata Implementer
**Rótulo de revisão**: `AGENT_REVIEWED` (auto-checagem do implementador; veredito é dos auditores)
**Estado desta fase**: `DOWNLOAD_ACCESS_PENDING` — **nenhum download real foi executado**
(`network_requests_executed = 0` em todos os componentes).

---

## 1. Por que este diretório existe

A §8 da especificação da fase autoriza, quando o Downloads API oficial **não** estiver disponível:

> não contornar restrições; executar somente a descoberta e inventário; **preparar downloader em
> modo dry-run**; testar com demos legitimamente acessíveis; emitir `DOWNLOAD_ACCESS_PENDING`.

Este diretório é exatamente esse downloader. Ele é **código real e executável**, não um esqueleto:
todas as proteções descritas abaixo estão implementadas por lógica de verdade e são exercitadas em
`--dry-run` e nos `--self-test`, sem abrir um único socket.

O modo `--execute` existe e está implementado, mas **falha por política** enquanto não houver fonte
aprovada por autorização humana (`CSBOT_APPROVED_SOURCE_ID` ausente). Isso é intencional: a fase não
autoriza aquisição real.

---

## 2. Arquitetura

Nove scripts executáveis + dois artefatos de apoio. Cada script é **autocontido** (sem import entre
irmãos) para que possa ser auditado isoladamente e para respeitar a lista fechada de 11 arquivos.
As funções de política (`redact`, detecção de URL assinada, allowlist, rate limiter, backoff) são
replicadas de forma idêntica em cada script que as usa — duplicação deliberada, não acidental.

| # | Arquivo | Responsabilidade | Rede em dry-run |
|---|---|---|---|
| 1 | `README.md` | este documento | — |
| 2 | `config.example.json` | configuração com placeholders vazios e `secret_source: "ENV"` | — |
| 3 | `discover_matches.py` | monta o plano de descoberta de partidas candidatas | ❌ nenhuma |
| 4 | `fetch_match_metadata.py` | normaliza metadado nos 17 campos do contrato | ❌ nenhuma |
| 5 | `validate_skill_bucket.py` | decide ACCEPT/REJECT por bucket de skill (§6/§4) | ❌ nenhuma |
| 6 | `download_demo.py` | download resumable com Range, backoff, checksum | ❌ nenhuma |
| 7 | `verify_archive.py` | magic bytes, checksum, entradas perigosas, bombas de descompressão | ❌ nenhuma |
| 8 | `extract_demo.py` | extração segura + integração com o pipeline NPZ canônico | ❌ nenhuma |
| 9 | `deduplicate_demo.py` | duplicatas por SHA-256 no corpus intermediário | ❌ nenhuma |
| 10 | `build_manifest.py` | monta o inventário §10 a partir de metadado + hashes do disco | ❌ nenhuma |
| 11 | `resume_download.py` | retomada determinística via `.part` + `.state.json` | ❌ nenhuma |

---

## 3. Fluxo operacional

```
                    ┌──────────────────────────────┐
                    │ config.example.json          │  (sem segredos; segredos vêm de ENV)
                    └──────────────┬───────────────┘
                                   │
   1. discover_matches.py ─────────┤  plano de consulta (buckets INCLUDED_PILOT)
                                   │
   2. fetch_match_metadata.py ─────┤  17 campos canônicos; pseudonimiza SteamID64
                                   │
   3. validate_skill_bucket.py ────┤  ACCEPT somente se bucket INCLUDED_PILOT
                                   │
   4. download_demo.py ────────────┤  Range + backoff + rate limit + SHA-256 → raw_demos/
        └─ resume_download.py ─────┤  retomada a partir de .part (URL nunca persistida)
                                   │
   5. verify_archive.py ───────────┤  magic bytes, checksum, traversal, symlink, bombas
                                   │
   6. extract_demo.py ─────────────┤  extração contida em raw_demos/
        └─ pipeline canônico ──────┤  DEM → NPZ 16 Hz (reutilizado via CSBOT_PIPELINE_DIR)
                                   │
   7. deduplicate_demo.py ─────────┤  duplicatas por SHA-256 → quarantine/
                                   │
   8. build_manifest.py ───────────┘  inventário §10 (M4, requer --execute + --out)
```

Regra transversal: **tudo o que falha vai para `quarantine/` com checksum e motivo**, nunca é
apagado. Nenhum componente escreve em `datasets/mirage_v2/` nem em
`training_runs/positioning_v2_real_temporal/`.

---

## 4. Modo dry-run

- `--dry-run` é o **padrão** de todos os scripts. A flag existe explicitamente e é mutuamente
  exclusiva com `--execute`.
- Em dry-run: nenhuma conexão de rede, nenhum byte escrito em `datasets/`, nenhum subprocesso
  (o extrator canônico só roda com `--execute`), nenhum `.part`/`.state.json`/`.dem`/`.npz` criado.
- O único evento de escrita possível em dry-run é o **audit log** quando `--audit-log PATH` é
  passado explicitamente; sem esse argumento, o evento vai para **stdout** e nenhum arquivo nasce.
- `build_manifest.py` imprime o inventário no stdout e **avisa** que `--out` foi ignorado, porque a
  materialização do inventário pertence à etapa M4.

### Exemplos verdes (executados nesta fase)

```bash
python tools/intermediate_demo_acquisition/discover_matches.py --dry-run
python tools/intermediate_demo_acquisition/fetch_match_metadata.py --dry-run
python tools/intermediate_demo_acquisition/validate_skill_bucket.py --self-test
python tools/intermediate_demo_acquisition/verify_archive.py --self-test
python tools/intermediate_demo_acquisition/extract_demo.py --self-test
python tools/intermediate_demo_acquisition/deduplicate_demo.py --self-test
python tools/intermediate_demo_acquisition/resume_download.py --self-test
python tools/intermediate_demo_acquisition/build_manifest.py --dry-run
python tools/intermediate_demo_acquisition/resume_download.py --scan
```

### Exemplo do que `--execute` faz hoje

```bash
python tools/intermediate_demo_acquisition/download_demo.py \
  --url "https://open.faceit.com/data/v4/matches/<id>" --demo-id <id> --execute
# → POLÍTICA: execução real bloqueada: nenhuma fonte aprovada. (exit code 2)
```

---

## 5. Códigos de saída (todos os scripts)

| Código | Significado |
|---|---|
| `0` | sucesso (inclui dry-run bem-sucedido e self-test com todas as asserções corretas) |
| `1` | erro de validação — política violada, hash inválido, payload inseguro, self-test falho |
| `2` | erro de uso — argumento inválido (`argparse`) ou bloqueio de política de execução |

Todo script aceita `--help` e sai com `0`.

---

## 6. Matriz de conformidade §9

Requisito → arquivo(s) → como é satisfeito (mecanismo concreto, não declaração).

| Requisito §9 | Arquivo(s) | Como é satisfeito |
|---|---|---|
| **resumable downloads** | `download_demo.py`, `resume_download.py` | `Range: bytes=<offset>-` montado a partir de `os.path.getsize(.part)`; `status == 206` mantém append, `status == 200` detecta servidor sem suporte a Range e reinicia do zero em vez de corromper; estado em `<arquivo>.state.json`. `--self-test` de `resume_download.py` cobre offset 0, retomada coerente, estado inconsistente e parcial maior que o esperado. |
| **exponential backoff** | `download_demo.py`, `resume_download.py` | `backoff_delay(attempt) = min(backoff_max_seconds, backoff_initial_seconds × backoff_factor^attempt)`; agenda impressa no plano (2→4→8→16→32 s com a config de exemplo). |
| **rate limiting** | `discover_matches.py`, `download_demo.py`, `resume_download.py` | `RateLimiter` por token bucket com `requests_per_second` e `burst` da config; `acquire()` aplica `time.sleep` real apenas fora de dry-run. |
| **retry limit** | `download_demo.py`, `resume_download.py` | `retry_limit` da config; ao esgotar, erro de validação explícito. Não há flag nem argumento que eleve o limite — a política não é contornável por CLI. |
| **checksum** | `download_demo.py`, `resume_download.py`, `verify_archive.py`, `build_manifest.py`, `deduplicate_demo.py` | SHA-256 de 64 hex validado por regex `^[0-9a-f]{64}$`; calculado por streaming em blocos de 1 MiB do disco. Divergência no download → arquivo movido para `quarantine/` antes de qualquer promoção. |
| **archive validation** | `verify_archive.py` | magic bytes (`PK\x03\x04`, `\x1f\x8b`, `BZh`, `ustar` em offset 257) confrontados com o formato declarado; `zipfile`/`tarfile` abertos em memória; `--self-test` com 8 casos (seguro, `..`, absoluto POSIX, absoluto Windows, symlink, bytes corrompidos, checksum divergente, SHA malformado). |
| **decompression segura** | `verify_archive.py`, `extract_demo.py` | Dupla barreira: (a) `verify_archive.py` recusa `..`, caminho absoluto, `C:\`, symlink/hardlink/device e limite de bytes/razão; (b) `extract_demo.py` resolve cada destino com `Path.resolve()` e exige contenção em `dest_root` (`OUTSIDE_DEST_ROOT`), reconferindo no momento da escrita. `--self-test` cobre 8 casos, incluindo `a/../../b.dem`. |
| **duplicate detection** | `deduplicate_demo.py` | Agrupa por SHA-256 e distingue **duplicata exata** (mesmo hash) de **colisão de nome** (nomes iguais, conteúdos diferentes — não é duplicata). Cruza opcionalmente com `--known-hashes`. `--self-test` cria 4 arquivos reais em `tempfile` e verifica 6 asserções. |
| **dry-run mode** | todos | `--dry-run` padrão via grupo mutuamente exclusivo; `--execute` necessário para qualquer efeito colateral. Documentado na §4 desta README. |
| **allowlist de domínio** | `discover_matches.py`, `download_demo.py`, `resume_download.py` | `network.allowed_domains` obrigatório (lista vazia = erro); match exato ou sufixo `.dominio`; HTTPS obrigatório; recusa de IP literal e de `user:pass@` na URL. |
| **audit log** | `discover_matches.py`, `fetch_match_metadata.py`, `download_demo.py` | JSONL append-only (`open(..., "a")`), uma linha por evento, `timestamp_utc` + `script` + `event` + payload; destino = `audit_log.path` da config ou stdout quando vazio. Antes de gravar, o payload passa por `assert_no_signed_url` e `assert_no_secret_leak`. |
| **credential redaction** | todos | `redact()` mascara `Authorization:`, `X-Api-Key:`, `Cookie:`, `steamLoginSecure=`, `Bearer …` e pares `token=|api_key=|password=|secret=`. Aplicado em stdout, stderr, audit log e arquivos de estado. |
| **quarantine de arquivos inválidos** | `verify_archive.py`, `download_demo.py`, `resume_download.py`, `deduplicate_demo.py`, `extract_demo.py` | `quarantine()`/`replace()` move para `datasets/mirage_domains/intermediate_competitive/quarantine/`, com sufixo `__<sha256:8>` em colisão de nome. Nada é apagado. |
| **segredos: ENV ou secret store local** | `config.example.json` + todos | `secret_source: "ENV"`; `secret_env_vars` mapeia nome lógico → variável; os valores de `credentials` no JSON devem estar vazios e a carga falha com exit 1 se algum estiver preenchido; nenhum script aceita segredo por flag. |
| **proibição de URL assinada persistida** | `config.example.json` + todos | `signed_url_persistence_allowed: false` e a carga de config **falha** se for `true`; `detect_signed_url()` reconhece `X-Amz-Signature`, `X-Amz-Credential`, `Key-Pair-Id`, `Signature=`, `sig=`, `token=`, `expires=`, `Policy=`; URL assinada é recusada na entrada, no plano, no estado e no audit log. |

---

## 7. Política de segredos

**Onde os segredos podem existir**

1. variáveis de ambiente, nomeadas por `config.example.json → secret_env_vars`:
   - `CSBOT_FACEIT_DATA_API_KEY`
   - `CSBOT_FACEIT_DOWNLOADS_API_KEY`
   - `CSBOT_STEAM_API_KEY`
   - `CSBOT_CORPUS_PSEUDONYM_SALT`
2. um secret store local do operador (não versionado), que exporte as mesmas variáveis.

**Onde é proibido** — e o que o código faz:

| Lugar | Barreira implementada |
|---|---|
| `config.example.json` / qualquer JSON versionado | `load_config()` falha (exit 1) se `credentials.*` não estiver vazio |
| logs e stdout | `redact()` + `assert_no_secret_leak()` (compara o valor real do segredo no texto) |
| arquivo de estado de resume | `write_state()` chama `assert_no_secret_leak` antes de gravar |
| URL | `assert_no_secret_leak(args.url, secrets, "url")` no downloader e na retomada |
| relatórios Markdown | nenhum script escreve segredo em Markdown; a política é declarada no contrato de domínios e nesta README |

**Nunca** são aceitos: senha Steam, Steam Guard secret, `steamLoginSecure`, cookie de sessão, token em
query string, `user:pass@` em URL. Nenhuma tentativa de contornar autenticação, ToS ou rate limit
existe no código — e o `--execute` real está bloqueado por ausência de fonte aprovada.

---

## 8. Reutilização do pipeline canônico NPZ (sem modificá-lo)

Caminhos reais descobertos no repositório:

| Papel | Caminho |
|---|---|
| Extrator DEM → NPZ 16 Hz | `tools/mlmove_pipeline/extract_16hz_tensors.py` |
| Contrato de features e diretórios | `tools/mlmove_pipeline/contract_spec.py` |
| DataLoader temporal canônico | `tools/phase3a_training/canonical_temporal_dataloader.py` |
| Materializador do índice temporal | `tools/phase3a_training/materialize_full_temporal_index.py` |

Formato canônico do NPZ (herdado, não redefinido): `X` = `[total_frames, 10, 18]` `float32`,
`Y` = `[total_frames, 10, 3]` `uint8`, 16 Hz (tick stride 4 sobre 64 tick),
`X[:, 0, 17]` = `round_time_norm` (usado pelo DataLoader para fronteiras de round com `diff > 0.15`).

**Ponto de compatibilidade real** — `contract_spec.py` linhas 53–65:

```python
DEFAULT_BASE_DIR = os.environ.get("CSBOT_PIPELINE_DIR", ...)
RAW_DEMOS_DIR_D = os.path.join(DEFAULT_BASE_DIR, "raw_demos")
EXTRACTED_TENSORS_DIR_D = os.path.join(DEFAULT_BASE_DIR, "extracted_tensors")
```

`extract_demo.py --run-npz --execute` define `CSBOT_PIPELINE_DIR` para
`datasets/mirage_domains/intermediate_competitive/` e invoca o extrator canônico com
`--map de_mirage`. Consequências verificáveis:

- o extrator passa a ler `.../intermediate_competitive/raw_demos/`;
- escreve em `.../intermediate_competitive/extracted_tensors/de_mirage/`;
- os `.npz` são então relocados para `.../intermediate_competitive/processed_npz/`.

**Nenhuma linha do pipeline canônico é alterada**, e `--delete-after-extract` **nunca** é passado,
para preservar a cadeia de custódia do `.dem`.

---

## 9. Limitações conhecidas e pendências honestas

1. **Nenhuma demo foi baixada.** `demos_intermediate_acquired = 0`. O veredito esperado da fase é
   `INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING` (emitido pelo Phase Gate, não por este diretório).
2. **A FACEIT Data API comum não autoriza download de demo.** O plano de descoberta
   (`discover_matches.py`) consulta apenas metadado; acesso ao `.dem` depende do Downloads API com
   aplicação e scopes aprovados, o que exige cadastro externo e autorização humana.
3. **Bucket Premier não está definido** (`NOT_DEFINED_PENDING_DISTRIBUTION_AUDIT`); o validador
   rejeita qualquer demo apenas-Premier até a auditoria de distribuição.
4. **SteamID64 pseudonimizado exige salt**: sem `CSBOT_CORPUS_PSEUDONYM_SALT`, o normalizador de
   metadado falha em vez de publicar identificador em claro.
5. **`--execute` está bloqueado por política** enquanto `CSBOT_APPROVED_SOURCE_ID` não existir no
   ambiente. Isso é uma barreira de governança, não um defeito.
6. Os `--self-test` usam **fixtures sintéticas rotuladas** (`TEST_FIXTURE_NOT_REAL_DATA` /
   `TEST_FIXTURE_IN_TEMPDIR_NOT_REAL_DATA`) e **não** constituem telemetria real: são asserções de
   lógica de política, não observação de partidas.
