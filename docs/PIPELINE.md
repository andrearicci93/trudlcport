# Pipeline: how the `mods/` tree is produced

The final tree (`B90_gold_L4`) is **not** the output of one script. It is a chain of immutable "baselines": a base conversion, then ~90 derived steps, each replacing a handful of files and each passing static gates. This file maps the stages to the scripts that exist in this repo. Scripts were written with the original machine's absolute paths replaced by `/path/to/...` placeholders — run `scripts/set_root.sh` and fix the Xbox-file paths (see SETUP.md).

Convention used everywhere: `python -I tools/<script>.py` inside the project venv (`-I` isolates from user site-packages). Never write into a baseline; derive a new one.

## Stage 0 — indexes and pairings
* `tools/archive.py`, `tools/bigfile.py`, `tools/index_all.py`: read PC (little-endian) and Xbox (big-endian) bigfile/layer/pack archives; `index_all.py` produces `work/idx_pc.json`, `idx_xbox_base.json`, `idx_dlc.json` (which DRM sits in which archive, with section lists).
* `tools/generic_cache.py`, `generic_store.py`, `generic_ids.py`, `generic_symbols.py`, `pairs.py`, `tex_pairs.py`: pair every base-game Xbox section with its PC twin to learn id maps and per-type conversion rules. The PC `patch.000` overrides the bigfile; the Xbox `TitleUpdate.000` overrides the layers ("runtime authoritative").
* `tools/drm.py`, `drm_write.py`, `drm_reloc.py`: DRM/CDRM reader and writer, relocation tables (internal and external), section order rules. `tools/dtp_schema.py`, `dtp_*`: DTP (data-type-property) schemas.

## Stage 1 — generic conversion Xbox DLC → PC
`tools/convert_dlc.py OUTDIR name.drm ...` → `assemble_dlc.assemble()` → `dlc_generic.convert_drm()` with media callbacks:
* type 5 textures: `tex_convert.py` (de-tiling, DXT/DXN, endian) 
* type 6 waves: `wave_convert.py` (initially silence; real audio later by `wave_swap.py`)
* type 10 materials: `material_dlc.py` / `material_convert.py` (shader-tuple remap, MaterialParams rules)
* type 12 meshes / terrain: `mesh_convert.py`, `terrain_convert.py`
* ids: `DlcIds` (one deterministic table; DLC-new ids keep their Xbox value unless they collide with a PC id).
`tools/dlc_convert_all.py [--media] [--write]` converts and self-checks every DLC DRM. Result of this stage = the early baselines (`mods_fix*`, B1–B11).

## Stage 2 — data fixes found by comparing with the base game
Each is small, evidence-driven, and listed in LINEAGE.md. Examples:
* DTP word conversions: `tools/dtp_*`, `work/ws/progress/template_rule.py`, `apply_words.py`; float words left unconverted: `work/ws/cine/float_fix.py`.
* Raft/grapple rings: record tag `0x404`, enable byte raw (`work/ws/raftring/`).
* Cutscene command lists: `work/ws/cine/build_cine.py`, `cine_cmd.py` (106/106 base DTPs reproduced exactly).
* Streamgroup names, ids, padshock, locals: `tools/streamname_fix.py`, `padshock_convert.py`, `locals*.py`.
* Real audio: `tools/wave_swap.py` (8 227 Wave sections, in place, same size), `tools/mul_audio_batch.py` (XMA → IMA stereo for `.mul` streams).
* Enemy AI records (0x390-byte records in level DTPs, DTP ids without relocation): `tools/aidata_fix.py` inside the converter.
  Its table `work/generic/aidata_table.pkl` is **gitignored** and rebuilt by `../bin/pyt tools/aidata_fix.py learn`
  (pipeline step Prep, seconds; inputs `work/generic/pairs.pkl` from step Cache and the base id map of the generic store
  from step Ids; expected output `offsets 93 ambiguous/conflicting 0`, 450 base records). Since 2026-11-13 a missing or
  empty table stops every caller with exit 1 (before it silently changed nothing: the 12 Nov run shipped 19 wrong
  records). Gate on the output trees (step Fixes): `tools/scan_aidata_tree.py check TREE --pack PACK` (exit 1 on a wrong
  id / count).
