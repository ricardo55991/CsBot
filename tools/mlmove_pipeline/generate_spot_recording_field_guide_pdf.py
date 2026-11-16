import os
import shutil
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
)

PDF_OUTPUT_PATH = r"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\docs\fase_1_7\guia_campo_gravacao_spots_mirage.pdf"
BRAIN_PDF_PATH = r"C:\Users\ricar\.gemini\antigravity\brain\d65e2bde-5cae-4311-b714-4707e256a192\guia_campo_gravacao_spots_mirage.pdf"
CARDS_DIR = r"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\docs\fase_1_7\tactical_cards"

SPOTS = [
    {
        "num": "01",
        "id": "ct_b_van_anchor",
        "role": "CT B — Van Anchor",
        "side": "Counter-Terrorist (CT)",
        "sector": "Bombsite B",
        "stance": "Agachado (Crouching) ou Em Pé",
        "card": "spot_05_ct_b_van_peek.png",
        "position_where": "Em cima da Van (ou colado na lataria/traseira da Van) no Bomb B.",
        "aim_target": "Fresta da saída do Tapete (Apartments Exit/Deep). A mira deve vigiar diretamente a soleira por onde os TRs saem correndo.",
        "cover_protect": "O chassi e o teto da Van protegem seu corpo contra disparos vindos do Short (L) e do Mercado enquanto você vigia o Tapete.",
        "dynamic_aims": "Mira 2 (Tapete Fundo) -> Mira 3 (Se TR cair no Bomb, virar para o centro do bomb).",
        "voice_cue": "Posicione-se na Van, aponte para o Tapete e diga 'Gravar' (ou aperte F8)."
    },
    {
        "num": "02",
        "id": "tr_staging_a_ramp_safe",
        "role": "TR A — Caverna Rampa A (Staging Seguro)",
        "side": "Terrorist (TR)",
        "sector": "Bombsite A (Rampa)",
        "stance": "Em Pé (Standing)",
        "card": "spot_06_tr_staging_a_ramp.png",
        "position_where": "Dentro da caverna/túnel da Rampa A, antes da saída aberta para o bomb.",
        "aim_target": "Abertura da Rampa em direção ao Tetris e Cabecinha. A mira fica pronta para dar pre-aim na saída.",
        "cover_protect": "Paredes sólidas da caverna cobrem 100% contra a AWP do Ticket CT e contra a Janela/Jungle.",
        "dynamic_aims": "Mira 1 (Saída da Rampa) -> Mira 2 (Topo do Tetris) -> Mira 3 (Stairs/Jungle na execução).",
        "voice_cue": "Fique dentro da caverna, aponte para a saída e diga 'Gravar' (ou aperte F8)."
    },
    {
        "num": "03",
        "id": "ct_a_jungle_connector_hold",
        "role": "CT Mid/A — Jungle Controle Conector",
        "side": "Counter-Terrorist (CT)",
        "sector": "Jungle / Meio",
        "stance": "Em Pé ou Agachado",
        "card": "spot_08_ct_retake_a_connector.png",
        "position_where": "Na Jungle, posicionado na entrada superior que dá visão para os degraus do Conector.",
        "aim_target": "Saída e subida do Conector / Top Mid. Foco total em punir TRs que tentam subir a ligação.",
        "cover_protect": "Pilar de tijolos da Jungle cobrindo a lateral direita contra a Rampa A e Palácio.",
        "dynamic_aims": "Mira 1 (Subida do Conector) -> Mira 2 (Avanço Meio para Conector) -> Mira 3 (Suporte ao Bomb A).",
        "voice_cue": "Fique na Jungle olhando o Conector e diga 'Gravar' (ou aperte F8)."
    },
    {
        "num": "04",
        "id": "ct_b_bench_deep",
        "role": "CT B — Forest / Banco Deep",
        "side": "Counter-Terrorist (CT)",
        "sector": "Bombsite B (Forest)",
        "stance": "Agachado (Crouching)",
        "card": "spot_09_ct_b_bench_deep.png",
        "position_where": "Atrás do banco de tijolos (Forest), na quina esquerda do fundo do Bomb B.",
        "aim_target": "Janela e queda do Tapete (Apartments Drop). Mira pronta para abater quem pular da janela.",
        "cover_protect": "Mureta sólida do Banco protege corpo e cabeça contra disparos frontais do Tapete até o inimigo avançar.",
        "dynamic_aims": "Mira 1 (Queda do Tapete) -> Mira 2 (Saída da Porta do Tapete) -> Mira 3 (Arco do Short).",
        "voice_cue": "Agache atrás do Banco B, mire na queda do Tapete e diga 'Gravar' (ou aperte F8)."
    },
    {
        "num": "05",
        "id": "ct_b_market_window",
        "role": "CT B — Janela do Mercado (Cozinha)",
        "side": "Counter-Terrorist (CT)",
        "sector": "Mercado / Cozinha B",
        "stance": "Agachado ou Em Pé",
        "card": "spot_10_ct_b_market_window.png",
        "position_where": "Dentro do Mercado, posicionado rente ao parapeito da janela quebrada mirando para o Bomb B.",
        "aim_target": "Saída do Tapete e região ao redor da Van. Ângulo cruzado para dar suporte ao Anchor da Van.",
        "cover_protect": "Parede da cozinha oferece recuo imediato (basta dar um passo para o lado para quebrar linha de visão).",
        "dynamic_aims": "Mira 1 (Saída do Tapete) -> Mira 2 (Van) -> Mira 3 (Entrada do Bomb / Defuse).",
        "voice_cue": "Fique na Janela do Mercado olhando o Tapete/Van e diga 'Gravar' (ou aperte F8)."
    },
    {
        "num": "06",
        "id": "ct_mid_connector_headshot",
        "role": "CT Mid — Conector Degrau Headshot",
        "side": "Counter-Terrorist (CT)",
        "sector": "Conector / Meio",
        "stance": "Agachado (Crouching)",
        "card": "spot_12_ct_mid_connector_headshot.png",
        "position_where": "Nos degraus do Conector, usando a elevação para mostrar apenas a cabeça (Headshot angle).",
        "aim_target": "Top Mid (Saída da Caverna Meio e pixel da caixa de ferro do Meio).",
        "cover_protect": "O desnível dos degraus esconde 80% do corpo, tornando o CT um alvo minúsculo para quem vem do Meio.",
        "dynamic_aims": "Mira 1 (Top Mid) -> Mira 2 (Rato / Underpass) -> Mira 3 (Suporte à Jungle).",
        "voice_cue": "Agache no degrau do Conector mostrando pixel do Meio e diga 'Gravar' (ou aperte F8)."
    },
    {
        "num": "07",
        "id": "ct_a_jungle_support",
        "role": "CT A — Jungle Suporte Central",
        "side": "Counter-Terrorist (CT)",
        "sector": "Jungle / Bomb A",
        "stance": "Em Pé (Standing)",
        "card": "spot_08_ct_retake_a_connector.png",
        "position_where": "No centro da Jungle, ligeiramente recuado com visão aberta para o Bomb A e saída do Palácio.",
        "aim_target": "Saída da varanda do Palácio (Palace Exit). Ângulo canônico para punir quem pular do Palácio.",
        "cover_protect": "Paredes laterais da Jungle protegem contra o Meio enquanto você foca na execução do Bomb A.",
        "dynamic_aims": "Mira 1 (Palácio) -> Mira 2 (Cruzamento Rampa A) -> Mira 3 (Entrada do Conector).",
        "voice_cue": "Fique no centro da Jungle mirando na saída do Palácio e diga 'Gravar' (ou aperte F8)."
    },
    {
        "num": "08",
        "id": "ct_a_stairs_palace_hold",
        "role": "CT A — Cabecinha / Stairs",
        "side": "Counter-Terrorist (CT)",
        "sector": "Bombsite A (Stairs)",
        "stance": "Agachado ou Em Pé",
        "card": "spot_14_ct_a_stairs_cross.png",
        "position_where": "No degrau superior da Cabecinha (Stairs), marcando o avanço do Bomb A.",
        "aim_target": "Fresta de queda do Palácio e avanço da Rampa A.",
        "cover_protect": "Degraus da escada dão vantagem de altura e cover contra o Meio se a Jungle estiver fechada.",
        "dynamic_aims": "Mira 1 (Palácio) -> Mira 2 (Saída Rampa A) -> Mira 3 (Conector / Meio).",
        "voice_cue": "Fique nos degraus da Cabecinha mirando no Palácio e diga 'Gravar' (ou aperte F8)."
    },
    {
        "num": "09",
        "id": "ct_a_tetris_hold",
        "role": "CT A — Areia / Tetris (Ativo)",
        "side": "Counter-Terrorist (CT)",
        "sector": "Bombsite A (Tetris)",
        "stance": "Agachado ou Em Pé",
        "card": "spot_16_ct_a_tetris_hold.png",
        "position_where": "Na Areia / Tetris, encostado nas caixas de madeira abaixo do Palácio.",
        "aim_target": "Saída da Rampa A (close combat) e queda imediata do Palácio.",
        "cover_protect": "Pilhas de caixas do Tetris fornecem cobertura contra Ticket CT e Conector, isolando duelo com a Rampa.",
        "dynamic_aims": "Mira 1 (Rampa A) -> Mira 2 (Queda Palácio) -> Mira 3 (Plant Padrão).",
        "voice_cue": "Fique no Tetris colado na caixa mirando na Rampa e diga 'Gravar' (ou aperte F8)."
    },
    {
        "num": "10",
        "id": "ct_a_sandwich_hold",
        "role": "CT A — Sanduíche",
        "side": "Counter-Terrorist (CT)",
        "sector": "Bombsite A (Sanduíche)",
        "stance": "Agachado (Crouching)",
        "card": "spot_17_ct_a_sandwich_hold.png",
        "position_where": "No vão estreito do Sanduíche (entre a rampa da Cabecinha e as caixas do Tetris).",
        "aim_target": "Saída da Rampa A e quem tentar avançar para o Default Plant.",
        "cover_protect": "Protegido em ambos os lados pela madeira do Tetris e alvenaria da Cabecinha. Totalmente invisível para o Meio.",
        "dynamic_aims": "Mira 1 (Rampa A) -> Mira 2 (Queda do Palácio) -> Mira 3 (Default Plant).",
        "voice_cue": "Agache dentro do vão do Sanduíche mirando na Rampa e diga 'Gravar' (ou aperte F8)."
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
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        alignment=1
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#475569'),
        alignment=1
    )

    spot_title = ParagraphStyle(
        'SpotTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0f172a')
    )

    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#0369a1')
    )

    tbl_label = ParagraphStyle(
        'TblLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1e293b')
    )

    tbl_val = ParagraphStyle(
        'TblVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#334155')
    )

    tbl_val_bold = ParagraphStyle(
        'TblValBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#0f172a')
    )

    voice_cue_style = ParagraphStyle(
        'VoiceCue',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#15803d')
    )

    story = []

    # --- CABEÇALHO / INSTRUÇÕES RÁPIDAS ---
    story.append(Paragraph("GUIA VISUAL DE CAMPO — GRAVAÇÃO TÁTICA MIRAGE V3", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Fila Guiada (10 Spots) com Captura Automática via Voz ('Gravar') ou Tecla F8", subtitle_style))
    story.append(Spacer(1, 10))

    intro_data = [
        [
            Paragraph("<b>COMO GRAVAR NO CS2 EM 3 SEGUNDOS SEM MEXER NO CHAT:</b><br/>"
                      "<b>1.</b> Olhe o mapa do spot abaixo para saber onde fica a posição e para onde olhar.<br/>"
                      "<b>2.</b> Vá até a posição no servidor CS2, ajuste a postura (Em Pé ou Agachado) e aponte a mira para o alvo.<br/>"
                      "<b>3.</b> <b>Segure V e diga 'Gravar'</b> (ou aperte a tecla <b>F8</b>). O jogo fará contagem de <b>2 segundos</b> na tela e registrará sozinho!<br/>"
                      "<b>4.</b> O plugin avançará automaticamente para o próximo spot da fila. Repita até o 10º!", tbl_val)
        ]
    ]
    intro_table = Table(intro_data, colWidths=[540])
    intro_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0fdf4')),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#22c55e')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(intro_table)
    story.append(Spacer(1, 10))

    # --- LISTA DOS 10 SPOTS (1 POR PÁGINA) ---
    for i, s in enumerate(SPOTS):
        if i > 0:
            story.append(PageBreak())

        # Header do Spot
        story.append(Paragraph(f"<b>SPOT [{s['num']}/10]: {s['role']}</b>", spot_title))
        story.append(Paragraph(f"<b>Lado:</b> {s['side']} | <b>Setor:</b> {s['sector']} | <b>Postura Recomendada:</b> {s['stance']}", badge_style))
        story.append(Spacer(1, 6))

        # Imagem do Cartão Tático
        card_path = os.path.join(CARDS_DIR, s['card'])
        if os.path.exists(card_path):
            img = RLImage(card_path, width=7.2*inch, height=4.1*inch)
            story.append(img)
            story.append(Spacer(1, 6))

        # Tabela com Instruções Claras
        table_data = [
            [Paragraph("ONDE FICAR:", tbl_label), Paragraph(s['position_where'], tbl_val_bold)],
            [Paragraph("POSTURA:", tbl_label), Paragraph(s['stance'], tbl_val)],
            [Paragraph("DEVE MARCAR (MIRA):", tbl_label), Paragraph(s['aim_target'], tbl_val_bold)],
            [Paragraph("DEVE SE PROTEGER (COVER):", tbl_label), Paragraph(s['cover_protect'], tbl_val)],
            [Paragraph("MIRAS DINÂMICAS:", tbl_label), Paragraph(s['dynamic_aims'], tbl_val)],
            [Paragraph("COMO GRAVAR AGORA:", tbl_label), Paragraph(s['voice_cue'], voice_cue_style)]
        ]

        info_tbl = Table(table_data, colWidths=[140, 400])
        info_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f8fafc')),
            ('BACKGROUND', (1,0), (1,-1), colors.HexColor('#ffffff')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(info_tbl)

    doc.build(story)
    print(f"PDF successfully generated at: {PDF_OUTPUT_PATH}")

    try:
        shutil.copyfile(PDF_OUTPUT_PATH, BRAIN_PDF_PATH)
        print(f"Copied to Artifacts: {BRAIN_PDF_PATH}")
    except Exception as ex:
        print(f"Aviso ao copiar para artefatos: {ex}")

if __name__ == "__main__":
    build_pdf()
