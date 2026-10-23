with open(r'src/CsBotManager/EconomyManager.cs', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add EquipBestWeapon right above RemovePrimaryWeapons
equip_helper = """    public static void EquipBestWeapon(CCSPlayerController bot)
    {
        if (bot == null || !bot.IsValid || !bot.PawnIsAlive) return;
        bot.ExecuteClientCommand("slot1");
        Server.NextFrame(() =>
        {
            if (!bot.IsValid || !bot.PawnIsAlive) return;
            var pawn = bot.PlayerPawn.Value;
            var active = pawn?.WeaponServices?.ActiveWeapon.Value?.DesignerName ?? "";
            if (string.IsNullOrEmpty(active) || active.Contains("none", StringComparison.OrdinalIgnoreCase) || BotLocomotionDriver.IsGrenadeWeapon(active))
            {
                bot.ExecuteClientCommand("slot2");
            }
        });
    }

"""
equip_helper_crlf = equip_helper.replace('\n', '\r\n')

target_rpm = '    public static void RemovePrimaryWeapons(CCSPlayerController player)'
assert target_rpm in text, 'target_rpm not found'
text = text.replace(target_rpm, equip_helper_crlf + target_rpm, 1)

# 2. Add EquipBestWeapon inside RemovePrimaryWeapons
target_rpm_end = """                if (CombatAdapter.IsPrimaryWeapon(w.DesignerName))
                {
                    w.Remove();
                }
            }
        }
    }"""
target_rpm_end_crlf = target_rpm_end.replace('\n', '\r\n')

replacement_rpm_end = """                if (CombatAdapter.IsPrimaryWeapon(w.DesignerName))
                {
                    w.Remove();
                }
            }
        }
        EquipBestWeapon(player);
    }"""
replacement_rpm_end_crlf = replacement_rpm_end.replace('\n', '\r\n')

if target_rpm_end_crlf in text:
    text = text.replace(target_rpm_end_crlf, replacement_rpm_end_crlf, 1)
elif target_rpm_end in text:
    text = text.replace(target_rpm_end, replacement_rpm_end, 1)
else:
    raise AssertionError('target_rpm_end not found')

# 3. Add EquipBestWeapon to SanitizeNativePurchasesAndRefund
target_san = """            if (refundAmount > 0 && bot.InGameMoneyServices != null)
            {
                bot.InGameMoneyServices.Account += refundAmount;
                Utilities.SetStateChanged(bot, "CCSPlayerController", "m_pInGameMoneyServices");
            }
        }
    }"""
target_san_crlf = target_san.replace('\n', '\r\n')

replacement_san = """            if (refundAmount > 0 && bot.InGameMoneyServices != null)
            {
                bot.InGameMoneyServices.Account += refundAmount;
                Utilities.SetStateChanged(bot, "CCSPlayerController", "m_pInGameMoneyServices");
            }
            EquipBestWeapon(bot);
        }
    }"""
replacement_san_crlf = replacement_san.replace('\n', '\r\n')

if target_san_crlf in text:
    text = text.replace(target_san_crlf, replacement_san_crlf, 1)
elif target_san in text:
    text = text.replace(target_san, replacement_san, 1)
else:
    raise AssertionError('target_san not found')

# 4. Add EquipBestWeapon to EnsureAwp
target_awp = """            if (bot.InGameMoneyServices.Account >= 4750)
            {
                RemovePrimaryWeapons(bot);
                bot.InGameMoneyServices.Account -= 4750;
                Utilities.SetStateChanged(bot, "CCSPlayerController", "m_pInGameMoneyServices");
                bot.GiveNamedItem("weapon_awp");
            }
            else
            {
                bot.ExecuteClientCommand("buy awp");
            }
        }
    }"""
target_awp_crlf = target_awp.replace('\n', '\r\n')

replacement_awp = """            if (bot.InGameMoneyServices.Account >= 4750)
            {
                RemovePrimaryWeapons(bot);
                bot.InGameMoneyServices.Account -= 4750;
                Utilities.SetStateChanged(bot, "CCSPlayerController", "m_pInGameMoneyServices");
                bot.GiveNamedItem("weapon_awp");
                EquipBestWeapon(bot);
            }
            else
            {
                bot.ExecuteClientCommand("buy awp");
                EquipBestWeapon(bot);
            }
        }
        else
        {
            EquipBestWeapon(bot);
        }
    }"""
replacement_awp_crlf = replacement_awp.replace('\n', '\r\n')

if target_awp_crlf in text:
    text = text.replace(target_awp_crlf, replacement_awp_crlf, 1)
elif target_awp in text:
    text = text.replace(target_awp, replacement_awp, 1)
else:
    raise AssertionError('target_awp not found')

# 5. Add EquipBestWeapon in EnsureUtility
target_util = """                bot.InGameMoneyServices.Account -= cost;
                Utilities.SetStateChanged(bot, "CCSPlayerController", "m_pInGameMoneyServices");
                bot.GiveNamedItem(weaponName);
            }
            else
            {
                bot.ExecuteClientCommand($"buy {subName}");
            }
        }
    }"""
target_util_crlf = target_util.replace('\n', '\r\n')

replacement_util = """                bot.InGameMoneyServices.Account -= cost;
                Utilities.SetStateChanged(bot, "CCSPlayerController", "m_pInGameMoneyServices");
                bot.GiveNamedItem(weaponName);
                EquipBestWeapon(bot);
            }
            else
            {
                bot.ExecuteClientCommand($"buy {subName}");
            }
        }
    }"""
replacement_util_crlf = replacement_util.replace('\n', '\r\n')

if target_util_crlf in text:
    text = text.replace(target_util_crlf, replacement_util_crlf, 1)
elif target_util in text:
    text = text.replace(target_util, replacement_util, 1)
else:
    raise AssertionError('target_util not found')

# 6. AWPer check in ExecuteDeterministicBuys + EquipBestWeapon at end of bot loop
target_buy_awp = """                case BuyState.FULL_BUY:
                    if (role == BotRole.AWPer)
                    {
                        EnsureAwp(bot);
                        if (botMoney >= 1000) bot.ExecuteClientCommand("buy vesthelm");
                        else if (botMoney >= 650) bot.ExecuteClientCommand("buy vest");
                        if (isCt && botMoney >= 400) bot.ExecuteClientCommand("buy defuser");
                    }"""
target_buy_awp_crlf = target_buy_awp.replace('\n', '\r\n')

replacement_buy_awp = """                case BuyState.FULL_BUY:
                    if (role == BotRole.AWPer)
                    {
                        if (botMoney >= 4750)
                        {
                            EnsureAwp(bot);
                            if (botMoney >= 1000) bot.ExecuteClientCommand("buy vesthelm");
                            else if (botMoney >= 650) bot.ExecuteClientCommand("buy vest");
                            if (isCt && botMoney >= 400) bot.ExecuteClientCommand("buy defuser");
                        }
                        else
                        {
                            // Pistol round ou verba insuficiente para AWP: compra colete e pistola
                            if (botMoney >= 650) bot.ExecuteClientCommand("buy vest");
                            else if (botMoney >= 500) bot.ExecuteClientCommand(isCt ? "buy fiveseven" : "buy tec9");
                            EquipBestWeapon(bot);
                        }
                    }"""
replacement_buy_awp_crlf = replacement_buy_awp.replace('\n', '\r\n')

if target_buy_awp_crlf in text:
    text = text.replace(target_buy_awp_crlf, replacement_buy_awp_crlf, 1)
elif target_buy_awp in text:
    text = text.replace(target_buy_awp, replacement_buy_awp, 1)
else:
    raise AssertionError('target_buy_awp not found')

# Add EquipBestWeapon(bot) at end of bot loop in ExecuteDeterministicBuys
target_bot_loop_end = """                case BuyState.FULL_ECO:
                    // Trava compra nativa para não gastar saldo no Eco
                    locomotionDriver?.BotApi?.SetBuySkip(bot.Slot);
                    break;
            }
        }
    }"""
target_bot_loop_end_crlf = target_bot_loop_end.replace('\n', '\r\n')

replacement_bot_loop_end = """                case BuyState.FULL_ECO:
                    // Trava compra nativa para não gastar saldo no Eco
                    locomotionDriver?.BotApi?.SetBuySkip(bot.Slot);
                    break;
            }
            EquipBestWeapon(bot);
        }
    }"""
replacement_bot_loop_end_crlf = replacement_bot_loop_end.replace('\n', '\r\n')

if target_bot_loop_end_crlf in text:
    text = text.replace(target_bot_loop_end_crlf, replacement_bot_loop_end_crlf, 1)
elif target_bot_loop_end in text:
    text = text.replace(target_bot_loop_end, replacement_bot_loop_end, 1)
else:
    raise AssertionError('target_bot_loop_end not found')

with open(r'src/CsBotManager/EconomyManager.cs', 'w', encoding='utf-8') as f:
    f.write(text)
print('EconomyManager.cs patched successfully')
