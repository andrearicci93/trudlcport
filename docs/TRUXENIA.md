# TruXenia - Xbox values from Xenia (menu + link)

TruXenia is the Xbox-side counterpart of TruMenu's diagnostics: while *Tomb Raider: Underworld* with the title update
runs in the Xenia emulator, it shows enemy and Lara values, writes a hit log in the same layout as TruMenu's
`combo.trace` on PC, offers a small command link for scripts (like TruLink on PC) and keeps a library of named Xbox
saves. The goal is to measure the same fight on both sides and compare it line by line (TODO N18 "combat like the
Xbox"). No plugin runs inside Xenia; the Xbox game behaves as it should.

## Safety

- **Read only by default.** Xenia is opened with `PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION` and only
  `ReadProcessMemory` is used - no debugger, no suspend (a debugger listing of all memory regions froze Xenia once).
- **Proof words first.** Every TU address in `docs/data/xenia_tu_combat_addresses.json` carries TU instruction words
  that prove it; TruXenia compares all of them (139 since 2026-11-11, every JSON section with a `proof` block) with the guest memory
  and refuses to read on a mismatch. Sections marked `"optional": true` (the four sonar sections, 89 words since
  2026-11-14) are counted apart: a mismatch there does not stop TruXenia, it shows that section's values as `?`.
- **Unproven fields are `?`.** Fields marked `"proven": false` (target slot, coordinator `Ko`) are shown as `?`; the
  check box "show unproven fields" shows them marked with `~`. Camera position / look-at / FOV are `?` (not proven).
- **Writes are locked.** `set <inst> lp|stamina <value>` exists, but only with `--allow-write` and an explicit unlock
  (GUI button with confirmation, or the link command `unlock yes`). Data words only, never code (Xenia translates the
  code ahead of time); every write is read back. Security software may flag `WriteProcessMemory`
  into another process - that is expected; nothing is hidden or obfuscated.
- **Xenia's own options are not touched.** TruXenia never edits the Xenia config (shader dump / store options are
  only mentioned below as a possible second source).
- **Saves:** "restore" works only while `xenia_canary.exe` is closed and backs up the current save folder first.

## Start

