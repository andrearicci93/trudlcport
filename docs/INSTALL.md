# Install the DLC on your PC (players)

This turns your **Steam PC copy of Tomb Raider: Underworld** into the same build the author plays (latest build **B138**),
using **your own** Xbox 360 DLC files. The installer applies binary patches to files you own and checks every result against an
MD5 list, so if it says "Installed" your files are byte-identical to the author's.

Time: ~10 minutes. Disk: ~1.5 GB free in the game folder.

> Italiano: istruzioni brevi in fondo alla pagina.

---

## 1. What you need

| # | What | Where it comes from | Check |
|---|---|---|---|
| 1 | **Tomb Raider: Underworld, Steam, PC** (exe v1.1) | Steam | `tru.exe` MD5 `b36da327a320eab8b5c8464b27685840` |
| 2 | **Beneath the Ashes** Xbox 360 DLC files: `pack10.000` and `credits_DLC1.wmv` | your Xbox 360 content folder `Content/<profile>/534307EC/00000002/9CA70CF0EDA43654D158C2E37470D301DFA850E753/` (e.g. copied from your console's storage, or from a Xenia content folder) | the installer checks every file it reads |
| 3 | *(optional)* **Lara's Shadow** `pack11.000` (folder `600A12643FCDAC84003E6E0DBD0A1A8F7DAE9DD153`) | same | only adds the DLC2 menu images/music; DLC2 is **not** playable yet |
| 4 | **ModLoader** for TR Underworld (`ModLoader.asi` + its `binkw32.dll` proxy) | https://github.com/TombRaiderModding/ModLoader/releases | makes the game read the `mods` folder |
| 5 | **Python 3.9+** and the `bsdiff4` module | https://www.python.org/ → then `python -m pip install bsdiff4` | `python --version` |
| 6 | The **kit**: `trudlcport-kit-B138.zip` (patches + `manifest.json`, 1.15 GB) and `install_dlc.py` | this repository's **Releases** page | zip MD5 `9fb60fa291df6e299a8ea5cc2d44352d` |

Other language/version combinations of the game (GOG, retail DVD, non-Steam exe) are **not supported**: the installer will refuse
them instead of producing a broken build.

## 2. Install ModLoader

1. Download the ModLoader release for *Tomb Raider: Underworld*.
2. Copy its files (`ModLoader.asi` and the `binkw32.dll` proxy, as its README says) into the game folder, usually
   `C:\Program Files (x86)\Steam\steamapps\common\Tomb Raider Underworld`.

## 3. Run the installer

1. Download `install_dlc.py` and `trudlcport-kit-B138.zip` from Releases. Unzip the kit into a folder named `kit` next to `install_dlc.py`.
2. Close the game. Open a terminal (Windows: *PowerShell*) in that folder.
3. First a dry run that only checks your files:
   ```
   python install_dlc.py --game "C:\Program Files (x86)\Steam\steamapps\common\Tomb Raider Underworld" --dlc "D:\xbox\Content" --kit .\kit --check
   ```
   `--dlc` can be any folder that contains `pack10.000` (and optionally `pack11.000`) and `credits_DLC1.wmv` somewhere below it.
4. If it prints **All inputs OK**, run the same command **without** `--check`.

What the installer writes (nothing is deleted):

| In the game folder | Content | Backup it keeps |
|---|---|---|
| `mods\` | 276 converted files (DLC levels, objects, audio, menu, texts) | your previous `mods\` → `mods_backup_<date>` |
| `tru.exe` | patched exe (crash guards, large-address-aware) | original → `tru.exe.steam_original` |
| `movies\credits_DLC1.bik` | DLC end credits (the game waits for this file after the final cutscene) | — |

Use `--no-exe` if you want to keep your exe (the game will be less stable).

## 4. Play

Start the game from Steam → main menu → **Downloadable Content** → **Beneath the Ashes** → **Play mission**. Start a **new** DLC game
(saves made with older builds of this port may contain broken treasure counters). **Lock the game to 60 fps**: physics and
camera are tied to the frame rate ([TROUBLESHOOTING.md](TROUBLESHOOTING.md)).

## 5. Uninstall

Delete `mods\` (or rename it), rename `tru.exe.steam_original` back to `tru.exe`, delete `movies\credits_DLC1.bik`. Steam's
"Verify integrity of game files" also restores the exe.

## 6. If something goes wrong

| Message / symptom | Meaning / fix |
|---|---|
| `expected the Steam v1.1 exe` | your `tru.exe` is not the Steam v1.1 one (or already modified). Verify the game in Steam and retry. |
| `source ... has a different MD5` | your DLC/game file is a different version or damaged. |
| `pack10.000 ... not found` | point `--dlc` at the folder that contains it. |
| Game crashes immediately at start, sometimes | known FMOD (audio) start-up failure on some systems; start it again. |
| The DLC entry is missing from the menu | ModLoader is not installed (the `mods` folder is not being read). |
| "A problem has occured with your display driver" | probable cause fixed in B133 (update to B138); if it persists: workaround and native test in [TROUBLESHOOTING.md](TROUBLESHOOTING.md). |
| Boxes, ragdolls or puzzles behave strangely | lock the game to 60 fps, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md). |

Updating from B132: just run the installer again with the B138 kit (the old `mods\` is kept as `mods_backup_<date>`). Changes and known open issues of B138: [CHANGELOG.md](../CHANGELOG.md), see [STATUS.md](STATUS.md).

## Using a coding agent

Open this repository in your agent (Claude Code, Codex, …) and say:

> Install the Tomb Raider: Underworld DLC port for me. Follow `docs/INSTALL.md`. My game is in `<folder>` and my Xbox DLC files are
> somewhere under `<folder>`. Download the latest release kit, run the installer with `--check` first, show me the result, and only
> then install. Do not delete anything.

---

## Istruzioni in italiano (breve)

1. Servono: TRU **Steam PC** (exe v1.1), i file Xbox 360 del DLC **Beneath the Ashes** (`pack10.000` e `credits_DLC1.wmv`;
   `pack11.000` di *Lara's Shadow* è facoltativo), **ModLoader** nella cartella del gioco, **Python 3.9+** con `pip install bsdiff4`.
2. Scarica dalla pagina *Releases* `install_dlc.py` e `trudlcport-kit-B138.zip`, scompatta il kit nella cartella `kit`.
3. Gioco chiuso, prova a secco: `python install_dlc.py --game "<cartella gioco>" --dlc "<cartella file Xbox>" --kit .\kit --check`.
4. Se risponde *All inputs OK*, ripeti il comando senza `--check`. Vengono scritti `mods\`, `tru.exe` e `movies\credits_DLC1.bik`;
   i vecchi file restano come copie (`mods_backup_…`, `tru.exe.steam_original`).
5. Avvia da Steam → *Contenuti scaricabili* → *Beneath the Ashes* → *Gioca missione*, con una **nuova partita** DLC, e **blocca il gioco a 60 fps**.
6. Se compare "A problem has occured with your display driver": vedi [TROUBLESHOOTING.md](TROUBLESHOOTING.md) (rimedio con
   dgVoodoo2 e test da mandarci).
