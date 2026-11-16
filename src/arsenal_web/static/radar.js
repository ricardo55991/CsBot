/**
 * ==============================================================================
 * CsBot Tactical Radar 2D & Operations Center (TOC) Engine
 * Renderizador de alta performance via HTML5 Canvas + WebSocket 20Hz
 * ==============================================================================
 */

(() => {
    'use strict';

    // 1. Constantes de Projeção Oficial de de_mirage (CS2 Source 2)
    const MIRAGE_PROJECTION = {
        pos_x: -3230.0,
        pos_y: 1713.0,
        scale: 5.0
    };

    // 2. Principais Spots Táticos e Callouts da Mirage (para exibição no radar)
    const MIRAGE_CALLOUTS = [
        { name: "BOMBSITE A", x: -1090, y: -430, type: "site" },
        { name: "BOMBSITE B", x: -1780, y: 505, type: "site" },
        { name: "Ticket / CT", x: -1011, y: -2480, type: "ct" },
        { name: "Jungle", x: -500, y: -1400, type: "mid" },
        { name: "Conector", x: -820, y: -840, type: "mid" },
        { name: "Janela (Window)", x: -1380, y: -540, type: "mid" },
        { name: "Varanda / Short", x: -950, y: -1050, type: "mid" },
        { name: "Underpass (Rato)", x: -720, y: -1020, type: "mid" },
        { name: "Top Mid", x: -1500, y: -1300, type: "mid" },
        { name: "Palácio", x: -350, y: -480, type: "a" },
        { name: "Rampa A", x: -250, y: -200, type: "a" },
        { name: "Van", x: -1800, y: 700, type: "b" },
        { name: "Apartamentos B", x: -650, y: 650, type: "b" },
        { name: "Mercado", x: -1700, y: -200, type: "b" },
        { name: "Banco", x: -1300, y: 900, type: "b" },
        { name: "Base CT", x: -1800, y: -2200, type: "base" },
        { name: "Base TR", x: 800, y: -150, type: "base" }
    ];

    // 3. Estado Global do Radar
    const state = {
        ws: null,
        wsConnected: false,
        telemetry: null,
        interpolatedPlayers: new Map(), // slot -> { x, y, yaw, hp, targetX, targetY, targetYaw }
        radarImage: new Image(),
        radarLoaded: false,
        lastFrameTime: performance.now(),
        pulsePhase: 0,
        options: {
            showCallouts: true,
            showFov: true
        }
    };

    // 4. Elementos DOM
    const DOM = {
        canvas: document.getElementById('radarCanvas'),
        ctx: null,
        mapNameText: document.getElementById('mapNameText'),
        tickrateText: document.getElementById('tickrateText'),
        toggleCallouts: document.getElementById('toggleCallouts'),
        toggleFov: document.getElementById('toggleFov'),
        btnFullscreen: document.getElementById('btnFullscreen'),
        c4Banner: document.getElementById('c4Banner'),
        c4Title: document.getElementById('c4Title'),
        c4Timer: document.getElementById('c4Timer'),
        c4DefuseBar: document.getElementById('c4DefuseBar'),
        defuseProgress: document.getElementById('defuseProgress'),
        ctScore: document.getElementById('ctScore'),
        trScore: document.getElementById('trScore'),
        roundBadge: document.getElementById('roundBadge'),
        phaseBadge: document.getElementById('phaseBadge'),
        buyStatePill: document.getElementById('buyStatePill'),
        teamCashText: document.getElementById('teamCashText'),
        tacticName: document.getElementById('tacticName'),
        tacticSummary: document.getElementById('tacticSummary'),
        tempoPill: document.getElementById('tempoPill'),
        tierPill: document.getElementById('tierPill'),
        stagingTimerPill: document.getElementById('stagingTimerPill'),
        alertsContainer: document.getElementById('alertsContainer'),
        voiceCmdText: document.getElementById('voiceCmdText'),
        voiceActionText: document.getElementById('voiceActionText'),
        rosterCount: document.getElementById('rosterCount'),
        rosterList: document.getElementById('rosterList'),
        btnExecute: document.getElementById('btnExecute'),
        btnRotate: document.getElementById('btnRotate'),
        btnFlash: document.getElementById('btnFlash'),
        btnPause: document.getElementById('btnPause')
    };

    if (DOM.canvas) {
        DOM.ctx = DOM.canvas.getContext('2d');
    }

    // 5. Conversão Matemática: CS2 World -> Radar Canvas 1024x1024
    function worldToRadar(worldX, worldY) {
        const rx = (worldX - MIRAGE_PROJECTION.pos_x) / MIRAGE_PROJECTION.scale;
        const ry = (MIRAGE_PROJECTION.pos_y - worldY) / MIRAGE_PROJECTION.scale;
        return { x: rx, y: ry };
    }

    // Normaliza ângulo com o menor delta circular (-PI a +PI)
    function lerpAngle(fromRad, toRad, t) {
        let diff = (toRad - fromRad) % (Math.PI * 2);
        if (diff < -Math.PI) diff += Math.PI * 2;
        if (diff > Math.PI) diff -= Math.PI * 2;
        return fromRad + diff * t;
    }

    // 6. Atualização e Interpolação de Jogadores a 60 FPS
    function updateInterpolation(deltaTime) {
        if (!state.telemetry || !state.telemetry.players) return;

        const lerpFactor = Math.min(1.0, deltaTime * 12.0); // Convergência suave (~0.2 a 0.35)

        const currentSlots = new Set();
        state.telemetry.players.forEach(p => {
            currentSlots.add(p.slot);
            const radarPos = worldToRadar(p.x, p.y);
            const targetYawRad = -p.yaw * (Math.PI / 180.0);

            if (!state.interpolatedPlayers.has(p.slot)) {
                state.interpolatedPlayers.set(p.slot, {
                    x: radarPos.x,
                    y: radarPos.y,
                    yawRad: targetYawRad,
                    hp: p.hp,
                    dto: p
                });
            } else {
                const interp = state.interpolatedPlayers.get(p.slot);
                interp.x += (radarPos.x - interp.x) * lerpFactor;
                interp.y += (radarPos.y - interp.y) * lerpFactor;
                interp.yawRad = lerpAngle(interp.yawRad, targetYawRad, lerpFactor);
                interp.hp += (p.hp - interp.hp) * lerpFactor;
                interp.dto = p;
            }
        });

        // Limpa slots desconectados
        for (const slot of state.interpolatedPlayers.keys()) {
            if (!currentSlots.has(slot)) {
                state.interpolatedPlayers.delete(slot);
            }
        }
    }

    // 7. Loop de Desenho do Canvas (60 FPS)
    function render(currentTime) {
        const deltaTime = (currentTime - state.lastFrameTime) / 1000.0;
        state.lastFrameTime = currentTime;
        state.pulsePhase = (currentTime / 300.0) % (Math.PI * 2);

        updateInterpolation(deltaTime);

        const ctx = DOM.ctx;
        if (!ctx) {
            requestAnimationFrame(render);
            return;
        }

        ctx.clearRect(0, 0, 1024, 1024);

        // 7.1 Fundo: Mapa Oficial Radar da Mirage
        if (state.radarLoaded) {
            ctx.drawImage(state.radarImage, 0, 0, 1024, 1024);
        } else {
            ctx.fillStyle = "#0c131d";
            ctx.fillRect(0, 0, 1024, 1024);
            ctx.fillStyle = "#388bfd";
            ctx.font = "bold 20px 'JetBrains Mono'";
            ctx.textAlign = "center";
            ctx.fillText("CARREGANDO RADAR DE_MIRAGE...", 512, 512);
        }

        // Vinheta sutil e linhas táticas
        drawRadarOverlay(ctx);

        // 7.2 Callouts / Spots Táticos (se ativado)
        if (state.options.showCallouts) {
            drawCallouts(ctx);
        }

        // 7.3 Bomba C4 (Plantada ou no Chão)
        drawC4(ctx);

        // 7.4 Jogadores e Cones de Visão
        drawPlayers(ctx);

        requestAnimationFrame(render);
    }

    // Camada decorativa de overlay tático
    function drawRadarOverlay(ctx) {
        const grad = ctx.createRadialGradient(512, 512, 380, 512, 512, 600);
        grad.addColorStop(0, "rgba(7, 9, 13, 0)");
        grad.addColorStop(1, "rgba(7, 9, 13, 0.55)");
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, 1024, 1024);
    }

    // Desenha Callouts e Nomes das Áreas
    function drawCallouts(ctx) {
        ctx.save();
        ctx.font = "bold 11px 'Inter', sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        MIRAGE_CALLOUTS.forEach(callout => {
            const pos = worldToRadar(callout.x, callout.y);
            
            // Fundo da etiqueta
            const textWidth = ctx.measureText(callout.name).width;
            const padX = 6;
            const padY = 3;

            let bgColor = "rgba(13, 17, 23, 0.75)";
            let textColor = "#8b949e";
            let borderColor = "rgba(255, 255, 255, 0.1)";

            if (callout.type === "site") {
                bgColor = "rgba(255, 51, 68, 0.22)";
                textColor = "#ff6b77";
                borderColor = "rgba(255, 51, 68, 0.4)";
            } else if (callout.type === "ct") {
                textColor = "#79b8ff";
            } else if (callout.type === "base") {
                textColor = "#d29922";
            }

            ctx.fillStyle = bgColor;
            ctx.strokeStyle = borderColor;
            ctx.lineWidth = 1;

            const rx = pos.x - textWidth / 2 - padX;
            const ry = pos.y - 8 - padY;
            const rw = textWidth + padX * 2;
            const rh = 16 + padY * 2;

            ctx.beginPath();
            ctx.roundRect(rx, ry, rw, rh, 4);
            ctx.fill();
            ctx.stroke();

            ctx.fillStyle = textColor;
            ctx.fillText(callout.name, pos.x, pos.y);
        });
        ctx.restore();
    }

    // Desenha a C4 com Fidelidade Competitiva Oficial (Sem Visão Noturna / Sem Cheat)
    function drawC4(ctx) {
        if (!state.telemetry || !state.telemetry.c4) return;
        const c4 = state.telemetry.c4;

        // Determina o time do jogador humano
        let myTeam = "CT";
        for (const interp of state.interpolatedPlayers.values()) {
            if (interp.dto.is_human) {
                myTeam = interp.dto.team;
                break;
            }
        }

        if (c4.is_planted) {
            // Regra Oficial CS2: Se for CT e a bomba ainda não foi avistada/confirmada, NÃO desenha no radar!
            const isVisibleToTeam = (myTeam === "TR") || c4.is_spotted;
            if (!isVisibleToTeam) {
                return; // Oculta a bomba no radar para manter realismo competitivo
            }

            const pos = worldToRadar(c4.x, c4.y);
            const pulse = (Math.sin(state.pulsePhase * 3) + 1) * 0.5;

            ctx.save();
            // Onda de choque vermelha em expansão
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, 14 + pulse * 10, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 51, 68, ${0.35 - pulse * 0.25})`;
            ctx.fill();

            // Círculo base da bomba
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, 10, 0, Math.PI * 2);
            ctx.fillStyle = "#ff2233";
            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = 1.5;
            ctx.fill();
            ctx.stroke();

            // Ícone de Bomba
            ctx.font = "bold 12px 'Inter'";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillStyle = "#ffffff";
            ctx.fillText("💣", pos.x, pos.y + 1);

            // Texto Flutuante SEM cronômetro de trapaça decimal! Apenas identificação
            ctx.font = "bold 10px 'JetBrains Mono'";
            ctx.fillStyle = "#ffffff";
            ctx.shadowColor = "#000000";
            ctx.shadowBlur = 4;
            const siteLabel = c4.site && c4.site !== "?" ? `C4 (${c4.site})` : "C4 ARMADA";
            ctx.fillText(siteLabel, pos.x, pos.y - 15);

            ctx.restore();
        } else if (c4.is_dropped) {
            const isVisibleToTeam = (myTeam === "TR") || c4.is_spotted;
            if (!isVisibleToTeam) {
                return;
            }

            const pos = worldToRadar(c4.x, c4.y);
            const pulse = (Math.sin(state.pulsePhase * 2) + 1) * 0.5;

            ctx.save();
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, 10 + pulse * 5, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 165, 0, ${0.35 - pulse * 0.2})`;
            ctx.fill();

            ctx.beginPath();
            ctx.arc(pos.x, pos.y, 8, 0, Math.PI * 2);
            ctx.fillStyle = "#ffa500";
            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = 1.5;
            ctx.fill();
            ctx.stroke();

            ctx.font = "bold 10px 'Inter'";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillStyle = "#ffffff";
            ctx.fillText("💣", pos.x, pos.y + 1);

            ctx.font = "bold 10px 'JetBrains Mono'";
            ctx.fillStyle = "#ffa500";
            ctx.fillText("C4 DROP", pos.x, pos.y - 13);
            ctx.restore();
        }
    }

    // Desenha Todos os Jogadores com Cones de Visão, Mira e Status
    function drawPlayers(ctx) {
        // Encontra o time do jogador humano
        let humanTeam = "CT";
        for (const interp of state.interpolatedPlayers.values()) {
            if (interp.dto.is_human) {
                humanTeam = interp.dto.team;
                break;
            }
        }

        // Desenha primeiro os mortos (embaixo)
        for (const interp of state.interpolatedPlayers.values()) {
            if (!interp.dto.is_alive) {
                drawDeadPlayer(ctx, interp);
            }
        }

        // Desenha cones de visão dos vivos (se ativado)
        if (state.options.showFov) {
            for (const interp of state.interpolatedPlayers.values()) {
                if (interp.dto.is_alive && (interp.dto.team === humanTeam || interp.dto.is_spotted)) {
                    drawPlayerFov(ctx, interp);
                }
            }
        }

        // Desenha os pontos dos jogadores vivos
        for (const interp of state.interpolatedPlayers.values()) {
            if (interp.dto.is_alive) {
                drawLivePlayer(ctx, interp, humanTeam);
            }
        }
    }

    // Marcador de Morte Suave
    function drawDeadPlayer(ctx, interp) {
        ctx.save();
        ctx.strokeStyle = "rgba(139, 148, 158, 0.45)";
        ctx.lineWidth = 2;
        const size = 5;

        ctx.beginPath();
        ctx.moveTo(interp.x - size, interp.y - size);
        ctx.lineTo(interp.x + size, interp.y + size);
        ctx.moveTo(interp.x + size, interp.y - size);
        ctx.lineTo(interp.x - size, interp.y + size);
        ctx.stroke();
        ctx.restore();
    }

    // Cone de Visão (FOV ~75 graus com gradiente direcional)
    function drawPlayerFov(ctx, interp) {
        const isHuman = interp.dto.is_human;
        const fovAngle = (75 * Math.PI) / 180.0;
        const fovRadius = isHuman ? 130 : 95;
        const halfFov = fovAngle / 2;

        ctx.save();
        ctx.beginPath();
        ctx.moveTo(interp.x, interp.y);
        ctx.arc(interp.x, interp.y, fovRadius, interp.yawRad - halfFov, interp.yawRad + halfFov);
        ctx.closePath();

        const grad = ctx.createRadialGradient(interp.x, interp.y, 5, interp.x, interp.y, fovRadius);
        if (isHuman) {
            grad.addColorStop(0, "rgba(255, 215, 0, 0.35)");
            grad.addColorStop(1, "rgba(255, 215, 0, 0.0)");
        } else if (interp.dto.team === "CT") {
            grad.addColorStop(0, "rgba(56, 139, 253, 0.22)");
            grad.addColorStop(1, "rgba(56, 139, 253, 0.0)");
        } else if (interp.dto.team === "TR") {
            grad.addColorStop(0, "rgba(240, 136, 62, 0.22)");
            grad.addColorStop(1, "rgba(240, 136, 62, 0.0)");
        } else {
            grad.addColorStop(0, "rgba(255, 51, 68, 0.25)");
            grad.addColorStop(1, "rgba(255, 51, 68, 0.0)");
        }

        ctx.fillStyle = grad;
        ctx.fill();
        ctx.restore();
    }

    // Desenha o Ponto do Jogador com Anel de HP, Direção e Identidade
    function drawLivePlayer(ctx, interp, humanTeam) {
        const p = interp.dto;
        const isHuman = p.is_human;
        const isTeammate = p.team === humanTeam;
        const isEnemy = !isTeammate && p.team !== "SPEC";

        // Se for inimigo e não estiver 'spotted', não desenha (preserva realismo tático)
        if (isEnemy && !p.is_spotted && !state.telemetry.is_warmup) {
            return;
        }

        ctx.save();

        const dotRadius = isHuman ? 10 : 8;

        // Cores Primárias
        let mainColor = "#388bfd"; // CT
        if (isHuman) {
            mainColor = "#ffd700"; // Dourado exclusivo para o humano
        } else if (p.team === "TR") {
            mainColor = "#f0883e"; // TR
        }
        if (isEnemy) {
            mainColor = "#ff3344"; // Inimigo spotted
        }

        // 1. Halo Pulsante para o Humano ou Inimigo Revelado
        if (isHuman) {
            const pulse = (Math.sin(state.pulsePhase * 2.5) + 1) * 0.5;
            ctx.beginPath();
            ctx.arc(interp.x, interp.y, dotRadius + 4 + pulse * 5, 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(255, 215, 0, ${0.45 - pulse * 0.25})`;
            ctx.lineWidth = 2;
            ctx.stroke();
        } else if (isEnemy) {
            const pulse = (Math.sin(state.pulsePhase * 4) + 1) * 0.5;
            ctx.beginPath();
            ctx.arc(interp.x, interp.y, dotRadius + 3 + pulse * 4, 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(255, 51, 68, ${0.5 - pulse * 0.25})`;
            ctx.lineWidth = 1.5;
            ctx.stroke();
        }

        // 2. Anel de Vida (HP Arc) ao redor do círculo
        const hpPercent = Math.max(0, Math.min(100, interp.hp)) / 100.0;
        ctx.beginPath();
        ctx.arc(interp.x, interp.y, dotRadius + 2.5, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * hpPercent);
        let hpColor = "#00ff66";
        if (interp.hp < 30) hpColor = "#ff3344";
        else if (interp.hp < 60) hpColor = "#ffa500";
        ctx.strokeStyle = hpColor;
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // 3. Círculo do Jogador
        ctx.beginPath();
        ctx.arc(interp.x, interp.y, dotRadius, 0, Math.PI * 2);
        ctx.fillStyle = mainColor;
        ctx.strokeStyle = "#07090d";
        ctx.lineWidth = 2;
        ctx.fill();
        ctx.stroke();

        // 4. Ponteiro de Direção (Ângulo de Mira Yaw)
        const arrowLen = dotRadius + 8;
        const arrowTipX = interp.x + Math.cos(interp.yawRad) * arrowLen;
        const arrowTipY = interp.y + Math.sin(interp.yawRad) * arrowLen;

        ctx.beginPath();
        ctx.moveTo(interp.x + Math.cos(interp.yawRad) * (dotRadius - 1), interp.y + Math.sin(interp.yawRad) * (dotRadius - 1));
        ctx.lineTo(arrowTipX, arrowTipY);
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2.5;
        ctx.lineCap = "round";
        ctx.stroke();

        // 5. Se o jogador é o portador da C4, desenha o selo da bomba
        if (state.telemetry.c4 && state.telemetry.c4.carrier_name === p.name) {
            ctx.font = "bold 11px 'Inter'";
            ctx.fillStyle = "#ffffff";
            ctx.fillText("💣", interp.x + 10, interp.y - 10);
        }

        // 6. Rótulo com Nome e Função (Role)
        ctx.font = isHuman ? "bold 11px 'Inter'" : "600 10px 'Inter'";
        ctx.textAlign = "center";
        ctx.textBaseline = "bottom";

        let labelText = isHuman ? `${p.name} (VOCÊ)` : p.name;
        if (p.role && !isHuman && isTeammate) {
            const shortRole = p.role.replace("Role_", "").substring(0, 4).toUpperCase();
            labelText = `[${shortRole}] ${p.name}`;
        }

        const textWidth = ctx.measureText(labelText).width;
        ctx.fillStyle = "rgba(7, 9, 13, 0.85)";
        ctx.fillRect(interp.x - textWidth / 2 - 3, interp.y - dotRadius - 16, textWidth + 6, 13);
        
        ctx.fillStyle = isHuman ? "#ffd700" : (isEnemy ? "#ff6b77" : "#f0f6fc");
        ctx.fillText(labelText, interp.x, interp.y - dotRadius - 4);

        ctx.restore();
    }

    // ==========================================================================
    // 8. Atualização do Painel Lateral (TOC - 30% Right Sidebar)
    // ==========================================================================
    function updateSidebar(data) {
        if (!data) return;

        // 8.1 Header & Placar
        if (DOM.ctScore) DOM.ctScore.textContent = data.ct_score;
        if (DOM.trScore) DOM.trScore.textContent = data.tr_score;
        if (DOM.roundBadge) DOM.roundBadge.textContent = `ROUND ${data.round}`;

        if (DOM.phaseBadge) {
            let phaseText = data.phase;
            if (data.is_warmup) phaseText = "AQUECIMENTO";
            else if (data.is_freezetime) phaseText = "FREEZETIME";
            else if (data.is_paused) phaseText = "PAUSADO";
            else if (data.phase === "Staging") phaseText = "STAGING";
            else if (data.phase === "Executing") phaseText = "EXECUTANDO";
            else if (data.phase === "PostPlantHold") phaseText = "PÓS-PLANT";
            else if (data.phase === "Retake") phaseText = "RETAKE";
            else if (data.phase === "TacticalSave") phaseText = "SAVE TÁTICO";

            DOM.phaseBadge.textContent = phaseText;
            DOM.phaseBadge.className = `phase-badge ${data.is_freezetime ? 'freezetime' : ''} ${data.is_paused ? 'paused' : ''}`;
        }

        if (DOM.buyStatePill) {
            const buyMap = {
                "FULL_BUY": "FULL BUY",
                "FORCE_BUY": "FORCE BUY",
                "HALF_BUY": "HALF BUY",
                "ECO": "ECO TOTAL"
            };
            const buyText = buyMap[data.buy_state] || data.buy_state;
            DOM.buyStatePill.textContent = buyText;
            DOM.buyStatePill.className = `econ-pill ${data.buy_state.toLowerCase().replace('_', '-')}`;
        }

        if (DOM.teamCashText) {
            DOM.teamCashText.textContent = `Caixa da Equipe: $${(data.team_money || 0).toLocaleString('en-US')}`;
        }

        // 8.2 Tática Ativa
        if (DOM.tacticName) {
            DOM.tacticName.textContent = data.tactic_name || "Aguardando definição tática...";
        }
        if (DOM.tacticSummary) {
            DOM.tacticSummary.textContent = data.tactic_summary || "Bots aguardando chamada de posicionamento.";
        }
        if (DOM.tempoPill) {
            DOM.tempoPill.textContent = `RITMO: ${data.tempo || "PADRÃO"}`;
        }
        if (DOM.tierPill) {
            DOM.tierPill.textContent = `${data.tier || "TIER 1"}`;
        }
        if (DOM.stagingTimerPill) {
            if (data.staging_time_remaining > 0) {
                DOM.stagingTimerPill.style.display = "inline-block";
                DOM.stagingTimerPill.textContent = `STAGING: ${data.staging_time_remaining.toFixed(1)}s`;
            } else {
                DOM.stagingTimerPill.style.display = "none";
            }
        }

        // Alertas contextuais
        if (DOM.alertsContainer) {
            DOM.alertsContainer.innerHTML = "";
            if (data.alerts && data.alerts.length > 0) {
                data.alerts.forEach(alertText => {
                    const alertDiv = document.createElement("div");
                    alertDiv.className = "alert-item";
                    alertDiv.textContent = `⚠️ ${alertText}`;
                    DOM.alertsContainer.appendChild(alertDiv);
                });
            }
        }

        // 8.3 Feed de Voz IGL (Faster-Whisper)
        if (DOM.voiceCmdText) {
            if (data.last_voice_command && data.last_voice_command.trim().length > 0) {
                DOM.voiceCmdText.innerHTML = `"${escapeHtml(data.last_voice_command)}"`;
            } else {
                DOM.voiceCmdText.innerHTML = `<i>Segure 'V' no jogo para comandar por voz...</i>`;
            }
        }
        if (DOM.voiceActionText) {
            if (data.last_voice_action && data.last_voice_action.trim().length > 0) {
                DOM.voiceActionText.textContent = data.last_voice_action;
            } else {
                DOM.voiceActionText.textContent = "Status: Reconhecimento ativo via Faster-Whisper";
            }
        }

        // 8.4 Banner Flutuante de Bomba (C4) - Regra Oficial CS2 Sem Trapaça
        if (data.c4 && data.c4.is_planted) {
            DOM.c4Banner.classList.remove('hidden');

            const human = data.players.find(p => p.is_human);
            const myTeam = human ? human.team : "CT";
            const isSpotted = data.c4.is_spotted || myTeam === "TR";

            if (myTeam === "TR") {
                if (DOM.c4Title) DOM.c4Title.textContent = `💣 C4 ARMADA NO BOMBSITE ${data.c4.site || "BOMB"}`;
                if (DOM.c4Timer) DOM.c4Timer.textContent = "PROTEJA O PLANT - IMPEÇA O DEFUSE";
            } else {
                if (isSpotted && data.c4.site && data.c4.site !== "?") {
                    if (DOM.c4Title) DOM.c4Title.textContent = `💣 C4 LOCALIZADA NO BOMBSITE ${data.c4.site}`;
                    if (DOM.c4Timer) DOM.c4Timer.textContent = "INICIE O RETAKE COM A EQUIPE";
                } else {
                    if (DOM.c4Title) DOM.c4Title.textContent = "⚠️ C4 PLANTADA (LOCAL NÃO CONFIRMADO)";
                    if (DOM.c4Timer) DOM.c4Timer.textContent = "PROCURE POR BARULHOS OU VÁ AO BOMB";
                }
            }

            // Oculta barra de progresso de defuse para manter fidelidade competitiva oficial
            if (DOM.c4DefuseBar) {
                DOM.c4DefuseBar.classList.add('hidden');
            }
        } else {
            DOM.c4Banner.classList.add('hidden');
        }

        // 8.5 Lista de Posicionamento da Equipe (Roster)
        updateRoster(data.players);
    }

    // Atualiza Lista de Jogadores da Equipe
    function updateRoster(players) {
        if (!DOM.rosterList || !players) return;

        // Identifica time do humano
        const human = players.find(p => p.is_human);
        const myTeam = human ? human.team : "CT";

        // Filtra apenas jogadores da mesma equipe
        const teamPlayers = players.filter(p => p.team === myTeam);
        const aliveCount = teamPlayers.filter(p => p.is_alive).length;

        if (DOM.rosterCount) {
            DOM.rosterCount.textContent = `${aliveCount}/${teamPlayers.length} VIVOS`;
        }

        // Ordena: humano primeiro, depois bots por ordem de role
        teamPlayers.sort((a, b) => {
            if (a.is_human) return -1;
            if (b.is_human) return 1;
            return a.name.localeCompare(b.name);
        });

        DOM.rosterList.innerHTML = "";

        teamPlayers.forEach(p => {
            const card = document.createElement("div");
            card.className = `roster-card ${p.is_human ? 'is-human' : ''} ${!p.is_alive ? 'dead' : ''}`;

            // Classe da Role
            let roleClass = "rotator";
            let roleLabel = p.role || "Bot";
            if (p.is_human) {
                roleClass = "human";
                roleLabel = "IGL";
            } else if (roleLabel.toLowerCase().includes("awp")) {
                roleClass = "awp";
                roleLabel = "AWP";
            } else if (roleLabel.toLowerCase().includes("entry")) {
                roleClass = "entry";
                roleLabel = "ENTRY";
            } else if (roleLabel.toLowerCase().includes("anchor")) {
                roleClass = "anchor";
                roleLabel = "ANCHOR";
            } else if (roleLabel.toLowerCase().includes("support") || roleLabel.toLowerCase().includes("rotator")) {
                roleClass = "rotator";
                roleLabel = "ROTATOR";
            }

            // Cor de Vida (HP)
            let hpColor = "#00ff66";
            if (p.hp < 30) hpColor = "#ff3344";
            else if (p.hp < 60) hpColor = "#ffa500";

            // Normalização de Stance
            let stanceClass = "passivo";
            const sLower = (p.stance || "").toLowerCase();
            if (sLower.includes("jiggle")) stanceClass = "jiggle";
            else if (sLower.includes("poke") || sLower.includes("aggress")) stanceClass = "poke";
            else if (sLower.includes("one")) stanceClass = "oneanddone";

            const weaponFormatted = (p.weapon || "faca").toUpperCase();

            card.innerHTML = `
                <div class="card-top">
                    <div class="player-identity">
                        <span class="role-badge ${roleClass}">${roleLabel}</span>
                        <span class="player-name">${escapeHtml(p.name)}</span>
                    </div>
                    <span class="weapon-label">${escapeHtml(weaponFormatted)}</span>
                </div>
                <div class="card-mid">
                    <div class="hp-bar-bg">
                        <div class="hp-bar-fill" style="width: ${p.hp}%; background-color: ${hpColor}"></div>
                    </div>
                    <span class="hp-val" style="color: ${hpColor}">${p.is_alive ? p.hp : 0}</span>
                </div>
                <div class="card-bottom">
                    <div class="spot-tag">
                        <span>📍</span>
                        <span>${escapeHtml(p.spot || "Base")}</span>
                    </div>
                    <span class="stance-pill ${stanceClass}">${escapeHtml(p.stance || "Hold")}</span>
                </div>
            `;

            DOM.rosterList.appendChild(card);
        });
    }

    // ==========================================================================
    // 9. Comunicação em Tempo Real (WebSocket + Fallback Polling)
    // ==========================================================================
    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/radar`;

        try {
            state.ws = new WebSocket(wsUrl);

            state.ws.onopen = () => {
                state.wsConnected = true;
                if (DOM.tickrateText) {
                    DOM.tickrateText.textContent = "20Hz WS LIVE";
                    DOM.tickrateText.style.color = "var(--accent-cyan)";
                }
            };

            state.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data && data.map) {
                        state.telemetry = data;
                        updateSidebar(data);
                    }
                } catch (e) {
                    console.error("[Radar WS] Erro ao processar telemetria:", e);
                }
            };

            state.ws.onclose = () => {
                state.wsConnected = false;
                if (DOM.tickrateText) {
                    DOM.tickrateText.textContent = "RECONECTANDO...";
                    DOM.tickrateText.style.color = "var(--accent-red)";
                }
                setTimeout(connectWebSocket, 1500);
            };

            state.ws.onerror = () => {
                state.ws?.close();
            };
        } catch (e) {
            console.warn("[Radar WS] Falha ao instanciar WebSocket. Ativando fallback polling.");
            setTimeout(connectWebSocket, 2500);
        }
    }

    // Envio de Comando Tático ao C# Bridge via WebSocket ou REST
    function sendCommand(cmd) {
        if (!cmd) return;

        if (state.ws && state.ws.readyState === WebSocket.OPEN) {
            state.ws.send(JSON.stringify({ command: cmd }));
        } else {
            fetch('/api/radar/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: cmd })
            }).catch(err => console.error("[Radar CMD] Erro ao enviar comando:", err));
        }

        // Feedback sonoro/visual sutil no botão
        console.log(`[Radar CMD] Comando enviado: ${cmd}`);
    }

    // Utilitário de escape HTML
    function escapeHtml(text) {
        if (!text) return "";
        return text.replace(/&/g, "&amp;")
                   .replace(/</g, "&lt;")
                   .replace(/>/g, "&gt;")
                   .replace(/"/g, "&quot;")
                   .replace(/'/g, "&#039;");
    }

    // ==========================================================================
    // 10. Inicialização de Eventos e Listeners
    // ==========================================================================
    function init() {
        // 1. Carrega a Imagem do Radar Oficial
        state.radarImage.src = "/static/de_mirage_radar.png";
        state.radarImage.onload = () => {
            state.radarLoaded = true;
        };

        // 2. Controles de Toggle
        if (DOM.toggleCallouts) {
            DOM.toggleCallouts.addEventListener('change', (e) => {
                state.options.showCallouts = e.target.checked;
            });
        }

        if (DOM.toggleFov) {
            DOM.toggleFov.addEventListener('change', (e) => {
                state.options.showFov = e.target.checked;
            });
        }

        if (DOM.btnFullscreen) {
            DOM.btnFullscreen.addEventListener('click', () => {
                if (!document.fullscreenElement) {
                    document.documentElement.requestFullscreen().catch(() => {});
                } else {
                    document.exitFullscreen().catch(() => {});
                }
            });
        }

        // 3. Ações Rápidas
        if (DOM.btnExecute) {
            DOM.btnExecute.addEventListener('click', () => sendCommand("!executar"));
        }
        if (DOM.btnRotate) {
            DOM.btnRotate.addEventListener('click', () => sendCommand("!miou"));
        }
        if (DOM.btnFlash) {
            DOM.btnFlash.addEventListener('click', () => sendCommand("!flash"));
        }
        if (DOM.btnPause) {
            DOM.btnPause.addEventListener('click', () => sendCommand("!pause"));
        }

        // 4. Inicia WebSocket e Loop de Renderização
        connectWebSocket();
        requestAnimationFrame(render);
    }

    // Inicia quando o DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
