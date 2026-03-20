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


class TestSpawnerCluster(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module("spawner_cluster", "infra/spawner-cluster.py")

    def test_build_data_merge_command_with_entity_filter(self):
        cmd = self.mod.build_data_merge_command(
            (-10, 64, 20),
            ["RequiredPlayerRange:40s", "SpawnCount:8s"],
            match_entity="minecraft:wither_skeleton",
        )
        self.assertIn('execute if data block -10 64 20 {SpawnData:{entity:{id:\\"minecraft:wither_skeleton\\"}}} run ', cmd)
        self.assertTrue(cmd.endswith("data merge block -10 64 20 {RequiredPlayerRange:40s,SpawnCount:8s}"))

    def test_build_clear_command_with_entity_filter(self):
        cmd = self.mod.build_clear_command((1, 2, 3), match_entity="minecraft:skeleton")
        self.assertEqual(
            cmd,
            'execute if data block 1 2 3 {SpawnData:{entity:{id:\\"minecraft:skeleton\\"}}} run setblock 1 2 3 minecraft:air replace',
        )

    def test_parse_args_defaults(self):
        args = self.mod.parse_args(["--center", "1", "2", "3"])
        self.assertEqual(tuple(args.center), (1, 2, 3))
        self.assertEqual(args.dimension, "overworld")
        self.assertFalse(args.apply)
        self.assertFalse(args.clear)


if __name__ == "__main__":
    unittest.main()
