with open(r'src/CsBotManager/MicroMoveEngine.cs', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add ToReadableString to MicroMoveStep
step_helper = """    /// <summary>
    /// Retorna uma representacao legivel do comando cinematico relativo ao Yaw atual do bot.
    /// </summary>
    public readonly string ToReadableString(float botYaw = 0f)
    {
        if (ActionId <= 0 || ActionId > 96)
            return "Parado (0u)";

        float worldAngleDeg = DirectionIndex * 22.5f;
        float relAngle = worldAngleDeg - botYaw;
        while (relAngle > 180f) relAngle -= 360f;
        while (relAngle < -180f) relAngle += 360f;

        string dirName = relAngle switch
        {
            >= -22.5f and <= 22.5f => "Avanco",
            > 22.5f and <= 67.5f => "Diag-Dir",
            > 67.5f and <= 112.5f => "Strafe-Dir",
            > 112.5f and <= 157.5f => "Recuo-Dir",
            < -22.5f and >= -67.5f => "Diag-Esq",
            < -67.5f and >= -112.5f => "Strafe-Esq",
            < -112.5f and >= -157.5f => "Recuo-Esq",
            _ => "Recuo"
        };

        string speedName = SpeedTier switch
        {
            MicroSpeedTier.Run => "250u",
            MicroSpeedTier.WalkShift => "Shift",
            MicroSpeedTier.Crouch => "Duck",
            _ => "Run"
        };

        string extra = IsJump ? "+Jump" : "";
        return $"{dirName}({speedName}{extra})";
    }

"""
step_helper_crlf = step_helper.replace('\n', '\r\n')

target_step = '    public readonly (float ForwardMove, float SideMove) ToBotRelativeMoves(float botYawDegrees)'
assert target_step in text, 'target_step not found'
text = text.replace(target_step, step_helper_crlf + target_step, 1)

# 2. Add IDisposable and fields to MicroMoveEngine
target_class = 'public class MicroMoveEngine : IMicroMovePredictor\r\n{'
if target_class not in text:
    target_class = 'public class MicroMoveEngine : IMicroMovePredictor\n{'

rep_class = """public class MicroMoveEngine : IMicroMovePredictor, IDisposable
{
    public CsBotManagerPlugin? Plugin { get; set; }
    private readonly Dictionary<(int Slot, string ChokepointName), float> _hotzoneEntryTimes = new();
    private readonly Dictionary<(int Slot, string ChokepointName), float> _hotzoneCooldowns = new();
    private readonly Dictionary<int, (Vector Pos, float SinceTime)> _stationaryTrackers = new();"""

text = text.replace(target_class, rep_class.replace('\n', '\r\n'), 1)

# 3. Add Dispose method and clear dicts in ResetRound
target_reset = """        _lastDebugLogTime.Clear();
        _tickCounter = 0;
    }"""
target_reset_crlf = target_reset.replace('\n', '\r\n')

rep_reset = """        _lastDebugLogTime.Clear();
        _hotzoneEntryTimes.Clear();
        _hotzoneCooldowns.Clear();
        _stationaryTrackers.Clear();
        _tickCounter = 0;
    }

    public void Dispose()
    {
        if (_onnxWatcher != null)
        {
            try
            {
                _onnxWatcher.EnableRaisingEvents = false;
                _onnxWatcher.Dispose();
            }
            catch { }
        }
        lock (_onnxLock)
        {
            _onnxSession?.Dispose();
            _onnxSession = null;
        }
    }"""
rep_reset_crlf = rep_reset.replace('\n', '\r\n')

if target_reset_crlf in text:
    text = text.replace(target_reset_crlf, rep_reset_crlf, 1)
elif target_reset in text:
    text = text.replace(target_reset, rep_reset, 1)
else:
    raise AssertionError('target_reset not found')

# 4. Limit Hotzone_PreMapped in EvaluateLegitimateAdrenalineTrigger
target_hz = """        // 3. Gatilho de "Zona de Perigo" (Hotzone pré-mapeada: boca da Caverna, Palácio, Janela, Conector, Tapete)
        if (currentCp != null)
        {
            return AdrenalineTriggerType.Hotzone_PreMapped;
        }

        return AdrenalineTriggerType.None_SafeTransitGps;"""
target_hz_crlf = target_hz.replace('\n', '\r\n')

rep_hz = """        // 3. Gatilho de "Zona de Perigo" (Hotzone pré-mapeada com limite de 2.0s e cooldown de 8.0s)
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
rep_hz_crlf = rep_hz.replace('\n', '\r\n')

if target_hz_crlf in text:
    text = text.replace(target_hz_crlf, rep_hz_crlf, 1)
elif target_hz in text:
    text = text.replace(target_hz, rep_hz, 1)
else:
    raise AssertionError('target_hz not found')

# 5. Applying active step safeguard
target_step_apply = """            // Se a ação for StandStill (ex: metade final do Counter-Strafe para precisão de tiro)
            if (activeStep.ActionId == 0 || activeStep.SpeedScale <= 0.1f)
            {
                if (_activeMicroMoveCmdIds.TryRemove(slot, out long prevId) && prevId != 0)
                {
                    try { botApi.CancelUsercmdMovement(slot, prevId); } catch { }
                }"""
target_step_apply_crlf = target_step_apply.replace('\n', '\r\n')

rep_step_apply = """            // Se a ação for StandStill (ex: metade final do Counter-Strafe para precisão de tiro)
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
rep_step_apply_crlf = rep_step_apply.replace('\n', '\r\n')

if target_step_apply_crlf in text:
    text = text.replace(target_step_apply_crlf, rep_step_apply_crlf, 1)
elif target_step_apply in text:
    text = text.replace(target_step_apply, rep_step_apply, 1)
else:
    raise AssertionError('target_step_apply not found')

# 6. Stationary tracker in PredictBatch16Hz
target_wp_name = """            string weaponName = pawn.WeaponServices?.ActiveWeapon.Value?.DesignerName ?? "";"""
target_wp_name_crlf = target_wp_name.replace('\n', '\r\n')

rep_wp_name = """            string weaponName = pawn.WeaponServices?.ActiveWeapon.Value?.DesignerName ?? "";

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
rep_wp_name_crlf = rep_wp_name.replace('\n', '\r\n')

if target_wp_name_crlf in text:
    text = text.replace(target_wp_name_crlf, rep_wp_name_crlf, 1)
elif target_wp_name in text:
    text = text.replace(target_wp_name, rep_wp_name, 1)
else:
    raise AssertionError('target_wp_name not found')

# 7. Section 4 Multi-Horizon Anti-Inertia promotion and TR C4 priority
target_sec4 = """            // =========================================================================
            // 4. INFERÊNCIA DIRETA DO TRANSFORMER ONNX (Multi-Horizonte: 0ms, 125ms, 250ms)
            // =========================================================================
            if (onnxRan && (trigger == AdrenalineTriggerType.Vision_Spotted || trigger == AdrenalineTriggerType.Audio_HeardCue))
            {
                for (int a = 0; a < ActionSpaceSize; a++)
                    logits[a] = _onnxBatchOutputLogits[teamBatchIdx, playerRowIdx, 0, a];
                int act0 = SampleActionFromLogits(logits, temperature: 0.85f);

                for (int a = 0; a < ActionSpaceSize; a++)
                    logits[a] = _onnxBatchOutputLogits[teamBatchIdx, playerRowIdx, 1, a];
                int act1 = SampleActionFromLogits(logits, temperature: 0.85f);

                for (int a = 0; a < ActionSpaceSize; a++)
                    logits[a] = _onnxBatchOutputLogits[teamBatchIdx, playerRowIdx, 2, a];
                int act2 = SampleActionFromLogits(logits, temperature: 0.85f);

                traj.Step0_Now = MicroMoveStep.FromActionId(act0, 125f);
                traj.Step1_125ms = MicroMoveStep.FromActionId(act1, 125f);
                traj.Step2_250ms = MicroMoveStep.FromActionId(act2, 125f);
                traj.GeneratedAtTime = currentTime;
                traj.IsOverrideActive = true;
                traj.ActiveBehaviorTag = $"ONNX_{trigger}";
                traj.OverrideExpiresAt = currentTime + 0.25f;

                LogDebugWithCooldown(
                    bot.Slot,
                    currentTime,
                    4.0f,
                    "MLMOVE - ONNX 16HZ",
                    $"`[Modo ONNX Ativo]` **{bot.PlayerName}** ({trigger}, Latência CPU: `{LastInferenceLatencyMs:F2}ms`) -> Horizontes `[{act0}, {act1}, {act2}]`.");
                continue;
            }"""
target_sec4_crlf = target_sec4.replace('\n', '\r\n')

rep_sec4 = """            // =========================================================================
            // 4. INFERÊNCIA DIRETA DO TRANSFORMER ONNX (Multi-Horizonte: 0ms, 125ms, 250ms)
            // =========================================================================
            if (onnxRan && (trigger == AdrenalineTriggerType.Vision_Spotted || trigger == AdrenalineTriggerType.Audio_HeardCue || trigger == AdrenalineTriggerType.Hotzone_PreMapped))
            {
                for (int a = 0; a < ActionSpaceSize; a++)
                    logits[a] = _onnxBatchOutputLogits[teamBatchIdx, playerRowIdx, 0, a];
                int act0 = SampleActionFromLogits(logits, temperature: 0.85f);

                for (int a = 0; a < ActionSpaceSize; a++)
                    logits[a] = _onnxBatchOutputLogits[teamBatchIdx, playerRowIdx, 1, a];
                int act1 = SampleActionFromLogits(logits, temperature: 0.85f);

                for (int a = 0; a < ActionSpaceSize; a++)
                    logits[a] = _onnxBatchOutputLogits[teamBatchIdx, playerRowIdx, 2, a];
                int act2 = SampleActionFromLogits(logits, temperature: 0.85f);

                // CORREÇÃO 1A: Quebra da Armadilha de Inércia do 0ms
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
                traj.Step2_250ms = MicroMoveStep.FromActionId(act2, 125f);
                traj.GeneratedAtTime = currentTime;
                traj.IsOverrideActive = true;
                traj.ActiveBehaviorTag = $"ONNX_{trigger}";
                traj.OverrideExpiresAt = currentTime + 0.25f;

                float botYaw = pawn.EyeAngles?.Y ?? 0.0f;
                string h0 = traj.Step0_Now.ToReadableString(botYaw);
                string h1 = traj.Step1_125ms.ToReadableString(botYaw);
                string h2 = traj.Step2_250ms.ToReadableString(botYaw);

                LogDebugWithCooldown(
                    bot.Slot,
                    currentTime,
                    3.0f,
                    "MLMOVE - ONNX 16HZ",
                    $"`[Modo ONNX Ativo]` **{bot.PlayerName}** acionou `{trigger}` em `({curX:F0}, {curY:F0}, {curZ:F0})` [Mira: Yaw {botYaw:F0}° | CPU: `{LastInferenceLatencyMs:F2}ms`] -> Horizontes: **0ms:** `{h0}` | **125ms:** `{h1}` | **250ms:** `{h2}`");
                continue;
            }"""
rep_sec4_crlf = rep_sec4.replace('\n', '\r\n')

if target_sec4_crlf in text:
    text = text.replace(target_sec4_crlf, rep_sec4_crlf, 1)
elif target_sec4 in text:
    text = text.replace(target_sec4, rep_sec4, 1)
else:
    raise AssertionError('target_sec4 not found')

with open(r'src/CsBotManager/MicroMoveEngine.cs', 'w', encoding='utf-8') as f:
    f.write(text)
print('MicroMoveEngine.cs clean patch applied successfully')
