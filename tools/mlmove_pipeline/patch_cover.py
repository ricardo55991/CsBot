path = "tools/mlmove_pipeline/build_complete_automated_spots_catalog.py"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace(
    'Paragraph("Geometria Oficial Source 2 | 50 Spots de Elite | Miras Primárias e Secundárias | CsBot Engine", sub_style)',
    'Paragraph("Geometria Oficial Source 2 | 53 Spots Homologados | Esquema Tático 2D + Captura 3D Real In-Game | CsBot Engine", sub_style)'
)
c = c.replace(
    '["Novos Spots Essenciais (Domínio)", "12 spots (#39 a #50)", "Tapete B (Sofá/Cozinha), Edward, Jail, Arch B, Janela Esq., Cadeira, Escada, Tetris, Sanduíche, Default A, Rampa Staging"],',
    '["Novos Spots Essenciais & Ancoragem", "15 spots (#39 a #53)", "Sofá/Cozinha, Edward, Jail, Arch, Janela Esq, Cadeira, Escada, Tetris Top, Canto Tetris, Default A, Staging, Areia/Rampa, Conector/Rato, Areia Palácio"],'
)
c = c.replace(
    '["Total Homologado Oficial", "50 spots", "100% Alinhado à Geometria Real da Source 2 (de_mirage)"]',
    '["Total Homologado Oficial", "53 spots", "100% Geometria Source 2 Homologada com Fotos Reais In-Game"]'
)

with open(path, "w", encoding="utf-8") as f:
    f.write(c)
print("[+] Cover table updated to 53 spots!")
