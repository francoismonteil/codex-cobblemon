import importlib.util
import sys
import unittest
from pathlib import Path


def load_module(name: str, relpath: str):
    root = Path(__file__).resolve().parents[2]
    infra_dir = root / "infra"
    if str(infra_dir) not in sys.path:
        sys.path.insert(0, str(infra_dir))
    path = root / relpath
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


class TestHostileMobTowerAfk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = load_module("hostile_mob_tower_spec", "infra/hostile_mob_tower_spec.py")
        cls.afk = load_module("hostile_mob_tower_afk", "infra/hostile-mob-tower-afk.py")

    def test_kill_room_reference_loses_spawn_positions(self):
        origin = (0, 70, 0)
        pos = self.spec.reference_player_positions(origin, 3)["kill_room_center"]
        metrics = self.spec.spawn_distance_metrics(origin, 3, pos)
        self.assertLess(metrics["min_distance"], 24.0)
        self.assertLess(metrics["active_positions"], metrics["total_positions"])

    def test_roof_reference_disables_all_spawn_positions(self):
        origin = (0, 70, 0)
        pos = self.spec.reference_player_positions(origin, 3)["roof_center"]
        metrics = self.spec.spawn_distance_metrics(origin, 3, pos)
        self.assertEqual(metrics["active_positions"], 0)

    def test_recommended_ground_positions_keep_all_spawn_positions_active(self):
        origin = (0, 70, 0)
        recs = self.spec.recommended_afk_positions(origin, 3)
        self.assertEqual([item["label"] for item in recs], ["south_ground", "north_ground", "east_ground", "west_ground"])
        for item in recs:
            metrics = item["metrics"]
            self.assertEqual(metrics["active_positions"], metrics["total_positions"])
            self.assertGreaterEqual(metrics["min_distance"], 24.0)
            self.assertLessEqual(metrics["max_distance"], 128.0)

    def test_cli_report_exposes_diagnostics_and_recommendations(self):
        report = self.afk.build_report((0, 70, 0), 3)
        self.assertEqual(report["kind"], "hostile_mob_tower_afk_report")
        self.assertEqual(len(report["diagnostics"]), 3)
        self.assertEqual(len(report["recommended_positions"]), 4)


if __name__ == "__main__":
    unittest.main()
