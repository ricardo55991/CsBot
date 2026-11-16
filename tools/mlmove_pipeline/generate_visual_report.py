import json
import os

with open("docs/fase_1_7/mirage_uniform_spot_schema.json", "r", encoding="utf-8") as f:
    uniform_data = json.load(f)["spots"]
spots_map = {s["id"]: s for s in uniform_data}

sensitive_spots = [
    {
        "id": "ct_a_ticket_passive",
        "num": "01",
        "alias": "Ticket",
        "fp_img": "screenshots/01_ct_a_ticket_passive_first_person.png",
        "ext_img": "screenshots/01_ct_a_ticket_passive_external.png",
        "cmd": "setpos -1011.5 -2479.9 -168.0; setang 0.0 60.0 0.0"
    },
    {
        "id": "ct_a_firebox_oneanddone",
        "num": "02",
        "alias": "Firebox",
        "fp_img": "screenshots/02_ct_a_firebox_oneanddone_first_person.png",
        "ext_img": "screenshots/02_ct_a_firebox_oneanddone_external.png",
        "cmd": "setpos -284.2 -2399.9 -164.0; setang 0.0 110.0 0.0"
    },
    {
        "id": "ct_a_ninja_hide",
        "num": "03",
        "alias": "Ninja",
        "fp_img": "screenshots/03_ct_a_ninja_hide_first_person.png",
        "ext_img": "screenshots/03_ct_a_ninja_hide_external.png",
        "cmd": "setpos -439.8 -2337.7 -168.0; setang 0.0 120.0 0.0"
    },
    {
        "id": "ct_mid_window_crouch",
        "num": "04",
        "alias": "Window",
        "fp_img": "screenshots/04_ct_mid_window_crouch_first_person.png",
        "ext_img": "screenshots/04_ct_mid_window_crouch_external.png",
        "cmd": "setpos -1139.4 -462.3 -168.0; setang -5.0 -20.0 0.0"
    },
    {
        "id": "ct_b_van_peek",
        "num": "05",
        "alias": "Van",
        "fp_img": "screenshots/05_ct_b_van_peek_first_person.png",
        "ext_img": "screenshots/05_ct_b_van_peek_external.png",
        "cmd": "setpos -2191.6 712.6 -101.8; setang 0.0 -85.0 0.0"
    },
    {
        "num": "06",
        "id": "tr_staging_a_ramp",
        "alias": "Ramp",
        "fp_img": "screenshots/06_tr_staging_a_ramp_first_person.png",
        "ext_img": "screenshots/06_tr_staging_a_ramp_external.png",
        "cmd": "setpos 321.1 -1708.1 -176.0; setang 0.0 -135.0 0.0"
    },
    {
        "num": "07",
        "id": "tr_staging_palace_room",
        "alias": "Palace",
        "fp_img": "screenshots/07_tr_staging_palace_room_first_person.png",
        "ext_img": "screenshots/07_tr_staging_palace_room_external.png",
        "cmd": "setpos 288.1 -2373.4 -40.0; setang 0.0 -140.0 0.0"
    },
    {
        "num": "08",
        "id": "ct_retake_a_connector",
        "alias": "Retake Connector",
        "fp_img": "screenshots/08_ct_retake_a_connector_first_person.png",
        "ext_img": "screenshots/08_ct_retake_a_connector_external.png",
        "cmd": "setpos -802.4 -1221.3 -168.0; setang 0.0 0.0 0.0"
    }
]

sha256 = "26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1"

lines = []
lines.append("# Relatório de Homologação Visual Humana — Mirage V2 (Fase 1.7)\n")
lines.append("> [!IMPORTANT]")
lines.append("> Este relatório apresenta as evidências capturadas no CS2 real (`de_mirage`) para os 8 spots mais sensíveis do mapa.")
lines.append("> A decisão de homologação presencial cabe exclusivamente ao usuário humano através do checklist curto.\n")
lines.append("## O que o usuário avaliará\n")
lines.append("Para cada um dos 8 spots, o usuário avaliará exclusivamente 4 perguntas visuais diretas:")
lines.append("1. **O spot está no landmark correto?**")
lines.append("2. **O bot está apoiado corretamente, sem flutuar ou entrar na geometria?**")
lines.append("3. **A posição oferece a cobertura coerente com o uso tático?**")
lines.append("4. **O ângulo aponta para a entrada ou linha que deveria vigiar?**\n")
lines.append("> [!NOTE]")
lines.append("> Aspectos de baixo nível (NavMesh, hash SHA-256, bounds jogáveis, clustering, parser e contratos de locomoção) foram validados automaticamente por 291 testes unitários aprovados na suíte de testes.\n")
lines.append("---\n")

for item in sensitive_spots:
    sid = item["id"]
    sp = spots_map[sid]
    lines.append(f"## {sid} ({item['alias']})\n")
    lines.append(f"- **Name:** `{sp['name']}`")
    lines.append(f"- **Sector:** `{sp['sector']}`")
    lines.append(f"- **Side:** `{sp['side']}`")
    lines.append(f"- **AssociatedBombsite:** `{sp['associated_bombsite']}`")
    lines.append(f"- **Usage:** `{sp['usage']}`")
    lines.append(f"- **AllowedRoles:** `{json.dumps(sp['allowed_roles'])}`")
    lines.append(f"- **Confidence:** `{sp['confidence']}`")
    lines.append(f"- **ValidationStatus:** `{sp['validation_status']}`")
    lines.append(f"- **Position:** `[{sp['x']}, {sp['y']}, {sp['z']}]`")
    lines.append(f"- **Angles:** `[{sp['pitch']}, {sp['yaw']}, 0.0]`")
    lines.append(f"- **ConsoleCommand:** `{item['cmd']}`")
    lines.append(f"- **ProfileSha256:** `{sha256}`\n")
    lines.append(f"### Evidências Visuais Reais CS2 (1280x720 RGBA):\n")
    lines.append(f"**Primeira Pessoa (Visada / Ângulo Vigiado):**\n")
    lines.append(f"![First Person]({item['fp_img']})\n")
    lines.append(f"**Visão Externa / Aérea (Landmark / Relação com Cover):**\n")
    lines.append(f"![External]({item['ext_img']})\n")
    lines.append(f"- **UserDecision:** `PENDING_HUMAN_REVIEW`")
    lines.append(f"- **UserNote:** \n")
    lines.append("---\n")

lines.append("## Status da Homologação Formal\n")
lines.append("Como as 8 decisões humanas permanecem em aberto para revisão do usuário, a decisão técnica do subsistema é:")
lines.append("`MIRAGE_SEMANTIC_PROFILE_READY_FOR_PHASE_2_PENDING_HUMAN_REVIEW`\n")

with open("docs/fase_1_7/profile_v2_visual_homologation_report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("Saved docs/fase_1_7/profile_v2_visual_homologation_report.md")
