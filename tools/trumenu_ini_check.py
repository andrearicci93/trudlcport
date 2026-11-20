"""Check that the shipped src/asi/TruMenu/TruMenu.ini is exactly the text TruMenu writes from its defaults table
(kOpts in TruMenu.cpp, DefaultIniText) - read-only. Since TruMenu 0.8 also the regression lists tests/regress/*.txt
(TruMenu.tests.txt row format, 8 tab-separated columns; step ids step<n> = number; ids unique; every check id named in
backticks in its source doc docs/Regression-DLC1.md / docs/Regression-DLC2.md; ASCII only).
Since TruMenu 0.8.1 a row may have a 9th column "shortcut" (Prepare button / regress.prepare): ';'-separated commands,
optional first element "#title"; checked: at most 12 commands, 319 characters, every command starts with an item id of
kItems in TruMenu.cpp, no game.quit, level.load takes one unit name (a-z 0-9 _ -), bool items take 0 / 1.
Since TruMenu 0.10 also the radial menu file src/asi/TruMenu/TruMenu.radial.txt ("path | label | item id [arg]"):
ASCII only, first line "# TruMenu radial menu", three fields, path segments / labels at most 47 characters, every item
id in kItems (dev.<slug> rows are only known at run time and are accepted), none of the ids TruMenu never offers in the
ring (kRadForbidden in TruMenu.cpp - the list here must be the same: game.quit, cmd.run, save.*, settings.reset), bool
items take 0 / 1, instance.spawn / level.load one name, the limits of TruMenu.cpp (256 entries, 48 levels, 64 per level).
Since TruMenu 0.10.1 also the tour file src/asi/TruMenu/TruMenu.tour.txt (written by tools/tour_from_rundgang.py; the
same format and rules, first line "# TruMenu tour", its levels below Tests/Rundgang), the [Radial] values of the INI
(Mode menu / wheel, Freeze world / player / 0 / 1 / 2, QuitSector and TestsLevel 0 / 1; since 0.10.3 FreezeSound
0 / 1, since 0.10.4 FreezeShaderClock 0 / 1) and the limits with the built-in entries of Mode=menu (top level + "Tests" + "Spiel beenden", Tests = 4 virtual
folders + Rundgang + 1 slot).
Since TruMenu 0.10.5 also the [Shot] values (Enabled / Clean 0 / 1, Hotkey a virtual key 0 .. 0xFE as hex or decimal,
MaxPerMinute 0 .. 120, Folder without < > " | ? *), the ids shot.save / shot.status / claude.mark in kItems, the six
Claude marks of the radial file (level "Claude" on the top level: claude.mark now / good / bug / gfx / sound / stutter,
no other item there) and the exports TruMenuShot / TruMenuMark in TruMenu.cpp.
Since TruMenu 0.11 also the [Flow] values (Enabled / Overlay / AutoAdvance 0 / 1, Position tl / tr / bl / br, Size 0.5 ..
3, Lines 1 .. 3, ToastSeconds 1 .. 30, PollMs 100 .. 5000, File), the flow items in kItems, the include of TruFlowCore.h,
and the flow entries flow.next / flow.skip / flow.back / flow.status (no argument, once each) allowed in the level Claude
next to the six marks (which keep their order).
Since TruMenu 0.12 also the [Debug] values (Enabled / NavMask 0 / 1, NavDraw a comma list of the switch names of
kNavSwitches in TruMenu.cpp), the items nav.status / nav.draw / nav.mask / nav.off in kItems and the nav.* entries of the
radial file (nav.draw takes exactly one switch name of kNavSwitches, nav.mask / nav.off / nav.status no argument).
Since TruMenu 0.13 also the [Debug] label values (Labels / LabelCross 0 / 1, LabelRadius 100 .. 50000, LabelMax 1 .. 32,
LabelMatch a comma list of name parts a-z 0-9 _ or *), the item dbg.labels in kItems and exactly one dbg.labels entry
in the radial file (no argument).
Since TruMenu 0.14 (2026-11-06 TruMenu 0.14 triggers) also the [Debug] debug view values (View / Triggers / Trg* /
Portals / Checkpoints / TrgLabels / Legend / Markup / Persist 0 / 1, TriggerMax 1 .. 256, TriggerRadius 500 .. 200000,
TriggerLabelMax 0 .. 64, ViewNav a comma list of kNavSwitches names), the items dbg.view / dbg.triggers / dbg.show /
dbg.portals / dbg.checkpoints / dbg.legend / dbg.status in kItems, every layer of kDvLayers once in the radial file
(dbg.show <layer> or its own bool item) and dbg.show taking exactly one layer name of kDvLayers; the object name keys
(Names / NameIds 0 / 1, NameMatch a comma list or empty, NameRadius 100 .. 200000, NameMax 1 .. 64, NameScale 0.5 .. 3,
NameColour RRGGBB), the items dbg.names / dbg.namefilter / dbg.namecolour / dbg.namesize and their ring arguments.
Since TruMenu 0.15 (2026-11-06 TruMenu 0.15 render mode) also the render mode keys (Slide / EnemyColl / Census / Flat /
FlatModels / FlatEdges / FlatAnyTarget 0 / 1, CollRadius 500 .. 200000, CollMax 100 .. 20000, CensusFrames 10 .. 1200,
FlatPasses a hex / decimal mask of the pass ids 0x200 0x100 0x80 0x400 0x800 1 2 (0xf83), FlatColour material / class),
kDvLayers with 15 layers (slide / enemycoll have their own items dbg.slide / dbg.enemycoll), the items dbg.census /
dbg.flat / dbg.flatpass / dbg.flatpasses / dbg.flatcolour / dbg.flatmodels / dbg.flatedges / dbg.flatanyrt / dbg.render /
dbg.slide / dbg.enemycoll in kItems and their ring entries: each switch once without an argument, dbg.flatpass once per
pass id, dbg.flatcolour once for material and once for class, dbg.flatpasses with census / default / a mask.
Since TruMenu 0.16 (2026-11-06 TruMenu 0.16 readability) also the display keys (Fade / Fill / LabelShort / LaraIn 0 / 1,
Depth 0 .. 2, DepthDim 5 .. 80, DepthCall 0 .. 7, LineAlpha 10 .. 100, LineBright 30 .. 150, FadeStart 0 .. 100000,
FadeEnd 500 .. 200000, FadeMin 0 .. 100, FillAlpha 2 .. 40, ViewLabelMax 0 .. 64, Enclosing 0 .. 2, EnclosingSize 100 ..
100000, MarkerMax 2 .. 50, TriggerMax now 1 .. 512, ViewSkip a comma list of kDvLayers names or empty), the items
dbg.depth / dbg.alpha / dbg.bright / dbg.fade / dbg.fill / dbg.short / dbg.larain / dbg.enclosing / dbg.style in kItems
and their ring entries (dbg.depth once each for on / dim / off, dbg.enclosing once each for normal / dim / hide,
dbg.alpha 10 .. 100, dbg.bright 30 .. 150, the switches once without an argument) and the flight entries of the ring
(cheat.flight once without an argument, cheat.speed with a number 0 .. 1000).
Since TruMenu 0.17 (2026-11-06 TruMenu 0.17 quick toggles) also DepthCall -1 .. 7, the [Quick] keys (Enabled / ShowClosed
0 / 1, OpenButtons a mask without D-pad / LB / RB, ChordMs 50 .. 1000, Language de / en, Top 5 .. 80, Scale 0.5 .. 3),
[Shot] OnCine 0 / 1, OnCinePairs / OnCineFastPairs 1 .. 50, OnCineIntervalMs 250 .. 10000, OnCineSlowMs 250 .. 60000,
OnCineSignal cine / camera / both, [Debug] CheckpointHide (intro ids or empty), the items quick.* / shot.oncine /
dbg.depthdump / dbg.cp* / pos.* in kItems, the quick-toggle bar's row tables kQbDebug .. kQbAi (every item id in kItems,
bool rows on bool items or dbg.show <layer>, value rows on the value items, every kDvLayers layer reachable) and the new
ring entries (quick.open / shot.oncine / dbg.depthdump / dbg.cplist / dbg.cpall 0 / dbg.cpall 1 once each).
Since TruMenu 0.18 (2026-11-06 TruMenu 0.18) also [Menu] OverlayLaraIn / [Debug] LegendLaraIn / [Saves] DirectLoad /
[Shot] OnCineSegments 0 / 1, the items overlay.larain / pos.goload / save.load in kItems, save.load in kRadForbidden (and
never in the ring), the bar's row tables kQbEmergency .. kQbAccess (new kinds: info rows on info items, choice rows on
action items, label / planned rows with id "-" and a planned row's text "German|English"; kQfConfirm / kQfBackup rows
are actions; level.load rows take one unit name a-z 0-9 _; time.scale is a value item), the ring's overlay.larain once
(no argument), pos.goload with a saved name or last, time.scale with a number 0 .. 10.
Since TruMenu 0.19 (2026-11-06 TruMenu 0.19 dumb AI) also the [AI] keys (Dumb 0 .. 2, DumbFilter a comma list of name
parts a-z 0-9 _ or empty, DumbMode purge / gate, NoInvestigate / NoAttack 0 / 1), every INI comment shorter than 512
characters (DefaultIniText cuts there), the items ai.dumb / ai.mode / ai.noinvestigate / ai.noattack / ai.status in
kItems, the presets of kAiPresets (all / sharks / spiders / thralls) plus filter, bool rows "ai.dumb <preset>" in the bar
(the only bool rows with an argument besides dbg.show), ai.mode as a value row, the ring's ai.dumb entries (exactly one
preset word, all / sharks / spiders each at least once, sharks / spiders also in Spieler/Barrierefreiheit), ai.noinvestigate
/ ai.noattack / ai.status once each without an argument, the Barrierefreiheit bar page without the planned row "Haie",
and the 0.19 precheck tables kAiChecks / kAiGateChecks / kAiBitChecks present with at most 64 bytes per check.
Since TruMenu 0.20 (2026-11-06 TruMenu 0.20) also 17 layers (collect / enemies with their own items dbg.collect /
dbg.enemies), [Debug] Collect / Enemies 0 / 1, MarkRadius 500 .. 200000, MarkMax 1 .. 64, [Media] MuteMusic / MuteAmbient
0 / 1, the defaults DumbMode gate / Depth 2 / FlatPasses 0x600 in kOpts, the items dbg.collect / dbg.enemies /
media.mutemusic / media.muteambient / pos.portal, the owner's bar rows (Leveldaten collectibles; Render / KI enemies,
enemy health, edges; Zeit / Test music / ambience off; game.quit as the last plain action row of Notfall), the ring's
dbg.collect / dbg.enemies / media.mutemusic / media.muteambient once without an argument (pos.portal never), and the
precheck tables kCoChecks / kAiForgetChecks / kSndMusicChecks with at most 64 bytes per check.
Since TruMenu 0.20.1 (2026-11-06 sound list) also the [Sound] values (List / OnlyPlaying / ShowMusic / ShowSfx /
ShowSpeech / ShowOther 0 / 1, Position bl / tl / tr / br, MaxLines 1 .. 40, RefreshMs 100 .. 10000, Sort group / volume /
name, FontScale 0.5 .. 3) and [Debug] EnemyStateLog 0 / 1, the snd.* items in kItems (snd.dump on the game thread),
snd.pos / snd.lines / snd.sort as value rows, the bar rows on Debug / Darstellung (every snd.* switch) and Zeit / Test
(snd.list, snd.dump), the ring's snd.* entries (snd.list in Zeit and Spieler/Debug/Ton, the four corners once each,
snd.dump once, snd.sort group / volume / name, snd.lines 1 .. 40, bool / info / dump entries without argument), the
precheck tables kSnChecks / kSmChecks / kEsChecks with at most 64 bytes per check, and SndMuteTick trying the FMOD group
mute (g_smOk / SmMuteOn) before the 0.20 SOUND_SetMusicVolume path.
Since TruMenu 0.21.3 (2026-11-07 quick bar X / Y, sound list width) also: kQbOwn = 0xC30F (D-pad / LB / RB + X / Y; a
[Quick] OpenButtons holding X or Y is refused like D-pad / LB / RB), QuickTick takes Y before X before left / right,
QbExecRow (value rows never run, bool rows toggle from QbRowOn, the rest = the right press), QbFavPin (rows with an
argument refused before FavSet, no other write of the favourites), the footer "X: ausfuehren  Y: Favorit" (DE / EN) and
the confirmation text "rechts / X nochmal", TruMenuPadBlock unchanged in meaning (kQbOwn while open, bits 16 / 17 / 18),
the [Quick] Enabled / OpenButtons comments naming X / Y, SnRow aligned to the frame's widest row (no
GetContentRegionAvail in SnRow; DrawSoundList measures every row before it draws one).
Since TruMenu 0.21.4 (2026-11-07 hall02 counter) also: the items fix.hall02 (action, game thread; help text names the
saves whose checkpoint 11258 already holds thralls) and thrall.scriptval (action, not on the game thread, read only);
the page Tests rows (fix.hall02 = action with kQfConfirm, thrall.scriptval); RunFixHall02's guards in order (unit
hall02, dispatcher values present, broken refused, a living object-1004 thrall refused - all before the first
sticky.set), tutorial before population, the 18509 rule (only when below 2), exactly two sticky.set calls and no other
write, the reply naming the arena trigger 11268 and "Betreten / Verlassen"; H2Alive (present, kill flag, AkDying = the
four death states, RegenerateDeath not among them); H2ValueAddr ([inst+0x60] -> +0xc -> +8, zero pointers refused);
H2IsThrall by object id 1004 and name; thrall.scriptval without any write; no E3 safety net (no [Fix] Hall02Restore,
no H2Tick / fix.hall02restore - docs/Befund-Hall02-TU-Vergleich-0711.md: a PC data bug, the Xbox never restores
thralls there); the precheck table kH2Checks (whole bytes, at most 64, no foreign byte); no code patch and no direct
store in the section (no WriteDword / VirtualProtect / volatile write).

Since TruMenu 0.21.5 (2026-11-07 Fixes + frozen ring) also the switches file src/asi/TruMenu/TruMenu.switches.txt
(first line "# TruMenu switches", ASCII, group lines "group | key | DE | EN [| open]", switch lines "Plugin | Section |
Key | bool / int:lo..hi[:step] / choice:a,b | DE | EN | live / restart / live-if:<Key> | default | hint [| since]",
at most 512 rows / 24 groups (0.22.23; was 160 rows), no key twice): every key in its shipped plugin INI (src/asi/<Plugin>/<Plugin>.ini) with
the default = the INI value (a row whose "since" version is newer than the plugin source may wait), the INI value
fits the type, every live / live-if row has the plugin re-read function of SW_LIVE (body holds the section and key
literals), no restart row is re-read, every key of the eight plugin INIs has a row (text filters excepted); the items
sw.set / sw.list / sw.reload (not game thread), page Fixes, RunSwSet order (listed key, value fits, INI exists,
value changed, then the one write), the marker in SwLoadLocked, Y refused on page Fixes, X with kQbXDir, the menu
sections PageSwitches / PageQbAll, Build-TruAsi.ps1 / Set-TruMenu.ps1 copy the file; the frozen ring: its header
says so ("aktuell nicht weiter gemacht"), at most 172 entries, every entry is a bar row (ring_parity: bool rows take
0 / 1 / no argument, value rows their steps, choice rows their choices, other rows the same argument).
0.22.23 (Q39, switches file limit): SW_MAX 512 = kSwMax of TruMenu.cpp (was 160), the loader names lines over the
limits in TruMenu.log (no silent cut), the page Fixes head names rows it cannot hold, the switches file's own header
says 512, and the page model of the shipped file: group rows + the largest group <= kQbViewMax (128) - else the open
group would be cut on the bar page (split the group).
0.22.24 (Q36, fall watch / fall net): check_02224 - kFwChecks / kCtChecks rows, FwCheck before any chart read, the
fall watch rules and constants, FallNetTick's order (time, count, sample, height, pause, switch, then UnstuckPlace),
RunUnstuck and the net share UnstuckPlace, [Rescue] FallNet in kOpts / ReadOptions / FnReadSwitch / the INI, the one
TruMenu switch row (SW_ROW_ONLY: TruMenu may have rows without every TruMenu.ini key being one), precheck_02224 = the
49 rows of precheck_02223 + kCtChecks + kFwChecks, Set-TruMenu.ps1 knows the 0.22.23 hash.
0.22.25 (Q45, settings.reset wrote a cut INI): check_02225 - no fixed char array in RunSettingsReset / DefaultIniText
that is not larger than the generated default text (the 0.10 .. 0.22.24 static 16384 vs ~42 KB), the measured build
(DefaultIniText(nullptr, 0), malloc, cut / write / close checked, built before the backup), IniPut / TextAdd measure
first; the texts built from TruMenu's tables against their buffers (table_texts: Log line vs light.cut, [Quick] Closed
with every group key, [Menu] OpenPages, [Cheats] State, [Debug] NavDraw, settings.show in t_value, [Quick] Recent),
QbGroupSet / CpPersist whole keys only, Set-TruMenu.ps1 knows the 0.22.24 hash.
0.22.26 (Q76, test arena): check_02226 - kAdmChecks rows (= work/asi/menu0249/precheck_02226.txt section 12), the
meter-full call only through AdmFillNow inside __try, adren.fill / adren.keep behind CheatGate, AdmTick in the per-frame
block, items adren.meter / adren.fill / adren.keep, ai.remove spawned through SpIsOurs (address + stamp +0x44, filled by
RunAiSpawn), the page Tests group ts_arena1 ("Arena 1 - Kampf") with the rows arena.go 1a / 1b / 1c, kArenas = units +
intro ids of the finding (spot key = arena number + letter, one list for later arenas),
arena.go = backup, unit.go, wait.unit, flight, player.goto <intro> force (refusals as cp.jump), no new INI key,
Set-TruMenu.ps1 knows the 0.22.25 hash.
Q75 (2026-11-11): SW_START_GATED - switches the plugin re-reads at run time only when they were 1 at the start
(TruShadowPower 0.27 [Camera] ShakeTuTimeStep / [Player] TuTimeStep): row "restart", the re-read function reads the key,
the hint names "live nur wenn 1 beim Start" // "live if 1 at start" (live-if:<own key> would be read after the write).
0.22.28 (Q90, test packages on page Tests): check_02228 - the block "TP Q90" of kQbTests (every row readable by qb_rows
and flagged kQfTp, kQfTp nowhere else), group tp_q90 + one closed kQfSub group per package A, 1 .. 9 with a hint and a
check, check ids tp<package>.<name> unique and in their package, switch rows only keys of TruMenu.switches.txt, the
row kinds kQbCheck / kQbSwitch / kQbNote handled in view / action / X / help / long menu and refused as favourites,
the bar's TO TEST list skips the tp ids, no new INI key; check_018 accepts id "-" on kQbNote rows; check_02227 looks
for its kVersion part; Set-TruMenu.ps1 knows the 0.22.27 hash.
Options: --switches FILE checks that file instead of the shipped one.

Usage (from the repository root):
  ../bin/pyt -t 60 tools/trumenu_ini_check.py            compare + list check, print the first difference / every
                                                         list problem; exit 1 on a mismatch
  ../bin/pyt -t 60 tools/trumenu_ini_check.py --print    print the text generated from the table
  options (negative tests on copies): --ini FILE, --radial FILE, --tour FILE check that file instead of the shipped one;
  since 0.19 also --cpp FILE (a copy of TruMenu.cpp: the table rules of the bar, kItems, kAiPresets, the precheck tables)
"""
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CPP = os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'TruMenu.cpp')
INI = os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'TruMenu.ini')
# 0.22.6 (2026-11-09): TruMenu's German texts carry umlauts as octal UTF-8 escapes (tools/trumenu_umlauts.py); the checks
# below compare with the ASCII spelling, so the source is read with those escapes turned back into ae / oe / ue / ss
# (a text with umlauts then counts 2 characters per umlaut - stricter than on screen)
UMLAUT_ESCAPES = {r'\303\244': 'ae', r'\303\266': 'oe', r'\303\274': 'ue', r'\303\204': 'Ae', r'\303\226': 'Oe',
                  r'\303\234': 'Ue', r'\303\237': 'ss'}


def read_cpp():
    src = open(CPP, 'r', encoding='utf-8').read()
    for esc, ascii_text in UMLAUT_ESCAPES.items():
        src = src.replace(esc, ascii_text)
    return src
REGRESS = {'dlc1.txt': 'Regression-DLC1.md', 'dlc2.txt': 'Regression-DLC2.md'}
RADIAL = os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'TruMenu.radial.txt')
TOUR = os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'TruMenu.tour.txt')
RADIAL_FORBIDDEN = ['game.quit', 'cmd.run', 'save.delete', 'save.restore', 'save.import', 'settings.reset', 'save.load']
RADIAL_VALUES = {'Mode': ('menu', 'wheel'), 'Freeze': ('world', 'player', '0', '1', '2'), 'QuitSector': ('0', '1'),
                 'TestsLevel': ('0', '1'), 'FreezeSound': ('0', '1'), 'FreezeShaderClock': ('0', '1')}
SHOT_VALUES = {'Enabled': ('0', '1'), 'Clean': ('0', '1')}       # 0.10.5; Hotkey / MaxPerMinute / Folder in check_shot
CLAUDE_KINDS = ['now', 'good', 'bug', 'gfx', 'sound', 'stutter']
# 0.11 Ablauf: [Flow] values, the flow items, the flow entries allowed directly in the ring level Claude
FLOW_VALUES = {'Enabled': ('0', '1'), 'Overlay': ('0', '1'), 'AutoAdvance': ('0', '1'),
               'Position': ('tl', 'tr', 'bl', 'br')}
FLOW_RANGES = {'Size': (0.5, 3.0), 'Lines': (1, 3), 'ToastSeconds': (1, 30), 'PollMs': (100, 5000)}
FLOW_ITEMS = ['flow.status', 'flow.list', 'flow.next', 'flow.back', 'flow.skip', 'flow.goto', 'flow.add', 'flow.say',
              'flow.result', 'flow.reload']
FLOW_RING = ['flow.next', 'flow.skip', 'flow.back', 'flow.status']
# 0.12 Debug-Zeichnung: the nav items and their types
NAV_ITEMS = {'nav.status': 'info', 'nav.draw': 'action', 'nav.mask': 'bool', 'nav.off': 'action'}
# 0.13 Thrall-Labels: the [Debug] label keys, their ranges, the item
LABEL_KEYS = ('Labels', 'LabelRadius', 'LabelMax', 'LabelMatch', 'LabelCross')
LABEL_RANGES = {'LabelRadius': (100, 50000), 'LabelMax': (1, 32)}
LABEL_ITEMS = {'dbg.labels': 'bool'}
# 0.14 debug view: the [Debug] keys (0 / 1 or ranges), the items, the layers that have a bool item of their own
DV_BOOL_KEYS = ('View', 'Triggers', 'TrgDeath', 'TrgFire', 'TrgCheckpoint', 'TrgWater', 'TrgSound', 'TrgVolume',
                'TrgPlane', 'TrgUnknown', 'Portals', 'Checkpoints', 'TrgLabels', 'Legend', 'Markup', 'Persist', 'Names',
                'NameIds',
                'Slide', 'EnemyColl', 'Census', 'Flat', 'FlatModels', 'FlatEdges', 'FlatAnyTarget',   # 0.15
                'Fade', 'Fill', 'LabelShort', 'LaraIn',                                              # 0.16
                'Collect', 'Enemies')                                                                # 0.20
DV_RANGES = {'TriggerMax': (1, 512), 'TriggerRadius': (500, 200000), 'TriggerLabelMax': (0, 64),
             'NameRadius': (100, 200000), 'NameMax': (1, 64), 'NameScale': (0.5, 3),
             'CollRadius': (500, 200000), 'CollMax': (100, 20000), 'CensusFrames': (10, 1200),   # 0.15
             'Depth': (0, 2), 'DepthDim': (5, 80), 'DepthCall': (-1, 7), 'LineAlpha': (10, 100),  # 0.16 (0.17: -1 auto)
             'LineBright': (30, 150), 'FadeStart': (0, 100000), 'FadeEnd': (500, 200000), 'FadeMin': (0, 100),
             'FillAlpha': (2, 40), 'ViewLabelMax': (0, 64), 'Enclosing': (0, 2), 'EnclosingSize': (100, 100000),
             'MarkerMax': (2, 50),
             'MarkRadius': (500, 200000), 'MarkMax': (1, 64)}                                       # 0.20
DV_FLOAT_KEYS = ('TriggerRadius', 'NameRadius', 'NameScale', 'CollRadius',     # the others are whole numbers
                 'FadeStart', 'FadeEnd', 'EnclosingSize',                      # 0.16
                 'MarkRadius')                                                 # 0.20
DV_ITEMS = {'dbg.view': 'bool', 'dbg.triggers': 'bool', 'dbg.show': 'action', 'dbg.portals': 'bool',
            'dbg.checkpoints': 'bool', 'dbg.legend': 'bool', 'dbg.status': 'info', 'dbg.names': 'bool',
            'dbg.namefilter': 'action', 'dbg.namecolour': 'action', 'dbg.namesize': 'action',
            # 0.15 render mode
            'dbg.census': 'action', 'dbg.flat': 'bool', 'dbg.flatpass': 'action', 'dbg.flatpasses': 'action',
            'dbg.flatcolour': 'action', 'dbg.flatmodels': 'bool', 'dbg.flatedges': 'bool', 'dbg.flatanyrt': 'bool',
            'dbg.render': 'info', 'dbg.slide': 'bool', 'dbg.enemycoll': 'bool',
            # 0.16 readability
            'dbg.depth': 'action', 'dbg.alpha': 'action', 'dbg.bright': 'action', 'dbg.fade': 'bool', 'dbg.fill': 'bool',
            'dbg.short': 'bool', 'dbg.larain': 'bool', 'dbg.enclosing': 'action', 'dbg.style': 'info',
            # 0.20 collectibles / enemies
            'dbg.collect': 'bool', 'dbg.enemies': 'bool'}
# 0.16: ring entries with a fixed set of arguments (each once), percent presets, switches without an argument (once)
DP_RING_ARGS = {'dbg.depth': ('on', 'dim', 'off'), 'dbg.enclosing': ('normal', 'dim', 'hide')}
DP_RING_PERCENT = {'dbg.alpha': (10, 100), 'dbg.bright': (30, 150)}
DP_RING_SWITCHES = ('dbg.fade', 'dbg.fill', 'dbg.short', 'dbg.larain', 'dbg.style')
DV_OWN_ITEM = {'portals': 'dbg.portals', 'checkpoints': 'dbg.checkpoints', 'legend': 'dbg.legend', 'names': 'dbg.names',
               'slide': 'dbg.slide', 'enemycoll': 'dbg.enemycoll',
               'collect': 'dbg.collect', 'enemies': 'dbg.enemies',                                  # 0.20
               'keyitems': 'dbg.keyitems'}                                                          # 0.22.37
# 0.15: the pass ids of the flat view (kRmPassNames in TruMenu.cpp), their mask, the ring switches without an argument
RM_PASSES = ('0x200', '0x100', '0x80', '0x400', '0x800', '1', '2')
RM_PASS_ALL = 0xf83
RM_RING_SWITCHES = ('dbg.flat', 'dbg.census', 'dbg.flatedges', 'dbg.flatmodels', 'dbg.flatanyrt', 'dbg.render')
DV_LAYER_COUNT = 18                          # 0.20: + collect, enemies; 0.22.37: + keyitems
# 0.22.37: layers added after the ring was frozen (0.21.5, TruMenu.radial.txt line 11: no new ring entries) - bar + menu only
DV_RING_FROZEN = ('keyitems',)
# 0.17 quick toggles: [Quick] keys / ranges, the buttons the open bar owns, [Shot] OnCine ranges, the new items, the row
# tables of the bar and the items a value row may use
QB_KEYS = ('Enabled', 'OpenButtons', 'ChordMs', 'ShowClosed', 'Language', 'Top', 'Scale')
QB_RANGES = {'ChordMs': (50, 1000), 'Top': (5, 80), 'Scale': (0.5, 3)}
QB_OWN = 0xC30F                              # D-pad / LB / RB (0.17) + X / Y (0.21.3)
OC_RANGES = {'OnCinePairs': (1, 50), 'OnCineFastPairs': (1, 50), 'OnCineIntervalMs': (250, 10000),
             'OnCineSlowMs': (250, 60000)}
QB_ITEMS = {'quick.open': 'bool', 'quick.lang': 'action', 'quick.status': 'info', 'shot.oncine': 'bool',
            'dbg.depthdump': 'action', 'dbg.cp': 'action', 'dbg.cpall': 'action', 'dbg.cplist': 'info',
            'dbg.cpgo': 'action', 'pos.save': 'action', 'pos.list': 'info', 'pos.go': 'action'}
# 0.22.16: kQbEmergency merged into kQbRescue, kQbRenderMore into kQbRender; new kQbSettings, kQbEnemies
QB_TABLES = ('kQbSettings', 'kQbRescue', 'kQbLara', 'kQbEnemies', 'kQbLevel', 'kQbRender', 'kQbDebug', 'kQbTimeTest',
             'kQbTests', 'kQbChapters', 'kQbAccess',
             'kQbCoop')                                                          # 0.21 Koop (planned rows only)
QB_VALUE_ITEMS = ('dbg.depth', 'dbg.alpha', 'dbg.bright', 'dbg.enclosing', 'cheat.speed', 'dbg.flatpasses', 'quick.lang',
                  'time.scale', 'ai.mode',                                       # 0.19 ai.mode
                  'snd.pos', 'snd.lines', 'snd.sort',                            # 0.20.1 sound list
                  'cam.shakescale', 'cam.rumble',                                # 0.21 camera shake / rumble
                  'ai.spawncount', 'ai.spawnat',                                 # 0.21.1 enemy spawn
                  'snd.vol.ambience', 'snd.vol.steps', 'snd.vol.weapons',       # 0.21.8 sound group sliders
                  'snd.vol.enemies', 'snd.vol.lara', 'snd.vol.objects', 'snd.vol.dlc2', 'snd.vol.hud',
                  # 0.22.16 page Spiel-Einstellungen (sub.lang cycles; gfx.r.* = greyed placeholders with their value)
                  'sub.lang', 'sub.size', 'sub.boxalpha', 'sub.colour', 'sub.pos', 'game.vol.music', 'game.vol.sfx',
                  'game.vol.voice', 'game.mouse', 'gfx.filter', 'gfx.aspect', 'gfx.r.vsync', 'gfx.r.triple', 'gfx.r.aa',
                  'gfx.r.mode', 'gfx.r.fullscreen', 'gfx.r.present2',
                  # 0.22.18 subtitle alignment, voice language, frame-step rate
                  'sub.valign', 'sub.halign', 'sub.margin', 'voice.lang', 'cine.steprate',
                  'menu.attracticon',                                            # 0.22.40 (Q126b) styles 0 .. 7
                  'sonar.fade', 'sonar.area',                                    # 0.22.51 S5
                  'sonar.tint',                                                  # 0.22.52 aus / ein / je Bereich
                  'snd.hear')                                                    # 0.22.53 W11 (kQvHear, arg = key)
# 0.18: the new items, the 0 / 1 keys, the bar pages (QbPage rows of kQbPages: 10 pages, special ones without a table)
Q18_ITEMS = {'overlay.larain': 'bool', 'pos.goload': 'action', 'save.load': 'action'}
Q18_KEYS = (('Menu', 'OverlayLaraIn'), ('Debug', 'LegendLaraIn'), ('Saves', 'DirectLoad'), ('Shot', 'OnCineSegments'))
QB_PAGES_MAX = 17                            # 0.21: + Koop; 0.21.1: + Favoriten / Zuletzt, Tests; 0.21.5: + Render-Details, Fixes;
                                             # 0.21.6: + Kostueme (16); 0.21.11: + Rettung (= g_qbRow[17], the limit)
# 0.21.6 (2026-11-07): bar page Kostueme, flight key line ([Cheat] FlightHint), quick command line
Q216_COS_NAMES = ('Classic Lara', 'Blue Bikini', 'Black and White Bikini', 'Red Bikini', 'Camo Bikini', 'Casual Explorer',
                  'Grey Jungle Shorts', 'Legend Lara', 'Bright Blue Bikini', 'Gold Bikini', 'Red Drysuit',
                  'Fashion Winner', "People's Choice", 'Grey Jungle Shorts', 'Grey Jungle Shorts', 'Blue Wetsuit')
Q216_COS_ITEMS = ('costume.set', 'costume.next', 'costume.choosereload')   # the only items the page runs
Q216_SETTLE = (300, 1000)                   # kCosSettleMs: "about 0.5 s" (owner / coordinator spec)
Q216_TOGGLE_ITEMS = ('nav.draw', 'dbg.flatpass', 'dbg.show', 'ai.dumb')   # "<item> <one word>" flips a flag
Q216_EXEC = ('InvokeCore(', 'CmdExecute(', 'QueueItem(', 'InvokeItem(', 'QbRun(', 'RunPending(', 'ShortcutStart(')
# 0.19 dumb AI: the items, the presets (kAiPresets + "filter"), the [AI] keys
Q19_ITEMS = {'ai.dumb': 'action', 'ai.mode': 'action', 'ai.noinvestigate': 'bool', 'ai.noattack': 'bool',
             'ai.status': 'info'}
AI_PRESETS = ('all', 'sharks', 'spiders', 'thralls')
AI_SETTINGS = AI_PRESETS + ('filter',)
AI_KEYS = ('Dumb', 'DumbFilter', 'DumbMode', 'NoInvestigate', 'NoAttack')
# 0.20: the new items, the [Media] mute keys, the bar rows the owner asked for (table, item, arg), the ring entries once
Q20_ITEMS = {'dbg.collect': 'bool', 'dbg.enemies': 'bool', 'media.mutemusic': 'bool', 'media.muteambient': 'bool',
             'pos.portal': 'action'}
Q20_MEDIA_KEYS = ('MuteMusic', 'MuteAmbient')
Q20_BAR = (('kQbLevel', 'dbg.collect', ''), ('kQbEnemies', 'dbg.enemies', ''), ('kQbEnemies', 'cheat.enemyhealth', ''),
           ('kQbRender', 'dbg.flatedges', ''), ('kQbSettings', 'media.mutemusic', ''),   # 0.22.16 pages
           ('kQbSettings', 'media.muteambient', ''), ('kQbRescue', 'game.quit', ''))
Q20_RING = ('dbg.collect', 'dbg.enemies', 'media.mutemusic', 'media.muteambient')
Q20_DEFAULTS = (('AI', 'DumbMode', 'gate'), ('Debug', 'Depth', '2'), ('Debug', 'FlatPasses', '0x600'))
# 0.20.1: the sound list - items, [Sound] keys (key, rule), bar rows (table, item, kind), check tables
Q201_ITEMS = {'snd.list': 'bool', 'snd.pos': 'action', 'snd.lines': 'action', 'snd.refresh': 'action',
              'snd.sort': 'action', 'snd.scale': 'action', 'snd.playing': 'bool', 'snd.music': 'bool', 'snd.sfx': 'bool',
              'snd.speech': 'bool', 'snd.other': 'bool', 'snd.dump': 'action', 'snd.status': 'info'}
SND_POS = ('bl', 'tl', 'tr', 'br')
SND_SORT = ('group', 'volume', 'name')
Q201_KEYS = (('List', 'bool'), ('Position', SND_POS), ('MaxLines', (1, 40)), ('RefreshMs', (100, 10000)),
             ('Sort', SND_SORT), ('FontScale', (0.5, 3.0)), ('OnlyPlaying', 'bool'), ('ShowMusic', 'bool'),
             ('ShowSfx', 'bool'), ('ShowSpeech', 'bool'), ('ShowOther', 'bool'))
Q201_BAR = (('kQbDebug', 'snd.list', 'kQbBool'), ('kQbDebug', 'snd.pos', 'kQbValue'),
            ('kQbDebug', 'snd.lines', 'kQbValue'), ('kQbDebug', 'snd.sort', 'kQbValue'),
            ('kQbDebug', 'snd.playing', 'kQbBool'), ('kQbDebug', 'snd.music', 'kQbBool'),
            ('kQbDebug', 'snd.sfx', 'kQbBool'), ('kQbDebug', 'snd.speech', 'kQbBool'),
            ('kQbDebug', 'snd.other', 'kQbBool'), ('kQbDebug', 'snd.dump', 'kQbAction'))
            # 0.22.16: the copies on Zeit / Test are gone (plan: the sound list stays on Debug / Darstellung)
Q201_TABLES = ('kSnChecks', 'kSmChecks', 'kEsChecks')
DV_NAME_COLOURS = ('white', 'yellow', 'cyan', 'magenta', 'weiss', 'gelb')
# 0.21: Arachnophobie / camera / ai.remove - items, game-thread items, [Arachno] / [Camera] keys (key, rule), defaults,
# bar rows (table, item, kind, arg), check tables, the planned rows they replace, the Koop page
Q21_ITEMS = {'arachno.on': 'bool', 'arachno.hide': 'bool', 'arachno.picture': 'bool', 'arachno.mute': 'bool',
             'arachno.list': 'action', 'arachno.status': 'info', 'cam.shakescale': 'action', 'cam.rumble': 'action',
             'cam.shakelist': 'action', 'cam.shake': 'action', 'cam.shakestate': 'info', 'ai.remove': 'action'}
Q21_GAME_THREAD = ('arachno.list', 'cam.shakelist', 'cam.shake', 'ai.remove')
Q21_ARACHNO_KEYS = (('Enabled', 'bool'), ('Hide', 'bool'), ('Picture', 'bool'), ('Mute', 'bool'), ('Match', 'list'),
                    ('Exclude', 'list0'), ('Image', 'png'), ('Scale', (0.2, 5.0)), ('MinPx', (4, 256)),
                    ('MaxScreen', (0.1, 1.0)), ('FadeNear', (0, 2000)), ('MaxDist', (500, 50000)),
                    ('WobbleAmp', (0.0, 0.5)), ('WobbleHz', (0.0, 10.0)), ('SquashAmp', (0.0, 0.5)), ('TiltDeg', (0, 45)),
                    ('Flip', 'bool'))
Q21_CAMERA_KEYS = (('ShakeScale', (0, 100)), ('Rumble', (0, 100)))
Q21_DEFAULTS = (('Arachno', 'Enabled', '0'), ('Camera', 'ShakeScale', '100'), ('Camera', 'Rumble', '100'),
                ('Sound', 'Position', 'br'))
Q21_BAR = (('kQbAccess', 'arachno.on', 'kQbBool', ''), ('kQbAccess', 'arachno.hide', 'kQbBool', ''),
           ('kQbAccess', 'arachno.picture', 'kQbBool', ''), ('kQbAccess', 'arachno.mute', 'kQbBool', ''),
           ('kQbAccess', 'cam.shakescale', 'kQbValue', ''), ('kQbAccess', 'cam.rumble', 'kQbValue', ''),
           ('kQbEnemies', 'ai.remove', 'kQbAction', 'others'))   # 0.22.16: page Gegner (KI)
Q21_TABLES = ('kArDrawChecks', 'kArSoundChecks', 'kCsChecks', 'kRbChecks', 'kLfChecks', 'kAdChecks')
Q21_REPLACED = ('Arachnophobie', 'Kamera-Wackeln aus')
AD_ARGS = ('nearest', 'others', 'all')
# 0.21.1 (2026-11-07): ai.kill, sticky, room check, physics bodies, enemy spawn, bar groups / page 0 / Tests page
Q211_ITEMS = {'ai.kill': 'action', 'sticky.get': 'action', 'sticky.set': 'action', 'unit.go': 'action',
              'phys.status': 'info', 'phys.dump': 'action', 'ai.spawn': 'action', 'ai.spawncount': 'action',
              'ai.spawnat': 'action', 'dbg.hpbar': 'bool', 'menu.hidecursor': 'bool'}
Q211_GAME_THREAD = ('ai.kill', 'sticky.set', 'phys.dump', 'ai.spawn')
Q211_NOT_GAME_THREAD = ('unit.go', 'sticky.get')   # unit.go starts a shortcut (render side); get only reads
Q211_QUICK_KEYS = (('Closed', 'groups'), ('RecentMax', (0, 16)), ('Recent', 'recent'))
Q211_GROUPS = (('ki_dumm', 'ai.dumb'), ('ki_spawn', 'ai.spawn'), ('ki_weg', 'ai.kill'))   # key, an item inside
Q211_TABLES = ('kAkChecks', 'kStChecks', 'kRkChecks', 'kPhChecks', 'kSpChecks', 'kHpChecks')
Q211_SWITCHES = (('Debug', 'EnemyHpBar', '1'), ('Menu', 'HideCursor', '0'))   # 0 / 1 keys and their defaults
# bytes other plugins patch at run time - never a TruMenu byte check: TruShadowCombat 0.6 (damage entry, switch bound,
# table operand), TruTrace's call bytes
Q211_FOREIGN = [(0x637590, 5), (0x63761b, 1), (0x637625, 4), (0x5b6a2f, 2)]
Q211_KILL_TYPES = '{6, 4, 2, 1, 0}'          # 6 RigidBody = the game's own Kill (0x63831c) first
TRUTRACE_BYTES = (0x5b6a2f, 0x5b6a30)        # the call TruTrace checks - never a TruMenu patch site
# 0.21.3 (2026-11-07): the bar's X / Y footer texts (DE, EN) and the confirmation text
Q213_FOOTER = ('"X: ausfuehren  Y: Favorit"', '"X: run  Y: favourite"')
Q213_CONFIRM = ('"rechts / X nochmal (3 s) = ausfuehren"', '"right / X again (3 s) = run"')
# 0.21.4 (2026-11-07): hall02 counter (fix.hall02, thrall.scriptval, [Fix] Hall02Restore)
Q214_ITEMS = {'fix.hall02': ('action', 'true'), 'thrall.scriptval': ('action', 'false')}
Q214_DROPPED = ('Hall02Restore', 'fix.hall02restore', 'H2Tick', 'H2RestorePass')   # E3, not built (coordinator 17:30)
Q214_REPLY = ('Arena-Trigger 11268', 'Betreten / Verlassen', 'arena trigger 11268', 'enter / leave')
LIT =re.compile(r'"((?:[^"\\]|\\.)*)"')


def item_types(src):
    """{item id: type} from the kItems table of TruMenu.cpp"""
    block = src[src.index('const Item kItems[] = {'):]
    block = block[:block.index('\n};')]
    return dict(re.findall(r'\{"([a-z][a-z0-9_.]*)", "([a-z]+)"', block))


def check_shortcut(where, text, items):
    """problems of one shortcut column (empty list = fine)"""
    out = []
    if len(text) > 319: out.append('%s: shortcut longer than 319 characters' % where)
    parts = [p.strip() for p in text.split(';') if p.strip()]
    if parts and parts[0].startswith('#'): parts = parts[1:]
    if not parts: out.append('%s: shortcut without a command' % where)
    if len(parts) > 12: out.append('%s: shortcut with %d commands, at most 12' % (where, len(parts)))
    for p in parts:
        if p.startswith('#'):
            out.append('%s: title "%s" must be the first element' % (where, p))
            continue
        word, _, arg = p.partition(' ')
        arg = arg.strip()
        if word == 'game.quit': out.append('%s: game.quit is never run by a shortcut' % where)
        elif word not in items: out.append('%s: unknown item id %s' % (where, word))
        elif word == 'level.load' and not re.fullmatch(r'[A-Za-z0-9_-]{1,63}', arg):
            out.append('%s: level.load needs one unit name, got "%s"' % (where, arg))
        elif items[word] == 'bool' and arg not in ('', '0', '1'):
            out.append('%s: %s is a bool item, arg "%s" (0 / 1)' % (where, word, arg))
    return out


def check_lists():
    """problems of tests/regress/*.txt (empty list = fine) and a summary per file"""
    problems, summary = [], []
    items = item_types(read_cpp())
    for name, doc in sorted(REGRESS.items()):
        path = os.path.join(ROOT, 'tests', 'regress', name)
        if not os.path.exists(path):
            problems.append('%s missing' % name)
            continue
        raw = open(path, 'rb').read()
        if any(b > 126 or (b < 32 and b not in (9, 10, 13)) for b in raw):
            problems.append('%s: non-ASCII bytes (the menu font has no umlauts)' % name)
        doc_text = open(os.path.join(ROOT, 'docs', doc), encoding='utf-8').read()
        doc_ids = set(re.findall(r'`([a-z0-9][a-z0-9-]+)`', doc_text))
        seen, steps, checks, shortcuts = set(), 0, 0, 0
        for n, line in enumerate(raw.decode('ascii', 'replace').splitlines(), 1):
            if not line or line.startswith('#'): continue
            f = line.split('\t')
            if len(f) not in (8, 9):
                problems.append('%s:%d: %d columns, want 8 (or 9 with a shortcut)' % (name, n, len(f)))
                continue
            if len(f) == 9:
                shortcuts += 1
                problems += check_shortcut('%s:%d' % (name, n), f[8], items)
            rid, state, hint, note, when, kind, target, num = f[:8]
            if rid in seen: problems.append('%s:%d: id %s twice' % (name, n, rid))
            seen.add(rid)
            if kind not in ('step', 'check'): problems.append('%s:%d: kind %s' % (name, n, kind))
            if state != 'open' or note or when: problems.append('%s:%d: state / note / time must be open / empty' % (name, n))
            if not hint or len(hint) > 239: problems.append('%s:%d: hint empty or longer than 239' % (name, n))
            if kind == 'step':
                steps += 1
                if rid != 'step%s' % num: problems.append('%s:%d: step id %s vs number %s' % (name, n, rid, num))
            else:
                checks += 1
                if target or num != '0': problems.append('%s:%d: a check has no target / number' % (name, n))
                if rid not in doc_ids: problems.append('%s:%d: check id %s not in docs/%s' % (name, n, rid, doc))
        summary.append('%s %d steps + %d checks, %d shortcuts' % (name, steps, checks, shortcuts))
    return problems, summary


def check_radial(path=RADIAL, name='TruMenu.radial.txt', marker='# TruMenu radial menu', items=None):
    """problems of a radial-format file (TruMenu.radial.txt, 0.10.1 also TruMenu.tour.txt; empty list = fine), a summary
    line and its levels {path: [entries]} (for the limits with the built-in entries)"""
    problems = []
    src = read_cpp()
    items = items or item_types(src)
    m = re.search(r'kRadForbidden\[\] = \{(.*?)\};', src, re.S)
    cpp_forbidden = re.findall(r'"([^"]+)"', m.group(1)) if m else []
    if sorted(cpp_forbidden) != sorted(RADIAL_FORBIDDEN):
        problems.append('kRadForbidden in TruMenu.cpp %s differs from this tool %s' % (cpp_forbidden, RADIAL_FORBIDDEN))
    if not os.path.exists(path):
        return problems + ['%s missing' % name], '', {'': []}
    raw = open(path, 'rb').read()
    if any(b > 126 or (b < 32 and b not in (9, 10, 13)) for b in raw):
        problems.append('%s: non-ASCII bytes (the menu font has no umlauts)' % name)
    lines = raw.decode('ascii', 'replace').splitlines()
    if not lines or not lines[0].startswith(marker):
        problems.append('%s: first line must start with "%s" (Set-TruMenu.ps1 marker)' % (name, marker))
    levels = {'': []}                        # path -> entries (folders + items) in order, as RadialLoad builds them
    seen, entries = set(), 0
    for n, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'): continue
        where = '%s:%d' % (name, n)
        f = line.split('|')
        if len(f) != 3:
            problems.append('%s: want "path | label | item id [arg]" (%d fields)' % (where, len(f)))
            continue
        path, label, cmd = (x.strip() for x in f)
        segs = [s.strip() for s in path.split('/') if s.strip()]
        word, _, arg = cmd.partition(' ')
        arg = arg.strip()
        if not label or len(label) > 47: problems.append('%s: label empty or longer than 47' % where)
        for s in segs:
            if len(s) > 47 or not re.fullmatch(r'[A-Za-z0-9 _().-]+', s):
                problems.append('%s: path segment "%s" (letters, digits, space _ ( ) . -; at most 47)' % (where, s))
        if len('/'.join(segs)) > 95: problems.append('%s: path longer than 95' % where)
        if word in RADIAL_FORBIDDEN:
            problems.append('%s: %s is never offered in the radial menu' % (where, word))
            continue
        if word not in items and not word.startswith('dev.'):
            problems.append('%s: unknown item id %s' % (where, word))
        elif items.get(word) == 'bool' and arg not in ('', '0', '1'):
            problems.append('%s: %s is a bool item, arg "%s" (0 / 1)' % (where, word, arg))
        elif items.get(word) == 'todo':
            problems.append('%s: %s is a todo item' % (where, word))
        if word in ('instance.spawn', 'weapon.give', 'level.load') and not re.fullmatch(r'[a-z0-9_-]{1,63}', arg):
            problems.append('%s: %s needs one name (a-z 0-9 _ -), got "%s"' % (where, word, arg))
        key = ('/'.join(segs).lower(), label.lower())
        if key in seen: problems.append('%s: label "%s" twice in "%s"' % (where, label, '/'.join(segs)))
        seen.add(key)
        full = ''
        for s in segs:                       # folders on the way (case-insensitive like RadLevelFor)
            child = (full + '/' + s) if full else s
            if not any(e == ('folder', child.lower()) for e in levels[full]):
                levels[full].append(('folder', child.lower()))
                levels.setdefault(child.lower(), [])
            full = child.lower()
        levels.setdefault(full, []).append(('item', label))
        entries += 1
    total = entries + sum(1 for v in levels.values() for e in v if e[0] == 'folder')
    if total > 256: problems.append('%s: %d entries incl. folders, TruMenu keeps 256' % (name, total))
    if len(levels) > 48: problems.append('%s: %d levels, TruMenu keeps 48' % (name, len(levels)))
    for p, v in levels.items():
        if len(v) > 64: problems.append('%s: level "%s" has %d entries, TruMenu keeps 64' % (name, p, len(v)))
    paged = ['%s (%d)' % (p or 'top', len(v)) for p, v in sorted(levels.items()) if len(v) > 8]
    summary = '%d entries in %d levels (top %d sectors)%s' % (entries, len(levels), len(levels['']),
                                                            ', pages: ' + ', '.join(paged) if paged else '')
    return problems, summary, levels


def check_builtins(rows, radial_levels, tour_levels):
    """0.10.1: the limits / top sectors with the built-in entries the table defaults give (Mode=menu: "Tests" with 4
    virtual folders + "Rundgang" (the tour levels below it) + 1 virtual slot, "Spiel beenden" last on the top level)"""
    d = {k: v for s, k, v, _ in rows if s == 'Radial'}
    menu = d.get('Mode') == 'menu'
    tests = menu and d.get('TestsLevel') == '1'
    quit_ = menu and d.get('QuitSector') == '1'
    top = len(radial_levels['']) + (1 if tests else 0) + (1 if quit_ else 0)
    entries = sum(len(v) for v in radial_levels.values())
    levels = len(radial_levels)
    if tests:                                # Tests folder, 4 virtual folders, Rundgang folder, the tour file
        entries += 1 + 4 + 1 + sum(len(v) for p, v in tour_levels.items())
        levels += 1 + 1 + 1 + sum(1 for p in tour_levels if p)
    if quit_: entries += 1
    problems = []
    if entries > 256: problems.append('built-ins: %d entries with Tests / Rundgang / quit sector, TruMenu keeps 256' % entries)
    if levels > 48: problems.append('built-ins: %d levels with Tests / Rundgang / the virtual slot, TruMenu keeps 48' % levels)
    pages = (top + 7) // 8
    return problems, 'top level %d sectors with the built-ins (%s%s), %d page(s); %d entries, %d levels' % (
        top, 'Tests' if tests else '', ' + Spiel beenden' if quit_ else '', pages, entries, levels)


def check_ini_values(ini_path):
    """0.10.1: the [Radial] values of the INI file that is checked (Mode / Freeze / QuitSector / TestsLevel)"""
    problems, section = [], None
    for n, line in enumerate(open(ini_path, encoding='utf-8').read().splitlines(), 1):
        line = line.strip()
        m = re.match(r'^\[(.+)\]$', line)
        if m:
            section = m.group(1)
            continue
        if section != 'Radial' or not line or line.startswith(';') or '=' not in line: continue
        key, _, value = line.partition('=')
        key, value = key.strip(), value.strip()
        if key in RADIAL_VALUES and value.lower() not in RADIAL_VALUES[key]:
            problems.append('%s:%d: [Radial] %s=%s (%s)' % (os.path.basename(ini_path), n, key, value,
                                                          ' / '.join(RADIAL_VALUES[key])))
    return problems


def check_shot(ini_path, radial_path):
    """0.10.5: the [Shot] values of the INI, the shot items / exports in TruMenu.cpp, the Claude level of the radial file"""
    problems, section, seen = [], None, set()
    name = os.path.basename(ini_path)
    for n, line in enumerate(open(ini_path, encoding='utf-8').read().splitlines(), 1):
        line = line.strip()
        m = re.match(r'^\[(.+)\]$', line)
        if m:
            section = m.group(1)
            continue
        if section != 'Shot' or not line or line.startswith(';') or '=' not in line: continue
        key, _, value = line.partition('=')
        key, value = key.strip(), value.strip()
        seen.add(key)
        if key in SHOT_VALUES and value not in SHOT_VALUES[key]:
            problems.append('%s:%d: [Shot] %s=%s (%s)' % (name, n, key, value, ' / '.join(SHOT_VALUES[key])))
        elif key in ('Hotkey', 'MaxPerMinute'):
            try:
                v = int(value, 0)
            except ValueError:
                v = -1
            hi = 0xFE if key == 'Hotkey' else 120
            if not 0 <= v <= hi: problems.append('%s:%d: [Shot] %s=%s (0 .. %d)' % (name, n, key, value, hi))
        elif key == 'Folder' and re.search(r'[<>"|?*]', value):
            problems.append('%s:%d: [Shot] Folder=%s has a character Windows does not allow' % (name, n, value))
    for key in ('Enabled', 'Folder', 'Clean', 'Hotkey', 'MaxPerMinute'):
        if key not in seen: problems.append('%s: [Shot] %s missing' % (name, key))
    src = read_cpp()
    items = item_types(src)
    for item, typ in (('shot.save', 'action'), ('shot.status', 'info'), ('claude.mark', 'action')):
        if items.get(item) != typ: problems.append('TruMenu.cpp: item %s (%s) missing in kItems' % (item, typ))
    for export in ('TruMenuShot', 'TruMenuMark'):
        if not re.search(r'__declspec\(dllexport\) int __cdecl %s\(const char \*' % export, src):
            problems.append('TruMenu.cpp: export %s(const char *) missing' % export)
    kinds, top, flow_ring = [], [], []
    if os.path.exists(radial_path):
        for line in open(radial_path, encoding='ascii', errors='replace').read().splitlines():
            line = line.strip()
            if not line or line.startswith('#') or line.count('|') != 2: continue
            path, label, cmd = (x.strip() for x in line.split('|'))
            first = path.split('/')[0].strip()
            if first not in top: top.append(first)
            if first.lower() != 'claude': continue
            word, _, arg = cmd.partition(' ')
            if word in FLOW_RING and path.strip().lower() == 'claude' and not arg.strip():   # 0.11 Ablauf entries
                flow_ring.append(word)
                continue
            if word != 'claude.mark' or path.strip().lower() != 'claude':
                problems.append('radial: level Claude holds "%s | %s" (only claude.mark <kind> and the flow entries %s '
                                'directly in Claude)' % (path, cmd, ' / '.join(FLOW_RING)))
            else:
                kinds.append(arg.strip())
    if kinds != CLAUDE_KINDS:
        problems.append('radial: level Claude marks %s, want %s in this order' % (kinds, CLAUDE_KINDS))
    if len(set(flow_ring)) != len(flow_ring):
        problems.append('radial: level Claude holds a flow entry twice (%s)' % ', '.join(flow_ring))
    return problems, 'Claude marks %s, flow entries %s; file top levels %s' % (' '.join(kinds), ' '.join(flow_ring) or '-',
                                                                              ', '.join(top))


def check_flow(ini_path):
    """0.11: the [Flow] values of the INI, the flow items in kItems, the parser header included by TruMenu.cpp"""
    problems, section, seen = [], None, set()
    name = os.path.basename(ini_path)
    for n, line in enumerate(open(ini_path, encoding='utf-8').read().splitlines(), 1):
        line = line.strip()
        m = re.match(r'^\[(.+)\]$', line)
        if m:
            section = m.group(1)
            continue
        if section != 'Flow' or not line or line.startswith(';') or '=' not in line: continue
        key, _, value = line.partition('=')
        key, value = key.strip(), value.strip()
        seen.add(key)
        if key in FLOW_VALUES and value not in FLOW_VALUES[key]:
            problems.append('%s:%d: [Flow] %s=%s (%s)' % (name, n, key, value, ' / '.join(FLOW_VALUES[key])))
        elif key in FLOW_RANGES:
            lo, hi = FLOW_RANGES[key]
            try:
                v = float(value) if key == 'Size' else int(value, 0)
            except ValueError:
                v = lo - 1
            if not lo <= v <= hi: problems.append('%s:%d: [Flow] %s=%s (%s .. %s)' % (name, n, key, value, lo, hi))
        elif key == 'File' and (not value or re.search(r'[<>"|?*]', value)):
            problems.append('%s:%d: [Flow] File=%s empty or with a character Windows does not allow' % (name, n, value))
    for key in ('Enabled', 'File', 'Overlay', 'Position', 'Size', 'Lines', 'AutoAdvance', 'ToastSeconds', 'PollMs'):
        if key not in seen: problems.append('%s: [Flow] %s missing' % (name, key))
    src = read_cpp()
    items = item_types(src)
    for item in FLOW_ITEMS:
        want = 'info' if item in ('flow.status', 'flow.list') else 'action'
        if items.get(item) != want: problems.append('TruMenu.cpp: item %s (%s) missing in kItems' % (item, want))
    if '#include "TruFlowCore.h"' not in src: problems.append('TruMenu.cpp does not include TruFlowCore.h')
    return problems


def gn_names(src):
    """0.22.16: the registry names of kGnDefs (gfx.next) in TruMenu.cpp"""
    if 'const GnDef kGnDefs[] = {' not in src: return []
    block = src[src.index('const GnDef kGnDefs[] = {'):]
    block = block[:block.index('\n};')]
    return re.findall(r'\{"([A-Za-z0-9]+)", (?:0x[0-9a-f]+|-1)\}', block)


def nav_switches(src):
    """0.12: the switch names of kNavSwitches in TruMenu.cpp (in table order)"""
    if 'const NavSwitch kNavSwitches[] = {' not in src: return []
    block = src[src.index('const NavSwitch kNavSwitches[] = {'):]
    block = block[:block.index('\n};')]
    return re.findall(r'\{"([a-z0-9_]+)", 0x', block)


def dv_layers(src):
    """0.14: the layer names of kDvLayers in TruMenu.cpp (in table order)"""
    if 'const DvLayerDef kDvLayers[kDvCount] = {' not in src: return []
    block = src[src.index('const DvLayerDef kDvLayers[kDvCount] = {'):]
    block = block[:block.index('\n};')]
    return re.findall(r'\{"([a-z]+)", "[A-Za-z]+", ', block)


def check_debug(ini_path, radial_path):
    """0.12: the [Debug] values of the INI, the nav items in kItems, the nav.* entries of the radial file; 0.13 the
    label keys / dbg.labels; 0.14 the debug view keys, items and ring entries"""
    problems, section, seen = [], None, set()
    name = os.path.basename(ini_path)
    src = read_cpp()
    switches = nav_switches(src)
    if not switches: problems.append('TruMenu.cpp: kNavSwitches missing or empty')
    layers = dv_layers(src)
    if len(layers) != DV_LAYER_COUNT:
        problems.append('TruMenu.cpp: kDvLayers has %d layers, want %d' % (len(layers), DV_LAYER_COUNT))
    for n, line in enumerate(open(ini_path, encoding='utf-8').read().splitlines(), 1):
        line = line.strip()
        m = re.match(r'^\[(.+)\]$', line)
        if m:
            section = m.group(1)
            continue
        if section != 'Debug' or not line or line.startswith(';') or '=' not in line: continue
        key, _, value = line.partition('=')
        key, value = key.strip(), value.strip()
        seen.add(key)
        if key in ('Enabled', 'NavMask', 'Labels', 'LabelCross') and value not in ('0', '1'):
            problems.append('%s:%d: [Debug] %s=%s (0 / 1)' % (name, n, key, value))
        elif key in LABEL_RANGES:
            lo, hi = LABEL_RANGES[key]
            try:
                ok = lo <= float(value) <= hi and (key != 'LabelMax' or value.isdigit())
            except ValueError:
                ok = False
            if not ok: problems.append('%s:%d: [Debug] %s=%s (%g .. %g)' % (name, n, key, value, lo, hi))
        elif key == 'LabelMatch' and (not value or not re.match(r'^[A-Za-z0-9_*, ]+$', value)):
            problems.append('%s:%d: [Debug] LabelMatch=%s (comma list of name parts a-z 0-9 _ or *)' % (name, n, value))
        elif key in ('NavDraw', 'ViewNav'):
            for word in [w for w in re.split(r'[ ,]+', value) if w]:
                if word not in switches: problems.append('%s:%d: [Debug] %s names "%s" (not in kNavSwitches)'
                                                         % (name, n, key, word))
        elif key in DV_BOOL_KEYS and value not in ('0', '1'):        # 0.14
            problems.append('%s:%d: [Debug] %s=%s (0 / 1)' % (name, n, key, value))
        elif key in DV_RANGES:
            lo, hi = DV_RANGES[key]
            try:
                ok = lo <= float(value) <= hi and (key in DV_FLOAT_KEYS or re.fullmatch(r'-?\d+', value) is not None)
            except ValueError:
                ok = False
            if not ok: problems.append('%s:%d: [Debug] %s=%s (%g .. %g)' % (name, n, key, value, lo, hi))
        elif key == 'NameColour' and not re.fullmatch(r'[0-9A-Fa-f]{6}', value):
            problems.append('%s:%d: [Debug] NameColour=%s (RRGGBB)' % (name, n, value))
        elif key == 'NameMatch' and value and not re.match(r'^[A-Za-z0-9_*, ]+$', value):
            problems.append('%s:%d: [Debug] NameMatch=%s (comma list of name parts a-z 0-9 _ or *, may be empty)'
                            % (name, n, value))
        elif key == 'FlatPasses':                # 0.15: a mask of the pass ids, hex or decimal
            try:
                mask = int(value, 0)
                ok = mask > 0 and not (mask & ~RM_PASS_ALL)
            except ValueError:
                ok = False
            if not ok: problems.append('%s:%d: [Debug] FlatPasses=%s (a mask of 0x200 0x100 0x80 0x400 0x800 1 2, e.g. '
                                       '0x200)' % (name, n, value))
        elif key == 'FlatColour' and value not in ('material', 'class'):
            problems.append('%s:%d: [Debug] FlatColour=%s (material / class)' % (name, n, value))
        elif key == 'ViewSkip':                  # 0.16: layer names of kDvLayers, may be empty
            for word in [w for w in re.split(r'[ ,]+', value) if w]:
                if word not in layers: problems.append('%s:%d: [Debug] ViewSkip names "%s" (not in kDvLayers)'
                                                       % (name, n, word))
    for key in (('Enabled', 'NavDraw', 'NavMask', 'ViewNav', 'NameColour', 'NameMatch', 'FlatPasses', 'FlatColour',
                 'ViewSkip') + LABEL_KEYS + DV_BOOL_KEYS + tuple(sorted(DV_RANGES))):
        if key not in seen: problems.append('%s: [Debug] %s missing' % (name, key))
    items = item_types(src)
    for item, typ in sorted(NAV_ITEMS.items()) + sorted(LABEL_ITEMS.items()) + sorted(DV_ITEMS.items()):
        if items.get(item) != typ: problems.append('TruMenu.cpp: item %s (%s) missing in kItems' % (item, typ))
    entries, used, labels, flight = 0, set(), 0, 0
    dv_seen = {}                             # 0.14: layer / item -> count of ring entries
    if os.path.exists(radial_path):
        for n, line in enumerate(open(radial_path, encoding='ascii', errors='replace').read().splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#') or line.count('|') != 2: continue
            path, label, cmd = (x.strip() for x in line.split('|'))
            word, _, arg = cmd.partition(' ')
            arg = arg.strip()
            if word in LABEL_ITEMS:          # 0.13: dbg.labels, no argument (the ring flips it)
                labels += 1
                if arg: problems.append('%s:%d: %s takes no argument in the ring, got "%s"'
                                        % (os.path.basename(radial_path), n, word, arg))
                continue
            if word in DV_ITEMS:             # 0.14: dbg.show <layer>, the others no argument
                where = '%s:%d' % (os.path.basename(radial_path), n)
                if word == 'dbg.show':
                    if arg not in layers:
                        problems.append('%s: dbg.show needs one layer of kDvLayers, got "%s"' % (where, arg))
                    elif arg in DV_OWN_ITEM:
                        problems.append('%s: layer %s has its own item %s - use that' % (where, arg, DV_OWN_ITEM[arg]))
                    else:
                        dv_seen[arg] = dv_seen.get(arg, 0) + 1
                elif word == 'dbg.namefilter':
                    if not re.fullmatch(r'[A-Za-z0-9_*,]+', arg):
                        problems.append('%s: dbg.namefilter needs one list of name parts (a-z 0-9 _ , or *), got "%s"'
                                        % (where, arg))
                elif word == 'dbg.namecolour':
                    if arg not in DV_NAME_COLOURS and not re.fullmatch(r'[0-9A-Fa-f]{6}', arg):
                        problems.append('%s: dbg.namecolour needs a preset %s or RRGGBB, got "%s"'
                                        % (where, '/'.join(DV_NAME_COLOURS), arg))
                elif word == 'dbg.namesize':
                    try:
                        ok = 0.5 <= float(arg) <= 3.0
                    except ValueError:
                        ok = False
                    if not ok: problems.append('%s: dbg.namesize needs 0.5 .. 3, got "%s"' % (where, arg))
                elif word == 'dbg.flatpass':         # 0.15: one pass id, once each
                    if arg not in RM_PASSES:
                        problems.append('%s: dbg.flatpass needs one pass id of %s, got "%s"'
                                        % (where, ' '.join(RM_PASSES), arg))
                    else:
                        dv_seen[word + ' ' + arg] = dv_seen.get(word + ' ' + arg, 0) + 1
                elif word == 'dbg.flatcolour':       # 0.15: material / class, once each
                    if arg not in ('material', 'class'):
                        problems.append('%s: dbg.flatcolour needs material or class, got "%s"' % (where, arg))
                    else:
                        dv_seen[word + ' ' + arg] = dv_seen.get(word + ' ' + arg, 0) + 1
                elif word == 'dbg.flatpasses':       # 0.15: census / default / a mask
                    try:
                        ok = arg in ('census', 'default') or (int(arg, 0) > 0 and not (int(arg, 0) & ~RM_PASS_ALL))
                    except ValueError:
                        ok = False
                    if not ok: problems.append('%s: dbg.flatpasses needs census, default or a pass mask, got "%s"'
                                               % (where, arg))
                elif word in DP_RING_ARGS:           # 0.16: dbg.depth on / dim / off, dbg.enclosing normal / dim / hide
                    if arg not in DP_RING_ARGS[word]:
                        problems.append('%s: %s needs one of %s, got "%s"' % (where, word, ' / '.join(DP_RING_ARGS[word]),
                                                                              arg))
                    else:
                        dv_seen[word + ' ' + arg] = dv_seen.get(word + ' ' + arg, 0) + 1
                elif word in DP_RING_PERCENT:        # 0.16: dbg.alpha / dbg.bright presets
                    lo, hi = DP_RING_PERCENT[word]
                    if not (arg.isdigit() and lo <= int(arg) <= hi):
                        problems.append('%s: %s needs a percent %d .. %d, got "%s"' % (where, word, lo, hi, arg))
                elif arg:
                    problems.append('%s: %s takes no argument in the ring, got "%s"' % (where, word, arg))
                else:
                    dv_seen[word] = dv_seen.get(word, 0) + 1
                continue
            if word == 'cheat.flight':           # 0.16: the flight switch in the ring, once, no argument
                flight += 1
                if arg: problems.append('%s:%d: cheat.flight takes no argument in the ring, got "%s"'
                                        % (os.path.basename(radial_path), n, arg))
                continue
            if word == 'cheat.speed':            # 0.16: speed presets
                try:
                    ok = 0.0 < float(arg) < 1000.0
                except ValueError:
                    ok = False
                if not ok: problems.append('%s:%d: cheat.speed needs a number 0 .. 1000, got "%s"'
                                           % (os.path.basename(radial_path), n, arg))
                continue
            if not word.startswith('nav.'): continue
            entries += 1
            where = '%s:%d' % (os.path.basename(radial_path), n)
            if word == 'nav.draw':
                if arg not in switches:
                    problems.append('%s: nav.draw needs one switch of kNavSwitches, got "%s"' % (where, arg))
                else:
                    used.add(arg)
            elif arg:
                problems.append('%s: %s takes no argument in the ring, got "%s"' % (where, word, arg))
    if os.path.exists(radial_path) and labels != 1:
        problems.append('%s: dbg.labels must be in the radial file once, found %d' % (os.path.basename(radial_path), labels))
    if os.path.exists(radial_path):          # 0.14: every layer and every dbg.* switch item once
        want = [DV_OWN_ITEM.get(l, l) for l in layers if l not in DV_RING_FROZEN] + ['dbg.view', 'dbg.triggers', 'dbg.status']
        want += list(RM_RING_SWITCHES) + ['dbg.flatpass ' + p for p in RM_PASSES] + \
            ['dbg.flatcolour material', 'dbg.flatcolour class']                     # 0.15 render mode
        want += list(DP_RING_SWITCHES) + ['%s %s' % (w, a) for w, args in sorted(DP_RING_ARGS.items()) for a in args]
        for w in want:
            if dv_seen.get(w, 0) != 1:
                problems.append('%s: debug view entry %s must be in the radial file once, found %d'
                                % (os.path.basename(radial_path), w, dv_seen.get(w, 0)))
        if flight != 1:                      # 0.16
            problems.append('%s: cheat.flight must be in the radial file once, found %d'
                            % (os.path.basename(radial_path), flight))
    return problems, ('%d switches in kNavSwitches, %d nav entries in the radial file (%d switches), %d dbg.labels entry, '
                      '%d debug view layers, %d debug view entries' % (len(switches), entries, len(used), labels,
                                                                       len(layers), sum(dv_seen.values())))


def ini_section(ini_path, wanted):
    """[(line number, key, value)] of one INI section"""
    out, section = [], None
    for n, line in enumerate(open(ini_path, encoding='utf-8').read().splitlines(), 1):
        line = line.strip()
        m = re.match(r'^\[(.+)\]$', line)
        if m:
            section = m.group(1)
            continue
        if section != wanted or not line or line.startswith(';') or '=' not in line: continue
        key, _, value = line.partition('=')
        out.append((n, key.strip(), value.strip()))
    return out


def qb_rows(src, with_tail=False):
    """0.17: the rows of the quick-toggle bar tables: [(table, de, id, arg, kind, layer)]; 0.18: id may be "-" (label /
    planned rows), the argument may be several adjacent string literals, with_tail adds the rest of the row (flags);
    0.22.28: a line break may follow any comma of a row (before only after the layer)"""
    rows = []
    for table in QB_TABLES:
        start = 'const QbRow %s[] = {' % table
        if start not in src: continue
        block = src[src.index(start):]
        block = block[:block.index('\n};')]
        for m in re.finditer(r'\{"([^"]*)",\s+"([^"]*)",\s+"([a-z][a-z0-9_.]*|-)",\s+((?:"[^"]*"\s*)+),\s+(kQb[A-Za-z]+),'
                             r'\s+(-1|kDv[A-Za-z]+),([^{}]*)\}', block, re.S):
            arg = ''.join(re.findall(r'"([^"]*)"', m.group(4)))
            row = (table, m.group(1), m.group(3), arg, m.group(5), m.group(6))
            rows.append(row + (m.group(7),) if with_tail else row)
    return rows


def check_quick(ini_path, radial_path):
    """0.17 (2026-11-06 TruMenu 0.17 quick toggles): the [Quick] values, [Shot] OnCine*, [Debug] CheckpointHide; the new
    items in kItems; the bar's rows (every item id in kItems, bool rows on bool items or dbg.show <layer>, value rows on
    the value items, every debug view layer reachable from the bar); the new ring entries"""
    problems = []
    name = os.path.basename(ini_path)
    src = read_cpp()
    seen = set()
    for n, key, value in ini_section(ini_path, 'Quick'):
        seen.add(key)
        where = '%s:%d: [Quick] %s=%s' % (name, n, key, value)
        if key in ('Enabled', 'ShowClosed') and value not in ('0', '1'): problems.append(where + ' (0 / 1)')
        elif key == 'OpenButtons':
            try:
                v = int(value, 0)
            except ValueError:
                v = -1
            if not 1 <= v <= 0xFFFF: problems.append(where + ' (an XInput button mask 1 .. 0xFFFF)')
            elif v & QB_OWN: problems.append(where + ' (must not hold D-pad / LB / RB / X / Y = 0x%04X: the open bar '
                                             'owns them)' % QB_OWN)
        elif key in QB_RANGES:
            lo, hi = QB_RANGES[key]
            try:
                ok = lo <= float(value) <= hi and (key == 'Scale' or value.isdigit())
            except ValueError:
                ok = False
            if not ok: problems.append(where + ' (%g .. %g)' % (lo, hi))
        elif key == 'Language' and value not in ('de', 'en'): problems.append(where + ' (de / en)')
    for key in QB_KEYS:
        if key not in seen: problems.append('%s: [Quick] %s missing' % (name, key))
    seen = set()
    for n, key, value in ini_section(ini_path, 'Shot'):
        if not key.startswith('OnCine'): continue
        seen.add(key)
        where = '%s:%d: [Shot] %s=%s' % (name, n, key, value)
        if key == 'OnCine' and value not in ('0', '1'): problems.append(where + ' (0 / 1)')
        elif key == 'OnCineSignal' and value not in ('cine', 'camera', 'both'): problems.append(where + ' (cine / camera / both)')
        elif key in OC_RANGES:
            lo, hi = OC_RANGES[key]
            if not (value.isdigit() and lo <= int(value) <= hi): problems.append(where + ' (%d .. %d)' % (lo, hi))
    for key in ['OnCine', 'OnCineSignal'] + sorted(OC_RANGES):
        if key not in seen: problems.append('%s: [Shot] %s missing' % (name, key))
    hide = [v for n, k, v in ini_section(ini_path, 'Debug') if k == 'CheckpointHide']
    if len(hide) != 1: problems.append('%s: [Debug] CheckpointHide missing' % name)
    elif hide[0] and not all(w.isdigit() and int(w) < 65536 for w in re.split(r'[ ,]+', hide[0]) if w):
        problems.append('%s: [Debug] CheckpointHide=%s (comma list of intro ids 0 .. 65535, or empty)' % (name, hide[0]))
    items = item_types(src)
    for item, typ in sorted(QB_ITEMS.items()):
        if items.get(item) != typ: problems.append('TruMenu.cpp: item %s (%s) missing in kItems' % (item, typ))
    rows = qb_rows(src)
    if len(rows) < 20: problems.append('TruMenu.cpp: quick-toggle bar tables: only %d rows found' % len(rows))
    layers = dv_layers(src)
    reach = set()
    for table, de, item, arg, kind, layer in rows:
        where = 'TruMenu.cpp: %s row "%s" (%s %s)' % (table, de, item, arg)
        if kind in ('kQbLabel', 'kQbPlanned') or item == '-':   # 0.18: checked in check_018
            continue
        if item not in items: problems.append(where + ': item not in kItems')
        elif kind == 'kQbBool':
            if item == 'dbg.show':
                if arg not in layers: problems.append(where + ': dbg.show needs a layer of kDvLayers')
                reach.add(arg)
            elif item == 'ai.dumb':          # 0.19: "ai.dumb <preset>" (the bar adds 0 / 1)
                if arg not in AI_SETTINGS: problems.append(where + ': ai.dumb needs one of %s' % ' / '.join(AI_SETTINGS))
            elif item == 'nav.draw':         # 0.21.6: "nav.draw <switch>" (RadialOn: the switch byte)
                if arg not in nav_switches(src): problems.append(where + ': nav.draw needs a switch of kNavSwitches')
            elif item == 'dbg.flatpass':     # 0.21.6: "dbg.flatpass <pass>" (RadialOn: the pass bit)
                if arg not in RM_PASSES: problems.append(where + ': dbg.flatpass needs one of %s' % ' / '.join(RM_PASSES))
            elif item == 'gfx.next':         # 0.22.16: "gfx.next <RegistryName>" (RadialOn: GnOn, the registry value)
                if arg not in gn_names(src): problems.append(where + ': gfx.next needs a name of kGnDefs')
            elif item in W8_CAT_ITEMS:       # 0.22.50: "snd.logcat / snd.catmute / snd.catsolo <kind>" (RadialOn: W8RowOn)
                if arg not in W8_CATS: problems.append(where + ': %s needs one of %s' % (item, ' / '.join(W8_CATS)))
            elif item == 'snd.logsub':       # 0.22.53 W11: "snd.logsub <sub-group key>" (RadialOn: W8RowOn)
                if arg not in w11_subs(src): problems.append(where + ': snd.logsub needs a key of kW8Sub')
            elif items[item] != 'bool' or arg: problems.append(where + ': a bool row needs a bool item without argument')
        elif kind == 'kQbValue' and item not in QB_VALUE_ITEMS:
            problems.append(where + ': a value row needs one of %s' % ', '.join(QB_VALUE_ITEMS))
        elif kind == 'kQbValue' and item == 'snd.hear' and arg not in W8_CATS + tuple(w11_subs(src)):
            problems.append(where + ': snd.hear needs a kind or a key of kW8Sub')   # 0.22.53 W11
        elif kind == 'kQbAction' and items[item] != 'action' and not (item == 'player.health' and not arg) and \
                not (item == 'game.vol.music' and arg == '128') and \
                not (item == 'puzzle.thorgap' and not arg):   # 0.22.18: music volume warning; 0.22.62: typed gap (kQfLine)
            problems.append(where + ': an action row needs an action item (or player.health without argument)')
        elif kind == 'kQbInfo' and items[item] != 'info': problems.append(where + ': an info row needs an info item')
        elif kind == 'kQbChoice' and items[item] != 'action': problems.append(where + ': a choice row needs an action item')
        for lname, own in DV_OWN_ITEM.items():
            if item == own: reach.add(lname)
    for lname in layers:
        if lname not in reach: problems.append('TruMenu.cpp: layer %s is not reachable from the quick-toggle bar' % lname)
    counts = {}
    if os.path.exists(radial_path):
        for n, line in enumerate(open(radial_path, encoding='ascii', errors='replace').read().splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#') or line.count('|') != 2: continue
            cmd = line.split('|')[2].strip()
            word, _, arg = cmd.partition(' ')
            arg = arg.strip()
            where = '%s:%d: %s' % (os.path.basename(radial_path), n, cmd)
            if word in ('quick.open', 'shot.oncine', 'dbg.depthdump', 'dbg.cplist', 'pos.list'):
                counts[word] = counts.get(word, 0) + 1
                if arg: problems.append(where + ' (no argument in the ring)')
            elif word == 'dbg.cpall':
                counts['dbg.cpall ' + arg] = counts.get('dbg.cpall ' + arg, 0) + 1
                if arg not in ('0', '1'): problems.append(where + ' (0 / 1)')
            elif word == 'dbg.cpgo' and not (arg == 'active' or arg.isdigit()):
                problems.append(where + ' (active or an intro id)')
            elif word == 'pos.go' and not re.fullmatch(r'[A-Za-z0-9_-]+', arg):
                problems.append(where + ' (a saved name or last)')
            elif word == 'pos.save' and arg and not re.fullmatch(r'[A-Za-z0-9_-]+', arg):
                problems.append(where + ' (no argument or a name a-z 0-9 _ -)')
        for want in ('quick.open', 'shot.oncine', 'dbg.depthdump', 'dbg.cplist', 'dbg.cpall 0', 'dbg.cpall 1'):
            if counts.get(want, 0) != 1:
                problems.append('%s: %s must be in the radial file once, found %d'
                                % (os.path.basename(radial_path), want, counts.get(want, 0)))
    return problems, '%d bar rows in %d tables (every one of %d layers reachable), %d new items, [Quick] %d keys' % (
        len(rows), len({r[0] for r in rows}), len(layers), len(QB_ITEMS), len(QB_KEYS))


def check_018(ini_path, radial_path):
    """0.18 (2026-11-06 TruMenu 0.18): the 0 / 1 keys, the new items, kQbPages (at most QB_PAGES_MAX pages, every table
    on a page), label / planned rows, confirm / backup flags only on action rows, level.load rows with one unit name, the
    ring's overlay.larain (once, no argument), pos.goload (a name or last), time.scale (a number 0 .. 10)"""
    problems = []
    name = os.path.basename(ini_path)
    src = read_cpp()
    for section, key in Q18_KEYS:
        found = [(n, v) for n, k, v in ini_section(ini_path, section) if k == key]
        if len(found) != 1: problems.append('%s: [%s] %s missing' % (name, section, key))
        elif found[0][1] not in ('0', '1'):
            problems.append('%s:%d: [%s] %s=%s (0 / 1)' % (name, found[0][0], section, key, found[0][1]))
    items = item_types(src)
    for item, typ in sorted(Q18_ITEMS.items()):
        if items.get(item) != typ: problems.append('TruMenu.cpp: item %s (%s) missing in kItems' % (item, typ))
    block = src[src.index('const QbPage kQbPages[] = {'):]
    block = block[:block.index('\n};')]
    pages = re.findall(r'QB_PAGE\("([^"]*)", "([^"]*)", (kQb[A-Za-z]+), (kQs[A-Za-z]+)\)', block)
    special = re.findall(r'\{"([^"]*)", "([^"]*)", nullptr, 0, (kQs[A-Za-z]+)\}', block)
    if len(pages) + len(special) > QB_PAGES_MAX:
        problems.append('TruMenu.cpp: kQbPages has %d pages (at most %d)' % (len(pages) + len(special), QB_PAGES_MAX))
    on_page = {p[2] for p in pages}
    for table in QB_TABLES:
        if table not in on_page: problems.append('TruMenu.cpp: row table %s is on no page of kQbPages' % table)
    planned = labels = confirm = 0
    for table, de, item, arg, kind, layer, tail in qb_rows(src, True):
        where = 'TruMenu.cpp: %s row "%s" (%s %s)' % (table, de, item, arg)
        flags = 'kQfConfirm' in tail or 'kQfBackup' in tail
        if (item == '-') != (kind in ('kQbLabel', 'kQbPlanned', 'kQbGroup', 'kQbNote')):   # 0.21.1 kQbGroup, 0.22.28
            problems.append(where + ': id "-" exactly on label / planned / group / note rows')
        if kind == 'kQbPlanned':
            planned += 1
            if arg.count('|') != 1 or not all(arg.split('|')): problems.append(where + ': planned text "German|English"')
        if kind == 'kQbLabel': labels += 1
        if flags:
            confirm += 1
            if kind != 'kQbAction' and not (kind == 'kQbChoice' and 'kQfBackup' not in tail):   # 0.21.1 spawn
                problems.append(where + ': kQfConfirm / kQfBackup only on action rows (kQfConfirm also on choice rows)')
        if item == 'level.load' and not re.fullmatch(r'[a-z0-9_]+', arg):
            problems.append(where + ': level.load takes one unit name a-z 0-9 _')
        if item == 'level.load' and 'kQfConfirm' not in tail: problems.append(where + ': level.load rows need kQfConfirm')
        if not re.fullmatch(r'[\x20-\x7e]*', de + arg): problems.append(where + ': ASCII only')
    counts = {}
    if os.path.exists(radial_path):
        for n, line in enumerate(open(radial_path, encoding='ascii', errors='replace').read().splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#') or line.count('|') != 2: continue
            cmd = line.split('|')[2].strip()
            word, _, arg = cmd.partition(' ')
            arg = arg.strip()
            where = '%s:%d: %s' % (os.path.basename(radial_path), n, cmd)
            if word == 'overlay.larain':
                counts[word] = counts.get(word, 0) + 1
                if arg: problems.append(where + ' (no argument in the ring)')
            elif word == 'pos.goload' and not re.fullmatch(r'[A-Za-z0-9_-]+', arg):
                problems.append(where + ' (a saved name or last)')
            elif word == 'time.scale':
                try:
                    ok = 0.0 <= float(arg) <= 10.0
                except ValueError:
                    ok = False
                if not ok: problems.append(where + ' (a number 0 .. 10)')
        if counts.get('overlay.larain', 0) != 1:
            problems.append('%s: overlay.larain must be in the radial file once, found %d'
                            % (os.path.basename(radial_path), counts.get('overlay.larain', 0)))
    return problems, '%d pages (%d special), %d label + %d planned rows, %d confirm rows, %d new items, %d keys' % (
        len(pages) + len(special), len(special), labels, planned, confirm, len(Q18_ITEMS), len(Q18_KEYS))


def check_019(ini_path, radial_path, rows):
    """0.19 (2026-11-06 TruMenu 0.19 dumb AI): the [AI] keys, every INI comment < 512 characters, the ai.* items, the
    presets of kAiPresets, the bar's ai.dumb rows (presets) and Barrierefreiheit page, the ring's ai.* entries, the 0.19
    precheck tables (present, at most 64 bytes a check - HexBytesAt's buffer)"""
    problems = []
    name = os.path.basename(ini_path)
    src = read_cpp()
    found = {}
    for n, key, value in ini_section(ini_path, 'AI'):
        found[key] = (n, value)
    for key in AI_KEYS:
        if key not in found:
            problems.append('%s: [AI] %s missing' % (name, key))
            continue
        n, value = found[key]
        where = '%s:%d: [AI] %s=%s' % (name, n, key, value)
        if key == 'Dumb' and value not in ('0', '1', '2'): problems.append(where + ' (0 / 1 / 2)')
        elif key == 'DumbFilter' and value and not re.fullmatch(r'[A-Za-z0-9_]+( *, *[A-Za-z0-9_]+)*', value):
            problems.append(where + ' (comma list of name parts a-z 0-9 _, or empty)')
        elif key == 'DumbMode' and value not in ('purge', 'gate'): problems.append(where + ' (purge / gate)')
        elif key in ('NoInvestigate', 'NoAttack') and value not in ('0', '1'): problems.append(where + ' (0 / 1)')
    for sec, key, default, comment in rows:
        if len(comment) >= 512:
            problems.append('TruMenu.cpp: kOpts [%s] %s comment has %d characters (at most 511 - DefaultIniText cut there '
                            'until 0.22.24, kept as the limit)'
                            % (sec, key, len(comment)))
    items = item_types(src)
    for item, typ in sorted(Q19_ITEMS.items()):
        if items.get(item) != typ: problems.append('TruMenu.cpp: item %s (%s) missing in kItems' % (item, typ))
    m = re.search(r'const AiPreset kAiPresets\[\] = \{(.*?)\};', src, re.S)
    cpp_presets = tuple(re.findall(r'\{"([a-z]+)", "', m.group(1))) if m else ()
    if cpp_presets != AI_PRESETS:
        problems.append('TruMenu.cpp: kAiPresets %s differs from this tool %s' % (cpp_presets, AI_PRESETS))
    for table in ('kAiChecks', 'kAiGateChecks', 'kAiBitChecks'):
        m = re.search(r'const DvCheck %s\[\] = \{(.*?)\n\};' % table, src, re.S)
        if not m:
            problems.append('TruMenu.cpp: %s missing' % table)
            continue
        for a, h in re.findall(r'\{(0x[0-9a-fA-F]+), "([0-9a-fA-F ]+)"\}', m.group(1)):
            hexs = h.replace(' ', '')
            if len(hexs) % 2 or len(hexs) // 2 > 64:
                problems.append('TruMenu.cpp: %s %s "%s" (whole bytes, at most 64)' % (table, a, h))
    bar_ai = {}
    access = []
    for table, de, item, arg, kind, layer, tail in qb_rows(src, True):
        if item == 'ai.dumb':
            if kind != 'kQbBool': problems.append('TruMenu.cpp: %s row "%s": ai.dumb rows are bool rows' % (table, de))
            bar_ai[arg] = bar_ai.get(arg, 0) + 1
        if item == 'ai.mode' and kind != 'kQbValue':
            problems.append('TruMenu.cpp: %s row "%s": ai.mode is a value row' % (table, de))
        if table == 'kQbAccess': access.append((de, item, arg, kind))
    for want in AI_SETTINGS:
        if not bar_ai.get(want): problems.append('TruMenu.cpp: no bar row ai.dumb %s' % want)
    if any(de == 'Haie' and kind == 'kQbPlanned' for de, item, arg, kind in access):
        problems.append('TruMenu.cpp: kQbAccess still has the planned row "Haie" (0.19: ai.dumb sharks)')
    for want in ('sharks', 'spiders'):
        if not any(item == 'ai.dumb' and arg == want for de, item, arg, kind in access):
            problems.append('TruMenu.cpp: kQbAccess has no row ai.dumb %s' % want)
    counts, access_ring = {}, set()
    if os.path.exists(radial_path):
        for n, line in enumerate(open(radial_path, encoding='ascii', errors='replace').read().splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#') or line.count('|') != 2: continue
            path, label, cmd = (x.strip() for x in line.split('|'))
            word, _, arg = cmd.partition(' ')
            arg = arg.strip()
            where = '%s:%d: %s' % (os.path.basename(radial_path), n, cmd)
            if word == 'ai.dumb':
                if arg not in AI_SETTINGS:
                    problems.append(where + ' (exactly one of %s - the ring adds 0 / 1)' % ' / '.join(AI_SETTINGS))
                counts[word + ' ' + arg] = counts.get(word + ' ' + arg, 0) + 1
                if path.lower() == 'spieler/barrierefreiheit': access_ring.add(arg)
            elif word in ('ai.noinvestigate', 'ai.noattack', 'ai.status'):
                counts[word] = counts.get(word, 0) + 1
                if arg: problems.append(where + ' (no argument in the ring)')
            elif word == 'ai.mode' and arg not in ('purge', 'gate'):
                problems.append(where + ' (purge / gate)')
        for want in ('ai.noinvestigate', 'ai.noattack', 'ai.status'):
            if counts.get(want, 0) != 1:
                problems.append('%s: %s must be in the radial file once, found %d'
                                % (os.path.basename(radial_path), want, counts.get(want, 0)))
        for want in ('all', 'sharks', 'spiders'):
            if not counts.get('ai.dumb ' + want):
                problems.append('%s: ai.dumb %s missing in the radial file' % (os.path.basename(radial_path), want))
        for want in ('sharks', 'spiders'):
            if want not in access_ring:
                problems.append('%s: Spieler/Barrierefreiheit has no ai.dumb %s' % (os.path.basename(radial_path), want))
    return problems, '%d [AI] keys, %d items, presets %s, %d bar ai.dumb rows, %d ring ai.* entries' % (
        len(AI_KEYS), len(Q19_ITEMS), '/'.join(cpp_presets), sum(bar_ai.values()), sum(counts.values()))


def check_020(ini_path, radial_path, rows):
    """0.20 (2026-11-06 TruMenu 0.20): the [Media] mute keys 0 / 1, the new defaults (DumbMode gate, Depth 2, FlatPasses
    0x600) in kOpts, the new items in kItems, the bar rows the owner asked for (collectibles on Leveldaten, enemies /
    enemy health / edges on Render / KI, the mutes on Zeit / Test, game.quit as the LAST row of Notfall), the ring entries
    once without an argument, the 0.20 precheck tables present with at most 64 bytes a check"""
    problems = []
    name = os.path.basename(ini_path)
    src = read_cpp()
    found = {k: (n, v) for n, k, v in ini_section(ini_path, 'Media')}
    for key in Q20_MEDIA_KEYS:
        if key not in found: problems.append('%s: [Media] %s missing' % (name, key))
        elif found[key][1] not in ('0', '1'):
            problems.append('%s:%d: [Media] %s=%s (0 / 1)' % (name, found[key][0], key, found[key][1]))
    defaults = {(sec, key): default for sec, key, default, comment in rows}
    for sec, key, want in Q20_DEFAULTS:
        if defaults.get((sec, key)) != want:
            problems.append('TruMenu.cpp: kOpts [%s] %s default "%s", want "%s" (0.20)' % (sec, key, defaults.get((sec, key)),
                                                                                       want))
    items = item_types(src)
    for item, typ in sorted(Q20_ITEMS.items()):
        if items.get(item) != typ: problems.append('TruMenu.cpp: item %s (%s) missing in kItems' % (item, typ))
    bar = qb_rows(src, True)
    for table, item, arg in Q20_BAR:
        if not any(t == table and i == item and a == arg for t, de, i, a, kind, layer, tail in bar):
            problems.append('TruMenu.cpp: %s has no row %s%s' % (table, item, ' ' + arg if arg else ''))
    emergency = [r for r in bar if r[0] == 'kQbRescue']   # 0.22.16: Notfall merged into Rettung / Cheats
    if emergency and emergency[-1][2] != 'game.quit':
        problems.append('TruMenu.cpp: kQbRescue - game.quit must be the last row (got %s)' % emergency[-1][2])
    for t, de, i, a, kind, layer, tail in bar:
        if i == 'game.quit' and ('kQfConfirm' in tail or kind != 'kQbAction'):
            problems.append('TruMenu.cpp: %s row "%s": game.quit is a plain action row (the item arms itself, 10 s)'
                            % (t, de))
    counts = {}
    if os.path.exists(radial_path):
        for n, line in enumerate(open(radial_path, encoding='ascii', errors='replace').read().splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#') or line.count('|') != 2: continue
            cmd = line.split('|')[2].strip()
            word, _, arg = cmd.partition(' ')
            if word in Q20_RING or word == 'pos.portal':
                counts[word] = counts.get(word, 0) + 1
                if arg.strip(): problems.append('%s:%d: %s (no argument in the ring)' % (os.path.basename(radial_path), n,
                                                                                         cmd))
        for want in Q20_RING:
            if counts.get(want, 0) != 1:
                problems.append('%s: %s must be in the radial file once, found %d'
                                % (os.path.basename(radial_path), want, counts.get(want, 0)))
        if counts.get('pos.portal'):
            problems.append('%s: pos.portal is a pos.goload step, not a ring entry' % os.path.basename(radial_path))
    for tbl in ('kCoChecks', 'kAiForgetChecks', 'kSndMusicChecks'):
        m = re.search(r'const DvCheck %s\[\] = \{(.*?)\n\};' % tbl, src, re.S)
        if not m:
            problems.append('TruMenu.cpp: %s missing' % tbl)
            continue
        body = re.sub(r'"\s*\n\s*"', '', m.group(1))           # a literal split over two lines is one literal
        for a, h in re.findall(r'\{(0x[0-9a-fA-F]+), "([0-9a-fA-F ]+)"\}', body):
            hexs = h.replace(' ', '')
            if len(hexs) % 2 or len(hexs) // 2 > 64:
                problems.append('TruMenu.cpp: %s %s (whole bytes, at most 64; got %d)' % (tbl, a, len(hexs) // 2))
    return problems, '%d items, [Media] %d keys, %d bar rows, %d ring entries, defaults %s' % (
        len(Q20_ITEMS), len(Q20_MEDIA_KEYS), len(Q20_BAR), sum(counts.get(w, 0) for w in Q20_RING),
        ', '.join('%s %s' % (k, v) for s, k, v in Q20_DEFAULTS))


def snd_value_ok(rule, v):
    if rule == 'bool': return v in ('0', '1')
    if isinstance(rule[0], str): return v.lower() in rule
    try:
        x = float(v)
    except ValueError:
        return False
    return rule[0] <= x <= rule[1] and (isinstance(rule[0], float) or v.isdigit())


def check_0201(ini_path, radial_path):
    """0.20.1 (2026-11-06 sound list): [Sound] values, [Debug] EnemyStateLog, the snd.* items (snd.dump on the game
    thread), the bar rows, the ring entries and their arguments, the precheck tables, the mute order in SndMuteTick"""
    problems = []
    name = os.path.basename(ini_path)
    src = read_cpp()
    found = {k: (n, v) for n, k, v in ini_section(ini_path, 'Sound')}
    for key, rule in Q201_KEYS:
        if key not in found:
            problems.append('%s: [Sound] %s missing' % (name, key))
        elif not snd_value_ok(rule, found[key][1]):
            problems.append('%s:%d: [Sound] %s=%s (%s)' % (name, found[key][0], key, found[key][1],
                                                           '0 / 1' if rule == 'bool' else ' .. '.join(map(str, rule))
                                                           if not isinstance(rule[0], str) else ' / '.join(rule)))
    dbg = {k: (n, v) for n, k, v in ini_section(ini_path, 'Debug')}
    if 'EnemyStateLog' not in dbg: problems.append('%s: [Debug] EnemyStateLog missing' % name)
    elif dbg['EnemyStateLog'][1] not in ('0', '1'):
        problems.append('%s:%d: [Debug] EnemyStateLog=%s (0 / 1)' % (name, dbg['EnemyStateLog'][0],
                                                                     dbg['EnemyStateLog'][1]))
    items = item_types(src)
    for item, typ in sorted(Q201_ITEMS.items()):
        if items.get(item) != typ: problems.append('TruMenu.cpp: item %s (%s) missing in kItems' % (item, typ))
    m = re.search(r'\{"snd\.dump", "action", (?:"[^"]*"\s*)+, (true|false),', src)
    if not m or m.group(1) != 'true':
        problems.append('TruMenu.cpp: snd.dump must run on the game thread (gameThread true)')
    bar = qb_rows(src)
    for table, item, kind in Q201_BAR:
        if not any(t == table and i == item and k == kind and not a for t, de, i, a, k, layer in bar):
            problems.append('TruMenu.cpp: %s has no %s row %s' % (table, kind, item))
    counts, levels = {}, {}
    if os.path.exists(radial_path):
        rname = os.path.basename(radial_path)
        for n, line in enumerate(open(radial_path, encoding='ascii', errors='replace').read().splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#') or line.count('|') != 2: continue
            path, _, cmd = [p.strip() for p in line.split('|')]
            word, _, arg = cmd.partition(' ')
            arg = arg.strip()
            if not word.startswith('snd.'): continue
            key = word + (' ' + arg if arg else '')
            counts[key] = counts.get(key, 0) + 1
            levels.setdefault(word, set()).add(path)
            where = '%s:%d: %s' % (rname, n, cmd)
            if word not in Q201_ITEMS: problems.append(where + ' (unknown snd.* item)')
            elif word == 'snd.pos' and arg not in SND_POS: problems.append(where + ' (bl / tl / tr / br)')
            elif word == 'snd.sort' and arg not in SND_SORT: problems.append(where + ' (group / volume / name)')
            elif word == 'snd.lines' and not (arg.isdigit() and 1 <= int(arg) <= 40): problems.append(where + ' (1 .. 40)')
            elif word == 'snd.refresh' and not (arg.isdigit() and 100 <= int(arg) <= 10000):
                problems.append(where + ' (100 .. 10000)')
            elif word == 'snd.scale' and not snd_value_ok((0.5, 3.0), arg): problems.append(where + ' (0.5 .. 3)')
            elif (Q201_ITEMS[word] in ('bool', 'info') or word == 'snd.dump') and arg:
                problems.append(where + ' (no argument)')
        for pos in SND_POS:
            if counts.get('snd.pos ' + pos, 0) != 1:
                problems.append('%s: snd.pos %s must be in the ring once, found %d'
                                % (rname, pos, counts.get('snd.pos ' + pos, 0)))
        for want in ('Zeit', 'Spieler/Debug/Ton'):
            if want not in levels.get('snd.list', set()):
                problems.append('%s: snd.list missing in level %s' % (rname, want))
        if counts.get('snd.dump', 0) != 1:
            problems.append('%s: snd.dump must be in the ring once, found %d' % (rname, counts.get('snd.dump', 0)))
    for tbl in Q201_TABLES:
        mt = re.search(r'const DvCheck %s\[\] = \{(.*?)\n\};' % tbl, src, re.S)
        if not mt:
            problems.append('TruMenu.cpp: %s missing' % tbl)
            continue
        body = re.sub(r'"\s*\n\s*"', '', mt.group(1))
        for a, h in re.findall(r'\{(0x[0-9a-fA-F]+), "([0-9a-fA-F ]+)"\}', body):
            hexs = h.replace(' ', '')
            if len(hexs) % 2 or len(hexs) // 2 > 64:
                problems.append('TruMenu.cpp: %s %s (whole bytes, at most 64; got %d)' % (tbl, a, len(hexs) // 2))
    ms = re.search(r'\nvoid SndMuteTick\(\) \{(.*?)\n\}', src, re.S)
    body = ms.group(1) if ms else ''
    if 'SmMuteOn()' not in body or not (0 <= body.find('g_smOk') < body.find('g_sndOk')):
        problems.append('TruMenu.cpp: SndMuteTick must try the FMOD group mute (g_smOk / SmMuteOn) before the 0.20 path')
    return problems, '%d items, [Sound] %d keys + [Debug] EnemyStateLog, %d bar rows, %d ring snd.* entries, tables %s' % (
        len(Q201_ITEMS), len(Q201_KEYS), len(Q201_BAR), sum(counts.values()), ' / '.join(Q201_TABLES))


def q21_value_ok(rule, v):
    if rule == 'bool': return v in ('0', '1')
    if rule == 'list': return bool(re.fullmatch(r'[A-Za-z0-9_]+( *, *[A-Za-z0-9_]+)*', v))
    if rule == 'list0': return not v or bool(re.fullmatch(r'[A-Za-z0-9_]+( *, *[A-Za-z0-9_]+)*', v))
    if rule == 'png': return bool(v) and v.lower().endswith('.png') and not re.search(r'[<>"|?*]', v)
    try:
        x = float(v)
    except ValueError:
        return False
    return rule[0] <= x <= rule[1] and (isinstance(rule[0], float) or v.isdigit())


def check_021(ini_path, radial_path, rows):
    """0.21 (2026-11-07 Arachnophobie / camera / labels / ai.remove): [Arachno] / [Camera] values, the new defaults
    (Enabled 0, ShakeScale / Rumble 100, Sound Position br), the items (types, game thread), the bar rows (the planned
    rows Arachnophobie / Kamera-Wackeln aus replaced, ai.remove with a confirmation, the Koop page with planned rows only,
    right after Barrierefreiheit), the ring entries of these items (arguments), the precheck tables (at most 64 bytes),
    the slot-7 hook's mask order (set -1, the game's draw, the game's value back), no patch site on TruTrace's call bytes,
    and the owner-picture rules (.gitignore, Set-TruMenu.ps1, tools/pending_upload_scan.py)"""
    problems = []
    name = os.path.basename(ini_path)
    src = read_cpp()
    for section, keys in (('Arachno', Q21_ARACHNO_KEYS), ('Camera', Q21_CAMERA_KEYS)):
        found = {k: (n, v) for n, k, v in ini_section(ini_path, section)}
        for key, rule in keys:
            if key not in found:
                problems.append('%s: [%s] %s missing' % (name, section, key))
            elif not q21_value_ok(rule, found[key][1]):
                problems.append('%s:%d: [%s] %s=%s (%s)' % (name, found[key][0], section, key, found[key][1],
                                                            rule if isinstance(rule, str) else
                                                            ' .. '.join(map(str, rule))))
    defaults = {(sec, key): default for sec, key, default, comment in rows}
    for sec, key, want in Q21_DEFAULTS:
        if defaults.get((sec, key)) != want:
            problems.append('TruMenu.cpp: kOpts [%s] %s default "%s", want "%s" (0.21)' % (sec, key, defaults.get((sec, key)),
                                                                                       want))
    items = item_types(src)
    for item, typ in sorted(Q21_ITEMS.items()):
        if items.get(item) != typ: problems.append('TruMenu.cpp: item %s (%s) missing in kItems' % (item, typ))
    for item in Q21_GAME_THREAD:
        m = re.search(r'\{"%s", "action", (?:"[^"]*"\s*)+, (true|false),' % re.escape(item), src)
        if not m or m.group(1) != 'true':
            problems.append('TruMenu.cpp: %s must run on the game thread (gameThread true)' % item)
    bar = qb_rows(src, True)
    for table, item, kind, arg in Q21_BAR:
        if not any(t == table and i == item and k == kind and a == arg for t, de, i, a, k, layer, tail in bar):
            problems.append('TruMenu.cpp: %s has no %s row %s%s' % (table, kind, item, ' ' + arg if arg else ''))
    for t, de, i, a, k, layer, tail in bar:
        where = 'TruMenu.cpp: %s row "%s"' % (t, de)
        if t == 'kQbAccess' and k == 'kQbPlanned' and de in Q21_REPLACED:
            problems.append(where + ': still planned (0.21 built it)')
        if i == 'ai.remove':
            if a not in AD_ARGS + ('spawned',):   # 0.22.26: spawned = only ai.spawn's instances
                problems.append(where + ': ai.remove needs nearest / others / all / spawned')
            if k != 'kQbAction' or 'kQfConfirm' not in tail: problems.append(where + ': ai.remove = action row with kQfConfirm')
        if t == 'kQbCoop' and k not in ('kQbLabel', 'kQbPlanned', 'kQbGroup'):   # 0.22.18: the heading is a group
            problems.append(where + ': the Koop page has planned rows only (no function yet)')
    if not any(t == 'kQbCoop' and k == 'kQbPlanned' for t, de, i, a, k, layer, tail in bar):
        problems.append('TruMenu.cpp: kQbCoop has no planned row')
    pages = re.findall(r'QB_PAGE\("([^"]*)", "([^"]*)", (kQb[A-Za-z]+), (kQs[A-Za-z]+)\)', src)
    tables = [p[2] for p in pages]
    if 'kQbCoop' not in tables: problems.append('TruMenu.cpp: kQbPages has no page Koop (kQbCoop)')
    elif 'kQbAccess' in tables and tables.index('kQbCoop') != tables.index('kQbAccess') + 1:
        problems.append('TruMenu.cpp: page Koop must follow Barrierefreiheit')
    counts = {}
    if os.path.exists(radial_path):
        rname = os.path.basename(radial_path)
        for n, line in enumerate(open(radial_path, encoding='ascii', errors='replace').read().splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#') or line.count('|') != 2: continue
            cmd = line.split('|')[2].strip()
            word, _, arg = cmd.partition(' ')
            arg = arg.strip()
            if word not in Q21_ITEMS: continue
            counts[word] = counts.get(word, 0) + 1
            where = '%s:%d: %s' % (rname, n, cmd)
            if word in ('cam.shakescale', 'cam.rumble') and not (arg.isdigit() and int(arg) <= 100):
                problems.append(where + ' (0 .. 100)')
            elif word == 'ai.remove' and arg not in AD_ARGS and not arg.isdigit():
                problems.append(where + ' (nearest / others / all / an intro id)')
            elif word == 'cam.shake' and not arg.isdigit(): problems.append(where + ' (a shake number)')
            elif Q21_ITEMS[word] in ('bool', 'info') and arg: problems.append(where + ' (no argument)')
    for tbl in Q21_TABLES:
        mt = re.search(r'const DvCheck %s\[\] = \{(.*?)\n\};' % tbl, src, re.S)
        if not mt:
            problems.append('TruMenu.cpp: %s missing' % tbl)
            continue
        body = re.sub(r'"\s*\n\s*"', '', mt.group(1))
        for a, h in re.findall(r'\{(0x[0-9a-fA-F]+), "([0-9a-fA-F ]+)"\}', body):
            hexs = h.replace(' ', '')
            if len(hexs) % 2 or len(hexs) // 2 > 64:
                problems.append('TruMenu.cpp: %s %s (whole bytes, at most 64; got %d)' % (tbl, a, len(hexs) // 2))
    mh = re.search(r'\nvoid __fastcall ArDrawHook\(.*?\n\}', src, re.S)
    body = mh.group(0) if mh else ''
    i_set = body.find('AiPutDword(inst + 0x23c, 0xffffffffu)')
    i_draw = body.find('game(self, edx, a, b)', i_set if i_set >= 0 else 0)
    i_back = body.find('AiPutDword(inst + 0x23c, m23c)')
    if not (0 <= i_set < i_draw < i_back):
        problems.append('TruMenu.cpp: ArDrawHook must set +0x23c = -1, call the game\'s draw, then put the game\'s value back')
    mp = re.search(r'AiPatch g_arSndPatches\[\d+\] = \{(.*?)\n\};', src, re.S)
    sites = [int(x, 16) for x in re.findall(r'\{(0x[0-9a-fA-F]+),', mp.group(1))] if mp else []
    if len(sites) != 7: problems.append('TruMenu.cpp: g_arSndPatches must have the 6 call sites + the table word (got %d)'
                                        % len(sites))
    for s in sites:
        if s in TRUTRACE_BYTES: problems.append('TruMenu.cpp: sound gate patches 0x%x - TruTrace checks those bytes' % s)
    gi = os.path.join(ROOT, '.gitignore')
    gtext = open(gi, encoding='utf-8', errors='replace').read() if os.path.exists(gi) else ''
    for want in ('TruMenu.arachno*.png', 'work/arachno_owner/'):
        if want not in gtext.split('\n') and want + '\r' not in gtext.split('\n'):
            problems.append('.gitignore: line %s missing (owner picture)' % want)
    st = os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1')
    stext = open(st, encoding='utf-8-sig', errors='replace').read() if os.path.exists(st) else ''
    for line in stext.split('\n'):
        if re.search(r'\b(Copy-Item|Remove-Item)\b', line) and 'Assert-NotOwnerImage' not in line:
            problems.append('Set-TruMenu.ps1: "%s" without Assert-NotOwnerImage (owner picture rule)' % line.strip()[:80])
    if "$ownerImagePattern = 'TruMenu.arachno*.png'" not in stext:
        problems.append('Set-TruMenu.ps1: $ownerImagePattern = \'TruMenu.arachno*.png\' missing')
    us = os.path.join(ROOT, 'tools', 'pending_upload_scan.py')
    utext = open(us, encoding='utf-8', errors='replace').read() if os.path.exists(us) else ''
    if 'arachno_owner' not in utext or r'\.arachno' not in utext:
        problems.append('tools/pending_upload_scan.py: the Owner rule (*.arachno*.png, work/arachno_owner/) missing')
    return problems, ('%d items, [Arachno] %d + [Camera] %d keys, %d bar rows, Koop page, %d ring entries, tables %s, '
                      'owner-picture rules' % (len(Q21_ITEMS), len(Q21_ARACHNO_KEYS), len(Q21_CAMERA_KEYS), len(Q21_BAR),
                                               sum(counts.values()), ' / '.join(Q21_TABLES)))


def check_0211(ini_path, radial_path, rows):
    """0.21.1 (2026-11-07 ai.kill / sticky / room check / physics / spawn / bar): the items (types, threads), [Quick]
    Closed / RecentMax / Recent, the bar (page 0 Favoriten / Zuletzt = kQsFav, page Tests = kQbTests + kQsTests after
    Zeit / Test, the three KI groups on Render / KI with their keys unique and an item inside, ai.kill rows with a
    confirmation and nearest / others / all, the hall02 repair rows), the ring entries of the new items, the precheck
    tables (whole bytes, at most 64, none on a byte another plugin patches), the kill path (types in order, the pick
    before the call, the game's own kill), sticky.set never creates an entry, player.goto takes the room check, the pot
    rule (placed intros only from drawn instances), the thrall-fight Prepare takes unit.go"""
    problems = []
    name = os.path.basename(ini_path)
    src = read_cpp()
    items = item_types(src)
    for item, typ in sorted(Q211_ITEMS.items()):
        if items.get(item) != typ: problems.append('TruMenu.cpp: item %s (%s) missing in kItems' % (item, typ))
    for item in Q211_GAME_THREAD + Q211_NOT_GAME_THREAD:
        m = re.search(r'\{"%s", "(?:action|info)", (?:"[^"]*"\s*)+,\s*(true|false),' % re.escape(item), src)
        want = 'true' if item in Q211_GAME_THREAD else 'false'
        if not m or m.group(1) != want:
            problems.append('TruMenu.cpp: %s must %srun on the game thread (gameThread %s)'
                            % (item, '' if want == 'true' else 'not ', want))
    found = {k: (n, v) for n, k, v in ini_section(ini_path, 'Quick')}
    for key, rule in Q211_QUICK_KEYS:
        if key not in found:
            problems.append('%s: [Quick] %s missing' % (name, key))
            continue
        n, v = found[key]
        if rule == 'groups': ok = not v or bool(re.fullmatch(r'[a-z0-9_]+(,[a-z0-9_]+)*', v))
        elif rule == 'recent': ok = not v or all(re.fullmatch(r'[a-z][a-z0-9_.]*( [^;]+)?', e) for e in v.split(';'))
        else: ok = v.isdigit() and rule[0] <= int(v) <= rule[1]
        if not ok: problems.append('%s:%d: [Quick] %s=%s (%s)' % (name, n, key, v, rule))
    defaults = {(sec, key): default for sec, key, default, comment in rows}
    for sec, key, want in Q211_SWITCHES:
        fs = {k: (n, v) for n, k, v in ini_section(ini_path, sec)}
        if key not in fs: problems.append('%s: [%s] %s missing' % (name, sec, key))
        elif fs[key][1] not in ('0', '1'): problems.append('%s:%d: [%s] %s=%s (0 / 1)' % (name, fs[key][0], sec, key, fs[key][1]))
    for sec, key, want in (('Quick', 'Closed', ''), ('Quick', 'RecentMax', '8'), ('Quick', 'Recent', '')) + Q211_SWITCHES:
        if defaults.get((sec, key)) != want:
            problems.append('TruMenu.cpp: kOpts [%s] %s default "%s", want "%s" (0.21.1)' % (sec, key, defaults.get((sec, key)),
                                                                                         want))
    block = src[src.index('const QbPage kQbPages[] = {'):]
    block = block[:block.index('\n};')]
    order = re.findall(r'(?:QB_PAGE\("([^"]*)", "[^"]*", (kQb[A-Za-z]+), (kQs[A-Za-z]+)\)|\{"([^"]*)", "[^"]*", nullptr, 0, '
                       r'(kQs[A-Za-z]+)\})', block)
    pages = [(a or d, b or None, c or e) for a, b, c, d, e in order]
    if not pages or pages[0][2] != 'kQsFav': problems.append('TruMenu.cpp: page 0 must be Favoriten / Zuletzt (kQsFav)')
    tables = [p[1] for p in pages]
    if 'kQbTests' not in tables: problems.append('TruMenu.cpp: kQbPages has no page Tests (kQbTests)')
    elif pages[tables.index('kQbTests')][2] != 'kQsTests': problems.append('TruMenu.cpp: page Tests needs kQsTests')
    elif 'kQbTimeTest' in tables and tables.index('kQbTests') != tables.index('kQbTimeTest') + 1:
        problems.append('TruMenu.cpp: page Tests must follow Zeit / Test')
    ms = re.search(r'const int kQbStartPage = (\d+);', src)
    if not ms or int(ms.group(1)) >= len(pages) or pages[int(ms.group(1))][1] != 'kQbLevel':
        problems.append('TruMenu.cpp: kQbStartPage must point at Leveldaten (kQbLevel)')
    bar = qb_rows(src, True)
    keys = {}
    group = None
    inside = {}
    for t, de, i, a, k, layer, tail in bar:
        where = 'TruMenu.cpp: %s row "%s"' % (t, de)
        if k == 'kQbGroup':
            if not re.fullmatch(r'[a-z0-9_]+', a): problems.append(where + ': a group needs a key a-z 0-9 _ (arg)')
            if a in keys: problems.append(where + ': group key %s twice (also %s)' % (a, keys[a]))
            keys[a] = de
            group = a
            inside[a] = []
            continue
        if k == 'kQbLabel': group = None
        elif group: inside[group].append(i)
        if i == 'ai.kill':
            if a not in AD_ARGS: problems.append(where + ': ai.kill needs nearest / others / all')
            if k != 'kQbAction' or 'kQfConfirm' not in tail: problems.append(where + ': ai.kill = action row with kQfConfirm')
        if i == 'sticky.set' and (k != 'kQbAction' or 'kQfConfirm' not in tail or not re.fullmatch(r'\d+ \d+ -?\d+', a)):
            problems.append(where + ': sticky.set = action row "<owner> <key> <value>" with kQfConfirm')
        if i == 'ai.spawn' and (k != 'kQbChoice' or 'kQfConfirm' not in tail or 'kQvSpawnKind' not in tail):
            problems.append(where + ': ai.spawn = choice row (kQvSpawnKind) with kQfConfirm')
    for key, item in Q211_GROUPS:
        if key not in keys: problems.append('TruMenu.cpp: group %s missing (KI page)' % key)
        elif item not in inside.get(key, []): problems.append('TruMenu.cpp: group %s has no %s row' % (key, item))
    # 0.22.16: the KI groups moved to page Gegner (KI) (kQbEnemies)
    renders = [k for k, _ in Q211_GROUPS
               if any(t == 'kQbEnemies' and kk == 'kQbGroup' and a == k for t, de, i, a, kk, layer, tail in bar)]
    if len(renders) != 3: problems.append('TruMenu.cpp: Gegner (KI) needs the three KI groups (got %d)' % len(renders))
    for want in ('11270 17287 0', '11270 18509 2'):
        if not any(i == 'sticky.set' and a == want for t, de, i, a, k, layer, tail in bar):
            problems.append('TruMenu.cpp: no bar row sticky.set %s (hall02 repair)' % want)
    if not any(i == 'phys.status' and k == 'kQbInfo' and 'kQcPhys' in layer + tail for t, de, i, a, k, layer, tail in bar):
        problems.append('TruMenu.cpp: no info row phys.status with the count kQcPhys')
    counts = {}
    if os.path.exists(radial_path):
        rname = os.path.basename(radial_path)
        for n, line in enumerate(open(radial_path, encoding='ascii', errors='replace').read().splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#') or line.count('|') != 2: continue
            cmd = line.split('|')[2].strip()
            word, _, arg = cmd.partition(' ')
            arg = arg.strip()
            if word not in Q211_ITEMS: continue
            counts[word] = counts.get(word, 0) + 1
            where = '%s:%d: %s' % (rname, n, cmd)
            if word == 'ai.kill' and arg not in AD_ARGS and not arg.isdigit():
                problems.append(where + ' (nearest / others / all / an intro id)')
            elif word == 'sticky.set' and not re.fullmatch(r'((int|bool|float) )?(\d:)?\w+ \d+ \S+', arg):
                problems.append(where + ' ([type] <owner> <key> <value>)')
            elif word == 'unit.go' and not re.fullmatch(r'[A-Za-z0-9_]+', arg): problems.append(where + ' (one unit name)')
            elif Q211_ITEMS[word] == 'info' and arg: problems.append(where + ' (no argument)')
    for tbl in Q211_TABLES:
        mt = re.search(r'const DvCheck %s\[\] = \{(.*?)\n\};' % tbl, src, re.S)
        if not mt:
            problems.append('TruMenu.cpp: %s missing' % tbl)
            continue
        body = re.sub(r'"\s*\n\s*"', '', mt.group(1))
        for a, h in re.findall(r'\{(0x[0-9a-fA-F]+), "([0-9a-fA-F ]+)"\}', body):
            hexs = h.replace(' ', '')
            if len(hexs) % 2 or len(hexs) // 2 > 64:
                problems.append('TruMenu.cpp: %s %s (whole bytes, at most 64; got %d)' % (tbl, a, len(hexs) // 2))
            lo, hi = int(a, 16), int(a, 16) + len(hexs) // 2
            for f, size in Q211_FOREIGN:
                if lo < f + size and f < hi:
                    problems.append('TruMenu.cpp: %s %s covers 0x%x - another plugin patches it' % (tbl, a, f))
    if Q211_KILL_TYPES not in src: problems.append('TruMenu.cpp: kAkTypes must be %s (the game\'s own type first)' % Q211_KILL_TYPES)
    mk = re.search(r'\nbool RunAkKill\([^;{]*\) \{.*?\n\}', src, re.S)
    body = mk.group(0) if mk else ''
    i_pick, i_call = body.find('AkPick('), body.find('AkKillOne(')
    if not (0 <= i_pick < i_call): problems.append('TruMenu.cpp: RunAkKill must pick the kill path (AkPick) before AkKillOne')
    if 'kAkKill = 0x006376e0' not in src: problems.append('TruMenu.cpp: ai.kill must call the game\'s Kill 0x6376e0')
    ma = re.search(r'\nconst char \*AkPick\([^;{]*\) \{.*?\n\}', src, re.S)
    pick = ma.group(0) if ma else ''
    for need in ('0x800', 'fc & 2', 'AkDying', 'AkCaseOf(t) != 0', '0x2c60 + 0x1c', 'kAkRegen'):
        if need not in pick: problems.append('TruMenu.cpp: AkPick lacks the rule "%s"' % need)
    mset = re.search(r'\nbool RunStickySet\([^;{]*\) \{.*?\n\}', src, re.S)
    sbody = mset.group(0) if mset else ''
    if '0x4aee30' in sbody or '0x4b16a0' in sbody or 'StFind(' not in sbody:
        problems.append('TruMenu.cpp: sticky.set must find the entry itself (StFind) and never call Find / create 0x4aee30 / '
                        '0x4b16a0')
    mf = re.search(r'\nint StFind\([^;{]*\) \{.*?\n\}', src, re.S)
    if not mf or re.search(r'WriteDword|AiPutDword|volatile|\(\*reinterpret_cast', mf.group(0)):
        problems.append('TruMenu.cpp: StFind must only read (ReadDword / ReadWord / ReadByte)')
    mg = re.search(r'\nbool RunGoto\([^;{]*\) \{.*?\n\}', src, re.S)
    gbody = mg.group(0) if mg else ''
    i_rk, i_set = gbody.find('RkCheck('), gbody.find('SetPosition(')
    if not (0 <= i_rk < i_set) or 'force' not in gbody:
        problems.append('TruMenu.cpp: player.goto must run the room check (RkCheck, "force") before SetPosition')
    mm = re.search(r'\nvoid M20Draw\([^;{]*\) \{.*?\n\}', src, re.S)
    mbody = mm.group(0) if mm else ''
    i_nd = mbody.find('if (LfNotDrawn(inst)) {      // 0.21: picked up')
    if i_nd < 0:   # 0.22.37 (P5): collected ones with LabelCollected 1 reach the else branch grey - the register needs !nd
        i_nd = mbody.find('if ((nd && !bit) || (bit && !g_lblCollected)) {   // 0.21: picked up')
        if 'if (intro && placed && !nd && placedN < 256) {' not in mbody: i_nd = -1
    i_reg = mbody.find('placedIntro[placedN] = intro;')
    i_else = mbody.find('} else {', i_nd)
    if not (0 <= i_nd < i_else < i_reg): problems.append('TruMenu.cpp: M20Draw must register placed intros only for drawn '
                                                         'instances (0.21.1 pot rule)')
    reg = os.path.join(ROOT, 'tests', 'regress', 'dlc2.txt')
    rtext = open(reg, encoding='ascii', errors='replace').read() if os.path.exists(reg) else ''
    if '#Thrall fight: hall02 + god mode;unit.go dlc_yggdrasil_hall02;' not in rtext:
        problems.append('tests/regress/dlc2.txt: the thrall-fight Prepare must take unit.go dlc_yggdrasil_hall02')
    return problems, ('%d items, [Quick] %d keys, pages 0 / Tests, %d groups, %d ring entries, tables %s, kill path, sticky, '
                      'room check, pot rule, Prepare' % (len(Q211_ITEMS), len(Q211_QUICK_KEYS), len(keys),
                                                        sum(counts.values()), ' / '.join(Q211_TABLES)))


def fn_body(src, head):
    """the text of a top-level function (head = the start of its line, e.g. 'void QuickTick('), '' when missing"""
    m = re.search(r'\n' + re.escape(head) + r'[^;{]*\) \{.*?\n\}', src, re.S)
    return m.group(0) if m else ''


def check_0213(ini_path):
    """0.21.3 (2026-11-07 quick bar X / Y, sound list width): see the module text"""
    problems = []
    src = read_cpp()
    m = re.search(r'const WORD kQbOwn = (0x[0-9A-Fa-f]+);', src)
    if not m or int(m.group(1), 16) != QB_OWN:
        problems.append('TruMenu.cpp: kQbOwn must be 0x%04X (D-pad / LB / RB + X / Y), got %s' % (QB_OWN, m.group(1) if m
                                                                                                     else 'none'))
    if not re.search(r'const WORD kQbX = 0x4000, kQbY = 0x8000;', src):
        problems.append('TruMenu.cpp: kQbX / kQbY must be 0x4000 / 0x8000 (XINPUT_GAMEPAD_X / _Y)')
    tick = fn_body(src, 'void QuickTick(')
    i_y, i_x, i_d = tick.find('if (edges & kQbY)'), tick.find('if (edges & kQbX)'), tick.find('QbAct(g_qbPage')
    if not (0 <= i_y < i_x < i_d):
        problems.append('TruMenu.cpp: QuickTick must take Y (QbFavPin) before X (QbExecRow) before left / right (QbAct)')
    else:
        yb, xb = tick[i_y:i_x], tick[i_x:i_d]
        if 'QbFavPin(' not in yb or 'return;' not in yb:
            problems.append('TruMenu.cpp: QuickTick: Y must call QbFavPin and return (no other press in that frame)')
        if 'QbExecRow(' not in xb or 'return;' not in xb or 'QbSpecialAct(p.special, row - g_qbStaticN, ' not in xb:
            problems.append('TruMenu.cpp: QuickTick: X must call QbExecRow (special rows: QbSpecialAct dir 1) and return')
    if 'pad.wButtons & kQbOwn' not in tick:
        problems.append('TruMenu.cpp: QuickTick must read the open bar\'s buttons as pad.wButtons & kQbOwn')
    ex = fn_body(src, 'void QbExecRow(')
    mv = re.search(r'case kQbValue:(.*?)return;', ex, re.S)
    if not ex: problems.append('TruMenu.cpp: QbExecRow missing')
    else:
        # 0.22.51 (e, owner 2026-11-14): X on a value row = its default, through QbActRow with kQbDefDir (was: nothing)
        if not mv or 'QbActRow(page, r, kQbDefDir);' not in mv.group(1) or 'QbRun' in mv.group(1):
            problems.append('TruMenu.cpp: QbExecRow: X on a value row = QbActRow(page, r, kQbDefDir) (0.22.51: the default)')
        mb = re.search(r'case kQbBool:(.*?)return;', ex, re.S)
        if not mb or 'QbRowOn(r)' not in mb.group(1) or '? -1 : 1' not in mb.group(1):
            problems.append('TruMenu.cpp: QbExecRow: X on a bool row must toggle from QbRowOn (on -> -1, off -> +1)')
        if 'default: QbActRow(page, r, 1);' not in ex:
            problems.append('TruMenu.cpp: QbExecRow: action / choice / info / planned rows = the right press '
                            '(QbActRow(page, r, 1)) - keeps the confirmation rows')
        if 'QbRun(' in ex or 'InvokeCore(' in ex or 'QbConfirm(' in ex:
            problems.append('TruMenu.cpp: QbExecRow must not run items itself (only through QbActRow)')
    fav = fn_body(src, 'void QbFavPin(')
    # 0.21.8: rows with an argument are pinnable ("<id>|<argument>"); the argument passes FavArgOk before FavSetArg
    # (0.21.3: refused before FavSet)
    i_arg, i_set = fav.find('if (!FavArgOk(r->arg))'), fav.find('FavSetArg(r->id, r->arg')
    if not (0 <= i_arg < i_set):
        problems.append('TruMenu.cpp: QbFavPin must check the argument (FavArgOk) before FavSetArg ([Favorites] Ids)')
    if fav and ('WritePrivateProfileString' in fav or 'g_favs' in fav or 'FavHasArg(r->id, r->arg)' not in fav):
        problems.append('TruMenu.cpp: QbFavPin must toggle through FavHasArg / FavSetArg only (no own write of the '
                        'favourites)')
    draw = fn_body(src, 'void DrawQuick(')
    for t in Q213_FOOTER:
        if t not in draw: problems.append('TruMenu.cpp: DrawQuick lacks the footer text %s' % t)
    conf = fn_body(src, 'bool QbConfirm(')
    for t in Q213_CONFIRM:
        if t not in conf: problems.append('TruMenu.cpp: QbConfirm lacks %s (X arms / confirms as right)' % t)
    pb = fn_body(src, 'extern "C" __declspec(dllexport) DWORD __cdecl TruMenuPadBlock(')
    for need in ('if (bar) out |= kQbOwn;', 'out |= static_cast<DWORD>(g_qbPad[pad].owned | g_qbPad[pad].gated);',
                 'out &= 0xFFFF;', 'out |= 1u << 16;', 'out |= 1u << 17;', 'out |= 1u << 18;'):
        if need not in pb: problems.append('TruMenu.cpp: TruMenuPadBlock changed its meaning (missing "%s")' % need)
    opts = {(s, k): c for s, k, d, c in table(src)[1]}
    if 'X = run' not in opts.get(('Quick', 'Enabled'), '') or 'X and Y are kept' not in opts.get(('Quick', 'Enabled'), ''):
        problems.append('TruMenu.cpp: kOpts [Quick] Enabled comment must name X / Y (run, favourite, kept from the game)')
    if 'X or Y' not in opts.get(('Quick', 'OpenButtons'), ''):
        problems.append('TruMenu.cpp: kOpts [Quick] OpenButtons comment must forbid X / Y')
    sr = fn_body(src, 'void SnRow(')
    if not sr or 'float edge' not in sr or 'GetContentRegionAvail' in sr:
        problems.append('TruMenu.cpp: SnRow must align to the frame\'s widest row (edge), not the window\'s content width')
    sd = fn_body(src, 'void DrawSoundList(')
    i_meas, i_row = sd.find('CalcTextSize(g_snRowBuf[i].text)'), sd.find('SnRow(')
    if not (0 <= i_meas < i_row):
        problems.append('TruMenu.cpp: DrawSoundList must measure every row (CalcTextSize) before it draws one (SnRow)')
    if 'ImGuiWindowFlags_AlwaysAutoResize' not in sd:
        problems.append('TruMenu.cpp: DrawSoundList: the box must stay AlwaysAutoResize')
    return problems, 'kQbOwn 0x%04X, Y > X > left / right, X / Y rules, footer + confirm texts, TruMenuPadBlock, sound ' \
                     'list width' % QB_OWN


def check_0214(ini_path, rows):
    """0.21.4 (2026-11-07 hall02 counter): see the module text"""
    problems = []
    name = os.path.basename(ini_path)
    src = read_cpp()
    for item, (typ, thread) in sorted(Q214_ITEMS.items()):
        m = re.search(r'\{"%s", "%s", (?:"[^"]*"\s*)+,\s*(true|false),' % (re.escape(item), typ), src)
        if not m: problems.append('TruMenu.cpp: item %s (%s) missing in kItems' % (item, typ))
        elif m.group(1) != thread:
            problems.append('TruMenu.cpp: %s gameThread must be %s' % (item, thread))
    m = re.search(r'\{"fix\.hall02", "action", ((?:"[^"]*"\s*)+),', src)
    if not m or 'already holds tutorial' not in ''.join(re.findall(r'"([^"]*)"', m.group(1))).replace('  ', ' '):
        problems.append('TruMenu.cpp: the fix.hall02 help text must say it is for saves whose checkpoint 11258 already '
                        'holds tutorial thralls')
    # E3 was dropped (docs/Befund-Hall02-TU-Vergleich-0711.md: PC data bug, the Xbox never restores thralls there)
    ini_text = open(ini_path, encoding='utf-8', errors='replace').read()
    for word in Q214_DROPPED:
        if word in src: problems.append('TruMenu.cpp: %s present - the E3 safety net must not be built' % word)
        if word in ini_text: problems.append('%s: %s present - the E3 safety net must not be built' % (name, word))
    if any(sec == 'Fix' for sec, key, default, comment in rows):
        problems.append('TruMenu.cpp: kOpts has a [Fix] section (E3 dropped)')
    tests = [r for r in qb_rows(src, True) if r[0] == 'kQbTests']
    want = {'fix.hall02': ('kQbAction', True), 'thrall.scriptval': ('kQbAction', False)}
    for item, (kind, confirm) in want.items():
        hit = [r for r in tests if r[2] == item]
        if not hit: problems.append('TruMenu.cpp: page Tests has no %s row' % item)
        elif hit[0][4] != kind or hit[0][3] or (confirm and 'kQfConfirm' not in hit[0][6]):
            problems.append('TruMenu.cpp: page Tests row %s must be %s without argument%s' % (
                item, kind, ' with kQfConfirm (right / X twice)' if confirm else ''))
    fx = fn_body(src, 'bool RunFixHall02(')
    marks = [fx.find(s) for s in ('_stricmp(unit, kH2Unit)', 'if (!hp || !ht || !hb)', 'if (broken)', 'if (alive)',
                                  'RunStickySet(')]
    if not fx or -1 in marks or marks != sorted(marks):
        problems.append('TruMenu.cpp: RunFixHall02 must refuse in this order before the first sticky.set: wrong unit, '
                        'missing dispatcher values, broken, a living thrall (got %s)' % marks)
    i_tut, i_pop = fx.find('RunStickySet("int 11270 18509 2"'), fx.find('RunStickySet("int 11270 17287 0"')
    if not (0 <= i_tut < i_pop): problems.append('TruMenu.cpp: RunFixHall02 sets tutorial (18509) before population (17287)')
    if 'if (tut < 2)' not in fx: problems.append('TruMenu.cpp: RunFixHall02 sets tutorial 2 only when it is below 2')
    if fx.count('RunStickySet(') != 2 or re.search(r'WriteDword|volatile|kStNotify', fx):
        problems.append('TruMenu.cpp: RunFixHall02 writes only through two sticky.set calls')
    for t in Q214_REPLY:
        if t not in fx: problems.append('TruMenu.cpp: the fix.hall02 reply lacks "%s"' % t)
    al = fn_body(src, 'bool H2Alive(')
    for need in ('0x44', 'flags & 0x20', 'AkDying(brain', 'flags & 0x800'):
        if need not in al: problems.append('TruMenu.cpp: H2Alive lacks the rule "%s"' % need)
    mn = re.search(r'const char \*const kAkDeathNames\[4\] = \{([^}]*)\}', src)
    if not mn or 'Regenerate' in mn.group(1):
        problems.append('TruMenu.cpp: kAkDeathNames must be the four count-event states (RegenerateDeath = alive)')
    va = fn_body(src, 'DWORD H2ValueAddr(')
    i60, ic, i8 = va.find('inst + kH2ScriptRef'), va.find('ref + kH2ScriptData'), va.find('data + kH2ThrallInt')
    if not (0 <= i60 < ic < i8) or '!ref' not in va or '!data' not in va:
        problems.append('TruMenu.cpp: H2ValueAddr must be [[inst+0x60]+0xc]+8 with zero pointers refused')
    for const, val in (('kH2ScriptRef', '0x60'), ('kH2ScriptData', '0xc'), ('kH2ThrallInt', '8'),
                       ('kH2RuntimeIntro', '0x40000000'), ('kH2ThrallObject', '1004')):
        if not re.search(r'\b%s = %s\b' % (const, val), src): problems.append('TruMenu.cpp: %s must be %s' % (const, val))
    sc = fn_body(src, 'bool H2IsThrall(')
    if 'kH2ThrallObject' not in sc or 'kH2ThrallName' not in sc:
        problems.append('TruMenu.cpp: H2IsThrall must match object 1004 by id and name')
    for fn in ('bool RunThrallScript(', 'void ValThrallScript(', 'int H2Scan(', 'DWORD H2ValueAddr(', 'bool H2Alive('):
        b = fn_body(src, fn)
        if not b or re.search(r'RunStickySet|kStNotify|WriteDword|volatile|values\[', b):
            problems.append('TruMenu.cpp: %s) must only read' % fn.strip('('))
    a, b = src.find('// ---- 0.21.4 hall02 counter'), src.find('// ---- end of 0.21.4')
    sec = src[a:b] if 0 <= a < b else ''
    if not sec: problems.append('TruMenu.cpp: section "0.21.4 hall02 counter" .. "end of 0.21.4" missing')
    elif re.search(r'WriteDword|VirtualProtect|WriteProcessMemory|volatile [A-Z]+ \*>?\(?[a-z.]*\)? *=|'
                   r'\*reinterpret_cast<volatile', sec):
        problems.append('TruMenu.cpp: section 0.21.4 must not patch code or store directly (only sticky.set writes)')
    mt = re.search(r'const DvCheck kH2Checks\[\] = \{(.*?)\n\};', src, re.S)
    if not mt: problems.append('TruMenu.cpp: kH2Checks missing')
    else:
        body = re.sub(r'"\s*\n\s*"', '', mt.group(1))
        for ad, h in re.findall(r'\{(0x[0-9a-fA-F]+), "([0-9a-fA-F ]+)"\}', body):
            hexs = h.replace(' ', '')
            if len(hexs) % 2 or len(hexs) // 2 > 64:
                problems.append('TruMenu.cpp: kH2Checks %s (whole bytes, at most 64)' % ad)
            lo, hi = int(ad, 16), int(ad, 16) + len(hexs) // 2
            for f, size in Q211_FOREIGN:
                if lo < f + size and f < hi: problems.append('TruMenu.cpp: kH2Checks %s covers 0x%x (another plugin)' % (ad, f))
    if 'M214Check();' not in src: problems.append('TruMenu.cpp: M214Check is never called')
    return problems, '2 items, page Tests rows, fix.hall02 help / guards / order / 18509 rule / reply, alive rule, +8 ' \
                     'address, read-only scriptval, no E3 safety net, kH2Checks'


SWITCHES = os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'TruMenu.switches.txt')
PLUGINS = os.path.join(ROOT, 'src', 'asi')
# 0.21.5 (2026-11-07 TruMenu 0.21.5 Fixes): the plugins of the switches file (never TruGuard); text keys are no switches
SW_PLUGINS = ('TruShadowPower', 'TruShadowCombat', 'TruShadowHud', 'TruRockVein', 'TruDoppelganger', 'TruDlc2Player',
              'TruMercLang', 'TruTrace', 'TruQoL')   # 2026-11-08 (17y): + the player plugin TruQoL 0.1.1
# 0.22.24 (Q36): plugins that may have rows without every INI key being one - TruMenu's own [Rescue] FallNet row (its
# other TruMenu.ini keys are the bar / menu items' business, not switches)
SW_ROW_ONLY = ('TruMenu',)
SW_TEXT_KEYS = {('TruMercLang', 'MercLang', 'PathFilter'), ('TruTrace', 'Trace', 'SpawnFilter'),
                ('TruTrace', 'Trace', 'ProgressFilter')}
# the run-time re-read of every live key: (plugin, section, key) -> function head in the plugin source whose body holds
# the section and key literals (read from the plugin sources 2026-11-07; everything else is read once in DllMain)
SW_LIVE = {
    ('TruRockVein', 'JumpTarget', 'Translate'): 'void JumpTargetReadSwitch(',      # 0.12 (Q61, 2026-11-11)
    ('TruShadowCombat', 'Damage', 'Translate'): 'void DamageReadSwitch(',
    ('TruShadowCombat', 'Chunk', 'Translate'): 'void ChunkReadSwitch(',
    ('TruShadowCombat', 'Splash', 'Translate'): 'void SplashReadSwitch(',
    ('TruShadowCombat', 'Death', 'TranslateNotify33'): 'void DeathReadSwitch(',
    # 0.6.5 (P1d): P1dReadSwitches loops over the key table kP1dKeys (once per second)
    ('TruShadowCombat', 'Companion', 'Translate'): ('void P1dReadSwitches(', 'kP1dKeys[] = {'),
    ('TruShadowCombat', 'Companion', 'Log'): ('void P1dReadSwitches(', 'kP1dKeys[] = {'),
    ('TruShadowCombat', 'Death', 'TranslateNotify34'): ('void P1dReadSwitches(', 'kP1dKeys[] = {'),
    ('TruShadowCombat', 'Death', 'TranslateNotify38'): ('void P1dReadSwitches(', 'kP1dKeys[] = {'),
    ('TruShadowCombat', 'Death', 'TranslateRegenList'): ('void P1dReadSwitches(', 'kP1dKeys[] = {'),
    ('TruShadowCombat', 'Death', 'TranslateLand'): ('void P1dReadSwitches(', 'kP1dKeys[] = {'),
    ('TruShadowCombat', 'Melee', 'TranslateInterrupt'): ('void P1dReadSwitches(', 'kP1dKeys[] = {'),
    ('TruShadowCombat', 'Death', 'TranslateT5'): ('void P1dReadSwitches(', 'kP1dKeys[] = {'),            # 0.6.6
    ('TruShadowCombat', 'Death', 'TranslateVaulted'): ('void P1dReadSwitches(', 'kP1dKeys[] = {'),
    ('TruShadowCombat', 'Death', 'TranslateVaultedClock'): ('void P1dReadSwitches(', 'kP1dKeys[] = {'),
    ('TruShadowCombat', 'Hit', 'Translate'): ('void P1dReadSwitches(', 'kP1dKeys[] = {'),               # 0.6.7
    ('TruShadowCombat', 'Hit', 'TranslateKnockback'): ('void P1dReadSwitches(', 'kP1dKeys[] = {'),
    ('TruShadowCombat', 'Hit', 'Log'): ('void P1dReadSwitches(', 'kP1dKeys[] = {'),
    ('TruShadowCombat', 'Hit', 'TranslateImpulseGate'): ('void P1dReadSwitches(', 'kP1dKeys[] = {'),    # 0.6.8
    ('TruShadowCombat', 'Death', 'Log'): ('void P1dReadSwitches(', 'kP1dKeys[] = {'),                   # 0.6.9
    ('TruShadowCombat', 'Hit', 'TranslateHitSpeed'): ('void P1dReadSwitches(', 'kP1dKeys[] = {'),       # 0.6.10
    ('TruShadowCombat', 'Strike', 'Translate'): 'void ReadSwitches(',
    ('TruShadowCombat', 'States', 'Translate1013'): 'void ReadSwitches(',
    ('TruShadowCombat', 'States', 'Translate1019'): 'void ReadSwitches(',
    ('TruShadowCombat', 'States', 'Translate1020'): 'void ReadSwitches(',
    ('TruShadowCombat', 'States', 'Translate1004'): 'void ReadSwitches(',
    ('TruShadowCombat', 'States', 'Translate1008'): 'void ReadSwitches(',            # 0.6.11
    ('TruShadowCombat', 'States', 'Translate1015Exit'): 'void ReadSwitches(',        # 0.6.12
    ('TruShadowCombat', 'Adrenaline', 'AssistPointer'): 'void Q108ReadSwitches(',   # 0.6.13 (group C, 2026-11-12)
    ('TruShadowCombat', 'Lock', 'MouseSwitch'): 'void Q108ReadSwitches(',
    ('TruShadowCombat', 'Lock', 'RightKey'): 'void Q108ReadSwitches(',
    ('TruShadowCombat', 'Lock', 'LeftKey'): 'void Q108ReadSwitches(',
    ('TruShadowCombat', 'Chunk', 'RemoveLastPiece'): 'void Q108ReadSwitches(',
    ('TruShadowCombat', 'Adrenaline', 'FillPercent'): 'void L14ReadSwitches(',   # 0.6.14 (group L, 2026-11-12)
    ('TruShadowCombat', 'Adrenaline', 'DrainPercent'): 'void L14ReadSwitches(',
    ('TruShadowCombat', 'Adrenaline', 'DrainModePercent'): 'void L14ReadSwitches(',
    ('TruShadowCombat', 'Adrenaline', 'StrikeWithoutFullMeter'): 'void L14ReadSwitches(',
    # 0.6.15 (2026-11-14; rows corrected to live with TruMenu 0.22.48): M15ReadSwitches from Q108ReadSwitches (once a second)
    ('TruShadowCombat', 'Adrenaline', 'ModeWithoutTarget'): 'void M15ReadSwitches(',
    ('TruShadowCombat', 'Adrenaline', 'StrikeWithoutButton'): 'void M15ReadSwitches(',
    ('TruShadowCombat', 'States', 'Translate231Slot0'): 'void ReadSwitches(',
    ('TruShadowCombat', 'States', 'Translate231Slot1'): 'void ReadSwitches(',
    ('TruShadowPower', 'Adrenaline', 'Translate'): 'void K11ReadSwitch(',
    ('TruShadowPower', 'TimeScale', 'TranslateSlot6'): 'void Slot6ReadSwitch(',     # 0.21 (X23, 2026-11-10)
    ('TruShadowPower', 'Reticle', 'TranslateRequest'): 'void ReticleReadSwitch(',   # 0.22 (K-5, 2026-11-10)
    ('TruShadowPower', 'Reticle', 'TranslateRefill'): 'void ReticleReadSwitch(',
    ('TruShadowPower', 'Meter', 'Infinite'): 'void InfiniteReadSwitch(',             # 0.23 (N2, 2026-11-10)
    ('TruShadowPower', 'Camera', 'Trace'): 'void CamTraceReadSwitch(',               # 0.25 (camera trace, 2026-11-11)
    ('TruShadowPower', 'Camera', 'TraceInterval'): 'void CamTraceReadSwitch(',
    ('TruRockVein', 'LedgeProbe', 'Translate'): 'void ProbeLiveRead(',             # 0.13 (Q62, 2026-11-11)
    ('TruRockVein', 'LedgeProbe', 'BestEdge'): 'void ProbeLiveRead(',
    ('TruMercLang', 'MercLang', 'Enabled'): 'void PollIni(',
    ('TruMercLang', 'MercLang', 'Language'): 'void PollIni(',
    # TruQoL 0.1.1 (17y): LiveTick (game thread, once a second after a change of the file time) -> LiveReadOptions
    ('TruQoL', 'TruQoL', 'LogLevel'): 'void LiveReadOptions(',
    ('TruQoL', 'FrameLimit', 'Enabled'): 'void LiveReadOptions(',
    ('TruQoL', 'FrameLimit', 'MaxFps'): 'void LiveReadOptions(',
    ('TruQoL', 'FrameLimit', 'AutoOff'): 'void LiveReadOptions(',
    ('TruQoL', 'FrameLimit', 'SpinUs'): 'void LiveReadOptions(',
    ('TruQoL', 'Camera', 'Fov'): 'void LiveReadOptions(',
    ('TruQoL', 'Camera', 'FovCutscenes'): 'void LiveReadOptions(',
    ('TruQoL', 'Camera', 'ShakeScale'): 'void LiveReadOptions(',
    ('TruQoL', 'Fixes', 'FrontEndPauseBit'): 'void LiveReadOptions(',   # TruQoL 0.1.4 (2026-11-11)
    ('TruMenu', 'Rescue', 'FallNet'): 'void FnReadSwitch(',             # TruMenu 0.22.24 (Q36, about once a second)
    ('TruMenu', 'Debug', 'LabelCollected'): 'void LgReadSwitch(',       # TruMenu 0.22.36 (labels, about once a second)
    ('TruMenu', 'Debug', 'LabelLaraGear'): 'void LgReadSwitch(',
    ('TruMenu', 'Log', 'Save'): 'void SvReadSwitch(',                   # TruMenu 0.22.27 (Q79, TruSaveProbe.h)
    # TruMenu 0.22.39 (Q126, about once a second); 0.22.40 (Q126b): AtReadSwitch -> AtStyleRead, AttractIconText gone
    ('TruMenu', 'Menu', 'AttractIcon'): 'LONG AtStyleRead(',
    # TruMenu 0.22.48 (Sonar komplett, about once a second from SoTick)
    ('TruMenu', 'Sonar', 'FullMap'): 'void SoReadSwitch(',
    ('TruMenu', 'Sonar', 'HidePlaceholder'): 'void SoReadSwitch(',
    ('TruMenu', 'Sonar', 'FloorMarkers'): 'void SoReadSwitch(',
    ('TruMenu', 'Sonar', 'AllFloors'): 'void SoReadSwitch(',             # TruMenu 0.22.49
    ('TruMenu', 'Sonar', 'TriangleCap'): 'void SoReadSwitch(',
    # TruMenu 0.22.50 (the sound log box filters, about once a second from W8Tick)
    ('TruMenu', 'Sound', 'LogLara'): 'void W8ReadSwitch(',
    ('TruMenu', 'Sound', 'LogEnemies'): 'void W8ReadSwitch(',
    ('TruMenu', 'Sound', 'LogWorld'): 'void W8ReadSwitch(',
    ('TruMenu', 'Sound', 'LogObjects'): 'void W8ReadSwitch(',
    ('TruMenu', 'Sound', 'LogUi'): 'void W8ReadSwitch(',
    ('TruMenu', 'Sound', 'LogSpeech'): 'void W8ReadSwitch(',
    ('TruMenu', 'Sound', 'LogMusic'): 'void W8ReadSwitch(',
    ('TruMenu', 'Sound', 'LogOnlyAudible'): 'void W8ReadSwitch(',
    ('TruMenu', 'Sound', 'LogCollapse'): 'void W8ReadSwitch(',
    ('TruMenu', 'Sound', 'LogMaxDist'): 'void W8ReadSwitch(',
    # TruMenu 0.22.51 (sonar fade / tint, base PDA; about once a second from S5Tick)
    ('TruMenu', 'Sonar', 'FadeFar'): 'void S5ReadSwitch(',
    ('TruMenu', 'Sonar', 'TintOthers'): 'void S5ReadSwitch(',
    ('TruMenu', 'PDA', 'ShadowPdaAsBasePda'): 'void S5ReadSwitch(',
    ('TruMenu', 'Sound', 'ReverbFollowsMute'): 'void W9ReadSwitch(',   # TruMenu 0.22.51 W9 (the game's reverb send)
    ('TruMenu', 'Sound', 'ReverbOff'): 'void W9ReadSwitch(',
    # TruMenu 0.22.53 W11 / S7 (W8ReadSwitch / S7ReadSwitch, about once a second)
    ('TruMenu', 'Sound', 'LogWeapons'): 'void W8ReadSwitch(',
    ('TruMenu', 'Sound', 'LogFollowMute'): 'void W8ReadSwitch(',
    ('TruMenu', 'Sonar', 'LoadNeighbourFloors'): 'void S7ReadSwitch(',
    ('TruMenu', 'Sonar', 'LoadAllConnected'): 'void S7ReadSwitch(',
    ('TruMenu', 'Sonar', 'LoadMaxUnits'): 'void S7ReadSwitch(',
}
# TruMenu 0.22.50: the bar's bool rows with a category argument (RadialOn -> W8RowOn) and the categories (kW8CatKey)
W8_CAT_ITEMS = ('snd.logcat', 'snd.catmute', 'snd.catsolo')
W8_CATS = ('lara', 'enemies', 'world', 'objects', 'ui', 'speech', 'music', 'weapons')   # 0.22.53: + weapons


def w11_subs(src):
    """0.22.53 W11: the sub-group keys of kW8Sub (first string of every row of the table)"""
    m = re.search(r'const W8Sub kW8Sub\[kW8Subs\] = \{(.*?)\n\};', src, re.S)
    return re.findall(r'\n    \{"([a-z0-9_]+)", ', m.group(1)) if m else []
# Q75 (2026-11-11): keys the plugin re-reads at run time only when they were 1 at the game start (the code is patched
# only then; a 1 after a start with 0 needs a restart). No "when" form of TruMenu says that: live-if:<Key> asks the key's
# value after the write (SwIsLive), so a row naming its own key would claim live for 0 -> 1 and restart for 1 -> 0 -
# both wrong. The row is "restart" (true for the first switch-on) and its hint names the live case in both languages.
SW_START_GATED = {
    ('TruShadowPower', 'Camera', 'ShakeTuTimeStep'): 'void TimeStepReadSwitch(',   # 0.27 (Q50, 2026-11-11)
    ('TruShadowPower', 'Player', 'TuTimeStep'): 'void TimeStepReadSwitch(',
}
SW_START_GATED_HINT = ('live nur wenn 1 beim Start', 'live if 1 at start')
SW_MAX, SW_GROUP_MAX = 512, 24              # 0.22.23: 512 rows (was 160 - the shipped file had 159)
QB_VIEW_MAX = 384                            # kQbViewMax: rows of one bar page (page Fixes: group rows + the open group);
                                             # 0.22.44 (W2): 256 (was 128) - page Tests 227 static rows; 0.22.48: 320 -
                                             # page Tests 259 static rows (Paket A copies, Paket G); 0.22.51: 384 - 306
RING_FROZEN = 172                            # 0.21.5: the ring is frozen - no new entries


def ring_entries(path):
    """0.21.5: [(line, path, label, id, arg)] of a radial-format file (comments / blank lines skipped)"""
    out = []
    for n, line in enumerate(open(path, encoding='ascii', errors='replace').read().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'): continue
        f = [x.strip() for x in line.split('|')]
        if len(f) != 3: continue
        word, _, arg = f[2].partition(' ')
        out.append((n, f[0], f[1], word, arg.strip()))
    return out


def choice_args(src, table):
    """0.21.5: the first fields of a QbChoice table (kQbWeapons / kQbMarks)"""
    m = re.search(r'const QbChoice %s\[\] = \{(.*?)\};' % table, src, re.S)
    return set(re.findall(r'\{"([^"]+)", "[^"]*", "[^"]*"\}', m.group(1))) if m else set()


def row_covers(row, word, arg, src):
    """0.21.5 ring parity rule: does a bar row (qb_rows tuple) run the ring entry (id, arg)? bool rows: the entry's
    0 / 1 / no argument; value rows: their steps; choice rows: one of their choices; others: the same argument"""
    table, de, rid, rarg, kind, layer = row[:6]
    if rid != word: return False
    if kind == 'kQbBool':
        base = (rarg + ' ') if rarg else ''
        return arg in (rarg, base + '0', base + '1') or (not rarg and arg in ('', '0', '1'))
    if kind == 'kQbValue': return True
    if kind == 'kQbChoice':
        tab = {'weapon.give': 'kQbWeapons', 'claude.mark': 'kQbMarks'}.get(word)
        return bool(tab) and arg in choice_args(src, tab)
    return rarg == arg


def ring_parity(src, radial_path):
    """0.21.5: ring entries no bar row runs ([(line, path, label, id, arg)])"""
    rows = qb_rows(src)
    return [e for e in ring_entries(radial_path) if not any(row_covers(r, e[3], e[4], src) for r in rows)]


def plugin_version(plugin):
    """'0.6.3' from the plugin sources ("<Plugin> 0.6.3" in a string literal), '' when missing"""
    best = ()
    folder = os.path.join(PLUGINS, plugin)
    for f in os.listdir(folder) if os.path.isdir(folder) else []:
        if not f.endswith(('.cpp', '.h')): continue
        for m in re.finditer(r'"%s (\d+(?:\.\d+)+)' % plugin, open(os.path.join(folder, f), encoding='utf-8',
                                                                     errors='replace').read()):
            best = max(best, tuple(int(x) for x in m.group(1).split('.')))
    return best


def plugin_source(plugin):
    """the plugin's .cpp files, Q79: and its .h files (TruMenu 0.22.27 keeps SvReadSwitch in TruSaveProbe.h)"""
    folder = os.path.join(PLUGINS, plugin)
    return '\n'.join(open(os.path.join(folder, f), encoding='utf-8', errors='replace').read()
                     for f in sorted(os.listdir(folder)) if f.endswith(('.cpp', '.h')))


def plugin_ini(plugin):
    """{(section, key): (line, value)} of the shipped plugin INI"""
    out, section = {}, None
    path = os.path.join(PLUGINS, plugin, plugin + '.ini')
    if not os.path.exists(path): return None
    for n, line in enumerate(open(path, encoding='utf-8', errors='replace').read().splitlines(), 1):
        line = line.strip()
        m = re.match(r'^\[(.+)\]$', line)
        if m:
            section = m.group(1)
            continue
        if not line or line.startswith(';') or '=' not in line: continue
        key, _, value = line.partition('=')
        out[(section, key.strip())] = (n, value.strip())
    return out


def sw_value_ok(typ, v):
    if typ == 'bool': return v in ('0', '1')
    m = re.fullmatch(r'int:(-?\d+)\.\.(-?\d+)(?::(\d+))?', typ)
    if m: return bool(re.fullmatch(r'-?\d{1,9}', v)) and int(m.group(1)) <= int(v) <= int(m.group(2))
    if typ.startswith('choice:'): return v.lower() in [c.lower() for c in typ[7:].split(',')]
    return False


Q217_HELP_MAX = 60                           # 0.21.7: a help line (bar footer / tooltip), characters per language
# 0.21.7: German words that must be written with their umlaut in the DE texts of the switches file (Lukas: "Umlaute
# spaeter nachziehen") - an ASCII transliteration of one of them is a problem
Q217_TRANSLIT = ('Doppelgaengerin', 'Kostuem', 'Soeldner', 'Zustaende', 'Aktivitaeten', 'fuer', 'ueber', 'ausserhalb',
                 'zurueck', 'Aenderung', 'anhaengen', 'Uebersetzung', 'Toedlich', 'loescht', 'Spruenge', 'Uebergaenge',
                 'Empfaenger', 'Geaendert', 'waehrend', 'Fuellt', 'behaelt', 'pruef', 'Pruef')


def sw_translit(where, text):
    """0.21.7: ASCII transliterations (ae / oe / ue / ss) of Q217_TRANSLIT words in a DE text"""
    low = text.lower()
    return ['%s: write "%s" with its umlaut (DE text "%s")' % (where, w, text) for w in Q217_TRANSLIT if w.lower() in low]


def check_switches(path):
    """0.21.5: the switches file - format, every key in its shipped plugin INI (rows of a newer plugin version than the
    sources may wait), default = the INI value, type fits, live = the plugin's re-read function (SW_LIVE), every INI key
    of the plugins covered (text keys excepted); returns problems, summary, rows"""
    problems, rows, groups, seen, gkeys = [], [], 0, set(), set()
    name = os.path.basename(path)
    if not os.path.exists(path): return ['%s missing' % name], '', []
    raw = open(path, 'rb').read()
    # 0.21.7 (TODO "Umlaute in TruMenu.switches.txt"): UTF-8 without BOM, umlauts in the texts (the bar's font, ImGui's
    # ProggyClean, has the Latin-1 glyphs - work/m0217_0711/font_glyphs.py); was: ASCII only
    if raw.startswith(b'\xef\xbb\xbf'): problems.append('%s: UTF-8 BOM (write the file without BOM)' % name)
    if any(b == 127 or (b < 32 and b not in (9, 10, 13)) for b in raw):
        problems.append('%s: control bytes' % name)
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as e:
        problems.append('%s: not UTF-8 (%s)' % (name, e))
        text = raw.decode('utf-8', 'replace')
    bad_chars = sorted({c for c in text if ord(c) > 0xff})
    if bad_chars: problems.append('%s: characters outside Latin-1 (no glyph in the bar font): %s' % (name, ''.join(bad_chars)))
    lines = text.lstrip('﻿').splitlines()
    if not lines or not lines[0].startswith('# TruMenu switches'):
        problems.append('%s: first line must start with "# TruMenu switches" (Set-TruMenu.ps1 / SwLoadLocked marker)' % name)
    inis, versions, sources = {}, {}, {}
    word = re.compile(r'[A-Za-z0-9_]+')
    for n, line in enumerate(lines, 1):
        s = line.strip()
        if not s or s.startswith('#'): continue
        where = '%s:%d' % (name, n)
        f = [x.strip() for x in s.split('|')]
        if f[0] == 'group':
            if len(f) not in (4, 5) or not word.fullmatch(f[1]) or len(f[1]) > 23 or not f[2] or not f[3] or \
                    (len(f) == 5 and f[4] != 'open'):
                problems.append('%s: group | <key> | <DE> | <EN> [| open]' % where)
            elif f[1] in gkeys: problems.append('%s: group key %s twice' % (where, f[1]))
            if len(f) >= 4 and (len(f[2].encode('utf-8')) > 63 or len(f[3].encode('utf-8')) > 63):
                problems.append('%s: group DE / EN longer than 63 bytes (SwGroup)' % where)
            if len(f) >= 3: problems += sw_translit(where, f[2])
            gkeys.add(f[1])
            groups += 1
            continue
        if not groups: problems.append('%s: switch line before the first group line' % where)
        if len(f) not in (9, 10):
            problems.append('%s: want 9 or 10 fields, got %d' % (where, len(f)))
            continue
        plugin, section, key, typ, de, en, when, default, hint = f[:9]
        since = f[9] if len(f) == 10 else ''
        if plugin not in SW_PLUGINS + SW_ROW_ONLY:
            problems.append('%s: plugin %s not in %s' % (where, plugin, SW_PLUGINS + SW_ROW_ONLY))
        if not (word.fullmatch(section) and len(section) < 32 and word.fullmatch(key) and len(key) < 40):
            problems.append('%s: section / key (letters, digits, _)' % where)
        # 17y: choice values may hold a dot (TruQoL Fov / ShakeScale floats as their exact INI text)
        if not re.fullmatch(r'bool|int:-?\d+\.\.-?\d+(:\d+)?|choice:[A-Za-z0-9_.]+(,[A-Za-z0-9_.]+)+', typ):
            problems.append('%s: type %s (bool | int:<lo>..<hi>[:<step>] | choice:<a>,<b>)' % (where, typ))
        m = re.fullmatch(r'int:(-?\d+)\.\.(-?\d+)(?::(\d+))?', typ)
        if m and (int(m.group(1)) >= int(m.group(2)) or (m.group(3) and not
                  1 <= int(m.group(3)) <= int(m.group(2)) - int(m.group(1)))):
            problems.append('%s: int range / step' % where)
        if typ.startswith('choice:') and len(typ) - 7 >= 64: problems.append('%s: choice list longer than 63' % where)
        if not de or not en or len(de.encode('utf-8')) > 63 or len(en.encode('utf-8')) > 63:
            problems.append('%s: DE / EN text empty or longer than 63 bytes' % where)
        if len(hint.encode('utf-8')) > 199: problems.append('%s: hint longer than 199 bytes' % where)
        # 0.21.7: the hint column = "<DE help> // <EN help>", each half the bar's help line (at most Q217_HELP_MAX)
        halves = hint.split(' // ')
        if len(halves) != 2 or not halves[0].strip() or not halves[1].strip():
            problems.append('%s: hint must be "<DE help> // <EN help>" (got %r)' % (where, hint[:50]))
        else:
            for lang, h in zip(('DE', 'EN'), halves):
                if len(h) > Q217_HELP_MAX: problems.append('%s: %s help %d characters > %d' % (where, lang, len(h), Q217_HELP_MAX))
        for label, v in (('plugin', plugin), ('section', section), ('key', key), ('type', typ), ('when', when),
                         ('default', default), ('since', since)):
            if any(ord(c) > 126 for c in v): problems.append('%s: %s must stay ASCII' % (where, label))
        problems += sw_translit(where, de) + sw_translit(where, halves[0])
        if when not in ('live', 'restart') and not re.fullmatch(r'live-if:[A-Za-z0-9_]+', when):
            problems.append('%s: when %s (live | restart | live-if:<Key>)' % (where, when))
        if not sw_value_ok(typ, default): problems.append('%s: default %s does not fit %s' % (where, default, typ))
        if (plugin, section, key) in seen: problems.append('%s: [%s] %s of %s twice' % (where, section, key, plugin))
        seen.add((plugin, section, key))
        rows.append((n, plugin, section, key, typ, when, default, since))
        if plugin not in SW_PLUGINS + SW_ROW_ONLY: continue
        if plugin not in inis:
            inis[plugin], versions[plugin], sources[plugin] = plugin_ini(plugin), plugin_version(plugin), \
                plugin_source(plugin)
        ini = inis[plugin] or {}
        pending = False
        if since:
            sm = re.fullmatch(r'(Tru[A-Za-z0-9]+) (\d+(?:\.\d+)+)', since)
            if not sm or sm.group(1) != plugin: problems.append('%s: since "%s" (<the row\'s plugin> <version>)' % (where, since))
            else: pending = tuple(int(x) for x in sm.group(2).split('.')) > versions[plugin]
        got = ini.get((section, key))
        if got is None:
            if not pending: problems.append('%s: [%s] %s is not in %s.ini' % (where, section, key, plugin))
        else:
            if not sw_value_ok(typ, got[1]):
                problems.append('%s: %s.ini:%d %s=%s does not fit %s' % (where, plugin, got[0], key, got[1], typ))
            if got[1] != default and not pending:
                problems.append('%s: default %s, %s.ini:%d has %s' % (where, default, plugin, got[0], got[1]))
        live = SW_LIVE.get((plugin, section, key))
        if when == 'restart' and live:
            fn_name = live[0] if isinstance(live, tuple) else live
            problems.append('%s: [%s] %s is re-read at run time (%s) - mark it live' % (where, section, key, fn_name.strip('(')))
        if when != 'restart':
            if not live: problems.append('%s: [%s] %s marked %s but %s reads it only at the start' % (where, section, key,
                                                                                                  when, plugin))
            elif isinstance(live, tuple):
                # 0.6.5 form: the re-read function loops over a key table - the function must use the table and the
                # table must hold {"section", "key", ...}
                fn, table = live
                body = fn_body(sources[plugin], fn)
                src = sources[plugin]
                at = src.find(table)
                tbl = src[at:src.find('\n};', at)] if at >= 0 else ''
                if not body or table.split('[')[0] not in body or '{"%s", "%s"' % (section, key) not in tbl:
                    problems.append('%s: %s / %s has no read of [%s] %s' % (where, fn.strip('('), table, section, key))
            else:
                body = fn_body(sources[plugin], live)
                if not body or '"%s"' % key not in body or '"%s"' % section not in body:
                    problems.append('%s: %s has no read of [%s] %s' % (where, live.strip('('), section, key))
            if when.startswith('live-if:') and (section, when[8:]) not in ini:
                problems.append('%s: %s - [%s] %s not in %s.ini' % (where, when, section, when[8:], plugin))
        gated = SW_START_GATED.get((plugin, section, key))
        if gated:                            # Q75: re-read only when 1 at the start - restart row, hint names live
            if live: problems.append('%s: [%s] %s in SW_LIVE and SW_START_GATED' % (where, section, key))
            if when != 'restart':
                problems.append('%s: [%s] %s is re-read only when 1 at the start - mark it restart (got %s)' % (
                    where, section, key, when))
            body = fn_body(sources[plugin], gated)
            if not body or '"%s"' % key not in body or '"%s"' % section not in body:
                problems.append('%s: %s has no read of [%s] %s' % (where, gated.strip('('), section, key))
            for h, need in zip(halves, SW_START_GATED_HINT):
                if need not in h: problems.append('%s: hint must name "%s"' % (where, need))
    if len(rows) > SW_MAX: problems.append('%s: %d switch lines, TruMenu keeps %d' % (name, len(rows), SW_MAX))
    if groups > SW_GROUP_MAX: problems.append('%s: %d groups, TruMenu keeps %d' % (name, groups, SW_GROUP_MAX))
    for plugin in SW_PLUGINS:                # every switch of the plugin INIs is a row
        for (section, key), (line, value) in sorted((plugin_ini(plugin) or {}).items()):
            if (plugin, section, key) not in seen and (plugin, section, key) not in SW_TEXT_KEYS:
                problems.append('%s: %s.ini:%d [%s] %s has no row' % (name, plugin, line, section, key))
    for (plugin, section, key) in SW_LIVE:
        if (plugin, section, key) not in seen: problems.append('%s: live key [%s] %s of %s has no row' % (name, section,
                                                                                                         key, plugin))
    for (plugin, section, key) in SW_START_GATED:
        if (plugin, section, key) not in seen:
            problems.append('%s: start-gated key [%s] %s of %s has no row' % (name, section, key, plugin))
    live_n = sum(1 for r in rows if r[5] != 'restart')
    return problems, '%d switches (%d live / live-if) in %d groups, %d plugins' % (len(rows), live_n, groups,
                                                                                len({r[1] for r in rows})), rows


def check_0215(radial_path, switches_path):
    """0.21.5 (2026-11-07 TruMenu 0.21.5 Fixes + frozen ring): see the module text"""
    problems, summary, rows = check_switches(switches_path)
    src = read_cpp()
    items = item_types(src)
    for item in ('sw.set', 'sw.list', 'sw.reload'):
        m = re.search(r'\{"%s", "action", (?:"[^"]*"\s*)+,\s*(true|false),' % re.escape(item), src)
        if not m: problems.append('TruMenu.cpp: item %s (action) missing in kItems' % item)
        elif m.group(1) != 'false': problems.append('TruMenu.cpp: %s must not be a game-thread item' % item)
    if not re.search(r'\{"Fixes", "Fixes", nullptr, 0, kQsSwitches\}', src):
        problems.append('TruMenu.cpp: kQbPages has no page Fixes (kQsSwitches)')
    sec = src[src.find('// ---- 0.21.5 Fixes'):src.find('// ---- end of 0.21.5 Fixes')]
    if not sec: problems.append('TruMenu.cpp: section "0.21.5 Fixes" missing')
    if sec.count('WritePrivateProfileStringA(') != 1:
        problems.append('TruMenu.cpp: section 0.21.5 Fixes must write the plugin INI in exactly one place (RunSwSet)')
    rs = fn_body(src, 'bool RunSwSet(')
    marks = [rs.find(t) for t in ('SwFindLocked(', 'SwValueOk(', 'GetFileAttributesA(', 'strcmp(old.text, v)',
                                  'WritePrivateProfileStringA(')]
    if not rs or -1 in marks or marks != sorted(marks):
        problems.append('TruMenu.cpp: RunSwSet must check in this order before the write: listed key, value fits, INI '
                        'exists, value changed (got %s)' % marks)
    if 'TestIniTarget(' not in rs: problems.append('TruMenu.cpp: RunSwSet must build the path with TestIniTarget')
    if 'kSwMarker' not in fn_body(src, 'void SwLoadLocked(') or '"# TruMenu switches"' not in src:
        problems.append('TruMenu.cpp: SwLoadLocked must refuse a file without the first-line marker')
    if not re.search(r'kSwMax = %d, kSwGroupMax = %d' % (SW_MAX, SW_GROUP_MAX), src):
        problems.append('TruMenu.cpp: kSwMax / kSwGroupMax differ from this tool (%d / %d)' % (SW_MAX, SW_GROUP_MAX))
    fav = fn_body(src, 'void QbFavPin(')
    if 'kQsSwitches' not in fav: problems.append('TruMenu.cpp: QbFavPin must refuse Y on page Fixes (no favourite)')
    tick = fn_body(src, 'void QuickTick(')
    if 'p.special == kQsSwitches ? kQbXDir : 1' not in tick and \
            'p.special == kQsSwitches || swRow ? kQbXDir : 1' not in tick:   # 0.21.8: + a pinned switch on page 0
        problems.append('TruMenu.cpp: QuickTick: X on page Fixes must pass kQbXDir')
    act = fn_body(src, 'void QbSwAct(')
    if 'QbRun("Fixes"' not in act or '"sw.set"' not in act:
        problems.append('TruMenu.cpp: QbSwAct must write through the item sw.set (QbRun)')
    if 'g_swGroup[g].open = false' not in act: problems.append('TruMenu.cpp: QbSwAct must keep one group open at a time')
    # 0.21.8: the widget is SwMenuWidget (also on the favourites page), the write SwMenuAfter -> RunSwSet
    if 'RunSwSet(pending' not in fn_body(src, 'void PageSwitches(') and not (
            'SwMenuAfter(pending' in fn_body(src, 'void PageSwitches(') and
            'RunSwSet(pending' in fn_body(src, 'void SwMenuAfter(')):
        problems.append('TruMenu.cpp: the menu section Fixes must write through RunSwSet')
    if 'PageSwitches();' not in src or 'PageQbAll();' not in src or 'kQbPages[p]' not in fn_body(src, 'void PageQbAll('):
        problems.append('TruMenu.cpp: the long menu needs the sections Fixes (PageSwitches) and Quick bar pages (PageQbAll '
                        'over kQbPages)')
    build = open(os.path.join(ROOT, 'scripts', 'windows', 'Build-TruAsi.ps1'), encoding='utf-8-sig').read()
    if "'switches.txt'" not in build: problems.append('Build-TruAsi.ps1 does not copy TruMenu.switches.txt')
    st = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if 'TruMenu.switches.txt' not in st: problems.append('Set-TruMenu.ps1 does not install TruMenu.switches.txt')
    # the frozen ring: its header says so, no new entries, every entry is a bar row (and so a row of the menu section)
    rtext = open(radial_path, encoding='ascii', errors='replace').read()
    if 'aktuell nicht weiter gemacht' not in rtext or 'frozen' not in rtext:
        problems.append('%s: the header must say the ring is frozen ("aktuell nicht weiter gemacht")' %
                        os.path.basename(radial_path))
    entries = ring_entries(radial_path)
    if len(entries) > RING_FROZEN:
        problems.append('%s: %d entries - the ring is frozen at %d (no new entries)' % (os.path.basename(radial_path),
                                                                                       len(entries), RING_FROZEN))
    for e in ring_parity(src, radial_path):
        problems.append('%s:%d: ring entry %s | %s | %s %s is no bar row (ring frozen: every entry belongs in the bar)' %
                        ((os.path.basename(radial_path),) + e))
    return problems, '%s; items sw.*, page Fixes, RunSwSet order, Y refused, menu sections; ring %d entries all bar ' \
                     'rows' % (summary, len(entries))


def check_0216(ini_path):
    """0.21.6 (2026-11-07 TruMenu 0.21.6): bar page Kostueme (own page after Lara, page limit 16 / row limit 64; rows from
    the cycle list and the player records, the current costume marked, refused without a level; the choice row switches
    only after kCosSettleMs without a new step, wraps, X = now; Y refused; the only items costume.set / .next /
    .choosereload), the flight key line ([Cheat] FlightHint 0 / 1 default 1, drawn only while flight is on + menu closed +
    the INI switch on, above the bottom-right sound list / flow line, the same text as footer / tooltip) and the quick
    command line (L3 alone, not as part of L3 + R3; one command path = CmdRunLine only; keys held from the game)"""
    problems = []
    name = os.path.basename(ini_path)
    src = read_cpp()
    if not src.startswith('//') or '0.21.6 (bar page Kostueme' not in src[:src.find('\n', src.find('kVersion = '))]:
        problems.append('TruMenu.cpp: kVersion must keep the 0.21.6 text (0.21.7: the version check moved to check_0217)')
    # [Cheat] FlightHint
    opts = {(s, k): d for s, k, d, c in table(src)[1]}
    if opts.get(('Cheat', 'FlightHint')) != '1':
        problems.append('TruMenu.cpp: kOpts [Cheat] FlightHint missing or default not 1')
    found = [(n, v) for n, k, v in ini_section(ini_path, 'Cheat') if k == 'FlightHint']
    if len(found) != 1: problems.append('%s: [Cheat] FlightHint missing' % name)
    elif found[0][1] not in ('0', '1'): problems.append('%s:%d: [Cheat] FlightHint=%s (0 / 1)' % ((name,) + found[0]))
    if 'g_flightHint = OptInt(ini, "Cheat", "FlightHint")' not in src:
        problems.append('TruMenu.cpp: [Cheat] FlightHint is never read (g_flightHint = OptInt(...))')
    # pages / rows
    block = src[src.index('const QbPage kQbPages[] = {'):]
    block = block[:block.index('\n};')]
    order = re.findall(r'(?:QB_PAGE\("([^"]*)", "[^"]*", (kQb[A-Za-z]+), (kQs[A-Za-z]+)\)|\{"([^"]*)", "[^"]*", nullptr, 0, '
                       r'(kQs[A-Za-z]+)\})', block)
    pages = [(a or d, b or None, c or e) for a, b, c, d, e in order]
    if len(pages) > QB_PAGES_MAX:             # 0.21.11: 17 (page Rettung; g_qbRow[17])
        problems.append('TruMenu.cpp: kQbPages has %d pages - g_qbRow holds %d' % (len(pages), QB_PAGES_MAX))
    specials = [p[2] for p in pages]
    if specials.count('kQsCostume') != 1:
        problems.append('TruMenu.cpp: kQbPages needs exactly one page Kostueme (kQsCostume), found %d'
                        % specials.count('kQsCostume'))
    elif pages[specials.index('kQsCostume') - 1][1] != 'kQbLara':
        problems.append('TruMenu.cpp: page Kostueme must follow page Lara')
    if 'static_assert(kQbPageN <= %d' % QB_PAGES_MAX not in src or 'g_qbRow[%d]' % QB_PAGES_MAX not in src or \
            'const int kQbViewMax = %d;' % QB_VIEW_MAX not in src:   # 0.22.16: 112; 0.22.18: 128; 0.22.44: 256
        problems.append('TruMenu.cpp: the page / row limits (static_assert kQbPageN <= %d, g_qbRow[%d], kQbViewMax %d) '
                        'changed' % (QB_PAGES_MAX, QB_PAGES_MAX, QB_VIEW_MAX))
    sec = src[src.find('// ---- 0.21.6 costumes'):src.find('// ---- end of 0.21.6 costumes')]
    if len(sec) < 100: problems.append('TruMenu.cpp: section "0.21.6 costumes" missing')
    m = re.search(r'const DWORD kCosSettleMs = (\d+);', sec)
    if not m or not Q216_SETTLE[0] <= int(m.group(1)) <= Q216_SETTLE[1]:
        problems.append('TruMenu.cpp: kCosSettleMs must be %d .. %d ms (the choice row waits about 0.5 s)' % Q216_SETTLE)
    mn = re.search(r'kCosSlotNames\[16\] = \{(.*?)\};', sec, re.S)
    names = tuple(x.replace('\\"', '"') for x in re.findall(r'"((?:[^"\\]|\\.)*)"', mn.group(1))) if mn else ()
    if names != Q216_COS_NAMES:
        problems.append('TruMenu.cpp: kCosSlotNames differ from the game texts (PC locals 83 + slot, '
                        'work/rebuild/costumes_0311/logs/check_names.txt)')
    names_log = os.path.join(ROOT, 'work', 'rebuild', 'costumes_0311', 'logs', 'check_names.txt')
    if os.path.isfile(names_log):              # the measured texts (the log is local work data, not in the repository)
        log = dict(re.findall(r"^slot ([a-p]) xbox \d+ -> pc \d+ b['\"](.*?)['\"]\s", open(names_log, encoding='utf-8',
                                                                                          errors='replace').read(), re.M))
        for i, want in enumerate(Q216_COS_NAMES):
            got = log.get(chr(97 + i))
            if got is not None and got != want:
                problems.append('Q216_COS_NAMES slot %s "%s" != check_names.txt "%s"' % (chr(97 + i), want, got))
    refresh = fn_body(src, 'void CosRefresh(')
    for need in ('GlobalCostumes(g_cos.ids, 128)', 'TypeRecord(', 'ObjectId(', 'ReadDword(kCostumeNow'):
        if need not in refresh: problems.append('TruMenu.cpp: CosRefresh must read %s (the long menu\'s data)' % need)
    rows = fn_body(src, 'int QbCosRows(')
    for need in ('CosRefresh();', 'add(kQdCosPick', 'add(kQdCosNext', 'add(kQdCosRec', 'add(kQdCosGroup', 'add(kQdCos, g_cos.ids[i])',
                 'static_cast<DWORD>(g_cos.ids[i]) == g_cos.now', 'g_cos.listOpen && i < listN && n < max'):
        if need not in rows: problems.append('TruMenu.cpp: QbCosRows lacks %s (rows from the list, current marked, '
                                             'limit)' % need)
    why = fn_body(src, 'const char *CosWhy(')
    if '!InLevel()' not in why or '!g_experimental' not in why:
        problems.append('TruMenu.cpp: CosWhy must refuse without a level / with Experimental=0 (the long menu\'s rule)')
    act = fn_body(src, 'void QbCosAct(')
    cases = dict(re.findall(r'case (kQdCos[A-Za-z]*): \{?(.*?)(?=\n    case |\n    default:)', act, re.S))
    pick = cases.get('kQdCosPick', '')
    i_why, i_x, i_step = pick.find('CosWhy(true'), pick.find('if (x)'), pick.find('CosStep(')
    if not (0 <= i_why < i_x < i_step):
        problems.append('TruMenu.cpp: QbCosAct kQdCosPick: CosWhy first, then X (= now), then the step')
    else:
        step = pick[i_step:]
        if 'g_cos.pending = true' not in step or 'CosApply(' in step or 'QbRun(' in step:
            problems.append('TruMenu.cpp: QbCosAct: a left / right step must only pick (pending) - the switch belongs to '
                            'QbCosTick after kCosSettleMs (no switch on every step)')
        if 'CosApply(shown)' not in pick[i_x:i_step]: problems.append('TruMenu.cpp: QbCosAct: X must apply the shown entry')
    for case, rule in (('kQdCos', 'CosWhy(true'), ('kQdCosRec', 'CosWhy(false')):
        body = cases.get(case, '')
        run = max(body.find('CosApply('), body.find('QbRun('))
        if not (0 <= body.find(rule) < body.find('if (why[0]) {') < run):
            problems.append('TruMenu.cpp: QbCosAct %s must check %s and refuse before it runs' % (case, rule))
    if 'QbConfirm(' not in cases.get('kQdCosRec', ''):
        problems.append('TruMenu.cpp: QbCosAct kQdCosRec (reloads the unit) must confirm (QbConfirm)')
    tick = fn_body(src, 'void QbCosTick(')
    marks = [tick.find(t) for t in ('kCosSettleMs', 'g_cos.pending = false', 'CosWhy(true', 'CosApply(g_cos.pickId)')]
    if not tick or -1 in marks or marks != sorted(marks):
        problems.append('TruMenu.cpp: QbCosTick must wait kCosSettleMs, clear the pick, check CosWhy, then CosApply')
    step = fn_body(src, 'int CosStep(')
    if '% n' not in step or 'n - 1' not in step:
        problems.append('TruMenu.cpp: CosStep must wrap at both ends (% n, n - 1)')
    runs = re.findall(r'QbRun\("Kostueme", [^;]*?"(costume\.[a-z]+)"', sec)
    if sorted(runs) != ['costume.choosereload', 'costume.set'] or 'kQbCosNext = {"Naechstes Kostuem", "Next costume", ' \
                                                                  '"costume.next", ""' not in src:
        problems.append('TruMenu.cpp: page Kostueme must run costume.set (CosApply, once), costume.choosereload and the '
                        'row kQbCosNext = costume.next - nothing else (got %s)' % runs)
    items = item_types(src)
    for item in Q216_COS_ITEMS:
        if items.get(item) != 'action': problems.append('TruMenu.cpp: item %s missing in kItems' % item)
    if 'QbCosTick();' not in fn_body(src, 'void Render('):
        problems.append('TruMenu.cpp: Render must call QbCosTick every frame (the waiting switch also with the bar closed)')
    if 'kQsCostume' not in fn_body(src, 'void QbFavPin('):
        problems.append('TruMenu.cpp: QbFavPin must refuse Y on the costume rows (no favourite with an argument)')
    if 'p.special == kQsCostume) QbSpecialAct(p.special, row - g_qbStaticN, kQbXDir)' not in fn_body(src, 'void QuickTick('):
        problems.append('TruMenu.cpp: QuickTick: X on page Kostueme must pass kQbXDir')
    if 'kQsCostume) n = QbCosRows(' not in fn_body(src, 'int QbSpecialBuild('):
        problems.append('TruMenu.cpp: QbSpecialBuild does not build page Kostueme')
    # flight key line
    mw = re.search(r'bool FlightHintWanted\(\) \{ return ([^;]*); \}', src)
    want = mw.group(1).replace(' ', '') if mw else ''
    for need in ('g_flightHint', 'g_flight', '!g_menuOpen', 'InLevel()'):
        if need not in want.split('&&'):
            problems.append('TruMenu.cpp: FlightHintWanted must be g_flightHint && g_flight && !g_menuOpen && InLevel() '
                            '(missing %s)' % need)
    render = fn_body(src, 'void Render(')
    # 0.22.1: the early-return condition goes on with "&& !cnBadge)" (the cutscene pause badge)
    if 'const bool flightHint = FlightHintWanted();' not in render or \
            not re.search(r'!flightHint( && ![A-Za-z]+)*\)', render) or \
            'if (flightHint) DrawFlightHint();' not in render:
        problems.append('TruMenu.cpp: Render must draw the flight line only when FlightHintWanted()')
    elif render.find('if (flowDraw) DrawFlowOverlay();') > render.find('if (flightHint) DrawFlightHint();') or \
            render.find('if (g_snOn) DrawSoundList();') > render.find('if (flightHint) DrawFlightHint();'):
        problems.append('TruMenu.cpp: the flight line must be drawn after the sound list and the flow line (keeps above)')
    dh = fn_body(src, 'void DrawFlightHint(')
    for need in ('"##TruSoundList"', '"##TruMenuFlow"', 'w->Pos.y - 6.0f', 'FlightHintText(g_qbLang == 0'):
        if need not in dh: problems.append('TruMenu.cpp: DrawFlightHint lacks %s (above the bottom-right windows, the '
                                           'bar\'s language)' % need)
    ft = fn_body(src, 'void FlightHintText(')
    for need in ('RT hoch', 'LT runter', 'Stick bewegt', 'Tempo', 'RT up', 'LT down', 'g_flightSpeed'):
        if need not in ft: problems.append('TruMenu.cpp: FlightHintText lacks "%s"' % need)
    if 'FlightHintText(' not in fn_body(src, 'void PageCheat(') or 'cheat.flight' not in fn_body(src, 'bool QbRowHint('):
        problems.append('TruMenu.cpp: the keys must be the menu flight button\'s tooltip and the bar row\'s hint')
    # quick command line
    qc = src[src.find('// ---- 0.21.6 quick command line'):src.find('// ---- end of 0.21.6 quick command line')]
    if len(qc) < 100: problems.append('TruMenu.cpp: section "0.21.6 quick command line" missing')
    if qc.count('CmdRunLine(') != 1:
        problems.append('TruMenu.cpp: the quick command line must run every line through exactly one CmdRunLine call '
                        '(found %d)' % qc.count('CmdRunLine('))
    for t in Q216_EXEC:
        if t in qc: problems.append('TruMenu.cpp: second exec path: the quick command line calls %s (one command path: '
                                    'CmdRunLine only)' % t)
    pt = fn_body(src, 'bool QcPadTick(')
    for need in ('(g_toggleButtons | g_radHold) & ~fb', 'if (down && (buttons & others)) armed = false;',
                 'QcOpen(false, !g_qbOpen'):
        if need not in pt: problems.append('TruMenu.cpp: QcPadTick lacks %s (L3 alone only, closes with the bar / menu / '
                                           'ring)' % need)
    qt = fn_body(src, 'void QuickTick(')
    i_qc, i_ret = qt.find('QcPadTick('), qt.find('InterlockedExchange(&g_qbJust, 0)')
    if not (0 <= i_qc < i_ret) or 'if (qcHasPad) {' not in qt:
        problems.append('TruMenu.cpp: QuickTick must call QcPadTick before its early return and let the rows wait')
    if 'g_imguiReady && g_qcOpen && IsKeyMessage(msg)' not in fn_body(src, 'LRESULT CALLBACK WndProcHook(') or \
            'RadMenuOpen() || g_qcOpen' not in fn_body(src, 'int __fastcall KbdReadHook('):
        problems.append('TruMenu.cpp: the command line must hold the keys from the game (WndProcHook + KbdReadHook)')
    if not re.search(r'const WORD kQcOwn = 0x3000;', src) or 'g_cmdFocusButton | (g_qcOpen ? kQcOwn : 0)' not in \
            fn_body(src, 'WORD QbPad('):
        problems.append('TruMenu.cpp: QbPad must keep FocusButton (bar open) and A / B (line open) from the game')
    if 'if (quickDraw && g_qcOpen && !g_menuOpen) DrawQuickCmd();' not in render:
        problems.append('TruMenu.cpp: Render must draw the command line only with the bar open and the menu closed')
    # toggle rows (owner live test 20:52): an item that flips a flag per argument has a state function in RadialOn - its
    # bar rows must be bool rows (an / aus, right on, left off, X toggle), never action rows ("rechts", a blind flip)
    ron = fn_body(src, 'bool RadialOn(')
    toggles = 0
    for tab, de, item, arg, kind, _ in qb_rows(src):
        if item not in Q216_TOGGLE_ITEMS or not arg or ' ' in arg: continue
        toggles += 1
        if kind != 'kQbBool':
            problems.append('TruMenu.cpp: %s row "%s" (%s %s) flips a flag - toggle rows must be bool rows with a value '
                            'function (RadialOn), not %s' % (tab, de, item, arg, kind))
    for item in Q216_TOGGLE_ITEMS:
        if '!_stricmp(e.id, "%s")' % item not in ron:
            problems.append('TruMenu.cpp: RadialOn has no state (value function) for the toggle item %s' % item)
    nn = fn_body(src, 'const char *NavRowNote(')
    if not nn or 'NavRowNote(r.arg, de)' not in fn_body(src, 'void QbViewOf(') or \
            any(t in nn for t in ('PutByte(', 'WriteDword(', 'WriteByte(', 'NavSet(')):
        problems.append('TruMenu.cpp: a nav.draw row that is on but cannot draw needs NavRowNote (read only) in QbViewOf')
    return problems, 'FlightHint key, page Kostueme after Lara (%d pages), settle %s ms, %d slot names, flight line rule, ' \
                     'one command path, %d toggle rows all bool' % (len(pages), m.group(1) if m else '?', len(names), toggles)


Q217_ITEMS = {'dbg.uber': 'bool', 'uber.dump': 'action', 'shader.labels': 'bool', 'shader.reload': 'action',
              'shader.dump': 'action', 'nav.labels': 'bool',                   # 0.21.7: all render-thread, read only
              'sap.status': 'info', 'sap.reset': 'action'}
Q217_KEYS = {('Debug', 'UberLabels'): '0', ('Debug', 'UberRadius'): '8000', ('Debug', 'UberMax'): '12',
             ('Debug', 'UberMatch'): 'switch,lever', ('Debug', 'NavLabels'): '0', ('Debug', 'NavLabelRadius'): '3000',
             ('Debug', 'NavLabelMax'): '40', ('Shader', 'Labels'): '0', ('Shader', 'File'): 'TruMenu.shaderlabel.txt',
             ('Shader', 'LabelRadius'): '15000', ('Shader', 'LabelMax'): '40', ('Shader', 'ShowOrig'): '0',
             ('Debug', 'SapWatch'): '1'}
Q217_GATES = (3165, 3357)                    # live 2026-11-07: the dlc_caverns_hall gates' distances (not labelled)
Q217_WRITES = ('WriteDword(', 'PutByte(', 'WriteByte(', 'NavPutDword(', 'VirtualProtect(', 'WritePrivateProfileString',
               'QueueItem(', 'InvokeCore(', 'Fn>(')          # nothing of these in the three read-only label sections
Q217_SECTIONS = ('uber labels', 'shader labels', 'navmesh labels', 'SweepAndPrune read-out')
Q217_UMLAUT_WORDS = ('Doppelgängerin', 'Kostüm', 'Söldner', 'Zustände')   # the owner's examples, now with umlauts


def check_0217(ini_path, switches_path):
    """0.21.7 (2026-11-07/08 TruMenu 0.21.7, night build): footer "Y: -" where QbFavPin refuses (QbFavOk), "L3:
    Befehlszeile", the help line (kQbHelp "DE|EN" <= 60 characters per half, keys = bar rows, the Fixes hint column, the
    costume / chapter rows), the switches file with umlauts (UTF-8, the parser cuts at a character boundary), costume
    rows the game refuses (0x5c54e0 on the game thread, grey, skipped, refused), page Kapitel units per chapter (the
    level list's groups, level.load through QbActRow with confirm + backup, the DLC 2 note), the pad diagnosis (log /
    footer only), and the three read-only label layers (uber / shader / navmesh: byte-check tables, no writes, INI keys,
    items, bar rows, Render)"""
    problems = []
    name = os.path.basename(ini_path)
    src = read_cpp()
    # 0.21.8: the version line keeps the 0.21.7 part (as check_0216 reads its own part)
    if not src.startswith('//') or '0.21.7 (bar footer' not in src[:src.find('\n', src.find('kVersion = '))]:
        problems.append('TruMenu.cpp: kVersion must hold the 0.21.7 part "0.21.7 (bar footer"')
    # 1a footer Y
    fav = fn_body(src, 'bool QbFavOk(')
    for need in ('kQbLabel', 'kQbGroup', 'kQbPlanned', 'strcmp(r->id, "-")'):
        if need not in fav: problems.append('TruMenu.cpp: QbFavOk lacks %s (the rule of QbFavPin)' % need)
    if '!r->arg[0]' not in fav and 'FavArgOk(r->arg)' not in fav:   # 0.21.8: an argument that fits the list
        problems.append('TruMenu.cpp: QbFavOk lacks the argument rule (!r->arg[0] / 0.21.8 FavArgOk(r->arg))')
    dq = fn_body(src, 'void DrawQuick(')
    if 'QbFavOk(QbSelRow(g_qbPage, sel))' not in dq or '"X: ausfuehren  Y: -"' not in dq or '"X: run  Y: -"' not in dq:
        problems.append('TruMenu.cpp: DrawQuick must show "Y: -" where QbFavOk(QbSelRow(...)) refuses Y')
    pin = fn_body(src, 'void QbFavPin(')
    if 'kQsChapters' not in pin: problems.append('TruMenu.cpp: QbFavPin must refuse Y on the chapter unit rows')
    # 1b L3 hint
    if 'QbComboText(g_cmdFocusButton' not in dq or '"Befehlszeile"' not in dq or 'g_cmdEnabled && g_cmdFocusButton' not in dq:
        problems.append('TruMenu.cpp: DrawQuick lacks the footer hint "<FocusButton>: Befehlszeile" (only with [Cmd] Enabled)')
    # 1c umlauts
    pr = fn_body(src, 'bool SwParseRow(')
    if 'SwCopyText(r.de' not in pr or 'SwCopyText(r.en' not in pr or '" // "' not in pr or 'r.hintEn' not in pr:
        problems.append('TruMenu.cpp: SwParseRow must copy the texts with SwCopyText and split the hint at " // "')
    if 'Utf8TrimTail(o)' not in fn_body(src, 'void SwCopyText(') or '"\\xef\\xbb\\xbf"' not in fn_body(src, 'void SwLoadLocked('):
        problems.append('TruMenu.cpp: SwCopyText must cut at a UTF-8 character boundary, SwLoadLocked skip a BOM')
    stext = open(switches_path, encoding='utf-8', errors='replace').read()
    for w in Q217_UMLAUT_WORDS:
        if w not in stext: problems.append('%s: "%s" missing (German texts with umlauts)' % (os.path.basename(switches_path), w))
    # 1d help
    m = re.search(r'const QbHelp kQbHelp\[\] = \{(.*?)\n\};', src, re.S)
    helps = [(a, b, unescape(''.join(LIT.findall(t)))) for a, b, t in
             re.findall(r'\{"([a-z][a-z0-9_.]*)", "([^"]*)", ((?:"(?:[^"\\]|\\.)*"\s*)+)\}', m.group(1))] if m else []
    if not helps: problems.append('TruMenu.cpp: kQbHelp missing')
    if 'const int kQbHelpMax = %d;' % Q217_HELP_MAX not in src:
        problems.append('TruMenu.cpp: kQbHelpMax must be %d (the owner: "nicht zu lange")' % Q217_HELP_MAX)
    rows = qb_rows(src) + [('kQbCosNext', 'Naechstes Kostuem', 'costume.next', '', 'kQbAction', '-1')]
    keys = set()
    for hid, harg, text in helps:
        halves = text.split('|')
        if len(halves) != 2 or not halves[0] or not halves[1]:
            problems.append('TruMenu.cpp: kQbHelp %s %s: "DE|EN" (got %r)' % (hid, harg, text[:40]))
        for lang, h in zip(('DE', 'EN'), halves):
            if len(h) > Q217_HELP_MAX:
                problems.append('TruMenu.cpp: kQbHelp %s %s: %s %d characters > %d' % (hid, harg, lang, len(h), Q217_HELP_MAX))
        if (hid, harg) in keys: problems.append('TruMenu.cpp: kQbHelp %s %s twice' % (hid, harg))
        keys.add((hid, harg))
        if not any(r[2] == hid and (harg == '*' or r[3] == harg) for r in rows):
            problems.append('TruMenu.cpp: kQbHelp %s %s is no bar row (help without a row)' % (hid, harg))
    for need in (('nav.draw', 'planner_areas'), ('nav.mask', ''), ('cheat.flight', ''), ('dbg.uber', ''),
                 ('shader.labels', ''), ('nav.labels', '')):
        if need not in keys: problems.append('TruMenu.cpp: kQbHelp lacks %s %s' % need)
    if not any(h[0] == 'nav.draw' and h[1] == 'planner_areas' and 'Alle Ebenen' in h[2] for h in helps):
        problems.append('TruMenu.cpp: the help of "Navmesh Flaechen" must name "Alle Ebenen" (live 2026-11-07 21:57)')
    hl = fn_body(src, 'bool QbHelpLine(')
    for need in ('QbHelpText(r->id, r->arg)', 'g_sw[i].hint', 'g_sw[i].hintEn', 'kQdCosPick', 'kQdCosRec', 'kQdCos:',
                 'ChapHelp('):
        if need not in hl: problems.append('TruMenu.cpp: QbHelpLine lacks %s' % need)
    for body in (hl, fn_body(src, 'bool ChapHelp(')):
        for t in LIT.findall(body):
            if len(unescape(t)) > Q217_HELP_MAX + 2 and ' ' in t:
                problems.append('TruMenu.cpp: help text longer than %d: "%s"' % (Q217_HELP_MAX, unescape(t)[:50]))
    if 'QbHelpLine(g_qbPage, sel, de, help, sizeof(help))' not in dq or 'QbHelpText(r.id, r.arg)' not in \
            fn_body(src, 'void PageQbRow('):
        problems.append('TruMenu.cpp: the help must be the bar footer line (DrawQuick) and the menu tooltip (PageQbRow)')
    if 'r.hintEn' not in fn_body(src, 'void PageSwitches(') and not (   # 0.21.8: the widget is SwMenuWidget
            'SwMenuWidget(' in fn_body(src, 'void PageSwitches(') and 'r.hintEn' in fn_body(src, 'void SwMenuWidget(')):
        problems.append('TruMenu.cpp: PageSwitches tooltip must show both halves of the hint')
    # 1e costumes the game refuses
    pad = fn_body(src, 'DWORD WINAPI PadHook(')
    clk = pad[pad.find('if (clock != g_lastClock)'):]
    if 'CosValidTick();' not in clk or 'CosValidTick();' in fn_body(src, 'void Render('):
        problems.append('TruMenu.cpp: CosValidTick must run in the pad hook\'s once-per-game-frame block (game thread), '
                        'not in Render')
    cvt = fn_body(src, 'void CosValidTick(')
    if 'CosValidCall(' not in cvt or 'g_cosValidWant' not in cvt or '!same' not in cvt.replace('if (same) return;', '!same'):
        problems.append('TruMenu.cpp: CosValidTick must call the check only while the page is shown and the list changed')
    if 'kCostumeValid' not in fn_body(src, 'bool CosValidCall(') or any(t in cvt for t in Q217_WRITES[:5]):
        problems.append('TruMenu.cpp: CosValidCall = the game\'s check 0x5c54e0 only, CosValidTick writes nothing')
    cr = fn_body(src, 'int QbCosRows(')
    if 'CosOffered(g_cos.ids[i]) == 0' not in cr or 'g_cosValidWant' not in cr:
        problems.append('TruMenu.cpp: QbCosRows must mark the refused entries and ask CosValidTick for the check')
    act = fn_body(src, 'void QbCosAct(')
    cases = dict(re.findall(r'case (kQdCos[A-Za-z]*): \{?(.*?)(?=\n    case |\n    default:)', act, re.S))
    pick, one = cases.get('kQdCosPick', ''), cases.get('kQdCos', '')
    i_off, i_pend = pick.find('CosOffered(g_cos.ids[next]) != 0'), pick.find('g_cos.pending = true')
    if not (0 <= i_off < i_pend): problems.append('TruMenu.cpp: QbCosAct kQdCosPick must skip refused entries before it picks')
    i_ref, i_apply = one.find('CosOffered(static_cast<WORD>(q.intro)) == 0'), one.find('CosApply(')
    if not (0 <= i_ref < i_apply): problems.append('TruMenu.cpp: QbCosAct kQdCos must refuse a refused entry before CosApply')
    # 1f / 3 uber labels; 4 navmesh; 5 shader: read only, tables, INI keys
    for sec in Q217_SECTIONS:
        body = src[src.find('// ---- 0.21.7 %s' % sec):src.find('// ---- end of 0.21.7 %s' % sec)]
        if len(body) < 500: problems.append('TruMenu.cpp: section "0.21.7 %s" missing' % sec); continue
        for t in Q217_WRITES:
            if t in body: problems.append('TruMenu.cpp: section 0.21.7 %s calls %s (read only)' % (sec, t))
        if 'HexBytesAt(c.at, c.hex)' not in body: problems.append('TruMenu.cpp: section 0.21.7 %s has no byte-check loop' % sec)
    us = fn_body(src, 'DWORD UberStateOf(')
    for need in ('inst + 0x2d0', 'a + 0x2ec', 'u - 0x10', 'b + 0x70', 'kUbMagic'):
        if need not in us: problems.append('TruMenu.cpp: UberStateOf lacks %s (the engine path 0x4d5d59)' % need)
    if 'const DWORD kUbMagic = 0xf0012345;' not in src: problems.append('TruMenu.cpp: kUbMagic must be 0xf0012345')
    ut = fn_body(src, 'void UberText(')
    for need in ('cond != 1', 'tr + 0x1c', 'b + 0x88', 'b + 0x80', 'b + 0x8c', 'faehrt hoch', 'faehrt runter', 'noch %s'):
        if need not in ut: problems.append('TruMenu.cpp: UberText lacks %s' % need)
    opts = {(s, k): d for s, k, d, c in table(src)[1]}
    for key, want in Q217_KEYS.items():
        if opts.get(key) != want: problems.append('TruMenu.cpp: kOpts [%s] %s default must be %s (got %s)' % (key + (want,
                                                                                                    opts.get(key))))
        sec_rows = [(n, v) for n, k, v in ini_section(ini_path, key[0]) if k == key[1]]
        if len(sec_rows) != 1: problems.append('%s: [%s] %s missing' % ((name,) + key))
    if not all(float(opts.get(('Debug', 'UberRadius'), '0')) > g for g in Q217_GATES):
        problems.append('TruMenu.cpp: [Debug] UberRadius must reach the gates of the live test (%d / %d)' % Q217_GATES)
    sl = fn_body(src, 'ImU32 ShLabelText(')
    for need in ('ShLive(', 'kShStatusNames[fileStatus]', 'live = file', 'live %s %s %s'):
        if need not in sl: problems.append('TruMenu.cpp: ShLabelText must show file and live (lacks %s)' % need)
    lv = fn_body(src, 'bool ShLive(')
    for need in ('data + 0x28', 'ShLibId(', 'm->pc[k]', 'm->sur[k]', 'g_shFirstNew'):
        if need not in lv: problems.append('TruMenu.cpp: ShLive lacks %s (live lib ids per slot)' % need)
    nc = fn_body(src, 'int NlCollect(')
    for need in ('mask & (1ul << i)', 'layer + 0xc + 4 * k', 'g + 0x1c', 'head + 8', '0x38 + 0x14 * (flags & 0x7f)'):
        if need not in nc: problems.append('TruMenu.cpp: NlCollect lacks %s (the planner path)' % need)
    lg = fn_body(src, 'void NlLegend(')
    for need in ('gruen normal', 'rot Bit 27', 'orange +0x34 b8-11', 'gelb +0x34 b12-15', 'blau Bit 26 verschieden',
                 'magenta Bit 26', 'hellblau Kante 0x200'):
        if need not in lg: problems.append('TruMenu.cpp: NlLegend lacks "%s"' % need)
    items = item_types(src)
    for item, typ in Q217_ITEMS.items():
        mm = re.search(r'\{"%s", "%s", (?:"[^"]*"\s*)+,\s*(true|false),' % (re.escape(item), typ), src)
        if not mm: problems.append('TruMenu.cpp: item %s (%s) missing' % (item, typ))
        elif mm.group(1) != 'false': problems.append('TruMenu.cpp: %s must not be a game-thread item' % item)
        if not any(r[2] == item for r in rows): problems.append('TruMenu.cpp: item %s has no bar row' % item)
    render = fn_body(src, 'void Render(')
    for need in ('!LabelLayersOn()', 'if (g_ubOn) DrawUberLabels();', 'if (g_shOn) DrawShaderLabels();',
                 'if (g_nlOn) DrawNavLabels();'):
        if need not in render: problems.append('TruMenu.cpp: Render lacks %s' % need)
    if not (0 <= render.find('SapTick();') < render.find('!LabelLayersOn()')):
        problems.append('TruMenu.cpp: Render must call SapTick before its early return (the read-out runs without a draw)')
    sr = fn_body(src, 'bool SapRead(')
    for need in ('kSapMgr2', 'kSapVtbl', 'mgr + 0x18', 'core + 0x24', 'core + 0x2c', '1 + 204 * n + 16 * m', 'core + 0x28',
                 'ends != 2 * b', 'core + 0x30', 'p > 2 * m', 'u <= 1000'):
        if need not in sr: problems.append('TruMenu.cpp: SapRead lacks %s (the measuring plan of Befund-SweepAndPrune)' % need)
    st = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if '5d6dd6301472d6139706af928b6673679b04d4c2941ef89fb69e6f0f631a14b4' not in st or 'TruMenu.shaderlabel.txt' not in st:
        problems.append('Set-TruMenu.ps1: the 0.21.6 build in $earlierBuilds / the shader label data install missing')
    # 2 chapter units
    # 0.22.48 (owner 2026-11-14): the page name without "(debug)"
    if not re.search(r'QB_PAGE\("Kapitel", "Chapters", kQbChapters, kQsChapters\)', src):
        problems.append('TruMenu.cpp: page Kapitel must be kQsChapters (the units per chapter)')
    ub = src[src.index('const UnitRow kUnits[] = {'):]
    ub = ub[:ub.index('\n};')]
    groups = []
    for g in re.findall(r'\{"([^"]+)", "[^"]+", "[^"]+"\}', ub):
        if g not in groups: groups.append(g)
    unit_n = len(re.findall(r'\{"[^"]+", "[^"]+", "[^"]+"\}', ub))
    cg = re.search(r'const ChapGroup kChapGroups\[\] = \{(.*?)\n\};', src, re.S)
    ckeys = re.findall(r'\{"([^"]+)", "[^"]+", "[^"]+"\}', cg.group(1)) if cg else []
    if ckeys != groups: problems.append('TruMenu.cpp: kChapGroups keys %s != the groups of kUnits %s' % (ckeys, groups))
    biggest = max((len(re.findall(r'\{"%s", ' % re.escape(g), ub)) for g in groups), default=0)
    static_n = len([r for r in qb_rows(src) if r[0] == 'kQbChapters'])
    if static_n + len(groups) + biggest > 64:
        problems.append('TruMenu.cpp: page Kapitel with the biggest group open has %d rows > 64' % (static_n + len(groups) + biggest))
    qr = fn_body(src, 'int QbChapRows(')
    if '"level.load", kUnits[i].unit, kQbAction' not in qr or 'kQfConfirm | kQfBackup' not in qr:
        problems.append('TruMenu.cpp: a unit row must be level.load <unit> with kQfConfirm | kQfBackup (the chapter rows\' '
                        'path)')
    ca = fn_body(src, 'void QbChapAct(')
    if 'QbActRow(g_qbPage, r,' not in ca or any(t in ca for t in ('LoadUnit(', 'InvokeCore(', 'ShortcutStart(', 'QbRun(')):
        problems.append('TruMenu.cpp: QbChapAct must run a unit only through QbActRow (confirm, backup, one path)')
    if 'g_chapOpen = open ? g : -1' not in ca: problems.append('TruMenu.cpp: page Kapitel keeps one group open at a time')
    if 'besser DLC-2-Start + laufen' not in ca or '"DLC 2"' not in fn_body(src, 'bool ChapDlc2Note('):
        problems.append('TruMenu.cpp: the DLC 2 units need the note "besser DLC-2-Start + laufen"')
    if 'p.special == kQsChapters) QbSpecialAct(p.special, row - g_qbStaticN, kQbXDir)' not in fn_body(src, 'void QuickTick('):
        problems.append('TruMenu.cpp: QuickTick: X on page Kapitel must pass kQbXDir')
    # 1g pad diagnosis: log and footer only - QbPad (the only place that keeps bar buttons from the game) is unchanged
    qt = fn_body(src, 'void QuickTick(')
    if 'diagnosis 0.21.7' not in qt or 'g_padModeIdle && edges && !idleEdgeLogged' not in qt:
        problems.append('TruMenu.cpp: QuickTick must log the bar buttons pressed while PadHook is not called (diagnosis)')
    if 'diagnosis' in fn_body(src, 'WORD QbPad(') or 'g_qcOpen ? kQcOwn : 0' not in fn_body(src, 'WORD QbPad('):
        problems.append('TruMenu.cpp: the 0.21.7 pad diagnosis must not touch QbPad (the 0.21.6 cleared buttons stay)')
    if 'g_padModeIdle ? (de ? "   (Pad NICHT gesperrt)"' not in dq:
        problems.append('TruMenu.cpp: DrawQuick must warn while the pad is read past PadHook')
    return problems, '%d help rows, umlauts, costume check on the game thread, %d chapter groups / %d units, uber / shader / ' \
                     'navmesh layers read only with %d keys' % (len(helps), len(ckeys), unit_n, len(Q217_KEYS))


# 0.21.8 (2026-11-08 TruMenu 0.21.8, night build)
Q218_PATCHES = ((0x006203e4, 5), (0x006824b9, 5), (0x006826d3, 5), (0x0065b181, 6),   # TruShadowCombat 0.6.5 .text
                (0x0085b104, 4), (0x0085b0fc, 4), (0x0085b15c, 4), (0x00858c90, 4), (0x00859160, 4))   # .. vtable slots
Q218_RV_SAP = {0x005be3a7: '68f401000068b80b0000', 0x005be3bd: 'c74618e8030000c74620f4010000'}   # TruRockVein 0.10
Q218_DANGER = ('cheat.', 'player.invincible', 'player.die', 'level.load', 'level.start', 'level.reload', 'unit.go',
               'pos.goload', 'save.load', 'save.delete', 'save.restore', 'save.import', 'costume.reset',
               'costume.choosereset', 'costume.setreload', 'costume.choosereload', 'sw.set', 'sticky.set', 'game.quit')
Q218_SG_KEYS = ('Ambience', 'Steps', 'Weapons', 'Enemies', 'Lara', 'Objects', 'Dlc2', 'Hud')
Q218_SG_GROUPS = {'Ambience': [15], 'Steps': [32, 78], 'Weapons': [58, 60, 51, 31], 'Enemies': [27, 65],
                  'Lara': [68, 70, 72, 77], 'Objects': [43], 'Dlc2': [79], 'Hud': [54, 55, 56, 57]}   # finding section 4
Q218_STORY = ('kH2KeyPopulation', 'kH2KeyDeaths', 'kH2KeyTutorial', 'kH2KeyBroken')


def check_0218(ini_path, switches_path):
    """0.21.8: the byte check moved off TruShadowCombat 0.6.5's patch sites, the SweepAndPrune rows accept TruRockVein
    0.10's form, the quick command line (suggestions, the one on-screen keyboard with a target, history line shown,
    kCmdDanger asks twice), favourites with an argument + star, story values (read only), sound group sliders"""
    problems = []
    src = read_cpp()
    # 0.21.9: the version line keeps the 0.21.8 part (as check_0217 reads its own part)
    if not src.startswith('//') or '0.21.8 (quick command line' not in src[:src.find('\n', src.find('kVersion = '))]:
        problems.append('TruMenu.cpp: kVersion must hold the 0.21.8 part "0.21.8 (quick command line"')
    # 1 byte checks vs the patch sites of TruShadowCombat 0.6.5
    joined = re.sub(r'"\s*\n\s*"', '', src)
    rows = [(int(a, 16), len(re.sub(r'[^0-9a-fA-F]', '', h)) // 2) for a, h in
            re.findall(r'\{\s*(0x[0-9a-fA-F]{6,8})\s*,\s*"([0-9a-fA-F ]+)"', joined)]
    for site, ln in Q218_PATCHES:
        for a, n in rows:
            if a < site + ln and site < a + n:
                problems.append('TruMenu.cpp: byte check 0x%08x (+%d) covers the TruShadowCombat 0.6.5 patch 0x%08x (+%d) '
                                '- it would fail once that plugin has run' % (a, n, site, ln))
    ak = re.search(r'const DvCheck kAkChecks\[\] = \{(.*?)\n\};', src, re.S)
    if not ak or '{0x006203e9, "83c410 84c0 7417"}' not in ak.group(1):
        problems.append('TruMenu.cpp: kAkChecks must check the bytes after the call: {0x006203e9, "83c410 84c0 7417"}')
    # SweepAndPrune: the TruRockVein 0.10 form accepted for the same rows (and only there)
    tu = re.search(r'const NavCheckBytes kSapChecksTu\[\] = \{(.*?)\n\};', src, re.S)
    got = dict((int(a, 16), h.replace(' ', '')) for a, h in re.findall(r'\{(0x[0-9a-f]{8}), "([0-9a-f ]+)"\}', tu.group(1))) \
        if tu else {}
    if got != Q218_RV_SAP:
        problems.append('TruMenu.cpp: kSapChecksTu must hold exactly the TruRockVein 0.10 form of 0x5be3a7 / 0x5be3bd')
    sap = re.search(r'const NavCheckBytes kSapChecks\[\] = \{(.*?)\n\};', src, re.S)
    if not sap or '{0x005be3a7, "68c800000068e8030000"}' not in sap.group(1) or \
            '{0x005be3bd, "c74618e8030000c74620c8000000"}' not in sap.group(1):
        problems.append('TruMenu.cpp: kSapChecks must keep the retail rows (= precheck_0217_sap.txt)')
    sc = fn_body(src, 'void SapCheck(')
    if 'kSapChecksTu' not in sc or 't.at == c.at' not in sc:
        problems.append('TruMenu.cpp: SapCheck must accept the kSapChecksTu form only for the same row')
    if 'Grenzen %s' not in fn_body(src, 'void ValSap(') or 'g_sap.n == 3000 && g_sap.m2 == 1000' not in fn_body(src, 'void ValSap('):
        problems.append('TruMenu.cpp: ValSap must name the limits read from the core (PC 1000/400, TU 3000/1000)')
    stext = open(switches_path, encoding='utf-8', errors='replace').read()
    if 'TruRockVein | SweepAndPrune | Translate | bool |' not in stext:
        problems.append('%s: row TruRockVein [SweepAndPrune] Translate missing' % os.path.basename(switches_path))
    # 2a suggestions under the small line: the menu bar's list and rows
    qc = src[src.find('// ---- 0.21.6 quick command line'):src.find('// ---- end of 0.21.6 quick command line')]
    if 'CmdBuildSuggestions(g_qcBuf, false)' not in qc or 'CmdSugRows(' not in qc:
        problems.append('TruMenu.cpp: the quick command line must show CmdBuildSuggestions(g_qcBuf) with CmdSugRows')
    if 'CmdSugRows(10)' not in fn_body(src, 'void DrawCmdSuggestions('):
        problems.append('TruMenu.cpp: DrawCmdSuggestions must draw its rows with CmdSugRows (one list look)')
    # 2b one keyboard with a target
    if src.count('\nvoid DrawOsk(') != 1 or src.count('\nvoid OskInput(') != 1 or 'struct OskTarget {' not in src:
        problems.append('TruMenu.cpp: exactly one on-screen keyboard (DrawOsk / OskInput) with an OskTarget')
    for head in ('void OskAppend(', 'void OskBackspace(', 'void OskTakeSuggestion(', 'void OskRun(', 'void OskActivate(',
                 'void OskInput(', 'void DrawOsk('):
        if 'g_cmdBuf' in fn_body(src, head) or 'g_oskOpen' in fn_body(src, head):
            problems.append('TruMenu.cpp: %s...) must edit the target (g_osk), not the menu bar' % head)
    if 'DrawOsk(g_oskQc)' not in qc or 'OskInput(g_oskQc, e)' not in qc or 'DrawOsk(g_oskMenu)' not in \
            fn_body(src, 'void DrawCmdBar('):
        problems.append('TruMenu.cpp: the menu bar (g_oskMenu) and the quick command line (g_oskQc) must use the keyboard')
    if 'g_osk = &g_oskMenu;' not in fn_body(src, 'void DrawCmdBar('):
        problems.append('TruMenu.cpp: DrawCmdBar must set the keyboard target first')
    if 'const WORD kQcOskOwn = 0x0010;' not in src or 'down & ~s.passed & ~qcOsk' not in fn_body(src, 'WORD QbPad(') or \
            'kQcOskOwn' not in fn_body(src, 'extern "C" __declspec(dllexport) DWORD __cdecl TruMenuPadBlock('):
        problems.append('TruMenu.cpp: Start must be kept from the game (never a gated tap) while the line\'s keyboard is open')
    # 2c history safety
    m = re.search(r'const CmdDanger kCmdDanger\[\] = \{(.*?)\n\};', src, re.S)
    dids = re.findall(r'\{"([a-z0-9_.]+)", "', m.group(1)) if m else []
    for d in Q218_DANGER:
        if d not in dids: problems.append('TruMenu.cpp: kCmdDanger lacks %s' % d)
    dg = fn_body(src, 'const CmdDanger *CmdDangerOf(')
    for need in ('kCkInfo', 'kCkBuiltin', 'CmdIsValue(k) && !arg[0]', 'CmdCanonical('):
        if need not in dg: problems.append('TruMenu.cpp: CmdDangerOf lacks %s (reads are never dangerous)' % need)
    run = fn_body(src, 'void QcRun(')
    i_d, i_r = run.find('CmdDangerOf(line)'), run.find('CmdRunLine(')
    if not (0 <= i_d < i_r) or 'pad ? CmdDangerOf(line)' not in run or 'QcArmed()' not in run:
        problems.append('TruMenu.cpp: QcRun must arm a kCmdDanger pad run before CmdRunLine')
    if 'const DWORD kQcArmMs = 3000;' not in src:
        problems.append('TruMenu.cpp: kQcArmMs must be 3000 (the owner: "a second A within 3 s")')
    pt = fn_body(src, 'bool QcPadTick(')
    if 'QcRun(true)' not in pt or 'QcRun(false)' not in fn_body(src, 'void DrawQuickCmd(') or 'QcRun(true)' not in \
            fn_body(src, 'void QcOskRun('):
        problems.append('TruMenu.cpp: pad runs (A, the keyboard\'s Start) must be QcRun(true), Enter QcRun(false)')
    dq = fn_body(src, 'void DrawQuickCmd(')
    if '"A fuehrt aus:"' not in dq or 'g_qcHistPos >= 0 || osk' not in dq or 'ACHTUNG: %s' not in dq:
        problems.append('TruMenu.cpp: DrawQuickCmd must show the picked line before A and the armed warning')
    # 3a favourites with an argument + star
    ok = fn_body(src, 'bool FavArgOk(')
    if "arg[i] == ','" not in ok or "arg[i] == '|'" not in ok or 'kFavArgMax' not in ok:
        problems.append('TruMenu.cpp: FavArgOk must refuse "," and "|" and long arguments')
    fe = src[src.find('template <typename F> void ForFavEntries('):]
    fe = fe[:fe.find('\n}\n') + 3]
    if "strchr(e, '|')" not in fe or '" \\t"' not in fe:
        problems.append('TruMenu.cpp: ForFavEntries must read "<id>|<argument>" and the old space-separated ids')
    if 'full = true' not in fn_body(src, 'bool FavSetArg(') or 'never write a cut list' not in fn_body(src, 'bool FavSetArg('):
        problems.append('TruMenu.cpp: FavSetArg must refuse a list that does not fit (no cut write)')
    fr = fn_body(src, 'int QbFavRows(')
    if 'ForFavEntries(' not in fr or 'QbSwView(i, v[n], d[n], de)' not in fr or 'kQfConfirm | kQfBackup' not in fr:
        problems.append('TruMenu.cpp: QbFavRows must show entries with an argument (switch row, level.load with backup)')
    pin = fn_body(src, 'void QbFavPin(')
    if 'QbDynFav(dyn' not in pin or 'FavSetArg(dynId, dynArg' not in pin:
        problems.append('TruMenu.cpp: QbFavPin must pin the special rows QbDynFav names')
    dyn = fn_body(src, 'bool QbDynFav(')
    for need in ('kQdSw', 'kQdCos', 'kQdChap', '"sw.set"', '"costume.set"', '"level.load"'):
        if need not in dyn: problems.append('TruMenu.cpp: QbDynFav lacks %s' % need)
    if 'QbMarkFavs(page);' not in fn_body(src, 'void QbBuild(') or 'if (v.fav)' not in fn_body(src, 'void DrawQuick('):
        problems.append('TruMenu.cpp: the star: QbBuild must mark the favourites, DrawQuick draw " *"')
    if 'RunFavArg(arg, true' not in src or 'FavSetArg(id, arg, false' not in fn_body(src, 'void PageFavourites('):
        problems.append('TruMenu.cpp: fav.add / fav.del and the menu page must handle entries with an argument')
    # 3b story values: read only
    sv = fn_body(src, 'void ValStoryValues(')
    m = re.search(r'const StoryVal kStoryVals\[\] = \{(.*?)\n\};', src, re.S)
    for k in Q218_STORY:
        if not m or k not in m.group(1): problems.append('TruMenu.cpp: kStoryVals lacks %s (hall02)' % k)
    if 'StFind(0, s.owner' not in sv or any(t in sv for t in ('StNotify', 'kStNotify', 'WriteDword(', 'PutByte(', 'QueueItem(')):
        problems.append('TruMenu.cpp: ValStoryValues must only read (StFind / StValue)')
    if '{"story.values", "info"' not in src:
        problems.append('TruMenu.cpp: item story.values (info) missing')
    # 3c sound group sliders
    sg = src[src.find('// ---- 0.21.8 sound group sliders'):src.find('// ---- end of 0.21.8 sound group sliders')]
    sl = re.findall(r'\{"([A-Za-z0-9]+)", "[^"]*", "[^"]*", \{([0-9, ]+)\}, (\d)\}', sg)
    have = {k: [int(x) for x in g.split(',')][:int(c)] for k, g, c in sl}
    if have != Q218_SG_GROUPS:
        problems.append('TruMenu.cpp: kSgSliders must be the finding\'s eight sliders (%s)' % have)
    tick = fn_body(src, 'void SgTick(')
    if 'SgCovered(s, s.groups[k])' not in tick or 'st.orig' not in tick or '* 0x84' in tick:
        problems.append('TruMenu.cpp: SgTick must skip covered groups, restore the old factor, never write the game volume')
    wr = fn_body(src, 'bool SgWrite(')
    if 'cg + 0x38' not in wr or 'kFmCgUpdateVol' not in wr or '__try' not in wr:
        problems.append('TruMenu.cpp: SgWrite = cg + 0x38 then FMOD\'s recompute 0x7c4774 under __try')
    if 'SgTick();' not in src[src.find('        SndMuteTick();'):src.find('        SndMuteTick();') + 200]:
        problems.append('TruMenu.cpp: SgTick must run on the game thread next to SndMuteTick')
    if 'g_sgOk = g_smOk && DvChecks(kSgChecks' not in fn_body(src, 'void SgCheck(') or 'SgCheck();' not in src:
        problems.append('TruMenu.cpp: SgCheck must gate the sliders on the 0.20.1 group checks and kSgChecks')
    ini = {k: v for _, k, v in ini_section(ini_path, 'SoundGroups')}
    for k in Q218_SG_KEYS:
        if ini.get(k) != '100': problems.append('%s: [SoundGroups] %s must be 100 (got %s)' % (os.path.basename(ini_path), k,
                                                                                           ini.get(k)))
        item = 'snd.vol.%s' % k.lower()
        if '{"%s", "int"' % item not in src: problems.append('TruMenu.cpp: item %s (int) missing' % item)
        if '"%s", "", kQbValue, -1, kQcNone, kQvSndGroup' % item not in src:
            problems.append('TruMenu.cpp: bar value row for %s (kQvSndGroup) missing' % item)
    if 'r.val == kQvSndGroup ? (SgPctAt(r.id) + 5) / 10' not in fn_body(src, 'void QbActRow('):
        problems.append('TruMenu.cpp: QbActRow must step a sound group row from its item')
    return problems, 'byte check 0x6203e9, 0 checks on the 0.6.5 sites, SAP both forms, %d danger ids, one keyboard, ' \
                     'favourites with arguments, %d story values, %d sound sliders' % (
                         len(dids), len(re.findall(r'\n    \{', m.group(1))) if m else 0, len(have))


Q02213_FT_NEW = ('pc_ring_bits', 'pc_hud_g12', 'pc_ret_style', 'pc_ret40', 'pc_drip_q10706', 'pc_drip_q10707', 'pc_drip_n',
                 'pc_drip_near_x', 'pc_drip_near_y', 'pc_drip_near_z', 'pc_drip_near_dxy', 'pc_drip_near_dz',
                 'pc_drip_near_iflags', 'pc_drip_near_node', 'pc_lara_dmg')
Q02213_FT_OLD_LAST = 'pc_ramp_last'      # the 0.22.11 header ended here (TruXenia order first, then the PC columns)


def check_02213():
    """0.22.13: cutscene pad combos (sub-combos on release, the photo at once), the subtitle line clock held with the
    pause (data patch at 0x583f24, byte checks), sub.lang calls the settings save 0x478010 (byte checks, __try), the enemy
    panel text "Kampf-Spur: an (n Zeilen)", ring.bits = an info item (read only), the new fight.trace columns at the end
    (header and format agree), no hook on 0x637590 (TruShadowCombat's site), no check on TruShadowPower's 0x71e979"""
    problems = []
    src = read_cpp()
    # 1 pad combos
    pt = fn_body(src, 'void CnPadTick(')
    if 'CnPadIsSub(i)' not in pt or 'g_cnPadPeak' not in pt or 'peak == m && active' not in pt:
        problems.append('TruMenu.cpp: CnPadTick must fire a sub-combo on release only when the peak is exactly its set')
    if '!CnPadIsSub(i)' not in pt or 'held == g_cnPadMask[i]' not in pt:
        problems.append('TruMenu.cpp: CnPadTick must fire a combo that is part of no other at once (exactly its buttons)')
    sub = fn_body(src, 'bool CnPadIsSub(')
    if '(g_cnPadMask[j] & m) == m' not in sub:
        problems.append('TruMenu.cpp: CnPadIsSub must test "inside a larger combo"')
    # 2 subtitle clock
    if '{0x00583f1c, "d98308020000 d82588f1e700' not in src or 'const DvCheck kCnSubChecks[] = {' not in src:
        problems.append('TruMenu.cpp: kCnSubChecks must check the subtitle countdown 0x583f1c (fsub [0xe7f188])')
    if '{0x00583f24, kCnSubDtGame, false, "N3 subtitle clock 0x583f24"' not in src:
        problems.append('TruMenu.cpp: g_cnSubPatch must be the disp32 at 0x583f24 (data patch, not a call)')
    tick = fn_body(src, 'void CnTick(')
    i_v, i_p = tick.find('g_cnSubDt = dt;'), tick.find('M21PatchGroup(g_cnSubPatch, 1, g_cnSubOk && g_cnOn')
    if not (0 <= i_v < i_p):
        problems.append('TruMenu.cpp: CnTick must set g_cnSubDt before it patches, and patch only with the walk (g_cnOn)')
    if 'CnHeldNow() && !g_cnStepping' not in tick:
        problems.append('TruMenu.cpp: the subtitle clock stands only while held and not stepping')
    # 3 settings save
    sv = fn_body(src, 'bool SbSave(')
    if 'kSbSaveChecks' not in sv or '__try' not in sv or '0x00478010' not in sv or '0x00ad75e4' not in sv:
        problems.append('TruMenu.cpp: SbSave must byte-check 0x478010, test [0xad75e4] and call it under __try')
    if 'SbSave(saved, sizeof(saved))' not in fn_body(src, 'bool RunSb('):
        problems.append('TruMenu.cpp: RunSb must call SbSave after the option setter')
    if not re.search(r'\{"sub\.lang", "action", .*?true, ValSb, RunSb\}', src, re.S):
        problems.append('TruMenu.cpp: sub.lang must stay a game-thread item (the save runs there)')
    # 4 enemy panel text
    ep = re.sub(r'//[^\n]*', '', fn_body(src, 'void DrawEnemyPanel('))
    if '"Kampf-Spur: an (%ld Zeilen)"' not in ep or '"Fight trace: on (%ld lines)"' not in ep or 'Kampf-Spur: Zeilen' in ep:
        problems.append('TruMenu.cpp: DrawEnemyPanel must say "Kampf-Spur: an (n Zeilen)" / "Fight trace: on (n lines)"')
    # 5 ring.bits: an info item, read only
    if '{"ring.bits", "info",' not in src or 'false, ValRg, nullptr}' not in src:
        problems.append('TruMenu.cpp: ring.bits must be an info item without a runner')
    rg = src[src.find('// ---- 0.22.13 ring bits'):src.find('// ---- 0.22.13 goo drips')]
    if not rg or any(t in rg for t in ('WriteDword(', 'WriteBytes(', 'PutByte(', 'QueueItem(')):
        problems.append('TruMenu.cpp: the ring bit section must only read')
    code = re.sub(r'//[^\n]*', '', rg)
    if any(a in code for a in ('0x0071e979', '0x00715026', '0x00716f5f')):
        problems.append('TruMenu.cpp: no run-time byte check on TruShadowPower\'s patch sites 0x71e979 / 0x715026 / 0x716f5f')
    if '"Ziel-Ring: Bits (live)", "Target ring: bits (live)", "ring.bits", "", kQbInfo' not in src:
        problems.append('TruMenu.cpp: bar row "Ziel-Ring: Bits (live)" (info) missing')
    # 6 fight.trace columns: the old header unchanged, new columns at the end, the format has one field per column
    m = re.search(r'const char \*const kFtHeader = (.*?);\r?\n', src, re.S)
    head = ''.join(re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))).replace('\\t', '\t').replace('\\n', '\n') if m else ''
    cols = head.rstrip('\n').split('\t')
    new_at = cols.index(Q02213_FT_OLD_LAST) + 1 if Q02213_FT_OLD_LAST in cols else 0   # 0.22.18: more columns after
    if Q02213_FT_OLD_LAST not in cols or tuple(cols[new_at:new_at + len(Q02213_FT_NEW)]) != Q02213_FT_NEW or \
            cols[:3] != ['host_time', 'inst', 'obj_id']:
        problems.append('TruMenu.cpp: kFtHeader must keep the TruXenia order and end with %s' % ', '.join(Q02213_FT_NEW))
    wr = fn_body(src, 'void FtWrite(')
    fm = re.search(r'_snprintf_s\(line, sizeof\(line\), _TRUNCATE,\s*((?:"[^"]*"\s*)+),', wr)
    fmt = ''.join(re.findall(r'"([^"]*)"', fm.group(1))) if fm else ''
    fields = fmt.count('\\t') + 1 if fmt else 0
    if fields != len(cols):
        problems.append('TruMenu.cpp: FtWrite writes %d fields, kFtHeader has %d columns' % (fields, len(cols)))
    ft = fn_body(src, 'void FtTick(')
    if 'FtDripRead(w.pos, w.drip)' not in ft or 'w.drip.zone' not in ft:
        problems.append('TruMenu.cpp: FtTick must read the goo drips (FtDripRead) and write a line every sample in the zone')
    dr = fn_body(src, 'void FtDripRead(')
    if 'oid == 926' not in dr or 'intro == 10706 || intro == 10707' not in dr or 'oid == 929 || oid == 942' not in dr or \
            '2500.0f * 2500.0f' not in dr:
        problems.append('TruMenu.cpp: FtDripRead must use the finding\'s sources 10706 / 10707 (926), copies 929 / 942, 2500')
    look = fn_body(src, 'void FtDmgLook(')
    if 'HexBytesAt(0x00637590' not in look or re.search(r'Write(Bytes|Dword)\(\s*0x00637590', src):
        problems.append('TruMenu.cpp: 0x637590 must only be looked at (TruShadowCombat hooks it), never written')
    return problems, 'pad sub-combos on release, subtitle clock 0x583f24, settings save 0x478010, panel text, ring.bits ' \
                     'info, %d fight.trace columns (%d new at the end)' % (len(cols), len(Q02213_FT_NEW))


def unescape(s):
    return s.replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')


def check_02214():
    """0.22.14: sub.lang rewrites the shown subtitle lines at once - the two call patches 0x4574ec (reader) and 0x453a17
    (box add line) with their byte checks, a ring of 2 whole records (copied, not a pointer), the rewrite only after the
    option setter and the settings save, the box written only at +0 / +0x100 (never the clock +0x208 or the floats)"""
    problems = []
    src = read_cpp()
    a, b = src.find('// ---- 0.22.14 sub.lang switches'), src.find('\nbool RunSb(')
    sec = src[a:b] if 0 <= a < b else ''
    if not sec:
        return ['TruMenu.cpp: section "0.22.14 sub.lang switches" missing (before RunSb)'], ''
    for want in ('{0x004574ec, 0x004538d0, true, "S1 subtitle reader call 0x4574ec"',
                 '{0x00453a17, 0x00583db0, true, "S2 subtitle box add call 0x453a17"',
                 '{0x004574de, "68a0cf9c00 8bce c683a0cf9c0000 e8dfc3ffff"}', '{0x00453a0f, "6a5a 50 b9c0decc00 e894031300"}',
                 '{0x00453a75, "c20400"}', '{0x00583e15, "c20800"}', 'const int kSrRing = 2'):
        if want not in sec:
            problems.append('TruMenu.cpp: 0.22.14 section must hold %s' % want)
    rd = fn_body(src, 'void __fastcall SrReader(')
    if 'r.text[i] = text[i]' not in rd or '__try' not in rd or 'reinterpret_cast<SrReaderFn>(0x004538d0)' not in rd:
        problems.append('TruMenu.cpp: SrReader must copy the whole record under __try, then call the reader 0x4538d0')
    tk = fn_body(src, 'void SrTick(')
    if not (0 <= tk.find('CnCheck();') < tk.find('SrCheck()') < tk.find('M21PatchGroup(g_srPatches')):
        problems.append('TruMenu.cpp: SrTick must run CnCheck (reads 0x4574ec) and SrCheck before it patches')
    code = re.sub(r'//[^\n]*', '', fn_body(src, 'void SrRewrite('))
    if 'WriteBytes(at, buf, len + 1)' not in code or 'strnlen_s(want[s], 0xff)' not in code:
        problems.append('TruMenu.cpp: SrRewrite must write each box line with its NUL, at most 0xff bytes')
    if re.search(r'kSrBox \+ 0x20[048]', code) or 'WriteDword(' in code:
        problems.append('TruMenu.cpp: SrRewrite must not touch the clock +0x208 or the floats +0x200 / +0x204')
    rs = fn_body(src, 'bool RunSb(')
    i_set, i_save, i_rw = rs.find('0x005d5100'), rs.find('SbSave(saved'), rs.find('SrRewrite(v,')
    if not (0 <= i_set < i_save < i_rw):
        problems.append('TruMenu.cpp: RunSb must rewrite the box after the option setter and the settings save')
    if 'SrTick();' not in fn_body(src, 'DWORD WINAPI PadHook('):
        problems.append('TruMenu.cpp: SrTick must run once per game frame (PadHook)')
    return problems, 'record ring (2 whole records), calls 0x4574ec / 0x453a17, rewrite after setter + save, box +0 / ' \
                     '+0x100 only'


def check_02215():
    """0.22.15: aim.trace / aim.why read the lock-on path only - 25 byte checks (kAmChecks) behind AmCheck (which also
    needs the ring.bits and chart checks), no write into game memory and no game call in the section, the TruAim.log
    header has as many columns as AmBody writes, both items in kOpts, bar rows on page Tests next to ring.bits, AmTick
    once per game frame"""
    problems = []
    src = read_cpp()
    a, b = src.find('// ---- 0.22.15 aim.trace / aim.why'), src.find('\nvoid ValFt(')
    sec = src[a:b] if 0 <= a < b else ''
    if not sec:
        return ['TruMenu.cpp: section "0.22.15 aim.trace / aim.why" missing (before ValFt)'], ''
    tab = sec[sec.find('const DvCheck kAmChecks[] = {'):]
    tab = tab[:tab.find('\n};')]
    n_checks = len(re.findall(r'\{0x[0-9a-f]{8}, "', tab))
    if n_checks != 25:
        problems.append('TruMenu.cpp: kAmChecks must hold 25 byte checks (has %d)' % n_checks)
    for want in ('{0x006f2800, "53 8b1d58dbfa00 8b8300050000 56 8bb034010000 83fe0c"}',
                 '{0x0072170a, "a164d7fa00 0fb69094020000"}', '{0x00484c32, "c7460404000000"}',
                 '{0x007216b0, "83ec08 55 8be9 f785fc01000000000400"}', '{0x0071d97d, "898f90000000"}',
                 'g_amOk = RgCheck() && CtCheck() && DvChecks(kAmChecks'):
        if want not in sec:
            problems.append('TruMenu.cpp: 0.22.15 section must hold %s' % want)
    code = re.sub(r'//[^\n]*', '', sec)
    for bad in ('WriteDword(', 'WriteBytes(', 'WriteByte(', 'VirtualProtect(', '__asm', 'Fn>(0x00'):
        if bad in code:
            problems.append('TruMenu.cpp: the 0.22.15 section must stay read only (found %s)' % bad)
    hdr = re.search(r'kAmHeader = ((?:"[^"]*"\s*)+);', sec)
    cols = ''.join(re.findall(r'"([^"]*)"', hdr.group(1))).replace('\\t', '\t').replace('\\n', '').split('\t') if hdr else []
    body = fn_body(src, 'void AmBody(')
    fmt = re.search(r'Out\(o, n, ((?:"[^"]*"\s*)+),', body)
    nfmt = len(re.findall(r'%[-0-9.]*l?[dusxf]', ''.join(re.findall(r'"([^"]*)"', fmt.group(1))))) if fmt else -1
    # the line = host_time + AmBody's fields; the four bucket counts %lu/%lu/%lu/%lu are one column (t0_buckets)
    if not cols or len(cols) - 1 != nfmt - 3:
        problems.append('TruMenu.cpp: TruAim.log header has %d columns, AmBody writes %d' % (len(cols), nfmt - 3 + 1))
    for item in ('{"aim.trace", "bool",', '{"aim.why", "info",'):
        if item not in src:
            problems.append('TruMenu.cpp: kOpts needs %s' % item)
    rows = src.find('"ring.bits", "", kQbInfo')
    if rows < 0 or src.find('"aim.trace", "", kQbBool', rows) < 0 or src.find('"aim.why", "", kQbInfo', rows) < 0:
        problems.append('TruMenu.cpp: bar rows aim.trace (bool) / aim.why (info) must follow ring.bits on page Tests')
    if 'AmTick();' not in fn_body(src, 'DWORD WINAPI PadHook('):
        problems.append('TruMenu.cpp: AmTick must run once per game frame (PadHook)')
    return problems, '%d byte checks, read only, %d TruAim.log columns, items + bar rows, AmTick per frame' % (
        n_checks, len(cols))


Q2216_ITEMS = {'sub.show': 'bool', 'sub.size': 'float', 'sub.box': 'bool', 'sub.boxalpha': 'int', 'sub.colour': 'action',
               'sub.pos': 'int', 'sub.reset': 'action', 'gfx.save': 'action', 'gfx.status': 'info', 'gfx.next': 'action'}
Q2216_KEYS = (('SubShow', '1'), ('SubSize', '0.6'), ('SubBox', '1'), ('SubBoxAlpha', '25'), ('SubColour', 'white'),
              ('SubPos', '352'))
Q2216_PAGES = ('Spiel-Einstellungen', 'Rettung / Cheats', 'Figur', 'Gegner (KI)', 'Leveldaten', 'Render',
               'Debug / Darstellung', 'Zeit / Ablauf', 'Tests')


def check_02216(ini_path):
    """0.22.16: game settings page - the plan's 29 byte checks (kGsChecks), ValGs<k> / RunGs<k> of kItems = kGsDefs[k],
    ApplySettings only in GfTick (PadHook via GsTick, never the Present hook), the [Settings] keys with their defaults,
    the subtitle sites only written in SuApply / GsShutdown, U3 (shown[] matched in SrRewrite), SbName(11), the new
    page order (still 17 pages, Leveldaten = start page)"""
    problems = []
    src = read_cpp()
    a, b = src.find('// ---- 0.22.16 game settings'), src.find('// ---- end of 0.22.16 game settings')
    sec = src[a:b] if 0 <= a < b else ''
    if not sec:
        return ['TruMenu.cpp: section "0.22.16 game settings" missing'], ''
    tab = sec[sec.find('const GsCheckRow kGsChecks[] = {'):]
    tab = tab[:tab.find('\n};')]
    n_checks = len(re.findall(r'\{kGg[A-Za-z]+, 0x[0-9a-f]{8}, "', tab))
    if n_checks != 29:
        problems.append('TruMenu.cpp: kGsChecks must hold the plan\'s 29 byte checks (has %d)' % n_checks)
    defs = sec[sec.find('const GsDef kGsDefs[] = {'):]
    defs = re.findall(r'\{"([a-z.0-9]+)", kGk', defs[:defs.find('\n};')])
    for k, item in enumerate(defs):
        if not re.search(r'\{"%s", "[a-z]+",\s*(?:"[^"]*"\s*)+,\s*(?:true|false),\s*ValGs<%d>,\s*(?:RunGs<%d>|nullptr)\}'
                         % (re.escape(item), k, k), src):
            problems.append('TruMenu.cpp: kItems row %s must use ValGs<%d> (kGsDefs index)' % (item, k))
    items = dict(re.findall(r'\{"([a-z0-9.]+)", "(bool|int|float|info|action)",', src))
    for item, typ in Q2216_ITEMS.items():
        if items.get(item) != typ: problems.append('TruMenu.cpp: item %s (%s) missing in kItems' % (item, typ))
    code = re.sub(r'//[^\n]*', '', sec)
    if code.count('0x00522a10)(dm') != 1 or 'reinterpret_cast<GsApplyFn>(0x00522a10)' not in fn_body(src, 'void GfTick('):
        problems.append('TruMenu.cpp: ApplySettings 0x522a10 is called in GfTick only')
    if 'GfTick();' not in fn_body(src, 'void GsTick(') or 'GsTick();' not in fn_body(src, 'DWORD WINAPI PadHook('):
        problems.append('TruMenu.cpp: GfTick runs from GsTick, GsTick once per game frame in PadHook')
    for fn in ('HRESULT STDMETHODCALLTYPE PresentHook(', 'HRESULT STDMETHODCALLTYPE SwapPresentHook('):
        if 'GsTick' in fn_body(src, fn) or 'GfTick' in fn_body(src, fn):
            problems.append('TruMenu.cpp: no game settings tick in the Present hook')
    if 'if (dm + 0x10' in code or 'ReadDword(dm + 0x10, &lost) || lost' not in fn_body(src, 'void GfTick('):
        problems.append('TruMenu.cpp: GfTick must wait while [dm+0x10] != 0 (device lost)')
    writes = [m.start() for m in re.finditer(r'WriteBytes\(s\.at', code)]
    if len(writes) != 2 or 'WriteBytes(s.at, bytes, static_cast<size_t>(s.size))' not in fn_body(src, 'bool SuSiteSet('):
        problems.append('TruMenu.cpp: the subtitle sites are written only by SuSiteSet / GsShutdown')
    rw = fn_body(src, 'void SrRewrite(')
    if 'r.shown[all[i].k]' not in rw or 'hit.shown[all[pos[s]].k], 0x100, buf' not in rw:
        problems.append('TruMenu.cpp: U3 - SrRewrite must match and remember the rewritten line (shown[k])')
    if 'case 11: return "Nederlands";' not in fn_body(src, 'const char *SbName('):
        problems.append('TruMenu.cpp: SbName(11) must be "Nederlands"')
    if 'const int kQbSubLangs[7] = {-1, 0, 1, 2, 3, 4, 11};' not in src:
        problems.append('TruMenu.cpp: sub.lang bar steps -1 / 0 / 1 / 2 / 3 / 4 / 11')
    ini = open(ini_path, encoding='utf-8').read()
    for key, default in Q2216_KEYS:
        if not re.search(r'^\[Settings\][^\[]*^%s=%s$' % (key, re.escape(default)), ini, re.M | re.S):
            problems.append('TruMenu.ini: [Settings] %s=%s missing' % (key, default))
    block = src[src.index('const QbPage kQbPages[] = {'):]
    block = block[:block.index('\n};')]
    names = re.findall(r'(?:QB_PAGE\(|\{)"([^"]*)", "[^"]*", (?:kQb|nullptr)', block)
    pos = -1
    for want in Q2216_PAGES:
        if want not in names: problems.append('TruMenu.cpp: page %s missing' % want)
        elif names.index(want) < pos: problems.append('TruMenu.cpp: page %s out of the plan\'s order' % want)
        else: pos = names.index(want)
    if len(names) != 17: problems.append('TruMenu.cpp: kQbPages must keep 17 pages (has %d)' % len(names))
    return problems, '%d byte checks, %d settings items in kGsDefs order, ApplySettings only in GfTick (PadHook), ' \
                     '[Settings] keys, U3, %d pages' % (n_checks, len(defs), len(names))


def check_02217(ini_path):
    """0.22.17: subtitle fallback - [Settings] SubtitleFallback=1 (kOpts, sample .ini, GsReadOptions), SrReader hands
    the English record to the reader 0x4538d0 only through SfUse (wanted id missing, id 0 present, the stream never
    carried the wanted id) + SfBuild, the stream reset on a handler change or a time step back (stream list offsets
    +0x14 / +0x77c / +0x384 = the ones of kCnChecks, read only with g_cnOk), SrLines uses the same rule with r.seen"""
    problems = []
    src = read_cpp()
    if '"0.22.17 (subtitle fallback' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.18: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.17 part "0.22.17 (subtitle fallback"')
    if not re.search(r'\{"Settings", "SubtitleFallback", "1", "0\.22\.17:', src):
        problems.append('TruMenu.cpp: kOpts row [Settings] SubtitleFallback default 1 missing')
    ini = open(ini_path, encoding='utf-8').read()
    if not re.search(r'^\[Settings\][^\[]*^SubtitleFallback=1$', ini, re.M | re.S):
        problems.append('TruMenu.ini: [Settings] SubtitleFallback=1 missing')
    if 'OptInt(ini, "Settings", "SubtitleFallback")' not in fn_body(src, 'void GsReadOptions('):
        problems.append('TruMenu.cpp: GsReadOptions must read [Settings] SubtitleFallback')
    use = re.sub(r'//[^\n]*', '', fn_body(src, 'bool SfUse('))
    for want in ('g_sfOn', 'want > 0', '!(mask & (1u << want))', '(mask & 1u)', '!(seen & (1u << want))'):
        if want not in use: problems.append('TruMenu.cpp: SfUse must test %s' % want)
    rd = re.sub(r'//[^\n]*', '', fn_body(src, 'void __fastcall SrReader('))
    i_time, i_use, i_or, i_call = (rd.find('SfStreamTime(self, &t)'), rd.find('SfUse(mask, want, g_sfSeen)'),
                                   rd.find('g_sfSeen |= mask'), rd.find('(self, edx, r.fallback ? g_sfBuf : text)'))
    if not (0 <= i_time < i_use < i_or < i_call):
        problems.append('TruMenu.cpp: SrReader order - stream time, SfUse (ids before this record), add the record\'s '
                        'ids, then the reader with g_sfBuf only on a fallback')
    if 'self != g_sfHandler || (timed && t + 0.5f < g_sfTime)' not in rd or 'g_sfSeen = 0;' not in rd:
        problems.append('TruMenu.cpp: SrReader must start a new stream on a handler change or a time step back')
    st = re.sub(r'//[^\n]*', '', fn_body(src, 'bool SfStreamTime('))
    for want in ('if (!g_cnOk) return false;', 'ReadDword(0x00ccdc64, &s)', 'ReadDword(s + 0x77c, &h)',
                 'ReadFloats(s + 0x384, t, 1)', 'ReadDword(s + 0x14, &s)'):
        if want not in st: problems.append('TruMenu.cpp: SfStreamTime must hold %s' % want)
    for want in ('{0x005904d0, "a164dccc00', '{0x00590303, "8b8e7c070000', '{0x0059023f, "d99e84030000"}',
                 '{0x00590431, "8b4614'):
        if want not in src: problems.append('TruMenu.cpp: kCnChecks must still pin %s (SfStreamTime relies on it)' % want)
    ln = fn_body(src, 'int SrLines(')
    if 'SfUse(SrIdMask(r.text), SrWant(word, gameLang, r.kind), r.seen)' not in ln or 'english ? id == 0 :' not in ln:
        problems.append('TruMenu.cpp: SrLines must use the fallback rule with the record\'s stream ids (r.seen)')
    bd = re.sub(r'//[^\n]*', '', fn_body(src, 'bool SfBuild('))
    if 'n + static_cast<size_t>(hl) + el + 2 > cap' not in bd or 'out[n] = 0;' not in bd:
        problems.append('TruMenu.cpp: SfBuild must stay inside its buffer and end with NUL')
    return problems, 'SubtitleFallback key, SfUse rule, stream reset, stream list offsets pinned by kCnChecks'


def check_02218(ini_path):
    """0.22.18: volume save through 0x4796b0, groups everywhere (nesting, no '--' labels), frame stepping, subtitle
    alignment, voice.lang / voice.full, music rows, goo drip candidates, light.demote, settings written back, defaults
    (big menu / ring off, bar on, English), TruShadowPower [Meter] Infinite, Set-TruMenu hashes + media fallback"""
    problems = []
    src = read_cpp()
    if '"0.22.18 (volumes / mouse saved' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.19: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.18 part "0.22.18 (volumes / mouse saved"')
    ini = open(ini_path, encoding='utf-8').read()
    # defaults: kOpts = sample .ini = code default when the key is missing
    for sec, key, val in (('Menu', 'Enabled', '0'), ('Menu', 'Load', '1'), ('Radial', 'Enabled', '0'),
                          ('Quick', 'Enabled', '1'), ('Quick', 'Language', 'en'), ('Settings', 'StepRate', '10'),
                          ('Settings', 'SubAlignV', '0'), ('Settings', 'SubAlignH', '0'), ('Settings', 'SubMargin', '5'),
                          ('Settings', 'VoiceLanguage', 'game'), ('Light', 'Demote', '0')):
        if not re.search(r'\{"%s", "%s", "%s",' % (sec, key, re.escape(val)), src):
            problems.append('TruMenu.cpp: kOpts [%s] %s default must be %s' % (sec, key, val))
        block = re.search(r'^\[%s\]\r?\n(.*?)(?=^\[|\Z)' % sec, ini, re.M | re.S)   # comments may hold '['
        if not block or not re.search(r'^%s=%s\r?$' % (key, re.escape(val)), block.group(1), re.M):
            problems.append('TruMenu.ini: [%s] %s=%s missing' % (sec, key, val))
    for want in ('int g_menuWindow = 0;', 'int g_radEnabled = 0;', 'int g_qbLang = 1;', 'g_enabled = OptInt(ini, "Menu", "Load");',
                 "g_qbLang = !_stricmp(v, \"de\") ? 0 : 1;"):
        if want not in src: problems.append('TruMenu.cpp: default %s missing' % want)
    tm = re.sub(r'//[^\n]*', '', fn_body(src, 'void ToggleMenu('))
    if 'if (open && !g_menuWindow)' not in tm or 'return;' not in tm:
        problems.append('TruMenu.cpp: ToggleMenu must refuse to open while [Menu] Enabled=0')
    # 1 volume save
    m = re.search(r'const DvCheck kVsChecks\[\] = \{(.*?)\n\};', src, re.S)
    if not m or len(re.findall(r'\{0x', m.group(1))) != 6:
        problems.append('TruMenu.cpp: kVsChecks must hold the 6 rows of precheck_02218 (mirrors, 0x4796b0, native)')
    full = re.sub(r'//[^\n]*', '', fn_body(src, 'bool GsSaveFull('))
    for want in ('SbSave(', '0x004796b0', 'GnRewrite()', 'prof + off[k]'):
        if want not in full: problems.append('TruMenu.cpp: GsSaveFull must hold %s' % want)
    tick = fn_body(src, 'void GsTick(')
    if 'g_gsSaveFull' not in tick or 'GsSaveFull("options"' not in tick or 'VlTick();' not in tick:
        problems.append('TruMenu.cpp: GsTick must save volumes through GsSaveFull and call VlTick')
    # 2 groups: no '--' label rows left in the bar tables, sub-groups, nesting in QbBuild
    tables = src[src.find('const QbRow kQbSettings[] = {'):src.find('const QbPage kQbPages[]')]
    # 0.22.53 W11: the owner's plain heading "Schnell-Hoeren" between the two sound log trees (level 2, kQfLv2) is wanted
    if re.search(r'"-", "[^"]*", kQbLabel(?![^}]*kQfLv2\})', tables):
        problems.append('TruMenu.cpp: a bar table still has a kQbLabel heading (0.22.18: every section a group)')
    keys = re.findall(r'"-", "([a-z0-9_]+)", kQbGroup', tables)
    dup = sorted(set(k for k in keys if keys.count(k) > 1))
    if dup: problems.append('TruMenu.cpp: group keys used twice: %s' % ', '.join(dup))
    for key in ('ton_gruppen', 'set_gfxdev'):
        if not re.search(r'"-", "%s", kQbGroup, -1, kQcNone, 0, kQb\w+, kQfSub\}' % key, tables):
            problems.append('TruMenu.cpp: group %s must be a sub-group (kQfSub)' % key)
    qb = fn_body(src, 'void QbBuild(')
    if 'QbGroupLevel(r)' not in qb or 'hideAbove' not in qb or 'v.depth = ' not in qb:
        problems.append('TruMenu.cpp: QbBuild must nest groups (QbGroupLevel, hideAbove, depth)')
    dq = fn_body(src, 'void DrawQuick(')
    if 'leftOf' not in dq or 'AddLine' not in dq:
        problems.append('TruMenu.cpp: DrawQuick must indent rows per level and draw the guide line')
    # 3 frame stepping
    pad = fn_body(src, 'void CnPadTick(')
    if 'CnStepRepeat(held, active, now);' not in pad or 'CnPadMod()' not in pad or 'g_cnStepEnded' not in pad:
        problems.append('TruMenu.cpp: CnPadTick must use CnPadMod / CnStepRepeat / g_cnStepEnded (0.22.18)')
    # 4 subtitle alignment, 5 voice, 8 light.demote: check tables
    for name, n in (('kSaChecks', 7), ('kVlChecks', 9), ('kLdChecks', 10)):
        m = re.search(r'const DvCheck %s\[\] = \{(.*?)\n\};' % name, src, re.S)
        if not m or len(re.findall(r'\{0x', m.group(1))) != n:
            problems.append('TruMenu.cpp: %s must hold %d rows (precheck_02218)' % (name, n))
    sl = fn_body(src, 'DWORD __fastcall GsSubLine(')
    if 'if (shift) SaSetOriginX(ox);' not in sl:
        problems.append('TruMenu.cpp: GsSubLine must put the origin x back after the line')
    pre = os.path.join(ROOT, 'work', 'asi', 'menu0241', 'precheck_02218.txt')
    if os.path.exists(pre):
        rows = [l for l in open(pre, encoding='utf-8').read().splitlines() if l.strip() and not l.startswith('#')]
        if len(rows) != 32: problems.append('precheck_02218.txt: 32 rows expected, %d' % len(rows))
    # persistence: the bar's TruMenu-own settings write their key at once
    for fn, key in (('bool RunQuickLang(', '"Quick", "Language"'), ('bool RunCsScale(', '"Camera", "ShakeScale"'),
                    ('bool RunRbRumble(', '"Camera", "Rumble"'), ('bool RunMuteMusic(', '"Media", "MuteMusic"'),
                    ('bool RunMuteAmbient(', '"Media", "MuteAmbient"'), ('bool RunLs(', '"Light", "Stable"'),
                    ('bool RunLcStable(', '"Light", "StableCut"'), ('bool RunCnStepRate(', '"Settings", "StepRate"'),
                    ('bool RunVl(', '"Settings", "VoiceLanguage"'), ('bool RunMusicInLevels(', '"Media", "MusicInLevels"'),
                    ('bool RunLd(', '"Light", "Demote"'), ('bool RunHideCursor(', '"Menu", "HideCursor"')):
        if key not in fn_body(src, fn): problems.append('TruMenu.cpp: %s must write [%s] at once' % (fn[5:-1], key))
    for want in ('"SubAlignV"', '"SubAlignH"', '"SubMargin"'):
        if want not in fn_body(src, 'void SuSave('): problems.append('TruMenu.cpp: SuSave must write %s' % want)
    # 6 music rows, 7 drip candidates, TruShadowPower Infinite
    for item in ('media.music.inlevels', 'voice.lang', 'voice.full', 'light.demote', 'cine.steprate', 'sub.valign',
                 'sub.halign', 'sub.margin'):
        if not re.search(r'\{"%s", "' % re.escape(item), src): problems.append('TruMenu.cpp: item %s missing' % item)
    if '"pc_drip_b0_x\\tpc_drip_b0_y\\tpc_drip_b0_z\\tpc_drip_b0_dz\\tpc_drip_b0_lowz\\t"' not in src:
        problems.append('TruMenu.cpp: fight.trace header must end with the 0.22.18 drip candidate columns')
    if '{"TruShadowPower", "Meter", "Infinite"}' not in src or 'kQdFigPlan' in src:
        problems.append('TruMenu.cpp: kQbFigShadow must hold [Meter] Infinite, the planned row must be gone')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    for h in ('6fb7c6772c147b952ae595a39b7601fb2d8b36e34bfa37cf73c6bc18d06a8235',
              '7c810b6dc7a344b3302f70762b6e0f77bf7aab6cdf17922058ae1b70e8d0ff38'):
        if h not in ps: problems.append('Set-TruMenu.ps1: earlier build hash %s... missing' % h[:12])
    if 'work\\media\\menu\\$mediaList' not in ps:
        problems.append('Set-TruMenu.ps1: the media list fallback work\\media\\menu is missing')
    return problems, 'defaults, volume save, %d groups (no labels), step mode, alignment / voice / demote checks, ' \
                     'settings written back, drip columns, Set-TruMenu' % len(keys)


def check_02219(ini_path, switches_path):
    """0.22.19: pages remembered ([Menu] RememberPage / OpenPages for the big window's collapsing headers, [Quick]
    RememberPage / LastPage for the bar), power.infinite (TruShadowPower 0.23 [Meter] Infinite) with its bar row"""
    problems = []
    src = read_cpp()
    if '"0.22.19 (pages remembered' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.20: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.19 part "0.22.19 (pages remembered"')
    ini = open(ini_path, encoding='utf-8').read()
    for sec, key, val in (('Menu', 'RememberPage', '1'), ('Menu', 'OpenPages', 'totest,quick'),
                          ('Quick', 'RememberPage', '1'), ('Quick', 'LastPage', '')):
        if not re.search(r'\{"%s", "%s", "%s",' % (sec, key, re.escape(val)), src):
            problems.append('TruMenu.cpp: kOpts [%s] %s default must be "%s"' % (sec, key, val))
        block = re.search(r'^\[%s\]\r?\n(.*?)(?=^\[|\Z)' % sec, ini, re.M | re.S)
        if not block or not re.search(r'^%s=%s\r?$' % (key, re.escape(val)), block.group(1), re.M):
            problems.append('TruMenu.ini: [%s] %s=%s missing' % (sec, key, val))
    # 1a big window: every page header through MenuPage, one key each, all keys in kMpPages
    m = re.search(r'const char \*const kMpPages\[\] = \{(.*?)\};', src, re.S)
    mp = re.findall(r'"([a-z0-9]+)"', m.group(1)) if m else []
    if not mp: problems.append('TruMenu.cpp: kMpPages missing')
    if len(set(mp)) != len(mp): problems.append('TruMenu.cpp: kMpPages holds a key twice')
    dm = re.sub(r'//[^\n]*', '', fn_body(src, 'void DrawMenu('))
    if 'TmCollapsingHeader(' in dm or 'ImGui::CollapsingHeader(' in dm:
        problems.append('TruMenu.cpp: DrawMenu still draws a page header without MenuPage')
    used = re.findall(r'MenuPage\((?:"(?:[^"\\]|\\.)*"|header), "([a-z0-9]+)"', dm)
    if sorted(used) != sorted(mp):
        problems.append('TruMenu.cpp: DrawMenu MenuPage keys %s != kMpPages %s' % (sorted(used), sorted(mp)))
    for k in 'totest,quick'.split(','):
        if k not in mp: problems.append('TruMenu.cpp: OpenPages default key %s not in kMpPages' % k)
    pg = fn_body(src, 'bool MenuPage(')
    for want in ('ImGui::SetNextItemOpen(MpHas(g_mpOpen, key), ImGuiCond_Once)', 'ImGui::IsItemToggledOpen()',
                 'IniKeep("Menu", "OpenPages", g_mpOpen)', 'if (g_mpRemember'):
        if want not in pg: problems.append('TruMenu.cpp: MenuPage must hold %s' % want)
    ro = fn_body(src, 'void ReadOptions(')
    for want in ('OptInt(ini, "Menu", "RememberPage")', 'MpLoad(pages);', 'quick("RememberPage", 0, 1)',
                 'OptString(ini, "Quick", "LastPage"', 'QbPageLoad(last);'):
        if want not in ro: problems.append('TruMenu.cpp: ReadOptions must hold %s' % want)
    # 1b quick bar: written only on a change (debounced while open), page names unique
    qt = fn_body(src, 'void QuickTick(')
    if 'QbPageKeep();' not in qt or qt.find('QbPageKeep();') > qt.find('if (!g_qbOpen || g_menuOpen'):
        problems.append('TruMenu.cpp: QuickTick must call QbPageKeep before its early returns')
    keep = fn_body(src, 'void QbPageKeep(')
    for want in ('g_qbPage == g_qbPageSaved', 'now - g_qbPageAt < 1000', 'IniKeep("Quick", "LastPage", kQbPages[g_qbPage].en)'):
        if want not in keep: problems.append('TruMenu.cpp: QbPageKeep must hold %s' % want)
    load = fn_body(src, 'void QbPageLoad(')
    if 'g_qbPage = 0;' not in load or 'Log(1, ' not in load or 'kQbStartPage' not in load:
        problems.append('TruMenu.cpp: QbPageLoad must fall back to page 1 with a log line, empty = kQbStartPage')
    pages = re.findall(r'(?:QB_PAGE\(|\{)"((?:[^"\\]|\\.)*)", "((?:[^"\\]|\\.)*)", (?:kQb\w+|nullptr)',
                       src[src.find('const QbPage kQbPages[] = {'):src.find('#undef QB_PAGE')])
    names = [n.lower() for de, en in pages for n in {de, en}]
    if len(pages) != 17: problems.append('TruMenu.cpp: kQbPages: 17 pages expected, %d' % len(pages))
    if len(names) != len(set(names)): problems.append('TruMenu.cpp: a bar page name is used twice (LastPage)')
    for de, en in pages:
        if not re.match(r'^[ -~]+$', en) or en != en.strip() or en.isdigit():
            problems.append('TruMenu.cpp: page name "%s" unfit for [Quick] LastPage' % en)
    # 2 power.infinite
    if not re.search(r'\{"power\.infinite", "bool", "', src): problems.append('TruMenu.cpp: item power.infinite missing')
    if 'const char *const kPiTarget = "ini:TruShadowPower:Meter:Infinite";' not in src:
        problems.append('TruMenu.cpp: kPiTarget must be ini:TruShadowPower:Meter:Infinite')
    run = fn_body(src, 'bool RunPi(')
    for want in ('if (!v[0]) { ValPi(o, n); return true; }', 'WritePrivateProfileStringA("Meter", "Infinite"',
                 'PiWhy()', 'InterlockedExchange(&g_swReadAt, 0);'):
        if want not in run: problems.append('TruMenu.cpp: RunPi must hold %s' % want)
    why = fn_body(src, 'const char *PiWhy(')
    for t in re.findall(r'"((?:[^"\\]|\\.)*)"', why):
        if len(t) > 60: problems.append('TruMenu.cpp: PiWhy text over 60 characters: %s' % t)
    if 'if (!_stricmp(id, "power.infinite")) return PiWhy();' not in fn_body(src, 'const char *RadialWhy('):
        problems.append('TruMenu.cpp: RadialWhy must grey power.infinite with PiWhy')
    rescue = src[src.find('const QbRow kQbRescue[] = {'):]
    rescue = rescue[:rescue.find('\n};')]
    a, b = rescue.find('"rc_cheats", kQbGroup'), rescue.find('"rc_game", kQbGroup')
    row = rescue.find('"power.infinite", "", kQbBool')
    if not (0 <= a < row < b): problems.append('TruMenu.cpp: row power.infinite (bool) must sit in group Cheats of Rettung')
    sw = open(switches_path, encoding='utf-8').read()
    if not re.search(r'^TruShadowPower \| Meter \| Infinite \| bool \|', sw, re.M):
        problems.append('TruMenu.switches.txt: the TruShadowPower [Meter] Infinite row is missing')
    tsp = open(os.path.join(PLUGINS, 'TruShadowPower', 'TruShadowPower.cpp'), encoding='utf-8').read()
    # 0.22.21: 0.23 or later (TruShadowPower 0.24 of 4222070); 0.22.33: a patch number may follow (0.27.1, group I)
    vm = re.search(r'return "TruShadowPower 0\.(\d+)(?:\.\d+)? \(', tsp)
    if not vm or int(vm.group(1)) < 23 or 'GetPrivateProfileIntA("Meter", "Infinite"' not in tsp:
        problems.append('TruShadowPower.cpp: version export 0.23+ / [Meter] Infinite read not found (kPiMinVersion 23)')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if '1e466d0709564db15ef8b7cf0b1d97dac49c8ef98cb043617a608f7ad2d5cd3c' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.18 build hash (work\\asi\\menu0241) is missing')
    return problems, '%d menu pages, 17 bar page names, power.infinite row / item / greying' % len(mp)


def check_02220(ini_path):
    """0.22.20: menu.noattract ([Menu] NoAttract, default 0): the AttractTimer clock (generalbank script 60 member 4) taken
    at the clock f11 native, held at elapsed 0 through the clock update slot 0x84584c while on; bar row in
    Spiel-Einstellungen / Hauptmenue, item, help, greying, persistence, 13 byte checks = precheck_02220 rows"""
    problems = []
    src = read_cpp()
    if '"0.22.20 (main menu attract video off' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.21: later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.20 part "0.22.20 (main menu attract video off"')
    ini = open(ini_path, encoding='utf-8').read()
    if not re.search(r'\{"Menu", "NoAttract", "0",', src):
        problems.append('TruMenu.cpp: kOpts [Menu] NoAttract default must be "0"')
    block = re.search(r'^\[Menu\]\r?\n(.*?)(?=^\[|\Z)', ini, re.M | re.S)
    if not block or not re.search(r'^NoAttract=0\r?$', block.group(1), re.M):
        problems.append('TruMenu.ini: [Menu] NoAttract=0 missing')
    if 'InterlockedExchange(&g_naWant, OptInt(ini, "Menu", "NoAttract") != 0 ? 1 : 0);' not in fn_body(src, 'void ReadOptions('):
        problems.append('TruMenu.cpp: ReadOptions must read [Menu] NoAttract into g_naWant')
    # item: bool, explicit value, no argument = report (never a flip), written at once
    if not re.search(r'\{"menu\.noattract", "bool", "', src): problems.append('TruMenu.cpp: item menu.noattract missing')
    run = fn_body(src, 'bool RunNa(')
    for want in ('if (!arg || !arg[0]) { ValNa(o, n); return true; }', 'IniKeep("Menu", "NoAttract", on ? "1" : "0");',
                 'usage: menu.noattract 1|0'):
        if want not in run: problems.append('TruMenu.cpp: RunNa must hold %s' % want)
    if 'BoolArg(' in run: problems.append('TruMenu.cpp: RunNa must not use BoolArg (an empty argument would flip)')
    # mechanism: capture at the f11 native (passive), hold through the update slot only for the captured clock in the
    # front end, the game's code called on in both hooks
    f11 = fn_body(src, 'void __fastcall NaF11(')
    if 'NaCapture(' not in f11 or 'reinterpret_cast<NaClockFn>(kNaF11Body)(slot);' not in f11:
        problems.append('TruMenu.cpp: NaF11 must capture and then call the game\'s f11 body 0x4a34f0')
    cap = fn_body(src, 'void NaCapture(')
    for want in ('if (vt != kNaClockVt)', 'if (!NaFrontEnd())', 'g_naClock = clock;'):
        if want not in cap: problems.append('TruMenu.cpp: NaCapture must hold %s' % want)
    upd = fn_body(src, 'void __fastcall NaUpdate(')
    for want in ('g_naWant && clock == want', 'clock == want && NaFrontEnd()', '*elapsed = 0.0f;',   # 0.22.21 form
                 'reinterpret_cast<NaUpdFn>(kNaUpdOrig)(self, edx, dt);'):
        if want not in upd: problems.append('TruMenu.cpp: NaUpdate must hold %s' % want)
    if upd.find('reinterpret_cast<NaUpdFn>(kNaUpdOrig)') < upd.find('*elapsed = 0.0f;'):
        problems.append('TruMenu.cpp: NaUpdate must reset before the game\'s update runs')
    fe = fn_body(src, 'bool NaFrontEnd(')
    if '(state == 6 || state == 10)' not in fe: problems.append('TruMenu.cpp: NaFrontEnd must test main state 6 / 10')
    for want in ('const DWORD kNaF11Site = 0x00795cc4, kNaF11Body = 0x004a34f0, kNaClockVt = 0x00845860;',
                 'const DWORD kNaUpdSlot = 0x0084584c, kNaUpdOrig = 0x004a3960;',
                 'const BYTE kNaF11Orig[5] = {0xe9, 0x27, 0xd8, 0xd0, 0xff};',
                 'const BYTE kNaUpdSlotOrig[4] = {0x60, 0x39, 0x4a, 0x00};'):
        if want not in src: problems.append('TruMenu.cpp: %s missing' % want)
    tick = fn_body(src, 'void NaTick(')
    for want in ('LcPatch(kNaF11Site, kNaF11Orig, g_naF11Patch, 5, true)', 'LcPatch(kNaUpdSlot, kNaUpdSlotOrig, g_naUpdPatch, 4, true)',
                 'LcPatch(kNaUpdSlot, kNaUpdSlotOrig, g_naUpdPatch, 4, false)'):
        if want not in tick: problems.append('TruMenu.cpp: NaTick must hold %s' % want)
    if 'NaTick();' not in fn_body(src, 'DWORD WINAPI PadHook(') or 'if (padIdle) NaTick();' not in fn_body(src, 'void Render('):
        problems.append('TruMenu.cpp: NaTick must run in PadHook (every poll) and in Render while no pad poll')
    if 'if (!_stricmp(id, "menu.noattract")) return NaWhy();' not in fn_body(src, 'const char *RadialWhy('):
        problems.append('TruMenu.cpp: RadialWhy must grey menu.noattract with NaWhy')
    for t in re.findall(r'"((?:[^"\\]|\\.)*)"', fn_body(src, 'const char *NaWhy(')):
        if len(t) > 60: problems.append('TruMenu.cpp: NaWhy text over 60 characters: %s' % t)
    # 13 byte checks = the rows of precheck_02220 section 9
    m = re.search(r'const DvCheck kNaChecks\[\] = \{(.*?)\n\};', src, re.S)
    rows = re.findall(r'\{0x([0-9a-f]{8}), "([0-9a-f ]+)"\}', m.group(1)) if m else []
    if len(rows) != 13: problems.append('TruMenu.cpp: kNaChecks must hold 13 rows, %d' % len(rows))
    pre = os.path.join(ROOT, 'work', 'asi', 'menu0243', 'precheck_02220.txt')
    if os.path.exists(pre):
        lines = [l.split(None, 1) for l in open(pre, encoding='utf-8').read().splitlines() if l.strip() and not l.startswith('#')]
        if len(lines) != 45: problems.append('precheck_02220.txt: 45 rows expected, %d' % len(lines))
        have = {(a.lower(), b.replace(' ', '').lower()) for a, b in lines}
        for a, b in rows:
            if (a, b.replace(' ', '')) not in have: problems.append('precheck_02220.txt: row 0x%s missing' % a)
    # bar row: own group "Hauptmenue" in Spiel-Einstellungen, before "TruMenu selbst"; help line within 60 characters
    tables = src[src.find('const QbRow kQbSettings[] = {'):]
    tables = tables[:tables.find('\n};')]
    g, r, t = (tables.find('"set_main", kQbGroup'), tables.find('"menu.noattract", "", kQbBool'),
               tables.find('"set_tm", kQbGroup'))
    if not (0 <= g < r < t): problems.append('TruMenu.cpp: row menu.noattract (bool) must sit in group set_main of kQbSettings')
    if 'Main menu attract video off' not in tables or 'Hauptmenue-Video aus' not in tables:   # read_cpp: umlauts as ue
        problems.append('TruMenu.cpp: bar row texts "Hauptmenue-Video aus" / "Main menu attract video off" missing')
    hm = re.search(r'\{"menu\.noattract", "", "((?:[^"\\]|\\.)*)"\s*"((?:[^"\\]|\\.)*)"\}', src)
    if not hm: problems.append('TruMenu.cpp: kQbHelp row menu.noattract missing')
    else:
        de, en = unescape(hm.group(1) + hm.group(2)).split('|')
        if len(de) > 60 or len(en) > 60: problems.append('TruMenu.cpp: menu.noattract help over 60 characters')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if '1121ff2ac48ec544401d5fbbc51be70697c8b450cbeda9de0b96fc35d289601c' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.19 build hash (work\\asi\\menu0242) is missing')
    return problems, 'menu.noattract: [Menu] NoAttract=0, item / row / help / greying, capture + hold, %d byte checks' % len(rows)


def check_02221(ini_path):
    """0.22.21: menu.attracttimer ([Menu] AttractTimerShow, default 0; [Menu] AttractTimerPosition, default tr): the teaser
    timer line in the front end - read only through the 0.22.20 update slot (NaUpdate writes only in the hold branch,
    NtPre / NtPost only read), a shadow count with a flash + log line per alarm; bar row next to "Hauptmenue-Video aus",
    item, help, greying, persistence; no new byte checks (precheck_02221 = the 45 rows of precheck_02220)"""
    problems = []
    src = read_cpp()
    if '"0.22.21 (teaser timer: menu.attracttimer' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.22: later
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.21 part "0.22.21 (teaser timer: menu.attracttimer"')
    ini = open(ini_path, encoding='utf-8').read()
    block = re.search(r'^\[Menu\]\r?\n(.*?)(?=^\[|\Z)', ini, re.M | re.S)
    for key, val in (('AttractTimerShow', '0'), ('AttractTimerPosition', 'tr')):
        if not re.search(r'\{"Menu", "%s", "%s",' % (key, val), src):
            problems.append('TruMenu.cpp: kOpts [Menu] %s default must be "%s"' % (key, val))
        if not block or not re.search(r'^%s=%s\r?$' % (key, val), block.group(1), re.M):
            problems.append('TruMenu.ini: [Menu] %s=%s missing' % (key, val))
    ro = fn_body(src, 'void ReadOptions(')
    if 'InterlockedExchange(&g_ntWant, OptInt(ini, "Menu", "AttractTimerShow") != 0 ? 1 : 0);' not in ro:
        problems.append('TruMenu.cpp: ReadOptions must read [Menu] AttractTimerShow into g_ntWant')
    if 'OptString(ini, "Menu", "AttractTimerPosition", v, sizeof(v));' not in ro or 'g_ntPos = 2;' not in ro:
        problems.append('TruMenu.cpp: ReadOptions must read [Menu] AttractTimerPosition (default tr = index 2)')
    m = re.search(r'const char \*const kSnPosNames\[4\] = \{([^}]*)\};', src)
    if not m or re.findall(r'"(\w+)"', m.group(1))[2:3] != ['tr']:
        problems.append('TruMenu.cpp: kSnPosNames[2] must be "tr" (the AttractTimerPosition default index)')
    # item: bool, explicit value, no argument = report (never a flip), written at once
    if not re.search(r'\{"menu\.attracttimer", "bool", "', src): problems.append('TruMenu.cpp: item menu.attracttimer missing')
    run = fn_body(src, 'bool RunNt(')
    for want in ('if (!arg || !arg[0]) { ValNt(o, n); return true; }', 'IniKeep("Menu", "AttractTimerShow", on ? "1" : "0");',
                 'usage: menu.attracttimer 1|0'):
        if want not in run: problems.append('TruMenu.cpp: RunNt must hold %s' % want)
    if 'BoolArg(' in run: problems.append('TruMenu.cpp: RunNt must not use BoolArg (an empty argument would flip)')
    # read only: the slot follows hold || line; NaUpdate writes the clock only in the hold branch; NtPre / NtPost read
    tick = fn_body(src, 'void NaTick(')
    if 'want = hold || g_ntWant != 0;' not in tick and 'want = hold || g_ntWant != 0 || g_atWant != 0;' not in tick:
        problems.append('TruMenu.cpp: NaTick must patch the slot for hold || line (0.22.39: || icon)')
    upd = fn_body(src, 'void __fastcall NaUpdate(')
    if upd.count('= 0.0f;') != 2 or upd.count('*elapsed = 0.0f;') != 1:   # `float game = 0.0f;` + the hold's write
        problems.append('TruMenu.cpp: NaUpdate may write the clock only in the hold branch (*elapsed = 0.0f)')
    hb = upd.find('if (g_naWant && clock == want && NaFrontEnd())')
    if hb < 0 or not (hb < upd.find('*elapsed = 0.0f;') < upd.find('held = true;')):
        problems.append('TruMenu.cpp: the write in NaUpdate must sit in the g_naWant hold branch')
    if not (0 <= upd.find('NtPre(clock);') < hb):
        problems.append('TruMenu.cpp: NaUpdate must call NtPre before the hold (the elapsed the game itself had)')
    orig, post = upd.find('reinterpret_cast<NaUpdFn>(kNaUpdOrig)(self, edx, dt);'), upd.find('NtPost(seen, game, st, firedBefore, held, dt);')
    if not (0 <= orig < post): problems.append('TruMenu.cpp: NaUpdate must call NtPost after the game\'s update')
    for name in ('void NtPre(', 'void NtPost('):
        body = fn_body(src, name)
        if not body: problems.append('TruMenu.cpp: %s missing' % name); continue
        if re.search(r'reinterpret_cast<(?:float|DWORD|BYTE) \*>', body):
            problems.append('TruMenu.cpp: %s must only read the clock (const casts)' % name.strip('( '))
    post_b = fn_body(src, 'void NtPost(')
    for want in ('if (running) g_ntShadow = g_ntShadow + dt;', '(g_naRepeat || g_ntPassed == 0)',
                 'if (!flash || !g_ntWant) return;', 'g_ntFlashTick = GetTickCount();', 'Log(1, "menu.attracttimer: '):
        if want not in post_b: problems.append('TruMenu.cpp: NtPost must hold %s' % want)
    if 'bool NtWantsDraw() { return g_ntWant != 0 && NaFrontEnd(); }' not in src:
        problems.append('TruMenu.cpp: NtWantsDraw must be g_ntWant && NaFrontEnd (front end only)')
    rnd = fn_body(src, 'void Render(')
    for want in ('const bool ntDraw = NtWantsDraw();', '!cnBadge && !ntDraw)', 'if (ntDraw) DrawNt();'):
        if want not in rnd: problems.append('TruMenu.cpp: Render must hold %s' % want)
    if 'g_ntFlashTick && now - g_ntFlashTick < 1000' not in fn_body(src, 'void DrawNt(').replace('flashAt', 'g_ntFlashTick'):
        problems.append('TruMenu.cpp: DrawNt must flash 1 s after g_ntFlashTick')
    if 'if (!_stricmp(id, "menu.attracttimer")) return NaWhy();' not in fn_body(src, 'const char *RadialWhy('):
        problems.append('TruMenu.cpp: RadialWhy must grey menu.attracttimer with NaWhy')
    # bar row right after "Hauptmenue-Video aus" in group set_main, before "TruMenu selbst"; help within 60 characters
    tables = src[src.find('const QbRow kQbSettings[] = {'):]
    tables = tables[:tables.find('\n};')]
    g, a, r, t = (tables.find('"set_main", kQbGroup'), tables.find('"menu.noattract", "", kQbBool'),
                  tables.find('"menu.attracttimer", "", kQbBool'), tables.find('"set_tm", kQbGroup'))
    if not (0 <= g < a < r < t):
        problems.append('TruMenu.cpp: row menu.attracttimer (bool) must follow menu.noattract in group set_main of kQbSettings')
    if '"Teaser-Uhr anzeigen", "Show teaser timer", "menu.attracttimer"' not in tables:
        problems.append('TruMenu.cpp: bar row texts "Teaser-Uhr anzeigen" / "Show teaser timer" missing')
    hm = re.search(r'\{"menu\.attracttimer", "", "((?:[^"\\]|\\.)*)"\s*"((?:[^"\\]|\\.)*)"\}', src)
    if not hm: problems.append('TruMenu.cpp: kQbHelp row menu.attracttimer missing')
    else:
        de, en = unescape(hm.group(1) + hm.group(2)).split('|')
        if len(de) > 60 or len(en) > 60: problems.append('TruMenu.cpp: menu.attracttimer help over 60 characters')
    # no new byte checks: precheck_02221 = the 45 rows of precheck_02220
    pre20 = os.path.join(ROOT, 'work', 'asi', 'menu0243', 'precheck_02220.txt')
    pre21 = os.path.join(ROOT, 'work', 'asi', 'menu0244', 'precheck_02221.txt')
    rows = lambda p: sorted(l.split(None, 1)[0].lower() + ' ' + l.split(None, 1)[1].replace(' ', '').lower()
                            for l in open(p, encoding='utf-8').read().splitlines() if l.strip() and not l.startswith('#'))
    if os.path.exists(pre20) and os.path.exists(pre21):
        r20, r21 = rows(pre20), rows(pre21)
        if len(r21) != 45 or r20 != r21: problems.append('precheck_02221.txt: must hold the 45 rows of precheck_02220 (%d)' % len(r21))
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if '8e3d279fde431b57f9417d9954d692476b256c69cc92ac004a241b990aaebc2c' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.20 build hash (work\\asi\\menu0243) is missing')
    return problems, ('menu.attracttimer: [Menu] AttractTimerShow=0 / AttractTimerPosition=tr, item / row / help / '
                      'greying, read-only shadow + flash, front end only, 45 byte checks unchanged')


NT_LITSEQ = r'"(?:[^"\\]|\\.)*"(?:\s*"(?:[^"\\]|\\.)*")*'


def check_02222(ini_path):
    """0.22.22 (live 2026-11-10): the teaser timer line in the bar language (every text a de ? .. : .. pair after
    `const bool de = g_qbLang == 0;`), the game clock (shadow) next to the wall clock since the clock's (re)start, and the
    pause bit marker - [0xe7f188] == 0.5 and [0xe7f0b4] & 0x10000000, read only after the 4 kNtChecks rows (precheck_02222
    = the 45 rows of precheck_02221 + these 4); INI unchanged"""
    problems = []
    src = read_cpp()
    if '"0.22.22 (teaser timer line' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.23: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.22 part "0.22.22 (teaser timer line"')
    draw = fn_body(src, 'void DrawNt(')
    if not draw.split('\n')[2:3] == ['    const bool de = g_qbLang == 0;']:
        problems.append('TruMenu.cpp: DrawNt must start with const bool de = g_qbLang == 0; (the bar language)')
    # bilingual: with every de ? A : B pair taken out, no literal with words is left (only formats / the window id)
    rest = re.sub(r'de\s*\?\s*' + NT_LITSEQ + r'\s*:\s*' + NT_LITSEQ, '', draw)
    left = [unescape(x) for x in re.findall(r'"((?:[^"\\]|\\.)*)"', rest)]
    single = [t for t in left if re.search(r'[A-Za-z]{2}', t.replace('%ld', '').replace('%s', '')) and
              t != '##TruAttractTimer']
    if single: problems.append('TruMenu.cpp: DrawNt texts without a de / en pair: %s' % ', '.join(single))
    for want in ('Spieluhr %.1f s / Wanduhr %.1f s seit Start', 'game clock %.1f s / wall clock %.1f s "\n            "since start',
                 '"Pause-Bit aktiv (halbe Zeit)" : "Pause bit set (half time)"', 'NtWallSeconds()',
                 'const int half = NtPauseHalf(&frame, &gameFlags);', 'if (half > 0) Out(l4,',
                 'flashAt && now - flashAt < 1000'):
        if want not in draw: problems.append('TruMenu.cpp: DrawNt must hold %s' % want.replace('\n', ' '))
    wall = fn_body(src, 'double NtWallSeconds(')
    if 'const DWORD at = g_ntResetTick;' not in wall or 'GetTickCount() - at' not in wall:
        problems.append('TruMenu.cpp: NtWallSeconds must count GetTickCount since g_ntResetTick (NtPre\'s (re)start)')
    if 'g_ntResetTick = GetTickCount();' not in fn_body(src, 'void NtPre('):
        problems.append('TruMenu.cpp: NtPre must set g_ntResetTick at the clock\'s (re)start')
    # the marker: both conditions, read only, only after the checks
    if 'const DWORD kNtFrameTime = 0x00e7f188, kNtGameFlags = 0x00e7f0b4, kNtPauseBit = 0x10000000;' not in src:
        problems.append('TruMenu.cpp: kNtFrameTime 0xe7f188 / kNtGameFlags 0xe7f0b4 / kNtPauseBit 0x10000000 missing')
    ph = fn_body(src, 'int NtPauseHalf(')
    for want in ('NtPbCheck();', 'if (!g_ntPbDone) return 0;',
                 'if (!g_ntPbOk || !ReadFloats(kNtFrameTime, frame, 1) || !ReadDword(kNtGameFlags, flags)) return -1;',
                 'return (*flags & kNtPauseBit) && *frame == 0.5f ? 1 : 0;'):
        if want not in ph: problems.append('TruMenu.cpp: NtPauseHalf must hold %s' % want)
    uses = re.findall(r'[^\n]*\bkNt(?:FrameTime|GameFlags)\b[^\n]*', src)
    if len(uses) != 2 or any('const DWORD kNtFrameTime' not in u and 'ReadFloats(kNtFrameTime' not in u for u in uses):
        problems.append('TruMenu.cpp: kNtFrameTime / kNtGameFlags may only be defined and read (ReadFloats / ReadDword)')
    pc = fn_body(src, 'void NtPbCheck(')
    if 'if (InterlockedExchange(&g_ntPbChecked, 1)) return;' not in pc or 'InterlockedExchange(&g_ntPbDone, 1);' not in pc:
        problems.append('TruMenu.cpp: NtPbCheck must run once and mark g_ntPbDone after the result')
    val = fn_body(src, 'void ValNt(')
    for want in ('NtPauseHalf(&frame, &gameFlags)', 'wall %.1f s since the (re)start', 'frame time %.3f'):
        if want not in val: problems.append('TruMenu.cpp: ValNt must hold %s' % want)
    # 4 byte checks = the rows of section 10 of precheck_02222; precheck_02222 = precheck_02221 + these 4
    m = re.search(r'const DvCheck kNtChecks\[\] = \{(.*?)\n\};', src, re.S)
    rows = [(a, b.replace(' ', '')) for a, b in re.findall(r'\{0x([0-9a-f]{8}), "([0-9a-f ]+)"\}', m.group(1))] if m else []
    want_rows = [('005da233', 'f705b4f0e70000000010'), ('005da664', 'd905a8138400c70584f3e70001000000d91d88f1e700'),
                 ('008413a8', '0000003f'), ('0047b036', 'd90588f1e700dc0db03c8400')]
    if rows != want_rows: problems.append('TruMenu.cpp: kNtChecks must be the 4 rows 0x5da233 / 0x5da664 / 0x8413a8 / 0x47b036')
    pre21 = os.path.join(ROOT, 'work', 'asi', 'menu0244', 'precheck_02221.txt')
    pre22 = os.path.join(ROOT, 'work', 'asi', 'menu0245', 'precheck_02222.txt')
    prows = lambda p: sorted(l.split(None, 1)[0].lower() + ' ' + l.split(None, 1)[1].replace(' ', '').lower()
                             for l in open(p, encoding='utf-8').read().splitlines() if l.strip() and not l.startswith('#'))
    if os.path.exists(pre21) and os.path.exists(pre22):
        r21, r22 = prows(pre21), prows(pre22)
        if len(r22) != 49 or sorted(r21 + ['%s %s' % r for r in want_rows]) != r22:
            problems.append('precheck_02222.txt: must hold the 45 rows of precheck_02221 + the 4 kNtChecks rows (%d)' % len(r22))
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if '362f51e23edff6116e183ff7c5212b3d120981a558bf99a47a5fde015755af67' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.21 build hash (work\\asi\\menu0244) is missing')
    return problems, ('teaser timer line in the bar language, game clock / wall clock, pause bit marker (0.5 + bit), '
                      '%d byte checks read only, precheck_02222 = 45 + 4 rows' % len(rows))


def switch_groups(path):
    """0.22.23: [(group key, switch lines)] of a switches file in file order (comments / blank lines skipped)"""
    out = []
    for line in open(path, encoding='utf-8').read().splitlines()[1:]:
        s = line.strip()
        if not s or s.startswith('#'): continue
        f = [x.strip() for x in s.split('|')]
        if f[0] == 'group': out.append([f[1] if len(f) > 1 else '?', 0])
        elif out: out[-1][1] += 1
    return out


def check_02223(switches_path):
    """0.22.23 (Q39, switches file limit): kSwMax 512 (was 160) = SW_MAX, the tables sized by it, file lines over the
    limits named in TruMenu.log (one line per kind with count and first line number, no silent "too many" skip), rows
    below a group over the limit not given to the previous group, g_swState / the page Fixes head say so, the page
    model of the file (group rows + the largest group <= kQbViewMax), the file header names 512, no new byte checks
    (precheck_02223 = the 49 rows of precheck_02222), Set-TruMenu.ps1 knows the 0.22.22 hash; INI unchanged"""
    problems = []
    src = read_cpp()
    if '"0.22.23 (switches file limit' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.24: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.23 part "0.22.23 (switches file limit"')
    if 'const int kQbViewMax = %d;' % QB_VIEW_MAX not in src:
        problems.append('TruMenu.cpp: kQbViewMax differs from this tool (%d)' % QB_VIEW_MAX)
    for want in ('SwRow g_sw[kSwMax];', 'SwGroup g_swGroup[kSwGroupMax];', 'SwValue g_swVal[kSwMax];'):
        if want not in src: problems.append('TruMenu.cpp: %s missing (the switch tables are sized by the limits)' % want)
    if re.search(r'\b(g_sw|g_swVal)\[\s*\d+\s*\]', src):
        problems.append('TruMenu.cpp: a switch table with a number instead of kSwMax')
    load = fn_body(src, 'void SwLoadLocked(')
    for want in ('g_swN = g_swGroupN = g_swOver = 0;', 'else if (g_swGroupN >= kSwGroupMax) {',
                 'if (!overGroups++) overGroupAt = number;', 'groupDropped = true;', 'groupDropped = false;',
                 'else if (groupDropped) {', '++overGroupRows;', 'else if (g_swN >= kSwMax) {',
                 'if (!overRows++) overRowAt = number;', 'exceeds the limit of %d groups',
                 'exceeds the limit of %d switch lines', 'kSwMax, overRows, overRowAt',
                 'kSwGroupMax, overGroups, overGroupAt, overGroupRows', 'g_swOver = overRows + overGroups + overGroupRows;',
                 'lines over the limit not shown (log)'):
        if want not in load: problems.append('TruMenu.cpp: SwLoadLocked must hold %s' % want)
    if 'too many switch lines' in load or 'too many groups' in load:
        problems.append('TruMenu.cpp: SwLoadLocked still skips lines over the limit in the 5-line skip log only')
    rows = fn_body(src, 'int QbSwRows(')
    for want in ('want += 1 + (g_swGroup[g].open ? g_swGroup[g].count : 0);', 'if (g_swN && (want > n || g_swOver))',
                 'rows not shown (page max %d, the menu shows all)', 'want - n, max', 'file over the limit (log)'):
        if want not in rows: problems.append('TruMenu.cpp: QbSwRows must hold %s' % want)
    # the page model of the file: one group open at a time, so the largest page = every group row + the largest group
    groups = switch_groups(switches_path)
    name = os.path.basename(switches_path)
    biggest = max(groups, key=lambda g: g[1]) if groups else ['-', 0]
    page = len(groups) + biggest[1]
    if page > QB_VIEW_MAX:
        problems.append('%s: group %s open = %d rows on page Fixes > kQbViewMax %d (split the group)' %
                        (name, biggest[0], page, QB_VIEW_MAX))
    total = sum(g[1] for g in groups)
    head = open(switches_path, encoding='utf-8').read()[:4000]
    if 'At most %d switch lines and %d groups' % (SW_MAX, SW_GROUP_MAX) not in head:
        problems.append('%s: the header must name the limits (At most %d switch lines and %d groups)' % (name, SW_MAX,
                                                                                                      SW_GROUP_MAX))
    pre22 = os.path.join(ROOT, 'work', 'asi', 'menu0245', 'precheck_02222.txt')
    pre23 = os.path.join(ROOT, 'work', 'asi', 'menu0246', 'precheck_02223.txt')
    prows = lambda p: sorted(l.split(None, 1)[0].lower() + ' ' + l.split(None, 1)[1].replace(' ', '').lower()
                             for l in open(p, encoding='utf-8').read().splitlines() if l.strip() and not l.startswith('#'))
    if os.path.exists(pre22) and os.path.exists(pre23) and (len(prows(pre23)) != 49 or prows(pre22) != prows(pre23)):
        problems.append('precheck_02223.txt: must be the 49 rows of precheck_02222 (no new byte checks)')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if 'cddddc1bb118000f06c60b6e41f089338305e5fbcb9894c1f4468001e06867ea' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.22 build hash (work\\asi\\menu0245) is missing')
    return problems, ('switches limit %d / %d groups (file %d rows in %d groups, %d free), lines over it logged, page '
                      'Fixes at most %d rows (group %s open) <= %d, no new byte checks' %
                      (SW_MAX, SW_GROUP_MAX, total, len(groups), SW_MAX - total, page, biggest[0], QB_VIEW_MAX))


FW_ROWS = [('00787910', '8b570c0fbfc18b2c8285ed8b9e10050000'),
           ('007859d0', '8b5e1833ed66396e0c7649eb038d49008b44241885c00fb733')]
CT_ROW = ('00768c50', 'a158dbfa00568bb0100f0000578bb8140f00008bcee8f6f10100')


def check_02224(ini_path, switches_path):
    """0.22.24 (Q36, the Q19 fall out of the world in hall02): fall watch lines at LogLevel 1 (records 742 / 743 / 1068 /
    1080, states 1008 / 1015, watchdog in 1068, safe-ground additions, one rate limit) and [Rescue] FallNet (default 0,
    live, re-read by FnReadSwitch): the net acts only after 3 s in 1068 and 3000 units below the newest safe-ground
    sample before the fall, through UnstuckPlace (player.unstuck's teleport), after the pause test, at most 3 times per
    fall; 2 byte checks kFwChecks + kCtChecks before any read (precheck_02224 = the 49 rows of precheck_02223 + the
    kCtChecks row + these 2); the TruMenu switch row; Set-TruMenu.ps1 knows the 0.22.23 hash"""
    problems = []
    src = read_cpp()
    if '0.22.24 (fall watch + fall net' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.25: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.24 part "0.22.24 (fall watch + fall net"')
    m = re.search(r'const DvCheck kFwChecks\[\] = \{(.*?)\n\};', src, re.S)
    rows = [(a, b.replace(' ', '')) for a, b in re.findall(r'\{0x([0-9a-f]{8}), "([0-9a-f ]+)"\}', m.group(1))] if m else []
    if rows != FW_ROWS: problems.append('TruMenu.cpp: kFwChecks must be the 2 rows 0x787910 / 0x7859d0')
    m = re.search(r'const DvCheck kCtChecks\[\] = \{(.*?)\n\};', src, re.S)
    ct = [(a, b.replace(' ', '')) for a, b in re.findall(r'\{0x([0-9a-f]{8}), "([0-9a-f ]+)"\}', m.group(1))] if m else []
    if ct != [CT_ROW]: problems.append('TruMenu.cpp: kCtChecks must stay the one row 0x768c50')
    chk = fn_body(src, 'bool FwCheck(')
    for want in ('const bool ct = CtCheck();', 'g_fwOk = ct && DvChecks(kFwChecks,'):
        if want not in chk: problems.append('TruMenu.cpp: FwCheck must hold %s' % want)
    watch = fn_body(src, 'void FallWatchTick(')
    for want in ('if ((g_logLevel < 1 && !g_fnOn) || !FwCheck())', 'if (now - g_fnReadTick >= 1000) { g_fnReadTick = now; FnReadSwitch(); }',
                 'if (dt > kFwFrameCapMs) dt = kFwFrameCapMs;', 'ReadDword(machine + 0x510, &rec)',
                 'g_fwIdx = CtRecordIndex(machine, rec);', '(FwWatched(oldIdx) || FwWatched(g_fwIdx) || changed) && FwLineOk(',
                 'g_fwNextWatchMs += g_fwNextWatchMs < 30000 ? 1000 : 10000;', 'FallNetTick(player, p, unit);'):
        if want not in watch: problems.append('TruMenu.cpp: FallWatchTick must hold %s' % want)
    if watch.find('FwCheck()') > watch.find('ReadDword(0x00fadb58'):
        problems.append('TruMenu.cpp: FallWatchTick reads the chart machine before FwCheck')
    tick = src[src.find('        SafeGroundTick();'):][:300]   # the per-frame block of PadHook
    if 'FallWatchTick();' not in tick: problems.append('TruMenu.cpp: FallWatchTick must run right after SafeGroundTick')
    net = fn_body(src, 'void FallNetTick(')
    order = ['if (g_fwInMs <= kFnAfterMs) return;', 'if (g_fnRescues >= kFnMaxRescues) {',
             'if (!FwNewestSafe(unit, g_fwInTick, g_fnUsedTick, &s)) {', 'if (!(below > kFnBelow)) return;',
             'const char *why = FnPauseReason();', 'if (!g_fnOn) {', 'UnstuckPlace(player, s.p, s.yaw, &yawOk);']
    at = [net.find(x) for x in order]
    if any(a < 0 for a in at) or at != sorted(at):
        problems.append('TruMenu.cpp: FallNetTick must test time, count, sample, height, pause, switch - then place')
    if 'SetPosition(' in net or 'SetYaw(' in net:
        problems.append('TruMenu.cpp: FallNetTick must teleport only through UnstuckPlace')
    for name, want in (('kFnAfterMs', '3000'), ('kFnAgainMs', '1000'), ('kFnBelow', '3000.0f'), ('kFnMaxRescues', '3'),
                       ('kFwMaxLines', '40'), ('kFwWindowMs', '10000'), ('kFwSafeLogMs', '2000'), ('kFwFrameCapMs', '100')):
        if not re.search(r'\b%s = %s[,;]' % (name, re.escape(want)), src):
            problems.append('TruMenu.cpp: %s must be %s' % (name, want))
    if 'const int kFwRecords[] = {742, 743, 1068, 1080};' not in src or 'const WORD kFwStateA = 1008, kFwStateB = 1015;' not in src:
        problems.append('TruMenu.cpp: kFwRecords 742 / 743 / 1068 / 1080 and states 1008 / 1015 missing')
    unstuck = fn_body(src, 'bool RunUnstuck(')
    if 'UnstuckPlace(player, to, yaw, &yawOk)' not in unstuck or 'SetPosition(' in unstuck:
        problems.append('TruMenu.cpp: RunUnstuck must teleport through UnstuckPlace (the one path of the fall net)')
    pause = fn_body(src, 'const char *FnPauseReason(')
    for want in ('if (!g_experimental)', 'SafePauseReason(false)', '!(health > 0.0f)'):
        if want not in pause: problems.append('TruMenu.cpp: FnPauseReason must hold %s' % want)
    safe = fn_body(src, 'const char *SafePauseReason(')
    for want in ('"menu open"', '"ring open"', '"flight on"', '"cinematic"', '"player control off"', 'if (timeScale &&'):
        if want not in safe: problems.append('TruMenu.cpp: SafePauseReason must hold %s' % want)
    rd = fn_body(src, 'void FnReadSwitch(')
    if 'GetPrivateProfileIntA("Rescue", "FallNet"' not in rd:
        problems.append('TruMenu.cpp: FnReadSwitch must read [Rescue] FallNet')
    if 'InterlockedExchange(&g_fnOn, OptInt(ini, "Rescue", "FallNet") != 0 ? 1 : 0);' not in fn_body(src, 'void ReadOptions('):
        problems.append('TruMenu.cpp: ReadOptions must read [Rescue] FallNet')
    if 'if (add) FwSafeAdded(added, count);' not in fn_body(src, 'void SafeGroundTick('):
        problems.append('TruMenu.cpp: SafeGroundTick must hand each ring addition to FwSafeAdded (outside the lock)')
    ini = open(ini_path, encoding='utf-8').read()
    if not re.search(r'\n\[Rescue\]\n(;[^\n]*\n)+FallNet=0\n', ini.replace('\r\n', '\n')):
        problems.append('%s: [Rescue] FallNet=0 missing' % os.path.basename(ini_path))
    sw = [l for l in open(switches_path, encoding='utf-8').read().splitlines() if l.startswith('TruMenu | Rescue | FallNet ')]
    # 0.22.27 (Q79): TruMenu has a second row ([Log] Save, check_02227) - here only the FallNet row counts
    if len(sw) != 1 or not sw[0].startswith('TruMenu | Rescue | FallNet | bool | ') or ' | live | 0 | ' not in sw[0]:
        problems.append('%s: one row TruMenu | Rescue | FallNet | bool | ... | live | 0 | ... wanted' %
                        os.path.basename(switches_path))
    pre23 = os.path.join(ROOT, 'work', 'asi', 'menu0246', 'precheck_02223.txt')
    pre24 = os.path.join(ROOT, 'work', 'asi', 'menu0247', 'precheck_02224.txt')
    prows = lambda p: sorted(l.split(None, 1)[0].lower() + ' ' + l.split(None, 1)[1].replace(' ', '').lower()
                             for l in open(p, encoding='utf-8').read().splitlines() if l.strip() and not l.startswith('#'))
    if os.path.exists(pre23) and os.path.exists(pre24):
        r23, r24 = prows(pre23), prows(pre24)
        if len(r24) != 52 or sorted(r23 + ['%s %s' % r for r in [CT_ROW] + FW_ROWS]) != r24:
            problems.append('precheck_02224.txt: must hold the 49 rows of precheck_02223 + kCtChecks + the 2 kFwChecks '
                            'rows (%d)' % len(r24))
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if 'ad52175615e9cded7b3a0c08a51566618d71e8751b30a62293ad26ab4b221b2f' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.23 build hash (work\\asi\\menu0246) is missing')
    return problems, ('fall watch (records %s, states 1008 / 1015, watchdog, safe ground, 40 lines / 10 s), [Rescue] '
                      'FallNet default 0 live, net after 3 s / 3000 units through UnstuckPlace, %d + 1 byte checks, '
                      'switch row' % ('/'.join(['742', '743', '1068', '1080']), len(rows)))


def c_size(src, text):
    """the size of a C array declaration size text ('512', 'kQbRecentCap * 112', 'sizeof(g_qbClosed)'); None = unknown"""
    total = 1
    for part in text.split('*'):
        part = part.strip()
        m = re.fullmatch(r'sizeof\((\w+)\)', part)
        if m:
            d = re.search(r'\bchar %s\[([^\]]+)\]' % m.group(1), src)
            value = c_size(src, d.group(1)) if d else None
        elif re.fullmatch(r'\d+', part):
            value = int(part)
        else:
            d = re.search(r'\bconst (?:int|size_t) %s = (\d+);' % re.escape(part), src)
            value = int(d.group(1)) if d else None
        if value is None: return None
        total *= value
    return total


def c_array(src, body, name):
    """size of 'char <name>[N]' in body (the first one), None when there is none"""
    m = re.search(r'\bchar %s\[([^\]]+)\]' % re.escape(name), body)
    return c_size(src, m.group(1)) if m else None


def table_texts(src):
    """0.22.25 (Q45): the worst-case lengths of TruMenu texts built from its own tables (no NUL)"""
    def block(head):
        b = src[src.index(head):] if head in src else ''
        return b[:b.find('};')]
    header, rows = table(src)
    out = {'ini': len(text(header, rows).encode('utf-8')), 'keys': len(rows),
           'comment': max(len(c) for _, _, _, c in rows),
           'settings': len('; '.join('[%s] %s=%s (default)' % (s, k, d) for s, k, d, _ in rows))}
    cheats = re.findall(r'\{"([a-z0-9_.]+)", kCat[A-Za-z]+', block('const CheatRow kCheatRows[] = {'))
    out['cheats'] = (len(','.join(cheats)), len(cheats))
    nav = re.findall(r'^\s*\{"([a-z0-9_]+)", 0x', block('const NavSwitch kNavSwitches[] = {'), re.M)
    out['nav'] = (len(','.join(nav)), len(nav))
    pages = LIT.findall(block('const char *const kMpPages[] = {'))
    out['pages'] = (len(','.join(pages)), len(pages))
    starts = LIT.findall(block('const char *const kQbStartClosed[] = {'))
    groups = []
    for g in re.findall(r'"-", "([a-z0-9_]+)", kQbGroup', src) + ['fig_shadow', 'fig_combat']:
        if g not in groups: groups.append(g)
    out['closed'] = (len(','.join(('+' + g) if g in starts else g for g in groups)), len(groups))
    return out


def check_02225():
    """0.22.25 (Q45, agent finding during Q36): settings.reset built the default TruMenu.ini in a static 16384-byte buffer
    while the text is ~42 KB - it wrote a truncated INI. Now: no fixed buffer for the default text (measured with
    DefaultIniText(nullptr, 0), built in a malloc of that size before the backup, cut / write / close checked); every
    fixed char array left in RunSettingsReset / DefaultIniText must be larger than the text (this rule would have caught
    16384 < 42 KB). The other texts built from TruMenu's tables against their buffers: Log line (light.cut lines of 1400),
    [Quick] Closed with every group key toggled, [Menu] OpenPages with every page, [Cheats] State with every cheat,
    [Debug] NavDraw with every switch, settings.show at the defaults in t_value, [Quick] Recent at its field limits;
    QbGroupSet / CpPersist append whole keys only (TextAdd); Set-TruMenu.ps1 knows the 0.22.24 hash"""
    problems = []
    src = read_cpp()
    if '0.22.25 (settings.reset writes the whole TruMenu.ini' not in src[:src.find('\n', src.find('kVersion = '))]:
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.25 part "0.22.25 (settings.reset writes the whole '
                        'TruMenu.ini"')   # 0.22.26: a later part
    t = table_texts(src)
    reset, dtext = fn_body(src, 'bool RunSettingsReset('), fn_body(src, 'size_t DefaultIniText(')
    if not reset or not dtext: problems.append('TruMenu.cpp: RunSettingsReset / DefaultIniText missing')
    for where, body in (('RunSettingsReset', reset), ('DefaultIniText', dtext)):
        for name, size in re.findall(r'\bchar (\w+)\[([^\]]+)\]', body):
            n = c_size(src, size)
            if name == 'backup' and where == 'RunSettingsReset': continue      # the backup path (MAX_PATH)
            if name == 'comment' and n is not None and n > t['comment']: continue
            if n is None or n <= t['ini']:
                problems.append('TruMenu.cpp: %s holds char %s[%s] - the default text is %d bytes (settings.reset would '
                                'write a cut TruMenu.ini)' % (where, name, size, t['ini']))
    for want in ('const size_t len = DefaultIniText(nullptr, 0);', 'malloc(len + 1)',
                 'DefaultIniText(text, len + 1, &cut)', 'if (cut || built != len || strlen(text) != len)',
                 'fwrite(text, 1, len, f)', 'if (wrote != len || !closed)'):
        if want not in reset: problems.append('TruMenu.cpp: RunSettingsReset must hold %s' % want)
    if not (0 <= reset.find('DefaultIniText(text') < reset.find('CopyFileA(') < reset.find('fopen_s(')):
        problems.append('TruMenu.cpp: RunSettingsReset must build the text before the backup and the write')
    put = fn_body(src, 'void IniPut(')
    if '_vscprintf(fmt, ap)' not in put or not put.endswith('\n    t.used += static_cast<size_t>(w);\n}') or \
            'if (t.out) {' not in put:   # counted on the function level: also when measuring / not written
        problems.append('TruMenu.cpp: IniPut must measure every piece (_vscprintf) and count it also when not writing')
    if 'IniPut(' not in dtext or '_snprintf_s' in dtext or 'strtok_s' in dtext:
        problems.append('TruMenu.cpp: DefaultIniText must build through IniPut (no _snprintf_s / strtok_s copy)')
    add = fn_body(src, 'bool TextAdd(')
    if '_vscprintf(fmt, ap)' not in add or 'return false;' not in add:
        problems.append('TruMenu.cpp: TextAdd must measure the piece and refuse it whole')
    # the other table texts
    line = c_array(src, fn_body(src, 'void Log('), 'line')
    lc = c_array(src, fn_body(src, 'void LcLogFrame('), 'text')
    if line is None or line < 2048 or (lc is not None and lc + 13 >= line):
        problems.append('TruMenu.cpp: Log line must hold 2048 and the light.cut text + time stamp (line %s, text %s)'
                        % (line, lc))
    sizes = {name: c_size(src, m) for name, m in re.findall(r'^(?:extern )?char (g_qbClosed|g_mpOpen|g_cheatState|'
                                                            r'g_navAuto)\[([^\]]+)\]', src, re.M)}
    decl = re.findall(r'^(?:extern )?char g_qbClosed\[([^\]]+)\]', src, re.M)
    if len(set(decl)) != 1: problems.append('TruMenu.cpp: g_qbClosed extern and definition differ (%s)' % decl)
    for key, buf, what in (('closed', 'g_qbClosed', '[Quick] Closed, every group key toggled'),
                           ('pages', 'g_mpOpen', '[Menu] OpenPages, every page open'),
                           ('cheats', 'g_cheatState', '[Cheats] State, every cheat on'),
                           ('nav', 'g_navAuto', '[Debug] NavDraw, every switch on')):
        need, count = t[key]
        if sizes.get(buf) is None or need >= sizes[buf]:
            problems.append('TruMenu.cpp: %s %s too small: %s needs %d + 1 (%d entries)' % (buf, sizes.get(buf), what,
                                                                                          need, count))
    for fn, name, key in (('void CheatPersistSave(', 'list', 'cheats'), ('void DvPersistNav(', 'list', 'nav'),
                          ('void MpLogKeys(', 'keys', 'pages')):
        n = c_array(src, fn_body(src, fn), name)
        if n is None or t[key][0] >= n:
            problems.append('TruMenu.cpp: %s char %s[%s] too small for %d + 1' % (fn[5:-1], name, n, t[key][0]))
    grp = fn_body(src, 'bool QbGroupSet(')
    if not grp or 'LabelAdd(' in grp or grp.count('TextAdd(') != 3 or 'return false;' not in grp:
        problems.append('TruMenu.cpp: QbGroupSet must append whole keys (TextAdd) and refuse a list that does not fit')
    if src.count('if (!QbGroupSet(') != 2:
        problems.append('TruMenu.cpp: both QbGroupSet callers must handle a refused list')
    cp = fn_body(src, 'void CpPersist(')
    hide = c_array(src, fn_body(src, 'void ReadOptions('), 'hide')
    if 'LabelAdd(' in cp or 'TextAdd(' not in cp or c_array(src, cp, 'list') != hide or \
            c_array(src, fn_body(src, 'void CpHideParse('), 'copy') != hide:
        problems.append('TruMenu.cpp: CpPersist must write whole ids (TextAdd) into the read size of CheckpointHide')
    vs = fn_body(src, 'void ValSettings(')
    tv = c_size(src, (re.search(r'char t_value\[([^\]]+)\]', src) or re.search('(x)', 'x')).group(1))
    if '_snprintf_s(o + used' in vs or 'TextAdd(o, n - kMoreRoom, &used' not in vs or 'more keys' not in vs:
        problems.append('TruMenu.cpp: ValSettings must add whole keys and name the keys it could not hold')
    if tv is None or t['settings'] + 120 >= tv:
        problems.append('TruMenu.cpp: t_value %s too small for settings.show at the defaults (%d)' % (tv, t['settings']))
    rec = c_array(src, fn_body(src, 'void QbRecentSave('), 'text')
    m = re.search(r'struct QbRecent \{ char id\[(\d+)\], arg\[(\d+)\]; \};', src)
    cap = c_size(src, 'kQbRecentCap')
    if not m or rec is None or cap is None or cap * (int(m.group(1)) - 1 + int(m.group(2)) - 1 + 2) - 1 >= rec:
        problems.append('TruMenu.cpp: QbRecentSave text too small for kQbRecentCap full entries')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if 'd792fca9fc969130ac3db5ae98263062af55f47b6933545fe17e929376a57ba9' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.24 build hash (work\\asi\\menu0247) is missing')
    return problems, ('settings.reset: default text %d bytes (%d keys) built in a measured buffer, no fixed array; table '
                      'texts fit: Log line %s (light.cut %s), [Quick] Closed %d of %s, OpenPages %d of %s, Cheats %d of '
                      '%s, NavDraw %d of %s, settings.show %d of %s' % (
                          t['ini'], t['keys'], line, lc, t['closed'][0], sizes.get('g_qbClosed'), t['pages'][0],
                          sizes.get('g_mpOpen'), t['cheats'][0], sizes.get('g_cheatState'), t['nav'][0],
                          sizes.get('g_navAuto'), t['settings'], tv))


ADM_ROWS = [('005d4859', 'a158dbfa008b8804050000'),
            ('006e6630', 'a164d7fa00d980d00200008b81fc0100008bd0d9593c'),
            ('006e664e', '0d000040008981fc010000c605afe8fa0001c605d8e8fa0000c3'),
            ('00777a50', 'a158dbfa008b8804050000e9d0ebf6ff'),
            ('006f28c0', 'c605afe8fa0001f781fc010000000040007537d9413cd8442404d9593c'),
            ('006f2930', '8b91fc010000d9ee83ec08f7c200004000756fd8513c')]
ARENA_ROWS = [('arena.go', '1a'), ('arena.go', '1b'), ('arena.go', '1c')]   # arena 1 "Kampf" (arena 2 "Museum" later)
ARENA_TABLE = [('1', '1a', 'l7_helheim03', '8785'), ('1', '1b', 'l7_yggdrasil_hall02', '8762'),
               ('1', '1c', 'dlc_yggdrasil_hall02', '10644')]


def check_02226(ini_path):
    """0.22.26 (Q76, test arena; workspace docs/Befund-Test-Arena-Q76-1111.md): the adrenaline meter - kAdmChecks = the 6
    rows (meter-full 0x6e6630 checked only before / after the 8 bytes TruShadowPower 0.22 patches at 0x6e6646), the
    meter-full call only in AdmFillNow inside __try, adren.fill / adren.keep behind CheatGate (cheats + experimental +
    level), AdmTick in PadHook's per-frame block and gated by the switch; items adren.meter (info) / adren.fill (action,
    game thread) / adren.keep (bool); ai.remove spawned only through SpIsOurs (address + allocation stamp +0x44, entries
    from RunAiSpawn); page Tests group ts_arena1 with the rows arena.go 1a / 1b / 1c, kArenas = the 3 spots of the finding
    (arena 1 "Kampf", spot keys start with the arena number),
    RunArenaGo's shortcut (backup, unit.go, wait.unit, flight, player.goto force) and refusals, arena.go in kCmdDanger;
    no new INI key ([Adrenaline] / [Arena] absent);
    Set-TruMenu.ps1 knows the 0.22.25 hash"""
    problems = []
    src = read_cpp()
    if '"0.22.26 (test arena, Q76' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.27: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.26 part "0.22.26 (test arena, Q76"')
    m = re.search(r'const DvCheck kAdmChecks\[\] = \{(.*?)\n\};', src, re.S)
    rows = [(a, ''.join(b).replace(' ', '')) for a, b in
            [(x, re.findall(r'"([0-9a-f ]+)"', y)) for x, y in
             re.findall(r'\{0x([0-9a-f]{8}), ((?:"[0-9a-f ]+"\s*)+)\}', m.group(1))]] if m else []
    if rows != ADM_ROWS: problems.append('TruMenu.cpp: kAdmChecks must be the 6 rows of precheck_02226 section 12')
    if any(int(a, 16) <= 0x6e6646 < int(a, 16) + len(b) // 2 or int(a, 16) <= 0x6e664d < int(a, 16) + len(b) // 2
           for a, b in rows):
        problems.append('TruMenu.cpp: kAdmChecks must not cover 0x6e6646..0x6e664d (TruShadowPower 0.22 patch)')
    fill = fn_body(src, 'bool AdmFillNow(')
    if src.count('reinterpret_cast<AdmFullFn>(kAdmFull)') != 1 or 'reinterpret_cast<AdmFullFn>(kAdmFull)' not in fill or \
            not 0 <= fill.find('__try') < fill.find('AdmFullFn') < fill.find('__except'):
        problems.append('TruMenu.cpp: the meter-full 0x6e6630 must be called once, in AdmFillNow inside __try')
    for fn in ('bool RunAdmFill(', 'bool RunAdmKeep('):
        if 'if (!CheatGate(AdmCheck(), g_admWhy, o, n)) return false;' not in fn_body(src, fn):
            problems.append('TruMenu.cpp: %s must start with CheatGate(AdmCheck(), ...)' % fn.strip('('))
    tick = fn_body(src, 'void AdmTick(')
    for want in ('if (!g_admKeep || !g_admOk || !InLevel()) return;', '(s.w & (0x400000 | 0x8000000))',
                 'AdmFillNow(s, nullptr, 0);'):
        if want not in tick: problems.append('TruMenu.cpp: AdmTick must hold %s' % want)
    block = src[src.find('        AkTick();'):][:400]
    if 'AdmTick();' not in block: problems.append('TruMenu.cpp: AdmTick must run in the per-frame block (after AkTick)')
    if 'AdmCheck() ||' not in fn_body(src, 'bool AdmRead('):
        problems.append('TruMenu.cpp: AdmRead must run AdmCheck before any read')
    items = item_types(src)
    for item, typ in (('adren.meter', 'info'), ('adren.fill', 'action'), ('adren.keep', 'bool')):
        if items.get(item) != typ: problems.append('TruMenu.cpp: item %s (%s) missing in kItems' % (item, typ))
    m = re.search(r'\{"adren\.fill", "action", (?:"[^"]*"\s*)+, (true|false),', src)
    if not m or m.group(1) != 'true': problems.append('TruMenu.cpp: adren.fill must run on the game thread')
    remove = fn_body(src, 'bool RunAdRemove(')
    if 'else if (!_stricmp(a, "spawned")) mode = 4;' not in remove or 'mode == 4 ? SpIsOurs(g_adCand[i].inst)' not in remove:
        problems.append('TruMenu.cpp: ai.remove spawned must take only SpIsOurs instances')
    ours = fn_body(src, 'bool SpIsOurs(')
    if 'ReadDword(inst + 0x44, &stamp)' not in ours or 'g_spMade[i].stamp == stamp' not in ours:
        problems.append('TruMenu.cpp: SpIsOurs must compare address and allocation stamp +0x44')
    spawn = fn_body(src, 'bool RunAiSpawn(')
    if not 0 <= spawn.find('++born;') < spawn.find('SpRemember(inst);'):
        problems.append('TruMenu.cpp: RunAiSpawn must remember each born instance (SpRemember)')
    bar = qb_rows(src, True)
    tests = [(i, a, k, tail) for t, de, i, a, k, layer, tail in bar if t == 'kQbTests']
    for item, arg in ARENA_ROWS:
        if not any(i == item and a == arg and k == 'kQbAction' and 'kQfConfirm' in tail for i, a, k, tail in tests):
            problems.append('TruMenu.cpp: kQbTests lacks the arena row %s %s (action, kQfConfirm)' % (item, arg))
    for item, kind in (('adren.meter', 'kQbInfo'), ('adren.fill', 'kQbAction'), ('adren.keep', 'kQbBool'),
                       ('ai.spawn', 'kQbChoice')):
        if not any(i == item and k == kind for i, a, k, tail in tests):
            problems.append('TruMenu.cpp: kQbTests lacks the %s row %s' % (kind, item))
    if not any(i == 'ai.remove' and a == 'spawned' for i, a, k, tail in tests):
        problems.append('TruMenu.cpp: kQbTests lacks the row ai.remove spawned')
    if '"ts_arena1", kQbGroup' not in src: problems.append('TruMenu.cpp: kQbTests lacks the group ts_arena1')
    m = re.search(r'const TarArena kArenas\[\] = \{(.*?)\n\};', src, re.S)
    arenas = re.findall(r'\{(\d+), "([0-9][a-z])", "([a-z0-9_]+)", (\d+), ', m.group(1)) if m else []
    if arenas[:3] != ARENA_TABLE:   # 0.22.32: 1d .. follow (check_02232)
        problems.append('TruMenu.cpp: kArenas must start with the 3 spots of arena 1 (1a / 1b / 1c)')
    if any(not k.startswith(a) for a, k, u, i in arenas):
        problems.append('TruMenu.cpp: a kArenas spot key must start with its arena number')
    if 'const char *const kArenaNames[][2] = {{"", ""}, {"Kampf", "combat"}};' not in src:
        problems.append('TruMenu.cpp: kArenaNames must name arena 1 "Kampf" (owner 2026-11-11 13:05)')
    go = fn_body(src, 'bool RunArenaGo(')
    if '"save.backup kapitel;unit.go %s;wait.unit %s;cheat.flight 1;player.goto %ld force"' not in go and \
            '"save.backup kapitel;%s %s;wait.unit %s;cheat.flight 1;player.goto %ld force;arena.mode %s"' not in go:
        problems.append('TruMenu.cpp: arena.go must run backup, unit.go, wait.unit, flight, player.goto force')
    for want in ('UnitIndexOf(a->unit) < 0', 'UnitNameNoDrm(a->unit)', 'LevelChangePending(why, sizeof(why))',
                 'ShortcutStart(steps, title, o, n)'):   # 0.22.32: if (!ShortcutStart(...)) return false;
        if want not in go: problems.append('TruMenu.cpp: RunArenaGo must hold %s' % want)
    if items.get('arena.go') != 'action' or items.get('arena.list') != 'info':
        problems.append('TruMenu.cpp: items arena.go (action) / arena.list (info) missing in kItems')
    if not re.search(r'\{"arena\.go", "Sicherung', src): problems.append('TruMenu.cpp: kCmdDanger lacks arena.go')
    for sec in ('Adrenaline', 'Arena'):
        for line, key, value in ini_section(ini_path, sec):
            problems.append('TruMenu.ini:%d: [%s] %s - 0.22.26 adds no INI key' % (line, sec, key))
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if '79af7b39926cb91c87ec4804a0698e6ec310d3e14ce9041eae5242762e29a211' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.25 build hash (work\\asi\\menu0248) is missing')
    return problems, ('test arena: %d kAdmChecks rows (0x6e6646 patch left out), meter-full once in __try, CheatGate on '
                      'fill / keep, AdmTick per frame, ai.remove spawned by address + stamp, page Tests %d arena rows, no '
                      'new INI key' % (len(rows), len(ARENA_ROWS)))


ARENA_TABLE_02232 = ARENA_TABLE + [('1', '1d', 'l5_valgrind', '7329'), ('1', '1e', 'l2_puzzleroom', '2074'),
                                   ('1', '1f', 'l4_traprooms', '5722')]   # Q98 (workspace docs/Befund-Gruppe-A-1211.md)
ARENA_MODES_02232 = {'1a': '0', '1b': '0', '1c': '2', '1d': '0', '1e': '0', '1f': '0'}   # 2 = DLC 2 doppelganger spot


def check_02232(ini_path):
    """0.22.32 (group A 12.11.; workspace docs/Befund-Gruppe-A-1211.md): Q86 - RunAiSpawn reads the LP of each born enemy
    through SpBornLp (AiBrainOf, brain+0x2c64), names the EnemyHP step [[0xc59264]+0x3ef98] and warns while the one-hit
    kill byte 0xe91ffd is set (SpHealthNote, read only), lists the loaded kinds (SpLoadedKinds) on no / a wrong name;
    Q100 - item arena.mode (action, ValArenaMode / RunArenaMode, never err after the spot test), ArenaModeRead reads the
    player tracker byte +0x1244 and calls TruDlc2PlayerDoppelganger inside __try, RunArenaGo reads the mode first,
    takes level.load for a main-game spot with the flag set and ends its shortcut with arena.mode <spot>; Q98 - kArenas
    = 1a .. 1f with their modes, page Tests rows arena.go 1d / 1e / 1f (kQfConfirm) + arena.mode, help lines for them;
    no new INI key ([Arena] absent); Set-TruMenu.ps1 knows the 0.22.31 hash"""
    problems = []
    src = read_cpp()
    if '0.22.32 (arena, group A' not in src[:src.find('\n', src.find('kVersion = '))]:
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.32 part "0.22.32 (arena, group A"')
    if 'const DWORD kSpGameBlock = 0x00c59264, kSpEnemyHp = 0x0003ef98;' not in src:
        problems.append('TruMenu.cpp: kSpGameBlock / kSpEnemyHp must be 0x00c59264 / 0x0003ef98 (EnemyHP, 0x6e7710)')
    born = fn_body(src, 'float SpBornLp(')
    if 'AiBrainOf(inst)' not in born or 'brain + 0x2c64' not in born:
        problems.append('TruMenu.cpp: SpBornLp must read brain+0x2c64 through AiBrainOf')
    note = fn_body(src, 'void SpHealthNote(')
    if 'ByteAt(kOneHitKill)' not in note or 'gb + kSpEnemyHp' not in note:
        problems.append('TruMenu.cpp: SpHealthNote must read the EnemyHP step and the one-hit kill byte')
    spawn = fn_body(src, 'bool RunAiSpawn(')
    for want in ('SpBornLp(inst)', 'SpHealthNote(note, sizeof(note));', 'SpLoadedKinds(kinds, sizeof(kinds), nullptr);',
                 'SpLoadedKinds(like, sizeof(like), name);', 'usage: ai.spawn <exact object name>'):
        if want not in spawn: problems.append('TruMenu.cpp: RunAiSpawn must hold %s' % want)
    if not 0 <= spawn.find('SpRemember(inst);') < spawn.find('SpBornLp(inst)'):
        problems.append('TruMenu.cpp: RunAiSpawn reads the LP after SpRemember (after the birth)')
    for fn in ('float SpBornLp(', 'void SpHealthNote(', 'int SpLoadedKinds(', 'void ArenaModeRead(', 'bool RunArenaMode('):
        body = fn_body(src, fn)
        if not body: problems.append('TruMenu.cpp: %s missing' % fn.strip('('))
        if any(w in body for w in ('WriteByte(', 'WriteDword(', 'WriteFloat', 'WriteCode(', 'memcpy(reinterpret_cast')):
            problems.append('TruMenu.cpp: %s must only read' % fn.strip('('))
    items = item_types(src)
    if items.get('arena.mode') != 'action': problems.append('TruMenu.cpp: item arena.mode (action) missing in kItems')
    m = re.search(r'\{"arena\.mode", "action", (?:"[^"]*"\s*)+,\s*(true|false),\s*ValArenaMode, RunArenaMode\}', src)
    if not m or m.group(1) != 'false': problems.append('TruMenu.cpp: arena.mode = ValArenaMode / RunArenaMode, not queued')
    mode = fn_body(src, 'void ArenaModeRead(')
    if 'tracker + 0x1244' not in mode or 'ReadDword(0x00fadb58, &tracker)' not in mode or \
            not 0 <= mode.find('__try') < mode.find('g_ftDg()') < mode.find('__except'):
        problems.append('TruMenu.cpp: ArenaModeRead must read [[0xfadb58]+0x1244] and call g_ftDg inside __try')
    run = fn_body(src, 'bool RunArenaMode(')
    if run.count('return false;') != 1 or 'Log(1, "arena.mode' not in run:
        problems.append('TruMenu.cpp: RunArenaMode must log and answer err only for an unknown spot')
    go = fn_body(src, 'bool RunArenaGo(')
    for want in ('"save.backup kapitel;%s %s;wait.unit %s;cheat.flight 1;player.goto %ld force;arena.mode %s"',
                 'reload ? "level.load" : "unit.go"', 'reload = a->mode != 2 && dg', 'ArenaModeRead(m);',
                 'if (!ShortcutStart(steps, title, o, n)) return false;'):
        if want not in go: problems.append('TruMenu.cpp: RunArenaGo must hold %s' % want)
    if not 0 <= go.find('ArenaModeRead(m);') < go.find('ShortcutStart('):
        problems.append('TruMenu.cpp: RunArenaGo must read the mode before the shortcut starts')
    m = re.search(r'const TarArena kArenas\[\] = \{(.*?)\n\};', src, re.S)
    table = m.group(1) if m else ''
    arenas = re.findall(r'\{(\d+), "([0-9][a-z])", "([a-z0-9_]+)", (\d+), ', table)
    if arenas != ARENA_TABLE_02232: problems.append('TruMenu.cpp: kArenas must be the 6 spots 1a .. 1f (Q98)')
    modes = dict(re.findall(r'\{\d+, "([0-9][a-z])", .*?,\s*(\d)\},', table, re.S))
    if modes != ARENA_MODES_02232: problems.append('TruMenu.cpp: kArenas modes must be %s (got %s)' % (ARENA_MODES_02232, modes))
    if 'struct TarArena { int arena; const char *key, *unit; long intro; const char *what; int mode; };' not in src:
        problems.append('TruMenu.cpp: TarArena must carry the mode')
    bar = qb_rows(src, True)
    tests = [(i, a, k, tail) for t, de, i, a, k, layer, tail in bar if t == 'kQbTests']
    for arg in ('1d', '1e', '1f'):
        if not any(i == 'arena.go' and a == arg and k == 'kQbAction' and 'kQfConfirm' in tail for i, a, k, tail in tests):
            problems.append('TruMenu.cpp: kQbTests lacks the arena row arena.go %s (action, kQfConfirm)' % arg)
    if not any(i == 'arena.mode' and k == 'kQbAction' for i, a, k, tail in tests):
        problems.append('TruMenu.cpp: kQbTests lacks the action row arena.mode')
    for hid, harg in (('arena.go', '1d'), ('arena.go', '1e'), ('arena.go', '1f'), ('arena.mode', '')):
        if not re.search(r'\{"%s", "%s", "' % (re.escape(hid), harg), src):
            problems.append('TruMenu.cpp: kQbHelp lacks %s %s' % (hid, harg))
    for line, key, value in ini_section(ini_path, 'Arena'):
        problems.append('TruMenu.ini:%d: [Arena] %s - 0.22.32 adds no INI key' % (line, key))
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if '502f5805137f21bec0e8128c68f87066350dd9d4c7910189845780f39743ebcc' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.31 build hash (work/asi/menu0254) is missing')
    return problems, ('arena: ai.spawn LP / EnemyHP / one-hit-kill note and kind list (read only), arena.mode + mode-aware '
                      'arena.go (level.load for a main-game spot with the doppelganger flag), %d spots (%s), no INI key'
                      % (len(arenas), ' '.join(k for a, k, u, i in arenas)))


K_CHECKS_02233 = os.path.join(ROOT, 'work', 'k_menu_1211', 'k_checks.txt')
QL_TABLE_02233 = [('217', 'shark_blueshark'), ('311', 'merc'), ('312', 'merc_deux'), ('336', 'bat_enemy'), ('337', 'tiger'),
                  ('367', 'naga_green'), ('368', 'naga_red'), ('370', 'small_albino_spider'),
                  ('419', 'small_brown_spider'), ('448', 'small_brown_spider_no_jump'), ('516', 'panther_thrall'),
                  ('564', 'cat_panther'), ('565', 'poacher'), ('566', 'poacher_long_range'), ('600', 'mayan_thrall'),
                  ('603', 'viking_thrall'), ('604', 'giant_albino_tarantula'), ('703', 'giant_albino_tarantula_blind'),
                  ('705', 'yeti_thrall'), ('791', 'yeti_thrall_yggdrasil'), ('821', 'shark_greenland'),
                  ('855', 'knight_thrall'), ('927', 'viking_thrall_dlc2_'), ('931', 'yeti_thrall_dlc2_'),
                  ('943', 'yeti_thrall_armored_dlc2_'), ('1004', 'viking_thrall_tutorial_dlc2_')]


def check_02233(ini_path):
    """0.22.33 (group K 12.11.; workspace docs/Befund-Gruppe-K-1211.md): F1 photo mode - items photo.on / photo.off
    (queued) / photo.shot / photo.status, kPmChecks = rows of the offline-checked list work/k_menu_1211/k_checks.txt,
    PmRefusal refuses cutscene / loading / game pause / flight / cine.pause / camera layer, RunPhotoOn switches with
    0x5edd70(mgr, 5, 0) after the pause bit / UI byte and undoes them when the FreeCamera is not current, PmLeave goes
    back with the remembered mode (0x5edf50 only when mode / layer changed) and clears the pause bit / UI byte only when
    photo.on set them, PmTick (Present hook) leaves on level change / state / cutscene / pause / camera, PmShutdown in
    DllMain makes no game call; Q83 arena.load / arena.unload (queued) / arena.enemies, kQlChecks also from k_checks.txt,
    the 26 kinds of the Q83 catalog, request 0x5c1760 only after the tracker / anim pool / 3D navgraph / DRM checks,
    ai.spawn asks QlSpawnBlock, unload only own requests whose entry still holds the id; glyphs.status; bar rows / help
    lines; no new INI key; Set-TruMenu.ps1 knows the 0.22.32 hash"""
    problems = []
    src = read_cpp()
    if '0.22.33 (photo mode, arena.load, glyphs.status, group K' not in src[:src.find('\n', src.find('kVersion = '))]:
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.33 part "0.22.33 (photo mode, arena.load, glyphs.status, '
                        'group K"')
    offline = {}
    if os.path.exists(K_CHECKS_02233):
        for line in open(K_CHECKS_02233, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if line:
                addr, hexs = line.split(None, 1)
                offline[int(addr, 16)] = hexs.replace(' ', '').lower()
    else:
        problems.append('work/k_menu_1211/k_checks.txt (the offline byte list) is missing')
    counts = {}
    for table in ('kPmChecks', 'kQlChecks'):
        rows = sv_rows(src, table)
        counts[table] = len(rows)
        if not rows: problems.append('TruMenu.cpp: DvCheck table %s missing' % table)
        for a, b in rows:
            if offline.get(int(a, 16)) != b.lower():
                problems.append('TruMenu.cpp: %s row 0x%s is not the offline-checked bytes of k_checks.txt' % (table, a))
    if counts.get('kPmChecks') != 23 or counts.get('kQlChecks') != 14:
        problems.append('TruMenu.cpp: kPmChecks / kQlChecks must hold 23 / 14 rows (got %s)' % counts)
    items = item_types(src)
    for item, kind in (('photo.on', 'action'), ('photo.off', 'action'), ('photo.shot', 'action'), ('photo.status', 'info'),
                       ('arena.load', 'action'), ('arena.unload', 'action'), ('arena.enemies', 'info'),
                       ('glyphs.status', 'info')):
        if items.get(item) != kind: problems.append('TruMenu.cpp: item %s (%s) missing in kItems' % (item, kind))
    for item, queued, val, run in (('photo.on', 'true', 'ValPhoto', 'RunPhotoOn'), ('photo.off', 'true', 'ValPhoto', 'RunPhotoOff'),
                                   ('photo.shot', 'false', 'ValPhoto', 'RunPhotoShot'),
                                   ('arena.load', 'true', 'ValArenaEnemies', 'RunArenaLoad'),
                                   ('arena.unload', 'true', 'ValArenaEnemies', 'RunArenaUnload')):
        m = re.search(r'\{"%s", "action", (?:"[^"]*"\s*)+,\s*(true|false),\s*%s,\s*%s\}' % (re.escape(item), val, run), src)
        if not m or m.group(1) != queued:
            problems.append('TruMenu.cpp: %s = %s / %s, game thread %s' % (item, val, run, queued))
    ref = fn_body(src, 'void PmRefusal(')
    for want in ('CinematicNow()', 'LevelChangePending(', 'g_cnPause', 'kPmGamePause', 'g_flight', 'kCameraManager + 0x4c',
                 'kCameraManager + 0x7c', 'kCameraManager + 4 + mode * 4', 'kCameraManager + 0x3370', 'kPmFreeCamVt',
                 'PmCheck()'):
        if want not in ref: problems.append('TruMenu.cpp: PmRefusal must test %s' % want)
    on = fn_body(src, 'bool RunPhotoOn(')
    sw = on.find('(kCameraManager, 0, 5, 0)')
    if not (0 <= on.find('PmRefusal(why, sizeof(why));') < on.find('InterlockedOr(f, 0x1000)') < sw <
            on.find('cur != kPmFreeCam')):
        problems.append('TruMenu.cpp: RunPhotoOn = refusal test, pause bit, then 0x5edd70(mgr, 5, 0), then the camera test')
    for want in ('g_pmPauseOurs = !(before & 0x1000) || menuHeld || ringHeld;', 'g_pmUiOurs = !ui;',
                 'InterlockedExchange(&g_menuPaused, 0)', 'if (g_pmPauseOurs) InterlockedAnd(f, ~0x1000L);'):
        if want not in on: problems.append('TruMenu.cpp: RunPhotoOn must hold %s' % want)
    leave = fn_body(src, 'void PmLeave(')
    for want in ('(kCameraManager, 0, g_pmMode, 0)', 'ours && !layer && mode == 5', 'kCameraRestore', 'kPmCtlOff',
                 'g_pmPauseOurs && ReadDword(kStreamFlags, &flags) && (flags & 0x1000)', 'g_pmUiOurs && ByteAt(kUiHidden)',
                 '__try', '__except'):
        if want not in leave: problems.append('TruMenu.cpp: PmLeave must hold %s' % want)
    tick = fn_body(src, 'void PmTick(')
    for want in ('LevelChangePending(', 'player != g_pmPlayer', 'unit != g_pmUnit', 'CinematicNow()', 'kPmGamePause',
                 'cur != kPmFreeCam', 'PmLeave(why'):
        if want not in tick: problems.append('TruMenu.cpp: PmTick must test %s' % want)
    shut = fn_body(src, 'void PmShutdown(')
    if 'reinterpret_cast<PmSetModeFn>' in shut or 'kCameraRestore' in shut or 'kPmCtlOff' in shut:
        problems.append('TruMenu.cpp: PmShutdown must not call the game (DllMain)')
    render = fn_body(src, 'void Render(')
    if 'PmTick();' not in render or 'QlTick();' not in render:
        problems.append('TruMenu.cpp: Render (Present hook) must call PmTick / QlTick')
    if 'PmShutdown();' not in src[src.find('DLL_PROCESS_DETACH'):]:
        problems.append('TruMenu.cpp: DllMain detach must call PmShutdown')
    shot = fn_body(src, 'bool RunPhotoShot(')
    if '"clean photo_%03ld%s%s"' not in shot or 'RunShotSave(a, o, n)' not in shot:
        problems.append('TruMenu.cpp: photo.shot = shot.save clean photo_<n>')
    m = re.search(r'const QlKind kQlKinds\[\] = \{(.*?)\n\};', src, re.S)
    kinds = re.findall(r'\{(\d+), "([a-z0-9_]+)", \d, \d, \d+, \d+, \d+, "[^"]*"\}', m.group(1) if m else '')
    if kinds != QL_TABLE_02233: problems.append('TruMenu.cpp: kQlKinds must be the 26 enemy kinds of the Q83 catalog')
    load = fn_body(src, 'bool RunArenaLoad(')
    req = load.find('reinterpret_cast<QlRequestFn>(kQlRequest)(q.id)')
    for want in ('g_qlN >= kQlMax', 'QlHas3dNav()', 'freeCount < q.drms + 2', 'animFree < q.anims + 100',
                 'reinterpret_cast<DrmExistsFn>(kDrmExists)(t)', 'RunSaveBackup("spawn"', 'TrackerScan(q.id, &freeCount)',
                 'LevelChangePending('):
        pos = load.find(want)
        if pos < 0 or req < 0 or pos > req: problems.append('TruMenu.cpp: RunArenaLoad must test %s before 0x5c1760' % want)
    if 'const int kQlMax = 2;' not in src: problems.append('TruMenu.cpp: kQlMax must be 2 (Q83: at most 2 foreign kinds)')
    walk = fn_body(src, 'void QlWalk(')
    for want in ('e + 0xe', 'status != 2', 'object + 0x3c', 'object + 0x44', 'slot == 0xffff', 'object + 0x2c',
                 'depth >= 4'):
        if want not in walk: problems.append('TruMenu.cpp: QlWalk must read %s' % want)
    spawn = fn_body(src, 'bool RunAiSpawn(')
    if not 0 <= spawn.find('QlSpawnBlock(id, qlWhy, sizeof(qlWhy));') < spawn.find('TrackerScan(id, &freeCount)'):
        problems.append('TruMenu.cpp: RunAiSpawn must ask QlSpawnBlock before the tracker test')
    unload = fn_body(src, 'bool RunArenaUnload(')
    if 'static_cast<SHORT>(id) == q.id' not in unload or 'held && QlDumpOne(q.id)' not in unload:
        problems.append('TruMenu.cpp: RunArenaUnload dumps only an entry that still holds the id')
    if 'reinterpret_cast<QlDumpFn>(kQlDump)(id)' not in fn_body(src, 'bool QlDumpOne('):
        problems.append('TruMenu.cpp: QlDumpOne must call 0x5c1790')
    for fn in ('void PmRefusal(', 'void QlWalk(', 'void QlKindState(', 'void ValArenaEnemies(', 'void ValGlyphStatus(',
               'int QlAnimFree(', 'bool QlHas3dNav('):
        body = fn_body(src, fn)
        if not body: problems.append('TruMenu.cpp: %s missing' % fn.strip('('))
        if any(w in body for w in ('WriteByte(', 'WriteDword(', 'WriteCode(', 'reinterpret_cast<volatile', 'Interlocked',
                                   'Fn>(')):
            problems.append('TruMenu.cpp: %s must only read' % fn.strip('('))
    gl = fn_body(src, 'void GlDevice(')
    if 'g_glLastTick = GetTickCount();' not in gl or 'GetLocalTime(&t);' not in gl or 'g_glSub' not in gl:
        problems.append('TruMenu.cpp: GlDevice must note the input kind and the switch time (glyphs.status)')
    bar = qb_rows(src, True)
    lara = [(i, a, k) for t, de, i, a, k, layer, tail in bar if t == 'kQbLara']
    for i, k in (('photo.on', 'kQbAction'), ('photo.shot', 'kQbAction'), ('photo.off', 'kQbAction'),
                 ('photo.status', 'kQbInfo')):
        if (i, '', k) not in lara: problems.append('TruMenu.cpp: kQbLara lacks the row %s (%s)' % (i, k))
    tests = [(i, a, k, tail) for t, de, i, a, k, layer, tail in bar if t == 'kQbTests']
    loads = [a for i, a, k, tail in tests if i == 'arena.load' and k == 'kQbAction' and 'kQfConfirm' in tail]
    if loads != ['mayan_thrall', 'yeti_thrall_yggdrasil', 'panther_thrall', 'tiger', 'giant_albino_tarantula', 'merc',
                 'knight_thrall', 'viking_thrall_dlc2_']:
        problems.append('TruMenu.cpp: kQbTests arena.load rows must follow the T19 order (got %s)' % loads)
    if not any(i == 'arena.unload' and a == 'all' and 'kQfConfirm' in tail for i, a, k, tail in tests):
        problems.append('TruMenu.cpp: kQbTests lacks arena.unload all (kQfConfirm)')
    if not any(i == 'arena.enemies' and k == 'kQbInfo' for i, a, k, tail in tests):
        problems.append('TruMenu.cpp: kQbTests lacks the info row arena.enemies')
    for hid, harg in (('arena.enemies', ''), ('arena.load', r'\*'), ('arena.unload', 'all'), ('photo.on', ''),
                      ('photo.shot', ''), ('photo.off', '')):
        if not re.search(r'\{"%s", "%s", "' % (re.escape(hid), harg), src):
            problems.append('TruMenu.cpp: kQbHelp lacks %s %s' % (hid, harg))
    for section in ('Photo', 'ArenaLoad'):
        for line, key, value in ini_section(ini_path, section):
            problems.append('TruMenu.ini:%d: [%s] %s - 0.22.33 adds no INI key' % (line, section, key))
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if '5f7ba420c25f717ede72b60c30d87665174807f0a8fd2f73bc30c0781a33750e' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.32 build hash (work/asi/menu0255) is missing')
    return problems, ('photo mode (FreeCamera mode 5, pause bit, UI byte, way back, auto-leave; %d byte checks), arena.load '
                      '(%d kinds, %d byte checks, ready before ai.spawn), glyphs.status, no INI key'
                      % (counts.get('kPmChecks', 0), len(kinds), counts.get('kQlChecks', 0)))


M_CHECKS_02234 = os.path.join(ROOT, 'work', 'm_menu_1211', 'm_checks.txt')
B_ROWS_02234 = os.path.join(ROOT, 'work', 'b_nav_1211', 'q105_chaporder_rows.txt')
# Q20 / I-2 (docs/Befund-Gruppe-I-1211.md 2b): native f0 .. f15 -> Xbox achievement id (Xbox stubs `li r4, id`), unsure =
# f12 - f15 (shared script 5 not read)
ACH_IDS_02234 = [1, 40, 41, 42, 43, 44, 45, 46, 2, 23, 24, 25, 27, 14, 17, 18]


def check_02234(ini_path, switches_path):
    """0.22.34 (group M 12.11.; workspace docs/Befund-Gruppe-M-1211.md): Q20 achievements - kAchChecks (23) and the
    photo.pose kPpChecks (13) = rows of the offline-checked work/m_menu_1211/m_checks.txt; kAchDefs = the 16 Xbox ids of
    I-2 with f12 - f15 (only) unsure; AchStart patches the 16 push immediates from 0x7abb8e (14 bytes apart) only after the
    byte checks and with [Achievements] Enabled, is called after SaveFolderInit in Start, g_achLock initialised in
    DllMain; AchCall / AchAppend / AchLoad write no game memory; [Achievements] Enabled=1 in kOpts / TruMenu.ini, a
    restart switch row; items ach.list / ach.status (info), photo.pose (action, game thread); RunPhotoPose refuses outside
    the photo mode and requests mode 0 only after the section / resident tests, PpUndo requests mode 1 only for the same
    instance / processor, outside cutscenes and below the slot count, PmLeave undoes the pose first, PmShutdown makes no
    game call; ai.spawn warns through QlChildWarn (QlWalk) and does not refuse; kChapOrder base rows = the B generator
    output (1.2 before l1_kraken_entrance); bar rows / page / group; Set-TruMenu.ps1 knows the 0.22.33 hash"""
    problems = []
    src = read_cpp()
    if '0.22.34 (achievements, photo.pose, group M' not in src[:src.find('\n', src.find('kVersion = '))]:
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.34 part "0.22.34 (achievements, photo.pose, group M"')
    offline = {}
    if os.path.exists(M_CHECKS_02234):
        for line in open(M_CHECKS_02234, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if line:
                addr, hexs = line.split(None, 1)
                offline[int(addr, 16)] = hexs.replace(' ', '').lower()
    else:
        problems.append('work/m_menu_1211/m_checks.txt (the offline byte list) is missing')
    counts = {}
    for tname in ('kAchChecks', 'kPpChecks'):
        rows = sv_rows(src, tname)
        counts[tname] = len(rows)
        for a, b in rows:
            if offline.get(int(a, 16)) != b.lower():
                problems.append('TruMenu.cpp: %s row 0x%s is not the offline-checked bytes of m_checks.txt' % (tname, a))
    if counts.get('kAchChecks') != 23 or counts.get('kPpChecks') != 13:
        problems.append('TruMenu.cpp: kAchChecks / kPpChecks must hold 23 / 13 rows (got %s)' % counts)
    for k in range(16):
        want = '6820667900 6a%02x 8bce' % k
        if offline.get(0x7abb8d + 14 * k, '')[:len(want.replace(' ', ''))] != want.replace(' ', ''):
            problems.append('m_checks.txt: binder row %d (0x%08x) must start with push 0x796620 / push %d' % (k, 0x7abb8d + 14 * k, k))
    m = re.search(r'const AchDef kAchDefs\[16\] = \{(.*?)\};', src, re.S)
    defs = re.findall(r'\{(\d+), (\d+), "([^"]+)", (true|false)\}', m.group(1) if m else '')
    if [int(i) for i, s, nm, u in defs] != ACH_IDS_02234:
        problems.append('TruMenu.cpp: kAchDefs ids must be %s (I-2)' % ACH_IDS_02234)
    if [u == 'true' for i, s, nm, u in defs] != [k >= 12 for k in range(16)]:
        problems.append('TruMenu.cpp: kAchDefs must mark exactly f12 - f15 unsure')
    if 'const DWORD kAchPush = 0x007abb8e;' not in src: problems.append('TruMenu.cpp: kAchPush must be 0x007abb8e')
    st = fn_body(src, 'void AchStart(')
    chk, en, wr = st.find('DvChecks(kAchChecks'), st.find('!g_achEnabled'), st.find('WriteBytes(kAchPush + 14 * static_cast<DWORD>(k), &stub, 4)')
    if not (0 <= chk < en < wr): problems.append('TruMenu.cpp: AchStart = byte checks, Enabled test, then the 16 push writes')
    start = fn_body(src, 'void Start(')
    if not 0 <= start.find('SaveFolderInit();') < start.find('AchStart();'):
        problems.append('TruMenu.cpp: Start must call AchStart after SaveFolderInit')
    if 'InitializeCriticalSection(&g_achLock);' not in src[src.find('DLL_PROCESS_ATTACH'):]:
        problems.append('TruMenu.cpp: DllMain must initialise g_achLock')
    for fn in ('void AchCall(', 'bool AchAppend(', 'void AchLoad(', 'void ValAchList(', 'void ValAchStatus(',
               'void PageAchievements(', 'void QlChildWarn(', 'void PpTarget(', 'bool PpEntry('):
        body = fn_body(src, fn)
        if not body: problems.append('TruMenu.cpp: %s missing' % fn.strip('('))
        if any(w in body for w in ('WriteByte(', 'WriteBytes(', 'WriteDword(', 'reinterpret_cast<volatile', 'Fn>(')):
            problems.append('TruMenu.cpp: %s must not write game memory or call the game' % fn.strip('('))
    if 'AchCall(K, argc, args)' not in src: problems.append('TruMenu.cpp: AchStub<K> must call AchCall')
    if not re.search(r'\{"Achievements", "Enabled", "1",', src):
        problems.append('TruMenu.cpp: kOpts [Achievements] Enabled default must be 1')
    if [(k, v) for l, k, v in ini_section(ini_path, 'Achievements')] != [('Enabled', '1')]:
        problems.append('TruMenu.ini: [Achievements] must hold Enabled=1 only')
    header, opt_rows = table(src)
    if len(opt_rows) < 260:   # 0.22.36 adds [Debug] LabelCollected / LabelLaraGear (check_02236): at least the 260 keys
        problems.append('TruMenu.cpp: kOpts has %d keys - 0.22.34 adds [Achievements] Enabled (260)' % len(opt_rows))
    sw = open(switches_path, encoding='utf-8').read()
    if not re.search(r'^TruMenu \| Achievements \| Enabled \| bool \|[^|]+\|[^|]+\| restart \| 1 \|', sw, re.M):
        problems.append('TruMenu.switches.txt: row TruMenu | Achievements | Enabled | bool | ... | restart | 1 missing')
    items = item_types(src)
    for item, kind in (('ach.list', 'info'), ('ach.status', 'info'), ('photo.pose', 'action')):
        if items.get(item) != kind: problems.append('TruMenu.cpp: item %s (%s) missing in kItems' % (item, kind))
    if not re.search(r'\{"photo.pose", "action", (?:"[^"]*"\s*)+,\s*true,\s*ValPhoto,\s*RunPhotoPose\}', src):
        problems.append('TruMenu.cpp: photo.pose = ValPhoto / RunPhotoPose on the game thread')
    if 'const int kPpLastIndex = 1604;' not in src or 'const WORD kPpLastSection = 1551;' not in src:
        problems.append('TruMenu.cpp: kPpLastIndex / kPpLastSection must be 1604 / 1551 (screen_capture_01, group F)')
    pose = fn_body(src, 'bool RunPhotoPose(')
    req = pose.find('reinterpret_cast<PpRequestFn>(kPpRequest)(proc, 0, rec, 0)')
    for want in ('!g_pmActive', 'PpCheck()', 'g_experimental', 'section != kPpLastSection + 1 - pose', 'slot == 0xffff',
                 'const WORD rec[2] = {0, static_cast<WORD>(k)};', 'ReadDword(proc + 0x44, &before)'):
        pos = pose.find(want)
        if pos < 0 or req < 0 or pos > req: problems.append('TruMenu.cpp: RunPhotoPose must test / note %s before 0x444ba0' % want)
    undo = fn_body(src, 'void PpUndo(')
    req = undo.find('reinterpret_cast<PpRequestFn>(kPpRequest)(proc, 0, rec, 0)')
    for want in ('player != g_ppPlayer', 'proc != g_ppProc', 'CinematicNow()', 'LevelChangePending(', 'g_ppSlot >= count',
                 'const WORD rec[2] = {1, static_cast<WORD>(g_ppSlot)};'):
        pos = undo.find(want)
        if pos < 0 or req < 0 or pos > req: problems.append('TruMenu.cpp: PpUndo must test %s before 0x444ba0 mode 1' % want)
    leave = fn_body(src, 'void PmLeave(')
    if not 0 <= leave.find('PpUndo(reason') < leave.find('PmSetModeFn'):
        problems.append('TruMenu.cpp: PmLeave must undo the pose before the camera switch')
    if 'PpUndo' in fn_body(src, 'void PmShutdown('): problems.append('TruMenu.cpp: PmShutdown must not call PpUndo (DllMain)')
    spawn = fn_body(src, 'bool RunAiSpawn(')
    kid = spawn.find('QlChildWarn(id, kidWarn, sizeof(kidWarn));')
    if not (0 <= spawn.find('QlSpawnBlock(id, qlWhy, sizeof(qlWhy));') < kid < spawn.find('kBirthObject')):
        problems.append('TruMenu.cpp: RunAiSpawn must ask QlChildWarn after QlSpawnBlock, before the birth')
    if 'return false' in spawn[kid:spawn.find('\n', spawn.find('if (kidWarn[0])', kid))]:
        problems.append('TruMenu.cpp: the child warning must not refuse the spawn')
    if 'QlWalk(id, 0, &total, &ready, &animMissing, stuck, sizeof(stuck));' not in fn_body(src, 'void QlChildWarn('):
        problems.append('TruMenu.cpp: QlChildWarn must use the ready walk QlWalk')
    raw = open(CPP, encoding='utf-8').read()  # the octal escapes as written (read_cpp replaces the umlaut escapes)
    order = raw[raw.index('const ChapOrder kChapOrder[] = {'):]
    order = order[:order.index('\n};')]
    have = re.findall(r'\{"(Base game l\d)", "(\w+)", false, "([0-9 ]*)",\s*((?:"[^"]*"\s*)+|nullptr)\}', order)
    have = [(g, u, c, ''.join(re.findall(r'"([^"]*)"', h)) if h != 'nullptr' else None) for g, u, c, h in have]
    want = []
    for line in open(B_ROWS_02234, encoding='utf-8'):
        m = re.match(r'\s*\{"(Base game l\d)", "(\w+)", false, "([0-9 ]*)", (?:"(.*)"|nullptr)\},$', line.rstrip())
        if m: want.append((m.group(1), m.group(2), m.group(3), m.group(4)))
    # (0.22.37: both patterns skip the return-visit rows "..., 2}" - check_02237 compares those)
    if have != want or len(want) != 84:
        problems.append('TruMenu.cpp: kChapOrder base rows != work/b_nav_1211/q105_chaporder_rows.txt (%d / %d)' % (len(have), len(want)))
    if not any(g == 'Base game l1' and u == 'l1_kraken_entrance' and h == 'Kapitel 1.2 Niflheim|Chapter 1.2 Niflheim'
               for g, u, c, h in want):   # 0.22.37: its checkpoints are Paket R's 672 673 696 now
        problems.append('q105_chaporder_rows.txt: chapter 1.2 must head l1_kraken_entrance (J-5)')
    bar = qb_rows(src, True)
    lara = [(i, a, k) for t, de, i, a, k, layer, tail in bar if t == 'kQbLara']
    for i, a in (('photo.pose', 'next'), ('photo.pose', 'off')):
        if (i, a, 'kQbAction') not in lara: problems.append('TruMenu.cpp: kQbLara lacks the row %s %s' % (i, a))
    for hid, harg in (('photo.pose', 'next'), ('photo.pose', 'off')):
        if not re.search(r'\{"%s", "%s", "' % (re.escape(hid), harg), src):
            problems.append('TruMenu.cpp: kQbHelp lacks %s %s' % (hid, harg))
    fig = fn_body(src, 'int QbFigRows(')
    if 'QbGroupClosed("fig_ach")' not in fig or 'q.intro = 2;' not in fig:
        problems.append('TruMenu.cpp: QbFigRows must hold the group fig_ach (intro 2)')
    if '"fig_ach"' not in src[src.index('const char *const kQbStartClosed[] = {'):][:2000]:
        problems.append('TruMenu.cpp: fig_ach must start closed (kQbStartClosed)')
    if 'q.intro == 2 ? "fig_ach"' not in fn_body(src, 'void QbFigAct('):
        problems.append('TruMenu.cpp: QbFigAct must open / close fig_ach')
    if 'MenuPage("Achievements / Erfolge (0.22.34)###achpage", "achievements")) PageAchievements();' not in src:
        problems.append('TruMenu.cpp: big window page Achievements (key achievements) missing')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if '8dabebd42c9e5b0991c73f89dbd485b4f5a14ea834abe4c474d64704a5c66236' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.33 build hash (work/asi/menu0256) is missing')
    return problems, ('achievements (16 natives -> stubs, %d byte checks, [Achievements] Enabled=1 restart), photo.pose '
                      '(mode 0 / mode 1 back, %d byte checks), ai.spawn child warning, chapter 1.2 at l1_kraken_entrance'
                      % (counts.get('kAchChecks', 0), counts.get('kPpChecks', 0)))


Q113_CP_02235 = os.path.join(ROOT, 'work', 'q113_chain_1211', 'q113_cp_order.txt')
# 0.22.37 (P5): the first-visit rows the Paket R run corrected (generator PAKET_R_FWD)
P5_PAKET_R_UNITS = ('l1_kraken_room', 'l1_kraken_entrance', 'l1_norse_hallway_a', 'l1_baldrs_tomb')


def check_02235():
    """0.22.35 (Q113, 12.11.; workspace docs/Befund-Q113-Levelkette-1211.md): only kChapOrder changes - the base rows stay
    the B generator output (check_02234) and their checkpoint ids are now in WALKING order = work/q113_chain_1211/
    q113_cp_order.txt (written by q113_chain.py, the proven level chain); same 84 units / 303 ids as the +0x52 order;
    loop headings with direction (l1, l2) and the l4_temple side trip; kVersion holds the 0.22.35 part; Set-TruMenu.ps1
    knows the 0.22.34 hash"""
    problems = []
    src = read_cpp()
    if '0.22.35 (level chain, Q113' not in src[:src.find('\n', src.find('kVersion = '))]:
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.35 part "0.22.35 (level chain, Q113"')
    raw = open(CPP, encoding='utf-8').read()
    order = raw[raw.index('const ChapOrder kChapOrder[] = {'):]
    order = order[:order.index('\n};')]
    have = re.findall(r'\{"(Base game l\d)", "(\w+)", false, "([0-9 ]*)",\s*((?:"[^"]*"\s*)+|nullptr)\}', order)
    walk = {}
    if os.path.exists(Q113_CP_02235):
        for line in open(Q113_CP_02235, encoding='utf-8'):
            if line.startswith('#') or not line.strip(): continue
            u, _, ids = line.rstrip('\n').partition('\t')
            walk[u] = ids.split()
    else:
        problems.append('work/q113_chain_1211/q113_cp_order.txt is missing')
    n_ids = 0
    for g, u, c, h in have:
        n_ids += len(c.split())
        if u in P5_PAKET_R_UNITS: continue   # 0.22.37: the Paket R rows (check_02237: = the generator, proven ids)
        if walk and walk.get(u) != c.split():
            problems.append('TruMenu.cpp: kChapOrder %s checkpoints "%s" != walking order %s' % (u, c, walk.get(u)))
    # 0.22.37: 303 + 7 save ids Paket R added (84, 696, 672, 673, 781, 160, 42) - 76 moved to the return row = 309
    if len(have) != 84 or n_ids != 309:
        problems.append('TruMenu.cpp: kChapOrder base rows %d / ids %d (want 84 / 309 since 0.22.37)' % (len(have), n_ids))
    heads = {u: ''.join(re.findall(r'"([^"]*)"', h)) for g, u, c, h in have if h != 'nullptr'}
    for u, want in (('l1_baldrsstairs_a', 'Rundweg ab l1_kraken_room: Treppen -> Grab'),
                    ('l2_norsehall', 'Rundweg ab l2_puzzleroom: norsehall'), ('l4_templepath', 'Abstecher in 4.2: Tempel')):
        if not heads.get(u, '').startswith(want): problems.append('TruMenu.cpp: kChapOrder %s heading must start "%s"' % (u, want))
    if 'Richtung nicht in den Daten)|Loop from l1_kraken_room' in order:
        problems.append('TruMenu.cpp: the old l1 loop heading (direction not in the data) is still there')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if '646c4b3e9b9e7dc3fae507b8254ebd3d73332f8978e4f001e1ce91ff96a0883b' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.34 build hash (work/asi/menu0257) is missing')
    return problems, 'level chain Q113 (84 base rows, %d checkpoint ids in walking order, loop / side-trip headings)' % n_ids


LG_CHECKS_02236 = os.path.join(ROOT, 'work', 'labels_1211', 'precheck_02236.txt')


def check_02236(ini_path, switches_path):
    """0.22.36 (labels, live 2026-11-12; workspace docs/Befund-Labels-1211.md): the name labels dbg.labels (DrawLabels) and
    dbg.names (DvDrawNames) both ask LabelFilter, which asks the ONE 0.21 check LfNotDrawn (no second implementation) and
    LgIsLaraGear (game data: parent +0x54 = player, weapon-manager handles of LgCollect - no object-name test); kLgChecks
    = the rows of the offline-checked work/labels_1211/precheck_02236.txt (11), g_lgOk = g_lfOk && DvChecks(kLgChecks);
    the filter functions write no game memory and call no game function; [Debug] LabelCollected / LabelLaraGear default
    0 in kOpts and TruMenu.ini, read by ReadOptions and about once a second by LgReadSwitch (FallWatchTick), switches
    rows live 0; items dbg.labelcollected / dbg.labelgear (bool), bar rows on page Render next to Objektnamen, menu
    checkboxes, bar help; README 0.22.36 with TO TEST; Set-TruMenu.ps1 knows the 0.22.35 hash"""
    problems = []
    src = read_cpp()
    if '0.22.36 (label filter' not in src[:src.find('\n', src.find('kVersion = '))]:
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.36 part "0.22.36 (label filter"')
    offline = []
    if os.path.exists(LG_CHECKS_02236):
        for line in open(LG_CHECKS_02236, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if line:
                addr, hexs = line.split(None, 1)
                offline.append(('%08x' % int(addr, 16), hexs.replace(' ', '').lower()))
    else:
        problems.append('work/labels_1211/precheck_02236.txt (the offline byte list) is missing')
    rows = [(a.lower(), b.lower()) for a, b in sv_rows(src, 'kLgChecks')]
    if rows != offline or len(rows) != 11:
        problems.append('TruMenu.cpp: kLgChecks (%d rows) must be the 11 rows of precheck_02236.txt in order' % len(rows))
    if src.count('\nint LfNotDrawn(DWORD inst) {') != 1:
        problems.append('TruMenu.cpp: exactly one LfNotDrawn implementation wanted')
    lf = fn_body(src, 'int LabelFilter(')
    for need in ('LgIsLaraGear(inst, player)', 'LfNotDrawn(inst)', 'g_lblCollected', 'g_lblGear'):
        if need not in lf: problems.append('TruMenu.cpp: LabelFilter lacks %s' % need)
    for fn, layer in (('void DrawLabels(', '"dbg.labels"'), ('void DvDrawNames(', '"dbg.names"')):
        body = fn_body(src, fn)
        if 'LabelFilter(%s' % layer not in body or 'LgCollect();' not in body:
            problems.append('TruMenu.cpp: %s must call LgCollect and LabelFilter(%s, ...)' % (fn.strip('('), layer))
        if 'LabelCollectedText()' not in body: problems.append('TruMenu.cpp: %s must add the grey suffix' % fn.strip('('))
    gear = fn_body(src, 'bool LgIsLaraGear(')
    if 'ReadDword(inst + 0x54, &parent) && parent == player' not in gear or 'g_lgSet[i] == inst' not in gear:
        problems.append('TruMenu.cpp: LgIsLaraGear = parent +0x54 == player or a weapon-manager handle')
    col = fn_body(src, 'void LgCollect(')
    for need in ('tracker + 0x500', 'wm + (hand ? 0xc : 0x4) + 0x10 * slot', 'wm + 0xf4 + 8 * i', 'slot < 15', 'i < 8'):
        if need not in col: problems.append('TruMenu.cpp: LgCollect lacks %s' % need)
    for fn in ('int LabelFilter(', 'bool LgIsLaraGear(', 'void LgCollect(', 'void LgNote(', 'void LgReadSwitch('):
        body = fn_body(src, fn)
        if not body: problems.append('TruMenu.cpp: %s missing' % fn.strip('('))
        if any(w in body for w in ('WriteByte(', 'WriteBytes(', 'WriteDword(', 'reinterpret_cast<volatile', 'Fn>(')):
            problems.append('TruMenu.cpp: %s must not write game memory or call the game' % fn.strip('('))
        if fn in ('bool LgIsLaraGear(', 'void LgCollect(') and ('ObjectName(' in body or 'strstr(' in body):
            problems.append('TruMenu.cpp: %s must tell gear by data, not by names' % fn.strip('('))
    if 'g_lgOk = g_lfOk && DvChecks(kLgChecks,' not in src:
        problems.append('TruMenu.cpp: g_lgOk must be g_lfOk && DvChecks(kLgChecks, ...)')
    rd = fn_body(src, 'void LgReadSwitch(')
    for key in ('"LabelCollected"', '"LabelLaraGear"', '"Debug"'):
        if key not in rd: problems.append('TruMenu.cpp: LgReadSwitch must read %s' % key)
    if 'if (now - g_lgReadTick >= 1000) { g_lgReadTick = now; LgReadSwitch(); }' not in fn_body(src, 'void FallWatchTick('):
        problems.append('TruMenu.cpp: FallWatchTick must call LgReadSwitch about once a second')
    if 'LgReadSwitch();' not in fn_body(src, 'void ReadOptions('):
        problems.append('TruMenu.cpp: ReadOptions must call LgReadSwitch')
    header, opt_rows = table(src)
    keys = {(s, k): d for s, k, d, _ in opt_rows}
    for k in ('LabelCollected', 'LabelLaraGear'):
        if keys.get(('Debug', k)) != '0': problems.append('TruMenu.cpp: kOpts [Debug] %s must default to 0' % k)
    ini = open(ini_path, encoding='utf-8').read()
    for k in ('LabelCollected', 'LabelLaraGear'):
        if '\n%s=0\n' % k not in ini.replace('\r\n', '\n'): problems.append('%s: [Debug] %s=0 missing' % (ini_path, k))
    for item, val, run in (('dbg.labelcollected', 'ValLblCollected', 'RunLblCollected'),
                           ('dbg.labelgear', 'ValLblGear', 'RunLblGear')):
        if not re.search(r'\{"%s", "bool", .*?, false, %s, %s\}' % (re.escape(item), val, run), src, re.S):
            problems.append('TruMenu.cpp: item %s (bool, %s / %s) missing' % (item, val, run))
        if not re.search(r'\{"[^"]+", "[^"]+", "%s", "", kQbBool, -1, kQcNone, 0, kQbWhite, 0\}' % re.escape(item), src):
            problems.append('TruMenu.cpp: bar row %s missing' % item)
        if '{"%s", "", "' % item not in src: problems.append('TruMenu.cpp: bar help row %s missing' % item)
    for need in ('[dbg.labelcollected]###dvlcol', '[dbg.labelgear]###dvlgear'):
        if need not in src: problems.append('TruMenu.cpp: menu checkbox %s missing (page Debug view)' % need)
    want = {'LabelCollected', 'LabelLaraGear'}   # (0.22.37 adds LabelRoom - only these two keys are 0.22.36's)
    sw = [l.rstrip('\r\n') for l in open(switches_path, encoding='utf-8')
          if l.startswith('TruMenu | Debug | Label') and l.split(' | ')[2] in want]
    got = {l.split(' | ')[2] for l in sw if ' | bool | ' in l and ' | live | 0 | ' in l and l.endswith('| TruMenu 0.22.36')}
    if got != want or len(sw) != 2:
        problems.append('%s: rows TruMenu | Debug | LabelCollected / LabelLaraGear | bool | ... | live | 0 | ... | TruMenu '
                        '0.22.36 wanted (got %s)' % (os.path.basename(switches_path), sorted(got)))
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8').read()
    if '\n## 0.22.36 - ' not in readme or '\n### TO TEST 0.22.36' not in readme:
        problems.append('README.md: section "## 0.22.36 - ..." with "### TO TEST 0.22.36" missing')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if 'dcb5a5a1d570ab00f213e19dca404f6594dbe8e5459cf12fd5d4f39e99268ee9' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.35 build hash (work/asi/menu0258) is missing')
    return problems, ('label filter (dbg.labels + dbg.names -> LabelFilter -> the one LfNotDrawn; Lara\'s gear by parent '
                      '+0x54 / weapon manager, %d byte checks = precheck_02236; LabelCollected / LabelLaraGear 0, live)' % len(rows))


P5_CHECKS_02237 = os.path.join(ROOT, 'work', 'p5_menu_1311', 'precheck_02237.txt')
P5_ROOMS_02237 = os.path.join(ROOT, 'work', 'b_nav_1211', 'q105_room_names.txt')
# 0.22.42 (W3, owner wish 13.11.): DistMetres default 1, its switches row says "TruMenu 0.22.42" (P5_SINCE_02237)
P5_KEYS_02237 = {'KeyItems': '0', 'StyleCollect': 'both', 'StyleKeyItems': 'both', 'StyleNames': 'both',
                 'StyleCheckpoints': 'both', 'StylePortals': 'both', 'LabelRoom': '1', 'DistMetres': '1',
                 'DrawDistance': '0', 'Occlusion': '1', 'HideCo': '1', 'HideFx': '1', 'RoomOnly': '0'}
P5_SINCE_02237 = {'DistMetres': 'TruMenu 0.22.42'}
P5_ITEMS_02237 = (('dbg.keyitems', 'bool', 'ValDvKeyItems', 'RunDvKeyItems'),
                  ('dbg.labelstyle', 'action', 'ValDvLabelStyle', 'RunDvLabelStyle'),
                  ('dbg.room', 'bool', 'ValDvRoom', 'RunDvRoom'), ('dbg.metres', 'bool', 'ValDvMetres', 'RunDvMetres'),
                  ('dbg.drawdist', 'action', 'ValDvDrawDist', 'RunDvDrawDist'),
                  ('dbg.occlusion', 'action', 'ValDvOcclusion', 'RunDvOcclusion'),
                  ('dbg.hideco', 'bool', 'ValDvHideCo', 'RunDvHideCo'), ('dbg.hidefx', 'bool', 'ValDvHideFx', 'RunDvHideFx'),
                  ('dbg.roomonly', 'bool', 'ValDvRoomOnly', 'RunDvRoomOnly'))


def check_02237(ini_path, switches_path):
    """0.22.37 (P5, 13.11.; workspace docs/Befund-P5-Debugansicht-1311.md): kP5Checks = the 6 rows of the offline-checked
    work/p5_menu_1311/precheck_02237.txt; kChapOrder = ALL rows of the generator output q105_chaporder_rows.txt (also the
    7 return visits ", 2}" - CP 76 on the kraken_room return, 160 / 42 in the tomb, going_in 781 / going_out 782);
    kRoomNames = q105_room_names.txt; the reward bit / table, prefix filter, key items and occlusion read only (no game
    write, no game call); LabelFilter: 4 = co_ / fx_, reason 5 = reward bit; the label layers ask P5OcclFactor;
    DpDrawBuffer issues the queries before sb->Apply, DpOnReset releases them; arena.load: QlTick asks LevelChangePending
    before its 100 ms gate and QlForget dumps (0x5c1790) only entries that still carry the id; 12 [Debug] keys with
    defaults (kOpts, TruMenu.ini, switches rows restart); 8 items; bar rows; README 0.22.37 with TO TEST; Set-TruMenu.ps1
    knows the 0.22.36 hash; TruTrace 0.3.2 ProgressFilter default (_rw_, weightbreak, ping_map, grapple)"""
    problems = []
    src = read_cpp()
    if '0.22.37 (debug view P5' not in src[:src.find('\n', src.find('kVersion = '))]:
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.37 part "0.22.37 (debug view P5"')
    offline = []
    if os.path.exists(P5_CHECKS_02237):
        for line in open(P5_CHECKS_02237, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if line:
                addr, hexs = line.split(None, 1)
                offline.append(('%08x' % int(addr, 16), hexs.replace(' ', '').lower()))
    else:
        problems.append('work/p5_menu_1311/precheck_02237.txt (the offline byte list) is missing')
    rows = [(a.lower(), b.lower()) for a, b in sv_rows(src, 'kP5Checks')]
    if rows != offline or len(rows) != 6:
        problems.append('TruMenu.cpp: kP5Checks (%d rows) must be the 6 rows of precheck_02237.txt in order' % len(rows))
    if 'g_p5Ok = g_dvBaseOk && g_coOk && DvChecks(kP5Checks,' not in src:
        problems.append('TruMenu.cpp: g_p5Ok must be g_dvBaseOk && g_coOk && DvChecks(kP5Checks, ...)')
    # kChapOrder: every base row (first visits and return visits) = the generator output
    raw = open(CPP, encoding='utf-8').read()
    order = raw[raw.index('const ChapOrder kChapOrder[] = {'):]
    order = order[:order.index('\n};')]
    pat = r'\{"(Base game l\d)", "(\w+)", false, "([0-9 ]*)",\s*((?:"[^"]*"\s*)+|nullptr)(?:,\s*(\d+))?\}'
    have = [(g, u, c, ''.join(re.findall(r'"([^"]*)"', h)) if h != 'nullptr' else None, v or '1')
            for g, u, c, h, v in re.findall(pat, order)]
    want = []
    for line in open(B_ROWS_02234, encoding='utf-8'):
        m = re.match(r'\s*\{"(Base game l\d)", "(\w+)", false, "([0-9 ]*)", (?:"(.*)"|nullptr)(?:, (\d+))?\},$', line.rstrip())
        if m: want.append((m.group(1), m.group(2), m.group(3), m.group(4), m.group(5) or '1'))
    if have != want or len(want) != 91:
        problems.append('TruMenu.cpp: kChapOrder base rows != q105_chaporder_rows.txt incl. return visits (%d / %d, want 91)'
                        % (len(have), len(want)))
    ret = {u: c for g, u, c, h, v in want if v == '2'}
    first = {u: c for g, u, c, h, v in want if v == '1'}
    if len(ret) != 7 or ret.get('l1_kraken_room') != '76 75' or ret.get('l1_norse_hallway_a') != '782 779':
        problems.append('q105_chaporder_rows.txt: 7 return visits wanted, kraken_room "76 75", norse_hallway_a "782 779"')
    if '76' in first.get('l1_kraken_room', '').split() or first.get('l1_baldrs_tomb') != '140 72 160 42 141' or \
            '781' not in first.get('l1_norse_hallway_a', '').split():
        problems.append('q105_chaporder_rows.txt: Paket R first visits (no 76 in kraken_room, tomb 140 72 160 42 141, 781)')
    if 'int visit; };' not in src or 'co && co->visit > 1 ?' not in fn_body(src, 'int QbChapRows('):
        problems.append('TruMenu.cpp: ChapOrder.visit and the return mark on page Kapitel missing')
    if 'g_chapCpOpen == rowKey' not in fn_body(src, 'int QbChapRows('):
        problems.append('TruMenu.cpp: a return visit row must open its checkpoints alone (row key)')
    # room names = the generator's rooms file
    rooms_want = []
    if os.path.exists(P5_ROOMS_02237):
        rooms_want = [l.strip() for l in open(P5_ROOMS_02237, encoding='utf-8') if l.strip()]
    else:
        problems.append('work/b_nav_1211/q105_room_names.txt is missing')
    m = re.search(r'const P5Room kRoomNames\[\] = \{\n(.*?)\n\};', raw, re.S)
    rooms_have = [l.strip() for l in (m.group(1).split('\n') if m else []) if l.strip()]
    if rooms_have != rooms_want or len(rooms_want) < 84:
        problems.append('TruMenu.cpp: kRoomNames (%d rows) != q105_room_names.txt (%d)' % (len(rooms_have), len(rooms_want)))
    # read only: no game write / game call in the P5 readers and the label paths
    for fn in ('int P5Collected(', 'int P5RewardKind(', 'bool P5PrefixHidden(', 'void P5KeyDraw(', 'void P5KeyLabels(',
               'float P5OcclFactor(', 'void P5OcclIssue(', 'void P5CapUpdate(', 'int P5SymOfName(', 'void P5DrawSymbol('):
        body = fn_body(src, fn)
        if not body: problems.append('TruMenu.cpp: %s missing' % fn.strip('('))
        if any(w in body for w in ('WriteByte(', 'WriteBytes(', 'WriteDword(', 'reinterpret_cast<volatile', 'Fn>(')):
            problems.append('TruMenu.cpp: %s must not write game memory or call the game' % fn.strip('('))
    col = fn_body(src, 'int P5Collected(')
    for need in ('CoKindOf(', 'data + 0x3ed90 + (ri >> 5) * 4', '(word >> (ri & 31)) & 1'):
        if need not in col: problems.append('TruMenu.cpp: P5Collected lacks %s' % need)
    lf = fn_body(src, 'int LabelFilter(')
    if 'if (P5PrefixHidden(inst)) return 4;' not in lf or 'P5Collected(inst)) *reason = 5;' not in lf:
        problems.append('TruMenu.cpp: LabelFilter must return 4 for co_ / fx_ and give reason 5 for the reward bit')
    for fn in ('void DvDrawNames(', 'bool M20Label(', 'void DvTagsDraw(', 'void DrawUberLabels('):
        if 'P5OcclFactor(' not in fn_body(src, fn): problems.append('TruMenu.cpp: %s must ask P5OcclFactor' % fn.strip('('))
    # live wish 13.11.: Lara's room only (uber labels + key items), readable names
    if 'P5RoomOnlyDrops(c.inst)' not in fn_body(src, 'void DrawUberLabels(') or \
            '!P5RoomOnlyDrops(inst)' not in fn_body(src, 'void P5KeyDraw('):
        problems.append('TruMenu.cpp: [Debug] RoomOnly must filter the uber labels and the key items')
    for fn in ('void DrawUberLabels(', 'void P5KeyDraw(', 'void DvDrawNames('):
        if 'P5Readable(name)' not in fn_body(src, fn): problems.append('TruMenu.cpp: %s must show P5Readable' % fn.strip('('))
    if '{"switch_oneway_wall", "Wandschalter (einmalig)", "wall switch (one-way)"},' not in raw or \
            '{"hpole", "Stange (waagrecht)", "pole (horizontal)"},' not in raw or '{"sewer_gate", "Kanaltor", "sewer gate"},' not in raw:
        problems.append('TruMenu.cpp: kP5Readable must hold the owner examples (switch_oneway_wall, hpole, sewer_gate)')
    uc = fn_body(src, 'int UberCollect(')
    if 'roomOnly && P5RoomOnlyDrops(inst)' not in uc or 'strstr(name, "_uo_") || strstr(name, "_ei_") || strstr(name, "_pt_")' not in uc:
        problems.append('TruMenu.cpp: UberCollect with roomOnly must keep Lara\'s room and take every _uo_ / _ei_ / _pt_ object')
    if 'UberCollect(g_ubCand, max, lara, player, &g_ubFound, g_p5RoomOnly != 0)' not in fn_body(src, 'void DrawUberLabels('):
        problems.append('TruMenu.cpp: DrawUberLabels must pass [Debug] RoomOnly to UberCollect')
    for fn in ('void DrawLabels(', 'void DvDrawNames(', 'void P5KeyDraw('):   # hidden helpers: "versteckt", not "eingesammelt"
        if 'P5IsReward(' not in fn_body(src, fn) or 'LabelHiddenText()' not in fn_body(src, fn):
            problems.append('TruMenu.cpp: %s must say "versteckt" for a hidden instance that is no collectible' % fn.strip('('))
    db = fn_body(src, 'void DpDrawBuffer(')
    if not (0 <= db.find('P5OcclIssue(dev, c, b);') < db.find('sb->Apply();')):
        problems.append('TruMenu.cpp: DpDrawBuffer must issue the occlusion queries before sb->Apply')
    if 'P5OcclRelease();' not in fn_body(src, 'void DpOnReset('):
        problems.append('TruMenu.cpp: DpOnReset must release the occlusion queries')
    # arena.load: release at the level change
    qt = fn_body(src, 'void QlTick(')
    if not (0 <= qt.find('if (LevelChangePending(why, sizeof(why))) { QlForget(why); return; }') < qt.find('now - last < 100')):
        problems.append('TruMenu.cpp: QlTick must ask LevelChangePending before its 100 ms gate')
    if 'if (unit != g_qlUnit) g_qlUnit = unit;' not in qt:
        problems.append('TruMenu.cpp: a portal move (same player) must keep the arena.load list')
    qf = fn_body(src, 'void QlForget(')
    if 'static_cast<SHORT>(id) == q.id' not in qf or 'QlDumpOne(q.id)' not in qf:
        problems.append('TruMenu.cpp: QlForget must dump with 0x5c1790 only entries that still carry the id')
    # keys, items, bar, switches, README, Set-TruMenu, TruTrace
    header, opt_rows = table(src)
    keys = {(s, k): d for s, k, d, _ in opt_rows}
    ini = open(ini_path, encoding='utf-8').read().replace('\r\n', '\n')
    for k, d in P5_KEYS_02237.items():
        if keys.get(('Debug', k)) != d: problems.append('TruMenu.cpp: kOpts [Debug] %s must default to %s' % (k, d))
        if '\n%s=%s\n' % (k, d) not in ini: problems.append('%s: [Debug] %s=%s missing' % (os.path.basename(ini_path), k, d))
    for item, typ, val, run in P5_ITEMS_02237:
        if not re.search(r'\{"%s", "%s", .*?,\s+false,\s+%s,\s+%s\}' % (re.escape(item), typ, val, run), src, re.S):
            problems.append('TruMenu.cpp: item %s (%s, %s / %s) missing' % (item, typ, val, run))
        if not re.search(r'\{"%s", "[*]?", "' % re.escape(item), src): problems.append('TruMenu.cpp: bar help row %s missing' % item)
    if '"dbg.keyitems", "", kQbBool, kDvKeyItems, kQcLayer, 0, 0}' not in src:
        problems.append('TruMenu.cpp: bar row Schluesselgegenstaende (dbg.keyitems, page Level data) missing')
    if 'P5MenuControls(o, sizeof(o));' not in src: problems.append('TruMenu.cpp: menu controls (page Debug view) missing')
    sw = [l.rstrip('\r\n').split(' | ') for l in open(switches_path, encoding='utf-8') if l.startswith('TruMenu | Debug | ')]
    got = {f[2]: f for f in sw if len(f) >= 10 and f[9] == P5_SINCE_02237.get(f[2], 'TruMenu 0.22.37')}
    for k, d in P5_KEYS_02237.items():
        f = got.get(k)
        if not f or f[6] != 'restart' or f[7] != d:
            problems.append('%s: row TruMenu | Debug | %s | ... | restart | %s | ... | %s missing'
                            % (os.path.basename(switches_path), k, d, P5_SINCE_02237.get(k, 'TruMenu 0.22.37')))
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8').read()
    if '\n## 0.22.37 - ' not in readme or '\n### TO TEST 0.22.37' not in readme:
        problems.append('README.md: section "## 0.22.37 - ..." with "### TO TEST 0.22.37" missing')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if '1648a83dde7feb4033220d6f4c101ba1a2dd3b8e5fe1c3dc651459b62802a09a' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.36 build hash (work/asi/menu0259) is missing')
    tt = open(os.path.join(ROOT, 'src', 'asi', 'TruTrace', 'TruTrace.cpp'), encoding='utf-8').read()
    tini = open(os.path.join(ROOT, 'src', 'asi', 'TruTrace', 'TruTrace.ini'), encoding='utf-8').read()
    filt = 'checkpoint,breakwall,trigger,door,gate,lever,plate,switch,spawner,_rw_,weightbreak,ping_map,grapple'
    if 'const char kVersion[] = "TruTrace 0.3.2";' not in tt or '\nProgressFilter=%s\n' % filt not in tini.replace('\r\n', '\n'):
        problems.append('TruTrace: 0.3.2 with the ProgressFilter default %s (source + sample .ini) wanted' % filt)
    # TruTrace 0.3.2 [Ground]: the kCatGround facts = work/p5_menu_1311/precheck_trace032.txt, Ground=1 in the sample .ini
    gpath = os.path.join(ROOT, 'work', 'p5_menu_1311', 'precheck_trace032.txt')
    gwant = []
    if os.path.exists(gpath):
        for line in open(gpath, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if line:
                addr, hexs = line.split(None, 1)
                gwant.append(('%08x' % int(addr, 16), hexs.replace(' ', '').lower()))
    ghave = [(a.lower(), ''.join(LIT.findall(b)).replace(' ', '').lower()) for a, b in
             re.findall(r'\{kCatGround, 0x([0-9a-fA-F]{8}), ((?:"[0-9a-f ]+"\s*)+)\}', tt)]
    if ghave != gwant or len(gwant) != 6 or '\nGround=1\n' not in tini.replace('\r\n', '\n'):
        problems.append('TruTrace: kCatGround facts (%d) must be the 6 rows of precheck_trace032.txt, Ground=1 in the .ini' % len(ghave))
    tf = re.search(r'#define TRUTRACE_PROG_FILTER ((?:"[^"]*"\s*\\?\s*)+)', tt)
    if not tf or ''.join(re.findall(r'"([^"]*)"', tf.group(1))) != filt:
        problems.append('TruTrace.cpp: TRUTRACE_PROG_FILTER must be %s' % filt)
    return problems, ('debug view P5 (%d byte checks = precheck_02237; kChapOrder %d base rows = generator incl. %d return '
                      'visits; %d room names; %d keys, %d items; arena.load release at the level change; TruTrace 0.3.2 '
                      'filter)' % (len(rows), len(want), len(ret), len(rooms_want), len(P5_KEYS_02237), len(P5_ITEMS_02237)))


PD_KEYS_02238 = {('Debug', 'TriggerNearest'): '0', ('Debug', 'TriggerCornerId'): '1', ('Input', 'DeviceGlyphs'): '1'}
PD_ITEMS_02238 = (('dbg.trignear', 'action', 'ValDvTrigNear', 'RunDvTrigNear'),
                  ('dbg.trigcorner', 'bool', 'ValDvTrigCorner', 'RunDvTrigCorner'))
PD_LISTS_02238 = os.path.join(ROOT, 'work', 'generic', 'lists')


def pd_prefix_kind(low):
    """Python copy of P5PrefixKind (0.22.38): 1 co_, 2 fx_, 3 neither / an exception"""
    m = re.match(r'dlc[0-9]*_', low)
    s = low[m.end():] if m else low
    if s.startswith('co_') and not s.startswith('co_rock'): return 1
    if s.startswith('fx_') and '_grab_prompt' not in s: return 2
    return 3


def check_02238(ini_path, switches_path):
    """0.22.38 (PD, 13.11.; workspace docs/Befund-TruMenu-02238-1311.md): [Input] DeviceGlyphs default 1 (kOpts, INI,
    switches row restart 1); P5PrefixKind skips "dlc_" / "dlc<digits>_" before the co_ / fx_ rule (exceptions co_rock*,
    *_grab_prompt) and P5PrefixHidden uses it - the Python copy run over the real object lists of work/generic/lists
    (dlc_fx_* / dlc1_fx_* hidden, co_rock* / fx_saving_grab_prompt kept); trigger edges: DpLine.edge from DvEdgeBegin /
    DvLine, the trigger loop keys both passes, a sphere circle is one key, DpDrawBuffer draws PdEdgeHow 1 whole without
    the depth test (g_dpAlways) and issues the query pairs before sb->Apply, PdEdgeHow is 0 with Occlusion 0, DpOnReset
    releases the pairs, the PD functions read only; [Debug] TriggerNearest / TriggerCornerId (kOpts, INI, switches rows
    restart), items + bar rows + help rows, ReadOptions / load call PdReadOptions / PdCheck; README 0.22.38 with TO TEST;
    Set-TruMenu.ps1 knows the 0.22.37 hash"""
    problems = []
    src = read_cpp()
    if '0.22.38 (PD' not in src[:src.find('\n', src.find('kVersion = '))]:
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.38 part "0.22.38 (PD"')
    header, opt_rows = table(src)
    keys = {(s, k): d for s, k, d, _ in opt_rows}
    ini = open(ini_path, encoding='utf-8').read().replace('\r\n', '\n')
    for (sec, k), d in PD_KEYS_02238.items():
        if keys.get((sec, k)) != d: problems.append('TruMenu.cpp: kOpts [%s] %s must default to %s' % (sec, k, d))
        if '\n%s=%s\n' % (k, d) not in ini: problems.append('%s: [%s] %s=%s missing' % (os.path.basename(ini_path), sec, k, d))
    sw = [l.rstrip('\r\n').split(' | ') for l in open(switches_path, encoding='utf-8') if l.startswith('TruMenu | ')]
    got = {(f[1], f[2]): f for f in sw if len(f) >= 10 and f[9] == 'TruMenu 0.22.38'}
    for (sec, k), d in PD_KEYS_02238.items():
        f = got.get((sec, k))
        if not f or f[6] != 'restart' or f[7] != d:
            problems.append('%s: row TruMenu | %s | %s | ... | restart | %s | ... | TruMenu 0.22.38 missing'
                            % (os.path.basename(switches_path), sec, k, d))
    # co_ / fx_ after dlc_ / dlc<n>_
    pk = fn_body(src, 'int P5PrefixKind(')
    for need in ('if (!strncmp(s, "dlc", 3)) {', "while (*p >= '0' && *p <= '9') ++p;", "if (*p == '_') s = p + 1;",
                 'if (!strncmp(s, "co_", 3) && strncmp(s, "co_rock", 7)) return 1;',
                 'if (!strncmp(s, "fx_", 3) && !strstr(s, "_grab_prompt")) return 2;'):
        if need not in pk: problems.append('TruMenu.cpp: P5PrefixKind lacks %s' % need)
    if 'k = P5PrefixKind(low);' not in fn_body(src, 'bool P5PrefixHidden('):
        problems.append('TruMenu.cpp: P5PrefixHidden must use P5PrefixKind')
    names = set()
    for path in glob.glob(os.path.join(PD_LISTS_02238, '*objectlist.txt')):
        for line in open(path, encoding='latin1').read().splitlines()[1:]:
            if ',' in line: names.add(line.split(',', 1)[1].strip().lower())
    dlcfx = [n for n in names if re.match(r'dlc[0-9]*_fx_', n)]
    if names and (len(names) < 1000 or len(dlcfx) < 70):   # work/generic is gitignored: no lists = this part skipped
        problems.append('work/generic/lists: object names not readable (%d names, %d dlc*_fx_*)' % (len(names), len(dlcfx)))
    if any(pd_prefix_kind(n) != 2 for n in dlcfx): problems.append('prefix rule: a dlc*_fx_* name is not hidden')
    for keep in ('co_rock', 'co_rock_b', 'fx_saving_grab_prompt', 'dlc1_uo_sewer_gate', 'dlc_dispatcher'):
        if pd_prefix_kind(keep) != 3: problems.append('prefix rule: %s must stay labelled' % keep)
    # trigger edges: keys, both passes, sphere circles, the faded batch, query pairs, reset
    if 'float thick; int dashed; DWORD edge; };' not in src or 'l.edge = g_dvEdgeKey;' not in fn_body(src, 'void DpPushLine('):
        problems.append('TruMenu.cpp: DpLine.edge / DpPushLine must carry the edge key')
    if 'if (g_dvEdgeBase) g_dvEdgeKey = DvEdgeKeyOf(g_dvEdgeBase, g_dvEdgeSeg++ / g_dvEdgeRun);' not in fn_body(src, 'bool DvLine('):
        problems.append('TruMenu.cpp: DvLine must number the edges (also behind the camera)')
    dv = fn_body(src, 'void DrawDebugView(')
    i0, i1 = dv.find('DvEdgeBegin(t.inst, 0);'), dv.find('DvEdgeBegin(t.inst, 1);')
    i2 = dv.find('DvDrawTrig(dl, c, t, colour, thick, fill, &at, &seen);')
    if not (0 <= i0 < i1 < i2) or dv.count('DvEdgeEnd();') < 2:
        problems.append('TruMenu.cpp: DrawDebugView must key both trigger passes (DvEdgeBegin 0 / 1 ... DvEdgeEnd)')
    if 'if (g_pdTrigNear > 0 && !t.laraIn) {' not in dv or 'PdCornerDraw(dl, c, t.inst, colour);' not in dv:
        problems.append('TruMenu.cpp: DrawDebugView lacks TriggerNearest / the corner id')
    dt = fn_body(src, 'void DvDrawTrig(')
    if 'g_dvEdgeRun = 24;' not in dt or 'g_dvEdgeRun = 1;' not in dt:
        problems.append('TruMenu.cpp: a sphere circle (24 segments) must be one edge key')
    db = fn_body(src, 'void DpDrawBuffer(')
    i_how, i_alw, i_iss, i_app = (db.find('PdEdgeHow(b.line[i].edge)'), db.find('g_dpAlways = true;'),
                                  db.find('PdEdgeIssue(dev, c, b, fw, fh);'), db.find('sb->Apply();'))
    if not (0 <= i_how < i_alw < i_iss < i_app) or 'l.colour = PdEdgeFaded(l.colour);' not in db or \
            'g_dpAlways = false;' not in db:
        problems.append('TruMenu.cpp: DpDrawBuffer must draw PdEdgeHow 1 faded without the depth test, then issue the pairs '
                        'before sb->Apply')
    fl = fn_body(src, 'void DpFlush(')
    if 'if (g_dpAlways) {' not in fl or 'D3DCMP_ALWAYS' not in fl:
        problems.append('TruMenu.cpp: DpFlush lacks the g_dpAlways branch (ZFUNC ALWAYS)')
    how = fn_body(src, 'int PdEdgeHow(')
    if 'if (!key || !g_p5Occl || g_pdQFailed) return 0;' not in how or 'return g_p5Occl == 2 ? 2 : 1;' not in how:
        problems.append('TruMenu.cpp: PdEdgeHow must be 0 without a key / with Occlusion 0 and drop only with Occlusion 2')
    if 'PdEdgeRelease();' not in fn_body(src, 'void DpOnReset('):
        problems.append('TruMenu.cpp: DpOnReset must release the edge query pairs')
    iss = fn_body(src, 'void PdEdgeIssue(')
    if 'D3DRS_COLORWRITEENABLE, 0' not in iss or 'vis + 2 + all / 32 >= all' not in iss:
        problems.append('TruMenu.cpp: PdEdgeIssue must ask without colour and compare all / visible pixels')
    for fn in ('void PdEdgeIssue(', 'int PdEdgeHow(', 'void PdCornerDraw(', 'int PdLookup(', 'void PdStore(',
               'int P5PrefixKind('):
        body = fn_body(src, fn)
        if not body: problems.append('TruMenu.cpp: %s missing' % fn.strip('('))
        if any(w in body for w in ('WriteByte(', 'WriteBytes(', 'WriteDword(', 'reinterpret_cast<volatile', 'Fn>(')):
            problems.append('TruMenu.cpp: %s must not write game memory or call the game' % fn.strip('('))
    # items, bar, options, load
    for item, typ, val, run in PD_ITEMS_02238:
        if not re.search(r'\{"%s", "%s", .*?,\s+false,\s+%s,\s+%s\}' % (re.escape(item), typ, val, run), src, re.S):
            problems.append('TruMenu.cpp: item %s (%s, %s / %s) missing' % (item, typ, val, run))
        if not re.search(r'\{"%s", "[*]?", "' % re.escape(item), src): problems.append('TruMenu.cpp: bar help row %s missing' % item)
        if not re.search(r'"%s", "[^"]*", kQb(Bool|Action), -1' % re.escape(item), src):
            problems.append('TruMenu.cpp: bar row %s missing' % item)
    if 'PdReadOptions(ini);' not in src or not re.search(r'\n    P5Check\(\);[^\n]*\n[^\n]*\n    PdCheck\(\);', src):
        problems.append('TruMenu.cpp: ReadOptions must call PdReadOptions and the load PdCheck after P5Check')
    if 'PdMenuControls(o, sizeof(o));' not in src: problems.append('TruMenu.cpp: menu controls 0.22.38 missing')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8').read()
    if '\n## 0.22.38 - ' not in readme or '\n### TO TEST 0.22.38' not in readme:
        problems.append('README.md: section "## 0.22.38 - ..." with "### TO TEST 0.22.38" missing')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if '8f2f6b2a99e172c624ca56258e8d973e0cb3cb0ddcf16addc5bd7388779f5c3f' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.37 build hash (work/asi/menu0260) is missing')
    lists = ('%d object names, %d dlc*_fx_* hidden' % (len(names), len(dlcfx)) if names
             else 'object lists not present - name test skipped')
    return problems, ('PD (DeviceGlyphs 1; co_ / fx_ after dlc_ / dlc<n>_: %s; trigger edges whole + faded by query '
                      'pairs; %d keys, %d items)' % (lists, len(PD_KEYS_02238), len(PD_ITEMS_02238)))


AT_KEYS_02239 = (('AttractIcon', '1'), ('AttractIconText', '1'))


def check_02239(ini_path, switches_path):
    """0.22.39 (Q126, owner idea 13.11.; workspace docs/Befund-AttractIcon-1311.md): menu.attracticon ([Menu] AttractIcon
    default 1, [Menu] AttractIconText default 1, both re-read about once a second by AtReadSwitch from NaTick = live
    switches rows in group "Hauptmenue (TruMenu)"): the game's AttractTimer values - elapsed / alarm of the clock captured
    at the f11 native, with NoAttract holding the shadow modulo the alarm - read through the 0.22.20 update slot (NaTick
    patches it for hold || line || icon; nothing new is written), AtOnLimit from NtPost counts skipped / started and sets
    the blink; drawn only in the front end, below the timer box when that is top right; item / bar row / help / greying;
    the icon functions read only TruMenu's own variables; README 0.22.39 with TO TEST; Set-TruMenu knows the 0.22.38 hash.
    0.22.40 (Q126b): the keys / default, the switches row, ReadOptions / AtReadSwitch, RunAt's values, the item type and the
    bar row kind moved to check_02240 (AttractIcon 0 .. 7, AttractIconText gone); the rest stays checked here"""
    problems = []
    src = read_cpp()
    if '0.22.39 (Q126 attract icon' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.40: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.39 part "0.22.39 (Q126 attract icon"')
    groups = [l.rstrip('\r\n') for l in open(switches_path, encoding='utf-8') if l.startswith('group | tmhauptmenue | ')]
    if len(groups) != 1: problems.append('%s: group tmhauptmenue missing' % os.path.basename(switches_path))
    if 'AtReadSwitch();' not in fn_body(src, 'void AtTick('):
        problems.append('TruMenu.cpp: AtTick must call AtReadSwitch')
    if 'if (g_atReadTick && now - g_atReadTick < 1000) return;' not in fn_body(src, 'void AtTick('):
        problems.append('TruMenu.cpp: AtTick must read the INI at most once a second')
    tick = fn_body(src, 'void NaTick(')
    i_ai, i_want = tick.find('AtTick();'), tick.find('want = hold || g_ntWant != 0 || g_atWant != 0;')
    if not (0 <= i_ai < i_want): problems.append('TruMenu.cpp: NaTick must call AtTick and patch the slot for the icon too')
    post = fn_body(src, 'void NtPost(')
    i_lim, i_ret = post.find('if (flash) AtOnLimit(held);'), post.find('if (!flash || !g_ntWant) return;')
    if not (0 <= i_lim < i_ret): problems.append('TruMenu.cpp: NtPost must call AtOnLimit(held) before the timer line return')
    lim = fn_body(src, 'void AtOnLimit(')
    for want in ('InterlockedIncrement(held ? &g_atSkipped : &g_atStarted);', 'g_atBlinkTick = GetTickCount() | 1;',
                 'Log(1, "menu.attracticon: limit '):
        if want not in lim: problems.append('TruMenu.cpp: AtOnLimit must hold %s' % want)
    fr = fn_body(src, 'float AtFraction(')
    for want in ('const float alarm = g_naAlarm;', 'if (!g_naClock || !g_ntClock || !(alarm > 0.0f)) return -1.0f;',
                 'float e = held ? g_ntShadow : g_ntReal;', 'g_naRepeat ? fmodf(e, alarm)'):
        if want not in fr: problems.append('TruMenu.cpp: AtFraction must hold %s' % want)
    # 0.22.42 (W3): && W3AtMainMenu() appended (main menu only, not in the credits) - check_02242 tests that part
    if 'bool AtWantsDraw() { return g_atWant != 0 && NaFrontEnd()' not in src:
        problems.append('TruMenu.cpp: AtWantsDraw must be g_atWant && NaFrontEnd (front end only)')
    rnd = fn_body(src, 'void Render(')
    i_nt, i_ai2 = rnd.find('if (ntDraw) DrawNt();'), rnd.find('if (atDraw) DrawAt(ntDraw);')
    if 'const bool atDraw = AtWantsDraw();' not in rnd or '!atDraw && !cnBadge && !ntDraw)' not in rnd or not (0 <= i_nt < i_ai2):
        problems.append('TruMenu.cpp: Render must compute atDraw, keep ImGui on for it and draw DrawAt after DrawNt')
    if 'g_ntBoxH = ImGui::GetWindowSize().y;' not in fn_body(src, 'void DrawNt('):
        problems.append('TruMenu.cpp: DrawNt must note its box height (the icon goes below it)')
    draw = fn_body(src, 'void DrawAt(')
    if not draw.split('\n')[2:3] == ['    const bool de = g_qbLang == 0;']:
        problems.append('TruMenu.cpp: DrawAt must start with const bool de = g_qbLang == 0; (the bar language)')
    rest = re.sub(r'de\s*\?\s*' + NT_LITSEQ + r'\s*:\s*' + NT_LITSEQ, '', draw)
    left = [unescape(x) for x in re.findall(r'"((?:[^"\\]|\\.)*)"', rest)]
    single = [t for t in left if re.search(r'[A-Za-z]{2}', re.sub(r'%[-.0-9]*[a-z]+', '', t)) and t != '##TruAttractIcon']
    if single: problems.append('TruMenu.cpp: DrawAt texts without a de / en pair: %s' % ', '.join(single))
    for want in ('const bool blinking = blinkAt && now - blinkAt < kAtBlinkMs;', 'g_ntPos == 2 && g_ntBoxH > 0.0f',
                 'AtSector(dl, c, r, a, a + kPi * 0.5f < a1 ? a + kPi * 0.5f : a1, fill);',
                 'bersprungen %ld" : "skipped %ld"', 'NaWhy();'):   # read_cpp turns the umlaut escape into ue
        # 0.22.40: 'if (g_atText) {' became the style switch (check_02240)
        if want not in draw: problems.append('TruMenu.cpp: DrawAt must hold %s' % want)
    if 'const DWORD kAtBlinkMs = 1200, kAtBlinkPhaseMs = 200;' not in src:
        problems.append('TruMenu.cpp: kAtBlinkMs 1200 / kAtBlinkPhaseMs 200 missing')
    for fn in ('void AtOnLimit(', 'void AtReadSwitch(', 'void AtTick(', 'float AtFraction(', 'void AtSector(',
               'void DrawAt(', 'void ValAt('):
        body = fn_body(src, fn)
        if not body: problems.append('TruMenu.cpp: %s missing' % fn.strip('(')); continue
        if any(w in body for w in ('reinterpret_cast<', 'WriteByte(', 'WriteBytes(', 'WriteDword(', 'LcPatch(', 'Fn>(')):
            problems.append('TruMenu.cpp: %s must read only TruMenu\'s own values (no game memory, no game call)'
                            % fn.strip('('))
    # item: no argument = report (never a flip); 0.22.40: type, values, INI write and bar row kind in check_02240
    run = fn_body(src, 'bool RunAt(')
    if 'if (!arg || !arg[0]) { ValAt(o, n); return true; }' not in run:
        problems.append('TruMenu.cpp: RunAt must report without an argument')
    if 'BoolArg(' in run: problems.append('TruMenu.cpp: RunAt must not use BoolArg (an empty argument would flip)')
    if 'if (!_stricmp(id, "menu.attracticon")) return NaWhy();' not in fn_body(src, 'const char *RadialWhy('):
        problems.append('TruMenu.cpp: RadialWhy must grey menu.attracticon with NaWhy')
    hm =re.search(r'\{"menu\.attracticon", "", "((?:[^"\\]|\\.)*)"\s*"((?:[^"\\]|\\.)*)"\}', src)
    if not hm: problems.append('TruMenu.cpp: kQbHelp row menu.attracticon missing')
    else:
        de, en = unescape(hm.group(1) + hm.group(2)).split('|')
        if len(de) > 60 or len(en) > 60: problems.append('TruMenu.cpp: menu.attracticon help over 60 characters')
    m = re.search(r'const DvCheck kNaChecks\[\] = \{(.*?)\n\};', src, re.S)
    if not m or len(re.findall(r'\{0x[0-9a-f]{8}, "[0-9a-f ]+"\}', m.group(1))) != 13:
        problems.append('TruMenu.cpp: kNaChecks must stay 13 rows (no new byte checks for the icon)')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8').read()
    if '\n## 0.22.39 - ' not in readme or '\n### TO TEST 0.22.39' not in readme:
        problems.append('README.md: section "## 0.22.39 - ..." with "### TO TEST 0.22.39" missing')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if '0246bd14f4c26d0bbc370587e44d8398c646138fafab85d325109e6a0eed758e' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.38 build hash (work/asi/menu0261) is missing')
    return problems, ('attract icon (Q126): the game\'s clock values through the 0.22.20 slot, AtOnLimit counts + '
                      'blink, front end only, help / greying (keys / row / item: check_02240)')


AT_DEFAULT = '12'   # 0.22.48 (owner 2026-11-14): [Menu] AttractIcon default 12 (0.22.40 .. 0.22.47: 7)
AT_STYLES_02240 = (('Aus', 'off'), ('Nur Text', 'text only'), ('Kreis', 'circle'), ('Kreis + Strich', 'circle + strike'),
                   ('Kreis, Text innen', 'circle, text inside'), ('Kreis, Text unten', 'circle, text below'),
                   ('Kreis + Strich, Text innen', 'circle + strike, text inside'),
                   ('wie 0.22.39 (Text links)', 'as 0.22.39 (text left)'))
# circle, strike, text place of the 8 styles (owner Q126b: 1 text, 2 no strike, 3 strike, 4 inside, 5 below, 6 = 4 +
# strike; 7 = the 0.22.39 look, the default)
AT_SHAPES_02240 = (('0', '0', 'kAtTextNone'), ('0', '0', 'kAtTextOnly'), ('1', '0', 'kAtTextNone'),
                   ('1', '1', 'kAtTextNone'), ('1', '0', 'kAtTextInside'), ('1', '0', 'kAtTextBelow'),
                   ('1', '1', 'kAtTextInside'), ('1', '1', 'kAtTextLeft'))


def check_02240(ini_path, switches_path):
    """0.22.40 (Q126b, owner 13.11.; workspace docs/Befund-AttractIcon-Varianten-1311.md): one cycle switch [Menu]
    AttractIcon 0 .. 7 (default 7 = the 0.22.39 look) instead of AttractIcon 0 / 1 + AttractIconText: kOpts / INI /
    switches row (int:0..7, live via AtStyleRead from AtReadSwitch), AttractIconText gone everywhere except the one-time
    mapping of a 0.22.39 INI (0 -> 0, 1 + 1 -> 7, 1 + 0 -> 3; key removed); the style table (8 rows, DE / EN names, circle /
    strike / text place); DrawAt draws by the style (text only returns before the circle, the strike only for strike
    styles, text inside / below / left); item menu.attracticon "value" 0..7 (one digit or off, else usage; the old key
    removed before the write); bar row kQbValue kQvAtStyle after menu.attracttimer with the style name (ItemValueShort);
    kVersion 0.22.40; README 0.22.40 with TO TEST; Set-TruMenu knows the 0.22.39 hash.
    0.22.41 (Q126c): the range (0 .. 16, kAtStyleN 17), the switches row type / version, the two-digit parse in RunAt and
    the item text moved to check_02241; the first 8 table rows and everything else stay checked here"""
    problems = []
    src = read_cpp()
    if '0.22.40 (Q126b attract display styles' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.41: later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.40 part "0.22.40 (Q126b attract display styles"')
    # keys: one key, default 7 (0.22.48: AT_DEFAULT 12); AttractIconText only in AtStyleRead / RunAt (the 0.22.39 mapping)
    # and comments / texts
    if not re.search(r'\{"Menu", "AttractIcon", "%s",' % AT_DEFAULT, src):
        problems.append('TruMenu.cpp: kOpts [Menu] AttractIcon must be "%s"' % AT_DEFAULT)
    if re.search(r'\{"Menu", "AttractIconText",', src): problems.append('TruMenu.cpp: kOpts [Menu] AttractIconText must be gone')
    if 'g_atText' in src: problems.append('TruMenu.cpp: g_atText must be gone (the style replaces it)')
    code = re.sub(r'//[^\n]*', '', src)
    uses = [m.start() for m in re.finditer(r'"AttractIconText"', code)]
    sr, ra = fn_body(code, 'LONG AtStyleRead('), fn_body(code, 'bool RunAt(')
    if len(uses) != sr.count('"AttractIconText"') + ra.count('"AttractIconText"') or sr.count('"AttractIconText"') != 2 \
            or ra.count('"AttractIconText"') != 1:
        problems.append('TruMenu.cpp: "AttractIconText" only in AtStyleRead (read + remove) and RunAt (remove)')
    ini = open(ini_path, encoding='utf-8').read().replace('\r\n', '\n')
    block = re.search(r'^\[Menu\]\n(.*?)(?=^\[|\Z)', ini, re.M | re.S)
    if not block or not re.search(r'^AttractIcon=%s$' % AT_DEFAULT, block.group(1), re.M):
        problems.append('%s: [Menu] AttractIcon=%s missing' % (os.path.basename(ini_path), AT_DEFAULT))
    if re.search(r'^AttractIconText=', ini, re.M): problems.append('%s: AttractIconText must be gone' % os.path.basename(ini_path))
    sw = [l.rstrip('\r\n').split(' | ') for l in open(switches_path, encoding='utf-8') if l.startswith('TruMenu | Menu | ')]
    f = [x for x in sw if len(x) >= 10 and x[2] == 'AttractIcon']
    if not f or not f[0][3].startswith('int:0..') or f[0][6] != 'live' or f[0][7] != AT_DEFAULT:   # 0.22.41: range in check_02241
        problems.append('%s: row TruMenu | Menu | AttractIcon | int:0..<n> | ... | live | %s | ... missing'
                        % (os.path.basename(switches_path), AT_DEFAULT))
    if [x for x in sw if len(x) >= 3 and x[2] == 'AttractIconText']:
        problems.append('%s: row AttractIconText must be gone' % os.path.basename(switches_path))
    # the style table
    m = re.search(r'const AtStyleDef kAtStyles\[\] = \{(.*?)\};', src, re.S)
    rows = re.findall(r'\{(\d), (\d), (kAtText[A-Za-z]+), "((?:[^"\\]|\\.)*)", "((?:[^"\\]|\\.)*)"\}', m.group(1)) if m else []
    if len(rows) < 8: problems.append('TruMenu.cpp: kAtStyles must hold the 8 rows of 0.22.40 first (got %d)' % len(rows))
    else:                                    # 0.22.41: rows 8 .. 16 in check_02241
        for i, (row, shape, names) in enumerate(zip(rows, AT_SHAPES_02240, AT_STYLES_02240)):
            if row[:3] != shape: problems.append('TruMenu.cpp: kAtStyles[%d] must be %s (got %s)' % (i, shape, row[:3]))
            if (unescape(row[3]), row[4]) != names:
                problems.append('TruMenu.cpp: kAtStyles[%d] names must be %s / %s' % (i, names[0], names[1]))
            if len(names[0]) > 40 or len(names[1]) > 40: problems.append('kAtStyles[%d]: name over 40 characters' % i)
    if not re.search(r'const int kAtStyleN = \d+, kAtStyleDefault = %s;' % AT_DEFAULT, src):   # 0.22.41: N in check_02241
        problems.append('TruMenu.cpp: kAtStyleN / kAtStyleDefault %s missing' % AT_DEFAULT)
    if 'return kAtStyles[s >= 0 && s < kAtStyleN ? s : kAtStyleDefault];' not in fn_body(src, 'const AtStyleDef &AtStyleOf('):
        problems.append('TruMenu.cpp: AtStyleOf must clamp to the default')
    # reading: the INI value, the 0.22.39 mapping, the range; migrate only from AtReadSwitch
    sr = fn_body(src, 'LONG AtStyleRead(')
    for want in ('GetPrivateProfileIntA("Menu", "AttractIcon", def, ini)',
                 'GetPrivateProfileStringA("Menu", "AttractIconText", "", old, sizeof(old), ini);',
                 'const int mapped = v == 0 ? 0 : v == 1 ? (text ? 7 : 3) : v;',
                 'WritePrivateProfileStringA("Menu", "AttractIconText", nullptr, ini)',
                 'if (v < 0 || v >= kAtStyleN) { *bad = true; v = def; }'):
        if want not in sr: problems.append('TruMenu.cpp: AtStyleRead must hold %s' % want)
    if not re.search(r'if \(migrate\) \{', sr): problems.append('TruMenu.cpp: AtStyleRead may write only with migrate')
    rd = fn_body(src, 'void AtReadSwitch(')
    for want in ('AtStyleRead(g_iniPath, true, &bad, &raw);', 'if (style != g_atIniOn) {',
                 'InterlockedExchange(&g_atStyle, style);', 'InterlockedExchange(&g_atWant, style ? 1 : 0);'):
        if want not in rd: problems.append('TruMenu.cpp: AtReadSwitch must hold %s' % want)
    ro = fn_body(src, 'void ReadOptions(')
    for want in ('AtStyleRead(ini, false, &bad, &raw);', 'InterlockedExchange(&g_atStyle, style);',
                 'InterlockedExchange(&g_atWant, style ? 1 : 0);'):
        if want not in ro: problems.append('TruMenu.cpp: ReadOptions must hold %s' % want)
    # drawing by the style
    draw = fn_body(src, 'void DrawAt(')
    for want in ('const AtStyleDef &st = AtStyleOf(g_atStyle);',
                 'if (why[0] && textAt == kAtTextInside) textAt = kAtTextBelow;', 'if (!st.circle) {',
                 'if (textAt == kAtTextLeft) {', 'const bool textBelow = textAt == kAtTextBelow;', 'if (held && st.strike)',
                 'if (inside) {', 'd = fs * 6.0f > need ? fs * 6.0f : need;'):
        if want not in draw: problems.append('TruMenu.cpp: DrawAt must hold %s' % want)
    i_only, i_ret, i_circle = draw.find('if (!st.circle) {'), draw.find('return;'), draw.find('AddCircleFilled(')
    if not (0 <= i_only < i_ret < i_circle): problems.append('TruMenu.cpp: DrawAt style 1 must return before the circle')
    if draw.count('ImGui::End();') != 2 or draw.count('if (lit) ImGui::PopStyleColor();') != 2:
        problems.append('TruMenu.cpp: DrawAt must End / pop the colour on both paths')
    if 'if (held) dl->AddLine(' in draw: problems.append('TruMenu.cpp: DrawAt must strike only in strike styles')
    for fn in ('LONG AtStyleRead(', 'const AtStyleDef &AtStyleOf(', 'void AtReadSwitch(', 'void DrawAt(', 'bool RunAt('):
        body = fn_body(src, fn)
        if any(w in body for w in ('reinterpret_cast<', 'WriteByte(', 'WriteBytes(', 'WriteDword(', 'LcPatch(', 'Fn>(')):
            problems.append('TruMenu.cpp: %s must not touch game memory' % fn.strip('('))
    # item, bar row, help, value helpers
    # 0.22.41: the item text "0.22.41 0..16" and the two-digit parse are checked in check_02241
    if not re.search(r'\{"menu\.attracticon", "value", "0\.22\.4\d 0\.\.\d+ .*?,\s+false, ValAt, RunAt\}', src, re.S):
        problems.append('TruMenu.cpp: item menu.attracticon ("value", "0.22.4x 0..n ...", ValAt / RunAt) missing')
    run = fn_body(src, 'bool RunAt(')
    for want in ('if (!arg || !arg[0]) { ValAt(o, n); return true; }',
                 'else if (!_stricmp(arg, "off")) v = 0;', 'if (v < 0 || v >= kAtStyleN) {', 'usage: menu.attracticon 0..%d',
                 'IniKeepInt("Menu", "AttractIcon", v);'):
        if want not in run: problems.append('TruMenu.cpp: RunAt must hold %s' % want)
    i_del, i_keep = run.find('"AttractIconText", nullptr'), run.find('IniKeepInt("Menu", "AttractIcon", v);')
    if not (0 <= i_del < i_keep): problems.append('TruMenu.cpp: RunAt must remove AttractIconText before it writes AttractIcon')
    run_code = fn_body(code, 'bool RunAt(')
    if '"on"' in run_code or '"true"' in run_code: problems.append('TruMenu.cpp: RunAt must not take on / true any more (1 = text only)')
    tables = src[src.find('const QbRow kQbSettings[] = {'):]
    tables = tables[:tables.find('\n};')]
    a, r, t = (tables.find('"menu.attracttimer", "", kQbBool'),
               tables.find('{"Teaser-Anzeige", "Teaser display", "menu.attracticon", "", kQbValue, -1, kQcNone, kQvAtStyle,'),
               tables.find('"set_tm", kQbGroup'))
    if not (0 <= a < r < t):
        problems.append('TruMenu.cpp: bar row "Teaser-Anzeige" (kQbValue kQvAtStyle) must follow menu.attracttimer in set_main')
    if '"menu.attracticon", "", kQbBool' in src: problems.append('TruMenu.cpp: the bool bar row menu.attracticon must be gone')
    # 0.22.51: kQvSoFade / kQvSoArea follow kQvAtStyle (was: kQvAtStyle closed the enum)
    # 0.22.52: kQvSoTint after kQvSoArea; 0.22.53: kQvHear after kQvSoTint
    # 0.22.56: kQvChapKeep after kQvHear
    if not re.search(r'kQvAtStyle,[^\n]*\n\s*kQvSoFade, kQvSoArea(,[^\n]*\n\s*kQvSoTint(,[^\n]*\n\s*kQvHear'
                     r'(,[^\n]*\n\s*kQvChapKeep)?)?)? \};', src):
        problems.append('TruMenu.cpp: kQvAtStyle must be in the QbVal enum (0.22.51: before kQvSoFade, kQvSoArea)')
    if ': val == kQvAtStyle ? kAtStyleN ' not in fn_body(src, 'int QbValueCount('):
        problems.append('TruMenu.cpp: QbValueCount must give kAtStyleN for kQvAtStyle')
    if 'case kQvAtStyle: Out(o, n, "%d", i); break;' not in fn_body(src, 'void QbValueArg('):
        problems.append('TruMenu.cpp: QbValueArg kQvAtStyle missing')
    if 'case kQvAtStyle: v = static_cast<int>(g_atStyle); break;' not in fn_body(src, 'int QbValueNow('):
        problems.append('TruMenu.cpp: QbValueNow kQvAtStyle missing')
    ivs = fn_body(src, 'bool ItemValueShort(')
    if 'Out(o, n, "%ld %s", s, de ? AtStyleOf(s).de : AtStyleOf(s).en);' not in ivs:
        problems.append('TruMenu.cpp: ItemValueShort must name the style (DE / EN)')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8').read()
    if '\n## 0.22.40 - ' not in readme or '\n### TO TEST 0.22.40' not in readme:
        problems.append('README.md: section "## 0.22.40 - ..." with "### TO TEST 0.22.40" missing')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if '11bce73110d4c61c3b85cf8375e5bb019442c6154060468027b589372a10f6d5' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.39 build hash (work/asi/menu0262) is missing')
    return problems, ('attract display styles (Q126b): [Menu] AttractIcon = 7 live, the 8 styles 0 .. 7, 0.22.39 INI '
                      'mapped once, item value, bar row with the style name (0.22.41 range: check_02241)')


# 0.22.41 (Q126c, owner 14.11. after trying 0.22.40): the styles 8 .. 16 appended to the same cycle switch
AT_STYLES_02241 = (('Klein, ohne Kasten', 'small, no box'), ('Klein + Strich, ohne Kasten', 'small + strike, no box'),
                   ('Klein, Zahl daneben', 'small, count beside'), ('Klein, Zahl darunter', 'small, count below'),
                   ('Klein, Zahl am Rand', 'small, count badge'), ('Knapp: Zeit + Zahl', 'terse: time + count'),
                   ('Knapp: Zeit/Limit + Zahl', 'terse: time/limit + count'), ('Nur Zahl (Wort)', 'count only (word)'),
                   ('Nur Zahl (Pfeil)', 'count only (arrow)'))
AT_SHAPES_02241 = (('1', '0', 'kAtTextBare'), ('1', '1', 'kAtTextBare'), ('1', '0', 'kAtTextCountLeft'),
                   ('1', '0', 'kAtTextCountBelow'), ('1', '0', 'kAtTextBadge'), ('0', '0', 'kAtTextTerse'),
                   ('0', '0', 'kAtTextTerseOf'), ('0', '0', 'kAtTextWord'), ('0', '0', 'kAtTextArrow'))
AT_HASH_02240 = '71374f9d167be140a6b124b71b55f6c24c603dfd3a0effbcf4e0cb8fc2b80f4b'   # work/asi/menu0263


def check_02241(ini_path, switches_path):
    """0.22.41 (Q126c, owner 14.11. after trying 0.22.40; workspace docs/Befund-AttractIcon-Kompakt-1411.md): [Menu]
    AttractIcon 0 .. 16 - styles 8 .. 16 appended (0 .. 7 unchanged, default 7): all drawn by DrawAtBare without the box
    (ImGuiWindowFlags_NoBackground, no box colour / alpha), the small circle (3 font sizes) without any time next to it,
    only the counter (skipped while NoAttract holds, else the game's teasers) beside / below / as a badge, the strike only
    in style 9, terse text 13 / 14 (the only places the seconds are drawn), the counter alone 15 / 16; the blink (lit)
    for all; texts in de / en pairs and only Latin-1 glyphs (the ImGui default font); RunAt takes one or two digits;
    switches row int:0..16; item text; help; kVersion 0.22.41; README 0.22.41 with TO TEST; Set-TruMenu knows the 0.22.40
    hash"""
    problems = []
    src = read_cpp()
    raw = open(CPP, 'r', encoding='utf-8').read()
    if '0.22.41 (Q126c compact attract styles' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.42: a part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.41 part "0.22.41 (Q126c compact attract styles"')
    if 'const int kAtStyleN = 17, kAtStyleDefault = %s;' % AT_DEFAULT not in src:   # 0.22.48: AT_DEFAULT
        problems.append('TruMenu.cpp: kAtStyleN 17 / kAtStyleDefault %s missing' % AT_DEFAULT)
    em = re.search(r'enum AtTextAt \{(.*?)\};', src, re.S)
    names = re.findall(r'kAtText[A-Za-z]+', re.sub(r'//[^\n]*', '', em.group(1))) if em else []
    want_enum = ['kAtTextNone', 'kAtTextOnly', 'kAtTextInside', 'kAtTextBelow', 'kAtTextLeft', 'kAtTextBare',
                 'kAtTextCountLeft', 'kAtTextCountBelow', 'kAtTextBadge', 'kAtTextTerse', 'kAtTextTerseOf', 'kAtTextWord',
                 'kAtTextArrow']
    if names != want_enum: problems.append('TruMenu.cpp: enum AtTextAt must be %s' % ', '.join(want_enum))
    m = re.search(r'const AtStyleDef kAtStyles\[\] = \{(.*?)\};', src, re.S)
    rows = re.findall(r'\{(\d), (\d), (kAtText[A-Za-z]+), "((?:[^"\\]|\\.)*)", "((?:[^"\\]|\\.)*)"\}', m.group(1)) if m else []
    if len(rows) != 17: problems.append('TruMenu.cpp: kAtStyles must hold 17 rows (got %d)' % len(rows))
    else:
        for i, (row, shape, nm) in enumerate(zip(rows[8:], AT_SHAPES_02241, AT_STYLES_02241), 8):
            if row[:3] != shape: problems.append('TruMenu.cpp: kAtStyles[%d] must be %s (got %s)' % (i, shape, row[:3]))
            if (unescape(row[3]), row[4]) != nm:
                problems.append('TruMenu.cpp: kAtStyles[%d] names must be %s / %s' % (i, nm[0], nm[1]))
            if len(nm[0]) > 40 or len(nm[1]) > 40: problems.append('kAtStyles[%d]: name over 40 characters' % i)
        for col, lang in ((3, 'DE'), (4, 'EN')):
            if len(set(r[col] for r in rows)) != len(rows): problems.append('TruMenu.cpp: kAtStyles %s names not unique' % lang)
    # DrawAt hands 8 .. 16 to DrawAtBare before its own text and box
    draw = fn_body(src, 'void DrawAt(')
    disp = 'if (st.text >= kAtTextBare) return DrawAtBare(st, ntDrawn, lit, held, why, frac, shown);'
    i_frac, i_disp, i_l1, i_begin = (draw.find('const float frac = why[0] ? -1.0f : AtFraction(held, &shown);'),
                                     draw.find(disp), draw.find('char l1[64]'), draw.find('ImGui::Begin('))
    if not (0 <= i_frac < i_disp < i_l1 < i_begin):
        problems.append('TruMenu.cpp: DrawAt must hand styles 8 .. 16 to DrawAtBare after the fraction, before its text / box')
    bare = fn_body(src, 'void DrawAtBare(')
    bare_raw = fn_body(raw, 'void DrawAtBare(')
    if not bare: problems.append('TruMenu.cpp: DrawAtBare missing')
    else:
        if not bare.split('\n')[2:3] == ['    const bool de = g_qbLang == 0;']:
            problems.append('TruMenu.cpp: DrawAtBare must start with const bool de = g_qbLang == 0; (the bar language)')
        for want in ('ImGuiWindowFlags_NoBackground', 'ImGui::Begin("##TruAttractIcon", nullptr, flags)',
                     'g_ntPos == 2 && g_ntBoxH > 0.0f', 'const LONG count = held ? g_atSkipped : g_atStarted;',
                     'const bool strike = held && st.strike;', 'const ImU32 text = lit ?', 'const ImU32 base = lit ?',
                     'case kAtTextCountLeft:', 'case kAtTextBadge:', 'case kAtTextTerse:', 'case kAtTextWord:',
                     'case kAtTextArrow:', 'if (st.text == kAtTextCountLeft) {', 'if (st.text == kAtTextCountBelow) {',
                     'if (st.text == kAtTextBadge) {', 'AtSkipArrow(dl, p, lh, text, 0.0f);'):
            if want not in bare: problems.append('TruMenu.cpp: DrawAtBare must hold %s' % want)
        for bad in ('PushStyleColor', 'SetNextWindowBgAlpha', 'ImGuiCol_WindowBg'):
            if bad in bare: problems.append('TruMenu.cpp: DrawAtBare must not draw a box (%s)' % bad)
        if bare.count('ImGui::Begin(') != 1 or bare.count('ImGui::End();') != 1 or \
                not bare.rstrip().endswith('ImGui::End();\n}') and not bare.rstrip().endswith('ImGui::End();\r\n}'):
            problems.append('TruMenu.cpp: DrawAtBare must Begin once and End once at its end (also when Begin is false)')
        # no time next to a circle: the seconds / the limit only in the terse case
        i_t, i_w = bare.find('case kAtTextTerse:'), bare.find('case kAtTextWord:')
        for word in ('shown', 'g_naAlarm'):
            uses = [x.start() for x in re.finditer(r'\b%s\b' % word, bare)]
            outside = [u for u in uses if not (i_t <= u < i_w) and not bare[:u].endswith('float ')]
            if outside: problems.append('TruMenu.cpp: DrawAtBare uses %s outside the terse styles 13 / 14' % word)
        rest = re.sub(r'de\s*\?\s*' + NT_LITSEQ + r'\s*:\s*' + NT_LITSEQ, '', bare)
        left = [unescape(x) for x in re.findall(r'"((?:[^"\\]|\\.)*)"', rest)]
        single = [t for t in left if re.search(r'[A-Za-z]{2}', re.sub(r'%[-.0-9]*[a-z]+', '', t)) and t != '##TruAttractIcon']
        if single: problems.append('TruMenu.cpp: DrawAtBare texts without a de / en pair: %s' % ', '.join(single))
        for esc in re.findall(r'\\([0-7]{3})', bare_raw):   # UTF-8 lead bytes: only \302 / \303 (U+0080 .. U+00FF)
            if 0xc0 <= int(esc, 8) and int(esc, 8) not in (0xc2, 0xc3):
                problems.append('TruMenu.cpp: DrawAtBare draws a glyph outside Latin-1 (\\%s) - not in the ImGui font' % esc)
    sc = fn_body(src, 'void AtSmallCircle(')
    for want in ('if (strike)', 'lit ? IM_COL32(242, 115, 26, 235)', 'AtSector(dl, c, r, a,'):
        if want not in sc: problems.append('TruMenu.cpp: AtSmallCircle must hold %s' % want)
    if 'AddLine(' in sc and sc.find('if (strike)') > sc.find('AddLine('):
        problems.append('TruMenu.cpp: AtSmallCircle must strike only when strike')
    for fn in ('void DrawAtBare(', 'void AtSmallCircle(', 'void AtSkipArrow(', 'void AtShadowText(', 'bool RunAt('):
        body = fn_body(src, fn)
        if not body: problems.append('TruMenu.cpp: %s missing' % fn.strip('(')); continue
        if any(w in body for w in ('reinterpret_cast<', 'WriteByte(', 'WriteBytes(', 'WriteDword(', 'LcPatch(', 'Fn>(')):
            problems.append('TruMenu.cpp: %s must not touch game memory' % fn.strip('('))
    run = fn_body(src, 'bool RunAt(')
    for want in ("if (arg[0] >= '0' && arg[0] <= '9' && (!arg[1] || (arg[1] >= '0' && arg[1] <= '9' && !arg[2])))",
                 "v = arg[1] ? (arg[0] - '0') * 10 + (arg[1] - '0') : arg[0] - '0';", 'if (v < 0 || v >= kAtStyleN) {',
                 '8 .. %d compact without a "'):
        if want not in run: problems.append('TruMenu.cpp: RunAt must hold %s' % want)
    if not re.search(r'\{"menu\.attracticon", "value", "0\.22\.41 0\.\.16 \(', src):
        problems.append('TruMenu.cpp: item menu.attracticon text must start with "0.22.41 0..16 ("')
    hm = re.search(r'\{"menu\.attracticon", "", "((?:[^"\\]|\\.)*)"\s*"((?:[^"\\]|\\.)*)"\}', src)
    if not hm or '8-16' not in hm.group(1) + hm.group(2): problems.append('TruMenu.cpp: menu.attracticon help must name 8-16')
    sw = [l.rstrip('\r\n').split(' | ') for l in open(switches_path, encoding='utf-8') if l.startswith('TruMenu | Menu | ')]
    f = [x for x in sw if len(x) >= 10 and x[2] == 'AttractIcon']
    if not f or f[0][3] != 'int:0..16' or f[0][6] != 'live' or f[0][7] != AT_DEFAULT or f[0][9] != 'TruMenu 0.22.41' \
            or '(0-16)' not in f[0][4] or '(0-16)' not in f[0][5]:
        problems.append('%s: row TruMenu | Menu | AttractIcon | int:0..16 | ...(0-16) | live | %s | ... | TruMenu 0.22.41 '
                        'missing' % (os.path.basename(switches_path), AT_DEFAULT))
    ini = open(ini_path, encoding='utf-8').read().replace('\r\n', '\n')
    if '\n; 0.22.40 / 0.22.41 (menu.attracticon)' not in ini or '; 7 the 0.22.39 look; no box: 8 / 9 small circle' not in ini:
        problems.append('%s: the [Menu] AttractIcon comment must name 0.22.41 and the styles 8 ..' % os.path.basename(ini_path))
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8').read()
    if '\n## 0.22.41 - ' not in readme or '\n### TO TEST 0.22.41' not in readme:
        problems.append('README.md: section "## 0.22.41 - ..." with "### TO TEST 0.22.41" missing')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if AT_HASH_02240 not in ps: problems.append('Set-TruMenu.ps1: the 0.22.40 build hash (work/asi/menu0263) is missing')
    return problems, ('compact attract styles (Q126c): [Menu] AttractIcon 0 .. 16 = 7 live, 17 styles, 8 .. 16 without '
                      'a box (small circle + counter / terse text), no time next to a circle, one or two digits')


W3_CHECKS_02242 = os.path.join(ROOT, 'work', 'w3_1411', 'precheck_02242.txt')
W3_KEYS_02242 = (('RoomNear', '3000'), ('OcclNear', '600'), ('HideEmptyPots', '1'), ('LabelStack', '3'),
                 ('LabelCellMax', '5'))
W3_ITEMS_02242 = (('dbg.roomnear', 'action', 'ValDvRoomNear', 'RunDvRoomNear'),
                  ('dbg.occlnear', 'action', 'ValDvOcclNear', 'RunDvOcclNear'),
                  ('dbg.emptypots', 'bool', 'ValDvEmptyPots', 'RunDvEmptyPots'))
W3_HASH_02241 = '35f834c671333ef62065bd1e5044e5c1f411e09ace27fa4add3b4bbd2aecaed9'   # work/asi/menu0264


def check_02242(ini_path, switches_path):
    """0.22.42 (W3, owner live notes of the test evening 13.11.; workspace docs/Befund-W3-Debugansicht-1411.md):
    RoomOnly - P5RoomOnlyDrops asks W3RoomDrops only for an instance of another intro unit; W3RoomDrops keeps it when its
    own stream unit +0xe0 (g_rkOk) equals Lara's (kUnitId) or it lies within [Debug] RoomNear, logs every verdict through
    W3RoomLog (once per instance and Lara unit, at most 20 lines per 10 s; object, intro unit, +0xe0 unit, Lara's unit,
    distance); DistMetres default 1 (check_02237); P5OcclFactor asks W3OcclNear before it queues a probe (Lara herself and
    [Debug] OcclNear never fade), names / uber labels test 1 m above the origin (kW3OcclLift 100); de-clutter - one rect
    list per ImGui frame (W3LabFrame resets g_dvRectN, DrawDebugView no longer does), the uber labels drawn after the debug
    view through W3UberDraw (merge into another layer's label of the same instance, the same object id within 50 units =
    one label x n), names / collectibles / key items through W3LabFind + W3LabPlace + W3LabAdd ([Debug] LabelStack,
    LabelCellMax); W3EmptyPot in UberCollect, DvDrawNames and M20Draw (reward pots); the teaser icon only in the main menu
    (W3AtMainMenu: front-end state 3 and no one-shot Bink movie, kW3AtChecks = precheck_02242.txt, fallback = shown);
    W3 functions read only; 5 keys (kOpts, INI, switches rows restart 0.22.42), 3 items, bar + help row; README 0.22.42
    with TO TEST; Set-TruMenu knows the 0.22.41 hash"""
    problems = []
    src = read_cpp()
    if '0.22.42 (W3 debug view' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.43: a part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.42 part "0.22.42 (W3 debug view"')
    # byte checks of the teaser icon = the offline list
    offline = []
    if os.path.exists(W3_CHECKS_02242):
        for line in open(W3_CHECKS_02242, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if line:
                addr, hexs = line.split(None, 1)
                offline.append(('%08x' % int(addr, 16), hexs.replace(' ', '').lower()))
    else:
        problems.append('work/w3_1411/precheck_02242.txt (the offline byte list) is missing')
    rows = [(a.lower(), b.lower()) for a, b in sv_rows(src, 'kW3AtChecks')]
    if rows != offline or len(rows) != 3:
        problems.append('TruMenu.cpp: kW3AtChecks (%d rows) must be the 3 rows of precheck_02242.txt in order' % len(rows))
    if 'g_w3AtOk = DvChecks(kW3AtChecks,' not in fn_body(src, 'void W3Check('):
        problems.append('TruMenu.cpp: W3Check must set g_w3AtOk from DvChecks(kW3AtChecks, ...)')
    # 1. room rule
    rod = fn_body(src, 'bool P5RoomOnlyDrops(')
    if 'return unit[0] && !DvIsLaraUnit(unit) && W3RoomDrops(inst, unit);' not in rod:
        problems.append('TruMenu.cpp: P5RoomOnlyDrops must ask W3RoomDrops only for another known intro unit')
    rd = fn_body(src, 'bool W3RoomDrops(')
    for need in ('g_rkOk && ReadDword(inst + 0xe0, &sid)', 'ReadDword(kUnitId, &laraSid) && sid == laraSid',
                 'g_w3RoomNear > 0.0f && dist >= 0.0f && dist <= g_w3RoomNear', 'const int verdict = sameSid ? 1 : nearLara ? 2 : 0;',
                 'W3RoomLog(inst, unit, haveSid, sid, dist, verdict);', 'return verdict == 0;'):
        if need not in rd: problems.append('TruMenu.cpp: W3RoomDrops lacks %s' % need)
    rl = fn_body(src, 'void W3RoomLog(')
    for need in ('if (g_w3Seen[i].verdict == verdict) return;', 'now - g_w3LogWindow > 10000', 'if (g_w3LogLines >= 20)',
                 'intro unit %s, own stream unit (+0xe0) %s, Lara\'s unit %s', 'RkUnitEntry(sid)'):
        if need not in rl: problems.append('TruMenu.cpp: W3RoomLog lacks %s' % need)
    # 3. near labels, test point
    of = fn_body(src, 'float P5OcclFactor(')
    if not (0 <= of.find('if (W3OcclNear(key, p)) return 1.0f;') < of.find('g_p5Pending[g_p5PendingN++]')):
        problems.append('TruMenu.cpp: P5OcclFactor must ask W3OcclNear before it queues a probe')
    on = fn_body(src, 'bool W3OcclNear(')
    if 'if (key == player) { ++g_w3NearKept; return true; }' not in on or 'g_w3OcclNear * g_w3OcclNear' not in on:
        problems.append('TruMenu.cpp: W3OcclNear must keep Lara and everything within OcclNear unfaded')
    if 'const float kW3OcclLift = 100.0f;' not in src:
        problems.append('TruMenu.cpp: kW3OcclLift must be 100.0f (1 m above the origin)')
    for fn, var in (('void DvDrawNames(', 'd.pos[2] + kW3OcclLift'), ('void DrawUberLabels(', 'c.pos[2] + kW3OcclLift')):
        body = fn_body(src, fn)
        if var not in body or '+ 60.0f};' in body:
            problems.append('TruMenu.cpp: %s must test occlusion at %s (not +60)' % (fn.strip('('), var))
    # 4. de-clutter
    lf = fn_body(src, 'bool W3LabFrame(')
    for need in ('ImGui::GetFrameCount()', 'g_dvRectN = 0;', 'g_w3LabN = 0;', 'memset(g_w3Cell, 0, sizeof(g_w3Cell));'):
        if need not in lf: problems.append('TruMenu.cpp: W3LabFrame lacks %s' % need)
    dv = fn_body(src, 'void DrawDebugView(')
    if 'W3LabFrame();' not in dv or 'g_dvRectN = 0' in dv:
        problems.append('TruMenu.cpp: DrawDebugView must start the frame with W3LabFrame (and not reset g_dvRectN itself)')
    render = fn_body(src, 'void Render(')
    # 0.22.56: the condition also holds for notes with flag bit 0 ("if (DvAnyOn() || g_ntAlways) DrawDebugView();")
    if not (0 <= render.find(') DrawDebugView();') < render.find('if (g_ubOn) DrawUberLabels();')):
        problems.append('TruMenu.cpp: Render must draw the uber labels after the debug view')
    ub = fn_body(src, 'void DrawUberLabels(')
    for need in ('W3LabFrame();', 'dx * dx + dy * dy + dz * dz <= 2500.0f', 'W3UberDraw(dl, at, line1, line2,',
                 'if (dupOf[i] >= 0) { ++dupes; continue; }'):
        if need not in ub: problems.append('TruMenu.cpp: DrawUberLabels lacks %s' % need)
    if 'LabelDraw(dl, at, line1, line2' in ub: problems.append('TruMenu.cpp: DrawUberLabels must not use LabelDraw (no overlap test)')
    wu = fn_body(src, 'int W3UberDraw(')
    for need in ('const int had = W3LabFind(inst);', 'if (!state || !line2[0]) return 1;', 'if (!W3LabPlace(&r, at, h + 3.0f)) return 2;',
                 'W3LabAdd(inst, r);'):
        if need not in wu: problems.append('TruMenu.cpp: W3UberDraw lacks %s' % need)
    pl = fn_body(src, 'bool W3LabPlace(')
    for need in ('g_w3Cell[cy][cx] >= g_w3CellMax', 'for (int k = 0; k <= g_w3Stack; ++k) {', 'if (!DvRectFree(t)) continue;'):
        if need not in pl: problems.append('TruMenu.cpp: W3LabPlace lacks %s' % need)
    for fn, need in (('void DvDrawNames(', ('W3LabFind(d.inst) >= 0', 'W3LabPlace(&r, at,', 'W3LabAdd(d.inst, r);')),
                     ('bool M20Label(', ('W3LabFind(m.inst) >= 0 || !W3LabPlace(&r, at, h + 4.0f)', 'W3LabAdd(m.inst, r);'))):
        body = fn_body(src, fn)
        for x in need:
            if x not in body: problems.append('TruMenu.cpp: %s lacks %s' % (fn.strip('('), x))
    # 5. empty pots
    for fn, need in (('int UberCollect(', 'if (take && W3EmptyPot(inst)) take = false;'),
                     ('void DvDrawNames(', 'if (hit && W3EmptyPot(inst)) { ++pots; hit = false; }'),
                     ('void M20Draw(', 'if (ck == kCoPot && W3EmptyPot(inst)) {')):
        if need not in fn_body(src, fn): problems.append('TruMenu.cpp: %s lacks %s' % (fn.strip('('), need))
    ep = fn_body(src, 'bool W3EmptyPot(')
    for need in ('if (!g_w3EmptyPots) return false;', 'CoKindOf(id) == kCoPot', 'strstr(low, "weightbreak")',
                 'k == 1 || !CoRewardIndex(inst, &script) || P5Collected(inst)'):
        if need not in ep: problems.append('TruMenu.cpp: W3EmptyPot lacks %s' % need)
    # 6. teaser icon
    if 'bool AtWantsDraw() { return g_atWant != 0 && NaFrontEnd() && W3AtMainMenu(); }' not in src:
        problems.append('TruMenu.cpp: AtWantsDraw must add W3AtMainMenu()')
    am = fn_body(src, 'bool W3AtMainMenu(')
    for need in ('if (!g_w3AtOk) return true;', 'const bool movie = handle && !loop;', 'const int why = fe != 3 ? 1 : movie ? 2 : 0;',
                 'return why == 0;'):
        if need not in am: problems.append('TruMenu.cpp: W3AtMainMenu lacks %s' % need)
    if 'kW3FeState = 0x00fae8da, kW3BinkHandle = 0x00a039bc, kW3BinkLoop = 0x00a039dc;' not in src:
        problems.append('TruMenu.cpp: kW3FeState / kW3BinkHandle / kW3BinkLoop must be 0xfae8da / 0xa039bc / 0xa039dc')
    # read only
    for fn in ('bool W3RoomDrops(', 'void W3RoomLog(', 'bool W3OcclNear(', 'bool W3LabFrame(', 'bool W3LabPlace(',
               'int W3UberDraw(', 'bool W3EmptyPot(', 'bool W3AtMainMenu('):
        body = fn_body(src, fn)
        if not body: problems.append('TruMenu.cpp: %s missing' % fn.strip('(')); continue
        if any(w in body for w in ('WriteByte(', 'WriteBytes(', 'WriteDword(', 'reinterpret_cast<volatile', 'Fn>(', 'LcPatch(')):
            problems.append('TruMenu.cpp: %s must not write game memory or call the game' % fn.strip('('))
    # keys, items, bar, switches, options, load, menu
    header, opt_rows = table(src)
    keys = {(s, k): d for s, k, d, _ in opt_rows}
    ini = open(ini_path, encoding='utf-8').read().replace('\r\n', '\n')
    sw = [l.rstrip('\r\n').split(' | ') for l in open(switches_path, encoding='utf-8') if l.startswith('TruMenu | Debug | ')]
    got = {f[2]: f for f in sw if len(f) >= 10 and f[9] == 'TruMenu 0.22.42'}
    for k, d in W3_KEYS_02242 + (('DistMetres', '1'),):
        if keys.get(('Debug', k)) != d: problems.append('TruMenu.cpp: kOpts [Debug] %s must default to %s' % (k, d))
        if '\n%s=%s\n' % (k, d) not in ini: problems.append('%s: [Debug] %s=%s missing' % (os.path.basename(ini_path), k, d))
        f = got.get(k)
        if not f or f[6] != 'restart' or f[7] != d:
            problems.append('%s: row TruMenu | Debug | %s | ... | restart | %s | ... | TruMenu 0.22.42 missing'
                            % (os.path.basename(switches_path), k, d))
    if 'int g_p5Room = 1, g_p5Metres = 1,' not in src:
        problems.append('TruMenu.cpp: g_p5Metres must start at 1 (code default = kOpts)')
    for item, typ, val, run in W3_ITEMS_02242:
        if not re.search(r'\{"%s", "%s", .*?,\s+false,\s+%s,\s+%s\}' % (re.escape(item), typ, val, run), src, re.S):
            problems.append('TruMenu.cpp: item %s (%s, %s / %s) missing' % (item, typ, val, run))
    if '"dbg.emptypots", "", kQbBool, -1, kQcNone, 0, kQbWhite, 0}' not in src or \
            not re.search(r'\{"dbg\.emptypots", "", "', src):
        problems.append('TruMenu.cpp: bar row + help row dbg.emptypots missing')
    if 'W3ReadOptions(ini);' not in src or not re.search(r'\n    PdCheck\(\);[^\n]*\n    W3Check\(\);', src):
        problems.append('TruMenu.cpp: ReadOptions must call W3ReadOptions and the load W3Check after PdCheck')
    if 'W3MenuControls(o, sizeof(o));' not in src: problems.append('TruMenu.cpp: menu controls 0.22.42 missing')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8').read()
    if '\n## 0.22.42 - ' not in readme or '\n### TO TEST 0.22.42' not in readme:
        problems.append('README.md: section "## 0.22.42 - ..." with "### TO TEST 0.22.42" missing')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if W3_HASH_02241 not in ps: problems.append('Set-TruMenu.ps1: the 0.22.41 build hash (work/asi/menu0264) is missing')
    return problems, ('W3 debug view (RoomOnly + own stream unit / RoomNear with a reason log; DistMetres 1; OcclNear + '
                      'test point +1 m; one label per instance and frame, uber labels after the debug view, LabelStack / '
                      'LabelCellMax; HideEmptyPots; teaser icon main menu only, %d byte checks = precheck_02242; %d keys, '
                      '%d items)' % (len(rows), len(W3_KEYS_02242) + 1, len(W3_ITEMS_02242)))


W5_CHECKS_02243 = os.path.join(ROOT, 'work', 'w5_1411', 'precheck_02243.txt')
W5_HASH_02242 = 'c415a6c42b146f1051a017b921ce7c3542476dae6f989be2f0013224e46f140e'


def check_02243():
    """0.22.43 (W5, owner live notes of the test evening 13.11.; workspace docs/Befund-W5-Markup-Saeule-1411.md):
    DrawMarkup = W5DrawMarkup - object markup (box +0xc owner) through the owner's bone matrix like the engine (0x5be360:
    [owner+0x90] + s16 record +0x30 * 0x40, 0x49ba20 x * row0 + y * row1 + z * row2 + row3, only with owner +0x2d8 set,
    0x5c41c3), without a matrix left out; the query's skip rules (record +0x32 == 1, box +0x28 bit 31, owner +0x18
    0x20000002, stream unit entry +5) - W5Skipped; type / id as the getter 0x5be340 (item +0x4d / +0x48, record +0x33 /
    +0x2e); 24 type names DE / EN; labels within kW5LabelNear 4350 (15 m), at most kW5LabelMax 24, through W3LabFrame /
    W3LabPlace / W3LabAdd; dbg.roomonly (W5RoomKeeps) and P5OcclFactor (key = box); kW5MkChecks = precheck_02243.txt;
    W5Check after W3Check; bar rows Markup / Nur Kanten first in their group (once); no new key or item; README 0.22.43
    with TO TEST; Set-TruMenu knows the 0.22.42 hash"""
    problems = []
    src = read_cpp()
    if '0.22.43 (W5 markup' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.44: a part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.43 part "0.22.43 (W5 markup"')
    offline = []
    if os.path.exists(W5_CHECKS_02243):
        for line in open(W5_CHECKS_02243, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if line:
                addr, hexs = line.split(None, 1)
                offline.append(('%08x' % int(addr, 16), hexs.replace(' ', '').lower()))
    else:
        problems.append('work/w5_1411/precheck_02243.txt (the offline byte list) is missing')
    rows = [(a.lower(), b.lower()) for a, b in sv_rows(src, 'kW5MkChecks')]
    if rows != offline or len(rows) != 6:
        problems.append('TruMenu.cpp: kW5MkChecks (%d rows) must be the 6 rows of precheck_02243.txt in order' % len(rows))
    if 'g_w5MkOk = DvChecks(kW5MkChecks,' not in fn_body(src, 'void W5Check('):
        problems.append('TruMenu.cpp: W5Check must set g_w5MkOk from DvChecks(kW5MkChecks, ...)')
    if 'void DrawMarkup() { W5DrawMarkup(); }' not in src:
        problems.append('TruMenu.cpp: DrawMarkup must call W5DrawMarkup')
    om = fn_body(src, 'bool W5OwnerMatrix(')
    for need in ('ReadDword(owner + 0x2d8, &use) || !use) return false;', 'ReadWord(rec + 0x30, &bone)',
                 'ReadDword(owner + 0x90, &base)', 'static_cast<short>(bone)) * 0x40'):
        if need not in om: problems.append('TruMenu.cpp: W5OwnerMatrix lacks %s' % need)
    if 'out[c] = p[0] * m[c] + p[1] * m[4 + c] + p[2] * m[8 + c] + m[12 + c];' not in fn_body(src, 'void W5Apply('):
        problems.append('TruMenu.cpp: W5Apply must be x * row0 + y * row1 + z * row2 + row3 (0x49ba20)')
    sk = fn_body(src, 'bool W5Skipped(')
    for need in ('ReadByte(rec + 0x32, &b) && b == 1', 'flags & 0x80000000u', '(oflags & 0x20000002u)',
                 'ReadByte(entry + 5, &b) && b'):
        if need not in sk: problems.append('TruMenu.cpp: W5Skipped lacks %s' % need)
    dm = fn_body(src, 'void W5DrawMarkup(')
    for need in ('if (g_w5MkOk && W5Skipped(here, rec, flags, owner)) { ++skipped; continue; }',
                 'const bool xform = local && g_w5MkOk && W5OwnerMatrix(owner, rec, m);',
                 'if (local && !xform) { ++skipped; continue; }', 'if (!W5RoomKeeps(here, owner, nearest)) { ++room; continue; }',
                 'ReadByte(item + 0x4d, &tb)', 'ReadWord(item + 0x48, &w)', 'ReadByte(rec + 0x33, &tb)',
                 'ReadWord(rec + 0x2e, &w)', 'alpha = P5OcclFactor(here, mid);', 'W3LabFrame();',
                 'if (!W3LabPlace(&r, l.at, fs + 3.0f)) continue;', 'W3LabAdd(l.box, r);'):
        if need not in dm: problems.append('TruMenu.cpp: W5DrawMarkup lacks %s' % need)
    rk = fn_body(src, 'bool W5RoomKeeps(')
    for need in ('if (!g_p5RoomOnly) return true;', 'entry == RkUnitEntry(laraSid)', 'ReadDword(owner + 0xe0, &sid) && sid == laraSid',
                 'nearest <= g_w3RoomNear'):
        if need not in rk: problems.append('TruMenu.cpp: W5RoomKeeps lacks %s' % need)
    if 'const float kW5LabelNear = 4350.0f;' not in src or 'const int kW5LabelMax = 24;' not in src:
        problems.append('TruMenu.cpp: kW5LabelNear 4350.0f / kW5LabelMax 24 missing')
    m = re.search(r'const W5Type kW5Types\[24\] = \{(.*?)\n\};', src, re.S)
    if not m or len(re.findall(r'\{"[^"]*", "[^"]*", IM_COL32', m.group(1))) != 24:
        problems.append('TruMenu.cpp: kW5Types must hold 24 rows {de, en, colour}')
    if not re.search(r'\n    W3Check\(\);[^\n]*\n    W5Check\(\);', src):
        problems.append('TruMenu.cpp: the load must call W5Check right after W3Check')
    for row in ('{"Markup", "Markup", "draw.markup", "", kQbBool, -1, kQcMarkup, 0, kQbMarkup},',
                '{"Nur Kanten", "Ledges only", "draw.ledges", "", kQbBool, -1, kQcNone, 0, kQbMarkup},'):
        if src.count(row) != 1: problems.append('TruMenu.cpp: bar row %s must exist once' % row)
    grp = src.find('"rd_markup", kQbGroup')
    if grp < 0 or not (0 <= src.find('"draw.markup", "", kQbBool', grp) < src.find('"dbg.slide"', grp)):
        problems.append('TruMenu.cpp: bar rows Markup / Nur Kanten must come first in the group rd_markup')
    for fn in ('void W5Check(', 'bool W5Skipped(', 'bool W5OwnerMatrix(', 'void W5Apply(', 'bool W5RoomKeeps(',
               'void W5DrawMarkup('):
        body = fn_body(src, fn)
        if not body: problems.append('TruMenu.cpp: %s missing' % fn.strip('(')); continue
        if any(w in body for w in ('WriteByte(', 'WriteBytes(', 'WriteDword(', 'reinterpret_cast<volatile', 'Fn>(', 'LcPatch(')):
            problems.append('TruMenu.cpp: %s must not write game memory or call the game' % fn.strip('('))
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8').read()
    if '\n## 0.22.43 - ' not in readme or '\n### TO TEST 0.22.43' not in readme:
        problems.append('README.md: section "## 0.22.43 - ..." with "### TO TEST 0.22.43" missing')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if W5_HASH_02242 not in ps: problems.append('Set-TruMenu.ps1: the 0.22.42 build hash (work/asi/menu0265) is missing')
    return problems, ('W5 markup (object markup through the bone matrix, query skip rules, type + id labels within 15 m, '
                      'RoomOnly / occlusion, bar rows first; %d byte checks = precheck_02243)' % len(rows))


W2_HASH_02243 = '36d8966b52c39b9ad58c38c6abd83d97fab0f632d52917a750d475160264ad82'
# the packages of the test guide 14.11. (workspace docs/Testanleitung-1411.md): letter, group label start, items the
# package needs (item, argument) - owner 2026-11-13 "adren.fill / adren.keep auch im passenden Testpaket"
W2_PACKAGES = (('a', 'Paket A: Adrenalin + Kampf', (('arena.go', '1a'), ('adren.fill', ''), ('adren.keep', ''),
                                                    ('cheat.onehitkill', ''), ('adren.meter', ''))),
               ('b', 'Paket B: Hoeren', (('snd.dump', ''),)),            # read_cpp: umlaut escapes -> ae / oe / ue
               # 0.22.50: Paket B2 Ton-Log (README 0.22.50 TO TEST)
               ('b2', 'Paket B2: Ton-Log', (('snd.list', ''), ('snd.logcollapse', ''), ('snd.logaudible', ''),
                                            ('snd.catmute', 'enemies'), ('snd.catsolo', 'lara'), ('snd.solonew', ''),
                                            ('snd.mute', 'all 0'), ('snd.fmod', ''), ('snd.hooks', ''))),
               ('c', 'Paket C: DLC 2 aus dem Pausemenue', ()),
               ('d', 'Paket D: Debug-Ansicht', (('dbg.roomonly', ''), ('dbg.metres', ''))),
               ('e', 'Paket E: Markup / Saeule / Wasser', (('draw.markup', ''), ('level.load', 'dlc_dungeon'))),
               ('f', 'Paket F: Fixes 13.11.', (('level.start', 'dlc1'),)),
               # 0.22.48: Paket G Sonar komplett (README 0.22.48 TO TEST; not in the 14.11. guide)
               ('g', 'Paket G: Sonar komplett', (('sonar.full', ''), ('sonar.placeholder', ''), ('sonar.markers', ''),
                                                 ('sonar.status', ''), ('snd.sonar', ''))))
W2_ARCHIVED = ('tp_q90', 'ts_spots', 'light_diag', 'ts_diag', 'ts_hall02')   # sub-groups of ts_archive, in this order
W2_KEPT = ('ts_teleport', 'ts_arena1', 'ts_cine')                           # level 0 between the TG block and the archive


def check_02244(switches_path):
    """0.22.44 (W2, owner live notes of the test evening 13.11.; workspace docs/Befund-W2-TruMenu-Ordnung-1411.md):
    page Tests - the block "TG 1411" first in kQbTests: group tg_1411 (level 0, the first row), a note, then one kQfSub
    group tg_a .. tg_f per package of the test guide (label "Paket <X>: ..." as the guide, in kQbStartClosed) with a note,
    the items the package needs and at least one check test.mark tg<X>.<name> of its own package (unique); every row of
    the block kQfTg, kQfTg nowhere else; switch rows sw.set of TruMenu.switches.txt; then ts_teleport / ts_arena1 /
    ts_cine on level 0, then the closed group ts_archive (the last level-0 group) holding tp_q90 (the TP block), ts_spots,
    light_diag, ts_diag, ts_hall02 as kQfSub groups - no old row lost (the arena / hall02 / light items still on the
    page); QbTestsRows skips tg ids, TpCheckSet tags them 1411; kQbViewMax 256 (page Tests static rows + 16 <= it). Barrierefreiheit: no label with a
    leading space, the planned rows only in the last group acc_planned (closed at the start), the arachnophobia rows in
    the sub-group acc_arachno; QbViewOf: planned rows without the "   " prefix. [Menu]: an INI without Load (before
    0.22.18) keeps the big window off (g_menuOldIni; Load stays as read), logged at the start and in ToggleMenu; row
    DeviceGlyphs (sw.set TruMenu:Input:DeviceGlyphs) in the group set_ctl of page Spiel-Einstellungen; no new INI key /
    item; README 0.22.44 with TO TEST; Set-TruMenu knows the 0.22.43 hash"""
    problems = []
    src = read_cpp()
    if '0.22.44 (W2 order' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.45: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.44 part "0.22.44 (W2 order"')
    tests = src[src.find('const QbRow kQbTests[] = {'):]
    tests = tests[:tests.find('\n};')]
    a, b = tests.find('// ---- TG 1411 begin'), tests.find('// ---- TG 1411 end')
    if a < 0 or b < a: return problems + ['TruMenu.cpp: kQbTests lacks the block "TG 1411 begin" .. "TG 1411 end"'], 'TG: no block'
    if re.search(r'\n    \{"', tests[:a]): problems.append('TruMenu.cpp: the TG block must be the first rows of kQbTests')
    block = tests[a:b]
    raw = re.findall(r'\n    \{"', block)
    rows = [r for r in qb_rows(src, True) if r[0] == 'kQbTests' and 'kQfTg' in r[6]]
    if len(rows) != len(raw):
        problems.append('TruMenu.cpp: TG block has %d rows, qb_rows parses %d with kQfTg' % (len(raw), len(rows)))
    flags = len(re.findall(r'kQfTg\}', src))
    if flags != len(raw) or re.findall(r'kQfTg\}', tests[:a] + tests[b:]):
        problems.append('TruMenu.cpp: kQfTg only on the rows of the TG block (%d flags, %d rows)' % (flags, len(raw)))
    if 'kQfTg = 32 };' not in src and 'kQfTg = 32,' not in src:   # 0.22.53: kQfLv2 / kQfLv3 follow
        problems.append('TruMenu.cpp: QbFlag kQfTg = 32 missing')
    starts = LIT.findall(src[src.find('const char *const kQbStartClosed[] = {'):].split('};')[0])
    sw_keys = set()
    for line in open(switches_path, encoding='utf-8').read().splitlines():
        f = [x.strip() for x in line.split('|')]
        if line.startswith('#') or len(f) < 9 or f[0] == 'group': continue
        sw_keys.add('%s:%s:%s' % (f[0], f[1], f[2]))
    pkg, seen, ids, order = None, {}, set(), []
    labels = {p: lab for p, lab, _ in W2_PACKAGES}
    for t, de, item, arg, kind, layer, tail in rows:
        where = 'TruMenu.cpp: TG row "%s" (%s %s)' % (de, item, arg)
        de_en = re.search(r'\{"%s", "([^"]*)", "%s"' % (re.escape(de), re.escape(item)), block)
        for text in (de, de_en.group(1) if de_en else ''):
            if len(text.encode('utf-8')) > 100: problems.append(where + ': label longer than 100 bytes')
            if text[:1] == ' ': problems.append(where + ': label with a leading space')
        if kind == 'kQbGroup':
            if arg == 'tg_1411':
                if 'kQfSub' in tail or pkg is not None: problems.append(where + ': tg_1411 = the first row, level 0')
                pkg = ''
                continue
            m = re.fullmatch(r'tg_([a-g]|b2)', arg)   # 0.22.48: + g; 0.22.50: + b2
            if not m or 'kQfSub' not in tail: problems.append(where + ': a package group tg_<a-g|b2> with kQfSub'); continue
            if arg not in starts: problems.append(where + ': %s missing in kQbStartClosed' % arg)
            pkg = m.group(1)
            if not de.startswith(labels[pkg]): problems.append(where + ': label must start "%s" (the guide)' % labels[pkg])
            order.append(pkg)
            seen[pkg] = {'note': 0, 'check': 0, 'items': set()}
            continue
        if pkg is None: problems.append(where + ': before the group tg_1411'); continue
        if kind == 'kQbNote':
            if item != '-' or arg: problems.append(where + ': a note row has id "-" and no argument')
            if pkg in seen: seen[pkg]['note'] += 1
        elif kind == 'kQbCheck':
            cm = re.fullmatch(r'tg([A-G]|B2)\.[a-z0-9]+', arg)   # 0.22.50: + B2
            if item != 'test.mark' or not cm or len(arg) > 63:
                problems.append(where + ': a check row is test.mark tg<A-G|B2>.<name>')
            elif cm.group(1).lower() != pkg: problems.append(where + ': check id of another package (group tg_%s)' % pkg)
            if arg in ids: problems.append(where + ': check id twice')
            ids.add(arg)
            if pkg in seen: seen[pkg]['check'] += 1
        elif kind == 'kQbSwitch':
            if item != 'sw.set' or arg not in sw_keys:
                problems.append(where + ': a switch row is sw.set <Plugin>:<Section>:<Key> of %s' %
                                os.path.basename(switches_path))
        elif kind in ('kQbLabel', 'kQbPlanned'): problems.append(where + ': no label / planned rows in the TG block')
        elif pkg in seen: seen[pkg]['items'].add((item, arg))
    if order != [p for p, _, _ in W2_PACKAGES]:
        problems.append('TruMenu.cpp: TG package groups %s, wanted a .. g in order' % ''.join(order))
    for p, lab, need in W2_PACKAGES:
        c = seen.get(p)
        if not c: continue
        if not c['note'] or not c['check']: problems.append('TruMenu.cpp: package %s needs a hint and a check' % p.upper())
        for it in need:
            if it not in c['items']: problems.append('TruMenu.cpp: package %s lacks the row %s %s' % (p.upper(), it[0], it[1]))
    # the groups after the block: kept ones on level 0, then the closed archive with the old groups as sub-groups
    groups = re.findall(r'\{"[^"]*",\s+"[^"]*",\s+"-",\s+"([a-z0-9_]+)",\s+kQbGroup,\s+-1,\s+kQcNone,\s+0,\s+[A-Za-z0-9]+,'
                        r'\s+([^}]*)\}', tests[b:])
    names = [g for g, _ in groups]
    top = [g for g, f in groups if 'kQfSub' not in f]
    if top != list(W2_KEPT) + ['ts_archive']:
        problems.append('TruMenu.cpp: level-0 groups after the TG block must be %s + ts_archive (got %s)' %
                        (', '.join(W2_KEPT), ', '.join(top)))
    if 'ts_archive' not in starts: problems.append('TruMenu.cpp: ts_archive missing in kQbStartClosed')
    if 'ts_archive' in names:
        after = names[names.index('ts_archive') + 1:]
        subs = [g for g in after if g in W2_ARCHIVED]
        if subs != list(W2_ARCHIVED): problems.append('TruMenu.cpp: archive sub-groups %s, wanted %s' % (subs, W2_ARCHIVED))
        for g, f in groups[names.index('ts_archive') + 1:]:
            if 'kQfSub' not in f: problems.append('TruMenu.cpp: group %s in the archive must be kQfSub' % g)
    for item, arg in (('arena.go', '1b'), ('arena.load', 'mayan_thrall'), ('fix.hall02', ''), ('light.list', ''),
                      ('dbg.depthdump', ''), ('cp.jump', 'dlc_yggdrasil_end 9608'), ('cine.pause', '')):
        if not any(r[0] == 'kQbTests' and r[2] == item and r[3] == arg for r in qb_rows(src)):
            problems.append('TruMenu.cpp: kQbTests lost the row %s %s' % (item, arg))
    qt = fn_body(src, 'int QbTestsRows(')
    if '!strncmp(t.id, "tg", 2)' not in qt: problems.append('TruMenu.cpp: QbTestsRows must skip the tg<X>.<name> rows too')
    if '!_strnicmp(r.arg, "tg", 2) ? "1411" : "Q90"' not in fn_body(src, 'void TpCheckSet('):
        problems.append('TruMenu.cpp: TpCheckSet must tag the tg checks 1411 (the archived ones Q90)')
    if 'const int kQbViewMax = %d;' % QB_VIEW_MAX not in src:   # 0.22.48: QB_VIEW_MAX (320; 0.22.44: 256)
        problems.append('TruMenu.cpp: kQbViewMax must be %d' % QB_VIEW_MAX)
    n_tests = len([r for r in qb_rows(src) if r[0] == 'kQbTests'])
    if n_tests + 16 > QB_VIEW_MAX:   # every group open: the static rows + room for the Prepare / TO TEST rows
        problems.append('TruMenu.cpp: page Tests has %d static rows - kQbViewMax %d leaves < 16 for Prepare / TO TEST' %
                        (n_tests, QB_VIEW_MAX))
    # Barrierefreiheit
    acc = [r for r in qb_rows(src, True) if r[0] == 'kQbAccess']
    accb = src[src.find('const QbRow kQbAccess[] = {'):]
    accb = accb[:accb.find('\n};')]
    for de, en in re.findall(r'\{"([^"]*)", "([^"]*)", "', accb):
        if de[:1] == ' ' or en[:1] == ' ': problems.append('TruMenu.cpp: kQbAccess label "%s" starts with a space' % de)
    heads = [(i, r) for i, r in enumerate(acc) if r[4] == 'kQbGroup']
    if not heads or heads[-1][1][3] != 'acc_planned' or 'kQfSub' in heads[-1][1][6]:
        problems.append('TruMenu.cpp: kQbAccess must end with the level-0 group acc_planned')
    else:
        last = heads[-1][0]
        if any(r[4] == 'kQbPlanned' for r in acc[:last]):
            problems.append('TruMenu.cpp: kQbAccess has planned rows outside the group acc_planned')
        if any(r[4] != 'kQbPlanned' for r in acc[last + 1:]):
            problems.append('TruMenu.cpp: the group acc_planned holds planned rows only')
        if not any(r[4] == 'kQbPlanned' for r in acc[last + 1:]): problems.append('TruMenu.cpp: acc_planned is empty')
    if 'acc_planned' not in starts: problems.append('TruMenu.cpp: acc_planned missing in kQbStartClosed')
    ar = [i for i, r in enumerate(acc) if r[3] == 'acc_arachno' and r[4] == 'kQbGroup' and 'kQfSub' in r[6]]
    want = ['arachno.on', 'arachno.hide', 'arachno.picture', 'arachno.mute', 'arachno.status']
    if not ar or [r[2] for r in acc[ar[0] + 1:ar[0] + 6]] != want:
        problems.append('TruMenu.cpp: kQbAccess needs the kQfSub group acc_arachno with %s' % ', '.join(want))
    view = fn_body(src, 'void QbViewOf(')
    if 'label ? "-- " : "", de ? r.de : r.en);' not in view:
        problems.append('TruMenu.cpp: QbViewOf: planned rows without the "   " prefix')
    # [Menu] Enabled in an INI before 0.22.18
    ro = re.sub(r'//[^\n]*', '', fn_body(src, 'void ReadOptions('))
    i_win = ro.find('g_menuWindow = OptInt(ini, "Menu", "Enabled") != 0 ? 1 : 0;')
    i_old = ro.find('g_menuOldIni = GetPrivateProfileStringA("Menu", "Load", "", probe, sizeof(probe), ini) == 0 ? 1 : 0;')
    i_off = ro.find('if (g_menuOldIni) g_menuWindow = 0;')
    if not 0 <= i_win < i_old < i_off:
        problems.append('TruMenu.cpp: ReadOptions must read Enabled, then g_menuOldIni (no [Menu] Load), then window off')
    if re.search(r'g_enabled\s*=\s*g_menuWindow', ro): problems.append('TruMenu.cpp: an old INI must not unload TruMenu')
    if 'int g_menuOldIni = 0;' not in src: problems.append('TruMenu.cpp: int g_menuOldIni = 0; missing')
    if 'if (g_menuOldIni)   // 0.22.44 (W2)' not in src or 'TruMenu.ini has no [Menu] Load (written before 0.22.18)' not in src:
        problems.append('TruMenu.cpp: the start line about an INI without [Menu] Load missing')
    if 'g_menuOldIni ? "TruMenu.ini without [Menu] Load' not in fn_body(src, 'void ToggleMenu('):
        problems.append('TruMenu.cpp: ToggleMenu must name the old INI as the reason')
    # DeviceGlyphs row on page Spiel-Einstellungen, group set_ctl
    st = [r for r in qb_rows(src, True) if r[0] == 'kQbSettings']
    grp, ok = None, False
    for r in st:
        if r[4] == 'kQbGroup': grp = r[3]
        elif r[2] == 'sw.set' and r[3] == 'TruMenu:Input:DeviceGlyphs' and r[4] == 'kQbSwitch' and grp == 'set_ctl': ok = True
    if not ok: problems.append('TruMenu.cpp: page Spiel-Einstellungen group set_ctl lacks the switch row DeviceGlyphs')
    if 'TruMenu:Input:DeviceGlyphs' not in sw_keys: problems.append('switches: TruMenu | Input | DeviceGlyphs missing')
    header, opt_rows = table(src)
    # 0.22.44 added none, 0.22.45 the three [Sound] wave log keys, 0.22.47 the seven sound monitor / sonar keys, 0.22.48
    # the three [Sonar] keys, 0.22.49 [Sonar] AllFloors + TriangleCap, 0.22.50 the 11 [Sound] keys of W8_KEYS_02250,
    # 0.22.51 the three keys of S5_KEYS_02251, 0.22.53 the six keys of W11_KEYS_02253, 0.22.54 [Sound] ResetAtStart,
    # 0.22.55 [Cheat] FlightKeepOnLoad, 0.22.58 [Chapter] UnitFresh + [Costume] DoppelLive, 0.22.59 [Puzzle] Help + HintFile,
    # 0.22.61 [Puzzle] ThorGap, 0.22.62 [Puzzle] Hints + Actions for Help (net 1), 0.22.66 [Sonar] KeepView, 0.22.68 [Puzzle]
    # ThorStep + ThorFoot + ThorGalleryDirect
    if len(opt_rows) != 283 + len(W6_KEYS_02245) + len(W7_KEYS_02247) + len(SO_KEYS_02248) + 2 + len(W8_KEYS_02250) + \
            len(S5_KEYS_02251) + len(W11_KEYS_02253) + 1 + 1 + 2 + 2 + 1 + 1 + 1 + 3:
        problems.append('TruMenu.cpp: kOpts has %d keys - 0.22.44 adds no INI key (283), 0.22.45 adds %d, 0.22.47 adds %d, '
                        '0.22.48 adds %d, 0.22.49 adds 2, 0.22.50 adds %d, 0.22.51 adds %d, 0.22.53 adds %d, 0.22.54 adds 1, '
                        '0.22.55 adds 1, 0.22.58 adds 2, 0.22.59 adds 2, 0.22.61 adds 1, 0.22.62 adds 1, 0.22.66 adds 1, '
                        '0.22.68 adds 3' % (
                            len(opt_rows), len(W6_KEYS_02245), len(W7_KEYS_02247), len(SO_KEYS_02248), len(W8_KEYS_02250),
                            len(S5_KEYS_02251), len(W11_KEYS_02253)))
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8').read()
    if '\n## 0.22.44 - ' not in readme or '\n### TO TEST 0.22.44' not in readme:
        problems.append('README.md: section "## 0.22.44 - ..." with "### TO TEST 0.22.44" missing')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if W2_HASH_02243 not in ps: problems.append('Set-TruMenu.ps1: the 0.22.43 build hash (work/asi/menu0266) is missing')
    n = {k: sum(1 for r in rows if r[4] == k) for k in ('kQbGroup', 'kQbCheck', 'kQbSwitch', 'kQbNote')}
    return problems, ('W2 order (page Tests: TG block %d rows - %d groups, %d checks, %d switch, %d notes, packages %s; '
                      'archive %s; Barrierefreiheit planned rows in acc_planned, acc_arachno; old INI keeps the big '
                      'window off; DeviceGlyphs on Spiel-Einstellungen; kQbViewMax 256)' %
                      (len(rows), n['kQbGroup'], n['kQbCheck'], n['kQbSwitch'], n['kQbNote'],
                       ' '.join(p.upper() for p in order), ' '.join(W2_ARCHIVED)))


W6_CHECKS_02245 = os.path.join(ROOT, 'work', 'w6_1411', 'precheck_02245.txt')
W6_HASH_02244 = 'c9d397f7849fe79e1ba891cde0067047fd118d0b98d1bf39857f63ca1a785164'
W6_KEYS_02245 = (('WaveLog', '1'), ('WaveIds', '10'), ('WaveLogMax', '500'))   # [Sound]
# item, type, game thread (queued)
W6_ITEMS_02245 = (('snd.mute', 'action', 'true'), ('snd.solo', 'action', 'true'), ('snd.mutes', 'info', 'false'),
                  ('snd.ambmute', 'bool', 'true'), ('snd.now', 'action', 'true'), ('snd.wavelog', 'action', 'true'),
                  ('music.stop', 'action', 'true'), ('music.next', 'action', 'true'), ('music.mute', 'bool', 'false'))
# the rows of the bar: (item, argument) in Paket B (tg_b) and in the group ton_einzeln of page Spiel-Einstellungen
W6_TGB_02245 = (('snd.ambmute', ''), ('music.mute', ''), ('snd.now', ''), ('snd.mute', '10'), ('snd.solo', '10'),
                ('snd.mute', 'all 0'), ('snd.mutes', ''), ('test.mark', 'tgB.wave10log'))
W6_SET_02245 = (('snd.ambmute', ''), ('music.mute', ''), ('music.stop', ''), ('music.next', ''), ('snd.now', ''),
                ('snd.mute', '10'), ('snd.solo', '10'), ('snd.mute', 'all 0'), ('snd.mutes', ''))


def check_02245(switches_path):
    """0.22.45 (W6 hearing tests, owner live notes of the test evening 13.11.; workspace docs/Befund-W6-Toene-1411.md):
    kW6Checks = precheck_02245.txt (15 rows: ChannelI validate 0x7c7e5a, wrapper pattern 0x7b9be0, ChannelI::setMute
    0x7c92b5 + its ret 4, getMute 0x7c9346, emitter vtable / section id / walker arguments, wave node params -> voice
    +0x1c, instance sound list); W6Check after SgCheck (needs g_snOk and g_smOk), W6ReadOptions after SgReadOptions,
    W6Tick from SnTick before the snd.list gate; per channel only through validate + ChannelI::setMute, unmute only the
    channels TruMenu muted (a channel muted by someone else is skipped); groups through SmSetMute with the SmMuted guard
    (never undo a foreign mute), ambience = group 15 + the '_amb_' beds; tracks through SndStopSlot, the way back only
    where MusicPlace allows; emitter = params - 0x14 with vtable 0x851240, owner from [inst+0x248] (+0xc slots * 0xc,
    +0x10 dynamic, end [0xcd3bb8]); wave log one line per new (voice, sample, channel), WaveLogMax; nothing written into
    game memory by the W6 functions; 9 items, 3 [Sound] keys, 2 switch rows, Paket B + group ton_einzeln rows; README
    0.22.45 with TO TEST; Set-TruMenu knows the 0.22.44 hash"""
    problems = []
    src = read_cpp()
    if '0.22.45 (W6 sound switches' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.46: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.45 part "0.22.45 (W6 sound switches"')
    offline = []
    if os.path.exists(W6_CHECKS_02245):
        for line in open(W6_CHECKS_02245, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if line:
                addr, hexs = line.split(None, 1)
                offline.append(('%08x' % int(addr, 16), hexs.replace(' ', '').lower()))
    else:
        problems.append('work/w6_1411/precheck_02245.txt (the offline byte list) is missing')
    rows = [(a.lower(), b.lower()) for a, b in sv_rows(src, 'kW6Checks')]
    if rows != offline or len(rows) != 15:
        problems.append('TruMenu.cpp: kW6Checks (%d rows) must be the 15 rows of precheck_02245.txt in order' % len(rows))
    ck = fn_body(src, 'void W6Check(')
    if 'g_w6Ok = g_snOk && g_smOk && DvChecks(kW6Checks,' not in ck:
        problems.append('TruMenu.cpp: W6Check must set g_w6Ok = g_snOk && g_smOk && DvChecks(kW6Checks, ...)')
    if not re.search(r'\n    SgCheck\(\);[^\n]*\n    W6Check\(\);', src):
        problems.append('TruMenu.cpp: the load must call W6Check right after SgCheck')
    if not re.search(r'\n    SgReadOptions\(ini\);[^\n]*\n    W6ReadOptions\(ini\);', src):
        problems.append('TruMenu.cpp: ReadOptions must call W6ReadOptions(ini) right after SgReadOptions(ini)')
    st = re.sub(r'//[^\n]*', '', fn_body(src, 'void SnTick('))
    if not 0 <= st.find('W6Tick();') < st.find('if (!g_snOk || !g_snOn) return;'):
        problems.append('TruMenu.cpp: SnTick must call W6Tick() before the snd.list gate')
    for need in ('kW6ChValidate = 0x007c7e5a', 'kW6ChSetMute = 0x007c92b5', 'kW6ChGetMute = 0x007c9346',
                 'kW6EmitterVtbl = 0x00851240', 'kW6ListEnd = 0x00cd3bb8', 'const int kW6AmbGroup = 15;'):
        if need not in src: problems.append('TruMenu.cpp: constant %s missing' % need)
    cm = fn_body(src, 'bool W6ChMute(')
    i_v, i_m = cm.find('reinterpret_cast<W6ValidateFn>(kW6ChValidate)(handle, &chan) != 0 || !chan) return false;'), \
        cm.find('reinterpret_cast<W6ChMuteFn>(kW6ChSetMute)(chan, nullptr, mute ? 1 : 0);')
    if not 0 <= i_v < i_m: problems.append('TruMenu.cpp: W6ChMute must validate the handle before ChannelI::setMute')
    if '__except' not in cm: problems.append('TruMenu.cpp: W6ChMute must run under __try / __except')
    em = fn_body(src, 'DWORD W6Emitter(')
    if 'ReadDword(params - 0x14, &vt) || vt != kW6EmitterVtbl) return 0;' not in em or 'return params - 0x14;' not in em:
        problems.append('TruMenu.cpp: W6Emitter must be params - 0x14 only with the vtable 0x851240')
    # 0.22.50: W6EmitterOwner (one walk over every instance per watched start) is gone - the same list walk lives in
    # W7OwnBuild (at most once a second while shown, check_02250)
    if 'bool W6EmitterOwner(' in src: problems.append('TruMenu.cpp: W6EmitterOwner must be gone (0.22.50)')
    ow = fn_body(src, 'void W7OwnBuild(')
    for need in ('ReadDword(x.addr + 0x248, &list)', 'ReadDword(list + 0xc, &slots)', 'ReadDword(slots + i * 0xc, &handle)',
                 'ReadDword(list + 0x10, &node)', 'node != listEnd', 'ReadDword(node + 4, &handle)'):
        if need not in ow: problems.append('TruMenu.cpp: W7OwnBuild lacks %s' % need)
    vt = fn_body(src, 'void W6VoiceTick(')
    for need in ('if (W6ChMuted(v.channel, &already) && already) continue;', 'g_w6Chan[g_w6ChanN++] = {v.voice, v.channel, true};',
                 'g_w6Seen[i].channel == v.channel', 'if (!old) W6WaveLine(v);'):
        if need not in vt: problems.append('TruMenu.cpp: W6VoiceTick lacks %s' % need)
    if vt.count('W6ChMute(') != 3 or vt.count('W6ChMute(v.channel, false);') != 1 or \
            vt.count('W6ChMute(g_w6Chan[i].channel, false);') != 1:
        problems.append('TruMenu.cpp: W6VoiceTick may unmute only the channels of g_w6Chan (3 W6ChMute calls)')
    cg = fn_body(src, 'void W6CgTick(')
    for need in ('if (SmMuted(cg)) {', 'c.ours = false; }', 'if (c.ours) {', 'SmMuted(cg) && SmSetMute(cg, false)',
                 'want[wn++] = kW6AmbGroup;'):
        if need not in cg: problems.append('TruMenu.cpp: W6CgTick lacks %s' % need)
    if 'const bool ok = SndStopSlot(s);' not in fn_body(src, 'void W6TrackTick('):
        problems.append('TruMenu.cpp: W6TrackTick must stop through SndStopSlot (the game\'s stop path)')
    tb = fn_body(src, 'void W6TrackBack(')
    if not 0 <= tb.find('if (!MusicPlace(why, sizeof(why))) {') < tb.find('reinterpret_cast<MusicLoadFn>(kMusicLoad)(s, g_w6Back[s],'):
        problems.append('TruMenu.cpp: W6TrackBack must ask MusicPlace before LoadMusic')
    if 'SndAmbName(name)' not in fn_body(src, 'bool W6TrackRuled('):
        problems.append('TruMenu.cpp: W6TrackRuled: ambience must name the \'_amb_\' beds (SndAmbName)')
    wl = fn_body(src, 'void W6WaveLine(')
    for need in ('g_w6WaveMax > 0 && g_w6WaveLines >= g_w6WaveMax', 'CurrentUnit(unit, sizeof(unit));',
                 'W7VoiceSource(v.emitter, W7KindOf(group, cat), v.wave, false, src, sizeof(src));',   # 0.22.50
                 '"snd.wave %d START #%ld: unit %s;'):
        if need not in wl: problems.append('TruMenu.cpp: W6WaveLine lacks %s' % need)
    if 'if (GetCurrentThreadId() != g_snGameThread) {' not in fn_body(src, 'bool RunW6Now('):
        problems.append('TruMenu.cpp: snd.now must run on the game thread only (FMOD queries, as snd.dump)')
    if 'if (GetCurrentThreadId() == g_snGameThread) W6Tick();' not in fn_body(src, 'void W6Apply('):
        problems.append('TruMenu.cpp: W6Apply may call W6Tick on the game thread only')
    for fn in ('bool W6ChMute(', 'bool W6ChMuted(', 'DWORD W6Emitter(', 'void W7OwnBuild(', 'void W6WaveLine(',
               'void W6CgTick(', 'void W6TrackTick(', 'void W6TrackBack(', 'void W6VoiceTick(', 'void W6Tick(',
               'bool W6Parse(', 'bool RunW6Mute(', 'bool RunW6Solo(', 'bool RunW6Now(', 'bool RunW6MusicStop(',
               'bool RunW6MusicNext(', 'void W6Check('):
        body = fn_body(src, fn)
        if not body: problems.append('TruMenu.cpp: %s missing' % fn.strip('(')); continue
        if any(w in body for w in ('WriteByte(', 'WriteBytes(', 'WriteDword(', 'reinterpret_cast<volatile', 'LcPatch(')):
            problems.append('TruMenu.cpp: %s must not write game memory' % fn.strip('('))
    for item, typ, gt in W6_ITEMS_02245:
        if not re.search(r'\{"%s", "%s", "0\.22\.45[^}]*?,\s+%s,\s+[A-Za-z0-9_<>]+,\s+[A-Za-z0-9_<>]+\},' %
                         (re.escape(item), typ, gt), src, re.S):
            problems.append('TruMenu.cpp: item %s (%s, game thread %s) missing in kItems' % (item, typ, gt))
    header, opt_rows = table(src)
    keys = {(s, k): d for s, k, d, _ in opt_rows}
    for key, default in W6_KEYS_02245:
        if keys.get(('Sound', key)) != default: problems.append('TruMenu.cpp: kOpts [Sound] %s=%s missing' % (key, default))
    sw = open(switches_path, encoding='utf-8').read()
    for row in ('TruMenu | Sound | WaveLog | bool |', 'TruMenu | Sound | WaveLogMax | int:0..5000:50 |'):
        if row not in sw: problems.append('switches: row "%s" missing' % row)
    tg, grp = set(), None
    for r in qb_rows(src):
        if r[0] == 'kQbTests' and r[4] == 'kQbGroup': grp = r[3]
        elif r[0] == 'kQbTests' and grp == 'tg_b': tg.add((r[2], r[3]))
    # 0.22.50 C: snd.ambmute / music.mute rows merged into the one "Ambient aus" / "Musik aus" (media.muteambient /
    # media.mutemusic, check_02250) - the items stay, their rows are no longer wanted here
    merged = (('snd.ambmute', ''), ('music.mute', ''))
    for it in W6_TGB_02245:
        if it not in tg and it not in merged: problems.append('TruMenu.cpp: Paket B (tg_b) lacks the row %s %s' % it)
    se, grp = set(), None
    for r in qb_rows(src):
        if r[0] == 'kQbSettings' and r[4] == 'kQbGroup': grp = r[3]
        elif r[0] == 'kQbSettings' and grp == 'ton_einzeln': se.add((r[2], r[3]))
    for it in W6_SET_02245:
        if it not in se and it not in merged:
            problems.append('TruMenu.cpp: page Spiel-Einstellungen group ton_einzeln lacks %s %s' % it)
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8').read()
    if '\n## 0.22.45 - ' not in readme or '\n### TO TEST 0.22.45' not in readme:
        problems.append('README.md: section "## 0.22.45 - ..." with "### TO TEST 0.22.45" missing')
    for key, _ in W6_KEYS_02245:
        if '`[Sound] %s`' % key not in readme: problems.append('README.md: options row `[Sound] %s` missing' % key)
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if W6_HASH_02244 not in ps: problems.append('Set-TruMenu.ps1: the 0.22.44 build hash (work/asi/menu0267) is missing')
    return problems, ('W6 sound switches (%d byte checks = precheck_02245; per channel ChannelI::setMute behind the '
                      'validate, groups / ambience ChannelGroupI::setMute, tracks srmusic stop; wave log; %d items, %d '
                      'keys, Paket B %d rows, ton_einzeln %d rows)' % (len(rows), len(W6_ITEMS_02245), len(W6_KEYS_02245),
                                                                     len(W6_TGB_02245), len(W6_SET_02245)))


FE_CHECKS_02246 = os.path.join(ROOT, 'work', 'arena_1411', 'precheck_02246.txt')
FE_HASH_02245 = '95246e56abd1950bf8623b683cd4d301578c58b738351c008990d22afce77639'
FE_MENU_STEPS_02246 = ('"save.backup kapitel;level.start %s 0;wait.unit %s;cheat.flight 1;player.goto %ld force;"\n'
                       '        "%sarena.mode %s"')
FE_LEVEL_STEPS_02232 = '"save.backup kapitel;%s %s;wait.unit %s;cheat.flight 1;player.goto %ld force;arena.mode %s"'


def check_02246():
    """0.22.46 (arena from the main menu, owner live 2026-11-14 12:07; workspace docs/Befund-Arena-Hauptmenue-1411.md):
    kFeChecks = precheck_02246.txt (10 rows: the request 0x5df760 sets +0xb9 / +0xb8, 0x5df8c0 ignores a request while
    +0xb9 is set, only main state 1 serves one (0x5e0050 -> 0x5dab40), the dispatcher table entries 1 / 10, the state-10
    handler without the tracker and its switch on 0xfae8da, state 2 clears +0xb9 (0x5de864), the game's front-end save
    load clears it itself (0x7744ce), the front-end state getter); FeCheck right after PendingCheck; LevelChangePending
    ignores +0xb9 only through FeStaleRequest (main state 10); level.load refused in the front end (FeInFrontEnd, main
    state 6 / 10) after the pending test and before the request; level.start takes a second word 0|1 as f27's selection
    argument (0 only with g_outfitRuleOk); the shortcut runner waits for the unit of "level.start <unit> 0|1" and logs
    "level up"; RunArenaGo: main menu -> ArenaGoMenu before the mode read, no level -> refused, a cutscene -> refused,
    the in-level steps unchanged; ArenaGoMenu: gates (g_feOk, mission path, experimental), front-end state 3, no one-shot
    movie, steps backup / level.start <unit> 0 / wait.unit / flight / player.goto force / cheat.onehitkill 0 (cheats on) /
    arena.mode, one log line, nothing written by itself; arena.mode logs the unit and the one-hit kill byte; Paket A
    note names the main menu; README 0.22.46 with TO TEST; Set-TruMenu knows the 0.22.45 hash"""
    problems = []
    src = read_cpp()
    if '0.22.46 (arena from the main menu' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.47: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.46 part "0.22.46 (arena from the main menu"')
    offline = []
    if os.path.exists(FE_CHECKS_02246):
        for line in open(FE_CHECKS_02246, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if line:
                addr, hexs = line.split(None, 1)
                offline.append(('%08x' % int(addr, 16), hexs.replace(' ', '').lower()))
    else:
        problems.append('work/arena_1411/precheck_02246.txt (the offline byte list) is missing')
    m = re.search(r'const FeRow kFeChecks\[\] = \{(.*?)\n\};', src, re.S)
    rows = [(a.lower(), ''.join(LIT.findall(b)).replace(' ', '').lower()) for a, b in
            re.findall(r'\{0x([0-9a-fA-F]{8}), ((?:"[0-9a-f ]+"\s*)+)\}', m.group(1) if m else '')]
    if rows != offline or len(rows) != 10:
        problems.append('TruMenu.cpp: kFeChecks (%d rows) must be the 10 rows of precheck_02246.txt in order' % len(rows))
    if not re.search(r'\n    g_pendingOk = PendingCheck\(\);\n    FeCheck\(\);', src):
        problems.append('TruMenu.cpp: the load must call FeCheck right after g_pendingOk = PendingCheck()')
    fc = fn_body(src, 'void FeCheck(')
    if 'g_feOk = g_mainStateOk && g_pendingOk;' not in fc or '!HexBytesAt(r.at, r.hex)' not in fc or 'Log(' not in fc:
        problems.append('TruMenu.cpp: FeCheck must test every kFeChecks row after the main state / pending checks and log')
    st = fn_body(src, 'bool FeStaleRequest(')
    if 'g_feOk && g_mainStateOk && ReadDword(kMainState, &state) && state == 10' not in st:
        problems.append('TruMenu.cpp: FeStaleRequest = g_feOk and main state 10 only')
    fe = fn_body(src, 'bool FeInFrontEnd(')
    if '(*state == 6 || *state == 10)' not in fe or 'g_feOk && g_mainStateOk' not in fe:
        problems.append('TruMenu.cpp: FeInFrontEnd = g_feOk and main state 6 / 10')
    lp = fn_body(src, 'bool LevelChangePending(')
    if 'if (((busy >> 8) & 0xff) && !FeStaleRequest()) {' not in lp or lp.count('FeStaleRequest') != 1:
        problems.append('TruMenu.cpp: LevelChangePending may skip +0xb9 only through FeStaleRequest')
    lu = fn_body(src, 'bool LoadUnit(')
    i_p, i_f, i_c = lu.find('LevelChangePending(why, sizeof(why))'), lu.find('if (FeInFrontEnd(&feState)) {'), \
        lu.find('reinterpret_cast<LevelChangeFn>(kLevelChange)')
    if not 0 <= i_p < i_f < i_c: problems.append('TruMenu.cpp: LoadUnit must refuse the front end before the request')
    ls = fn_body(src, 'bool RunLevelStart(')
    for want in ('int select = given >= 0 ? given : MissionSelectArg(unit);', 'if (given == 0 && !g_outfitRuleOk) {'):
        if want not in ls: problems.append('TruMenu.cpp: RunLevelStart must hold %s' % want)
    # 0.22.58 (S1): a third word "mark" is allowed - the usage rule then reads words > 3 || (words == 3 && !mark) || ...
    if 'words > 2 || (words == 2 && given < 0)' not in ls and \
            'words > 3 || (words == 3 && !mark) || (words == 2 && given < 0)' not in ls:
        problems.append('TruMenu.cpp: RunLevelStart must refuse extra words (words > 2 / > 3 with mark)')
    sc = fn_body(src, 'void ShortcutTick(')
    if 'if (!_strnicmp(step, "level.start ", 12)) {' not in sc or 'StartUnitName(u, g_scWaitUnit, sizeof(g_scWaitUnit))' \
            not in sc or 'level up - unit %s' not in sc:
        problems.append('TruMenu.cpp: ShortcutTick must wait for the unit of level.start <unit> 0|1 and log "level up"')
    go = fn_body(src, 'bool RunArenaGo(')
    i_l, i_m, i_r, i_c, i_mode = go.find('LevelChangePending(why, sizeof(why))'), \
        go.find('if (stateOk && state == 10) return ArenaGoMenu(a, o, n);'), go.find('if (!InLevel()) {'), \
        go.find('if (CinematicNow()) {'), go.find('ArenaModeRead(m);')
    if not 0 <= i_l < i_m < i_r < i_c < i_mode:
        problems.append('TruMenu.cpp: RunArenaGo: pending test, main menu -> ArenaGoMenu, no level / cutscene refused, '
                        'then the 0.22.32 mode read')
    if FE_LEVEL_STEPS_02232 not in go: problems.append('TruMenu.cpp: RunArenaGo: the in-level steps must stay (0.22.32)')
    am = fn_body(src, 'bool ArenaGoMenu(')
    for want in (FE_MENU_STEPS_02246, 'ohk ? "cheat.onehitkill 0;" : ""', 'const bool ohk = g_cheatsEnabled && g_ohkOk;',
                 'if (!g_feOk || !g_missionOk || !g_experimental) {', 'ReadByte(kFeStateByte, &fe);', 'if (fe != 3) {',
                 'movie && ReadByte(kW3BinkLoop, &loop) && !loop', 'Log(1, "arena.go %s: main menu',
                 'if (!ShortcutStart(steps, title, o, n)) return false;'):
        if want not in am: problems.append('TruMenu.cpp: ArenaGoMenu must hold %s' % want.replace('\n', ' '))
    for fn in ('bool ArenaGoMenu(', 'bool FeStaleRequest(', 'bool FeInFrontEnd(', 'void FeCheck(', 'bool RunArenaMode('):
        body = fn_body(src, fn)
        if not body: problems.append('TruMenu.cpp: %s missing' % fn.strip('(')); continue
        if any(w in body for w in ('WriteByte(', 'PutByte(', 'WriteDword(', 'reinterpret_cast<volatile', 'LcPatch(')):
            problems.append('TruMenu.cpp: %s must not write game memory' % fn.strip('('))
    mo = fn_body(src, 'bool RunArenaMode(')
    if 'one-hit kill byte 0x%08lx = %d%s' not in mo or 'CurrentUnit(unit, sizeof(unit));' not in mo:
        problems.append('TruMenu.cpp: arena.mode must log the unit and the one-hit kill byte')
    note, grp = None, None
    for r in qb_rows(src):
        if r[0] == 'kQbTests' and r[4] == 'kQbGroup': grp = r[3]
        elif r[0] == 'kQbTests' and grp == 'tg_a' and r[4] == 'kQbNote' and note is None: note = r[1]
    if not note or 'Hauptmen' not in note: problems.append('TruMenu.cpp: the Paket A note must name the main menu')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8').read()
    if '\n## 0.22.46 - ' not in readme or '\n### TO TEST 0.22.46' not in readme:
        problems.append('README.md: section "## 0.22.46 - ..." with "### TO TEST 0.22.46" missing')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if FE_HASH_02245 not in ps: problems.append('Set-TruMenu.ps1: the 0.22.45 build hash (work/asi/menu0268) is missing')
    return problems, ('arena from the main menu (%d byte checks = precheck_02246; +0xb9 in main state 10 = unserved '
                      'request, level.load refused in the front end, arena.go -> level.start <unit> 0 + wait + spot + '
                      'one-hit kill off + arena.mode)' % len(rows))


W7_CHECKS_02247 = os.path.join(ROOT, 'work', 'sndui_1411', 'precheck_02247.txt')
W7_HASH_02246 = '8358f69fd09a1092708448a8a0bbe9b7abb9c2b58ac2f6b4839ebb306c008876'
W7_KEYS_02247 = (('History', '1'), ('HistoryMax', '30'), ('HistoryLog', '0'), ('OverlayStyle', '1'), ('LogFadeSec', '15'),
                 ('SonarMute', '0'), ('SonarWaves', '914 915 916'))   # [Sound]
# item, type, game thread (queued)
W7_ITEMS_02247 = (('snd.monitor', 'action', 'true'), ('snd.history', 'action', 'true'), ('snd.logview', 'bool', 'false'),
                  ('snd.sonar', 'bool', 'true'), ('snd.sonar57', 'bool', 'true'))
W7_SET_02247 = (('snd.sonar', '', 'kQbBool'), ('snd.sonar57', '', 'kQbBool'), ('snd.list', '', 'kQbBool'),
                ('snd.logview', '', 'kQbBool'), ('snd.monitor', 'rules', 'kQbSndMon'), ('snd.monitor', 'voices', 'kQbSndMon'),
                ('snd.monitor', 'history', 'kQbSndMon'), ('snd.monitor', '', 'kQbAction'), ('snd.mute', 'all 0', 'kQbAction'))
W7_TGB_02247 = (('snd.sonar', '', 'kQbBool'), ('snd.monitor', 'voices', 'kQbSndMon'), ('snd.monitor', 'history', 'kQbSndMon'),
                ('test.mark', 'tgB.sonar', 'kQbCheck'), ('test.mark', 'tgB.monitor', 'kQbCheck'))
W7_SWITCHES_02247 = ('TruMenu | Sound | SonarMute | int:0..2:1 |', 'TruMenu | Sound | OverlayStyle | bool |',
                     'TruMenu | Sound | History | bool |', 'TruMenu | Sound | HistoryMax | int:5..200:5 |',
                     'TruMenu | Sound | HistoryLog | bool |', 'TruMenu | Sound | LogFadeSec | int:0..120:5 |')


def check_02247(switches_path):
    """0.22.47 (sound monitor, log overlay, sonar sound off; owner wishes 2026-11-14, workspace
    docs/Befund-Tonanzeige-1411.md): kW7Checks = precheck_02247.txt (6 rows: Play gets the wave entry's +4, Wave_Find's
    entry layout, the wave node's new 0x90 params object and its ctor +0x74 = the node's params, ret 0x14); W7Check right
    after W6Check, W7ReadOptions(ini, dir) right after W6ReadOptions; the wave id from W7Wave (map entry +4 -> id, the old
    (sample - table) / 0x18 gone from SnBuild and W6VoiceTick), the emitter from W7Emitter (params -> +0x74, at most 4
    steps, decided by W6Emitter's vtable test); the sonar switch per channel inside W6VoiceTick's want test (no new
    W6ChMute call), group 57 only as SonarMute 2 through W6CgTick; SonarMute / OverlayStyle written back with IniKeepInt;
    the overlay as a log (DrawSoundList -> DrawSoundLog), icons only ImDrawList primitives; the monitor rows (kQbSndMon in
    QbBuild, src <= kQbSmSrc first in QuickTick, the long menu W7MenuRows); SnTick builds the list for the rows without
    snd.list, Render runs SnTick from the Present hook while the game polls no pad (main menu) on the pad thread only;
    no game memory written by the W7 functions; 5 items, 7 [Sound] keys, 6 switch rows, group ton_monitor + Paket B rows;
    README 0.22.47 with TO TEST; Set-TruMenu knows the 0.22.46 hash"""
    problems = []
    src = read_cpp()
    if '0.22.47 (sound monitor' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.48: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.47 part "0.22.47 (sound monitor"')
    offline = []
    if os.path.exists(W7_CHECKS_02247):
        for line in open(W7_CHECKS_02247, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if line:
                addr, hexs = line.split(None, 1)
                offline.append(('%08x' % int(addr, 16), hexs.replace(' ', '').lower()))
    else:
        problems.append('work/sndui_1411/precheck_02247.txt (the offline byte list) is missing')
    rows = [(a.lower(), b.lower()) for a, b in sv_rows(src, 'kW7Checks')]
    if rows != offline or len(rows) != 6:
        problems.append('TruMenu.cpp: kW7Checks (%d rows) must be the 6 rows of precheck_02247.txt in order' % len(rows))
    if 'g_w7Ok = g_w6Ok && DvChecks(kW7Checks,' not in fn_body(src, 'void W7Check('):
        problems.append('TruMenu.cpp: W7Check must set g_w7Ok = g_w6Ok && DvChecks(kW7Checks, ...)')
    if not re.search(r'\n    W6Check\(\);[^\n]*\n    W7Check\(\);', src):
        problems.append('TruMenu.cpp: the load must call W7Check right after W6Check')
    if not re.search(r'\n    W6ReadOptions\(ini\);[^\n]*\n    W7ReadOptions\(ini, dir\);', src):
        problems.append('TruMenu.cpp: ReadOptions must call W7ReadOptions(ini, dir) right after W6ReadOptions(ini)')
    sb, vt = fn_body(src, 'int SnBuild('), fn_body(src, 'void W6VoiceTick(')
    for name, body in (('SnBuild', sb), ('W6VoiceTick', vt)):
        if 'v.wave = W7Wave(v.sample);' not in body or 'v.emitter = W7Emitter(v.params);' not in body:
            problems.append('TruMenu.cpp: %s must take the wave from W7Wave and the emitter from W7Emitter' % name)
        if 'waveLo' in body or ') / 0x18)' in body:
            problems.append('TruMenu.cpp: %s still holds the 0.20.1 wave id (sample - table) / 0x18' % name)
    if 'if (!want && sonar && W7SonarWave(v.wave)) want = true;' not in vt or 'if (hist) W7HistVoice(v);' not in vt:
        problems.append('TruMenu.cpp: W6VoiceTick must test the sonar waves in its want test and feed the history')
    mb = fn_body(src, 'void W7MapBuild(')
    for need in ('ReadDword(entry, &loaded) || !loaded', 'ReadDword(entry + 4, &sample)', 'mgr + 8 + static_cast<DWORD>(i) * 0x18',
                 'qsort('):
        if need not in mb: problems.append('TruMenu.cpp: W7MapBuild lacks %s' % need)
    em = fn_body(src, 'DWORD W7Emitter(')
    for need in ('const DWORD e = W6Emitter(p);', 'ReadDword(p + 0x74, &up)', 'depth < 4;'):
        if need not in em: problems.append('TruMenu.cpp: W7Emitter lacks %s' % need)
    if 'if (W7SonarMode() == 2 && wn < kW6CgMax) want[wn++] = kW7SonarGroup;' not in fn_body(src, 'void W6CgTick('):
        problems.append('TruMenu.cpp: W6CgTick must mute group 57 only for SonarMute 2')
    for need in ('const int kW7SonarGroup = 57;', 'int g_w7SonarWaves[8] = {914, 915, 916,', 'kQbSndMon };',
                 'const int kQbSmSrc = -1000;', '{914, "computer_hum_12"}', '{915, "computer_hum_04"}', '{916, "alrm_radar_03"}'):
        if need not in src: problems.append('TruMenu.cpp: %s missing' % need)
    if 'IniKeepInt("Sound", "SonarMute", mode);' not in fn_body(src, 'void W7SonarSet('):
        problems.append('TruMenu.cpp: W7SonarSet must keep [Sound] SonarMute (IniKeepInt)')
    if 'IniKeepInt("Sound", "OverlayStyle", g_w7Style);' not in fn_body(src, 'bool RunW7LogView('):
        problems.append('TruMenu.cpp: snd.logview must keep [Sound] OverlayStyle (IniKeepInt)')
    if 'if (g_w7Style == 1) { DrawSoundLog(); return; }' not in fn_body(src, 'void DrawSoundList('):
        problems.append('TruMenu.cpp: DrawSoundList must hand over to DrawSoundLog with OverlayStyle 1')
    ic = fn_body(src, 'void W7Icon(')
    if not ic or re.search(r'\\x[fF]0|\\36[0-7]|AddText', ic):
        problems.append('TruMenu.cpp: W7Icon must draw with ImDrawList primitives only (no font glyphs)')
    st = re.sub(r'//[^\n]*', '', fn_body(src, 'void SnTick('))
    i_w, i_g = st.find('if (g_snOk && !g_snOn && W7SnapWanted()) { W7SnapTick(); return; }'), \
        st.find('if (!g_snOk || !g_snOn) return;')
    if not 0 <= st.find('W6Tick();') < i_w < i_g:
        problems.append('TruMenu.cpp: SnTick: W6Tick, then the monitor list without snd.list, then the snd.list gate')
    if 'W7PresentTick(padIdle);' not in re.sub(r'//[^\n]*', '', fn_body(src, 'void Render(')):
        problems.append('TruMenu.cpp: Render must call W7PresentTick(padIdle)')
    if 'const int state = !g_snGameThread || g_snGameThread == me ? 1 : 0;' not in fn_body(src, 'void W7PresentTick('):
        problems.append('TruMenu.cpp: W7PresentTick may run SnTick only on the pad thread (or before any pad poll)')
    qb = fn_body(src, 'void QbBuild(')
    if 'if (r.kind == kQbSndMon) {' not in qb or 'W7QbRows(g_qbView + g_qbViewN, room, r.arg, lv, de)' not in qb \
            or 'W7QbReset();' not in qb:
        problems.append('TruMenu.cpp: QbBuild must put the live monitor rows in place of a kQbSndMon row')
    qt = fn_body(src, 'void QuickTick(')
    i_m, i_s = qt.find('if (g_qbView[row].src <= kQbSmSrc) {'), qt.find('const QbRow *src =')
    if not 0 <= i_m < i_s: problems.append('TruMenu.cpp: QuickTick must hand a monitor row to W7QbAct first')
    if 'W7MenuRows(r.arg, page, index);' not in fn_body(src, 'void PageQbRow('):
        problems.append('TruMenu.cpp: the long menu must draw a kQbSndMon row through W7MenuRows')
    for fn in ('void W7MapBuild(', 'int W7Wave(', 'DWORD W7Emitter(', 'void W7OwnBuild(', 'void W7HistAdd(', 'void W7Check(',
               'void W7HistVoice(', 'void W7HistEnd(', 'void W7SnapTick(', 'void W7ReadOptions(', 'void W7NamesLoad(',
               'void W7SonarSet(', 'bool RunW7Monitor(', 'bool RunW7History(', 'int W7QbRows(', 'void W7QbAct(',
               'void DrawSoundLog(', 'void W7PresentTick('):
        body = fn_body(src, fn)
        if not body: problems.append('TruMenu.cpp: %s missing' % fn.strip('(')); continue
        if any(w in body for w in ('WriteByte(', 'WriteBytes(', 'WriteDword(', 'reinterpret_cast<volatile', 'LcPatch(',
                                   'VirtualProtect(')):
            problems.append('TruMenu.cpp: %s must not write game memory' % fn.strip('('))
    for item, typ, gt in W7_ITEMS_02247:
        if not re.search(r'\{"%s", "%s", "0\.22\.47[^}]*?,\s+%s,\s+[A-Za-z0-9_<>]+,\s+[A-Za-z0-9_<>]+\},' %
                         (re.escape(item), typ, gt), src, re.S):
            problems.append('TruMenu.cpp: item %s (%s, game thread %s) missing in kItems' % (item, typ, gt))
    header, opt_rows = table(src)
    keys = {(s, k): d for s, k, d, _ in opt_rows}
    for key, default in W7_KEYS_02247:
        if keys.get(('Sound', key)) != default: problems.append('TruMenu.cpp: kOpts [Sound] %s=%s missing' % (key, default))
    sw = open(switches_path, encoding='utf-8').read()
    for row in W7_SWITCHES_02247:
        if row not in sw: problems.append('switches: row "%s" missing' % row)
    se, tg, grp = set(), set(), None
    for r in qb_rows(src):
        if r[4] == 'kQbGroup': grp = r[3]; continue
        if r[0] == 'kQbSettings' and grp == 'ton_monitor': se.add((r[2], r[3], r[4]))
        if r[0] == 'kQbTests' and grp == 'tg_b': tg.add((r[2], r[3], r[4]))
    for it in W7_SET_02247:
        if it not in se: problems.append('TruMenu.cpp: page Spiel-Einstellungen group ton_monitor lacks %s %s (%s)' % it)
    for it in W7_TGB_02247:
        if it not in tg: problems.append('TruMenu.cpp: Paket B (tg_b) lacks the row %s %s (%s)' % it)
    if 'ton_monitor' not in [r[3] for r in qb_rows(src) if r[0] == 'kQbSettings' and r[4] == 'kQbGroup']:
        problems.append('TruMenu.cpp: page Spiel-Einstellungen lacks the group ton_monitor')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8').read()
    if '\n## 0.22.47 - ' not in readme or '\n### TO TEST 0.22.47' not in readme:
        problems.append('README.md: section "## 0.22.47 - ..." with "### TO TEST 0.22.47" missing')
    for key, _ in W7_KEYS_02247:
        if '`[Sound] %s`' % key not in readme: problems.append('README.md: options row `[Sound] %s` missing' % key)
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if W7_HASH_02246 not in ps: problems.append('Set-TruMenu.ps1: the 0.22.46 build hash (work/asi/menu0269) is missing')
    return problems, ('sound monitor (%d byte checks = precheck_02247; wave id from the entry +4 map, emitter via +0x74; '
                      'sonar waves per channel / group 57 fallback; log overlay; %d items, %d keys, ton_monitor %d rows, '
                      'Paket B %d rows)' % (len(rows), len(W7_ITEMS_02247), len(W7_KEYS_02247), len(W7_SET_02247),
                                            len(W7_TGB_02247)))


SO_CHECKS_02248 = os.path.join(ROOT, 'work', 'menu48_1411', 'precheck_02248.txt')
SO_HASH_02247 = 'c78918209e28ff41be82bf5deea56739b2f23a37e9736e027c3eb563a37c628b'   # work/asi/menu0270
SO_KEYS_02248 = (('FullMap', '0'), ('HidePlaceholder', '1'), ('FloorMarkers', '0'))   # [Sonar]
# item, type, game thread (queued)
SO_ITEMS_02248 = (('sonar.full', 'bool', 'true'), ('sonar.placeholder', 'bool', 'true'), ('sonar.markers', 'bool', 'true'),
                  ('sonar.status', 'info', 'false'))
# the patch sites: (constant, address, the game's bytes, ours) - ours of H3 is the call built at run time
SO_SITES_02248 = (('kSoC1', '0x006e3b25', '0x0f, 0x94, 0xc3', '0xb3, 0x01, 0x90'),
                  ('kSoC2', '0x006e3b59', '0x0f, 0x94, 0x44, 0x24, 0x11', '0xc6, 0x44, 0x24, 0x11, 0x01'),
                  ('kSoC3', '0x006e3ba2', '0x0f, 0x94, 0x44, 0x24, 0x12', '0xc6, 0x44, 0x24, 0x12, 0x01'),
                  ('kSoH3', '0x006e3ab0', '0x8b, 0x41, 0x44, 0x85, 0xc0', None),
                  ('kSoC4', '0x006e40c6', '0x74, 0x40', '0x90, 0x90'))
# the rows of the bar: page Spiel-Einstellungen group set_sonar
SO_SET_02248 = (('sonar.full', '', 'kQbBool'), ('sonar.placeholder', '', 'kQbBool'), ('sonar.markers', '', 'kQbBool'),
                ('sonar.status', '', 'kQbInfo'), ('snd.sonar', '', 'kQbBool'))
# page Figur group fig_adren: TruMenu's items and every TruShadowCombat [Adrenaline] switch (+ [Conditions] Enabled)
SO_ADREN_ITEMS_02248 = (('adren.meter', '', 'kQbInfo'), ('adren.fill', '', 'kQbAction'), ('adren.keep', '', 'kQbBool'))
SO_ADREN_DEP_02248 = 'TruShadowCombat:Conditions:Enabled'
SO_TGA_02248 = ('TruShadowCombat:Adrenaline:ModeWithoutTarget', 'TruShadowCombat:Adrenaline:StrikeWithoutButton',
                'TruShadowCombat:Adrenaline:StrikeWithoutFullMeter')
# the sites of the finding's options A / B (they reveal for real and end up in the save) - never in TruMenu
SO_NOT_02248 = ('0x006deed5', '0x006deeeb', '0x006e3686', '0x006e3783', '0x006e4b06', '0x006dfb1d')


def check_02248(switches_path):
    """0.22.48 (owner wishes 2026-11-14; workspace docs/Befund-TruMenu-02248-1411.md): (1) page Figur group fig_adren owns
    adren.meter / adren.fill / adren.keep and every TruShadowCombat [Adrenaline] switch of TruMenu.switches.txt (kQbSwitch
    rows + the [Conditions] Enabled row and a note naming it), page Tests rows of adrenaline items / switches are copies
    of rows on page Figur, Paket A holds the 0.6.15 test switches; the rows ModeWithoutTarget / StrikeWithoutButton are
    live (SW_LIVE M15ReadSwitches) and the hints of StrikeWithoutButton / StrikeWithoutFullMeter name [Conditions]
    Enabled=1; (2) teaser default 12 (checked in check_02240 / check_02241 by AT_DEFAULT); (3) page Kapitel without
    "(debug)" (check_0217), no package name 17p / 17s in any string of the code; (4) Sonar komplett = kSoChecks the 13 rows
    of precheck_02248.txt, SoCheck after W7Check, SoReadOptions after W7ReadOptions, SoTick in PadHook every poll before
    the clock test, the five sites with the finding's bytes, the stub (face count, 0 for 100 faces + 56 vertices, test
    eax, ret), H3 / C4 only with FullMap, writes only through SoWrite over the expected bytes, the triangle-cap line reads
    only, no site of the options A / B; 3 [Sonar] keys, 4 items, 3 live switch rows (group tmsonar), page
    Spiel-Einstellungen group set_sonar (with a copy of snd.sonar), Paket G (check_02244); (5) docs/Regression-DLC2.md
    step 24 and tests/regress/dlc2.txt step 6 without level.load in the main menu; README 0.22.48 with TO TEST, options
    rows; Set-TruMenu knows the 0.22.47 hash"""
    problems = []
    src = read_cpp()
    code = re.sub(r'//[^\n]*', '', src)
    if '0.22.48 (adrenaline at Lara + sonar full map' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.49: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.48 part "0.22.48 (adrenaline at Lara + sonar full map"')
    # ---- (1) adrenaline at Lara
    sw_rows = {}
    for line in open(switches_path, encoding='utf-8').read().splitlines():
        f = [x.strip() for x in line.split('|')]
        if line.startswith('#') or len(f) < 9 or f[0] == 'group': continue
        sw_rows['%s:%s:%s' % (f[0], f[1], f[2])] = f
    adren_sw = sorted(k for k in sw_rows if k.startswith('TruShadowCombat:Adrenaline:'))
    lara, grp, in_adren = [], None, []
    for r in qb_rows(src):
        if r[0] != 'kQbLara': continue
        lara.append((r[2], r[3], r[4]))
        if r[4] == 'kQbGroup': grp = r[3]; continue
        if grp == 'fig_adren': in_adren.append((r[2], r[3], r[4]))
    if ('-', 'fig_adren', 'kQbGroup') not in lara: problems.append('TruMenu.cpp: page Figur lacks the group fig_adren')
    for it in SO_ADREN_ITEMS_02248:
        if it not in in_adren: problems.append('TruMenu.cpp: group fig_adren lacks %s (%s)' % (it[0], it[2]))
    for key in adren_sw + [SO_ADREN_DEP_02248]:
        if ('sw.set', key, 'kQbSwitch') not in in_adren:
            problems.append('TruMenu.cpp: group fig_adren lacks the switch row %s' % key)
    if len(adren_sw) != 8: problems.append('switches: %d TruShadowCombat [Adrenaline] rows, 8 expected' % len(adren_sw))
    for it in in_adren:
        if it[2] == 'kQbSwitch' and it[1] not in sw_rows:
            problems.append('TruMenu.cpp: fig_adren switch row %s not in %s' % (it[1], os.path.basename(switches_path)))
    block = src[src.find('const QbRow kQbLara[] = {'):]
    block = block[:block.find('\n};')]
    notes = re.findall(r'\{"([^"]*)",\s+"[^"]*",\s+"-",\s+"",\s+kQbNote', block)
    if not any('[Conditions] Enabled=1' in n for n in notes):
        problems.append('TruMenu.cpp: group fig_adren needs a note naming [Conditions] Enabled=1')
    tests = [(r[2], r[3], r[4]) for r in qb_rows(src) if r[0] == 'kQbTests']
    lara_items = {(i, a) for i, a, k in lara}
    for item, arg, kind in tests:
        adren = item.startswith('adren.') or (item == 'sw.set' and arg.startswith('TruShadowCombat:Adrenaline:'))
        if adren and (item, arg) not in lara_items:
            problems.append('TruMenu.cpp: page Tests row %s %s is no copy of a page Figur row' % (item, arg))
    tga, grp = set(), None
    for r in qb_rows(src):
        if r[0] != 'kQbTests': continue
        if r[4] == 'kQbGroup': grp = r[3]; continue
        if grp == 'tg_a' and r[2] == 'sw.set': tga.add(r[3])
    for key in SO_TGA_02248:
        if key not in tga: problems.append('TruMenu.cpp: Paket A lacks the copy of %s' % key)
    for key in ('TruShadowCombat:Adrenaline:ModeWithoutTarget', 'TruShadowCombat:Adrenaline:StrikeWithoutButton'):
        f = sw_rows.get(key)
        if not f or f[6] != 'live': problems.append('switches: %s must be live (M15ReadSwitches)' % key)
        if SW_LIVE.get(tuple(key.split(':'))) != 'void M15ReadSwitches(':
            problems.append('trumenu_ini_check: SW_LIVE lacks %s -> M15ReadSwitches' % key)
    for key in ('TruShadowCombat:Adrenaline:StrikeWithoutButton', 'TruShadowCombat:Adrenaline:StrikeWithoutFullMeter'):
        f = sw_rows.get(key)
        if not f or f[8].count('[Conditions] Enabled=1') != 2:
            problems.append('switches: the hint of %s must name [Conditions] Enabled=1 (DE and EN)' % key)
    # ---- (3) chapter page: no package names in the strings of the code
    shown = re.sub(r'const char \*const kVersion = [^\n]*', '', code)   # the version history keeps its old words
    pk = sorted({s for s in LIT.findall(shown) if re.search(r'\b17[ps]\b', s)})
    if pk: problems.append('TruMenu.cpp: strings still name the packages 17p / 17s: %s' % ' | '.join(x[:50] for x in pk))
    # ---- (4) Sonar komplett
    offline = []
    if os.path.exists(SO_CHECKS_02248):
        for line in open(SO_CHECKS_02248, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if line:
                addr, hexs = line.split(None, 1)
                offline.append(('%08x' % int(addr, 16), hexs.replace(' ', '').lower()))
    else:
        problems.append('work/menu48_1411/precheck_02248.txt (the offline byte list) is missing')
    rows = [(a.lower(), b.lower()) for a, b in sv_rows(src, 'kSoChecks')]
    if rows[:13] != offline or len(offline) != 13:   # 0.22.49: 3 rows appended (check_02249 = precheck_02249.txt)
        problems.append('TruMenu.cpp: kSoChecks (%d rows) must start with the 13 rows of precheck_02248.txt in order' % len(rows))
    if 'g_soOk = DvChecks(kSoChecks,' not in fn_body(src, 'void SoCheck('):
        problems.append('TruMenu.cpp: SoCheck must set g_soOk = DvChecks(kSoChecks, ...)')
    if not re.search(r'\n    W7Check\(\);[^\n]*\n    SoCheck\(\);', src):
        problems.append('TruMenu.cpp: the load must call SoCheck right after W7Check')
    if not re.search(r'\n    W7ReadOptions\(ini, dir\);[^\n]*\n    SoReadOptions\(ini\);', src):
        problems.append('TruMenu.cpp: ReadOptions must call SoReadOptions(ini) right after W7ReadOptions')
    ph = re.sub(r'//[^\n]*', '', fn_body(src, 'DWORD WINAPI PadHook('))
    i_so, i_clock = ph.find('SoTick();'), ph.find('DWORD clock = *kGameClock;')
    if not 0 <= i_so < i_clock: problems.append('TruMenu.cpp: PadHook must call SoTick every poll (before the clock test)')
    for name, addr, game, ours in SO_SITES_02248:
        if not re.search(r'\b%s = %s\b' % (name, addr), src): problems.append('TruMenu.cpp: %s = %s missing' % (name, addr))
        if not re.search(r'%sGame\[\d\] = \{%s\}' % (name, re.escape(game)), src):
            problems.append('TruMenu.cpp: %sGame must be {%s}' % (name, game))
        if ours and not re.search(r'%sNew\[\d\] = \{%s\}' % (name, re.escape(ours)), src):
            problems.append('TruMenu.cpp: %sNew must be {%s}' % (name, ours))
    stub = re.sub(r'//[^\n]*', '', fn_body(src, '__declspec(naked) void SoPlaceholderStub('))
    seq = ('mov eax, dword ptr [ecx + 0x44]', 'cmp eax, 100', 'jne so_keep', 'cmp dword ptr [ecx + 0x48], 56', 'jne so_keep',
           'xor eax, eax', 'so_keep:', 'test eax, eax', 'ret')
    at = 0
    for s in seq:
        at = stub.find(s, at)
        if at < 0: problems.append('TruMenu.cpp: SoPlaceholderStub must be %s (in order)' % ' / '.join(seq)); break
    if re.search(r'\b(push|pop|esp|ebp|edx|ebx|esi|edi)\b', stub):
        problems.append('TruMenu.cpp: SoPlaceholderStub may touch eax / ecx reads / flags only (no stack, no other register)')
    if 'g_soH3New[0] = 0xe8;' not in fn_body(src, 'void SoCheck(') or \
            'reinterpret_cast<DWORD>(&SoPlaceholderStub) - (kSoH3 + 5)' not in fn_body(src, 'void SoCheck('):
        problems.append('TruMenu.cpp: SoCheck must build the call rel32 to SoPlaceholderStub from kSoH3 + 5')
    ap = fn_body(src, 'void SoApply(')
    if 'const bool wantC = g_soFull != 0, wantH = wantC && g_soHide != 0, wantM = wantC && g_soMarkers != 0;' not in ap:
        problems.append('TruMenu.cpp: SoApply: the filter / markers only with FullMap')
    if 'return SoBytesAre(at, from, len) && WriteBytes(at, to, len) && SoBytesAre(at, to, len);' not in \
            fn_body(src, 'bool SoWrite('):
        problems.append('TruMenu.cpp: SoWrite must test the old bytes, write, read back')
    sec = src[src.find('// ---- 0.22.48 Sonar komplett'):src.find('// ---- end of 0.22.48 Sonar komplett ----')]
    if not sec: problems.append('TruMenu.cpp: section "0.22.48 Sonar komplett" missing')
    sec_code = re.sub(r'//[^\n]*', '', sec)
    writers = [m.group(1) for m in re.finditer(r'\n(?:[A-Za-z_][A-Za-z0-9_<>*& ]* )?(\w+)\([^;{]*\) \{', sec_code)
               if 'WriteBytes(' in fn_body(sec_code, m.group(0).strip('\n').split('(')[0] + '(')]
    if writers != ['SoWrite']: problems.append('TruMenu.cpp: only SoWrite may call WriteBytes in the section (got %s)' % writers)
    for bad in SO_NOT_02248:
        if bad in sec_code: problems.append('TruMenu.cpp: section 0.22.48 names %s (options A / B - not built)' % bad)
    cap = fn_body(src, 'void SoCapTick(')
    if 'ReadDword(kSoTriRefused, &refused)' not in cap or any(w in cap for w in ('WriteBytes(', 'WriteDword(', 'PutByte(')):
        problems.append('TruMenu.cpp: SoCapTick must only read [0xee03ec]')
    if 'kSoMode = 0x00ee03c8, kSoTriDrawn = 0x00ee03e8, kSoTriRefused = 0x00ee03ec' not in src:
        problems.append('TruMenu.cpp: kSoMode / kSoTriDrawn / kSoTriRefused addresses missing')
    tick = fn_body(src, 'void SoTick(')
    for want in ('if (!g_soOk) return;', 'if (now - g_soReadTick >= 1000) { g_soReadTick = now; SoReadSwitch(); }',
                 'SoApply("run time");', 'if (g_soOnC) SoCapTick(now);'):
        if want not in tick: problems.append('TruMenu.cpp: SoTick must hold %s' % want)
    rs = fn_body(src, 'void SoReadSwitch(')
    for key, _ in SO_KEYS_02248:
        if 'GetPrivateProfileIntA("Sonar", "%s"' % key not in rs: problems.append('TruMenu.cpp: SoReadSwitch lacks %s' % key)
    if 'IniKeepInt("Sonar", key, on ? 1 : 0);' not in fn_body(src, 'void SoSetKey('):
        problems.append('TruMenu.cpp: SoSetKey must keep the [Sonar] key (IniKeepInt)')
    for item, typ, gt in SO_ITEMS_02248:
        if not re.search(r'\{"%s", "%s", "0\.22\.48[^}]*?,\s+%s,\s+[A-Za-z0-9_<>]+,\s+[A-Za-z0-9_<>]+\},' %
                         (re.escape(item), typ, gt), src, re.S):
            problems.append('TruMenu.cpp: item %s (%s, game thread %s) missing in kItems' % (item, typ, gt))
        hm = re.search(r'\{"%s", "", "((?:[^"\\]|\\.)*)"\}' % re.escape(item), src)
        if not hm: problems.append('TruMenu.cpp: kQbHelp row %s missing' % item)
        else:
            de, en = unescape(hm.group(1)).split('|')
            if len(de) > 60 or len(en) > 60: problems.append('TruMenu.cpp: help of %s over 60 characters' % item)
    header, opt_rows = table(src)
    keys = {(s, k): d for s, k, d, _ in opt_rows}
    for key, default in SO_KEYS_02248:
        if keys.get(('Sonar', key)) != default: problems.append('TruMenu.cpp: kOpts [Sonar] %s=%s missing' % (key, default))
    for key, default in SO_KEYS_02248:
        f = sw_rows.get('TruMenu:Sonar:%s' % key)
        if not f or f[3] != 'bool' or f[6] != 'live' or f[7] != default or (len(f) < 10 or f[9] != 'TruMenu 0.22.48'):
            problems.append('switches: row TruMenu | Sonar | %s | bool | ... | live | %s | ... | TruMenu 0.22.48 missing'
                            % (key, default))
    if 'group | tmsonar | ' not in open(switches_path, encoding='utf-8').read():
        problems.append('switches: group tmsonar missing')
    se, grp = set(), None
    for r in qb_rows(src):
        if r[0] != 'kQbSettings': continue
        if r[4] == 'kQbGroup': grp = r[3]; continue
        if grp == 'set_sonar': se.add((r[2], r[3], r[4]))
    for it in SO_SET_02248:
        if it not in se: problems.append('TruMenu.cpp: page Spiel-Einstellungen group set_sonar lacks %s (%s)' % (it[0], it[2]))
    # ---- (5) Regression-DLC2 step 24 / dlc2.txt step 6
    reg = open(os.path.join(ROOT, 'docs', 'Regression-DLC2.md'), encoding='utf-8').read()
    m = re.search(r'\n24\. (.*?)\n25\. ', reg, re.S)
    if not m or '(TruMenu `level.load`' in m.group(1) or 'TruMenu `level.start l1_seatop 0`' not in m.group(1):
        problems.append('docs/Regression-DLC2.md: step 24 must use level.start <unit> 0 (level.load is refused in the main menu)')
    lst = open(os.path.join(ROOT, 'tests', 'regress', 'dlc2.txt'), encoding='utf-8').read()
    s6 = [l for l in lst.splitlines() if l.startswith('step6\t')]
    if not s6 or 'level.load' in s6[0] or 'level.start' not in s6[0]:
        problems.append('tests/regress/dlc2.txt: step6 must use level.start <unit> 0')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8').read()
    if '\n## 0.22.48 - ' not in readme or '\n### TO TEST 0.22.48' not in readme:
        problems.append('README.md: section "## 0.22.48 - ..." with "### TO TEST 0.22.48" missing')
    for key, _ in SO_KEYS_02248:
        if '| `[Sonar] %s` |' % key not in readme: problems.append('README.md: options row `[Sonar] %s` missing' % key)
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if SO_HASH_02247 not in ps: problems.append('Set-TruMenu.ps1: the 0.22.47 build hash (work/asi/menu0270) is missing')
    return problems, ('adrenaline at Lara (fig_adren: %d rows, %d TruShadowCombat [Adrenaline] switches + [Conditions], '
                      'Tests copies only, 0.6.15 rows live); Sonar komplett (%d byte checks = precheck_02248, 5 sites, '
                      'stub, %d keys / %d items / set_sonar %d rows); chapter strings; Regression-DLC2 step 24' %
                      (len(in_adren), len(adren_sw), len(rows), len(SO_KEYS_02248), len(SO_ITEMS_02248), len(se)))


SO_CHECKS_02249 = os.path.join(ROOT, 'work', 'menu49_1411', 'precheck_02249.txt')
SO_HASH_02248 = '673b7bc62a2654a1e7f4e88856a298f0a7a9a78314b1911af4d38768bf138ef0'   # work/asi/menu0271
# item, type, game thread (queued)
SO_ITEMS_02249 = (('sonar.allfloors', 'bool', 'true'), ('sonar.unitmap', 'info', 'false'),
                  ('adren.stayfull', 'bool', 'false'))
SO_SET_02249 = (('sonar.allfloors', '', 'kQbBool'), ('sonar.unitmap', '', 'kQbInfo'),
                ('sw.set', 'TruMenu:Sonar:TriangleCap', 'kQbSwitch'))
# page Figur group fig_adren: the labels of the owner (14.11.): (item, arg) -> DE label
SO_LABELS_02249 = {('adren.keep', ''): 'Nach Einsatz auffuellen', ('adren.stayfull', ''): 'Adrenalin bleibt voll',
                   ('sw.set', 'TruShadowCombat:Adrenaline:ModeWithoutTarget'): 'Modus ohne Ziel',
                   ('sw.set', 'TruShadowCombat:Adrenaline:StrikeWithoutButton'): 'Absprung-Schlag ohne X',
                   ('sw.set', 'TruShadowCombat:Adrenaline:AssistPointer'): 'Zielhilfe Kreis'}


def check_02249(switches_path):
    """0.22.49 (owner wishes 2026-11-14; workspace docs/Befund-TruMenu-02249-1411.md): (1) [Sonar] AllFloors = the je at
    0x6e429b (the floor test of the frame 0x6e4130) -> nop nop, only with FullMap, through SoPart / SoWrite like the other
    sites; kSoChecks = the 16 rows of precheck_02249.txt; no load / unit-list write anywhere in the section (no call of
    0x6e4e80 / 0x551470 / 0x6e2e60, no write of the floor / list globals); (2) the map info (SoReadUnit / SoLogUnits /
    SoMapTick) reads only, only while the sonar mode is 1 .. 4 and only a unit of the live list; (3) adren.keep labelled
    "Nach Einsatz auffuellen" everywhere, adren.stayfull = the two TruShadowCombat drain keys (no memory write), the 0.6.15
    switches without "(Test)", AssistPointer "Zielhilfe Kreis", Paket A copies; (4) the snd.sonar log line has a %s for the
    wave list; README 0.22.49 + TO TEST; Set-TruMenu knows the 0.22.48 hash"""
    problems = []
    src = read_cpp()
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '0.22.49 (sonar all floors + map info' not in ver:   # 0.22.50: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.49 part "0.22.49 (sonar all floors + map info"')
    # ---- (1) AllFloors
    offline = []
    if os.path.exists(SO_CHECKS_02249):
        for line in open(SO_CHECKS_02249, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if line:
                addr, hexs = line.split(None, 1)
                offline.append(('%08x' % int(addr, 16), hexs.replace(' ', '').lower()))
    else:
        problems.append('work/menu49_1411/precheck_02249.txt (the offline byte list) is missing')
    rows = [(a.lower(), b.lower()) for a, b in sv_rows(src, 'kSoChecks')]
    if rows != offline or len(rows) != 16:
        problems.append('TruMenu.cpp: kSoChecks (%d rows) must be the 16 rows of precheck_02249.txt in order' % len(rows))
    for want in ('const DWORD kSoA1 = 0x006e429b;', 'const BYTE kSoA1Game[2] = {0x74, 0x1d}, kSoA1New[2] = {0x90, 0x90};',
                 'const SoSiteDef kSoPartA = {kSoA1, kSoA1Game, kSoA1New, 2, "A1"};'):
        if want not in src: problems.append('TruMenu.cpp: %s missing' % want)
    ap = fn_body(src, 'void SoApply(')
    if 'const bool wantA = wantC && g_soAll != 0;' not in ap:
        problems.append('TruMenu.cpp: SoApply: AllFloors only with FullMap (wantA = wantC && g_soAll != 0)')
    for want in ('SoPart(&kSoPartA, 1, false, "all floors")', 'SoPart(&kSoPartA, 1, true, "all floors")'):
        if want not in ap: problems.append('TruMenu.cpp: SoApply must write A1 through %s' % want)
    if 'SoWrite(kSoPartA.at, kSoPartA.ours, kSoPartA.game, kSoPartA.len)' not in fn_body(src, 'void SoAllBack('):
        problems.append('TruMenu.cpp: SoAllBack must put A1 back')
    if 'GetPrivateProfileIntA("Sonar", "AllFloors"' not in fn_body(src, 'void SoReadSwitch('):
        problems.append('TruMenu.cpp: SoReadSwitch lacks AllFloors')
    # TriangleCap: T1 = the imm32 of 0x6dfa69 (bytes at 0x6dfa6f), only with FullMap, cap - 1, through SoPart
    for want in ('const DWORD kSoT1 = 0x006dfa6f;', 'const BYTE kSoT1Game[4] = {0x83, 0x6d, 0x01, 0x00};',
                 'kSoCapGame = 0x16d84, kSoCapMax = 1000000;'):
        if want not in src: problems.append('TruMenu.cpp: %s missing' % want)
    if 'const LONG wantT = wantC && g_soCap > kSoCapGame ? g_soCap : 0;' not in ap:
        problems.append('TruMenu.cpp: SoApply: TriangleCap only with FullMap and above the game\'s 93572')
    for want in ('const DWORD imm = static_cast<DWORD>(wantT - 1);', 'SoPart(&t, 1, true, "triangle cap")',
                 'SoPart(&t, 1, false, "triangle cap")'):
        if want not in ap: problems.append('TruMenu.cpp: SoApply lacks %s' % want)
    if 'SoWrite(kSoT1, g_soT1New, kSoT1Game, 4)' not in fn_body(src, 'void SoAllBack('):
        problems.append('TruMenu.cpp: SoAllBack must put T1 back')
    if 'GetPrivateProfileIntA("Sonar", "TriangleCap"' not in fn_body(src, 'void SoReadSwitch('):
        problems.append('TruMenu.cpp: SoReadSwitch lacks TriangleCap')
    if 'OptInt(ini, "Sonar", "AllFloors")' not in fn_body(src, 'void SoReadOptions('):
        problems.append('TruMenu.cpp: SoReadOptions lacks AllFloors')
    if 'SoSetKey("AllFloors", &g_soAll, on, "sonar.allfloors");' not in fn_body(src, 'bool RunSoAll('):
        problems.append('TruMenu.cpp: RunSoAll must go through SoSetKey (INI + SoApply)')
    sec = src[src.find('// ---- 0.22.48 Sonar komplett'):src.find('// ---- end of 0.22.48 Sonar komplett ----')]
    # 0.22.53: the section "0.22.53 S7" (the owner's extra loads, check_02253) is the one place that loads - cut out here
    s7a, s7b = sec.find('// ---- 0.22.53 S7:'), sec.find('// ---- end of 0.22.53 S7')
    if 0 <= s7a < s7b: sec = sec[:s7a] + sec[s7b:]
    sec_code = re.sub(r'//[^\n]*', '', sec)
    for bad in ('0x6e4e80', '0x006e4e80', '0x551470', '0x00551470', '0x6e2e60', '0x006e2e60', 'WriteDword(', 'PutByte(',
                'WriteByte('):
        if bad in sec_code: problems.append('TruMenu.cpp: the sonar section must not name %s (no load, no write)' % bad)
    # ---- (2) map info: read only, sonar open, live list
    for fn in ('bool SoReadUnit(', 'void SoLogUnits(', 'void SoMapTick('):
        body = re.sub(r'//[^\n]*', '', fn_body(src, fn))
        if not body: problems.append('TruMenu.cpp: %s missing' % fn); continue
        if any(w in body for w in ('WriteBytes(', 'WriteDword(', 'SoWrite(', 'memcpy(reinterpret_cast')):
            problems.append('TruMenu.cpp: %s must only read' % fn)
    mt = fn_body(src, 'void SoMapTick(')
    if 'mode == 0 || mode > 4' not in mt or 'listed = ReadDword(list + 4 * k, &u) && u == anchor;' not in mt:
        problems.append('TruMenu.cpp: SoMapTick must read only while the sonar is open and only a unit of the live list')
    if 'SoMapTick(now);' not in re.sub(r'//[^\n]*', '', fn_body(src, 'void SoTick(')):
        problems.append('TruMenu.cpp: SoTick must call SoMapTick(now)')
    for want in ('kSoUnits = 0x008aff3c', 'kSoUnitCount = 0x008aff34', 'kSoAnchor = 0x00edf254', 'kSoFloor = 0x00edf268',
                 'kSoTuning = 0x00ee03e0'):
        if want not in src: problems.append('TruMenu.cpp: %s missing' % want)
    # items, help, options, switches, bar rows
    for item, typ, gt in SO_ITEMS_02249:
        if not re.search(r'\{"%s", "%s", "0\.22\.49[^}]*?,\s+%s,\s+[A-Za-z0-9_<>]+,\s+[A-Za-z0-9_<>]+\},' %
                         (re.escape(item), typ, gt), src, re.S):
            problems.append('TruMenu.cpp: item %s (%s, game thread %s) missing in kItems' % (item, typ, gt))
        hm = re.search(r'\{"%s", "", "((?:[^"\\]|\\.)*)"\}' % re.escape(item), src)
        if not hm: problems.append('TruMenu.cpp: kQbHelp row %s missing' % item)
        else:
            de, en = unescape(hm.group(1)).split('|')
            if len(de) > 60 or len(en) > 60: problems.append('TruMenu.cpp: help of %s over 60 characters' % item)
    header, opt_rows = table(src)
    keys = {(s, k): d for s, k, d, _ in opt_rows}
    if keys.get(('Sonar', 'AllFloors')) != '0': problems.append('TruMenu.cpp: kOpts [Sonar] AllFloors=0 missing')
    if keys.get(('Sonar', 'TriangleCap')) != '300000':
        problems.append('TruMenu.cpp: kOpts [Sonar] TriangleCap=300000 missing')
    sw_rows = {}
    for line in open(switches_path, encoding='utf-8').read().splitlines():
        f = [x.strip() for x in line.split('|')]
        if line.startswith('#') or len(f) < 9 or f[0] == 'group': continue
        sw_rows['%s:%s:%s' % (f[0], f[1], f[2])] = f
    f = sw_rows.get('TruMenu:Sonar:AllFloors')
    if not f or f[3] != 'bool' or f[6] != 'live' or f[7] != '0' or len(f) < 10 or f[9] != 'TruMenu 0.22.49':
        problems.append('switches: row TruMenu | Sonar | AllFloors | bool | ... | live | 0 | ... | TruMenu 0.22.49 missing')
    f = sw_rows.get('TruMenu:Sonar:TriangleCap')
    if not f or f[3] != 'int:0..1000000:50000' or f[6] != 'live' or f[7] != '300000' or len(f) < 10 or \
            f[9] != 'TruMenu 0.22.49':
        problems.append('switches: row TruMenu | Sonar | TriangleCap | int:0..1000000:50000 | ... | live | 300000 | ... '
                        '| TruMenu 0.22.49 missing')
    for page, grp_key, flag in (('kQbSettings', 'set_sonar', None), ('kQbTests', 'tg_g', None)):
        got, grp = set(), None
        for r in qb_rows(src):
            if r[0] != page: continue
            if r[4] == 'kQbGroup': grp = r[3]; continue
            if grp == grp_key: got.add((r[2], r[3], r[4]))
        for it in SO_SET_02249:
            if it not in got: problems.append('TruMenu.cpp: %s group %s lacks %s (%s)' % (page, grp_key, it[0], it[2]))
    # ---- (3) adrenaline labels / stays full
    lara, grp = {}, None
    for r in qb_rows(src):
        if r[0] != 'kQbLara': continue
        if r[4] == 'kQbGroup': grp = r[3]; continue
        if grp == 'fig_adren': lara[(r[2], r[3])] = unescape(r[1])   # read_cpp: umlaut escapes as ASCII (ue)
    for k, want in SO_LABELS_02249.items():
        if lara.get(k) != want: problems.append('TruMenu.cpp: fig_adren row %s %s must read "%s" (got %r)' % (k + (want, lara.get(k))))
    if any('(Test)' in v for v in lara.values()): problems.append('TruMenu.cpp: fig_adren still has a "(Test)" label')
    if re.search(r'\{"Adrenalin voll halten", ', src): problems.append('TruMenu.cpp: a row still reads "Adrenalin voll halten"')
    tga, grp = set(), None
    for r in qb_rows(src):
        if r[0] != 'kQbTests': continue
        if r[4] == 'kQbGroup': grp = r[3]; continue
        if grp == 'tg_a': tga.add((r[2], r[3]))
    for k in (('adren.stayfull', ''), ('adren.keep', ''), ('sw.set', 'TruShadowCombat:Adrenaline:ModeWithoutTarget'),
              ('sw.set', 'TruShadowCombat:Adrenaline:StrikeWithoutButton')):
        if k not in tga: problems.append('TruMenu.cpp: Paket A lacks the copy of %s %s' % k)
    for key in ('TruShadowCombat:Adrenaline:ModeWithoutTarget', 'TruShadowCombat:Adrenaline:StrikeWithoutButton'):
        f = sw_rows.get(key)
        if not f or '(Test)' in f[4] or '(test)' in f[5]: problems.append('switches: %s still labelled as a test' % key)
    st = re.sub(r'//[^\n]*', '', fn_body(src, 'bool RunAdmStay('))
    writes = re.findall(r'WritePrivateProfileStringA\("([^"]+)", "([^"]+)", [^,]+, (\w+)\)', st)
    if sorted(w for w in writes if w[2] == 'path') != [('Adrenaline', 'DrainModePercent', 'path'),
                                                         ('Adrenaline', 'DrainPercent', 'path')]:
        problems.append('TruMenu.cpp: RunAdmStay must write exactly [Adrenaline] DrainPercent / DrainModePercent of '
                        'TruShadowCombat.ini (got %s)' % writes)
    if any(w in st for w in ('WriteBytes(', 'WriteDword(', 'WriteCode(')):
        problems.append('TruMenu.cpp: RunAdmStay must not patch memory (the INI way)')
    for want in ('IniKeepInt("Adrenaline", "StayFullDrainWas", d);', 'IniKeepInt("Adrenaline", "StayFullDrainModeWas", m);',
                 'if (nd == 0 && nm == 0) nd = nm = 100;', 'kAsMinVersion'):
        if want not in st: problems.append('TruMenu.cpp: RunAdmStay lacks %s' % want)
    if 'kAsDrain = "ini:TruShadowCombat:Adrenaline:DrainPercent"' not in src:
        problems.append('TruMenu.cpp: kAsDrain (the TruShadowCombat.ini target) missing')
    # ---- (4) snd.sonar log line, README, Set-TruMenu
    if '"snd.sonar %d (src=%s, was %d): %s%s; [Sound] SonarMute=%d written"' not in fn_body(src, 'void W7SonarSet('):
        problems.append('TruMenu.cpp: W7SonarSet: the log line needs %s for the wave list before SonarMute=%d')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8').read()
    if '\n## 0.22.49 - ' not in readme or '\n### TO TEST 0.22.49' not in readme:
        problems.append('README.md: section "## 0.22.49 - ..." with "### TO TEST 0.22.49" missing')
    if '| `[Sonar] AllFloors` |' not in readme: problems.append('README.md: options row `[Sonar] AllFloors` missing')
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if SO_HASH_02248 not in ps: problems.append('Set-TruMenu.ps1: the 0.22.48 build hash (work/asi/menu0271) is missing')
    return problems, ('AllFloors (A1 0x6e429b, %d byte checks = precheck_02249), map info read only, adrenaline labels '
                      '(%d checked) + stays full (INI keys only), snd.sonar log line' % (len(rows), len(SO_LABELS_02249)))


W8_CHECKS_02250 = os.path.join(ROOT, 'work', 'menu50_1411', 'precheck_02250.txt')
W8_HASH_02249 = 'fa98427c3e4cac0d22886b05c5012232c6faf098b183a6c3d86663e1cbc8340d'   # work/asi/menu0272
W8_KEYS_02250 = (('SourceHooks', '1'), ('LogLara', '1'), ('LogEnemies', '1'), ('LogWorld', '1'), ('LogObjects', '1'),
                 ('LogUi', '1'), ('LogSpeech', '1'), ('LogMusic', '1'), ('LogOnlyAudible', '0'), ('LogCollapse', '1'),
                 ('LogMaxDist', '0'))   # [Sound]
# item, type, game thread (queued)
W8_ITEMS_02250 = (('snd.logcat', 'action', 'false'), ('snd.logaudible', 'bool', 'false'),
                  ('snd.logcollapse', 'bool', 'false'), ('snd.logdist', 'action', 'false'),
                  ('snd.catmute', 'action', 'true'), ('snd.catsolo', 'action', 'true'), ('snd.solonew', 'action', 'true'),
                  ('snd.fmod', 'action', 'true'), ('snd.hooks', 'info', 'false'))
# the stubs, in order (comments stripped)
W8_PLAY_STUB = ('push dword ptr [esp + 4]', 'call dword ptr [g_w8PlayFn]', 'pushad', 'pushfd', 'push esi', 'push eax',
                'call W8OnPlay', 'popfd', 'popad', 'ret 4')
# E1 replaces the 6 bytes AFTER the create call (mov eax,[esp+0x18]; test eax,eax) - one return address deeper = +0x1c
W8_EMIT_STUB = ('mov eax, dword ptr [esp + 0x1c]', 'pushad', 'pushfd', 'push dword ptr [ebp + 0xc]', 'push eax',
                'call W8OnEmit', 'popfd', 'popad', 'test eax, eax', 'ret')


def check_02250(switches_path):
    """0.22.50 (owner wishes 2026-11-14 live; workspace docs/Befund-TruMenu-02250-1411.md, design docs/Befund-FMOD-Kanaele-
    1411.md): (1) kW8Checks = the 27 rows of precheck_02250.txt, W8Check right after SoCheck, W8ReadOptions right after
    SoReadOptions, W8Tick in SnTick before W6Tick; (2) V1 = the call redirect 0x591351 -> VoicePool::Play 0x58bfc0 only
    through AiPatchOn (rel32 over the game's), E1 = the 6 bytes at 0x5b99fc after the untouched create call (TruTrace keys
    on its return address) only through W8E1Set (the game's bytes in, read back), both back in W8Shutdown
    (DLL_PROCESS_DETACH); the stubs are exactly the source sequences, the callbacks __stdcall with two arguments, no write
    of game memory in the W8 code but these two; (3) FMOD read without a call: W8FmOf as the validator (slot >> 16 & 0xfff, +0x148, +0x14c, 0x1b8,
    +0x70, +0x30, +0x74, real +0x68 / +0x64), W8ForUsed over SystemI +0x150; (4) the monitor: W8Extras in SnBuild before
    the publish, the FMOD count / "Fremdkanal (DSP)" / music slot rows, filled square = audible; (5) the box: on / off box
    from FMOD's bit, the loop mark as primitives, collapsed lines (same wave + source), the filters; (6) the owner walk at
    most once a second and only while shown, the source from hook E1 first; (7) category rules: kW6Cat, whole groups in
    W6CgTick, the channels outside the pool in W8ExtraMutes; (8) one Ambient aus / Musik aus; (9) page Kapitel from the
    main menu through ChapSteps (mission start, DLC starts as the DLC menu, refused in a level), cp.jump; (10) items,
    help, keys, switches, group ton_log; README 0.22.50 + TO TEST; Set-TruMenu knows the 0.22.49 hash"""
    problems = []
    src = read_cpp()
    code = re.sub(r'//[^\n]*', '', src)
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '0.22.50 (sound log readable + FMOD channels + source hooks' not in ver:   # 0.22.51: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.50 part "0.22.50 (sound log readable + FMOD channels + '
                        'source hooks"')
    # ---- (1) checks, order
    offline = []
    if os.path.exists(W8_CHECKS_02250):
        for line in open(W8_CHECKS_02250, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if line:
                addr, hexs = line.split(None, 1)
                offline.append(('%08x' % int(addr, 16), hexs.replace(' ', '').lower()))
    else:
        problems.append('work/menu50_1411/precheck_02250.txt (the offline byte list) is missing')
    rows = [(a.lower(), b.lower()) for a, b in sv_rows(src, 'kW8Checks')]
    if rows != offline or len(rows) != 27:
        problems.append('TruMenu.cpp: kW8Checks (%d rows) must be the 27 rows of precheck_02250.txt in order' % len(rows))
    if 'g_w8Ok = g_w7Ok && DvChecks(kW8Checks,' not in fn_body(src, 'void W8Check('):
        problems.append('TruMenu.cpp: W8Check must set g_w8Ok = g_w7Ok && DvChecks(kW8Checks, ...)')
    if not re.search(r'\n    SoCheck\(\);[^\n]*\n    W8Check\(\);', src):
        problems.append('TruMenu.cpp: the load must call W8Check right after SoCheck')
    if not re.search(r'\n    SoReadOptions\(ini\);[^\n]*\n    W8ReadOptions\(ini\);', src):
        problems.append('TruMenu.cpp: ReadOptions must call W8ReadOptions(ini) right after SoReadOptions(ini)')
    st = re.sub(r'//[^\n]*', '', fn_body(src, 'void SnTick('))
    if not 0 <= st.find('W8Tick();') < st.find('W6Tick();'):
        problems.append('TruMenu.cpp: SnTick must call W8Tick() before W6Tick()')
    # ---- (2) hooks
    for want in ('AiPatch g_w8Patches[1] = {\n    {0x00591351, 0x0058bfc0, true, "V1 voice -> emitter 0x591351", 0, 0, false},\n};',
                 'DWORD g_w8PlayFn = 0x0058bfc0;', 'const DWORD kW8E1 = 0x005b99fc;',
                 'const BYTE kW8E1Game[6] = {0x8b, 0x44, 0x24, 0x18, 0x85, 0xc0};'):
        if want not in src: problems.append('TruMenu.cpp: %s missing' % want)
    if re.search(r'0x005b99f7, 0x005935d0|e8 d4 9b fd ff', code):
        problems.append('TruMenu.cpp: the create call 0x5b99f7 must stay the game\'s (TruTrace keys on its return address)')
    ck = fn_body(src, 'void W8Check(')
    for want in ('g_w8Patches[0].hook = reinterpret_cast<DWORD>(&W8PlayStub) - (g_w8Patches[0].site + 5);',
                 'g_w8Patches[0].game = g_w8Patches[0].target - (g_w8Patches[0].site + 5);',
                 'const DWORD rel = reinterpret_cast<DWORD>(&W8EmitStub) - (kW8E1 + 5);', 'g_w8E1New[0] = 0xe8;',
                 'g_w8E1New[5] = 0x90;'):
        if want not in ck: problems.append('TruMenu.cpp: W8Check lacks %s' % want)
    es = fn_body(src, 'bool W8E1Set(')
    if 'if (!W8E1Bytes(from) || !WriteBytes(kW8E1, to, 6) || !W8E1Bytes(to)) return false;' not in es or \
            'const BYTE *from = on ? kW8E1Game : g_w8E1New, *to = on ? g_w8E1New : kW8E1Game;' not in es:
        problems.append('TruMenu.cpp: W8E1Set must write only over the expected bytes and read back')
    tk = fn_body(src, 'void W8Tick(')
    for want in ('if (!AiPatchOn(p, o, sizeof(o))) { ok = false; break; }', 'for (AiPatch &p : g_w8Patches) AiPatchOff(p);',
                 'if (ok && !W8E1Set(true)) {', 'W8E1Set(false);', 'g_w8HooksOn = true;',
                 'if (g_w8HooksTried || !g_w8HooksWanted) return;'):
        if want not in tk: problems.append('TruMenu.cpp: W8Tick lacks %s' % want)
    sd = fn_body(src, 'void W8Shutdown(')
    if 'for (AiPatch &p : g_w8Patches) AiPatchOff(p);' not in sd or 'W8E1Set(false);' not in sd:
        problems.append('TruMenu.cpp: W8Shutdown must put V1 (AiPatchOff) and E1 (W8E1Set(false)) back')
    dm = src[src.find('reason == DLL_PROCESS_DETACH'):]
    if 'W8Shutdown();' not in dm[:dm.find('return TRUE;')]: problems.append('TruMenu.cpp: DLL_PROCESS_DETACH must call W8Shutdown')
    for name, seq in (('W8PlayStub', W8_PLAY_STUB), ('W8EmitStub', W8_EMIT_STUB)):
        body = re.sub(r'//[^\n]*', '', fn_body(src, '__declspec(naked) void %s(' % name))
        lines = [l.strip() for l in body.split('\n') if l.strip() and l.strip() not in ('__asm {', '}', '{')]
        lines = [l for l in lines if not l.startswith('__declspec')]
        if lines != list(seq): problems.append('TruMenu.cpp: %s must be exactly %s (got %s)' % (name, ' / '.join(seq), lines))
    for cb in ('void __stdcall W8OnPlay(DWORD voice, DWORD node) {', 'void __stdcall W8OnEmit(DWORD handle, DWORD inst) {'):
        if cb not in src: problems.append('TruMenu.cpp: callback %s missing (__stdcall, two arguments)' % cb)
    sec = src[src.find('// ---- 0.22.50 W8 core'):src.find('// ---- who caused it:')]
    sec2 = src[src.find('// ---- 0.22.50 W8: checks'):src.find('// ---- end of 0.22.50 W8 ----')]
    if not sec or not sec2: problems.append('TruMenu.cpp: the sections "0.22.50 W8 core" / "0.22.50 W8" missing')
    both = re.sub(r'//[^\n]*', '', sec + sec2)
    for bad in ('WriteDword(', 'WriteByte(', 'SoWrite(', 'VirtualProtect('):
        if bad in both: problems.append('TruMenu.cpp: the W8 sections must not call %s' % bad)
    if both.count('WriteBytes(') != 1 or 'WriteBytes(' not in es:
        problems.append('TruMenu.cpp: in the W8 sections only W8E1Set may call WriteBytes (once)')
    # ---- (3) FMOD reads
    fm = fn_body(src, 'bool W8FmOf(')
    for want in ('(handle >> 16) & 0xfff', 'ReadDword(sys + 0x148, &count)', 'ReadDword(sys + 0x14c, &arr)',
                 'arr + slot * 0x1b8', 'ReadDword(c + 0x70, &h) || h != handle', 'ReadDword(c + 0x30, &real) || !real',
                 'ReadDword(c + 0x74, flags)', 'ReadDword(real + 0x68, rflags);', 'ReadDword(real + 0x64, mode);'):
        if want not in fm: problems.append('TruMenu.cpp: W8FmOf lacks %s' % want)
    fu = fn_body(src, 'template <typename F> int W8ForUsed(')
    for want in ('ReadDword(sys + 0x150, &p)', 'const DWORD head = sys + 0x150;', 'p && p != head && steps <= count',
                 'ReadDword(p, &next)', 'ReadDword(p + 0x30, &real) && real'):
        if want not in fu: problems.append('TruMenu.cpp: W8ForUsed lacks %s' % want)
    if any(w in code for w in ('kFmChSetMode', 'setLoopCount')):
        problems.append('TruMenu.cpp: no FMOD mode / loop setter is called (the loop mark only reads +0x64)')
    # ---- (4) monitor
    sb = re.sub(r'//[^\n]*', '', fn_body(src, 'int SnBuild('))
    if not 0 <= sb.find('W8Extras(cats, groups);') < sb.find('EnterCriticalSection(&g_snLock);'):
        problems.append('TruMenu.cpp: SnBuild must call W8Extras before it publishes the snapshot')
    for want in ('v.fmOk = W8FmOf(v.channel, &fci, &ffl, &frf, &fmode);', 'v.fmMute = v.fmOk && (ffl & 8) != 0;',
                 'v.loop = v.fmOk && (fmode & 6) != 0;', 'const DWORD hooked = W8VoiceEmitter(v.voice, v.channel);'):
        if want not in sb: problems.append('TruMenu.cpp: SnBuild lacks %s' % want)
    qr = fn_body(src, 'int W7QbRows(')
    # 0.22.51 W9: the square = audible incl. the game's reverb send (x.aud), was FMOD's dry mute bit alone
    for want in ('Kanaele belegt (%d Pool, %d fremd)', '"Fremdkanal (DSP)"', '"Musik-Slot"',   # read_cpp: umlauts -> ae
                 'view(name, state, count, c, muted ? red : grey, muted ? 2 : 1,', 'const bool muted = x.fmOk ? !x.aud :'):
        if want not in qr: problems.append('TruMenu.cpp: W7QbRows lacks %s' % want)
    if 'const bool muted = w.square == 2;' not in fn_body(src, 'void W7MenuRows('):
        problems.append('TruMenu.cpp: W7MenuRows: an outline square (2) = muted')
    # ---- (5) the box
    dl = fn_body(src, 'void DrawSoundLog(')
    # 0.22.51 W9: box and filter by e.aud (audible incl. the reverb path), was !e.fmMute / e.fmMute
    # 0.22.53 W11: + the sub-group and "Filter folgt Stumm" (W8MutedByTree)
    for want in ('W8Box(dl, p, h, e.aud, c);', 'if (e.loop) W8LoopIcon(', 'if (!W8LineShown(e.cat, e.sub, !e.aud, e.fmPause, '
                 'e.dist,', 'const bool collapse = g_w8Collapse != 0;', '" \\303\\227%d"',
                 'if (!v.loop || !v.playing || v.ending) continue;'):
        if want not in dl: problems.append('TruMenu.cpp: DrawSoundLog lacks %s' % want)
    li = fn_body(src, 'void W8LoopIcon(')
    if not li or re.search(r'AddText|\\342\\206|\\xe2', li): problems.append('TruMenu.cpp: W8LoopIcon: primitives only')
    ag = fn_body(src, 'void W8AggAdd(')
    if 'a.wave == h.wave && !strcmp(a.src, h.src) && (h.wave >= 0 || !strcmp(a.name, h.name))' not in ag or \
            'a.count = count + 1;' not in ag:
        problems.append('TruMenu.cpp: W8AggAdd: same wave + same source (a stream: same name) = one line, count up')
    if 'W8AggAdd(h);' not in fn_body(src, 'void W7HistAdd(') or 'W8AggRefresh();' not in fn_body(src, 'void W7HistEnd('):
        problems.append('TruMenu.cpp: W7HistAdd must collapse (W8AggAdd), W7HistEnd refresh (W8AggRefresh)')
    # ---- (6) owner walk / source
    ow = fn_body(src, 'bool W7Owner(')
    # 0.22.53 W11: also while a Lara / Waffen rule needs the source of a group-14 voice (g_w8NeedOwners)
    if '(!g_w7OwnAt || now - g_w7OwnAt > 1000) && (W8Visible() || g_w8NeedOwners)' not in ow:
        problems.append('TruMenu.cpp: W7Owner: the walk at most once a second and only while shown (W8Visible)')
    vs = fn_body(src, 'void W7VoiceSource(')
    if not 0 <= vs.find('W8EmitterInst(emitter, &er)') < vs.find('W7Owner(emitter, &ow)'):
        problems.append('TruMenu.cpp: W7VoiceSource must ask hook E1 before the owner list')
    if 'ForInstances(' in fn_body(src, 'void W6WaveLine('): problems.append('TruMenu.cpp: W6WaveLine must not walk the instances')
    # ---- (7) category rules
    if ('kW6Cat };' not in src and 'kW6Cat,' not in src) or ('"category"};' not in src and '"category", "sub-group"};' not in src):
        problems.append('TruMenu.cpp: rule kind kW6Cat missing')   # 0.22.53: kW6Sub follows
    if 'wn += W8CatPureGroups(static_cast<int>(g_w6Rules[i].value), want + wn, kW6CgMax - wn);' not in fn_body(src, 'void W6CgTick('):
        problems.append('TruMenu.cpp: W6CgTick must mute the whole sub-trees of a category rule')
    vt = fn_body(src, 'void W6VoiceTick(')
    if 'if (catRule || g_w6SoloOn) W8ExtraMutes(poolCh, poolN, tgroups, catRule);' not in vt:
        problems.append('TruMenu.cpp: W6VoiceTick must reach the channels outside the pool (W8ExtraMutes)')
    em = fn_body(src, 'void W8ExtraMutes(')
    if not 0 <= em.find('if (fl & 2) return;') < em.find('W6ChMute(h, true)') or 'g_w6Chan[g_w6ChanN++] = {0, h, true};' not in em:
        problems.append('TruMenu.cpp: W8ExtraMutes: never over a foreign mute bit, keep what TruMenu muted')
    # ---- (8) one Ambient aus / Musik aus
    if not re.search(r'\{"media\.muteambient", "bool", "0\.20[^}]*?, true, ValW6Amb, RunW6Amb\},', src, re.S):
        problems.append('TruMenu.cpp: item media.muteambient must be the one Ambient aus (ValW6Amb / RunW6Amb, game thread)')
    if not re.search(r'\{"snd\.ambmute", "bool", "0\.22\.45[^}]*?, true, ValW6Amb, RunW6Amb\},', src, re.S):
        problems.append('TruMenu.cpp: item snd.ambmute must stay the same switch')
    settings = [(r[2], r[3]) for r in qb_rows(src) if r[0] == 'kQbSettings']
    for item, n_want in (('media.muteambient', 1), ('media.mutemusic', 1), ('snd.ambmute', 0), ('music.mute', 0)):
        if settings.count((item, '')) != n_want:
            problems.append('TruMenu.cpp: page Spiel-Einstellungen has %d %s rows (want %d)' % (settings.count((item, '')),
                                                                                              item, n_want))
    if 'IniKeep("Media", "MuteAmbient", on ? "1" : "0");' not in fn_body(src, 'bool RunW6Mute('):
        problems.append('TruMenu.cpp: snd.mute ambience must keep [Media] MuteAmbient')
    if 'if (g_w6Ok && g_sndMuteAmb && g_w6RuleN < kW6RuleMax) {' not in fn_body(src, 'void W6Check('):
        problems.append('TruMenu.cpp: W6Check must turn [Media] MuteAmbient=1 into the ambience rule')
    # ---- (9) page Kapitel from the main menu
    cs = fn_body(src, 'bool ChapSteps(')
    for want in ('*menu = stateOk && state == 10;', 'Out(steps, n, "save.backup kapitel;level.start %s", dlc);',
                 'Out(steps, n, "save.backup kapitel;level.start %s 0", unit);', 'if (dlcStart && InLevel()) {',
                 'Out(steps, n, "save.backup kapitel;level.load %s", unit);'):
        if want not in cs: problems.append('TruMenu.cpp: ChapSteps lacks %s' % want)
    if '"dlc_level1_start") ? "dlc1" : !_stricmp(unit, "dlc_level2_start") ? "dlc2"' not in fn_body(src, 'bool ChapDlcStart('):
        problems.append('TruMenu.cpp: ChapDlcStart must map the two DLC start units to dlc1 / dlc2')
    if '!_stricmp(r.id, "level.load") && !ChapSteps(r.arg, steps, sizeof(steps), &menu, o, sizeof(o))' not in \
            fn_body(src, 'void QbActRow('):
        problems.append('TruMenu.cpp: QbActRow: a level.load backup row goes through ChapSteps')
    if 'ChapSteps(r.arg, steps, sizeof(steps), &menu, o,' not in fn_body(src, 'void PageQbRow('):
        problems.append('TruMenu.cpp: the long menu backup rows go through ChapSteps')
    cj = fn_body(src, 'bool RunCpJump(')
    if 'if (menu) Out(go, sizeof(go), "level.start %s 0", unit);' not in cj:
        problems.append('TruMenu.cpp: cp.jump from the main menu must use the mission start')
    # ---- (10) items, help, keys, switches, bar
    for item, typ, gt in W8_ITEMS_02250:
        if not re.search(r'\{"%s", "%s", "0\.22\.50[^}]*?,\s+%s,\s+[A-Za-z0-9_<>]+,\s+[A-Za-z0-9_<>]+\},' %
                         (re.escape(item), typ, gt), src, re.S):
            problems.append('TruMenu.cpp: item %s (%s, game thread %s) missing in kItems' % (item, typ, gt))
        if item == 'snd.logdist': continue   # its bar row is the switch row LogMaxDist (the hint of TruMenu.switches.txt)
        hm = re.search(r'\{"%s", "\*?", "((?:[^"\\]|\\.)*)"\}' % re.escape(item), src)
        if not hm: problems.append('TruMenu.cpp: kQbHelp row %s missing' % item)
        else:
            de, en = unescape(hm.group(1)).split('|')
            if len(de) > 60 or len(en) > 60: problems.append('TruMenu.cpp: help of %s over 60 characters' % item)
    header, opt_rows = table(src)
    keys = {(s, k): d for s, k, d, _ in opt_rows}
    for key, default in W8_KEYS_02250:
        if keys.get(('Sound', key)) != default: problems.append('TruMenu.cpp: kOpts [Sound] %s=%s missing' % (key, default))
    sw_rows = {}
    for line in open(switches_path, encoding='utf-8').read().splitlines():
        f = [x.strip() for x in line.split('|')]
        if line.startswith('#') or len(f) < 9 or f[0] == 'group': continue
        sw_rows['%s:%s:%s' % (f[0], f[1], f[2])] = f
    for key, default in W8_KEYS_02250:
        f = sw_rows.get('TruMenu:Sound:%s' % key)
        when = 'restart' if key == 'SourceHooks' else 'live'
        if not f or f[6] != when or f[7] != default or len(f) < 10 or f[9] != 'TruMenu 0.22.50':
            problems.append('switches: row TruMenu | Sound | %s | ... | %s | %s | ... | TruMenu 0.22.50 missing' %
                            (key, when, default))
    if 'group | tmtonlog | ' not in open(switches_path, encoding='utf-8').read():
        problems.append('switches: group tmtonlog missing')
    se, grp = set(), None
    for r in qb_rows(src):
        if r[0] != 'kQbSettings': continue
        if r[4] == 'kQbGroup': grp = r[3]; continue
        # 0.22.53 W11: the group ton_log holds the two trees (ton_log_filter / ton_log_hear and their kinds tlf_* / tls_*)
        if grp == 'ton_log' or grp in ('ton_log_filter', 'ton_log_hear') or (grp or '')[:4] in ('tlf_', 'tls_'):
            se.add((r[2], r[3], r[4]))
    want_rows = [('snd.logcollapse', '', 'kQbBool'), ('snd.logaudible', '', 'kQbBool'),
                 ('sw.set', 'TruMenu:Sound:LogMaxDist', 'kQbSwitch'), ('snd.solonew', '', 'kQbAction'),
                 ('snd.mute', 'all 0', 'kQbAction'), ('snd.fmod', '', 'kQbAction'), ('snd.hooks', '', 'kQbInfo')]
    for c in W8_CATS:                        # 0.22.53: Stumm / Solo per kind = one value row snd.hear <kind>
        want_rows += [('snd.logcat', c, 'kQbBool'), ('snd.hear', c, 'kQbValue')]
    for it in want_rows:
        if it not in se: problems.append('TruMenu.cpp: page Spiel-Einstellungen group ton_log lacks %s %s (%s)' % it)
    cats = re.findall(r'"([a-z]+)"', src[src.find('const char *const kW8CatKey[kW8Cats] = {'):].split('};')[0])
    if tuple(cats) != W8_CATS: problems.append('TruMenu.cpp: kW8CatKey must be %s' % ' / '.join(W8_CATS))
    if not re.search(r'const signed char kW8GroupSub\[80\] = \{', src):   # 0.22.53: was kW8GroupCat (the kind)
        problems.append('TruMenu.cpp: kW8GroupSub[80] missing')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8').read()
    if '\n## 0.22.50 - ' not in readme or '\n### TO TEST 0.22.50' not in readme:
        problems.append('README.md: section "## 0.22.50 - ..." with "### TO TEST 0.22.50" missing')
    for key, _ in W8_KEYS_02250:
        if '`[Sound] %s`' % key not in readme: problems.append('README.md: options row `[Sound] %s` missing' % key)
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if W8_HASH_02249 not in ps: problems.append('Set-TruMenu.ps1: the 0.22.49 build hash (work/asi/menu0272) is missing')
    return problems, ('sound log readable (%d byte checks = precheck_02250; hooks V1 / E1 through AiPatch, stubs exact; '
                      'FMOD read without a call; monitor + box; owner walk throttled; category rules; one Ambient aus / '
                      'Musik aus; Kapitel from the main menu; %d items, %d keys, ton_log %d rows)' %
                      (len(rows), len(W8_ITEMS_02250), len(W8_KEYS_02250), len(se)))


# TruMenu 0.22.51 (S5 sonar view + base PDA, X default, cmd suggestions, DLC start from a level)
S5_CHECKS_02251 = os.path.join(ROOT, 'work', 'menu51_1411', 'precheck_02251.txt')
S5_KEYS_02251 = (('Sonar', 'FadeFar', '0'), ('Sonar', 'TintOthers', '0'), ('PDA', 'ShadowPdaAsBasePda', '0'),
                 ('Sound', 'ReverbFollowsMute', '1'), ('Sound', 'ReverbOff', '0'))   # the last two: W9 (reverb)
# item, type, game thread (queued)
# 0.22.52: sonar.tint became an action (the 0 / 1 / 2 value row "Sonar: Bereichsfarben")
S5_ITEMS_02251 = (('sonar.fade', 'action', 'true'), ('sonar.tint', 'action', 'true'), ('sonar.area', 'action', 'true'),
                  ('sonar.why', 'action', 'true'), ('sonar.view', 'info', 'false'), ('pda.basepda', 'bool', 'true'),
                  ('pda.state', 'info', 'false'), ('snd.reverbmute', 'bool', 'true'), ('snd.reverboff', 'bool', 'true'),
                  ('snd.reverb', 'info', 'false'))
W9_CHECKS_02251 = os.path.join(ROOT, 'work', 'menu51_1411', 'precheck_02251_reverb.txt')
W9_SEND_STUB = ('pushad', 'pushfd', 'push esi', 'call W9VoiceMuted', 'test eax, eax', 'je w9_keep',
                'mov dword ptr [esp + 0x2c], 0', 'w9_keep:', 'popfd', 'popad', 'jmp dword ptr [g_w9SetMixFn]')
S5_FOG_STUB = ('mov eax, dword ptr [g_s5FogFar]', 'test eax, eax', 'je s5f_go', 'mov dword ptr [esp + 0x14], eax',
               'mov eax, dword ptr [g_s5FogNear]', 'mov dword ptr [esp + 0x10], eax', 'lock inc dword ptr [g_s5FogCalls]',
               's5f_go:', 'jmp dword ptr [g_s5FogFn]')
S5_UNIT_STUB = ('mov eax, dword ptr [esp + 4]', 'mov ecx, dword ptr [g_s5ShowUnit]', 'test ecx, ecx', 'je s5u_draw',
                'cmp eax, ecx', 'je s5u_draw', 'lock inc dword ptr [g_s5AreaSkips]', 'ret', 's5u_draw:',
                # 0.22.52: the colour comes from S5ColourFor (one tint / per area; 0 = the game's), the unit pushed again
                'cmp dword ptr [g_s5Tint], 0', 'je s5u_plain', 'push eax', 'call S5ColourFor', 'test eax, eax',
                'je s5u_plain', 'mov ecx, dword ptr [g_s5ColourAt]', 'push dword ptr [ecx]',
                'mov dword ptr [ecx], eax', 'push dword ptr [esp + 0xc]', 'push dword ptr [esp + 0xc]',
                'call dword ptr [g_s5DrawFn]', 'add esp, 8', 'mov ecx, dword ptr [g_s5ColourAt]', 'pop edx',
                'mov dword ptr [ecx], edx', 'lock inc dword ptr [g_s5Tinted]', 'ret', 's5u_plain:',
                'jmp dword ptr [g_s5DrawFn]')
S5_HASH_02250 = 'b1262935dc898fd7f55201d943c9ddd6dd2a686093292f0084797e6c93154ced'


def check_02251(switches_path):
    """0.22.51 (owner wishes 2026-11-14 evening; workspace docs/Befund-TruMenu-02251-1411.md): (1) kS5Checks = the 22 rows of
    work/menu51_1411/precheck_02251.txt in order, S5Check right after W8Check, S5ReadOptions after W8ReadOptions, S5Tick
    after SoTick in PadHook, S5Shutdown after W8Shutdown; (2) the three call redirects D1 0x6e42ac / F1 0x6e4d94 / F2
    0x6e4bf9 only through SoWrite (the game's call bytes in, read back), the stubs exactly the source sequences, the
    section writes no game code otherwise and its only WriteBytes are the PDA word (S5PdaTick, S5Shutdown); (3) fade =
    fog n/2 .. n m, -1 = 90 / 100 km, 0 = the game's call; tint 40 % amber, alpha kept; (4) PDA: script 3347 by the hash
    map, f1 found by its words, written only through S5PdaSafe, back only over our own word; (5) items, help, kOpts keys,
    INI, switch rows, bar rows (set_sonar + Paket G), value rows kQvSoFade / kQvSoArea; (6) X = default (kQbDefDir, the
    switch file's default, footer); (7) command line suggestions; (8) the DLC rows in a level = the pause menu's DLC start
    (LevelStartInGame); (9) README 0.22.51 + TO TEST, Set-TruMenu knows the 0.22.50 hash"""
    problems = []
    src = read_cpp()
    code = re.sub(r'//[^\n]*', '', src)
    ver = src[:src.find('\n', src.find('kVersion = '))]
    # 0.22.52: the 0.22.51 part follows the 0.22.52 text in kVersion
    if '0.22.51 (sonar view + base PDA + X default + DLC start from a level' not in ver:
        problems.append('TruMenu.cpp: kVersion must start with "TruMenu 0.22.51 (sonar view + base PDA + X default + DLC '
                        'start from a level"')
    # ---- (1) checks, order
    offline = []
    if os.path.exists(S5_CHECKS_02251):
        for line in open(S5_CHECKS_02251, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if line:
                addr, hexs = line.split(None, 1)
                offline.append(('%08x' % int(addr, 16), hexs.replace(' ', '').lower()))
    else:
        problems.append('work/menu51_1411/precheck_02251.txt (the offline byte list) is missing')
    rows = [(a.lower(), b.lower()) for a, b in sv_rows(src, 'kS5Checks')]
    if rows != offline or len(rows) != 22:
        problems.append('TruMenu.cpp: kS5Checks (%d rows) must be the 22 rows of precheck_02251.txt in order' % len(rows))
    if 'g_s5Ok = DvChecks(kS5Checks,' not in fn_body(src, 'void S5Check('):
        problems.append('TruMenu.cpp: S5Check must set g_s5Ok = DvChecks(kS5Checks, ...)')
    for pat, what in ((r'\n    W8Check\(\);[^\n]*\n    S5Check\(\);', 'the load must call S5Check right after W8Check'),
                      (r'\n    W8ReadOptions\(ini\);[^\n]*\n    S5ReadOptions\(ini\);',
                       'ReadOptions must call S5ReadOptions(ini) right after W8ReadOptions(ini)'),
                      (r'\n    SoTick\(\);[^\n]*\n    S5Tick\(\);', 'PadHook must call S5Tick() right after SoTick()'),
                      (r'\n        W8Shutdown\(\);[^\n]*\n        S5Shutdown\(\);',
                       'DLL_PROCESS_DETACH must call S5Shutdown right after W8Shutdown')):
        if not re.search(pat, src): problems.append('TruMenu.cpp: %s' % what)
    # ---- (2) redirects, stubs, writes
    for want in ('const DWORD kS5D1 = 0x006e42ac, kS5F1 = 0x006e4d94, kS5F2 = 0x006e4bf9;',
                 'const BYTE kS5D1Game[5] = {0xe8, 0x4f, 0xf7, 0xff, 0xff};',
                 'const BYTE kS5F1Game[5] = {0xe8, 0xa7, 0xb0, 0xed, 0xff};',
                 'const BYTE kS5F2Game[5] = {0xe8, 0x42, 0xb2, 0xed, 0xff};',
                 'DWORD g_s5DrawFn = 0x006e3a00, g_s5FogFn = 0x005bfe40, g_s5AnchorAt = 0x00edf254, g_s5ColourAt = 0x00ee03bc;'):
        if want not in src: problems.append('TruMenu.cpp: %s missing' % want)
    ck = fn_body(src, 'void S5Check(')
    for want in ('S5CallBytes(g_s5D1New, kS5D1, &S5UnitStub);', 'S5CallBytes(g_s5F1New, kS5F1, &S5FogStub);',
                 'S5CallBytes(g_s5F2New, kS5F2, &S5FogStub);'):
        if want not in ck: problems.append('TruMenu.cpp: S5Check lacks %s' % want)
    ap = fn_body(src, 'void S5Apply(')
    for want in ('SoWrite(kS5D1, wantD ? kS5D1Game : g_s5D1New, wantD ? g_s5D1New : kS5D1Game, 5)',
                 'SoWrite(kS5F1, wantF ? kS5F1Game : g_s5F1New, wantF ? g_s5F1New : kS5F1Game, 5)',
                 'SoWrite(kS5F2, wantF ? kS5F2Game : g_s5F2New, wantF ? g_s5F2New : kS5F2Game, 5)',
                 'const bool wantD = g_s5ShowUnit != 0 || g_s5Tint != 0, wantF = g_s5Fade != 0;'):
        if want not in ap: problems.append('TruMenu.cpp: S5Apply lacks %s' % want)
    for name, seq in (('S5FogStub', S5_FOG_STUB), ('S5UnitStub', S5_UNIT_STUB)):
        body = re.sub(r'//[^\n]*', '', fn_body(src, '__declspec(naked) void %s(' % name))
        lines = [l.strip() for l in body.split('\n') if l.strip() and l.strip() not in ('__asm {', '}', '{')]
        lines = [l for l in lines if not l.startswith('__declspec')]
        if lines != list(seq): problems.append('TruMenu.cpp: %s must be exactly %s (got %s)' % (name, ' / '.join(seq), lines))
    sec = src[src.find('// ---- 0.22.51 S5: sonar view + base PDA'):src.find('// ---- end of 0.22.51 S5 ----')]
    if not sec: problems.append('TruMenu.cpp: the section "0.22.51 S5" is missing')
    sc = re.sub(r'//[^\n]*', '', sec)
    for bad in ('WriteDword(', 'WriteByte(', 'VirtualProtect('):
        if bad in sc: problems.append('TruMenu.cpp: the S5 section must not call %s' % bad)
    pt, sd = fn_body(src, 'void S5PdaTick('), fn_body(src, 'void S5Shutdown(')
    if sc.count('WriteBytes(') != 2 or 'WriteBytes(g_s5PdaAt, &to, 4)' not in pt or \
            'WriteBytes(g_s5PdaOursAt, &game, 4)' not in sd:
        problems.append('TruMenu.cpp: in the S5 section only the PDA word is written with WriteBytes (S5PdaTick, S5Shutdown)')
    # ---- (3) fade / tint values
    fv = fn_body(src, 'void S5FogValues(')
    # 0.22.52: every FadeFar != 0 puts the fog out (the fade is the shader's, check_02252)
    for want in ('if (f != 0) { nearV = 9.0e6f; farV = 1.0e7f; }',):
        if want not in fv: problems.append('TruMenu.cpp: S5FogValues lacks %s' % want)
    # 0.22.52: the amber tint = palette entry 0, blended 40 % by S5Blend (alpha kept)
    if '{{255, 170, 40},' not in src or 'mixed = (ch * 6 + tint[k] * 4) / 10' not in fn_body(src, 'DWORD S5Blend(') or \
            'S5Blend(c, kS5Pal[0])' not in fn_body(src, 'void S5TintValue('):
        problems.append('TruMenu.cpp: S5TintValue: 40 % towards amber (255, 170, 40), alpha kept')
    if 'LONG S5FadeClamp(LONG v) { return v < -1 ? -1 : v > 2000 ? 2000 : v; }' not in src:
        problems.append('TruMenu.cpp: S5FadeClamp must keep FadeFar in -1 .. 2000')
    lv = fn_body(src, 'void S5LogView(')
    for want in ('ReadFloats(0x00ee04e0, c, 4);', 'ReadFloats(0x00ee0440, ax, 4);', 'ReadFloats(mesh + 0x20, o, 3)',
                 'if (plane < -40.0f) ++behind;'):
        if want not in lv: problems.append('TruMenu.cpp: S5LogView lacks %s' % want)
    if 'S5LogView("open");' not in re.sub(r'//[^\n]*', '', fn_body(src, 'void SoMapTick(')):
        problems.append('TruMenu.cpp: SoMapTick must log S5LogView("open") with the open line')
    # ---- (4) base PDA
    for want in ('const DWORD kS5ScrBuckets = 0x008a6ed0, kS5ScrTable = 0x008a6ed8, kS5ScrObjVt = 0x0084e4d4, '
                 'kS5PdaScript = 3347;', 'const DWORD kS5PdaGame = 0x04000001, kS5PdaOurs = 0x04000000;',
                 '{0x4c, 0x32636c64}', 'const DWORD kS5F1Word = 0x20;'):
        if want not in src: problems.append('TruMenu.cpp: %s missing' % want)
    if not 0 <= pt.find('if (!S5PdaSafe(why, sizeof(why)))') < pt.find('WriteBytes(g_s5PdaAt, &to, 4)'):
        problems.append('TruMenu.cpp: S5PdaTick must pass S5PdaSafe before it writes')
    if 'if (word != from || (!want && g_s5PdaOursAt != g_s5PdaAt))' not in pt:
        problems.append('TruMenu.cpp: S5PdaTick must write only over the expected word and put back only its own')
    sf = fn_body(src, 'bool S5PdaSafe(')
    for want in ('InLevel()', '(flags & 0x1000)', 'ReadDword(kSoMode, &mode) && mode', 'g_menuOpen'):
        if want not in sf: problems.append('TruMenu.cpp: S5PdaSafe lacks %s' % want)
    if 'if (!_stricmp(id, "pda.basepda")) return S5PdaWhy();' not in fn_body(src, 'const char *RadialWhy('):
        problems.append('TruMenu.cpp: RadialWhy must grey pda.basepda while no DLC g_pda is loaded (S5PdaWhy)')
    # ---- (5) items, help, keys, switches, bar
    for item, typ, gt in S5_ITEMS_02251:
        if not re.search(r'\{"%s", "%s", "0\.22\.51[^}]*?,\s+%s,\s+[A-Za-z0-9_<>]+,\s+[A-Za-z0-9_<>]+\},' %
                         (re.escape(item), typ, gt), src, re.S):
            problems.append('TruMenu.cpp: item %s (%s, game thread %s) missing in kItems' % (item, typ, gt))
        hm = re.search(r'\{"%s", "\*?", "((?:[^"\\]|\\.)*)"\}' % re.escape(item), src)
        if not hm: problems.append('TruMenu.cpp: kQbHelp row %s missing' % item)
        else:
            de, en = unescape(hm.group(1)).split('|')
            if len(de) > 60 or len(en) > 60: problems.append('TruMenu.cpp: help of %s over 60 characters' % item)
    header, opt_rows = table(src)
    keys = {(s, k): d for s, k, d, _ in opt_rows}
    sw_rows = {}
    for line in open(switches_path, encoding='utf-8').read().splitlines():
        f = [x.strip() for x in line.split('|')]
        if line.startswith('#') or len(f) < 9 or f[0] == 'group': continue
        sw_rows['%s:%s:%s' % (f[0], f[1], f[2])] = f
    for sec_, key, default in S5_KEYS_02251:
        if keys.get((sec_, key)) != default: problems.append('TruMenu.cpp: kOpts [%s] %s=%s missing' % (sec_, key, default))
        f = sw_rows.get('TruMenu:%s:%s' % (sec_, key))
        # 0.22.52: FadeFar / TintOthers rows were renewed for 0.22.52
        if not f or f[6] != 'live' or f[7] != default or len(f) < 10 or f[9] not in ('TruMenu 0.22.51', 'TruMenu 0.22.52'):
            problems.append('switches: row TruMenu | %s | %s | ... | live | %s | ... | TruMenu 0.22.51 missing' %
                            (sec_, key, default))
    if sw_rows.get('TruMenu:Sonar:FadeFar', [''] * 4)[3] != 'int:-1..2000:50':
        problems.append('switches: FadeFar must be int:-1..2000:50')
    for tbl, grp_want, flag in (('kQbSettings', 'set_sonar', None), ('kQbTests', 'tg_g', 'kQfTg')):
        have, grp = set(), None
        for r in qb_rows(src, True):
            if r[0] != tbl: continue
            if r[4] == 'kQbGroup': grp = r[3]; continue
            if grp == grp_want: have.add((r[2], r[4]))
        for it in (('sonar.fade', 'kQbValue'), ('sonar.area', 'kQbValue'), ('sonar.tint', 'kQbValue'),   # 0.22.52 tint
                   ('sonar.why', 'kQbAction'), ('sonar.view', 'kQbInfo'), ('pda.basepda', 'kQbBool'), ('pda.state', 'kQbInfo')):
            if it not in have: problems.append('TruMenu.cpp: %s group %s lacks %s (%s)' % (tbl, grp_want, it[0], it[1]))
    for want in ('"sonar.fade", "", kQbValue, -1, kQcNone, kQvSoFade,', '"sonar.area", "", kQbValue, -1, kQcNone, kQvSoArea,'):
        if src.count(want) != 2: problems.append('TruMenu.cpp: two bar rows (settings + Paket G) with %s' % want)
    if 'const LONG kS5FadeSteps[8] = {-1, 0, 800, 400, 200, 100, 50, 20};' not in src or \
            'const int kS5FadeStepN = 8, kS5FadeStepDefault = 1;' not in src:
        problems.append('TruMenu.cpp: the fade row steps (aus, Spiel, 800 .. 20 m; default Spiel) missing')
    for fn_head, want in (('int QbValueCount(', 'val == kQvSoFade ? kS5FadeStepN : val == kQvSoArea ? S5AreaCount() : 0'),
                          ('void QbValueArg(', 'case kQvSoArea: S5AreaArg(i, o, n); break;'),
                          ('int QbValueNow(', 'case kQvSoArea: v = S5AreaNow(); break;'),
                          ('bool ItemValueShort(', 'else if (!_stricmp(id, "sonar.area")) S5AreaShort(de, o, n);')):
        if want not in fn_body(src, fn_head): problems.append('TruMenu.cpp: %s lacks %s' % (fn_head.strip('('), want))
    # ---- (6) X = default
    if 'const int kQbDefDir = 3;' not in src: problems.append('TruMenu.cpp: kQbDefDir = 3 missing')
    if 'case kQbValue: QbActRow(page, r, kQbDefDir); return;' not in fn_body(src, 'void QbExecRow('):
        problems.append('TruMenu.cpp: QbExecRow: X on a value row = QbActRow(page, r, kQbDefDir)')
    qa = fn_body(src, 'void QbActRow(')
    if 'else if (r.kind == kQbValue && dir == kQbDefDir) {' not in qa or 'if (!QbValueDefault(r.val, arg, sizeof(arg))) {' not in qa:
        problems.append('TruMenu.cpp: QbActRow: a value row with kQbDefDir takes QbValueDefault')
    dv = fn_body(src, 'bool QbValueDefault(')
    for want in ('case kQvTime:', 'case kQvSoFade: i = kS5FadeStepDefault; break;', 'case kQvSoArea: i = 0; break;',
                 'default: return false;', 'case kQvAtStyle: i = atoi(OptDefault("Menu", "AttractIcon")); break;'):
        if want not in dv: problems.append('TruMenu.cpp: QbValueDefault lacks %s' % want)
    sw = fn_body(src, 'void QbSwAct(')
    if 'if (dir == kQbXDir && r.type != kSwBool) {' not in sw or 'Out(arg, sizeof(arg), "%s %s", r.target + 4, r.def);' not in sw:
        problems.append('TruMenu.cpp: QbSwAct: X on an int / choice switch = the file\'s default column')
    dq = fn_body(src, 'void DrawQuick(')
    if 'const bool xDef = QbSelIsValue(g_qbPage, sel);' not in dq or '"X: Standard  Y: Favorit"' not in dq:
        problems.append('TruMenu.cpp: DrawQuick: the footer says "X: Standard" on a value row (QbSelIsValue)')
    # ---- (7) command line
    av = fn_body(src, 'template <typename F> void CmdArgValues(')
    if 'if (!UnitUnused(i) && !UnitNameNoArchive(kUnits[i].unit) && !UnitNoDrm(i))' not in av:
        problems.append('TruMenu.cpp: CmdArgValues: level.start must list the usable units')
    if 'const bool menuStart = !_stricmp(word, "level.load") && !InLevel();' not in fn_body(src, 'void CmdBuildSuggestions('):
        problems.append('TruMenu.cpp: CmdBuildSuggestions: level.load in the main menu suggests level.start')
    # ---- (8) DLC start from a level
    cs = fn_body(src, 'bool ChapSteps(')
    if not re.search(r'if \(dlcStart && InLevel\(\)\) \{[^}]*?LevelStartInGameOk\(\)', cs, re.S) or \
            cs.count('Out(steps, n, "save.backup kapitel;level.start %s", dlc);') != 2:
        problems.append('TruMenu.cpp: ChapSteps: the DLC rows in a level = "level.start dlc1|dlc2" (LevelStartInGameOk)')
    rls = fn_body(src, 'bool RunLevelStart(')   # 0.22.58: the in-level start may arm the intro marks after the call
    if 'if (state == 1 && InLevel()) return LevelStartInGame(name, given, o, n);' not in rls and \
            not ('if (state == 1 && InLevel()) {' in rls and 'const bool ok = LevelStartInGame(name, given, o, n);' in rls):
        problems.append('TruMenu.cpp: RunLevelStart must hand a level (main state 1) to LevelStartInGame')
    lg = fn_body(src, 'bool LevelStartInGame(')
    # 0.22.56 (P3 fix 2): any unit in a level - the DLC-only refusal became the dlcStart flag + the camera-hint checks
    for want in ('reinterpret_cast<MissionStartFn>(kUgdF27)(args, select, 0, 1);', 'reinterpret_cast<VoidFn>(kScrF7)();',
                 'reinterpret_cast<VoidFn>(kScrF19)();', '&& !g_menuPaused && !g_radPaused;',
                 'const bool dlcStart = !_stricmp(name, "dlc_level1_start") || !_stricmp(name, "dlc_level2_start");',
                 'if (!dlcStart && !ChOk())', 'if (CinematicNow())'):
        if want not in lg: problems.append('TruMenu.cpp: LevelStartInGame lacks %s' % want)
    if 'kUgdF22' in lg: problems.append('TruMenu.cpp: LevelStartInGame must not call uigamedata f22 (case 8 does not)')
    if not 0 <= lg.find('(kUgdF27)') < lg.find('(kScrF7)') < lg.find('(kScrF19)'):
        problems.append('TruMenu.cpp: LevelStartInGame: f27, then f7, then f19 (the case-8 order)')
    # ---- (i) W9: the game's reverb send (workspace docs/Befund-Ton-ausserhalb-FMOD-1411.md)
    offline9 = []
    if os.path.exists(W9_CHECKS_02251):
        for line in open(W9_CHECKS_02251, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if line:
                addr, hexs = line.split(None, 1)
                offline9.append(('%08x' % int(addr, 16), hexs.replace(' ', '').lower()))
    else:
        problems.append('work/menu51_1411/precheck_02251_reverb.txt (the offline byte list) is missing')
    rows9 = [(a.lower(), b.lower()) for a, b in sv_rows(src, 'kW9Checks')]
    if rows9 != offline9 or len(rows9) != 11:
        problems.append('TruMenu.cpp: kW9Checks (%d rows) must be the 11 rows of precheck_02251_reverb.txt in order' % len(rows9))
    for pat, what in ((r'\n    S5Check\(\);[^\n]*\n    W9Check\(\);', 'the load must call W9Check right after S5Check'),
                      (r'\n    S5ReadOptions\(ini\);[^\n]*\n    W9ReadOptions\(ini\);', 'W9ReadOptions right after S5ReadOptions'),
                      (r'\n    S5Tick\(\);[^\n]*\n    W9Tick\(\);', 'PadHook must call W9Tick() right after S5Tick()'),
                      (r'\n        S5Shutdown\(\);[^\n]*\n        W9Shutdown\(\);', 'W9Shutdown right after S5Shutdown')):
        if not re.search(pat, src): problems.append('TruMenu.cpp: %s' % what)
    for want in ('const DWORD kW9R1 = 0x00591591, kW9R2 = 0x005841bf, kW9Holder = 0x00ccde98;',
                 'const BYTE kW9R1Game[5] = {0xe8, 0x5d, 0x8a, 0x22, 0x00};',
                 'const BYTE kW9R2Game[5] = {0xe8, 0x2f, 0x5e, 0x23, 0x00};', 'DWORD g_w9SetMixFn = 0x007b9ff3;'):
        if want not in src: problems.append('TruMenu.cpp: %s missing' % want)
    body = re.sub(r'//[^\n]*', '', fn_body(src, '__declspec(naked) void W9SendStub('))
    lines = [l.strip() for l in body.split('\n') if l.strip() and l.strip() not in ('__asm {', '}', '{')]
    lines = [l for l in lines if not l.startswith('__declspec')]
    if lines != list(W9_SEND_STUB):
        problems.append('TruMenu.cpp: W9SendStub must be exactly %s (got %s)' % (' / '.join(W9_SEND_STUB), lines))
    if 'int __stdcall W9VoiceMuted(DWORD voice) {' not in src or \
            '!W8FmOf(handle, &ci, &fl, &rf, &mode) || !(fl & 8)) return 0;' not in fn_body(src, 'int __stdcall W9VoiceMuted('):
        problems.append('TruMenu.cpp: W9VoiceMuted (__stdcall, one argument) must zero only FMOD-muted voices (bit 3)')
    wa = fn_body(src, 'void W9Apply(')
    for want in ('SoWrite(kW9R1, want ? kW9R1Game : g_w9R1New, want ? g_w9R1New : kW9R1Game, 5)',
                 'SoWrite(kW9R2, want ? kW9R2Game : g_w9R2New, want ? g_w9R2New : kW9R2Game, 5)',
                 'const bool want = g_w9Follow != 0;'):
        if want not in wa: problems.append('TruMenu.cpp: W9Apply lacks %s' % want)
    sec9 = src[src.find('// ---- 0.22.51 W9: the game'):src.find('// ---- end of 0.22.51 W9 ----')]
    if not sec9: problems.append('TruMenu.cpp: the section "0.22.51 W9" is missing')
    for bad in ('WriteDword(', 'WriteByte(', 'WriteBytes(', 'VirtualProtect('):
        if bad in re.sub(r'//[^\n]*', '', sec9): problems.append('TruMenu.cpp: the W9 section must not call %s' % bad)
    au = fn_body(src, 'bool W9Audible(')
    for want in ('if (paused) return false;', 'return dryOn || (send > 0.0f && W9RevOutNow() > 0.0f);'):
        if want not in au: problems.append('TruMenu.cpp: W9Audible lacks %s' % want)
    rt = fn_body(src, 'void W9RevTick(')
    for want in ('if (g_w9RevOff && !g_w9RevConn && level > 0.0f) {', 'g_w9RevOld = level;',
                 'if (level == 0.0f && W9SetMix(conn, g_w9RevOld))'):
        if want not in rt: problems.append('TruMenu.cpp: W9RevTick lacks %s' % want)
    if 'W9Levels(v.voice, fci, &v.dry, &v.send);' not in fn_body(src, 'int SnBuild(') or \
            'W9Levels(a.voice, ci, &a.dry, &a.send);' not in fn_body(src, 'void W8AggRefresh('):
        problems.append('TruMenu.cpp: the snapshot and the collapsed lines must read the send (W9Levels)')
    if 'W9RevRow(de, sends, mutedSends, smax, name, sizeof(name), state, sizeof(state));' not in fn_body(src, 'int W7QbRows('):
        problems.append('TruMenu.cpp: the monitor needs the reverb row (W9RevRow)')
    dl9 = fn_body(src, 'void DrawSoundLog(')
    for want in ('W8Box(dl, p, h, e.aud, c);', 'W8Box(dl, p, h, v.aud, c);', 'W9SendText(e.fmMute, e.send, de, rev, sizeof(rev));'):
        if want not in dl9: problems.append('TruMenu.cpp: DrawSoundLog lacks %s (0.22.51: audible incl. the reverb)' % want)
    for tbl, grp_want in (('kQbSettings', None), ('kQbTests', 'tg_b2')):
        have, grp = set(), None
        for r in qb_rows(src):
            if r[0] != tbl: continue
            if r[4] == 'kQbGroup': grp = r[3]; continue
            if grp_want is None or grp == grp_want: have.add((r[2], r[4]))
        for it in (('snd.reverbmute', 'kQbBool'), ('snd.reverboff', 'kQbBool'), ('snd.reverb', 'kQbInfo')):
            if it not in have: problems.append('TruMenu.cpp: %s %s lacks %s (%s)' % (tbl, grp_want or '', it[0], it[1]))
    # ---- (9) README, Set-TruMenu
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8').read()
    if '\n## 0.22.51 - ' not in readme or '\n### TO TEST 0.22.51' not in readme:
        problems.append('README.md: section "## 0.22.51 - ..." with "### TO TEST 0.22.51" missing')
    for sec_, key, _ in S5_KEYS_02251:
        if '`[%s] %s`' % (sec_, key) not in readme: problems.append('README.md: options row `[%s] %s` missing' % (sec_, key))
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if S5_HASH_02250 not in ps: problems.append('Set-TruMenu.ps1: the 0.22.50 build hash (work/asi/menu0273) is missing')
    return problems, ('sonar view + base PDA (%d byte checks = precheck_02251; D1 / F1 / F2 through SoWrite, stubs exact; '
                      'PDA word only through S5PdaSafe; X default; cmd suggestions; DLC start from a level; %d items, %d keys)'
                      % (len(rows), len(S5_ITEMS_02251), len(S5_KEYS_02251)))


SV_HEADER = os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'TruSaveProbe.h')
SV_ITEMS = ('save.pending', 'save.inv', 'save.waiting', 'save.find')


def sv_rows(src, name):
    """the {0xADDR, "hex"} rows of a DvCheck table in TruSaveProbe.h (hex joined over string pieces, no spaces)"""
    m = re.search(r'const DvCheck %s\[\] = \{(.*?)\n\};' % re.escape(name), src, re.S)
    if not m: return []
    return [(a, ''.join(LIT.findall(b)).replace(' ', '')) for a, b in
            re.findall(r'\{0x([0-9a-f]{8}), ((?:"[0-9a-f ]+"\s*)+)\}', m.group(1))]


S6_CHECKS_02252 = os.path.join(ROOT, 'work', 'menu52_1411', 'precheck_02252.txt')


def check_02252(switches_path):
    """0.22.52 (owner wishes 2026-11-14 late evening; workspace docs/Befund-TruMenu-02252-1411.md): (1) kVersion starts with
    0.22.52; (2) kS6Checks = the first 6 rows of work/menu52_1411/precheck_02252.txt in order, S6Check right after W9Check,
    S6Apply inside S5Apply before the early return, S6Shutdown in S5Shutdown, S6 writes only the three shader values over
    the game's (S6Apply / S6Back) and only with WriteBytes; (3) W10: W10Tick right after W9Tick, the reverb mark in both
    box loops and the monitor (QbView.rev), W10Sweep zeroes through W9SetMix only for an FMOD-muted voice, snd.dspgraph
    info item + rows; (4) sonar.tint 0 / 1 / 2 (S5TintClamp, kQvSoTint value row, S5ColourFor in the stub, palette 8);
    (5) (j) the Raetsel row: no drive for an open range on a free hinge, the range cut to the limits, JtTick takes our
    lock back after a node change; (6) README 0.22.52 + TO TEST"""
    problems = []
    src = read_cpp()
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '0.22.52 (reverb mark + DSP graph + sonar shader fade + area colours + joint row fix' not in ver:   # 0.22.53: a part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.52 part "0.22.52 (reverb mark + DSP graph ..."')
    # ---- (2) S6
    offline = []
    if os.path.exists(S6_CHECKS_02252):
        for line in open(S6_CHECKS_02252, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if line:
                addr, hexs = line.split(None, 1)
                offline.append(('%08x' % int(addr, 16), hexs.replace(' ', '').lower()))
    else:
        problems.append('work/menu52_1411/precheck_02252.txt (the offline byte list) is missing')
    rows = [(a.lower(), b.lower()) for a, b in sv_rows(src, 'kS6Checks')]
    if len(rows) != 6 or rows != offline[:6]:
        problems.append('TruMenu.cpp: kS6Checks (%d rows) must be the first 6 rows of precheck_02252.txt in order' % len(rows))
    if not re.search(r'\n    W9Check\(\);[^\n]*\n    S6Check\(\);', src):
        problems.append('TruMenu.cpp: the load must call S6Check right after W9Check')
    ap = fn_body(src, 'void S5Apply(')
    if not 0 <= ap.find('S6Apply(why);') < ap.find('if (wantD == g_s5OnD && wantF == g_s5OnF) return;'):
        problems.append('TruMenu.cpp: S5Apply must call S6Apply(why) before its early return')
    if 'S6Shutdown();' not in fn_body(src, 'void S5Shutdown('):
        problems.append('TruMenu.cpp: S5Shutdown must call S6Shutdown')
    sec = src[src.find('// ---- 0.22.52 S6:'):src.find('// ---- end of 0.22.52 S6 ----')]
    if not sec: problems.append('TruMenu.cpp: the section "0.22.52 S6" is missing')
    sc = re.sub(r'//[^\n]*', '', sec)
    for bad in ('WriteDword(', 'WriteByte(', 'VirtualProtect(', 'SoWrite('):
        if bad in sc: problems.append('TruMenu.cpp: the S6 section must not call %s' % bad)
    if sc.count('WriteBytes(') != 2: problems.append('TruMenu.cpp: S6 writes with exactly two WriteBytes (S6Apply, S6Back)')
    for want in ('const DWORD kS6Off[3] = {0x8c, 0x9c, 0xa0};', 'const DWORD kS6Tuning = 0x00ee03e0, kS6MatVt = 0x00849018;'):
        if want not in src: problems.append('TruMenu.cpp: %s missing' % want)
    sp = fn_body(src, 'bool S6Params(')
    if 'cnt != 11' not in sp or 'vt != kS6MatVt' not in sp:
        problems.append('TruMenu.cpp: S6Params must check the vtable 0x849018 and 11 PS MaterialParams')
    sa = fn_body(src, 'void S6Apply(')
    for want in ('if (cur != m.game[k] && cur != m.ours[k])', 'v[2] = 1.0f;', 'ReadDword(tun + 0x34, &mats[0]);',
                 'ReadDword(tun + 0x40, &mats[1]);'):
        if want not in sa: problems.append('TruMenu.cpp: S6Apply lacks %s' % want)
    if 'cur == m.ours[k] && cur != m.game[k]' not in fn_body(src, 'void S6Back('):
        problems.append('TruMenu.cpp: S6Back must put back only over our own value')
    # ---- (3) W10
    if not re.search(r'\n    W9Tick\(\);[^\n]*\n    W10Tick\(\);', src):
        problems.append('TruMenu.cpp: PadHook must call W10Tick() right after W9Tick()')
    dl = fn_body(src, 'void DrawSoundLog(')
    if dl.count('W10RevIcon(dl, ImVec2(p.x + h * 3.3f, p.y), h, ') != 2:
        problems.append('TruMenu.cpp: DrawSoundLog must draw the reverb mark in both line loops')
    if 'W10RevIcon(dl, ImVec2(stateX, y), fs, v.rev - 1,' not in src or 'int rev;' not in src:
        problems.append('TruMenu.cpp: the bar must draw QbView.rev in front of the state')
    sw = fn_body(src, 'void W10Sweep(')
    if '!(fl & 8)' not in sw or 'W9SetMix(conn, 0.0f)' not in sw or 'if (!g_w9On' not in sw:
        problems.append('TruMenu.cpp: W10Sweep must zero only FMOD-muted voices (bit 3) through W9SetMix while R1 / R2 are ours')
    if not re.search(r'\{"snd\.dspgraph", "info", "0\.22\.52[^}]*?false, ValW10State, nullptr\}', src, re.S):
        problems.append('TruMenu.cpp: item snd.dspgraph (info) missing')
    if src.count('"snd.dspgraph", "", kQbInfo') != 2:
        problems.append('TruMenu.cpp: two bar rows snd.dspgraph (Spiel-Einstellungen / Ton + Paket B2)')
    for tag in ('tgB2.revmark', 'tgB2.dspgraph'):
        if '"%s", kQbCheck' % tag not in src: problems.append('TruMenu.cpp: TO TEST row %s missing' % tag)
    # ---- (4) area colours
    for want in ('LONG S5TintClamp(LONG v) { return v <= 0 ? 0 : v >= 2 ? 2 : 1; }', 'const int kS5PalN = 8;',
                 'kQvSoTint', 'DWORD __stdcall S5ColourFor(DWORD unit) {'):   # 0.22.53: kQvHear follows kQvSoTint
        if want not in src: problems.append('TruMenu.cpp: %s missing' % want)
    if src.count('"sonar.tint", "", kQbValue, -1, kQcNone, kQvSoTint,') != 2:
        problems.append('TruMenu.cpp: two value rows "Sonar: Bereichsfarben" (settings + Paket G)')
    sw_rows = {}
    for line in open(switches_path, encoding='utf-8').read().splitlines():
        f = [x.strip() for x in line.split('|')]
        if line.startswith('#') or len(f) < 9 or f[0] == 'group': continue
        sw_rows['%s:%s:%s' % (f[0], f[1], f[2])] = f
    if sw_rows.get('TruMenu:Sonar:TintOthers', [''] * 4)[3] != 'int:0..2':
        problems.append('switches: TintOthers must be int:0..2')
    # ---- (5) (j) joint rows
    pz = fn_body(src, 'void PzRefresh(')
    # 0.22.56: the joint rows are a list only (no "solve" arg, so no "usable" any more)
    for want in ('const bool motion = type == 1 && limOk && !limOn && (loOpen || hiOpen);', 'if (a < lr0) a = lr0;',
                 'if (z > lr1) z = lr1;'):
        if want not in pz: problems.append('TruMenu.cpp: PzRefresh lacks %s' % want)
    if 'right 2x = solve' in pz or 'Out(r->arg' in pz:
        problems.append('TruMenu.cpp: PzRefresh must not offer a joint "solve" row any more (0.22.56)')
    jt = fn_body(src, 'void JtTick(')
    if 'JtStop(line, ours);' not in jt or 'lim[0] == t && lim[1] == t' not in jt:
        problems.append('TruMenu.cpp: JtTick must take our lock back after a node change when it still stands')
    # ---- (6) README
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8-sig').read()
    if '## 0.22.52' not in readme or 'TO TEST 0.22.52' not in readme:
        problems.append('README.md: section "## 0.22.52" with "TO TEST 0.22.52" missing')
    return problems, 'reverb mark + DSP graph (W10), shader fade S6 (%d byte checks), area colours, joint rows (j)' % len(rows)


S7_CHECKS_02253 = os.path.join(ROOT, 'work', 'menu53_1411', 'precheck_02253.txt')
S7_DESIGN_02253 = os.path.join(ROOT, 'work', 'menu53_1411', 'sonar', 'precheck_sonarload.txt')
W11_KEYS_02253 = (('Sound', 'LogWeapons', '1'), ('Sound', 'LogHideSubs', ''), ('Sound', 'LogFollowMute', '1'),
                  ('Sonar', 'LoadNeighbourFloors', '0'), ('Sonar', 'LoadAllConnected', '0'), ('Sonar', 'LoadMaxUnits', '24'))
W11_ITEMS_02253 = (('snd.logsub', 'action'), ('snd.logfollow', 'bool'), ('snd.hear', 'action'), ('sonar.loadnb', 'bool'),
                   ('sonar.loadall', 'bool'), ('sonar.loadstate', 'info'))


def pre_rows(path):
    out = []
    for line in open(path, encoding='utf-8'):
        line = line.split('#')[0].strip()
        if line:
            addr, hexs = line.split(None, 1)
            out.append(('%08x' % int(addr, 16), hexs.replace(' ', '').lower()))
    return out


def check_02253(switches_path):
    """0.22.53 (owner wishes 2026-11-14 night, docs/Status-2026-11-14.md W-53 / LT-2310; workspace
    docs/Befund-TruMenu-02253-1411.md): (1) kVersion starts with 0.22.53; (2) W11 kinds / sub-groups: 8 kinds with
    weapons, 38 sub-groups, kW8GroupSub[80] (77 / 78 Lara's, the weapon groups Waffen's), kW8WeaponWaves = the 174 waves
    of work/menu53_1411/weapon_waves.inc, W8SubOf by source for group 14, the box filter by sub-group + "Filter folgt
    Stumm"; (3) the owner's layout of Ton-Log (settings, Filter (Zeigen), the heading Schnell-Hoeren, Stumm / Solo with its
    four first rows, every kind + sub-group in both trees), nesting levels 2 / 3; (4) S7: kS7Checks = precheck_02253.txt
    (a subset of the 51 design rows), R1 only while closed through SoWrite, the gates in S7Extend, S7Check / S7Shutdown;
    (5) the markup layer with 0xe804a0 while the sonar is open; (6) keys, items, switches, README"""
    problems = []
    src = read_cpp()
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '0.22.53 (sound log trees + kind Waffen + sonar extra loads + markups in the sonar view' not in ver:   # 0.22.54: a part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.53 part "0.22.53 (sound log trees ..."')
    # ---- (2) kinds / sub-groups
    if 'kW8CatKey[kW8Cats] = {"lara", "enemies", "world", "objects", "ui", "speech", "music", "weapons"};' not in src:
        problems.append('TruMenu.cpp: kW8CatKey must end with weapons')
    subs = w11_subs(src)
    # 0.22.54: + mu_menu (group 1, the main menu music) = 39
    if len(subs) != 39 or len(set(subs)) != 39: problems.append('TruMenu.cpp: kW8Sub must hold 39 unique keys (%d)' % len(subs))
    m = re.search(r'const signed char kW8GroupSub\[80\] = \{(.*?)\};', src, re.S)
    gs = re.findall(r'kW8s[A-Za-z0-9]+', re.sub(r'//[^\n]*', '', m.group(1))) if m else []
    if len(gs) != 80: problems.append('TruMenu.cpp: kW8GroupSub must have 80 entries (%d)' % len(gs))
    else:
        for g, want in ((77, 'kW8sLaraVoice'), (78, 'kW8sLaraBody'), (68, 'kW8sLaraVoice'), (69, 'kW8sLaraVoice'),
                        (58, 'kW8sWpDraw'), (59, 'kW8sWpDraw'), (61, 'kW8sWpBrass'), (62, 'kW8sWpShot'),
                        (63, 'kW8sWpReload'), (51, 'kW8sWpImpact'), (52, 'kW8sWpImpact'), (14, 'kW8sWoDefault')):
            if gs[g] != want: problems.append('TruMenu.cpp: kW8GroupSub[%d] must be %s (%s)' % (g, want, gs[g]))
    # the weapon-only wave ids are game data: never a table in the source, only the optional TruMenu.weaponwaves.txt
    if re.search(r'const WORD kW8WeaponWaves\[\]', src):
        problems.append('TruMenu.cpp: no wave id table in the source (game data) - TruMenu.weaponwaves.txt only')
    wl = fn_body(src, 'void W8WeaponWavesLoad(')
    if '"%s\\\\TruMenu.weaponwaves.txt"' not in wl or 'qsort(g_w8WeaponWaves,' not in wl:
        problems.append('TruMenu.cpp: W8WeaponWavesLoad must read TruMenu.weaponwaves.txt and sort it (bsearch)')
    if 'W8WeaponWavesLoad(dir);' not in re.sub(r'//[^\n]*', '', src):
        problems.append('TruMenu.cpp: TruMenu.weaponwaves.txt is never loaded')
    if 'g_w8WeaponN <= 0) return false;' not in fn_body(src, 'bool W8WeaponWave('):
        problems.append('TruMenu.cpp: W8WeaponWave must answer false without the file')
    so = fn_body(src, 'int W8SubOf(')
    for want in ('if (group != 14 || cat == kSnMusic || cat == kSnSpeech) return sub;', 'W8EmitterInst(emitter, &er)',
                 'W7Owner(emitter, &ow)', 'return own == 2 || W8WeaponWave(wave) ? kW8sWpLara14 : kW8sLaraGear;'):
        if want not in so: problems.append('TruMenu.cpp: W8SubOf lacks %s' % want)
    lo = fn_body(src, 'int W8LaraOwner(')
    if 'ReadDword(inst + 0x54, &parent) && parent == player' not in lo or '"wp_", 3' not in lo:
        problems.append('TruMenu.cpp: W8LaraOwner must test parent +0x54 = player and the wp_ object name')
    ls = fn_body(src, 'bool W8LineShown(')
    for want in ('(g_w8DrawHide & (1ull << sub))', 'if (g_w8FollowMute && tree) return false;'):
        if want not in ls: problems.append('TruMenu.cpp: W8LineShown lacks %s' % want)
    if 'W8PublishMute();' not in fn_body(src, 'void W6Tick('): problems.append('TruMenu.cpp: W6Tick must publish the mute state')
    vt = fn_body(src, 'void W6VoiceTick(')
    if 'if (rec && final) rec->sub = v.sub;' not in vt: problems.append('TruMenu.cpp: W6VoiceTick keeps only a final sub-group')
    if 'wn += W8CatPureGroups(static_cast<int>(g_w6Rules[i].value), want + wn, kW6CgMax - wn, true);' not in \
            fn_body(src, 'void W6CgTick('):
        problems.append('TruMenu.cpp: W6CgTick must mute the pure sub-trees of a sub-group rule')
    # ---- (3) layout
    rows = [r for r in qb_rows(src) if r[0] == 'kQbSettings']
    keys = [(r[2], r[3], r[4]) for r in rows]
    def at(item, arg, kind, start=0):        # the first such row from start on (snd.list is also in Ton-Monitor)
        return keys.index((item, arg, kind), start) if (item, arg, kind) in keys[start:] else -1
    tl = at('-', 'ton_log', 'kQbGroup')
    tf = at('-', 'ton_log_filter', 'kQbGroup')
    th = at('-', 'ton_log_hear', 'kQbGroup')
    # 0.22.54 (owner 2026-11-15): the plain heading Schnell-Hoeren is gone (check_02254 refuses it)
    order = [tl, at('snd.list', '', 'kQbBool', tl), at('snd.logcollapse', '', 'kQbBool', tl),
             at('snd.logaudible', '', 'kQbBool', tl), at('sw.set', 'TruMenu:Sound:LogMaxDist', 'kQbSwitch', tl), tf,
             at('snd.logfollow', '', 'kQbBool', tl), th]
    if any(x < 0 for x in order) or order != sorted(order):
        problems.append('TruMenu.cpp: Ton-Log must be settings -> Filter (Zeigen) -> Stumm / Solo (%s)' % order)
    elif keys[th + 1:th + 5] != [('snd.mute', 'all 0', 'kQbAction'), ('snd.solonew', '', 'kQbAction'),
                                 ('snd.reverbmute', '', 'kQbBool'), ('snd.reverboff', '', 'kQbBool')]:
        problems.append('TruMenu.cpp: Stumm / Solo must start with Alles zurueck, Neuester Ton solo, Hall folgt Stumm, Hall aus')
    for c in W8_CATS:
        if at('snd.logcat', c, 'kQbBool') < tf or at('snd.hear', c, 'kQbValue') < th:
            problems.append('TruMenu.cpp: kind %s needs a Filter row and a Stumm / Solo row' % c)
    for s in subs:
        if not tf < at('snd.logsub', s, 'kQbBool') < th or at('snd.hear', s, 'kQbValue') < th:
            problems.append('TruMenu.cpp: sub-group %s needs a Filter row and a Stumm / Solo row' % s)
    for g in ('lara', 'wp', 'en', 'wo', 'ob', 'ui', 'sp', 'mu'):
        for t in ('tlf_', 'tls_'):
            if '"%s%s", kQbGroup, -1, kQcNone, 0, kQbSound, kQfLv3}' % (t, g) not in src:
                problems.append('TruMenu.cpp: kind group %s%s (level 3) missing' % (t, g))
            if '"%s%s"' % (t, g) not in src[src.find('const char *const kQbStartClosed[]'):][:3000]:
                problems.append('TruMenu.cpp: kind group %s%s must start closed' % (t, g))
    gl = fn_body(src, 'int QbGroupLevel(')
    if '(r.flags & kQfLv3) ? 3 : (r.flags & kQfLv2) ? 2 : (r.flags & kQfSub) ? 1 : 0' not in gl:
        problems.append('TruMenu.cpp: QbGroupLevel must know the levels 2 / 3')
    # ---- (4) S7
    if os.path.exists(S7_CHECKS_02253) and os.path.exists(S7_DESIGN_02253):
        mine, design = pre_rows(S7_CHECKS_02253), pre_rows(S7_DESIGN_02253)
        rows7 = [(a.lower(), b.lower()) for a, b in sv_rows(src, 'kS7Checks')]
        # 0.22.54: + 6 rows (S7FreshEntry, check_02254 / precheck_02254.txt) after these 17
        if rows7[:17] != mine or len(mine) != 17:
            problems.append('TruMenu.cpp: kS7Checks must start with the 17 rows of precheck_02253.txt')
        if any(r not in design for r in mine): problems.append('precheck_02253.txt: every row must be one of the 51 design rows')
    else:
        problems.append('work/menu53_1411/precheck_02253.txt or sonar/precheck_sonarload.txt missing')
    if not re.search(r'\n    S6Check\(\);[^\n]*\n    S7Check\(\);', src):
        problems.append('TruMenu.cpp: the load must call S7Check right after S6Check')
    if 'S7Shutdown();' not in src[src.find('BOOL WINAPI DllMain('):]: problems.append('TruMenu.cpp: DllMain must call S7Shutdown')
    tk = fn_body(src, 'void S7Tick(')
    if not 0 <= tk.find('if (mode == 0) {') < tk.find('SoWrite(kS7R1, kS7R1Game, g_s7R1New, 5)'):
        problems.append('TruMenu.cpp: S7Tick may write R1 only while the sonar is closed (mode 0), through SoWrite')
    ex = fn_body(src, 'void S7Extend(')
    for want in ('mode != 1) return;', 'pause != 6', 'ReadDword(kS7MapHeap, &heap) || heap', 'if (g_s7Extra >= g_s7Max)',
                 'if (S7Faces() >= g_soCap)', 'if (!scope || !g_soOnC) return;', 'scope == 2 ? 1 : 0, 0, 0)'):
        if want not in ex: problems.append('TruMenu.cpp: S7Extend lacks %s' % want)
    st = fn_body(src, 'void __cdecl S7LoadStub(')
    if not 0 <= st.find('reinterpret_cast<S7RuleFn>(kS7Rule)(u);') < st.find('S7Extend(u);'):
        problems.append('TruMenu.cpp: S7LoadStub must call the game rule 0x6e2e60 first')
    sec7 = src[src.find('// ---- 0.22.53 S7:'):src.find('// ---- end of 0.22.53 S7')]
    for bad in ('WriteDword(', 'WriteByte(', 'VirtualProtect(', '0x551470'):
        if bad in re.sub(r'//[^\n]*', '', sec7): problems.append('TruMenu.cpp: the S7 section must not use %s' % bad)
    # ---- (5) markup
    mk = fn_body(src, 'void W5DrawMarkup(')
    if not 0 <= mk.find('ReadFloats(kLblMatrix, sonarM, 16)') < mk.find('memcpy(v.m, sonarM, sizeof(sonarM));'):
        problems.append('TruMenu.cpp: W5DrawMarkup must take the 0xe804a0 matrix while the sonar is open')
    # ---- (6) keys, items, switches, README
    header, opt_rows = table(src)
    keysd = {(s, k): d for s, k, d, _ in opt_rows}
    for s, k, d in W11_KEYS_02253:
        if keysd.get((s, k)) != d: problems.append('TruMenu.cpp: kOpts [%s] %s=%s missing' % (s, k, d))
    items = item_types(src)
    for it, typ in W11_ITEMS_02253:
        if items.get(it) != typ: problems.append('TruMenu.cpp: item %s (%s) missing' % (it, typ))
    sw = open(switches_path, encoding='utf-8').read()
    for s, k, d in W11_KEYS_02253:
        if k == 'LogHideSubs': continue      # a key list, set by the bar rows
        if not re.search(r'\nTruMenu \| %s \| %s \| [^\n]*\| live \| %s \| [^\n]*\| TruMenu 0\.22\.53' % (s, k, re.escape(d)), sw):
            problems.append('switches: row TruMenu | %s | %s | ... | live | %s | ... | TruMenu 0.22.53 missing' % (s, k, d))
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8-sig').read()
    if '## 0.22.53' not in readme or 'TO TEST 0.22.53' not in readme:
        problems.append('README.md: section "## 0.22.53" with "TO TEST 0.22.53" missing')
    return problems, 'sound log trees (8 kinds, %d sub-groups, 174 weapon waves), S7 sonar loads (%d byte checks), markup ' \
                     'in the sonar view' % (len(subs), len(sv_rows(src, 'kS7Checks')))


S7_CHECKS_02254 = os.path.join(ROOT, 'work', 'menu54_1511', 'precheck_02254.txt')
FMT_FUNCS_02254 = ('void Log(int level, ', 'void Out(char *out, size_t size, ', 'void LabelAdd(char *o, size_t n, size_t *used, ',
                   'bool TextAdd(char *o, size_t n, size_t *used, ', 'void IniPut(IniTextOut &t, ', 'void Text(',
                   'void ShotNote(bool failed, ', 'void LxAppend(', 'void SndNote(int level, ', 'void ClkNote(int level, ',
                   'void QbResult(bool err, ')


def check_02254(switches_path):
    """0.22.54 (owner 2026-11-15 evening; workspace docs/Befund-TruMenu-02254-1511.md): (1) kVersion starts with 0.22.54;
    (2) crash TruMenu+0x13aec6 (strnlen under RunW6Mute's log line): kHow holds one text per rule kind (kW6Kinds,
    static_assert) and the index is checked; every printf-style function of TruMenu carries _Printf_format_string_ (the
    MSVC /analyze check work/fmt_1511/Test-TruMenuFormats.ps1 needs it) and no format is forwarded through 'auto...';
    (3) crash tru+0x14f05d (sonar close, 1.0f as a load handle): S7Extend clears +0x88 / +0xb2 / +0xb4 of a list entry
    the find 0x6e2a60 has just appended (S7FreshEntry) before anything reads it; kS7Checks = precheck_02254.txt (23 rows);
    (4) [Sound] ResetAtStart (default 1): SndResetAtStart runs once, before MuteMusic / MuteAmbient / ReverbOff are read,
    writes the 0 into TruMenu.ini, never touches the log filters / ReverbFollowsMute / SonarMute; item, Stumm / Solo row,
    switches row, start log line; (5) sub-group mu_menu = group 1; (6) no heading row Schnell-Hoeren; README"""
    problems = []
    src = read_cpp()
    code = re.sub(r'//[^\n]*', '', src)
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '0.22.54 (two crash fixes + sound switches reset at start' not in ver:   # 0.22.55: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.54 part "0.22.54 (two crash fixes ..."')
    # ---- (2) kHow + format annotations
    if not re.search(r'kW6Sub,[^\n]*\n\s*kW6Kinds \};', src):
        problems.append('TruMenu.cpp: the rule kinds must end with kW6Sub, kW6Kinds')
    mu = fn_body(src, 'bool RunW6Mute(')
    for want in ('static const char *const kHow[] = {', 'static_assert(sizeof(kHow) / sizeof(kHow[0]) == kW6Kinds,',
                 'how >= 0 && how < kW6Kinds ? kHow[how] : "?"'):
        if want not in mu: problems.append('TruMenu.cpp: RunW6Mute lacks %s' % want)
    if 'kHow[r.kind]' in mu: problems.append('TruMenu.cpp: RunW6Mute indexes kHow unchecked')
    for fn in FMT_FUNCS_02254:
        if fn + '_Printf_format_string_ const char *fmt, ...) {' not in src:
            problems.append('TruMenu.cpp: %s...) needs _Printf_format_string_ on fmt' % fn.strip())
    bare = re.findall(r'\n[^\n]*(?<!_Printf_format_string_ )const char \*fmt, \.\.\.\)', code)
    if bare: problems.append('TruMenu.cpp: printf-style function(s) without _Printf_format_string_: %s' % bare[0].strip()[:80])
    if re.search(r'const char \*fmt, auto\.\.\.', code):
        problems.append('TruMenu.cpp: a format forwarded through auto... escapes the /analyze check')
    # ---- (3) S7 fresh entry
    fe = fn_body(src, 'bool S7FreshEntry(')
    for want in ('(nb + 0x88) = 0;', '(nb + 0xb2) = 0;', '(nb + 0xb4) = 0;', '__except (EXCEPTION_EXECUTE_HANDLER)'):
        if want not in fe: problems.append('TruMenu.cpp: S7FreshEntry lacks %s' % want)
    ex = re.sub(r'//[^\n]*', '', fn_body(src, 'void S7Extend('))
    seq = [ex.find('ReadDword(kSoUnitCount, &before)'), ex.find('reinterpret_cast<S7FindFn>(kS7Find)(name)'),
           ex.find('after == before + 1'), ex.find('last == nb'), ex.find('S7FreshEntry(nb)'),
           ex.find('ReadDword(nb + 0x8c, &loaded)'), ex.find('ReadDword(nb + 0x88, &h)')]
    if any(x < 0 for x in seq) or seq != sorted(seq):
        problems.append('TruMenu.cpp: S7Extend must clear a new entry (count + 1, last = it) before it reads +0x8c / +0x88 (%s)'
                        % seq)
    if os.path.exists(S7_CHECKS_02254):
        mine = pre_rows(S7_CHECKS_02254)
        rows7 = [(a.lower(), b.lower()) for a, b in sv_rows(src, 'kS7Checks')]
        if rows7 != mine or len(mine) != 23: problems.append('TruMenu.cpp: kS7Checks must be the 23 rows of precheck_02254.txt')
        if os.path.exists(S7_CHECKS_02253) and pre_rows(S7_CHECKS_02253) != mine[:17]:
            problems.append('precheck_02254.txt must start with the 17 rows of precheck_02253.txt')
    else:
        problems.append('work/menu54_1511/precheck_02254.txt missing')
    # ---- (4) reset at start
    rs = re.sub(r'//[^\n]*', '', fn_body(src, 'void SndResetAtStart('))
    for want in ('OptInt(ini, "Sound", "ResetAtStart")', '{"Media", "MuteMusic"}', '{"Media", "MuteAmbient"}',
                 '{"Sound", "ReverbOff"}', 'WritePrivateProfileStringA(k[0], k[1], "0", ini)', 'static bool done',
                 'if (!g_sndResetAtStart) {'):
        if want not in rs: problems.append('TruMenu.cpp: SndResetAtStart lacks %s' % want)
    for keep in ('LogFollowMute', 'LogHideSubs', 'ReverbFollowsMute', 'SonarMute', 'LogOnlyAudible', 'LogLara'):
        if keep in rs: problems.append('TruMenu.cpp: SndResetAtStart must keep %s (a filter / kept switch)' % keep)
    ro = re.sub(r'//[^\n]*', '', fn_body(src, 'void ReadOptions('))
    seq = [ro.find('SndResetAtStart(ini);'), ro.find('OptInt(ini, "Media", "MuteMusic")'),
           ro.find('OptInt(ini, "Media", "MuteAmbient")'), ro.find('W9ReadOptions(ini);')]
    if any(x < 0 for x in seq) or seq != sorted(seq):
        problems.append('TruMenu.cpp: ReadOptions must call SndResetAtStart before MuteMusic / MuteAmbient / ReverbOff (%s)' % seq)
    if 'Log(1, "0.22.54 sound switches at start: %s"' not in fn_body(src, 'void Start('):
        problems.append('TruMenu.cpp: Start must log the reset (0.22.54 sound switches at start)')
    header, opt_rows = table(src)
    if {(s, k): d for s, k, d, _ in opt_rows}.get(('Sound', 'ResetAtStart')) != '1':
        problems.append('TruMenu.cpp: kOpts [Sound] ResetAtStart=1 missing')
    if item_types(src).get('snd.resetatstart') != 'bool': problems.append('TruMenu.cpp: item snd.resetatstart (bool) missing')
    rows = [r for r in qb_rows(src) if r[0] == 'kQbSettings']
    keys = [(r[2], r[3], r[4]) for r in rows]
    th = keys.index(('-', 'ton_log_hear', 'kQbGroup')) if ('-', 'ton_log_hear', 'kQbGroup') in keys else -1
    if th < 0 or keys[th + 4:th + 6] != [('snd.reverboff', '', 'kQbBool'), ('snd.resetatstart', '', 'kQbBool')]:
        problems.append('TruMenu.cpp: Stumm / Solo needs the row snd.resetatstart right after Hall aus')
    sw = open(switches_path, encoding='utf-8').read()
    if not re.search(r'\nTruMenu \| Sound \| ResetAtStart \| bool \| [^\n]*\| restart \| 1 \| [^\n]*\| TruMenu 0\.22\.54', sw):
        problems.append('switches: row TruMenu | Sound | ResetAtStart | bool | ... | restart | 1 | ... | TruMenu 0.22.54 missing')
    # ---- (5) mu_menu = group 1
    subs = w11_subs(src)
    if 'mu_menu' not in subs: problems.append('TruMenu.cpp: sub-group mu_menu (group 1) missing')
    m = re.search(r'const signed char kW8GroupSub\[80\] = \{(.*?)\};', src, re.S)
    gs = re.findall(r'kW8s[A-Za-z0-9]+', re.sub(r'//[^\n]*', '', m.group(1))) if m else []
    if len(gs) != 80 or gs[1] != 'kW8sMuMenu' or gs[2] != 'kW8sMuMusic':
        problems.append('TruMenu.cpp: kW8GroupSub[1] must be kW8sMuMenu, [2] kW8sMuMusic')
    if 'group == 13 ? kW8sMuStinger : group == 1 ? kW8sMuMenu : kW8sMuMusic' not in fn_body(src, 'int W8SubOfGroup('):
        problems.append('TruMenu.cpp: W8SubOfGroup must give group 1 the sub-group mu_menu')
    for item, kind in (('snd.logsub', 'kQbBool'), ('snd.hear', 'kQbValue')):
        if (item, 'mu_menu', kind) not in keys: problems.append('TruMenu.cpp: row %s mu_menu missing' % item)
    # ---- (6) heading gone
    if re.search(r'\{"Schnell-H[^\n]*kQbLabel', code): problems.append('TruMenu.cpp: the heading row Schnell-Hoeren must be gone')
    # ---- (7) joint.set drive (owner 20:28, l3_chapel door rail out of its limits): clamp, ramped lock, guards, tick log
    jw = fn_body(src, 'void JtWrite(')
    if 'd.type == 1 ? d.lock * 0.017453292519943295f : d.lock' not in jw:
        problems.append('TruMenu.cpp: JtWrite must write the moving lock, not the target')
    jt = re.sub(r'//[^\n]*', '', fn_body(src, 'void JtTick('))
    seq = [jt.find('g_jt.lines < 400'), jt.find("left the joint's limits"), jt.find('moves away from the target'),
           jt.find('overshot the target'), jt.find('if (line[0]) { JtStop(line, true); return; }'), jt.find('JtWrite(g_jt);')]
    if any(x < 0 for x in seq) or seq != sorted(seq):
        problems.append('TruMenu.cpp: JtTick must log the tick and stop on limits / away / overshoot before JtWrite (%s)' % seq)
    for want in ('if (g_jt.limits && (v < g_jt.limLo - margin || v > g_jt.limHi + margin))',
                 'else if (dist > g_jt.best + away)', 'else if (passed && dist > over)',
                 'if (val && next > v + lead) next = v + lead;', 'if (val && next < v - lead) next = v - lead;',
                 'if (g_jt.limits && next < g_jt.limLo) next = g_jt.limLo;', 'g_jtTried[g_jtTriedN++] ='):
        if want not in jt: problems.append('TruMenu.cpp: JtTick lacks %s' % want)
    js = fn_body(src, 'bool RunJointSet(')
    for want in ('d.limits = d.saveLimit && lim[0] < lim[1];', 'clamped to the limit', 'd.lock = cur;'):
        if want not in js: problems.append('TruMenu.cpp: RunJointSet lacks %s' % want)
    # 0.22.56: no joint "solve" rows at all; the "tried" text stays on the list rows
    if '"range not armed here (tried)"' not in src or 'right 2x = solve' in src:
        problems.append('TruMenu.cpp: a puzzle row tried without a node change must not offer "solve" again')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8-sig').read()
    if '## 0.22.54' not in readme or 'TO TEST 0.22.54' not in readme:
        problems.append('README.md: section "## 0.22.54" with "TO TEST 0.22.54" missing')
    return problems, 'kHow per kind + format annotations, S7FreshEntry (%d byte checks), ResetAtStart, mu_menu, no heading' % \
        len(sv_rows(src, 'kS7Checks'))


def check_02255():
    """0.22.55 (package P2a, docs/Pakete-1611.md; owner live notes 2026-11-15): (1) kVersion starts with 0.22.55; (2) page
    Kapitel row chapter.reload first (kQfConfirm), Lara's chapter start from kChapOrder ("Kapitel " / "Prolog" headings)
    through ChapSteps + ShortcutStart; (3) [Cheat] FlightKeepOnLoad default 0, item flight.keep (bool) right after
    Flug-Tempo, FlightOffForLoad before the request in LoadUnit / after the refusals in LevelStartInGame / before
    MissionCall, cp.jump without cheat.flight 1 / dbg.cpgo and with the trailing cheat.flight 0; (4) doppelganger_casual
    refused for the live switch without the doppelganger flag (CosBlocked in SwitchCostume before 0x6f0a90, in the
    costume rows); (5) UnitNotFound in LoadUnit / RunLevelStart / ChapSteps; (6) kUnitsPerMetre 290 in DvDistText; (7)
    kMbChecks (5 rows), MbPartOf (link table +0x6c / +0x70, stamp +0x44, bone 0 +0x90 / +0x30) before the same-place merge
    of the uber labels and before DvVisible of the names; (8) the pole scan by object name + instanceref members, no id
    list; (9) README"""
    problems = []
    src = read_cpp()
    code = re.sub(r'//[^\n]*', '', src)
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '"TruMenu 0.22.55 (chapter page + display fixes' not in ver and '" - 0.22.55 (chapter page + display fixes' not in ver:
        problems.append('TruMenu.cpp: kVersion must start with "TruMenu 0.22.55 (chapter page + display fixes ..."')
    # ---- (2) chapter.reload
    ch = [r for r in qb_rows(src) if r[0] == 'kQbChapters']
    if not ch or (ch[0][2], ch[0][3], ch[0][4]) != ('chapter.reload', '', 'kQbAction'):
        problems.append('TruMenu.cpp: kQbChapters must start with the row chapter.reload (action)')
    if item_types(src).get('chapter.reload') != 'action': problems.append('TruMenu.cpp: item chapter.reload (action) missing')
    rc = re.sub(r'//[^\n]*', '', fn_body(src, 'bool RunChapReload('))
    seq = [rc.find('ChapReloadPlan('), rc.find('ChapSteps(unit, steps, sizeof(steps), &menu, why, sizeof(why))'),
           rc.find('ShortcutStart(steps, title,')]
    if any(x < 0 for x in seq) or seq != sorted(seq):
        problems.append('TruMenu.cpp: RunChapReload must plan, then ChapSteps, then ShortcutStart (%s)' % seq)
    cs = fn_body(src, 'const ChapOrder *ChapStartOf(')
    for want in ('!strncmp(h, "Kapitel ", 8)', '!strncmp(h, "Prolog", 6)', 'strcmp(kChapOrder[i].group, group)'):
        if want not in cs: problems.append('TruMenu.cpp: ChapStartOf lacks %s' % want)
    # ---- (3) flight
    header, opt_rows = table(src)
    if {(s, k): d for s, k, d, _ in opt_rows}.get(('Cheat', 'FlightKeepOnLoad')) != '0':
        problems.append('TruMenu.cpp: kOpts [Cheat] FlightKeepOnLoad=0 missing')
    if item_types(src).get('flight.keep') != 'bool': problems.append('TruMenu.cpp: item flight.keep (bool) missing')
    lara = [(r[2], r[3], r[4]) for r in qb_rows(src) if r[0] == 'kQbLara']
    k = lara.index(('cheat.speed', '', 'kQbValue')) if ('cheat.speed', '', 'kQbValue') in lara else -1
    if k < 0 or lara[k + 1:k + 2] != [('flight.keep', '', 'kQbBool')]:
        problems.append('TruMenu.cpp: page Figur needs the row flight.keep right after Flug-Tempo')
    if 'InterlockedExchange(&g_flightKeep, OptInt(ini, "Cheat", "FlightKeepOnLoad") != 0 ? 1 : 0);' not in \
            fn_body(src, 'void ReadOptions('):
        problems.append('TruMenu.cpp: ReadOptions must read [Cheat] FlightKeepOnLoad')
    fo = fn_body(src, 'void FlightOffForLoad(')
    for want in ('if (g_flightKeep) return;', '(kCheatMode) = 0;', '(reinterpret_cast<void *>(player), 12, 0)', 'g_flight = false;'):
        if want not in fo: problems.append('TruMenu.cpp: FlightOffForLoad lacks %s' % want)
    lu = re.sub(r'//[^\n]*', '', fn_body(src, 'bool LoadUnit('))
    seq = [lu.find('UnitNotFound(unit, o, n)'), lu.find('FlightOffForLoad("level.load");'),
           lu.find('reinterpret_cast<LevelChangeFn>(kLevelChange)')]
    if any(x < 0 for x in seq) or seq != sorted(seq):
        problems.append('TruMenu.cpp: LoadUnit must check the unit, end the flight, then request (%s)' % seq)
    lg = re.sub(r'//[^\n]*', '', fn_body(src, 'bool LevelStartInGame('))
    seq = [lg.find('if (CinematicNow())'), lg.find('FlightOffForLoad('), lg.find('reinterpret_cast<MissionStartFn>(kUgdF27)')]
    if any(x < 0 for x in seq) or seq != sorted(seq):
        problems.append('TruMenu.cpp: LevelStartInGame must end the flight after its refusals, before f27 (%s)' % seq)
    ls = re.sub(r'//[^\n]*', '', fn_body(src, 'bool RunLevelStart('))
    seq = [ls.find('UnitNotFound(name, o, n)'), ls.find('FlightOffForLoad("the mission start");'), ls.find('MissionCall(args, select)')]
    if any(x < 0 for x in seq) or seq != sorted(seq):
        problems.append('TruMenu.cpp: RunLevelStart must check the unit and end the flight before MissionCall (%s)' % seq)
    cj = re.sub(r'//[^\n]*', '', fn_body(src, 'bool RunCpJump('))
    if 'cheat.flight 1' in cj or 'dbg.cpgo %ld' in cj: problems.append('TruMenu.cpp: cp.jump must not turn flight on')
    if 'const char *off = flying ? "" : ";cheat.flight 0";' not in cj:
        problems.append('TruMenu.cpp: cp.jump must end with cheat.flight 0 when flight was off')
    # ---- (4) costume 857
    cb = fn_body(src, 'bool CosBlocked(')
    for want in ('"doppelganger_casual"', 'ReadDword(0x00fadb58, &tracker)', 'ReadByte(tracker + 0x1244, &dg) && dg) return false;'):
        if want not in cb: problems.append('TruMenu.cpp: CosBlocked lacks %s' % want)
    sc = re.sub(r'//[^\n]*', '', fn_body(src, 'bool SwitchCostume('))
    if not 0 <= sc.find('CosBlocked(target,') < sc.find('reinterpret_cast<VoidFn>(kCostumeSwitch)()'):
        problems.append('TruMenu.cpp: SwitchCostume must refuse a blocked costume before 0x6f0a90')
    if 'CosBlocked(g_cos.ids[i], de, block, sizeof(block))' not in fn_body(src, 'int QbCosRows('):
        problems.append('TruMenu.cpp: QbCosRows must grey a blocked costume')
    if 'CosBlocked(static_cast<int>(q.intro), de, block, sizeof(block))' not in fn_body(src, 'void QbCosAct('):
        problems.append('TruMenu.cpp: QbCosAct must refuse a blocked costume row')
    # ---- (5) level not found
    nf = fn_body(src, 'bool UnitNotFound(')
    if 'UnitIndexOf(unit) >= 0 || UnitNameInNoArchive(unit) || !UnitModsDrmMissing(unit)) return false;' not in nf:
        problems.append('TruMenu.cpp: UnitNotFound must pass the level list, the Q105 names and an existing mods drm')
    if 'if (UnitNotFound(unit, o, on)) return false;' not in fn_body(src, 'bool ChapSteps('):
        problems.append('TruMenu.cpp: ChapSteps must refuse a missing unit before the backup step')
    # ---- (6) metres
    if 'const float kUnitsPerMetre = 290.0f;' not in src: problems.append('TruMenu.cpp: kUnitsPerMetre 290 missing')
    dd = re.sub(r'//[^\n]*', '', fn_body(src, 'void DvDistText('))
    if '/ 100.0f' in dd or dd.count('/ kUnitsPerMetre') != 2:
        problems.append('TruMenu.cpp: DvDistText must divide distance and height by kUnitsPerMetre')
    # ---- (7) multibody parts
    mb = src[src.find('const NavCheckBytes kMbChecks[] = {'):]
    n_mb = len(re.findall(r'\{0x[0-9a-fA-F]{8},', mb[:mb.find('\n};')]))
    if n_mb != 5: problems.append('TruMenu.cpp: kMbChecks must hold 5 rows (%d)' % n_mb)
    mp = fn_body(src, 'bool MbPartOf(')
    for want in ('ReadDword(x + 0x70, &count)', 'ReadDword(x + 0x6c, &table)', 'ReadDword(inst + 0x44, &now) || now != stamp',
                 'ReadDword(inst + 0x90, &mats)', 'ReadFloats(mats + 0x30, p, 3)', 'fabsf(p[c] - o[c]) < kMbFar'):
        if want not in mp: problems.append('TruMenu.cpp: MbPartOf lacks %s' % want)
    ul = re.sub(r'//[^\n]*', '', fn_body(src, 'void DrawUberLabels('))
    if not 0 <= ul.find('MbPartOf(g_ubCand[i].inst, &parts[i])') < ul.find('int dupOf[33], dupN[33];'):
        problems.append('TruMenu.cpp: DrawUberLabels must move the parts before the same-place merge')
    dn = re.sub(r'//[^\n]*', '', fn_body(src, 'void DvDrawNames('))
    if not 0 <= dn.find('MbPartOf(inst, &part) && part.posOk') < dn.find('DvVisible(c, p, 100.0f, &d2)'):
        problems.append('TruMenu.cpp: DvDrawNames must take the part position before DvVisible')
    if 'MbCheck();' not in re.sub(r'//[^\n]*', '', fn_body(src, 'void Start(')):
        problems.append('TruMenu.cpp: Start must run MbCheck')
    # ---- (8) poles: by name at run time, no id list
    ps = fn_body(src, 'void PlScan(')
    for want in ('ObjectId("ma_pt_pole_a")', 'ObjectId("ma_pt_pole_hole")', 'ReadDword(inst + 0xe0, &unit)', 'PlIsInstRef('):
        if want not in ps: problems.append('TruMenu.cpp: PlScan lacks %s' % want)
    if '"instanceref"' not in fn_body(src, 'bool PlIsInstRef('): problems.append('TruMenu.cpp: PlIsInstRef must test the type name')
    if re.search(r'const (?:LONG|DWORD|int|WORD) kPl[A-Za-z]*\[\]', code):
        problems.append('TruMenu.cpp: no pole id table in the source (game data) - the scan decides at run time')
    if 'PlVerdict(d.inst) == 1' not in fn_body(src, 'void DvDrawNames(') or 'PlScan();' not in fn_body(src, 'void PzRefresh('):
        problems.append('TruMenu.cpp: the names layer and the puzzle list must show the pole verdict')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8-sig').read()
    if '## 0.22.55' not in readme or 'TO TEST 0.22.55' not in readme:
        problems.append('README.md: section "## 0.22.55" with "TO TEST 0.22.55" missing')
    return problems, ('chapter.reload, FlightKeepOnLoad + cp.jump without flight, doppelganger_casual guard, level not found, '
                      '290 units / m, multibody part labels (%d byte checks), pole scan' % n_mb)


def check_02257():
    """0.22.57 (package Q2): (1) kVersion starts with 0.22.57; (2) export TruMenuPuzzleList; (3) puzzle.figures refused
    while the fire is out; (4) hold kinds: PzKeepTick in PzGameTick, the timer write only to [b+0x88], the counter
    command only through tlact::CmdExec, the hinge wrap (tlobj::HingeUnwrap) in PzDoorOf and in the shared drive; (5)
    switch -> command from the scripts (PzSwitchEntry) and the 0.22.56 'continue' that skipped the door rows gone;
    (6) "already used" from +0x1c bit 0x200; (7) level not found before queueing; (8) no game ids in the new code;
    (9) README section"""
    problems = []
    src = read_cpp()
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '"TruMenu 0.22.57 (puzzle helpers 2' not in ver and ' - 0.22.57 (puzzle helpers 2' not in ver:   # 0.22.58: later head
        problems.append('TruMenu.cpp: kVersion must start with "TruMenu 0.22.57 (puzzle helpers 2 ..." (or name it later)')
    if 'extern "C" __declspec(dllexport) int __cdecl TruMenuPuzzleList(char *out, int size, int lang)' not in src:
        problems.append('TruMenu.cpp: export TruMenuPuzzleList missing')
    figures = fn_body(src, 'bool RunPzFigures(')
    if 'if (fire == 0) {' not in figures:
        problems.append('TruMenu.cpp: RunPzFigures must refuse while the fire is out')
    if 'PzKeepTick();' not in fn_body(src, 'void PzGameTick('):
        problems.append('TruMenu.cpp: PzGameTick must run PzKeepTick')
    keep = fn_body(src, 'void PzKeepTick(')
    if 'void PzKeepTickOne(PzKeep &q) {' in src:   # 0.22.59: one body per hold slot
        keep = fn_body(src, 'void PzKeepTickOne(PzKeep &q) {')
    if 'lb + 0x88) = 0.0f' not in keep or 'tlact::CmdExec(q.x, q.openCmd)' not in keep:
        problems.append('TruMenu.cpp: PzKeepTick must write only the time in node and send only the opening entry')
    core = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'TruPuzzleCore.h'), encoding='utf-8').read()
    if 'tlobj::HingeUnwrap(d->v' not in core or 'inline int PzSwitchEntry(' not in core:
        problems.append('TruPuzzleCore.h: PzDoorOf with HingeUnwrap / PzSwitchEntry missing')
    act = open(os.path.join(ROOT, 'src', 'asi', 'TruLink', 'TruLinkAct.h'), encoding='utf-8').read()
    if act.count('tlobj::HingeUnwrap(') < 2:
        problems.append('TruLinkAct.h: the drive must take the hinge wrap (tick + stop)')
    rows = fn_body(src, 'void PzNewRows(')
    if 'if (!ring) continue;' in rows:
        problems.append('TruMenu.cpp: PzNewRows still skips the door rows after a non-ring check')
    if 'PzSwUsed(o.inst)' not in rows or 'PzDataSwitch(' not in rows:
        problems.append('TruMenu.cpp: PzNewRows must use PzSwUsed and PzDataSwitch')
    inv = fn_body(src, 'const char *InvokeCore(')
    if 'UnitNotFound(unit, why, sizeof(why))' not in inv:
        problems.append('TruMenu.cpp: InvokeCore must test "level not found" before queueing')
    for name in ('bool PzHoldRows(', 'int PzCounterOf(', 'bool RunPzWeights(', 'void PzKeepTick(', 'int PzListText('):
        body = re.sub(r'//[^\n]*', '', fn_body(src, name))
        if not body: problems.append('TruMenu.cpp: %s missing' % name)
        elif re.search(r'\b(48[0-9]{2}|9[0-9]{3}|45[0-9]{2})\b', body):
            problems.append('TruMenu.cpp: %s holds a game id' % name)
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8').read()
    if '## 0.22.57' not in readme or 'TO TEST 0.22.57' not in readme:
        problems.append('README.md: section "## 0.22.57" with "TO TEST 0.22.57" missing')
    return problems, 'puzzle helpers 2 (fire rule, three hold kinds, hinge wrap, switch -> command from the scripts, used bit, ' \
                     'weights -> plate, puzzle list export, level not found before queueing)'


def check_02258():
    """0.22.58 (package Q1b, spec S1 - S7 of Q1a + Q4 costume 857): (1) kVersion starts with 0.22.58; (2) the byte checks
    kCrChecks (6 rows = ENGINE section 4.2 "Death restart request") and kDgChecks (5 rows = ENGINE section 20.6 "Player
    message 35"); (3) cp.reload writes only the request bit (no health, no tracker flags) after its refusals (main state
    1, a player, no cutscene, no level change pending, not already set) and after FlightOffForLoad + ChArm; (4) level.keep
    = LoadUnit, then the played mark (key 5968) through UiMarkSet, then the watchdog; level.reload / chapter.keep /
    chapter.unit use it; (5) the intro table comes from TruMenu.unitintros.txt (no intro id table in the source); (6) the
    fresh unit start writes marks only in main state 2; (7) mid-chapter rows = chapter.unit, chapter starts = level.load
    through ChapSteps; (8) costume: fix A by name (ObjectId("dlc_doppel_costume_a")), option B writes +0x390 only in
    DgBeforePost right before message 35 and checks slot 0 (WM + 4); (9) [Chapter] UnitFresh / [Costume] DoppelLive
    default 0; (10) README"""
    problems = []
    src = read_cpp()
    code = re.sub(r'//[^\n]*', '', src)
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '"TruMenu 0.22.58 (chapter / loading + costume 857' not in ver and \
            ' - 0.22.58 (chapter / loading + costume 857' not in ver:   # 0.22.59: later head
        problems.append('TruMenu.cpp: kVersion must start with "TruMenu 0.22.58 (chapter / loading + costume 857 ..."')
    # ---- (2) byte checks
    def rows_of(start, stop):
        part = src[src.find(start):src.find(stop, src.find(start))]
        return {a: h.replace(' ', '') for a, h in re.findall(r'\{0x([0-9a-f]{8}), "([0-9a-f ]+)"\}', part)}
    cr = rows_of('const ChCheck kCrChecks[] = {', '};')
    want_cr = {'005dfcad': 'f705b8f0e70000100000', '005dfcba': '8b4730a9000008007427',
               '005dfcc4': '25fffff7ff57894730e80e48ffff', '005dfcda': 'e8a1e7ffffeb076a06e878faffff',
               '005d44e0': '8b4424045332db3898690100007427a16492c50083c010', '006f55a7': '810db8f0e70000000800'}
    if cr != want_cr: problems.append('TruMenu.cpp: kCrChecks must hold the 6 rows of ENGINE 4.2 (got %s)' % sorted(cr))
    dg = rows_of('const ChCheck kDgChecks[] = {', '};')
    want_dg = {'007200ba': '8b3d6492c500', '007200c0': '81c790030000', '007200c6': '3817755b',
               '007200df': '80b94412000000', '00720125': 'a158dbfa00'}
    if dg != want_dg: problems.append('TruMenu.cpp: kDgChecks must hold the 5 rows of ENGINE 20.6 (got %s)' % sorted(dg))
    # ---- (3) cp.reload
    rc = re.sub(r'//[^\n]*', '', fn_body(src, 'bool RunCpReload('))
    seq = [rc.find('!CrOk()'), rc.find('state != 1'), rc.find('if (!InLevel())'), rc.find('if (CinematicNow())'),
           rc.find('LevelChangePending(why, sizeof(why))'), rc.find('if (flags & 0x80000)'), rc.find('FlightOffForLoad("cp.reload");'),
           rc.find('ChArm("cp.reload");'), rc.find('_InterlockedOr(reinterpret_cast<volatile long *>(kStreamFlags), 0x80000);')]
    if any(x < 0 for x in seq) or seq != sorted(seq):
        problems.append('TruMenu.cpp: RunCpReload must refuse, end the flight, arm the hint clear, then set the bit (%s)' % seq)
    for bad in ('0x628', '0x968', '0x960', 'kLevelChange', '0x5de480', '0x5df760'):
        if bad in re.sub(r'"[^"\n]*"', '', rc): problems.append('TruMenu.cpp: RunCpReload must only set the request bit (%s)' % bad)
    if 'CrTick(state);' not in fn_body(src, 'void UiTick(') or 'UiTick(state);' not in fn_body(src, 'void ChTick('):
        problems.append('TruMenu.cpp: ChTick -> UiTick -> CrTick missing')
    # ---- (4) keep-state load
    kl = re.sub(r'//[^\n]*', '', fn_body(src, 'bool KeepLoad('))
    seq = [kl.find('if (!LoadUnit(unit, o, n)) return false;'), kl.find('UiMarkSet(h, 0)'), kl.find('WdArm(unit, what);')]
    if any(x < 0 for x in seq) or seq != sorted(seq):
        problems.append('TruMenu.cpp: KeepLoad must request, clear the mark, then arm the watch (%s)' % seq)
    if 'return KeepLoad(unit, "level.reload", o, n);' not in fn_body(src, 'bool RunReload('):
        problems.append('TruMenu.cpp: RunReload must go through KeepLoad')
    if 'Out(steps, sizeof(steps), "save.backup kapitel;level.keep %s", unit);' not in fn_body(src, 'bool RunChapKeep('):
        problems.append('TruMenu.cpp: RunChapKeep must use level.keep')
    if 'Out(steps, sizeof(steps), "save.backup kapitel;level.keep %s", unit);' not in fn_body(src, 'bool RunChapUnit('):
        problems.append('TruMenu.cpp: RunChapUnit must use level.keep by default')
    if 'const WORD kUiPlayedKey = 5968;' not in src: problems.append('TruMenu.cpp: kUiPlayedKey 5968 missing')
    wd = fn_body(src, 'void WdTick(')
    if 'now - g_wd.cineTick >= 10000' not in wd or 'WdScriptLine(g_scriptPartial);' not in fn_body(src, 'void ScriptText('):
        problems.append('TruMenu.cpp: watchdog: 10 s after "Cine already played", fed from ScriptText')
    # ---- (5) intro table from the file, no ids in the code
    if '"%sTruMenu.unitintros.txt"' not in fn_body(src, 'void UiLoad('):
        problems.append('TruMenu.cpp: UiLoad must read TruMenu.unitintros.txt')
    sec = code[code.find('struct UiIntro {'):code.find('void UiTick(DWORD state) {')]
    for gid in ('997', '2562', '4318', '4483', '5484', '7530', '7652', '9071'):
        if re.search(r'\b%s\b' % gid, sec): problems.append('TruMenu.cpp: intro id %s in the 0.22.58 code (game data)' % gid)
    # ---- (6) fresh marks only in main state 2
    im = fn_body(src, 'void ImTick(')
    if not 0 <= im.find('if (state == 2) {') < im.find('UiMarkSet(h, 1)'):
        problems.append('TruMenu.cpp: ImTick must write the marks only in main state 2')
    if 'if (ok && mark) ImArm(name);' not in fn_body(src, 'bool RunLevelStart('):
        problems.append('TruMenu.cpp: RunLevelStart must arm the marks after the in-level start ("mark")')
    # ---- (7) rows by kind
    qr = fn_body(src, 'int QbChapRows(')
    if 'ChapIsStartRow(co, kUnits[i].unit)' not in qr or '"chapter.unit", kUnits[i].unit, kQbAction' not in qr:
        problems.append('TruMenu.cpp: QbChapRows must split chapter starts (level.load) from chapter.unit rows')
    ch = [r for r in qb_rows(src) if r[0] == 'kQbChapters']
    if len(ch) < 2 or (ch[1][2], ch[1][4]) != ('cp.reload', 'kQbAction'):
        problems.append('TruMenu.cpp: kQbChapters row 2 must be cp.reload')
    for item, kind in (('cp.reload', 'action'), ('level.keep', 'action'), ('chapter.unit', 'action'),
                       ('chapter.unitfresh', 'bool'), ('costume.doppellive', 'bool'), ('chapter.intros', 'info')):
        if item_types(src).get(item) != kind: problems.append('TruMenu.cpp: item %s (%s) missing' % (item, kind))
    # ---- (8) costume
    sc = re.sub(r'//[^\n]*', '', fn_body(src, 'bool SwitchCostume('))
    if not 0 <= sc.find('CosRedirect(target)') < sc.find('CosValidCall(static_cast<WORD>(clone))') < \
            sc.find('reinterpret_cast<VoidFn>(kCostumeSwitch)()'):
        problems.append('TruMenu.cpp: SwitchCostume must redirect and check the clone before 0x6f0a90')
    if 'ObjectId("dlc_doppel_costume_a")' not in fn_body(src, 'int CosDoppelClone('):
        problems.append('TruMenu.cpp: the clone must be found by name')
    if code.count('+ 0x390) = 0') != 1 or '+ 0x390) = 0' not in fn_body(src, 'void DgBeforePost('):
        problems.append('TruMenu.cpp: +0x390 is written only in DgBeforePost')
    wt = fn_body(src, 'void WeaponsTick(')
    if not 0 <= wt.find('if (b) DgBeforePost();') < wt.find('Post(player, 35, 0);'):
        problems.append('TruMenu.cpp: WeaponsTick must write +0x390 right before message 35')
    if 'HandleInstance(wm + 4)' not in fn_body(src, 'void DgSlotCheck('):
        problems.append('TruMenu.cpp: DgSlotCheck must test slot 0 (WM + 4)')
    # ---- (9) INI defaults
    header, opt_rows = table(src)
    d = {(s, k): v for s, k, v, _ in opt_rows}
    if d.get(('Chapter', 'UnitFresh')) != '0' or d.get(('Costume', 'DoppelLive')) != '0':
        problems.append('TruMenu.cpp: kOpts [Chapter] UnitFresh=0 / [Costume] DoppelLive=0 missing')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8-sig').read()
    if '## 0.22.58' not in readme or 'TO TEST 0.22.58' not in readme:
        problems.append('README.md: section "## 0.22.58" with "TO TEST 0.22.58" missing')
    return problems, 'chapter / loading (rows by kind, level.keep + intro marks, watchdog, cp.reload %d byte checks, ' \
                     'safe-ground chapter, DLC row) + costume 857 (fix A, DoppelLive %d byte checks)' % (len(cr), len(dg))


def check_02265():
    """0.22.65 (package S5, evidence instead of guesses): (1) kVersion starts with 0.22.65; log.perch default on, read
    only (no write in its section), the record set 826 / 840 / 841 / 849 / 860..867 + states 420 / 603, the DROP
    threshold 100, PchTick once per game frame; (2) Thor obstacle extents + floor ray kinds, [Cam] geometry / water
    readers read only; README section"""
    problems = []
    done = []
    src = read_cpp()
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '"TruMenu 0.22.65 (build S5' not in ver and ' - 0.22.65 (build S5' not in ver:
        problems.append('TruMenu.cpp: kVersion must start with "TruMenu 0.22.65 (build S5 ..."')
    at = src.find('// ---- 0.22.65 (package S5 1) [Perch] log')
    end = src.find('\nvoid MdTick() {', at)
    part = src[at:end] if at >= 0 and end > at else ''
    if not part:
        problems.append('TruMenu.cpp: section "0.22.65 (package S5 1) [Perch] log" before MdTick missing')
    for bad in ('WriteBytes', 'WriteDword', 'WriteFloat', 'VirtualProtect'):
        if bad in part:
            problems.append('TruMenu.cpp: the [Perch] section must only read (found %s)' % bad)
    if 'volatile LONG g_pchOn = 1;' not in part:
        problems.append('TruMenu.cpp: log.perch must default to on (g_pchOn = 1)')
    act = fn_body(src, 'bool PchActive(')
    if 'idx == 826 || idx == 840 || idx == 841 || idx == 849 || (idx >= 860 && idx <= 867)' not in act or \
            'PchRecHas(rec, 420, 603)' not in act:
        problems.append('TruMenu.cpp: PchActive must take records 826 / 840 / 841 / 849 / 860..867 and states 420 / 603 (R9 2.1)')
    tick = fn_body(src, 'void PchTick(')
    # 0.22.67 (B1): DROP only downwards (dz < -100), upwards = [Perch] LIFT
    if ('fabsf(dz) > 100.0f' not in tick and 'dz < -100.0f' not in tick) or '[Perch] DROP' not in tick or 'PchDiff(' not in tick:
        problems.append('TruMenu.cpp: PchTick must log DROP with the field diffs on > 100 units z in one frame')
    box = fn_body(src, 'void PchBoxText(')
    if 't + 0xc94' not in box or 'flags & 0x20000' not in box or 'flags & 0x10' not in box or 'ROTATED' not in box:
        problems.append('TruMenu.cpp: PchBoxText must show the box gt+0xc94, PERCH 0x20000 / PILLAR 0x10 and the matrix rotation')
    if 'PchTick(copy.sThumbLX, copy.sThumbLY);' not in fn_body(src, 'DWORD WINAPI PadHook('):
        problems.append('TruMenu.cpp: PadHook must run PchTick once per game frame')
    if '{"log.perch", "bool",' not in src:
        problems.append('TruMenu.cpp: item log.perch missing')
    lara = src[src.find('const QbRow kQbLara[] = {'):src.find('const QbRow kQbDebug[] = {')]
    if '"log.perch", "", kQbBool' not in lara:
        problems.append('TruMenu.cpp: bar row log.perch missing on kQbLara')
    done.append('1 log.perch')
    ext = fn_body(src, 'void ThObsExtent(') or fn_body(src, 'float ThObsExtent(')   # 0.22.68: returns the extent
    if 'MdProbe(a, o.pos, hit, 0, words)' not in ext or 'default 100' not in ext:
        problems.append('TruMenu.cpp: ThObsExtent must measure by queries and fall back to "default 100"')
    fin = fn_body(src, 'void ThFinish(')
    # 0.22.68 (B2 1): no floor ray cells any more (terrain mesh, rays only as the fallback) - the [Thor] terrain line
    # names the source instead (check_02268)
    if '#include "TruThorCore.h"' not in src and ('floor rays:' not in fin or 's.hitKind[i]' not in fin):
        problems.append('TruMenu.cpp: ThFinish must summarise the floor ray kinds in the [Thor] areas line')
    geo = fn_body(src, 'void CnwGeoTick(')
    if not geo or 'WriteBytes' in geo or 'kCnwCam + 0x150' not in geo or 'CnwWaterNow(' not in geo:
        problems.append('TruMenu.cpp: CnwGeoTick must read cam+0x150 and the water state only')
    wat = fn_body(src, 'int CnwWaterNow(')
    if 't + 0x8dc' not in wat or 't + 0x8e0' not in wat:
        problems.append('TruMenu.cpp: CnwWaterNow must read gt+0x8dc / gt+0x8e0 (0x5ea200)')
    if 'if (g_cnwHave == 2) CnwGeoTick(now);' not in fn_body(src, 'void CnwTick('):
        problems.append('TruMenu.cpp: CnwTick must run CnwGeoTick at level 2 only')
    done.append('2 Thor / Cam evidence')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8-sig').read()
    if '## 0.22.65' not in readme or 'TO TEST 0.22.65' not in readme:
        problems.append('README.md: section "## 0.22.65" with "TO TEST 0.22.65" missing')
    return problems, 'build S5 (%s)' % ', '.join(done)


def check_02267():
    """0.22.67 (package B1, docs Pakete-2111.md row 5): kVersion starts with 0.22.67; (1) K1: the 7 byte checks, the
    request only through 0x5c1760 after the switch (SwitchCostume / DgSlotCheck), the reload gate in LoadUnit /
    cp.reload / level.start / chapter rows, armed only after a live switch; (2) V1: puzzle.pull chains vt 58 -> vt 59 from
    on with bit 0x200 = 0 (not inside puzzle.pullto), at most 2 s; (3) N5: puzzle.pullout through the TruLinkAct drive
    (no limit / node write), item + label, rows in the targets; (4) logs: [Death] detours 8 / 7 bytes after 9 byte checks
    and nothing written in the hooks, B1 section without other writes, log.vein default on with item + bar row, the
    [Jump] velocity turned into the world, [Perch] LIFT; README section"""
    problems = []
    done = []
    src = read_cpp()
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '"TruMenu 0.22.67 (build B1' not in ver and ' - 0.22.67 (build B1' not in ver:
        problems.append('TruMenu.cpp: kVersion must start with "TruMenu 0.22.67 (build B1 ..."')
    at = src.find('// ---- 0.22.67 B1 (package B1')
    end = src.find('// ---- end of 0.22.67 B1', at)
    part = src[at:end] if at >= 0 and end > at else ''
    if not part:
        problems.append('TruMenu.cpp: section "0.22.67 B1" missing')
    k1 = src[src.find('const ChCheck kK1Checks[] = {'):]
    k1 = k1[:k1.find('};')]
    for a, h in (('0x006f0b90', '6639730e7409 53 e8640eedff'), ('0x006f0b04', 'a3c8f1e700 c705ccf1e70000000000'),
                 ('0x00555cb1', '66a1c8f1e700 6689820c020000'), ('0x00556fbd', '0fbf880c020000 890dc8f1e700'),
                 ('0x005c1760', '8b442404 6a01 50 e8e4fdffff'), ('0x005c1730', '8b442404 6a00 50 e814feffff'),
                 ('0x005de6f5', 'e8c659ffff')):
        if '{%s, "%s"}' % (a, h) not in k1:
            problems.append('TruMenu.cpp: kK1Checks row %s "%s" missing' % (a, h))
    if 'K1AfterSwitch("costume switch");' not in fn_body(src, 'bool SwitchCostume(') or \
            'K1AfterSwitch("costume B back");' not in fn_body(src, 'void DgSlotCheck('):
        problems.append('TruMenu.cpp: K1AfterSwitch must follow both live switches (SwitchCostume, DgSlotCheck)')
    req = fn_body(src, 'bool K1Request(')
    if 'QlRequestFn>(0x005c1760)' not in req:
        problems.append('TruMenu.cpp: K1Request must request through 0x5c1760 (the game\'s request with a reference)')
    gate = fn_body(src, 'bool K1Gate(')
    if 'if (!g_k1.live' not in gate or 'st == 2 && obj' not in gate:
        problems.append('TruMenu.cpp: K1Gate must act only after a live switch and pass a loaded costume')
    for fn, what in (('bool LoadUnit(', 'level.load'), ('bool RunCpReload(', 'cp.reload'), ('bool RunLevelStart(', 'level.start'),
                     ('bool RunChapKeep(', 'chapter.keep'), ('bool RunChapUnit(', 'chapter.unit'), ('bool RunChapReload(', 'chapter.reload')):
        if 'K1Gate("%s", o, n)' % what not in fn_body(src, fn):
            problems.append('TruMenu.cpp: %s) must ask K1Gate("%s")' % (fn.strip('('), what))
    done.append('1 K1')
    pull = fn_body(src, 'bool RunPzPull(')
    if 'p.chain = vt == 58 && st == 1 && !PzSwUsed(inst)' not in pull or '!PzPullToBusy(intro)' not in pull:
        problems.append('TruMenu.cpp: RunPzPull must chain only vt 58 from on with bit 0x200 = 0 outside puzzle.pullto')
    ptick = fn_body(src, 'void PzPullTick(')
    if 'p.chain == 1' not in ptick or 'PzSwState(sw) == 0' not in ptick or 'now - p.at > 2000' not in ptick:
        problems.append('TruMenu.cpp: PzPullTick must send vt 59 once +32 reads off, at most 2 s after vt 58')
    done.append('2 V1')
    pout = fn_body(src, 'bool RunPzPullOut(')
    if 'tlact::DriveBegin(g_poDrive, d)' not in pout:
        problems.append('TruMenu.cpp: RunPzPullOut must drive through the TruLinkAct drive')
    for bad in ('kJtSetLimits', 'kJtLimitOn', 'WriteDword', 'WriteBytes', '+ 0x84) ='):
        if bad in pout or bad in fn_body(src, 'bool PoFind('):
            problems.append('TruMenu.cpp: puzzle.pullout must not write limits / nodes (found %s)' % bad)
    if 'tlobj::D(tr + 0x18) != 15' not in fn_body(src, 'bool PoFind('):
        problems.append('TruMenu.cpp: PoFind must take the "joint range left" transitions (condition 15)')
    if '{"puzzle.pullout", "action",' not in src or '{"puzzle.pullout", "R' not in src:
        problems.append('TruMenu.cpp: item / confirm label puzzle.pullout missing')
    if 'PzPullOutRows(o, x, de)' not in fn_body(src, 'void PzNewRows('):
        problems.append('TruMenu.cpp: PzNewRows must offer the pull-out rows in the targets')
    done.append('3 N5')
    dh = src[src.find('const ChCheck kDhChecks[] = {'):]
    dh = dh[:dh.find('};')]
    if '{0x006f5030, "51 f60544f1e70001 c6042400 0f85fb000000"}' not in dh or \
            '{0x006f55a0, "a158dbfa00 d9ee 810db8f0e70000000800"}' not in dh:
        problems.append('TruMenu.cpp: kDhChecks must pin the two entries 0x6f5030 / 0x6f55a0')
    tick = fn_body(src, 'void DhTick(')
    if 'B1Detour(0x006f5030, 8,' not in tick or 'B1Detour(0x006f55a0, 7,' not in tick:
        problems.append('TruMenu.cpp: DhTick must move 8 bytes of 0x6f5030 and 7 of 0x6f55a0')
    for fn in ('void __cdecl DhHitHook(', 'void __cdecl DhKillHook(', 'void B1ChartTick(', 'void B1JumpTick(',
               'void B1TempoTick(', 'void B1CamTick(', 'void K1StandLine('):
        body = fn_body(src, fn)
        if not body:
            problems.append('TruMenu.cpp: %s) missing' % fn.strip('('))
        for bad in ('WriteBytes', 'WriteDword', 'WriteFloat', 'VirtualProtect', '*reinterpret_cast<volatile DWORD *>(t',
                    '*reinterpret_cast<volatile float *>(t + 0x628) ='):
            if bad in body:
                problems.append('TruMenu.cpp: %s) must only read (found %s)' % (fn.strip('('), bad))
    if part.count('WriteBytes(') != 1:
        problems.append('TruMenu.cpp: the B1 section writes code only in B1Detour (found %d WriteBytes)' % part.count('WriteBytes('))
    if 'volatile LONG g_vnOn = 1;' not in part or '{"log.vein", "bool",' not in src:
        problems.append('TruMenu.cpp: log.vein must default to on and be an item')
    lara = src[src.find('const QbRow kQbLara[] = {'):src.find('const QbRow kQbDebug[] = {')]
    if '"log.vein", "", kQbBool' not in lara:
        problems.append('TruMenu.cpp: bar row log.vein missing on kQbLara')
    note = fn_body(src, 'void MdLaunchNote(')
    if 'B1ToWorld(irot[2], vLocal, v);' not in note or 'B1NoteDrop();' not in note:
        problems.append('TruMenu.cpp: MdLaunchNote must turn v into the world and count the 0x71f6e4 calls')
    if '[Perch] LIFT' not in fn_body(src, 'void PchTick('):
        problems.append('TruMenu.cpp: PchTick must log upward jumps as [Perch] LIFT')
    if 'B1Tick(b1Raw, copy.sThumbLX, copy.sThumbLY, copy.sThumbRX, copy.sThumbRY);' not in fn_body(src, 'DWORD WINAPI PadHook('):
        problems.append('TruMenu.cpp: PadHook must run B1Tick once per game frame')
    done.append('4 logs')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8-sig').read()
    if '## 0.22.67' not in readme or 'TO TEST 0.22.67' not in readme:
        problems.append('README.md: section "## 0.22.67" with "TO TEST 0.22.67" missing')
    return problems, 'build B1 (%s)' % ', '.join(done)


def check_02268():
    """0.22.68 (package B2, docs Pakete-2111.md row 6): kVersion starts with 0.22.68; (1) Thor: TruThorCore.h holds the
    A3 rules (highest surface per cell, blocked = rise > step or hole, valid = distance > foot, 8-neighbour flood fill,
    rings -> next edge gap <= 900 / rise 0 .. 500), TruMenu copies the terrain mesh with an index check and falls back to
    rays, rebuilds at every [Push] end of the pillar, the seven [Thor] log lines, 3 INI keys, 4 items + bar rows, the
    offline selftest; README section"""
    problems = []
    done = []
    src = read_cpp()

    def rows_in(table_name):
        at = src.find('const QbRow %s[] = {' % table_name)
        return src[at:src.find('\n};', at)] if at >= 0 else ''
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '"TruMenu 0.22.68 (build B2' not in ver and ' - 0.22.68 (build B2' not in ver:
        problems.append('TruMenu.cpp: kVersion must start with "TruMenu 0.22.68 (build B2 ..."')
    core = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'TruThorCore.h'), encoding='utf-8').read()
    build = fn_body(core, 'inline bool Build(')
    for frag, what in (('R.blocked[i] = static_cast<unsigned char>(!(rise <= P.step) ? 1 : 0);', 'blocked = rise > step or hole'),
                       ('R.valid[k] = static_cast<unsigned char>(R.dist[k] > P.foot ? 1 : 0);', 'valid = distance > foot'),
                       ('for (int db = -1; db <= 1; ++db)', '8-neighbour flood fill'),
                       ('ceil(len / (cell * 0.4))', 'samples <= cell * 0.4 apart'),
                       ('LedgeDist(L[static_cast<size_t>(R.rings[r])], c) - P.head <= P.gap', 'ring areas D <= gap')):
        if frag not in build:
            problems.append('TruThorCore.h: Build must hold the rule "%s"' % what)
    cls = fn_body(core, 'inline void Classify(')
    if 'float best = 900.0f;' not in cls or 'rise < 0.0f || rise > 500.0f' not in cls:
        problems.append('TruThorCore.h: Classify must take the next edge of a ring with gap <= 900 and rise 0 .. 500')
    if not os.path.exists(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'selftest', 'TruThorCoreTest.cpp')):
        problems.append('selftest/TruThorCoreTest.cpp missing')
    mesh = fn_body(src, 'bool ThCopyMesh(')
    if 'ix[0] >= nv || ix[1] >= nv || ix[2] >= nv' not in mesh or 'WriteBytes' in mesh:
        problems.append('TruMenu.cpp: ThCopyMesh must check every face index against the vertex count (read only)')
    tick = fn_body(src, 'void ThTick(')
    if 'MdProbe(a, b, hit, s.pillar)' not in tick or 'InterlockedExchange(&s.pushEnd, 0)' not in tick or \
            'ThLaunch(s, "[Push] end");' not in tick:
        problems.append('TruMenu.cpp: ThTick must hold the ray fallback and rebuild at a [Push] end')
    if 'ThNotePushEnd(o.inst);' not in fn_body(src, 'void MdObjTick('):
        problems.append('TruMenu.cpp: MdObjTick must report each [Push] end to ThNotePushEnd')
    if 'ThNoteLaunch(p);' not in fn_body(src, 'void MdLaunchNote('):
        problems.append('TruMenu.cpp: MdLaunchNote must report Lara\'s launches to ThNoteLaunch')
    for line in ('[Thor] terrain: ', '[Thor] reach from ', '[Thor] target ', '[Thor] pillar at ', '[Thor] MISMATCH pillar at ',
                 '[Thor] foot: 4 horizontal rays', '[Thor] jump from the pillar top at '):
        if line not in src:
            problems.append('TruMenu.cpp: log line "%s" missing' % line)
    header, opt_rows = table(src)
    d = {(s, k): v for s, k, v, _ in opt_rows}
    for key, val in (('ThorStep', '10'), ('ThorFoot', '290'), ('ThorGalleryDirect', '0')):
        if d.get(('Puzzle', key)) != val:
            problems.append('TruMenu.cpp: kOpts [Puzzle] %s=%s missing' % (key, val))
    for item, kind in (('puzzle.thorstep', 'int'), ('puzzle.thorfoot', 'int'), ('puzzle.thordirect', 'bool'),
                       ('puzzle.thormap', 'bool')):
        if '{"%s", "%s",' % (item, kind) not in src:
            problems.append('TruMenu.cpp: item %s missing' % item)
        if '"%s"' % item not in rows_in('kQbChapters'):
            problems.append('TruMenu.cpp: bar row %s missing on kQbChapters' % item)
    done.append('1 Thor')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8-sig').read()
    if '## 0.22.68' not in readme or 'TO TEST 0.22.68' not in readme:
        problems.append('README.md: section "## 0.22.68" with "TO TEST 0.22.68" missing')
    return problems, 'build B2 (%s)' % ', '.join(done)


def check_02264():
    """0.22.64 (package S4, Befund-S2 "S2b Spielkamera", ENGINE 22): (1) kVersion starts with 0.22.64; cam.nowall: the
    three sites with the game's / the own bytes, the three target checks, written only in CnwTick (game thread, follow
    camera current), item + bar rows; README section"""
    problems = []
    done = []
    src = read_cpp()
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '"TruMenu 0.22.64 (build S4' not in ver and ' - 0.22.64 (build S4' not in ver:
        problems.append('TruMenu.cpp: kVersion must start with "TruMenu 0.22.64 (build S4 ..."')
    at = src.find('const CnwSite kCnwSites[3] = {')
    part = src[at:src.find('};', at)] if at >= 0 else ''
    sites = re.findall(r'\{0x([0-9a-f]{8}), \{([^}]*)\}, \{([^}]*)\}, (\d)\}', part)
    hexs = {a: (o.replace('0x', '').replace(', ', ''), p.replace('0x', '').replace(', ', ''), lv) for a, o, p, lv in sites}
    want = {'00600598': ('0f845f010000', 'e96001000090', '1'), '0060037c': ('0f842c010000', 'e92d01000090', '2'),
            '006004e3': ('0f85a8000000', 'e9a900000090', '2')}
    if hexs != want:
        problems.append('TruMenu.cpp: kCnwSites must be the three sites of Befund-S2 S2b (got %s)' % hexs)
    at = src.find('const ChCheck kCnwTargets[] = {')
    part = src[at:src.find('};', at)] if at >= 0 else ''
    rows = {a: h.replace(' ', '') for a, h in re.findall(r'\{0x([0-9a-f]{8}), "([0-9a-f ]+)"\}', part)}
    if rows != {'006004ae': '8b4c2420', '006006fd': '5f5e5b', '00600754': 'e8a7faffff'}:
        problems.append('TruMenu.cpp: kCnwTargets must be 0x6004ae / 0x6006fd / 0x600754 (got %s)' % rows)
    tick = fn_body(src, 'void CnwTick(')
    if 'cur != kCnwCam' not in tick or 'WriteBytes(s.at, to, 6)' not in tick or 'memcmp(b, from, 6)' not in tick:
        problems.append('TruMenu.cpp: CnwTick must write only with the follow camera current and only over the expected bytes')
    if 'WriteBytes' in fn_body(src, 'bool RunCamNoWall('):
        problems.append('TruMenu.cpp: RunCamNoWall must not write (game thread only)')
    if 'CnwTick();' not in fn_body(src, 'DWORD WINAPI PadHook('):
        problems.append('TruMenu.cpp: PadHook must run CnwTick once per game frame')
    if '{"cam.nowall", "action",' not in src:
        problems.append('TruMenu.cpp: item cam.nowall missing')
    lara = src[src.find('const QbRow kQbLara[] = {'):src.find('const QbRow kQbDebug[] = {')]
    for arg in ('0', '1', '2'):
        if '"cam.nowall", "%s", kQbAction' % arg not in lara:
            problems.append('TruMenu.cpp: bar row cam.nowall %s missing on kQbLara' % arg)
    done.append('1 cam.nowall')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8-sig').read()
    if '## 0.22.64' not in readme or 'TO TEST 0.22.64' not in readme:
        problems.append('README.md: section "## 0.22.64" with "TO TEST 0.22.64" missing')
    return problems, 'build S4 (%s)' % ', '.join(done)


def check_02263():
    """0.22.63 (package S3 after the analysis S2, docs Befund-S2-1911.md): (1) kVersion starts with 0.22.63; puzzle.pull
    from on = vt 58, lever / off / action; README section"""
    problems = []
    done = []
    src = read_cpp()

    def rows_in(table_name):
        at = src.find('const QbRow %s[] = {' % table_name)
        return src[at:src.find('\n};', at)] if at >= 0 else ''
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '"TruMenu 0.22.63 (build S3' not in ver and ' - 0.22.63 (build S3' not in ver:
        problems.append('TruMenu.cpp: kVersion must start with "TruMenu 0.22.63 (build S3 ..."')
    run = fn_body(src, 'bool RunPzPull(')
    if 'optLever ? 59 : optOff ? 58 : direct ? 55 : st == 0 ? 59 : 58' not in run:
        problems.append('TruMenu.cpp: RunPzPull: from on vt 58, lever / off / action = vt 59 / 58 / 55')
    done.append('1 vt 58')
    # (2) bal.nofall: the 4 byte checks of S2, the three immediates, written only through BalWrite
    def rows_of(start):
        at = src.find(start)
        part = src[at:src.find('};', at)] if at >= 0 else ''
        return {a: h.replace(' ', '') for a, h in re.findall(r'\{0x([0-9a-f]{8}), "([0-9a-f ]+)"\}', part)}
    want_bal = {'00742eea': 'b801000000eb0233c0884665', '00742f16': 'b801000000eb0233c0884665',
                '00742f3b': 'b801000000884665eb23', '00764c50': '8a91bd030000'}
    if rows_of('const ChCheck kBalChecks[] = {') != want_bal:
        problems.append('TruMenu.cpp: kBalChecks must be the 4 rows of Befund-S2 section 1')
    if 'const DWORD kBalImm[3] = {0x00742eeb, 0x00742f17, 0x00742f3c};' not in src:
        problems.append('TruMenu.cpp: kBalImm must be 0x742eeb / 0x742f17 / 0x742f3c')
    if 'WriteBytes(at, &want, 1)' not in fn_body(src, 'bool BalWrite(') or '{"bal.nofall", "bool",' not in src:
        problems.append('TruMenu.cpp: bal.nofall item / BalWrite missing')
    done.append('2 bal.nofall')
    # (3) photo extras: byte checks, the bits set / put back only through InterlockedOr / InterlockedAnd, items, rows
    want_phx = {'005c69f1': 'f7461400080000', '005c6b7f': 'f7461400080000', '005b9521': 'f7461400080000',
                '005dfe29': 'e8329bfdff'}
    if rows_of('const DvCheck kPhxChecks[] = {') != want_phx:
        problems.append('TruMenu.cpp: kPhxChecks must be the 4 rows of Befund-S2 sections 3 / 4')
    if 'InterlockedOr(Word32(player + 0x1c), 0x1000L);' not in fn_body(src, 'void PrStart(') or \
            'if (!(r.old & 0x1000)) InterlockedAnd(Word32(r.inst + 0x1c), ~0x1000L);' not in fn_body(src, 'void PrEnd('):
        problems.append('TruMenu.cpp: photo.pose run bit +0x1c 0x1000: set in PrStart, exactly back in PrEnd')
    if 'if (!(e.old & 0x800)) InterlockedAnd(Word32(e.inst + 0x14), ~0x800L);' not in fn_body(src, 'void LhShow(') or \
            'tlobj::D(e.inst + 0x44) != e.stamp' not in fn_body(src, 'void LhShow('):
        problems.append('TruMenu.cpp: photo.show must put 0x800 back exactly, only on unchanged instances')
    if 'PrEnd(reason);' not in fn_body(src, 'void PmLeave(') or 'LhShow(reason);' not in fn_body(src, 'void PmLeave('):
        problems.append('TruMenu.cpp: photo.off must end the run bit and show Lara')
    for item in ('photo.shotui', 'photo.hide', 'photo.show'):
        if '{"%s", "action",' % item not in src: problems.append('TruMenu.cpp: item %s missing' % item)
        if '"%s"' % item not in fn_body(src, 'const QbRow kQbLara[] = {') and \
                '"%s"' % item not in src[src.find('const QbRow kQbLara[] = {'):src.find('const QbRow kQbDebug[] = {')]:
            problems.append('TruMenu.cpp: bar row %s missing on kQbLara' % item)
    if '!g_qbOpen && !g_menuOpen && !g_radOpen' not in fn_body(src, 'void PhxTick('):
        problems.append('TruMenu.cpp: photo.shotui waits until bar / menu / ring are closed')
    done.append('3 photo')
    # (4) [Push] only in state 1477, pushed instance compared with the kind filter
    if rows_of('const ChCheck kPushChecks[] = {') != {'007306d9': '8b0d04e5fa00',
                                                      '008b1c24': 'c5050000c0067300c006730010067300' +
                                                                  '00ac74000000000000000000'}:
        problems.append('TruMenu.cpp: kPushChecks must be the two rows of Befund-S2 section 7a')
    objt = fn_body(src, 'void MdObjTick(')
    if 'if (!MdRecHasState(1477)) continue;' not in objt or 'ReadDword(pbody + 0x148, &pushed)' not in objt or \
            'if (match != kindOk)' not in objt:
        problems.append('TruMenu.cpp: MdObjTick: [Push] only in state 1477, pushed instance logged against the kind filter')
    done.append('4 push 1477')
    # (5) Thor: strict 6 units for areas / state, relaxed only drawn with puzzle.thorloose, obstacles, artifacts from the
    # unit intro list with the measured offset, galleries chained
    tick5 = fn_body(src, 'void ThTick(')
    # 0.22.68 (B2 1) replaced the 150-unit ray cells (strict / relaxed, 552 + 100 obstacle rule) by the terrain-mesh
    # reach of TruThorCore.h - those three rules are checked by check_02268 then; the chaining moved into the core
    b2thor = '#include "TruThorCore.h"' in src
    if not b2thor:
        if tick5.count('f = dz <= 6.0f ? 1 : dz <= 130.0f ? 2 : 0;') != 2 or 'ThObsTick(s, now);' not in tick5:
            problems.append('TruMenu.cpp: ThTick: strict |dz| <= 6 in both probe passes, ThObsTick')
        if 's.inRelaxed' in fn_body(src, 'int ThPillarState('):
            problems.append('TruMenu.cpp: ThPillarState must use the strict cells only')
        if 'stone = ox * ox + oy * oy < 652.0f * 652.0f;' not in fn_body(src, 'void ThFinish('):
            problems.append('TruMenu.cpp: ThFinish must block cells near obstacles (552 + 100)')
    elif 'ThObsTick(s, now);' not in tick5:
        problems.append('TruMenu.cpp: ThTick must run ThObsTick')
    if 'ReadFloats(rec + 0x10, data, 3)' not in fn_body(src, 'void ThOffset(') or \
            'PzNameHas(name, "ma_rw_artifact")' not in fn_body(src, 'void ThArtifacts('):
        problems.append('TruMenu.cpp: artifacts from the unit intro list with the measured data -> live offset')
    join = 'joined = dx * dx + dy * dy < 300.0f * 300.0f && fabsf(pa[2] - pb[2]) < 100.0f;'
    core = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'TruThorCore.h'), encoding='utf-8').read() if b2thor else ''
    if join not in (fn_body(core, 'inline void Classify(') if b2thor else fn_body(src, 'bool ThStart(')):
        problems.append('TruMenu.cpp: ThStart (0.22.68: TruThorCore Classify) must chain open ledges into galleries')
    if '{"puzzle.thorloose", "bool",' not in src or '"puzzle.thorloose"' not in rows_in('kQbChapters'):
        problems.append('TruMenu.cpp: item / bar row puzzle.thorloose missing')
    done.append('5 thor')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8-sig').read()
    if '## 0.22.63' not in readme or 'TO TEST 0.22.63' not in readme:
        problems.append('README.md: section "## 0.22.63" with "TO TEST 0.22.63" missing')
    return problems, 'build S3 (%s)' % ', '.join(done)


def check_02262():
    """0.22.62 (package S1, fix build after the live test 18.11.): (1) kVersion starts with 0.22.62; (a) puzzle.pull:
    vt 59 from off and on ('action' = vt 55 from on only), the lever node in the check after and the "changed nothing"
    line; README section"""
    problems = []
    done = []
    src = read_cpp()
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '"TruMenu 0.22.62 (fix build S1' not in ver and ' - 0.22.62 (fix build S1' not in ver:
        problems.append('TruMenu.cpp: kVersion must start with "TruMenu 0.22.62 (fix build S1 ..."')
    # (a) vt 59 also from on
    run = fn_body(src, 'bool RunPzPull(')
    tick = fn_body(src, 'void PzPullTick(')
    v62 = 'st == 0 ? 59 : st == 1 ? (direct ? 55 : 59) : -1'
    v63 = 'optLever ? 59 : optOff ? 58 : direct ? 55 : st == 0 ? 59 : 58'   # 0.22.63 (S3 1): vt 58 from on
    if not (v62 in run or v63 in run) or 'strstr(arg, " action")' not in run:
        problems.append('TruMenu.cpp: RunPzPull must use vt 59 from off and on, vt 55 only with "action" from on')
    if 'PzTargetState(p.inst, ls, sizeof(ls));' not in tick or 'changed nothing' not in tick:
        problems.append('TruMenu.cpp: PzPullTick must follow the lever node and log "... changed nothing"')
    done.append('a vt 59')
    # (b) two switches instead of the level, Help still read
    header, opt_rows = table(src)
    d = {(s, k): v for s, k, v, _ in opt_rows}
    if (d.get(('Puzzle', 'Hints')), d.get(('Puzzle', 'Actions'))) != ('1', '1') or ('Puzzle', 'Help') in d:
        problems.append('TruMenu.cpp: kOpts [Puzzle] Hints=1 / Actions=1 (no Help row) missing')
    for item, kind in (('puzzle.hints', 'bool'), ('puzzle.actions', 'bool'), ('puzzle.help', 'int')):
        if '{"%s", "%s",' % (item, kind) not in src: problems.append('TruMenu.cpp: item %s missing' % item)
    if 'g_pzHelp' in re.sub(r'//[^\n]*', '', src):
        problems.append('TruMenu.cpp: g_pzHelp is gone (0.22.62) - use g_pzHints / g_pzActions')
    if 'GetPrivateProfileIntA("Puzzle", "Help", -1, ini)' not in src:
        problems.append('TruMenu.cpp: the 0.22.59 key [Puzzle] Help must still be read when Hints / Actions are missing')
    if '"puzzle.hints" : "puzzle.actions"' not in fn_body(src, 'int QbPzRows('):
        problems.append('TruMenu.cpp: QbPzRows must show the two rows Hinweise / Aktionen')
    done.append('b hints / actions')
    # (c) bar rows on their pages, dbg.plates apart from the key items
    def rows_in(table_name):
        at = src.find('const QbRow %s[] = {' % table_name)
        return src[at:src.find('\n};', at)] if at >= 0 else ''
    want_rows = {'kQbLara': ('"fall.box"', '"trace.arcs"'), 'kQbChapters': ('"puzzle.thor"', '"puzzle.thorgap"'),
                 'kQbDebug': ('"obj.track", "list"',), 'kQbLevel': ('"dbg.plates"',)}
    for tname, ids in want_rows.items():
        part = rows_in(tname)
        for i in ids:
            if i not in part: problems.append('TruMenu.cpp: bar row %s missing on %s' % (i, tname))
    if '{"dbg.plates", "bool",' not in src:
        problems.append('TruMenu.cpp: item dbg.plates missing')
    if 'const bool pzKey = g_kiPlates && !keyItem && PiKeyState(' not in fn_body(src, 'void P5KeyDraw('):
        problems.append('TruMenu.cpp: P5KeyDraw must draw plates / weights / holes only with dbg.plates')
    done.append('c bar rows')
    # (d) arc velocity source, (e) site kinds and the held v = 0 calls
    tick = fn_body(src, 'void MdTick(')
    for want in ('if (tgt && tvl > 0.01f) src = 1;', 'else if (since >= 1 && ivl > 0.5f) src = 3;', 'f.vSrc'):
        if want not in tick: problems.append('TruMenu.cpp: MdTick arc velocity source: %s missing' % want)
    note = fn_body(src, 'void MdLaunchNote(')
    if 'ret == 0x00766b4f || ret == 0x0071b519' not in note or 'Log(3, "[Jump] (no jump)' not in note:
        problems.append('TruMenu.cpp: MdLaunchNote must log ground moves / restart at LogLevel 3 only')
    if '(ret == 0x0073f0d3 || ret == 0x0073f2cc)' not in note or 'f.confirm = still;' not in note:
        problems.append('TruMenu.cpp: MdLaunchNote: re-aim only from the aim solver, v = 0 calls held until a flight follows')
    site = fn_body(src, 'const char *MdSite(')
    if 'case 0x0071f6e4: return "pole take-off' not in site or 'case 0x00766b4f:' not in site:
        problems.append('TruMenu.cpp: MdSite must name 0x71f6e4 pole take-off and 0x766b4f / 0x71b519')
    done.append('d arc velocity, e jump sites')
    # (d) dashed preview: byte check of the jump table lookup 0x6f1950, read only (no call), items + bar rows, JpTick
    at = src.find('const ChCheck kJpChecks[] = {')
    part = src[at:src.find('};', at)] if at >= 0 else ''
    rows = {x: h.replace(' ', '') for x, h in re.findall(r'\{0x([0-9a-f]{8}), "([0-9a-f ]+)"\}', part)}
    if rows != {'006f1950': 'a194f0e7008b48508b91e40d0000'}:
        problems.append('TruMenu.cpp: kJpChecks must be the 0x6f1950 row of ENGINE 12 (R11) (got %s)' % rows)
    jp = src[src.find('// ---- 0.22.62 (package S1 d) jump preview'):src.find('// game frame: the detours (once)')]
    jpc = re.sub(r'//[^\n]*', '', jp)
    if not jp or '0x006f1950)(' in jpc or re.search(r'\*reinterpret_cast<volatile [A-Za-z]+ \*>\([^)]*\) =(?!=)', jpc):
        problems.append('TruMenu.cpp: the jump preview section must read only (no call of 0x6f1950, no store)')
    for want in ('ReadDword(t + 0xb00, &ids[0]);', 'ReadDword(t + 0xc90, &ids[1]);', 'ReadDword(pb + 0xde4, &cnt)',
                 'const float lx = r.a[0], ly = -r.a[1], lz = r.a[2]', 'd2 > 300.0f * 300.0f'):
        if want not in jpc: problems.append('TruMenu.cpp: jump preview: %s missing' % want)
    for item in ('jump.preview', 'jump.catch'):
        if '{"%s", "bool",' % item not in src: problems.append('TruMenu.cpp: item %s missing' % item)
        if '"%s"' % item not in rows_in('kQbLara'): problems.append('TruMenu.cpp: bar row %s missing on kQbLara' % item)
    if 'JpTick(player, lara, now);' not in tick:
        problems.append('TruMenu.cpp: MdTick must run JpTick')
    done.append('d preview')
    # (f) fading throw path, [Push] gate, one multibody once
    if 'g_mdTrailRest' not in fn_body(src, 'void MdDrawArcs(') or 'age >= 3000' not in fn_body(src, 'void MdDrawArcs('):
        problems.append('TruMenu.cpp: MdDrawArcs must fade the throw path out 3 s after the rest')
    objt = fn_body(src, 'void MdObjTick(')
    if 'MdPushable(o.inst)' not in objt or 'MdLaraAir()' not in objt or 'if (!o.dup) MdObjLine("Push", "end", o);' not in objt:
        problems.append('TruMenu.cpp: MdObjTick: [Push] only for pushable objects, Lara on the ground, multibody once')
    done.append('f paths / push')
    # (g) Figur aufs Ziel: pulls only through RunPzPull, waits for the figure, stops when locked
    ptt = fn_body(src, 'void PzPullToTick(')
    if 'RunPzPull(arg, out, sizeof(out))' not in ptt or 'tlobj::D(lb + 0x80) != 0' not in ptt or 'st == 2' not in ptt:
        problems.append('TruMenu.cpp: PzPullToTick must pull through RunPzPull, wait for the figure, stop when locked')
    if re.search(r'0x0057b380|0x00575fb0', re.sub(r'//[^\n]*', '', ptt + fn_body(src, 'bool RunPzTo('))):
        problems.append('TruMenu.cpp: puzzle.pullto must not call the script path itself (only puzzle.pull)')
    if '{"puzzle.pullto", "action",' not in src or 'PzPullToTick();' not in fn_body(src, 'void PzGameTick('):
        problems.append('TruMenu.cpp: item puzzle.pullto / PzPullToTick in PzGameTick missing')
    done.append('g figure to target')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8-sig').read()
    if '## 0.22.62' not in readme or 'TO TEST 0.22.62' not in readme:
        problems.append('README.md: section "## 0.22.62" with "TO TEST 0.22.62" missing')
    return problems, 'fix build S1 (%s)' % ', '.join(done)


def check_02261():
    """0.22.61 (package R1c point 1): (1) kVersion starts with 0.22.61; (2) [Puzzle] ThorGap=600; (3) the Thor section
    holds no game id and no position constant (everything from the loaded objects / markup / floor query); (4) it writes
    nothing into the game (no reinterpret_cast store) and queries the floor only through MdProbe; (5) items puzzle.thor /
    puzzle.thorgap; ThTick in PadHook; (6) README section"""
    problems = []
    src = read_cpp()
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '"TruMenu 0.22.61 (Thor pillar areas, package R1c' not in ver and ' - 0.22.61 (Thor pillar areas' not in ver:
        problems.append('TruMenu.cpp: kVersion must start with "TruMenu 0.22.61 (Thor pillar areas, package R1c ..."')
    header, opt_rows = table(src)
    d = {(s, k): v for s, k, v, _ in opt_rows}
    if d.get(('Puzzle', 'ThorGap')) != '600':
        problems.append('TruMenu.cpp: kOpts [Puzzle] ThorGap=600 missing')
    a = src.find('// ---- 0.22.61 (package R1c point 1) Thor pillar floor areas')
    b = src.find('// ---- state log + switch learning', a)
    sec = re.sub(r'//[^\n]*', '', src[a:b]) if a >= 0 and b > a else ''
    if not sec:
        problems.append('TruMenu.cpp: section "Thor pillar floor areas" missing')
    else:
        if re.search(r'\b(46[0-9]{2}|9[0-9]{3})\b', sec) or re.search(r'-?\b1[0-3][0-9]{3}\.[0-9]', sec):
            problems.append('TruMenu.cpp: the Thor section holds a game id or a position constant')
        if re.search(r'\*reinterpret_cast<volatile [A-Za-z]+ \*>\([^)]*\) =(?!=)', sec) or '0x00493330' in sec:
            problems.append('TruMenu.cpp: the Thor section must not write game memory or call the query directly')
    for item, kind in (('puzzle.thor', 'bool'), ('puzzle.thorgap', 'int'), ('puzzle.insert', 'action'), ('obj.msg', 'action')):
        if '{"%s", "%s",' % (item, kind) not in src: problems.append('TruMenu.cpp: item %s missing' % item)
    # (R1c 2) the insert: the two byte checks of the game's 0x165 sends, 0x5b3750 called only from InsTick / RunObjMsg
    at = src.find('const ChCheck kInsChecks[] = {')
    part = src[at:src.find('};', at)] if at >= 0 else ''
    rows = {x: h.replace(' ', '') for x, h in re.findall(r'\{0x([0-9a-f]{8}), "([0-9a-f ]+)"\}', part)}
    if rows != {'007179db': '8b915808000085d27419576865010000' + '52e85fbde9ff', '00717a5a': '686501000056e8ebbce9ff'}:
        problems.append('TruMenu.cpp: kInsChecks must be the two 0x165 call sites (got %s)' % rows)
    code = re.sub(r'//[^\n]*', '', src)
    if code.count('reinterpret_cast<InsPostFn>(0x005b3750)') != 2:
        problems.append('TruMenu.cpp: 0x5b3750 only from InsTick and RunObjMsg')
    if 'ThTick();' not in fn_body(src, 'DWORD WINAPI PadHook('):
        problems.append('TruMenu.cpp: PadHook must run ThTick once per game frame')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8-sig').read()
    if '## 0.22.61' not in readme or 'TO TEST 0.22.61' not in readme:
        problems.append('README.md: section "## 0.22.61" with "TO TEST 0.22.61" missing')
    return problems, 'Thor pillar areas (run time, ThorGap %s)' % d.get(('Puzzle', 'ThorGap'))


def check_02260():
    """0.22.60 (package R1b): (1) kVersion starts with 0.22.60; (2) kMdChecks = the 6 rows (launch 0x70e050, drop
    0x70e100, the aimed jump's call 0x73f0ce, segment query 0x493330 / 0x49333d, g at 0x85e2b0); (3) the two hooks call
    the original once each and write nothing into the game; (4) the segment query only from MdProbe with mask
    0x2c19e7; (5) items trace.arcs / obj.track; MdTick in PadHook's frame block; (6) README section"""
    problems = []
    src = read_cpp()
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '"TruMenu 0.22.60 (motion data, package R1b' not in ver and ' - 0.22.60 (motion data' not in ver:
        problems.append('TruMenu.cpp: kVersion must start with "TruMenu 0.22.60 (motion data, package R1b ..."')
    at = src.find('const ChCheck kMdChecks[] = {')
    part = src[at:src.find('};', at)] if at >= 0 else ''
    rows = {a: h.replace(' ', '') for a, h in re.findall(r'\{0x([0-9a-f]{8}), "([0-9a-f ]+)"\}', part)}
    want = {'0070e050': '558bec83e4f083ec10f30f10051c118400', '0070e100': '558bec83e4f083ec108b4d08',
            '0073f0ce': 'e87deffcff', '00493330': '558bec83e4f081ec9400000053', '0049333d': '8b5d08f7c300400000',
            '0085e2b0': '882eb7c0'}
    if rows != want:
        problems.append('TruMenu.cpp: kMdChecks must be the 6 rows of ENGINE 12 (R2b) (got %s)' % rows)
    for name, orig in (('void __cdecl MdLaunchHook(', 'g_mdLaunch(inst, g, vx, vy, vz);'),
                       ('void __cdecl MdDropHook(', 'g_mdDrop(inst, g);')):
        body = re.sub(r'//[^\n]*', '', fn_body(src, name))
        if body.count(orig) != 1 or re.search(r'\*reinterpret_cast<volatile [A-Za-z]+ \*>\([^)]*\) =(?!=)', body):
            problems.append('TruMenu.cpp: %s must call the original once and write nothing' % name)
    code = re.sub(r'//[^\n]*', '', src)
    if code.count('reinterpret_cast<MdProbeFn>(0x00493330)') != 1 or '0x002c19e7' not in fn_body(src, 'bool MdProbe('):
        problems.append('TruMenu.cpp: 0x493330 only from MdProbe with mask 0x2c19e7')
    for item, kind in (('trace.arcs', 'bool'), ('obj.track', 'action')):
        if '{"%s", "%s",' % (item, kind) not in src: problems.append('TruMenu.cpp: item %s missing' % item)
    if 'MdTick();' not in fn_body(src, 'DWORD WINAPI PadHook('):
        problems.append('TruMenu.cpp: PadHook must run MdTick once per game frame')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8-sig').read()
    if '## 0.22.60' not in readme or 'TO TEST 0.22.60' not in readme:
        problems.append('README.md: section "## 0.22.60" with "TO TEST 0.22.60" missing')
    return problems, 'motion data (%d byte checks; [Jump] / [Throw] / [Push] / [Track], arcs, ground probe)' % len(rows)


def check_02259():
    """0.22.59 (package R1): (1) kVersion starts with 0.22.59; (2) the byte checks kPullChecks (3 rows: 0x575fb0 vtable
    lookup, 0x57b380 call, the exe's own use 0x796ea3) and kFlChecks (4 rows: 0x75d080 + its three callers, package R2);
    (3) puzzle.pull calls only through 0x575fb0 / 0x57b380 with vt 59 / 55 after the chain check (SpVtEntries) and
    refuses disabled / used switches; (4) the landing hook only reads (no write into the tracker / machine) and calls the
    original once; (5) KeepLoad arms the same-group intro marks (ImArm(unit, what, true)); (6) up to kPzHoldMax holds
    (g_pzHolds / g_pzKeeps), PzCounterOf opens a closed gate only with one opening record; (7) [Puzzle] Help=2 and
    HintFile; the hint file is read from next to tru.exe, no hint text with game ids in the source; (8) items
    puzzle.pull / puzzle.help; (9) README section"""
    problems = []
    src = read_cpp()
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '"TruMenu 0.22.59 (puzzles + landing log, package R1' not in ver and ' - 0.22.59 (puzzles + landing log' not in ver:
        problems.append('TruMenu.cpp: kVersion must start with "TruMenu 0.22.59 (puzzles + landing log, package R1 ..."')

    def rows_of(start):
        at = src.find(start)
        part = src[at:src.find('};', at)] if at >= 0 else ''
        return {a: h.replace(' ', '') for a, h in re.findall(r'\{0x([0-9a-f]{8}), "([0-9a-f ]+)"\}', part)}
    pull = rows_of('const ChCheck kPullChecks[] = {')
    want_pull = {'00575fb0': '8b41088b48088b51448b4424088b04820fb7108b4c24043bca7d078b448804c20800',
                 '0057b380': '5556 8b74240c85f68be90f8421010000837d0c000f8417010000 53bb01000000845e04741e'.replace(' ', ''),
                 '00796ea3': '8b157cb505016a006a006a000fb6c05250e8f7f0ddff8b0e50e8bf44deff'}
    if pull != want_pull:
        problems.append('TruMenu.cpp: kPullChecks must be the 3 rows of ENGINE 9 "Native call of a script function" (got %s)' % pull)
    fl = rows_of('const ChCheck kFlChecks[] = {')
    want_fl = {'0075d080': '83ec088b4c240cd9e8', '0075d275': 'e806feffff', '0075d2d6': 'e8a5fdffff', '0075d301': 'e87afdffff'}
    if fl != want_fl:
        problems.append('TruMenu.cpp: kFlChecks must be the 4 rows of the R2 spec (got %s)' % fl)
    tick = fn_body(src, 'void PzPullTick(')
    if tick.count('reinterpret_cast<SpCallFn>(0x0057b380)') != 1 or tick.count('reinterpret_cast<SpFindFn>(0x00575fb0)') != 1:
        problems.append('TruMenu.cpp: PzPullTick must call 0x575fb0 and 0x57b380 once each')
    if 'known = cand[i] == entry' not in tick:
        problems.append('TruMenu.cpp: PzPullTick must check the vtable entry against the chain functions first')
    run = fn_body(src, 'bool RunPzPull(')
    vts = ('st == 0 ? 59 : st == 1 ? 55 : -1', 'st == 0 ? 59 : st == 1 ? (direct ? 55 : 59) : -1',   # 0.22.62: vt 59 from on
           'optLever ? 59 : optOff ? 58 : direct ? 55 : st == 0 ? 59 : 58')                        # 0.22.63: vt 58 from on
    if not any(v in run for v in vts) or 'if (st == 2) {' not in run or 'PzSwUsed(inst) && !reusable' not in run:
        problems.append('TruMenu.cpp: RunPzPull must use vt 59 (off) / 55 (on) and refuse disabled / used switches')
    hook = re.sub(r'//[^\n]*', '', fn_body(src, 'void __cdecl FlHook('))
    if hook.count('g_flOrig(m);') != 1 or re.search(r'\*reinterpret_cast<volatile [A-Za-z]+ \*>\([^)]*\) =(?!=)', hook):
        problems.append('TruMenu.cpp: FlHook must call the original once and write nothing')
    if 'ImArm(unit, what, true);' not in fn_body(src, 'bool KeepLoad('):
        problems.append('TruMenu.cpp: KeepLoad must keep the same-group intro marks at 1 for mid-chapter units')
    if 'tlact::DriveCtl g_pzHolds[kPzHoldMax]' not in src or 'PzKeep g_pzKeeps[kPzHoldMax]' not in src:
        problems.append('TruMenu.cpp: several holds (g_pzHolds / g_pzKeeps) missing')
    if 'if (cands != 1) return 0;' not in fn_body(src, 'int PzCounterOf('):
        problems.append('TruMenu.cpp: PzCounterOf opens a closed gate only with exactly one opening record')
    header, opt_rows = table(src)
    d = {(s, k): v for s, k, v, _ in opt_rows}
    helped = d.get(('Puzzle', 'Help')) == '2' or (d.get(('Puzzle', 'Hints')), d.get(('Puzzle', 'Actions'))) == ('1', '1')
    if not helped or d.get(('Puzzle', 'HintFile')) != 'TruMenu.puzzlehints.txt':   # 0.22.62: Help -> Hints + Actions
        problems.append('TruMenu.cpp: kOpts [Puzzle] Help=2 / HintFile=TruMenu.puzzlehints.txt missing')
    info = src[src.find('// ---- 0.22.59 puzzle info'):src.find('// ---- 0.22.59 (R1 point 7) landing log line')]
    if not info or re.search(r'\b(48[0-9]{2}|45[0-9]{2}|46[0-9]{2}|47[0-9]{2})\b', re.sub(r'//[^\n]*', '', info)):
        problems.append('TruMenu.cpp: the puzzle info section is missing or holds a game id (hints come from the objects)')
    for item, kind in (('puzzle.pull', 'action'), ('puzzle.help', 'int'), ('fall.box', 'bool')):
        if '{"%s", "%s",' % (item, kind) not in src: problems.append('TruMenu.cpp: item %s missing' % item)
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8-sig').read()
    if '## 0.22.59' not in readme or 'TO TEST 0.22.59' not in readme:
        problems.append('README.md: section "## 0.22.59" with "TO TEST 0.22.59" missing')
    return problems, 'puzzles + landing log (pull %d byte checks, landing %d byte checks, several holds, open first, help ' \
                     'levels, intro marks mid-chapter)' % (len(pull), len(fl))


def check_02256():
    """0.22.56 (package P2b): (1) kVersion starts with 0.22.56; (2) the note exports TruMenuNote / TruMenuNoteClear /
    TruMenuNoteList as in src/asi/TruLink/README.md (64 notes, 95 characters, flags 1 / 2), drawn in DvDrawNames and by
    NtDrawLoose, cleared at main state 2; (3) P3 fix 1: kChChecks (6 rows = ENGINE section 22), ChArm at the three level
    requests (LoadUnit, LevelStartInGame, the mission start), ChTick in Render and PadHook, the two words written only
    while the main state is 2, no call of 0x5f2440; (4) P3 fix 2: ChapSteps in a level = "level.start <unit> 0" for every
    other unit, chapter.keep row (choice kQvChapKeep, level.load); (5) the puzzle section from TruLinkObj.h /
    TruLinkAct.h - no joint limit setter, no set-node message, the three items, PzGameTick in the PadHook frame block;
    no game ids in the puzzle code; (6) README"""
    problems = []
    src = read_cpp()
    code = re.sub(r'//[^\n]*', '', src)
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '"TruMenu 0.22.56 (puzzle helpers' not in ver and '0.22.56 (puzzle helpers' not in ver:   # 0.22.57: later head
        problems.append('TruMenu.cpp: kVersion must start with "TruMenu 0.22.56 (puzzle helpers ..." (or name it later)')
    for want in ('#include "../TruLink/TruLinkObj.h"', '#include "../TruLink/TruLinkAct.h"'):
        if want not in src: problems.append('TruMenu.cpp: %s missing' % want)
    # ---- (2) notes
    for want in ('extern "C" __declspec(dllexport) int __cdecl TruMenuNote(unsigned intro, const char *text, unsigned flags)',
                 'extern "C" __declspec(dllexport) int __cdecl TruMenuNoteClear(unsigned intro)',
                 'extern "C" __declspec(dllexport) int __cdecl TruMenuNoteList(char *out, int size)',
                 'const int kNtMax = 64;', 'if (!len || len > 95) return -1;', 'if (!intro || intro == 0xffffffffu || !text || (flags & ~3u)) return -1;'):
        if want not in src: problems.append('TruMenu.cpp: notes: %s missing' % want)
    if 'NtGet(static_cast<unsigned>(intro), noteText' not in fn_body(src, 'void DvDrawNames('):
        problems.append('TruMenu.cpp: DvDrawNames must append the note line')
    if 'NtDrawLoose(dl, c,' not in fn_body(src, 'void DrawDebugView('):
        problems.append('TruMenu.cpp: DrawDebugView must draw the loose notes (flag bit 0)')
    if 'if (g_ntNotes[i].flags & 2)' not in fn_body(src, 'void NtLevelLoad('):
        problems.append('TruMenu.cpp: NtLevelLoad must keep the notes with flag bit 1')
    # ---- (3) camera hints
    rows = re.findall(r'\{0x([0-9a-f]{8}), "([0-9a-f ]+)"\}', src[src.find('const ChCheck kChChecks[] = {'):
                                                            src.find('const DWORD kChMgr = ')])
    want_rows = {'005edf61': '898e0c010000', '005edf79': '898e10010000', '005e8490': '8b810c010000c3',
                 '005e84c0': '8b8110010000c3', '00722497': 'e8a47becffe89fffecff'}
    got = {a: h.replace(' ', '') for a, h in rows}
    if len(rows) != 6 or any(got.get(a) != h for a, h in want_rows.items()):
        problems.append('TruMenu.cpp: kChChecks must hold the 6 rows of ENGINE section 22 (got %d)' % len(rows))
    for fn, want in (('bool LoadUnit(', 'ChArm("level.load");'), ('bool LevelStartInGame(', 'ChArm("the in-level level start");'),
                     ('bool RunLevelStart(', 'ChArm("the mission start");'), ('void Render(', 'ChTick();'),
                     ('DWORD WINAPI PadHook(', 'ChTick();')):
        if want not in fn_body(src, fn): problems.append('TruMenu.cpp: %s lacks %s' % (fn, want))
    ct = fn_body(src, 'void ChTick(')
    if not 0 <= ct.find('if (state == 2) {') < ct.find('*reinterpret_cast<volatile DWORD *>(kChMgr + 0x110) = 0;'):
        problems.append('TruMenu.cpp: ChTick must write the hint words only in main state 2')
    if '0x5f2440' in re.sub(r'//[^\n]*|"[^"\n]*"', '', ct) or 'GetTickCount() - g_chArmTick > 30000' not in ct:
        problems.append('TruMenu.cpp: ChTick: no call of 0x5f2440, 30 s timeout')
    # ---- (4) chapters
    cs = fn_body(src, 'bool ChapSteps(')
    if 'Out(steps, n, "save.backup kapitel;level.start %s 0", unit);' not in cs or '!ChOk()' not in cs:
        problems.append('TruMenu.cpp: ChapSteps: other units in a level = level.start <unit> 0 (camera-hint checks)')
    if '{"Kapitel (Stand behalten)", "Chapter (keep state)", "chapter.keep", "", kQbChoice, -1, kQcNone, kQvChapKeep,' not in src:
        problems.append('TruMenu.cpp: kQbChapters: choice row "Kapitel (Stand behalten)" (chapter.keep) missing')
    keep = fn_body(src, 'bool RunChapKeep(')   # 0.22.58 (S2): level.keep = level.load + the intro mark step
    if 'Out(steps, sizeof(steps), "save.backup kapitel;level.load %s", unit);' not in keep and \
            'Out(steps, sizeof(steps), "save.backup kapitel;level.keep %s", unit);' not in keep:
        problems.append('TruMenu.cpp: RunChapKeep must load with level.load / level.keep after the backup')
    # ---- (5) puzzles
    pz = src[src.find('// ---- 0.22.56 puzzles nearby'):src.find('// ---- end of 0.22.56 puzzles nearby')]
    pzc = re.sub(r'//[^\n]*', '', pz)
    if not pz: problems.append('TruMenu.cpp: section "0.22.56 puzzles nearby" missing')
    for bad in ('kJtSetLimits', 'JtLimitsFn', 'kUberMsg', '0x4d7680', 'kJtLimitOn'):
        if bad in pzc: problems.append('TruMenu.cpp: the puzzle section must not use %s (no limits, no set node)' % bad)
    for want in ('tlact::CmdExec(x, g_pzFig.cmd[q])', 'tlact::DriveBegin(g_pzHold, d);', 'tlact::PlaceBody(inst, target, nullptr)',
                 'd.holdOff = true;', 'tlobj::RunChecks(g_tlGrp'):
        if want == 'tlact::DriveBegin(g_pzHold, d);' and 'tlact::DriveBegin(*slot, d);' in pzc:
            continue                          # 0.22.59: one drive per hold slot (g_pzHolds)
        if want not in pzc: problems.append('TruMenu.cpp: puzzle section lacks %s' % want)
    if re.search(r'\b(48[0-9]{2}|45[0-9]{2}|46[0-9]{2})\b', pzc):
        problems.append('TruMenu.cpp: no intro ids in the puzzle code (hints come from the loaded instances)')
    for item in ('puzzle.figures', 'puzzle.hold', 'puzzle.bring', 'chapter.keep'):
        if '{"%s", "action",' % item not in src: problems.append('TruMenu.cpp: item %s missing' % item)
    if 'PzGameTick();' not in fn_body(src, 'DWORD WINAPI PadHook('):
        problems.append('TruMenu.cpp: PadHook must run PzGameTick once per game frame')
    if '"joint.set", q.arg' in fn_body(src, 'void QbPzAct('):
        problems.append('TruMenu.cpp: QbPzAct must not run the old joint.set solve')
    readme = open(os.path.join(ROOT, 'src', 'asi', 'TruMenu', 'README.md'), encoding='utf-8-sig').read()
    if '## 0.22.56' not in readme or 'TO TEST 0.22.56' not in readme:
        problems.append('README.md: section "## 0.22.56" with "TO TEST 0.22.56" missing')
    return problems, 'notes (3 exports), camera hints (6 byte checks), chapter rows in a level, chapter.keep, puzzle section'


def check_02227(ini_path, switches_path):
    """0.22.27 (Q79, save / checkpoint probe; workspace docs/Befund-Speicher-Probe-Q79-1111.md, P1 of Q72): the items
    save.pending / save.inv / save.waiting / save.find (actions, TruLink thread, read only) in TruSaveProbe.h, included
    once inside TruMenu.cpp before the item table; the byte checks = work/asi/menu0250/precheck_02227_sv.txt (kSvChecks 32
    + kSvHookChecks 5 + the two prologues), each at most 64 bytes, SvReady -> SvCheck before any read; read only: no
    write helper, no VirtualProtect, no game function call except the game's memcpy 0x8148a0 inside SvSaveCopy /
    SvRestoreCopy (the [Log] Save call patches, M21PatchGroup only after g_svHookOk, the frame offsets of the two copy
    calls); [Log] Save default 0 (kOpts, TruMenu.ini, ReadOptions, live SvReadSwitch), SvTick in PadHook's per-frame block
    after FallWatchTick, SvCheck in Start after FwCheck; one switch row TruMenu | Log | Save (live, 0); precheck_02227 =
    the 58 rows of precheck_02226 + these 39; Set-TruMenu.ps1 knows the 0.22.26 hash"""
    problems = []
    src = read_cpp()
    if '"0.22.27 (save probe, Q79' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.28: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.27 part "0.22.27 (save probe, Q79"')
    inc = '#include "TruSaveProbe.h"'
    if src.count(inc) != 1 or not 0 < src.find(inc) < src.find('struct Item {') or src.find(inc) < src.find('namespace {'):
        problems.append('TruMenu.cpp: TruSaveProbe.h must be included once inside the namespace, before struct Item')
    if not os.path.exists(SV_HEADER): return problems + ['TruSaveProbe.h missing'], 'save probe: header missing'
    hdr = open(SV_HEADER, encoding='utf-8').read()
    reads, hooks = sv_rows(hdr, 'kSvChecks'), sv_rows(hdr, 'kSvHookChecks')
    pre_sv = os.path.join(ROOT, 'work', 'asi', 'menu0250', 'precheck_02227_sv.txt')
    pre26 = os.path.join(ROOT, 'work', 'asi', 'menu0249', 'precheck_02226.txt')
    pre27 = os.path.join(ROOT, 'work', 'asi', 'menu0250', 'precheck_02227.txt')
    prows = lambda p: sorted(l.split(None, 1)[0].lower() + ' ' + l.split(None, 1)[1].replace(' ', '').lower()
                             for l in open(p, encoding='utf-8').read().splitlines() if l.strip() and not l.startswith('#'))
    mine = sorted('%s %s' % r for r in reads + hooks + [('005570f0', '807c240400'), ('00557130', '83ec1c')])
    if len(reads) != 32 or len(hooks) != 5: problems.append('TruSaveProbe.h: kSvChecks 32 / kSvHookChecks 5 rows wanted '
                                                            '(%d / %d)' % (len(reads), len(hooks)))
    if any(len(h) > 128 for a, h in reads + hooks): problems.append('TruSaveProbe.h: a byte check longer than 64 bytes')
    if os.path.exists(pre_sv) and prows(pre_sv) != mine:
        problems.append('precheck_02227_sv.txt: must be the 39 rows of TruSaveProbe.h')
    if os.path.exists(pre26) and os.path.exists(pre27) and sorted(prows(pre26) + mine) != prows(pre27):
        problems.append('precheck_02227.txt: must hold the rows of precheck_02226 + the 39 save probe rows')
    for want in ('HexBytesAt(0x005570f0, "807c240400")', 'HexBytesAt(0x00557130, "83ec1c")', 'j1 == 0xe9', 'j2 == 0xe9'):
        if want not in fn_body(hdr, 'bool SvCheck('): problems.append('TruSaveProbe.h: SvCheck must hold %s' % want)
    for bad in ('WriteDword(', 'WriteBytes(', 'VirtualProtect', 'CallFn', 'GiveObject'):
        if bad in hdr: problems.append('TruSaveProbe.h: %s found - the probe is read only' % bad)
    if hdr.count('reinterpret_cast<SvCopyFn>(kSvCopy)(d, s, n)') != 2 or 'kSvCopy = 0x008148a0' not in hdr:
        problems.append('TruSaveProbe.h: the game memcpy 0x8148a0 must be called exactly twice (SvSaveCopy / SvRestoreCopy)')
    for fn, want in (('void *__cdecl SvSaveCopy(', 'SvOnSave(frame[4], static_cast<BYTE>(frame[5] & 0xff));'),
                     ('void *__cdecl SvRestoreCopy(', 'SvOnRestore(frame[17], frame[18], before);')):
        body = fn_body(hdr, fn)
        if want not in body or 'reinterpret_cast<SvCopyFn>(kSvCopy)(d, s, n)' not in body or '__try' not in body:
            problems.append('TruSaveProbe.h: %s must call the copy and then %s inside __try' % (fn.split()[-1], want))
    if '{0x00557127, kSvCopy, true,' not in hdr or '{0x005571a3, kSvCopy, true,' not in hdr:
        problems.append('TruSaveProbe.h: g_svPatches must be the two copy calls 0x557127 / 0x5571a3')
    tick = fn_body(hdr, 'void SvTick(')
    order = ['SvReadSwitch();', 'if (want == g_svPatchOn) return;', 'SvCheck();', 'if (want && !g_svHookOk) {',
             'M21PatchGroup(g_svPatches, 2, want,']
    at = [tick.find(x) for x in order]
    if any(a < 0 for a in at) or at != sorted(at):
        problems.append('TruSaveProbe.h: SvTick must read the switch, return while unchanged, check, refuse, then patch')
    if 'GetPrivateProfileIntA("Log", "Save"' not in fn_body(hdr, 'void SvReadSwitch('):
        problems.append('TruSaveProbe.h: SvReadSwitch must read [Log] Save')
    if 'if (!SvCheck())' not in fn_body(hdr, 'bool SvReady('):
        problems.append('TruSaveProbe.h: SvReady must run SvCheck first')
    for fn in ('bool RunSvPending(', 'bool RunSvInv(', 'bool RunSvWaiting(', 'bool RunSvFind('):
        body = fn_body(hdr, fn)
        lines = body.split('\n')               # fn_body starts with the newline before the head line
        if len(lines) < 3 or 'if (!SvReady(o, n)) return false;' not in lines[2]:
            problems.append('TruSaveProbe.h: %s must start with SvReady' % fn.strip('('))
    items = item_types(src)
    for item in SV_ITEMS:
        m = re.search(r'\{"%s", "action", (?:"[^"]*"\s*)+, (true|false),' % re.escape(item), src)
        if items.get(item) != 'action' or not m or m.group(1) != 'false':
            problems.append('TruMenu.cpp: item %s must be an action on the TruLink thread (gameThread false)' % item)
    block = src[src.find('        FallWatchTick();'):][:300]
    if not re.search(r'\n        SvTick\(\);', block):     # a call statement, not a comment
        problems.append('TruMenu.cpp: SvTick must run in the per-frame block after FallWatchTick')
    if 'void SvTick();' not in src[:src.find('DWORD WINAPI PadHook(')]:
        problems.append('TruMenu.cpp: SvTick must be declared before PadHook')
    start = fn_body(src, 'void Start(')
    fw, sv = re.search(r'\n    FwCheck\(\);', start), re.search(r'\n    SvCheck\(\);', start)
    if not fw or not sv or fw.start() > sv.start():
        problems.append('TruMenu.cpp: Start must run SvCheck after FwCheck')
    if 'InterlockedExchange(&g_svLogOn, OptInt(ini, "Log", "Save") != 0 ? 1 : 0);' not in fn_body(src, 'void ReadOptions('):
        problems.append('TruMenu.cpp: ReadOptions must read [Log] Save')
    if not any(k == 'Save' and v == '0' for line, k, v in ini_section(ini_path, 'Log')):
        problems.append('%s: [Log] Save=0 missing' % os.path.basename(ini_path))
    sw = [l for l in open(switches_path, encoding='utf-8').read().splitlines() if l.startswith('TruMenu | Log | Save ')]
    if len(sw) != 1 or not sw[0].startswith('TruMenu | Log | Save | bool | ') or ' | live | 0 | ' not in sw[0]:
        problems.append('%s: one row TruMenu | Log | Save | bool | ... | live | 0 | ... wanted' %
                        os.path.basename(switches_path))
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if '99c948b48082fc1f4cb58c89922454b64f609354ca602bdf2d8f9695d2ddfb1e' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.26 build hash (work\\asi\\menu0249) is missing')
    return problems, ('save probe: %d items read only on the TruLink thread, kSvChecks %d + kSvHookChecks %d + 2 prologues '
                      '= precheck_02227_sv, memcpy 0x8148a0 only in the 2 copy hooks, [Log] Save default 0 live, switch '
                      'row' % (len(SV_ITEMS), len(reads), len(hooks)))


TP_PACKAGES = ('a', '1', '2', '3', '4', '5', '6', '7', '8', '9')   # docs/Testpakete-1111.md, package 0 = install only
TP_KINDS = ('kQbCheck', 'kQbSwitch', 'kQbNote')


def check_02228(ini_path, switches_path):
    """0.22.28 (Q90, test packages of docs/Testpakete-1111.md on page Tests; workspace docs/Befund-Testseiten-Q90-1111.md):
    the block "TP Q90" at the top of kQbTests - every row parsed by qb_rows (no row the other checks cannot see) and
    flagged kQfTp, no kQfTp row anywhere else; group tp_q90 (level 0) with one kQfSub group per package A, 1 .. 9 (no
    package 0), each in kQbStartClosed, each with a hint (kQbNote) and at least one check (kQbCheck); checks = test.mark
    with a unique id tp<package>.<name> of their own package; switch rows = sw.set with a key of TruMenu.switches.txt; note
    rows id "-" without argument; labels fit the bar row (QbView name 112 bytes); the three kinds handled in QbViewOf /
    QbActRow / QbExecRow / QbHelpLine / PageQbRow, no favourites, the TO TEST list on the bar skips the tp ids, a check
    joins the TO TEST list through RunTestAdd only when it is not listed and is marked through TestMark; the start-up row
    count skips the notes; no new INI key (258); Set-TruMenu.ps1 knows the 0.22.27 hash"""
    problems = []
    src = read_cpp()
    if '"0.22.28 (test packages, Q90' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.29: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.28 part "0.22.28 (test packages, Q90"')
    tests = src[src.find('const QbRow kQbTests[] = {'):]
    tests = tests[:tests.find('\n};')]
    a, b = tests.find('// ---- TP Q90 begin'), tests.find('// ---- TP Q90 end')
    if a < 0 or b < a: return problems + ['TruMenu.cpp: kQbTests lacks the block "TP Q90 begin" .. "TP Q90 end"'], 'TP: no block'
    block = tests[a:b]
    # 0.22.44 (W2): the block is archived - inside the group ts_archive (after ts_teleport), tp_q90 a sub-group there;
    # before: the block stood first, before ts_teleport, tp_q90 on level 0
    arch = tests.find('"ts_archive", kQbGroup')
    if not 0 <= tests.find('"ts_teleport", kQbGroup') < arch < a:
        problems.append('TruMenu.cpp: the TP block must stand inside the group ts_archive (after ts_teleport)')
    raw = re.findall(r'\n    \{"', block)
    rows = [r for r in qb_rows(src, True) if r[0] == 'kQbTests' and 'kQfTp' in r[6]]
    if len(rows) != len(raw):
        problems.append('TruMenu.cpp: TP block has %d rows, qb_rows parses %d with kQfTp (a row split where the table '
                        'parser cannot read it, or a row without kQfTp)' % (len(raw), len(rows)))
    flags = len(re.findall(r'kQfTp\}', src))
    if flags != len(raw) or re.findall(r'kQfTp\}', tests[:a] + tests[b:]):
        problems.append('TruMenu.cpp: kQfTp only on the rows of the TP block (%d flags, %d rows)' % (flags, len(raw)))
    starts = LIT.findall(src[src.find('const char *const kQbStartClosed[] = {'):].split('};')[0])
    sw_keys = set()
    for line in open(switches_path, encoding='utf-8').read().splitlines():
        f = [x.strip() for x in line.split('|')]
        if line.startswith('#') or len(f) < 9 or f[0] == 'group': continue
        sw_keys.add('%s:%s:%s' % (f[0], f[1], f[2]))
    pkg, seen, ids = None, {}, set()
    for t, de, item, arg, kind, layer, tail in rows:
        where = 'TruMenu.cpp: TP row "%s" (%s %s)' % (de, item, arg)
        de_en = re.search(r'\{"%s", "([^"]*)", "%s"' % (re.escape(de), re.escape(item)), block)
        for text in (de, de_en.group(1) if de_en else ''):
            if len(text.encode('utf-8')) > 100: problems.append(where + ': label longer than 100 bytes')
        if kind == 'kQbGroup':
            if arg == 'tp_q90':   # 0.22.44: a sub-group of ts_archive (was level 0)
                if 'kQfSub' not in tail or pkg is not None: problems.append(where + ': tp_q90 = the first row, kQfSub')
                pkg = ''
                continue
            m = re.fullmatch(r'tp_([a-z0-9])', arg)
            if not m or 'kQfSub' not in tail: problems.append(where + ': a package group tp_<package> with kQfSub')
            elif arg not in starts: problems.append(where + ': %s missing in kQbStartClosed' % arg)
            pkg = m.group(1) if m else '?'
            seen[pkg] = {'note': 0, 'check': 0}
            continue
        if pkg is None: problems.append(where + ': before the group tp_q90')
        if kind == 'kQbNote':
            if item != '-' or arg: problems.append(where + ': a note row has id "-" and no argument')
            if pkg in seen: seen[pkg]['note'] += 1
        elif kind == 'kQbCheck':
            if item != 'test.mark' or not re.fullmatch(r'tp[A1-9]\.[a-z0-9]+', arg) or len(arg) > 63:
                problems.append(where + ': a check row is test.mark tp<package>.<name>')
            elif arg[2].lower() != pkg: problems.append(where + ': check id of another package (group tp_%s)' % pkg)
            if arg in ids: problems.append(where + ': check id twice')
            ids.add(arg)
            if pkg in seen: seen[pkg]['check'] += 1
        elif kind == 'kQbSwitch':
            if item != 'sw.set' or arg not in sw_keys:
                problems.append(where + ': a switch row is sw.set <Plugin>:<Section>:<Key> of %s' %
                                os.path.basename(switches_path))
        elif kind in ('kQbLabel', 'kQbPlanned'): problems.append(where + ': no label / planned rows in the TP block')
    if sorted(seen) != sorted(TP_PACKAGES):
        problems.append('TruMenu.cpp: TP package groups %s, wanted %s' % (sorted(seen), sorted(TP_PACKAGES)))
    for p, c in sorted(seen.items()):
        if not c['note'] or not c['check']: problems.append('TruMenu.cpp: package %s needs a hint and a check' % p)
    view = fn_body(src, 'void QbViewOf(')
    for k in TP_KINDS:
        if 'r.kind == %s' % k not in view: problems.append('TruMenu.cpp: QbViewOf must handle %s' % k)
    act = fn_body(src, 'void QbActRow(')
    for k in TP_KINDS:
        if 'r.kind == %s' % k not in act: problems.append('TruMenu.cpp: QbActRow must handle %s' % k)
    if act.find('r.kind == kQbSwitch') > act.find('g_qbActRow = &r;'):
        problems.append('TruMenu.cpp: QbActRow handles the TP kinds before g_qbActRow = &r (not in the recent list)')
    ex = fn_body(src, 'void QbExecRow(')
    if 'case kQbCheck: TpCheckSet(page, r, "skip", true)' not in ex or 'case kQbNote: return;' not in ex or \
            'TpSwAct(r, kQbXDir)' not in ex:
        problems.append('TruMenu.cpp: QbExecRow: X on a check = skip, on a switch = kQbXDir, on a note nothing')
    for fn in ('bool QbHelpLine(', 'void PageQbRow('):
        body = fn_body(src, fn)
        if any('kind == %s' % k not in body for k in TP_KINDS): problems.append('TruMenu.cpp: %s must handle the TP kinds' % fn)
    fav = fn_body(src, 'bool QbFavOk(')
    if any('r->kind != %s' % k not in fav for k in TP_KINDS): problems.append('TruMenu.cpp: QbFavOk must refuse the TP kinds')
    if 't.id[3] == \'.\') continue;' not in fn_body(src, 'int QbTestsRows('):
        problems.append('TruMenu.cpp: QbTestsRows must skip the tp<package>.<name> rows')
    cs = fn_body(src, 'void TpCheckSet(')
    i_list, i_add, i_mark = cs.find('if (!listed) {'), cs.find('RunTestAdd('), cs.find('TestMark(r.arg, state')
    if not (0 <= i_list < i_add < i_mark) or '"open" : want' not in cs:
        problems.append('TruMenu.cpp: TpCheckSet: test.add only when not listed, then TestMark; the same state again = open')
    sv = fn_body(src, 'void TpSwAct(')
    if 'SwFindLocked(r.arg)' not in sv or 'QbSwAct(y, dir)' not in sv or 'y.kind = kQdSw;' not in sv:
        problems.append('TruMenu.cpp: TpSwAct must find the switch and run the page Fixes path QbSwAct')
    if 'p.rows[i].kind == kQbNote' not in src: problems.append('TruMenu.cpp: the start-up row count must skip the notes')
    header, opt_rows = table(src)
    if len(opt_rows) < 258:   # 0.22.30 adds [Input] DeviceGlyphs: at least the 258 keys of 0.22.28
        problems.append('TruMenu.cpp: kOpts has %d keys - 0.22.28 adds no INI key (258)' % len(opt_rows))
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if 'ebd75bd759135f76a26bcf867310d394033c48467e1e64e93431ab337388159d' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.27 build hash (work\\asi\\menu0250) is missing')
    n = {k: sum(1 for r in rows if r[4] == k) for k in TP_KINDS + ('kQbGroup',)}
    return problems, ('TP block: %d rows (%d groups, %d checks, %d switches, %d notes), all kQfTp, packages %s, no INI '
                      'key' % (len(rows), n['kQbGroup'], n['kQbCheck'], n['kQbSwitch'], n['kQbNote'],
                               ' '.join(p.upper() for p in sorted(seen))))


def check_02229():
    """0.22.29 (Q103 radial lock; workspace docs/Befund-Radial-Sperre-Q103-1111.md): RadialTick with [Radial] Enabled=0
    closes a ring that is still open and drops its pending requests; DrawRadial counts its frames (g_radDrawn, reset at
    the open); every place that runs a ring entry from RadialTick (release, Mode=menu confirm, A / click, R3) asks
    RadDrawnEnough first, which logs 'radial: <what> ignored - not drawn'; no new INI key (258); Set-TruMenu.ps1 knows
    the 0.22.28 hash"""
    problems = []
    src = read_cpp()
    if '0.22.29 (radial lock, Q103' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.30: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.29 part "0.22.29 (radial lock, Q103"')
    tick = src[src.find('\nvoid RadialTick() {'):]
    tick = tick[:tick.find('\n}\n')]
    if not tick: return problems + ['TruMenu.cpp: RadialTick not found'], 'radial: no RadialTick'
    head = tick[:tick.find('bool front')]
    if 'if (!g_radEnabled) {' not in head or 'RadialClose("[Radial] Enabled=0")' not in head:
        problems.append('TruMenu.cpp: RadialTick must close an open ring when [Radial] Enabled=0')
    for req in ('g_radRelease', 'g_radOpenReq', 'g_radCloseReq'):
        if 'InterlockedExchange(&%s, 0);' % req not in head:
            problems.append('TruMenu.cpp: RadialTick with Enabled=0 must drop %s' % req)
    acts = len(re.findall(r'RadialActivate\(|RadVirtActivate\(|RadQuitPress\(', tick))
    guards = ['RadDrawnEnough("release")', 'RadDrawnEnough("confirm")', 'RadDrawnEnough("A / left click")',
              'RadDrawnEnough("R3 release")']
    for g in guards:
        if g not in tick: problems.append('TruMenu.cpp: RadialTick lacks %s' % g)
    if acts != 6:
        problems.append('TruMenu.cpp: RadialTick runs entries at %d places (0.22.29 guarded 6) - guard a new one' % acts)
    if 'InterlockedExchange(&g_radDrawn, 0);' not in tick: problems.append('TruMenu.cpp: g_radDrawn must reset at the open')
    draw = src[src.find('\nvoid DrawRadial() {'):]
    draw = draw[:draw.find('EnterCriticalSection(&g_radLock);')]
    if 'InterlockedIncrement(&g_radDrawn);' not in draw:
        problems.append('TruMenu.cpp: DrawRadial must count its frame before the lock')
    if 'ignored - not drawn (%ld frames)' not in src: problems.append('TruMenu.cpp: RadDrawnEnough log line missing')
    if src.count('RadialActivate(') - src.count('void RadialActivate(') != 4:
        problems.append('TruMenu.cpp: RadialActivate must be called only from RadialTick (4 places)')
    header, opt_rows = table(src)
    if len(opt_rows) < 258:   # 0.22.30 adds [Input] DeviceGlyphs
        problems.append('TruMenu.cpp: kOpts has %d keys - 0.22.29 adds no INI key (258)' % len(opt_rows))
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if 'e284247a58914abc4c856343d52f067fe83ad1a37fb4fa16a16e5cf01bf554fd' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.28 build hash (work\\asi\\menu0251) is missing')
    return problems, 'radial lock: Enabled=0 closes, %d drawn-frame guards, %d entry calls in RadialTick' % (
        len(guards), acts)


def check_02230():
    """0.22.30 (group D1 12.11.; workspace docs/Befund-Gruppe-D1-1211.md): Q107 - Log() stamps with TruLogStamp (date +
    time) and writes the session header through TruLogSessionStart (src/asi/TruLog.h), StampLength takes an optional
    date; Q95 - [Input] DeviceGlyphs (default 0), PadHook / WndProcHook feed the last device, GlTick patches the 23 bytes
    at 0x5a7d75 only after 12 byte checks (push esi / call GlName / add esp, 4 / 14 nops), GlName falls back to the
    game's vf+0x20; Q103 rest - QuickTick asks QbDrawnEnough before any bar press, DrawQuick counts the open bar,
    DrawMenu disables its widgets (PushItemFlag / PopItemFlag) and drops the TO TEST X / Y edges below 3 drawn frames,
    the counters reset at the open; kOpts 259 keys; Set-TruMenu.ps1 knows the 0.22.29 hash"""
    problems = []
    src = read_cpp()
    if '0.22.30 (log dates, device glyphs, drawn guards' not in src[:src.find('\n', src.find('kVersion = '))]:   # 0.22.31: a later part
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.30 part "0.22.30 (log dates, device glyphs, drawn guards"')
    log = fn_body(src, 'void Log(')
    if 'TruLogStamp(line, sizeof(line))' not in log or 'TruLogSessionStart(f, "TruMenu", kVersion);' not in log:
        problems.append('TruMenu.cpp: Log must stamp with TruLogStamp and write the session header (Q107)')
    if '#include "../TruLog.h"' not in src: problems.append('TruMenu.cpp: TruLog.h not included')
    hdr = open(os.path.join(ROOT, 'src', 'asi', 'TruLog.h'), encoding='utf-8-sig').read()
    if '"%04d-%02d-%02d %02d:%02d:%02d.%03d "' not in hdr or 'session start (pid %lu) ===' not in hdr:
        problems.append('TruLog.h: stamp "YYYY-MM-DD HH:MM:SS.mmm " / session header text changed')
    st = fn_body(src, 'size_t StampLength(')
    if "t[4] == '-'" not in st or 'StampLengthTime(t + date)' not in st:
        problems.append('TruMenu.cpp: StampLength must take an optional "YYYY-MM-DD " before the time')
    # Q95 device glyphs
    if '"Input", "DeviceGlyphs", "' not in src:   # 0.22.38: default 1 (owner decision 13.11.) - check_02238 checks it
        problems.append('TruMenu.cpp: kOpts lacks [Input] DeviceGlyphs')
    if 'g_glDevGlyphs = OptInt(ini, "Input", "DeviceGlyphs") != 0 ? 1 : 0;' not in src:
        problems.append('TruMenu.cpp: ReadOptions must read [Input] DeviceGlyphs')
    if 'if (connected) GlPadSeen(copy);' not in fn_body(src, 'DWORD WINAPI PadHook('):
        problems.append('TruMenu.cpp: PadHook must feed GlPadSeen with the raw poll')
    if 'GlWndSeen(hwnd, msg, wParam, lParam);' not in fn_body(src, 'LRESULT CALLBACK WndProcHook('):
        problems.append('TruMenu.cpp: WndProcHook must feed GlWndSeen')
    checks = src[src.find('const DvCheck kGlChecks[] = {'):]
    checks = checks[:checks.find('\n};')]
    n_checks = len(re.findall(r'\{0x00[0-9a-f]{6}, "', checks))
    if n_checks != 12: problems.append('TruMenu.cpp: kGlChecks has %d checks (0.22.30: 12)' % n_checks)
    orig = 'a1 68 2b a0 00 8b 48 08 8b 11 8b 04 b5 f8 9e 8a 00 8b 52 20 50 ff d2'.split()
    have = re.search(r'const BYTE kGlSiteOrig\[23\] = \{(.*?)\};', src, re.S)
    if not have or [x.strip()[2:] for x in have.group(1).split(',')] != orig:
        problems.append('TruMenu.cpp: kGlSiteOrig must be the 23 game bytes at 0x5a7d75')
    tick = fn_body(src, 'void GlTick(')
    i_chk, i_patch = tick.find('DvChecks(kGlChecks'), tick.find('LcPatch(kGlSite, kGlSiteOrig')
    if not (0 <= i_chk < i_patch) or 'if (!g_glDevGlyphs || g_glChecked) return;' not in tick:
        problems.append('TruMenu.cpp: GlTick must check the bytes before the patch and only with DeviceGlyphs=1')
    for b in ('g_glPatch[0] = 0x56;', 'g_glPatch[1] = 0xe8;', 'g_glPatch[6] = 0x83;', 'g_glPatch[8] = 0x04;',
              'for (int i = 9; i < 23; ++i) g_glPatch[i] = 0x90;', '(kGlSite + 1 + 5)'):
        if b not in tick: problems.append('TruMenu.cpp: GlTick patch layout lacks %s' % b)
    gn = fn_body(src, 'const GlStr *__cdecl GlName(')
    if 'return own(remap, 0, code);' not in gn or '__except' not in gn:
        problems.append('TruMenu.cpp: GlName must fall back to the game\'s vf+0x20 and catch faults')
    if 'GlTick();' not in fn_body(src, 'void Render('):
        problems.append('TruMenu.cpp: Render must call GlTick')
    # Q103 rest
    qt = fn_body(src, 'void QuickTick(')
    i_guard, i_dir = qt.find('if (edges && !QbDrawnEnough(edges)) {'), qt.find('const WORD dir = ')
    if not (0 <= i_guard < i_dir): problems.append('TruMenu.cpp: QuickTick must ask QbDrawnEnough before any bar press')
    if 'if (!g_qbOpen) InterlockedExchange(&g_qbDrawn, 0);' not in qt:
        problems.append('TruMenu.cpp: g_qbDrawn must reset while the bar is closed')
    if 'if (g_qbOpen) InterlockedIncrement(&g_qbDrawn);' not in fn_body(src, 'void DrawQuick('):
        problems.append('TruMenu.cpp: DrawQuick must count the open bar\'s frames')
    dm = fn_body(src, 'void DrawMenu(')
    if dm.count('ImGui::PushItemFlag(ImGuiItemFlags_Disabled, true);') != 1 or dm.count('if (notDrawn) ImGui::PopItemFlag();') != 1:
        problems.append('TruMenu.cpp: DrawMenu must push / pop the disabled flag once each')
    if '&& !notDrawn;' not in dm or 'InterlockedIncrement(&g_menuDrawn);' not in dm:
        problems.append('TruMenu.cpp: DrawMenu must drop X / Y while not drawn and count its frames')
    if 'InterlockedExchange(&g_menuDrawn, 0);' not in fn_body(src, 'void Render('):
        problems.append('TruMenu.cpp: g_menuDrawn must reset at the open / close')
    for line in ('quick: buttons 0x%04x ignored - not drawn (%ld frames)', 'menu: input ignored - not drawn (%ld frames)'):
        if line not in src: problems.append('TruMenu.cpp: log line "%s" missing' % line)
    header, opt_rows = table(src)
    if len(opt_rows) < 259:   # 0.22.34 adds [Achievements] Enabled (check_02234): at least the 259 keys of 0.22.30
        problems.append('TruMenu.cpp: kOpts has %d keys - 0.22.30 adds [Input] DeviceGlyphs (259)' % len(opt_rows))
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if '7c8acbb34540547c2ec2893072c0e8d3e941517a57b2a17b92bcf1c5444f2ab1' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.29 build hash (work\\asi\\menu0252) is missing')
    return problems, 'log dates + session header, device glyphs (%d byte checks, 23-byte patch), quick bar / menu drawn ' \
                     'guards, %d INI keys' % (n_checks, len(opt_rows))


def check_02231():
    """0.22.31 (group B 12.11.; workspace docs/Befund-Gruppe-B-1211.md): Q105 - kUnitsNoArchive (9 names in no PC archive)
    + kUnitsNoData = the 15 names of work/q97_q105_1111/q105_units.tsv, UnitNameNoDrm also for names outside the level
    list, unit.go refuses them; kChapOrder carries the base game (84 rows, head column) and checkpoint rows of the base
    game run cp.jump ... force; Q106 - kJtChecks (27 rows), JtCheck after UberCheck, JtTick in the PadHook frame block,
    joint.set on the game thread + danger row, uber.dump joint lines, QbPzRows on page Kapitel; no new INI key;
    Set-TruMenu.ps1 knows the 0.22.30 hash. The full table / byte check is work/b_nav_1211/check_0254.py."""
    problems = []
    src = read_cpp()
    ver = src[:src.find('\n', src.find('kVersion = '))]
    if '0.22.31 (level navigation + puzzles, group B' not in ver:
        problems.append('TruMenu.cpp: kVersion must hold the 0.22.31 part "0.22.31 (level navigation + puzzles, group B"')
    block = src[src.index('const char *const kUnitsNoArchive[] = {'):]
    names = re.findall(r'"(\w+)"', block[:block.index('};')])
    if len(names) != 9 or 'l1_rutlands_ship_m1' not in names:
        problems.append('TruMenu.cpp: kUnitsNoArchive must hold the 9 Q105 names (has %d)' % len(names))
    if 'UnitNameInNoArchive(unit) && UnitModsDrmMissing(unit)' not in fn_body(src, 'bool UnitNameNoDrm('):
        problems.append('TruMenu.cpp: UnitNameNoDrm must test names outside the level list')
    if 'UnitRefusal(unit, o, n); return false; }   // 0.22.31' not in fn_body(src, 'bool RunUnitGo('):
        problems.append('TruMenu.cpp: unit.go must refuse a unit without data')
    order = src[src.index('const ChapOrder kChapOrder[] = {'):]
    order = order[:order.index('\n};')]
    n_visit2 = len(re.findall(r'(?:nullptr|")\s*, 2\},', order))   # 0.22.37: the Paket R return visits (visit 2)
    if order.count('{"Base game l') - n_visit2 != 84:
        problems.append('TruMenu.cpp: kChapOrder must hold 84 base-game rows (has %d + %d return visits)'
                        % (order.count('{"Base game l') - n_visit2, n_visit2))
    if 'ChapBaseGroup(kUnits[i].group) ? " force" : ""' not in fn_body(src, 'int QbChapRows('):
        problems.append('TruMenu.cpp: base-game checkpoint rows must run cp.jump ... force')
    jt = src[src.index('const NavCheckBytes kJtChecks[] = {'):]
    n_jt = len(re.findall(r'\{0x[0-9a-fA-F]{8},', jt[:jt.index('\n};')]))
    if n_jt != 27: problems.append('TruMenu.cpp: kJtChecks has %d rows (0.22.31: 27)' % n_jt)
    for s, why in (('    JtCheck();', 'JtCheck at the start'), ('        JtTick();', 'JtTick in PadHook'),
                   ('true, ValJointSet,', 'joint.set on the game thread'), ('"puzzle cheat (moves a joint)"},   // 0.22.31 (Q106)', 'joint.set danger row'),
                   ('JtDumpLines(cand[i].state, name', 'uber.dump joint lines'), ('n += QbPzRows(v, d, max, de);', 'page Kapitel puzzles')):
        if s not in src: problems.append('TruMenu.cpp: %s missing' % why)
    ps = open(os.path.join(ROOT, 'scripts', 'windows', 'Set-TruMenu.ps1'), encoding='utf-8-sig').read()
    if '0753f83050ff70a2274f2ddcf65252607f2edbd33b6a91037ba4e37367244a90' not in ps:
        problems.append('Set-TruMenu.ps1: the 0.22.30 build hash (work\\asi\\menu0253) is missing')
    return problems, 'units without data (%d + 6 names), base-game chapter table (84 rows), joint puzzles (%d byte ' \
                     'checks, joint.set, page Kapitel Raetsel)' % (len(names), n_jt)


def table(src):
    block = src[src.index('const OptDef kOpts[] = {'):]
    block = block[:block.index('\n};')]
    rows = []
    for entry in re.findall(r'\{("(?:[^{}])*?)\},', block, re.S):
        lits = [unescape(x) for x in LIT.findall(entry)]
        rows.append((lits[0], lits[1], lits[2], ''.join(lits[3:])))
    header = unescape(LIT.search(src[src.index('kIniHeader ='):]).group(1))
    return header, rows


def text(header, rows):
    out = ['; %s\n' % header]
    section = None
    for sec, key, default, comment in rows:
        if sec != section:
            out.append(('\n[%s]\n' if section else '[%s]\n') % sec)
            section = sec
        for line in comment.split('\n'):
            if line: out.append('; %s\n' % line)
        out.append('%s=%s\n' % (key, default))
    return ''.join(out)


def main(argv):
    global CPP, SV_HEADER
    if '--cpp' in argv[:-1]: CPP = argv[argv.index('--cpp') + 1]   # 0.19: negative tests on a copy of TruMenu.cpp
    if '--svh' in argv[:-1]: SV_HEADER = argv[argv.index('--svh') + 1]   # 0.22.27: a copy of TruSaveProbe.h
    header, rows = table(read_cpp())
    want = text(header, rows)
    if argv and argv[0] == '--print':
        sys.stdout.write(want)
        return 0
    opt = {k: argv[i + 1] for i, k in enumerate(argv[:-1]) if k in ('--ini', '--radial', '--tour', '--switches')}
    ini_path = opt.get('--ini', INI)
    problems, summary = check_lists()
    for p in problems: print('LIST %s' % p)
    if not problems: print('ok: regression lists (%s)' % ', '.join(summary))
    radial_path = opt.get('--radial', RADIAL)
    rproblems, rsummary, rlevels = check_radial(radial_path, os.path.basename(radial_path))   # 0.10
    for p in rproblems: print('RADIAL %s' % p)
    if not rproblems: print('ok: radial menu file (%s)' % rsummary)
    problems += rproblems
    tour_path = opt.get('--tour', TOUR)       # 0.10.1
    tproblems, tsummary, tlevels = check_radial(tour_path, os.path.basename(tour_path), '# TruMenu tour')
    for p in tproblems: print('TOUR %s' % p)
    if not tproblems: print('ok: tour file (%s, below Tests/Rundgang)' % tsummary)
    problems += tproblems
    bproblems, bsummary = check_builtins(rows, rlevels, tlevels)
    for p in bproblems: print('RADIAL %s' % p)
    if not bproblems: print('ok: %s' % bsummary)
    problems += bproblems
    vproblems = check_ini_values(ini_path)
    for p in vproblems: print('INI %s' % p)
    if not vproblems: print('ok: [Radial] Mode / Freeze / QuitSector / TestsLevel / FreezeSound / FreezeShaderClock values')
    problems += vproblems
    sproblems, ssummary = check_shot(ini_path, radial_path)   # 0.10.5
    for p in sproblems: print('SHOT %s' % p)
    if not sproblems: print('ok: [Shot] Enabled / Folder / Clean / Hotkey / MaxPerMinute values, shot items + exports, %s'
                            % ssummary)
    problems += sproblems
    fproblems = check_flow(ini_path)          # 0.11
    for p in fproblems: print('FLOW %s' % p)
    if not fproblems: print('ok: [Flow] Enabled / File / Overlay / Position / Size / Lines / AutoAdvance / ToastSeconds / '
                            'PollMs values, %d flow items, TruFlowCore.h included' % len(FLOW_ITEMS))
    problems += fproblems
    dproblems, dsummary = check_debug(ini_path, radial_path)   # 0.12
    for p in dproblems: print('DEBUG %s' % p)
    if not dproblems: print('ok: [Debug] Enabled / NavDraw / NavMask values, %d nav items, %s' % (len(NAV_ITEMS), dsummary))
    problems += dproblems
    qproblems, qsummary = check_quick(ini_path, radial_path)   # 0.17
    for p in qproblems: print('QUICK %s' % p)
    if not qproblems: print('ok: [Quick] / [Shot] OnCine* / CheckpointHide values, %s, ring entries' % qsummary)
    problems += qproblems
    eproblems, esummary = check_018(ini_path, radial_path)   # 0.18
    for p in eproblems: print('Q018 %s' % p)
    if not eproblems: print('ok: 0.18 keys / items / bar pages: %s' % esummary)
    problems += eproblems
    aproblems, asummary = check_019(ini_path, radial_path, rows)   # 0.19
    for p in aproblems: print('Q019 %s' % p)
    if not aproblems: print('ok: 0.19 dumb AI: %s' % asummary)
    problems += aproblems
    zproblems, zsummary = check_020(ini_path, radial_path, rows)   # 0.20
    for p in zproblems: print('Q020 %s' % p)
    if not zproblems: print('ok: 0.20: %s' % zsummary)
    problems += zproblems
    xproblems, xsummary = check_021(ini_path, radial_path, rows)   # 0.21
    for p in xproblems: print('Q021 %s' % p)
    if not xproblems: print('ok: 0.21 arachnophobia / camera / ai.remove: %s' % xsummary)
    problems += xproblems
    wproblems, wsummary = check_0211(ini_path, radial_path, rows)   # 0.21.1
    for p in wproblems: print('Q0211 %s' % p)
    if not wproblems: print('ok: 0.21.1 ai.kill / sticky / room check / physics / spawn / bar: %s' % wsummary)
    problems += wproblems
    tproblems3, tsummary3 = check_0213(ini_path)   # 0.21.3
    for p in tproblems3: print('Q0213 %s' % p)
    if not tproblems3: print('ok: 0.21.3 quick bar X / Y, sound list width: %s' % tsummary3)
    problems += tproblems3
    hproblems, hsummary = check_0214(ini_path, rows)   # 0.21.4
    for p in hproblems: print('Q0214 %s' % p)
    if not hproblems: print('ok: 0.21.4 hall02 counter: %s' % hsummary)
    problems += hproblems
    fproblems5, fsummary5 = check_0215(radial_path, opt.get('--switches', SWITCHES))   # 0.21.5
    for p in fproblems5: print('Q0215 %s' % p)
    if not fproblems5: print('ok: 0.21.5 Fixes + frozen ring: %s' % fsummary5)
    problems += fproblems5
    gproblems6, gsummary6 = check_0216(ini_path)   # 0.21.6
    for p in gproblems6: print('Q0216 %s' % p)
    if not gproblems6: print('ok: 0.21.6 costumes / flight line / quick command line: %s' % gsummary6)
    problems += gproblems6
    gproblems7, gsummary7 = check_0217(ini_path, opt.get('--switches', SWITCHES))   # 0.21.7
    for p in gproblems7: print('Q0217 %s' % p)
    if not gproblems7: print('ok: 0.21.7 footer / help / umlauts / costumes / chapters / label layers: %s' % gsummary7)
    problems += gproblems7
    gproblems8, gsummary8 = check_0218(ini_path, opt.get('--switches', SWITCHES))   # 0.21.8
    for p in gproblems8: print('Q0218 %s' % p)
    if not gproblems8: print('ok: 0.21.8 checks / command line / favourites / story / sound groups: %s' % gsummary8)
    problems += gproblems8
    nproblems, nsummary = check_0201(ini_path, radial_path)   # 0.20.1
    for p in nproblems: print('Q0201 %s' % p)
    if not nproblems: print('ok: 0.20.1 sound list: %s' % nsummary)
    problems += nproblems
    cproblems13, csummary13 = check_02213()   # 0.22.13
    for p in cproblems13: print('Q02213 %s' % p)
    if not cproblems13: print('ok: 0.22.13 %s' % csummary13)
    problems += cproblems13
    cproblems14, csummary14 = check_02214()   # 0.22.14
    for p in cproblems14: print('Q02214 %s' % p)
    if not cproblems14: print('ok: 0.22.14 %s' % csummary14)
    problems += cproblems14
    cproblems15, csummary15 = check_02215()   # 0.22.15
    for p in cproblems15: print('Q02215 %s' % p)
    if not cproblems15: print('ok: 0.22.15 %s' % csummary15)
    problems += cproblems15
    cproblems16, csummary16 = check_02216(ini_path)   # 0.22.16
    for p in cproblems16: print('Q02216 %s' % p)
    if not cproblems16: print('ok: 0.22.16 %s' % csummary16)
    problems += cproblems16
    cproblems17, csummary17 = check_02217(ini_path)   # 0.22.17
    for p in cproblems17: print('Q02217 %s' % p)
    if not cproblems17: print('ok: 0.22.17 %s' % csummary17)
    problems += cproblems17
    cproblems18, csummary18 = check_02218(ini_path)   # 0.22.18
    for p in cproblems18: print('Q02218 %s' % p)
    if not cproblems18: print('ok: 0.22.18 %s' % csummary18)
    problems += cproblems18
    cproblems19, csummary19 = check_02219(ini_path, opt.get('--switches', SWITCHES))   # 0.22.19
    for p in cproblems19: print('Q02219 %s' % p)
    if not cproblems19: print('ok: 0.22.19 %s' % csummary19)
    problems += cproblems19
    cproblems20, csummary20 = check_02220(ini_path)   # 0.22.20
    for p in cproblems20: print('Q02220 %s' % p)
    if not cproblems20: print('ok: 0.22.20 %s' % csummary20)
    problems += cproblems20
    cproblems21, csummary21 = check_02221(ini_path)   # 0.22.21
    for p in cproblems21: print('Q02221 %s' % p)
    if not cproblems21: print('ok: 0.22.21 %s' % csummary21)
    problems += cproblems21
    cproblems22, csummary22 = check_02222(ini_path)   # 0.22.22
    for p in cproblems22: print('Q02222 %s' % p)
    if not cproblems22: print('ok: 0.22.22 %s' % csummary22)
    problems += cproblems22
    cproblems23, csummary23 = check_02223(opt.get('--switches', SWITCHES))   # 0.22.23
    for p in cproblems23: print('Q02223 %s' % p)
    if not cproblems23: print('ok: 0.22.23 %s' % csummary23)
    problems += cproblems23
    cproblems24, csummary24 = check_02224(ini_path, opt.get('--switches', SWITCHES))   # 0.22.24
    for p in cproblems24: print('Q02224 %s' % p)
    if not cproblems24: print('ok: 0.22.24 %s' % csummary24)
    problems += cproblems24
    cproblems25, csummary25 = check_02225()   # 0.22.25
    for p in cproblems25: print('Q02225 %s' % p)
    if not cproblems25: print('ok: 0.22.25 %s' % csummary25)
    problems += cproblems25
    cproblems26, csummary26 = check_02226(ini_path)   # 0.22.26
    for p in cproblems26: print('Q02226 %s' % p)
    if not cproblems26: print('ok: 0.22.26 %s' % csummary26)
    problems += cproblems26
    cproblems32, csummary32 = check_02232(ini_path)   # 0.22.32 (group A; next to its 0.22.26 arena check)
    for p in cproblems32: print('Q02232 %s' % p)
    if not cproblems32: print('ok: 0.22.32 %s' % csummary32)
    problems += cproblems32
    cproblems33, csummary33 = check_02233(ini_path)   # 0.22.33 (group K)
    for p in cproblems33: print('Q02233 %s' % p)
    if not cproblems33: print('ok: 0.22.33 %s' % csummary33)
    problems += cproblems33
    cproblems34, csummary34 = check_02234(ini_path, opt.get('--switches', SWITCHES))   # 0.22.34 (group M)
    for p in cproblems34: print('Q02234 %s' % p)
    if not cproblems34: print('ok: 0.22.34 %s' % csummary34)
    problems += cproblems34
    cproblems35, csummary35 = check_02235()   # 0.22.35 (Q113)
    for p in cproblems35: print('Q02235 %s' % p)
    if not cproblems35: print('ok: 0.22.35 %s' % csummary35)
    problems += cproblems35
    cproblems36, csummary36 = check_02236(ini_path, opt.get('--switches', SWITCHES))   # 0.22.36 (labels)
    for p in cproblems36: print('Q02236 %s' % p)
    if not cproblems36: print('ok: 0.22.36 %s' % csummary36)
    problems += cproblems36
    cproblems37, csummary37 = check_02237(ini_path, opt.get('--switches', SWITCHES))   # 0.22.37 (P5 debug view)
    for p in cproblems37: print('Q02237 %s' % p)
    if not cproblems37: print('ok: 0.22.37 %s' % csummary37)
    problems += cproblems37
    cproblems38, csummary38 = check_02238(ini_path, opt.get('--switches', SWITCHES))   # 0.22.38 (PD)
    for p in cproblems38: print('Q02238 %s' % p)
    if not cproblems38: print('ok: 0.22.38 %s' % csummary38)
    problems += cproblems38
    cproblems39, csummary39 = check_02239(ini_path, opt.get('--switches', SWITCHES))   # 0.22.39 (Q126 attract icon)
    for p in cproblems39: print('Q02239 %s' % p)
    if not cproblems39: print('ok: 0.22.39 %s' % csummary39)
    problems += cproblems39
    cproblems40, csummary40 = check_02240(ini_path, opt.get('--switches', SWITCHES))   # 0.22.40 (Q126b styles)
    for p in cproblems40: print('Q02240 %s' % p)
    if not cproblems40: print('ok: 0.22.40 %s' % csummary40)
    problems += cproblems40
    cproblems41, csummary41 = check_02241(ini_path, opt.get('--switches', SWITCHES))   # 0.22.41 (Q126c compact)
    for p in cproblems41: print('Q02241 %s' % p)
    if not cproblems41: print('ok: 0.22.41 %s' % csummary41)
    problems += cproblems41
    cproblems42, csummary42 = check_02242(ini_path, opt.get('--switches', SWITCHES))   # 0.22.42 (W3 debug view)
    for p in cproblems42: print('Q02242 %s' % p)
    if not cproblems42: print('ok: 0.22.42 %s' % csummary42)
    problems += cproblems42
    cproblems43, csummary43 = check_02243()   # 0.22.43 (W5 markup)
    for p in cproblems43: print('Q02243 %s' % p)
    if not cproblems43: print('ok: 0.22.43 %s' % csummary43)
    problems += cproblems43
    cproblems44, csummary44 = check_02244(opt.get('--switches', SWITCHES))   # 0.22.44 (W2 order)
    for p in cproblems44: print('Q02244 %s' % p)
    if not cproblems44: print('ok: 0.22.44 %s' % csummary44)
    problems += cproblems44
    cproblems45, csummary45 = check_02245(opt.get('--switches', SWITCHES))   # 0.22.45 (W6 sound switches)
    for p in cproblems45: print('Q02245 %s' % p)
    if not cproblems45: print('ok: 0.22.45 %s' % csummary45)
    problems += cproblems45
    cproblems46, csummary46 = check_02246()   # 0.22.46 (arena from the main menu)
    for p in cproblems46: print('Q02246 %s' % p)
    if not cproblems46: print('ok: 0.22.46 %s' % csummary46)
    problems += cproblems46
    cproblems47, csummary47 = check_02247(opt.get('--switches', SWITCHES))   # 0.22.47 (sound monitor)
    for p in cproblems47: print('Q02247 %s' % p)
    if not cproblems47: print('ok: 0.22.47 %s' % csummary47)
    problems += cproblems47
    cproblems48, csummary48 = check_02248(opt.get('--switches', SWITCHES))   # 0.22.48 (adrenaline at Lara, sonar)
    for p in cproblems48: print('Q02248 %s' % p)
    if not cproblems48: print('ok: 0.22.48 %s' % csummary48)
    problems += cproblems48
    cproblems49, csummary49 = check_02249(opt.get('--switches', SWITCHES))   # 0.22.49 (sonar all floors, adrenaline)
    for p in cproblems49: print('Q02249 %s' % p)
    if not cproblems49: print('ok: 0.22.49 %s' % csummary49)
    problems += cproblems49
    cproblems50, csummary50 = check_02250(opt.get('--switches', SWITCHES))   # 0.22.50 (sound log readable, Kapitel)
    for p in cproblems50: print('Q02250 %s' % p)
    if not cproblems50: print('ok: 0.22.50 %s' % csummary50)
    problems += cproblems50
    cproblems51, csummary51 = check_02251(opt.get('--switches', SWITCHES))   # 0.22.51 (sonar view, base PDA, X default)
    for p in cproblems51: print('Q02251 %s' % p)
    if not cproblems51: print('ok: 0.22.51 %s' % csummary51)
    problems += cproblems51
    cproblems52, csummary52 = check_02252(opt.get('--switches', SWITCHES))   # 0.22.52 (reverb mark, DSP graph, S6, joint)
    for p in cproblems52: print('Q02252 %s' % p)
    if not cproblems52: print('ok: 0.22.52 %s' % csummary52)
    problems += cproblems52
    cproblems53, csummary53 = check_02253(opt.get('--switches', SWITCHES))   # 0.22.53 (sound log trees, S7, markup)
    for p in cproblems53: print('Q02253 %s' % p)
    if not cproblems53: print('ok: 0.22.53 %s' % csummary53)
    problems += cproblems53
    cproblems54, csummary54 = check_02254(opt.get('--switches', SWITCHES))   # 0.22.54 (two crash fixes, reset at start)
    for p in cproblems54: print('Q02254 %s' % p)
    if not cproblems54: print('ok: 0.22.54 %s' % csummary54)
    problems += cproblems54
    cproblems55, csummary55 = check_02255()   # 0.22.55 (chapter page + display fixes, package P2a)
    for p in cproblems55: print('Q02255 %s' % p)
    if not cproblems55: print('ok: 0.22.55 %s' % csummary55)
    problems += cproblems55
    cproblems56, csummary56 = check_02256()   # 0.22.56 (puzzle helpers, notes, P3 fixes, package P2b)
    for p in cproblems56: print('Q02256 %s' % p)
    if not cproblems56: print('ok: 0.22.56 %s' % csummary56)
    problems += cproblems56
    cproblems57, csummary57 = check_02257()   # 0.22.57 (puzzle helpers 2, package Q2)
    for p in cproblems57: print('Q02257 %s' % p)
    if not cproblems57: print('ok: 0.22.57 %s' % csummary57)
    problems += cproblems57
    cproblems58, csummary58 = check_02258()   # 0.22.58 (chapter / loading + costume 857, package Q1b)
    for p in cproblems58: print('Q02258 %s' % p)
    if not cproblems58: print('ok: 0.22.58 %s' % csummary58)
    problems += cproblems58
    cproblems59, csummary59 = check_02259()   # 0.22.59 (puzzles + landing log, package R1)
    for p in cproblems59: print('Q02259 %s' % p)
    if not cproblems59: print('ok: 0.22.59 %s' % csummary59)
    problems += cproblems59
    cproblems60, csummary60 = check_02260()   # 0.22.60 (motion data, package R1b)
    for p in cproblems60: print('Q02260 %s' % p)
    if not cproblems60: print('ok: 0.22.60 %s' % csummary60)
    problems += cproblems60
    cproblems61, csummary61 = check_02261()   # 0.22.61 (Thor pillar areas, package R1c)
    for p in cproblems61: print('Q02261 %s' % p)
    if not cproblems61: print('ok: 0.22.61 %s' % csummary61)
    problems += cproblems61
    cproblems62, csummary62 = check_02262()   # 0.22.62 (fix build S1 after the live test 18.11.)
    for p in cproblems62: print('Q02262 %s' % p)
    if not cproblems62: print('ok: 0.22.62 %s' % csummary62)
    problems += cproblems62
    cproblems63, csummary63 = check_02263()   # 0.22.63 (build S3 after the analysis S2)
    for p in cproblems63: print('Q02263 %s' % p)
    if not cproblems63: print('ok: 0.22.63 %s' % csummary63)
    problems += cproblems63
    cproblems64, csummary64 = check_02264()   # 0.22.64 (build S4, follow camera)
    for p in cproblems64: print('Q02264 %s' % p)
    if not cproblems64: print('ok: 0.22.64 %s' % csummary64)
    problems += cproblems64
    cproblems65, csummary65 = check_02265()   # 0.22.65 (build S5, evidence logs)
    for p in cproblems65: print('Q02265 %s' % p)
    if not cproblems65: print('ok: 0.22.65 %s' % csummary65)
    problems += cproblems65
    cproblems67, csummary67 = check_02267()   # 0.22.67 (build B1: K1, V1, N5, logs)
    for p in cproblems67: print('Q02267 %s' % p)
    if not cproblems67: print('ok: 0.22.67 %s' % csummary67)
    problems += cproblems67
    cproblems68, csummary68 = check_02268()   # 0.22.68 (build B2: Thor reach, ...)
    for p in cproblems68: print('Q02268 %s' % p)
    if not cproblems68: print('ok: 0.22.68 %s' % csummary68)
    problems += cproblems68
    cproblems27, csummary27 = check_02227(ini_path, opt.get('--switches', SWITCHES))   # 0.22.27
    for p in cproblems27: print('Q02227 %s' % p)
    if not cproblems27: print('ok: 0.22.27 %s' % csummary27)
    problems += cproblems27
    cproblems28, csummary28 = check_02228(ini_path, opt.get('--switches', SWITCHES))   # 0.22.28
    for p in cproblems28: print('Q02228 %s' % p)
    if not cproblems28: print('ok: 0.22.28 %s' % csummary28)
    problems += cproblems28
    cproblems29, csummary29 = check_02229()   # 0.22.29
    for p in cproblems29: print('Q02229 %s' % p)
    if not cproblems29: print('ok: 0.22.29 %s' % csummary29)
    problems += cproblems29
    cproblems30, csummary30 = check_02230()   # 0.22.30
    for p in cproblems30: print('Q02230 %s' % p)
    if not cproblems30: print('ok: 0.22.30 %s' % csummary30)
    problems += cproblems30
    cproblems31, csummary31 = check_02231()   # 0.22.31
    for p in cproblems31: print('Q02231 %s' % p)
    if not cproblems31: print('ok: 0.22.31 %s' % csummary31)
    problems += cproblems31
    have =open(ini_path, encoding='utf-8', newline='').read().replace('\r\n', '\n')
    if have == want:
        print('ok: TruMenu.ini = defaults table (%d keys)' % len(rows))
        return 1 if problems else 0
    a, b = have.split('\n'), want.split('\n')
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else '<end>'
        y = b[i] if i < len(b) else '<end>'
        if x != y:
            print('MISMATCH line %d\n  ini:   %s\n  table: %s' % (i + 1, x, y))
            break
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
