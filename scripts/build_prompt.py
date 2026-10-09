#!/usr/bin/env python3
"""Build consistent image-generation prompts from a character profile JSON.

Usage:
  build_prompt.py PROFILE.json --mode hero --scene "SCENE TEXT"
  build_prompt.py PROFILE.json --mode turnaround [--with-reference]
  build_prompt.py PROFILE.json --mode turnaround --outfit OUTFIT.json --with-reference

Modes:
  hero        Single illustration of the character in a scene (use 9:16 or user ratio).
  turnaround  Model sheet: 4 full-body views + 2x2 face views on white (use 16:9).

--outfit replaces profile["outfit"] (same schema: garments, footwear, accessories, notes).
Empty accessories => the prompt explicitly forbids all accessories, which prevents
items from the reference image (kerchief, necklace...) carrying over.
"""
import argparse
import json
import re
import sys

REQUIRED_PROFILE_KEYS = ("art_style", "body", "heritage", "skin", "eyes", "face", "hair")

# Keywords meaning the outfit already contains an item of that category.
# Matched as whole words (optional plural), so "hat" does not match "that"
# and "chain" does not match "chainmail".
HEADWEAR_TERMS = ("hat", "sunhat", "beret", "beanie", "bandana", "kerchief", "headscarf",
                  "head scarf", "headband", "turban", "helmet", "baseball cap", "flat cap")
NECKWEAR_TERMS = ("necklace", "pendant", "chain", "cord", "neck", "choker", "locket",
                  "neckerchief")


def _as_list(value):
    """Accept a list of strings or a single string; drop empty entries."""
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    return [str(v).strip() for v in value if str(v).strip()]


def _mentions(text, terms):
    pattern = r"\b(?:" + "|".join(re.escape(t) for t in terms) + r")(?:e?s)?\b"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def identity_block(p):
    return (
        f"Character: {p['body']}, {p['heritage']}, {p['skin']}, {p['eyes']}, "
        f"{p['face']}. Hair: {p['hair']}."
    )


def outfit_block(o):
    lines = ["Outfit:"]
    lines += [f"- {g}" for g in _as_list(o.get("garments"))]
    fw = o.get("footwear") or "barefoot"
    lines.append(f"- Footwear: {fw}.")
    acc = _as_list(o.get("accessories"))
    if acc:
        lines.append("- Accessories (ONLY these): " + "; ".join(acc) + ".")
    else:
        lines.append("- NO accessories of any kind: no jewelry, no headwear, no hair ornaments.")
    if o.get("notes"):
        lines.append(f"- {o['notes']}")
    return "\n".join(lines)


def forbidden_items(o):
    """Item categories added to the Avoid list because the outfit does not include them."""
    acc = " ".join(_as_list(o.get("accessories")))
    garments = " ".join(_as_list(o.get("garments")))
    items = []
    if not _mentions(acc + " " + garments, HEADWEAR_TERMS):
        items.append("headwear")
    if not _mentions(acc, NECKWEAR_TERMS):
        items.append("necklaces")
    return items


def hero_prompt(p, o, scene):
    return "\n\n".join([
        f"Artistic illustration in this style: {p['art_style']}. Soft painterly background, cinematic lighting.",
        identity_block(p),
        outfit_block(o),
        f"Scene and pose: {scene}",
        "Keep skin tone exactly as described even under warm or colored light (light may tint shadows, not the base skin tone).",
        "No text, no watermark. Avoid: explicit nudity, distorted anatomy, extra limbs, malformed hands or feet, photorealism.",
    ])


def turnaround_prompt(p, o, with_reference):
    ref = (
        "Professional character turnaround / model sheet of the EXACT same character as the reference image. "
        "Keep identical face, body proportions, hairstyle, art style and scale; change ONLY the outfit as specified below. "
        "Ignore any clothing or accessories shown in the reference that are not listed below."
        if with_reference else
        "Professional character turnaround / model sheet."
    )
    avoid = ["inconsistent outfit or hair between views", "extra limbs", "malformed hands or feet",
             "cropped bodies", "text labels", "logos or readable brand text", "photorealism", "nudity"]
    avoid += forbidden_items(o)
    return "\n\n".join([
        f"{ref} Clean pure white background, 16:9 landscape layout. Style: {p['art_style']}, "
        "soft even NEUTRAL studio lighting (no golden or colored tint).",
        identity_block(p),
        outfit_block(o),
        "Layout:\n"
        "LEFT / MAIN AREA (about 70% of width): four full-body standing views in one row, same scale, common ground line, "
        "neutral relaxed pose with arms slightly away from the body: (1) front, (2) three-quarter, (3) side profile, "
        "(4) back view showing the back of the outfit and the back of the hair. Head to toe visible, footwear included, nothing cropped. "
        "Wrist/side-specific accessories stay on the same body side in every view.\n"
        "RIGHT AREA (about 30% of width): 2x2 grid of head-and-shoulders close-ups: front, three-quarter, side profile, back of head. "
        "Consistent facial features and hairstyle across all views.",
        "Thin light-grey divider lines between sections, generous white space, soft drop shadows under feet only. "
        "No text, no watermark, no scenery.",
        "Avoid: " + ", ".join(avoid) + ".",
    ])


def load_json(path, label):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        sys.exit(f"error: {label} file not found: {path}")
    except json.JSONDecodeError as e:
        sys.exit(f"error: {label} file is not valid JSON ({path}): {e}")
    if not isinstance(data, dict):
        sys.exit(f"error: {label} file must contain a JSON object: {path}")
    return data


def validate_profile(p, path):
    missing = [k for k in REQUIRED_PROFILE_KEYS if not str(p.get(k) or "").strip()]
    if missing:
        sys.exit(f"error: profile {path} is missing required field(s): {', '.join(missing)}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("profile", help="Character profile JSON (see templates/character_profile.json)")
    ap.add_argument("--mode", choices=["hero", "turnaround"], required=True)
    ap.add_argument("--outfit", help="JSON file overriding the profile outfit")
    ap.add_argument("--scene", default="", help="Scene/pose/background text for hero mode")
    ap.add_argument("--with-reference", action="store_true",
                    help="Add identity-lock wording for use with a reference image")
    a = ap.parse_args(argv)

    p = load_json(a.profile, "profile")
    validate_profile(p, a.profile)
    o = p.get("outfit") or {}
    if a.outfit:
        o = load_json(a.outfit, "outfit")

    if a.mode == "hero":
        if not a.scene.strip():
            sys.exit("--scene is required for hero mode")
        print(hero_prompt(p, o, a.scene))
    else:
        print(turnaround_prompt(p, o, a.with_reference))


if __name__ == "__main__":
    main()
