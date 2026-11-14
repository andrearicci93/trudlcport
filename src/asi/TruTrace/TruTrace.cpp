// TruTrace.asi - log-only diagnostics for the PC tru.exe (Steam, image base 0x400000). Nothing the game does changes:
// every hook logs and then runs the original code with all registers, the flags and the x87 / SSE state as they were
// (pushad / pushfd / fxsave around the plugin's code). The questions it answers ("where do we have to change it?"):
//
//   [Sound] F5 groan loop. Emitter create tru+0x1935d0 (entry hook, with the result): who started which sound - the
//     anim event sound branch of tru+0x1b99c0 (return 0x5b99fc: esi = event payload, ebp = its frame: +0xc instance,
//     +0x1c channel, +0x20 param; the emitter goes into the instance's sound list [inst+0x248] when payload byte 1 bit
//     0 is set or channel and param are both != -1, as 0x5b9aad..0x5b9abe test), the sound by id tru+0x1953e0 (return
//     0x595412; from the anim branch when its caller is 0x5b9bf7), the play wrappers 0x593c90 / 0x593ce0 / 0x594c60 /
//     0x594ca0 (their caller is logged) and every other caller. The sound id is emitter +0xc = [soundplex+8] (the
//     SoundPlex DTP id, 0x593659). Emitter end = vtable 0x851240 slot 0 (deleting destructor 0x590920; the only way an
//     emitter is freed: refcount 0 -> vtbl[1] 0x597810 -> vtbl[0](1)). Instance sound list release 0x58d740 (at
//     instance removal 0x5bca1c / 0x5d0d90): fixed slots stopped with 0x589820(4), the dynamic list (the anim event
//     sounds) only releases its handles (0x58a1f0, no stop). Fixed-slot stop 0x589820(mode) = node vtbl[+0x10](mode).
//     Emitters still alive after [Trace] SoundLiveMs are reported once ("sound LONG"), repeated starts of one sound by
//     one instance ("sound REPEAT").
//   [Teleport] F6. A poll thread (every PollMs) watches the player position (instance +0x20); a jump of more than
//     TeleportUnits between two polls logs the player state before / after (chart record of Lara's machine
//     gameTracker+0xf10 with its Lara state ids, gameTracker+0xa64 / +0xc94, instance +0x14, [0xfada74]) and again
//     after 0.25 / 0.5 / 1 / 2 / 3 s. [Chart] the chart machine's record changes for the player's machines: transition
//     tru+0x387890 (entry + result, caller = which update path), reset tru+0x3874d0, start tru+0x387e00 - level 1 in
//     the teleport window, level 2 otherwise.
//   [PowerMessages] Receivers of 0x1f4 / 0x1f5: TruShadowPower wakes every receiver with tru+0x1b2de0 right before
//     message(inst, msg, 0); the wake hook logs the calls that come from TruShadowPower.asi's code (instance, object,
//     handler +0x120). 0x1f4 / 0x1f5 from TruShadowPowerMeterApi flags bit 0 (set before 0x1f4, cleared before
//     0x1f5 in its source). The handler's return value cannot be seen from here (TruShadowPower calls the handler
//     through a pointer it read before the wake) - instance +0x14 is logged 0.5 s later instead.
//   [Spawn] intro tru+0x1bcc30 (cdecl, intro record: +0x50 object id, +0x58 unique id, +0x72 flags), birth
//     tru+0x1bd0f0 (object = arg 5) and tru+0x1bd270 (object = arg 2): every request for an object whose name contains
//     SpawnFilter, its caller and the result; a refused request gets the reason read from the same data the code
//     tests (instance with that intro id exists, object table state != 2, free list [0xd98d5c] empty, object flag).
//   [Object858] NEU-4: object table 0xdb7400 entry of object 858 (state +0xe, object +8, data +0x5c type) - every
//     change with time and unit.
//   [TimeVector] F7: RenderDevice [0xa1407c] +0xfa4c (u32, the upload 0x5096c7 uses (v % 1000000) x 0.001) and
//     +0xfa48 (float) once per TimeVectorMs, with the frame dt [0xe7f188] and the shader clock stop byte [0xdb94de].
//
// 0.2 (05.11., "what we log, we do not have to guess" - hall02 loaded into Yggdrasil-Ende):
//   [Level] GAMELOOP_RequestLevelChangeByName tru+0x1df8c0 (name, gameTracker 0xe7f088, doneType; caller + module;
//     ignored while gameTracker+0xb9 is set, 0x5df8d3), the request bytes gameTracker+0xb8..+0xbb / name +0x38 (poll),
//     STREAM_LevelLoadAndInit tru+0x1d30d0 (name -> stream unit entry; also called by STREAM_MoveIntoNewStreamUnit
//     tru+0x1c1bf0 through [0x8aa840]), the player placement tru+0x1d40c0 (unit entry; it picks the intro whose id
//     +0x58 = the game data checkpoint id [0xc59264]+0x90 (+0x114 when +0x1f4 != 0), else a checkpoint /
//     invis_checkpoint intro by the unit's default index, copies its position into the player intro 0x698180 and
//     spawns the player 0x5bd080; with no checkpoint intro it tail-jumps SAVE_SaveGame(0) 0x5d4330), the move into a
//     new stream unit (player +0xe0 != [0xe7f148], 0x5dfc8e).
//   [Portal] stream portal hit tru+0x1d2aa0 (instance, portal: "Hit stream portal in %s to %s" 0x5d2af7; record =
//     [[unit data]+4] + portal +0x14 * 0x100, target unit +0x84) - the player's at level 1.
//   [StreamUnits] poll of the stream unit table 0xdbab40 (32 x 0xd8: +0 id, +4 state, +0xc name): loads / unloads.
//   [Save] SAVE_SaveGame tru+0x1570f0 ("Save Game": backup [0xc5925c] = active [0xc59258], 0x557114; callers: the
//     checkpoint message handler 0x6a1a70 after writing the checkpoint record (0x6a1da2: +0x80 = checkpoint intro
//     id), the gameloop 0x5dfba0, the placement tail jump), SAVE_RestoreGame tru+0x157130 ("Restore Game": active =
//     backup, 0x556e90 copies data +0x10 into gameTracker+0x38 and prints "ID wanted" = data +0x90) with the result,
//     and a poll of the fields that decide the reload position (+0x10 unit, +0x90 / +0x114 checkpoint, +0x1f4 mode)
//     in both copies.
//   [Progress] instance births / removals (list 0xd98d54) and instance +0x14 flag changes of objects whose name
//     contains one of ProgressFilter; [Messages] INSTANCE_Post tru+0x1b3750 (inst, msg, data) to such instances;
//     [GameData] changed byte ranges of the active save buffer (0x140000 bytes) - progress flags, unit save data.
//
// 0.3 (05.11., F5 follow-up, docs Befund-Stoehnen-0511.md): [Sound] SoundSlots - the object sound-slot play
//   tru+0x193d50 (thiscall, ecx = the instance sound list [inst+0x248]; slot, mode, p3, p4; ret 0x10), reached only from
//   the anim event dispatcher tru+0x1b69c0 (type 0x60, call 0x5b6a30: slot = payload byte +4, mode = +5, p3 / p4 =
//   the dispatcher's arguments 2 / 4). Mode 1 starts the slot's SoundPlex node through 0x593c90 (return 0x593dec) only
//   when the slot's handle has no live emitter, mode 0 stops a live one (node vtbl[+0x10](4)) or releases a dead
//   handle. The entry + leave lines name the owner instance, slot, mode, p3 / p4, the emitter before / after and the
//   dispatcher's caller; emitters started there carry "fixed slot N of <instance>" in their START / LONG / END lines,
//   so "sound 20212" (the section id of the doppelganger's slot nodes) is tied to a slot.
//
// 0.3.3 (14.11., recurring crash tru+0x1b7476 in 0x5b7430: [[model DTP+0x68]+4] = 0, render path 0x5bbd06):
//   [ModelInst] every InstanceDrawable built by its ctor tru+0x1b93e0 (thiscall, this = the drawable, arg = the game
//     instance, ret 4; vtable 0x853abc; +4 instance, +0x10 one PCRenderModelInstance per model, +0x14 PCMatrixState):
//     instance, object id / name, intro id, position, unit, the object's model list (object +0x3a s16 count, +0x40
//     model DTP pointers), per model the DTP (word0, +4 segment count, +0x68 the mesh bone table {count, segments},
//     +0xc own segments), its PCRenderModel (DTP +0x64; +8 = the render resource SERIAL [0xa14148]++ of 0x502600 - not
//     a section id) and render model instance; who built it: the instance init 0x5ba810 (return 0x5ba9e6; its own
//     caller = intro 0x5bcc30 / birth 0x5bd0f0 / child birth 0x5bd270 / clone 0x4d0e50 / 0x5bb160 / 0x5bb84d), the
//     init 0x5d07e0 (return 0x5d0946) or the derived drawable ctor 0x6d0c20; plus the intro / birth hook running on
//     this thread (its caller, intro id, parent). A model whose bone table pointer is set but its segments are 0 (or
//     with no +0x68 and +0xc 0) is flagged at level 0. One line per object and unit at level 1, the rest at level 2,
//     and a summary 3 s after the last drawable of a burst.
//   [NullModel] entry hook of 0x5b7430 (cdecl, 5 args: model DTP, world matrix, 0, flag, PCMatrixState; callers
//     0x5bbd06 with ebx = the drawable and 0x5b80af with esi = the drawable): when the DTP is 0, or +0x68 != 0 and
//     [+0x68]+4 == 0, or +0x68 == 0 and +0xc == 0 (the path 0x5b7467..0x5b7476 reads [0+0x20]), one line with the
//     drawable, instance, object, model index, bone table words, position and the birth record of [ModelInst] -
//     written to the file at once (the game crashes on the next instruction). SkipNullModelDraw=1 returns from
//     0x5b7430 without running it (diagnostic aid, not a fix: the matrix state then keeps old data).
//
// Every hook site and every fact the decoding relies on is byte-checked first; a mismatch switches that category off
// and is logged. Lines are buffered and written by the poll thread (every 100 ms) - no file access in the game's hooks.
// Rate limit per category: MaxLinesPerSecond, MaxLinesPerCategory. Options: TruTrace.ini [Trace], log TruTrace.log.

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <ctype.h>
#include <math.h>
#include "../TruLog.h"                      // Q107: date + time in every log line, session header

