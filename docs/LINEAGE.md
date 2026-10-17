# Build lineage (what each step added)

The original baselines live outside this repo (they contain converted game data). Their manifests recorded origin and a note per file. Only the final manifest is included: `data/B90_gold_L4.manifest.tsv` (origin column: how many files came from which step).

| Step | Contents | Key finding |
|---|---|---|
| B1 – B11 | Base conversion of the DLC1 DRMs; crash fixes: material index crash in the dungeon (`B2`), rigid-body model index (`B5`), tag `0x403` ids (`B6`), portals (`B7`); dungeon cobwebs cut-outs; stream names (save-hang cause) | Early crashes were data conversion errors, each found by pairing with base-game data |
| B13, B14, B31, B32, B33 | Raft physics words, 67 unconverted float words (opening cutscene / dungeon), a 13-form physics family, 17 words of the final cutscene, **record `0x404` fix** (raft grapple) | B33 = reference; B30 is a known-bad regression |
| B41, B42 | MaterialParams remap for 76 materials; B42 reverts 22 multipliers ≥ 2× | B41 fixed white platforms but caused neon-green planks and red tints |
| B43 | Real audio instead of silence | |
| B44, B45 | Cutscene works (command lists reconverted structurally) | Opening cutscene confirmed |
| B46, B47 | Float words as u16 pairs (water wheel blades, pillory), 69 verified raw floats | |
| B72 – B83 | Shader work: translator, light transplant, one lib per material; B83 = the working line | Water wheel crash fixed |
| B86 `contratti` | Sampler contract fix: Xbox sampler register ≠ PC slot | 21/35 materials were wrong before |
| B87 `materiali19` | 19 materials re-translated (ids 2756–2774); exe guards for FMOD init and light texture | Start-up and dungeon-corner crashes gone |
| B88b `acqua` | 7 unlit water/waterfall libs translated directly (ids 2775–2781) | R6025 appears when going pillory → dlc_dungeon |
| B89 | + textures 259/2224 (fixes R6025), libs 975/976/2782, dead-bit remap L2 | New crash `0x592218` in dlc_dungeon |
| B90_gold | B89 without L2 | Remap was inconsistent (map sections) |
| **B90_gold_L4** | + calibrated cobweb `c104.x` for 23173 (0.46) and 23329 (0.44), + `soundplex_guard` in the exe | No crash; webs/red tint/dungeon look still open |

Superseded or rejected builds worth knowing: B9/B10 (cube fix at the wrong index, boot crash), B30 (regression), B40, B75/B76 (sampler `dcl` ≥ s16 / missing variants), B88_fullpass, `B90_gold_webdim` (based on a wrong harness).

File-origin counts in the final tree: 71 `derived:B43` (audio), 46 `mods_fix12`, 38 UI images, 30 + 10 files that were already installed in the test VM (`vm_mods_expected`, `vm_extra`), 15 `B86`, 13 + 6 from the latest layers, 12 `B87`, 11 `mods_fix18`, others ≤ 6.
