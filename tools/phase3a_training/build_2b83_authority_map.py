#!/usr/bin/env python3
"""
MARCO 2B.8.3 - ISOLAMENTO DA AUTORIDADE NATIVA DE LOCOMOCAO NO CANARY CT
Script-First builder for static authority inventory, graph, tick-order contract,
lease contract, and isolation experiment matrix.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "training_runs" / "positioning_v2_real_temporal" / "opening_route_canary_v1" / "movement_authority_isolation_v1"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. input_snapshot.json
    tracked_inputs = [
        "src/CsBotManager/OpeningRouteCanaryController.cs",
        "src/CsBotManager/OpeningRoutePlanner.cs",
        "src/CsBotManager/BotLocomotionDriver.cs",
        "src/CsBotManager/MovementArbitrator.cs",
        "src/CsBotManager/MovementExecutionTracker.cs",
        "src/CsBotManager/MobilityController.cs",
        "src/CsBotManager/PacingAndFallbackController.cs",
        "src/CsBotManager/CtDefenseController.cs",
        "src/CsBotManager/CsBotManagerPlugin.cs",
        "training_runs/positioning_v2_real_temporal/opening_route_canary_v1/route_executor_patch_v1/deliverable_evidence.json",
        "training_runs/positioning_v2_real_temporal/opening_route_canary_v1/route_executor_patch_v1/ct_canary_metrics.json",
        "training_runs/positioning_v2_real_temporal/opening_route_canary_v1/route_executor_patch_v1/ct_canary_telemetry.jsonl",
        "training_runs/positioning_v2_real_temporal/opening_route_canary_v1/route_executor_patch_v1/replay_after_fix.json",
        "training_runs/positioning_v2_real_temporal/opening_route_planner_v1/opening_route_catalog_de_mirage_v1.json",
    ]
    input_artifacts = []
    for rel in tracked_inputs:
        p = REPO_ROOT / rel
        if p.exists():
            input_artifacts.append({
                "relative_path": rel,
                "sha256": sha256_file(p),
                "size_bytes": p.stat().st_size,
                "nature": "REAL",
            })

    external_plugins_dir = Path(r"H:\CS2_AI_Server\game\csgo\addons\counterstrikesharp\plugins")
    external_dlls = [
        "BotState/BotState.dll",
        "BotControllerImpl/BotControllerImpl.dll",
        "BotAimImprover/BotAimImprover.dll",
        "BotRandomizer/BotRandomizer.dll",
        "BotHiderImpl/BotHiderImpl.dll",
    ]
    external_snapshots = []
    for rel_dll in external_dlls:
        p = external_plugins_dir / rel_dll
        if p.exists():
            external_snapshots.append({
                "plugin_dll": rel_dll,
                "sha256": sha256_file(p),
                "size_bytes": p.stat().st_size,
                "nature": "REAL",
            })

    input_snapshot = {
        "schema_version": "input_snapshot_2b83_v1",
        "marco": "2B.8.3",
        "title": "ISOLAMENTO DA AUTORIDADE NATIVA DE LOCOMOCAO NO CANARY CT",
        "generated_at_utc": now_iso,
        "baseline_observations_from_2b82": {
            "offline_targeted_tests": "77/77",
            "offline_ct_routes_navmesh_connected": "38/38",
            "offline_replay_arrivals": "10/10 (100.0%)",
            "offline_replay_on_time": "10/10 (100.0%)",
            "live_canary_non_interrupted_arrivals": "1/7 (14.29%)",
            "live_canary_on_time": "1/7 (14.29%)",
            "live_canary_timeouts": 3,
            "live_canary_detour_ratio": 1.3889,
            "root_cause_hypothesis": "Target applied by Opening Route Canary is overwritten by native CCSBot pathfinding (MoveToState::m_goalPosition +0x2e8 / m_taskEntity +0x5d4 / HuntState +0x220) and external plugin BotState (Smarter-Bot v1.10.2) + internal competing writers.",
        },
        "input_artifacts": input_artifacts,
        "external_plugin_binaries_inspected": external_snapshots,
    }
    (OUT_DIR / "input_snapshot.json").write_text(json.dumps(input_snapshot, indent=2), encoding="utf-8")

    # 2. movement_writer_inventory.json
    writers = [
        {
            "writer_id": "INTERNAL_OPENING_ROUTE_CANARY_CONTROLLER",
            "layer": "INTERNAL_CSBOTMANAGER",
            "component": "OpeningRouteCanaryController / OpeningRouteCanaryGuard",
            "source_file": "src/CsBotManager/OpeningRouteCanaryController.cs",
            "method_or_symbol": "EvaluateCanaryBotTick / TryStartRoundCanary",
            "fields_written": [
                "MovementIntent (IntentSource=OPENING_ROUTE_CANARY, Priority=TACTICAL_ORDER)",
                "BotLocomotionDriver.NavigateToPosition(bot, ActiveWaypoint, ...)",
                "BotApi.SwitchBotWeapon(slot, 9001) [Knife in safe segment]",
                "BotLocomotionDriver.ForceEquipBestFirearm(bot) [At readiness point / threat / cancel]",
            ],
            "trigger_condition": "Active during opening phase for 1 leased CT canary bot slot when CSBOT_OPENING_CANARY_ENABLED=true.",
            "execution_frequency": "Every Canary evaluation tick (~8 Hz / 8 ticks)",
            "conflicts_with_canary": False,
            "isolation_action": "AUTHORIZED_LEASE_OWNER",
        },
        {
            "writer_id": "INTERNAL_BOT_LOCOMOTION_DRIVER_NAVIGATE",
            "layer": "INTERNAL_CSBOTMANAGER",
            "component": "BotLocomotionDriver",
            "source_file": "src/CsBotManager/BotLocomotionDriver.cs",
            "method_or_symbol": "NavigateToSpot / NavigateToPosition / ApplyNativeNavigation / NativeCcsBotLocomotionBridge.ApplyIsolatedMoveTo",
            "fields_written": [
                "CCSBot.GoalPosition (+0x5e4)",
                "CCSBot.MoveToState.m_goalPosition (+0x2e8..+0x2f0)",
                "CCSBot.MoveToState.m_routeType (+0x2f4 = 1 FASTEST_ROUTE)",
                "CCSBot.m_state (+0x5c0 = &m_moveToState +0x2e0)",
                "CCSBot.m_task (+0x5d0 = 10 HOLD_POSITION after ComputePath)",
                "CCSBot.TaskEntity.Raw (+0x5d4 = 0xFFFFFFFF)",
                "CCSBot.GoalEntity.Raw (+0x5f0 = 0xFFFFFFFF)",
                "CCSBot.RepathTimer (+0x4f10..+0x4f18)",
                "CCSBot.SafeTime (+0x61ac), HasVisitedEnemySpawn (+0x61b0), IsEnemySniperVisible (+0x5f8)",
            ],
            "trigger_condition": "When MovementArbitrator selects winning MovementIntent or Canary dispatches waypoint.",
            "execution_frequency": "On waypoint dispatch and verified every tick during active lease.",
            "conflicts_with_canary": True,
            "conflict_mechanism": "If non-canary callers (Utility AI, PacingAndFallbackController, CtDefenseController) invoke NavigateToSpot/NavigateToPosition on the canary slot without lease validation, they overwrite Canary waypoint.",
            "isolation_action": "GATE_BY_MOVEMENT_AUTHORITY_LEASE_AND_USE_NATIVE_MOVETO_BRIDGE",
        },
        {
            "writer_id": "INTERNAL_BOT_LOCOMOTION_DRIVER_HOLD_POSITION",
            "layer": "INTERNAL_CSBOTMANAGER",
            "component": "BotLocomotionDriver",
            "source_file": "src/CsBotManager/BotLocomotionDriver.cs",
            "method_or_symbol": "HoldPosition",
            "fields_written": [
                "CCSBot.GoalPosition (+0x5e4 = current position)",
                "CCSBot.LookAtSpot (+0x5fc8)",
                "CCSBot.IsCrouching (+0x60ca)",
                "CCSBot.WaitTimer (+0x5aa8)",
            ],
            "trigger_condition": "Called during stagger hold before PlannedReleaseTick or when holding tactical spot.",
            "execution_frequency": "Per tick during stagger hold or post-arrival hold.",
            "conflicts_with_canary": True,
            "conflict_mechanism": "Previously lacked IsOpeningCanaryActiveSlot check when invoked by Utility AI.",
            "isolation_action": "REJECT_NON_CANARY_CALLERS_WHILE_LEASE_ACTIVE",
        },
        {
            "writer_id": "INTERNAL_BOT_LOCOMOTION_DRIVER_GRENADE_WATCHDOG",
            "layer": "INTERNAL_CSBOTMANAGER",
            "component": "BotLocomotionDriver",
            "source_file": "src/CsBotManager/BotLocomotionDriver.cs",
            "method_or_symbol": "CheckGrenadeEquipWatchdog / ThrowUtility",
            "fields_written": [
                "ForceEquipBestFirearm (BotApi.SwitchBotWeapon / ExecuteClientCommand slot1/slot2)",
                "ActiveThrowSessions",
            ],
            "trigger_condition": "CheckGrenadeEquipWatchdog forced firearm equip at RoundStartTime + 10.0s whenever active weapon was not firearm (including knife!).",
            "execution_frequency": "Every tick after 10.0s round elapsed.",
            "conflicts_with_canary": True,
            "conflict_mechanism": "Forced gun equip during Canary knife segment or triggered utility throw mid-route.",
            "isolation_action": "SUPPRESS_ON_LEASED_CANARY_SLOT_WHILE_KNIFE_ALLOWED_AND_REJECT_UTILITY_THROW",
        },
        {
            "writer_id": "INTERNAL_MOBILITY_CONTROLLER_KNIFE_LOGIC",
            "layer": "INTERNAL_CSBOTMANAGER",
            "component": "MobilityController",
            "source_file": "src/CsBotManager/MobilityController.cs",
            "method_or_symbol": "UpdateTick",
            "fields_written": [
                "controller.ExecuteClientCommandFromServer('slot3' / 'slot1')",
            ],
            "trigger_condition": "Every 10 ticks (~0.16s) during opening 12s based on 600u distance to AssignedSpot.",
            "execution_frequency": "Every 10 ticks (~6.4 Hz)",
            "conflicts_with_canary": True,
            "conflict_mechanism": "Fought Canary's readiness point and KnifeAllowed segment by issuing slot3/slot1 based on heuristic distance.",
            "isolation_action": "SKIP_LEASED_CANARY_SLOT_IN_MOBILITY_CONTROLLER",
        },
        {
            "writer_id": "INTERNAL_PACING_AND_FALLBACK_CONTROLLER",
            "layer": "INTERNAL_CSBOTMANAGER",
            "component": "PacingAndFallbackController",
            "source_file": "src/CsBotManager/PacingAndFallbackController.cs",
            "method_or_symbol": "OnRoundFreezeEnd / TriggerExecute / ApplyExecuteOrders / UpdateTick",
            "fields_written": [
                "LocomotionDriver.NavigateToSpot(bot, stageSpot / execSpot / fallbackSpot)",
                "LocomotionDriver.ThrowUtility(bot, 45)",
            ],
            "trigger_condition": "Staging timers on round freeze end and execute triggers.",
            "execution_frequency": "Event-driven on staging timer expiration and fallback triggers.",
            "conflicts_with_canary": True,
            "conflict_mechanism": "Issued ThrowUtility and NavigateToSpot on CT bots after staging timer without checking Canary lease.",
            "isolation_action": "SKIP_LEASED_CANARY_SLOT_DURING_OPENING_LEASE",
        },
        {
            "writer_id": "INTERNAL_CT_DEFENSE_CONTROLLER",
            "layer": "INTERNAL_CSBOTMANAGER",
            "component": "CtDefenseController",
            "source_file": "src/CsBotManager/CtDefenseController.cs",
            "method_or_symbol": "OnRoundFreezeEnd / UpdateTick",
            "fields_written": [
                "LocomotionDriver.ThrowUtility(supportBot / anchorBot, ...)",
                "LocomotionDriver.NavigateToSpot(supportBot / anchorBot, ...)",
            ],
            "trigger_condition": "1.5s and 2.5s timers after OnRoundFreezeEnd for CT duo plays, and retake/push triggers.",
            "execution_frequency": "Timers at +1.5s / +2.5s and periodic tick checks.",
            "conflicts_with_canary": True,
            "conflict_mechanism": "Overwrote Canary CT bot navigation and forced grenade throw at +1.5s/+2.5s into the round.",
            "isolation_action": "SKIP_LEASED_CANARY_SLOT_DURING_OPENING_LEASE",
        },
        {
            "writer_id": "INTERNAL_MICRO_MOVE_ENGINE_AND_TRACKER",
            "layer": "INTERNAL_CSBOTMANAGER",
            "component": "MovementExecutionTracker / MicroMoveEngine",
            "source_file": "src/CsBotManager/MovementExecutionTracker.cs",
            "method_or_symbol": "UpdateBotTick / EvaluateRecovery",
            "fields_written": [
                "BotApi.SetBotUsercmdVector",
                "BotApi.ForceBotAction(IN_JUMP / IN_DUCK)",
                "Repath / AlternateSpot recovery",
            ],
            "trigger_condition": "When stuck tracker detects progress stall or obstacle.",
            "execution_frequency": "Every MovementExecutionTracker update.",
            "conflicts_with_canary": True,
            "conflict_mechanism": "Section 6 forbids continuous UsercmdVector or IN_JUMP as primary Canary locomotion; Canary has its own deterministic blocker/recovery handling.",
            "isolation_action": "DISABLE_USERCMD_AND_JUMP_RECOVERY_ON_LEASED_CANARY_SLOT",
        },
        {
            "writer_id": "EXTERNAL_PLUGIN_BOTSTATE_SMARTER_BOT",
            "layer": "EXTERNAL_CSSHARP_PLUGIN",
            "component": "BotState (Smarter-Bot v1.10.2)",
            "source_file": "H:/CS2_AI_Server/game/csgo/addons/counterstrikesharp/plugins/BotState/BotState.dll",
            "method_or_symbol": "ApplyBotState / UpdateBotBehavior / UpdateBotMovement / RecoverStuckBot / ReequipGunForActiveBots",
            "fields_written": [
                "CCSBot.SafeTime = 0f (+0x61ac), HasVisitedEnemySpawn = true (+0x61b0) [Forces HuntState]",
                "CCSBot.IsEnemySniperVisible = true (+0x5f8), SawEnemySniperTimer = 600s (+0x5fc..+0x600)",
                "CCSBot.IsCrouching = true (+0x60ca) + Pawn.AbsVelocity (+215 u/s air boost)",
                "CCSBot.JumpTimestamp = 0f, StuckJumpTimer = now, RepathTimer = now (+100 u/s backward impulse)",
                "BotControllerBridge.SwitchBotWeapon (ReequipGunForActiveBots every 1.0s switches knife -> gun!)",
            ],
            "trigger_condition": "Runs on every bot where !controller.HasBeenControlledByPlayerThisRound.",
            "execution_frequency": "Every server tick (OnTick) + 1.0s repeating timer (ReequipGunForActiveBots).",
            "conflicts_with_canary": True,
            "conflict_mechanism": "1) Sets SafeTime=0 and HasVisitedEnemySpawn=true on freeze end, pushing CCSBot into HuntState; 2) Sets IsEnemySniperVisible=true every tick causing sniper panic jumps/detours; 3) ReequipGunForActiveBots overrides Canary knife run every 1.0s; 4) RecoverStuckBot forces jumps and repaths.",
            "isolation_action": "SET_HAS_BEEN_CONTROLLED_BY_PLAYER_THIS_ROUND_TRUE_ON_LEASED_CANARY_SLOT_AND_RESTORE_ON_RELEASE",
        },
        {
            "writer_id": "EXTERNAL_PLUGIN_BOT_CONTROLLER_IMPL",
            "layer": "EXTERNAL_CSSHARP_PLUGIN",
            "component": "BotControllerImpl (v0.7.1)",
            "source_file": "H:/CS2_AI_Server/game/csgo/addons/counterstrikesharp/plugins/BotControllerImpl/BotControllerImpl.dll",
            "method_or_symbol": "CBasePlayerController_ProcessUsercmds hook",
            "fields_written": [
                "CUserCmd.flForwardMove / flSideMove / flUpMove (when g_BotMoveVectorActive[slot])",
                "CUserCmd.nButtons (when g_BotForceActionButtons[slot] != 0)",
                "CUserCmd.nWeaponSelect (when g_BotPendingWeaponSwitch[slot] != 0)",
            ],
            "trigger_condition": "Passive native bridge; only modifies CUserCmd when invoked via IBotControllerApi.",
            "execution_frequency": "Every ProcessUsercmds tick when requested by caller.",
            "conflicts_with_canary": False,
            "isolation_action": "CLEAR_USERCMD_VECTOR_AND_FORCE_ACTION_FOR_CANARY_SLOT_USE_WEAPON_SWITCH_ONLY",
        },
        {
            "writer_id": "EXTERNAL_PLUGIN_BOT_AIM_IMPROVER",
            "layer": "EXTERNAL_CSSHARP_PLUGIN",
            "component": "BotAimImprover (v1.4.2)",
            "source_file": "H:/CS2_AI_Server/game/csgo/addons/counterstrikesharp/plugins/BotAimImprover/BotAimImprover.dll",
            "method_or_symbol": "OnTick (aim viewangles only when enemy visible)",
            "fields_written": [
                "Bot EyeAngles / LookAt when enemy visible",
            ],
            "trigger_condition": "Only active when enemy is visible (which immediately ends Canary lease via ENEMY_SEEN).",
            "execution_frequency": "Every tick during combat.",
            "conflicts_with_canary": False,
            "isolation_action": "NONE_REQUIRED_CANARY_RELEASES_ON_ENEMY_SEEN",
        },
        {
            "writer_id": "NATIVE_CCSBOT_UPDATE_PATH_MOVEMENT",
            "layer": "NATIVE_SERVER_DLL",
            "component": "CCSBot::UpdatePathMovement (server.dll RVA 0x2ec110)",
            "source_file": "H:/CS2_AI_Server/game/csgo/bin/win64/server.dll",
            "method_or_symbol": "CCSBot::UpdatePathMovement (RVA 0x2ec110, write at RVA 0x2ec173)",
            "fields_written": [
                "CCSBot::m_goalPosition (+0x5e4..+0x5ec)",
                "CCSBot::m_pathIndex (+0x4f00)",
            ],
            "trigger_condition": "Every tick while CCSBot follows m_path[256] (+0x688..+0x4e87).",
            "execution_frequency": "Every server tick (64 Hz)",
            "conflicts_with_canary": True,
            "conflict_mechanism": "CCSBot::m_goalPosition (+0x5e4) is an internal sub-goal along m_path[], NOT the macro destination! Writing only +0x5e4 without updating MoveToState::m_goalPosition (+0x2e8) and invoking MoveToState::OnEnter / CCSBot::ComputePath (RVA 0x2c1770) results in UpdatePathMovement immediately overwriting +0x5e4 with the old path's next node on the very next tick.",
            "isolation_action": "WRITE_MOVETOSTATE_GOAL_0x2E8_AND_INVOKE_MOVETOSTATE_ONENTER_COMPUTE_PATH_FASTEST_ROUTE",
        },
        {
            "writer_id": "NATIVE_CCSBOT_MOVETOSTATE_ONUPDATE_TASK_ENTITY",
            "layer": "NATIVE_SERVER_DLL",
            "component": "MoveToState::OnUpdate (server.dll RVA 0x337680)",
            "source_file": "H:/CS2_AI_Server/game/csgo/bin/win64/server.dll",
            "method_or_symbol": "MoveToState::OnUpdate (RVA 0x337680, entity goal overwrite at RVA 0x33774e..0x337978)",
            "fields_written": [
                "MoveToState::m_goalPosition (+0x2e8..+0x2f0)",
                "CCSBot::ComputePath (RVA 0x2c1770)",
                "CCSBot::SetState (transitions to IdleState +0x218 on arrival or path failure)",
            ],
            "trigger_condition": "When m_taskEntity (+0x5d4) != 0xFFFFFFFF (e.g., Bombsite entity assigned by IdleState::OnUpdate at round start).",
            "execution_frequency": "Every server tick while in MoveToState (+0x2e0)",
            "conflicts_with_canary": True,
            "conflict_mechanism": "If m_taskEntity (+0x5d4) holds a valid entity handle (such as a Bombsite), MoveToState::OnUpdate recomputes the path to m_taskEntity->WorldSpaceCenter() and overwrites MoveToState::m_goalPosition (+0x2e8)!",
            "isolation_action": "CLEAR_TASK_ENTITY_0x5D4_AND_GOAL_ENTITY_0x5F0_TO_0xFFFFFFFF_AND_SET_TASK_10_HOLD_POSITION",
        },
        {
            "writer_id": "NATIVE_CCSBOT_IDLESTATE_AND_HUNTSTATE",
            "layer": "NATIVE_SERVER_DLL",
            "component": "IdleState::OnUpdate (RVA 0x335920) & HuntState::OnUpdate (RVA 0x3351c0)",
            "source_file": "H:/CS2_AI_Server/game/csgo/bin/win64/server.dll",
            "method_or_symbol": "IdleState::OnUpdate (RVA 0x335920) / HuntState::OnUpdate (RVA 0x3351c0)",
            "fields_written": [
                "CCSBot::m_state (+0x5c0 -> &m_huntState +0x220 or &m_moveToState +0x2e0)",
                "CCSBot::m_task (+0x5d0) and CCSBot::m_taskEntity (+0x5d4)",
                "CCSBot::MoveTo (RVA 0x2d6690)",
            ],
            "trigger_condition": "When CCSBot enters IdleState (e.g., at round start or after reaching intermediate waypoint) or HuntState (when SafeTime expires).",
            "execution_frequency": "On state transition / every tick while in IdleState or HuntState.",
            "conflicts_with_canary": True,
            "conflict_mechanism": "IdleState picks a random Bombsite or HuntState picks a random NavArea across the map and calls ComputePath.",
            "isolation_action": "FORCE_STATE_TO_MOVETOSTATE_0x2E0_WITH_SAFE_TIME_25S_AND_DISPATCH_NEXT_WAYPOINT_BEFORE_IDLE_TRANSITION",
        },
    ]

    inventory_doc = {
        "schema_version": "movement_writer_inventory_v1",
        "marco": "2B.8.3",
        "generated_at_utc": now_iso,
        "total_writers_cataloged": len(writers),
        "writers_by_layer": {
            "INTERNAL_CSBOTMANAGER": sum(1 for w in writers if w["layer"] == "INTERNAL_CSBOTMANAGER"),
            "EXTERNAL_CSSHARP_PLUGIN": sum(1 for w in writers if w["layer"] == "EXTERNAL_CSSHARP_PLUGIN"),
            "NATIVE_SERVER_DLL": sum(1 for w in writers if w["layer"] == "NATIVE_SERVER_DLL"),
        },
        "conflicting_writers_count": sum(1 for w in writers if w["conflicts_with_canary"]),
        "writers": writers,
    }
    (OUT_DIR / "movement_writer_inventory.json").write_text(json.dumps(inventory_doc, indent=2), encoding="utf-8")

    # 3. movement_authority_graph.json
    graph_doc = {
        "schema_version": "movement_authority_graph_v1",
        "marco": "2B.8.3",
        "generated_at_utc": now_iso,
        "scope": "Delta locomotion authority flow for Opening Route Canary CT isolation",
        "nodes": [
            {"id": "CsBotManagerPlugin.OnTick", "type": "ENTRYPOINT", "layer": "INTERNAL_CSBOTMANAGER"},
            {"id": "OpeningRouteCanaryGuard", "type": "CONTROLLER", "layer": "INTERNAL_CSBOTMANAGER"},
            {"id": "MovementAuthorityLeaseManager", "type": "LEASE_GUARD", "layer": "INTERNAL_CSBOTMANAGER"},
            {"id": "MovementArbitrator", "type": "ARBITRATOR", "layer": "INTERNAL_CSBOTMANAGER"},
            {"id": "BotLocomotionDriver", "type": "DRIVER", "layer": "INTERNAL_CSBOTMANAGER"},
            {"id": "NativeCcsBotLocomotionBridge", "type": "NATIVE_BRIDGE", "layer": "INTERNAL_CSBOTMANAGER"},
            {"id": "PacingAndFallbackController", "type": "COMPETING_WRITER", "layer": "INTERNAL_CSBOTMANAGER"},
            {"id": "CtDefenseController", "type": "COMPETING_WRITER", "layer": "INTERNAL_CSBOTMANAGER"},
            {"id": "MobilityController", "type": "COMPETING_WRITER", "layer": "INTERNAL_CSBOTMANAGER"},
            {"id": "MovementExecutionTracker", "type": "COMPETING_WRITER", "layer": "INTERNAL_CSBOTMANAGER"},
            {"id": "BotState_SmarterBot", "type": "EXTERNAL_PLUGIN", "layer": "EXTERNAL_CSSHARP_PLUGIN"},
            {"id": "BotControllerImpl", "type": "EXTERNAL_PLUGIN", "layer": "EXTERNAL_CSSHARP_PLUGIN"},
            {"id": "CCSBot_MoveToState_0x2E0", "type": "NATIVE_STATE", "layer": "NATIVE_SERVER_DLL"},
            {"id": "CCSBot_ComputePath_0x2C1770", "type": "NATIVE_PATHFINDER", "layer": "NATIVE_SERVER_DLL"},
            {"id": "CCSBot_UpdatePathMovement_0x2EC110", "type": "NATIVE_FOLLOWER", "layer": "NATIVE_SERVER_DLL"},
        ],
        "edges": [
            {"from": "CsBotManagerPlugin.OnTick", "to": "OpeningRouteCanaryGuard", "relation": "STEP_1_TO_5_EVALUATE_CANARY"},
            {"from": "OpeningRouteCanaryGuard", "to": "MovementAuthorityLeaseManager", "relation": "ACQUIRE_VALIDATE_OR_RELEASE_LEASE"},
            {"from": "MovementAuthorityLeaseManager", "to": "PacingAndFallbackController", "relation": "SUPPRESS_ON_LEASED_SLOT"},
            {"from": "MovementAuthorityLeaseManager", "to": "CtDefenseController", "relation": "SUPPRESS_ON_LEASED_SLOT"},
            {"from": "MovementAuthorityLeaseManager", "to": "MobilityController", "relation": "SUPPRESS_ON_LEASED_SLOT"},
            {"from": "MovementAuthorityLeaseManager", "to": "MovementExecutionTracker", "relation": "SUPPRESS_USERCMD_AND_JUMP_ON_LEASED_SLOT"},
            {"from": "MovementAuthorityLeaseManager", "to": "BotState_SmarterBot", "relation": "ISOLATE_VIA_HasBeenControlledByPlayerThisRound"},
            {"from": "OpeningRouteCanaryGuard", "to": "MovementArbitrator", "relation": "PUBLISH_OPENING_ROUTE_CANARY_INTENT"},
            {"from": "MovementArbitrator", "to": "BotLocomotionDriver", "relation": "DISPATCH_WINNING_CANARY_WAYPOINT"},
            {"from": "BotLocomotionDriver", "to": "NativeCcsBotLocomotionBridge", "relation": "APPLY_ISOLATED_MOVETO"},
            {"from": "NativeCcsBotLocomotionBridge", "to": "CCSBot_MoveToState_0x2E0", "relation": "WRITE_GOAL_0x2E8_ROUTE_FASTEST_CLEAR_TASK_ENTITY"},
            {"from": "CCSBot_MoveToState_0x2E0", "to": "CCSBot_ComputePath_0x2C1770", "relation": "SYNCHRONOUS_ONENTER_A_STAR_NAVMESH_PATH"},
            {"from": "CCSBot_ComputePath_0x2C1770", "to": "CCSBot_UpdatePathMovement_0x2EC110", "relation": "FOLLOW_M_PATH_WITHOUT_BUNNYHOP"},
        ],
    }
    (OUT_DIR / "movement_authority_graph.json").write_text(json.dumps(graph_doc, indent=2), encoding="utf-8")

    # 4. tick_order_contract_v1.json
    tick_order_doc = {
        "schema_version": "tick_order_contract_v1",
        "marco": "2B.8.3",
        "generated_at_utc": now_iso,
        "enforced_steps": [
            {
                "step_index": 1,
                "step_name": "COLLECT_WORLD_STATE",
                "description": "Read pawn position, velocity, active weapon, round freeze state, enemy sightings, damage, hostile utility, and C4 state.",
            },
            {
                "step_index": 2,
                "step_name": "EVALUATE_CANARY_INTERRUPTION_TRIGGERS",
                "description": "Check all immediate cancellation triggers: ENEMY_SEEN, DAMAGE_TAKEN, HOSTILE_UTILITY, C4_RELEVANT, PLAN_CHANGED, ROLE_CHANGED, BOT_DIED, TIMEOUT, INVALID_WAYPOINT, BLOCKED_PATH_UNRECOVERABLE.",
            },
            {
                "step_index": 3,
                "step_name": "VALIDATE_MOVEMENT_AUTHORITY_LEASE",
                "description": "Verify CSBOT_OPENING_CANARY_ENABLED, lease active status, single-slot invariant, round_id match, and expires_tick.",
            },
            {
                "step_index": 4,
                "step_name": "SUPPRESS_COMPETING_WRITERS_IF_LEASE_ACTIVE",
                "description": "Reject/suppress PacingAndFallbackController, CtDefenseController, MobilityController, CheckGrenadeEquipWatchdog, non-canary NavigateToSpot/HoldPosition, and isolate external BotState via HasBeenControlledByPlayerThisRound=true on the leased slot only.",
            },
            {
                "step_index": 5,
                "step_name": "PUBLISH_CANARY_INTENT_AND_WEAPON_READINESS",
                "description": "Advance waypoint if within arrival radius, enforce stagger hold before PlannedReleaseTick, equip knife in safe segment or firearm at readiness point, and publish OPENING_ROUTE_CANARY intent.",
            },
            {
                "step_index": 6,
                "step_name": "RESOLVE_MOVEMENT_ARBITRATION",
                "description": "MovementArbitrator selects OPENING_ROUTE_CANARY intent while lease is active (unless preempted by emergency/combat which releases lease).",
            },
            {
                "step_index": 7,
                "step_name": "APPLY_WINNING_INTENT_TO_NATIVE_ENGINE",
                "description": "Invoke NativeCcsBotLocomotionBridge.ApplyIsolatedMoveTo to set MoveToState::m_goalPosition (+0x2e8), clear TaskEntity/GoalEntity, and trigger MoveToState::OnEnter (CCSBot::ComputePath FASTEST_ROUTE) over native NavMesh without continuous UsercmdVector or IN_JUMP.",
            },
            {
                "step_index": 8,
                "step_name": "VERIFY_END_OF_TICK_GOAL_INTEGRITY",
                "description": "Compare goal_before_canary, goal_after_canary, and goal_end_of_tick (MoveToState::m_goalPosition +0x2e8) to detect and count any unauthorized overwrite.",
            },
            {
                "step_index": 9,
                "step_name": "RECORD_PER_TICK_AUTHORITY_TELEMETRY",
                "description": "Emit structured per-tick telemetry record (tick, round_id, bot_slot, lease_active, active_waypoint, goal_before/after/end, competing_writers_detected, native_state, weapon_state, velocity_xy).",
            },
            {
                "step_index": 10,
                "step_name": "RELEASE_LEASE_AND_RESTORE_FALLBACK_ON_TERMINATION",
                "description": "Immediately upon arrival, interruption, round end, or unload, release lease, restore HasBeenControlledByPlayerThisRound and native state fields, and dispatch Utility AI fallback NavigateToSpot so the bot is never orphaned.",
            },
        ],
    }
    (OUT_DIR / "tick_order_contract_v1.json").write_text(json.dumps(tick_order_doc, indent=2), encoding="utf-8")

    # 5. movement_authority_lease_contract.json
    lease_contract = {
        "schema_version": "movement_authority_lease_contract_v1",
        "marco": "2B.8.3",
        "generated_at_utc": now_iso,
        "lease_fields": {
            "round_id": "int (1-based controlled round index)",
            "bot_slot": "int (0..63 CSSharp player slot)",
            "owner": "OPENING_ROUTE_CANARY",
            "acquired_tick": "int (server tick count at acquisition)",
            "expires_tick": "int (hard deadline tick = acquired_tick + max_lease_ticks)",
            "allowed_scope": "opening_navigation_only",
            "is_active": "bool",
            "release_reason": "string (CANARY_ARRIVED | ENEMY_SEEN | DAMAGE_TAKEN | HOSTILE_UTILITY | C4_INTERACTION | PLAN_CHANGED | ROLE_CHANGED | BOT_DIED | TIMEOUT | INVALID_WAYPOINT | CANARY_BLOCKED_FALLBACK | ROUND_END | KILL_SWITCH_DISABLED | PLUGIN_UNLOAD)",
        },
        "invariants": {
            "max_active_leases_per_round": 1,
            "allowed_team_in_2b83": "CT",
            "allowed_phase": "OPENING_ONLY",
            "forbid_continuous_usercmd_vector": True,
            "forbid_continuous_in_jump": True,
            "immediate_release_on_cancel_trigger": True,
            "restore_native_and_external_flags_on_release": True,
            "zero_active_leases_at_round_end": True,
            "kill_switch_env_var": "CSBOT_OPENING_CANARY_ENABLED",
        },
    }
    (OUT_DIR / "movement_authority_lease_contract.json").write_text(json.dumps(lease_contract, indent=2), encoding="utf-8")

    # 6. isolation_experiment_matrix.json
    experiment_matrix = {
        "schema_version": "isolation_experiment_matrix_v1",
        "marco": "2B.8.3",
        "generated_at_utc": now_iso,
        "experiments": [
            {
                "experiment_id": "EXP_A_BASELINE",
                "name": "Baseline (Current state without lease isolation)",
                "description": "All plugins active, Canary writes only legacy GoalPosition (+0x5e4) without MovementAuthorityLease or MoveToState (+0x2e8) isolation.",
                "target_rounds": 2,
                "expected_observation": "High rate of goal overwrites by native CCSBot::UpdatePathMovement / MoveToState and external BotState.",
            },
            {
                "experiment_id": "EXP_B_EXTERNAL_PLUGINS_DISABLED",
                "name": "External bot plugins temporarily disabled (BotState & BotRandomizer)",
                "description": "BotState and BotRandomizer temporarily disabled to isolate native CCSBot overwrite behavior from external plugin interference; restored immediately after 2 rounds.",
                "target_rounds": 2,
                "expected_observation": "External BotState sniper/knife/jump interference disappears, proving BotState's role, while native CCSBot taskEntity/MoveToState behaviour is observed cleanly.",
            },
            {
                "experiment_id": "EXP_C_CANARY_SLOT_LEASE_ISOLATED",
                "name": "Canary slot isolated via MovementAuthorityLease + Native MoveToState bridge (all plugins active)",
                "description": "All external plugins restored and active; MovementAuthorityLease isolates ONLY the single CT canary slot via NativeCcsBotLocomotionBridge + HasBeenControlledByPlayerThisRound=true during the opening route.",
                "target_rounds": 3,
                "expected_observation": "unauthorized_goal_overwrites = 0, continuous_jump = 0, authority_residue = 0, arrivals >= 2/3 across the 3 simple CT routes.",
            },
            {
                "experiment_id": "EXP_D_CANARY_DISABLED_CONTROL",
                "name": "Canary disabled via kill switch (CSBOT_OPENING_CANARY_ENABLED=false)",
                "description": "Control experiment with Canary disabled via kill switch to confirm 100% normal Utility AI + external plugin operation with zero canary leases.",
                "target_rounds": 2,
                "expected_observation": "canary_controlled_bots = 0, active_leases = 0, Utility AI operates normally.",
            },
        ],
    }
    (OUT_DIR / "isolation_experiment_matrix.json").write_text(json.dumps(experiment_matrix, indent=2), encoding="utf-8")

    print(json.dumps({
        "status": "OK",
        "out_dir": str(OUT_DIR.relative_to(REPO_ROOT)),
        "files_written": [
            "input_snapshot.json",
            "movement_writer_inventory.json",
            "movement_authority_graph.json",
            "tick_order_contract_v1.json",
            "movement_authority_lease_contract.json",
            "isolation_experiment_matrix.json",
        ],
    }))


if __name__ == "__main__":
    main()
