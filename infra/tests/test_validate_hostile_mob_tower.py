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


class FakeWorld:
    def __init__(self):
        self.blocks = {}
        self.light = {}

    def set_block(self, x, y, z, name):
        self.blocks[(x, y, z)] = name

    def block_name(self, x, y, z):
        return self.blocks.get((x, y, z), "minecraft:air")

    def set_light(self, x, y, z, value, ok=True):
        self.light[(x, y, z)] = (value, ok)

    def light_info(self, x, y, z):
        return self.light.get((x, y, z), (0, True))


class TestValidateHostileMobTower(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = load_module("hostile_mob_tower_spec", "infra/hostile_mob_tower_spec.py")
        cls.validator = load_module("validate_hostile_mob_tower", "infra/validate-hostile-mob-tower.py")

    def build_world(self, origin=(0, 70, 0), floors=3):
        world = FakeWorld()
        for pos, block in self.spec.expected_blocks(origin, floors).items():
            world.set_block(*pos, block)
        for pos in self.spec.planned_spawn_positions(origin, floors):
            world.set_light(*pos, 0, True)
        return world

    def test_complete_structure_passes(self):
        world = self.build_world()
        res = self.validator.validate_world(world, (0, 70, 0), floors=3)
        self.assertEqual(res["status"], "pass")

    def test_missing_critical_block_fails(self):
        world = self.build_world()
        critical = next(iter(self.spec.critical_block_expectations((0, 70, 0), 3)))
        world.set_block(*critical, "minecraft:air")
        res = self.validator.validate_world(world, (0, 70, 0), floors=3)
        self.assertEqual(res["status"], "fail")

    def test_lit_spawn_surface_fails(self):
        world = self.build_world()
        pos = next(iter(self.spec.planned_spawn_positions((0, 70, 0), 3)))
        world.set_light(*pos, 1, True)
        res = self.validator.validate_world(world, (0, 70, 0), floors=3)
        self.assertEqual(res["status"], "fail")

    def test_obstructed_shaft_fails(self):
        world = self.build_world()
        world.set_block(0, 80, 0, "minecraft:cobblestone")
        res = self.validator.validate_world(world, (0, 70, 0), floors=3)
        self.assertEqual(res["status"], "fail")

    def test_cleared_mode_requires_no_remaining_critical_blocks(self):
        world = FakeWorld()
        critical_pos, critical_block = next(iter(self.spec.critical_block_expectations((0, 70, 0), 3).items()))
        world.set_block(*critical_pos, critical_block)
        res = self.validator.validate_world(world, (0, 70, 0), floors=3, mode="cleared")
        self.assertEqual(res["status"], "fail")


if __name__ == "__main__":
    unittest.main()
