import json
import math
import os
import shutil
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
)

BASE_DIR = r"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot"
DE_MIRAGE_PATH = os.path.join(BASE_DIR, "src", "CsBotManager", "MapProfiles", "de_mirage.json")
RADAR_PATH = os.path.join(BASE_DIR, "src", "arsenal_web", "static", "de_mirage_radar.png")
CARDS_DIR = os.path.join(BASE_DIR, "docs", "fase_1_7", "tactical_cards")
QUEUE_ALL_PATH = os.path.join(BASE_DIR, "docs", "spot_recording", "mirage_all_spots_queue.json")
SERVER_QUEUE_DIR = r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins\CsBotManager\docs\spot_recording"
PDF_ALL_PATH = os.path.join(BASE_DIR, "docs", "fase_1_7", "guia_campo_gravacao_todos_45_spots_mirage.pdf")
BRAIN_PDF_PATH = r"C:\Users\ricar\.gemini\antigravity\brain\d65e2bde-5cae-4311-b714-4707e256a192\guia_campo_gravacao_todos_45_spots_mirage.pdf"

os.makedirs(CARDS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(QUEUE_ALL_PATH), exist_ok=True)

# Radar calibration
POS_X = -3230.0
POS_Y = 1713.0
SCALE = 5.0

def world_to_radar(x, y):
    rx = (x - POS_X) / SCALE
    ry = (POS_Y - y) / SCALE
    return rx, ry

FONT_REGULAR = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 13)
FONT_BOLD = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 14)
FONT_TITLE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 16)
FONT_BADGE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 13)
FONT_SMALL = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 11)
FONT_MONO = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 12)

def generate_spot_card(spot, radar_img, out_path):
    card_w = 980
    card_h = 630
    card = Image.new("RGBA", (card_w, card_h), (15, 23, 42, 255))
    draw = ImageDraw.Draw(card)
    
    draw.rectangle([0, 0, card_w - 1, card_h - 1], outline=(51, 65, 85, 255), width=2)
    
    is_ct = (spot.get("side", "CT") == "CT")
    header_color = (30, 41, 59, 255)
    draw.rectangle([2, 2, card_w - 3, 56], fill=header_color)
    draw.line([(2, 56), (card_w - 3, 56)], fill=(51, 65, 85, 255), width=1)
    
    badge_bg = (37, 99, 235, 255) if is_ct else (217, 119, 6, 255)
    draw.rounded_rectangle([16, 12, 60, 44], radius=6, fill=badge_bg)
    draw.text((25, 18), spot.get("side", "CT"), fill=(255, 255, 255, 255), font=FONT_BADGE)
    
    title_str = f"#{spot['num']:02d} - {spot['name']} ({spot['id']})"
    draw.text((75, 17), title_str, fill=(248, 250, 252, 255), font=FONT_TITLE)
    draw.text((card_w - 230, 20), "Aguardando Gravação", fill=(56, 189, 248, 255), font=FONT_BOLD)
    
    crop_size = 540
    rx, ry = world_to_radar(spot["x"], spot["y"])
    
    overlay_radar = radar_img.copy()
    overlay_draw = ImageDraw.Draw(overlay_radar, "RGBA")
    
    yaw_deg = spot.get("yaw", 0.0)
    yaw_rad = math.radians(yaw_deg)
    
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
    
    aim_dist = 135.0
    aim_x = rx + aim_dist * math.cos(yaw_rad)
    aim_y = ry - aim_dist * math.sin(yaw_rad)
    ray_color = (0, 255, 255, 240) if is_ct else (255, 170, 0, 240)
    overlay_draw.line([(rx, ry), (aim_x, aim_y)], fill=ray_color, width=3)
    
    ring_color = (0, 255, 255, 255) if is_ct else (255, 170, 0, 255)
    overlay_draw.ellipse([rx - 14, ry - 14, rx + 14, ry + 14], outline=ring_color, width=3)
    overlay_draw.ellipse([rx - 8, ry - 8, rx + 8, ry + 8], fill=(255, 255, 255, 255))
    overlay_draw.ellipse([rx - 4, ry - 4, rx + 4, ry + 4], fill=ring_color)
    
    box_half = 160
    left = max(0, min(1024 - box_half * 2, rx - box_half))
    top = max(0, min(1024 - box_half * 2, ry - box_half))
    crop_area = overlay_radar.crop((left, top, left + box_half * 2, top + box_half * 2))
    crop_area = crop_area.resize((crop_size, crop_size), Image.Resampling.LANCZOS)
    
    card.paste(crop_area, (16, 70))
    draw.rectangle([16, 70, 16 + crop_size, 70 + crop_size], outline=(51, 65, 85, 255), width=2)
    
    info_x = 16 + crop_size + 16
    info_w = card_w - info_x - 16
    
    draw.rounded_rectangle([info_x, 70, info_x + info_w, 170], radius=8, fill=(30, 41, 59, 255), outline=(51, 65, 85, 255))
    draw.text((info_x + 12, 78), "COORDENADAS E ORIENTAÇÃO REFERÊNCIA", fill=(148, 163, 184, 255), font=FONT_BOLD)
    draw.text((info_x + 12, 102), f"Posição XYZ : [{spot['x']:.1f}, {spot['y']:.1f}, {spot['z']:.1f}]", fill=(255, 255, 255, 255), font=FONT_MONO)
    draw.text((info_x + 12, 122), f"Mira (Pitch/Yaw): {spot.get('pitch', 0):.1f}° / {spot.get('yaw', 0):.1f}°", fill=(56, 189, 248, 255), font=FONT_MONO)
    draw.text((info_x + 12, 142), f"Setor: {spot.get('sector', '')} | Uso: {spot.get('usage', '')}", fill=(203, 213, 225, 255), font=FONT_REGULAR)
    
    draw.rounded_rectangle([info_x, 180, info_x + info_w, 480], radius=8, fill=(30, 41, 59, 255), outline=(51, 65, 85, 255))
    draw.text((info_x + 12, 190), "INSTRUÇÕES TÁTICAS DE CAMPO", fill=(148, 163, 184, 255), font=FONT_BOLD)
    
    def draw_wrapped_row(x, y, label, text, max_chars=38):
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
        return y + max(1, len(lines)) * 16 + 5
    
    cy = 215
    desc = spot.get("description", spot.get("name", ""))
    cy = draw_wrapped_row(info_x + 12, cy, "Função:", desc)
    stance = spot.get("recommended_stance", "Standing")
    cy = draw_wrapped_row(info_x + 12, cy, "Postura:", "Agachado" if stance.lower() == "crouching" else "Em Pé")
    cy = draw_wrapped_row(info_x + 12, cy, "Foco Mira:", f"Aponte para a linha de contato do setor {spot.get('sector', '')}")
    
    draw.rounded_rectangle([info_x, 495, info_x + info_w, card_h - 14], radius=8, fill=(20, 35, 45, 255), outline=(34, 197, 94, 90))
    draw.text((info_x + 12, 508), "COMO HOMOLOGAR NO CS2:", fill=(74, 222, 128, 255), font=FONT_BOLD)
    draw.text((info_x + 12, 532), f"1. Vá até o local indicado no mapa ao lado", fill=(203, 213, 225, 255), font=FONT_REGULAR)
    draw.text((info_x + 12, 554), f"2. Adote postura {stance} e aponte para o ângulo", fill=(203, 213, 225, 255), font=FONT_REGULAR)
    draw.text((info_x + 12, 576), f"3. Digite !spot capture -> !spot aim add primary -> !spot ok", fill=(56, 189, 248, 255), font=FONT_MONO)
    draw.text((info_x + 12, 598), f"   (Ou segure V e diga 'Gravar' / aperte F8)", fill=(74, 222, 128, 255), font=FONT_BOLD)
    
    card.save(out_path)

