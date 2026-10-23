with open(r'src/CsBotManager/BotLocomotionDriver.cs', 'r', encoding='utf-8') as f:
    text = f.read()

watchdog_check = """            // =========================================================================
            // WATCHDOG DE GRANADA NA MAO (Correcao 2)
            // =========================================================================
            var activeWp = pawn.WeaponServices?.ActiveWeapon.Value;
            string currentWpName = activeWp?.DesignerName ?? "";
            bool holdingNade = IsGrenadeWeapon(currentWpName);

            if (holdingNade)
            {
                if (!_grenadeHoldStartTime.TryGetValue(slot, out float gStart))
                {
                    _grenadeHoldStartTime[slot] = currentTime;
                }
                else if ((currentTime - gStart) >= 2.2f || bot.IsEnemyVisible)
                {
                    ForceSwitchToBestCombatWeapon(controller);
                    _grenadeHoldStartTime.TryRemove(slot, out _);
                }
            }
            else
            {
                _grenadeHoldStartTime.TryRemove(slot, out _);
            }
"""
watchdog_check_crlf = watchdog_check.replace('\n', '\r\n')

target_loc = '            float curZ = pawn.AbsOrigin.Z;\r\n'
if target_loc not in text:
    target_loc = '            float curZ = pawn.AbsOrigin.Z;\n'

assert target_loc in text, 'target_loc not found'
text = text.replace(target_loc, target_loc + '\r\n' + watchdog_check_crlf, 1)

old_micro_block = """            var microTraj = MicroMoveEngine?.GetTrajectory(slot);
            if (microTraj != null && microTraj.IsOverrideActive && currentTime <= microTraj.OverrideExpiresAt)
            {
                state.LastCheckX = curX;
                state.LastCheckY = curY;
                state.LastCheckTime = currentTime;
                state.StuckCount = 0;
                continue;
            }"""

new_micro_block = """            var microTraj = MicroMoveEngine?.GetTrajectory(slot);
            if (microTraj != null && microTraj.IsOverrideActive && currentTime <= microTraj.OverrideExpiresAt)
            {
                float dxTarget = curX - state.TargetX;
                float dyTarget = curY - state.TargetY;
                float dzTarget = curZ - state.TargetZ;
                float distSqToTarget = (dxTarget * dxTarget) + (dyTarget * dyTarget) + (dzTarget * dzTarget);
                bool isStandStill = (microTraj.Step0_Now.ActionId == 0 || microTraj.Step0_Now.SpeedScale <= 0.1f);
                bool hasBomb = HasC4(controller);

                // Correcao 1B: Se a micro-acao do ONNX for Parado (0u) e o bot precisa andar sem ver inimigos, nao pula o NavMesh!
                if (isStandStill && !bot.IsEnemyVisible && (hasBomb || distSqToTarget > (85.0f * 85.0f)))
                {
                    // Deixa o NavMesh conduzir o bot sem ficar congelado
                }
                else
                {
                    state.LastCheckX = curX;
                    state.LastCheckY = curY;
                    state.LastCheckTime = currentTime;
                    state.StuckCount = 0;
                    continue;
                }
            }"""

old_micro_block_crlf = old_micro_block.replace('\n', '\r\n')
new_micro_block_crlf = new_micro_block.replace('\n', '\r\n')

if old_micro_block_crlf in text:
    text = text.replace(old_micro_block_crlf, new_micro_block_crlf, 1)
elif old_micro_block in text:
    text = text.replace(old_micro_block, new_micro_block, 1)
else:
    raise AssertionError('old_micro_block not found')

helpers = """    public static bool IsGrenadeWeapon(string weaponName)
    {
        if (string.IsNullOrEmpty(weaponName)) return false;
        return weaponName.Contains("grenade", StringComparison.OrdinalIgnoreCase) ||
               weaponName.Contains("flashbang", StringComparison.OrdinalIgnoreCase) ||
               weaponName.Contains("molotov", StringComparison.OrdinalIgnoreCase) ||
               weaponName.Contains("incgrenade", StringComparison.OrdinalIgnoreCase) ||
               weaponName.Contains("decoy", StringComparison.OrdinalIgnoreCase);
    }

    public void CheckGrenadeHurtWatchdog(CCSPlayerController controller)
    {
        if (controller == null || !controller.IsValid || !controller.PawnIsAlive) return;
        var pawn = controller.PlayerPawn.Value;
        var activeWeapon = pawn?.WeaponServices?.ActiveWeapon.Value;
        string wName = activeWeapon?.DesignerName ?? "";
        if (IsGrenadeWeapon(wName))
        {
            ForceSwitchToBestCombatWeapon(controller);
            _grenadeHoldStartTime.TryRemove(controller.Slot, out _);
        }
    }

    public void ForceSwitchToBestCombatWeapon(CCSPlayerController controller)
    {
        if (controller == null || !controller.IsValid || !controller.PawnIsAlive) return;
        controller.ExecuteClientCommand("slot1");
        _plugin?.AddRoundTimer(0.15f, () =>
        {
            if (!controller.IsValid || !controller.PawnIsAlive) return;
            var pawn = controller.PlayerPawn.Value;
            var active = pawn?.WeaponServices?.ActiveWeapon.Value?.DesignerName ?? "";
            if (string.IsNullOrEmpty(active) || IsGrenadeWeapon(active) || active.Contains("none", StringComparison.OrdinalIgnoreCase))
            {
                controller.ExecuteClientCommand("slot2");
            }
        });
    }

"""
helpers_crlf = helpers.replace('\n', '\r\n')

target_helper = '    private static float GetBombTimeRemaining()'
assert target_helper in text, 'target_helper not found'
text = text.replace(target_helper, helpers_crlf + target_helper, 1)

with open(r'src/CsBotManager/BotLocomotionDriver.cs', 'w', encoding='utf-8') as f:
    f.write(text)
print('BotLocomotionDriver.cs patched successfully')
