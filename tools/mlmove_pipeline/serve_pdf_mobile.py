import http.server
import socketserver
import os
import sys

PORT = 8085
DIRECTORY = r"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\docs\fase_1_7"

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Desativa agressivamente qualquer cache no navegador mobile
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        clean_path = self.path.split('?')[0]
        if clean_path in ["/", "/index.html", "/index.htm"]:
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Catálogo Mirage V3.6 (53 Spots Calibrados) - CsBot</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #0b1120;
            color: #f8fafc;
            margin: 0;
            padding: 16px 12px;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            box-sizing: border-box;
        }
        .container {
            max-width: 540px;
            width: 100%;
            background: #1e293b;
            border-radius: 16px;
            padding: 20px 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.6);
            border: 1px solid #334155;
            text-align: center;
            box-sizing: border-box;
        }
        .badge-new {
            display: inline-block;
            background: #16a34a;
            color: #ffffff;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 12px;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 10px rgba(22,163,74,0.4);
        }
        h1 {
            font-size: 21px;
            margin: 0 0 6px 0;
            color: #38bdf8;
        }
        .version-tag {
            color: #fbbf24;
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 14px;
        }
        .alert-box {
            background: #064e3b;
            border: 1px solid #10b981;
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 16px;
            font-size: 13px;
            line-height: 1.45;
            text-align: left;
            color: #a7f3d0;
        }
        .btn {
            display: block;
            width: 100%;
            padding: 15px;
            background: #2563eb;
            color: #ffffff;
            text-decoration: none;
            font-weight: bold;
            font-size: 15px;
            border-radius: 12px;
            box-shadow: 0 4px 14px rgba(37,99,235,0.4);
            margin-bottom: 10px;
            box-sizing: border-box;
        }
        .btn-green {
            background: #059669;
            box-shadow: 0 4px 14px rgba(5,150,105,0.4);
        }
        .info-card {
            background: #0f172a;
            border-radius: 10px;
            padding: 14px;
            margin-top: 14px;
            text-align: left;
            font-size: 13px;
            border: 1px solid #334155;
        }
        .preview-box {
            margin-top: 18px;
            padding-top: 14px;
            border-top: 1px solid #334155;
            text-align: left;
        }
        .preview-box h3 {
            margin: 0 0 4px 0;
            font-size: 14px;
            color: #fbbf24;
        }
        .preview-box p {
            margin: 0 0 8px 0;
            font-size: 12px;
            color: #94a3b8;
        }
        .preview-img {
            width: 100%;
            border-radius: 8px;
            border: 1px solid #475569;
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <span class="badge-new">✓ AREIA DE FATO CALIBRADA (V3.6)</span>
        <h1>Catálogo de Spots Mirage V3.6</h1>
        <div class="version-tag">Spot #53 Areia (Embaixo do Palácio [-42, -1928]) | 54 Páginas</div>
        
        <div class="alert-box">
            <b>Correção Concluída:</b> O <b>Spot #53</b> foi reposicionado exatamente no "X" vermelho que você desenhou: na <b>Areia de fato</b> (embaixo da madeira do Palácio em $[-42.0, -1928.0]$) com mira cravada na subida da Caverna ($Yaw\ +70^\circ$). O Spot #48 permanece no Canto do Tetris ($[-360, -1570]$).
        </div>
        
        <a href="/catalogo_mirage_50_spots_source2_final.pdf?nocache=v36_final" class="btn" download>
            📥 Baixar PDF Final V3.6 (54 Páginas / 10.9 MB)
        </a>
        <a href="/catalogo_mirage_50_spots_source2_final.pdf?nocache=v36_final" class="btn btn-green" target="_blank">
            👁️ Abrir PDF Diretamente no Navegador
        </a>

        <div class="info-card">
            <b style="color: #38bdf8;">Diferença Real entre os Spots de A:</b>
            <ul style="margin: 8px 0 0 0; padding-left: 18px; color: #cbd5e1; font-size: 12px; line-height: 1.6;">
                <li><b>Spot #53 (Areia de Fato):</b> $[-42.0, -1928.0, -168.0]$ (Embaixo da madeira do Palácio, mira Caverna $Yaw\ +70^\circ$)</li>
                <li><b>Spot #48 (Canto do Tetris):</b> $[-360.0, -1570.0, -168.0]$ (Fora da parede no Tetris, mira Caverna $Yaw\ -20^\circ$ e Palácio $Yaw\ -100^\circ$)</li>
                <li><b>Total de Páginas:</b> 54 páginas (Capa + 53 Spots)</li>
                <li><b>Compilação C# (CDD):</b> 291/291 testes aprovados (100%)</li>
            </ul>
        </div>

        <div class="preview-box">
            <h3>Spot #53: Areia (Embaixo do Palácio) - Marcação Subida da Caverna</h3>
            <p>Coords: [-42.0, -1928.0, -168.0] | Agachado na Areia | Mira: Subida da Caverna (Yaw +70.0°)</p>
            <img src="/tactical_cards_v3/spot_53_ct_a_sand_pit_under_palace_hold_caverna.png?nocache=v36" class="preview-img" alt="Spot 53 Areia Real">
        </div>

        <div class="preview-box">
            <h3>Spot #48: Canto do Tetris - Marcação Caverna & Palácio</h3>
            <p>Coords: [-360.0, -1570.0, -168.0] | Agachado no Canto do Tetris | Mira: Caverna (Yaw -20.0°)</p>
            <img src="/tactical_cards_v3/spot_48_a_tetris_corner_ramp_palace.png?nocache=v36" class="preview-img" alt="Spot 48 Tetris">
        </div>

        <div class="preview-box">
            <h3>Spot #06: Em Cima da Van - Marcação Saída do Tapete</h3>
            <p>Coords: [-2280.0, 710.0, -38.0] | Em pé sobre a Van | Mira: Saída Tapete (Yaw +5.0°)</p>
            <img src="/tactical_cards_v3/spot_06_b_van_behind_apps_hold.png?nocache=v36" class="preview-img" alt="Spot 06 Van">
        </div>
    </div>
</body>
</html>
"""
            self.wfile.write(html.encode("utf-8"))
        else:
            self.path = clean_path
            return super().do_GET()

if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", PORT), CustomHandler) as httpd:
        print(f"Servidor HTTP ativo em http://0.0.0.0:{PORT}")
        httpd.serve_forever()
