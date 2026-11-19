<#
.SYNOPSIS
    Runs one stage of the trudlcport conversion pipeline (Python tools in the clone) with full logging.

.DESCRIPTION
    Each -Step runs one or more tools from the trudlcport clone root with the project venv
    (..\bin\venv\Scripts\python.exe -u -I -X utf8 tools\<tool>.py ...). Output is shown live and written to
    <workspace>\logs\Invoke-TruPipeline_<step>_<time>.log; at the end a summary with duration and exit codes is printed.
    The tools only read the game / Xbox data (via <workspace>\data junctions) and write below work\ of the repository.

    Steps (in order):
      Index    tools\index_all.py (3x)        which DRM sits where, with section lists
               -> work\idx_pc.json (bigfile + patch.000), idx_xbox_base.json (layers + TU), idx_dlc.json (pack10/11 and,
               since 2026-11-03, the costume packs pack1/2/20 after them)
      Cache    tools\generic_cache.py        pair the base-game DRMs Xbox <-> PC  -> work\generic\pairs.pkl
               tools\generic_cache.py patch   runtime pairs (Xbox TU / PC patch.000) -> work\generic\pairs_patch.pkl
      Ids      generic_store, generic_ids, objlists_extract (our reconstruction), objlist_merge
               -> store.pkl, idmap.json, merged\ (object lists + remap)
      Learn    generic_learn save, generic_symbols seed, script_pairs, unit_ids (needs script\pairs_8.pkl)
               -> mask_table.pkl, symbols in idmap.json, script\pairs_*.pkl, unit_idmaps.json   (about 26 min)
      Tables   dlc_drms_build (our reconstruction), dlc_generic (provisional dlc_idmap.json, script_learn needs it),
               script_learn save, generic_type0 save07, script_name_match, tex_idmap (both rewrite idmap.json),
               dlc_generic again (final dlc_idmap.json on the final base id map)
      Prep     generic_type0 save07 (type 0/7 tables), pc_vers_build (our reconstruction), model_point_fix learn +
               selftest, dtpid_evidence (rule inputs of Convert's --extra-fixes, learned from base pairs only)
               -> type0_table.pkl, type7_table.pkl, pc_vers.json, pc_vers_content.json,
                  work\chain_aim\model_point_rules.pkl, work\generic\dtpid_evidence.pkl;
               aidata_fix learn (2026-11-13, P4.2: enemy AI record table from pairs.pkl + the base id map, seconds)
               -> work\generic\aidata_table.pkl (Convert / dlc_patch stop with exit 1 without it)
      Convert  dlc_convert_all --media --write --extra-fixes -> work\generic\out\pack10|pack11\*.drm
      Names    dlc_names (file names of unnamed DLC records) -> work\generic\dlc_names.txt (can run any time after Ids)
      Media    dlc_media_build (our reconstruction: DLC 1 tree in the B138 layout), locals build (with the text
               rules of the played tables: localised placeholders, unfilled slot from the costume packs, unwrapped
               DLC descriptions; gate tools\locals_text_gate.py), padshock build, compare_b138 -> work\rebuild\stage1\mods + work\rebuild\compare_stage1.json
      Audio    dlc_audio_build (our glue: wave_swap for all DRMs incl. sub folders, mul_audio_batch), compare_b138
               -> work\rebuild\stage2a\mods (replaced on every run) + compare_stage2a.json
      Assemble upstream's full stage-1 route (optional, after Media): render tables (render_tables_build build,
               rend_extract pairs/dlc, shader_map, material_rules, material_dlc, pc_shader_sections,
               terrain_validate, mesh_tables_build), dlc_assemble_build (assemble_dlc, material 'dlc', PC shader sections),
               dlc_audio_build, compare_b138, compare_sections
               -> work\render\*, work\rebuild\asm_stage1\mods, asm_stage2a\mods (+ compare_asm_stage2a.json)
      Dlc2     DLC 2 (pack11) stage 1 + 2a, after Assemble (needs its render tables): dlc_media_build pack11,
               dlc_assemble_build --pack pack11, dlc_audio_build --pack pack11, tree_check (no reference build)
               -> work\rebuild\dlc2_stage1\mods, dlc2_asm_stage1\mods, dlc2_asm_stage2a\mods (the input of Fixes)
      Fixes    stage 2b: dlc_fixes_build for DLC 1 (asm_stage2a -> asm_stage2b, compare_b138) and DLC 2
               (dlc2_asm_stage2a -> dlc2_asm_stage2b, --pack pack11); cloth / uipath / uitext were found in DLC 2,
               uipath / uitext also change 10 DLC 1 level files (since 2026-10-30); statechart (2026-10-31) re-converts
               the state charts of the new DLC objects (DLC 2 player chart: needs the title-update memory image);
               twins / childids / translist / actlist / condlist / eventlist / reclist / fadeslots / animfx / markup /
               vmliteral (2026-11-01/02) apply the structure layouts proven on the base pairs
               (tools/dlc_struct_fixes.py, tests 47 / 48 / 48c-48m; twins ~20 min);
               objtex / objrec / objid (2026-11-04, after markup, findings 47 / 48) set the object data DTP faults:
               texture group counts (F16 machine room), particle record byte classes (F3 / B24) and the player data
               breath-sound ids (doppelganger_casual 0x68f40000); dlc_struct_fixes check runs on each output tree
               (exit 1 on a word left, report <tree>\objdata_check.json);
               seqrepeat (2026-11-05, after objid, finding 49) sets the SoundPlex Sequence word +0xc (repeat byte +
               3 bytes) to the Xbox bytes (the converter u32-swapped repeat 1 to 0 = endless: DLC 2 doppelganger groan,
               DLC 1 dlc_caverns_hall / dlc_dungeonhallb); the step first proves the rule on the base pairs
               (soundplex_sequence_fix proof: exit 1 when a pair contradicts it or a count differs) and gates each
               output tree afterwards (soundplex_sequence_fix scan: exit 1 on a wrong or unexplained word, report
               <tree>\soundplex_sequence_check.json; dlc_struct_fixes check covers seqrepeat too);
               navraw (2026-11-05, docs Befund-Navmesh-Kombi-0511.md) copies the NavPower NavGraph image of every unit
               (Level+0x60) raw from the Xbox original, the count word after resource 1 u32-swapped (the converter
               u16-pair / u32-swapped words of the image: DLC 2 5187 words in 10 units, our DLC 1 1670 in 8); the rule
               is proven first (navgraph_raw_fix proof: 82 base pairs, exit 1 when a count differs), applied as step
               navraw of dlc_fixes_build (after seqrepeat; since 2026-11-06, before an in-place run after it) and gated
               afterwards (navgraph_raw_fix scan: exit 1 on a wrong, unexplained or unpaired word, report
               <tree>\navgraph_check.json; dlc_struct_fixes check covers navraw too). The costume packs hold no unit
               (no NavGraph): the step and the check leave them alone;
               chunkrec / exttuning / thrallext / meleelink / genintro / costumedtp / dspkind (2026-11-08, after objid,
               before seqrepeat; the data fixes of 2026-11-07) type, each by its proven rule, the chunkdoll piece
               records (chunkdoll_record_fix), the DLC 2 player tuning DTP 22497 targeter + K9 pair words
               (player_ext_tuning_fix), the thrall extension objects 870 / 932 / 944 (thrall_extension_fix), the melee
               records incl. the link-only combo records (melee_link_record_fix), the pool generator intro data
               (generator_intro_fix, DLC 1 too), the costume model u16 arrays / list counts (costume_dtp_fix) and the
               SoundPlex DSP kind of dlc_caverns_hall DTP 23469 (soundplex_dsp_kind_fix); the rules are proven first
               (chunkdoll_record_fix / melee_link_record_fix / generator_intro_fix / thrall_extension_fix proof,
               costume_dtp_fix prove: exit 1 on a contradicting base word) and each output tree is gated afterwards
               (the tools' scans: exit 1 on a wrong or unexplained word, reports <tree>\chunkdoll_check.json,
               melee_link_check.json, genintro_check.json, DLC 2 also exttuning_check.json / thrall_extension_check.json;
               dlc_struct_fixes check covers all seven steps); fadecard / uberanim / fxrec / sgmesh / introtyped /
               leveltwin / basecopy (2026-11-08, 17n, after dspkind: the typed families of the night 07./08.11.,
               tools/typed_family_fix.py) are proven first (typed_family_fix proof: exit 1 on a contradicting base word
               or another pinned count) and gated by dlc_struct_fixes check; uiinit (2026-11-09, tools/ui_init_fix.py:
               UI element init words of DLC scripts re-derived from the Xbox original by the byte order proven on
               generalbank Xbox <-> PC, applied in place after dlc_fixes_build, gated by ui_text_init_scan: exit 1 on
               a broken text anchor; report <tree>\..\uiinit_apply.json); DLC 2 additionally gets the doppelganger language
               variants (vo_lang_variants build: <stream>.mul_NNN of the 4 localised voice streams, 20 files, then
               vo_lang_variants check --expect <tree>\vo_lang_md5.tsv, report <tree>\vo_lang_check.json);
               objevent / idword / animlist / fxnode / statevm / chartid (2026-11-03, finding 44) set the converter
               fault families that crash dumps of tests 50d-50j uncovered (tools/converter_faults_fix.py: event list
               words and sub-0x32 ids, anim event list words, effect node headers / type-1 ids, state-VM code words,
               state-chart id values); the step first proves every rule on the base pair (converter_faults_fix proof)
               and checks each output tree afterwards (converter_faults_fix check: exit 1 on any wrong or unexpected
               word, report <tree>\converter_faults_check.json);
               achievement (2026-10-31) drops the 11 script calls into the title update's achievement natives
               f16-f20 that the PC exe lacks (1 in DLC 1, 10 in DLC 2);
               scriptclash (2026-11-04, last, finding 46) gives DLC script classes re-authored under the id of an
               always-resident PC generalbank script with another instance layout their own PC id (rule in
               tools/script_clash_fix.py, ids in docs/data/script_clash_ids.json: DLC 2 thrall base 12433 -> 26884,
               16 DRMs; DLC 1: nothing); script_clash_fix check runs on each output tree (exit 1 on a clash left,
               report <tree>\script_clash_check.json).
               P4 gates (2026-11-13, workspace docs Befund-P4s-Pipeline-1311.md): cine_call_gate check on the DLC 1
               tree (dlc_level1_start script 20068 +0x6c4 -> Cinematic_Object 3523 +0x2410 vtIndex 57 PlayCinematic,
               exit 1 on the retired CINE_SKIP form or a missing file, report <tree>\..\cine_call_check.json) and
               scan_aidata_tree check on both trees (exit 1 on any wrong 0x390-byte AI record id / count, report
               <tree>\..\aidata_check.json).
               P4.8 / P4.9 gates (2026-11-14, workspace docs Befund-P48-P49-Pipeline-1411.md): instref_gate proof + check
               on both trees (script init words userType 4261 = PC 4697 {u16 intro id, u16}: exit 1 when a reference to a
               DLC intro / marker does not name the PC id of that intro, report <tree>\..\instref_check.json) and
               map_mesh_fix proof + check (*_map.drm collision mesh: exit 1 on a mesh not found, a KD node outside its
               arrays or node bytes +0xc..+0xf other than the Xbox bytes, report <tree>\..\map_mesh_check.json).
               F1 gate (2026-11-14, workspace docs Befund-F1-Zellstreamlisten-1411.md): cellstream_fix proof + check on
               both trees (per-cell stream lists {u16 StreamUnitID, u16 streamgroup index} of the unit scenes: exit 1
               when a pair is not {map(Xbox unit), Xbox index} or its index + 1 is not below the record count of the
               named unit's streamgroup table - the pillory reload hang, report <tree>\..\cellstream_check.json).
               -FixesOut DIR (relative to the repository) writes DIR\dlc1\mods and DIR\dlc2\mods instead of
               work\rebuild\asm_stage2b and dlc2_asm_stage2b (check runs that must not replace the usual outputs)
      Shaders  (2026-11-11, plan A2 stage 1, after Fixes; minutes) the recorded shader decisions on the Fixes output:
               tools\shader_step.py apply reads docs\data\shader_step.tsv (made by shader_step.py plan from
               docs\data\shader_decisions.tsv) and the lib store work\shader_store (our recorded translations, not in
               the repository) + the Xbox DLC DRMs of tu_batch xdump (work\sg_audit_0511\xbox): recorded ShaderLibs
               (nativefix ABS_CONST rewrite with stack-independent entry hashes), material shader tuples + Xbox
               MaterialParams where the material's texture records are the ones the lib was built for (else refused);
               only the changed DRMs -> <out>\shaders\mods (a layer over dlc1 / dlc2); then (A2 stage 2)
               tools\shader_translate.py run: OUR pass-2 translation on the pipeline material (our records) for the
               materials the recorded decisions cannot serve (kit state K_MAT_*, the q17q 20265 one-off, rows apply
               refused): reuse of a recorded lib for the same Xbox lib whose binding check passes on every copy, else
               tu_batch build_group + pack_lib (new ids from 3600), VS rule (recorded VS for the same Xbox VS when the
               PC VS lacks an interpolator), lane rule (pass-0/1 lanes keep their value) -> <out>\shaders_tr\mods,
               compared with docs\data\shader_translate.tsv (--expect, exit 1 on any difference); then rule_owned apply
               (the ring rule last, <out>\shaders_rule\mods), rule_owned check over the stack, shader_form_gate
               (-ShaderGate) and tu_batch vcheck --strict (binding check of every translated pass-2 lib, exit 1 on a
               problem) on both shader layers; (P4a, 13.11.) shader_translate --scope-gaps also translates every
               pass-2 slot gap of the stack, and tools\shader_slot_gate.py check over the whole stack fails (exit 1)
               on a pass-2 permutation slot gap (class A exempt) and prints WARNING SURROGATE / SURR_ROLE for every
               copy that keeps a converter surrogate. <out> = -FixesOut DIR, else work\rebuild. tools\own_tree.py assemble
               takes shaders, shaders_tr and shaders_rule as layers
      Costumes the three Xbox costume packs (2026-11-03; pack1 Wetsuit k / p, pack2 Classic a / h, pack20 Designer
               l / m), after Assemble (render tables) and Fixes' proof: verify_ids extend (adds the packs' ids to
               dlc_idmap.json, existing entries never change; second run adds nothing), converter_faults_fix proof,
               soundplex_sequence_fix proof (2026-11-05), costume_dtp_fix prove (2026-11-08, rule of the step
               costumedtp: costumes a h k l m), then per pack the DLC 2 route: dlc_media_build,
               dlc_assemble_build --pack, dlc_audio_build --pack, tree_check, dlc_fixes_build --pack,
               converter_faults_fix check --pack, script_clash_fix check, dlc_struct_fixes check --pack (objtex / objrec
               / objid / seqrepeat), soundplex_sequence_fix scan --pack, costume_scope_check tree (E4: no
               dlc_costume_g / n DRM, no dlc_costumes4 unit / record, costume object ids 20..35 unchanged)
               -> work\rebuild\costumes\<pack>\{stage1,asm_stage1,asm_stage2a,stage2b}\mods (-FixesOut DIR: DIR\<pack>\...)
               Only the two dlc_costume_<x>.drm of each pack are new for the game; images, names and lists are in
               the DLC 1 tree already (docs/COSTUMES.md)
               Needs the render tables WITH the costume packs (Index since 2026-11-03, then Assemble's rend_extract dlc /
               shader_map (shaderlibs.pkl moved away first) / material_dlc / pc_shader_sections); otherwise assemble
               passes the packs' materials through as Xbox bytes (media_error). Proven 2026-11-03: the extended tables
               leave DLC 1 / DLC 2 assemble byte-identical (tools/render_tables_compare.py tables / tree).
               About 75-90 min per costume DRM: their DTPs are larger than every Xbox base record (no pc_copy /
               template, route 'convert'; tools/costume_pack_check.py xids)
      DoppelCostume  (2026-11-11, Q23, after Fixes / Shaders, seconds, no kit) the Doppelganger costume
               dlc_doppel_costume_a.drm (pack20 lists the object, no Xbox package has a DRM for it; until now only in
               the B270 kit): tools\doppel_costume_clone.py build takes OUR doppelganger_casual.drm from the top of
               the stack Fixes dlc2 -> shaders -> shaders_rule and applies the upstream author's recipe (measured on
               the B270 kit pair): object section (type 11) id 857 -> 1031 and the object's id word +0x14 the same
               (ids from the dlc2 tree's objectlist.txt), nothing else; the structural gate runs before anything is
               written; then doppel_costume_clone check re-derives the clone from the current source (exit 1 when
               stale or any other byte differs) -> work\rebuild\doppel\mods\dlc_doppel_costume_a.drm +
               doppel_costume_build.json / doppel_costume_check.json (-FixesOut DIR: DIR\doppel\...); tools\own_tree.py
               assemble takes it as layer doppel. Docs: Befund-Kostuem-Klon-Q23-1111.md
      Repair   the repair tree for an installed B138 (finding 43, tested in game 2026-10-30): b138_snapshot (pristine
               B138 mods, verified against the kit manifest, from the game folder and the Install-TruTree backups),
               generalbank_build (see Generalbank), b138_fix_tree (shader constant fix, grapple ring shaders, DLC 1 UI
               paths / texts, DLC 1 state charts, DLC 1 structure fixes (anim event lists of the costumes, pillar
               markup, since 2026-11-08 costumedtp / dspkind; step struct), the DLC 1 achievement call, cinematic
               languages of both DLCs, our generalbank.drm - since 2026-11-08 the K12 one, k12\mods\generalbank.drm);
               gates afterwards: rule_owned check (2026-11-11: the grapple ring rule's sections = PC base ring,
               rule_owned_check.json; the same tool guards install stacks: Install-TruTree -RuleGate, and puts the
               rule back on top of a stack whose shader re-translation replaced it: rule_owned apply, finding 52),
               input_map_tu_fix / globalinfo_player_list_fix --verify (player_list_check.json),
               vo_lang_variants check pack11 (doppelganger language variants, vo_lang_check.json), generator_intro_fix
               scan (genintro_check.json), dlc_struct_fixes check --steps costumedtp,dspkind (datafix_check.json)
               -> work\rebuild\b138_pristine\mods, work\rebuild\b138_fixes\mods (install with Install-TruTree.ps1)
      Generalbank  (default since 2026-11-11, Q2, seconds, no kit) tools\generalbank_pc_build.py build: needs the
               player's own Xbox title update TitleUpdate.000 (--tu, default
               ..\data\TombRaiderUnderworld_Patched\TitleUpdate.000; raw md5 of its generalbank checked) and no local
               knowledge file (since c883db5, knowledge K20261111-3: rules instead of the local residual bytes);
               the PC patch.000 generalbank (raw md5 checked) + recipe P3 (DLC text, menu_dlc_patch) + the sections
               docs\data\generalbank_pc.json describes as references to sections of the PC / TU files (md5) + word
               rules, no game data (13 sections: B138's TU edits DTP 36 / script 72, scripts 6 /
               9 / 104 / 21239 / 20082 + DTP 47 of the chain below, K12 DTP 2, shadow meter HUD scripts 37 / 213 +
               textures 7899 / 7036) + menu_ring_p14 build (ring tree 7: DLC on slot 7, QUIT on position 14; step
               file gated md5 = b8b1eb71..., the installed ring tree 7) + the TU doppelganger camera DTPs 21237 / 21238
               and their curve records 22194 appended (tools/tu_camera_dtp.py; md5 810711f1...); a guard refuses every
               kit / reference / game-mods path and every Xbox path except the TitleUpdate.000 given with --tu; then
               (2026-11-17, Q7 / Q10, default) tools\script_word_set.py sets the loading screen's start-list count
               (script 6 +0x11b20) from the PC's 182 to the title update's 193 in place (the ported TU entries 182-192
               were never constructed: black base loading backgrounds; docs Befund-Q7-Ladebild-1711.md); then
               (2026-11-17, Q5; default since 2026-11-19, T1, after the live test of 2026-11-17; -NoDlcPanel leaves it
               out) tools\dlc_screen_panel.py build adds the title
               update's dark translucent panel (uibitmap member of TU script 134) to mission screen script 104 in place
               (docs\DLC_MENU.md "The panel behind the screen"; other section than the count word, the order of the
               two does not change the result); then the gates script_sfi_members --scan (no script with entries after
               its start-list count), script_count_gate (T1: count words of the TU-layout scripts = the TU's, three
               known code counts of script 6 allowed), menu_ring_layout --expect-p14, menu_quit_slot_check --expect f15,
               input_map_tu_fix --verify
               -> work\rebuild\generalbank_pc\mods\generalbank.drm + build_report.json (-FixesOut DIR:
               DIR\generalbank_pc). Docs: Befund-Generalbank-PC-Basis-1111.md. Not installed by anything yet.
               md5 of the result: 53f43332... (default since T1 = the installed file), 219aad62... (-NoDlcPanel);
               before Q10 810711f1...
               -GeneralbankKit = the old chain (developer; the source of the knowledge):
               our generalbank.drm alone (after Repair's snapshot): B138's + mission screen style + the title
               update's loading screen (script 6, DLC titles) and hint box (script 10 -> 9), 21 steps with the
               existing tools, two of them load the generic store (~16 GB RAM, one after the other); step 21 is
               compared with the played test 38 file (MD5); step 22 (2026-11-04) appends the title update's 6 input
               bindings of Lara's set 17 (tools/input_map_tu_fix.py: RB / X / Y / LB for the DLC 2 shadow combat)
               -> work\rebuild\generalbank_build\mods\generalbank.drm; input_map_tu_fix --verify checks the result
               (also in Repair, on b138_fixes), report <dir>\input_map_check.json; step 23 (2026-11-05, S104):
               mission screen script 104 starts DLC 2 like the title update, without costume / weapon selection
               (tools/dlc2_player_fix.py gb; result = dlc_test50l_input, md5 66efd71d...), gate
               dlc2_player_fix verify (every changed word explained), report <dir>\script104_check.json; K12
               (2026-11-08): globalinfo_player_list_fix appends 857 doppelganger_casual to the DTP 2 player list as the
               title update (28 -> 29 ids) -> <dir>\k12\mods\generalbank.drm (the file to install; mods\ stays the S104
               result), gates globalinfo_player_list_fix --verify (player_list_check.json) and input_map_tu_fix --verify
               -FixesOut DIR (2026-11-04, check runs): Generalbank writes DIR\generalbank_build; Repair writes
               DIR\b138_pristine\mods, DIR\generalbank_build (--base = that snapshot's generalbank.drm) and
               DIR\b138_fixes\mods instead of the usual work\rebuild\b138_pristine / generalbank_build / b138_fixes
      Exe      (2026-11-10, independent of every other step, seconds) our patched tru.exe instead of the kit's:
               tools\exe_build.py reads the Steamless-unpacked Steam exe (md5 56d1ce2d..., Install-TruAll step 8:
               ..\data\pc\tru.exe.unpacked.exe / tru.exe.steam_original.unpacked.exe / tru.exe.steamless_original, else
               work\b270_kit\exe\tru_steam_unpacked_realign.exe; the game folder is only read), sets the LAA bit, applies
               fmod_init_guard / light_tex_guard (+ .text writable) / soundplex_guard / combat_lock_guard (the fourth
               B138 guard, lock-on target at 0x71e710), checks the section headers and gates md5 = 5560abac... (the
               B138 exe); nothing is written when a stage or the gate fails. Then exe_build --check lists every stage
               of the result (exit 1 unless complete) -> work\rebuild\exe\tru.exe + exe_build.json, exe_check.json
               (-FixesOut DIR: DIR\exe\...). Not installed by anything yet
      Globalsound  (2026-11-10, independent of every other step, seconds) our globalsoundinfo.drm instead of the
               kit's: tools\globalsoundinfo_build.py takes the PC original (bigfile.000; its md5 is checked) and applies
               the recorded title-update edit docs\data\globalsoundinfo_tu.json (sound DTP 792: groups 77-79 for DLC 2,
               pause list + 79, two runtime areas, 88 bytes of TU values); gate = raw DRM md5 94a70736... (the B138 /
               B270 kit file; the CDRM bytes differ only by the zlib build), nothing is written when it fails; then
               --check re-reads the written file -> work\rebuild\globalsound\mods\globalsoundinfo.drm +
               globalsound_check.json (-FixesOut DIR: DIR\globalsound\...). Kit bytes on purpose: the two new u16 DSP
               kinds (entry +0x7c of groups 77 / 78) stay u32-swapped as in the kit until the owner decides
               (--tu-form, docs/WINDOWS_REBUILD.md finding 51). Not installed by anything yet
      Lang     (2026-11-11, R10, independent of every other step except Names; ~47 min with 3 processes) the language
               variants <name>.mul_NNN of the DLC cinematics (pdlc1_010 / 030, pdlc2_020 / 030 / 040 / 045 / 050) and
               the 5 DLC 1 radio lines from the Xbox packs: tools\lang_variants_step.py build = tools\mul_lang_build.py
               --variants-only (one process per cinematic + one for the voice lines, at most 3), 60 files: 001 EN,
               002 FR, 004 DE, 008 IT, 016 ES; no .mul_2048 (Dutch: no Dutch speech exists, the plain English name is
               the fallback) and no .mul_032 (the Japanese slot); then lang_variants_step check = gate: exactly these
               60 files, each md5 = docs\data\lang_variants_md5.tsv (the installed variants)
               -> work\rebuild\lang\mods + lang_md5.tsv, lang_check.json (-FixesOut DIR: DIR\lang\...).
               The DLC 2 doppelganger variants stay in Fixes (vo_lang_variants). Not installed by anything yet

    Aborting: a step can be stopped between tools without loss (each tool writes its output when it finishes);
    a tool stopped midway has to run again. -FromTool N resumes a step at its N-th tool (numbers as shown in the
    progress bar, "tool N/M"); -ToTool N (2026-11-08) stops after the N-th tool, so a long step can be split
    (e.g. Repair -ToTool 5 = snapshot + generalbank + K12, later -FromTool 6 = b138_fix_tree + checks).

    Progress: a progress bar (Write-Progress) shows the running tool and its time; steps with a known number of
    output files (Convert: 300 DRM files) also show percent and an estimate. Every 30 s a "still running" line is
    written to the console and the log.

    Processes: the heavy converters (dlc_convert_all, ~18 GB RAM each) run -Jobs processes, the light tools
    (audio, comparisons) -LightJobs. 0 = automatic: Jobs = (free RAM - 8 GB) / 18 GB, between 1 and 3;
    LightJobs = logical CPUs - 4, at most 24 (cores left for other work). Passed as TRUDLC_JOBS / TRUDLC_JOBS_LIGHT.

    -ShaderGate (2026-11-08): steps Fixes and Repair run tools\shader_form_gate.py on each output tree (ABS_CONST,
    SINCOS_SAME, X5584, ERR in port shaders; report <tree>\shader_form_check.json). Report (default for now) only
    lists them, Enforce makes a hard form fail the step (exit 1).

    -PlayerMode (2026-11-11, plan Spielerweg P0 / gate G2): player-path access guard, rules in
    docs\data\playerpath_guard.json. Off (default) = developer path, unchanged; a TRU_PLAYER_MODE / TRU_PLAYER_LOG
    left in the calling shell is ignored for the run. Report = every tool runs through tools\player_guard.py run
    with TRU_PLAYER_MODE=report: every open / listing / process start of an Xbox base-game path (layer1 / layer2,
    default.xex, the game folder except TitleUpdate.000 with its md5) or of developer data made from it (pairs.pkl,
    store.pkl, idx_xbox_base.json, script \ render \ cine pairs, Xenia images) is logged, nothing refused.
    Enforce (= -Player) = such accesses are refused (PermissionError in the tool, exit 2 -> the step fails); tool
    arguments naming such a path are refused before the tool starts (Assert-TruPlayerToolArgs). Access log:
    <workspace>\logs\player_guard_<step>_<time>.tsv, counts per tool in the run log and in <log>.json.
    P0 switches only the guard; the step lists stay the developer ones (the knowledge-based steps follow in P1 ...).

    -Verbose shows steps, -Debug the command lines, -Trace adds a PowerShell line trace.

.EXAMPLE
    .\Invoke-TruPipeline.ps1 -Step Globalsound -PlayerMode Report -FixesOut work/rebuild/q14_p0_1111 -Verbose
.EXAMPLE
    .\Invoke-TruPipeline.ps1 -Step Cache -Verbose
.EXAMPLE
    .\Invoke-TruPipeline.ps1 -Step Tables -FromTool 5 -Verbose
.EXAMPLE
    .\Invoke-TruPipeline.ps1 -Step Fixes -FixesOut work/rebuild/pipeline_check_0311 -Verbose
.EXAMPLE
    .\Invoke-TruPipeline.ps1 -Step Costumes -FixesOut work/rebuild/costumes_0311 -Jobs 1 -Verbose
.EXAMPLE
    .\Invoke-TruPipeline.ps1 -Step Exe -Verbose
.EXAMPLE
    .\Invoke-TruPipeline.ps1 -Step DoppelCostume -FixesOut work/rebuild/pipeline_check_1111b -Verbose
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('Index', 'Cache', 'Ids', 'Learn', 'Tables', 'Prep', 'Convert', 'Names', 'Media', 'Audio', 'Assemble', 'Dlc2', 'Fixes', 'Shaders', 'Costumes', 'DoppelCostume', 'Repair', 'Generalbank', 'Exe', 'Globalsound', 'Lang')][string]$Step,
    [ValidateRange(1, 99)][int]$FromTool = 1,
    [ValidateRange(1, 99)][int]$ToTool = 99,
    [ValidateRange(0, 16)][int]$Jobs = 0,
    [ValidateRange(0, 64)][int]$LightJobs = 0,
    # steps Fixes / Costumes / Generalbank / Repair: output folder below the repository instead of work/rebuild/asm_stage2b + dlc2_asm_stage2b
    # (Costumes: work/rebuild/costumes; Generalbank / Repair: work/rebuild/generalbank_build, b138_pristine, b138_fixes)
    # (one folder directly below work/rebuild; never a test tree dlc_test*)
    [ValidatePattern('^work[\\/]rebuild[\\/](?!dlc_test)[\w\-\.]+[\\/]?$')][string]$FixesOut,
    [ValidateSet('Report', 'Enforce')][string]$ShaderGate = 'Report',
    # step Generalbank: the old chain on B138's generalbank (+ two generic-store converter runs) instead of the PC build
    [switch]$GeneralbankKit,
    # step Generalbank: leave out the title update's dark panel behind the DLC mission screen (tools\dlc_screen_panel.py,
    # Q5; added by default since 2026-11-19, T1)
    [switch]$NoDlcPanel,
    # obsolete since 2026-11-19 (T1): the panel is the default; kept so older command lines still run (no effect)
    [switch]$DlcPanel,
    # player-path access guard (plan Spielerweg P0): Off / Report (log only) / Enforce; -Player = Enforce
    [ValidateSet('Off', 'Report', 'Enforce')][string]$PlayerMode = 'Off',
    [switch]$Player,
    [switch]$Trace
)
if ($Player) {
    if ($PSBoundParameters.ContainsKey('PlayerMode') -and $PlayerMode -ne 'Enforce') { throw '-Player means -PlayerMode Enforce; do not combine it with another -PlayerMode.' }
    $PlayerMode = 'Enforce'
}