namespace {

const char kVersion[] = "TruTrace 0.3.3";            // 0.3.1: dated log lines (Q107); 0.3.2: ProgressFilter default,
                                                      // stale player machines cleared (P5); 0.3.3: ModelInst, NullModel
const DWORD kImageBase = 0x00400000;

// ---- game data (read only) ----
const DWORD kPlayerPtr = 0x00e7f094;          // GameTracker +0xc player instance
const DWORD kGameTrackerPtr = 0x00fadb58;     // TU gameTracker (+0xf10 Lara's chart machine, +0xa64, +0xc94)
const DWORD kPlayerCtl = 0x00fada74;          // player control word (TruMenu: no-damage bit 0x20000)
const DWORD kInstanceHead = 0x00d98d54;       // active instances, +8 next
const DWORD kInstanceFree = 0x00d98d5c;       // free list of the instance pool (tru+0x1b2ef0)
const DWORD kObjNames = 0x00db94d0;           // +0 count, name of object id n at +n*8
const DWORD kObjectTable = 0x00db7400;        // 0xcc entries of 0x24: +8 object, +0xc s16 id, +0xe u16 state
const int kObjectEntries = 0xcc;
const DWORD kUnitId = 0x00e7f148;             // current stream unit id
const DWORD kStreamUnits = 0x00dbab40, kStreamUnitsEnd = 0x00dbc640, kStreamUnitSize = 0xd8;
const DWORD kRenderDevicePtr = 0x00a1407c;
const DWORD kFrameDt = 0x00e7f188, kClockStop = 0x00db94de;
const DWORD kListSentinel = 0x00cd3bb8;       // end node of a dynamic sound list (0x58d85d)

// return addresses of the emitter create calls
const DWORD kRetAnimSound = 0x005b99fc;       // tru+0x1b99c0 sound branch
const DWORD kRetSoundById = 0x00595412;       // tru+0x1953e0
const DWORD kRetAnimById = 0x005b9bf7;        // tru+0x1953e0 called from tru+0x1b99c0
struct WrapperRet { DWORD ret; int callerSlot; const char *name; };
const WrapperRet kWrappers[] = {{0x00593cac, 5, "play 0x593c90"}, {0x00593cfe, 5, "play 0x593ce0"},
                                {0x00594c9a, 6, "play by id 0x594c60"}, {0x00594cd6, 6, "play by id 0x594ca0"}};

// ---- 0.2: level / unit load, save / checkpoint, progress (read only) ----
const DWORD kGt = 0x00e7f088;                 // GameTracker (0x5dfb6d push; +0x38 unit name 0x5df8ee, +0xc0 unit id)
const DWORD kSaveActive = 0x00c59258;         // active save buffer (0x140000 bytes + guard 0xdeadbeef, 0x5571c6)
const DWORD kSaveBackup = 0x00c5925c;         // checkpoint copy ("Save Game" 0x557114: backup = active)
const DWORD kDataActive = 0x00c59264;         // game data block in the active buffer (+0x10 unit name, +0x90 checkpoint)
const DWORD kDataBackup = 0x00c59268;         // the same block in the backup buffer
const DWORD kSaveSize = 0x00140000;
const DWORD kRetCheckpoint = 0x006a1e17;      // SAVE_SaveGame(0) from the checkpoint message handler 0x6a1a70 (esi = it)
const DWORD kRetGameloopSave = 0x005dfbbc;    // SAVE_SaveGame(0) from the gameloop 0x5dfba0 (streamFlags 0x200000)
const DWORD kRetRequestByName = 0x005dfb78;   // RequestLevelChangeByName(name, gt, 4) from 0x5dfb20 (UI 0x77e4xx..)
const DWORD kRetRequestUi = 0x007744b8;       // RequestLevelChangeByName(gt+0x38, gt, 10) from 0x7744xx
const DWORD kRetLevelLoad = 0x005de02a;       // STREAM_LevelLoadAndInit from 0x5dded0 (the level load)
const DWORD kRetStreamMove = 0x005c1c4e;      // STREAM_LevelLoadAndInit through [0x8aa840] from 0x5c1bf0
const DWORD kRetPlaceLoad = 0x005de179;       // player placement from 0x5de040 (after a level load)
const DWORD kRetPlaceRestore = 0x005de6fa;    // player placement from 0x5de480 (restore path)

// ---- 0.3: object sound-slot play tru+0x193d50 (read only) ----
const DWORD kRetSlotPlay = 0x005b6a35;        // tru+0x193d50 from the anim event dispatcher tru+0x1b69c0 (type 0x60)
const DWORD kRetSlotStart = 0x00593dec;       // play 0x593c90 called from tru+0x193d50 (mode 1)

// ---- 0.3.3: drawables / model instances, the null-model draw 0x5b7430 (read only) ----
const DWORD kVtDrawable = 0x00853abc;         // cdc::InstanceDrawable (ctor 0x5b93e0, dtor 0x5b76b0)
const DWORD kVtDrawableDerived = 0x0085d468;  // drawable class of the ctor 0x6d0c20 (base ctor 0x5b93e0 first)
const DWORD kRetDrawInit = 0x005ba9e6;        // ctor from the instance init 0x5ba810 (frame 0x18: its return at E[8])
const DWORD kRetDrawInit2 = 0x005d0946;       // ctor from the init 0x5d07e0 (ebp frame: its return at [ebp+4])
const DWORD kRetDrawDerived = 0x006d0c30;     // ctor from the derived ctor 0x6d0c20 (4 pushes: its return at E[6])
const DWORD kRetDerivedCtor = 0x006d1b20;     // 0x6d0c20 from 0x6d1b1b
const DWORD kRetModelDrawA = 0x005bbd0b;      // 0x5b7430 from 0x5bbd06 (ebx = the drawable)
const DWORD kRetModelDrawB = 0x005b80b4;      // 0x5b7430 from 0x5b80af in 0x5b7fe0 (esi = the drawable)
struct RetName { DWORD ret; const char *name; };
// callers of the instance init 0x5ba810 (return addresses) and of the init 0x5d07e0
const RetName kInitCallers[] = {{0x005bcd04, "intro 0x5bcc30"}, {0x005bd180, "birth 0x5bd0f0"},
                                {0x005bd2da, "child birth 0x5bd270"}, {0x004d0eb3, "instance clone 0x4d0e50"},
                                {0x005bb300, "0x5bb160 (called from 0x55568a)"}, {0x005bb84d, "init site 0x5bb848"}};
const RetName kInit2Callers[] = {{0x0053802a, "0x538025"}, {0x0053f2fb, "0x53f2f6"}, {0x006c6ea4, "0x6c6e9f"},
                                 {0x006d40cb, "0x6d40c6"}};
// facts of the slot hook only (a mismatch switches SoundSlots off, not the whole sound category)
const char *const kSlotFacts[][2] = {
    {"005b69c0", "8b44240c 0fbf08"},                                         // payload = dispatcher arg 3, type word
    {"005b69f4", "8b4c2404 8b8948020000 85c9"},                              // ecx = [inst+0x248]
    {"005b6a1c", "0fbe4005 56 8b742414 56 8b742410 56 0fbed2 50 52 e81bd3fdff 5e c3"},   // slot / mode / p3 / p4, ret
    {"00593d82", "8b4508 8d1440 8d3491 8b4f08 0fbf5cc104 8d04c1 8b08 8b4514 3dff000000 7402 8bd8 8b450c 83e800 "
                 "0f84b9000000 83e801 0f85ea000000 8b06 85c0 7422 833800 0f85db000000"},   // slots 0xc / table 8, modes
    {"00593de7", "e8a4feffff 83c408"},                                       // mode 1: play 0x593c90 (return 0x593dec)
    {"00593e38", "668b4d10 66894844"},                                       // p3 -> emitter +0x44
    {"00593e97", "8b4908 8b11 8b4210 6a04 ffd0"},                            // mode 0: node vtbl[+0x10](4)
};

// ---- facts (read-only byte checks; same strings as work\asi\trace01\precheck_trace01.txt) ----
enum Cat { kCatTrace, kCatSound, kCatTele, kCatChart, kCatPower, kCatSpawn, kCatObj, kCatTime, kCatLevel, kCatPortal,
            kCatStream, kCatSave, kCatProg, kCatMsg, kCatData, kCatGround, kCatModel, kCatNull,
            kCatCount };   // 0.3.2: + ground; 0.3.3: + modelinst, nullmodel
const char *const kCatName[kCatCount] = {"trace", "sound", "teleport", "chart", "power", "spawn", "obj", "timevec",
                                         "level", "portal", "stream", "save", "progress", "message", "gamedata",
                                         "ground", "modelinst", "nullmodel"};
struct Fact { int cat; DWORD at; const char *hex; };
const Fact kFacts[] = {
    {kCatSound, 0x005b99d7, "0fbe06 85c0 0f8559010000 d9ee 8b4604 51 d91c24 50 8d4c2420 51 8b0d00818a00 e8d49bfdff"},
    {kCatSound, 0x005b9a50, "668b4514 668b5d1c"},
    {kCatSound, 0x005b9a6f, "668b4520 663dffff"},
    {kCatSound, 0x005b9aad, "f6460101 750d 6683fbff 744f 66837d20ff 7448 8b8f48020000"},
    {kCatSound, 0x005b9af1, "e8aa15fdff"},
    {kCatSound, 0x005953e0, "51 8b442410 56 8b3500818a00 50 e88e8bfbff 83c404 85c0 0f84a6000000 d9442424 51 d91c24 50 "
                            "8d4c240c 51 8bce e8bee1ffff"},
    {kCatSound, 0x005b9be1, "8b4608 50 8d4c2434 89542440 8b5514 51 52 e8e9b7fdff"},
    {kCatSound, 0x00593c90, "d9ee 8b442408 56 8b742408 51 8b0d00818a00 d91c24 50 56 e824f9ffff"},
    {kCatSound, 0x00593ce0, "d944240c 8b442408 56 8b742408 51 8b0d00818a00 d91c24 50 56 e8d2f8ffff"},
    {kCatSound, 0x00594c60, "8b442408 57 8b3d00818a00 50 e80f93fbff 83c404"},
    {kCatSound, 0x00594c84, "d9442410 56 8b74240c 51 d91c24 50 56 8bcf e836e9ffff"},
    {kCatSound, 0x00594ca0, "8b442408 57 50 8bf9 e8d392fbff 83c404 85c0 750e"},
    {kCatSound, 0x00594cc2, "d9ee 56 8b74240c 51 d91c24 50 56 8bcf e8fae8ffff"},
    {kCatSound, 0x005935e8, "c20c00"},
    {kCatSound, 0x005936bf, "c20c00"},
    {kCatSound, 0x00593712, "c20c00"},
    {kCatSound, 0x00593659, "8b4f08 dfe0 894e0c"},
    {kCatSound, 0x0059086e, "c70040128500"},
    {kCatSound, 0x005bca06, "8bbe48020000 85ff c7864802000000000000 7418 8bcf e81f0dfdff"},
    {kCatSound, 0x0058d76c, "6a04 e8adc0ffff"},
    {kCatSound, 0x0058d781, "8d4e10 5e e966caffff"},
    {kCatSound, 0x00589861, "8b4a08 8b01 8b5010 55 ffd2"},
    {kCatSound, 0x0058b112, "85f6 8b4b10 8908 894310"},
    {kCatSound, 0x0058d85b, "8b3e 3b3db83bcd00"},
    {kCatChart, 0x00787a10, "c20400"},
    {kCatChart, 0x007879b4, "89ae10050000"},
    {kCatChart, 0x00768b60, "a158dbfa00 56 c70574dafa0048000000 8bb0100f0000"},
    {kCatTele, 0x00768b60, "a158dbfa00 56 c70574dafa0048000000 8bb0100f0000"},
    {kCatSpawn, 0x005bcc7d, "0fb74750 6aff 50 e8a74a0000 83c408 85c0 0f8478030000 6683780e02"},
    {kCatSpawn, 0x005bccda, "e81162ffff 8bf0 85f6 0f8401030000"},
    {kCatSpawn, 0x005bcfe9, "c3"},
    {kCatSpawn, 0x005b2ef0, "a15c8dd900 85c0 7442"},
    {kCatSpawn, 0x005bf2d4, "b80074db00 b9cc000000 57 90 6683780e02"},
    {kCatObj, 0x005bf2d4, "b80074db00 b9cc000000 57 90 6683780e02"},
    {kCatTrace, 0x005bcff9, "8b0dd094db00 52 8b14c1"},
    {kCatTrace, 0x005c1b50, "56 8b742408 33c0 33d2 b940abdb00 8bff 80790402 7504 3931 7413 81c1d8000000 83c201 "
                            "81f940c6db00"},
    {kCatTrace, 0x005c1c28, "e823ffffff 8b0db0a2db00 8d680c"},
    {kCatTime, 0x005096c7, "8b854cfa0000 33d2 b940420f00 f7f1"},
    {kCatTime, 0x005096e8, "dc0dd0168400"},
    {kCatTime, 0x005096fb, "d98548fa0000"},
    {kCatTime, 0x008416d0, "000000e04d62503f"},
    // 0.2 [Level]: request (gt+0xb9 test, gt+0x2c |= 1, name -> gt+0x38, then 0x5df760(doneType)), the state bytes
    // 0x5df760 writes (gt+0xbb = 0, +0xb9 = 1, +0xb8 = doneType), the gameTracker push, the level load chain
    {kCatLevel, 0x005df8d3, "80bfb900000000 754d 834f2c01"},
    {kCatLevel, 0x005df8ee, "83c738 8bd7 8bc6 2bd6"},
    {kCatLevel, 0x005df916, "8b442418 d91d88b78a00 50 e83afeffff"},
    {kCatLevel, 0x005df883, "c60543f1e70000 a241f1e700 881d40f1e700"},
    {kCatLevel, 0x005dfb6b, "6a04 6888f0e700 56 e848fdffff"},
    {kCatLevel, 0x005de025, "e8a650ffff"},
    {kCatLevel, 0x005c1c42, "6888f0e700 55 ff1540a88a00 893d48f1e700"},
    {kCatLevel, 0x008aa840, "d0305d00"},
    {kCatLevel, 0x005d3355, "8bc6 5e 5b 8be5 5d c3"},
    // placement tru+0x1d40c0: entry +8 unit data, [+0x74] intro list (+0xc count, +0x10 array of 0x90: +0 position,
    // +0x50 object id, +0x58 intro id); the wanted checkpoint id; the search by +0x58; the default rule (names
    // 'checkpoint' 0x85512c / 'invis_checkpoint' 0x855118, index [[unit data +0x70] +0x2b4] +8); the copy 0x698180
    // (position +0..+0xc), the spawn 0x5bd080 -> [0xe7f094] and the tail jump SAVE_SaveGame(0). Not checked here:
    // 0x5d42e9..0x5d42ed (TruDlc2Player "player spawn" patch site).
    {kCatLevel, 0x005d40e7, "8b6f08 8b4d74 8b7910 8b490c"},
    {kCatLevel, 0x005d4107, "8d5750 8d9b00000000 0fb71a 3bde 740d 83c001 81c290000000"},
    {kCatLevel, 0x005d41df, "a16492c500 8b8890000000 8b9014010000 0fb780f4010000"},
    {kCatLevel, 0x005d4214, "6639b8f4010000 7408 8b9814010000 eb06 8b9890000000 85db 7437"},
    {kCatLevel, 0x005d4243, "8d4d58 3919 7412 83c001 81c190000000"},
    {kCatLevel, 0x005d426b, "682c518500 e8fbb4feff 6818518500"},
    {kCatLevel, 0x005d42a0, "8b442414 85c0 7407 0fb72a 3be8 740f 8b442418 85c0 741f 0fb72a 3be8 7518 8b44241c 8b4070 "
                            "8b80b4020000 0fb74008 3bc8 8d7ab0 740d"},
    {kCatLevel, 0x005d42f0, "56 57 e8893e0c00"},
    {kCatLevel, 0x005d4305, "e8768dfeff 50 a394f0e700"},
    {kCatLevel, 0x005d4323, "7510 83c410 c744240400000000 e9bb2df8ff"},
    {kCatLevel, 0x00698180, "8b442404 8b5010 8b4c2408 895110"},
    {kCatLevel, 0x006981a0, "8b10 8911 8b5004 895104 8b5008 895108 8b500c"},
    {kCatLevel, 0x0085512c, "636865636b706f696e7400"},
    {kCatLevel, 0x00855118, "696e7669735f636865636b706f696e7400"},
    {kCatLevel, 0x005de174, "e8475fffff"},
    {kCatLevel, 0x005de6f5, "e8c659ffff"},
    {kCatLevel, 0x005dfc88, "8b1548f1e700 3b90e0000000 7417"},
    // [Portal] tru+0x1d2aa0: unit of the instance (+0xe0), record = [[unit data]+4] + portal +0x14 * 0x100, target +0x84,
    // the print condition (player or instance +0x218 = player)
    {kCatPortal, 0x005d2aaf, "56 e89bf0feff 8b4808 8b11 8b4c2420 8b7914 c1e708 037a04 83c404 0fbf9f84000000 3bf3"},
    {kCatPortal, 0x005d2ad9, "8b3594f0e700 3bee 7408 39b518020000 751f"},
    {kCatPortal, 0x005d2af2, "83c00c 50 682c498500"},
    // [StreamUnits]: the table walk of 0x5c1b50 is the 0.1 trace fact; the level load's table walk (state byte 2)
    {kCatStream, 0x005de506, "be40abdb00"},
    {kCatStream, 0x005de510, "807e0402 7510"},
    // [Save]: "Save Game" copy, "Restore Game" copy + restore call, the data block pointers, the restore's name
    // and checkpoint reads, the checkpoint handler's record write + SAVE_SaveGame(0), the gameloop save
    {kCatSave, 0x00557114, "8b0d5892c500 8b155c92c500 6804001400 51 52 e874d72b00"},
    {kCatSave, 0x0055718f, "a15c92c500 6804001400 50 57"},
    {kCatSave, 0x005571c6, "81bf00001400efbeadde"},
    {kCatSave, 0x005571f2, "e8a9e6ffff 8b542430 52 e88ffcffff"},
    {kCatSave, 0x0055698b, "a36492c500"},
    {kCatSave, 0x00556997, "a36892c500"},
    {kCatSave, 0x00556f38, "8d4610 83c40c 803800"},
    {kCatSave, 0x00556f72, "8b9690000000"},
    {kCatSave, 0x006a1da2, "8b4658 898580000000"},
    {kCatSave, 0x006a1e0b, "e84063ffff 6a00 e8d952ebff"},
    {kCatSave, 0x005dfbb5, "6a00 e83475f7ff"},
    {kCatSave, 0x005571e9, "32c0 5b 83c41c c3"},
    {kCatSave, 0x005572d1, "b001 5b 83c41c c3"},
    {kCatSave, 0x005de537, "e8f48bf7ff"},
    // [Progress] / [Messages]: the active instance list head (+8 next) as INSTANCE_Find tru+0x1b3790 walks it
    {kCatProg, 0x005b3791, "8b35548dd900 85f6"},
    {kCatMsg, 0x005b3791, "8b35548dd900 85f6"},
    // [GameData]: the active buffer and its size (the guard at +0x140000)
    {kCatData, 0x005571c6, "81bf00001400efbeadde"},
    {kCatData, 0x00557174, "8b3d5892c500"},
    // 0.3.2 [Ground] (P5, live 13.11. dlc_dungeon): the player movement collision 0x5dce20 posts its contact record edi
    // to the player (esi) with INSTANCE_Post: 0x1c7 (other contact), 0x1c9 (facing up but steeper than player data
    // +0x100e = 52 deg), 0x1ca (walkable); the record: +0x10 / +0x14 / +0x18 a scaled vector (fstp), +0x1c ebx,
    // +0x20 [esp+0x50], +0x24 ecx, +0x28 [esp+0x58], +0x2c [esp+0x5c]; the instance pool [0xd98f60] stride 0x2f0
    {kCatGround, 0x005dd811, "d95f10 d94004 d8c9 d95f14 d84808 8b442450 894720 8b442458 894f24 d95f18 8b4c245c 894728 "
                             "895f1c 894f2c"},
    {kCatGround, 0x005dd877, "68c7010000 56 e8ce5efdff"},
    {kCatGround, 0x005dd89e, "68c9010000 56 e8a75efdff"},
    {kCatGround, 0x005dd8c5, "68ca010000 56 e8805efdff"},
    {kCatGround, 0x005dd4f4, "0fbf930e100000"},
    {kCatGround, 0x005b3969, "8b0d608fd900 0fbfc0 69c0f0020000"},
    // 0.3.3 [ModelInst]: the InstanceDrawable ctor 0x5b93e0 (vtable, +4 instance, object +0x3a s16 model count, +0x40
    // model DTP list, DTP +0x64 PCRenderModel -> device vf+0xb0 -> render model instance into [+0x10][i], +0x14 matrix
    // state, returns this, ret 4); its three call sites and the frames used to find their callers (0x5ba810: sub 8 +
    // 4 pushes, alloc thiscall; 0x5d07e0: ebp frame; 0x6d0c20: 4 pushes + arg); the callers of 0x5ba810 / 0x5d07e0 /
    // 0x6d0c20; the render resource serial at PCRenderModel +8 (base ctor 0x502600 at +4: [+4] = [0xa14148]++)
    {kCatModel, 0x005b93ea, "c706bc3a8500 896e04 8b4d10 0fbf513a"},
    {kCatModel, 0x005b9430, "8b4040 8b0c98 8b4164"},
    {kCatModel, 0x005b9444, "8b7e10 8b0d7c40a100 03fa 8b11 50 8b82b0000000 ffd0 8907"},
    {kCatModel, 0x005b947c, "894614"},
    {kCatModel, 0x005b94c7, "5f 8bc6 5e 5d 5b c20400"},
    {kCatModel, 0x005ba810, "83ec08 53 55 56 8b742418 8b5e44 57"},
    {kCatModel, 0x005ba9c6, "8b0dac9ccd00 8b4948 8b11 8b4234 6a00 6a24 ffd0 85c0 7416 56 8bc8 e8fae9ffff"},
    {kCatModel, 0x005d07e0, "55 8bec 83e4f0"},
    {kCatModel, 0x005d093e, "56 8bc8 e89a8afeff"},
    {kCatModel, 0x006d0c20, "8b442404 53 55 56 57 50 8bf1 e8b087eeff 8d4e24 c70668d48500"},
    {kCatModel, 0x006d1b1b, "e800f1ffff"},
    {kCatModel, 0x004d0eae, "e85d990e00"},
    {kCatModel, 0x005bb2fb, "e810f5ffff"},
    {kCatModel, 0x005bb848, "e8c3efffff"},
    {kCatModel, 0x005bccff, "e80cdbffff"},
    {kCatModel, 0x005bd17b, "e890d6ffff"},
    {kCatModel, 0x005bd2d5, "e836d5ffff"},
    {kCatModel, 0x00538025, "e8b6870900"},
    {kCatModel, 0x0053f2f6, "e8e5140900"},
    {kCatModel, 0x006c6e9f, "e83c99f0ff"},
    {kCatModel, 0x006d40c6, "e815c7efff"},
    {kCatModel, 0x00502600, "8bc1 c700c48e8400 8b0d4841a100 894804 83054841a10001"},
    {kCatModel, 0x0050ea89, "8d7e04 53 8bcf c706bc968400 e8663bffff"},
    {kCatModel, 0x0050eaa8, "c70604978400"},
    // 0.3.3 [NullModel]: the null path of 0x5b7430 (eax = [dtp+0x68] ? [[dtp+0x68]+4] : [dtp+0xc]; mov esi,[eax+0x20]),
    // its plain `ret` (cdecl: a skip returns with ret), both call sites with the drawable register and the caller's
    // add esp, 0x14 (eax unused after the call), 0x5b7fe0 = drawable method (this = esi, called with ecx = ebx), the
    // drawable +4 instance and the object's model list
    {kCatNull, 0x005b7467, "8b4168 85c0 7405 8b4004 eb03 8b410c 8b7020"},
    {kCatNull, 0x005b76a1, "5f 5e 5b 8be5 5d c3"},
    {kCatNull, 0x005bbcf5, "8b4314 8b4c2420 8b54241c 50 57 6a00 51 52 e825b7ffff 8b4b14 8b01 8b531c 8b400c 83c414"},
    {kCatNull, 0x005b809f, "8b4e14 8b7c241c 8b542418 51 57 53 55 52 e87cf3ffff 8b4e14 8b01 8b561c 8b400c 83c414"},
    {kCatNull, 0x005bbc71, "8bcb e868c3ffff"},
    {kCatNull, 0x005b7fe0, "56 8bf1 8b4e14"},
    {kCatNull, 0x005b93ea, "c706bc3a8500 896e04 8b4d10 0fbf513a"},
    {kCatNull, 0x005b9430, "8b4040 8b0c98 8b4164"},
};

// ---- options (TruTrace.ini, section [Trace]) ----
int g_enabled = 1, g_logLevel = 1, g_maxPerSec = 40, g_maxPerCat = 50000, g_pollMs = 5;
int g_catOn[kCatCount] = {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1};
int g_modelMaxPerSec = 200;                   // 0.3.3: [Trace] ModelInstMaxPerSecond (a level load builds hundreds)
int g_skipNullDraw = 0;                       // 0.3.3: [Trace] SkipNullModelDraw (diagnostic aid, not a fix)
int g_gameDataMs = 250;
// 0.3.2 (P5, docs Befund-P1-Mittelmeer-Objekte-1311.md): + _rw_ (rewards: appear / collected), weightbreak (jars:
// hit 0x2b / damage 0x11c, removal), ping_map (sonar pings destroyed on solve), grapple (grapple walls) - 13 of 16 tokens
#define TRUTRACE_PROG_FILTER "checkpoint,breakwall,trigger,door,gate,lever,plate,switch,spawner,_rw_,weightbreak,ping_map," \
                             "grapple"
const char kProgFilterDefault[] = TRUTRACE_PROG_FILTER;
char g_progFilterText[256] = TRUTRACE_PROG_FILTER;
int g_soundLiveMs = 4000, g_soundRepeat = 3, g_teleUnits = 300, g_teleWindowMs = 3000, g_timeMs = 1000;
int g_watchObject = 858;
char g_spawnFilter[64] = "thrall";
bool g_namesOk = false, g_unitOk = false;

// ---------------------------------------------------------------------------------------------------------------
// log: buffered, rate limited per category, "time [unit] category: text"
char g_logPath[MAX_PATH];
CRITICAL_SECTION g_logLock;
char g_buf[1 << 16];
size_t g_bufLen = 0;
char g_unit[48] = "-";
struct CatRate { LONG total, second, inSecond, dropped, droppedTotal; };
CatRate g_rate[kCatCount];

volatile LONG g_bufDropped = 0;             // lines lost because the buffer was full between two flushes

// poll thread: take the buffer under the lock, write it outside (game-thread hooks never wait for the disk)
char g_flushBuf[sizeof(g_buf)];
CRITICAL_SECTION g_fileLock;
void Flush() {
    EnterCriticalSection(&g_fileLock);
    EnterCriticalSection(&g_logLock);
    size_t n = g_bufLen;
    if (n) memcpy(g_flushBuf, g_buf, n);
    g_bufLen = 0;
    LeaveCriticalSection(&g_logLock);
    if (n && g_logPath[0]) {
        FILE *f = nullptr;
        if (fopen_s(&f, g_logPath, "ab") == 0 && f) {
            TruLogSessionStart(f, "TruTrace", kVersion, true);   // Q107: one header per process
            fwrite(g_flushBuf, 1, n, f);
            fclose(f);
        }
    }
    LeaveCriticalSection(&g_fileLock);
}

void Append(const char *line) {
    size_t n = strlen(line);
    if (g_bufLen + n + 2 > sizeof(g_buf)) { ++g_bufDropped; return; }   // the poll thread flushes every 100 ms
    memcpy(g_buf + g_bufLen, line, n);
    g_bufLen += n;
    g_buf[g_bufLen++] = '\r';
    g_buf[g_bufLen++] = '\n';
}

void Log(int cat, int level, const char *fmt, ...) {
    if (level > g_logLevel) return;
    DWORD err = GetLastError();
    char line[2000];
    SYSTEMTIME t;
    GetLocalTime(&t);
    EnterCriticalSection(&g_logLock);
    CatRate &r = g_rate[cat];
    LONG sec = static_cast<LONG>(GetTickCount() / 1000);
    if (sec != r.second) {
        if (r.dropped) {
            char note[200];                 // Q107: + 11 for the date
            _snprintf_s(note, sizeof(note), _TRUNCATE, "%04d-%02d-%02d %02d:%02d:%02d.%03d [%s] %s: (%ld lines suppressed "
                        "by the rate limit, MaxLinesPerSecond %d)", t.wYear, t.wMonth, t.wDay, t.wHour, t.wMinute,
                        t.wSecond, t.wMilliseconds, g_unit,
                        kCatName[cat], r.dropped, cat == kCatModel ? g_modelMaxPerSec : g_maxPerSec);
            Append(note);
        }
        r.second = sec;
        r.inSecond = 0;
        r.dropped = 0;
    }
    const int perSec = cat == kCatModel ? g_modelMaxPerSec : g_maxPerSec;   // 0.3.3: own budget for level loads
    bool drop = level > 0 && (r.inSecond >= perSec || r.total >= g_maxPerCat);
    if (drop) {
        ++r.dropped;
        ++r.droppedTotal;
        if (r.total == g_maxPerCat) {
            ++r.total;
            _snprintf_s(line, sizeof(line), _TRUNCATE, "%04d-%02d-%02d %02d:%02d:%02d.%03d [%s] %s: MaxLinesPerCategory "
                        "%d reached - no more lines of this category", t.wYear, t.wMonth, t.wDay, t.wHour, t.wMinute,
                        t.wSecond, t.wMilliseconds, g_unit,
                        kCatName[cat], g_maxPerCat);
            Append(line);
        }
        LeaveCriticalSection(&g_logLock);
        SetLastError(err);
        return;
    }
    ++r.inSecond;
    ++r.total;
    int n = _snprintf_s(line, sizeof(line), _TRUNCATE, "%04d-%02d-%02d %02d:%02d:%02d.%03d [%s] %s: ", t.wYear,
                        t.wMonth, t.wDay, t.wHour, t.wMinute, t.wSecond, t.wMilliseconds, g_unit, kCatName[cat]);
    va_list ap;
    va_start(ap, fmt);
    if (n > 0) _vsnprintf_s(line + n, sizeof(line) - n, _TRUNCATE, fmt, ap);
    va_end(ap);
    Append(line);
    LeaveCriticalSection(&g_logLock);
    SetLastError(err);
}

// small string builder
struct Str {
    char *p;
    size_t n, used;
    void Add(const char *fmt, ...) {
        if (used + 1 >= n) return;
        va_list ap;
        va_start(ap, fmt);
        int w = _vsnprintf_s(p + used, n - used, _TRUNCATE, fmt, ap);
        va_end(ap);
        if (w > 0) used += static_cast<size_t>(w);
        else used = n - 1;
    }
};

// ---------------------------------------------------------------------------------------------------------------
// guarded reads
bool RD(DWORD a, DWORD *v) {
    __try { *v = *reinterpret_cast<const volatile DWORD *>(a); return true; }
    __except (EXCEPTION_EXECUTE_HANDLER) { *v = 0; return false; }
}
DWORD D(DWORD a) { DWORD v = 0; RD(a, &v); return v; }
WORD W(DWORD a) {
    __try { return *reinterpret_cast<const volatile WORD *>(a); }
    __except (EXCEPTION_EXECUTE_HANDLER) { return 0; }
}
BYTE B(DWORD a) {
    __try { return *reinterpret_cast<const volatile BYTE *>(a); }
    __except (EXCEPTION_EXECUTE_HANDLER) { return 0; }
}
float F(DWORD a) {
    DWORD v = D(a);
    float f;
    memcpy(&f, &v, 4);
    return f;
}
bool ReadStr(DWORD a, char *out, size_t size) {
    out[0] = 0;
    if (!a) return false;
    __try {
        size_t i = 0;
        const volatile char *s = reinterpret_cast<const volatile char *>(a);
        for (; i + 1 < size && i < 95 && s[i]; ++i) {
            char c = s[i];
            if (static_cast<unsigned char>(c) < 32 || static_cast<unsigned char>(c) > 126) { out[0] = 0; return false; }
            out[i] = c;
        }
        out[i] = 0;
        return out[0] != 0;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        out[0] = 0;
        return false;
    }
}

bool HexBytesAt(DWORD address, const char *hex) {
    BYTE buf[128];
    size_t n = 0;
    for (const char *p = hex; *p && n < sizeof(buf);) {
        if (*p == ' ') { ++p; continue; }
        char two[3] = {p[0], p[1], 0};
        buf[n++] = static_cast<BYTE>(strtoul(two, nullptr, 16));
        p += 2;
    }
    __try {
        return memcmp(reinterpret_cast<const void *>(address), buf, n) == 0;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

// object id -> name ([0xdb94d0] + id * 8)
bool ObjectName(int id, char *out, size_t size) {
    out[0] = 0;
    if (!g_namesOk || id <= 0) return false;
    DWORD table = D(kObjNames), count = table ? D(table) : 0;
    if (!table || count > 8192 || id > static_cast<int>(count)) return false;
    return ReadStr(D(table + static_cast<DWORD>(id) * 8), out, size);
}

// stream unit name (entry with state byte 2 and the id, name at +0xc)
bool UnitName(DWORD id, char *out, size_t size) {
    out[0] = 0;
    if (!g_unitOk) return false;
    for (DWORD e = kStreamUnits; e < kStreamUnitsEnd; e += kStreamUnitSize) {
        if ((D(e + 4) & 0xff) != 2 || D(e) != id) continue;
        return ReadStr(e + 0xc, out, size);
    }
    return false;
}

int InstObjectId(DWORD inst) {
    DWORD obj = inst ? D(inst + 0x10) : 0;
    return obj ? static_cast<int>(D(obj + 0x14) & 0xffff) : 0;
}

// "inst 0x.. obj 1234 name intro 567 (player)"
void DescInst(DWORD inst, char *o, size_t n) {
    if (!inst) { _snprintf_s(o, n, _TRUNCATE, "inst 0"); return; }
    int id = InstObjectId(inst);
    char name[96];
    if (!ObjectName(id, name, sizeof(name))) strcpy_s(name, sizeof(name), "?");
    _snprintf_s(o, n, _TRUNCATE, "inst 0x%08lx obj %d %s intro %ld%s", inst, id, name, static_cast<LONG>(D(inst + 0x58)),
                inst == D(kPlayerPtr) ? " (player)" : "");
}

bool NameMatches(const char *name, const char *filter) {
    if (!filter[0]) return true;
    if (!name || !name[0]) return false;
    char a[96], b[64];
    size_t i = 0;
    for (; name[i] && i + 1 < sizeof(a); ++i) a[i] = static_cast<char>(tolower(static_cast<unsigned char>(name[i])));
    a[i] = 0;
    for (i = 0; filter[i] && i + 1 < sizeof(b); ++i) b[i] = static_cast<char>(tolower(static_cast<unsigned char>(filter[i])));
    b[i] = 0;
    return strstr(a, b) != nullptr;
}

// ---------------------------------------------------------------------------------------------------------------
// hook framework: entry patch (jmp to a stub, relocated prologue in a trampoline) or vtable slot. The stub pushes the
// hook index and jumps to CommonEnter; OnEnter replaces that slot by the trampoline address (the `ret` of CommonEnter
// jumps there) and, when the hook wants the result, swaps the return address for LeaveThunk (shadow stack per thread,
// entries matched by the stack pointer at the return).
struct Regs { DWORD edi, esi, ebp, espAtPush, ebx, edx, ecx, eax, slot, ret; };   // pushad order + slot + return
typedef bool (*EnterFn)(Regs *r, DWORD *ctx);
typedef void (*LeaveFn)(Regs *r, const DWORD *ctx);
struct Hook {
    const char *name; int cat; DWORD at; const char *hex; int copy; DWORD cleanup; bool vtable;
    EnterFn enter; LeaveFn leave;
    DWORD vtOrig;                             // vtable hooks: the function the slot must hold (hex is checked there)
    DWORD jump; bool on; volatile LONG calls;
};
const int kCtx = 8;
struct ShadowEntry { int hook; DWORD leaveEsp, ret; DWORD ctx[kCtx]; };
struct Shadow { int depth; ShadowEntry e[48]; };
DWORD g_tls = TLS_OUT_OF_INDEXES;
volatile LONG g_shadowFull = 0, g_enterFaults = 0, g_leaveFaults = 0, g_shadowMiss = 0;
extern "C" void __cdecl OnEnter(Regs *r);
extern "C" void __cdecl OnLeave(Regs *r);
void LeaveThunk();

// forward declarations of the hook bodies
bool SoundCreateEnter(Regs *r, DWORD *ctx);
void SoundCreateLeave(Regs *r, const DWORD *ctx);
bool EmitterDtorEnter(Regs *r, DWORD *ctx);
bool ListReleaseEnter(Regs *r, DWORD *ctx);
bool SlotStopEnter(Regs *r, DWORD *ctx);
bool WakeEnter(Regs *r, DWORD *ctx);
bool ChartMoveEnter(Regs *r, DWORD *ctx);
void ChartMoveLeave(Regs *r, const DWORD *ctx);
bool ChartResetEnter(Regs *r, DWORD *ctx);
bool ChartStartEnter(Regs *r, DWORD *ctx);
bool IntroEnter(Regs *r, DWORD *ctx);
void IntroLeave(Regs *r, const DWORD *ctx);
bool BirthEnter(Regs *r, DWORD *ctx);
bool Birth2Enter(Regs *r, DWORD *ctx);
void BirthLeave(Regs *r, const DWORD *ctx);
bool RequestEnter(Regs *r, DWORD *ctx);
bool StreamLoadEnter(Regs *r, DWORD *ctx);
void StreamLoadLeave(Regs *r, const DWORD *ctx);
bool PlaceEnter(Regs *r, DWORD *ctx);
void PlaceLeave(Regs *r, const DWORD *ctx);
bool MoveUnitEnter(Regs *r, DWORD *ctx);
void MoveUnitLeave(Regs *r, const DWORD *ctx);
bool PortalEnter(Regs *r, DWORD *ctx);
bool SaveEnter(Regs *r, DWORD *ctx);
void SaveLeave(Regs *r, const DWORD *ctx);
bool RestoreEnter(Regs *r, DWORD *ctx);
void RestoreLeave(Regs *r, const DWORD *ctx);
bool PostEnter(Regs *r, DWORD *ctx);
bool SlotPlayEnter(Regs *r, DWORD *ctx);
void SlotPlayLeave(Regs *r, const DWORD *ctx);
bool DrawCtorEnter(Regs *r, DWORD *ctx);       // 0.3.3
void DrawCtorLeave(Regs *r, const DWORD *ctx);
bool ModelDrawEnter(Regs *r, DWORD *ctx);

// offline self test (TruTraceSelfTest): hooks on the plugin's own test functions, same framework
bool TestEnter(Regs *r, DWORD *ctx);
void TestLeave(Regs *r, const DWORD *ctx);
bool TestSkipEnter(Regs *r, DWORD *ctx);

enum { kHSound, kHDtor, kHListRelease, kHSlotStop, kHWake, kHChartMove, kHChartReset, kHChartStart, kHIntro, kHBirth,
       kHBirth2, kHRequest, kHStreamLoad, kHPlace, kHMoveUnit, kHPortal, kHSave, kHRestore, kHPost, kHSlotPlay,
       kHDrawCtor, kHModelDraw, kRealHooks,
       kHT1 = kRealHooks, kHT2, kHT3, kHT4, kHT5, kHT6, kHT7, kHT8, kHT9, kHT10, kHT11, kHookCount };
Hook g_hooks[kHookCount] = {
    {"emitter create tru+0x1935d0", kCatSound, 0x005935d0, "53 57 8b7c2410 85ff 8bd9 750f 8b44240c", 6, 0xc, false,
     SoundCreateEnter, SoundCreateLeave, 0, 0, false, 0},
    {"emitter destructor (vtable 0x851240 slot 0 = 0x590920)", kCatSound, 0x00851240, "56 8bf1 8b4e08 85c9 c70640128500",
     0, 0, true, EmitterDtorEnter, nullptr, 0x00590920, 0, false, 0},
    {"instance sound list release tru+0x18d740", kCatSound, 0x0058d740, "56 8bf1 837e0c00 7523 837e0400 7e1d", 7, 0,
     false, ListReleaseEnter, nullptr, 0, 0, false, 0},
    {"sound slot stop tru+0x189820", kCatSound, 0x00589820, "53 56 8bf1 33db 395e04 7e4e 55 8b6c2410 57 33ff 8b460c 8b0c38",
     6, 0, false, SlotStopEnter, nullptr, 0, 0, false, 0},
    {"instance wake tru+0x1b2de0", kCatPower, 0x005b2de0, "56 8b742408 8b4618 a801 744e", 5, 0, false, WakeEnter, nullptr,
     0, 0, false, 0},
    {"chart transition tru+0x387890", kCatChart, 0x00787890, "83ec08 53 55 56 8bf1 8b4c2418 57 8b7e04", 5, 4, false,
     ChartMoveEnter, ChartMoveLeave, 0, 0, false, 0},
    {"chart reset tru+0x3874d0", kCatChart, 0x007874d0, "53 56 8bf1 8b8610050000 33db 53 50", 10, 0, false,
     ChartResetEnter, nullptr, 0, 0, false, 0},
    {"chart start tru+0x387e00", kCatChart, 0x00787e00, "56 8bf1 8b4604 0fb708 6685c9", 6, 0, false, ChartStartEnter,
     nullptr, 0, 0, false, 0},
    {"instance intro tru+0x1bcc30", kCatSpawn, 0x005bcc30, "55 8bec 83e4f0 83ec44 53 56 57 8b7d08 8b7758 56 e8086dffff",
     6, 0, false, IntroEnter, IntroLeave, 0, 0, false, 0},
    {"birth tru+0x1bd0f0", kCatSpawn, 0x005bd0f0, "55 8bec 83e4f0 83ec24 53 56 57 8b7d18 85ff", 6, 0, false, BirthEnter,
     BirthLeave, 0, 0, false, 0},
    {"birth tru+0x1bd270", kCatSpawn, 0x005bd270, "55 8bec 83e4f0 51 8b450c 85c0 53 56 57", 6, 0, false, Birth2Enter,
     BirthLeave, 0, 0, false, 0},
    // 0.2 (copy = whole position-independent instructions; 0x557130 copies `mov eax, [0xc59290]` - absolute operand)
    {"level change request tru+0x1df8c0", kCatLevel, 0x005df8c0,
     "56 8b742408 57 56 e8d45e0600 8b7c2414 83c404 80bfb900000000 754d", 5, 0, false, RequestEnter, nullptr, 0, 0, false,
     0},
    {"STREAM_LevelLoadAndInit tru+0x1d30d0", kCatLevel, 0x005d30d0, "55 8bec 83e4f0 83ec44 a1b0a2db00 53 56 57 8b7d08", 6,
     0, false, StreamLoadEnter, StreamLoadLeave, 0, 0, false, 0},
    {"player placement tru+0x1d40c0", kCatLevel, 0x005d40c0, "83ec10 53 55 56 57 8b7c2424 85ff 7413", 5, 0, false,
     PlaceEnter, PlaceLeave, 0, 0, false, 0},
    {"STREAM_MoveIntoNewStreamUnit tru+0x1c1bf0", kCatLevel, 0x005c1bf0, "a148f1e700 53 55 56 8b3594f0e700 57 8bbee0000000",
     5, 0, false, MoveUnitEnter, MoveUnitLeave, 0, 0, false, 0},
    {"stream portal hit tru+0x1d2aa0", kCatPortal, 0x005d2aa0, "51 53 55 8b6c2410 56 8bb5e0000000 57 56 e89bf0feff", 7, 0,
     false, PortalEnter, nullptr, 0, 0, false, 0},
    {"SAVE_SaveGame tru+0x1570f0", kCatSave, 0x005570f0, "807c240400 751d a19092c500 68d8d98400", 5, 0, false, SaveEnter,
     SaveLeave, 0, 0, false, 0},
    {"SAVE_RestoreGame tru+0x157130", kCatSave, 0x00557130, "83ec1c a19092c500 53 55 56 57 68fcd98400", 8, 0, false,
     RestoreEnter, RestoreLeave, 0, 0, false, 0},
    {"INSTANCE_Post tru+0x1b3750", kCatMsg, 0x005b3750, "56 8b742408 8d8610010000 85c0 7422 57 8bbe20010000", 5, 0, false,
     PostEnter, nullptr, 0, 0, false, 0},
    // 0.3: object sound-slot play (copy 6 = push ebp / mov ebp, esp / and esp, -16, as tru+0x1bcc30)
    {"sound slot play tru+0x193d50", kCatSound, 0x00593d50, "55 8bec 83e4f0 83ec14 53 56 57 8bf9 8b4f0c 85c9 751d", 6, 0x10,
     false, SlotPlayEnter, SlotPlayLeave, 0, 0, false, 0},
    // 0.3.3: InstanceDrawable ctor (copy 6 = push ebx / push ebp / mov ebp,[esp+0xc]; thiscall ret 4, returns this) and
    // the model draw 0x5b7430 (copy 6 = push ebp / mov ebp, esp / and esp, -16; cdecl, no leave hook - hot path)
    {"InstanceDrawable ctor tru+0x1b93e0", kCatModel, 0x005b93e0, "53 55 8b6c240c 56 8bf1 57 c706bc3a8500", 6, 4, false,
     DrawCtorEnter, DrawCtorLeave, 0, 0, false, 0},
    {"model draw tru+0x1b7430", kCatNull, 0x005b7430, "55 8bec 83e4f0 81ec44010000 f605b061da0001 8b4d08", 6, 0, false,
     ModelDrawEnter, nullptr, 0, 0, false, 0},
    // self test only (at / vtOrig filled in by TruTraceSelfTest; never placed in the game)
    {"test cdecl", kCatTrace, 0, "55 8bec 83e4f0", 6, 0, false, TestEnter, TestLeave, 0, 0, false, 0},
    {"test thiscall ret 0xc", kCatTrace, 0, "53 57 8b7c2410", 6, 0xc, false, TestEnter, TestLeave, 0, 0, false, 0},
    {"test float", kCatTrace, 0, "55 8bec 83e4f0", 6, 0, false, TestEnter, TestLeave, 0, 0, false, 0},
    {"test recursion", kCatTrace, 0, "55 8bec 83e4f0", 6, 0, false, TestEnter, TestLeave, 0, 0, false, 0},
    {"test vtable", kCatTrace, 0, "8bc1 33442404", 0, 0, true, TestEnter, nullptr, 0, 0, false, 0},
    // 0.2 shapes: 7-byte prologue (as tru+0x1d2aa0), absolute moffs in the copy (as tru+0x157130), push esi / mov esi
    // (as tru+0x1df8c0 / tru+0x1b3750), and a hooked function that tail-jumps into another hooked one (as the placement
    // tru+0x1d40c0 -> SAVE_SaveGame tru+0x1570f0 at 0x5d4330)
    {"test 7-byte prologue", kCatTrace, 0, "51 53 55 8b6c2410", 7, 0, false, TestEnter, TestLeave, 0, 0, false, 0},
    {"test moffs prologue", kCatTrace, 0, "83ec1c a10000fe7f", 8, 0, false, TestEnter, TestLeave, 0, 0, false, 0},
    {"test tail-jump caller", kCatTrace, 0, "83ec10 53 55", 5, 0, false, TestEnter, TestLeave, 0, 0, false, 0},
    {"test tail-jump target", kCatTrace, 0, "807c240400", 5, 0, false, TestEnter, TestLeave, 0, 0, false, 0},
    {"test push esi prologue", kCatTrace, 0, "56 8b742408", 5, 0, false, TestEnter, TestLeave, 0, 0, false, 0},
    // 0.3.3: an entry hook that skips the function (SkipNullModelDraw): r->slot = a plain ret, eax set by the hook
    {"test skip (plain ret)", kCatTrace, 0, "55 8bec 83e4f0", 6, 0, false, TestSkipEnter, nullptr, 0, 0, false, 0},
};

Shadow *GetShadow() {
    Shadow *s = static_cast<Shadow *>(TlsGetValue(g_tls));
    if (!s) {
        s = static_cast<Shadow *>(HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, sizeof(Shadow)));
        if (s) TlsSetValue(g_tls, s);
    }
    return s;
}

__declspec(naked) void CommonEnter() {
    __asm {
        pushad
        pushfd
        mov ebx, esp
        sub esp, 0x210
        and esp, 0xfffffff0
        fxsave [esp]
        lea eax, [ebx + 4]
        push eax
        call OnEnter
        add esp, 4
        fxrstor [esp]
        mov esp, ebx
        popfd
        popad
        ret
    }
}

__declspec(naked) void LeaveThunk() {
    __asm {
        push 0
        pushad
        pushfd
        mov ebx, esp
        sub esp, 0x210
        and esp, 0xfffffff0
        fxsave [esp]
        lea eax, [ebx + 4]
        push eax
        call OnLeave
        add esp, 4
        fxrstor [esp]
        mov esp, ebx
        popfd
        popad
        ret
    }
}

extern "C" void __cdecl OnEnter(Regs *r) {
    DWORD err = GetLastError();
    DWORD idx = r->slot;
    if (idx >= static_cast<DWORD>(kHookCount)) { SetLastError(err); return; }   // cannot happen (stubs push 0..10)
    Hook &h = g_hooks[idx];
    r->slot = h.jump;
    InterlockedIncrement(&h.calls);
    DWORD ctx[kCtx] = {0, 0, 0, 0, 0, 0, 0, 0};
    bool want = false;
    __try {
        want = h.enter(r, ctx);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        want = false;
        InterlockedIncrement(&g_enterFaults);
    }
    if (want && h.leave) {
        Shadow *s = GetShadow();
        if (s && s->depth < 48) {
            ShadowEntry &e = s->e[s->depth++];
            e.hook = static_cast<int>(idx);
            e.ret = r->ret;
            e.leaveEsp = reinterpret_cast<DWORD>(&r->ret) + 4 + h.cleanup;
            memcpy(e.ctx, ctx, sizeof(ctx));
            r->ret = reinterpret_cast<DWORD>(&LeaveThunk);
        } else {
            InterlockedIncrement(&g_shadowFull);
        }
    }
    SetLastError(err);
}

extern "C" void __cdecl OnLeave(Regs *r) {
    DWORD err = GetLastError();
    DWORD espNow = reinterpret_cast<DWORD>(&r->slot) + 4;
    Shadow *s = static_cast<Shadow *>(TlsGetValue(g_tls));
    int k = s ? s->depth - 1 : -1;
    while (k >= 0 && s->e[k].leaveEsp != espNow) --k;
    if (k < 0 && s && s->depth > 0) {          // not matched (cannot happen without an unwind): take the top entry
        k = s->depth - 1;
        InterlockedIncrement(&g_shadowMiss);
    }
    if (k < 0) { SetLastError(err); return; }  // no entry: unreachable (LeaveThunk is only reached through one)
    ShadowEntry e = s->e[k];
    s->depth = k;                               // drops abandoned entries above it as well
    r->slot = e.ret;
    __try {
        g_hooks[e.hook].leave(r, e.ctx);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        InterlockedIncrement(&g_leaveFaults);
    }
    SetLastError(err);
}

BYTE *g_code = nullptr;     // stubs + trampolines: 48 bytes per hook (stub at +0, trampoline at +16)

bool WriteMem(DWORD address, const void *bytes, size_t length) {
    DWORD old = 0;
    if (!VirtualProtect(reinterpret_cast<void *>(address), length, PAGE_EXECUTE_READWRITE, &old)) return false;
    memcpy(reinterpret_cast<void *>(address), bytes, length);
    DWORD dummy = 0;
    VirtualProtect(reinterpret_cast<void *>(address), length, old, &dummy);
    FlushInstructionCache(GetCurrentProcess(), reinterpret_cast<void *>(address), length);
    return true;
}

void Rel32(BYTE *at, DWORD target) {        // at = the E8 / E9 byte
    DWORD rel = target - (reinterpret_cast<DWORD>(at) + 5);
    memcpy(at + 1, &rel, 4);
}

bool Install(int idx) {
    Hook &h = g_hooks[idx];
    if (!h.at) return false;
    if (h.vtable) {
        DWORD slot = D(h.at);
        if (slot != h.vtOrig || !HexBytesAt(h.vtOrig, h.hex)) {
            Log(h.cat, 0, "%s: slot is 0x%08lx / code differs (expected 0x%08lx) - not hooked", h.name, slot, h.vtOrig);
            return false;
        }
    } else if (!HexBytesAt(h.at, h.hex)) {
        Log(h.cat, 0, "%s: bytes at 0x%08lx differ (another plugin patched it, or another exe) - not hooked", h.name, h.at);
        return false;
    }
    BYTE *stub = g_code + idx * 48;                       // fixed place per hook (Patch finds it there)
    stub[0] = 0x68;                                       // push idx
    DWORD v = static_cast<DWORD>(idx);
    memcpy(stub + 1, &v, 4);
    stub[5] = 0xe9;                                       // jmp CommonEnter
    Rel32(stub + 5, reinterpret_cast<DWORD>(&CommonEnter));
    BYTE *tramp = stub + 16;
    if (h.vtable) {
        h.jump = h.vtOrig;
    } else {
        memcpy(tramp, reinterpret_cast<const void *>(h.at), static_cast<size_t>(h.copy));   // position-independent prologue
        tramp[h.copy] = 0xe9;
        Rel32(tramp + h.copy, h.at + static_cast<DWORD>(h.copy));
        h.jump = reinterpret_cast<DWORD>(tramp);
    }
    return true;
}

bool Patch(int idx) {
    Hook &h = g_hooks[idx];
    BYTE *stub = g_code + idx * 48;
    if (h.vtable) {
        DWORD p = reinterpret_cast<DWORD>(stub);
        if (!WriteMem(h.at, &p, 4)) return false;
    } else {
        BYTE jmp[16];
        memset(jmp, 0x90, sizeof(jmp));
        jmp[0] = 0xe9;
        DWORD rel = reinterpret_cast<DWORD>(stub) - (h.at + 5);
        memcpy(jmp + 1, &rel, 4);
        if (!WriteMem(h.at, jmp, static_cast<size_t>(h.copy))) return false;
    }
    h.on = true;
    return true;
}

// ---------------------------------------------------------------------------------------------------------------
// [Sound] F5
struct Tracked {
    DWORD emitter, sid, tick, inst, payload, caller, via;
    int kind;                 // 1 anim event, 2 by id from an anim event, 3 by id, 4 wrapper, 5 other
    int inList;               // 1 = into [inst+0x248] (payload byte 1 bit 0 / channel + param), 0 = handle released
    int longDone;
    DWORD stopMode;           // last 0x589820 mode seen for it (0 = none)
    DWORD slotPlus1, slotOwner;   // 0.3: started by the slot play tru+0x193d50 (slot + 1, owner instance; 0 = no)
};
// 0.3: the slot play running on this thread (set at its entry, cleared at its leave; the emitter create runs inside it)
struct SlotCtx { DWORD tid, list, owner, slot; };
SlotCtx g_slotCtx = {0, 0, 0, 0};
int g_soundSlots = 1;         // [Trace] SoundSlots
bool g_slotFactsOk = false;
const int kTrackMax = 768;
Tracked g_track[kTrackMax];
CRITICAL_SECTION g_soundLock;
volatile LONG g_soundCreates = 0, g_soundEnds = 0, g_soundUntrackedEnds = 0;
struct RecentStart { DWORD inst, sid, tick; };
RecentStart g_recent[64];
int g_recentPos = 0;
const char *const kKindName[] = {"?", "anim event", "anim event by id", "by id", "wrapper", "other"};

void SoundOrigin(const Tracked &t, char *o, size_t n) {
    if (t.kind == 1 || t.kind == 2) {
        char inst[160];
        DescInst(t.inst, inst, sizeof(inst));
        _snprintf_s(o, n, _TRUNCATE, "%s from %s (0x1b99c0 called from 0x%08lx), payload 0x%08lx", kKindName[t.kind], inst,
                    t.via, t.payload);
    } else if (t.via && t.slotPlus1) {
        char inst[160];
        DescInst(t.slotOwner, inst, sizeof(inst));
        _snprintf_s(o, n, _TRUNCATE, "%s (return 0x%08lx, its caller 0x%08lx) - fixed slot %lu of %s (slot play "
                    "tru+0x193d50)", kKindName[t.kind], t.caller, t.via, t.slotPlus1 - 1, inst);
    } else if (t.via) {
        _snprintf_s(o, n, _TRUNCATE, "%s (return 0x%08lx, its caller 0x%08lx)", kKindName[t.kind], t.caller, t.via);
    } else {
        _snprintf_s(o, n, _TRUNCATE, "%s (return 0x%08lx)", kKindName[t.kind], t.caller);
    }
}

bool SoundCreateEnter(Regs *r, DWORD *ctx) {
    const DWORD *E = &r->ret;
    DWORD ret = E[0];
    ctx[0] = E[1];                            // out (handle)
    ctx[1] = E[2];                            // soundplex
    ctx[2] = ret;
    int kind = 5;
    DWORD payload = 0, inst = 0, via = 0, chanParam = 0xffffffff, id = 0;
    if (ret == kRetAnimSound) {
        kind = 1;
        payload = r->esi;
        inst = D(r->ebp + 0xc);
        chanParam = (D(r->ebp + 0x1c) & 0xffff) | (D(r->ebp + 0x20) << 16);
        via = D(r->ebp + 4);
    } else if (ret == kRetSoundById) {
        id = E[9];
        via = E[6];
        kind = 3;
        if (via == kRetAnimById) {
            kind = 2;
            payload = E[4];
            inst = D(r->ebp + 0xc);
            chanParam = (D(r->ebp + 0x1c) & 0xffff) | (D(r->ebp + 0x20) << 16);
            via = D(r->ebp + 4);
        }
    } else {
        for (const WrapperRet &w : kWrappers)
            if (w.ret == ret) { kind = 4; via = E[w.callerSlot]; }
    }
    ctx[3] = static_cast<DWORD>(kind);
    ctx[4] = payload;
    ctx[5] = inst;
    ctx[6] = chanParam;
    ctx[7] = via;                             // the sound id itself is read from the emitter (+0xc) at the return
    (void)id;
    return true;
}

void SoundCreateLeave(Regs *, const DWORD *ctx) {
    DWORD out = ctx[0], sp = ctx[1], ret = ctx[2], payload = ctx[4], inst = ctx[5], chanParam = ctx[6], via = ctx[7];
    int kind = static_cast<int>(ctx[3]);
    DWORD handle = out ? D(out) : 0, emitter = handle ? D(handle) : 0;
    DWORD sid = emitter ? D(emitter + 0xc) : (sp ? D(sp + 8) : 0);
    InterlockedIncrement(&g_soundCreates);
    SHORT chan = static_cast<SHORT>(chanParam & 0xffff), param = static_cast<SHORT>(chanParam >> 16);
    int inList = 0;
    BYTE b0 = 0, b1 = 0;
    SHORT s2 = 0, frame = 0;
    WORD hdr = 0;
    if (kind == 1 || kind == 2) {
        b0 = B(payload);
        b1 = B(payload + 1);
        s2 = static_cast<SHORT>(W(payload + 2));
        hdr = W(payload - 8);
        frame = static_cast<SHORT>(W(payload - 6));
        inList = kind == 1 && ((b1 & 1) || (chan != -1 && param != -1)) ? 1 : 0;
    }
    // 0.3: started by the slot play on this thread (wrapper 0x593c90 called from 0x593dec)
    DWORD slotPlus1 = 0, slotOwner = 0;
    if (kind == 4 && via == kRetSlotStart && g_slotCtx.tid == GetCurrentThreadId()) {
        slotPlus1 = g_slotCtx.slot + 1;
        slotOwner = g_slotCtx.owner;
    }
    if (emitter) {
        EnterCriticalSection(&g_soundLock);
        Tracked *slot = nullptr;
        for (int i = 0; i < kTrackMax && !slot; ++i)
            if (g_track[i].emitter == emitter) slot = &g_track[i];
        for (int i = 0; i < kTrackMax && !slot; ++i)
            if (!g_track[i].emitter) slot = &g_track[i];
        if (!slot) {                                // full: reuse the oldest entry
            DWORD now = GetTickCount(), age = 0;
            for (int i = 0; i < kTrackMax; ++i)
                if (!slot || now - g_track[i].tick > age) { slot = &g_track[i]; age = now - g_track[i].tick; }
        }
        if (slot) {
            slot->emitter = emitter; slot->sid = sid; slot->tick = GetTickCount(); slot->inst = inst;
            slot->payload = payload; slot->caller = ret; slot->via = via; slot->kind = kind; slot->inList = inList;
            slot->longDone = 0; slot->stopMode = 0;
            slot->slotPlus1 = slotPlus1; slot->slotOwner = slotOwner;
        }
        LeaveCriticalSection(&g_soundLock);
    }
    char who[400], instText[160];
    DescInst(inst, instText, sizeof(instText));
    // repeats of one sound by one starter (instance for anim events, else the calling code) within 10 s
    DWORD now = GetTickCount(), key = (kind == 1 || kind == 2) ? inst : (via ? via : ret);
    int same = 0;
    EnterCriticalSection(&g_soundLock);
    for (const RecentStart &s : g_recent)
        if (s.inst == key && s.sid == sid && now - s.tick < 10000) ++same;
    g_recent[g_recentPos] = {key, sid, now};
    g_recentPos = (g_recentPos + 1) % 64;
    LeaveCriticalSection(&g_soundLock);
    bool repeat = g_soundRepeat > 0 && same + 1 >= g_soundRepeat && (same + 1 == g_soundRepeat || (same + 1) % 10 == 0);
    if (kind == 1 || kind == 2) {
        Log(kCatSound, 1, "START sound %lu (soundplex 0x%08lx) emitter 0x%08lx %s: %s, via 0x%08lx; payload 0x%08lx bytes "
                          "%02x %02x s16 %d, record h 0x%04x frame %d; channel %d param %d; instance list: %s",
            sid, sp, emitter, kKindName[kind], instText, via, payload, b0, b1, s2, hdr, frame, chan, param,
            kind == 2 ? "no (by id: handle released at once)" : inList ? "yes ([inst+0x248], follows the bone)"
                                                                 : "no (handle released at once - plays until the "
                                                                   "SoundPlex ends by itself)");
        if (repeat)
            Log(kCatSound, 1, "REPEAT sound %lu started %d times in 10 s by %s (hypothesis A: the anim / event keeps "
                              "firing)", sid, same + 1, instText);
    } else {
        Tracked t = {};
        t.kind = kind; t.caller = ret; t.via = via; t.slotPlus1 = slotPlus1; t.slotOwner = slotOwner;
        SoundOrigin(t, who, sizeof(who));
        Log(kCatSound, 2, "start sound %lu (soundplex 0x%08lx) emitter 0x%08lx: %s", sid, sp, emitter, who);
        if (repeat)
            Log(kCatSound, 1, "REPEAT sound %lu started %d times in 10 s by %s (not an anim event: script / code path)",
                sid, same + 1, who);
    }
}

bool EmitterDtorEnter(Regs *r, DWORD *) {
    DWORD emitter = r->ecx;
    Tracked t = {};
    bool found = false;
    EnterCriticalSection(&g_soundLock);
    for (int i = 0; i < kTrackMax; ++i)
        if (g_track[i].emitter == emitter) { t = g_track[i]; g_track[i].emitter = 0; found = true; break; }
    LeaveCriticalSection(&g_soundLock);
    if (!found) { InterlockedIncrement(&g_soundUntrackedEnds); return false; }
    InterlockedIncrement(&g_soundEnds);
    char who[400];
    SoundOrigin(t, who, sizeof(who));
    DWORD age = GetTickCount() - t.tick;
    char stop[48] = "";
    if (t.stopMode) _snprintf_s(stop, sizeof(stop), _TRUNCATE, ", after a slot stop mode %ld", static_cast<LONG>(t.stopMode));
    // level 1: every emitter that got a LONG line, and anim event sounds that lived 1 s or more (short ones: level 2)
    Log(kCatSound, (t.longDone || ((t.kind == 1 || t.kind == 2) && age >= 1000)) ? 1 : 2,
        "END sound %lu emitter 0x%08lx after %lu.%03lu s%s (started: %s%s)", t.sid, emitter, age / 1000, age % 1000, stop,
        who, t.inList ? ", was in the instance list" : "");
    return false;
}

// emitter ids of a sound list ("1234 5678*" - * = tracked anim event emitter)
int ListIds(DWORD list, Str *s, bool *animTracked, DWORD stopMode) {
    int n = 0;
    DWORD count = D(list + 4), slots = D(list + 0xc);
    s->Add("fixed %lu [", count);
    for (DWORD i = 0; i < count && i < 24 && slots; ++i) {
        DWORD handle = D(slots + i * 0xc), em = handle ? D(handle) : 0;
        if (!em) continue;
        bool anim = false;
        EnterCriticalSection(&g_soundLock);
        for (int k = 0; k < kTrackMax; ++k)
            if (g_track[k].emitter == em) {
                anim = g_track[k].kind == 1 || g_track[k].kind == 2;
                if (stopMode) g_track[k].stopMode = stopMode;
            }
        LeaveCriticalSection(&g_soundLock);
        if (anim) *animTracked = true;
        s->Add("%s%lu%s", n++ ? " " : "", D(em + 0xc), anim ? "*" : "");
    }
    s->Add("]");
    return n;
}

int DynamicIds(DWORD list, Str *s, bool *animTracked) {
    DWORD sentinel = D(kListSentinel), node = D(list + 0x10);
    int n = 0;
    s->Add(", dynamic [");
    for (int guard = 0; node && node != sentinel && guard < 32; ++guard) {
        DWORD handle = D(node + 4), em = handle ? D(handle) : 0;
        if (em) {
            bool anim = false;
            EnterCriticalSection(&g_soundLock);
            for (int k = 0; k < kTrackMax; ++k)
                if (g_track[k].emitter == em) anim = g_track[k].kind == 1 || g_track[k].kind == 2;
            LeaveCriticalSection(&g_soundLock);
            if (anim) *animTracked = true;
            s->Add("%s%lu%s", n++ ? " " : "", D(em + 0xc), anim ? "*" : "");
        }
        node = D(node);
    }
    s->Add("]");
    return n;
}

bool ListReleaseEnter(Regs *r, DWORD *) {
    DWORD list = r->ecx, owner = D(list);
    char ids[400], inst[160];
    Str s = {ids, sizeof(ids), 0};
    ids[0] = 0;
    bool anim = false;
    int fixed = ListIds(list, &s, &anim, 0);
    int dyn = DynamicIds(list, &s, &anim);
    if (!fixed && !dyn) return false;
    DescInst(owner, inst, sizeof(inst));
    Log(kCatSound, (anim || owner == D(kPlayerPtr)) ? 1 : 2,
        "RELEASE instance sound list 0x%08lx of %s (caller 0x%08lx): %s - fixed slots get stop mode 4, the dynamic "
        "(anim event) entries only lose their handle (no stop) (* = started by an anim event)", list, inst, r->ret, ids);
    return false;
}

bool SlotStopEnter(Regs *r, DWORD *) {
    DWORD list = r->ecx, mode = (&r->ret)[1], owner = D(list);
    char ids[300], inst[160];
    Str s = {ids, sizeof(ids), 0};
    ids[0] = 0;
    bool anim = false;
    int fixed = ListIds(list, &s, &anim, mode ? mode : 0xffffffff);
    if (!fixed) return false;
    DescInst(owner, inst, sizeof(inst));
    Log(kCatSound, (anim || owner == D(kPlayerPtr)) ? 1 : 2, "STOP mode %lu on the fixed slots of list 0x%08lx of %s "
        "(caller 0x%08lx): %s", mode, list, inst, r->ret, ids);
    return false;
}

// 0.3: object sound-slot play tru+0x193d50 (thiscall, ecx = the sound list [inst+0x248]: +0 owner, +4 fixed slot count,
// +8 slot table (8 bytes: SoundPlex node, s16 default parameter), +0xc handles (0xc bytes: handle -> emitter)).
// Entry from the dispatcher call 0x5b6a30: [esp] 0x5b6a35, +4 slot, +8 mode, +0xc p3, +0x10 p4, +0x14 saved esi,
// +0x18 the dispatcher's return, +0x1c..+0x28 its arguments (instance, p3, payload, p4).
struct SlotKey { DWORD owner, slot, mode, result; LONG count; };
SlotKey g_slotKeys[64];
int g_slotKeyPos = 0;
const char *const kSlotResult[] = {"?", "STARTED", "already playing - not restarted", "stop mode 4 sent to the playing emitter",
                                   "dead handle released / slot empty", "mode not 0 / 1 - nothing", "start gave no emitter"};

bool SlotPlayEnter(Regs *r, DWORD *ctx) {
    const DWORD *E = &r->ret;
    const DWORD list = r->ecx, slot = E[1];
    const bool fromDispatcher = E[0] == kRetSlotPlay;
    ctx[0] = list;
    ctx[1] = slot;
    ctx[2] = E[2];                                  // mode
    ctx[3] = E[3];                                  // p3 (word -> emitter +0x44)
    ctx[4] = E[4];                                  // p4 (0xff = the slot's default parameter)
    ctx[5] = fromDispatcher ? E[6] : E[0];          // the dispatcher's caller (else the direct caller)
    DWORD slots = D(list + 0xc), handle = slots ? D(slots + slot * 0xc) : 0;
    ctx[6] = handle ? D(handle) : 0;                // emitter before (0 = none / dead handle)
    ctx[7] = fromDispatcher ? E[9] : 0;             // the event payload (type word, +4 slot, +5 mode)
    g_slotCtx.list = list;
    g_slotCtx.owner = D(list);
    g_slotCtx.slot = slot;
    g_slotCtx.tid = GetCurrentThreadId();
    return true;
}

void SlotPlayLeave(Regs *, const DWORD *ctx) {
    const DWORD list = ctx[0], slot = ctx[1], mode = ctx[2], p3 = ctx[3], p4 = ctx[4], caller = ctx[5], before = ctx[6],
                payload = ctx[7];
    if (g_slotCtx.tid == GetCurrentThreadId()) g_slotCtx.tid = 0;
    const DWORD owner = D(list), count = D(list + 4), table = D(list + 8), slots = D(list + 0xc);
    const DWORD node = table ? D(table + slot * 8) : 0;
    const SHORT defParam = table ? static_cast<SHORT>(W(table + slot * 8 + 4)) : 0;
    const DWORD handle = slots ? D(slots + slot * 0xc) : 0, after = handle ? D(handle) : 0;
    int result = 5;
    if (mode == 1) result = before ? 2 : (after ? 1 : 6);
    else if (mode == 0) result = before ? 3 : 4;
    if (result == 1) {                              // the create hook tags it already; tag it here if it could not
        EnterCriticalSection(&g_soundLock);
        for (int k = 0; k < kTrackMax; ++k)
            if (g_track[k].emitter == after && !g_track[k].slotPlus1) { g_track[k].slotPlus1 = slot + 1; g_track[k].slotOwner = owner; }
        LeaveCriticalSection(&g_soundLock);
    }
    // the same (owner, slot, mode, result): the first 5 and every 20th at level 1, the others at level 2
    LONG seen = 1;
    EnterCriticalSection(&g_soundLock);
    SlotKey *key = nullptr;
    for (SlotKey &k : g_slotKeys)
        if (k.count && k.owner == owner && k.slot == slot && k.mode == mode && k.result == static_cast<DWORD>(result)) key = &k;
    if (!key) {
        key = &g_slotKeys[g_slotKeyPos];
        g_slotKeyPos = (g_slotKeyPos + 1) % 64;
        *key = {owner, slot, mode, static_cast<DWORD>(result), 0};
    }
    seen = ++key->count;
    LeaveCriticalSection(&g_soundLock);
    char inst[160], param[40];
    DescInst(owner, inst, sizeof(inst));
    if (p4 == 0xff) _snprintf_s(param, sizeof(param), _TRUNCATE, "0xff = default %d", defParam);
    else _snprintf_s(param, sizeof(param), _TRUNCATE, "%ld", static_cast<LONG>(p4));
    const char *path = caller == 0x005b9fe8 ? "anim event kind 2 (call 0x5b9fe3)" : caller == 0x005b9f52 ? "call 0x5b9f4d"
                       : caller == 0x005bc336 ? "call 0x5bc331" : "?";
    Log(kCatSound, (seen <= 5 || seen % 20 == 0) ? 1 : 2,
        "SLOT %s of %s: slot %lu (of %lu) mode %lu (1 start, 0 stop), p3 0x%lx (emitter +0x44), p4 %s; node 0x%08lx "
        "(section %lu); emitter before 0x%08lx (sound %lu) -> after 0x%08lx (sound %lu); dispatcher caller 0x%08lx (%s), "
        "payload 0x%08lx bytes +4 %u +5 %u (seen %ld times)", kSlotResult[result], inst, slot, count, mode, p3 & 0xffff,
        param, node, node ? D(node + 8) : 0, before, before ? D(before + 0xc) : 0, after, after ? D(after + 0xc) : 0,
        caller, path, payload, payload ? B(payload + 4) : 0, payload ? B(payload + 5) : 0, seen);
}

void SoundTick() {                              // poll thread, once per second
    DWORD now = GetTickCount();
    Tracked longs[8];
    int n = 0;
    EnterCriticalSection(&g_soundLock);
    for (int i = 0; i < kTrackMax && n < 8; ++i) {
        Tracked &t = g_track[i];
        if (!t.emitter || t.longDone || now - t.tick < static_cast<DWORD>(g_soundLiveMs)) continue;
        t.longDone = 1;
        longs[n++] = t;
    }
    LeaveCriticalSection(&g_soundLock);
    for (int i = 0; i < n; ++i) {
        const Tracked &t = longs[i];
        char who[400];
        SoundOrigin(t, who, sizeof(who));
        DWORD age = now - t.tick;
        Log(kCatSound, 1, "LONG sound %lu emitter 0x%08lx still alive after %lu.%03lu s (refcount %u, flags +0x24 0x%08lx, "
                          "+0x44 0x%08lx; %s): started by %s", t.sid, t.emitter, age / 1000, age % 1000,
            W(t.emitter + 4), D(t.emitter + 0x24), D(t.emitter + 0x44), t.inList ? "in the instance list" :
            (t.kind == 1 || t.kind == 2) ? "handle released at start - nobody can stop it" : "not from an anim event", who);
    }
}

// ---------------------------------------------------------------------------------------------------------------
// [Teleport] / [Chart] F6
DWORD g_playerMachines[4];
volatile LONG g_teleUntil = 0;
bool InTeleWindow() { return static_cast<LONG>(GetTickCount()) - g_teleUntil < 0; }

int RecordIndex(DWORD machine, DWORD rec) {
    if (!rec) return -1;
    DWORD arr = D(D(machine + 4) + 0xc);
    if (!arr) return -1;
    for (int i = 0; i < 4096; ++i) {
        DWORD v = 0;
        if (!RD(arr + 4 * i, &v)) return -1;
        if (v == rec) return i;
    }
    return -1;
}

void RecordText(DWORD machine, DWORD rec, char *o, size_t n) {
    Str s = {o, n, 0};
    o[0] = 0;
    if (!rec) { s.Add("none"); return; }
    s.Add("%d [", RecordIndex(machine, rec));
    WORD count = W(rec + 0xc);
    DWORD list = D(rec + 0x18);
    for (int i = 0; i < count && i < 8 && list; ++i) s.Add("%s%u", i ? " " : "", W(list + 2 * i));
    s.Add("]");
}

void RememberMachine(DWORD m) {
    for (DWORD &x : g_playerMachines) if (x == m) return;
    for (DWORD &x : g_playerMachines) if (!x) { x = m; return; }
    g_playerMachines[3] = m;
}

bool PlayerMachine(DWORD m) {
    DWORD p = D(kPlayerPtr);
    return p && D(m + 8) == p;
}

bool ChartMoveEnter(Regs *r, DWORD *ctx) {
    DWORD m = r->ecx;
    if (!PlayerMachine(m)) return false;
    RememberMachine(m);
    ctx[0] = m;
    ctx[1] = D(m + 0x510);
    ctx[2] = (&r->ret)[1];                     // link record
    ctx[3] = r->ret;                           // caller (0x787c7d / 0x787d58 / 0x787da3 = the machine update)
    return true;
}

void ChartMoveLeave(Regs *, const DWORD *ctx) {
    DWORD m = ctx[0], now = D(m + 0x510);
    if (now == ctx[1]) return;
    char a[96], b[96];
    RecordText(m, ctx[1], a, sizeof(a));
    RecordText(m, now, b, sizeof(b));
    bool gtMachine = D(D(kGameTrackerPtr) + 0xf10) == m;
    Log(kCatChart, InTeleWindow() ? 1 : 2, "player machine 0x%08lx%s record %s -> %s (transition 0x787890, link 0x%08lx, "
        "called from 0x%08lx)%s", m, gtMachine ? " (gameTracker+0xf10)" : "", a, b, ctx[2], ctx[3],
        InTeleWindow() ? " [teleport window]" : "");
}

bool ChartResetEnter(Regs *r, DWORD *) {
    DWORD m = r->ecx;
    if (!PlayerMachine(m)) return false;
    RememberMachine(m);
    char a[96];
    RecordText(m, D(m + 0x510), a, sizeof(a));
    Log(kCatChart, 1, "player machine 0x%08lx RESET (0x7874d0, called from 0x%08lx) at record %s", m, r->ret, a);
    return false;
}

bool ChartStartEnter(Regs *r, DWORD *) {
    DWORD m = r->ecx;
    if (!PlayerMachine(m)) return false;
    RememberMachine(m);
    Log(kCatChart, 1, "player machine 0x%08lx START (0x787e00, called from 0x%08lx)", m, r->ret);
    return false;
}

struct Snap { DWORD tick, player, gt, a64, c94, iflags, ctl; float pos[3], yaw; DWORD machine[3], rec[3]; };

// 0.3.2 (P5 / P1-crash follow-up 5, docs Befund-DLC1-Absturz-Spinne-1311.md section 5: 1 190 caught AVs in 11 min at
// RD / W after a level change - the remembered machines belonged to the old player): a new player instance (level
// change, reload) forgets every remembered machine; a remembered machine whose owner +8 is not the player any more is
// dropped before its record is read
DWORD g_machinesPlayer = 0;
void TakeSnap(Snap *s) {
    memset(s, 0, sizeof(*s));
    s->tick = GetTickCount();
    s->player = D(kPlayerPtr);
    if (s->player != g_machinesPlayer) {
        if (g_machinesPlayer && (g_playerMachines[0] || g_playerMachines[1] || g_playerMachines[2] || g_playerMachines[3]))
            Log(kCatTele, 2, "player 0x%08lx -> 0x%08lx: remembered player machines cleared", g_machinesPlayer, s->player);
        for (DWORD &x : g_playerMachines) x = 0;
        g_machinesPlayer = s->player;
    }
    if (!s->player) return;
    for (DWORD &x : g_playerMachines)
        if (x && D(x + 8) != s->player) x = 0;   // no longer the player's (RD guards the read; at most one per stale entry)
    for (int i = 0; i < 3; ++i) s->pos[i] = F(s->player + 0x20 + 4 * i);
    s->yaw = F(s->player + 0x38);
    s->iflags = D(s->player + 0x14);
    s->ctl = D(kPlayerCtl);
    s->gt = D(kGameTrackerPtr);
    if (s->gt) { s->a64 = D(s->gt + 0xa64); s->c94 = D(s->gt + 0xc94); s->machine[0] = D(s->gt + 0xf10); }
    int k = 1;
    for (DWORD m : g_playerMachines)
        if (m && m != s->machine[0] && k < 3) s->machine[k++] = m;
    for (int i = 0; i < 3; ++i) if (s->machine[i]) s->rec[i] = D(s->machine[i] + 0x510);
}

void LogSnap(const char *tag, const Snap &s) {
    char text[600];
    Str o = {text, sizeof(text), 0};
    text[0] = 0;
    o.Add("%s: pos %.1f %.1f %.1f yaw %.3f; ", tag, s.pos[0], s.pos[1], s.pos[2], s.yaw);
    for (int i = 0; i < 3; ++i) {
        if (!s.machine[i]) continue;
        char r[96];
        RecordText(s.machine[i], s.rec[i], r, sizeof(r));
        o.Add("machine 0x%08lx%s record %s; ", s.machine[i], i == 0 ? " (gt+0xf10)" : "", r);
    }
    o.Add("gt+0xa64 0x%08lx, gt+0xc94 (attach box) 0x%08lx, inst+0x14 0x%08lx, [0xfada74] 0x%08lx", s.a64, s.c94, s.iflags,
          s.ctl);
    Log(kCatTele, 1, "%s", text);
}

Snap g_last;
bool g_haveLast = false;
DWORD g_teleTick = 0;
int g_teleFollow = -1;                       // next follow-up index
const DWORD kFollowMs[] = {250, 500, 1000, 2000, 3000};

void TeleportTick() {
    Snap now;
    TakeSnap(&now);
    if (!now.player) { g_haveLast = false; return; }
    if (g_haveLast && g_last.player == now.player) {
        float dx = now.pos[0] - g_last.pos[0], dy = now.pos[1] - g_last.pos[1], dz = now.pos[2] - g_last.pos[2];
        float d2 = dx * dx + dy * dy + dz * dz, lim = static_cast<float>(g_teleUnits);
        DWORD dt = now.tick - g_last.tick;
        if (d2 > lim * lim && dt <= 250) {
            InterlockedExchange(&g_teleUntil, static_cast<LONG>(now.tick + static_cast<DWORD>(g_teleWindowMs)));
            Log(kCatTele, 1, "JUMP of %.0f units in %lu ms (TeleportUnits %d) - TruMenu Zur Marke / Befreien / teleport "
                             "write instance +0x20 directly", sqrtf(d2), dt, g_teleUnits);
            LogSnap("before", g_last);
            LogSnap("after", now);
            g_teleTick = now.tick;
            g_teleFollow = 0;
        }
    }
    if (g_teleFollow >= 0 && g_teleFollow < 5 && now.tick - g_teleTick >= kFollowMs[g_teleFollow]) {
        char tag[32];
        _snprintf_s(tag, sizeof(tag), _TRUNCATE, "after +%lu ms", kFollowMs[g_teleFollow]);
        LogSnap(tag, now);
        if (++g_teleFollow >= 5) g_teleFollow = -1;
    }
    g_last = now;
    g_haveLast = true;
}

// ---------------------------------------------------------------------------------------------------------------
// [PowerMessages]
DWORD g_tspLo = 0, g_tspHi = 0;
volatile DWORD *g_tspFlags = nullptr;
struct Burst { DWORD tick, last; int n; DWORD inst[32], flags[32]; int msg; bool reported; };
Burst g_burst = {};
int g_burstNo = 0;
CRITICAL_SECTION g_burstLock;

void FindTsp() {
    HMODULE m = GetModuleHandleA("TruShadowPower.asi");
    if (!m) return;
    DWORD base = reinterpret_cast<DWORD>(m);
    DWORD pe = base + D(base + 0x3c);
    g_tspLo = base;
    g_tspHi = base + D(pe + 0x50);           // SizeOfImage
    typedef const void *(__cdecl *ApiFn)();
    ApiFn api = reinterpret_cast<ApiFn>(GetProcAddress(m, "TruShadowPowerMeterApi"));
    const void *p = api ? api() : nullptr;
    if (p && D(reinterpret_cast<DWORD>(p) + 4) >= 1) g_tspFlags = reinterpret_cast<volatile DWORD *>(D(reinterpret_cast<DWORD>(p) + 8));
}

void ReportBurstLocked() {
    if (!g_burst.n || g_burst.reported) return;
    g_burst.reported = true;
    char text[900];
    Str o = {text, sizeof(text), 0};
    text[0] = 0;
    int changed = 0;
    for (int i = 0; i < g_burst.n && i < 32; ++i) {
        DWORD f = D(g_burst.inst[i] + 0x14);
        if (f != g_burst.flags[i]) {
            o.Add("%s0x%08lx +0x14 0x%08lx -> 0x%08lx", changed++ ? "; " : "", g_burst.inst[i], g_burst.flags[i], f);
        }
    }
    Log(kCatPower, 1, "burst %d (message %s): %d receivers; 0.5 s later %d changed instance +0x14%s%s", g_burstNo,
        g_burst.msg == 1 ? "0x1f4 start" : g_burst.msg == 0 ? "0x1f5 stop" : "unknown", g_burst.n, changed,
        changed ? ": " : "", text);
}

bool WakeEnter(Regs *r, DWORD *) {
    DWORD ret = r->ret;
    if (!g_tspLo || ret < g_tspLo || ret >= g_tspHi) return false;
    DWORD inst = (&r->ret)[1], now = GetTickCount();
    int msg = -1;
    if (g_tspFlags) { DWORD f = 0; if (RD(reinterpret_cast<DWORD>(g_tspFlags), &f)) msg = (f & 1) ? 1 : 0; }
    EnterCriticalSection(&g_burstLock);
    if (!g_burst.n || now - g_burst.last > 300) {
        ReportBurstLocked();
        memset(&g_burst, 0, sizeof(g_burst));
        g_burst.tick = now;
        g_burst.msg = msg;
        ++g_burstNo;
    }
    g_burst.last = now;
    if (g_burst.n < 32) { g_burst.inst[g_burst.n] = inst; g_burst.flags[g_burst.n] = D(inst + 0x14); }
    int k = ++g_burst.n;
    int no = g_burstNo;
    LeaveCriticalSection(&g_burstLock);
    char desc[160];
    DescInst(inst, desc, sizeof(desc));
    Log(kCatPower, 1, "burst %d receiver %d (message %s, TruShadowPower wake from 0x%08lx): %s, handler +0x120 0x%08lx, "
        "query +0x11c 0x%08lx, +0x14 0x%08lx", no, k, msg == 1 ? "0x1f4" : msg == 0 ? "0x1f5" : "?", ret, desc,
        D(inst + 0x120), D(inst + 0x11c), D(inst + 0x14));
    return false;
}

void PowerTick() {
    EnterCriticalSection(&g_burstLock);
    if (g_burst.n && !g_burst.reported && GetTickCount() - g_burst.last >= 500) ReportBurstLocked();
    LeaveCriticalSection(&g_burstLock);
}

// ---------------------------------------------------------------------------------------------------------------
// [Spawn] F4 (hall02 thralls)
bool ObjectEntry(int id, DWORD *index, WORD *state, DWORD *object) {
    for (int i = 0; i < kObjectEntries; ++i) {
        DWORD e = kObjectTable + static_cast<DWORD>(i) * 0x24;
        if (static_cast<SHORT>(W(e + 0xc)) != id) continue;
        *index = static_cast<DWORD>(i);
        *state = W(e + 0xe);
        *object = D(e + 8);
        return true;
    }
    return false;
}

DWORD InstanceWithIntro(DWORD uid) {
    DWORD inst = D(kInstanceHead);
    for (int guard = 0; inst && guard < 4096; ++guard) {
        if (D(inst + 0x58) == uid) return inst;
        inst = D(inst + 8);
    }
    return 0;
}

const char *CallerName(DWORD ret) {
    switch (ret) {
    case 0x00780ac0: return "script native 0x780a70 (generator / spawner script)";
    case 0x005bd0df: return "intro wrapper 0x5bd080";
    default: return "";
    }
}

// 0.3.3 [ModelInst]: the intro / birth running on the game thread, pushed at its entry and popped at its leave; the
// drawable ctor inside it reads the innermost frame. A frame remembers the stack address of its entry: frames at or
// below a new entry / a leave are stale (a missed leave) and dropped. kind 1 intro 0x5bcc30, 2 birth 0x5bd0f0, 3
// child birth 0x5bd270
bool LooksInstance(DWORD v);
struct BirthFrame { int kind, obj; DWORD caller, uid, parent, esp, tick; };
struct BirthStack { DWORD tid; int depth; BirthFrame e[8]; };
BirthStack g_birthStack = {};
const char *const kBirthKind[] = {"-", "intro 0x5bcc30", "birth 0x5bd0f0", "child birth 0x5bd270"};

bool BirthPush(int kind, int obj, DWORD caller, DWORD uid, DWORD parent, DWORD esp) {
    if (!g_catOn[kCatModel]) return false;
    const DWORD tid = GetCurrentThreadId();
    BirthStack &s = g_birthStack;
    if (s.depth && s.tid != tid) return false;                  // births run on the game thread only
    while (s.depth && s.e[s.depth - 1].esp <= esp) --s.depth;   // stale frames (their leave was missed)
    if (s.depth >= 8) return false;
    s.tid = tid;
    BirthFrame &f = s.e[s.depth++];
    f.kind = kind;
    f.obj = obj;
    f.caller = caller;
    f.uid = uid;
    f.parent = parent;
    f.esp = esp;
    f.tick = GetTickCount();
    return true;
}
void BirthPop(DWORD esp) {                                      // esp = the entry stack address of the leaving call
    BirthStack &s = g_birthStack;
    if (s.tid != GetCurrentThreadId()) return;
    while (s.depth && s.e[s.depth - 1].esp <= esp) --s.depth;
}
// the innermost live frame above the stack address `esp` (0 = none)
const BirthFrame *BirthTop(DWORD esp) {
    BirthStack &s = g_birthStack;
    if (!s.depth || s.tid != GetCurrentThreadId()) return nullptr;
    return s.e[s.depth - 1].esp > esp ? &s.e[s.depth - 1] : nullptr;
}

bool IntroEnter(Regs *r, DWORD *ctx) {
    const DWORD *E = &r->ret;
    DWORD intro = E[1];
    int id = static_cast<int>(W(intro + 0x50));
    char name[96];
    if (!ObjectName(id, name, sizeof(name))) strcpy_s(name, sizeof(name), "?");
    // 0.3.3: the hook also runs for [ModelInst] (Spawn=0 or another object): spawn lines only for SpawnFilter
    const bool spawnLog = g_catOn[kCatSpawn] && NameMatches(name, g_spawnFilter);
    const bool pushed = BirthPush(1, id, E[0], D(intro + 0x58), 0, reinterpret_cast<DWORD>(E));
    if (!spawnLog && !pushed) return false;
    if (!spawnLog) {                          // only the birth frame: skip the instance list walk of the spawn line
        ctx[7] = 0x200;
        return true;
    }
    ctx[0] = intro;
    ctx[1] = static_cast<DWORD>(id);
    ctx[2] = D(intro + 0x58);
    ctx[3] = E[0];
    ctx[4] = B(intro + 0x72);
    ctx[5] = InstanceWithIntro(ctx[2]);
    ctx[6] = D(kInstanceFree);
    ctx[7] = (E[4] & 0xff) | (spawnLog ? 0x100 : 0) | (pushed ? 0x200 : 0);   // arg 4, spawn line, birth frame
    return true;
}

void IntroLeave(Regs *r, const DWORD *ctx) {
    if (ctx[7] & 0x200) BirthPop(reinterpret_cast<DWORD>(&r->slot));   // cdecl: &slot = the entry's &ret
    if (!(ctx[7] & 0x100)) return;
    DWORD inst = r->eax, intro = ctx[0], uid = ctx[2];
    int id = static_cast<int>(ctx[1]);
    char name[96];
    if (!ObjectName(id, name, sizeof(name))) strcpy_s(name, sizeof(name), "?");
    if (inst) {
        Log(kCatSpawn, 1, "intro %ld obj %d %s -> instance 0x%08lx at %.0f %.0f %.0f (intro record 0x%08lx, caller 0x%08lx "
            "%s)", static_cast<LONG>(uid), id, name, inst, F(inst + 0x20), F(inst + 0x24), F(inst + 0x28), intro, ctx[3],
            CallerName(ctx[3]));
        return;
    }
    DWORD index = 0, object = 0;
    WORD state = 0;
    // the code's order (tru+0x1bcc3c..): exists 0x5b3950 / save state 0x555730 / 0x555a10 -> +0x72 |= 0x80, and with
    // arg 4 == 0 refused; object lookup 0x5c1730: missing or state != 2 -> refused (no mark); object flag 0x10 -> mark +
    // refused; allocation 0x5b2ef0 empty -> print + refused (no mark)
    bool found = ObjectEntry(id, &index, &state, &object);
    bool newMark = !(ctx[4] & 0x80) && (B(intro + 0x72) & 0x80);
    bool flag10 = found && state == 2 && object && (B(D(object) + 8) & 0x10);
    char why[220];
    if (ctx[5] && !(ctx[7] & 0xff)) _snprintf_s(why, sizeof(why), _TRUNCATE, "an instance with this intro id exists (0x%08lx)",
                                             ctx[5]);
    else if (newMark && flag10) _snprintf_s(why, sizeof(why), _TRUNCATE, "object flag ([obj]+8 & 0x10)");
    else if (newMark) _snprintf_s(why, sizeof(why), _TRUNCATE, "save state check 0x555730 / 0x555a10 (marked +0x72 0x80, "
                                  "no live instance, arg 4 = 0)");
    else if (!found) _snprintf_s(why, sizeof(why), _TRUNCATE, "object %d not in the object table (not loaded)", id);
    else if (state != 2) _snprintf_s(why, sizeof(why), _TRUNCATE, "object table entry %lu state %u (needs 2 = loaded)",
                                     index, state);
    else if (!ctx[6]) _snprintf_s(why, sizeof(why), _TRUNCATE, "instance pool full (free list [0xd98d5c] empty)");
    else _snprintf_s(why, sizeof(why), _TRUNCATE, "other (+0x72 was 0x%02lx before, 0x%02x now; arg 4 = %lu)", ctx[4],
                     B(intro + 0x72), ctx[7] & 0xff);
    Log(kCatSpawn, 1, "intro %ld obj %d %s REFUSED: %s (intro record 0x%08lx, caller 0x%08lx %s)", static_cast<LONG>(uid), id,
        name, why, intro, ctx[3], CallerName(ctx[3]));
}

bool BirthCommon(Regs *r, DWORD *ctx, DWORD object, int which) {
    int id = object ? static_cast<int>(D(object + 0x14) & 0xffff) : 0;
    char name[96];
    if (!ObjectName(id, name, sizeof(name))) strcpy_s(name, sizeof(name), "?");
    const bool spawnLog = g_catOn[kCatSpawn] && NameMatches(name, g_spawnFilter);   // 0.3.3: see IntroEnter
    const DWORD a1 = (&r->ret)[1];
    const bool pushed = BirthPush(which ? 3 : 2, id, r->ret, 0, which && LooksInstance(a1) ? a1 : 0,
                                  reinterpret_cast<DWORD>(&r->ret));
    if (!spawnLog && !pushed) return false;
    ctx[0] = object;
    ctx[1] = static_cast<DWORD>(id);
    ctx[2] = r->ret;
    ctx[3] = static_cast<DWORD>(which);
    ctx[4] = D(kInstanceFree);
    ctx[5] = a1;
    ctx[6] = spawnLog ? 1 : 0;
    ctx[7] = pushed ? 1 : 0;
    return true;
}
bool BirthEnter(Regs *r, DWORD *ctx) { return BirthCommon(r, ctx, (&r->ret)[5], 0); }
bool Birth2Enter(Regs *r, DWORD *ctx) { return BirthCommon(r, ctx, (&r->ret)[2], 1); }

void BirthLeave(Regs *r, const DWORD *ctx) {
    if (ctx[7]) BirthPop(reinterpret_cast<DWORD>(&r->slot));    // 0.3.3
    if (!ctx[6]) return;
    DWORD inst = r->eax, object = ctx[0];
    int id = static_cast<int>(ctx[1]);
    char name[96];
    if (!ObjectName(id, name, sizeof(name))) strcpy_s(name, sizeof(name), "?");
    const char *fn = ctx[3] ? "0x5bd270" : "0x5bd0f0";
    if (inst) {
        Log(kCatSpawn, 1, "birth %s obj %d %s -> instance 0x%08lx at %.0f %.0f %.0f (arg 1 0x%08lx, caller 0x%08lx %s)", fn,
            id, name, inst, F(inst + 0x20), F(inst + 0x24), F(inst + 0x28), ctx[5], ctx[2], CallerName(ctx[2]));
        return;
    }
    const char *why = !object ? "no object" : (B(D(object) + 8) & 0x10) ? "object flag ([obj]+8 & 0x10)"
                    : !ctx[4] ? "instance pool full (free list [0xd98d5c] empty)" : "other";
    Log(kCatSpawn, 1, "birth %s obj %d %s REFUSED: %s (arg 1 0x%08lx, caller 0x%08lx %s)", fn, id, name, why, ctx[5], ctx[2],
        CallerName(ctx[2]));
}

// ---------------------------------------------------------------------------------------------------------------
// 0.2 helpers
char g_progFilter[16][32];                   // ProgressFilter tokens (lower case)
int g_progFilterN = 0;
BYTE g_objMatch[8192];                       // object id -> 0 unknown, 1 matches ProgressFilter, 2 not
volatile LONG g_inPlace = 0;                 // inside the player placement (its tail jump enters SAVE_SaveGame)

bool FilterMatch(const char *name) {
    if (!g_progFilterN) return true;
    for (int i = 0; i < g_progFilterN; ++i)
        if (NameMatches(name, g_progFilter[i])) return true;
    return false;
}

bool ObjMatches(int id) {
    if (id <= 0 || id >= 8192) return false;
    BYTE m = g_objMatch[id];
    if (!m) {
        char name[96];
        m = ObjectName(id, name, sizeof(name)) && FilterMatch(name) ? 1 : 2;
        g_objMatch[id] = m;
    }
    return m == 1;
}

// object id by name as tru+0x1bf770 does it (names table [0xdb94d0]: +0 count, name i at +8 + i * 8, id = i + 1;
// compare 0x82ec11 = the CRT _stricmp: __locale_changed test, 0x7fffffff on a null argument)
int ObjectIdByName(const char *want) {
    if (!g_namesOk) return 0;
    DWORD table = D(kObjNames), count = table ? D(table) : 0;
    if (!table || count > 8192) return 0;
    for (DWORD i = 0; i < count; ++i) {
        char name[96];
        if (ReadStr(D(table + 8 + i * 8), name, sizeof(name)) && _stricmp(name, want) == 0) return static_cast<int>(i + 1);
    }
    return 0;
}

// stream unit entry of an id as tru+0x1c1b50 finds it (state byte +4 = 2 and +0 = id)
DWORD UnitEntry(DWORD id) {
    if (!g_unitOk) return 0;
    for (DWORD e = kStreamUnits; e < kStreamUnitsEnd; e += kStreamUnitSize)
        if ((D(e + 4) & 0xff) == 2 && D(e) == id) return e;
    return 0;
}

void UnitText(DWORD id, char *o, size_t n) {
    char name[48];
    if (UnitName(id, name, sizeof(name))) _snprintf_s(o, n, _TRUNCATE, "%lu '%s'", id, name);
    else _snprintf_s(o, n, _TRUNCATE, "%lu (not loaded)", id);
}

// "TruMenu.asi+0x1234" / "tru.exe" for a code address
void ModuleText(DWORD a, char *o, size_t n) {
    HMODULE m = nullptr;
    char path[MAX_PATH];
    if (!GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                            reinterpret_cast<LPCSTR>(a), &m) || !m || !GetModuleFileNameA(m, path, MAX_PATH)) {
        _snprintf_s(o, n, _TRUNCATE, "unknown module");
        return;
    }
    const char *b = path;
    for (const char *p = path; *p; ++p)
        if (*p == '\\' || *p == '/') b = p + 1;
    _snprintf_s(o, n, _TRUNCATE, "%s+0x%lx", b, a - reinterpret_cast<DWORD>(m));
}

void PlayerText(char *o, size_t n) {
    DWORD p = D(kPlayerPtr);
    if (!p) { _snprintf_s(o, n, _TRUNCATE, "no player"); return; }
    char u1[64], u2[64];
    UnitText(D(p + 0xe0), u1, sizeof(u1));
    UnitText(D(kUnitId), u2, sizeof(u2));
    _snprintf_s(o, n, _TRUNCATE, "player 0x%08lx at %.1f %.1f %.1f, instance unit +0xe0 %s, current unit [0xe7f148] %s", p,
                F(p + 0x20), F(p + 0x24), F(p + 0x28), u1, u2);
}

// the fields of a game data block that decide where a (re)load puts the player
struct DataFields { bool ok; char unit[64]; DWORD cp, cp114; WORD mode; };
void ReadData(DWORD data, DataFields *f) {
    memset(f, 0, sizeof(*f));
    if (!data) return;
    f->ok = true;
    if (!ReadStr(data + 0x10, f->unit, sizeof(f->unit))) strcpy_s(f->unit, sizeof(f->unit), "");
    f->cp = D(data + 0x90);
    f->cp114 = D(data + 0x114);
    f->mode = W(data + 0x1f4);
}
void DataText(const DataFields &f, char *o, size_t n) {
    if (!f.ok) { _snprintf_s(o, n, _TRUNCATE, "none"); return; }
    _snprintf_s(o, n, _TRUNCATE, "unit '%s', checkpoint id +0x90 %lu, +0x114 %lu, mode +0x1f4 %u (placement uses %s)", f.unit,
                f.cp, f.cp114, f.mode, f.mode ? "+0x114" : "+0x90");
}

// intro list of a stream unit entry: [entry+8] unit data, [+0x74] list (+0xc count, +0x10 array of 0x90 bytes)
bool IntroList(DWORD entry, DWORD *ud, DWORD *arr, DWORD *count) {
    *ud = entry ? D(entry + 8) : 0;
    DWORD il = *ud ? D(*ud + 0x74) : 0;
    *arr = il ? D(il + 0x10) : 0;
    *count = il ? D(il + 0xc) : 0;
    return *arr && *count && *count < 20000;
}
void IntroText(DWORD arr, DWORD i, char *o, size_t n) {
    DWORD in = arr + i * 0x90;
    int obj = static_cast<int>(W(in + 0x50));
    char name[96];
    if (!ObjectName(obj, name, sizeof(name))) strcpy_s(name, sizeof(name), "?");
    _snprintf_s(o, n, _TRUNCATE, "intro #%lu id %ld obj %d %s at %.1f %.1f %.1f", i, static_cast<LONG>(D(in + 0x58)), obj,
                name, F(in), F(in + 4), F(in + 8));
}

// ---------------------------------------------------------------------------------------------------------------
// [Level]
bool RequestEnter(Regs *r, DWORD *) {
    const DWORD *E = &r->ret;
    DWORD ret = E[0], gt = E[2], done = E[3];
    char name[96], cur[96], who[160], player[260];
    if (!ReadStr(E[1], name, sizeof(name))) strcpy_s(name, sizeof(name), "?");
    if (!ReadStr(gt + 0x38, cur, sizeof(cur))) strcpy_s(cur, sizeof(cur), "");
    if (ret == kRetRequestByName) strcpy_s(who, sizeof(who), "game 0x5dfb20 (request by name, doneType 4)");
    else if (ret == kRetRequestUi) strcpy_s(who, sizeof(who), "game 0x7744b3 (gameTracker+0x38 again, doneType 10)");
    else ModuleText(ret, who, sizeof(who));
    PlayerText(player, sizeof(player));
    BYTE waiting = B(gt + 0xb9);
    char ign[120] = "";
    if (waiting)
        _snprintf_s(ign, sizeof(ign), _TRUNCATE, " - IGNORED by the game: gameTracker+0xb9 = %u (a request waits, 0x5df8da)",
                    waiting);
    Log(kCatLevel, 1, "REQUEST level change to '%s' (doneType %lu, gameTracker 0x%08lx; caller 0x%08lx %s)%s; before: "
        "gameTracker+0x38 '%s', +0xb8 %u, +0xb9 %u, +0xba %u; %s", name, done, gt, ret, who, ign, cur, B(gt + 0xb8),
        waiting, B(gt + 0xba), player);
    return false;
}

const char *LoadCaller(DWORD ret) {
    return ret == kRetLevelLoad ? "level load 0x5dded0" : ret == kRetStreamMove ? "STREAM_MoveIntoNewStreamUnit 0x5c1bf0"
                                                                              : "other caller";
}

bool StreamLoadEnter(Regs *r, DWORD *ctx) {
    const DWORD *E = &r->ret;
    ctx[0] = E[1];
    ctx[1] = E[0];
    char name[96], cur[64];
    if (!ReadStr(E[1], name, sizeof(name))) strcpy_s(name, sizeof(name), "?");
    UnitText(D(kUnitId), cur, sizeof(cur));
    Log(kCatLevel, 1, "STREAM_LevelLoadAndInit '%s' from 0x%08lx (%s); current unit before %s", name, E[0],
        LoadCaller(E[0]), cur);
    if (E[0] == kRetLevelLoad)                 // 0.3.2: a level load - the remembered player machines are stale
        for (DWORD &x : g_playerMachines) x = 0;
    return true;
}

void StreamLoadLeave(Regs *r, const DWORD *ctx) {
    DWORD e = r->eax;
    char want[96], got[48];
    if (!ReadStr(ctx[0], want, sizeof(want))) strcpy_s(want, sizeof(want), "?");
    if (!e || !ReadStr(e + 0xc, got, sizeof(got))) strcpy_s(got, sizeof(got), "?");
    Log(kCatLevel, 1, "STREAM_LevelLoadAndInit '%s' (%s) -> unit entry 0x%08lx id %lu '%s' state %u%s", want,
        LoadCaller(ctx[1]), e, e ? D(e) : 0, got, e ? B(e + 4) : 0,
        e && _stricmp(want, got) != 0 ? " - NOT the requested name" : "");
}

bool PlaceEnter(Regs *r, DWORD *ctx) {
    InterlockedIncrement(&g_inPlace);
    DWORD entry = (&r->ret)[1], ret = r->ret;
    ctx[0] = entry;
    ctx[1] = ret;
    ctx[2] = 0;
    ctx[3] = 0xffffffff;
    DataFields f;
    ReadData(D(kDataActive), &f);
    DWORD wanted = f.mode ? f.cp114 : f.cp;
    ctx[4] = wanted;
    DWORD ud = 0, arr = 0, count = 0;
    char unit[64], data[200], pick[200] = "";
    UnitText(entry ? D(entry) : 0, unit, sizeof(unit));
    DataText(f, data, sizeof(data));
    const char *how = "";
    if (IntroList(entry, &ud, &arr, &count)) {
        if (wanted) {                                    // 0x5d422f..0x5d4264: first intro with +0x58 == wanted
            how = "intro id = game data checkpoint id";
            for (DWORD i = 0; i < count; ++i)
                if (D(arr + i * 0x90 + 0x58) == wanted) { ctx[3] = i; break; }
        } else {                                         // 0x5d4266..0x5d42e1: checkpoint / invis_checkpoint intros
            how = "no checkpoint id: default checkpoint index of the unit";
            int a = ObjectIdByName("checkpoint"), b = ObjectIdByName("invis_checkpoint");
            DWORD def = W(D(D(ud + 0x70) + 0x2b4) + 8);
            for (DWORD i = 0; i < count; ++i) {
                int obj = static_cast<int>(W(arr + i * 0x90 + 0x50));
                if (!((a && obj == a) || (b && obj == b))) continue;
                ctx[3] = i;
                if (i == def) break;
            }
        }
        if (ctx[3] != 0xffffffff) {
            ctx[2] = arr + ctx[3] * 0x90;
            IntroText(arr, ctx[3], pick, sizeof(pick));
        }
    }
    if (ctx[2])
        Log(kCatLevel, 1, "PLACEMENT in unit %s (from 0x%08lx %s): game data %s -> %s: %s = the position the player gets "
            "(0x698180 copies it into the player intro)", unit, ret, ret == kRetPlaceLoad ? "after a level load" :
            ret == kRetPlaceRestore ? "restore path 0x5de480" : "", data, how, pick);
    else
        Log(kCatLevel, 1, "PLACEMENT in unit %s (from 0x%08lx %s): game data %s -> %s: NO such intro in this unit (%lu "
            "intros) - the player intro keeps its own position, then SAVE_SaveGame(0) (0x5d4330)", unit, ret,
            ret == kRetPlaceLoad ? "after a level load" : ret == kRetPlaceRestore ? "restore path 0x5de480" : "", data,
            wanted ? "intro id = game data checkpoint id" : "default checkpoint index", count);
    // the unit's checkpoint-like intros (object name contains "checkpoint"), so the log shows the choices
    if (arr && count) {
        char text[900];
        Str o = {text, sizeof(text), 0};
        text[0] = 0;
        int k = 0;
        for (DWORD i = 0; i < count && k < 12; ++i) {
            int obj = static_cast<int>(W(arr + i * 0x90 + 0x50));
            char name[96];
            if (!ObjectName(obj, name, sizeof(name)) || !NameMatches(name, "checkpoint")) continue;
            char one[200];
            IntroText(arr, i, one, sizeof(one));
            o.Add("%s%s%s", k++ ? "; " : "", one, i == ctx[3] ? " <- picked" : "");
        }
        Log(kCatLevel, 1, "PLACEMENT checkpoint intros of the unit (%d shown): %s", k, k ? text : "none");
    }
    return true;
}

void PlaceLeave(Regs *, const DWORD *ctx) {
    InterlockedDecrement(&g_inPlace);
    DWORD p = D(kPlayerPtr), pick = ctx[2];
    char player[260];
    PlayerText(player, sizeof(player));
    float d = -1.0f;
    if (p && pick) {
        float dx = F(p + 0x20) - F(pick), dy = F(p + 0x24) - F(pick + 4), dz = F(p + 0x28) - F(pick + 8);
        d = sqrtf(dx * dx + dy * dy + dz * dz);
    }
    char dist[80] = "";
    if (d >= 0.0f) _snprintf_s(dist, sizeof(dist), _TRUNCATE, ", %.1f units from the picked intro", d);
    Log(kCatLevel, 1, "PLACEMENT done: %s (intro %ld)%s", player, p ? static_cast<LONG>(D(p + 0x58)) : 0L, dist);
}

bool MoveUnitEnter(Regs *, DWORD *ctx) {
    DWORD p = D(kPlayerPtr);
    ctx[0] = D(kUnitId);
    ctx[1] = p ? D(p + 0xe0) : 0;
    char a[64], b[64], player[260];
    UnitText(ctx[0], a, sizeof(a));
    UnitText(ctx[1], b, sizeof(b));
    PlayerText(player, sizeof(player));
    Log(kCatLevel, 1, "MOVE into a new stream unit: %s -> %s (player +0xe0; 0x5dfc8e); %s", a, b, player);
    return true;
}

void MoveUnitLeave(Regs *, const DWORD *ctx) {
    char a[64];
    UnitText(D(kUnitId), a, sizeof(a));
    Log(kCatLevel, 1, "MOVE done: current unit [0xe7f148] %s (was %lu)", a, ctx[0]);
}

// ---------------------------------------------------------------------------------------------------------------
// [Portal]
bool PortalEnter(Regs *r, DWORD *) {
    const DWORD *E = &r->ret;
    DWORD inst = E[1], portal = E[2], id = D(inst + 0xe0), entry = UnitEntry(id);
    DWORD ud = entry ? D(entry + 8) : 0, head = ud ? D(ud) : 0, base = head ? D(head + 4) : 0;
    if (!base) return false;
    DWORD idx = D(portal + 0x14), rec = base + (idx << 8);
    LONG target = static_cast<SHORT>(W(rec + 0x84));
    if (target == static_cast<LONG>(id)) return false;     // 0x5d2ad3: same unit, nothing happens
    DWORD p = D(kPlayerPtr);
    bool player = p && (inst == p || D(inst + 0x218) == p);
    char from[64], to[64], recName[96], desc[160];
    UnitText(id, from, sizeof(from));
    UnitText(static_cast<DWORD>(target), to, sizeof(to));
    if (!ReadStr(rec, recName, sizeof(recName))) strcpy_s(recName, sizeof(recName), "?");
    DescInst(inst, desc, sizeof(desc));
    Log(kCatPortal, player ? 1 : 2, "HIT stream portal %lu (record 0x%08lx '%s') in unit %s to unit %s by %s at %.1f %.1f "
        "%.1f (caller 0x%08lx)", idx, rec, recName, from, to, desc, F(inst + 0x20), F(inst + 0x24), F(inst + 0x28), E[0]);
    return false;
}

// ---------------------------------------------------------------------------------------------------------------
// [Save]
bool SaveEnter(Regs *r, DWORD *ctx) {
    const DWORD *E = &r->ret;
    DWORD ret = E[0];
    ctx[0] = ret;
    ctx[1] = E[1] & 0xff;
    char who[300], a[220], b[220], player[260];
    if (ret == kRetCheckpoint) {
        DWORD cp = r->esi;
        char d[160];
        DescInst(cp, d, sizeof(d));
        _snprintf_s(who, sizeof(who), _TRUNCATE, "CHECKPOINT reached (checkpoint message handler 0x6a1a70): %s at %.1f %.1f "
                    "%.1f, unit +0xe0 %lu", d, F(cp + 0x20), F(cp + 0x24), F(cp + 0x28), D(cp + 0xe0));
    } else if (ret == kRetGameloopSave) {
        strcpy_s(who, sizeof(who), "gameloop 0x5dfba0 (no request waiting, streamFlags 0x200000), then 0x5df760(4)");
    } else if (ret == reinterpret_cast<DWORD>(&LeaveThunk) && g_inPlace > 0) {
        strcpy_s(who, sizeof(who), "the player placement found no checkpoint intro (tail jump 0x5d4330)");
    } else {
        char m[120];
        ModuleText(ret, m, sizeof(m));
        _snprintf_s(who, sizeof(who), _TRUNCATE, "0x%08lx %s", ret, m);
    }
    DataFields fa, fb;
    ReadData(D(kDataActive), &fa);
    ReadData(D(kDataBackup), &fb);
    ctx[2] = fb.cp;
    DataText(fa, a, sizeof(a));
    DataText(fb, b, sizeof(b));
    PlayerText(player, sizeof(player));
    Log(kCatSave, 1, "SAVE_SaveGame(%lu) by %s; active data %s; checkpoint copy before %s; %s", ctx[1], who, a, b, player);
    return true;
}

void SaveLeave(Regs *, const DWORD *ctx) {
    DataFields fb;
    ReadData(D(kDataBackup), &fb);
    char b[220];
    DataText(fb, b, sizeof(b));
    Log(kCatSave, 1, "SAVE_SaveGame done: checkpoint copy now %s%s", b, fb.cp != ctx[2] ? " - CHECKPOINT ID CHANGED" : "");
}

bool RestoreEnter(Regs *r, DWORD *ctx) {
    const DWORD *E = &r->ret;
    ctx[0] = E[0];
    ctx[1] = E[1];
    DataFields fa, fb;
    ReadData(D(kDataActive), &fa);
    ReadData(D(kDataBackup), &fb);
    char a[220], b[220], m[120], name[96];
    DataText(fa, a, sizeof(a));
    DataText(fb, b, sizeof(b));
    ModuleText(E[0], m, sizeof(m));
    if (!ReadStr(kGt + 0x38, name, sizeof(name))) strcpy_s(name, sizeof(name), "");
    Log(kCatSave, 1, "SAVE_RestoreGame(%lu) from 0x%08lx %s%s: restores the checkpoint copy %s (active before %s); "
        "gameTracker+0x38 '%s'", E[1], E[0], m, E[0] == 0x005de53c ? " (reload path 0x5de480)" : "", b, a, name);
    return true;
}

void RestoreLeave(Regs *r, const DWORD *ctx) {
    DataFields fa;
    ReadData(D(kDataActive), &fa);
    char a[220], name[96];
    DataText(fa, a, sizeof(a));
    if (!ReadStr(kGt + 0x38, name, sizeof(name))) strcpy_s(name, sizeof(name), "");
    Log(kCatSave, 1, "SAVE_RestoreGame(%lu) -> %u%s; active data now %s; gameTracker+0x38 now '%s' (0x556f38: the unit "
        "name of the data block)", ctx[1], r->eax & 0xff, (r->eax & 0xff) ? "" : " (load save game error)", a, name);
}

// ---------------------------------------------------------------------------------------------------------------
// [Ground] 0.3.2: what Lara stands on - the contact messages 0x1c7 / 0x1c9 / 0x1ca of the movement collision 0x5dce20
// to the player (game thread, inside INSTANCE_Post's hook); one line when the message, the contact instance (a record
// word that is an instance of the pool [0xd98f60], stride 0x2f0) or the direction of the record vector +0x10 changes,
// or Lara's z moves more than 100 units with the same contact (the 13.11. pillar: 3.4 m down on "safe ground")
const DWORD kInstPool = 0x00d98f60;
struct GroundLast { DWORD msg, owner; float n[3], z; bool have; };
GroundLast g_ground = {};
bool LooksInstance(DWORD v) {
    const DWORD pool = D(kInstPool);
    return pool && v >= pool && (v - pool) % 0x2f0 == 0 && (v - pool) / 0x2f0 < 0x1000;
}
void GroundNote(DWORD player, DWORD msg, DWORD rec) {
    if (!rec) return;
    float n[3] = {F(rec + 0x10), F(rec + 0x14), F(rec + 0x18)};
    const float len = sqrtf(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]);
    float u[3] = {0.0f, 0.0f, 0.0f};
    if (len > 1.0e-6f && len < 1.0e9f) for (int k = 0; k < 3; ++k) u[k] = n[k] / len;
    DWORD w[5], owner = 0;
    for (int k = 0; k < 5; ++k) {
        w[k] = D(rec + 0x1c + 4 * k);
        if (!owner && w[k] != player && LooksInstance(w[k])) owner = w[k];
    }
    const float z = F(player + 0x28);
    bool turned = false;
    for (int k = 0; k < 3; ++k) turned = turned || fabsf(u[k] - g_ground.n[k]) > 0.05f;
    const bool sank = g_ground.have && fabsf(z - g_ground.z) > 100.0f;
    if (g_ground.have && msg == g_ground.msg && owner == g_ground.owner && !turned && !sank) return;
    char on[160] = "terrain / no instance in the record";
    if (owner) DescInst(owner, on, sizeof(on));
    Log(kCatGround, 1, "ground: %s (message 0x%lx) on %s; record 0x%08lx vector +0x10 %.3f %.3f %.3f (unit %.3f %.3f "
        "%.3f), +0x1c..+0x2c %08lx %08lx %08lx %08lx %08lx; Lara z %.1f%s", msg == 0x1ca ? "walkable" : msg == 0x1c9 ?
        "too steep (> player data +0x100e)" : "other contact", msg, on, rec, n[0], n[1], n[2], u[0], u[1], u[2], w[0],
        w[1], w[2], w[3], w[4], z, sank ? " - z moved > 100 with the same contact" : "");
    g_ground.msg = msg;
    g_ground.owner = owner;
    for (int k = 0; k < 3; ++k) g_ground.n[k] = u[k];
    g_ground.z = z;
    g_ground.have = true;
}

