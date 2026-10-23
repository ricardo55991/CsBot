# 1. Update OllamaIglService.cs
with open(r'src/CsBotManager/OllamaIglService.cs', 'r', encoding='utf-8') as f:
    text_igl = f.read()

target_to = 'Timeout = TimeSpan.FromMilliseconds(4500)'
rep_to = 'Timeout = TimeSpan.FromSeconds(7.5)'
assert target_to in text_igl, 'target_to not found'
text_igl = text_igl.replace(target_to, rep_to, 1)

with open(r'src/CsBotManager/OllamaIglService.cs', 'w', encoding='utf-8') as f:
    f.write(text_igl)
print('OllamaIglService.cs updated with 7.5s timeout')

# 2. Update BotLocomotionDriver.cs
with open(r'src/CsBotManager/BotLocomotionDriver.cs', 'r', encoding='utf-8') as f:
    text_driver = f.read()

watchdog_method = """    public void CheckGrenadeEquipWatchdog(CCSPlayerController controller, float currentTime)
    {
        if (controller == null || !controller.IsValid || !controller.PawnIsAlive) return;
        var pawn = controller.PlayerPawn.Value;
        var activeWeapon = pawn?.WeaponServices?.ActiveWeapon.Value;
        string wName = activeWeapon?.DesignerName ?? "";
        bool isGrenade = IsGrenadeWeapon(wName);
        int slot = controller.Slot;

        if (isGrenade)
        {
            if (!_grenadeHoldStartTime.TryGetValue(slot, out float gStart))
            {
                _grenadeHoldStartTime[slot] = currentTime;
            }
            else if ((currentTime - gStart) >= 2.2f || (pawn?.Bot?.IsEnemyVisible ?? false))
            {
                ForceSwitchToBestCombatWeapon(controller);
                _grenadeHoldStartTime.TryRemove(slot, out _);
            }
        }
        else
        {
            _grenadeHoldStartTime.TryRemove(slot, out _);
        }
    }

"""
watchdog_method_crlf = watchdog_method.replace('\n', '\r\n')

target_dm = '    public void CheckGrenadeHurtWatchdog(CCSPlayerController controller)'
assert target_dm in text_driver, 'target_dm not found'
text_driver = text_driver.replace(target_dm, watchdog_method_crlf + target_dm, 1)

with open(r'src/CsBotManager/BotLocomotionDriver.cs', 'w', encoding='utf-8') as f:
    f.write(text_driver)
print('BotLocomotionDriver.cs updated with CheckGrenadeEquipWatchdog')

# 3. Update CsBotManagerPlugin.cs
with open(r'src/CsBotManager/CsBotManagerPlugin.cs', 'r', encoding='utf-8') as f:
    text_plugin = f.read()

# In OnTick, call CheckGrenadeEquipWatchdog for all aliveBots
target_ontick_loop = """        if (!_isFreezeTime)
        {
            var aliveBots = Utilities.GetPlayers().Where(p => p != null && p.IsValid && p.IsBot && p.PawnIsAlive).ToList();
            _mobilityController?.UpdateTick(currentTime, _currentPlan, aliveBots);
            _combatAdapter?.UpdateTick(currentTime, aliveBots);
        }"""

rep_ontick_loop = """        if (!_isFreezeTime)
        {
            var aliveBots = Utilities.GetPlayers().Where(p => p != null && p.IsValid && p.IsBot && p.PawnIsAlive).ToList();
            foreach (var b in aliveBots)
            {
                _locomotionDriver?.CheckGrenadeEquipWatchdog(b, currentTime);
            }
            _mobilityController?.UpdateTick(currentTime, _currentPlan, aliveBots);
            _combatAdapter?.UpdateTick(currentTime, aliveBots);
        }"""

target_ontick_loop_crlf = target_ontick_loop.replace('\n', '\r\n')
rep_ontick_loop_crlf = rep_ontick_loop.replace('\n', '\r\n')

if target_ontick_loop_crlf in text_plugin:
    text_plugin = text_plugin.replace(target_ontick_loop_crlf, rep_ontick_loop_crlf, 1)
elif target_ontick_loop in text_plugin:
    text_plugin = text_plugin.replace(target_ontick_loop, rep_ontick_loop, 1)
else:
    raise AssertionError('target_ontick_loop not found')

# Update catch (OperationCanceledException) in Task.Run
target_cancel1 = """                    catch (OperationCanceledException) { return; }
                    catch (Exception ex)
                    {
                        ctPlan = _iglService.GenerateDeterministicFallbackPlan(CsTeam.CounterTerrorist, currentBuyState, _mapProfileManager, ex.Message);
                    }"""

rep_cancel1 = """                    catch (OperationCanceledException) when (token.IsCancellationRequested) { return; }
                    catch (Exception ex)
                    {
                        ctPlan = _iglService.GenerateDeterministicFallbackPlan(CsTeam.CounterTerrorist, currentBuyState, _mapProfileManager, ex.Message);
                    }"""

target_cancel1_crlf = target_cancel1.replace('\n', '\r\n')
rep_cancel1_crlf = rep_cancel1.replace('\n', '\r\n')

if target_cancel1_crlf in text_plugin:
    text_plugin = text_plugin.replace(target_cancel1_crlf, rep_cancel1_crlf, 1)
elif target_cancel1 in text_plugin:
    text_plugin = text_plugin.replace(target_cancel1, rep_cancel1, 1)
else:
    raise AssertionError('target_cancel1 not found')

target_cancel2 = """                    catch (OperationCanceledException) { return; }
                    catch (Exception ex)
                    {
                        trPlan = _iglService.GenerateDeterministicFallbackPlan(CsTeam.Terrorist, currentBuyState, _mapProfileManager, ex.Message);
                    }"""

rep_cancel2 = """                    catch (OperationCanceledException) when (token.IsCancellationRequested) { return; }
                    catch (Exception ex)
                    {
                        trPlan = _iglService.GenerateDeterministicFallbackPlan(CsTeam.Terrorist, currentBuyState, _mapProfileManager, ex.Message);
                    }"""

target_cancel2_crlf = target_cancel2.replace('\n', '\r\n')
rep_cancel2_crlf = rep_cancel2.replace('\n', '\r\n')

if target_cancel2_crlf in text_plugin:
    text_plugin = text_plugin.replace(target_cancel2_crlf, rep_cancel2_crlf, 1)
elif target_cancel2 in text_plugin:
    text_plugin = text_plugin.replace(target_cancel2, rep_cancel2, 1)
else:
    raise AssertionError('target_cancel2 not found')

with open(r'src/CsBotManager/CsBotManagerPlugin.cs', 'w', encoding='utf-8') as f:
    f.write(text_plugin)
print('CsBotManagerPlugin.cs updated successfully')
