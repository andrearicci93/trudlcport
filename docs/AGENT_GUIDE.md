# Guide for a coding agent

You are helping a user who owns *Tomb Raider: Underworld* (PC, Steam) and the Xbox 360 files of its DLC. Goal: reproduce, verify, or improve the PC port in this repository. Read `README.md`, `docs/STATUS.md` and `docs/PIPELINE.md` first.

## Task 0 — the user only wants to play
Follow `docs/INSTALL.md`: get the latest release (`gh release download -R andrearicci93/trudlcport` or the Releases page), unzip the
kit to `kit/`, `python -m pip install bsdiff4`, run `python install_dlc.py --game <game> --dlc <xbox files> --kit kit --check`, show the
user the output, then run it without `--check` only after the user agrees. Make sure ModLoader is in the game folder. Never delete
the user's files: the installer keeps `mods_backup_*` and `tru.exe.steam_original`.

## Ground rules
1. **Never commit game data to git** (DRM/CDRM, bigfiles, exe, converted mods, Xbox files, decompiler output). `.gitignore` already blocks the common extensions; keep it that way. The binary-patch kit is published only as a release asset, by the owner's decision.
2. **Never modify the user's game folder without asking**; always keep a copy of `tru.exe` and `mods/`. `vm_baseline_sync.ps1` quarantines extra files instead of deleting.
3. Treat baselines as immutable: derive new ones (`tools/baseline_derive.py`), never edit in place.
4. Gate before testing: run the static gates for any new `mods/` tree before asking the user to play it. Do not use the VM/game for blind exploration; read code and build an offline oracle first.
5. Report faithfully: say what was verified in-game, what only offline, and what is a hypothesis. Several earlier conclusions had to be retracted because a harness was wrong (e.g. the cobweb fog lookup) — sanity-check harness outputs against sensitivities (does changing an input you expect to matter move the output?).
6. Use a venv: `python3 -m venv tools/venv && tools/venv/bin/pip install -r requirements.txt`, run tools as `tools/venv/bin/python -I tools/<x>.py`.

## Task A — set up and verify inputs
```
scripts/set_root.sh
python3 scripts/check_inputs.py "<PC game folder>" --md5
grep -rn "/path/to/" tools work | head        # point the Xbox-file placeholders at the user's files
```
Ask the user for: PC game folder; folder with `layer1.000`, `layer2.000`, `TitleUpdate.000`; folder with `pack10.000`, `pack11.000`, `pack1.000`, `pack2.000`; whether they want to run in a Windows VM.

## Task B — build the patched executable
1. Ask the user to run Steamless on their `tru.exe` (or run it if installed). 
2. `scripts/build_exe.sh unpacked.exe out/tru.exe`; expect MD5 `f47814ff116a4a33842bdb846bf97982` with the reference unpack (`56d1ce2d…`). If the unpack differs, run each tool with `--check` and read its message; do not force.
3. Back up the user's `tru.exe`, then (with permission) install `out/tru.exe`.

## Task C — obtain the `mods/` tree
* If the user already has a tree: `python3 scripts/verify_mods.py "<game>/mods"` against the manifest; report differences.
* Otherwise follow `docs/PIPELINE.md` stages 0–4. Work incrementally: after each stage compare the files you produced with `docs/data/B90_gold_L4.manifest.tsv` (size and MD5) to find the first divergence. Expect stage 1 alone not to be MD5-identical to the final files; the data fixes of stage 2 are listed in `docs/LINEAGE.md`. Record any new glue as a script in `scripts/`.

## Task D — install and test
Install ModLoader (user-supplied), copy the tree to `<game>/mods`, verify, launch, start the DLC from the menu. If a VM is used, `tools/vm_baseline_sync.ps1` and `tools/vm_run.ps1` document the automated flow (paths like `Z:\trudlcport` are the VM's shared folder — adapt).

## Task E — continue the investigation
Pick from `docs/INVESTIGATION.md`. Start with item 1 (ask the user for the exact symptom of *dlc_dungeon*), then 2–3 if a reference frame (Xbox/Xenia screenshot) exists. For each experiment: write the hypothesis, the offline check, the minimal build change (one lever at a time), the static gates to run, and what to look for in-game. Keep a short report like the ones summarised in `docs/STATUS.md`.

## Useful entry points
| Need | Script |
|---|---|
| Read a DRM / dump sections | `tools/drm.py`, `tools/dump_info.py`, `tools/compare_drm.py` |
| Static gate for a tree | `tools/dlc1_gate.py <mods> --scope overlay --baseline … --compare`, `work/ws/giro6/idref_selfcont.py`, `work/ws/shader4/gate_stesso_id.py`, `work/crash/B84_r6025/tex_lifetime_check.py` |
| Which texture/lib/material is where | `work/ws/giro6/mat_rows.py`, `mat_libs.py`, `tex_selfcont.py`, `uid_refs_all.py` |
| Shader harness | `work/ws/shader4/f9_common.py` (Env, run), `work/ws/giro5/hall_lit.py`, `web_eval2.py`, `work/ws/giro6/web_calib.py` |
| Engine function map / patches | `tools/*_guard.py` (each documents the exact bytes), `docs/FINDINGS.md` |
| Crash dump reading | `tools/minidump_read.py`, `tools/vm_crash_watch.ps1` |

## Suggested prompt for the user to paste
> Read `README.md` and `docs/AGENT_GUIDE.md`. My Steam game is in `<path>`; my Xbox 360 files are in `<path>`. Do Task A and Task B, then tell me what is missing for Task C. Do not change anything inside the game folder without asking me first.
