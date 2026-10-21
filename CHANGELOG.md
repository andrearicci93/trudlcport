# Changelog

"Played" = the project owner ran it in the game (Windows 11 VM). "Offline" = checked with static gates and data comparisons against the
Xbox/PC originals only, **not yet seen in game**.

## B138 — 21 Oct 2026 (kit `trudlcport-kit-B138.zip`)

Update of B132. Re-run `install_dlc.py` with the new kit: the previous `mods\` is kept as `mods_backup_<date>`. Start a **new DLC game** and remember to **lock the game to 60 fps**.

**Everything new in this release is offline-verified only: B138 has not been played yet** (B132 is the last build played end to end).

### What changed since B132
| Build | Change | Why |
|---|---|---|
| B133 | 274 pixel shaders rewritten (26 DRM): `cmp` with a negated-absolute constant and `sincos` with destination = source, the only two forms the original PC game never uses. Each one is bit-equivalent in our shader VM | Windows' own Direct3D 9 rejected them, which is the probable cause of *"A problem has occured with your display driver"* on real GPUs |
| B134–B137 | Physics-joint bytes that the converter had turned into 32-bit integers: grapple puzzle of **pillory** (`bend_switches`: the whole mechanism moved when pulling a switch), **dragon_slider** in the dungeon (20 words: plates/unlocking), 4 **bat generators** in level1_start (bat count was 65535/768 instead of 3) | found by comparing every mechanism against 1415 base-game joint words (0 differences) |
| B138 | 39 `.mul` audio files re-encoded for the game's own decoder (it ignores nibble 0; the port had used the FSB convention): DLC music, radio/VO, intro and final cutscene audio | "crackly" DLC audio reported by testers (≈432 clicks/min, now ≈9 in the offline emulation) |

### Should be fixed by this build — please report in game
- [ ] **No more "display driver" box on real GPUs without dgVoodoo2/DXVK** (B133). If it still appears, run the native test and send `native_report.txt` ([TROUBLESHOOTING](docs/TROUBLESHOOTING.md)).
- [ ] **DLC music, voices and cutscene audio no longer crackle** (B138).
- [ ] **Pillory:** pulling the two grapple switches lowers the mechanism instead of moving the whole thing (B134–B137).
- [ ] **Dungeon:** dragon slider plates go up/down and unlock the way (B134–B137).
- [ ] **First area (level1_start):** the bats appear in the right number and the frame rate stays fine.

### Still open / may still be wrong
| Issue | Notes |
|---|---|
| Rare crash right at game start | FMOD audio initialisation fails and the game ignores the error; just start it again |
| Golden shotgun (unlocked after all treasures) | needs title-update scripts/tables the PC exe lacks; untested, may crash when equipped |
| Dungeon material 23211 | small visual defect (texture layout), needs a shader transplant |
| Blue reflection on Lara at the four thrall portals (balcony) | probably faithful to Xbox, unconfirmed |
| Thrall in the dungeon reveal cutscenes | no data difference found; unconfirmed in game after the AI/navmesh fix |
| Torch looks like a cone, fog/attenuation differences | torch data identical to Xbox; not understood |
| Arched window (materials 22588/22589) | never confirmed |
| Watervolume field `+0x10` | unknown namespace; water works since B105 |
| ~200 data words of mechanical objects, 224 DTP words | no offline rule; would show as odd behaviour of a mechanism |
| DLC2 *Lara's Shadow* | not converted |

Details per area: [docs/STATUS.md](docs/STATUS.md).

### In breve (italiano)
Aggiornamento di B132, solo verificato offline (non provato in gioco): shader corretti per il D3D9 nativo (errore "display driver"),
giunti dei meccanismi di pillory e dungeon, numero di pipistrelli, audio senza gracchiare. Rilancia `install_dlc.py` col nuovo kit
(la vecchia `mods\` resta come copia), inizia una **nuova partita** DLC e **blocca il gioco a 60 fps**. Elenco di cosa dovrebbe essere
risolto e di cosa resta aperto qui sopra.

## B132 — 19 Oct 2026

First public release: **Beneath the Ashes playable from start to end credits** on the Steam PC game, with a one-command installer that
rebuilds the build byte for byte from the player's own files. Fixed since B90: enemies frozen (navmesh), crash when collecting DLC
treasures, cobwebs, black ceiling in pillory, black water textures, pause-menu QUIT, end-credits hang, many data fixes.
