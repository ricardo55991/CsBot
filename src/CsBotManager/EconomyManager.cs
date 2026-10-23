using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public class TeamEconomySnapshot
{
    public CsTeam TeamSide { get; set; } = CsTeam.None;
    public int RoundNumberInHalf { get; set; } = 1;
    public bool PistolRound { get; set; } = false;
    public int LossBonus { get; set; } = 1400;

    // Pre-buy metrics
    public int CashBeforeBuy { get; set; } = 0;
    public int AverageCashBeforeBuy { get; set; } = 0;
    public int EquipmentValueBeforeBuy { get; set; } = 0;
    public int SavedWeaponCount { get; set; } = 0;
    public BuyState PurchaseIntent { get; set; } = BuyState.FULL_BUY;

    // Post-buy metrics
    public int CashAfterBuy { get; set; } = 0;
    public int AverageCashAfterBuy { get; set; } = 0;
    public int SpentDuringFreezeTime { get; set; } = 0;
    public int EquipmentValueAfterBuy { get; set; } = 0;
    public int PrimaryWeaponCount { get; set; } = 0;
    public int RifleCount { get; set; } = 0;
    public int SmgCount { get; set; } = 0;
    public int ShotgunCount { get; set; } = 0;
    public int AwpCount { get; set; } = 0;
    public int ArmorCount { get; set; } = 0;
    public int HelmetCount { get; set; } = 0;
    public int DefuseKitCount { get; set; } = 0;
    public int UtilityValue { get; set; } = 0;

    public BuyState FinalBuyState { get; set; } = BuyState.UNKNOWN_INCOMPLETE_BUY;
    public BuyCompletionState CompletionState { get; set; } = BuyCompletionState.PENDING;
}

public class EconomyManager
{
    private readonly Random _random = new();
    public BotSystemConfig Config { get; set; } = BotSystemConfig.Default;
    public MatchTelemetryLogger? TelemetryLogger { get; set; }

    private TeamEconomySnapshot _ctSnapshot = new() { TeamSide = CsTeam.CounterTerrorist };
    private TeamEconomySnapshot _trSnapshot = new() { TeamSide = CsTeam.Terrorist };

    public TeamEconomySnapshot CtSnapshot => _ctSnapshot;
    public TeamEconomySnapshot TrSnapshot => _trSnapshot;

    public BuyState CurrentBuyState => _ctSnapshot.FinalBuyState != BuyState.UNKNOWN_INCOMPLETE_BUY
        ? _ctSnapshot.FinalBuyState
        : _ctSnapshot.PurchaseIntent;

    public int TeamAverageMoney { get; private set; } = 800;
    public bool IsDoubleAwpActive { get; private set; } = false;

    public TeamEconomySnapshot GetTeamSnapshot(CsTeam team)
    {
        return team == CsTeam.CounterTerrorist ? _ctSnapshot : _trSnapshot;
    }

    public BuyState GetTeamBuyState(CsTeam team)
    {
        var snap = GetTeamSnapshot(team);
        return snap.CompletionState == BuyCompletionState.STABILIZED || snap.CompletionState == BuyCompletionState.INCOMPLETE
            ? snap.FinalBuyState
            : snap.PurchaseIntent;
    }

    public void OnRoundStart()
    {
        IsDoubleAwpActive = false;
    }

    private static readonly Dictionary<string, int> NativeBlockedWeapons = new(StringComparer.OrdinalIgnoreCase)
    {
        { "weapon_xm1014", 2000 },
        { "weapon_nova", 1050 },
        { "weapon_mag7", 1300 },
        { "weapon_sawedoff", 1100 },
        { "weapon_m249", 5200 },
        { "weapon_negev", 1700 }
    };

    private static readonly Dictionary<string, int> WeaponMarketPrices = new(StringComparer.OrdinalIgnoreCase)
    {
        { "weapon_awp", 4750 },
        { "weapon_ssg08", 1700 },
        { "weapon_scar20", 5000 },
        { "weapon_g3sg1", 5000 },
        { "weapon_ak47", 2700 },
        { "weapon_m4a1_silencer", 2900 },
        { "weapon_m4a1", 3000 },
        { "weapon_aug", 3300 },
        { "weapon_sg556", 3000 },
        { "weapon_sg553", 3000 },
        { "weapon_famas", 2050 },
        { "weapon_galilar", 1800 },
        { "weapon_mp9", 1250 },
        { "weapon_mac10", 1050 },
        { "weapon_mp7", 1500 },
        { "weapon_mp5sd", 1500 },
        { "weapon_ump45", 1200 },
        { "weapon_p90", 2350 },
        { "weapon_bizon", 1400 },
        { "weapon_deagle", 700 },
        { "weapon_revolver", 600 },
        { "weapon_fiveseven", 500 },
        { "weapon_tec9", 500 },
        { "weapon_cz75a", 500 },
        { "weapon_p250", 300 },
        { "weapon_elite", 300 },
        { "weapon_usp_silencer", 200 },
        { "weapon_hkp2000", 200 },
        { "weapon_glock", 200 },
        { "weapon_smokegrenade", 300 },
        { "weapon_flashbang", 200 },
        { "weapon_hegrenade", 300 },
        { "weapon_molotov", 400 },
        { "weapon_incgrenade", 600 },
        { "weapon_decoy", 50 }
    };

    public static int GetWeaponPrice(string? designerName)
    {
        if (string.IsNullOrEmpty(designerName)) return 0;
        string normalized = designerName.StartsWith("weapon_", StringComparison.OrdinalIgnoreCase)
            ? designerName
            : $"weapon_{designerName}";
        return WeaponMarketPrices.TryGetValue(normalized, out int price) ? price : 0;
    }

