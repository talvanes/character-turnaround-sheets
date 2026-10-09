---
name: character-turnaround-sheets
description: Design an original illustrated character and keep it visually consistent across images. Generates a hero illustration from a text description, a 16:9 turnaround/model sheet on white (front, 3/4, side, back full-body views plus 2x2 face views), and outfit-swap variants of that sheet using the previous image as reference. Use when the user asks for character sheets, turnarounds, model sheets, reference sheets, multi-view character images, or "the same character wearing X".
---

# Character Turnaround Sheets

Workflow: **profile → hero image → turnaround sheet → outfit swaps**. Each stage reuses one character profile so identity stays locked while only the outfit changes.

Image generation runs through `manus-tools` → `generate_image` (`model: "default"`, `transparent_background: ""`, English prompts). Generation runs as a background job: end the turn with `job wait`, then view the result once before delivering.

## 1. Build the character profile

Copy `templates/character_profile.json` to the working directory (e.g. `/home/ubuntu/output/<character>/profile.json`) and fill it from the user's description: art style, body, heritage, skin, eyes, face, hair, outfit (garments, footwear, accessories). Keep the user's exact descriptors. Update the profile whenever the user changes a persistent trait (e.g. hair), so later sheets inherit it.

## 2. Hero illustration (when the user starts from a description)

```bash
python3 /home/ubuntu/skills/character-turnaround-sheets/scripts/build_prompt.py profile.json --mode hero --scene "POSE, SETTING, PROPS, MOOD"
```

Use the user's aspect ratio (default 9:16 for a single figure). Save as `hero.png`.

## 3. Turnaround sheet

```bash
python3 /home/ubuntu/skills/character-turnaround-sheets/scripts/build_prompt.py profile.json --mode turnaround --with-reference
```

Call `generate_image` with `aspect_ratio: "16:9"` and `references: [<latest image of the character>]` (the hero image, or the user's uploaded sheet). Layout: four full-body views (front, 3/4, side, back) in the left ~70%, a 2x2 grid of face views on the right.

## 4. Outfit swaps

Write the new outfit as JSON (same schema as `profile.outfit`) and build:

```bash
python3 /home/ubuntu/skills/character-turnaround-sheets/scripts/build_prompt.py profile.json --mode turnaround --outfit outfit_<name>.json --with-reference
```

Reference the most recent sheet the user attached (identity lock) and name the output `turnaround_sheet_<outfit>.png`. An empty `accessories` list makes the prompt forbid all accessories, which stops items in the reference from carrying over. For outfit-writing patterns and brand-style requests, read `references/lessons.md`.

## 5. Check and deliver

View the result once and confirm only:
- All 8 views are present, full bodies are uncropped, and the outfit is consistent across views.
- Requested garments, colors, footwear, and accessories appear; removed items are gone; side-specific items (e.g. a watch) are on the correct side.
- Skin tone matches the profile.

If a critical item fails, regenerate once with a focused fix. Otherwise deliver: link the file, summarize the outfit as rendered, and state any assumptions (interpretation of ambiguous wording, dropped items, invented details) and known deviations (e.g. skin-tone drift) with an offer to adjust. Do not generate extra variants unprompted.

## Resources

- `scripts/build_prompt.py` — builds hero and turnaround prompts from the profile and an optional outfit JSON.
- `templates/character_profile.json` — profile schema with a filled example.
- `references/lessons.md` — failure modes and fixes, outfit-writing examples, rules for ambiguous requests.