* DLC 1 start: the retired rule `CINE_SKIP` (2026-10-09 .. 2026-11-13, skipped the intro cinematic) is off; gate
  `tools/cine_call_gate.py check TREE` (step Fixes): script 20068 +0x6c4 must call Cinematic_Object 3523 +0x2410
  (vtIndex 57 PlayCinematic). Old trees: `tools/dlc_patch.py --only=cine_play OUT SRC dlc_level1_start.drm`.
* Script intro / marker references (2026-11-14, P4.8): init words of base type 10 / userType 4261 (PC 4697) keep the
  u16 intro id (intro id map) in `tools/script_learn.py` (`TRUDLC_SCRIPT_INSTREF=off` = the learned table). Proof + gate
  (step Fixes): `tools/instref_gate.py proof` / `check TREE --pack PACK --expect-refs`. Old trees:
  `tools/instref_gate.py fix OUT SRC name.drm ...`.
* Map collision meshes (2026-11-14, P4.9): the `*_map.drm` Mesh (header, vertices, faces, KD nodes) is converted by place
  (`tools/map_mesh_fix.py`, `dlc_generic` type 13, `TRUDLC_MAP_MESH=off` = the learned table). Proof + gate (step Fixes):
  `tools/map_mesh_fix.py proof` / `check TREE`. Old trees: `tools/map_mesh_fix.py fix OUT SRC [name_map.drm ...]`.