From the repository root (`../bin/pyt` = the project's Python runner; any Python 3 with tkinter works):

```
../bin/pyt -t 60 tools/truxenia.py --check        # Xenia running: proof words only
../bin/pyt -t 60 tools/truxenia.py --once         # one snapshot to the console
../bin/pyt -t 0  tools/truxenia.py                # window + link on 127.0.0.1:47011
../bin/pyt -t 0  tools/truxenia.py --nogui        # link only
../bin/pyt -t 120 tools/truxenia.py --selftest    # offline: simulated memory, hit log, link, saves (dry run)
../bin/pyt -t 60 tools/truxenia.py --dumpfile work/xenia_dump/tu_image_82000000.bin --check   # proof words vs a dump
../bin/pyt -t 0  tools/truxenia.py --camtrace --camtrace-seconds 300   # camera trace TSV only (next to a running TruXenia)
../bin/pyt -t 0  tools/truxenia.py --movelog --movelog-seconds 900     # move log (section "Move log"), next to TruXenia
../bin/pyt -t 120 tools/truxenia_moves.py --selftest                   # offline: move log lines on a simulated TU memory
../bin/pyt -t 120 tools/compare_pc_xenia_logs.py --selftest            # offline: the PC / Xbox comparison
```

Options: `--port N`, `--log PATH`, `--hitlog PATH`, `--unproven`, `--allow-write`, `--lang de|en`, `--verbose`,
`--debug`, `--trace`. Logs go to `<workspace>/logs/truxenia/` (`truxenia_<time>.log`, `hits_<time>.log`). Settings are
not saved (language and options only for the session).

## Window (DE / EN, flag button)

| Page | Content |
|---|---|
| Gegner / Enemies | real enemies only (brain test, below): kind symbol in its colour, name + object id, LP (`*` = LP note, e.g. RegenerateDeath), stamina, state layer 0 / 1, requested state, target, distance, `Ko` (`?`), Ko handle, attack (MeleeAttack record + anim ids), flight (running or last); refresh every 100 ms |
| Objekte / Objects | every instance of the instance list: kind, name, object id, enemy yes / no, distance; one coloured check box per kind = legend and filter |
| Lara | chart record **indices** of machine 0 / 1 and their state id lists, LP (max), position, shadow meter value + flags (active), world time scale, the 7 time-scale request slots and the winning slot per scale, ramp targets player / world, doppelganger flag, camera mode / flags (position / FOV `?`) |
| Geladene Daten / Loaded data | object table (loaded objects, state counts; read once per second) and the plan for units / sections / shaders (below) |
| Sonar | PDA sonar (ping map): mode, stage, ping radius, view distance, current map unit, floor, triangles drawn / refused per frame (and the maximum of the last 2 s) against the limit 93571; one row per loaded map unit: name, faces, vertices, map kind (echt / Platzhalter "MAP" / kein Netz), floor mask, placed, revealed vertices (%); read every 0.5 s while the page is shown (section "Sonar" below) |
| Log / Link | recording on / off (TSV of all values), the hit lines, the link address, the write lock |
| Spielstände / Saves | named saves in `<workspace>/_archiv/xenia-saves/<name>/534307EC` (+ README): store the current saves under a name, restore one (Xenia closed) |

### Kinds (symbol, colour, filter)

The kind comes from the object name; nothing is guessed - a name that matches no rule is "other" (Sonstiges).

| Kind | Rule (object name, lower case) |
|---|---|
| Lara | the player instance of the game tracker |
| Chunkdoll (pieces) | contains `chunkdoll` |
| Generator | contains `generator` |
| Goo (drips, balls, spawners) | contains `goo` |
| Natla / scripted actor | contains `natla` |
| Yeti | enemy (brain test) and `yeti` |
| Tutorial thrall | enemy and `tutorial` and `thrall` |
| Thrall | enemy and `thrall` |
| Pickup / interactable | contains pickup, medipack, health, ammo, treasure, reward, lever, switch, button, door, chest or relic |
| Other | everything else |

**Brain test (real enemies):** TU enemy init 0x822da9ac: `[inst+0x50]` word 0 == 0xdaf00018 and byte +0x18 > 0 ->
the game allocates a brain (PC 0x63c1b5 the same test). Only instances that pass are enemies; the live log of
09.11. 17:37 (before this test) had 883 "hits" with LP values like 0x3f800000 from non-enemy objects.

## Hit log

Every LP drop of an enemy gives one line after 0.5 s:

```
18:26:19.930 combo: Lara records 1477>1488 -> viking_thrall_tutorial_dlc2_ 1004 LP 500.0 -> 480.0 (-20.0), stamina 40.0 -> 40.0, state at the hit CombatStepIdle, reaction Hit | xbox: dist 50, meter 1000.0 active False, time scale 1.00 | xbox+: kind tutorial, attack -, fly -, last flight -, Lara LP 1000.0, Lara states [], time requests -, world ramp 1.00
```

The text up to `reaction` is the same as TruMenu 0.22.9 `combo.trace` on PC; the PC line names the intro id, the
Xbox line the object id. `records` = Lara's chart record indices of the last 2 s (combo path), `reaction` = the first
state the enemy enters within 0.5 s after the LP drop. Damage type / sub are not readable on the Xbox side; on PC they
come from TruShadowCombat's `damage types` line. The `| xbox:` part is unchanged; new values come after `| xbox+:`:

| Field | Meaning | Source |
|---|---|---|
| kind | kind of the enemy (table above) | object name + brain test |
| attack | `rec <record> anim t/a t/a t/a` while the enemy is in MeleeAttack: the attack record and its 3 anim refs (type / anim) - tells e.g. the spit attack from a strike | data = (brain+0x1254 + (slot + 2*layer)*0x19c + 0x1f) & ~0xf, slot = [brain+0x18d4+4*layer], record = [data+0x50], self-check [data+0x198] == state object (TU 0x8232fb48); anim refs record+0x78 (ENGINE.md 13.5) |
| fly / last flight | horizontal way of the enemy while in Fall / Splat / Land: `320 u in 0.6 s (Fall>Land)` | instance position +0x20 (TU 0x8238d384) |
| Lara LP | Lara's health | player tracker +0x628 (max +0x630; TU 0x823e8068) |
| Lara states | state ids of Lara's current chart record (machine 0) | record +0x18 list, +0xc count |
| time requests | occupied request slots `slot:player/world` | meter +0x40, 7 x {f32 player, f32 world} |
| world ramp | world time-scale ramp target | 0x827754cc |

**Reaction `finisher-in-RegenerateDeath`:** RegenerateDeath Enter (TU 0x8235dff8, state object 0x8277a7b8) sets the
enemy's LP to the maximum of its current tune. A hit while the enemy is in RegenerateDeath therefore removes that
restored maximum - it is the finisher, not normal damage. `combat_log_compare.py` counts these separately.

Since 09.11.2026 `records` are indices: machine+0x520 holds a **record pointer**; its index is its position in the
record array `[[machine+4]+0xc]` (TU machine reset 0x82482808). Earlier logs show the raw pointer.

### Recording (TSV)

The PC-compatible columns stay first and unchanged: `host_time inst obj_id obj_name lp stamina state0 state1 req target
dist lara_rec0 lara_rec1 meter active time_scale`. Appended: `kind pos_x pos_y pos_z speed fly last_flight attack
ko_handle lp_note lara_lp lara_states lara_pos ts_requests ts_selected ramp_player ramp_world cam_mode cam_flags
aim_cm1fc aim_bits aim_t0_flags aim_t0_target` (the last four since 2026-11-10, section "Lock-on path"), `cam_obj
cam_x cam_y cam_z cam_yaw cam_pitch cam_fov_deg cam_dir lara_yaw delta_yaw cam_dist cam_clock cam_delay cam_ramp
cam_weight cam_settings` (since 2026-11-11, section "Camera"). Rows are written per enemy only - for the camera alone
use `--camtrace`.
`ts_requests` / `ts_selected` have the same text as TruMenu 0.22.11's `pc_ts_requests` / `pc_ts_selected`
(`0:1.20/0.30 4:0.02/1.00`, `P0.02(s4) W1.00(s4)`), so PC and Xbox can be matched by column name
(`tools/fight_trace_compare.py` reads only the shared first 16 columns so far).

## Time-scale requests (shadow-power mode)

The meter object has 7 request slots at +0x40 (stride 8: f32 player scale, f32 world scale). The selector
(TU 0x823d7520) walks from slot 6 down to slot 0 - the highest slot with a value > 0.0 wins (compare with the constant
0.0 at 0x8207d538, `ble` skips; so 0 and TruMenu's "empty = -1" are both empty), separately for player and world - and
writes the ramp targets 0x827754ac (player) / 0x827754cc (world). Slot writers (Befund X23): 0 power
start / stop, 1 meter target, 2 strike look, 3 adrenaline look, 4 player event switch / condition 2401, 5 state 1018,
6 script natives 23 / 24. The Lara page shows all 7 slots, the winner per scale and both ramp targets.

## Link (for scripts)

`tools/truxenia_cmd.py <command>` sends one line to 127.0.0.1:47011 and prints the answer (also logged):
`status`, `enemies`, `lara`, `objects [kind]`, `loaded`, `hits [n]`, `snapshot <file.json>`,
`watch <seconds> <file.tsv>`, `saves`, `set <inst> lp|stamina <value>` (locked), `sonar`, `peek <addr> <len>`, `quit`.

`peek <guest address hex> <length>` (2026-11-14) is a generic **read-only** memory view: 1..4096 bytes inside guest RAM
0x00010000..0xffffffff (anything else is refused, an unmapped page answers `unreadable`), printed as hex + ASCII
lines and then every aligned word as big-endian u32 and float. It reads like every other value (ReadProcessMemory);
there is no matching write command.

## Compare a fight

```
../bin/pyt -t 120 tools/combat_log_compare.py --pc-menu <game>/TruMenu.log --pc-combat <game>/TruShadowCombat.log
      --since 14:55:00 --until 15:05:00 --xbox ../logs/truxenia/hits_<time>.log --out ../logs/compare.md
```

One row per hit (n-th PC hit next to the n-th Xbox hit; the `xbox+` part in its own last column) and a summary per
side: hits, mean / min / max damage, reactions counted, share of knock-down reactions (Fall / Vaulted / Knockdown /
Land / RegenerateDeath), finishers in RegenerateDeath (kept out of the damage numbers), hits per kind.

## Loaded data - proven part and plan

Proven and shown: the **object table** 0x82979280 (0xcc entries of 0x24 bytes; +8 object, u16 +0xc object id, u16
+0xe state, 2 = loaded; TU 0x8214684c, PC twin 0xdb7400, ENGINE.md section 2).

Not proven yet (shown as plan text, no values):

| Wanted | PC side (known) | Missing on the Xbox side |
|---|---|---|
| script units / unit list | TRScriptUnitManager 0xa13eec | TU twin of the manager and its unit list (find the TU function by the PC call pattern, then proof words) |
| DRMs / sections | section database (not mapped on PC either) | section DB address + entry layout on both sides |
| shaders / materials | - | material / shader library list. Second source without memory reads: Xenia's own shader cache (`store_shaders`) or `dump_shaders` - Xenia options, read only here, never changed by TruXenia |

### Camera

Shown: manager 0x82efc780 (TU 0x822a9a6c = PC flag reader 0x5e5e8e), mode +0x54, flags +0x7c (ENGINE.md section 22).

Since 2026-11-11 (camera comparison, workspace `docs\Plan-Kamera-Vergleich-Xenia-PC-1111.md`; address-file section
`camera`, 36 new proof words, 139 in all):

| Value | TU | Proof (PC twin) |
|---|---|---|
| current camera | `[0x82efc780+0x44]` | TU 0x822aabd0 = PC 0x5e7920 instruction for instruction (focus via vtable +0x48) |
| gameplay camera | `[0x82efc780+0xb50]` (LaraCameraRewrite, vtable 0x82068c60) | manager update 0x822ad048 (PC 0x5f3c70 +0xb80) |
| camera rotation | current camera +0xa0 (x pitch, z yaw, radians); yaw = +0xa8 | vtable slot 0x34 0x822a3968 `addi r3,r3,0xa0`, slot 0x44 0x822a3988 `lfs f1,0xa8(r3)` (PC 0x5e1c60 / 0x5e1ca0) |
| camera position | current camera transform +0x10, row 3 (+0x40) | slot 0x38 0x822a3970 `addi r3,r3,0x10` (PC 0x5e1c70); row 3 = position by data (w = 1.0, equals +0x90) |
| FOV | current camera +0xb0 (vertical radians) | slot 0x40 0x822a3980 (PC 0x5e1c90) |
| recenter clock | gameplay camera +0x1e4 | weight 0x822c20b8 (vtable slot 0x84), look step 0x822c2ca0 / 0x822c2cd4 |
| settings | own id +0x1d0, else `[[0x829ca200]+0x144]`, in doppelganger mode +0x14c; entry `[0x8287ba80+4*id]`, S = entry + 0x20; delay S+0xb4, ramp S+0xb8 | lookup 0x822bc198 |
| Lara yaw | player instance +0x38 | TU 0x8242f990..0x8242f9a8 (PC reads `[[0xe7f094]+0x38]` at 0x752c73) |

**Correction:** the getter PC 0x5e78a0 / slot 0x34 (+0xa0) is the camera ROTATION, not its position (ENGINE.md and
TruMenu 0.22.11 fight.trace called it "position"; TruFight.log 2026-11-10 shows pc_cam_dx = -Lara position, i.e. "+0xa0"
near 0). Proof by data: the TU dump `dlc2_shadow_off_image.bin` gameplay camera +0xa0 = (-0.0061, 0, -3.083) and its
transform rows give the same angles (forward = row 2 = (-sin z, cos z)); camera yaw -176.5 vs bearing camera -> Lara
-177.2 there, and live 2026-11-10 21:48 yaw 25.9 vs bearing 25.9.

Shown on the Lara page / link `lara` (`; camera: obj ..., position, yaw, pitch, FOV, bearing to Lara, Lara yaw, delta,
dist, recenter clock (delay, ramp, weight, settings)`) and in 16 new watch columns. Look-at point: not proven (`?`).

**`--camtrace [PATH]`** (`--camtrace-seconds`, default 120, `--camtrace-interval`, default 0.05): no window, no link -
it may run next to a running TruXenia. One TSV row per sample (`logs/truxenia/cam_<time>.tsv`, a header at every
start) with the columns of TruShadowPower 0.25's `TruCam.log` (CAM_COLS, side `xbox`; the PC-only pad columns `-`).
`tools/cam_compare.py` compares both. Live 2026-11-10 21:49-21:53 (DLC 2 start wall): settings `GI+0x14c id 21237`
(delay 0.25 s, ramp 5.0 s) throughout; the game often sets the clock to delay + ramp (instant recenter) while climbing.

### Attack coordinator (`Ko`)

Proven: MeleeAttack Enter passes brain+0x2fc4 (a requester with the handle {instance +4, stamp +8}) to TU 0x823551b0,
which checks the handle and the target's slot manager +0xf78. TruXenia logs the handle target (`ko_handle`); what the
coordinator grants (slot, order) is still open - `Ko` stays `?`.

### Lock-on path (aiming, 2026-11-10)

For the K-5 comparison (PC: no lock target while LT is held; PC side = TruMenu 0.22.15 `aim.trace` / `TruAim.log`,
ENGINE.md row "Lock-on path"). Address-file section `aim`, 9 proof words: CM = player tracker +0x504, **CM+0x1fc**
shown as bits 9 (soft lock, TU 0x823de858 = PC 0x71ec50) / 10 (lock, TU 0x823de9f0 = PC 0x71edf0) / 11 / 18 / 19 /
20 / 21; **targeter 0** = `[[0x829ca648]+0]`, flags +8, target = node +0x90 -> handle {instance, stamp} (stamp checked
against instance +0x44; TU getter 0x82404568 = PC 0x719f00). Lara page line "Zielen (Lock)", link `lara`, the four
`aim_*` TSV columns. Read only. Not read on the Xbox (offsets not proven there): the pad word, the aim timers
(TU player fields are shifted by +4 around +0x50f / +0x540), the candidate lists.

### Sonar (PDA ping map, 2026-11-14)

Purpose: see on the Xbox whether the DLC 2 sonar shows only the "MAP" placeholder (start unit and `dlc2_*` rooms) and
whether the Xbox hits the same triangle limit as the PC in big DLC 1 areas. PC side: ENGINE.md rows "PDA sonar ...".
Address-file sections `sonar`, `sonar_units`, `sonar_reveal`, `sonar_triangles` (89 proof words, all `"optional"`),
found with `work/xsonar_1411/xsonar_tu.py` in the TU image; both TU dumps match 89 / 89, the retail image 0 / 89.

| Value | TU | Proof (PC twin) |
|---|---|---|
| mode | `[0x829ca5a4]` 0 closed, 1 preparing, 2 building, 3 view, 4 area change | per-frame switch 0x823d6f9c (table 0x823d6fc4: 2 -> stage machine 0x823d2100), open 0x823d5690 sets 1, build end 0x823d21e4 sets 3 (PC `[0xee03c8]`, 0x6e55f0) |
| stage / progress | `[0x827599ec]` (-1 = done) / `[0x82759a80]` | stage machine 0x823d2100 (budget 500) |
| ping radius / view distance | `[[0x829ca5bc]+0xc]` / `[[0x829ca5bc]+0x10]` (+ 4000.0 at 0x8207dfb8) | stage 0 0x823d1a40, draw 0x823d4540 (PC `[0xee03e0]`) |
| map units | `[0x8277b2e8]` array, count `[0x8277b2e0]`; unit 0xc0 B: +2 name, +0x84 key, +0x8c -> {mesh 0, mesh 1}, +0xb0 floor mask, +0xb3 placed; mesh +0x44 faces, +0x48 vertices | lookup 0x823cfd48 (PC 0x6e2a60), draw loop 0x823d467c, unit draw 0x823d26f8 (PC 0x6e3a00) |
| current map unit | `[0x82987d40]`; floor `[0x8297f6e6]` (u8) | open 0x823d5734 (PC `[0xedf254]` / `[0xedf268]`) |
| reveal entries | `[0x8277b2c4]` array, count `[0x8277b2bc]`; entry 0x14 B: +0 key, +4 unit, +8 -> 2 bits per vertex (1 = revealed), +0xc vertex count (u16) | entry getter 0x823cf980 (PC 0x6e27d0), stage 0 decode 0x823d1b64.. |
| triangles per frame | drawn `[0x829ca5c4]`, refused `[0x829ca5c8]`, limit **93571** (`lis 1; ori 0x6d83`; refused when drawn > 93571) | triangle 0x823cf480 (PC 0x6dfa60, same limit), reset per frame 0x823d4560 |

Placeholder = a mesh 0 of 100 faces / 56 vertices without a mesh 1 (the "MAP" letters, workspace
`docs/Befund-Sonar-DLC2-1411.md`). Revealed % = vertices with state 1 / entry vertex count; `-` = no reveal entry (the
sonar keeps entries only while it is open). The counters are reset every sonar frame, so a single read may land
mid-frame - the 2 s maximum is the useful number; `refused` > 0 = limit hit (`LIMIT HIT` in the link answer).
Everything is read only; while the sonar is closed the unit list is empty (the units are freed on close).

## Move log (B3, 2026-11-20)

The Xbox side of TruMenu 0.22.65 .. 0.22.68's move lines, so that the same place can be played in Xenia and on the PC
and the two logs laid side by side. `--movelog [PATH]` (`--movelog-seconds`, default 600, `--movelog-interval`,
default 0.005) writes `logs/truxenia/moves_<time>.log` with TruMenu's time stamp and line format; no window, no link -
it may run next to a running TruXenia. Code: `tools/truxenia_moves.py`; addresses: sections `move_machine`,
`move_tracker`, `move_markup`, `move_input`, `move_time` of the address file (69 proof words, all `"optional"`: a
mismatch turns that section's values into `?`, without machine + tracker there are no lines; both TU dumps 69 / 69,
retail 0 / 69). TU twins: ENGINE.md row "TU move fields".

| Line | Xbox values (TU) | `?` on the Xbox side |
|---|---|---|
| `[Perch]` enter / change / leave, `LIFT` / `DROP` (> 100 u between two samples), the 8-sample ring and the dword diff of gt+0xa00..+0xcff / Lara +0..+0x2ff | machine m = `[[0x829892b0]+0xf10]`, record `[m+0x520]` as index; Lara position +0x20, yaw +0x38; gt+0xa64, gt+0xc94 (box: record id / type, item type, flags PERCH / PILLAR, owner, bone matrix rotated / straight, line points p0 / p1), gt+0xc98 | stick; item id, point count, owner intro id; matrix of a box without owner |
| `[Perch]` P1 - P5 | `[m+0x524]` pending (PC +0x514: target, kinds), `[m+0x24]`, byte `[m+0x54c]` (PC +0x53c), action 52 bits, P5 pillar point p0 + t (p1 - p0) | raw pad A |
| `[Vein]` watch, V1 - V3 (records 455, 1460..1517) | as P1; gt+0x78 is a **byte** (PC logs the dword - the comparison takes its low byte); V2 `power` = condition 1046 itself (TU 0x8246e400) | raw pad A, stick |
| `[Tempo]` (power on: once a second, and on each change) | meter flags bit 0, world `[gt+0x118]`, player `[gt+0x150]` (PC +0x14c), ramp targets 0x827754cc / 0x827754ac, the 7 request slots, meter value, Lara runs / stands (step > 3 u per sample) | HUD fraction, stick |
| `[Jump]` launch+ / launch / re-aim / fly / flight end, `kind` | T+0xa20, target T+0xa64 (box type), flight time T+0x77c, kinds T+0xb00 / T+0xc90 | T+0xaa0, T+0x610, dt, inst+0x2a0, the launch site (`via=?`) |
| `[Press]` | rising bit 0x10 of action 52: record before / now, T+0xb00 / T+0xc90 | mode / catch of the kind, stick, camera yaw, T+0xa60 |

Differences that are not values: TruXenia polls; a sample whose tracker, machine and Lara blocks are byte-equal to the
last one is dropped, so a logged step is one game frame when the poll is faster than the game (lines say "sample"
where TruMenu says "frame"). There is no launch hook: "launch" = T+0xa20 written with a new value outside a flight,
inside a flight a re-aim; "flight end" = z still for 0.3 s (heuristic). PC `drop` lines (calls with v = 0) have no
Xbox twin. "Action 52 = jump" comes from the chart data - the A press must show `PRESSED` live.

🔶 **Villa switch** (+32, bit 0x200, target node; TruMenu `puzzle.pull` and the 16.11. V3 notes) is **not** on the Xbox
side: the script object (`inst+0x60`), its class chain / member table and the Uber node layout are not proven on the
TU. How to prove: find the TU twins of `tlobj::ScriptObj` (PC inst+0x60), the IsA walk 0x5749e0 and the member table
root+0x2c by their PC call pattern, then proof words; instance +0x1c bit 0x200 (ENGINE 5.2) by a TU reader of +0x1c.
Until then `peek <inst> 128` on the link shows the raw instance words.

Compare: `tools/compare_pc_xenia_logs.py --pc <game>/TruMenu.log --xbox ../logs/truxenia/moves_<time>.log --out
../logs/compare_moves.md` (`--pc-since` / `--pc-until` / `--xbox-since` / `--xbox-until` as `HH:MM:SS` or a full stamp;
by default only the PC lines after the last `TruMenu.*loaded` line, `--pc-all` for the whole file). Per tag the events
are aligned by their record signature; a pair is `ok`, `DIFF: <field> pc / xbox`, `PC only` or `Xbox only`.
Tolerances: z / dz 5 u, t 0.02, time scale 0.02, vectors 0.5; pointers only as "0 / set" and "jump target == attach
box"; `?` is never a difference.

## State (2026-11-09)

- First live session 09.11. 17:35-18:10 (hit log, values readable, proof words passed).
- Stage 1b (09.11. evening, offline): record indices, Lara LP / states, enemy positions + flight, MeleeAttack record,
  brain test, kinds + filter, RegenerateDeath LP note, time-scale request slots, object table. `--selftest` passes
  (4 hit lines incl. the RegenerateDeath finisher, link commands, locked `set`, save dry run); both TU image dumps
  pass the 91 proof words. Not yet run live.
- 2026-11-10 (offline): lock-on values (section "Lock-on path"); `--selftest` passes with the new aim line, the TU
  image dump passes 103 proof words (0 mismatches). Not yet run live.
- 2026-11-11: camera values (section "Camera"), `--camtrace`; proof words 139 / 0 mismatches on both TU dumps,
  `--selftest` passes; read live 21:48 (Xenia running, read only) and used by the owner 21:49-21:53.
- 2026-11-14 (offline): `sonar` + `peek` and the Sonar page; 89 optional proof words (both TU dumps 89 / 89, retail
  0 / 89), `--selftest` passes with the sonar / peek checks (incl. refused peeks and '?' for a section with a proof
  mismatch); the DLC 2 dump `dlc2_shadow_off_image.bin` reads mode 0 (closed), no units. Window page not opened
  (Tk code path only reviewed). Not yet run live.
- 2026-11-20 (offline, B3): move log (section "Move log") and `tools/compare_pc_xenia_logs.py`; 69 optional proof
  words (both TU dumps 69 / 69, retail 0 / 69); `truxenia_moves.py --selftest` and `compare_pc_xenia_logs.py
  --selftest` pass, `truxenia.py --selftest` still passes; the comparison parses a real TruMenu 0.22.65 log of
  19.11. (788 / 788 `[Perch]` lines). Not yet run live; villa switch 🔶.
- Open: `Ko` meaning, camera look-at point, units / sections / shaders, Xenia function-trace reader (stage 2).
- TU addresses: ENGINE.md section 13 rows "TU combat addresses", "TU brain shift", "TU TruXenia stage 1b".
