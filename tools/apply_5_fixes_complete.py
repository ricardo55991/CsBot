import os
import re

print("Starting apply_5_fixes_complete.py...")

# ==============================================================================
# 1. ECONOMY MANAGER
# ==============================================================================
econ_path = r'src/CsBotManager/EconomyManager.cs'
with open(econ_path, 'r', encoding='utf-8') as f:
    econ_text = f.read()

# Replace ExecuteDeterministicBuys with the complete deterministic implementation
idx1 = econ_text.find('public void ExecuteDeterministicBuys(')
idx2 = econ_text.find('public static bool HasValuablePrimaryWeapon', idx1)
assert idx1 != -1 and idx2 != -1, f"Could not find ExecuteDeterministicBuys boundaries: idx1={idx1}, idx2={idx2}"

new_buys_impl = """public void ExecuteDeterministicBuys(
        List<CCSPlayerController> bots,
        BuyState buyState,
        CsTeam team,
        RoleManager roleManager,
        TacticalPlan plan,
        BotLocomotionDriver? locomotionDriver = null)
    {
        bool isCt = team == CsTeam.CounterTerrorist;
        bool isRushTactic = plan.RoundTempo == RoundTempo.FAST_CONTACT || plan.TacticName.ToLowerInvariant().Contains("rush");

        if (buyState == BuyState.FULL_BUY)
        {
            TryCoordinateTeamAwpDrop(bots, roleManager, team);
            if (isCt && TeamAverageMoney >= 7500 && _random.Next(100) < 35)
            {
                TryCoordinateDoubleAwpSetup(bots, roleManager, plan, team);
            }
        }

        foreach (var bot in bots)
        {
            if (!bot.IsValid || !bot.IsBot || bot.InGameMoneyServices == null) continue;

            var role = roleManager.GetBotRole(bot) ?? BotRole.Rotator;
            int botMoney = bot.InGameMoneyServices.Account;
            bool alreadyHasPrimary = HasValuablePrimaryWeapon(bot);

            // Se o saldo for alto (>= $4000), trata como FULL_BUY individual mesmo se o buyState do time for ECO/FORCE
            BuyState effectiveBuy = (botMoney >= 4000) ? BuyState.FULL_BUY : ((botMoney >= 1800 && buyState != BuyState.FULL_ECO) ? BuyState.FORCE_BUY : buyState);

            switch (effectiveBuy)
            {
                case BuyState.FULL_BUY:
                    // 1. Colete + Capacete obrigatório ($1000) e Defuser para CT ($400)
                    DeliverArmor(bot, helmet: true, cost: 1000);
                    if (isCt) DeliverDefuser(bot, cost: 400);

                    // 2. Arma Primária obrigatória
                    if (role == BotRole.AWPer)
                    {
                        if (bot.InGameMoneyServices.Account >= 4750 && !HasSpecificWeapon(bot, "awp"))
                        {
                            DeliverItem(bot, "weapon_awp", 4750, isPrimary: true, locomotionDriver);
                        }
                        else if (!alreadyHasPrimary)
                        {
                            string rifle = isCt ? "weapon_m4a1_silencer" : "weapon_ak47";
                            int cost = isCt ? 2900 : 2700;
                            if (bot.InGameMoneyServices.Account >= cost)
                            {
                                DeliverItem(bot, rifle, cost, isPrimary: true, locomotionDriver);
                            }
                        }
                    }
                    else if (!alreadyHasPrimary)
                    {
                        if (isCt)
                        {
                            if (bot.InGameMoneyServices.Account >= 2900)
                            {
                                DeliverItem(bot, "weapon_m4a1_silencer", 2900, isPrimary: true, locomotionDriver);
                            }
                            else if (bot.InGameMoneyServices.Account >= 2050)
                            {
                                DeliverItem(bot, "weapon_famas", 2050, isPrimary: true, locomotionDriver);
                            }
                        }
                        else // TR
                        {
                            if (bot.InGameMoneyServices.Account >= 2700)
                            {
                                DeliverItem(bot, "weapon_ak47", 2700, isPrimary: true, locomotionDriver);
                            }
                            else if (bot.InGameMoneyServices.Account >= 1800)
                            {
                                DeliverItem(bot, "weapon_galilar", 1800, isPrimary: true, locomotionDriver);
                            }
                        }
                    }

                    // 3. Utilitárias táticas
                    EnsureUtility(bot, "weapon_smokegrenade", 300);
                    EnsureUtility(bot, "weapon_flashbang", 200);
                    if (role == BotRole.EntryFragger || role == BotRole.Anchor || role == BotRole.AWPer)
                    {
                        EnsureUtility(bot, isCt ? "weapon_incgrenade" : "weapon_molotov", isCt ? 600 : 400);
                    }
                    else
                    {
                        EnsureUtility(bot, "weapon_hegrenade", 300);
                    }
                    break;

                case BuyState.FORCE_BUY:
                    // Colete leve
                    DeliverArmor(bot, helmet: false, cost: 650);

                    if (!alreadyHasPrimary)
                    {
                        if (isCt)
                        {
                            if (bot.InGameMoneyServices.Account >= 2050)
                            {
                                DeliverItem(bot, "weapon_famas", 2050, isPrimary: true, locomotionDriver);
                            }
                            else if (bot.InGameMoneyServices.Account >= 1250)
                            {
                                DeliverItem(bot, "weapon_mp9", 1250, isPrimary: true, locomotionDriver);
                            }
                            else if (bot.InGameMoneyServices.Account >= 700)
                            {
                                DeliverItem(bot, "weapon_deagle", 700, isPrimary: false, locomotionDriver);
                            }
                        }
                        else // TR
                        {
                            if (bot.InGameMoneyServices.Account >= 1800)
                            {
                                DeliverItem(bot, "weapon_galilar", 1800, isPrimary: true, locomotionDriver);
                            }
                            else if (bot.InGameMoneyServices.Account >= 1050)
                            {
                                DeliverItem(bot, "weapon_mac10", 1050, isPrimary: true, locomotionDriver);
                            }
                            else if (bot.InGameMoneyServices.Account >= 700)
                            {
                                DeliverItem(bot, "weapon_deagle", 700, isPrimary: false, locomotionDriver);
                            }
                        }
                    }

                    EnsureUtility(bot, "weapon_flashbang", 200);
                    break;

                case BuyState.SEMI_BUY:
                    if (botMoney >= 2500)
                    {
                        DeliverArmor(bot, helmet: false, cost: 650);
                        if (isCt && bot.InGameMoneyServices.Account >= 1250)
                            DeliverItem(bot, "weapon_mp9", 1250, isPrimary: true, locomotionDriver);
                        else if (!isCt && bot.InGameMoneyServices.Account >= 1050)
                            DeliverItem(bot, "weapon_mac10", 1050, isPrimary: true, locomotionDriver);
                    }
                    else if (botMoney >= 1200)
                    {
                        if (bot.InGameMoneyServices.Account >= 700)
                            DeliverItem(bot, "weapon_deagle", 700, isPrimary: false, locomotionDriver);
                    }
                    break;

                case BuyState.SEMI_ECO:
                    if (botMoney >= 2000)
                    {
                        if (bot.InGameMoneyServices.Account >= 700)
                            DeliverItem(bot, "weapon_deagle", 700, isPrimary: false, locomotionDriver);
                    }
                    break;

                case BuyState.FULL_ECO:
                default:
                    locomotionDriver?.BotApi?.SetBuySkip(bot.Slot);
                    break;
            }

            // Garante que o bot empunhe a melhor arma de fogo imediatamente
            if (locomotionDriver != null)
            {
                locomotionDriver.ForceEquipBestFirearm(bot);
            }
            else
            {
                EquipBestWeapon(bot);
            }
        }
    }

    private static void DeliverArmor(CCSPlayerController bot, bool helmet, int cost)
    {
        if (bot == null || !bot.IsValid || bot.InGameMoneyServices == null) return;
        var pawn = bot.PlayerPawn.Value;
        if (pawn == null) return;
        var itemServices = pawn.ItemServices as CCSPlayer_ItemServices;

        if (pawn.ArmorValue >= 100 && (!helmet || (itemServices?.HasHelmet ?? false))) return;

        if (bot.InGameMoneyServices.Account >= cost)
        {
            bot.InGameMoneyServices.Account -= cost;
            Utilities.SetStateChanged(bot, "CCSPlayerController", "m_pInGameMoneyServices");
            bot.GiveNamedItem(helmet ? "item_assaultsuit" : "item_kevlar");
        }
    }

    private static void DeliverDefuser(CCSPlayerController bot, int cost = 400)
    {
        if (bot == null || !bot.IsValid || bot.InGameMoneyServices == null) return;
        var pawn = bot.PlayerPawn.Value;
        if (pawn == null) return;
        var itemServices = pawn.ItemServices as CCSPlayer_ItemServices;
        if (itemServices?.HasDefuser ?? false) return;

        if (bot.InGameMoneyServices.Account >= cost)
        {
            bot.InGameMoneyServices.Account -= cost;
            Utilities.SetStateChanged(bot, "CCSPlayerController", "m_pInGameMoneyServices");
            bot.GiveNamedItem("item_defuser");
        }
    }

    private static void DeliverItem(CCSPlayerController bot, string itemName, int cost, bool isPrimary = false, BotLocomotionDriver? locomotionDriver = null)
    {
        if (bot == null || !bot.IsValid || bot.InGameMoneyServices == null) return;
        if (bot.InGameMoneyServices.Account < cost) return;

        if (isPrimary)
        {
            RemovePrimaryWeapons(bot);
        }

        bot.InGameMoneyServices.Account -= cost;
        Utilities.SetStateChanged(bot, "CCSPlayerController", "m_pInGameMoneyServices");
        bot.GiveNamedItem(itemName);

        if (locomotionDriver != null)
        {
            locomotionDriver.ForceEquipBestFirearm(bot);
        }
        else
        {
            EquipBestWeapon(bot);
        }
    }

    """

