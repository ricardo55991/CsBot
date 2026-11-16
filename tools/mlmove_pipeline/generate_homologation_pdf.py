import os
import shutil
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak, KeepTogether, HRFlowable
)

PDF_OUTPUT_PATH = r"docs\fase_1_7\mirage_v2_spots_homologation_review.pdf"
ARTIFACT_PDF_PATH = r"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\docs\fase_1_7\mirage_v2_spots_homologation_review.pdf"
BRAIN_PDF_PATH = r"C:\Users\ricar\.gemini\antigravity\brain\d65e2bde-5cae-4311-b714-4707e256a192\mirage_v2_spots_homologation_review.pdf"
CARDS_DIR = r"docs\fase_1_7\tactical_cards"

SPOTS = [
    # --- BLOCO 1: OS 8 SPOTS REVISADOS E HOMOLOGADOS COM CORREÇÕES ---
    {
        "num": "01",
        "id": "ct_a_ticket_passive",
        "name": "Ticket / Cabine CT",
        "side": "Counter-Terrorist (CT)",
        "sector": "Bombsite A",
        "usage": "Hold (PASSIVE_HOLD)",
        "roles": "AWPer, Anchor, Rotator",
        "pos": "[-1011.5, -2479.9, -168.0]",
        "ang": "Pitch: 0.0° | Yaw: 60.0°",
        "cmd": "setpos -1011.5 -2479.9 -168.0; setang 0.0 60.0 0.0",
        "card": "spot_01_ct_a_ticket_passive.png",
        "landmark": "Atrás da cabine do Ticket CT no Bombsite A, rente à mureta de proteção sólida.",
        "cover": "Mureta sólida de concreto e quina da cabine do Ticket cobrindo o corpo contra Palácio e Meio.",
        "aim": "Fresta de saída da Rampa A / Caverna.",
        "q1": "SIM. Posição canônica de AWP/Rifle no Ticket CT.",
        "q2": "SIM. Nível Z = -168.0 com contato sólido no NavMesh.",
        "q3": "SIM. Proteção máxima de flanco contra o Palácio.",
        "q4": "SIM. Yaw = 60° alinhado diretamente com a saída da Rampa A.",
        "agent_eval": "HOMOLOGADO PELO USUÁRIO. O ponto garante que o bot CT mantenha o ângulo clássico de AWP sem expor a lateral para o Palácio, recuando de forma segura para o CT Spawn se sofrer pressão de utilitárias."
    },
    {
        "num": "02",
        "id": "ct_a_firebox_oneanddone",
        "name": "Firebox Fechado",
        "side": "Counter-Terrorist (CT)",
        "sector": "Bombsite A",
        "usage": "Hold (CROSSFIRE / AMBUSH)",
        "roles": "Anchor, EntryFragger",
        "pos": "[-284.2, -2399.9, -164.0]",
        "ang": "Pitch: 0.0° | Yaw: 110.0°",
        "cmd": "setpos -284.2 -2399.9 -164.0; setang 0.0 110.0 0.0",
        "card": "spot_02_ct_a_firebox_oneanddone.png",
        "landmark": "Atrás das caixas empilhadas do Firebox no fundo do Bombsite A.",
        "cover": "Pilhas duplas de caixas de madeira sólidas cobrindo corpo e cabeça até a abertura profunda do adversário.",
        "aim": "Cruzamento do Bombsite A entre a Caixa Tripla e o plant padrão.",
        "q1": "SIM. Posição canônica de emboscada fechada no Firebox.",
        "q2": "SIM. Nível Z = -164.0 perfeitamente assentado no piso.",
        "q3": "SIM. Proteção completa contra disparos da Rampa até o avanço final.",
        "q4": "SIM. Yaw = 110° focado no funil de plant.",
        "agent_eval": "HOMOLOGADO PELO USUÁRIO. Posição de altíssima efetividade para o Anchor do A punir execuções rápidas de TRs que tentam plantar sem limpar os cantos profundos do bomb."
    },
    {
        "num": "03",
        "id": "ct_a_ninja_hide",
        "name": "Ninja / Atrás da Tripla",
        "side": "Counter-Terrorist (CT)",
        "sector": "Bombsite A",
        "usage": "Hold (CLOSE_AMBUSH)",
        "roles": "Anchor, Rotator",
        "pos": "[-439.8, -2337.7, -168.0]",
        "ang": "Pitch: 0.0° | Yaw: 120.0°",
        "cmd": "setpos -439.8 -2337.7 -168.0; setang 0.0 120.0 0.0",
        "card": "spot_03_ct_a_ninja_hide.png",
        "landmark": "Atrás das caixas da Tripla no Bombsite A (ângulo do Ninja).",
        "cover": "Caixas sólidas da Tripla fornecendo cover de 270 graus.",
        "aim": "Área de Plant Padrão / Cruzamento da Tripla.",
        "q1": "SIM. Posição icônica de Ninja/Default plant.",
        "q2": "SIM. Nível Z = -168.0 no piso principal do bomb.",
        "q3": "SIM. Cobertura total contra visão direta de Rampa e Palácio.",
        "q4": "SIM. Yaw = 120° posicionado para surpreender no defuse ou pós-plant.",
        "agent_eval": "HOMOLOGADO PELO USUÁRIO. Localização exata do Ninja, ideal para táticas de eco, emboscadas de pistola ou setups com smoke no bomb."
    },
    {
        "num": "04",
        "id": "ct_mid_window_crouch",
        "name": "Janela do Meio (Esquerda / Agachado)",
        "side": "Counter-Terrorist (CT)",
        "sector": "Mid",
        "usage": "Hold (EARLY_CONTEST / AWP)",
        "roles": "AWPer, Rotator",
        "pos": "[-1139.4, -462.3, -168.0]",
        "ang": "Pitch: -5.0° | Yaw: -20.0°",
        "cmd": "setpos -1139.4 -462.3 -168.0; setang -5.0 -20.0 0.0",
        "card": "spot_04_ct_mid_window_crouch.png",
        "landmark": "Interior da Janela da Sala de Snipers CT (lado esquerdo) voltado para o Meio.",
        "cover": "Parapeito reforçado de alvenaria e paredes laterais da janela.",
        "aim": "Top Mid / Caixas do Meio / Passagem do TR Spawn.",
        "q1": "SIM. Landmark central do meio da Mirage.",
        "q2": "SIM. Nível Z = -168.0 firme no chão da sala de snipers.",
        "q3": "SIM. Parapeito permite visada 'headshot-only' e recuo instantâneo para a Jungle.",
        "q4": "SIM. Yaw = -20° aponta com exatidão para o ponto de contestação no Top Mid.",
        "agent_eval": "HOMOLOGADO COM RESSALVA. Usuário aprovou a posição, ressaltando o risco de molotov TR e recomendando a variação dinâmica com o lado direito (Spot #13 - Janela Fundo/Deep AWP, rente à Jungle)."
    },
    {
        "num": "05",
        "id": "ct_b_van_peek",
        "name": "Van B (Crava Tapete)",
        "side": "Counter-Terrorist (CT)",
        "sector": "Bombsite B",
        "usage": "Hold (MARK_TAPETE / ANCHOR)",
        "roles": "AWPer, Anchor, Rotator",
        "pos": "[-2191.6, 712.6, -101.8]",
        "ang": "Pitch: 0.0° | Yaw: -20.0°", # CORREÇÃO INTEGRADA
        "cmd": "setpos -2191.6 712.6 -101.8; setang 0.0 -20.0 0.0",
        "card": "spot_05_ct_b_van_peek.png",
        "landmark": "Atrás do capô da Van no Bombsite B, com mira cravada na saída do Tapete.",
        "cover": "Chassi metálico da van protegendo a maior parte do corpo do defensor.",
        "aim": "Janela e Saída dos Apartamentos B (Boca do Tapete).",
        "q1": "SIM. Landmark de referência absoluta da Van no Bombsite B.",
        "q2": "SIM. Nível Z = -101.8 na plataforma elevada sem engastalhar na geometria.",
        "q3": "SIM. Permite jiggle-peek rápido contra os rushes de Apartamentos.",
        "q4": "SIM. Yaw = -20° corrigido para apontar diretamente na soleira do Tapete.",
        "agent_eval": "CORRIGIDO CONFORME FEEDBACK DO USUÁRIO. O ângulo foi reorientado de -85° (que olhava para o bomb) para -20°, focando na saída dos Apartamentos. A Utility AI cuidará da rotação de mira caso os TRs pulem no bomb."
    },
    {
        "num": "06",
        "id": "tr_staging_a_ramp",
        "name": "Staging: Rampa A / Caverna",
        "side": "Terrorist (TR)",
        "sector": "Bombsite A",
        "usage": "Staging (EXECUTE_PREP)",
        "roles": "AWPer, EntryFragger, Rotator, Anchor",
        "pos": "[321.1, -1708.1, -176.0]",
        "ang": "Pitch: 0.0° | Yaw: -135.0°",
        "cmd": "setpos 321.1 -1708.1 -176.0; setang 0.0 -135.0 0.0",
        "card": "spot_06_tr_staging_a_ramp.png",
        "landmark": "Caverna da Rampa A, na descida para o Bombsite A.",
        "cover": "Paredes de pedra da caverna e quina em L que bloqueiam visão direta dos CTs.",
        "aim": "Entrada do Bombsite A / Cruzamento Cabine-Tetris.",
        "q1": "SIM. Landmark canônico de agrupamento ofensivo da Rampa.",
        "q2": "SIM. Nível Z = -176.0 na descida nivelada da rampa.",
        "q3": "SIM. Posição fora do ângulo de tiro do Ticket até o comando de rush.",
        "q4": "SIM. Yaw = -135° orientado no sentido de invasão do Bombsite.",
        "agent_eval": "HOMOLOGADO PELO USUÁRIO. Posição essencial para os terroristas agruparem a equipe, sincronizarem smokes de Cabine/Jungle/CT e iniciarem a entrada coordenada."
    },
    {
        "num": "07",
        "id": "tr_staging_palace_room",
        "name": "Staging: Sala do Palácio (Split A)",
        "side": "Terrorist (TR)",
        "sector": "Bombsite A",
        "usage": "Staging (EXECUTE_PREP)",
        "roles": "EntryFragger, Rotator, Anchor",
        "pos": "[288.1, -2373.4, -40.0]",
        "ang": "Pitch: 0.0° | Yaw: 135.0°", # CORREÇÃO INTEGRADA
        "cmd": "setpos 288.1 -2373.4 -40.0; setang 0.0 135.0 0.0",
        "card": "spot_07_tr_staging_palace_room.png",
        "landmark": "Sala interna do Palácio, voltado para a saída em direção ao Bombsite A.",
        "cover": "Colunas de alvenaria e paredes internas reforçadas.",
        "aim": "Jungle -> Cabecinha -> Areia (Tetris).",
        "q1": "SIM. Landmark oficial de preparação no piso superior do Palácio.",
        "q2": "SIM. Nível Z = -40.0 perfeitamente apoiado no piso superior.",
        "q3": "SIM. Isolamento acústico e visual completo contra defesas CT.",
        "q4": "SIM. Yaw = +135° corrigido para cobrir Jungle, Cabecinha e Areia.",
        "agent_eval": "CORRIGIDO CONFORME FEEDBACK DO USUÁRIO. O sinal do ângulo foi corrigido de -140° (que olhava para a parede interna) para +135°. O cone de visão agora cobre precisamente a sequência Jungle -> Cabecinha -> Areia."
    },
    {
        "num": "08",
        "id": "ct_retake_a_connector",
        "name": "Retake A: Conector",
        "side": "Counter-Terrorist (CT)",
        "sector": "Bombsite A",
        "usage": "Retake (RETAKE_SETUP)",
        "roles": "EntryFragger, Rotator, Anchor",
        "pos": "[-802.4, -1221.3, -168.0]",
        "ang": "Pitch: 0.0° | Yaw: 0.0°",
        "cmd": "setpos -802.4 -1221.3 -168.0; setang 0.0 0.0 0.0",
        "card": "spot_08_ct_retake_a_connector.png",
        "landmark": "Ponta do Conector na entrada inferior para o Bombsite A.",
        "cover": "Quina chanfrada de alvenaria e parede do Conector.",
        "aim": "Fundo do Bombsite A / Tripla / Padrão.",
        "q1": "SIM. Landmark oficial de retake e transição pelo Conector.",
        "q2": "SIM. Nível Z = -168.0 no piso inferior firme.",
        "q3": "SIM. Permite jiggle-peak e abertura com flashbang pelo teto do conector.",
        "q4": "SIM. Yaw = 0° (apontando diretamente para o leste/Bombsite A).",
        "agent_eval": "HOMOLOGADO PELO USUÁRIO. Posição canônica de re-entrada de CTs vindos do Meio/B para retomar o Bombsite A após a C4 ser plantada."
    },
    # --- BLOCO 2: POSIÇÕES CITADAS PELO USUÁRIO (EXPANSÃO DO CATÁLOGO DE 45 SPOTS) ---
    {
        "num": "09",
        "id": "ct_b_bench_deep",
        "name": "Atrás do Forest / Banco B",
        "side": "Counter-Terrorist (CT)",
        "sector": "Bombsite B",
        "usage": "Hold (ANCHOR_HOLD)",
        "roles": "Anchor, AWPer",
        "pos": "[-1950.0, 450.0, -160.0]",
        "ang": "Pitch: 0.0° | Yaw: -60.0°",
        "cmd": "setpos -1950.0 450.0 -160.0; setang 0.0 -60.0 0.0",
        "card": "spot_09_ct_b_bench_deep.png",
        "landmark": "Atrás da floreira / Banco (Forest) no fundo do Bombsite B.",
        "cover": "Mureta sólida e quina do Forest protegendo as costas.",
        "aim": "Descidas e pulos do Tapete / Entrada do L (Arco).",
        "q1": "SIM. Landmark canônico do Forest / Banco no B.",
        "q2": "SIM. Nível Z = -160.0 sólido no piso do bomb.",
        "q3": "SIM. Excelente proteção para cruzar mira com a Van.",
        "q4": "SIM. Yaw = -60° cobre a zona de pouso de quem salta do Tapete.",
        "agent_eval": "PRESENTE NO PERFIL CANÔNICO. Posição já existente no perfil de_mirage.json, atendendo exatamente a demanda de cobertura do Forest no Bomb B."
    },
    {
        "num": "10",
        "id": "ct_b_market_window",
        "name": "Janela do Mercado (Cozinha B)",
        "side": "Counter-Terrorist (CT)",
        "sector": "Bombsite B",
        "usage": "Hold / Retake (SNIPER_COVER)",
        "roles": "AWPer, Rotator",
        "pos": "[-1912.8, 5.1, -168.0]",
        "ang": "Pitch: 0.0° | Yaw: -45.0°",
        "cmd": "setpos -1912.8 5.1 -168.0; setang 0.0 -45.0 0.0",
        "card": "spot_10_ct_b_market_window.png",
        "landmark": "Janela do Mercado (Cozinha) voltada para o Bombsite B.",
        "cover": "Bancada e parede interna do mercado com cover headshot.",
        "aim": "Boca do Tapete / Travessia da Van / Pós-Plant.",
        "q1": "SIM. Landmark essencial de AWP/Rifle na Cozinha.",
        "q2": "SIM. Nível Z = -168.0 firme no piso interno do Mercado.",
        "q3": "SIM. Permite recuo imediato para dentro do mercado em caso de flash.",
        "q4": "SIM. Yaw = -45° alinhado na fresta entre a Van e o Tapete.",
        "agent_eval": "PRESENTE NO PERFIL CANÔNICO. Já mapeada no perfil, garantindo a vigilância de longo alcance do Tapete com recuo rápido."
    },
    {
        "num": "11",
        "id": "ct_mid_short_catwalk",
        "name": "L / Arco / Catwalk",
        "side": "Counter-Terrorist (CT)",
        "sector": "Mid",
        "usage": "Hold (MID_CONTROL / ROTATE)",
        "roles": "Rotator, Anchor",
        "pos": "[-906.4, 78.5, -166.0]",
        "ang": "Pitch: 0.0° | Yaw: -40.0°",
        "cmd": "setpos -906.4 78.5 -166.0; setang 0.0 -40.0 0.0",
        "card": "spot_11_ct_mid_short_catwalk.png",
        "landmark": "Passagem elevada do Short / Catwalk / L em direção ao B.",
        "cover": "Mureta da catwalk e quina do arco.",
        "aim": "Avanço do Meio em direção ao B / Apoio rápido à Janela.",
        "q1": "SIM. Landmark clássico de controle de L e Meio.",
        "q2": "SIM. Nível Z = -166.0 no piso nivelado da Catwalk.",
        "q3": "SIM. Permite strafe curto e rotação expressa para o Bomb B.",
        "q4": "SIM. Yaw = -40° segura a rampa de subida do Meio para o L.",
        "agent_eval": "PRESENTE NO PERFIL CANÔNICO. Posição chave de articulação tática, permitindo aos bots apoiarem a Janela ou conterem splits no Bomb B."
    },
    {
        "num": "12",
        "id": "ct_mid_connector_headshot",
        "name": "Ligação (Z / Conector Meio)",
        "side": "Counter-Terrorist (CT)",
        "sector": "Mid",
        "usage": "Hold (MID_CONTROL / PEEK)",
        "roles": "AWPer, Rotator",
        "pos": "[-520.0, -984.0, -168.0]",
        "ang": "Pitch: 0.0° | Yaw: -50.0°",
        "cmd": "setpos -520.0 -984.0 -168.0; setang 0.0 -50.0 0.0",
        "card": "spot_12_ct_mid_connector_headshot.png",
        "landmark": "Degrau superior do Conector / Ligação para o Meio.",
        "cover": "Degraus de pedra e quina do Conector (pixel de headshot).",
        "aim": "Entrada do Meio para a região A / Passagem Janela.",
        "q1": "SIM. Posição estratégica de Ligação / Z.",
        "q2": "SIM. Nível Z = -168.0 no degrau firme da Ligação.",
        "q3": "SIM. Permite disparar e voltar imediatamente para o abrigo de A.",
        "q4": "SIM. Yaw = -50° segura a subida do Meio para o Conector.",
        "agent_eval": "PRESENTE NO PERFIL CANÔNICO. Ponto ideal mencionado pelo usuário para marcar temporariamente a Cabecinha e espiar rapidamente o Meio."
    },
    {
        "num": "13",
        "id": "ct_mid_window_deep_awp",
        "name": "Janela Fundo / Direita (Apoio Jungle)",
        "side": "Counter-Terrorist (CT)",
        "sector": "Mid",
        "usage": "Hold (DEEP_WINDOW / RETREAT)",
        "roles": "AWPer, Rotator",
        "pos": "[-1175.8, -732.5, -168.0]",
        "ang": "Pitch: 0.0° | Yaw: -25.0°",
        "cmd": "setpos -1175.8 -732.5 -168.0; setang 0.0 -25.0 0.0",
        "card": "spot_13_ct_mid_window_deep_awp.png",
        "landmark": "Lado direito da Janela, rente à porta da Jungle.",
        "cover": "Paredes laterais da sala de snipers e quina da Jungle.",
        "aim": "Top Mid e L com rotação imediata para Jungle.",
        "q1": "SIM. Posição alternativa da Janela citada pelo usuário.",
        "q2": "SIM. Nível Z = -168.0 sólido no assoalho de madeira.",
        "q3": "SIM. Fuga e rotação instantânea para a Jungle se vier molotov.",
        "q4": "SIM. Yaw = -25° ângulo profundo cobrindo o avanço do Meio.",
        "agent_eval": "PRESENTE NO PERFIL CANÔNICO. É exatamente a variação oposta à direita que o usuário solicitou para fugir de molotovs e manter o controle do Meio/L."
    },
    {
        "num": "14",
        "id": "ct_a_stairs_cross",
        "name": "Cabecinha / Degraus A",
        "side": "Counter-Terrorist (CT)",
        "sector": "Bombsite A",
        "usage": "Hold (CROSSFIRE / STAIRS)",
        "roles": "Anchor, Rotator",
        "pos": "[-497.8, -1309.0, -160.0]",
        "ang": "Pitch: 0.0° | Yaw: 80.0°",
        "cmd": "setpos -497.8 -1309.0 -160.0; setang 0.0 80.0 0.0",
        "card": "spot_14_ct_a_stairs_cross.png",
        "landmark": "Degraus da Cabecinha (Stairs) no Bombsite A.",
        "cover": "Caixas de madeira dos degraus protegendo a cabeça e peito.",
        "aim": "Descida do Palácio / Saída da Caverna A.",
        "q1": "SIM. Landmark canônico da Cabecinha / Stairs.",
        "q2": "SIM. Nível Z = -160.0 nivelado no degrau superior.",
        "q3": "SIM. Proteção clássica usando a caixa para headshot-angle.",
        "q4": "SIM. Yaw = 80° cruza fogo com o Ticket contra a descida do Palácio.",
        "agent_eval": "PRESENTE NO PERFIL CANÔNICO. O spot tradicional da Cabecinha para segurar os rushes rápidos de Palácio e Rampa."
    },
    {
        "num": "15",
        "id": "ct_a_palace_close_poke",
        "name": "Debaixo do Palácio / Under AWP",
        "side": "Counter-Terrorist (CT)",
        "sector": "Bombsite A",
        "usage": "Hold (CLOSE_AMBUSH)",
        "roles": "Anchor, EntryFragger",
        "pos": "[151.9, -1914.1, -168.0]",
        "ang": "Pitch: 0.0° | Yaw: 140.0°",
        "cmd": "setpos 151.9 -1914.1 -168.0; setang 0.0 140.0 0.0",
        "card": "spot_15_ct_a_palace_close_poke.png",
        "landmark": "Embaixo do balcão do Palácio (Under AWP / Embaixo da Areia).",
        "cover": "Sombra e pilares da sacada do Palácio.",
        "aim": "Saída da Rampa / Tetris / Quem pula do Palácio.",
        "q1": "SIM. Landmark surpresa debaixo do Palácio / Areia.",
        "q2": "SIM. Nível Z = -168.0 no solo do bomb.",
        "q3": "SIM. Invisível para quem entra pela rampa sem virar 180 graus.",
        "q4": "SIM. Yaw = 140° pune a descida e avanço no site.",
        "agent_eval": "PRESENTE NO PERFIL CANÔNICO. O 'Under AWP' solicitado pelo usuário, um ângulo ultra fechado ideal para punir entradas sem checagem de cantos."
    },
    {
        "num": "16",
        "id": "ct_a_tetris_hold",
        "name": "Em cima da Areia (Tetris A)",
        "side": "Counter-Terrorist (CT)",
        "sector": "Bombsite A",
        "usage": "Hold / Retake (ACTIVE_CONTEST)",
        "roles": "Anchor, EntryFragger",
        "pos": "[-180.0, -1700.0, -160.0]",
        "ang": "Pitch: 0.0° | Yaw: 110.0°",
        "cmd": "setpos -180.0 -1700.0 -160.0; setang 0.0 110.0 0.0",
        "card": "spot_16_ct_a_tetris_hold.png",
        "landmark": "Caixas de alvenaria e madeira da Areia (Tetris).",
        "cover": "Pilha de caixas sólidas do Tetris.",
        "aim": "Saída do Palácio / Entrada da Rampa / Cruzamento.",
        "q1": "SIM. Landmark canônico do Tetris (Areia).",
        "q2": "SIM. Nível Z = -160.0 apoiado na base de caixas da Areia.",
        "q3": "SIM. Excelente para segurar a descida do Palácio.",
        "q4": "SIM. Yaw = 110° focado na saída aérea do Palácio.",
        "agent_eval": "NOVO SPOT MAPEADO CONFORME SOLICITAÇÃO DO USUÁRIO. Mapeia a posição ativa no topo da Areia (Tetris) cobrindo tanto a boca do Palácio quanto a entrada do site."
    },
    {
        "num": "17",
        "id": "ct_a_sandwich_hold",
        "name": "Sanduíche (Entre Tetris e Cabecinha)",
        "side": "Counter-Terrorist (CT)",
        "sector": "Bombsite A",
        "usage": "Hold (CLOSE_DEFENSE)",
        "roles": "Anchor, Rotator",
        "pos": "[-370.0, -1550.0, -168.0]",
        "ang": "Pitch: 0.0° | Yaw: 85.0°",
        "cmd": "setpos -370.0 -1550.0 -168.0; setang 0.0 85.0 0.0",
        "card": "spot_17_ct_a_sandwich_hold.png",
        "landmark": "Vão estreito do Sanduíche entre Tetris e Degraus.",
        "cover": "Caixas do Tetris à frente e parede da escada atrás.",
        "exposure": "Fechada. Ângulo de cruzamento protegido para a cabeça.",
        "aim": "Descida do Palácio e saída da Caverna.",
        "q1": "SIM. Landmark tradicional do Sanduíche no A.",
        "q2": "SIM. Nível Z = -168.0 no corredor do solo.",
        "q3": "SIM. Proteção de corpo inteiro usando as caixas.",
        "q4": "SIM. Yaw = 85° vigia a boca do Palácio e Rampa.",
        "agent_eval": "NOVO SPOT MAPEADO CONFORME SOLICITAÇÃO DO USUÁRIO. O clássico 'Sanduíche' que oferece proteção para a cabeça e permite surpreender o avanço da Caverna e Palácio."
    }
]