// ---------------------------------------------------------------------------------------------------------------
// [ModelInst] / [NullModel] 0.3.3 (crash tru+0x1b7476, 14.11.: model DTP +0x68 -> bone table {0, NULL})
struct ModelRec {                    // one built drawable (ring; the null-model guard looks its drawable up here)
    DWORD drawable, inst, ctorRet, outer, outer2, birthCaller, birthParent, tick, nullMask;
    int obj, birthKind, birthObj, models;
};
const int kModelRecs = 1024;
ModelRec g_modelRec[kModelRecs];
int g_modelRecPos = 0;
struct ModelSeen { DWORD unit; int obj; };   // (unit, object) pairs already logged at level 1
const int kModelSeen = 1024;
ModelSeen g_modelSeen[kModelSeen];
int g_modelSeenN = 0;
struct ModelBurst { int obj, count, nulls, models; };   // the drawables of the current burst, per object
const int kModelBurst = 256;
ModelBurst g_modelBurst[kModelBurst];
int g_modelBurstN = 0;
LONG g_modelBurstTotal = 0, g_modelBurstOther = 0;
DWORD g_modelLastTick = 0;
CRITICAL_SECTION g_modelLock;
volatile LONG g_drawables = 0, g_drawNullBuilt = 0, g_nullDraws = 0, g_nullSkipped = 0;

