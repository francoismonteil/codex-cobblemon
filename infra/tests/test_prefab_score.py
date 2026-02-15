import importlib.util
import sys
import unittest
from pathlib import Path


def load_prefab_score_module():
    # infra/prefab-score.py has a hyphen, so import via spec.
    root = Path(__file__).resolve().parents[2]
    p = root / "infra" / "prefab-score.py"
    spec = importlib.util.spec_from_file_location("prefab_score", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["prefab_score"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


class FakeWorld:
    def __init__(self, *, light_default=(15, True)):
        self.blocks = {}
        self.light_default = light_default

    def set_block(self, x, y, z, name):
        self.blocks[(x, y, z)] = name

    def block_name(self, x, y, z):
        return self.blocks.get((x, y, z), "minecraft:air")

    def light_info(self, x, y, z):
        return self.light_default


class TestPrefabScore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_prefab_score_module()

    def test_bitstorage_palette_index_padding(self):
        # bits=6 => values_per_long=10 (padding at end of each long).
        palette = [f"b{i}" for i in range(41)]
        expected = list(range(20))

        def pack(vals):
            out = 0
            for i, v in enumerate(vals):
                out |= (v & 0x3F) << (i * 6)
            return out

        data = [pack(expected[:10]), pack(expected[10:20])]
        sec = self.mod.Section(y=0, palette=palette, data=data, block_light=None, sky_light=None)

        for i in range(20):
            self.assertEqual(sec.palette_index(i), expected[i])

    def test_spawnable_surface_strict(self):
        m = self.mod
        self.assertTrue(m.is_spawnable_surface("minecraft:stone_bricks"))
        self.assertFalse(m.is_spawnable_surface("minecraft:oak_slab"))
        self.assertFalse(m.is_spawnable_surface("minecraft:oak_stairs"))
        self.assertFalse(m.is_spawnable_surface("minecraft:white_carpet"))
        self.assertFalse(m.is_spawnable_surface("minecraft:rail"))
        self.assertFalse(m.is_spawnable_surface("minecraft:glass"))
        self.assertFalse(m.is_spawnable_surface("minecraft:oak_leaves"))
        self.assertFalse(m.is_spawnable_surface("minecraft:oak_door"))
        self.assertFalse(m.is_spawnable_surface("minecraft:lantern"))

    def _build_simple_room(self, world, *, floor_y=0):
        # 15x13 footprint at x=0..14, z=0..12
        x1, x2, z1, z2 = 0, 14, 0, 12
        # floor
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                world.set_block(x, floor_y, z, "minecraft:stone_bricks")
        # walls (y=1..4)
        for y in range(floor_y + 1, floor_y + 5):
            for x in range(x1, x2 + 1):
                world.set_block(x, y, z1, "minecraft:stone_bricks")
                world.set_block(x, y, z2, "minecraft:stone_bricks")
            for z in range(z1, z2 + 1):
                world.set_block(x1, y, z, "minecraft:stone_bricks")
                world.set_block(x2, y, z, "minecraft:stone_bricks")
        return (x1, floor_y, z1, x2, floor_y + 10, z2)

    def test_light_unreliable_does_not_penalize_spawn_dark(self):
        m = self.mod
        w = FakeWorld(light_default=(None, False))
        box = self._build_simple_room(w, floor_y=0)

        # Add a basic entrance door (so reachable exists) at facade x=0.
        # Door occupies y=1..2.
        w.set_block(0, 1, 6, "minecraft:oak_door")
        w.set_block(0, 2, 6, "minecraft:oak_door")

        res = m.compute_score(
            w,
            box,
            profile="pokecenter",
            facing="west",
            nav_start_mode="inside_cell",
            doors_passable=True,
            trapdoors_passable=True,
            floor_y=0,
            label="t",
        )

        self.assertFalse(res.metrics["spawn"]["light_data_reliable"])
        self.assertTrue(res.metrics["spawn"]["spawn_check_applicable"])
        self.assertGreater(res.metrics["spawn"]["unknown_light_positions"], 0)
        # No light-based penalty should apply.
        self.assertEqual(res.subs["spawn_proof"], 25)
        self.assertNotIn("spawn_dark", res.caps)

    def test_nav_start_mode_inside_cell_is_stable_when_doors_blocked(self):
        m = self.mod
        w = FakeWorld(light_default=(15, True))
        box = self._build_simple_room(w, floor_y=0)
        w.set_block(0, 1, 6, "minecraft:oak_door")
        w.set_block(0, 2, 6, "minecraft:oak_door")

        res_ok = m.compute_score(w, box, facing="west", nav_start_mode="inside_cell", doors_passable=True, trapdoors_passable=True, floor_y=0, label="ok")
        self.assertGreater(res_ok.metrics["walk"]["reachable"], 0)

        res_blocked = m.compute_score(w, box, facing="west", nav_start_mode="inside_cell", doors_passable=False, trapdoors_passable=True, floor_y=0, label="blocked")
        self.assertGreater(res_blocked.metrics["walk"]["reachable"], 0)

        res_door_cell_blocked = m.compute_score(w, box, facing="west", nav_start_mode="door_cell", doors_passable=False, trapdoors_passable=True, floor_y=0, label="door_cell_blocked")
        self.assertEqual(res_door_cell_blocked.metrics["walk"]["reachable"], 0)

    def test_nav_start_mode_inside_cell_uses_opposite_of_facing(self):
        m = self.mod
        w = FakeWorld(light_default=(15, True))
        box = self._build_simple_room(w, floor_y=0)

        # Facade is "north" (z1), door sits on that wall.
        w.set_block(7, 1, 0, "minecraft:oak_door")
        w.set_block(7, 2, 0, "minecraft:oak_door")

        res_inside = m.compute_score(w, box, facing="north", nav_start_mode="inside_cell", doors_passable=False, trapdoors_passable=True, floor_y=0, label="north_inside")
        self.assertGreater(res_inside.metrics["walk"]["reachable"], 0)

        res_door_cell = m.compute_score(w, box, facing="north", nav_start_mode="door_cell", doors_passable=False, trapdoors_passable=True, floor_y=0, label="north_door_cell")
        self.assertEqual(res_door_cell.metrics["walk"]["reachable"], 0)

    def test_hazards_only_count_in_reachable_interior(self):
        m = self.mod
        w = FakeWorld(light_default=(15, True))
        box = self._build_simple_room(w, floor_y=0)
        w.set_block(0, 1, 6, "minecraft:oak_door")
        w.set_block(0, 2, 6, "minecraft:oak_door")

        # Block passage to the right side with a wall at x=7.
        for z in range(1, 12):
            w.set_block(7, 1, z, "minecraft:stone_bricks")
            w.set_block(7, 2, z, "minecraft:stone_bricks")

        # Place a hazard in the unreachable right side.
        w.set_block(10, 1, 6, "minecraft:lava")

        res = m.compute_score(w, box, facing="west", nav_start_mode="inside_cell", doors_passable=True, trapdoors_passable=True, floor_y=0, label="haz")
        self.assertGreater(res.metrics["walk"]["unreachable_walkables"], 0)
        self.assertEqual(res.metrics["hazards"]["count"], 0)

    def test_spawnable_positions_drop_on_slabs(self):
        m = self.mod
        w = FakeWorld(light_default=(15, True))
        box = self._build_simple_room(w, floor_y=0)
        w.set_block(0, 1, 6, "minecraft:oak_door")
        w.set_block(0, 2, 6, "minecraft:oak_door")

        res_full = m.compute_score(w, box, facing="west", nav_start_mode="inside_cell", doors_passable=True, trapdoors_passable=True, floor_y=0, label="full")
        self.assertGreater(res_full.metrics["spawn"]["spawnable_positions"], 0)

        # Replace the floor with slabs: still walkable, but not a valid hostile spawn surface.
        x1, _y1, z1, x2, _y2, z2 = box
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                w.set_block(x, 0, z, "minecraft:oak_slab")

        res_slab = m.compute_score(w, box, facing="west", nav_start_mode="inside_cell", doors_passable=True, trapdoors_passable=True, floor_y=0, label="slab")
        self.assertEqual(res_slab.metrics["spawn"]["spawnable_positions"], 0)
        self.assertFalse(res_slab.metrics["spawn"]["spawn_check_applicable"])
        self.assertFalse(res_slab.metrics["spawn"]["light_data_reliable"])
        self.assertIsNone(res_slab.metrics["spawn"]["light_data_coverage"])

    def test_cli_help_does_not_crash(self):
        m = self.mod
        import contextlib
        import io

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            with self.assertRaises(SystemExit) as cm:
                m.main(["--help"])
        self.assertEqual(cm.exception.code, 0)

    def test_reachable_ratio_not_biased_by_bbox_padding(self):
        m = self.mod
        w = FakeWorld(light_default=(15, True))
        box = self._build_simple_room(w, floor_y=0)
        w.set_block(0, 1, 6, "minecraft:oak_door")
        w.set_block(0, 2, 6, "minecraft:oak_door")

        # Split interior so reachable_ratio is < 1.
        for z in range(1, 12):
            w.set_block(7, 1, z, "minecraft:stone_bricks")
            w.set_block(7, 2, z, "minecraft:stone_bricks")

        res_base = m.compute_score(w, box, facing="west", nav_start_mode="inside_cell", doors_passable=False, trapdoors_passable=True, floor_y=0, label="base")
        r_base = res_base.metrics["walk"]["reachable_ratio"]
        self.assertGreater(res_base.metrics["walk"]["unreachable_walkables"], 0)
        self.assertLess(r_base, 1.0)

        # Expand bbox by 1 and add an outside walkable ring.
        x1, y1, z1, x2, y2, z2 = box
        box2 = (x1 - 1, y1, z1 - 1, x2 + 1, y2, z2 + 1)
        for x in range(x1 - 1, x2 + 2):
            for z in range(z1 - 1, z2 + 2):
                w.set_block(x, 0, z, "minecraft:stone_bricks")

        res_pad = m.compute_score(w, box2, facing="west", nav_start_mode="inside_cell", doors_passable=False, trapdoors_passable=True, floor_y=0, label="pad")
        r_pad = res_pad.metrics["walk"]["reachable_ratio"]

        self.assertAlmostEqual(r_pad, r_base, places=6)


if __name__ == "__main__":
    unittest.main()
