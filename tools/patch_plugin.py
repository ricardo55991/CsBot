with open(r'src/CsBotManager/CsBotManagerPlugin.cs', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add TrPivotController and CurrentPlan properties
p_target = """    private TacticalPlan _currentPlan = new();"""
p_target_crlf = p_target.replace('\n', '\r\n')

p_rep = """    private TacticalPlan _currentPlan = new();
    private TacticalPlan _currentTrPlan = new();
    public TrMacroPivotController? TrPivotController => _trPivotController;
    public TacticalPlan CurrentPlan => _currentPlan;"""
p_rep_crlf = p_rep.replace('\n', '\r\n')

if p_target_crlf in text:
    text = text.replace(p_target_crlf, p_rep_crlf, 1)
elif p_target in text:
    text = text.replace(p_target, p_rep, 1)
else:
    raise AssertionError('p_target not found')

# 2. Add Plugin = this and _iglService.TelemetryLogger = _telemetryLogger
eng_target = """        _microMoveEngine = new MicroMoveEngine(_mapProfileManager, _roleManager)
        {
            TelemetryLogger = _telemetryLogger, CalloutSystem = _calloutSystem
        };"""
eng_target_crlf = eng_target.replace('\n', '\r\n')

eng_rep = """        _microMoveEngine = new MicroMoveEngine(_mapProfileManager, _roleManager)
        {
            TelemetryLogger = _telemetryLogger, CalloutSystem = _calloutSystem, Plugin = this
        };
        _iglService.TelemetryLogger = _telemetryLogger;"""
eng_rep_crlf = eng_rep.replace('\n', '\r\n')

if eng_target_crlf in text:
    text = text.replace(eng_target_crlf, eng_rep_crlf, 1)
elif eng_target in text:
    text = text.replace(eng_target, eng_rep, 1)
else:
    raise AssertionError('eng_target not found')

# 3. Add bot_eco_limit convar in OnRoundStart
rs_target = """        _currentRound++;
        _isFreezeTime = true;
        _isBombPlanted = false;"""
rs_target_crlf = rs_target.replace('\n', '\r\n')

rs_rep = """        _currentRound++;
        _isFreezeTime = true;
        _isBombPlanted = false;

        // Correcao 3: Bloqueia compra autonoma nativa no frame 0
        Server.ExecuteCommand("bot_eco_limit 16000; bot_autobuy 0;");"""
rs_rep_crlf = rs_rep.replace('\n', '\r\n')

if rs_target_crlf in text:
    text = text.replace(rs_target_crlf, rs_rep_crlf, 1)
elif rs_target in text:
    text = text.replace(rs_target, rs_rep, 1)
else:
    raise AssertionError('rs_target not found')

# 4. In OnPlayerHurt, check grenade watchdog
hurt_target = """        _clearAndPlantController?.OnPlayerHurt(@event);
        _trPivotController?.OnPlayerHurt(@event);
        _mobilityController?.OnPlayerHurt(@event);
        _combatAdapter?.OnPlayerHurt(@event);"""
hurt_target_crlf = hurt_target.replace('\n', '\r\n')

hurt_rep = """        _clearAndPlantController?.OnPlayerHurt(@event);
        _trPivotController?.OnPlayerHurt(@event);
        _mobilityController?.OnPlayerHurt(@event);
        _combatAdapter?.OnPlayerHurt(@event);

        if (@event.Userid != null && @event.Userid.IsValid && @event.Userid.IsBot)
        {
            _locomotionDriver?.CheckGrenadeHurtWatchdog(@event.Userid);
        }"""
hurt_rep_crlf = hurt_rep.replace('\n', '\r\n')

if hurt_target_crlf in text:
    text = text.replace(hurt_target_crlf, hurt_rep_crlf, 1)
elif hurt_target in text:
    text = text.replace(hurt_target, hurt_rep, 1)
else:
    raise AssertionError('hurt_target not found')

# 5. IGL dual-team querying (CT and TR)
old_igl_block = """                // C-04A: Captura os valores na Game Thread antes de despachar para o Task.Run
                string mapName = Server.MapName;
                CsTeam capturedHumanTeam = humanTeam;
                int capturedRound = _currentRound;
                int capturedMoney = _economyManager.TeamAverageMoney;
                int capturedHumanSlot = human?.Slot ?? -1;
                var currentBuyState = _economyManager.CurrentBuyState;

                int requestSeq = Interlocked.Increment(ref _iglRequestSequence);
                var token = _roundCts?.Token ?? CancellationToken.None;

                Task.Run(async () =>
                {
                    TacticalPlan plan;
                    try
                    {
                        plan = await _iglService.GetTacticalDecisionAsync(
                            mapName,
                            capturedHumanTeam,
                            currentBuyState,
                            capturedRound,
                            capturedMoney,
                            null,
                            false,
                            _mapProfileManager,
                            token);
                    }
                    catch (OperationCanceledException)
                    {
                        return;
                    }

                    // C-04B: Retorna para a Game Thread e revalida os ponteiros
                    Server.NextFrame(() =>
                    {
                        if (capturedRound != _currentRound || requestSeq != _iglRequestSequence)
                        {
                            return;
                        }

                        var freshPlayers = GetActivePlayers();
                        var freshHuman = freshPlayers.FirstOrDefault(p => p.Slot == capturedHumanSlot && !p.IsBot);
                        var freshCtBots = freshPlayers.Where(p => p.Team == CsTeam.CounterTerrorist && p.IsBot).ToList();
                        var freshTrBots = freshPlayers.Where(p => p.Team == CsTeam.Terrorist && p.IsBot).ToList();
                        var freshTeamBots = freshPlayers.Where(p => p.Team == capturedHumanTeam && p.IsBot).ToList();

                        _currentPlan = plan;
                        _currentPlan.PlayTier = tacticalDecision.Tier;
                        _currentPlan.PlayId = tacticalDecision.PlayId;
                        _currentPlan.CurrentPhase = RoundPhase.FreezeTime;

                        // C-03: Re-aplica automaticamente posição travada do humano se existir
                        if (_roleManager.IsHumanPositionLocked && freshHuman != null && !string.IsNullOrEmpty(_roleManager.LockedSectorName))
                        {
                            _roleManager.ClaimPositionForPlayer(freshHuman, _roleManager.LockedSectorName, freshTeamBots, _currentPlan, _mapProfileManager);
                        }

                        _ctController?.OnRoundStart(_currentPlan, freshCtBots);
                        _midRoundAdapter?.OnRoundStart(_currentPlan, freshTrBots, freshHuman);

                        UtilityAndClockCoordinator.PrintTeamChat(capturedHumanTeam, iglName, $"⚡ Tática: {plan.TacticName} | {plan.TacticSummary}");
                    });
                });"""

new_igl_block = """                // C-04A: Captura os valores na Game Thread antes de despachar para o Task.Run
                string mapName = Server.MapName;
                CsTeam capturedHumanTeam = humanTeam;
                int capturedRound = _currentRound;
                int capturedCtMoney = _economyManager.TeamAverageMoney;
                int capturedTrMoney = _economyManager.TeamAverageMoney;
                int capturedHumanSlot = human?.Slot ?? -1;
                var currentBuyState = _economyManager.CurrentBuyState;

                int requestSeq = Interlocked.Increment(ref _iglRequestSequence);
                var token = _roundCts?.Token ?? CancellationToken.None;

                Task.Run(async () =>
                {
                    TacticalPlan ctPlan;
                    TacticalPlan trPlan;
                    try
                    {
                        ctPlan = await _iglService.GetTacticalDecisionAsync(
                            mapName,
                            CsTeam.CounterTerrorist,
                            currentBuyState,
                            capturedRound,
                            capturedCtMoney,
                            null,
                            false,
                            _mapProfileManager,
                            token);
                    }
                    catch (OperationCanceledException) { return; }
                    catch (Exception ex)
                    {
                        ctPlan = _iglService.GenerateDeterministicFallbackPlan(CsTeam.CounterTerrorist, currentBuyState, _mapProfileManager, ex.Message);
                    }

                    try
                    {
                        trPlan = await _iglService.GetTacticalDecisionAsync(
                            mapName,
                            CsTeam.Terrorist,
                            currentBuyState,
                            capturedRound,
                            capturedTrMoney,
                            null,
                            false,
                            _mapProfileManager,
                            token);
                    }
                    catch (OperationCanceledException) { return; }
                    catch (Exception ex)
                    {
                        trPlan = _iglService.GenerateDeterministicFallbackPlan(CsTeam.Terrorist, currentBuyState, _mapProfileManager, ex.Message);
                    }

                    // C-04B: Retorna para a Game Thread e revalida os ponteiros
                    Server.NextFrame(() =>
                    {
                        if (capturedRound != _currentRound || requestSeq != _iglRequestSequence)
                        {
                            return;
                        }

                        var freshPlayers = GetActivePlayers();
                        var freshHuman = freshPlayers.FirstOrDefault(p => p.Slot == capturedHumanSlot && !p.IsBot);
                        var freshCtBots = freshPlayers.Where(p => p.Team == CsTeam.CounterTerrorist && p.IsBot).ToList();
                        var freshTrBots = freshPlayers.Where(p => p.Team == CsTeam.Terrorist && p.IsBot).ToList();
                        var freshTeamBots = freshPlayers.Where(p => p.Team == capturedHumanTeam && p.IsBot).ToList();

                        _currentPlan = (capturedHumanTeam == CsTeam.CounterTerrorist) ? ctPlan : trPlan;
                        _currentTrPlan = trPlan;
                        _currentPlan.PlayTier = tacticalDecision.Tier;
                        _currentPlan.PlayId = tacticalDecision.PlayId;
                        _currentPlan.CurrentPhase = RoundPhase.FreezeTime;
                        _currentTrPlan.CurrentPhase = RoundPhase.FreezeTime;

                        // C-03: Re-aplica automaticamente posição travada do humano se existir
                        if (_roleManager.IsHumanPositionLocked && freshHuman != null && !string.IsNullOrEmpty(_roleManager.LockedSectorName))
                        {
                            _roleManager.ClaimPositionForPlayer(freshHuman, _roleManager.LockedSectorName, freshTeamBots, _currentPlan, _mapProfileManager);
                        }

                        _ctController?.OnRoundStart(ctPlan, freshCtBots);
                        _midRoundAdapter?.OnRoundStart(trPlan, freshTrBots, freshHuman);

                        UtilityAndClockCoordinator.PrintTeamChat(capturedHumanTeam, iglName, $"⚡ Tática: {_currentPlan.TacticName} | {_currentPlan.TacticSummary}");
                    });
                });"""

old_igl_block_crlf = old_igl_block.replace('\n', '\r\n')
new_igl_block_crlf = new_igl_block.replace('\n', '\r\n')

if old_igl_block_crlf in text:
    text = text.replace(old_igl_block_crlf, new_igl_block_crlf, 1)
elif old_igl_block in text:
    text = text.replace(old_igl_block, new_igl_block, 1)
else:
    raise AssertionError('old_igl_block not found')

# 6. Combined JSON in _telemetryLogger.OnRoundStart
old_telem = """            // Telemetria Forense: Registra resumo inicial completo do round (F-013 / Bloco 8.3)
            _telemetryLogger?.OnRoundStart(
                _currentRound,
                _ctScore,
                _trScore,
                humanTeam == CsTeam.CounterTerrorist ? _economyManager.CurrentBuyState : enemyBuyState,
                humanTeam == CsTeam.Terrorist ? _economyManager.CurrentBuyState : enemyBuyState,
                _currentPlan,
                _currentPlan != null ? _currentPlan.RawJson : string.Empty,
                players);"""

new_telem = """            // Telemetria Forense: Registra resumo inicial completo com taticas CT e TR
            string rawCt = (_currentPlan != null && humanTeam == CsTeam.CounterTerrorist) ? _currentPlan.RawJson : (_currentTrPlan != null ? _currentTrPlan.RawJson : "{}");
            string rawTr = (_currentTrPlan != null && !string.IsNullOrEmpty(_currentTrPlan.RawJson)) ? _currentTrPlan.RawJson : (_currentPlan != null ? _currentPlan.RawJson : "{}");
            string combinedIglJson = "{\\n  \\"CT\\": " + (string.IsNullOrWhiteSpace(rawCt) ? "{}" : rawCt) + ",\\n  \\"TR\\": " + (string.IsNullOrWhiteSpace(rawTr) ? "{}" : rawTr) + "\\n}";

            _telemetryLogger?.OnRoundStart(
                _currentRound,
                _ctScore,
                _trScore,
                humanTeam == CsTeam.CounterTerrorist ? _economyManager.CurrentBuyState : enemyBuyState,
                humanTeam == CsTeam.Terrorist ? _economyManager.CurrentBuyState : enemyBuyState,
                _currentPlan,
                combinedIglJson,
                players);"""

old_telem_crlf = old_telem.replace('\n', '\r\n')
new_telem_crlf = new_telem.replace('\n', '\r\n')

if old_telem_crlf in text:
    text = text.replace(old_telem_crlf, new_telem_crlf, 1)
elif old_telem in text:
    text = text.replace(old_telem, new_telem, 1)
else:
    raise AssertionError('old_telem not found')

# 7. EquipBestWeapon for all bots at round start / freeze time
old_ft_equip = """            // 11.5s: Disciplina da C4 no Freeze Time (Parte A - Item 2 / Bloco 5.3)
            AddRoundTimer(0.5f, () =>
            {
                var curPlayers = GetActivePlayers();
                var curHuman = curPlayers.FirstOrDefault(p => !p.IsBot);
                var curTrBots = curPlayers.Where(p => p.Team == CsTeam.Terrorist && p.IsBot).ToList();"""

new_ft_equip = """            // 11.5s: Disciplina da C4 no Freeze Time e Garantia de Arma em Maos (Correcao 3)
            AddRoundTimer(0.5f, () =>
            {
                var curPlayers = GetActivePlayers();
                foreach (var b in curPlayers.Where(p => p != null && p.IsValid && p.IsBot && p.PawnIsAlive))
                {
                    EconomyManager.EquipBestWeapon(b);
                }

                var curHuman = curPlayers.FirstOrDefault(p => !p.IsBot);
                var curTrBots = curPlayers.Where(p => p.Team == CsTeam.Terrorist && p.IsBot).ToList();"""

old_ft_equip_crlf = old_ft_equip.replace('\n', '\r\n')
new_ft_equip_crlf = new_ft_equip.replace('\n', '\r\n')

if old_ft_equip_crlf in text:
    text = text.replace(old_ft_equip_crlf, new_ft_equip_crlf, 1)
elif old_ft_equip in text:
    text = text.replace(old_ft_equip, new_ft_equip, 1)
else:
    raise AssertionError('old_ft_equip not found')

with open(r'src/CsBotManager/CsBotManagerPlugin.cs', 'w', encoding='utf-8') as f:
    f.write(text)
print('CsBotManagerPlugin.cs patched successfully')