    public static BuyState DeterminePreBuyIntent(
        CsTeam team,
        int roundNumber,
        int avgCash,
        int lossBonus,
        int savedPrimaryCount,
        int preBuyEquipmentValue,
        BotSystemConfig? config = null)
    {
        var cfg = config ?? BotSystemConfig.Default;
        int roundInHalf = ((Math.Max(1, roundNumber) - 1) % 12) + 1;
        bool isPistol = roundNumber == 1 || roundNumber == 13 || roundInHalf == 1;

        if (isPistol)
        {
            return BuyState.PISTOL_ROUND;
        }

        if (savedPrimaryCount >= 3 && avgCash < (team == CsTeam.CounterTerrorist ? cfg.CtFullBuyMinAvgCash : cfg.TrFullBuyMinAvgCash))
        {
            return BuyState.SAVE_WITH_WEAPONS;
        }

        // Último round da metade -> Force Buy total se não tiver Full Buy
        if (roundNumber == 12 || roundNumber == 24)
        {
            int fullThreshold = team == CsTeam.CounterTerrorist ? cfg.CtFullBuyMinAvgCash : cfg.TrFullBuyMinAvgCash;
            return avgCash >= fullThreshold ? BuyState.FULL_BUY : BuyState.FORCE_BUY;
        }

        // Round 2 ou 14: se tiver grana de vitória ou plant, avalia compra; se perdeu sem plant, force ou half
        if (team == CsTeam.CounterTerrorist)
        {
            if (avgCash >= cfg.CtFullBuyMinAvgCash || (savedPrimaryCount >= 2 && avgCash >= 3400))
                return BuyState.FULL_BUY;
            if (avgCash >= 3000)
                return BuyState.HALF_BUY;
            if (avgCash + lossBonus >= 4500 && roundNumber != 2 && roundNumber != 14)
                return BuyState.FULL_ECO;
            if (avgCash >= 2000)
                return BuyState.FORCE_BUY;
            if (avgCash >= 1300)
                return BuyState.LIGHT_BUY;
            return BuyState.FULL_ECO;
        }
        else
        {
            if (avgCash >= cfg.TrFullBuyMinAvgCash || (savedPrimaryCount >= 2 && avgCash >= 3000))
                return BuyState.FULL_BUY;
            if (avgCash >= 2600)
                return BuyState.HALF_BUY;
            if (avgCash + lossBonus >= 4100 && roundNumber != 2 && roundNumber != 14)
                return BuyState.FULL_ECO;
            if (avgCash >= 1850)
                return BuyState.FORCE_BUY;
            if (avgCash >= 1200)
                return BuyState.LIGHT_BUY;
            return BuyState.FULL_ECO;
        }
    }

    public static BuyState ClassifyPostBuySnapshot(TeamEconomySnapshot snap, BotSystemConfig? config = null)
    {
        var cfg = config ?? BotSystemConfig.Default;

        if (snap.PistolRound || snap.RoundNumberInHalf == 1)
        {
            snap.FinalBuyState = BuyState.PISTOL_ROUND;
            return snap.FinalBuyState;
        }

        // Se ainda não houve compra consolidada mas o time tinha grana alta e continua com 0 primárias e 0 gasto:
        if (snap.CompletionState == BuyCompletionState.PENDING && snap.PrimaryWeaponCount == 0 && snap.AverageCashBeforeBuy >= 3500)
        {
            snap.FinalBuyState = BuyState.UNKNOWN_INCOMPLETE_BUY;
            return snap.FinalBuyState;
        }

        // Se mantiveram armas salvas do round anterior com baixo gasto adicional
        if (snap.SavedWeaponCount >= 3 && snap.SpentDuringFreezeTime < 2500 && snap.PrimaryWeaponCount >= 3)
        {
            snap.FinalBuyState = BuyState.SAVE_WITH_WEAPONS;
            return snap.FinalBuyState;
        }

        int fullBuyEquipThreshold = snap.TeamSide == CsTeam.CounterTerrorist
            ? cfg.CtFullBuyMinEquipmentValue
            : cfg.TrFullBuyMinEquipmentValue;

        // FULL_BUY real exige rifles/AWPs suficientes (>= 4 primárias ou equipamento total >= threshold com >= 3 rifles/awp)
        if ((snap.RifleCount + snap.AwpCount >= 4 && snap.ArmorCount >= 4) ||
            (snap.PrimaryWeaponCount >= 4 && snap.EquipmentValueAfterBuy >= fullBuyEquipThreshold && snap.ArmorCount >= 4))
        {
            snap.FinalBuyState = BuyState.FULL_BUY;
            return snap.FinalBuyState;
        }

        // Se o time tinha dinheiro de FULL_BUY, tentou comprar mas terminou sem primárias suficientes
        if (snap.PurchaseIntent == BuyState.FULL_BUY && snap.PrimaryWeaponCount <= 1 && snap.AverageCashAfterBuy >= 3000)
        {
            snap.FinalBuyState = BuyState.UNKNOWN_INCOMPLETE_BUY;
            return snap.FinalBuyState;
        }

        // FORCE_BUY vs HALF_BUY
        if (snap.PrimaryWeaponCount >= 3 || snap.EquipmentValueAfterBuy >= 10500)
        {
            // Se quase zerou o caixa médio (< $900) comprando SMGs/rifles parciais -> FORCE_BUY
            if (snap.AverageCashAfterBuy < 950 || snap.PurchaseIntent == BuyState.FORCE_BUY)
            {
                snap.FinalBuyState = BuyState.FORCE_BUY;
            }
            else
            {
                snap.FinalBuyState = BuyState.HALF_BUY;
            }
            return snap.FinalBuyState;
        }

        if (snap.PrimaryWeaponCount >= 1 || snap.EquipmentValueAfterBuy >= 5500 || snap.SpentDuringFreezeTime >= 3500)
        {
            snap.FinalBuyState = snap.AverageCashAfterBuy < 1000 ? BuyState.FORCE_BUY : BuyState.HALF_BUY;
            return snap.FinalBuyState;
        }

        if (snap.SpentDuringFreezeTime >= 1200 || snap.ArmorCount >= 2 || snap.UtilityValue >= 800)
        {
            snap.FinalBuyState = BuyState.LIGHT_BUY;
            return snap.FinalBuyState;
        }

        snap.FinalBuyState = BuyState.FULL_ECO;
        return snap.FinalBuyState;
    }

    public void SanitizeNativePurchasesAndRefund(List<CCSPlayerController> bots)
    {
        foreach (var bot in bots)
        {
            if (bot == null || !bot.IsValid || !bot.IsBot) continue;
            var pawn = bot.PlayerPawn.Value;
            if (pawn?.WeaponServices?.MyWeapons == null) continue;

            int refundAmount = 0;
            foreach (var handle in pawn.WeaponServices.MyWeapons)
            {
                var w = handle.Value;
                if (w != null && w.IsValid && !string.IsNullOrEmpty(w.DesignerName))
                {
                    if (NativeBlockedWeapons.TryGetValue(w.DesignerName, out int cost))
                    {
                        refundAmount += cost;
                        TelemetryLogger?.LogEvent("ECONOMIA - ITEM",
                            $"{bot.PlayerName} teve arma bloqueada ({w.DesignerName}) removida e reembolsada (+${cost}).");
                        w.Remove();
                    }
                }
            }

            if (refundAmount > 0 && bot.InGameMoneyServices != null)
            {
                bot.InGameMoneyServices.Account += refundAmount;
                Utilities.SetStateChanged(bot, "CCSPlayerController", "m_pInGameMoneyServices");
            }
            EquipBestWeapon(bot);
        }
    }

    public BuyState AnalyzeTeamEconomy(List<CCSPlayerController> teamMembers, int roundNumber, int lossBonus, CsTeam team)
    {
        var snap = CapturePreBuySnapshot(teamMembers, roundNumber, lossBonus, team);
        TeamAverageMoney = snap.AverageCashBeforeBuy;
        return snap.PurchaseIntent;
    }