econ_text = econ_text[:idx1] + new_buys_impl + econ_text[idx2:]
with open(econ_path, 'w', encoding='utf-8') as f:
    f.write(econ_text)
print("EconomyManager.cs updated successfully!")

# ==============================================================================
# 2. OLLAMA IGL SERVICE
# ==============================================================================
igl_path = r'src/CsBotManager/OllamaIglService.cs'
with open(igl_path, 'r', encoding='utf-8') as f:
    igl_text = f.read()

# Update GenerateDeterministicFallbackPlan to rotate tactics and populate rich RawJson
fbp_target = """    public TacticalPlan GenerateDeterministicFallbackPlan(CsTeam team, BuyState buyState, MapProfileManager? mapProfileManager, string? reason = null)
    {
        bool isCt = team == CsTeam.CounterTerrorist;
        string reasonClean = string.IsNullOrEmpty(reason) ? "Deterministic Rule" : reason.Replace("\"", "'").Replace("\\r", " ").Replace("\\n", " ");
        var plan = new TacticalPlan
        {
            TacticName = isCt ? "Defesa Padro 2-1-2" : (buyState == BuyState.FORCE_BUY ? "Rush B com Smoke Janela" : "Execuo A com Domnio Palcio"),
            TacticSummary = isCt ? "Marcao de posies 2 A, 1 Meio e 2 B com pacincia e crossfire" : (buyState == BuyState.FORCE_BUY ? "Entrada rpida na B explorando o apartamento" : "Staging controlado no palcio e rampa A com utilitrias"),
            RoundTempo = (isCt || buyState != BuyState.FORCE_BUY) ? RoundTempo.SLOW_DEFAULT : RoundTempo.FAST_CONTACT,
            StagingDurationSeconds = (isCt || buyState != BuyState.FORCE_BUY) ? 18.0f : 0.0f,
            RawJson = "{\\"fallback\\": true, \\"side\\": \\"" + (isCt ? "CT" : "TR") + "\\", \\"reason\\": \\"" + reasonClean + "\\"}"
        };

        EnsureValidBotOrders(plan, team, mapProfileManager);
        return plan;
    }"""

