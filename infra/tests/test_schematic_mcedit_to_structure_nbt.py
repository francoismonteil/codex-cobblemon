import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def load_module():
    # infra/schematic-mcedit-to-structure-nbt.py has hyphens, so import via spec.
    root = Path(__file__).resolve().parents[2]
    p = root / "infra" / "schematic-mcedit-to-structure-nbt.py"
    spec = importlib.util.spec_from_file_location("schem_to_struct", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["schem_to_struct"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


class TestSchematicToStructureNBT(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module()

    def test_self_test_writes_loadable_nbt(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "t.nbt"
            rc = self.mod.main(["--self-test", "--output", str(out)])
            self.assertEqual(rc, 0)
            self.assertTrue(out.exists())

            root = self.mod._load_nbt(out)
            self.assertEqual(root.get("size"), [2, 1, 1])
            self.assertEqual(len(root.get("palette", [])), 2)
            self.assertEqual(len(root.get("blocks", [])), 2)


if __name__ == "__main__":
    unittest.main()

