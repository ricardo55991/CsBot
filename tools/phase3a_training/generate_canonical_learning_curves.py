#!/usr/bin/env python3
"""
Fase 3A.1 - Passo 8: Geração Canônica das Curvas de Aprendizado e CSV Canônico.
Lê estritamente de metrics_train.jsonl e metrics_validation.jsonl das 3 seeds (RAW).
"""

import os
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, Rect, String, Line, PolyLine, Circle

def generate_curves():
    base_dir = Path(__file__).resolve().parents[2]
    runs_dir = base_dir / "training_runs" / "positioning_v1"
    out_csv = runs_dir / "learning_curves_canonical.csv"
    out_pdf = runs_dir / "learning_curves_canonical.pdf"

    seeds = [42026, 42027, 42028]
    all_rows = []
    seed_data = {}

    for s in seeds:
        s_dir = runs_dir / f"seed_{s}"
        train_lines = [json.loads(line) for line in open(s_dir / "metrics_train.jsonl", "r", encoding="utf-8")]
        val_lines = [json.loads(line) for line in open(s_dir / "metrics_validation.jsonl", "r", encoding="utf-8")]

        seed_data[s] = {"train": train_lines, "val": val_lines}

        for ep in range(len(train_lines)):
            t_rec = train_lines[ep]
            v_rec = val_lines[ep]

            row = {
                "seed": s,
                "epoch": t_rec["epoch"],
                "data_type": "RAW",
                "train_loss": round(t_rec["loss_total"], 4),
                "validation_loss": round(v_rec["val_loss"], 4),
                "state_macro_f1": round(v_rec["state_macro_f1"], 4),
                "state_balanced_accuracy": round(v_rec["state_balanced_accuracy"], 4),
                "sector_macro_f1": round(v_rec["sector_macro_f1"], 4),
                "spot_mrr": round(v_rec["spot_mrr"], 4),
                "spot_top1": round(v_rec["spot_top1_accuracy"], 4),
                "spot_top5": round(v_rec["spot_top5_accuracy"], 4),
                "transition_macro_f1": round(v_rec["transition_macro_f1"], 4),
                "trigger_macro_f1": round(v_rec["trigger_macro_f1"], 4),
                "composite_score": round(v_rec["composite_score"], 4)
            }
            all_rows.append(row)

    # 1. Salvar CSV Canônico
    df = pd.DataFrame(all_rows)
    df.to_csv(out_csv, index=False)
    print(f"Salvo CSV Canônico: {out_csv}")

    # 2. Gerar PDF Canônico
    doc = SimpleDocTemplate(
        str(out_pdf),
        pagesize=landscape(letter),
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
        textColor=colors.HexColor('#0F172A')
    )
    sub_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#475569')
    )
    sec_style = ParagraphStyle(
        'SecHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=8,
        spaceAfter=4
    )

    story = []
    story.append(Paragraph("Curvas de Aprendizado Canônicas (RAW) — Positioning Transformer V1", title_style))
    story.append(Paragraph(f"Dados Fatuais Extraídos Diretamente de metrics_train.jsonl e metrics_validation.jsonl • Sem Interpolação/Suavização • Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}", sub_style))
    story.append(Spacer(1, 10))

    # Desenho vetorial das curvas reais da Seed Vencedora (42027)
    v_winner = seed_data[42027]["val"]
    t_winner = seed_data[42027]["train"]

    dwg = Drawing(720, 230)
    dwg.add(Rect(0, 0, 720, 230, fillColor=colors.HexColor('#F8FAFC'), strokeColor=colors.HexColor('#CBD5E1'), strokeWidth=1, rx=6, ry=6))

    # Gráfico 1: Perdas Reais (x: 40 a 340, y: 30 a 190)
    dwg.add(String(40, 205, "Perda Multitarefa RAW (Seed Vencedora: 42027)", fontName="Helvetica-Bold", fontSize=10, fillColor=colors.HexColor('#0F172A')))
    dwg.add(Line(40, 40, 340, 40, strokeColor=colors.HexColor('#94A3B8'), strokeWidth=1))
    dwg.add(Line(40, 40, 40, 190, strokeColor=colors.HexColor('#94A3B8'), strokeWidth=1))

    # Escala Y: de 0.0 a 4.5 -> 150px
    # Épocas 1 a 6
    for ep in range(1, 7):
        x = 40 + (ep - 1) * (300 / 5)
        dwg.add(Line(x, 37, x, 40, strokeColor=colors.HexColor('#94A3B8'), strokeWidth=1))
        dwg.add(String(x - 3, 26, str(ep), fontName="Helvetica", fontSize=8, fillColor=colors.HexColor('#64748B')))
    dwg.add(String(170, 14, "Época", fontName="Helvetica-Bold", fontSize=8, fillColor=colors.HexColor('#475569')))

    pts_train = []
    pts_val = []
    for ep in range(6):
        x = 40 + ep * (300 / 5)
        y_tr = 40 + (t_winner[ep]["loss_total"] / 4.5) * 150
        y_vl = 40 + (v_winner[ep]["val_loss"] / 4.5) * 150
        pts_train.append((x, y_tr))
        pts_val.append((x, y_vl))

    dwg.add(PolyLine([coord for pt in pts_train for coord in pt], strokeColor=colors.HexColor('#2563EB'), strokeWidth=2))
    dwg.add(PolyLine([coord for pt in pts_val for coord in pt], strokeColor=colors.HexColor('#DC2626'), strokeWidth=2))
    for pt in pts_train:
        dwg.add(Circle(pt[0], pt[1], 3, fillColor=colors.HexColor('#2563EB'), strokeColor=colors.white, strokeWidth=1))
    for pt in pts_val:
        dwg.add(Circle(pt[0], pt[1], 3, fillColor=colors.HexColor('#DC2626'), strokeColor=colors.white, strokeWidth=1))

    # Legenda 1
    dwg.add(Rect(230, 185, 8, 8, fillColor=colors.HexColor('#2563EB'), strokeColor=None))
    dwg.add(String(242, 186, "Train Loss (RAW)", fontName="Helvetica", fontSize=7.5, fillColor=colors.HexColor('#1E293B')))
    dwg.add(Rect(230, 172, 8, 8, fillColor=colors.HexColor('#DC2626'), strokeColor=None))
    dwg.add(String(242, 173, "Val Loss (RAW)", fontName="Helvetica", fontSize=7.5, fillColor=colors.HexColor('#1E293B')))

    # Gráfico 2: Métricas Reais (State F1, Spot MRR, Comp Score) (x: 400 a 700)
    dwg.add(String(400, 205, "Métricas Validação RAW (Seed 42027)", fontName="Helvetica-Bold", fontSize=10, fillColor=colors.HexColor('#0F172A')))
    dwg.add(Line(400, 40, 700, 40, strokeColor=colors.HexColor('#94A3B8'), strokeWidth=1))
    dwg.add(Line(400, 40, 400, 190, strokeColor=colors.HexColor('#94A3B8'), strokeWidth=1))

    for ep in range(1, 7):
        x = 400 + (ep - 1) * (300 / 5)
        dwg.add(Line(x, 37, x, 40, strokeColor=colors.HexColor('#94A3B8'), strokeWidth=1))
        dwg.add(String(x - 3, 26, str(ep), fontName="Helvetica", fontSize=8, fillColor=colors.HexColor('#64748B')))
    dwg.add(String(530, 14, "Época", fontName="Helvetica-Bold", fontSize=8, fillColor=colors.HexColor('#475569')))

    pts_mrr = []
    pts_f1 = []
    pts_comp = []
    for ep in range(6):
        x = 400 + ep * (300 / 5)
        y_mrr = 40 + (v_winner[ep]["spot_mrr"]) * 150
        y_f1 = 40 + (v_winner[ep]["state_macro_f1"]) * 150
        y_comp = 40 + (v_winner[ep]["composite_score"]) * 150
        pts_mrr.append((x, y_mrr))
        pts_f1.append((x, y_f1))
        pts_comp.append((x, y_comp))

    dwg.add(PolyLine([coord for pt in pts_mrr for coord in pt], strokeColor=colors.HexColor('#7C3AED'), strokeWidth=2))
    dwg.add(PolyLine([coord for pt in pts_f1 for coord in pt], strokeColor=colors.HexColor('#059669'), strokeWidth=2))
    dwg.add(PolyLine([coord for pt in pts_comp for coord in pt], strokeColor=colors.HexColor('#D97706'), strokeWidth=2))

    for pt in pts_mrr:
        dwg.add(Circle(pt[0], pt[1], 3, fillColor=colors.HexColor('#7C3AED'), strokeColor=colors.white, strokeWidth=1))
    for pt in pts_f1:
        dwg.add(Circle(pt[0], pt[1], 3, fillColor=colors.HexColor('#059669'), strokeColor=colors.white, strokeWidth=1))
    for pt in pts_comp:
        dwg.add(Circle(pt[0], pt[1], 3, fillColor=colors.HexColor('#D97706'), strokeColor=colors.white, strokeWidth=1))

    # Legenda 2
    dwg.add(Rect(580, 185, 8, 8, fillColor=colors.HexColor('#7C3AED'), strokeColor=None))
    dwg.add(String(592, 186, "Spot MRR", fontName="Helvetica", fontSize=7.5, fillColor=colors.HexColor('#1E293B')))
    dwg.add(Rect(580, 172, 8, 8, fillColor=colors.HexColor('#059669'), strokeColor=None))
    dwg.add(String(592, 173, "State Macro F1", fontName="Helvetica", fontSize=7.5, fillColor=colors.HexColor('#1E293B')))
    dwg.add(Rect(580, 159, 8, 8, fillColor=colors.HexColor('#D97706'), strokeColor=None))
    dwg.add(String(592, 160, "Composite Score", fontName="Helvetica", fontSize=7.5, fillColor=colors.HexColor('#1E293B')))

    story.append(dwg)
    story.append(Spacer(1, 10))

    # Tabela com as 6 épocas da Seed Vencedora (42027)
    story.append(Paragraph("Tabela Factual Época a Época — Seed Vencedora (42027)", sec_style))
    table_data = [
        ["Época", "Train Loss", "Val Loss", "State Macro F1", "Balanced Acc", "Spot MRR", "Top-1 Acc", "Top-5 Acc", "Comp Score", "Status"]
    ]
    for ep in range(6):
        t = t_winner[ep]
        v = v_winner[ep]
        is_best = (ep == 5)
        st_label = "MELHOR MODELO" if is_best else "Treinando"
        table_data.append([
            f"{ep+1:02d}",
            f"{t['loss_total']:.4f}",
            f"{v['val_loss']:.4f}",
            f"{v['state_macro_f1']:.4f}",
            f"{v['state_balanced_accuracy']:.4f}",
            f"{v['spot_mrr']:.4f}",
            f"{v['spot_top1_accuracy']*100:.1f}%",
            f"{v['spot_top5_accuracy']*100:.1f}%",
            f"{v['composite_score']:.4f}",
            st_label
        ])

    t_rep = Table(table_data, colWidths=[40, 65, 65, 80, 75, 65, 65, 65, 75, 125])
    t_rep.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 6), (-1, 6), colors.HexColor('#DCFCE7')),
        ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, 5), [colors.white, colors.HexColor('#F8FAFC')])
    ]))
    story.append(t_rep)

    doc.build(story)
    print(f"Salvo PDF Canônico: {out_pdf}")

if __name__ == "__main__":
    generate_curves()
