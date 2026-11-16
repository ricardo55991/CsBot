# CsBot - Telemetria Forense de Partida
**Data/Hora:** 2026-11-04 22:13:12 | **Mapa:** de_mirage
**Status:** Gravação Ativa | **Arquivo:** `debug_match_20261104_221312.md` | **Motor MLMove:** `[Modo ONNX Ativo] ONNX-CPU-L3 (mlmove_de_mirage.onnx | 0.69ms)`

### 🛡️ Identificadores de Versão e Integridade
- **PluginVersion:** `1.3.0`
- **AssemblyVersion:** `1.0.0.0`
- **GitCommit:** `v4.2-release`
- **DllSha256:** `ccae06729c7921e1823448b8bf2923c84f2a526ee08dea8a664df0fd516b6794`
- **ModelSha256:** `6ce07226d84c8b3ff812500f85d7e0be855eac3b917ed58486501b7404a5a522`


### ⚙️ Parâmetros Configuráveis Ativos (BotSystemConfig V4)
- **Stuck 2D:** janela=`3.5s`, deslocamento_min=`40u`, progresso_alvo_min=`25u`, cooldown_waypoint=`12.0s`
- **StandStill & Parada Física:** max_agressivo=`1.60s`, max_defensivo=`5.00s`, low_speed=`10.0u/s`, reset_speed=`20.0u/s`, min_disp=`5.0u`, cooldown=`1.5s`
- **Arbitragem & Tracker:** histerese=`8 ticks`, max_speed_2d=`250 u/s`, tickrate=`64Hz`, progresso_500ms=`[5u, 20u]`
- **Trade Spacing & Wide Swing:** repulsao_min=`140u`, pair_cooldown=`2.5s`, nav_offset=`145u`, wide_swing_window=`[250u, 400u]` (2D)
- **Counter-Strafe:** cooldown=`2.5s`, max_aim_error=`16.0°`, min_speed_2d=`65 u/s`
- **Bombsite Clear & Pivôs:** permanencia_min=`2.0s`, confianca_min=`0.75`, raio_plant_2d=`320u`
- **Economia & IGL:** pistol_rounds=`[1, 13]`, full_buy_equip=`$3600`, ollama_timeout=`8.5s`, repetition_penalty=`35.00`


---


<details><summary><b>📊 Snapshot Tático das [01:55] (10 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | glock | TR Spawn | `1187,393,-252` | `2°,167°` | 240.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_house)) | Pending | Movendo |
| 2 | Ricksaw (AWPer) | CT | 100 | hkp2000 | CT Spawn | `-1565,-1435,-264` | `2°,81°` | 229.6 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_bench_deep)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | glock | TR Spawn | `1026,407,-258` | `2°,142°` | 240.0 | PASSIVE_HOLD | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | CT Spawn | `-1698,-1746,-265` | `2°,79°` | 3.7 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_short_corner)) | Pending | None |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1532,-1276,-260` | `2°,74°` | 240.0 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_market_window)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | glock | TR Spawn | `1112,200,-163` | `2°,124°` | 224.4 (Z -112 / 3D 251 aéreo) | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | glock | TR Spawn | `1159,339,-224` | `2°,140°` | 233.1 (Z -87 / 3D 249 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | hkp2000 | CT Spawn | `-1531,-1073,-224` | `2°,35°` | 240.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_mid_short_catwalk)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1570,-1769,-266` | `2°,100°` | 240.0 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | glock | TR Spawn | `1111,277,-249` | `2°,116°` | 226.8 (Z -387 / 3D 449 aéreo) | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>


<details><summary><b>📊 Snapshot Tático das [01:55] (10 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | glock | Beco | `518,472,-260` | `1°,-147°` | 240.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_house)) | Pending | Movendo |
| 2 | Ricksaw (AWPer) | CT | 100 | hkp2000 | CT Spawn | `-1414,-959,-168` | `1°,29°` | 16.6 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_bench_deep)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | glock | Apartamentos B | `569,678,-136` | `1°,161°` | 84.9 | PASSIVE_HOLD | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | CT Spawn | `-1606,-1221,-260` | `1°,85°` | 228.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_short_corner)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1455,-903,-168` | `1°,23°` | 123.4 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_market_window)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | glock | TR Spawn | `867,486,-253` | `1°,-176°` | 124.8 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | glock | TR Spawn | `762,585,-156` | `1°,-162°` | 197.5 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | hkp2000 | CT Spawn | `-1363,-964,-168` | `0°,-6°` | 42.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_mid_short_catwalk)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1640,-1226,-259` | `1°,43°` | 63.6 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | glock | TR Spawn | `1014,429,-208` | `1°,154°` | 191.8 (Z 161 / 3D 251 aéreo) | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[01:55]`** `[MLMOVE - TRADE SPACING]` **Syfers** (`yielding_slot=8`) cedeu espaço para **Ricksaw** (`priority_slot=2`) | `dist_before=115u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=2`.
- **`[01:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Hotzone_PreMapped` em `(-1617, -678, -168)` [Mira: Yaw 142° | CPU: `0.74ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Diag-Esq(250u)`

<details><summary><b>📊 Snapshot Tático das [01:55] (10 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | glock | Top Mid | `208,-30,-185` | `-1°,-97°` | 181.1 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_house)) | Pending | Movendo |
| 2 | Ricksaw (AWPer) | CT | 100 | hkp2000 | CT Spawn | `-1321,-983,-168` | `-1°,38°` | 14.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_bench_deep)) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 100 | glock | Apartamentos B | `120,826,-136` | `-1°,-168°` | 180.4 | PASSIVE_HOLD | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | Mercado / Kitchen | `-1624,-638,-168` | `-1°,139°` | 14.9 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Diag-Esq(Duck) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act37) | Pending | None |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1392,-950,-168` | `-1°,-22°` | 27.0 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_market_window)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | glock | TR Spawn | `1024,398,-257` | `-1°,-32°` | 100.8 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | glock | Beco | `241,365,-254` | `-1°,-92°` | 225.9 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | hkp2000 | CT Spawn | `-1227,-950,-168` | `-1°,60°` | 0.0 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Diag-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act37) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1500,-1025,-159` | `-1°,36°` | 187.5 (Z 161 / 3D 247 aéreo) | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | glock | TR Spawn | `752,641,-149` | `-1°,-171°` | 201.4 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

## 🎮 Round 1 [Placar: CT 0 x 0 TR]
- **internal_round_id:** `1` | **display_round_number:** `1` | **round_in_half:** `1` | **match_phase:** `LIVE` | **round_phase:** `ROUND_ACTIVE` | **start_tick:** `5581`
- **Motor Micro-Movimento (16Hz):** `[Modo ONNX Ativo] ONNX-CPU-L3 (mlmove_de_mirage.onnx | 0.76ms)`

### 💵 Economia por Time (Pré-compra vs Pós-compra)
| Time | PreBuyIntent | FinalBuyState | Completion | Caixa Médio Antes | Caixa Médio Depois | Gasto | Equip Antes | Equip Depois | Primárias | Rifles | SMGs | AWPs | Coletes | Capacetes | Kits | Utilitárias ($) | LossBonus |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| CT | `PISTOL_ROUND` | `PISTOL_ROUND` | `STABILIZED` | $2480 | $1620 | $4300 | $1000 | $4900 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | $1300 | $1400 |
| TR | `PISTOL_ROUND` | `PISTOL_ROUND` | `STABILIZED` | $3700 | $2850 | $4250 | $1650 | $5250 | 0 | 0 | 0 | 0 | 5 | 0 | 0 | $1000 | $1400 |

### 💰 Loadout Pós-Compra
| Slot | Jogador | Time | Role | Dinheiro | Arma Primária | Arma Secundária | Utilitárias | Colete/Kit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark | TR | AWPer | $2850 | Nenhuma | GLOCK | FLASHBANG | Colete (100) |
| 2 | Ricksaw | CT | AWPer | $2000 | Nenhuma | HKP2000 | FLASHBANG | Colete (100) |
| 3 | Delrow | TR | EntryFragger | $3150 | Nenhuma | GLOCK | FLASHBANG | Colete (100) |
| 4 | Commando | CT | EntryFragger | $1700 | Nenhuma | HKP2000 | FLASHBANG | Colete (100) |
| 5 | Soldier | CT | Rotator | $1400 | Nenhuma | HKP2000 | FLASHBANG | Colete (100) |
| 6 | Shamat | TR | Rotator | $2550 | Nenhuma | GLOCK | FLASHBANG | Colete (100) + 💣 C4 (Bomba) |
| 7 | Rebel | TR | Anchor | $2850 | Nenhuma | GLOCK | FLASHBANG | Colete (100) |
| 8 | Syfers | CT | Anchor | $1600 | Nenhuma | HKP2000 | SMOKEGRENADE, FLASHBANG | Sem Colete |
| 9 | Buckshot | CT | Rotator | $1400 | Nenhuma | HKP2000 | FLASHBANG | Colete (100) |
| 10 | Steel | TR | Rotator | $2850 | Nenhuma | GLOCK | FLASHBANG | Colete (100) |

#### 🤖 Auditoria IGL CT
- **decision_id:** `R1_CT_CT_ECO_STACK_GAMBLE_B_96e783` | **source:** `UTILITY_AI_ENGINE` | **latency:** `15ms` | **cache_hit:** `False` | **fallback:** `False` (NONE) | **parse:** `OK`
- **InitialTactic:** `Gamble Eco Stack B (Emboscada Tapete)` | **CurrentTactic:** `Gamble Eco Stack B (Emboscada Tapete)` | **TacticRevision:** `1` | **Ritmo:** `FAST_CONTACT` | **Tier:** `Tier2_Moderate`
- **Candidatas:** CT_ECO_STACK_GAMBLE_A (90.0); CT_ECO_STACK_GAMBLE_B (90.0); CT_RETAKE_PASSIVE_SETUP (70.0) | **penalidade_repetição:** `False`
- **Resumo:** Formação de Eco/Pistola com 3 defensores em ângulos curtos no Bomb B + 1 Underpass.

#### 🤖 Auditoria IGL TR
- **decision_id:** `R1_TR_TR_EXEC_B_APARTMENTS_RUSH_1e2547` | **source:** `UTILITY_AI_ENGINE` | **latency:** `7ms` | **cache_hit:** `False` | **fallback:** `False` (NONE) | **parse:** `OK`
- **InitialTactic:** `Execução Rápida Tapete B (Rush Apartamentos)` | **CurrentTactic:** `Execução Rápida Tapete B (Rush Apartamentos)` | **TacticRevision:** `1` | **Ritmo:** `FAST_CONTACT` | **Tier:** `Tier1_Standard`
- **Candidatas:** TR_EXEC_B_APARTMENTS_RUSH (90.0); TR_EXEC_A_PALACE_RAMP_SPLIT (50.0); TR_SPLIT_A_MID_TO_CONNECTOR (50.0) | **penalidade_repetição:** `False`
- **Resumo:** Explosão coordenada pelo Tapete B com limpeza da Van, Banco e contenção da Janela do Mercado.

### ⏱️ Linha do Tempo de Eventos
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Hotzone_PreMapped` em `(-1245, -936, -113)` [Mira: Yaw 55° | CPU: `0.63ms`] -> Horizontes: **0ms:** `Diag-Esq(Duck+Jump)` | **125ms:** `Diag-Esq(250u+Jump)` | **250ms:** `Avanco(250u+Jump)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Vision_Spotted` em `(-279, 720, -98)` [Mira: Yaw -159° | CPU: `0.62ms`] -> Horizontes: **0ms:** `Diag-Dir(250u)` | **125ms:** `Diag-Dir(250u)` | **250ms:** `Diag-Dir(250u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Vision_Spotted` em `(72, -494, -177)` [Mira: Yaw 175° | CPU: `0.71ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Audio_HeardCue` em `(240, -181, -168)` [Mira: Yaw -143° | CPU: `0.71ms`] -> Horizontes: **0ms:** `Diag-Dir(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Diag-Dir(250u)`
- **`[03:33]`** `[MLMOVE - TRADE SPACING]` **Soldier** (`yielding_slot=5`) cedeu espaço para **Ricksaw** (`priority_slot=2`) | `dist_before=66u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=10`.
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Syfers** acionou `Vision_Spotted` em `(-1130, -704, -142)` [Mira: Yaw 42° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Diag-Dir(Duck+Jump)` | **125ms:** `Avanco(Duck+Jump)` | **250ms:** `Strafe-Dir(Duck)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Audio_HeardCue` em `(-1489, -1135, -239)` [Mira: Yaw 54° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck)` | **125ms:** `Parado (0u)` | **250ms:** `Strafe-Esq(Shift)`

<details><summary><b>📊 Snapshot Tático das [03:33] (10 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | glock | Top Mid | `46,-496,-181` | `-2°,-172°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 2 | Ricksaw (AWPer) | CT | 100 | hkp2000 | CT Spawn | `-1231,-916,-130` | `-2°,44°` | 0.0 | PASSIVE_HOLD | Nenhuma | MicroMove:HoldStop(ONNX_Audio_HeardCue_StandStill) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 100 | glock | Beco | `-497,579,-81` | `-2°,-177°` | 204.9 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Diag-Dir(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_house)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | Mercado / Kitchen | `-1832,-607,-168` | `-2°,102°` | 208.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_short_corner)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1253,-948,-168` | `-2°,57°` | 0.0 | JIGGLE_INFO | ONNX_Audio_HeardCue | Diag-Esq(Duck) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act33) | Pending | None |
| 6 | Shamat (Rotator) | TR | 100 | glock | TR Spawn | `1288,313,-230` | `-2°,-91°` | 124.8 | JIGGLE_INFO | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | glock | Top Mid | `231,-221,-168` | `-2°,-155°` | 0.0 | PASSIVE_HOLD | Nenhuma | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act28) | Pending | None |
| 8 | Syfers (Anchor) | CT | 100 | hkp2000 | Janela | `-1130,-670,-126` | `4°,13°` | 91.0 (Z -108 / 3D 141 aéreo) | PASSIVE_HOLD | ONNX_Vision_Spotted | Strafe-Dir(Duck+Jump) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act85) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1493,-1132,-238` | `-2°,92°` | 0.0 | JIGGLE_INFO | ONNX_Audio_HeardCue | Parado (0u) | MicroMove:HoldStop(ONNX_Audio_HeardCue_StandStill) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | glock | Beco | `477,425,-252` | `-2°,-116°` | 128.4 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[03:33]`** `[COMBATE]` **Shark** causou **20 HP** em **Syfers** com **glock** a **1189u** (HP 100→80, raw=20, overkill=0, setor: Janela)
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Vision_Spotted` em `(446, 375, -252)` [Mira: Yaw -114° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Audio_HeardCue` em `(-1183, -872, -68)` [Mira: Yaw 61° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Esq(Duck+Jump)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Diag-Esq(250u+Jump)`
- **`[03:33]`** `[COMBATE]` **Rebel** causou **41 HP** em **Syfers** com **glock** a **1300u** (HP 80→39, raw=24, overkill=0, setor: Janela)
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Vision_Spotted` em `(-815, 522, -77)` [Mira: Yaw 2° | CPU: `0.72ms`] -> Horizontes: **0ms:** `Recuo(250u)` | **125ms:** `Recuo(250u)` | **250ms:** `Recuo(250u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Vision_Spotted` em `(1260, 77, -168)` [Mira: Yaw -91° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(Shift)` | **125ms:** `Avanco(Shift)` | **250ms:** `Avanco(Shift)`
- **`[03:33]`** `[MLMOVE - TRADE SPACING]` **Soldier** (`yielding_slot=5`) cedeu espaço para **Ricksaw** (`priority_slot=2`) | `dist_before=59u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=12`.
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Vision_Spotted` em `(46, -496, -181)` [Mira: Yaw -173° | CPU: `0.71ms`] -> Horizontes: **0ms:** `Avanco(Duck)` | **125ms:** `Parado (0u)` | **250ms:** `Avanco(Duck)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Vision_Spotted` em `(125, -309, -172)` [Mira: Yaw -165° | CPU: `0.71ms`] -> Horizontes: **0ms:** `Diag-Dir(Duck)` | **125ms:** `Diag-Dir(Duck)` | **250ms:** `Avanco(Duck)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Syfers** acionou `Vision_Spotted` em `(-1130, -652, -168)` [Mira: Yaw 7° | CPU: `0.74ms`] -> Horizontes: **0ms:** `Strafe-Esq(Duck)` | **125ms:** `Strafe-Esq(Shift)` | **250ms:** `Strafe-Esq(Duck)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Audio_HeardCue` em `(-1488, -979, -200)` [Mira: Yaw 22° | CPU: `0.74ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`

<details><summary><b>📊 Snapshot Tático das [03:33] (10 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | glock | Top Mid | `46,-496,-181` | `2°,-173°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Strafe-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act45) | Pending | None |
| 2 | Ricksaw (AWPer) | CT | 100 | hkp2000 | Janela | `-1149,-721,-113` | `-0°,54°` | 289.4 (Z -136 / 3D 320 aéreo) | PASSIVE_HOLD | ONNX_Audio_HeardCue | Diag-Dir(250u+Jump) | TradeSpacing:UsercmdVector(TradeSpacing_Repulsion_Act14) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | glock | Beco | `-957,533,-80` | `-0°,1°` | 0.0 | PASSIVE_HOLD | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_house)) | Pending | None |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | Mercado / Kitchen | `-1888,-345,-124` | `-2°,56°` | 148.8 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_short_corner)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1120,-885,-168` | `0°,85°` | 0.0 | JIGGLE_INFO | ONNX_Audio_HeardCue | Parado (0u) | MicroMove:HoldStop(ONNX_Audio_HeardCue_StandStill) | Pending | None |
| 6 | Shamat (Rotator) | TR | 100 | glock | TR Spawn | `1258,-55,-168` | `-2°,-90°` | 124.8 | JIGGLE_INFO | ONNX_Vision_Spotted | Avanco(Shift) | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | glock | Top Mid | `125,-309,-172` | `1°,-165°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 8 | Syfers (Anchor) | CT | 14 | hkp2000 | Janela | `-1130,-654,-168` | `2°,7°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Strafe-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act37) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1488,-979,-200` | `-2°,22°` | 0.0 | JIGGLE_INFO | ONNX_Audio_HeardCue | Parado (0u) | MicroMove:HoldStop(ONNX_Audio_HeardCue_StandStill) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | glock | Beco | `288,124,-233` | `-2°,-95°` | 18.7 | JIGGLE_INFO | ONNX_Vision_Spotted | Avanco(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act45) | Pending | Movendo |

</details>

- **`[03:33]`** `[COMBATE]` **Rebel** causou **14 HP** em **Ricksaw** com **glock** a **1336u** (HP 100→86, raw=14, overkill=0, setor: Janela)
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Vision_Spotted` em `(287, 122, -211)` [Mira: Yaw -99° | CPU: `0.65ms`] -> Horizontes: **0ms:** `Avanco(Duck+Jump)` | **125ms:** `Avanco(Shift)` | **250ms:** `Strafe-Esq(Duck+Jump)`
- **`[03:33]`** `[COMBATE]` **Ricksaw** causou **17 HP** em **Rebel** com **hkp2000** a **1342u** (HP 100→83, raw=17, overkill=0, setor: Top Mid)
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-1163, -685, -168)` [Mira: Yaw 16° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck)` | **125ms:** `Parado (0u)` | **250ms:** `Strafe-Dir(Duck)`
- **`[03:33]`** `[MORTE]` **Rebel** eliminou **Syfers** com **glock** no setor **Janela**
- **`[03:33]`** `[MLMOVE - TRADE SPACING]` **Soldier** (`yielding_slot=5`) cedeu espaço para **Ricksaw** (`priority_slot=2`) | `dist_before=137u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=12`.
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Vision_Spotted` em `(-774, 522, -35)` [Mira: Yaw -7° | CPU: `0.72ms`] -> Horizontes: **0ms:** `Avanco(250u+Jump)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Vision_Spotted` em `(1255, -297, -164)` [Mira: Yaw -94° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Avanco(Shift)` | **125ms:** `Avanco(Shift)` | **250ms:** `Avanco(Shift)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Audio_HeardCue` em `(-1753, -633, -168)` [Mira: Yaw -43° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Vision_Spotted` em `(-37, -506, -120)` [Mira: Yaw -170° | CPU: `0.72ms`] -> Horizontes: **0ms:** `Avanco(250u+Jump)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(Shift)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Vision_Spotted` em `(125, -309, -172)` [Mira: Yaw -164° | CPU: `0.72ms`] -> Horizontes: **0ms:** `Diag-Dir(Shift)` | **125ms:** `Parado (0u)` | **250ms:** `Diag-Dir(Shift)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Audio_HeardCue` em `(-1488, -979, -200)` [Mira: Yaw 24° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck)` | **125ms:** `Strafe-Dir(Duck)` | **250ms:** `Parado (0u)`

<details><summary><b>📊 Snapshot Tático das [03:33] (9 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | glock | Catwalk / Short | `-79,-512,-145` | `2°,-171°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 2 | Ricksaw (AWPer) | CT | 77 | hkp2000 | Janela | `-1167,-682,-168` | `0°,94°` | 20.5 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | glock | Beco | `-614,520,-78` | `-1°,-102°` | 224.9 | PASSIVE_HOLD | ONNX_Vision_Spotted | Strafe-Dir(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_house)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | Mercado / Kitchen | `-1714,-644,-168` | `-1°,-48°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | Janela | `-1150,-730,-168` | `-0°,103°` | 0.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Strafe-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act41) | Pending | None |
| 6 | Shamat (Rotator) | TR | 100 | glock | TR Spawn | `1278,-425,-164` | `-1°,-100°` | 123.7 | JIGGLE_INFO | ONNX_Vision_Spotted | Avanco(Shift) | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 22 | glock | Top Mid | `125,-309,-172` | `1°,-164°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Recuo(Shift) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act18) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1488,-979,-200` | `-1°,25°` | 0.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Strafe-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act38) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | glock | Top Mid | `232,-118,-165` | `-1°,-116°` | 0.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Strafe-Esq(Shift) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act24) | Pending | None |

</details>

- **`[03:33]`** `[COMBATE]` **Shark** causou **17 HP** em **Ricksaw** com **glock** a **1104u** (HP 86→69, raw=8, overkill=0, setor: Janela)
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Vision_Spotted` em `(220, -142, -121)` [Mira: Yaw -116° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Avanco(250u+Jump)` | **125ms:** `Avanco(250u)` | **250ms:** `Diag-Esq(250u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-1166, -682, -168)` [Mira: Yaw 95° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Strafe-Dir(Shift)` | **125ms:** `Strafe-Dir(Shift)` | **250ms:** `Parado (0u)`
- **`[03:33]`** `[MLMOVE - TRADE SPACING]` **Soldier** (`yielding_slot=5`) cedeu espaço para **Ricksaw** (`priority_slot=2`) | `dist_before=50u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=12`.
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Vision_Spotted` em `(-531, 520, -42)` [Mira: Yaw -155° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Diag-Esq(Shift+Jump)` | **125ms:** `Diag-Esq(250u+Jump)` | **250ms:** `Diag-Esq(250u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Vision_Spotted` em `(1246, -660, -164)` [Mira: Yaw -114° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Dir(Shift)` | **125ms:** `Avanco(Shift)` | **250ms:** `Diag-Dir(Shift)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1714, -644, -168)` [Mira: Yaw -47° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Vision_Spotted` em `(-79, -512, -145)` [Mira: Yaw -171° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Vision_Spotted` em `(125, -309, -138)` [Mira: Yaw -164° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Recuo(Duck+Jump)` | **125ms:** `Parado (0u)` | **250ms:** `Avanco(Duck+Jump)`
- **`[03:33]`** `[MORTE]` **Shark** eliminou **Ricksaw** com **glock** no setor **Janela**
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Vision_Spotted` em `(-1440, -864, -168)` [Mira: Yaw 10° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`

<details><summary><b>📊 Snapshot Tático das [03:33] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | glock | Catwalk / Short | `-79,-512,-145` | `2°,-168°` | 0.0 | PASSIVE_HOLD | Nenhuma | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act33) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 100 | glock | Beco | `-615,498,-44` | `-0°,-60°` | 152.2 | PASSIVE_HOLD | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_house)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | Mercado / Kitchen | `-1714,-644,-168` | `-0°,-47°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Strafe-Esq(Shift) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act27) | Pending | None |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | Janela | `-1130,-724,-168` | `-0°,110°` | 16.6 | JIGGLE_INFO | ONNX_Vision_Spotted | Strafe-Esq(Shift) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act18) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | glock | TR Spawn | `1178,-794,-246` | `-0°,-124°` | 89.1 | JIGGLE_INFO | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 22 | glock | Top Mid | `118,-311,-153` | `2°,-166°` | 138.8 (Z -248 / 3D 284 aéreo) | PASSIVE_HOLD | Nenhuma | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act81) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1440,-850,-111` | `-0°,6°` | 72.2 (Z 14 / 3D 74 aéreo) | JIGGLE_INFO | ONNX_Vision_Spotted | Diag-Dir(Duck+Jump) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act84) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | glock | Top Mid | `199,-222,-103` | `-0°,-147°` | 188.0 (Z 161 / 3D 248 aéreo) | JIGGLE_INFO | Nenhuma | TradeSpacing:UsercmdVector(TradeSpacing_WideSwing_Act14) | Pending | Movendo |