const char *RetLookup(const RetName *t, size_t n, DWORD ret) {
    for (size_t i = 0; i < n; ++i)
        if (t[i].ret == ret) return t[i].name;
    return nullptr;
}

// the model path of 0x5b7430 (0x5b7467): segments = [dtp+0x68] ? [[dtp+0x68]+4] : [dtp+0xc]; 0 = the null read
bool ModelNull(DWORD md, DWORD *bt, DWORD *seg) {
    *bt = md ? D(md + 0x68) : 0;
    *seg = *bt ? D(*bt + 4) : (md ? D(md + 0xc) : 0);
    return !md || !*seg;
}

void ModelText(Str *o, int i, DWORD md, DWORD rmi) {
    DWORD bt = 0, seg = 0;
    const bool nul = ModelNull(md, &bt, &seg);
    const DWORD rm = md ? D(md + 0x64) : 0;
    o->Add("%s[%d] DTP 0x%08lx (word0 0x%08lx, %ld segments, +0xc 0x%08lx, bone table +0x68 0x%08lx", i ? "; " : "", i, md,
           md ? D(md) : 0, md ? static_cast<LONG>(D(md + 4)) : 0, md ? D(md + 0xc) : 0, bt);
    if (bt) o->Add(" {count %ld, segments 0x%08lx}", static_cast<LONG>(D(bt)), D(bt + 4));
    o->Add(") PCRenderModel 0x%08lx (render serial %lu, not an id) instance 0x%08lx%s", rm, rm ? D(rm + 8) : 0, rmi,
           nul ? " - NULL SEGMENTS: a draw (0x5b7430) reads [0+0x20]" : "");
}

