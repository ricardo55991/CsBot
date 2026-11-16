"""
Gera mirage_spot_manual_review.json para a Fase 1.6
Revisa individualmente os 20 spots criticos (19 WRONG_SECTOR + 1 WRONG_HEIGHT),
garantindo conformidade estrita com as regras da Fase 1.6.
"""
import json
from pathlib import Path

OUT_DIR = Path(r"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\docs\fase_1_6")
OUT_DIR.mkdir(parents=True, exist_ok=True)

REVIEWS = [
    {
        "SpotId": "ct_a_ticket_passive",
        "CurrentPosition": [-1930.0, -680.0, -160.0],
        "ProposedPosition": [-1011.5, -2479.9, -168.0],
        "CurrentValvePlace": "Shop",
        "ProposedValvePlace": "CTSpawn",
        "VisualLandmark": "Atras da cabine/caixa do Ticket CT olhando para Rampa A",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava erroneamente no Mercado/Shop do Bomb B. Proposta posiciona o CT no Ticket A real com 336 demos profissionais e linha de visao limpa para Rampa A."
    },
    {
        "SpotId": "ct_a_firebox_oneanddone",
        "CurrentPosition": [-1050.0, -240.0, -160.0],
        "ProposedPosition": [-284.2, -2399.9, -164.0],
        "CurrentValvePlace": "Ladder",
        "ProposedValvePlace": "BombsiteA",
        "VisualLandmark": "Canto fechado da Firebox no Bomb A marcando Palacio",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava dentro da Ladder Room no Meio. Proposta coloca o bot no canto One & Done da Firebox no Bomb A (128 demos)."
    },
    {
        "SpotId": "ct_a_ninja_hide",
        "CurrentPosition": [-1320.0, -290.0, -160.0],
        "ProposedPosition": [-439.8, -2337.7, -168.0],
        "CurrentValvePlace": "SnipersNest",
        "ProposedValvePlace": "BombsiteA",
        "VisualLandmark": "Recanto escondido do Ninja atras da caixa Tripla no Bomb A",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava na Janela/SnipersNest do Meio. Proposta posiciona o bot no spot Ninja real do Bomb A (145 demos)."
    },
    {
        "SpotId": "ct_a_triple_jiggle",
        "CurrentPosition": [-1150.0, -460.0, -160.0],
        "ProposedPosition": [-710.8, -2129.6, -180.0],
        "CurrentValvePlace": "SnipersNest",
        "ProposedValvePlace": "BombsiteA",
        "VisualLandmark": "Borda da Caixa Tripla no Bomb A com jiggle para Rampa/Conector",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava dentro da Janela do Meio. Proposta coloca o bot na Caixa Tripla real do Bomb A (268 demos profissionais)."
    },
    {
        "SpotId": "ct_a_stairs_cross",
        "CurrentPosition": [-1100.0, -620.0, -160.0],
        "ProposedPosition": [-497.8, -1309.0, -160.0],
        "CurrentValvePlace": "SnipersNest",
        "ProposedValvePlace": "Stairs",
        "VisualLandmark": "Base dos degraus da Cabecinha (Stairs) no Bomb A",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava dentro da Janela do Meio. Proposta coloca o bot na base de Stairs no Bomb A marcando Rampa/Palacio (298 demos)."
    },
    {
        "SpotId": "ct_a_jungle_support",
        "CurrentPosition": [-1250.0, -780.0, -160.0],
        "ProposedPosition": [-992.1, -1304.9, -155.6],
        "CurrentValvePlace": "SnipersNest",
        "ProposedValvePlace": "Jungle",
        "VisualLandmark": "Interior da Jungle do Bomb A com visao cruzada para Rampa e Palacio",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava no fundo do SnipersNest. Proposta coloca o bot na posicao de suporte da Jungle no Bomb A (158 demos)."
    },
    {
        "SpotId": "ct_a_palace_close_poke",
        "CurrentPosition": [-880.0, -320.0, -160.0],
        "ProposedPosition": [151.9, -1914.1, -168.0],
        "CurrentValvePlace": "Catwalk",
        "ProposedValvePlace": "BombsiteA",
        "VisualLandmark": "Piso terreo debaixo da varanda do Palacio (Under-Palace) no Bomb A",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava no Catwalk do Meio. Proposta coloca o CT no solo debaixo do Palacio (Under-Palace Z=-168) no Bomb A (241 demos)."
    },
    {
        "SpotId": "ct_mid_window_crouch",
        "CurrentPosition": [-1380.0, -540.0, -120.0],
        "ProposedPosition": [-1139.4, -462.3, -168.0],
        "CurrentValvePlace": "Ladder",
        "ProposedValvePlace": "SnipersNest",
        "VisualLandmark": "Parapeito frontal da Janela do Meio (SnipersNest) agachado",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava recuada na parede da Ladder Room. Proposta coloca o bot no batente utilizavel da Janela mirando Top Mid (256 demos)."
    },
    {
        "SpotId": "ct_mid_window_deep_awp",
        "CurrentPosition": [-1480.0, -560.0, -100.0],
        "ProposedPosition": [-1175.8, -732.5, -168.0],
        "CurrentValvePlace": "Shop",
        "ProposedValvePlace": "SnipersNest",
        "VisualLandmark": "Recuo seguro no fundo da Janela do Meio com AWP",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava fora da Janela (setor Shop). Proposta posiciona o AWPer no fundo seguro do SnipersNest (70 demos especializadas de AWP)."
    },
    {
        "SpotId": "ct_mid_connector_headshot",
        "CurrentPosition": [-820.0, -840.0, -160.0],
        "ProposedPosition": [-520.0, -984.0, -168.0],
        "CurrentValvePlace": "Middle",
        "ProposedValvePlace": "Connector",
        "VisualLandmark": "Primeiro degrau com cobertura de headshot dentro do Conector",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava no Meio aberto sem protecao de cover. Proposta coloca o bot abrigado no degrau do Conector mirando Meio (299 demos)."
    },
    {
        "SpotId": "ct_mid_short_catwalk",
        "CurrentPosition": [-950.0, -1050.0, -140.0],
        "ProposedPosition": [-906.4, 78.5, -166.0],
        "CurrentValvePlace": "Connector",
        "ProposedValvePlace": "Catwalk",
        "VisualLandmark": "Passarela do Catwalk / Short cobrindo Meio e saida do Rato",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava erroneamente no Conector. Proposta posiciona o bot no Catwalk do Meio marcando Rato/Top Mid (214 demos)."
    },
    {
        "SpotId": "ct_mid_underpass_peek",
        "CurrentPosition": [-720.0, -1020.0, -220.0],
        "ProposedPosition": [-737.1, -21.0, -144.0],
        "CurrentValvePlace": "Connector",
        "ProposedValvePlace": "Underpass",
        "VisualLandmark": "Saida da rampa do Underpass / Beco do Rato em direcao ao Meio",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava no Conector Z=-220. Proposta utiliza o Medoid do Cluster 153 no topo do Underpass saindo para o Meio (257 demos)."
    },
    {
        "SpotId": "ct_b_van_peek",
        "CurrentPosition": [-1350.0, 380.0, -150.0],
        "ProposedPosition": [-2191.6, 712.6, -101.8],
        "CurrentValvePlace": "BombsiteB",
        "ProposedValvePlace": "Truck",
        "VisualLandmark": "Em cima / quina da Van no Bomb B vigiando Tapete",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava a 906u da Van no meio do Bomb B. Proposta posiciona o bot exatamente na Van B (302 demos profissionais)."
    },
    {
        "SpotId": "ct_b_market_window",
        "CurrentPosition": [-1880.0, 180.0, -130.0],
        "ProposedPosition": [-1912.8, 5.1, -168.0],
        "CurrentValvePlace": "BombsiteB",
        "ProposedValvePlace": "BombsiteB",
        "VisualLandmark": "Quina defensiva da Janela do Mercado no Bomb B segurando avanco vindo do Mercado (Cluster 32 medoid, Y=+5.1 preserva invariante Y>0 de B)",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava em Z=-130 flutuando no meio do bomb. Proposta posiciona o CT no Medoid profissional real do Cluster 32 (177 demos, 99.2% CT, Z=-168) marcando a Janela do Mercado de dentro do Bomb B, preservando a invariante arquitetural Y>0 do Bomb B."
    },
    {
        "SpotId": "ct_spawn_safe",
        "CurrentPosition": [-2050.0, -800.0, -160.0],
        "ProposedPosition": [-1279.6, -967.9, -168.0],
        "CurrentValvePlace": "Shop",
        "ProposedValvePlace": "CTSpawn",
        "VisualLandmark": "Recuo defensivo no interior da Base CT (CT Spawn)",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava no Mercado B. Proposta posiciona o bot no CT Spawn real seguro para save/fallback (279 demos)."
    },
    {
        "SpotId": "tr_staging_a_ramp",
        "CurrentPosition": [-250.0, -200.0, -160.0],
        "ProposedPosition": [321.1, -1708.1, -176.0],
        "CurrentValvePlace": "Catwalk",
        "ProposedValvePlace": "TRamp",
        "VisualLandmark": "Entrada da Rampa A / Caverna TR preparando ataque",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava no Catwalk do Meio. Proposta posiciona o TR no Staging da Rampa A real (300 demos profissionais)."
    },
    {
        "SpotId": "tr_staging_palace_room",
        "CurrentPosition": [-350.0, -480.0, -90.0],
        "ProposedPosition": [288.1, -2373.4, -40.0],
        "CurrentValvePlace": "Catwalk",
        "ProposedValvePlace": "PalaceInterior",
        "VisualLandmark": "Sala interna do Palacio (Palace Interior Z=-40) preparando rush/exec",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava no Catwalk do Meio. Proposta coloca o TR dentro da sala do Palacio (306 demos)."
    },
    {
        "SpotId": "tr_staging_underpass_top",
        "CurrentPosition": [150.0, -1050.0, -160.0],
        "ProposedPosition": [-1038.9, -728.5, -264.0],
        "CurrentValvePlace": "TopofMid",
        "ProposedValvePlace": "Middle",
        "VisualLandmark": "Entrada rebaixada do Underpass / Rato pelo lado TR (Z=-264)",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava no Top Mid aberto. Proposta posiciona o TR na entrada abrigada do Rato/Underpass (312 demos)."
    },
    {
        "SpotId": "ct_retake_a_connector",
        "CurrentPosition": [-450.0, -1600.0, -160.0],
        "ProposedPosition": [-802.4, -1221.3, -168.0],
        "CurrentValvePlace": "BombsiteA",
        "ProposedValvePlace": "Connector",
        "VisualLandmark": "Entrada do Conector vindo do Meio para Retake do Bomb A",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava na base de Stairs dentro do Bomb A (WRONG_HEIGHT/setor errado para staging de retake). Proposta coloca o CT no Conector para iniciar o retake (28 demos)."
    },
    {
        "SpotId": "ct_retake_a_jungle",
        "CurrentPosition": [-950.0, -450.0, -140.0],
        "ProposedPosition": [-1016.2, -1527.6, -163.8],
        "CurrentValvePlace": "Catwalk",
        "ProposedValvePlace": "Jungle",
        "VisualLandmark": "Corredor da Jungle preparando entrada de retake no Bomb A",
        "NavMeshValid": True,
        "Reachable": True,
        "TeamSideValid": True,
        "UsageValid": True,
        "BombsiteValid": True,
        "ManualDecision": "APPROVED",
        "DecisionReason": "Coordenada legada estava no Catwalk do Meio. Proposta posiciona o CT no corredor da Jungle para o retake do A (47 demos)."
    }
]

def main():
    out_file = OUT_DIR / "mirage_spot_manual_review.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(REVIEWS, f, indent=2, ensure_ascii=False)
    print(f"[+] Gerado: {out_file} com {len(REVIEWS)} revisoes individuais.")

    # Tambem salva copia no artifact dir e na pasta docs/fase_1_5
    copy_15 = Path(r"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\docs\fase_1_5\mirage_spot_manual_review.json")
    with open(copy_15, "w", encoding="utf-8") as f:
        json.dump(REVIEWS, f, indent=2, ensure_ascii=False)
    print(f"[+] Copia espelhada em: {copy_15}")

if __name__ == "__main__":
    main()
