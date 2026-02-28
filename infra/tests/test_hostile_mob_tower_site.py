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


class FakeTerrainWorld:
    def __init__(self, default_height=70, default_block="minecraft:grass_block"):
        self.default_height = default_height
        self.default_block = default_block
        self.heights = {}
        self.blocks = {}
        self.missing_chunks = set()

    def set_height(self, x, z, y):
        self.heights[(x, z)] = y

    def set_block(self, x, y, z, name):
        self.blocks[(x, y, z)] = name

    def height_at(self, x, z, *, heightmap_type="MOTION_BLOCKING_NO_LEAVES"):
        return self.heights.get((x, z), self.default_height)

    def block_name(self, x, y, z):
        return self.blocks.get((x, y, z), self.default_block if y == self.height_at(x, z) else "minecraft:air")

    def region_exists_for_chunk(self, cx, cz):
        return (cx, cz) not in self.missing_chunks


class TestHostileMobTowerSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module("find_hostile_mob_tower_site", "infra/find-hostile-mob-tower-site.py")

    def test_candidate_origins_sorted_by_preferred_radius(self):
        pts = self.mod.candidate_origins(0, 0, min_distance=64, max_distance=96, step=32, preferred_radius=64)
        self.assertTrue(len(pts) > 0)
        self.assertIn((64, 0), pts[:4])

    def test_evaluate_site_rejects_slope_over_one(self):
        w = FakeTerrainWorld()
        w.set_height(-11, -10, 70)
        w.set_height(11, 11, 72)
        self.assertIsNone(self.mod.evaluate_site(w, 0, 0, floors=3))

    def test_evaluate_site_rejects_liquid_surface(self):
        w = FakeTerrainWorld()
        w.set_block(0, 70, 0, "minecraft:water")
        self.assertIsNone(self.mod.evaluate_site(w, 0, 0, floors=3))

    def test_evaluate_site_accepts_flat_dry_area(self):
        w = FakeTerrainWorld()
        site = self.mod.evaluate_site(w, 0, 0, floors=3)
        self.assertIsNotNone(site)
        self.assertEqual(site["origin"]["y"], 70)

    def test_evaluate_site_rejects_missing_chunk_region(self):
        w = FakeTerrainWorld()
        w.missing_chunks.add((0, 0))
        self.assertIsNone(self.mod.evaluate_site(w, 0, 0, floors=3))


if __name__ == "__main__":
    unittest.main()
