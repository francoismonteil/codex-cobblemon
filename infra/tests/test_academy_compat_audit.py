import importlib.util
import json
import sys
import unittest
from pathlib import Path


def load_module():
    root = Path(__file__).resolve().parents[2]
    path = root / "infra" / "academy-compat-audit.py"
    spec = importlib.util.spec_from_file_location("academy_compat_audit", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["academy_compat_audit"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


class TestAcademyCompatAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module()
        cls.lock = json.loads((Path(__file__).resolve().parents[2] / "modpack" / "academy-v2" / "stack.lock.json").read_text(encoding="utf-8"))

    def test_extract_dependency_version(self):
        text = 'modImplementation("com.cobblemon:fabric:1.6.1+1.21.1")'
        self.assertEqual(
            self.mod.extract_dependency_version(text, "com.cobblemon:fabric:"),
            "1.6.1+1.21.1",
        )

    def test_compatibility_decision_falls_back_when_versions_do_not_match(self):
        decision = self.mod.compatibility_decision(
            self.lock,
            {"cobblemon_fabric_version": "1.6.1+1.21.1"},
        )
        self.assertEqual(decision["mode"], "fidelity_reduced")
        self.assertEqual(decision["base_cobblemon"], "1.7.3+1.21.1")

    def test_render_markdown_mentions_blocked_components(self):
        report = self.mod.build_report(self.lock)
        markdown = self.mod.render_markdown(report)
        self.assertIn("academy-integration", markdown)
        self.assertIn("fidelity_reduced", markdown)


if __name__ == "__main__":
    unittest.main()