    public TeamEconomySnapshot CapturePreBuySnapshot(List<CCSPlayerController> teamMembers, int roundNumber, int lossBonus, CsTeam team)
    {
        int roundInHalf = ((Math.Max(1, roundNumber) - 1) % 12) + 1;
        bool isPistol = roundNumber == 1 || roundNumber == 13 || roundInHalf == 1;

        var snap = new TeamEconomySnapshot
        {
            TeamSide = team,
            RoundNumberInHalf = roundInHalf,
            PistolRound = isPistol,
            LossBonus = lossBonus,
            CompletionState = BuyCompletionState.PENDING
        };

        if (teamMembers.Count > 0)
        {
            int totalCash = 0;
            int totalEquip = 0;
            int savedPrimaries = 0;

            foreach (var m in teamMembers)
            {
                if (m == null || !m.IsValid) continue;
                totalCash += m.InGameMoneyServices?.Account ?? 0;
                var inv = InspectPlayerInventory(m);
                totalEquip += inv.TotalEquipmentValue;
                if (inv.HasPrimary) savedPrimaries++;
            }

            snap.CashBeforeBuy = totalCash;
            snap.AverageCashBeforeBuy = totalCash / Math.Max(1, teamMembers.Count);
            snap.EquipmentValueBeforeBuy = totalEquip;
            snap.SavedWeaponCount = savedPrimaries;
        }

        snap.PurchaseIntent = DeterminePreBuyIntent(
            team,
            roundNumber,
            snap.AverageCashBeforeBuy,
            lossBonus,
            snap.SavedWeaponCount,
            snap.EquipmentValueBeforeBuy,
            Config);

        snap.FinalBuyState = isPistol ? BuyState.PISTOL_ROUND : snap.PurchaseIntent;

        if (team == CsTeam.CounterTerrorist)
            _ctSnapshot = snap;
        else if (team == CsTeam.Terrorist)
            _trSnapshot = snap;

        return snap;
    }

    public TeamEconomySnapshot ConsolidatePostBuySnapshot(List<CCSPlayerController> teamMembers, CsTeam team)
    {
        var snap = GetTeamSnapshot(team);
        int totalCashAfter = 0;
        int totalEquipAfter = 0;
        int primaries = 0;
        int rifles = 0;
        int smgs = 0;
        int shotguns = 0;
        int awps = 0;
        int armors = 0;
        int helmets = 0;
        int kits = 0;
        int utilities = 0;

        foreach (var m in teamMembers)
        {
            if (m == null || !m.IsValid) continue;
            totalCashAfter += m.InGameMoneyServices?.Account ?? 0;
            var inv = InspectPlayerInventory(m);
            totalEquipAfter += inv.TotalEquipmentValue;
            if (inv.HasPrimary) primaries++;
            if (inv.IsRifle) rifles++;
            if (inv.IsSmg) smgs++;
            if (inv.IsShotgun) shotguns++;
            if (inv.IsAwp) awps++;
            if (inv.HasArmor) armors++;
            if (inv.HasHelmet) helmets++;
            if (inv.HasDefuser) kits++;
            utilities += inv.UtilityValue;
        }

        snap.CashAfterBuy = totalCashAfter;
        snap.AverageCashAfterBuy = teamMembers.Count > 0 ? totalCashAfter / teamMembers.Count : 0;
        int rawSpent = Math.Max(0, snap.CashBeforeBuy - totalCashAfter);
        int equipDelta = Math.Max(0, totalEquipAfter - snap.EquipmentValueBeforeBuy);
        snap.SpentDuringFreezeTime = Math.Max(rawSpent, equipDelta);
        snap.EquipmentValueAfterBuy = totalEquipAfter;
        snap.PrimaryWeaponCount = primaries;
        snap.RifleCount = rifles;
        snap.SmgCount = smgs;
        snap.ShotgunCount = shotguns;
        snap.AwpCount = awps;
        snap.ArmorCount = armors;
        snap.HelmetCount = helmets;
        snap.DefuseKitCount = kits;
        snap.UtilityValue = utilities;
        snap.CompletionState = BuyCompletionState.STABILIZED;

        ClassifyPostBuySnapshot(snap, Config);
        return snap;
    }

    private struct InventoryInspectionResult
    {
        public bool HasPrimary;
        public bool IsRifle;
        public bool IsSmg;
        public bool IsShotgun;
        public bool IsAwp;
        public bool HasArmor;
        public bool HasHelmet;
        public bool HasDefuser;
        public int UtilityValue;
        public int TotalEquipmentValue;
        public string PrimaryWeaponName;
    }

    private static InventoryInspectionResult InspectPlayerInventory(CCSPlayerController player)
    {
        var res = new InventoryInspectionResult { PrimaryWeaponName = "none" };
        var pawn = player.PlayerPawn.Value;
        if (pawn == null) return res;

        var itemServices = pawn.ItemServices as CCSPlayer_ItemServices;
        bool hasHelmet = itemServices?.HasHelmet ?? false;
        bool hasDefuser = itemServices?.HasDefuser ?? false;
        int armorVal = pawn.ArmorValue;

        if (armorVal > 0)
        {
            res.HasArmor = true;
            res.HasHelmet = hasHelmet;
            res.TotalEquipmentValue += hasHelmet ? 1000 : 650;
        }

        if (hasDefuser)
        {
            res.HasDefuser = true;
            res.TotalEquipmentValue += 400;
        }

        if (pawn.WeaponServices?.MyWeapons != null)
        {
            foreach (var handle in pawn.WeaponServices.MyWeapons)
            {
                var w = handle.Value;
                if (w == null || !w.IsValid || string.IsNullOrEmpty(w.DesignerName)) continue;
                string dName = w.DesignerName.ToLowerInvariant();
                int price = GetWeaponPrice(dName);

                // Pistolas iniciais não somam como compra extra relevante além do valor base
                if (dName.Contains("glock") || dName.Contains("hkp2000") || dName.Contains("usp_silencer"))
                {
                    res.TotalEquipmentValue += 200;
                    continue;
                }

                res.TotalEquipmentValue += price;

                if (BotLocomotionDriver.IsGrenadeWeapon(dName))
                {
                    res.UtilityValue += price;
                }
                else if (CombatAdapter.IsPrimaryWeapon(dName))
                {
                    res.HasPrimary = true;
                    res.PrimaryWeaponName = dName;
                    if (dName.Contains("awp"))
                    {
                        res.IsAwp = true;
                    }
                    else if (dName.Contains("ak47") || dName.Contains("m4a1") || dName.Contains("m4a4") ||
                             dName.Contains("galilar") || dName.Contains("famas") || dName.Contains("aug") ||
                             dName.Contains("sg553") || dName.Contains("sg556") || dName.Contains("ssg08"))
                    {
                        res.IsRifle = true;
                    }
                    else if (dName.Contains("mp9") || dName.Contains("mac10") || dName.Contains("mp7") ||
                             dName.Contains("mp5") || dName.Contains("ump45") || dName.Contains("p90") || dName.Contains("bizon"))
                    {
                        res.IsSmg = true;
                    }
                    else if (dName.Contains("xm1014") || dName.Contains("nova") || dName.Contains("mag7") || dName.Contains("sawedoff"))
                    {
                        res.IsShotgun = true;
                    }
                }
            }
        }

        return res;
    }