* Cell stream lists (2026-11-14, F1): every {u16 StreamUnitID, u16 streamgroup index} pair of the per-cell lists in the
  unit DTP goes through the unit id map (`tools/unit_ids.py cell_stream_fields`, applied in
  `generic_type0.fix_unit_fields`; `TRUDLC_CELLSTREAM=off` = the learned table, which mapped only the first pair of a
  list - pillory reload hang). Proof + gate (step Fixes): `tools/cellstream_fix.py proof` / `check TREE --pack PACK`
  (also index + 1 < record count of the named unit's streamgroup table). Old trees:
  `tools/cellstream_fix.py fix OUT SRC name.drm ...`.

## Stage 3 — shaders and materials (the long tail)
PC pixel shaders cannot be copied from Xbox microcode, so the Xbox shader libs are **translated**:
* `work/ws/shader4/`: Xbox Xenos microcode → SM3 translator (`xenos2sm3`), SM3 assembler/disassembler (`sm3asm`, 6139/6139 PS and 15789/15789 VS round-trip), a numeric VM (`sm3vm`) used as an oracle, lib builder `f4_build.py`, gate `gate_stesso_id.py` (same material ⇒ same lib bytes in every DRM).
* Two regimes, never mixed in one material: **light transplant** (Xbox lit shader + a PC light block copied from a donor PC shader; `f9_transplant.py`, `f10`, `f12`) and **direct translation** of unlit shaders (`f13_unlit.py`).
* `work/ws/contratti/`: the *sampler contract* (`f14_slotmap.py`): Xbox sampler register → PC sampler slot of the canonical material; `test_contract.py` (16 tests).
* Builders per baseline: `work/ws/codefirst/build_B87.py` (19 materials), `work/ws/giro5/build_unlit.py` (7 water libs 2775–2781), `work/ws/giro6/build_20323.py` (lib 2782).
* Validation on a real device: `tools/vm_ps_validate.ps1` (CreatePixelShader) and `tools/vm_ps_draw.ps1` (draw + present) with dgVoodoo's `d3d9.dll`.

## Stage 4 — the last layers (Giro 5–7), reproducible from `B88b_acqua`
Run from `work/ws/giro6` after setting paths (all layers read the previous state and write only changed files):
1. `layers.py L1 L3a L3b` (skip `L2`): 
   * L1 adds textures 259 (to `dlc_costume_b/c/e/f/j/o`) and 2224 (to `doppelganger`) copied from the base game, appended at the end of the DRM (no external reloc may point past the original section count);
   * L3a copies shader libs 975/976 into streamgroups `dungeon_main` and `dungeon_sewer`;
   * L3b copies lib 2782 (material 20323, `knight_thrall`; built by `build_20323.py`) into 4 DRMs.
2. `l4_webs.py SRC OUT 23173=0.46,23329=0.44 c104x`: sets `c104.x` of the material's MaterialParams record 4 (asserts the old value is 1.0) in every DRM containing the material.
3. `work/ws/giro7/compose7.sh` and `compose.sh` assemble `B88b + tree`; `run_gates.sh` / `work/ws/giro7/run_gates7.sh TAG` run the static gates (expected: `idref_selfcont` solo_base 0 / NESSUNO 0; `gate_stesso_id` 0 new divergences; `tex_lifetime_check` 0 violations for types 5/9/10 in scenarios `all_resident`/`only12`; `test_contract` 16/16; `dlc1_gate --compare` OK).
4. `tools/baseline_derive.py --parent B90_gold --name B90_gold_L4 relpath=path ...` records the new baseline with a manifest; compare with `docs/data/B90_gold_L4.manifest.tsv`.

## Stage 5 — executable
See SETUP.md §2: LAA flag + `fmod_init_guard` + `light_tex_guard` + `soundplex_guard` (`scripts/build_exe.sh`).
Fork: pipeline step `Exe` (`tools/exe_build.py`, with the fourth guard `combat_lock_guard`; gate md5 = the B138 exe),
also under `-Player` (2026-11-17: 0 refused accesses).

## Player path: knowledge package (plan Spielerweg P2, 2026-11-17)
* `tools/knowledge_export.py slim-mask PKG`: the learned mask table (`work/generic/mask_table.pkl`, 778 MB of counters)
  as `PKG/learn/mask_best.npz` + `mask_best_vocab.json` (per key only the class `Table.best()` gives - the converter calls
  nothing else); gate in the same run: `best()` equal on every key (19 538 409 / 19 538 409, 0 hash collisions).
* `export PKG` copies the id maps, learned classes, rules and render tables (32 files, 332 MB; never a source the
  player-path guard refuses) and writes `PKG/manifest.json` + `docs/data/knowledge_manifest.json` (names, sizes, md5);
  `check` / `same` re-hash the package / its sources; `place PKG` puts the tables at the work paths the tools read.
* The converter takes the package's mask table with `TRUDLC_MASK_TABLE=PKG/learn/mask_best.npz` (unset = as before).
* Open: a pipeline step `Knowledge` (place + skip Cache / Ids / Learn / Tables / Prep under `-Player`), the pickles as
  JSON / npz, `mask_best.npz` / `type0_table_slim.npz` over 100 MB (cut to the keys the DLC inputs use, P7), and Convert
  still needs the developer store (`store.pkl` with `xb_store`, P3 / P8).

## Stage 6 — deployment and testing (VM)
* `tools/vm_baseline_sync.ps1 -Baseline X -Mode dryrun|apply|verify [-RestoreSave name]`: makes the game's `mods/` byte-identical to a baseline (extra files are quarantined, never deleted); `verify` compares MD5 of everything (non-critical files are size-checked only in `apply`).
* `tools/vm_run.ps1` + `tools/runner_scenarios/*.json`: scripted runs (e.g. `dungeon_direct_cal`: load *dlc_dungeon* through the F8 menu, PASS = level reached and alive N seconds, evidence in `work/runs/<id>/result.json`). Always started detached.
* Crash tooling: `tools/vm_crash_watch.ps1` (full dump on crash), `vm_logtail.ps1` (engine log), `vm_read_ltg.ps1` (light-guard counters; the SoundPlex counters live at `0x83DF00`).

## What is missing to make it one command
Glue between stages 1–2 and the early baselines: the order in which the ~90 data fixes were applied is only recorded in the manifest notes (`origin` / `exception` columns of the original manifests) and in LINEAGE.md. A reasonable first goal for a contributor: write a script that applies the fixes in that order to a fresh stage-1 conversion and reproduces every file of the manifest (MD5-exact), starting with the files whose origin is `derived:B43` (71 audio files) and `mods_fix12` (46 files).
