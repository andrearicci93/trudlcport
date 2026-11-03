# Status — B270 (Nov 2026, release build B270_acqua)

"Confirmed" means the project owner played it (Windows 11 VM, dgVoodoo2). "Offline" means static checks only, not yet seen in game. Changes since B138: [../CHANGELOG.md](../CHANGELOG.md).

- **DLC1 *Beneath the Ashes*** was played from the start to the end credits on B132. The tables further down describe that build.
  - Later builds carry back to DLC1 the data fixes found for DLC2: costumes, materials, scripts. All of them pass the DLC1 gates offline.
  - A full replay of DLC1 on B270 is still to do.
  - B270 fixes the black water of the DLC1 dungeons offline (material 20262: VS 976 → 164, COLOR0 now written). It is not yet seen in game.
- **DLC2 *Lara's Shadow*** is converted and played as the doppelganger. Install it with [INSTALL.md](INSTALL.md).

## DLC2: what works (confirmed in VM tests, Oct-Nov 2026)
| Area | Notes |
|---|---|
| Start, opening cutscene, doppelganger outfit | B140+ |
| Doppelganger look | colours near goo and while shooting fixed with the irradiance probes (B260); hair with time scaling fixed with the exe cloth patch |
| Combat | Q/E deal damage, Shift+E distortion and trail without black overlay, finisher on a downed thrall |
| Thralls, goo cannons, pools, torches, goo columns, bridges | working after the B251–B258 data audit |
| Ceremony-room cutscene | starts (B259) |
| Goo waterfalls | correct with the ceremony-room goo FX switched off (B265) |
| Flying with F2 (debug) between the wings | no crash (SweepAndPrune 3000 and camera-shake guard in the exe) |

## DLC2: fixed offline, not yet seen in game
- Final sequence 045 → 050 → credits (B266, needs `credits_DLC2.bik`).
- Script vtable slots 14 and 31 (B267–B268).
- Black extending bridges and goo pipes in the machine room (B269).
- Native-D3D9 shader forms (B269).
- Treasure-room material 26584: VS 831 → 243, which now passes the vertex colour (B270).

## DLC2: known open issues
| Issue | Notes |
|---|---|
| Flicker in the Natla cutscene | block-shaped patches on Natla, the doppelganger and the throne. Cause not found |
| Wall-run on rock veins | does not grab in some places (`NONE` in the F8 menu in front of the doppelganger) |
| Ceremony-room goo FX | switched off: they drew wrong shapes |
| Machine-room terrain, material 26622 | black. The fix needs the Xbox vertex shader (UV scale) as well |
| Material 25165 (goo grinder / converter) | black surrogate shader |
| Glow pass without alpha clip in some goo libraries | translator bug found in B269. Libraries to regenerate |

# DLC1 details (B132, last full play-through)

## What works (confirmed)
| Area | Notes |
|---|---|
| Start, DLC menu entry, new DLC game, opening cutscene | |
| caverns → caverns_hall → water_wheel → watertunnel → dungeon → halls A/B → pillory → treasureroom | all reached and played |
| Enemies: thralls, spiders, tarantulas, bats | move and attack (the NavPower navmesh had been byte-swapped by the converter) |
| Treasures | collecting DLC treasures no longer crashes: the PC reward table was the pre-title-update one (206 entries, DLC ids 0xCE–0xEA beyond its end); now extended exactly as the Xbox title update |
| Cobwebs in caverns_hall | rendered with the cut-out web shader |
| Black patches on the pillory ceiling | a terrain moss layer had a MaterialParams component at 0 (`c110.y`); fixed |
| Pause menu → QUIT | quits again (it used to open the DLC sub-menu) |
| Final cutscene → credits → main menu | needs `movies\credits_DLC1.bik` (written by the installer) |

## Fixed offline, not yet seen in game
pillar_of_doom data reference (dungeon) · global sound-info table from the Xbox title update · cobweb material 20264 in caverns_hall/dungeon/halls/treasureroom · moss layer of material 20268 (water_wheel).

## Known open issues
| Issue | Impact |
|---|---|
| Guillotine `dlc1_uo_guillotine` (B270) | pixel shaders 738/739 discard on `v0.w`, which vertex shader 211 never writes. Not fixed |
| Black water in the dungeons with newer drivers | fixed offline in B270 (VS 976 → 164); to confirm in game |
| Occasional crash right at game start (FMOD audio init fails and the game ignores the error) | start the game again |
| "A problem has occurred with your display driver" on a real GPU (reported 20 Oct 2026) | cause: 2 shader forms rejected by Windows' D3D9 on AMD; fixed in B133, came back in B147–B268, fixed again in B269 (offline). See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Physics and camera tied to the frame rate (base game) | lock the game to 60 fps |
| Golden shotgun (unlocked after all treasures) depends on title-update scripts/tables the PC exe lacks | may not work or crash when equipped; untested |
| Material 23211 (dungeon) texture layout | small visual defect |
| Blue reflection on Lara at the four thrall portals (balcony) | probably faithful to Xbox |
| ~200 data words of mechanical objects with no offline rule | would show as odd behaviour of a mechanism; report it |

## How B132 was checked
Static gates on every build (id references, shader identity, texture lifetime, material counters, light bridge, 21 data rules at fixed
point, uid checks) and a per-area audit Xbox vs PC: same number of meshes/animations/collisions/scripts/DTPs in all 133 converted
files, all scripts parse, no silent audio, all 29 DLC1 treasures in the reward table.

## Lineage
`… B90_gold_L4 → B92–B105 (water volumes, instance data, triggers, texts, DTP words) → B106 (cell streaming) → B107 (audio channels) → B108/B116 (cobwebs) → B109 (save-slot name) → B117 (light colour bridge) → B119–B121 (thrall data) → B122 (navmesh) → B123/B124 (cobwebs, black water textures) → B125 (reward table) → B126 (pillar_of_doom) → B127 (sound info) → B129 (cobweb 20264) → B130 (QUIT) → B131/B132 (moss) → B133 (native D3D9 shaders) → B134–B137 (joints, bat generators) → B138 (audio .mul) → B139–B141 (DLC2) → B147–B158 (materials) → B159–B213 (doppelganger/thrall data) → B215–B247 (crashes, look, combat) → B251–B258 (audits) → B259–B268 (cutscenes, light probes, goo, ending, vtables) → B269 (machine room) → B269_nativo (native-D3D9 shaders, release)`.
