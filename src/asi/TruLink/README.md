# TruLink.asi

Live read / write channel into the running `tru.exe` (PC, Steam, image base 0x400000) for our tests. It replaces
the earlier channel through a cdb command file: a small TCP server inside the game process answers a line-based text
protocol that is easy to drive from PowerShell (`scripts\windows\Invoke-TruLink.ps1`).

Version 0.3 - built and checked with `dumpbin` only, not yet tried in the game (0.2 works in the game). 0.2 added the
`menu` command: every item of TruMenu.asi (in-game debug menu) can be listed and run by its id without the controller.
0.3 adds a Cheat-Engine-style memory search (`scan`), polled watches (`watch`) and struct snapshots (`snapshot` /
`diff`) to find unknown values (health, ammo, walking speed) live without a debugger - see
[Memory search](#memory-search-03).

## 0.5.2: puzzle.list, the hinge 180 wrap, the uber.events time (2026-11-17)

Built 2026-11-17 into `work\asi\trulink052` (0 warnings; MD5 `ca2fb61d86f84ae4dc080b265bb322c9`, sha256
`017d74889f05f75900a0c64d1b7045746219d9d1d9f0a2ed7ff1db7c99bb1eb1`; `TruLink.ini` unchanged; offline `TruLinkObjTest`
checks 118 rows, 0 bad), **not installed, not tried in the game**. `puzzle.list` needs TruMenu 0.22.57 (the other
commands work without it). Install (game closed): `scripts\windows\Set-TruLink.ps1 -Install -SourceDir work\asi\trulink052`.

- **`puzzle.list [de|en]`** (game thread job): TruMenu's Kapitel -> "Raetsel in der Naehe" rows through the new export
  `TruMenuPuzzleList(out, size, lang)` - block `ok+ puzzle.list`, one line per row `name<TAB>state<TAB>count<TAB>action`;
  action = the TruMenu item + argument the row runs (`puzzle.hold 4835 1`, `puzzle.weights 4834` ...; run it with
  `menu <item> <argument>`), `-` for a list-only row. Default English. Without TruMenu 0.22.57: `err needs TruMenu 0.22.57`.
- **Hinge wrap:** the engine's hinge getter returns (-180, 180] degrees; a hinge whose limit reaches 180 reads -180 at
  its stop (live 2026-11-16 21:44 / 21:52: the chapel door read -180.00 between 179.91 and 175.18, and `joint.drive 4835 1
  177 hold-until-off` stopped at once "outside the joint's limits"). `tlobj::HingeUnwrap` takes such a value back into
  the limits (+-360 when that lands within 3 degrees of them): in `joint.drive` (start value, answer note `read as ...
  (180 / -180 wrap)`), in every drive tick and stop (TruLinkAct.h, shared with TruMenu) and in the `obj.info` /
  `joint.get` joint line (`... deg (getter -180.00: 180 wrap)`). Pick a hold target below the upper limit (170 held).
- **`uber.events` time:** the field is the **time in the current node in game seconds** (now printed `in node n s (game
  time)`): Update 0x4d7550 adds `[0xe7f188] / 30.0` per update only while no transition runs and `+0x90` bit 3 is clear
  (0 while GameTracker +0xbb is 6); a set node clears it. Pauses (menu, pause screen) and frames without an update do
  not count - the 133 s of 16.11. for locks unlocked ~440 s of wall time earlier (ENGINE section 9 "Update").
- **Reading a pressure plate** (live 16.11. K6): its pressed flag is base-class member **b3.m15 (+92)** of the plate's
  script - read it with **`obj.info <plate>`** (the `b3.m15 +92 stickybool ... = 1` line). `sticky.get <plate> +92` and
  `joint.get <plate> 0` do not answer it: the plate's slider joint belongs to its part object (`b3.m0` multibody), the
  anchor has no joint list of its own.
- Offline: `TruLinkObjTest ... swcmd <switch> <target> [trace]` runs TruMenu 0.22.57's switch -> command reader on a dump
  (`scripts\windows\Test-TruLinkObj.ps1 -Command 'swcmd 4819 4837'`; dump 26292: 4819 -> 0, 4820 -> 3, 4821 -> 1, 4822 ->
  2 as the static P4 scan).

### TO TEST 0.5.2 (live, with TruMenu 0.22.57)

| # | TO TEST | expected |
|---|---|---|
| 1 | `ping` | `pong TruLink 0.5.2` |
| 2 | `l3_chapel`: `puzzle.list`, `puzzle.list de` | the rows of TruMenu's list (switches with their command entry, plates, targets, figures, holds, weights) |
| 3 | door at its open stop: `joint.get 4835 1`, then `joint.drive 4835 1 170 hold-until-off`, `joint.hold off` | the joint line names the wrap; the drive starts (no "outside the limits"), holds, closes after off |
| 4 | `uber.events 4835` after the locks opened | `in node n s (game time)` - smaller than the wall time when the game was paused |
| 5 | `obj.info 4834` with a weight on the centre plate | `b3.m15 +92 stickybool ... = 1` |

## 0.5.1: mark.* (notes under TruMenu's labels), shared action code (2026-11-16)

Built 2026-11-16 into `work\asi\trulink051` (0 warnings, imports `KERNEL32` / `WS2_32` as before; sha256
`b7021fc73b366812b0802ad45165270506a56796f21e6404997c912d1915d440`, MD5 `a41d928f2571e019594ce427a18f9490`;
`TruLink.ini` unchanged), **not installed, not tried in the game**. Needs TruMenu 0.22.56 for `mark.*` (the other
commands work without it). Install (game closed): `scripts\windows\Set-TruLink.ps1 -Install -SourceDir work\asi\trulink051`.

- **`mark.note <intro> [+keep] [+names] <text...>`** - TruMenu's `TruMenuNote(intro, text, flags)` (section
  [mark.note](#marknote-needs-trumenu)): the rest of the line (printable ASCII, cut to 95 characters) as one more line
  under TruMenu's label of that intro id. Default flags 1 = shown even when TruMenu's object names are off; `+names` =
  only inside the name label; `+keep` = flag 2, kept over a level load. Answers `ok mark.note ...` / `err ... full` /
  `err needs TruMenu 0.22.56 ...` (exports missing). Server thread (TruMenu locks its table).
- **`mark.clear [<intro>|all]`** (no argument = all), **`mark.list`** (block: `intro<TAB>flags<TAB>text`).
- **`mark.refs <id>`** - game thread: every instance `obj.refs <id>` finds gets the note `<- <id> <member>` (e.g.
  `<- 4835 m0` on the shadow pillars); one note per referrer (the first member), flags 1.
- **TruLinkAct.h**: `obj.place`'s placement (`PlaceCalls` / `PlaceBody`), the command-table call of `uber.send cmd`
  (`CmdExec`, now with its own fault guard) and the whole `joint.drive` (record, motor / wake helpers, `DriveStop`,
  `DriveTick` incl. hold-until-off) moved unchanged out of TruLink.cpp into a header that TruMenu 0.22.56 includes too
  (its `puzzle.bring` / `puzzle.figures` / `puzzle.hold` run the same code). Only the log prefix comes from the caller
  (`joint.drive` here, so TruLink.log reads as before); one log text is shorter ("holding until stop / hold off").
  `obj.refs` walks through the new `tlobj::RefsEach` (same output: `refs 4834 / 4835 / 4837 / 4830` on dump 26292
  identical to 0.5).
- Offline test: `TruLinkObjTest ... puzzle <id>` runs TruMenu 0.22.56's `TruPuzzleCore.h` (switch base, plate flag,
  portable, graph kinds, the best object check with steps / commands, hinges) on a dump
  (`scripts\windows\Test-TruLinkObj.ps1 -Command 'puzzle 4837'`).

### TO TEST 0.5.1 (live, with TruMenu 0.22.56)

| # | TO TEST | expected |
|---|---|---|
| 1 | `ping`, `status` | `pong TruLink 0.5.1`; checks as 0.5 (118 rows, 0 bad) |
| 2 | `mark.note 4837 figures here`, then look at the shadow pillars with TruMenu's object names on and off | a second label line `figures here`; with names off a small label `4837: figures here` |
| 3 | `mark.note 4834 +names centre plate`, names off | not drawn; names on: drawn |
| 4 | `mark.list` | both notes with flags 1 / 0 |
| 5 | `mark.refs 4834` | `ok mark.refs ...: 6 reference(s) ...`; notes `<- 4834 m1` / `m2` / `m3` on the plates and wall switches |
| 6 | `mark.note 4835 +keep door`, reload the level (Kapitel) | the other notes are gone, `door` stays (ids of placed objects stay the same) |
| 7 | `mark.clear all` | `n note(s) removed`; labels without notes |
| 8 | TruMenu 0.22.55 installed instead | `err needs TruMenu 0.22.56 ...` |
| 9 | 0.5 rows 2 - 11 (`obj.place`, `joint.drive ... hold-until-off`, `uber.send ... cmd`) | unchanged behaviour (the code moved only) |

## 0.5: physics objects, base classes, object checks, hold until off (2026-11-16)

Built 2026-11-16 into `work\asi\trulink05` (0 warnings, imports `KERNEL32` / `WS2_32` as before; sha256
`bb11bcd6dc6dc68f0ecc553a23a225a673d425a1f073aba69860031d8a1444fa`, MD5 `a578b71b4afb509f66d987aaaa4887ce`;
`TruLink.ini` unchanged), **not installed, not tried in the game**.
Install (game closed): `scripts\windows\Set-TruLink.ps1 -Install -SourceDir work\asi\trulink05`. Offline: 118 byte check
rows (14 groups, 37 new) match the Steam `tru.exe` and the images of all three full dumps of 2026-11-15
(`scripts\windows\Test-TruLinkObj.ps1`, new decoder commands `body`, `refs`, `events <id> all`). Details:
[Objects (0.4)](#objects-04) and [0.5 additions](#05-additions).

| What | 0.5 | Proven |
|---|---|---|
| `obj.place <id> near-lara [m] \| at <x y z> \| onto <id> [dz] [yaw deg] [force]` | puts a physics object (body `+0x274`: weights, props) somewhere through **the game's own placement path** - `INSTANCE_SetPosition` 0x5b4100 then `0x497740(body, inst)` (body pose = instance pose x centre of mass `+0x250`), as the game's message 0x75 handler and its birth placement do; velocity 0 (the game's setters), body woken, journaled, `obj.undo` puts it back the same way. Refused for multibody anchors, instances without a body, and (without `force`) when the prop's holder handle is the player | ✅ static (code path, 25 byte rows); ⬜ live |
| `obj.info`: physics body | body pos / quaternion / velocity (units/s) / spin / mass / asleep flag, centre of mass `+0x250`, holder handle | ✅ dump: body pos - R x COM = instance pos exactly (weight, 2026-11-15) |
| `obj.info`: base classes | every class of the script chain (`root +0x18` = the base class's runtime type, as IsA 0x5749e0 walks it) with its members `b<d>.m<k>` and values | ✅ static + dump |
| `uber.events <id> [all]` | object-check transitions (condition 9) list **which link must be in which node** and whether it holds now; `all` lists every node's transitions | ✅ static (0x4d322a / 0x4d1360) + dump |
| `obj.refs <id>` | every loaded instance whose script members (own + base classes) hold an instanceref to `<id>` | ✅ dump |
| motor velocity unit | `obj.info` / `joint.get` print the motor velocity per second **and** raw per physics tick (1/30 s); `joint.drive` speeds are deg/s / units/s and are written per tick (0.4 wrote them 30x too fast) | ✅ static; matches the measured 3.5 deg/s of the chapel door |
| `joint.drive ... hold-until-off`, `joint.hold off` | keeps the target without the 10 s limit until `joint.hold off` / `joint.drive stop`; pushes off the target are driven back; old motor settings restored at stop; stops on unit change / instance gone / leaving the limits | ⬜ live |
| `mark.note` (labels) | interface only, **needs TruMenu** - see [mark.note](#marknote-needs-trumenu); 0.5.1 + TruMenu 0.22.56: implemented | ⬜ live |

### TO TEST 0.5 (live, `l3_chapel`)

| # | TO TEST | expected |
|---|---|---|
| 1 | `ping`, `status` | `pong TruLink 0.5`; `0.5 checks (118 rows, 0 bad ...)`, every group 1 (also `place objcheck super units`) |
| 2 | `obj.info 4828` (a weight on the floor) | `physics body +0x274 ...` with mass 30, asleep, centre of mass 0 0 64.5; base classes with a stickybool |
| 3 | `obj.place 4828 near-lara 1.5` | the weight appears ~1.5 m from Lara (in front if the yaw guess is right, else beside / behind - note which) and falls to the floor; `obj.info 4828` pos = drawn cube |
| 4 | `obj.undo` | the weight is back where it was |
| 5 | `obj.place 4828 onto 4834` (the middle plate) | the weight drops onto the plate; the plate reacts as when carried there (watch `uber.events 4834` / the fire) |
| 6 | carry a weight, `obj.place <it> near-lara` | refused (holder = the player) unless `force` |
| 7 | `uber.events 4837 all` | link 4 `unsolved -> RightSolved_LeftNot` needs links 0 / 2 in `position_a`, `LeftSolved_RightNot` links 1 / 3, `preSolve -> solved` all four; `holds now` follows the switches |
| 8 | `obj.info 4617` / `4525` (villa electric switches) before and after pulling | the base-class members show what changes on the pull (the reuse guard) |
| 9 | `obj.refs 4528` (secret door) | trigger volume 4521 and switch 4617 (by hand on 15.11.) |
| 10 | `joint.get 4835 1` while the door closes by itself | `vel -3.500 deg/s = raw -0.00204 rad/tick` |
| 11 | `joint.drive 4835 1 177 hold-until-off`, wait 60 s, `joint.drive status`, `joint.hold off` | the door opens (~6 s at 30 deg/s), stays open with no time limit (`HOLDING`), closes by itself after `joint.hold off` (motor settings back, `TruLink.log`) |

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
| `obj.place`, `obj.refs`, `uber.events <id> all`, `joint.drive ... hold-until-off`, `joint.hold off` | 0.5, see [0.5 additions](#05-additions) | game |
| `mark.note`, `mark.clear`, `mark.list` / `mark.refs` | 0.5.1, notes under TruMenu's labels (needs TruMenu 0.22.56), see [0.5.1](#051-mark-notes-under-trumenus-labels-shared-action-code-2026-11-16) | server / game |
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
- each game frame the motor velocity (axis 0, 0x4da160; 0.5: the engine's unit is **per physics tick of 1/30 s** -
  hinge rad/tick, rail units/tick; 0.4 wrote deg/s as rad/s, i.e. 30x too fast) is set proportional to the rest (2 /s), at
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

## 0.5 additions

All on the game thread like 0.4; the decoders are in `TruLinkObj.h` (offline test commands in brackets).

**obj.place** (`place` byte rows). A physics object is drawn where its body is: the engine writes the instance pose
from the body every frame (0x497610: `pos = body pos - R(body) x COM`, COM = instance `+0x250`), which is why
`obj.set pos` on a weight only moved the label. `obj.place` uses the path the game itself takes to put such an object
somewhere (message 0x75 handler 0x6c2a5c..0x6c2a91; the same at 0x6bd193..0x6bd1da; birth placement 0x6baf8b..0x6bafc8):

1. `INSTANCE_SetPosition` 0x5b4100 (= `jmp 0x5c55b0`, cdecl inst, `vec4 *` 16-byte aligned): instance `+0x20`, the
   attached parts, the body origin (`0x4ef720`);
2. only with `yaw <deg>`: `INSTANCE_SetRotation` 0x5b4040 (instance `+0x30`, the body quaternion), upright;
3. `0x497740(body, inst)` (cdecl): body position = instance matrix x COM, body quaternion from the instance rotation
   (Body::SetPosition 0x4ef720 / SetQuaternion 0x4ef780 - both also move the body's geoms);
4. TruLink's additions, all game functions: linear / angular velocity 0 (0x4d8df0 / 0x4d8e30), wake (0x4d8fd0).

Destinations: `near-lara [m]` = Lara's position + m metres (default 1.5) along (-sin yaw, cos yaw) and 100 units up
(the forward convention is the camera's, ENGINE section 16; **live 2026-11-16: this lands BEHIND Lara** - TruMenu's
"Gewicht zu mir" uses the same direction and says so), `at x y z` (instance
origin), `onto <id> [dz]` = 150 (or dz) units above that instance's origin. Refused: multibody anchors, no body,
holder handle = the player (`force` overrides). Journal kind `place`; `obj.undo` runs the same path back to the old
position and rotation.

**Base classes** (`super`). `[inst+0x60]+8` is the runtime ScriptType; its root `[t+8]` holds the class Symbol (u16
`+8`), a native class its name (`+0x10`), and the base class's runtime ScriptType (`+0x18`, 0 at the end) - the chain
IsA 0x5749e0 walks. Every class's members address the same data block `[so+0xc]`; `obj.info` lists them as
`b<depth>.m<k>` after the own members `m<k>` (sticky members of base classes decode with the owner's intro id).

**Object checks** (`objcheck`). Uber condition 9 (0x4d31e0 case 9 = 0x4d322a): X = the multibody of `[[b+0x74]+0x4c]`
(0x453310), record `[trans+0x1c]` = {+4 count, +8 entries of 12 B {link index, kind, node}}, evaluated by 0x4d1360:
every entry must hold - kind 1 = the link's uber is in that node (a running transition fails), kind 2 = the link has
no uber state; other kinds and an empty list are false. `uber.events` prints each entry with its current node and
`holds now`; `uber.events <id> all` adds every other node's transitions (so `position_d -> position_a` and
`preSolve -> solved` can be read without waiting for them).

**obj.refs**. Walks the instance list once; each script object once (runtime parts share the anchor's); every member
of type `instanceref` in the whole class chain whose data equals the target's intro id. Arrays of instancerefs are not
read.

**Motor velocity unit** (`units`). The physics step dt is `[0xe7f188]` = frame microseconds / 33333.3 (double
0x855280, 0x5da47c), i.e. 1.0 per 1/30 s; bodies integrate `pos += v x dt` (0x4ef84b) and a joint's motor row takes
the motor velocity as its target velocity (0x4e2340), so it is in **rad (hinge) or units (rail) per tick**. `obj.info`
prints `vel <x> deg/s = raw <r> rad/tick` (x = r x 57.3 x 30). Chapel door hinge: raw -0.00204 rad/tick = -3.5 deg/s,
the measured closing speed on 2026-11-15 (148.04 -> 103.22 deg in ~13 s).

**joint.drive ... hold-until-off**. Approach as before (30 s instead of 10 s to reach the target); once reached no
time limit, no away / overshoot / no-progress stop and node changes of the linked ubers are only logged (as
`through 1`): the motor keeps velocity 0 inside the tolerance and drives back when the joint is pushed off (logged).
Ends with `joint.hold off` or `joint.drive stop`, a new drive, the instance gone (unit change), the joint type changed
or the value leaving the limits; the saved motor velocity / force / enable are put back then (when the joint still
carries TruLink's force). `joint.drive status` says `HOLDING`; `TruLink.log` gets one line every 10 s.

### mark.note (needs TruMenu)

Labels are drawn by TruMenu, so TruLink cannot add text to them. Interface wanted from TruMenu (exports next to
`TruMenuList` / `TruMenuInvoke`; TruLink resolves them with `GetProcAddress` and answers `err needs TruMenu <version>`
when they are missing):

```c
// text: printable ASCII, at most 95 characters (TruMenu copies it); flags bit 0 = show even when object names are
// off, bit 1 = keep over a level / unit load (default: cleared at level load). Thread safe (TruMenu locks its table).
// returns 1 stored / replaced, 0 table full (64 notes), -1 bad arguments
extern "C" __declspec(dllexport) int TruMenuNote(unsigned intro, const char *text, unsigned flags);
extern "C" __declspec(dllexport) int TruMenuNoteClear(unsigned intro);       // 0xffffffff = all; returns notes removed
// one line per note "intro<TAB>flags<TAB>text\n" into out (0-terminated); returns the length, or the size needed
extern "C" __declspec(dllexport) int TruMenuNoteList(char *out, int size);
```

TruMenu draws the note as one more line under the instance's label (same colour rule as the label, `^` / distance as
today), keyed by the intro id (runtime ids too). TruLink commands then: `mark.note <id> <text...>`, `mark.clear
[<id>|all]`, `mark.list`, and `mark.refs <id>` = a note `<- <intro> <member>` on every instance `obj.refs <id>` finds.

**Done in 0.5.1 / TruMenu 0.22.56** (see [0.5.1](#051-mark-notes-under-trumenus-labels-shared-action-code-2026-11-16)):
the exports are `__cdecl` as the other TruMenu exports; `mark.note` takes an intro id (decimal) and the options
`+keep` / `+names` before the text; `mark.refs` writes `<- <target id> <member>` on each referrer.

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