// "instance init 0x5ba810 from birth 0x5bd0f0; inside birth 0x5bd0f0 called from 0x780ac0 (...)"
void BuiltText(const ModelRec &m, char *o, size_t n) {
    char a[160], b[220], mod[96];
    const char *nm = nullptr;
    if (m.ctorRet == kRetDrawInit) {
        nm = RetLookup(kInitCallers, sizeof(kInitCallers) / sizeof(kInitCallers[0]), m.outer);
        if (m.outer2) _snprintf_s(a, sizeof(a), _TRUNCATE, "instance init 0x5ba810 from %s (return 0x%08lx; the clone's "
                                  "caller 0x%08lx)", nm ? nm : "?", m.outer, m.outer2);
        else _snprintf_s(a, sizeof(a), _TRUNCATE, "instance init 0x5ba810 from %s (return 0x%08lx)", nm ? nm : "?", m.outer);
    } else if (m.ctorRet == kRetDrawInit2) {
        nm = RetLookup(kInit2Callers, sizeof(kInit2Callers) / sizeof(kInit2Callers[0]), m.outer);
        _snprintf_s(a, sizeof(a), _TRUNCATE, "init 0x5d07e0 from %s (return 0x%08lx)", nm ? nm : "?", m.outer);
    } else if (m.ctorRet == kRetDrawDerived) {
        _snprintf_s(a, sizeof(a), _TRUNCATE, "derived drawable ctor 0x6d0c20 (vtable 0x85d468) from 0x%08lx%s", m.outer,
                    m.outer == kRetDerivedCtor ? " (0x6d1b1b)" : "");
    } else {
        ModuleText(m.ctorRet, mod, sizeof(mod));
        _snprintf_s(a, sizeof(a), _TRUNCATE, "an unknown caller (return 0x%08lx %s)", m.ctorRet, mod);
    }
    if (m.birthKind > 0 && m.birthKind <= 3) {
        char par[160] = "";
        if (m.birthParent) {
            char d[140];
            DescInst(m.birthParent, d, sizeof(d));
            _snprintf_s(par, sizeof(par), _TRUNCATE, ", parent %s", d);
        }
        ModuleText(m.birthCaller, mod, sizeof(mod));
        _snprintf_s(b, sizeof(b), _TRUNCATE, "inside %s of obj %d called from 0x%08lx %s %s%s",
                    kBirthKind[m.birthKind], m.birthObj, m.birthCaller, mod, CallerName(m.birthCaller), par);
    } else {
        strcpy_s(b, sizeof(b), "no intro / birth hook frame on this thread");
    }
    _snprintf_s(o, n, _TRUNCATE, "%s; %s", a, b);
}

