import os

# 1. Fix EconomyManager.cs
with open('src/CsBotManager/EconomyManager.cs', 'r', encoding='utf-8') as f:
    text = f.read()

bad_semi = """                case BuyState.SEMI_BUY:
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
                    break;"""

good_half = """                case BuyState.HALF_BUY:
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
                    break;"""

if bad_semi.replace('\r\n', '\n') in text.replace('\r\n', '\n'):
    lines = text.splitlines()
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if 'case BuyState.SEMI_BUY:' in line:
            new_lines.append('                case BuyState.HALF_BUY:')
            new_lines.append('                    if (botMoney >= 2500)')
            new_lines.append('                    {')
            new_lines.append('                        DeliverArmor(bot, helmet: false, cost: 650);')
            new_lines.append('                        if (isCt && bot.InGameMoneyServices.Account >= 1250)')
            new_lines.append('                            DeliverItem(bot, "weapon_mp9", 1250, isPrimary: true, locomotionDriver);')
            new_lines.append('                        else if (!isCt && bot.InGameMoneyServices.Account >= 1050)')
            new_lines.append('                            DeliverItem(bot, "weapon_mac10", 1050, isPrimary: true, locomotionDriver);')
            new_lines.append('                    }')
            new_lines.append('                    else if (botMoney >= 1200)')
            new_lines.append('                    {')
            new_lines.append('                        if (bot.InGameMoneyServices.Account >= 700)')
            new_lines.append('                            DeliverItem(bot, "weapon_deagle", 700, isPrimary: false, locomotionDriver);')
            new_lines.append('                    }')
            new_lines.append('                    break;')
            # skip until break after SEMI_ECO
            while i < len(lines) and 'case BuyState.FULL_ECO:' not in lines[i]:
                i += 1
            continue
        new_lines.append(line)
        i += 1
    with open('src/CsBotManager/EconomyManager.cs', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines) + '\n')
    print('EconomyManager.cs fixed')
else:
    print('bad_semi not found in EconomyManager.cs')

# 2. Fix CsBotManagerPlugin.cs duplicate declaration
with open('src/CsBotManager/CsBotManagerPlugin.cs', 'r', encoding='utf-8') as f:
    lines2 = f.read().splitlines()

new_lines2 = []
seen = False
for line in lines2:
    if 'var currentPlayersList = GetActivePlayers();' in line:
        if not seen:
            seen = True
            new_lines2.append(line)
        else:
            continue
    elif seen and ('var humanPl =' in line or 'var humTeam =' in line or '_currentPlan = _iglService' in line or '_currentTrPlan = _iglService' in line):
        continue
    else:
        new_lines2.append(line)

with open('src/CsBotManager/CsBotManagerPlugin.cs', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines2) + '\n')
print('CsBotManagerPlugin.cs fixed')