# Normalize crlf
fbp_idx = igl_text.find('public TacticalPlan GenerateDeterministicFallbackPlan')
assert fbp_idx != -1, "GenerateDeterministicFallbackPlan not found in OllamaIglService"
fbp_end = igl_text.find('\n    }\n}', fbp_idx)
if fbp_end == -1:
    fbp_end = igl_text.find('\r\n    }\r\n}', fbp_idx)

new_fbp = """    public TacticalPlan GenerateDeterministicFallbackPlan(CsTeam team, BuyState buyState, MapProfileManager? mapProfileManager, string? reason = null, int roundNumber = 1)
    {
        bool isCt = team == CsTeam.CounterTerrorist;
        string reasonClean = string.IsNullOrEmpty(reason) ? "Deterministic Rule" : reason.Replace("\"", "'").Replace("\\r", " ").Replace("\\n", " ");

        string tacticName;
        string tacticSummary;
        RoundTempo tempo;
        float stagingDuration;

        if (isCt)
        {
            int ctMod = roundNumber % 3;
            switch (ctMod)
            {
                case 1:
                    tacticName = "Avanço Agressivo Meio";
                    tacticSummary = "Pressão no meio para coleta de informação e first pick antecipado";
                    tempo = RoundTempo.FAST_CONTACT;
                    stagingDuration = 5.0f;
                    break;
                case 2:
                    tacticName = "Stack A / Retake Preparado";
                    tacticSummary = "Foco concentrado no bomb A com âncora solo no B e retake preparado";
                    tempo = RoundTempo.SLOW_DEFAULT;
                    stagingDuration = 15.0f;
                    break;
                case 0:
                default:
                    tacticName = "Defesa Padrão 2-1-2";
                    tacticSummary = "Marcação equilibrada com 2 no A, 1 no meio e 2 no B";
                    tempo = RoundTempo.SLOW_DEFAULT;
                    stagingDuration = 18.0f;
                    break;
            }
        }
        else // TR
        {
            int trMod = roundNumber % 4;
            switch (trMod)
            {
                case 1:
                    tacticName = "Execução A (Palácio / Rampa)";
                    tacticSummary = "Staging coordenado palácio e rampa A com utilitárias e entrada sincronizada";
                    tempo = RoundTempo.SLOW_DEFAULT;
                    stagingDuration = 16.0f;
                    break;
                case 2:
                    tacticName = "Split A (Meio / Palácio / Conector)";
                    tacticSummary = "Avanço pelo meio e conector com pressão simultânea pelo palácio A";
                    tempo = RoundTempo.SLOW_DEFAULT;
                    stagingDuration = 18.0f;
                    break;
                case 3:
                    tacticName = "Split B (Meio / Tapete / L-B)";
                    tacticSummary = "Domínio inicial de meio seguido de pinça rápida no bomb B";
                    tempo = RoundTempo.SLOW_DEFAULT;
                    stagingDuration = 15.0f;
                    break;
                case 0:
                default:
                    tacticName = "Execução B (Tapete / Apartamentos)";
                    tacticSummary = "Execução rápida na B explorando tapete e apartamentos";
                    tempo = RoundTempo.FAST_CONTACT;
                    stagingDuration = 0.0f;
                    break;
            }
        }

        var plan = new TacticalPlan
        {
            TacticName = tacticName,
            TacticSummary = tacticSummary,
            RoundTempo = tempo,
            StagingDurationSeconds = stagingDuration
        };

        EnsureValidBotOrders(plan, team, mapProfileManager);

        plan.RawJson = System.Text.Json.JsonSerializer.Serialize(new
        {
            tacticName = plan.TacticName,
            summary = plan.TacticSummary,
            tempo = plan.RoundTempo.ToString(),
            stagingDuration = plan.StagingDurationSeconds,
            side = isCt ? "CT" : "TR",
            round = roundNumber,
            botOrders = plan.BotOrders,
            fallbackReason = reasonClean
        }, new System.Text.Json.JsonSerializerOptions { WriteIndented = false });

        return plan;
    }"""

