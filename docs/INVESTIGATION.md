# What still has to be investigated

Ordered roughly by value to a player. Every item lists the evidence so far, hypotheses, and the tools to start from. Rules that proved useful: no blind VM trials; read the code and build an offline oracle first; static gates before every test; never mix the two shader "regimes" (transplant vs direct translation) in one material.

## 1. dlc_dungeon looks "broken" on natural arrival (highest priority)
**Symptom:** reaching *dlc_dungeon* by playing (pillory → dungeon) gives a level that looks wrong/broken. The exact symptom was not described yet — **first ask the tester what is missing or wrong** (missing geometry? lighting? collision? objects?).
**Facts:** loading the same level via the F8 debug menu (`dungeon_direct_cal`) loads and stays alive; the natural path crashed with R6025 (fixed) and then `0x592218` (guarded). The difference is the set of DRMs resident when the level loads.
**Hypotheses**
* Another instance of the *texture lifetime* class: the engine keeps one global texture cache keyed by id with a per-DRM refcount, so a texture used by a material but contained only in a DRM that gets unloaded dangles. `work/crash/B84_r6025/tex_lifetime_check.py --types 5,9,10` checks this statically for scenarios `all_resident` and `only12`; `only12` still reports **84 unknown textures** (type 5) — look at those first.
* The same class for other resource types (shader libs, DTPs): extend the check beyond types 5/9/10.
* The SoundPlex null node (guarded) may be one symptom of a missing/unloaded DTP; read the guard counters (VA `0x83DF00`, magic `SPG1`: calls, hits, last_edi, last_type) after reaching the level.
* The dead-bit issue (item 6) can hide objects whose spawn is gated by a `uid ≥ 16352`.
**How:** capture the engine log (`tools/vm_logtail.ps1`) on a natural arrival and compare with a direct-load log; diff the list of loaded units/objects; `tools/vm_crash_watch.ps1` can take a full dump if something crashes.

## 2. Cobwebs (materials 20673, 20676, 23173, 23329, 20876)
**Facts:** webs use PC stock lit shader library 242 (8 slots) with additive blend (`material +0x38 = 5`, `SRCALPHA/ONE`); the Xbox shaders are libs 2199/2209/2094. Params were synthesised by `tools/web_cutout.py` (never validated against an oracle). In the fog-aware harness (`work/ws/giro6/web_calib.py`, `web_lever.py`) the PC output is ~2× brighter than Xbox for 23173/23329 (fixed with `c104.x` = 0.46/0.44) and ~1.0–1.4× *dimmer* for the other three. The user still sees them wrong.
**Pitfalls found:** `s15` in these shaders is the **fog lookup** (`texld (v4.w, c54.z), s15`), not only the light attenuation sampler — return 0 for the fog read in any harness, or the output collapses to the fog colour. Data is identical in every DRM (`work/ws/giro6/web_cmp.py`), so differences between levels come from lighting/fog context, not from the material.
**Unknowns:** which of the 8 PC slots / 2 Xbox variants the engine really selects; the real fog colour and ambient/irradiance per level; whether alpha (PC 0.35–0.81 of the Xbox flat alpha on strand pixels) is the real problem; whether the Xbox draws webs in a different pass/sort order (the `+0x40` bit pattern differs but is only a sort class).
**Next:** get a reference frame of the same room on the Xbox/Xenia and compare numerically; test one lever at a time in the VM (`c104.x`, `c100.w` alpha, `c98.x` opacity) on a single web material.

## 3. Reddish surfaces in dlc_caverns_hall
**Facts:** all 14 stock-PC-shader materials of the hall have MaterialParams identical to the Xbox (`work/ws/giro7/hall_params_audit.py`); surrogate-lib materials only show rule-driven record permutations; the simulation with a red ambient and strong lights gives PC−Xbox chroma differences ≤ 0.006; mean texels equal. Earlier, B41 had introduced red tints and 5–15× multipliers; B42/B83 removed the ≥ 2× ones.
**Hypotheses not yet tested:** per-level ambient/irradiance values fed by the engine (registers c70–c76, `g_Ambient` c15) come from level data we converted — check the light/irradiance DTPs of the hall; vertex colour channel order (BGRA vs RGBA) in converted meshes; texture format conversion details (DXT/DXN, sRGB); the not-simulated surrogate libs of the hall list (materials 21164/20345, 23211, 23198, 20167, 20548, 20265, 21084, 24275, 20211); materials in streamgroups visible from the hall (not audited).
**Next:** a reference screenshot of the same spot from the Xbox; then bisect by replacing one material's lib at a time.

## 4. Bridge collapse / Adrenaline trap
After `Cine_End` of `pdlc1_010_intro` the bridge should collapse (`ma_ei_breakable_k..t`, script 23175 in `dlc_level1_start`, `dlc_caverns`). The bridge exists but behaviour is unverified. Needs script decoding: Xbox script interpreter `FUN_82223398` vs PC `FUN_0057ce50` (same 133-case structure); see `work/ws/cancello/` for a worked example of tracing a script chain.

## 5. Sluice gate at the water wheel
Last analysis (15 Oct): the bar is `dlc1_uo_sewer_gate` (intro 9759), it lowers by itself ~7 s after load and consumes its `initial→locked` transition before the grapple; a link record between two joints is suspected. Status in current builds unknown — **re-test first**.

## 6. Dead bits (uid ≥ 16352)
The engine has 16352 bits for unique ids. DLC intro uids 29392, 29397, 29395, 29396, 26713 (Xbox ids + 20000) are outside. A remap to free uids 12241–12245 across intro + DTP + script words was built (layer L2 in `work/ws/giro6/layers.py`) but **dropped** because the uids also appear in map sections (type 13: `dlc_dungeon_map`, `dlc_pillory_map`, `dlc_dungeonhalla_map`, `dlc_dungeonhallb_map`) that the remap did not touch. A correct fix must remap those too (`work/ws/giro6/uid_refs_all.py` lists every reference).

## 7. SoundPlex null node (root cause)
`FUN_005920b0` walks SoundPlex nodes `{u32 type 0..13, ptr data}`; type 0 reads a float through `data`. Some node arrives with `data == NULL`. `work/ws/giro7/soundplex_null_audit.py` found no Xbox↔PC discrepancy in DTPs that exist on both sides, but DTPs with different size (848, 20327, 20558) and DRMs without an Xbox twin are unaudited. Find which DTP produces the null node (read `last_edi` from the counters, locate the owning DTP in memory).

## 8. Remaining lit-shader surrogates and the shader oracle
Libs 21118 / 20262 / 21164 have no donor. The direct-light path of the harness is unvalidated (direct light share < 50 % in 16/32 cases), so lit-material conclusions are weak. A better oracle (e.g. compare against a real Xbox/Xenia render of one lit surface under known lights) would unlock items 2 and 3.

## 9. Everything else
* DLC2 (*Lara's Shadow*, `pack11.000`): the converter handles generic parts, nothing was tested.
* F8 debug menu not working for the tester.
* Audio quality (IMA encoder) never re-judged after B43; A/B listening clips (original XMA vs converted) were produced by scripts that are not part of this repo.
* Water in the dungeon, stained-glass window noise, torch/axe visuals: listed as open in older notes, not re-checked.
