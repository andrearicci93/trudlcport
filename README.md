# trudlcport

Port of the **Xbox 360-only DLC of Tomb Raider: Underworld** (*Beneath the Ashes*) to the **Steam PC game**, without an emulator.
**DLC1 is playable from the start to the end credits.** DLC2 (*Lara's Shadow*) is not converted yet.

Latest build: **B138** → [Releases](https://github.com/andrearicci93/trudlcport/releases/latest)

## Install

You need: the Steam PC game, your own Xbox 360 DLC files (`pack10.000`, `credits_DLC1.wmv`), [ModLoader](https://github.com/TombRaiderModding/ModLoader/releases) in the game folder, and Python 3.9+ with `pip install bsdiff4`.

1. From [Releases](https://github.com/andrearicci93/trudlcport/releases/latest) download `install_dlc.py` and `trudlcport-kit-B138.zip`; unzip the kit into a folder named `kit`.
2. Close the game and check your files first:
   `python install_dlc.py --game "<game folder>" --dlc "<folder with the Xbox files>" --kit kit --check`
3. If it says *All inputs OK*, run the same command without `--check`. The old `mods\` and `tru.exe` are kept as backups.
4. Start a **new DLC game** from Steam → *Downloadable content* → *Beneath the Ashes*, and **lock the game to 60 fps**.

Details, requirements and problems (display-driver error, crashes, 60 fps): [docs/INSTALL.md](docs/INSTALL.md) · [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## Changelog

**B138 (21 Oct 2026) — offline-verified, not played yet** (B132 is the last build played end to end)
- B133: 274 shaders fixed for native Direct3D 9 (probable cause of the *"display driver"* error on real GPUs)
- B134–B137: mechanism joints in pillory and dungeon, bat generators
- B138: DLC audio no longer crackles (39 `.mul` re-encoded)

Still open: rare crash at start-up (restart), golden shotgun untested, dungeon material 23211, DLC2.
Full list, with what should now be fixed and what to report: [CHANGELOG.md](CHANGELOG.md).

## More

[Status](docs/STATUS.md) · [Development notes, repository map, rebuild](docs/DEVELOPMENT.md) · [Technical findings](docs/FINDINGS.md)

## Legal

Tomb Raider: Underworld and its DLC belong to their respective owners. This project is unofficial and for people who own the PC game and the Xbox 360 DLC: the release kit is binary patches that are useless without (and checked against) your own files, and the repository contains no game data. Code is MIT-licensed (see `LICENSE`).
