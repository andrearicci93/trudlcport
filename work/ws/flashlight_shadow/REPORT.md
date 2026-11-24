# Flashlight shadows on PC (TruFlashShadow)

The Xbox 360 version shadows the world from Lara's flashlight. The PC version never did (PCGamingWiki lists it as a
missing 360 feature; no earlier PC fix was found, 2026-11-22). This work makes the PC flashlight cast real-time shadows
with a small ASI plugin. **No game file is changed**; removing the `.asi` restores the stock game.

Status:
- **Tested in game** on the **GOG** `tru.exe` (md5 `76b4da2f…`, the B138-style exe built from it), owner-played across
  several base-game levels and DLC 1 (Beneath the Ashes): "everything works".
- **Steam: not tested.** The GOG exe is the same retail v1.1 image as the Steamless-unpacked Steam exe at every
  checked site (see the GOG research PR); the plugin checks every byte it patches and patches nothing on a mismatch,
  so on Steam it either works or stays off. To be confirmed by a Steam tester.
- Independent of the DLC port: it works on the base game with or without the DLC kit.

## The result in one paragraph

The PC game already contains everything the Xbox flashlight shadow needs: the flashlight's shadow-casting spot light
(in `g_personal_light`, DTP 3404, the same data as the Xbox), the spot shadow-map renderer and the material shaders
that sample it. Four run-time gates in the PC code stop it. The plugin opens all four in memory, for the flashlight
only.

## The four gates (PC `tru.exe` addresses)

| # | Gate | Effect | Fix |
|---|---|---|---|
| 1 | Right after the flashlight's chest spot light is created, its cast bit (PCRenderLight `+0xc5` bit 2) is cleared | light never counts as a shadow caster | set the bit again every frame before the shadow pass (hook of the `call RenderShadowMaps 0x5050c0` at `0x509756`) |
| 2 | Each draw passes two lists: all lights and shadow lights (device SetLights `0x5076a0` -> scene `0x505530`); the flashlight is never in the shadow list | its light instance is never registered for the shadow pass (`+0x65` stays 0) | hook the call at `0x5076c2`; pass a copy of the shadow list with the flashlight added (ini `AddToShadowList`, `AddToAllShadowLists` for draws whose light list lacks it) |
| 3 | Static batches (`0x50f7c0`) register as casters (`0x504ee0`) only when their data flag has bit 2 | unflagged level geometry never casts | the three `je` at `0x50fc32 / 0x50fd10 / 0x50fe2f` are removed; a stub at `0x504ee0` sends flagged batches the stock way and unflagged ones to the flashlight only (ini `StaticAllCast`) |
| 4 | Level terrain (`PCRenderTerrain`, vtable slot `0x8499c8` -> draw `0x5128b0`) casts per part through a 128-bit caster mask (part record `+0x18..+0x24`, 0x28-byte records) that never contains the flashlight | poles, beams, steps, platforms never cast | replace the vtable entry with a stub that finds (or appends) the flashlight in the draw's light array and sets its bit in every part mask (ini `TerrainCast`) |

Flashlight identification: a fingerprint of the first 0x40 bytes of its light record (DTP 3407 at `res+0x42c`); the
pointer is checked against the scene light array (`[0xa1407c] + 0xfdfc`, count `+0x14`, array `+0x1c`) before every
use. Every patch site is byte-checked first and refused on mismatch; each part has an ini switch.

The plugin goes beyond the Xbox on purpose: Lara and her guns cast too (the Xbox excludes them), and all terrain casts.

## How it was found (short)

1. TruMenu `light.list` with the flashlight off / on: one new **point** light; forcing its shadow switch changed
   nothing. The flashlight object `g_personal_light` holds two light records: 3407 = **spot with shadow**, 3408 =
   point. PC and Xbox data are identical; the 5-entry light table puts the spot in entry 3.
2. Overlay experiments on the data produced the first PC flashlight shadows but from the wrong place (entry 5 is the
   bounce light at the beam end); stock data is right, so the blocker is code.
3. A read-only memory monitor (`tools/light_monitor.py`) showed the cast bit is cleared after creation -> gate 1.
   `light.frame` captures showed the light never marked visible -> traced to the SetLights shadow list -> gate 2.
   With these, models cast (Lara, guns, gate bars, vases, medipacks).
4. Ghidra (headless) decompiled the caster paths; plugin diagnostics counted registrations. Side-by-side Xbox clips
   (Xenia) showed what the Xbox shadows. Gate 3 opened static batches; the pole still did not cast; reading the object
   list proved the pole is not an object; RTTI showed the per-part-mask draw `0x5128b0` belongs to `PCRenderTerrain`
   -> gate 4. With 0.5 everything the Xbox shadows casts on PC.

## Known issues (open)

- **Zone switch (Xbox too):** the game turns flashlight shadows off when Lara crosses into some lighting zones; the
  scene brightens slightly with a smooth blend. Confirmed on Xbox (Xenia) at the start of Croft Manor (move forward:
  ledge shadows; one step further: gone) and with the motorcycle in a Mexico tunnel (shadow on one side, not the
  other, same brightness). This is why the Xbox (and PC) never shadow the pillar-room pillars or the sea levels. Next
  step: find the zone / light-group blend code and keep the flashlight's shadow on across zones (a fifth gate).
- **Light cut off by a hard horizontal line** above and below in two Mexico areas (Land of the Dead and the "days"
  area), with a smooth transition at a boundary: possibly the same zone blend.
  An almost complete pass through Mexico showed it in these two areas only.
- **Faint flicker of the flashlight's glow** (the lit area itself, not the shadows): a slight, fast brightness
  flicker that is barely noticeable, if at all. It is the same with the frame rate capped at 72 fps as uncapped, so it
  is not frame-rate related. The shadows themselves do not flicker.
- Some tests ran uncapped at 200+ fps; the cut-off still needs a re-check at a 60 fps cap before calling it a shadow
  bug (the engine has frame-rate-dependent behaviour above 60).
- Diagnostics are on in the tested ini (`Diagnostics=1`, `LogLevel=1`: a log line every 120 frames). A release build
  should default them off.
- Also seen working in an ultrawide test build (a separate aspect-ratio plugin loaded at the same time): no conflict
  noticed.

## Planned (not in this PR)

- **Fifth gate:** keep the flashlight shadow on in every lighting zone, so the pillar-room pillars and the sea levels
  get shadows too (beyond the Xbox).
- **Menu / launcher option** to turn the flashlight shadows on and off, next to the game's own shadow settings.
- **Motorcycle headlight shadows:** the headlight's spot record has shadow byte 0 on PC and on Xbox; the same four
  gates could be reused (beyond the Xbox).
- Regression pass (combat, cutscenes, DLC 2, saves) and release defaults before the PR leaves draft.

## Files

- `src/TruFlashShadow.cpp`, `src/TruFlashShadow.ini`, `src/build.bat` (MSVC Build Tools, x86, `/MT`).
- `tools/light_monitor.py`: read-only monitor of the scene lights in a running `tru.exe`.

Install: put `TruFlashShadow.asi` + `.ini` next to `tru.exe` (loaded by the ASI loader that the DLC kit already uses).
It writes `TruFlashShadow.log` next to the game.

## Contributors

Investigation and code by the GOG tester and Claude Code (Anthropic), November 2026.