    public static string GetPrimaryWeaponDesignerName(CCSPlayerController bot)
    {
        var pawn = bot.PlayerPawn.Value;
        if (pawn?.WeaponServices?.MyWeapons == null) return "none";

        foreach (var handle in pawn.WeaponServices.MyWeapons)
        {
            var w = handle.Value;
            if (w != null && w.IsValid && !string.IsNullOrEmpty(w.DesignerName))
            {
                if (CombatAdapter.IsPrimaryWeapon(w.DesignerName))
                {
                    return w.DesignerName;
                }
            }
        }
        return "none";
    }

    public void ReconcileTeamWeaponsAndRoles(List<CCSPlayerController> teamBots, RoleManager roleManager, CsTeam team)
    {
        // Regra 7: Verifica se algum bot não-AWPer salvou ou pegou AWP.
        // Nunca deleta uma AWP salva sem substituição segura! Adapta formalmente o round_role e assigned_weapon_role.
        CCSPlayerController? savedAwpHolder = null;
        foreach (var bot in teamBots)
        {
            if (bot == null || !bot.IsValid) continue;
            if (HasSpecificWeapon(bot, "awp"))
            {
                savedAwpHolder = bot;
                break;
            }
        }

        var profileAwper = teamBots.FirstOrDefault(b => b != null && b.IsValid && roleManager.GetBotProfileRole(b.Slot) == BotRole.AWPer);

        if (savedAwpHolder != null && profileAwper != null && savedAwpHolder.Slot != profileAwper.Slot)
        {
            var prevHolderRole = roleManager.GetBotProfileRole(savedAwpHolder.Slot) ?? BotRole.Rotator;
            roleManager.ReconcileWeaponRoleOverride(
                savedAwpHolder.Slot,
                "weapon_awp",
                hasSavedAwp: true,
                teamAlreadyHasSavedAwpOnTeammate: false,
                couldNotAffordAwp: false);

            string profileAwperPrimary = GetPrimaryWeaponDesignerName(profileAwper);
            roleManager.ReconcileWeaponRoleOverride(
                profileAwper.Slot,
                profileAwperPrimary,
                hasSavedAwp: false,
                teamAlreadyHasSavedAwpOnTeammate: true,
                couldNotAffordAwp: (profileAwper.InGameMoneyServices?.Account ?? 0) < 4750);

            TelemetryLogger?.LogEvent("ROLE_RECONCILE",
                $"[{team}] {savedAwpHolder.PlayerName} manteve AWP salva (round_role=AWPer, pickup_override=true). {profileAwper.PlayerName} adaptado para {prevHolderRole} para evitar dupla AWP acidental.");
        }
        else
        {
            foreach (var bot in teamBots)
            {
                if (bot == null || !bot.IsValid) continue;
                var pRole = roleManager.GetBotProfileRole(bot.Slot) ?? BotRole.Rotator;
                string primary = GetPrimaryWeaponDesignerName(bot);
                bool hasAwp = primary.Contains("awp", StringComparison.OrdinalIgnoreCase);
                bool isFallbackRifle = pRole == BotRole.AWPer && !hasAwp && !string.Equals(primary, "none", StringComparison.OrdinalIgnoreCase);
                roleManager.ReconcileWeaponRoleOverride(
                    bot.Slot,
                    primary,
                    hasSavedAwp: hasAwp,
                    teamAlreadyHasSavedAwpOnTeammate: false,
                    couldNotAffordAwp: isFallbackRifle);
            }
        }
    }

    private void EnsureUtility(CCSPlayerController bot, string weaponName, int cost)
    {
        if (bot.InGameMoneyServices == null) return;
        string subName = weaponName.Replace("weapon_", "");
        if (!HasSpecificWeapon(bot, subName))
        {
            if (bot.InGameMoneyServices.Account >= cost)
            {
                int cashBefore = bot.InGameMoneyServices.Account;
                bot.InGameMoneyServices.Account -= cost;
                Utilities.SetStateChanged(bot, "CCSPlayerController", "m_pInGameMoneyServices");
                bot.GiveNamedItem(weaponName);
                TelemetryLogger?.LogEvent("ECONOMIA - ITEM",
                    $"{bot.PlayerName} comprou utilitária {weaponName} (-${cost}, saldo: ${cashBefore} -> ${bot.InGameMoneyServices.Account}) [motivo: loadout tático]");
                EquipBestWeapon(bot);
            }
        }
    }

    public bool DropWeaponForPlayer(CCSPlayerController player, string? requestedWeapon, List<CCSPlayerController> teamBots)
    {
        if (teamBots.Count == 0 || player == null || !player.IsValid) return false;

        string req = (requestedWeapon ?? string.Empty).Trim().ToLowerInvariant();
        bool isCt = player.Team == CsTeam.CounterTerrorist;

        string weaponToBuy = req switch
        {
            "awp" => "awp",
            "m4" or "m4a1" or "m4a4" => isCt ? "m4a1_silencer" : "ak47",
            "ak" or "ak47" => "ak47",
            "deagle" => "deagle",
            _ => isCt ? "m4a1_silencer" : "ak47"
        };

        int cost = weaponToBuy switch
        {
            "awp" => 4750,
            "ak47" => 2700,
            "m4a1_silencer" => 2900,
            "deagle" => 700,
            _ => 2700
        };

        var richestBot = teamBots
            .Where(b => b.IsValid && b.InGameMoneyServices != null && (b.InGameMoneyServices.Account - cost) >= 2000)
            .OrderByDescending(b => b.InGameMoneyServices?.Account ?? 0)
            .FirstOrDefault();

        if (richestBot == null || richestBot.InGameMoneyServices == null)
        {
            return false;
        }

        int beforeCash = richestBot.InGameMoneyServices.Account;
        richestBot.InGameMoneyServices.Account -= cost;
        Utilities.SetStateChanged(richestBot, "CCSPlayerController", "m_pInGameMoneyServices");

        string prevPrimary = GetPrimaryWeaponDesignerName(player);
        if (CombatAdapter.IsPrimaryWeapon($"weapon_{weaponToBuy}"))
        {
            RemovePrimaryWeapons(player);
        }

        player.GiveNamedItem($"weapon_{weaponToBuy}");
        TelemetryLogger?.LogEvent("ECONOMIA - ITEM",
            $"{richestBot.PlayerName} dropou weapon_{weaponToBuy} para {player.PlayerName} (arma anterior={prevPrimary}, custo=${cost}, saldo doador=${beforeCash}->${richestBot.InGameMoneyServices.Account})");

        player.PrintToChat($" {ChatColors.Green}[CsBot Economy]{ChatColors.Default} {richestBot.PlayerName} comprou e entregou {weaponToBuy.ToUpper()} para você!");
        return true;
    }

