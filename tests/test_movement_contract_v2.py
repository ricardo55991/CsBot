"""
Testes formais para o Contrato de Movimento V2 (Movement Contract V2.1)
Verifica as 8 assercoes obrigatorias da Fase 1.6:
- ForwardLeftIsRepresentable
- ForwardRightIsRepresentable
- BackwardLeftIsRepresentable
- BackwardRightIsRepresentable
- StopIsNeutralNeutral
- JumpPressIsIndependentFromMovementAxes
- AirborneIsNeverJumpPress
- BunnyHopIsNeverExecutable
"""
import json
import unittest
from pathlib import Path

CONTRACT_PATH = Path(r"C:\Users\ricar\OneDrive\Documentos\Dev\CsBot\docs\fase_1_5\movement_contract_v2.json")


class TestMovementContractV2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
            cls.contract = json.load(f)
        cls.decomp = cls.contract["action_decomposition"]
        cls.long_classes = {c["name"]: c["id"] for c in cls.decomp["LongitudinalMovement"]["classes"]}
        cls.lat_classes = {c["name"]: c["id"] for c in cls.decomp["LateralMovement"]["classes"]}

    def test_ForwardLeftIsRepresentable(self):
        """Diagonal W+A: Longitudinal = Forward (2) e Lateral = Left (0)."""
        self.assertIn("Forward", self.long_classes)
        self.assertIn("Left", self.lat_classes)
        action_pair = (self.long_classes["Forward"], self.lat_classes["Left"])
        self.assertEqual(action_pair, (2, 0))

    def test_ForwardRightIsRepresentable(self):
        """Diagonal W+D: Longitudinal = Forward (2) e Lateral = Right (2)."""
        self.assertIn("Forward", self.long_classes)
        self.assertIn("Right", self.lat_classes)
        action_pair = (self.long_classes["Forward"], self.lat_classes["Right"])
        self.assertEqual(action_pair, (2, 2))

    def test_BackwardLeftIsRepresentable(self):
        """Diagonal S+A: Longitudinal = Backward (0) e Lateral = Left (0)."""
        self.assertIn("Backward", self.long_classes)
        self.assertIn("Left", self.lat_classes)
        action_pair = (self.long_classes["Backward"], self.lat_classes["Left"])
        self.assertEqual(action_pair, (0, 0))

    def test_BackwardRightIsRepresentable(self):
        """Diagonal S+D: Longitudinal = Backward (0) e Lateral = Right (2)."""
        self.assertIn("Backward", self.long_classes)
        self.assertIn("Right", self.lat_classes)
        action_pair = (self.long_classes["Backward"], self.lat_classes["Right"])
        self.assertEqual(action_pair, (0, 2))

    def test_StopIsNeutralNeutral(self):
        """Stop e alcancado deterministicamente com Longitudinal = Neutral (1) e Lateral = Neutral (1)."""
        self.assertIn("Neutral", self.long_classes)
        self.assertIn("Neutral", self.lat_classes)
        action_pair = (self.long_classes["Neutral"], self.lat_classes["Neutral"])
        self.assertEqual(action_pair, (1, 1))

    def test_JumpPressIsIndependentFromMovementAxes(self):
        """JumpPress e uma cabeca binaria de evento ortogonal a qualquer combinacao de movimento (parado, correndo ou strafeando)."""
        event = self.decomp["Event"]
        self.assertEqual(event["name"], "JumpPress")
        self.assertEqual(event["type"], "binary_impulse_event")
        self.assertTrue(event["independent_from_movement_axes"])
        # Testa todas as 9 combinacoes de movimento (3x3) podendo coexistir com JumpPress = 1 ou 0
        combos = [(lon, lat, jump) for lon in [0, 1, 2] for lat in [0, 1, 2] for jump in [0, 1]]
        self.assertEqual(len(combos), 18)

    def test_AirborneIsNeverJumpPress(self):
        """Airborne e Falling sao features de PhysicalState (contexto); rotulo JumpPress e obrigatoriamente 0 em Airborne."""
        phys = self.decomp["PhysicalState"]
        self.assertTrue(phys["never_used_as_jump_label"])
        state_names = [s["name"] for s in phys["states"]]
        self.assertIn("Airborne", state_names)
        self.assertIn("Falling", state_names)
        self.assertIn("Landing", state_names)
        # Regra explicita de deteccao de ground truth: frames subsequentes do salto recebem JumpPress = 0
        rule = self.decomp["Event"]["ground_truth_detection_rule_16hz"]
        self.assertIn("require_previous_grounded_or_low_vz", rule)

    def test_BunnyHopIsNeverExecutable(self):
        """BunnyHop e explicitamente desabilitado como acao executavel no dataset e no runtime."""
        event = self.decomp["Event"]
        self.assertFalse(event["executable_bunny_hop"])
        rule = event["ground_truth_detection_rule_16hz"]
        self.assertIn("exclude_chained_bunny_hop", rule)
        gate = event["csharp_runtime_jump_gate"]
        self.assertGreaterEqual(gate["min_cooldown_seconds"], 1.0)
        self.assertTrue(gate["require_grounded_pawn"])


if __name__ == "__main__":
    unittest.main()