</details>

- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Audio_HeardCue` em `(288, -164, -123)` [Mira: Yaw -147° | CPU: `0.63ms`] -> Horizontes: **0ms:** `Recuo(250u+Jump)` | **125ms:** `Recuo(250u)` | **250ms:** `Recuo-Esq(250u)`
- **`[03:33]`** `[COMBATE]` **Rebel** causou **9 HP** em **Soldier** com **glock** a **1306u** (HP 100→91, raw=9, overkill=0, setor: Janela)
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(-1130, -724, -168)` [Mira: Yaw 81° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Vision_Spotted` em `(-595, 361, -224)` [Mira: Yaw -146° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Diag-Esq(Shift)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1568, -706, -168)` [Mira: Yaw -45° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Dir(Duck)` | **125ms:** `Parado (0u)` | **250ms:** `Diag-Dir(Duck)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Vision_Spotted` em `(108, -309, -177)` [Mira: Yaw -161° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Avanco(Duck)` | **125ms:** `Avanco(Duck)` | **250ms:** `Avanco(Duck)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Vision_Spotted` em `(-1366, -854, -111)` [Mira: Yaw 32° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`

<details><summary><b>📊 Snapshot Tático das [03:33] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | glock | Meio | `-191,-522,-102` | `1°,-178°` | 215.1 (Z -189 / 3D 286 aéreo) | PASSIVE_HOLD | TradeSpacing_WideSwing | Recuo-Dir(250u) | TradeSpacing:UsercmdVector(TradeSpacing_WideSwing_Act16) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | glock | Underpass | `-831,367,-335` | `1°,-133°` | 216.5 | PASSIVE_HOLD | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_house)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | CT Spawn | `-1569,-806,-148` | `1°,-45°` | 276.7 (Z -211 / 3D 348 aéreo) | PASSIVE_HOLD | Nenhuma | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act45) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 91 | hkp2000 | Janela | `-1131,-715,-168` | `0°,125°` | 80.6 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_market_window)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | glock | Palácio A | `746,-1152,-258` | `1°,-125°` | 226.8 | JIGGLE_INFO | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 22 | glock | Top Mid | `108,-309,-143` | `1°,-161°` | 0.0 (Z 152 / 3D 152 aéreo) | PASSIVE_HOLD | ONNX_Vision_Spotted | Recuo(Duck+Jump) | Unstuck:UsercmdVector(STAGE2_BLACKLIST_WAYPOINT_AND_SELECT_ALTERNATIVE) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1368,-855,-111` | `1°,38°` | 52.1 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | glock | Top Mid | `420,-52,-163` | `1°,-136°` | 0.0 | JIGGLE_INFO | ONNX_Audio_HeardCue | Strafe-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act47) | Pending | None |

</details>

- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Vision_Spotted` em `(-218, -525, -132)` [Mira: Yaw -176° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u+Jump)` | **125ms:** `Avanco(Shift)` | **250ms:** `Avanco(250u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Hotzone_PreMapped` em `(-1126, -892, -168)` [Mira: Yaw 126° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Strafe-Esq(Shift)` | **125ms:** `Strafe-Esq(Shift)` | **250ms:** `Parado (0u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Hotzone_PreMapped` em `(69, -318, -121)` [Mira: Yaw -162° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Recuo(Duck+Jump)` | **125ms:** `Recuo(Duck+Jump)` | **250ms:** `Recuo(Duck+Jump)`

<details><summary><b>📊 Snapshot Tático das [03:33] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | glock | Meio | `-595,-582,-276` | `-6°,-167°` | 7.3 | PASSIVE_HOLD | Nenhuma | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act58) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 100 | glock | Underpass | `-1043,-94,-368` | `2°,-90°` | 240.0 | PASSIVE_HOLD | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_house)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | CT Spawn | `-1372,-947,-168` | `2°,-44°` | 8.9 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | None |
| 5 | Soldier (Rotator) | CT | 91 | hkp2000 | CT Spawn | `-1121,-1030,-132` | `1°,124°` | 28.3 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_market_window)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | glock | Rampa A | `394,-1620,-209` | `2°,-177°` | 229.6 | JIGGLE_INFO | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 22 | glock | Top Mid | `69,-318,-181` | `-1°,-162°` | 0.0 | PASSIVE_HOLD | Nenhuma | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act44) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1360,-979,-168` | `2°,22°` | 12.7 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | glock | Top Mid | `221,-267,-168` | `2°,-152°` | 230.2 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Hotzone_PreMapped` em `(-560, -577, -276)` [Mira: Yaw 141° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Recuo-Esq(250u)` | **125ms:** `Recuo-Esq(250u)` | **250ms:** `Recuo-Esq(250u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-26, -456, -168)` [Mira: Yaw 177° | CPU: `1.03ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Diag-Dir(250u)`
- **`[03:33]`** `[MLMOVE - TRADE SPACING]` **Buckshot** (`yielding_slot=9`) cedeu espaço para **Soldier** (`priority_slot=5`) | `dist_before=56u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=1`.
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Hotzone_PreMapped` em `(-980, -624, -272)` [Mira: Yaw -40° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Diag-Dir(250u)` | **125ms:** `Diag-Dir(250u)` | **250ms:** `Avanco(250u)`

<details><summary><b>📊 Snapshot Tático das [03:33] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | glock | Meio | `-489,-623,-208` | `2°,123°` | 216.2 (Z -39 / 3D 220 aéreo) | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Avanco(250u) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act6) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | glock | Meio | `-882,-634,-262` | `2°,-51°` | 232.2 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Diag-Dir(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_house)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | CT Spawn | `-1359,-964,-168` | `12°,20°` | 14.5 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | None |
| 5 | Soldier (Rotator) | CT | 91 | hkp2000 | CT Spawn | `-1310,-970,-168` | `2°,173°` | 0.0 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_market_window)) | Pending | None |
| 6 | Shamat (Rotator) | TR | 100 | glock | Bomb A | `-228,-1748,-168` | `2°,-115°` | 227.1 | JIGGLE_INFO | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 22 | glock | Catwalk / Short | `-126,-458,-104` | `2°,-149°` | 215.5 (Z -64 / 3D 225 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_jungle_safe)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1150,-949,-168` | `-13°,21°` | 0.0 | JIGGLE_INFO | ONNX_Hotzone_PreMapped | Parado (0u) | MicroMove:HoldStop(ONNX_Hotzone_PreMapped_StandStill) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | glock | Catwalk / Short | `-216,-454,-167` | `2°,176°` | 49.0 | JIGGLE_INFO | ONNX_Hotzone_PreMapped | Avanco(250u+Jump) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act57) | Pending | Movendo |

</details>

- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Hotzone_PreMapped` em `(-522, -551, -274)` [Mira: Yaw 123° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Avanco(Duck)` | **125ms:** `Avanco(Duck)` | **250ms:** `Parado (0u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Hotzone_PreMapped` em `(-676, -1116, -174)` [Mira: Yaw -57° | CPU: `0.65ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Strafe-Esq(250u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Hotzone_PreMapped` em `(-189, -679, -240)` [Mira: Yaw -165° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u+Jump)`

<details><summary><b>📊 Snapshot Tático das [03:33] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | glock | Meio | `-532,-541,-271` | `1°,115°` | 64.4 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Recuo-Esq(Duck) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act33) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | glock | Conector | `-646,-1208,-168` | `1°,-44°` | 240.0 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Avanco(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_house)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | CT Spawn | `-1395,-974,-168` | `10°,9°` | 0.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | None |
| 5 | Soldier (Rotator) | CT | 91 | hkp2000 | CT Spawn | `-1351,-969,-168` | `1°,149°` | 40.7 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_market_window)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | c4 | Bomb A | `-331,-2039,-176` | `1°,-102°` | 0.0 | JIGGLE_INFO | Nenhuma | BombObjective:ReleaseHoldAndRepath(C4Carrier_InBombZone_AuthorizedToPlant) | Pending | None |
| 7 | Rebel (Anchor) | TR | 22 | glock | Meio | `-202,-683,-241` | `1°,-165°` | 186.1 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Avanco(250u) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act10) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1136,-799,-168` | `2°,98°` | 125.8 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | glock | Catwalk / Short | `-77,-464,-166` | `1°,-136°` | 120.9 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-60, -498, -148)` [Mira: Yaw -142° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Diag-Dir(250u)` | **125ms:** `Diag-Dir(250u)` | **250ms:** `Diag-Dir(Duck)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Hotzone_PreMapped` em `(-526, -542, -258)` [Mira: Yaw 120° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Recuo(Duck+Jump)` | **125ms:** `Recuo(Duck+Jump)` | **250ms:** `Recuo(Duck+Jump)`
- **`[03:33]`** `[BOMBA]` C4 plantada no bombsite!

<details><summary><b>📊 Snapshot Tático das [03:33] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | glock | Meio | `-453,-716,-203` | `-0°,118°` | 214.3 (Z -36 / 3D 217 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | glock | Escadas A | `-496,-1313,-160` | `4°,-112°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_house)) | Pending | None |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | CT Spawn | `-1411,-977,-168` | `10°,38°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 5 | Soldier (Rotator) | CT | 91 | hkp2000 | CT Spawn | `-1360,-970,-168` | `-0°,24°` | 13.2 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 6 | Shamat (Rotator) | TR | 100 | glock | Bomb A | `-360,-2028,-178` | `-0°,-168°` | 188.2 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 22 | glock | Meio | `-411,-781,-260` | `-0°,-145°` | 59.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_jungle_safe)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1167,-958,-168` | `-0°,-99°` | 177.1 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | glock | Meio | `-277,-671,-199` | `-0°,-153°` | 212.1 (Z 39 / 3D 216 aéreo) | AGGRESSIVE_POKE | ONNX_Hotzone_PreMapped | Avanco(250u+Jump) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act58) | Pending | Movendo |

</details>

- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Hotzone_PreMapped` em `(-558, -777, -260)` [Mira: Yaw -115° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Avanco(Shift)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-564, -735, -264)` [Mira: Yaw -111° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Esq(Duck)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Diag-Esq(250u+Jump)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Vision_Spotted` em `(-496, -1313, -160)` [Mira: Yaw -137° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Diag-Dir(Duck+Jump)` | **125ms:** `Diag-Dir(Duck+Jump)` | **250ms:** `Parado (0u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Hotzone_PreMapped` em `(-1262, -1052, -168)` [Mira: Yaw -58° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[03:33]`** `[COMBATE]` **Delrow** causou **14 HP** em **Buckshot** com **glock** a **609u** (HP 100→86, raw=14, overkill=0, setor: CT Spawn)
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Vision_Spotted` em `(-1079, -1441, -165)` [Mira: Yaw -19° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Avanco(Duck)` | **125ms:** `Parado (0u)` | **250ms:** `Avanco(250u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Audio_HeardCue` em `(-1561, -1100, -231)` [Mira: Yaw -24° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Diag-Esq(250u)`

<details><summary><b>📊 Snapshot Tático das [03:33] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | glock | Meio | `-462,-710,-269` | `-2°,-128°` | 235.2 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | glock | Escadas A | `-496,-1313,-160` | `4°,-168°` | 0.0 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Avanco(Shift+Jump) | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_house)) | Pending | None |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | CT Spawn | `-1557,-1114,-234` | `-2°,-37°` | 236.4 | AGGRESSIVE_POKE | ONNX_Audio_HeardCue | Diag-Esq(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 91 | hkp2000 | CT Spawn | `-1198,-1228,-168` | `-2°,-73°` | 190.8 | AGGRESSIVE_POKE | ONNX_Audio_HeardCue | Avanco(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | glock | Bomb A | `-798,-1994,-152` | `-2°,-100°` | 60.9 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 22 | glock | Conector | `-658,-967,-216` | `-2°,-84°` | 42.8 | PASSIVE_HOLD | TradeSpacing_WideSwing | Diag-Esq(250u) | TradeSpacing:UsercmdVector(TradeSpacing_WideSwing_Act12) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 53 | hkp2000 | CT Spawn | `-1074,-1442,-165` | `2°,5°` | 0.0 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Diag-Dir(Duck) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | glock | Meio | `-604,-780,-213` | `-2°,-92°` | 203.3 (Z 114 / 3D 233 aéreo) | AGGRESSIVE_POKE | ONNX_Audio_HeardCue | Avanco(250u+Jump) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act61) | Pending | Movendo |

</details>

- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Audio_HeardCue` em `(-528, -739, -259)` [Mira: Yaw -116° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(250u+Jump)`
- **`[03:33]`** `[COMBATE]` **Buckshot** causou **23 HP** em **Delrow** com **hkp2000** a **596u** (HP 100→77, raw=23, overkill=0, setor: Escadas A)
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Audio_HeardCue` em `(-662, -1130, -133)` [Mira: Yaw -129° | CPU: `0.77ms`] -> Horizontes: **0ms:** `Avanco(250u+Jump)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(250u+Jump)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Audio_HeardCue` em `(-695, -894, -228)` [Mira: Yaw -120° | CPU: `0.77ms`] -> Horizontes: **0ms:** `Avanco(250u+Jump)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(250u)`
- **`[03:33]`** `[COMBATE]` **Delrow** causou **11 HP** em **Soldier** com **glock** a **559u** (HP 91→80, raw=11, overkill=0, setor: Jungle)
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Audio_HeardCue` em `(-780, -1832, -180)` [Mira: Yaw 99° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(250u)`
- **`[03:33]`** `[COMBATE]` **Soldier** causou **77 HP** em **Delrow** com **hkp2000** a **558u** (HP 77→0, raw=19, overkill=0, setor: Escadas A)
- **`[03:33]`** `[MORTE]` **Soldier** eliminou **Delrow** com **hkp2000** no setor **Escadas A**
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Vision_Spotted` em `(-496, -1313, -160)` [Mira: Yaw -162° | CPU: `0.72ms`] -> Horizontes: **0ms:** `Strafe-Esq(Duck)` | **125ms:** `Strafe-Esq(Duck)` | **250ms:** `Diag-Esq(250u+Jump)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(-1037, -1450, -166)` [Mira: Yaw 14° | CPU: `0.65ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck)` | **125ms:** `Parado (0u)` | **250ms:** `Strafe-Esq(Shift)`

<details><summary><b>📊 Snapshot Tático das [03:33] (7 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | glock | Meio | `-623,-920,-209` | `-4°,-100°` | 153.1 (Z 214 / 3D 264 aéreo) | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Avanco(Duck+Jump) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act93) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | CT Spawn | `-1526,-1819,-262` | `-3°,-88°` | 240.0 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 80 | hkp2000 | Jungle | `-957,-1483,-168` | `-33°,19°` | 201.6 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | glock | Bomb A | `-760,-1748,-180` | `2°,133°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | None |
| 7 | Rebel (Anchor) | TR | 22 | glock | Conector | `-660,-1182,-111` | `20°,-120°` | 218.8 (Z 14 / 3D 219 aéreo) | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Recuo(250u+Jump) | TradeSpacing:UsercmdVector(TradeSpacing_Repulsion_Act12) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 16 | hkp2000 | Jungle | `-981,-1516,-166` | `0°,23°` | 197.6 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | glock | Conector | `-711,-1103,-181` | `-3°,-90°` | 236.6 | AGGRESSIVE_POKE | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Hotzone_PreMapped` em `(-633, -983, -181)` [Mira: Yaw -101° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Diag-Esq(250u+Jump)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1524, -1967, -264)` [Mira: Yaw -88° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[03:33]`** `[MLMOVE - TRADE SPACING]` **Buckshot** (`yielding_slot=9`) cedeu espaço para **Soldier** (`priority_slot=5`) | `dist_before=128u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=8`.
- **`[03:33]`** `[COMBATE]` **Shamat** causou **29 HP** em **Soldier** com **glock** a **204u** (HP 80→51, raw=16, overkill=0, setor: Jungle)
- **`[03:33]`** `[COMBATE]` **Soldier** causou **24 HP** em **Shark** com **hkp2000** a **436u** (HP 100→76, raw=24, overkill=0, setor: Conector)
- **`[03:33]`** `[COMBATE]` **Rebel** causou **86 HP** em **Buckshot** com **glock** a **492u** (HP 86→0, raw=19, overkill=0, setor: Jungle)
- **`[03:33]`** `[MORTE]` **Rebel** eliminou **Buckshot** com **glock** no setor **Jungle**
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Vision_Spotted` em `(-589, -1113, -132)` [Mira: Yaw -115° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Strafe-Esq(Duck+Jump)` | **125ms:** `Avanco(Duck+Jump)` | **250ms:** `Diag-Dir(Duck+Jump)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Audio_HeardCue` em `(-785, -1233, -168)` [Mira: Yaw -102° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Recuo(Duck)` | **125ms:** `Strafe-Esq(Duck)` | **250ms:** `Recuo(Duck)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Vision_Spotted` em `(-760, -1748, -180)` [Mira: Yaw 98° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck)` | **125ms:** `Strafe-Dir(Duck)` | **250ms:** `Strafe-Esq(Shift+Jump)`
- **`[03:33]`** `[COMBATE]` **Shark** causou **45 HP** em **Soldier** com **glock** a **437u** (HP 51→6, raw=12, overkill=0, setor: Bomb A)
- **`[03:33]`** `[MORTE]` **Shamat** eliminou **Soldier** com **glock** no setor **Bomb A**

<details><summary><b>📊 Snapshot Tático das [03:33] (5 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 36 | glock | Conector | `-710,-1247,-147` | `7°,-104°` | 215.3 (Z -236 / 3D 319 aéreo) | PASSIVE_HOLD | ONNX_Audio_HeardCue | Avanco(250u+Jump) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act60) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | CT Spawn | `-1309,-2397,-202` | `-2°,-15°` | 234.6 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Avanco(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | glock | Bomb A | `-742,-1862,-180` | `2°,95°` | 240.0 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 22 | glock | Conector | `-544,-998,-168` | `-2°,-126°` | 15.2 | PASSIVE_HOLD | ONNX_Audio_HeardCue | Recuo(Duck) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act36) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | glock | Conector | `-738,-1186,-103` | `41°,-54°` | 171.4 (Z -155 / 3D 231 aéreo) | AGGRESSIVE_POKE | ONNX_Audio_HeardCue | Diag-Esq(Shift+Jump) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act77) | Pending | Movendo |

</details>

- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Audio_HeardCue` em `(-710, -1265, -168)` [Mira: Yaw -104° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1166, -2354, -177)` [Mira: Yaw 12° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(Duck+Jump)`
- **`[03:33]`** `[PIVOT TÁTICO TR - REJEITADO]` Declaração de `SITE CLEAR` em `Bomb A` por **Shamat** rejeitada: `ENEMIES_PRESENT_IN_SITE(1)` (`setor_atual=Bomb A`, `dwell=2.2s`, `inimigos_proximos=1`).
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Audio_HeardCue` em `(-657, -1017, -216)` [Mira: Yaw -159° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Avanco(Duck)` | **125ms:** `Avanco(Duck)` | **250ms:** `Strafe-Dir(Duck+Jump)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Audio_HeardCue` em `(-808, -1236, -140)` [Mira: Yaw -133° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Avanco(Duck+Jump)` | **125ms:** `Avanco(Duck+Jump)` | **250ms:** `Parado (0u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Vision_Spotted` em `(-722, -2280, -180)` [Mira: Yaw -114° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Avanco(Shift)` | **125ms:** `Diag-Esq(Duck)` | **250ms:** `Avanco(250u)`
- **`[03:33]`** `[COMBATE]` **Commando** causou **21 HP** em **Shamat** com **hkp2000** a **190u** (HP 100→79, raw=21, overkill=0, setor: Bomb A)
- **`[03:33]`** `[COMBATE]` **Shamat** causou **21 HP** em **Commando** com **glock** a **182u** (HP 100→79, raw=21, overkill=0, setor: CT Spawn)

<details><summary><b>📊 Snapshot Tático das [03:33] (5 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 36 | glock | Bomb A | `-730,-1575,-168` | `-0°,-96°` | 0.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_site_default_crouch)) | Pending | None |
| 4 | Commando (EntryFragger) | CT | 79 | hkp2000 | CT Spawn | `-933,-2323,-168` | `12°,32°` | 0.0 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Recuo-Esq(Duck+Jump) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 6 | Shamat (Rotator) | TR | 79 | glock | Bomb A | `-769,-2231,-180` | `7°,-149°` | 84.1 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Strafe-Dir(Shift) | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 22 | glock | Conector | `-733,-1047,-168` | `-0°,57°` | 0.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | glock | Conector | `-808,-1236,-168` | `-0°,-131°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act38) | Pending | None |

</details>

- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-933, -2323, -168)` [Mira: Yaw 35° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Diag-Esq(Duck+Jump)` | **125ms:** `Diag-Esq(Duck+Jump)` | **250ms:** `Parado (0u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-689, -1074, -195)` [Mira: Yaw -95° | CPU: `0.72ms`] -> Horizontes: **0ms:** `Strafe-Esq(Duck)` | **125ms:** `Parado (0u)` | **250ms:** `Strafe-Esq(Duck)`

<details><summary><b>📊 Snapshot Tático das [03:33] (5 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 36 | glock | Bomb A | `-752,-1869,-180` | `1°,-96°` | 240.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_site_default_crouch)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 63 | hkp2000 | CT Spawn | `-933,-2323,-168` | `1°,28°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 6 | Shamat (Rotator) | TR | 11 | glock | Bomb A | `-770,-2169,-180` | `0°,71°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | None |
| 7 | Rebel (Anchor) | TR | 22 | glock | Conector | `-681,-1280,-168` | `1°,-62°` | 205.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | glock | Conector | `-686,-1028,-141` | `3°,-93°` | 209.9 (Z 64 / 3D 220 aéreo) | AGGRESSIVE_POKE | ONNX_Hotzone_PreMapped | Recuo(250u+Jump) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act53) | Pending | Movendo |

</details>

- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Audio_HeardCue` em `(-770, -2002, -180)` [Mira: Yaw -109° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(250u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Vision_Spotted` em `(-770, -2167, -180)` [Mira: Yaw -175° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Strafe-Esq(Duck)` | **125ms:** `Strafe-Esq(Duck)` | **250ms:** `Strafe-Esq(Duck+Jump)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-868, -2368, -168)` [Mira: Yaw 33° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Esq(Shift)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Diag-Esq(250u+Jump)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Audio_HeardCue` em `(-688, -1543, -168)` [Mira: Yaw -97° | CPU: `0.72ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u+Jump)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-697, -1260, -168)` [Mira: Yaw -81° | CPU: `0.73ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(250u+Jump)`

<details><summary><b>📊 Snapshot Tático das [03:33] (5 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 36 | glock | Bomb A | `-654,-2010,-137` | `-2°,42°` | 144.5 (Z -189 / 3D 238 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_site_default_crouch)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 63 | hkp2000 | CT Spawn | `-896,-2345,-168` | `25°,-2°` | 0.0 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Avanco(Duck) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 6 | Shamat (Rotator) | TR | 11 | glock | Bomb A | `-791,-2364,-175` | `1°,8°` | 17.4 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 22 | glock | Bomb A | `-728,-1922,-180` | `2°,-94°` | 240.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | glock | Conector | `-691,-1302,-168` | `3°,-77°` | 123.0 | AGGRESSIVE_POKE | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[03:33]`** `[MORTE]` **Commando** eliminou **Shamat** com **hkp2000** no setor **Bomb A**
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Vision_Spotted` em `(-674, -1999, -180)` [Mira: Yaw -129° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[03:33]`** `[MLMOVE - TRADE SPACING]` **Rebel** (`yielding_slot=7`) cedeu espaço para **Shark** (`priority_slot=1`) | `dist_before=60u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=8`.
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-837, -2295, -174)` [Mira: Yaw 33° | CPU: `0.65ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Diag-Esq(Duck)`
- **`[03:33]`** `[COMBATE]` **Rebel** causou **36 HP** em **Commando** com **glock** a **363u** (HP 79→43, raw=20, overkill=0, setor: Bomb A)
- **`[03:33]`** `[COMBATE]` **Commando** causou **82 HP** em **Rebel** com **hkp2000** a **365u** (HP 83→1, raw=20, overkill=0, setor: Bomb A)
- **`[03:33]`** `[MORTE]` **Commando** eliminou **Rebel** com **hkp2000** no setor **Bomb A**
- **`[03:33]`** `[COMBATE]` **Steel** causou **29 HP** em **Commando** com **glock** a **1000u** (HP 43→14, raw=12, overkill=0, setor: Bomb A)
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Vision_Spotted` em `(-677, -1367, -168)` [Mira: Yaw -94° | CPU: `0.74ms`] -> Horizontes: **0ms:** `Strafe-Esq(Duck)` | **125ms:** `Strafe-Esq(Duck)` | **250ms:** `Strafe-Esq(Duck)`
- **`[03:33]`** `[MORTE]` **Steel** eliminou **Commando** com **glock** no setor **Bomb A**
- **`[03:33]`** `[FIM_ROUND]` internal_round_id=1 | round_oficial=1 | Vencedor: Terrorist | Motivo: `TerroristsWin` (9) — Eliminação total dos Contraterroristas pelos Terroristas | Placar: CT 0 x 1 TR | tick=9361

### 🕒 Auditoria de Eventos Atrasados (Late Events)
| seq | Evento | Round Original | Round Atual | Tick Original | Tick Processamento | Origem | Motivo | Disposição | Detalhes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | EventPlayerDeath | 0 | 0 | 5133 | 5133 | EventPlayerDeath | UNKNOWN_ROUND | AUDITED_LATE | Delrow -> Syfers |
| 2 | RoundEnd(duplicado) | 0 | 0 | 5133 | 5133 | EventRoundEnd | UNKNOWN_ROUND | AUDITED_LATE | winner=Terrorist reason=9 |

- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-664, -1258, -168)` [Mira: Yaw 65° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Diag-Dir(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Diag-Dir(250u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-446, -696, -272)` [Mira: Yaw 15° | CPU: `0.72ms`] -> Horizontes: **0ms:** `Diag-Dir(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[03:33]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Hotzone_PreMapped` em `(-1630, -660, -147)` [Mira: Yaw 117° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Diag-Esq(250u+Jump)` | **125ms:** `Diag-Esq(250u+Jump)` | **250ms:** `Diag-Esq(250u)`
## 🎮 Round 2 [Placar: CT 0 x 1 TR]
- **internal_round_id:** `2` | **display_round_number:** `2` | **round_in_half:** `2` | **match_phase:** `LIVE` | **round_phase:** `ROUND_ACTIVE` | **start_tick:** `9809`
- **Motor Micro-Movimento (16Hz):** `[Modo ONNX Ativo] ONNX-CPU-L3 (mlmove_de_mirage.onnx | 0.67ms)`

### 💵 Economia por Time (Pré-compra vs Pós-compra)
| Time | PreBuyIntent | FinalBuyState | Completion | Caixa Médio Antes | Caixa Médio Depois | Gasto | Equip Antes | Equip Depois | Primárias | Rifles | SMGs | AWPs | Coletes | Capacetes | Kits | Utilitárias ($) | LossBonus |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| CT | `HALF_BUY` | `FULL_BUY` | `STABILIZED` | $4350 | $270 | $20400 | $1000 | $18600 | 5 | 5 | 0 | 0 | 5 | 0 | 0 | $2200 | $1900 |
| TR | `FULL_BUY` | `FULL_BUY` | `STABILIZED` | $6460 | $1650 | $24050 | $2700 | $23700 | 5 | 4 | 0 | 1 | 5 | 0 | 0 | $3900 | $1400 |

### 💰 Loadout Pós-Compra
| Slot | Jogador | Time | Role | Dinheiro | Arma Primária | Arma Secundária | Utilitárias | Colete/Kit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark | TR | AWPer | $350 | AWP | GLOCK | FLASHBANG, SMOKEGRENADE | Colete (100) |
| 2 | Ricksaw | CT | Rotator | $50 | M4A1 | HKP2000 | FLASHBANG | Colete (100) |
| 3 | Delrow | TR | EntryFragger | $1800 | AK47 | GLOCK | SMOKEGRENADE, FLASHBANG, MOLOTOV | Colete (100) |
| 4 | Commando | CT | EntryFragger | $50 | M4A1 | HKP2000 | SMOKEGRENADE, FLASHBANG | Colete (100) |
| 5 | Soldier | CT | Rotator | $0 | FAMAS | HKP2000 | SMOKEGRENADE, FLASHBANG, HEGRENADE | Colete (100) |
| 6 | Shamat | TR | Rotator | $1900 | AK47 | GLOCK | SMOKEGRENADE, FLASHBANG, HEGRENADE | Colete (100) + 💣 C4 (Bomba) |
| 7 | Rebel | TR | Anchor | $2100 | AK47 | GLOCK | SMOKEGRENADE, FLASHBANG, MOLOTOV | Colete (100) |
| 8 | Syfers | CT | Anchor | $200 | FAMAS | HKP2000 | SMOKEGRENADE, FLASHBANG | Colete (100) |
| 9 | Buckshot | CT | Rotator | $1050 | FAMAS | HKP2000 | FLASHBANG | Colete (100) |
| 10 | Steel | TR | Rotator | $2100 | AK47 | GLOCK | FLASHBANG, SMOKEGRENADE, HEGRENADE | Colete (100) |

#### 🤖 Auditoria IGL CT
- **decision_id:** `R2_CT_CT_STANDARD_2_1_2_BALANCED_c9ff3b` | **source:** `UTILITY_AI_ENGINE` | **latency:** `2ms` | **cache_hit:** `False` | **fallback:** `False` (NONE) | **parse:** `OK`
- **InitialTactic:** `Defesa 2-1-2 Padrão Equilibrada` | **CurrentTactic:** `Defesa 2-1-2 Padrão Equilibrada` | **TacticRevision:** `1` | **Ritmo:** `SLOW_DEFAULT` | **Tier:** `Tier2_Moderate`
- **Candidatas:** CT_STANDARD_2_1_2_BALANCED (78.0); CT_2_1_2_HEAVY_ANCHOR_B (68.0); CT_2_1_2_HEAVY_PALACE_RAMP_A (68.0) | **penalidade_repetição:** `False`
- **Resumo:** 2 A (Ticket + Cabecinha), 1 Meio (Janela), 2 B (Van + Banco) com AuthorizedHold.

#### 🤖 Auditoria IGL TR
- **decision_id:** `R2_TR_TR_SLOW_DEFAULT_MAP_CONTROL_a43e80` | **source:** `UTILITY_AI_ENGINE` | **latency:** `0ms` | **cache_hit:** `False` | **fallback:** `False` (NONE) | **parse:** `OK`
- **InitialTactic:** `Default Lento de Controle de Mapa (1-2-2)` | **CurrentTactic:** `Default Lento de Controle de Mapa (1-2-2)` | **TacticRevision:** `1` | **Ritmo:** `SLOW_DEFAULT` | **Tier:** `Tier1_Standard`
- **Candidatas:** TR_SLOW_DEFAULT_MAP_CONTROL (68.0); TR_EXEC_A_PALACE_RAMP_SPLIT (68.0); TR_SPLIT_A_MID_TO_CONNECTOR (68.0) | **penalidade_repetição:** `False`
- **Resumo:** 1 Top Mid, 2 Rampa/Palácio A, 2 Tapete/Underpass B buscando pick inicial antes de executar A.

### ⏱️ Linha do Tempo de Eventos

<details><summary><b>📊 Snapshot Tático das [04:39] (10 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | awp | Meio | `-10,-646,-198` | `-0°,-168°` | 191.5 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_top_mid_boxes)) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | Mercado / Kitchen | `-1911,-385,-152` | `1°,59°` | 163.3 (Z 187 / 3D 249 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_mid_window_deep_awp)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | TR Spawn | `660,499,-258` | `1°,171°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | Mercado / Kitchen | `-1790,-621,-168` | `-0°,-57°` | 225.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | famas | CT Spawn | `-1591,-1708,-264` | `1°,-82°` | 215.5 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_stairs_cross)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | ak47 | Beco | `520,472,-260` | `1°,-135°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_palace_room)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Beco | `-166,452,-71` | `1°,-72°` | 30.8 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_t_roof)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | famas | Mercado / Kitchen | `-1924,-297,-168` | `0°,-91°` | 21.9 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_bench_deep)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | famas | Mercado / Kitchen | `-1720,-504,-168` | `1°,107°` | 0.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_van_peek)) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | TR Spawn | `878,468,-254` | `1°,-180°` | 207.1 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Hotzone_PreMapped` em `(-143, -635, -227)` [Mira: Yaw -163° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`

<details><summary><b>📊 Snapshot Tático das [04:39] (10 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | awp | Meio | `-175,-638,-237` | `-0°,-161°` | 20.5 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_top_mid_boxes)) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | Mercado / Kitchen | `-1872,-304,-106` | `2°,59°` | 7.2 (Z -20 / 3D 21 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_mid_window_deep_awp)) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | TR Spawn | `624,527,-258` | `2°,36°` | 111.8 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1488,-1027,-212` | `-0°,-57°` | 202.5 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | famas | CT Spawn | `-1448,-2336,-235` | `2°,-11°` | 220.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_stairs_cross)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | ak47 | Top Mid | `392,-3,-202` | `2°,-114°` | 199.5 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_palace_room)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Beco | `-185,422,-78` | `2°,-74°` | 89.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_t_roof)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | famas | Mercado / Kitchen | `-1936,-296,-168` | `0°,-108°` | 0.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_bench_deep)) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | famas | Mercado / Kitchen | `-1802,-566,-168` | `2°,94°` | 210.9 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_van_peek)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Beco | `297,370,-262` | `2°,-100°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>


<details><summary><b>📊 Snapshot Tático das [04:39] (10 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | awp | Meio | `-341,-722,-268` | `-0°,-149°` | 192.7 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_top_mid_boxes)) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | Mercado / Kitchen | `-1895,-348,-130` | `2°,62°` | 156.7 (Z -13 / 3D 157 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_mid_window_deep_awp)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | TR Spawn | `865,578,-225` | `2°,154°` | 111.8 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1600,-821,-166` | `2°,130°` | 206.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | famas | CT Spawn | `-847,-2367,-169` | `2°,18°` | 220.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_stairs_cross)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | ak47 | Top Mid | `57,-488,-179` | `2°,172°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_palace_room)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Beco | `-226,547,-79` | `2°,62°` | 206.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_t_roof)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | famas | Mercado / Kitchen | `-1957,-321,-168` | `0°,-13°` | 64.9 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_bench_deep)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | famas | Mercado / Kitchen | `-1871,-487,-168` | `2°,-44°` | 220.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_van_peek)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Top Mid | `210,-254,-168` | `2°,-118°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Hotzone_PreMapped` em `(-30, -465, -168)` [Mira: Yaw 170° | CPU: `0.71ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Diag-Dir(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Hotzone_PreMapped` em `(-564, -731, -265)` [Mira: Yaw -114° | CPU: `0.65ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Diag-Esq(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-171, -662, -236)` [Mira: Yaw -170° | CPU: `0.71ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Diag-Esq(250u+Jump)` | **250ms:** `Avanco(250u+Jump)`

<details><summary><b>📊 Snapshot Tático das [04:39] (10 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | awp | Meio | `-594,-740,-262` | `-0°,-102°` | 0.0 | JIGGLE_INFO | ONNX_Hotzone_PreMapped | Parado (0u) | MicroMove:HoldStop(ONNX_Hotzone_PreMapped_StandStill) | Pending | None |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | Mercado / Kitchen | `-1872,-304,-168` | `1°,67°` | 6.2 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_mid_window_deep_awp)) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Apartamentos B | `575,684,-136` | `1°,163°` | 64.1 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | Mercado / Kitchen | `-1855,-501,-168` | `1°,99°` | 42.3 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | famas | Bomb A | `-415,-2025,-180` | `1°,22°` | 209.1 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_stairs_cross)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | ak47 | Catwalk / Short | `-329,-405,-136` | `1°,170°` | 215.0 (Z -236 / 3D 319 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_palace_room)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Apartamentos B | `198,819,-136` | `1°,-13°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_t_roof)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | famas | Mercado / Kitchen | `-2230,-500,-168` | `1°,142°` | 212.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_bench_deep)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | famas | Mercado / Kitchen | `-1616,-690,-168` | `1°,-76°` | 135.5 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_van_peek)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Meio | `-190,-658,-240` | `1°,-168°` | 102.7 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Diag-Esq(Shift) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act24) | Pending | Movendo |

</details>

- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Hotzone_PreMapped` em `(-556, -378, -168)` [Mira: Yaw 149° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Diag-Dir(250u)` | **125ms:** `Diag-Dir(250u)` | **250ms:** `Parado (0u)`

<details><summary><b>📊 Snapshot Tático das [04:39] (10 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | awp | Conector | `-675,-1111,-177` | `-0°,-122°` | 195.4 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_top_mid_boxes)) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | Mercado / Kitchen | `-1872,-304,-149` | `0°,58°` | 0.0 (Z -212 / 3D 212 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_mid_window_crouch)) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Apartamentos B | `576,779,-136` | `0°,176°` | 0.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | None |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | Mercado / Kitchen | `-1660,-696,-168` | `0°,93°` | 173.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | famas | Bomb A | `-96,-1622,-168` | `0°,28°` | 220.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | ak47 | Catwalk / Short | `-848,-256,-167` | `0°,98°` | 204.4 | PASSIVE_HOLD | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Apartamentos B | `544,774,-136` | `0°,-41°` | 36.9 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_t_roof)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | famas | Bomb B | `-2100,-234,-165` | `0°,24°` | 164.1 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_site_default_crouch)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | famas | CT Spawn | `-1527,-1313,-260` | `0°,-92°` | 220.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_short_corner)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Meio | `-245,-642,-248` | `0°,-150°` | 40.6 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Hotzone_PreMapped` em `(-675, -1111, -177)` [Mira: Yaw -122° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Diag-Dir(250u)` | **125ms:** `Diag-Dir(250u)` | **250ms:** `Diag-Dir(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Hotzone_PreMapped` em `(-1583, -725, -168)` [Mira: Yaw 93° | CPU: `0.74ms`] -> Horizontes: **0ms:** `Recuo-Esq(250u)` | **125ms:** `Recuo-Esq(250u)` | **250ms:** `Recuo-Esq(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-578, -726, -268)` [Mira: Yaw -108° | CPU: `0.71ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Diag-Esq(250u+Jump)` | **250ms:** `Diag-Esq(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Vision_Spotted` em `(-1007, 188, -173)` [Mira: Yaw 177° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Syfers** acionou `Vision_Spotted` em `(-1620, 92, -168)` [Mira: Yaw 9° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Dir(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(Shift)`

<details><summary><b>📊 Snapshot Tático das [04:39] (10 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | awp | Conector | `-808,-1236,-120` | `-0°,-124°` | 0.0 (Z -164 / 3D 164 aéreo) | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_top_mid_boxes)) | Pending | None |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | Mercado / Kitchen | `-1800,-511,-168` | `-0°,107°` | 176.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_mid_window_crouch)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Apartamentos B | `608,766,-136` | `-1°,176°` | 181.6 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1408,-1100,-168` | `0°,93°` | 6.5 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | None |
| 5 | Soldier (Rotator) | CT | 100 | famas | Rampa A | `426,-1569,-225` | `-1°,27°` | 220.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | ak47 | Catwalk / Short | `-1030,191,-173` | `2°,-175°` | 71.3 | PASSIVE_HOLD | CounterStrafe | Recuo(250u) | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Apartamentos B | `562,789,-136` | `-1°,-36°` | 27.9 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_t_roof)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | famas | Bomb B | `-1610,99,-168` | `0°,9°` | 166.6 | PASSIVE_HOLD | ONNX_Vision_Spotted | Diag-Dir(250u) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act3) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | famas | CT Spawn | `-1534,-1967,-264` | `-1°,-75°` | 212.7 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_short_corner)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Meio | `-611,-740,-262` | `-1°,-96°` | 0.0 | PASSIVE_HOLD | Nenhuma | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act41) | Pending | None |

</details>

- **`[04:39]`** `[COMBATE]` **Syfers** causou **80 HP** em **Shamat** com **famas** a **584u** (HP 100→20, raw=80, overkill=0, setor: Catwalk / Short)
- **`[04:39]`** `[MORTE]` **Syfers** eliminou **Shamat** com **famas** no setor **Catwalk / Short**
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Hotzone_PreMapped` em `(-687, -1238, -153)` [Mira: Yaw 86° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Recuo-Esq(250u+Jump)` | **125ms:** `Strafe-Esq(250u+Jump)` | **250ms:** `Strafe-Esq(Duck+Jump)`

<details><summary><b>📊 Snapshot Tático das [04:39] (9 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | awp | Bomb A | `-672,-1318,-168` | `-0°,86°` | 200.0 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_top_mid_boxes)) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | Mercado / Kitchen | `-1872,-338,-168` | `-0°,100°` | 0.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_mid_window_crouch)) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Beco | `394,360,-259` | `-2°,-111°` | 204.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1335,-965,-168` | `-2°,9°` | 51.5 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | famas | Palácio A | `736,-1177,-259` | `-2°,32°` | 185.8 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Apartamentos B | `595,747,-136` | `-2°,-104°` | 185.2 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_t_roof)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | famas | Bomb B | `-1183,174,-170` | `-2°,0°` | 211.8 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | famas | CT Spawn | `-1457,-2224,-242` | `-2°,103°` | 220.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_short_corner)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Meio | `-625,-721,-267` | `-2°,17°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-431, -671, -273)` [Mira: Yaw 10° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Hotzone_PreMapped` em `(-1252, -947, -168)` [Mira: Yaw 57° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Avanco(Duck)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Hotzone_PreMapped` em `(-667, -1236, -168)` [Mira: Yaw 85° | CPU: `0.65ms`] -> Horizontes: **0ms:** `Strafe-Esq(Duck)` | **125ms:** `Parado (0u)` | **250ms:** `Strafe-Esq(Duck)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-1872, -304, -106)` [Mira: Yaw 74° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(Duck+Jump)` | **125ms:** `Avanco(Duck+Jump)` | **250ms:** `Recuo(Duck)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(1114, -1013, -258)` [Mira: Yaw 84° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Diag-Esq(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Syfers** acionou `Vision_Spotted` em `(-798, 69, -166)` [Mira: Yaw -73° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Vision_Spotted` em `(-1569, -1793, -267)` [Mira: Yaw 94° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[04:39]`** `[COMBATE]` **Syfers** causou **20 HP** em **Shark** com **hkp2000** a **1273u** (HP 100→80, raw=20, overkill=0, setor: Conector)

<details><summary><b>📊 Snapshot Tático das [04:39] (9 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 62 | awp | Conector | `-681,-1236,-168` | `1°,95°` | 0.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | Mercado / Kitchen | `-1872,-304,-168` | `-2°,60°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Strafe-Esq(Shift) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act32) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Top Mid | `272,-222,-168` | `-2°,-150°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1227,-931,-168` | `-2°,63°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 5 | Soldier (Rotator) | CT | 100 | famas | Palácio A | `1129,-989,-259` | `-2°,90°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Strafe-Esq(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act33) | Pending | None |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Beco | `386,339,-258` | `-2°,-112°` | 211.1 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_t_roof)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | hkp2000 | Catwalk / Short | `-789,32,-167` | `2°,-85°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Strafe-Dir(Shift) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act17) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | famas | CT Spawn | `-1573,-1756,-265` | `-2°,93°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Meio | `-278,-617,-241` | `-2°,37°` | 89.6 (Z 264 / 3D 279 aéreo) | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Strafe-Esq(Duck) | EmergencyFallback:NavigateNavMesh(AlertNearbyTeammatesOfThreat_TradeFocus) | Pending | Movendo |

</details>

- **`[04:39]`** `[COMBATE]` **Shark** causou **100 HP** em **Syfers** com **awp** a **1273u** (HP 100→0, raw=136, overkill=36, setor: Catwalk / Short)
- **`[04:39]`** `[MORTE]` **Shark** eliminou **Syfers** com **awp** no setor **Catwalk / Short**
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Audio_HeardCue` em `(-412, -739, -239)` [Mira: Yaw 37° | CPU: `0.73ms`] -> Horizontes: **0ms:** `Recuo(250u+Jump)` | **125ms:** `Recuo(250u)` | **250ms:** `Recuo-Esq(Duck+Jump)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1227, -931, -168)` [Mira: Yaw 62° | CPU: `0.73ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck)` | **125ms:** `Parado (0u)` | **250ms:** `Strafe-Dir(Duck)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Audio_HeardCue` em `(-681, -1236, -168)` [Mira: Yaw 93° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Hotzone_PreMapped` em `(62, -337, -180)` [Mira: Yaw -176° | CPU: `0.73ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Diag-Esq(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-1907, -318, -120)` [Mira: Yaw -29° | CPU: `0.85ms`] -> Horizontes: **0ms:** `Recuo-Esq(250u+Jump)` | **125ms:** `Recuo-Esq(250u)` | **250ms:** `Recuo-Esq(250u+Jump)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(1130, -917, -262)` [Mira: Yaw 89° | CPU: `0.85ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Vision_Spotted` em `(-1576, -1572, -263)` [Mira: Yaw 91° | CPU: `0.85ms`] -> Horizontes: **0ms:** `Avanco(Duck)` | **125ms:** `Diag-Esq(Duck)` | **250ms:** `Avanco(Duck)`

<details><summary><b>📊 Snapshot Tático das [04:39] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 42 | awp | Conector | `-650,-1044,-169` | `0°,74°` | 188.1 (Z 164 / 3D 250 aéreo) | JIGGLE_INFO | ONNX_Audio_HeardCue | Avanco(Duck+Jump) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act84) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | Mercado / Kitchen | `-1933,-296,-164` | `-1°,-69°` | 100.2 (Z -289 / 3D 306 aéreo) | PASSIVE_HOLD | ONNX_Vision_Spotted | Recuo-Dir(250u+Jump) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act51) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Catwalk / Short | `-113,-377,-167` | `-1°,177°` | 0.0 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Recuo-Esq(Shift) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act19) | Pending | None |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1128,-788,-168` | `-1°,65°` | 14.9 | PASSIVE_HOLD | ONNX_Vision_Spotted | Recuo-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act41) | Pending | None |
| 5 | Soldier (Rotator) | CT | 100 | famas | Palácio A | `1131,-881,-260` | `-1°,88°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Top Mid | `260,-214,-168` | `-1°,-143°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_t_roof)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | famas | CT Spawn | `-1577,-1569,-263` | `-1°,91°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Meio | `-315,-637,-263` | `-1°,16°` | 211.9 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1129, -788, -168)` [Mira: Yaw 72° | CPU: `0.73ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Audio_HeardCue` em `(-615, -902, -233)` [Mira: Yaw 53° | CPU: `0.63ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - TRADE SPACING]` **Rebel** (`yielding_slot=7`) cedeu espaço para **Steel** (`priority_slot=10`) | `dist_before=79u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=5`.
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-25, -468, -168)` [Mira: Yaw 167° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Avanco(Duck)` | **125ms:** `Avanco(Shift)` | **250ms:** `Avanco(Shift)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-1918, -300, -168)` [Mira: Yaw -65° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(1131, -881, -260)` [Mira: Yaw 91° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Strafe-Esq(Duck)` | **125ms:** `Strafe-Esq(Duck)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Vision_Spotted` em `(-1583, -1418, -264)` [Mira: Yaw 93° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Avanco(Duck)` | **125ms:** `Parado (0u)` | **250ms:** `Avanco(Duck)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Hotzone_PreMapped` em `(-544, -392, -168)` [Mira: Yaw 143° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Diag-Dir(250u)` | **125ms:** `Diag-Dir(250u)` | **250ms:** `Diag-Dir(250u)`

<details><summary><b>📊 Snapshot Tático das [04:39] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 42 | awp | Conector | `-608,-882,-186` | `0°,49°` | 158.1 (Z 164 / 3D 228 aéreo) | JIGGLE_INFO | ONNX_Audio_HeardCue | Avanco(Duck+Jump) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act83) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | Mercado / Kitchen | `-1918,-300,-168` | `0°,-64°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Strafe-Esq(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act42) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Catwalk / Short | `-578,-400,-168` | `0°,129°` | 0.0 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Recuo-Esq(Duck) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act33) | Pending | None |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1129,-788,-168` | `0°,75°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Strafe-Esq(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act48) | Pending | None |
| 5 | Soldier (Rotator) | CT | 100 | famas | Palácio A | `1131,-881,-260` | `0°,91°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Catwalk / Short | `-147,-453,-114` | `0°,173°` | 214.6 (Z -86 / 3D 231 aéreo) | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Avanco(250u) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act9) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | famas | CT Spawn | `-1583,-1418,-264` | `0°,93°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Recuo-Esq(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act47) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Catwalk / Short | `-34,-464,-168` | `0°,170°` | 0.0 | PASSIVE_HOLD | Nenhuma | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act38) | Pending | None |

