# GATE STATUS — FASE 2A-INTERMEDIATE

## Pré-gate: M0 — Marcador de pausa formal
| Item | Valor |
|---|---|
| Artefato | `training_runs/positioning_v2_real_temporal/PAUSED_FOR_INTERMEDIATE_DOMAIN_ACQUISITION_STUDY.json` |
| Bytes | 37114 |
| SHA-256 (64 hex) | `465f4cb93e41cbc50fb86a8fb9e2544b901633e8d0282ee0a31fe9db9813efad` |
| Verificação independente — Sentinel | PASS (recalculado do disco) |
| Verificação independente — Orchestrator | MATCH (recalculado do disco, 64 hex) |
| Auto-checagem do implementador | `AGENT_REVIEWED` / `AUTOMATED_CHECK_PASS` (reclassificada; NÃO é validação — Regras 07/09) |
| Natureza do dado | `REAL` |
| Resultado | **M0 PRE-GATE PASS** |

### Decisão registrada: M0 **NÃO** será reemitido
O implementador solicitou autorização para reemitir o marcador com rótulos internos renomeados. **Negado**, por três razões: (i) o hash `465f4cb9…13efad` está ancorado por três verificações independentes e reemitir destruiria a prova de anterioridade da pausa (Regra 01); (ii) a Regra 06 exigiria backup + hash anterior + diff + rollback para artefato sensível, desproporcional para mudança cosmética; (iii) a reclassificação `AGENT_REVIEWED`/`AUTOMATED_CHECK_PASS` já está registrada no `progress.md` e neste arquivo, com o veredito reservado aos auditores da Wave 3. Diretriz do Sentinel coincide. O arquivo permanece **byte-idêntico**: 37114 B / `465f4cb93e41cbc50fb86a8fb9e2544b901633e8d0282ee0a31fe9db9813efad`.

### Pendência de ambiente: `PENDING_TOOLCHAIN`
| Componente | Estado (verificado por `importlib.util.find_spec`) |
|---|---|
| `demoparser2` | **ABSENT** |
| `pyarrow` | PRESENT |
| `numpy` | PRESENT |

Consequência: a verificação end-to-end de `extract_demo.py --run-npz --execute` (DEM→NPZ real) **não é executável** nesta fase. Rótulo obrigatório: **`PENDING_TOOLCHAIN`**. Não é falha da fase, **não** pode virar "validado por omissão", e **nenhum agente instala pacotes** por conta própria.

## EVIDENCE_LOSS_EVENT (obrigatório na matriz e no relatório final)

| Campo | Valor |
|---|---|
| `event` | `EVIDENCE_LOSS_EVENT` |
| `t_removal_utc` | `2026-11-09T01:08:42Z` — remoção dos 7 `_tmp_*` (`Remove-Item -Force`, sem Lixeira) |
| `t_order_issued_utc` | `2026-11-09T01:08:48Z` — ordem "não apague" chegou 6 s após o ato |
| `t_recapture_window_utc` | `2026-11-09T01:09:09Z – 01:09:17Z` |
| `recaptured_location` | `scratch/2a_intermediate_research_cache/` — 10 arquivos, 1.590.118 B, 10/10 hashes conferidos por Orchestrator e Sentinel |
| `consequence` | `originals_unavailable_for_report_to_source_fidelity_check` |
| `classification` | `PHASE_LIMITATION` — não falha disciplinar; autodeclaração espontânea |

**Regras vinculantes decorrentes (E2–E4)**:
- `REPORT_TO_SOURCE_FIDELITY_UNVERIFIED`: toda afirmação de `source_feasibility_report.md` dependente dos `_tmp_*` originais fica com fidelidade **não demonstrável**; nenhuma pode ser promovida a `VERIFIED_ONLINE`.
- O cache é sempre rotulado **`RECAPTURED`** ao lado de caminho e hash — **nunca** evidência primária.
- O auditor adversarial da Wave 3 deve caçar qualquer afirmação sustentada apenas pelo cache recapturado apresentada como verificação da época.
- Falha F12 preservada: `steam_icsgoplayers_730.txt` é índice genérico (0 ocorrências de `ICSGOPlayers`/`IGCVersion_730`) — **a ausência de prova não pode virar "interface confirmada"**.

## Gate A — Aquisição (pré-veredito M2; veredito final reservado à Wave 3)