bool DrawCtorEnter(Regs *r, DWORD *ctx) {
    const DWORD *E = &r->ret;
    ctx[0] = r->ecx;                          // the drawable (this)
    ctx[1] = E[1];                            // the game instance
    ctx[2] = E[0];                            // who builds it
    DWORD outer = 0, outer2 = 0;
    if (E[0] == kRetDrawInit && E[9] == E[1]) {          // 0x5ba810(inst, ...): sub 8 + 4 pushes -> its return at E[8]
        outer = E[8];
        if (outer == 0x004d0eb3) outer2 = D(E[4] + 4);   // the clone 0x4d0e50 has an ebp frame (its ebp saved at E[4])
    } else if (E[0] == kRetDrawInit2) {
        outer = D(r->ebp + 4);                           // 0x5d07e0: push ebp / mov ebp, esp
    } else if (E[0] == kRetDrawDerived) {
        outer = E[6];                                    // 0x6d0c20: 4 pushes + the argument
    }
    ctx[3] = outer;
    ctx[4] = outer2;
    const BirthFrame *f = BirthTop(reinterpret_cast<DWORD>(E));
    ctx[5] = f ? static_cast<DWORD>(f->kind) | (static_cast<DWORD>(f->obj & 0xffff) << 8) : 0;
    ctx[6] = f ? f->caller : 0;
    ctx[7] = f ? f->parent : 0;
    return true;
}

void DrawCtorLeave(Regs *r, const DWORD *ctx) {
    const DWORD drawable = r->eax ? r->eax : ctx[0];
    DWORD inst = D(drawable + 4);
    if (!inst) inst = ctx[1];
    InterlockedIncrement(&g_drawables);
    const DWORD obj = D(inst + 0x10), list = D(obj + 0x40), rmis = D(drawable + 0x10);
    const int id = InstObjectId(inst);
    int n = static_cast<SHORT>(W(obj + 0x3a));
    if (n < 0) n = 0;
    char models[1200];
    Str o = {models, sizeof(models), 0};
    models[0] = 0;
    DWORD nullMask = 0;
    for (int i = 0; i < n && i < 16; ++i) {
        const DWORD md = D(list + 4 * static_cast<DWORD>(i));
        DWORD bt = 0, seg = 0;
        if (ModelNull(md, &bt, &seg)) nullMask |= 1u << i;
        ModelText(&o, i, md, D(rmis + 4 * static_cast<DWORD>(i)));
    }
    if (n > 16) o.Add("; ... %d more", n - 16);
    ModelRec m = {};
    m.drawable = drawable;
    m.inst = inst;
    m.ctorRet = ctx[2];
    m.outer = ctx[3];
    m.outer2 = ctx[4];
    m.birthKind = static_cast<int>(ctx[5] & 0xff);
    m.birthObj = static_cast<int>(ctx[5] >> 8);
    m.birthCaller = ctx[6];
    m.birthParent = ctx[7];
    m.tick = GetTickCount();
    m.nullMask = nullMask;
    m.obj = id;
    m.models = n;
    const DWORD unit = D(kUnitId);
    bool first = true;
    EnterCriticalSection(&g_modelLock);
    g_modelRec[g_modelRecPos] = m;
    g_modelRecPos = (g_modelRecPos + 1) % kModelRecs;
    for (int i = 0; i < g_modelSeenN && first; ++i)
        if (g_modelSeen[i].unit == unit && g_modelSeen[i].obj == id) first = false;
    if (first) {
        if (g_modelSeenN >= kModelSeen) g_modelSeenN = 0;           // full: start over (lines at level 1 again)
        g_modelSeen[g_modelSeenN].unit = unit;
        g_modelSeen[g_modelSeenN].obj = id;
        ++g_modelSeenN;
    }
    ModelBurst *b = nullptr;
    for (int i = 0; i < g_modelBurstN && !b; ++i)
        if (g_modelBurst[i].obj == id) b = &g_modelBurst[i];
    if (!b && g_modelBurstN < kModelBurst) {
        b = &g_modelBurst[g_modelBurstN++];
        b->obj = id;
        b->count = b->nulls = 0;
        b->models = n;
    }
    if (b) {
        ++b->count;
        if (nullMask) ++b->nulls;
    } else {
        ++g_modelBurstOther;
    }
    ++g_modelBurstTotal;
    g_modelLastTick = m.tick;
    LeaveCriticalSection(&g_modelLock);
    if (nullMask) InterlockedIncrement(&g_drawNullBuilt);
    char d[160], who[420];
    DescInst(inst, d, sizeof(d));
    BuiltText(m, who, sizeof(who));
    Log(kCatModel, nullMask ? 0 : first ? 1 : 2, "drawable 0x%08lx (vtable 0x%08lx) for %s at %.0f %.0f %.0f (+0x54 0x%08lx); "
        "built by %s; %d model(s): %s", drawable, D(drawable), d, F(inst + 0x20), F(inst + 0x24), F(inst + 0x28),
        D(inst + 0x54), who, n, n ? models : "none");
}

// poll thread: one summary 3 s after the last drawable of a burst (a level load, a spawn wave)
void ModelTick() {
    if (!g_modelBurstTotal || GetTickCount() - g_modelLastTick < 3000) return;
    static ModelBurst copy[kModelBurst];
    EnterCriticalSection(&g_modelLock);
    const int n = g_modelBurstN;
    memcpy(copy, g_modelBurst, sizeof(ModelBurst) * static_cast<size_t>(n));
    const LONG total = g_modelBurstTotal, other = g_modelBurstOther;
    g_modelBurstN = 0;
    g_modelBurstTotal = g_modelBurstOther = 0;
    LeaveCriticalSection(&g_modelLock);
    int nulls = 0;
    for (int i = 0; i < n; ++i) nulls += copy[i].nulls ? 1 : 0;
    Log(kCatModel, 1, "summary: %ld drawables of %d objects in the last burst (%ld of further objects not listed), %d "
        "object(s) with NULL SEGMENTS (a draw would crash at tru+0x1b7476)", total, n, other, nulls);
    char text[1600];
    Str o = {text, sizeof(text), 0};
    text[0] = 0;
    int part = 0;
    for (int i = 0; i < n; ++i) {
        char name[96];
        if (!ObjectName(copy[i].obj, name, sizeof(name))) strcpy_s(name, sizeof(name), "?");
        o.Add("%s%d %s x%d (%d models)%s", o.used ? "; " : "", copy[i].obj, name, copy[i].count, copy[i].models,
              copy[i].nulls ? " NULL SEGMENTS" : "");
        if (o.used > 1400 || i + 1 == n) {
            Log(kCatModel, 1, "summary part %d: %s", ++part, text);
            o.used = 0;
            text[0] = 0;
        }
    }
}

// [NullModel]: entry of 0x5b7430 - one line before the game dereferences [0+0x20]
__declspec(naked) void RetStub() {           // SkipNullModelDraw: CommonEnter's ret lands here, this ret returns
    __asm { ret }                             // to the caller of 0x5b7430 (cdecl: the caller removes the arguments)
}
struct NullSeen { DWORD md, drawable; LONG count; };
NullSeen g_nullSeen[16];
int g_nullSeenN = 0;

void NullModelNote(Regs *r, DWORD md, DWORD bt) {
    const DWORD *E = &r->ret;
    const DWORD ret = E[0];
    const DWORD drawable = ret == kRetModelDrawA ? r->ebx : ret == kRetModelDrawB ? r->esi : 0;
    for (int i = 0; i < g_nullSeenN; ++i) {                 // the same model / drawable again (SkipNullModelDraw=1)
        NullSeen &s = g_nullSeen[i];
        if (s.md != md || s.drawable != drawable) continue;
        if (++s.count % 1000 == 0)
            Log(kCatNull, 1, "null model draw again: DTP 0x%08lx drawable 0x%08lx, %ld times (%s)", md, drawable, s.count,
                g_skipNullDraw ? "skipped" : "not skipped");
        return;
    }
    NullSeen &s = g_nullSeen[g_nullSeenN < 16 ? g_nullSeenN++ : 15];
    s.md = md;
    s.drawable = drawable;
    s.count = 1;
    const DWORD inst = drawable ? D(drawable + 4) : 0;
    char d[160];
    if (inst && LooksInstance(inst)) DescInst(inst, d, sizeof(d));
    else _snprintf_s(d, sizeof(d), _TRUNCATE, "instance ? (drawable +4 0x%08lx, caller 0x%08lx)", inst, ret);
    const DWORD obj = LooksInstance(inst) ? D(inst + 0x10) : 0, list = obj ? D(obj + 0x40) : 0;
    int n = obj ? static_cast<SHORT>(W(obj + 0x3a)) : 0, index = -1;
    for (int i = 0; i < n && i < 64 && index < 0; ++i)
        if (D(list + 4 * static_cast<DWORD>(i)) == md) index = i;
    char model[600];
    Str o = {model, sizeof(model), 0};
    model[0] = 0;
    ModelText(&o, index < 0 ? 0 : index, md, index < 0 ? 0 : D(D(drawable + 0x10) + 4 * static_cast<DWORD>(index)));
    char built[460] = "drawable not seen built by TruTrace (built before the plugin, or another path)";
    EnterCriticalSection(&g_modelLock);
    for (int i = 0; i < kModelRecs; ++i) {
        const ModelRec &m = g_modelRec[(g_modelRecPos + kModelRecs - 1 - i) % kModelRecs];   // newest first
        if (!m.drawable || m.drawable != drawable) continue;
        char who[420];
        BuiltText(m, who, sizeof(who));
        _snprintf_s(built, sizeof(built), _TRUNCATE, "drawable built %.1f s ago by %s",
                    static_cast<double>(GetTickCount() - m.tick) / 1000.0, who);
        break;
    }
    LeaveCriticalSection(&g_modelLock);
    const DWORD wm = E[2];
    Log(kCatNull, 0, "NULL MODEL DRAW ahead: 0x5b7430 called from 0x%08lx for %s, model %d of %d: %s; bone table words "
        "%08lx %08lx %08lx %08lx %08lx %08lx %08lx %08lx; drawable 0x%08lx (vtable 0x%08lx), world matrix 0x%08lx (pos "
        "%.0f %.0f %.0f), arg 3 0x%08lx, arg 4 0x%08lx, arg 5 0x%08lx; %s; %s", ret, d, index, n, model, D(bt), D(bt + 4),
        D(bt + 8), D(bt + 0xc), D(bt + 0x10), D(bt + 0x14), D(bt + 0x18), D(bt + 0x1c), drawable, D(drawable), wm,
        F(wm + 0x30), F(wm + 0x34), F(wm + 0x38), E[3], E[4], E[5], built,
        g_skipNullDraw ? "SKIPPED (SkipNullModelDraw=1, diagnostic: the matrix state keeps old data)"
                       : "the game reads [0+0x20] next - crash expected (SkipNullModelDraw=0)");
    Flush();                                  // on the game thread, once per model: the process may end right after
}

bool ModelDrawEnter(Regs *r, DWORD *) {
    const DWORD md = (&r->ret)[1];
    DWORD bt = 0, seg = 0;
    if (!ModelNull(md, &bt, &seg)) return false;
    InterlockedIncrement(&g_nullDraws);
    NullModelNote(r, md, bt);
    if (g_skipNullDraw) {
        r->slot = reinterpret_cast<DWORD>(&RetStub);   // CommonEnter returns into RetStub instead of the trampoline
        InterlockedIncrement(&g_nullSkipped);
    }
    return false;
}

// ---------------------------------------------------------------------------------------------------------------
// [Messages]
bool PostEnter(Regs *r, DWORD *) {
    const DWORD *E = &r->ret;
    DWORD inst = E[1];
    if (g_catOn[kCatGround] && (E[2] == 0x1c7 || E[2] == 0x1c9 || E[2] == 0x1ca) && inst && inst == D(kPlayerPtr))
        GroundNote(inst, E[2], E[3]);           // 0.3.2 [Ground]
    if (!g_catOn[kCatMsg] || !ObjMatches(InstObjectId(inst))) return false;
    char d[160];
    DescInst(inst, d, sizeof(d));
    Log(kCatMsg, 1, "POST message 0x%lx (%lu) data 0x%08lx to %s, handler +0x120 0x%08lx (caller 0x%08lx)", E[2], E[2],
        E[3], d, D(inst + 0x120), E[0]);
    return false;
}

