# Changelog

"Played" means the project owner ran it in game (Windows 11 VM). "Offline" means it was checked only with static gates and data comparisons against the Xbox/PC originals and has **not yet been seen in game**.

## B269 — Nov 2026 (kit `trudlcport-kit-B269.zip`, kit format 2)

**Lara's Shadow (DLC2) is now converted and can be played.** This release also needs a new install procedure:

- **Installer and kit, format 2.**
  - The installer needs `pack11.000` as well. Files shared by both DLCs are built for both. `--dlc1-only` exists but is untested.
  - The exe patch now starts from the **Steamless** output of your own `tru.exe` instead of the encrypted Steam exe, so the kit no longer carries the game's code.
  - Xbox textures are converted on your PC (`tex_convert.py`, needs `numpy`) instead of travelling inside the patches.
  - Each installed file is re-read from disk and checked. `--verify` and `--restore` use an install record.
- **End credits.** The credits movies are no longer in the kit. `--credits` builds `credits_DLC1.bik` and `credits_DLC2.bik` on your PC from your own `.wmv` files (Windows, ffmpeg + RAD Video Tools). Without them the game hangs on a black screen after each final cutscene.
- **Native Direct3D 9.** The 240 pixel shaders with forms that Windows' own D3D9 rejects on AMD are rewritten: 228 `cmp` with `-|c|`, 12 `sincos` with destination = source. This is offline only; please run the native test v3.
- **Lock the game to 60 fps**, as before.

### What changed since B138, in plain words
| Builds | Area | Change |
|---|---|---|
| B139–B141 | DLC2 start | 210 new files converted from `pack11`. The opening cutscene starts, the doppelganger outfit is forced, and the effect ids of the first fight are mapped to PC ids |
| B147–B158 | Materials (DLC2, back-ported to DLC1) | 98 lit materials rebuilt with new shader libraries, dedicated libraries for the materials with no PC donor, missing-texture placeholders, back-buffer flags, and the RGB light bridge in transplanted libraries |
| B159–B213 | Doppelganger and thrall data | Tens of thousands of data words that the generic converter had byte-swapped the wrong way: behaviour graph, tuning, action lists, block tables, id references. Each was decided against an independent PC oracle (the PC Lara class 850) and back-ported to the DLC1 costumes |
| B202, B216, B218 | DLC menu | Mission descriptions no longer overlap the title (wrapped as on Xbox) |
| B215–B236 | Doppelganger crashes and controls | Fixed crashes on spawn, actions, animation index and node lists. The black screen when jumping at a rock vein is gone (movement profile 26 was big-endian), and so is a vein marker with swapped bytes |
| B230–B231, B238–B245 | Doppelganger look | Green arms (normal map on the colour sampler), cube map, flat normals, trousers |
| B237, B246–B247 | Combat | Q/E punches and kicks deal damage. Fixed the crash on Shift+E (FX id). Distortion and trail of the shadow attack are restored without the black overlay |
| B251–B258 | Data audit | 24 + 71 more (type, index) words swapped at 32 bits. This fixes the crash after the Natla cutscene (`0x444c62`), on the cannonball, Natla pod and pistons, and on bridges, columns and pipes |
| B259 | Ceremony room | Its cutscene now starts (script message 103) |
| B260–B261 | Lighting | Irradiance probes of ceremony_room and dungeon fixed, so the doppelganger and thralls are no longer magenta near goo or while shooting. Goo cannon materials fixed |
| B264–B265 | Goo | Waterfall and goo materials fixed. The four ceremony-room goo FX are **switched off** (they drew wrong shapes) |
| B266–B268 | Ending, scripts | DLC2 final sequence (wrong script symbols that left the game paused on a black screen), 11 DLC1 scripts, yggdrasil_end camera spline, goo converter. Script vtable slots 14 and 31 match the PC layout |
| B269 | Machine room | The dark extending bridges and goo pipes (materials 22915/25901) get their translated Xbox shaders. On top of that comes the native-D3D9 shader fix above |

The **exe** chain also gained, step by step, these patches (all on the Steamless exe, offline-verified and then played):

- title-update code the PC exe lacked, needed by DLC2 (wall-run, attacks);
- crash guards;
- the cloth time step for the doppelganger's hair when time is scaled;
- a fix for the ChunkDoll geometry;
- a larger SweepAndPrune pool (3000, like the Xbox title update);
- a guard for NPC camera shakes.

### Should be fixed: please report in game
- [ ] No "display driver" box on a real GPU with Windows' own D3D9 (run the native test v3 if it still appears)
- [ ] DLC2 end: final cutscene → crush cutscene → credits → menu (needs `credits_DLC2.bik`)
- [ ] Machine room: extending bridges and goo pipes are no longer black
- [ ] DLC1 still fine from start to end credits on B269 (it received many back-ported fixes)

### Still open
| Issue | Notes |
|---|---|
| Flicker on Natla, the doppelganger and the throne in the Natla cutscene | block-shaped patches. Cause not found (duplicated instances and lights excluded) |
| Wall-run on rock veins in some places | on B269 one vein in front of the doppelganger reported `NONE` in the F8 menu. To be checked spot by spot |
| Ceremony-room goo FX switched off | they rendered wrong shapes. To be re-enabled once understood |
| Machine-room terrain material 26622 black | fix ready but needs the Xbox vertex shader too (UV scale) |
| Material 25165 (goo grinder / converter) black | surrogate shader with real parameters. Not fixed |
| Glow pass without alpha clip in some goo libraries | translator bug found in B269. The affected libraries need regenerating |
| Rare FMOD crash at start-up, golden shotgun, dungeon material 23211 | unchanged |

### In breve (italiano)
B269 aggiunge il DLC2 (*Lara's Shadow*): si gioca col doppelganger fino all'area finale; la finale e' corretta offline ma non ancora confermata. Servono anche `pack11.000` e l'exe sbustato con Steamless; i crediti `.bik` li crea l'installatore sul tuo PC con `--credits` (servono per finire i DLC). Blocca il gioco a 60 fps.

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
