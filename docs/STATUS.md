# Status (as of 17 Oct 2026, build `B90_gold_L4`)

"Confirmed" means the project owner played it in a real Windows VM. "Offline" means checked only by static analysis / simulation, never seen in-game.

## What works

| Area | State | Evidence |
|---|---|---|
| Game start with the patched exe | Works, no start-up crash | 4/4 automated starts + user (FMOD init guard) |
| DLC1 entry from the menu, new game | Works | Confirmed |
| Opening cutscene (`pdlc1_010_intro`) | Plays with `Cine_Start`/`Cine_End` | Confirmed (B45). Cause of the earlier failure: cutscene command lists converted as u32 instead of per-frame `{type,frame}` records |
| Real audio (music, ambience, voice) | Present (converted Xbox XMA → PC IMA, in place) | Present since B43. Sound *quality* ("crackly" in an early test) was never formally re-judged |
| Grapple rings from the raft (water wheel) | Works | Confirmed (record tag `0x404`: enable byte must stay raw, not s32) |
| Ceiling rings after a new game | Works | Confirmed 15 Oct |
| Water wheel level loads | Works; the "rainbow" noise object is fixed | Confirmed (B83/B87) |
| Bridge at the start of the DLC | Present in a new game | Confirmed (B88b, B89, B90) |
| Texture lifetime crash `R6025` (pillory → dlc_dungeon) | Fixed | Confirmed (B89): textures 259 and 2224 were referenced by materials but lived in no resident DRM; they are now added to the DRMs that need them |
| Light crash at dungeon corner (`0x5076fa`) | Fixed by exe guard | Confirmed 17 Oct (guard fired once, with the known stale pointer) |
| SoundPlex crash on arrival in dlc_dungeon (`0x592218`) | No crash with the exe guard | Confirmed in `B90_gold_L4` (counters not read) |
| Shader pipeline | 19 + 7 + 1 materials re-translated from Xbox pixel shaders; all new shader libs accepted by a real D3D9 device (dgVoodoo HAL) | 152/152 and 64/64 `CreatePixelShader`+draw HRESULT 0 |
| Static gates | `idref_selfcont`, `gate_stesso_id`, `tex_lifetime_check`, `test_contract`, `dlc1_gate` | Green on `B90_gold_L4` |

Net result: you can start DLC1, watch the opening cutscene, play through the caverns, water wheel and reach *dlc_dungeon* without crashing.

## What does not work / is wrong

| Area | Symptom | Notes |
|---|---|---|
| **Cobwebs** | Wrong brightness/look, in particular from *water_wheel* onwards | Still wrong after calibrating two materials (23173, 23329) to 0.46/0.44 on `c104.x`. See INVESTIGATION #2 |
| **Reddish surfaces in *dlc_caverns_hall*** | Some surfaces tinted red | MaterialParams of the hall are identical to the Xbox ones for every stock-PC-shader material; simulation shows no shader/param/texel cause. Unexplained. INVESTIGATION #3 |
| **dlc_dungeon looks "broken" when reached naturally** | Level appears broken/incomplete (symptom not yet described precisely) | Loading it directly with the debug menu works and does not look broken → likely a streaming/resident-set issue. INVESTIGATION #1 |
| Bridge collapse / Adrenaline trap | Bridge is there; the collapse after the intro cutscene could not be verified | Driven by scripts (`ma_ei_breakable_*`, script 23175); not decodable statically so far |
| Sluice gate / tunnel at the water wheel | Last known (15 Oct): grapple works but the tunnel does not open | Static analysis points at `dlc1_uo_sewer_gate` lowering by itself before the grapple; **not re-verified** in recent builds |
| Small waterfall in *caverns_hall* | Missing in the B87 test | Water libs 2775–2781 were added afterwards (offline); not re-checked |
| Remaining lit shaders | Libs 21118 / 20262 / 21164 still use PC surrogates | No donor shader found |
| Direct-light path in the shader harness | Not validated (direct light share only 50 % Xbox / 33 % PC in the simulation) | Limits every conclusion about lit materials |
| SoundPlex root cause | A node with a null data pointer exists in some DLC data; the guard only *masks* it | Cause not proven (probably older than B89, hidden by R6025) |
| Dead bits (`uid ≥ 16352`) | 5 DLC intro uids exceed the engine's 16352-bit table (queries are harmless, sets are no-ops) | A first fix (remap to 12241–12245) was dropped because map sections (type 13) still referenced the old uids |
| DLC2 *Lara's Shadow* (`pack11`) | Not started | |
| In-game debug menu F8 | Did not work for the tester | Not investigated |

## Where we stopped
* Last user test: `B90_gold_L4` + exe `f47814ff…`. No crash; cobwebs, red tint and the "broken" dlc_dungeon remain. The owner asked to record the result and stop investigating.
* Last offline work (Giro 7): SoundPlex audit (264 054 nodes, no discrepancy in comparable DTPs), a fog-aware cobweb calibration harness (`work/ws/giro6/web_calib.py`, `web_lever.py`), MaterialParams audit of caverns_hall (`work/ws/giro7/hall_params_audit.py`).
* The VM was left on `B90_gold_L4` with the patched exe.

## Build lineage in one line
`B11 → B14 → B31 → B33 (rings) → B41/B42 (material params) → B43 (audio) → B45 (cutscene) → B47 → B73…B83 (shader transplant) → B86 (sampler contract) → B87 (19 materials + exe guards) → B88b (7 water libs) → B89/B90 (tex 259/2224, libs 975/976/2782, cobweb K) = B90_gold_L4`. See [LINEAGE.md](LINEAGE.md).
