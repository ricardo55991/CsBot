import base64
import json
import os

radar_path = r"H:\CS2_AI_Server\arsenal_web\static\de_mirage_radar.png"
with open(radar_path, "rb") as f:
    radar_b64 = base64.b64encode(f.read()).decode("utf-8")

spots_data = [
    {
        "id": "ct_a_ticket_passive",
        "name": "Ticket / Cabine CT",
        "alias": "Ticket",
        "sector": "Bombsite A",
        "side": "CounterTerrorist",
        "associated_bombsite": "A",
        "usage": "Hold (PASSIVE_HOLD)",
        "allowed_roles": ["AWPer", "Anchor", "Rotator"],
        "x": -1011.5, "y": -2479.9, "z": -168.0,
        "pitch": 0.0, "yaw": 60.0,
        "landmark": "Atrás da cabine do Ticket CT no Bombsite A, rente à mureta de proteção",
        "cover": "Mureta sólida de concreto e quina da cabine do Ticket cobrindo o corpo",
        "exposure": "Baixa. Coberto contra Palácio e Meio; focado na fresta da Rampa",
        "aim_target": "Saída da Rampa A / Caverna",
        "q1": "Sim, landmark clássico de AWP/Rifle no Ticket CT.",
        "q2": "Sim, apoiado no chão firme nivelado Z = -168.0 (solo de CT Spawn).",
        "q3": "Sim, proteção total contra Palácio enquanto vigia a Rampa.",
        "q4": "Sim, Yaw = 60° aponta com precisão para a fresta de saída da Rampa A."
    },
    {
        "id": "ct_a_firebox_oneanddone",
        "name": "Firebox Fechado",
        "alias": "Firebox",
        "sector": "Bombsite A",
        "side": "CounterTerrorist",
        "associated_bombsite": "A",
        "usage": "Hold (ONE_AND_DONE)",
        "allowed_roles": ["Anchor", "EntryFragger"],
        "x": -284.2, "y": -2399.9, "z": -164.0,
        "pitch": 0.0, "yaw": 110.0,
        "landmark": "Canto fechado no fundo da Firebox, prensado entre as caixas triplas e a parede leste do site A",
        "cover": "Pilhas de caixas de madeira da Firebox à esquerda e retaguarda",
        "exposure": "Nula para Rampa/Tetris até que o ataque penetre o centro do site",
        "aim_target": "Entrada do Palácio e descida de Tetris",
        "q1": "Sim, posição clássica de emboscada no fundo das caixas da Firebox.",
        "q2": "Sim, apoiado perfeitamente no piso do site A em Z = -164.0.",
        "q3": "Sim, cobertura bilateral permitindo surpreender quem sai do Palácio.",
        "q4": "Sim, Yaw = 110° alinhado com o drop do Palácio e entrada de Tetris."
    },
    {
        "id": "ct_a_ninja_hide",
        "name": "Ninja / Atrás da Tripla",
        "alias": "Ninja",
        "sector": "Bombsite A",
        "side": "CounterTerrorist",
        "associated_bombsite": "A",
        "usage": "Hold (PASSIVE_HOLD)",
        "allowed_roles": ["Anchor", "Rotator"],
        "x": -439.8, "y": -2337.7, "z": -168.0,
        "pitch": 0.0, "yaw": 120.0,
        "landmark": "Vão estreito protegido atrás da Caixa Tripla no Bombsite A ('Ninja defuse')",
        "cover": "Caixa Tripla frontal maciça bloqueando visão direta da Rampa A",
        "exposure": "Invisível para Rampa e Stairs; vulnerável apenas para Palácio aberto",
        "aim_target": "Ponto de plant default da Caixa Default / Palácio",
        "q1": "Sim, o lendário spot 'Ninja' atrás da Caixa Tripla do Bombsite A.",
        "q2": "Sim, solo nivelado do site A em Z = -168.0.",
        "q3": "Sim, excelente cover frontal para punir plant default ou defuse furtivo.",
        "q4": "Sim, Yaw = 120° focado no perímetro de plantação e passagem Palácio-Default."
    },
    {
        "id": "ct_mid_window_crouch",
        "name": "Janela do Meio / Sniper Nest",
        "alias": "Window",
        "sector": "Mid",
        "side": "CounterTerrorist",
        "associated_bombsite": "Mid",
        "usage": "Hold (PASSIVE_HOLD)",
        "allowed_roles": ["AWPer", "Rotator"],
        "x": -1139.4, "y": -462.3, "z": -168.0,
        "pitch": -5.0, "yaw": -20.0,
        "landmark": "Bancada/parapeito central da Janela CT voltado para o Meio",
        "cover": "Muretas laterais da janela de madeira oferecendo jiggle e headglitch",
        "exposure": "Visível apenas do Top Mid / Cartola quando espreita",
        "aim_target": "Top Mid, Saída do Rato (Underpass) e Caixas de Cartola",
        "q1": "Sim, no parapeito central da Janela do Meio (Sniper Nest).",
        "q2": "Sim, apoiado no chão firme da sala em Z = -168.0 (corrige os -120 antigos flutuantes).",
        "q3": "Sim, headglitch perfeito atrás do parapeito da janela.",
        "q4": "Sim, Pitch = -5° e Yaw = -20° mirando a descida de Top Mid."
    },
    {
        "id": "ct_b_van_peek",
        "name": "Van do Bombsite B",
        "alias": "Van",
        "sector": "Bombsite B",
        "side": "CounterTerrorist",
        "associated_bombsite": "B",
        "usage": "Hold (PASSIVE_HOLD)",
        "allowed_roles": ["AWPer", "Anchor", "Rotator"],
        "x": -2191.6, "y": 712.6, "z": -101.8,
        "pitch": 0.0, "yaw": -85.0,
        "landmark": "Sobre o capô / chassi da Van no Bombsite B, rente à carcaça do veículo",
        "cover": "Carcaça e janelas da Van oferecendo obstáculo frontal contra o Tapete",
        "exposure": "Linha direta de duelo contra a janela e sacada dos Apartamentos B",
        "aim_target": "Janela do Tapete B e saída da Sacada",
        "q1": "Sim, no capô da Van vigiando a saída dos Apartamentos B.",
        "q2": "Sim, Z = -101.8 apoiado solidamente na superfície da Van.",
        "q3": "Sim, ângulo clássico de primeiro contato contra rush B.",
        "q4": "Sim, Yaw = -85° aponta diretamente para a boca dos Apartamentos B."
    },
    {
        "id": "tr_staging_a_ramp",
        "name": "Staging Rampa A / A Lobby",
        "alias": "Ramp",
        "sector": "Bombsite A",
        "side": "Terrorist",
        "associated_bombsite": "A",
        "usage": "Staging",
        "allowed_roles": ["AWPer", "EntryFragger", "Rotator", "Anchor"],
        "x": 321.1, "y": -1708.1, "z": -176.0,
        "pitch": 0.0, "yaw": -135.0,
        "landmark": "Entrada segura da Caverna/Rampa A recuada na base Terrorista",
        "cover": "Paredes sólidas da caverna à esquerda e à direita protegendo contra smokes CT",
        "exposure": "Nula contra linhas de tiro do Bombsite A até cruzar o aclive",
        "aim_target": "Corredor de avanço e subida para o Bombsite A",
        "q1": "Sim, área de agrupamento e preparação dos Terroristas para executar a Rampa A.",
        "q2": "Sim, piso sólido da base da caverna em Z = -176.0.",
        "q3": "Sim, cobertura lateral total antes do disparo da tática.",
        "q4": "Sim, Yaw = -135° orientado para a rota de entrada e aclive."
    },
    {
        "id": "tr_staging_palace_room",
        "name": "Interior da Sala do Palácio",
        "alias": "Palace",
        "sector": "Bombsite A",
        "side": "Terrorist",
        "associated_bombsite": "A",
        "usage": "Staging",
        "allowed_roles": ["EntryFragger", "Rotator", "Anchor"],
        "x": 288.1, "y": -2373.4, "z": -40.0,
        "pitch": 0.0, "yaw": -140.0,
        "landmark": "Interior do salão nobre do Palácio, atrás da coluna ornamental",
        "cover": "Colunas de pedra e paredes maciças do interior do Palácio",
        "exposure": "Seguro contra qualquer arma de longo alcance do site A",
        "aim_target": "Porta de saída para a sacada do Palácio",
        "q1": "Sim, salão do Palácio A antes da varanda.",
        "q2": "Sim, piso de madeira em Z = -40.0 (cota superior de Palácio).",
        "q3": "Sim, proteção contra granadas e spam de dentro do bombsite.",
        "q4": "Sim, Yaw = -140° direcionado para o gargalo de saída."
    },
    {
        "id": "ct_retake_a_connector",
        "name": "Boca do Conector / Retake A",
        "alias": "Retake Connector",
        "sector": "Bombsite A",
        "side": "CounterTerrorist",
        "associated_bombsite": "A",
        "usage": "Retake",
        "allowed_roles": ["EntryFragger", "Rotator", "Anchor"],
        "x": -802.4, "y": -1221.3, "z": -168.0,
        "pitch": 0.0, "yaw": 0.0,
        "landmark": "Degraus inferiores na boca de saída do Conector para o Bombsite A",
        "cover": "Paredes de alvenaria do Conector fornecendo jiggle-peek para a A",
        "exposure": "Visada cruzada para Stairs, Jungle e Default",
        "aim_target": "Caixa Default, Tripla e Rampa durante retake",
        "q1": "Sim, ponto nevrálgico de retake entre o Meio e o Bombsite A.",
        "q2": "Sim, degrau firme da escada do Conector em Z = -168.0 (corrige altura antiga).",
        "q3": "Sim, permite fatiar os ângulos de A com apoio de flashbang.",
        "q4": "Sim, Yaw = 0° apontando frontalmente para o Bombsite A."
    }
]

