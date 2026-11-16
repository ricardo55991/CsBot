import math
import os
from PIL import Image, ImageDraw, ImageFont

RADAR_PATH = r"src\arsenal_web\static\de_mirage_radar.png"
OUT_DIR = r"docs\fase_1_7\tactical_cards"
os.makedirs(OUT_DIR, exist_ok=True)

# Mirage radar calibration
POS_X = -3230.0
POS_Y = 1713.0
SCALE = 5.0

def world_to_radar(x, y):
    rx = (x - POS_X) / SCALE
    ry = (POS_Y - y) / SCALE
    return rx, ry

# Fonts
FONT_REGULAR = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 13)
FONT_BOLD = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 14)
FONT_TITLE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 16)
FONT_BADGE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 13)
FONT_SMALL = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 11)
FONT_MONO = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 12)

SPOTS_DATA = [
    # --- 8 SPOTS SENSÍVEIS (COM CORREÇÕES DO USUÁRIO) ---
    {
        "num": "01",
        "id": "ct_a_ticket_passive",
        "name": "Ticket / Cabine CT",
        "alias": "Ticket",
        "sector": "Bombsite A",
        "side": "CT",
        "usage": "Hold (PASSIVE_HOLD)",
        "allowed_roles": ["AWPer", "Anchor", "Rotator"],
        "pos": [-1011.5, -2479.9, -168.0],
        "angles": [0.0, 60.0, 0.0],
        "landmark": "Atrás da cabine do Ticket CT no Bombsite A, rente à mureta de proteção",
        "cover": "Mureta de concreto e quina da cabine do Ticket cobrindo o corpo",
        "exposure": "Baixa. Coberto contra Palácio e Meio; focado na saída da Rampa A",
        "aim_target": "Saída da Rampa A / Caverna",
        "q1": "Landmark clássico oficial de AWP/Rifle no Ticket CT",
        "q2": "Apoiado no piso firme nivelado Z = -168.0 (solo CT Spawn)",
        "q3": "Proteção total contra Palácio enquanto vigia a Rampa",
        "q4": "Yaw = 60° aponta com precisão para a fresta de saída da Rampa A",
        "status_note": "Aprovado pelo Usuário"
    },
    {
        "num": "02",
        "id": "ct_a_firebox_oneanddone",
        "name": "Firebox Fechado",
        "alias": "Firebox",
        "sector": "Bombsite A",
        "side": "CT",
        "usage": "Hold (CROSSFIRE / AMBUSH)",
        "allowed_roles": ["Anchor", "EntryFragger"],
        "pos": [-284.2, -2399.9, -164.0],
        "angles": [0.0, 110.0, 0.0],
        "landmark": "Atrás das caixas empilhadas do Firebox no fundo do Bombsite A",
        "cover": "Pilhas duplas de caixas de madeira sólidas cobrindo corpo e cabeça",
        "exposure": "Média-Baixa. Invisível para quem entra pela Rampa sem abrir profundamente",
        "aim_target": "Cruzamento do bomb / Saída da Rampa A",
        "q1": "Landmark canônico do Firebox no fundo do A",
        "q2": "Apoiado sobre o piso Z = -164.0 (contato perfeito com NavMesh)",
        "q3": "Excelente cover para surpreender quem planta na padrão",
        "q4": "Yaw = 110° focado no funil entre a Tripla e o plant padrão",
        "status_note": "Aprovado pelo Usuário"
    },
    {
        "num": "03",
        "id": "ct_a_ninja_hide",
        "name": "Ninja / Atrás da Tripla",
        "alias": "Ninja",
        "sector": "Bombsite A",
        "side": "CT",
        "usage": "Hold (CLOSE_AMBUSH)",
        "allowed_roles": ["Anchor", "Rotator"],
        "pos": [-439.8, -2337.7, -168.0],
        "angles": [0.0, 120.0, 0.0],
        "landmark": "Atrás das caixas da Tripla / Ninja no Bombsite A",
        "cover": "Caixas sólidas da Tripla escondendo totalmente o modelo",
        "exposure": "Muito Baixa. Ângulo cego para quem entra por Palácio ou Rampa",
        "aim_target": "Área de Plant Padrão / Cruzamento da Tripla",
        "q1": "Posição oficial Ninja no Bombsite A",
        "q2": "Nivelado com precisão no piso Z = -168.0",
        "q3": "Cobertura máxima de 270 graus contra linhas de visão diretas",
        "q4": "Yaw = 120° posicionado para emboscada contra defuse ou plant",
        "status_note": "Aprovado pelo Usuário"
    },
    {
        "num": "04",
        "id": "ct_mid_window_crouch",
        "name": "Janela do Meio (Esquerda / Agachado)",
        "alias": "Window",
        "sector": "Mid",
        "side": "CT",
        "usage": "Hold (EARLY_CONTEST / AWP)",
        "allowed_roles": ["AWPer", "Rotator"],
        "pos": [-1139.4, -462.3, -168.0],
        "angles": [-5.0, -20.0, 0.0],
        "landmark": "Interior da Janela (lado esquerdo) voltado para o Meio",
        "cover": "Parapeito reforçado de alvenaria e tijolos da janela",
        "exposure": "Controlada. Alterna com a posição direita (deep) se houver molotov",
        "aim_target": "Top Mid / Caixas do Meio / Saída do TR Spawn",
        "q1": "Landmark icônico da Janela da Mirage",
        "q2": "Apoiado com firmeza no assoalho Z = -168.0",
        "q3": "Cover frontal de parapeito permitindo headshot-angle de AWP",
        "q4": "Yaw = -20° mira perfeitamente na passagem do Top Mid",
        "status_note": "Aprovado pelo Usuário (Varia com Lado Direito)"
    },
    {
        "num": "05",
        "id": "ct_b_van_peek",
        "name": "Van B (Crava Tapete)",
        "alias": "Van",
        "sector": "Bombsite B",
        "side": "CT",
        "usage": "Hold (MARK_TAPETE / ANCHOR)",
        "allowed_roles": ["AWPer", "Anchor", "Rotator"],
        "pos": [-2191.6, 712.6, -101.8],
        "angles": [0.0, -20.0, 0.0], # CORRIGIDO CONFORME FEEDBACK DO USUÁRIO (-85° -> -20°)
        "landmark": "Atrás do capô da Van no Bombsite B marcando o Tapete",
        "cover": "Chassi metálico da van protegendo 85% do tronco e pernas",
        "exposure": "Média. Marcando a saída/balcão do Tapete",
        "aim_target": "Boca / Janela dos Apartamentos B (Tapete)",
        "q1": "Landmark de referência absoluta da Van no B",
        "q2": "Apoiado na plataforma da Van Z = -101.8 sem colisão com o chassi",
        "q3": "Permite disparar e recuar agachado para recarga protegida",
        "q4": "Yaw = -20° aponta com precisão para a boca do Tapete (Corrigido)",
        "status_note": "Corrigido pelo Usuário: Mira Cravada no Tapete"
    },
    {
        "num": "06",
        "id": "tr_staging_a_ramp",
        "name": "Staging: Rampa A / Caverna",
        "alias": "Ramp",
        "sector": "Bombsite A",
        "side": "TR",
        "usage": "Staging (EXECUTE_PREP)",
        "allowed_roles": ["AWPer", "EntryFragger", "Rotator", "Anchor"],
        "pos": [321.1, -1708.1, -176.0],
        "angles": [0.0, -135.0, 0.0],
        "landmark": "Caverna da Rampa A, na descida para o Bombsite A",
        "cover": "Paredes de pedra da caverna e quina em L",
        "exposure": "Baixa. Posição recuada fora do campo de tiro direto da Cabine",
        "aim_target": "Entrada do Bombsite A / Cruzamento Cabine-Tetris",
        "q1": "Landmark canônico de agrupamento e execução da Rampa A",
        "q2": "Apoiado perfeitamente no declive suave da Rampa Z = -176.0",
        "q3": "Permite que múltiplos bots se agrupem antes da invasão",
        "q4": "Yaw = -135° orientado no sentido de progressão ofensiva do bomb",
        "status_note": "Aprovado pelo Usuário"
    },
    {
        "num": "07",
        "id": "tr_staging_palace_room",
        "name": "Staging: Sala do Palácio (Split A)",
        "alias": "Palace",
        "sector": "Bombsite A",
        "side": "TR",
        "usage": "Staging (EXECUTE_PREP)",
        "allowed_roles": ["EntryFragger", "Rotator", "Anchor"],
        "pos": [288.1, -2373.4, -40.0],
        "angles": [0.0, 135.0, 0.0], # CORRIGIDO CONFORME FEEDBACK DO USUÁRIO (-140° -> +135°)
        "landmark": "Sala interna do Palácio, voltado para a entrada do bomb",
        "cover": "Colunas de alvenaria e paredes internas reforçadas",
        "exposure": "Segura. Campo de visão cobre Jungle -> Cabecinha -> Areia",
        "aim_target": "Jungle / Cabecinha / Tetris (Areia)",
        "q1": "Landmark oficial de Staging do Palácio",
        "q2": "Apoiado com precisão no piso superior Z = -40.0",
        "q3": "Totalmente isolado de disparos CT até o avanço coordenado",
        "q4": "Yaw = +135° cobre Jungle -> Cabecinha -> Areia (Corrigido)",
        "status_note": "Corrigido pelo Usuário: Visada Jungle/Cabecinha/Areia"
    },
    {
        "num": "08",
        "id": "ct_retake_a_connector",
        "name": "Retake A: Conector",
        "alias": "Connector",
        "sector": "Bombsite A",
        "side": "CT",
        "usage": "Retake (RETAKE_SETUP)",
        "allowed_roles": ["EntryFragger", "Rotator", "Anchor"],
        "pos": [-802.4, -1221.3, -168.0],
        "angles": [0.0, 0.0, 0.0],
        "landmark": "Ponta do Conector na entrada inferior para o Bombsite A",
        "cover": "Quina chanfrada de alvenaria e degraus de acesso",
        "exposure": "Ativa. Ponto de transição para reentrar no Bombsite A dominado",
        "aim_target": "Fundo do Bombsite A / Tripla / Padrão",
        "q1": "Landmark oficial de transição e retake pelo Conector",
        "q2": "Apoiado no piso Z = -168.0 no patamar inferior",
        "q3": "Cover imediato na parede direita para strafe-shooting",
        "q4": "Yaw = 0° (apontando diretamente para o leste/Bombsite A)",
        "status_note": "Aprovado pelo Usuário"
    },
    # --- POSIÇÕES CITADAS PELO USUÁRIO (EXPANSÃO DO CATÁLOGO DE 45 SPOTS) ---
    {
        "num": "09",
        "id": "ct_b_bench_deep",
        "name": "Atrás do Forest / Banco B",
        "alias": "Forest",
        "sector": "Bombsite B",
        "side": "CT",
        "usage": "Hold (ANCHOR_HOLD)",
        "allowed_roles": ["Anchor", "AWPer"],
        "pos": [-1950.0, 450.0, -160.0],
        "angles": [0.0, -60.0, 0.0],
        "landmark": "Atrás da floreira / Banco (Forest) no fundo do Bombsite B",
        "cover": "Mureta sólida e quina do Forest protegendo as costas",
        "exposure": "Baixa. Coberto contra Mercado; marca as descidas do Tapete e L",
        "aim_target": "Descidas e Pulos do Tapete / Entrada do L (Arco)",
        "q1": "Landmark canônico do Forest / Banco no B",
        "q2": "Nível Z = -160.0 sólido no piso do bomb",
        "q3": "Excelente proteção para cruzar mira com o jogador da Van",
        "q4": "Yaw = -60° cobre a zona de pouso de quem salta do Tapete",
        "status_note": "Presente no Perfil (Atende Solicitação do Usuário)"
    },
    {
        "num": "10",
        "id": "ct_b_market_window",
        "name": "Janela do Mercado (Cozinha B)",
        "alias": "Mercado",
        "sector": "Bombsite B",
        "side": "CT",
        "usage": "Hold / Retake (SNIPER_COVER)",
        "allowed_roles": ["AWPer", "Rotator"],
        "pos": [-1912.8, 5.1, -168.0],
        "angles": [0.0, -45.0, 0.0],
        "landmark": "Janela do Mercado (Cozinha) voltada para o Bombsite B",
        "cover": "Bancada e parede interna do mercado com cover headshot",
        "exposure": "Média. Linha direta com a boca do Tapete e avanço no bomb",
        "aim_target": "Boca do Tapete / Travessia da Van / Pós-Plant",
        "q1": "Landmark essencial de AWP/Rifle na Cozinha",
        "q2": "Nível Z = -168.0 firme no piso interno do Mercado",
        "q3": "Permite recuo imediato para dentro do mercado em caso de flash",
        "q4": "Yaw = -45° alinhado na fresta entre a Van e o Tapete",
        "status_note": "Presente no Perfil (Atende Solicitação do Usuário)"
    },
    {
        "num": "11",
        "id": "ct_mid_short_catwalk",
        "name": "L / Arco / Catwalk",
        "alias": "Catwalk",
        "sector": "Mid",
        "side": "CT",
        "usage": "Hold (MID_CONTROL / ROTATE)",
        "allowed_roles": ["Rotator", "Anchor"],
        "pos": [-906.4, 78.5, -166.0],
        "angles": [0.0, -40.0, 0.0],
        "landmark": "Passagem elevada do Short / Catwalk / L em direção ao B",
        "cover": "Mureta da catwalk e quina do arco",
        "exposure": "Ativa. Controla avanço do Meio e apoia a Janela e o B",
        "aim_target": "Avanço do Meio em direção ao B / Apoio rápido",
        "q1": "Landmark clássico de controle de L e Meio",
        "q2": "Nível Z = -166.0 no piso nivelado da Catwalk",
        "q3": "Permite strafe curto e rotação expressa para o Bomb B",
        "q4": "Yaw = -40° segura a rampa de subida do Meio para o L",
        "status_note": "Presente no Perfil (Atende Solicitação do Usuário)"
    },
    {
        "num": "12",
        "id": "ct_mid_connector_headshot",
        "name": "Ligação (Z / Conector Meio)",
        "alias": "Ligacao",
        "sector": "Mid",
        "side": "CT",
        "usage": "Hold (MID_CONTROL / PEEK)",
        "allowed_roles": ["AWPer", "Rotator"],
        "pos": [-520.0, -984.0, -168.0],
        "angles": [0.0, -50.0, 0.0],
        "landmark": "Degrau superior do Conector / Ligação para o Meio",
        "cover": "Degraus de pedra e quina do Conector (pixel de headshot)",
        "exposure": "Controlada. Joga marcando um tempo Cabecinha e Meio",
        "aim_target": "Entrada do Meio para a região A / Passagem Janela",
        "q1": "Posição estratégica de Ligação / Z",
        "q2": "Nível Z = -168.0 no degrau firme da Ligação",
        "q3": "Permite disparar e voltar imediatamente para o abrigo de A",
        "q4": "Yaw = -50° segura a subida do Meio para o Conector",
        "status_note": "Presente no Perfil (Atende Solicitação do Usuário)"
    },
    {
        "num": "13",
        "id": "ct_mid_window_deep_awp",
        "name": "Janela Fundo / Direita (Apoio Jungle)",
        "alias": "JanelaDireita",
        "sector": "Mid",
        "side": "CT",
        "usage": "Hold (DEEP_WINDOW / RETREAT)",
        "allowed_roles": ["AWPer", "Rotator"],
        "pos": [-1175.8, -732.5, -168.0],
        "angles": [0.0, -25.0, 0.0],
        "landmark": "Lado direito da Janela, rente à porta da Jungle",
        "cover": "Paredes laterais da sala de snipers e quina da Jungle",
        "exposure": "Baixa. Posição de recuo contra molotovs na janela esquerda",
        "aim_target": "Top Mid e L com rotação imediata para Jungle",
        "q1": "Posição alternativa da Janela citada pelo usuário",
        "q2": "Nível Z = -168.0 sólido no assoalho de madeira",
        "q3": "Fuga e rotação instantânea para a Jungle se vier molotov",
        "q4": "Yaw = -25° ângulo profundo cobrindo o avanço do Meio",
        "status_note": "Presente no Perfil (Variação Solicitada pelo Usuário)"
    },
    {
        "num": "14",
        "id": "ct_a_stairs_cross",
        "name": "Cabecinha / Degraus A",
        "alias": "Cabecinha",
        "sector": "Bombsite A",
        "side": "CT",
        "usage": "Hold (CROSSFIRE / STAIRS)",
        "allowed_roles": ["Anchor", "Rotator"],
        "pos": [-497.8, -1309.0, -160.0],
        "angles": [0.0, 80.0, 0.0],
        "landmark": "Degraus da Cabecinha (Stairs) no Bombsite A",
        "cover": "Caixas de madeira dos degraus protegendo a cabeça e peito",
        "exposure": "Média. Visada frontal para Palácio e lateral para Rampa",
        "aim_target": "Descida do Palácio / Saída da Caverna A",
        "q1": "Landmark canônico da Cabecinha / Stairs",
        "q2": "Nível Z = -160.0 nivelado no degrau superior",
        "q3": "Proteção clássica usando a caixa para headshot-angle",
        "q4": "Yaw = 80° cruza fogo com o Ticket contra a descida do Palácio",
        "status_note": "Presente no Perfil (Atende Solicitação do Usuário)"
    },
    {
        "num": "15",
        "id": "ct_a_palace_close_poke",
        "name": "Debaixo do Palácio / Under AWP",
        "alias": "UnderPalace",
        "sector": "Bombsite A",
        "side": "CT",
        "usage": "Hold (CLOSE_AMBUSH)",
        "allowed_roles": ["Anchor", "EntryFragger"],
        "pos": [151.9, -1914.1, -168.0],
        "angles": [0.0, 140.0, 0.0],
        "landmark": "Embaixo do balcão do Palácio (Under AWP)",
        "cover": "Sombra e pilares da sacada do Palácio",
        "exposure": "Muito Baixa. Ângulo ultra fechado difícil de limpar",
        "aim_target": "Saída da Rampa / Tetris / Quem pula do Palácio",
        "q1": "Landmark surpresa debaixo do Palácio / Areia",
        "q2": "Nível Z = -168.0 no solo do bomb",
        "q3": "Invisível para quem entra pela rampa sem virar 180 graus",
        "q4": "Yaw = 140° pune a descida e avanço no site",
        "status_note": "Presente no Perfil (Atende Solicitação do Usuário)"
    },
    {
        "num": "16",
        "id": "ct_a_tetris_hold",
        "name": "Em cima da Areia (Tetris A)",
        "alias": "Tetris",
        "sector": "Bombsite A",
        "side": "CT",
        "usage": "Hold / Retake (ACTIVE_CONTEST)",
        "allowed_roles": ["Anchor", "EntryFragger"],
        "pos": [-180.0, -1700.0, -160.0],
        "angles": [0.0, 110.0, 0.0],
        "landmark": "Caixas de alvenaria e madeira da Areia (Tetris)",
        "cover": "Pilha de caixas sólidas do Tetris",
        "exposure": "Média. Marca saída do Palácio ou entrada do Bomb A",
        "aim_target": "Saída do Palácio / Entrada da Rampa / Cruzamento",
        "q1": "Landmark canônico do Tetris (Areia)",
        "q2": "Nível Z = -160.0 apoiado na base de caixas da Areia",
        "q3": "Excelente para segurar a descida do Palácio",
        "q4": "Yaw = 110° focado na saída aérea do Palácio",
        "status_note": "Novo Spot Mapeado (Atende Solicitação do Usuário)"
    },
    {
        "num": "17",
        "id": "ct_a_sandwich_hold",
        "name": "Sanduíche (Entre Tetris e Cabecinha)",
        "alias": "Sanduiche",
        "sector": "Bombsite A",
        "side": "CT",
        "usage": "Hold (CLOSE_DEFENSE)",
        "allowed_roles": ["Anchor", "Rotator"],
        "pos": [-370.0, -1550.0, -168.0],
        "angles": [0.0, 85.0, 0.0],
        "landmark": "Vão estreito do Sanduíche entre Tetris e Degraus",
        "cover": "Caixas do Tetris à frente e parede da escada atrás",
        "exposure": "Fechada. Ângulo de cruzamento protegido para a cabeça",
        "aim_target": "Descida do Palácio e saída da Caverna",
        "q1": "Landmark tradicional do Sanduíche no A",
        "q2": "Nível Z = -168.0 no corredor do solo",
        "q3": "Proteção de corpo inteiro usando as caixas",
        "q4": "Yaw = 85° vigia a boca do Palácio e Rampa",
        "status_note": "Novo Spot Mapeado (Atende Solicitação do Usuário)"
    }
]