| Artefato | Bytes | SHA-256 (verificado pelo Orchestrator) |
|---|---|---|
| `training_runs/intermediate_domain_study/source_feasibility_report.md` | 59871 | `55f1d9d2cda42297885d2a05471dc651ba63c17e4eabdeecc354d171109f2d4c` |
| `training_runs/intermediate_domain_study/legal_and_access_constraints.md` | 6439 | `989ceb724f918da5d298a08452bc8eda6dbfd1d217c1a2cd7720ab7f7a26555a` |
| `training_runs/intermediate_domain_study/faceit_access_readiness.json` | 15880 | `26739883cec11877c83ecb33bd821fa9fd478fa84847058d65d4f6e384b20712` |
| `training_runs/intermediate_domain_study/valve_opt_in_feasibility.md` | 7987 | `f63ba568aa0fd9de456b7c8fd4ca9fb1b4e1f6e73ae0f91c56a8b60e91f8f61f` |
| `datasets/mirage_domains/intermediate_competitive/acquisition_source_matrix.json` | 31073 | `f09ac2a5962bb69fb38361739200b7f656d29e25f0d3c68a2c1b82fde380f3e8` |

| Critério Gate A (§22) | Resultado |
|---|---|
| fonte legítima | `PARTIAL` — caminho oficial documentado, nenhum liberado |
| rank rastreável | `PARTIAL` — FACEIT `game_skill_level`/`skill_level`; semântica temporal `INFERRED` |
| demo acessível | **PASS em 0/8 sub-fontes** |
| licença ou autorização registrada | `PARTIAL` — FACEIT ML use `UNVERIFIED_REQUIRES_HUMAN_READ_OF_TERMS`; CC BY-NC-SA 4.0 pendente |
| zero segredo persistido | `PASS` (nenhuma credencial tocada) |
| downloader reproduzível | `PASS` (dry-run, 11 componentes; verificação na Wave 3) |

**Veredito recomendado de Gate A: `INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING`** (0/8 sub-fontes com 6/6 critérios).

### Regra de rótulos — VINCULANTE para o finalizador
| Rótulo observado | NÃO pode ser convertido em |
|---|---|
| `PARTIAL` | `PASS` |
| `UNKNOWN_UNVERIFIED` | `FAIL` |
| `DEFERRED` | `NOT_EXECUTABLE` |
| `AUTOMATED_CHECK_PASS` (auto-checagem) | validação independente |

As 9 respostas do §2: **P1–P4 `PARTIAL`**, **P5–P8 `UNKNOWN_UNVERIFIED`**, **P9 `DEFERRED`**.

### Bloqueios que exigem decisão humana
1. Leitura dos Termos FACEIT + submissão da aplicação ao Downloads API (HTTP 403 nos termos; `application_submitted: false`).
2. Aprovação do instrumento de consentimento da Fonte D.
3. Compatibilidade da licença CC BY-NC-SA 4.0 (PureSkill CS2 CSDS) com o enquadramento do projeto.

## Gate — Iteração 1
| Agent | Role | Verdict | Source |
|-------|------|---------|--------|
| researcher_2a_int_1 | Data Acquisition Researcher (M2) | DONE — `INTERMEDIATE_CORPUS_ACQUISITION_ACCESS_PENDING` (auto-declarado; 5/5 hashes verificados por Orchestrator e Sentinel) | handoff + recálculo |
| implementer_core_2a_int_1 | Dataset and Metadata Implementer (M0, M1, M3) | M0 PASS; M1/M3 EM EXECUÇÃO (artefatos já materializados, handoff pendente) | disco |
| implementer_data_2a_int_1 | Manifests and Tests Implementer (M4, M7, M8) | EM EXECUÇÃO | — |
| analyst_2a_int_1 | Spatial and Statistical Analyst (M5, M6) | EM EXECUÇÃO | — |

Gate Result: **EM EXECUÇÃO**

## Gate — Wave 3 (3 auditorias independentes). Registro: 2026-11-09T01:39Z

| Agent | Role | Verdict | Source |
|-------|------|---------|--------|
| math_stat_auditor_2a_int_1 | Mathematical/Statistical Auditor | `CONDITIONAL` (1 MAJOR §14 + 3 MINOR) | `parecer_mathematical_audit.md` 33207 B `054192bc99aa706d365f7dbec53bd80f264a1215f92f2386bda26fd594602645` |
| adversarial_auditor_2a_int_1 | Adversarial Success Auditor | `CONDITIONAL` (V1 + V2 HIGH) | `parecer_adversarial_audit.md` 31490 B `12b9f16f88129b3bc1768934ae66e42f50ff4e8d1e35e118f61781567229cad7` |
| provenance_auditor_2a_int_1 | Data Provenance and Compliance Auditor | `CONDITIONAL` (R1 bloqueia; R2–R8) | `parecer_provenance_audit.md` 42063 B `927488363073ad64ef8048fd1705c32f075dd939c2b29adc63219c1f79ac4844` |

