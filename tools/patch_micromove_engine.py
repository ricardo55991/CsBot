with open(r'src/CsBotManager/MicroMoveEngine.cs', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add fields and property
fld_target = """    public MatchTelemetryLogger? TelemetryLogger { get; set; }

    public TacticalCalloutSystem? CalloutSystem { get; set; }"""
fld_target_crlf = fld_target.replace('\n', '\r\n')

fld_rep = """    public MatchTelemetryLogger? TelemetryLogger { get; set; }

    public TacticalCalloutSystem? CalloutSystem { get; set; }

    public CsBotManagerPlugin? Plugin { get; set; }

    private readonly Dictionary<(int Slot, string ChokepointName), float> _hotzoneEntryTimes = new();

    private readonly Dictionary<(int Slot, string ChokepointName), float> _hotzoneCooldowns = new();

    private readonly Dictionary<int, (Vector Pos, float SinceTime)> _stationaryTrackers = new();"""
fld_rep_crlf = fld_rep.replace('\n', '\r\n')

if fld_target_crlf in text:
    text = text.replace(fld_target_crlf, fld_rep_crlf, 1)
elif fld_target in text:
    text = text.replace(fld_target, fld_rep, 1)
else:
    raise AssertionError('fld_target not found')

# 2. ResetRound additions
rr_target = """        _lastDebugLogTime.Clear();

        _tickCounter = 0;"""
rr_target_crlf = rr_target.replace('\n', '\r\n')

rr_rep = """        _lastDebugLogTime.Clear();

        _hotzoneEntryTimes.Clear();

        _hotzoneCooldowns.Clear();

        _stationaryTrackers.Clear();

        _tickCounter = 0;"""
rr_rep_crlf = rr_rep.replace('\n', '\r\n')

if rr_target_crlf in text:
    text = text.replace(rr_target_crlf, rr_rep_crlf, 1)
elif rr_target in text:
    text = text.replace(rr_target, rr_rep, 1)
else:
    raise AssertionError('rr_target not found')

# 3. EvaluateLegitimateAdrenalineTrigger hotzone limit
hz_target = """        // 3. Gatilho de "Zona de Perigo" (Hotzone pré-mapeada: boca da Caverna, Palácio, Janela, Conector, Tapete)

        if (currentCp != null)

        {

            return AdrenalineTriggerType.Hotzone_PreMapped;

        }



        return AdrenalineTriggerType.None_SafeTransitGps;"""
hz_target_crlf = hz_target.replace('\n', '\r\n')

hz_rep = """        // 3. Gatilho de "Zona de Perigo" (Hotzone pré-mapeada: boca da Caverna, Palácio, Janela, Conector, Tapete)

        if (currentCp != null)

        {

            float nowTime = Server.CurrentTime;

            var hzKey = (bot.Slot, currentCp.Name);



            if (_hotzoneCooldowns.TryGetValue(hzKey, out float cdExpire) && nowTime < cdExpire)

            {

                return AdrenalineTriggerType.None_SafeTransitGps;

            }



            if (!_hotzoneEntryTimes.TryGetValue(hzKey, out float entryTime))

            {

                _hotzoneEntryTimes[hzKey] = nowTime;

                return AdrenalineTriggerType.Hotzone_PreMapped;

            }



            if ((nowTime - entryTime) > 2.0f)

            {

                _hotzoneCooldowns[hzKey] = nowTime + 8.0f;

                _hotzoneEntryTimes.Remove(hzKey);

                return AdrenalineTriggerType.None_SafeTransitGps;

            }



            return AdrenalineTriggerType.Hotzone_PreMapped;

        }

        else

        {

            var keysToRemove = _hotzoneEntryTimes.Keys.Where(k => k.Slot == bot.Slot).ToList();

            foreach (var k in keysToRemove) _hotzoneEntryTimes.Remove(k);

        }



        return AdrenalineTriggerType.None_SafeTransitGps;"""
hz_rep_crlf = hz_rep.replace('\n', '\r\n')

if hz_target_crlf in text:
    text = text.replace(hz_target_crlf, hz_rep_crlf, 1)
elif hz_target in text:
    text = text.replace(hz_target, hz_rep, 1)
else:
    raise AssertionError('hz_target not found')

# 4. Applying active step safeguard (around line 1571)
step_target = """            // Se a ação for StandStill (ex: metade final do Counter-Strafe para precisão de tiro)

            if (activeStep.ActionId == 0 || activeStep.SpeedScale <= 0.1f)

            {

                if (_activeMicroMoveCmdIds.TryRemove(slot, out long prevId) && prevId != 0)

                {

                    try { botApi.CancelUsercmdMovement(slot, prevId); } catch { }

                }"""
step_target_crlf = step_target.replace('\n', '\r\n')

step_rep = """            // Se a ação for StandStill (ex: metade final do Counter-Strafe para precisão de tiro)

            if (activeStep.ActionId == 0 || activeStep.SpeedScale <= 0.1f)

            {

                bool isTrObjectiveBot = bot.Team == CsTeam.Terrorist &&

                    (BotLocomotionDriver.HasC4(bot) ||

                     pawn.InBombZone ||

                     (Plugin?.CurrentPlan?.CurrentPhase == RoundPhase.Executing) ||

                     (Plugin?.TrPivotController?.HasPivotedThisRound == true));



                if (isTrObjectiveBot && !(pawn.Bot?.IsEnemyVisible ?? false))

                {

                    traj.IsOverrideActive = false;

                    continue;

                }



                if (_activeMicroMoveCmdIds.TryRemove(slot, out long prevId) && prevId != 0)

                {

                    try { botApi.CancelUsercmdMovement(slot, prevId); } catch { }

                }"""
step_rep_crlf = step_rep.replace('\n', '\r\n')

if step_target_crlf in text:
    text = text.replace(step_target_crlf, step_rep_crlf, 1)
elif step_target in text:
    text = text.replace(step_target, step_rep, 1)
else:
    raise AssertionError('step_target not found')

# 5. Stationary check in PredictBatch16Hz
stat_target = """            string weaponName = pawn.WeaponServices?.ActiveWeapon.Value?.DesignerName ?? "";"""
stat_target_crlf = stat_target.replace('\n', '\r\n')

stat_rep = """            string weaponName = pawn.WeaponServices?.ActiveWeapon.Value?.DesignerName ?? "";



            bool isStationary = false;

            if (_stationaryTrackers.TryGetValue(bot.Slot, out var stPosTime))

            {

                float dX = curX - stPosTime.Pos.X;

                float dY = curY - stPosTime.Pos.Y;

                float dZ = curZ - stPosTime.Pos.Z;

                float distMoved = MathF.Sqrt(dX * dX + dY * dY + dZ * dZ);

                if (distMoved > 50.0f)

                {

                    _stationaryTrackers[bot.Slot] = (new Vector(curX, curY, curZ), currentTime);

                }

                else if ((currentTime - stPosTime.SinceTime) > 3.0f)

                {

                    isStationary = true;

                }

            }

            else

            {

                _stationaryTrackers[bot.Slot] = (new Vector(curX, curY, curZ), currentTime);

            }"""
stat_rep_crlf = stat_rep.replace('\n', '\r\n')

if stat_target_crlf in text:
    text = text.replace(stat_target_crlf, stat_rep_crlf, 1)
elif stat_target in text:
    text = text.replace(stat_target, stat_rep, 1)
else:
    raise AssertionError('stat_target not found')

# 6. Multi-Horizon Anti-Inertia promotion in ONNX inference section
act_target = """                traj.Step0_Now = MicroMoveStep.FromActionId(act0, 125f);

                traj.Step1_125ms = MicroMoveStep.FromActionId(act1, 125f);

                traj.Step2_250ms = MicroMoveStep.FromActionId(act2, 125f);"""
act_target_crlf = act_target.replace('\n', '\r\n')

act_rep = """                // CORREÇÃO 1A: Quebra da Armadilha de Inércia do 0ms

                if (act0 == 0 && speed2D < 25.0f)

                {

                    if (act1 != 0)

                    {

                        act0 = act1;

                    }

                    else if (act2 != 0)

                    {

                        act0 = act2;

                    }

                    else

                    {

                        int bestAct = 0;

                        float bestLogit = float.NegativeInfinity;

                        int secondAct = 0;

                        float secondLogit = float.NegativeInfinity;

                        for (int a = 0; a < ActionSpaceSize; a++)

                        {

                            float val = _onnxBatchOutputLogits[teamBatchIdx, playerRowIdx, 0, a];

                            if (val > bestLogit)

                            {

                                secondLogit = bestLogit;

                                secondAct = bestAct;

                                bestLogit = val;

                                bestAct = a;

                            }

                            else if (val > secondLogit)

                            {

                                secondLogit = val;

                                secondAct = a;

                            }

                        }

                        if (secondAct != 0 && (bestLogit - secondLogit) < 2.5f)

                        {

                            act0 = secondAct;

                        }

                    }

                }



                // CORREÇÃO 1B: Proibição de Congelar TRs em Execução, C4 ou Parados > 3s

                bool isTrObjective = bot.Team == CsTeam.Terrorist &&

                    (BotLocomotionDriver.HasC4(bot) ||

                     pawn.InBombZone ||

                     (Plugin?.CurrentPlan?.CurrentPhase == RoundPhase.Executing) ||

                     (Plugin?.TrPivotController?.HasPivotedThisRound == true) ||

                     (isStationary && !csBot.IsEnemyVisible));



                if (isTrObjective && trigger == AdrenalineTriggerType.Hotzone_PreMapped)

                {

                    if (act0 == 0)

                    {

                        if (act1 != 0) act0 = act1;

                        else if (act2 != 0) act0 = act2;

                        else

                        {

                            traj.IsOverrideActive = false;

                            traj.ActiveBehaviorTag = "NavMesh_TR_Advance";

                            continue;

                        }

                    }

                }



                traj.Step0_Now = MicroMoveStep.FromActionId(act0, 125f);

                traj.Step1_125ms = MicroMoveStep.FromActionId(act1, 125f);

                traj.Step2_250ms = MicroMoveStep.FromActionId(act2, 125f);"""
act_rep_crlf = act_rep.replace('\n', '\r\n')

if act_target_crlf in text:
    text = text.replace(act_target_crlf, act_rep_crlf, 1)
elif act_target in text:
    text = text.replace(act_target, act_rep, 1)
else:
    raise AssertionError('act_target not found')

with open(r'src/CsBotManager/MicroMoveEngine.cs', 'w', encoding='utf-8') as f:
    f.write(text)
print('MicroMoveEngine.cs patched successfully')
