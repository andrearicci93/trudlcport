# Status — reference build B132 (19 Oct 2026)

"Confirmed" = the project owner played it (Windows 11 VM). "Offline" = static checks only, not yet seen in game.

DLC1 *Beneath the Ashes* is **playable from the start to the end credits** on the native PC game. DLC2 *Lara's Shadow* is not converted.
Install it with [INSTALL.md](INSTALL.md).

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
| Occasional crash right at game start (FMOD audio init fails and the game ignores the error) | start the game again |
| Golden shotgun (unlocked after all treasures) depends on title-update scripts/tables the PC exe lacks | may not work or crash when equipped; untested |
| Material 23211 (dungeon) texture layout | small visual defect |
| Blue reflection on Lara at the four thrall portals (balcony) | probably faithful to Xbox |
| ~200 data words of mechanical objects with no offline rule | would show as odd behaviour of a mechanism; report it |

## How B132 was checked
Static gates on every build (id references, shader identity, texture lifetime, material counters, light bridge, 21 data rules at fixed
point, uid checks) and a per-area audit Xbox vs PC: same number of meshes/animations/collisions/scripts/DTPs in all 133 converted
files, all scripts parse, no silent audio, all 29 DLC1 treasures in the reward table.

## Lineage
`… B90_gold_L4 → B92–B105 (water volumes, instance data, triggers, texts, DTP words) → B106 (cell streaming) → B107 (audio channels) → B108/B116 (cobwebs) → B109 (save-slot name) → B117 (light colour bridge) → B119–B121 (thrall data) → B122 (navmesh) → B123/B124 (cobwebs, black water textures) → B125 (reward table) → B126 (pillar_of_doom) → B127 (sound info) → B129 (cobweb 20264) → B130 (QUIT) → B131/B132 (moss)`.
