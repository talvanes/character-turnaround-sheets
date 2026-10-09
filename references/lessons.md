# Lessons and Outfit-Writing Guide

Read when writing a new outfit, interpreting an ambiguous request, or fixing a failed generation.

## Known failure modes and fixes

| Problem observed | Cause | Fix |
| --- | --- | --- |
| Skin rendered warm/tan instead of requested pale tone | Golden-hour or warm scene lighting tints the whole figure; reference images propagate the drift | State the base skin tone explicitly in every prompt; use neutral studio lighting for sheets; add "light tints shadows, not base skin tone". If it still drifts, disclose it and offer a regeneration |
| Previous accessories (kerchief, necklace) reappear in an outfit swap | The reference image carries them over | List accessories exhaustively; when none, write "NO accessories of any kind" and add the old items to Avoid (the script does this) |
| Style drifts toward semi-realistic anime | "Disney-style" alone is weak | Keep the full `art_style` string from the profile in every prompt |
| Watch/bag on the wrong side between views | Model mirrors views | Name the body side ("her LEFT wrist") and require it in every view; verify in front view (appears on viewer's right) and back view (viewer's left) |
| Real brand names requested ("Calvin Klein-style", "Adidas-style") | Logos/trademarks render poorly and should not be reproduced | Describe the design language (wide elastic logo band, three side stripes, white midsole) and add "no readable brand text" |

## Writing an outfit

Describe each garment with: type, color (with nuance, e.g. "dark charcoal, not pure black"), material/finish, cut and key construction details, how it layers with other pieces. Always specify footwear (or "barefoot") and accessories.

Examples from use:
- Qipao: "form-fitting sleeveless qipao in solid blueish-green teal silk satin, faint tone-on-tone floral brocade, high mandarin collar, frog-knot buttons along a diagonal closure, mid-calf length, side slits"; footwear "matching teal satin low-heel pumps".
- Athleisure: "dark charcoal sports bralette with wide light-grey elastic underband (blank)", "matching high-waisted leggings", "bright orange muscle tank with deep armholes showing the bra, knotted at one hip"; footwear "dark performance runners with light three-stripe-like accents, white midsole"; accessories ["black smartwatch on her LEFT wrist"].
- Beachwear: "light-blue triangle string bikini top", "light-wash frayed denim micro shorts; bikini bottom side strings pulled high on the hips, visible above the waistband"; accessories ["thin silver chain necklace with small cross pendant"].

## Interpreting ambiguous requests

- "Triptych" with 4 body + 4 face views: produce a standard turnaround sheet; mention that it is not literally three panels.
- Unclear garment phrasing (e.g. "bikini top strips show up to the sides above the shorts"): choose the most plausible fashion reading, proceed, and state the interpretation in the reply.
- Items not mentioned (shirt held in the hero image, previous accessories): drop them in turnaround sheets and say so.
- When hair changes are requested, update `hair` in the profile so later sheets inherit it.
