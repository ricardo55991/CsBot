import re

path = "tools/mlmove_pipeline/build_complete_automated_spots_catalog.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Substitui o início de SimpleDocTemplate e estilos em generate_catalog_pdf
old_doc_setup = """    print(f"[*] Compilando documento PDF em {PDF_PATH}...")
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )"""

new_doc_setup = """    print(f"[*] Compilando documento PDF em {PDF_PATH}...")
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=letter,
        leftMargin=24,
        rightMargin=24,
        topMargin=20,
        bottomMargin=20
    )"""

content = content.replace(old_doc_setup, new_doc_setup)

# Substitui o loop de páginas por spot
old_loop = """    # 1 Página por spot
    for spot, c_path in card_paths:
        story.append(Paragraph(f"<b>SPOT #{spot['num']:02d}: {spot['name']}</b> ({spot['group']})", styles['Heading2']))
        story.append(Spacer(1, 4))
        
        # Imagem do Cartao
        img = RLImage(c_path, width=7.2*inch, height=4.63*inch)
        story.append(img)
        story.append(Spacer(1, 8))
        
        # Tabela com dados técnicos
        tech_data = [
            ["ID Técnico", spot["id"], "Lado", spot["side"], "Setor", spot["sector"]],
            ["Coordenadas Source 2", f"[{spot['coords'][0]:.1f}, {spot['coords'][1]:.1f}, {spot['coords'][2]:.1f}]", "Postura", spot["stance"], "Cover", spot.get("cover", "Geometria oficial")],
            ["Mira Principal", f"{spot['primary_aim']['name']} (Yaw {spot['primary_aim']['yaw']:+.1f}°, Pitch {spot['primary_aim']['pitch']:+.1f}°)", "Alvo Landmark", spot['primary_aim']['target'], "Status", "GEOMETRIA SOURCE 2 HOMOLOGADA"]
        ]
        t_tech = Table(tech_data, colWidths=[1.3*inch, 1.8*inch, 0.9*inch, 1.2*inch, 0.8*inch, 1.2*inch])
        t_tech.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 7.5),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
            ('FONTNAME', (4,0), (4,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (-1,-1), (-1,-1), colors.HexColor('#16A34A')),
            ('FONTNAME', (-1,-1), (-1,-1), 'Helvetica-Bold'),
        ]))
        story.append(t_tech)
        story.append(PageBreak())"""

new_loop = """    spot_title_style = ParagraphStyle(
        'SpotTitle',
        parent=styles['Heading2'],
        fontSize=10.5,
        leading=12.5,
        textColor=colors.HexColor('#0F172A'),
        fontName='Helvetica-Bold',
        spaceAfter=2
    )
    label_3d_style = ParagraphStyle(
        'Label3D',
        parent=styles['Normal'],
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#0284C7'),
        fontName='Helvetica-Bold',
        spaceAfter=2
    )

    # 1 Página por spot com layout DUPLO: Cartão Tático 2D + Captura 3D Real In-Game
    screenshots_dir = r"docs\fase_1_7\screenshots"
    for spot, c_path in card_paths:
        story.append(Paragraph(f"<b>SPOT #{spot['num']:02d}: {spot['name']}</b> ({spot['group']})", spot_title_style))
        story.append(Spacer(1, 2))
        
        # 1. Painel Superior: Cartão Tático 2D (Radar com Ângulos e Cones)
        img_2d = RLImage(c_path, width=7.3*inch, height=3.15*inch)
        story.append(img_2d)
        story.append(Spacer(1, 3))
        
        # 2. Painel Inferior: Captura 3D In-Game Real (Source 2 DirectX 11)
        shot_path = os.path.join(screenshots_dir, f"spot_{spot['num']:02d}_{spot['id']}.jpg")
        if os.path.exists(shot_path):
            story.append(Paragraph("<b>VISÃO 3D REAL IN-GAME (CS2 SOURCE 2 ENGINE — M4A1-S / FOV 90°):</b>", label_3d_style))
            story.append(Spacer(1, 1))
            img_3d = RLImage(shot_path, width=7.3*inch, height=3.75*inch)
            story.append(img_3d)
            story.append(Spacer(1, 3))
        else:
            story.append(Spacer(1, 8))
        
        # 3. Tabela com dados técnicos ultra-compacta
        tech_data = [
            ["ID Técnico", spot["id"], "Lado", spot["side"], "Setor", spot["sector"]],
            ["Coords Source 2", f"[{spot['coords'][0]:.1f}, {spot['coords'][1]:.1f}, {spot['coords'][2]:.1f}]", "Postura", spot["stance"], "Cover", spot.get("cover", "Geometria oficial")],
            ["Mira Principal", f"{spot['primary_aim']['name']} (Yaw {spot['primary_aim']['yaw']:+.1f}°, Pitch {spot['primary_aim']['pitch']:+.1f}°)", "Alvo Landmark", spot['primary_aim']['target'], "Status", "SOURCE 2 3D HOMOLOGADO"]
        ]
        t_tech = Table(tech_data, colWidths=[1.25*inch, 1.85*inch, 0.75*inch, 1.25*inch, 0.75*inch, 1.45*inch])
        t_tech.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 6.5),
            ('LEADING', (0,0), (-1,-1), 7.8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
            ('TOPPADDING', (0,0), (-1,-1), 1.5),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
            ('FONTNAME', (4,0), (4,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (-1,-1), (-1,-1), colors.HexColor('#16A34A')),
            ('FONTNAME', (-1,-1), (-1,-1), 'Helvetica-Bold'),
        ]))
        story.append(t_tech)
        story.append(PageBreak())"""

if old_loop in content:
    content = content.replace(old_loop, new_loop)
    print("[+] Loop de páginas atualizado com sucesso!")
else:
    print("[-] Falha ao encontrar old_loop!")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("[+] Arquivo salvo com sucesso.")