igl_text = igl_text[:fbp_idx] + new_fbp + igl_text[fbp_end:]

# Add tactical rotation instructions into Ollama prompt
rot_anchor = 'string historySummary = historySnapshot.Count > 0'
rot_idx = igl_text.find(rot_anchor)
assert rot_idx != -1, "historySummary anchor not found"

rot_rule_code = """            string tacticalRotationRule = isCt
                ? "ROTAÇÃO TÁTICA OBRIGATÓRIA (CT): Alterne rigorosamente entre as táticas: 1. 'Defesa Padrão 2-1-2', 2. 'Avanço Agressivo Meio', 3. 'Stack A / Retake Preparado'. NÃO repita a mesma tática de dois rounds atrás!"
                : "ROTAÇÃO TÁTICA OBRIGATÓRIA (TR): Alterne rigorosamente entre as 4 táticas: 1. 'Execução B (Tapete / Apartamentos)', 2. 'Execução A (Palácio / Rampa)', 3. 'Split A (Meio / Palácio / Conector)', 4. 'Split B (Meio / Tapete / L-B)'. NÃO repita a mesma tática de dois rounds atrás!";
"""
if "tacticalRotationRule" not in igl_text:
    igl_text = igl_text[:rot_idx] + rot_rule_code + igl_text[rot_idx:]
    # inject into prompt
    igl_text = igl_text.replace("- Histrico: {historySummary}", "- Histórico: {historySummary}\\n- {tacticalRotationRule}")
    igl_text = igl_text.replace("- Histórico: {historySummary}", "- Histórico: {historySummary}\\n- {tacticalRotationRule}")

