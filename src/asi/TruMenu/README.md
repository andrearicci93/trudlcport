# TruMenu.asi

In-game debug menu for the **PC** `tru.exe` (Steam, Tomb Raider: Underworld, image base 0x400000), operated with the
**Xbox controller** and drawn with [Dear ImGui](../third_party/imgui/README.md) (MIT, v1.91.9). Every menu entry is also
an **item with a stable id** that tools can list and run without the controller (exports `TruMenuList` /
`TruMenuInvoke`, TruLink command `menu`).

**Status: 0.1.3 runs in the game (menu drawn through the swap chain's Present, L3 + R3, items over TruLink). 0.2
(status page, outfits page, level select with the base game) and 0.3 (Crystal's original developer menu drawn from
the exe's own tables, time / player / HUD, instances, live outfit switch, Debug / Log page + overlay, videos,
experimental markup drawing, weapons / ammo / health) built 2026-10-31 and checked with `dumpbin` only (x86 DLL,
imports `KERNEL32.dll` + `USER32.dll`, exports `TruMenuVersion` / `TruMenuList` / `TruMenuInvoke`) - not yet run in
the game. 0.4 (TO TEST checklist filled over TruLink, log page: collapse repeats / hide TruLink reads / severity
filter / rate limit, `weapon.slots` / `weapon.has`, `ammo.fill`, `gear.give`) built 2026-10-31 into `work\asi\menu04`,
checked with `dumpbin` only - not yet run in the game. 0.5 (TO TEST row kinds step / check / toggle, `test.step`,
`test.toggle`, `test.export`; for `scripts\windows\Invoke-TruTestRun.ps1`) built 2026-10-31 into `work\asi\menu05`,
checked with `dumpbin` only - not yet run in the game. 0.6 (**command bar**: one input line directly under the menu
window, autocomplete, history, pad picker, `cmd.focus` / `cmd.run` / `cmd.history`, `[Cmd]` keys; on top of the 0.5
source with the TruGuard items `guard.*`) built 2026-11-01 into `work\asi\menu06`, checked with `dumpbin` only - not
yet run in the game. 0.7 (TruGuard action `guard.dump`: full minidump + thread snapshot on the TruLink thread, also
while the game hangs; longer `guard.status` buffer) built 2026-11-02 into `work\asi`, checked with `dumpbin` only -
not yet run in the game. 0.7 also got the **command bar without a keyboard** (Steam Machine at the TV): L3 = focus +
on-screen keyboard, the mouse belongs to the menu while it is open, `[Cmd] UpOpensHistory` /
`FirstPadPressOnlyFocuses`, `cmd.keyboard`; built 2026-11-02 into `work\asi\menu07` (with guard.dump), checked with
`dumpbin` only - not yet run in the game (section "Controller and mouse (0.7)"). 0.7 was live-tested 2026-11-02 (mouse,
L3 keyboard, history, real keyboard, `time.scale` ok; typing moved Lara, Esc opened the pause menu, B closed the menu).
0.7.1 (**game input frozen while the menu is open**: `[Menu] BlockGameInput` holds the game's DirectInput keyboard and
the key messages, `[Menu] PauseGame`; B twice = keyboard, then menu; the real-keyboard switch no longer depends on
hover / focus; `level.start` + `[Test] AutoStart` = the mission menu's DLC start with intro; `[Log] UnitChanges`)
built 2026-11-02 into `work\asi\menu071`, checked with `dumpbin` and offline byte checks only - not yet run in the
game (section "Game input frozen (0.7.1)"); live test 2026-11-02 20:28: `level.start dlc2` showed the outfit selection,
a `level.load` during it hung the game. 0.7.2 (**`game.quit`** with a safety step and exit code 0x544D; level.load /
level.start **refused while a mission start is pending** (main state 2 / 9); `level.start` with the **title update's
outfit rule** - DLC 2 without the outfit selection, `[Levels] OutfitRule`; Level page DLC 1 first; log overlay filter
`[Log] OverlaySources` / `OverlayExclude`) built 2026-11-02 into `work\asi\menu072`, checked with `dumpbin` and offline
byte checks only - not yet run in the game (section "Mission start, outfit rule, game.quit (0.7.2)"). 0.8.0
(**Regression page** with the fixed DLC 1 / DLC 2 lists and `TruMenu.regress_results.txt`; **Cheats page** from the
2007 prototype evaluation - god mode, one-hit kill, enemy health, infinite ammo, fill 'er up, cheat codes, each with
its category and byte pre-check; **camera log** `[Log] CameraChanges`) built 2026-11-02 into `work\asi\menu080`,
checked with `dumpbin` and offline byte checks only - first live test 2026-11-02 22:15-22:26 (runs `221539`, `223338`,
`224047`). 0.8.1 (fixes from that test: game.quit "Quit now" button, `[Log] InputTrace`, menu keys released at open /
close, a queued item runs once, cheat.ammo reasons per weapon, `player.unstuck`, regression shortcuts) built
2026-11-02 into `work\asi\menu081`, compiled (0 warnings in TruMenu.cpp) and offline checks only - not yet run in the
game (section "Live-test fixes (0.8.1)"). 0.9 (Saves page, music) built 2026-11-02 into `work\asi\menu09` (section
"Saves page and music (0.9)"; since 0.9 the DLL also imports `SHELL32.dll` for `SHGetFolderPathW`). 0.10 (**radial
menu**: L3 + R3 held / F9 held = a ring of up to 8 entries from `TruMenu.radial.txt`, `[Radial]` keys; stage R2
`instance.spawn <object>` behind `[Radial] Spawn=1`) built 2026-11-03 into `work\asi\menu010`, compiled (0 warnings in
TruMenu.cpp), `dumpbin` and offline byte checks only - not yet run in the game (section "Radial menu (0.10)").
`camera.free` is still a todo (see "0.4 items").**

## Controls

| Input | Effect |
|---|---|
| **L3 + R3** (both sticks pressed together) | open / close the menu (edge-triggered; `[Menu] ToggleButtons`) |
| D-pad / left stick | move between entries |
| A | activate (button, checkbox, open a page) |
| B | back / cancel (ImGui) |
| LB / RB, triggers | ImGui navigation tweaks (sliders) |
| `[Menu] ToggleKey` (off by default, e.g. 119 = F8) | open / close from the keyboard |
| mouse / keyboard | work while the menu is open (forwarded from the game window's message loop) |
| 0.6: typing | goes to the **command bar** under the menu (it has the keyboard focus when the menu opens); see "Command bar (0.6)" |
| 0.6: D-pad / stick / B while the bar has the focus | the focus goes into the menu window (as before 0.6; 0.7 `[Cmd] FirstPadPressOnlyFocuses=0`: the press also moves there) |
| 0.6: View (Back) in the menu, F2, Tab | back to the bar (View: pad picker, F2 / Tab: typing) |
| 0.7: **L3** alone (press + release, menu open; `[Cmd] FocusButton`) | focus into the bar + **on-screen keyboard** under it; L3 again closes the keyboard (see "Controller and mouse (0.7)") |
| 0.7: mouse while the menu is open | belongs to the menu (`[Menu] FreeMouse`): ImGui draws a cursor, the game gets no mouse messages (no camera turn, no re-centring), its `SetCursorPos` / `ClipCursor` wait until the menu closes |
| 0.7.1: keyboard while the menu is open | belongs to the menu (`[Menu] BlockGameInput`): the game's DirectInput keyboard reads no key events, no key message reaches the game - typing does not move Lara, Esc does not open the pause menu |
| 0.7.1: **B, B** with the on-screen keyboard open | first B closes the keyboard, a second B right after it closes the menu |
| 0.10: **L3 + R3 short** (< `[Radial] HoldMs`, menu closed) | opens the menu **at the release** (with `[Radial] Enabled=1` and HoldButtons = ToggleButtons); in the open menu L3 + R3 still closes at the press |
| 0.10: **L3 + R3 held** (>= HoldMs, 500 ms) / **F9 held** / `[Radial] MouseButton` held | the **radial menu** (section "Radial menu (0.10)"): right stick / mouse picks, the release runs |

While the menu is open the game gets a **neutral pad** (no buttons, sticks centred, triggers 0; the packet number is
kept). After a toggle the pad stays neutral until both sticks are released, so the game never sees the L3 / R3 press
that closed the menu. 0.7.1 (`[Menu] BlockGameInput=1`, default): the game gets **no keyboard** either - see "Game input
frozen (0.7.1)". With `BlockGameInput=0` it is as in 0.7: key messages still reach the game except `WM_KEYDOWN` /
`WM_CHAR` / `WM_DEADCHAR` / `WM_SYSCHAR` while a text field or the on-screen keyboard has the focus (key-up messages
always pass), and the game's DirectInput keyboard is not touched (that is why typing moved Lara in the 0.7 live test).
With `[Menu] FreeMouse=1` no mouse message reaches the game while the menu is open. The very first stick pressed
(before the second one completes the combo) does reach the game for a frame or two.

## Pages and items

The menu window holds collapsible pages. The id in brackets is the item that the button runs.

| Page | Content | Items |
|---|---|---|
| TO TEST | 0.4, **first page, open, shown only while the list holds rows** (header "TO TEST (n open, n ok, n fail, n skip)"): one row per test - state, hint, id, note; on the selected row **A = OK, X = FAIL, Y = SKIP** (X / Y go to the row, not to ImGui, while a row has the focus), buttons OK / FAIL / SKIP and "Run <id>" when the id is a menu item (`id:arg` runs it with `arg`); "Remove the marked rows", "Remove all rows" (A twice). 0.5: **switches** (toggle rows, a checkbox each) on top, then **numbered steps** (NEXT marks the first open one; A = run its item + done) and checks in list order. Filled by the main session or `Invoke-TruTestRun.ps1` over TruLink; kept in `TruMenu.tests.txt` next to `tru.exe` (sections "TO TEST" below) | `test.add <id> <hint>`, `test.step <n> <id\|id:arg\|-> <text>`, `test.toggle <id> <item\|ini:Plugin:Section:Key> <text>`, `test.mark <id> ok\|fail\|skip\|open\|done\|on\|off [note]`, `test.list`, `test.export`, `test.del <id>`, `test.clear [done]` |
| Regression | 0.8, under TO TEST, collapsed (header "Regression DLC 1 + DLC 2 (n open, n ok, n fail, n skip)"): selector **DLC 1 / DLC 2 / all**, the rows of `TruMenu.regress_dlc1.txt` / `_dlc2.txt` (next to the `.asi`, copied by `Set-TruMenu.ps1`); checks **A = OK, X = FAIL, Y = SKIP**, buttons OK / FAIL / SKIP / **Note** (puts `regress.note <list>:<id> ` into the command bar and opens the on-screen keyboard; Enter saves); steps: A = run its item + done; "Reload lists" (A twice). Every mark / note is appended to `TruMenu.regress_results.txt` (section "Regression, Cheats, camera log (0.8)") | `regress.list`, `regress.load dlc1\|dlc2\|all`, `regress.mark <dlc1:id\|dlc2:id\|id> ok\|fail\|skip\|open\|done [note]`, `regress.note <list:id> <text>`, `regress.export`; 0.8.1: Quick prepare list + Prepare per row (column 9 shortcut), `regress.prepare <list:id>\|stop`, `regress.shortcuts` |
| Cheats (2007 prototype evaluation) | 0.8: one row per cheat with its **category** (PC has it / re-attach / cheat-code path / rebuild from prototype); a failed byte pre-check greys the row and names the reason in red; in a level only; the "rebuild" rows are listed read-only as "not built yet" | `cheat.list`, `cheat.god [0/1]`, `cheat.godfull [0/1]`, `cheat.onehitkill [0/1]`, `cheat.enemyhealth [0/1]`, `cheat.ammo [0/1]`, `cheat.fillup`, `cheat.code <1\|2\|9\|10\|11>` |
| Status | TruMenu version, `tru.exe` PE time stamp / image size, all code checks, whether a level is loaded; current unit + stream unit id; game state; costume line (current costume, game-data base, `+0x1f4`, chosen `+0x20c` / `+0x20e` / `+0x210`, unit default); player line (instance, object id / name, type record, object-table entry); our plugins (`TruShadowPower`, `TruDoppelganger`, `TruDlc2Player`, `TruRockVein`, `TruLink`: loaded? `<Name>Version()` string), ModLoader.asi, the pad chain (what the game calls, what PadHook calls, with module names), the `d3d9.dll` in use (game folder = TRAWindowed proxy, else system), device / window; 0.7.2: button **"Quit game (press twice)"** at the end (section "Mission start, outfit rule, game.quit (0.7.2)") | `status.version`, `status.hooks`, `status.unit`, `status.state`, `status.costume`, `status.player`, `status.plugins`, 0.7.2 `game.quit` |
| Outfits (next level load) | the same costume facts, then one button per **player record of the game's type table** (index, name, object id; `[chosen]` / `[current]` marked), "Reset chosen costume", checkbox "reload the current unit after choosing" | `costume.records`, `costume.current`, `costume.choose <index\|name> [20c\|210]`, `costume.choosereload <index\|name>`, `costume.choosereset`; the 0.2 ids `costume.setreload` / `costume.reset` still work. **0.3 changed** `costume.list` (now the live cycle list; the 0.2 list = `costume.records`) and `costume.set` (now the live switch; the 0.2 meaning = `costume.choose`) |
| Overlay: Lara's position | checkbox for a small top-left overlay with Lara's position and heading; position / rotation in the page | `overlay.position`, `player.position` |
| Free camera | known facts; experimental `CAMERA_SetMode(mode)` with a mode slider (TRLAU enters its free camera with mode 11; TruLink notes that retail switches only for 6, 11, 12) and "Restore game camera". **TODO** own free camera (moving the camera transform with the sticks) | `camera.current`, `camera.mode <n>`, `camera.restore`, `camera.free` (todo) |
| Cheat / flight | `GameTracker.cheatMode` + player message 12 (TRLAU "skew" cheat); while on and the menu is closed **RT lifts, LT lowers** Lara (`[Cheat] FlightSpeed` per 30 fps frame); 0.21.6: a key line bottom right while flying (`[Cheat] FlightHint`); 0.22.55: a TruMenu level load ends the flight unless `[Cheat] FlightKeepOnLoad=1` | `cheat.flight [0/1]`, `cheat.speed <v>`, `flight.keep [0/1]` |
| Markup / collision draw | 0.3: experimental markup drawing (boxes / poly lines of the MarkupManager projected with the game's view matrix into ImGui's background draw list), "ledges only", projected-space size. `draw.debugflag` was **removed** (debugFlags2 0x100 is the TR7 / TRAE path, catalog section 7) | `draw.markup [0/1]`, `draw.ledges [0/1]`, `draw.scale <w> <h>` |
| Quick access / Favourites | 0.3, **first page, open when the menu opens** (Status is now collapsed): one widget per favourite id (bool = checkbox, info = value, other = button that runs the item with its default argument); **Y** on an item pins / unpins it (on this page, in "Add an item" and on the Developer menu rows - other pages: use "Add an item" or TruLink); saved in `[Favorites] Ids`; default list (empty `Ids`): `player.invincible, player.health, time.scale, time.pause, level.reload, overlay.position, log.overlay, costume.next` (`camera.free` is skipped while it is a todo) | `fav.list`, `fav.add <id>`, `fav.del <id>` |
| Developer menu (original) | 0.3: Crystal's own debug menu, read at load from the tables in `.data` and drawn row by row: page links switch pages, flags / bools as checkboxes, ints as sliders / inputs with the table's limits, actions as buttons; the table's callbacks / functions run on the game thread. Every row shows its static facts (who reads the target in retail, empty functions) in blue; "All pages" lists every page, also those the retail root no longer links | `dev.list`, `dev.<label slug>` (42 ids, list below) |
| Time / player / HUD | 0.3: time scale slider, freeze world, hide HUD; player control, ragdoll death, mark / back to mark, camera fov; weapons / ammo / health (experimental, catalog section 17) | `time.scale <f>`, `time.pause [0/1]`, `ui.hide [0/1]`, `player.control [0/1]`, `player.die`, `player.teleport x y z`, `player.mark`, `player.recall`, 0.8.1 `player.unstuck [mark\|safe]`, `player.goto <inst>`, `camera.fov <rad>`, `player.health [n]`, `player.invincible [0/1]`, `weapon.list`, `weapon.give <name>`, `ammo.show`, `ammo.set <type> <n>`; 0.4 (TruLink / favourites, no own widgets on this page): `weapon.slots`, `weapon.has <name>`, `ammo.fill`, `gear.give <name>` |
| Instances | 0.3: the instance list (name filter, max 200 shown), per instance: Lara goes there, bring to Lara, unhide, remove; "Unhide all" | `instance.list [filter]`, `instance.info <inst>`, `instance.bring <inst>`, `instance.unhide <inst>`, `instance.unhideall`, `instance.remove <inst>` (`<inst>` = intro id, `0x<address>` or `#<index>`) |
| Outfits (live switch) | 0.3: "Next outfit" and one button per id of the game's outfit cycle list; switches at once (needs a level) | `costume.list`, `costume.next`, `costume.set <name\|id>` |
| Debug / Log | 0.3: the last lines of every `Tru*.log` next to the `.asi` / `tru.exe` (tailed once per second by the worker thread, shared read, only new bytes), the game's script prints (`log.script`), lines mentioning errors / exceptions in red, counters (exception lines, exceptions TruMenu caught in its own game calls); source filter buttons (TruLink.log holds the last TruLink commands); corner overlay bottom left. 0.4: repeated lines of a source collapse into one `text x42 (17:09:02-17:09:33)`, TruLink's read-type command lines are dropped, filter all / warnings + errors / errors (warnings yellow, errors red), at most `[Log] MaxLinesPerSecond` new lines per source and second (then one line "(n lines dropped ...)"), counters for all three | `log.page`, `log.show`, `log.script [0/1]`, `log.overlay [0/1]`, `log.lines <n>`, `log.filter <source\|all>`, `log.clear`; 0.4: `log.collapse [0/1]`, `log.hidereads [0/1]`, `log.level 0\|1\|2` (or `all` / `warn` / `error`), `log.rate <n>`; 0.7.2: `log.overlaysources <list\|*>`, `log.overlayexclude <list\|none>` (overlay only, section "Log overlay filter (0.7.2)") |
| Settings | 0.3: every `TruMenu.ini` key with its current value, changed keys marked `*` (yellow) with their default, missing keys shown with the default; "Favourites back to the default list" and "Reset all settings" - both need **A twice** (the button turns red: "press A again to confirm", 5 s) | `settings.show`, `settings.reset` (backup `TruMenu.ini.bak_<yyyymmdd_hhmmss>`, rewrite from the defaults table, reload the options; Scale / Enabled / Script apply at the next start), `fav.reset` |
| Media: videos | 0.3: `Movies\*.bik`, "Play" (main menu only), "as menu loop" | `media.video.list`, `media.video.play <name>`, `media.video.menuloop [name]` |
| Level select | current unit name (GameTracker+0x38), one button per unit of `[Levels] List` (default `dlc_level1_start`, `dlc_level2_start`), "Reload current unit", 0.7.1: "Start DLC 1 / DLC 2 as the mission menu (intro)" (0.7.2: DLC 1 first; a grey line says why level.load / level.start are refused right now), then **all 111 playable units** in tree nodes per group (see below). Any other unit: `menu level.load <unit>` over TruLink | `level.current`, `level.list` (all units: `group: unit unit ...; ...`), `level.presets` (`[Levels] List`; was `level.list` in 0.1), `level.load <unit>`, `level.reload`, 0.7.1 `level.start [dlc2\|dlc1\|<unit>]` (game thread, main menu only; "Game input frozen (0.7.1)") |
| Dev channel | there is no developer channel in `tru.exe` (TCP 9264 is FMOD's profiler). **TODO** re-enable the compiled-out log stub 0x6457a0 | `dev.log` (todo) |
| Radial menu (0.10, no page: a ring over the game) | the entries of `TruMenu.radial.txt`; the Status page has a line `radial (0.10): ...`, the Settings page the `[Radial]` keys (section "Radial menu (0.10)") | `radial.status`, `radial.list`, `radial.reload`, `radial.open [path]`; stage R2 `instance.spawn <object>` (`[Radial] Spawn=1`) |
| Command bar (0.6, own window under the menu) | one input line: `<id> [arg]`, `get <id>`, `list [filter]`, `help`; autocomplete, history, pad picker (section "Command bar (0.6)"); 0.7: on-screen keyboard under the bar (section "Controller and mouse (0.7)") | `cmd.focus`, `cmd.run <line>`, `cmd.history`; 0.7: `cmd.keyboard` |

Items that need a level (camera, cheat) answer / show **"needs a level"** while no player instance exists
(`[0xe7f094]` = 0, e.g. in the main menu). Level select works from the main menu as well.

### Item interface (no controller)

```c
const char *__cdecl TruMenuList(void);                          // "id\ttype\tvalue\tlabel\n" per item
const char *__cdecl TruMenuInvoke(const char *id, const char *arg);   // "ok ..." / "err ..."
```

- Types: `bool` (arg `""` toggles, `0` / `1` / `on` / `off` set), `int` / `float` / `action` (arg as described),
  `info` (read-only: `TruMenuInvoke` returns `ok <id> <value>`), `todo` (answers `err todo`).
- `menu.open`, `overlay.position`, `cheat.speed` run at once on the caller's thread (0.3: also `time.scale`,
  `player.mark`, `instance.list` / `instance.info`, the `log.*` settings, `draw.*`, `player.invincible`,
  `media.video.menuloop`). `camera.mode`, `camera.restore`, `cheat.flight`, `level.load`, `level.reload`, the
  `costume.*` actions, every `dev.<slug>` row and the other 0.3 actions (`time.pause`, `player.*`, `ui.hide`,
  `camera.fov`, `instance.bring` / `unhide` / `unhideall` / `remove`, `log.script`, `media.video.play`,
  `weapon.give`, `ammo.set`, `player.health`) are queued (one slot) and run on the **game thread**
  - inside PadHook, or inside the Present hook while the game does not poll the pad; `TruMenuInvoke` waits up to 3 s
  and returns the result, else `ok queued <id> (...)` and the item runs at the next frame. A second request while one
  is pending answers `err busy`.
- 0.4: the `test.*` items, `log.collapse` / `log.hidereads` / `log.level` / `log.rate`, `weapon.slots` and
  `weapon.has` (read-only, our own reads under `__try`) run at once on the caller's thread; `ammo.fill` and
  `gear.give` are queued for the game thread.
- 0.6: `cmd.focus`, `cmd.run` and `cmd.history` run at once on the caller's thread; `cmd.run <line>` then runs the
  line's own item through the same path (a game-thread item waits as usual), see "Command bar (0.6)". 0.7:
  `cmd.keyboard` (open the menu, focus the bar, show the on-screen keyboard) runs at once as well.
- The returned text lives in a buffer of the calling thread until that thread's next call.
- TruLink 0.2: `menu list`, `menu <id> [arg]` (e.g. `Invoke-TruLink.ps1 -Command 'menu level.load dlc_level2_start'`).
- Values are one line (`; ` between entries) so `level.list` / `costume.list` fit TruLink's one-line answer; the
  per-thread buffers are 48 KB (answer) / 16 KB (one value).

## Command bar (0.6)

One input line in a small window **directly under the menu window** (same width, follows the menu when it is moved;
pushed up to stay on screen). It is a window of its own, so the menu window and its navigation are unchanged: TO TEST
/ Quick access still open first in the menu. The bar is drawn whenever the menu is open (`[Cmd] Enabled=1`).

| Line | Effect |
|---|---|
| `<id>` on a value item (bool / int / float / info, developer-menu flag / bool / int rows) | shows the value: `ok time.scale = 1.000` (does **not** toggle - unlike `menu <id>` over TruLink) |
| `<id>` on an action | runs it without argument (`level.reload`, `costume.next`, `player.mark`) |
| `<id> <arg>` | sets / runs with the argument: `time.scale 0.5`, `ui.hide 1`, `costume.set doppelganger_casual`, `level.load dlc_level2_start`, `dev.fog_far 9000`, `fav.add dev.fog_far` |
| `get <id>` | the value (alias of `<id>` alone, also for actions: `get level.load` = current unit) |
| `list [filter]` | ids containing the filter (`list cost`) |
| `help` | the short help in the result line |

- **Execution:** every line goes through `InvokeCore` - the function behind `TruMenuInvoke`; the bar calls it without
  waiting: items for the game thread go into the same one-slot queue (`ok queued <id> ...`, `err busy` while another
  request is pending) and their answer replaces the result line when the game thread has run them (within 5 s).
- **Result line** under the input: the line, its source (`bar`, `TruLink`, `menu`) and the answer, green for `ok`, red
  for `err`; long answers (`list`, `help`, `level.list`) in a small scroll box.
- **Autocomplete** while typing: a list above the bar with the matching ids (prefix matches first, then ids that
  contain the text), each with its current value (re-read every 0.5 s) and label. After `<id> ` the list holds the
  known arguments: `0` / `1` for bool items and flag rows, the outfit cycle list for `costume.set`, the player records
  for `costume.choose` / `costume.choosereload` / `costume.setreload`, the 111 units for `level.load`, `Movies\*.bik`
  for `media.video.play` / `media.video.menuloop`, the weapon names for `weapon.give` / `weapon.has`, `0..2` for
  `guard.mode` / `log.level`, the favourites for `fav.del`, all ids for `get` / `fav.add`.
- **Keyboard:** Tab = take the highlighted (or first) suggestion (with a space when the item takes an argument);
  Down / Up = move in the list; Enter = run (the highlighted suggestion if one is highlighted, else the line); Up in
  the **empty** bar = history (Up older, Down newer, Down past the newest = empty line); Down in the empty bar, Up /
  Down with nothing to choose and Esc = focus into the menu; **F2** (always) or **Tab** (while no text field is
  active) = back to the bar. Typed keys do not reach the game (see Controls). 0.7: `[Cmd] UpOpensHistory=0` makes Up
  in the empty bar go into the menu as well (Ctrl + Up = history).
- **History:** the last `[Cmd] HistorySize` (32) lines, a repeated line moves to the end; `TruMenu.history.txt` next to
  `tru.exe` (a `#` comment line, then one line per command, oldest first), rewritten after every line, read at start.
  Lines from TruLink's `cmd.run` go into the history as well.
- **Focus:** when the menu opens the keyboard focus is in the bar (type at once). The pad keeps working as before:
  the first D-pad / stick / B press moves the focus into the menu window (that press is not passed on, the next ones
  navigate); A in the empty bar does the same, A with text runs the line.
- **Pad picker** (View / Back in the menu or in the bar, or the "Pick (View)" button): the list shows every id (or
  the matches of the typed text); D-pad up / down (hold = repeat), left / right = 8 rows; **A**: a toggle runs with
  the other state (`<id> 0|1`), an action runs without argument, an info item shows its value, an item with known
  arguments opens their list (A runs `<id> <value>`, B back to the ids), an int / float item opens the value picker
  (**LB - / RB +**, hold RT = x10, A = set, B = back; steps: `time.scale` 0.1, `camera.fov` 0.05, `player.health` 10,
  developer-menu ints 1 or range / 64 within their range); **Y** pins / unpins the id (favourites); **B** = into the
  menu; View = back to typing.

TruLink:

```text
menu cmd.run time.scale 0.5          runs the line as typed into the bar (bar rules: "menu cmd.run ui.hide" shows the value)
menu cmd.run list costume            answer: ok list: <n> of <total> ids matching costume: ...
menu cmd.focus                       opens the menu (if closed) and puts the keyboard focus into the bar
menu cmd.history                     <n>: newest; ...; oldest
```

`cmd.run` waits for the game thread like any `menu <id>` (3 s); `cmd.run cmd.run ...` is refused.

## Controller and mouse (0.7)

Goal: the command bar is usable on a Steam Machine at the TV **without a keyboard**, and the mouse can click into the
menu / bar at any time.

### L3 = focus into the bar

While the menu is open, **L3 pressed and released alone** (`[Cmd] FocusButton`, default 64 = 0x0040 L3) puts the focus
into the command bar and opens the on-screen keyboard - from anywhere in the menu window, also from the pad picker.
L3 again closes the keyboard (the bar keeps the focus). A press that becomes part of the open / close combo (L3 + R3)
does not count: as soon as another button of `[Menu] ToggleButtons` is down while L3 is held, the tap is cancelled, so
closing the menu never opens the keyboard. With `[Cmd] Keyboard=0` L3 only focuses the text field.

### On-screen keyboard

Drawn inside the bar window **under** the input line and the result line (rounded keys in the menu's button colours,
the key under the cursor with the yellow frame of the suggestion list, a pressed key lights up shortly). It opens when
the bar gets the focus **by controller**: L3, A in the idle bar (bar focused, text field not active), View in the pad
picker ("back to typing"), `menu cmd.keyboard` over TruLink. It does **not** open when the menu opens (the text field
gets the keyboard focus as in 0.6) nor for F2 / Tab.

| Row | Content |
|---|---|
| 0 suggestions | the matching ids / argument values of the line (the same list as the 0.6 autocomplete: `time.` -> `time.scale`, `time.pause`; `level.load ` -> the units); while the line is **empty**: the history, newest first. The highlighted chip (also when the cursor is in another row) is what **Y** takes; its value and label are shown under the keyboard |
| 1 quick tokens | `time.` `player.` `costume.` `level.` `dev.` `menu.` `0` `1` space `.` |
| 2..5 keyboard | number row `1 .. 0 -`, then QWERTZ `q w e r t z u i o p _`, `a s d f g h j k l : #`, `y x c v b n m , . /` (lower case: ids and unit / outfit names are lower case, `#` / `:` for `instance.*` and `id:arg`) |
| 6 | space, backspace (X), clear, close (B), run (Start) |

| Pad | Effect |
|---|---|
| D-pad / left stick | move (hold = repeat); up / down go to the nearest key of the next row, the rows wrap |
| A | type the key / take the suggestion chip under the cursor |
| X | backspace (hold = repeat) |
| Y | take the highlighted suggestion (an id that takes an argument gets a space, so row 0 then lists its values) |
| Start | run the line (as Enter; the result line shows the answer; the line is emptied, the keyboard stays open) |
| B | close the keyboard (the bar keeps the focus; D-pad then goes into the menu as in 0.6); 0.7.1: **a second B** right after it (no other button between) closes the menu |
| LB / RB | jump between the rows suggestions -> tokens -> keyboard (letters) |
| View | pad picker (0.6) |
| L3 | close the keyboard |

- The text field is not active while the keyboard is open; the keys edit the line directly (the field shows it).
- **A real keyboard wins:** a typed character (or Backspace) closes the on-screen keyboard and puts the focus into the
  text field with the line so far (cursor at the end); Esc closes it; a mouse click into the field does the same. While
  the on-screen keyboard is open, typed keys do not reach the game (as for the text field in 0.6).
- 0.7.1: the switch no longer depends on the bar focus, the mouse hover or the selected key (live test 2026-11-02:
  sometimes incomplete with the cursor elsewhere and no key selected yet). Any real key press the window procedure sees
  (not Esc, modifiers, F2, Tab, the toggle key) switches; the typed characters are taken out of ImGui's queue (no
  double insert), and for up to 20 frames the focus is requested again and further characters still go into the line
  until the text field is really active. The open keyboard owns the pad whatever has the focus.
- 0.7.1: the keyboard comes back with the menu when it was open at the last close (owner decision 2026-11-02; in 0.7
  this only happened by chance) - B, B or L3 before closing gives a menu without it.
- Mouse: every key is clickable.
- The bar window grows by the keyboard; it is pushed up to stay on screen (it can then cover the lower part of the menu
  window while the keyboard is open).

### Mouse while the menu is open (`[Menu] FreeMouse=1`)

Owner report (0.6): the game keeps the mouse centred and swaps in its own cursor, so clicking into the bar after a focus
loss failed. Static facts (Steam `tru.exe`, `dumpbin /imports` + `tools/pe_dis.py` / `pe_callers.py`, 2026-11-02):

| Fact | Address | Check at load |
|---|---|---|
| USER32 import address table | 0x0083e278; `SetCursorPos` slot **0x0083e308** (entry 36), `ClipCursor` slot **0x0083e2e0** (entry 26), also `GetCursorPos` 0x0083e2a0, `ShowCursor` 0x0083e30c, `SetCursor` 0x0083e2cc | both slots found by name in the import directory at load and compared with these addresses |
| class window procedure | 0x478bc0 (`WNDCLASS.lpfnWndProc` written at tru+0x790cf), starts with `cmp edi, WM_MOUSEMOVE` | `81ff00020000` at 0x478bda, `c744241cc08b4700` at 0x4790cf |
| mouse look | `WM_MOUSEMOVE` while captured: `ShowCursor(FALSE)` until hidden, `ClipCursor(client rect)` (0x478e75), delta = position - client centre -> 0x4827d0, `SetCursorPos(centre)` (0x478f15); not captured: `ShowCursor(TRUE)`, absolute position -> 0x482670 (the game's own cursor), `ClipCursor(NULL)` | `ff15e0e28300` at 0x478e75, `ff1508e38300` at 0x478f15 |
| activation path | `SetCursorPos(centre)` 0x4791b6, `ClipCursor(rect)` 0x4791c1 | both call bytes |
| other input | no raw input imports; DirectInput8 is created (CoCreateInstance, `EnumDevices` tru+0x865f7, callback 0x486380), `GUID_SysMouse` is not in the file - **not verified live** that no mouse input comes that way. 0.7.1: the callback enumerates devices by type: 0x12 mouse -> wrapper 0x485ae0 at input manager +0x28, 0x13 keyboard -> wrapper 0x485e00 at +0x24 (see "Game input frozen (0.7.1)"); so a DirectInput **mouse** device exists as well - not hooked (the 0.7 live test showed no camera turn while the menu was open) | - |

While the menu is open TruMenu therefore:

1. passes **mouse messages** (`WM_MOUSEMOVE` .. `WM_MOUSEHWHEEL`, `WM_MOUSELEAVE`) and `WM_SETCURSOR` (client area)
   **to ImGui only** - the game's window procedure never sees them: no camera turn, no re-centring, no `ShowCursor`;
2. lets ImGui draw its own cursor (`io.MouseDrawCursor`, the system cursor is hidden with `SetCursor(NULL)`);
3. points the two **import slots** `SetCursorPos` / `ClipCursor` to holders that only remember the game's request (only
   while the menu is open; the slots are written back on close, only if they still hold ours) and releases the clip
   (`ClipCursor(NULL)` through TruMenu's own import);
4. on close (game window in front): the game's last `ClipCursor` / `SetCursorPos` request, or else the clip and the cursor
   position from before the menu, are applied once - so the game's next mouse delta starts at its centre (no camera jump).

Mouse positions are scaled from client to back-buffer pixels (ImGui draws in back-buffer pixels; with a scaling window
proxy they differ - in 0.6 the mouse was off then). Status page / `status.hooks`: line `mouse (0.7): ...`; `TruMenu.log`
"0.7 mouse: SetCursorPos slot ...". `[Menu] FreeMouse=0` = 0.6 behaviour (the game gets the mouse as well).

### The two open owner questions (0.6 log page) as options

| Key | Default (= 0.6 behaviour) | Other value |
|---|---|---|
| `[Cmd] UpOpensHistory` | 1: Up in the empty bar opens the history (Up older, Down newer) | 0: Up goes into the menu like Down; **Ctrl + Up** still opens the history |
| `[Cmd] FirstPadPressOnlyFocuses` | 1: the first D-pad / stick press in the bar only moves the focus into the menu (not passed on) | 0: the same press also moves in the menu at once (the held direction is handed to ImGui in the next frame) |

## Game input frozen (0.7.1)

Live test 2026-11-02 (0.7): typing into the command bar moved Lara, Esc in the menu opened the game's pause menu, B
with the on-screen keyboard open closed the whole menu, and the real-keyboard switch was sometimes incomplete.

### Keyboard while the menu is open (`[Menu] BlockGameInput=1`)

How `tru.exe` reads the keyboard (Steam exe, `tools/pe_dis.py`, `pe_callers.py`, `pe_abs_uses.py`, `exe_xref.py`,
`dumpbin /imports`, 2026-11-02):

| Fact | Address |
|---|---|
| no `GetAsyncKeyState` / `GetKeyState` / `GetKeyboardState` / raw input imports; DirectInput8 through `CoCreateInstance` | import table |
| `EnumDevices` callback 0x486380 sorts by `dwDevType & 0xff`: 0x12 mouse -> new 0x890 bytes, wrapper 0x485ae0, stored at input manager `[0xa02b9c]+0x28`; **0x13 keyboard** -> new 0x894 bytes, wrapper **0x485e00**, stored at `[0xa02b9c]+0x24`; 0x14 / 0x15 joystick / gamepad (XInput devices skipped) | 0x486393, 0x4863f3, 0x48641f, 0x48642a |
| keyboard wrapper 0x485e00: vtable **0x844f5c**, `IDirectInputDevice8` at +4; `CreateDevice`, `SetDataFormat(0x8654dc)`, `SetProperty(DIPROP_BUFFERSIZE, 64)`, `SetCooperativeLevel([0x9eedec], DISCL_NONEXCLUSIVE \| DISCL_FOREGROUND)`, `EnumObjects(0x482420)` | 0x485e3f (`mov [esi], 0x844f5c`) |
| vtable slot 2 (**0x844f64** = 0x486100) = `Read(events, room, full)` (thiscall, `ret 0xc`): not full and no resync flag (+0x890) -> buffered `GetDeviceData` 0x486020; else buffered + full `GetDeviceState` 0x485f10 (also after `DIERR_INPUTLOST` / `NOTACQUIRED` -> `Acquire`) | 0x486100, 0x486020, 0x485f10 |
| events: 16 bytes `{1, DIK code, time stamp, value 1.0 / 0.0}` (buffered: `dwOfs`, `dwTimeStamp`, `dwData & 0x80`; full: index, `GetTickCount` via slot 3, state byte & 0x80) | 0x48609d, 0x485fb1 |
| the input manager's read 0x483db0 (its vtable 0x844c54 slot 2) calls pad (+0x2c), mouse (+0x28), keyboard (+0x24) each through `call [vtable+8]` with `(events, room, full)`; keyboard ids + 0x80; byte +0x1a of the manager zeroes keyboard values (the game's own switch 0x4825b0, used by its UI 0x5ac98c / 0x780060 - not touched by TruMenu) | 0x483eea |
| window procedure 0x478bc0: `WM_KEYDOWN` not handled; `WM_KEYUP` + `VK_ESCAPE` -> 0x477ae0 (puts 0x1b into the character queue 0x9eeb40, count 0x9eedf8); `WM_CHAR` -> the same queue (128 entries); `WM_SYSKEYDOWN` only filters Alt combinations (not Alt + F4) | 0x478c0e, 0x478c27, 0x478caa, 0x478d7d |

What 0.7.1 does:

1. At load, after the byte checks below, slot 2 of the keyboard wrapper vtable (0x844f64, `.rdata`) points to
   `KbdReadHook` (only the keyboard wrapper uses this vtable: constructor 0x485e3f, destructor 0x486160). The hook calls
   the game's own read first (the device buffer is emptied as usual, nothing piles up), tracks which keys are down, and:
   - menu open: returns **no** events, except once a release event (value 0) for every key the game saw going down -
     the neutral state (Lara stops if a movement key was held when the menu opened);
   - menu closed: passes the events on, but a key that was held when the menu closed stays away from the game until its
     release (the release is dropped too - the game never saw it go down), so no key "arrives" pressed after the close.
2. While the menu is open `WM_KEYDOWN` / `WM_KEYUP` / `WM_CHAR` / `WM_DEADCHAR` / `WM_SYSCHAR` / `WM_SYSDEADCHAR` go
   to ImGui only (the Esc key-up no longer reaches the game's character queue); the key-up of a key that went down
   while the menu was open is kept away after the close as well. `WM_SYSKEYDOWN` / `WM_SYSKEYUP` pass (Alt + Tab,
   Alt + F4).
3. Pad (neutral, `[Pad] BlockInput`) and mouse (`[Menu] FreeMouse`) as in 0.7. The DirectInput mouse device is not
   touched.

A check that fails switches the DirectInput part off with a log line ("0.7.1 keyboard: code 0, slot ... -> code / slot
NOT matched - DirectInput keyboard not held, only the key messages"); the message part still works. Status page /
`status.hooks`: `keyboard (0.7.1): ...` with the counters (events held, releases sent, kept after close).

Byte pre-checks (all `ok` against the Steam `tru.exe` 2026-11-02 with `tools/pe_bytes_check.py --file
work\asi\menu071\precheck_071.txt`, 36 checks, 0 mismatches):

| Address | Bytes | Meaning |
|---|---|---|
| 0x844f64 | `00614800` | vtable slot 2 = 0x486100 (dword read, then replaced) |
| 0x486100 | `56 8bf1 837e0400 7506 33c0 5e c20c00 807c241000 751e 80be9008000000` | Read(events, room, full) |
| 0x485e3f | `c7065c4f8400` | constructor writes the vtable |
| 0x4863f3 | `83f813 754a` | enum callback: type 0x13 keyboard |
| 0x48641f | `e8dcf9ffff 8b0d9c2ba000 894124` | builds the wrapper, stores it at +0x24 |
| 0x483eea | `8b4f24 8b01 8b4008 52 55 56 ffd0` | input manager calls slot 2 of the keyboard |
| 0x48609d | `8970f4 8b79fc 8978f8 f60180` | buffered event layout |
| 0x485fb1 | `f6440c1480 8970f4 8948f8` | full-state event layout |
| 0x478c0e / 0x478c27 / 0x478caa | `2df1000000 0f850a030000 83bc24800000001b` / `6a1b e8b2eeffff` / `0fb7942484000000` | window procedure Esc key-up / WM_CHAR (documentation; not needed for the hook) |

### `[Menu] PauseGame` (default 0)

1 = the `time.pause` bit (streamFlags 0xe7f0b8 bit 0x1000, checked as for `time.pause`) is set while the menu is open
(Present, as the menu state changes). On close only what TruMenu set is cleared: a pause from before the menu stays,
and `time.pause` used while the menu is open takes over (no restore). Status `status.hooks` `pause=...`.

### B twice, keyboard reopen

B with the on-screen keyboard open closes only the keyboard; a **second B** right after it (no other pad button between)
closes the menu (`TruMenu.log`: "menu closed (B twice: keyboard, then menu)"). B in the idle bar otherwise still moves
the focus into the menu (0.6). Why 0.7 closed the menu on the first B could **not** be found statically: the 0.7 code
only closes the keyboard on B, and the live `TruMenu.log` of 2026-11-02 has only "menu closed (pad)" (L3 + R3) and
"(level change)" lines. 0.7.1 therefore logs every open / close with its reason at `LogLevel` 1 - if a first B still
closes the menu, the log line says by what. The open keyboard now owns the pad independent of the bar focus.

### `level.start` and `[Test] AutoStart` (the mission menu's DLC start, intro plays)

`level.load` (GAMELOOP_RequestLevelChangeByName) skips the DLC intro. The mission menu (PC generalbank script 104)
starts a DLC with `uigamedata` f22, `uigamedata` f27(unit, 1, 0, 1), `stdscreenmgr` f19 + f7
(`docs/Befund-Direktstart.md`; test 41e did the same from the attract timer script and the DLC 2 intro played). The
natives, read statically:

| Native | Registration | Code | Note |
|---|---|---|---|
| `uigamedata` f22 | binder 0x7af0c0, 0x7af201 `push 0x7a0d00; push 0x16` | 0x7a0d00 jmp 0x77bc90 jmp **0x4a0f10** | `byte [0xa039b8] = 1; ret` - no arguments |
| `uigamedata` f27 | 0x7af247 `push 0x7a0d40; push 0x1b` | 0x7a0d40: the three bools of the argument block, then jmp **0x77e170** | cdecl `(DataValue *args, bool, bool, bool)`, `args[0]` = `char *unit` (copied by 0x5dfb20 into GameTracker+0x38), plain `ret` (0x77e442) |
| `stdscreenmgr` f7 | binder 0x7adca0, 0x7add0f `push 0x79ea00; push 7` | 0x79ea00 jmp **0x4be580** | ignores the script instance: `[0xa13f58]` (vtable 0x847c7c) slot 4 |
| `stdscreenmgr` f19 | 0x7addb7 `push 0x79eac0; push 0x13` | 0x79eac0 jmp **0x4be5e0** | `[0xa13f50]` (vtable 0x847cc4) slot 4 |
| slot 4 of both | 0x847c8c / 0x847cd4 = 0x4c5260 | `push ecx; mov eax, [ecx+4]; ...; call 0x7a5160; pop ecx; ret` | thiscall, no arguments |

So the sequence needs no script frame: `level.start [dlc2|dlc1|<unit>]` (game thread, main state 10 only, experimental)
calls 0x4a0f10(), 0x77e170({unit, 1, 0, 1}, 1, 0, 1) (0.7.2: the 2nd value follows `[Levels] OutfitRule`, section
"Mission start, outfit rule, game.quit (0.7.2)"), 0x4be5e0(), 0x4be580() inside `__try`, after checking that no
level change is pending and that both screen managers exist with the expected vtables (singletons created at 0x4ccd3d /
0x4ccd96). Not reproduced from script 104 (as in test 41e): the `dlcsystem` existence check, the "game in progress"
dialog, the `messagechannel` "enableSound" broadcast. Level select page: two buttons "Start DLC 2 / DLC 1 as the
mission menu (intro)".

`[Test] AutoStart=dlc2` (or `dlc1` or a unit name; default empty = off): once per game start, when the main menu
(main state 10) has been up for `[Test] AutoStartDelay` seconds (default 3), TruMenu queues `level.start <unit>` -
the TruMenu replacement for the generalbank test patch 41e, which must never ship. Without the verified path (a check
failed) it queues `level.load` instead and logs "AutoStart: intro skipped (mission start path not available)". Needs
`[Cheat] Experimental=1`. Byte checks (all `ok`, same precheck file): 0x7af201, 0x7af247, 0x7a0d00, 0x77bc90,
0x4a0f10, 0x7a0d40, 0x7a0d69 (`e902d4fdff`), 0x77e170, 0x77e425 (name -> 0x5dfb20, `ret`), 0x7add0f, 0x7addb7,
0x79ea00, 0x79eac0, 0x4be580, 0x4be5e0, 0x847c8c, 0x847cd4, 0x4c5260, 0x4ccd3d, 0x4ccd96; at the call additionally
the two singleton pointers and their vtables.

### `[Log] UnitChanges` (default 1): the stream unit Lara is in

`GameTracker+0x38` (`status.unit`, `level.current`) is only the unit the level load started with. The stream unit Lara
is in: the game loop (0x5dfc88) compares `GameTracker+0xc0` (0xe7f148) with the player instance's +0xe0 and on a
difference calls `STREAM_MoveIntoNewStreamUnit` 0x5c1bf0, which stores the new id into 0xe7f148 (0x5c1c4e) and prints
the name at **entry +0xc** of the stream unit table (0xdbab40, 0xd8 per entry, +0 id, +4 state byte 2 = loaded; lookup
0x5c1b50; format "STREAM_MoveIntoNewStreamUnit(%s)" at 0x5c1c33); the name lookup 0x5c1b90 compares entry +0xc too.
TruMenu's worker thread reads id + name every 250 ms (read-only) and logs a line only on a change:
`unit: dlc2_goo_room (was dlc_level2_start; stream unit id 7)` - into `TruMenu.log`, so also onto the log page and the
log overlay (`log.overlay`). `status.unit` shows the stream unit name too. Checks: 0x5c1bf0, 0x5c1c28, 0x5c1c4e,
0x5c1b9c, 0x5dfc88 and the 0.2 unit table check; a mismatch switches the option off with a log line.

## Mission start, outfit rule, game.quit (0.7.2)

Live test 2026-11-02 (`TruMenu.log`): 20:28:40 `level.start dlc2` from the open main menu -> outfit selection; 20:29:17
`level.load dlc_level2_start` during that screen was accepted ("level change ... requested") -> black screen, game hung,
TruMenu still drawn; 20:32:03 a further `level.load` said "a level change is already pending (GameTracker+0xb9)".

### What a mission start does after f27 (static, `tools/pe_dis.py`, `tools/pe_callers.py`)

| Step | Code | Fact |
|---|---|---|
| game loop | 0x5e01ab `push 0xe7f088; push 0xe7ed60; call 0x5e0090` | the main-state dispatcher gets `&mainState` (0xe7ed60) and the GameTracker; jump table 0x5e015c on `state - 1` (states 1 .. 10; 1 = in a level, 10 = main menu) |
| f27 = 0x77e170 | 0x77e17c `cmp byte [ebp+0xc], 0` ... 0x77e193 `mov [0xfae8d9], dl` | its **2nd argument** is stored as the selection byte 0xfae8d9 ("costume / weapon selection", TU `MainTracker_UILoadLevel`) |
| 0x5dfb20 (end of f27) | 0x5dfb5c `cmp [0xe7ed60], 1`, 0x5dfb83 `mov [0xe7ed60], 2` | unit name -> GameTracker+0x38; in a level `GAMELOOP_RequestLevelChangeByName`, otherwise **main state = 2** - GameTracker+0xb9 is not set |
| state 2 | 0x5e0160 -> 0x5e00cd -> 0x5de7e0; 0x5de877 `cmp [0xfae8d9], 0`, 0x5de884 `mov [state], 9` | selection byte set -> **main state 9 = outfit / weapon selection** (0x5e017c -> 0x5e012e); else the level load (0x5de2b0) |
| selection done | 0x77e450 `mov byte [0xfae8d9], 0; jmp 0x5de9c0` | the byte is cleared, the load goes on |

So during the outfit selection GameTracker+0xb9 is 0 (0.7.1 only tested that), and a `level.load` there sets a request
the state-9 screen never serves -> hang. **0.7.2:** `level.load`, `level.reload` and `level.start` are refused with
`refused: level change pending (<reason>)` (in `TruMenu.log` as `item level.load: err refused: ...`) while
GameTracker+0xb9 is set **or** the main state is 2 (start being set up) or 9 (outfit / weapon selection). `status.state`
and the Level page show the reason. Byte checks (`work\asi\menu072\precheck_072.txt`, all ok on the Steam exe):
0x5e01ab, 0x5e0096, 0x5e0160, 0x5e017c, 0x5e00cd, 0x5de877, 0x5dfb5c, 0x5dfb83; a mismatch keeps the 0.7.1 test
(GameTracker+0xb9 only) with a log line.

### Outfit rule (`[Levels] OutfitRule`, default 1) - translated from the title update

TU generalbank **script 134 function 9** (`tools/menu_dlc_probe.py dis xt 134`, +0x257c .. +0x2608; copy in
`work\asi\menu072\notes\xt134.dis`): `if unit == dlc_level4_start || dlc_level5_start || dlc_level6_start ||
dlc_level2_start: uigamedata f26(unit, 0, 0, 1) else f26(unit, 1, 0, 1)`. The PC script 104 function 9 (`dis pp 104`,
+0x23c0 .. +0x2438) tests only levels 4 / 5 / 6, so on PC DLC 2 gets `f27(unit, 1, 0, 1)` = the selection. (The TU exe's
in-game yes / no path has the same rule, string "Attempting to load DLC2 starting unit without costume/weapon select";
`docs/Befund-Felsrinne.md` step a.) The installed test generalbank 47 (md5 3a2b9a1d...) already carries the TU test in
script 104 and a `(0, 0, 1)` direct-start stub - that is why the old direct start showed no outfit screen.
`level.start` now passes **0** for `dlc_level2_start` (and 4 .. 6) and **1** for every other unit (DLC 1 keeps its
selection, as on the Xbox: `Xenia-TU_DLC1_13`). Without the selection the level load takes the unit default costume
(`lara_doppelganger`, which TruDlc2Player maps to `doppelganger_casual`). `OutfitRule=0` = the PC rule (always 1).
Checks: the mission path, the pending checks, 0x77e17c, 0x77e186, 0x77e193, 0x77e450; a mismatch keeps 1 with a log
line. Still open: the live Xbox observation (Xenia checklist 12c).

### `game.quit` (owner wish 2026-11-02)

Status page, last button "Quit game (press twice)", and the item `game.quit` (command bar, favourites, TO TEST "Run").
**Safety step:** the first run arms it (button turns red: "CONFIRM: quit the game now (n s)"), a second run 0.3 .. 5 s
later quits. **0.8.1:** the countdown label broke the second press with pad / keyboard (see "Live-test fixes (0.8.1)");
now a fixed "Quit game (press twice, or hold 1 s)" button, while armed a separate red **"Quit now"** button (the focus
moves to it once the arming press is released) with "armed - n s left" beside it, a **10 s** window, and holding A /
Enter / Space / the mouse **1 s** on either button quits as well (progress bar "hold 1 s to quit"). Then: `TruMenu.log` line `game.quit by the owner (TruMenu) - logs flushed next, then TerminateProcess(...)`,
the TO TEST list and the command history are written once more, the CRT streams flushed and `TruMenu.log` committed
(`FlushFileBuffers`), then `TerminateProcess(GetCurrentProcess(), 0x544D)` - runs on the render / bar thread, so it
works while the game thread hangs (as long as the menu is still drawn); `TerminateProcess` instead of `ExitProcess` so
no DLL detach can block. **Never automatic:** over TruLink (`menu game.quit`, `cmd.run game.quit`) it answers `err` and
logs "game.quit refused"; TO TEST toggles refuse it; nothing in TruMenu queues it. `Invoke-TruTestRun.ps1` shows exit
code 21581 (0x544D) as "ended via TruMenu game.quit (exit code 0x544D, not a crash)" in the status and the verdict
notes; owner checks still count.

### Log overlay filter (`[Log] OverlaySources`, `[Log] OverlayExclude`)

In the 0.7.1 live test TruShadowPower's "activity 1009 (player +0xc8 = record +4) ... value 0" lines (several per
second) flooded the overlay. The corner overlay now shows only the sources of `[Log] OverlaySources` (default
`TruMenu,TruGuard`; comma list of log names - the file name without `.log`, plus `script`; `*` or empty = all) and
drops lines holding one of the texts of `[Log] OverlayExclude` (comma list of substrings, default empty). Only the
overlay: the Debug / Log page and the log files stay complete. At run time: `log.overlaysources TruMenu,TruShadowPower`,
`log.overlayexclude activity 1009` (`none` = off; no argument = show the value). The overlay says "(log: no lines - n
kept out by ...)" when the filter hid everything.

## Regression, Cheats, camera log (0.8)

Spec: `docs\Plan-TruMenu-Medien.md` (workspace) P0, P0c, P0b. Byte pre-checks of every new engine address:
`work\asi\menu080\precheck_080.txt` (30 checks, `tools/pe_bytes_check.py --file`, all ok on the Steam `tru.exe`
2026-11-02); at load TruMenu checks the same bytes, a mismatch disables that row with a log line
(`0.8 cheats: cheat.x disabled - <reason>`) and a grey row with the reason in red.

### Regression page (P0)

- **Lists** `tests\regress\dlc1.txt` (DLC 1: 6 steps + 12 checks, from `docs/Regression-DLC1.md`) and
  `tests\regress\dlc2.txt` (DLC 2: 7 steps + 23 checks, from `docs/Regression-DLC2.md`), the row format of
  `TruMenu.tests.txt` (`id<TAB>state<TAB>hint<TAB>note<TAB>time<TAB>kind<TAB>target<TAB>number`; check ids = the ids in
  the docs, steps `step<n>`; step 5 of DLC 2 runs `time.scale 0.5`). ASCII only, no game data.
  `tools/trumenu_ini_check.py` checks them too (8 columns, unique ids, every check id named in its doc).
  `Set-TruMenu.ps1 -Install` copies them next to the `.asi` as `TruMenu.regress_dlc1.txt` / `TruMenu.regress_dlc2.txt`
  (from the build folder if it holds them, else from `tests\regress`; a list is ours when its first line starts with
  `# TruMenu regression list`; `-Remove` deletes only ours).
- **Page**: loaded at the menu start without harness / TruLink; every row starts **open** at each game start (the list
  files are never written). Selector DLC 1 / DLC 2 / all (`[Regress] List`, default `all`); checks A ok / X fail /
  Y skip (as TO TEST; X / Y go to the focused row), **Note** = command bar `regress.note dlc2:<id> <text>` + on-screen
  keyboard; steps A = run + done.
- **Results** `TruMenu.regress_results.txt` next to the `.asi`, appended, CRLF, tab separated:
  `#session<TAB><session start><TAB><versions><TAB><sha256>` once per game start before its first row (versions = each
  loaded plugin's `<Name>Version()` up to " (", e.g. `TruMenu=TruMenu 0.8.0; TruShadowPower=...; TruDataGuard=no`;
  sha256 = the loaded `Tru*.asi` files, computed once by the worker thread), then one line per mark / note
  `yyyy-mm-dd hh:mm:ss<TAB>dlc2<TAB>hint-vein<TAB>fail<TAB><note><TAB><session start>`.
- **TruLink**: `menu regress.load dlc2` (re-read, rows open, page selection), `menu regress.export` (block as
  `test.export`: `ok+ regress.export ...`, then `list kind id state number target hint note time` per row, then `.`),
  `menu regress.mark dlc2:wall-run ok`, `menu regress.list`.
- **Harness (not built in 0.8)** - what `scripts\windows\Invoke-TruTestRun.ps1` needs: (1) a profile key
  `"regression": "dlc1" | "dlc2" | "all"`; after the TO TEST preload send `menu regress.load <value>`; (2) after the run
  copy `TruMenu.regress_results.txt` from the game folder into the run folder (`$run.collected`) and, optionally, the
  answer of `menu regress.export` while the game still runs; (3) a reader `Read-RegressResults` that keeps the lines of
  the **last** `#session` block (the run's game start), the newest state per `list + id`; (4) `summary.md` section
  "Regression rows" (list, id, state, note, time) and `summary.json.regression`; (5) the verdict counts them like owner
  checks (fail -> FAIL, open / skip -> INCOMPLETE); (6) `-Compare` lists changed regression states.

### Cheats page (P0c)

Source `docs\Befund-Prototyp-2007.md` 3i (workspace); every address re-read with `tools/pe_dis.py`,
`tools/pe_abs_uses.py`, `tools/pe_callers.py`. All rows run on the game thread (queued), only in a level, need
`[Cheats] Enabled=1` and `[Cheat] Experimental=1`, and log on / off (`cheat: god mode ON (...)`). `[Cheats] Persist=0`
(default): the bytes are `.bss` / weapon data, so after a game start everything is off; `Persist=1` writes the ids that
are on into `[Cheats] State` and switches them on again in the first level of the next start.

| Item | Category | What it does (PC) | Notes |
|---|---|---|---|
| `cheat.god` | PC has it (switchable) | byte `0xfadf60` (`gInvincibleCheat`, cheat code 2 toggles it at 0x5d355a) = 1; `ProcessHealth` 0x6f5160 then keeps the hit-invulnerability timer `P+0x638` = 30.0 and `P+0x63c` = 5 every frame | as the prototype: damage types 8 / 5, `0x6e7930(type)` types and instant deaths still pass |
| `cheat.godfull` | PC has it (switchable) | `cheat.god` + `GameTracker.cheatMode` 0xe7f144 bit 0 (`PlayerTakeDamage` 0x6f5030 returns at once, 0x6f5031) | the bit is also `cheat.flight`'s switch and has **60 uses** in `tru.exe` (`pe_abs_uses.py`) - side effects likely; off clears only a bit TruMenu set (and not while `cheat.flight` is on) |
| `cheat.onehitkill` | PC has it (switchable) | byte `0xe91ffd` through **`ENEMY_ToggleOneHitKill` 0x60f670** (the game's own toggle, cheat code 1 jumps there), called only when the state differs | readers 0x62e39f, 0x633eb3, 0x63bb68 |
| `cheat.enemyhealth` | PC has it (switchable) | byte `0xe91ffc` = 1; reader 0x638ed4 in `EnemyProcessFunc` 0x638d40 prints `[enemy+0x2c64]` through 0x622600 (format 0x858608) | whether retail draws that debug text = live test |
| `cheat.ammo` | logic present, entry cut (re-attach) | per weapon in the 15 slots (`WM+4/+0xc+0x10*slot`, handle check as 0x5b39d0): `T = INSTANCE_Query(inst, 0x36)` (0x5b36f0 -> `inst+0x11c`), `T+0x88 |= 0x80` -> the reloads 0x69c600 / 0x6e7ae0 refill the clip without the reserve; `ResetAmmo` 0x6f58d1 passes the same slot instances to 0x6e7ae0 (proof of the path) | T is the weapon object's shared data; weapons with ammo type 0xff are skipped; new weapons are picked up every 30 game frames; off clears only bits TruMenu set and only on weapon data a slot still returns |
| `cheat.fillup` | logic present, entry cut (re-attach) | `GainHealth` 0x6f4ef0 **cdecl `(float amount, bool noClamp)`** (`fld [esp+4]`, `cmp byte [esp+8], 0`, plain `ret`; ecx unused) with `(MaxHealth 0x6e7990(), 0)` -> health = max, HUD trigger 0x77d9d0 inside; then `ammo.fill` (prototype `DEBUG_FillUpAll` = health + ammo) | |
| `cheat.code <n>` | cheat-code path | `DEBUG_ApplyCheatCode` 0x5d3520 cdecl `(code)`: first `0x6a5dd0(player, 0x71, 0xff, 0, &player.pos)` (hit-reaction effect; `[0xe7f094]` used **without** a null check), then jump table 0x5d358c / index 0x5d35a8: 1 -> 0x60f670, 2 -> toggle 0xfadf60, 9 -> xor 0xe7edb0, 10 -> xor 0xe7edac, 11 -> toggle 0xe91ffc; 3..8, 65, 66 = `ret` | built: the game itself calls it every frame from `GAMELOOP_Process` (0x5dfc5f, unless gameMode `[0xe7f143]` is 6 / 10); TruMenu calls it on the game thread with the same guard + a player; 9 / 10 have no readers on PC (nothing visible expected) |
| no fall damage, enemies ignore Lara, no AI, infinite grenades, enemies don't attack / no attack damage / no health / don't move / don't investigate / no barks | flag + reader gone (rebuild from prototype) | listed read-only, "not built yet" (`cheat.list`) | the prototype function per row is on the page |

### Camera log (P0b, `[Log] CameraChanges`, default 1)

Read-only poll on the render thread every 200 ms: the camera manager 0xe804f0 is processed by 0x5f3c70 (called at
0x5f3e0c with `ecx = 0xe804f0`; vtable 0x855ae4 slot 10), which calls the **mode chooser 0x5e7fe0 with `this` = the
manager**: it writes the requested mode to **manager+0x58** (0x5e80b9 `mov [esi+0x58], 0x34` = adrenaline mode,
others seen there 1 / 0x13 / 0x30 / 0x33 / 0x36) and at 0x5e80da compares it with the applied mode +0x54 (on a
difference: current camera `vtbl[0x60](mode)`, +0x54 = +0x58, time in mode +0x5c = 0). Lines in `TruMenu.log` (log
page / overlay, source TruMenu): `camera: mode 1 -> 52 (0x1 -> 0x34; requested manager+0x58, applied +0x54 = 1)` and,
for the current camera object (manager+0x44 = 0xe80534), `camera: object 0x00e80610 (manager+0x120, vtable 0x...) ->
0x... (manager+0x5b90, vtable 0x...)` (the manager's camera objects +0x120 / +0x670 / +0x5b90 / pointer +0xb80 are named).
**No target instance / object name**: no field of the PC camera struct is proven to hold one (the 2007
`CAMERA_SetInstanceFocus` offsets do not transfer). `camera.log [0/1]` switches it for the session, its value shows
the current fields and the change counters. Checks: 0x5f3e0c, 0x5f3d12, 0x5e7feb, 0x5e8041, 0x5e80b9, 0x5e80da,
0x5e810b, 0x5f3cb0.

## Live-test fixes (0.8.1)

Spec: `docs\Plan-TruMenu-Medien.md` (workspace) P00c; evidence: `TruMenu.log` of the runs `20261102_221539`,
`_223338`, `_224047` (`regress_shadowlara_50k`). No new engine address (`work\asi\menu081\precheck_081.txt` only
re-reads the reload bytes behind the cheat.ammo finding, 2 checks ok).

- **game.quit, second press lost** - cause: the armed label `CONFIRM: quit the game now (%lu s) ...##quit` changed
  every second. In ImGui `##` only hides the rest of a label; the **id is the hash of the whole label**, so the button
  got a new id each second. The pad / keyboard focus (`NavId`) then named a widget that no longer existed, and A /
  Enter activated nothing; after 5 s the label was `Quit game (press twice)##quit` again - the first id, the focus
  was alive again and that press **re-armed** (22:24:06 / :12 / :17 / :24, 5.2-7.3 s apart; with the command bar the
  same item worked, 22:47:57 / 22:48:01). A mouse click only failed when a second boundary fell between press and
  release. Not involved: `FirstPadPressOnlyFocuses` (command bar only), pad ownership (the bar did not have the
  focus). Fix: fixed labels with `###` ids, a separate red "Quit now" button while armed, 10 s, hold 1 s (section
  `game.quit` above). The same bug class was fixed on every label that changes with its state: `ConfirmButton` ("press
  A again to confirm" - Reload lists, settings / favourites reset), item buttons with their value, TO TEST /
  Regression rows ([OK] / [FAIL] / [DONE] / NEXT), the list selectors, live outfit / costume / instance buttons,
  the flight button.
- **Input trace** (`[Log] InputTrace=1`, lines at LogLevel 2; `log.inputtrace`): while the menu is open every pad
  button edge (A B X Y LB RB L3 R3 Start View D-pad, down / up; source "XInput hook" = the game's poll through PadHook,
  "Present fallback" = TruMenu's own read), every mouse button and every key message (no auto-repeat) is queued and
  written one frame later as `input: pad0 A down (XInput hook) -> activated 'Quit now  [game.quit]' (0x...)` or
  `-> not activated: <reason> (focus '<label>' 0x... in <window>)`. Reasons: no widget has the nav focus / the focused
  widget was not drawn (id changed - the game.quit case) / disabled / pressed and released between two frames / not
  the menu's pad / command bar or on-screen keyboard owns the pad (with what the bar did, e.g. "swallowed by
  FirstPadPressOnlyFocuses") / X = fail, Y = skip on a row / menu combo. D-pad and arrow keys: `focus 'a' -> 'b'`.
  Labels come from wrappers around Button / SmallButton / Checkbox / Selectable / CollapsingHeader (`TraceItem`);
  other widgets show their id. At every close (also with InputTrace=0, LogLevel 1): `input while the menu was open:
  n pad presses (A n: n activated, n not), n mouse clicks, n keys`.
- **Stuck Enter in the command bar** (found in run 224047, 22:47:45-53: 70 runs of an empty line every 100 ms, plus
  single letters "u", "i", "." while the owner typed): key messages reach ImGui only while the menu is open; the
  Enter of `level.load ...` in the bar closed the menu before Enter went up, so ImGui kept Enter down and repeated it
  at the next open. Fix: ImGui's keys are released (`io.ClearInputKeys`) at every open / close, and the bar runs a line
  only on a fresh Enter (a repeat keeps the text and the focus).
- **cheat.flight on and off within 16 ms** (22:19:54.690 / .706 after ONE "queued"): `RunPending` tested the request
  flag outside its lock and not again inside, so a second caller that passed the test while the first one ran waited
  for the lock and ran the same request again - with the button's "" (= flip) the flag flipped back. Which second
  caller it was (another thread through PadHook, the Present fallback, or a re-entry through the pad poll - the lock
  is recursive) is not visible in the 0.8.0 log. Fix: the request is claimed with one interlocked exchange (1 queued
  -> 2 running), so it runs exactly once whatever calls it; the flight button sends the target state (1 / 0); the
  "pad slot not polled" test is signed (a newer tick stored between two reads looked like 49 days).
- **cheat.ammo "2 weapon(s), 0 bit(s) set"** (run 223338, hall02): not a failed write. The reload 0x69c600 queries
  0x36 and skips the reserve when **T+0xa == 0xff or T+0x88 & 0x80** (bytes re-read: 0x69c61b..0x69c635). The two
  slot weapons were most likely the pistol pair (left / right hand), whose ammo type is 0xff (unlimited already) - so
  nothing had to be set. 0.8.1 names every slot weapon in the answer and the log: `slot 0 wp_pistol: T 0x... type -1
  flags 0x.. -> ammo type 0xff = unlimited already` / `-> bit set` / `-> bit 0x80 set already` / `query 0x36 = 0 - no
  weapon data`. Live: give a weapon with ammo (`weapon.give wp_shotgun`) and switch it on again.
- **player.unstuck** (Lara slid into the eitr in hall02 with god mode): a ring of 16 "safe ground" spots - every
  ~0.5 s (game thread, 15 game frames) with the menu closed, flight off, health > 0 and Lara's height changed less than
  5 units over ~1 s, a spot at least 100 units from the newest one is kept (no proven on-ground flag yet - read from the
  position). `player.unstuck` takes the newer of `player.mark` (same unit) and the newest spot that is >= 3 s old and
  >= 150 units away from Lara; again within 20 s = one spot further back; `player.unstuck mark|safe` forces the source.
  Button "Unstuck" on the Time / player / HUD page.
- **Regression shortcuts**: optional 9th column `shortcut` in `tests\regress\*.txt` = `#title;cmd;cmd ...` (title
  optional, at most 12 commands). Button **Prepare** on the row and a **Quick prepare** list at the top of the
  Regression page (one button per distinct shortcut, tooltip = the commands, a status line and Stop while one runs);
  `regress.prepare <list:id>|stop`, `regress.shortcuts`. The commands run one after the other through the command bar
  path (source "shortcut", history + TruMenu.log line each) from the render thread: the next one when the game-thread
  slot is free; after `level.*` it waits until no level change is pending, a player exists and (level.load) the unit
  is the requested one for 2 s (timeout 120 s); an `err` answer stops it; `game.quit` is refused. Shipped shortcuts:
  DLC 1 step3 (`level.load dlc_level1_start`), step5 (`cheat.god 0`), dlc1-treasure (`level.load dlc_treasureroom`);
  DLC 2 step4 (`level.load dlc_level2_start`, rock channel ahead), health (`cheat.god 0`), step5 (`cheat.god 0;
  time.scale 0.5`), new **step7 thrall fight** (`level.load dlc_yggdrasil_hall02;cheat.god 1`; the old step7 "Mark
  the checks" is now step8). `tools/trumenu_ini_check.py` checks the column (known item ids, no game.quit, level.load
  unit name, bool args 0 / 1).

## Saves page and music (0.9)

Spec: `docs\Plan-TruMenu-Medien.md` (workspace) P0d, P1-P3; facts with addresses and tools: workspace
`docs\Menue-Funktionen-Katalog.md` sections 11.3 (music) and 11.4 (saves). Byte checks:
`work\asi\menu09\precheck_09.txt` (19 checks, 0 mismatches). Nothing of this was run in the game yet.

### Saves page (P0d)

- **Folder** as `tru.exe` builds it (0x78B550): Documents (`CSIDL_PERSONAL`) + `\Eidos\Tomb Raider - Underworld\`,
  files `<name>.TRUSave` (the game's own names, e.g. `Autosave.TRUSave`); `[Saves] Folder` overrides it. Backups,
  export and import live in **`TruMenu.saves\`** next to tru.exe (never touched by `Set-TruMenu.ps1`).
- **Format** (all proven, `tools/trusave_info.py`): `RGMH` rich saved game header (0x2028) + `PCUD` container (entry
  table, three CRC-32/BZIP2 checks as the reader 0x6DBBA7 / 0x6DBC8D / 0x6DBCC6) + PNG thumbnail + one 0x140000-byte
  data block; in the block only +0x10 (unit name) and +0x90 (checkpoint id) are proven. The list shows name, date,
  size, unit, checkpoint and whether all CRCs match.
- Items: `save.folder`, `save.list`, `save.backups` (info); `save.backup [label]` (all files ->
  `TruMenu.saves\<yyyyMMdd_HHmmss>[_label]\`), `save.export <save>` (-> `TruMenu.saves\export\`, never overwrites);
  **owner only, safety step** (the same command twice within 10 s; menu: a separate red `CONFIRM` button with a stable
  id, `cancel`; refused over TruLink): `save.delete <save>` (full backup `<time>_deleted` first, then the file is
  deleted from the save folder - the copy stays), `save.restore <backup>` (backup `<time>_before_restore` first, then
  the backup's files are copied over; other saves stay), `save.import <name>` (`TruMenu.saves\import\<name>.TRUSave`,
  CRCs must match; backup `<time>_before_import` first).
- **No save field is written** (no unlocks / chapter / inventory / costume / end-game edits in 0.9): nothing beyond
  +0x10 / +0x90 has a proven reader yet.

### Music (P1-P3, Media: music page)

- Engine path only (translate, don't imitate): `media.music.play <track> [slot]` = **`SRMUSIC_LoadMusic` 0x594320
  `(slot, name, fade, fade)`** exactly as the game's unit start 0x5B2211 (slot 0, 60 frames); `media.music.stop
  [slot|all]` = `LoadMusic(slot, NULL, fade, 0)` as the stop native 0x4AA490; `media.music.now` = the 8 slots at
  0xCC5260 (+0 current, +0x100 requested, +0x51C loaded object) and the unit music name 0xD98F64. Game thread,
  experimental, main menu (main state 10) always, a level only with `[Media] MusicInLevels=1`.
- Track names only from **`TruMenu.media.txt`** next to the .asi, written by `tools/music_list.py --menu-out <build
  folder>` and copied by `Set-TruMenu.ps1` (not in the repository). Without it nothing can be played. The list carries
  the source (base / DLC1 / DLC2 / mods override) and `referenced` / `unused?` (today: none unused). DLC tracks of the
  port are silent (converted with silent audio).
- `dev.musicvars` / `dev.monstermusicvars` switch the developer flags 0xE7F098 & 0x10000000 / 0xE7F0A0 & 0x01000000,
  only when the original developer table has that row (found at runtime). `media.video.flags` lists the videos with
  source + flag.
- `weapon.give` was already complete in 0.8.1 (item + "Give <name>" buttons on Time / player / HUD) - unchanged.

### TO TEST 0.9 (owner, in this order)

| # | Where | Step | Expected |
|---|---|---|---|
| 1 | load | Start the game with 0.9 | TruMenu.log: `TruMenu 0.9 (Saves page ...`, `0.9 music 1 (LoadMusic 0x594320 ok, ...)`, media list with 63 rows, `0.9 saves: folder ...\Eidos\Tomb Raider - Underworld\` |
| 2 | main menu, Saves page | open the page | every save with date, unit (e.g. `dlc_caverns`), checkpoint, `CRC ok` |
| 3 | Saves page | `Back up all saves now` | log `saves: backup <time>: n file(s) copied, 0 failed`; the folder appears under backups; files in `TruMenu.saves\<time>\` |
| 4 | Saves page | `Export` on one save | file in `TruMenu.saves\export\`; a second export of the same save gets a time suffix |
| 5 | Saves page | `Delete` on a test save, then wait 11 s | the first press only arms (red CONFIRM + seconds left); after 10 s the arm is gone, nothing deleted |
| 6 | Saves page | `Delete` again, then `CONFIRM` | backup `<time>_deleted` holds ALL saves incl. the deleted one; the file is gone from the save folder; the game's load menu no longer lists it |
| 7 | Saves page | `Restore` on that `_deleted` backup, `CONFIRM` | backup `<time>_before_restore` made first; the save is back, listed in the game's load menu and it loads |
| 8 | TruLink | `menu save.delete <name>` | refused: `err save.delete only from the menu or the command bar (owner)` |
| 9 | main menu, Music page | `Stop all slots`, then `Play` on `l2_waters_of_thailand` | note whether the title music stops; the track fades in (~2 s); `now:` shows slot 0 = the track, object loaded |
| 10 | Music page | `Stop slot 0` | the track fades out (~2 s); `now:` slot 0 without object |
| 11 | Music page | `Show Music Vars` on | is anything drawn in the main menu? (retail draw path unknown) - note it, switch off again |
| 12 | Media: videos | `Play explode` (0.6 item, first live test) | the video plays, the menu comes back; `media.video.flags` lists 6 videos `referenced` |
| 13 | level, only with `MusicInLevels=1` | play / stop once in `dlc_level1_start` | no crash, no stuck audio; the unit music comes back at the next unit change |

## Radial menu (0.10)

Spec: workspace `docs\Konzept-Bau-Rad.md` (stage R1; R2 behind a switch). The ring is only a faster way to run the
existing items - every entry is an item id as typed into the command bar and runs through the same path
(`InvokeCore`, game-thread items queued). Built 2026-11-03 into `work\asi\menu010`; compiled, `dumpbin` and offline
checks only - **not yet seen in the game**.

### Controls

| Input | Effect |
|---|---|
| **L3 + R3 held** >= `HoldMs` (500 ms, menu closed) | the ring opens in **hold mode**: the **right stick** picks a sector live, **releasing** the buttons runs it and closes the ring; released with the stick in the **centre** = nothing (cancel); released on a **level** (`Cheats >`) = that level opens and the ring stays (**latched**) |
| L3 + R3 short (< HoldMs) | TruMenu as before, but it opens at the **release** (owner decision: release variant). In the open menu L3 + R3 closes at the press as in 0.9 |
| **F9 held** (`[Radial] Key`; Steam Controller back button -> F9 in Steam Input) | the ring at once (no HoldMs: F9 has no short meaning); the **mouse direction** (a white dot) or the right stick picks; releasing F9 runs |
| `[Radial] MouseButton` held (3 middle, 4 / 5 side) | as F9 |
| **A** (also left click) | run the pick and **stay open** (several steps in a row: hold, pick, A, A, A); on a level: open it |
| **B** (also right click) | one level back (the pick = the folder you came from); at the top: close |
| LB / RB | page back / on (a level with more than 8 entries) |
| **R3 alone** (latched ring) | run the pick and close (pick with the right stick, then click it) |
| L3 + R3 / F9 again (latched ring) | hold mode again: the release runs the pick (the stick must point at it) |

- **Hold mode** picks live: back in the centre = no pick. **Latched** keeps the pick when the stick springs back (the
  thumb goes to A). The release uses the pick of the frame before (the stick may spring back in the release poll).
- **Remember** (`RememberPosition=1`): a close keeps level, page and pick; the next open shows them highlighted, but a
  release without moving the stick still cancels (centre rule). Repeating an entry = A in the open ring. `0` = top.
- The ring and TruMenu are never open together: opening the menu (F8 / TruLink) closes the ring.
- **Pad while the ring is open:** the game gets a neutral pad (buttons, right stick, triggers), with `PassLeftStick=1`
  the left stick still reaches it (Lara walks). After the close the pad stays neutral until every button is up (the
  B / A / R3 of the close never reach the game). While L3 + R3 wait for HoldMs the game gets the same neutral pad.
- **Keyboard:** `[Radial] Key` never reaches the game while the ring is enabled: `KbdReadHook` drops its DirectInput
  events (DIK = `MapVirtualKey(VK, VSC_EX)`, F9 = 0x43; needs `[Menu] BlockGameInput=1`, which installs the hook) and
  the window procedure drops its `WM_KEYDOWN` / `WM_KEYUP`; other keys pass (WASD walks). **F9 in the game:** tru.exe
  holds no key-name strings at all (`tools/pe_find_str.py` / `pe_find_wstr.py`: no `F9`, `Escape`, `Backspace`,
  `Keyboard`, ASCII or UTF-16) - the PC bindings come from the game data, not read; if the owner has F9 bound in the
  game, set another `Key`.
- **Mouse:** with `[Menu] FreeMouse=1` the ring holds the mouse like the menu (no camera turn, the game's
  `SetCursorPos` / `ClipCursor` held, cursor restored at the close); the middle / side button of `MouseButton` never
  reaches the game.
- `SlowMotion` > 0: `time.scale` = that value while the ring is open; at the close the old value comes back unless
  an entry changed it meanwhile.
- Not built (concept options): a "recently used" sector, "Y = add to the ring" in the menu, the input trace for the
  ring (`[Log] InputTrace` records while the menu is open only - test 102 checks the neutral pad by sight).

### `TruMenu.radial.txt` (next to tru.exe)

```text
# TruMenu radial menu ...                      first line = marker (Set-TruMenu.ps1: ours)
path | label | item id [argument]
Cheats | Gott-Modus | cheat.god
Objekte/Kisten | Kiste A | instance.spawn sh_ei_combat_crate_a       "/" = a level below
```

- A level holds the folders of its sub-paths (`Cheats >`, in the order of their first line) and its entries in file
  order; 8 sectors per page. Limits: 256 entries incl. folders, 48 levels, 64 per level.
- **Bool items without an argument** (`cheat.god`, `time.pause`, `player.invincible`) show **on / off** in the sector
  and run with the other state (`cheat.god 1` / `0` - never "" = flip, the 0.8.1 lesson).
- **Greyed out** with the reason (in the centre when picked, "not available - ..." when run): an unknown id (logged at
  load: `radial: line 31: unknown item 'x' - entry greyed out`), a failed byte pre-check of the item (the Cheats page
  reasons, weapon / ammo / health / time checks, `instance.spawn`), `[Cheats] Enabled=0`, `[Cheat] Experimental=0` for
  game-thread items, `[Radial] Spawn=0`, and "needs a level" for `cheat.*`, `player.*`, `weapon.give`, `ammo.*`,
  `gear.*`, `instance.spawn` / `bring` / `remove` / `unhide`, `camera.mode` / `restore` / `fov`, `costume.next` / `set`.
- **Never offered** (dropped at load with a log line; `RadialRun` refuses them again): `game.quit` (owner rule:
  button-only), `cmd.run`, `save.delete`, `save.restore`, `save.import`, `settings.reset`.
- Every run logs `radial: <path> -> <item> [arg]: <answer>` (LogLevel 1). Queued items show their answer as "last
  action" under the ring.
- Shipped default (`src\asi\TruMenu\TruMenu.radial.txt`, German labels without umlauts - the menu font has none):
  top = Cheats, Marken, Zeit, Waffen, Spieler, Objekte.

| Level | Entries (item) |
|---|---|
| Cheats | Gott-Modus `cheat.god`, Gott-Modus voll `cheat.godfull`, Ein Treffer toetet `cheat.onehitkill`, Gegner-Leben zeigen `cheat.enemyhealth`, Munition endlos `cheat.ammo`, Alles auffuellen `cheat.fillup` |
| Marken | Marke setzen `player.mark`, Zur Marke `player.recall`, Befreien (Marke) `player.unstuck mark` |
| Zeit | Normal 1.0 / Zeitlupe 0.5 / 0.25 `time.scale 1 / 0.5 / 0.25`, Welt einfrieren `time.pause` |
| Waffen | `weapon.give wp_shotgun`, `wp_uzi`, `wp_dlc_gold_shotgun`, `wp_assault_rifle`, `wp_tranq`; Munition voll `ammo.fill` |
| Spieler | Befreien `player.unstuck`, Volle Gesundheit `player.health` ("" = MaxHealth), Unverwundbar `player.invincible` |
| Objekte (R2) | `instance.spawn g_healthpack`, `sh_ei_combat_crate_a`, `_b`, `_c`, `wp_shotgun` (greyed while `Spawn=0`) |

- `Set-TruMenu.ps1 -Install` copies the file next to tru.exe (from the build folder, else `src\asi\TruMenu`; ours =
  first line `# TruMenu radial menu`), `-Remove` deletes only ours; `Build-TruAsi.ps1` puts it into the build folder.
  `../bin/pyt -t 60 tools/trumenu_ini_check.py` checks it (ASCII, three fields, known ids, the forbidden list equal to
  `kRadForbidden`, bool args 0 / 1, one name for `instance.spawn` / `weapon.give` / `level.load`, the limits).

### Items (TruLink / command bar)

| Item | Meaning |
|---|---|
| `radial.status` | the `[Radial]` options, file state (entries / levels / dropped / unknown / skipped), ring state (closed / hold / latched, by pad / key / mouse / radial.open, level, page), entries run, spawn check; also the Status page line `radial (0.10): ...` (0.10.1: `radial (0.10.1)`, plus mode / freeze / quit sector / tests level / tour) and `status.hooks` `radial=...` |
| `radial.list` | every entry `path \| label \| item [arg]` with `= greyed: <reason>` |
| `radial.reload` | read the file again (ring closed) |
| `radial.open [path]` | open the ring latched at that level (test without the pad; B at the top closes) |

### Stage R2: `instance.spawn <object>` (`[Radial] Spawn=1`)

The catalog row "Spawn object at Lara" (workspace `docs\Menue-Funktionen-Katalog.md` section 6), every address re-read
on the Steam exe with `tools/pe_dis.py`, `pe_callers.py`, `pe_cstr.py` and the new `tools/pe_find_bytes.py`;
`work\asi\menu010\precheck_010.txt` = 20 checks, `tools/pe_bytes_check.py --file`: **0 mismatches** (2026-11-03). The
same bytes are checked at load (`SpawnCheck`); a mismatch disables the item with the reason (log line
`0.10 instance.spawn disabled - ...`).

| Step | Function (cdecl) | Fact / check |
|---|---|---|
| DRM present | `0x5bf7b0(name)` -> bool | the game's own composition of the catalog step: `LOAD_UnitFileName 0x477970(buf[0x100], name)` (`sprintf("%s%s.drm" 0x8443bc, prefix 0xa03824, name)` - on PC two arguments, `.drm` is in the format) + `GetFS 0x472b50` (`[0x9ce278]`) -> vtable +8 (FileExists); used by the costume validator (tail call 0x5c54f8) and the level load (0x5de368) |
| object id | `OBTABLE_GetObjectID 0x5bf770` != 0 | 0.2 check (TruMenu's `ObjectId` reads the same table) |
| tracker | `STREAM_GetObjectTrackerByName 0x5c17d0(name)` | id -> `0x5c1550(id, 0)`: finds or requests the entry of table 0xdb7400 (0xcc entries of 0x24: +8 Object*, +0xc s16 id, +0xe u16 status; a new entry gets status 1 at 0x5c1670). No free entry = `"Out of objecttracker space!"` (0x854154 through 0x596cb0) - so TruMenu refuses with fewer than 2 free entries |
| load | `STREAM_PollLoadQueue 0x5c1da0()` until status 2 | 1 while busy (0x5c1dc3 / 0x5c1ddb); status 2 = loaded is the game's own test (0x5bf2e0 `cmp word [eax+0xe], 2` in the loaded-object lookup); the costume switch 0x6f0bc5 polls the same way after 0x5c17d0. TruMenu: at most 3000 ms, `Sleep(1)` between polls - the game thread blocks (a stutter) |
| birth | `INSTANCE_BirthObjectNoParent 0x5bd0f0(unit, &pos, &rot, NULL, object, 0, 1)` | 7 arguments: the script native at 0x780aaf passes `(unit, &pos, &rot, x, object, 0, 1)`, `add esp, 0x1c`; pos / rot are copied at once (0x5bd180, 16 bytes each into +0x20 / +0x30); returns the instance (0 = refused). unit = StreamUnitID `[0xe7f148]` (GameTracker+0xc0, compared with the player's +0xe0 by the game loop 0x5dfc88; both are logged) |

Gates: `Spawn=1`, `[Cheat] Experimental=1`, main state 1 with a player, no level change pending, name `a-z 0-9 _`.
Everything runs on the game thread (queued) inside `__try`; the answer / `TruMenu.log`: `instance.spawn: g_healthpack
(id 55) born at Lara (x y z): instance 0x...; tracker 0x... was in the table / requested now, n polls / m ms; stream
unit u (player +0xe0 = v)`. **Lara's position exactly** (as the catalog) - a crate appears inside Lara; placing in
front of her is stage R3.

**Spawn candidates** (harmless pickups / crates / a weapon object; 2026-11-03):

| Object | id (merged list) | DRM (`tools/archive_has.py`) | Units that load it (`tools/objlist_users.py`, merged `objlist.dat`) | Note |
|---|---|---|---|---|
| `g_healthpack` | 55 | xbase, xbase2, **pcbig** | 115 units incl. `dlc_level2_start`, `dlc_yggdrasil_hall01` / `hall02`, every `dlc2_*` unit | already loaded in DLC 2: no load, tests the birth only - first test |
| `sh_ei_combat_crate_a` | 296 | xbase, **pcbig** | l1 / l6 ship units only | loaded on demand (tests the tracker + load queue) |
| `sh_ei_combat_crate_b` | 297 | xbase, **pcbig** | l1 / l6 ship units only | as a |
| `sh_ei_combat_crate_c` | 306 | xbase, **pcbig** | l1 / l6 ship units only | as a |
| `wp_shotgun` | 40 | xbase2, **pcbig** | l3 units, the DLC 1 units, `container_all_weapons` | a weapon object without an owner - test last |

Not taken: `sh_ei_combat_crate_d` (same kind), `sh_ei_exploading_barrel` (explodes), `wp_dlc_gold_shotgun` /
`dlc1_health_pack` (only in the port's mods, pack10). **Open (before more objects):** whether born instances are
written into saves (back up the saves first - Saves page), how objects without their unit scripts behave, whether a
crate keeps physics without its unit.

### Owner questions of the concept, answered by defaults (all configurable)

| Question (concept section 8) | Default in 0.10 |
|---|---|
| objects first | R2 candidates above (health pack, three crates, the shotgun object); enemies / traps not offered |
| slow motion at the open | off (`SlowMotion=0`) |
| Lara walks while the ring is open | yes (`PassLeftStick=1`) |
| release variant (menu opens up to 0.5 s later) | yes (`HoldMs=500`); `[Radial] Enabled=0` = the 0.9 press variant |
| R1 now, R2 later | both built, R2 off (`Spawn=0`) |

## Radial menu (0.10.1)

Owner wish 2026-11-03: the ring should work like a menu, not like a hold-and-release weapon wheel (workspace
`docs\Konzept-Bau-Rad.md` section 10 "Bedienung v2"), plus a "Tests" level. Built into `work\asi\menu0101`; compiled
(0 warnings in TruMenu.cpp), `dumpbin` and offline checks only - **not yet seen in the game**. `[Radial] Mode=wheel`
keeps the 0.10 ring above unchanged (no Freeze, no built-in sectors).

### `[Radial] Mode=menu` (default)

| Input (ring open) | Effect |
|---|---|
| **L3 + R3 held** >= HoldMs / **F9 tapped** / `MouseButton` tapped / `radial.open` | the ring opens and **stays open** after the release; nothing runs on a release |
| **left stick**, right stick, mouse direction | move the pick (the stronger stick wins; the pick stays when the stick springs back; the mouse picks only while it moves) |
| **D-pad left / right**, arrow keys left / right | the previous / next sector of the page |
| **A** / Enter / left click | runs the pick or opens its level (`Cheats >`); the ring stays open |
| **B** / Backspace / Esc / right click | one level back (the folder you came from is picked); at the top: close |
| LB / RB | page back / on (a level with more than 8 entries) |
| **L3 + R3 again** / F9 again / `MouseButton` again | close (level, page and pick are kept with `RememberPosition=1`) |

- The game gets the **whole pad neutral** while the ring is open (`PassLeftStick` applies to `Mode=wheel` only) and,
  with `[Menu] BlockGameInput=1`, **no keys** (DirectInput events and key messages held as for the menu; a key that
  went down meanwhile stays away from the game until it is released). After the close the pad stays neutral until every
  button is up. L3 + R3 short (< HoldMs) still opens TruMenu at the release.
- A **level.\*** entry (file, tour, a TO TEST row's Run) and "Prepare" **close the ring** after they ran: whether a
  level change goes on while the time.pause bit is set is not proven, the freeze must end (see below).

### `[Radial] Freeze` (Mode=menu; read again at every open - the TO TEST switch `radial-freeze` works at once)

- `world` (or `1`, default): at the open in a level the **time.pause bit** (streamFlags 0xe7f0b8 bit 0x1000, the 0.3 code
  check `g_pauseOk`, the same as `[Menu] PauseGame`) is set; at the close it is cleared **only if the ring set it** and
  nobody ran `time.pause` meanwhile - `time.pause` run from the ring (Zeit -> Welt einfrieren) clears the ring's claim,
  the user's choice stays. A pause from before the ring stays. The game's own pause menu (gameMode 6, 0x5d479b /
  0x5d4810) clears the bit when it opens - then nothing is restored.
- `player` (or `2`): `player.control 0` at the open (the 0.3 byte 0x8ab4e6, `[Cheat] Experimental=1`), the value from
  before back at the close unless `player.control` ran meanwhile or something else changed the byte; the pad is
  neutral anyway.
- `0`: nothing. Outside a level nothing is frozen. Log lines (LogLevel 2): `radial: freeze world - time.pause bit set by
  the ring ...`, `radial: freeze world released (time.pause bit cleared)`.

**Queued items while the world is frozen (static, `tools/pe_dis.py` / `pe_callers.py` / `pe_abs_uses.py`; pinned in
`work\asi\menu0101\precheck_0101.txt`, 17 checks, 0 mismatches):** the main loop 0x5e0190 calls the state dispatcher
0x5e0090 and then `STREAM_PollLoadQueue` 0x5c1da0 every iteration (0x5e01ab). State 1 (in a level, 0x5dffe0) first
calls the input update **0x483810** (no streamFlags test: only `[0xa02b78] && ![0xa02b79]`), which runs 0x483520 per
input manager -> its device object's slot 2 0x483db0 -> the pad object (`[obj+0x2c]`, constructor 0x484520, vtable
0x844dcc, stored at 0x486268) slot 2 0x484b70 -> `call [0xa02b8c]` = **PadHook**, where `RunPending` runs the queued
item - all **before** `GAMELOOP_Process` 0x5dfbe0, which holds every 0x1000 test (0x5dfc2c, 0x5dfcad, 0x5dfd89,
0x5dfdcd, 0x5dfe36, 0x5dfeb2, 0x5dff2c). So the queue does **not** stall: `instance.spawn` (its own poll loop on
0x5c1da0, which the main loop also calls unpaused, then the birth) and the other game-thread items run while frozen;
a born instance is not processed until the close (the instance loop 0x5bbe70 sits in the skipped 0x5dfeb2 block). Not
traced: that the manager's device object `[0xa02b68 + 8]` is the object at `[0xa02b9c]` that holds the pad (same
layout, +0x24 keyboard / +0x2c pad); the existing safety net covers it anyway - when PadHook is not called for 250 ms
the Present hook runs `RunPending` itself. What **does** wait: PadHook's per-game-frame ticks (FlightTick, WeaponsTick
- the weapon re-post after a costume switch -, InvincibleTick, CheatsTick - the cheat.ammo re-apply -, SafeGroundTick)
run when the game clock GameTracker+0xd4 (`kGameClock`, 0xe7f15c) changes, and 0x5dfc2c advances it only without the
pause bit - they go on at the close. No temporary unpause was built.

### Built-in sector "Spiel beenden" (`[Radial] QuitSector=1`, Mode=menu)

The last sector of the **top level only** - not from `TruMenu.radial.txt` (the file check still rejects `game.quit`,
`RadialLoad` still drops it). Same safety as the Status page button of 0.8.1: the first **A** (Enter / left click)
**arms** it (the sector turns red, label `A nochmal = beenden (n s)`, a 10 s window); a **second A** >= 0.3 s later or
**A held 1 s** runs the same path as `game.quit` (`QuitNow`: `game.quit by the owner (TruMenu) - logs flushed next,
then TerminateProcess(...)`, TO TEST list / history written, logs flushed, exit code 0x544D). **Pointing away**, a page
change, **B** and **closing** disarm (`game.quit (radial sector): disarmed - <why>`); 10 s without a second press as
well. The ring has no ImGui widgets, so the 0.8.1 id lesson is kept the other way round: the arm belongs to the
sector's item index, the label only shows the seconds. Its own arm time (the Status button's arm is separate). Only
`RadialTick` reaches it, from real pad / keyboard / mouse edges: no item, no TruLink command (`radial.open` only opens),
no TO TEST toggle, no favourite, no list, no shortcut. Log lines: `game.quit armed by the owner (radial sector 'Spiel
beenden', pad A) - ...`, `game.quit (radial sector): confirmed by the owner (pad A, second press after n ms)` or
`... held 1 s by the owner`, `... second press too fast (n ms) - still armed`.

The top level of the shipped file: Cheats, Marken, Zeit, Waffen, Spieler, Objekte + **Tests** + **Spiel beenden** = 8
sectors (more than 8 = pages; `trumenu_ini_check.py` counts them).

### Built-in level "Tests" (`[Radial] TestsLevel=1`, Mode=menu; owner request 2026-11-03)

No second copy of a list: the levels below Tests are made **every frame** from the lists the pages show (`g_tests` of
`TruMenu.tests.txt`, `g_reg` / column 9 of `TruMenu.regress_dlc1/2.txt`, under `g_testLock`) into one reserved level
slot; every action calls the page's own function, so log lines and result files are the same as on the pages.

| Level (label with counts) | Entries | A on an entry |
|---|---|---|
| `TO TEST n/m offen` | the **open** rows (steps not done, checks open; toggles are in Schalter), list order; steps `S<n> <text>`, checks their id | opens the row: **Run `<item>`** (only when the step's target / the check's id is a usable item and not one of `kRadForbidden` - never `game.quit`), **OK / Fail / Skip** (checks) or **Done** (steps), **Hint** (the hint under the ring; the centre shows it for every entry of the row). OK / Fail / Skip / Done = `TestMarkFromMenu` (`tests: test.mark <id> <state>`, `TruMenu.tests.txt` written) and back to the list |
| `Regression n/m offen` -> `DLC 1` / `DLC 2` / `Alle` `n/m offen` | every row with its state (`[ok]`, `[FAIL]`, `[skip]`, `[done]`) | the row: Run (steps with a target), OK / Fail / Skip (checks) or Done / `Wieder offen` (steps), **Prepare** (rows with a shortcut), Hint - `RegMarkFromMenu` (`TruMenu.regress_results.txt` as the page) |
| `Prepare (n)` | one entry per distinct regression shortcut (as the page's "Quick prepare"), `Stop` while one runs | `RunRegressPrepare` + `SetLastAction` (the page's Prepare button); the ring closes (its first command is a level change) |
| `Schalter n/m an` | the TO TEST **toggles** of the loaded list (e.g. `radial-spawn`, `radial-freeze`) with on / off | `TestMarkFromMenu(id, on / off)` - the page's checkbox (INI written at once / item run with 1 / 0) |
| `Rundgang` | `TruMenu.tour.txt` next to tru.exe, a level per section of the shader tour (Start, hall02, Yggdrasil-Ende, Maschinenraum, Halle Maschine-Zeremonie, Zeremonienraum, Halle Zeremonie-Goo, Goo-Raum, Nur in Zwischensequenzen, DLC 1) and of the hidden-content tour (Versteckt: golden shotgun, `container1`, extended ending) - 11 levels, 2 pages (0.10.2: the DLC 2 rooms below `Rundgang/DLC 2`, section "TruMenu 0.10.2") | the stop's command: `player.goto <intro id>`, `level.start dlc2 / dlc1`; a stop that needs a unit has a `Laden <unit>` entry (`level.load`) in front of it (once per unit); a stop without a command (cutscene, "RB halten") runs `status.unit`. Labels `NN <title>`, `(?)` = place unverified in the doc (04, 06, 17, 23) |

- `TruMenu.tour.txt` (38 entries: 28 stops + 10 `Laden`; 2026-11-03 afternoon: + level `Versteckt` - `Laden
  dlc_dungeon`, `26 Goldene Schrotflinte` = `player.goto 9475` (the `ma_rw_treasure` pickup), `27 container1: Test-Einheit
  (Saves sichern!)` = `level.load container1`, `28 Erweitertes Ende (Saves sichern!)` = `level.load l7_himalaya_end`) is
  written by `../bin/pyt -t 60 tools/tour_from_rundgang.py <workspace>\docs\Shader-Rundgang.md
  <workspace>\docs\Versteckte-Inhalte-Rundgang.md src\asi\TruMenu\TruMenu.tour.txt` (read-only on the docs, several
  docs in order; a stop whose only command is a `level.load` is that entry itself; `Laden` once per unit and section;
  first line `# TruMenu tour`) - also into the build folder `work\asi\menu0101` (data only, no rebuild; Set-TruMenu.ps1
  installs it from there); the radial file format and rules (forbidden ids dropped, unknown ids greyed), log `radial: tour n entries
  from ...TruMenu.tour.txt (0 dropped, 0 unknown, 0 lines skipped)`. `Build-TruAsi.ps1` puts it into the build
  folder, `Set-TruMenu.ps1 -Install` copies it next to tru.exe (ours = the marker line), `-Remove` deletes only ours.
  `trumenu_ini_check.py` checks it like the radial file.
- B on a row -> its list (the row picked), on a list -> the level above, on the first level -> Tests. A row that vanished
  (test.clear, regress.load) -> its list. With RememberPosition the ring reopens on the same virtual level, made anew.
- 0.10.1 also raises the TO TEST / regression list limit `kTestMax` from 64 to 128 rows: `Invoke-TruTestRun.ps1`
  sends the profile rows one by one and the 0.10 profile `regress_shadowlara_50l_radial` has 77 (rows 65 - 77 got
  "list full" with the 0.10 build), `_radial2` has 98 (94 + the two TruShadowCombat 0.4.1 switch steps / checks),
  `_50n_radial2` 62, `_50l_hud_radial2` 60. The virtual level holds up to 128 entries (a file level still 64).
- Deviation from the request: steps have no Fail / Skip (the TO TEST row kinds allow `done` / `open` only for steps);
  "TO TEST" shows checks as well as steps (both are open rows); the regression lists show all rows with their state;
  a note (Regression page "Note") is not offered (it needs the keyboard).

### Keys, status, check

| Key | Default | Meaning |
|---|---|---|
| `[Radial] Mode` | `menu` | `menu` / `wheel` (anything else = menu) |
| `[Radial] Freeze` | `world` | `world` / `1`, `player` / `2`, `0` (Mode=menu) |
| `[Radial] QuitSector` | `1` | the built-in "Spiel beenden" sector (Mode=menu) |
| `[Radial] TestsLevel` | `1` | the built-in "Tests" level (Mode=menu) |

`TruMenu.log` at the start: `0.10.1 radial: mode menu (stays open, A confirms, ...), freeze world (read again at every
open), quit sector 1 (built in), tests level 1 (tour 38 stops / entries), pause code ok, control code ok`; Status page
`radial (0.10.1): ... ; 0.10.1: mode menu, freeze world (ini now world; last open: ...), quit sector on / ARMED, tests
level on (tour ...)` (`radial.status`); `status.hooks` `radial=open (menu) (enabled 1, mode menu)`; `radial.list` names
the quit sector as `- | Spiel beenden | (built-in game.quit safety sector)` (the virtual levels are not listed).
`tools/trumenu_ini_check.py` checks the new keys (values in the INI: Mode menu / wheel, Freeze world / player / 0 / 1 / 2,
QuitSector / TestsLevel 0 / 1), the tour file and the limits with the built-ins (`--ini` / `--radial` / `--tour FILE`
check a copy - the negative test).

## TruMenu 0.10.2 (fixes from the 03.11. ring tests)

Built into `work\asi\menu0102` (asi, ini, radial, tour, `precheck_0102.txt`); compiled with 0 warnings in TruMenu.cpp,
`dumpbin` ok, byte checks 0102 (10) + the older lists 010 / 0101 / 071 / 072 / 080 / 081 / 09 (136): 0 mismatches,
`trumenu_ini_check.py` ok - offline only, **not yet seen in the game**. Owner note (German):
`<workspace>\docs\TruMenu-0.10.2.md`.

### `cheat.godfull` without flight (F15, los7 21:22:21)

0.8 - 0.10.1 set `GameTracker.cheatMode` bit 0: PlayerTakeDamage returns at once, but the same bit is the flight
cheat's switch (55 `test` sites gate player behaviour with it) - Lara flew. 0.10.2 leaves cheatMode alone and uses the
player's **own no-damage bit** `[0xfada74] & 0x20000` (the 2007 prototype's `ControlFlag` bit "rlwinm 14,14", workspace
`docs\Abakus-Pruefung.md` 18.7 and item 1):

| Site | Code | Effect of the bit |
|---|---|---|
| ApplyDamage 0x6f4f70 | first instruction 0x6f4f71 `test [0xfada74], 0x20000; jne ret` | no damage at all; ApplyDamage is the only code that lowers `P+0x628` (all `+0x628` writes in 0x6e0000..0x780000: 0x6f4e6c / 0x7000d9 refill, 0x6f4f2e GainHealth, 0x6f4fd7 / 0x6f5004 ApplyDamage, 0x6f55cc HealthInstantDeath) |
| PlayerTakeDamage 0x6f5030 | 0x6f5042, **before** the type 8 (raw) / 5 tests | types 8 / 5 are blocked too (cheat.god lets them through) |
| DamageBypass 0x6f5140, 0x703008 | the other two ApplyDamage callers | blocked |
| 0x721c8d | skips ProcessHealth 0x6f5160 | the hit timer / death check do not run while it is set (as in the game's death state, `mov [0xfada74], 0x40020208` at 0x75a447) |

Every player state entry rewrites the word (`mov [0xfada74], imm`), so `NoDamageTick` (PadHook, once per game frame,
before `GAMELOOP_Process`) ORs the bit in again - a state entry and a hit **in the same frame** can still let one hit
through. **Instant deaths** (`HealthInstantDeath` 0x6f55a0, callers 0x75afda in the death state's process / 0x75b099)
test neither this bit nor cheatMode: they still kill (the old variant only avoided them because Lara flew). The off
clears the bit only while the word is still the one the tick left (otherwise it is the game's own), sets
`gInvincibleCheat` 0 as before, and **ends a left-over flight**: cheatMode bit 0 set while `cheat.flight` is off ->
cleared + `INSTANCE_Post(player, 12, 0)` (as `cheat.flight 0`). Pre-check: the five tests and the call 0x6f50aa
(`g_godFullWhy` names them). Ring label: `Gott-Modus voll (ausser Sofort-Tod)`. Log: `cheat: god mode full ON (byte
0x00fadf60 = 1, mode flags [0x00fada74] = 0x...)`; answer `cheat.godfull 1 (gInvincibleCheat + no-damage bit ... per
frame, no flight; instant deaths still kill)`.

### `player.unstuck` / marks (F6, B28)

- **No sampling** while TruMenu or the ring is open, the time.pause bit (streamFlags 0x1000) is set, the main state is
  not 1, a **cinematic** runs (the game's own test tru+0x53f00 - `[0xe7f1c0] && byte +0xdd && dword +0x2c != -1`, the
  gate TruShadowPower 0.9 uses; read here, not called; bytes checked at load, `g_cineOk`), player control is off,
  `time.scale` is not 1, flight is on or health <= 0; the window starts again after each pause. los3 (20:35:58): the
  spot used lay ~7300 units above Lara (`-1311 4869 -683` vs `684 -1149 -7947`) - it was taken during the DLC 2 intro.
- **Ground test (heuristic, no proven on-ground flag):** 7 samples 5 game frames apart (~1 s); the middle one becomes a
  spot when every sample is within 12 units of the chord from the first to the last (free flight is a parabola: ~120
  units off over 1 s at ~980 units/s^2, 1 unit ~ 1 cm) and the slope first -> last is at most 0.8 plus 10 units for
  steps. Walking up / down ramps and over small bumps passes (los7: "height changed < 5 in 1 s" let almost nothing
  through on uneven ground). **Blind spots:** hanging at a ledge / shimmying, swimming at the surface, a moving
  platform look like ground.
- **Facing:** `player.mark` and every safe spot store Lara's yaw (instance +0x38); `player.recall` / `player.unstuck`
  write it back with the position (x / y rotation untouched). **Not done:** movement state and velocity - no
  player-state / velocity field and no "stand now" call is proven, so a recall during a jump or fall keeps that state
  (los7: she grabbed a ledge in reach). Recall while she stands.
- `player.safeground` (info, ring `Spieler/Helfer/Befreien: Stand`): `n safe spots, newest ...; mark set; ground windows
  a ok / b not; waiting: <reason>`. Start log: `0.10.2: cheat.godfull = no-damage bit ..., safe ground: 7 samples x 5
  frames, chord 12, slope 0.8 + 10, cinematic test 1, marks keep the yaw`.

### Tour and `level.start` (F8)

- `tools/tour_from_rundgang.py`: the "DLC 2 - <room>" sections of the shader tour go below **`Rundgang/DLC 2/<room>`**
  (8 rooms = one page); DLC 1, Versteckt, Paket-Ziele and "Nur in Zwischensequenzen" stay on the Rundgang level (5
  sectors). Every `level.start` stop gets a `Laden <start unit>` entry in front (dlc2 -> `dlc_level2_start`, dlc1 ->
  `dlc_level1_start`): `level.start` works from the main menu only (los7 21:22:37 `err main menu only (main state 1)`),
  the `Laden` entry is the in-level way (no intro). 33 stops, 46 entries, 12 sections.
- The ring greys `level.start` out outside the main menu (main state != 10): `main menu only - in a level: 'Laden ...'
  (level.load, no intro)`. The item itself is unchanged (TruLink / TO TEST / AutoStart).
- Note: `Laden dlc_level1_start` from DLC 2 is the cross-DLC load of F12 (Lara loads as the doppelganger; the fix is
  TruDlc2Player 0.3 `[Dlc2Player] CostumeReset`, offline) - without it, start DLC 1 from the main menu.

## TruMenu 0.10.3 (F7: sound with the world freeze)

Built into `work\asi\menu0103` (asi, ini, radial, tour, `precheck_0103.txt`); 0 warnings in TruMenu.cpp, `dumpbin`
ok, byte checks 0103 (15) + 0102 (10): 0 mismatches, `trumenu_ini_check.py` ok - offline only, **not yet heard in
the game**. Owner note (German): `<workspace>\docs\TruMenu-0.10.2.md`, section "0.10.3".

**Switches (both 0 = off by default, live test first):** `[Radial] FreezeSound=1` - while `[Radial] Freeze=world`
holds the world (the ring set the pause bit itself) the sound pauses too; `[Menu] PauseSound=1` - for every other
world pause in a level (`time.pause` from ring / menu / bar, `[Menu] PauseGame`). Items (runtime only, TruMenu.ini is
not written; a value changed in the ini is taken over within a second, so the TO TEST switches
`ini:TruMenu:Radial:FreezeSound` / `ini:TruMenu:Menu:PauseSound` work too): `time.freezesound`, `time.pausesound`
(bool), `time.sound` (info: switches, pause bit, gameMode, `[0xccde88]`, last action). Ring: `Zeit` -> `Ton mit
Rad-Einfrieren`, `Ton mit Welt einfrieren`, `Ton-Pause: Stand`.

**The game's functions (static, `tools/pe_dis.py` / `pe_callers.py` / `pe_abs_uses.py`):**

| Function | What it does | Callers |
|---|---|---|
| 0x5874b0 | `0x5873a0(1)`; `[0xccde88] = 1`; `jmp 0x4831c0` | pause menu open 0x5d47b6 (0x5d4780), 0x5d4821 (0x5d4810) |
| 0x5874d0 | `0x5873a0(0)`; `[0xccde88] = 0`; `jmp 0x4831d0` | pause menu close 0x5d4738 (only at gameMode 6), level start 0x5de4a5, level loads 0x5df80c / 0x5dfb7d / 0x5dfb8e |
| 0x5873a0(b) | for each index in the list `[0xccdea0]` (+0x1c count, +0x20 ints): bit 0 of `+0x10` of the sound group `[0x8a80d8] + index * 0x84` := b | the two above |
| `[0xccde88]` | 1 = the stream / music update 0x595250 (8 players at 0xcca9a0, 0x178 bytes) returns at once | set only by the pair, 0 at init 0x586435 |
| 0x4831c0 / 0x4831d0 | input manager 0xa02bd0: 0x4816f0 clears, 0x481750 sets again one byte flag in 4 slots of 4 pads | only the pair (rumble not proven: XInputSetState is called from 0x484940, another object) |

- **No counter, no toggle:** the pair *sets* a state - two pauses and one resume = running. `[0xccdea0]` is read
  without a null test and is 0 between levels (set 0x5df0c9, cleared 0x5df961) - TruMenu never calls the pair then.
  Which sound groups the list holds (sfx / voice / music?) is game data, not code. The window-focus pause
  (0x587410 / 0x587460, flag `[0xccde92]`, master group via 0x7b9490) is separate and not touched.
- **Balance with the pause menu:** the menu's open clears the pause bit 0x1000 itself and pauses the sound; its close
  resumes only at gameMode 6. TruMenu (`SoundFreezeTick`, game thread, every pad poll) acts only on the edges of its
  own want (the same answer on two polls), only when `[0xccde88]` is the other state, never at gameMode 6 (an own
  pause is dropped then - the menu resumes at its close), and once the game resumed the sound itself (level start /
  load) it is not paused again until the next freeze. A fault in a call turns the feature off (`__try`).
- Load check `SoundCheck`: both functions, 0x5873a0's list read, the reader 0x595253, the pause menu's open
  (gameMode 6 + call) and close (gameMode test + call). Start log: `0.10.3 sound with the freeze: code ok ...`.
- Log lines: `sound: sound paused (0x5874b0) - ring freeze, [Radial] FreezeSound`, `sound: sound resumed (0x5874d0) -
  pause bit cleared`, `sound: the pause menu opened - ...`, `sound: time.freezesound 1 (...)`.

**Light shaft (B29, not built):** the shader clock `TimeVector` (PS c53 / VS c23, uploaded at 0x5096c7 from
RenderDevice `[0xa1407c]` +0xfa4c / +0xfa48) advances by the dt of 0x5bf840 = `[0xe7f188]` (frame time x time scale),
which the pause bit 0x1000 does not stop (it only skips the instances). Only the pause menu stops it, through
0x5bfdf0(1) (`[0xdb94de] = 1`, back to 0 at the close 0x5d4765). So every `TimeVector` material keeps moving in the
freeze - in `dlc_level2_start.drm` (Xbox materials with `TimeVector`: 23157 = tuple 1058-1061, unlit one-texture
material with opacity and height fog, base twins in `l7_helheim0x` / `l7_yggdrasil_end` = the likely light shaft;
24920 eitr water surface, 24691 eitr column, 24736 / 26444 / 26445, 972 distortion). The unit's 41 objects contain no
light-ray object (`tools/objlist_unit_compare.py --units dlc_level2_start --list`), so the shaft is level geometry.
Proposal: a later `[Radial] FreezeShaders` calls 0x5bfdf0(1) / (0) with the same edge / gameMode-6 rules.

## TruMenu 0.10.4 (F7: shader clock with the world freeze; F6 stand state not built)

Built into `work\asi\menu0104` (asi, ini, radial, tour, `precheck_0104.txt`); 0 warnings in TruMenu.cpp (2 x C4100
in `imgui_demo.cpp` as before), exports / imports as 0.10.3, byte checks 0104 (14) + 0103 (15) + 0102 (10): 0
mismatches, `trumenu_ini_check.py` ok (60 keys) - offline only, **not yet seen in the game**. Owner note (German):
`<workspace>\docs\Befund-Menue-Dlc2Player-0411b.md`.

**Switch (0 = off by default):** `[Radial] FreezeShaderClock=1` - while the world is frozen in a level (pause bit
0x1000: the ring's `Freeze=world`, `time.pause`, `[Menu] PauseGame`) the shader clock `TimeVector` holds too. Item
`time.freezeclock` (bool, runtime only; a value changed in the ini is taken over within a second, TO TEST switch
`ini:TruMenu:Radial:FreezeShaderClock`), info `time.clock` (switch, pause bit, gameMode, `[0xdb94de]`, RenderDevice
+0xfa4c / +0xfa48, last action). Ring: `Zeit` -> `Shader-Uhr mit Einfrieren`.

**How the game makes the value (static, `pe_dis.py` / `pe_callers.py` / `pe_disp_scan.py`):**

| Step | PC | What |
|---|---|---|
| dt | 0x5bf840 (only caller 0x5cebc0, once per frame) | `[0xdb94de]` != 0 -> dt = 0 (`fldz`), else `[0xe7f188]` / `[0x8439b8]` (double 30.0; or `[0xe7f194]` / `[0x84bd00]` while `[0xe7f0b4]` & 0x10000000) |
| accumulate | RenderDevice `[0xa1407c]` vtable +0xc = 0x506f10(dt) | `+0xfa48` = dt; `+0xfa4c` += (int)(dt x `[0x8416d8]`, double 1000.0) - an integer accumulator (getter 0x509190; also written at 0x508900, `mov [esi+0FA4Ch], ebx`); only when the device state test at 0x506f67..0x506f7b passes |
| upload | 0x5096c7 | TimeVector = ((`+0xfa4c` mod 1000000) x `[0x8416d0]` (double 0.001), `+0xfa48`, 0, 0) -> PS c53 (0x509711) / VS c23 (0x509721) |
| hold | 0x5bfdf0(b) = `[0xdb94de]` := b | pause menu open 0x5d47ae (1), close 0x5d4765 (0), level start 0x5de3c7 (0), unknown menu 0x6e4887 / 0x6e548c |

The pause bit does not touch this path; the pause menu holds it with 0x5bfdf0(1): dt 0, the accumulator stays (x held,
y = 0), and after 0x5bfdf0(0) it goes on from the held value - **no jump, so no offset is needed**. TruMenu
(`ShaderClockTick`, game thread, every pad poll) calls the same function with the 0.10.3 sound rules: own edges only
(two polls agree), never at gameMode 6 (the pause menu owns the byte: claim dropped), the game's own release (level
start) is not fought. Load check `ClockCheck` (reader, setter, accumulator, upload, pause menu open / close). Log:
`shader clock: ON - TimeVector held (0x5bfdf0(1), ring freeze, ...): accumulator +0xfa4c N, dt ...`, `shader clock:
OFF - TimeVector runs on (0x5bfdf0(0), ...) after S s: accumulator N (held at N: unchanged = no jump)`, `shader clock:
the pause menu opened - ...`, `shader clock: the game released the clock itself ...`.

**Costume check:** the state save tru+0x155cb1 is accepted as the game's store or as TruDlc2Player 0.5's
`[Costume] TuMapping` detour (`jmp` out of tru.exe + 8 nops) - log `costume: state save 0x00555cb1 is a detour to ...
accepted`; 0.10.3 turns its costume items off in that case.

**F6 "Zur Marke" stand state - not built (`[Menu] MarkSetStand` not added):** no game function that puts the player
into standing was found offline. Every player state change on PC goes through the data-driven chart:
SCAgent::ChangeState tru+0x387890 (string `* Agent %d ChangeState to NULL is illegal!` 0x861070) is called only from
the agent's own transition / event code (tru+0x387c78 / 0x387d53 / 0x387d9e). The 2007 prototype map names the
script teleport `NsInstance::WarpTo` (position, stream unit, rotation only) and `INSTANCE_SetPositionPlayerFindGround`
(ground probe + `STREAM_SetInstancePosition` + `PLAYER_ResetSmoothRide`) - neither touches the state; a respawn builds
a new tracker / agent (initial chart state), which is not a teleport. Which chart state is "stand" is data, so a state
log (TruTrace) has to show it first. `player.recall` is unchanged.

## TruMenu 0.10.5 (screenshots, Claude marks)

Built into `work\asi\menu0105` - offline only, **not yet seen in the game**. Owner note (German):
`<workspace>\docs\Befund-TruMenu-Shot-0511.md`. Goal: the test session gets named in-game screenshots in the run
folder instead of ShareX files (no useful names, wrong times), and marks the player sets while playing.

**Screenshots.** Item `shot.save [ui|clean] [name]` (command bar, TruLink `menu shot.save <name>`, ring `Spieler` ->
`Screenshot`), the export `TruMenuShot(const char *name)` for other plugins, and the Claude marks below. A request gets
its file name at once: `[Shot] Folder` (default `TruShots\` next to tru.exe) + `shot_<HHMMSS>_<step>_<name>.png`,
`<step>` = `step<n>` of the lowest TO TEST step that is not done, else `-`; `<name>` sanitised to `A-Z a-z 0-9 _ - .`
(at most 40, empty = `-`); the same second / step / name again = `_2`, `_3`; a file left from an earlier session =
`-2` .. `-9`. The copy is taken by the existing Present hooks (device Present slot 17 and swap-chain Present slot 3 -
**no new hook**): before `Render()` = clean (no menu, ring, command bar or TruMenu overlay; default `[Shot] Clean=1`),
after it = as on screen (`shot.save ui ...` or `Clean=0`). On the render thread only: `GetBackBuffer(0)`, for a
multisampled back buffer `CreateRenderTarget` + `StretchRect`, `CreateOffscreenPlainSurface(D3DPOOL_SYSTEMMEM)` +
`GetRenderTargetData`, `LockRect` + row copy, all surfaces released in the same call (nothing is held over a Reset).
Pixel conversion (X8R8G8B8 / A8R8G8B8, R5G6B5, X1R5G5B5 / A1R5G5B5, A2R10G10B10), PNG encoding (`TruShotPng.h`, own
code: per-row PNG filter, fixed-Huffman deflate with a 32 KB hash-chain LZ77, CRC-32, Adler-32) and the file write
run on a worker thread (at most 2 at once; a request waits a frame while they are busy; queue of 4). One log line
per file:

```text
shot: <folder>\shot_142233_step3_lightshaft.png 1920x1080 1672169 bytes, capture <ms> ms (render thread), encode <ms> ms + write <ms> ms (worker); clean, TruLink
```

The capture time is the GPU sync of `GetRenderTargetData` and only known from a live run; the offline encoder test
took 255.5 ms for a synthetic 1920x1080 image (worker thread). Over TruLink the answer waits up to 2 s for the copy:
`ok captured <path> (the PNG is written on a worker thread ...)`; from the menu / ring / bar it is `ok queued <path>
...`. Refusals: `shots off ([Shot] Enabled=0)`, `no d3d9 device hooked yet`, `busy (...)`, `more than N shots per
minute ([Shot] MaxPerMinute)` (log line `shot: <source> refused - ...`, at most one per second). `shot.status` shows
the options, the folder, the counters and the last file / error.

**Claude marks.** Ring level `Claude` on the top level, drawn in coral #D97757 (217, 119, 87) with white text:
`Jetzt` (now), `Gut` (good), `Fehler` (bug), `Grafik komisch` (gfx), `Ton komisch` (sound), `Ruckler / Haenger`
(stutter) = item `claude.mark <kind>` (also command bar / TruLink `menu claude.mark bug`, export
`TruMenuMark(const char *kind)`, `[Shot] Hotkey` = `now`). Each writes one TruMenu.log line and requests a clean shot
named `<kind>`; the ring closes after the pick (play goes on at once; the shot is clean either way):

```text
HH:MM:SS.mmm claude.mark <kind>: <HH:MM:SS.mmm> unit=<stream unit> pos=<x> <y> <z> step=<step<n>|-> shot=<file|-> src=<ring|hotkey|menu|TruLink|TruMenuMark>[ (no shot: <reason>)]
```

`unit` = the stream unit Lara is in (as `[Log] UnitChanges`; else the unit at GameTracker+0x38, else `-`), `pos` =
Lara's position rounded (`- - -` without a player), `shot` = the file name in `[Shot] Folder`. Marks are rate-limited
like shots (`MaxPerMinute`, own window). To make room on the top level (8 sectors, one page), the R2 level `Objekte`
moved to `Spieler/Objekte` (`Claude` takes its sector; Cheats, Marken, Zeit, Waffen, Spieler, Tests, Spiel beenden keep
their places).

**Options** `[Shot]`: `Enabled=1` (requests only - nothing is taken automatically), `Folder=` (empty = `TruShots`
next to tru.exe, relative = below the game folder), `Clean=1`, `Hotkey=0` (e.g. `0x7A` = F11 -> `claude.mark now`;
the game still gets the key), `MaxPerMinute=30` (1 .. 120, 0 = no limit).

**Offline proof:** `selftest\TruShotPngTest.cpp` (built with the same x86 compiler, not part of the asi) encodes 8
test images in every supported format with padded rows; `tools/png_selftest_check.py` decodes each PNG on its own
(chunk CRCs, zlib / Adler-32, the five filters) and compares the pixels with its own conversion of the raw source
pixels: 8 / 8 equal. `tools/pe_import_export_diff.py` 0.10.4 vs 0.10.5: imports unchanged (141 functions, KERNEL32 /
SHELL32 / USER32; the D3D9 calls go through the device vtable), exports + `TruMenuShot`, `TruMenuMark`.
`tools/src_hook_sites_diff.py`: vtable patches 4 / 4, code writes 12 / 12, VirtualProtect 6 / 6, byte checks 147 / 147
- the new lines are 5 device calls in `ShotCapture`, 1 `CreateThread` (worker) and the 2 exports.
`tools/trumenu_ini_check.py` checks the `[Shot]` values and the Claude level.

## TruMenu 0.11 "Ablauf" (guided test runs)

Owner wish 2026-11-05 (stage 2 of the Claude marks): a test run is a **flow** of steps that the ring shows one after
the other, with counters that fill themselves from the plugin logs. Built into `work\asi\menu011`; compiled, offline
checks only - **not yet seen in the game**. Everything is off without `[Flow] Enabled=1` (the profile sets it); the
ring entries of the flow are then greyed out ("kein Ablauf").

### `TruMenu.flow.txt` (next to tru.exe, `[Flow] File`)

UTF-8 (BOM optional), one record per line, fields separated by `|` (so `|` cannot appear inside a field), `#` lines and
empty lines skipped. First line `# TruMenu flow ...` = ours (`Set-TruMenu.ps1`, `Invoke-TruTestRun.ps1`). Written by
the workbench generator `New-FlowFile.ps1` from a test profile; the parser is `TruFlowCore.h` (own code) and the same
rules in PowerShell in `Invoke-TruTestRun.ps1` / `Test-TruPreflight.ps1`.

```text
flow    | <id> | <title>                               once, optional
counter | <id> | <source> | <target> | <text>          target 0 = only counted
step    | <id> | action|observe|mark | <text> [| key=value ...]
```

| Step kind | Weiter (`flow.next`) | Gut / Fehler (`claude.mark good / bug`) | other Claude mark |
|---|---|---|---|
| `action` | runs its `do=` commands (the regression-shortcut path: one command per free game-thread slot, `level.*` waited for, an `err` stops); ok when they are done and (if any) a `check=` is met | ok / fail | recorded on the step |
| (any kind) | | | `mark:<name>` conditions and `mark:` counters see it |
| `observe` | leaves it open (no result) and goes on | ok / fail | recorded |
| `mark` (an instruction) | done (ok) | ok / fail | done (ok) |

| Step key | Meaning |
|---|---|
| `do=<cmd>;<cmd>` | action only; at most 12 commands / 319 characters (`kShortcutLen`), never `game.quit`, no `#title` |
| `after=<cond>` | all must be met before Weiter runs an action (repeatable, at most 4); the status line shows "wartet: ..." |
| `check=<cond>` | any one met after the step started = ok (an action: after its commands); at most 4 |
| `fail=<cond>` | any one met after the step started = fail; at most 4 |
| `count=<counter>[,<counter>]` | at most 4; the first one is shown in the status line |
| `skip=<reason>` | skipped when the flow reaches it |
| `hint=<text>` | third line of the status line / the ring centre |

Conditions: `step:<id>` (that step ok), `done:<id>` (ok / fail / skip), `counter:<id>` (target reached; target must
be > 0), `mark:<name>` (a Claude mark of that kind while the step is current: `now`/`Jetzt`, `good`/`Gut`,
`bug`/`Fehler`, `gfx`/`Grafik`, `sound`/`Ton`, `stutter`/`Ruckler`), `log:<TruX.log>:<pattern>`,
`trace:<category>:<pattern>` (TruTrace.log lines `time [unit] <category>: text`, an empty pattern = any line).

Counter sources:

| Source | Counts | From |
|---|---|---|
| `units[:<unit>]` | stream unit slots that became loaded | TruTrace 0.2 `stream: stream unit slot n: id x '<unit>' state 2 = loaded` |
| `levels[:<unit>]` | level loads (result of `STREAM_LevelLoadAndInit`) | TruTrace 0.2 `level: STREAM_LevelLoadAndInit '<unit>' (...) -> unit entry` |
| `restores` | checkpoint restores | TruTrace 0.2 `save: SAVE_RestoreGame(n) -> r` |
| `deaths` | player deaths | the rising edge of bit 0x10000 of the player state-mode word `[0xfada74]` (below) |
| `toggle:<id>` | TO TEST switch flips | `test.mark <id> on/off` (page, ring Schalter, TruLink) |
| `item:<id>` | runs of an item (not info reads) | `InvokeCore` (menu, ring, bar, TruLink, shortcuts) |
| `mark:<name>` | Claude marks of that kind | `claude.mark` (ring, hotkey, TruLink, `TruMenuMark`) |
| `log:<TruX.log>:<pattern>` / `trace:<cat>:<pattern>` | matching lines | the tail below |

Patterns: plain text = substring (case-sensitive); `re:<expr>` = a regex subset (literals, `.`, `\d \w \s \D \W \S`,
escaped punctuation, classes `[a-z]` / `[^...]`, the postfix `* + ?`, `^` first and `$` last; no groups, no `|`, no
`{n}`), matched as a state set (linear in the line, no backtracking). Texts are shown in ASCII (`ae oe ue ss`).
Limits: 64 steps, 16 counters, 48 distinct log patterns, 8 log files, 159 bytes per text.

**Why the log tail and not a TruTrace export:** TruTrace writes the unit / level / restore lines anyway; reading them
needs no interface between the two plugins (no load-order or version coupling, no change to TruTrace, works with an
older TruTrace for the other counters and degrades to "0" without it). TruMenu's own tail (worker thread, every
`[Flow] PollMs` = 500 ms) reads **every** new byte of the files the flow names (at most 256 KB per file and poll; more
is skipped with a log line), not the 6 KB window of the log page. TruTrace rate-limits its categories (40 lines / s) -
unit / level / restore lines are far below that. A pattern line is "after the step started" with poll granularity.

**Player deaths (static, `tools/pe_flag_bit_writers.py data/pc/tru.exe 0xfada74 0x10000`, pinned in
`work\asi\menu011\precheck_011.txt`, 14 / 14 ok):** of the 33 instructions that write `[0xfada74]` only one sets bit
0x10000: `or dword [0xfada74], 0x10408` at 0x75aa69 in `DeathState::Entry` 0x75aa50; 11 clear it (the immediate stores
of every other state entry and the store of ecx = 0x81 at 0x7522da), 20 keep it, 1 (0x752320, ecx = 0x81 from 0x7522d5,
no ecx write in between - read by hand) clears it too. TruMenu reads the word once per frame (render thread, no hook)
and counts a rising edge while a player exists; the bytes at 0x75aa69 are checked at load (mismatch = deaths not
counted, said in the load line).

### Ring level "Claude" (TruMenu.radial.txt)

Page 1: **Weiter** (`flow.next`, label "Weiter: <current step>"), **Ueberspringen** (`flow.skip`), Jetzt, **Gut**,
**Fehler**, Grafik komisch, Ton komisch, Ruckler / Haenger (the 0.10.5 marks, order kept); page 2 (RB): **Zurueck**
(`flow.back`), **Ablauf n/m** (`flow.status`). The centre shows the current step, its hint and what it waits for. Gut /
Fehler write the 0.10.5 mark line + clean shot and set the current step ok / fail; Weiter that ran / finished a step
closes the ring (as a mark does). Shot names use the current flow step instead of the TO TEST step.

### Status line, toast

`[Flow] Overlay=1`: `Claude-Ablauf  Schritt n/m | <counter a/b> | naechster: <text>` in coral in the corner
`[Flow] Position` (tl / tr / bl / br, default br), `Size`, `Lines` (2 = + the current step, 3 = + waits for / hint).
`flow.say <text>`: a coral toast at the top for `[Flow] ToastSeconds` (6 s). Both drawn by TruMenu (not in clean shots).

### Items (TruLink `menu <id> [arg]`, command bar)

| Item | Meaning |
|---|---|
| `flow.status` | file, step n/m with state / waits for, results, deaths, every counter (one line) |
| `flow.list` | every step `n id kind state by` (`>` = current) |
| `flow.next` / `flow.back` | Weiter / Zurueck (the step before is reopened) |
| `flow.skip [<id> [reason]]` | skip (no id = the current step) |
| `flow.goto <id>` | that step is current (reopened) |
| `flow.add <record>` | append a counter or step record (file syntax) |
| `flow.say <text>` | toast + log line |
| `flow.result ok` / `fail [note]` | = `claude.mark good / bug` (+ the note on the step) |
| `flow.reload` | read the file again (all states anew) |

TruLink needs no change (`menu` passes the rest of the line), but its tokenizer keeps at most 24 words per line and
joins them with single spaces: a long `flow.add` record is cut, double spaces in a pattern become one.

### `TruMenu.log` lines (Invoke-TruTestRun.ps1 builds the summary section "Ablauf" from them)

```text
flow: loaded <path>: n steps, m counters, w log patterns, e errors (id <id>: <title>); deaths counted (...)
flow: error line <n>: <message>
flow: step <id> start|run|open|ok|fail|skip <i>/<n> t=<s since load> [dur=<s>] [by=<Weiter|Gut|Fehler|auto|commands|file|...>] [note=<text>]
flow: counter <id> <value>/<target> t=<s>[ reached]          (at most one line per counter and second)
flow: mark <kind> step=<id|-> shot=<file|-> t=<s>
flow: death <n> ([0x00fada74] = 0x..., DeathState entry bit 0x10000) t=<s>
flow: say <text> | flow: add <record> -> ok|err ... | flow: goto <id> | flow: done ... | flow: end (game.quit) ...
```

### Keys, checks

| Key | Default | Meaning |
|---|---|---|
| `[Flow] Enabled` | `0` | 1 = read the flow file (worker thread), tail the logs it names, flow entries in the ring |
| `[Flow] File` | `TruMenu.flow.txt` | relative = next to tru.exe |
| `[Flow] Overlay` / `Position` / `Size` / `Lines` | `1` / `br` / `1.0` / `2` | status line |
| `[Flow] AutoAdvance` | `1` | a step finished by check / fail / its commands moves on |
| `[Flow] ToastSeconds` / `PollMs` | `6` / `500` | toast time, tail interval |

Offline checks: `/W4` 0 warnings in `TruMenu.cpp` / `TruFlowCore.h`; `tools/pe_import_export_diff.py` 0.10.5 vs 0.11:
exports unchanged, one new import `KERNEL32!GetFileAttributesExA` (the tail's start size); `tools/src_hook_sites_diff.py`:
no new hook / patch / write, one new byte pre-check (0x75aa69); `tools/trumenu_ini_check.py` (`[Flow]` values, flow
items, the flow entries in the level Claude); `selftest/TruFlowCoreTest.cpp` + the workbench test compare the C++
parser / matcher with the PowerShell parser and .NET Regex.

## TruMenu 0.12 "Debug-Zeichnung" (NavPower debug drawing, debug view stage S0)

Built into `work\asi\menu012`; compiled, offline checks only - **not yet seen in the game**. Owner notes (German):
`<workspace>\docs\Befund-Debug-Ansicht-0511.md` section 1.1 (the research) and `<workspace>\docs\Befund-TruMenu-Debug-0511.md`
(this build). Everything is off without `[Debug] Enabled=1`; the ring entries are greyed then.

**What it switches.** The Steam `tru.exe` contains the complete debug drawing of the NavPower ("BabelFlux", `bfx`)
middleware: 39 `BoolSetting` objects (vtable 0x841144, `tools/bfx_settings_dump.py`), each pointing at one switch byte in
`.bss` (0 in retail; `tools/pe_abs_uses.py`: no instruction writes them). Every game frame 0x5da141 -> 0x489c60 ->
`jmp 0x42f900` runs the draw function of every NavPower component while `[[0x8c0f0c]+0x10] == 1`; the planner's
(0x418870, registered at 0x4211ad) calls the planner draw 0x418680 and the obstacle draw 0x407690 and draws the recent
navprobes. Lines go through Crystal's renderer bridge `CDCRenderer` (vtable 0x845224, object `[0x8c0f3c]`) slot 0
0x48a500 -> `DRAW_DrawLines` 0x5bfcd0. TruMenu only writes those data bytes (and the layer mask below) - **no game code
is changed, no new hook**. Middleware text goes to the empty stub 0x6457a0 (invisible), so only line switches are offered:

| Switch (`nav.draw <name>`) | Byte | Reader(s) | Draws | Note |
|---|---|---|---|---|
| `planner_areas` | 0x8bf2e5 | 0x41869c, 0x40c3a0 | navmesh areas, outline | drives the per-area loop |
| `planner_areas_solid` | 0x8bf2e6 | 0x4186a5, 0x40c3ba, 0x40c68d | navmesh areas, filled | drives the per-area loop; cost unknown |
| `planner_connectivity` | 0x8bf2e7 | 0x40c8bb | a line from each area to each neighbour | **only with `planner_areas` or `_solid` on** |
| `planner_area_normals` | 0x8bf2ec | 0x40c7c8 | the normal of each area | **only with `planner_areas` or `_solid` on** |
| `obstacles` | 0x8bf308 | 0x407690 | dynamic obstacles (list `[0x8bf2f8]`) | own path |
| `recent_navprobes` | 0x8bf309 | 0x418880, 0x420583, 0x4205bf | the latest navmesh probes of the AI | the probe query 0x420580 records each probe while on (one extra call 0x41b4b0 in the query path) |
| `draw_mover3d_path` | 0x8bf006 | 0x40432d | the path of each Mover3D | flyers only (list `[0x8bf00c]`, component 4) - probably empty in the Yggdrasil units |

Why connectivity / normals need the areas: 0x418680 jumps over the whole per-layer loop (0x416750 -> 0x413250 -> per area
0x40c3a0) unless `planner_areas` or `planner_areas_solid` is set; both are read only inside 0x40c3a0. The answer and the log
line say so.

**Layer mask `[0x88e454]`** (dword, `.data`, file value 0xffffffff; 5 references in the exe: 4 reads in 0x418680, the only
writer 0x48aa23 in the CDC init, which sets `(1 << n) | (1 << (n + 16))`, n = `[0xa03590]`). The planner draws nothing when
it is 0 and layer i (of 32) only when bit i is set. `nav.mask 1` writes the file value 0xffffffff (every layer) and keeps
the value before; `nav.mask 0` / `nav.off` write that value back - unless the game changed the mask meanwhile (then it
stays). The mask is used by nothing but the draw function. `nav.status` lists the layers that hold something (tested as
0x4186bb .. 0x4186cd: bit i, `[[0x8bf310] + 4i] != 0`, `[layer + 8] != 0`), so a missing drawing can be told apart from a
mask that leaves the navmesh layers out.

### Items (TruLink `menu <id> [arg]`, command bar)

| Item | Meaning |
|---|---|
| `nav.draw <switch> [0\|1]` | one switch; no 0 / 1 = flip; no switch = usage + every state |
| `nav.mask [0\|1]` | bool: layer mask = 0xffffffff / the value before |
| `nav.off` | every switch TruMenu wrote back to the value before its first write (0 in retail), then the mask |
| `nav.status` | read-only, any time: `[Debug]`, check results, CDCRenderer / line buffer / NavPower state, mask, layers, every switch |

Guards of every write (as `CheatGate` + `instance.spawn`): `[Debug] Enabled=1`, `[Cheat] Experimental=1`, the byte
checks below, a player instance, main state `[0xe7ed60]` = 1, no level change pending (`GameTracker+0xb9`, main state 2 /
9) - never while loading -, `[0x8c0f3c]` = an object with vtable 0x845224, line buffer `[0x8c0f48]` != 0; per switch at
run time the setting object still pairs name and byte (`[obj]` = 0x841144, `[obj+0xc]` = the name string, the string itself,
`[obj+0x10]` = the byte). The items run on the calling thread (one byte / dword write each; no game function is called).

### Ring level `Spieler/Debug` (TruMenu.radial.txt)

Page 1: Navmesh Flaechen, Navmesh gefuellt, Navmesh Verbindungen, Hindernisse, Nav-Proben, Laufweg (Flieger), Alle Ebenen
(`nav.mask`), Alles aus (`nav.off`); page 2 (RB): Flaechen-Normalen, Debug: Stand (`nav.status`). Each switch shows on /
off: an entry `nav.draw <switch>` (one word) is treated as a bool of that switch byte, the ring sends
`nav.draw <switch> 0|1`. Below `Spieler` so the top level keeps its 8 sectors (as `Spieler/Objekte` in 0.10.5).

### `TruMenu.log` lines

```text
0.12 debug drawing: [Debug] Enabled <0|1> (NavDraw <list|->, NavMask <0|1>), draw path ok, layer mask ok (0x<mask> now), 7 / 7 switches ok
nav.draw <switch> <0|1> (byte 0x<addr> <before> -> <after>; <what it draws>; mask [0x0088e454] = 0x<mask>, layers <n n ..|none|no planner> (0x<bits>), NavPower state <s>; src=<ring|menu|TruLink|[Debug] NavDraw>)[ - <note>]
nav.draw <switch> <0|1> refused - <reason> (src=...)
nav.mask <0|1> ([0x0088e454] 0x<before> -> 0x<after>: <every layer|the value before|...>; layers ...; src=...)
nav.off: <n> switch(es) back to the value before (<names>|-), <n> failed; <mask answer> (src=...)
nav: [Debug] NavDraw / NavMask applied in the first loaded level: <n> ok, <n> failed
```

Notes after `nav.draw`: `draws only together with planner_areas / planner_areas_solid ...`, `layer mask [0x88e454] = 0:
the planner draws nothing (nav.mask 1)`, `no layer that holds a navgraph is in the layer mask (nav.mask 1)`.

### Keys, checks

| Key | Default | Meaning |
|---|---|---|
| `[Debug] Enabled` | `0` | 1 = the nav items may write (ring entries usable) |
| `[Debug] NavDraw` | (empty) | comma list of switches turned on once in the first loaded level (game thread, same guards) |
| `[Debug] NavMask` | `0` | 1 = with NavDraw also `nav.mask 1` |

**Byte checks** (`NavCheck` at load; pinned in `work\asi\menu012\precheck_012.txt`, `tools/pe_bytes_check.py` on the Steam
exe: 33 / 33 ok; `tools/trumenu_precheck_match.py`: the 33 lines = the 33 checks in the source section): the draw path
(CDCRenderer creation 0x48a95f, vtable slot 0, frame calls 0x5da141 / 0x489c68, component loop 0x42f98a, planner
registration 0x4211ad, planner frame draw 0x418870), the mask (its 4 reads + its only writer 0x48aa23), the area chain
(0x4167a4, 0x4132d2), per switch its readers and the static initialiser that stores name and byte into the setting object
(e.g. 0x83098e `c7053cf48b0000268400 c70540f48b00e5f28b00` for `planner_areas`). A failed check greys that switch (or all
of them) with the reason; one log line per disabled switch.

Offline checks: `/W4` 0 warnings in `TruMenu.cpp`; `tools/pe_import_export_diff.py` 0.11 vs 0.12: imports and exports
unchanged; `tools/src_hook_sites_diff.py`: no new hook, patch or VirtualProtect, 1 new raw store (the mask dword), 11 new
byte pre-check lines (= the 33 checks, the table rows run in one loop); `tools/trumenu_ini_check.py` (`[Debug]` values, the
nav items, the nav entries of the radial file: `nav.draw` one switch name of `kNavSwitches`, the others without argument).

**TO TEST (0.12)** - `[Debug] Enabled=1`, `dlc_yggdrasil_hall02`:

1. `TruMenu.log`: `0.12 debug drawing: ... 7 / 7 switches ok`.
2. Ring -> Spieler -> Debug -> Navmesh Flaechen: lines on the floor = the engine drawing works on PC (log `nav.draw
   planner_areas 1 ...`, note the layers and the mask). Nothing: Alle Ebenen, look again; still nothing = the lines do
   not reach the screen (`DRAW_DrawLines` path) - `nav.status` into the log (Debug: Stand).
3. With the areas on: Navmesh Verbindungen, then Nav-Proben near thralls, Hindernisse; frame rate with Navmesh gefuellt.
4. Alles aus: everything gone, log `nav.off: n switch(es) back ...`.

## TruMenu 0.13 "Thrall-Labels" (debug view stage S1, F28)

Built into `work\asi\menu0130` (`menu013` already held an older build from 31.10. and was not touched); compiled, offline
checks only - **not yet seen in the game**. Owner notes (German): `<workspace>\docs\Befund-Thrall-Labels-0511.md`. Off
unless `[Debug] Enabled=1` and `dbg.labels 1` (ring `Spieler/Debug` -> Thrall-Labels, or `[Debug] Labels=1`).

**What it draws.** Every Present while on, in a loaded level only (player instance, main state 1, no level change
pending - the guards of `nav.draw`): for the instances within `[Debug] LabelRadius` of Lara whose object name contains a
part of `[Debug] LabelMatch` (default `thrall`; `*` = every instance), thralls first, then the nearest, at most
`LabelMax`, a label in ImGui's foreground draw list at the projected instance position (+0x20):

* line 1: object name, intro id (+0x58), distance to Lara (game units), `LP <hit points>` for names containing `thrall`
  - EnemyProcessFunc 0x638d40's own value: brain = `[[inst+0x2d0]]+0x2ec` (0x638d59), hit points brain+0x2c64 (the value
  `cheat.enemyhealth` prints at 0x638edd);
* line 2 (only with TruShadowCombat 0.5.3, export `TscTargeterSnapshot`): `Z9 ZIEL` (yellow, targeter 9's target),
  `Z9 Fach <g>` (green, in the bucket of filter group g), `Z9 abgelehnt E0` / `F<xx>` / `(Grund ?)` (orange, in the
  rejected list: eligibility tru+0x2ecca0 failed / filter groups passed as a bit mask / not evaluated yet - the last WHY
  result of TruShadowCombat's diagnostics), `Z9 -` (white, not in targeter 9), ` | H` (in the player's hit list
  `[[0xfadb58]+0x504]+0xa4`), ` | 2011 Pfad <p> q<query> = <result> (<age>s)` (the last condition 2011 had this instance
  as target; path 1 empty / excluded, 2 query 0x161 = 0, 3 ok);
* a magenta cross at Lara's position (`[Debug] LabelCross`, default 1) - the live check of the projection.

No state-chart state id: the only chart machine constructor tru+0x3873c0 has one caller (tru+0x2eff9a, the player's
machines at playerstate +0xf10..); where the thralls' charts run is unknown, so nothing is shown (translate, don't
imitate).

**Projection = the game's own text-at-an-instance path** (EnemyProcessFunc's health text 0x6224e0, not the TRANS matrix
0xa038f0 that `draw.markup` reads - that one holds whatever 0x49f620 set last): matrix = the address the getter 0x5e7890
returns (0xe804a0), projected like TRANS_RotTransPersVectorf 0x49f630 (`x' = m[0] x + m[4] y + m[8] z + m[12]`, ...;
screen `x = x' / z' * f + 256.0`, `y = y' / z' * f + 224.0`, f = `[0x8906d0]`), drawn when `16.0 < z'` (0x62257b).
0xe804a0 is written once per game frame by the camera update 0x5f3df0 (called at 0x5d46a9, right after the instance
walk): a copy of the camera's world -> camera matrix, column x scaled by `(4 / 3) / aspect` (0x5c59f0, aspect =
`[[0xad75e4]+0x170] / 10000`), column y by `448 / 384` (0x5e7b30); `f = 192 / tan(fov / 2)` (0x5f3ef6, tan = 0x813870
with `fptan`, stored by 0x49f610). So the text space is 512 x 448 with a vertical field of view; it is scaled to the back
buffer with `draw.scale` (default 512 448, shared with `draw.markup`). Constants and the derivation: `tools/pe_dis.py`,
`tools/pe_float_consts.py` (new, logs `labels0511_*`).

**Live checks** (cannot be done offline): the magenta cross must sit on Lara's origin (feet); with `cheat.enemyhealth 1`
the game's own `%8.2f` hit points must appear at the anchor dot of a thrall's label (same matrix, same projection); if
the cross is offset by a constant factor, `draw.scale <w> <h>` fixes the text-space size (log line below prints the
matrix, focal, aspect, back buffer and Lara's projected point every 10 s).

### Item, ring, keys

| Item / key | Default | Meaning |
|---|---|---|
| `dbg.labels [0\|1]` | 0 | bool; needs `[Debug] Enabled=1` and the byte checks; may be switched outside a level (draws in the next one) |
| `[Debug] Labels` | `0` | 1 = on from the start (needs `Enabled=1`) |
| `[Debug] LabelRadius` | `3000` | game units, 100 .. 50000 |
| `[Debug] LabelMax` | `12` | 1 .. 32 |
| `[Debug] LabelMatch` | `thrall` | comma list of name parts, `*` = every instance |
| `[Debug] LabelCross` | `1` | the magenta cross at Lara |

Ring `Spieler/Debug`: entry 11 "Thrall-Labels" (page 2), shows on / off. Cost per frame: one walk of the instance list
(position read, distance test; the name test is cached per object id), at most 32 projections and labels; fixed static
buffers, no allocation by TruMenu (ImGui reuses its draw list buffers). TruShadowCombat builds its copy on the game
thread only while TruMenu asked within 2 s.

**Byte checks** (`LabelCheck` at load; pinned in `work\asi\menu0130\precheck_013.txt`, `tools/pe_bytes_check.py` on the
Steam exe: 20 / 20 ok; `tools/trumenu_precheck_match.py --from "---- 0.13 Thrall-Labels" --to "---- favourites"`: 20 =
20): the game's instance-text path (0x5e7890, 0x6224ed, 0x62257b), the camera update (0x5d46a9, 0x5f3e25, 0x5e7b30,
0x5e7b5d, 0x5e7b87, 0x5c59f1, 0x5f3ef6, 0x5f3f19, 0x49f610), the projection and its constants (0x49f6f8, 0x49f702,
0x49f713, 256.0 at 0x843a00, 224.0 at 0x8454c8, 16.0 at 0x8451e4), the health chain (0x638d59, 0x638edd); plus the 0.3
instance-list, player and main-state checks. A failed check disables `dbg.labels` with the reason.

### `TruMenu.log` lines

```text
0.13 thrall labels: checks ok; [Debug] Labels <0|1> (on now <0|1>), LabelRadius <r>, LabelMax <n>, LabelMatch '<list>', LabelCross <0|1>; projection matrix 0x00e804a0, focal [0x8906d0], text space 512 x 448 (draw.scale)
0.13 thrall labels: <TruShadowCombat not loaded | TruShadowCombat without TscTargeterSnapshot (older than 0.5.3) | export found>
dbg.labels <0|1> (src=<ring|menu|TruLink>)
0.13 thrall labels: <n> shown (<k> thralls), <m> in <r> units; TruShadowCombat: <state>; matrix 0xe804a0 rows ...; t ...; focal <f>, aspect [[0xad75e4]+0x170] <a>, back buffer <w> x <h>; Lara (<x y z>) -> screen <sx> <sy>
```

The last line comes with the first labelled frame after `dbg.labels 1` and then every 10 s while on (log only).

**TO TEST (0.13)** - `[Debug] Enabled=1`, TruShadowCombat 0.5.3 (`work\asi\combat053`), `dlc_yggdrasil_hall02`:

1. `TruMenu.log`: `0.13 thrall labels: checks ok`; `TruShadowCombat.log`: `0.5.3 snapshot: TscTargeterSnapshot ... on`.
2. Ring -> Spieler -> Debug -> Thrall-Labels: magenta cross on Lara, a label above each thrall (name, intro id,
   distance, LP). `cheat.enemyhealth 1`: the game's number at the label's dot?
3. Knock a thrall down, stand next to it, power on: line 2 changes `Z9 -` -> `Z9 abgelehnt ...` / `Z9 Fach 0` /
   `Z9 ZIEL`; X / Y at the thrall: `2011 Pfad ...` on its label.

## TruMenu 0.14 "Debug view" (triggers, loading areas, checkpoints, object names; debug view stage S3)

Built into `work\asi\menu014`; compiled, offline checks only - **not yet seen in the game**. Owner notes (German):
`<workspace>\docs\Befund-TruMenu-Trigger-0611.md`. Everything is read-only (no game memory written, no game function
called) and off unless `[Debug] Enabled=1` plus a layer switch. Drawn at Present (background draw list; legend in the
foreground) in a loaded level only - player instance, main state 1, no level change pending, the gates of `dbg.labels`;
nothing about Lara's own state, so it keeps drawing during the 0.8.1 flight (`cheat.flight`, RT up / LT down). Fixed
static buffers, nothing allocated by TruMenu per frame; projection as 0.13 (matrix 0xe804a0, 0x49f630) plus clipping of
every line at the near plane (`z' > 16`), so a box the camera stands in still shows its visible edges.

**Triggers (`dbg.triggers`, per kind `dbg.show <kind>`).** The two lists the game tests every frame (0x5cd520): planes
`[0xdba21c]` / 0xda61c8, volumes `[0xdba220]` / 0xdb6be0 (at most 0x200 each, adders 0x5c8990 / 0x5c89e0); entry +0x20 =
the trigger instance, +0x24 bit 31 = enabled (0x4a4360; disabled entries are skipped by the game and drawn dim), bit 30
= tested against the player (0x4a4450). Data = `[[instance+0x100]+0x78]` (IntroDataTrigger). Drawn the way the engine
tests them:

* volume, shape byte +0x30 = 1 (box): centre = instance +0x20, half extents +0x34 / +0x38 / +0x3c along the rows of
  `M = Rz * Ry * Rx` from the instance Euler angles +0x30 (0x49d500: identity post-multiplied by 0x49bd40 / 0x49bc70 /
  0x49bb90, cos 0x813420 / sin 0x813680; row vectors). The game tests through the quaternion of M (0x49d720) as
  `|conjugate(q) rotated (p - centre)| <= h` (0x46b730, Hamilton product 0x49c940), i.e. corner = centre + (+-h) * M -
  12 lines. `tools/trigger_box_math.py` checks the closed form against those steps (2000 random cases: 0 matrix
  elements off, 16000 / 16000 corners inside at x0.999 and outside at x1.001, 8000 / 8000 plane corners equal; the
  transposed matrix fails as it must);
* volume, shape 2 (sphere): squared distance to instance +0x20 below radius +0x40 squared (0x4355d0) - 3 circles;
* plane (0x5ccc20): the quad `(+-w, 0, +-h) * M + instance +0x20` (0x435220 -> 0x49ba20 adds row 3), w = +0x34,
  h = +0x3c; byte +0x44 = 0 = one-sided (the crossing direction is tested) -> an arrow along row 1 (the quad normal).
  The game tests the segment of the player's test point between two frames against the two triangles (0x461640);
* the test point itself: player +0x20 + (0, 0, 200.0) (`[0x853f08]`) - a white cross.

Kind (colour) from the trigger instance's object name, first match wins: `checkpoint` (green), `death` / `kill` (red),
`fire` / `burn` / `flame` (orange), `water` / `swim` (blue), `sound` / `swoosh` / `audio` / `music` / `sfx` (violet);
no keyword = plain volume (yellow) / plane (cyan); no intro data, unknown shape or no name = unknown (grey). A full
memory dump of DLC 2 (30.10., `dlc_level2_start` + `dlc_yggdrasil_hall01` loaded, `tools/debugview_dump_check.py`) holds 7 planes (`triggerplane`) and 19
volumes (`triggervolume`, `soundvolume`, `soundtriggervolume`), all boxes; the generic names carry no death / fire
meaning there - what a plain trigger does is in its script, which 0.14 does not read. Selection: the triggers nearest to
the camera first, at most `[Debug] TriggerMax` (64) within `TriggerRadius` (20000 units from the camera, so it still works
from high above), names for the nearest `TriggerLabelMax` (`dbg.show trglabels`: object name, intro id, B / K / E1 / E2
= box / sphere / one-sided / two-sided plane, `(aus)` = disabled).

**Loading areas (`dbg.portals`).** Every loaded stream unit (table 0xdbab40, state 2): entry +8 Level, `[Level]`
Terrain, Terrain +2 s16 count, +4 array of 0x100-byte StreamUnitPortal (0x5d295f, 0x5d2ab5); quad corners +0xb0 /
+0xc0 / +0xd0 / +0xe0, normal +0xf0 (layout from the unit DRMs; in the DLC 2 dump the two records of the
`dlc_level2_start` <-> `dlc_yggdrasil_hall01` connection lie on the same quad, normals opposite). White quad, diagonals,
normal arrow, label `<unit> -> <destination>`. What actually starts a unit load is the signal geometry of a terrain group
(0x5d2ca0 -> 0x5d2aa0); the quad is the portal's boundary.

**Checkpoints (`dbg.checkpoints`).** Instances whose object name contains `checkpoint` (`checkpoint`,
`invis_checkpoint`, `dlc2_checkpoint`): a post with a diamond and `CP <intro id>`; the active one (game data
`[0xc59264]` +0x90, +0x114 when the word +0x1f4 is not 0 - the id the player placement 0x5d40c0 uses) in yellow with
`AKTIV`. In the DLC 2 dump: 5 `checkpoint` instances, game data id 9400 = one of them.

**Object names (`dbg.names`).** The object name of every instance from the **live PC object list** `[0xdb94d0]` (via
`[[inst+0x10]+0x14]`, the `ObjectName` / `LabelKind` path - never a name table from the Xbox data), with the intro id
(`[Debug] NameIds`), nearest to the camera first, at most `NameMax` within `NameRadius`; filter `NameMatch` / item
`dbg.namefilter <parts|*>` (ring presets: all, thralls, triggers); font size `NameScale` / `dbg.namesize 0.5 .. 3`;
colour `NameColour` / `dbg.namecolour white|yellow|cyan|magenta|RRGGBB` (menu: colour picker). The 0.13 Thrall-Labels
(`dbg.labels`) stay as they were.

**Legend (`dbg.legend`)**: top right, every layer that is on with its colour and `drawn / found`.

**Master (`dbg.view`)**: on = every 0.14 layer whose checks passed + `dbg.labels` + `draw.markup` + the NavPower
switches of `[Debug] ViewNav` (default `planner_areas,planner_connectivity,obstacles`; these need a loaded level and
`[Cheat] Experimental=1` like `nav.draw`); off = all of them off (`nav.off`). Afterwards every switch works alone; the
value of `dbg.view` is 1 while any of them is on.

### Items, keys, menu, ring

| Item | Type | Meaning |
|---|---|---|
| `dbg.view [0\|1]` | bool | master switch (above) |
| `dbg.triggers [0\|1]` | bool | every trigger kind |
| `dbg.show <layer> [0\|1]` | action | one layer: `death fire checkpoint water sound volume plane unknown` (trigger kinds), `portals checkpoints trglabels legend names` |
| `dbg.portals` / `dbg.checkpoints` / `dbg.legend` / `dbg.names` | bool | the same layers as items of their own (ring on / off) |
| `dbg.namefilter <parts\|*>`, `dbg.namecolour <preset\|RRGGBB>`, `dbg.namesize <f>` | action | object name settings |
| `dbg.status` | info | checks, layers on, what the last frame drew |

`[Debug]` keys (all 0 / off by default): `View`, `ViewNav`, `Triggers`, `TrgDeath`, `TrgFire`, `TrgCheckpoint`,
`TrgWater`, `TrgSound`, `TrgVolume`, `TrgPlane`, `TrgUnknown`, `Portals`, `Checkpoints`, `TrgLabels`, `Legend`,
`Markup`, `TriggerMax` (64, 1 .. 256), `TriggerRadius` (20000, 500 .. 200000), `TriggerLabelMax` (16, 0 .. 64), `Names`,
`NameMatch` (empty = all), `NameRadius` (5000), `NameMax` (24, 1 .. 64), `NameScale` (1.0, 0.5 .. 3), `NameColour`
(FFFFFF), `NameIds` (1), `Persist` (0; 1 = every switch of the debug view - layers, Labels, Markup, NavDraw, name
settings - is written back into `TruMenu.ini` at once; `Set-TruMenu.ps1` then treats the file as owner-edited and keeps
it on updates).

Menu page **"Debug view / Debug-Ansicht (0.12 - 0.14)"**: master checkbox; groups Level data / Leveldaten (triggers
all, loading areas, checkpoints, the eight kinds with colour swatch and drawn / found, trigger names, sliders), AI / KI
(the seven NavPower switches, every layer, Thrall-Labels), Object names / Objektnamen (switch, filter text + presets,
radius, max, font size, colour picker + presets, intro id), Lara (markup, ledges), Display / Anzeige (legend, Persist
note). Ring **`Spieler/Debug`**: `Alles an / aus` (dbg.view), folders `Leveldaten` (12 entries, 2 pages), `KI` (the
0.12 NavPower entries + Thrall-Labels, 10 entries, 2 pages - moved from `Spieler/Debug`), `Namen` (11, 2 pages),
`Lara` (markup), then `Legende`, `Debug: Stand` (dbg.status), `Navmesh: Stand` (nav.status). Every switch shows on / off.

**Byte checks** (`DebugViewCheck` at load; pinned in `work\asi\menu014\precheck_014.txt`, `tools/pe_bytes_check.py` on
the Steam exe: 68 / 68 ok; `tools/trumenu_precheck_match.py --from "---- 0.14 Debug view" --to "---- favourites"`: 68 =
68): trigger lists, loop and adders (0x5cd527 .. 0x5c89f1), the enabled / player bits (0x4a4360, 0x4a4450), the volume
test (test point lift, data chain, shape, extents, radius, branches, 0x4355d0), the box test (0x46b75f .. 0x46b7c6,
0x49cdce, 0x49cdea, 0x49c987), the Euler matrix (0x49d50b .. 0x49d63f, constants 0.0 / 1.0, fcos / fsin, the three
axis rotations), the quaternion (0x49d720), the plane test (0x5ccc40 .. 0x5ccf55, 0x435259, 0x49ba20 / 0x49ba4b), the
portal walk (0x5d295f, 0x5d2a48, 0x5d2ab5, 0x5d2aca), the checkpoint game data reader (0x5d41df, 0x5d4214) and names
(0x85512c, 0x855118); plus the 0.13 projection checks and the 0.3 instance / player / main-state checks. A failed group
disables its layers with the reason (`dbg.status`, greyed ring entries).

### `TruMenu.log` lines

```text
0.14 debug view: triggers <ok|why>, portals <ok|why>, checkpoints <ok|why>, object names <ok|why>; [Debug] View <0|1>, Triggers <0|1>, <n> layer(s) on now, Markup <0|1>, ViewNav '<list>', TriggerMax <n>, ...
dbg.show <layer> <0|1> (src=<ring|menu|TruLink>)      dbg.triggers <0|1> (all 8 kinds, src=...)
dbg.view <0|1>: <n> layer(s), labels: <answer>, markup: <answer>, nav: <switch on|refused, ...> (src=...)
0.14 debug view drawn: triggers <n> drawn (box b, sphere s, plane p) of <m> listed, <k> off-screen, ...; portals ...; checkpoints ...; names ...
```

The `drawn` line is written once with the first frame after a switch (no per-frame logging).

**TO TEST (0.14)** - `[Debug] Enabled=1`, a loaded level (e.g. Croft Manor `l3_*` via the level select):

1. `TruMenu.log`: `0.14 debug view: triggers ok, portals ok, checkpoints ok, object names ok`.
2. Ring -> Spieler -> Debug -> `Legende`, then Leveldaten -> `Trigger alle`, `Ladebereiche`, `Checkpoints`: boxes /
   quads where doors, rooms and corridors are; the white cross 200 above Lara; walking into a box triggers what it
   should (the box is where the game tests).
3. `cheat.flight 1`, RT up, look down; `Alles an / aus`: everything stays drawn from above, the nearest first.
4. Namen -> `Objektnamen`, `Filter: alle`, `Farbe gelb`, `Schrift 1.5x`.

Fixed in 0.15: in 0.14 the Present hook returned before the ImGui frame unless the menu / ring was open or labels /
markup were on, so a 0.14 layer disappeared as soon as the ring closed (`DvAnyOn()` is now part of that test).

## TruMenu 0.15 "Render mode" (render census, flat view, collision overlay; debug render stages R0 / R1 / R2)

Built into `work\asi\menu015`; compiled, offline checks only - **not yet seen in the game**. Owner notes:
`<workspace>\docs\Befund-TruMenu-Rendermodus-0611.md` (research: `docs\Befund-Debug-Rendermodus-0611.md`). Off unless
`[Debug] Enabled=1` plus a switch. The renderer is Crystal's cdc PC renderer (RTTI): `cdc::PCTerrainDrawable` (vtable
0x849944) and `cdc::PCModelDrawable` (0x849754) have `Draw` in slot 1 (0x510dd0 / 0x50f4a0, thiscall `(pass,
previous drawable)`, `ret 8`), called by the draw list 0x4f6080 for the pass ids 1, 2, 0x80, 0x100, 0x200, 0x400, 0x800
(`PCScene::Draw` 0x5150e0 hands its lists over in the order 0x200, 0x100, 0x80, 0x800, 0x80). The device is created
PURE (0x522687: behaviour flags 0x50), so TruMenu asks the device for no state: the game's state manager
`[[0xad75e4]+0x284]` (device at +0xc) keeps the pixel shader it set at +0x20 (0x526630; the `IDirect3DPixelShader9` at
PCPixelShader +0xc) and every render state at `+0x168 + 4 * state` (0x502b70).

**R0 census (`dbg.census [frames]`).** For N frames (`[Debug] CensusFrames`, 120) TruMenu counts per pass id and class
(terrain / model) the drawable calls and their device draws, render target 0 (pointer, size, format; up to 3 per pass),
RT1 bound, and from the state manager's cache Z, Z write, alpha test, alpha blend and colour write 0 per draw, the
material pass `[0x8a2340]`, plus the `PCScene::Draw` calls per frame (render target at entry) and the device draws
outside a drawable. Then **one block** of `0.15 census` lines in `TruMenu.log`, a verdict per pass (colour candidate /
no colour writes / other target size / blended) and the suggested pass mask (passes drawn into a target of the back
buffer's size with colour writes and mostly without blending). `dbg.flatpasses census` takes it over.

**R1 flat view (`dbg.flat`).** Inside the terrain (and with `dbg.flatmodels` the model) `Draw` of a pass in
`[Debug] FlatPasses` (default 0x200, the first opaque list - a guess until the census), every device
`DrawIndexedPrimitive` / `DrawPrimitive` draws with one of 16 palette pixel shaders, then the game's own pixel shader is
set again at once (state manager +0x20), so the state manager's cache and the device stay equal. Colour = hash of the
current material `[0xa14188]` (`dbg.flatcolour material`) or terrain one colour / models another (`class`). The palette
shaders are built from tokens at run time (`def c0, r, g, b, 1` + `mov oC0, c0`, no constant register written) as
ps_2_0 and ps_3_0; the version of the game's shader of that draw picks the set (a vs_3_0 needs a ps_3_0 and the other
way round; `GetFunction` once per game shader). `tools/trumenu_flat_ps_check.py` disassembles all 34 with the Windows
`d3dcompiler_47.dll` and compares the HLSL compiler's own ps_2_0 / ps_3_0 output (same tokens without its comment
block). Edge pass (`dbg.flatedges`): the same draw again in wireframe with a dark shader, depth bias -0.00005 / slope
-1, Z write off; fill mode, depth bias and Z write come back from the state manager's cache. By default only into a
render target of the back buffer's size (`dbg.flatanyrt` / `[Debug] FlatAnyTarget=1` = every target), so shadow maps
and reflections keep the game's shading even with a wrong pass mask. Water, effects, HUD are other classes - unchanged;
fog / DOF still tint the result. **Not part of `dbg.view`** (a big separate switch; the master covers the overlays).

**Writes into game memory (R0 / R1 only, TruGuard).** Only while the census runs or the flat view is on, in a loaded
level (player instance, main state 1, no level change pending): `.rdata` words **0x849948** (PCTerrainDrawable::Draw,
game value 0x510dd0) and **0x849758** (PCModelDrawable::Draw, 0x50f4a0), during a census also **0x849a2c**
(PCScene::Draw, 0x5150e0). A word is written only while it holds the game's value (else refused with a log line),
`WriteDword` = VirtualProtect + interlocked store + VirtualProtect back; it is put back (only while it still holds
TruMenu's hook) when switched off, when the level is left or a level change starts, when the census ends and at unload.
The same for the game device's vtable slots 81 / 82 (`DrawPrimitive` / `DrawIndexedPrimitive`, memory of d3d9.dll or of
a proxy such as TRAWindowed, not of tru.exe). Everything is patched / unpatched in the Present hook, between two frames.
The palette shaders are created on the game's device in the Present hook and released in the Reset hook (created again
at the next Present).

**R2 collision overlay (`dbg.slide`, `dbg.enemycoll`; layers `slide` / `enemycoll` of the 0.14 table, part of
`dbg.view`).** Read-only. The collision meshes of every loaded stream unit: table 0xdbab40 (state 2) +8 Level,
`[Level]` Terrain, +8 group count, +0xc TerrainGroups (0x50 bytes), group +0x38 mesh - taken only when mesh +0x3c points
back to the group (0x48d2d4 reads it that way); faces 20 bytes at mesh +0x34 (count +0x44), vertices at +0x30 (mesh +0x54
word 0: 3 x s16 converted without a scale, else 16-byte floats - 0x460770 / 0x460690 / 0x460824), world = vertex + mesh
+0x20 (the mesh query 0x78d040 subtracts it). Read once per change of the loaded units into a static buffer (24576
triangles, no allocation), drawn as translucent triangles with edges through the 0.14 projection (near plane clipped),
the nearest to the camera first (`[Debug] CollRadius` 8000, `CollMax` 3000), **on top** (no depth test - visible
through walls). Slide = clientFlags (face +0x0e) & 0x04 (0x5d3af0 / ground probe 0x5dd356): **red** when steeper than
the tuning angle s16 `[[0xfad764]+0x100e]` degrees (0x5dd3ba: the game slides only then), **orange** when flatter.
Enemy-only = TerrainGroup extra flags (`[group +0x30]` +0) & 0x800, **violet**: the name is TRLAU's; in tru.exe the
collision filter 0x48d2d0 (collide kinds 7 and 4, registered at 0x4964eb / 0x4964ff) skips such groups and the filter
0x48d280 of kind 3 does not - which kind is the player's is not proven. A `0.15 collision: read ...` line per reading.

### Items, keys, menu, ring

| Item | Type | Meaning |
|---|---|---|
| `dbg.census [frames]` | action | R0: one census of N frames (10 .. 1200), result in `TruMenu.log` |
| `dbg.flat [0\|1]` | bool | R1 flat view |
| `dbg.flatpass <0x200\|0x100\|0x80\|0x400\|0x800\|1\|2> [0\|1]` | action | one pass id in / out of the mask (live) |
| `dbg.flatpasses <mask>\|census\|default` | action | the whole mask (`census` = the last census' suggestion) |
| `dbg.flatcolour material\|class` | action | colour per material, or terrain / models |
| `dbg.flatmodels`, `dbg.flatedges`, `dbg.flatanyrt` | bool | models flat too, edge pass, every render target |
| `dbg.render` | info | checks, patched slots, last frame (flat draws, skipped), census state / suggestion |
| `dbg.slide`, `dbg.enemycoll` (also `dbg.show slide` / `enemycoll`) | bool | R2 overlay layers |

`[Debug]` keys (0 / off by default): `Slide`, `EnemyColl`, `CollRadius` (8000, 500 .. 200000), `CollMax` (3000, 100 ..
20000), `Census` (1 = one census in the first loaded level), `CensusFrames` (120, 10 .. 1200), `Flat`, `FlatPasses`
(0x200), `FlatColour` (material / class), `FlatModels`, `FlatEdges`, `FlatAnyTarget`. With `Persist=1` the switches are
written back as the 0.14 ones.

Menu page "Debug view": new group **Render (0.15)** at the top (flat view, census button + state, one checkbox per pass
id, census suggestion / default buttons, colour mode, models, edges, every target, state line); `slide faces` in Level
data (after checkpoint objects) with the sliders CollRadius / CollMax, `enemy-only collision` in AI / KI. Ring
`Spieler/Debug`: `Render` as the second entry (page 1: Flach-Ansicht, Render-Zaehlung, Kanten, Figuren einfaerben,
Farbe: Material, Farbe: Terrain / Figuren, Jedes Ziel (auch Schatten), Render: Stand; page 2: Pass 0x200 .. Pass 2,
Passe aus Zaehlung), `Rutschflaechen` in Leveldaten (4th), `Gegner-Kollision` in KI (5th); `Navmesh: Stand` moved to
page 2 of `Spieler/Debug`.

**Byte checks** (`RenderModeCheck` at load; `work\asi\menu015\precheck_015.txt`, 46 / 46 ok on the Steam exe;
`tools/trumenu_precheck_match.py --from "---- 0.15 Render mode" --to "---- favourites"`: 46 = 46): R0 / R1 (27) - the
three vtable words, the constructors' stores, the draw list call, the Draw heads / tails, the terrain pass dispatch, the
device draw sites (vtable +0x148), the scene's list dispatch, the state manager getter / SetPixelShader / SetRenderState
wrappers, the material pointer / pass globals; R2 (19) - face clientFlags reader, ground probe masks, tuning angle
reader and pi / 180, mesh query / vertex fetch (both vertex formats), the collision filters and their registration. A
failed group disables its part with the reason (`dbg.render`, greyed ring entries).

### `TruMenu.log` lines

```text
0.15 render mode: census / flat view <ok|why>, collision overlay <ok|why>; [Debug] Flat <0|1> (passes ..., colour ..., models, edges, any target), Census .., Slide .., EnemyColl .., CollRadius .., CollMax ..
dbg.flat <0|1> (passes 0x200, colour material, models 0, edges 0, any target 0; src=...)   dbg.flatpass 0x100 1 (mask now 0x300; src=...)
0.15 flat view: 34 palette pixel shaders created (17 ps_2_0 + 17 ps_3_0) on device 0x........
0.15 render mode patched (flat view): +PCTerrainDrawable::Draw 0x00849948 (0x00510dd0 -> TruMenu), +PCModelDrawable::Draw ..., +device DrawIndexedPrimitive (82) ..., +device DrawPrimitive (81) ...
0.15 render mode unpatched (<why: not while loading / flat view off / census done>): -PCTerrainDrawable::Draw 0x00849948, ...
0.15 flat view drawn: flat 1 (passes ...), slots 0x1b; last frame: <n> drawable calls, <n> flat (terrain .., model ..), <n> without game shader / version, <n> other pass, <n> other target
0.15 census started: 120 frames, back buffer 1920x1080
0.15 census (done): 120 frame(s), back buffer ...; PCScene::Draw <f> per frame (render target 0 at entry: ...); device draws outside a drawable ...
0.15 census pass 0x200: terrain .. calls / .. DIP .. DP, model ..; per draw Z ..%, Z write ..%, alpha test ..%, blend ..%, colour write 0 ..%, RT1 bound ..%; [0x8a2340] ... -> colour candidate
0.15 census pass 0x200: render target 0 0x........ 1920x1080 fmt 21 (n), ...
0.15 census: suggested [Debug] FlatPasses=0x... (...) - 'dbg.flatpasses census' sets it; now 0x200
0.15 collision: read <n> unit(s), <n> mesh(es) (...), <n> faces: <n> slide (clientFlags 0x04), <n> in <n> enemy-only group(s) ...
```

No line per frame: the `drawn` line once after a switch, patch / unpatch lines only when the slots change (switch,
level change), the census block once, the collision line once per reading of the loaded units.

## TruMenu 0.16 "Readability" (debug view after the first live run, 2026-11-06)

Owner feedback from the first live run of 0.15 in the Croft Manor prologue: it works, but it is hard to read (lines
over Lara and through walls, labels on top of each other, legend cut off, huge enclosing volumes, the active checkpoint
marker filling the foreground, 15 triggers silently missing at TriggerMax 64). Workspace report
`docs\Befund-TruMenu-Lesbarkeit-0611.md`; byte checks `work\asi\menu016\precheck_016.txt` (17, section
"---- 0.16 depth" of `TruMenu.cpp`); offline math `tools/trumenu_readability_check.py`.

* **Depth** (`dbg.depth off|on|dim`, `[Debug] Depth` 0 / 1 / 2, default 0): with 1 / 2 the lines and faces of every
  debug view layer are not drawn by ImGui at Present but kept in a world-space buffer and drawn by TruMenu inside the
  next frame, right after `PCScene::Draw` returned (vtable word 0x849a2c - the 0.15 census slot, patched while Depth is
  on and a layer is on), into the render target / depth surface the scene left bound: pre-transformed vertices, x / y
  from the 0.14 projection, z from the scene's own projection `[scene+0x100]` applied to the depth (after checking that
  the scene's view `[scene+0x140]` gives the same depth as the 0.14 camera), Z test on, Z write off. `dim` draws the
  hidden parts first at `DepthDim` % with the inverse test. Only a scene without its own target object
  (`[scene+0x1c0]` = 0), render target 0 of the back buffer's size and a depth surface; `DepthCall` picks the n-th such
  scene of a frame. Device state through a `D3DSBT_ALL` state block (captured before, applied after - as ImGui's DX9
  backend), own dynamic vertex buffer (released in the Reset hook). If anything does not fit, that frame draws as
  Depth 0 (lines on top) and `dbg.style` / the legend say why. Labels and the legend stay on top (ImGui).
* **Style**: `[Debug] LineAlpha` (60 %, `dbg.alpha`), `LineBright` (100 %, `dbg.bright`), distance fade `Fade` /
  `FadeStart` 2000 / `FadeEnd` 10000 / `FadeMin` 20 % (`dbg.fade`), faint faces `Fill` / `FillAlpha` 10 % (`dbg.fill`,
  default off) - for every 0.14 / 0.15 overlay (triggers, loading areas, checkpoints, collision faces).
* **Labels**: trigger, loading-area and checkpoint labels are candidates drawn at the end of the frame, nearest first,
  at most `ViewLabelMax` (10), each nudged up / down or skipped when it overlaps one already drawn or the legend;
  coincident triggers (same kind, centres within 25 units) get one label `TV x3 (4535..4537)`, both directions of one
  loading area `a <-> b`. `LabelShort` (`dbg.short`, 1): `TV 4463`, `TP 4129`, `FIRE 4492`, `-> main_bedroom`; the nearest
  label and the one nearest to the screen centre keep the full text. Every label (also `dbg.names`) shows the distance
  to Lara and the height difference in game units (`6100u v1500u`) and the owner unit when it is not Lara's
  (`[mansion_exterior_afterburn]`, from the loaded unit whose intro array holds the instance's intro). Dark background
  box, text in the kind's colour, anchored at the top centre.
* **Lara in** (`dbg.larain`, `[Debug] LaraIn` 1): the point the engine tests (Lara +0x20 + 200 up) against every listed
  trigger with the engine's math; the containing ones bold with a pulsing white outline, the legend line
  `Lara in: triggervolume 4537` (3 names, then +N; "(aus)" / "(nicht Spieler)" when the engine would skip the entry).
  Planes: "near" within 50 units (the engine tests a crossing). The engine keeps no inside flag of its own (0x5cd1b0
  returns 0 / 1 / 2 / 3 = out / inside / enter / exit from the old and the new position every frame).
* **Clutter**: boxes around the camera, or big ones (`EnclosingSize` 1500) around Lara, dim + dashed
  (`dbg.enclosing normal|dim|hide`, `[Debug] Enclosing` 1); `ViewSkip` (default `sound`) = layers `dbg.view` / `View=1`
  leave off; checkpoint markers at most `MarkerMax` (8 %) of the screen height; `TriggerMax` 256 (was 64, 1 .. 512).
* **Legend**: fully inside the screen, right-aligned, as wide as its text, counts (drawn / found) in their own column,
  colour squares at the right edge; extra rows `GEKAPPT / capped` (warning colour) when TriggerMax cuts, `Lara in`,
  enclosing count, depth state.
* **Ring**: `Spieler/Debug` page 1 Alles an / aus, **Fliegen** (`cheat.flight`), **Darstellung**, Render, Leveldaten, KI,
  Namen, Lara; page 2 Legende, Debug: Stand, Navmesh: Stand, Flug-Tempo 10 / 20 / 40 (`cheat.speed`).
  `Spieler/Debug/Darstellung` (17 entries, 3 pages): Tiefe an / gedimmt / aus, Deckkraft 100 / 60 / 35, Ferne blasser,
  Flaechen fuellen | Kurze Namen, Lara drin markieren, Heller / normal / Dunkler, Umhuellende blass / aus / normal |
  Darstellung: Stand. Menu page "Debug view": new first group "Display / Darstellung (0.16)" (legend and Persist note
  moved there).
* **Script prints into TruMenu.log** (`log.scriptfile`, `[Log] ScriptToFile`, default 0; checkbox on the Log page): with
  `log.script` on, every script line also as `script: <text>` in `TruMenu.log` - at most `[Log] MaxLinesPerSecond` per
  second (the rest counted: `script: <n> line(s) dropped`), a line repeated at once is counted (`script: (last line x N
  more)`, at the latest every 10 s) instead of written again. Note: the log page tails `TruMenu.log` too, so such a line
  shows there once as `script` and once as `TruMenu`.

Writes into game memory added by 0.16: the vtable word 0x00849a2c (`PCScene::Draw`, 0x005150e0 -> TruMenu) now also
while Depth is 1 / 2, a debug view layer is on and a level is loaded (same rules, same log lines as the 0.15 census:
written only while it holds the game's function, put back at off / level change / unload). Device calls inside the
frame (render thread, after the game's scene Draw): CreateStateBlock / Capture / Apply, SetViewport, SetFVF,
SetStreamSource, Set(Vertex|Pixel)Shader(NULL), SetTexture(0, NULL), 30 SetRenderState, 7 SetTextureStageState,
DrawPrimitive, GetRenderTarget / GetDepthStencilSurface; CreateVertexBuffer once per device.

```text
0.16 readability: depth <ok|why>, Lara in <ok|why>, owner units <ok|why>; [Debug] Depth off (DepthDim 25, DepthCall 0), LineAlpha 60, ...
dbg.depth on (DepthDim 25, DepthCall 0; src=ring)
0.15 render mode patched (depth lines (0.16)): +PCScene::Draw 0x00849a2c (0x005150e0 -> TruMenu)
0.16 depth: vertex buffer created on device 0x........ (6144 vertices, dynamic, default pool)
0.16 depth drawn: an (scene 0 of 1 qualifying, 3 calls; row vectors, z LESSEQUAL, z(16.5) 0.0000; 812 lines, 0 faces)
0.16 depth waits (180 frames): wartet, Linien oben / waits, lines on top: <why> (.. scene calls, .. qualifying)
```

## TruMenu 0.17 "Schnellschalter" (quick-toggle bar, cutscene shots, depth diagnosis, checkpoints, positions; 2026-11-06)

A third control next to the long menu and the ring, for switching the debug view while playing, plus the live findings
of 0.16. Workspace report `docs\Befund-TruMenu-Schnellschalter-0611.md`; byte checks `work\asi\menu017\precheck_017.txt`
(6, section "// ---- 0.17 quick toggles ----" .. "// ---- 0.3 pages ----"); offline models `tools/trumenu_quick_check.py`.

* **Schnellschalter** (`quick.open`, `[Quick]`): a small panel at the LEFT screen edge (`Top` % of the height), the game
  keeps running - no freeze, no neutral pad. **View + Start** (`OpenButtons` 0x0030) opens / closes it; D-pad up / down
  = row, left / right = off / on (value rows: one step down / up), LB / RB = page; a held direction repeats after 400 ms.
  While it is open only D-pad, LB and RB are kept from the game (masked in the state PadHook hands the game; one held at
  the close stays away until released). The combo itself never reaches the game: a lone View / Start is held back for
  `ChordMs` (250); released inside that window the game gets it as a 100 ms tap at once, held longer it gets it late.
  Why View + Start: every pad button is bound in the PC input map (generalbank DTP 47, `tools/input_map_find.py`):
  D-pad and LB / RB are gameplay, L3 + R3 is TruMenu's own menu / ring combo; View and Start are menu buttons (pause /
  PDA, actions 9 / 10 / 71 / 89 in set 0) and no binding uses both together.
* Pages (the menu / ring group order): **Debug** (Alles an / aus, Legende, Fliegen, Flug-Tempo, Zwischensequenz-Fotos,
  Sprache), **Darstellung** (Tiefe, Deckkraft, Helligkeit, Ferne blasser, Flaechen fuellen, Kurze Namen, Lara drin,
  Umhuellende), **Render** (Flach-Ansicht, Pass, Zaehlung, Rutschflaechen, Gegner-Kollision), **Leveldaten** (Alle
  Trigger, Tod, Feuer, Checkpoint-Trigger, Wasser, Ton, Trigger, Ebenen, Unbekannt, Ladebereiche, Checkpoints,
  Trigger-Namen - the start page), **KI / Namen / Lara** (Thrall-Labels, Objektnamen, Markup, Nur Kanten) and
  **Checkpoints** (the nearest 14, marker off / on). Rows in their layer colour with the count drawn in the last frame;
  greyed rows say why. Every row runs the existing item (`dbg.show`, `dbg.depth`, `dbg.alpha`, `cheat.flight`, ...)
  through the ring's path and reads its state the ring's way - no state of its own. One `quick: <page> / <row> ->
  <item> <arg>: <answer>` line per action. Closed: one line `Debug: N an` (`ShowClosed`, with `[Debug] Enabled=1`, in a
  level). `quick.lang de|en` / `[Quick] Language` (TruMenu has no global language switch).
* **shot.oncine** (`[Shot] OnCine*`, ring Spieler / Debug): when a cutscene starts in a level - the game's cinematic
  test 0x453f00 or the camera leaving the gameplay camera `[0xe804f0+0xb80]` (`OnCineSignal` both) - pairs of shots, a
  clean one and a ui one of the same Present (`cine<NN>_<i>_clean / _ui`): the first `OnCineFastPairs` (4) every
  `OnCineIntervalMs` (1500), then every `OnCineSlowMs` (5000), at most `OnCinePairs` (10). The cutscene ends when the
  signal has been gone for 2 s (camera flips inside a cutscene keep one burst); pairs have their own MaxPerMinute window.
* **Depth diagnosis** (live: `[scene+0x140]` never mapped): `dbg.depthdump` writes one block per PCScene::Draw call of
  the next frame (scene +0xe0 .. +0x1fc, the 0.14 camera, 0xa038f0, five test points against six view forms);
  `DpMapping` now tries six view forms (row / column, camera-relative, of the inverse) with a least-squares scale over
  five test points, |k| = 1 first, and needs the projection to span half the depth range; `[Debug] DepthCall` -1 (new
  default) = the first qualifying scene that maps.
* Ring entries that set a value show the current one ("= an (wartet)", "jetzt 60%"), switches show an / aus.
* Legend in short English terms (`Death`, `Fire`, `Checkpoint trg`, ..., `CAPPED`, `Lara in: ...`, `Depth: on (waits)`);
  labels whose anchor lies outside the screen are skipped (they were pinned to the screen edges).
* **Checkpoint list** (`dbg.cp <id> 0|1`, `dbg.cpall 0|1`, `dbg.cplist`, `dbg.cpgo <id>|active`, `[Debug]
  CheckpointHide`): menu page Debug view, the bar's page Checkpoints, ring Leveldaten.
* **Positions** (`pos.save [name]`, `pos.list`, `pos.go <name>|last`, `TruMenu.positions.txt` next to tru.exe): unit,
  live position, yaw, the unit's shift P and origin V; `pos.go` only while that unit is loaded, converted with its shift
  then and now (live = data - V + P), otherwise refused with the reason.

```text
0.17 quick toggles: [Quick] Enabled 1, OpenButtons 0x0030 (Start + View), ChordMs 250, ... cutscene shots: camera checks ok, cinematic test ok, ...
0.17 checkpoint list: 0 marker(s) hidden ([Debug] CheckpointHide); positions: ok, file <game>\TruMenu.positions.txt
quick: opened (pad 0: Start + View)
quick: Leveldaten / Tod -> dbg.show death 1: ok dbg.show death 1
shot.oncine: cutscene 01 start - camera left [manager+0xb80]; camera 0x00e80de0 (other, vtable ...); main state 1; ...
shot.oncine: cutscene 01 end (gameplay camera back 2 s) - 7 pair(s) taken, 0 refused; 21.4 s
0.17 depthdump frame 1234 call 0: scene 0x........ - qualifying; [scene+0x1c0] 0x00000000; target 1920x1080 (...)
```

## TruMenu 0.18 (Lara in overlay, owner units, cutscene segments, bar pages, save.load; 2026-11-06)

Lukas' live wishes after 0.17 plus the found bugs. Workspace report `docs\Befund-TruMenu-018-0611.md`; byte checks
`work\asi\menu018\precheck_018.txt` (33, section "// ---- 0.18 save.load" .. the next "// ======" line); static load-path
research `logs\r18_load_*.txt` (workspace).

* **Lara in** (`overlay.larain`, `[Menu] OverlayLaraIn` 1): the position overlay (top left) has a second line
  `Lara in: triggervolume 4537, ...` - up to 3 names (most dangerous kind first) and `+N`, each in its kind's colour
  (death red, fire orange, checkpoint green, water blue, sound violet, trigger yellow, plane cyan, unknown grey). It is
  computed every 100 ms from both trigger lists with the 0.16 test (player +0x20 + (0, 0, 200); box / sphere inside,
  plane within 50 units), whether a trigger layer is drawn or not. The legend's row is gone (`[Debug] LegendLaraIn` 1
  brings it back); the pulsing outline of `dbg.larain` stays.
* **Owner units**: stream table names come in two spellings (`L3_main_bedroom` from the new-game start data,
  `l3_main_hall` from a portal) - the label prefix cut is case-insensitive now, Lara's stream entry is found in the
  whole table (0.16 stopped after 16 units), GameTracker+0x38 is the fallback when no loaded entry has Lara's id; one
  `0.18 units:` log line when the two names differ.
* **shot.oncine segments** (`[Shot] OnCineSegments` 1): inside a running cutscene a new segment with its own pair budget
  starts when GameTracker+0x38 changes, the cinematic object `[0xe7f1c0]` / its track +0x2c changes, or a script prints
  `StartCinematic called` / `Cine about to play` (with `log.script`); at least 1 s per segment. `OnCineSlowMs` 8000 (was
  5000): 4 pairs every 1.5 s, then every 8 s up to 10 per segment (~54 s). Names `cine<NN>_<i>` / `cine<NN>s<k>_<i>`;
  log lines per segment and one summary per cutscene.
* **Quick-toggle bar: 10 pages** - Notfall / Cheats, Lara (+ the saved positions), Debug / Darstellung, Leveldaten
  (start page), Render / KI, Zeit / Test, Checkpoints, Saves, Kapitel (debug), Barrierefreiheit. New row kinds: info
  (right = the item's value in the footer), choice (left = next choice, right = run: weapons, Claude marks), heading,
  planned (greyed, right = what it will do). Dangerous rows need a second right press within 3 s (die, unit reload,
  chapter loads, checkpoint go, "load + go" of a position); restore / load keep the 0.9 double confirmation (10 s).
  Long pages scroll with the selection.
* **save.load** `<save>|autosave` (`[Saves] DirectLoad` 1; menu Saves page "Load" + CONFIRM, bar page Saves, never over
  TruLink, never in the ring): the game's own load path - `0x788a50()`, `0x789de0(index)`, step index `[0xfaf7a4]` = 2
  (TruMenu's confirmation replaces the game's yes / no box); the game then reads the file, runs `SAVE_RestoreGame` and
  changes the level. Only in a level (main state 1, no level change pending), with the save system idle and the name in
  the game's own list (index by name; Autosave = 0x38). Runs on the game thread; while it runs `LevelChangePending`
  says so. Not seen live yet.
* **pos.goload** `<name>|last`: level.load of the position's unit when it is not loaded, then `cheat.flight 1` and
  `pos.go` (the 0.8.1 shortcut runner waits for the level). Explicit only; a level.load may change story state.
* **Kapitel (debug)**: one bar row per chapter start the game's level select uses (`L1_seatop`, `L2_cliffclimb`,
  `L3_caverns_start`, `L4_trailstart`, `L5_startsnow`, `l6_ship_exterior`, `L7_thin_ice` - generalbank script (8, 119))
  plus the prologue `l3_main_bedroom` and the DLC starts; right twice = `save.backup kapitel`, then `level.load` - no
  story value is set.
* **Barrierefreiheit** (skeleton): menu page, ring level Spieler / Barrierefreiheit, bar page - the five categories of
  the game paper (Sehen / Hoeren / Verstehen / Steuerung / Sonstige); working assists only (Zeitlupe 0.5 / 0.75 / 1,
  Befreien, Befreien: Stand, Unverwundbar, Gott voll), everything else greyed "geplant".

```text
0.18 save.load: ok ([Saves] DirectLoad 1; 33 byte checks)
0.17 quick toggles: ... 10 pages (0.18), 82 item rows + 10 planned, 0 unknown item(s); ... segments 1)
shot.oncine: cutscene 01 segment 2 start - unit l3_main_hall -> l3_mansion_exterior_afterburn; unit ...; up to 10 pair(s)
save.load: 'Slot 2' (list index 1) loading - 0x789de0 = 1, step 2 set; Lara was in l3_main_hall
save.load: 'Slot 2' loaded - unit l4_trailstart (14.2 s)
```

## TruMenu 0.19 "Dumme KI" (enemies ignore Lara; 2026-11-06)

Workspace finding `docs\Befund-Gegner-Wahrnehmung-0611.md` (one brain class for every AI enemy, one perception list),
report `docs\Befund-TruMenu-019-DummeKI-0611.md`; byte checks `work\asi\menu019\precheck_019.txt` (33, section
"// ---- 0.19 dumb AI" .. the next "// ======" line).

* **`ai.dumb`** `off|all|sharks|spiders|thralls|filter [0|1]` or `list <name parts>` (`[AI] Dumb` 0 / 1 / 2,
  `[AI] DumbFilter`): every AI enemy, or those whose object name contains a part (sharks `shark`, spiders
  `spider,tarantula`, thralls `thrall`, filter = the INI list), ignore Lara. One setting at a time - switching a group
  on replaces the other; `<preset> 0` only switches off its own active setting; `""` / `1` bring the last one back.
  Not AI enemies (no effect): jellyfish, kraken, Natla, `natla_thrall` (DLC 2).
* **Method** (`ai.mode`, `[AI] DumbMode`): `purge` (default, stage A, no code patch) - once per game frame (PadHook,
  game thread) every enemy in scope gets each sense slot that holds Lara reset with the engine's own `0x65a140` (the
  function `EnemySense::DoProcess` calls when a target is gone). Lara can be sensed again by the scan of the same frame;
  whether that is enough is the first live question. `gate` (stage B) - only while `ai.dumb` is on in a loaded level:
  the rel32 of the calls `0x6648bb` / `0x659d8f` / `0x664a64` (AddToSenses) and `0x623e5f` (noise override) and the
  EnemySense vtable slot `0x85a2fc` lead through TruMenu, which passes everything except Lara for an enemy in scope;
  patched / put back on the game thread, all or nothing, only over the game's bytes; back when off, at a level change
  and at unload.
* **`ai.noinvestigate` / `ai.noattack`** (`[AI] NoInvestigate` / `NoAttack`): the prototype's flags rebuilt as brain+8
  bits - 0x80 (Investigate), 0x20 (Attack / ScriptAttack) + 0x100000 (Melee); set once per frame for the enemies in
  scope (the ai.dumb filter, else every AI enemy), only TruMenu's bits are cleared again. `ai.noattack` is partial
  (close / ranged combat states not checked).
* **Where**: ring Spieler / Debug / KI (8 entries) and Spieler / Barrierefreiheit (Haie / Spinnen ignorieren Lara),
  quick-toggle bar Render / KI (heading + 9 rows, count = enemies in scope), Notfall ("Gegner ignorieren Lara"),
  Barrierefreiheit (Sonstige: the planned row "Haie" is now "Haie ignorieren Lara", plus "Spinnen ignorieren Lara"),
  menu page "AI / KI: enemies ignore Lara (0.19)"; `ai.status` = setting, checks, enemies seen / in scope, last second.
* **Log**: one line per switch change, one per burst of removals / gate blocks (when it ends, every 30 s while it lasts),
  never per frame. Cheats page: the rebuild rows "no senses" / "don't attack" / "don't investigate" name their 0.19 item;
  "no barks" is unknown (0x616c20 is the EnemyProcess constructor, not ENEMY_UpdateBark).

```text
0.19 dumb AI: purge (stage A) ok (11 checks), gate (stage B) ok (15), brain flags ok (7); [AI] Dumb -> off, ...
ai.dumb sharks (src=ring): off -> filter 'shark'; purge (stage A): the engine's sense reset 0x65a140 once per frame
ai.dumb: burst ended after 4.0 s (4 active second(s)) - stage A purge 37 sense(s); gate 0 add(s) / 0 override(s) ...
ai.dumb gate (stage B) on (ai.dumb on): A1 scan 0x6648bb, A2 AddTarget 0x659d8f, ... -> TruMenu
```

## TruMenu 0.20 (collectibles, enemies, forget, goload over portals, mutes; 2026-11-06)

Report `docs\Befund-TruMenu-020-0611.md`; byte checks `work\asi\menu020\precheck_020.txt` (16, section
"// ---- 0.20 collectibles, enemies" .. "// ---- end of 0.20 collectibles"); analysis files `work\m020_0611`.

* **`dbg.collect`** (layer `collect`, `[Debug] Collect`): every instance whose object name holds `_rw_` (artifact gold,
  treasure pink, shard turquoise, other reward light gold) and every reward container (`_pt_` + `reward`:
  `dlc1_pt_reward_pot`, `*_pt_weightbreak_reward`) as a magenta ring with **"enthaelt Artefakt #<index>"** - the
  container's object type data names `tp_rw_artifact_spawned` (the same for every pot), the reward index is intro data
  +0x30 (`[[inst+0x100]+0x78]+0x30`). "Collected" is not shown (not verified cheaply).
* **`dbg.enemies`** (layer `enemies`, `[Debug] Enemies`): every AI enemy (the 0.19 brain test) coloured by kind -
  thrall, spider / tarantula, shark, tiger / panther, naga, bat, merc / poacher, other; label name, intro id, LP,
  distance; thralls with the 0.13 targeter 9 line. While on, `dbg.labels` leaves AI enemies to it. Both layers: the
  nearest `[Debug] MarkMax` within `MarkRadius`, legend rows per kind (found in the loaded units).
* **ai.dumb forget**: when ai.dumb comes on (and for an enemy entering scope while on) the enemy's current target
  (`EnemyTargeting` +0x30) and override (+0xf0) are cleared once with the engine's slot setter `0x653cf0` when they
  hold Lara, then her senses are purged. **`[AI] DumbMode=gate` is the default** (purge = fallback).
* **`shot.oncine`**: a track change of the same cinematic no longer starts a segment (unit change, another cinematic
  object or a StartCinematic print still do).
* **`pos.goload <name> [load]`**: a target unit that a loaded unit has a stream portal to is reached over that portal -
  `cheat.flight 1;pos.portal <unit>;wait.unit <unit>;pos.go <name>` (`wait.unit` = the runner waits until the unit is
  loaded 1 s in a row, at most 30 s); `level.load` only without such a portal or with `load`.
* **`media.mutemusic`** (`[Media] MuteMusic`): `SOUND_SetMusicVolume 0x589520(0)` whenever the music comes back
  (level loads re-apply the slider); off = the player's value `[0x8900d8]`. **`media.muteambient`**
  (`[Media] MuteAmbient`): `_amb_` srmusic tracks (DLC 2) stopped when they start; base-game ambience not covered.
* Defaults: `[Debug] Depth=2` (dim), `FlatPasses=0x600`. Bar: Leveldaten "Sammelgegenstaende", Render / KI "Gegner",
  "Gegner-Leben zeigen", "Kanten", Zeit / Test "Musik aus" / "Ambient aus", Notfall last row "Spiel beenden"
  (`game.quit`: right arms, right again within 10 s quits). Ring: Leveldaten, KI, Zeit.

## TruMenu 0.20.1 (sound list, music mute without the slider, enemy state on the labels; 2026-11-06)

Report `docs\Befund-TruMenu-0201-0611.md`; byte checks `work\asi\menu0201\precheck_0201.txt` (44, section
"// ---- 0.20.1 sound list" .. "// ---- end of 0.20.1 sound list"); analysis files `work\m0201_0611`.

* **FMOD Ex is linked into `tru.exe`**: the exe imports no `fmodex.dll` (the DLL next to it is not used by the exe);
  `tools/pe_fmod_api_map.py` lists the linked public wrappers (System 26, Channel 24, ChannelGroup 5, DSP / Sound 21)
  and their callers. `FMOD::System*` = `[0xcc9f80]`.
* **`snd.list`** (`[Sound] List`): an overlay, **bottom left** by default, header "Ton (n spielen)", one line per voice:
  group (MUSIK / SFX / SPRACHE / ?, plus the group number), wave id (`Welle 1234`; sounds carry no name in memory) or
  `Stream`, the channel volume the game set and the group volume, state (spielt / virtuell / pausiert / stumm /
  startet / endet; not audible = dimmed), distance to Lara for 3D voices; MUSIK lines add the srmusic tracks
  (`media.music.now`). Source: the game's voice pool `0x8a8108` - `VoicePool::Play 0x58bfc0` is the only caller of
  `System::playSound`, so every channel the game plays is in it. Built on the game thread every `RefreshMs` (also while
  paused): memory reads plus the game's read-only FMOD wrappers `Channel::isPlaying / getPaused / getVolume /
  isVirtual`. Groups: music = categories [0] (slider "Musik") and [3] (FMOD channel group "music"), SFX = [1], speech
  = [2] (the third option slider, speech / cutscenes).
* Settings `[Sound]` Position (bl / tl / tr / br), MaxLines 16, RefreshMs 1000, Sort (group / volume / name), FontScale,
  OnlyPlaying, ShowMusic / ShowSfx / ShowSpeech / ShowOther; items `snd.list / pos / lines / refresh / sort / scale /
  playing / music / sfx / speech / other / status`. Menu page Debug view, group "Sound list / Ton-Liste"; bar Debug /
  Darstellung (every switch; Ort / Zeilen / Sortierung as value rows) and Zeit / Test (Ton-Liste, ins Log); ring
  Spieler/Debug/Ton (on / off, dump, four corners, audible only, sort group / volume, status) and Zeit | Ton-Liste. The
  ring is now at TruMenu's 256-entry limit - the group filters stay on the bar and the menu page.
* **`snd.dump`** (game thread, once): every voice, unfiltered, with addresses / flags / position into `TruMenu.log`;
  `snd.list` on writes one burst line (FMOD system, voices, groups), never per frame.
* **`media.mutemusic`** now mutes the **FMOD channel groups** of the music groups (FMOD's own
  `ChannelGroupI::setMute 0x7c48cd`; no public wrapper is linked, the game never mutes a group) - no game volume and
  not the option slider is written; muted again after a level load (new groups); off unmutes only the groups TruMenu
  muted. Fallback when those checks fail: the 0.20 `SOUND_SetMusicVolume` path (logged at load).
* **Enemy state** (coordinator): the `dbg.enemies` label and the thrall line of `dbg.labels` show the behaviour state
  `(char *)[[brain+0x125c]+8]` (e.g. Vaulted, Land, Getup, RegenerateDeath, Regenerate); RegenerateDeath adds the rest
  until it stands up (`~n s` from the measured game clock rate; `(wacht)` when due). `[Debug] EnemyStateLog=1`: one log
  line per state change of a labelled enemy.

## TruMenu 0.21 (Arachnophobie stage 1, camera shake, label fixes, ai.remove, Koop placeholder; 2026-11-07)

Report `docs\Befund-TruMenu-021-0611.md`; plan `docs\Befund-Arachnophobie-Stufe1-Kamera-0611.md`; byte checks
`work\asi\menu021\precheck_021.txt` (65, section "// ---- 0.21 arachnophobia" .. "// ---- end of 0.21 arachnophobia");
analysis files `work\m021_0611` (`labels\`, `airemove\`).

* **Arachnophobie** (`[Arachno] Enabled`, item `arachno.on`, default off) - the master switch of three parts (each 1 by
  default, so switching the master on gives the whole mode):
  * **Model off** (`Hide`, `arachno.hide`): the `InstanceDrawable` vtable slot 7 (`.rdata` word `0x853ad8` = `0x5bba90`)
    leads through TruMenu while the mode is on in a level; for a spider the engine wants to draw, the draw-group mask
    `+0x23c` is `-1` **only during its draw call** (the engine's own "all groups hidden" exit) and the game's value comes
    back right after. Logic, collision, AI, hits and Lara's aim are untouched; the shadow goes with the model. If the
    draw runs on another thread than the game logic (logged once: `arachno: spider draw calls run on thread ...`), V2
    skips the call instead of writing the mask.
  * **Picture** (`Picture`, `arachno.picture`): a wobbling picture (bob / squash / tilt, `WobbleAmp / WobbleHz /
    SquashAmp / TiltDeg`) at the spider's projected bones, size relative to them (`Scale`, `MinPx`, `MaxScreen`), faded
    closer than `FadeNear`, none beyond `MaxDist` or at LP 0, mirrored while it moves left (`Flip`). Drawn over the game
    and its HUD (walls do not hide it yet - the depth path is 0.22).
  * **Sounds off** (`Mute`, `arachno.mute`): spider sounds are not started - 6 call gates (anim sound `0x5b99c0`, random
    set `0x5b2820`) + the sound-slot jump table word `0x5b6b1c`; TruTrace's checked call bytes `0x5b6a2f` stay.
  * Spiders = object names with a part of `Match` (`spider,tarantula`) and none of `Exclude` (`_generator`).
    `arachno.list` writes every spider (drawable class, flags, masks, bones, children, LP, draw thread) into the log;
    `arachno.status` shows the state.
  * **The picture file**: `TruMenu.arachno.png` next to `tru.exe` (`[Arachno] Image`, PNG with alpha, read with
    stb_image - `src\asi\third_party\stb`, public domain / MIT, no new DLL import). **The owner's own image is local
    only**: it is not in the repository (`.gitignore` `TruMenu.arachno*.png`, `work/arachno_owner/`), never shipped,
    and `Set-TruMenu.ps1` never copies, overwrites or removes it (`Assert-NotOwnerImage`); `tools/pending_upload_scan.py`
    reports a pending `*.arachno*.png` or `work/arachno_owner/` path as an error. Without the file a built-in picture
    (a friendly cat face drawn by code) is used.
* **Camera shake** `[Camera] ShakeScale` (`cam.shakescale 0 .. 100`, 100 = the game's own, no patch): the two callers of
  the shake strength `0x5eb460` (camera apply `0x5eea55`, shake sum `0x5eb56d`) call a stub that multiplies the result.
  **Rumble** `[Camera] Rumble` (`cam.rumble 0 .. 100`): the resolved `XInputSetState` pointer `[0xa02b90]` is wrapped while
  below 100. Test helpers `cam.shakelist` (the `camerashakes` table into the log), `cam.shake <n>` (the game's start by
  key `0x5ee940`), `cam.shakestate`.
* **Labels** (0.20 live test): a reward pot is labelled once - a runtime copy (`INSTANCE_BirthObject` gives a child the
  parent's intro record and a runtime id from `0x40000000`) is skipped while the placed instance (`+0x58` =
  `[intro+0x58]`) is in the walk; instances the game does not draw (hide bit `0x800`, kill flag `0x20`, scene entity
  off, draw masks `-1`) get no label - a picked-up artifact no longer keeps its label in mid air.
* **`ai.remove nearest | others | all | <intro id>`** (game thread): AI enemies out of the world the way the game's
  despawn behaviour does it (`0x61cda0`: hide `0x800`, `CSenseManager::RemoveInstance 0x71dcb0`, the generator's
  notification, kill flag `0x20`; the game's sweep `0x5bcbb0` removes them in the next frame). No damage, no death, no
  save mark (back after a reload). Bar Render / KI "Alle bis auf den naechsten" / "Den naechsten" (right twice), menu
  page AI. A level script waiting for those enemies to die will not go on.
* **Sound list**: bottom right by default (`[Sound] Position=br`; bottom left is the quick-toggle bar's side), rows
  right-aligned in a right corner, the srmusic tracks once in a MUSIK header line (not on every music row); the bar's
  value rows Ton: Ort / Zeilen / Sortierung show their value (0.20.1 showed `?`).
* **Places**: bar page Barrierefreiheit (Arachnophobie + 3 parts + state, Kamera-Wackeln / Vibration 100 / 50 / 0 %;
  the planned rows are replaced, "Blitze daempfen" stays planned), new bar page **Koop** (planned rows only, no
  function yet), menu groups "Arachnophobia, camera shake" and "Co-op / Koop (planned)". The ring has no new entries
  (it is at its 256-entry limit).

## TruMenu 0.21.1 (ai.kill, sticky, room check, physics bodies, enemy spawn, bar page 0 / Tests / groups; 2026-11-07)

Report `docs\Befund-TruMenu-0211-0711.md`; byte checks `work\asi\menu0211\precheck_0211.txt` (62, section
"// ---- 0.21.1 ai.kill" .. "// ---- end of 0.21.1 ai.kill"); analysis files `work\m0211_0711` (`dis_*.txt`).

* **`ai.kill nearest | others | all | <intro id>`** (game thread): enemies die the game's own way - the game's "Kill"
  `0x6376e0` (its only caller `0x63831c` passes type 6 RigidBody) = the damage function `0x637590` with amount = LP,
  then the death check `0x620380` -> `0x641650` -> state `EnemyState_Death`, whose Enter fires the instance's script
  event (vt 31) - level scripts count it (the hall02 wall waits for these deaths, `docs\Befund-Hall02-Wand-0711.md`).
  Per enemy the type is picked first: 6, else 4 / 2 / 1 / 0 - the first one whose case in the live type switch is
  "damage + death check" (TruShadowCombat's `[Damage] Translate` table is read as well), not absorbed by the health mask
  and not on the enemy's regeneration list (the game's `ShouldRegenerate 0x67f040` asked) - so the enemy ends in
  `Death`, not `RegenerateDeath`. Refused for an enemy with brain+8 `0x800`, brain+0xc bit 1 or already dying, and for
  the whole call while the physics step runs or fewer than 60 of the 405 physics bodies are free (a death may build a
  chunkdoll - the "ChunkDoll: failed to create geom" crash). One log line per call, one line ~1 s later with each
  enemy's state.
* **`ai.remove`** warns: an enemy from a generator or with a script is a story enemy - "zaehlt nicht als Tod - Skripte
  warten evtl." in the log line, the answer and the bar's confirmation text.
* **`sticky.get <owner> <key>`**, **`sticky.set [int|bool|float] <owner> <key> <value>`** (set on the game thread):
  owner = an intro id (kind 0) or `<kind>:<id>`; the StickyManager `[0xa13f18]` stores are searched like the game's Find
  (never appended); set writes the value as the game's setters do and calls their change notification; old and new value
  logged. hall02 repair: `sticky.set 11270 17287 0` (population) and `sticky.set 11270 18509 2` (tutorial), then walk
  through the arena trigger 11268 (bar Render / KI, menu AI).
* **Room check**: `player.goto <instance> [force]` refuses a target whose stream unit (`+0xe0`) is not loaded, a
  resident unit's template ("geparkt", parked at (32000, 32000, -32000)), one the game does not draw and one farther than
  25000 units outside Lara's unit; `force` jumps anyway. The enemy / collectible labels say `| geparkt`. `pos.go` to a
  unit behind a portal of Lara's own unit takes the portal path; `pos.goload` and `pos.portal` use only Lara's own
  unit's portals for that (from a neighbour's portal the engine never requests the target). **`unit.go <unit>`** (also a
  shortcut step): nothing when Lara is in it, `cheat.flight 1;pos.portal <unit>` when it is loaded, else `level.load` -
  the regression Prepare "Thrall fight: hall02 + god mode" (`tests\regress\dlc2.txt` step 7) uses it. Two portals away
  (DLC 2 start -> hall02) still needs `level.load`: the engine's unit switch is not built.
* **Physics bodies** (read only): `phys.status` / bar Render / KI "Physik-Koerper n/405" (`[0xa037f4]+0x20a8`, lock
  `+0x20f8`, chunkdolls `[0xecfc70]`), a log line when the used count crosses 300 / 380 / 400 (and back under 280),
  `phys.dump` = the used list grouped by name, orphans (owner 0 or the owner's `+0x274` is another body) one by one.
* **Enemy spawn** `ai.spawn <object> [1..5] [lara|front]`, `ai.spawncount`, `ai.spawnat`: an AI enemy object loaded in
  this level (object tracker status 2, family 14; no generators / chunkdolls / doppelganger) through
  `INSTANCE_BirthObjectNoParent 0x5bd0f0` at Lara or 250 units in front (the debug view's camera); `save.backup spawn`
  before the first spawn of a session; needs `[Cheat] Experimental`. "KI dumm only for these", "model only", gear,
  behaviour and the navmesh check are planned rows.
* **Health bar** `dbg.hpbar` / `[Debug] EnemyHpBar=1`: the enemy labels of the layer Gegner show a bar (green -> red,
  LP / max LP of the difficulty, the number in it) instead of `| LP n`.
* **`menu.hidecursor`** / `[Menu] HideCursor=0`: no mouse cursor over the game picture while the menu is closed
  (WM_SETCURSOR in the client area; no game memory).
* **Quick-toggle bar**: page 0 **Favoriten / Zuletzt** (the favourites, then the last `[Quick] RecentMax` rows that ran,
  kept in `[Quick] Recent`); page **Tests** after Zeit / Test (teleports, the regression Prepare shortcuts - right twice -,
  Stop, the TO TEST rows: right = OK / done / on, left = Fehler / open / off); **collapsible groups** (row kind
  `kQbGroup`: `[-]` open / `[+]` closed, right = open, left = close, `[Quick] Closed`); page Render / KI in the groups
  "Dumme KI", "Gegner spawnen", "Gegner entfernen / toeten" (ai.kill rows, ai.remove rows, the hall02 repair rows),
  "Physik-Koerper", "Lebensleiste"; the long menu's page AI has the same three groups as collapsible sections.
* **Export `TruMenuPadBlock(DWORD pad)`**: the buttons TruMenu keeps from the game right now (0xFFFF = neutral pad; bar
  open: D-pad / LB / RB) plus bits 16 / 17 / 18 = menu / ring / bar open - for plugins that read the pad themselves.
  The pad import filter: while the pad pointer is still empty a rewritten import slot `0x83e08c` is logged with the
  module that wrote it (`pad: import slot ... was rewritten ...`, diagnosis only).

```text
0.21.1: ai.kill ok (27 checks), sticky ok (16 checks), room check ok (3 checks), physics bodies ok (11 checks), enemy spawn ok (1 check), health bar ok (4 checks); [Debug] EnemyHpBar 1, [Menu] HideCursor 0, [Quick] RecentMax 8, Closed ''
ai.kill others (src=quick): 3 of 4 AI enemy(ies) killed the game's way (...); kept the nearest ... - viking_thrall_tutorial_dlc2_ 0 (type 6 RigidBody, LP 500 -> 0, script), ...
ai.kill: 1 s later 3 of 3 in a death state (...): viking_thrall_tutorial_dlc2_ 0 Death, ...
sticky.set int 0:11270 key 17287 (index 37): 3 -> 0 (src=quick; the game's set + change notification 0x004af740)
phys: bodies used 301 / 405 (crossed 300; peak 301), chunkdolls 1 / 4, lock 0 - ...
```

## TruMenu 0.21.2 (queued items outside the pad hooks of other plugins; 2026-11-07)

Report `docs\Befund-Padkette-StartView-0711.md`; build `work\asi\menu0212`; no new byte check (no new game address).

Live 2026-11-07 14:55 (DLC 2): from one moment on, every View + Start of the quick bar also opened the game's pause
menu. Cause: the bar row "Fliegen" queued `cheat.flight 0`; the item runs on the game thread inside PadHook and its
message 12 to the player makes the game poll the pad again through 0x00a02b8c. In that run TruLink sat outermost
(`game -> TruLink -> TruShadowPower -> TruMenu -> XInputGetState`), was still on the stack and took the same-thread
re-entry for a hook loop: `pad hook re-entered (hook chain loops back to TruLink) - calling XInputGetState directly
from now on` (TruLink.log 14:55:07.230). TruShadowPower and TruMenu were out of the chain for the rest of the session
(`pad: slot not polled - reading the pad in Present`, never "polled again"); the bar then worked from TruMenu's own
reads in Present, which cannot mask - the game got Start. The same happened once before (16:14:39, also
`cheat.flight 0`, TruLink outermost); `cheat.flight 0` in the other orders (TruMenu or TruShadowPower outermost) never
cut the chain.

0.21.2: PadHook runs a queued item only when the **game itself** called it (return address inside tru.exe - no other
pad hook is outside PadHook on this thread); otherwise the item waits for the Present hook (same thread, between two
polls, the path the front end has always used) - at most one frame later. One log line per caller module
(`pad: PadHook is called through another pad hook (TruLink.asi, return 0x...) - queued items run in the Present hook
instead ...`), later items at LogLevel 2. Without a Present hook (d3d9 code check failed) items run in PadHook as
before. The per-frame ticks of PadHook are unchanged. The order of the three pad hooks still depends on load timing
(the import slot is rewritten to KERNEL32's GetProcAddress after TruMenu's filter in every run - by whom is unproven);
with this rule and TruShadowPower 0.19
(TruMenuPadBlock, no re-wrap) no order cuts the chain (model `padchain` in `tools\trumenu_quick_check.py`, all six
orders).

## TruMenu 0.21.3 (quick bar: X runs, Y pins; sound list width; 2026-11-07)

Report `docs\Befund-TruMenu-0213-0711.md`; build `work\asi\menu0213`; no new byte check (no new game address), no new
option (only the comments of `[Quick] Enabled` / `OpenButtons` name X / Y).

* **X and Y belong to the open bar.** Before 0.21.3 the bar kept only D-pad / LB / RB from the game (`kQbOwn 0x030F`) -
  X and Y reached the game while the bar was open. Now `kQbOwn = 0xC30F`: QbPad masks X / Y in the state the game gets
  while the bar is open, a button held at the close stays away until it is released (as the D-pad), and the export
  `TruMenuPadBlock` reports them while the bar is open (same meaning: the buttons the game does not get).
* **Y = favourite** (as Y in the long menu / `fav.add` / `fav.del`): pins / unpins the selected row's item in
  `[Favorites] Ids` (toggled by item id, so an item is never in the list twice and every row of that item shares the
  state); the footer says "als Favorit angeheftet (Seite 1)" / "Favorit entfernt", page 0 "Favoriten / Zuletzt" is
  rebuilt every frame (a pinned row moves out of "Zuletzt" at once). Only rows that are one item **without an
  argument** can be favourites - `[Favorites] Ids` holds item ids; `dbg.show death`, `ai.dumb sharks`, `shot.save ui`,
  `ai.kill others`, the chapter rows etc. are refused with a footer line. Headings, groups, planned rows and the special
  rows (positions, checkpoints, saves, Prepare, TO TEST) say "keine Item-Zeile". Log: `quick: <page> / <row> -> Y: fav
  add|del <id> (...)`.
* **X = execute.** Action, choice, info and planned rows and every special row: exactly the right press - so every
  confirmation row keeps its safety: the first X arms (footer "rechts / X nochmal (3 s) = ausfuehren"), a second X **or**
  right on the same row within 3 s runs it (Spiel beenden arms itself for 10 s; the Saves rows ask twice inside their
  items as before). bool rows: X toggles. Group rows: X opens / closes. **Value rows: X does nothing** (footer "Wert mit
  links / rechts (X: nichts)") - a value row has no default step of its own; left / right stay the way. One of Y, X,
  left / right per frame (Y first): an X and a right press in the same frame never count twice.
* **Footer**: the second line (never replaced by a result) reads `X: ausfuehren  Y: Favorit   View + Start: zu`
  (EN `X: run  Y: favourite   View + Start: close`); the page-0 heading `Favoriten (Y = anheften / loesen, hier und im
  Menue)`.
* **Sound list width** (`snd.list`): the box now follows the rows of the current frame. Cause of the old behaviour: in a
  right corner every row was shifted to end at the window's right edge (`avail - w`), which made the content always as
  wide as the window, so `AlwaysAutoResize` could only grow it. Now the rows are gathered first, the widest one of this
  frame sets the right edge (at most the window's content width), right alignment in the right corners stays; left
  corners were not affected.

Checks: `tools\trumenu_ini_check.py` `check_0213` (14 negatives), `tools\trumenu_quick_check.py` chord (+3 X / Y cases)
and models `xyfav`, `xyexec`, `footer`, `sndwidth`.

## TruMenu 0.21.4 (hall02 counter rescue, thrall script value; 2026-11-07)

Report `docs\Befund-TruMenu-0214-0711.md`; build `work\asi\menu0214`; 19 new byte checks (`precheck_0214.txt`, table
`kH2Checks`), no new option (the sample `TruMenu.ini` is the 0.21.3 one). Background: `docs\Befund-Hall02-Zaehler-Drift-
0711.md` (why population stays at 4) and `docs\Befund-Hall02-TU-Vergleich-0711.md` (root cause: the intro data of
generator 10028 are mis-converted on the PC, so checkpoint 11258 stores pre-spawned thralls - the Xbox never does). The
real fix belongs into the data; TruMenu only rescues saves that already hold them.

* **`fix.hall02`** (game thread, bar page Tests "hall02-Zaehler reparieren" right / X twice, long menu page AI group
  "Gegner entfernen / toeten"): refused unless Lara's stream unit is `dlc_yggdrasil_hall02`, the dispatcher 11270 has its
  sticky values, `broken` (10029) is 0 and **no** object-1004 `viking_thrall_tutorial_dlc2_` is alive (alive = present
  `[inst+0x44] != 0`, no kill flag `+0x14 & 0x20`, brain not in Death / LandDeath / DrownDeath / DeferredInstantDie -
  RegenerateDeath counts as alive; without a readable brain: hidden = gone, else alive). Then `tutorial` (18509) = 2 if
  below 2, `population` (17287) = 0 - both through `sticky.set` (the game's write + change notification, old / new
  logged). The answer: "jetzt einmal durch den Arena-Trigger 11268 zurueck- oder hineinlaufen (Pruefung nur beim
  Betreten / Verlassen)" with the trigger's live position and distance; with `[Debug] Enabled` the debug view layers
  Trigger + Trigger-Namen are switched on (drawing only) so the trigger is visible.
* **`thrall.scriptval`** (read only, bar page Tests, long menu): every object-1004 thrall with intro (runtime / placed),
  state and its thrall-script int +8, plus every other generator enemy (raw +8, other script) into `TruMenu.log`;
  expected: restored 0, generator-born 2. Address = the game's own path: `[[inst+0x60]+0xc]+8` - `[inst+0x60]` is the
  script reference the generator hands to OnSpawn (0x781342) and the death event uses (0x66c31f); the interpreter's
  op14 (0x57d04b) takes member data `[R+0xc]` (0 when R or the data is 0), script 22809 f0 writes "R.+8 = 2" with it.
* Not built (coordinator, after the TU comparison): the restore-time safety net E3 (`[Fix] Hall02Restore`) - it would
  imitate behaviour the Xbox does not have.

Checks: `tools\trumenu_ini_check.py` `check_0214` (17 negatives), `tools\trumenu_quick_check.py` models `h2drift`,
`fixhall02`, `scriptval`.

## TruMenu 0.21.5 (page Fixes: plugin INI switches; the ring is frozen; 2026-11-07)

**Bar page "Fixes" / menu section "Fixes"** - one data file `TruMenu.switches.txt` (source `src\asi\TruMenu\`,
`Build-TruAsi.ps1` copies it into the build folder, `Set-TruMenu.ps1` installs it next to `tru.exe` with the
first-line rule of the radial / tour files: ours = first line starts with `# TruMenu switches`; `-Remove` deletes only
ours). Format (also in the file header):

```text
group | <key> | <DE heading> | <EN heading> [| open]
<Plugin> | <Section> | <Key> | bool | int:<lo>..<hi>[:<step>] | choice:<a>,<b> | <DE> | <EN> | live | restart | live-if:<Key> | <default> | <hint> [| <since>]
```

- `live` = the plugin re-reads the key while the game runs (about once a second): TruShadowCombat `[Damage]`,
  `[Chunk]`, `[Splash]` `Translate`, `[Strike] Translate`, `[States] Translate1013 / 1019 / 1020 / 1004 / 231Slot0 /
  231Slot1`, `[Death] TranslateNotify33` (0.6.3), TruShadowPower `[Adrenaline] Translate` (K11); `live-if:LiveReload` =
  TruMercLang `Enabled` / `Language` (live only with `LiveReload=1` at the start); every other key is read once in
  DllMain (`restart` / "Neustart"). Some live keys only act when their hook was installed at the start (the hint says
  so, e.g. `[Damage] Translate` needs `Translate` or `Log` = 1 at the start).
- 112 switches in 9 groups (DLC 2 Kampf, Schattenkraft, Kampf Grundschalter / Diagnose, HUD, Felsader,
  Doppelgaengerin, DLC 2 Spielerin / Kostuem, Soeldner-Sprache, TruTrace): every key of the eight plugin INIs except
  the text filters (`PathFilter`, `SpawnFilter`, `ProgressFilter`). Keys that exist only in code (TruShadowPower
  `Cond1046` / `Cond1055`, the hidden TruRockVein keys) are not listed (not in the sample INIs). TruGuard is not part
  of it.
- Bar: one group row per group (`[+]` / `[-]`); **one group open at a time** (right / X opens and closes the others,
  left / X closes; kept until the game ends, the file's `open` mark = the start state) - with all groups open the page
  would have 124 rows (`kQbViewMax` 64). Switch row: name, value (`an` / `aus`, `< 3 >`, `< es >`; a key missing in
  the INI shows the default in brackets, a plugin without INI `keine INI`), count column `live` / `Neustart`. Right /
  left = on / off or one step (stops at the end), **X** = toggle (bool) or one step up with wrap (int / choice). **Y**
  is refused ("Fix-Schalter sind kein Favorit"): `[Favorites] Ids` holds item ids without an argument and a switch row
  is `sw.set <target> <value>` - no pinning, no recent rows for these rows.
- Long menu: section "Fixes: plugin switches / Plugin-Schalter (0.21.5)" - tree node per group, checkbox / - + /
  choice buttons, tooltip = hint; buttons `sw.reload` / `sw.list`.
- One write path, item `sw.set <Plugin>:<Section>:<Key> <value>` (bar, menu, TruLink): only keys listed in the file,
  only values of the row's type / range, only into an existing `<Plugin>.ini` next to the `.asi` files (a plugin that
  is not installed never gets an INI), never an unchanged value; `WritePrivateProfileStringA` as the TO TEST toggle
  rows (`TestIniTarget`). The live re-reads pass the current value as their default, so a read that meets the write
  keeps the old value one second longer. Log `sw.set <Plugin> [<Section>] <Key>: old -> new (live|restart) in <path>
  (src=...)`. `sw.list` logs every row with its INI value, `sw.reload` reads the file again.

**Ring frozen** ("aktuell nicht weiter gemacht"): `TruMenu.radial.txt` keeps its 172 entries, no new ones (header
note). Every ring entry is now a bar row: 52 were ring-only and became rows - Notfall (Befreien (Marke), Saves
sichern), Lara (Foto wie im Rad, Positionen: Liste, group "Objekte spawnen (Rad-Stufe R2)" with the five
`instance.spawn` rows, right / X twice), Debug / Darstellung (Schnellschalter, Darstellung / Debug / Ton: Stand),
Leveldaten (Checkpoints alle zeigen / verbergen / Liste), Zeit / Test (Ton mit Welt anhalten, Shader-Uhr mit anhalten,
Musik Thailand / stoppen) and the new page **Render-Details** (groups Flach-Ansicht Farbe / Paesse, Navmesh,
Objektnamen). The long menu got the section "Quick bar pages / Schnellleiste-Seiten (0.21.5)": every static row of
every bar page from the same tables (confirmation rows with the menu's A-twice `ConfirmButton`, chapters back up
first) - so the menu reaches every ring entry too. The bar now has 15 pages.

Checks: `tools\trumenu_ini_check.py` `check_0215` (switches file format, every key in its plugin INI with the shipped
default, live claims against the plugins' re-read functions, every INI key covered; ring frozen + every entry a bar
row; 19 negatives), `tools\trumenu_quick_check.py` models `switches`, `swfold`, `ringparity`. No new game address, no
new byte check, imports / exports unchanged. Not in 0.21.5: the SweepAndPrune read-out (P6a) and the shader labels
(room for 0.21.6).

## TruMenu 0.21.6 (bar page Kostueme, flight key line, quick command line; 2026-11-07)

Owner wishes 2026-11-07: "Kostuem-Wechsel in der Leiste waere auch gut" (a list or one row switched with left / right -
both), "beim Fliegen anzeigen, mit welchen Tasten man fliegt, die stehen ja nicht da", and the TODO item "Kleine
Kommandozeile in der Leiste" ("bau das direkt mit"). Build `work\asi\menu0216`; no new game address, no new byte check;
one new option `[Cheat] FlightHint`.

**Bar page "Kostueme"** (page 4 of 16, right after Lara - its own page: with the list open it has 4 + N rows, N = the
outfit cycle list, about 36; on the Lara page that would be 15 + 8 positions + 4 + N > 64 = `kQbViewMax`; the bar is now
at its 16-page limit, `kQbStartPage` = 5 = Leveldaten). Every row runs the existing items on the data of the long menu
sections "Outfits (live switch)" / "Outfits (next level load)" - no new write path:

| Row | Keys | Item |
|---|---|---|
| `Kostuem: < name >` | left / right = previous / next entry of the cycle list GlobalInfo `[0xe7ee50]+4`, **wraps** at both ends; only the shown name changes, the switch runs once the choice stood still **0.5 s** (`kCosSettleMs`; `QbCosTick` every frame, also with the bar closed) - holding or tapping quickly never switches on every step; one switch = one `quick: Kostueme / Kostuem -> costume.set <id>` line; **X** = the shown entry now; the entry worn already = "schon an", nothing runs | `costume.set <object id>` (live, 0x6f0a90) |
| `Naechstes Kostuem` | right / X | `costume.next` (the game's own cycle step) - kept: the only costume row **Y** can pin as a favourite (no argument) |
| `Fuers naechste Laden + neu laden` | left / right = a player record of the type table (wraps, only records whose name is in the object list), **X** arms, X or right within 3 s runs (the confirmation of the other reload rows) | `costume.choosereload <record index>` (choose + reload the unit) |
| `[+] Alle Kostueme (N)` | closed at the start; right / X open, left / X close (as a Fixes group; kept until the game ends) | - |
| one row per cycle entry | right / X = this costume now; the worn one is marked (green square, "aktuell") | `costume.set <object id>` |

Head line: the current costume `[0xe7f1c8]`, the list / record counts. Labels: `dlc_costume_<a..p>` = `<slot> <the game's
outfit text> (<object name>)`, e.g. `f Casual Explorer (dlc_costume_f)` - the texts are PC locals ids 83 + slot (B138
`locals.bin_001`, measured in `work\rebuild\costumes_0311\logs\check_names.txt`, `docs\Befund-Kostueme-Port.md`; g, n and
o all read "Grey Jungle Shorts"). Every other costume (`lara_*`, `dlc_doppel_costume_a..d`, `doppelganger_casual`) shows
its object name only - no text mapping is known for them. Without a level (or with `[Cheat] Experimental=0`, or a failed
costume code check) the rows are grey with the reason in the right column ("braucht ein Level") and refuse with it. **Y**
on a costume row other than "Naechstes Kostuem" is refused ("Kostuem-Zeilen sind kein Favorit"): `[Favorites] Ids` holds
item ids without an argument (as page Fixes in 0.21.5). The footer's first line names the selected row's keys.

**Flight key line** (`[Cheat] FlightHint`, default 1): while `cheat.flight` is on, in a level, and the menu is closed,
one line bottom right: `Fliegen: RT hoch | LT runter | Stick bewegt | Tempo 20` (EN `Flight: RT up | LT down | stick
moves | speed 20`, the bar's language `[Quick] Language` / `quick.lang`). The bottom-right corner may already hold the
sound list (`[Sound] Position` br, the default) and the flow status line (`[Flow] Position` br): the line is drawn after
them and goes above whichever of their windows of this frame reaches into the bottom-right quarter - it never covers
them. The same text is the footer of the bar rows "Fliegen" / "Flug-Tempo" while selected and the tooltip of the menu's
flight button (Cheat page) and of the row in the section "Quick bar pages". Keyboard: FlightTick reads the pad only -
there is **no** key for up / down (horizontal movement = the game's walking keys); "Tastatur: nicht belegt" did not fit
the short line, it is in the tooltip ("pad only - no keyboard key for up / down").

**Quick command line** (TODO "Kleine Kommandozeile in der Leiste"): in the open bar `[Cmd] FocusButton` (**L3**, the
button that focuses the menu's command bar) pressed and released **alone** opens / closes a compact command line right
of the bar: one input line, the last 4 answers (newest first, coloured ok / err), a key line. L3 is free in the bar (the
bar owns D-pad / LB / RB / X / Y, View + Start toggle it); a press that becomes part of L3 + R3 (long menu / ring hold:
`[Menu] ToggleButtons`, `[Radial] HoldButtons`) is not one - R3 down while L3 is held cancels it, as the 0.7 FocusButton
rule. It is the 0.6 command bar's line, **one command path**: every run goes through `CmdRunLine` (same parser `help` /
`list` / `get` / `<id> [arg]`, same items, the history shared with the menu's bar and TruLink `cmd.run`, the log line
`cmd (quick): <line> -> <answer>`, queued game-thread answers via `CmdNoteQueued` / `CmdPollQueued`).

- Keyboard: typing goes to the line - key messages go to ImGui only and the game's DirectInput keyboard gets no events
  while it is open (as the menu with `[Menu] BlockGameInput=1`); Tab = the first suggestion of the command bar's list,
  Up / Down = history, Enter = run, Esc = close.
- Pad: D-pad up / down = history (older / newer), **A** = run, **B** = close, L3 = close. While the bar is open L3 is
  kept from the game, while the line is open A and B too (`QbPad`; `TruMenuPadBlock` reports them); the bar's rows wait.
- Closing the bar, opening the long menu or the ring closes the line. `[Cmd] Enabled=0` = refused. Log `quick: command
  line opened / closed (<why>)`.
- Not built: the 0.7 on-screen keyboard (it lives inside the long menu window - DrawOsk and its focus rules); with the
  pad only history lines can be run.

**Toggle rows show their state** (owner live test 2026-11-07 20:52: the Navmesh rows only said "rechts"): the rows that
flip a flag per argument are bool rows now - page Render-Details, group Navmesh (`nav.draw planner_areas` /
`planner_areas_solid` / `planner_connectivity` / `planner_area_normals` / `obstacles` / `recent_navprobes` /
`draw_mover3d_path`) and group Flach-Ansicht (`dbg.flatpass 0x200` / `0x100` / `0x80` / `0x400` / `0x800` / `1` / `2`).
State `an` / `aus` from the ring's `RadialOn` (the NavPower switch byte the item writes, e.g. `0x008bf2e5`; the pass bit
of the flat view's mask); right = on, left = off (no blind flip; "schon an" writes nothing), X = toggle; the item gets
`<switch> 1|0` (no new write path). A Navmesh row that is on but cannot draw shows `an` in orange with the reason in the
right column - `(Ebene fehlt)` when no layer that holds a navgraph is in the layer mask `[0x88e454]` (nav.mask 1),
`(nur mit Flaechen)` for connectivity / normals without planner_areas(_solid) - the conditions of NavSet's log notes,
read only (`NavRowNote`). The other action rows of the bar were checked: none else flips a readable flag (setters with a
fixed value - `dbg.flatcolour`, `dbg.namefilter` / `namecolour` / `namesize`, `dbg.cpall 0` / `1` - stay action rows).

Checks: `tools\trumenu_ini_check.py` `check_0216` (FlightHint key, page / row limits, costume rows from the cycle list
and the records, debounce + wrap, refusal without a level, Y refused, flight line rule, one command path, toggle rows =
bool rows with a RadialOn state, NavRowNote read only; 22 negatives in `work\m0216_0711\make_negative.py`),
`tools\trumenu_quick_check.py` models `cosbar`, `cosdebounce`, `flighthint`, `quickcmd`, `togglerows`.

### TO TEST 0.21.6 (owner)

| # | Step | Expected |
|---|---|---|
| 1 | game start | `TruMenu.log`: `TruMenu 0.21.6 (` |
| 2 | main menu: bar (View + Start), RB to page **Kostueme** | rows grey, right column "braucht ein Level"; right on "Kostuem" = refused with the reason |
| 3 | in a level: page Kostueme, head line | "aktuell: <costume> - N im Wechsel, M Spieler-Records" |
| 4 | "Kostuem": right 5 x quickly | the name steps (wraps at the end), Lara changes **once** about 0.5 s after the last press; `TruMenu.log` one `quick: Kostueme / Kostuem -> costume.set` line |
| 5 | "Kostuem": left once, then X at once | switches at once (no 0.5 s wait) |
| 6 | "[+] Alle Kostueme": right, then right on a DLC costume | list opens (`f Casual Explorer (dlc_costume_f)` style names), the costume is worn, marked "aktuell" |
| 7 | Y on a list row / on "Naechstes Kostuem" | refused "Kostuem-Zeilen sind kein Favorit" / pinned (page 1) |
| 8 | "Fuers naechste Laden + neu laden": right to a record, X, X | unit reloads with that costume |
| 9 | Lara page "Fliegen" on, close the bar | bottom right: "Fliegen: RT hoch \| LT runter \| Stick bewegt \| Tempo 20"; with the sound list on (br) the line sits above it |
| 10 | open the long menu | the line disappears; Cheat page: hover the flight button = the keys as tooltip |
| 11 | `[Cheat] FlightHint=0`, restart, fly | no line |
| 12 | bar open, L3 alone; type `get cheat.speed`, Enter | command line right of the bar; answer `ok cheat.speed = 20`; `cmd (quick):` line in the log |
| 13 | D-pad up, A | the last line again from the history, runs |
| 14 | L3 + R3 with the bar open | long menu opens, the command line does **not** toggle (and closes) |
| 15 | B | command line closes, the game never saw A / B / L3 |
| 16 | page Render-Details, group Navmesh: "Navmesh Flaechen" right, right, left | `an`, "schon an", `aus`; X toggles |
| 17 | "Navmesh Flaechen" on with "Alle Ebenen" off in a level whose navgraph layer is not in the mask | `an` orange, right column "(Ebene fehlt)"; "Alle Ebenen" on = white `an`, no reason |
| 18 | group Flach-Ansicht: "Pass 0x200" left / right | `aus` / `an` as the flat view's mask (`dbg.render`) |

## TruMenu 0.21.7 (footer / help, umlauts, refused costumes, chapter units, uber / shader / navmesh labels; 2026-11-07)

Night build after the owner's live test of 0.21.5 / 0.21.6 (`docs\Autopilot-2026-11-07.md` from 20:38). Build
`work\asi\menu0217`; 85 new byte checks (three read-only label layers, the SweepAndPrune read-out), no new hook,
imports / exports unchanged.

**Bar footer.** The X / Y line says `Y: -` where Y is refused (`QbFavOk` = the rule of `QbFavPin`: one item without an
argument - page Fixes, costume, chapter-unit, position / checkpoint / save rows and rows with an argument), adds
`L3: Befehlszeile` (EN `cmd line`; the `[Cmd] FocusButton` name, only with `[Cmd] Enabled=1`) and, while the game is
not calling PadHook (the pad is read in Present: front end / loading), `(Pad NICHT gesperrt)` in orange.

**Help line** (TODO "kurze Hilfe-Zeile"): rows that are not self-explanatory have one line "DE|EN" of at most 60
characters per language - the bar's footer (a third line while the row is selected) and the long menu's tooltip. Bar
rows: table `kQbHelp` keyed by item + argument (`*` = any argument; 46 rows: Navmesh / Render-Details / flat view,
debug view, flight, triggers, time / sound, costume.next, chapter starts, the new label layers). Page Fixes: the hint
column of `TruMenu.switches.txt` is now `<DE help> // <EN help>` (each at most 60 characters). Costume and chapter-unit
rows have their own lines (a refused costume says why).

**`TruMenu.switches.txt` with umlauts.** UTF-8 without BOM (a BOM is skipped anyway); the German texts use their umlauts
(`Doppelgängerin`, `Kostüm`, `Söldner`, `Zustände` ...), plugin / section / key / type / when / default stay ASCII. The
bar font (ImGui's built-in ProggyClean, range 0x20 .. 0xFF) has the glyphs - `work\m0217_0711\font_glyphs.py`
decompresses the embedded font and finds outlines for ä ö ü Ä Ö Ü ß. Texts cut by a field limit lose at most the
partial last character (`SwCopyText` / `Utf8TrimTail`). 114 switches now (+ TruShadowHud 0.2 `TranslateDlc2F1`;
TruShadowPower 0.20 `CameraFlag` default 1 - both from tonight's plugin builds, rows from the coordinator). The code's own texts stay ASCII (no `/utf-8` in the build).

**Costumes the game refuses** (live 21:14: object 33 "refused by the game's check 0x005c54e0 (no .drm?)"): while page
Kostueme is shown, `CosValidTick` runs that check once per changed cycle list on the game thread (the pad hook's
once-per-frame block, where `costume.set` runs it too); refused entries are grey ("abgelehnt (keine .drm?)"), the
`Kostuem` row's left / right passes over them, right / X on one is refused, the head line counts them, one log line
`costumes: N cycle-list entries checked ..., K refused`. No new write path.

**Page Kapitel: units per chapter** (TODO "Abschnitte je Level"): below the chapter starts one foldable group per chapter
/ DLC with its units from the level list (`kUnits`, 111 units in 10 groups; one group open at a time). A unit row runs
exactly what a chapter row runs - right / X twice within 3 s = `save.backup kapitel`, then `level.load <unit>` (debug, no
story values). DLC 2 units other than `dlc_level2_start` are orange with "Doppel-Zustand?" and the confirmation says
"Doppelgaengerin evtl. nicht aufgesetzt (besser DLC-2-Start + laufen)". Lara's unit is marked "Lara hier".

**Uber labels** (`dbg.uber`, bar page Leveldaten "Tore / Plattformen (Zustand)"; `uber.dump`; `[Debug] UberLabels /
UberRadius 8000 / UberMax 12 / UberMatch switch,lever`): every instance with an uber state (the engine's path 0x4d5d59:
`[[inst+0x2d0]]+0x2ec - 0x10`, magic 0xF0012345) within UberRadius of Lara - independent of LabelMatch / LabelRadius
(the dlc_caverns_hall gates stood 3165 / 3357 units away, LabelRadius was 3000) - gets "<object> <intro> | <distance>"
and its state: the node name, for a timed transition (condition 1 = time in node, 0x4d3204) the time left, for a running
transition the target. Gates (object name holds "gate"): `Tor: oben, noch 12 s` / `Tor: faehrt runter` / `Tor: unten,
bereit in 1.5 s` / `Tor: unten, bereit`. Instances matching UberMatch without an uber state get a plain label.

**Shader labels** (`shader.labels`, `shader.dump`, `shader.reload`; bar page Render-Details group "Shader-Etiketten";
`[Shader] Labels / File / LabelRadius 15000 / LabelMax 40 / ShowOrig`; stage S1 of `docs\Befund-Shader-Etiketten-0711.md`
section 4): terrain batches of `TruMenu.shaderlabel.txt` (written by `tools\shader_labels.py build`, generated locally,
`Set-TruMenu.ps1` installs it from the build folder when present) whose owner unit / streamgroup is loaded, nearest to
Lara by box distance, one per material within 2000 units. Line 1: material, file status, slots, PC libs, terrain section;
line 2: the **live** state - the material's `PCMaterial` from the game's hash map, its four lib pointers, their ids from
the lib hash map: `live = Datei` or `live PART S-TS 1909/-/2851/1911 (Datei SURR)`. Colour by the live status (SURR red,
PART orange, UNK violet, TU green, ORIG / BASE yellow; ORIG / BASE only with ShowOrig=1). Not built: the red tint per draw
(S2), `shader.pick` / `shader.aim`, object (O) and streamgroup (G) labels.

**Navmesh labels** (`nav.labels`, Render-Details group Navmesh "Navmesh beschriften"; `[Debug] NavLabels /
NavLabelRadius 3000 / NavLabelMax 40`; stage 1 of TODO "Navmesh beschriften"): at each area of the layers the planner
draws (the mask: "Alle Ebenen" = `nav.mask 1`) near Lara: `E<layer>.<graph> #<area> <unit>` and `27:x 26:x b8:x b12:x | n
Kanten` in the area's fill colour, plus one legend line of the engine's edge colours (0x40c3a0: light blue edge type
0x200, red bit 27 on either side, orange +0x34 bits 8..11 > 1, yellow bits 12..15 > 1, blue bit 26 differs, magenta bit 26,
green). Path: planner [0x8bf310] -> 32 layers -> 8 graphs -> area block `[g+0x1c]`, size `[[g+0x18]+8]`, stride 0x38 +
0x14 * edges. The unit name comes from an address test against the units' NavPower images (Level+0x60) - shown only when
it matches. Areas cut by obstacles are labelled as their static area. Not built: stage 2 (the NavPower text stub
0x6457a0), islands.

**SweepAndPrune read-out** (P6a; `sap.status` info, `sap.reset`; bar page Render / KI "Kanten-Kollision (SAP)";
`[Debug] SapWatch` default 1; `docs\Befund-SweepAndPrune-0611.md` section 4): the markup collision pool of the
MarkupManager `[0xdb94cc]` read every 250 ms (render thread, read only, the finding's chain with all its plausibility
checks - N 1000 / 3000, M 200 / 500, memory 1 + 204 N + 16 M, endpoints 2 b): boxes b / N, pair links p / 2M, proxies u /
1000 (list walk), session peaks, frames with a full pool, the warning mark ("Out of space for pairs / boxes" in 0xa035f0).
One `sap: new peak in <unit> - boxes ... pair links ... proxies ...` line per new peak (at most every 2 s). Decision rule of
the finding: boxes >= 800 or pairs >= 320 (80 %) or any full frame -> translate the TU constants.

**Front-end pad (research, not blocked):** the game reads the pad only through the XInputGetState pointer 0x00a02b8c (3
call sites: 0x482619 / 0x48620a device checks, 0x484b82 the per-frame poll) - no second input path. The miss in the DLC 2
mission menu is most likely PadHook not being called there (unproven - an archived run's main menu did call it; in the
Present fallback `QbPad`'s clear never reaches the game - the footer now says "(Pad NICHT gesperrt)"); 0.21.7 logs `quick: bar open while PadHook is not called ...`
and `quick: bar buttons 0x.... pressed while PadHook is not called - the game reads them too (diagnosis 0.21.7)` once per
bar opening - read only, nothing blocked yet (a block needs the live answer which hook chain the front end runs).

Checks: `tools\trumenu_ini_check.py` `check_0217` (+ the 0.21.7 rules of `check_switches`: UTF-8 / umlauts / hint halves;
33 negatives in `work\m0217_0711\make_negative.py`), `tools\trumenu_quick_check.py` models `yfooter`, `utf8cut`,
`cosvalid`, `uber`, `navwalk`, `chapters`, `shlive`; byte lists `work\asi\menu0217\precheck_0217_uber.txt` (8) /
`_shader.txt` (27, = `work\shaderlabel_0711\precheck_shaderlabel.txt`) / `_nav.txt` (30) / `_sap.txt` (20, =
`work\sap_0611\precheck.txt`).

### TO TEST 0.21.7 (owner)

| # | Step | Expected |
|---|---|---|
| 1 | game start | `TruMenu.log`: `TruMenu 0.21.7 (`, `0.21.7 uber labels: checks ok (8 rows)`, `shader labels: checks ok (27 rows)`, `navmesh labels: checks ok (30 rows)` |
| 2 | bar, page Fixes, a switch row | footer `X: ausfuehren  Y: -  L3: Befehlszeile`, help line in blue (e.g. "Schadensarten 17-27 wie TU ..."); group names with umlauts (Doppelgängerin, Söldner) |
| 3 | page Render-Details, "Navmesh Flaechen" | help "Umrisse der Gegner-Laufflaechen - braucht 'Alle Ebenen'"; on a plain item row (e.g. "Alle Ebenen") `Y: Favorit` |
| 4 | page Kostueme in a level, open "Alle Kostueme" | refused entries grey "abgelehnt (keine .drm?)"; head line "N vom Spiel abgelehnt"; `TruMenu.log` one `costumes: ... refused` line; "Kostuem" left / right skips them |
| 5 | page Kapitel, group "Abschnitte DLC 2 ...", right on dlc_yggdrasil_hall02 | orange "Doppel-Zustand?", footer note "besser DLC-2-Start + laufen"; second right = backup + load |
| 6 | dlc_caverns_hall, Leveldaten "Tore / Plattformen (Zustand)" on | both gates labelled from the switches' platform; switch on: "Tor: faehrt hoch", "Tor: oben, noch 25 s" counting down, "faehrt runter", "unten, bereit in 2 s", "unten, bereit"; `uber.dump` lines |
| 7 | `TruMenu.shaderlabel.txt` installed, dlc_yggdrasil_end, Render-Details "Shader-Etiketten" on | red labels "23164 SURR S-SS 1909/-/1910/1911 [Gelaende 20969]" at the goo tube; line 2 `live = Datei` (installed tree) or `live PART S-TS ... (Datei SURR)` with the shader test copy; `shader.dump` block in the log |
| 8 | hall02, "Navmesh Flaechen" + "Alle Ebenen" + "Navmesh beschriften" on | legend line at the top; labels `E11.0 #n` with flag bits; the red / magenta areas show `27:1` / `26:1` |
| 8b | big DLC 2 rooms (end, machine room) / F2 flight, page Render / KI "Kanten-Kollision (SAP)" right | "Boxen b/N (Spitze ..), Paare p/2M ..." with the limits read from the core (PC 1000 / 400; 3000 / 1000 with TruRockVein 0.10 `[SweepAndPrune] Translate=1` - 0.21.8 adds "Grenzen ..."); `sap: new peak` lines in the log |
| 9 | DLC 2 mission menu: bar open, left, X | if X still starts the mission: footer "(Pad NICHT gesperrt)" and the log's "diagnosis 0.21.7" lines; if neither shows, PadHook was called and the leak is elsewhere (note the time) |

## TruMenu 0.21.8 (quick command line: suggestions, keyboard, history safety; favourites with an argument; story values; sound group sliders; 2026-11-08)

Night build `work\asi\menu0218` (TODO items "TruMenu 0.21.8", "kleine Befehlszeile ausbauen" (2) / (3), the history
accident of 2026-11-07 21:23:53 - `cheat.god 0` from the quick command line's history). 6 new byte checks (sound
groups), one check row moved, one second form accepted; no new hook, imports / exports unchanged.

**Byte checks next to other plugins' patches.** TruShadowCombat 0.6.5 H1 rewrites the call at 0x6203e4 (death check ->
`RegenListHook`); `kAkChecks` (ai.kill) now checks `{0x006203e9, "83c410 84c0 7417"}` (the bytes after the call) - it
passed before only because TruMenu.asi loads first. No other TruMenu check touches the 0.6.5 sites 0x6824b9 / 0x6826d3 /
0x65b181 or the vtable entries 0x85b104 / 0x85b0fc / 0x85b15c / 0x858c90 / 0x859160 (`work\m0218_0711\overlap_scan.py`).
TruRockVein 0.10 (`[SweepAndPrune] Translate`) rewrites 0x5be3a7 (create(3000, 500)) and 0x5be3c4 (field 500):
`SapCheck` accepts the retail row or its TruRockVein form (`kSapChecksTu`, only for the same row); `sap.status` says which
limits the core has ("Grenzen PC 1000/400" / "TU 3000/1000 (TruRockVein 0.10)"). `TruMenu.switches.txt` has the new
rows TruRockVein `[SweepAndPrune] Translate` and TruShadowCombat 0.6.6 `[Death] TranslateT5` / `TranslateVaulted` /
`TranslateVaultedClock` (live, `P1dReadSwitches`) - 125 switches. TruShadowCombat 0.6.6's patch sites (0x63ad82,
0x71d5cc, 0x63b421, 0x623fa2, 0x65a4a2, 0x64fdb9, 0x638d6f, 0x638e76, 0x638efb) touch no TruMenu check either.

**Quick command line (L3 in the open bar).**
- Suggestions: while a typed line has some, the menu bar's list (`CmdBuildSuggestions` + the shared `CmdSugRows`) is
  shown under the input (6 rows: id / value / label). Keyboard: Up / Down choose among them (else the history), Tab takes
  the selected (else the first), Enter on a selected one runs it - the menu bar's rules.
- On-screen keyboard: **Y** opens the 0.7 keyboard of the long menu - the same code, now with a target (`OskTarget`: the
  menu bar `g_oskMenu` or this line `g_oskQc`; `DrawOsk` / `OskInput` draw and steer whichever). Keys as in the menu: A
  type, X backspace, Y take suggestion, Start run, B back to the compact line (B again closes it), LB / RB rows, L3
  closes the line; an empty line starts on the history chips. While it is open the bar also keeps **Start** from the
  game (`kQcOskOwn`; in `QbPad` it is never a gated combo tap, so its release is not passed to the game). A real key
  switches back to typing (the characters are kept).
- Safety: the line a pad step put into the input is shown with its item label (`A fuehrt aus: cheat.god 0 - ...`) and,
  for a line of `kCmdDanger`, an orange "Vorsicht: ..." before anything runs. A pad run (A, the keyboard's Start / run
  key) of such a line only **arms**: red footer `ACHTUNG: <line> (<why>) - A nochmal in 2.4 s = ausfuehren`; the same line
  again within 3 s (`kQcArmMs`) runs it, any edit / history step disarms. Enter on the real keyboard runs at once (typed
  on purpose). `kCmdDanger` (one table): `cheat.*`, `player.invincible`, `player.die`, `level.load` / `start` / `reload`,
  `unit.go`, `pos.goload`, `regress.prepare`, `save.load` / `delete` / `restore` / `import`, `costume.reset` /
  `choosereset` / `setreload` / `choosereload`, `sw.set`, `sticky.set`, `fix.hall02`, `ai.kill`, `ai.remove`,
  `instance.remove`, `settings.reset`, `fav.reset`, `game.quit`. Reads never ask: `help` / `list` / `get`, info items,
  a value item without an argument (shows its value). Log `quick: '<line>' <why> - armed ...`.

**Favourites with an argument + star.** `[Favorites] Ids` entries are `<id>` or `<id>|<argument>` (argument without ',' /
'|', < 96 characters); old lists (comma or space separated) read as before, a TruMenu before 0.21.8 skips the new
entries. Y now pins rows with an argument: static rows (e.g. `dbg.flatpass 0x200`), page Fixes switches
(`sw.set|<Plugin>:<Section>:<Key>` - on page 0 the switch row itself with its value, right / left / X as on Fixes),
costume list rows (`costume.set|<id>`), chapter units (`level.load|<unit>` - on page 0 with the chapter rows' right-twice
+ backup). Group / chooser / position / checkpoint / save rows still refuse Y. A row whose item + argument is a
favourite shows a yellow ` *` (every page). `fav.add` / `fav.del` take `<id> <argument>` (or `<id>|<argument>`); the
long menu's favourites page lists them (switches as their widget, others as a button; Y unpins), page Fixes: Y on a
switch pins it. A list that would not fit (1023 characters) is refused unchanged.

**Story values** (`story.values`, info; bar page Leveldaten "Story-Werte (nur lesen)" and Tests / hall02 group
"hall02-Werte (live)"): the known sticky values of Lara's level through the `sticky.get` read (`StFind` / `StValue`,
nothing written): hall02 dispatcher 11270 population / deaths / tutorial / wall (the `fix.hall02` keys), Croft Manor
dispatcher 4086 IsLevelZeroDone / IsL3_Reset_OK (Befund-Manor-Prolog row 4). `-` = no entry yet.

**Sound group sliders** (`docs\Befund-Ton-Gruppen-0611.md` sections 4 / 5; bar page Zeit / Test, group "Ton-Gruppen
(Lautstaerke)"; items `snd.group <Key> <0..100>`, `snd.groups`, `snd.vol.<key>`; `[SoundGroups] Ambience / Steps /
Weapons / Enemies / Lara / Objects / Dlc2 / Hud`, default 100, kept in TruMenu.ini): the eight proposed sliders (15; 32 +
78; 58 + 60 + 51 + 31; 27 + 65; 68 + 70 + 72 + 77; 43; 79; 54 .. 57). Game thread, next to the music mute: factor =
`*(float *)(cg + 0x38)` of the group's FMOD channel group, then FMOD's own recompute 0x7c4774; the game's group volume
(entry +0) is never written. A group whose ancestor (entry +0x68) is in the same slider is skipped (60 under 58); two
sliders on one path multiply. New channel groups after a level load are written again; 100 % puts the value from before
TruMenu back. Open (finding section 6): whether the factor is audible, whether the game writes cg + 0x38 itself.

Not built: Arachno 0.22 (occlusion = picture quads in the depth path with their own render-state patch condition, glitch
effects - `docs\Befund-Arachnophobie-Stufe1-Kamera-0611.md` 0.22-A / B; too large for this night and not testable
offline), the front-end pad block (research only until the 0.21.7 diagnosis lines were seen live).

Checks: `tools\trumenu_ini_check.py` `check_0218` (36 negatives `work\m0218_0711\make_negative.py`; the 0.21.7
negatives adapted in `make_negative_0217.py`), `tools\trumenu_quick_check.py` models `qcdanger`, `qcarm`, `favargs`,
`sgcover`, `qcsuggest`; byte lists `work\asi\menu0218\precheck_0218_sndgroups.txt` (6) and `precheck_0218_aikill.txt`
(62, the 0.21.1 list with the moved row).

### TO TEST 0.21.8 (owner)

| # | Step | Expected |
|---|---|---|
| 1 | game start | `TruMenu.log`: `TruMenu 0.21.8 (`, `0.21.1 ... checks ok`, `0.21.8 sound group sliders: checks ok (6 rows)`, `SweepAndPrune read-out: checks ok (20 rows, N in the TruRockVein 0.10 form)` (N = 0 while TruMenu.asi loads before TruRockVein.asi, as today; 2 if it ever loads after); with TruRockVein 0.10 on, `sap.status` ends "Grenzen TU 3000/1000 (TruRockVein 0.10)" |
| 2 | bar open, L3, type `cheat.g` | suggestions under the input (`cheat.god`, `cheat.godfull` with values); Down + Enter runs the selected one |
| 3 | D-pad up until `cheat.god 0` shows | blue `A fuehrt aus: cheat.god 0 - ...`, orange `Vorsicht: aendert einen Cheat ...` |
| 4 | A once | nothing runs; red `ACHTUNG: cheat.god 0 ... A nochmal in 3.0 s`; log `quick: 'cheat.god 0' ... armed` |
| 5 | A again within 3 s / after 3 s | runs (`cmd (quick): cheat.god 0`) / arms again |
| 6 | `get cheat.god` from the history, A | runs at once (a read) |
| 7 | Y in the open line | the menu's keyboard under the line; A types, X deletes, Start runs, B back, B again closes; Start does not pause the game |
| 8 | page Fixes, a switch, Y | `als Favorit angeheftet (Seite 1)`; ` *` after the name; page 0 shows the switch with its value, right / left / X switch it |
| 9 | page Kostueme list row / page Kapitel unit, Y | pinned with ` *`; on page 0 the unit row asks right twice + backup |
| 10 | TruMenu.ini `[Favorites] Ids` | `...,sw.set|TruShadowCombat:Death:TranslateNotify33,...` style entries |
| 11 | hall02, Leveldaten "Story-Werte (nur lesen)" | `Bev 1, Tote 0, Tutorial 1, Wand 0` (live values; kill a thrall: Tote / Bev change) |
| 12 | Zeit / Test, "Ton-Gruppen": Umgebung left to 0 near a waterfall / wind | ambience goes, footsteps stay; log `snd.group Ambience: group 15 factor 0.00 ...`; back to 100 = `back to 1.00` |
| 13 | Sonstiges (HUD) 0, then Lara-Stimme 0 | HUD / menu sounds off; Lara's breathing / hints off - note anything that stays (finding section 6) |
| 14 | level load with a slider below 100 | `new (level load) group ...` lines; the factor holds |

## TruMenu 0.21.9 (test spots, DLC units in play order with checkpoints, units without a DRM, goo / navmesh labels with meaning, B7, F11; 2026-11-08)

Night build `work\asi\menu0219` from the gap list `docs\Befund-17i-Menue-Luecken-0811.md` (data
`work\menu17i_0811\dlc_intros_all.txt`) and `docs\Befund-R17e-Goo-Navmesh-0811.md`. No new byte check (no new code
address is read: the goo label uses the 0.21.7 uber read path, the navmesh labels the bits of the area words they already
read), no hook, imports / exports unchanged, `TruMenu.ini` unchanged (= the 0.21.8 sample).

**`cp.jump <unit> <checkpoint intro>`** (new action item, not on the game thread): one shortcut of the 0.8.1 runner -
`save.backup kapitel;unit.go <unit>;wait.unit <unit>;dbg.cpgo <id>`. `unit.go` decides when its step comes (Lara in the
unit: nothing; loaded with a stream portal: flight + portal; else `level.load`); `dbg.cpgo <id>` as a shortcut step now
runs its two steps in place (`cheat.flight 1;player.goto <id>`, `ShortcutTick`) instead of starting a second shortcut over
the running one (`dbg.cpgo active` stays a command). Refused: a unit not in the level list, a unit without a DRM, a
pending level change. In `kCmdDanger` (the quick command line asks twice).

**Page Tests: test spots** (group "Teststellen (rechts 2x)"): "End-Szene (020_ghoul)" = `cp.jump dlc_yggdrasil_end 9608`
(help: CP 9608 lies most likely inside trigger volume 10026 - the cutscene 020_ghoul starts at once), "Boden 25057 (CP
9970)" = `cp.jump dlc_yggdrasil_end 9970` (the nearest data checkpoint, ~1300 units from the floor spot), "Zeremonienraum
030_pod" = `level.load dlc2_ceremony_room` with backup. Not in the tour file: `trumenu_ini_check.py` counts 256 of 256
ring entries with the built-ins (`kRadMaxItems`), new tour entries would be dropped - and the ring is frozen since 0.21.5.

**Units without a DRM** (17i: `dlc_level1_left` / `dlc_level1_right` are in unitlist.txt, also on the Xbox, but no DRM
exists): at start every DLC 1 / DLC 2 unit of the level list is checked once against `<tru.exe folder>\mods\<unit>.drm`
(log `0.21.9 units: 23 DLC 1 / DLC 2 units checked ..., 2 without a .drm: dlc_level1_left, dlc_level1_right`). Such a
unit is grey "keine .drm / nicht ladbar" on page Kapitel and in the long menu's level list, its command-line value says
"no .drm in mods", Y does not pin it, and `level.load` refuses it (`LoadUnit`). Base-game units (bigfile) and the other
DLC starts are never marked (0.21.10: the other DLC starts are marked too - section "TruMenu 0.21.10").

**Page Kapitel: DLC 1 / DLC 2 in play order with checkpoints** (`kChapOrder`, every id from `dlc_intros_all.txt`,
objects 83 `checkpoint` / 1036 `dlc2_checkpoint`, ordered by their +0x52 index): DLC 2 level2_start (4 CP) -> hall01 (1)
-> hall02 (3) -> end (4) -> ceremony_room (9) -> "-- Rundweg (Richtung nicht in den Daten)": machine_ceremony (7) /
machine_room (18) / goo_machine (3) / goo_room (10) / ceremony_goo (5), each "(Rundweg)" -> treasure_room_cine; DLC 1
level1_start (1) -> caverns (3) -> caverns_hall (1) -> water_wheel (3) -> pillory (6) -> dungeonhalla (3) / dungeonhallb
(3) -> watertunnel (1) -> dungeon (7) -> treasureroom, then the two units without a DRM. A unit row shows `[+] 4 CP`;
**left** opens its checkpoint rows (one unit at a time, "rechts 2x, links: CP"), a checkpoint row "CP 9608" runs `cp.jump
<unit> <id>` on right twice (end / 9608 says "020_ghoul sofort"). Right on the unit row = backup + `level.load` as
before. Page rows with the biggest unit open: at most 50 of 64.

**Goo drip label** (`dbg.uber`, `uber.dump`; only objects 926 `dlc2_uo_goo_drips` / 937 `_sml` and only when the live
graph has 8 nodes with node 3 "goo_off" - DTP 24411 / 24872): `goo: leicht, naechster Tropfen 0.3 s` (easy: drop on
entering node 4, every 0.7 s), `goo: leicht (Startpause), naechster Tropfen 2.1 s` (node 7, 4 s), `goo: hart (ohne
Ausgang), naechster Tropfen 0.2 s` (nodes 1 / 2: drops at 0.3 / 0.6 s; no command leaves hard), `goo: ..., Tropfen
jetzt` (the auto nodes 0 / 5), `goo: aus (Befehl 0 = hart / 1 = leicht)` (goo_off), `goo: ein Tropfen, dann aus`
(spawn_one). Rest = `[trans+0x1c] - [b+0x88]` of the node's timed transition (condition 1), as the 0.21.7 gate label.

**Navmesh labels / legend with meaning** (`nav.labels`; ENGINE.md section 15): line 1 `E<layer>.<graph> #<area> <unit>
Insel <n|->` (+0x30 bits 7..16, 0x3ff = none), line 2 `gesperrt (Hindernis) custom (handgebaut) | Strafe x3 / fest x1 | 5
Kanten | 27:1 26:1` (bit 27 = blocked by an obstacle, runtime; bit 26 = custom, else `auto`; +0x34 bits 8..11 obstacle /
12..15 static penalty multiplier, shown when one is above 1). The legend wraps into rows that fit the screen: "rot Bit 27 =
von Hindernis gesperrt (Laufzeit)", "orange ... = Hindernis-Strafe", "gelb ... = feste Strafe", "blau Bit 26 verschieden
(custom / auto)", "magenta Bit 26 = custom (handgebaut)", plus the hint row "lila / violette Flaeche ohne Etikett = wohl
dbg.enemycoll (Gegner-Kollision), kein Navmesh" (r17e 2b, still to be confirmed live).

**B7: the TO TEST switch note** (`test.toggle <id> ini:<Plugin>:<Section>:<Key>` and toggling it): instead of "INI: takes
effect at the next start" the note names the switch's "when" column of `TruMenu.switches.txt` (`SwWhenNote`): "INI: live
(~1 s, TruMenu.switches.txt)", "INI: after a restart (...)", "INI: live while <Key>=1 (now 0), else after a restart
(...)", or "not in TruMenu.switches.txt - when it takes effect is unknown". No new switches row.

**F11**: the bar's default key line ends with `F11: Foto + Marke` while `[Shot] Enabled=1` and a `[Shot] Hotkey` is set
(0x7A in the installed INI; another key shows as `F<n>` / `0x..`), and the shot rows (page Lara "Foto mit UI" / "Foto
sauber", the shot rows of the other pages) have the help "Foto jetzt; Taste F11 ([Shot] Hotkey) = Marke + Foto".

**`Set-TruMenu.ps1 -ShaderLabelFile <path>`** (Install only): installs that file as `TruMenu.shaderlabel.txt` instead of
the build folder's one (e.g. `work\shader17c_0811\trumenu\<variant>\TruMenu.shaderlabel.txt`); the first line must be
`# shaderlabel v1`, checked before anything is copied. Without it nothing changes. `$earlierBuilds` now knows the 0.21.7
/ 0.21.8 builds and sample INIs (the installed 0.21.7 asi would otherwise be "not a build of ours"). `work\asi\menu0219`
holds no shader label file - pick a variant with the parameter (or the old one stays installed).

Checks: `tools\trumenu_ini_check.py` green (check_0218 now reads its part of the version line, as check_0217);
`work\asi\menu0219\check_0219.py` (CP ids = data, play order, test spots, the DRM list against the game's mods, the goo
graph against the r17e dumps, a ShortcutTick model of cp.jump, source rules) with 10 negatives
(`make_negative_0219.py`); `tools\trumenu_quick_check.py` all ok.

### TO TEST 0.21.9 (owner)

Install: `.\scripts\windows\Set-TruMenu.ps1 -Install -SourceDir .\work\asi\menu0219 -ShaderLabelFile
.\work\shader17c_0811\trumenu\<variant>\TruMenu.shaderlabel.txt` (game closed).

| # | Step | Expected |
|---|---|---|
| 1 | game start | `TruMenu.log`: `TruMenu 0.21.9 (`, `0.21.9 units: 23 DLC 1 / DLC 2 units checked ..., 2 without a .drm: dlc_level1_left, dlc_level1_right` |
| 2 | bar, page Kapitel, group "Abschnitte DLC 1 ..." | play order level1_start .. treasureroom; `dlc_level1_left` / `_right` last, grey "keine .drm", right = "keine .drm in mods - nicht ladbar"; `menu level.load dlc_level1_left` = "refused: ... no .drm in mods" |
| 3 | group "Abschnitte DLC 2 ...", left on `dlc_yggdrasil_end  [+] 4 CP` | rows CP 10036 / 9953 / 9970 / 9608 below it; CP 9608 "020_ghoul sofort"; the ring units under "-- Rundweg" with "(Rundweg)" |
| 4 | CP 9970: right, right | backup, then (not in end) level.load or portal, Lara flies to CP 9970; log `shortcut 'CP 9970 (dlc_yggdrasil_end)' ... dbg.cpgo -> cheat.flight 1;player.goto 9970` |
| 5 | page Tests, "End-Szene (020_ghoul)" right twice | help line "CP 9608 liegt wohl im Trigger 10026 ..."; Lara at CP 9608, 020_ghoul starts at once (note whether it does) |
| 6 | page Tests, "Boden 25057 (CP 9970)" / "Zeremonienraum 030_pod" | Lara at CP 9970 (floor 25057 ~1300 units away) / ceremony room loads after a backup (does 030_pod play?) |
| 7 | end room, Leveldaten "Tore / Plattformen (Zustand)" on, near the light columns | goo drips: `goo: leicht, naechster Tropfen 0.x s` counting down (or `goo: aus (Befehl 0 = hart / 1 = leicht)` as on 07.11.); note every change while the fight runs |
| 8 | hall02 / DLC 1 caverns, "Navmesh Flaechen" + "Alle Ebenen" + "Navmesh beschriften" | legend in rows with the meanings and the violet hint; labels `... Insel n`, `custom (handgebaut)` (DLC 1 caverns) / `auto`; then toggle `dbg.enemycoll`: does the violet ramp go away? |
| 9 | `menu test.toggle x ini:TruShadowCombat:Death:TranslateT5 x` (any live row of page Fixes) | TO TEST row note "INI: live (~1 s, TruMenu.switches.txt)" instead of "takes effect at the next start"; a restart row says "after a restart" |
| 10 | bar open on a row without its own key line; page Lara "Foto sauber" | key line ends with `F11: Foto + Marke`; help line "Foto jetzt; Taste F11 ..."; F11 = a Claude mark + clean shot as before |
| 11 | shader labels in end (Render-Details "Shader-Etiketten") | labels from the variant given to `-ShaderLabelFile` (compare a `shader.dump` block with the variant's notes) |

## TruMenu 0.21.10 (unused DLC slots 3 - 6 and left / right: proven without data, grey, refused with the engine's reaction; 2026-11-08)

Build `work\asi\menu0220` from package 17s (`work\units17s_0811\PROGRESS.md`; 17p Q4 `work\q17p_0811\PROGRESS.md`). No new
hook, no new byte check (the start-up scan is file tests only), imports / exports = 0.21.9, `TruMenu.ini` unchanged (=
the 0.21.8 sample).

**Why these six are grey.** `dlc_level3_start` .. `dlc_level6_start` and `dlc_level1_left` / `_right` have **no data
anywhere**: no archive index holds them (PC bigfile / patch, Xbox layer1 / layer2 / TU, packs 10 / 11 / 1 / 2 / 20; 6
units x 8 path forms x 4 prefixes by name hash, with positive controls `l1_seatop`, `dlc_level1_start` /
`dlc_level2_start`, `dlc_levelN_preview.raw`), and a plain search through every record (25.2 GB decoded) plus the
installed mods tree, the B270 kit, tru.exe and the Xbox exe images finds the names only in generalbank (scripts 6 / 104),
`objlist.dat`, `unitlist.txt`, the kit manifest (preview image names) and the TU exe. Every unit DRM names itself (2 - 10
times), so a renamed copy would have been found. The retail mission screen (generalbank script 104) only adds a slot when
`dlcsystem` f1 finds `dlc_levelN_start.drm` (function 7, `uimenu` f25), so slots 3 - 6 never appear; their data in the
game are placeholders only: names 452 - 455 "DLC Mission 3" .. "6", descriptions 458 - 461 "Unavailable", preview
images `image\dlc_level3_preview.raw` .. `6` = 64 x 36 "M 3" .. "M 6" (Xbox 64 x 64), error text 464 "ERROR : Cannot find
selected DLC level pack." (DE "FEHLER: Das ausgewählte herunterladbare Level Pack konnte nicht gefunden werden.").

**What the engine would do on a load (static, tru.exe, 17s task 2).** `level.load` (`GAMELOOP_RequestLevelChangeByName`
0x5df8c0) and the mission start (`uigamedata` f27 0x77e170 -> 0x5dfb20) both end in 0x5dded0 -> `STREAM_LevelLoadAndInit`
0x5d30d0 -> `STREAM_LoadLevel` 0x5d23f0, which builds `pc-w\<unit>.drm` (0x477970, `%s%s.drm`) and requests it (0x551470)
**without an exists test** (only `STREAM_LoadOverlayUnit` 0x5d2610 has one). The file system (MultiFS, vtable 0x8440ec)
sends a name no archive has to its slot 0 (`GetFS` 0x473560: miss -> index 0; the patch archive is mounted at the front,
0x478997), whose `RequestRead` 0x472890 finds nothing (lookup 0x4726e0 -> 0) and calls the fatal-error path 0x596cb0
with **"Can't open file pc-w\<unit>.drm"** -> 0x478b00: window hidden in full screen, the game's error dialog
(`DialogBoxParamW`, template 0x7d) -> 0x478a10: `ExitProcess(0)` (main thread) / `TerminateProcess` (other threads).
So: no fallback to the menu, no hang, no crash dump - an error box, then the game is gone (unsaved progress lost).
ModLoader's own file system layer is not read (it hooks 0x472c50 / 0x472b31 / 0x478930 / 0x49a84f by signature); if it
answered a miss itself the message could differ (🔶). No safe load path exists, so nothing is offered behind a
confirmation.

**Changes.**
- `kUnitsNoData` (the six) and `UnitUnused` (one of the six **and** no `mods\<unit>.drm` - a file built later would load).
  `UnitDrmChecked` also file-tests the group "DLC other starts" (dlc_level3..6_start), so the start-up line is now
  `0.21.10 units: 27 DLC units (DLC 1 / DLC 2 / slots 3 - 6) checked against ...mods\<unit>.drm, 6 without a .drm:
  dlc_level1_left, dlc_level1_right, dlc_level3_start, dlc_level4_start, dlc_level5_start, dlc_level6_start, 6 of them
  unused slots without data (17p / 17s; grey, level.load / level.start refuse them)`.
- **Page Kapitel**: the last group is now "Ungenutzte DLC-Plaetze 3 - 6 + left / right" ("Unused DLC slots 3 - 6 + left /
  right", head column "keine Daten (17p/17s)") with six grey rows `dlc_level3_start` .. `dlc_level6_start`,
  `dlc_level1_left`, `dlc_level1_right` - state "ungenutzt", column "keine Daten (17p/17s)"; left / right stay at the end
  of the DLC 1 group with the same text. Help line (the footer's third line): "In keinem Archiv (17s); Laden:
  Fehlerfenster + Spielende" / "In no archive (17s); a load: error box + the game exits"; key line "ungenutzt - keine
  Daten (17p/17s), nicht ladbar"; right / X answers "ungenutzt - in keinem Archiv und nicht in mods (17p/17s); Laden =
  Fehlerfenster "Can't open file" + Spielende - nicht angeboten". Y does not pin them (0.21.9 rule).
- Long menu level list: the six are grey "(ungenutzt - keine Daten / unused - no data, 17p/17s)" with a tooltip naming the
  error box; command-line value "unused slot - no data (17s)".
- `level.load` and now also **`level.start`** refuse a unit without a DRM; for the six the answer is `refused:
  dlc_level3_start is an unused slot - no data in any archive or in mods (17p / 17s); the engine would stop with "Can't
  open file pc-w\dlc_level3_start.drm" (error box, then the game exits)`.
- Comment at `MissionSelectArg`: the TU exe's yes / no dialog accept path (`ScriptDialogYesNo::RegisterAcceptChanges`,
  0x8247f3b8 .. 0x8247f510, "Attempting to load level: %s") skips the outfit selection for `dlc_level2_start` ..
  `dlc_level6_start` (level 3 included, table 0x820760f8); not copied (no data for 3, the PC exe has no such strings).
- `Set-TruMenu.ps1`: `$earlierBuilds` knows the 0.21.9 asi (sha256 cf4f3871...), example `-SourceDir .\work\asi\menu0220`.

Checks: `tools\trumenu_ini_check.py` green (exit 0), `tools\trumenu_quick_check.py` all ok, `work\asi\menu0219\check_0219.py`
all ok (its version test now reads the 0.21.9 part), `work\asi\menu0220\check_0220.py` all ok (proof files, the table, the
mods tree, the exe bytes of the load / error chain, source rules) with 11 / 11 negatives caught
(`make_negative_0220.py`).

### TO TEST 0.21.10 (owner)

Install: `.\scripts\windows\Set-TruMenu.ps1 -Install -SourceDir .\work\asi\menu0220` (game closed; add `-ShaderLabelFile`
as for 0.21.9 if wanted).

| # | Step | Expected |
|---|---|---|
| 1 | game start | `TruMenu.log`: `TruMenu 0.21.10 (`, `0.21.10 units: 27 DLC units ... 6 without a .drm: dlc_level1_left, dlc_level1_right, dlc_level3_start, ... 6 of them unused slots` |
| 2 | bar, page Kapitel, last group "Ungenutzte DLC-Plaetze 3 - 6 + left / right" | 6 grey rows "ungenutzt" / "keine Daten (17p/17s)"; help line "In keinem Archiv (17s); Laden: Fehlerfenster + Spielende"; right = the refusal text, nothing loads |
| 3 | group "Abschnitte DLC 1", last two rows | `dlc_level1_left` / `_right` grey with the same texts |
| 4 | `menu level.load dlc_level4_start`, `menu level.start dlc_level5_start` (main menu) | both `refused: ... unused slot ... "Can't open file pc-w\..."`; the game keeps running |
| 5 | long menu, Levels, group "DLC other starts" | the four grey with "(ungenutzt - keine Daten ...)" and the tooltip |
| 6 | DLC mission menu (retail screen) | only "UNTER DER ASCHE" and "LARAS SCHATTEN" listed (slots 3 - 6 are never added) |

Not to test: a real load of one of the six - it would end the game (see above). If the owner wants the engine's reaction
seen once: a throw-away session, windowed (TRAWindowed), save backed up, TruTrace on (it logs `STREAM_LevelLoadAndInit`
0x5d30d0 before the box), cdb with breakpoints on 0x596cb0 (log the format + name) and 0x478a10; load through the 0.21.8
asi (no refusal) or `GAMELOOP_RequestLevelChangeByName` from cdb. Expected: the box "Can't open file pc-w\dlc_level3_start.drm"
(note its title / buttons), then the process ends with exit code 0.

## Switches data 2026-11-08: group "Komfort (TruQoL)" (TruMenu binary unchanged 0.21.10; `work\asi\menu0221`)

Data only: `TruMenu.switches.txt` gets the group `truqol` "Komfort (TruQoL)" / "Comfort (TruQoL)" with the 10 keys of
the player plugin TruQoL 0.1.1 - live: `[TruQoL] LogLevel`, `[FrameLimit] Enabled` / `MaxFps` (choice 30 .. 144) /
`AutoOff` / `SpinUs`, `[Camera] Fov` (choice `0,0.9,1.0,1.1,1.15,1.2,1.3`) / `FovCutscenes` / `ShakeScale` (choice
`0,0.25,0.5,0.75,1.0`); restart: `[TruQoL] Enabled`, `[Startup] ThreadCap`. Float keys are `choice:` rows of exact INI
texts - `SwChoiceHas` compares text, so `1.0` is a value of its own (an INI holding `1` shows `1`; right / X then goes
to the first choice, left to the last). No code change: the parser takes any `Tru<name>` plugin with an INI next to tru.exe; now 135
switches in 10 groups (limits 160 / 24), page Fixes at most 37 rows (`kQbViewMax` 64); the ring stays frozen.
`tools\trumenu_ini_check.py` knows TruQoL (`SW_PLUGINS`, `SW_LIVE` -> `LiveReadOptions`) and accepts a dot in choice
values. `work\asi\menu0221` = the menu0220 files + the new switches file; checks `work\qol17y_0811\check_0221.py`
(+ 14 negatives). TruQoL's `[Camera] ShakeScale` below 1.0 makes TruMenu's own `cam.shakescale` refuse ("another
plugin?"); back at 1.0 TruQoL gives the two calls back - move TruMenu's slider once more to retry.

TO TEST (owner, with TruQoL 0.1.1 installed): page Fixes, group "Komfort (TruQoL)": `MaxFps` 60 -> 30 and back, `Fov`
1.2, `ShakeScale` 0.5 -> 1.0 - each takes effect within about a second (`TruQoL.log` one `live:` line each); the rows
`TruQoL an` / `Start-Fix ...` show "Neustart". Without TruQoL installed the group shows "keine INI" and writes nothing.

## TruMenu 0.21.11 (light.list / light.shadow for the flashlight shadow; page Rettung for players; 2026-11-08)

Build `work\asi\menu0222` from package 18d (`work\menu18d_0811\PROGRESS.md`, `finding_18d.md`; facts of 18b
`work\research18b_0811\finding_18b.md`, ENGINE.md section 16 "Shadow caster gate"). No new hook, imports / exports =
0.21.10, `TruMenu.ini` unchanged (= the 0.21.8 sample), ring untouched (`kRadMaxItems` 256 frozen, radial / tour files
unchanged). `TruMenu.switches.txt` = the source file at build time.

**Lights (section "0.21.11 lights").** The scene light list is proven statically (tru.exe 5560abac): `[0xa1407c]` = the
PCRenderDevice (vtable 0x8492cc), scene = device + 0xfdfc, every PCRenderLight sits in the array count `[scene+0x14]` /
data `[scene+0x1c]` from its ctor (0x50b120 -> push_back 0x5054f0) to its dtor (0x50b1e0 -> remove 0x504a10). 18b's
"scene+0x20, count +0x1020" is the per-frame list of light **instances** (`[E]` = the light, E+0x64 / +0x65 run-time
flags; reset to 0 by 0x504c50, so outside the device frame it may be empty). 18b's "device" `[L+0x1c]` is the light's
**PCLightResource** (vtable 0x8494ec): CastsShadow 0x50a080 = `(L+0xc5 & 4) && res+0x1878`, and RenderShadowMaps'
`vf1c()+0x144d` is res+0x1879 (res vf+0x1c 0x50a030 = res+0x42c). Before the first read TruMenu checks 13 byte patterns
and 4 vtable slots (`LtCheck`; a mismatch = "disabled: bytes differ at ...").
- **`light.list`** (action, game thread, read only): one `TruMenu.log` line per light - `light.list #3 0x0a1b2c40 type 1
  +0xc5 0x05 (bit 2 1) +0xc4 0 | res 0x0c3d4e00 +0x42c 1 +0x1878 1 +0x1879 (vf1c+0x144d) 0 -> CastsShadow 1 | frame E
  0x... +0x64 1 +0x65 1 | pos 120.0 -40.5 310.0 (Lara 85u) NEW` - plus a head line (count, frame list count, +0x1240 list
  count, EnableShadows `[[0xad75e4]+0x184]`). The answer is short: `#3 t1 s1 85u NEW; ... | 12 lights, 3 cast (s1), 1 NEW,
  frame 0, EnableShadows 1`. **NEW** = not in the previous `light.list`: list with the flashlight off, switch it on, list
  again - the NEW light near Lara is the flashlight. Position = row 3 of the light transform L+0x20 (L+0x50, 🔶 live).
- **`light.shadow <n|0x<light>> 0|1`** (action, game thread): SetCastShadows vf+0x4c 0x50a3a0 of light `n` of
  `light.list` (or its address); refuses an index out of range, an address not in the array, a vtable other than
  PCRenderLight 0x849594 and any value but 0 / 1; logs +0xc5 and CastsShadow before / after and says when res+0x1878 = 0
  keeps the light unshadowed anyway.
- What the result means (18b): bit 2 clear on the flashlight -> data / setter; bit 2 set and res+0x1878 = 0 -> the light
  resource (res+0x42c kind 0 clears +0x1878 in 0x50afb0); both set -> slice / budget (0x504f30, <= 16 slices) or
  EnableShadows 0 (then only the first light with res+0x1879 is shadowed).
- Bar page Render-Details, group "Lichter (Schatten)": "Lichter ins Log" (`light.list`), "Licht-Schatten ..." (opens the
  quick command line with `light.shadow `).

**Page Rettung / Rescue** (bar page 1, right after Favoriten / Zuletzt; long menu: section "Quick bar pages"): the
existing soft-lock helpers of finding 18b part D in one place, every row an item of 0.21.10 - no new game logic.

| Group | Row (DE / EN) | Item | Note |
|---|---|---|---|
| Festgesteckt / Stuck | Befreien / Unstuck | `player.unstuck` | |
| | Befreien (Marke) / Unstuck (mark) | `player.unstuck mark` | |
| | Befreien: Stand / Safe ground state | `player.safeground` | info |
| | Punkt merken / Mark here | `player.mark` | |
| | Zum Punkt / Back to mark | `player.recall` | |
| | Unit neu laden / Reload unit | `level.reload` | right / X twice (kQfConfirm; kCmdDanger) |
| Spielstaende / Saves | Saves sichern / Back up saves | `save.backup rettung` | folder `<time>_rettung` |
| | Sicherungen (Liste) / Backups (list) | `save.backups` | info |
| | Sicherung zurueck ... / Restore a backup ... | `save.restore` | line; kCmdDanger + its own double confirm |
| Objekte / Objects | Objekte suchen ... / Find objects ... | `instance.list` | line (name filter) |
| | Objekt zu Lara ... / Bring object ... | `instance.bring` | line (#index / intro id) |
| | Objekt einblenden ... / Unhide object ... | `instance.unhide` | line |
| Ausruestung / Gear | Gegenstand geben ... / Give item ... | `gear.give` | line (object name) |
| | Medipack geben / Give medipack | `gear.give g_healthpack` | |
| | Waffe geben / Give weapon | `weapon.give` | choice (the five ring weapons) |
| | Munition voll / Ammo fill | `ammo.fill` | |

Rows marked "line" (new row flag `kQfLine`; the label ends in "...") need a typed argument: right / X puts `<item> ` into
the quick command line and opens it (type the argument, A runs it through `CmdExecute` - `kCmdDanger` asks twice for
`save.restore` / `level.reload` as for every line); in the long menu the button puts the line into the command bar and
focuses it. Y refuses them (a favourite without its argument would only answer "usage"). Every row has a help line
(`kQbHelp`, DE / EN <= 60 characters each).
Limits: 17 bar pages now (`g_qbRow[17]`, `static_assert(kQbPageN <= 17)`; was 16 - full), `kQbStartPage` 6 = still
Leveldaten; page Rettung 20 rows, Render-Details 43 (`kQbViewMax` 64); `tools\trumenu_ini_check.py` (`QB_PAGES_MAX` 17,
`kQbRescue` in `QB_TABLES`) and `tools\trumenu_quick_check.py` (cosbar: 17 pages) follow the new limit.

`Set-TruMenu.ps1`: `$earlierBuilds` knows the 0.21.10 asi (sha256 148066e8...), example `-SourceDir .\work\asi\menu0222`.

Checks: build 0 warnings (/W4, TruMenu.cpp; the 2 C4100 of imgui_demo as before), `tools\trumenu_ini_check.py` exit 0,
`tools\trumenu_quick_check.py` all ok, `work\menu18d_0811\check_0222.py` all ok (exe proof + LtCheck patterns / slots
against the exe, light rules, page Rettung, ring, source, folder) with 22 / 22 negatives caught (`make_negative_0222.py`);
`work\asi\menu0220\check_0220.py` / `menu0219\check_0219.py` all ok (0220's version test and its negative now read the
0.21.10 part).

### TO TEST 0.21.11 (owner)

Install: `.\scripts\windows\Set-TruMenu.ps1 -Install -SourceDir .\work\asi\menu0222` (game closed; add `-ShaderLabelFile`
as for 0.21.9 if wanted).

| # | Step | Expected |
|---|---|---|
| 1 | game start | `TruMenu.log`: `TruMenu 0.21.11 (` |
| 2 | in a level, flashlight OFF: `menu light.list` (or bar Render-Details "Lichter ins Log") | answer `... N lights, S cast (s1) ...`; per light a `light.list #i ...` line; no "disabled: bytes differ" |
| 3 | flashlight ON, `light.list` again | one (or more) light marked `NEW`, a few units from Lara (`(Lara <d>u)`); note its line: +0xc5 bit 2, res+0x1878, +0x1879, CastsShadow, frame flags |
| 4 | `menu light.shadow <n of the NEW light> 1` | `cast bit 1 (+0xc5 0x.. -> 0x..), CastsShadow x -> y`; does a flashlight shadow appear? (if "res+0x1878 is 0" - resource side, note it) |
| 5 | `light.shadow <n> 0`, then `light.shadow 999 1`, `light.shadow 0x12345678 1` | shadow gone again (if it came); refused: "index 999 out of range" / "not in the scene's light array" |
| 6 | bar: RB once from page 0 | page "Rettung" with the four groups; help line under each row |
| 7 | Rettung "Objekt zu Lara ..." right | quick command line opens with `instance.bring `; type `#<n>` from "Objekte suchen ...", A = object at Lara |
| 8 | Rettung "Unit neu laden" right once / twice | first: arms (footer), second within 3 s: reload |
| 9 | Rettung "Sicherung zurueck ..." | line `save.restore `; type a folder of "Sicherungen (Liste)"; A asks twice (kCmdDanger), then the restore's own confirmation |
| 10 | long menu, Quick bar pages, "Rettung / Rescue" | same rows; the "..." buttons fill the command bar |

## TruMenu 0.22 (cutscene pause: cine.pause / cine.step / cine.status; 2026-11-08)

Build `work\asi\menu0223` (TODO N12; facts: `docs\Befund-Szenenpause-0811.md` of the workspace, ENGINE.md section 3
"Cinematic stream clock"). Asked for to look at the flicker at the throne in the DLC 2 end cutscene: hold the cutscene
only, while the world goes on. `TruMenu.ini` unchanged, ring untouched, no new import.

**How (section "0.22 cutscene pause").** Every multiplex stream (a cutscene is one: animation and sound in one stream
object) is advanced once per frame by a list walk: head `[0xccdc64]`, update 0x5901a0 (thiscall, float dt) returns the
next stream `[obj+0x14]`; the walk exists twice, its calls are 0x5904e3 / 0x5954f8. For a cutscene stream
(`[obj+0x77c]` = its cinematic handler, `[obj+0x18]` = 4 playing) the update reads the stream file, feeds the sound
ring (its sample counter is the cutscene clock), sets the cutscene time `[obj+0x384]`, plays the keys between the old
and the new time and runs the handler update. While `cine.pause` is on, the rel32 of both calls point to a gate that
skips the update of a playing cutscene stream only and returns its next pointer: cutscene time, actors and camera
stand still; world time, particles, shader time and lights run on; other streams (music, ambience) are untouched.
Patched on the game thread while the pause is on, put back when it is off; **off by itself** when the main state
`[0xe7ed60]` leaves 1 (a load). Before the first use 7 byte patterns are checked (a mismatch = "disabled: pre-check
failed"). Not used on purpose: the pause bit 0xe7f0b8 & 0x1000 (stops the instance updates, so the effects too) and
the capture mode 0xe7f0a4 & 4 (a fixed 1/30 s per frame, so double speed at 60 fps).

| Item | Kind | What |
|---|---|---|
| `cine.pause [0\|1]` | bool | hold / release a playing cutscene (no argument = toggle); needs a loaded level |
| `cine.step [n]` | action | let n frames (default 1, at most 600) of the held cutscene through |
| `cine.status` | info | the stream list: the cutscene stream (state, time, handler, sound), GameTracker cinematic `[0xe7f1c0]`, the pause |

Bar page **Tests**, group "Zwischensequenz": Szene anhalten (bool), Ein Bild weiter, Szenen-Strom (live). Log lines:
on / off, one "holds cutscene stream 0x... at time ..." per held stream, the held frames when it is released.

Open (live): what the sound does while held - the sound ring is not fed, so FMOD may play silence or repeat the ring;
whether the cinematic handler counts its own times that would jump on release.

### TO TEST 0.22

| # | Step | Expected |
|---|---|---|
| 1 | log after the first `cine.status` | `0.22 cine.pause: 7 checks ok` |
| 2 | in a level without a cutscene: `cine.status` | "no cutscene stream", a few streams (music / ambience) |
| 3 | DLC 2 end cutscene `020_ghoul` (bar Tests "End-Szene"), while it plays: `cine.pause 1` | picture of the scene stands, particles / lights move on; log "holds cutscene stream" |
| 4 | `cine.step` a few times, then `cine.step 30` | one frame / half a second of the scene each time |
| 5 | listen while held | note: silence or a repeating sound |
| 6 | `cine.pause 0` | the scene goes on from where it stood, sound in sync |
| 7 | held, then a load (level.load / checkpoint) | log "off by itself"; the load works |

Live 2026-11-08 (0.22, DLC 2 end-room cutscene at the throne): the pause works - the scene stands, torches and the
flicker go on, the stream is recognised (its handler = GameTracker cinematic). The sound looped: the stream's sound
ring is no longer fed and FMOD plays it again (fixed in 0.22.1). A TruLink `menu cine.pause` without an argument
flipped the pause (0.22.1: report only).

## TruMenu 0.22.1 (cutscene pause: sound held, badge, mark / pause at; 2026-11-08)

Build `work\asi\menu0224`, live wishes of the 0.22 test. `TruMenu.ini` unchanged, no new import.

- **Sound held with the picture.** The cutscene time is the sound position (the sample counter of the stream's DSP
  ring), so the sound must stop with it - else FMOD repeats the ring and on release the play cursor no longer matches
  the clock. The game's own "pause all sound" (0x587420 / 0x587460) pauses the master channel group:
  System_GetMasterChannelGroup 0x7b99b9 and ChannelGroup_SetPaused 0x7b9490 -> ChannelGroupI::setPaused 0x7c4875
  (flag +0x59, every child group and channel). While a cutscene is held TruMenu pauses the master group - only if it
  was not paused already, and it gives it back only if TruMenu paused it (the game's pause screen keeps its own).
  Music and ambience stand still with it.
- **Steps without drift.** `cine.step n` lets n game frames through with the sound running **muted**
  (ChannelGroupI::setMute 0x7c48cd, flag +0x58): the clock is the sound, so picture and sound move on together.
- **Badge** top centre while held: `||  Szene angehalten  <s> s  -  Ton angehalten` (EN with `quick.lang 1`); while
  stepping `> Bild weiter`. Seconds = `[obj+0x384]` / 30 (the cutscene time counts 1/30 s: dt x 30.0 `[0x8439b8]`,
  the sound path 0x5800d0 multiplies by the same constant).
- **`cine.mark`** remembers the playing cutscene's time (seconds); **`cine.pauseat [seconds|off]`** holds the next
  cutscene that reaches it (no argument = the mark) and stays armed over loads: mark, reload the checkpoint, the
  cutscene plays and stops at the same spot. No real rewind: the stream is read forward from disk, the cutscene fires
  one-shot events, and the clock is the sound.
- **`cine.pause` without an argument only reports** (the bar, the command bar and the menu always send 1 / 0).
- Byte checks: 4 more (`kCnSndChecks`); without them the picture pause still works and the badge says "Ton: Schleife".
- Bar page Tests, group "Zwischensequenz": + Stelle merken, Bei Marke anhalten.

Live 2026-11-08 (20:44 - 21:08): the first build released and paused the sound every 30 - 130 ms (unsigned tick
difference, fixed); the master group alone did not hold the cutscene line - the sound category groups form their own
tree (master: 12 plain channels, no child group). The final build pauses the master group and the root of every
category tree (log: "2 channel group(s) paused"): silence while held, the line goes on exactly where it stopped, in
sync. Steps and `cine.pauseat` not yet tried live.

## TruMenu 0.22.2 (light.frame: per-frame light capture; 2026-11-08)

Build `work\asi\menu0225`. `light.frame [n]` (default 60, at most 600): while it runs, the rel32 of the frame end call
0x5098ca (the reset 0x504c50 of the scene lists, ecx = scene) points to a gate that records this frame's lists before
the reset: light instances (pointers scene+0x20, count +0x1020; 0x80 bytes each), the light behind each instance
(0x100 bytes, only when new or changed), light resources (scene+0x1024, count +0x11a4, slot R+0x1d18) and the third
count +0x1228. After n frames the game thread writes `TruMenu.lightframe.txt` next to tru.exe and puts the call back;
the file ends with one `S` line per light: frames present, instance / light byte changes, `BLINK?` when it was missing
in frames or changed in more than a quarter of them. 3 byte checks. Bar page Tests: "Lichter mitschreiben (60 Bilder)".

Played 2026-11-08 21:30 (DLC 2 end cutscene held at the throne): 14 lights, all in every frame; 4 torch lights change
their colour every frame (flicker, wanted), the 3 shadow-casting cutscene lights run a 5-frame cycle (instance +0x60
1, 1, 1, 2, 3; +0x78 0 / 1.0); with global shadows off the throne stood still - the flicker is their shadow rendering.

## TruMenu 0.22.3 - 0.22.5 (light.stable: steady scene light order, on by default; 2026-11-08)

`light.stable 1|0` (no argument = report). 0.22.3 sorted the scene lights in the visible-entity list before the light
pass 0x56d5c0 - never needed (0 of 111 frames), flicker unchanged. 0.22.4 sorts the light pass's own collected list
(+0x250, count +0x258) by address right after the collection loop: the 6 bytes `mov ecx, [esi+0x250]` at 0x56d69a
become `jmp LsStub` + nop (the stub saves all registers, sorts, runs the instruction, jumps back to 0x56d6a0), written on
the game thread only while on and only over the expected bytes, put back when off. **Played:** the collected order of
the 15 scene lights changed in every frame (112 of 112); with the switch the brightness of the lit figures stood still
(spread 13.9 -> 0.0, off / on / off) - cause of the end-cutscene flicker proven (ENGINE.md 16). The five cycling states
are different light combinations (warm torch light vs. a cool front light on Natla); the sorted order keeps one of them.
**0.22.5: on by default** - `[Light] Stable=1` (missing key = 1), the owner prefers a steady light set to the flicker
until the real fix (a stable order by weight, or the right weights in the DLC light data, checked against Xenia / the
Xbox original). The sort applies in every scene; `Stable=0` gives the game's own order. Bar page Tests: "Licht-
Reihenfolge fest (Flacker-Test)".

## TruMenu 0.22.6 / 0.22.7 (Steam overlay guard, umlauts, cutscene keys; 2026-11-09)

- **0.22.6 Present re-entry guard** (crash of 2026-11-08 with the Steam overlay: TruMenu's swap-chain Present hook and
  the overlay's d3d9 detour called each other until the stack overflowed): per thread the device and the swap-chain
  Present hook note that they run; a nested call draws nothing and goes straight to d3d9 behind the overlay's `jmp`
  through a trampoline that rebuilds the 5 hot-patch bytes (`mov edi, edi; push ebp; mov ebp, esp`), built only when the
  original starts with E9 and a function body follows; otherwise the nested call returns D3D_OK. One log line.
  Not yet tested with the overlay.
- **0.22.6 umlauts:** the German texts show umlauts; `tools/trumenu_umlauts.py` wrote 251 words of a fixed list as octal
  UTF-8 escapes inside the string literals (the INI option table stays ASCII).
- **0.22.7 cutscene keys** in `[Cine]`: `PauseKey`, `StepKey`, `ShotKey` (keyboard, virtual key code, hex or decimal -
  0x78 F9, 0x79 F10) and `PausePad`, `StepPad`, `ShotPad` (XInput masks pressed together - 0x0100 LB, 0x0200 RB, 0x0020
  View, 0x0010 Start, 0x1000 A, 0x2000 B, 0x4000 X, 0x8000 Y; e.g. 0x0120 = View + LB). Pause toggles `cine.pause`, Step
  = `cine.step 1`, Shot = `claude.mark now` (mark line + clean shot). Edges only; the game still gets the keys and
  buttons; the pad combos act only while neither the menu nor the ring owns the pad. All 0 by default. To use the
  8BitDo's R4 / L4: map them in the pad's own software to such a combo (the pad sends no own XInput bit for them).
- **0.22.8:** the pad combos are on by default - `PausePad=0x0120` (View + LB), `StepPad=0x0220` (View + RB),
  `ShotPad=0x0320` (View + LB + RB). Pause acts only while a cutscene plays or is held (a stray combo in normal play
  cannot arm the pause for the next cutscene), step only while held. The pause badge shows a second line with the keys /
  combos as set now (e.g. `LB + View = weiter . RB + View = 1 Bild . LB + RB + View = Foto`), built from the INI values,
  so it follows any change.

## 0.22.63 - build S3 after the analysis S2 (2026-11-19)

Package S3 (`docs/Befund-S2-1911.md` in the workspace). Not installed.

- **(1) villa switches, corrects 0.22.62 (a):** S2 found vt 59 = switch base 3637 f7 acts only at +32 == +16 ("off");
  from "on" the static lever path is **vt 58** = f6 ("invoking OFF reaction", only at +32 == +20, then
  `modifiable.f4(+8)`). `puzzle.pull` from on now sends vt 58; `puzzle.pull <intro> lever|off|action` forces vt 59 /
  58 / 55 in either state for the live comparison. The check after 6 s as before (lever node, +32, bit 0x200,
  target); a "vt n from on / off changed nothing" line for every vt. Whether vt 58 moves the villa lever and what +32
  does then (vt 54 "off state" instead of the door?) is open.
- **(2) `bal.nofall`** "Balancieren ohne Fallen" (cheat, default off, not kept in the INI; page Figur "Sprung / Fall"):
  the beam helper's fall flag M+0x3bd (machine M = `[[0xfadb58]+0xf10]`, read by chart condition 512) is set to 1
  only at three `mov eax, 1` in the balance process (S2). After four byte checks (`0x742eea` / `0x742f16` /
  `0x742f3b`, reader `0x764c50`) the immediates at 0x742eeb / 0x742f17 / 0x742f3c become 00; off writes 01 back (only
  where 00 stands). Wobble, blend, timers and direction run as in the game. Without a hook "would have fallen" is not
  readable: while on, one line per balance stay (state 301) with the highest flag value (must be 0).

### TO TEST 0.22.63

| # | Where | Do | Expected |
|---|---|---|---|
| 1a | villa, 4617 | `Schalter betaetigen` (= vt 58 from on) | log `-> vt 58 (request the off reaction from on ...)`, check after 6 s: lever node / +32 / bit / door 4528 - report all four |
| 1b | same | TruLink `menu puzzle.pull 4617 lever` / `action` | vt 59: "changed nothing" expected (S2); vt 55: door opens, lever stays up |
| 2a | a beam | `bal.nofall 1`, balance, let the stick go / wobble hard | log `4 byte checks ok`, `bal.nofall 1`; Lara wobbles but does not fall; at the end `balance stay ... fall flag max 0` |
| 2b | same | `bal.nofall 0` | `ValBalNoFall` immediates 01 01 01; falling as in the game |

## 0.22.62 - fix build after the live test of 18.11. (2026-11-19)

Package S1 (live test 18.11.). Not installed.

- **(a) `puzzle.pull` with the lever also at the villa:** live 18.11. vt 59 (request the on reaction) at the chapel
  switch 4819 moved the lever and ran the action without Lara's animation; vt 55 at the villa switches 4617 / 4525
  (+32 = 0 = "on" before and after) opened the door but left the lever up and bit 0x200 at 0. Now vt 59 from off **and
  from on**; `puzzle.pull <intro> action` keeps the 0.22.59 direct action (vt 55, only from on) for a comparison. The
  check after (log) now also follows the switch's own node (the lever) and says when vt 59 from on changed nothing
  (ENGINE §9 reads vt 58 / 59 as acting only from on / off - the live test decides; no other path is tried by itself).
- **(b) Hinweise / Aktionen:** live 18.11. help level 1 hid the action rows and they were not found. The level
  `[Puzzle] Help` (0 / 1 / 2) is replaced by two switches: **`puzzle.hints`** (`[Puzzle] Hints`, default 1) and
  **`puzzle.actions`** (`[Puzzle] Actions`, default 1), two rows "Hinweise" / "Aktionen (Cheats)" at the top of
  "Raetsel in der Naehe" (right 2x = toggle). An INI without the two keys still reads `Help` (0 = both off, 1 = hints,
  2 = both); `puzzle.help 0|1|2` still sets both.
- **(c) bar rows** (live 18.11. they were reachable only through TruLink): page **Figur**, group "Sprung / Fall
  (Anzeige)": `fall.box`, `trace.arcs` (Lara's own motion); page **Kapitel**, group "Raetsel-Anzeigen" above the puzzle
  list: `puzzle.thor`, `puzzle.thorgap ...` (typed value); page **Debug / Darstellung**, group "Objekt-Daten (Log)":
  `obj.track ...` (typed `<id> on|off`) and `obj.track list` (a log diagnosis, no display). Page **Leveldaten**: new
  switch **`dbg.plates`** "Druckplatten / Gewichte / Loecher" (default off) - these are no longer part of
  "Schluesselgegenstaende" (that one keeps parts, switches, doors, grapple points).
- **(d) flight arc fix** (live 18.11.: the arc fell straight down from the take-off - the game hands 0x70e050 /
  0x70e100 v = 0 almost always): the arc's velocity is **T+0xa20 while a jump target T+0xa64 is set** (re-solved every
  frame), else the call's own v when it is not 0, else **inst+0x2a0 from the frame after the call** (R11, live
  22:10:42: T+0xa20 1.09 / -39.91 / 42.54, in flight inst+0x2a0 1.09 / -39.99 / ..). The `[Jump] arc:` line names the
  source (`T+0xa20 (target)` / `the call` / `inst+0x2a0`) and the frame.
- **(d) dashed jump preview `jump.preview`** (default off; page Figur "Sprung / Fall (Anzeige)"): while Lara stands
  (no air state), about 8 times a second, the arcs of the jump kinds in her target slots **A = T+0xb00** (white, live
  standing 56) and **B = T+0xc90** (violet, live 8): record X of the player block's jump table (P = `[[0xe7f094]+0x50]`,
  count P+0xde4, array P+0xde8 of {id, X} - read the way 0x6f1950 reads it; its first 14 bytes are checked, it is not
  called), v = R(yaw inst+0x38) (X+0x08, -X+0x0c, X+0x10), p(t) = p + v t + (0, 0, -2.862 t^2), dashed for t = 0 .. N
  (N = X+0xa4, else s16 P+0xbde, else 40), then dotted to the ground (segment query). Target guess: the unit markup
  lines within 3000 units (boxes without owner, as the Thor areas): the arc's descending time at a segment's height,
  that point within **300 units** (X+0x78, how the game uses it is unproven) flat of the segment, t <= N, first one
  reached = green diamond + "du landest auf Markup-Kante / -Linie (x m daneben)"; else "kein Ziel - Fallhoehe x m" with
  a diamond coloured by the fall limits a / b / c (green / yellow / orange / red). One `[Preview]` log line per change
  (slot, id, A, N and its source, target box / ground, the unproven parts marked). **`jump.catch`** (default off): a
  300-unit tube round the markup lines within 2500 units. Not proven: that the slot's kind is the one used at the
  take-off, the 300-unit rule, owned (moving) markup boxes are left out.
- **(e) `[Jump]` sites** (R11): 0x766b4f = ground move (state 1303, velocity reset) and 0x71b519 = restart (player
  set-up) are no jumps - one line at LogLevel 3 only; 0x71f6e4 = pole take-off (was "let go / tread water"), 0x75b12d
  = tread water. A call with v = 0 is logged (two lines + "flight follows the v = 0 call") only when an air state or a
  velocity follows within 10 frames, else at LogLevel 3 with "not a jump". A re-aim is counted only for the aim
  solver's sites 0x73f0d3 / 0x73f2cc (0.22.61 counted the pole take-off as a re-aim).
- **(f) throw paths and `[Push]`** (live 18.11. fight with the thrall panther: the light blue paths stayed, 16 panther
  chunks were logged as "pushed", the Thor pillar's 2 parts twice): the light blue real path fades out within 3 s after
  the body's rest; `[Push]` only for an object Lara can push - an uber (push-block) graph or a multibody with joints,
  no names with chunk / doll / debris / grenade - while Lara is not in the air and within 3 m; of one multibody only the
  first moving part is logged. Lara's own push state is not known yet: the gate is by object kind (marked in the log),
  the `[Push] start` line carries her record for the next build.
- **(g) "Figur aufs Ziel"** (wish 18.11.): under each chapel wall switch whose ring figure is not on its target a row
  `Figur aufs Ziel` (right 2x, "n Zuege"); **`puzzle.pullto <switch>|stop`** pulls it the n times one after the other
  through `puzzle.pull` (vt 59, the game's reaction): the next pull only when the figure stands (uber +0x80 = 0), the
  switch is back off (or 6 s after the last pull) and 1.5 s have passed; it stops when the figure is on target, the
  switch is locked (no centre plate, as in the game), a pull is refused, after 8 pulls or 60 s. Each pull and the end
  in the log (`puzzle.pullto ...`).

### TO TEST 0.22.62

| # | Where | Do | Expected |
|---|---|---|---|
| a1 | villa, switch 4617 (clock) | Raetsel -> `Schalter betaetigen` right 2x | log `-> vt 59 (request the on reaction from on ...)`, then `check after 6 s (vt 59 from on)`: lever node changes, bit 0x200 0 -> 1, secret door 4528 opens; or the line `vt 59 from on changed nothing` |
| a2 | villa, switch 4525 | the same | house door 4520 open, lever down, bit 0x200 1 (or the "changed nothing" line) |
| a3 | after a "changed nothing" line | TruLink `menu puzzle.pull 4617 action` | the 0.22.59 path (door opens, lever stays up) |
| b1 | Kapitel -> Raetsel in der Naehe | rows "Hinweise" / "Aktionen (Cheats)": Aktionen right 2x | action rows gone, hint lines stay; again = back; `[Puzzle] Actions=0` / `1` written |
| b2 | same | Hinweise right 2x | hint lines (list + world) gone, action rows stay |
| c1 | bar | Figur -> "Sprung / Fall (Anzeige)"; Kapitel -> "Raetsel-Anzeigen"; Debug -> "Objekt-Daten (Log)" | the rows switch / run as through TruLink |
| c2 | Kapelle, Leveldaten | "Schluesselgegenstaende" on, "Druckplatten / Gewichte / Loecher" off, then on | plates / weights / holes appear only with the new switch |
| d1 | Kapelle, `trace.arcs 1` | jump forward without a target, then platform -> pole | yellow arc forward along the jump (not straight down); log `[Jump] arc: ... from inst+0x2a0` resp. `from T+0xa20 (target)` |
| d2 | Kapelle platform, facing the pole, `jump.preview 1` | stand still, turn slowly | log `0.22.62 jump preview: byte check 0x6f1950 ok`; white dashed arc ahead; green "du landest auf Markup-..." when facing the pole, else "kein Ziel - Fallhoehe x m"; `[Preview] slot A id 56 ...` lines |
| d3 | same | jump forward | where Lara lands / catches vs the preview (report both) |
| d4 | beam <-> platform | `jump.catch 1` | cyan tubes round the nearby ledges / poles |
| f1 | fight (thrall panther, grenades), `trace.arcs 1` | wait after a throw / a kill | light blue paths fade out ~3 s after the rest; no `[Push]` lines for chunks |
| f2 | secret chamber | push the Thor pillar | one `[Push] start` (not two), the gate line, `lara rec=` = her push record (note it) |
| g1 | chapel, fire lit, centre plate down, a figure off target | Raetsel -> switch -> `Figur aufs Ziel` right 2x | log `puzzle.pullto <id>: ... needs n pull(s)`, `pull 1 ..`, .. `figure on its target`; the figure stands on its target |
| g2 | same, centre plate up | the same row | row shows "gesperrt"; TruLink `menu puzzle.pullto <id>` -> refused "locked" |
| e1 | walk, land, restart | log at LogLevel 1 | no `[Jump] drop via=0x766b4f` / `0x71b519` lines; a pole take-off shows `pole take-off`, followed by `flight follows the v = 0 call` |

## 0.22.61 - Thor pillar floor areas (2026-11-18)

Package R1c point 1 (ENGINE §9 "Thor pillar floor positions (R8b)"). Not installed.

- **`puzzle.thor`** (default off): where the pushable Thor pillar in `l3_secretchamber` must stand so that Lara can jump
  from its top (radius 552, ~1250 above its base) to a ledge - **computed at run time**, nothing built in:
  - pillar = the instance named `thor_pillar` (link 1 = the turning part), floor = the segment query 0x493330 below it;
  - targets = unit markup ledge boxes (no owner, box +0x28 bit 30) 1700 .. 2200 above the floor: a closed loop = column
    ring (yellow), an open ledge within 1500 units of a reward artifact `ma_rw_artifact` = that artifact (lower intro id
    green, higher blue), else the exit side (red);
  - floor cells of 150 units: one query per cell centre from floor + 1700 down (ignoring the pillar), within 20 units of
    the floor = strict, within 130 = relaxed; a cell is a valid pillar centre when every cell within 552 is floor;
  - area = valid centre whose flat distance to the ledge minus 552 is <= **`[Puzzle] ThorGap`** (default 600,
    `puzzle.thorgap <n>`).
  The build runs on the game thread (300 queries per frame, a few seconds), then the areas are drawn as cell outlines on
  the floor (thick = strict, thin = relaxed), the pillar's 552 circle, above the pillar per target "im Bereich" or
  "x m daneben", and a white arrow to the nearest valid cell. `[Thor] build ...`, `[Thor] areas ...` and one
  `[Thor] pillar at ...` line per change go into the log. No push action.

- **Holder rule + "Einstecken"** (R1c point 2, R4 `docs/Befund-R4-Halter-1811.md`): a carryable (component block
  class 0x32) gets the row `Einstecken -> Halter n (rule)` under "Gewichte / Stangen": the holder X names (its
  instanceref), else a holder whose script names X, else the nearest free holder (block class 6) whose entry lists accept
  X's object id (free = no other carryable of that id within 150 units, by position). **`puzzle.insert <carryable>
  [holder]`** puts it onto the holder (as obj.place, unless Lara carries it) and the next frame sends **message 0x165**
  (arg = the holder) through the game's send 0x5b3750 - Lara's own insert path (0x7179db / 0x717a5a, both byte
  checked; 0x5b3750 itself is not, another plugin jumps there); log lines before, at the send and 2 s after (pole
  place / distance, its holder, Lara's carry T+0x858, the hole's block). Whether 0x165 inserts a pole that Lara does
  not carry is unproven. **`obj.msg <intro> <msg> [<arg intro>|0]`**: one message through 0x5b3750 (TruLink 0.5.3
  `obj.msg`). "Gewichte -> Platte" takes the weights a counter trigger names first. Uber sockets (artifacts): no insert
  (the game needs Lara's target / entry, message 0x158); Thor gear sockets, the Mexico seal: no action.

### TO TEST 0.22.61

| # | Where | Do | Expected |
|---|---|---|---|
| 4 | start | log | `insert / obj.msg: 2 byte checks ok` |
| 5 | a level with a pole hole (R4 list) | Raetsel -> pole -> `Einstecken -> Halter n (...)` right 2x | log `puzzle.insert ... rule ...`, `before`, `message 0x165 sent`, `check after 2 s`: pole at the hole (0 .. 50 units), hole block records; the pole stands in the hole or not (report both) |
| 6 | same, Lara carries the pole | the same row | `Lara carries it (the game's own case)`; the pole goes in as with her own insert |
| 7 | TruLink | `obj.msg <pole> 0x165 <hole>` | `obj.msg ... sent through 0x5b3750` |
| 1 | `l3_secretchamber` | `puzzle.thor 1` | log `[Thor] build: pillar part ... floor ~173 ..., n target ledge(s): exit / artifact A / B / rings`, then `[Thor] areas (relaxed cells): ...`; outlines on the floor red / green / blue / yellow, white circle round the pillar |
| 2 | same | push the pillar into a red area | text `Ausgang: im Bereich`, log `[Thor] pillar at ...: exit in`; from its top the south gallery is in reach |
| 3 | same | `puzzle.thorgap 800` | areas grow (rebuild), `[Puzzle] ThorGap=800` written |

## 0.22.60 - motion data for live tests: jump launch / drop, throws and grenades, pushing, object tracking, flight arcs, ground below Lara (2026-11-18)

Package R1b (owner request 18.11.: jumps, grenades, jumping back / sideways off a ledge, throwing the heavy cubes, pushing -
shown as arcs, live, with every value in the log). Specs: ENGINE §12 "Lara jump: launch, gravity, aimed parabola
(R2b)", "Ground probe and catch data (R2b)", "Launch sites by kind (R10)", "Thrown objects and the physics body (R10)".
Not installed.

- **`[Jump]` lines**: the game's launch **0x70e050**(inst, g, vx, vy, vz) and drop **0x70e100**(inst, g) are wrapped
  (9 bytes = 4 whole instructions -> jmp, trampoline, pass-through; 6 byte checks incl. the aimed jump's call 0x73f0ce,
  the segment query 0x493330 / 0x49333d and g = -5.724 at 0x85e2b0). Line `launch` / `drop`: call site by kind (R10:
  aimed jump, InAirAnimTarget, state 510 simulation, state 230, grapple rope release, state 1001 slot 5, combat manager,
  let go / tread water, else the address), who, Lara's record `index [state ids]`, p0, v (u / frame), horizontal
  speed, direction against her heading (forward / back / left / right - the forward vector is unproven), inst+0x2a0, g,
  T+0xa64 target, T+0xa00 aim (as before this call), T+0x77c, plus a `launch+` line with T+0xa20, T+0xaa0, T+0x610 and
  dt [0xe7f188]. The aimed jump re-aims every frame of state 510: calls within 250 ms are `re-aim #n` (at most 3 / s).
  Then `[Jump] arc ...` (landing point or no hit), `[Jump] fly` every 2nd frame (position, inst+0x2a0, T+0x77c, dt; at
  most 90) until the record has no 510 / 515 / 517, `[Jump] flight end`. With the 0.22.59 `[Fall] land` line.
- **`[Throw]`**: a portable within 10 m leaving Lara's hands (`release`) or a grenade-named body within ~34 m taking
  off (`launch (no holder)`): position, body +0x80, v / w per tick, mass, sleep bit, Lara's record; `fly` every 2nd frame
  (at most 120), `rest` after 0.3 s still or 8 s (flat distance, drop, apex, path, time); once the physics world values
  (gravity [0xa037f4]+0x20c0, bounce +0x20d8) with the body's mass and damping +0x154 / +0x158. The thrower function is
  not found (R10) - no hook on the body setters.
- **`[Push]`**: a body within 3 m moving while Lara does not hold it: `start`, `move` (10 / s, at most 600), `end` (0.5 s
  still): position, rotation, the first hinge of its multibody (Thor pillar), velocity / angular velocity per tick,
  sleep bit (body +0x15c bit 0), Lara's record, the way since the start, and the last script print "Overriding Lara pull
  strength" (only while the script prints are redirected, `log.script 1`). A contact / "blocked" reason is not readable.
- Each `[Push]` / `[Track]` sample has a second line (R4, `docs/Befund-R4-Halter-1811.md`): Lara's carried object
  T+0x858 (unproven), her target T+0x854 -> +0xa0 / entry +0xac, the object's component block class (6 holder, 0x32
  carryable, 0x4f uber) and for a holder its record count B+0x6c with the first accepted object ids - track a hole
  before / after inserting a pole. The holder rule and "insert the pole" (message 0x165 through 0x5b3750) are not built.
- **`obj.track <intro> on|off | list`**: `[Track] sample` lines 5 / s for up to 8 objects. Over TruLink:
  `menu obj.track 4640 on` (no TruLink change; the lines go to TruMenu.log, not TruLink.log).
- **`trace.arcs`** (default off): Lara's flight arc p0 + v0 t + (0, 0, g t^2 / 2) from the latest launch call (every
  re-aim of the aimed jump redraws it = the target parabola), 2 frames per point, cut at the first hit of the segment
  query (mask 0x2c19e7, ignore Lara; hit point = res+0x10, unproven: the first hit's raw bytes go into the log once, a
  hit outside the segment is refused); yellow, red diamond at the landing, green at T+0xa00 with a target. A flying body:
  its predicted path orange (per tick v = (v + g3) x clamp(1 - k dt), p += v, no bounces), its real path cyan. No preview before the
  take-off (without a target there is no fixed launch velocity, R10).
- **`fall.box`**: + "Boden unter dir" and "Fallhöhe bei Landung" (ground probe every 100 ms on the game thread), air
  states 510 / 515 / 517, the scale of the last landing (records #1282 0.6 / #1283 0.3, else 1.0, the R2 table).

Not in this build: E Thor pillar areas, F (`chapter.cp`, sonar view, intro table at run time, holder rule), the
grapple-rope preview.

### TO TEST 0.22.60

| # | Where | Do | Expected |
|---|---|---|---|
| 1 | start | `TruMenu.log` | `0.22.60 motion data: 6 byte checks ok; launch 0x70e050 wrapped, drop 0x70e100 wrapped` |
| 2 | any level | standing jump, running jump, back / sideways off a ledge, let go of a ledge | one `[Jump] launch` / `drop` line each (site, v, direction, record), `fly` lines, `flight end` |
| 3 | chapel, jump to the pole | jump with a target | `aimed jump ... target=0x...`, `re-aim #n`, `[Jump] arc ... lands at` |
| 4 | `trace.arcs 1` | jump | yellow arc, red diamond on the ground, green at the target; `ground probe first hit` raw line |
| 5 | chapel weights | pick up and throw a weight | `[Throw] release`, `fly`, `rest`, `physics:` line; orange prediction, cyan path |
| 6 | secret chamber, Thor pillar | push / turn it, `log.script 1` | `[Push] start` / `move` / `end` with hinge degrees; `pull: Overriding Lara pull strength ...` |
| 7 | any | `obj.track <id> on`, `off`, `list` | `[Track] sample` 5 / s |
| 8 | `fall.box 1` | at a ledge, jump down | "Boden unter dir", "Fallhöhe bei Landung" match the drop (chapel gap ~10.8 m) |

## 0.22.59 - intro marks mid-chapter, pull a switch through its script, holds that open first and several at once, puzzle help levels with hints, key items for plates / weights / pole holes, landing log (2026-11-18)

Package R1 (live test 17.11., `docs/Pakete-1811.md`). Not installed - the owner installs with the game closed.

- **Mid-chapter keep-state loads** (`chapter.unit`, `chapter.keep`, `level.keep` of a unit that is no level-start
  intro's own unit): on the loading screen (main state 2) the played marks (sticky int 0:<intro> key 5968) of the table
  intros whose own unit is loaded and in the **same level group** (`kUnits` group) are kept at 1 - the chapel no longer
  plays chapter 3.1's intro of the neighbour `l3_caverns_start` (live 17.11. test 5; 5b proved mark 1 = no intro, Lara
  on CP 4735). Log after the screen: the marks of every loaded table intro (`1+`, `0`, `unbound`).
- **`puzzle.pull <switch>` "Schalter betaetigen"** (row under every switch, help level 2): the switch's own script as
  Lara's pull. Switch base 3637: off -> vt 59 (request the on reaction: the lever; the game then runs vt 20 -> vt 55),
  on (villa switches: +32 = 0 = on before and after a pull) -> vt 55 (the action itself: clock + secret door, house door,
  pillars command). Called as the exe does it (checkpointbase 0x796e90): entry = 0x575fb0(so, byte [[so+0xc]], vt),
  then 0x57b380(so, entry, 0, 0, 0), next game frame; the entry must be one of the chain's functions whose prototype has
  that vtable index. Refused: disabled (+32 == +24, e.g. chapel without the centre plate), used (+0x1c bit 0x200 and a
  one-shot target). 3 byte checks at the start. Check after: every change of +32 / bit 0x200 / the target's node (or
  open flag) for 15 s, a summary at 6 s (`marked used`, `the target moved through the switch` or `NO target change`).
- **Hold open** (`puzzle.hold`): (a) a closed motor door is opened by the same drive first ("Tuer oeffnen + offen
  halten", the locks of an object check stay the game's); a closed plate gate with exactly one opening set-node record
  gets "Tor oeffnen + offen halten (Eintrag n)" - the first tick sends it; (b) up to 4 motor holds and 4 gate holds at
  the same time, a new hold of the same door / gate replaces only that one; `puzzle.hold <intro> off` /
  `<intro> <joint> off` release one, `off` all, left on a row = release all; (c) the shadow door's turning pedestal is
  offered closed too (0 -> 170 degrees, the 180 wrap is taken). Node changes of a held gate link are logged.
- **Puzzle help levels** (`puzzle.help`, `[Puzzle] Help`, first row of "Raetsel in der Naehe"): 0 off (objects and
  state), 1 hints, 2 solve (hints + every action row, default). Hints are computed from the loaded objects: switch
  "noch n x ziehen (Figur k)" / "erst Platte x druecken" / "schon benutzt", plate "braucht n Gewichte (eins drueckt nur
  beim Aufprall)", plate gate "offen solange Platte x unten", motor door "zu in ~n s", timer gate "Restzeit n s", gates
  "Weg ab CP n (m m)" (nearest checkpoint object), weight "-> Platte x (oben)", pole hole "Stange einstecken". A local
  `[Puzzle] HintFile` (default `TruMenu.puzzlehints.txt` next to tru.exe, lines `<intro id> <text>`, never in the
  repository) adds text. Hints show green in the list and at the object in the world (under its label, else a label of
  its own; the debug view runs for them). Built every 500 ms on the game thread while level >= 1 or the key items layer
  is on.
- **Key items** (`dbg.keyitems`): plates, weights / poles and pole holes (`ma_pt_pole_hole`) of the puzzle info table
  get a label with their state (`oben / unten: Gewicht x`, `auf Platte x`, `Loch leer` / `Stange x daneben (steckt?)` -
  the pole by position only).
- **Sonar**: the rows `sonar.loadnb` / `sonar.loadall` say "wirkt beim naechsten Oeffnen".
- **Landing log line** (package R2, `docs/Befund-R2-Fallschaden-1811.md`): the fall damage check of chart state 1304
  0x75d080 is wrapped (7 bytes -> jmp, trampoline; 4 byte checks): `[Fall] land via=enter|tick|exit rec=<record>
  h=<height> (m) z0 / off / z / att / mk thr=a/b/c vz hp before -> after (dmg / max) type DEAD|hurt|no damage`, then
  `[Fall] next rec=<record>` (m+0x510 changing within 5 s). Read only.
- **Fall height box** (`fall.box`, default off, bottom left; owner request 18.11.): the height since the take-off
  h = z0 + offset - z (R2, without the markup term - "+ Markup" is named) while Lara's current record holds state 515 /
  517, else "am Boden"; the limits a / b / c read at run time from `[0xfad764]` +0x4c / +0x50 / +0x54 (DLC 2's Lara has
  her own), green < a, yellow a .. b, orange b .. c, red > c, and the distance to the next limit in m. The landing scale
  (parameter 1315) and a ground probe below Lara are not in this build.

Not in this build (report R1): `chapter.cp` (Q11 spec), the intro table from the archives at run time, the sonar view
kept over a close, the holder rule from the references.

### TO TEST 0.22.59

Install TruMenu 0.22.59 (game closed). `TruMenu.unitintros.txt` stays next to `tru.exe`.

| # | Where | Do | Expected |
|---|---|---|---|
| 1 | start | `TruMenu.log` | version 0.22.59; `puzzle.pull: 3 byte checks ok`; `landing log: 4 byte checks ok, 0x75d080 ... wrapped` |
| 2 | new game, Prolog done, `l3_chapel` never played | Kapitel -> `l3_chapel` right 2x | log `armed ... (0.22.59: only intros of the same level group)`, `intro 4318 of the loaded unit l3_caverns_start - played mark 0 -> 1`; no intro, Lara on CP 4735 |
| 3 | villa `l3_chamberrockhall`, switch 4617 unused | Raetsel -> `Schalter betaetigen` right 2x | log `vt 55 ... called`; within 6 s `bit 0x200 0 -> 1`?, secret door 4528 `closed` -> `opening` -> `open`; row `bereits benutzt` |
| 4 | chapel, centre plate down | wall switch 4819 `Schalter betaetigen` | `vt 59`; lever moves; a pillar steps; log `+32` change |
| 5 | chapel, reward grate 4836 closed (plate 4833 up) | `Tor oeffnen + offen halten (Eintrag n)` | log `closed at the start, ... sent`, node `... -> ...` lines; the grate opens and stays |
| 6 | chapel | hold round gate + reward grate + shadow door | all three hold, `3 hold(s) running`; left on a row = release all |
| 7 | chapel, shadow door closed | `Tuer oeffnen + offen halten (Motor)` | opens to ~170, holds |
| 8 | chapel | `Raetsel-Hilfe` right 2x until `Hinweise` | no action rows; green hints in the list and at the objects |
| 9 | chapel, `dbg.keyitems 1` | look at the plates | plate 4834 labelled with `oben` / `unten: ...` |
| 10 | chapel platform | jump into the gap / onto the pole | `[Fall] land ... h=... DEAD` / `no damage`, then `[Fall] next rec=...` |
| 11 | any level | `fall.box 1`, jump down a ledge | bottom left: height grows green -> yellow -> orange -> red over a / b / c; on the ground "am Boden" |

## 0.22.58 - chapter rows by kind, keep-state loads with the intro mark, loading-screen watch, reload last checkpoint, costume 857 outside DLC 2 (2026-11-17)

Build `work\asi\menu02258` (TruMenu.asi MD5 `f932052dbcf3c83f7fe06014dbe20fe7`, sha256
`94a1f3c5c104d985052d772dfbd47f69c4bec0d24584ab0a0c1f158d631a320c`; 0 warnings in TruMenu.cpp; quick / readability /
format checks exit 0, ini check exit 1 only for the 5 known TruTrace rows), not installed. Package Q1b of the workspace
`docs\Pakete-1711.md`: the Q1a spec S1 - S7 (ENGINE 4.2 "Death restart request", ENGINE 11 "Loading screen close = 8:6
f3", "Chapter intro under another main unit", "Level-start unit scripts and their intro objects", "TruMenu level.reload
and Lara's chapter"; TRU-Knowledge 8) and the Q4 spec (`docs\Befund-Q4-Doppelgaenger-Kostuem-1711.md`, ENGINE 20.6).
Offline only: build, the TruMenu checks, the table tool on the PC files. "(unproven)" = only the live test shows it.

- **Intro table (S3)** - the eight level-start intros (the start scripts with the already-played branch) are game data,
  so they are not in the source: `tools/unit_intro_table.py` reads the own PC files and writes
  `TruMenu.unitintros.txt` (default into `local_results\unit_intros\`; copy it next to `tru.exe`, like
  `TruMenu.weaponwaves.txt`). One line per intro: `<intro id> <own unit> # script; carried by ...`. Info item
  `chapter.intros` lists the table with every intro's played mark now (sticky int `0:<intro>` key 5968). Without the file
  the mark steps below are skipped (one log line at the start), the watch still runs.
- **Page Kapitel rows by kind (S1).** Chapter starts (the rows on top, and unit rows under a heading `Kapitel ...` /
  `Prolog ...` on the first visit, the DLC starts) = as 0.22.56: backup, the in-level level start f27 (new game data, the
  intro plays). Every other unit row (mid-chapter, return visits, DLC units) = **`chapter.unit <unit>`**: backup, then
  **`level.keep <unit>`** (state kept), column `Stand bleibt`. `[Chapter] UnitFresh=1` / `chapter.unitfresh 1`
  (experimental) = backup, `level.start <unit> 0 mark`: new game data, and on the loading screen (main state 2) the played
  marks of the table intros whose own unit is loaded (not the target) are kept at 1 - the chapel then should not play
  chapter 3.1's intro of `l3_caverns_start` ~19 m off its scenery (unproven).
- **Keep-state loads (S2):** `level.keep <unit>` = `level.load`; when `<unit>` is an intro's own unit and that intro's
  played mark is not 0, the mark goes to 0 right after the request (the game's sticky set + change notification, as
  `sticky.set`), so the intro plays and closes the loading screen (unproven). Used by `Kapitel (Stand behalten)`
  (`chapter.keep`), the `chapter.unit` rows and `level.reload`. **Watch:** after such a load TruMenu watches the script
  prints for 90 s (it redirects them for the watch when `log.script` is off, and back after): `: Cine already played`
  without `*** ABOUT TO FADE OUT LOADING SCREEN` within 10 s = a warning line `0.22.58 watch: ...` and the footer
  `Ladebild haengt evtl. ...`; nothing else is done.
- **`Letzten Checkpoint laden` / `cp.reload` (S4)**, page Kapitel (second row) and page Rettung: the game's restart after a
  death without the death - only `[0xe7f0b8] |= 0x80000` (6 byte checks `kCrChecks`), refused outside main state 1, without
  a player, in a cutscene, with a level change pending, while the game's pause bit 0x1000 is set (not by TruMenu) or the
  bit is already set. Flight off and the camera-hint clear are armed first. The log names the prediction (byte
  `[GameTracker+0x169]`, the checkpoint's unit loaded -> in-place restore 0x5de480, else full reload 0x5df760(6)) and the
  result (main state 2 seen within 5 s = full reload, the longest game-thread gap, the player instance before / after).
  Not served within 20 s = the bit is taken back.
- **`level.reload` (S5)** is named what it is: `Unit neu laden (Anfang, Stand bleibt)` / `Reload unit (unit start, state
  kept)` - a `level.keep` of the current unit (Lara starts at the unit's start, not where she stood).
- **Chapter from the safe ground (S6):** `chapter.reload` / `chapter.keep current` take Lara's stream unit, but the newest
  safe-ground spot's stream unit (new field of the sampler) when she is off the map: no stream unit, a unit outside the
  chapter table, in the fall record 1068, or more than 3000 units below that spot. The row shows the unit it will load
  and where it came from: `l3_caverns_start (von l3_chapel)`, `... (sicherer Boden ...)`.
- **DLC (S7):** in DLC 1 / DLC 2 the row reads `DLC-Start neu laden` / `Reload DLC start` (the DLCs have no sub-chapters);
  `Letzten Checkpoint laden` is the per-area restart.
- **Costume 857 outside DLC 2** (replaces the 0.22.55 grey lock). **Fix A (default):** with the doppelganger flag
  `[[0xfadb58]+0x1244]` = 0 the live switch to `doppelganger_casual` (row, `costume.set 857`, the cycle step) goes to its
  clone **`dlc_doppel_costume_a`** (found by name, checked with the game's 0x5c54e0) - the same model without the type
  entry: no DoppelgangerInit, no shadow power. Row label `doppelganger_casual -> dlc_doppel_costume_a (ohne
  Schattenkraft)`, one log line with both ids. Without the clone the row stays grey as 0.22.55. DLC 2 (flag 1) = 857
  unchanged; `costume.choose` (the next load) untouched. **Option B** `[Costume] DoppelLive=1` / `costume.doppellive 1`
  (experimental, 5 byte checks `kDgChecks`): the real 857; right before message 35 game data `+0x390` = 0 (the default
  branch: the unit's gear list instead of the restore branch that waited for the old weapons), two game frames later slot
  0 (right hand, `WM+4`) must hold a live weapon - else the log line `slot 0 empty after doppelganger switch`, a red footer
  and at once back to the previous costume.

### TO TEST 0.22.58

Install TruMenu 0.22.58 (game closed) and copy `local_results\unit_intros\TruMenu.unitintros.txt` next to `tru.exe`.

| # | Where | Do | Expected |
|---|---|---|---|
| 1 | start | `TruMenu.log` | version 0.22.58; `0.22.58 intro table: 8 level-start intro(s) from ...`; `cp.reload: 6 byte checks ok`; `costume B: 5 byte checks ok` |
| 2 | any level | `chapter.intros` | 8 rows `<intro> <unit> mark <n / ->` |
| 3 | `l3_chapel` | Kapitel -> Abschnitte 3 -> `l3_chapel` right 2x | column `Stand bleibt`; log `chapter.unit ... level.keep`; no intro, the screen closes at once, Lara at CP 4735 |
| 4 | `l3_chapel` | row `3 Croft Manor` right 2x | the 3.1 intro plays from `l3_caverns_start` (fresh), the screen closes, Lara on its checkpoint |
| 5 | `l3_caverns_start`, intro played | `Unit neu laden (Anfang, Stand bleibt)` right 2x | log `intro 4318: played mark 1 -> 0`; the intro plays again and the screen closes; no `watch: ... no '*** ABOUT TO FADE` warning |
| 6 | same, without `TruMenu.unitintros.txt` | the same | after ~10 s the warning `0.22.58 watch: ': Cine already played' ...` and the footer hint (the screen may stay - then 7) |
| 7 | a level, Lara alive | `Letzten Checkpoint laden` right 2x | log prediction + `result IN-PLACE RESTORE` (checkpoint unit loaded) or `FULL RELOAD`; Lara at the last checkpoint |
| 8 | DLC 1 `dlc_caverns_hall` | Kapitel row 1 | name `DLC-Start neu laden`, state `dlc_level1_start (von dlc_caverns_hall)`; `cp.reload` restarts the area |
| 9 | `chapter.unitfresh 1`, then `l3_chapel` row | right 2x | log `fresh unit start l3_chapel: intro 4318 of the loaded unit l3_caverns_start - played mark 0 -> 1`; no misplaced intro (unproven) |
| 10 | after a fall out of the map (or Lara under the chapel ledge) | look at row 1 | `... (sicherer Boden <unit>)`; `chapter.reload` logs `off the map (...)` |
| 11 | DLC 1, normal costume | `costume.set` another Lara costume, `weapon.slots`, `save.waiting` | slot 0 = pistols, wait table empty (Q4 test 1) |
| 12 | DLC 1 | Kostueme -> `doppelganger_casual -> dlc_doppel_costume_a (ohne Schattenkraft)` | log `857 doppelganger_casual -> 1031 dlc_doppel_costume_a`; doppelganger look; no new DoppelgangerInit in TruDlc2Player.log; `weapon.slots` slot 0 set; draw, attack, 2 min walking / climbing without a freeze |
| 13 | DLC 1, `costume.doppellive 1` | `costume.set 857` | log `+0x390 1 -> 0 right before message 35`, `slot 0 ... - ok`; draw without a freeze; LB / RB shadow power. Slot 0 empty: `slot 0 empty ...`, red footer, back to the previous costume |
| 14 | DLC 2 | `costume.set 857` with the flag set | unchanged (no redirect, no +0x390 line) |

## 0.22.57 - puzzle helpers 2: figures only with the fire, hold open for every gate kind, part labels, weights onto a plate, switch commands from the scripts (2026-11-17)

Build `work\asi\menu0257` (TruMenu.asi MD5 `30c8cdcddd91353874e2fecde5f63562`, sha256
`382a58c6b085f3daa906535de9b4d7af9c3ad96136b21400063cb6ef888fd7de`; 0 warnings; quick / readability / format checks exit
0, ini check exit 1 only for the 5 known TruTrace rows), not installed;
with TruLink 0.5.2 (`work\asi\trulink052`, `src\asi\TruLink\README.md`). Package Q2 of the workspace
`docs\Pakete-1711.md`, from the live test of 2026-11-16 (`docs\Testanleitung-1611.md`, results K3 - K13, V3, D1, D7).
Offline only: build, the four TruMenu checks, the switch trace on the chapel dump 26292. "(unproven)" = only the live
test shows it.

- **"Figuren auf Ziel setzen" only while the fire burns.** Live 16.11. (K7c / K7d): a picture set in the dark is stored
  by the pillar script (+112 / +168) but **not** acted on at the lighting; the locks open at the **next switch pull
  while lit**, from the stored pictures. The original cannot reach the dark case (its switches are disabled without the
  fire). The row is grey with `gesperrt: erst Feuer (Platte unten)` / `locked: fire first (plate down)` while the fire
  plate is up, and `puzzle.figures` refuses then (log line). The check row says `Feuer aus: Schloesser erst bei Feuer +
  Schalterzug`. The 0.22.56 text "the locks open only at the next lighting" below is wrong (kept as history).
- **Hold open for every gate that can close** (Kapitel -> Raetsel in der Naehe, under the target), kind from the gate's
  data at run time (no id list), one hold at a time (a new one ends the old one; left = release):
  - *motor* (`puzzle.hold <intro> <joint>`): a hinge **or rail** with limit and motor on and a velocity (0.22.56: hinge
    only). Row `Tuer (Gelenk j, Teil p)` with `offen 156 Grad, zu in ~45 s` and `Tuer offen halten (Motor)`; only while
    open (> 5 degrees / 10 units from the closed end) or held - closed joints (the shadow door's locks) get no row. The
    drive target is **8 degrees / 20 units inside the open limit** (was 1; live K11b: 170 with the limit ~178 held), the
    **180 / -180 wrap** of the hinge getter at the stop is taken back into the limits (`tlobj::HingeUnwrap`, in the row,
    the start value and every drive tick - live K10 / K11b: -180.00 between 179.91 and 175.18, the drive stopped "outside
    the limits"). **Fix:** 0.22.56 left the door rows out after a check over non-ring parts (`if (!ring) continue;` in
    the target loop) - the reason the great shadow door 4835 showed no door / hold row (K11), not its parts.
  - *timer* (`puzzle.hold <intro> timer`): an auto-reset gate (P4: back to its start on time alone - DLC 1
    `dlc_caverns_hall`, 25.0 s). While the link is in the node of the longest time condition on the way back (`open`) and
    no transition runs, its time in node `[b+0x88]` is set to 0 every game frame, so "time >= 25 s" never holds. Row
    `Tor offen halten (Zeit in 'open' anhalten, 25 s)`; `rechts 2x (haelt, sobald offen)` before the gate opened. Off =
    the time runs again from 0 (the full 25 s).
  - *counter command* (`puzzle.hold <intro> counter`): a reversible gate with "set node" records in its object command
    table (chapel round gates / reward grate: Raise / Lower). The open entry = the set-node record whose node is the
    link's node now or leads to it on internal edges (Raise -> At_Top); when the link reaches the closing side (Lower and
    what it reaches internally: AtBottom, FX_collision) the open entry is sent at once through X vf+4 (`tlact::CmdExec`,
    the plate's own path), at most every 250 ms, 400 times. `erst oeffnen (Platte / Schalter)` while closed.
  - none for a target that a trigger volume names (`nein: Story schliesst (Trigger t)` - villa secret door) and none for
    one-shot gates without a closing motor.
- **Part labels** (live K3 / K10): the key-items layer (debug view 14, the layer that labelled the door parts on 16.11.)
  now names a part `<object> . Teil n/N (<node>)` at its model (bone 0) as the names layer; parts whose bone 0 shares a
  spot (within 30 units) with a lower link are lifted 90 units per such link. The door's rest time sits on the part the
  joint moves (joint record B, A when B is the world: shadow door hinge 1 = link 2 = the turning pedestal), in the
  **state line of the first label** of that part (key items / names) instead of a merged extra line that was dropped
  when labels overlapped. Same in the uber labels (0.22.56 matched either body of the joint).
- **Labels of anchors and poles:** a multibody anchor carries the hide bit from its own constructor while its parts are
  drawn - names / labels / key items now label it (centre plate 4834 had none, K4). The key-items layer adds
  `kein Loch (Original-Daten)` to a pole's state line (it labels poles first; the names layer then skipped the pole, K13).
- **"Gewicht zu mir"** lands **behind** Lara (live K5 / K7a; the owner: fine) - row, log and answer say so now; every
  weight gets its own spot (its slot in the undo table: 120 units apart sideways, four per row, the next row 150 units
  farther) instead of one stacked pile.
- **NEW `Gewichte -> Platte x`** (`puzzle.weights <plate>`, one row per plate): the nearest free weights (not carried,
  not on this plate, loose ones before those on another plate) onto the plate until two lie on it, side by side (+-70
  units along x, 150 above the plate origin = TruLink `obj.place onto`; one added next to a weight already there goes to
  the far side of it). Live K12: one weight presses the plate only by its impact, two keep it down. Each old place is
  kept for `puzzle.bring <id> back`.
- **Switch -> command from the data** (instead of "learned"): `PzSwitchEntry` (TruPuzzleCore.h) reads the switch's
  loaded script as `tools/puzzle_switch_scan.py` reads the files - an `instanceref` member holding the target's intro id
  bound by `instanceref` f6 / f7, then a call of a function / prototype of a class of the target's chain (override by
  vtable index), whose code pushes an `uberobjectcommand` (member or local) and calls `uberobjectbase` f1: the command
  entry = value word 1 of its init block. Offline on dump 26292: 4819 -> 0 (link 1), 4820 -> 3, 4821 -> 1 (link 0),
  4822 -> 2 = P4. Switch rows show `-> <target> <id>, Befehl n (Teil l)`; the figure rows `Schalter s noch n x` at once
  (the 0.22.56 learning stays as a fallback). One log line per switch / target and level.
- **"bereits benutzt"** = instance +0x1c bit **0x200** (live V3 / V3b: villa switches 4617 / 4525 0 -> 0x200 at the
  first pull, +32 stays 0 = their "on" value before and after) with the target state (node, or the open flag of a door
  without a graph: house door 4520 = its stickybool, +8). The bit is the engine's "has been animated" bit - every pulled
  switch gets it - so a target that can act again (ring / toggle / repeatable / auto-reset) keeps the switch
  `bereit (schon gezogen)`. `bereit` replaces `aus, bereit` / `an` (the on value of +32 is no state for these switches).
- **Export `TruMenuPuzzleList(char *out, int size, int lang)`** (game thread only): the rows of Raetsel in der Naehe as
  text, for TruLink 0.5.2 `puzzle.list`.
- **Level not found before queueing** (live D7): the command bar / TruLink answer `err refused: level not found ...` at
  once for `level.load` / `level.start` (the same unit-list / `mods\<unit>.drm` tests; the item tests again when it runs).

### TO TEST 0.22.57

Install TruMenu 0.22.57 **and** TruLink 0.5.2 (game closed).

| # | Where | Do | Expected |
|---|---|---|---|
| 1 | start | `TruMenu.log`, TruLink `ping` | version 0.22.57; `pong TruLink 0.5.2`; checks as 0.22.56 |
| 2 | `l3_chapel`, plates up | Kapitel -> Raetsel in der Naehe | switch rows `-> ma_uo_shadow_pillars 4837, Befehl 0 (Teil 1)` (4819), 3 / 1 / 2; figure rows `Schalter 48xx noch n x` without a pull; log `0.22.57 puzzle: switch ... sends command entry ...`; `Figuren auf Ziel setzen` grey `gesperrt: erst Feuer` |
| 3 | same | debug view names + key items (14) | centre plate 4834 has a label; the shadow door parts `... Teil n/6 (...)`, the closed door's part labels stacked, not on one spot |
| 4 | same | `Gewichte -> Platte 4834`, right 2x | two weights land side by side on the centre plate, the plate goes down, the fire lights; `zurueck` rows per weight |
| 5 | same, fire lit | `Figuren auf Ziel setzen` | the locks open (the game's sequence) |
| 6 | same | turn the pedestal open, look at its label and the list | `Tuer offen ...` in the pedestal's label (state line), list rows `Tuer (Gelenk 1, Teil 2)` + `Tuer offen halten (Motor)` |
| 7 | same | `Tuer offen halten (Motor)` at the open stop, right 2x; wait; left | no "outside the limits" stop; holds ~170 degrees; after left the door closes with -3.5 deg/s |
| 8 | same, a side plate down | `Tor offen halten (Gegenbefehl)` on the round gate, then take the weight off | the gate stays up (log `counter: ... reached 'Lower' ... sent`); off: it lowers |
| 9 | same | `Gewicht zu mir` for three weights | each behind Lara on its own spot (not stacked) |
| 10 | DLC 1 `dlc_caverns_hall` | `Tor offen halten (Zeit ...)`, pull the gate switch, wait 60 s, then off | the gate stays open, label `noch 25 s`; after off it closes 25 s later |
| 11 | villa | switches 4617 / 4525 before / after | `bereit` before; after `bereits benutzt, Ziel open` / house door `offen` |
| 12 | `l3_secretchamber` | pole 4686, key items layer | state line `kein Loch (Original-Daten)` |
| 13 | command bar | `level.load xyz_nichtda` | at once `err refused: level not found ...` (no "ok queued") |
| 14 | TruLink | `puzzle.list`, `puzzle.list de` | the rows of 2 as tab-separated lines |

## 0.22.56 - puzzle helpers, notes (TruLink mark.*), camera hints on a level change, chapter rows as a level start (2026-11-16)

Build `work\asi\menu0256` (TruMenu.asi MD5 `a8609c5488595ae4b67f04f1ac1f4125`, sha256
`c61fc98bd3c49f8fa4d727261b5649fa1de9dd828b70306680832b8e631631a5`; 0 warnings in TruMenu.cpp; quick / readability /
format checks exit 0, ini check exit 1 only for the 5 known TruTrace rows), not installed; new exports
`TruMenuNote` / `TruMenuNoteClear` / `TruMenuNoteList`; new header `TruPuzzleCore.h` (pure reads, run offline on the
chapel dump by `TruLinkObjTest puzzle <id>`). Package P2b of the workspace `docs\Pakete-1611.md`; P1 = TruLink 0.5, P3 =
the chapel load analysis, P4 = the switch rules, P5 = the chapel / villa scripts. Everything here is checked offline
only (byte checks, build, the four TruMenu checks); "(unproven)" marks what only the live test can show.

- **Notes (exports `TruMenuNote` / `TruMenuNoteClear` / `TruMenuNoteList`)** - the interface of the TruLink README
  section "mark.note (needs TruMenu)": up to 64 notes keyed by intro id (runtime ids too), printable ASCII up to 95
  characters, flags bit 0 = shown even when the object names are off, bit 1 = kept over a level load (else cleared when
  the main state turns 2). The object-name layer adds the note as one more line of the name label (same colour); a
  note with bit 0 that the name layer did not draw (layer off, instance filtered) is drawn right under another layer's
  label of the instance, else as a small label `<intro>: <text>` at the instance (a multibody part at its model).
  Thread safe (SRW lock). TruLink 0.5.1 `mark.note` / `mark.clear` / `mark.list` / `mark.refs` use them.
- **P3 fix 1 - stale camera hints** (crash 2026-11-15 22:27, ENGINE section 22): every level change TruMenu requests
  (`level.load` and everything that uses it, the in-level level start, the mission start) arms a flag; while it is
  armed and the main state `[0xe7ed60]` is 2, the game-thread hooks (Present - the game's own Present call, it runs on
  the loading screen - and PadHook) log the old values and write 0 to `[0xe804f0+0x110]` (object hint) and
  `[0xe804f0+0x10c]` (volume hint count), exactly the words the game's reset 0x5edf50 clears; the game's own reset
  0x5f2440 still follows at 0x72249c. No game function is called. The flag ends when the main state leaves 2 (one log
  line with the number of clears) or after 30 s without a state 2 (log line, nothing written). 6 byte checks
  (`kChChecks`: the two writes of 0x5edf50, the getters 0x5e8490 / 0x5e84a0 / 0x5e84c0, the player-init order
  0x722497 / 0x72249c); info item `camera.hints`.
- **P3 fix 2 - chapter rows in a level** (the loading screen held over the level after `level.load` into a room whose
  intro was played, 15.11. 20:40): the chapter rows of page Kapitel and `Aktuelles Kapitel neu laden` now run, in a
  level, the in-level level start of 0.22.51 for **every** unit: `save.backup kapitel;level.start <unit> 0` =
  uigamedata f27 0x77e170(unit, 0, 0, 1) (the new-game block 0x556940(0) = new game data: costume words, the played
  marks (unproven word by word)), the UI stack's top screen vf+0x148 only while the game holds the pause bit, then
  stdscreenmgr f7 0x4be580 and f19 0x4be5e0 - with fix 1 armed. Preconditions as in 0.22.51 (main state 1, a player,
  no cutscene, no pending change, the case-8 byte rows) plus the outfit-rule rows and the camera-hint rows; otherwise the
  row is refused with the reason. DLC starts as before (TU rule). **`Kapitel (Stand behalten)` / `Chapter (keep
  state)`** (choice row, left = the chapter, first choice `aktuelles Kapitel`, right twice) = `chapter.keep
  <unit>|current`: backup, then `level.load` as up to 0.22.55, with the warning "Stand bleibt: Intro evtl. nicht,
  Ladebild kann haengen".
- **Kapitel -> `Raetsel in der Naehe` rebuilt** from TruLink 0.5's decoders (`src\asi\TruLink\TruLinkObj.h`, the same
  118 byte check rows, log `0.22.56 puzzles: TruLink 0.5 byte checks ...`) and TruLink's own action code
  (`TruLinkAct.h`, moved out of TruLink.cpp unchanged), within 2 x `[Debug] UberRadius` of Lara, every 300 ms while open:
  - *Schalter*: an instance whose class chain holds the switch base (P5 base 3637, recognised by its shape: member 0 a
    `modifiable` at +4, ints at +8 .. +32): `aus, bereit` (+32 = +16), `an` (+32 = +20; `an - bereits benutzt` when its
    target is one-shot), `gesperrt` (+32 = +24) - `gesperrt: Platte <p> nicht gedrueckt` when a plate it names is up
    (P5: the chapel wall switches are enabled only while the centre plate is down); the target (first multibody / uber
    instance it names) with its kind from the graph (P4 rules: einmalig / Ring n / Umschalter / wiederholbar / umkehrbar
    / setzt sich nach n s zurueck).
  - *Druckplatten* (name holds `plate`): `unten` / `oben` from the plate base's stickybool (P5 +92), the rail value,
    `Gewicht <w>` / `Lara` on it (physics positions within 200 units across, -100 .. +350 high), and what it names
    (`oeffnet / steuert Tor <g>, Feuer <f>`).
  - *Ziele* (multibody anchors and uber objects that something names): kind and node, `braucht Gewicht auf Platte <p>`
    for every plate naming it that is up.
  - *Figuren* (a multibody with an object check, condition 9): the check with the most entries (chapel: all four ring
    pillars on `position_a`), per checked link `Figur n: <now>, Ziel <target>` with the steps left along its trigger
    edges - `Schalter <s> noch n x` once TruMenu has learned which switch steps that link (a link moved while Lara stood
    within 2 m of a switch naming the object, log `puzzle: learned ...`), else `Befehl c noch n x`; the fire from the
    plate that names the igniter that names the object (`Feuer an (Platte p unten)` / `Feuer aus: Schloesser erst bei
    Feuer`, P5: the pillar check acts only while the fire burns). Row **`Figuren auf Ziel setzen`** = `puzzle.figures
    <intro>`: the command entries with one event record to that link through X vf+4 0x4d77a0 (as the switches), one
    command per idle link (no transition, events not dropped), at most every 250 ms, 64 commands / 60 s; the game's
    object check and the pillar script do the rest - **no lock, door or node is set**, and without the fire the locks
    open only at the next lighting (the row says so). **Wrong (live 2026-11-16 K7c / K7d, corrected in 0.22.57):** the
    locks open on the next switch pull while lit, not at the lighting; 0.22.57 offers the row only with the fire.
  - *Tuer*: a hinge with its motor on and a velocity != 0 (motor-closed; chapel: hinge 1 of the great shadow door
    4835 = the turning pedestal / Kreiselschalter that holds the door open): `offen 148 Grad,
    zu in ~42 s` = (value - the limit the motor drives to) / motor speed (rad per 1/30 s tick x 57.3 x 30), also on the
    uber label of the part the hinge moves (`... | Tuer offen 148 Grad, zu in ~42 s`). Row **`Tuer offen halten`** =
    `puzzle.hold <intro> <joint>`: TruLink's joint drive with hold-until-off (30 deg/s, force 20000, limits kept) to 1
    degree inside the open limit; only when the door is open (> 5 degrees from closed); right again / left =
    `puzzle.hold off`: the saved motor velocity / force / enable go back, the door closes by itself.
  - *Gewichte / Stangen* (body + class `portablebase`): `liegt` / `auf Platte p` / `Lara traegt es`; **`Gewicht zu
    mir`** / **`Stange zu mir`** = `puzzle.bring <intro>`: TruLink's `obj.place near-lara 1.5` path
    (INSTANCE_SetPosition 0x5b4100 + body <- instance 0x497740, velocity 0, woken), refused while Lara carries it;
    `zurueck an den alten Platz` = `puzzle.bring <intro> back` (the first old place, same path). **No "Stange in Loch y"
    row**: the placement only moves the body - inserting is the game's interaction with Lara holding the pole (insert
    check 0x6d5b38), which the placement path does not run; the pole would lie under the hole. Lara inserts it herself.
  - the 0.22.31 joint-range rows stay as a list (`Gelenk-Bereiche (nur Anzeige)`); their **"solve" (joint.set to the
    middle of a range) is gone** - it drove the great shadow door's rail while both locks were closed.
  - Log: one line `puzzle: <object> <intro> '<node>' -> '<node>'` per node change / transition start of an uber state
    near Lara (every 250 ms in a level, 400 per level).

### TO TEST 0.22.56

Install TruMenu 0.22.56 **and** TruLink 0.5.1 (game closed). Chapel = `l3_chapel`, villa = `l3_main_bedroom` /
`l3_chamberrockhall`, DLC 1 gate = `dlc_caverns_hall`.

| # | Where | Do | Expected |
|---|---|---|---|
| 1 | start | read `TruMenu.log` | `0.22.56 camera hints: 6 byte checks ok`, `0.22.56 puzzles: TruLink 0.5 byte checks 0 of 118 rows bad` |
| 2 | `l3_stairhall` (or any base unit) | Kapitel -> the chapter row that starts in `l3_chapel` / `3 Croft Manor`, right 2x | footer backup + start; log `camera hints: armed ...`, `main state 2 ... -> 0` (or `already 0`), `loading screen over ... flag off`; the intro plays with textures, no hang, **no crash after the load** |
| 3 | a room whose intro was played (villa `l3_main_bedroom`) | the Prolog row, right 2x | the intro plays again (new game data), the loading screen goes away |
| 4 | same | `Kapitel (Stand behalten)`, left to `Prolog`, right 2x | footer with the warning; `level.load` as 0.22.55 (the hold may come back - the known behaviour) |
| 5 | chapel, plates up | Kapitel -> Raetsel in der Naehe | the four wall switches `gesperrt: Platte 4834 nicht gedrueckt`, target `ma_uo_shadow_pillars 4837: Ring 4`; plates `oben, frei`; `Figur 1..4` rows with target `position_a` |
| 6 | chapel | weights on the centre plate (carry, or `Gewicht zu mir` first) | plate `unten: Gewicht ...`, switches `aus, bereit`, check row `Feuer an (Platte 4834 unten)` |
| 7 | chapel, fire lit | pull a wall switch once | log `puzzle: learned - switch ... steps link n of 4837`; that figure row now says `Schalter ... noch n x` |
| 8 | chapel, fire lit | `Figuren auf Ziel setzen`, right 2x | log `puzzle.figures ... cmd c ... sent` per step, then `every figure on its target`; the check goes `unsolved -> ... -> solved`, the pillar script opens both locks of the great shadow door (the game's own sequence); the door row lists the two lock parts as `nur Anzeige (das Spiel)` |
| 9 | chapel, fire out (centre plate up), fresh load | repeat 8 | row / footer `Schloesser erst bei Feuer`; figures move, locks stay - light the fire: they open then (P5: stored picture) - **live 16.11.: they do NOT open at the lighting, only on the next switch pull while lit (0.22.57)** |
| 10 | chapel, great shadow door opened with the turning pedestal and closing again | read the door row (target 4835) and the uber label of the pedestal | `offen 1xx Grad, zu in ~nn s`, counting down at ~3.5 degrees per second |
| 11 | chapel, door open | `Tuer offen halten`, right 2x, wait 60 s, then right (or left) | the pedestal turns fully open and stays (`HAELT`), the door stays open; after off it closes by itself; log `puzzle.hold ... settings put back` |
| 12 | chapel | `Gewicht zu mir` on a weight, then `zurueck an den alten Platz` | the weight drops ~1.5 m from Lara (in front if the yaw guess is right - note where), physics calm; then back at its old place |
| 13 | villa `l3_chamberrockhall` | switch 4617 before / after pulling | before `aus, bereit`; after: note the state text (`an` / `an - bereits benutzt`) and the target kind of the secret door (`umkehrbar` expected) |
| 14 | villa `l3_main_bedroom` | switch 4525 | its state; the house door has no graph (target kind `?`) |
| 15 | DLC 1 `dlc_caverns_hall` | pull a gate switch, read the gate row and its uber label | target kind `setzt sich nach 27 s zurueck`; the uber label still counts `noch 25 s` |
| 16 | TruLink | `mark.note 4837 test`, `mark.list`, names layer on / off, `mark.refs 4835`, `mark.clear all` | the note line under the label (also with names off), a refs note `<- 4835 m0` on 4837; a level load clears notes without `+keep` |

## 0.22.55 - Aktuelles Kapitel neu laden, flight off after a load, doppelganger_casual guard, level not found, 290 units per metre, multibody part labels, poles without a hole (2026-11-16)

Build `work\asi\menu0278`, not installed (package P2a of the workspace `docs\Pakete-1611.md`; owner notes of the
chapel / villa evening 2026-11-15). "(unproven)" marks a reason that is not proven by code / logs.

- **Kapitel: `Aktuelles Kapitel neu laden` / `Reload current chapter`** (first row, `chapter.reload`, right / X twice):
  the start of Lara's current chapter. The chapter comes from page Kapitel's own table (`kChapOrder`): Lara's unit
  (stream entry, else GameTracker+0x38), its first row (a unit with a return visit counts as its way in), then back to
  the nearest row of the same group whose heading is a chapter start (`Kapitel ...` / `Prolog ...`), else the group's
  first row - in DLC 1 / DLC 2 that is `dlc_level1_start` / `dlc_level2_start`. The unit then runs through `ChapSteps`,
  the one path of the chapter rows: `save.backup kapitel`, then in a level the pause menu's DLC start (`level.start
  dlc1|dlc2`, the new-game block: the unit's own costume, DLC 2's doppelganger) or, for a base-game chapter,
  `level.load` (debug, no story values - the only in-level path verified for those units). `Unit neu laden` stays the
  unit reload. Greyed without a level. Long menu: Level select, button `Reload current chapter`.
- **Fliegen nach Kapitel-Laden beibehalten** (`flight.keep`, `[Cheat] FlightKeepOnLoad`, default **0**, row under
  Fliegen / Flug-Tempo on page Figur, checkbox on the long menu's Cheat page): the game keeps GameTracker.cheatMode over
  a level change (15.11. 20:25: flight from a checkpoint row stayed on over the next `level.load`). With 0 every level
  load TruMenu starts ends the flight first, as `cheat.flight 0` does (cheatMode 0, message 12 (0) to the player):
  `level.load` / `level.reload` / the chapter and unit rows / `unit.go`'s load (LoadUnit), the mission start from the
  main menu and the in-level DLC start (after their refusals). Log `0.22.55 flight off before ...`. 1 = flight stays.
- **Checkpoint rows never turn flight on:** `cp.jump` ends with `player.goto <intro>` (base game: `... force`) instead
  of `dbg.cpgo` / `cheat.flight 1;player.goto`; `unit.go`'s portal path still flies Lara to the portal, so a row that
  started without flight ends with `cheat.flight 0`. A checkpoint is the game's own respawn place, on the floor
  (unproven for every checkpoint - live test 7).
- **Kostuem `doppelganger_casual` (857) gesperrt** (15.11. 22:11, `costume.set 857` in `dlc_caverns` froze the game:
  wait loop 0x5551d9 -> 0x6f5cxx, the handle resolver 0x5b39d0 always 0 - an instance that never comes; which one is
  unproven, likely the shadow weapons of message 35): the live switch to it (`costume.set`, `costume.next` when it is
  next, the page Kostueme rows / choice row) is refused unless the doppelganger flag `[[0xfadb58]+0x1244]` is set
  (DoppelgangerInit, i.e. TruDlc2Player set her up in this level). The row says `gesperrt (friert ein)` / `nur DLC 2`.
  The next-load choice (`costume.choose`) is unchanged (no freeze seen there).
- **Level not found:** `level.load` / `level.reload` / `level.start` / the chapter rows refuse a name that is neither in
  the level list (`kUnits`, PC unitlist.txt) nor a `mods\<unit>.drm` - before the backup step, with a log line
  `0.22.55 level not found`. The engine has no exists test (`Can't open file` + exit, or an endless loading screen).
- **Markup scale:** every metre text of the debug labels (`[Debug] DistMetres`: distance, `^` height, `v` depth) and the
  debug-view log lines (RoomOnly / RoomNear / OcclNear) use `kUnitsPerMetre` = 290 game units per metre - the constant
  of TruLink and ENGINE 4.3 (280 .. 310, not proven exactly). Was 100 units = 1 m: hole 4824 said `10.3m`, TruLink
  about 3.5 m. The 50-unit height threshold and the `[Debug]` distances in game units are unchanged.
- **Labels of multi-part objects** (15.11. ~23:50: the turning pedestal of `ma_rb_shadow_door_b` had no label): every
  link of a multibody object has its +0x20 at the anchor's reference point, so the six parts were drawn on one spot and
  the uber labels merged them into one `x 6`. A part (uber state b, b+0x7c = X, the instance in X's link table +0x6c /
  count +0x70 with a valid stamp) is now labelled at its model: bone 0 `[[inst+0x90]+0x30]` (the matrix the engine
  transforms object markup with, 0.22.43 W5) and named `<object> (middle dot) Teil n/N (<node>)` (n = the link index,
  TruLink's `link n`) - object names, uber labels and the Kapitel puzzle list. A bone 0 farther than 20000 units from
  +0x20 is not used. 5 byte checks (`kMbChecks`, log `0.22.55 multibody part labels ...`). Whether bone 0 sits at the
  visible part of every part model is unproven (live test 11).
- **Poles without a hole:** a `ma_pt_pole_a` whose stream unit (+0xe0) has no `ma_pt_pole_hole` and to which no
  `instanceref` member of any loaded instance points is marked `kein Loch (Original-Daten)` / `no hole (original data)`,
  on its name label and as a list row in Kapitel / Raetsel in der Naehe (within UberRadius). Not "unused": the static
  Xbox / PC cross-check of package P6 found pole 4686 listed in the manor units' shared `modifiable` script (with
  neighbour objects) - it is referenced by a script, it only has no hole / holder. Decided at run time (object names +
  script members as TruLink 0.4 reads them, at most every 2 s); no id list in the source; units that are not loaded are
  not seen. One log line per pole and verdict `0.22.55 pole ma_pt_pole_a <intro> ...`.
- Small items: `trumenu_quick_check` `menupages` wants 29 page keys (the page Erfolge of 0.22.34 had made it fail since);
  "Filter folgt Stumm": default 1 in kOpts / TruMenu.ini / switches row checked - nothing to change.

### TO TEST 0.22.55

| # | Where | Do | Expected |
|---|---|---|---|
| 1 | start | read `TruMenu.log` | `0.22.55 multibody part labels at bone 0 + unused poles: checks ok (5 rows)` |
| 2 | DLC 1, a unit after the start (e.g. `dlc_caverns`) | Kapitel -> `Aktuelles Kapitel neu laden`, right 2x | footer `DLC 1 Unter der Asche: dlc_level1_start - Sicherung, dann Start wie das Spiel`; backup `kapitel`; DLC 1 starts as from the pause menu (outfit / weapon screen) |
| 3 | DLC 2, e.g. `dlc2_ceremony_room` | same | DLC 2 start (no selection), doppelganger set up |
| 4 | base game, e.g. `l3_chapel` | same | footer names the chapter heading (`Kapitel 3.1 ...` / `Prolog`), `level.load` of its first unit |
| 5 | Figur | `Fliegen` on, then a chapter / unit row (right 2x) | after the load Lara does not fly; log `0.22.55 flight off before level.load ...` |
| 6 | Figur | `Fliegen nach Kapitel-Laden beibehalten` on, repeat 5 | flight stays on; TruMenu.ini `FlightKeepOnLoad=1`; switch it off again |
| 7 | Kapitel, a unit's `CP` row (flight off before) | right 2x | Lara at the checkpoint, on the floor, flight off afterwards (shortcut log ends with `cheat.flight 0`) |
| 8 | DLC 1, page Kostueme | `Alle Kostueme` -> `doppelganger_casual` | grey `gesperrt (friert ein)` / `nur DLC 2`, right = the reason in the footer, **no freeze**; the choice row skips it |
| 9 | DLC 2 start (doppelganger) | same row | not greyed (flag set), the switch works as before |
| 10 | command line | `level.load xyz_nichtda` | `refused: level not found ...`, nothing loads |
| 11 | l3_chapel, Debug view names + uber labels | look at the shadow door | one label per part; the pedestal labelled `ma_rb_shadow_door_b ... Teil 2/6 (start / turn)` at the pedestal |
| 12 | l3_chapel, hole 4824 / pole 4823 | read the label metres | about 3.5 m / 2.5 m (was 10.3 m / 7.1 m) |
| 13 | l3_secretchamber, pole 4686 | names layer / Kapitel -> Raetsel | `kein Loch (Original-Daten)`; log `0.22.55 pole ma_pt_pole_a 4686 ... NO HOLE`; the chapel pole 4823 is NOT marked |

## 0.22.54 - two crash fixes (sub-group mute, sonar close after extra loads), sound switches reset at start, Menue-Musik (2026-11-15 evening)

Build `work\asi\menu0277`, not installed. Workspace finding `docs\Befund-TruMenu-02254-1511.md`.

- **Crash TruMenu+0x13aec6 (19:48, main menu, Stumm / Solo / Musik -> stumm):** every `snd.mute sub:<sub-group>`
  (0.22.53 `snd.hear <sub> stumm`) crashed - the log line's `%s` took `kHow[7]`, one past the end of the 7 texts (the
  sub-group kind had none), i.e. the bytes `ever` of the first text as a pointer. One text per rule kind now
  (`kW6Kinds`, `static_assert`), the index checked. All printf-style functions carry `_Printf_format_string_`; the
  check `work\fmt_1511\Test-TruMenuFormats.ps1` (MSVC `/analyze`, ImGui text calls included, with its own negative
  probe) found 2 harmless sign mismatches (fixed) and nothing else.
- **Crash tru+0x14f05d (20:07, closing the sonar after "alles Verbundene laden") and the stop after one extra step
  (20:04 chapel):** the game's find 0x6e2a60 appends a new list entry whose constructor never sets the load handle
  +0x88; the extra-load step read that heap garbage as "requested already" - no load, no further step through that
  unit (the villa stayed unloaded), and the close released the garbage (1.0f) as a handle. A new entry now gets +0x88 /
  +0xb2 / +0xb4 = 0 at once (as the game's "no file" path); 6 more byte checks (23); the open line names
  `new list entries n (handle cleared)`. The two switches stay default off.
- **Ton-Schalter beim Start zuruecksetzen** (`snd.resetatstart`, `[Sound] ResetAtStart`, default 1, last row of the
  Stumm / Solo block): every start begins with the game's sound - `[Media] MuteMusic`, `[Media] MuteAmbient`,
  `[Sound] ReverbOff` go to 0, also in TruMenu.ini; the Stumm / Solo rules start empty anyway. Kept: the log filters
  (Filter (Zeigen), LogHideSubs, LogOnlyAudible, LogFollowMute ...), Hall folgt Stumm, Sonar-Ton aus. Off = 0.22.53.
  Log line after `loaded`: `0.22.54 sound switches at start: [Media] MuteMusic 1 -> 0, ...`.
- **Menue-Musik (g1):** a sub-group of its own for group 1 (the main theme stream of the menu / costume screens);
  `Musik` is g2-3, g10-12 now. Group 1 is the parent of all music groups, so it is never muted as a group - its voices
  (the two stream voices, wave -1) are muted per channel.
- The heading row `-- Schnell-Hoeren` is gone. "Filter folgt Stumm": no fault in the value / display path (log 19:43:
  the row switched off / on / off / on by the bar); the start line `0.22.50 sound log: ...` names `LogFollowMute` now.
- **joint.set / Raetsel "loesen" (20:28 l3_chapel, `ma_rb_shadow_door_b` rail: from -0.84 to -1115 instead of 60.05,
  outside its limits [0, 948]):** the lock jumped to the target and replaced the joint's limits. Now the target is
  clamped into the joint's own limits, the lock point moves from the value towards the target (hinge 90 deg/s, lead
  10 deg; rail 300 units/s, lead 30 units), and the drive stops at once (saved limits back) when the value leaves the
  limits, moves away from the target (3 deg / 10 units farther than its best) or overshoots it (2 deg / 5 units). One
  log line per tick `joint.set <intro> joint <n> tick <s>: value, velocity, lock, target, best distance` (at most 400).
  A drive that stood at the target without a node change marks its row `Bereich hier nicht scharf (versucht)` - no
  second "loesen" in that node.

### TO TEST 0.22.54

| # | Where | Do | Expected |
|---|---|---|---|
| 1 | start (INI with MuteMusic=1, MuteAmbient=1, ReverbOff=1) | read `TruMenu.log`, TruMenu.ini | `0.22.54 sound switches at start: [Media] MuteMusic 1 -> 0, [Media] MuteAmbient 1 -> 0, [Sound] ReverbOff 1 -> 0`; music, ambience, reverb audible; the INI holds 0; filters as before |
| 2 | main menu, box on | Stumm / Solo / Musik / Menue-Musik (g1) -> stumm, then solo, then hoerbar | no crash; main theme silent / alone / back; log `snd.mute sub:mu_menu 1 ... the sub-group: ...` |
| 3 | main menu | Musik (ganze Art) -> stumm / hoerbar, Musik (g2-3, g10-12) -> stumm | no crash; whole music off / on |
| 4 | Ton-Log groups | open | no `-- Schnell-Hoeren`; Stumm / Solo ends its first block with `Ton-Schalter beim Start zuruecksetzen` (an) |
| 5 | same row off, restart | | Musik aus / Ambient aus / Hall aus kept as before (log `off ([Sound] ResetAtStart=0) ...`) |
| 6 | l3_chapel, Sonar komplett + alles Verbundene laden | open the sonar, wait, close it, close TruMenu | the whole villa (main hall, bedroom hall, bedrooms) on the map; log `sonar load open n: ... extra n (...), new list entries n (handle cleared)`; close: no crash |
| 7 | same | close the sonar at once while it still loads | no crash, no hang |
| 8 | Filter (Zeigen) / Filter folgt Stumm | look after a start | the row shows the INI value (start line `LogFollowMute 1`) |
| 9 | l3_chapel, Kapitel / Raetsel in der Naehe, row `ma_rb_shadow_door_b` G2 | right 2x | the door slides to ~60 and stops (tick lines in the log, no value < -5 or > 953); if the node does not change: after ~2 s `stood 1.5 s at the target ...` and the row reads `Bereich hier nicht scharf (versucht)` |
| 10 | same, Lara standing in the door's way | right 2x | `stopped: value ... moves away from the target` within a few ticks, the door back inside its limits, no fling |

## 0.22.53 - sound log trees (Filter / Stumm-Solo per kind and sub-group), the kind Waffen, Lara by source, the sonar loads more areas, markups in the sonar view (2026-11-15)

Build `work\asi\menu0276`, not installed. Workspace finding `docs\Befund-TruMenu-02253-1411.md`.

- **Ton-Log layout (the owner's, binding):** Spiel-Einstellungen / Ton / `[-] Ton-Log (unten rechts)` -> the settings rows
  (Ton-Anzeige, Wiederholungen, Nur hoerbare, Hoechstens so weit, FMOD channels to the log, hooks state) ->
  `[+] Filter (Zeigen)` (the log display only - a hidden kind stays audible) -> the plain heading **Schnell-Hoeren** ->
  `[+] Stumm / Solo` (the sound only - a muted kind stays in the log unless filtered): Alles zurueck, Neuester Ton solo,
  Hall folgt Stumm, Hall aus, then the kinds. Both trees have the same structure: a collapsible kind (Lara, Waffen,
  Gegner, Welt / Umgebung, Objekte & Mechanik, PDA / UI, Sprache, Musik) -> one row for the whole kind -> one row per
  sub-group (38 named sets of the game's sound groups, the group numbers in the row name). Filter rows are bool
  (`snd.logcat <kind>`, `snd.logsub <sub>`), Stumm / Solo rows are value rows `hoerbar / stumm / solo`
  (`snd.hear <kind|sub> normal|stumm|solo` = `snd.mute` / `snd.solo` `cat:` / `sub:`; one solo at a time). Nesting levels
  2 / 3 for groups (`kQfLv2` / `kQfLv3`); all new groups start closed.
- **Kind Waffen:** groups 58 / 59 (draw & cock), 62 (shots), 63 (reload & grenades), 61 (brass), 51 / 52 (impacts &
  whiz) were Lara's - "Stumm: Lara" muted the weapons too. Lara's voice 68 / 69 and the DLC 2 player groups 77 (voice,
  `VO\Lara` streams) / 78 (player foley of `doppelganger_casual`) are Lara's now (was speech / "Effekt").
- **Group 14 by source:** a sound without an Assign plays in group 14 "world default" (e.g. drawing the weapon from
  Lara's anim event). If its source is Lara or her gear (hook E1 / the owner list; gear = instance +0x54 = the player)
  it is **Waffen / Laras Waffe ohne Gruppe** when the owner object is `wp_*` or the wave is one the data puts only into
  weapon groups (174 waves; game data, so not in the source: the optional `TruMenu.weaponwaves.txt` next to tru.exe,
  made from the own game files by `work\menu53_1411\weapon_waves.py`, log line `0.22.53 sound kinds: n weapon waves`;
  without it only a `wp_*` owner counts), else **Lara / Ausruestung**. While a Lara / Waffen /
  Welt rule or solo is on, the owner list is walked about once a second also with the box closed.
- **Filter folgt Stumm** (`snd.logfollow`, `[Sound] LogFollowMute`, default 1): what Stumm / Solo silences (TruMenu's
  kind / sub-group rules, "Musik aus", the solo - also of a wave) leaves the box. Off = muted sounds stay visible.
  "Nur hoerbare Zeilen" stays separate: it follows FMOD's state now (whoever muted / paused it, the game's pause, silent
  lines), not TruMenu's switches.
- **Monitor:** "Aktive Stimmen" lists the voices under `-- <kind>: n, m spielen` and `--    <sub-group> (groups): n`;
  history and box lines name `kind / sub-group`.
- **Sonar loads more** (with "Sonar komplett", default off): `Sonar: Nachbar-Stockwerke nachladen` (`[Sonar]
  LoadNeighbourFloors`, one step further than the game: the neighbours of its off-floor neighbours, 0 .. 5 units; shown
  with "Alle verbundenen Bereiche") and `Sonar: alles Verbundene laden` (`[Sonar] LoadAllConnected`, every
  portal-connected map unit of the level, up to 22 units / 16 MB / + 0 .. 2 s at the open). One call redirect R1
  0x6e4e3f (the game's neighbour rule first, then the game's own find / request functions inside the load callback,
  only while the game is paused in the sonar's load mode and no PDA map heap exists), written only while the sonar is
  closed; caps `[Sonar] LoadMaxUnits` (24) and TriangleCap; the game's close frees them. 17 byte checks
  (`0.22.53 sonar load: checks ok (17 rows)`), one log line per open `0.22.53 sonar load open n: ...`; info row
  "Sonar-Laden: Stand". Level 2 as a whole has 350 712 faces - raise TriangleCap to 400000 there.
- **Markups in the sonar view:** the markup layer projects with the camera matrix 0xe804a0 while the sonar is open
  (like the trigger layer; 0xa038f0 stays the paused gameplay camera), log line `0.22.53 markup: the sonar is open ...`.

### TO TEST 0.22.53

| # | Where | Do | Expected |
|---|---|---|---|
| 1 | start | read `TruMenu.log` | `0.22.53 sonar load: checks ok (17 rows)` |
| 2 | Spiel-Einstellungen / Ton / Ton-Log | open the groups | settings, `[+] Filter (Zeigen)`, `-- Schnell-Hoeren`, `[+] Stumm / Solo` (Alles zurueck, Neuester Ton solo, Hall folgt Stumm, Hall aus, kinds); each kind opens to its sub-groups |
| 3 | a level with a weapon | Stumm / Solo / Lara -> stumm, shoot | shots audible (Waffen), Lara's breath / steps silent |
| 4 | same | draw the weapon, box on | the line reads `Waffen / Laras Waffe ohne Gruppe g14` (or `Lara / Ausruestung g14` for gear); Waffen -> stumm silences it |
| 5 | DLC 2 | box on, walk / breathe | g78 / g77 lines read `Lara / Koerper / Foley` / `Lara / Stimme` |
| 6 | box on, Lara stumm | Filter folgt Stumm on / off | on: Lara lines gone, filter line `Stummes ausgeblendet`; off: they stay (outline box) |
| 7 | Filter / Gegner / one sub-group off | fight | only that sub-group's lines gone, still audible |
| 8 | Ton-Monitor / Aktive Stimmen | look | `-- Lara: n, m spielen`, `--    Koerper / Foley (...)`, then the voices |
| 9 | water wheel or manor, Sonar komplett + Alle verbundenen Bereiche | Nachbar-Stockwerke nachladen on, open the sonar | more areas, log `0.22.53 sonar load open 1: scope neighbour floors ... extra n` |
| 10 | same | alles Verbundene laden on, open | the whole level, open < 2 s longer; close + walk on: no hang |
| 11 | debug view + markups | open the sonar, pan | markup lines move with the map like the triggers; log `0.22.53 markup: the sonar is open` |

## 0.22.52 - reverb mark per line, the whole DSP graph in the monitor, the sonar's real distance dimming, a colour per area, the puzzle row fix (2026-11-14 late)

Build `work\asi\menu0275\TruMenu.asi`. Workspace finding `docs\Befund-TruMenu-02252-1411.md`.

- **DSP graph (analysis, live 22:02 read only + static):** 189 DSP units - one game `SFX Reverb` (13 sends, -> master
  head 1.0), two `FMOD ParamEQ` (groups 58 / 59: group head -> EQ -> group head = inserts behind the channels' muted
  dry connections), three stream codecs, 162 channel group heads, target, sound card. No echo / chorus (groups 77 / 78
  have no DSP on PC), no oscillator playing, no other send. Static: the game creates DSPs only at 0x586fda (the reverb),
  0x5839f3 (oscillator, played by System::playDSP as its own channel - FMOD's channel mute holds) and 0x5876df (kinds
  1 .. 11 for groups / SoundPlex DSP nodes, put in with ChannelGroup::addDSP = inserts); DSP::addInput only at 0x58223b
  (reverb -> master) and 0x584188 (the voice sends). **The reverb send stays the only path past the mute** - no second
  effect needs a mute rule.
- **Reverb mark per line** (box and monitor): arcs = the send reaches the reverb; arcs struck through = the game would
  send (params +0xc > 0) but "Hall folgt Stumm" / "Hall aus" hold it at 0; a dot = no send. Legend in the help line of
  "Ton-Anzeige unten rechts" and "Aktive Stimmen".
- **Monitor:** a row `DSP-Graph: n Einheiten, m Effekte; Hall-Eingaenge, Updates/s, sofort auf 0` and one row per effect
  (name, kind, the head it feeds, level, inputs, active, voices of its group); info row "DSP-Graph: Stand"
  (`snd.dspgraph`). The walk runs every 2 s only while the monitor or the box is shown.
- **Hall folgt Stumm at once:** a muted voice's send is set to 0 on the game thread within 50 ms (W10Sweep); the game's
  next voice update (once per frame, 0x47ad8f -> 0x591e80 -> 0x591480) keeps it at 0 through R1. The count of voice
  updates per second is measured (log line `0.22.52 reverb: voice updates ...`).
- **Sonar: Abblenden Ferne** now drives the real dimming: the face shader (PS lib 192 of materials 3348 / 3349) darkens
  with the depth - a 1/d falloff down to half (floor c110.x 0.5) and a fade to black between c108.w and c109.w (3348:
  500 .. 600 m, 3349: 200 .. 300 m). `aus` = no falloff, no fade; `n m` = no falloff, black from n/2 to n m; `Spiel` =
  untouched. The fog is put out for every value != 0 (the game's fog call is a hard step at 655 m). Only the three
  values of both materials are written, over the game's values only, back at `Spiel`, on a material change and at
  unload. 6 byte checks (`0.22.52 sonar fade (shader values): checks ok (6 rows)`).
- **Sonar: Bereichsfarben** (value row, `[Sonar] TintOthers` 0 / 1 / 2): aus / ein Farbton (amber, as 0.22.51) / je
  Bereich = a muted colour per area (amber, teal green, violet, rose, olive, slate blue, sand, rust - each 40 % from the
  game's cyan), Lara's area stays cyan; the legend `colours: <unit> <colour>, ...` is in "Sonar-Ansicht: Stand".
- **Kapitel / Raetsel (j):** the l3_secretchamber pillar (free hinge, limits off) offered `joint.set ... 5000.50` - the
  middle of the open range [1, 10000) of the motion detector Not_Rotating -> Rotating - and our lock lo = hi = 5000.5
  degrees stayed after the node change, so the pillar spun through the geometry. Now: an open-ended range on a free hinge
  is list only ("Bewegungs-Melder, kein Ziel"); every range is cut to the joint's own limits first
  (ma_rb_chapel_gate_round At_Top: 861 -> 782.2 inside [0, 790.1]); an open bound is replaced by the near bound + 2
  degrees / 5 units; after a node change our lock is taken back when it still stands. The pillar's real solution is not
  a joint range of its uber graph (only Not_Rotating / Rotating) - no "solve" row for it.

### TO TEST 0.22.52

| # | Where | Do | Expected |
|---|---|---|---|
| 1 | start | read `TruMenu.log` | `0.22.52 sonar fade (shader values): checks ok (6 rows)`; later `0.22.52 DSP graph (first walk ...)` with `SFX Reverb` and `FMOD ParamEQ` |
| 2 | DLC 2 Eitr beam, box + monitor | everything muted, "Hall folgt Stumm" on | beam lines: struck arcs; monitor: struck arcs before `stumm`; tone gone; log `0.22.52 reverb: voice updates ... per voice and second` |
| 3 | same | "Hall folgt Stumm" off | arcs (not struck), tone back |
| 4 | Ton-Monitor | look at the rows under `Hall (Spiel-Reverb)` | `DSP-Graph: ...` + `DSP SFX Reverb (Hall)` + 2 x `DSP FMOD ParamEQ` (where groups 58 / 59 are loaded) |
| 5 | DLC 1 water wheel, sonar | "Sonar: Abblenden Ferne" -> aus | the far map no longer darkens (screenshot); log `0.22.52 sonar fade (sonar.fade): material 0 ... c110.x 0.50 -> 1.00` |
| 6 | same | -> 50 m, then X | 50 m: black from 25 m; X = Spiel: the game's look, log `... 3 of 3 game values back` |
| 7 | sonar | "Sonar: Bereichsfarben" -> je Bereich | every area its own soft colour, Lara's cyan; "Sonar-Ansicht: Stand" lists `colours: ...` |
| 8 | l3_secretchamber (reload first: the pillar of 22:13) | page Kapitel / Raetsel | the pillar rows read `Bewegungs-Melder, kein Ziel`, no `rechts 2x` |
| 9 | a rail puzzle (chapel gate / bend switches) | right 2x | target inside the joint's limits; after the node change `... solved step` (with `our lock was still on the joint` if it stood) |

## 0.22.51 - sonar: fade of the far map, one area, other areas tinted, why one is missing; base PDA in DLC 2; X = default; DLC start from a level; the game's reverb follows mute (2026-11-14)

Built into `work\asi\menu0274`, not installed, no live test (owner wishes of 14.11. evening; report in the workspace
`docs\Befund-TruMenu-02251-1411.md`). 22 byte checks `kS5Checks` (`work\menu51_1411\precheck_02251.txt`, 0 mismatches
on `data\pc\tru.exe`; start line `0.22.51 sonar view / base PDA: checks ok (22 rows) ...`), three 5-byte call redirects
(only while an option needs them) and one script word (only with the DLC g_pda).

- **"Sonar: Abblenden Ferne"** (`sonar.fade`, `[Sonar] FadeFar`, value row: aus / Spiel / 800 / 400 / 200 / 100 / 50 /
  20 m; page Fixes: -1 .. 2000). What the code shows: every map vertex gets the same colour (`[0xee03bc]`, no distance
  term on the CPU); the sonar view sets the camera far plane = tuning +0x10 (live 100000) and a fog override
  `0x5bfe40(r, g, b, 65536.0, 65536.0)` - fog near == far, so the engine's linear fog is degenerate (1 / (far - near) =
  inf). The game's own fade is therefore not a linear fog; most likely the shading of the sonar materials (lit by the face
  normal) - **not proven**. The row drives the engine's fog for the sonar: 0 = the game's call untouched, n m = fog from
  n/2 to n m into the background colour, aus = fog 90 / 100 km. TO TEST 1 / 2 decide whether "aus" also removes the
  game's own fade; if not, the next step is the material / shader of tuning +0x34.
- **"Bereich anzeigen"** (`sonar.area`, value row: alle + every unit of the sonar's own list): only that unit is drawn
  (the frame's draw call 0x6e42ac -> S5UnitStub skips the others). No load (only units the sonar loaded itself), the
  camera is not moved (the view centre comes from the game's pan input - no safe way to set it was found; documented).
  Kept for the session (not in the INI); X = alle.
- **"Sonar: andere Bereiche einfärben"** (`sonar.tint`, `[Sonar] TintOthers`): Lara's unit (the sonar's open unit) in the
  game's cyan, every other drawn unit with the draw colour 40 % towards amber (only for that unit's draw call; the game's
  value back right after). Partly revealed edges (game mode without "Sonar komplett") stay cyan.
- **Why a unit is missing** (helheim01 without helheim02): the view distance is 100000 (+4000) live - not the reason.
  0x6dfa60 drops a triangle when `(v0 - view centre) . view axis < -4000` - everything more than 40 m in front of the view
  centre (towards the camera) is cut, depending on where the camera looks. The sonar-open log line now has a second line
  `0.22.51 sonar view (open): centre ..., axis ..., per unit plane / dist, origins behind the cut`; "Sonar: warum fehlt
  ein Bereich? (Log)" (`sonar.why`) writes it at any moment (turn the camera, press it again).
- **"Shadow-PDA durch Basis-PDA ersetzen"** (`pda.basepda`, `[PDA] ShadowPdaAsBasePda`): with the DLC g_pda, DLC 2 shows
  the base PDA (Croft VX2, sonar map) instead of its journal PDA. TruMenu finds the resident script 3347 through the
  ScriptSection hash map (FindResource 0x551560 read by hand: `[0x8a6ed0]` buckets, `[0x8a6ed8]` table, object vtable
  0x84e4d4, +8 = the section bytes), recognises f1 `level tag == "dlc2"` by its 19 words + 'dlc2' (first at +0x2294, else
  a scan of 64 KiB) and writes `04000000` over `04000001` - only in a level, world running, sonar and TruMenu menu
  closed; back on off and at unload, only over its own word. The PC's own g_pda (installed today) has no DLC branch: the
  row is greyed with "keine DLC-PDA geladen", nothing is written. Info row "Basis-PDA: Stand" (`pda.state`).
- **X on a value row = its default** (owner wish): every `kQbValue` row (default = its INI default / neutral value;
  volumes, mouse, graphics and the pass mask have none - the footer says so) and every int / choice switch of
  `TruMenu.switches.txt` (page Fixes, pinned rows, kQbSwitch rows of page Tests; default = the file's default column).
  The footer shows `X: Standard` on such rows.
- **Command line (L3)**: `level.start ` suggests every usable unit (as `level.load`); `level.load ...` in the main menu
  (where it is refused since 0.22.46) suggests `level.start <unit>` lines.
- **Kapitel: DLC 1 / DLC 2 from inside a level** (owner wish, was refused since 0.22.50): the two DLC start rows run
  `save.backup kapitel;level.start dlc1|dlc2` in a level too; `level.start` there = the game's own DLC start from the
  pause menu (RegisterAcceptChanges case 8 as the title update / TruDlc2Player 0.6: `f27 UILoadLevel(unit, 1 for DLC 1 /
  0 for DLC 2, 0, 1)` - the new-game block zeroes the chosen-costume words -> the unit's default outfit, DLC 2 = the
  doppelganger - then stdscreenmgr f7 + f19; the case's UI-stack call only when the game's own pause menu is open).
  Refused only during a cutscene or while a level change waits. 4 more byte checks at the first use
  (`work\menu51_1411\evidence_dlcstart_level.txt`, 12 rows, 0 mismatches).
- **The game's reverb (Eitr beam: "alles stumm", a tone still)** (workspace `docs\Befund-Ton-ausserhalb-FMOD-1411.md`,
  live 20:50 - 21:10): the game feeds every pool voice also into its own FMOD DSP "SFX Reverb" (holder `[0xccde98]`, an
  input of the master group's head). The send (voice +8) leaves the channel's DSP head (real +0x98) **before** the dry
  connection, so FMOD's mute never reaches it; its level is the game volume, set again on every voice update (0x591591)
  and at the attach (0x5841bf). 11 byte checks `kW9Checks` (`work\menu51_1411\precheck_02251_reverb.txt`).
  - **"Hall folgt Stumm"** (`snd.reverbmute`, `[Sound] ReverbFollowsMute`, default 1): the two `call 0x7b9ff3` sites ->
    W9SendStub: a voice whose channel FMOD has muted (bit 3 - every TruMenu mute: Alles stumm, category, solo, sonar
    sound off) sends 0 into the reverb; then the game's setMix. Takes effect at the voice's next update.
  - **"Hall aus"** (`snd.reverboff`, `[Sound] ReverbOff`): the reverb -> master connection to 0 (the level before kept,
    set back on off) - the simple switch; audible sounds lose their reverb too.
  - **Audible** in the box, the monitor and "Nur hörbare Zeilen" = not paused and (dry mix > 0 or (send > 0 and reverb
    out > 0)); muted lines with a live send say `stumm, Hall 0.34` and keep a filled box; the monitor has a row
    `-- Hall (Spiel-Reverb) -> Master 1.00 | Sends n (m stumm), max x`. Info row "Hall: Stand" (`snd.reverb`).
  - Rows on Spiel-Einstellungen / Ton (after "Ambient aus") and in Paket B2 (B2.8 / B2.9).
- Rows: Spiel-Einstellungen / PDA / Sonar and copies in Paket G (G.9 - G.14). Options `[Sonar] FadeFar`, `TintOthers`,
  `[PDA] ShadowPdaAsBasePda` (live, switch group `tmsonar`). Items `sonar.fade`, `sonar.tint`, `sonar.area`, `sonar.why`,
  `sonar.view`, `pda.basepda`, `pda.state`. Checks: `trumenu_ini_check` `check_02251` (+ `check_0213` X rule,
  `check_02240` enum, `check_02244` key count, `check_02250` version part adapted); negative cases
  `work\menu51_1411\m51_negative_tests.py`; compiled stubs `work\menu51_1411\s5_stub_bytes.py`.

### TO TEST 0.22.51

| # | Where | Do | Expected |
|---|---|---|---|
| 1 | start | read `TruMenu.log` | `0.22.51 sonar view / base PDA: checks ok (22 rows); [Sonar] FadeFar 0, TintOthers 0, [PDA] ShadowPdaAsBasePda 0` |
| 2 | DLC 1 water wheel, PDA -> Sonar (FullMap on) | "Sonar: Abblenden Ferne" -> aus, then 50 m, then X | log `0.22.51 sonar view (sonar.fade): ... F1 0x6e4d94 / F2 0x6e4bf9 -> S5FogStub`; 50 m: the far map fades into black; **aus: does the game's own dimming of far meshes go away?** (screenshot - decides the cause); X: `Spiel`, `the game's calls` |
| 3 | same | "Bereich anzeigen" right / left | only `dlc_pillory` (etc.) drawn, the others gone; `alle` = everything again; X = alle; no load in the log |
| 4 | same | "Sonar: andere Bereiche einfärben" on | water wheel cyan, pillory / caverns amber-tinted; off = all cyan |
| 5 | helheim01 (Arena 1a area), Sonar | look for helheim02, then "Sonar: warum fehlt ein Bereich? (Log)", turn the camera, again | line `0.22.51 sonar view (open)` / `(sonar.why)`: helheim02 `plane` < -40 m = behind the cut (then it appears when the camera turns) - or `UNPLACED` / `(other floor)` |
| 6 | any page | X on "Zeitlupe", "Teaser-Anzeige", "Sonar komplett: Dreiecks-Grenze", "Höchstens so weit weg (m)" | each goes back to its default (1.00 / 12 / 300000 / 0), footer `X: Standard`; a volume row: "kein TruMenu-Standard" |
| 7 | PDA / Sonar | "Shadow-PDA durch Basis-PDA ersetzen" (PC g_pda, today) | greyed, "keine DLC-PDA geladen"; "Basis-PDA: Stand" says so; nothing in the log but `no DLC branch` |
| 8 | after the DLC g_pda is installed, DLC 2 | switch on, then open the PDA | log `base PDA: ... f1 word ... 0x04000001 -> 0x04000000`; Croft VX2 PDA with SONARKARTE; off = the journal PDA again at the next open |
| 9 | main menu, L3 command line | type `level.start ` / `level.load l7` | unit suggestions; `level.load` turns into `level.start <unit>` lines |
| 10 | base game level (e.g. Arena 1a), page Kapitel | "DLC 2 Laras Schatten" right twice | `level.start dlc_level2_start in a level ... f27('dlc_level2_start', 0, 0, 1)`; DLC 2 loads with the doppelganger (`DoppelgangerInit`), shadow meter, no gold bikini; objectives DLC 2 |
| 11 | DLC 1 level, page Kapitel | "DLC 2 ..." right twice, then from DLC 2 "DLC 1 ..." right twice | DLC 2 as in 10; DLC 1: the outfit / weapon screen, Lara without doppelganger mode (`arena.mode`: doppelganger byte 0), DLC 1 objectives |
| 12 | main menu, page Kapitel | "DLC 2 ..." / "DLC 1 ..." | as 0.22.50 (mission start), unchanged |
| 13 | a level, during a cutscene | a DLC row | refused: "a cutscene plays ..." |
| 14 | start | read `TruMenu.log` | `0.22.51 reverb: checks ok (11 rows); [Sound] ReverbFollowsMute 1, ReverbOff 0`; at the first pad poll `0.22.51 reverb (run time): R1 0x591591 / R2 0x5841bf -> W9SendStub ...` |
| 15 | DLC 2 at the Eitr beam, Ton-Monitor | "Hall folgt Stumm" **off**, "Stumm: Welt / Umgebung" on | the beam lines: `stumm, Hall 0.xx`, filled box; monitor row `Hall (Spiel-Reverb) -> Master 1.00 \| Sends 15 (15 stumm) ...`; the tone is **still there** (as 0.22.50) |
| 16 | same | "Hall folgt Stumm" **on** | within a second the tone is **gone**; lines `(stumm)` with empty boxes; `Hall: Stand`: sends set to 0 counts up (B2.8) |
| 17 | same, nothing muted | "Hall aus" on / off | on: the beam sounds dry (no reverb), monitor row `-> Master 0.00 (Hall aus)`, log `Hall aus - reverb -> master ... -> 0`; off: back to 1.00 (B2.9) |
| 18 | optional, outside | `work\ton_1411\Get-AudioSessions.ps1` with all muted | tru.exe session peak about 0 with "Hall folgt Stumm" on (was 0.28 .. 0.38) |

## 0.22.50 - the sound log readable, every FMOD channel, two source hooks, one Ambient aus, Kapitel from the main menu (2026-11-14)

Built into `work\asi\menu0273`, not installed, no live test (owner live wishes of 14.11.; report in the workspace
`docs\Befund-TruMenu-02250-1411.md`, design `docs\Befund-FMOD-Kanaele-1411.md`). 27 byte checks `kW8Checks`
(`work\menu50_1411\precheck_02250.txt`, 0 mismatches on `data\pc\tru.exe`; start line `0.22.50 sound log: checks ok (27
rows) ...`), two small code redirects (V1 5 bytes, E1 6 bytes; only with `[Sound] SourceHooks=1`, the default).

- **The bottom-right box, line by line** (`snd.list` + `snd.logview`): `[box] [kind icon] [loop mark] 19:14:02
  viking_axe_hit ×3  <- viking_thrall #8783  |  g29 Gegner-Ausrüstung  12 m`.
  - The **box** is FMOD's own state, not TruMenu's rule: filled = audible, an outline = muted (ChannelI +0x74 bit 3 =
    FMOD's effective mute - the channel's own bit or a muted channel group above it), as every bool row of the bar.
    It is read without an FMOD call (handle -> ChannelI exactly as the validator 0x7c7e5a: slot = handle >> 16 & 0xfff,
    `[SystemI+0x14c] + slot * 0x1b8`, the full handle at +0x70) at the start and every 200 ms while the channel lives;
    an ended sound keeps its last state.
  - The **group** as text (`g29 Gegner-Ausrüstung`, `g69 Lara-Stimme`, `g14 Welt-Standard` - the monitor's table).
  - The **loop mark** (an open circle with an arrow, draw-list primitives - the bar font has no such glyph): the real
    channel's mode +0x64 has FMOD_LOOP_NORMAL 0x2 / FMOD_LOOP_BIDI 0x4 (getter 0x7c9863, copied from the sound at the
    channel start 0x7c88ba).
  - **Repetitions collapse** (`[Sound] LogCollapse`, default 1): same wave + same source (a stream: same name) = one
    line with `×n` and the newest time; every new start moves it to the top. 0 = one line per start (0.22.47).
  - **"läuft gerade"** block on top: the looping channels now (from the voice list), one line per wave + source with
    `×n` while they play; below only the new sounds.
  - Header: `(n voices, k playing; FMOD u, others x)`; a yellow filter line names what is hidden.
- **Source** (`[Sound] SourceHooks`): two `call rel32` redirects through AiPatch (only over the game's rel32 - another
  value = refused, nothing written, one line; back only over ours, at unload `W8Shutdown`), written once on the game
  thread (first pad poll):
  - **V1 0x591351** = `call VoicePool::Play` inside the wave node ctor 0x591220 (esi = the node; node +0x10 = the
    emitter = the ctor's 4th argument). `W8PlayStub` calls Play with the same argument (thiscall, `ret 4`), then
    records {voice, voice +4 = its channel, emitter} - exact for every wave, also under inner SoundPlex nodes where the
    0.22.47 params walk gave "emitter ?".
  - **E1 0x5b99fc** = the 6 bytes right after `call 0x5935d0` (the emitter create, 0x5b99f7) inside the anim sound
    event 0x5b99c0 (`[ebp+0xc]` = the instance): `mov eax,[esp+0x18]; test eax,eax` (the handle the create wrote) ->
    `call W8EmitStub; nop`. The create call itself stays the game's: **TruTrace** (installed) tells this anim sound
    branch by that call's return address 0x5b99fc and checks the bytes up to it - a redirected call would hide it.
    `W8EmitStub` does the same mov / test (one return address deeper: `[esp+0x1c]`) around the record {emitter ->
    instance, intro, object, section id}. These emitters leave `[inst+0x248]` at once (payload byte 1 bit 0, 0x5b9aad)
    - the 0.22.47 list could never name them. A lookup trusts a record only while the emitter still has the emitter
    vtable 0x851240 and the same section id. Written by `W8E1Set` only over the game's 6 bytes (read back), back only
    over ours.
  - Both stubs keep every register and the flags as the game's code would; their compiled bytes are checked by
    `work\menu50_1411\stub_bytes.py` (one match each, both callbacks `__stdcall` with `ret 8`).
  - Source text: the player instance = `Lara`, else `<object> #<intro>`; then the owner list of `[inst+0x248]`;
    `Level / Skript` only when that list is fresh (else `Emitter (Quelle offen)` - no wrong answer).
- **Faster menu** (owner: "Menü wird langsamer"): `W7OwnBuild` (a walk over every instance) runs at most once a second
  and only while the box or the monitor rows are drawn (was every 250 ms whenever a source was asked); `W6EmitterOwner`
  (one more walk over every instance per watched-wave start) is gone - the wave 10 log line takes the source from
  hook E1 / the owner list.
- **Filters** (bar page Spiel-Einstellungen / Ton / **Ton-Log (unten rechts)**, items, live, INI-backed - the items
  write TruMenu.ini, `W8ReadSwitch` re-reads it about once a second): per kind show / hide (`snd.logcat
  <lara|enemies|world|objects|ui|speech|music> [1|0]`, `[Sound] LogLara` .. `LogMusic`), `snd.logaudible`
  (`LogOnlyAudible`), `snd.logcollapse` (`LogCollapse`), `snd.logdist <m>` (`LogMaxDist`, a switch row). The kind of a
  sound comes from its group (`kW8GroupCat`, proposal by group content: Lara = body / gear / weapons, enemies = creatures
  + enemy gear / voices, world = ambience 14 .. 24 + effect nodes, objects = mechanisms / traps / debris / explosions,
  PDA / UI = HUD / menu / PDA / binoculars, speech = voices / Lara's voice + hints / radio / cutscenes) - the music /
  speech slider categories win.
- **Quick hearing** (same group): per kind **Stumm** (`snd.catmute <kind> [1|0]` = `snd.mute cat:<kind>`) and **Solo**
  (`snd.catsolo <kind> [1|0]` = `snd.solo cat:<kind>`), **Neuester Ton solo** (`snd.solonew`: the wave, else the emitter,
  of the newest start = the top line), **Alles zurück** (`snd.mute all 0`). A category rule mutes (a) every largest
  sub-tree of groups that lies wholly in the kind with FMOD's `ChannelGroupI::setMute` (parent = group entry +0x68; 57
  PDA is no such sub-tree - its child 70 is Lara's hints), so channels started later and **channels outside the voice
  pool** in those groups are muted too, (b) every pool voice of the kind per channel, (c) every used FMOD channel outside
  the pool (oscillator / DSP, `SystemI+0x150`) of the kind through its own handle (ChannelI +0x70) - never over a
  foreign mute bit, back only what TruMenu muted. Music = the one "Musik aus" (`media.mutemusic`). A solo mutes the DSP
  channels too (a wave solo: all of them - they have no wave).
- **Monitor** (Ton-Monitor / Aktive Stimmen): `-- FMOD: n Kanäle belegt (p Pool, x fremd)` from FMOD's own list of used
  channels (`SystemI+0x150`, walked as System::update's loop 0x7bcae6); each voice row shows FMOD's mute / pause bits
  and `(Schleife)`; rows `Fremdkanal (DSP)` with group and state (right twice = their whole group); the music slots as
  rows of their own (`Musik-Slot n: <track>` - läuft / startet / von TruMenu gestoppt / Musik aus). Squares as the bar:
  filled = audible. `snd.fmod`: every used channel to TruMenu.log (pool / EXTRA, flags, mode, group, volume).
- **One "Ambient aus", one "Musik aus"** (owner: two of each): `media.muteambient` and `snd.ambmute` are now the same
  switch - `snd.mute ambience` = sound groups 15 .. 24 (FMOD channel group mute) **and** the `_amb_` srmusic beds - kept
  in `[Media] MuteAmbient` (W6Check turns a kept 1 into the rule at the start; `snd.mute all 0` ends it too); without
  the W6 checks the 0.20 bed stop is the fallback. "Musik aus (Kanäle)" (`music.mute`) was the same command as "Musik
  aus" (`media.mutemusic`) - one row now. Old names stay as items. Page Spiel-Einstellungen / Ton: "Musik aus",
  "Ambient aus (Umgebung + DLC-2-Betten)"; group "Ton einzeln" without the two duplicates; Paket B: copies.
- **Page Kapitel from the main menu** (owner: the chapter rows used `level.load`, refused in the front end since
  0.22.46; live 19:14 Kapitel -> `dlc_level2_start` from `dlc_water_wheel` loaded the unit with Lara in her gold bikini,
  no doppelganger): `ChapSteps` decides when the row is pressed - main menu (main state 10) = the game's mission start
  (`save.backup kapitel;level.start dlc1|dlc2` for the two DLC start rows = exactly the DLC menu's start with the title
  update's outfit rule, `level.start <unit> 0` for every other unit as `arena.go`); in a level = `level.load` as
  before, but the two DLC start rows are **refused** there ("nur aus dem Hauptmenü ... level.load behält Laras
  Kostüm"). Why: the mission start (f27(unit, select, 0, 1), 4th argument 1 = new game data) clears the chosen costume
  (game data +0x20c / +0x20e / +0x210 - the TU's `MainTracker_UILoadLevel` 0x8247d818 -> reset 0x821fe9a8), so the unit's
  default costume loads (DLC 2: `lara_doppelganger` -> TruDlc2Player `doppelganger_casual` + DoppelgangerInit + tracker
  +0x1244 = 1); a `level.load` keeps the game data, so the current outfit stays and DoppelgangerInit never runs. No
  verified way back to the main menu from a level exists in TruMenu - so a refusal, not a half-set player. `cp.jump`
  from the main menu uses `level.start <unit> 0` instead of `unit.go`. Covered: the static chapter rows, the unit rows of
  every chapter group, favourites `level.load <unit>`, the Tests rows with `level.load` + backup, the long menu's
  backup rows. The regress lists (`tests/regress/dlc1.txt` steps 3 / dlc1-treasure, `dlc2.txt` step 4) prepare with
  `level.load` **inside** the DLC (after the DLC start of step 2) - unchanged.
- Page Tests: **"Paket B2: Ton-Log"** (copies of the Ton-Log / Ton-Monitor rows, checks B2.1 - B2.7).
- Options: `[Sound] SourceHooks`, `LogLara`, `LogEnemies`, `LogWorld`, `LogObjects`, `LogUi`, `LogSpeech`, `LogMusic`,
  `LogOnlyAudible`, `LogCollapse`, `LogMaxDist`; switch group `tmtonlog`. Items: `snd.logcat`, `snd.logaudible`,
  `snd.logcollapse`, `snd.logdist`, `snd.catmute`, `snd.catsolo`, `snd.solonew`, `snd.fmod`, `snd.hooks`.
- Checks: `trumenu_ini_check` `check_02250`; `check_02244` (Paket B2, key count), `check_02245` (W6EmitterOwner gone,
  merged rows), `check_02249` version part adapted; negative cases `work\menu50_1411\m50_negative_tests.py`.

### TO TEST 0.22.50

| # | Where | Do | Expected |
|---|---|---|---|
| 1 | start | read `TruMenu.log` | `0.22.50 sound log: checks ok (27 rows); [Sound] SourceHooks 1 ...`; at the first pad poll `0.22.50 sound log: source hooks on - V1 0x591351 ... E1 0x5b99fc after the create call 0x5b99f7 ...` (no `refused`); TruTrace's sound category still reports anim sounds (kind 1) |
| 2 | Spiel-Einstellungen / Ton / Ton-Log | "Ton-Anzeige unten rechts" on, walk, fight in l7 (Arena 1a) | lines `[■][icon] 19:.. name ×n <- viking_thrall #8783  \|  g29 Gegner-Ausrüstung  12 m`; Lara's breath / voice `<- Lara`; a click in the menu `<- UI` |
| 3 | same | repeated sound (steps, axe) | one line with `×n`, it jumps to the top on every new start (B2.3) |
| 4 | Sonar open (PDA) | look at the top of the box | block "läuft gerade" with the loop mark: `computer_hum_12` / `_04` (g57); the ping without the loop mark |
| 5 | Ton-Log | "Stumm: Gegner" right | `snd.mute: group 27 / 28 / 29 ... muted` lines; enemy lines turn to an outline box, `(stumm)`; enemies silent; left = back (B2.4) |
| 6 | Ton-Log | "Solo: Lara" right | only Lara's body / gear / weapons audible; voices / ambience outline boxes; again = off |
| 7 | Ton-Log | "Neuester Ton solo" | log `snd.solonew ... -> snd.solo w<id>`; only that sound; "Alles zurück" = everything back |
| 8 | Ton-Log | "Zeigen: Welt / Umgebung" left, "Nur hörbare Zeilen" right, "Höchstens so weit weg" 20 | ambience lines gone, muted lines gone, far 3D sounds gone; yellow filter line; `TruMenu.ini` `[Sound] LogWorld=0`, `LogOnlyAudible=1`, `LogMaxDist=20` |
| 9 | Ton-Monitor / Aktive Stimmen | read the head | `-- FMOD: n Kanäle belegt (p Pool, x fremd)`; music slot rows; a muted voice row = outline square, `stumm` |
| 10 | anywhere | "Alle FMOD-Kanäle ins Log" | `snd.fmod ...` lines, `pool` / `EXTRA`; with an oscillator sound: `EXTRA` + a `Fremdkanal (DSP)` row in the monitor |
| 11 | menu with the monitor open for a minute | navigate | not slower than with the monitor closed (B2.5); `snd.hooks`: owner list walks about 1 per second while shown, 0 while closed |
| 12 | Spiel-Einstellungen / Ton | read the rows | ONE "Musik aus", ONE "Ambient aus (Umgebung + DLC-2-Betten)"; "Ton einzeln" without them (B2.6); Ambient aus on: wind / water / animals go, `_amb_` bed stops, restart: still on (`[Media] MuteAmbient=1`) |
| 13 | main menu, page Kapitel | "1 Mittelmeer" right twice | log `shortcut 'save.backup kapitel;level.start l1_seatop 0' (main menu: the game's mission start)`; the level starts (B2.7) |
| 14 | main menu, page Kapitel | "DLC 2 Laras Schatten" right twice | `level.start dlc2`; DLC 2 starts as from the DLC menu: doppelganger, `TruDlc2Player ... DoppelgangerInit finished`; `arena.mode`: doppelganger byte 1 |
| 15 | main menu, page Kapitel | "DLC 1 Unter der Asche" right twice | `level.start dlc1`; the outfit / weapon screen as in the DLC menu |
| 16 | in a level (DLC 1), page Kapitel | `dlc_level2_start` right twice | refused: "DLC 2 nur aus dem Hauptmenü (Pause -> Hauptmenü, dann diese Zeile) ..." - nothing loads |
| 17 | in a level | a base-game unit row | `level.load` as before |
| 18 | main menu, Kapitel, a checkpoint row | right twice | `cp.jump`: `level.start <unit> 0;wait.unit ...;player.goto ...` |

## 0.22.49 - sonar: all connected areas + map of this unit; adrenaline options, "Adrenalin bleibt voll" (2026-11-14)

Built into `work\asi\menu0272`, not installed, no live test (owner live notes of 14.11. 16:28 - 16:33, Arena 1a; report in
the workspace `docs\Befund-TruMenu-02249-1411.md`). 16 byte checks `kSoChecks` (the 13 of 0.22.48 + 3,
`work\menu49_1411\precheck_02249.txt`, 0 mismatches on `data\pc\tru.exe`; the installed exe has the same SHA256), two
more patches - 2 bytes for AllFloors, 4 bytes for the triangle cap - written only while `[Sonar] FullMap=1`.

- **Why the sonar map is split** (proven from the map files, `work\sonar_1411b\sonar_floors.py`): every `<unit>_map.drm`
  header carries a floor mask (byte +0x10). Opening the PDA sets the floor `[0xedf268]` to the lowest bit of the current
  unit's mask; the load callback 0x6e4df0 -> 0x6e2e60 goes on from a unit only while its mask holds that bit, and the
  frame 0x6e4130 draws only units with that bit. Helheim: `l7_helheim01` 0x02, `l7_helheim02` 0x06, `l7_helheim03` 0x04,
  `l7_helheim_hall01` 0x03, `l7_helheim_hall02` 0x02, `l7_yggdrasil` / `_hall01` 0x04, `_hall02` 0x0c, `_end` 0x08.
  Opened in helheim03 (floor 4): helheim03 + helheim02 + the Yggdrasil side, helheim01 loaded but skipped = the stop at
  the portal helheim02 -> helheim01 seen live (the log names `l7_helheim03` as the unit until 16:33:10).
- **"Alle verbundenen Bereiche"** (`sonar.allfloors`, `[Sonar] AllFloors`, default 0, live, only with FullMap): 0x6e429b
  `74 1d` -> `90 90`, the frame's floor test skipped - every loaded, placed map unit is drawn. Loaded are only the units
  the game's own open path asks for (the floor's units and their direct portal neighbours of any floor), so **no load is
  added**: the sonar's own list, its own handles (+0x88), unloaded by the close 0x6e4800 -> 0x6dff20 as before; the
  stream units and the shared loader 0x551470 see nothing new. Not built: loading across floors (it would put 6 - 8 more
  map DRMs, about 3 - 4 MB, into the loader queue the streaming uses - the owner's condition "must not touch loading
  zones" rules that out). So "all connected" = the floor + its direct neighbour units of other floors (helheim03 adds
  helheim01 and `l7_yggdrasil_end`; helheim01 / 02 add helheim03 and `l7_arctic_sea`), not the whole level. Overlapping
  floors are drawn on top of each other at their real heights (placement 0x6e2ef0(unit, 0xff) already places every
  loaded unit in mode 1). Faces: helheim floor 2 = 67 874, with AllFloors 120 575 (> the game's 93 572, fits the new
  TriangleCap 300000; the current unit is always drawn first).
- **Triangle cap** (`[Sonar] TriangleCap`, default **300000**, live, only with FullMap; row "Sonar komplett:
  Dreiecks-Grenze"): live 17:17 in `dlc_water_wheel` (FullMap 1) the log showed `drew 93572 triangles and refused
  28709` every 10 s. The limit is the imm32 of `cmp dword [0xee03e8], 0x16d83; jbe` at 0x6dfa69 - a **per-frame
  budget only**: `[0xee03e8]` has no other reader, the triangles go into 4 batch objects of 2000 (0x54 B each, flushed
  at 2000 by 0x6dfe7c and at the frame end), every flush is copied into the render device's dynamic vertex pool, which
  adds a 512 KiB D3D vertex buffer when the current one is full and is reset every frame (a failed allocation = a draw
  without primitives, no crash). TruMenu writes `cap - 1` into the 4 bytes at 0x6dfa6f (game's `83 6d 01 00`) on the
  game thread, only over the game's bytes, back with FullMap off. "Flush and continue" = what the game already does
  (batches of 2000) - the counter is the only stop, so raising it is the fix. Draw order (for what was missing): the
  frame walks the sonar's unit list in creation order = the open's unit, then its portal neighbours breadth-first; per
  unit mesh 0 then 1, faces in file order (not by distance); after the cap every later triangle is refused - the rest
  of the unit where it crossed (scattered pieces, file order) and every later unit, also the floor markers and icons
  drawn after the units. Predicted for `dlc_water_wheel` floor 2: 121 581 faces, cut inside `dlc_watertunnel` (5 112
  drawn, 8 601 refused), `dlc_caverns` (19 408) refused = 28 009 (23 %) - live 28 709 (the rest = markers / icons).
  With 300000 the whole DLC 1 chain (250 805 faces with AllFloors) fits. The installed DLC maps are the P4.9-fixed
  ones (`map_mesh_fix check` on the copies: exit 0; md5 now = the copies) - the gaps are the cap, not map data.
- **"Karte dieser Unit"** (`sonar.unitmap`, read only): `<unit>: echt (N Flächen)` / `nur Platzhalter` / `keine Datei` /
  `lädt ...`, read from the sonar's unit list while it is open (the unit of the open `[0xedf254]`, only if it is in the
  live list `[0x8aff3c]`), kept after the close; before the first open "Sonar einmal öffnen". Plus one log line per
  sonar open: `0.22.49 sonar open: floor [0xedf268] 0x.., radius .., view distance .., ...; n map units, k drawn with f
  faces (cap 93572) - *unit m.. drawn|skipped|unplaced|loading|nofile faces, ...` and `0.22.49 sonar: map of <unit>:
  real|placeholder only|no file ...` - the evidence for what the sonar draws (open point: in helheim01 helheim02 has
  floor bit 2 too and should be drawn; the live note says it was not - the view distance (tuning +0x10 + 4000 around
  the view centre) is the suspect, this line shows the value).
- **Adrenaline (page Figur, group "Adrenalin (Lara)")**: `adren.keep` is now **"Nach Einsatz auffüllen" / "Refill
  after use"** (same command, same behaviour: it refills only while bit 27 - the mode - is clear, so the bar still drains
  during the mode and is full again after it). New **"Adrenalin bleibt voll" / "Adrenaline stays full"**
  (`adren.stayfull`): writes TruShadowCombat `[Adrenaline] DrainPercent=0` and `DrainModePercent=0` (the two rows below
  it show the values), keeps the values it found in TruMenu.ini `[Adrenaline] StayFullDrainWas` / `StayFullDrainModeWas`
  and writes them back when switched off (missing = 100). TruShadowCombat 0.6.14 multiplies the bar's rate by the
  percent: 0 = rate 0.0 exactly, the meter keeps its value bit for bit, in and out of the mode; nothing else changes
  (fill, a strike that empties the meter outside the mode, the mode ends by LT / lock / target). No memory patch.
  `ModeWithoutTarget` = **"Modus ohne Ziel"**, `StrikeWithoutButton` = **"Absprung-Schlag ohne X"** (both tested live
  by the owner, options now; INI keys unchanged), `AssistPointer` = **"Zielhilfe Kreis"**; page Fixes: "Adrenalin-Modus
  ohne Ziel", "Absprung-Schlag ohne X", "Adrenalin: Zielhilfe Kreis". A note row: "DLC 2 Doppelgängerin: Leiste + Modus
  laufen nicht" (CombatManager::Update skips the tick 0x718bd0 and the bar 0x6f2930 there - TruShadowPower `[Adrenaline]
  Translate=1`, the TU's test). Paket A keeps copies (+ "Adrenalin bleibt voll").
- **Log fix**: `snd.sonar 0` logged `[Sound] SonarMute=1483714163 written` (live 14.11. 16:50:20) - the wave list had no
  `%s` of its own, the INI got the right value; the line now prints the list and the value.
- Options: `[Sonar] AllFloors`, `[Sonar] TriangleCap`; switch rows (group `tmsonar`, live). Checks: `trumenu_ini_check` `check_02249`,
  `check_02248` (version part, the first 13 byte rows), `check_02244` key count; Set-TruMenu knows the 0.22.48 hash.

### TO TEST 0.22.49

| # | Where | Do | Expected |
|---|---|---|---|
| 1 | start | read `TruMenu.log` | `0.22.48 sonar: checks ok (16 rows); [Sonar] FullMap .., HidePlaceholder .., FloorMarkers .., AllFloors 0 (0.22.49) ...` |
| 2 | Arena 1a (helheim03), Spiel-Einstellungen / PDA / Sonar | Sonar komplett on, open the sonar | log `0.22.49 sonar open: floor [0xedf268] 0x04 ...` lists helheim03 / helheim02 / yggdrasil* `drawn`, helheim01 + yggdrasil_end `skipped`; `0.22.49 sonar: map of l7_helheim03: real (faces 11634 ...)` |
| 3 | same, sonar open | "Alle verbundenen Bereiche" right | log `... AllFloors 1 - 0x6e429b the loaded units of every floor drawn (no extra load)`; helheim01 and the Yggdrasil end appear (G.6); no load stutter, no streaming hitch after closing |
| 4 | close the PDA, walk on | cross into helheim02 / helheim01 | the loading zones behave as always (nothing changed there) |
| 5 | helheim01, sonar open | read the `sonar open` line | `floor 0x02`, helheim02 `drawn`? note the view distance - if helheim02 is `drawn` but not visible, it is the view distance |
| 6 | Spiel-Einstellungen / PDA / Sonar | "Karte dieser Unit" | `l7_helheim01: echt (27096 Flächen)`; in a DLC 2 room: `nur Platzhalter` (G.7) |
| 7 | Figur / Adrenalin (Lara) | read the labels | "Nach Einsatz auffüllen", "Adrenalin bleibt voll", "Modus ohne Ziel", "Absprung-Schlag ohne X", "Zielhilfe Kreis", no "(Test)" |
| 8 | Figur | "Adrenalin bleibt voll" right | the two "Abbau" rows show 0 / 0 within ~1 s; `TruShadowCombat.log` `0.6.14 switches (run time): ... DrainPercent 0, DrainModePercent 0`; the bar stays where it is, also in the R3 mode (Zeitlupe lasts until LT is let go) |
| 9 | Figur | "Adrenalin bleibt voll" left | the old values come back (100 / 100 or the owner's); TruMenu.ini `[Adrenaline]` keys gone |
| 10 | Figur | "Nach Einsatz auffüllen" on, use the mode | the bar drains in the mode, is full again right after it |
| 11 | Spiel-Einstellungen | Sonar-Ton aus off / on | log `snd.sonar 0 (... ): off - ...; [Sound] SonarMute=0 written` (no big number) |
| 12 | DLC 1 `dlc_water_wheel`, FullMap 1 | open the sonar, look around (also with "Alle verbundenen Bereiche") | `0.22.48 sonar (...): ... triangle cap 300000 - 0x6dfa6f ours ...`; no `sonar: triangle cap hit` line; no floating pieces of `dlc_watertunnel`, `dlc_caverns` drawn; frame rate ok (G.8) |
| 13 | same | "Dreiecks-Grenze" left down to 50000 (= the game's) | the cap line comes back (`the limit 93572 ..., the game's`), the gaps too |

## 0.22.48 - adrenaline at Lara, teaser style 12, page Kapitel, Sonar komplett (2026-11-14)

Built into `work\asi\menu0271`, not installed, no live test (owner wishes of 14.11.; report in the workspace
`docs\Befund-TruMenu-02248-1411.md`, the sonar finding `docs\Befund-Sonar-Komplett-1411.md`). 13 byte checks
`kSoChecks` (`work\menu48_1411\precheck_02248.txt`, 0 mismatches on `data\pc\tru.exe` and the installed exe; start line
`0.22.48 sonar: checks ok (13 rows); ...`), one call stub and three byte patches - all written only while
`[Sonar] FullMap=1`.

- **Adrenaline at Lara** (owner rule: "alles was Adrenalin betrifft kommt wie bei der Schattenpower zu Lara"): bar page
  **Figur**, new group **"Adrenalin (Lara)"** (open at the start, not greyed while Lara is played - the switches act in
  the main game): `adren.meter` (live), `adren.fill`, `adren.keep` and every TruShadowCombat `[Adrenaline]` switch as the
  page Fixes row of `TruMenu.switches.txt` (kQbSwitch: one state, the file is the one source) - FillPercent,
  DrainPercent, DrainModePercent, AssistPointer, StrikeWithoutFullMeter, ModeWithoutTarget ("Adrenalin-Modus ohne Ziel
  (Test)"), StrikeWithoutButton ("Absprung-Schlag ohne X (Test)"), Log - plus a hint line "Ohne X / ohne volle Leiste:
  braucht [Conditions] Enabled=1" and that switch (`TruShadowCombat [Conditions] Enabled`) right below it. Page Tests
  keeps copies only: the old `adren.*` rows (Paket A, Arena 1, Paket 4) and in Paket A the three 0.6.14 / 0.6.15 test
  switches with the checks A.6 / A.7. The shadow-power groups of 0.22.16 stay as they were.
- **Switches rows corrected:** `ModeWithoutTarget` / `StrikeWithoutButton` are **live** (0.22.47 said restart):
  TruShadowCombat 0.6.15 reads both in `M15ReadSwitches`, called from `Q108ReadSwitches` by the Q108 thread about once
  a second (the INI comment "Read again at run time" is right). StrikeWithoutButton acts only when condition 150 was
  wrapped at the start - that needs `[Conditions] Enabled=1`, as StrikeWithoutFullMeter (condition 538): both hints say
  so now. `trumenu_ini_check` knows both as live keys (SW_LIVE).
- **Teaser display default 12** (small circle + light blue count badge on its lower right; was 7): `[Menu] AttractIcon`
  default, `kAtStyleDefault`, the switches row. An INI that holds a value keeps it.
- **Page Kapitel** (was "Kapitel (debug)"): the name without "(debug)". The six unused unit slots
  (`dlc_level3_start` .. `dlc_level6_start`, `dlc_level1_left` / `_right`: only named in the game's unit lists
  `unitlist.txt` / `objlist.dat` / scripts, never built - no archive holds them) no longer show the work package names
  "17p / 17s": group "nie gebaute Plätze / never-built slots", row "nie gebaut / never built", footer / help / answer
  "nur in der Unit-Liste, nie gebaut ...", the long menu and `level.load` value list the same.
- **Sonar komplett** (`sonar.full`, `[Sonar] FullMap`, live; finding option C only - display only): the PDA sonar keeps
  2 bits per map vertex (0 unknown, 1 revealed, 2 pending) and the draw 0x6e3a00 shows a face only from vertices in
  state 1. With FullMap the three tests become "= 1": 0x6e3b25 `0f 94 c3` -> `b3 01 90`, 0x6e3b59 `0f 94 44 24 11` ->
  `c6 44 24 11 01`, 0x6e3ba2 `0f 94 44 24 12` -> `c6 44 24 12 01` - every face of every loaded, placed map unit of the
  floor is drawn (the PDA loads all portal-connected units of the floor; a ping only tests the current unit and its
  direct neighbours). The reveal state itself, the ping, the rays and the save block are not touched: off = the game's
  bytes, the map is again exactly what the pings revealed (also after a save / load). Not built: the finding's options
  A / B (they reveal for real and end up in the save).
  - **MAP placeholder** (`sonar.placeholder`, `[Sonar] HidePlaceholder`, default 1, live): units without a baked map
    carry a placeholder mesh (100 faces / 56 vertices = big 3D letters "MAP": DLC 2 rooms, `dlc_level1_start`,
    `dlc_treasureroom`, five base units). With FullMap and HidePlaceholder 1 a call stub at 0x6e3ab0 (`8b 41 44 85 c0`
    -> `call`) gives such a mesh the face count 0, the game's own `jle 0x6e3ad2` skips it. Decision: default 1, because
    without it the full map would show the letters exactly where the owner plays DLC 2; with FullMap 0 the stub is not
    written at all (the game's code, its letters only where a ping reveals them).
  - **Floor markers** (`sonar.markers`, `[Sonar] FloorMarkers`, default 0, live, only with FullMap): 0x6e40c6 `74 40` ->
    `90 90` - every stair / floor-change marker of the loaded units, not only those a ping saw. Display only (the
    marker draw 0x6e1e00 with the game's own floor tests); off by default because it changes what the owner sees more
    than the map itself.
  - **Triangle cap**: the sonar draws at most 93572 triangles per frame (0x6dfa60, `[0xee03e8]`; `[0xee03ec]` counts
    the refused ones, both reset at each sonar frame by 0x6e4130). While FullMap is written and the sonar is open
    (`[0xee03c8]` 2 .. 4) TruMenu reads the counter: one line `sonar: triangle cap hit - the last sonar frame drew ...
    triangles and refused ...` (at most one per 10 s, 40 per game start). Large DLC 1 areas (dungeon + halls ~129 000
    faces) may hit it - then parts of the far map are missing; nothing else happens.
  - **When written**: on the game thread only (PadHook, every pad poll; the sonar draws on the same thread), only over
    the expected bytes and put back only over our own; a site found changed = one line `0.22.48 sonar: ... refused -
    ... holds ..., not the ... bytes; Sonar komplett off for this run` and everything of ours goes back. One line per
    change: `0.22.48 sonar (<why>): FullMap 1 - 0x6e3b25 / 0x6e3b59 / 0x6e3ba2 every vertex counts as revealed while
    drawing (display only, the save untouched); HidePlaceholder 1 - 0x6e3ab0 call stub ...; FloorMarkers 0 - 0x6e40c6
    the game's bytes (sonar mode [0xee03c8] = n)`. The INI is read again about once a second (`sonar: [Sonar] FullMap 0
    -> 1, ... (TruMenu.ini, live)`); the items write it (`IniKeepInt`) and act at once.
  - `sonar.status`: what is written now, the INI values, the sonar mode, the MAP meshes the stub skipped, the polls
    with refused triangles.
  - Bar page **Spiel-Einstellungen**, new group **"PDA / Sonar"**: Sonar komplett, MAP-Platzhalter aus, alle
    Stockwerk-Marker, Stand, and a copy of "Sonar-Ton aus" (`snd.sonar`, the same `[Sound] SonarMute` as in
    "Ton-Monitor (live)"). Page Fixes: group **"PDA / Sonar (TruMenu)"** with the three `[Sonar]` rows (live). Page
    Tests: **"Paket G: Sonar komplett"** (copies of those rows, the dungeon load, checks G.1 - G.5).
- `docs/Regression-DLC2.md` step 24 / `tests/regress/dlc2.txt` step 6: from the main menu `level.start l1_seatop 0` (or
  `arena.go 1a`) - `level.load` is refused there since 0.22.46.
- `kQbViewMax` 320 (was 256): page Tests has 259 static rows; with every group open 240 was the limit.
- Options: `[Sonar] FullMap`, `[Sonar] HidePlaceholder`, `[Sonar] FloorMarkers`; switch rows for the three (group
  `tmsonar`, live); `[Menu] AttractIcon` default 12.
- Checks: `trumenu_ini_check` `check_02248` (negative cases `work\menu48_1411\m48_negative_tests.py`: 37 + 1 positive);
  `check_02240` / `check_02241` default by `AT_DEFAULT`, `check_0217` page name, `check_02244` Paket G + key count +
  kQbViewMax, `check_02247` version part; `trumenu_quick_check` QB_VIEW_MAX 320. The stub's compiled bytes:
  `work\menu48_1411\stub_bytes.py` (one match, both `jne` land on `test eax,eax`).

### TO TEST 0.22.48

1. Start, `TruMenu.log`: `0.22.48 sonar: checks ok (13 rows); [Sonar] FullMap 0, HidePlaceholder 1, FloorMarkers 0
   (live; ...)`; no `0.22.48 sonar: ... refused`.
2. Bar page **Figur**: group "Adrenalin (Lara)" open, white rows (not grey) - Adrenalin (live), voll, voll halten, the
   eight TruShadowCombat rows with their values (`keine INI` / missing key: TruShadowCombat 0.6.15 INI not installed),
   the hint line, "Bedingungen 2005/2006/2013". The help line of "Absprung-Schlag ohne X (Test)" names
   `[Conditions] Enabled=1`. Count column of ModeWithoutTarget / StrikeWithoutButton: `live`.
3. "Adrenalin-Modus ohne Ziel (Test)" right: `TruShadowCombat.ini` `[Adrenaline] ModeWithoutTarget=1`, within ~1 s
   `TruShadowCombat.log` `0.6.15 switches (run time) ...` (no restart). Page Tests / Paket A shows the same value.
   Left: back to 0, the same log line with 0.
4. Main menu: the teaser display is the small circle with the light blue count badge on its lower right - only if
   TruMenu.ini has no `AttractIcon` (the owner's has `AttractIcon=12` = the same).
5. Page **Kapitel** (name without "(debug)"): group "Ungenutzte DLC-Plätze 3 - 6 + left / right" shows "nie gebaute
   Plätze"; a unit row "nie gebaut"; right on it: the answer "ungenutzt - nur in den Unit-Listen genannt, nie gebaut
   ...". Nowhere "17p" / "17s".
6. **Sonar komplett** in a level with a map (base game, e.g. Croft Manor, or DLC 1 `dlc_caverns`): open the PDA sonar
   with FullMap 0 - note what is revealed. Close it, Spiel-Einstellungen / PDA / Sonar "Sonar komplett" right: log
   `0.22.48 sonar (sonar.full): FullMap 1 - ... every vertex counts as revealed ...; HidePlaceholder 1 - 0x6e3ab0 call
   stub ...`; open the sonar: the whole floor map (also rooms never visited), stair markers only where seen (G.1).
   Also try it with the sonar open (bar over the PDA): the map changes at once.
7. Off again: `FullMap 0 - ... the game's bytes`; the sonar shows exactly the earlier revealed part (G.2). Save, load
   the save, open the sonar: as before the test (G.4) - nothing revealed for real.
8. "alle Stockwerk-Marker" on (with FullMap): more stair / floor markers at the edges of the floor; off: as before.
9. DLC 2 (`dlc_level2_start`, a `dlc2_*` room) with FullMap 1: no big letters "MAP" in the sonar (G.3); `sonar.status`
   counts `MAP meshes skipped`. "MAP-Platzhalter aus" off (FullMap stays 1): the letters appear; on: gone.
10. DLC 1 dungeon (`dlc_dungeon`, Paket G "Kerker laden"), FullMap 1, open the sonar, look around: frame rate; if
    parts of the far map are missing, `sonar: triangle cap hit - ...` in the log (G.5); `sonar.status` cap hits > 0.
11. Fixes page group "PDA / Sonar (TruMenu)": FullMap right -> `[Sonar] FullMap=1` in TruMenu.ini, within ~1 s
    `sonar: [Sonar] FullMap 0 -> 1 ... (TruMenu.ini, live)` and the `0.22.48 sonar (run time): ...` line.
12. Negative: `sonar.full 2` -> bool (= on); `[Sonar] FullMap=7` in the INI -> on (non-zero); a changed byte at a site
    (another plugin) -> the `refused` line, `sonar.full` answers `disabled: pre-check failed (...)`; `sonar.placeholder
    1` / `sonar.markers 1` with FullMap 0 -> "(wirkt erst mit Sonar komplett)", nothing written (`sonar.status`: full 0
    placeholder 0 markers 0); main menu with FullMap 1: the bytes are written at the first pad poll in a level.

## 0.22.47 - sound monitor, the sound box as a log, sonar sound off (2026-11-14)

Built into `work\asi\menu0270`, not installed, no live test (finding in the workspace `docs\Befund-Tonanzeige-1411.md`;
owner wishes of 14.11. after the sonar test: "Ton-Monitor", "Ton-Anzeige unten rechts als Log", "Sonar-Ton aus"). 6 byte
checks `kW7Checks` (`work\sndui_1411\precheck_02247.txt`, 0 mismatches on the installed exe; start line `0.22.47 sound
monitor: checks ok (6 rows); ...`), no hook, no patch - the voice pool walk of 0.20.1 / 0.22.45 is the only source.

- **Fix: the wave id of a voice** (static, `work\sndui_1411\dis_*.txt`): the wave node 0x591220 gives VoicePool::Play
  the wave table entry's **+4** (0x591348), so voice +0x10 is never an entry. 0.20.1 .. 0.22.46 computed `(sample -
  table) / 0x18` and every voice read `Stream` (all `snd.now` / `snd.dump` lines of 14.11.) - `snd.mute w<id>`, `snd.solo
  <wave>` and the wave 10 log line could not match. Now a map entry +4 -> id (rebuilt when a sample is unknown and the
  map is older than 0.5 s, and every 2 s).
- **Fix: the emitter of a voice**: before Play the node's +8 is replaced by a new 0x90-byte params object (0x5912f9 /
  0x59131b / 0x59132c); voice +0x1c is that object, the params the node got sit at its **+0x74** (ctor 0x5906e0). The
  emitter is found by walking params -> [params+0x74] (at most 4 steps), decided by the emitter vtable 0x851240 as in
  0.22.45; none = `emitter ?`. `snd.mute s<id>` / `e<hex>`, `snd.now` and the object column use it.
- **Sound monitor** (bar page Spiel-Einstellungen / Ton, sub-group **"Ton-Monitor (live)"**, and Tests / Paket B):
  - "Aktive Stimmen": every voice of the pool, playing first, then paused / starting / muted: name (the wave name -
    built-in for the PDA waves and wave 10, all others from an optional `TruMenu.wavenames.txt` next to tru.exe, else
    `Welle <id>`; `Strom` / `Musik-Strom` for a stream), `w<id>` / `s<section>`, the source (`<object> #<intro>` from the
    instance sound list `[inst+0x248]`, `Level / Skript` for an emitter in no list, `UI`, `Musik`, `Strom`), state, group
    with a readable name (`g57 PDA & Sonar`, `g15 Umgebung`, ...), volume, 2D / 3D with the distance in metres.
    Right = mute (`snd.mute w<id> 1`, or `e<hex> 1` when the wave is unknown), left = on again, X = toggle; a stream
    with neither: only its whole group, right twice. A filled square / red state = muted now.
  - "Zuletzt gestartet": the newest `[Sound] HistoryMax` starts (time, name, source, kind + group), same keys.
  - "Aktive Ton-Regeln": every `snd.mute` rule and the sonar switch, left / right = that one off.
  - "Monitor + Verlauf ins Log" = `snd.monitor`: one `snd.monitor` line per voice (name, wave, section, group, kind,
    volume, distance, state, source, voice / channel / emitter) and the history to `TruMenu.log`.
  - The rows are built from the list of the game thread; while they are drawn (bar or the long menu, where every row has
    a mute / on button) the list is refreshed every 0.5 s even with `snd.list` off.
- **Main menu**: while the game polls no pad (front end, loading - PadHook does not run) the sound list, the monitor,
  the sound switches and the history run from the Present hook - only on the thread PadHook ran on (or before any pad
  poll), the same rule queued items follow there; one log line `snd: the game polls no pad ...` says which.
- **The bottom-right box as a log** (`snd.logview`, `[Sound] OverlayStyle=1`, written back by the bar; 0 = the 0.20.1
  voice list): newest start on top, one short line `12:55:02  computer_hum_12  <- UI`, one colour and one icon per kind
  (voice: speech bubble, ambience: wave line, UI: screen, music: note, enemy: warning triangle, effect: burst). The bar
  font is ImGui's built-in one (TruMenu adds no font, no emoji glyphs), so the icons are ImDrawList primitives. A line
  fades over `[Sound] LogFadeSec` (15 s) and goes after 4 x that; at most `[Sound] MaxLines` lines. The kind comes from
  the group (table of the 80 groups, `docs\Befund-Ton-Gruppen-0611.md`) and the music / speech slider categories.
- **Sonar-Ton aus** (`snd.sonar`, `[Sound] SonarMute=1`, kept in TruMenu.ini): **scope** - only the waves of `[Sound]
  SonarWaves` (default `914 915 916`: `computer_hum_12` / `computer_hum_04` = the two-voice loop of SoundPlex section
  3381 that plays while the PDA sonar is open, `alrm_radar_03` = section 3382, the radar ping), muted per channel
  (FMOD's `ChannelI::setMute` as `snd.mute w<id>`); **when** - at every start of such a voice, so after a level load and
  each new sonar open again, and after a game restart (read at the start); **undo** - the same row again
  (`snd.sonar 0`), the row in "Aktive Ton-Regeln", or `SonarMute=0` in TruMenu.ini. `snd.mute all 0` does not touch
  it (a separate, kept switch). Group 57 holds only the 8 waves of `g_pda.drm` (909 .. 916), but its child group **70 =
  Lara's hint lines** - so the whole group is only the fallback `snd.sonar57` (`SonarMute=2`, row "Sonar: ganze Gruppe
  57 aus (Notlösung)"), which silences her hints too.
- **Start history** (`[Sound] History=1`, `HistoryMax=30`, `HistoryLog=0`): a voice counts as started when its (voice,
  sample, channel) was not in the pool walk before (the first walk after a switch-on records nothing); `HistoryLog=1`
  writes one `snd.start #n` line per start (at most 5000 per game start). `snd.history [n]` writes the newest n.
- `snd.mutes` names the sonar switch; `snd.list` / `snd.dump` / `snd.now` lines show the wave name, section and source.
- Options: `[Sound] History`, `[Sound] HistoryMax`, `[Sound] HistoryLog`, `[Sound] OverlayStyle`, `[Sound] LogFadeSec`,
  `[Sound] SonarMute`, `[Sound] SonarWaves`; switch rows SonarMute / OverlayStyle / History / HistoryMax / HistoryLog /
  LogFadeSec (read at the start).
- Optional `TruMenu.wavenames.txt` next to tru.exe: `<group> TAB <wave id> TAB <name>` as `tools/sound_groups.py scan`
  writes it (`groups_waves.tsv`), or `<id> <name>`; the first name of a wave wins, `.wav` is cut.
- Checks: `trumenu_ini_check` `check_02247`; `check_02244` key count (283 + 3 + 7), `check_02246` version part adapted.

### TO TEST 0.22.47

1. Start, `TruMenu.log`: `0.22.47 sound monitor: checks ok (6 rows); wave names 9 built-in (no TruMenu.wavenames.txt);
   [Sound] History 1 (max 30, log 0), OverlayStyle 1 (log), LogFadeSec 15, SonarMute 0 (off), SonarWaves 914 915 916`.
2. Main menu, bar Spiel-Einstellungen / Ton / "Ton-Monitor (live)": "Aktive Stimmen" lists the menu music / clicks (not
   `Stream` only: a click = `ui_drop_04 w10 <- UI` or another `Welle <id>`); "Zuletzt gestartet" gets a line per click.
   If the game polls no pad there: log line `snd: the game polls no pad (front end / loading) - ... Present hook`.
3. "Ton-Anzeige unten rechts" on: the box is a log, newest on top, colours / icons per kind, old lines fade.
   "Ton-Anzeige als Log" off: the old list again (now with names and `<- source`).
4. DLC 1 / 2 in a level: "Aktive Stimmen" - ambience `g23 Wasser` / `g22 Wind & Gewitter` with an object or
   `Level / Skript`; Lara's steps / voice; right on one row - that sound goes, the row turns red; left - back.
5. **Sonar**: open the PDA sonar - "Aktive Stimmen" shows `computer_hum_12 w914 ...` and `computer_hum_04 w915 ...`
   (g57 PDA & Sonar); the ping at the opening appears in "Zuletzt gestartet" - note its wave. "Sonar-Ton aus" on - the
   scan sound is gone, everything else unchanged; close / open the sonar again, load a level, restart the game: still
   off (`[Sound] SonarMute=1` in TruMenu.ini). Lara's hint line (group 70) still audible with the sonar switch on.
6. "Sonar: ganze Gruppe 57 aus (Notlösung)": log `snd.mute: group 57 muted`; off again: `group 57 unmuted`.
7. "Monitor + Verlauf ins Log": `snd.monitor` lines with names, groups, sources; `snd.history` lines.
8. Old W6 rows with real ids now: "Welle 10 stumm / an" (main menu click silent), "Nur Welle 10 (Solo)".
9. Negative: `snd.history 0` / `snd.history 999` -> usage; `snd.sonar 2` -> bool (= on, mode 1); `[Sound] SonarMute=7`
   / `HistoryMax=0` / `LogFadeSec=-1` in TruMenu.ini -> the defaults (start line); `SonarWaves=abc` -> 914 915 916; a
   stream row (no wave / emitter) right once -> "only its whole group (right twice)", left -> nothing muted.

## 0.22.46 - arena from the main menu, GameTracker+0xb9 in the front end (2026-11-14)

Built into `work\asi\menu0269`, not installed, no live test (finding in the workspace
`docs\Befund-Arena-Hauptmenue-1411.md`). Owner live 2026-11-14 12:07, Paket A "Arena 1a" from the main menu: `arena.go
1a: refused: level change pending (GameTracker+0xb9 = 1)`. 10 byte checks `kFeChecks`
(`work\arena_1411\precheck_02246.txt`, start line `0.22.46 front end: checks ok (10 rows)`), no hook, no patch, no INI
key.

- **What the `+0xb9 = 1` in the main menu was** (TruMenu.log of that session + static reading, `tools/pe_abs_uses.py`
  0xe7f140 / 0xe7f141, `tools/pe_disp_scan.py` +0xb8 / +0xb9, `tools/pe_dis.py`): the first click at 12:07:21 was
  accepted; its step `unit.go l7_helheim03` became `level.load l7_helheim03` (`level change to 'l7_helheim03' requested`
  12:07:21.658). That call (GAMELOOP_RequestLevelChangeByName 0x5df8c0 -> 0x5df760) sets `+0xb9 = 1` and the doneType
  `+0xb8` (0x5df88a). A request is served **only in main state 1** (0x5e0050: `+0xb8` != 0 / 8 -> 0x5dab40, its only
  caller); the main-menu handler (state 10, 0x5dae20) gets no tracker. `+0xb9` goes back to 0 only at the start of main
  state 2 (0x5de864) and in the game's own front-end save load (0x7743c0: request doneType 10, main state 2, `+0xb9 = 0`
  by hand at 0x7744ce). So TruMenu's own level.load left a request nobody served; every later click was refused by it,
  until the owner's own new game (12:09:00) went through state 2. The game's mission start (`f27` -> 0x5dfb20) never
  calls the request outside state 1 - it sets main state 2 itself.
- **`LevelChangePending`**: in main state 10 (with `kFeChecks` ok) `+0xb9` no longer counts as pending (an unserved
  request the next level start clears); everywhere else as before. `status.state` says so.
- **`level.load`** is refused in the front end (main state 6 / 10): `refused: front end (main state 10) - the game serves
  a level change request only in a level (main state 1); from the main menu: level.start <unit> 0 (the mission start) or
  arena.go <spot>` - before, it left the dead request (also the tour's "Laden ..." and `unit.go` steps in the main menu).
- **`level.start <unit> [0|1]`**: an optional second word = f27's own second argument (the outfit / weapon selection byte
  `[0xfae8d9]`, 0x77e193): 0 = none (as the title update starts `dlc_level2..6_start`), 1 = the selection; without it the
  0.7.2 rule. 0 needs the 0.7.2 selection-byte check (`g_outfitRuleOk`). In a shortcut, `level.start <unit> 0|1` waits for
  that unit (as `level.load`); every finished level wait now logs `shortcut '...': level up - unit ..., player present, no
  level change pending (n s after the request)`.
- **`arena.go <spot>` from the main menu** (main state 10, front-end state `0xfae8da` = 3, no one-shot Bink movie): one
  shortcut `save.backup kapitel;level.start <unit> 0;wait.unit <unit>;cheat.flight 1;player.goto <intro> force;
  cheat.onehitkill 0;arena.mode <spot>` (`cheat.onehitkill 0` only with `[Cheats] Enabled=1` and its check ok - else the
  log says it was not switched). The level start is the PC generalbank script 104 mission start (uigamedata f22, f27(unit,
  0, 0, 1), stdscreenmgr f19 + f7): f27's 4th argument 1 = new game data in memory (0x77e19f: 0x556940(0) with the player
  tailoring / options kept and put back - no profile change, TruMenu writes no save; a checkpoint may write the game's
  Autosave as in every level, the backup comes first); a fresh level = a new player tracker = doppelganger flag 0 =
  main-game mode. Log: `arena.go 1a: main menu (main state 10, front-end state 3) -> the game's mission start of
  l7_helheim03 (...)`, then the runner's step lines, `level up`, `unit l7_helheim03 streamed`, the goto, `cheat: one-hit
  kill OFF (...)`, `arena.mode 1a (...): ... fits the main-game spot (adrenaline runs); unit l7_helheim03, one-hit kill
  byte 0x00e91ffd = 0`. DLC 2 spot 1c from the main menu: allowed with a warning (a direct unit start has no doppelganger).
- **Refusals** (one answer line each): main menu checks failed / experimental off / mission path not verified; front-end
  state != 3 (title screen, a sub menu, the intro); a one-shot movie (credits / teaser); no level and not the main menu
  (main state 6 / loading); in a level: a cutscene plays (cinematic test 0x453f00); as before a pending level change
  (main state 2 / 9, `+0xb9` in a level).
- **In a level** the steps are those of 0.22.32 (`unit.go` / `level.load` by the doppelganger flag, `arena.mode` last).
- **`arena.mode`** logs the unit and the one-hit kill byte in the same line (`WARNING one-hit kill is ON` when set).
- Bar page Tests / Paket A: the note reads "Hauptmenü oder Hauptspiel; One-Hit-Kill geht aus".
- Switches file: row `TruQoL | Fixes | ReleaseWalk` (TruQoL 0.1.8, PT.2 - it was missing, `trumenu_ini_check` Q0215).
- Checks: `trumenu_ini_check` `check_02246`; `check_02245` version part adapted; negative cases
  `work\arena_1411\arena_negative_tests.py`.

### TO TEST 0.22.46

1. Start, `TruMenu.log`: `0.22.46 front end: checks ok (10 rows); GameTracker+0xb9 in the main menu = ...`.
2. Main menu, bar Tests / Paket A: "Arena 1a: Helheim-Halle" right twice. Expected: the menu goes, the loading screen,
   Lara in the Helheim hall on the floor (z about -3216), flight on. Log in this order: `arena.go 1a: main menu ...`,
   `shortcut 'arena 1a (l7_helheim03, main menu)' 2/7: level.start l7_helheim03 0 -> ok queued ...`, `item level.start:
   mission start 'l7_helheim03': ... f27('l7_helheim03', 0, 0, 1) ... no outfit / weapon selection - second word 0`,
   `level up - unit l7_helheim03`, `unit l7_helheim03 streamed`, `cheat: one-hit kill OFF`, `arena.mode 1a ... byte 0
   ... fits the main-game spot (adrenaline runs); unit l7_helheim03, one-hit kill byte 0x00e91ffd = 0`, `shortcut ...
   done`. Note: which outfit Lara wears; does a cutscene or the outfit screen come (it should not)?
3. Then Paket A as before (adrenaline full, LT + R3, jump-off headshot): adrenaline runs = main-game mode.
4. Main menu again (pause -> main menu), "1d: Valgrind" - the same lines with `l5_valgrind` / CP 7329.
5. The old case: main menu, command bar `level.load l7_helheim03` -> refused with the front-end reason, nothing waits;
   then "Arena 1a" works at once (before: `refused: level change pending (GameTracker+0xb9 = 1)`).
6. `status.state` in the main menu: "in a level ..." no; after step 5 not "level change pending".
7. Saves: the manual saves unchanged after the run (file times in the save folder; `TruMenu.saves\<time>_kapitel` holds
   the backup); note whether `Autosave.TRUSave` changed.
8. Negative: title screen ("press start") -> `arena.go 1a` refused (`front-end state ...`); a sub menu (options) open ->
   refused; during a cutscene in a level -> refused (`a cutscene plays`); `level.start l7_helheim03 2` and
   `level.start l7_helheim03 0 x` -> usage; one-hit kill on in the main menu? (needs a level - set it in a level, quit to
   the main menu, "Arena 1a": arrives with `one-hit kill OFF`).
9. In a level (main game), "Arena 1a": as 0.22.32 (`unit.go` / portal or `level.load`), log ends with `arena.mode 1a`.

## 0.22.45 - W6: hearing tests faster - single sounds / tracks off, ambience off, wave 10 log line (2026-11-14)

Built into `work\asi\menu0268`, not installed, no live test (finding in the workspace `docs\Befund-W6-Toene-1411.md`;
owner live notes of 13.11., package W6 of `docs\Testabend-1311-Warteschlange.md`). 15 byte checks
(`work\w6_1411\precheck_02245.txt`, `0.22.45 W6 sound switches: checks ok (15 rows)` at the start), no hook, no patch.

- **`snd.mute <target> [1|0]`** (TruLink / command bar; no value = toggle; at most 16 rules, for this game start):

  | Target | What is muted | How (the game's / FMOD's own path) |
  |---|---|---|
  | `w<id>` or `<id>` | every voice of that wave (wave table index, `Welle 1234` in `snd.list`) | FMOD's `ChannelI::setMute` 0x7c92b5 per channel, behind the game's handle check 0x7c7e5a (as every Channel call of the game, e.g. `Channel::setPaused` 0x7b9be0); the game has no single-channel mute of its own |
  | `s<id>` | every voice whose emitter plays that SoundPlex section | same, per channel |
  | `e<hex>` | every voice of one emitter (address from `snd.now`) | same, per channel |
  | `g<n>` | a whole sound group with its children | `ChannelGroupI::setMute` on the group's FMOD channel group (as `media.mutemusic`), again after a level load |
  | `ambience` | group 15 (16 .. 24: ambient events, loops, animals, fire, wind / foliage / thunder, water, underwater) and the `_amb_` srmusic beds (DLC 2) - effects, voices, music stay | group mute + the srmusic stop below |
  | `music` | = `music.mute` (`media.mutemusic`) | |
  | a track name | that srmusic track (`TruMenu.media.txt` or a slot now) | the game's stop `SRMUSIC_LoadMusic(slot, NULL, fade, 0)` whenever it starts; `0` again = `LoadMusic(slot, name)` where `media.music.play` may run (main menu, a level with `[Media] MusicInLevels=1`), else the unit starts it again |
  | `all 0` | every rule and the solo off | everything TruMenu muted is unmuted |

  Only channels / groups TruMenu muted are ever unmuted; a channel or group muted by someone else is left alone. No
  volume of the game and no option slider is written.
- **`snd.solo <target> | off`**: every voice but the target's muted per channel (targets as above, no track: the
  srmusic stream voices cannot be told apart); the same target again = off.
- **`snd.now`** (game thread): one `snd.now` line per voice in `TruMenu.log` (the `snd.list` text + voice / channel +
  emitter and SoundPlex section), the audible ones as the answer: `w10/s23469/g22 0.32; ... music [..]`.
- **`snd.mutes`** (info): rules, solo, channels / groups muted now, stopped tracks, wave log counters. **`snd.ambmute`**
  (bool) = `snd.mute ambience` for the bar. **`music.stop [slot|all]`** (default all; also in a level, as
  `media.muteambient`), **`music.next`** (the next music row of `TruMenu.media.txt` after slot 0's track, through
  `media.music.play` and its gates), **`music.mute`** = `media.mutemusic`.
- **Wave 10 log line** (`[Sound] WaveLog=1`, `WaveIds=10`, `WaveLogMax=500`; `snd.wavelog on|off|<ids>`): whenever a
  voice of a watched wave starts, one line `snd.wave 10 START #n: unit <unit>; voice .. ch .., SFX g<n>, vol ..,
  3D / 2D, ...; emitter 0x.. sound s<id> (SoundPlex section); object <name> (object <id>, intro <id>, inst 0x.., fixed
  slot n / dynamic list of [inst+0x248]) | in no instance sound list (...); wave entry ...` - so the owner's hearing test
  can be matched (6:10 = `ui_drop_04` of the generalbank and the DLC 2 reuse, Befund-Gruppe-J J-2). The emitter is
  voice +0x1c - 0x14 (vtable 0x851240) only when the wave sits directly under it; else `emitter ?` (inner SoundPlex
  node). The wave table entry (6 dwords) is logged raw for the comparison of the two wave versions.
- Bar: page Spiel-Einstellungen / Ton, sub-group **"Ton einzeln (Hörtest)"** (ambience off, music off / stop / next,
  `snd.now`, wave 10 mute / solo, every switch back, state); page Tests / Paket B: the same rows + check `tgB.wave10log`.
  Switch rows `[Sound] WaveLog` / `WaveLogMax` in group `Diagnose (TruMenu)` (read at the start).
- Checks: `trumenu_ini_check` `check_02245`; `check_02244` (version part, key count 283 + 3) adapted; negative cases
  `work\w6_1411\w6_negative_tests.py`.

### TO TEST 0.22.45

1. Start, `TruMenu.log`: `0.22.45 W6 sound switches: checks ok (15 rows); [Sound] WaveLog 1, WaveIds 10, WaveLogMax 500`.
2. Main menu: move through the menu - every click that plays wave 10 gives one `snd.wave 10 START #n: unit ...` line
   (main menu: `ui_drop_04`, 2D, no object); note how many lines per click (expected 1).
3. DLC 2 (`dlc_level2_start` / `dlc2_ceremony_room`): play on with the log open; each `snd.wave 10 START` line names the
   unit, the emitter + `sound s<id>` and the object (or `in no instance sound list`) - say what you heard at that time
   (menu click or another sound).
4. Bar Paket B: "Umgebung aus (DLC-2-Ambience)" on - wind / foliage / thunder / water and the `_amb_` bed go, steps,
   voices, music stay; log `snd.mute: group 15 muted ...` and `srmusic slot n '..._amb_...' stopped`. Off again: group
   unmuted; the bed comes back only with `[Media] MusicInLevels=1` (else at the next unit start - log says which).
5. "Was spielt gerade? (snd.now)": the answer lists `w<id>/s<id>/g<n> volume`; `TruMenu.log` one `snd.now` line per voice.
6. "Welle 10 stumm / an", then trigger wave 10: no sound, `snd.mutes` shows `w10` and `channels muted now 1` while it
   plays; again = on.
7. "Nur Welle 10 (Solo an / aus)": everything else silent (music too); again = everything back.
8. TruLink: `menu snd.mute s<id>` with an id from `snd.now` - that emitter's sounds go; `menu snd.mute all 0` - all back.
9. `menu music.stop` in a level - the level music fades out (log `music.stop: slot 0 '...' stopped`); `menu music.next`
   in the main menu - the next track plays (in a level only with `MusicInLevels=1`).
10. Negative: `snd.mute w9999` (wave table 5120), `snd.mute g0` (root), `snd.mute g999`, `snd.mute s0`, `snd.mute e1234`
    (no emitter), `snd.mute nosuchtrack`, `snd.mute 10 2`, `snd.mute all 1`, `snd.solo <track>`, `snd.wavelog 99999`
    - each refused with its reason, nothing muted (`snd.mutes`).

## 0.22.44 - W2: TruMenu order - page Tests by the test guide, accessibility rows, big window, DeviceGlyphs row (2026-11-14)

Built into `work\asi\menu0267`, not installed, no live test (finding in the workspace
`docs\Befund-W2-TruMenu-Ordnung-1411.md`; owner live notes of 13.11., package W2 of `docs\Testabend-1311-Warteschlange.md`).
No new INI key, no new item, no hook, no byte check.

- **Page Tests by the test guide.** The first group is "Testanleitung 14.11.: Pakete A - F" (`tg_1411`, open) with one
  sub-group per package of `docs\Testanleitung-1411.md`, the same names, closed at the start (`tg_a` .. `tg_f`):

  | Group | Rows (existing items) | Checks |
  |---|---|---|
  | Paket A: Adrenalin + Kampf | hint, `arena.go 1a`, `cheat.onehitkill` (keep off), `arena.mode`, `adren.meter`, `adren.fill`, `adren.keep`, switch `[Input] DeviceGlyphs` | `tgA.r3slow`, `tgA.jumpoff`, `tgA.empty`, `tgA.finisher` |
  | Paket B: Hören | hint, `snd.dump`, `claude.mark sound` | `tgB.dopple`, `tgB.wave10` |
  | Paket C: DLC 2 aus dem Pausemenü | hint | `tgC.nocostume`, `tgC.pda` |
  | Paket D: Debug-Ansicht | hint, `dbg.view`, `dbg.names`, `dbg.roomonly`, `dbg.metres`, `dbg.emptypots` | `tgD.labels`, `tgD.roomonly`, `tgD.near` |
  | Paket E: Markup / Säule / Wasser (alter Baum) | hint, `level.load dlc_dungeon` / `dlc_caverns` (right twice, backup first), `draw.markup`, `draw.ledges`, `claude.mark gfx` | `tgE.pillar`, `tgE.lines`, `tgE.water` |
  | Paket F: Fixes 13.11. (eigener Baum) | hint, `level.start dlc1`, `level.load dlc_dungeon`, `claude.mark gfx` | `tgF.start`, `tgF.spiders`, `tgF.gate`, `tgF.dry`, `tgF.pillar` |

  Check rows work as the 0.22.28 ones (right OK, left Fehler, X skipped, the same press again = open); their first mark
  adds `test.add "<id> 1411 <English label>"` (the archived Q90 checks keep the tag Q90); the TO TEST list on the page
  skips `tg<X>.<name>` like `tp<X>.<name>`. Rows of the block carry the new flag `kQfTg` (marker only).
- **Archive.** Then the groups in use (Teleport, Arena 1 - Kampf, Zwischensequenz), then the closed group **"Archiv /
  Alt"** (`ts_archive`) with the rows of earlier rounds, moved unchanged as sub-groups: "Alte Testpakete 11.11. (Q90)"
  (`tp_q90` + packages A, 1 .. 9), Teststellen (`ts_spots`), Licht (Diagnose) (`light_diag`), Diagnose (`ts_diag`),
  hall02-Zähler (`ts_hall02`). Nothing deleted; the group keys are the same, so `[Quick] Closed` keeps applying.
- **`kQbViewMax` 256** (was 128): with every group open the page has 227 static rows (170 before) - the Prepare / TO
  TEST rows after them were already cut at 128 (`work\w2_1411\w2_row_counts.py`).
- **Barrierefreiheit.** The rows "verschoben": planned rows were drawn with a 3-space prefix after the (empty) square
  column (QbViewOf, since 0.18 - the column came in 0.22.18), the arachnophobia parts had two leading spaces in their
  labels. Now: no prefix, no leading spaces; the arachnophobia rows are a sub-group "Arachnophobie" of "Sonstige
  (Phobien)" (master switch first - the parts act only while it is on); **every planned row is in the closed group
  "Geplant (noch ohne Funktion)"** at the end, its category in front (Sehen / Hören / Verstehen / Steuerung / Phobien).
  The groups Sehen and Hören had planned rows only and are gone. The planned row "Untertitel groß" became "Sehen:
  Sprechername" (size and bar exist: group Verstehen). The prefix change applies to planned rows on every page (Gegner,
  Koop).
- **Big menu window off for an INI before 0.22.18.** 0.22.18 (coordinator decision, section 0.22.18 "Defaults ... for new
  users: only the bar") made `[Menu] Enabled` the big window (default 0) and moved the old master switch to `[Menu] Load`;
  Set-TruMenu keeps an edited INI. The owner's INI is from before 0.22.18 (comment "0 = load but hook nothing", no
  `Load` line), so its `Enabled=1` - meant as "load" - opened the big window: `TruMenu.log` 13. / 14.11. "0.22.18: big
  menu window on" at all 12 starts, `menu opened (pad)` 18:10:13. Now an INI **without `[Menu] Load`** never opens the big
  window; `Load` keeps its default 1 (an old `Enabled=0` does not unload TruMenu). Start line `0.22.44: TruMenu.ini has no
  [Menu] Load ...`; L3 + R3 logs `menu not opened (pad): TruMenu.ini without [Menu] Load ...`. For the big window: add
  `Load=1` and `Enabled=1` under `[Menu]`.
- **DeviceGlyphs row.** Page Spiel-Einstellungen, group Steuerung: "Tasten-Hinweise nach Gerät (Neustart)" = the page
  Fixes row `TruMenu | Input | DeviceGlyphs` (group "Eingabe (TruMenu)"); also in Paket A. Read at the start (patch of
  0x5a7c20), so a change acts after a restart. The owner's INI has no `[Input]` section: the default 1 applies (log
  `0.22.38 PD: [Input] DeviceGlyphs 1` at 23:11 and 01:36).
- Checks: `trumenu_ini_check` `check_02244`; `check_02228` (the TP block now inside `ts_archive`, `tp_q90` a sub-group) and
  `check_02243` (version part) adapted; `trumenu_quick_check` model `persist` knows the old-INI rule, `QB_VIEW_MAX` 192.

### TO TEST 0.22.44

1. Start, `TruMenu.log`: `0.22.18: big menu window off ...` and `0.22.44: TruMenu.ini has no [Menu] Load ...` (with the
   current INI). L3 + R3: no big window, log `menu not opened (pad): TruMenu.ini without [Menu] Load ...`.
2. Negative: add `Load=1` under `[Menu]` (keep `Enabled=1`), restart: the big window opens with L3 + R3 again, no
   `0.22.44` line. Remove `Load=1` again if the window is not wanted.
3. Bar page Tests: first `[-] Testanleitung 14.11.: Pakete A - F` with six closed packages `[+] Paket A: Adrenalin +
   Kampf` .. `[+] Paket F: ...`; then Teleport, Arena 1, Zwischensequenz; last `[+] Archiv / Alt`.
4. Paket A open: Arena 1a (right twice), Adrenalin voll / voll halten, Ein Treffer; a check right = OK (green), again
   right = offen; `TruMenu.log` `tests: test.mark tgA.r3slow ok`, `TruMenu.tests.txt` has `tgA.r3slow ... 1411 ...`.
5. Archiv / Alt open: the old packages and groups as sub-groups, each closed / open as before.
6. Every group open (also the archive): the page still ends with "Vorbereiten" / "TO TEST" rows.
7. Bar page Barrierefreiheit (bar language en and de): live rows aligned with each other (no extra indent);
   "Arachnophobie" a sub-group under Sonstige; last `[+] Geplant (noch ohne Funktion)` with 10 grey rows "geplant".
8. Bar page Spiel-Einstellungen, group Steuerung: "Tasten-Hinweise nach Gerät (Neustart)" shows the INI value (1); left
   writes `DeviceGlyphs=0` into TruMenu.ini (as page Fixes).
9. Long menu (only with step 2): section "Quick bar pages" / Tests and Barrierefreiheit show the same groups.

## 0.22.43 - W5: markup drawn where the engine uses it, type + id labels (2026-11-14)

Built into `work\asi\menu0266`, not installed, no live test (finding in the workspace
`docs\Befund-W5-Markup-Saeule-1411.md`; owner live notes of 13.11.: floating yellow lines in the caverns 21:20, a yellow
"coil" in front of a dungeon wall 21:53, a grey line in Thailand 00:52, V pairs on a climbing wall 00:01).
Section "0.22.43 W5 markup" in `TruMenu.cpp`; render thread, read only - nothing is written into tru.exe memory.

- **Object markup at its real place.** A markup box with an owner instance (box `+0xc`) keeps its poly line in the
  object's local frame. The engine's users take the matrix of the getter 0x5be360 (`[owner+0x90] + s16 record +0x30 *
  0x40` = the bone matrix) and transform every point with 0x49ba20 (x * row0 + y * row1 + z * row2 + row3) - only when
  `[owner+0x2d8]` is set (0x5c41c3). `draw.markup` drew the stored points, so every object ledge appeared around the
  world origin. The 21:53 coil was exactly that: the ledges of `dlc1_uo_pillar_of_doom_a` / `_b` (local rings around
  their bones), projected with the logged camera of 21:53:11, cover the coil on the shot to a few pixels. Markup2 (unit
  DTP items) and classic unit markup stay as stored - they are world points already and sit on beams / walls live.
  Without its matrix an object box is left out (no known place).
- **Unusable boxes left out.** The engine's markup query skips record `+0x32 == 1`, box `+0x28` bit 31 (disabled), owners
  with `+0x18` bit 2 or 0x20000000 and boxes whose stream unit entry `+0x3c` has byte `+5` set (0x5ce447 .. 0x5ce496);
  `draw.markup` does the same.
- **Labels "type #id".** At the middle point of each line within 15 m (4350 units) of Lara, the nearest 24, through the
  W3 label rect list (one label per box, `LabelStack`, `LabelCellMax`). Type / id as the engine's getter 0x5be340 (markup2
  item `+0x4d` / `+0x48`, else record `+0x33` / `+0x2e`). Names in the bar language:

  | Type | DE | EN | Colour |
  |---|---|---|---|
  | 1 | Kante | ledge | yellow |
  | 2 | Sprungziel | jump landing | light grey |
  | 3 | Gegner-Absprung | enemy drop-down | red |
  | 4 / 5 / 6 | Wandstange / Stange senkrecht / Reckstange | wall pole / vertical pole / horizontal pole | cyan |
  | 7 / 8 | Seilrutsche / Rutschschiene | zip line / rail slide | pink |
  | 9 | Leiter | ladder | green |
  | 10 | Volumen | volume | blue |
  | 11 | Seil | rope | orange |
  | 12 | Deckung | cover | lilac |
  | 13 | Pfostenkopf | perch | magenta |
  | 14 | Balken | balance beam | light green |
  | 15 | Säule | pillar | dark orange |
  | 16 .. 20 | Griff 2 / 1 / 4 / 3 oben links / 3 oben rechts | hold 2 / 1 / 4 / 3 top left / 3 top right | white |
  | 22 / 23 | Felsader (TU) / Art 23 (TU) | rock vein (TU) / type 23 (TU) | brown |

  There is no markup type for wall-jump pairs: the climbing wall of 00:01 is made of free-climb holds (types 16 .. 20,
  class DICE) - each hold a 3-point line, drawn as a "V"; the jump between holds is chosen at run time by the jump
  targeting (`gt+0xa64` jump-target box).
- **RoomOnly and fading.** With `dbg.roomonly` a box stays when its stream unit entry is Lara's, its owner's `+0xe0` unit
  is Lara's, or a point lies within `[Debug] RoomNear`; lines and labels within 15 m fade behind geometry like the trigger
  labels (`dbg.occlusion`, key = the box address).
- **Bar.** Page Render, group "Markup / Kanten / Physik / SAP": the rows `Markup` and `Nur Kanten` come first now.
- 6 byte checks (`kW5MkChecks` = `work\w5_1411\precheck_02243.txt`, `pe_bytes_check`: 6 / 0 on the Steam exe); on a
  mismatch object markup is left out and no query filter applies (log line `0.22.43 W5: ...`). Menu page Markup shows the
  counters of the last frame. No new INI key, no new item.

### TO TEST 0.22.43

1. Start, `TruMenu.log`: `0.22.43 W5: draw.markup - object markup through the owner's bone matrix, ...: ok (6 checks)`.
2. DLC 1 `dlc_dungeon`, the wall with the round windows (21:53, Lara about 1504 / 1394 / -1320), `Markup` on: **no
   coil** in the air; the yellow rings sit on the pillar_of_doom objects (or are gone while those objects are disabled /
   hidden). Labels `Kante #2187` ... at the pillar.
3. DLC 1 `dlc_caverns`, the skull-niche hall (21:20, Lara about -459 / -1333 / -122), looking up: do the **three parallel
   yellow lines** stay? If yes, their labels name type + id - please note them (the W5 data search found no exact match;
   the best candidates are the cavern gate ledges `Kante #2309 / #2310 / #2312`, which now move to the gates).
4. Same place, `Nur aktueller Raum` on / off: with it on, only markup of Lara's unit or within 30 m stays (menu page
   Markup: "left out by RoomOnly" counts the rest).
5. `dlc_dungeon` wooden post (x -268 / y 10178): labels `Pfostenkopf #2170` and `Säule #2175` at the top.
6. Main game Mediterranean climbing wall (00:01): white V lines labelled `Griff 3 oben links #65` etc.
7. Thailand `l2_junglehub` (00:52 spot): the grey 3-point line is labelled `Sprungziel #639`.
8. Label behind a wall with `dbg.occlusion faded`: line and label pale; `hidden`: gone.
9. Bar page Render: group "Markup / Kanten / Physik / SAP" starts with `Markup`, `Nur Kanten`.

## 0.22.42 - W3: debug view after the test evening - room rule, near labels, de-clutter, empty jars, teaser icon (2026-11-14)

Built into `work\asi\menu0265`, not installed, no live test (finding in the workspace
`docs\Befund-W3-Debugansicht-1411.md`; owner live notes of 13.11., package D of `docs\Testabend-1311-Warteschlange.md`).
Section "0.22.42 W3 debug view" in `TruMenu.cpp`; render thread, read only - nothing is written into tru.exe memory.

- **"Nur aktueller Raum" (`dbg.roomonly`) - why the bridge markers vanished** (21:15, `dlc_caverns`, Lara ~30 m before
  the portal to `dlc_caverns_hall`): the room was the unit whose intro array holds the instance's intro record, nothing
  else. The unit data show that this is too narrow: `dlc_level1_start`, loaded together with `dlc_caverns`, holds
  **copies of the bridge objects at the very same place** - `adrenaline_tracker` 9920 = caverns 9865 and intro 9921 =
  caverns 9864 (same position to 0.1 unit after the origin shift), trigger planes 9922 / 9923 / 9925 with the extents of
  9871 / 9867 / 9870 (`work/w3_1411/intros_caverns.txt`, `tools/manor_gate_scan.py intros`). Those instances counted as
  "another room" and were dropped although they stand on the bridge. **New rule:** an instance of another intro unit stays
  when its **own stream unit `+0xe0`** (INSTANCE_SetCurrentStreamUnitID 0x5b3a56, the 0.21.1 `kRkChecks`) is Lara's
  stream unit, or when it is within **`[Debug] RoomNear`** (default 3000 = 30 m, `dbg.roomnear <0 .. 20000>|off`, 0 = the
  unit alone). Every verdict is logged **once per instance and Lara unit** (at most 20 lines per 10 s, held-back lines
  are counted in the next one):
  `dbg.roomonly: dlc1_uo_... 9921 (0x........) dropped - another unit, farther than RoomNear - intro unit
  dlc_level1_start, own stream unit (+0xe0) dlc_level1_start, Lara's unit dlc_caverns, 34.2 m from Lara, RoomNear 30.0 m`
  (or `kept - its own stream unit is Lara's` / `kept - within RoomNear`). The `dbg.roomonly` / `dbg.roomnear` values
  count the verdicts since Lara entered her unit.
- **Distance in metres by default:** `[Debug] DistMetres` default **1** (code, example INI, switches row); an installed
  INI keeps its own value.
- **Near labels never pale** (21:17: the medipack 5.4 m in front of Lara and Lara's own label were faded): within
  **`[Debug] OcclNear`** (default 600 = 6 m, `dbg.occlnear <0 .. 5000>|off`) of Lara no label fades, Lara's own label never
  does (its test point lies inside her model), and the occlusion test point of object names and uber labels is
  **1 m above the origin** (was 0.6 m; the origin of a floor object lies on / under the floor).
- **De-clutter** (23:30 three or four labels on top of each other at Lara's feet, 23:32 / 23:51 the same jar or switch
  labelled twice): the 0.16 tags, collectibles, key items, object names and the uber labels share **one rect list per
  frame**; the uber labels are drawn **after** the debug view now. An instance another layer labelled this frame gets no
  second label - the uber layer adds only its **state line** right under that label. The same object id within 50 units
  = **one** uber label with `x n`. A covered box moves up at most **`[Debug] LabelStack`** box heights (default 3; the
  0.20 labels moved once, names never), and at most **`[Debug] LabelCellMax`** labels (default 5) are drawn per cell of an
  8 x 6 screen grid (the nearest first; 0 = no cap). The uber state line and `dbg.names` / `dbg.collect` counts name
  how many labels were joined / stacked / left out.
- **Empty jars hidden** (`[Debug] HideEmptyPots` default 1, `dbg.emptypots`, bar Level data "Leere Kruege
  ausblenden"): no label at plain breakable jars (`*weightbreak*` without the reward kind, e.g. `ar_pt_weightbreak_b`) and
  at reward containers (0.20 kind "pot") **without a reward index** (intro data +0x30) or **with the game's reward bit
  set** - in the collectibles, object names and uber layers (with RoomOnly the uber layer took every `_pt_` object).
- **Teaser icon only in the main menu** (it showed during the DLC 1 credits): drawn only while the front-end state byte
  `0xfae8da` is **3 (MainMenu)** and **no one-shot Bink movie** plays (handle `0xa039bc` set with the loop byte `0xa039dc`
  = 0; the main menu itself runs inside the looping `medsea_loop`, PlayMovie passes loop 0) - 3 byte checks
  `kW3AtChecks`; a difference = shown as in 0.22.41. One log line per change: `menu.attracticon: hidden - a movie plays
  (no loop: credits / teaser) (front-end state ..., Bink handle 0x..., loop 0)` - the live proof which state the
  credits have. **Click and credits:** the click that ends the credits is the **game's own Bink skip** (0x4a1492 ..:
  actions 9 / 13 / 87 or the latch `[0xa02ba8]` bit 1 read and cleared by 0x4828f0; no skip test in front-end state 3, or
  2 with 0x4c5300) - TruMenu passes clicks unchanged while its menu is closed and injects none.
- New INI keys 5 (283), switches rows 5 + 1 changed (DistMetres default 1, since 0.22.42), items 3, bar rows 1, help rows
  1, menu page Debug view: sliders room distance / never faded, checkbox empty jars. Check: `trumenu_ini_check`
  `check_02242` (`check_02237` takes DistMetres 1, `check_02239` / `check_02241` take the appended parts). Build: 0
  warnings in TruMenu.cpp.

```text
0.22.42 W3: RoomNear 3000 (+ own stream unit +0xe0: ok), OcclNear 600 (test point +100), HideEmptyPots 1, LabelStack 3, LabelCellMax 5, DistMetres 1; teaser icon main menu only (front-end state 3, no one-shot movie): ok (3 checks)
dbg.roomonly: adrenaline_tracker 9920 (0x........) kept - within RoomNear - intro unit dlc_level1_start, own stream unit (+0xe0) dlc_level1_start, Lara's unit dlc_caverns, 20.4 m from Lara, RoomNear 30.0 m
menu.attracticon: hidden - a movie plays (no loop: credits / teaser) (front-end state 3, Bink handle 0x........, loop 0)
```

### TO TEST 0.22.42

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | start | start, `TruMenu.log` | `0.22.42 W3: RoomNear 3000 (+ own stream unit +0xe0: ok), OcclNear 600 ... (3 checks)` |
| 2 | bridge | DLC 1 `dlc_caverns` at the bridge before the portal to `dlc_caverns_hall` (claude.mark 21:14 place), `dbg.uber 1` + `dbg.keyitems 1` + names, "Nur aktueller Raum" on / off | the bridge markers stay with RoomOnly on; log `dbg.roomonly: ... kept - within RoomNear` / `kept - its own stream unit is Lara's` for the `dlc_level1_start` copies, `dropped` only for far objects of other units |
| 3 | room distance | same place, `dbg.roomnear off` | the strict 0.22.37 rule: the copies of `dlc_level1_start` are dropped, log lines `dropped - another unit ...` (the reason per object); `dbg.roomnear 3000` = back |
| 4 | room log | walk through the portal into `dlc_caverns_hall` | new verdict lines for the new Lara unit (once each); never more than 20 lines per 10 s |
| 5 | metres | any label, fresh INI (or `DistMetres` removed) | `5.4m ^1.2m` instead of `540u`; `dbg.metres 0` = game units |
| 6 | near not pale | the 21:17 place (medipack on the floor in front of Lara), Occlusion faded | medipack label and Lara's label full colour; walk away > 6 m behind a wall - faded; `dbg.occlnear off` = the 0.22.37 look |
| 7 | overlap 1 | Mediterranean, the 23:30 place (big cogs, thick pillar), `dbg.uber 1` | no labels on top of each other: stacked up to 3 steps, the rest left out; the uber state line counts `joined / without a free place` |
| 8 | overlap 2 | kraken room, the jar room of 23:51, names + collectibles + `dbg.uber 1` | `ar_pt_weightbreak_reward ... enthaelt Artefakt #1` once, with the uber state line under it; `ms_ei_switch_oneway_wall 30` once |
| 9 | same object | a place with two instances of one object at one spot (DLC 1 bridge) | one uber label with ` x2` |
| 10 | empty jars | jar room 23:51, collectibles + names, RoomOnly on | the plain `ar_pt_weightbreak_b` jars have no label; the reward jar has; after its artifact is picked up it has none; bar Level data "Leere Kruege ausblenden" off = all jars again |
| 11 | cell cap | look at a crowded place, `LabelCellMax=1` in the INI (game closed) | at most one label per screen cell (8 x 6) |
| 12 | teaser icon | main menu, style 7 | icon as in 0.22.41; log `menu.attracticon: shown - main menu (front-end state 3, ...)` |
| 13 | credits | finish DLC 1 (or the end jump) and let the credits run | **no** teaser icon during the credits; log `menu.attracticon: hidden - ...` names front-end state, handle, loop - report that line; after the credits the main menu shows the icon again |
| 14 | credits click | during the credits one mouse click | the credits end (game's own skip); TruMenu log has no line of its own for it |
| 15 | negative: room off | `dbg.roomonly 0` | no `dbg.roomonly:` log lines at all, every room labelled as before |
| 16 | negative: values | `dbg.roomnear 20001`, `dbg.roomnear -1`, `dbg.occlnear 5001`, `dbg.occlnear abc` | usage line each, value unchanged |
| 17 | negative: jars off | `dbg.emptypots 0` | every jar labelled as in 0.22.41 (plain jars, collected reward jars grey with LabelCollected 1) |
| 18 | negative: level | in a level the teaser icon never shows (front end only, unchanged) | no icon |

## 0.22.41 - Q126c: compact attract styles without a box (2026-11-14)

Built into `work\asi\menu0264`, not installed, no live test (finding in the workspace
`docs\Befund-AttractIcon-Kompakt-1411.md`). Feedback of the project owner after trying 0.22.40: no time next to a
filling circle (the circle already shows it), the **small** circle rather than the large one (styles 4 / 6), **no box**
around it, shorter texts (only time + counter). Styles **8 .. 16** are appended to the same cycle switch; 0 .. 7 stay
exactly as in 0.22.40 and the **default stays 7** until a style is picked. Values, slot, counters and the log line are
those of 0.22.39; read only, no new byte checks.

All new styles are drawn by `DrawAtBare` without the box (`ImGuiWindowFlags_NoBackground`); circle and text get a dark
ground / shadow instead so they stay readable over the menu picture. The counter is the skipped teasers while NoAttract
holds (light blue), else the game's teasers (amber). **Blink** at each limit for all: three orange flashes - the circle
ground turns orange, texts turn orange (the box that flashed in 0 .. 7 is gone here).

| Value | Name (DE / EN) | Drawn |
|---|---|---|
| 8 | Klein, ohne Kasten / small, no box | small circle (3 font sizes, as style 2) + play icon, no strike, no text |
| 9 | Klein + Strich, ohne Kasten / small + strike, no box | as 8 with the red strike while NoAttract holds |
| 10 | Klein, Zahl daneben / small, count beside | small circle, left of it only the counter `×3` |
| 11 | Klein, Zahl darunter / small, count below | small circle, the counter `×3` centred below it |
| 12 | Klein, Zahl am Rand / small, count badge | small circle, the counter as a small rounded badge on its lower right edge (`3`) |
| 13 | Knapp: Zeit + Zahl / terse: time + count | one line `12s · 3` |
| 14 | Knapp: Zeit/Limit + Zahl / terse: time/limit + count | one line `12/40 · ×3` |
| 15 | Nur Zahl (Wort) / count only (word) | one line `übersprungen 3` / `skipped 3` (NoAttract off: `Teaser 1` / `teaser 1`) |
| 16 | Nur Zahl (Pfeil) / count only (arrow) | a drawn skip arrow (clockwise arc, head down) + `3`; NoAttract off a small play icon + `1` |

- Only the styles 13 / 14 show seconds; the circle styles 8 .. 12 never do. Without a clock yet 13 / 14 show `keine Uhr`
  / `no clock`; 15 / 16 show the counter anyway. A reason of NaWhy (checks differ / patch refused) greys the circle and
  stands in place of the counter in 10 / 11 / 13 .. 16 (8 / 9 / 12: grey circle only). The counter shows 0 as well.
- Glyphs: only Latin-1 (`×`, `·`, `ü`) - the ImGui default font has no arrows, so the skip arrow of 16 is drawn.
- `menu.attracticon 0..16`: one or two digits or `off`; anything else (`17`, `123`, `1a`, `-1`, `on`) = usage, nothing
  changed; no argument = report. Bar row "Teaser-Anzeige" steps 0 .. 16 (at the ends "Ende"), e.g.
  `< 12 Klein, Zahl am Rand >`; help "Aus, Text oder Kreis bis zum Teaser (2-7, knapp 8-16)". Page Fixes row
  `AttractIcon` `int:0..16`, live. A value outside 0 .. 16 in the INI = 7 + one log line.
- INI keys 278 (0, the comment of `AttractIcon` +3 lines), switches rows 0 (changed), items 0, bar rows 0. Check:
  `trumenu_ini_check` `check_02241` (`check_02240` keeps the parts of 0.22.40 that did not change). Build: 0 warnings in
  TruMenu.cpp.

### TO TEST 0.22.41

Main menu, NoAttract on (`menu.noattract 1`) unless noted; one input in the menu first so the clock runs. Switch with the
bar row "Teaser-Anzeige" (left / right) or `menu.attracticon n`.

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | style 8 | `menu.attracticon 8` | small circle top right, light blue fill, play icon, **no** box, no strike, no text |
| 2 | style 9 | right -> 9 | as 8 with the red strike |
| 3 | style 10 | right -> 10 | small circle, `×0` (later `×1` ...) left of it, no box, no seconds |
| 4 | style 11 | right -> 11 | small circle, `×n` centred below it |
| 5 | style 12 | right -> 12 | small circle, a small light blue badge with the number on the lower right edge |
| 6 | style 13 | right -> 13 | one line `12s · n`, no box, readable over the menu picture (dark shadow) |
| 7 | style 14 | right -> 14 | one line `12/40 · ×n` |
| 8 | style 15 | right -> 15 | one line `übersprungen n` (EN `skipped n`) |
| 9 | style 16 | right -> 16 | a drawn arrow (arc over the top, head down on the right) + `n` |
| 10 | blink | in each style 8 .. 16 wait for a limit (40 s) | 3 orange flashes (circle ground / text orange), counter + 1 |
| 11 | NoAttract off | `menu.noattract 0`, styles 9 / 12 / 15 / 16 | 9 without strike, amber; at the limit the teaser starts; 15 `Teaser 1`, 16 play icon + `1` |
| 12 | language | bar language EN, styles 13 .. 16 and the row | `skipped n` / `teaser n`, `no clock`; row `< 16 count only (arrow) >` |
| 13 | Fixes row | page Fixes, "Hauptmenü (TruMenu)", AttractIcon 7 -> 12 -> 16 | within about a second the style changes (live) |
| 14 | timer box | `menu.attracttimer 1` (tr), style 11 | the display sits below the timer box |
| 15 | old styles | `menu.attracticon 7`, then 2, 4 | exactly the 0.22.40 looks (box, text left / inside) |
| 16 | negative: values | `menu.attracticon 17`, `123`, `1a`, `-1`, `on`; then without argument | usage line each, style unchanged; no argument = report only |
| 17 | negative: bad INI | `AttractIcon=17` in the INI (game closed), start | style 7 and one log line `[Menu] AttractIcon=17 is not 0 .. 16 - 7 used` |
| 18 | negative: level | style 12, start a level | no display in the level (front end only) |

## 0.22.40 - Q126b: attract display styles, one cycle switch (2026-11-13)

Built into `work\asi\menu0263`, not installed, no live test (finding in the workspace
`docs\Befund-AttractIcon-Varianten-1311.md`; owner wish Q126b of 13.11.: "either the icon or only text, one switch
instead of two, several variants to pick from"). Same values, slot, counters and blink as 0.22.39 - only the drawing and
the switch changed; read only, no new byte checks.

`[Menu] AttractIcon` is now **one cycle switch 0 .. 7** (replaces `AttractIcon` 0 / 1 + `AttractIconText`), default
**7** = the 0.22.39 look, so nothing changes until a style is picked. Every circle style keeps the filling circle and the
play triangle; every style (1 .. 7) blinks orange three times at the limit.

| Value | Name (DE / EN) | Drawn |
|---|---|---|
| 0 | Aus / off | nothing (the update slot is put back as in 0.22.39 when nothing else wants it) |
| 1 | Nur Text / text only | the two lines `12 / 40 s` and `übersprungen 3` / `Teaser gestartet 1`, no circle |
| 2 | Kreis / circle | circle + play icon, no strike, no text |
| 3 | Kreis + Strich / circle + strike | circle + play icon, red strike while NoAttract holds, no text |
| 4 | Kreis, Text innen / circle, text inside | larger circle (about six font sizes, wider when the text needs it), small play icon in the upper part, `12 / 40 s` and the short counter (`übersp. 3` / `skipped 3`, `Teaser 1` / `teaser 1`) inside, white with a dark shadow; no strike |
| 5 | Kreis, Text unten / circle, text below | circle + play icon, both lines centred below it; no strike |
| 6 | Kreis + Strich, Text innen / circle + strike, text inside | as 4 with the red strike over the small icon |
| 7 | wie 0.22.39 (Text links) / as 0.22.39 (text left) | the 0.22.39 look: circle + strike, the two lines left of it |

- Bar: Spiel-Einstellungen / Hauptmenü **"Teaser-Anzeige"** (was the bool row "Teaser-Symbol (Kreis)"), a value row:
  left / right step 0 .. 7 (at the ends "Ende"), the row shows `< 4 Kreis, Text innen >` (EN: `< 4 circle, text inside >`).
  Help "Aus, nur Text oder Kreis bis zum Teaser (Varianten 2-7)". Page Fixes, group "Hauptmenü (TruMenu)": one row
  `AttractIcon` `int:0..7`, live (the row `AttractIconText` is gone).
- `menu.attracticon 0..7` (item type `value`; one digit or `off`; anything else = usage, nothing changed; no argument =
  report, e.g. `4 (circle, text inside; the game's elapsed; clock read, 12.40 / 40.00 s = 31 %, ...)`). **`1` is now
  "text only"**, no longer "on"; `on` / `true` are refused.
- Old INI: `AtStyleRead` maps a 0.22.39 INI (key `AttractIconText` present) - `AttractIcon=0` -> 0, `1` + text 1 -> **7**,
  `1` + text 0 -> **3**; about a second after the start `AtReadSwitch` writes the mapped value to `AttractIcon`, removes
  `AttractIconText` and logs `menu.attracticon: TruMenu.ini of 0.22.39 (AttractIcon 1, AttractIconText 1) -> AttractIcon 7,
  AttractIconText removed`. `RunAt` removes the old key before it writes, so a new `1` is never read as the old "on". A
  value outside 0 .. 7 = 7 (one log line). Without both keys (an INI older than 0.22.39) the default 7 applies.
- In styles 4 / 6 a reason of NaWhy (checks differ / patch refused) is drawn below the circle (too long for inside).
- INI keys 278 (-1), switches rows -1, items 0, bar rows 0 (changed). Check: `trumenu_ini_check` `check_02240`
  (`check_02239` keeps the 0.22.39 parts that did not change). Build: 0 warnings in TruMenu.cpp.

### TO TEST 0.22.40

Main menu, NoAttract on (`menu.noattract 1`) unless noted, so the strike / light blue / `übersprungen` are visible; one
input in the menu first so the clock runs. Switch with the bar row "Teaser-Anzeige" (left / right) or `menu.attracticon n`.

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | old INI | before the start: `[Menu] AttractIcon=1` and `AttractIconText=1` in TruMenu.ini | the 0.22.39 look at once; after about 1 s the log line `... -> AttractIcon 7, AttractIconText removed`; TruMenu.ini then holds `AttractIcon=7` and no `AttractIconText` |
| 2 | old INI, text off | as 1 with `AttractIconText=0` | style 3 (circle + strike, no text); INI `AttractIcon=3` |
| 3 | style 1 | `menu.attracticon 1` | only the two text lines top right, no circle; at the limit 3 orange blinks |
| 4 | style 2 | right -> 2 | circle + play icon, **no** strike, no text; light blue while NoAttract holds |
| 5 | style 3 | right -> 3 | as 2 with the red strike |
| 6 | style 4 | right -> 4 | larger circle, small icon at the top, `12 / 40 s` and `übersp. 3` inside, readable over the fill; no strike |
| 7 | style 5 | right -> 5 | circle, both lines centred below it; no strike |
| 8 | style 6 | right -> 6 | as 4 with the red strike over the small icon |
| 9 | style 7 | right -> 7 | the 0.22.39 look (text left, strike) |
| 10 | blink | in each style wait for a limit (40 s) | 3 orange blinks, counter + 1 |
| 11 | NoAttract off | `menu.noattract 0`, styles 3 / 6 / 7 | no strike, amber; at the limit the teaser starts, `Teaser gestartet 1` (style 4 / 6: `Teaser 1`) |
| 12 | language | bar language EN, style 4 and 5 | `skipped 3`, `teaser 1` / `teaser started 1`; row `< 4 circle, text inside >` |
| 13 | Fixes row | page Fixes, "Hauptmenü (TruMenu)", AttractIcon 2 -> 5 | within about a second the style changes (live) |
| 14 | negative: off | style 0 (NoAttract 0, timer line 0) | display gone; log `menu.noattract off ...` (slot back) |
| 15 | negative: values | `menu.attracticon 8`, `on`, `12`; then without argument | usage line each, style unchanged; no argument = report only |
| 16 | negative: bad INI | `AttractIcon=9` in the INI (game closed), start | style 7 and one log line `[Menu] AttractIcon=9 is not 0 .. 7 - 7 used` |
| 17 | negative: level | start a level | no display in the level (front end only) |
| 18 | timer box | `menu.attracttimer 1` (tr), style 4 | the display sits below the timer box |

## 0.22.39 - Q126: attract icon in the main menu (2026-11-13)

Built into `work\asi\menu0262`, not installed, no live test (finding in the workspace `docs\Befund-AttractIcon-1311.md`;
owner idea Q126 of 13.11.). Section "0.22.39 menu.attracticon" in `TruMenu.cpp`; read only - nothing new is written into
tru.exe memory, no new byte checks (the 13 `kNaChecks` rows of 0.22.20 pin the clock layout and the update slot).

**What it shows** (top right, only in the front end = main state 6 / 10, never in a level; below the teaser timer box
when `menu.attracttimer` is on in the same corner):

| Part | Meaning |
|---|---|
| circle | fills clockwise from 12 o'clock with the way to the teaser limit: the game's AttractTimer clock (generalbank script 60 member 4, captured at the clock f11 native as in 0.22.20) - elapsed `+0x10` / alarm `+0x14` (init block 40.0 s, repeat 1). With `menu.noattract` holding the clock (real elapsed kept at 0): the 0.22.21 shadow count (the dt the game handed the clock since its last (re)start) modulo the alarm - after each skipped teaser the circle starts empty again |
| icon in the middle | a play triangle (the teaser video); crossed out in red while NoAttract holds |
| colour | amber = the game's teaser will start, light blue = NoAttract holds, grey = no clock yet / code differs |
| text left of the circle (`[Menu] AttractIconText`, default 1) | `12 / 40 s` (whole seconds passed / limit; `(Pause)` / `(steht)` when the clock is paused / stopped), then `übersprungen 3` / `skipped 3` (NoAttract holds) or `Teaser gestartet 1` / `teaser started 1` (the game's teaser) - counts since the game start; `Teaser: noch keine Uhr` until the timer's next START / RESTART (an input in the menu); the NaWhy reason when the 0.22.20 checks failed |
| blink | each time the limit is reached the box flashes orange three times in 1.2 s (the timer box: 1 s orange) and one `TruMenu.log` line: `menu.attracticon: limit 40.0 s reached - teaser skipped (NoAttract holds the clock) (3 this session; skipped 3, game's teaser 0)` |

- `menu.attracticon 1|0` (no argument = report, never a flip; a bad value = usage), `[Menu] AttractIcon` (**default 1**,
  written back at once), `[Menu] AttractIconText` (default 1). Both keys are re-read about once a second (`AtReadSwitch`
  from `NaTick`), so the new switches rows (page Fixes, group "Hauptmenü (TruMenu)") are `live`. Bar: Spiel-Einstellungen
  / Hauptmenü "Teaser-Symbol (Kreis)" after "Teaser-Uhr anzeigen"; help "Kreis oben rechts füllt sich bis zum Teaser +
  Zähler"; greyed with the reason of `menu.noattract` (checks differ / patch refused).
- Mechanism: `NaTick` patches the update slot 0x84584c for hold || timer line || icon (0.22.21 did it for the line);
  with the icon alone `NaUpdate` writes nothing (its hold branch needs `g_naWant`). `NtPost` calls `AtOnLimit(held)` when
  it sees the limit (held: the shadow passes alarm x n; not held: the game's clock fired in this update) - counted also
  while the icon is off, logged only while it is on. "Teaser gestartet" counts the clock firing; the clock event (f2)
  still checks front-end state != 4 and two `stdscreenmgr` tests before it starts the teaser, so a count with no video
  is possible in theory (not seen yet).
- Because the default is 1, the update slot is now patched (read only) in every start and ImGui draws in the main menu
  without any other overlay. `menu.attracticon 0` (or the INI / switches row) puts the slot back when neither NoAttract
  nor the timer line wants it.
- `menu.attracticon` without an argument reports e.g. `1 (text 1; NoAttract holds - shadow modulo the alarm; clock read,
  12.40 / 40.00 s = 31 %, skipped 3, game's teaser 0, 3 blink(s))`.
- New INI keys 2 (279), switches rows 2 (+ group), items 1, bar rows 1. Check: `trumenu_ini_check` `check_02239`
  (`check_02221` accepts the NaTick condition with the icon). Build: 0 warnings in TruMenu.cpp.

### TO TEST 0.22.39

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | start | start the game, main menu, touch nothing | icon top right: `Teaser: noch keine Uhr` until the first input in the menu (or at once when the timer started at the menu entry); `TruMenu.log`: `menu.noattract / attracttimer on: update slot 0x84584c -> NaUpdate (teaser timer line / attract icon only ...)` |
| 2 | fill | one input in the menu, then wait | the circle fills clockwise, text counts `1 / 40 s` ... `39 / 40 s` at the game clock (half speed after "back to the main menu" from the pause screen unless TruQoL `FrontEndPauseBit` is on) |
| 3 | input resets | press a direction at ~20 s | circle and seconds back to 0 (script 7 -> RESTART) |
| 4 | teaser | NoAttract off, wait for the limit | 3 orange blinks, log line `... the game's teaser starts (1 this session ...)`, the teaser video plays; `Teaser gestartet 1` |
| 5 | skipped | `menu.noattract 1`, wait 40 s, then 80 s | at 40 s and 80 s: blinks, log line `teaser skipped`, `übersprungen 1` / `2`, the menu stays; the circle starts empty after each skip; the play icon is crossed out, the colour light blue |
| 6 | timer box | `menu.attracttimer 1` (corner tr) | the icon sits below the timer box; both blink at the same limit |
| 7 | text off | page Fixes, group "Hauptmenü (TruMenu)": "Teaser-Symbol: Sekunden + Zähler" off | within a second only the circle remains |
| 8 | language | bar language EN (`quick.lang en`) | `skipped 2`, `teaser started 1`, `Teaser: no clock yet` |
| 9 | negative: level | start a level | no icon in the level (front end only) |
| 10 | negative: off | `menu.attracticon 0` (with NoAttract 0 and the timer line 0) | icon gone; log `menu.noattract off ...` (slot put back); `menu.attracticon` -> `0 (...)` |
| 11 | negative: argument | `menu.attracticon 2`, `menu.attracticon` | usage line for 2 (nothing changed); no argument = report only, no flip |

## 0.22.38 - PD: device glyphs on, dlc_fx_ filter, trigger edges faded whole, nearest triggers, corner ids (2026-11-13)

Built into `work\asi\menu0261`, not installed, no live test (finding in the workspace `docs\Befund-TruMenu-02238-1311.md`;
owner decisions of 13.11., live findings of the 0.22.37 run in DLC 1). Section "0.22.38 PD" in `TruMenu.cpp`; render
thread, read only - nothing new is written into tru.exe memory (the device glyph patch is the 0.22.30 one).
- **`[Input] DeviceGlyphs` default 1** (owner decision): the button prompts follow the last used device (pad symbols /
  key names, section 0.22.30) without editing the INI. An installed `TruMenu.ini` keeps its own value (`DeviceGlyphs=0`
  in an old INI stays 0) - the new switches row "Eingabe (TruMenu)" on page Fixes sets it (restart).
- **co_ / fx_ filter after a DLC prefix** (live 13.11.: `dlc_fx_*` / `dlc1_fx_*` kept their labels - only the name start
  was tested): `P5PrefixKind` skips `dlc_` / `dlc<digits>_` first, then the 0.22.37 rule with its exceptions
  (`co_rock*`, `*_grab_prompt`). Against the merged object lists (PC + Xbox TU / DLC, 1045 distinct names;
  `work/menu38_1311/prefix_names.py`): fx_ hidden 222 -> 298 (+74 `dlc_fx_*`, +2 `dlc1_fx_*`); there is no `dlc2_fx_*`
  and no `dlc*_co_*` (the rule takes them anyway); `co_fx_*` stays a co_ object; `rainfx*` / `fxt_rain_four` are no
  fx_ names and stay labelled.
- **Trigger edges faded whole** (`[Debug] Occlusion` 1 / 2; live 13.11.: edges cut into loose pieces by the depth test):
  every edge of a trigger carries a key (box 12 edges, plane 4 + 2 diagonals + the normal, sphere one key per circle of
  24 segments, the "Lara in" outline its own keys). In the 0.16 depth pass each edge gets a **pair of D3D9 occlusion
  queries** on the same screen quads (3 px, no colour): all pixels with the depth test off and the visible ones with the
  0.16 test. The answer of an earlier frame decides: all visible (within 3 %) or no answer yet = drawn as before
  (depth-tested); partly or wholly behind geometry = **drawn whole and faded** (30 %, no depth test); wholly hidden with
  Occlusion 2 = left out. 192 pairs, at most 96 edges asked per frame in turn, an answer counts 90 frames; released at
  Reset. `[Debug] Occlusion 0` or no depth mapping = as before. The `dbg.occlusion` value counts the faded / left-out
  line pieces and the pairs. Note: the floating yellow strokes of the live pictures 7 - 12 turned out to be the game's
  climbing **markup** (switch "Markup"), not trigger edges - this change does not touch the markup drawing.
- **Fewer triggers:** `[Debug] TriggerNearest` (default 0 = all, item `dbg.trignear <0 .. 64>|off`, bar Darstellung
  "Trigger: Lara + 8 nächste" / "Trigger: alle", menu slider): only the triggers Lara stands in plus the n nearest
  others (nearest to the camera = the list order; enclosing / cap rules first). The state line names how many were left
  out.
- **Trigger number at a corner:** `[Debug] TriggerCornerId` (default 1, item `dbg.trigcorner`, bar "Trigger-Nummer an der
  Ecke"): `#<intro id>` (the id of the trigger labels) at box corner +x +y +z / plane corner +x +z in the trigger's
  colour, faded (or left out with Occlusion 2) when all edges of that corner are behind geometry; at most 64 per frame.
- New INI keys 2 (277), switches rows 3 (`TriggerNearest`, `TriggerCornerId`, `[Input] DeviceGlyphs`), items 2, bar rows
  3. Check: `trumenu_ini_check` `check_02238`; `check_02230` accepts the new DeviceGlyphs default. Build: 0 warnings in
  TruMenu.cpp.

```text
0.22.38 PD: [Input] DeviceGlyphs 1 (default 1 since 0.22.38); co_ / fx_ filter also after dlc_ / dlc<n>_; trigger edges faded whole with Occlusion faded (192 query pairs, 96 edges per frame); TriggerNearest 0, TriggerCornerId 1
0.14 debug view drawn: triggers 37 drawn (...) ... Lara in 1; 0.22.38: 0 beyond the nearest 0 (TriggerNearest), 31 corner id(s); ...
```

### TO TEST 0.22.38

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | start | start, `TruMenu.log` | `0.22.38 PD: [Input] DeviceGlyphs ...` line; with an old INI `DeviceGlyphs 0` |
| 2 | glyphs | page Fixes, group "Eingabe (TruMenu)": `DeviceGlyphs` on, restart; pad, then keyboard | pad symbols / key names switch with the last device (0.22.30 TO TEST 4 - 6) |
| 3 | dlc_fx_ | DLC 1 (`dlc_watertunnel` / `dlc_dungeon`), object names `*` | no `dlc_fx_*` / `dlc1_fx_*` labels; `dbg.hidefx 0` = back |
| 4 | edges faded | triggers on, a box partly behind a wall, `dbg.occlusion faded` | the hidden edges are drawn whole and faded, no loose pieces; the free edges as before |
| 5 | edges hidden | same place, `dbg.occlusion hidden` | wholly hidden edges gone, partly hidden ones whole + faded |
| 6 | negative | `dbg.occlusion off` (or `[Debug] Depth=0`) | edges as in 0.22.37 (cut by the depth test / on top) |
| 7 | nearest | bar "Trigger: Lara + 8 nächste" | only the boxes Lara is in + 8 others; "Trigger: alle" = all again; state line `n beyond the nearest 8` |
| 8 | corner id | `dbg.trigcorner 1` | `#<intro>` at one upper corner of each box / plane, same number as the trigger label; behind a wall faded |
| 9 | load | look around fast for a minute with many triggers | no stutter compared to 0.22.37; `dbg.occlusion` value: pairs issued / answered grow |

## 0.22.37 - debug view P5: symbols, rooms, key items, draw distance, occlusion, chain after Paket R (2026-11-13)

Built into `work\asi\menu0260`, not installed, no live test (finding in the workspace `docs\Befund-P5-Debugansicht-1311.md`;
owner wishes of Paket R 12.11. = Q119 / Q120, data of P1 `docs\Befund-P1-Mittelmeer-Objekte-1311.md`). Section
"0.22.37 debug view P5" in `TruMenu.cpp`; render thread, read only - nothing is written into tru.exe memory.
- **Name / symbol / both per layer:** `[Debug] StyleCollect`, `StyleKeyItems`, `StyleNames`, `StyleCheckpoints`,
  `StylePortals` = `name` | `symbol` | `both` (default `both`), item `dbg.labelstyle <layer>|all <name|symbol|both>`
  (`dbg.style` stays the 0.16 display info). Symbols are ImGui primitives on a dark disc (no texture files): artifact
  (diamond), treasure (coin), relic (star - when the game's reward table names the index a relic), reward jar (with
  `#n` beside it in symbol-only mode), medipack (box with cross, `*_rw_shard` = health pack per P1), switch / lever,
  door / gate, key item (key), key-item target (rings), grapple point (hook), checkpoint (flag), portal (frame with
  arrow). An object name without a symbol keeps its text in symbol-only mode. The **legend** gets one row per symbol
  drawn this frame (symbol instead of the colour square, count).
- **Distance, height, room:** collectible, key-item and object-name labels name the room **always** (`[Debug]
  LabelRoom` 1, item `dbg.room`): readable DE / EN name in the bar language (`Kraken-Raum` / `Kraken room` for
  `l1_kraken_room`), fallback the unit name; trigger / checkpoint / portal labels keep the 0.16 rule (room only when it
  is not Lara's unit) with the readable name. Names = `kRoomNames`, generated with the chapter rows
  (`work\b_nav_1211\q105_order_table.py` ... `OUT_ROOMS` -> `q105_room_names.txt`, 111 units; a reading of the unit
  name - the game has no room names). **`[Debug] DistMetres`** (item `dbg.metres`, default 0 = the documented
  `5140u ^2540u`): 1 = `51.4m ^25.4m`.
- **Collected = the game's own bit:** the reward pickup 0x5db6a0(index) sets bit `index & 31` of
  `[[0xc59264] + 0x3ed90 + (index >> 5) * 4]` once (P1); index = intro data +0x30. Collectibles (`dbg.collect`), key
  items and the name labels follow `[Debug] LabelCollected` for a set bit (0 = no label, 1 = grey ` | eingesammelt`),
  also when the game still draws the instance (`labels: ... no label - reward bit +0x3ed90 set (0.22.37)`). A hidden
  instance without the bit stays out as in 0.21. Relic / treasure from the reward table `[0xe7f338]` (generalbank
  DTP 36) - the game loads it at the first pickup of a session, before that the object name decides.
- **Key items layer** (`dbg.keyitems`, `[Debug] KeyItems`, bar page Level data, menu page Debug view): carryable parts
  (`_pt_` without weightbreak / reward, `*puzzle_piece*`, `*_key*`), switches / levers / pressure plates, doors /
  gates, grapple points, and **P1's part -> target links** (`kP5Links`, unit + intro ids from the script members P1
  read in the unit data: eye pieces 232 / 233 -> centre 231 -> CP 234, keys 970 / 971 -> 976 / 978, switch 498 ->
  tomb door 497, switch 30 -> platform 27 + chains 61 / 62, switches 55 / 57 -> cogs 36 / 32 + kraken 33, hint 353 ->
  grapple wall 326, wall switch 748 -> gate 743 + flint walls 746 / 747, scene 51 (42) -> gate 45, locks 69 / 70, pings
  66 - 68) as a **world line** part -> target (depth path). State line: part `liegt` / **`getragen?`** (link parent
  id `inst+0x228` != 0 - the field the save writer stores at 0x555422; that it means "carried" is **not proven live**)
  / `eingesetzt / weg` (not drawn any more); the instance's uber node (`Zustand open` ...), a node named open / solved
  / destroyed / done / broken / dead / activated / complete = `= erledigt` (green). Radius / count = `[Debug]
  MarkRadius` / `MarkMax`.
- **Draw distance:** `[Debug] DrawDistance` (default 0 = off) caps the radii of triggers, collectibles / enemies, key
  items, object names and Thrall-Labels; rows per unit or area in **`TruMenu.debugview.txt`** next to tru.exe
  (`l1_kraken_room 8000`, `l1_* 12000`; a unit row wins over the longest prefix row). Item `dbg.drawdist <units>|off |
  here <units>|clear | reload` - `here` writes the row of Lara's unit at once; menu slider "draw distance here".
- **Behind walls** (`[Debug] Occlusion` 0 off / **1 faded** / 2 hidden, item `dbg.occlusion`): no engine ray is called -
  the targeter's sight ray (0x713200 -> 0x4935f0 -> 0x493330) is game-thread code with its own query record, the labels
  are drawn at Present. Instead every label anchor is tested against the **scene's own depth buffer**: inside the 0.16
  depth pass (`DpDrawBuffer`, same mapping `DpDepth`) a D3D9 occlusion query draws 5 x 5 pixels with no colour; the
  answer of 1 .. 3 frames ago dims (30 %) or drops the label. Needs `[Debug] Depth` 1 / 2 and an accepted depth
  mapping (`dbg.depthdump`), else the labels are drawn as before; the world markers / lines were already dimmed by the
  0.16 depth pass. 48 queries, released at Reset.
- **co_ / fx_** (`[Debug] HideCo` / `HideFx`, default 1, items `dbg.hideco` / `dbg.hidefx`): name labels and key items
  leave out `co_*` (cutscene objects - P1: 39 of 43 in a scene's cast; `co_rock*` stays) and `fx_*` (effects,
  `*_grab_prompt` stays).
- **Live wish 13.11. - only the current room, fade, readable names:** `[Debug] RoomOnly` (default 0, item
  `dbg.roomonly`, bar Render "Nur aktueller Raum", menu checkbox) keeps the **uber labels** (`dbg.uber`: gates,
  platforms, switches, levers) and the **key items** of Lara's room only - the room is her stream unit (the data has no
  finer room); an instance of an unknown unit stays. The uber labels now **fade behind walls** with the same `[Debug]
  Occlusion` (they get their anchor tested while a debug view layer keeps the depth pass running). **Readable names**
  next to the object name on uber labels, key items and object names: `kP5Readable` (37 name patterns, DE / EN in the
  bar language, the specific ones first), e.g. `ms_ei_switch_oneway_wall` -> "Wandschalter (einmalig)" / "wall switch
  (one-way)", `tp_ei_grapple_wall` -> "Greifwand", `*hpole*` -> "Stange (waagrecht)"; a name without a pattern stays
  as it is.
- **Live finding 13.11. (`dlc_watertunnel`, sewer bar):** with `RoomOnly` the uber labels take **every `_uo_` / `_ei_`
  / `_pt_` puzzle object of Lara's room** besides the uber states and `UberMatch` (the owner's `UberMatch=switch,lever`
  hid the sewer gate), radius at least 50000 (the room bounds it); the label names the readable name and the uber
  node in the bar language: `dlc1_uo_sewer_gate 9xxx (Kanaltor, verschlossen)` (`kP5NodeWords`: locked, open, closed,
  solved, destroyed, ... - an unlisted node keeps its name). The grey suffix of a hidden instance says **`versteckt` /
  `hidden`** unless it is a real collectible (`*_rw_*` / `*_pt_*reward*`) - before, `dlc_dispatcher` showed
  "eingesammelt". **Not built:** the label anchor stays the instance origin (`+0x20`) - an interaction / grab point or
  model bounds of an instance are not known in our data yet (the uber action 29 "interaction record" is unread, the
  model DTP has only the segment bind offsets); the sewer gate's origin is 51 m from its bar.
- **Chain after Paket R** (page Kapitel): same generator (`q105_order_table.py` `PAKET_R_FWD` / `PAKET_R_RET`, proof:
  every id a save intro of its unit, no checkpoint id lost): CP 76 on the **return visit** of `l1_kraken_room`, the
  saving cinematics 84 / 696 / 160 (scene 50) / 42 (scene 51), `checkpoint_l1_going_in` 672 / 673 / 781 on the way in,
  `_going_out` 674 / 675 / 782 on the way back; **7 return visits as rows of their own** (`visit 2`, "(Rückweg)",
  heading "Rückweg zum Boot (Paket R)"); a return row opens its checkpoints alone. 84 base rows + 7 = 91.
- **arena.load leak (N-5):** a level change no longer forgets the list with the extra references inside the engine:
  `QlTick` (Present = game thread) asks the pending request (GameTracker+0xb9) every frame, before its 100 ms gate,
  and gives every request of TruMenu whose tracker entry still carries its id `STREAM_DumpObject` 0x5c1790 once - the
  arena.unload call (Paket R: +0xb9 at 20:38:37.219, old units dumped .246, load .532). A change seen only afterwards
  releases in a loaded level only (main state 1, a player), never during the load; a portal move keeps the list. Log
  `arena.load: <why> - 0.22.37: TruMenu's references released before the level change (...)`.
- **Byte checks** `kP5Checks` (6, = `work\p5_menu_1311\precheck_02237.txt`, `tools/pe_bytes_check.py` on the Steam exe
  6 / 6 ok): reward bit test / set, table pointer, entry / record, kind, save writer +0x228. Failed: no reward bits, no
  relic from the table, no `getragen?` (the rest works).

```text
0.22.37 debug view P5: reward bits / table + link parent ok (6 checks); key items layer off; styles collect both, keyitems both, names both, checkpoints both, portals both; LabelRoom 1, DistMetres 0, Occlusion faded, HideCo 1, HideFx 1, DrawDistance 0, TruMenu.debugview.txt no TruMenu.debugview.txt; 25 link(s) of P1
0.14 debug view drawn: ... key items 6 of 9 (radius 15000; 2 link line(s) of 25 known; 0 hidden / gone without label; 412 instances); names ... 0.22.37: 14 co_ / fx_ hidden, 3 behind geometry hidden, 11 symbols); ...
arena.load: level change pending (GameTracker+0xb9) - 0.22.37: TruMenu's references released before the level change (mayan_thrall dumped; 1 dumped with 0x5c1790, 0 no longer held, 0 failed)
```

### TO TEST 0.22.37

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | start | start, `TruMenu.log` | `0.22.37 debug view P5: reward bits / table + link parent ok (6 checks)` |
| 2 | symbols | Mediterranean, `dbg.collect 1`, bar Render "Symbole + Namen" / "Nur Symbole" / "Nur Namen" | diamond / coin / jar with `#n` / medipack box; symbol-only = no boxes; legend rows with the symbols |
| 3 | room | any label in `l1_kraken_room` | ` [Kraken-Raum]` also in Lara's own unit; bar language en = ` [Kraken room]`; `dbg.metres 1` = `m` |
| 4 | collected | pick up an artifact with `dbg.labelcollected 1` | grey ` | eingesammelt` at once (bit set), log `... reward bit +0x3ed90 set` or a hide flag |
| 5 | key items | `l1_seafloor` eye puzzle, `dbg.keyitems 1` | key symbols at 232 / 233, target at 231, lines 232 -> 231 -> 234; picking up a piece: `getragen? (Eltern-Id n)` or not (= the meaning of +0x228, report) |
| 6 | key items 2 | `l1_kraken_room` at switch 498 | line 498 -> door 497, door `Zustand closed`, after the switch `open = erledigt` (green) |
| 7 | behind walls | names on, look at a label behind a wall | faded (default); `dbg.occlusion hidden` = gone; `dbg.depth off` = all drawn as before |
| 8 | draw distance | `dbg.drawdist here 3000` in the kraken room | labels only within 30 m; `TruMenu.debugview.txt` has `l1_kraken_room 3000`; `here clear` = back |
| 9 | co_ / fx_ | names `*` in `l1_seafloor` | no `co_light_rig` / `fx_haze_*`; `co_rock` and `fx_*_grab_prompt` stay; `dbg.hideco 0` = back |
| 10 | chain | page Kapitel, base game l1 | `l1_kraken_room (Rückweg)` with CP 76 / 75 below the heading "Rückweg zum Boot"; tomb 140 72 160 42 141 |
| 11 | arena.load | `arena.load mayan_thrall`, ready, then `level.load` | log `... references released before the level change (mayan_thrall dumped ...)`; `arena.enemies` afterwards `loadable` |
| 12 | negative | `[Debug] Depth=0` | no occlusion (labels as before), `dbg.occlusion` value says `waits for the depth mapping` |
| 13 | room only | `l1_kraken_room`, `dbg.uber 1` + `dbg.keyitems 1`, bar Render "Nur aktueller Raum" | only switches / gates / parts of the kraken room; `dbg.uber` value `... n outside Lara's room (RoomOnly)`; off = the neighbours again |
| 14 | readable | same place | `ms_ei_switch_oneway_wall 498 (Wandschalter (einmalig))`, `tp_ei_grapple_wall ... (Greifwand)`; bar language en = English |
| 15 | uber fade | `dbg.uber 1` with a debug view layer on, a gate behind a wall | the gate label faded (Occlusion 1) / gone (2) |
| 16 | room puzzle objects | `dlc_watertunnel` at the sewer bar, `dbg.uber 1`, "Nur aktueller Raum" on (own `UberMatch` kept) | `dlc1_uo_sewer_gate ... (Kanaltor, verschlossen)` and the other `_uo_` / `_ei_` / `_pt_` objects of the unit; off = as before |
| 17 | hidden text | names `*`, `dbg.labelcollected 1`, a hidden helper (e.g. `dlc_dispatcher`) | grey ` | versteckt`; a picked-up artifact ` | eingesammelt` |

## 0.22.36 - label filter: collected items and Lara's gear (2026-11-12)

Built into `work\asi\menu0259`, not installed, no live test (finding in the workspace `docs\Befund-Labels-1211.md`,
offline files in `work\labels_1211\`). Live bug of 2026-11-12: the white name labels kept collected artifacts
(`ar_rw_artifact` 678) and picked-up medipacks, while the 0.20 collectibles layer (`dbg.collect`) dropped them - only
`M20Draw` asked the 0.21 check (`TruMenu.log` "0.21: <n> hidden / collected instance(s) ... (label checks ok)").
- **One check for every name label:** `dbg.labels` (0.13, `DrawLabels`) and `dbg.names` (0.14 object names,
  `DvDrawNames`) now ask `LabelFilter`, which asks the same `LfNotDrawn` of 0.21 (no second implementation): an
  instance the game no longer draws - hide bit `+0x14 & 0x800`, kill flag `0x20`, scene entity off, draw masks
  `+0x23c | +0x240 == -1`. That covers every kind the game hides or removes after a pickup (artifacts, treasures,
  relics, shards, medipacks, ammo, keys, any other instance), not only names with `_rw_`. **`[Debug] LabelCollected`**
  (default 0, item `dbg.labelcollected`): 0 = no label, 1 = a grey label with ` | eingesammelt` / ` | collected` (bar
  language `[Quick] Language`).
- **Lara's own gear by game data** (no name list): an instance whose parent `+0x54` is the player (INSTANCE_BirthObject
  0x5bd270 stores its parent there at 0x5bd381; the give-gear path 0x716174 passes `[0xe7f094]` - `larabase` f37 and
  the default gear per unit) or one held by her weapon manager `[[0xfadb58]+0x500]` (15 slots x 2 hands, handles
  `+4 / +0xc + 16 * slot`, reader 0x6e7b90; gear list `+0xf4`, 8 handles). **`[Debug] LabelLaraGear`** (default 0, item
  `dbg.labelgear`): 0 = no label, 1 = labelled as before. Offline (`work\labels_1211\gear_dump_scan.py`, 3 full DLC 2
  dumps): `g_tanks`, 2 x `wp_dlc_handgun` (parent = player and weapon-manager slots 13 / 0) and `grenade_reticule`
  (parent = player, hidden) - no other instance has Lara as parent.
- **Byte checks** `kLgChecks` (11, = `work\labels_1211\precheck_02236.txt`, `tools/pe_bytes_check.py` on the Steam exe:
  11 / 11 ok); `g_lgOk` needs the 0.21 label checks too. Failed: gear is labelled as before, `dbg.labelgear` refuses.
- **Live switch:** both keys are read at the start and about once a second (`LgReadSwitch`, applied only when the INI
  value changed - an item switch without `[Debug] Persist` is not undone); `TruMenu.switches.txt` rows (page Fixes,
  group Diagnose (TruMenu)) write them.
- **Places:** menu page Debug view, group Object names (two checkboxes + last-frame counts); bar page Render, group
  Markup, after Objektnamen: "Namen: Eingesammeltes grau", "Namen: Laras Ausrüstung" (with help lines).
- **Log:** one line per instance that loses its label (at most 20 per 10 s), with the reason - the evidence for which
  flag a pickup sets:

```text
0.22.36 labels: collected / hidden check ok (8 checks, LfNotDrawn), Lara's gear ok (11 checks: parent +0x54 = player, weapon manager slots + gear list); [Debug] LabelCollected 0, LabelLaraGear 0
labels: dbg.names ar_rw_artifact 678 (0x........, parent 0x00000000) no label - hide bit 0x800
labels: dbg.labels g_tanks 1073741831 (0x........, parent 0x........) no label - Lara's gear ([Debug] LabelLaraGear 0)
labels: [Debug] LabelCollected 0 -> 1 (TruMenu.ini, live)
```

- `dbg.labels` value / `dbg.status`: `... n grey ..., m collected / hidden + g gear without label`.
- **Not covered:** an item whose pickup leaves the instance drawn (only a script value changes) keeps its label; a
  reward pot stays labelled after it was opened (the pot is still drawn - "contains artifact" is the 0.20 layer's
  text); the 0.21 runtime-copy rule (one label per pot) stays in the collectibles layer only. Gear the game gives
  without Lara as parent and outside the weapon manager would still be labelled (none seen in the dumps).
- **Checks:** `trumenu_ini_check` new `check_02236` (one `LfNotDrawn`, both layers through `LabelFilter`, gear by data
  only, `kLgChecks` = `precheck_02236.txt`, no game writes in the filter, keys / items / bar / menu / switches rows,
  the 0.22.35 hash in `Set-TruMenu.ps1`).

### TO TEST 0.22.36

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | start | start, `TruMenu.log` | `0.22.36 labels: collected / hidden check ok ..., Lara's gear ok (11 checks ...)` |
| 2 | collected | `dbg.names 1` (filter `*`) or `dbg.labels` with `LabelMatch=*`, pick up an artifact and a medipack | label gone at the pickup; log `labels: ... no label - <reason>` names the flag (hide bit / kill flag / scene entity / masks) |
| 3 | grey | bar Render "Namen: Eingesammeltes grau" on | the picked-up items get a grey label ` | eingesammelt`; off = gone again |
| 4 | gear | `dbg.names 1` near Lara, bar "Namen: Laras Ausrüstung" off / on | off: no `g_*` / `wp_*` / `grenade_reticule` labels on Lara; on: back; Lara's own name stays in both |

## 0.22.35 - base-game checkpoints in walking order, loop directions (2026-11-12)

Built into `work\asi\menu0258`, not installed, no live test (Q113; finding in the workspace
`docs\Befund-Q113-Levelkette-1211.md`, scripts in `work\q113_chain_1211\`). Only the table `kChapOrder` changes (no new
INI key, no byte check, no new item):
- **Checkpoints in walking order:** on the page Kapitel each base-game unit lists its checkpoints by their place
  between the entry and the exit portal of the proven level chain (`q113_chain.py` -> `q113_cp_order.txt` -> the B
  generator `work\b_nav_1211\q105_order_table.py`), not by the +0x52 editor number (group J: no walking order). Same 84
  units and 303 ids as before. A unit walked twice (way back) keeps its checkpoints with the first visit.
- **Headings:** the l1 loop with its direction (kraken_room -> Baldr stairs -> tomb -> side room -> hall -> back,
  from the cutscene numbers 45 / 49 / 50; inferred), the l2 loop (puzzleroom -> norsehall -> towers -> upperhallway ->
  back; the two doors to norsehall are alternatives), the l4 temple side trip in 4.2, the prologue units come again
  after 3.1.
- **Checks:** `trumenu_ini_check` new `check_02235` (kVersion part, rows = walking order of `q113_cp_order.txt`, 84 /
  303, the three headings, the 0.22.34 hash in `Set-TruMenu.ps1`).

### TO TEST 0.22.35

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | headings | page Kapitel (debug), Base game l1 / l2 / l4 / l3 | l1: "Rundweg ab l1_kraken_room: Treppen -> Grab ..." above `l1_baldrsstairs_a`; l2: "Rundweg ab l2_puzzleroom ..." above `l2_norsehall`; l4: "Abstecher in 4.2: Tempel ..." above `l4_templepath`; l3: prologue heading mentions the second pass |
| 2 | order | open `l1_ship_engine_hall`, `l1_baldrs_tomb`, `l2_puzzleroom` | engine_hall `1412 1411`; tomb `140 72 141`; puzzleroom starts `2817 2818 2824` |
| 3 | jump | right twice on the first and the last checkpoint of `l1_baldrs_tomb` | Lara at 140 near the stairs portal, at 141 near the side-room portal (5 m) |

## 0.22.34 - achievements, photo.pose, chapter 1.2, spawn child warning (2026-11-12)

Built into `work\asi\menu0257`, not installed, no live test (group M; finding in the workspace
`docs\Befund-Gruppe-M-1211.md`, scripts and byte lists in `work\m_menu_1211\`). New INI key `[Achievements] Enabled`
(default 1, read at the start), 36 new byte checks (23 achievements `kAchChecks`, 13 pose `kPpChecks`), all 36 lines of
`work\m_menu_1211\m_checks.txt` ok on `data\pc\tru.exe` and on the installed `tru.exe` (the same file, md5
`5560abac...`).

- **Achievements (Q20):** the PC keeps the script type `achievement` (generalbank script 66) and the scripts call its
  16 natives f0 - f15, but the binder 0x7abb80 binds every one to the empty 0x796620 (`jmp 0x6457a0` = `ret`). With
  `[Achievements] Enabled=1` TruMenu writes its own stub into each of the 16 `push 0x796620` (0x7abb8e + 14 k) **at the
  start** - before the generalbank binds the script, so the game's own bind 0x5768f0 stores the stubs. A stub records
  `achievement <id> <name> unlocked (native fN, G, args)` **once per profile** in `TruMenu.log` and as a line in
  `TruMenu.achievements.txt` next to `tru.exe` (profile, native, Xbox id, date / time, name); later calls are counted, the
  first repeat of a session is logged. Profile = the save folder the game uses (`CSIDL_PERSONAL\Eidos\Tomb Raider -
  Underworld` or `[Saves] Folder`; the PC has one save set per Windows user). No game data, no save written. Index ->
  achievement from the Xbox native stubs (`li r4, id`): f0 1 Prologue, f1 40 Mediterranean Sea, f2 41 Coastal
  Thailand, f3 42 Croft Manor, f4 43 Southern Mexico, f5 44 Jan Mayen Island, f6 45 Andaman Sea, f7 46 Arctic Sea, f8 2
  Master Survivalist, f9 - f11 23 - 25 Speed Demon I - III, f12 27 Master Speed Demon, f13 14 / f14 17 / f15 18 Swan
  Diver I / II / Master Swan Diver - **f12 - f15 unsure** (called from the shared script 5, not read yet). Items
  `ach.list` / `ach.status`; bar page Figur, group "Erfolge (Skripte, Q20)" (closed at the start: one row per
  achievement with the unlock time or "gesperrt"); big window page "Achievements / Erfolge"; switch row on page Fixes
  (Diagnose (TruMenu), restart). The executable's own achievements of the Xbox (treasures, chimney jump, motorbike,
  grenade, adrenaline headshot) have no PC code and are not in the list.
- **`photo.pose 1..7|next|off` (F2):** Lara's poses `screen_capture_01` .. `_07` = entries 1604 .. 1598 of her object's
  anim table (sections 1551 .. 1545, in `lara.drm`); no chart slot points to them. The game's own way to play a table
  entry by index on an instance is the anim request **0x444ba0 in mode 0** (the uber action "play anim" 0x4d86d9 and the
  script instance helper 0x4abb10 use it): it builds a one-entry slot record (0x4321d0: the index, speed 1.0) and starts
  it (0x4428a0) on processor 0 `[[inst+0x280]+0x14]`. Only in the photo mode (the world is paused there: Lara's own
  process - her chart - is skipped, her processors still get their per-frame update 0x443690); refused when the entry
  does not hold the expected section (another costume object) or is not resident. Before the first pose the processor's
  `+0x44` (the slot of the last mode-1 request) is noted; **`photo.pose off`**, `photo.off` and every automatic leave of
  the photo mode request that slot again in mode 1 (bounded by the object's slot count) - the anim Lara had, from its
  start; nothing is requested when the instance changed, a cutscene plays or a level change waits. Bar: page Figur,
  group Fotos: "Foto-Modus: naechste Pose", "Foto-Modus: Pose aus".
- **Chapter 1.2 (J-5):** page Kapitel shows "Kapitel 1.2 Niflheim" before `l1_kraken_entrance` (its title card runs
  from intro 696, the gate cutscene 40; group J) instead of "1.2?" at `l1_norse_hallway_a`; regenerated with
  `work\b_nav_1211\q105_order_table.py` (owner of chapter 1.2 added there).
- **`ai.spawn` child warning (K follow-up):** for a kind the game loaded itself, the same walk as arena.load's ready
  test (object + children at tracker status 2, anims resolved) - a missing child or anim gives a `WARNING` in the answer
  and the log; the spawn goes on.
- **Checks:** `trumenu_ini_check` new `check_02234` (byte lists, ids, order of tests and requests, INI key / switch row,
  rows, chapter table = generator output, the 0.22.33 hash in `Set-TruMenu.ps1`); `check_02230` accepts more INI keys.

### TO TEST 0.22.34

Main-game session; `[Cheats] Enabled=1`, `[Cheat] Experimental=1`, `[Achievements] Enabled=1` (default). Logs only
after the session header line.

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | achievements start | start the game, TruLink `menu ach.status` | `16 natives bound to TruMenu's stubs`; profile = the save folder; log line `0.22.34: achievements ...` |
| 2 | Prologue | finish the prologue (`l3_main_hall`, Croft Manor burning) | log `achievement 1 Prologue unlocked (native f0, 25 G ...)`; page Figur / Erfolge: f0 with date / time |
| 3 | persist | quit, start again, `menu ach.list` | f0 still unlocked with the first time; no second "unlocked" line when the script calls f0 again (`called again` once) |
| 4 | f13 swan dive | a swan dive from one of the three highest points over water | `achievement 14 Swan Diver I unlocked (native f13 ...)` - confirms f13 (else note what triggered f12 - f15) |
| 5 | Enabled=0 | `[Achievements] Enabled=0`, restart | `ach.status`: `Enabled=0 - the game's empty natives stay`; no achievement lines |
| 6 | pose | photo mode on, "Foto-Modus: naechste Pose" 7 times | Lara takes poses 1 .. 7 (screen_capture_01 .. 07) although the world is paused; log `photo.pose ... entry 1604 ...`; note whether she moves or freezes in the pose |
| 7 | pose off | "Foto-Modus: Pose aus", then "Foto-Modus aus" | Lara back in her anim from before (`her slot requested again`); after photo off she moves normally |
| 8 | pose + leave | pose 3, then Start (pause menu) | log `photo.pose: pose 3 off (the game's pause menu opened) ...`, then `photo: off ...`; normal after resume |
| 9 | pose guards | "Foto-Modus: naechste Pose" outside the photo mode; in a DLC costume | grey `only in the photo mode`; costume: refused with `holds section ...` or works (note which) |
| 10 | chapter 1.2 | page Kapitel (debug), Base game l1 | heading "Kapitel 1.2 Niflheim" above `l1_kraken_entrance`, none above `l1_norse_hallway_a` |
| 11 | spawn warning | arena 1a: `ai.spawn viking_thrall 1` | normal spawn, no `WARNING` (children resident); a `WARNING children not loaded` only where a child is missing |

## 0.22.33 - photo mode, arena.load, glyphs.status (2026-11-12)

Built into `work\asi\menu0256`, not installed, no live test (group K; finding in the workspace
`docs\Befund-Gruppe-K-1211.md`, scripts and byte lists in `work\k_menu_1211\`). No new INI key, 37 new byte checks
(23 photo mode `kPmChecks`, 14 object load `kQlChecks`), all 38 lines of `work\k_menu_1211\k_checks.txt` ok on
`data\pc\tru.exe` and on the installed `tru.exe` (the same file, md5 `5560abac...`).

- **Photo mode (F1 / Q78): `photo.on` / `photo.off` / `photo.shot` / `photo.status`** - the game's own free camera, not
  one of ours: the camera manager's slot of **mode 5** (FreeCamera `0xe8e9a0`, vtable `0x855e54`) through the manager's
  own switch **`0x5edd70(mgr, 5, 0)`** (`CAMERA_SetMode` 0x5f39f0 knows only 6 / 11 / 12, so `camera.mode 5` does
  nothing). The FreeCamera brings its own controls (left stick = fly, right stick / mouse = look, the game's actions 19 -
  22 = speed / up-down) and data (generalbank DTP 16: FOV 50, speeds); its activate turns Lara's control off itself
  (0x5d5f60). With it: the world pause bit `0xe7f0b8 | 0x1000` (as `time.pause`; the camera update 0x5f3df0 still runs
  - the world block jumps from 0x5dfeb2 to 0x5dff0f, the camera call is at 0x5dff14) and the UI byte `0xcdc9a0 = 1` (as
  `ui.hide`; the game's own screenshot task 0x774aa0 hides the HUD with the same byte around its frame redraw).
  **Refused** while a cutscene plays, a level change / level start waits, the main state is not 1, the game is paused
  (pause menu, `[0xe7f0b4] & 0x10000000`), flight or `cine.pause` is on, the camera manager runs another layer
  (`+0x4c`), holds its mode (`+0x7c`), or the current camera is not the slot of its mode. **`photo.off`** goes back with
  the same switch to the remembered mode (0x5edf50 restore only if mode / layer changed meanwhile, nothing if the game
  took the camera itself), puts the control byte back as before (0x5d5f60 again if it was off) and clears the pause bit /
  UI byte **only if `photo.on` set them** (an open menu's or the ring's pause becomes the photo mode's, as with
  `time.pause`). **Left by itself** (Present hook, game thread) on a level change request, a new player instance or
  stream unit, main state != 1, a cutscene start, the game's pause menu, or a camera the game switched to. TruMenu's
  own bar / big menu do not end it (they are the way to `photo.shot` / `photo.off`). Plugin unload: only the pause bit /
  UI byte back (no game call from DllMain). `photo.shot [name]` = `shot.save clean photo_<n>[_name]`. `shot.oncine`'s
  camera signal ignores the photo mode's camera. Bar: page Figur, group Fotos (four rows).
- **`arena.load <kind>` / `arena.unload <kind>|all` / `arena.enemies` (Q83):** loads one of the 26 enemy kinds of the
  Q83 table (`kQlKinds`, made by `work\k_menu_1211\ar_kinds_table.py` from the Q83 catalog) with the game's own **object
  request with reference 0x5c1760** (= 0x5c1550(id, 1), what a unit load does for every intro); no poll loop - the loader
  runs on by itself and the engine requests the children (chunkdoll, weapon, DLC 2 extension) at the load end. Before
  the request: not resident / not loading already, at most **2** kinds of arena.load, a volumetric kind (bat, sharks)
  only while a loaded unit has a 3D navigation image, the group's DRMs + 2 **tracker** entries free (204), the group's
  anim entries + 100 free in the **anim pool** (3000, no overflow test in the game), every DRM present (the game's
  FileExists 0x5bf7b0), `save.backup spawn` once per session (shared with `ai.spawn`). **Ready** = the object and every
  child (recursive) at status 2 with an object and every anim entry with an id resolved -> one log line `arena.load
  <kind>: ready after n ms`; `stalled after 30 s` names the first object that waits. **`ai.spawn` refuses a kind of
  arena.load until it is ready.** `arena.unload` calls STREAM_DumpObject 0x5c1790 once per own request while the tracker
  entry still holds the id (spawned instances keep their own reference - remove them first). A level change forgets the
  list (nothing dumped). `arena.enemies` lists each kind: resident / ready / loading a/b / loadable / refused with the
  reason; the 4 objects without enemy data are refused. Base and DLC kinds together: the answer warns (the first loaded
  copy of shared ids serves both). Bar: page Tests, group "Arena 1 - Kampf (Q76)": status row, eight load rows in the T19
  order, "release".
- **`glyphs.status` (Q95 follow-up):** `[Input] DeviceGlyphs`, the patch state, the device now (pad / keyboard / mouse -
  the last input), the last switch time (date + time) and the prompt counters; with `DeviceGlyphs=0` it says that no
  device is tracked.
- **Checks:** `trumenu_ini_check` new `check_02233` (byte lists, refusals, the way back, ticks, rows, help lines, no
  INI key, the 0.22.32 hash in `Set-TruMenu.ps1`); `check_02219` accepts a TruShadowPower patch version (`0.27.1`).

### TO TEST 0.22.33

Main-game session; `[Cheats] Enabled=1`, `[Cheat] Experimental=1`. Logs only after the session header line.

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | photo on | in free play: page Figur, Fotos: "Foto-Modus an (Freikamera)" | answer `photo mode on ...`; world stands, HUD gone, left stick flies, right stick / mouse looks, Lara does not move; log `photo.on ... FreeCamera 0x00e8e9a0 current` |
| 2 | photo keys | hold / press the game's keys of actions 19 - 22 (pad: try LB / RB / LT / RT) | slower / faster / up / down - note which button does what |
| 3 | photo shot | "Foto-Modus: Foto" (or F11) | PNG `photo_001` without HUD and TruMenu |
| 4 | photo off | "Foto-Modus aus" | camera back behind Lara exactly as before, world runs, HUD back, Lara moves; log `photo: off (photo.off) ... camera mode back (0x5edd70) ... world runs again, HUD back` |
| 5 | photo guards | try "Foto-Modus an" in a cutscene, in the pause menu, with flight on | refused with the reason (grey row with the reason in the bar) |
| 6 | photo auto-off | photo on, then Start (pause menu) | log `photo: off (the game's pause menu opened) ...`; after resume: normal camera, HUD, control |
| 7 | photo + time.pause / ui.hide before | `time.pause 1`, `ui.hide 1`, photo on, photo off | the pause bit and HUD stay as they were before photo on (`pause bit left`, `UI byte left`) |
| 8 | arena.enemies | arena 1a: "Gegnerarten (arena.enemies)" | `viking_thrall`, `yeti_thrall` resident; bat / sharks `refused: needs 3D navgraph`; the rest `loadable`; 4 `no enemy data` |
| 9 | arena.load | "Laden: mayan_thrall", immediately `ai.spawn mayan_thrall` | first `requested mayan_thrall ...`; the early spawn is refused `not ready yet`; log `arena.load mayan_thrall: ready after n ms`; then `ai.spawn mayan_thrall 1` fights, falls apart at death |
| 10 | limit | load `panther_thrall`, then `tiger` | the third is refused `2 kinds by arena.load already` |
| 11 | unload | `ai.remove spawned`, "Geladene Arten freigeben" | `mayan_thrall dumped (0x5c1790); panther_thrall dumped (0x5c1790)`; no crash; arena.enemies shows them `loadable` again |
| 12 | merc | "Laden: merc" (6 DRMs) | ready line; `ai.spawn merc 1` shoots? note memory (Watch-TruMemory) |
| 13 | glyphs.status | `[Input] DeviceGlyphs=1`, pad then keyboard then mouse; TruLink `menu glyphs.status` each time | `device now pad / keyboard / mouse`, the last switch time moves with each switch |

## 0.22.32 - arena: spawn health note, game mode check, three new spots (2026-11-12)

Built into `work\asi\menu0255`, not installed, no live test (group A; finding in the workspace
`docs\Befund-Gruppe-A-1211.md`, scripts in `work\a_arena_1211\`). Read only: no new write, hook, byte check or INI key.

- **`ai.spawn` (Q86):** the live case of 2026-11-11 21:02 ("the spawned thrall just stood and fell apart, LP 0 / state
  none") was the **one-hit-kill cheat**, switched on at 20:37:57 in the same session (`[0xe91ffd] = 1`; the enemy health
  component 0x62e370 then stores LP 0 on every hit, 0x62e39f): TruShadowCombat logged `LP 350 -> 0` from a 23.4 hit, the
  thrall had LP 350 like the placed ones and its AI ran (CombatStepIdle 0.1 s after the birth, RegenerateDeath, Regenerate,
  MoveNav, Vaulted, Death). The birth already runs the game's whole enemy init (0x63c190: brain, tune 0x637730, LP from
  the tune's health record by the EnemyHP step `[[0xc59264]+0x3ef98]` through 0x620cc0 / 0x6e77b0, senses, AI query
  0x632200) - the same path as placed and generator enemies. So nothing is set by hand; the answer now **names what the
  game gave**: `1 x viking_thrall at Lara: 0x... LP 350; EnemyHP step 1` and **warns while one-hit kill is on**. No name /
  a name that is not an exact loaded AI enemy object = the reason (no such object / not loaded here / no AI enemy) and
  **the list of the loaded kinds** (plus those containing the typed part: `ai.spawn thrall` lists `viking_thrall,
  yeti_thrall`). Syntax: `ai.spawn <exact object name> [1..5] [lara|front]`.
- **`arena.mode [spot]` (Q100):** the game mode now - the player object, the doppelganger byte `[[0xfadb58]+0x1244]`
  (cleared only by a new game tracker, TruDlc2Player `FlagReset`) and the TruDlc2Player flag -> "main-game mode
  (adrenaline runs)" / "DLC 2 doppelganger mode" / "MIXED"; with a spot it says whether that fits (main game: 0, DLC 2:
  1) and logs one line. **`arena.go`** reads the mode first: a main-game spot while the flag is set loads its unit with
  **`level.load`** instead of `unit.go` (a portal walk would keep the old tracker; the load makes a new one = flag 0,
  TruDlc2Player CostumeReset gives the unit's costume back), a DLC 2 spot without the flag warns (TruMenu never writes
  the flag); the shortcut ends with `arena.mode <spot>` (the mode after the arrival in `TruMenu.log`). The 2026-11-11
  "hanging flag" was not one: `arena.go 1a` from a DLC 2 session made tracker 7, "doppelganger flag 1 -> 0" at
  19:35:55, adrenaline ran in Helheim; the quoted 19:36 / 19:38 lines are from an earlier day of the multi-day logs.
- **Spots 1d / 1e / 1f (Q98):** the largest open flat floors of the unit navmeshes with a resident AI enemy kind and a
  checkpoint on the floor (`work\a_arena_1211\q98_flat_areas.py`, "r" = the largest free circle):
  **1d `l5_valgrind` CP 7329** (r 2950, 14350 x 17550, z -26105, `viking_thrall`), **1e `l2_puzzleroom` CP 2074** (Kali
  hall, r 3050, z -15275, `naga_green` / `naga_red`; the puzzle pillars are still there), **1f `l4_traprooms` CP 5722**
  (r 2851, 7776 x 8819, z -2785, `giant_albino_tarantula` / `small_albino_spider`). For comparison 1a r 803 (a loop),
  1b r 767, 1c r 733. Page Tests, group "Arena 1 - Kampf (Q76)": the three rows and "Modus prüfen".
- **Checks:** `trumenu_ini_check` new `check_02232` (LP / EnemyHP / one-hit-kill note read only, kind list, `arena.mode`
  item and its reads, `arena.go` mode step and `level.load` choice, the 6 spots with their modes, rows, help lines, no
  INI key; `check_02226` accepts the later spots) - exit 0; negative tests on copies 4 of 4 caught (no SpHealthNote,
  always `unit.go`, a wrong checkpoint, a write in SpBornLp). Byte checks of the quoted code sites
  (`work\a_arena_1211\precheck_02232_evidence.txt`): 8 / 8 on `data\pc\tru.exe` and the installed `tru.exe`.

### TO TEST 0.22.32

Main-game session (no DLC 2 before it in the same run); `[Cheats] Enabled=1`, `[Cheat] Experimental=1`; one-hit kill off.

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | mode | page Tests, "Arena 1": "Modus prüfen" | `player lara_... , doppelganger byte 0, TruDlc2Player flag 0 -> main-game mode` |
| 2 | spot 1d | "1d: Valgrind (l5, CP 7329)" (right twice) | `l5_valgrind` loads, Lara at CP 7329 (flight on); last log line `arena.mode 1d ... fits the main-game spot` |
| 3 | spawn names | command line `ai.spawn` (no name), then `ai.spawn thrall` | the answers list the loaded kinds (`viking_thrall`), `thrall` = "no object is named 'thrall'" + the matching kinds |
| 4 | spawn LP | `ai.spawn viking_thrall 1` | `... at Lara: 0x... LP 350; EnemyHP step n`; he attacks; a few hits do not kill him |
| 5 | one-hit kill | cheat "Ein Treffer" on, spawn again, off | the answer carries `WARNING one-hit kill is ON`; one hit = RegenerateDeath |
| 6 | spots 1e / 1f | "1e: Kali-Halle", spawn `naga_green`; "1f: Fallenräume", spawn `giant_albino_tarantula` | Lara on the hall floor; the kinds spawn and fight; note pillars / traps in the way |
| 7 | DLC 2 flag | after a DLC 2 start: "1a: Helheim-Halle" | log `arena.go 1a ... level.load l7_helheim03 ... doppelganger flag set ...`, after the arrival `arena.mode 1a ... byte 0 ... fits` |
| 8 | DLC 2 spot | from the main game: "1c: hall02 DLC 2" | answer / log `WARNING ... DLC 2 spot without the doppelganger` |

## 0.22.31 - level navigation (Q105) and room puzzles (Q106) (2026-11-12)

Built into `work\asi\menu0254`, not installed, no live test (group B; finding in the workspace
`docs\Befund-Gruppe-B-1211.md`, data / proofs in `work\b_nav_1211\`).

- **Q105 - units without data are grey and refused.** The 15 names of the unit lists that no PC archive holds
  (`work\q97_q105_1111\q105_units.tsv`, column `loadable_pc = NO`): the six DLC slots of 0.21.10 plus `kUnitsNoArchive` =
  `l1_rutlands_ship_m1`, `l2_mapconnector`, `l2_puzzleconnector` (in the level list) and `cinefx`, `container_dvd`,
  `container_all_weapons`, `dlc_costumes1`, `dlc_costumes2`, `dlc_costume1` (only a typed name could hit them). Each is
  file-tested against `<tru.exe folder>\mods\<unit>.drm` (ModLoader would load such a file). Without it: grey on page
  Kapitel ("kein PC-Archiv") and in the long menu's level list, command-line value `in no PC archive (Q105)`, and
  `level.load`, `level.start`, **`unit.go`** (new) and `cp.jump` refuse it: `refused: l1_rutlands_ship_m1 is in no PC
  archive (bigfile / patch) and not in mods (Q105) - live 2026-11-11 a load of l1_rutlands_ship_m1 hung in the loading
  screen`. Start-up line `0.22.31 units: 9 names in no PC archive (Q105 TSV), 9 of them without a mods\<unit>.drm ...`.
  A built-in table (from the TSV), not the game's FileExists 0x5bf7b0: that call runs the file system on the calling
  thread, the page is drawn on the render thread.
- **Q105 - base game in play order with chapters and checkpoints (page Kapitel).** The groups "Abschnitte 1 Mittelmeer"
  .. "7 Arktisches Meer" now list their units in play order with headings: the chapter starts (generalbank script 72
  `SetChapterUIData(level, chapter)` - 20 callers, owner intro + the constant arguments, e.g. `l1_seatop` intro 997 = 1.1
  "Der Weg nach Avalon", `l4_ballcourt` = 4.2 + 4.3, `l7_thin_ice` = 7.1 Helheim; 1.2 Niflheim's caller is a class script
  without a unit, so its heading says "Start unklar"), the Croft Manor prologue, and the one loop whose direction the
  data do not give (`l1_kraken_room` -> Baldr's halls). The order comes from the stream portals of the 81 base unit DRMs
  (`tools/stream_unit_graph.py`); `work\b_nav_1211\q105_order_table.py` proves every row (each unit has a portal to an
  earlier unit of its level, except a level's first unit and a unit that starts a chapter with its own title card) and
  that no unit is lost. Each unit shows `[+] n CP`: left opens its checkpoint rows (object `checkpoint`, 303 intros, in
  the order of their +0x52 index), right twice on a checkpoint row runs **`cp.jump <unit> <cp> force`** = `save.backup
  kapitel; unit.go; wait.unit; cheat.flight 1; player.goto <cp> force`. The group head says "Debug, ohne Story"; the
  unit / checkpoint help lines say "Debug-Laden ohne Story-Stand". `cp.jump` takes the optional third word `force`; the
  0.21.9 two-word form (DLC rows, page Tests) is unchanged.
- **Q106 - joint values in `uber.dump`.** After each instance line, one line per joint-range transition (condition 14
  enter / 15 leave, any node) of its graph: `uber.dump   joint <object> <intro>: node 3 prism_locked_high (current) -> 9
  SOLVED on enter [-64.00, -57.00) watch kind 0 | joint 0 hinge value 30.12 limits [0.5236, 0.5236] limit on motor off`.
  The value is the engine's own getter (hinge 0x4e1ef0 -> 0x4da930 radians x 57.29577951 = degrees, rail 0x4e1ea0 ->
  0x4da460 = units; the watcher 0x4937a0 compares exactly these, `min <= v < max`), limits are J+0xd8 / +0xdc (radians
  for a hinge). The joint index is the position in the multibody object's list (`[b+0x7c]`, magic 0xFEA51B1E, list
  +0x74), found by the transition's joint record pointer as the engine does.
- **Q106 - `joint.set <intro> <joint index> <value>` | `joint.set stop`** (cheat, game thread, in `kCmdDanger`): drives a
  hinge (degrees) or rail (units) joint with the engine's own action-12 setters - SetLimits 0x4d9fc0 with lo = hi =
  target, limit on 0x4d9f50, motor off 0x4da0c0, wake both bodies 0x4d8fd0 - once per game frame. It ends when the uber
  starts a transition / changes the node (`joint.set ...: node 3 prism_locked_high -> 9 SOLVED after 0.8 s ... - solved
  step`; nothing is put back, the new node's actions own the joint), after 6 s, or when the value stood 1.5 s in the
  target without a node change (then the saved limits and the limit / motor bits come back). A transition running at
  the start is refused (the engine drops events then, 0x4d5a54).
- **Q106 - page Kapitel group "Rätsel in der Nähe (Q106)"** (first group of the page): the uber instances of the loaded
  units, puzzles first (graphs with joint-range transitions, at most 16, nearest first), then other uber objects within
  `[Debug] UberRadius` (at most 8, "(Ereignis)", list only). Per puzzle: object, intro, current node, distance ("+Knoten"
  = more joint targets in other nodes); per joint-range transition of the current node: `G<index> Scharnier 30.1 rein
  [-64.0, -57.0) -> SOLVED` with "drin" when the value is inside. An "enter" row of a hinge / rail: right twice = `joint.set
  <intro> <index> <middle of the range>`; left on any puzzle row stops a running drive. Refreshed every 300 ms while open.
- 27 new byte checks (`kJtChecks`, all read from the PC tru.exe by `work\b_nav_1211\check_0254.py`), no hook, no new INI
  key, no new switches row. `Set-TruMenu.ps1` knows the 0.22.30 build hash. Checks: `trumenu_ini_check` `check_02231`
  (+ `check_02230` reads its kVersion part), `work\b_nav_1211\check_0254.py` (bytes, the 84 table rows against the
  generator output, the 15 names against the TSV, source rules).

### TO TEST 0.22.31

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | start | game start | `TruMenu.log`: `0.22.31 joint puzzles: checks ok (27 rows)`, `0.22.31 units: 9 names in no PC archive (Q105 TSV), 9 of them without a mods\<unit>.drm` |
| 2 | refusal | `menu level.load l1_rutlands_ship_m1`, `menu unit.go l2_puzzleconnector`, `menu level.load cinefx` | each `refused: ... in no PC archive ... (Q105)`, nothing loads |
| 3 | page Kapitel, l1 | open "Abschnitte 1 Mittelmeer" | headings "Kapitel 1.1 Der Weg nach Avalon" (above l1_seatop) .. "1.5 Reich der Toten", the loop note, `l1_rutlands_ship_m1` grey "kein PC-Archiv" at the end |
| 4 | base checkpoint | l2 group, left on `l2_puzzleroom [+] 15 CP`, right twice on "CP 2826" | backup, load (or portal), Lara at CP 2826 with flight on; log `cp.jump l2_puzzleroom 2826: ... player.goto 2826 force` |
| 5 | uber.dump | in `l2_puzzleroom` near the mirror pillars: `menu uber.dump` | per mirror `uber.dump   joint sa_uo_mirror_left 2072: node ...` lines with `joint 0 hinge value ...` / `joint 1 rail value ...` (note the indices / values) |
| 6 | Rätsel group | page Kapitel, "Rätsel in der Nähe" right | the two mirrors (yellow) with node and `G..` rows, "drin" where the value is inside; gates / scales below |
| 7 | solve, one step | on a mirror's "rein [...]" row right twice | the mirror turns / slides; `joint.set ...: node A -> B ... - solved step`, the row list shows the next node; if the value reaches the target but the node stays: `stood 1.5 s ... node unchanged` (note which row) |
| 8 | stop | start a drive, left on a puzzle row | `joint.set ... stopped`, the joint keeps its pose, limits back |
| 9 | calendar | `l4_*` calendar (ca_uo_calendar, one-joint cases) | the solve row moves the dial, node "solved" |

## 0.22.30 - log dates, device glyphs, drawn guards for bar and menu (2026-11-12)

Built into `work\asi\menu0253`, not installed, no live test (group D1: Q107, Q95, Q103 rest; finding in the workspace
`docs\Befund-Gruppe-D1-1211.md`).

- **Q107 - date in every log line:** `TruMenu.log` lines start with `YYYY-MM-DD HH:MM:SS.mmm` (was `HH:MM:SS.mmm`), and
  the first line a process writes is the session header `=== <date time> TruMenu 0.22.30 session start (pid n) ===`.
  The stamp and the header come from the shared `src\asi\TruLog.h`; every other plugin log uses it as well (TruShadowPower,
  TruShadowCombat, TruQoL incl. `TruQoL.exit.log` lines, TruRockVein, TruDlc2Player, TruLink, TruTrace, TruShadowHud,
  TruMercLang, TruDoppelganger, TruDataGuard). All plugins read the clock with `GetLocalTime`; the "one TruShadowCombat line
  1 h off" of 2026-11-11 was a line of an earlier day in the multi-day log (no clock difference). The log page / overlay
  (`StampLength`) accept a stamp with or without the date and show the time. The `claude.mark` line keeps its inner
  `HH:MM:SS.mmm`. Readers accept both forms: `Invoke-TruTestRun.ps1` (marks, flow lines), `combat_log_compare.py`,
  `combo_hitlist_trace.py`, `hitch_scan.py`, `trace_sound_life.py`, `hall02_tutorial_episodes.py`,
  `light_frame_report.py`. TSV traces (TruFight.log, TruAim.log, TruShadowPower's TSV) keep their time column.
- **Q95 - button prompts by the last used device** (`[Input] DeviceGlyphs`, default 0; **0.22.38: default 1**): the PC replaces every pad
  character U+1800..U+182E of a UIText by the name of the bound key (0x5a7c20; Q9). With 1, TruMenu notes the last used
  device - pad: a button, a trigger past 30 or a stick past XInput's dead zone in the game's poll (PadHook); keyboard /
  mouse: a key, a mouse button, the wheel or a mouse move away from the client centre (WndProcHook; the game puts the
  cursor back to the centre after each camera move, that move does not count) - and at the first frame patches 23 bytes
  at 0x5a7d75 (`push esi` / `call GlName` / `add esp, 4` / 14 nops) after 12 byte checks. `GlName` gives for a pad the
  symbol of the first XInput binding (the 14 symbols of texts 5061..5076 and U+1810 / U+1811 for Start / Back - the
  font DTP 46, page 1 = texture 110, holds both), for keyboard / mouse the name of the first other binding; no device
  seen yet, the Enter / Esc / Backspace aliases without a pad, stick directions or `DeviceGlyphs=0` again
  (`settings.reset`) keep the game's own name. Log: `glyphs: last device pad -> keyboard / mouse (key 0x57; switch n)`
  (the first 20 at LogLevel 1), `glyphs: first pad prompt - U+1811 ...`, `0.22.30 device glyphs: 12 checks ok ...`.
- **Q103 rest - only what is on screen acts:** as the ring in 0.22.29, the quick bar acts on its presses (D-pad, LB / RB,
  X / Y) only after DrawQuick drew the open bar in 3 frames, else `quick: buttons 0x.... ignored - not drawn (n
  frames)`; the big menu's widgets (menu window and command bar) are disabled (`ImGuiItemFlags_Disabled`, the look stays)
  and the TO TEST X / Y edges dropped until DrawMenu built the window in 3 frames since the open, a press then logs
  `menu: input ignored - not drawn (n frames)`. Both counters reset at each open.
- One new INI key (259). Check: `trumenu_ini_check` `check_02230` (Log stamp / header, StampLength, the key and its
  readers, 12 checks, the original 23 bytes, patch layout, GlName fallback, bar guard before any press, menu push / pop,
  frame counters, Set-TruMenu 0.22.29 hash); `check_02228` / `check_02229` accept 259 keys and look for their kVersion
  part. Build: 0 warnings in TruMenu.cpp (2 in the third-party `imgui_demo.cpp`).

### TO TEST 0.22.30

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | log date | start the game once | every new line of `TruMenu.log` (and of every other `Tru*.log`) starts with today's date; one `=== ... session start (pid n) ===` line per plugin and start |
| 2 | log page | open the log page / overlay | lines show `HH:MM:SS.mmm` as before (no date in the overlay) |
| 3 | glyphs off | `[Input] DeviceGlyphs=0` (default until 0.22.37), DLC 2 banner "ZIEL FREIGESCHALTET" | as before: `BACK` as a word (pad) |
| 4 | glyphs, pad | `DeviceGlyphs=1`, restart, play with the pad, banner / any hint with Start or Back | the Back / Start symbol instead of the word; `glyphs: first pad prompt` line |
| 5 | glyphs, keyboard | same session: press a key or move the mouse, look at a hint | the key name (e.g. Tab for Back); `glyphs: last device pad -> keyboard / mouse` |
| 6 | glyphs, switch back | touch the pad again | symbols again; no flicker while only the mouse camera turns |
| 7 | bar not drawn | open the quick bar during a load / right after Start + View and press X / right at once | nothing runs before the bar is visible; possibly `quick: buttons ... ignored - not drawn` |
| 8 | menu not drawn | open the big menu and press A / Enter at once | nothing runs in the first frames; `menu: input ignored - not drawn` possible; afterwards the menu works as before |

## 0.22.29 - radial lock: Enabled=0 closes, entries only after a drawn ring (2026-11-11)

Built into `work\asi\menu0252` (sha256 `7c8acbb3...c5444f2ab1`, 1,927,680 bytes), not installed, no live test (Q103;
finding in the workspace `docs\Befund-Radial-Sperre-Q103-1111.md`). Trigger: the evening of 2026-11-11 read the lines
`radial: level 'Tests/Prepare'` / `radial: closed (Prepare started ...)` at 19:35 as today's. They stand in a TruMenu
0.10.1 session of an earlier day (TruMenu.log line 2690 ff.); today's 0.22.28 sessions (from 19:09:55, `radial: enabled
0`) hold no radial line at all, and the code had every ring path behind `g_radEnabled` already (OnPad `hold = 0`,
RadialTick returns, the window procedure branch, `radial.open` refused). 0.22.29 hardens two gaps anyway:

- **Enabled=0 closes an open ring**: when `[Radial] Enabled` turns 0 while a ring is open (`settings.reset` re-reads
  the INI), RadialTick used to return early and the ring state (neutral pad, frozen world) stayed. Now it closes it
  (`radial: closed ([Radial] Enabled=0) ...`) and drops pending release / open / close requests.
- **Entries only after a drawn ring**: DrawRadial counts the frames it really drew since the open (`g_radDrawn`). A
  release (Mode=wheel), a confirm (Mode=menu: A / Enter / left click), A / left click (wheel) or the R3 release (latched)
  runs an entry only when the ring was drawn in at least 3 frames; else nothing runs and `radial: <what> ignored - not
  drawn (n frames)` is logged (a release then closes the ring). The close line names the frames: `radial: closed (...)
  at '...', drawn in n frames`.
- `TruMenuPadBlock` (the state other plugins read, e.g. TruShadowPower's "pad input suppressed" lines) is unchanged: it
  is built from the live open flags; the 0x0200 / 0x0100 (RB / LB) suppressions of 21:32:46 .. 21:33:23 and 21:45:34
  all fall inside an open quick bar (`quick: opened` 21:32:29 .. `closed` 21:33:31, `opened` 21:45:33) - the bar's
  page buttons, as documented in 0.21.1.
- No new INI key (258), no hook, no byte check. Check: `trumenu_ini_check` `check_02229` (Enabled=0 close + dropped
  requests, 4 guards, 6 entry calls in RadialTick, frame count reset / increment, Set-TruMenu 0.22.28 hash);
  `check_02228` looks for its kVersion part. Build: 0 warnings in TruMenu.cpp (2 in the third-party `imgui_demo.cpp`).

### TO TEST 0.22.29

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | radial off | `[Radial] Enabled=0`; hold Start + View (and L3 + R3) 2 s, release | the quick bar / menu toggles as usual; `TruMenu.log` has **no** `radial: opened` / `radial: level` line |
| 2 | RB, bar closed | bar closed, tap RB a few times | `TruShadowPower.log` writes **no** `pad input suppressed: buttons 0x0200` line |
| 3 | RB, bar open | bar open, RB page change | a suppression line may come (the bar owns RB) - as before |
| 4 | ring on (optional) | `[Radial] Enabled=1`, open the ring, confirm an entry | runs as before; the close line ends `drawn in n frames` with n > 0 |

## 0.22.28 - test packages on page Tests (2026-11-11)

Built into `work\asi\menu0251` (sha256 `e284247a...1bf554fd`, 1,926,656 bytes), not installed, no live test (Q90;
finding in the workspace `docs\Befund-Testseiten-Q90-1111.md`). Owner wish for tonight's tests: the packages of the
workspace `docs\Testpakete-1111.md` as groups on the bar page **Tests**, so each package is one place in the game.

- **Group "Testpakete 11.11. (Q90)"** at the top of page Tests (open), one **sub-group per package** A, 1 .. 9 (package 0
  is the install, no group), each closed at the start (`kQbStartClosed` `tp_a`, `tp_1` .. `tp_9`; opening one is kept in
  `[Quick] Closed` as every group since 0.21.1 / 0.22.16). The groups were collapsible already (0.21.1 / 0.22.18: right
  = open, left = close, X = toggle; the long menu shows them as collapsing headers) - nothing new was needed for that.
- Each package: a **hint line** (where / before, grey, passed over by up / down), **jump / load rows** of existing items
  (`level.start dlc2` / `dlc1` (main menu), `level.load l1_seatop` / `l3_caverns_start` with backup, `arena.go 1a`), the
  **switches** the package toggles as the page Fixes rows themselves (same value, colour, count column live /
  Neustart, help line, write path `sw.set`): TruShadowPower `[Camera] ShakeTuTimeStep`, `[Player] TuTimeStep`, `[Camera]
  DoppelgangerSettings`, `[Camera] CameraTuTimeStep`; TruQoL `[FrameLimit] Enabled` / `MaxFps`; TruRockVein `[JumpTarget]
  Translate`, `[LedgeProbe] Translate` / `BestEdge`; TruMenu `[Log] Save`; existing bool items `log.script` /
  `log.scriptfile` (`[Log] Script` / `ScriptToFile`), `gfx.water`, `fight.trace`, `menu.attracttimer`, `cheat.god`,
  `adren.keep`; **probe rows** `save.inv`, `save.find 5240` / `5695`, `save.pending`, `save.waiting`, `thrall.scriptval`,
  `adren.meter`, `adren.fill`, `phys.status`, `ai.remove spawned`, `save.backup paket5|6|7`, `claude.mark gfx`; and the
  **TO TEST checks** of the package.
- **Check rows** (`kQbCheck`, id `test.mark`, argument = the check id `tp<package>.<name>`, e.g. `tp1.climbcam`,
  `tp7.pole`; 46 checks): state `offen` / `OK` / `Fehler` / `übersprungen`, the id in the count column. Bar: **right =
  OK, left = Fehler, X = übersprungen**; the same press again on a row in that state = `offen` (undo). Long menu: one
  button per state. At its first mark the check joins the TO TEST list (`test.add <id> Q90 <English label>`), so
  `TruMenu.tests.txt`, `test.list` and the ring's TO TEST hold it too; the bar's own TO TEST list on page Tests leaves
  the `tp*` rows out (they stand in their package). Log lines per mark:
  `tests: test.mark tp1.climbcam ok` (TestMark) and `quick: Tests / TP tp1.climbcam (Climb camera turns after ~1/4 s
  (T5)) -> ok`.
- **Test-package content is tagged**: every row carries the flag `kQfTp` and stands in the block `// ---- TP Q90 begin`
  .. `// ---- TP Q90 end` of `kQbTests`; owner 2026-11-11: after the tests each row becomes a real row of its page or is
  deleted. The three row kinds `kQbCheck` / `kQbSwitch` / `kQbNote` are only used there so far; no favourites, not in
  "Zuletzt".
- No new INI key (258), no hook, no byte check. Checks: `trumenu_ini_check` `check_02228` (block parsed completely and
  flagged, kQfTp nowhere else, 10 package groups closed at the start with a hint and a check each, check ids unique and
  in their package, switch rows only keys of `TruMenu.switches.txt`, the kinds handled in view / action / X / help /
  long menu, no favourites, the bar's TO TEST list skips `tp*`, test.add only when not listed, Set-TruMenu 0.22.27 hash);
  `qb_rows` reads rows with a line break after any comma (it skipped such rows silently - with the wider pattern 3 older
  rows are checked too, all pass); `check_018` allows id `-` on note rows; `check_02227` looks for its kVersion part.
  Negative test on copies: 10 of 10 mutations caught (`work\q90_testpages_1111\make_neg.py`). `trumenu_quick_check` all
  ok, `trumenu_readability_check` all pass. Build: 0 warnings in TruMenu.cpp (2 in the third-party `imgui_demo.cpp`).

### TO TEST 0.22.28

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | groups | bar page Tests | first row `[-] Testpakete 11.11. (Q90)`, below it the hint and ten closed rows `[+] Paket A ...` .. `[+] Paket 9 ...` (`n Zeilen - rechts = auf`) |
| 2 | open / close | right on `Paket 1`, left again; X on it | opens / closes; after a restart the state is kept (`[Quick] Closed` `+tp_1`) |
| 3 | switch row | Paket 5 "Bilder je Sekunde" left / right | `< 60 >` steps through 30 .. 144, log `quick: Fixes / Bilder je Sekunde -> sw.set TruQoL:FrameLimit:MaxFps 75`; page Fixes shows the same value |
| 4 | check | Paket 1 "Kletterkamera ..." right; right again; left; X | `OK` (green square) -> `offen` -> `Fehler` -> `übersprungen`; `TruMenu.log` `tests: test.mark tp1.climbcam ok` ...; `TruMenu.tests.txt` holds `tp1.climbcam` |
| 5 | TO TEST list | after 4: bottom of page Tests | the TO TEST list does not repeat `tp1.climbcam`; ring Tests / TO TEST and `test.list` show it |
| 6 | long menu | section "Quick bar pages" / Tests | the package groups as headers; a check row with OK / Fehler / Skip / Offen buttons, a switch row with < / > |
| 7 | hint line | up / down over a package | the grey hint line is passed over |

## 0.22.27 - save probe: save.pending / save.inv / save.waiting / save.find, [Log] Save (2026-11-11)

Built into `work\asi\menu0250` (sha256 `ebd75bd7...388159d`, 1,909,248 bytes), not installed, no live test (Q79; finding in
the workspace `docs\Befund-Speicher-Probe-Q79-1111.md`, follow-up P1 of `docs\Befund-Checkpoint-Zustand-Q72-1111.md`,
ENGINE.md 6.4). Question: after death + checkpoint reload an object (pole, key) or an inventory item is gone for good
(Q63 cases 1 / 3 / 13 / 18) - which of the restore conditions held it back? The probe shows it from memory, **read only**.
The code is its own file `TruSaveProbe.h`, included by `TruMenu.cpp` right before the item table (it uses TruMenu's
helpers; no new file in the build).

- **What it reads** (all static, PC `tru.exe`; byte checks below): the live SaveInfo arena `[0xc59258]` and the
  checkpoint snapshot `[0xc5925c]` (`SAVE_SaveGame` copies live -> snapshot, `SAVE_RestoreGame` back); their blocks
  (head = type | size / 4 << 8, used end at +0x1357f4); block 3 (+4 current unit, +8 object, +0xc birth unit, +0x10 link
  parent, +0x14 intro id), block 4 (+4 birth unit, +0x10 link parent, +0x14 intro id); the dead bits (+0x1357f8); the
  restore buffer 0xc57258 (0x800 block pointers, count `[0xc59260]`); the game blocks `[0xc59264]` (live) /
  `[0xc59268]` (snapshot) with the inventory area +0x34c; the waiting table 0xc592a8 (64 x 0x14); the instance lookup
  of `INSTANCE_Find` 0x5b3950 (index table 0xd99000 / ids 0xda1000 / base `[0xd98f60]`, bit 0x20 of +0x14 = being
  removed), the object tracker 0xdb7400 (status 2 = loaded), the stream unit table 0xdbab40 and the unit's intro lists
  (`[[unit+8]+0x74]`, as 0x5b3860). No game function is called, nothing is written.
- **Restore reason** (the pass 0x555640 with 0x5bb160 / 0x5bb640, written as words): `waits for its unit X to load` /
  `unit X (not loaded) - the next pass takes it out of the buffer` (0x55567a; the unit's next load buffers it again,
  0x5556d0); `instance exists - no restore` (0x5bb1c3 / 0x5bb692: the pass returns 0 and **keeps** the slot);
  `waits: object N name not loaded (tracker status s / no tracker entry)` (0x5bb1df / 0x5bb6af); `no intro record`
  (block 4); `waits: link parent N missing (dead bit d)` (0x5bb1f1 / 0x5bb6c1); `ready - restores at the next pass`.
- **Unit names**: the probe remembers every loaded unit's name once a second (128 per session), so a block bound to an
  unloaded unit says `l4_pool (not loaded)`; a unit never loaded in this session shows as `#<id> (not loaded, name not
  seen this session)`.
- **`[Log] Save`** (default 0, live - read about once a second; bar page Fixes, group `Diagnose (TruMenu)`): 1 points the
  rel32 of the two memcpy calls 0x557127 (`SAVE_SaveGame`) / 0x5571a3 (`SAVE_RestoreGame`) at TruMenu - each calls the
  game's memcpy 0x8148a0 with the same arguments, then writes two lines (below); 0 puts the game's call back. Only the
  call targets change (M21PatchGroup: only while the dword is the game's). The prologues 0x5570f0 / 0x557130 are
  TruTrace's hook places: SvCheck accepts the game's bytes or a `jmp` there.

### Items (TruLink `menu <id> [arg]`, command bar)

| Item | Kind | What |
|---|---|---|
| `save.pending [all]` | action | the restore buffer slot by slot (block decoded + restore reason), then the live blocks 3 / 4 **without an instance** that **moved unit** (block 3, +4 != +0xc, marked `MOVED`) or hang on a **link parent**; `all` = every block 3 / 4 without an instance (long: the full text in `TruMenu.log`) |
| `save.inv` | action | the inventory area of the live game block (+0x44, +4 / +8 / +0xc, 15 + 8 intro ids, 6 counts +0xa4, 6 floats +0xbc, +0xd4, player unit +0x1a8, unit name, checkpoint id), each id with its instance or `NO INSTANCE` + its block 3 / 4 and unit + waiting slot + dead bit; the snapshot's area (or `equal to live`); then the WeaponManager slots **now** (`[[0xfadb58]+0x500]`: 15 right-hand slots, 8 gear) as intro ids |
| `save.waiting` | action | the waiting table 0xc592a8: owner (intro id, name, `(Lara)`), id with its state, callback (`inventory 0x715e90`), flag; slots whose owner handle no longer resolves count as free (as 0x5550a0) |
| `save.find <id>` | action | one intro / instance id (decimal or `0x` hex): instance list (address, name, position, units +0xe0 / +0xe4, link parent +0x228, iflags), `INSTANCE_Find`, every block of the id in the live arena (with the restore reason) and in the snapshot, child blocks (link parent = id), the dead bit in both, buffer slots, waiting slots, inventory places (live / snapshot game block, WeaponManager now) |

All four run on the TruLink thread (no `[Cheat] Experimental` needed); each answer also goes into `TruMenu.log`
(`save.<item> (k/n): ...`, cut into pieces of 1,800 characters). The value of each item is a status line: checks,
`[Log] Save`, the patch state, the save / restore counts seen. Intro ids of objects made at run time (weapons, gear:
>= 0x40000000 = 1073741824) are shown decimal; `tools/trusave_diff.py inv` prints both forms.

### `TruMenu.log` lines (`[Log] Save=1`)

```
save: #1 SAVE_RestoreGame(<arg>) from 0x005de53c = death reload 0x5de480 (0x5de537): live before used 0x.., N blocks (1:a 2:b 3:c 4:d 5:e 6:1), m moved block 3, d dead bits; after the copy ... (unit '<name>' checkpoint <id>); rolled back: blocks +x, block 3 +y, block 4 +z, dead bits +w; check word 0xdeadbeef; buffered k (cleared next), waiting w (Lara l)
save: #1 inventory after the copy (handed back by 0x715ef0 at the player's restore): [0] <id> <name> block 3 <unit>; ...; g[2] ...; counts a b c d e f
save: #2 SAVE_SaveGame(0) from 0x005de6fa = player spawn 0x5d40c0 (jmp 0x5d4330) after the death reload 0x5de480 (0x5de6f5): snapshot unit '<name>' checkpoint <id>; used ...; Lara's unit <unit>; buffered k, waiting w (Lara l)
save: #2 inventory in the snapshot (written by the player query 0x17 just now): ...
```

The caller is named for the return addresses read from the code (`0x6a1e17` = call 0x6a1e12 in 0x6a1a70, `0x5dfbbc` =
`dev.reload_current_unit`, `0x5de6fa` / `0x5de179` = the player spawn's tail jump after the death reload / from
0x5de040, `0x5de53c` = death reload, `0x78b00f` / `0x78b0fa` / `0x78b21c` = the save file load 0x78ab60), else with its
module. The save line after a death reload (the spawn's `SAVE_SaveGame(0)`) is the one that shows the waiting table
filled by the inventory restore - that is the moment an item that never comes back is seen (`waiting w (Lara l)`).

### Checks

- Byte checks `kSvChecks` (32 rows: arenas / copy size, block head, walker, game block pointers, buffer, the restore
  conditions of blocks 3 / 4, intro lists, `INSTANCE_Find`, tracker, unit lookup, dead bits, waiting table, handle,
  inventory save / restore, query 0x17) and `kSvHookChecks` (5 rows: the code between each function's entry and its
  copy call - no other push, so the caller / argument are read at `frame[4]` / `[5]` and `frame[17]` / `[18]` - and the
  two calls), plus the two prologues: `work\asi\menu0250\precheck_02227.txt` = the 58 rows of 0.22.26 + these 39, 97
  checks 0 mismatches against `data/pc/tru.exe` and the installed `tru.exe`; `trumenu_precheck_match --cpp
  TruSaveProbe.h` section `0.22.27 save probe` 39 = 39. Without the reads: every item answers `disabled: pre-check
  failed (...)`; without the hook rows: `[Log] Save=1` writes one `no lines - <reason>` line.
- `trumenu_ini_check` `check_02227` (items on the TruLink thread, include once before the item table, rows = the
  precheck file, no write helper / VirtualProtect, the game memcpy only in the two copy hooks inside `__try`, the frame
  offsets, `SvTick` order, `SvReady` first in each runner, [Log] Save in kOpts / INI / ReadOptions / `SvReadSwitch` /
  switches row, Set-TruMenu 0.22.26 hash); `plugin_source` reads the plugin's `.h` files too (SW_LIVE `SvReadSwitch`);
  `check_02224` counts only the FallNet row (TruMenu has two rows now); `check_02226` looks for its kVersion part.
  Negative test on copies: 14 of 14 mutations caught (`work\q79_saveprobe_1111\make_neg.py`).
- Harness with the header's own code on real saves (`work\q79_saveprobe_1111\harness.cpp`, MSVC x86: the game addresses
  committed at the same places with a fake game state around the save's arena): 3 saves of the owner (read in place:
  Mittelmeer `l1_seatop` 470 blocks, Autosave `dlc_level2_start` 39, a test save 121) x 28 checks PASS, 0 FAIL - block
  counts, moved blocks and dead bits equal `trusave_diff`; every restore reason, both `INSTANCE_Find` paths, the bit
  0x20, dead bits, stale waiting handles, the two log lines, the switch on / off and the refusal without checks.
- `TruMenu.ini` = the defaults table (258 keys; `settings.reset` now writes 42,760 bytes).

### TO TEST 0.22.27

Before: `save.backup` (or `menu save.backup` over TruLink); `[Log] Save=1` (bar page Fixes, group `Diagnose (TruMenu)`,
or `sw.set TruMenu:Log:Save 1`); god mode off (a death is needed).

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | start-up | start the game, read `TruMenu.log` | `0.22.27: save probe ok (kSvChecks 32); [Log] Save lines ok (prologues game / game) (kSvHookChecks 5), [Log] Save=0 (live)` (with TruTrace's save hooks: `jmp of another plugin`) |
| 2 | switch | `[Log] Save` 1 | `save: [Log] Save 0 -> 1 (TruMenu.ini, live)` and `0.22.27 [Log] Save: save / restore lines on ([Log] Save=1): S1 ..., S2 ... -> TruMenu` within ~1 s |
| 3 | items idle | in any level: `save.inv`, `save.waiting`, `save.pending` | inventory ids with names (weapons / gear), `0 waiting of 64`, `buffered [0xc59260] = 0` (or a few) |
| 4 | T10 pole | Süd-Mexiko `l4_temple`, before the poles 5240 / 5241: checkpoint; `save.find 5240`; pick the pole up, put it down **in a neighbour unit** (or on a moving object); `save.find 5240`; die (fall) before the next checkpoint; after the reload `save.find 5240`, `save.pending` | before: `instance ... unit +0xe0 <unit>`; after the drop the live block 3 says `MOVED` / link parent; after the reload: the restore line (`rolled back ...`), the spawn's save line; if the pole is missing, `save.find` names its block and the reason (`waits for its unit ...` / `waits: link parent ...` / `instance exists`) - **copy the lines** |
| 5 | T10 key | `l4_ragnarok_room`, key 5695 not taken: take it, walk into `l4_staircase_mictlan` or `l4_pool`, reach a checkpoint there, walk back and die; reload; `save.inv`, `save.waiting`, `save.find 5695`, `save.pending` | `save:` lines with `5695` in the inventory list and its block unit; after the reload: is 5695 in a 15 / 8 slot, `NO INSTANCE`, a waiting slot of Lara? Screenshot of the inventory ring |
| 6 | T14 Manor | Croft Manor, a room with thralls before a checkpoint: checkpoint with thralls alive, kill one, die, reload; `save.inv` before and after, `thrall.scriptval` | counts +0xa4 before / after (ammo back to the checkpoint = intended), the restore line `dead bits -n` (thralls back) |
| 7 | switch off | `[Log] Save` 0 | `... save / restore lines off ([Log] Save=0): S1 ..., S2 ... put back`; no more `save:` lines |
| 8 | file | after a test: `tools/trusave_diff.py inv <Autosave>` | the same inventory ids as `save.inv` (snapshot) |

## 0.22.26 - test arena "Arena 1 - Kampf": arena spots, adrenaline meter, remove the spawned (2026-11-11)

Built into `work\asi\menu0249` (sha256 `99c948b4...d2ddfb1e`, 1,880,064 bytes), not installed, no live test (Q76;
finding in the workspace `docs\Befund-Test-Arena-Q76-1111.md`). Owner wish: a large flat place in an existing level
where enemies can be spawned on demand for combat tests (adrenaline jump-off, finishers, grapple, lock-on). Owner
2026-11-11 13:05: this is **"Arena 1 - Kampf"**; an "Arena 2 - Museum" (unused objects) follows as its own task - the
names leave room for it: one arena list `kArenas` with spot keys `<arena number><letter>` (`1a`..), `arena.go <spot>`,
`arena.list` for every arena, one bar group per arena (`ts_arena1`, later `ts_arena2`).

- **Page Tests, group "Arena 1 - Kampf (Q76)"** (`ts_arena1`): three floors where AI enemy kinds are resident (the
  unit's `objlist.dat` entries), reached with **`arena.go 1a|1b|1c`** (right twice) = one shortcut like `cp.jump`:
  `save.backup kapitel`, `unit.go <unit>`, `wait.unit <unit>`, `cheat.flight 1`, `player.goto <intro> force` (a
  generator may not be drawn - `player.goto` would refuse it; after `wait.unit` its unit is loaded); the "Fliegen" row
  turns the flight off; `arena.list` names the spots:
  - **1a** `l7_helheim03` intro 8785 (`viking_thrall_generator`, live (5230.9, -452.0, -3215.7)): 8 placed
    `viking_thrall`, 1 `yeti_thrall`, 3 viking + 1 yeti generators, all 14 intros at live z -3215.7 over 11,943 x 3,629
    units - base game, adrenaline works there.
  - **1b** `l7_yggdrasil_hall02` intro 8762 (`viking_thrall_generator`, live (1504.2, 6958.9, -312.7)): 2 vikings, 1 yeti
    at z -312.7 / -295.3 - base game.
  - **1c** `dlc_yggdrasil_hall02` checkpoint 10644 (live (-161.3, 3925.0, -312.7)): `viking_thrall_tutorial_dlc2_`,
    `yeti_thrall_dlc2_`; the DLC 2 doppelganger mode skips the game's adrenaline tick / bar (TU test, TruShadowPower
    `[Adrenaline] Translate`), so no adrenaline here. The hall02 story counter may count spawned thralls' deaths (not
    proven either way) - `save.backup` runs before.
  - then: flight, god mode, **the `ai.spawn` rows** of page Gegner (KI) (kind = the AI enemy objects loaded now, count,
    place), **"Gespawnte entfernen"** = `ai.remove spawned`, the adrenaline rows, enemy panel, fight trace.
- **`ai.remove spawned`**: only the instances `ai.spawn` made (ring of 64: address + allocation stamp `+0x44`, so a
  reused slot is not taken); the other modes unchanged.
- **Adrenaline meter** (ENGINE.md 13.7, Q65): `adren.meter` (info, read only) = CM+0x3c / max `[[0xfad764]+0x2d0]`
  (CM = `[[0xfadb58]+0x504]`), "held full" = CM+0x1fc bit 22, bit 27, the doppelganger byte `[[0xfadb58]+0x1244]`.
  `adren.fill` (cheat, game thread) calls the game's own **meter full 0x6e6630** (thiscall CM, leaf: CM+0x3c = max,
  unless bit 27: bit 22 + HUD bytes 0xfae8af / 0xfae8d8) - the body of the script native 0x777a50 and of the refill's own
  call 0x6f2905. `adren.keep 1|0` (cheat, not kept in the INI) does the same once per game frame (PadHook) while the
  meter is below the maximum and bits 22 / 27 are clear. Both behind `[Cheats] Enabled` + `[Cheat] Experimental`.
- 6 byte checks `kAdmChecks` (checked at the first use, one log line `0.22.26: adrenaline meter ok (6 checks)`): the CM
  read 0x5d4859, 0x6e6630 before and after the 8 bytes TruShadowPower 0.22 `[Reticle] TranslateRefill` patches at
  0x6e6646 (left out on purpose), 0x777a50, the refill 0x6f28c0, the bar 0x6f2930. `precheck_02226.txt` = the 52 rows of
  0.22.25 + these 6: 58 checks, 0 mismatches against `data/pc/tru.exe`. No new INI key.
- Not built (finding section 1): spawning an enemy that is **not** resident. `instance.spawn` can stream an object in
  (request + poll), but the engine marks it loaded (state 2, 0x54e756) **before** it requests the children
  (0x54e84b: chunkdoll, companion, weapons) - an enemy born at once may miss them. A stream-in mode would have to wait
  for the children's entries too; not proven, so the arena uses resident kinds only.
- Checks: `trumenu_ini_check` `check_02226` (kAdmChecks rows, meter-full only in `AdmFillNow` inside `__try`, CheatGate
  on fill / keep, `AdmTick` per frame, items, `ai.remove spawned` through `SpIsOurs`, `kArenas` + the `arena.go` steps,
  the three spot rows of arena 1, `arena.go` in kCmdDanger, no INI key, the 0.22.25 hash in `Set-TruMenu.ps1`); negative tests on
  copies, 4 of 4 caught (no `AdmTick` call, no `SpRemember`, `player.goto` without `force`, fill / keep without
  CheatGate). `trumenu_quick_check` all ok, `trumenu_readability_check` all pass, `trumenu_precheck_match` (section
  0.22.26) 6 equal / 0 only in the source. Build: 0 warnings in TruMenu.cpp (2 in the third-party `imgui_demo.cpp`).

### TO TEST 0.22.26

`[Cheats] Enabled=1` and `[Cheat] Experimental=1` in `TruMenu.ini`. Recipe with the arena (T17 / T18): workspace
`docs\Befund-Test-Arena-Q76-1111.md` section 4.

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | spot 1a | page Tests, group "Arena 1 - Kampf (Q76)": "1a: Helheim-Halle (l7)" (right twice) | backup `..._kapitel`, `l7_helheim03` loads, log `shortcut 'arena 1a (l7_helheim03)' ... player.goto 8785 force`, Lara at the generator (flight on); "Fliegen" off: she stands on the floor (z about -3216) |
| 2 | spawn | "Gegner spawnen" -> kind `viking_thrall` (or `yeti_thrall`), count 2, right twice | log `ai.spawn viking_thrall x2 ... 2 born at Lara`; they attack (enemy panel: CombatStepIdle / MeleeAttack) |
| 3 | remove | "Gespawnte entfernen" (right twice) | `ai.remove spawned: 2 removed`; placed thralls stay |
| 4 | meter | "Adrenalin (live)" while fighting | value rises with hits, max as in the HUD; bit 22 when full |
| 5 | fill | "Adrenalin voll" | `adrenaline x -> max of max (held full until it is used)`; HUD bar full |
| 6 | keep | "Adrenalin voll halten" on, use the adrenaline, off | the bar is full again after each use; off = the game's own |
| 7 | spot 1c | "1c: hall02 DLC 2" then "Adrenalin (live)" | the line names the doppelganger mode (no adrenaline in DLC 2) |

## 0.22.25 - settings.reset writes the whole TruMenu.ini (2026-11-11)

Built into `work\asi\menu0248`, not installed, no live test (night queue Q45, agent finding during Q36).
`settings.reset` (menu Settings "Reset all settings", TruLink `settings.reset`) built the default text in a
`static char text[16384]` (since 0.10) - the text from the `kOpts` table is 42,408 bytes (257 keys, 27 sections), so the
written `TruMenu.ini` held only the first 16,383 bytes: 15 sections, 84 keys, the rest missing (missing keys then took
the built-in defaults, so the game ran on, but the file was cut - measured with the 0.22.24 code in a harness,
`work\menu0248_1111\reset_old.ini`).

- **Fix:** `DefaultIniText(nullptr, 0)` measures the text (`IniPut` counts every piece with `_vscprintf`), the reset
  allocates exactly that size and builds it; the text is built **before** the backup and the write (a failure changes
  nothing), a cut text / short write / failed close is refused with the byte counts; the answer names the size:
  `TruMenu.ini rewritten from the defaults (42408 bytes, 257 keys), backup ...`. Comment lines are split in place (no
  512-byte copy any more). Harness with TruMenu's own code (`work\menu0248_1111\make_harness.py`, MSVC x86): measured
  42,408, built 42,408, the file equals the shipped `TruMenu.ini` (LF) byte for byte; into a 16,384 buffer it now stops
  at a whole line (16,360) and reports `cut`.
- **Other texts built from TruMenu's tables** (searched in `TruMenu.cpp`; worst cases from the tables,
  `trumenu_ini_check` `table_texts`):
  - `TruMenu.log` line buffer 512 -> **2048**: `light.cut` lines are built in 1400 bytes, the patch lines of the 0.15
    render mode / `M21PatchGroup` in 480 / 600 - a `Log` line held at most 498 characters after the time stamp, the
    rest was dropped.
  - `[Quick] Closed` (`g_qbClosed`) 384 -> **1024**: every bar group toggled needs 470 (50 group keys, 17 start
    closed); `QbGroupSet` now adds whole keys only and refuses a list that does not fit (log line, bar answer
    `[Quick] Closed voll` / `full`) - before, `LabelAdd` could write half a key into the INI.
  - `[Debug] CheckpointHide` (`CpPersist`, 512 = the read size): whole ids only; ids that do not fit are named in one
    log line (hidden for the session only) - before, half an id could be written (a wrong id at the next start).
  - `settings.show` (`ValSettings`, 16 KB answer): whole keys; when full it ends with `... (+N more keys ...)` instead
    of stopping in the middle of a key. All defaults need 8,330 characters; every key changed to a 40-character value
    would need ~19,400.
  - Fit, unchanged: `[Menu] OpenPages` 207 of 400 (28 pages), `[Cheats] State` 69 of 256 (5 ids), `[Debug] NavDraw`
    120 of 200 / 256 (7 switches), `[Quick] Recent` 1,791 of 1,792 at the field limits, favourites (refused whole since
    0.21.8), `list` (TruLink) 39,102 of 49,152 without values, `sw.list` lines (one log line per switch, < 512).
- Checks: `trumenu_ini_check` `check_02225` - no fixed char array in `RunSettingsReset` / `DefaultIniText` that is not
  larger than the generated default text (on the 0.22.24 source: `RunSettingsReset holds char text[16384] - the default
  text is 42408 bytes`), the measured build, the order build / backup / write, `IniPut` / `TextAdd`, the table texts
  above against their buffers; negative test on copies: 14 of 14 caught (the 0.22.24 source + 13 mutations).
  `precheck_02225.txt` = the 52 rows of 0.22.24 (no new byte checks): 52 checks 0 mismatches against `data/pc/tru.exe`
  and the installed `tru.exe`. `trumenu_quick_check`, qb layout (unchanged), readability, umlauts, flat PS pass.
  `Set-TruMenu.ps1` knows the 0.22.24 hash.

### TO TEST 0.22.25

**Back up the installed `TruMenu.ini` first** (copy it next to the game, e.g. `TruMenu.ini.vor-0.22.25`) - the reset
rewrites it with the defaults (it makes its own `TruMenu.ini.bak_<time>` too).

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | reset | menu Settings: "Reset all settings" (A twice) or `menu settings.reset` | answer / log `settings: TruMenu.ini rewritten from the defaults (42408 bytes, 257 keys), backup ...TruMenu.ini.bak_<time>`; the new `TruMenu.ini` is 42,408 bytes with LF (Explorer: ~41 KB), last section `[Rescue]` with `FallNet=0` at its end - equal to `src\asi\TruMenu\TruMenu.ini` apart from the line ends |
| 2 | after the reset | `menu settings.show` | every key `(default)`, no `(missing: default)` |
| 3 | restore | close the game, copy the backup from before the test back over `TruMenu.ini` | your settings as before |
| 4 | bar groups | quick bar: close and open a few groups | `[Quick] Closed` in `TruMenu.ini` holds whole keys, log `quick: ... group ... closed ([Quick] Closed=...)` |

## 0.22.24 - fall watch + fall net (2026-11-11)

Built into `work\asi\menu0247`, not installed, no live test (night queue Q36). Finding Q19 (workspace
`docs\Befund-Sturz-durch-Welt-1111.md`): after a finisher Y on a thrall lying at the edge of hall02 (live 2026-11-10
22:12) Lara fell out of the world - chart record 1068 [517] = falling, x / y fixed, z down to -170,000 and more, no
kill plane. The logs had no position between the 10-s labels, no record line outside TruTrace's teleport window,
nothing for states 1008 / 1015 and no safe-ground samples.

- **Reads (2 new byte checks, `kFwChecks`):** Lara's chart machine 1 `[[0xfadb58]+0xf10]` (the `kCtChecks` row of
  0.22.9), current record `[machine+0x510]` and its index in `[[machine+4]+0xc]` (ChangeState 0x787910 / 0x78791b:
  `8b570c 0fbfc1 8b2c82 85ed 8b9e10050000`), the record's state ids u16 count `rec+0xc` / list `rec+0x18` (state enter
  loop 0x7859d0: `8b5e18 33ed 66396e0c ...  0fb733`) - the same reads as `combo.trace` / `fight.trace` / TruTrace /
  TruRockVein. Without all three checks: one log line, no watch line, no net.
- **Fall watch (log lines `fall watch:` at `[Menu] LogLevel` 1, always on):** every record change whose old or new
  record is 742 / 743 / 1068 / 1080 (finisher Y 742 [1004 1015] -> 743 [1008]; jump / fall 1080 [515] -> 1068 [517])
  or that makes state 1008 / 1015 appear / disappear in the record's state ids: `fall watch: record 742 [1004 1015] ->
  743 [1008] (state 1008 on, state 1015 off), Lara x y z, unit <unit>`; entering 1068 adds `; fall begins, Lara <n>
  below the newest safe ground x y z (<s> s old)`, leaving it `; after <s> s in record 1068, z <+-n> since it began`.
  While in 1068 a watchdog line every second (1, 2 .. 30 s, then every 10 s): `fall watch: <s> s in record 1068, Lara
  x y z, z drop <n> since it began (<z0>), <n> below the newest safe ground ...`. Safe-ground ring additions
  (`player.unstuck` sampler): `fall watch: safe ground + x y z yaw <r>, unit <unit>, ring <n> of 16 (<k> added since the
  last line)` at most every 2 s. One rate limit for all of them: 40 lines per 10 s, the next line names the dropped
  count. "Time in 1068" = the wall time of the game frames, at most 100 ms per frame (a pause or load does not count).
- **Fall net `[Rescue] FallNet` (default 0, live - TruMenu reads the key about once a second; bar page Fixes, group
  `Rettung (TruMenu)`):** when Lara is more than 3 s in record 1068 **and** more than 3000 units below the newest
  safe-ground sample of her unit taken before 1068 began, she is put back on that sample with its yaw through
  `UnstuckPlace` - the one teleport of `player.unstuck` (position, then yaw), which `player.unstuck` now uses too.
  Lines: `fall net: rescue 1 of 3 after 3.0 s in record 1068: Lara x y z (<n> below) -> safe ground x y z yaw <r>
  (sample <s> s old, unit <unit>); velocity / chart state not reset` and 1 s later `fall net: 1 s after rescue 1:
  record <rec>, Lara x y z (z <+-n> from the safe ground)`. Never while the menu or ring is open, flight is on, the
  world pause bit is set, the main state is not 1, a cinematic runs, player control is off, LP <= 0 or `[Cheat]
  Experimental=0` (one `waiting (<reason>)` line per fall; the rescue follows once the reason is gone).
  `FallNet=0`: one `fall net off ([Rescue] FallNet=0): would put Lara ...` line per fall.
- **Open: velocity.** No velocity / "stand" field of the player is proven (see `player.mark`, 0.10.2 / 0.10.4), so the
  net moves the position only; Lara keeps record 1068 and her fall speed (Q19 fit: -5,151 units/s^2, at 3 s about
  15,000 units/s = ~500 units per 30-fps frame). Whether the floor catches her at that speed is the live test's
  question. If she falls again, the next rescue (at least 1 s later, again 3000 units below) takes the next older
  sample; after 3 rescues in one fall the net stops for that fall (`fall net: 3 rescues in this fall, no more ...`).
- Checks: `precheck_02224.txt` = the 49 rows of 0.22.23 + the `kCtChecks` row + the 2 `kFwChecks` rows, 52 checks 0
  mismatches against `data/pc/tru.exe` and the installed `tru.exe`; `trumenu_precheck_match` section `0.22.24 fall
  watch` 2 = 2; `trumenu_ini_check` `check_02224` (negative test on copies: 12 of 12 mutations caught), the switches
  check accepts TruMenu's own row (`SW_ROW_ONLY`, live = `FnReadSwitch`), `check_02223` looks for its kVersion part;
  `trumenu_quick_check` new model `fallnet` (11 cases on the Q19 fall numbers: first rescue at 3.03 s, worst case 3
  rescues 1 s apart with older samples, floor holds = one rescue and a fall-end line, FallNet=0 / menu open / normal jump
  / frame gap / watchdog cadence / rate limit / foreign unit, and a negative model without the 1 s spacing); qb layout,
  readability, umlauts, flat PS pass. `Set-TruMenu.ps1` knows the 0.22.23 hash.

### TO TEST 0.22.24

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | start-up | start the game, read `TruMenu.log` | `0.22.24: fall watch ok (kCtChecks 1 + kFwChecks 2), fall net [Rescue] FallNet=0 (live)` |
| 2 | watch lines | hall02, a normal jump and a fall from a ledge | `fall watch: record ... -> 1080 [515]`, `1080 [515] -> 1068 [517] ...; fall begins`, `1068 [517] -> <landing> ...; after <s> s in record 1068`; while walking `fall watch: safe ground + ...` at most every 2 s |
| 3 | finisher lines | hall02 thrall fight, finisher Y on a lying thrall | `record ... -> 742 [1004 1015] (state 1015 on)`, `742 [...] -> 743 [1008] (state 1008 on, state 1015 off)` with Lara's positions |
| 4 | net on | bar page Fixes, group `Rettung (TruMenu)`: `Fallnetz (Sturz aus der Welt)` on (`sw.set TruMenu:Rescue:FallNet 1`) | log `fall net: [Rescue] FallNet 0 -> 1 (TruMenu.ini, live)` within ~1 s |
| 5 | provoke the fall | TruShadowCombat `Translate1008=0` (as the Q19 session), hall02: knock a thrall to the y ~ 8260 edge, finisher Y | `fall begins` line, watchdog lines, then **within ~3 s** `fall net: rescue 1 of 3 ... -> safe ground ...`, Lara back on the floor; `1 s after rescue 1: record <landing>` and a `... -> <landing> ...; after <s> s in record 1068 ... (fall net used)` line. If she falls through again: rescues 2 / 3 1 s apart, then `no more` - note the lines (velocity question) |
| 6 | net off | `FallNet` 0, provoke again (or any long fall) | `fall net off ([Rescue] FallNet=0): would put Lara ...` once, no teleport |
| 7 | menu during the fall | net on, open the bar while she falls | `fall net: ... waiting (menu open)`, the rescue right after closing the bar |
| 8 | unstuck unchanged | `player.unstuck` as before | the same answer text as 0.22.23 |

## 0.22.23 - switches file limit 512 (2026-11-11)

Built into `work\asi\menu0246`, not installed, no live test (night queue Q39). `TruMenu.switches.txt` (bar page Fixes,
menu section Fixes, the Figur switch groups) had a hard limit of 160 switch lines; after TruShadowCombat 0.6.12 /
TruDlc2Player 0.6 the file held 159, and every new plugin INI key needs a row (`trumenu_ini_check` enforces it).

- **Limit 512 switch lines** (`kSwMax`, was 160; `kSwGroupMax` stays 24). A fixed table, no heap container: the file
  is read in DllMain and under `g_swLock`, rows are copied by value. Measured on the two builds
  (`work\menu0246_1111\pe_vsizes.txt`): `.data` virtual size +336,520 bytes (352 more rows x 956 bytes `SwRow` +
  `SwValue`), raw size unchanged (18,432) - zero-filled memory, the `.asi` grew only by the new code and text (1,536
  bytes). **File format unchanged** (only the header comment names the new limit).
- **No silent cut any more.** Before, lines past the limit went through the 5-line skip log ("too many switch lines"),
  so a long file lost rows nearly unnoticed, and the switch lines below a group line past 24 groups were given to the
  previous group. Now each kind gets one `TruMenu.log` line with the count and the first line number:
  `switches: <path> exceeds the limit of 512 switch lines: N switch line(s) from line L on not shown` and
  `switches: <path> exceeds the limit of 24 groups: N group line(s) from line L on not shown, with their M switch
  line(s)` (those rows belong to no shown group). The start-up line reads `switches: N switches in G groups from <path>
  (S lines skipped, O over the limit of 512 / 24)`; `sw.reload` / the page head say `lines over the limit not shown
  (log)`.
- **Places that use the count**, checked: the loader `SwLoadLocked`, `SwRefresh` / `sw.list` (loop over the rows read),
  `SwFindLocked` (`sw.set`, favourites `sw.set|<switch>`, the TO TEST when column - a linear search, no own limit),
  the long menu section Fixes (`PageSwitches`, every row), the Figur page (fixed key lists looked up by name). The
  quick bar page Fixes holds `kQbViewMax` = 128 rows (group rows + the one open group's rows); a group too large for
  the page used to be cut silently - the head now says `- N Zeilen nicht gezeigt (Seite max. 128, Menü zeigt alle)` /
  `- N rows not shown (page max 128, the menu shows all)`. The shipped file: largest page 43 rows (group
  Schattenkraft open).
- **Switch row** for TruDlc2Player 0.7 `[Mission] DialogDifficulty` (restart, default 0, group DLC 2 Spielerin /
  Kostüm: `Levelstart: Anpassung auf Mittel` / `Level start: tailoring to Medium`) - its commit 94dab2b left it out
  because the list was at 159 of 160; the file now holds 160 rows in 10 groups (352 free).
- Checks: byte prechecks unchanged (`precheck_02223.txt` = the 49 rows of 0.22.22, 49 checks 0 mismatches against
  `data/pc/tru.exe` and the installed `tru.exe`); `trumenu_ini_check` SW_MAX 512 and `check_02223` (limits, tables
  sized by `kSwMax`, the two log lines, rows below a dropped group, the page head note, the page model of the file:
  group rows + the largest group <= 128, the file header, Set-TruMenu 0.22.22 hash; negative test on copies: 8 of 8
  mutations caught), `check_02222` looks for its part inside kVersion; `trumenu_quick_check` `swfold` reads the
  shipped file's groups against 128 (was a fixed 9-group list against 64) and new model `swcap` (8 cases: 160 rows
  all shown; 161 rows - 0.22.22 drops one, 0.22.23 none; 600 rows = 512 shown and one line; the old 5-line cap as
  negative model; 26 groups; page cut and head count). qb layout, readability, umlauts, flat PS pass. `Set-TruMenu.ps1`
  knows the 0.22.22 hash.

### TO TEST 0.22.23

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | start-up | start the game, read `TruMenu.log` | `switches: 162 switches in 11 groups from ...TruMenu.switches.txt (0 lines skipped, 0 over the limit of 512 / 24)` (the file as of 0.22.24: 160 at 0.22.23 + `DialogHoldClear` (Q41) + `FallNet` in the group `Rettung (TruMenu)` (0.22.24); an older installed file shows its own count) |
| 2 | new row | bar page Fixes, group `DLC 2 Spielerin / Kostüm` | row `Levelstart: Anpassung auf Mittel` (Neustart, value of `TruDlc2Player.ini`; `(aus)` while the installed INI is older than 0.7) |
| 3 | page / menu | open each group on page Fixes; menu section Fixes | every group's rows as before, no "nicht gezeigt" in the head |
| 4 | optional: over the limits | back up the installed `TruMenu.switches.txt`, copy `work\menu0246_1111\TruMenu.switches.limittest.txt` over it (570 rows, 25 groups; the extra rows belong to the made-up plugin `TruLimitTest` without INI = `keine INI`, never written), `menu sw.reload` | log: `exceeds the limit of 24 groups: 1 group line(s) from line 613 on not shown, with their 20 switch line(s)`, `exceeds the limit of 512 switch lines: 38 switch line(s) from line 574 on not shown`, `512 switches in 24 groups ... (0 lines skipped, 59 over the limit of 512 / 24)`; page Fixes with group `Limit-Test limittest` open: head `... - 26 Zeilen nicht gezeigt (Seite max. 128, Menü zeigt alle)`; then put the backup back and `menu sw.reload` |

## 0.22.22 - teaser timer line: game clock / wall clock, pause bit marker (2026-11-11)

Built into `work\asi\menu0245`, not installed, no live test. Two wishes from the 0.22.21 live test of 2026-11-10:

1. **Language.** The line showed `Teaser timer held - 19.2 s since start / alarm every 40.0 s - teaser would have
   started 0x` in English. The line already took its language from the bar language `[Quick] Language` / `quick.lang`
   (`const bool de = g_qbLang == 0;`, the same pattern as the cutscene badge, the flight line and every other overlay).
   Evidence that the bar language was English in that session: the installed `TruMenu.ini` holds `[Quick]
   Language=en`, `TruMenu.log` shows `quick.lang en (src=quick): [Quick] Language written` at 20:12:22 (bar row
   Menüsprache, after `quick.lang de` at 20:07:04) and `Language en` in the start-up line of every later start
   (21:54:10, 22:04:32, 22:21:47). So nothing in the code chose English on its own; with `quick.lang de` (bar row
   Spiel-Einstellungen / TruMenu selbst / Menüsprache) the line is German. 0.22.22 keeps that pattern and makes it a
   check: every text of `DrawNt` is a `de ? .. : ..` pair (`trumenu_ini_check` `check_02222`, `trumenu_quick_check`
   model `ntclock`).
2. **Half speed.** The clock ran at half speed because of the stale pause bit
   (`docs\Befund-Skript-Uhr-halbe-Zeit-1111.md`; fixed separately by TruQoL 0.1.4 `[Fixes] FrontEndPauseBit`). The
   line now shows both clocks and a marker:

| Line | German (bar language de) | English (bar language en) |
|---|---|---|
| 1 head, NoAttract holds | `Teaser-Uhr gesperrt` (+ ` (Pause)` / ` (steht)`) | `Teaser timer held` |
| 1 head, NoAttract off | `Teaser-Uhr 12.3 / 40.0 s` (real elapsed / alarm) | `Teaser timer 12.3 / 40.0 s` |
| 2 clocks (new) | `Spieluhr 19.2 s / Wanduhr 38.5 s seit Start` | `game clock 19.2 s / wall clock 38.5 s since start` |
| 3 alarms, NoAttract holds | `Alarm alle 40.0 s - Teaser wäre 0x gestartet` | `alarm every 40.0 s - teaser would have started 0x` |
| 3 alarms, NoAttract off | `Teaser 0x gestartet seit Start` | `teaser started 0x since start` |
| 3 for 1 s after an alarm | `>> jetzt wäre der Teaser gestartet` / `>> Teaser startet jetzt` | `>> the teaser would start now` / `>> teaser starts now` |
| 4 marker (new, orange-red) | `Pause-Bit aktiv (halbe Zeit)` | `Pause bit set (half time)` |
| 4 checks failed | `Pause-Bit: nicht prüfbar (TruMenu.log)` | `Pause bit: not checkable (TruMenu.log)` |

- **Spieluhr / game clock** = the shadow count of 0.22.21: the dt the game handed the clock's update since the clock's
  (re)start (counts on while NoAttract holds the real elapsed at 0).
- **Wanduhr / wall clock** = `GetTickCount` since the same (re)start (`g_ntResetTick`, set by `NtPre` when the game
  (re)starts the clock) - the value the 0.22.21 flash log line already wrote as "wall time since the clock's
  (re)start". With the bit stale in the main menu the game clock grows half as fast as the wall clock (live
  2026-11-10: 40.02 s at 81.3 s wall).
- **Marker** while `[0xe7f188] == 0.5` **and** `[0xe7f0b4] & 0x10000000`: the frame time function 0x5da230 stores the
  fixed 0.5 (`fld [0x8413a8]`) to `[0xe7f188]` in its paused branch; the per-frame update 0x47afd0 hands the clocks
  `[0xe7f188]` × 1/30. Both conditions are needed: at 60 fps without the bit the measured frame time is also 0.5 (real
  time), and the first frame after a pause has the bit with the lock value 1.0. Read on the render thread
  (`ReadFloats` / `ReadDword`, `NtPauseHalf`), nothing written; the two addresses are only read.
- **Byte checks** (new, `kNtChecks`, checked once at the first draw / report, one TruMenu.log line
  `0.22.22 menu.attracttimer pause bit: 4 checks ok`): 0x5da233 `test [0xe7f0b4], 0x10000000`; 0x5da664 `fld
  [0x8413a8]; mov [0xe7f384], 1; fstp [0xe7f188]` (TruQoL hooks only the call 0x5da684 after it); 0x8413a8 = 0.5f;
  0x47b036 `fld [0xe7f188]; fmul qword [0x843cb0]`. A failed check = line 4 "nicht prüfbar", the rest of the line as
  before.
- `menu.attracttimer` without an argument also reports `wall %.1f s since the (re)start`, `frame time`, the flags dword
  and `pause bit set (half time)` / `no pause bit`.
- INI unchanged (no new key); the item help names the new lines.

Checks: `work\asi\menu0245\precheck_02222.txt` = the 45 rows of `precheck_02221.txt` + the 4 rows of `kNtChecks`: 49
checks, 0 mismatches against `data\pc\tru.exe` and read-only against the installed `tru.exe`;
`trumenu_precheck_match` 0.22.20 section 13 = 13, 0.22.21 section 4 = 4. `trumenu_ini_check` `check_02222`
(kVersion, `de` from `g_qbLang`, no `DrawNt` text without a de / en pair, the clock line and the marker texts,
`NtWallSeconds` from `g_ntResetTick`, `NtPauseHalf` rule bit + 0.5 after the checks, the two addresses only defined and
read, `NtPbCheck` once, `ValNt` fields, the 4 rows = `precheck_02222` section 10, Set-TruMenu 0.22.21 hash; negative test
on a copy: 6 of 6 mutations caught), `check_02221` now looks for its part inside kVersion; `trumenu_quick_check` model
`ntclock` (8 cases: texts from the source in both languages; stale bit with the Bink loop at 29.97 Hz = first flash at
game clock 40.02 s / wall 80.1 s, marker on; bit cleared at 30 s = the gap stays 15.0 s, marker off; 60 Hz without the
bit = no marker, game clock = wall clock; bit with 1.0 / 0.5 without the bit = no marker; checks failed = "nicht
prüfbar"). qb layout (unchanged), readability, umlauts, flat PS pass. `Set-TruMenu.ps1` knows the 0.22.21 hash.

### TO TEST 0.22.22

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | language | bar Spiel-Einstellungen / TruMenu selbst / Menüsprache = DE (`quick.lang de`); main menu with "Teaser-Uhr anzeigen" on | all lines German (`Teaser-Uhr ...`, `Spieluhr ... / Wanduhr ...`); `quick.lang en` -> English at once |
| 2 | fresh start | start the game, main menu, touch nothing | line 2 game clock ≈ wall clock; no line 4; teaser (NoAttract off) at 40 s wall |
| 3 | stale pause bit | load a level, pause, "back to the main menu" (TruQoL `[Fixes] FrontEndPauseBit=0`) | line 4 `Pause-Bit aktiv (halbe Zeit)`; game clock ≈ half the wall clock |
| 4 | TruQoL fix | same as 3 with `[Fixes] FrontEndPauseBit=1` | no line 4; game clock ≈ wall clock |
| 5 | report | `menu attracttimer` over TruLink (no argument) | in case 3: `... wall N s since the (re)start ... frame time 0.500, flags 0x........: pause bit set (half time)` (flags with bit 0x10000000) |
| 6 | checks | TruMenu.log after the first draw | `0.22.22 menu.attracttimer pause bit: 4 checks ok` |

## 0.22.21 - teaser timer line in the main menu (2026-11-10)

Built into `work\asi\menu0244`, not installed, no live test. Owner's wish after the 0.22.20 live result (21:25-21:27,
no teaser after 113 s): a switch **"Teaser-Uhr anzeigen" / "Show teaser timer"** that shows the AttractTimer clock in
the main menu, also while `menu.noattract` holds it, and marks the moment the teaser would have started.
`menu.attracttimer 1|0` (no argument = report, never a flip; a bad value = usage), `[Menu] AttractTimerShow` (default 0,
written back at once like the 0.22.18 settings), `[Menu] AttractTimerPosition` (corner `tl` / `tr` / `bl` / `br` as the
sound list's `[Sound] Position`, default `tr`; anything else = `tr`; INI only). Bar row on page Spiel-Einstellungen,
group "Hauptmenü", right after "Hauptmenü-Video aus"; help line "Zeit bis zum Teaser im Hauptmenü - blinkt beim Alarm";
greyed with the same reason as `menu.noattract` (13 checks of 0.22.20 differ / a patch refused).

**What the line shows** (section "0.22.21 menu.attracttimer", drawn in Present only in the front end = main state 6 /
10, the AttractTimer's own gate; never in a level):

| State | Line 1 | Line 2 |
|---|---|---|
| clock not taken yet (TruMenu waits for the timer's next START / RESTART) | `Teaser-Uhr: noch keine Uhr` | `kommt mit dem nächsten Start (Eingabe im Menü)` |
| `menu.noattract` off | `Teaser-Uhr 12.3 / 40.0 s` (real elapsed / alarm; `(steht)` / `(Pause)` when the clock is stopped / paused) | `Teaser 1x gestartet seit Start` |
| `menu.noattract` holds | `Teaser-Uhr gesperrt - 52.3 s seit Start` (shadow count) | `Alarm alle 40.0 s - Teaser wäre 1x gestartet` |
| 1 s after an alarm | the box orange, white text | `>> Teaser startet jetzt` (real) / `>> jetzt wäre der Teaser gestartet` (held) |
| checks failed / patch refused | `Teaser-Uhr: Spielcode weicht ab (TruMenu.log)` | - |

English texts with the bar language English (`Teaser timer 12.3 / 40.0 s`, `Teaser timer held - 52.3 s since start`,
`>> the teaser would start now` ...).

**How it reads the clock** (game thread, read only): the 0.22.20 update slot 0x84584c now points to `NaUpdate` while
the hold **or** the line wants it (`NaTick`); with the line alone `NaUpdate` writes nothing - it only reads the captured
clock around the game's 0x4a3960 (`NtPre` before the hold, `NtPost` after the game's update): state +8, elapsed +0x10,
fired +0x18; alarm / repeat come from the capture at the f11 native. These are the offsets the 0.22.20 rows of
0x4a3993 / 0x4a39b7 already pin, so there are no new byte checks.

- **Shadow count** = the dt the game hands the clock's update while the clock runs (state 2 - the game adds dt only
  then), so it keeps counting while NoAttract sets the real elapsed to 0. It starts anew when the game (re)starts the
  clock outside the update: `NtPre` sees an elapsed that is not what the previous update left, or the clock running at
  0 again after a stop (clock f0 Start: "only when not running: fired 0, elapsed 0, state 2", ENGINE.md "Script
  `clock`"). That is "since the last START / RESTART" whenever that call really restarts the clock (RESTART = f11 + f1
  Stop + f0; in TruMenu.log of 2026-11-10 21:24-21:31 every "STARTING" followed a "STOPPING"); a START on a clock that
  already runs changes nothing in the game, so the shadow does not restart there either - it stays the time the game
  itself would have counted.
- **Flash** (1 s orange box) + one TruMenu.log line at LogLevel 1 per flash - while held: each time the shadow passes
  the alarm (40 s, then 80 s, 120 s ... because repeat = 1; once without repeat); while not held: when the real clock
  fires in this update (fired set, or elapsed -= alarm with repeat) - the teaser then starts as the game's. Log line
  e.g. `menu.attracttimer: the teaser would start now (held) (alarm 1) - shadow 40.01 s, alarm 40.00 s, real elapsed
  0.02, 40.0 s wall time since the clock's (re)start, NoAttract holds`. The wall time is TruMenu's own GetTickCount
  since the shadow restart: that the clock's dt is in seconds is an assumption (alarm 40.0 and the ~40 s idle time
  match), the log line lets the live test confirm it.
- Switching NoAttract while the line is on keeps the slot patched; the hold change gets its own log line
  (`menu.noattract on: update slot 0x84584c already NaUpdate ...` / `menu.noattract off (update slot stays NaUpdate for
  the teaser timer line, read only): N frames held ...`). Both off = slot put back as in 0.22.20.

`menu.attracttimer` without an argument reports e.g. `1 (NoAttract holds - shadow count; clock read, real 0.02 / 40.00
s, shadow 52.31 s, 1 alarm(s) since the start, 1 flash(es), corner tr)`.

Also in this commit (the TruMenu checks failed on HEAD because of TruShadowPower 0.24, commit 4222070):
`TruMenu.switches.txt` got the row for TruShadowPower `[Camera] TuTimeStep` (restart, default 0, since TruShadowPower
0.24; read once in its ReadOptions), and `check_02219` accepts a TruShadowPower version export 0.23 or later.

Checks: `work\asi\menu0244\precheck_02221.txt` = the 45 rows of `precheck_02220.txt` (no new rows): 45 checks, 0
mismatches against `data\pc\tru.exe` and read-only against the installed `tru.exe`; `trumenu_precheck_match` 0.22.20
section 13 = 13, 0.22.21 section 0 = 0. `trumenu_ini_check` `check_02221` (defaults in kOpts / sample INI /
ReadOptions, item / row order / help / greying, RunNt no-flip + usage + IniKeep, the slot for hold or line, NaUpdate
writes only in the hold branch, NtPre / NtPost only read, NtPost after the game's update, front end only, 1 s flash, the
45 precheck rows, Set-TruMenu 0.22.20 hash; negative test on a copy: 5 of 5 mutations caught); `check_02220` follows
the new NaUpdate form; `trumenu_quick_check` model `attracttimer` (15 cases: read only - 400 frames identical to the
game alone, flash frames = the frames the free clock fires with mixed dt, RESTART / START on a running clock / STOP +
START, no repeat, line off, level, RunNt, position default); qb layout, readability, umlauts, flat PS checks pass.
`Set-TruMenu.ps1` knows the 0.22.20 hash.

### TO TEST 0.22.21

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | line, NoAttract off | bar Spiel-Einstellungen / Hauptmenü, "Teaser-Uhr anzeigen" right; main menu, touch nothing | top right `Teaser-Uhr 0.0 / 40.0 s` counting up; at 40 s the box flashes orange 1 s with `>> Teaser startet jetzt`, the teaser starts (the game's); TruMenu.log `menu.attracttimer: the clock fired - the teaser starts (alarm 1) - ... 40.0 s wall time ...` |
| 2 | dt = seconds? | compare the line with a stopwatch / the log line's wall time | shadow / elapsed seconds = wall seconds (else note the factor) |
| 3 | line + NoAttract | also "Hauptmenü-Video aus" right; touch nothing ~2.5 min | `Teaser-Uhr gesperrt - ... s seit Start`; flashes at 40 / 80 / 120 s with `>> jetzt wäre der Teaser gestartet`, no teaser; one log line per flash |
| 4 | input | press a direction in the menu | the count starts from 0 again (RESTART) |
| 5 | level | start / load a level | no line in the level; back in the main menu it is there again |
| 6 | corner / persist | `[Menu] AttractTimerPosition=bl`, restart | line bottom left; `AttractTimerShow=1` kept from the row |
| 7 | toggle NoAttract with the line on | "Hauptmenü-Video aus" right / left | log `menu.noattract on: update slot 0x84584c already NaUpdate ...` / `menu.noattract off (update slot stays NaUpdate ...)`; line switches between real and shadow |
| 8 | line off | row left | line gone; with NoAttract off too: log `menu.noattract off: N frames held` (slot put back) |

## 0.22.20 - main menu attract video off (2026-11-10)

Built into `work\asi\menu0243`, not installed, no live test. Owner's wish: the main menu shall stay on screen (for
screenshots) - no teaser video after the idle time; the menu background (the scene behind the ring) stays exactly as it
is. `menu.noattract 1|0` (no argument = report, never a flip), `[Menu] NoAttract` (default 0 = the game's teaser,
written back at once like the 0.22.18 settings), bar row **"Hauptmenü-Video aus" / "Main menu attract video off"** on
page Spiel-Einstellungen, own group "Hauptmenü" / "Main menu" (before "TruMenu selbst"), help line "Kein Teaser-Video
nach Leerlauf im Hauptmenü".

**Who starts the teaser** (static, `tools/script_dis.py` / `script_func_list.py` / `script_members_list.py` on the
installed `mods\generalbank.drm` and the PC patch generalbank - script 60 is the same in both - and `tools/pe_dis.py` on
`data\pc\tru.exe`; one-off tools and outputs in `work\menu0243_1011`):

- Generalbank **script 60 `AttractTimer`** (print "AttractTimer()::Run()"; the log lines "UI - STARTING / RESTARTING /
  STOPPING Attract Mode Timer" are its functions 4 / 3 / 5, called by the main menu script 7 - "Stopping Main Menu
  attract mode timer...N" is script 7's own print). Member 4 (instance +4) is a native **`clock`** (script 125, package
  `game/script/core/core`; init block `{autostart 0, alarm 40.0, repeat 1}`).
- f1 (vtable 22, the per-frame update) starts the clock while `uigamedata` f37 holds (0x5d56e0: main state 6 or 10 = the
  front end); f4 START = clock f11 + f0, f3 RESTART = clock f11 + f1 + f0.
- When the clock fires, f2 (vtable 1, the clock event) checks clock f10 (`==` its member 4), front-end state != 4 and
  two `stdscreenmgr` tests, then broadcasts **"stopTitleMusic"**, calls `uigamedata` f22 (StopMovie) and **f26** =
  0x7a0d30 -> 0x77bd40 -> 0x5d5700: front-end state 6, screens closed, main state 10 -> the front-end switch plays the
  attract list 0x8abef4 ("intro") through 0x5d5520 / the Bink player 0x4a12b0. f26 has no other caller in the
  generalbank (`work\menu0243_1011\native_callers.py`).
- The clock in the exe: class vtable 0x861e94, binder 0x7ab770 (natives f0 0x795c30 Start, f1 Stop, f4 IsRunning, f7
  elapsed, f9 SetAlarm, f10 0x796fd0 `==`, f11 0x795cc0 = `mov ecx, [esp+4]; jmp 0x4a34f0` re-registers the update
  object). Object 0x20 B, vtable 0x845860: +8 state (2 = running), +0x10 elapsed, +0x14 alarm, +0x18 fired, +0x19
  repeat, +0xc update object (vtable 0x84583c) whose **slot 4 (0x84584c) = 0x4a3960(dt)**: while running elapsed += dt;
  not fired and elapsed >= alarm -> fired (repeat: elapsed -= alarm) and the event goes to the owner script.
- Clock **f11 is called only by script 60** (+0x608 in f3, +0x698 in f4): 54 calls in the 27 DRMs of the installed mods
  tree that carry clock calls, all script 60 (`work\menu0243_1011\clock_f11_callers_mods.txt`); the base levels inside
  the bigfile were not scanned - hence the extra gates below.

**What TruMenu does** (section "0.22.20 menu.noattract", game thread, generalbank.drm untouched):

1. Capture (passive, placed once the 13 checks pass, whether the switch is on or not - so turning it on in the menu needs
   no restart of the timer): the jmp of the f11 native (0x795cc4) goes to `NaF11`. It gets the member address
   (AttractTimer +4); the clock behind it is taken when its vtable is 0x845860 and the main state is 6 / 10 (log line
   `menu.noattract: AttractTimer clock 0x... (member 0x...; state, elapsed, alarm, repeat) taken from clock f11`), then
   the game's 0x4a34f0 runs.
2. Hold (only while the switch is on): slot 4 of the update vtable (0x84584c) points to `NaUpdate`. For the captured
   clock only, and only in main state 6 / 10, elapsed is set to 0 before the game's 0x4a3960 runs - the alarm never
   fires, f2 never runs: no "stopTitleMusic", no StopMovie, no f26, so the title music and the menu background go on as
   before. Every other clock (and the AttractTimer clock outside the front end) is the game's. Off = slot 4 put back
   (log line with the held frames); elapsed then starts from one frame, so no teaser at once - the full idle time first.
3. Turned on before the clock was taken (e.g. TruMenu loaded late): the game's teaser can come once until the timer's
   next START / RESTART (any input in the menu, or the menu coming back after the teaser) - from then on it is held.

`menu.noattract` without an argument reports e.g. `1 (held; clock taken, repeat, 3120 frames held, 4 timer starts
seen)`; the row is greyed with the reason when the code differs (13 checks) or a patch site was not the game's bytes.

**Start-up intro (TODO "faster start"):** not part of TruMenu - TruQoL 0.1.2 already has `[Startup] SkipIntro`
(PlayMovie call 0x77bc7b, only before "press start"; switchable on bar page Fixes, restart). The legal screens are
script-drawn, no movie. The attract "intro" is the same Bink file, but it is played by 0x5d5520 directly and is
covered by `menu.noattract`, not by SkipIntro.

Checks: `work\asi\menu0243\precheck_02220.txt` = the 32 rows of 0.22.18 + the 13 rows of `kNaChecks` (clock class /
binder / f11 native + body, clock vtable + constructor, update object vtable + slot 4, update body, init block, f37
gate): 45 checks, 0 mismatches against `data\pc\tru.exe` and read-only against the installed `tru.exe`;
`trumenu_precheck_match` 13 = 13. `trumenu_ini_check` `check_02220` (default 0 in kOpts / sample INI / ReadOptions,
item / row / group / help / greying, RunNa no-flip + usage + IniKeep, capture and hold order, the 13 rows in the precheck
file, Set-TruMenu 0.22.19 hash; negative test on a copy: 3 of 3 mutations caught); `trumenu_quick_check` model
`noattract` (14 cases: game's teaser when off, 10 000 held frames without an event, other clocks / levels untouched, no
teaser at once after off, capture rules, RunNa). `Set-TruMenu.ps1` knows the 0.22.19 hash.

### TO TEST 0.22.20

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | off (default) | main menu, touch nothing ~1 min | the game's teaser starts as before; TruMenu.log `menu.noattract: AttractTimer clock ... taken from clock f11` (main state 6 / 10) |
| 2 | on | bar Spiel-Einstellungen / Hauptmenü, "Hauptmenü-Video aus" right; back in the main menu, touch nothing 5 min | no teaser; menu background and title music keep running; `menu menu.noattract` = `1 (held; clock taken, ... frames held ...)` |
| 3 | persist | restart the game | `[Menu] NoAttract=1` in TruMenu.ini, menu stays from the first idle on |
| 4 | off again | row left, wait in the menu | log `menu.noattract off: N frames held`; teaser after the normal idle time, not at once |
| 5 | level | start a level with the switch on | nothing changes in the level (other clocks are the game's) |

## 0.22.19 - pages remembered, "Kraft unendlich" in the cheats (2026-11-10)

Built into `work\asi\menu0242`, not installed, no live test. Owner's wishes after the 0.22.18 live result (20:10:
language and music volume kept over restarts). No game code touched - INI files only, so no new byte checks
(`work\asi\menu0242\precheck_02219.txt` = the 32 rows of 0.22.18 run again: 0 mismatches against `data\pc\tru.exe` and
read-only against the installed `tru.exe`).

- **Quick bar: the last page.** The bar opens on the page it showed last, also after a restart: `[Quick] LastPage` holds
  the page's English name (the German name and a page number 1 .. 17 are read too). Written by `QbPageKeep` (every
  Present, two compares per frame): 1 s after the last LB / RB page change while the bar is open, or at once when it is
  closed - never per frame, never an unchanged value (paging away and back before the write writes nothing). Empty =
  page Level data as before; a name that is no page any more (a later version renamed it) opens page 1 (Favourites /
  recent) with the log line `quick: [Quick] LastPage '<name>' is no bar page (any more) - opening page 1 ...`, the next
  close writes a real name. `[Quick] RememberPage=0` = always page Level data, nothing written. Only the page, not the
  row (rows are rebuilt per frame; the row per page is kept for the session as before).
- **Big window: the open pages.** The big window has no tabs - its pages are collapsing headers, several may be open.
  Each page has a short key (`kMpPages`: totest, regress, quick, status, devmenu, timeplayer, instances, costumelive,
  log, videos, music, saves, settings, overlay, access, arachno, coop, ai, fixes, qbpages, camera, cheat, cheats, markup,
  debugview, level, outfits, devchannel; the start line `menu pages: ...` lists them). `[Menu] OpenPages` (default
  `totest,quick` = the old defaults) lists the open ones; the first draw of a page in this ImGui context takes its state
  from the list (`SetNextItemOpen(..., ImGuiCond_Once)`; `io.IniFilename` is null, so once per start), a toggle (click,
  A / Enter: `IsItemToggledOpen`) rewrites the list at once through `IniKeep`. Keys that are no page are dropped with a
  log line; a value of only unknown keys = the built-in pages; an empty value = every page closed. `[Menu]
  RememberPage=0` = the headers' own defaults (TO TEST, Quick access open), nothing written.
- **`power.infinite 1|0`** (bar row **"Kraft unendlich" / "Infinite shadow power"** in Rettung / Cheats, group Cheats,
  next to "Munition unendlich"): writes TruShadowPower 0.23's `[Meter] Infinite` into `TruShadowPower.ini` next to the
  `.asi` files (the same path as the Fixes rows: `TestIniTarget`, the folder of TruMenu's own INI) with
  `WritePrivateProfileString` - only that key line changes; an older INI without the key gets it at the end of `[Meter]`,
  comments and every other line stay. TruShadowPower reads it within ~1 s (`InfiniteReadSwitch`). No argument = report
  (`1 ([Meter] Infinite 1; TruShadowPower.asi loaded 0.23, TruShadowPower.ini found)`), never a flip. Refused, and the
  row greyed with the reason in the help line and a short one in the count column, while TruShadowPower.asi is not
  loaded ("nicht installiert"), its version export is older than 0.23 ("< 0.23") or the INI is missing ("INI fehlt") -
  no INI is ever created. The state is read at most once per second, at once after a write; the Figur / Fixes switch row
  of the same key (`TruMenu.switches.txt`) is refreshed with it. A missing key shows "aus" (TruShadowPower starts with 0).
- Checks: `trumenu_ini_check` `check_02219` (defaults = sample INI, every page header through `MenuPage` with one key
  of `kMpPages`, `QbPageKeep` before `QuickTick`'s early returns, 17 unique page names, `power.infinite` item / row /
  greying / write, TruShadowPower 0.23 export, Set-TruMenu 0.22.18 hash); `trumenu_quick_check` models `lastpage` (13),
  `menupages` (9), `infinite` (13). `Set-TruMenu.ps1` knows the 0.22.18 hash.

### TO TEST 0.22.19

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | bar page | open the bar, RB to "Rescue / cheats", wait 2 s, close; `game.quit`, restart, open the bar | opens on "Rescue / cheats"; TruMenu.ini `[Quick] LastPage=Rescue / cheats` |
| 2 | bar page | RB 3 x quickly, close within 1 s | one write (the last page), log level 2: one `[Quick] LastPage=... written` line |
| 3 | bar page | edit `LastPage=Lara` (no page), restart | bar opens on page 1, log `... is no bar page (any more) - opening page 1` |
| 4 | bar page | `[Quick] RememberPage=0`, restart | always page Level data, `LastPage` untouched |
| 5 | big window | `[Menu] Enabled=1`: open Fixes and Status, close Quick access; restart, open the window | Fixes + Status open, Quick access closed; `[Menu] OpenPages=totest,status,fixes` |
| 6 | infinite | page Rettung / Cheats, "Kraft unendlich" right (TruShadowPower 0.23 installed) | row "an"; `TruShadowPower.ini [Meter] Infinite=1` (the older INI: key added, the rest unchanged); TruShadowPower.log `0.23 switch: [Meter] Infinite 0 -> 1`; DLC 2: the meter stays full |
| 7 | infinite | `menu power.infinite` over TruLink (no argument) | report only, nothing written |
| 8 | infinite | the same row on page Figur (Schattenkraft group) | shows the same state within 1 s |
| 9 | infinite | without TruShadowPower.asi (or an older one) | row grey, count column "nicht installiert" / "< 0.23", help line the reason; right = refused, nothing written |

## 0.22.18 - volume save, groups everywhere, step mode, subtitle alignment, speech language, light demote (2026-11-10)

Built into `work\asi\menu0241`, not installed, no live test. Byte checks: `work\asi\menu0241\precheck_02218.txt` (32
new checks: `kVsChecks` 6, `kSaChecks` 7, `kVlChecks` 9 + 1 ret, `kLdChecks` 10; 0 mismatches against
`data\pc\tru.exe` and read-only against the installed `tru.exe`). Wishes of 2026-11-10 (owner / coordinator).

- **1 Volume save (live 16:44: `game.vol.music 128` live, `options saved`, registry `MusicVolume` stayed 0).** Static
  (`tools/pe_dis.py`): the settings save 0x478010 refreshes the mirrors 0x8900e0 / d8 / dc from the FMOD categories
  (0x47809b..0x4780b4) but its `RegSetValueEx` calls write only Language, SubtitleLanguage, Vibration, CombatMode, the
  four inversions, 0x890100, 0x8900c8, 0x890104 - **never MouseSensitivity, VoVolume, MusicVolume, SfxVolume**. Those are
  written only by 0x4796b0 (0x4796ef / 0x47977a / 0x479791 / 0x4797a8; root values + Graphics from 0x890388). The game's
  own menu: its volume natives 0x5a4af0 / 0x5a4b30 / 0x5a4b70 set the mirror, leaving the pause menu (0x5d473d) calls
  0x4796b0. TruMenu now does the same: a volume / mouse change sets the mirror at once; the delayed save runs 0x478010,
  sets the volume mirrors from the profile fields P+0x338 / +0x33c / +0x340 (what the callbacks and the natives write -
  not the FMOD category, which `media.mutemusic`'s fallback sets to 0), then 0x4796b0, then the next-start values of this
  session again (`GnRewrite`, as `gfx.save`). Log `0.22.18 options: 0x478010 + 0x4796b0 done (#n) - MusicVolume 128 ...`.
  Other options (inversion, sub.lang ...) keep the 0x478010-only save. Model `volsave` (8 cases).
- **2 Groups everywhere, indentation.** Every `-- ...` heading of the bar tables is a collapsible group now (16 headings:
  Kostuem, Barrierefreiheit Sehen / Hoeren / Verstehen / Steuerung / Sonstige, Koop, Rettung Festgesteckt / Spielstaende
  / Objekte / Ausruestung, Tests Teleport / Teststellen / Zwischensequenz / Diagnose / hall02-Zaehler) plus "Zeit" (page
  Zeit / Ablauf) and "Darstellung" (page Debug) for their loose rows - new keys, open at the start, so an existing
  `[Quick] Closed` resolves as before. `kQfSub` = a sub-group: "Ton-Gruppen (TruMenu)" in Ton, "Geraet (Diagnose)" in
  "Grafik ab naechstem Start" (the bug of the shot `pc_leiste_gruppen_164959.png`). A closed group hides everything up
  to the next heading of its level or above; the closed count includes its sub-groups' rows. Drawing: headings at the
  left, rows one step (`[-] ` wide) per level further right, the square column only on rows, a thin guide line per open
  level. Special pages: a `[+]` / `[-]` / `-- ` special row is a heading, the rows after it one step in. Long menu
  (Quick bar pages, Barrierefreiheit): groups are collapsing headers, sub-groups indented. `QuickCheck` no longer counts
  group headings as unknown items (the start line said 29 unknown). `kQbViewMax` 128. Model `groups 0.22.18` (7 cases).
- **3 Frame stepping.** While View (the button all three combos share, `CnPadMod`) stays down, each RB tap is one frame
  (step mode; 0.22.13's wait for a full release never ended with View held - only one step). RB + View held 0.4 s =
  `cine.step 1` every 1000 / `[Settings] StepRate` ms (5 / 10 / 15, `cine.steprate`, bar row in Tests / Zwischensequenz;
  the subtitles run along); letting go stops with no extra frame; LB added stops the repeat, the photo fires, the pause
  stays. Keyboard keys unchanged. Model `cinepad` + 12 cases (the 0.22.13 bug case included).
- **4 Subtitle alignment.** Evidence: the draw 0x583e20 sets the text origin (0, 352) through 0x474ce0 (0x9de6e8 /
  ec), the line draw 0x477180 centres each `\n` segment: x = ([0x9ce6cc] - width (0x4758c0, thiscall) * [0x9ce6bc]) *
  0.5 -> 0x9de6e0; the box 0x4759b0 and the string entry 0x476bc0 add the origin. `sub.halign centre|left|right` +
  `sub.margin 0..30` (percent of the width): `GsSubLine` (the 0.22.16 line call 0x583eb6) moves the origin x for its line
  by (wanted x - centred x) and puts it back - no game code changed. `sub.valign bottom|top|free`: bottom = `sub.pos` 250
  .. 420 (game 352), top = 16, free = `sub.pos` 16 .. 448 - 2 x line step - 8 (two lines always fit). `[Settings]
  SubAlignV / SubAlignH / SubMargin`; rows in the Untertitel group; `sub.reset` resets them too. Only the first `\n`
  segment of a box line sets the shift (box lines are single lines). Model `subalign` (9 cases).
- **5 Speech language (plan S1).** `voice.lang game|en|fr|de|it|es|nl|ja|ru` (row "Sprachausgabe (nur Ton)" in Ton):
  on the game thread, while MultiFS slot +0x18 (0x472be0) says free, slot +0x10 (0x472d80) gets `1 << lang` (game =
  `1 << [0x8906b8]`); read back through +0x14; ModLoader found by its mask setter bytes (its child's +0xc compared). No
  locals reload - in-game lines switch at the next sentence, cutscenes at the next scene, texts stay. NL / JA / RU only
  when `mods\cinstream`, `mods\vo\dlc1` or `mods\vo\dlc2` hold a `*_2048` / `*_032` / `*_512` file (checked once, else
  refused). `[Settings] VoiceLanguage` (written at once, applied at the first game frames). `voice.full <lang>` (rows
  "Sprache komplett (Text + Ton)" DE / EN, right twice): option 0x95 stored without its callback (no live text switch),
  0x478010 writes `Language`, speech now; texts and menus at the next start.
- **6 Music player (plan S2).** `Set-TruMenu.ps1` falls back to the last generated `work\media\menu\TruMenu.media.txt`
  when the build folder has none (warning with its date; the list there is from 2026-11-02 - regenerate with
  `tools/music_list.py --menu-out work\media\menu` for the DLC tracks' sound flags). Rows in Ton: "Musik auf 100 %" -
  red **"Musik-Lautstaerke ist 0 - der Player bleibt stumm"** while option 2 is 0, else the volume in the count column;
  "Musik auch im Level" (`media.music.inlevels`, `[Media] MusicInLevels`, written at once); "Musik: laeuft gerade".
- **7 Goo drip columns.** `TruFight.log` 2026-11-10 13:39: in 2145 zone lines every copy stood at the source (x -195,
  y -6292 / -5725, z 12110) - inst+0x20 of a copy does not move while it falls (animation 1). Not decidable offline, so
  candidate columns at the end: `pc_drip_b0_x/_y/_z/_dz` (bone matrix 0 translation `[[inst+0x90]+0x30]`, the nearest
  copy by it), `pc_drip_b0_lowz` (lowest bone-0 z of all copies), `pc_drip_near_oldz` (inst+0xc0),
  `pc_drip_near_phys` (inst+0x274); one TruMenu.log line the first time bone 0 and inst+0x20 differ by > 50 units.
- **8 `light.demote`** (`[Light] Demote`, default 0, Tests / Licht (Diagnose)): set builder 0x504cc0, caster branch
  0x504e06 (`cmp dl, 3; jae drop`) -> `LdBuildStub`: shadow part full, a plain place free, the new light a plain shadow
  caster (no shadow map) -> of the set's casters and the new one, the one **farthest from the camera** (entry+0x10)
  is demoted (plain count + 1, marked per builder object); slot distributor 0x5042b0, CastsShadow call 0x504341 ->
  `LdCastStub`: a marked entry of the same object answers "no shadow" and takes a plain slot. Marks live 50 ms (the set is built every frame). Written
  on the game thread, put back when off; `light.demote` (no argument) reports demoted / kept / no plain place.
- **Settings written back (owner, live 17:07).** `IniKeep` (WritePrivateProfileString: only that key line changes,
  comments and other keys stay) right after: `quick.lang` ([Quick] Language), `cam.shakescale` / `cam.rumble`
  ([Camera]), `media.mutemusic` / `.muteambient` / `.music.inlevels` ([Media]), `light.stable` / `.stablecut` /
  `.demote` ([Light]), `cine.steprate`, `sub.valign` / `.halign` / `.margin`, `voice.lang` ([Settings]). Already kept
  before: `sub.*` look, `snd.vol.*` ([SoundGroups]), `menu.hidecursor`, `[Quick] Closed` / favourites / recent; the game
  options (`game.vol.*`, inversion, `sub.lang`, `gfx.*`) go to the registry. **Session-only by design:** debug / diagnosis
  toggles (`dbg.*`, `nav.*`, `fight.trace`, `aim.trace`, `enemy.panel`, `light.cutlabels`, `cine.pause`, `time.*`,
  cheats, `ai.*`), the sound list display (`snd.pos` / `.lines` / `.sort` / ...), `shot.oncine`. Model `persist`.
- **Defaults (coordinator, for new users: only the bar).** `[Menu] Enabled` is now the big menu window (default **0**:
  L3 + R3 / ToggleKey / items never open it, log `menu not opened ... [Menu] Enabled=0`); the old master switch "load but
  hook nothing" moved to **`[Menu] Load`** (default 1). `[Radial] Enabled` default **0**, `[Quick] Enabled` 1, `[Quick]
  Language` default **en** (also when the key is missing). Code defaults = sample `TruMenu.ini`; an edited ini is kept
  by `Set-TruMenu.ps1` (its `Enabled=1` keeps the big menu).
- **TruShadowPower 0.23 `[Meter] Infinite`**: row "Kraft unendlich" in the group "Schattenkraft (Doppelgaengerin)" (page
  Figur) - the planned row is gone.
- `Set-TruMenu.ps1` knows the 0.22.17 hash; checks `trumenu_ini_check` `check_02218`, `trumenu_quick_check` models
  `volsave`, `groups 0.22.18`, `cinepad` 0.22.18, `persist`, `subalign`.

### TO TEST 0.22.18

| # | Point | Step | Expected |
|---|---|---|---|
| 1 | volume | `game.vol.music` 64 -> 128 (bar), wait 3 s, read registry `MusicVolume`; game.quit, restart | log `0.22.18 options: 0x478010 + 0x4796b0 done ... MusicVolume 128`; registry 128; after the restart music at 100 % |
| 2 | volume | `game.mouse` 15; `game.vol.sfx` 40 | registry MouseSensitivity 15 / SfxVolume 40 |
| 3 | volume | after a `gfx.next` row (e.g. VSync), change the music volume | the next-start value stays in the registry (log `... 1 next-start value(s) again`) |
| 4 | groups | page Spiel-Einstellungen: open Ton, Grafik ab naechstem Start | headings left, rows indented, Ton-Gruppen / Geraet one step more, guide lines; closing Grafik hides Geraet too |
| 5 | groups | pages Rettung / Cheats, Tests, Zeit / Ablauf, Barrierefreiheit, Koop | every section `[-]` / `[+]`, an old `[Quick] Closed` still applies |
| 6 | groups | long menu (big window), section "Quick bar pages" | groups collapsible, sub-groups indented |
| 7 | step | held cutscene: keep View down, tap RB 3 times | 3 frames |
| 8 | step | hold RB + View 2 s (StepRate 10), release | ~16 frames, the subtitles run along, no extra frame at the release |
| 9 | step | while repeating add LB | repeat stops, photo, the cutscene stays held |
| 10 | step | `cine.steprate 5` / `15`, restart | rate as set; `[Settings] StepRate` kept |
| 11 | subtitles | `sub.halign left`, `right`, `sub.margin 0` / `10` in a cutscene and a Bink movie | lines and grey bar at the left / right margin; centre again with `centre` |
| 12 | subtitles | `sub.valign top`; `free` + `sub.pos` steps; size 1.1 | at the top; free range 16 .. 360 at 1.1, two lines visible |
| 13 | voice | in a level with Zip / Alister lines: `voice.lang de` (English game) | log `0.22.18 voice.lang #1: German: mask 0x4 set, archives report 0x4, ModLoader +0xc agrees`; next sentence German, texts English |
| 14 | voice | `voice.lang de` before a DLC 2 cutscene | the cutscene speaks German (mods `_004` files) |
| 15 | voice | `voice.lang nl` / `ja` / `ru` | refused (no `_2048` / `_032` / `_512` files) unless the mods hold them |
| 16 | voice | restart with `VoiceLanguage=de` | German speech from the start, log line at the first game frames |
| 17 | voice | "Sprache komplett: Deutsch" (right twice), restart | speech German at once; after the restart texts / menus German; registry Language 2 |
| 18 | music | install with `Set-TruMenu.ps1` (build folder has no list) | warning "using the last generated list ..."; TruMenu.log `media list ...: 63 rows` |
| 19 | music | music volume 0 | red warning row in Ton; right = 100 % |
| 20 | music | `media.music.inlevels 1`, `media.music.play l2_waters_of_thailand` in a level | plays; `[Media] MusicInLevels=1` kept |
| 21 | goo | end level corridor, `fight.trace 1`, stand under the drips | `pc_drip_b0_*` / `_lowz` move with the falling drop? log `0.22.18 goo drip copy ... differs`? report which column moves |
| 22 | light | throne cutscene held, `light.demote 1`, `light.cut 3` | no dropped light in the 5 sets (#91 plain without shadow), warm top + cool side together; `light.demote` report counts |
| 23 | defaults | fresh sample ini: L3 + R3 | nothing opens (log `menu not opened`), Start + View opens the bar, bar text English |
| 24 | persist | `quick.lang en` in the bar, restart | the bar stays English (`[Quick] Language=en` written) |
| 25 | figure | page Figur, Schattenkraft group: "Kraft unendlich" | a live switch row (TruShadowPower 0.23), no "geplant" row |

## 0.22.17 - subtitle fallback to English (2026-11-10)

For a game language whose subtitles the DLC cinematics do not carry (Russian, id 9, installed from a retail copy for the
owner's own game: `tools/lang_retail_build.py`): the DLC cinematic records hold ids 0 1 2 3 4 11 only, so the subtitle
reader 0x4538d0 found no line and the DLC cutscenes stayed without subtitles.

- In TruMenu's reader hook (the 0.22.14 call patch 0x4574ec, `SrReader`): when a record lacks the id the reader would
  show (`SrWant`: the profile word, or the game language for word -1 and kind 1; kind 2 shows nothing) and holds id 0,
  the reader gets `'<wanted id>\r<English text>\r'` (`SfBuild`) instead of the record - **only while no record of the
  same stream carried the wanted id** (`SfUse`).
- Why per stream: every language has its own cue times; a record holds only the languages whose line starts at that
  frame (32 of the 832 Russian base cinematic records carry id 0 but not 9). A per-record rule would mix English lines
  into the Russian base cutscenes. In the Russian data no record with id 0 comes before the first record with id 9 of its
  file (38 cinematics; 0 in the 3 neutral PC cinematics with subtitles; `lang_retail_build.py speech`), so the rule never
  shows English in a stream that has the language.
- Stream = the cinematic handler (`ecx` of the reader); a new stream when the handler changes or the stream time
  `[s+0x384]` of the stream whose `[s+0x77c]` is that handler goes back (stream list head `[0xccdc64]`, next `[s+0x14]`
  - the offsets of the 0.22 `kCnChecks`; read only when those checks held, else the handler alone).
- `sub.lang` rewrites (0.22.14) and TruMenu's own parse (`SrLines`, the "agrees" log) use the same rule with the stream
  ids stored per record (`seen`).
- `[Settings] SubtitleFallback=1` (default 1; a missing key counts as 1); 0 = the game's behaviour. `sub.lang` without
  argument reports `English fallback on (n record(s))`; the first 20 fallbacks log one line each
  (`0.22.17: subtitle record #n has no id 9 - English line shown`). `SbName(9)` = "Russkij (Russian)" (the menu font has
  no Cyrillic).
- No new patch site; the bytes the rule relies on (reader, language choice, stream walk) are the existing kSrChecks /
  kCnChecks rows, pinned again in `work\asi\menu0240\precheck_02217.txt` (9 checks, 0 mismatches against
  `data\pc\tru.exe`).

Checks: `tools/trumenu_ini_check.py` `check_02217`, `tools/trumenu_quick_check.py` model `subfallback` (16 cases: DLC
stream in Russian, fallback off, English game, kind 0 / 2, the id sets of a Russian base cutscene - no English stand-in,
new handler / time back / time on / time unreadable, TruMenu's parse = the reader's lines, `sub.lang` 2 -> 9 in a DLC
cutscene, `SfBuild` form, two-digit id).

### TO TEST 0.22.17

| # | Step | Expected |
|---|---|---|
| 1 | `Language` = 9 (registry), DLC 2 cutscene `pdlc2_030_pod` or `045_finale` (5 min) | English subtitle lines with Cyrillic menus; TruMenu.log `0.22.17: subtitle record #n has no id 9 - English line shown` |
| 2 | same, base-game cutscene (e.g. the prologue `010_pro_surprise`) (3 min) | Russian lines only, **no** English line in between, no fallback log line |
| 3 | `SubtitleFallback=0`, DLC 2 cutscene (3 min) | no subtitles (the game's behaviour) |
| 4 | German game (`Language` = 2), DLC cutscene (2 min) | German lines as before, no fallback log line |

## 0.22.16 - page Spiel-Einstellungen, bar reorganised, sub.lang fixes (2026-11-10)

Built into `work\asi\menu0239`, not installed. Plan: workspace `docs\Plan-TruMenu-Einstellungen-1011.md`; evidence
`docs\Befund-Spieloptionen-1011.md`; ENGINE.md rows "Option table", "Graphics block fields", "Graphics apply",
"Settings save with Graphics", "Subtitle draw parameters". Byte checks: `work\asi\menu0239\precheck_02216.txt` (the
plan's 29 checks, `kGsChecks`; 29 / 0 mismatches against `data\pc\tru.exe` and read-only against the installed
`tru.exe`). A failed check group greys only its rows and writes one log line (`0.22.16 settings: <group> - code
differs ...`); the summary line is `0.22.16: game settings page 29 of 29 byte checks ok` (first game frame).

**Page 1 "Spiel-Einstellungen / Game settings"** (collapsible groups; closed at the start: "Braucht D3D-Reset",
"Grafik ab naechstem Start", "Geraet (Diagnose)", "Ton-Gruppen (TruMenu)", "TruMenu selbst"):

| Group | Rows (item) | Way |
|---|---|---|
| Untertitel | Sprache (`sub.lang`, value row: Spielsprache -1 / English 0 / Francais 1 / Deutsch 2 / Italiano 3 / Espanol 4 / Nederlands 11, live), zeigen (`sub.show`), Textgroesse (`sub.size` 0.5 / 0.6 / 0.75 / 0.9 / 1.1), grauer Balken (`sub.box`), Balken-Deckkraft (`sub.boxalpha` 0 / 25 / 40 / 60 / 80 %), Textfarbe (`sub.colour` white / yellow / cyan / grey), Position (`sub.pos` 300 .. 400), Standard (`sub.reset`) | sub.lang: option setter 0x5d5100 + settings save 0x478010 (0.22.13 / 0.22.14). The look is TruMenu's own: draw parameters of 0x583e20 - y base disp32 0x583e39 -> TruMenu float, scale disp32 0x583e7c -> TruMenu float with line step imm8 0x583ebd = round(22 x s / 0.6) and limit 0x583ec6 = 2 x step, box flag 0x583eaa, box colour imm32 0x474f54 = alpha << 24, the line call 0x583eb6 -> `GsSubLine` (off: nothing drawn; colour: `[0x9ce6c0]` set around 0x477180 and put back, alpha byte kept). Written on the game thread (PadHook) only; a site only while it holds the game's bytes or TruMenu's own (else that row greys: "taken by another plugin"); a value at its default puts the game's bytes back; DLL detach puts back what is still TruMenu's. Kept in `TruMenu.ini [Settings]` (SubShow, SubSize, SubBox, SubBoxAlpha, SubColour, SubPos), applied at the first game frame |
| Ton | Musik / Effekte / Sprache (`game.vol.music` / `.sfx` / `.voice`, 0 .. 128 in steps of 8, shown in %), Musik aus, Ambient aus, Musik: Thailand / stoppen, group "Ton-Gruppen (TruMenu)" (the 0.21.8 sliders) | options 2 / 1 / 3 through the setter with callback 1 (live); the game's settings save 0x478010 runs once, 2 s after the last change (log `0.22.16 settings: options saved 2 s after the last change`) |
| Bild / Grafik (live) | Vollbild-Effekte (`gfx.fsfx`, +0x25), Tiefenunschaerfe (`gfx.dof`, +0x26, grey while FS is off), Schatten (+0x28), Wasser (+0x3d), Spiegelungen (+0x3c), Volumen (+0x3e), Texturfilter (`gfx.filter` 0..2, +0x50), Seitenverhaeltnis (`gfx.aspect` 4:3 / 16:9 / 16:10, +0x14), Grafik speichern (`gfx.save`, right twice), Grafik: Stand (`gfx.status`) | the runner only queues; `GfTick` in PadHook (never the Present hook) copies the active block `[0xad75e4]+0x15c`, changes the wanted fields, checks vtable `[dm]` = 0x84b54c / slot 0 = 0x522a10 and `[dm+0x10]` == 0 (else it waits, 5 s at most), calls ApplySettings(window `[0x9eede8]`, block); al = 1 -> block to 0x890388 and the option set with bool 0. Log `gfx: ApplySettings ... -> al 1, n ms`. FS grey with DisableNonPow2Textures = 1. `gfx.save` = 0x478010 + 0x4796b0 (root + Graphics), then the next-start values of this session again |
| Braucht D3D-Reset (geplant) | VSync, Dreifachpuffer, Kantenglaettung, Aufloesung / Bildrate, Vollbild, Bild-Intervall 2 (`gfx.r.*`) | **greyed by design** (coordinator 2026-11-10): the value now is shown read only; a press says "geplant: braucht D3D-Reset (TruMenu-Reset-Hook fehlt)"; no reset hook |
| Grafik ab naechstem Start | VSync, Dreifachpuffer, Kantenglaettung ... / Textur-Detail ... (command line), Ruckel-Fix (DontDeferShaderCreation = 0 + DisableDynamicTextures = 0), 32-Bit-Texturen / Hardware-DXTC / Hardware-Schattenkarten / Null-Render-Ziele aus; group "Geraet (Diagnose)": the device values of the finding's table 2.3 | `gfx.next <RegistryName> [value]`: one DWORD in `HKCU\Software\Crystal Dynamics\Tomb Raider: Underworld\Graphics` (RegOpenKeyExW / RegSetValueExW of advapi32 looked up at run time - no new import; the key must exist); the row shows the registry value; `gfx.status` lists registry != active. AntiAliasing 0 .. 8 / TextureDetail 0 .. 4: range not verified |
| Steuerung | Kamera X / Y, Zielen X / Y invertiert (`game.camxinv` ...), Vibration (Spiel) (`game.vibration`), Vibration-Staerke (TruMenu, `cam.rumble`), Maus (`game.mouse` 1 .. 20), Kampfmodus (`game.combatmode`, meaning open) | options 0xc..0xf / 0x10 / 0x96 / 0x11 through the setter (callback 1), saved 2 s later |
| TruMenu selbst | Menuesprache (`quick.lang`), Mauszeiger aus, Schnellschalter (offen) | moved from Debug / Darstellung |

**sub.lang fixes:** `SbName(11)` = "Nederlands" (was "?"), Francais / Espanol with their accents. **U3** (live 13:48:
after the first instant switch the box line was the rewritten text, which is no stored line - the second `sub.lang`
logged `did not come from a stored subtitle record`): each stored record keeps `shown[k]` = the text TruMenu wrote
(or found) for its line k; `SrRewrite` matches a box line against the reader's line or `shown[k]`, so every further
switch rewrites again (model `sublang`: + EN -> DE -> NL -> EN, + one line four times).

**Bar reorganised** (plan section 2; 17 pages, Leveldaten stays the start page 6): 0 Favoriten / Zuletzt, 1
Spiel-Einstellungen (new), 2 **Rettung / Cheats** (Rettung + the rows of Notfall that Rettung did not have, groups
"Cheats" (closed) and "Spiel" (Sterben, Spiel beenden last)), 3 **Figur** (was Lara: groups Bewegung / Anzeige,
Positionen, Fotos, Kostuem, Objekte spawnen (closed); then the saved positions and the switch groups **"Schattenkraft
(Doppelgaengerin)"** (open) / **"Kampf (Doppelgaengerin)"** (closed) - the same switches as page Fixes (TruShadowPower
ShadowPower Enabled / Buttons, Look Enabled / ScreenEffect, Meter HudBar, Adrenaline / Reticle / TimeScale;
TruShadowCombat Strike Translate / Gate, Damage, Hit, Melee, Companion), greyed (count column "(Lara)") while
TruDlc2Player's `TruDlc2PlayerDoppelganger` says Lara is played, still switchable; "Kraft unendlich" planned), 4
Kostueme, 5 **Gegner (KI)** (Anzeigen, Dumme KI, Gegner spawnen (closed), Gegner entfernen / toeten (closed),
Gegner-Diagnose (closed: ai.why, combo / fight / aim traces, ring.bits, aim.why)), 6 Leveldaten, 7 **Render** (Render /
KI + Render-Details: Flach-Ansicht, Farbe / Paesse (closed), Markup / Kanten / Physik / SAP, Navmesh / Shader /
Objektnamen (closed)), 8 Debug / Darstellung (sound list as the closed group "Ton-Liste (Diagnose)"), 9 **Zeit /
Ablauf** (time rows, Claude mark, group Ablauf), 10 Tests (teleports, test spots, cutscene, **"Licht (Diagnose)"**
closed with light.list / light.shadow, depth dump, hall02), 11 .. 16 unchanged (Barrierefreiheit "Verstehen": +
sub.size / sub.box / sub.colour). Every item of 0.22.15 stays a bar row (`trumenu_ini_check`: ring frozen, every
ring entry a row; help rows); only the doubles inside the merged page went. Groups that start closed
(`kQbStartClosed`) count as closed until opened once - `[Quick] Closed` then holds `+<key>`; keys of 0.22.15
(`ki_dumm`, `ki_spawn`, `ki_weg`, `rd_*`, `obj_spawn`, `ton_gruppen`) are the same, so an existing `[Quick] Closed`
still resolves; favourites / recent rows are item + argument and find their rows on the new pages. `kQbViewMax` 112
(the settings page with every group open).

Checks: `tools/trumenu_ini_check.py` check_02216 (29 byte checks, `ValGs<k>` = `kGsDefs[k]`, ApplySettings only in
GfTick / PadHook, `[Settings]` keys, U3, page order) and the layout checks moved to the new tables;
`tools/trumenu_quick_check.py` model `settings` (sites, steps, start-closed groups) and `sublang` + 2 U3 cases.

### TO TEST 0.22.16

| # | Step | Expected |
|---|---|---|
| 1 | `sub.lang` row on page 1: Spiel -> EN -> FR -> DE -> IT -> ES -> NL in a cutscene (5 min) | each step switches the shown line at once, label "Nederlands" for 11 |
| 2 | `sub.size` 0.5 / 0.9, `sub.pos` 300 / 400, `sub.box` off, `sub.boxalpha` 60 %, `sub.colour` yellow - in a scene and a Bink movie (10 min) | sizes / height / bar as set; centred at size != 0.6? (inference); **yellow shows yellow** (if it shows cyan the byte order is the other way round - report) |
| 3 | `sub.show` off / on in a scene (3 min) | no line while off; no old lines after on |
| 4 | Music 0 -> 64 -> 128, effects, speech; restart the game (5 min) | live; after 2 s log `options saved`; registry VoVolume / MusicVolume / SfxVolume = the values; same after the restart |
| 5 | **`gfx.fsfx` off -> on in the end level** dlc_yggdrasil_end (10 min) | short hitch, game log "Destroy Resources" / "Create Resources", **no** "Init and Reset"; picture as with the registry = 1; TruMenu.log `gfx: ApplySettings ... -> al 1` |
| 6 | `gfx.dof` on / off with FS on (far = blurred), then FS off (5 min) | DoF row greyed "nur mit Vollbild-Effekten" |
| 7 | `gfx.shadows`, `gfx.water`, `gfx.reflect`, `gfx.volfx` once each (2 min each) | live, no reset |
| 8 | `gfx.aspect`, `gfx.filter` (5 min) | no rebuild; picture changes? |
| 9 | `gfx.save` (right twice), quit the game normally, read the registry `Graphics` (5 min) | the active values; next-start values of this session written again (log) |
| 10 | a next-start row (e.g. VSync) (3 min) | registry changed, active value unchanged, `gfx.status` lists it |
| 11 | Controls: camera Y inverted live; combat mode: what changes? (5 min) | inversion at once; note the combat mode effect |
| 12 | page Figur: shadow power group in Croft Manor greyed, in DLC 2 as the doppelganger active; "Blick: Bildschirm-Effekt" off, power on (5 min) | state "grau: Lara spielt" / "Doppelgaengerin aktiv"; the switch writes TruShadowPower.ini as on page Fixes |
| 13 | new order: every old favourite row still there; page 2 Rettung / Cheats complete (5 min) | favourites / recent rows resolve; `[Quick] Closed` of before still applies |
| 14 | **U3 retest**: held cutscene with a line, `sub.lang` EN -> DE -> NL -> EN (3 min) | every switch rewrites the line (log `sub.lang: box +0x100 ... -> ...` each time, no `did not come from a stored subtitle record`) |
| 15 | group "Braucht D3D-Reset" (1 min) | **greyed by design**: values shown, a press says "geplant: braucht D3D-Reset (TruMenu-Reset-Hook fehlt)" |

## 0.22.15 - aim.trace / aim.why: the lock-on path (2026-11-10)

Live test 2026-11-10 13:30 (DLC 2 hall02, 0.22.14): LT held on an attacking yeti, Lara drew the pistol, but her chart
record stayed 39 / 40 / 15 (never 718 as on the Xbox) and CM+0x1fc bits 9 / 10 / 11 / 21 stayed 0. The new items show
which step of the lock-on path stops (static map: ENGINE.md section 13.7 "Lock-on path"; workspace
`docs\Befund-Zielerfassung-1011.md`):

1. aim input = the action records `[[[0xa02b68]+0x18]+0]` + action * 0x30 (flag 4 = held): **+0x630 = action 33
   = RT** (PC DTP 47 source 4 = pad code 5), **+0x690 = action 35 = LT** (source 22 = pad code 4; the XInput poll
   0x484c06..0x484c47 gives bLeftTrigger code 4, bRightTrigger code 5); gates byte 0x8ab4e6 != 0, `[0xe7f144]` bit 0
   clear, byte `[0xe7f143]` != 4; weapon slot `[[P+0x500]+0x134]` (P = `[0xfadb58]`; -1 none, 7 / 12 block, 3 / 4
   always) - condition 506 (0x763c50 -> 0x6f2800) reads action 33 (RT), the lock update 0x7216b0 sets **P+0x58c =
   tuning byte `[0xfad764]+0x294` while LT is held** and P+0x588 = byte +0x27c while RT is held (`[0xfad764]` = the
   player instance's data +0x50, set at 0x71adbd);
2. chart: condition 506 takes record 38 -> 709, then 714 / 716 -> **718** (`{400,401,401} {400,403,415} {500,525,0}
   {2100,2102,3,NOT}`); record 710 runs activities 1001 / 1003 / 1004 = CM+0x1fc bits 19 / 18 / 20;
3. lock update 0x7216b0 (from CombatManager::Update 0x7227d3): bit 18 clear -> off; bit 11 -> nothing; timers P+0x58c
   (LT) / P+0x588 (RT) not > 0, P+0x798 == 0 and bit 21 clear -> off; else bit 19 -> lock 0x71edf0 (**bit 10**) or
   soft lock 0x71ec50 (**bit 9**), which set targeter 0's parameters (chart parameter 0x3f6 or `[0xfad764]+0x488`) and
   select / set its target;
4. target = P+0x540 while P+0x788 > 0, else targeter 0's +0x90 node (0x71d0c0) - the ring chain reads it (`ring.bits`).

- **`aim.trace 1|0`** (bool, default 0, live; bar page Tests "Ziel-Spur (TruAim.log)"): every 100 ms on the game
  thread, one TSV line per change into **`TruAim.log`** next to TruMenu.log (header at every open; 40 columns): RT
  (action 33) / LT (action 35) held + both action flag words, the three gates, weapon slots +0x134 / +0x138, timers
  P+0x588 / +0x58c / +0x798 / +0x788, tuning bytes +0x294 / +0x27c, CM+0x1fc with bits 9 / 10 / 11 / 18 / 19 / 20 / 21, Lara's chart records (machines 1 / 2), targeter 0 (flags,
  target, candidates, bucket counts, rejected count, parameter pointer / flags / groups), its candidate list
  (`name#intro@distance/angle:group<g>|rejected|TARGET`, angle = between the camera view and Lara -> enemy, x / y), the
  nearest AI enemy (6000 units), where it is in targeter 0, why code + text. Change key: timers as sign, distances
  to 100 units, angles to 10 degrees. At most 100 000 lines.
- **`aim.why`** (info item, bar row "Warum kein Ziel? (live)"): the first blocking step for the nearest enemy in plain
  words (DE / EN after the quick bar language), then RT / LT held, weapon, bits 9 / 10 / 11 / 18 / 19, records,
  targeter 0 candidates / rejected. Order (model `aimwhy` in `tools/trumenu_quick_check.py`, 18 cases): no enemy ->
  locked -> scripted target -> no weapon -> weapon 7 / 12 -> game gate -> no aim input -> bit 18 -> bit 11 -> LT held
  but tuning byte +0x294 = 0 -> no lock bits -> targeter 0 missing / no candidates / not offered / rejected / other
  target / in a group.
- A candidate in group g passed eligibility 0x6ecca0 and filter group g (0x712090, distance / angle records); in the
  rejected list it failed eligibility or every group - which one is **not** read (no game function is called;
  TruShadowCombat's WHY does it for targeter 9 only). The thrall label "Z9 abgelehnt F00 (Filter)" is **targeter 9**
  (TU index 9, the doppelganger finisher targeter of condition 2011, parameters from the DLC 2 tuning), not the aim
  targeter 0: F00 = eligibility passed, none of its filter groups.
- Read only, every pointer checked, 25 byte checks (`kAmChecks`, `work\asi\menu0238\precheck_02215.txt`: 0 mismatches
  against `data\pc\tru.exe` and the installed `tru.exe`); also needs the ring.bits and combo.trace checks.

### TO TEST 0.22.15

| # | Step | Expected |
|---|---|---|
| 1 | game start, first `aim.trace 1` | log `0.22.15: aim.trace / aim.why ok (25 checks)`, reply `aim.trace 1 - one TSV line per change in TruAim.log ...`; TruAim.log gets the header |
| 2 | DLC 2 hall02, pistol drawn, no enemy near, no trigger held | lines with `act35_lt_held 0`, why 2 (`noenemy`) or 6 (`noinput`); note `tune294` / `tune27c` |
| 3 | yeti / thrall in front, **hold LT** (as 13:30) | `act35_lt_held` 1? `t58c_lt` > 0? `tune294` > 0? bits b9 / b10? `lara_rec0` 718? |
| 4 | same, read `aim.why` in the bar (page Tests) | one sentence; note it with the screenshot |
| 5 | **hold RT** at the enemy (without LT), then both | `act33_rt_held` 1, `t588_rt` > 0 (`tune27c`), b9 or b10? |
| 5a | if `act35_lt_held` stays 0 while LT is held | the trigger reaches the game as another pad code (pad mapping / XInput) - press the bumpers / RS click one by one, 2 s each, and note which column moves |
| 6 | if the lock bits come (b10 1) but no ring: candidates column | yeti `group0` / `rejected` / `TARGET`, distance / angle |
| 7 | main game (any level with pistols), hold the aim button at an enemy | the same columns with a lock (b9 / b10 1, `TARGET`) - the PC baseline |
| 8 | `aim.trace 0` | file closed, `aim.trace 0 - off`; regression: `fight.trace`, `ring.bits`, `enemy.panel` unchanged |

## 0.22.14 - sub.lang switches the shown subtitle lines at once (2026-11-10)

Built into `work\asi\menu0237`, not installed. Byte checks: `work\asi\menu0237\precheck_02214.txt` (13 checks, 0
mismatches against `data\pc\tru.exe` and the installed `tru.exe`); the 21 checks of 0.22.13 stay. Background: ENGINE.md
rows "Subtitle record format", "Subtitle line clock", "Subtitle language at run time"; workspace
`docs\Befund-Untertitel-Live-0911.md`.

Before, `sub.lang` changed only the profile word: the two lines in the subtitle box 0xccdec0 are finished copies, so the
old language stayed on screen until the next line - in a cutscene held by `cine.pause` (0.22.13 holds the line clock)
until the user stepped on.

- **Subtitle record (static, from the code):** the cinematic handler update 0x457100 copies a frame's subtitle text
  (at most 0xfff bytes, NUL at the end) to the static buffer 0x9ccfa0 and calls the reader 0x4538d0 with it (call
  0x4574ec). One record holds **every language**: `<id>\r<text>\r<id>\r<text>\r...` (ids 0 en, 1 fr, 2 de, 3 it, 4 es,
  11 nl in DLC 2). Per entry the reader takes `atoi` of the id, the text up to the next `\r` (**255 bytes at most**, the
  rest is skipped), and shows it when the handler's kind byte `[[ecx+4]+4]` is not 2 and (id == the profile word, or
  word -1 and id == the game language `[0x8906b8]` and kind 1). A shown entry is cut at `\n` (strtok) into lines; each
  line loses a leading `<speaker>: ` and goes to 0x583db0(box, line, 90) - **one record adds 0..n lines** (n = the `\n`
  lines of the chosen entry; usually 1). Text bytes are **UTF-8** (`tools/mul_sub_records.py`: 107 non-ASCII entries
  in 76 records of the installed `cinstream\*.mul`, all valid UTF-8); the box keeps them as they are (strcpy).
- **Record ring:** the call 0x4574ec goes to TruMenu's `SrReader`, which copies the **whole record** (not the pointer -
  0x9ccfa0 is reused for the next frame) with the kind byte, the profile word and the game language into its ring of the
  last 2 records, then calls the reader. The call 0x453a17 (reader -> box) goes to `SrAddLine`, which notes each line
  the box takes (not in game state 6 / 10, where 0x583db0 drops it), then calls 0x583db0. Both are rel32 call patches,
  set once on the first game frame after 13 byte checks (`kSrChecks`) - after the 0.22.13 checks, which also read
  0x4574ec. A patch site that is not the game's (another plugin) is left alone: `patch refused` in the log and in
  `sub.lang` (no argument), and `sub.lang <n>` works as in 0.22.13. Because of that order the `0.22 cine.pause: ...
  checks` log line now comes at the first game frame, not at the first `cine.pause`.
- **Rewrite on `sub.lang <n>`** (after the option setter and the settings save, game thread): each non-empty box line
  (+0 upper, +0x100 newest) is looked up among the stored lines (newest first; the box moves the newest line up at the
  next line, 0x583d80, and when the clock runs out); the record's lines for the new language are built exactly as the
  reader does, and the line is written into the box (<= 0x100 bytes incl. NUL). If the two box lines followed each
  other, the upper one becomes the line before the new newest one. The clock +0x208 and the floats +0x200 / +0x204 are
  not touched - in a held cutscene the new line stands at once and the clock stays held. A line that did not come from
  a stored record (Bink movie 0x4a09c8 / 0x4a0a02, the 0xfff-text line 0x4574d7, an older record) stays and is logged
  (`did not come from a stored subtitle record ... left unchanged`); a record without the new language leaves the line
  before it as the newest (as the game would). Log per record: ids, kind, word, lines then / now and `TruMenu's parse
  agrees` (the reader's own lines against TruMenu's copy of the parse; `DIFFERS` = report it).
- `sub.lang` (no argument) adds `instant switch on (n records read, n lines, n rewrite(s))`; the reply of
  `sub.lang <n>` says `shown lines: 2 rewritten, 0 left ...`.
- Checks: `tools/trumenu_ini_check.py` check_02214, `tools/trumenu_quick_check.py` model `sublang` (13 cases: the
  DLC 2 record of `pdlc2_030_pod.mul`, back to English, French UTF-8, clock expired, Bink line, -1 / kind, 2 lines -> 1,
  no German entry, speaker strip, 255 bytes, id -1).

### TO TEST 0.22.14

| # | Step | Expected |
|---|---|---|
| 1 | game start (first game frame, front end) | log `0.22.14: sub.lang instant switch (subtitle records) ok (13 checks)` and `0.22.14 sub.lang: subtitle record ring on (checks ok): S1 ..., S2 ... -> TruMenu` |
| 2 | `sub.lang` (no argument) after a cutscene line | `... instant switch on (n records read, n lines, 0 rewrite(s))` |
| 3 | DLC 2 ceremony room `pdlc2_030_pod` (English subtitles), hold the cutscene with a line on screen (LB + View), `sub.lang 0` first if needed | the line stays English |
| 4 | held: `sub.lang 2` | **the shown line switches to German at once** (both lines if two are shown); reply `shown lines: 1 rewritten` (or 2); log `sub.lang: box +0x100 (record #n line 1/1) '...' -> '...'`, `TruMenu's parse agrees`; badge still `Untertitel stehen` |
| 5 | held: `sub.lang 0` | **back to English at once** |
| 6 | held: `sub.lang 2`, then step with RB + View until the next line | the next line in German; the clock still held after the step |
| 7 | release (LB + View) | the cutscene runs on, the lines in German and in sync |
| 8 | `sub.lang 0` during a running (not held) cutscene | the shown line switches at once, the next lines English |
| 9 | Bink movie with subtitles, `sub.lang 2` during it | its line stays (log `did not come from a stored subtitle record`), next movie German |
| 10 | `sub.lang -1` (game language) in a held cutscene | the line in the game's language (German game -> German) |
| 11 | regression: the 0.22.13 rows 1, 5, 8 | unchanged |

## 0.22.13 - pad combos on release, subtitles held, sub.lang kept, ring bits, goo drip columns (2026-11-10)

Built into `work\asi\menu0236`, not installed. Byte checks: `work\asi\menu0236\precheck_02213.txt` (21 checks, 0
mismatches against the installed `tru.exe`). Background (workspace): `docs\Befund-PC-Test-0911-Abend.md` rows 6, 7, 7b,
9 and "TruMenu 0.22.12", `docs\Befund-Goo-Tropfen-1011.md` section 3, `docs\Befund-Anvisier-Kreis-0911.md` section 6.

- **Cutscene pad combos (row 6: LB + View pressed before RB fired "weiter" on the way to the photo).** A combo whose
  buttons are part of another combo - by default LB + View (weiter) and RB + View (1 Bild), both inside LB + RB + View
  (Foto) - now fires on **release** (when one of its buttons is let go) and only if no other combo button was added
  while it was held. A combo that is part of no other (the photo) fires as soon as exactly its buttons are held. One
  action per press; then every combo waits until no combo button was held for 120 ms (as 0.22.9). A press that had
  another combo button in it and does nothing writes `cine pad: combo 0x.... let go after 0x.... was held - no action`.
  Keyboard keys (`[Cine] PauseKey` ...) unchanged. Model: `tools/trumenu_quick_check.py` `cinepad` (11 cases).
- **The pause holds the subtitle lines too (row 7b).** Static (2026-11-10): a cutscene's subtitle text comes with its
  stream frames - the cinematic handler update 0x457100 (skipped by the 0.22 gate) hands it to the reader 0x4538d0,
  which adds each line with 0x583db0(text, 90) to the subtitle box 0xccdec0 (two 0x100-byte lines, line clock +0x208).
  The only thing that counts the clock down is the subtitle **draw** 0x583e20 (from the game display 0x5da17d):
  `+0x208 -= [0xe7f188]` (the scaled frame time) unless the game state byte 0xe7f143 is 6 / 10 (the game's pause); at
  <= 0 the newest line moves up, the lower one is cleared and the clock restarts at 90 (3 s) - that is why the lines
  scrolled away while picture and sound stood. While a cutscene is held, the disp32 of that `fsub` (0x583f24) points to
  TruMenu's own float: 0.0 while held, the game's frame time while stepping (`cine.step`) or while nothing is held; it
  goes in and out with the stream walk calls. 6 byte checks (`kCnSubChecks`); a mismatch keeps only this part off
  (`0.22.13 subtitle clock: 6 checks ...` in the first `cine.pause` log line). The badge says `, Untertitel stehen`; the
  "holds cutscene stream" line shows the clock and both lines.
- **`sub.lang` survives a restart.** The game writes its settings only in **0x478010**, whose only caller is the
  shutdown path 0x5df930 (0x5df935) - a game ended by `game.quit` (TerminateProcess) or a crash never saves, so the
  option was back at -1. `sub.lang <n>` now calls 0x478010 right after the option setter (game thread, `__try`, 3 byte
  checks `kSbSaveChecks`, `[0xad75e4]` must be set): it writes the settings as they are now - graphics copy, options,
  volumes, `SubtitleLanguage` - to `HKCU\...\Tomb Raider: Underworld`, exactly what the game writes at a clean exit. Log:
  `sub.lang: settings save 0x478010 done (#1) - registry mirror [0x8900e8] now 2`. No INI value needed.
- **Enemy panel:** `Kampf-Spur: an (203 Zeilen)` / `Fight trace: on (203 lines)` (was `Kampf-Spur: Zeilen 203`), and a
  new line `Ring: Bits 9:0 10:1 11:0 21:0 | HUD12 1 | Stil 2 | Fk40 0x0040 (6:1 9:0)`.
- **`ring.bits` (info, bar page Tests "Ziel-Ring: Bits (live)")** - the combat reticle request (K-5, ENGINE.md "Combat
  reticle"): CM = `[[0xfadb58]+0x504]`, `+0x1fc` bits 9 / 10 (helper 0x6f1ed0) / 11 (lock-on, 0x71e73f) / 21, HUD group
  bit 12 of 0xfae924 (0x77d9d0), style byte 0xfae8ac (0x77a680), position 0xfae8a4 / a8, reticle `[CM+0]` word +0x40
  (bits 6 / 9, 0x71e992 / 0x7037dc). Read only, never switches anything. 7 byte checks `kRgChecks`; bit 21's own
  readers 0x71e979 / 0x715026 are only checked offline - TruShadowPower patches 0x71e979.
- **`fight.trace` new columns (at the end; the TruXenia order and every older column unchanged):** `pc_ring_bits`
  (`9:0 10:1 11:0 21:0 (0x<word>)`), `pc_hud_g12`, `pc_ret_style`, `pc_ret40`; goo drips `pc_drip_q10706`,
  `pc_drip_q10707` (uber node of each source + time in it, `Spawn_easy@0.35`, `->Done` while a transition runs),
  `pc_drip_n` (copies of object 929 / 942), the nearest copy (x / y distance to Lara): `pc_drip_near_x/_y/_z`,
  `pc_drip_near_dxy`, `pc_drip_near_dz` (copy - Lara), `pc_drip_near_iflags` (inst+0x14), `pc_drip_near_node`; and
  `pc_lara_dmg` (Lara's LP drop in this 100 ms sample, `-2000.0 dead` when the LP is gone). The drip columns are filled
  only when a source (intro 10706 / 10707 of object 926) is loaded and Lara is within 2500 units (x / y) of their mid
  point; there a line is written every sample. A line is also written when the ring bits change or Lara loses LP. A
  header line is written at every `fight.trace 1` (the column count grew; `tools/fight_trace_compare.py` takes repeated
  headers). **No hook on 0x637590:** TruShadowCombat hooks it (`[Damage] Log`: target, type, sub, amount as `damage
  types` lines); TruMenu logs once whether the entry is the game's or a foreign jump and uses the LP drop.

### TO TEST 0.22.13

| # | Step | Expected |
|---|---|---|
| 1 | first `cine.status` / `cine.pause` | log `... 0.22.13 subtitle clock: 6 checks ok` |
| 2 | end cutscene with subtitles, LB + View, release | pause on when released (not on pressing); log `cine key (pad (released))` |
| 3 | held: LB + View, then add RB | photo only; the pause stays on (no "weiter"); log `cine key (pad)` with the shot |
| 4 | held: RB + View, release | one frame on |
| 5 | held for 10 s with a subtitle line on screen | the line stays (badge `, Untertitel stehen`); log line "holds cutscene stream ... subtitle clock ... held" |
| 6 | `cine.step 30` while held | the subtitle moves on with the frames |
| 7 | release (LB + View) | the line runs on from where it stood, next lines in sync with the speech |
| 8 | `sub.lang 2` | log `sub.lang: settings save 0x478010 done (#1) - registry mirror [0x8900e8] now 2` |
| 9 | quit the game (also with `game.quit`), start again, `sub.lang` | `subtitles now 2 (Deutsch) ... registry mirror 2` |
| 10 | `enemy.panel 1`, `fight.trace 1` | panel: `Kampf-Spur: an (n Zeilen)` and a `Ring:` line |
| 11 | bar Tests "Ziel-Ring: Bits (live)" while Lara aims at a thrall (LT), then with the power (RB) | bits / HUD12 / style change; note which ones (K-5: target + bit 9/10/21 -> HUD12 1) |
| 12 | DLC 2 end level, goo drip corridor with `fight.trace 1` (with / without power, die once) | TruFight.log: lines every 100 ms there, `pc_drip_*` filled, `pc_lara_dmg` at the death; log `0.22.13: damage function 0x637590 ...` once |

## 0.22.12 - fight trace follows Lara, quick bar shows trace states (2026-11-09)

Built into `work\asi\menu0235`, not installed. No new hooks (no byte checks needed).

- **`fight.trace`:** a Lara-only line (enemy columns `-`, the same column layout as 0.22.11, TruXenia compatible) is
  also written when Lara's chart record of machine 2 (`lara_rec1`) or her machine-1 state ids (`pc_lara_states`)
  change. Before only machine 1's record (`lara_rec0`), the camera, the power mode and enemy changes started a line, so
  phases where only Lara changed (aiming next to an idle tutorial thrall) were missing or only caught by chance (PC log
  2026-11-09 20:18-20:19: `lara_rec1` 48 / 40 only on lines written for other reasons). Still at most one line per
  100 ms sample; an enemy line in the same sample carries Lara's columns anyway.
- **Quick bar:** the bool rows Kampf-Spur (`fight.trace`) and Kombo-Spur (`combo.trace`) always showed "aus": their
  value text starts with the id (`fight.trace 1; 12 line(s) -> ...`) and the on / off reader looked only at the first
  character. It now skips a leading `<id> ` - the same reader serves the ring and the menu's bar pages. The switch
  itself worked (log `fight.trace 1`). `enemy.panel`, `light.stable`, `light.stablecut`, `light.cutlabels` already
  showed their state (value text starts with 0 / 1).
- **Quick bar:** an action row of an item with a short value shows the value before "rechts" - Untertitel-Sprache
  (`sub.lang`) shows the subtitle language now, e.g. `Deutsch (2) - rechts`.

## 0.22.11 - Xbox comparison, PC side: fight trace and enemy panel (2026-11-09)

Built into `work\asi\menu0234`, not installed. Byte checks: `work\asi\menu0234\precheck_0231.txt` (13 checks, 0
mismatches against the installed `tru.exe`). Goal: the PC logs the same values as TruXenia (`tools/truxenia.py`
`watch`) does on the Xbox in Xenia, so both runs of the same test card (`docs\Testkarte-Kampf-0911.md` in the
workspace) can be put side by side. Read-only: no game value is written; every pointer is checked before it is read.

- **`fight.trace 1|0`** (default 0, bar page Tests "Kampf-Spur (TruFight.log)"): tab-separated lines into
  **`TruFight.log`** next to TruMenu.log (opened shared, readable while the game writes; header line when the file is
  empty, at most 200000 lines per session). Sampled every 100 ms on the game thread; a line is written when an enemy's
  LP, state (layer 0 / 1), requested state or target changes, and a Lara line (`inst` = `-`) when Lara's chart record,
  the camera mode / position, power active, a time scale or a time-scale request changes. Columns - the TruXenia ones
  first, in its order and format: `host_time inst obj_id obj_name lp stamina state0 state1 req target dist lara_rec0
  lara_rec1 meter active time_scale`, then the PC-only ones: `pc_intro pc_ko pc_attack pc_hit pc_lara_lp pc_lara_states
  pc_lara_x pc_lara_y pc_lara_z pc_x pc_y pc_z pc_power_mode pc_player_time_scale pc_doppelganger pc_cam_obj
  pc_cam_mode pc_cam_req pc_cam_dx pc_cam_dy pc_cam_dz pc_cam_dist pc_cam_fov_deg pc_ts_requests pc_ts_selected
  pc_ramp_last`.
  - `time_scale` = world time scale `[0xe7f1a0]` (TU gameTracker+0x118, the TruXenia column), `pc_player_time_scale`
    = `[0xe7f1d4]`; `meter` / `active` from `TruShadowPowerMeterApi` (value, flags bit 0); `pc_power_mode` `slow`
    (world < 0.99) / `fast` (active at 1.0 - the Xbox goo-drip run, X23) / `-`.
  - `pc_ts_requests` = the meter's 7 time-scale request slots (TU meter +0x40, `{player, world}`, empty = -1) as
    `slot:player/world` for each occupied slot; `pc_ts_selected` = what the selector takes (highest occupied slot,
    `P1.20(s0) W0.30(s0)`). TruShadowPower 0.20 fills slots 0 / 4 / 5 only - the column shows it, nothing is changed.
  - `pc_ramp_last` = the last call of the retail time-ramp natives SetWorldTimeScale 0x776030 / SetPlayerTimeScale
    0x776090 (`gamebase` natives 23 / 24, the ones the TU routes to slot 6). While fight.trace or enemy.panel is on, a
    pass-through counter sits on both (6-byte jump after a byte check of the prologue, trampoline back; arguments and
    result unchanged) and writes one TruMenu.log line per call: `time ramp: world <- 0.300 over 0.250 s (gamebase native
    23; caller 0x... in <module>)` (24 for player; at most 2000 lines); `pc_ramp_last` = `hh:mm:ss.mmm W0.300@0.250s
    <module>`. It stays in place until the game ends.
  - `pc_attack` while an enemy is in MeleeAttack: the attack record (state data+0x50) and its anim refs +0x78 / +0x7c /
    +0x80 (`0x... a<type>/<anim> ...`) - which melee attack runs (the spit attack, X22).
  - `pc_hit` = the last hit of this enemy: amount, the state at the hit, the reaction (the first other layer-0 state
    within 1.5 s). Damage type and knockback come from TruShadowCombat's own lines (`damage types`, `0.6.7 hit`,
    `0.6.7 knockback`) in TruMenu.log, joined by time - TruShadowCombat does not export them.
  - Camera: position = vtable +0x34 of the current camera (base 0x5e1c60 `lea eax,[ecx+0xa0]`, snapshot 0xe8eeb0 while
    byte `[0xe8eec8]`), FOV = vtable +0x40 (base 0x5e1c90 `fld [ecx+0xb0]`, radians, logged in degrees), read only when
    the camera's vtable slot holds that base function; `pc_cam_d*` / `pc_cam_dist` = camera minus Lara. The look-at
    point is **not** logged (no proven field yet).
- **`enemy.panel 1|0`** (default 0, bar page Tests "Gegneranzeige"): a fixed panel at the right edge for the nearest
  enemy within 3000 units (the trace takes 6000; DE / EN with the language switch):
  ```
  Gegner viking_thrall (11270) - 312
  [#########.....] 420 / 500
  St 0.0 | Zustand Hit / - | Soll -
  Ziel Lara | Ko ja 1/2
  Treffer -60 Hit | -40 Hit | -20 Hit
  Lara 1000 | Kraft 967 Zeitlupe | Zeit Welt / Lara 0.30 / 1.20
  Zeit-Anforderungen 0:1.20/0.30 -> P1.20(s0) W0.30(s0)
  ```
  `St` stamina, `Zustand` layer 0 / 1, `Soll` requested state, `Ziel` target (Lara / ? / -), `Ko` attack coordinator
  (holds a slot ja / nein, grants / calls; `Ko 0` = no record, `Ko ?` = not read), `Angriff` line during MeleeAttack,
  `Treffer` the last 3 hits (amount and reaction), then Lara's LP, the power and both time scales, the request slots.
- Compare: new read-only `tools/fight_trace_compare.py --pc TruFight.log --xbox <truxenia watch .tsv>` (time
  filters per side, `--enemy`, `--show COL`): the n-th hit of each side in one table (time, enemy, LP, damage, state at
  the hit -> reaction, the same rule on both sides), the state sequence per enemy, reaction counts and the power phases.
  `tools/combat_log_compare.py` (combo lines) is unchanged.
- Open: the look-at point; whether the PC also routes script ramps into a request slot (the column shows it live);
  `stamina` on the PC is the brain field the 0.22.9 label shows (meaning against the Xbox column still to compare).

## 0.22.10 - light cut diagnosis and a stable light choice per object (2026-11-09)

Built into `work\asi\menu0233`, not installed. Byte checks: `work\asi\menu0233\precheck_0230.txt` (9 checks, 0
mismatches against the installed `tru.exe`). Background: workspace `docs\Befund-Licht-Kuerzung-0911.md`, ENGINE.md 16
"Light set builder". The PC cuts every object's lights in the set builder **0x504cc0**: it walks the object's light
list in order and keeps the first lights that fit - at most 7, sun 1, shadow slots 3 (of them at most 2 with a shadow
map), plain 3 (overflow into free shadow slots); a light that fits nowhere is dropped (0x504e56), lights after the 7th
are not looked at. When the order of the list changes from frame to frame (the throne end cutscene), an object with more
fitting lights than slots gets another choice every frame - the flicker. The Xbox shaders take 7 lights of any kind
(Xenia 2026-11-09: no flicker, Natla lit warm and cool at once).

- **`light.cutlabels 1|0`** (bar page Tests next to "Licht-Reihenfolge fest", no argument = report): a line top left
  `Licht-Kürzung Bild <n>: <sets> Sätze, <cut> gekürzt; stärkste: Li 9 -> 7 (S1 M2 C1 P3) drop 2` and a label at every
  light that was dropped in the last frame (`Licht #<index from light.list> (<kind>)` / `verworfen <n>x, behalten <n>x`).
  `Li a -> b` = lights offered to the set -> kept; `S` sun, `M` with a shadow map, `C` shadow slots without a map
  (shadow casters and plain lights that overflowed there), `P` plain slots; `drop` = taken out again because no slot
  was free. Kinds: Sonne / Schattenkarte / Schattenwerfer / einfach - the builder's own tests (res+0x42c == 2,
  res+0x418 && res+0x42c, CastsShadow 0x50a080, rest). The label position is the light's transform row L+0x50 (as
  light.list - to be confirmed live).
- **`light.cut [frames] [all]`** (bar: "Licht-Kürzung ins Log (3 Bilder)"): frames (default 3, at most 30) into
  TruMenu.log - per frame a summary line, then per set `caller`, offered -> kept, category byte, drop, "not looked at",
  and the offered list in order: `+` kept, `-` dropped, `.` not looked at, each `#index 0xlight kind (position)`.
  Default only the sets that dropped a light; `all` = every set (several hundred lines per frame). Info only. A set
  cannot be named by the game object it belongs to (the builder only gets the light list); the list and the caller
  address tell them apart.
- **`light.stablecut 1|0`** and **`[Light] StableCut`** (default 0, live from the bar): before the cut, the object's list
  is ordered by kind (sun, shadow map, shadow caster, plain), then by the light's address - stable from frame to frame,
  only for the per-object choice; the collected scene list and with it the shadow atlas order stay the game's.
  **How it relates to `light.stable` (`[Light] Stable=1`, default since 0.22.5):** light.stable sorts the whole
  collected list +0x250 at 0x56d69a (also the shadow atlas order) and keeps the choice that the address order gives
  (warm at the throne, the cool front light on Natla missing); light.stablecut only fixes the per-object choice and puts
  the shadow-mapped and shadow-casting lights first. Both on is allowed (StableCut decides the per-object order then).
  **A / B at the throne:** (1) Stable=1, StableCut=0 (as now) and (2) Stable=0, StableCut=1 - each with
  `light.cutlabels 1` and a `light.cut 3` while Natla is on screen; compare the flicker and which light is dropped.
- Hooks: `jmp` at 0x504e56 (5 bytes `80 44 24 1a ff`, back 0x504e5b) and at 0x504eb9 (8 bytes `8b 4e 0c 51 8d 54 24 18`,
  back 0x504ec1) only while the labels are on or a capture runs; `jmp` at 0x504cd9 (6 bytes `8b 86 34 12 00 00`, back
  0x504cdf) only while StableCut is on. All written on the game thread and put back when off; refused (one log line)
  when the bytes are not the game's.

### TO TEST 0.22.10

| # | Step | Expected |
|---|---|---|
| 1 | log | `0.22.10 light cut: 9 checks ok` (first use) |
| 2 | throne cutscene, "Licht-Kürzung anzeigen" on, `cine.pause` | summary line top left; labels at dropped lights; `light cut diagnosis on` in the log |
| 3 | `light.cut 3` while Natla is on screen | 3 frames of `light.cut f<n>` lines: which light is `-` (dropped) and whether it changes per frame |
| 4 | light.stable off, "Licht-Auswahl je Objekt fest" on | no flicker; compare Natla's light with the Xenia picture (warm + cool) |
| 5 | both off | the flicker is back (proves the order is the cause) |

## 0.22.9 - enemy diagnosis, combo trace, subtitle language live, combo fix (2026-11-09)

Built into `work\asi\menu0232`, not installed. Byte checks: `work\asi\menu0232\precheck_0229.txt` (9 checks, 0
mismatches against the installed `tru.exe`).

- **Third enemy label line** (dbg.enemies, every AI enemy, light blue): why an enemy attacks or not and how it took the
  last hit. Live symptom 2026-11-09: the hall02 tutorial thrall walks to Lara, follows her, stays in `CombatStepIdle`
  and never attacks. Example: `Ziel Lara 312 | Ko nein 0/14 2s | Soll - | L1 - | Sp - | St 40 | Tr 3 -20>HitReaction`.
  - `Ziel` - the enemy's current target (EnemyTargeting brain+0x4e10, slot +0x30: mode 0 sense / 1 instance / 2
    position): `Lara <distance>`, another instance, or `- (m<mode>)` = none.
  - `Ko` - attack slots: the coordinator 0x67d780 (asked before Attack / MeleeAttack, callers 0x63a731, 0x64fefb,
    0x65b9f9, 0x65bd26, 0x673981) counted per enemy: `ja` / `nein` = last answer, granted / calls, seconds since the last
    call; `Ko 0` = the enemy never asked. A pass-through detour on its 5-byte prologue (`83 ec 18 53 56` ->
    trampoline), placed on the game thread the first time a label or `ai.why` needs it; it never changes the answer.
  - `Soll` - the requested state (brain+0x18f8), `L1` - the layer 1 state (brain+0x1260); `-` = none, else the state name.
  - `Sp` - the game's gate bits brain+8: `A` = 0x20 Attack / ScriptAttack off, `M` = 0x100000 Melee off, `X` = 0x800 no
    damage; `-` = none set.
  - `St` - stamina (health component brain+0x2c60 +0xc, lowered by 0x620ea0).
  - `Tr n -x>State` - hits seen (LP drops), the last amount, and the first state the enemy entered within 1.5 s after it
    (= the hit reaction the game chose: e.g. HitReaction / Vaulted / Fall / RegenerateDeath).
- **`ai.why [intro id|0xINSTANCE]`** (bar page Tests, group "Gegner-Diagnose"): the nearest AI enemy (or the given one),
  one long line in TruMenu.log - L0 / L1 / requested states, brain+8 and +0xc, target slot and override slot (+0xf0) with
  "Lara", the 12 senses (how many hold Lara), attack-slot calls / grants / last answer, LP / damage taken / stamina, hits
  and the last reaction. Read-only, never toggles anything.
- **`combo.trace 1|0`** (off by default, live, no argument = report): per AI enemy hit within 3000 units one log line
  `combo: Lara records <path> -> <enemy> LP a -> b (-x), stamina s -> t, state at the hit ..., reaction ...`. Path =
  Lara's chart records of chart machine 1 (`[[0xfadb58]+0xf10]`, update 0x787e60 from 0x768c65), the last up to 6 record
  indices within 2 s - the combo steps; the damage type / sub / amount of the same hit is TruShadowCombat's
  `damage types` line with the same time stamp. Not traced: the input / link window of each chart transition (needs a
  hook on the transition 0x787890, which TruTrace already logs), no bar line yet.
- **`sub.lang -1|0..4|7|9..12`** (no argument = report): the subtitle language live, as `docs\Befund-Untertitel-Live-0911.md`
  (workspace) proposes - the game's option setter 0x5d5100(0xb, value, 1) on the game thread; its callback 0x5d4dc0
  writes both profile words `[[0xc59264]+0x208]` / `[[0xc59268]+0x208]`, which every subtitle line reads (0x453990);
  movies take it at their next start; the next settings save keeps it in the registry. Checks 0x5d5100, 0x5d4dc0,
  0x453990; at run time `[0x8ab594] == 0x5d4dc0` and both profiles set.
- **Cutscene pad combos fixed** (live 2026-11-09 15:13: the photo combo View + LB + RB also fired View + LB = pause off
  and View + RB = step): only the buttons of the three combos count, a combo fires when exactly its buttons are held and
  that set stood still for 120 ms (pressing View, LB, RB one after the other gives the photo, not the pause on the way),
  once per press - then all combos wait until no combo button was held for 120 ms. Keyboard keys unchanged (edges).

### TO TEST 0.22.9

| # | Step | Expected |
|---|---|---|
| 1 | log | `0.22.9: ai.why / enemy diagnosis line ok (5 checks)`; after the first labels `coordinator 0x67d780 counted` |
| 2 | hall02 tutorial thrall, dbg.enemies on | third line; while it idles: `Ko 0` (never asks) or `Ko nein n/m` (asks, refused) - decides the next step |
| 3 | bar Tests: "Warum greift er nicht an?" | one `ai.why:` line in TruMenu.log |
| 4 | "Kombo-Spur" on, hit a thrall with X X X | `combo:` lines, path grows per step; reaction state per hit |
| 5 | cutscene, View + LB + RB | photo only - no pause toggle, no step |
| 6 | cutscene with subtitles, `sub.lang 0` then `sub.lang 2` | next line in English, then German |

### TO TEST 0.22.1

| # | Step | Expected |
|---|---|---|
| 1 | log | `0.22 cine.pause: 7 checks ok; 0.22.1 sound pause: 4 checks ok` |
| 2 | end cutscene, Szene anhalten | badge top centre, sound silent (no loop); log "master channel group ... paused" |
| 3 | wait 10 s, release | speech goes on where it stopped, lips and sound in sync |
| 4 | held: Ein Bild weiter a few times, `cine.step 60` | the scene moves on a little, no sound, still in sync after release |
| 5 | at the throne: Stelle merken; reload the checkpoint; Bei Marke anhalten | the cutscene stops at the same spot by itself |
| 6 | held, open the game's pause screen, close it | sound stays held (TruMenu did not pause it twice); release gives it back |

## TO TEST (0.4)

A checklist the main session (Claude over TruLink) fills while the player plays; the player marks the rows with the controller.

```text
menu test.add level.reload Reload the current unit - Lara at the same spot?   new row (or new hint: state open again)
menu test.add level.load:dlc_level2_start Load DLC 2                          "Run" runs level.load dlc_level2_start
menu test.add look-shadow Shadows at the start look right?                    free key (no item: no Run button)
menu test.mark look-shadow fail dark band at the left wall                    ok | fail | skip | open, optional note
menu test.list                                                                 read the states back
menu test.del <id>      menu test.clear      menu test.clear done                (done = only the marked rows)
```

- **`test.list`** answers one line: `<n> rows (<o> open, <k> ok, <f> fail, <s> skip): <id> [<state>] <hint> {<note>} |
  <id> [<state>] <hint> | ...` (`{note}` only when there is one). Tabs / line breaks in hints and notes become
  spaces, `|` becomes `/`, `{` `}` become `(` `)`, so the answer stays parseable; spaces in an id become `_`.
- **TruLink limits** (TruLink's tokenizer, not TruMenu): a line has at most 24 words, so a hint gets at most 21 words
  (`test.mark` notes 20) - more are cut without a message; runs of spaces become one; a last word `force` is taken
  as TruLink's force flag and dropped; the argument is cut at 511 characters.
- **File** `TruMenu.tests.txt` next to `tru.exe`, rewritten on every change, read at start (survives a restart):
  a `#` comment line, then one line per row `id<TAB>state<TAB>hint<TAB>note<TAB>time` (time = `HH:MM:SS` of the last
  mark). At most 64 rows (0.10.1: 128 - the radial profiles send 77 / 98 rows; also the regression lists); `test.add`
  on a full list answers `err list full`.
- **In the menu** the page "TO TEST" is the first page (open) and is not drawn while the list is empty. A marks the
  selected row OK (also a mouse click), X FAIL, Y SKIP; while a row has the nav focus TruMenu keeps X and Y away from
  ImGui (else X would jump to the title bar layer and Y would activate the row = OK). A mark from the menu keeps the
  note; `TruMenu.log` gets a line `tests: test.mark <id> <state>` for every change (also visible on the Log page).

## TO TEST 0.5: steps, checks, switches

Goal: go through a test **in order** in the game without the chat, and switch features on / off yourself to find the
step or feature that crashes (bisecting) instead of one run per step. Three row kinds:

| Kind | Command | Row id | States | In the menu |
|---|---|---|---|---|
| `check` | `test.add <id> <hint>` (as 0.4) | `<id>` | open / ok / fail / skip | A = OK, X = FAIL, Y = SKIP, buttons, "Run" for `id` / `id:arg` |
| `step` | `test.step <n> <id\|id:arg\|-> <text>` (n = 1..999) | `step<n>` | open / done (not checkable) | "NEXT->" on the first open step; A = run the item (if any) + done; "Run <id arg>" only runs, "Done" / "Open again" only marks |
| `toggle` | `test.toggle <id> <target> <text>` | `<id>` | on / off | a checkbox in "Switches" at the top of the page |

```text
menu test.step 1 - Wait in the main menu                                       step without an item
menu test.step 4 level.load:dlc_level2_start Load the DLC 2 start              "Run level.load dlc_level2_start"
menu test.add d3d-box No D3D error box after the load?                         a check as in 0.4
menu test.toggle sp-states ini:TruShadowPower:States:Enabled States 243/245    INI switch (next start)
menu test.toggle flight cheat.flight Flight cheat on                           item switch: runs cheat.flight 1 / 0
menu test.mark sp-states off      menu test.mark step4 done                    switch / step from TruLink
menu test.export                                                               the whole list as a block
```

- **Order:** a new step goes in front of the first step with a higher number, so steps stay in number order; checks
  and toggles are appended. Sending the rows in the wanted order (step 1, step 2, check, step 3, ...) gives exactly
  that order; `test.step` with an existing number replaces that step (text / item, open again).
- **Toggle targets:** a TruMenu item id (bool items: on = `<id> 1`, off = `<id> 0`, run like a menu click; the state
  shown is the item's value when the row is added: `1` / `on` / `true` = on) or `ini:<Plugin>:<Section>:<Key>` -
  `<Plugin>.ini` next to the `.asi` files, written **at once** with `1` / `0` (`WritePrivateProfileString`). Our
  plugins read their `.ini` only at start, so the row carries the note "INI: takes effect at the next start". The
  plugin name must start with `Tru` (letters / digits), section and key letters / digits / `_`; a missing `.ini` is
  not created (`err ... not found`). INI toggles show the INI value again when the list is loaded at start.
- **`test.mark`** takes the state that fits the kind: checks `ok|fail|skip|open`, steps `done|open`, toggles `on|off`
  (switches the target); a wrong one answers `err <id> is a <kind> row: ...`.
- **`test.export`** answers a TruLink block: `ok+ test.export <n> rows; checks <o> open <k> ok <f> fail <s> skip;
  steps <d>/<t> done; toggles <on>/<t> on (...)`, then one line per row `kind<TAB>id<TAB>state<TAB>number<TAB>target
  <TAB>hint<TAB>note<TAB>time`, then `.`. In `menu list` its value is only the counts line.
- **`test.list`** stays one line; steps / toggles carry their kind: `step4 (step 4 -> level.load:dlc_level2_start)
  [open] ...`, `sp-states (toggle ini:TruShadowPower:States:Enabled) [on] ...`. The header counts (`TO TEST (n
  open, ...)`, `test.list`) count checks only; `test.clear done` removes only marked checks (steps and toggles stay).
- **TruLink limits** as above: `test.step` / `test.toggle` texts get at most 20 words.
- **File:** 0.5 writes three more columns, `id<TAB>state<TAB>hint<TAB>note<TAB>time<TAB>kind<TAB>target<TAB>number`;
  a 0.4 file (5 columns) loads as checks. (0.4 reading a 0.5 file sees steps / toggles as checks with odd states.)
- **Regression runs:** `scripts\windows\Invoke-TruTestRun.ps1 -RunProfile <name>` preloads the rows of
  `tests\profiles\<name>.json` (`test.clear`, then the rows in profile order) and collects `TruMenu.tests.txt`
  after the run ([scripts/windows/README.md](../../../scripts/windows/README.md)).

## Level list (0.2)

Source: the PC unit list the game loads, `tr8/pc-w/unitlist.txt` (119 units; the repository's merged list
`work/generic/merged/tr8/pc-w/unitlist.txt`, byte-identical to the installed `mods/tr8/pc-w/unitlist.txt` on
2026-10-31). `tools/menu_unit_table.py` turns it into the `kUnits` table in `TruMenu.cpp` (re-run it and paste the rows
when the list changes). Groups, all from the list itself:

| Group | Rule | Units |
|---|---|---|
| Base game l1 .. l7 | `levels\...`, by the unit name prefix `l1_` .. `l7_` (the `l7_*` units sit in the folder `levels\l5`) | 23, 16, 9, 11, 6, 6, 13 |
| DLC 1 | `dlc\dlc_level1\...` | 12 |
| DLC 2 | `dlc\dlc_level2\...` | 11 |
| DLC other starts | `dlc\dlc_level3..6\dlc_levelN_start` | 4 |

Not offered (not playable units): `container\*`, `dlc\container\*`, `dlc\dlc_costume_containers\*`, `imf\*`,
`special\cinefx`. Chapter / location titles ("Mediterranean Sea" ...) are **not** shown: they are not in the unit list
and were not verified against the game's text data (TRLAU-menu-hook has such names; not taken).

## Outfits (0.2)

All addresses read from the PC `tru.exe` with `tools/pe_dis.py` / `pe_callers.py` / `player_type_table.py` and
checked against the expected bytes at load (`costume` / `unit table` on the Status page).

| Fact | PC address | Notes |
|---|---|---|
| game data pointer | `[0x00c59264]` | re-allocated by the new-game reset tru+0x156940 - read fresh every time |
| level load: chosen costume | tru+0x1de2d6 in `GAMELOOP_LevelLoadAndInit` tru+0x1de2b0 | `u16 +0x1f4 == 0 ? +0x20c : +0x210` (as retail Xbox 0x8229b3f0); if non-zero and accepted by the validator the name is `[0xdb94d0][id*8]`; in `l1_seatop` (string 0x85539c) it takes `lara_wetsuit_warm` instead; a name in byte buffer `0x0084216c` (empty) overrides all; else the unit default `[[unit+8]+0x70]+0x294` |
| costume validator | `0x005c54e0` bool cdecl(id) | id <= object count, then tru+0x1bf7b0(name) (`<name>.drm` present) |
| current costume | `[0x00e7f1c8]` | object id written by the level load (= the player object) |
| object names | `[0x00db94d0]` | +0 count, name of id n at +n*8; name -> id tru+0x1bf770 |
| type table | operand of tru+0x1bf121 (orig. `0x008aba28`, 0x1c per record) | the Outfits list = records whose f2 is the player's `0x007228e0` (36 on PC: records 0-11 and 15-38; 37 with TruDlc2Player's `doppelganger_casual`); index = record index |
| state save | tru+0x155cb1 | `word [gd+0x20c] = word [0xe7f1c8]` - the game's own write of the field |
| new-game reset | tru+0x156abe .. 0x156ad7 (PC partner of TU 0x821fe9a8) | `+0x210 = +0x20e = +0x20c = 0`, then `+0x228 / +0x226 / +0x224 = 100` |
| unit default | stream unit table `0x00dbab40` (0xd8 per unit, +0 id, +4 state 2, +8 data), unit id `[0x00e7f148]` | tru+0x1c1b50, read at tru+0x1de379 |

- `costume.set <index|name> [20c|210]` (game thread): record must be a player record and in the object list; the
  game's validator 0x5c54e0 must accept it; then **u16 object id -> game data + 0x20c** (or **+0x210** while
  `+0x1f4 != 0`; the optional slot argument forces one). Takes effect at the next level load. `costume.setreload` also
  reloads the current unit (`level.reload`).
- `costume.reset` (game thread): **+0x210, +0x20e, +0x20c = 0** in the current game data - only those three words of
  the reset; the next level load takes the unit default (`dlc_level2_start`: 11 `lara_doppelganger`, which
  TruDlc2Player turns into `doppelganger_casual`).
- The costume-selection screen's own write was **not** located: no other code writes `+0x20c` / `+0x210` by
  displacement; the scripts set costumes through `uigamedata` natives (e.g. stub 0x7a0d79 -> 0x77bd50 ->
  tru+0x1d9f40 `[0xe7f1c8] = id(name)` + costume load request tru+0x1c1760 - an immediate load, not the chosen
  field). The loading-screen script (generalbank script 6, function 5) names the base costumes `lara_casual`,
  `lara_bikini`, `lara_jungle_heavy`, `lara_jungle_a`, `lara_jungle_b`, `lara_snow_light`, `lara_snow_heavy`,
  `lara_wetsuit_cold`, `lara_wetsuit_warm` and the DLC costumes `dlc_costume_a..p`, `dlc_doppel_costume_a..d`.
- Display names (localised outfit titles) are not shown; the list shows object names.

## Developer menu (original) (0.3)

Crystal Dynamics' debug menu **data** is still in the retail `.data` (0x8aaa6c .. 0x8ab3f0); the driver that drew it
is gone (the root page 0x8aaae8 is referenced only from the tables and from the lone dword 0x8aaa9c). TruMenu reads
the rows at load (`DevRead`, check: the root row must be `{0x0b, 0, 0, 0x855070, 0x8aaa6c, 0}` with the label
"This should not be the Options Title") and draws them as their types say - labels, targets, limits, masks and
callbacks all come from the table. `tools/devmenu_dump.py` lists the same rows statically (with the retail code that
reads each target) - re-run it for this table:

```text
../bin/pyt -t 300 tools/devmenu_dump.py <tru.exe>          pages, rows, readers
../bin/pyt -t 300 tools/devmenu_dump.py <tru.exe> --md     Markdown table
../bin/pyt -t 300 tools/devmenu_dump.py <tru.exe> --raw    plain rows
```

**Row format** (0x18 bytes = 6 dwords): `+0 type`, `+4 min` (int) / argument (action), `+8 max` (int), `+0xC label`
(`char*`), `+0x10 target` (variable, function or page), `+0x14 mask` (flag) / value (bool) / callback (int).

| Type | Meaning | TruMenu |
|---|---|---|
| 0x00 flag | bit(s) `mask` of the dword at `target` | checkbox, read-modify-write of the dword |
| 0x02 bool | byte at `target`, `+0x14` = 0xffffffff (the value for "on") | checkbox, writes 0xff / 0 (all three targets are in `.rdata`: written with `VirtualProtect`) |
| 0x03 int | s32 at `target`, range `[+4, +8]`, optional callback `+0x14` called after a change | slider (range <= 255) or input with step; clamps; callback cdecl with argument 0 (as the game's own caller 0x5d3760 calls 0x5d36a0) |
| 0x09 action | cdecl function `target`, `+4` = its argument (only the Chapter rows have one: `"chapterN"`) | button; empty functions (`ret` / `jmp` to `ret`) are marked "empty in retail" |
| 0x0A page link | `target` = first row of a page | button that switches the page |
| 0x0B title | page title, `target` = parent page (root: the empty page 0x8aaa6c) | heading |
| 0x10 end | end of a page (label "", target 0xe7f098 in every end row) | - |
| 0x11 header | page header with a text layout string (`"-abs 160 40 -center"`), followed by empty 0x10 slots | note (5 such pages, all empty in retail) |

**Count (2026-10-31, Steam `tru.exe`): 101 rows in 15 pages** - 22 actions, 10 flags, 7 ints, 3 bools, 9 page links,
2 titles, 5 headers, 43 end rows; **42 value / action rows** with an id `dev.<slug of the label>` (lower case, every
run of other characters = `_`, e.g. `dev.show_spline_info`, `dev.fog_far`, `dev.perfect_game_now`,
`dev.chapter_1`). The retail root only links "Units" (with "Reload Current Unit") and the "Chapters" action; the
other pages are reachable through "All pages" in the menu.

| Row | Id | Type / target | Static facts (`devmenu_dump.py`; effect in retail not verified live) |
|---|---|---|---|
| 0x8aaab8 | `dev.reload_current_unit` | action 0x5dfba0 | if `[0xe7f141]` == 0 { if streamFlags & 0x200000: 0x5570f0(0); 0x5df760(4) }; `[0xe7f143]` = 0 |
| 0x8aab00 | `dev.keep_info_between_loads` | flag streamFlags 0xe7f0b8 & 0x200000 | live: read by 0x5dfba0 and ~20 other sites |
| 0x8aab30 | `dev.chapters` | action 0x5d37b0 | `jmp 0x6457a0` (empty): compiled out |
| 0x8aab78 | `dev.save_current_game` | action 0x6457a0 | empty function: compiled out |
| 0x8aab90 | `dev.restore_game` | action 0x555d40 | streamFlags \|= 0x200000 only |
| 0x8aabd8 | `dev.show_spline_info` | flag 0xe7f09c & 0x400000 | readers with this mask: 0x5cf331, 0x5cf434, 0x5cf57b |
| 0x8aabf0 | `dev.enable_keypad` | flag 0xe7edb4 & 1 | no reader found |
| 0x8aac38 / 50 | `dev.fog_far` / `dev.fog_near` | int 0x8aaa60 / 0x8aaa64, -1 .. 0x9400, callback 0x5d36a0 | callback writes the current unit's fog (unit +0x94 / +0x98 / +0xa0..a3) and calls 0x5bfe10 / 0x5bfe40; **needs a level** |
| 0x8aac68 / 80 / 98 | `dev.fog_red` / `green` / `blue` | int 0xe7eda0 / a4 / a8, 0 .. 255, callback 0x5d36a0 | as above |
| 0x8aacb0 | `dev.restore_fog` | action 0x5d3760 | unit fog defaults (0xe7b8a0 / 0xe7ecdc) back, then 0x5d36a0(0) |
| 0x8aacf8 | `dev.projected_shadows` | flag 0x8aaa54 & 1 | written once at init (0x5df56d = 1), no reader found |
| 0x8aad10 | `dev.show_input_actions` | flag 0xa02b80 & 1 | no reader found |
| 0x8aad28 | `dev.frame_rate_lock` | int 0xe7f1a8, 0 .. 3 | live: read at 0x5da2e9 |
| 0x8aad40 | `dev.time_mult` | int 0xe7f1a4, 0 .. 0x4000 | live: init 0x1000 (0x5d3d44), read at 0x5da380 |
| 0x8aad58 | `dev.ignore_object_scripts` | bool 0x8550c0 (`.rdata`) | no reader |
| 0x8aad70 / 88 / b8 | `dev.vv_stats` / `dev.show_music_vars` / `dev.enable_screenshot` | flag 0xe7f098 & 0x2000000 / 0x10000000 / 0x4000 | debugFlags is tested with a register mask (0x5dfd7b ...): unresolved |
| 0x8aada0 | `dev.show_monster_music_vars` | flag 0xe7f0a0 & 0x1000000 | no reader with this mask found |
| 0x8aadd0 | `dev.perfect_game_now` | action 0x5d3510 | `[0xe7f0b4]` \|= 0x100 (GameTracker+0x2c) - progress bit, TruMenu cannot undo it |
| 0x8aae18 | `dev.ui_trigger_all_fade_groups` | action 0x5d7590 | calls `[0x8ab79c](float [0x8416b4])` |
| 0x8aae30 | `dev.ui_make_hints_modal` | flag 0xe7f0a4 & 0x200000 | no reader with this mask found |
| 0x8aae48 / 0x8aaf38 | `dev.unlock_all_unlockables` / `dev.skip_all_puppet_shows` | bool 0x8550c2 / 0x8550c1 (`.rdata`) | no reader |
| 0x8ab280 .. 0x8ab3d0 | `dev.chapter_1` .. `dev.chapter_15` | action 0x6457a0("chapterN") | empty function: compiled out |

Guards: every row needs `[Cheat] Experimental=1`; ints with a callback and non-empty actions need a level (the fog
callback dereferences the current stream unit); everything runs inside `__try` (an exception is reported and counted
on the Debug / Log page). Over TruLink: `menu dev.list`, `menu dev.fog_far 9000`, `menu dev.show_spline_info 1`,
`menu dev.time_mult` (no argument = current value and range).

## 0.3 items: facts

Every address is checked at load against an instruction of the game that uses it (Status page line "0.3: ...",
`TruMenu.log` "0.3 checks"). Sources: catalog `docs/Menue-Funktionen-Katalog.md` (TRLAU facts with file / line) and
our own disassembly with `tools/pe_dis.py` / `pe_callers.py` on 2026-10-31.

| Item(s) | Fact | Check at load |
|---|---|---|
| `time.scale` | float timeDilation 0xe7f1d0 (GameTracker+0x148, TRLAU), 0..10 | init `fst [0xe7f1d0]` 0x5d3d25, reader 0x5da3a0 |
| `time.pause` | streamFlags 0xe7f0b8 bit 0x1000 (TRLAU F3) | 0x555d40 `or dword [0xe7f0b8], 0x200000` |
| `player.control` | byte 0x8ab4e6, 1 = on (TRLAU) | 0x5d5f45 / 0x5d5f60 (`mov byte [0x8ab4e6], 1 / 0`) |
| `player.die` | INSTANCE_Post(player, 4, 3) (TRLAU F11) | INSTANCE_Post prologue (0.1) |
| `ui.hide` | bool 0xcdc9a0 (TRLAU) | `cmp byte [0xcdc9a0], 0` at 0x5a434c |
| `camera.fov` | float current camera `[0xe80534]` + 0xb0 (TRLAU) | none in code; refuses unless the field already holds 0.05 .. 3.1 |
| `instance.*`, `player.goto` | first instance `[0xd98d54]`, next +0x08; +0x10 object (+0x14 object id), +0x20 position, +0x30 rotation, +0x58 intro id, +0x14 iflags, +0x23c no-draw groups (TRLAU); unhide = message 7, 0 (TRLAU) | `mov [0xd98d54], ecx` 0x5b2ec6 and the game's own walk at 0x5d467d (`esi = [0xd98d54] ... esi = [esi+8]`) |
| `instance.remove` | INSTANCE_ReallyRemoveInstance 0x5bc4e0 cdecl (inst, 0, 0) (TRLAU); refused for the player | prologue |
| `costume.next` / `costume.set` | the game's switch **0x6f0a90** (reached from the costume native 0x79db50 -> 0x778ca0, which sets altPlayerObjectID 0xe7f1cc from its table first): if `[0xe7f1cc]` != 0 it becomes the current costume, else the id after the player's object id in GlobalInfo `[0xe7ee50]+4` `{u16 count; u16 *ids at +4}`; then INSTANCE_Post(player, 35, 0) two game frames later (TRLAU: weapons). TruMenu sets `[0xe7f1cc]` itself (0 = next) and calls 0x6f0a90; `costume.set` checks the id with the game's validator 0x5c54e0 | 0x6f0a90, 0x778ca0, 0x79db50 prologues, `mov edx, [0xe7ee50]; mov edi, [edx+4]` at 0x6f0ac7 |
| `log.script` | the 8 NsCoreBase print / log natives (registered as natives 0..7 at 0x7b3920 .. 0x7b399e, cdecl `(instance, numArgs, DataValue *args)`, 4 bytes per argument): 0x795d30 print int, 0x795d50 bool, 0x795d80 float, 0x795db0 string (args: value, float time, bool newline) and 0x795dd0 / 0x795df0 / 0x795e10 / 0x795e30 log int / bool / float / string (value, newline). In retail they end in empty functions (0x574be0 `ret 0xc`, 0x7987b0 `ret 8`) or in sprintf into a dropped stack buffer (0x4a3200 .. 0x4a32c0). TruMenu writes a 5-byte `jmp` to its handlers over their first bytes while `log.script` is on (restored when off); a string argument is read as `char*` or pointer to one (not verified) | registration bytes at 0x7b3990 + the first bytes of all 8 |
| `media.video.*` | player 0x4a12b0 cdecl (name, bool loop) (catalog 11.1), only when main state `[0xe7ed60]` = 10 (TRLAU: main menu); menu background name pointer `[0x8abf20]` = "medsea_loop" 0x8552a8, read at 0x5daf35 | prologue, 0x5d56e0 reader, 0x5daf35 bytes + `[0x8abf20]` == 0x8552a8 |
| `draw.markup` / `draw.ledges` | MarkupManager `[0xdb94cc]` (vtable object); the walk 0x5c3ce0 (called with `ecx = [0xdb94cc]` at 0x5d3349): box = `[mgr+0x14]`, next `[box+4]`, `+0x20` MarkUp, `+0x28` flags; MarkUp `+0x34` position, `+0x58` poly line `{int count; points at +0x10 + 16*i}` (all moved by the world shift there = world space). Projection as TRANS_RotTransPersVectorf 0x49f630: `view = M * p`, M = 4 columns of 16 bytes at 0xa038f0; `x' = x / z * f + 256`, `y' = y / z * f + 224`, f = float `[0x8906d0]` (512.0 in the file), centre doubles 0x843a00 / 0x8454c8; drawn when z > 16 (TRLAU). The **512 x 448 screen space** is our reading of those constants and is scaled to the back buffer (`draw.scale`) - to verify live. Colour per flag bit with the catalog's (TRLAU) names, not verified for box +0x28 | 0x5c3ce8, 0x5c3d1e, 0x5c3d54, 0x5c3da2, 0x5d3349, 0x49f64e / 67f / 6f8 / 702 / 713 |
| `weapon.give` | WM::GiveWeaponByName 0x7161f0 thiscall `ecx = [[0xfadb58]+0x500]`, `(name, 1, 0)` (catalog 17.1: the default loadout's call; blocks while the object streams in) - only when main state = 1 | prologue |
| `ammo.*` | reserve u16 `playerstate+0x51c+2*type`, 6 types (catalog 17.2) | HUD reader `movzx eax, word [ecx+edx*2+0x51c]` 0x6e8475 |
| `player.health` / `player.invincible` | float `playerstate+0x628` (GetHealth 0x6e7860); MaxHealth 0x6e7990 `() -> float`; invincible = variant A of catalog 17.5 (health = MaxHealth once per game frame in PadHook; state deaths such as falls still kill) | 0x6e7860 and 0x6e7990 prologues |
| Debug / Log | `Tru*.log` in the `.asi` folder and the `tru.exe` folder, read with `FILE_SHARE_READ \| WRITE \| DELETE`, only the new bytes (at most the last ~6 KB per second, 2 KB at first sight); ring of 512 lines; per frame only a copy of the shown lines | - |

## 0.4 items: facts

Sources: catalog `docs/Menue-Funktionen-Katalog.md` section 17 and our disassembly with `tools/pe_dis.py` on
2026-10-31 (Steam `tru.exe`); every address checked at load (Status page line "0.4: ...", `TruMenu.log` "0.4
checks"). Not yet run in the game.

| Item(s) | Fact | Check at load |
|---|---|---|
| `weapon.slots`, `weapon.has` | weapon manager `WM = [[0xfadb58]+0x500]`; 15 slots, right hand handle `{instance, id}` at `WM+4+0x10*slot`, left hand at `WM+0xc+0x10*slot` (reader 0x6e7b90: `cmp esi, 0xe`, `[esi+edi+4/8]`, `[esi+edi+0xc/0x10]`); a handle is valid when `[instance+0x44] == id` (the game's check 0x5b39d0 - TruMenu repeats it with its own reads instead of calling it); object name `[[instance+0x10]+0x60]` (as the gear callback reads it at 0x715ea2); selected slot `WM+0x138` | 0x5b39d0 bytes, 0x6e7b98 / 0x6e7bb9 / 0x6e7bde |
| `ammo.fill` | for type 0..5: `reserve[type]` (u16 `playerstate+0x51c+2*type`) = *MaxAmmo* 0x6eeae0 cdecl `(s8 type) -> u16` (6-entry jump table, `0xffff` for other types; reads the player's object data `[[0xe7f094]+0x50]`, so a level is needed); the clips are **not** refilled (0x6e7ae0 not used) | 0x6eeae0 prologue + jump, 0x6eec67 `or ax, 0xffff; ret` |
| `gear.give` | *GiveObject* 0x555f60 cdecl `(owner = player instance, objectId, callback 0x715e90, flag 1)`: an existing instance of the object (0x5b3950) goes to the callback at once, else 0x5550a0 loads / births it first; the callback with flag 1 calls *WM::AddGear* (catalog 17.1 step 5). Main state 1 only | 0x555f60 and 0x715e90 bytes, 0x715eb2 `mov eax, [0xfadb58]; mov ecx, [eax+0x500]` |
| Log collapse / filters | in `PushLine`: a leading `[YYYY-MM-DD ]HH:MM:SS[.mmm] ` is the time stamp (0.22.30: the date is optional and not shown); the newest line of the same source with the same text is counted and moved to the head; TruLink lines `> read* / scan* / watch* / ping` and `[>] menu <id>` with an info item (or `status.*`, `list`) are dropped when `HideLinkReads=1`; severity by words (errors: fail, error, exception, ` NO `, `err `, crash; warnings: warn, not match, mismatch, busy, refused, unreadable, timeout, missing, skipped, not verified); rate limit counted per source and second, the dropped count is written as one line when the second is over | - |
| `camera.free` | **still todo**: the free camera needs the offsets of the camera's `transform` / `invTransform` and the per-frame rebuild (catalog section 9). Found on 2026-10-31 only a lead: 0x5edb50 writes a matrix at 0xe8ee30 (via 0x431e10) and its inverse at 0xe8ee70 (`0x49be10(0xe8ee70, src)`), i.e. inverse = transform + 0x40 for that camera object; which camera / base it is and whether mode 11 keeps the game from overwriting it is **not verified** | - |

## Hooks

Every address below is checked against the expected bytes at load (`Start()`); on a mismatch that part stays off,
the reason goes to `TruMenu.log` and the Status page shows `NO`. Nothing is patched in the game code itself - with one
opt-in exception since 0.3: `log.script` writes a 5-byte `jmp` over the start of the 8 script print / log natives
(restored when it is turned off; see "0.3 items: facts"). Import slots: `GetProcAddress` (pad, since 0.1) and, 0.7,
only while the menu is open, `SetCursorPos` / `ClipCursor` (see "Controller and mouse (0.7)").

### Pad: import filter on `GetProcAddress`

The game loads XInput itself: tru+0x824f0 calls `LoadLibraryW(L"xinput9_1_0.dll")`, then `GetProcAddress` through
its import slot **0x0083e08c** and stores `XInputGetState` in **0x00a02b8c** - the pointer the per-frame pad poll at
tru+0x84b82 (`call dword ptr [0x00a02b8c]`) calls. The same import slot serves the `Direct3DCreate9` lookup at
tru+0x1239e6. At load TruMenu replaces the slot (it is filled long before the game reaches its XInput setup) with a
filter that passes every lookup through and hands out **PadHook** for `"XInputGetState"` only. So the game itself writes
PadHook into 0x00a02b8c.

**Chaining with TruShadowPower / TruLink.** These plugins wait until 0x00a02b8c is non-zero and then wrap whatever it
holds. Because the game writes PadHook there, they always wrap TruMenu, whatever order the ASI loader loads the
plugins in: `game -> TruShadowPower / TruLink -> PadHook -> XInputGetState`. PadHook neutralises the pad *before*
the outer hooks see it, so the shadow power and TruLink's frame hook get the neutral pad while the menu is open.
TruMenu follows the project's chaining rule (shared with TruShadowPower 0.5.1 and TruLink):

1. hook once;
2. re-hook only when the slot points into the real `XInputGetState` again (address inside a module whose name starts
   with `xinput`) - never because the slot is "not mine";
3. a thread-local re-entry guard: if PadHook is entered again on the same thread (another wrapper that wrapped
   PadHook and is also called by it), the inner call goes straight to the real `XInputGetState`.

Late load (the pointer is already filled when TruMenu starts): PadHook is placed on top of whatever the slot holds,
once (compare-exchange); rule 3 keeps an older plugin that re-wraps everything (TruShadowPower 0.5) from recursing.
If even that swap fails, the menu reads the pad itself and **cannot block** the game's input (Status page says so).

Mixed versions: TruShadowPower **0.5** (re-wraps whenever the slot is not its own) together with TruLink can make
TruLink cut the loop by calling the real `XInputGetState` directly - PadHook is then no longer called. TruMenu notices
that (no PadHook call for 250 ms) and reads the pad in Present, so the menu still opens, but input is not blocked.
Use TruShadowPower **0.5.1** or later (same chaining rule) with TruLink + TruMenu.

Observed since 2026-11-06 (TruMenu.log, `Befund-TruShadowPower-017-0611.md`, `Befund-Padkette-StartView-0711.md`): the
import filter never handed out PadHook - the slot is rewritten to KERNEL32's GetProcAddress after the filter - so
PadHook is always placed late and the order of the three hooks depends on load timing. TruLink's same-thread re-entry
breaker also fires when an item run inside PadHook polls the pad while TruLink sits outside PadHook; since 0.21.2 such
items run in the Present hook (section "TruMenu 0.21.2").

**Front end.** If PadHook has not been called for 250 ms (main menu, loading - the game may not poll the slot
there), the Present hook reads the pad itself (`XInputGetState` of the loaded xinput module, pad index of the last
active pad) for the L3 + R3 toggle and the menu navigation, and runs queued items there. Input is not blocked then.

### Direct3D 9: device vtable

The device manager is created at tru+0x1239c0 and stored in **[0x00ad75e4]**; its `IDirect3DDevice9*` is the
`ppReturnedDeviceInterface` of the CreateDevice call at tru+0x122736, i.e. **manager+0x20** (`lea ebp,[esi+0x20]`
at tru+0x12270a; manager+0x208 holds the present parameters - 0.1 used it by mistake, fixed in 0.1.3). Since 0.1.3
the implicit swap chain's `Present` (slot 3) is hooked as well - the game presents through it. A worker thread polls that pointer (50 ms until found, then every second for a new device) and
patches the device's own vtable entries **Reset (16)** and **Present (17)** (`VirtualProtect`, original saved before
the swap). This is independent of who provides `d3d9.dll`: with TRAWindowed's proxy in the game folder the vtable
patched is the one of the object the game calls (the proxy's or the system one), and other overlays that hook later
chain on top. `d3d9.dll` is never replaced, `Direct3DCreate9` is not hooked.

- Present: when the menu or the overlay is visible, `BeginScene` -> ImGui frame -> `EndScene`, then the original
  Present. With nothing to show it only checks the keyboard toggle and the front-end pad read.
- Reset: `ImGui_ImplDX9_InvalidateDeviceObjects` before the original; the next frame re-creates them.
- ImGui is created on the first frame that shows something; window = the device's focus window (or the swap chain's
  device window); its window procedure is chained (`SetWindowLongPtr`) and forwards messages to ImGui only while the
  menu is open. `imgui.ini` is not written (`IniFilename = nullptr`).

### Game functions (experimental, `[Cheat] Experimental=1`)

| Use | Address | Check | Source of the fact |
|---|---|---|---|
| player instance | `[0xe7f094]` = GameTracker 0xe7f088 + 0xc | reader at 0x741764 | TRLAU `Game.h`, TruShadowPower |
| position / rotation | instance +0x20 / +0x30 (16-byte vectors) | - | TRLAU `Instance.h`, `cdc/math/Vector.h` |
| cheatMode | byte 0xe7f144 (GameTracker+0xbc) | - | TRLAU `Game.h`, `modules/Skew.cpp` |
| INSTANCE_Post(instance, msg, data) | 0x5b3750, cdecl | prologue bytes | TRLAU `instance/Instance.cpp`; message 12 = flight from `Skew.cpp` |
| CAMERA_SetMode(mode) | 0x5f39f0, cdecl | prologue bytes | TRLAU `game/Camera.cpp`, docs `Befund-Entwicklerkanal.md` |
| camera restore | 0x5edf50, thiscall CameraManager 0xe804f0 | prologue bytes | TRLAU `modules/camera/Underworld.cpp` |
| GAMELOOP_RequestLevelChangeByName(name, gameTracker, doneType) | 0x5df8c0, cdecl, doneType 4 | prologue + name copy to GameTracker+0x38 | name / signature TRLAU `game/Game.cpp`; doneType 4 and the reload of GameTracker+0x38 from the game's own callers tru+0x1dfb73 / tru+0x3744b3 |
| frame time | float 0xe7f190 (30 fps units) | store at 0x5da40c | TruShadowPower |

The level change is refused while `GameTracker+0xb9` is set (the function itself ignores requests then) and for names
with characters other than `a-z 0-9 _ -` or longer than 63 characters; the menu closes after a request.

## Options (`TruMenu.ini` next to the `.asi`, optional)

Since 0.3 every key, its default and its comment live in **one table** (`kOpts` in `TruMenu.cpp`): a missing key
takes the table's default, `settings.reset` writes the file from that table, and the shipped `TruMenu.ini` is that
exact text - `../bin/pyt -t 60 tools/trumenu_ini_check.py` checks it (`--print` shows the generated text). Change a
default or comment only in the table, then copy `--print` into `TruMenu.ini`.

| Section / key | Default | Meaning |
|---|---|---|
| `[Menu] Enabled` | 0 (0.22.18; was 1) | 0.22.18: 1 = the big menu window may open (ToggleButtons / ToggleKey), 0 = never - the bar, ring and items work. Before 0.22.18: 0 = load but hook nothing. 0.22.44: in an INI without `[Menu] Load` (written before 0.22.18) Enabled never opens the window - add `Load=1` for that |
| `[Menu] Load` | 1 | 0.22.18: 0 = load but hook nothing (the old meaning of `[Menu] Enabled=0`) |
| `[Menu] LogLevel` | 1 | 0 errors, 1 info, 2 every toggle / item, 3 debug; `TruMenu.log` next to `tru.exe` |
| `[Menu] ToggleButtons` | 192 (0x00C0) | XInput button mask that opens / closes the menu (all buttons of the mask together) |
| `[Menu] ToggleKey` | 0 | virtual key that also toggles the menu (0 = off) |
| `[Menu] Scale` | 1.5 | font and spacing scale (0.5 .. 4) |
| `[Menu] Overlay` | 0 | 1 = position overlay on from the start |
| `[Menu] FreeMouse` | 1 | 0.7: while the menu is open the mouse belongs to the menu (cursor drawn, no mouse messages to the game, its `SetCursorPos` / `ClipCursor` held until close); 0 = as 0.6 |
| `[Menu] BlockGameInput` | 1 | 0.7.1: while the menu is open the game gets no keyboard (its DirectInput keyboard reads no key events, a key it saw going down is released once, a key held at the close stays away until released; key messages to the menu only); 0 = as 0.7 |
| `[Menu] PauseGame` | 0 | 0.7.1: 1 = also set the `time.pause` bit while the menu is open; on close only what TruMenu set is cleared |
| `[Menu] RememberPage` | 1 | 0.22.19: 1 = the big window opens with the pages that were open last time (`OpenPages`), also after a restart; 0 = the built-in pages (TO TEST, Quick access) |
| `[Menu] OpenPages` | `totest,quick` | 0.22.19: keys of the open pages (comma list, rewritten when a page is opened / closed; keys in the start line `menu pages`); unknown keys dropped, only unknown = the built-in pages |
| `[Menu] NoAttract` | 0 | 0.22.20 (`menu.noattract`): 1 = no teaser video (attract mode) after the idle time in the main menu - the AttractTimer clock is held at 0 in the front end, the background stays; 0 = the game's teaser |
| `[Menu] AttractTimerShow` | 0 | 0.22.21 (`menu.attracttimer`): 1 = a line in a screen corner while in the main menu (front end) shows the teaser timer - elapsed / alarm, while `NoAttract` holds a shadow count that flashes 1 s (and writes a log line) when the teaser would have started; read only; 0 = no line |
| `[Menu] AttractTimerPosition` | `tr` | 0.22.21: corner of the teaser timer line - `tl`, `tr`, `bl`, `br`; anything else = `tr` |
| `[Quick] RememberPage` | 1 | 0.22.19: 1 = the bar opens on the page it showed last (`LastPage`), also after a restart; 0 = always page Level data |
| `[Quick] LastPage` | (empty) | 0.22.19: English name of the last bar page (rewritten 1 s after a page change and at the close); empty = Level data, a name that is no page any more = page 1, logged |
| `[Pad] BlockInput` | 1 | 0 = the game sees the pad while the menu is open |
| `[Cheat] Experimental` | 1 | 0 = no game-changing actions (pages read-only) |
| `[Cheat] FlightSpeed` | 20 | units per 30 fps frame at full trigger |
| `[Cheat] FlightHint` | 1 | 0.21.6: 1 = while flight is on and the menu is closed one line bottom right names the keys (RT up, LT down, stick moves, the speed); 0 = no line |
| `[Cheats] Enabled` | 1 | 0.8: 1 = the Cheats page can switch (also needs `[Cheat] Experimental=1`); 0 = list only |
| `[Cheats] Persist` | 0 | 0.8: 0 = every cheat off at each game start; 1 = the ids that are on are kept in `State` and switched on again in the first level of the next start |
| `[Cheats] State` | (empty) | 0.8: written by TruMenu when `Persist=1` (comma list of cheat ids) |
| `[Levels] List` | `dlc_level1_start,dlc_level2_start` | units offered as buttons on the Level select page |
| `[Levels] OutfitRule` | 1 | 0.7.2: `level.start` as the title update's mission menu - `dlc_level2_start` (and `dlc_level4..6_start`) without the outfit / weapon selection, other units with it; 0 = PC script 104 (always with the selection) |
| `[Favorites] Ids` | (empty = default list) | favourite item ids, comma list; rewritten by TruMenu when you pin / unpin (`WritePrivateProfileString` on this file) |
| `[Cmd] Enabled` | 1 | 0.6: 1 = command bar under the menu window (0 = no bar; `cmd.run` still works, `cmd.focus` answers `err`) |
| `[Cmd] HistorySize` | 32 | 0.6: lines kept in `TruMenu.history.txt` next to `tru.exe`, 1 .. 64 |
| `[Cmd] FocusButton` | 64 (0x0040 L3) | 0.7: XInput button (pressed and released alone, menu open) = focus into the bar + on-screen keyboard; 0 = off |
| `[Cmd] Keyboard` | 1 | 0.7: on-screen keyboard when the bar gets the focus by controller; 0 = L3 / A only focus the text field |
| `[Cmd] UpOpensHistory` | 1 | 0.7: 1 = Up in the empty bar = history; 0 = Up into the menu like Down (Ctrl + Up = history) |
| `[Cmd] FirstPadPressOnlyFocuses` | 1 | 0.7: 1 = the first D-pad / stick press in the bar only focuses the menu; 0 = it also moves there |
| `[Log] Overlay` | 0 | 1 = log lines in the bottom-left corner from the start |
| `[Log] Lines` | 12 | lines on the Debug / Log page and in the overlay (1 .. 64) |
| `[Log] Script` | 0 | 1 = redirect the 8 script print / log natives from the start (patched at load, before any script runs; needs `Experimental=1`) |
| `[Log] Collapse` | 1 | 0.4: repeated lines (same source, same text after the time stamp) become one line `text x42 (first-last)` (`log.collapse`) |
| `[Log] HideLinkReads` | 1 | 0.4: drop TruLink's echo of `read*` / `scan*` / `watch*` / `ping` and its `menu` lines for info items (`status.*`, `test.list`, ...) (`log.hidereads`) |
| `[Log] MinLevel` | 0 | 0.4: 0 all lines, 1 warnings + errors, 2 errors only (`log.level`) |
| `[Log] MaxLinesPerSecond` | 40 | 0.4: new lines per source and second, more are dropped and counted; 0 = no limit (`log.rate`) |
| `[Log] UnitChanges` | 1 | 0.7.1: a line `unit: <name> (was <name>; stream unit id N)` in `TruMenu.log` (log page / overlay) when Lara moves into another stream unit |
| `[Log] OverlaySources` | `TruMenu,TruGuard` | 0.7.2: sources the corner overlay shows (log names without `.log`, plus `script`); `*` or empty = all; overlay only (`log.overlaysources`) |
| `[Log] OverlayExclude` | (empty) | 0.7.2: overlay only - lines holding one of these texts (comma list) are not shown (`log.overlayexclude`; `none` = off) |
| `[Log] CameraChanges` | 1 | 0.8: `camera: mode A -> B` / `camera: object ...` lines when the camera manager's mode (manager+0x58) or current camera changes (read-only poll, 200 ms; `camera.log`) |
| `[Log] InputTrace` | 1 | 0.8.1: with `[Menu] LogLevel=2` one `input: ...` line per pad button edge / mouse click / key while the menu is open, with the source and what the menu did (focus, activated or why not); 0 = only the summary line at each close (`log.inputtrace`) |
| `[Test] AutoStart` | (empty = off) | 0.7.1, test only: `dlc2` / `dlc1` / a unit name - once per game start, when the main menu is up, `level.start` (mission menu path, intro plays); without the verified path `level.load` + log line "intro skipped" |
| `[Test] AutoStartDelay` | 3 | 0.7.1: seconds the main menu must be up before AutoStart starts, 1 .. 60 |
| `[Regress] List` | `all` | 0.8: list the Regression page shows at start: `dlc1`, `dlc2` or `all` |
| `[Media] MusicInLevels` | 0 | 0.9: 1 = `media.music.play` / `stop` also in a level; 0 = main menu only (until a live test proves it safe) |
| `[Media] MusicFade` | 60 | 0.9: fade in / out frames (30 per second) of `media.music.play` / `stop`, 0 .. 300 (the game's unit start uses 60) |
| `[Saves] Folder` | (empty) | 0.9: save folder of the Saves page; empty = the game's own (Documents\Eidos\Tomb Raider - Underworld) |
| `[Radial] Enabled` | 1 | 0.10: radial menu on; 0 = TruMenu exactly as 0.9 (L3 + R3 toggles at the press, F9 reaches the game) |
| `[Radial] HoldButtons` | `0x00C0` | 0.10: pad buttons held for the ring (hex or decimal; L3 + R3); 0 = no pad hold. Same mask as `[Menu] ToggleButtons` = short press menu (at the release), held = ring; another mask = watched on its own |
| `[Radial] HoldMs` | 500 | 0.10: hold time in ms, 100 .. 3000 |
| `[Radial] Key` | `0x78` | 0.10: virtual key held for the ring (F9; Steam Controller back button -> F9 in Steam Input); kept from the game (DirectInput event + key messages); 0 = off |
| `[Radial] MouseButton` | 0 | 0.10: 3 = middle, 4 / 5 = side buttons held = ring (mouse direction picks); 0 = off |
| `[Radial] RememberPosition` | 1 | 0.10: the ring opens at the level / page / pick of its last close; 0 = always at the top |
| `[Radial] PassLeftStick` | 1 | 0.10: the left stick reaches the game while the ring is open (Lara walks); 0 = neutral pad |
| `[Radial] SlowMotion` | 0 | 0.10: `time.scale` while the ring is open (e.g. 0.25), the old value comes back at the close (unless an entry changed it); 0 = off |
| `[Radial] Deadzone` | 0.5 | 0.10: stick deflection that picks a sector, 0.2 .. 0.95 (mouse: 30 px x Scale at 0.5) |
| `[Radial] Scale` | 1.0 | 0.10: ring size relative to the back-buffer height, 0.5 .. 2 |
| `[Radial] Spawn` | 0 | 0.10 stage R2: 1 = `instance.spawn <object>` works (ring level Objekte - `Spieler/Objekte` since 0.10.5, command bar, TruLink); 0 = refused. Read again from the ini at most once a second, so a TO TEST switch `ini:TruMenu:Radial:Spawn` works in the running game |
| `[Shot] Enabled` | 1 | 0.10.5: screenshots on request (`shot.save`, ring, `claude.mark`, Hotkey, exports `TruMenuShot` / `TruMenuMark`); nothing automatic; 0 = every shot refused (mark lines still written, `shot=-`) |
| `[Shot] Folder` | (empty) | 0.10.5: PNG folder; empty = `TruShots` next to tru.exe, relative = below the game folder |
| `[Shot] Clean` | 1 | 0.10.5: 1 = copied before TruMenu draws; 0 = after (as on screen); `shot.save ui` / `clean` per shot; `claude.mark` always clean |
| `[Shot] Hotkey` | 0 | 0.10.5: virtual key (e.g. `0x7A` = F11) = `claude.mark now`; the game still gets it; 0 = off |
| `[Shot] MaxPerMinute` | 30 | 0.10.5: shots (and, separately, marks) per minute, 1 .. 120; 0 = no limit |
| `[Rescue] FallNet` | 0 | 0.22.24: 1 = fall net - Lara more than 3 s in the fall record 1068 and more than 3000 units below the newest safe-ground sample of her unit (the `player.unstuck` ring) is put back on that sample (at most 3 times per fall, never with the menu / ring open, in a cinematic, without player control); 0 = off, one "would" line per fall. Live: TruMenu reads the key about once a second (switch row in group `Rettung (TruMenu)`). The `fall watch:` log lines come at LogLevel 1 either way |
| `[Sound] WaveLog` | 1 | 0.22.45 (W6): one `snd.wave <id> START` line in `TruMenu.log` per start of a wave in `WaveIds` - unit, voice, group, volume, emitter + SoundPlex section, the object whose sound list holds the emitter, the wave table entry; `snd.wavelog on / off` switches it for this game start (switch row in group `Diagnose (TruMenu)`, read at the start) |
| `[Sound] WaveIds` | 10 | 0.22.45 (W6): the waves of `WaveLog`, decimal 0 .. 5119, at most 8 (space or comma between); 10 = `ui_drop_04` / the DLC 2 reuse of 6:10 (`docs\Befund-Gruppe-J-1211.md`); `snd.wavelog <ids>` for this game start |
| `[Sound] WaveLogMax` | 500 | 0.22.45 (W6): at most n `snd.wave` lines per game start (0 = no limit); later starts are only counted (`snd.mutes`) |
| `[Sonar] FullMap` | 0 | 0.22.48 (`sonar.full`): 1 = Sonar komplett - the PDA sonar draws every face of the loaded, placed map units of the floor, not only what the ping revealed (3 patches in the draw 0x6e3a00: every vertex counts as revealed); display only - the reveal state in the save (SaveInfo block 6) is not touched, off = the game's bytes and map at once. Live: TruMenu reads the key about once a second (switch row in group `PDA / Sonar (TruMenu)`), the item writes it |
| `[Sonar] HidePlaceholder` | 1 | 0.22.48 (`sonar.placeholder`): only with `FullMap=1`: 1 = the placeholder mesh of units without a baked map (100 faces / 56 vertices = the big 3D letters "MAP" in DLC 2, `dlc_level1_start`, `dlc_treasureroom` and five base units) is not drawn (call stub at 0x6e3ab0); 0 = drawn. With `FullMap=0` nothing is hooked (the game's code). Live |
| `[Sonar] FloorMarkers` | 0 | 0.22.48 (`sonar.markers`): only with `FullMap=1`: 1 = every stair / floor-change marker of the loaded units (0x6e40c6), not only the ones a ping saw; 0 = the game's. Live |
| `[Sonar] AllFloors` | 0 | 0.22.49 (`sonar.allfloors`, "Alle verbundenen Bereiche"): only with `FullMap=1`: 1 = the sonar frame 0x6e4130 also draws the map units of other floors that the sonar loaded itself (0x6e429b `74 1d` -> `90 90`: the floor test `[unit+0xb0] & [0xedf268]` skipped). Loaded are only the units the game's own open path asks for - the floor's units and their direct portal neighbours of any floor - so no load is added and streaming is not touched; display only. Live |
| `[Sonar] TriangleCap` | 300000 | 0.22.49 ("Sonar komplett: Dreiecks-Grenze"): only with `FullMap=1`: the sonar's per-frame triangle budget - TruMenu writes `cap - 1` into the imm32 of `cmp dword [0xee03e8], 0x16d83` (0x6dfa6f); values up to 93572 = the game's bytes, at most 1000000. A budget only (the triangles are flushed in batches of 2000 into the render device's growing dynamic vertex pool, 84 bytes each: 300000 = about 25 MB of vertex buffers per sonar frame). Live |
| `[Sound] ReverbFollowsMute` | 1 | 0.22.51 (`snd.reverbmute`, "Hall folgt Stumm"): the game sends every pool voice also into its own FMOD DSP "SFX Reverb" (holder `[0xccde98]`) - a send from the channel's DSP head that FMOD's mute (dry mix 0) never reaches; 1 = a voice whose channel FMOD has muted (ChannelI +0x74 bit 3: TruMenu's mute / solo / category / sonar-sound rules) sends 0 into it (two call redirects 0x591591 / 0x5841bf of the game's send `setMix`); 0 = the game's (muted sounds keep their reverb). Live |
| `[Sound] ReverbOff` | 0 | 0.22.51 (`snd.reverboff`, "Hall aus"): 1 = the game's reverb -> master connection set to 0 through the game's `setMix` 0x7b9ff3 (the level before kept and set back on 0); every reverb of the game is gone, also of audible sounds. Live |
| `[Sonar] FadeFar` | 0 | 0.22.51 (`sonar.fade`, "Sonar: Abblenden Ferne"): the fog of the sonar view. 0 = the game's call (its fog near = far = 65536, i.e. no linear fog); n = 1 .. 2000 metres: the map fades from n/2 to n m into the background colour (smaller = stronger); -1 = aus (fog 90 / 100 km). Two call redirects 0x6e4d94 / 0x6e4bf9 (`call 0x5bfe40` -> S5FogStub). Live |
| `[Sonar] TintOthers` | 0 | 0.22.51 (`sonar.tint`, "Sonar: andere Bereiche einfärben"): 1 = every map unit except the sonar's open unit (Lara's, `[0xedf254]`) is drawn with an amber-tinted draw colour (`[0xee03bc]` 40 % towards 255 / 170 / 40 for that unit's call, call redirect 0x6e42ac). Live |
| `[PDA] ShadowPdaAsBasePda` | 0 | 0.22.51 (`pda.basepda`, "Shadow-PDA durch Basis-PDA ersetzen"): 1 = DLC 2 shows the base PDA (Croft VX2 with the sonar map) instead of its journal PDA - in the resident g_pda script 3347 the DLC branch f1 (`level tag == "dlc2"`) returns 0 (word `04000001` -> `04000000`), written only in a level with the world running, the sonar and TruMenu's menu closed, back on 0 and at unload. Only with the DLC g_pda; the PC's own g_pda has no DLC branch ("keine DLC-PDA geladen", nothing written). Live |
| `[Sound] SourceHooks` | 1 | 0.22.50: 1 = the two small code redirects that name a sound's source exactly - V1 0x591351 (the wave node's `call VoicePool::Play` -> a stub: voice -> the node's emitter +0x10) and E1 0x5b99fc (the 6 bytes after the anim sound event's untouched `call 0x5935d0` -> a stub: emitter -> the event's instance `[ebp+0xc]`); written on the game thread only over the game's bytes, put back at unload; 0 = the owner list of `[inst+0x248]` only. Read at the start |
| `[Sound] LogLara` | 1 | 0.22.50 (`snd.logcat lara`): the sound box shows Lara's body / gear / weapons sounds. Live |
| `[Sound] LogEnemies` | 1 | 0.22.50 (`snd.logcat enemies`): enemies and creatures. Live |
| `[Sound] LogWorld` | 1 | 0.22.50 (`snd.logcat world`): world and ambience (groups 14 .. 24 and the effect nodes). Live |
| `[Sound] LogObjects` | 1 | 0.22.50 (`snd.logcat objects`): objects, mechanisms, traps, debris, explosions. Live |
| `[Sound] LogUi` | 1 | 0.22.50 (`snd.logcat ui`): HUD, menu, PDA / sonar, binoculars. Live |
| `[Sound] LogSpeech` | 1 | 0.22.50 (`snd.logcat speech`): Lara's voice and hints, radio, cutscene speech. Live |
| `[Sound] LogMusic` | 1 | 0.22.50 (`snd.logcat music`): music voices and streams. Live |
| `[Sound] LogOnlyAudible` | 0 | 0.22.50 (`snd.logaudible`): 1 = the box hides lines FMOD mutes or pauses (ChannelI +0x74 bit 3 / real channel +0x68 bit 0x20). Live |
| `[Sound] LogCollapse` | 1 | 0.22.50 (`snd.logcollapse`): 1 = same wave + same source = one line with `×n` and the newest time, moving to the top on every new start; 0 = one line per start. Live |
| `[Sound] LogMaxDist` | 0 | 0.22.50 (`snd.logdist`): the box hides 3D sounds farther from Lara than n metres (0 = every distance), 0 .. 500. Live |

## Build, install, test (Windows)

```powershell
.\scripts\windows\Build-TruAsi.ps1 -Name TruMenu -Verbose   # also compiles src\asi\third_party\imgui -> work\asi\TruMenu.asi
.\scripts\windows\Set-TruMenu.ps1 -Install                  # copies .asi + .ini next to tru.exe (game closed)
.\scripts\windows\Set-TruMenu.ps1 -Remove                   # removes them again (only if they are a build of ours)
```

Static runtime (`/MT`), imports `KERNEL32.dll` and `USER32.dll` only (since 0.9 also `SHELL32.dll`:
`SHGetFolderPathW` for the save folder; 0.10 added `GetWindowThreadProcessId` / `MapVirtualKeyA` from USER32). Test plan
for the first run:

1. Main menu: press L3 + R3 - the menu appears (Status page open). Check the code-check line (all `ok`), the pad line
   ("PadHook given to the game ..."), `d3d9.dll` path, "pad read in Present" (yes = the game does not poll there).
   Navigate with the D-pad / A, close with L3 + R3.
2. Level select from the main menu: "Load dlc_level2_start" (or `menu level.load ...` over TruLink).
3. In a level: open the menu - Lara must not move while it is open; Overlay page -> tick the position overlay, close
   the menu, walk: the numbers change. With TruShadowPower: LB / RB do nothing while the menu is open.
4. Cheat / flight ON, close the menu, RT / LT - Lara rises / sinks. Turn it off again.
5. Free camera page: `CAMERA_SetMode(11)`, then "Restore game camera".
6. Send `TruMenu.log` (and `TruShadowPower.log` / `TruLink.log` if loaded).

0.2 additions (built e.g. with `-OutDir work\asi\menu02` so the 0.1.3 build stays):

7. Status page: the line `costume ok, unit table ok`; unit / state / costume / player lines change between main
   menu and a level (`menu status.costume` over TruLink gives the same text).
8. Level select: open "Base game l2", load `l2_junglehub` - the level loads; then DLC 1 / DLC 2 starts as before.
9. Outfits in a level: tick "reload ...", choose `lara_bikini` - the unit reloads with that outfit; `menu
   costume.current` shows its id. "Reset chosen costume", reload: the unit default comes back.
10. With TruDlc2Player loaded the list holds `doppelganger_casual` as well (record 39).

0.3 additions (built with `-OutDir work\asi\menu03`). Every step: note the result and send `TruMenu.log`.

11. Quick access opens first with the default favourites; Y on "time.pause" removes it, "Add an item" -> Y / A adds
    it back; `TruMenu.ini` next to the `.asi` now has `[Favorites] Ids=...`; `menu fav.list` / `fav.add dev.fog_far`.
    Then the Status page: the two "0.3:" lines - every entry `ok` (`dev menu ok`, ... `markup draw ok`, `weapon.give ok`,
    `ammo ok`, `health ok`); `TruMenu.log` holds "0.3 checks" and "dev menu: 101 rows in 15 pages".
12. Developer menu page (main menu): root shows the title, "Keep Info Between Loads", "Units ->", "Chapters (empty in
    retail)"; "Units ->" and "<< root page" work; "All pages" lists 15 pages. `menu dev.list` over TruLink lists 42
    rows; `menu dev.time_mult` answers `4096 (0..16384)` (init value 0x1000).
13. Developer menu in a level, one live test per row (note what changes on screen): Show Spline Info, Projected
    Shadows, Show Input Actions, VV Stats, Show Music Vars, Show Monster Music Vars, Enable ScreenShot, UI Make Hints
    Modal; Fog Far / Near / RGB (the fog should change at once), Restore Fog; Frame Rate Lock 0..3; Time Mult (e.g.
    2048 / 8192). Leave out "Perfect Game NOW" (progress bit, not undone) unless on a throw-away save.
14. Time / player / HUD in a level: time scale 0.3 / 1.0, freeze world on / off, hide HUD on / off, player control off
    (Lara does not react) / on, mark, walk away, back to mark, camera fov slider, ragdoll death last.
15. Instances: list fills (names, positions); "Lara goes there" to a pickup (flight on), "Bring to Lara", "Remove" on a
    harmless object; `menu instance.list wp_` / `menu instance.info #0` over TruLink.
16. Outfits (live switch) in a level: "Next outfit" changes Lara at once and she keeps her weapons (message 35 a frame
    later); a button of the list switches to that outfit; `menu costume.list` gives the same ids.
17. Debug / Log: lines from TruMenu / TruLink / TruShadowPower appear within a second; filter buttons; overlay on;
    "script prints" on, play a bit - script lines appear (or not: then the natives are not called in retail - note
    it); `menu log.page`, `menu log.lines 20`, `menu log.filter TruLink`.
18. Media in the main menu: Play `intro` (watch whether the game shows it and returns to the menu), "as menu loop"
    `explode`, leave and re-enter the main menu (background changes?), "menu loop back to medsea_loop".
19. Markup draw in a level near ledges: lines / circles appear; if they are offset or scaled, try `menu draw.scale
    640 480` (or the sliders) and note the values that fit; "ledges only".
20. Weapons / health in a level (main state 1): `menu weapon.give wp_shotgun` (an already loaded weapon first),
    `menu ammo.show`, `menu ammo.set 1 50` (HUD reserve changes?), "Full health", "invincible" + a hit (no damage).
21. Settings: pin something (Ids changes, `*` on the Settings page); "Reset all settings" once - nothing happens but
    the red "press A again" - A again: `TruMenu.ini.bak_<time>` appears next to the `.asi`, the ini equals the shipped
    one, favourites are the default list again; `menu settings.show`, `menu fav.reset`.

0.4 additions (built with `-OutDir work\asi\menu04`; install the `.asi` **and** the new `TruMenu.ini` - it has four
new `[Log]` keys, an old ini works too: missing keys take the defaults). Every step: note the result, send
`TruMenu.log`, `TruLink.log` and `TruMenu.tests.txt`.

22. Status page: the line `0.4: weapon slots ok, ammo.fill ok, gear.give ok; TO TEST file <tru.exe folder>\TruMenu.tests.txt`;
    `TruMenu.log` holds "0.4 checks". With no `TruMenu.tests.txt` there is **no** TO TEST page; Quick access is first.
23. TO TEST over TruLink: `menu test.add level.reload Reload - Lara at the same spot?`, `menu test.add
    ui.hide:1 HUD gone?`, `menu test.add look-shadow Shadows at the start look right?` - open the menu: "TO TEST (3
    open, ...)" is the first page, rows with "Run level.reload" / "Run ui.hide 1" and none for `look-shadow`.
24. Marking with the pad: D-pad to a row, A -> `[OK]` green, X -> `[FAIL]` red (the focus stays on the row, no jump to
    the title bar), Y -> `[SKIP]` grey (the row is **not** marked OK first); the buttons OK / FAIL / SKIP do the same;
    "Run ui.hide 1" hides the HUD. `menu test.list` shows the states; `menu test.mark look-shadow fail dark band left`
    -> the row shows the note.
25. Restart the game: the rows and states are back (`TruMenu.log` "tests: 3 rows from ..."); "Remove the marked rows"
    removes the marked ones; "Remove all rows" needs A twice; the page disappears; `menu test.clear` answers `0 left`.
26. Log page: let TruLink poll (e.g. `watch add` + repeated `read32 player`): no `> read32` lines; a line that repeats
    shows as `... x<n> (<first>-<last>)`; "warnings + errors" / "errors" hide the info lines; set `menu log.rate 2`,
    produce many lines - one yellow line "(n lines dropped ...)"; `menu log.page` shows the same; `menu log.collapse 0`
    / `log.hidereads 0` bring the raw lines back (only new ones). The counter line under the list counts all three.
27. Weapons in a level: `menu weapon.slots` (slot numbers + names, the selected slot), `menu weapon.has wp_handgun`
    (yes, slot n), `menu weapon.has wp_uzi` before / after `weapon.give wp_uzi`; `menu ammo.fill` -> `menu ammo.show`
    gives the MaxAmmo values (HUD reserve full?); `menu gear.give g_binoculars` (note whether the item appears /
    whether anything breaks - static facts only).

0.5 additions (built with `-OutDir work\asi\menu05`; `TruMenu.ini` unchanged from 0.4;
`Set-TruMenu.ps1 -Install -SourceDir .\work\asi\menu05` replaces 0.1.3 - 0.4 builds as ours):

28. `menu test.clear`, `menu test.step 2 - Second`, `menu test.step 1 - First`, `menu test.add c1 Check one`,
    `menu test.step 3 ui.hide:1 Hide the HUD` - the page shows "NEXT->  1. First", "2. Second", the check, "3. Hide
    the HUD" with "Run ui.hide 1"; A on step 1 -> `[DONE]`, NEXT moves to step 2; A on step 3 hides the HUD and marks it
    done; "Open again" opens it again. `menu test.mark step2 ok` -> `err step2 is a step row: open|done`.
29. `menu test.toggle sp-states ini:TruShadowPower:States:Enabled States` (TruShadowPower installed): a checkbox under
    "Switches", state = the INI value, note "INI: takes effect at the next start"; untick it -> `TruShadowPower.ini`
    holds `Enabled=0` in `[States]` at once (the plugin still runs as before); restart: the row shows off and the
    plugin log says states 0. `menu test.toggle x ini:Foo:A:B x` -> `err bad ini target`.
30. `menu test.toggle fly cheat.flight Flight` - tick: flight on (as `menu cheat.flight 1`), untick: off.
31. `menu test.export` -> `ok+ test.export ...`, one tab-separated line per row, `.`; `Invoke-TruLink.ps1 -Command
    'menu test.export'` prints the block. Restart: steps / toggles / checks and their states are back; a 0.4
    `TruMenu.tests.txt` loads as checks.

0.6 additions (built with `-OutDir work\asi\menu06`; install the `.asi` **and** the new `TruMenu.ini` - it has the
`[Cmd]` section, an old ini works too: `Set-TruMenu.ps1 -Install -SourceDir .\work\asi\menu06`). Every step: note the
result, send `TruMenu.log`, `TruLink.log` and `TruMenu.history.txt`.

32. Main menu, open the menu (L3 + R3): the bar sits directly under the menu window, the text cursor blinks in it;
    TO TEST / Quick access are still the first pages. Type `time.scale` - the list above the bar shows `time.scale = 1.000`
    first; Enter -> green `ok time.scale = 1.000`. Type `ui.hide` + Enter -> its value, the HUD does **not** change.
33. Keys do not leak: type `wasd` and Esc in the bar while in a level - Lara does not move, no pause menu; Esc puts the
    focus into the menu; F2 brings it back.
34. Autocomplete: `cost` -> `costume.*` ids first (prefix), Down / Down / Tab takes the third one; `costume.set ` (with
    space, in a level) lists the outfit cycle names, `doppel` filters them; Enter runs `costume.set doppelganger_casual`
    -> `ok queued costume.set ...`, then (next game frame) the real answer replaces it. `level.load ` lists the units.
35. `time.scale 0.5` (world slower), `time.scale 1`; `get level.load`; `list fog`; `help`; `nonsense` -> red
    `err unknown item 'nonsense'`; `costume.sett` -> `... did you mean costume.set?`.
36. History: run three lines, empty bar, Up / Up / Down - the lines come back in order; restart the game - Up still
    shows them (`TruMenu.history.txt` next to `tru.exe`); `menu cmd.history` over TruLink lists them newest first.
37. Pad with the bar focused (menu just opened): D-pad down -> the focus is in the menu (TO TEST / Quick access header),
    D-pad again navigates as in 0.5; A / B / X / Y on the pages work as before (TO TEST: A = OK, X = FAIL, Y = SKIP).
38. Pad picker: in the menu press View - the list shows all ids with values; D-pad to `ui.hide`, A -> the HUD toggles
    (result line `ok ...`); to `time.scale`, A -> value picker, RB x5 -> 1.5, A -> world faster, B, B -> back in the
    menu; to `level.load`, A -> unit list, A on `dlc_level1_start` loads it; Y on an id pins it (Quick access).
39. TruLink: `menu cmd.run time.scale 0.5` -> answer as `menu time.scale 0.5`, the bar shows `TruLink: time.scale 0.5`;
    `menu cmd.focus` opens the menu with the focus in the bar; with `[Cmd] Enabled=0` there is no bar and
    `menu cmd.focus` answers `err command bar off`.

0.7 additions (built with `-OutDir work\asi\menu07`; install the `.asi` **and** the new `TruMenu.ini` - five new keys,
an old ini works too: `Set-TruMenu.ps1 -Install -SourceDir .\work\asi\menu07`; the 0.6 builds `work\asi\menu06` /
`work\asi` and the 0.6 ini are recognised as ours). Every step: note the result, send `TruMenu.log`, `TruLink.log` and
`TruMenu.history.txt`.

40. Status page: line `mouse (0.7): ready (...)`; `TruMenu.log` holds "0.7 cmd: focus button 0x0040, ..." and "0.7
    mouse: SetCursorPos slot 0x0083e308, ClipCursor slot 0x0083e2e0 ... game code 1 -> ready". (`slots NOT matched`:
    send the log - only the mouse messages are held then.)
41. Controller only, in a level: open the menu (L3 + R3) - **no** keyboard appears and closing with L3 + R3 opens none
    either. Open, D-pad into the menu, press **L3** alone: the bar gets the focus, the keyboard appears under it with the
    cursor on `q`; row 0 shows the history (or "(no history yet ...)").
42. Keyboard: RB -> tokens row, A on `time.` -> the line is `time.`, row 0 lists `time.scale`, `time.pause`; LB -> row 0,
    A (or Y from any row) takes `time.scale ` (with space); type `0`, `.`, `5` with the D-pad / A; Start -> green
    `ok ...`, the world runs at half speed; `time.scale 1` back. X deletes (hold = repeat). B closes the keyboard, D-pad
    then goes into the menu as in 0.6. View with the keyboard open -> pad picker; View there -> keyboard again.
43. Look: rounded keys, highlighted key with a yellow frame, pressed key lights up; Run key green; nothing cut off at the
    right edge (also at `[Menu] Scale` 1.0 / 2.0 - note how it looks on the TV).
44. Keyboard + real keyboard: with the on-screen keyboard open, type `ui` on the real keyboard -> it closes, the field
    holds the line + `ui` with the cursor at the end (nothing selected), Lara does not move. Esc with the on-screen
    keyboard open only closes it.
45. Mouse in a level (camera follows the mouse when the menu is closed): open the menu - an ImGui cursor appears, moving
    the mouse does **not** turn the camera and the cursor is not pulled back to the centre; click into the bar, type,
    click a menu button, click a key of the on-screen keyboard (L3 first). Alt + Tab away and back, click into the bar
    - it takes the focus (0.6 failed here). Close the menu: the camera does not jump, mouse look works as before, the
    cursor is hidden / clipped again. Windowed (TRAWindowed): the cursor tip matches the clicked widget.
46. `[Menu] FreeMouse=0` (restart): behaviour as 0.6 (camera turns while the menu is open). Back to 1.
47. Options: `[Cmd] UpOpensHistory=0` -> Up in the empty bar goes into the menu, Ctrl + Up opens the history;
    `[Cmd] FirstPadPressOnlyFocuses=0` -> the first D-pad press in the bar moves the focus into the menu **and** one
    entry further (hold = repeats); `[Cmd] Keyboard=0` -> L3 only focuses the text field; `[Cmd] FocusButton=0` -> L3
    does nothing.
48. TruLink: `menu cmd.keyboard` (menu closed) -> menu opens with the bar focused and the keyboard shown;
    `menu status.hooks` ends with `mouse=...`.

0.7.1 additions (built with `-OutDir work\asi\menu071`; install the `.asi` **and** the new `TruMenu.ini` - five new
keys, an old ini works too: `Set-TruMenu.ps1 -Install -SourceDir .\work\asi\menu071`; the 0.7 build `work\asi\menu07`
and its ini are recognised as ours). Every step: note the result, send `TruMenu.log`, `TruLink.log` and
`TruMenu.history.txt`.

49. `TruMenu.log` after the start: "0.7.1 keyboard: wrapper vtable slot 0x00844f64 0x00486100 -> KbdReadHook -> ready
    ..." and "0.7.1: block game input 1 (keyboard hooked), pause game 0 (...), mission start path 1, stream unit name 1
    ...". Status page: line `keyboard (0.7.1): ready ...`.
50. In a level, Lara standing: open the menu, type `wasd` and Enter into the command bar (also hold `w` for a second)
    - **Lara must not move**; close the menu - she stays standing (also when `w` is still held while closing: she only
    walks after `w` is released and pressed again). Status line counters: events held > 0.
51. Hold `w` (Lara runs), open the menu with L3 + R3 while still holding it - Lara **stops** (neutral state, "releases
    sent" > 0); release `w`, close the menu - she stays standing.
52. Esc in the menu (bar focused, on-screen keyboard open, and in the menu window): **no pause menu** of the game; with
    the on-screen keyboard open Esc only closes it. After closing the TruMenu, Esc opens the game's pause menu as usual.
53. B twice: L3 (keyboard open), **B** -> only the keyboard closes (menu stays, bar focused); **B** again -> the menu
    closes (`TruMenu.log`: "menu closed (B twice: keyboard, then menu)"). Variant: L3, B, D-pad down -> focus in the
    menu (no close). If a single B still closes the menu: send the log line "menu closed (...)".
54. Real keyboard switch with the mouse elsewhere: L3 (keyboard open, cursor on `q`), move the mouse cursor away (over
    the menu window or outside the game), do **not** touch the pad, type `ui` on the real keyboard -> the keyboard closes,
    the field holds `ui` with the cursor at the end, typing goes on (`.hide`), Enter runs it. Repeat with the
    cursor over the bar and after selecting a key with the D-pad.
55. Keyboard reopen: L3 (keyboard open), close the menu with L3 + R3, open again -> the keyboard is back; B (closes it),
    L3 + R3, L3 + R3 -> menu without keyboard.
56. `[Menu] PauseGame=1` (restart): in a level with enemies / moving water, open the menu - the world stands still,
    close - it moves on. `time.pause 1` before opening -> still paused after closing; `time.pause` used inside the menu
    -> its state is kept after closing. Back to 0.
57. `[Menu] BlockGameInput=0` (restart): as 0.7 (typing in the bar can move Lara again) - only to confirm the switch.
58. Lara's stream unit: `log.overlay 1`, walk through DLC 2 from the start room into the next rooms - the overlay shows
    lines `unit: <name> (was <name>; stream unit id N)` at each room change; `menu status.unit` shows "Lara's unit".
    Note the names (catalog of the internal room names).
59. `level.start dlc2` from the main menu (command bar or Level select button "Start DLC 2 as the mission menu
    (intro)"): the DLC 2 **intro plays**, then the level (compare `level.load dlc_level2_start`: no intro). Outfit /
    weapon choice as with the mission menu? Sound on?
60. `[Test] AutoStart=dlc2` (restart, game data **without** test patch 41e): after the main menu has been up for 3 s the
    DLC 2 intro starts by itself, once per game start (quit to the main menu: it stays). `TruMenu.log`: "AutoStart:
    main menu up ..." and "AutoStart: level.start dlc_level2_start queued ...". Back to empty.

0.7.2 additions (built with `-OutDir work\asi\menu072`; install the `.asi` **and** the new `TruMenu.ini` - three new
keys, an old ini works too: `Set-TruMenu.ps1 -Install -SourceDir .\work\asi\menu072`; the 0.7.1 build
`work\asi\menu071` and its ini are recognised as ours). Every step: note the result, send `TruMenu.log`.

61. `TruMenu.log` after the start: "0.7.2: pending check 1 (main state 2 / 9 + GameTracker+0xb9), outfit rule 1 (ini 1;
    ...), game.quit ready (exit code 0x544d, ...)". `menu level.start` (value) shows "outfit rule title update ...;
    pending check main state 2 / 9 + GameTracker+0xb9".
62. Level select page: the two mission-menu buttons in the order **DLC 1, DLC 2**.
63. `level.start dlc2` from the main menu: the DLC 2 intro plays and **no outfit / weapon selection** comes; Lara is the
    doppelganger (TruDlc2Player log: costume "lara_doppelganger" -> doppelganger_casual). `TruMenu.log`: "mission start
    'dlc_level2_start': ... f27('dlc_level2_start', 0, 0, 1) ... no outfit / weapon selection". Compare with the Xbox
    (Xenia checklist 12c).
64. `level.start dlc1` from the main menu: the outfit / weapon selection **does** come (`f27(..., 1, 0, 1)`). While it is
    open: open the menu, `level.load dlc_level2_start` and `level.start dlc2` -> both answer `refused: level change
    pending (main state 9: the outfit / weapon selection of a level start is open)`; the Level page shows the grey
    reason line; `status.state` says "outfit / weapon selection ...". Close the menu, choose an outfit - DLC 1 loads
    normally (no hang).
65. `[Levels] OutfitRule=0` (restart): `level.start dlc2` shows the outfit selection again (as 0.7.1). Back to 1.
66. `game.quit`: Status page (expand "Status"), last button "Quit game (press twice)" - press once: it turns red
    "CONFIRM: quit the game now (5 s)"; wait > 5 s: back to normal, nothing happens. Press twice: the game ends at once.
    `TruMenu.log` ends with "game.quit armed by the owner ..." and "game.quit by the owner (TruMenu) - logs flushed
    next, then TerminateProcess(...)". Also from the command bar: `game.quit`, Enter, `game.quit`, Enter.
67. TruLink: `menu game.quit` -> `err game.quit only from the menu, the command bar or a favourite (owner) - never over
    TruLink`; the game keeps running.
68. Harness: a run of `Invoke-TruTestRun.ps1` ended with `game.quit` -> `summary.md` status "... - ended via TruMenu
    game.quit (exit code 0x544D, not a crash)", exit code row `21581 (0x544D: ended via TruMenu game.quit)`, first
    crash marker `-`, the verdict notes name it and the owner checks still count. Only the exit code is mapped: under
    `-Debugger` the code is the one cmd / cdb hand back, and a session that echoes `TERMINATEPROCESS` still counts that
    marker as a crash (not changed in 0.7.2).
69. Log overlay filter: `log.overlay 1` in DLC 2 with TruShadowPower: the overlay shows only TruMenu / TruGuard lines
    (unit changes readable, no "activity 1009" lines); the Debug / Log page still shows TruShadowPower.
    `log.overlaysources *` -> all again; `log.overlayexclude activity 1009` -> those lines gone from the overlay only;
    `log.overlayexclude none` -> back.

0.8 additions (built with `-OutDir work\asi\menu080`; install with `Set-TruMenu.ps1 -Install -SourceDir
.\work\asi\menu080` - it copies the `.asi`, the new `TruMenu.ini` (five new keys; an old ini works too) and the two
regression lists; the 0.7.2 build `work\asi\menu072` and its ini are recognised as ours). Every step: note the result,
send `TruMenu.log` and `TruMenu.regress_results.txt`.

70. `TruMenu.log` after the start: "0.8 cheats (enabled 1, persist 0): god 1, god full 1, one-hit kill 1, enemy health
    1, infinite ammo 1, fill 'er up 1, cheat code 1" (no "disabled" line) and "0.8: camera log 1 (...), regression lists
    ... (dlc1 18 rows, dlc2 30 rows, page shows all)". Status page: line "0.8: cheats god ok ...".
71. Regression page (main menu is enough): header "Regression DLC 1 + DLC 2 (35 open, ...)"; DLC 1 / DLC 2 / all switch
    the rows. On a check: A -> green [OK], X -> red [FAIL], Y -> grey [SKIP] (X / Y must not act on anything else).
    `TruMenu.regress_results.txt` next to the `.asi`: one `#session` line (plugin versions incl. `TruMenu=TruMenu
    0.8.0`, sha256 of every loaded `Tru*.asi` - compare TruMenu's with this build), then one line per mark.
72. Note: "Note" on a row -> the command bar shows `regress.note dlc2:<id> ` with the on-screen keyboard; type a word,
    Run / Enter -> the row shows "- <word>", a result line with the note. Restart the game: every row open again, the
    results file keeps the old lines, a new `#session` line comes before the next mark.
73. TruLink: `menu regress.load dlc2` -> page shows DLC 2, all rows open; `menu regress.mark dlc2:waterfall ok bright`;
    `menu regress.mark no-crash ok` with "all" selected -> `err 'no-crash' is in both lists - write dlc1:no-crash or
    dlc2:no-crash`; `menu regress.export` -> block with 48 rows, ends with `.`.
74. Cheats page in the main menu: every switch greyed out, "needs a level". In a level: `cheat.god` on (log "cheat: god
    mode ON") - an enemy hit / small fall does not lower health; a deep fall still kills (instant death passes, as in
    the prototype). Off again.
75. `cheat.godfull` on: no damage at all (also types 8 / 5)? Watch for side effects of cheatMode bit 0 (no-clip /
    flight behaviour, camera, controls); then off - `cheat.flight` must still work as before.
76. `cheat.onehitkill` on: one shot kills an enemy (log "toggle 0x0060f670 called"); off: normal damage.
77. `cheat.enemyhealth` on: is a hit-point number drawn at enemies? (may draw nothing in retail - mark what you see).
78. `cheat.ammo` on with pistols + another weapon: shoot past one clip - the reserve (`ammo.show`) does not drop; pick up
    / give another weapon (`weapon.give wp_shotgun`), wait 1 s - it reloads without reserve as well; off: reserve drops
    again (the pistols keep their own behaviour).
79. `cheat.fillup` after taking damage: health back to max (HUD health silhouette flashes), reserves at max
    (`ammo.show`); log "cheat: fill 'er up - health a -> b".
80. Cheat codes in a level: `cheat.code 2` -> Lara shows the hit-reaction effect, `cheat.god` reads 1; again -> 0;
    `cheat.code 1` / `11` toggle `cheat.onehitkill` / `cheat.enemyhealth`; `cheat.code 9` / `10`: nothing visible
    expected (no readers); `cheat.code 4` -> usage error. No crash.
81. `[Cheats] Persist=1` (restart): switch `cheat.god` on, quit, start again, load a level -> log "cheats: [Cheats]
    Persist=1 - cheat.god on again"; `[Cheats] State=cheat.god` in the ini. Back to 0 (and clear State).
82. Camera log (DLC 2, `log.overlay 1`): walk - "camera: mode ... at the start of the log"; hold RB / aim -> mode lines;
    the second DLC 2 hint (rock channel) that swings the camera to the wall: which "camera: mode" / "camera: object"
    lines come (copy them into the report). `camera.log 0` -> no more lines.

0.8.1 additions (built with `-OutDir work\asi\menu081`; install with `Set-TruMenu.ps1 -Install -SourceDir
.\work\asi\menu081` - `.asi`, the new `TruMenu.ini` (one new key `[Log] InputTrace`) and the two regression lists; the
0.8.0 build and its ini are recognised as ours). Run with `[Menu] LogLevel=2` (the harness profiles do) and send
`TruMenu.log` + `TruMenu.regress_results.txt`.

83. Start: `TruMenu.log` holds "0.8.1: input trace 1 (... now 2), game.quit window 10 s + hold 1 s, request slot claimed
    once, regression shortcuts 7, player.unstuck ring 16 spots".
84. **game.quit with the pad**: Status page, D-pad to "Quit game (press twice, or hold 1 s)", A once -> a red
    "Quit now" button appears beside it with "armed - 10 s left" (the label does not change), the focus jumps to
    "Quit now" after you let go of A; A again within 10 s -> the game ends (exit code 0x544D). Log: two
    `input: pad0 A down (XInput hook) -> activated '...'` lines, "game.quit armed", "game.quit by the owner".
85. game.quit, hold: A on "Quit game ..." and keep it held -> a progress bar "hold 1 s to quit" fills, after 1 s the game
    ends (log "game.quit: button held 1 s by the owner"). Same with the PC keyboard (arrow keys + Enter) and with the
    mouse (click "Quit game", then click "Quit now"; or hold the mouse 1 s). Let it run out once: after 10 s the red
    button disappears and nothing happens.
86. Input trace: open the menu, press A on a few buttons, D-pad around, a key, a mouse click; close. `TruMenu.log`: one
    `input:` line per press / release with "activated" / "focus 'a' -> 'b'" / a "not activated: <reason>" that makes
    sense, and at the close "input while the menu was open: n pad presses (A n: n activated, n not), ...". Try the
    bar: D-pad down from the bar -> "command bar owns the pad: focus from the bar into the menu - swallowed by
    FirstPadPressOnlyFocuses". `log.inputtrace 0` -> only the summary lines.
87. Stuck Enter: in the bar type `level.load dlc_level2_start`, Enter (menu closes, level loads); open the menu again
    -> the bar must NOT run empty lines (no "cmd (bar):  -> err empty line" lines in the log); hold Enter in the bar
    with a typed line -> it runs once.
88. cheat.flight: Cheat / flight page, "Cheat / flight ON" -> one `item cheat.flight: cheat.flight 1` line only (no
    "0" right after), Lara flies with RT / LT (menu closed); "OFF" -> one `cheat.flight 0` line. Several times.
89. cheat.ammo in hall02 with only the pistols: answer lists every slot weapon, e.g. "slot 0 ...: type -1 ... ammo type
    0xff = unlimited already" (copy the line). Then `weapon.give wp_shotgun` (or any ammo weapon), wait 1 s, `cheat.ammo
    0` + `cheat.ammo 1` -> that weapon shows "bit set"; shoot past one clip: the reserve (`ammo.show`) does not drop.
90. player.unstuck: in hall02 walk around on firm ground for ~10 s, then jump / slide into the eitr (god mode on);
    `player.unstuck` (button on Time / player / HUD or command bar) -> Lara stands on ground she walked on before; again
    within 20 s -> one spot further back. `player.mark` somewhere, walk away, `player.unstuck` -> back at the mark
    (newer). Before walking anywhere: "no target: ..." (no crash).
91. Regression shortcuts: Regression page -> "Quick prepare" list with "Thrall fight: hall02 + god mode (dlc2:step7)",
    "DLC 2 start unit ...", "Treasure room", ... A on "Thrall fight" -> the menu closes for the level load, hall02
    loads, about 2 s later god mode switches on (`TruMenu.log`: "shortcut 'Thrall fight: hall02 + god mode' 1/2:
    level.load ... 2/2: cheat.god 1 -> ok ..., done"); the page line "shortcut: ...: done". "Prepare" on the dlc2 step5
    row: god mode off + time.scale 0.5. `menu regress.prepare dlc2:step7` over TruLink works the same; `regress.prepare
    stop` while it waits stops it.

0.10 additions (radial menu; built with `-OutDir work\asi\menu010`, profile `regress_shadowlara_50l_radial`; install with
`Set-TruMenu.ps1 -Install -SourceDir .\work\asi\menu010` - also copies `TruMenu.radial.txt`; the new `TruMenu.ini` has the
`[Radial]` section, an edited ini is kept and takes the defaults). Section "Radial menu (0.10)".

92. Start: `TruMenu.log` holds "0.10 radial: enabled 1, hold buttons 0x00c0 500 ms (= the menu combo: short press = menu
    at the release), key 0x78 (DirectInput 0x43, kept from the game) ..." and "radial: 27 entries in 7 levels from
    ...TruMenu.radial.txt (0 dropped, 0 unknown, 0 lines skipped)"; Status page line `radial (0.10): ...`; Settings page
    lists the 11 `[Radial]` keys.
93. L3 + R3 **short** (main menu or level): TruMenu opens when you let go ("menu opened (pad, short press)"); L3 + R3 in
    the open menu closes it at once. Lara does not crouch / look while you press.
94. In a level, **hold** L3 + R3: after 0.5 s the ring with Cheats, Marken, Zeit, Waffen, Spieler, Objekte; the right
    stick lights one sector; release on **Zeit** -> the Zeit level opens and the ring stays open.
95. Latched ring in Zeit: stick to "Zeitlupe 0.5", **A** -> the world runs slower, the ring stays, `TruMenu.log`
    "radial: Zeit -> time.scale 0.5: ok time.scale 0.500 ..."; stick to "Normal 1.0", **R3** -> runs and closes.
96. Hold, leave the stick in the **centre**, release -> nothing runs ("radial: closed (released in the centre)" at
    LogLevel 2). Hold, release on Cheats, **B** -> top level, **B** -> closed.
97. Remember: close the ring in Cheats with a sector picked; hold again -> it opens in Cheats with that sector lit;
    release without moving the stick -> nothing runs. `[Radial] RememberPosition=0` (restart) -> always the top.
98. Cheats -> Gott-Modus shows **off**; A -> **on** (green), log "radial: Cheats -> cheat.god 1"; A again -> off
    ("cheat.god 0"). Same for Spieler -> Unverwundbar and Zeit -> Welt einfrieren.
99. Main menu (no level): hold -> Cheats / Spieler / Waffen entries grey with "needs a level" in the centre; A on one ->
    "not available - needs a level" under the ring. Objekte entries grey "[Radial] Spawn=0 (stage R2 off)".
100. Keyboard: **hold F9** -> the ring at once; move the mouse -> a white dot and the sector in that direction; release
    F9 -> runs. The game does not react to F9. Steam Controller: Steam Input, map a back button to F9 -> the same.
101. `[Radial] MouseButton=3` (restart): hold the middle mouse button -> ring, mouse picks, release runs; left click = A,
    right click = B.
102. While the ring is open: the camera does not turn (right stick, mouse), A / B / LB / RB do nothing in the game,
    Lara walks with the left stick; `[Radial] PassLeftStick=0` (restart) -> she stands. After closing with B / R3 the
    game does not see that button.
103. `[Radial] SlowMotion=0.25` (restart): the world slows while the ring is open and is back to normal after the close;
    with "Zeitlupe 0.5" run from the ring it stays at 0.5.
104. Waffen -> Schrotflinte (in hall02 or dlc_level2_start): `weapon.give wp_shotgun` queued, "last action" shows the
    answer; the shotgun is in the inventory. Munition voll -> `ammo.show` at max.
105. `[Radial] Enabled=0` (restart): L3 + R3 toggles at the press as in 0.9, holding does nothing else, F9 reaches the
    game; `radial.status` says "enabled 0".
106. TruLink: `menu radial.status`, `menu radial.list` (27 entries, the Objekte ones "= greyed: [Radial] Spawn=0"), `menu
    radial.open Zeit` (ring opens latched at Zeit, B B closes), `menu radial.reload`.

Stage R2 - **only with `[Radial] Spawn=1`, back up the saves first** (Saves page "Back up all saves now"; the key is
read again while the game runs - in the profile the TO TEST switch `radial-spawn` sets it, no restart):

107. `TruMenu.log` at the start: "0.10 radial: ... spawn (R2) code ok, [Radial] Spawn=0"; switch it on (TO TEST switch or
    ini) -> within a second the Objekte entries are no longer grey (in a level); `radial.status` "... (Spawn=1)".
108. hall02 (or dlc_level2_start): Objekte -> **Medipack** -> `TruMenu.log` "instance.spawn: g_healthpack (id 55) born
    at Lara ...: instance 0x...; tracker ... was in the table, 0 polls" - a health pack at Lara's feet; walk away, look,
    pick it up if possible. `instance.list healthpack` lists it.
109. Objekte -> **Kiste A**: a short stutter (load), "... requested now, n polls / m ms"; a crate at Lara (inside her -
    step out); push / shoot it, note physics. Kiste B / C the same. A second Kiste A: "was in the table", no stutter.
110. Objekte -> **Schrotflinte (Objekt)** last: note what appears (pickup or bare model), whether it can be taken, no
    crash. Then a save / load (checkpoint): are the spawned objects in the loaded game? Note it (open point of R2).
111. Command bar: `instance.spawn sh_ei_combat_crate_a` works the same; `instance.spawn nosuch` -> "not in the object
    list"; `[Radial] Spawn=0` again afterwards.

0.10.1 additions (radial menu as a menu, Freeze, quit sector, Tests level; built with `-OutDir work\asi\menu0101`,
profile `regress_shadowlara_50l_radial2`; install with `Set-TruMenu.ps1 -Install -SourceDir .\work\asi\menu0101` - also
copies `TruMenu.tour.txt`). Section "Radial menu (0.10.1)". Tests 93 - 104 above describe `[Radial] Mode=wheel` now.

112. Start: `TruMenu.log` "0.10.1 radial: mode menu (...), freeze world ..., quit sector 1 (built in), tests level 1
    (tour 38 stops / entries) ..." and "radial: tour 38 entries from ...TruMenu.tour.txt (0 dropped, 0 unknown, 0 lines
    skipped)" (34 with the tour file of the first 0.10.1 build); Settings page lists the 15 `[Radial]` keys.
113. In a level **hold** L3 + R3 0.5 s: the ring with Cheats, Marken, Zeit, Waffen, Spieler, Objekte, Tests, Spiel
    beenden (8 sectors); **let go** - it stays open, nothing runs.
114. **Left stick** to Zeit, let the stick go - Zeit stays picked; nothing runs. **A** -> the Zeit level. D-pad right /
    left steps through the entries. A on "Zeitlupe 0.5" -> runs (`radial: Zeit -> time.scale 0.5`), the ring stays.
115. **B** -> top level (Zeit picked), **B** -> closed. Hold L3 + R3 again -> it opens in the top level with Zeit lit;
    **L3 + R3** again -> closed. Lara never moved, the camera never turned, A / B never reached the game.
116. Freeze world (TO TEST switch `radial-freeze` on = `[Radial] Freeze=1`): open the ring next to a thrall / moving
    water -> everything stands still while it is open, runs on after the close (`radial: freeze world - time.pause bit
    set by the ring`, `... released`). Switch `radial-freeze` off, open again -> the world keeps running.
117. Freeze on: Zeit -> "Welt einfrieren" shows **on** -> A (off) -> the world runs in the open ring and stays running
    after the close (the user's choice). Freeze off: A on it (on) -> close -> the world stays frozen; open, A (off).
118. Spawn while frozen (only with `radial-spawn`, after "Back up all saves now"): Objekte -> Medipack -> TruMenu.log
    `instance.spawn: g_healthpack ... born at Lara` while the world stands; it moves / can be taken after the close.
119. **F9 tapped** -> ring; the mouse moves the pick; **Enter** / left click runs; Backspace = back; **F9** again closes.
    The game never saw F9 / Enter / Backspace.
120. Top level **Spiel beenden**: A -> red, "A nochmal = beenden (10 s)" counting down; wait 11 s -> disarmed (log
    `game.quit (radial sector): disarmed - 10 s passed`). A, then the stick to another sector -> disarmed ("the pick left
    the sector"). A, then B -> disarmed ("B") and closed. A, then L3 + R3 -> disarmed ("ring closed").
121. Tests -> `TO TEST n/m offen` -> a row -> Hint (text under the ring), Run (if offered), OK / Done -> back in the
    list, the row is gone, the TO TEST page shows it marked (`tests: test.mark ...`). Tests -> Schalter -> `radial-freeze`
    toggles on / off as the page's checkbox. Tests -> Regression -> DLC 2 -> a check -> OK (`regress: ...` line,
    `TruMenu.regress_results.txt`). Tests -> Prepare -> one shortcut runs (ring closes). Tests -> Rundgang -> Maschinenraum
    -> "Laden dlc2_machine_room" (ring closes); after the load reopen -> "10 Maschinensaeule" -> Lara at the column.
    Tests -> Rundgang -> **Versteckt** shows `Laden dlc_dungeon`, `26 Goldene Schrotflinte ...`, `27 container1: ...
    (Saves sichern!)`, `28 Erweitertes Ende (Saves sichern!)` - run 27 / 28 only after "Back up all saves now", in a
    run of its own (workspace `docs\Versteckte-Inhalte-Rundgang.md`).
122. **Last step - ends the game:** top level Spiel beenden, A (red), A again within 10 s (or hold A 1 s) -> the game
    ends; `TruMenu.log` `game.quit (radial sector): confirmed by the owner ...` then `game.quit by the owner (TruMenu)
    ...`; the run summary says "ended via TruMenu game.quit (exit code 0x544D, not a crash)".

## Ideas

- **`[Test] SkipHintBoxes`** (research only, nothing built): the DLC 2 hint boxes come from the ported generalbank script
  9 (`popUpTitleMessage`, TU script 10; `docs/Befund-Test33-Native.md`): it pauses the game until A (Xenia reference: DLC
  2 hints modal with pause, DLC 1 top right without). Known from that finding: script 9 inherits from script 93
  (`uiscreen`); its f7 lies near the "paused" string and calls the replaced `dlc2data` f1(0), f8 calls f1(1), f9 reads
  f0 and calls f1(0); its external calls include `inputaction` f0 and `uiscreen` f90 / f91 / f99. Not yet found: which
  native / engine flag the modal box uses to pause the game (candidates, unverified: a `uiscreen` modal flag, a
  `uigamedata` pause native, streamFlags) and which call closes it on A. Next step: disassemble script 9 f7 / f8 / f9
  (`tools/menu_dlc_probe.py`, `script_func_list.py`) and map their `op65` calls to exe natives as done for f22 / f27
  above; an auto-confirm could then run the close path's natives on the game thread while the box is up - only with
  byte checks and as a test option.
- The DirectInput mouse device (input manager +0x28, wrapper 0x485ae0) could be held the same way as the keyboard if a
  live test ever shows mouse clicks reaching the game while the menu is open.

## Credits

- **Dear ImGui** by Omar Cornut and contributors (MIT), unmodified in `src/asi/third_party/imgui`.
- **TheIndra55/TRLAU-menu-hook** (GPL v3, <https://github.com/TheIndra55/TRLAU-menu-hook>) was **read as a reference
  only** (2026-10-31, raw.githubusercontent.com): the TR8 addresses / signatures / flags marked "TRLAU" above (GameTracker
  layout, Instance position offset, INSTANCE_Post, CAMERA_SetMode / restore, cheatMode + message 12,
  GAMELOOP_RequestLevelChangeByName; 0.3: timeDilation, streamFlags 0x1000, player control byte, message 4 / 3,
  UI hidden byte, camera fov offset, instance list / offsets, message 7, INSTANCE_ReallyRemoveInstance, the costume
  switch native 0x79db50 + message 35, the script print natives, the markup flag bit names, z > 16 for drawing) come
  from it. No code or structure of it is used; TruMenu's hooks (import filter
  for the pad, device-vtable patch found through the game's own device manager) are our own and differ from its
  approach (an inline hook of the game's D3D init function and the game's frame callbacks).
- Camera manager / mode facts cross-checked in `docs/Befund-Entwicklerkanal.md` of the project.
- The **developer menu** is Crystal Dynamics' own data in `tru.exe` (labels, limits, targets, callbacks); TruMenu only
  reads and draws it. Its format was decoded by us (`tools/devmenu_dump.py`); weapons / ammo / health facts are from
  the project's static pass (catalog section 17).

License: MIT, as the repository.