// ---------------------------------------------------------------------------------------------------------------
// polls (poll thread)
struct GtState { char name[64]; BYTE b8, b9, ba, bb; };
GtState g_gtLast;
bool g_gtHave = false;

void LevelTick() {
    GtState s = {};
    if (!ReadStr(kGt + 0x38, s.name, sizeof(s.name))) s.name[0] = 0;
    s.b8 = B(kGt + 0xb8); s.b9 = B(kGt + 0xb9); s.ba = B(kGt + 0xba); s.bb = B(kGt + 0xbb);
    if (g_gtHave && !strcmp(s.name, g_gtLast.name) && s.b8 == g_gtLast.b8 && s.b9 == g_gtLast.b9 && s.ba == g_gtLast.ba &&
        s.bb == g_gtLast.bb)
        return;
    Log(kCatLevel, 1, "gameTracker: +0x38 '%s', done type +0xb8 %u, request +0xb9 %u, +0xba %u, +0xbb %u (was '%s', %u, %u, "
        "%u, %u)", s.name, s.b8, s.b9, s.ba, s.bb, g_gtHave ? g_gtLast.name : "-", g_gtLast.b8, g_gtLast.b9, g_gtLast.ba,
        g_gtLast.bb);
    g_gtLast = s;
    g_gtHave = true;
}

struct UnitSlot { DWORD id; BYTE state; char name[48]; };
const int kUnitSlots = static_cast<int>((kStreamUnitsEnd - kStreamUnits) / kStreamUnitSize);
UnitSlot g_slots[32];
bool g_slotsHave = false;

void StreamTick() {
    for (int k = 0; k < kUnitSlots && k < 32; ++k) {
        DWORD e = kStreamUnits + static_cast<DWORD>(k) * kStreamUnitSize;
        UnitSlot s = {};
        s.id = D(e);
        s.state = B(e + 4);
        if (!ReadStr(e + 0xc, s.name, sizeof(s.name))) s.name[0] = 0;
        UnitSlot &old = g_slots[k];
        if (g_slotsHave && s.id == old.id && s.state == old.state && !strcmp(s.name, old.name)) continue;
        if (g_slotsHave || s.state)
            Log(kCatStream, 1, "stream unit slot %d: id %lu '%s' state %u%s (was id %lu '%s' state %u)", k, s.id, s.name,
                s.state, s.state == 2 ? " = loaded (0x5c1b50 / 0x5de510 test)" : "", old.id, old.name, old.state);
        old = s;
    }
    g_slotsHave = true;
}

DataFields g_saveLast[2];
bool g_saveHave = false;

void SaveTick() {
    for (int i = 0; i < 2; ++i) {
        DataFields f;
        ReadData(D(i ? kDataBackup : kDataActive), &f);
        DataFields &o = g_saveLast[i];
        if (g_saveHave && f.ok == o.ok && !strcmp(f.unit, o.unit) && f.cp == o.cp && f.cp114 == o.cp114 && f.mode == o.mode)
            continue;
        char a[220], b[220];
        DataText(f, a, sizeof(a));
        DataText(o, b, sizeof(b));
        Log(kCatSave, 1, "game data %s: %s (was %s)", i ? "checkpoint copy [0xc59268]" : "active [0xc59264]", a,
            g_saveHave ? b : "-");
        o = f;
    }
    g_saveHave = true;
}

// [Progress]: instance births / removals / flag changes of ProgressFilter objects
struct InstRec { DWORD inst, intro, f14, f18; int obj; };
const int kInstMax = 3000;
InstRec g_instA[kInstMax], g_instB[kInstMax];
InstRec *g_instPrev = g_instA, *g_instCur = g_instB;
int g_instPrevN = 0;
bool g_instHave = false;
DWORD g_instUnit = 0xffffffff;

int __cdecl InstCmp(const void *a, const void *b) {
    DWORD x = static_cast<const InstRec *>(a)->inst, y = static_cast<const InstRec *>(b)->inst;
    return x < y ? -1 : x > y ? 1 : 0;
}

void InstLine(const char *what, const InstRec &e, int level) {
    char name[96];
    if (!ObjectName(e.obj, name, sizeof(name))) strcpy_s(name, sizeof(name), "?");
    Log(kCatProg, level, "%s instance 0x%08lx obj %d %s intro %ld, +0x14 0x%08lx, +0x18 0x%08lx", what, e.inst, e.obj, name,
        static_cast<LONG>(e.intro), e.f14, e.f18);
}

void ProgressTick() {
    int n = 0;
    DWORD inst = D(kInstanceHead);
    for (int guard = 0; inst && guard < 8192 && n < kInstMax; ++guard) {
        InstRec &e = g_instCur[n++];
        e.inst = inst;
        e.intro = D(inst + 0x58);
        e.obj = InstObjectId(inst);
        e.f14 = D(inst + 0x14);
        e.f18 = D(inst + 0x18);
        inst = D(inst + 8);
    }
    qsort(g_instCur, static_cast<size_t>(n), sizeof(InstRec), InstCmp);
    DWORD unit = D(kUnitId);
    if (!g_instHave || unit != g_instUnit) {         // first look / new unit: the matching instances as a list
        char text[1000];
        Str o = {text, sizeof(text), 0};
        text[0] = 0;
        int k = 0;
        for (int i = 0; i < n; ++i) {
            if (!ObjMatches(g_instCur[i].obj)) continue;
            char name[96];
            if (!ObjectName(g_instCur[i].obj, name, sizeof(name))) strcpy_s(name, sizeof(name), "?");
            if (k < 24) o.Add("%s%s intro %ld (0x%08lx +0x14 0x%lx)", k ? "; " : "", name,
                              static_cast<LONG>(g_instCur[i].intro), g_instCur[i].inst, g_instCur[i].f14);
            ++k;
        }
        Log(kCatProg, 1, "%d instances, %d match ProgressFilter: %s", n, k, k ? text : "none");
    } else {
        int births = 0, removals = 0, i = 0, j = 0;
        bool bulk = false;
        for (int pass = 0; pass < 2; ++pass) {        // pass 0 counts, pass 1 logs
            i = j = 0;
            while (i < n || j < g_instPrevN) {
                const InstRec *c = i < n ? &g_instCur[i] : nullptr, *p = j < g_instPrevN ? &g_instPrev[j] : nullptr;
                if (c && p && c->inst == p->inst && c->intro == p->intro && c->obj == p->obj) {
                    if (pass && ObjMatches(c->obj) && (c->f14 != p->f14 || c->f18 != p->f18)) {
                        char name[96];
                        if (!ObjectName(c->obj, name, sizeof(name))) strcpy_s(name, sizeof(name), "?");
                        Log(kCatProg, 1, "FLAGS instance 0x%08lx obj %d %s intro %ld: +0x14 0x%08lx -> 0x%08lx, +0x18 "
                            "0x%08lx -> 0x%08lx", c->inst, c->obj, name, static_cast<LONG>(c->intro), p->f14, c->f14,
                            p->f18, c->f18);
                    }
                    ++i; ++j;
                } else if (c && (!p || c->inst <= p->inst)) {
                    if (pass) InstLine("BIRTH", *c, ObjMatches(c->obj) ? 1 : 2);
                    else ++births;
                    ++i;
                    if (p && c->inst == p->inst) {   // same address, other instance: the old one went
                        if (pass) InstLine("REMOVAL", *p, ObjMatches(p->obj) ? 1 : 2);
                        else ++removals;
                        ++j;
                    }
                } else {
                    if (pass) InstLine("REMOVAL", *p, ObjMatches(p->obj) ? 1 : 2);
                    else ++removals;
                    ++j;
                }
            }
            if (!pass) {
                bulk = births + removals > 64;
                if (bulk) Log(kCatProg, 1, "bulk change: %d births, %d removals in one poll (unit load / unload) - only "
                              "ProgressFilter objects at level 1", births, removals);
            }
        }
    }
    InstRec *t = g_instPrev;
    g_instPrev = g_instCur;
    g_instCur = t;
    g_instPrevN = n;
    g_instHave = true;
    g_instUnit = unit;
}

// [GameData]: changed ranges of the active save buffer; a dword that changes in 8 polls in a row is muted
BYTE *g_dataSnap = nullptr;
DWORD *g_dataLastTick = nullptr;
BYTE *g_dataStreak = nullptr;                // 255 = muted
DWORD g_dataBuf = 0, g_dataTick = 0;
LONG g_dataMuted = 0;