with open(igl_path, 'w', encoding='utf-8') as f:
    f.write(igl_text)
print("OllamaIglService.cs updated successfully!")

# ==============================================================================
# 3. CSBOT MANAGER PLUGIN
# ==============================================================================
plugin_path = r'src/CsBotManager/CsBotManagerPlugin.cs'
with open(plugin_path, 'r', encoding='utf-8') as f:
    plugin_text = f.read()

# Update OnRoundStart to populate _currentPlan and _currentTrPlan immediately at frame 0
round_start_idx = plugin_text.find('_currentPlan.CurrentPhase = RoundPhase.FreezeTime;')
assert round_start_idx != -1, "_currentPlan.CurrentPhase not found in CsBotManagerPlugin"

pop_plans_code = """        var currentPlayersList = GetActivePlayers();
        var humanPl = currentPlayersList.FirstOrDefault(p => !p.IsBot);
        var humTeam = humanPl?.Team ?? CsTeam.CounterTerrorist;
        _currentPlan = _iglService.GenerateDeterministicFallbackPlan(humTeam, _economyManager.CurrentBuyState, _mapProfileManager, "Deterministic Baseline", _currentRound);
        _currentTrPlan = _iglService.GenerateDeterministicFallbackPlan(CsTeam.Terrorist, _economyManager.CurrentBuyState, _mapProfileManager, "Deterministic Baseline", _currentRound);
        _currentPlan.CurrentPhase = RoundPhase.FreezeTime;"""

plugin_text = plugin_text[:round_start_idx] + pop_plans_code + plugin_text[round_start_idx + len('_currentPlan.CurrentPhase = RoundPhase.FreezeTime;'):]

with open(plugin_path, 'w', encoding='utf-8') as f:
    f.write(plugin_text)
print("CsBotManagerPlugin.cs updated successfully!")

# ==============================================================================
# 4. BOT LOCOMOTION DRIVER
# ==============================================================================
driver_path = r'src/CsBotManager/BotLocomotionDriver.cs'
with open(driver_path, 'r', encoding='utf-8') as f:
    driver_text = f.read()

# Add HoldingSinceTime to TrackedBotNavState
if "public float HoldingSinceTime" not in driver_text:
    target_prop = "public bool IsHoldingSpot { get; set; }"
    rep_prop = "public bool IsHoldingSpot { get; set; }\n    public float HoldingSinceTime { get; set; }"
    assert target_prop in driver_text, "IsHoldingSpot not found in TrackedBotNavState"
    driver_text = driver_text.replace(target_prop, rep_prop, 1)

# Add RoundStartTime and _lastHurtTime to BotLocomotionDriver
if "public float RoundStartTime" not in driver_text:
    target_rst = "public float RoundTimeRemaining { get; set; } = 115.0f;"
    rep_rst = "public float RoundTimeRemaining { get; set; } = 115.0f;\n    public float RoundStartTime { get; set; } = 0f;\n    private readonly System.Collections.Concurrent.ConcurrentDictionary<int, float> _lastHurtTime = new();"
    assert target_rst in driver_text, "RoundTimeRemaining not found in BotLocomotionDriver"
    driver_text = driver_text.replace(target_rst, rep_rst, 1)

# Update ResetRound to initialize RoundStartTime and clear hurt times
target_rr = "public void ResetRound()\n    {\n        _botStates.Clear();"
target_rr_crlf = "public void ResetRound()\r\n    {\r\n        _botStates.Clear();"
rep_rr = """public void ResetRound()
    {
        _botStates.Clear();
        RoundStartTime = Server.CurrentTime;
        _lastHurtTime.Clear();"""

if target_rr_crlf in driver_text:
    driver_text = driver_text.replace(target_rr_crlf, rep_rr.replace('\n', '\r\n'), 1)
elif target_rr in driver_text:
    driver_text = driver_text.replace(target_rr, rep_rr, 1)

# Replace ForceSwitchToBestCombatWeapon with ForceEquipBestFirearm
target_fs = "public void ForceSwitchToBestCombatWeapon(CCSPlayerController controller)"
fs_idx = driver_text.find(target_fs)
assert fs_idx != -1, "ForceSwitchToBestCombatWeapon not found"
fs_end = driver_text.find("private static float GetBombTimeRemaining()", fs_idx)
assert fs_end != -1, "GetBombTimeRemaining not found"