html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mirage V2 — Homologação Visual dos 8 Spots Sensíveis</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    .radar-container {{
      position: relative;
      width: 100%;
      max-width: 520px;
      aspect-ratio: 1/1;
      margin: 0 auto;
      border-radius: 12px;
      overflow: hidden;
      background: #111827;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    canvas {{
      width: 100%;
      height: 100%;
      display: block;
    }}
  </style>
</head>
<body class="bg-transparent text-[var(--foreground)] p-3 md:p-6 antialiased">
  <div class="max-w-4xl mx-auto bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4 md:p-6 shadow-xl space-y-6">
    
    <!-- Header -->
    <div class="border-b border-[var(--border)] pb-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
      <div>
        <div class="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-2">
          <span>🎮 CS2 Engine Radar</span>
          <span>•</span>
          <span>Fase 1.7 Homologação</span>
        </div>
        <h1 class="text-xl md:text-2xl font-bold text-[var(--foreground)] tracking-tight">Revisão Visual dos 8 Spots Sensíveis (Mirage V2)</h1>
        <p class="text-xs md:text-sm text-[var(--muted-foreground)]">Valide os landmarks, coberturas e cones de visada diretamente aqui no seu dispositivo.</p>
      </div>
      <div class="text-right">
        <span class="text-xs font-mono px-2 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-md">SHA-256: 26962295...dbc1</span>
      </div>
    </div>

    <!-- Navegação de Spots (Pills) -->
    <div>
      <label class="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)] block mb-2">Selecione o Spot para Inspecionar:</label>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2" id="spotTabsContainer">
        <!-- Injetado via JS -->
      </div>
    </div>

    <!-- Layout Grid: Radar 2D Interativo + Detalhes Táticos -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      
      <!-- Coluna Radar -->
      <div class="lg:col-span-6 space-y-3">
        <div class="radar-container shadow-inner">
          <canvas id="radarCanvas" width="1024" height="1024"></canvas>
        </div>
        <div class="flex items-center justify-between text-xs text-[var(--muted-foreground)] px-2">
          <span>Projeção Oficial CS2: Scale 5.0</span>
          <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-cyan-400 inline-block animate-pulse"></span> Posição e Cone de Visão (FOV 90°)</span>
        </div>
      </div>

      <!-- Coluna Detalhes e Validação -->
      <div class="lg:col-span-6 space-y-4">
        
        <div class="bg-[var(--background)] border border-[var(--border)] rounded-xl p-4 space-y-3">
          <div class="flex items-start justify-between gap-2">
            <div>
              <h2 id="spotTitle" class="text-lg font-bold text-[var(--foreground)]">Ticket / Cabine CT</h2>
              <span id="spotIdBadge" class="text-xs font-mono text-cyan-400">ct_a_ticket_passive</span>
            </div>
            <span id="spotSideBadge" class="px-2 py-0.5 rounded text-xs font-bold uppercase bg-blue-600/20 text-blue-400">CT</span>
          </div>

          <div class="grid grid-cols-2 gap-2 text-xs pt-1 border-t border-[var(--border)]">
            <div><span class="text-[var(--muted-foreground)]">Setor:</span> <b id="spotSector" class="text-[var(--foreground)]">Bombsite A</b></div>
            <div><span class="text-[var(--muted-foreground)]">Uso:</span> <b id="spotUsage" class="text-[var(--foreground)]">Hold</b></div>
            <div><span class="text-[var(--muted-foreground)]">Posição XYZ:</span> <b id="spotPos" class="font-mono text-[var(--foreground)]">[-1011.5, -2479.9, -168.0]</b></div>
            <div><span class="text-[var(--muted-foreground)]">Mira (Pitch/Yaw):</span> <b id="spotAng" class="font-mono text-cyan-400">0.0° / 60.0°</b></div>
          </div>

          <div class="space-y-1.5 text-xs pt-2 border-t border-[var(--border)]">
            <div><b class="text-[var(--foreground)]">Landmark:</b> <span id="spotLandmark" class="text-[var(--muted-foreground)]"></span></div>
            <div><b class="text-[var(--foreground)]">Cobertura (Cover):</b> <span id="spotCover" class="text-[var(--muted-foreground)]"></span></div>
            <div><b class="text-[var(--foreground)]">Exposição:</b> <span id="spotExposure" class="text-[var(--muted-foreground)]"></span></div>
            <div><b class="text-[var(--foreground)]">Alvo Principal da Mira:</b> <span id="spotAimTarget" class="text-cyan-400 font-medium"></span></div>
          </div>
        </div>

        <!-- 4 Perguntas de Validação Técnica -->
        <div class="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4 space-y-2 text-xs">
          <h3 class="font-bold text-blue-400 uppercase tracking-wider text-[11px]">Respostas da Auditoria Geométrica</h3>
          <ul class="space-y-1 text-[var(--muted-foreground)]">
            <li>1. Landmark correto? <b id="ansQ1" class="text-emerald-400"></b></li>
            <li>2. Chão firme Z sem flutuar? <b id="ansQ2" class="text-emerald-400"></b></li>
            <li>3. Cobertura coerente com o papel? <b id="ansQ3" class="text-emerald-400"></b></li>
            <li>4. Ângulo alinhado com a entrada? <b id="ansQ4" class="text-emerald-400"></b></li>
          </ul>
        </div>

        <!-- Botões de Decisão Humana para este spot -->
        <div class="bg-[var(--background)] border border-[var(--border)] rounded-xl p-4 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold uppercase text-[var(--muted-foreground)]">Sua Decisão para este Spot:</span>
            <span id="currentDecisionBadge" class="text-xs font-bold px-2 py-0.5 rounded bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">PENDING_HUMAN_REVIEW</span>
          </div>

          <div class="grid grid-cols-3 gap-2">
            <button onclick="setDecision('APPROVED_BY_USER')" class="px-3 py-2 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 rounded-lg text-xs font-semibold transition active:scale-95">
              ✓ Aprovar
            </button>
            <button onclick="setDecision('APPROVED_BY_USER_WITH_NOTE')" class="px-3 py-2 bg-amber-600/20 hover:bg-amber-600/30 text-amber-400 border border-amber-500/30 rounded-lg text-xs font-semibold transition active:scale-95">
              📝 Com Nota
            </button>
            <button onclick="setDecision('REJECTED_BY_USER')" class="px-3 py-2 bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 border border-rose-500/30 rounded-lg text-xs font-semibold transition active:scale-95">
              ✕ Rejeitar
            </button>
          </div>

          <div id="noteContainer" class="hidden pt-1">
            <input type="text" id="spotNoteInput" oninput="saveNote(this.value)" placeholder="Escreva sua observação aqui..." class="w-full text-xs px-3 py-2 bg-[var(--card)] border border-[var(--border)] rounded-lg text-[var(--foreground)] placeholder-[var(--placeholder)] focus:outline-none focus:border-blue-500">
          </div>
        </div>

      </div>

    </div>

    <!-- Rodapé: Gerar Checklist de Resposta Completo -->
    <div class="border-t border-[var(--border)] pt-4 flex flex-col sm:flex-row items-center justify-between gap-3">
      <div class="text-xs text-[var(--muted-foreground)]">
        Progresso da Revisão: <b id="progressCount" class="text-[var(--foreground)]">0/8 aprovados</b>
      </div>
      <button onclick="copyCompletedChecklist()" id="copyBtn" class="w-full sm:w-auto px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-blue-500/20 transition active:scale-95 flex items-center justify-center gap-2">
        <span>📋 Copiar Checklist Completo para o Chat</span>
      </button>
    </div>

  </div>

  <script>
    const spots = {json.dumps(spots_data, indent=2)};
    const radarBase64 = "data:image/png;base64,{radar_b64}";
    
    let currentIndex = 0;
    const userDecisions = {{}};
    const userNotes = {{}};

    // Inicializa decisões com PENDING_HUMAN_REVIEW
    spots.forEach(s => {{
      userDecisions[s.id] = "PENDING_HUMAN_REVIEW";
      userNotes[s.id] = "";
    }});

    const MIRAGE_PROJECTION = {{
      pos_x: -3230.0,
      pos_y: 1713.0,
      scale: 5.0
    }};

    function worldToRadar(wx, wy) {{
      return {{
        x: (wx - MIRAGE_PROJECTION.pos_x) / MIRAGE_PROJECTION.scale,
        y: (MIRAGE_PROJECTION.pos_y - wy) / MIRAGE_PROJECTION.scale
      }};
    }}

    const radarImg = new Image();
    radarImg.src = radarBase64;
    let imgLoaded = false;
    radarImg.onload = () => {{
      imgLoaded = true;
      drawRadar();
    }};

    const canvas = document.getElementById('radarCanvas');
    const ctx = canvas.getContext('2d');

    function renderTabs() {{
      const container = document.getElementById('spotTabsContainer');
      container.innerHTML = spots.map((s, idx) => {{
        const isCurrent = idx === currentIndex;
        const dec = userDecisions[s.id];
        let statusDot = 'bg-yellow-400';
        if (dec === 'APPROVED_BY_USER') statusDot = 'bg-emerald-400';
        else if (dec === 'APPROVED_BY_USER_WITH_NOTE') statusDot = 'bg-amber-400';
        else if (dec === 'REJECTED_BY_USER') statusDot = 'bg-rose-500';

        return `
          <button onclick="selectSpot(${{idx}})" class="text-left px-3 py-2 rounded-xl text-xs font-semibold border transition ${{
            isCurrent 
              ? 'bg-blue-600/15 border-blue-500 text-blue-400 shadow-sm' 
              : 'bg-[var(--card)] border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:border-slate-600'
          }}">
            <div class="flex items-center justify-between mb-0.5">
              <span class="text-[10px] text-slate-500 font-mono">#0${{idx + 1}}</span>
              <span class="w-2 h-2 rounded-full ${{statusDot}}"></span>
            </div>
            <div class="truncate font-bold text-[var(--foreground)]">${{s.alias}}</div>
          </button>
        `;
      }}).join('');
    }}

    function selectSpot(idx) {{
      currentIndex = idx;
      renderTabs();
      updateDetails();
      drawRadar();
    }}

    function updateDetails() {{
      const s = spots[currentIndex];
      document.getElementById('spotTitle').innerText = s.name;
      document.getElementById('spotIdBadge').innerText = s.id;
      document.getElementById('spotSideBadge').innerText = s.side === 'CounterTerrorist' ? 'CT' : 'TR';
      document.getElementById('spotSideBadge').className = s.side === 'CounterTerrorist' 
        ? 'px-2 py-0.5 rounded text-xs font-bold uppercase bg-blue-600/20 text-blue-400' 
        : 'px-2 py-0.5 rounded text-xs font-bold uppercase bg-amber-600/20 text-amber-400';
      
      document.getElementById('spotSector').innerText = s.sector;
      document.getElementById('spotUsage').innerText = s.usage;
      document.getElementById('spotPos').innerText = `[${{s.x}}, ${{s.y}}, ${{s.z}}]`;
      document.getElementById('spotAng').innerText = `${{s.pitch}}° / ${{s.yaw}}°`;

      document.getElementById('spotLandmark').innerText = s.landmark;
      document.getElementById('spotCover').innerText = s.cover;
      document.getElementById('spotExposure').innerText = s.exposure;
      document.getElementById('spotAimTarget').innerText = s.aim_target;

      document.getElementById('ansQ1').innerText = s.q1;
      document.getElementById('ansQ2').innerText = s.q2;
      document.getElementById('ansQ3').innerText = s.q3;
      document.getElementById('ansQ4').innerText = s.q4;

      const dec = userDecisions[s.id];
      const badge = document.getElementById('currentDecisionBadge');
      badge.innerText = dec;
      if (dec === 'APPROVED_BY_USER') {{
        badge.className = 'text-xs font-bold px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30';
      }} else if (dec === 'APPROVED_BY_USER_WITH_NOTE') {{
        badge.className = 'text-xs font-bold px-2 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-500/30';
      }} else if (dec === 'REJECTED_BY_USER') {{
        badge.className = 'text-xs font-bold px-2 py-0.5 rounded bg-rose-500/15 text-rose-400 border border-rose-500/30';
      }} else {{
        badge.className = 'text-xs font-bold px-2 py-0.5 rounded bg-yellow-500/15 text-yellow-400 border border-yellow-500/30';
      }}

      const noteBox = document.getElementById('noteContainer');
      const noteInput = document.getElementById('spotNoteInput');
      if (dec === 'APPROVED_BY_USER_WITH_NOTE' || dec === 'REJECTED_BY_USER') {{
        noteBox.classList.remove('hidden');
        noteInput.value = userNotes[s.id] || '';
      }} else {{
        noteBox.classList.add('hidden');
      }}

      updateProgress();
    }}

    function setDecision(decision) {{
      const s = spots[currentIndex];
      userDecisions[s.id] = decision;
      renderTabs();
      updateDetails();
    }}

    function saveNote(val) {{
      const s = spots[currentIndex];
      userNotes[s.id] = val;
    }}

    function updateProgress() {{
      const total = spots.length;
      const approved = Object.values(userDecisions).filter(d => d.startsWith('APPROVED')).length;
      document.getElementById('progressCount').innerText = `${{approved}}/${{total}} avaliados`;
    }}

    function drawRadar() {{
      if (!imgLoaded) return;
      ctx.clearRect(0, 0, 1024, 1024);
      ctx.drawImage(radarImg, 0, 0, 1024, 1024);

      // Desenha todos os 8 spots como pequenos pontos
      spots.forEach((s, idx) => {{
        const pt = worldToRadar(s.x, s.y);
        const isCurrent = idx === currentIndex;

        if (!isCurrent) {{
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 8, 0, Math.PI * 2);
          ctx.fillStyle = s.side === 'CounterTerrorist' ? 'rgba(59, 130, 246, 0.7)' : 'rgba(245, 158, 11, 0.7)';
          ctx.fill();
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 2;
          ctx.stroke();

          ctx.fillStyle = '#ffffff';
          ctx.font = 'bold 16px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(s.alias, pt.x, pt.y - 12);
        }}
      }});

      // Destaque do spot atual com Cone de Visão (FOV 90°) e Linha de Mira
      const cur = spots[currentIndex];
      const curPt = worldToRadar(cur.x, cur.y);
      const yawRad = -cur.yaw * (Math.PI / 180.0);
      const fovHalf = 45.0 * (Math.PI / 180.0);
      const fovRadius = 240;

      // 1. Cone de Visão (FOV)
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(curPt.x, curPt.y);
      ctx.arc(curPt.x, curPt.y, fovRadius, yawRad - fovHalf, yawRad + fovHalf);
      ctx.closePath();
      const grad = ctx.createRadialGradient(curPt.x, curPt.y, 10, curPt.x, curPt.y, fovRadius);
      grad.addColorStop(0, 'rgba(6, 182, 212, 0.45)');
      grad.addColorStop(1, 'rgba(6, 182, 212, 0.0)');
      ctx.fillStyle = grad;
      ctx.fill();
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.7)';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.restore();

      // 2. Linha de Mira Central Laser
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(curPt.x, curPt.y);
      ctx.lineTo(curPt.x + Math.cos(yawRad) * (fovRadius + 60), curPt.y + Math.sin(yawRad) * (fovRadius + 60));
      ctx.strokeStyle = '#22d3ee';
      ctx.lineWidth = 3;
      ctx.setLineDash([8, 4]);
      ctx.stroke();
      ctx.restore();

      // 3. Ponto do Bot
      ctx.beginPath();
      ctx.arc(curPt.x, curPt.y, 14, 0, Math.PI * 2);
      ctx.fillStyle = '#06b6d4';
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 4;
      ctx.stroke();

      // Rótulo destacado
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 22px sans-serif';
      ctx.textAlign = 'center';
      ctx.shadowColor = 'rgba(0,0,0,0.9)';
      ctx.shadowBlur = 8;
      ctx.fillText(`★ ${{cur.alias}} (Z=${{cur.z}})`, curPt.x, curPt.y - 20);
    }}

    function copyCompletedChecklist() {{
      const template = `Ticket:
${{userDecisions["ct_a_ticket_passive"]}}
Note: ${{userNotes["ct_a_ticket_passive"]}}

Firebox:
${{userDecisions["ct_a_firebox_oneanddone"]}}
Note: ${{userNotes["ct_a_firebox_oneanddone"]}}

Ninja:
${{userDecisions["ct_a_ninja_hide"]}}
Note: ${{userNotes["ct_a_ninja_hide"]}}

Window:
${{userDecisions["ct_mid_window_crouch"]}}
Note: ${{userNotes["ct_mid_window_crouch"]}}

Van:
${{userDecisions["ct_b_van_peek"]}}
Note: ${{userNotes["ct_b_van_peek"]}}

Ramp:
${{userDecisions["tr_staging_a_ramp"]}}
Note: ${{userNotes["tr_staging_a_ramp"]}}

Palace:
${{userDecisions["tr_staging_palace_room"]}}
Note: ${{userNotes["tr_staging_palace_room"]}}

Retake Connector:
${{userDecisions["ct_retake_a_connector"]}}
Note: ${{userNotes["ct_retake_a_connector"]}}`;

      navigator.clipboard.writeText(template).then(() => {{
        const btn = document.getElementById('copyBtn');
        const orig = btn.innerHTML;
        btn.innerHTML = '<span>✓ Copiado para a Área de Transferência!</span>';
        btn.classList.replace('bg-blue-600', 'bg-emerald-600');
        setTimeout(() => {{
          btn.innerHTML = orig;
          btn.classList.replace('bg-emerald-600', 'bg-blue-600');
        }}, 3000);
      }}).catch(() => {{
        alert(template);
      }});
    }}

    // Boot inicial
    renderTabs();
    updateDetails();
  </script>
</body>
</html>
"""

artifact_path = r"C:\Users\ricar\.gemini\antigravity\brain\d65e2bde-5cae-4311-b714-4707e256a192\mirage_visual_spot_reviewer.html"
with open(artifact_path, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"Generated standalone interactive review widget at: {artifact_path}")
print(f"Size: {os.path.getsize(artifact_path)} bytes")