$ErrorActionPreference = 'Stop'
if ($PSBoundParameters.ContainsKey('Debug')) { $DebugPreference = 'Continue' }
# shared helpers: Write-Log, Set-TruLogFile, Get-TruWorkspacePath, ...
Import-Module (Join-Path $PSScriptRoot 'TruCommon.psm1') -Force -Verbose:$false

# <workspace> = the folder that holds the repository (see Get-TruWorkspacePath)
$paths  = Get-TruWorkspacePath -ScriptRoot $PSScriptRoot
$root   = $paths.Workspace
$clone  = $paths.Repository
$python = Join-Path $root 'bin\venv\Scripts\python.exe'
$logDir = $paths.Logs

$align = '@7ff00000'          # bigfile part size (tools/archive.py ALIGN)
$dlc   = '../data/Xenia-SteveRepack/Content/534307EC/00000002'
# outputs of step Fixes (-FixesOut: a separate check folder, the usual trees stay untouched)
if ($FixesOut) {
    $fixRoot = ($FixesOut -replace '\\', '/').TrimEnd('/')
    $fix1 = "$fixRoot/dlc1/mods"; $fix2 = "$fixRoot/dlc2/mods"
    $fixLabel = Split-Path -Leaf $fixRoot
    $cmp1 = "${fixLabel}_dlc1"
} else {
    $fix1 = 'work/rebuild/asm_stage2b/mods'; $fix2 = 'work/rebuild/dlc2_asm_stage2b/mods'
    $cmp1 = 'asm_stage2b'
}
$chk1 = (Split-Path -Parent $fix1) + '/converter_faults_check.json'
$chk2 = (Split-Path -Parent $fix2) + '/converter_faults_check.json'
$clash1 = (Split-Path -Parent $fix1) + '/script_clash_check.json'
$clash2 = (Split-Path -Parent $fix2) + '/script_clash_check.json'
$obj1 = (Split-Path -Parent $fix1) + '/objdata_check.json'
$obj2 = (Split-Path -Parent $fix2) + '/objdata_check.json'
$seq1 = (Split-Path -Parent $fix1) + '/soundplex_sequence_check.json'
$seq2 = (Split-Path -Parent $fix2) + '/soundplex_sequence_check.json'
$nav1 = (Split-Path -Parent $fix1) + '/navgraph_check.json'
$nav2 = (Split-Path -Parent $fix2) + '/navgraph_check.json'
# gates of the 2026-11-07 data fixes (steps since 2026-11-08)
$chunk1 = (Split-Path -Parent $fix1) + '/chunkdoll_check.json'
$chunk2 = (Split-Path -Parent $fix2) + '/chunkdoll_check.json'
$melee1 = (Split-Path -Parent $fix1) + '/melee_link_check.json'
$melee2 = (Split-Path -Parent $fix2) + '/melee_link_check.json'
$gen1 = (Split-Path -Parent $fix1) + '/genintro_check.json'
$gen2 = (Split-Path -Parent $fix2) + '/genintro_check.json'
$ext2 = (Split-Path -Parent $fix2) + '/exttuning_check.json'
$thrall2 = (Split-Path -Parent $fix2) + '/thrall_extension_check.json'
$sg1 = (Split-Path -Parent $fix1) + '/shader_form_check.json'
$sg2 = (Split-Path -Parent $fix2) + '/shader_form_check.json'
$sgEnforce = if ($ShaderGate -eq 'Enforce') { @('--enforce') } else { @() }
$voMd5 = (Split-Path -Parent $fix2) + '/vo_lang_md5.tsv'
$vo2 = (Split-Path -Parent $fix2) + '/vo_lang_check.json'
$gbOut = 'work/rebuild/generalbank_build'
$repPristine = 'work/rebuild/b138_pristine/mods'
$repFixes = 'work/rebuild/b138_fixes/mods'
$gbBase = @()
if ($FixesOut) {
    # steps Generalbank / Repair as check runs: every output below -FixesOut, the usual trees stay untouched
    $gbOut = "$fixRoot/generalbank_build"
    $repPristine = "$fixRoot/b138_pristine/mods"
    $repFixes = "$fixRoot/b138_fixes/mods"
    # Repair: generalbank_build reads its base from this run's own snapshot (its default is work/rebuild/b138_pristine)
    if ($Step -eq 'Repair') { $gbBase = @('--base', "$repPristine/generalbank.drm") }
}
# step Exe (2026-11-10): our B138 tru.exe from the Steamless-unpacked Steam exe
$exeOut = if ($FixesOut) { "$fixRoot/exe" } else { 'work/rebuild/exe' }
# step Generalbank (2026-11-11): our generalbank.drm from the PC patch.000 original + recorded knowledge + ring P14
$gbPcOut = if ($FixesOut) { "$fixRoot/generalbank_pc" } else { 'work/rebuild/generalbank_pc' }
# DLC panel (2026-11-17, Q5): the title update's dark panel behind the DLC mission screen, added in place to the
# Generalbank result (tools\dlc_screen_panel.py; default since 2026-11-19, T1, after the live test of 2026-11-17,
# -NoDlcPanel leaves it out); runs after the default script 6 count fix and before the gates (Q10: both orders give
# the same file, only script 104 + one word of script 6 change)
$gbPanel = @()
if (!$NoDlcPanel) { $gbPanel = ,@('tools\dlc_screen_panel.py', 'build', "$gbPcOut/mods/generalbank.drm", "$gbPcOut/mods/generalbank.drm") }
# step Globalsound (2026-11-10): our globalsoundinfo.drm from the PC original + the recorded title-update edit
$gsOut = if ($FixesOut) { "$fixRoot/globalsound" } else { 'work/rebuild/globalsound' }
# step Lang (2026-11-11, R10): the 60 language variants of the DLC cinematics / DLC 1 radio lines
$langOut = if ($FixesOut) { "$fixRoot/lang" } else { 'work/rebuild/lang' }
# step Shaders (2026-11-11, A2 stage 1): recorded shader decisions as a layer over the Fixes trees, ring rule last
$shOut = if ($FixesOut) { "$fixRoot/shaders" } else { 'work/rebuild/shaders' }
$shRule = if ($FixesOut) { "$fixRoot/shaders_rule" } else { 'work/rebuild/shaders_rule' }
# A2 stage 2 (2026-11-11): our own pass-2 translations on the pipeline materials (kit / one-off / refused rows)
$shTr = if ($FixesOut) { "$fixRoot/shaders_tr" } else { 'work/rebuild/shaders_tr' }
# step DoppelCostume (2026-11-11, Q23): dlc_doppel_costume_a.drm cloned from the top-most doppelganger_casual.drm
$dpOut = if ($FixesOut) { "$fixRoot/doppel" } else { 'work/rebuild/doppel' }
$dpStack = @('--stack', $fix2, "$shOut/mods", "$shTr/mods", "$shRule/mods")
# step Costumes: one chain per costume pack (the DLC 2 route), below work/rebuild/costumes or -FixesOut
$costRoot = if ($FixesOut) { $fixRoot } else { 'work/rebuild/costumes' }
$costumeTools = @(
    @('tools\costume_scope_check.py', 'selftest'),
    @('tools\verify_ids.py', 'extend'),
    @('tools\converter_faults_fix.py', 'proof'),
    @('tools\soundplex_sequence_fix.py', 'proof'),
    # rule MESH16 / LISTCOUNT of step costumedtp (2026-11-08): base Lara model DTPs, exit 1 on any exception
    @('tools\costume_dtp_fix.py', 'prove')
)
foreach ($pk in 'pack1', 'pack2', 'pack20') {
    $o = "$costRoot/$pk"
    $costumeTools += , @('tools\dlc_media_build.py', "$o/stage1/mods", $pk)
    $costumeTools += , @('tools\dlc_assemble_build.py', "$o/stage1/mods", "$o/asm_stage1/mods", '--pack', $pk)
    $costumeTools += , @('tools\dlc_audio_build.py', "$o/asm_stage1/mods", "$o/asm_stage2a/mods", '--pack', $pk)
    $costumeTools += , @('tools\tree_check.py', "$o/asm_stage2a/mods", ('{0}_{1}' -f (Split-Path -Leaf $costRoot), $pk))
    $costumeTools += , @('tools\dlc_fixes_build.py', "$o/asm_stage2a/mods", "$o/stage2b/mods", '--pack', $pk)
    $costumeTools += , @('tools\converter_faults_fix.py', 'check', "$o/stage2b/mods", '--pack', $pk, '--report', "$o/converter_faults_check.json")
    $costumeTools += , @('tools\script_clash_fix.py', 'check', "$o/stage2b/mods", '--report', "$o/script_clash_check.json")
    $costumeTools += , @('tools\dlc_struct_fixes.py', 'check', "$o/stage2b/mods", '--pack', $pk, '--report', "$o/objdata_check.json")
    $costumeTools += , @('tools\soundplex_sequence_fix.py', 'scan', "$o/stage2b/mods", '--pack', $pk, '--report', "$o/soundplex_sequence_check.json")
    # E4 (2026-11-05, docs Befund-E4-E12-0511.md): no dlc_costume_g / n DRM, no dlc_costumes4 unit, costume ids unchanged
    $costumeTools += , @('tools\costume_scope_check.py', 'tree', "$o/stage2b/mods", '--report', "$o/costume_scope_check.json")
}
$steps = @{
    Index = @(
        @('tools\index_all.py', 'work/idx_pc.json', 'le', "../data/pc/bigfile.000$align", "../data/pc/patch.000$align"),
        @('tools\index_all.py', 'work/idx_xbox_base.json', 'be', "../data/TombRaiderUnderworld_Patched/layer1.000$align",
          "../data/TombRaiderUnderworld_Patched/layer2.000$align", "../data/TombRaiderUnderworld_Patched/TitleUpdate.000$align"),
        # costume packs last (2026-11-03): the first record of a section id wins in the render tables, so pack10 / pack11
        # keep every entry they had (tools/render_tables_compare.py index / tables)
        @('tools\index_all.py', 'work/idx_dlc.json', 'be', "$dlc/9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000$align",
          "$dlc/600A12643FCDAC84003E6E0DBD0A1A8F7DAE9DD153/pack11.000$align",
          "$dlc/E5AFB2B959A72C52120D73678AED11BD8752686753/pack1.000$align",
          "$dlc/9FDDD06617D1016DE468ACF53AC663E8BA2AD41853/pack2.000$align",
          "$dlc/AC0089F81B621CD0E0C156B6176EFCC6C844705D53/pack20.000$align")
    )
    Cache = @(
        @('tools\generic_cache.py'),
        @('tools\generic_cache.py', 'patch')
    )
    Ids = @(
        @('tools\generic_store.py'),
        @('tools\generic_ids.py'),
        @('tools\objlists_extract.py'),
        @('tools\objlist_merge.py')
    )
    Learn = @(
        @('tools\generic_learn.py', 'save'),
        @('tools\generic_symbols.py', 'seed'),
        @('tools\script_pairs.py'),
        @('tools\unit_ids.py')
    )
    Tables = @(
        @('tools\dlc_drms_build.py'),
        @('tools\dlc_generic.py'),
        @('tools\script_learn.py', 'save'),
        @('tools\generic_type0.py', 'save07'),
        @('tools\script_name_match.py'),
        @('tools\tex_idmap.py'),
        @('tools\dlc_generic.py')
    )
    Prep = @(
        @('tools\generic_type0.py', 'save07'),
        @('tools\pc_vers_build.py'),
        @('tools\model_point_fix.py', 'learn'),
        @('tools\model_point_fix.py', 'selftest'),
        @('tools\dtpid_evidence.py'),
        # P4.2 (2026-11-13): the enemy AI record table (gitignored); without it aidata_fix stops the converter (exit 1)
        @('tools\aidata_fix.py', 'learn')
    )
    # leading comma: a step with a single tool must stay a list of argument lists (PowerShell unrolls @(@(...)))
    Convert = @(
        , @('tools\dlc_convert_all.py', '--media', '--write', '--extra-fixes')
    )
    Names = @(
        , @('tools\dlc_names.py')
    )
    Media = @(
        @('tools\dlc_media_build.py', 'work/rebuild/stage1/mods', 'pack10'),
        @('tools\locals.py', 'build', 'work/rebuild/stage1'),
        @('tools\padshock_convert.py', 'build', 'work/rebuild/stage1/mods'),
        @('tools\compare_b138.py', 'work/rebuild/stage1/mods', 'stage1'),
        @('tools\compare_sections.py', 'work/rebuild/stage1/mods', 'stage1')
    )
    Audio = @(
        @('tools\dlc_audio_build.py', 'work/rebuild/stage1/mods', 'work/rebuild/stage2a/mods'),
        @('tools\compare_b138.py', 'work/rebuild/stage2a/mods', 'stage2a'),
        @('tools\compare_sections.py', 'work/rebuild/stage2a/mods', 'stage2a')
    )
    Assemble = @(
        @('tools\render_tables_build.py', 'build'),
        @('tools\rend_extract.py', 'pairs'),
        @('tools\render_tables_build.py', 'check'),
        @('tools\rend_extract.py', 'dlc'),
        # shader_map reads work\render\shaderlibs.pkl as a cache when it exists: after a new rend_extract (pairs / dlc)
        # move that file away first, else the libraries / materials of the new index are missing from all DLC tables
        @('tools\shader_map.py'),
        @('tools\material_rules.py'),
        @('tools\material_dlc.py'),
        @('tools\pc_shader_sections.py'),
        @('tools\terrain_validate.py'),
        @('tools\mesh_tables_build.py'),
        @('tools\dlc_assemble_build.py', 'work/rebuild/stage1/mods', 'work/rebuild/asm_stage1/mods'),
        @('tools\dlc_audio_build.py', 'work/rebuild/asm_stage1/mods', 'work/rebuild/asm_stage2a/mods'),
        @('tools\compare_b138.py', 'work/rebuild/asm_stage2a/mods', 'asm_stage2a'),
        @('tools\compare_sections.py', 'work/rebuild/asm_stage2a/mods', 'asm_stage2a')
    )
    Dlc2 = @(
        @('tools\dlc_media_build.py', 'work/rebuild/dlc2_stage1/mods', 'pack11'),
        @('tools\dlc_assemble_build.py', 'work/rebuild/dlc2_stage1/mods', 'work/rebuild/dlc2_asm_stage1/mods', '--pack', 'pack11'),
        @('tools\dlc_audio_build.py', 'work/rebuild/dlc2_asm_stage1/mods', 'work/rebuild/dlc2_asm_stage2a/mods', '--pack', 'pack11'),
        @('tools\tree_check.py', 'work/rebuild/dlc2_asm_stage2a/mods', 'dlc2_asm_stage2a')
    )
    Fixes = @(
        @('tools\converter_faults_fix.py', 'proof'),
        @('tools\soundplex_sequence_fix.py', 'proof'),
        @('tools\navgraph_raw_fix.py', 'proof'),
        # 2026-11-08: the rules of the data fix steps chunkrec / meleelink / genintro / thrallext / costumedtp, proven on
        # the base / retail pairs first (exit 1 on a contradicting word or another count than pinned)
        @('tools\chunkdoll_record_fix.py', 'proof'),
        @('tools\melee_link_record_fix.py', 'proof'),
        @('tools\generator_intro_fix.py', 'proof'),
        @('tools\thrall_extension_fix.py', 'proof'),
        @('tools\costume_dtp_fix.py', 'prove'),
        # 2026-11-08 (17n): the seven typed-family rules (fadecard / uberanim / fxrec / sgmesh / introtyped / leveltwin /
        # basecopy) on the base pairs (exit 1 on a contradicting word or another count than pinned)
        @('tools\typed_family_fix.py', 'proof'),
        # 2026-11-09 uiinit: byte order of UI element init words (userTypes 301 / 303 / 316 / 320) proven on generalbank
        # Xbox <-> PC (exit 1 on a contradiction or another count than pinned)
        @('tools\ui_init_fix.py', 'proof'),
        # 2026-11-11 (Q58): the twin Symbol entries the converter reads (docs/data/symbol_twins.json) re-derive from the
        # base pairs (exit 1 when they differ or a twin vote disagrees with the learned base map)
        @('tools\symbol_twins.py', 'check'),
        # 2026-11-10 K-5b playerblock: byte order of the player data block (DTP +0xc8, PC [0xfad764]) on five base
        # player pairs, leave-one-out (exit 1 on a contradicting word or a READERS order the pairs do not allow)
        @('tools\player_block_fix.py', 'proof'),
        # 2026-11-12 (Q110) objfield: u16 object ids of the unit default gear lists and the chunkdoll data D+8 = PC id
        # of the Xbox object name on every base pair (exit 1 on a contradicting field or another count than pinned)
        @('tools\object_id_field_fix.py', 'proof'),
        # 2026-11-14 (P4.8 / P4.9): the converter rules for script intro / marker references (userType 4261 -> 4697)
        # and the *_map.drm collision meshes, proven on the base pairs (exit 1 on a contradicting word or another count)
        @('tools\instref_gate.py', 'proof'),
        @('tools\map_mesh_fix.py', 'proof'),
        # 2026-11-14 (F1): the converter rule for the per-cell stream lists (every pair through the unit id map),
        # proven on the base unit pairs (exit 1 on a contradicting pair, an index out of range or another count)
        @('tools\cellstream_fix.py', 'proof'),
        @('tools\dlc_fixes_build.py', 'work/rebuild/asm_stage2a/mods', $fix1),
        # uiinit on the DLC 1 tree in place (planned words only, every write re-read), then the text-anchor gate
        @('tools\ui_init_fix.py', 'apply', $fix1, '--report', ((Split-Path -Parent $fix1) + '/uiinit_apply.json')),
        @('tools\ui_text_init_scan.py', $fix1),
        @('tools\converter_faults_fix.py', 'check', $fix1, '--report', $chk1),
        @('tools\script_clash_fix.py', 'check', $fix1, '--report', $clash1),
        # 2026-11-11 (Q58): Symbol paths in script init data resolve on PC to the member / function the Xbox path names
        # (exit 1 on a wrong or unresolved element; the converter writes them as two Symbols since Q58)
        @('tools\script_path_check.py', 'scan', $fix1, '--report', ((Split-Path -Parent $fix1) + '/script_path_check.json')),
        @('tools\dlc_struct_fixes.py', 'check', $fix1, '--report', $obj1),
        # DLC 1 = pack10 first, the same Xbox sources as dlc_fixes_build without --pack
        @('tools\soundplex_sequence_fix.py', 'scan', $fix1, '--pack', 'pack10', '--report', $seq1),
        @('tools\navgraph_raw_fix.py', 'scan', $fix1, '--pack', 'pack10', '--report', $nav1),
        # data fix gates (2026-11-08; costumedtp / dspkind are gated by dlc_struct_fixes check above)
        @('tools\chunkdoll_record_fix.py', 'scan', $fix1, '--pack', 'pack10', '--report', $chunk1),
        @('tools\melee_link_record_fix.py', 'scan', $fix1, '--pack', 'pack10', '--report', $melee1),
        @('tools\generator_intro_fix.py', 'scan', $fix1, '--pack', 'pack10', '--report', $gen1),
        # P4 gates (2026-11-13): DLC 1 start calls PlayCinematic (no retired CINE_SKIP), no wrong enemy AI record
        @('tools\cine_call_gate.py', 'check', $fix1, '--report', ((Split-Path -Parent $fix1) + '/cine_call_check.json')),
        @('tools\scan_aidata_tree.py', 'check', $fix1, '--pack', 'pack10', '--report', ((Split-Path -Parent $fix1) + '/aidata_check.json')),
        # P4.8 / P4.9 gates (2026-11-14): every script reference to a DLC intro / marker names the PC id of that intro
        # (dungeon water markers, Q124); every *_map.drm collision mesh has the Xbox KD node bytes (PDA sonar hang)
        @('tools\instref_gate.py', 'check', $fix1, '--pack', 'pack10', '--expect-refs', '--report', ((Split-Path -Parent $fix1) + '/instref_check.json')),
        @('tools\map_mesh_fix.py', 'check', $fix1, '--pack', 'pack10', '--report', ((Split-Path -Parent $fix1) + '/map_mesh_check.json')),
        # F1 gate (2026-11-14): every cell stream pair = {map(Xbox unit), Xbox index}, index inside the named unit's
        # streamgroup table (pillory reload hang: (101,1) = one record past the end of dlc_water_wheel)
        @('tools\cellstream_fix.py', 'check', $fix1, '--pack', 'pack10', '--report', ((Split-Path -Parent $fix1) + '/cellstream_check.json')),
        # shader form gate (2026-11-08): the forms Windows' D3D9 or a GPU driver refuses (-ShaderGate)
        (@('tools\shader_form_gate.py', 'check', $fix1, '--list', '3', '--report', $sg1) + $sgEnforce),
        @('tools\compare_b138.py', $fix1, $cmp1),
        @('tools\dlc_fixes_build.py', 'work/rebuild/dlc2_asm_stage2a/mods', $fix2, '--pack', 'pack11'),
        # uiinit on the DLC 2 tree (objective / hint notifier banners), then the text-anchor gate
        @('tools\ui_init_fix.py', 'apply', $fix2, '--pack', 'pack11', '--report', ((Split-Path -Parent $fix2) + '/uiinit_apply.json')),
        @('tools\ui_text_init_scan.py', $fix2),
        # doppelganger language variants (2026-11-08, no DRM step): <stream>.mul_NNN of the 4 localised DLC 2 voice
        # streams (20 files + the plain English names), vo_lang_md5.tsv next to the mods folder
        @('tools\vo_lang_variants.py', 'build', $fix2, 'pack11'),
        @('tools\converter_faults_fix.py', 'check', $fix2, '--pack', 'pack11', '--report', $chk2),
        @('tools\script_clash_fix.py', 'check', $fix2, '--report', $clash2),
        @('tools\script_path_check.py', 'scan', $fix2, '--pack', 'pack11', '--report', ((Split-Path -Parent $fix2) + '/script_path_check.json')),
        @('tools\dlc_struct_fixes.py', 'check', $fix2, '--pack', 'pack11', '--report', $obj2),
        @('tools\soundplex_sequence_fix.py', 'scan', $fix2, '--pack', 'pack11', '--report', $seq2),
        @('tools\navgraph_raw_fix.py', 'scan', $fix2, '--pack', 'pack11', '--report', $nav2),
        @('tools\chunkdoll_record_fix.py', 'scan', $fix2, '--pack', 'pack11', '--report', $chunk2),
        @('tools\player_ext_tuning_fix.py', 'scan', $fix2, '--pack', 'pack11', '--report', $ext2),
        @('tools\thrall_extension_fix.py', 'scan', $fix2, '--pack', 'pack11', '--report', $thrall2),
        @('tools\melee_link_record_fix.py', 'scan', $fix2, '--pack', 'pack11', '--report', $melee2),
        @('tools\generator_intro_fix.py', 'scan', $fix2, '--pack', 'pack11', '--report', $gen2),
        @('tools\scan_aidata_tree.py', 'check', $fix2, '--pack', 'pack11', '--report', ((Split-Path -Parent $fix2) + '/aidata_check.json')),
        @('tools\instref_gate.py', 'check', $fix2, '--pack', 'pack11', '--expect-refs', '--report', ((Split-Path -Parent $fix2) + '/instref_check.json')),
        @('tools\map_mesh_fix.py', 'check', $fix2, '--pack', 'pack11', '--report', ((Split-Path -Parent $fix2) + '/map_mesh_check.json')),
        @('tools\cellstream_fix.py', 'check', $fix2, '--pack', 'pack11', '--report', ((Split-Path -Parent $fix2) + '/cellstream_check.json')),
        # 2026-11-09: the end-level words the 0813 tree had wrong vs the installed tree (Level twin s32, unit root block
        # twin, uber TRANS +0x34 raw; DTP 24420 +0x6c only WARN) - exit 1 when one comes back
        @('tools\endlevel_word_judge.py', 'check', $fix2, '--report', ((Split-Path -Parent $fix2) + '/endlevel_words_check.json')),
        @('tools\vo_lang_variants.py', 'check', $fix2, 'pack11', '--expect', $voMd5, '--report', $vo2),
        (@('tools\shader_form_gate.py', 'check', $fix2, '--list', '3', '--report', $sg2) + $sgEnforce)
    )
    # Shaders (2026-11-11, A2 stage 1): recorded decisions -> shaders layer, ring rule on top, then the gates
    Shaders = @(
        @('tools\shader_step.py', 'apply', '--layers', "$fix1,$fix2", '--out', "$shOut/mods", '--report', "$shOut/shader_step_apply.json"),
        @('tools\shader_translate.py', 'run', '--layers', "$fix1,$fix2,$shOut/mods", '--out', "$shTr/mods", '--apply-report', "$shOut/shader_step_apply.json",
          '--work', "$shTr/work", '--scope-gaps', '--expect', 'docs/data/shader_translate.tsv', '--report', "$shTr/shader_translate.json"),
        @('tools\rule_owned.py', 'apply', "$shRule/mods", $fix1, $fix2, "$shOut/mods", "$shTr/mods"),
        @('tools\rule_owned.py', 'check', $fix1, $fix2, "$shOut/mods", "$shTr/mods", "$shRule/mods", '--report', "$shRule/rule_owned_check.json"),
        (@('tools\shader_form_gate.py', 'check', "$shOut/mods", '--list', '3', '--report', "$shOut/shader_form_check.json") + $sgEnforce),
        (@('tools\shader_form_gate.py', 'check', "$shTr/mods", '--list', '3', '--report', "$shTr/shader_form_check.json") + $sgEnforce),
        @('tools\tu_batch.py', 'vcheck', "$shOut/mods", 'work/sg_audit_0511/xbox', '--strict'),
        @('tools\tu_batch.py', 'vcheck', "$shTr/mods", 'work/sg_audit_0511/xbox', '--strict'),
        # P4a (2026-11-13): pass-2 slot gaps = ERROR (exit 1), refused copies with a surrogate = visible WARNING
        @('tools\shader_slot_gate.py', 'check', '--layers', "$fix1,$fix2,$shOut/mods,$shTr/mods,$shRule/mods", '--report', "$shTr/shader_slot_gate.json")
    )
    Costumes = $costumeTools
    # DoppelCostume (Q23): recipe object id 857 -> 1031 on our doppelganger_casual (gate before writing), then re-check
    DoppelCostume = @(
        (@('tools\doppel_costume_clone.py', 'build') + $dpStack + @('--out', "$dpOut/mods", '--report', "$dpOut/doppel_costume_build.json")),
        (@('tools\doppel_costume_clone.py', 'check', "$dpOut/mods/dlc_doppel_costume_a.drm") + $dpStack + @('--report', "$dpOut/doppel_costume_check.json"))
    )
    Repair = @(
        @('tools\b138_snapshot.py', '../release/B138/kit/manifest.json', '../data/pc/mods', '../backup', $repPristine, '../backup/mods', 'work/rebuild/base_b138'),
        (@('tools\generalbank_build.py', $gbOut) + $gbBase),
        @('tools\input_map_tu_fix.py', '--verify', "$gbOut/mods/generalbank.drm", '--report', "$gbOut/input_map_check.json"),
        # K12 (2026-11-08): the title update's player list (29 ids, + 857) into DTP 2, idempotent (--done-ok), then gate
        @('tools\globalinfo_player_list_fix.py', "$gbOut/mods/generalbank.drm", "$gbOut/k12/mods/generalbank.drm", '--done-ok'),
        @('tools\globalinfo_player_list_fix.py', '--verify', "$gbOut/k12/mods/generalbank.drm", '--report', "$gbOut/player_list_check.json"),
        @('tools\b138_fix_tree.py', $repPristine, $repFixes, '--dlc2', '--replace', '--generalbank', "$gbOut/k12/mods/generalbank.drm"),
        # rule gate (2026-11-11, N3): the sections a fix rule owns (grapple ring: base material 16637 + ShaderLibs
        # 1704-1707 on 21164 / 21093 / 20345 / 20344) are byte-equal to the PC base ring (exit 1 otherwise)
        @('tools\rule_owned.py', 'check', $repFixes, '--report', ((Split-Path -Parent $repFixes) + '/rule_owned_check.json')),
        @('tools\input_map_tu_fix.py', '--verify', "$repFixes/generalbank.drm", '--report', ((Split-Path -Parent $repFixes) + '/input_map_check.json')),
        # data fix gates on the repair tree (2026-11-08): K12 list, doppelganger language variants (mul_lang_build --dlc2),
        # generator intro data (B138: 0 words), costume DTPs / caverns DSP kind (steps costumedtp / dspkind of b138_fix_tree)
        @('tools\globalinfo_player_list_fix.py', '--verify', "$repFixes/generalbank.drm", '--report', ((Split-Path -Parent $repFixes) + '/player_list_check.json')),
        @('tools\vo_lang_variants.py', 'check', $repFixes, 'pack11', '--report', ((Split-Path -Parent $repFixes) + '/vo_lang_check.json')),
        @('tools\generator_intro_fix.py', 'scan', "$repPristine,$repFixes", '--pack', 'pack10', '--report', ((Split-Path -Parent $repFixes) + '/genintro_check.json')),
        @('tools\dlc_struct_fixes.py', 'check', "$repPristine,$repFixes", '--steps', 'costumedtp,dspkind', '--pack', 'pack10', '--report', ((Split-Path -Parent $repFixes) + '/datafix_check.json')),
        (@('tools\shader_form_gate.py', 'check', $repFixes, '--list', '3', '--report', ((Split-Path -Parent $repFixes) + '/shader_form_check.json')) + $sgEnforce)
    )
    # Generalbank (2026-11-11, Q2): the PC patch.000 generalbank + the player's TitleUpdate.000 (tool default path) +
    # docs\data\generalbank_pc.json + ring P14 (md5 gate = ring tree 7, kit paths and Xbox paths other than the TU
    # refused by the tool's guard), then PC-only gates; -GeneralbankKit: the old chain
    Generalbank = if (!$GeneralbankKit) { @(
        @('tools\generalbank_pc_build.py', 'build', $gbPcOut),
        # Q7 / Q10 (2026-11-17): loading screen script 6 start-list count = the title update's 193 (refuses unless 182)
        @('tools\script_word_set.py', "$gbPcOut/mods/generalbank.drm", "$gbPcOut/mods/generalbank.drm", '6', '11b20=000000b6:000000c1')
    ) + $gbPanel + @(
        # gate: no script of the result has start-list entries after its count (exit 1 on a finding)
        @('tools\script_sfi_members.py', '--scan', "$gbPcOut/mods/generalbank.drm"),
        # gate (2026-11-19, T1): every structural count word of the scripts that keep the title update's layout = the
        # TU count (exit 1 otherwise; it finds the old 182). Allowed: the three code counts of script 6 (f3 / f5 /
        # f19: 117 / 1044 / 269, TU 120 / 1115 / 284) that script_init_from_pc copied from the PC in the kit chain -
        # in every played file since test 38, open until a live test (docs\Befund-T1-1911.md, workspace)
        @('tools\script_count_gate.py', "$gbPcOut/mods/generalbank.drm", 'tu:', '--map', '10=9,38=37', '--allow',
          '6:7920,6:8550,6:2460', '--report', "$gbPcOut/count_gate.json"),
        @('tools\menu_ring_layout.py', "$gbPcOut/mods/generalbank.drm", '--expect-p14'),
        @('tools\menu_quit_slot_check.py', "$gbPcOut/mods/generalbank.drm", '--expect', 'f15'),
        @('tools\input_map_tu_fix.py', '--verify', "$gbPcOut/mods/generalbank.drm", '--report', "$gbPcOut/input_map_check.json")
    ) } else { @(
        @('tools\generalbank_build.py', $gbOut),
        @('tools\input_map_tu_fix.py', '--verify', "$gbOut/mods/generalbank.drm", '--report', "$gbOut/input_map_check.json"),
        # gate S104 (2026-11-05): the result = step 22 + exactly the script 104 fix of step 23, block = TU script 134 test
        @('tools\dlc2_player_fix.py', 'verify', "$gbOut/steps/22_input.drm", "$gbOut/mods/generalbank.drm", '--tu', "$gbOut/steps/10_tu_be.drm", '--report', "$gbOut/script104_check.json"),
        # K12 (2026-11-08, docs Befund-Datenfixes-0711.md 2): DTP 2 player list = the title update's 29 ids (+ 857
        # doppelganger_casual); mods\generalbank.drm stays the S104 result (its md5 66efd71d... gate above), the file to
        # install is k12\mods\generalbank.drm
        @('tools\globalinfo_player_list_fix.py', "$gbOut/mods/generalbank.drm", "$gbOut/k12/mods/generalbank.drm", '--done-ok'),
        @('tools\globalinfo_player_list_fix.py', '--verify', "$gbOut/k12/mods/generalbank.drm", '--report', "$gbOut/player_list_check.json"),
        @('tools\input_map_tu_fix.py', '--verify', "$gbOut/k12/mods/generalbank.drm", '--report', "$gbOut/k12/input_map_check.json")
    ) }
    # Exe: build (every stage checks its bytes first, gate md5 = B138), then list the stages of the result
    Exe = @(
        @('tools\exe_build.py', "$exeOut/tru.exe", '--report', "$exeOut/exe_build.json"),
        @('tools\exe_build.py', '--check', "$exeOut/tru.exe", '--report', "$exeOut/exe_check.json")
    )
    # Globalsound: build (PC original md5 checked first, gate raw md5 = B138 / B270 kit file), then re-check the file
    Globalsound = @(
        @('tools\globalsoundinfo_build.py', 'build', $gsOut),
        @('tools\globalsoundinfo_build.py', '--check', "$gsOut/mods/globalsoundinfo.drm")
    )
    # Lang: build (mul_lang_build --variants-only, one process per cinematic / voice set, at most 3), then the gate
    # (exactly the 60 files, md5 = the installed variants, no .mul_2048 / .mul_032)
    Lang = @(
        @('tools\lang_variants_step.py', 'build', "$langOut/mods", '--replace'),
        @('tools\lang_variants_step.py', 'check', "$langOut/mods", '--report', "$langOut/lang_check.json")
    )
}
$outputDirs = @{
    Index   = @('work')
    Cache   = @('work\generic')
    Ids     = @('work\generic', 'work\generic\merged')
    Learn   = @('work\generic', 'work\script')
    Tables  = @('work\generic', 'work\script')
    Prep    = @('work\generic', 'work\chain_aim')
    Convert = @('work\generic\out')
    Names   = @('work\generic')
    Media   = @('work\rebuild')
    Audio   = @('work\rebuild')
    Assemble = @('work\render', 'work\rebuild')
    Dlc2    = @('work\rebuild')
    Fixes   = @('work\rebuild')
    Shaders = @(($shOut -replace '/', '\'), ($shTr -replace '/', '\'), ($shRule -replace '/', '\'))
    Costumes = @('work\rebuild')
    DoppelCostume = @(($dpOut -replace '/', '\'))
    Repair  = @('work\rebuild')
    Generalbank = @('work\rebuild')
    Exe     = @(($exeOut -replace '/', '\'))
    Globalsound = @(($gsOut -replace '/', '\'))
    Lang    = @(($langOut -replace '/', '\'))
}
# steps whose progress can be measured by counting output files
$progressHints = @{
    # 307 pack records, 300 distinct file names (7 duplicate records write the same file again)
    Convert = @{ Dir = 'work\generic\out'; Filter = '*.drm'; Total = 300 }
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir ('Invoke-TruPipeline_{0}_{1}.log' -f $Step, (Get-Date -Format 'yyyyMMdd_HHmmss'))
Set-TruLogFile -Path $logFile

function Get-ProgressCount {
    # number of output files written since the tool started (older files from a previous run do not count),
    # for steps with a known total (see $progressHints)
    param([datetime]$Since)
    $hint = $progressHints[$Step]
    if (!$hint) { return $null }
    $dir = Join-Path $clone $hint.Dir
    if (!(Test-Path -LiteralPath $dir)) { return 0 }
    return @(Get-ChildItem -LiteralPath $dir -Recurse -File -Filter $hint.Filter -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -ge $Since }).Count
}

function Invoke-Tool {
    param([string[]]$ToolArgs, [string]$Label)
    # -X utf8: with -I Python ignores PYTHONIOENCODING and would write cp1252 to the pipe; any character outside
    # cp1252 in a tool's output (e.g. game text, an arrow) would then raise UnicodeEncodeError
    $allArgs = @('-u', '-I', '-X', 'utf8') + $ToolArgs
    $argLine = ($allArgs | ForEach-Object { if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ } }) -join ' '
    Write-Log "python $argLine" -Level DEBUG

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $python
    $psi.Arguments = $argLine
    $psi.WorkingDirectory = $clone
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    $psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8
    $process = [System.Diagnostics.Process]::Start($psi)
    $script:runningProcess = $process    # for the finally block: report it if the run is aborted while it runs

    # read stdout and stderr line by line without blocking; heartbeat every 30 s
    $outTask = $process.StandardOutput.ReadLineAsync()
    $errTask = $process.StandardError.ReadLineAsync()
    $t0 = Get-Date
    $nextBeat = $t0.AddSeconds(30)
    $nextCount = $t0
    $count = $null
    $hint = $progressHints[$Step]
    while ($outTask -or $errTask) {
        $idle = $true
        if ($outTask -and $outTask.IsCompleted) {
            $line = $outTask.Result
            if ($null -eq $line) { $outTask = $null } else { Write-Log $line; $outTask = $process.StandardOutput.ReadLineAsync(); $idle = $false }
        }
        if ($errTask -and $errTask.IsCompleted) {
            $line = $errTask.Result
            if ($null -eq $line) { $errTask = $null } else { Write-Log ('stderr: ' + $line); $errTask = $process.StandardError.ReadLineAsync(); $idle = $false }
        }
        $now = Get-Date
        $elapsed = $now - $t0
        $status = '{0}  running {1:hh\:mm\:ss}' -f $Label, $elapsed
        if ($now -ge $nextCount) { $count = Get-ProgressCount -Since $t0; $nextCount = $now.AddSeconds(5) }
        if ($null -ne $count -and $hint.Total -gt 0) {
            $percent = [Math]::Min(99, [int](100 * $count / $hint.Total))
            $remaining = if ($count -gt 0) { [int]($elapsed.TotalSeconds * ($hint.Total - $count) / $count) } else { -1 }
            Write-Progress -Activity "Invoke-TruPipeline $Step" -Status ('{0}  {1}/{2} files' -f $status, $count, $hint.Total) -PercentComplete $percent -SecondsRemaining $remaining
        } else {
            Write-Progress -Activity "Invoke-TruPipeline $Step" -Status $status
        }
        if ($now -ge $nextBeat) {
            $beat = if ($null -ne $count) { '{0} / {1} files' -f $count, $hint.Total } else { 'no output yet' }
            Write-Log ('... still running: {0}, {1:hh\:mm\:ss}, {2}' -f $Label, $elapsed, $beat)
            $nextBeat = $now.AddSeconds(30)
        }
        if ($idle) { Start-Sleep -Milliseconds 250 }
    }
    $process.WaitForExit()
    $script:runningProcess = $null
    Write-Progress -Activity "Invoke-TruPipeline $Step" -Completed
    return $process.ExitCode
}

if ($Trace) { Set-PSDebug -Trace 1 }
$results = @()
$started = Get-Date
$script:runningProcess = $null
$savedEnv = @{}
$playerRules = $null; $playerLog = $null
Push-Location $clone
try {
    Write-Log "Invoke-TruPipeline step=$Step log=$logFile" -Level VERBOSE
    if (!(Test-Path -LiteralPath $python)) { throw "Python venv not found: $python (see README, Entwicklungsumgebung)." }
    Write-Log "Python: $((& $python --version 2>&1) -join ' ')" -Level DEBUG
    # audio conversion: prefer the ffmpeg from <workspace>\bin (Get-Tools.ps1), else the tools find one on PATH
    $ffmpeg = Join-Path $root 'bin\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe'
    if (Test-Path -LiteralPath $ffmpeg) { $env:TRUDLC_FFMPEG = $ffmpeg }
    Write-Log "ffmpeg: $(if ($env:TRUDLC_FFMPEG) { $env:TRUDLC_FFMPEG } else { 'from PATH' })" -Level DEBUG
    # process counts (docs/WINDOWS_REBUILD.md finding 36: one converter process needs ~18 GB, light tools < 20 MB)
    $freeGb = [int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB)
    $cpus = [int](Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
    if ($Jobs -eq 0) { $Jobs = [Math]::Max(1, [Math]::Min(3, [int][Math]::Floor(($freeGb - 8) / 18))) }
    if ($LightJobs -eq 0) { $LightJobs = [Math]::Max(1, [Math]::Min(24, $cpus - 4)) }
    $env:TRUDLC_JOBS = $Jobs
    $env:TRUDLC_JOBS_LIGHT = $LightJobs
    # DLC selection and string id map come from the step's own arguments (--pack pack11), never from the calling
    # shell: a TRUDLC_PACK_FIRST left over from a manual DLC 2 run would switch DLC 1 to DLC-2-only fixes
    foreach ($name in 'TRUDLC_PACK_FIRST', 'TRUDLC_LOCMAP') {
        $value = [Environment]::GetEnvironmentVariable($name, 'Process')
        if ($value) {
            $savedEnv[$name] = $value
            Write-Log "ignoring $name=$value from the calling shell for this run" -Level VERBOSE
            [Environment]::SetEnvironmentVariable($name, $null, 'Process')
        }
    }
    # player-path access guard (P0): the run's own -PlayerMode, never a mode left in the calling shell
    foreach ($name in 'TRU_PLAYER_MODE', 'TRU_PLAYER_LOG') {
        $value = [Environment]::GetEnvironmentVariable($name, 'Process')
        if ($value) {
            $savedEnv[$name] = $value
            Write-Log "ignoring $name=$value from the calling shell for this run" -Level VERBOSE
            [Environment]::SetEnvironmentVariable($name, $null, 'Process')
        }
    }
    if ($PlayerMode -ne 'Off') {
        $playerRules = Get-TruPlayerGuardRules -Repository $clone
        $playerLog = Join-Path $logDir ('player_guard_{0}_{1}.tsv' -f $Step, (Get-Date -Format 'yyyyMMdd_HHmmss'))
        $env:TRU_PLAYER_MODE = $PlayerMode.ToLower()
        $env:TRU_PLAYER_LOG = $playerLog
        Write-Log ('player guard: {0}, rules {1}, access log {2}' -f $PlayerMode, $playerRules.Version, $playerLog) -Level VERBOSE
    }
    Write-Log ('processes: heavy {0}, light {1} (free RAM {2} GB, {3} logical CPUs)' -f $Jobs, $LightJobs, $freeGb, $cpus) -Level VERBOSE
    foreach ($dir in $outputDirs[$Step]) { New-Item -ItemType Directory -Force -Path (Join-Path $clone $dir) | Out-Null }

    $toolCount = @($steps[$Step]).Count
    $toolIndex = 0
    foreach ($toolArgs in $steps[$Step]) {
        $toolIndex++
        if ($toolIndex -lt $FromTool) {
            Write-Log ('== skipped (FromTool {0}): {1}' -f $FromTool, ($toolArgs -join ' ')) -Level VERBOSE
            continue
        }
        if ($toolIndex -gt $ToTool) {
            Write-Log ('== skipped (ToTool {0}): {1}' -f $ToTool, ($toolArgs -join ' ')) -Level VERBOSE
            continue
        }
        $t0 = Get-Date
        $label = 'tool {0}/{1} {2}' -f $toolIndex, $toolCount, (Split-Path -Leaf $toolArgs[0])
        Write-Log ('== ' + ($toolArgs -join ' ')) -Level VERBOSE
        $runArgs = $toolArgs
        if ($playerRules) {
            # arguments first (Enforce throws here), then the tool runs inside the guard (its own default paths)
            $null = Assert-TruPlayerToolArgs -ToolArgs $toolArgs -Rules $playerRules -Mode $PlayerMode -BaseDir $clone
            $runArgs = @('tools\player_guard.py', 'run') + $toolArgs
        }
        $code = Invoke-Tool -ToolArgs $runArgs -Label $label
        $seconds = [int]((Get-Date) - $t0).TotalSeconds
        $results += [pscustomobject]@{ Tool = ($toolArgs -join ' '); ExitCode = $code; Seconds = $seconds }
        if ($code -ne 0) { throw "Tool failed (exit code $code): $($toolArgs -join ' ')" }
    }
}
catch {
    Write-Log "FAILED: $($_.Exception.Message)" -Level ERROR
    Write-Log ($_.ScriptStackTrace) -Level DEBUG
    throw
}
finally {
    Pop-Location
    if ($Trace) { Set-PSDebug -Off }
    if ($playerRules) {
        # counts per tool / action / category from the access log (tools\player_guard.py summary)
        Write-Log ('--- player guard ({0}) ---' -f $PlayerMode)
        if (Test-Path -LiteralPath $playerLog) {
            $guardTool = Join-Path $clone 'tools\player_guard.py'
            $sum = & $python -u -I -X utf8 $guardTool summary $playerLog --json ($playerLog -replace '\.tsv$', '.json') 2>&1
            foreach ($l in $sum) { Write-Log ('{0}' -f $l) }
        } else {
            Write-Log 'no access matched a guard rule (no access log written)'
        }
        [Environment]::SetEnvironmentVariable('TRU_PLAYER_MODE', $null, 'Process')
        [Environment]::SetEnvironmentVariable('TRU_PLAYER_LOG', $null, 'Process')
    }
    foreach ($name in $savedEnv.Keys) { [Environment]::SetEnvironmentVariable($name, $savedEnv[$name], 'Process') }
    # aborted (Ctrl+C, error) while a tool was running: the tool and its worker processes keep running (they were
    # started without a console). Nothing is ended automatically - the PIDs are logged so the user can decide.
    if ($script:runningProcess -and !$script:runningProcess.HasExited) {
        $toolPid = $script:runningProcess.Id
        $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$toolPid" -ErrorAction SilentlyContinue |
            ForEach-Object { $_.ProcessId })
        Write-Log ('Tool still running after the abort: PID {0}, worker PIDs: {1}. Not ended - end them yourself if needed.' -f
            $toolPid, $(if ($children.Count) { $children -join ', ' } else { 'none' })) -Level WARN
    }
    Write-Log '--- summary ---'
    foreach ($r in $results) { Write-Log ('{0,-40} exit {1}  {2} s' -f $r.Tool, $r.ExitCode, $r.Seconds) }
    foreach ($dir in $outputDirs[$Step]) {
        Get-ChildItem -LiteralPath (Join-Path $clone $dir) -File -ErrorAction SilentlyContinue |
            ForEach-Object { Write-Log ('{0,-40} {1,14} bytes' -f "$dir\$($_.Name)", $_.Length) }
    }
    # plain integers: N0 uses the culture's group separator ("3.097 s" on German systems)
    Write-Log ('total {0} s' -f [int]((Get-Date) - $started).TotalSeconds)
    Write-Host "Log: $logFile"
}