    // Drop automático de AWP para o sniper designado da equipe (CORRIGIDO: == BotRole.AWPer e respeita limite de AWP no time)
    public void TryCoordinateTeamAwpDrop(List<CCSPlayerController> teamBots, RoleManager roleManager, CsTeam team)
    {
        // Se qualquer bot da equipe já possui uma AWP salva, não compra segunda AWP fora de Double AWP explícito
        int currentTeamAwps = teamBots.Count(b => b != null && b.IsValid && HasSpecificWeapon(b, "awp"));
        if (currentTeamAwps >= 1) return;

        var awpBot = teamBots.FirstOrDefault(b => b != null && b.IsValid && roleManager.GetBotRole(b) == BotRole.AWPer);
        if (awpBot == null || awpBot.InGameMoneyServices == null) return;

        if (HasValuablePrimaryWeapon(awpBot)) return;

        int awpBotMoney = awpBot.InGameMoneyServices.Account;
        if (awpBotMoney >= 4750) return; // Ele mesmo comprará no loop determinístico

        var donorBot = teamBots
            .Where(b => b != null && b.IsValid && b.Slot != awpBot.Slot && b.InGameMoneyServices != null && (b.InGameMoneyServices.Account - 4750) >= 2000)
            .OrderByDescending(b => b.InGameMoneyServices?.Account ?? 0)
            .FirstOrDefault();

        if (donorBot != null && donorBot.InGameMoneyServices != null)
        {
            int donorBefore = donorBot.InGameMoneyServices.Account;
            string prevWeapon = GetPrimaryWeaponDesignerName(awpBot);
            donorBot.InGameMoneyServices.Account -= 4750;
            Utilities.SetStateChanged(donorBot, "CCSPlayerController", "m_pInGameMoneyServices");

            RemovePrimaryWeapons(awpBot);
            awpBot.GiveNamedItem("weapon_awp");
            TelemetryLogger?.LogEvent("ECONOMIA - ITEM",
                $"{donorBot.PlayerName} financiou weapon_awp para o AWPer {awpBot.PlayerName} (arma anterior={prevWeapon}, custo=$4750, saldo doador=${donorBefore}->${donorBot.InGameMoneyServices.Account})");
            UtilityAndClockCoordinator.PrintTeamChat(team, donorBot.PlayerName, $"Comprei AWP pra você, {awpBot.PlayerName}! Destrói eles!");
        }
    }

    public void TryCoordinateDoubleAwpSetup(
        List<CCSPlayerController> teamBots,
        RoleManager roleManager,
        TacticalPlan plan,
        CsTeam team)
    {
        if (team != CsTeam.CounterTerrorist || IsDoubleAwpActive) return;

        int existingAwps = teamBots.Count(b => b != null && b.IsValid && HasSpecificWeapon(b, "awp"));
        if (existingAwps >= Config.MaxDoubleAwpPerTeamCt)
        {
            IsDoubleAwpActive = true;
            return;
        }

        var anchorBot = teamBots.FirstOrDefault(b => b.IsValid && roleManager.GetBotRole(b) == BotRole.Anchor && !HasSpecificWeapon(b, "awp"))
                     ?? teamBots.FirstOrDefault(b => b.IsValid && roleManager.GetBotRole(b) == BotRole.Rotator && !HasSpecificWeapon(b, "awp"));

        if (anchorBot == null || anchorBot.InGameMoneyServices == null) return;

        bool hasAwp = HasSpecificWeapon(anchorBot, "awp");
        if (!hasAwp)
        {
            int botMoney = anchorBot.InGameMoneyServices.Account;
            if (botMoney >= 4750 && !HasValuablePrimaryWeapon(anchorBot))
            {
                DeliverItem(anchorBot, "weapon_awp", 4750, isPrimary: true, reason: "Double AWP CT Setup");
                hasAwp = HasSpecificWeapon(anchorBot, "awp");
            }
            else if (!HasValuablePrimaryWeapon(anchorBot))
            {
                var donorBot = teamBots
                    .Where(b => b.IsValid && b.Slot != anchorBot.Slot && b.InGameMoneyServices != null && (b.InGameMoneyServices.Account - 4750) >= 2500)
                    .OrderByDescending(b => b.InGameMoneyServices?.Account ?? 0)
                    .FirstOrDefault();

                if (donorBot != null && donorBot.InGameMoneyServices != null)
                {
                    int donorBefore = donorBot.InGameMoneyServices.Account;
                    string prevWep = GetPrimaryWeaponDesignerName(anchorBot);
                    donorBot.InGameMoneyServices.Account -= 4750;
                    Utilities.SetStateChanged(donorBot, "CCSPlayerController", "m_pInGameMoneyServices");
                    RemovePrimaryWeapons(anchorBot);
                    anchorBot.GiveNamedItem("weapon_awp");
                    hasAwp = true;
                    TelemetryLogger?.LogEvent("ECONOMIA - ITEM",
                        $"{donorBot.PlayerName} financiou segunda AWP (Double AWP CT) para {anchorBot.PlayerName} (anterior={prevWep}, custo=$4750, saldo doador=${donorBefore}->${donorBot.InGameMoneyServices.Account})");
                    UtilityAndClockCoordinator.PrintTeamChat(team, donorBot.PlayerName, $"Comprei a segunda AWP pra você, {anchorBot.PlayerName}! Double AWP no setup!");
                }
            }
        }

        if (hasAwp)
        {
            IsDoubleAwpActive = true;
            roleManager.ConfigureDoubleAwpSetup(anchorBot, plan);
            UtilityAndClockCoordinator.PrintTeamChat(team, "IGL", "Economia alta! Vamos de DOUBLE AWP, domina as pontas!");
        }
    }