bool CopyGuarded(void *dst, DWORD src, size_t n) {
    __try { memcpy(dst, reinterpret_cast<const void *>(src), n); return true; }
    __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
bool SameGuarded(const BYTE *snap, DWORD live, size_t n, bool *same) {
    __try { *same = memcmp(snap, reinterpret_cast<const void *>(live), n) == 0; return true; }
    __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}

void GameDataTick() {
    if (!g_dataSnap || !g_dataLastTick || !g_dataStreak) return;
    DWORD buf = D(kSaveActive);
    if (!buf) return;
    DWORD data = D(kDataActive);
    if (buf != g_dataBuf) {
        if (!CopyGuarded(g_dataSnap, buf, kSaveSize)) return;
        g_dataBuf = buf;
        Log(kCatData, 1, "watching the active save buffer 0x%08lx (0x%lx bytes; game data block [0xc59264] at +0x%lx); lines "
            "give +offset: old -> new bytes", buf, kSaveSize, data - buf);
        return;
    }
    ++g_dataTick;
    char text[1400];
    Str o = {text, sizeof(text), 0};
    text[0] = 0;
    int ranges = 0, bytes = 0, chunks = 0;
    DWORD runStart = 0xffffffff, runEnd = 0;
    BYTE oldB[8], newB[8];
    auto flushRun = [&]() {
        if (runStart == 0xffffffff) return;
        DWORD len = runEnd - runStart;
        if (ranges < 10) {
            o.Add("%s+0x%05lx", ranges ? "; " : "", runStart);
            if (data >= buf && runStart >= data - buf && runStart < data - buf + 0x41028)
                o.Add(" (data+0x%lx)", runStart - (data - buf));
            o.Add(" %lu:", len);
            DWORD show = len < 8 ? len : 8;
            for (DWORD k = 0; k < show; ++k) o.Add(" %02x", oldB[k]);
            o.Add(" ->");
            for (DWORD k = 0; k < show; ++k) o.Add(" %02x", newB[k]);
            if (len > 8) o.Add(" ..");
        }
        ++ranges;
        runStart = 0xffffffff;
    };
    for (DWORD c = 0; c < kSaveSize; c += 64) {
        bool same = true;
        if (!SameGuarded(g_dataSnap + c, buf + c, 64, &same)) return;
        if (same) continue;
        BYTE live[64];
        if (!CopyGuarded(live, buf + c, 64)) return;
        ++chunks;
        for (DWORD w = 0; w < 64; w += 4) {
            DWORD wi = (c + w) / 4;
            bool changed = memcmp(g_dataSnap + c + w, live + w, 4) != 0;
            if (changed && g_dataStreak[wi] != 255) {
                g_dataStreak[wi] = g_dataLastTick[wi] == g_dataTick - 1 ? static_cast<BYTE>(g_dataStreak[wi] + 1) : 1;
                g_dataLastTick[wi] = g_dataTick;
                if (g_dataStreak[wi] >= 8) {
                    g_dataStreak[wi] = 255;
                    ++g_dataMuted;
                    Log(kCatData, 1, "+0x%05lx changes in every poll - muted (a clock / counter)", c + w);
                }
            }
            for (DWORD k = 0; k < 4; ++k) {
                DWORD off = c + w + k;
                bool diff = g_dataSnap[off] != live[w + k] && g_dataStreak[wi] != 255;
                if (diff) {
                    ++bytes;
                    if (runStart != 0xffffffff && off == runEnd) {
                        if (runEnd - runStart < 8) { oldB[runEnd - runStart] = g_dataSnap[off]; newB[runEnd - runStart] = live[w + k]; }
                        ++runEnd;
                    } else {
                        flushRun();
                        runStart = off;
                        runEnd = off + 1;
                        oldB[0] = g_dataSnap[off];
                        newB[0] = live[w + k];
                    }
                }
            }
        }
        memcpy(g_dataSnap + c, live, 64);
    }
    flushRun();
    if (!bytes) return;
    Log(kCatData, 1, "%d bytes in %d ranges changed%s: %s%s", bytes, ranges,
        chunks > 256 ? " (bulk: restore / level load)" : "", text, ranges > 10 ? "; .." : "");
}

// ---------------------------------------------------------------------------------------------------------------
// [Object858] NEU-4 and [TimeVector] F7
struct ObjWatch { bool known, present; DWORD index, object, data; WORD state, type; };
ObjWatch g_obj = {};

void ObjectTick() {
    ObjWatch now = {};
    now.known = true;
    WORD state = 0;
    if (ObjectEntry(g_watchObject, &now.index, &state, &now.object)) {
        now.present = true;
        now.state = state;
        now.data = now.object ? D(now.object + 0x5c) : 0;
        now.type = now.data ? W(now.data + 2) : 0;
    }
    if (g_obj.known && now.present == g_obj.present && now.index == g_obj.index && now.state == g_obj.state &&
        now.object == g_obj.object && now.data == g_obj.data && now.type == g_obj.type)
        return;
    char name[96];
    if (!ObjectName(g_watchObject, name, sizeof(name))) strcpy_s(name, sizeof(name), "?");
    if (!now.present)
        Log(kCatObj, 1, "object %d %s: not in the object table%s", g_watchObject, name,
            g_obj.present ? " (entry gone)" : "");
    else
        Log(kCatObj, 1, "object %d %s: entry %lu state %u%s, object 0x%08lx, data +0x5c 0x%08lx type %u%s (TruShadowPower "
            "needs state 2 and type 60)", g_watchObject, name, now.index, now.state, now.state == 2 ? " (loaded)" : "",
            now.object, now.data, now.type, g_obj.present && g_obj.state != now.state ? " - STATE CHANGED" : "");
    g_obj = now;
}

DWORD g_tvLastRaw = 0;
bool g_tvHave = false;
double g_tvScale = 0.001;

void TimeTick() {
    DWORD dev = D(kRenderDevicePtr);
    if (!dev) return;
    DWORD raw = D(dev + 0xfa4c), dtRaw = D(kFrameDt);
    float y = F(dev + 0xfa48), dt;
    memcpy(&dt, &dtRaw, 4);
    double x = static_cast<double>(raw % 1000000u) * g_tvScale;
    LONG delta = g_tvHave ? static_cast<LONG>(raw - g_tvLastRaw) : 0;
    Log(kCatTime, 1, "TimeVector x %.3f (+0xfa4c %lu, %+ld since the last line%s) y %.4f (+0xfa48); dt [0xe7f188] %.5f "
        "(0x%08lx), clock stop [0xdb94de] %u; device 0x%08lx", x, raw, delta, g_tvHave && delta == 0 ? " = FROZEN" : "",
        y, dt, dtRaw, B(kClockStop), dev);
    g_tvLastRaw = raw;
    g_tvHave = true;
}

// ---------------------------------------------------------------------------------------------------------------
void UnitTick() {
    static DWORD lastId = 0xffffffff;
    DWORD id = D(kUnitId);
    if (id == lastId) return;
    char name[48];
    if (!UnitName(id, name, sizeof(name))) return;
    lastId = id;
    EnterCriticalSection(&g_logLock);
    char was[48];
    strcpy_s(was, sizeof(was), g_unit);
    strcpy_s(g_unit, sizeof(g_unit), name);
    LeaveCriticalSection(&g_logLock);
    Log(kCatTrace, 1, "unit %s (was %s; stream unit id %lu)", name, was, id);
}

void Status() {
    char text[1500];
    Str o = {text, sizeof(text), 0};
    text[0] = 0;
    for (const Hook &h : g_hooks)
        if (h.on) o.Add("%s%s %ld", o.used ? ", " : "", h.name, h.calls);
    Log(kCatTrace, 1, "status: hook calls: %s; sound starts %ld, tracked ends %ld, untracked ends %ld; game data words muted "
        "%ld; enter faults %ld, leave faults %ld, shadow full %ld, unmatched leaves %ld, lines lost (buffer full) %ld", text,
        g_soundCreates, g_soundEnds, g_soundUntrackedEnds, g_dataMuted, g_enterFaults, g_leaveFaults, g_shadowFull,
        g_shadowMiss, g_bufDropped);
    if (g_catOn[kCatModel] || g_catOn[kCatNull])      // 0.3.3
        Log(kCatTrace, 1, "status 0.3.3: drawables built %ld (%ld with a NULL-segments model); null model draws %ld, "
            "skipped %ld (SkipNullModelDraw %d)", g_drawables, g_drawNullBuilt, g_nullDraws, g_nullSkipped, g_skipNullDraw);
}

volatile LONG g_stop = 0;                   // set at process detach (the thread is not waited for)

DWORD WINAPI Worker(LPVOID) {
    DWORD lastFlush = 0, lastUnit = 0, lastObj = 0, lastSec = 0, lastTime = 0, lastStatus = GetTickCount();
    DWORD lastStream = 0, lastSave = 0, lastProg = 0, lastData = 0, lastModel = 0;
    while (!g_stop) {
        Sleep(static_cast<DWORD>(g_pollMs));
        DWORD now = GetTickCount();
        __try {
            if (g_catOn[kCatTele]) TeleportTick();
            if (now - lastUnit >= 250) { lastUnit = now; UnitTick(); }
            if (g_catOn[kCatLevel]) LevelTick();
            if (g_catOn[kCatStream] && now - lastStream >= 20) { lastStream = now; StreamTick(); }
            if (g_catOn[kCatSave] && now - lastSave >= 20) { lastSave = now; SaveTick(); }
            if (g_catOn[kCatProg] && now - lastProg >= 50) { lastProg = now; ProgressTick(); }
            if (g_catOn[kCatData] && now - lastData >= static_cast<DWORD>(g_gameDataMs)) { lastData = now; GameDataTick(); }
            if (g_catOn[kCatObj] && now - lastObj >= 10) { lastObj = now; ObjectTick(); }
            if (now - lastSec >= 1000) {
                lastSec = now;
                if (g_catOn[kCatSound]) SoundTick();
            }
            if (g_catOn[kCatModel] && now - lastModel >= 500) { lastModel = now; ModelTick(); }   // 0.3.3
            if (g_catOn[kCatPower]) PowerTick();
            if (g_catOn[kCatTime] && now - lastTime >= static_cast<DWORD>(g_timeMs)) { lastTime = now; TimeTick(); }
            if (now - lastStatus >= 60000) { lastStatus = now; Status(); }
        } __except (EXCEPTION_EXECUTE_HANDLER) {
        }
        if (now - lastFlush >= 100) { lastFlush = now; Flush(); }
    }
    return 0;
}

void ReadOptions(const char *dir) {
    char ini[MAX_PATH];
    _snprintf_s(ini, sizeof(ini), _TRUNCATE, "%sTruTrace.ini", dir);
    g_enabled = GetPrivateProfileIntA("Trace", "Enabled", 1, ini);
    g_logLevel = GetPrivateProfileIntA("Trace", "LogLevel", 1, ini);
    g_maxPerSec = GetPrivateProfileIntA("Trace", "MaxLinesPerSecond", 40, ini);
    g_maxPerCat = GetPrivateProfileIntA("Trace", "MaxLinesPerCategory", 50000, ini);
    g_pollMs = GetPrivateProfileIntA("Trace", "PollMs", 5, ini);
    if (g_pollMs < 1) g_pollMs = 1;
    if (g_pollMs > 100) g_pollMs = 100;
    g_catOn[kCatSound] = GetPrivateProfileIntA("Trace", "Sound", 1, ini);
    g_soundLiveMs = GetPrivateProfileIntA("Trace", "SoundLiveMs", 4000, ini);
    g_soundRepeat = GetPrivateProfileIntA("Trace", "SoundRepeat", 3, ini);
    g_soundSlots = GetPrivateProfileIntA("Trace", "SoundSlots", 1, ini);     // 0.3
    g_catOn[kCatTele] = GetPrivateProfileIntA("Trace", "Teleport", 1, ini);
    g_teleUnits = GetPrivateProfileIntA("Trace", "TeleportUnits", 300, ini);
    g_teleWindowMs = GetPrivateProfileIntA("Trace", "TeleportWindowMs", 3000, ini);
    g_catOn[kCatChart] = GetPrivateProfileIntA("Trace", "Chart", 1, ini);
    g_catOn[kCatPower] = GetPrivateProfileIntA("Trace", "PowerMessages", 1, ini);
    g_catOn[kCatSpawn] = GetPrivateProfileIntA("Trace", "Spawn", 1, ini);
    GetPrivateProfileStringA("Trace", "SpawnFilter", "thrall", g_spawnFilter, sizeof(g_spawnFilter), ini);
    g_catOn[kCatObj] = GetPrivateProfileIntA("Trace", "Object858", 1, ini);
    g_watchObject = GetPrivateProfileIntA("Trace", "ObjectId", 858, ini);
    g_catOn[kCatTime] = GetPrivateProfileIntA("Trace", "TimeVector", 1, ini);
    g_timeMs = GetPrivateProfileIntA("Trace", "TimeVectorMs", 1000, ini);
    if (g_timeMs < 100) g_timeMs = 100;
    // 0.2
    g_catOn[kCatLevel] = GetPrivateProfileIntA("Trace", "Level", 1, ini);
    g_catOn[kCatPortal] = GetPrivateProfileIntA("Trace", "Portal", 1, ini);
    g_catOn[kCatStream] = GetPrivateProfileIntA("Trace", "StreamUnits", 1, ini);
    g_catOn[kCatSave] = GetPrivateProfileIntA("Trace", "Save", 1, ini);
    g_catOn[kCatProg] = GetPrivateProfileIntA("Trace", "Progress", 1, ini);
    g_catOn[kCatMsg] = GetPrivateProfileIntA("Trace", "Messages", 1, ini);
    g_catOn[kCatData] = GetPrivateProfileIntA("Trace", "GameData", 1, ini);
    g_catOn[kCatGround] = GetPrivateProfileIntA("Trace", "Ground", 1, ini);   // 0.3.2
    g_gameDataMs = GetPrivateProfileIntA("Trace", "GameDataMs", 250, ini);
    if (g_gameDataMs < 50) g_gameDataMs = 50;
    g_catOn[kCatModel] = GetPrivateProfileIntA("Trace", "ModelInst", 1, ini);              // 0.3.3
    g_modelMaxPerSec = GetPrivateProfileIntA("Trace", "ModelInstMaxPerSecond", 200, ini);
    if (g_modelMaxPerSec < 1) g_modelMaxPerSec = 1;
    g_catOn[kCatNull] = GetPrivateProfileIntA("Trace", "NullModelGuard", 1, ini);
    g_skipNullDraw = GetPrivateProfileIntA("Trace", "SkipNullModelDraw", 0, ini) != 0 ? 1 : 0;
    GetPrivateProfileStringA("Trace", "ProgressFilter", kProgFilterDefault, g_progFilterText, sizeof(g_progFilterText), ini);
    g_progFilterN = 0;
    for (const char *p = g_progFilterText; *p && g_progFilterN < 16;) {
        while (*p == ',' || *p == ' ') ++p;
        size_t k = 0;
        char *dst = g_progFilter[g_progFilterN];
        while (*p && *p != ',' && k + 1 < sizeof(g_progFilter[0])) dst[k++] = static_cast<char>(tolower(static_cast<unsigned char>(*p++)));
        while (*p && *p != ',') ++p;
        while (k && dst[k - 1] == ' ') --k;
        dst[k] = 0;
        if (k) ++g_progFilterN;
    }
}

void StartInner(HMODULE self);
void Start(HMODULE self) {
    StartInner(self);
    Flush();                                  // also when StartInner returned early (no poll thread then)
}

void StartInner(HMODULE self) {
    char dir[MAX_PATH];
    DWORD len = GetModuleFileNameA(self, dir, MAX_PATH);
    while (len > 0 && dir[len - 1] != '\\' && dir[len - 1] != '/') --len;
    dir[len] = 0;
    _snprintf_s(g_logPath, sizeof(g_logPath), _TRUNCATE, "%sTruTrace.log", dir);
    ReadOptions(dir);
    Log(kCatTrace, 0, "%s loaded (log only; enabled %d, log level %d, max %d lines/s and %d per category, poll %d ms; sound "
        "%d (live %d ms, repeat %d), teleport %d (%d units, window %d ms), chart %d, power messages %d, spawn %d (filter "
        "'%s'), object %d watch %d, TimeVector %d (%d ms))", kVersion, g_enabled, g_logLevel, g_maxPerSec, g_maxPerCat,
        g_pollMs, g_catOn[kCatSound], g_soundLiveMs, g_soundRepeat, g_catOn[kCatTele], g_teleUnits, g_teleWindowMs,
        g_catOn[kCatChart], g_catOn[kCatPower], g_catOn[kCatSpawn], g_spawnFilter, g_watchObject, g_catOn[kCatObj],
        g_catOn[kCatTime], g_timeMs);
    Log(kCatTrace, 0, "0.2: level %d, portal %d, stream units %d, save %d, progress %d / messages %d (filter '%s', %d "
        "tokens), game data %d (%d ms)", g_catOn[kCatLevel], g_catOn[kCatPortal], g_catOn[kCatStream], g_catOn[kCatSave],
        g_catOn[kCatProg], g_catOn[kCatMsg], g_progFilterText, g_progFilterN, g_catOn[kCatData], g_gameDataMs);
    Log(kCatTrace, 0, "0.3: sound slots %d (object sound-slot play tru+0x193d50, needs sound)", g_soundSlots);
    Log(kCatTrace, 0, "0.3.2: ground %d (the player's contact messages 0x1c7 / 0x1c9 / 0x1ca of 0x5dce20, on change)",
        g_catOn[kCatGround]);
    Log(kCatTrace, 0, "0.3.3: model inst %d (InstanceDrawable ctor tru+0x1b93e0, max %d lines/s), null model guard %d "
        "(entry of 0x5b7430), SkipNullModelDraw %d%s", g_catOn[kCatModel], g_modelMaxPerSec, g_catOn[kCatNull],
        g_skipNullDraw, g_skipNullDraw && g_catOn[kCatNull] ? " - DIAGNOSTIC: null model draws are skipped, not a fix" : "");
    if (g_skipNullDraw && !g_catOn[kCatNull]) Log(kCatTrace, 0, "SkipNullModelDraw needs NullModelGuard=1 - nothing skipped");
    if (!g_enabled) { Log(kCatTrace, 0, "disabled by TruTrace.ini - nothing hooked, no poll thread"); return; }
    DWORD base = static_cast<DWORD>(reinterpret_cast<DWORD_PTR>(GetModuleHandleA(nullptr)));
    if (base != kImageBase) { Log(kCatTrace, 0, "image base 0x%08lx, expected 0x%08lx - nothing hooked", base, kImageBase); return; }
    char exe[MAX_PATH];
    DWORD el = GetModuleFileNameA(nullptr, exe, MAX_PATH);
    if (el < 7 || _stricmp(exe + el - 7, "tru.exe") != 0 || (el > 7 && exe[el - 8] != '\\' && exe[el - 8] != '/')) {
        Log(kCatTrace, 0, "host is not tru.exe (%s) - nothing hooked (self test: TruTraceSelfTest)", exe);
        return;
    }
    // facts: a failed fact switches its category off
    bool factOk[kCatCount];
    for (int c = 0; c < kCatCount; ++c) factOk[c] = true;
    for (const Fact &f : kFacts)
        if (!HexBytesAt(f.at, f.hex)) {
            factOk[f.cat] = false;
            Log(kCatTrace, 0, "fact check 0x%08lx (%s) differs", f.at, kCatName[f.cat]);
        }
    g_namesOk = factOk[kCatTrace];
    g_unitOk = factOk[kCatTrace];
    if (!factOk[kCatTrace]) Log(kCatTrace, 0, "name / unit table code differs - names and units not shown");
    for (int c = kCatSound; c < kCatCount; ++c)
        if (g_catOn[c] && !factOk[c]) {
            g_catOn[c] = 0;
            Log(kCatTrace, 0, "%s: code facts differ - category off", kCatName[c]);
        }
    // names / units are needed for the 0.2 lines (unit names, filter); without them those categories stay quiet
    const int kNeedTables[] = {kCatLevel, kCatPortal, kCatProg, kCatMsg};
    if (!g_namesOk || !g_unitOk)
        for (int c : kNeedTables)
            if (g_catOn[c]) { g_catOn[c] = 0; Log(kCatTrace, 0, "%s: needs the name / unit tables - category off", kCatName[c]); }
    if (g_catOn[kCatData]) {
        g_dataSnap = static_cast<BYTE *>(VirtualAlloc(nullptr, kSaveSize, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
        g_dataLastTick = static_cast<DWORD *>(VirtualAlloc(nullptr, kSaveSize, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
        g_dataStreak = static_cast<BYTE *>(VirtualAlloc(nullptr, kSaveSize / 4, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
        if (!g_dataSnap || !g_dataLastTick || !g_dataStreak) {
            g_catOn[kCatData] = 0;
            Log(kCatTrace, 0, "gamedata: no memory for the snapshot - category off");
        }
    }
    g_tls = TlsAlloc();
    g_code = static_cast<BYTE *>(VirtualAlloc(nullptr, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
    if (g_tls == TLS_OUT_OF_INDEXES || !g_code) {
        Log(kCatTrace, 0, "no TLS slot / code page - nothing hooked");
        return;
    }
    FindTsp();
    // 0.3: the slot play hook has its own facts (a mismatch switches only SoundSlots off)
    g_slotFactsOk = true;
    for (const auto &f : kSlotFacts)
        if (!HexBytesAt(strtoul(f[0], nullptr, 16), f[1])) {
            g_slotFactsOk = false;
            Log(kCatSound, 0, "sound slot play: fact check 0x%s differs - SoundSlots off", f[0]);
        }
    bool want[kRealHooks], ok[kRealHooks];
    for (int i = 0; i < kRealHooks; ++i) {
        want[i] = (g_catOn[g_hooks[i].cat] != 0 || (i == kHPost && g_catOn[kCatGround]) ||    // 0.3.2: Post for [Ground]
                   ((i == kHIntro || i == kHBirth || i == kHBirth2) && g_catOn[kCatModel])) &&  // 0.3.3: birth frames
                  (i != kHSlotPlay || (g_soundSlots && g_slotFactsOk));
        ok[i] = want[i] && Install(i);            // stub + trampoline at idx * 48 (Patch finds it there)
    }
    DWORD old = 0;
    if (!VirtualProtect(g_code, 4096, PAGE_EXECUTE_READ, &old)) {
        Log(kCatTrace, 0, "code page protection failed (%lu) - nothing hooked", GetLastError());
        return;
    }
    char list[1600];
    Str o = {list, sizeof(list), 0};
    list[0] = 0;
    for (int i = 0; i < kRealHooks; ++i) {
        if (!want[i] || !ok[i]) continue;
        if (Patch(i)) o.Add("%s%s", o.used ? "; " : "", g_hooks[i].name);
        else Log(g_hooks[i].cat, 0, "%s: VirtualProtect failed (%lu) - not hooked", g_hooks[i].name, GetLastError());
    }
    Log(kCatTrace, 1, "hooks: %s", list[0] ? list : "none");
    Log(kCatTrace, 1, "TruShadowPower.asi %s (code 0x%08lx..0x%08lx, meter flags %s)", g_tspLo ? "found" : "not loaded - "
        "no power message receivers", g_tspLo, g_tspHi, g_tspFlags ? "found (0x1f4 / 0x1f5 from flag bit 0)" : "not found");
    HANDLE th = CreateThread(nullptr, 0, Worker, nullptr, 0, nullptr);
    if (th) CloseHandle(th);
    else Log(kCatTrace, 0, "poll thread not started (%lu) - teleport / object / TimeVector / LONG sound lines off",
             GetLastError());
    Flush();
}

// ---------------------------------------------------------------------------------------------------------------
// offline self test of the hook framework (TruTraceSelfTest, SelfTest.cpp): the same stubs / trampolines / leave
// thunk on the plugin's own functions with game-like prologues and calling conventions
__declspec(naked) int __cdecl T1(int, int) {          // 2a + b, prologue as tru+0x1bcc30
    __asm {
        push ebp
        mov ebp, esp
        and esp, 0xfffffff0
        mov eax, [ebp + 8]
        add eax, eax
        add eax, [ebp + 0xc]
        mov esp, ebp
        pop ebp
        ret
    }
}
__declspec(naked) void T2() {                         // thiscall(this; a, b, c) ret 0xc = this + a + b + c (as tru+0x1935d0)
    __asm {
        push ebx
        push edi
        mov edi, [esp + 0x10]
        mov eax, [esp + 0xc]
        add eax, edi
        add eax, [esp + 0x14]
        add eax, ecx
        pop edi
        pop ebx
        ret 0xc
    }
}
__declspec(naked) float __cdecl T3(float) {           // x + x in st0
    __asm {
        push ebp
        mov ebp, esp
        and esp, 0xfffffff0
        fld dword ptr [ebp + 8]
        fadd st(0), st(0)
        mov esp, ebp
        pop ebp
        ret
    }
}
__declspec(naked) int __cdecl T4(int) {               // n + T4(n - 1), T4(0) = 0 - recursion through the hook
    __asm {
        push ebp
        mov ebp, esp
        and esp, 0xfffffff0
        mov eax, [ebp + 8]
        test eax, eax
        jle done
        dec eax
        push eax
        call T4
        add esp, 4
        add eax, [ebp + 8]
    done:
        mov esp, ebp
        pop ebp
        ret
    }
}
__declspec(naked) void T5() {                         // thiscall(this; x) ret 4 = this ^ x (vtable slot)
    __asm {
        mov eax, ecx
        xor eax, [esp + 4]
        ret 4
    }
}
__declspec(naked) int __cdecl T6(int) {               // a + 1, prologue as tru+0x1d2aa0 (push ecx/ebx/ebp, mov ebp,[esp+0x10])
    __asm {
        push ecx
        push ebx
        push ebp
        mov ebp, [esp + 0x10]
        lea eax, [ebp + 1]
        pop ebp
        pop ebx
        pop ecx
        ret
    }
}
__declspec(naked) int __cdecl T7(int) {               // 2a, prologue as tru+0x157130 (sub esp; mov eax, [abs])
    __asm {
        sub esp, 0x1c
        _emit 0xa1                                    // mov eax, [0x7ffe0000] (KUSER_SHARED_DATA, readable in every
        _emit 0x00                                    // process) - emitted: the inline assembler adds a ds: prefix
        _emit 0x00
        _emit 0xfe
        _emit 0x7f
        mov eax, [esp + 0x20]
        add eax, eax
        add esp, 0x1c
        ret
    }
}
__declspec(naked) int __cdecl T9(int) {               // a + 100, prologue as tru+0x1570f0 (cmp byte [esp+4], 0)
    __asm {
        cmp byte ptr [esp + 4], 0
        jne go
        nop
    go:
        mov eax, [esp + 4]
        add eax, 100
        ret
    }
}
__declspec(naked) int __cdecl T8(int) {               // tail-jumps T9(7) as tru+0x1d40c0 jumps SAVE_SaveGame(0)
    __asm {
        sub esp, 0x10
        push ebx
        push ebp
        pop ebp
        pop ebx
        add esp, 0x10
        mov dword ptr [esp + 4], 7
        jmp T9
    }
}
__declspec(naked) int __cdecl T10(int) {              // 5a, prologue as tru+0x1df8c0 / tru+0x1b3750 (push esi; mov esi,[esp+8])
    __asm {
        push esi
        mov esi, [esp + 8]
        lea eax, [esi + esi * 4]
        pop esi
        ret
    }
}
volatile LONG g_t11Ran = 0;
__declspec(naked) int __cdecl T11(int) {              // 3a, prologue as tru+0x1b7430; g_t11Ran = 1 when the body runs
    __asm {
        push ebp
        mov ebp, esp
        and esp, 0xfffffff0
        mov dword ptr g_t11Ran, 1
        mov eax, [ebp + 8]
        lea eax, [eax + eax * 2]
        mov esp, ebp
        pop ebp
        ret
    }
}
DWORD g_testVt[1];
volatile LONG g_testEnters = 0, g_testLeaves = 0;
DWORD g_testLeaveOrder[4];
int g_testLeaveN = 0;
DWORD g_testLastArg = 0, g_testLastEcx = 0, g_testLastEax = 0;
char g_testFloatText[64];

bool TestEnter(Regs *r, DWORD *ctx) {
    InterlockedIncrement(&g_testEnters);
    g_testLastArg = (&r->ret)[1];
    g_testLastEcx = r->ecx;
    ctx[0] = g_testLastArg;
    SetLastError(0x7777);                     // the framework must restore the caller's value
    return true;
}
void TestLeave(Regs *r, const DWORD *ctx) {
    InterlockedIncrement(&g_testLeaves);
    g_testLastEax = r->eax;
    if (g_testLeaveN < 4) g_testLeaveOrder[g_testLeaveN++] = ctx[0];
    double x = static_cast<double>(ctx[0]) * 1.25 + sqrt(2.0);   // x87 / SSE use inside the hook
    _snprintf_s(g_testFloatText, sizeof(g_testFloatText), _TRUNCATE, "%.4f", x);
    SetLastError(0x8888);
}
bool TestSkipEnter(Regs *r, DWORD *) {       // 0.3.3: skip T11(4) as SkipNullModelDraw skips 0x5b7430
    InterlockedIncrement(&g_testEnters);
    if ((&r->ret)[1] == 4) {
        r->slot = reinterpret_cast<DWORD>(&RetStub);
        r->eax = 0x5151;
    }
    return false;
}

int CallT2(DWORD self, int a, int b, int c, DWORD *saved) {   // also checks ebx / esi / edi across the call
    int result = 0;
    DWORD okRegs = 0;
    __asm {
        push ebx
        push esi
        push edi
        mov ebx, 0x11111111
        mov esi, 0x22222222
        mov edi, 0x33333333
        mov ecx, self
        push c
        push b
        push a
        call T2
        mov result, eax
        xor edx, edx
        cmp ebx, 0x11111111
        jne bad
        cmp esi, 0x22222222
        jne bad
        cmp edi, 0x33333333
        jne bad
        mov edx, 1
    bad:
        mov okRegs, edx
        pop edi
        pop esi
        pop ebx
    }
    *saved = okRegs;
    return result;
}

DWORD CallT5(DWORD self, DWORD x) {
    DWORD result = 0;
    __asm {
        mov ecx, self
        push x
        mov eax, offset g_testVt
        call dword ptr [eax]
        mov result, eax
    }
    return result;
}

int RunSelfTest(char *report, int size) {
    Str o = {report, static_cast<size_t>(size > 0 ? size : 1), 0};
    report[0] = 0;
    int failed = 0;
    auto check = [&](bool ok, const char *what) {
        o.Add("%s %s\n", ok ? "PASS" : "FAIL", what);
        if (!ok) ++failed;
    };
    if (g_tls == TLS_OUT_OF_INDEXES) g_tls = TlsAlloc();
    if (!g_code) g_code = static_cast<BYTE *>(VirtualAlloc(nullptr, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
    DWORD old = 0;
    if (g_tls == TLS_OUT_OF_INDEXES || !g_code || !VirtualProtect(g_code, 4096, PAGE_READWRITE, &old)) {
        check(false, "TLS slot / code page");
        return failed;
    }
    // unhooked reference results
    DWORD regs = 0;
    int r1 = T1(3, 4), r2 = CallT2(100, 1, 2, 3, &regs), r4 = T4(5);
    float r3 = T3(1.5f);
    g_testVt[0] = reinterpret_cast<DWORD>(&T5);
    DWORD r5 = CallT5(0xf0f0, 0x0ff0);
    check(r1 == 10 && r2 == 106 && regs == 1 && r4 == 15 && r3 == 3.0f && r5 == 0xff00, "reference results unhooked");
    g_hooks[kHT1].at = reinterpret_cast<DWORD>(&T1);
    g_hooks[kHT2].at = reinterpret_cast<DWORD>(&T2);
    g_hooks[kHT3].at = reinterpret_cast<DWORD>(&T3);
    g_hooks[kHT4].at = reinterpret_cast<DWORD>(&T4);
    g_hooks[kHT5].at = reinterpret_cast<DWORD>(&g_testVt[0]);
    g_hooks[kHT5].vtOrig = reinterpret_cast<DWORD>(&T5);
    int r6 = T6(41), r7 = T7(21), r8 = T8(5), r9 = T9(1), r10 = T10(3);
    check(r6 == 42 && r7 == 42 && r8 == 107 && r9 == 101 && r10 == 15, "0.2 reference results unhooked (7-byte prologue, "
          "moffs prologue, tail jump, push esi prologue)");
    g_hooks[kHT6].at = reinterpret_cast<DWORD>(&T6);
    g_hooks[kHT7].at = reinterpret_cast<DWORD>(&T7);
    g_hooks[kHT8].at = reinterpret_cast<DWORD>(&T8);
    g_hooks[kHT9].at = reinterpret_cast<DWORD>(&T9);
    g_hooks[kHT10].at = reinterpret_cast<DWORD>(&T10);
    g_t11Ran = 0;
    int r11 = T11(5);
    check(r11 == 15 && g_t11Ran == 1, "0.3.3 reference result unhooked (prologue as tru+0x1b7430)");
    g_hooks[kHT11].at = reinterpret_cast<DWORD>(&T11);
    bool inst = true;
    for (int i = kHT1; i <= kHT11; ++i) {
        bool one = Install(i);
        if (!one) {
            BYTE *p = reinterpret_cast<BYTE *>(g_hooks[i].at);
            o.Add("  install failed: %s (first bytes %02x %02x %02x %02x %02x %02x %02x %02x)\n", g_hooks[i].name, p[0], p[1],
                  p[2], p[3], p[4], p[5], p[6], p[7]);
        }
        inst = one && inst;
    }
    VirtualProtect(g_code, 4096, PAGE_EXECUTE_READ, &old);
    for (int i = kHT1; i <= kHT11 && inst; ++i) inst = Patch(i) && inst;
    check(inst, "install + patch of the 11 test hooks (byte checks of the test prologues)");
    if (!inst) return failed;

    LONG e0 = g_testEnters, l0 = g_testLeaves;
    SetLastError(0x1234);
    int h1 = T1(3, 4);
    DWORD err = GetLastError();
    check(h1 == 10 && g_testEnters == e0 + 1 && g_testLeaves == l0 + 1 && g_testLastArg == 3 && g_testLastEax == 10,
          "cdecl: result, enter (arg 3) and leave (eax 10)");
    check(err == 0x1234, "cdecl: GetLastError of the caller kept across enter / leave");

    e0 = g_testEnters; l0 = g_testLeaves;
    int h2 = CallT2(100, 1, 2, 3, &regs);
    check(h2 == 106 && regs == 1 && g_testLastEcx == 100 && g_testLeaves == l0 + 1 && g_testLastEax == 106,
          "thiscall ret 0xc: result, ecx, ebx / esi / edi kept, leave after ret 0xc");

    l0 = g_testLeaves;
    float h3 = T3(1.5f);
    check(h3 == 3.0f && g_testLeaves == l0 + 1 && g_testFloatText[0], "float result in st0 kept while the leave hook "
          "formats a double");

    e0 = g_testEnters; l0 = g_testLeaves;
    int h4 = T4(5);
    check(h4 == 15 && g_testEnters == e0 + 6 && g_testLeaves == l0 + 6, "recursion depth 6: every level through enter + "
          "leave, results right");

    e0 = g_testEnters;
    DWORD h5 = CallT5(0xf0f0, 0x0ff0);
    check(h5 == 0xff00 && g_testEnters == e0 + 1 && g_testLastEcx == 0xf0f0 && g_testLastArg == 0x0ff0,
          "vtable slot: result, ecx and the argument seen");

    // 0.2 shapes
    e0 = g_testEnters; l0 = g_testLeaves;
    int h6 = T6(41);
    check(h6 == 42 && g_testEnters == e0 + 1 && g_testLeaves == l0 + 1 && g_testLastArg == 41 && g_testLastEax == 42,
          "7-byte prologue (push ecx / ebx / ebp, mov ebp,[esp+0x10]): result, enter, leave");
    e0 = g_testEnters; l0 = g_testLeaves;
    int h7 = T7(21);
    check(h7 == 42 && g_testEnters == e0 + 1 && g_testLeaves == l0 + 1 && g_testLastEax == 42,
          "moffs prologue (sub esp, 0x1c; mov eax, [abs]) relocated: result, enter, leave");
    e0 = g_testEnters; l0 = g_testLeaves;
    int h10 = T10(3);
    check(h10 == 15 && g_testEnters == e0 + 1 && g_testLeaves == l0 + 1 && g_testLastArg == 3,
          "push esi; mov esi,[esp+8] prologue: result, enter, leave");
    e0 = g_testEnters; l0 = g_testLeaves;
    g_testLeaveN = 0;
    int h8 = T8(5);
    check(h8 == 107 && g_testEnters == e0 + 2 && g_testLeaves == l0 + 2 && g_testLeaveN == 2 && g_testLeaveOrder[0] == 7 &&
          g_testLeaveOrder[1] == 5, "tail jump between two hooked functions: both enters, leaves target (arg 7) then "
          "caller (arg 5) on the same stack slot, result 107");
    l0 = g_testLeaves;
    bool tailAll = true;
    for (int i = 0; i < 200 && tailAll; ++i) tailAll = T8(i) == 107;
    check(tailAll && g_testLeaves == l0 + 400, "200 tail-jump pairs");

    // 0.3.3: the skip of SkipNullModelDraw (entry hook sets r->slot = a plain ret and eax; cdecl caller cleans up)
    e0 = g_testEnters;
    g_t11Ran = 0;
    SetLastError(0x4321);
    int h11 = T11(4);
    err = GetLastError();
    check(h11 == 0x5151 && g_t11Ran == 0 && g_testEnters == e0 + 1 && err == 0x4321, "skip: T11(4) returns through the "
          "plain ret with the hook's eax, body not run, GetLastError kept");
    g_t11Ran = 0;
    int h11b = T11(5);
    bool skipAll = true;
    for (int i = 0; i < 500 && skipAll; ++i) skipAll = T11(4) == 0x5151 && T11(6) == 18;
    check(h11b == 15 && g_t11Ran == 1 && skipAll, "skip hook not taken for other arguments; 500 skipped + 500 normal calls");

    Shadow *s = static_cast<Shadow *>(TlsGetValue(g_tls));
    check(s && s->depth == 0, "shadow stack empty after the calls");
    check(g_shadowMiss == 0 && g_enterFaults == 0 && g_leaveFaults == 0 && g_shadowFull == 0,
          "no unmatched leave, no fault, shadow never full");
    // 1000 calls in a row
    bool all = true;
    for (int i = 0; i < 1000 && all; ++i) all = T1(i, 1) == 2 * i + 1;
    check(all, "1000 hooked cdecl calls");
    o.Add("%d failed\n", failed);
    return failed;
}

}  // namespace

BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(instance);
        InitializeCriticalSection(&g_logLock);
        InitializeCriticalSection(&g_fileLock);
        InitializeCriticalSection(&g_soundLock);
        InitializeCriticalSection(&g_burstLock);
        InitializeCriticalSection(&g_modelLock);   // 0.3.3
        Start(instance);
    } else if (reason == DLL_PROCESS_DETACH) {
        InterlockedExchange(&g_stop, 1);
        Flush();
    }
    return TRUE;
}

// offline only: refuses inside tru.exe (returns -1); else the number of failed checks, report in `report`
extern "C" __declspec(dllexport) int __cdecl TruTraceSelfTest(char *report, int size) {
    char exe[MAX_PATH];
    DWORD el = GetModuleFileNameA(nullptr, exe, MAX_PATH);
    if (el >= 7 && _stricmp(exe + el - 7, "tru.exe") == 0) {
        if (report && size > 0) _snprintf_s(report, static_cast<size_t>(size), _TRUNCATE, "refused: runs inside tru.exe\n");
        return -1;
    }
    if (!report || size < 64) return -1;
    return RunSelfTest(report, size);
}

extern "C" __declspec(dllexport) const char *TruTraceVersion() {
    return "TruTrace 0.3.3 (log only: sound start / end F5, teleport + chart state F6, 0x1f4 / 0x1f5 receivers, spawn "
           "requests, object 858 entry, TimeVector; 0.2: level change requests, unit loads, player placement + checkpoint "
           "id, stream unit moves / portals / table, save / restore, progress instances, messages, game data changes; "
           "0.3: [Sound] SoundSlots object sound-slot play; 0.3.1: dated log lines, this export said 0.2 until 0.3.1; "
           "0.3.2: ProgressFilter default + _rw_, weightbreak, ping_map, grapple; stale player machines cleared; [Ground] "
           "the player's contact messages 0x1c7 / 0x1c9 / 0x1ca; 0.3.3: [ModelInst] drawable births with their models and "
           "who built them, [NullModel] line before the null model draw tru+0x1b7476, SkipNullModelDraw diagnostic "
           "skip, default 0)";
}
