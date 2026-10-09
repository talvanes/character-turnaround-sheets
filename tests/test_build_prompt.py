"""Tests for scripts/build_prompt.py. Run with: python3 -m unittest discover -s tests -v"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_prompt.py"
TEMPLATE = ROOT / "templates" / "character_profile.json"
EXAMPLES = ROOT / "examples"

sys.path.insert(0, str(SCRIPT.parent))
import build_prompt as bp  # noqa: E402


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_cli(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                          capture_output=True, text=True)


def outfit(garments=(), accessories=(), footwear="sneakers", notes=""):
    return {"garments": list(garments), "footwear": footwear,
            "accessories": list(accessories), "notes": notes}


class ForbiddenItemsTest(unittest.TestCase):
    def test_no_accessories_forbids_headwear_and_necklaces(self):
        self.assertEqual(bp.forbidden_items(outfit(["plain white t-shirt"])), ["headwear", "necklaces"])

    def test_necklace_variants_are_recognised(self):
        for acc in ("round brass magnifying loupe on a cord around her neck",
                    "black velvet choker", "small silver locket", "gold chain necklace",
                    "jade pendant", "two thin gold chains", "red neckerchief"):
            with self.subTest(acc=acc):
                self.assertNotIn("necklaces", bp.forbidden_items(outfit(accessories=[acc])))

    def test_headwear_variants_are_recognised(self):
        for acc in ("woven straw panama hat", "red beret", "grey wool beanie", "navy baseball cap",
                    "silk headscarf", "two hats stacked"):
            with self.subTest(acc=acc):
                self.assertNotIn("headwear", bp.forbidden_items(outfit(accessories=[acc])))

    def test_headwear_in_garments_counts(self):
        self.assertNotIn("headwear", bp.forbidden_items(outfit(["white kerchief tied on the head", "sundress"])))

    def test_words_containing_keywords_do_not_match(self):
        # "that" contains "hat", "chainmail" contains "chain", "neckline" contains "neck",
        # "cap sleeves" is a garment detail, not a cap.
        o = outfit(["dress that flows, cap sleeves, sweetheart neckline", "chainmail vest"],
                   accessories=["leather bracelet"])
        self.assertEqual(bp.forbidden_items(o), ["headwear", "necklaces"])

    def test_necklace_only_checked_in_accessories(self):
        # A neckline described in a garment must not unlock necklaces.
        self.assertIn("necklaces", bp.forbidden_items(outfit(["top with a high neck"])))

    def test_accessories_given_as_string(self):
        o = outfit()
        o["accessories"] = "silver locket"
        self.assertEqual(bp.forbidden_items(o), ["headwear"])


class OutfitBlockTest(unittest.TestCase):
    def test_lists_only_given_accessories(self):
        block = bp.outfit_block(outfit(["shirt"], ["watch on her LEFT wrist", "ring"]))
        self.assertIn("- Accessories (ONLY these): watch on her LEFT wrist; ring.", block)

    def test_empty_accessories_forbid_everything(self):
        self.assertIn("NO accessories of any kind", bp.outfit_block(outfit(["shirt"])))

    def test_missing_footwear_defaults_to_barefoot(self):
        self.assertIn("- Footwear: barefoot.", bp.outfit_block({"garments": ["robe"]}))

    def test_string_accessory_is_not_split_into_characters(self):
        block = bp.outfit_block({"garments": ["shirt"], "accessories": "gold watch"})
        self.assertIn("(ONLY these): gold watch.", block)

    def test_notes_are_appended(self):
        self.assertIn("- No satchel.", bp.outfit_block(outfit(["dress"], notes="No satchel.")))


class PromptTest(unittest.TestCase):
    def setUp(self):
        self.p = load(TEMPLATE)

    def test_hero_contains_style_identity_scene_and_skin_guard(self):
        text = bp.hero_prompt(self.p, self.p["outfit"], "standing on a pier at dusk")
        for needle in (self.p["art_style"], self.p["skin"], self.p["hair"],
                       "Scene and pose: standing on a pier at dusk", "Keep skin tone exactly"):
            self.assertIn(needle, text)

    def test_turnaround_layout_and_lighting(self):
        text = bp.turnaround_prompt(self.p, self.p["outfit"], False)
        for needle in ("16:9", "NEUTRAL studio lighting", "four full-body", "2x2 grid",
                       "same body side in every view", "Avoid:"):
            self.assertIn(needle, text)
        self.assertNotIn("EXACT same character", text)

    def test_with_reference_adds_identity_lock(self):
        text = bp.turnaround_prompt(self.p, self.p["outfit"], True)
        self.assertIn("EXACT same character as the reference image", text)
        self.assertIn("change ONLY the outfit", text)

    def test_identity_is_identical_across_modes(self):
        ident = bp.identity_block(self.p)
        self.assertIn(ident, bp.hero_prompt(self.p, self.p["outfit"], "x"))
        self.assertIn(ident, bp.turnaround_prompt(self.p, outfit(["coat"]), True))


class CliTest(unittest.TestCase):
    def test_hero_requires_scene(self):
        r = run_cli(TEMPLATE, "--mode", "hero")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--scene is required", r.stderr)

    def test_outfit_override(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "outfit.json"
            path.write_text(json.dumps(outfit(["yellow raincoat"], ["red beret"])))
            r = run_cli(TEMPLATE, "--mode", "turnaround", "--outfit", path, "--with-reference")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("yellow raincoat", r.stdout)
        self.assertNotIn("striped sundress", r.stdout)

    def test_missing_profile_field_gives_clear_error(self):
        p = copy.deepcopy(load(TEMPLATE))
        del p["skin"]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "profile.json"
            path.write_text(json.dumps(p))
            r = run_cli(path, "--mode", "turnaround")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("missing required field(s): skin", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_invalid_json_gives_clear_error(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "profile.json"
            path.write_text("{not json")
            r = run_cli(path, "--mode", "turnaround")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not valid JSON", r.stderr)

    def test_missing_file_gives_clear_error(self):
        r = run_cli("/nonexistent/profile.json", "--mode", "turnaround")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not found", r.stderr)


class ExamplesTest(unittest.TestCase):
    def test_every_example_builds(self):
        profiles = sorted(EXAMPLES.glob("*/profile.json")) + [TEMPLATE]
        self.assertGreaterEqual(len(profiles), 3)
        for profile in profiles:
            with self.subTest(profile=profile.parent.name):
                r = run_cli(profile, "--mode", "hero", "--scene", "a quiet morning")
                self.assertEqual(r.returncode, 0, r.stderr)
                r = run_cli(profile, "--mode", "turnaround", "--with-reference")
                self.assertEqual(r.returncode, 0, r.stderr)
            for o in sorted(profile.parent.glob("outfit_*.json")):
                with self.subTest(outfit=o.name):
                    r = run_cli(profile, "--mode", "turnaround", "--outfit", o, "--with-reference")
                    self.assertEqual(r.returncode, 0, r.stderr)

    def test_marina_loupe_is_not_forbidden(self):
        p = load(EXAMPLES / "marina" / "profile.json")
        self.assertNotIn("necklaces", bp.forbidden_items(p["outfit"]))

    def test_benedito_sunday_hat_allows_headwear(self):
        o = load(EXAMPLES / "benedito" / "outfit_domingo.json")
        self.assertEqual(bp.forbidden_items(o), ["necklaces"])


class SkillMetadataTest(unittest.TestCase):
    def test_frontmatter_has_name_and_description(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        front = text.split("---", 2)[1]
        self.assertIn("name: character-turnaround-sheets", front)
        self.assertIn("description:", front)

    def test_referenced_resources_exist(self):
        for rel in ("scripts/build_prompt.py", "templates/character_profile.json", "references/lessons.md"):
            self.assertTrue((ROOT / rel).is_file(), rel)


if __name__ == "__main__":
    unittest.main()