def main():
    with open(DE_MIRAGE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    raw_spots = data.get("spots", [])
    print(f"Total spots in de_mirage.json: {len(raw_spots)}")
    
    radar_img = Image.open(RADAR_PATH).convert("RGBA")
    
    # Monta a fila com os 45 spots
    queue_items = []
    processed_spots = []
    
    for idx, s in enumerate(raw_spots, 1):
        s_copy = dict(s)
        s_copy["num"] = idx
        card_file = f"spot_{idx:02d}_{s['id']}.png"
        card_full_path = os.path.join(CARDS_DIR, card_file)
        
        # Gera o cartão se ainda não existir
        if not os.path.exists(card_full_path):
            generate_spot_card(s_copy, radar_img, card_full_path)
        
        s_copy["card_path"] = card_full_path
        processed_spots.append(s_copy)
        
        # Monta item da fila
        q_item = {
            "queue_index": idx,
            "spot_id": s["id"],
            "requested_position_role": f"{s.get('side', 'CT')} - {s.get('name', s['id'])}",
            "target_name": s.get("name", s["id"]),
            "team_side": s.get("side", "CT"),
            "sector": s.get("sector", "Bombsite A"),
            "associated_bombsite": s.get("associated_bombsite", "A"),
            "usage": s.get("usage", "Hold"),
            "allowed_roles": s.get("allowed_roles", ["Anchor", "Rotator"]),
            "recommended_stance": s.get("recommended_stance", "Standing"),
            "categories": ["STANDARD"],
            "objective": s.get("description", f"Posição de controle no setor {s.get('sector')}"),
            "required_aim_profiles": [
                {
                    "aim_profile_id": "primary",
                    "is_primary": True,
                    "priority": 1,
                    "description": f"Ângulo principal de visada para {s.get('name')}",
                    "trigger": "None"
                }
            ],
            "optional_aim_profiles": [
                {
                    "aim_profile_id": "secondary",
                    "is_primary": False,
                    "priority": 2,
                    "description": "Ângulo de checagem secundária / suporte",
                    "trigger": "EnemyContact"
                }
            ],
            "questions_for_user": [
                "A visada está livre de obstrução?",
                "A cobertura física protege contra o flanco esperado?"
            ],
            "validation_requirements": [
                "Posição finita e no solo",
                "Trace maior que 128 unidades"
            ]
        }
        queue_items.append(q_item)
    
    # Salva mirage_all_spots_queue.json
    all_queue = {
        "session_name": "mirage_all_spots",
        "map": "de_mirage",
        "version": "3.0.0",
        "description": "Fila completa com todos os 45 spots oficiais de Mirage para homologação física no CS2",
        "spots": queue_items
    }
    with open(QUEUE_ALL_PATH, "w", encoding="utf-8") as f:
        json.dump(all_queue, f, indent=2, ensure_ascii=False)
    print(f"Queue with all 45 spots saved to: {QUEUE_ALL_PATH}")
    
    # Copia para o servidor CS2
    try:
        os.makedirs(SERVER_QUEUE_DIR, exist_ok=True)
        shutil.copyfile(QUEUE_ALL_PATH, os.path.join(SERVER_QUEUE_DIR, "mirage_all_spots_queue.json"))
        print(f"Queue deployed to server: {SERVER_QUEUE_DIR}")
    except Exception as ex:
        print(f"Aviso ao copiar para servidor: {ex}")
        
    # --- GERAÇÃO DO PDF COMPLETO DE 45 PÁGINAS ---
    print("Building 45-page Field Guide PDF...")
    doc = SimpleDocTemplate(
        PDF_ALL_PATH,
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
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        alignment=1
    )
    
    spot_title = ParagraphStyle(
        'SpotTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
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
    
    # Capa / Resumo
    story.append(Paragraph("GUIA VISUAL DE CAMPO COMPLETO — TODOS OS 45 SPOTS MIRAGE", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Catálogo Completo de Mirage (Bomb A, Meio, Bomb B, Spawns, Staging e Retakes) para Validação Humana no CS2", subtitle_style))
    story.append(Spacer(1, 10))
    
    intro_data = [
        [
            Paragraph("<b>COMO EXECUTAR A HOMOLOGAÇÃO COMPLETA:</b><br/>"
                      "<b>1.</b> No CS2, inicie a fila completa digitando: <b>!spotrecord start mirage_all_spots</b><br/>"
                      "<b>2.</b> A cada spot, veja a imagem e coordenadas nesta página, caminhe até a posição no mapa e adote a postura indicada.<br/>"
                      "<b>3.</b> Aponte a mira para o ângulo principal e use <b>!spot capture</b> (ou segure <b>V</b> e diga <b>'Gravar'</b> / aperte <b>F8</b>).<br/>"
                      "<b>4.</b> Para ângulos adicionais, aponte e use <b>!spot aim add &lt;id&gt;</b>. Finalize com <b>!spot ok</b> e avance com <b>!spot next</b>!", tbl_val)
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
    
    # 45 Páginas (1 por spot)
    for i, s in enumerate(processed_spots):
        if i > 0:
            story.append(PageBreak())
        
        story.append(Paragraph(f"<b>SPOT [{s['num']:02d}/45]: {s.get('name', s['id'])}</b> ({s['id']})", spot_title))
        story.append(Paragraph(f"<b>Lado:</b> {s.get('side', 'CT')} | <b>Setor:</b> {s.get('sector', '')} | <b>Uso:</b> {s.get('usage', '')} | <b>Postura:</b> {s.get('recommended_stance', 'Standing')}", badge_style))
        story.append(Spacer(1, 6))
        
        if os.path.exists(s["card_path"]):
            img = RLImage(s["card_path"], width=7.2*inch, height=4.1*inch)
            story.append(img)
            story.append(Spacer(1, 6))
        
        stance_str = "Agachado (Crouching)" if s.get("recommended_stance", "").lower() == "crouching" else "Em Pé (Standing)"
        
        table_data = [
            [Paragraph("LOCAL NO MAPA:", tbl_label), Paragraph(f"Setor {s.get('sector')} — Posição canônica de {s.get('name')}", tbl_val_bold)],
            [Paragraph("COORDENADAS REF:", tbl_label), Paragraph(f"XYZ: [{s['x']:.1f}, {s['y']:.1f}, {s['z']:.1f}] | Yaw: {s.get('yaw', 0):.1f}° | Pitch: {s.get('pitch', 0):.1f}°", tbl_val)],
            [Paragraph("POSTURA:", tbl_label), Paragraph(stance_str, tbl_val_bold)],
            [Paragraph("FINALIDADE TÁTICA:", tbl_label), Paragraph(s.get("description", s.get("name")), tbl_val)],
            [Paragraph("ONDE MARCAR:", tbl_label), Paragraph(f"Aponte para a linha de visão esperada do adversário em direção a {s.get('sector')}", tbl_val_bold)],
            [Paragraph("COMO GRAVAR:", tbl_label), Paragraph(f"!spot capture -> !spot aim add primary -> !spot ok (ou aperte F8 / diga 'Gravar')", voice_cue_style)]
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
    print(f"45-page PDF generated successfully at: {PDF_ALL_PATH}")
    
    try:
        shutil.copyfile(PDF_ALL_PATH, BRAIN_PDF_PATH)
        print(f"Copied to Artifacts: {BRAIN_PDF_PATH}")
    except Exception as ex:
        print(f"Aviso ao copiar para artefatos: {ex}")

if __name__ == "__main__":
    main()
