# Checklist de Revisão Humana de Spots — Mirage V2 (Fase 1.6.3)

> [!IMPORTANT]
> O documento `human_visual_spot_confirmation.md` reflete a auditoria geométrica gerada pelo pipeline autônomo (`PIPELINE_VISUAL_GEOMETRY_REVIEW`).
> Este checklist destina-se à validação pessoal presencial do operador humano no cliente CS2.
> O status de cada spot permanece como `PENDING_HUMAN_REVIEW` até a confirmação manual pelo usuário.

## Instruções para o Operador Humano no CS2
1. Inicie o CS2 em modo offline no mapa Mirage (`map de_mirage`).
2. Abra o console (`'`) e execute o `ConsoleCommand` de cada linha da tabela.
3. Avalie se o bot fica no chão firme (Z real), com boa cobertura e linha de mira adequada.
4. Atualize a coluna `UserDecision` para `APPROVED_BY_USER` ou `REJECTED_BY_USER` e registre observações em `UserNote`.

---

## Tabela de Homologação Presencial

| # | SpotId | ConsoleCommand | UserDecision | UserNote |
| :-: | :--- | :--- | :--- | :--- |
| 1 | `ct_a_ticket_passive` | `setpos -1011.5 -2479.9 -168.0; setang 0.0 60.0 0.0` | `PENDING_HUMAN_REVIEW` | Pendente de teste in-game pelo usuário |
| 2 | `ct_a_firebox_oneanddone` | `setpos -284.2 -2399.9 -164.0; setang 0.0 110.0 0.0` | `PENDING_HUMAN_REVIEW` | Pendente de teste in-game pelo usuário |
| 3 | `ct_a_ninja_hide` | `setpos -439.8 -2337.7 -168.0; setang 0.0 120.0 0.0` | `PENDING_HUMAN_REVIEW` | Pendente de teste in-game pelo usuário |
| 4 | `ct_mid_window_crouch` | `setpos -1139.4 -462.3 -168.0; setang -5.0 -20.0 0.0` | `PENDING_HUMAN_REVIEW` | Pendente de teste in-game pelo usuário |
| 5 | `ct_b_van_peek` | `setpos -2191.6 712.6 -101.8; setang 0.0 -85.0 0.0` | `PENDING_HUMAN_REVIEW` | Pendente de teste in-game pelo usuário |
| 6 | `tr_staging_a_ramp` | `setpos 321.1 -1708.1 -176.0; setang 0.0 -135.0 0.0` | `PENDING_HUMAN_REVIEW` | Pendente de teste in-game pelo usuário |
| 7 | `tr_staging_palace_room` | `setpos 288.1 -2373.4 -40.0; setang 0.0 -140.0 0.0` | `PENDING_HUMAN_REVIEW` | Pendente de teste in-game pelo usuário |
| 8 | `ct_retake_a_connector` | `setpos -802.4 -1221.3 -168.0; setang 0.0 0.0 0.0` | `PENDING_HUMAN_REVIEW` | Pendente de teste in-game pelo usuário |

---

## Status da Decisão de Produção
- Enquanto houver itens com `PENDING_HUMAN_REVIEW`, a homologação formal é classificada como:
  `MIRAGE_PROFILE_V2_READY_FOR_PRODUCTION_PENDING_HUMAN_REVIEW`
- A decisão `MIRAGE_PROFILE_V2_READY_FOR_PRODUCTION` só será declarada após confirmação humana explícita.