Gate Result: **CONDITIONAL** — nenhuma auditoria emitiu `FAIL`; as três bloquearam o `PASS` por convergência independente sobre **fidelidade de proveniência (V2 ≡ R1)** e, em segundo lugar, **§14 (7/15 métricas circulares)**.

### Achados que bloqueiam o PASS (consolidados)
| # | Achado | Origem | Correção exigida |
|---|---|---|---|
| B1 | `VERIFIED_ONLINE` **163×** nos 4 entregáveis do pesquisador com `RECAPTURED`/`REPORT_TO_SOURCE`/`EVIDENCE_LOSS` **0×** — `(0/163)`; capturas sobreviventes são de 01:09:09–01:09:17Z contra janela declarada 00:51–00:56Z ⇒ `(0/5)` no instante declarado | Adversarial V2 + Proveniência R1 | Rotular E1–E25 + topo do §12; nota de `EVIDENCE_LOSS_EVENT` dentro de entregável do §21 |
| B2 | 20/25 evidências citadas sem captura materializada; frase de `source_feasibility_report.md` L812 ("Todas as URLs abaixo foram recuperadas nesta sessão") falsa para 20/25 | Adversarial V1 | Rebaixar para `UNVERIFIED_NO_MATERIALIZED_CAPTURE`; corrigir L812 e `INDEX.md` L7–L8 |
| B3 | **7/15** métricas do §14 (`PVSI_01, 04, 09, 10, 12, 14, 15`) com JSD e Wasserstein mutuamente circulares (`applicable=false` em ambas) | Matemático MAJOR | Estado único e não circular por métrica: `JSD aplicável` / `Wasserstein aplicável` / `NOT_A_DISTRIBUTION` com fundamento |
| B4 | `round_outcome_dependency = true` afirmado em texto mas **ausente** nas 32 métricas CT+TR | Matemático MINOR 2 | Adicionar o campo nas 32 entradas |
| B5 | 5 `.pyc` `TRANSIENT_CACHE` presentes (estado alvo 11 arquivos não atingido) | Proveniência R4 | Remoção física **após** a última execução de teste + recontagem = 11 |
| B6 | 7 entregáveis do §21 não materializados | Proveniência R5 | Materializar (tarefa do Orchestrator) |
| B7 | Suíte C# não executada por auditor | Adversarial (lacuna) | Auditor independente executa `dotnet test` e reporta contagem real |

### Ressalvas aceitas como registradas, sem correção (decisão fundamentada)
`R3` schema de `pilot_download_manifest.json` (`KNOWN_SCHEMA_ASYMMETRY`) · `R6` `403` vs `404` no artigo de Elo (`UNRESOLVED_DETAIL_DIVERGENCE`) · `R7` despacho "16 campos" vs literal **17** (meu erro de contagem nº 3) · `R8` `overlap_percentage` (nenhuma violação da Regra 03) · `bombsite` divergente em 4/53 spots (`UNRESOLVED_DISCREPANCY`, artefato preservado, §1 + Regra 06) · `F12` índice genérico (`ABSENCE_OF_PROOF_PRESERVED`).

## Gate — Wave 4 (correção + reauditoria) — EM EXECUÇÃO

| Etapa | Responsável | Estado |
|---|---|---|
| W4.1 Correção cirúrgica (B1, B2, B3, B4 + rótulo `dispatch_declared`) | `fix_corrections_2a_int_1` (contexto limpo) | DESPACHADO 2026-11-09T01:40Z |
| W4.2 Atualização de hashes, `ARTIFACT_INVENTORY.md` e matriz; 3 pareceres → `AUDITED_ARTIFACT_SUPERSEDED` | Orchestrator | PENDENTE (depende de W4.1) |
| W4.3 Reauditoria com 3 auditores **novos** (B1–B4 fechados, B5/B7 executados por auditor, 95 artefatos recalculados, segredos reescaneados) | auditores novos | PENDENTE |
| W4.4 Materialização dos 7 entregáveis do §21 (B6) + relatório final `CONDITIONAL` | Orchestrator | PENDENTE |
| W4.5 Remoção de `__pycache__` + recontagem 11 arquivos (B5) — **por último** | Orchestrator | PENDENTE |

**Nenhum `PASS` será emitido antes de W4.3 concluída.**
