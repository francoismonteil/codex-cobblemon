import importlib.util
import sys
import unittest
from pathlib import Path


def load_module():
    root = Path(__file__).resolve().parents[2]
    p = root / "infra" / "schematic-mcedit-to-commands.py"
    spec = importlib.util.spec_from_file_location("schem_to_cmds", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["schem_to_cmds"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def encode_varints(values):
    out = bytearray()
    for value in values:
        v = int(value)
        while True:
            b = v & 0x7F
            v >>= 7
            if v:
                out.append(b | 0x80)
            else:
                out.append(b)
                break
    return bytes(out)


class TestSchematicToCommands(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module()

    def test_iter_blocks_sponge_v2_decodes_palette_and_block_entities(self):
        root = {
            "Version": self.mod.NbtInt(2),
            "Width": self.mod.NbtShort(2),
            "Height": self.mod.NbtShort(1),
            "Length": self.mod.NbtShort(2),
            "Offset": [self.mod.NbtInt(250), self.mod.NbtInt(0), self.mod.NbtInt(2)],
            "Palette": {
                "minecraft:air": self.mod.NbtInt(0),
                "minecraft:stone": self.mod.NbtInt(1),
                "minecraft:ladder[facing=north,waterlogged=false]": self.mod.NbtInt(2),
                "minecraft:chest[facing=north,type=single,waterlogged=false]": self.mod.NbtInt(3),
            },
            "BlockData": encode_varints([1, 2, 0, 3]),
            "BlockEntities": [
                {
                    "Pos": [self.mod.NbtInt(1), self.mod.NbtInt(0), self.mod.NbtInt(1)],
                    "Id": "minecraft:chest",
                    "Items": [
                        {
                            "Slot": self.mod.NbtByte(0),
                            "id": "minecraft:stone",
                            "Count": self.mod.NbtByte(1),
                        }
                    ],
                }
            ],
        }

        w, h, l, blocks, offset = self.mod._iter_blocks_sponge_v2(root)

        self.assertEqual((w, h, l), (2, 1, 2))
        self.assertEqual(offset, (250, 0, 2))
        self.assertEqual(len(blocks), 3)

        coords = {(b.x, b.y, b.z): b for b in blocks}
        self.assertEqual(coords[(0, 0, 0)].block_state, "minecraft:stone")
        self.assertEqual(coords[(1, 0, 0)].block_state, "minecraft:ladder[facing=north,waterlogged=false]")
        self.assertEqual(coords[(1, 0, 1)].block_state, "minecraft:chest[facing=north,type=single,waterlogged=false]")
        self.assertEqual(
            coords[(1, 0, 1)].block_entity_nbt,
            {
                "Items": [
                    {
                        "Slot": self.mod.NbtByte(0),
                        "id": "minecraft:stone",
                        "Count": self.mod.NbtByte(1),
                    }
                ]
            },
        )

    def test_to_snbt_preserves_numeric_suffixes(self):
        snbt = self.mod._to_snbt(
            {
                "Slot": self.mod.NbtByte(0),
                "Count": self.mod.NbtByte(1),
                "Power": self.mod.NbtShort(2),
                "Age": self.mod.NbtLong(3),
                "Speed": self.mod.NbtFloat(1.5),
                "Exact": self.mod.NbtDouble(2.25),
                "id": "minecraft:ender_pearl",
            }
        )

        self.assertEqual(
            snbt,
            '{Slot:0b,Count:1b,Power:2s,Age:3l,Speed:1.5f,Exact:2.25d,id:"minecraft:ender_pearl"}',
        )

    def test_iter_blocks_sponge_v3_decodes_nested_schematic(self):
        root = {
            "Schematic": {
                "Version": self.mod.NbtInt(3),
                "Width": self.mod.NbtShort(2),
                "Height": self.mod.NbtShort(1),
                "Length": self.mod.NbtShort(2),
                "Offset": [self.mod.NbtInt(-5), self.mod.NbtInt(-1), self.mod.NbtInt(0)],
                "Blocks": {
                    "Palette": {
                        "minecraft:air": self.mod.NbtInt(0),
                        "minecraft:stone": self.mod.NbtInt(1),
                        "minecraft:furnace[facing=north,lit=false]": self.mod.NbtInt(2),
                    },
                    "Data": encode_varints([1, 2, 0, 1]),
                    "BlockEntities": [
                        {
                            "Pos": [self.mod.NbtInt(1), self.mod.NbtInt(0), self.mod.NbtInt(0)],
                            "Id": "minecraft:furnace",
                            "Data": {
                                "id": "minecraft:furnace",
                                "Items": [
                                    {
                                        "Slot": self.mod.NbtByte(1),
                                        "id": "minecraft:bamboo",
                                        "count": self.mod.NbtInt(1),
                                    }
                                ],
                            },
                        }
                    ],
                },
            }
        }

        w, h, l, blocks, offset = self.mod._iter_blocks_sponge_v3(root)

        self.assertEqual((w, h, l), (2, 1, 2))
        self.assertEqual(offset, (-5, -1, 0))
        self.assertEqual(len(blocks), 3)

        coords = {(b.x, b.y, b.z): b for b in blocks}
        self.assertEqual(coords[(0, 0, 0)].block_state, "minecraft:stone")
        self.assertEqual(coords[(1, 0, 0)].block_state, "minecraft:furnace[facing=north,lit=false]")
        self.assertEqual(
            coords[(1, 0, 0)].block_entity_nbt,
            {
                "Items": [
                    {
                        "Slot": self.mod.NbtByte(1),
                        "id": "minecraft:bamboo",
                        "count": self.mod.NbtInt(1),
                    }
                ]
            },
        )

    def test_rotate_block_state_y90_for_common_directional_blocks(self):
        self.assertEqual(
            self.mod._rotate_block_state("minecraft:furnace[facing=north,lit=false]", 1),
            "minecraft:furnace[facing=east,lit=false]",
        )
        self.assertEqual(
            self.mod._rotate_block_state("minecraft:powered_rail[powered=true,shape=east_west,waterlogged=false]", 1),
            "minecraft:powered_rail[powered=true,shape=north_south,waterlogged=false]",
        )
        self.assertEqual(
            self.mod._rotate_block_state("minecraft:glass_pane[east=true,north=false,south=false,waterlogged=false,west=true]", 1),
            "minecraft:glass_pane[south=true,east=false,west=false,waterlogged=false,north=true]",
        )


if __name__ == "__main__":
    unittest.main()
