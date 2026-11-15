# TruLink.asi

Live read / write channel into the running `tru.exe` (PC, Steam, image base 0x400000) for our tests. It replaces
the earlier channel through a cdb command file: a small TCP server inside the game process answers a line-based text
protocol that is easy to drive from PowerShell (`scripts\windows\Invoke-TruLink.ps1`).

Version 0.3 - built and checked with `dumpbin` only, not yet tried in the game (0.2 works in the game). 0.2 added the
`menu` command: every item of TruMenu.asi (in-game debug menu) can be listed and run by its id without the controller.
0.3 adds a Cheat-Engine-style memory search (`scan`), polled watches (`watch`) and struct snapshots (`snapshot` /
`diff`) to find unknown values (health, ammo, walking speed) live without a debugger - see
[Memory search](#memory-search-03).

## 0.4: live objects - inspect, change, undo (2026-11-15)

Built 2026-11-15 into `work\asi\trulink04` (sha256 `e0e142a2b65c93046620ac2a1e137a4d447bb582d5ed4846e18429670bad6bd0`,
`TruLink.ini` unchanged), **not installed, not tried in the game**. Install (game closed):
`scripts\windows\Set-TruLink.ps1 -Install -SourceDir work\asi\trulink04`. Commands, safety and the live test:
[Objects (0.4)](#objects-04). Offline: the decoders ran on the full dump of 2026-11-15 20:07 (`l3_chapel`), all 81
byte check rows match the Steam `tru.exe` and that dump's image (`scripts\windows\Test-TruLinkObj.ps1`).

## 0.3.1: dated log lines (Q107, 2026-11-12)

Built 2026-11-12 into `work\asi\i_1211\TruLink`, not installed, not played. Only the log format and the version
changed (shared helper `src\asi\TruLog.h`): every line of `TruLink.log` starts with `YYYY-MM-DD HH:MM:SS.mmm`, and each
game process writes one header line `=== <date time> TruLink 0.3.1 session start (pid n) ===` before its first line;
`ping` answers `pong TruLink 0.3.1`. Commands are as in 0.3. Install:
`scripts\windows\Set-TruLink.ps1 -Install -SourceDir work\asi\i_1211\TruLink`.

| # | TO TEST 0.3.1 | expected |
|---|---|---|
| 1 | start the game once with 0.3.1 installed, `Invoke-TruLink.ps1 ping`, then read `TruLink.log` from its last `session start` line on | `pong TruLink 0.3.1`; header and `loaded` line name 0.3.1; every newer line starts with the date (`2026-11-..`); the time matches the other plugin logs of the same start |

## Safety

- The server binds **127.0.0.1 only** (`INADDR_LOOPBACK`, never `0.0.0.0`) with `SO_EXCLUSIVEADDRUSE`; accepted peers
  outside 127.0.0.0/8 are closed (cannot happen on a loopback socket, checked anyway). It is reachable from the
  network by no route; every program of the logged-on user on the same PC can use it.
- Default port **9265** (`TruLink.ini`, `Port`). 9264 is FMOD's profiler port (docs `Befund-Entwicklerkanal.md`) and is
  refused.
- It is a **test tool**: `Enabled=1` is the default of our test builds. Remove it with `Set-TruLink.ps1 -Remove` or set
  `Enabled=0` when not testing.
- One client at a time; a second connection gets `err busy: another client is connected` and is closed.
- Memory reads and writes are wrapped in `__try / __except` (an access fault answers `err ... access fault (caught)`)
  and checked before with `VirtualQuery` region by region (no `IsBadReadPtr`):
  - allowed without `force`: the `tru.exe` image and private memory (`MEM_PRIVATE`: heap, `VirtualAlloc`, stacks -
    where the game's instances and objects live);
  - needs a trailing `force`: other modules' images (system DLLs, other plugins) and mapped files, and writes to
    read-only pages outside the `tru.exe` image; `AllowForce=0` in the ini refuses `force` altogether;
  - never: uncommitted, `PAGE_NOACCESS` or guard pages.
- Writes to read-only pages (code in `tru.exe`) go through `VirtualProtect` (restored afterwards) and
  `FlushInstructionCache`. The write happens on the server thread while the game runs - patch code only where the
  game thread cannot be executing it at that moment (or accept the race). Every write answers with the old bytes
  (`was ...`) so it can be undone, and is logged at LogLevel 1.
- Game functions (`camera`, `post`) are called only after their first bytes matched at load (status line `checks`).

## Protocol

One command per line (`\n`, `\r\n` accepted), ASCII, case-insensitive command names, tokens separated by blanks.
Lines that are empty or start with `#` get no answer. A trailing `force` token sets the force flag.

Answers:

- one line starting with `ok `, `err ` or (for `ping`) `pong `;
- or a block: a first line starting with `ok+ `, then data lines, then a line holding only `.`.

Addresses: hex with or without `0x`, or a name - `player` (the player instance `[0xe7f094]` = GameTracker+0xc),
`gametracker` (0xe7f088), `cheat` (GameTracker.cheatMode byte 0xe7f144), `camera` (current camera `[0xe80534]`),
`cameramgr` (0xe804f0), `playerstate` (`[0xfadb58]`) - optionally followed by `+hexoffset`, e.g. `player+0x20`.
Numbers (`len`, `value`, `msg`, `data`, `mode`): `0x...` hex, otherwise decimal (negative allowed).

| Command | Answer | Thread |
|---|---|---|
| `ping` | `pong TruLink 0.3` | server |
| `help` | block: command list | server |
| `status` | block: version / port / log level; hook on/off, the slot `[0x00a02b8c]`, the pointer TruLink calls (`next`), XInputGetState (`real`), TruLink's hook (`self`), each with its module; pad calls, frames, ms since the last call, re-entries; code checks | server |
| `read <addr> <len> [force]` | `ok 0x00e7f144 4 01000000` (len 1..4096, bytes as hex) | server |
| `read32 <addr> [force]` | `ok 0x00e7f144 0x00000001 1` (hex, signed decimal) | server |
| `readf <addr> [force]` | `ok 0x... 1 0x3f800000` (float, raw dword) | server |
| `write <addr> <hexbytes> [force]` | `ok wrote 1 at 0x00e7f144 was 00` (bytes may be split over several tokens, up to 1024) | server |
| `write32 <addr> <value> [force]` / `writef <addr> <float> [force]` | as `write` | server |
| `player` | `ok instance 0x... pos x y z` (instance +0x20) or `ok none (GameTracker +0xc is 0)` | server |
| `camera` | `ok current 0x... mode m` (mode = index of the slot `[mgr+4+4*m]` holding the current camera, -1 = none) | server |
| `camera <mode>` | `CAMERA_SetMode(mode)` 0x5f39f0, then `ok done, current ...`. Retail switches only for 6, 11 (free camera, as TRLAU-menu-hook) and 12; other modes return unchanged | game |
| `camera restore` | camera restore 0x5edf50 (thiscall on the CameraManager 0xe804f0, how TRLAU-menu-hook leaves its free camera) | game |
| `post <instance> <msg> <data>` | `INSTANCE_Post(instance, msg, data)` 0x5b3750 (cdecl); refused when the instance is not readable up to +0x124 or its handler +0x120 is 0. Example: `post player 12 1` = the "skew" cheat message of TRLAU-menu-hook | game |
| `objects` | block: `index id state object` of every used entry of the object table 0xdb7400 (0xcc entries of 0x24 bytes, +0xc id, +0xe state, 2 = loaded, +8 object) | server |
| `modules` | block: every loaded `.asi` with base, size and the string of its exported `<Name>Version()` (or `-`), then our known plugins that are not loaded | server |
| `menu list` | block: one line per TruMenu item, tab separated `id type value label` (from `TruMenuList()` of TruMenu.asi); `err no TruMenu` when TruMenu.asi is not loaded | server |
| `menu <id> [arg]` | runs the TruMenu item `<id>` through `TruMenuInvoke(id, arg)` (the rest of the line is `arg`), e.g. `menu level.load dlc_level2_start`, `menu cheat.flight 1`, `menu overlay.position`; the answer is TruMenu's `ok ...` / `err ...` line. Items that touch the game are run by TruMenu on its own game-thread hook (it waits up to 3 s); see `src\asi\TruMenu\README.md` for the ids. TruMenu 0.5 TO TEST list: `menu test.step <n> <id\|id:arg\|-> <text>`, `menu test.toggle <id> <item\|ini:Plugin:Section:Key> <text>`, `menu test.add <id> <hint>` (checks), `menu test.mark ...`; `menu test.export` is a block answer (`ok+ test.export ...`, one tab-separated line per row, `.`) - TruLink passes TruMenu's answer through unchanged | server (TruMenu: game) |
| `scan <type> <op> ...` | first scan, see [Memory search](#memory-search-03): `ok scan float range align 4: 81234 candidates in 412 regions 389.5 MB, 610 ms` | server |
| `scan next <op> [value]` | refines the candidate set: `ok scan float next decreased (pass 2, from 81234, 12 unreadable dropped): 517 candidates, 9 ms` | server |
| `scan list [n]` | block: the first n (default 20, at most 500) candidates `address current previous-scan` | server |
| `scan status` / `scan clear` | one line: type, align, tol, count, passes / frees the candidate set | server |
| `scan regions [n]` | block: the searched regions (first n, default 40) `start size kind protection`, then `total <regions> <MB>` | server |
| `watch add <addr> <type> [name] [force]` | `ok watch #0 hp 0x... float = 100 (polled every 100 ms)`; at most 32 watches, name default `w<index>` | server |
| `watch del <name\|#i\|addr\|all>` / `watch list` | removes / block `#index name address type value changes` | server |
| `watch log [n]` | block: the last n (default 50) of up to 1024 events `ms-ago game-clock name address old -> new` | server |
| `snapshot <name> <addr> <len> [force]` | `ok snapshot p 0x... 2048 bytes` (len up to 4096, 16 snapshots); `snapshot <name>` takes it again at the same address; `snapshot list`, `snapshot del <name>` | server |
| `diff <name> [update]` | block: every changed dword since the snapshot `+offset address old new f:old f:new i:old i:new` (at most 400 lines); `update` makes the current bytes the new baseline | server |
| `obj.near`, `obj.info`, `obj.set`, `obj.journal`, `obj.undo`, `uber.events`, `uber.send`, `sticky.get`, `sticky.set`, `joint.get`, `joint.drive` | 0.4, see [Objects (0.4)](#objects-04) | game |
| `log <0-3>` | `ok log level n` (TruLink.log; not saved) | server |
| `quit` / `exit` / `bye` | `ok bye`, connection closed | server |

Game-thread commands wait up to `GameThreadTimeoutMs` (default 5000) for the next pad poll. If the game thread does not
poll (loading, hook not installed or bypassed by another plugin), the job is taken back and the answer is
`err timeout: ...`; a job the game thread had already started is waited for (30 s more).

## Memory search (0.3)

A value search in the style of Cheat Engine, run on the server thread (the game thread is never stopped).

**Searched memory** (VirtualQuery region by region): `MEM_COMMIT` with a writable protection (`PAGE_READWRITE`,
`PAGE_WRITECOPY`, `PAGE_EXECUTE_READWRITE`, `PAGE_EXECUTE_WRITECOPY`), no guard and no no-access pages, and either
`MEM_PRIVATE` (heaps, `VirtualAlloc`, stacks) or inside the `tru.exe` image (its writable sections `.data` / `.bss`).
Skipped: other modules' images (system DLLs, our plugins incl. TruLink itself), mapped files, TruLink's own candidate
arrays and the server thread's stack. Memory is copied in 64 KB chunks under `__try` (a faulting chunk is skipped and
counted); every 4 MB the thread yields (`Sleep(0)`) and polls the watches. `scan regions` shows what would be searched.

**First scan** - `scan <type> <op> [values] [options]`, replaces any earlier candidate set:

- types `u8 s8 u16 s16 u32 s32 float` (`f32` = float); integer values decimal or `0x` hex, negative allowed (cut to
  the type: `-1` as `u8` = 255);
- ops `eq <v>`, `ne <v>`, `gt <v>`, `lt <v>`, `range <lo> <hi>` (inclusive), `unknown` (keeps every value - for float
  only finite ones);
- options `tol <x>` (tolerance of every compare; default 0.001 for float, 0 for integers), `align 1|2|4` (default the
  type size), `at <addr> <len>` (search only `[addr, addr+len)`, addr may be a name such as `player`).

**Refine** - `scan next <op> [value] [tol x]`: every candidate is read again (VirtualQuery per region, guarded read;
unreadable ones are dropped) and compared with the value of the previous scan, which is then replaced by the current
one: `eq / ne / gt / lt <v>`, `range <lo> <hi>`, `changed`, `unchanged`, `increased` (`inc`), `decreased` (`dec`),
`inc_by <v>`, `dec_by <v>` (difference = v within the tolerance). Integers compare as their type (`u8` 255 -> 0 is a
decrease).

**Limits**

- At most `ScanMaxCandidates` candidates (default 4 194 304 = 32 MB, 8 bytes each, committed in 1 MB steps; at most
  16 M in the ini). A first scan that hits the cap stops and answers `TRUNCATED` - the set then covers only the low
  addresses. `unknown` over all memory always truncates (hundreds of MB of writable memory = tens of millions of
  dwords): use a value op (`range 1 1000` rules out the many zeros) or restrict it with `at`.
- A first scan stops after `ScanMaxSeconds` (default 60) with a partial set (`STOPPED`).
- Speed (estimate from the code, not measured in the game): a first scan with align 4 does a 64 KB copy plus one
  compare per position, roughly 0.5 - 1.5 GB/s, i.e. well under a second for the few hundred MB of a typical session;
  `align 1` / `u8` about four times slower. `scan next` costs one guarded read per candidate, roughly 0.1 - 0.3 s for
  4 M candidates. Each answer reports its time in ms.
- Values that cross a region end are not found; reads race with the game (a value may change during the copy).
- `Invoke-TruLink.ps1` waits up to `-ScanTimeoutSeconds` (default 120) for `scan` answers.

**Watches** - `watch add <addr> <type> [name]` (the address is resolved once, e.g. `player+0x150`). The server thread
reads every watch each `WatchIntervalMs` (default 100) - also between the chunks of a running scan - and records every
change (and unreadable / readable again) in `TruLink.log` (LogLevel 1) and in a ring of 1024 events (`watch log`).
Values that change every frame (positions) fill the log quickly; delete such watches when done.

**Snapshots** - `snapshot <name> <addr> <len>` copies up to 4096 bytes; `diff <name>` lists every dword that changed
since, as hex, float and signed integer, with the offset into the snapshot. `diff <name> update` moves the baseline.

### Recipe: find health / ammo / walking speed

TruLink takes no comments at the end of a command line; the `#` lines below are comments on their own line (skipped by
`Invoke-TruLink.ps1 -Script`), the steps in brackets happen in the game.

Health (type unknown - most likely a float; TRU shows a bar, no number, so search by direction):

```text
# full health; if the answer says TRUNCATED, add: at <addr> <len>
scan float range 1 100000
# (take damage)
scan next decreased
# (wait a moment without damage)
scan next unchanged
# (take damage again)
scan next decreased
# (heal: medipack)
scan next increased
# a handful left: look at them, confirm one live
scan list
watch add 0x0a1b2c3c float hp
watch log
```

Not found as float: the same with `s32`, `s16` or `u8` (`scan s32 range 1 100000`).

Ammo (an integer that the HUD shows, e.g. 30): `scan s32 eq 30`, fire one shot, `scan next eq 29` (or
`scan next dec_by 1`), reload, `scan next eq 30`. Try `s16` if `s32` finds nothing.

Walking speed / a field of the player: compare the player instance itself first.

```text
# standing still
snapshot p player 0x1000
# (walk) - every dword that changed: position, velocity, animation, timers ...; update = new baseline
diff p update
# (stop walking) - compare again
diff p
# or search inside the instance
scan float unknown at player 0x1000
# (walk)
scan next changed
```

Pointers found in the instance (`i:` values that look like addresses) can be followed with another
`snapshot` / `scan ... at <pointer> <len>`.

## Objects (0.4)

A general live channel to look at and change objects (puzzles, positions, switches, script values) while playing,
without a new build per question. Everything here runs as **one job on the game thread** (the pad-poll hook, like
`camera` / `post`): the server thread parses the line, the game thread resolves the instance, reads, writes and fills
the answer - no read races the instance list, every write happens where the game itself writes. The decoders are pure
memory reads in `TruLinkObj.h`, shared with the offline test `selftest\TruLinkObjTest.cpp` (same code on a full
minidump). Every layout and every called function is a byte check row (81 rows in 10 groups, `status` line
`0.4 checks`); a command whose group failed answers `err byte checks '<group>' failed`.

`<id>` = intro id (decimal), `0x<instance>` (must be in the instance list), `#<list index>` or `player`. Distances: the
radius is given in metres at **~290 units per metre** (ENGINE 4.3, not proven exactly); the answers show both.

| Command | Answer |
|---|---|
| `obj.near [m] [filter] [max n]` | block, nearest first (default 10 m, at most 500 m / 400 rows): `#index instance intro obj name unit name pos dist (m)` plus `uber '<node>'` (`-> '<target>'` while a transition runs), `multibody links n`, `hidden`, `kill`, `parent <intro>`. Filter: `uber` (only uber states), `multi` (only multibody placed instances), or a part of the object name |
| `obj.info <id>` | block: intro id (placed / runtime and whose intro record it carries), object, list index, stamp `+0x44`; unit `+0xe0` / birth unit `+0xe4`; pos `+0x20` (and the start-of-frame copy `+0xc0`), rot `+0x30` (rad + deg); iflags `+0x14` / `+0x18` / `+0x1c`, no-draw masks; intro record (pos, rot, **scale `+0x40`**, object, unique id, data); intro data `+0x104`, parent `+0x54`, child / sibling `+0x218` / `+0x21c`, link parent id `+0x228`; models; process / message handlers; **script members** of the instance's own script type with their type (`instanceref` -> intro id + name, `stickybool` / `stickyint` / `stickyfloat` -> key + store value, others raw); **multibody**: links (part instances + uber node), joints (type, value, limits, limit / motor bits, motor velocity / force), command table; **uber state**: node, running transition, time, flags and the whole graph (every node with its transitions and conditions, joint ranges with the joint index) |
| `obj.set <id> pos x y z` / `move dx dy dz` / `rot x y z` (degrees) / `yaw deg` | writes `+0x20` / `+0x30` (journaled). Notes in the answer: a multibody placed instance is only the hidden anchor (move a part = a link), an instance with a physics body `+0x274` may be put back by the solver |
| `obj.set <id> hide 0\|1` | `INSTANCE_Post(id, 7, 1 / 0)` - the game's own hide / unhide (default handler 0x5b4110: `+0x14 \|= 0x40800`, `+0x18 \|= 0x20000000`; the multibody handler 0x4d14d0 does it for every part). Journaled with the old state |
| `obj.set <id> collide ...` / `scale ...` | **refused**: no proven collision switch and no per-instance scale field (only the intro record's scale, read at birth 🔶) |
| `obj.journal [clear]` | block: every 0.4 change `#n kind what old -> new` (at most 256; full = writes refused until `obj.undo all` / `clear`) |
| `obj.undo` / `obj.undo all` | undoes the last / every change, newest first, after checking the instance is still the same (stamp `+0x44`, intro id, in the list): pos / rot written back, hide = message 7 with the old state, sticky = the old value through the game's set + notification; `uber.send` is **not undoable** (the game's logic ran - passed with a note); a `joint.drive` entry stops the drive (the joint stays where the physics left it) |
| `uber.events <id>` | block: the current node of the uber state (or of every link of a multibody placed instance): each transition with its target and how to fire it (`command c`, `event v`, `broadcast v`, joint range with the joint index and its value, time, object check, damage ...); then the **command table** of the multibody: `cmd n.r: link k (intro, node) <kind> <value> -> '<node it would reach now>'` or `(no transition in this node now)` |
| `uber.send <id> cmd <n>` | entry n of the object command table through the multibody's own vf+4 = **0x4d77a0** - the same call uber action 11 makes (0x4d886d) and the path a lever / plate command takes; it delivers each record with 0x4d7680 to the linked uber. Answer: every target link's node before -> after |
| `uber.send <id> command <c>` / `event <v>` / `broadcast <v>` `[link k]` `[force]` | one uber message through **0x4d7680** (kind 4 / 2 / 3: cond 16 with arg c / cond == v / cond 13 with arg v). For a multibody placed instance the link is taken from `link k`, else the only link whose current node takes the message. Refused without `force` when the engine would drop it (transition running, `+0x90 & 9`) or no transition of the node matches. Set-node (kind 1) is refused: it is not the event path |
| `sticky.get <owner> <key>` | `ok sticky 0:<owner> key <k> (...) = bool 1 (index n)`. Owner = intro id (kind 0) or `<kind>:<id>`; key = the Symbol, or a script member of the owner's instance: `m<index>` / `+<offset>` (from `obj.info`; the key is the member's init word, the owner the script's owning instance) |
| `sticky.set [int\|bool\|float] <owner> <key> <value>` | an existing entry only: the store write + the game's change notification (0x4af740 / 0x4af6d0 / 0x4af7b0, as TruMenu `sticky.set`), journaled with the old value |
| `joint.get <id> <index>` | block: the joint line (as in `obj.info`) and every joint-range transition on this joint in every linked uber (node, target, enter / leave, range) |
| `joint.drive <id> <index> <target> [speed s] [force f] [hold s] [through 1]` | drives a hinge (degrees) / rail (units) with **the joint's own motor**, limits untouched; see below. `joint.drive status` / `joint.drive stop` |

**joint.drive (safe drive).** TruMenu 0.22.53 `joint.set` locked lo = hi = target; on 2026-11-15 20:28 that replaced
the shadow door rail's limits [0, 948.2] and the door went to -1115. `joint.drive` never writes the limits:

- the target is clamped inside the joint's limits (limit bit on, lo < hi; 1 degree / 2 units inside); a joint without
  limits moves at most 180 degrees / 3000 units per drive;
- each game frame the motor velocity (axis 0, 0x4da160; hinge in rad/s) is set proportional to the rest (2 /s), at
  most `speed` (default 30 deg/s or 150 units/s), at least 10 % of it, with the force `force` (default 20000, the
  order of the engine's own hinge / rail motors in the chapel door; at most 1e6), motor on (0x4da0c0), both bodies
  woken (0x4d8fd0);
- it stops and puts the saved motor velocity / force / enable back on: reached (then `hold` s at velocity 0, default
  2), moving away from the target by more than 3 degrees / 10 units (the motor sign is not proven: one sign flip is
  allowed and logged, the second time it stops), overshoot by 2 degrees / 5 units, a step larger than 4x the commanded
  speed, leaving the limits, no progress for 1.5 s, **a node change of any linked uber** (the game reacts; its node
  actions own the joint from then on - `through 1` goes on and logs it), 10 s, `joint.drive stop`, unit change;
- the saved settings are only put back while the joint still carries our force (a node action may have set its own).
  Every tick (the first 20, then every 10th, at most 300) is a log line.

**Journal / log.** Every change is a `TruLink.log` line (LogLevel 1) with the old and new value and its journal
number; `obj.journal` lists them, `obj.undo` reverts them. Nothing of it is saved.

**Offline test** (no game): `scripts\windows\Test-TruLinkObj.ps1 -Dump <full tru.exe dump> [-Command 'near 15;info
4820;events 4835']` builds `TruLinkObjTest.exe` and runs `checks` against `tru.exe` and the dump image, then the
decoder commands on the dump (joint values need the engine's getter: `n/a` offline). 2026-11-15: dump 20:07
(`l3_chapel`, 213 instances) - all 81 rows match, `obj.near` / `obj.info` / `uber.events` / joints / stickies decode
(shadow pillars 4837: 6 links, 6 commands, 5 stickybools with store values, instancerefs to the four wall switches
4819 - 4822; shadow door 4835: 6 links, 8 joints, commands 0 / 1 = command 1 / 0 to the lock links 3 / 4); dump 19:48
(no level) - the "needs a level" refusals.

### TO TEST 0.4 (live, `l3_chapel`, at the shadow pillars / shadow door)

Start with `Set-TruLink.ps1 -Install -SourceDir work\asi\trulink04`, load the chapel, stand near the wall switches.

| # | TO TEST | expected |
|---|---|---|
| 1 | `ping`, `status` | `pong TruLink 0.4`; `0.4 checks (81 rows, 0 bad ...)` with every group 1 |
| 2 | `obj.near 15`, `obj.near 60 uber` | the switches 4819 - 4822, the pillars 4837 (multibody) and their runtime links with node names (`position_a` ...) |
| 3 | `obj.info 4820` | 3 instancerefs: 4802 cameraanchor_object, 4837 ma_uo_shadow_pillars, 4834 ma_rb_press_plate |
| 4 | `uber.events 4837`, press wall switch 4820 in the game, `uber.events 4837` again | one link moved one position; which `cmd n` predicted it (the switch's command) |
| 5 | `uber.send 4837 cmd <n>` (the n of row 4), `obj.journal`, `obj.undo` | the pillar turns like with the switch; journal row `uber`; undo answers "not undoable - passed" |
| 6 | `sticky.get 4837 m1` ... `m5` | the pillar stickybools (m1 = 1 in the dump) |
| 7 | `uber.events 4835`, then `uber.send 4835 cmd 0` and `uber.send 4835 cmd 1` | links 3 / 4 `locked -> unlocked`; then link 2 `start -> turn` (object check) = the shadow door opens the game's way |
| 8 | `joint.get 4835 2`, `joint.drive 4835 2 5`, `joint.drive status` | rail value near 0, limits [0, 948.17]; the drive reaches ~5 (or stops with a reason in `TruLink.log`), motor settings back; the door never leaves [0, 948.2] |
| 9 | `joint.drive 4835 2 -200` | `target -200 clamped into the limits -> 2.00`; no move below 0 |
| 10 | `obj.set 4820 hide 1`, `obj.undo` | the switch disappears / comes back; iflags 0x800 set / clear |

## Threading

- **Server thread** (created at load; `WSAStartup` runs there, not in `DllMain`): non-blocking listening socket,
  `select` every 100 ms (`WatchIntervalMs`, at most 250), one client socket (blocking sends with a 5 s timeout). All
  memory commands run here, including `scan` (while a scan runs, the next command waits for it) and the watch polling.
- **Game thread** (0.4: also every object command and, once per game frame, the `joint.drive` tick): `camera` and
  `post` are put into a one-slot job (`queued` -> `running` -> `done`, interlocked) and
  executed inside TruLink's pad-poll hook, i.e. once per poll on the thread that runs the game's frame. A fault inside
  the game function is caught and answered as `err`.
- **Hook thread**: installs and watches the pad-poll hook (below), every 100 ms until installed, then every 500 ms.

## Chaining the pad-poll hook

The game polls the pad once per frame on the game thread through `call dword ptr [0x00a02b8c]` at tru+0x84b82; the slot
holds `XInputGetState`, which the game takes itself from `xinput9_1_0.dll` (`LoadLibraryW` + `GetProcAddress`).
TruShadowPower.asi and TruMenu.asi hook the same slot (TruMenu hands its hook to the game through `GetProcAddress`
before the slot is filled, so it is always the innermost one and wraps nobody). Each plugin saves what it finds there, writes its own hook and
calls the saved pointer. TruShadowPower 0.5 re-swaps whenever the slot is not its own hook; two plugins doing that
would call each other in a loop. TruLink keeps the load order irrelevant:

1. It installs itself on top of whatever the slot holds (the real function or another plugin's hook) and calls that.
2. It re-installs only when the slot holds the real `XInputGetState` again (a module whose name starts with
   `xinput`, or the address resolved from `xinput9_1_0.dll` / `xinput1_4.dll` / `xinput1_3.dll`) - never over another
   plugin's hook, which has saved TruLink's pointer and calls it.
3. Loops are broken: if the plugin TruLink calls takes the slot over (it now calls TruLink), TruLink calls the real
   `XInputGetState` from then on; and if TruLink's hook is re-entered on the same thread (a thread-local flag), the
   inner call goes straight to the real function and the outer chain is shortened the same way. Both are logged.

So with TruShadowPower loaded first or last the chain settles to `slot -> TruShadowPower -> TruLink -> XInputGetState`
(or the other way round), every hook running once per poll. `status` shows the chain; `reentries` > 0 means a loop
was seen and cut.

## Options (`TruLink.ini` next to the `.asi`, optional)

| Key (`[TruLink]`) | Default | Meaning |
|---|---|---|
| `Enabled` | 1 | 0 = load but start nothing |
| `Port` | 9265 | TCP port on 127.0.0.1 (9264 refused) |
| `LogLevel` | 1 | 0 errors, 1 info + every write / game call, 2 every command, 3 debug; `TruLink.log` next to `tru.exe` |
| `AllowForce` | 1 | 0 = the `force` flag is refused |
| `GameThreadTimeoutMs` | 5000 | wait for the game thread (at least 500) |
| `ScanMaxCandidates` | 4194304 | most candidates of a scan (8 bytes each; 1024 .. 16777216) |
| `ScanMaxSeconds` | 60 | a first scan stops after this many seconds (partial set) |
| `WatchIntervalMs` | 100 | watch polling interval (at least 20) |

## Build, install, remove (Windows)

```powershell
.\scripts\windows\Build-TruAsi.ps1 -Name TruLink -Verbose   # Visual Studio 2022 x86 toolchain -> work\asi\TruLink.asi
.\scripts\windows\Set-TruLink.ps1 -Install                  # copies .asi + .ini next to tru.exe (game closed)
.\scripts\windows\Set-TruLink.ps1 -Remove                   # removes them again (only if they are a build of ours)
```

Client (game running):

```powershell
.\scripts\windows\Invoke-TruLink.ps1 -Command 'ping', 'status', 'modules'
.\scripts\windows\Invoke-TruLink.ps1 -Command 'read32 cheat' -PassThru
.\scripts\windows\Invoke-TruLink.ps1 -Interactive
.\scripts\windows\Invoke-TruLink.ps1 -Script .\checks.txt      # one command per line, # comments
```

No external libraries; static runtime (`/MT`), imports `KERNEL32.dll` and `WS2_32.dll` (linked with
`#pragma comment(lib, "ws2_32.lib")`). Addresses of the camera functions, `INSTANCE_Post` and the GameTracker fields are
facts noted from TheIndra55/TRLAU-menu-hook (GPL v3) and checked in our `tru.exe`; no code of it is used. License:
MIT, as the repository.
