# Install the DLC on your PC (players)

This turns your **Steam PC copy of Tomb Raider: Underworld** into the build the author plays (latest build **B270**), using **your own** Xbox 360 DLC files.

The installer works only from files you own and checks every one of them:

- it decompresses the DLC files and converts their Xbox textures on your PC;
- it applies binary patches, then recompresses the files;
- it checks every source, every intermediate result and every written file against `manifest.json`.

If it says "Installed" and "Final check ... OK", your files match the author's.

Time: about 15 minutes, plus 5-20 minutes per credits movie. Disk: about 4 GB free: the new `mods\` (2 GB), the backup of your previous one and the unzipped kit (0.9 GB). The credits need about 1.5 GB of temporary space. The `--check` run takes several minutes, because it converts the textures too.

> Italiano: istruzioni brevi in fondo alla pagina.

---

## 1. What you need

| # | What | Where it comes from | Check |
|---|---|---|---|
| 1 | **Tomb Raider: Underworld, Steam, PC** (exe v1.1) | Steam | `tru.exe` MD5 `b36da327a320eab8b5c8464b27685840` |
| 2 | [**Steamless**](https://github.com/atom0s/Steamless/releases) (tested: the March 2024 release, v3.1.0.x, default options) | GitHub | run it once on your `tru.exe`. It writes `tru.exe.unpacked.exe` (MD5 `56d1ce2dffa62f16354063da2df44d5a`) |
| 3 | **Beneath the Ashes**: `pack10.000` (+ `credits_DLC1.wmv`) | your Xbox 360 content folder `Content/<profile>/534307EC/00000002/9CA70CF0EDA43654D158C2E37470D301DFA850E753/` | checked by the installer |
| 4 | **Lara's Shadow**: `pack11.000` (+ `credits_DLC2.wmv`) | same, folder `600A12643FCDAC84003E6E0DBD0A1A8F7DAE9DD153/` | required. Use `--dlc1-only` (untested) if you do not have it |
| 5 | **ModLoader** (`ModLoader.asi` + its `binkw32.dll` proxy) | <https://github.com/TombRaiderModding/ModLoader/releases> | makes the game read the `mods` folder |
| 6 | **Python 3.9+** with `bsdiff4` and `numpy` | <https://www.python.org/>, then `python -m pip install bsdiff4 numpy` | `python --version` |
| 7 | *(credits, Windows only)* **ffmpeg** and **RAD Video Tools** | <https://www.gyan.dev/ffmpeg/builds/>, <https://www.radgametools.com/bnkdown.htm> | needed to finish each DLC (see step 4) |
| 8 | The **kit**: `trudlcport-kit-B270.zip`, `install_dlc.py`, `tex_convert.py`, `credits_convert.py` | this repository's **Releases** page | the kit's MD5 is in the release notes |

Other versions of the game (GOG, retail DVD, other exe) are **not supported**. The installer refuses them instead of producing a broken build.

## 2. Install ModLoader and unpack the exe

1. Copy the ModLoader files (`ModLoader.asi` and the `binkw32.dll` proxy) into the game folder, usually `C:\Program Files (x86)\Steam\steamapps\common\Tomb Raider Underworld`.
2. Run Steamless on `tru.exe` in that folder. Keep the `tru.exe.unpacked.exe` it writes. The installer builds the patched exe from it and leaves your Steam `tru.exe` as a backup.

## 3. Run the installer

1. Put `install_dlc.py`, `tex_convert.py`, `credits_convert.py` and the unzipped `kit` folder in one folder.
2. Close the game. Open PowerShell in that folder.
3. Do a dry run first. It only reads:
   ```
   python install_dlc.py --game "C:\Program Files (x86)\Steam\steamapps\common\Tomb Raider Underworld" --dlc "D:\xbox\Content" --kit .\kit --check
   ```
   `--dlc` can be any folder with `pack10.000`, `pack11.000` and the `.wmv` files somewhere below it.
4. If it prints **All inputs OK**, run the same command without `--check`. To build the credits movies in the same run, add:
   ```
   --credits --rad "C:\Tools\RADVideo\radvideo64.exe" --ffmpeg "C:\Tools\ffmpeg\bin\ffmpeg.exe"
   ```
   If the credits fail (RAD sometimes needs a second try), run the same command again with `--credits`. When this build is already installed and intact, only the credits are built and nothing else is touched (`--reinstall` forces a full install).

What the installer writes (nothing is deleted):

| In the game folder | Content | What it keeps |
|---|---|---|
| `mods\` | about 480 files: levels, objects, audio, menu and texts of both DLCs | your previous `mods\`, as `mods_backup_<date>` |
| `tru.exe` | patched exe (title-update code for DLC2, crash guards, large-address-aware) | the previous exe, as `tru.exe.before_trudlcport_<date>` (and `tru.exe.steam_original`) |
| `movies\credits_DLC1.bik`, `credits_DLC2.bik` | end credits, made on your PC (only with `--credits`) | — |
| `trudlcport_install.json` | install record: MD5 of every installed file and the backup names | — |

- `--no-exe` keeps your exe. DLC2 will not work properly without the patched one.
- If a file is reported as *content-identical but recompressed by a different zlib build*, that is fine. Its decompressed content matches the author's byte for byte.

### Updating from B132/B138

Your `tru.exe` is the one patched by the old build, and the Steam exe is in `tru.exe.steam_original`.

1. Run Steamless on `tru.exe.steam_original`. It writes `tru.exe.steam_original.unpacked.exe`, which the installer finds by itself.
2. Run the installer as above. Your old `mods\` is kept as `mods_backup_<date>`.

## 4. Play

Start the game from Steam: main menu → **Downloadable Content** → **Beneath the Ashes** or **Lara's Shadow** → **Play mission**.

- Start a **new** DLC game.
- **Lock the game to 60 fps** ([TROUBLESHOOTING.md](TROUBLESHOOTING.md)).
- The end credits movie is **required to finish** each DLC. Without it the game stays on a black screen after the final cutscene.

## 5. Check, update, uninstall

| Goal | Command |
|---|---|
| Check that nothing changed since the install | `python install_dlc.py --game "<game folder>" --verify` |
| Update to a newer build | run the installer again with the new kit. The current `mods\` is kept as a backup |
| Uninstall / go back | `python install_dlc.py --game "<game folder>" --restore`. It puts back the previous `mods\` and `tru.exe`, and renames the credits movies with a date suffix |

## 6. If something goes wrong

| Message / symptom | Meaning / fix |
|---|---|
| `tru.exe: need the Steamless-unpacked v1.1 exe` | run Steamless on the Steam `tru.exe`, or pass `--exe-source <file>` |
| `source ... has a different MD5` | your DLC or game file is a different version or is damaged |
| `converted source differs from the kit` | your `numpy`/Python converts the textures differently. Please report it with your Python and numpy versions |
| `pack11.000 ... not found` | point `--dlc` at the folder that contains it, or use `--dlc1-only` (untested) |
| Black screen after a final cutscene | credits movie missing: `--credits` |
| Game crashes immediately at start, sometimes | known FMOD (audio) start-up failure. Start it again |
| The DLC entry is missing from the menu | ModLoader is not installed |
| "A problem has occurred with your display driver" | see [TROUBLESHOOTING.md](TROUBLESHOOTING.md): native test v3, DXVK |

## Using a coding agent

Open this repository in your agent (Claude Code, Codex, …) and say:

> Install the Tomb Raider: Underworld DLC port for me. Follow `docs/INSTALL.md`. My game is in `<folder>` and my Xbox DLC files are somewhere under `<folder>`. Download the latest release kit, run the installer with `--check` first, show me the result, and only then install. Do not delete anything.

---

## Istruzioni in italiano (breve)

1. **Cosa serve:**
   - TRU **Steam PC** (exe v1.1) e **Steamless**: va lanciato una volta su `tru.exe` e crea `tru.exe.unpacked.exe`;
   - i file Xbox 360 `pack10.000` e `pack11.000`, e per i crediti `credits_DLC1.wmv` e `credits_DLC2.wmv`;
   - **ModLoader**;
   - **Python 3.9+** con `pip install bsdiff4 numpy`;
   - per i crediti, solo su Windows: ffmpeg e RAD Video Tools.
2. Dalla pagina *Releases* scarica `install_dlc.py`, `tex_convert.py`, `credits_convert.py` e `trudlcport-kit-B270.zip`, e scompatta il kit nella cartella `kit`.
3. A gioco chiuso fai la prova a secco: `python install_dlc.py --game "<cartella gioco>" --dlc "<cartella file Xbox>" --kit .\kit --check`.
4. Se risponde *All inputs OK*, ripeti il comando senza `--check`. Per creare anche i crediti aggiungi `--credits --rad "<radvideo64.exe>" --ffmpeg "<ffmpeg.exe>"`: sono necessari per finire i DLC.
5. Avvia una **nuova partita** DLC e **blocca il gioco a 60 fps**.
6. Per controllare l'installazione usa `--verify`, per tornare indietro `--restore`.