    public void ExecuteDeterministicBuys(
        List<CCSPlayerController> bots,
        BuyState buyState,
        CsTeam team,
        RoleManager roleManager,
        TacticalPlan plan,
        BotLocomotionDriver? locomotionDriver = null)
    {
        bool isCt = team == CsTeam.CounterTerrorist;
        var snap = GetTeamSnapshot(team);

        // Primeiro reconcilia armas salvas (ex.: AWP salva por não-AWPer) sem nunca deletar AWP gratuitamente
        ReconcileTeamWeaponsAndRoles(bots, roleManager, team);

        if (buyState == BuyState.FULL_BUY)
        {
            TryCoordinateTeamAwpDrop(bots, roleManager, team);
            if (isCt && snap.AverageCashBeforeBuy >= 7500 && _random.Next(100) < 35)
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

            if (buyState == BuyState.PISTOL_ROUND || snap.PistolRound)
            {
                // Round pistol: compra colete leve ($650) ou utilitárias/kit conforme a função
                if (isCt && role == BotRole.Anchor && bot.InGameMoneyServices.Account >= 400)
                {
                    DeliverDefuser(bot, cost: 400);
                    EnsureUtility(bot, "weapon_smokegrenade", 300);
                }
                else if (bot.InGameMoneyServices.Account >= 650)
                {
                    DeliverArmor(bot, helmet: false, cost: 650);
                }
                if (bot.InGameMoneyServices.Account >= 200)
                {
                    EnsureUtility(bot, "weapon_flashbang", 200);
                }

                if (locomotionDriver != null)
                    locomotionDriver.ForceEquipBestFirearm(bot);
                else
                    EquipBestWeapon(bot);
                continue;
            }

            BuyState effectiveBuy = (botMoney >= 4000)
                ? BuyState.FULL_BUY
                : ((botMoney >= 1800 && buyState != BuyState.FULL_ECO) ? BuyState.FORCE_BUY : buyState);

            switch (effectiveBuy)
            {
                case BuyState.FULL_BUY:
                case BuyState.SAVE_WITH_WEAPONS:
                    DeliverArmor(bot, helmet: true, cost: 1000);
                    if (isCt) DeliverDefuser(bot, cost: 400);

                    int currentTeamAwps = bots.Count(b => b != null && b.IsValid && HasSpecificWeapon(b, "awp"));
                    int maxAllowedAwps = isCt && IsDoubleAwpActive ? Config.MaxDoubleAwpPerTeamCt : Config.MaxStandardAwpPerTeam;

                    if (role == BotRole.AWPer)
                    {
                        if (bot.InGameMoneyServices.Account >= 4750 && !HasSpecificWeapon(bot, "awp") && currentTeamAwps < maxAllowedAwps)
                        {
                            DeliverItem(bot, "weapon_awp", 4750, isPrimary: true, locomotionDriver, reason: "Primary AWPer FullBuy");
                        }
                        else if (!alreadyHasPrimary)
                        {
                            string rifle = isCt ? "weapon_m4a1_silencer" : "weapon_ak47";
                            int cost = isCt ? 2900 : 2700;
                            if (bot.InGameMoneyServices.Account >= cost)
                            {
                                DeliverItem(bot, rifle, cost, isPrimary: true, locomotionDriver, reason: "AWPer Rifle Fallback");
                            }
                            else if (bot.InGameMoneyServices.Account >= (isCt ? 2050 : 1800))
                            {
                                DeliverItem(bot, isCt ? "weapon_famas" : "weapon_galilar", isCt ? 2050 : 1800, isPrimary: true, locomotionDriver, reason: "AWPer Tier2 Rifle Fallback");
                            }
                        }
                    }
                    else if (!alreadyHasPrimary)
                    {
                        if (isCt)
                        {
                            if (bot.InGameMoneyServices.Account >= 2900)
                            {
                                DeliverItem(bot, "weapon_m4a1_silencer", 2900, isPrimary: true, locomotionDriver, reason: $"FullBuy CT ({role})");
                            }
                            else if (bot.InGameMoneyServices.Account >= 2050)
                            {
                                DeliverItem(bot, "weapon_famas", 2050, isPrimary: true, locomotionDriver, reason: $"FullBuy CT Tier2 ({role})");
                            }
                        }
                        else // TR
                        {
                            if (bot.InGameMoneyServices.Account >= 2700)
                            {
                                DeliverItem(bot, "weapon_ak47", 2700, isPrimary: true, locomotionDriver, reason: $"FullBuy TR ({role})");
                            }
                            else if (bot.InGameMoneyServices.Account >= 1800)
                            {
                                DeliverItem(bot, "weapon_galilar", 1800, isPrimary: true, locomotionDriver, reason: $"FullBuy TR Tier2 ({role})");
                            }
                        }
                    }

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
                    DeliverArmor(bot, helmet: false, cost: 650);

                    if (!alreadyHasPrimary)
                    {
                        if (isCt)
                        {
                            if (bot.InGameMoneyServices.Account >= 2050)
                            {
                                DeliverItem(bot, "weapon_famas", 2050, isPrimary: true, locomotionDriver, reason: $"ForceBuy CT ({role})");
                            }
                            else if (bot.InGameMoneyServices.Account >= 1250)
                            {
                                DeliverItem(bot, "weapon_mp9", 1250, isPrimary: true, locomotionDriver, reason: $"ForceBuy CT SMG ({role})");
                            }
                            else if (bot.InGameMoneyServices.Account >= 700)
                            {
                                DeliverItem(bot, "weapon_deagle", 700, isPrimary: false, locomotionDriver, reason: $"ForceBuy CT Pistol ({role})");
                            }
                        }
                        else // TR
                        {
                            if (bot.InGameMoneyServices.Account >= 1800)
                            {
                                DeliverItem(bot, "weapon_galilar", 1800, isPrimary: true, locomotionDriver, reason: $"ForceBuy TR ({role})");
                            }
                            else if (bot.InGameMoneyServices.Account >= 1050)
                            {
                                DeliverItem(bot, "weapon_mac10", 1050, isPrimary: true, locomotionDriver, reason: $"ForceBuy TR SMG ({role})");
                            }
                            else if (bot.InGameMoneyServices.Account >= 700)
                            {
                                DeliverItem(bot, "weapon_deagle", 700, isPrimary: false, locomotionDriver, reason: $"ForceBuy TR Pistol ({role})");
                            }
                        }
                    }

                    EnsureUtility(bot, "weapon_flashbang", 200);
                    break;

                case BuyState.HALF_BUY:
                case BuyState.LIGHT_BUY:
                    if (botMoney >= 2500)
                    {
                        DeliverArmor(bot, helmet: false, cost: 650);
                        if (!alreadyHasPrimary)
                        {
                            if (isCt && bot.InGameMoneyServices.Account >= 1250)
                                DeliverItem(bot, "weapon_mp9", 1250, isPrimary: true, locomotionDriver, reason: "HalfBuy CT SMG");
                            else if (!isCt && bot.InGameMoneyServices.Account >= 1050)
                                DeliverItem(bot, "weapon_mac10", 1050, isPrimary: true, locomotionDriver, reason: "HalfBuy TR SMG");
                        }
                    }
                    else if (botMoney >= 1200)
                    {
                        if (bot.InGameMoneyServices.Account >= 700)
                            DeliverItem(bot, "weapon_deagle", 700, isPrimary: false, locomotionDriver, reason: "LightBuy Deagle");
                    }
                    break;

                case BuyState.FULL_ECO:
                default:
                    locomotionDriver?.BotApi?.SetBuySkip(bot.Slot);
                    break;
            }

            if (locomotionDriver != null)
            {
                locomotionDriver.ForceEquipBestFirearm(bot);
            }
            else
            {
                EquipBestWeapon(bot);
            }
        }

        // Reconcilia novamente os papéis finais pós-compra e consolida o snapshot econômico
        ReconcileTeamWeaponsAndRoles(bots, roleManager, team);
        ConsolidatePostBuySnapshot(bots, team);
    }

