# Instructions for coding agents (Claude Code, Codex, …)

Project: PC port of the Xbox 360 DLC of *Tomb Raider: Underworld* (DLC1 "Beneath the Ashes", DLC2 "Lara's Shadow") through ModLoader. Read this file first, then the docs in the order below. The human you work with decides the direction and does the in-game testing; you do the investigation and the implementation.

## Read first (in this order)
1. `README.md`: what the project is and what is supported.
2. `docs/STATUS.md`: what works, what is open, where we stopped. Check it before starting: your topic may already be partly done or a known dead end.
3. `docs/AGENT_GUIDE.md`: full agent brief (ground rules, tasks A–E, entry-point scripts).
4. `docs/DEVELOPMENT.md`, `docs/PIPELINE.md`, `docs/FINDINGS.md`, `docs/INVESTIGATION.md`: repository map, build pipeline, verified engine/format knowledge, open questions.
5. `CHANGELOG.md`: what each build changed. Add an entry for every change that ends up in a build.

## Hard rules
- **Never commit game data**: no DRM/CDRM, bigfiles, `.exe`, `.mul`, Xbox files, converted `mods/` trees, decompiler output, dumps. `.gitignore` blocks the common extensions; do not work around it. Binary patch kits are published only as release assets by the owner.
- **Never touch the user's game folder without asking.** Keep a backup of `tru.exe` and `mods/` first. Never delete or overwrite without an explicit yes, and look at the target before doing it.
- **Baselines are immutable.** Derive a new one (`tools/baseline_derive.py`), never edit in place.
- **Code first, no blind exploration.** Read the code and build an offline check (oracle) before asking the human to play. Run the static gates on any new `mods/` tree before testing it.
- **One lever at a time.** One hypothesis, one minimal change, one gate, one in-game check. Mixed changes make results unreadable.
- **No private data in the repo**: no personal paths, usernames, emails or tokens. Use placeholders such as `/path/to/` (`scripts/set_root.sh` rewrites them for a checkout).
- **Fixes apply to both DLCs.** A conversion fix found for DLC2 must be checked (and applied if needed) on DLC1, and the other way round.

## Reporting
Say exactly what was verified **in game**, what only **offline**, and what is a **hypothesis**. If a test fails, report the output as is. Sanity-check every harness: change an input that should matter and confirm the output moves; several earlier conclusions had to be retracted because a harness was wrong. Do not write "should work" without proof.

## Supported setup and game versions
- Supported: Steam PC build of Tomb Raider: Underworld, patched `tru.exe` (see `docs/INSTALL.md`, `docs/SETUP.md`). The installer refuses other builds (GOG, retail DVD) on purpose rather than produce a broken result.
- The development environment is Windows 11 (VM) with dgVoodoo2 plus a native D3D9 test path (`tools/win_diag`, branch `native-d3d-test`). macOS/Linux is enough for the offline tools.
- Work on a GOG install is welcome as research, but state clearly which build a result was tested on, and do not break the Steam path.
- Python tools: use a venv, `python3 -m venv tools/venv && tools/venv/bin/pip install -r requirements.txt`, then run `tools/venv/bin/python -I tools/<x>.py`.
- Source comments and log strings in the scripts are largely Italian (original working language). Docs, commit messages and PRs are in English.

## Workflow for contributors
1. Fork (or, if you have write access, branch) from `main`; **one branch per topic**, for example `flashlight-shadow`. Never push directly to `main`, `release-b138` or `native-d3d-test`.
2. Open a **draft PR early**, even rough, so nobody duplicates work. In the PR description: the goal, the hypothesis, the files touched, how it was checked (offline / in game), and which game build (Steam / GOG) it was tested on.
3. Before starting a topic, comment on the related issue (or open one) saying what you are going to work on.
4. Save findings next to the code: a short note in `docs/FINDINGS.md` (verified facts) or `docs/INVESTIGATION.md` (open questions), plus the script that reproduces them in `tools/` or `work/ws/`. Put raw outputs that are large or derived from game data outside the repo.
5. Keep commits small and focused; do not reformat unrelated files.

## Useful entry points
See the table at the end of `docs/AGENT_GUIDE.md` (DRM reading, gates, material/texture lookups, shader harness, exe guards, crash dumps).