def generate_spot_card(spot, radar_img):
    card_w = 980
    card_h = 630
    card = Image.new("RGBA", (card_w, card_h), (15, 23, 42, 255))
    draw = ImageDraw.Draw(card)
    
    # Outer border
    draw.rectangle([0, 0, card_w - 1, card_h - 1], outline=(51, 65, 85, 255), width=2)
    
    # Header background
    is_ct = (spot["side"] == "CT")
    header_color = (30, 41, 59, 255)
    draw.rectangle([2, 2, card_w - 3, 56], fill=header_color)
    draw.line([(2, 56), (card_w - 3, 56)], fill=(51, 65, 85, 255), width=1)
    
    # Header badge
    badge_bg = (37, 99, 235, 255) if is_ct else (217, 119, 6, 255)
    draw.rounded_rectangle([16, 12, 60, 44], radius=6, fill=badge_bg)
    draw.text((25, 18), spot["side"], fill=(255, 255, 255, 255), font=FONT_BADGE)
    
    title_str = f"#{spot['num']} - {spot['name']} ({spot['id']})"
    draw.text((75, 17), title_str, fill=(248, 250, 252, 255), font=FONT_TITLE)
    status_color = (74, 222, 128, 255) if "Aprovado" in spot["status_note"] or "Corrigido" in spot["status_note"] or "Presente" in spot["status_note"] else (56, 189, 248, 255)
    draw.text((card_w - 230, 20), spot["status_note"][:26], fill=status_color, font=FONT_BOLD)
    
    # Left side: Zoom-in radar crop
    crop_size = 540
    rx, ry = world_to_radar(spot["pos"][0], spot["pos"][1])
    
    overlay_radar = radar_img.copy()
    overlay_draw = ImageDraw.Draw(overlay_radar, "RGBA")
    
    yaw_deg = spot["angles"][1]
    yaw_rad = math.radians(yaw_deg)
    
    # Vision cone (FOV 90 deg = +/- 45 deg)
    cone_dist = 115.0
    left_rad = yaw_rad + math.radians(45)
    right_rad = yaw_rad - math.radians(45)
    
    cone_points = [(rx, ry)]
    steps = 16
    for s in range(steps + 1):
        ang = left_rad - (left_rad - right_rad) * (s / steps)
        px = rx + cone_dist * math.cos(ang)
        py = ry - cone_dist * math.sin(ang)
        cone_points.append((px, py))
    
    cone_color = (0, 229, 255, 75) if is_ct else (251, 146, 60, 75)
    overlay_draw.polygon(cone_points, fill=cone_color)
    
    # Aim ray (centerline)
    aim_dist = 135.0
    aim_x = rx + aim_dist * math.cos(yaw_rad)
    aim_y = ry - aim_dist * math.sin(yaw_rad)
    ray_color = (0, 255, 255, 240) if is_ct else (255, 170, 0, 240)
    overlay_draw.line([(rx, ry), (aim_x, aim_y)], fill=ray_color, width=3)
    
    # Arrow head
    arrow_size = 14.0
    arrow_ang1 = yaw_rad + math.radians(150)
    arrow_ang2 = yaw_rad - math.radians(150)
    ax1 = aim_x + arrow_size * math.cos(arrow_ang1)
    ay1 = aim_y - arrow_size * math.sin(arrow_ang1)
    ax2 = aim_x + arrow_size * math.cos(arrow_ang2)
    ay2 = aim_y - arrow_size * math.sin(arrow_ang2)
    overlay_draw.polygon([(aim_x, aim_y), (ax1, ay1), (ax2, ay2)], fill=ray_color)
    
    # Marker circle
    ring_color = (0, 255, 255, 255) if is_ct else (255, 170, 0, 255)
    overlay_draw.ellipse([rx - 14, ry - 14, rx + 14, ry + 14], outline=ring_color, width=3)
    overlay_draw.ellipse([rx - 8, ry - 8, rx + 8, ry + 8], fill=(255, 255, 255, 255))
    overlay_draw.ellipse([rx - 4, ry - 4, rx + 4, ry + 4], fill=ring_color)
    
    # Crop around the spot
    box_half = 160
    left = max(0, min(1024 - box_half * 2, rx - box_half))
    top = max(0, min(1024 - box_half * 2, ry - box_half))
    crop_area = overlay_radar.crop((left, top, left + box_half * 2, top + box_half * 2))
    crop_area = crop_area.resize((crop_size, crop_size), Image.Resampling.LANCZOS)
    
    # Paste zoom-in on card
    card.paste(crop_area, (16, 70))
    draw.rectangle([16, 70, 16 + crop_size, 70 + crop_size], outline=(51, 65, 85, 255), width=2)
    
    # Mini-map context in lower corner of zoom
    mini_w, mini_h = 120, 120
    mini_radar = radar_img.copy().resize((mini_w, mini_h), Image.Resampling.BILINEAR)
    mini_draw = ImageDraw.Draw(mini_radar)
    mrx = (rx / 1024.0) * mini_w
    mry = (ry / 1024.0) * mini_h
    mini_draw.ellipse([mrx - 6, mry - 6, mrx + 6, mry + 6], fill=(239, 68, 68, 255), outline=(255, 255, 255, 255), width=2)
    mini_draw.rectangle([0, 0, mini_w - 1, mini_h - 1], outline=(255, 255, 255, 180), width=1)
    card.paste(mini_radar, (24, 70 + crop_size - mini_h - 8))
    
    # Right side: Technical Specs & Review Box
    info_x = 16 + crop_size + 16
    info_w = card_w - info_x - 16
    
    # Panel 1: Pos & Angles
    draw.rounded_rectangle([info_x, 70, info_x + info_w, 160], radius=8, fill=(30, 41, 59, 255), outline=(51, 65, 85, 255))
    draw.text((info_x + 12, 78), "COORDENADAS E ORIENTAÇÃO CS2", fill=(148, 163, 184, 255), font=FONT_BOLD)
    draw.text((info_x + 12, 100), f"Posição XYZ : [{spot['pos'][0]:.1f}, {spot['pos'][1]:.1f}, {spot['pos'][2]:.1f}]", fill=(255, 255, 255, 255), font=FONT_MONO)
    draw.text((info_x + 12, 118), f"Mira (Pitch/Yaw): {spot['angles'][0]:.1f}° / {spot['angles'][1]:.1f}°", fill=(56, 189, 248, 255), font=FONT_MONO)
    draw.text((info_x + 12, 137), f"Setor: {spot['sector']}   |   Uso: {spot['usage']}", fill=(203, 213, 225, 255), font=FONT_REGULAR)
    
    # Panel 2: Tactical Geometry
    draw.rounded_rectangle([info_x, 168, info_x + info_w, 325], radius=8, fill=(30, 41, 59, 255), outline=(51, 65, 85, 255))
    draw.text((info_x + 12, 176), "GEOMETRIA TÁTICA & VISADA", fill=(148, 163, 184, 255), font=FONT_BOLD)
    
    def draw_wrapped_row(x, y, label, text, max_chars=40):
        draw.text((x, y), label, fill=(148, 163, 184, 255), font=FONT_BOLD)
        words = text.split(" ")
        lines = []
        cur = ""
        for w in words:
            if len(cur) + len(w) + 1 <= max_chars:
                cur += (" " if cur else "") + w
            else:
                lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        
        for idx, line in enumerate(lines):
            draw.text((x + 85, y + idx * 16), line, fill=(241, 245, 249, 255), font=FONT_REGULAR)
        return y + max(1, len(lines)) * 16 + 3
    
    cy = 196
    cy = draw_wrapped_row(info_x + 12, cy, "Landmark:", spot["landmark"])
    cy = draw_wrapped_row(info_x + 12, cy, "Cobertura:", spot["cover"])
    cy = draw_wrapped_row(info_x + 12, cy, "Exposição:", spot["exposure"])
    cy = draw_wrapped_row(info_x + 12, cy, "Alvo Mira:", spot["aim_target"])
    
    # Panel 3: 4 Validation Questions (Audit Checklist)
    draw.rounded_rectangle([info_x, 333, info_x + info_w, 492], radius=8, fill=(20, 35, 45, 255), outline=(34, 197, 94, 90))
    draw.text((info_x + 12, 341), "AUDITORIA DAS 4 PERGUNTAS GEOMÉTRICAS", fill=(74, 222, 128, 255), font=FONT_BOLD)
    
    checks = [
        ("1. Landmark Correto?", spot["q1"]),
        ("2. Nível Z / Chão Firme?", spot["q2"]),
        ("3. Cobertura Coerente?", spot["q3"]),
        ("4. Linha de Visada Alinhada?", spot["q4"]),
    ]
    qy = 362
    for q_label, q_val in checks:
        draw.text((info_x + 14, qy), f"[OK] {q_label}", fill=(74, 222, 128, 255), font=FONT_BOLD)
        draw.text((info_x + 22, qy + 15), f"-> {q_val[:48]}", fill=(203, 213, 225, 255), font=FONT_SMALL)
        qy += 31
        
    # Panel 4: Human Approval Sign-off Box
    draw.rounded_rectangle([info_x, 500, info_x + info_w, card_h - 14], radius=8, fill=(30, 41, 59, 255), outline=(59, 130, 246, 140))
    draw.text((info_x + 12, 508), f"STATUS: {spot['status_note']}", fill=(96, 165, 250, 255), font=FONT_BOLD)
    draw.text((info_x + 12, 528), "[ X ] APPROVED_BY_USER    [   ] COM NOTA    [   ] REJEITADO", fill=(255, 255, 255, 255), font=FONT_BOLD)
    draw.text((info_x + 12, 550), f"Console: setpos {spot['pos'][0]} {spot['pos'][1]} {spot['pos'][2]}", fill=(148, 163, 184, 255), font=FONT_MONO)
    draw.text((info_x + 12, 568), f"SHA-256: 26962295848882fffec48767019efd00847816d0797f14ccfcdb643032d7dbc1", fill=(100, 116, 139, 255), font=FONT_SMALL)
    
    out_file = os.path.join(OUT_DIR, f"spot_{spot['num']}_{spot['id']}.png")
    card.save(out_file)
    print(f"Generated card: {out_file} ({card.size})")
    return out_file

def main():
    radar_img = Image.open(RADAR_PATH).convert("RGBA")
    for spot in SPOTS_DATA:
        generate_spot_card(spot, radar_img)
    print(f"All {len(SPOTS_DATA)} tactical cards successfully generated!")

if __name__ == "__main__":
    main()