    private void DeliverArmor(CCSPlayerController bot, bool helmet, int cost)
    {
        if (bot == null || !bot.IsValid || bot.InGameMoneyServices == null) return;
        var pawn = bot.PlayerPawn.Value;
        if (pawn == null) return;
        var itemServices = pawn.ItemServices as CCSPlayer_ItemServices;

        if (pawn.ArmorValue >= 100 && (!helmet || (itemServices?.HasHelmet ?? false))) return;

        if (bot.InGameMoneyServices.Account >= cost)
        {
            int cashBefore = bot.InGameMoneyServices.Account;
            string item = helmet ? "item_assaultsuit" : "item_kevlar";
            bot.InGameMoneyServices.Account -= cost;
            Utilities.SetStateChanged(bot, "CCSPlayerController", "m_pInGameMoneyServices");
            bot.GiveNamedItem(item);
            TelemetryLogger?.LogEvent("ECONOMIA - ITEM",
                $"{bot.PlayerName} recebeu {item} (-${cost}, saldo: ${cashBefore} -> ${bot.InGameMoneyServices.Account})");
        }
    }

    private void DeliverDefuser(CCSPlayerController bot, int cost = 400)
    {
        if (bot == null || !bot.IsValid || bot.InGameMoneyServices == null) return;
        var pawn = bot.PlayerPawn.Value;
        if (pawn == null) return;
        var itemServices = pawn.ItemServices as CCSPlayer_ItemServices;
        if (itemServices?.HasDefuser ?? false) return;

        if (bot.InGameMoneyServices.Account >= cost)
        {
            int cashBefore = bot.InGameMoneyServices.Account;
            bot.InGameMoneyServices.Account -= cost;
            Utilities.SetStateChanged(bot, "CCSPlayerController", "m_pInGameMoneyServices");
            bot.GiveNamedItem("item_defuser");
            TelemetryLogger?.LogEvent("ECONOMIA - ITEM",
                $"{bot.PlayerName} recebeu item_defuser (-${cost}, saldo: ${cashBefore} -> ${bot.InGameMoneyServices.Account})");
        }
    }

    private void DeliverItem(
        CCSPlayerController bot,
        string itemName,
        int cost,
        bool isPrimary = false,
        BotLocomotionDriver? locomotionDriver = null,
        string reason = "DeterministicBuy")
    {
        if (bot == null || !bot.IsValid || bot.InGameMoneyServices == null) return;
        if (bot.InGameMoneyServices.Account < cost) return;

        string prevPrimary = GetPrimaryWeaponDesignerName(bot);
        if (isPrimary)
        {
            // Proteção explícita: jamais substitui uma AWP salva por rifle comum!
            if (prevPrimary.Contains("awp", StringComparison.OrdinalIgnoreCase) && !itemName.Contains("awp", StringComparison.OrdinalIgnoreCase))
            {
                return;
            }
            RemovePrimaryWeapons(bot);
        }

        int cashBefore = bot.InGameMoneyServices.Account;
        bot.InGameMoneyServices.Account -= cost;
        Utilities.SetStateChanged(bot, "CCSPlayerController", "m_pInGameMoneyServices");
        bot.GiveNamedItem(itemName);

        TelemetryLogger?.LogEvent("ECONOMIA - ITEM",
            $"{bot.PlayerName} adquiriu {itemName} (anterior={prevPrimary}, custo=${cost}, saldo=${cashBefore}->${bot.InGameMoneyServices.Account}, motivo={reason})");

        if (locomotionDriver != null)
        {
            locomotionDriver.ForceEquipBestFirearm(bot);
        }
        else
        {
            EquipBestWeapon(bot);
        }
    }

    public static bool HasValuablePrimaryWeapon(CCSPlayerController bot)
    {
        var pawn = bot.PlayerPawn.Value;
        if (pawn == null || pawn.WeaponServices == null) return false;

        foreach (var handle in pawn.WeaponServices.MyWeapons)
        {
            var weapon = handle.Value;
            if (weapon != null && weapon.IsValid && !string.IsNullOrEmpty(weapon.DesignerName))
            {
                string name = weapon.DesignerName.ToLowerInvariant();
                if (name.Contains("awp") || name.Contains("ak47") || name.Contains("m4a1") || name.Contains("m4a4") ||
                    name.Contains("ssg08") || name.Contains("galilar") || name.Contains("famas") || name.Contains("aug") || name.Contains("sg553"))
                {
                    return true;
                }
            }
        }
        return false;
    }

    public bool HasTier1PrimaryWeapon(CCSPlayerController bot)
    {
        var pawn = bot.PlayerPawn.Value;
        if (pawn == null || pawn.WeaponServices == null) return false;

        foreach (var handle in pawn.WeaponServices.MyWeapons)
        {
            var weapon = handle.Value;
            if (weapon != null && weapon.IsValid && !string.IsNullOrEmpty(weapon.DesignerName))
            {
                string name = weapon.DesignerName.ToLowerInvariant();
                if (name.Contains("awp") || name.Contains("ak47") || name.Contains("m4a1"))
                {
                    return true;
                }
            }
        }
        return false;
    }

    public bool HasSpecificWeapon(CCSPlayerController bot, string weaponSubName)
    {
        var pawn = bot.PlayerPawn.Value;
        if (pawn == null || pawn.WeaponServices == null) return false;

        foreach (var handle in pawn.WeaponServices.MyWeapons)
        {
            var weapon = handle.Value;
            if (weapon != null && weapon.IsValid && !string.IsNullOrEmpty(weapon.DesignerName))
            {
                if (weapon.DesignerName.Contains(weaponSubName, StringComparison.OrdinalIgnoreCase))
                {
                    return true;
                }
            }
        }
        return false;
    }

