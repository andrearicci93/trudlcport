# Setup: what you need and how to install

This repository ships **no game files**. Everything below is something you must own and supply yourself.

## 1. Files you need

### A. The PC game (required)
Tomb Raider: Underworld, Steam version, installed normally. The project was built and tested against exactly these files (see `docs/data/pc_game_files.tsv`; `scripts/check_inputs.py` verifies them):

| File | Size | MD5 |
|---|---|---|
| `tru.exe` (Steam, version 1.1) | 6 766 592 | `b36da327a320eab8b5c8464b27685840` |
| `bigfile.000` | 2 145 345 536 | `839e192dbfded17d5f788a99279efc70` |
| `bigfile.001` | 2 139 930 624 | `f4ceeb06c1accbcb4a4e1aa7e613895e` |
| `bigfile.002` | 2 146 330 624 | `1d5b5c46daf69b62dc93a68394952d15` |
| `bigfile.003` | 857 427 968 | `b700d3153784366540dbbc87cc7a8149` |
| `patch.000` | 20 924 416 | `942d7f5639757fa80a9c6750d86067f4` |

The localized game folder also contains `fmodex.dll`, `binkw32.dll` etc.; other language/version combinations were never tested.

### B. The Xbox 360 game and DLC files (required to *convert*; not needed if you already have a verified `mods/` tree)
These are read by the converters (hard-coded paths in `tools/convert_dlc.py`, `tools/pairs.py`, `tools/generic_cache.py`, …; edit them or use symlinks):

| Content | Files | Used for |
|---|---|---|
| Xbox 360 base game (disc layers) + title update | `layer1.000`, `layer2.000`, `TitleUpdate.000` (the tools expect a folder called `TombRaiderUnderworld_Patched/`) | Xbox↔PC pairing of ids/sections, learning the Xbox→PC conversion rules, shader/material oracle |
| DLC packs (Xbox 360 marketplace content for title `534307EC`, content type `00000002`) | `pack10.000` (*Beneath the Ashes*), `pack11.000` (*Lara's Shadow*), `pack1.000`, `pack2.000` | The DLC levels, objects, audio, cutscenes |
| Xbox 360 executable (optional, analysis only) | `default.xex` + title-update patch | Decompiling the Xbox engine for reference (`tools/xex_extract.py`, XenonRecomp tools) |

The tools assume the Xenia content-folder layout (`Content/534307EC/00000002/<contentID>/packNN.000`). Any other way of getting those files is fine as long as the bytes are the same.

### C. Third-party software (not included, not modified)
| Software | Role |
|---|---|
| [ModLoader](https://github.com/TombRaiderModding/ModLoader) (`ModLoader.asi` + the `binkw32.dll` proxy from its release) | Loads files from `<game>/mods/` instead of the bigfiles. **Required.** |
| [Steamless](https://github.com/atom0s/Steamless) | Removes the SteamStub wrapper from `tru.exe` so the exe can be patched. **Required for the exe patches.** |
| [dgVoodoo2](http://dege.fw.hu/) `D3D9.dll` | D3D9 wrapper used in the test VM (the author's tester reported that enabling v-sync / a 60 fps cap made the game behave better; this was never proven to matter for the physics objects). Recommended. |
| [TRLAU-Menu-Hook](https://github.com/TheIndra55/TRLAU-menu-hook) (`TR8-Menu-Hook.asi`) | Debug menu used by the automated VM runner (F8). Optional. |
| Python 3.10+ with `numpy`, `Pillow`, `capstone` | All tools |
| Windows (VM or native) | The game itself. The author tested in a Windows 11 VM driven by PowerShell scripts (`tools/vm_*.ps1`); the Python tooling also runs on macOS/Linux. |

## 2. Build the patched executable

The unmodified Steam exe is wrapped by SteamStub and cannot be patched directly.

1. Back up the original: copy `tru.exe` somewhere safe.
2. Run Steamless on `tru.exe`. The reference unpacked file has MD5 `56d1ce2dffa62f16354063da2df44d5a` (size 6 422 528). A different Steamless version may give a different but equivalent file; the patch tools refuse to patch bytes they do not recognise.
3. `scripts/build_exe.sh unpacked_tru.exe out/tru.exe` applies, in order:
   1. the LARGE_ADDRESS_AWARE flag (`scripts/make_laa.py`, expected MD5 after this step `bf5b16111a06b11b6ccd1dbe928f7d82`);
   2. `tools/fmod_init_guard.py` — fixes a latent crash at start-up when FMOD fails to initialise (uninitialised local in `FUN_00582200`, access violation at `0x7b92fb`);
   3. `tools/light_tex_guard.py` — guards a stale projected-light texture pointer (`X+0x418`, crash `0x5076fa`), keeps counters at VA `0x83DE20`;
   4. `tools/soundplex_guard.py` — skips SoundPlex nodes with a null data pointer (crash `0x592218` in `FUN_005920b0`), keeps counters at VA `0x83DF00` (magic `SPG1`).

   With the reference unpack the final exe must have MD5 **`f47814ff116a4a33842bdb846bf97982`** (verified: this chain reproduces it byte for byte). Each tool has `--check IN.exe` (original / patched / different) and a built-in self-test.
4. Replace the game's `tru.exe` with `out/tru.exe` (keep your backup).

## 3. Install the mods

1. Install ModLoader into the game folder (`ModLoader.asi`, `binkw32.dll`); create `<game>/mods/`.
2. Put the 279-file `mods/` tree there. The tree contains converted DLC levels (`dlc_*.drm`, `streamgroups/*.drm`), objects, cutscene streams (`cinstream/`), converted music/ambience (`music/`, `audio/`), localisation (`local/`), UI images (`image/`), and a patched `generalbank.drm` (origin `menu_dlc_B`, built with `tools/menu_dlc_patch.py`) that exposes the DLC from the menu. The expected file list with sizes and MD5 is `docs/data/B90_gold_L4.manifest.tsv`.
3. `python3 scripts/verify_mods.py "<game>/mods"` must report `missing 0, different 0, extra 0`.
4. Start the game, choose the DLC from the menu, start a new game.

If you only have the converters and not the finished tree, see [PIPELINE.md](PIPELINE.md).

## 4. Recommended settings
* Keep the frame rate capped at 60 (dgVoodoo `FPSLimit`) and enable v-sync (user-reported to help; unproven whether it affects the raft/bridge/rings physics).
* Windows registry `HKCU\Software\Crystal Dynamics\Tomb Raider: Underworld`: the author's VM had `EnableDepthOfField=1`.
* Save games of an earlier build may confuse the DLC; use a fresh profile when testing a new build.
