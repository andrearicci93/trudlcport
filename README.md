# trudlcport

Work-in-progress port of the **Xbox 360-only DLC of Tomb Raider: Underworld** — *Beneath the Ashes* (DLC1) and *Lara's Shadow* (DLC2) — to the **native PC version** (Steam `tru.exe`), without an emulator.

The result is a `mods/` overlay for the PC game (loaded by a third-party mod loader) plus a few small binary patches to `tru.exe`. DLC1 is playable up to and including the *dlc_dungeon* level in the current best build (`B90_gold_L4`), with known visual and gameplay defects (see [docs/STATUS.md](docs/STATUS.md)). DLC2 has not been started.

> **No game data is included in this repository.** You must own the PC game, and you must supply the Xbox 360 files yourself (see [docs/SETUP.md](docs/SETUP.md)). The repo contains only the conversion tools, patch tools, analysis scripts, notes, and a hash manifest that lets you check your own output.

## Where we are (short version)

| | |
|---|---|
| Best build | `B90_gold_L4` (manifest: [docs/data/B90_gold_L4.manifest.tsv](docs/data/B90_gold_L4.manifest.tsv), 279 files) + patched exe `f47814ff…` |
| Crashes | None in the last user test (new game → bridge → pillory → dlc_dungeon reached naturally) |
| Works | Boot, DLC menu entry, opening cutscene, converted audio, grapple rings, water wheel, most geometry/textures/materials |
| Broken / open | Cobwebs look wrong, reddish surfaces in *caverns_hall*, *dlc_dungeon* looks "broken" when reached naturally, bridge-collapse/Adrenaline trap, sluice gate, DLC2 |

Details: [docs/STATUS.md](docs/STATUS.md) · open questions with leads: [docs/INVESTIGATION.md](docs/INVESTIGATION.md).

## Repository map

| Path | What it is |
|---|---|
| `docs/SETUP.md` | Which files you need and how to install the result |
| `docs/STATUS.md` | What works, what does not, where we stopped |
| `docs/INVESTIGATION.md` | What still has to be investigated, with hypotheses and the tools to use |
| `docs/PIPELINE.md` | How the build is produced, layer by layer, and which script does what |
| `docs/FINDINGS.md` | Verified technical knowledge about the file formats and the engine |
| `docs/LINEAGE.md` | History of the build steps (B1 → B90) |
| `docs/AGENT_GUIDE.md` | A ready-made brief for a coding agent (Claude Code, Codex, …) to run or continue the project |
| `tools/` | Converters (Xbox → PC), DRM reader/writer, shader translator pieces, exe patch tools, gates, VM helper scripts |
| `work/ws/` | Workstream scripts (shader translation, cutscene fixes, giro5/6/7 layers, code-first reverse engineering helpers) |
| `work/crash/` | Crash-diagnosis scripts |
| `scripts/` | `build_exe.sh`, `make_laa.py`, `check_inputs.py`, `verify_mods.py`, `set_root.sh` |

## Quick start (for a human)

1. Read [docs/SETUP.md](docs/SETUP.md) and collect the required files.
2. `python3 -m venv tools/venv && tools/venv/bin/pip install -r requirements.txt` (Windows: `tools\venv\Scripts\`).
3. `scripts/set_root.sh` (rewrites the hard-coded path placeholders to your checkout).
4. `python3 scripts/check_inputs.py "<your TRU game folder>" --md5`.
5. Build the patched exe: `scripts/build_exe.sh <Steamless-unpacked tru.exe> out/tru.exe`.
6. Produce / obtain the `mods/` tree and check it with `python3 scripts/verify_mods.py <game>/mods`.

**Honest caveat:** the full chain from the raw Xbox files to the 279-file `mods/` tree was developed incrementally over ~90 derived builds and is **not yet a single one-command script**. The converters, the layers and the verification manifest are here; the glue is described in [docs/PIPELINE.md](docs/PIPELINE.md) and [docs/LINEAGE.md](docs/LINEAGE.md). A coding agent can follow [docs/AGENT_GUIDE.md](docs/AGENT_GUIDE.md) to rebuild it step by step and verify each step against the manifest.

## Using a coding agent

Open this repo in your agent and say, for example:

> Read `README.md` and `docs/AGENT_GUIDE.md`. My PC game is in `<path>`, my Xbox 360 files are in `<path>`. Check my inputs, build the patched exe, and then work through `docs/PIPELINE.md` to produce the `mods/` tree, verifying against `docs/data/B90_gold_L4.manifest.tsv`. Stop and ask before touching anything inside the game folder.

## Language note

All documentation is in English. Source-code comments, docstrings and some log strings inside the scripts are largely in **Italian** (the original working language); the code is otherwise self-explanatory and each guard tool prints its exact patch bytes.

## Credits and third-party software

Not included, needed by the setup: [ModLoader](https://github.com/TombRaiderModding/ModLoader) (GPL-3.0), [TRLAU-Menu-Hook](https://github.com/TheIndra55/TRLAU-menu-hook), [dgVoodoo2](http://dege.fw.hu/), [Steamless](https://github.com/atom0s/Steamless), and (for analysis) Ghidra. The Xbox 360 executable analysis used XenonRecomp's `xex_dump`/`XenonAnalyse`. Thanks to the Tomb Raider modding community for the cdcEngine tooling.

## Legal

Tomb Raider: Underworld and its DLC are the property of their respective owners. This project is unofficial, ships no copyrighted game content, and is intended for people who own the game and the DLC. Code in this repository is MIT-licensed (see `LICENSE`).
