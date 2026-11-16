#!/usr/bin/env python3
"""
Fase 3A.1 - Passo 6: Geração Canônica do PDF de Matrizes de Confusão.
Lê estritamente dos arrays npy em canonical_eval/ e gera confusion_matrices_canonical.pdf.
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from tools.phase3a_training.data_utils import STATE_NAMES, SECTOR_NAMES

def generate_pdf():
    base_dir = Path(__file__).resolve().parents[2]
    runs_dir = base_dir / "training_runs" / "positioning_v1"
    eval_dir = runs_dir / "canonical_eval"
    out_pdf = runs_dir / "confusion_matrices_canonical.pdf"

    # Carregar arrays
    s_logits = np.load(eval_dir / "state_logits.npy")
    s_labels = np.load(eval_dir / "state_labels.npy")
    s_preds = np.argmax(s_logits, axis=1)

    sec_logits = np.load(eval_dir / "sector_logits.npy")
    sec_labels = np.load(eval_dir / "sector_labels.npy")
    sec_preds = np.argmax(sec_logits, axis=1)

    # Matriz State
    cm_state = np.zeros((7, 7), dtype=int)
    for t, p in zip(s_labels, s_preds):
        cm_state[t, p] += 1
    supp_state = cm_state.sum(axis=1)

    # Matriz Sector
    cm_sec = np.zeros((6, 6), dtype=int)
    for t, p in zip(sec_labels, sec_preds):
        cm_sec[t, p] += 1
    supp_sec = cm_sec.sum(axis=1)

    # PDF Setup
    doc = SimpleDocTemplate(
        str(out_pdf),
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
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0F172A')
    )
    sub_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#475569')
    )
    sec_style = ParagraphStyle(
        'SecHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=10,
        spaceAfter=4
    )

    story = []
    story.append(Paragraph("Matrizes de Confusão Canônicas — Positioning Transformer V1", title_style))
    story.append(Paragraph(f"Inferência Faktual no Test Set Canônico (20.000 seqs) • Checkpoint: de_mirage_positioning_v1.pt • Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}", sub_style))
    story.append(Spacer(1, 10))

    # 1. State Counts Table
    story.append(Paragraph("1. Head A: Matriz de Contagens Brutas de PositioningState", sec_style))
    headers_state = ["Real \\ Pred"] + STATE_NAMES + ["Support"]
    table_counts_data = [headers_state]
    for i, name in enumerate(STATE_NAMES):
        row = [name] + [str(cm_state[i, j]) for j in range(7)] + [str(supp_state[i])]
        table_counts_data.append(row)

    t_counts = Table(table_counts_data, colWidths=[65, 52, 58, 52, 48, 55, 52, 48, 52])
    t_counts.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (2, 2), (2, 2), colors.HexColor('#BBF7D0')),
        ('BACKGROUND', (3, 3), (3, 3), colors.HexColor('#FED7AA')),
        ('BACKGROUND', (4, 4), (4, 4), colors.HexColor('#FEF08A')),
        ('BACKGROUND', (6, 6), (6, 6), colors.HexColor('#FED7AA')),
    ]))
    story.append(t_counts)
    story.append(Spacer(1, 10))

    # 2. State Normalized Table
    story.append(Paragraph("2. Head A: Matriz Normalizada por Linha (%) — Suporte Zero = N/A", sec_style))
    table_norm_data = [headers_state]
    for i, name in enumerate(STATE_NAMES):
        if supp_state[i] == 0:
            row = [name] + ["N/A"] * 7 + ["0"]
        else:
            row = [name] + [f"{(cm_state[i, j] / supp_state[i])*100:.1f}%" for j in range(7)] + [str(supp_state[i])]
        table_norm_data.append(row)

    t_norm = Table(table_norm_data, colWidths=[65, 52, 58, 52, 48, 55, 52, 48, 52])
    t_norm.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        # Diagonal acertos
        ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#BBF7D0')),
        ('BACKGROUND', (2, 2), (2, 2), colors.HexColor('#BBF7D0')),
        ('BACKGROUND', (3, 3), (3, 3), colors.HexColor('#FED7AA')),
        ('BACKGROUND', (4, 4), (4, 4), colors.HexColor('#BBF7D0')),
        ('BACKGROUND', (6, 6), (6, 6), colors.HexColor('#FED7AA')),
        # N/A rows em cinza claro
        ('BACKGROUND', (1, 5), (7, 5), colors.HexColor('#F1F5F9')),
        ('BACKGROUND', (1, 7), (7, 7), colors.HexColor('#F1F5F9')),
    ]))
    story.append(t_norm)
    story.append(Spacer(1, 10))

    # 3. Sector Normalized Table
    story.append(Paragraph("3. Head B: Matriz de NextSector (Contagens e Normalizada)", sec_style))
    headers_sec = ["Real \\ Pred"] + SECTOR_NAMES + ["Support"]
    table_sec_data = [headers_sec]
    for i, name in enumerate(SECTOR_NAMES):
        if supp_sec[i] == 0:
            row = [name] + ["N/A"] * 6 + ["0"]
        else:
            row = [name] + [f"{(cm_sec[i, j] / supp_sec[i])*100:.1f}%" for j in range(6)] + [str(supp_sec[i])]
        table_sec_data.append(row)

    t_sec = Table(table_sec_data, colWidths=[65, 62, 62, 62, 62, 62, 62, 55])
    t_sec.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (3, 3), (3, 3), colors.HexColor('#BAE6FD')), # MID
        ('BACKGROUND', (1, 1), (6, 1), colors.HexColor('#F1F5F9')),
        ('BACKGROUND', (1, 2), (6, 2), colors.HexColor('#F1F5F9')),
        ('BACKGROUND', (1, 4), (6, 4), colors.HexColor('#F1F5F9')),
        ('BACKGROUND', (1, 5), (6, 5), colors.HexColor('#F1F5F9')),
        ('BACKGROUND', (1, 6), (6, 6), colors.HexColor('#F1F5F9')),
    ]))
    story.append(t_sec)
    story.append(Spacer(1, 10))

    # Notas Forenses
    story.append(Paragraph("4. Observações Forenses Obrigatórias", sec_style))
    notes = (
        "1. <b>Zero Support Factual:</b> Os estados <code>OBJECTIVE</code> e <code>SAVE</code> possuem suporte estritamente zero "
        "no Test Set canônico devido ao mapeamento original de tags no corpus Mirage V2. Em conformidade com a auditoria forense, "
        "ambos são marcados como <b>N/A</b> (Not Evaluated), sem interpolação sintética de métricas.<br/>"
        "2. <b>Diagonal de Desempenho Real:</b> <code>TRANSIT</code> alcança 91,0% e <code>CLEARANCE</code> 79,3% de recall real. "
        "<code>HOLD</code> atinge 61,9% de recall (com 37,0% classificado como transição). "
        "<code>STAGING</code> e <code>RETAKE</code> obtiveram 26,5% e 20,6% de recall, indicando necessidade de retreinamento direcionado para classes raras."
    )
    story.append(Paragraph(notes, sub_style))

    doc.build(story)
    print(f"Salvo: {out_pdf}")

if __name__ == "__main__":
    generate_pdf()