new_force_equip = """public void ForceSwitchToBestCombatWeapon(CCSPlayerController controller)
    {
        ForceEquipBestFirearm(controller);
    }

    public void ForceEquipBestFirearm(CCSPlayerController bot)
    {
        if (bot == null || !bot.IsValid || !bot.PawnIsAlive) return;
        var pawn = bot.PlayerPawn.Value;
        if (pawn?.WeaponServices?.MyWeapons == null) return;

        ushort? primaryDefIndex = null;
        ushort? secondaryDefIndex = null;

        foreach (var handle in pawn.WeaponServices.MyWeapons)
        {
            var w = handle.Value;
            if (w == null || !w.IsValid || string.IsNullOrEmpty(w.DesignerName)) continue;
            string dName = w.DesignerName;

            if (CombatAdapter.IsPrimaryWeapon(dName))
            {
                primaryDefIndex = (ushort)w.AttributeManager.Item.ItemDefinitionIndex;
                break;
            }
            else if (CombatAdapter.IsSecondaryWeapon(dName) && !secondaryDefIndex.HasValue)
            {
                secondaryDefIndex = (ushort)w.AttributeManager.Item.ItemDefinitionIndex;
            }
        }

        ushort? targetDef = primaryDefIndex ?? secondaryDefIndex;
        if (targetDef.HasValue)
        {
            var api = BotApi;
            if (api != null)
            {
                api.SwitchBotWeapon(bot.Slot, (int)targetDef.Value);
            }
            else
            {
                bot.ExecuteClientCommand(primaryDefIndex.HasValue ? "slot1" : "slot2");
            }
        }
    }

    """

driver_text = driver_text[:fs_idx] + new_force_equip + driver_text[fs_end:]

# Update CheckGrenadeEquipWatchdog and CheckGrenadeHurtWatchdog
cg_target = "public void CheckGrenadeEquipWatchdog(CCSPlayerController controller, float currentTime)"
cg_idx = driver_text.find(cg_target)
assert cg_idx != -1, "CheckGrenadeEquipWatchdog not found"
cg_end = driver_text.find("public void ForceSwitchToBestCombatWeapon", cg_idx)
assert cg_end != -1, "ForceSwitchToBestCombatWeapon after watchdog not found"

new_watchdogs = """public void CheckGrenadeEquipWatchdog(CCSPlayerController controller, float currentTime)
    {
        if (controller == null || !controller.IsValid || !controller.PawnIsAlive) return;
        var pawn = controller.PlayerPawn.Value;
        var activeWeapon = pawn?.WeaponServices?.ActiveWeapon.Value;
        string wName = activeWeapon?.DesignerName ?? "";
        int slot = controller.Slot;

        // Proibir puxar knife com inimigos vivos / C4 plantada pós-10s do round
        bool isKnife = wName.Contains("knife", StringComparison.OrdinalIgnoreCase) || wName.Contains("bayonet", StringComparison.OrdinalIgnoreCase);
        if (isKnife && (_isBombPlanted || (currentTime - RoundStartTime >= 10.0f) || RoundTimeRemaining <= 105.0f))
        {
            ForceEquipBestFirearm(controller);
            return;
        }

        bool isGrenade = IsGrenadeWeapon(wName);
        if (isGrenade)
        {
            bool wasHurtRecently = _lastHurtTime.TryGetValue(slot, out float hTime) && (currentTime - hTime) <= 3.0f;
            if (!_grenadeHoldStartTime.TryGetValue(slot, out float gStart))
            {
                _grenadeHoldStartTime[slot] = currentTime;
            }
            else
            {
                float heldTime = currentTime - gStart;
                bool enemyVisible = pawn?.Bot?.IsEnemyVisible ?? false;

                if (heldTime >= 2.0f || enemyVisible || wasHurtRecently)
                {
                    ForceEquipBestFirearm(controller);

                    if (heldTime >= 2.8f || enemyVisible || wasHurtRecently)
                    {
                        try
                        {
                            activeWeapon?.Remove();
                        }
                        catch { }
                        ForceEquipBestFirearm(controller);
                        _grenadeHoldStartTime.TryRemove(slot, out _);
                    }
                }
            }
        }
        else
        {
            _grenadeHoldStartTime.TryRemove(slot, out _);
        }
    }

    public void CheckGrenadeHurtWatchdog(CCSPlayerController controller)
    {
        if (controller == null || !controller.IsValid || !controller.PawnIsAlive) return;
        _lastHurtTime[controller.Slot] = Server.CurrentTime;

        var pawn = controller.PlayerPawn.Value;
        var activeWeapon = pawn?.WeaponServices?.ActiveWeapon.Value;
        string wName = activeWeapon?.DesignerName ?? "";
        if (IsGrenadeWeapon(wName))
        {
            try
            {
                activeWeapon?.Remove();
            }
            catch { }
            ForceEquipBestFirearm(controller);
            _grenadeHoldStartTime.TryRemove(controller.Slot, out _);
        }
    }

    """

