# GOG build: research notes and tools

The installer refuses GOG builds on purpose. This folder records what is different on GOG, how the DLC was played on a
GOG install, and what was tested there. **Nothing here changes the installer, `scripts/`, `tools/` or the Steam path.**

Tested on: **GOG** Tomb Raider: Underworld (gameId `1900745791`, buildId `58082205556264096`), Windows 11, native
D3D9, RTX 3050, kit data B270. Labels: **in game** = played on GOG; **offline** = checked on files only.

## 1. GOG vs Steam: the files (offline)

| File | GOG MD5 | vs Steam (`docs/data/pc_game_files.tsv`) |
|---|---|---|
| bigfile.000 .. .003 | `839e192d…`, `f4ceeb06…`, `1d5b5c46…`, `b700d315…` | **identical** |
| patch.000 | `942d7f56…` | identical |
| fmodex.dll | `14e2160f…` | identical |
| binkw32.dll | `5afebc08…` | the Ultimate ASI Loader proxy (GOG ships it already) |
| tru.exe | `76b4da2fd9178299065bb83412f324ef` | differs from Steam `b36da327…` (no SteamStub); **same size as the Steamless output** (6 422 528) |

So the kit's data inputs are byte-identical on GOG. GOG also ships `D3D9.dll` + `dxwrapper.dll/.ini` (its D3D9
wrapper is off; `LoadPlugins=0`), and `DEPHook.asi` (turns DEP off; the exe has no NX / ASLR flags). Adding the DLC
needs only `ModLoader.asi`; GOG's `binkw32.dll` must not be replaced.

## 2. The GOG tru.exe vs the Steamless exe (offline)

- Same PE layout as the Steamless output: 6 sections (`.text .rdata .data .shad .rsrc .extra`), same size, LAA not set,
  `.text` flags `0x60000020`.
- **Every guard site of the chain has the original bytes**, and the build chain on `main` runs on the GOG exe
  **unchanged**: `scripts/build_exe.sh GOG_tru.exe out.exe` passes all stages (LAA, fmod `0x582200`, lighttex
  `0x50a645 / 0x50a683`, soundplex `0x5920d5`) -> md5 `5d7bb9cc…` (Steam reference result: `f47814ff…`).
- **Not byte-identical to the Steamless exe.** Known: the last 16 bytes of `.text` (`0x83dff0..0x83dfff`) are `0x10`
  padding on GOG, zeros on Steam. With those zeroed the GOG md5 is `2f5398c8…`, not `56d1ce2d…`, so **other bytes
  differ too** (where is unknown: no Steamless file here). That is why the md5-gated stages of `work/ws/exe_chain`
  refuse GOG.
- To find them without sharing exes: `tools/exe_block_hashes.py` prints one MD5 per 4 KiB block. The GOG list is in
  `data/blocks_gog_tru_76b4da2f.txt`; running the tool on `56d1ce2d…` and `--diff` against it lists the differing
  blocks. Sanity check: same file -> 0 blocks; GOG vs GOG with the padding zeroed -> exactly 1 block (`.text 0x83d000`).
- Plugin byte checks (the `windows` branch ASI plugins, `sig_audit.py`) against the GOG exe: 1 700 match, 13 explained,
  0 mismatches, 85 unresolved (run-time addresses).

## 3. How it was played on GOG

The exe **tested in game** is not `main`'s chain: it is the `windows` branch (LukasKurthRocks) B138 exe recipe
(LAA + fmod / lighttex / soundplex / combat-lock guards) built from the GOG exe with `tools/exe_build_gog.py` (GOG md5
gate, the 16 padding bytes zeroed because the combat-lock cave covers them), plus B270's camera-shake null guard
ported byte for byte (`tools/exe_port_guard.py --guard shakeguard`, checked against the B270 exe). DLC 2 movement then
runs through the `windows` branch ASI plugins (TruShadowPower, TruShadowCombat, TruRockVein, TruDoppelganger,
TruDlc2Player), not through the chain's native stages.

Data: the B270 kit files, then these repairs (tested in game as a set):
- **Native D3D9 shaders:** 500 of the 954 port pixel shaders were rejected by Windows' D3D9 (two different constant
  registers in one instruction) and crashed both DLCs. `tools/shader_const_fix_all.py` runs the existing
  `shader_const_fix.py` over all port libraries (2173 and >= 2720): 30 DRMs, 664 shaders, 0 rejected afterwards
  (native test). B271 addresses the same problem another way; not compared yet.
- `tools/playerblock_lock_fix.py`: the two documented player-block words (`+0x294`, `+0x25c` of the DLC 2 player
  object) without the Xbox base game.
- The title update's 6 input bindings (141-147) added to `generalbank` (fixed DLC 2 melee: combos, finishers, shadow
  attacks); exttuning, meleelink, script-clash and converter-fault repairs from the `windows` branch tools.

The wrappers import existing tools from a checkout given with `--fork DIR` (`exe_build.py`, `shader_const_fix.py`, DRM
readers) and do not modify them.

## 4. Results on GOG (in game)

- **DLC 1 complete**, start to credits.
- **DLC 2:** shadow power (slow motion, climb), melee incl. combos / finishers / shadow attacks, pistol, the Natla
  level change.
- **B272/B273 typelist fix confirmed on GOG** (2026-11-24): all 10 old byte patterns matched in our
  `doppelganger_casual` / `dlc_doppel_costume_a`; `tools/typelist_fix_gog.py` applies the same table and checks
  without hard-coded paths. In game: dropping onto a rock vein with the shadow now grabs it.
- **B274 tu616 confirmed on GOG:** the GOG exe holds the retail value at `0x85e4ac`; patched, the ledge after the vein
  that refused the grab while falling is now grabbed. `tools/patch_tu616_gog.py` = `patch_tu616.py` without its input
  md5 gate (same checks: retail value present, only the two `fcomp` references). Offline on the GOG chain output:
  3 bytes changed, a second run refuses. (The in-game test used -616.30 instead of the exact TU float -616.2975;
  the tool writes the exact value.)

## 5. Open, found on GOG

See `docs/INVESTIGATION.md` (this PR adds the item): instant death on the goo-room eitr-tub ledges.

## Files

| File | What |
|---|---|
| `tools/exe_block_hashes.py`, `data/blocks_gog_tru_76b4da2f.txt` | locate GOG vs Steamless byte differences by sharing hashes only |
| `tools/patch_tu616_gog.py` | B274 without the md5 gate |
| `tools/typelist_fix_gog.py` | B272/B273 table without hard-coded paths |
| `tools/exe_build_gog.py` | `windows` branch B138 exe stages on the GOG exe |
| `tools/exe_port_guard.py` | B270 camera-shake guard ported onto another exe, byte-checked against B270 |
| `tools/shader_const_fix_all.py` | shader constant fix over all port libraries |
| `tools/playerblock_lock_fix.py` | the two player-block words |
| `tools/sig_audit.py` | static audit of ASI plugin byte checks against an exe |

## Suggestion

A GOG input path could be: (1) `--diff` the block hashes against `56d1ce2d…`; (2) if the differences sit outside
patched ranges, normalise GOG to the chain input (or switch the stage gates from whole-file md5 to byte-site checks);
(3) accept GOG md5 `76b4da2f…` in the installer. Not done here, to keep the Steam path untouched.
