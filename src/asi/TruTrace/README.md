# TruTrace.asi

A **log-only** ASI plugin for the PC `tru.exe` (Steam, image base `0x400000`). It changes nothing in the game: every
hook writes log lines and then runs the original code with all registers, the flags and the x87 / SSE state as they
were. It answers "where do we have to change it?" for open points of the DLC port. Log `TruTrace.log`, options
`TruTrace.ini` `[Trace]` (both next to `tru.exe`). Every category is on by default and rate limited. The one exception
to "changes nothing" is the 0.3.3 diagnostic switch `SkipNullModelDraw=1` (default 0, section 0.3.3).

**Status 0.3: built 2026-11-05 (`work\asi\trace03`), offline self test 17 / 17 (framework; the new hook itself only
runs in the game), byte checks 0.1 51 / 51 + 0.2 55 / 55 + 0.3 8 / 8, not played.** 0.2: built 2026-11-05
(`work\asi\trace02`), self test 17 / 17. 0.1: built 2026-11-04 (`work\asi\trace01`), self test 11 / 11.

## 0.3.3: model instances and the null-model draw (crash tru+0x1b7476, 2026-11-14)

Built 2026-11-14 into `work\asi\trutrace033` (sha256 `eb3a3b4433683ffa9f825dd0534752b832d76d2377e3e7d61ec6dc5a254ee123`,
0 warnings), offline self test 20 / 20, byte checks `work\trutrace033_1411\precheck_trutrace033.txt` 34 / 34 against the
Steam exe and 32 / 32 sites unpatched in the code of both crash dumps; not installed, not played. Why: two DLC 1 starts
with the ported DLC 2 g_pda crashed at tru+0x1b7476 in **0x5b7430** (cdecl: model DTP, world matrix, 0, flag, PCMatrixState), whose path
0x5b7467 takes `[[DTP+0x68]+4]` (the mesh bone table's segment array) when `+0x68` is set, else `[DTP+0xc]`, and reads
`[0+0x20]`. In both dumps the drawn instance is the **`g_pda` object (id 48)**, runtime intro 0x40000008, `+0x54` = the
player; its only model's bone table is `{count 0, segments NULL}`. The `0x1235` read before as a "model id" is
PCRenderModel `+8` = a render resource serial (`[0xa14148]++` in 0x502600; 4661 in one dump, 2624 in the other for the
same model data) - not a section id.

* **`[Trace] ModelInst=1`** (category `modelinst`, own rate limit `ModelInstMaxPerSecond=200`): every InstanceDrawable
  from its ctor `tru+0x1b93e0` (vtable 0x853abc; +4 instance, +0x10 render model instances, +0x14 matrix state):
  `drawable 0x.. (vtable ..) for inst 0x.. obj n <name> intro i at x y z (+0x54 ..); built by <instance init 0x5ba810 from
  intro 0x5bcc30 / birth 0x5bd0f0 / child birth 0x5bd270 / instance clone 0x4d0e50 / ...; inside <intro / birth> of obj
  n called from 0x.. <module> [parent ..]>; k model(s): [0] DTP 0x.. (word0, segments, +0xc, bone table +0x68 {count,
  segments}) PCRenderModel 0x.. (render serial n, not an id) instance 0x..`. A model with NULL segments is written at
  level 0 with ` - NULL SEGMENTS: a draw (0x5b7430) reads [0+0x20]`; otherwise the first drawable per object and unit at
  level 1, the rest at level 2. 3 s after the last drawable of a burst: `summary: n drawables of m objects ...` plus
  `summary part k: id name xN (models) [NULL SEGMENTS]`. The intro / birth hooks (0x5bcc30 / 0x5bd0f0 / 0x5bd270) are
  placed for this too (also with `Spawn=0`); spawn lines still only for `SpawnFilter`.
* **`[Trace] NullModelGuard=1`** (category `nullmodel`): entry hook of 0x5b7430. When the DTP is 0, or `+0x68 != 0` and
  `[+0x68]+4 == 0`, or `+0x68 == 0` and `+0xc == 0`: `NULL MODEL DRAW ahead: 0x5b7430 called from 0x5bbd0b for inst ..
  obj 48 g_pda ..., model 0 of 1: [0] DTP ...; bone table words ...; drawable ..., world matrix .. (pos ..), arg 3 / 4 /
  5; drawable built x s ago by ...; the game reads [0+0x20] next - crash expected (SkipNullModelDraw=0)` - written to
  the file at once (the crash follows on the next instruction). Callers: 0x5bbd06 (drawable = ebx) and 0x5b80af in
  0x5b7fe0 (drawable = esi). Repeats of the same model / drawable: one line per 1000.
* **`[Trace] SkipNullModelDraw=0`** (default): `1` returns from 0x5b7430 for exactly that case without running it (the
  entry hook points `CommonEnter`'s return at a plain `ret`; cdecl, the callers remove the 5 arguments and do not use
  eax). **A diagnostic aid, not a fix**: the matrix state then keeps the previous model's data - the PDA model is drawn
  wrong or not at all. Needs `NullModelGuard=1`.
* Offline proof (both dumps, `work\trutrace033_1411\guard_replay.py`, same reads as the C++): condition TRUE in
  `tru.exe.60720.dmp` (dlc_level1_start, DTP 0x1830e250, bone table 0x208d1e98 {0, NULL}) and `tru.exe.9480.dmp`
  (dlc_caverns, DTP 0x1837e560, bone table 0x20a0c8f8 {0, NULL}); every logged field readable.
* Install: `scripts\windows\Set-TruTrace.ps1 -Install -SourceDir work\asi\trutrace033` (copies the new sample .ini as
  well; an owner-edited .ini is kept - the new keys then take their built-in defaults ModelInst 1, NullModelGuard 1,
  SkipNullModelDraw 0).

| # | TO TEST 0.3.3 | expected |
|---|---|---|
| 1 | install, start the game, read `TruTrace.log` from the last `session start` | `TruTrace 0.3.3` header; `0.3.3: model inst 1 (...), null model guard 1 (...), SkipNullModelDraw 0`; the `hooks:` line names `InstanceDrawable ctor tru+0x1b93e0` and `model draw tru+0x1b7430`; no `fact check ... differs` |
| 2 | load a base-game save, wait 5 s | `modelinst: drawable ... built by ...` lines (Lara `lara_casual` from the init, objects of the unit), then `summary: n drawables of m objects` + parts; no `NULL SEGMENTS` |
| 3 | with the ported DLC 2 g_pda (the crash setup): DLC 1 from the main menu or a chapter | before the crash: a `modelinst` line for `obj 48 g_pda` with `NULL SEGMENTS` (who built it, which birth / caller), then `nullmodel: NULL MODEL DRAW ahead ...` as the last line before the crash |
| 4 | the same with `SkipNullModelDraw=1` (diagnostic only) | the game does not crash at tru+0x1b7476; one `NULL MODEL DRAW ahead ... SKIPPED` line, then `null model draw again ... skipped` every 1000; status line `null model draws n, skipped n`; the PDA model looks wrong / missing - expected |
| 5 | negative: `ModelInst=0`, `NullModelGuard=0` | no `modelinst` / `nullmodel` lines, neither hook in the `hooks:` line; with `Spawn=0` too the intro / birth hooks are gone |
| 6 | play 10 min in a base level | frame rate as before (0x5b7430 runs per model per frame; the hook only reads three words); status `enter faults 0` |

## 0.3.2: progress filter for rewards, jars, pings, grapple walls (P5, 2026-11-13)

Built 2026-11-13 into `work\asi\trace032`, not installed, not played. Only the default of `[Trace] ProgressFilter`
changed (TruTrace.cpp + sample .ini): `checkpoint,breakwall,trigger,door,gate,lever,plate,switch,spawner` + **`_rw_`**
(artifacts / treasures / relics / medipacks: birth, flag change on pick-up, removal), **`weightbreak`** (jars: messages
0x2b hit / 0x11c damage, removal - workspace `docs\Befund-P1-Mittelmeer-Objekte-1311.md` section 2), **`ping_map`**
(sonar ping objects, destroyed by the puzzle's "solved" handler) and **`grapple`** (`tp_ei_grapple_wall`, two runtime
instances per intro 326). 13 of the 16 tokens. An owner-edited .ini keeps its own list. The sound category already has
its switch: **`Sound=0`** places none of its hooks (in Paket R the sound lines hit their rate limit; the sample .ini now
says so). **Stale player machines** (P1-crash follow-up 5, workspace `docs\Befund-DLC1-Absturz-Spinne-1311.md` section 5:
1 190 caught access violations in 11 min in the poll thread's `RD` / `W` after a level change, and nonsense lines
`record -1 [...]`): the teleport snapshot forgets every remembered machine when the player instance changes (level
change, reload) and drops a machine whose owner `+8` is no longer the player; a real level load
(`STREAM_LevelLoadAndInit` from 0x5de02a) clears them too. **New category `ground`** (`[Trace] Ground=1`, owner live
13.11. `dlc_dungeon`: Lara sank 3.4 m into a slanted pillar while TruMenu's fall watch still called it "safe ground"):
what Lara stands on, from the game's own contact result - the player movement collision 0x5dce20 posts its contact
record to the player with `INSTANCE_Post` as **0x1ca** (walkable), **0x1c9** (facing up but steeper than player data
`+0x100e` = 52 deg, 0x5dd4f4) or **0x1c7** (other contact). One line on change (message, contact instance, direction of
the record vector) or when Lara's z moves more than 100 units with the same contact: `ground: walkable (message 0x1ca)
on inst 0x... obj n <name> intro m; record 0x... vector +0x10 x y z (unit ...), +0x1c..+0x2c <5 words>; Lara z ...`.
Field sources (byte checks, a mismatch switches only `ground` off): the record build 0x5dd811 (`+0x10 / +0x14 / +0x18`
scaled vector, `+0x1c` ebx, `+0x20` [esp+0x50], `+0x24` ecx, `+0x28` [esp+0x58], `+0x2c` [esp+0x5c]), the three post
sites 0x5dd877 / 0x5dd89e / 0x5dd8c5, the 52-degree limit 0x5dd4f4, the instance pool `[0xd98f60]` stride 0x2f0
(INSTANCE_Find 0x5b3969) - a record word that is an instance of the pool is named as the contact instance; otherwise
"terrain / no instance in the record". The meaning of the vector and the five words is **not proven** (logged raw so the
next run shows it). Uses the INSTANCE_Post hook also when `Messages=0`. Install: `scripts\windows\Set-TruTrace.ps1
-Install -SourceDir work\asi\trace032`.

| # | TO TEST 0.3.2 | expected |
|---|---|---|
| 1 | start with 0.3.2 and the new sample .ini (or `ProgressFilter` copied), read `TruTrace.log` from the last `session start` | `0.2: ... progress 1 / messages 1 (filter 'checkpoint,...,grapple', 13 tokens)`; `TruTrace 0.3.2` in the header and TruLink `modules` |
| 2 | Mediterranean: break a jar (`*_pt_weightbreak_*`), pick up the artifact it drops | `progress` lines for the jar (message 0x2b or 0x11c, then removal) and for `tp_rw_artifact_spawned` (birth, flag change / removal); `gamedata` bit +0x3ed9x as before |
| 3 | negative: `ProgressFilter=checkpoint` in the .ini | only checkpoint instances again (the .ini wins over the default) |
| 4 | `Sound=0` | no `sound` lines, `hooks:` line without the sound hooks |
| 5 | level change (e.g. DLC 1 start or a chapter load), then 10 min play; TruQoL `exit.log` at the end | no burst of first-chance AVs in the TruTrace worker thread; no `machine 0x... record -1 [...]` lines after the change |
| 6 | `ground`: walk on flat floor, onto a steep slope, onto a moving / object platform; DLC 1 `dlc_dungeon` slanted pillar | `ground: walkable (message 0x1ca)` / `too steep` lines only at a change; on an object the contact instance is named; the pillar: a line `z moved > 100 with the same contact` shows what Lara stood on while sinking |
| 7 | negative: `Ground=0` | no `ground` lines; with `Messages=0` too the `hooks:` line has no INSTANCE_Post |

## 0.3.1: dated log lines (Q107, 2026-11-12)

Built 2026-11-12 into `work\asi\i_1211\TruTrace`, not installed, not played (0.3 is installed since 2026-11-05).
Only the log format and the version text changed (shared helper `src\asi\TruLog.h`): every line of `TruTrace.log`
starts with `YYYY-MM-DD HH:MM:SS.mmm`, and each game process writes one header line
`=== <date time> TruTrace 0.3.1 session start (pid n) ===` (at the first buffer flush). The exported
`TruTraceVersion()` (TruLink `modules`) said 0.2 up to 0.3 - it now says 0.3.1. Hooks and options are as in 0.3 (same
sample .ini). Install: `scripts\windows\Set-TruTrace.ps1 -Install -SourceDir work\asi\i_1211\TruTrace`.

| # | TO TEST 0.3.1 | expected |
|---|---|---|
| 1 | start the game once with 0.3.1 installed, read `TruTrace.log` from its last `session start` line on | header and `loaded` line name 0.3.1; every newer line starts with the date (`2026-11-..`); the time matches the other plugin logs of the same start; TruLink `modules` shows `TruTrace 0.3.1` |

## Categories

| INI key | Question | Source of the lines |
|---|---|---|
| `Sound` | Which sound keeps playing after the wall run (groan loop), who started it, was it ever stopped? | entry + result hook on the emitter create `tru+0x1935d0` (callers: anim event sound branch `tru+0x1b99c0`, sound by id `tru+0x1953e0`, play wrappers), emitter end = vtable `0x851240` slot 0 (`0x590920`), instance sound list release `tru+0x18d740`, fixed-slot stop `tru+0x189820(mode)`; `LONG` = emitter alive after `SoundLiveMs`, `REPEAT` = same sound started `SoundRepeat` times in 10 s |
| `Teleport` | Player state before / after a position jump (TruMenu "Zur Marke", unstuck) | poll thread: instance +0x20, chart record of `gameTracker+0xf10` with its Lara state ids, `gameTracker+0xa64` / `+0xc94`, instance +0x14, `[0xfada74]`; follow-ups after 0.25 / 0.5 / 1 / 2 / 3 s |
| `Chart` | Which call changes the player's state | transition `tru+0x387890` (old -> new record, caller), reset `tru+0x3874d0`, start `tru+0x387e00` - player machines only; level 1 inside the teleport window |
| `PowerMessages` | Who receives 0x1f4 / 0x1f5 | wake `tru+0x1b2de0` called from `TruShadowPower.asi` (it wakes every receiver right before the message); message number from `TruShadowPowerMeterApi` flags bit 0; instance +0x14 0.5 s later |
| `Spawn` | Spawn requests and why one is refused (hall02 thralls) | intro `tru+0x1bcc30`, birth `tru+0x1bd0f0` / `tru+0x1bd270` with result; objects whose name contains `SpawnFilter` (default `thrall`) |
| `Object858` | When does the object table entry of 858 change state | poll of table `0xdb7400` (state +0xe, object +8, data +0x5c type) |
| `TimeVector` | Does the shader clock stand still while the world is frozen | RenderDevice `[0xa1407c]` +0xfa4c / +0xfa48, `[0xe7f188]`, `[0xdb94de]` once per `TimeVectorMs` |

0.2 (why does a level load put the player somewhere else?):

| INI key | Question | Source of the lines |
|---|---|---|
| `Level` | Which unit was requested, by whom, which unit was loaded, where was the player put and why | `GAMELOOP_RequestLevelChangeByName` `tru+0x1df8c0` (name, doneType, caller / module; ignored while `gameTracker+0xb9` is set), poll of `gameTracker` `0xe7f088` +0x38 / +0xb8..+0xbb, `STREAM_LevelLoadAndInit` `tru+0x1d30d0` (requested name -> unit entry; also reached from `STREAM_MoveIntoNewStreamUnit` through `[0x8aa840]`), the player placement `tru+0x1d40c0` (game data `[0xc59264]` +0x90 checkpoint id, +0x114 when +0x1f4 != 0 -> the intro with that id +0x58 in the loaded unit, else a `checkpoint` / `invis_checkpoint` intro by the unit's default index; position copy `0x698180`, spawn `0x5bd080`; no checkpoint intro -> `SAVE_SaveGame(0)`), `STREAM_MoveIntoNewStreamUnit` `tru+0x1c1bf0` |
| `Portal` | Which stream portal moved the player into another unit | `tru+0x1d2aa0` (instance, portal; record = `[[unit data]+4] + portal+0x14 * 0x100`, target unit +0x84) - the player's at level 1 |
| `StreamUnits` | Which units are loaded / unloaded when | poll of the stream unit table `0xdbab40` (32 x 0xd8: +0 id, +4 state, +0xc name) |
| `Save` | When is a checkpoint written, with which unit / checkpoint id; what does a restore bring back | `SAVE_SaveGame` `tru+0x1570f0` (callers: checkpoint message handler `0x6a1a70` - logs the checkpoint instance -, gameloop `0x5dfba0`, the placement's tail jump), `SAVE_RestoreGame` `tru+0x157130` with the result; poll of +0x10 / +0x90 / +0x114 / +0x1f4 in the active block and the checkpoint copy `[0xc59268]` |
| `Progress`, `ProgressFilter` | Which checkpoint / trigger / wall instances appear, go or change flags | poll of the active instance list `0xd98d54` (+8 next): births, removals, +0x14 / +0x18 changes of objects whose name contains a filter token |
| `Messages` | Which messages reach those instances | `INSTANCE_Post` `tru+0x1b3750` (instance, message, data) to ProgressFilter objects |
| `Ground` (0.3.2) | What Lara stands on | the contact messages 0x1ca / 0x1c9 / 0x1c7 of the movement collision 0x5dce20 to the player (same INSTANCE_Post hook), on change |
| `GameData`, `GameDataMs` | Which game data bytes change (progress flags) | diff of the active save buffer `[0xc59258]` (0x140000 bytes) every `GameDataMs`; a word changing in 8 polls in a row is muted |

0.3 (F5 follow-up: which fixed sound slot plays "sound 20212"?):

| INI key | Question | Source of the lines |
|---|---|---|
| `SoundSlots` (needs `Sound`) | Which object sound slot started / stopped an emitter, with which mode and parameter | entry + leave hook on the slot play `tru+0x193d50` (thiscall, `ecx` = the instance sound list `[inst+0x248]`: +0 owner, +4 slot count, +8 slot table of {SoundPlex node, s16 default parameter}, +0xc handles), reached only from the anim event dispatcher `tru+0x1b69c0` (type 0x60, call `0x5b6a30`): `SLOT STARTED / already playing - not restarted / stop mode 4 sent / dead handle released` with owner instance, slot, mode (1 start only when the slot has no live emitter, 0 stop), p3 (word -> emitter +0x44), p4 (0xff = the slot's default parameter), node + its section id, emitter / sound before and after, the dispatcher's caller (`0x5b9fe8` = anim event kind 2) and the payload bytes +4 / +5. The same (owner, slot, mode, result) is logged at level 1 the first 5 times and every 20th time, else at level 2. Emitters started there carry `fixed slot N of <instance>` in their START / REPEAT / LONG / END lines |

No generic "trigger fired" / script event point was proven statically; `Progress` / `Messages` / `GameData` log the
effects instead.

Every line: `time [stream unit] category: text`. A status line every 60 s counts the hook calls and any framework
fault (should stay 0).

## Safety

* Every hook site and every fact the decoding relies on is byte-checked at load (list in
  `work\asi\trace01\precheck_trace01.txt` 51 / 51, `work\asi\trace02\precheck_trace02.txt` 55 / 55 and
  `work\asi\trace03\precheck_trace03.txt` 8 / 8, offline `tools/pe_bytes_check.py`); a mismatch switches that category
  off and is logged (0.3: a slot-play fact mismatch switches only `SoundSlots` off). The plugin loads after the other
  `Tru*.asi` (alphabetical), so it sees their patches. 0.2 never hooks a site another plugin patches; it hooks entries
  that TruMenu (`0x5df8c0`, `0x5c1bf0`, `0x5b3750`), TruLink / TruShadowCombat (`0x5b3750`) only byte-check in their
  own start, and the placement `0x5d40c0` whose body TruDlc2Player patches at `0x5d42e9` (not checked by TruTrace).
* Hooks: a 5-byte `jmp` over position-independent prologue instructions (relocated into a trampoline) or a vtable slot;
  results through a per-thread shadow stack of return addresses (matched by the stack pointer).
* Lines are buffered and written by the poll thread every 100 ms - no file access on the game thread.
* Not in `tru.exe` (self test host): nothing is hooked.

## Self test

`SelfTest.cpp` (build line in its header) loads the plugin outside the game and calls `TruTraceSelfTest`: the same
framework on the plugin's own test functions (cdecl, thiscall `ret 0xc`, float in st0, recursion depth 6, vtable slot,
`GetLastError` kept, 1000 calls; 0.2: 7-byte prologue, prologue with an absolute `mov eax, [abs]`, `push esi; mov
esi,[esp+8]`, and a hooked function tail-jumping into another hooked one - both leaves on the same stack slot, as the
placement `tru+0x1d40c0` jumps into `SAVE_SaveGame`).

## Exports

`TruTraceVersion()`, `TruTraceSelfTest(buf, size)` (offline only, refuses inside `tru.exe`).