driver_text = driver_text[:cg_idx] + new_watchdogs + driver_text[cg_end:]

# Update ThrowUtility to switch to best firearm after 0.80s + 0.35s
tu_target = "api.InjectUsercmd(controller.Slot, IN_ATTACK, 250);\n                    }"
tu_target_crlf = "api.InjectUsercmd(controller.Slot, IN_ATTACK, 250);\r\n                    }"
rep_tu = """api.InjectUsercmd(controller.Slot, IN_ATTACK, 250);
                    }

                    _plugin?.AddRoundTimer(0.35f, () =>
                    {
                        if (controller.IsValid && controller.PawnIsAlive)
                        {
                            ForceEquipBestFirearm(controller);
                        }
                    });"""

if tu_target_crlf in driver_text:
    driver_text = driver_text.replace(tu_target_crlf, rep_tu.replace('\n', '\r\n'), 1)
elif tu_target in driver_text:
    driver_text = driver_text.replace(tu_target, rep_tu, 1)

tu_fb_target = "controller.ExecuteClientCommand(\"-attack\");\n            });"
tu_fb_target_crlf = "controller.ExecuteClientCommand(\"-attack\");\r\n            });"
rep_tu_fb = """controller.ExecuteClientCommand("-attack");
                ForceEquipBestFirearm(controller);
            });"""

if tu_fb_target_crlf in driver_text:
    driver_text = driver_text.replace(tu_fb_target_crlf, rep_tu_fb.replace('\n', '\r\n'), 1)
elif tu_fb_target in driver_text:
    driver_text = driver_text.replace(tu_fb_target, rep_tu_fb, 1)

# In UpdateTick: add HoldingSinceTime tracking, 14s expiration, TR <= 45s urgency, and CT retake urgency
dest_target = "// Chegou ao spot alvo (Ponto 2: Crava o pixel e congela movimentao de patrulha)\n                state.HasReachedDestination = true;\n                state.IsHoldingSpot = true;"
dest_target_crlf = "// Chegou ao spot alvo (Ponto 2: Crava o pixel e congela movimentao de patrulha)\r\n                state.HasReachedDestination = true;\r\n                state.IsHoldingSpot = true;"

# Let's search by string 'state.HasReachedDestination = true;' inside UpdateTick
dt_idx = driver_text.find("state.HasReachedDestination = true;")
assert dt_idx != -1, "state.HasReachedDestination = true not found"
dt_sub = driver_text[dt_idx:dt_idx+150]

rep_dt_sub = """state.HasReachedDestination = true;
                if (!state.IsHoldingSpot)
                {
                    state.IsHoldingSpot = true;
                    state.HoldingSinceTime = currentTime;
                }"""

# Replace the first two lines
driver_text = driver_text[:dt_idx] + rep_dt_sub + driver_text[dt_idx + len("state.HasReachedDestination = true;\n                state.IsHoldingSpot = true;") if "state.HasReachedDestination = true;\n                state.IsHoldingSpot = true;" in driver_text else dt_idx + len("state.HasReachedDestination = true;\r\n                state.IsHoldingSpot = true;"):]

# Now right before destination check (at distToTargetSq <= 85*85), inject holding expiration, TR plant urgency, CT retake urgency
chk_target = "float distSq = (dx * dx) + (dy * dy) + (dz * dz);"
chk_idx = driver_text.find(chk_target)
assert chk_idx != -1, "chk_target not found"

