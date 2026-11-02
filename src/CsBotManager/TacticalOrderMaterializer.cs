#pragma warning disable CS8600, CS8602, CS8604, CS8620
using System;
using System.Collections.Generic;
using System.Linq;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace CsBotManager;

public static class TacticalOrderMaterializer
{
	public static Dictionary<string, BotTacticalOrder> MaterializeTacticalOrders(string tacticId, CsTeam side, IReadOnlyDictionary<BotRole, int>? roleAssignments, MapProfileManager? mapProfile)
	{
		//IL_000c: Unknown result type (might be due to invalid IL or missing references)
		//IL_000e: Invalid comparison between Unknown and I4
		Dictionary<string, BotTacticalOrder> dictionary = new Dictionary<string, BotTacticalOrder>(StringComparer.OrdinalIgnoreCase);
		bool flag = (int)side == 3;
		string text = tacticId.ToLowerInvariant().Trim();
		if (flag)
		{
			if (text.Contains("anti-split b") || (text.Contains("b") && text.Contains("underpass")))
			{
				dictionary[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
				{
					TargetArea = "Mid Window",
					RoleAction = "Sniper window overwatch on Top Mid to Underpass",
					StagingSpotId = "ct_mid_window_deep_awp",
					ExecuteSpotId = "ct_mid_window_crouch",
					Stance = EngagementStance.PASSIVE_HOLD,
					FallbackSpotId = "ct_spawn_safe"
				};
				dictionary[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
				{
					TargetArea = "Bombsite B",
					RoleAction = "Early Van contest against Apartments B",
					StagingSpotId = "ct_b_van_peek",
					ExecuteSpotId = "ct_b_short_corner",
					Stance = EngagementStance.AGGRESSIVE_POKE,
					FallbackSpotId = "ct_b_bench_deep"
				};
				dictionary[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
				{
					TargetArea = "Bombsite B",
					RoleAction = "Crossfire Short/Catwalk and Market window",
					StagingSpotId = "ct_b_short_corner",
					ExecuteSpotId = "ct_b_site_default_crouch",
					Stance = EngagementStance.JIGGLE_INFO,
					FallbackSpotId = "ct_b_market_window"
				};
				dictionary[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
				{
					TargetArea = "Bombsite A",
					RoleAction = "Solo passive anchor on Ticket/Stairs",
					StagingSpotId = "ct_a_ticket_passive",
					ExecuteSpotId = "ct_a_stairs_cross",
					Stance = EngagementStance.PASSIVE_HOLD,
					FallbackSpotId = "ct_spawn_safe"
				};
			}
			else if (text.Contains("meio") || text.Contains("mid") || text.Contains("connector"))
			{
				dictionary[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
				{
					TargetArea = "Mid Window",
					RoleAction = "Hold sniper line on Top Mid",
					StagingSpotId = "ct_mid_window_deep_awp",
					ExecuteSpotId = "ct_mid_window_crouch",
					Stance = EngagementStance.PASSIVE_HOLD,
					FallbackSpotId = "ct_jungle_safe"
				};
				dictionary[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
				{
					TargetArea = "Connector",
					RoleAction = "Aggressive contest in Connector/Short",
					StagingSpotId = "ct_mid_connector_headshot",
					ExecuteSpotId = "ct_mid_short_catwalk",
					Stance = EngagementStance.AGGRESSIVE_POKE,
					FallbackSpotId = "ct_a_stairs_cross"
				};
				dictionary[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
				{
					TargetArea = "Bombsite A",
					RoleAction = "Support Connector and hold A Ramp",
					StagingSpotId = "ct_a_stairs_cross",
					ExecuteSpotId = "ct_a_ticket_passive",
					Stance = EngagementStance.JIGGLE_INFO,
					FallbackSpotId = "ct_spawn_safe"
				};
				dictionary[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
				{
					TargetArea = "Bombsite B",
					RoleAction = "Anchor B Site and watch Van",
					StagingSpotId = "ct_b_van_peek",
					ExecuteSpotId = "ct_b_site_default_crouch",
					Stance = EngagementStance.JIGGLE_INFO,
					FallbackSpotId = "ct_b_bench_deep"
				};
			}
			else if (text.Contains("stack a") || (text.Contains("a") && text.Contains("retake b")))
			{
				dictionary[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
				{
					TargetArea = "Bombsite A",
					RoleAction = "Ticket sniper covering A Ramp",
					StagingSpotId = "ct_a_ticket_passive",
					ExecuteSpotId = "ct_a_triple_jiggle",
					Stance = EngagementStance.PASSIVE_HOLD,
					FallbackSpotId = "ct_spawn_safe"
				};
				dictionary[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
				{
					TargetArea = "Bombsite A",
					RoleAction = "Close Palace and Ramp contest",
					StagingSpotId = "ct_a_palace_close_poke",
					ExecuteSpotId = "ct_a_firebox_oneanddone",
					Stance = EngagementStance.AGGRESSIVE_POKE,
					FallbackSpotId = "ct_a_ninja_hide"
				};
				dictionary[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
				{
					TargetArea = "Bombsite A",
					RoleAction = "Jungle support and stairs crossfire",
					StagingSpotId = "ct_a_stairs_cross",
					ExecuteSpotId = "ct_a_jungle_support",
					Stance = EngagementStance.JIGGLE_INFO,
					FallbackSpotId = "ct_jungle_safe"
				};
				dictionary[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
				{
					TargetArea = "Bombsite B",
					RoleAction = "Deep anchor info on B bench for retake",
					StagingSpotId = "ct_b_bench_deep",
					ExecuteSpotId = "ct_b_site_default_crouch",
					Stance = EngagementStance.PASSIVE_HOLD,
					FallbackSpotId = "ct_b_market_window"
				};
			}
			else
			{
				dictionary[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
				{
					TargetArea = "Mid Window",
					RoleAction = "Window sniper overwatch",
					StagingSpotId = "ct_mid_window_crouch",
					ExecuteSpotId = "ct_mid_window_deep_awp",
					Stance = EngagementStance.PASSIVE_HOLD,
					FallbackSpotId = "ct_jungle_safe"
				};
				dictionary[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
				{
					TargetArea = "Bombsite A",
					RoleAction = "A Ramp and Palace contest",
					StagingSpotId = "ct_a_palace_close_poke",
					ExecuteSpotId = "ct_a_stairs_cross",
					Stance = EngagementStance.AGGRESSIVE_POKE,
					FallbackSpotId = "ct_a_ticket_passive"
				};
				dictionary[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
				{
					TargetArea = "Connector",
					RoleAction = "Connector/Short rotation pivot",
					StagingSpotId = "ct_mid_connector_headshot",
					ExecuteSpotId = "ct_a_stairs_cross",
					Stance = EngagementStance.JIGGLE_INFO,
					FallbackSpotId = "ct_spawn_safe"
				};
				dictionary[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
				{
					TargetArea = "Bombsite B",
					RoleAction = "Anchor B Site and watch Apartments",
					StagingSpotId = "ct_b_van_peek",
					ExecuteSpotId = "ct_b_site_default_crouch",
					Stance = EngagementStance.JIGGLE_INFO,
					FallbackSpotId = "ct_b_bench_deep"
				};
			}
		}
		else if (text.Contains("fake a"))
		{
			dictionary[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
			{
				TargetArea = "Ramp A",
				RoleAction = "Fake pressure on A Ramp with sniper line",
				StagingSpotId = "tr_staging_a_ramp",
				ExecuteSpotId = "tr_exec_a_triple_clear",
				Stance = EngagementStance.AGGRESSIVE_POKE,
				FallbackSpotId = "tr_staging_t_roof",
				IsNoiseGroup = true
			};
			dictionary[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
			{
				TargetArea = "Palace",
				RoleAction = "Fake Palace presence with sounds/flashes",
				StagingSpotId = "tr_staging_palace_room",
				ExecuteSpotId = "tr_exec_a_site_default",
				Stance = EngagementStance.AGGRESSIVE_POKE,
				FallbackSpotId = "tr_staging_t_roof",
				IsNoiseGroup = true
			};
			dictionary[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
			{
				TargetArea = "Bombsite B",
				RoleAction = "Fast push Apartments B into site during A fake",
				StagingSpotId = "tr_staging_b_apartments_kitchen",
				ExecuteSpotId = "tr_exec_b_site_plant",
				Stance = EngagementStance.AGGRESSIVE_POKE,
				FallbackSpotId = "tr_staging_b_apartments_house"
			};
			dictionary[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
			{
				TargetArea = "Bombsite B",
				RoleAction = "Advance Apartments B with C4 and plant at B Site",
				StagingSpotId = "tr_staging_b_apartments_kitchen",
				ExecuteSpotId = "tr_exec_b_site_plant",
				Stance = EngagementStance.JIGGLE_INFO,
				FallbackSpotId = "tr_staging_b_apartments_house"
			};
		}
		else if (text.Contains("fake b"))
		{
			dictionary[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
			{
				TargetArea = "Apartments B",
				RoleAction = "Fake pressure on Apartments B",
				StagingSpotId = "tr_staging_b_apartments_house",
				ExecuteSpotId = "tr_exec_b_van_clear",
				Stance = EngagementStance.AGGRESSIVE_POKE,
				FallbackSpotId = "tr_spawn_safe",
				IsNoiseGroup = true
			};
			dictionary[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
			{
				TargetArea = "Underpass",
				RoleAction = "Fake Underpass noise and push towards Catwalk",
				StagingSpotId = "tr_staging_underpass_top",
				ExecuteSpotId = "tr_exec_b_market_push",
				Stance = EngagementStance.AGGRESSIVE_POKE,
				FallbackSpotId = "tr_staging_t_roof",
				IsNoiseGroup = true
			};
			dictionary[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
			{
				TargetArea = "Palace",
				RoleAction = "Infiltrate Palace into A Site during B fake",
				StagingSpotId = "tr_staging_palace_room",
				ExecuteSpotId = "tr_exec_a_site_default",
				Stance = EngagementStance.AGGRESSIVE_POKE,
				FallbackSpotId = "tr_staging_t_roof"
			};
			dictionary[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
			{
				TargetArea = "Ramp A",
				RoleAction = "Advance Ramp A with C4 and plant at A Default",
				StagingSpotId = "tr_staging_a_ramp",
				ExecuteSpotId = "tr_exec_a_site_default",
				Stance = EngagementStance.JIGGLE_INFO,
				FallbackSpotId = "tr_staging_t_roof"
			};
		}
		else if (text.Contains("execução b") || text.Contains("rush b") || text.Contains("tapete"))
		{
			dictionary[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
			{
				TargetArea = "Apartments B",
				RoleAction = "Cover Apartments B and long angle on Van",
				StagingSpotId = "tr_staging_b_apartments_house",
				ExecuteSpotId = "tr_exec_b_van_clear",
				Stance = EngagementStance.PASSIVE_HOLD,
				FallbackSpotId = "tr_spawn_safe"
			};
			dictionary[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
			{
				TargetArea = "Bombsite B",
				RoleAction = "Fast push through Apartments onto Van and Site",
				StagingSpotId = "tr_staging_b_apartments_kitchen",
				ExecuteSpotId = "tr_exec_b_site_plant",
				Stance = EngagementStance.AGGRESSIVE_POKE,
				FallbackSpotId = "tr_staging_b_apartments_house"
			};
			dictionary[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
			{
				TargetArea = "Bombsite B",
				RoleAction = "Follow entry, secure site and plant C4",
				StagingSpotId = "tr_staging_b_apartments_kitchen",
				ExecuteSpotId = "tr_exec_b_site_plant",
				Stance = EngagementStance.JIGGLE_INFO,
				FallbackSpotId = "tr_staging_b_apartments_house"
			};
			dictionary[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
			{
				TargetArea = "Underpass",
				RoleAction = "Lurk Underpass to cut CT Window/Short rotations",
				StagingSpotId = "tr_staging_underpass_top",
				ExecuteSpotId = "tr_exec_b_market_push",
				Stance = EngagementStance.PASSIVE_HOLD,
				FallbackSpotId = "tr_staging_t_roof"
			};
		}
		else if (text.Contains("split b"))
		{
			dictionary[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
			{
				TargetArea = "Top Mid",
				RoleAction = "Sniper pin on Mid Window",
				StagingSpotId = "tr_staging_top_mid_boxes",
				ExecuteSpotId = "tr_exec_b_site_plant",
				Stance = EngagementStance.PASSIVE_HOLD,
				FallbackSpotId = "tr_spawn_safe"
			};
			dictionary[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
			{
				TargetArea = "Catwalk / Short",
				RoleAction = "Push Short/Catwalk into Bombsite B",
				StagingSpotId = "tr_staging_underpass_top",
				ExecuteSpotId = "tr_exec_b_site_plant",
				Stance = EngagementStance.AGGRESSIVE_POKE,
				FallbackSpotId = "tr_staging_top_mid_boxes"
			};
			dictionary[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
			{
				TargetArea = "Apartments B",
				RoleAction = "Advance Apartments with C4 into B Site",
				StagingSpotId = "tr_staging_b_apartments_kitchen",
				ExecuteSpotId = "tr_exec_b_site_plant",
				Stance = EngagementStance.JIGGLE_INFO,
				FallbackSpotId = "tr_staging_b_apartments_house"
			};
			dictionary[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
			{
				TargetArea = "Underpass",
				RoleAction = "Underpass control and flank cover",
				StagingSpotId = "tr_staging_underpass_top",
				ExecuteSpotId = "tr_exec_b_market_push",
				Stance = EngagementStance.JIGGLE_INFO,
				FallbackSpotId = "tr_staging_t_roof"
			};
		}
		else if (text.Contains("split a"))
		{
			dictionary[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
			{
				TargetArea = "Top Mid",
				RoleAction = "Overwatch Top Mid into Connector",
				StagingSpotId = "tr_staging_top_mid_boxes",
				ExecuteSpotId = "tr_exec_mid_connector_push",
				Stance = EngagementStance.PASSIVE_HOLD,
				FallbackSpotId = "tr_spawn_safe"
			};
			dictionary[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
			{
				TargetArea = "Palace",
				RoleAction = "Entry Palace onto A Default",
				StagingSpotId = "tr_staging_palace_room",
				ExecuteSpotId = "tr_exec_a_site_default",
				Stance = EngagementStance.AGGRESSIVE_POKE,
				FallbackSpotId = "tr_staging_t_roof"
			};
			dictionary[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
			{
				TargetArea = "Ramp A",
				RoleAction = "Advance Ramp A with C4 for plant",
				StagingSpotId = "tr_staging_a_ramp",
				ExecuteSpotId = "tr_exec_a_site_default",
				Stance = EngagementStance.JIGGLE_INFO,
				FallbackSpotId = "tr_staging_t_roof"
			};
			dictionary[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
			{
				TargetArea = "Connector",
				RoleAction = "Push Underpass to Connector to pinch A Site",
				StagingSpotId = "tr_staging_underpass_top",
				ExecuteSpotId = "tr_exec_mid_connector_push",
				Stance = EngagementStance.AGGRESSIVE_POKE,
				FallbackSpotId = "tr_staging_top_mid_boxes"
			};
		}
		else
		{
			dictionary[RoleManager.GetOrderKey(BotRole.AWPer)] = new BotTacticalOrder
			{
				TargetArea = "Ramp A",
				RoleAction = "Sniper line on Ticket and CT from Ramp",
				StagingSpotId = "tr_staging_a_ramp",
				ExecuteSpotId = "tr_exec_a_triple_clear",
				Stance = EngagementStance.PASSIVE_HOLD,
				FallbackSpotId = "tr_staging_t_roof"
			};
			dictionary[RoleManager.GetOrderKey(BotRole.EntryFragger)] = new BotTacticalOrder
			{
				TargetArea = "Palace",
				RoleAction = "Entry A Site from Palace room",
				StagingSpotId = "tr_staging_palace_room",
				ExecuteSpotId = "tr_exec_a_site_default",
				Stance = EngagementStance.AGGRESSIVE_POKE,
				FallbackSpotId = "tr_staging_t_roof"
			};
			dictionary[RoleManager.GetOrderKey(BotRole.Rotator)] = new BotTacticalOrder
			{
				TargetArea = "Ramp A",
				RoleAction = "Advance Ramp A with C4 and plant at Default",
				StagingSpotId = "tr_staging_a_ramp",
				ExecuteSpotId = "tr_exec_a_site_default",
				Stance = EngagementStance.JIGGLE_INFO,
				FallbackSpotId = "tr_staging_t_roof"
			};
			dictionary[RoleManager.GetOrderKey(BotRole.Anchor)] = new BotTacticalOrder
			{
				TargetArea = "Top Mid",
				RoleAction = "Lurk Mid/T Roof to cut CT pushes",
				StagingSpotId = "tr_staging_top_mid_boxes",
				ExecuteSpotId = "tr_exec_a_stairs_clear",
				Stance = EngagementStance.PASSIVE_HOLD,
				FallbackSpotId = "tr_spawn_safe"
			};
		}
		if (mapProfile != null)
		{
			foreach (KeyValuePair<string, BotTacticalOrder> item in dictionary)
			{
				BotTacticalOrder value = item.Value;
				if (!string.IsNullOrEmpty(value.StagingSpotId) && mapProfile.GetSpotById(value.StagingSpotId) == null)
				{
					value.StagingSpotId = (flag ? "ct_spawn_safe" : "tr_spawn_safe");
				}
				if (!string.IsNullOrEmpty(value.ExecuteSpotId) && mapProfile.GetSpotById(value.ExecuteSpotId) == null)
				{
					value.ExecuteSpotId = value.StagingSpotId;
				}
			}
		}
		return dictionary;
	}

	public static bool MaterializeCtStandard212Formation(TacticalPlan plan, IReadOnlyList<CCSPlayerController>? ctBots, MapProfileManager? mapProfile, MatchTelemetryLogger? logger, string decisionId)
	{
		if (plan == null)
		{
			return false;
		}
		plan.CtFormationAssignments.Clear();
		List<int> list = ((ctBots != null && ctBots.Count > 0) ? (from b in ctBots
			where (CEntityInstance)(object)b != (CEntityInstance)null && ((CEntityInstance)b).IsValid && b.IsBot
			select b.Slot).ToList() : new List<int> { 2, 3, 6, 7, 9 });
		while (list.Count < 5)
		{
			list.Add(list.Count + 1);
		}
		List<CtFormationAssignment> list2 = new List<CtFormationAssignment>
		{
			new CtFormationAssignment
			{
				Slot = list[0],
				FormationRole = CtFormationRole.A1_Anchor,
				AssignedSite = "A",
				InitialSpot = "ct_a_ticket_passive",
				ExecuteSpot = "ct_a_firebox_oneanddone",
				RotationPolicy = "HoldUntilTrigger",
				HoldMinimumDuration = 20f,
				RotationTrigger = "None"
			},
			new CtFormationAssignment
			{
				Slot = list[1],
				FormationRole = CtFormationRole.A2_Support,
				AssignedSite = "A",
				InitialSpot = "ct_a_palace_close_poke",
				ExecuteSpot = "ct_a_stairs_cross",
				RotationPolicy = "HoldUntilTrigger",
				HoldMinimumDuration = 20f,
				RotationTrigger = "None"
			},
			new CtFormationAssignment
			{
				Slot = list[2],
				FormationRole = CtFormationRole.Mid_Controller,
				AssignedSite = "Mid",
				InitialSpot = "ct_mid_window_crouch",
				ExecuteSpot = "ct_mid_window_deep_awp",
				RotationPolicy = "HoldUntilTrigger",
				HoldMinimumDuration = 15f,
				RotationTrigger = "None"
			},
			new CtFormationAssignment
			{
				Slot = list[3],
				FormationRole = CtFormationRole.B1_Anchor,
				AssignedSite = "B",
				InitialSpot = "ct_b_van_peek",
				ExecuteSpot = "ct_b_site_default_crouch",
				RotationPolicy = "HoldUntilTrigger",
				HoldMinimumDuration = 20f,
				RotationTrigger = "None"
			},
			new CtFormationAssignment
			{
				Slot = list[4],
				FormationRole = CtFormationRole.B2_Support,
				AssignedSite = "B",
				InitialSpot = "ct_b_short_corner",
				ExecuteSpot = "ct_b_bench_deep",
				RotationPolicy = "HoldUntilTrigger",
				HoldMinimumDuration = 20f,
				RotationTrigger = "None"
			}
		};
		int num = list2.Count((CtFormationAssignment a) => a.AssignedSite == "A");
		int num2 = list2.Count((CtFormationAssignment a) => a.AssignedSite == "Mid");
		int num3 = list2.Count((CtFormationAssignment a) => a.AssignedSite == "B");
		int num4 = (from a in list2
			where a.AssignedSite == "A"
			select a.InitialSpot).Distinct().Count();
		int num5 = (from a in list2
			where a.AssignedSite == "B"
			select a.InitialSpot).Distinct().Count();
		bool flag = num == 2 && num2 == 1 && num3 == 2 && num4 == 2 && num5 == 2;
		foreach (CtFormationAssignment item in list2.Where((CtFormationAssignment a) => a.AssignedSite == "B"))
		{
			if (item.ExecuteSpot.Contains("mid", StringComparison.OrdinalIgnoreCase) || item.ExecuteSpot.Contains("ct_a_", StringComparison.OrdinalIgnoreCase))
			{
				flag = false;
			}
		}
		string value = ((!string.IsNullOrEmpty(plan.CurrentTactic)) ? plan.CurrentTactic : (plan.TacticName ?? "Defesa Padrão 2-1-2"));
		if (flag)
		{
			TrackerMetricsAggregator.RecordCtFormation(isValid: true);
			foreach (CtFormationAssignment item2 in list2)
			{
				plan.CtFormationAssignments[item2.Slot] = item2;
				logger?.LogEvent("CT_FORMATION_MATERIALIZED", $"tacticId=\"{value}\" slot={item2.Slot} formationRole={item2.FormationRole} assignedSite={item2.AssignedSite} spotId={item2.InitialSpot} executeSpotId={item2.ExecuteSpot} rotationPolicy={item2.RotationPolicy}");
			}
			return true;
		}
		TrackerMetricsAggregator.RecordCtFormation(isValid: false);
		logger?.LogEvent("CT_FORMATION_INVALID", $"tacticId=\"{value}\" aDefenders={num} midControllers={num2} bDefenders={num3} distinctBSpots={num5} applyingFallback=2-1-2");
		foreach (CtFormationAssignment item3 in list2)
		{
			plan.CtFormationAssignments[item3.Slot] = item3;
		}
		return false;
	}

	public static bool ValidateAndRepairOrders(TacticalPlan plan, CsTeam team, MapProfileManager? mapProfile, MatchTelemetryLogger? logger, string decisionId)
	{
		//IL_0014: Unknown result type (might be due to invalid IL or missing references)
		//IL_001c: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b9: Unknown result type (might be due to invalid IL or missing references)
		//IL_00bb: Invalid comparison between Unknown and I4
		//IL_01c5: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c7: Invalid comparison between Unknown and I4
		//IL_01fe: Unknown result type (might be due to invalid IL or missing references)
		//IL_0345: Unknown result type (might be due to invalid IL or missing references)
		//IL_0347: Invalid comparison between Unknown and I4
		if (plan == null)
		{
			return false;
		}
		plan.Team = team;
		plan.TeamSide = team;
		plan.DecisionId = decisionId;
		string text = ((!string.IsNullOrEmpty(plan.CurrentTactic)) ? plan.CurrentTactic : (plan.TacticName ?? string.Empty));
		bool flag = text.Contains("Fake A", StringComparison.OrdinalIgnoreCase);
		bool flag2 = text.Contains("Fake B", StringComparison.OrdinalIgnoreCase);
		string text2;
		if (flag)
		{
			text2 = "B";
		}
		else if (flag2)
		{
			text2 = "A";
		}
		else if (text.Contains(" B", StringComparison.OrdinalIgnoreCase))
		{
			text2 = "B";
		}
		else
		{
			text2 = (text.Contains(" A", StringComparison.OrdinalIgnoreCase) ? "A" : "Mid");
		}
		if ((int)team == 2)
		{
			if (flag)
			{
				plan.SetFakeExecution("A", "B", 12f, plan.CompletedAtTick, "MaterializedFakeAtoB", decisionId);
			}
			else if (flag2)
			{
				plan.SetFakeExecution("B", "A", 12f, plan.CompletedAtTick, "MaterializedFakeBtoA", decisionId);
			}
			else if (text2 == "B")
			{
				plan.RealTargetSite = "B";
				plan.CurrentTargetSite = "B";
				plan.FakeTargetSite = string.Empty;
				plan.BombObjectiveState.CommitMaterializedSite(decisionId, text, BombsiteTarget.None, BombsiteTarget.B, plan.CompletedAtTick, "MaterializedDirectB");
			}
			else
			{
				plan.RealTargetSite = "A";
				plan.CurrentTargetSite = "A";
				plan.FakeTargetSite = string.Empty;
				plan.BombObjectiveState.CommitMaterializedSite(decisionId, text, BombsiteTarget.None, BombsiteTarget.A, plan.CompletedAtTick, "MaterializedDirectA");
			}
		}
		if ((int)team == 3 && (text.Contains("2-1-2", StringComparison.OrdinalIgnoreCase) || text.Contains("Padrão", StringComparison.OrdinalIgnoreCase)))
		{
			MaterializeCtStandard212Formation(plan, null, mapProfile, logger, decisionId);
		}
		Dictionary<string, BotTacticalOrder> dictionary = MaterializeTacticalOrders(text, team, null, mapProfile);
		bool result = false;
		BotRole[] array = new BotRole[4]
		{
			BotRole.AWPer,
			BotRole.EntryFragger,
			BotRole.Rotator,
			BotRole.Anchor
		};
		BotRole[] array2 = array;
		foreach (BotRole botRole in array2)
		{
			string orderKey = RoleManager.GetOrderKey(botRole);
			if (!plan.BotOrders.TryGetValue(orderKey, out BotTacticalOrder value))
			{
				if (dictionary.TryGetValue(orderKey, out var value2))
				{
					plan.BotOrders[orderKey] = value2;
					result = true;
					logger?.LogEvent("LLM_ORDER_REPAIRED", $"decisionId={decisionId} tacticId=\"{text}\" role={botRole} originalLlmOrder=MISSING materializedOrder=\"{value2.TargetArea}:{value2.StagingSpotId}\" repairReason=OrderMissingInPlan");
				}
				continue;
			}
			bool flag3 = false;
			string value3 = string.Empty;
			bool flag4 = botRole == BotRole.Anchor;
			bool flag5 = (int)team == 2 && botRole == BotRole.Rotator;
			if (text2 == "B")
			{
				if (((botRole == BotRole.EntryFragger) | flag5) && (value.TargetArea.Contains("Mid", StringComparison.OrdinalIgnoreCase) || value.StagingSpotId.Contains("mid", StringComparison.OrdinalIgnoreCase) || value.StagingSpotId.Contains("ramp", StringComparison.OrdinalIgnoreCase)))
				{
					flag3 = true;
					value3 = $"Role {botRole} assigned to Mid/Ramp during Bombsite B tactic";
				}
			}
			else if (text2 == "A" && ((botRole == BotRole.EntryFragger) | flag5) && (value.TargetArea.Contains("Mid", StringComparison.OrdinalIgnoreCase) || value.StagingSpotId.Contains("apartments", StringComparison.OrdinalIgnoreCase) || value.StagingSpotId.Contains("van", StringComparison.OrdinalIgnoreCase)))
			{
				flag3 = true;
				value3 = $"Role {botRole} assigned to Mid/B-Apartments during Bombsite A tactic";
			}
			if (mapProfile != null)
			{
				if (!string.IsNullOrEmpty(value.StagingSpotId) && mapProfile.GetSpotById(value.StagingSpotId) == null)
				{
					flag3 = true;
					value3 = "Staging spot '" + value.StagingSpotId + "' does not exist in map profile";
				}
				if (!string.IsNullOrEmpty(value.ExecuteSpotId) && mapProfile.GetSpotById(value.ExecuteSpotId) == null)
				{
					flag3 = true;
					value3 = "Execute spot '" + value.ExecuteSpotId + "' does not exist in map profile";
				}
			}
			if (flag3 && dictionary.TryGetValue(orderKey, out var value4))
			{
				string value5 = $"{value.TargetArea}:{value.StagingSpotId}->{value.ExecuteSpotId}";
				value.TargetArea = value4.TargetArea;
				value.StagingSpotId = value4.StagingSpotId;
				value.ExecuteSpotId = value4.ExecuteSpotId;
				value.RoleAction = value4.RoleAction;
				value.Stance = value4.Stance;
				value.FallbackSpotId = value4.FallbackSpotId;
				result = true;
				string value6 = $"{value4.TargetArea}:{value4.StagingSpotId}->{value4.ExecuteSpotId}";
				logger?.LogEvent("LLM_ORDER_REPAIRED", $"decisionId={decisionId} tacticId=\"{text}\" role={botRole} originalLlmOrder=\"{value5}\" materializedOrder=\"{value6}\" repairReason=\"{value3}\"");
			}
		}
		return result;
	}

	public static MaterializedRetakePlan MaterializeCtRetakeOrders(string site, Vector bombPos, IReadOnlyList<CCSPlayerController> aliveCtBots, MapProfileManager? mapProfile = null)
	{
		List<(int, Vector, bool, bool)> list = new List<(int, Vector, bool, bool)>();
		if (aliveCtBots != null)
		{
			foreach (CCSPlayerController aliveCtBot in aliveCtBots)
			{
				if ((CEntityInstance)(object)aliveCtBot == (CEntityInstance)null || !((CEntityInstance)aliveCtBot).IsValid)
				{
					continue;
				}
				Vector item = null;
				bool item2 = false;
				bool item3 = false;
				try
				{
					CCSPlayerPawn value = aliveCtBot.PlayerPawn.Value;
					if ((CEntityInstance)(object)value != (CEntityInstance)null)
					{
						item = ((CBaseEntity)value).AbsOrigin;
						item2 = CtRetakeAndDefuseBrain.HasDefuser(aliveCtBot);
						CPlayer_WeaponServices weaponServices = ((CBasePlayerPawn)value).WeaponServices;
						NetworkedVector<CHandle<CBasePlayerWeapon>> val = ((weaponServices != null) ? weaponServices.MyWeapons : null);
						if (val != null && ((IEnumerable<CHandle<CBasePlayerWeapon>>)val).Any((CHandle<CBasePlayerWeapon> w) =>
						{
							CBasePlayerWeapon value2 = w.Value;
							return value2 != null && ((CEntityInstance)value2).DesignerName?.Contains("awp", StringComparison.OrdinalIgnoreCase) == true;
						}))
						{
							item3 = true;
						}
					}
				}
				catch
				{
				}
				list.Add((aliveCtBot.Slot, item, item2, item3));
			}
		}
		return MaterializeCtRetakeOrdersDeterministic(site, bombPos, list, mapProfile);
	}

	public static MaterializedRetakePlan MaterializeCtRetakeOrdersDeterministic(string site, Vector bombPos, IReadOnlyList<(int Slot, Vector? Position, bool HasDefuser, bool HasAwp)> aliveBotsInfo, MapProfileManager? mapProfile = null)
	{
		//IL_0206: Unknown result type (might be due to invalid IL or missing references)
		//IL_01e1: Unknown result type (might be due to invalid IL or missing references)
		//IL_0210: Expected Obj, but got Unknown
		string text = site?.Trim().ToUpperInvariant() ?? "A";
		if (text != "A" && text != "B")
		{
			text = "A";
		}
		Dictionary<int, BotTacticalOrder> dictionary = new Dictionary<int, BotTacticalOrder>();
		Dictionary<int, string> dictionary2 = new Dictionary<int, string>();
		List<string> list = new List<string>();
		if (aliveBotsInfo == null || aliveBotsInfo.Count == 0)
		{
			return new MaterializedRetakePlan
			{
				PlantedSite = ((!(text == "B")) ? BombsiteTarget.A : BombsiteTarget.B),
				BombPosition = bombPos,
				OrdersBySlot = dictionary,
				RoleBySlot = dictionary2,
				MaterializedSpotIds = list
			};
		}
		(int Slot, Vector Position, bool HasDefuser, bool HasAwp) defuserCandidate = aliveBotsInfo.OrderByDescending(((int Slot, Vector Position, bool HasDefuser, bool HasAwp) b) => b.HasDefuser ? 2 : 0).ThenBy(((int Slot, Vector Position, bool HasDefuser, bool HasAwp) b) =>
		{
			if (b.Position == null)
			{
				return float.MaxValue;
			}
			float num2 = b.Position.X - bombPos.X;
			float num3 = b.Position.Y - bombPos.Y;
			return num2 * num2 + num3 * num3;
		}).First();
		dictionary2[defuserCandidate.Slot] = "Defuser";
		List<(int, Vector, bool, bool)> list2 = aliveBotsInfo.Where(((int Slot, Vector Position, bool HasDefuser, bool HasAwp) b) => b.Slot != defuserCandidate.Slot).ToList();
		(int, Vector, bool, bool) tuple = list2.FirstOrDefault(((int Slot, Vector Position, bool HasDefuser, bool HasAwp) b) => b.HasAwp);
		var (num, val, flag, flag2) = tuple;
		if (num != 0 || val != null || flag || flag2)
		{
			dictionary2[tuple.Item1] = "AWPer";
			list2.Remove(tuple);
		}
		Vector entryChokepoint = ((text == "A") ? new Vector((float?)(-820f), (float?)(-840f), (float?)(-160f)) : new Vector((float?)(-1300f), (float?)(-100f), (float?)(-160f)));
		List<(int, Vector, bool, bool)> list3 = list2.OrderBy(((int Slot, Vector Position, bool HasDefuser, bool HasAwp) b) =>
		{
			if (b.Position == null)
			{
				return float.MaxValue;
			}
			float num2 = b.Position.X - entryChokepoint.X;
			float num3 = b.Position.Y - entryChokepoint.Y;
			return num2 * num2 + num3 * num3;
		}).ToList();
		if (list3.Count > 0)
		{
			dictionary2[list3[0].Item1] = "EntryFragger";
		}
		if (list3.Count > 1)
		{
			dictionary2[list3[1].Item1] = "Rotator";
		}
		if (list3.Count > 2)
		{
			dictionary2[list3[2].Item1] = "Anchor";
		}
		if (list3.Count > 3)
		{
			dictionary2[list3[3].Item1] = "Support";
		}
		foreach (var item in aliveBotsInfo)
		{
			string text2 = (dictionary2.TryGetValue(item.Slot, out var value) ? value : "Rotator");
			EngagementStance engagementStance = EngagementStance.AGGRESSIVE_POKE;
			string text3 = "ct_spawn_default";
			string text4;
			string text5;
			string roleAction;
			if (text == "A")
			{
				switch (text2)
				{
				case "Defuser":
					text4 = "ct_retake_a_ticket";
					text5 = "ct_retake_a_defuse_cover";
					roleAction = "Retake Defuser: advance to C4 and secure defuse under cover";
					engagementStance = EngagementStance.AGGRESSIVE_POKE;
					text3 = "ct_retake_a_ticket";
					break;
				case "EntryFragger":
					text4 = "ct_retake_a_connector";
					text5 = "ct_retake_a_defuse_cover";
					roleAction = "Retake PrimaryEntry: breach via Connector and clear site";
					engagementStance = EngagementStance.AGGRESSIVE_POKE;
					text3 = "ct_retake_a_connector";
					break;
				case "AWPer":
					text4 = "ct_retake_a_jungle";
					text5 = "ct_retake_a_stairs";
					roleAction = "Retake AWPer: long angle cover from Jungle/Stairs";
					engagementStance = EngagementStance.PASSIVE_HOLD;
					text3 = "ct_retake_a_jungle";
					break;
				case "Rotator":
					text4 = "ct_retake_a_stairs";
					text5 = "ct_retake_a_defuse_cover";
					roleAction = "Retake SecondaryEntry: support Stairs/Connector trade";
					engagementStance = EngagementStance.AGGRESSIVE_POKE;
					text3 = "ct_retake_a_stairs";
					break;
				default:
					text4 = "ct_retake_a_ticket";
					text5 = "ct_retake_a_stairs";
					roleAction = "Retake Cover/FlankBlock: watch Palace/Ramp flank";
					engagementStance = EngagementStance.PASSIVE_HOLD;
					text3 = "ct_retake_a_ticket";
					break;
				}
			}
			else
			{
				switch (text2)
				{
				case "Defuser":
					text4 = "ct_retake_b_entry";
					text5 = "ct_retake_b_defuse_cover";
					roleAction = "Retake Defuser: push B site and initiate defuse";
					engagementStance = EngagementStance.AGGRESSIVE_POKE;
					text3 = "ct_retake_b_entry";
					break;
				case "EntryFragger":
					text4 = "ct_retake_b_short";
					text5 = "ct_retake_b_entry";
					roleAction = "Retake PrimaryEntry: contest Short/Catwalk into site";
					engagementStance = EngagementStance.AGGRESSIVE_POKE;
					text3 = "ct_retake_b_short";
					break;
				case "AWPer":
					text4 = "ct_retake_b_awp_cover";
					text5 = "ct_retake_b_market";
					roleAction = "Retake AWPer: sniper line from Market window/door";
					engagementStance = EngagementStance.PASSIVE_HOLD;
					text3 = "ct_retake_b_awp_cover";
					break;
				case "Rotator":
					text4 = "ct_retake_b_market";
					text5 = "ct_retake_b_entry";
					roleAction = "Retake SecondaryEntry: flood from Market into site";
					engagementStance = EngagementStance.AGGRESSIVE_POKE;
					text3 = "ct_retake_b_market";
					break;
				default:
					text4 = "ct_retake_b_market";
					text5 = "ct_retake_b_short";
					roleAction = "Retake Cover/FlankBlock: hold Apartments push";
					engagementStance = EngagementStance.PASSIVE_HOLD;
					text3 = "ct_retake_b_market";
					break;
				}
			}
			if (text4.StartsWith("tr_", StringComparison.OrdinalIgnoreCase) || text5.StartsWith("tr_", StringComparison.OrdinalIgnoreCase))
			{
				throw new InvalidOperationException("CROSS_TEAM_WAYPOINT_IN_RETAKE: staging=" + text4 + ", execute=" + text5);
			}
			dictionary[item.Slot] = new BotTacticalOrder
			{
				TargetArea = "Bombsite " + text,
				RoleAction = roleAction,
				StagingSpotId = text4,
				ExecuteSpotId = text5,
				Stance = engagementStance,
				FallbackSpotId = text3
			};
			if (!list.Contains(text4))
			{
				list.Add(text4);
			}
			if (!list.Contains(text5))
			{
				list.Add(text5);
			}
		}
		return new MaterializedRetakePlan
		{
			PlantedSite = ((!(text == "B")) ? BombsiteTarget.A : BombsiteTarget.B),
			BombPosition = bombPos,
			OrdersBySlot = dictionary,
			RoleBySlot = dictionary2,
			MaterializedSpotIds = list
		};
	}
}