</details>

- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1129, -788, -168)` [Mira: Yaw 75° | CPU: `0.72ms`] -> Horizontes: **0ms:** `Recuo(Duck)` | **125ms:** `Parado (0u)` | **250ms:** `Recuo(Duck)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Audio_HeardCue` em `(-719, -904, -198)` [Mira: Yaw 42° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Recuo(Duck+Jump)` | **125ms:** `Recuo(Duck+Jump)` | **250ms:** `Recuo-Esq(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Hotzone_PreMapped` em `(-534, -423, -168)` [Mira: Yaw 143° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Diag-Dir(250u)` | **125ms:** `Diag-Dir(250u)` | **250ms:** `Diag-Dir(250u)`

<details><summary><b>📊 Snapshot Tático das [04:39] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 42 | awp | Conector | `-749,-1195,-168` | `0°,63°` | 41.2 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | Mercado / Kitchen | `-1885,-473,-168` | `2°,-50°` | 76.7 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Catwalk / Short | `-800,-28,-168` | `2°,130°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1142,-823,-168` | `2°,71°` | 203.7 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | famas | TR Spawn | `1130,-541,-191` | `2°,88°` | 220.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Catwalk / Short | `-569,-430,-168` | `2°,130°` | 6.2 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Diag-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act41) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | famas | CT Spawn | `-1608,-1061,-221` | `1°,92°` | 220.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_short_corner)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Catwalk / Short | `-431,-383,-167` | `2°,157°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-548, -388, -168)` [Mira: Yaw 142° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Dir(250u)` | **125ms:** `Diag-Dir(250u)` | **250ms:** `Diag-Dir(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Hotzone_PreMapped` em `(-1150, -814, -168)` [Mira: Yaw 91° | CPU: `0.73ms`] -> Horizontes: **0ms:** `Recuo(250u)` | **125ms:** `Recuo-Dir(250u)` | **250ms:** `Recuo-Dir(250u)`
- **`[04:39]`** `[MLMOVE - TRADE SPACING]` **Buckshot** (`yielding_slot=9`) cedeu espaço para **Ricksaw** (`priority_slot=2`) | `dist_before=81u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=15`.
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Audio_HeardCue` em `(-630, -980, -216)` [Mira: Yaw 80° | CPU: `0.73ms`] -> Horizontes: **0ms:** `Avanco(Duck)` | **125ms:** `Avanco(Duck)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-1625, -697, -168)` [Mira: Yaw -78° | CPU: `0.73ms`] -> Horizontes: **0ms:** `Avanco(Shift)` | **125ms:** `Avanco(250u)` | **250ms:** `Diag-Esq(Shift)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(1158, -79, -165)` [Mira: Yaw 86° | CPU: `0.73ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`

<details><summary><b>📊 Snapshot Tático das [04:39] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 42 | awp | Conector | `-630,-978,-216` | `0°,63°` | 0.0 | JIGGLE_INFO | Nenhuma | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act44) | Pending | None |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | Mercado / Kitchen | `-1627,-721,-163` | `2°,-44°` | 0.0 (Z 289 / 3D 289 aéreo) | PASSIVE_HOLD | ONNX_Vision_Spotted | Diag-Esq(Shift) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act29) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 100 | famas | Catwalk / Short | `-1048,192,-173` | `2°,-163°` | 113.6 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1149,-847,-168` | `0°,93°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Strafe-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act41) | Pending | None |
| 5 | Soldier (Rotator) | CT | 100 | famas | TR Spawn | `1162,-42,-165` | `2°,92°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Catwalk / Short | `-665,-344,-160` | `2°,112°` | 0.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:HoldStop(SpotHold_PASSIVE_HOLD) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | famas | Mercado / Kitchen | `-1590,-675,-168` | `2°,144°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Strafe-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act43) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Catwalk / Short | `-633,-345,-160` | `2°,120°` | 12.5 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | None |

</details>

- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-610, -406, -95)` [Mira: Yaw 116° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Recuo(250u)` | **125ms:** `Recuo-Dir(250u+Jump)` | **250ms:** `Recuo-Dir(Duck+Jump)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1149, -847, -168)` [Mira: Yaw 93° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Vision_Spotted` em `(-1590, -675, -168)` [Mira: Yaw 144° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Dir(Duck)` | **125ms:** `Diag-Dir(Duck)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Audio_HeardCue` em `(-588, -879, -149)` [Mira: Yaw 56° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Recuo-Esq(250u)` | **125ms:** `Recuo-Esq(250u+Jump)` | **250ms:** `Recuo-Esq(250u+Jump)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-1436, -941, -168)` [Mira: Yaw -49° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(1158, 112, -165)` [Mira: Yaw 105° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck)` | **125ms:** `Parado (0u)` | **250ms:** `Strafe-Dir(Duck)`

<details><summary><b>📊 Snapshot Tático das [04:39] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 42 | awp | Conector | `-632,-1020,-174` | `0°,51°` | 218.6 (Z -238 / 3D 323 aéreo) | JIGGLE_INFO | ONNX_Audio_HeardCue | Recuo(250u+Jump) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act60) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | CT Spawn | `-1436,-941,-168` | `2°,-53°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 100 | famas | Bomb B | `-1587,246,-170` | `2°,-179°` | 220.0 | PASSIVE_HOLD | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1149,-859,-137` | `0°,93°` | 164.7 (Z 199 / 3D 258 aéreo) | PASSIVE_HOLD | ONNX_Vision_Spotted | Recuo(Shift+Jump) | Unstuck:UsercmdVector(STAGE1_CANCEL_MICROMOVE_AND_STRAFE_UNSTUCK) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | famas | TR Spawn | `1158,112,-165` | `2°,108°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Catwalk / Short | `-665,-343,-160` | `2°,112°` | 18.5 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_t_roof)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | famas | Mercado / Kitchen | `-1699,-597,-147` | `2°,145°` | 214.9 (Z -264 / 3D 340 aéreo) | PASSIVE_HOLD | ONNX_Vision_Spotted | Avanco(250u+Jump) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act55) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Meio | `-345,-609,-269` | `2°,135°` | 192.1 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Hotzone_PreMapped` em `(-1622, -657, -168)` [Mira: Yaw 130° | CPU: `0.65ms`] -> Horizontes: **0ms:** `Diag-Esq(Shift)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Diag-Esq(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Hotzone_PreMapped` em `(-668, -1099, -116)` [Mira: Yaw 73° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Avanco(250u+Jump)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(Duck)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-1428, -961, -168)` [Mira: Yaw -48° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Diag-Dir(250u)` | **125ms:** `Diag-Dir(250u)` | **250ms:** `Diag-Dir(Duck)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1138, -1159, -168)` [Mira: Yaw 59° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck)` | **125ms:** `Strafe-Esq(Duck)` | **250ms:** `Strafe-Dir(Duck)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(1069, 379, -261)` [Mira: Yaw 166° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`

<details><summary><b>📊 Snapshot Tático das [04:39] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 42 | awp | Conector | `-628,-1013,-216` | `0°,66°` | 12.1 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | CT Spawn | `-1400,-960,-168` | `6°,37°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 100 | c4 | Bomb B | `-2013,157,-160` | `0°,-79°` | 0.0 | PASSIVE_HOLD | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | None |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1151,-1154,-168` | `1°,-25°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Diag-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act33) | Pending | None |
| 5 | Soldier (Rotator) | CT | 100 | famas | TR Spawn | `1046,396,-259` | `0°,171°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Strafe-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act45) | Pending | None |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Catwalk / Short | `-863,159,-173` | `0°,160°` | 196.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_t_roof)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | famas | Mercado / Kitchen | `-1617,-640,-168` | `7°,-70°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Meio | `-149,-539,-223` | `0°,-86°` | 152.8 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Vision_Spotted` em `(-1617, -640, -168)` [Mira: Yaw 144° | CPU: `0.72ms`] -> Horizontes: **0ms:** `Strafe-Esq(Shift)` | **125ms:** `Parado (0u)` | **250ms:** `Strafe-Esq(Shift)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Audio_HeardCue` em `(-580, -860, -168)` [Mira: Yaw 39° | CPU: `0.75ms`] -> Horizontes: **0ms:** `Recuo-Esq(Duck)` | **125ms:** `Recuo-Esq(Duck)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-1400, -960, -168)` [Mira: Yaw 26° | CPU: `0.71ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1151, -1154, -168)` [Mira: Yaw 98° | CPU: `0.71ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(930, 475, -254)` [Mira: Yaw -179° | CPU: `0.71ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`

<details><summary><b>📊 Snapshot Tático das [04:39] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 42 | awp | Conector | `-591,-876,-135` | `0°,39°` | 201.3 (Z 21 / 3D 202 aéreo) | JIGGLE_INFO | ONNX_Audio_HeardCue | Recuo(Duck+Jump) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act91) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | CT Spawn | `-1400,-960,-168` | `-1°,-2°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 100 | c4 | Bomb B | `-2013,157,-160` | `-1°,-80°` | 0.0 | PASSIVE_HOLD | Nenhuma | BombObjective:ReleaseHoldAndRepath(C4Carrier_InBombZone_AuthorizedToPlant) | Pending | None |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1151,-1154,-168` | `8°,97°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 5 | Soldier (Rotator) | CT | 100 | famas | TR Spawn | `930,475,-254` | `-1°,-180°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Diag-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act44) | Pending | None |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Catwalk / Short | `-757,-24,-162` | `-1°,-73°` | 204.1 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_t_roof)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | famas | Mercado / Kitchen | `-1617,-640,-168` | `-1°,137°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Meio | `-591,-539,-271` | `0°,-80°` | 7.9 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | None |

</details>

- **`[04:39]`** `[BOMBA]` C4 plantada no bombsite!
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-381, -626, -272)` [Mira: Yaw 3° | CPU: `0.75ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Strafe-Esq(250u)` | **250ms:** `Diag-Esq(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Vision_Spotted` em `(-1695, -696, -132)` [Mira: Yaw -172° | CPU: `0.65ms`] -> Horizontes: **0ms:** `Avanco(250u+Jump)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Audio_HeardCue` em `(-580, -860, -168)` [Mira: Yaw 44° | CPU: `0.63ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Hotzone_PreMapped` em `(-613, -379, -168)` [Mira: Yaw -23° | CPU: `0.63ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-1477, -927, -122)` [Mira: Yaw 135° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Diag-Dir(250u+Jump)` | **125ms:** `Diag-Dir(250u+Jump)` | **250ms:** `Strafe-Dir(250u+Jump)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1184, -1171, -168)` [Mira: Yaw 114° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Strafe-Dir(250u)` | **125ms:** `Recuo-Dir(250u)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(821, 594, -196)` [Mira: Yaw -161° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`

<details><summary><b>📊 Snapshot Tático das [04:39] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 42 | awp | Conector | `-640,-935,-161` | `0°,40°` | 216.3 (Z -144 / 3D 260 aéreo) | JIGGLE_INFO | ONNX_Audio_HeardCue | Recuo(250u+Jump) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act59) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | CT Spawn | `-1559,-923,-184` | `-2°,131°` | 22.6 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Avanco(Duck) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | famas | Bomb B | `-2089,507,-168` | `-2°,124°` | 201.4 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1217,-1247,-168` | `-2°,-134°` | 181.6 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Avanco(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | famas | TR Spawn | `756,550,-152` | `-2°,-158°` | 140.9 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Diag-Dir(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Catwalk / Short | `-580,-394,-168` | `-2°,-17°` | 0.0 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Strafe-Esq(Duck) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act45) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | famas | Mercado / Kitchen | `-1804,-641,-168` | `-2°,109°` | 202.5 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Diag-Dir(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Meio | `-227,-613,-246` | `-2°,44°` | 0.0 | AGGRESSIVE_POKE | ONNX_Hotzone_PreMapped | Recuo-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act40) | Pending | None |

</details>

- **`[04:39]`** `[MLMOVE - COUNTER-STRAFE]` **Buckshot** aplicou *Velocity Zeroing* contra **Delrow** (`dist_2d=1104u`, `aim_error=4.5° <= 16°`, `vel_before=220 u/s`, `ammo=25`, `pulso=99ms`, `action=14`) com `famas`.
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Hotzone_PreMapped` em `(-469, -438, -122)` [Mira: Yaw -8° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Recuo(250u+Jump)` | **125ms:** `Recuo(250u+Jump)` | **250ms:** `Recuo(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Audio_HeardCue` em `(-1868, -636, -168)` [Mira: Yaw -170° | CPU: `0.75ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(250u+Jump)`

<details><summary><b>📊 Snapshot Tático das [04:39] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 42 | awp | Conector | `-732,-1173,-106` | `0°,71°` | 212.2 (Z 61 / 3D 221 aéreo) | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | Mercado / Kitchen | `-1881,-639,-168` | `-2°,-170°` | 225.0 | AGGRESSIVE_POKE | ONNX_Audio_HeardCue | Avanco(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | famas | Bomb B | `-2113,624,-154` | `-0°,152°` | 121.7 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1356,-965,-168` | `6°,-79°` | 64.5 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | famas | Beco | `310,322,-263` | `-2°,-86°` | 220.0 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Catwalk / Short | `-590,-433,-168` | `-2°,-8°` | 28.6 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_t_roof)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | famas | Mercado / Kitchen | `-1936,-296,-168` | `-0°,108°` | 0.0 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Parado (0u) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Catwalk / Short | `-43,-486,-167` | `-2°,169°` | 167.2 | AGGRESSIVE_POKE | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-54, -484, -166)` [Mira: Yaw 169° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Audio_HeardCue` em `(-702, -1045, -210)` [Mira: Yaw 72° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(Duck)` | **125ms:** `Parado (0u)` | **250ms:** `Diag-Esq(Duck)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1422, -936, -168)` [Mira: Yaw -151° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Diag-Esq(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(322, 187, -256)` [Mira: Yaw -90° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Recuo-Esq(Duck)` | **250ms:** `Avanco(250u+Jump)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Vision_Spotted` em `(-1936, -296, -168)` [Mira: Yaw 108° | CPU: `0.71ms`] -> Horizontes: **0ms:** `Diag-Dir(Duck)` | **125ms:** `Diag-Dir(Duck)` | **250ms:** `Diag-Dir(Duck+Jump)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Vision_Spotted` em `(-179, -488, -166)` [Mira: Yaw 16° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Avanco(250u)`
- **`[04:39]`** `[COMBATE]` **Soldier** causou **19 HP** em **Rebel** com **famas** a **642u** (HP 100→81, raw=19, overkill=0, setor: Catwalk / Short)
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-2305, -445, -168)` [Mira: Yaw 80° | CPU: `0.76ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(250u+Jump)`

<details><summary><b>📊 Snapshot Tático das [04:39] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 42 | awp | Conector | `-690,-896,-236` | `-13°,69°` | 0.0 | JIGGLE_INFO | ONNX_Audio_HeardCue | Strafe-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act40) | Pending | None |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | Mercado / Kitchen | `-2306,-432,-168` | `-1°,79°` | 210.7 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Avanco(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | famas | Bomb B | `-1647,278,-171` | `-0°,152°` | 217.4 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | Mercado / Kitchen | `-1757,-645,-168` | `-1°,176°` | 225.0 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Avanco(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | famas | Top Mid | `368,-119,-165` | `-0°,-145°` | 0.0 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Strafe-Esq(Duck) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 7 | Rebel (Anchor) | TR | 31 | ak47 | Catwalk / Short | `-154,-493,-105` | `10°,35°` | 0.0 (Z 56 / 3D 56 aéreo) | PASSIVE_HOLD | ONNX_Vision_Spotted | Recuo-Dir(Duck+Jump) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act89) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | famas | Mercado / Kitchen | `-1936,-296,-168` | `-0°,108°` | 0.0 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Avanco(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Catwalk / Short | `-373,-427,-153` | `2°,34°` | 73.0 (Z 264 / 3D 274 aéreo) | AGGRESSIVE_POKE | ONNX_Audio_HeardCue | Diag-Dir(Duck+Jump) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act85) | Pending | Movendo |

</details>

- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Audio_HeardCue` em `(-367, -422, -138)` [Mira: Yaw 30° | CPU: `0.73ms`] -> Horizontes: **0ms:** `Avanco(250u+Jump)` | **125ms:** `Diag-Dir(250u+Jump)` | **250ms:** `Strafe-Esq(250u)`
- **`[04:39]`** `[MORTE]` **Soldier** eliminou **Rebel** com **famas** no setor **Catwalk / Short**
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Audio_HeardCue` em `(-720, -976, -184)` [Mira: Yaw 68° | CPU: `0.71ms`] -> Horizontes: **0ms:** `Recuo(250u+Jump)` | **125ms:** `Recuo(250u+Jump)` | **250ms:** `Recuo(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(364, -122, -165)` [Mira: Yaw -143° | CPU: `0.71ms`] -> Horizontes: **0ms:** `Avanco(Shift)` | **125ms:** `Avanco(Duck)` | **250ms:** `Recuo(Shift)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1871, -568, -168)` [Mira: Yaw 135° | CPU: `0.75ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(250u)`
- **`[04:39]`** `[MLMOVE - TRADE SPACING]` **Buckshot** (`yielding_slot=9`) cedeu espaço para **Commando** (`priority_slot=4`) | `dist_before=139u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=5`.
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-2321, -222, -167)` [Mira: Yaw 22° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`

<details><summary><b>📊 Snapshot Tático das [04:39] (7 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 42 | awp | Conector | `-727,-1234,-111` | `-4°,-143°` | 331.8 (Z -114 / 3D 351 aéreo) | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | m4a1 | Bomb B | `-2321,-222,-167` | `2°,22°` | 0.0 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Parado (0u) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 100 | famas | Bomb B | `-1367,112,-162` | `0°,149°` | 85.1 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | Mercado / Kitchen | `-1931,-296,-168` | `-0°,-160°` | 15.0 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Diag-Esq(Duck+Jump) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 5 | Soldier (Rotator) | CT | 100 | famas | Catwalk / Short | `7,-454,-176` | `-1°,-149°` | 209.7 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Avanco(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | famas | Mercado / Kitchen | `-1958,-333,-168` | `-0°,108°` | 0.0 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Diag-Esq(Duck) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Catwalk / Short | `-220,-332,-158` | `13°,-21°` | 0.0 (Z -286 / 3D 286 aéreo) | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Recuo-Dir(Duck+Jump) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act87) | Pending | None |

</details>

- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Vision_Spotted` em `(-220, -332, -164)` [Mira: Yaw -23° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Vision_Spotted` em `(-1378, 123, -163)` [Mira: Yaw 145° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Avanco(Shift)` | **125ms:** `Avanco(250u)` | **250ms:** `Diag-Dir(250u)`
- **`[04:39]`** `[COMBATE]` **Ricksaw** causou **16 HP** em **Delrow** com **m4a1** a **987u** (HP 100→84, raw=16, overkill=0, setor: Bomb B)
- **`[04:39]`** `[MLMOVE - COUNTER-STRAFE]` **Soldier** aplicou *Velocity Zeroing* contra **Steel** (`dist_2d=189u`, `aim_error=15.2° <= 16°`, `vel_before=171 u/s`, `ammo=17`, `pulso=80ms`, `action=3`) com `famas`.
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Vision_Spotted` em `(-662, -1193, -168)` [Mira: Yaw 66° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1889, -335, -104)` [Mira: Yaw 115° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Recuo(250u+Jump)` | **125ms:** `Recuo(250u+Jump)` | **250ms:** `Recuo-Esq(250u+Jump)`
- **`[04:39]`** `[MLMOVE - TRADE SPACING]` **Buckshot** (`yielding_slot=9`) cedeu espaço para **Commando** (`priority_slot=4`) | `dist_before=77u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=7`.
- **`[04:39]`** `[COMBATE]` **Steel** causou **34 HP** em **Soldier** com **ak47** a **192u** (HP 100→66, raw=34, overkill=0, setor: Catwalk / Short)
- **`[04:39]`** `[COMBATE]` **Soldier** causou **25 HP** em **Steel** com **famas** a **192u** (HP 100→75, raw=25, overkill=0, setor: Catwalk / Short)
- **`[04:39]`** `[MORTE]` **Soldier** eliminou **Steel** com **famas** no setor **Catwalk / Short**
- **`[04:39]`** `[COMBATE]` **Delrow** causou **20 HP** em **Ricksaw** com **famas** a **974u** (HP 100→80, raw=20, overkill=0, setor: Bomb B)
- **`[04:39]`** `[MORTE]` **Ricksaw** eliminou **Delrow** com **m4a1_silencer** no setor **Bomb B**

<details><summary><b>📊 Snapshot Tático das [04:39] (5 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 42 | awp | Conector | `-659,-1200,-168` | `-0°,80°` | 0.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Strafe-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act41) | Pending | None |
| 2 | Ricksaw (Rotator) | CT | 80 | m4a1 | Bomb B | `-2300,-286,-168` | `3°,39°` | 49.9 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | Mercado / Kitchen | `-1931,-296,-146` | `0°,173°` | 162.2 (Z 261 / 3D 308 aéreo) | AGGRESSIVE_POKE | Nenhuma | Unstuck:UsercmdVector(STAGE1_CANCEL_MICROMOVE_AND_STRAFE_UNSTUCK) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 4 | famas | Catwalk / Short | `-216,-377,-167` | `1°,174°` | 107.2 | AGGRESSIVE_POKE | ONNX_Audio_HeardCue | Avanco(Duck) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | famas | Mercado / Kitchen | `-1956,-335,-138` | `0°,101°` | 134.4 (Z 236 / 3D 272 aéreo) | AGGRESSIVE_POKE | Nenhuma | Unstuck:UsercmdVector(STAGE1_CANCEL_MICROMOVE_AND_STRAFE_UNSTUCK) | Pending | Movendo |

</details>

- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Audio_HeardCue` em `(-295, -370, -167)` [Mira: Yaw 176° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Vision_Spotted` em `(-659, -1200, -168)` [Mira: Yaw 80° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Strafe-Esq(Duck)` | **125ms:** `Strafe-Esq(Duck)` | **250ms:** `Recuo(Duck)`

<details><summary><b>📊 Snapshot Tático das [04:39] (5 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 42 | awp | Conector | `-687,-1207,-168` | `1°,82°` | 0.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Avanco(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act37) | Pending | None |
| 2 | Ricksaw (Rotator) | CT | 80 | m4a1 | Bomb B | `-2061,100,-160` | `2°,55°` | 140.6 | AGGRESSIVE_POKE | Nenhuma | BombObjective:NavigateNavMesh(CT_DefuseObjective) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | Mercado / Kitchen | `-1924,-314,-115` | `0°,148°` | 96.5 (Z 136 / 3D 167 aéreo) | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 4 | famas | Catwalk / Short | `-533,-408,-168` | `4°,140°` | 0.0 | AGGRESSIVE_POKE | ONNX_Hotzone_PreMapped | Diag-Dir(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | famas | Mercado / Kitchen | `-1892,-304,-168` | `0°,51°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |

</details>

- **`[04:39]`** `[DEFUSE]` Jogador Ricksaw iniciou desarme da C4!
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-2055, 112, -160)` [Mira: Yaw 52° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1929, -345, -106)` [Mira: Yaw -141° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Avanco(250u+Jump)` | **125ms:** `Diag-Esq(250u+Jump)` | **250ms:** `Avanco(Duck+Jump)`
- **`[04:39]`** `[MLMOVE - TRADE SPACING]` **Buckshot** (`yielding_slot=9`) cedeu espaço para **Commando** (`priority_slot=4`) | `dist_before=69u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=1`.
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(-533, -408, -168)` [Mira: Yaw -118° | CPU: `0.72ms`] -> Horizontes: **0ms:** `Recuo-Dir(Duck)` | **125ms:** `Parado (0u)` | **250ms:** `Recuo-Dir(Duck)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Audio_HeardCue` em `(-679, -1209, -140)` [Mira: Yaw 80° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck+Jump)` | **125ms:** `Strafe-Dir(Duck+Jump)` | **250ms:** `Strafe-Esq(Shift)`
- **`[04:39]`** `[MLMOVE - TRADE SPACING]` **Buckshot** (`yielding_slot=9`) cedeu espaço para **Commando** (`priority_slot=4`) | `dist_before=38u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=16`.

<details><summary><b>📊 Snapshot Tático das [04:39] (5 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 42 | awp | Conector | `-679,-1209,-131` | `2°,91°` | 0.0 (Z 214 / 3D 214 aéreo) | JIGGLE_INFO | ONNX_Vision_Spotted | Diag-Dir(Duck+Jump) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act87) | Pending | None |
| 2 | Ricksaw (Rotator) | CT | 80 | m4a1 | Bomb B | `-2055,112,-160` | `2°,-150°` | 0.0 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Parado (0u) | BombObjective:NavigateNavMesh(CT_DefuseObjective) | Pending | None |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | Mercado / Kitchen | `-1935,-296,-168` | `0°,50°` | 6.7 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Diag-Dir(Duck) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 5 | Soldier (Rotator) | CT | 4 | famas | Catwalk / Short | `-731,-373,-168` | `2°,169°` | 182.0 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Diag-Esq(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | famas | Mercado / Kitchen | `-1902,-300,-168` | `0°,-106°` | 38.2 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Recuo(Duck+Jump) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |

</details>

- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-2051, 119, -160)` [Mira: Yaw 166° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Recuo-Esq(Duck)` | **125ms:** `Strafe-Esq(Shift)` | **250ms:** `Diag-Esq(Duck)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1935, -296, -168)` [Mira: Yaw 44° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(-769, -279, -160)` [Mira: Yaw 114° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Diag-Esq(250u+Jump)` | **250ms:** `Diag-Esq(250u+Jump)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Vision_Spotted` em `(-680, -1190, -153)` [Mira: Yaw 94° | CPU: `0.65ms`] -> Horizontes: **0ms:** `Avanco(Duck+Jump)` | **125ms:** `Avanco(Duck)` | **250ms:** `Diag-Dir(Duck)`
- **`[04:39]`** `[COMBATE]` **Shark** causou **66 HP** em **Soldier** com **awp** a **981u** (HP 66→0, raw=84, overkill=18, setor: Catwalk / Short)
- **`[04:39]`** `[PIVOT TÁTICO TR]` First Kill conquistado por **Shark** (`setor_killer=Conector`) sobre **Soldier** (`setor_vitima=Catwalk / Short`) | C4: **Shark** (`setor_c4=Conector`, `distA=1075u`, `distB=1898u`) | Vivos: `1v4` | Transição imediata `rev=2`: `Defesa 2-1-2 Padrão Equilibrada` -> `Exploit 5v4 -> Execução Bomb B (Pick em Catwalk / Short)` (Alvo: **Bomb B**, `conf=0.88`).
- **`[04:39]`** `[MORTE]` **Shark** eliminou **Soldier** com **awp** no setor **Catwalk / Short**
- **`[04:39]`** `[DEFUSE]` Jogador Ricksaw iniciou desarme da C4!
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Vision_Spotted` em `(-1987, -201, -148)` [Mira: Yaw 158° | CPU: `0.72ms`] -> Horizontes: **0ms:** `Avanco(250u+Jump)` | **125ms:** `Strafe-Esq(Duck+Jump)` | **250ms:** `Avanco(Shift)`

<details><summary><b>📊 Snapshot Tático das [04:39] (4 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 42 | awp | Conector | `-672,-1239,-114` | `2°,96°` | 209.9 (Z 64 / 3D 220 aéreo) | JIGGLE_INFO | Nenhuma | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act61) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 80 | m4a1 | Bomb B | `-2037,163,-160` | `69°,-15°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | BombObjective:NavigateNavMesh(CT_DefuseObjective) | Pending | None |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | Mercado / Kitchen | `-1957,-524,-168` | `1°,-40°` | 219.0 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | famas | Bomb B | `-2031,-179,-121` | `1°,161°` | 213.6 (Z 9 / 3D 214 aéreo) | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |

</details>

- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Hotzone_PreMapped` em `(-1613, -685, -168)` [Mira: Yaw -7° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Diag-Esq(Shift)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Strafe-Esq(250u)`

<details><summary><b>📊 Snapshot Tático das [04:39] (4 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 42 | awp | Jungle | `-1074,-1388,-166` | `-0°,126°` | 196.0 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 80 | m4a1 | Bomb B | `-2037,163,-160` | `67°,-14°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | BombObjective:NavigateNavMesh(CT_DefuseObjective) | Pending | None |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1663,-761,-168` | `-1°,177°` | 94.6 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | famas | Bomb B | `-2348,-24,-127` | `-1°,-134°` | 221.6 (Z -192 / 3D 293 aéreo) | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |

</details>

- **`[04:39]`** `[FIM_ROUND]` internal_round_id=2 | round_oficial=2 | Vencedor: CounterTerrorist | Motivo: `BombDefused` (7) — C4 desarmada pelos Contraterroristas | Placar: CT 1 x 1 TR | tick=15154
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Hotzone_PreMapped` em `(-1113, -1322, -108)` [Mira: Yaw 56° | CPU: `0.73ms`] -> Horizontes: **0ms:** `Diag-Dir(250u+Jump)` | **125ms:** `Diag-Dir(250u)` | **250ms:** `Diag-Dir(250u+Jump)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Hotzone_PreMapped` em `(-1637, -625, -168)` [Mira: Yaw -47° | CPU: `1.06ms`] -> Horizontes: **0ms:** `Diag-Dir(250u)` | **125ms:** `Diag-Dir(250u)` | **250ms:** `Diag-Dir(250u)`
- **`[04:39]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Hotzone_PreMapped` em `(-1249, -947, -168)` [Mira: Yaw 67° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Avanco(Shift)` | **250ms:** `Diag-Dir(Duck)`
## 🎮 Round 3 [Placar: CT 1 x 1 TR]
- **internal_round_id:** `3` | **display_round_number:** `3` | **round_in_half:** `3` | **match_phase:** `LIVE` | **round_phase:** `ROUND_ACTIVE` | **start_tick:** `15602`
- **Motor Micro-Movimento (16Hz):** `[Modo ONNX Ativo] ONNX-CPU-L3 (mlmove_de_mirage.onnx | 0.69ms)`

### 💵 Economia por Time (Pré-compra vs Pós-compra)
| Time | PreBuyIntent | FinalBuyState | Completion | Caixa Médio Antes | Caixa Médio Depois | Gasto | Equip Antes | Equip Depois | Primárias | Rifles | SMGs | AWPs | Coletes | Capacetes | Kits | Utilitárias ($) | LossBonus |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| CT | `SAVE_WITH_WEAPONS` | `FULL_BUY` | `STABILIZED` | $4270 | $1820 | $12250 | $11350 | $19400 | 5 | 5 | 0 | 0 | 5 | 0 | 0 | $3000 | $1400 |
| TR | `HALF_BUY` | `FULL_BUY` | `STABILIZED` | $3750 | $690 | $15300 | $6900 | $20500 | 5 | 4 | 0 | 1 | 5 | 0 | 0 | $1600 | $1900 |

### 💰 Loadout Pós-Compra
| Slot | Jogador | Time | Role | Dinheiro | Arma Primária | Arma Secundária | Utilitárias | Colete/Kit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark | TR | AWPer | $1900 | AWP | GLOCK | FLASHBANG, SMOKEGRENADE | Colete (100) |
| 2 | Ricksaw | CT | Rotator | $2350 | FAMAS | HKP2000 | FLASHBANG, MOLOTOV, SMOKEGRENADE, HEGRENADE | Colete (100) |
| 3 | Delrow | TR | EntryFragger | $100 | AK47 | GLOCK | SMOKEGRENADE | Colete (100) |
| 4 | Commando | CT | EntryFragger | $3750 | M4A1 | HKP2000 | SMOKEGRENADE, FLASHBANG | Colete (100) |
| 5 | Soldier | CT | Rotator | $0 | M4A1 | HKP2000 | Nenhuma | Colete (100) |
| 6 | Shamat | TR | Rotator | $1250 | GALILAR | GLOCK | FLASHBANG | Colete (100) + 💣 C4 (Bomba) |
| 7 | Rebel | TR | Anchor | $100 | AK47 | GLOCK | SMOKEGRENADE | Colete (100) |
| 8 | Syfers | CT | Anchor | $250 | FAMAS | HKP2000 | SMOKEGRENADE, FLASHBANG | Colete (100) |
| 9 | Buckshot | CT | Rotator | $2750 | FAMAS | HKP2000 | FLASHBANG, SMOKEGRENADE, HEGRENADE | Colete (100) |
| 10 | Steel | TR | Rotator | $100 | AK47 | GLOCK | SMOKEGRENADE | Colete (100) |

#### 🤖 Auditoria IGL CT
- **decision_id:** `R3_CT_CT_STANDARD_2_1_2_BALANCED_13d4e4` | **source:** `UTILITY_AI_ENGINE` | **latency:** `0ms` | **cache_hit:** `False` | **fallback:** `False` (NONE) | **parse:** `OK`
- **InitialTactic:** `Defesa 2-1-2 Padrão Equilibrada` | **CurrentTactic:** `Defesa 2-1-2 Padrão Equilibrada` | **TacticRevision:** `1` | **Ritmo:** `SLOW_DEFAULT` | **Tier:** `Tier1_Standard`
- **Candidatas:** CT_STANDARD_2_1_2_BALANCED (78.0); CT_2_1_2_HEAVY_ANCHOR_B (68.0); CT_2_1_2_HEAVY_PALACE_RAMP_A (68.0) | **penalidade_repetição:** `False`
- **Resumo:** 2 A (Ticket + Cabecinha), 1 Meio (Janela), 2 B (Van + Banco) com AuthorizedHold.

#### 🤖 Auditoria IGL TR
- **decision_id:** `R3_TR_TR_FAKE_A_EXEC_B_72cdaa` | **source:** `UTILITY_AI_ENGINE` | **latency:** `1ms` | **cache_hit:** `False` | **fallback:** `False` (NONE) | **parse:** `OK`
- **InitialTactic:** `Fake A & Execução Real Bomb B` | **CurrentTactic:** `Fake A & Execução Real Bomb B` | **TacticRevision:** `1` | **Ritmo:** `POKE_AND_ROTATE` | **Tier:** `Tier1_Standard`
- **Candidatas:** TR_SPLIT_A_MID_TO_CONNECTOR (72.0); TR_SPLIT_B_MID_TO_SHORT_CATWALK (72.0); TR_FAKE_A_EXEC_B (72.0) | **penalidade_repetição:** `False`
- **Resumo:** 2 jogadores sem C4 gastam utilitárias e fazem barulho na Rampa/Palácio A; Carrier + 2 executam o Bomb B.

### ⏱️ Linha do Tempo de Eventos
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Audio_HeardCue` em `(-113, -2078, -168)` [Mira: Yaw 74° | CPU: `0.73ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Syfers** acionou `Audio_HeardCue` em `(-406, -2240, -172)` [Mira: Yaw 41° | CPU: `0.73ms`] -> Horizontes: **0ms:** `Avanco(Shift)` | **125ms:** `Avanco(Shift)` | **250ms:** `Avanco(Shift)`
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Vision_Spotted` em `(-140, -1801, -168)` [Mira: Yaw 47° | CPU: `0.73ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Diag-Dir(250u)`
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Vision_Spotted` em `(255, -1564, -176)` [Mira: Yaw -160° | CPU: `0.65ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(Duck)`
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Audio_HeardCue` em `(587, -1485, -260)` [Mira: Yaw -159° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Diag-Dir(250u)` | **125ms:** `Strafe-Dir(250u)` | **250ms:** `Diag-Dir(250u)`
- **`[06:10]`** `[COMBATE]` **Buckshot** causou **21 HP** em **Shamat** com **famas** a **402u** (HP 100→79, raw=21, overkill=0, setor: Rampa A)
- **`[06:10]`** `[COMBATE]` **Shamat** causou **28 HP** em **Buckshot** com **galilar** a **402u** (HP 100→72, raw=28, overkill=0, setor: Bomb A)
- **`[06:10]`** `[MORTE]` **Shamat** eliminou **Buckshot** com **galilar** no setor **Bomb A**
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Vision_Spotted` em `(-301, 780, -123)` [Mira: Yaw -152° | CPU: `0.72ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Diag-Dir(250u)`

<details><summary><b>📊 Snapshot Tático das [06:10] (9 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | awp | Beco | `-377,705,-80` | `0°,-160°` | 200.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Avanco(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | famas | Mercado / Kitchen | `-1887,-643,-168` | `2°,-32°` | 208.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Rampa A | `250,-1556,-176` | `2°,-150°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Diag-Esq(Duck) | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | None |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1213,-1204,-168` | `2°,-43°` | 205.1 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | famas | Bomb A | `-69,-1769,-168` | `4°,72°` | 96.6 | PASSIVE_HOLD | ONNX_Vision_Spotted | Avanco(Shift) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act20) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 33 | galilar | Palácio A | `337,-1474,-176` | `2°,-142°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Avanco(Duck) | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_house)) | Pending | None |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Beco | `-232,785,-136` | `2°,-155°` | 215.0 | PASSIVE_HOLD | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | famas | Bomb A | `-348,-2014,-176` | `4°,44°` | 96.6 | PASSIVE_HOLD | ONNX_Audio_HeardCue | Avanco(Shift) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act18) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Beco | `331,117,-230` | `2°,-85°` | 208.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_palace_room)) | Pending | Movendo |

</details>

- **`[06:10]`** `[COMBATE]` **Delrow** causou **27 HP** em **Soldier** com **ak47** a **378u** (HP 100→73, raw=27, overkill=0, setor: Bomb A)
- **`[06:10]`** `[PIVOT TÁTICO TR - REJEITADO]` Declaração de `SITE CLEAR` em `Bomb A` por **Shamat** rejeitada: `OUTSIDE_PLANT_PERIMETER(pos=(337,-1474,-176),claimed=A,testedVolume=Bomb A_Prio1,dist=1427.7u,current_sector=Palácio A)` (`setor_atual=Palácio A`, `dwell=2.2s`, `inimigos_proximos=1`).
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Hotzone_PreMapped` em `(-292, 757, -113)` [Mira: Yaw -155° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Diag-Dir(250u)` | **250ms:** `Avanco(250u+Jump)`
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(-65, -1759, -168)` [Mira: Yaw 41° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck)` | **125ms:** `Parado (0u)` | **250ms:** `Strafe-Dir(Duck)`
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Syfers** acionou `Audio_HeardCue` em `(-339, -2008, -175)` [Mira: Yaw 42° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Vision_Spotted` em `(337, -1474, -176)` [Mira: Yaw -144° | CPU: `0.74ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[06:10]`** `[PIVOT TÁTICO TR]` First Kill conquistado por **Delrow** (`setor_killer=Rampa A`) sobre **Soldier** (`setor_vitima=Bomb A`) | C4: **Shamat** (`setor_c4=Palácio A`, `distA=1642u`, `distB=2791u`) | Vivos: `5v4` | Transição imediata `rev=2`: `Defesa 2-1-2 Padrão Equilibrada` -> `Exploit 5v4 -> Execução Bomb A (Pick em Bomb A)` (Alvo: **Bomb A**, `conf=0.88`).
- **`[06:10]`** `[MORTE]` **Delrow** eliminou **Soldier** com **ak47** no setor **Bomb A**
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Vision_Spotted` em `(250, -1556, -176)` [Mira: Yaw -148° | CPU: `0.71ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[06:10]`** `[COMBATE]` **Syfers** causou **24 HP** em **Delrow** com **famas** a **681u** (HP 100→76, raw=24, overkill=0, setor: Rampa A)
- **`[06:10]`** `[COMBATE]` **Shamat** causou **11 HP** em **Syfers** com **galilar** a **776u** (HP 100→89, raw=11, overkill=0, setor: Bomb A)
- **`[06:10]`** `[COMBATE]` **Delrow** causou **64 HP** em **Syfers** com **ak47** a **678u** (HP 89→25, raw=27, overkill=0, setor: Bomb A)
- **`[06:10]`** `[MORTE]` **Shamat** eliminou **Syfers** com **galilar** no setor **Bomb A**
- **`[06:10]`** `[PIVOT TÁTICO TR - REJEITADO]` Declaração de `SITE CLEAR` em `Bomb A` por **Delrow** rejeitada: `OUTSIDE_PLANT_PERIMETER(pos=(257,-1508,-120),claimed=A,testedVolume=Bomb A_Prio1,dist=1382.4u,current_sector=Palácio A)` (`setor_atual=Palácio A`, `dwell=2.2s`, `inimigos_proximos=0`).

<details><summary><b>📊 Snapshot Tático das [06:10] (7 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | awp | Beco | `-938,584,-80` | `0°,167°` | 200.0 | JIGGLE_INFO | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | famas | CT Spawn | `-1598,-992,-203` | `1°,-86°` | 220.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 1 | ak47 | Palácio A | `329,-1458,-168` | `4°,-139°` | 216.1 (Z -301 / 3D 371 aéreo) | PASSIVE_HOLD | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | Jungle | `-971,-1390,-167` | `2°,-5°` | 0.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | None |
| 6 | Shamat (Rotator) | TR | 33 | galilar | Rampa A | `461,-1531,-242` | `-1°,-147°` | 24.9 | PASSIVE_HOLD | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Beco | `-777,553,-82` | `1°,171°` | 215.0 | PASSIVE_HOLD | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Top Mid | `211,-479,-166` | `1°,-145°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_short_corner)) | Pending | Movendo |

</details>

- **`[06:10]`** `[PIVOT TÁTICO TR - REJEITADO]` Declaração de `SITE CLEAR` em `Bomb A` por **Shamat** rejeitada: `OUTSIDE_PLANT_PERIMETER(pos=(461,-1520,-192),claimed=A,testedVolume=Bomb A_Prio1,dist=1557.0u,current_sector=Rampa A)` (`setor_atual=Rampa A`, `dwell=2.2s`, `inimigos_proximos=0`).
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-159, -660, -233)` [Mira: Yaw -170° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`

<details><summary><b>📊 Snapshot Tático das [06:10] (7 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | awp | Apartamentos B | `-1423,715,-51` | `0°,179°` | 195.5 | JIGGLE_INFO | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | famas | CT Spawn | `-1567,-1642,-264` | `-0°,-82°` | 220.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 1 | ak47 | Palácio A | `586,-1558,-264` | `-0°,62°` | 195.5 | PASSIVE_HOLD | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | Bomb A | `-741,-1517,-168` | `-0°,-22°` | 225.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 33 | galilar | Rampa A | `461,-1520,-242` | `-0°,-161°` | 0.0 | PASSIVE_HOLD | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | None |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Apartamentos B | `-1311,708,-80` | `-0°,179°` | 215.0 | PASSIVE_HOLD | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Meio | `-193,-664,-240` | `-0°,-162°` | 0.0 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Strafe-Esq(Duck) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act38) | Pending | None |

</details>

- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-541, -1672, -173)` [Mira: Yaw 1° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Strafe-Esq(250u)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Strafe-Esq(250u)`
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Audio_HeardCue` em `(682, -1322, -264)` [Mira: Yaw 50° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Dir(250u)` | **125ms:** `Diag-Dir(250u)` | **250ms:** `Diag-Dir(250u)`
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Vision_Spotted` em `(461, -1521, -242)` [Mira: Yaw -163° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Dir(Duck)` | **125ms:** `Strafe-Esq(Duck)` | **250ms:** `Avanco(250u)`
- **`[06:10]`** `[COMBATE]` **Commando** causou **48 HP** em **Shamat** com **m4a1** a **1003u** (HP 79→31, raw=1, overkill=0, setor: Rampa A)
- **`[06:10]`** `[COMBATE]` **Shamat** causou **4 HP** em **Commando** com **galilar** a **1003u** (HP 100→96, raw=4, overkill=0, setor: Bomb A)

<details><summary><b>📊 Snapshot Tático das [06:10] (7 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | awp | Apartamentos B | `-1988,710,-48` | `0°,176°` | 192.4 | JIGGLE_INFO | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | famas | CT Spawn | `-1462,-2279,-242` | `-2°,-25°` | 220.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 1 | ak47 | Palácio A | `915,-1097,-264` | `-2°,45°` | 215.0 | PASSIVE_HOLD | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 74 | m4a1 | Bomb A | `-525,-1697,-175` | `6°,10°` | 0.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | None |
| 6 | Shamat (Rotator) | TR | 31 | galilar | Rampa A | `460,-1521,-242` | `-1°,-171°` | 0.0 | PASSIVE_HOLD | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | None |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Apartamentos B | `-1869,749,-48` | `-2°,-121°` | 198.9 | PASSIVE_HOLD | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Meio | `-537,-783,-257` | `-2°,-116°` | 209.2 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_short_corner)) | Pending | Movendo |

</details>

- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-549, -786, -259)` [Mira: Yaw -113° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Diag-Esq(250u)`
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-525, -1697, -175)` [Mira: Yaw 10° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck)` | **125ms:** `Strafe-Dir(Duck)` | **250ms:** `Strafe-Dir(Duck)`
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Vision_Spotted` em `(460, -1521, -242)` [Mira: Yaw -170° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-1023, -2349, -168)` [Mira: Yaw 12° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(250u)`
- **`[06:10]`** `[COMBATE]` **Steel** causou **96 HP** em **Commando** com **ak47** a **779u** (HP 96→0, raw=27, overkill=0, setor: Bomb A)
- **`[06:10]`** `[MORTE]` **Steel** eliminou **Commando** com **ak47** no setor **Bomb A**

<details><summary><b>📊 Snapshot Tático das [06:10] (6 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | awp | Van | `-2329,770,-126` | `0°,-131°` | 25.3 | JIGGLE_INFO | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | famas | CT Spawn | `-990,-2349,-168` | `-1°,26°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Strafe-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act38) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 1 | ak47 | Palácio A | `668,-1245,-261` | `-2°,-118°` | 215.0 | PASSIVE_HOLD | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 31 | galilar | Rampa A | `460,-1521,-242` | `-4°,-170°` | 0.0 | PASSIVE_HOLD | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | None |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Bomb B | `-2005,439,-160` | `-2°,-94°` | 183.8 | PASSIVE_HOLD | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Meio | `-691,-937,-216` | `0°,-78°` | 0.0 | PASSIVE_HOLD | Nenhuma | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act42) | Pending | None |

</details>

- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Audio_HeardCue` em `(-691, -937, -216)` [Mira: Yaw -78° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-816, -2328, -174)` [Mira: Yaw 22° | CPU: `0.76ms`] -> Horizontes: **0ms:** `Diag-Esq(Duck)` | **125ms:** `Diag-Esq(Duck)` | **250ms:** `Diag-Esq(Duck)`

<details><summary><b>📊 Snapshot Tático das [06:10] (6 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | awp | Bomb B | `-2389,555,-126` | `0°,-44°` | 96.1 | JIGGLE_INFO | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | famas | CT Spawn | `-809,-2331,-174` | `1°,74°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 1 | ak47 | Palácio A | `537,-1601,-264` | `-2°,-169°` | 200.9 | PASSIVE_HOLD | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 31 | galilar | Palácio A | `643,-1303,-258` | `-2°,35°` | 215.0 | PASSIVE_HOLD | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Bomb B | `-1895,-92,-167` | `-2°,-28°` | 215.0 | PASSIVE_HOLD | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Conector | `-628,-1205,-168` | `1°,-98°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |

</details>

- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Vision_Spotted` em `(-628, -1205, -168)` [Mira: Yaw -98° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck)` | **125ms:** `Strafe-Dir(Duck)` | **250ms:** `Parado (0u)`
- **`[06:10]`** `[COMBATE]` **Steel** causou **26 HP** em **Ricksaw** com **ak47** a **1141u** (HP 100→74, raw=26, overkill=0, setor: CT Spawn)
- **`[06:10]`** `[COMBATE]` **Ricksaw** causou **19 HP** em **Steel** com **famas** a **1141u** (HP 100→81, raw=19, overkill=0, setor: Conector)
- **`[06:10]`** `[MORTE]` **Steel** eliminou **Ricksaw** com **ak47** no setor **CT Spawn**
- **`[06:10]`** `[FIM_ROUND]` internal_round_id=3 | round_oficial=3 | Vencedor: Terrorist | Motivo: `TerroristsWin` (9) — Eliminação total dos Contraterroristas pelos Terroristas | Placar: CT 1 x 2 TR | tick=17533
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Audio_HeardCue` em `(-629, -1205, -168)` [Mira: Yaw -99° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Strafe-Esq(Duck)` | **125ms:** `Strafe-Esq(Duck)` | **250ms:** `Strafe-Dir(Shift)`
- **`[06:10]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-1215, -1219, -168)` [Mira: Yaw 129° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Strafe-Esq(250u)` | **250ms:** `Strafe-Esq(250u)`
## 🎮 Round 4 [Placar: CT 1 x 2 TR]
- **internal_round_id:** `4` | **display_round_number:** `4` | **round_in_half:** `4` | **match_phase:** `LIVE` | **round_phase:** `ROUND_ACTIVE` | **start_tick:** `17981`
- **Motor Micro-Movimento (16Hz):** `[Modo ONNX Ativo] ONNX-CPU-L3 (mlmove_de_mirage.onnx | 0.68ms)`

### 💵 Economia por Time (Pré-compra vs Pós-compra)
| Time | PreBuyIntent | FinalBuyState | Completion | Caixa Médio Antes | Caixa Médio Depois | Gasto | Equip Antes | Equip Depois | Primárias | Rifles | SMGs | AWPs | Coletes | Capacetes | Kits | Utilitárias ($) | LossBonus |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| CT | `HALF_BUY` | `FORCE_BUY` | `STABILIZED` | $3720 | $130 | $17950 | $1000 | $16900 | 5 | 3 | 2 | 0 | 5 | 0 | 0 | $2100 | $1900 |
| TR | `FULL_BUY` | `FULL_BUY` | `STABILIZED` | $4240 | $3360 | $4400 | $20350 | $21450 | 5 | 4 | 0 | 1 | 5 | 0 | 0 | $3200 | $1400 |

### 💰 Loadout Pós-Compra
| Slot | Jogador | Time | Role | Dinheiro | Arma Primária | Arma Secundária | Utilitárias | Colete/Kit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark | TR | AWPer | $3750 | AWP | GLOCK | FLASHBANG, SMOKEGRENADE, MOLOTOV | Colete (100) + 💣 C4 (Bomba) |
| 2 | Ricksaw | CT | Rotator | $300 | FAMAS | HKP2000 | SMOKEGRENADE, FLASHBANG | Colete (100) |
| 3 | Delrow | TR | EntryFragger | $3000 | FAMAS | GLOCK | SMOKEGRENADE, FLASHBANG | Colete (100) |
| 4 | Commando | CT | EntryFragger | $250 | M4A1 | HKP2000 | SMOKEGRENADE, FLASHBANG, INCGRENADE | Colete (100) |
| 5 | Soldier | CT | Rotator | $0 | MP9 | HKP2000 | Nenhuma | Colete (100) |
| 6 | Shamat | TR | Rotator | $3800 | GALILAR | GLOCK | FLASHBANG, SMOKEGRENADE, HEGRENADE | Colete (100) |
| 7 | Rebel | TR | Anchor | $3150 | AK47 | GLOCK | SMOKEGRENADE, FLASHBANG | Colete (100) |
| 8 | Syfers | CT | Anchor | $50 | MP9 | HKP2000 | FLASHBANG | Colete (100) |
| 9 | Buckshot | CT | Rotator | $50 | M4A1 | HKP2000 | SMOKEGRENADE | Colete (100) |
| 10 | Steel | TR | Rotator | $3100 | AK47 | GLOCK | SMOKEGRENADE, FLASHBANG | Colete (100) |

#### 🤖 Auditoria IGL CT
- **decision_id:** `R4_CT_CT_STANDARD_2_1_2_BALANCED_46f679` | **source:** `UTILITY_AI_ENGINE` | **latency:** `0ms` | **cache_hit:** `False` | **fallback:** `False` (NONE) | **parse:** `OK`
- **InitialTactic:** `Defesa 2-1-2 Padrão Equilibrada` | **CurrentTactic:** `Defesa 2-1-2 Padrão Equilibrada` | **TacticRevision:** `1` | **Ritmo:** `SLOW_DEFAULT` | **Tier:** `Tier1_Standard`
- **Candidatas:** CT_STANDARD_2_1_2_BALANCED (78.0); CT_2_1_2_HEAVY_ANCHOR_B (68.0); CT_2_1_2_HEAVY_PALACE_RAMP_A (68.0) | **penalidade_repetição:** `False`
- **Resumo:** 2 A (Ticket + Cabecinha), 1 Meio (Janela), 2 B (Van + Banco) com AuthorizedHold.

#### 🤖 Auditoria IGL TR
- **decision_id:** `R4_TR_TR_SPLIT_B_MID_TO_SHORT_CATWALK_c3452a` | **source:** `UTILITY_AI_ENGINE` | **latency:** `0ms` | **cache_hit:** `False` | **fallback:** `False` (NONE) | **parse:** `OK`
- **InitialTactic:** `Split B pelo Meio/Catwalk e Tapete` | **CurrentTactic:** `Split B pelo Meio/Catwalk e Tapete` | **TacticRevision:** `1` | **Ritmo:** `TIMED_EXECUTE` | **Tier:** `Tier1_Standard`
- **Candidatas:** TR_EXEC_A_PALACE_RAMP_SPLIT (68.0); TR_SPLIT_A_MID_TO_CONNECTOR (68.0); TR_SPLIT_B_MID_TO_SHORT_CATWALK (68.0) | **penalidade_repetição:** `False`
- **Resumo:** 2 jogadores dominam Meio/Underpass para subir L (Short B) enquanto 3 entram pelo Tapete B com a C4.

### ⏱️ Linha do Tempo de Eventos
- **`[06:47]`** `[MLMOVE - TRADE SPACING]` **Buckshot** (`yielding_slot=9`) cedeu espaço para **Soldier** (`priority_slot=5`) | `dist_before=138u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=15`.

<details><summary><b>📊 Snapshot Tático das [06:47] (10 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | awp | Palácio A | `577,-1557,-264` | `0°,-169°` | 167.7 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_house)) | Pending | Movendo |
| 2 | Ricksaw (Rotator) | CT | 100 | famas | Bomb A | `162,-1581,-173` | `-2°,-21°` | 120.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_mid_window_deep_awp)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | famas | Palácio A | `853,-2218,-40` | `-2°,-168°` | 219.7 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_top_mid_boxes)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1576,-1438,-264` | `-2°,88°` | 225.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | mp9 | CT Spawn | `-1352,-969,-168` | `-2°,19°` | 36.3 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_stairs_cross)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | galilar | Palácio A | `822,-1985,-40` | `-2°,-160°` | 156.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Apartamentos B | `125,816,-136` | `-2°,-175°` | 161.2 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | mp9 | CT Spawn | `-1366,-935,-168` | `-2°,-58°` | 15.5 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_bench_deep)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | m4a1 | CT Spawn | `-1209,-961,-168` | `-2°,49°` | 0.0 | PASSIVE_HOLD | Nenhuma | MicroMove:HoldStop(ONNX_Hotzone_PreMapped_StandStill) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Beco | `-312,779,-119` | `-2°,-150°` | 198.6 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Vision_Spotted` em `(577, -1557, -264)` [Mira: Yaw -169° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Recuo-Dir(Shift)` | **125ms:** `Strafe-Dir(250u)` | **250ms:** `Strafe-Dir(250u)`
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Vision_Spotted` em `(-312, 779, -119)` [Mira: Yaw -150° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Diag-Dir(250u+Jump)`
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(162, -1581, -173)` [Mira: Yaw -21° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Avanco(Shift)` | **125ms:** `Avanco(Duck)` | **250ms:** `Avanco(Shift)`
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Audio_HeardCue` em `(813, -1991, -40)` [Mira: Yaw -160° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[06:47]`** `[COMBATE]` **Shark** causou **85 HP** em **Ricksaw** com **awp** a **414u** (HP 100→15, raw=85, overkill=0, setor: Palácio A)
- **`[06:47]`** `[COMBATE]` **Ricksaw** causou **25 HP** em **Shark** com **famas** a **414u** (HP 100→75, raw=25, overkill=0, setor: Palácio A)
- **`[06:47]`** `[MORTE]` **Ricksaw** eliminou **Shark** com **famas** no setor **Palácio A**
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Hotzone_PreMapped` em `(-1263, -1110, -168)` [Mira: Yaw -48° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`

<details><summary><b>📊 Snapshot Tático das [06:47] (9 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2 | Ricksaw (Rotator) | CT | 15 | famas | Palácio A | `222,-1572,-176` | `-2°,-137°` | 217.1 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | famas | Palácio A | `257,-2296,-40` | `-2°,-153°` | 155.8 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_top_mid_boxes)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1488,-1098,-191` | `-2°,36°` | 122.4 (Z 186 / 3D 223 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | mp9 | CT Spawn | `-1242,-1145,-168` | `-2°,-44°` | 0.0 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Diag-Esq(Shift) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act30) | Pending | None |
| 6 | Shamat (Rotator) | TR | 100 | galilar | Palácio A | `882,-1993,-72` | `-2°,-158°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Apartamentos B | `282,791,-136` | `-2°,-19°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | mp9 | CT Spawn | `-1362,-963,-168` | `-2°,-28°` | 81.6 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_bench_deep)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | m4a1 | CT Spawn | `-1194,-1028,-168` | `-2°,-73°` | 0.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:HoldStop(SpotHold_PASSIVE_HOLD) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Beco | `-284,722,-98` | `-2°,9°` | 0.0 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Avanco(Duck) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act33) | Pending | None |

</details>

- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-284, 722, -98)` [Mira: Yaw 9° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Strafe-Esq(Shift)` | **125ms:** `Parado (0u)` | **250ms:** `Strafe-Esq(Shift)`
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-22, -1610, -168)` [Mira: Yaw -86° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Vision_Spotted` em `(53, -2013, -40)` [Mira: Yaw 103° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Audio_HeardCue` em `(438, -2280, -40)` [Mira: Yaw -126° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Avanco(250u)`

<details><summary><b>📊 Snapshot Tático das [06:47] (9 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2 | Ricksaw (Rotator) | CT | 15 | famas | Bomb A | `-22,-1610,-168` | `-16°,-81°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 100 | famas | Palácio A | `55,-1995,-40` | `21°,101°` | 0.0 | PASSIVE_HOLD | Nenhuma | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act21) | Pending | None |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1367,-998,-168` | `-1°,31°` | 40.3 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | mp9 | CT Spawn | `-1303,-999,-168` | `-1°,-54°` | 116.9 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_stairs_cross)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | galilar | Palácio A | `415,-2291,-40` | `11°,-151°` | 73.2 | PASSIVE_HOLD | Nenhuma | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act26) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Apartamentos B | `637,643,-136` | `-1°,-24°` | 212.2 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | mp9 | CT Spawn | `-1312,-936,-168` | `-1°,41°` | 0.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_bench_deep)) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | m4a1 | CT Spawn | `-1194,-1028,-168` | `-1°,-74°` | 0.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:HoldStop(SpotHold_PASSIVE_HOLD) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Beco | `-273,747,-113` | `-1°,5°` | 201.2 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[06:47]`** `[COMBATE]` **Ricksaw** causou **14 HP** em **Delrow** com **famas** a **414u** (HP 100→86, raw=14, overkill=0, setor: Palácio A)
- **`[06:47]`** `[COMBATE]` **Delrow** causou **15 HP** em **Ricksaw** com **famas** a **414u** (HP 15→0, raw=62, overkill=47, setor: Bomb A)
- **`[06:47]`** `[MORTE]` **Delrow** eliminou **Ricksaw** com **famas** (HEADSHOT 💥) no setor **Bomb A**
- **`[06:47]`** `[MLMOVE - TRADE SPACING]` **Syfers** (`yielding_slot=8`) cedeu espaço para **Buckshot** (`priority_slot=9`) | `dist_before=91u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=8`.
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Hotzone_PreMapped` em `(-1194, -1028, -168)` [Mira: Yaw 126° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[06:47]`** `[PIVOT TÁTICO TR - REJEITADO]` Declaração de `SITE CLEAR` em `Bomb A` por **Delrow** rejeitada: `OUTSIDE_PLANT_PERIMETER(pos=(35,-1823,-6),claimed=A,testedVolume=Bomb A_Prio1,dist=1446.0u,current_sector=Palácio A)` (`setor_atual=Palácio A`, `dwell=2.2s`, `inimigos_proximos=0`).

<details><summary><b>📊 Snapshot Tático das [06:47] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 3 | Delrow (EntryFragger) | TR | 86 | famas | Palácio A | `50,-1628,-70` | `-0°,41°` | 312.8 (Z -389 / 3D 499 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1281,-1030,-168` | `-0°,-61°` | 211.9 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | mp9 | Janela | `-1092,-640,-135` | `-2°,4°` | 71.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_stairs_cross)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | galilar | Palácio A | `94,-2292,-40` | `-0°,106°` | 208.3 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | TR Spawn | `1200,406,-262` | `-0°,-72°` | 200.8 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | mp9 | CT Spawn | `-1211,-931,-168` | `-1°,-81°` | 0.0 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Recuo(Duck) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act37) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | m4a1 | CT Spawn | `-1194,-1028,-168` | `-6°,-85°` | 0.0 | PASSIVE_HOLD | TradeSpacing_Repulsion | Diag-Dir(250u) | TradeSpacing:UsercmdVector(TradeSpacing_Repulsion_Act15) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Apartamentos B | `266,778,-136` | `-0°,-17°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Hotzone_PreMapped` em `(-1268, -1054, -168)` [Mira: Yaw -60° | CPU: `0.71ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(Duck+Jump)`
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Hotzone_PreMapped` em `(-1056, -676, -131)` [Mira: Yaw -50° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Avanco(250u+Jump)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(250u+Jump)`

<details><summary><b>📊 Snapshot Tático das [06:47] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 3 | Delrow (EntryFragger) | TR | 86 | famas | Rampa A | `447,-1583,-235` | `1°,38°` | 117.2 | PASSIVE_HOLD | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | CT Spawn | `-1202,-1176,-168` | `1°,-61°` | 212.5 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | mp9 | Meio | `-1022,-755,-212` | `1°,2°` | 208.3 (Z 89 / 3D 227 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | galilar | Palácio A | `40,-1810,-40` | `1°,62°` | 166.3 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | TR Spawn | `1263,-165,-168` | `1°,-88°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | mp9 | CT Spawn | `-1180,-873,-168` | `-3°,-150°` | 9.9 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | m4a1 | CT Spawn | `-1123,-1082,-115` | `-4°,81°` | 201.1 (Z -139 / 3D 244 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_short_corner)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Beco | `601,561,-125` | `1°,-24°` | 208.1 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Syfers** acionou `Hotzone_PreMapped` em `(-1154, -700, -104)` [Mira: Yaw 23° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Strafe-Dir(250u)` | **125ms:** `Strafe-Dir(250u+Jump)` | **250ms:** `Recuo-Dir(250u+Jump)`

<details><summary><b>📊 Snapshot Tático das [06:47] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 3 | Delrow (EntryFragger) | TR | 86 | famas | Bomb A | `-67,-1677,-168` | `2°,-153°` | 220.0 | PASSIVE_HOLD | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | m4a1 | Jungle | `-785,-1573,-168` | `2°,-40°` | 225.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | mp9 | Meio | `-609,-743,-262` | `1°,-3°` | 240.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | galilar | Bomb A | `-145,-1732,-168` | `2°,-179°` | 205.1 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | TR Spawn | `1185,-770,-183` | `2°,-123°` | 215.1 (Z -276 / 3D 350 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | mp9 | Janela | `-1248,-705,-168` | `-14°,100°` | 0.0 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Parado (0u) | MicroMove:HoldStop(ONNX_Hotzone_PreMapped_StandStill) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | m4a1 | Jungle | `-1049,-1438,-166` | `2°,-20°` | 225.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_b_short_corner)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | TR Spawn | `1115,440,-262` | `2°,-58°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Audio_HeardCue` em `(-79, -1684, -168)` [Mira: Yaw -153° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[06:47]`** `[MLMOVE - TRADE SPACING]` **Shamat** (`yielding_slot=6`) cedeu espaço para **Delrow** (`priority_slot=3`) | `dist_before=93u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=12`.
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-752, -1599, -168)` [Mira: Yaw -40° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Diag-Dir(250u)` | **250ms:** `Diag-Dir(250u+Jump)`
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Audio_HeardCue` em `(-1009, -1452, -166)` [Mira: Yaw -21° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[06:47]`** `[COMBATE]` **Shamat** causou **28 HP** em **Commando** com **galilar** a **559u** (HP 100→72, raw=28, overkill=0, setor: Bomb A)
- **`[06:47]`** `[COMBATE]` **Commando** causou **31 HP** em **Shamat** com **m4a1** a **558u** (HP 100→69, raw=31, overkill=0, setor: Bomb A)
- **`[06:47]`** `[PIVOT TÁTICO TR]` First Kill conquistado por **Shamat** (`setor_killer=Bomb A`) sobre **Commando** (`setor_vitima=Bomb A`) | C4: **Delrow** (`setor_c4=Bomb A`, `distA=1083u`, `distB=2696u`) | Vivos: `4v4` | Transição imediata `rev=2`: `Defesa 2-1-2 Padrão Equilibrada` -> `Exploit 5v4 -> Execução Bomb A (Pick em Bomb A)` (Alvo: **Bomb A**, `conf=0.88`).
- **`[06:47]`** `[MORTE]` **Shamat** eliminou **Commando** com **galilar** no setor **Bomb A**
- **`[06:47]`** `[COMBATE]` **Buckshot** causou **30 HP** em **Delrow** com **m4a1** a **901u** (HP 86→56, raw=29, overkill=0, setor: Bomb A)
- **`[06:47]`** `[MORTE]` **Buckshot** eliminou **Delrow** com **m4a1_silencer** no setor **Bomb A**

<details><summary><b>📊 Snapshot Tático das [06:47] (6 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 5 | Soldier (Rotator) | CT | 100 | mp9 | Top Mid | `78,-604,-176` | `1°,23°` | 240.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 69 | galilar | Bomb A | `-394,-1666,-168` | `9°,173°` | 179.4 | PASSIVE_HOLD | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Palácio A | `862,-1113,-263` | `2°,-134°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | mp9 | Janela | `-1130,-751,-123` | `2°,-3°` | 93.8 (Z -83 / 3D 125 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | m4a1 | Jungle | `-1128,-1316,-168` | `2°,45°` | 216.6 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | TR Spawn | `1251,-71,-168` | `2°,-87°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[06:47]`** `[PIVOT TÁTICO TR - REJEITADO]` Declaração de `SITE CLEAR` em `Bomb A` por **Shamat** rejeitada: `RECENT_DAMAGE(2.22s<3.00s)` (`setor_atual=Bomb A`, `dwell=2.2s`, `inimigos_proximos=0`).
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Syfers** acionou `Hotzone_PreMapped` em `(-1126, -785, -131)` [Mira: Yaw 4° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Diag-Esq(Shift+Jump)` | **125ms:** `Diag-Esq(Shift+Jump)` | **250ms:** `Diag-Esq(Shift+Jump)`

<details><summary><b>📊 Snapshot Tático das [06:47] (6 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 5 | Soldier (Rotator) | CT | 100 | mp9 | Top Mid | `438,-67,-160` | `1°,110°` | 149.7 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 69 | c4 | Bomb A | `-491,-2053,-180` | `1°,-96°` | 0.0 | PASSIVE_HOLD | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Palácio A | `603,-1502,-264` | `1°,-106°` | 111.8 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | mp9 | Janela | `-1121,-677,-168` | `1°,-1°` | 45.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | m4a1 | Jungle | `-1167,-1308,-169` | `1°,92°` | 0.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:HoldStop(SpotHold_PASSIVE_HOLD) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | TR Spawn | `1235,-703,-180` | `1°,-114°` | 225.0 (Z -200 / 3D 301 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Syfers** acionou `Hotzone_PreMapped` em `(-1065, -673, -126)` [Mira: Yaw -5° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u+Jump)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Recuo(Duck)`

<details><summary><b>📊 Snapshot Tático das [06:47] (6 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 5 | Soldier (Rotator) | CT | 100 | mp9 | Beco | `410,466,-264` | `-0°,11°` | 240.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_ticket_passive)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 69 | c4 | Bomb A | `-491,-2053,-180` | `-0°,-98°` | 0.0 | PASSIVE_HOLD | Nenhuma | BombObjective:ReleaseHoldAndRepath(C4Carrier_InBombZone_AuthorizedToPlant) | Pending | None |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Palácio A | `800,-1130,-260` | `-0°,29°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | mp9 | Meio | `-819,-679,-266` | `-0°,1°` | 7.3 | PASSIVE_HOLD | Nenhuma | MicroMove:HoldStop(ONNX_Hotzone_PreMapped_StandStill) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | m4a1 | Jungle | `-1167,-1308,-169` | `-0°,90°` | 0.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:HoldStop(SpotHold_PASSIVE_HOLD) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Palácio A | `921,-1110,-264` | `-0°,-140°` | 213.3 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[06:47]`** `[BOMBA]` C4 plantada no bombsite!
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Syfers** acionou `Hotzone_PreMapped` em `(-621, -1073, -195)` [Mira: Yaw -86° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`

<details><summary><b>📊 Snapshot Tático das [06:47] (6 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 5 | Soldier (Rotator) | CT | 100 | mp9 | Beco | `254,57,-213` | `-2°,-103°` | 235.9 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 69 | galilar | Bomb A | `-191,-2232,-168` | `-2°,-49°` | 193.4 | AGGRESSIVE_POKE | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Palácio A | `704,-1044,-248` | `-1°,98°` | 73.1 | AGGRESSIVE_POKE | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_b_apartments_kitchen)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | mp9 | Conector | `-616,-1103,-181` | `-2°,-86°` | 240.0 | AGGRESSIVE_POKE | ONNX_Hotzone_PreMapped | Avanco(250u) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | m4a1 | Bomb A | `-756,-1575,-168` | `-2°,-56°` | 188.9 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Palácio A | `649,-1273,-259` | `-2°,-117°` | 49.8 | AGGRESSIVE_POKE | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |

</details>

- **`[06:47]`** `[DEFUSE]` Jogador Buckshot iniciou desarme da C4!

<details><summary><b>📊 Snapshot Tático das [06:47] (6 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 5 | Soldier (Rotator) | CT | 100 | mp9 | Top Mid | `69,-612,-178` | `-2°,-144°` | 240.0 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 69 | galilar | Bomb A | `-243,-2393,-164` | `-2°,80°` | 153.0 | AGGRESSIVE_POKE | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Palácio A | `704,-1038,-247` | `-2°,-84°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | TacticalNavigation:HoldStop(TimedHold(3.6s)) | Pending | None |
| 8 | Syfers (Anchor) | CT | 100 | mp9 | Bomb A | `-546,-1744,-180` | `-2°,-76°` | 239.8 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | m4a1 | Bomb A | `-476,-1993,-180` | `-0°,-103°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | BombObjective:NavigateNavMesh(CT_DefuseObjective) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Rampa A | `527,-1587,-264` | `-2°,-169°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | TacticalNavigation:HoldStop(TimedHold(3.6s)) | Pending | None |

</details>

- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Vision_Spotted` em `(-205, -2034, -105)` [Mira: Yaw 168° | CPU: `0.65ms`] -> Horizontes: **0ms:** `Diag-Esq(250u+Jump)` | **125ms:** `Diag-Esq(250u+Jump)` | **250ms:** `Avanco(250u+Jump)`
- **`[06:47]`** `[COMBATE]` **Shamat** causou **22 HP** em **Buckshot** com **galilar** a **265u** (HP 100→78, raw=22, overkill=0, setor: Bomb A)
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Syfers** acionou `Vision_Spotted` em `(-474, -1950, -180)` [Mira: Yaw -79° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Strafe-Esq(250u)` | **125ms:** `Parado (0u)` | **250ms:** `Strafe-Esq(250u)`
- **`[06:47]`** `[MLMOVE - TRADE SPACING]` **Buckshot** (`yielding_slot=9`) cedeu espaço para **Syfers** (`priority_slot=8`) | `dist_before=43u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=11`.

<details><summary><b>📊 Snapshot Tático das [06:47] (6 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 5 | Soldier (Rotator) | CT | 100 | mp9 | Meio | `-521,-744,-258` | `-2°,-116°` | 240.0 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 69 | galilar | Bomb A | `-250,-1970,-168` | `9°,169°` | 41.1 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Diag-Esq(250u+Jump) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act55) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Palácio A | `704,-1038,-247` | `-2°,-88°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | TacticalNavigation:HoldStop(TimedHold(0.6s)) | Pending | None |
| 8 | Syfers (Anchor) | CT | 100 | mp9 | Bomb A | `-474,-1950,-180` | `2°,-39°` | 0.0 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Recuo-Dir(Duck+Jump) | BombObjective:NavigateNavMesh(CT_DefuseObjective) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 49 | m4a1 | Bomb A | `-476,-1996,-180` | `1°,-73°` | 11.3 | AGGRESSIVE_POKE | ONNX_Audio_HeardCue | Parado (0u) | BombObjective:NavigateNavMesh(CT_DefuseObjective) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Rampa A | `527,-1587,-264` | `-2°,-174°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | TacticalNavigation:HoldStop(TimedHold(0.6s)) | Pending | None |

</details>

- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Hotzone_PreMapped` em `(-564, -755, -261)` [Mira: Yaw -109° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Diag-Esq(250u)`
- **`[06:47]`** `[COMBATE]` **Shamat** causou **28 HP** em **Syfers** com **galilar** a **224u** (HP 100→72, raw=28, overkill=0, setor: Bomb A)
- **`[06:47]`** `[MORTE]` **Shamat** eliminou **Syfers** com **galilar** no setor **Bomb A**
- **`[06:47]`** `[COMBATE]` **Buckshot** causou **32 HP** em **Shamat** com **m4a1** a **227u** (HP 69→37, raw=32, overkill=0, setor: Bomb A)
- **`[06:47]`** `[MORTE]` **Buckshot** eliminou **Shamat** com **m4a1_silencer** no setor **Bomb A**
- **`[06:47]`** `[DEFUSE]` Jogador Buckshot iniciou desarme da C4!
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Vision_Spotted` em `(192, -1575, -174)` [Mira: Yaw -143° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Audio_HeardCue` em `(705, -1310, -262)` [Mira: Yaw -111° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Avanco(Duck)` | **125ms:** `Avanco(Duck)` | **250ms:** `Parado (0u)`
- **`[06:47]`** `[COMBATE]` **Steel** causou **56 HP** em **Buckshot** com **ak47** a **783u** (HP 78→22, raw=27, overkill=0, setor: Bomb A)
- **`[06:47]`** `[MORTE]` **Steel** eliminou **Buckshot** com **ak47** no setor **Bomb A**

<details><summary><b>📊 Snapshot Tático das [06:47] (4 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 5 | Soldier (Rotator) | CT | 100 | mp9 | Conector | `-648,-1019,-216` | `-1°,64°` | 215.3 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Palácio A | `705,-1310,-262` | `-0°,-123°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | TacticalNavigation:HoldStop(TimedHold(3.1s)) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 0 | none | Bomb A | `-482,-2012,-180` | `37°,-103°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | BombObjective:NavigateNavMesh(CT_DefuseObjective) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Palácio A | `169,-1576,-174` | `4°,-146°` | 0.0 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Diag-Esq(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act40) | Pending | None |

</details>

- **`[06:47]`** `[PIVOT TÁTICO TR]` Lurker (**Steel**, setor=`Bomb A`, `in_plant_zone=True`, `dwell=2.2s`, `conf=0.77`) confirmou **Bomb A limpo** | `rev=3` | `initial=Defesa 2-1-2 Padrão Equilibrada` -> `current=Convergência C4 -> Bomb A Limpo por Steel`.

<details><summary><b>📊 Snapshot Tático das [06:47] (3 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 5 | Soldier (Rotator) | CT | 100 | mp9 | Conector | `-647,-986,-216` | `-1°,-35°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Palácio A | `717,-1452,-264` | `1°,-144°` | 215.0 | AGGRESSIVE_POKE | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Bomb A | `-75,-1812,-168` | `1°,-44°` | 210.3 | AGGRESSIVE_POKE | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |

</details>


<details><summary><b>📊 Snapshot Tático das [06:47] (3 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 5 | Soldier (Rotator) | CT | 100 | mp9 | Conector | `-633,-1272,-168` | `2°,-81°` | 182.3 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Rampa A | `306,-1530,-176` | `2°,-151°` | 207.6 | AGGRESSIVE_POKE | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Bomb A | `152,-1914,-168` | `0°,50°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | None |

</details>

- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Vision_Spotted` em `(-7, -1659, -168)` [Mira: Yaw -113° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Avanco(Shift)` | **125ms:** `Parado (0u)` | **250ms:** `Diag-Esq(250u)`
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Audio_HeardCue` em `(152, -1914, -131)` [Mira: Yaw 48° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Avanco(Duck+Jump)` | **125ms:** `Avanco(Duck+Jump)` | **250ms:** `Recuo(Duck)`
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(-583, -1685, -174)` [Mira: Yaw -73° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[06:47]`** `[COMBATE]` **Rebel** causou **27 HP** em **Soldier** com **ak47** a **613u** (HP 100→73, raw=27, overkill=0, setor: Bomb A)

<details><summary><b>📊 Snapshot Tático das [06:47] (3 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 5 | Soldier (Rotator) | CT | 73 | mp9 | Bomb A | `-609,-1852,-180` | `3°,15°` | 0.0 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Strafe-Esq(Shift+Jump) | EmergencyFallback:NavigateNavMesh(TransitTo(Target)) | Pending | None |
| 7 | Rebel (Anchor) | TR | 100 | ak47 | Bomb A | `-20,-1675,-168` | `3°,-164°` | 0.0 | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Recuo-Esq(Shift) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act19) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Bomb A | `151,-1936,-132` | `6°,-116°` | 35.5 (Z -83 / 3D 90 aéreo) | AGGRESSIVE_POKE | TradeSpacing_WideSwing | Diag-Esq(250u) | TradeSpacing:UsercmdVector(TradeSpacing_WideSwing_Act9) | Pending | Movendo |

</details>

- **`[06:47]`** `[COMBATE]` **Soldier** causou **13 HP** em **Rebel** com **mp9** a **615u** (HP 100→87, raw=13, overkill=0, setor: Bomb A)
- **`[06:47]`** `[COMBATE]` **Steel** causou **34 HP** em **Soldier** com **ak47** a **752u** (HP 73→39, raw=33, overkill=0, setor: Bomb A)
- **`[06:47]`** `[MORTE]` **Steel** eliminou **Soldier** com **ak47** no setor **Bomb A**
- **`[06:47]`** `[FIM_ROUND]` internal_round_id=4 | round_oficial=4 | Vencedor: Terrorist | Motivo: `TerroristsWin` (9) — Eliminação total dos Contraterroristas pelos Terroristas | Placar: CT 1 x 3 TR | tick=21856
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Vision_Spotted` em `(-20, -1674, -168)` [Mira: Yaw -170° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Vision_Spotted` em `(111, -1938, -155)` [Mira: Yaw 169° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Avanco(Duck+Jump)` | **125ms:** `Avanco(Duck+Jump)` | **250ms:** `Avanco(Duck+Jump)`
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(-623, -1808, -180)` [Mira: Yaw 10° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[06:47]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Hotzone_PreMapped` em `(-1242, -947, -168)` [Mira: Yaw 52° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Avanco(250u)`
## 🎮 Round 5 [Placar: CT 1 x 3 TR]
- **internal_round_id:** `5` | **display_round_number:** `5` | **round_in_half:** `5` | **match_phase:** `LIVE` | **round_phase:** `ROUND_ACTIVE` | **start_tick:** `22305`
- **Motor Micro-Movimento (16Hz):** `[Modo ONNX Ativo] ONNX-CPU-L3 (mlmove_de_mirage.onnx | 0.67ms)`

### 💵 Economia por Time (Pré-compra vs Pós-compra)
| Time | PreBuyIntent | FinalBuyState | Completion | Caixa Médio Antes | Caixa Médio Depois | Gasto | Equip Antes | Equip Depois | Primárias | Rifles | SMGs | AWPs | Coletes | Capacetes | Kits | Utilitárias ($) | LossBonus |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| CT | `FULL_ECO` | `FULL_ECO` | `STABILIZED` | $2860 | $2860 | $0 | $1000 | $1000 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | $0 | $2400 |
| TR | `FULL_BUY` | `FULL_BUY` | `STABILIZED` | $6970 | $3280 | $18450 | $8050 | $23450 | 5 | 4 | 0 | 1 | 5 | 0 | 0 | $4300 | $1400 |

### 💰 Loadout Pós-Compra
| Slot | Jogador | Time | Role | Dinheiro | Arma Primária | Arma Secundária | Utilitárias | Colete/Kit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark | TR | AWPer | $350 | AWP | GLOCK | SMOKEGRENADE, FLASHBANG, MOLOTOV | Colete (100) |
| 2 | Ricksaw | CT | AWPer | $3150 | Nenhuma | HKP2000 | Nenhuma | Sem Colete |
| 3 | Delrow | TR | EntryFragger | $1950 | AK47 | GLOCK | SMOKEGRENADE, FLASHBANG, MOLOTOV | Colete (100) |
| 4 | Commando | CT | EntryFragger | $2800 | Nenhuma | HKP2000 | Nenhuma | Sem Colete |
| 5 | Soldier | CT | Rotator | $2550 | Nenhuma | HKP2000 | Nenhuma | Sem Colete |
| 6 | Shamat | TR | Rotator | $3450 | AK47 | GLOCK | SMOKEGRENADE, FLASHBANG, HEGRENADE | Colete (100) |
| 7 | Rebel | TR | Anchor | $5000 | FAMAS | GLOCK | SMOKEGRENADE, FLASHBANG, MOLOTOV | Colete (100) |
| 8 | Syfers | CT | Anchor | $2600 | Nenhuma | HKP2000 | Nenhuma | Sem Colete |
| 9 | Buckshot | CT | Rotator | $3200 | Nenhuma | HKP2000 | Nenhuma | Sem Colete |
| 10 | Steel | TR | Rotator | $5650 | AK47 | GLOCK | SMOKEGRENADE, FLASHBANG, HEGRENADE | Colete (100) + 💣 C4 (Bomba) |

#### 🤖 Auditoria IGL CT
- **decision_id:** `R5_CT_CT_ECO_STACK_GAMBLE_B_326f45` | **source:** `UTILITY_AI_ENGINE` | **latency:** `0ms` | **cache_hit:** `False` | **fallback:** `False` (NONE) | **parse:** `OK`
- **InitialTactic:** `Gamble Eco Stack B (Emboscada Tapete)` | **CurrentTactic:** `Gamble Eco Stack B (Emboscada Tapete)` | **TacticRevision:** `1` | **Ritmo:** `FAST_CONTACT` | **Tier:** `Tier1_Standard`
- **Candidatas:** CT_ECO_STACK_GAMBLE_B (100.0); CT_ECO_STACK_GAMBLE_A (90.0); CT_2_1_2_HEAVY_ANCHOR_B (75.0) | **penalidade_repetição:** `False`
- **Resumo:** Formação de Eco/Pistola com 3 defensores em ângulos curtos no Bomb B + 1 Underpass.

#### 🤖 Auditoria IGL TR
- **decision_id:** `R5_TR_TR_SPLIT_A_MID_TO_CONNECTOR_10762d` | **source:** `UTILITY_AI_ENGINE` | **latency:** `0ms` | **cache_hit:** `False` | **fallback:** `False` (NONE) | **parse:** `OK`
- **InitialTactic:** `Split A pelo Meio e Conector` | **CurrentTactic:** `Split A pelo Meio e Conector` | **TacticRevision:** `1` | **Ritmo:** `TIMED_EXECUTE` | **Tier:** `Tier1_Standard`
- **Candidatas:** TR_SLOW_DEFAULT_MAP_CONTROL (93.0); TR_EXEC_A_PALACE_RAMP_SPLIT (93.0); TR_SPLIT_A_MID_TO_CONNECTOR (93.0) | **penalidade_repetição:** `False`
- **Resumo:** Domínio do Meio (Top Mid + Underpass) invadindo Conector/Jungle em pinça com Rampa A.

### ⏱️ Linha do Tempo de Eventos
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Hotzone_PreMapped` em `(75, -322, -183)` [Mira: Yaw -163° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[07:55]`** `[MLMOVE - TRADE SPACING]` **Syfers** (`yielding_slot=8`) cedeu espaço para **Ricksaw** (`priority_slot=2`) | `dist_before=45u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=11`.
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Vision_Spotted` em `(168, -436, -167)` [Mira: Yaw -169° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck)` | **125ms:** `Strafe-Dir(Duck)` | **250ms:** `Diag-Esq(Duck)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Audio_HeardCue` em `(294, -200, -168)` [Mira: Yaw -126° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Ricksaw** acionou `Vision_Spotted` em `(-1130, -693, -122)` [Mira: Yaw 23° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Dir(250u+Jump)` | **125ms:** `Diag-Dir(250u)` | **250ms:** `Diag-Dir(250u+Jump)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Audio_HeardCue` em `(-1276, -949, -168)` [Mira: Yaw 53° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Audio_HeardCue` em `(-1454, -893, -168)` [Mira: Yaw 11° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Recuo-Esq(Shift)` | **125ms:** `Strafe-Esq(250u)` | **250ms:** `Strafe-Esq(250u)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Vision_Spotted` em `(-293, 738, -104)` [Mira: Yaw -158° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u+Jump)`

<details><summary><b>📊 Snapshot Tático das [07:55] (10 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 100 | awp | Catwalk / Short | `-74,-360,-154` | `0°,-165°` | 205.5 (Z -236 / 3D 313 aéreo) | PASSIVE_HOLD | ONNX_Vision_Spotted | Avanco(250u+Jump) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act58) | Pending | Movendo |
| 2 | Ricksaw (AWPer) | CT | 100 | hkp2000 | Janela | `-1130,-630,-140` | `1°,17°` | 203.3 (Z -183 / 3D 273 aéreo) | PASSIVE_HOLD | ONNX_Vision_Spotted | Strafe-Dir(250u+Jump) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act53) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Palácio A | `550,-2014,-40` | `1°,167°` | 209.5 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | CT Spawn | `-1276,-949,-168` | `1°,52°` | 0.0 | PASSIVE_HOLD | ONNX_Audio_HeardCue | Avanco(Shift) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act19) | Pending | None |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1457,-913,-168` | `1°,24°` | 0.0 | JIGGLE_INFO | ONNX_Audio_HeardCue | Recuo-Esq(Duck) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act44) | Pending | None |
| 6 | Shamat (Rotator) | TR | 100 | ak47 | Top Mid | `168,-438,-167` | `-0°,-170°` | 0.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 7 | Rebel (Anchor) | TR | 100 | famas | Top Mid | `276,-232,-167` | `1°,-130°` | 8.1 | PASSIVE_HOLD | ONNX_Audio_HeardCue | Avanco(Duck) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act44) | Pending | None |
| 8 | Syfers (Anchor) | CT | 100 | hkp2000 | CT Spawn | `-1244,-953,-168` | `4°,63°` | 0.0 | PASSIVE_HOLD | ONNX_Audio_HeardCue | Parado (0u) | MicroMove:HoldStop(ONNX_Audio_HeardCue_StandStill) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | hkp2000 | Bomb A | `-224,-1823,-168` | `0°,144°` | 240.0 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Beco | `-306,733,-98` | `1°,-159°` | 215.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Avanco(250u) | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |

</details>

- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Vision_Spotted` em `(497, -2011, -40)` [Mira: Yaw 162° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Vision_Spotted` em `(-273, -1788, -168)` [Mira: Yaw 145° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[07:55]`** `[COMBATE]` **Shamat** causou **33 HP** em **Ricksaw** com **ak47** a **1308u** (HP 100→67, raw=33, overkill=0, setor: Janela)
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Vision_Spotted` em `(-78, -390, -166)` [Mira: Yaw -169° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[07:55]`** `[MLMOVE - TRADE SPACING]` **Syfers** (`yielding_slot=8`) cedeu espaço para **Commando** (`priority_slot=4`) | `dist_before=84u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=4`.
- **`[07:55]`** `[COMBATE]` **Ricksaw** causou **18 HP** em **Shark** com **hkp2000** a **1073u** (HP 100→82, raw=18, overkill=0, setor: Catwalk / Short)
- **`[07:55]`** `[COMBATE]` **Ricksaw** causou **7 HP** em **Rebel** com **hkp2000** a **1334u** (HP 100→93, raw=7, overkill=0, setor: Top Mid)
- **`[07:55]`** `[MORTE]` **Shamat** eliminou **Ricksaw** com **ak47** no setor **Janela**
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1120, -897, -168)` [Mira: Yaw 87° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Strafe-Dir(Shift)` | **125ms:** `Parado (0u)` | **250ms:** `Strafe-Dir(Shift)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(-1457, -913, -168)` [Mira: Yaw 28° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Esq(Duck+Jump)` | **125ms:** `Parado (0u)` | **250ms:** `Diag-Esq(Duck+Jump)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Audio_HeardCue` em `(-14, -453, -168)` [Mira: Yaw -175° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(250u)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-497, 410, -160)` [Mira: Yaw -174° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(250u)`

<details><summary><b>📊 Snapshot Tático das [07:55] (9 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 64 | awp | Catwalk / Short | `-211,-416,-142` | `4°,-169°` | 214.9 (Z -261 / 3D 338 aéreo) | PASSIVE_HOLD | ONNX_Audio_HeardCue | Avanco(250u+Jump) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act58) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Palácio A | `407,-2000,-40` | `2°,-4°` | 195.3 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | CT Spawn | `-1120,-897,-168` | `5°,87°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1498,-934,-114` | `2°,28°` | 209.9 (Z 61 / 3D 219 aéreo) | JIGGLE_INFO | ONNX_Vision_Spotted | Recuo(250u+Jump) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act58) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | ak47 | Catwalk / Short | `-26,-455,-168` | `2°,-174°` | 166.8 | JIGGLE_INFO | ONNX_Audio_HeardCue | Avanco(250u) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act9) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 93 | famas | Top Mid | `56,-399,-183` | `3°,-172°` | 212.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_palace_room)) | Pending | Movendo |
| 8 | Syfers (Anchor) | CT | 100 | hkp2000 | CT Spawn | `-1154,-846,-168` | `1°,17°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | hkp2000 | Bomb A | `-307,-1764,-168` | `2°,151°` | 0.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Strafe-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act44) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Beco | `-510,408,-169` | `2°,-174°` | 210.7 | JIGGLE_INFO | ONNX_Hotzone_PreMapped | Avanco(250u) | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |

</details>

- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Audio_HeardCue` em `(20, -418, -176)` [Mira: Yaw -173° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Vision_Spotted` em `(-307, -1764, -168)` [Mira: Yaw 151° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[07:55]`** `[MLMOVE - TRADE SPACING]` **Syfers** (`yielding_slot=8`) cedeu espaço para **Commando** (`priority_slot=4`) | `dist_before=61u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=8`.
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Audio_HeardCue` em `(-308, -460, -124)` [Mira: Yaw -165° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u+Jump)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Diag-Dir(250u+Jump)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Delrow** acionou `Vision_Spotted` em `(828, -2039, -40)` [Mira: Yaw 68° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Diag-Esq(250u)`
- **`[07:55]`** `[COMBATE]` **Shark** causou **74 HP** em **Syfers** com **awp** a **929u** (HP 100→26, raw=74, overkill=0, setor: Janela)
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1138, -760, -168)` [Mira: Yaw 107° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck)` | **125ms:** `Strafe-Dir(Duck)` | **250ms:** `Parado (0u)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(-1712, -1038, -207)` [Mira: Yaw 12° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Strafe-Esq(Duck)` | **125ms:** `Strafe-Esq(Duck)` | **250ms:** `Parado (0u)`
- **`[07:55]`** `[COMBATE]` **Rebel** causou **7 HP** em **Syfers** com **famas** a **898u** (HP 26→19, raw=6, overkill=0, setor: Janela)
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Vision_Spotted` em `(-223, -494, -165)` [Mira: Yaw -171° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`

<details><summary><b>📊 Snapshot Tático das [07:55] (9 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 64 | awp | Catwalk / Short | `-257,-452,-166` | `2°,-168°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Avanco(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act42) | Pending | None |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Palácio A | `869,-1982,-4` | `2°,82°` | 209.2 (Z 89 / 3D 228 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | CT Spawn | `-1130,-754,-168` | `-0°,108°` | 10.4 | PASSIVE_HOLD | ONNX_Vision_Spotted | Diag-Esq(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act36) | Pending | None |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1712,-1038,-207` | `2°,12°` | 0.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Strafe-Dir(Shift) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act22) | Pending | None |
| 6 | Shamat (Rotator) | TR | 100 | ak47 | Catwalk / Short | `-223,-494,-165` | `3°,-171°` | 0.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 7 | Rebel (Anchor) | TR | 93 | famas | Catwalk / Short | `-301,-400,-167` | `2°,-164°` | 10.5 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 8 | Syfers (Anchor) | CT | 19 | hkp2000 | Janela | `-1166,-638,-168` | `0°,96°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | hkp2000 | Bomb A | `-493,-1666,-172` | `2°,152°` | 0.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Underpass | `-1040,321,-368` | `2°,-94°` | 173.5 | JIGGLE_INFO | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |

</details>

- **`[07:55]`** `[MORTE]` **Rebel** eliminou **Syfers** com **famas** no setor **Janela**
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Vision_Spotted` em `(-300, -400, -167)` [Mira: Yaw -164° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Vision_Spotted` em `(-493, -1666, -172)` [Mira: Yaw 153° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Audio_HeardCue` em `(-257, -452, -166)` [Mira: Yaw -171° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Avanco(Shift)` | **125ms:** `Parado (0u)` | **250ms:** `Avanco(Shift)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1130, -754, -168)` [Mira: Yaw 114° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(-1712, -1044, -170)` [Mira: Yaw 13° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Recuo-Esq(Duck+Jump)` | **125ms:** `Recuo-Esq(Duck+Jump)` | **250ms:** `Recuo-Dir(Duck)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Audio_HeardCue` em `(-571, -557, -274)` [Mira: Yaw -144° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Strafe-Esq(Duck)` | **125ms:** `Parado (0u)` | **250ms:** `Strafe-Esq(Duck)`

<details><summary><b>📊 Snapshot Tático das [07:55] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 64 | awp | Catwalk / Short | `22,-399,-137` | `0°,133°` | 245.2 (Z -236 / 3D 340 aéreo) | PASSIVE_HOLD | ONNX_Audio_HeardCue | Recuo-Esq(250u+Jump) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act49) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Palácio A | `935,-1543,-139` | `1°,36°` | 204.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | CT Spawn | `-1130,-754,-168` | `0°,114°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1675,-1072,-146` | `1°,13°` | 234.2 (Z -76 / 3D 246 aéreo) | JIGGLE_INFO | ONNX_Vision_Spotted | Diag-Esq(250u) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act16) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 100 | ak47 | Meio | `-572,-557,-274` | `1°,-132°` | 0.0 | JIGGLE_INFO | ONNX_Audio_HeardCue | Strafe-Esq(Duck) | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act39) | Pending | None |
| 7 | Rebel (Anchor) | TR | 93 | famas | Catwalk / Short | `-583,-513,-144` | `5°,-165°` | 0.0 | PASSIVE_HOLD | Nenhuma | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act42) | Pending | None |
| 9 | Buckshot (Rotator) | CT | 100 | hkp2000 | Bomb A | `-493,-1666,-172` | `1°,154°` | 0.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Strafe-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act44) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Underpass | `-1044,-303,-368` | `1°,-68°` | 212.6 | JIGGLE_INFO | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |

</details>

- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Audio_HeardCue` em `(-577, -510, -114)` [Mira: Yaw -152° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Recuo(Shift+Jump)` | **125ms:** `Recuo-Dir(Shift)` | **250ms:** `Recuo(Duck+Jump)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Vision_Spotted` em `(-493, -1666, -172)` [Mira: Yaw 153° | CPU: `0.69ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck)` | **125ms:** `Strafe-Dir(Duck)` | **250ms:** `Parado (0u)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Hotzone_PreMapped` em `(-950, -595, -266)` [Mira: Yaw -47° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[07:55]`** `[COMBATE]` **Buckshot** causou **21 HP** em **Rebel** com **hkp2000** a **1295u** (HP 93→72, raw=20, overkill=0, setor: Catwalk / Short)
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Vision_Spotted` em `(301, -219, -168)` [Mira: Yaw 73° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Avanco(250u)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Commando** acionou `Vision_Spotted` em `(-1187, -621, -168)` [Mira: Yaw 7° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck)` | **125ms:** `Strafe-Dir(Duck)` | **250ms:** `Strafe-Dir(Duck)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(-1585, -1100, -230)` [Mira: Yaw 25° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[07:55]`** `[COMBATE]` **Commando** causou **19 HP** em **Shamat** com **hkp2000** a **627u** (HP 100→81, raw=19, overkill=0, setor: Meio)
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Vision_Spotted` em `(-572, -558, -274)` [Mira: Yaw -136° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck)` | **125ms:** `Strafe-Dir(Duck)` | **250ms:** `Parado (0u)`

<details><summary><b>📊 Snapshot Tático das [07:55] (8 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 64 | awp | Top Mid | `289,-181,-125` | `0°,-171°` | 225.9 (Z 89 / 3D 243 aéreo) | PASSIVE_HOLD | ONNX_Vision_Spotted | Diag-Esq(250u+Jump) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act56) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Palácio A | `1306,-1276,-168` | `-0°,91°` | 162.3 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |
| 4 | Commando (EntryFragger) | CT | 100 | hkp2000 | Janela | `-1187,-621,-168` | `14°,-5°` | 0.0 | PASSIVE_HOLD | ONNX_Vision_Spotted | Strafe-Esq(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act45) | Pending | None |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1585,-1100,-230` | `-0°,25°` | 0.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Strafe-Esq(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act46) | Pending | None |
| 6 | Shamat (Rotator) | TR | 81 | ak47 | Meio | `-572,-558,-274` | `-10°,-146°` | 0.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Strafe-Dir(Duck) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act47) | Pending | None |
| 7 | Rebel (Anchor) | TR | 72 | famas | Catwalk / Short | `-723,-416,-106` | `4°,160°` | 278.1 (Z -11 / 3D 278 aéreo) | PASSIVE_HOLD | ONNX_Vision_Spotted | Strafe-Dir(250u) | EmergencyFallback:NavigateNavMesh(AlertNearbyTeammatesOfThreat_TradeFocus) | Pending | Movendo |
| 9 | Buckshot (Rotator) | CT | 100 | hkp2000 | Bomb A | `-668,-1637,-169` | `-1°,93°` | 0.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 10 | Steel (Rotator) | TR | 100 | ak47 | Meio | `-735,-754,-262` | `-0°,-71°` | 212.7 | JIGGLE_INFO | ONNX_Vision_Spotted | Avanco(250u) | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |

</details>

- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Vision_Spotted` em `(-698, -470, -113)` [Mira: Yaw -177° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Recuo-Dir(Duck+Jump)` | **125ms:** `Recuo-Dir(250u+Jump)` | **250ms:** `Strafe-Dir(250u+Jump)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Buckshot** acionou `Vision_Spotted` em `(-667, -1637, -169)` [Mira: Yaw 92° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Strafe-Esq(Shift)` | **125ms:** `Parado (0u)` | **250ms:** `Strafe-Esq(Shift)`
- **`[07:55]`** `[COMBATE]` **Commando** causou **23 HP** em **Steel** com **hkp2000** a **578u** (HP 100→77, raw=23, overkill=0, setor: Meio)
- **`[07:55]`** `[COMBATE]` **Rebel** causou **28 HP** em **Commando** com **famas** a **532u** (HP 100→72, raw=28, overkill=0, setor: Janela)
- **`[07:55]`** `[COMBATE]` **Shamat** causou **28 HP** em **Commando** com **ak47** a **627u** (HP 72→44, raw=27, overkill=0, setor: Janela)
- **`[07:55]`** `[MORTE]` **Rebel** eliminou **Commando** com **famas** no setor **Janela**
- **`[07:55]`** `[COMBATE]` **Rebel** causou **20 HP** em **Buckshot** com **famas** a **1137u** (HP 100→80, raw=20, overkill=0, setor: Bomb A)
- **`[07:55]`** `[MORTE]` **Rebel** eliminou **Buckshot** com **famas** no setor **Bomb A**
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Steel** acionou `Audio_HeardCue` em `(-638, -832, -264)` [Mira: Yaw -92° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Diag-Dir(Duck)` | **125ms:** `Diag-Dir(Duck)` | **250ms:** `Parado (0u)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(-1585, -1100, -230)` [Mira: Yaw 49° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Audio_HeardCue` em `(-735, -601, -270)` [Mira: Yaw -73° | CPU: `0.68ms`] -> Horizontes: **0ms:** `Parado (0u)` | **125ms:** `Parado (0u)` | **250ms:** `Parado (0u)`

<details><summary><b>📊 Snapshot Tático das [07:55] (6 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 64 | awp | Catwalk / Short | `19,-455,-176` | `-1°,-143°` | 189.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_top_mid_boxes)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | TR Spawn | `1303,-689,-168` | `-2°,-131°` | 105.9 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1585,-1100,-230` | `-0°,54°` | 0.0 | JIGGLE_INFO | ONNX_Vision_Spotted | Parado (0u) | MicroMove:HoldStop(ONNX_Vision_Spotted_StandStill) | Pending | None |
| 6 | Shamat (Rotator) | TR | 81 | ak47 | Meio | `-735,-601,-270` | `-6°,-77°` | 0.0 | JIGGLE_INFO | Nenhuma | MicroMove:UsercmdVector(ONNX_Audio_HeardCue_Act34) | Pending | None |
| 7 | Rebel (Anchor) | TR | 12 | famas | Catwalk / Short | `-669,-501,-135` | `-1°,158°` | 0.0 (Z 289 / 3D 289 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:UsercmdVector(SpotJiggleInfo) | Pending | None |
| 10 | Steel (Rotator) | TR | 57 | ak47 | Meio | `-628,-879,-245` | `-2°,-91°` | 184.8 | JIGGLE_INFO | ONNX_Audio_HeardCue | Avanco(250u) | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |

</details>

- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Hotzone_PreMapped` em `(-16, -460, -168)` [Mira: Yaw -158° | CPU: `0.65ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u)` | **250ms:** `Avanco(250u)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Audio_HeardCue` em `(-642, -502, -104)` [Mira: Yaw 145° | CPU: `0.65ms`] -> Horizontes: **0ms:** `Recuo-Esq(250u+Jump)` | **125ms:** `Recuo-Esq(250u)` | **250ms:** `Recuo-Esq(250u+Jump)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Hotzone_PreMapped` em `(-676, -914, -198)` [Mira: Yaw -94° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(250u)` | **125ms:** `Avanco(250u+Jump)` | **250ms:** `Avanco(Shift)`

<details><summary><b>📊 Snapshot Tático das [07:55] (6 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 64 | awp | Catwalk / Short | `-30,-457,-168` | `-0°,176°` | 95.5 | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Diag-Dir(Shift) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act26) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Palácio A | `1075,-1043,-262` | `-2°,-147°` | 160.5 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1599,-966,-196` | `-2°,97°` | 240.0 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 81 | ak47 | Meio | `-677,-927,-206` | `-2°,-94°` | 213.5 (Z -11 / 3D 214 aéreo) | JIGGLE_INFO | ONNX_Hotzone_PreMapped | Avanco(250u) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act13) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 12 | famas | Catwalk / Short | `-193,-381,-149` | `-2°,172°` | 215.9 (Z -261 / 3D 338 aéreo) | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Recuo(250u+Jump) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act64) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 57 | ak47 | Bomb A | `-695,-1433,-168` | `-2°,-98°` | 215.0 | JIGGLE_INFO | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |

</details>

- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Hotzone_PreMapped` em `(-39, -461, -167)` [Mira: Yaw 175° | CPU: `0.67ms`] -> Horizontes: **0ms:** `Avanco(Duck)` | **125ms:** `Avanco(Duck)` | **250ms:** `Strafe-Dir(Duck)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Rebel** acionou `Hotzone_PreMapped` em `(-176, -385, -167)` [Mira: Yaw 174° | CPU: `0.65ms`] -> Horizontes: **0ms:** `Avanco(Duck)` | **125ms:** `Avanco(Duck)` | **250ms:** `Parado (0u)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Hotzone_PreMapped` em `(-1581, -728, -168)` [Mira: Yaw 139° | CPU: `0.70ms`] -> Horizontes: **0ms:** `Diag-Esq(250u)` | **125ms:** `Diag-Esq(250u)` | **250ms:** `Diag-Esq(250u)`

<details><summary><b>📊 Snapshot Tático das [07:55] (6 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 64 | awp | Catwalk / Short | `-323,-450,-153` | `-0°,173°` | 216.0 (Z -261 / 3D 338 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_top_mid_boxes)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Palácio A | `670,-1406,-264` | `-2°,-150°` | 215.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | Mercado / Kitchen | `-1580,-687,-168` | `-2°,147°` | 0.0 | JIGGLE_INFO | ONNX_Hotzone_PreMapped | Parado (0u) | MicroMove:HoldStop(ONNX_Hotzone_PreMapped_StandStill) | Pending | None |
| 6 | Shamat (Rotator) | TR | 81 | ak47 | Conector | `-798,-1236,-168` | `-2°,-139°` | 0.0 | JIGGLE_INFO | Nenhuma | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act41) | Pending | None |
| 7 | Rebel (Anchor) | TR | 12 | famas | Catwalk / Short | `-177,-385,-167` | `-2°,174°` | 43.7 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 57 | ak47 | Bomb A | `-757,-1976,-180` | `-2°,-72°` | 215.0 | JIGGLE_INFO | Nenhuma | BombObjective:NavigateNavMesh(C4Carrier_AdvanceToSite_B) | Pending | Movendo |

</details>

- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Hotzone_PreMapped` em `(-798, -1236, -168)` [Mira: Yaw -145° | CPU: `0.66ms`] -> Horizontes: **0ms:** `Strafe-Dir(Duck)` | **125ms:** `Strafe-Dir(Duck)` | **250ms:** `Parado (0u)`
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shark** acionou `Hotzone_PreMapped` em `(-532, -416, -168)` [Mira: Yaw 154° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Diag-Dir(250u)` | **125ms:** `Diag-Dir(250u)` | **250ms:** `Diag-Dir(250u)`
- **`[07:55]`** `[MLMOVE - TRADE SPACING]` **Rebel** (`yielding_slot=7`) cedeu espaço para **Shark** (`priority_slot=1`) | `dist_before=51u < 140u` | `shared_target=False` | `cooldown=2.5s` | `action=4`.

<details><summary><b>📊 Snapshot Tático das [07:55] (6 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 64 | awp | Catwalk / Short | `-600,-344,-153` | `-0°,140°` | 170.0 (Z -261 / 3D 311 aéreo) | PASSIVE_HOLD | ONNX_Hotzone_PreMapped | Diag-Dir(Shift+Jump) | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act73) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Rampa A | `348,-1561,-186` | `-0°,-169°` | 199.4 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | Mercado / Kitchen | `-1866,-495,-168` | `-3°,96°` | 110.6 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 81 | ak47 | Conector | `-699,-1258,-168` | `-0°,-157°` | 158.3 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 12 | famas | Catwalk / Short | `-641,-344,-121` | `-0°,-153°` | 199.5 (Z 39 / 3D 203 aéreo) | PASSIVE_HOLD | Nenhuma | MicroMove:UsercmdVector(ONNX_Hotzone_PreMapped_Act55) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 57 | ak47 | Bomb A | `-544,-2249,-177` | `-0°,63°` | 215.0 | JIGGLE_INFO | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |

</details>


<details><summary><b>📊 Snapshot Tático das [07:55] (6 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 64 | awp | Catwalk / Short | `-768,-80,-165` | `-0°,133°` | 200.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_top_mid_boxes)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Bomb A | `-92,-1750,-168` | `1°,-135°` | 187.9 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | Mercado / Kitchen | `-1633,-696,-168` | `-0°,103°` | 211.7 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(ct_a_jungle_support)) | Pending | Movendo |
| 6 | Shamat (Rotator) | TR | 81 | ak47 | Jungle | `-1054,-1394,-166` | `1°,129°` | 210.5 | JIGGLE_INFO | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 7 | Rebel (Anchor) | TR | 12 | famas | Catwalk / Short | `-829,135,-172` | `1°,173°` | 206.8 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 57 | c4 | Bomb A | `-523,-2193,-180` | `1°,85°` | 0.0 | JIGGLE_INFO | Nenhuma | BombObjective:ReleaseHoldAndRepath(C4Carrier_InBombZone_AuthorizedToPlant) | Pending | None |

</details>

- **`[07:55]`** `[BOMBA]` C4 plantada no bombsite!
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Shamat** acionou `Vision_Spotted` em `(-1263, -1028, -168)` [Mira: Yaw 111° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Avanco(Shift)` | **125ms:** `Avanco(250u)` | **250ms:** `Diag-Dir(250u)`

<details><summary><b>📊 Snapshot Tático das [07:55] (6 vivos)</b></summary>

| Slot | Jogador (Role) | Time | HP | Arma | Setor | Coord (X,Y,Z) | Mira (P,Y) | Vel 2D (u/s) | Stance | Ação Prevista (ONNX) | CurrentWinningIntent | CurrentIntentOutcome | LastCompletedOutcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Shark (AWPer) | TR | 64 | awp | Catwalk / Short | `-1192,140,-170` | `-0°,-172°` | 200.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_top_mid_boxes)) | Pending | Movendo |
| 3 | Delrow (EntryFragger) | TR | 100 | ak47 | Bomb A | `-466,-2083,-143` | `2°,-119°` | 161.8 (Z 211 / 3D 266 aéreo) | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(tr_staging_underpass_top)) | Pending | Movendo |
| 5 | Soldier (Rotator) | CT | 100 | hkp2000 | CT Spawn | `-1460,-903,-168` | `2°,143°` | 0.0 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:HoldStop(CT_TacticalSave_Hold) | Pending | None |
| 6 | Shamat (Rotator) | TR | 81 | ak47 | CT Spawn | `-1270,-1012,-155` | `5°,146°` | 0.0 (Z 264 / 3D 264 aéreo) | AGGRESSIVE_POKE | ONNX_Vision_Spotted | Avanco(Shift+Jump) | MicroMove:UsercmdVector(ONNX_Vision_Spotted_Act72) | Pending | None |
| 7 | Rebel (Anchor) | TR | 12 | famas | Bomb B | `-1470,157,-167` | `2°,-148°` | 220.0 | PASSIVE_HOLD | Nenhuma | TacticalNavigation:NavigateNavMesh(TransitTo(Target)) | Pending | Movendo |
| 10 | Steel (Rotator) | TR | 57 | ak47 | Bomb A | `-387,-2122,-180` | `2°,27°` | 80.6 | AGGRESSIVE_POKE | Nenhuma | EmergencyFallback:NavigateNavMesh(TransitTo(tr_staging_a_ramp)) | Pending | Movendo |

</details>

- **`[07:55]`** `[COMBATE]` **Shamat** causou **35 HP** em **Soldier** com **ak47** a **221u** (HP 100→65, raw=35, overkill=0, setor: CT Spawn)
- **`[07:55]`** `[MLMOVE - ONNX 16HZ]` `[Modo ONNX Ativo]` **Soldier** acionou `Vision_Spotted` em `(-1460, -903, -168)` [Mira: Yaw 4° | CPU: `0.64ms`] -> Horizontes: **0ms:** `Recuo(250u)` | **125ms:** `Parado (0u)` | **250ms:** `Recuo(250u)`
- **`[07:55]`** `[MORTE]` **Shamat** eliminou **Soldier** com **ak47** (HEADSHOT 💥) no setor **CT Spawn**
- **`[07:55]`** `[FIM_ROUND]` internal_round_id=5 | round_oficial=5 | Vencedor: Terrorist | Motivo: `TerroristsWin` (9) — Eliminação total dos Contraterroristas pelos Terroristas | Placar: CT 1 x 4 TR | tick=25208

---
## 🏁 Encerramento da Captura
- **capture_end_reason:** `MATCH_COMPLETED`
- **captured_rounds:** 5 | **complete_rounds:** 5 | **partial_round_id:** none
- **late_events_total:** 2
- **end_tick:** 0 | **end_timestamp:** 2026-11-04 22:18:19

> [!NOTE]
> capture_end_reason=MATCH_COMPLETED
> captured_rounds=5
> complete_rounds=5
> partial_round_id=none

### 📈 Resumo Agregado do MovementExecutionTracker (V4.2.6)
| Métrica | Total | Percentual |
| :--- | :--- | :--- |
| **TotalSamples** | `0` | 100.0% |
| **AppliedWithProgress** | `0` | 0.0% |
| **AppliedLowProgress** | `0` | 0.0% |
| **AppliedNoProgress** | `0` | 0.0% |
| **AuthorizedHoldApplied** | `0` | 0.0% |
| **FullStopApplied** | `0` | 0.0% |
| **BlockedByGeometryOrNavigation** | `0` | 0.0% |
| **PossibleExternalControllerOverride** | `0` | 0.0% |

#### 🧱 Auditoria de Bloqueio Geométrico e Ciclo de Vida (V4.2.5)
| Métrica | Valor | Descrição |
| :--- | :--- | :--- |
| **GeometryBlockDetected** | `0` | Total de classificações de GeometryBlock |
| **GeometryBlockRecoveryStarted** | `0` | Quantidade que iniciou recovery físico |
| **GeometryBlockRecovered** | `0` | Quantidade que recuperou movimentação com sucesso |
| **GeometryBlockFailed** | `0` | Falhas definitivas de recuperação geométrica |
| **PhysicalSamplesFinalizedAsBlocked** | `0` | Amostras físicas que finalizaram como bloqueadas |

#### 🛑 Auditoria de Classificação de Standstill e Recovery (V4.2.4)
| Classificação | Standstill Detectado | Recovery Permitido | Recovery Suprimido |
| :--- | :--- | :--- | :--- |
| **FalseRecoverySuppressedTotal** | - | - | `0` |

#### 🔄 Auditoria de Recovery por Resultado (V4.2.4)
| Métrica de Recovery | Valor |
| :--- | :--- |
| **RecoveryStarted** | `0` |
| **RecoverySucceeded** | `0` |
| **RecoveryEscalatedStage2** | `0` |
| **RecoveryEscalatedStage3** | `0` |
| **RecoveryFailed** | `0` |
| **MedianRecoveryTimeMs** | `0.0 ms` |
| **MedianRecoveryDisplacement** | `0.0 u` |
| **RepeatedRecoverySameSlot** | `0` |

#### 🛡️ Auditoria de Integridade por Episódio (V4.2.5)
| Métrica | Valor | Detalhes |
| :--- | :--- | :--- |
| **TotalIntegrityEpisodes** | `0` | Incidentes reais consolidados de integridade |
| **TransientEpisodes (< 16 ticks)** | `0` | Incidentes transitórios rapidamente corrigidos |
| **PersistentEpisodes (>= 16 ticks)** | `0` | Incidentes de alteração persistente da engine |
| **SamplesInEpisodes** | `0` | Total de amostras físicas brutas agrupadas |
| **MeanEpisodeDurationMs** | `0.0 ms` | Duração média de cada incidente |

#### 💣 Auditoria de Bombsite da C4 e Retake (V4.2.6)
| Métrica | Valor | Detalhes |
| :--- | :--- | :--- |
| **UniqueC4MismatchEpisodes** | `0` | Episódios únicos consolidados de divergência de bombsite |
| **C4SemanticMismatches** | `0` | Divergências semânticas entre CommittedSite, MaterializedRealSite e CarrierTarget |
| **TotalMismatchTicks** | `0` | Total de ticks sob correção de mismatch |
| **StaleObjectivesRejected** | `0` | Objetivos com revisão obsoleta rejeitados pelo Arbitrator |
| **RetakeSiteMismatches** | `0` | Tentativas de desvio do retake CT em relação ao PlantedSite |

#### 🦘 Auditoria de Controle de Jump (V4.2.8)
| Métrica | Valor | Detalhes |
| :--- | :--- | :--- |
| **JumpRequested** | `0` | Total de intenções ou predições solicitando salto |
| **JumpExecuted** | `0` | Saltos validados e executados fisicamente |
| **JumpSuppressedAirborne** | `0` | Saltos suprimidos por estar no ar (não-renovação) |
| **JumpSuppressedCooldown** | `0` | Saltos suprimidos por cooldown ativo |
| **JumpSuppressedContext** | `0` | Saltos suprimidos por contexto proibido / consenso ONNX |
| **RepeatedJumpSequences** | `0` | Sequências repetidas de salto sem justificativa |

#### 🛡️ Auditoria de Ciclo de Vida e Isolamento de Adaptações (V4.2.8)
| Métrica | Valor | Detalhes |
| :--- | :--- | :--- |
| **CrossTeamReplacementAttempts** | `0` | Total de tentativas cruzadas interceptadas |
| **UniqueCrossTeamReplacementEpisodes** | `0` | Episódios únicos registrados (sem spam) |
| **RepeatedAttemptsSuppressed** | `0` | Tentativas repetidas suprimidas pelo deduplicador |

#### ♟️ Auditoria de Formação CT 2-1-2 (V4.2.8)
| Métrica | Valor | Detalhes |
| :--- | :--- | :--- |
| **CtFormationsMaterialized** | `10` | Total de formações materializadas |
| **CtFormationsInvalidFallback** | `0` | Formações inválidas que acionaram fallback 2-1-2 |

#### 🛡️ Detalhes de Interceptação da Engine (V4.2.4)
| Métrica de Override | Valor | Detalhes |
| :--- | :--- | :--- |
| **UnexplainedStateChanges** | `0` | Microalterações inexplicadas da engine |
| **UniqueOverrideEvents** | `0` | Eventos únicos de interceptação detectados |
| **PersistentOverrideEvents** | `0` | Alterações críticas que persistiram por >= 16 ticks |
| **SamplesAffected** | `0` | Amostras físicas na janela do override (0.0%) |
| **SnapshotAppearances** | `0` | Aparições observadas em snapshots periódicos |

#### 📊 Distribuição por Fonte da Intenção (IntentSource)
| Fonte | Amostras | WithProgress | LowProgress | NoProgress | Replaced |
| :--- | :--- | :--- | :--- | :--- | :--- |

#### 🎯 Distribuição por Tipo de Comando (MovementCommandKind)
| Tipo | Amostras | WithProgress | LowProgress | NoProgress | Hold/Stop |
| :--- | :--- | :--- | :--- | :--- | :--- |

#### ⏱️ Distribuição por Round
| RoundId | Amostras | WithProgress | LowProgress | NoProgress | ExternalOverrides |
| :--- | :--- | :--- | :--- | :--- | :--- |

#### 🧭 Matriz Vencedor -> Desfecho Físico (WinnerToPhysicalOutcomeMatrix)
```
```

