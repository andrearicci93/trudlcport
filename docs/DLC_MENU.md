# DLC mission screen on PC: title over the description

Symptom (B138, PC Steam): in *Downloadable content* -> mission screen the level title is drawn on top of the
description text, in every language, and the title is grey instead of light blue. Fixed on branch `windows`
(2026-10-27, checked in game in all six languages EN/FR/DE/IT/ES/NL at 1920x1080).

## Reference

Xbox 360 game + title update 0.0.2.3 + DLC in Xenia Canary 02d2cb5 (16:9, 1280x720): title light blue, centred above
the description column; description starts below it (an independent screenshot of the same screen, posted on Tomb
Raider Forums in 2020 from another Xenia build, shows the same layout - see `docs/RELATED_WORK.md`):

<a href="https://i.imgur.com/od0lwMJ.png"><img src="https://i.imgur.com/od0lwMJ.png" width="480" alt="Xbox DLC mission screen in Xenia (forum member's screenshot, 2020)"></a>

Measured as fractions of the screen:

| Element | Xbox TU | PC B138 |
|---|---|---|
| preview image left/right | 19 % / 49 % | 19 % / 49 % |
| title centre x / y | 72 % / 17 % | 72 % / 20 % |
| description top | 21 % | 15 % (grows upwards into the title) |
| title colour | light blue | grey |

## Where the screen lives

`generalbank.drm`, Script section **Xbox id 134 / PC id 104** (the script that loads `dlc_level1..6_preview`;
section ids differ between platforms - Xbox id 134 is an unrelated script on PC). Sizes: Xbox retail 20 068,
Xbox TU 20 900, PC 20 084 -> the PC script is the retail version.

* Members: arrays at PC 0x168 / 0x1b0 / 0x1f8 (6 entries each, filled at run time) for title, description and
  preview widgets; the widgets themselves are members with init blocks (`uitext`, type symbol 301 on PC / 299 on
  Xbox; `uirenderimage` 306 / 304). The TU inserts one 12-byte member at 0x004, so Xbox TU offsets are PC + 0xc
  for all later members, plus one member at the end.
* Layout values are **not** in code: they are the member init blocks (widget objects). `uirenderimage` blocks hold
  normalised x/y/w/h (e.g. 0.2125, 0.35, 0.533, 0.3); `uitext` blocks hold colour (+0x4c), shadow offsets
  (+0x18/+0x24), a font texture id (+0x5c..), alignment-like words.

## The fix (`tools/dlc_screen_text_style.py` + `tools/dlc_text_unwrap.py`)

1. Init-block words of the DLC 1/2 widgets differ between Xbox TU and PC (everything else in these blocks is
   platform symbol/text ids or a PC-only flag at +0x64 that is set on every text widget):

   | PC member | field | Xbox TU | PC |
   |---|---|---|---|
   | 0x0cc, 0x0e4 (titles) | +0x4c colour | 0xff78afeb | 0xffc0c0c0 |
   | 0x0d8, 0x0f0 (descriptions) | +0x18, +0x24 (shadow) | 7.5 | 8.0 |
   | | +0x34 | 12.0 | 1.0 |
   | | +0x6c (bool) | 1 | 0 |
   | | +0x74 | 0 | 8 (most likely vertical alignment: centred vs top) |

   `dlc_screen_text_style.py` writes the Xbox values in place (same size, old values asserted). Colours and bools
   are plain u32 values on both platforms (a BE byte-bool 0x01000000 is 0x00000001 on PC).
2. With the Xbox style the description box wraps by itself. The DLC 1/2 descriptions (locals string index **456 /
   457**) contain hard line breaks every 47-52 characters in all languages; English fits, the longer lines of the
   other languages overflow and leave single words on a line. `dlc_text_unwrap.py` replaces those `\n` by spaces in
   all six `locals.bin_NNN` (same length, offsets unchanged). Language bits 001/002/004/008/016/032 = EN/FR/DE/IT/
   ES/NL = registry `Language` 0..5 (all verified in game).

