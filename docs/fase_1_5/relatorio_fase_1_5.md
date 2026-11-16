# Relatório Consolidado — Fase 1.5: Validação Espacial do Perfil Mirage e Contrato de Movimento V2

> [!IMPORTANT]
> **Integridade do Runtime Preservada**: Conforme determinado na especificação da Fase 1.5, o arquivo [`src/CsBotManager/MapProfiles/de_mirage.json`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/src/CsBotManager/MapProfiles/de_mirage.json) **NÃO foi alterado** e **nenhum treinamento foi iniciado**. Todas as coordenadas propostas abaixo são **Medoids reais observados** (posições exatas de jogadores profissionais em episódios de *hold* estacionário) prontas para revisão humana e inspeção via `setpos`.

---

## 1. Revisão Matemática e Física da Inflação de `Jump` (`18,0x` vs `24,1x` vs `32,4x`)

Arquivo de auditoria: [`docs/fase_1_5/jump_label_audit_v2.json`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_5/jump_label_audit_v2.json) | Script: [`tools/mlmove_pipeline/phase15_jump_audit.py`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/phase15_jump_audit.py).

### 1.1. Por que o relatório da Fase 1 exibiu `18,0x` quando `8,13% / 0,338% = 24,05x`?

No script da Fase 1 ([`tools/mlmove_pipeline/catalog_mirage_demos.py`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/tools/mlmove_pipeline/catalog_mirage_demos.py#L430-L433)), foram contabilizados sobre o universo de **`29.082.040` frames vivos**:
- **Numerador (`old_jump_labeled_frames`)**: $|v_z| > 45\text{ u/s} \implies \mathbf{2.363.125}\text{ frames}$ ($\mathbf{8,1257\%}$).
- **Denominador Bruto (`true_jump_onset_frames`)**: Transições de subida com $v_z[t] \ge 140\text{ u/s}$ e $v_z[t-1] < 50\text{ u/s}$, **incluindo** saltos encadeados (*bunny hops*) $\implies \mathbf{131.290}\text{ frames}$ ($\mathbf{0,4514\%}$).
- **Episódios de BunnyHop (`bunny_hop_episodes_detected`)**: Pares de *onsets* separados por $\le 20\text{ steps}$ ($1,25\text{s}$) $\implies \mathbf{32.788}\text{ frames}$ ($\mathbf{0,1127\%}$).
- **Denominador Líquido (`net_single_jump_onsets`)**: $131.290 - 32.788 = \mathbf{98.502}\text{ frames}$ ($\mathbf{0,3387\%}$).

A discrepância ocorreu porque o script da Fase 1 calculou o fator de inflação usando o **denominador bruto** (`131.290`), mas a tabela Markdown exibiu na linha do `JumpOnset` a porcentagem do **denominador líquido** (`0,3387%`):

$$\text{Fator Bruto (com BunnyHop)} = \frac{2.363.125}{131.290} = \frac{8,1257\%}{0,4514\%} = \mathbf{18,00\text{x}}$$

$$\text{Fator Líquido (sem BunnyHop)} = \frac{2.363.125}{98.502} = \frac{8,1257\%}{0,3387\%} = \mathbf{23,99\text{x}} \quad \left(\text{ou } \frac{8,13\%}{0,338\%} = \mathbf{24,05\text{x}}\right)$$

### 1.2. Como `JumpOnset` foi detectado e Auditoria de Sinais (`IN_JUMP`, `grounded`, `takeoff`, `vz`, `edge transition`)

Para verificar a qualidade de cada sinal físico, auditamos diretamente as **8 demos `.dem` brutas a 64Hz** (`2.704.920` ticks vivos) e os **444 arquivos `.npz` a 16Hz** (`29.082.040` steps vivos):

| Sinal / Critério | Presença nas `.dem` (64Hz) | Presença nos `.npz` (16Hz) | Diagnóstico Técnico na Auditoria (Fase 1.5) |
| :--- | :---: | :---: | :--- |
| **Botão `IN_JUMP` (`buttons & 2`)** | Sim | **Não** | Em demos GOTV/CSTV subtick do CS2, o pulso de `IN_JUMP` (especialmente via *scroll wheel*) dura frequentemente 1 subtick e cai entre snapshots de rede: **apenas `40,1%` dos takeoffs físicos reais têm `IN_JUMP=1` visível no tick**, e apenas `56,8%` das bordas de subida de `IN_JUMP` geram decolagem real. **Não deve ser usado isoladamente como ground truth.** |
| **Flag `grounded` / `is_airborne`** | Sim | **Não** | Nas `.dem` brutas, `is_airborne` é `true` em **`99,7%`** dos *takeoffs* em $t+2$ ticks. Porém, essa coluna não foi exportada para os 444 `.npz`. |
| **Velocidade Vertical (`velocity_Z`)** | Sim | Sim (`X[:,:,5] * 250`) | No CS2, o impulso inicial de pulo em superfície plana é $v_{z0} \approx 301,99\text{ u/s}$ com gravidade $g = -800\text{ u/s}^2$ ($\Delta v_z \approx -50\text{ u/s}$ por step de $62,5\text{ms}$ a 16Hz). |
| **Edge Transition + Decaimento Balístico (Detector V2)** | Sim | Sim | Exige simultaneamente: **(1)** estado prévio próximo ao solo ($-40 \le v_z[t-1] \le 60\text{ u/s}$); **(2)** borda positiva de decolagem ($120 \le v_z[t] < 600\text{ u/s}$ e $v_z[t] - v_z[t-1] \ge 100\text{ u/s}$); **(3)** desaceleração gravitacional livre no passo seguinte ($-85 \le v_z[t+1] - v_z[t] \le -20\text{ u/s}$), eliminando falsos positivos de rampas/escadas; **(4)** continuidade espacial 3D ($\le 60\text{u}$). |

### 1.3. Tabela Corrigida de Inflação de `Jump` (Fase 1 vs. Detector Balístico V2)

| Métrica | Contagem de Frames (`29.082.040` vivos) | % dos Frames Vivos | Fator de Inflação do Label V1 (`2.363.125` frames) |
| :--- | :---: | :---: | :---: |
| **Label V1 Legado (`\|vz\| > 45 u/s`)** | `2.363.125` | `8,1257%` | `1,00x` (baseline ruidoso) |
| **Fase 1 — Bruto (com BunnyHop)** | `131.290` | `0,4514%` | **`18,00x`** |
| **Fase 1 — Líquido (sem BunnyHop)** | `98.502` | `0,3387%` | **`23,99x`** (`24,05x` arredondado) |
| **Fase 1.5 Balístico V2 — Bruto (todos os takeoffs)** | `84.404` | `0,2902%` | **`28,00x`** |
| **Fase 1.5 Balístico V2 — Chained/BunnyHop (`vz[t-1] < -40`)** | `11.547` | `0,0397%` | *(excluído do treino)* |
| **Fase 1.5 Balístico V2 — Líquido (`JumpPress` limpo)** | **`72.857`** | **`0,2505%`** | **`32,43x`** |

---

## 2. Contrato de Movimento V2 (`movement_contract_v2.json`)

Arquivo: [`docs/fase_1_5/movement_contract_v2.json`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_5/movement_contract_v2.json).

O Contrato V2 separa rigorosamente **locomoção horizontal**, **modificadores de postura**, **evento discreto de salto** e **estado físico (somente leitura)**:

1. **`BaseMovement` (Cabeça Multiclasse Exclusiva — 5 classes)**:
   - `0: Stop` ($v_{2D} < 20\text{ u/s}$)
   - `1: Forward` ($\cos\theta > 0,3827$)
   - `2: Backward` ($\cos\theta < -0,3827$)
   - `3: StrafeLeft` ($|\cos\theta| \le 0,3827, \sin\theta > 0$)
   - `4: StrafeRight` ($|\cos\theta| \le 0,3827, \sin\theta < 0$)
2. **`Modifiers` (Cabeças Binárias Independentes — 2 canais)**:
   - `Shift` (Walk: $20 \le v_{2D} \le 135\text{ u/s}$ em `Grounded`)
   - `Duck` (Crouch: `IN_DUCK` / redução de cota de olho em `Grounded`)
3. **`Event` (Cabeça Binária de Pulso de 1 Step — 1 canal)**:
   - `JumpPress`: Positivo **exclusivamente** no frame de *takeoff* balístico único (`72.857` eventos = `0,2505%` do dataset).
4. **`PhysicalState` (Feature de Contexto / Somente Leitura — 4 estados)**:
   - `Grounded`, `Airborne` ($v_z > 45\text{ u/s}$ pós-takeoff), `Falling` ($v_z < -45\text{ u/s}$), `Landing` (retorno ao solo).
   - **Proibições explícitas no contrato**:
     - `forbid_airborne_or_falling_as_jump_label = true` (frames em `Airborne`, `Falling` e `Landing` recebem `JumpPress = 0`).
     - `forbid_bunnyhop_as_executable_action = true` (`BunnyHop` não existe como classe; os `11.547` *chained takeoffs* têm `JumpPress` mascarado para `0`).

---

## 3. Auditoria Espacial dos 45 Spots do `de_mirage.json` e Clustering 3D

- Auditoria completa JSON: [`docs/fase_1_5/mirage_spot_audit.json`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_5/mirage_spot_audit.json)
- Catálogo de 176 clusters 3D JSON: [`docs/fase_1_5/mirage_spot_clusters.json`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_5/mirage_spot_clusters.json)
- Proposta detalhada e comandos `setpos`: [`docs/fase_1_5/mirage_spot_change_proposal.md`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_5/mirage_spot_change_proposal.md)
- Mapa visual SVG: [`mirage_spot_audit_map.svg`](file:///C:/Users/ricar/.gemini/antigravity/brain/d65e2bde-5cae-4311-b714-4707e256a192/mirage_spot_audit_map.svg)

![Mapa de Auditoria Espacial dos 45 Spots da Mirage vs. 176 Clusters 3D Profissionais](C:/Users/ricar/.gemini/antigravity/brain/d65e2bde-5cae-4311-b714-4707e256a192/mirage_spot_audit_map.svg)

### 3.1. Metodologia Aplicada (Itens 3, 4, 5 e 6)
1. **Remoção de Passagem e Exigência de Permanência Mínima**: Extraídos apenas episódios contínuos onde o jogador vivo manteve $v_{2D} < 35\text{ u/s}$ por $\ge 24\text{ steps}$ ($\ge 1,5\text{s}$) sem derivar mais de $64\text{u}$ de sua posição mediana ($\mathbf{69.320}\text{ holds}$ válidos; `446` descartados por deriva).
2. **Separação por Altura e Clustering 3D**: Picos de densidade em grade 2D de $24\text{u}$ fatiada em bandas verticais de $56\text{u}$ (separando pisos sobrepostos como **Under-Palace** em $Z=-168$ vs. **Palace Balcony/Interior** em $Z=-40$, e **Underpass** em $Z=-364/-264$ vs. **Apartments/Ladder** em $Z=-56/-48$). Resultou em **176 clusters 3D**.
3. **Medoid Real em vez de Média/Mediana Global**: Para cada cluster, foi selecionado o **Medoid** (amostra física real de um jogador profissional que minimiza a distância 3D ponderada para o cluster), evitando que a coordenada caia dentro de caixas ou paredes.
4. **Filtragem por Lado, Fase, Papel (AWP) e Sub-Região de Landmark**: Antes de propor qualquer coordenada para um spot, os clusters foram filtrados por `TeamSide` (`CT` vs `TR`), fase do round (`setup/mid <= 65s`, `staging <= 50s`, `execute >= 18s`, `retake >= 35s`), arma (`awp_only` para spots de AWP) e caixa delimitadora 3D do sub-landmark (`Ticket`, `Firebox`, `Ninja`, `Triple`, `Under-Palace`, `Stairs`, `Jungle`, `Connector`, `T Roof`).

### 3.2. Síntese das Classificações dos 45 Spots Atuais

| Classificação | Total | Spots Afetados |
| :--- | :---: | :--- |
| **`WRONG_SECTOR`** | **19** | `ct_a_ticket_passive`, `ct_a_firebox_oneanddone`, `ct_a_ninja_hide`, `ct_a_triple_jiggle`, `ct_a_stairs_cross`, `ct_a_jungle_support`, `ct_a_palace_close_poke`, `ct_mid_window_crouch`, `ct_mid_window_deep_awp`, `ct_mid_connector_headshot`, `ct_mid_short_catwalk`, `ct_mid_underpass_peek`, `ct_b_van_peek`, `ct_b_market_window`, `ct_spawn_safe`, `tr_staging_a_ramp`, `tr_staging_palace_room`, `tr_staging_underpass_top`, `ct_retake_a_jungle` |
| **`WRONG_HEIGHT`** | **1** | `ct_retake_a_connector` (atual `[-450, -1600, -160]` cai em `BombsiteA`/`Stairs` fora da cota do piso; proposto Medoid no `Connector` real `[-802.4, -1221.3, -168.0]`) |
| **`SMALL_ADJUSTMENT`** | **12** | `ct_b_site_default_crouch`, `ct_b_market_door`, `tr_staging_b_apartments_house`, `tr_exec_a_site_default`, `tr_exec_a_stairs_clear`, `tr_exec_mid_connector_push`, `tr_exec_b_site_plant`, `tr_exec_b_market_push`, `ct_retake_a_stairs`, `ct_retake_a_defuse_cover`, `ct_retake_b_market`, `ct_retake_b_defuse_cover` |
| **`INSUFFICIENT_EVIDENCE`** | **6** | `tr_staging_top_mid_boxes`, `tr_staging_t_roof`, `tr_spawn_safe`, `tr_exec_b_van_clear`, `ct_retake_b_entry`, `ct_retake_b_awp_cover` *(todos possuem candidato Medoid proposto no setor correto)* |
| **`VALID`** | **7** | `ct_b_bench_deep`, `ct_b_short_corner`, `ct_jungle_safe`, `tr_staging_b_apartments_kitchen`, `tr_exec_a_triple_clear`, `ct_retake_a_ticket`, `ct_retake_b_short` |
| **`AMBIGUOUS` / `UNREACHABLE`** | **0** | Nenhum spot caiu em vazio geométrico sem cobertura empírica. |

---

## 4. Protocolo de Mudanças Controladas e Validação em Runtime (Itens 7 e 8 — Pós-Aprovação)

Assim que você revisar e aprovar [`mirage_spot_change_proposal.md`](file:///C:/Users/ricar/OneDrive/Documentos/Dev/CsBot/brain/d65e2bde-5cae-4311-b714-4707e256a192/mirage_spot_change_proposal.md), executaremos estritamente a seguinte sequência:

1. **Backup Imutável**: Copiar `src/CsBotManager/MapProfiles/de_mirage.json` para `src/CsBotManager/MapProfiles/backups/de_mirage.v1_backup.json`.
2. **Atualização Cirúrgica**:
   - Atualizar **somente** os 20 spots comprovadamente errados (`19 WRONG_SECTOR` + `1 WRONG_HEIGHT`) e, se autorizado, os spots de `INSUFFICIENT_EVIDENCE`/`SMALL_ADJUSTMENT` selecionados (`tr_staging_t_roof`, `tr_staging_top_mid_boxes`, etc.).
   - Preservar 100% dos `SpotId`s existentes para não quebrar referências nos `TacticalPresets`.
   - Incrementar `map_profile_version` no JSON (`1` $\rightarrow$ `2`) e salvar o log de auditoria `old_position -> new_position` com motivo.
3. **Validação Compilada e Testes de Rota/Presets**:
   - Executar `dotnet build -c Release` e a suíte de testes (`dotnet test`) validando o `MapProfileLoader` e todos os presets táticos da Mirage.
   - Fazer deploy das DLLs e do `de_mirage.json` atualizado para `H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\` e verificar hashes SHA256.
4. **Validação Visual em Runtime (`!debug 5`)**:
   - Iniciar partida de validação na Mirage com o sistema atual (`MLMove V1` + `Utility AI`) e `!debug 5`.
   - Confirmar visualmente e via telemetria que os bots alcançam sem travar: **Ticket (`ct_a_ticket_passive`)**, **Stairs (`ct_a_stairs_cross`)**, **Ramp (`tr_staging_a_ramp`)**, **Palace (`tr_staging_palace_room`)** e **T Roof (`tr_staging_t_roof`)**.

---

## 5. Índice dos 6 Entregáveis Obrigatórios da Fase 1.5

1. [`docs/fase_1_5/mirage_spot_audit.json`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_5/mirage_spot_audit.json) — Auditoria completa dos 45 spots com todos os 15 campos exigidos e candidatos ranqueados.
2. [`docs/fase_1_5/mirage_spot_clusters.json`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_5/mirage_spot_clusters.json) — Catálogo dos 176 clusters 3D com `centroid`, `medoid`, `sample_count`, `unique_demos`, `unique_player_instances`, `median_dwell_s`, `ct_ratio`, `tr_ratio`, `awp_ratio`, `movement_state` e `cluster_confidence`.
3. [`docs/fase_1_5/mirage_spot_change_proposal.md`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_5/mirage_spot_change_proposal.md) — Tabela comparativa completa e comandos `setpos` antes/depois para inspeção manual.
4. [`docs/fase_1_5/jump_label_audit_v2.json`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_5/jump_label_audit_v2.json) — Reconciliação matemática exata (`18,0x` vs `24,0x` vs `28,0x` vs `32,4x`) e auditoria de sinais `IN_JUMP`, `is_airborne` e detector balístico V2.
5. [`docs/fase_1_5/movement_contract_v2.json`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_5/movement_contract_v2.json) — Contrato formal V2 separando `BaseMovement`, `Modifiers`, `Event: JumpPress` e `PhysicalState`.
6. [`docs/fase_1_5/relatorio_fase_1_5.md`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_5/relatorio_fase_1_5.md) — Este relatório consolidado.

---

## 6. Decisão Final Explícita da Fase 1.5

```text
MIRAGE_PROFILE_NOT_READY_FOR_V2_DATASET
```

**Justificativa**: A auditoria espacial comprovou que **20 dos 45 spots atuais** do `de_mirage.json` (`19 WRONG_SECTOR` + `1 WRONG_HEIGHT`, além de `tr_staging_t_roof` e `tr_staging_top_mid_boxes` com coordenadas fora dos clusters reais de staging) estão com coordenadas legadas incorretas, e conforme a regra da seção 6 (*"Não alterar o JSON até a revisão"*), o `de_mirage.json` permanece intocado aguardando sua aprovação das coordenadas propostas em [`mirage_spot_change_proposal.md`](file:///c:/Users/ricar/OneDrive/Documentos/Dev/CsBot/docs/fase_1_5/mirage_spot_change_proposal.md). Assim que você autorizar a aplicação controlada (Seção 7) e validarmos no runtime (Seção 8), o status passará para `MIRAGE_PROFILE_READY_FOR_V2_DATASET`.
