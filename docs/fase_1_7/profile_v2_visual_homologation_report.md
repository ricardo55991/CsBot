# Relatório de Homologação Visual Humana — Mirage V2 (Fase 1.7)

> [!IMPORTANT]
> Este relatório apresenta as evidências capturadas no CS2 real (`de_mirage`) para os 8 spots mais sensíveis do mapa.
> A decisão de homologação presencial cabe exclusivamente ao usuário humano através do checklist curto.

## O que o usuário avaliará

Para cada um dos 8 spots, o usuário avaliará exclusivamente 4 perguntas visuais diretas:
1. **O spot está no landmark correto?**
2. **O bot está apoiado corretamente, sem flutuar ou entrar na geometria?**
3. **A posição oferece a cobertura coerente com o uso tático?**
4. **O ângulo aponta para a entrada ou linha que deveria vigiar?**

> [!NOTE]
> Aspectos de baixo nível (NavMesh, hash SHA-256, bounds jogáveis, clustering, parser e contratos de locomoção) foram validados automaticamente por 291 testes unitários aprovados na suíte de testes.

---

## ct_a_ticket_passive (Ticket)

- **Name:** `Ticket / Cabine CT`
- **Sector:** `Bombsite A`
- **Side:** `CounterTerrorist`
- **AssociatedBombsite:** `A`
- **Usage:** `Hold`
- **AllowedRoles:** `["AWPer", "Anchor", "Rotator"]`
- **Confidence:** `MEDIUM`
- **ValidationStatus:** `PENDING_HUMAN_REVIEW`
- **Position:** `[-1011.5, -2479.9, -168.0]`
- **Angles:** `[0.0, 60.0, 0.0]`
- **ConsoleCommand:** `setpos -1011.5 -2479.9 -168.0; setang 0.0 60.0 0.0`
- **ProfileSha256:** `26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1`

### Evidências Visuais Reais CS2 (1280x720 RGBA):

**Primeira Pessoa (Visada / Ângulo Vigiado):**

![First Person](screenshots/01_ct_a_ticket_passive_first_person.png)

**Visão Externa / Aérea (Landmark / Relação com Cover):**

![External](screenshots/01_ct_a_ticket_passive_external.png)

- **UserDecision:** `PENDING_HUMAN_REVIEW`
- **UserNote:** 

---

## ct_a_firebox_oneanddone (Firebox)

- **Name:** `Firebox (One & Done)`
- **Sector:** `Bombsite A`
- **Side:** `CounterTerrorist`
- **AssociatedBombsite:** `A`
- **Usage:** `Hold`
- **AllowedRoles:** `["Anchor", "EntryFragger"]`
- **Confidence:** `MEDIUM`
- **ValidationStatus:** `PENDING_HUMAN_REVIEW`
- **Position:** `[-284.2, -2399.9, -164.0]`
- **Angles:** `[0.0, 110.0, 0.0]`
- **ConsoleCommand:** `setpos -284.2 -2399.9 -164.0; setang 0.0 110.0 0.0`
- **ProfileSha256:** `26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1`

### Evidências Visuais Reais CS2 (1280x720 RGBA):

**Primeira Pessoa (Visada / Ângulo Vigiado):**

![First Person](screenshots/02_ct_a_firebox_oneanddone_first_person.png)

**Visão Externa / Aérea (Landmark / Relação com Cover):**

![External](screenshots/02_ct_a_firebox_oneanddone_external.png)

- **UserDecision:** `PENDING_HUMAN_REVIEW`
- **UserNote:** 

---

## ct_a_ninja_hide (Ninja)

- **Name:** `Ninja / Atrás da Tripla`
- **Sector:** `Bombsite A`
- **Side:** `CounterTerrorist`
- **AssociatedBombsite:** `A`
- **Usage:** `Hold`
- **AllowedRoles:** `["Anchor", "Rotator"]`
- **Confidence:** `MEDIUM`
- **ValidationStatus:** `PENDING_HUMAN_REVIEW`
- **Position:** `[-439.8, -2337.7, -168.0]`
- **Angles:** `[0.0, 120.0, 0.0]`
- **ConsoleCommand:** `setpos -439.8 -2337.7 -168.0; setang 0.0 120.0 0.0`
- **ProfileSha256:** `26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1`

### Evidências Visuais Reais CS2 (1280x720 RGBA):

**Primeira Pessoa (Visada / Ângulo Vigiado):**

![First Person](screenshots/03_ct_a_ninja_hide_first_person.png)

**Visão Externa / Aérea (Landmark / Relação com Cover):**

![External](screenshots/03_ct_a_ninja_hide_external.png)

- **UserDecision:** `PENDING_HUMAN_REVIEW`
- **UserNote:** 

---

## ct_mid_window_crouch (Window)

- **Name:** `Janela Meio (Agachado)`
- **Sector:** `Mid`
- **Side:** `CounterTerrorist`
- **AssociatedBombsite:** `Mid`
- **Usage:** `Hold`
- **AllowedRoles:** `["AWPer", "Rotator"]`
- **Confidence:** `MEDIUM`
- **ValidationStatus:** `PENDING_HUMAN_REVIEW`
- **Position:** `[-1139.4, -462.3, -168.0]`
- **Angles:** `[-5.0, -20.0, 0.0]`
- **ConsoleCommand:** `setpos -1139.4 -462.3 -168.0; setang -5.0 -20.0 0.0`
- **ProfileSha256:** `26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1`

### Evidências Visuais Reais CS2 (1280x720 RGBA):

