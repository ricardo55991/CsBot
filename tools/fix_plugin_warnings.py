with open(r'src/CsBotManager/CsBotManagerPlugin.cs', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix warning CS8604
target_w1 = """            _telemetryLogger?.OnRoundStart(
                _currentRound,
                _ctScore,
                _trScore,
                humanTeam == CsTeam.CounterTerrorist ? _economyManager.CurrentBuyState : enemyBuyState,
                humanTeam == CsTeam.Terrorist ? _economyManager.CurrentBuyState : enemyBuyState,
                _currentPlan,
                combinedIglJson,
                players);"""

rep_w1 = """            _telemetryLogger?.OnRoundStart(
                _currentRound,
                _ctScore,
                _trScore,
                humanTeam == CsTeam.CounterTerrorist ? _economyManager.CurrentBuyState : enemyBuyState,
                humanTeam == CsTeam.Terrorist ? _economyManager.CurrentBuyState : enemyBuyState,
                _currentPlan ?? new TacticalPlan(),
                combinedIglJson,
                players);"""

target_w1_crlf = target_w1.replace('\n', '\r\n')
rep_w1_crlf = rep_w1.replace('\n', '\r\n')

if target_w1_crlf in text:
    text = text.replace(target_w1_crlf, rep_w1_crlf, 1)
elif target_w1 in text:
    text = text.replace(target_w1, rep_w1, 1)

# Fix warning CS8602
target_w2 = """            float dist = 0.0f;
            if (victim.PlayerPawn.Value?.AbsOrigin != null && attacker.PlayerPawn.Value?.AbsOrigin != null)
            {
                var attackerPos = attacker.PlayerPawn.Value.AbsOrigin;
                dist = (victim.PlayerPawn.Value.AbsOrigin - attackerPos).Length();

                if (!_lastHurtThreatAlertTime.TryGetValue(attacker.Slot, out float lastAlert) || (Server.CurrentTime - lastAlert) >= 1.0f)
                {
                    _lastHurtThreatAlertTime[attacker.Slot] = Server.CurrentTime;
                    _locomotionDriver.AlertNearbyTeammatesOfThreat(attackerPos, victim.Slot, victim.Team, 950f);
                }
            }"""

rep_w2 = """            float dist = 0.0f;
            var victimPawn = victim.PlayerPawn.Value;
            var attackerPawn = attacker.PlayerPawn.Value;
            if (victimPawn?.AbsOrigin != null && attackerPawn?.AbsOrigin != null)
            {
                var attackerPos = attackerPawn.AbsOrigin;
                dist = (victimPawn.AbsOrigin - attackerPos).Length();

                if (!_lastHurtThreatAlertTime.TryGetValue(attacker.Slot, out float lastAlert) || (Server.CurrentTime - lastAlert) >= 1.0f)
                {
                    _lastHurtThreatAlertTime[attacker.Slot] = Server.CurrentTime;
                    _locomotionDriver.AlertNearbyTeammatesOfThreat(attackerPos, victim.Slot, victim.Team, 950f);
                }
            }"""

target_w2_crlf = target_w2.replace('\n', '\r\n')
rep_w2_crlf = rep_w2.replace('\n', '\r\n')

if target_w2_crlf in text:
    text = text.replace(target_w2_crlf, rep_w2_crlf, 1)
elif target_w2 in text:
    text = text.replace(target_w2, rep_w2, 1)

with open(r'src/CsBotManager/CsBotManagerPlugin.cs', 'w', encoding='utf-8') as f:
    f.write(text)
print('Warnings in CsBotManagerPlugin.cs fixed')