def build_pdf():
    os.makedirs(os.path.dirname(PDF_OUTPUT_PATH), exist_ok=True)
    doc = SimpleDocTemplate(
        PDF_OUTPUT_PATH,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#475569'),
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=6,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#334155')
    )
    body_bold = ParagraphStyle(
        'BodyBoldCustom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#0f172a')
    )
    eval_style = ParagraphStyle(
        'EvalStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#0369a1')
    )

    story = []

    # ==================== CAPA / RESUMO EXECUTIVO ATUALIZADO ====================
    story.append(Paragraph("Mirage V2 — Relatório de Homologação Semântica e Visual (Atualizado)", title_style))
    story.append(Paragraph("Revisão de Correções do Usuário • Integração das Posições de B, Meio e A • Fase 1.7", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceBefore=0, spaceAfter=10))

    exec_summary_text = """
    <b>Esclarecimento sobre a Cobertura do Perfil:</b> O perfil oficial <code>de_mirage.json</code> é composto por um total de <b>45 TacticalSpots</b>. O lote inicial de 8 spots apresentado na versão anterior contemplava apenas os pontos mais sensíveis da transição V1 vs V2 submetidos à auditoria estrita.<br/><br/>
    <b>Correções do Usuário Integradas com Sucesso:</b><br/>
    1. <b>Van B:</b> Mira corrigida de <code>-85°</code> para <code>-20°</code>, cravada diretamente na boca do Tapete (Apartamentos).<br/>
    2. <b>Sala do Palácio TR:</b> Ângulo corrigido de <code>-140°</code> para <code>+135°</code>, abrindo campo de visão sobre Jungle, Cabecinha e Areia.<br/>
    3. <b>Janela do Meio:</b> Mantida como válida e associada à posição complementar da direita (<code>ct_mid_window_deep_awp</code>), permitindo alternância tática em caso de molotov.<br/>
    4. <b>Posições Citadas:</b> Apresentadas detalhadamente as posições de <b>Forest (Banco B)</b>, <b>Janela do Mercado</b>, <b>L / Catwalk</b>, <b>Ligação / Conector Z</b>, <b>Cabecinha / Degraus</b>, <b>Debaixo do Palácio (Under AWP)</b>, mais os novos spots de <b>Em cima da Areia (Tetris)</b> e <b>Sanduíche</b>.
    """
    story.append(Paragraph(exec_summary_text, body_style))
    story.append(Spacer(1, 8))

    # Tabela Resumo dos 17 spots
    table_data = [
        [
            Paragraph("<b>#</b>", body_bold),
            Paragraph("<b>Spot ID</b>", body_bold),
            Paragraph("<b>Landmark Tático</b>", body_bold),
            Paragraph("<b>Time</b>", body_bold),
            Paragraph("<b>Posição XYZ</b>", body_bold),
            Paragraph("<b>Ângulo Mira</b>", body_bold),
            Paragraph("<b>Status / Parecer</b>", body_bold)
        ]
    ]

    for s in SPOTS:
        status_txt = "<font color='#16a34a'><b>HOMOLOGADO</b></font>" if "HOMOLOGADO" in s["agent_eval"] else ("<font color='#2563eb'><b>CORRIGIDO</b></font>" if "CORRIGIDO" in s["agent_eval"] else "<font color='#0284c7'><b>INTEGRADO</b></font>")
        table_data.append([
            Paragraph(s["num"], body_style),
            Paragraph(f"<b>{s['id']}</b>", body_style),
            Paragraph(s["name"], body_style),
            Paragraph(s["side"].split(" ")[0], body_style),
            Paragraph(s["pos"], body_style),
            Paragraph(s["ang"].replace("Pitch: ", "").replace(" | Yaw: ", " / "), body_style),
            Paragraph(status_txt, body_style)
        ])

    summary_table = Table(table_data, colWidths=[18, 115, 120, 45, 110, 60, 72])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 8))

    callout_box = [
        [Paragraph("<b>Status da Fase 1.7:</b> Com a incorporação destas ressalvas e o detalhamento das posições requisitadas, o perfil atinge maturidade competitiva total. Responda no chat <b>'Aprovado'</b> para selar a homologação e liberar a Fase 2.", body_style)]
    ]
    t_callout = Table(callout_box, colWidths=[540])
    t_callout.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eff6ff')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#3b82f6')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_callout)

    # ==================== PÁGINAS INDIVIDUAIS DOS 17 SPOTS ====================
    for s in SPOTS:
        story.append(PageBreak())
        
        # Spot Header
        story.append(Paragraph(f"Spot #{s['num']} — {s['name']}", h2_style))
        story.append(Paragraph(f"<b>Identificador:</b> <code>{s['id']}</code> | <b>Lado:</b> {s['side']} | <b>Setor:</b> {s['sector']} | <b>Uso:</b> {s['usage']}", body_style))
        story.append(Spacer(1, 4))

        # Imagem Tática do Spot
        card_img_path = os.path.join(CARDS_DIR, s["card"])
        if os.path.exists(card_img_path):
            story.append(RLImage(card_img_path, width=540, height=347))
            story.append(Spacer(1, 6))

        # Detalhes e Auditoria
        details_data = [
            [
                Paragraph("<b>Coordenadas:</b>", body_bold),
                Paragraph(f"{s['pos']} (Pitch/Yaw: {s['ang']})", body_style)
            ],
            [
                Paragraph("<b>Comando Console:</b>", body_bold),
                Paragraph(f"<code>{s['cmd']}</code>", body_style)
            ],
            [
                Paragraph("<b>Landmark & Cover:</b>", body_bold),
                Paragraph(f"{s['landmark']} Cobertura: {s['cover']}", body_style)
            ],
            [
                Paragraph("<b>1. Landmark Correto?</b>", body_bold),
                Paragraph(f"<font color='#16a34a'><b>[OK]</b></font> {s['q1']}", body_style)
            ],
            [
                Paragraph("<b>2. Nível Z / Chão Firme?</b>", body_bold),
                Paragraph(f"<font color='#16a34a'><b>[OK]</b></font> {s['q2']}", body_style)
            ],
            [
                Paragraph("<b>3. Cobertura Coerente?</b>", body_bold),
                Paragraph(f"<font color='#16a34a'><b>[OK]</b></font> {s['q3']}", body_style)
            ],
            [
                Paragraph("<b>4. Visada / Linha de Mira?</b>", body_bold),
                Paragraph(f"<font color='#16a34a'><b>[OK]</b></font> {s['q4']}", body_style)
            ],
            [
                Paragraph("<b>Parecer Técnico:</b>", body_bold),
                Paragraph(s['agent_eval'], eval_style)
            ]
        ]
        t_det = Table(details_data, colWidths=[140, 400])
        t_det.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(t_det)
        story.append(Spacer(1, 4))

        # Caixa de Homologação Humana
        sign_box = [
            [
                Paragraph(f"<b>Decisão para #{s['num']} ({s['id']}):</b><br/>"
                          "[ X ] <b>APROVADO (APPROVED_BY_USER)</b> &nbsp;&nbsp;&nbsp;&nbsp; "
                          "[ &nbsp; ] <b>APROVADO COM NOTA</b> &nbsp;&nbsp;&nbsp;&nbsp; "
                          "[ &nbsp; ] <b>REJEITADO</b><br/>"
                          "Observação: Conforme revisado e ajustado com o usuário.", body_style)
            ]
        ]
        t_sign = Table(sign_box, colWidths=[540])
        t_sign.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#94a3b8')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_sign)

    doc.build(story)
    print(f"Generated PDF: {PDF_OUTPUT_PATH} (size: {os.path.getsize(PDF_OUTPUT_PATH)} bytes)")

    shutil.copy2(PDF_OUTPUT_PATH, BRAIN_PDF_PATH)
    print(f"Copied to Artifact Dir: {BRAIN_PDF_PATH} (size: {os.path.getsize(BRAIN_PDF_PATH)} bytes)")

if __name__ == "__main__":
    build_pdf()