**Primeira Pessoa (Visada / Ângulo Vigiado):**

![First Person](screenshots/04_ct_mid_window_crouch_first_person.png)

**Visão Externa / Aérea (Landmark / Relação com Cover):**

![External](screenshots/04_ct_mid_window_crouch_external.png)

- **UserDecision:** `PENDING_HUMAN_REVIEW`
- **UserNote:** 

---

## ct_b_van_peek (Van)

- **Name:** `Van B (Jiggle Peek)`
- **Sector:** `Bombsite B`
- **Side:** `CounterTerrorist`
- **AssociatedBombsite:** `B`
- **Usage:** `Hold`
- **AllowedRoles:** `["AWPer", "Anchor", "Rotator"]`
- **Confidence:** `MEDIUM`
- **ValidationStatus:** `PENDING_HUMAN_REVIEW`
- **Position:** `[-2191.6, 712.6, -101.8]`
- **Angles:** `[0.0, -85.0, 0.0]`
- **ConsoleCommand:** `setpos -2191.6 712.6 -101.8; setang 0.0 -85.0 0.0`
- **ProfileSha256:** `26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1`

### Evidências Visuais Reais CS2 (1280x720 RGBA):

**Primeira Pessoa (Visada / Ângulo Vigiado):**

![First Person](screenshots/05_ct_b_van_peek_first_person.png)

**Visão Externa / Aérea (Landmark / Relação com Cover):**

![External](screenshots/05_ct_b_van_peek_external.png)

- **UserDecision:** `PENDING_HUMAN_REVIEW`
- **UserNote:** 

---

## tr_staging_a_ramp (Ramp)

- **Name:** `Staging: Rampa A / Caverna`
- **Sector:** `Bombsite A`
- **Side:** `Terrorist`
- **AssociatedBombsite:** `A`
- **Usage:** `Staging`
- **AllowedRoles:** `["AWPer", "EntryFragger", "Rotator", "Anchor"]`
- **Confidence:** `MEDIUM`
- **ValidationStatus:** `PENDING_HUMAN_REVIEW`
- **Position:** `[321.1, -1708.1, -176.0]`
- **Angles:** `[0.0, -135.0, 0.0]`
- **ConsoleCommand:** `setpos 321.1 -1708.1 -176.0; setang 0.0 -135.0 0.0`
- **ProfileSha256:** `26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1`

### Evidências Visuais Reais CS2 (1280x720 RGBA):

**Primeira Pessoa (Visada / Ângulo Vigiado):**

![First Person](screenshots/06_tr_staging_a_ramp_first_person.png)

**Visão Externa / Aérea (Landmark / Relação com Cover):**

![External](screenshots/06_tr_staging_a_ramp_external.png)

- **UserDecision:** `PENDING_HUMAN_REVIEW`
- **UserNote:** 

---

## tr_staging_palace_room (Palace)

- **Name:** `Staging: Sala do Palácio`
- **Sector:** `Bombsite A`
- **Side:** `Terrorist`
- **AssociatedBombsite:** `A`
- **Usage:** `Staging`
- **AllowedRoles:** `["EntryFragger", "Rotator", "Anchor"]`
- **Confidence:** `MEDIUM`
- **ValidationStatus:** `PENDING_HUMAN_REVIEW`
- **Position:** `[288.1, -2373.4, -40.0]`
- **Angles:** `[0.0, -140.0, 0.0]`
- **ConsoleCommand:** `setpos 288.1 -2373.4 -40.0; setang 0.0 -140.0 0.0`
- **ProfileSha256:** `26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1`

### Evidências Visuais Reais CS2 (1280x720 RGBA):

**Primeira Pessoa (Visada / Ângulo Vigiado):**

![First Person](screenshots/07_tr_staging_palace_room_first_person.png)

**Visão Externa / Aérea (Landmark / Relação com Cover):**

![External](screenshots/07_tr_staging_palace_room_external.png)

- **UserDecision:** `PENDING_HUMAN_REVIEW`
- **UserNote:** 

---

## ct_retake_a_connector (Retake Connector)

- **Name:** `Retake A: Conector`
- **Sector:** `Bombsite A`
- **Side:** `CounterTerrorist`
- **AssociatedBombsite:** `A`
- **Usage:** `Retake`
- **AllowedRoles:** `["EntryFragger", "Rotator", "Anchor"]`
- **Confidence:** `MEDIUM`
- **ValidationStatus:** `PENDING_HUMAN_REVIEW`
- **Position:** `[-802.4, -1221.3, -168.0]`
- **Angles:** `[0.0, 0.0, 0.0]`
- **ConsoleCommand:** `setpos -802.4 -1221.3 -168.0; setang 0.0 0.0 0.0`
- **ProfileSha256:** `26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1`

### Evidências Visuais Reais CS2 (1280x720 RGBA):

**Primeira Pessoa (Visada / Ângulo Vigiado):**

![First Person](screenshots/08_ct_retake_a_connector_first_person.png)

**Visão Externa / Aérea (Landmark / Relação com Cover):**

![External](screenshots/08_ct_retake_a_connector_external.png)

- **UserDecision:** `PENDING_HUMAN_REVIEW`
- **UserNote:** 

---

## Status da Homologação Formal

Como as 8 decisões humanas permanecem em aberto para revisão do usuário, a decisão técnica do subsistema é:
`MIRAGE_SEMANTIC_PROFILE_READY_FOR_PHASE_2_PENDING_HUMAN_REVIEW`