## The panel behind the screen (`tools/dlc_screen_panel.py`, 2026-11-17)

Symptom (PC, every path: main menu and pause menu, base game and DLC 2): image, text and list are drawn straight
onto the scene; the Xbox title update draws a dark translucent box behind them (references
`references/DLC2/Xenia-20261114_DLC-Missionsmenue_ausPause_grauerKasten.png` vs
`PC-Test-20261114_DLC-Missionsmenue_ausPause_ohneKasten.png` / `PC-Test-20261116_DLC-Missionsmenue_ausBasisspiel_ohneKasten.png`).

Cause (data, `dlc_screen_panel.py scan` / `script_members_list.py xt 134`): the "member inserted at 0x004" above is
the panel. It is a `uibitmap` (Xbox script 89 = PC 89) named Symbol 1195 (PC 1292) with an init block and a
start-function-info entry; no code uses it, the engine constructs and draws it:

| init field | value | meaning |
|---|---|---|
| +0x18 / +0x1c / +0x20 | 1.0 / 0.25 / 25.0 | position x / y / z (UI units, centre origin, y down) |
| +0x34 / +0x38 | 28.0 / 14.0 | scale (width / height in UI units) |
| +0x4c / +0x54 | 0x94050505 | colour ARGB: alpha 0x94 (58 %), RGB 5 / 5 / 5 |
| +0x5c | 0 | no texture (plain quad) |

UI unit = 1/20 of the screen height (36 px at 720p): 28 x 14 units at (+1.0, +0.25) = 13.4-92.2 % x 16-86 % of
the screen, exactly the box measured in the Xenia picture (172-1180 x 117-620 of 1280 x 720). z: texts 0.5,
preview image and selection bar 22, panel 25. The Xbox disc script (Xbox 134 retail) and the PC script 104 have no
such member - the PC never had the panel.

Fix: `dlc_screen_panel.py build IN OUT` adds the member to PC script 104 of our generalbank: next free instance
offset (680, no other offset moves), entry first in the member list and start-function-info entry last (the title
update's order), init = the TU's 240 bytes as u32 values (the three other `uibitmap` inits of the screen are equal
TU / PC word for word), its 16 property path pointers on the PC screen's own shared path. Self-verify (only script
104 changes, every old word except the instance size and the two list pointers unchanged, the new init = the TU
words); the pipeline gates of step Generalbank pass. Pipeline: `Invoke-TruPipeline.ps1 -Step Generalbank -DlcPanel`
(opt-in until the live test). Not combined with `generalbank_pc_build.py --tailoring` (that rule checks the md5 of
script 104 before it). Draw order: kept as on the Xbox, the exe rule (member order, construction order or z) is not
traced - the live test decides (panel behind the texts, texts not dimmed).

## Dead end (kept for reference): `tools/dlc_screen_widescreen.py`

The TU also changed function 1 of the screen (26 -> 103 words): `if (uiscreen.f10() > 1.5)` it adjusts shadows of
four text widgets and scales two image widgets. Ported to PC (code + 2-entry locals appended to the section,
member offsets -0xc, call targets mapped by prototype order: uiscreen 100->103 f10 @0x1bc, uitext 98->102 @0x35c,
uirenderimage 92->96 @0x138/0xe4, uimenu 93->97 @0x368->0x3a0, messagechannel 70->74 @0x8c) it runs without
problems but makes the PC screen **differ** from the Xbox reference at 16:9 - the branch is evidently not taken
on the Xbox there, so `uiscreen.f10` is not simply the aspect ratio. Not used.

## Tools used for the analysis (not in the repository, ad hoc)

`menu_dlc_probe.py scripts|strings` (upstream) to list Script sections of all four generalbank variants; ad hoc
walkers on top of `script_conv.Walk` to list functions/strings/float literals, dump bytecode (op 0x02 pushes the
next word as a literal - not in `Walk.EXTRA`), list method calls with arguments, and diff member init blocks.