    // =========================================================================
    // DISCIPLINA DA C4 NO FREEZE TIME
    // =========================================================================
    public void EnforceC4Discipline(List<CCSPlayerController> trBots, CCSPlayerController? human, RoleManager roleManager)
    {
        if (human != null && human.IsValid && BotLocomotionDriver.HasC4(human))
        {
            return;
        }

        var c4Bot = trBots.FirstOrDefault(b => b.IsValid && b.PawnIsAlive && BotLocomotionDriver.HasC4(b));
        if (c4Bot == null) return;

        var role = roleManager.GetBotRole(c4Bot);
        if (role == BotRole.EntryFragger || role == BotRole.Anchor)
        {
            var receiverBot = trBots.FirstOrDefault(b => b.Slot != c4Bot.Slot && b.PawnIsAlive && roleManager.GetBotRole(b) == BotRole.Rotator)
                           ?? trBots.FirstOrDefault(b => b.Slot != c4Bot.Slot && b.PawnIsAlive && roleManager.GetBotRole(b) == BotRole.AWPer)
                           ?? trBots.FirstOrDefault(b => b.Slot != c4Bot.Slot && b.PawnIsAlive);

            if (receiverBot != null)
            {
                var pawn = c4Bot.PlayerPawn.Value;
                bool c4Removed = false;
                if (pawn?.WeaponServices?.MyWeapons != null)
                {
                    foreach (var handle in pawn.WeaponServices.MyWeapons)
                    {
                        var w = handle.Value;
                        if (w != null && w.IsValid && !string.IsNullOrEmpty(w.DesignerName) && w.DesignerName.Contains("c4", StringComparison.OrdinalIgnoreCase))
                        {
                            w.Remove();
                            c4Removed = true;
                            break;
                        }
                    }
                }

                if (c4Removed && !BotLocomotionDriver.HasC4(receiverBot))
                {
                    receiverBot.GiveNamedItem("weapon_c4");
                    TelemetryLogger?.LogEvent("ECONOMIA - ITEM",
                        $"Transferência de C4 no FreezeTime: {c4Bot.PlayerName} ({role}) -> {receiverBot.PlayerName} ({roleManager.GetBotRole(receiverBot)})");
                    UtilityAndClockCoordinator.PrintTeamChatAndRadio(
                        c4Bot,
                        CsTeam.Terrorist,
                        c4Bot.PlayerName,
                        $"Passei a C4 pro suporte ({receiverBot.PlayerName}) pra eu abrir espaço na frente!",
                        "affirmative");
                }
            }
        }
    }

    public static void EquipBestWeapon(CCSPlayerController bot)
    {
        if (bot == null || !bot.IsValid || !bot.PawnIsAlive) return;

        bool hasPrimary = HasValuablePrimaryWeapon(bot);
        if (hasPrimary)
        {
            bot.ExecuteClientCommand("slot1");
        }
        else
        {
            bot.ExecuteClientCommand("slot2");
        }

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

    public static void RemovePrimaryWeapons(CCSPlayerController player)
    {
        if (player == null || !player.IsValid) return;
        var pawn = player.PlayerPawn.Value;
        if (pawn?.WeaponServices?.MyWeapons == null) return;

        foreach (var handle in pawn.WeaponServices.MyWeapons)
        {
            var w = handle.Value;
            if (w != null && w.IsValid && !string.IsNullOrEmpty(w.DesignerName))
            {
                if (CombatAdapter.IsPrimaryWeapon(w.DesignerName))
                {
                    w.Remove();
                }
            }
        }
        EquipBestWeapon(player);
    }

    public void PerformPostRoundLooting(List<CCSPlayerController> aliveBots, BotLocomotionDriver locomotionDriver)
    {
        var groundWeapons = Utilities.FindAllEntitiesByDesignerName<CBasePlayerWeapon>("weapon_ak47")
            .Concat(Utilities.FindAllEntitiesByDesignerName<CBasePlayerWeapon>("weapon_m4a1_silencer"))
            .Concat(Utilities.FindAllEntitiesByDesignerName<CBasePlayerWeapon>("weapon_m4a1"))
            .Concat(Utilities.FindAllEntitiesByDesignerName<CBasePlayerWeapon>("weapon_awp"))
            .Where(w => w.IsValid && (w.OwnerEntity == null || !w.OwnerEntity.IsValid) && w.AbsOrigin != null)
            .ToList();

        if (groundWeapons.Count == 0) return;

        foreach (var bot in aliveBots)
        {
            if (!bot.IsValid || !bot.PawnIsAlive || bot.PlayerPawn.Value == null || bot.PlayerPawn.Value.AbsOrigin == null) continue;

            if (HasTier1PrimaryWeapon(bot)) continue;

            var botPos = bot.PlayerPawn.Value.AbsOrigin;

            var bestWeapon = groundWeapons
                .Where(w => w.IsValid && w.AbsOrigin != null)
                .OrderBy(w => (w.AbsOrigin! - botPos).Length())
                .FirstOrDefault();

            if (bestWeapon == null) continue;

            var weaponPos = bestWeapon.AbsOrigin;
            if (weaponPos == null) continue;

            float dist = (weaponPos - botPos).Length();
            if (dist > 600.0f) continue;

            groundWeapons.Remove(bestWeapon);

            string designer = bestWeapon.DesignerName;
            string cleanName = designer switch
            {
                "weapon_ak47" => "AK-47",
                "weapon_m4a1_silencer" => "M4A1-S",
                "weapon_m4a1" => "M4A4",
                "weapon_awp" => "AWP",
                _ => "arma superior"
            };

            if (dist <= 140.0f)
            {
                string prevWep = GetPrimaryWeaponDesignerName(bot);
                RemovePrimaryWeapons(bot);
                if (bestWeapon.IsValid) bestWeapon.Remove();
                bot.GiveNamedItem(designer);
                TelemetryLogger?.LogEvent("ECONOMIA - ITEM",
                    $"{bot.PlayerName} coletou {designer} do chão pós-round (anterior={prevWep})");

                UtilityAndClockCoordinator.PrintTeamChatAndRadio(
                    bot,
                    bot.Team,
                    bot.PlayerName,
                    $"Peguei uma {cleanName} do chão pro próximo round!",
                    "cheer");
            }
            else
            {
                locomotionDriver.NavigateToPosition(bot, weaponPos.X, weaponPos.Y, weaponPos.Z, hurry: true);
                Server.NextFrame(() =>
                {
                    if (bot.IsValid && bot.PawnIsAlive && bestWeapon.IsValid)
                    {
                        string prevWep = GetPrimaryWeaponDesignerName(bot);
                        RemovePrimaryWeapons(bot);
                        bestWeapon.Remove();
                        bot.GiveNamedItem(designer);
                        TelemetryLogger?.LogEvent("ECONOMIA - ITEM",
                            $"{bot.PlayerName} coletou {designer} do chão pós-round (anterior={prevWep})");
                        UtilityAndClockCoordinator.PrintTeamChatAndRadio(
                            bot,
                            bot.Team,
                            bot.PlayerName,
                            $"Peguei uma {cleanName} do chão pro próximo round!",
                            "cheer");
                    }
                });
            }
        }
    }
}