urgency_and_expiration = """            // =========================================================================
            // URGENCIA CRITICA C4 TR (RoundTimeRemaining <= 45s) E RETAKE CT (Correcao 3)
            // =========================================================================
            if (controller.Team == CsTeam.Terrorist && RoundTimeRemaining <= 45.0f && !_isBombPlanted)
            {
                if (state.IsHoldingSpot)
                {
                    state.IsHoldingSpot = false;
                    state.HasReachedDestination = false;
                    state.HoldingSinceTime = 0f;
                    bot.IsStopping = false;
                    bot.WaitTimer.Duration = 0f;
                    bot.WaitTimer.Timestamp = 0f;
                }

                Vector? targetSitePos = null;
                var allPls = Utilities.GetPlayers();
                var c4Holder = allPls.FirstOrDefault(p => p != null && p.IsValid && p.PawnIsAlive && p.Team == CsTeam.Terrorist && HasC4(p));
                if (c4Holder != null && c4Holder.Slot != controller.Slot && c4Holder.PlayerPawn.Value?.AbsOrigin != null)
                {
                    targetSitePos = c4Holder.PlayerPawn.Value.AbsOrigin;
                }
                else
                {
                    string targetSite = (_plugin?.CurrentPlan?.TacticName ?? "").Contains("B", StringComparison.OrdinalIgnoreCase) ? "B" : "A";
                    targetSitePos = targetSite == "B" ? new Vector(-220.0f, 580.0f, -160.0f) : new Vector(-1280.0f, -420.0f, -160.0f);
                }

                if (targetSitePos != null && pawn.AbsOrigin != null && (targetSitePos - pawn.AbsOrigin).Length() > 150f)
                {
                    NavigateToPosition(controller, targetSitePos.X, targetSitePos.Y, targetSitePos.Z, null, null, null, hurry: true, stance: EngagementStance.AGGRESSIVE_POKE, priority: BotOrderPriority.Critical_SaveOrPivot);
                }
            }

            if (controller.Team == CsTeam.CounterTerrorist && _isBombPlanted)
            {
                Vector? bombPos = _bombPosition;
                if (bombPos == null)
                {
                    var pC4 = Utilities.FindAllEntitiesByDesignerName<CPlantedC4>("planted_c4").FirstOrDefault(c => c.IsValid && c.AbsOrigin != null);
                    if (pC4 != null) bombPos = pC4.AbsOrigin;
                }

                if (bombPos != null && pawn.AbsOrigin != null)
                {
                    float distToBomb = (bombPos - pawn.AbsOrigin).Length();
                    if (distToBomb > 350.0f)
                    {
                        if (state.IsHoldingSpot)
                        {
                            state.IsHoldingSpot = false;
                            state.HasReachedDestination = false;
                            state.HoldingSinceTime = 0f;
                        }
                        bot.IsStopping = false;
                        bot.WaitTimer.Duration = 0f;
                        bot.WaitTimer.Timestamp = 0f;
                        NavigateToPosition(controller, bombPos.X, bombPos.Y, bombPos.Z, null, null, null, hurry: true, stance: EngagementStance.AGGRESSIVE_POKE, priority: BotOrderPriority.Critical_SaveOrPivot);
                    }
                }
            }

            // =========================================================================
            // EXPIRACAO RIGOROSA DE ISHOLDINGSPOT (14.0s max ou 6.0s se sem inimigos)
            // =========================================================================
            if (state.IsHoldingSpot)
            {
                float holdDuration = currentTime - state.HoldingSinceTime;
                float maxHoldTime = (!bot.IsEnemyVisible || state.Stance == EngagementStance.AGGRESSIVE_POKE) ? 6.0f : 14.0f;

                if (state.HoldingSinceTime > 0f && holdDuration >= maxHoldTime)
                {
                    state.IsHoldingSpot = false;
                    state.HasReachedDestination = false;
                    state.HoldingSinceTime = 0f;
                    bot.IsStopping = false;
                    bot.WaitTimer.Duration = 0f;
                    bot.WaitTimer.Timestamp = 0f;

                    string targetSite = (_plugin?.CurrentPlan?.TacticName ?? "").Contains("B", StringComparison.OrdinalIgnoreCase) ? "B" : "A";
                    Vector nextTarget = targetSite == "B" ? new Vector(-220.0f, 580.0f, -160.0f) : new Vector(-1280.0f, -420.0f, -160.0f);
                    NavigateToPosition(controller, nextTarget.X, nextTarget.Y, nextTarget.Z, null, null, null, hurry: true, stance: EngagementStance.AGGRESSIVE_POKE, priority: BotOrderPriority.Medium_Tactical);
                }
            }

            """

driver_text = driver_text[:chk_idx] + urgency_and_expiration + driver_text[chk_idx:]

with open(driver_path, 'w', encoding='utf-8') as f:
    f.write(driver_text)
print("BotLocomotionDriver.cs updated successfully!")

print("ALL 4 FILES UPDATED!")
