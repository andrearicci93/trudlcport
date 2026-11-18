// TruLink.asi - live read / write channel into the running tru.exe (Steam, image base 0x400000) for our tests.
//
// A small TCP server bound to 127.0.0.1 ONLY (port from TruLink.ini, default 9265; 9264 is FMOD's profiler port)
// takes one client at a time and answers a line-based text protocol (README.md): memory reads / writes, the object
// table, the player instance, our loaded plugins, and two game functions (CAMERA_SetMode 0x5f39f0 / camera restore
// 0x5edf50, INSTANCE_Post 0x5b3750). It replaces the cdb command-file channel of the earlier debug sessions.
//
// Threads: the server thread does the socket work and the memory commands (guarded with __try / __except, ranges
// checked with VirtualQuery). Commands that call game functions are queued (one slot) and run on the game thread from
// the per-frame pad poll (tru+0x84b82, call dword ptr [0x00a02b8c] = XInputGetState), which TruShadowPower.asi and
// TruMenu.asi hook as well - the chaining rules below keep the order of the plugins irrelevant.
//
// 0.3 adds a Cheat-Engine-style value search (scan / scan next), polled watches with a change log, and struct
// snapshots with a diff - all on the server thread, so the game keeps running while they work.
//
// 0.4 adds live object inspection and manipulation (obj.near / obj.info / obj.set / obj.undo, uber.events /
// uber.send, sticky.get / sticky.set, joint.get / joint.drive): the decoders are pure memory reads shared with the
// offline dump test (TruLinkObj.h, selftest\TruLinkObjTest.cpp); every command runs as a job on the game thread,
// every write is journaled with its old value (obj.undo) and logged, and nothing runs when its byte checks failed.
//
// 0.5 adds obj.place (physics objects through the game's own placement path: INSTANCE_SetPosition 0x5b4100 + body <-
// instance 0x497740, as the game's reset / message 0x75 do), obj.refs (reverse instancerefs), base-class members and
// the physics body in obj.info, object-check conditions and all-node transitions in uber.events, the motor velocity
// in its real unit (per physics tick = 1/30 s) and joint.drive hold-until-off / joint.hold off.
//
// Every game address is checked against the expected bytes at load; on a mismatch the affected command answers
// "err" and the reason is logged. Loaded by the Ultimate ASI Loader (binkw32.dll of the installed game).

#define WIN32_LEAN_AND_MEAN
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <math.h>
#include <initializer_list>
#include "../TruLog.h"                      // Q107: date + time in every log line, session header
#include "TruLinkObj.h"                     // 0.4: object decoders (shared with selftest\TruLinkObjTest.cpp)
#include "TruLinkAct.h"                     // 0.5.1: placement / command / joint drive (shared with TruMenu 0.22.56)

#pragma comment(lib, "ws2_32.lib")

namespace {

const char kVersion[] = "0.5.3";           // 0.5.3: obj.msg (forwarded to TruMenu 0.22.61's obj.msg, the game's send 0x5b3750);
                                           // 0.5.2: puzzle.list, hinge 180 wrap in joint.drive, uber.events time text;
                                           // 0.5.1: mark.* (TruMenu notes), TruLinkAct.h shared with TruMenu; 0.5:
                                           // obj.place / obj.refs / hold-until-off; 0.4: obj / uber / sticky / joint

typedef DWORD(WINAPI *XInputGetStateFn)(DWORD, void *);
typedef void(__cdecl *CameraSetModeFn)(int mode);
typedef void(__fastcall *ThisCallFn)(void *self, int);                 // thiscall without stack arguments
typedef void(__cdecl *InstancePostFn)(void *instance, int message, int data);

const DWORD kImageBase = 0x00400000;
const DWORD kCallSite = 0x00484b82;     // ff 15 8c 2b a0 00 = call dword ptr [0x00a02b8c]
const BYTE kCallBytes[] = {0xff, 0x15, 0x8c, 0x2b, 0xa0, 0x00};
const DWORD kPadPointer = 0x00a02b8c;   // filled by the game: LoadLibraryW(L"xinput9_1_0.dll") + "XInputGetState"
const DWORD kGameClock = 0x00e7f15c;    // ms, advances once per frame (TruShadowPower)
const DWORD kGameTracker = 0x00e7f088;  // +0xc player instance, +0xbc cheatMode (TRLAU-menu-hook Game.h)
const DWORD kPlayerPtr = 0x00e7f094;    // GameTracker +0xc
const DWORD kCheatMode = 0x00e7f144;    // GameTracker +0xbc (byte)
const DWORD kPlayerState = 0x00fadb58;  // player game-state pointer (Befund-Entwicklerkanal 4)
const DWORD kCameraManager = 0x00e804f0;
const DWORD kCurrentCamera = 0x00e80534; // [mgr+0x44]; slot table [mgr+4+4*mode], modes 0..15

// CAMERA_SetMode (cdecl, mode): only 6, 11 and 12 switch anything in retail (11 = free camera, 12 = 0x5f2ba0(1),
// 6 = 0x5eb3c0); other modes return without a change
const DWORD kCameraSetMode = 0x005f39f0;
const BYTE kCameraSetModeBytes[] = {0x56, 0x8b, 0x74, 0x24, 0x08, 0x83, 0xfe, 0x06, 0x75, 0x1e, 0x81, 0x3d, 0x34,
                                    0x05, 0xe8, 0x00, 0xe0, 0xea, 0xe8, 0x00, 0x74, 0x68, 0xa1, 0xf8, 0xf3, 0xe7,
                                    0x00, 0x50, 0xb9, 0xf0, 0x04, 0xe8, 0x00};
// camera restore (thiscall CameraManager, no stack arguments; ends in jmp [[mgr+0x44]]->vfunc+8)
const DWORD kCameraRestore = 0x005edf50;
const BYTE kCameraRestoreBytes[] = {0xd9, 0x05, 0x30, 0x11, 0x84, 0x00, 0x56, 0x8b, 0xf1, 0x33, 0xc9, 0xd9, 0x5e,
                                    0x78, 0x39, 0x4e, 0x4c};
// INSTANCE_Post (cdecl instance, message, data): instance +0x120 handler called as (instance, message, data)
const DWORD kInstancePost = 0x005b3750;
const BYTE kInstancePostBytes[] = {0x56, 0x8b, 0x74, 0x24, 0x08, 0x8d, 0x86, 0x10, 0x01, 0x00, 0x00, 0x85, 0xc0,
                                   0x74, 0x22, 0x57, 0x8b, 0xbe, 0x20, 0x01, 0x00, 0x00, 0x85, 0xff, 0x74, 0x16,
                                   0x56, 0xe8, 0x70, 0xf6, 0xff, 0xff, 0x8b, 0x4c, 0x24, 0x18, 0x8b, 0x54, 0x24,
                                   0x14, 0x51, 0x52, 0x56, 0xff, 0xd7, 0x83, 0xc4, 0x10};
// object table: 0xcc entries of 0x24 bytes, +8 object, +0xc s16 id, +0xe u16 state (2 = loaded); checked through
// the lookup tru+0x14e930 that walks it (as TruShadowPower)
const DWORD kFindObject = 0x0054e930;
const BYTE kFindObjectBytes[] = {0x8b, 0x54, 0x24, 0x04, 0x33, 0xc0, 0xb9, 0x0c, 0x74, 0xdb, 0x00};
const DWORD kFindObjectLoop = 0x0054e951;
const BYTE kFindObjectLoopBytes[] = {0x83, 0xc1, 0x24, 0x3d, 0xcc, 0x00, 0x00, 0x00};
const DWORD kObjectTable = 0x00db7400;
const int kObjectCount = 0xcc;

const DWORD kMaxRead = 4096;
const DWORD kMaxWrite = 1024;

// options (TruLink.ini)
int g_enabled = 1;
int g_logLevel = 1;                     // 0 errors, 1 info + every write / game call, 2 every command, 3 debug
int g_port = 9265;
int g_allowForce = 1;                   // 0 = the "force" flag is refused
int g_timeoutMs = 5000;                 // wait for the game thread (camera / post)

char g_logPath[MAX_PATH];
CRITICAL_SECTION g_logLock;
volatile LONG g_stop = 0;
DWORD g_imageStart = 0, g_imageEnd = 0;
bool g_hookOk = false, g_cameraOk = false, g_restoreOk = false, g_postOk = false, g_tableOk = false;

void Log(int level, const char *fmt, ...) {
    if (level > g_logLevel || !g_logPath[0]) return;
    char line[1024];
    int n = TruLogStamp(line, sizeof(line));     // Q107: "YYYY-MM-DD HH:MM:SS.mmm "
    va_list ap;
    va_start(ap, fmt);
    if (n > 0) _vsnprintf_s(line + n, sizeof(line) - n, _TRUNCATE, fmt, ap);
    va_end(ap);
    EnterCriticalSection(&g_logLock);
    FILE *f = nullptr;
    if (fopen_s(&f, g_logPath, "a") == 0 && f) {
        TruLogSessionStart(f, "TruLink", kVersion);
        fputs(line, f);
        fputs("\n", f);
        fclose(f);
    }
    LeaveCriticalSection(&g_logLock);
}

bool BytesAt(DWORD address, const BYTE *expected, size_t length) {
    __try {
        return memcmp(reinterpret_cast<const void *>(address), expected, length) == 0;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

// ---- memory access ----

const DWORD kReadable = PAGE_READONLY | PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READ |
                        PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY;
const DWORD kWritable = PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY;

// Checks [address, address + length) region by region with VirtualQuery (no IsBadReadPtr). Allowed without "force":
// the tru.exe image and private memory (heap, VirtualAlloc, stacks - MEM_PRIVATE). Other modules' images and mapped
// files need "force". Writes to read-only pages are allowed in the tru.exe image (or with force): the write then goes
// through VirtualProtect. Returns nullptr when allowed, else the reason.
const char *CheckRange(DWORD address, DWORD length, bool write, bool force) {
    if (!length) return "length 0";
    if (address + length < address) return "range wraps around";
    if (force && !g_allowForce) return "force is switched off in TruLink.ini (AllowForce=0)";
    DWORD p = address, end = address + length;
    while (p < end) {
        MEMORY_BASIC_INFORMATION mbi;
        if (!VirtualQuery(reinterpret_cast<void *>(p), &mbi, sizeof(mbi))) return "VirtualQuery failed";
        if (mbi.State != MEM_COMMIT) return "not committed memory";
        if ((mbi.Protect & (PAGE_GUARD | PAGE_NOACCESS)) || !(mbi.Protect & kReadable)) return "page not readable";
        bool inImage = p >= g_imageStart && p < g_imageEnd;
        if (!force && !inImage && mbi.Type != MEM_PRIVATE)
            return "outside the tru.exe image and private memory (add 'force' to override)";
        if (write && !(mbi.Protect & kWritable) && !inImage && !force)
            return "read-only page outside the tru.exe image (add 'force' to override)";
        DWORD next = reinterpret_cast<DWORD>(mbi.BaseAddress) + static_cast<DWORD>(mbi.RegionSize);
        if (next <= p) return "VirtualQuery loop";
        p = next;
    }
    return nullptr;
}

// a guard page touched by a read (it became one after our VirtualQuery, e.g. another thread's stack) loses its guard
// flag on the fault - put it back, so that thread's stack can still grow
int ReadFaultFilter(DWORD code, EXCEPTION_POINTERS *info) {
    if (code == STATUS_GUARD_PAGE_VIOLATION && info->ExceptionRecord->NumberParameters >= 2) {
        void *page = reinterpret_cast<void *>(info->ExceptionRecord->ExceptionInformation[1]);
        MEMORY_BASIC_INFORMATION mbi;
        DWORD old = 0;
        if (VirtualQuery(page, &mbi, sizeof(mbi)) && !(mbi.Protect & PAGE_GUARD))
            VirtualProtect(page, 1, mbi.Protect | PAGE_GUARD, &old);
    }
    return EXCEPTION_EXECUTE_HANDLER;
}

bool ReadBytes(DWORD address, BYTE *out, DWORD length) {
    __try {
        memcpy(out, reinterpret_cast<const void *>(address), length);
        return true;
    } __except (ReadFaultFilter(GetExceptionCode(), GetExceptionInformation())) {
        return false;
    }
}

bool CopyGuarded(DWORD address, const BYTE *data, DWORD length) {
    __try {
        memcpy(reinterpret_cast<void *>(address), data, length);
        return true;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

// writes region by region; read-only pages (code) are opened with VirtualProtect for the copy and restored, then the
// instruction cache is flushed. Returns nullptr or the reason.
const char *WriteBytes(DWORD address, const BYTE *data, DWORD length, int *protectedRegions) {
    *protectedRegions = 0;
    DWORD p = address, end = address + length;
    while (p < end) {
        MEMORY_BASIC_INFORMATION mbi;
        if (!VirtualQuery(reinterpret_cast<void *>(p), &mbi, sizeof(mbi))) return "VirtualQuery failed";
        DWORD regionEnd = reinterpret_cast<DWORD>(mbi.BaseAddress) + static_cast<DWORD>(mbi.RegionSize);
        DWORD chunk = (regionEnd < end ? regionEnd : end) - p;
        const BYTE *src = data + (p - address);
        if (mbi.Protect & kWritable) {
            if (!CopyGuarded(p, src, chunk)) return "access fault while writing";
        } else {
            DWORD old = 0, dummy = 0;
            if (!VirtualProtect(reinterpret_cast<void *>(p), chunk, PAGE_EXECUTE_READWRITE, &old))
                return "VirtualProtect failed";
            bool ok = CopyGuarded(p, src, chunk);
            VirtualProtect(reinterpret_cast<void *>(p), chunk, old, &dummy);
            ++*protectedRegions;
            if (!ok) return "access fault while writing";
        }
        p += chunk;
    }
    FlushInstructionCache(GetCurrentProcess(), reinterpret_cast<void *>(address), length);
    return nullptr;
}

bool Read32(DWORD address, DWORD *value) {
    if (CheckRange(address, 4, false, false)) return false;
    return ReadBytes(address, reinterpret_cast<BYTE *>(value), 4);
}

// ---- game-thread job (one slot; the server handles one command at a time) ----

enum { kJobIdle = 0, kJobQueued = 1, kJobRunning = 2, kJobDone = 3 };
enum { kKindCamera = 1, kKindCameraRestore = 2, kKindPost = 3, kKindObj = 4 };
void ObjRun();                                 // 0.4: the obj / uber / sticky / joint job (section 0.4 below)
void DriveTick();                              // 0.4: joint.drive, once per pad poll on the game thread
// 0.5.1: the drive itself lives in TruLinkAct.h (shared with TruMenu 0.22.56 puzzle.hold); these names stay for the
// TruLink code (tag / end callback set in Start)
void DriveEnded(int journal);                  // 0.5.1: below (the journal row of a stopped drive)
tlact::DriveCtl g_dc = {{}, 0, "joint.drive", DriveEnded};
tlact::Drive &g_drv = g_dc.d;
volatile LONG &g_driveOn = g_dc.on;
bool g_onGameThread = false;                   // 0.4: set while a job runs (the joint getters are game-thread only)
bool g_grp[tlobj::kGrpCount];                  // 0.4: byte check groups (Start)
int g_grpRows[tlobj::kGrpCount];
int g_grpBad = -1;
DWORD g_grpFirstBad = 0;
int g_jCount = 0;                              // 0.4: journal entries in use
struct Job {
    volatile LONG state;
    int kind;
    DWORD a, b, c;
    bool faulted;
    DWORD frame;                        // game clock when it ran
};
Job g_job;
HANDLE g_jobDone = nullptr;

void RunJobBody() {
    switch (g_job.kind) {
    case kKindCamera:
        reinterpret_cast<CameraSetModeFn>(kCameraSetMode)(static_cast<int>(g_job.a));
        break;
    case kKindCameraRestore:
        reinterpret_cast<ThisCallFn>(kCameraRestore)(reinterpret_cast<void *>(kCameraManager), 0);
        break;
    case kKindPost:
        reinterpret_cast<InstancePostFn>(kInstancePost)(reinterpret_cast<void *>(g_job.a), static_cast<int>(g_job.b),
                                                        static_cast<int>(g_job.c));
        break;
    case kKindObj:
        ObjRun();
        break;
    }
}

void RunJob() {
    if (InterlockedCompareExchange(&g_job.state, kJobRunning, kJobQueued) != kJobQueued) return;
    g_job.faulted = false;
    g_job.frame = *reinterpret_cast<volatile DWORD *>(kGameClock);
    g_onGameThread = true;
    __try {
        RunJobBody();
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        g_job.faulted = true;
    }
    g_onGameThread = false;
    InterlockedExchange(&g_job.state, kJobDone);
    SetEvent(g_jobDone);
}

// 0.4: joint.drive runs once per pad poll; a fault stops the drive (the tick itself restores nothing then)
void RunDriveTick() {
    g_onGameThread = true;
    __try {
        DriveTick();
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        InterlockedExchange(&g_driveOn, 0);
        Log(0, "joint.drive: access fault in the tick (caught) - drive stopped without restore");
    }
    g_onGameThread = false;
}

// queues a job and waits; returns nullptr when it ran, else the reason
const char *CallOnGameThread(int kind, DWORD a, DWORD b, DWORD c) {
    if (!g_hookOk) return "pad poll hook not installed (see status / TruLink.log)";
    ResetEvent(g_jobDone);
    g_job.kind = kind;
    g_job.a = a; g_job.b = b; g_job.c = c;
    InterlockedExchange(&g_job.state, kJobQueued);
    if (WaitForSingleObject(g_jobDone, static_cast<DWORD>(g_timeoutMs)) != WAIT_OBJECT_0) {
        // not picked up: take it back; if the game thread just took it, wait for the end
        if (InterlockedCompareExchange(&g_job.state, kJobIdle, kJobQueued) == kJobQueued)
            return "timeout: the game thread did not poll the pad (paused / loading / hook bypassed? see status)";
        WaitForSingleObject(g_jobDone, 30000);
    }
    bool faulted = g_job.faulted;
    InterlockedExchange(&g_job.state, kJobIdle);
    return faulted ? "access fault inside the game function (caught)" : nullptr;
}

// ---- per-frame hook (pad poll) ----
//
// Chaining: the slot 0x00a02b8c holds one pointer. Every plugin saves what it finds there, puts its own hook in and
// calls the saved pointer. TruShadowPower 0.5 re-swaps whenever the slot is not its own hook, which would close a
// loop with any other plugin doing the same (A calls B calls A ...). TruLink therefore
//   1. installs itself on top of whatever is in the slot (the real XInputGetState or another plugin's hook),
//   2. re-installs only when the slot holds the real function again (the game wrote it back), never over another
//      plugin's hook - that plugin has saved TruLink's pointer and calls it,
//   3. breaks a loop: if the plugin it calls takes the slot over (it then calls TruLink), or if TruLink is re-entered
//      on the same thread, it calls the real XInputGetState (xinput9_1_0.dll, resolved by name) from then on.
// So every hook in the chain runs once per poll, whatever the load order.

volatile XInputGetStateFn g_next = nullptr;   // what TruLink calls
volatile XInputGetStateFn g_real = nullptr;   // XInputGetState itself
DWORD g_tls = TLS_OUT_OF_INDEXES;
volatile LONG g_padCalls = 0, g_frames = 0, g_reentries = 0;
volatile DWORD g_lastClock = 0, g_lastCallTick = 0;

void ModuleName(DWORD address, char *name, size_t size) {
    name[0] = 0;
    HMODULE mod = nullptr;
    if (!GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                            reinterpret_cast<LPCSTR>(address), &mod) || !mod) {
        strncpy_s(name, size, "?", _TRUNCATE);
        return;
    }
    char path[MAX_PATH];
    DWORD len = GetModuleFileNameA(mod, path, MAX_PATH);
    const char *base = path;
    for (DWORD i = 0; i < len; ++i)
        if (path[i] == '\\' || path[i] == '/') base = path + i + 1;
    strncpy_s(name, size, len ? base : "?", _TRUNCATE);
}

void ResolveReal() {
    const char *const dlls[] = {"xinput9_1_0.dll", "xinput1_4.dll", "xinput1_3.dll"};
    for (const char *dll : dlls) {
        HMODULE mod = GetModuleHandleA(dll);
        if (!mod) continue;
        FARPROC fn = GetProcAddress(mod, "XInputGetState");
        if (fn) {
            g_real = reinterpret_cast<XInputGetStateFn>(fn);
            Log(1, "XInputGetState resolved: %s 0x%08lx", dll, reinterpret_cast<DWORD>(fn));
            return;
        }
    }
}

DWORD WINAPI PadHook(DWORD index, void *state) {
    if (TlsGetValue(g_tls)) {
        // re-entered on the same thread: the chain loops back to TruLink - end it here with the real function and
        // let the outer call skip the loop from now on
        if (InterlockedIncrement(&g_reentries) == 1)
            Log(1, "pad hook re-entered (hook chain loops back to TruLink) - calling XInputGetState directly from now on");
        XInputGetStateFn real = g_real;
        if (real) g_next = real;
        return real ? real(index, state) : ERROR_DEVICE_NOT_CONNECTED;
    }
    TlsSetValue(g_tls, reinterpret_cast<void *>(1));
    XInputGetStateFn next = g_next;
    if (!next) next = g_real;
    DWORD result = next ? next(index, state) : ERROR_DEVICE_NOT_CONNECTED;
    InterlockedIncrement(&g_padCalls);
    g_lastCallTick = GetTickCount();
    DWORD clock = *reinterpret_cast<volatile DWORD *>(kGameClock);
    if (clock != g_lastClock) {
        g_lastClock = clock;
        InterlockedIncrement(&g_frames);
    }
    if (g_job.state == kJobQueued) RunJob();
    if (g_driveOn) RunDriveTick();
    TlsSetValue(g_tls, nullptr);
    return result;
}

DWORD WINAPI HookThread(LPVOID) {
    volatile LONG *slot = reinterpret_cast<volatile LONG *>(kPadPointer);
    const LONG ours = static_cast<LONG>(reinterpret_cast<LONG_PTR>(&PadHook));
    bool installed = false;
    for (int waited = 0; !g_stop; ++waited) {
        LONG current = *slot;
        if (current && !g_real) ResolveReal();
        if (current == 0) {
            if (waited == 600) Log(1, "pad pointer still empty after 60 s - still waiting");
        } else if (current != ours) {
            char name[MAX_PATH];
            ModuleName(static_cast<DWORD>(current), name, sizeof(name));
            bool isReal = _strnicmp(name, "xinput", 6) == 0 ||
                          (g_real && current == static_cast<LONG>(reinterpret_cast<LONG_PTR>(g_real)));
            if (isReal || !installed) {
                g_next = reinterpret_cast<XInputGetStateFn>(static_cast<LONG_PTR>(current));
                if (InterlockedCompareExchange(slot, ours, current) == current) {
                    Log(1, "pad pointer 0x%08lx %shooked, TruLink calls 0x%08lx (%s%s)", kPadPointer,
                        installed ? "re-" : "", current, name, isReal ? ", XInputGetState" : ", another plugin - chained");
                    installed = true;
                    g_hookOk = true;
                }
            } else if (g_real && reinterpret_cast<LONG>(g_next) == current) {
                // the plugin TruLink calls took the slot over and now calls TruLink: calling it back would loop
                g_next = g_real;
                Log(1, "pad pointer taken over by 0x%08lx (%s), which TruLink called - TruLink now calls XInputGetState "
                       "0x%08lx directly (loop avoided)", current, name, reinterpret_cast<DWORD>(g_real));
            } else {
                static LONG lastForeign = 0;
                if (lastForeign != current) {
                    lastForeign = current;
                    Log(1, "pad pointer now 0x%08lx (%s) - assumed to chain to TruLink, left in place", current, name);
                }
            }
        }
        Sleep(installed ? 500 : 100);
    }
    return 0;
}

// ---- parsing ----

bool ParseHex(const char *s, DWORD *value) {
    if (!s || !*s) return false;
    if (s[0] == '0' && (s[1] == 'x' || s[1] == 'X')) s += 2;
    if (!*s) return false;
    char *end = nullptr;
    unsigned long v = strtoul(s, &end, 16);
    if (*end) return false;
    *value = v;
    return true;
}

// "0x.." hex, otherwise decimal (signed)
bool ParseNumber(const char *s, DWORD *value) {
    if (!s || !*s) return false;
    if (s[0] == '0' && (s[1] == 'x' || s[1] == 'X')) return ParseHex(s, value);
    char *end = nullptr;
    long v = strtol(s, &end, 10);
    if (*end) {
        unsigned long u = strtoul(s, &end, 10);
        if (*end) return false;
        *value = u;
        return true;
    }
    *value = static_cast<DWORD>(v);
    return true;
}

// address: hex ("e7f144", "0xe7f144") or a name - player (the player instance [0xe7f094]), gametracker (0xe7f088),
// cheat (0xe7f144), camera (current camera [0xe80534]), cameramgr (0xe804f0), playerstate ([0xfadb58]) - with an
// optional "+hex" offset, e.g. player+0x20
bool ParseAddress(const char *s, DWORD *value, char *err, size_t errSize) {
    char base[64];
    strncpy_s(base, sizeof(base), s, _TRUNCATE);
    DWORD offset = 0;
    char *plus = strchr(base, '+');
    if (plus) {
        *plus = 0;
        if (!ParseHex(plus + 1, &offset)) { _snprintf_s(err, errSize, _TRUNCATE, "bad offset '%s'", plus + 1); return false; }
    }
    DWORD v = 0;
    struct { const char *name; DWORD address; bool pointer; } const names[] = {
        {"player", kPlayerPtr, true}, {"gametracker", kGameTracker, false}, {"cheat", kCheatMode, false},
        {"camera", kCurrentCamera, true}, {"cameramgr", kCameraManager, false}, {"playerstate", kPlayerState, true}};
    bool named = false;
    for (const auto &n : names) {
        if (_stricmp(base, n.name)) continue;
        named = true;
        v = n.address;
        if (n.pointer && !Read32(n.address, &v)) {
            _snprintf_s(err, errSize, _TRUNCATE, "cannot read the %s pointer at 0x%08lx", n.name, n.address);
            return false;
        }
        if (n.pointer && !v) { _snprintf_s(err, errSize, _TRUNCATE, "%s pointer is 0 (not in game?)", n.name); return false; }
    }
    if (!named && !ParseHex(base, &v)) { _snprintf_s(err, errSize, _TRUNCATE, "bad address '%s'", s); return false; }
    *value = v + offset;
    return true;
}

// ---- answers ----

struct Out {
    char buf[262144];                                          // 0.4: 256 KB (obj.info of a big uber graph)
    size_t n;
    void Reset() { n = 0; buf[0] = 0; }
    void Add(const char *fmt, ...) {
        if (n >= sizeof(buf) - 1) return;
        va_list ap;
        va_start(ap, fmt);
        int w = _vsnprintf_s(buf + n, sizeof(buf) - n, _TRUNCATE, fmt, ap);
        va_end(ap);
        n = w < 0 ? strlen(buf) : n + static_cast<size_t>(w);
    }
};
Out g_out;

void AddHex(const BYTE *data, DWORD length) {
    for (DWORD i = 0; i < length; ++i) g_out.Add("%02x", data[i]);
}

int ModeOfCamera(DWORD camera) {
    for (int mode = 0; mode < 16; ++mode) {
        DWORD slot = 0;
        if (Read32(kCameraManager + 4 + 4 * mode, &slot) && slot == camera && camera) return mode;
    }
    return -1;
}

void CmdHelp() {
    g_out.Add("ok+ help\n"
              "ping                          -> pong TruLink <version>\n"
              "status                        hook / chain / code checks (block)\n"
              "read <addr> <len> [force]     hex bytes (len <= 4096)\n"
              "read32 <addr> | readf <addr>  dword (hex + signed) | float\n"
              "write <addr> <hexbytes> [force]      e.g. write cheat 01 (answer names the old bytes)\n"
              "write32 <addr> <value> [force] | writef <addr> <float> [force]\n"
              "player                        player instance + position (+0x20)\n"
              "camera                        current camera + mode | camera <mode> | camera restore (game thread)\n"
              "post <instance> <msg> <data>  INSTANCE_Post on the game thread (instance may be 'player')\n"
              "objects                       object table 0xdb7400: index id state object (block)\n"
              "modules                       loaded .asi plugins + versions (block)\n"
              "menu list | menu <id> [arg]   TruMenu items: list (block) | run one by id (ok / err line)\n"
              "scan <type> eq|ne|gt|lt <v> | range <lo> <hi> | unknown [tol x] [align 1|2|4] [at <addr> <len>]\n"
              "                              first scan of writable memory; types u8 s8 u16 s16 u32 s32 float\n"
              "scan next eq|ne|gt|lt <v> | range <lo> <hi> | changed | unchanged | increased | decreased |\n"
              "          inc_by <v> | dec_by <v> [tol x]   refine the candidate set\n"
              "scan list [n] | scan status | scan clear | scan regions [n]\n"
              "watch add <addr> <type> [name] | watch del <name|#i|addr|all> | watch list | watch log [n]\n"
              "snapshot <name> <addr> <len> | snapshot <name> (again) | snapshot list | snapshot del <name>\n"
              "diff <name> [update]          changed dwords since the snapshot (block)\n"
              "obj.near [m] [filter|uber|multi] [max n]   instances near Lara (block; default 10 m, ~290 units/m)\n"
              "obj.info <id>                 everything readable: pos / rot / flags / intro / script members / links / "
              "joints / commands / uber graph\n"
              "obj.set <id> pos x y z | move dx dy dz | rot x y z (deg) | yaw deg | hide 0|1   (collide / scale: refused)\n"
              "obj.place <id> near-lara [m] | at <x y z> | onto <id> [dz]  [yaw deg] [force]   physics objects (body +0x274)\n"
              "obj.refs <id>                 every instance whose script members hold an instanceref to <id> (block)\n"
              "obj.msg <id> <msg> [<arg id>|0]   one game message through 0x5b3750 (needs TruMenu 0.22.61; cheat)\n"
              "obj.journal [clear] | obj.undo [all]   every write with its old value; undo the last one / all\n"
              "uber.events <id> [all]        current node (all: every node): transitions, object checks; links; commands\n"
              "uber.send <id> cmd <n> | command <c> | event <v> | broadcast <v> [link k] [force]   the game's path\n"
              "sticky.get <owner> <key|m<i>|+<off>> | sticky.set [int|bool|float] <owner> <key|m<i>|+<off>> <value>\n"
              "joint.get <id> <index> | joint.drive <id> <index> <target> [speed s] [force f] [hold s | hold-until-off] [through 1]\n"
              "joint.drive stop | status | joint.hold off   (speed: deg/s or units/s; the motor runs per 1/30 s tick)\n"
              "id: intro id | 0x<instance> | #<list index> | player   (all object commands run on the game thread)\n"
              "mark.note <intro> [+keep] [+names] <text...>   a note line under TruMenu's label of <intro> (needs TruMenu\n"
              "                              0.22.56; +keep = over a level load, +names = only with object names on)\n"
              "mark.clear [<intro>|all] | mark.list | mark.refs <id>   (refs: a note '<- <id> <member>' on every referrer)\n"
              "puzzle.list [de|en]           TruMenu's 'Puzzles nearby' rows (needs TruMenu 0.22.57): name, state, count,\n"
              "                              action (run it with menu <item> <argument>)\n"
              "log <0-3>                    TruLink.log level\n"
              "quit                          close the connection\n"
              "addr: hex or player | gametracker | cheat | camera | cameramgr | playerstate, optional +hexoffset\n"
              ".\n");
}

void CmdStatus() {
    DWORD slot = 0;
    Read32(kPadPointer, &slot);
    char slotName[MAX_PATH], nextName[MAX_PATH];
    ModuleName(slot, slotName, sizeof(slotName));
    ModuleName(reinterpret_cast<DWORD>(g_next), nextName, sizeof(nextName));
    DWORD since = g_lastCallTick ? GetTickCount() - g_lastCallTick : 0xffffffff;
    g_out.Add("ok+ status\n");
    g_out.Add("version %s port %d loglevel %d force %d timeout %d ms\n", kVersion, g_port, g_logLevel, g_allowForce,
              g_timeoutMs);
    g_out.Add("hook %s slot 0x%08lx (%s) next 0x%08lx (%s) real 0x%08lx self 0x%08lx\n", g_hookOk ? "on" : "off", slot,
              slotName, reinterpret_cast<DWORD>(g_next), nextName, reinterpret_cast<DWORD>(g_real),
              reinterpret_cast<DWORD>(&PadHook));
    g_out.Add("pad calls %ld frames %ld last call %ld ms ago reentries %ld\n", g_padCalls, g_frames,
              since == 0xffffffff ? -1L : static_cast<long>(since), g_reentries);
    g_out.Add("checks camera %d restore %d post %d objects %d image 0x%08lx-0x%08lx\n", g_cameraOk, g_restoreOk,
              g_postOk, g_tableOk, g_imageStart, g_imageEnd);
    g_out.Add("0.5 checks (%d rows, %d bad, first bad 0x%08lx):", tlobj::kTlCheckCount, g_grpBad, g_grpFirstBad);
    for (int g = 0; g < tlobj::kGrpCount; ++g) g_out.Add(" %s %d", tlobj::kGrpNames[g], g_grp[g] ? 1 : 0);
    g_out.Add("\njournal %d entries, joint.drive %s\n", g_jCount, g_driveOn ? "running" : "idle");
    g_out.Add(".\n");
}

void CmdRead(char **tok, int count, bool force) {
    char err[128];
    DWORD address = 0, length = 0;
    if (count < 3 || !ParseAddress(tok[1], &address, err, sizeof(err))) {
        g_out.Add("err %s\n", count < 3 ? "usage: read <addr> <len> [force]" : err);
        return;
    }
    if (!ParseNumber(tok[2], &length) || !length || length > kMaxRead) { g_out.Add("err len 1..%lu\n", kMaxRead); return; }
    const char *why = CheckRange(address, length, false, force);
    if (why) { g_out.Add("err 0x%08lx: %s\n", address, why); return; }
    static BYTE data[kMaxRead];
    if (!ReadBytes(address, data, length)) { g_out.Add("err 0x%08lx: access fault (caught)\n", address); return; }
    g_out.Add("ok 0x%08lx %lu ", address, length);
    AddHex(data, length);
    g_out.Add("\n");
}

void CmdRead32(char **tok, int count, bool force, bool asFloat) {
    char err[128];
    DWORD address = 0, value = 0;
    if (count < 2 || !ParseAddress(tok[1], &address, err, sizeof(err))) {
        g_out.Add("err %s\n", count < 2 ? "usage: read32|readf <addr> [force]" : err);
        return;
    }
    const char *why = CheckRange(address, 4, false, force);
    if (why) { g_out.Add("err 0x%08lx: %s\n", address, why); return; }
    if (!ReadBytes(address, reinterpret_cast<BYTE *>(&value), 4)) { g_out.Add("err 0x%08lx: access fault (caught)\n", address); return; }
    if (asFloat) {
        float f;
        memcpy(&f, &value, 4);
        g_out.Add("ok 0x%08lx %.9g 0x%08lx\n", address, static_cast<double>(f), value);
    } else {
        g_out.Add("ok 0x%08lx 0x%08lx %ld\n", address, value, static_cast<long>(value));
    }
}

void DoWrite(DWORD address, const BYTE *data, DWORD length, bool force) {
    const char *why = CheckRange(address, length, true, force);
    if (why) { g_out.Add("err 0x%08lx: %s\n", address, why); return; }
    static BYTE old[kMaxWrite];
    if (!ReadBytes(address, old, length)) { g_out.Add("err 0x%08lx: access fault (caught)\n", address); return; }
    int protectedRegions = 0;
    why = WriteBytes(address, data, length, &protectedRegions);
    if (why) { g_out.Add("err 0x%08lx: %s\n", address, why); Log(0, "write 0x%08lx (%lu bytes) failed: %s", address, length, why); return; }
    g_out.Add("ok wrote %lu at 0x%08lx%s was ", length, address, protectedRegions ? " (VirtualProtect)" : "");
    AddHex(old, length);
    g_out.Add("\n");
    Log(1, "write 0x%08lx %lu bytes%s%s", address, length, protectedRegions ? " (code page, VirtualProtect)" : "",
        force ? " FORCE" : "");
}

void CmdWrite(char **tok, int count, bool force) {
    char err[128];
    DWORD address = 0;
    if (count < 3 || !ParseAddress(tok[1], &address, err, sizeof(err))) {
        g_out.Add("err %s\n", count < 3 ? "usage: write <addr> <hexbytes> [force]" : err);
        return;
    }
    static BYTE data[kMaxWrite];
    DWORD length = 0;
    for (int i = 2; i < count; ++i) {
        const char *s = tok[i];
        if (s[0] == '0' && (s[1] == 'x' || s[1] == 'X')) s += 2;
        size_t len = strlen(s);
        if (len % 2) { g_out.Add("err odd number of hex digits in '%s'\n", tok[i]); return; }
        for (size_t k = 0; k < len; k += 2) {
            char two[3] = {s[k], s[k + 1], 0};
            char *end = nullptr;
            unsigned long b = strtoul(two, &end, 16);
            if (*end) { g_out.Add("err bad hex '%s'\n", tok[i]); return; }
            if (length >= kMaxWrite) { g_out.Add("err at most %lu bytes\n", kMaxWrite); return; }
            data[length++] = static_cast<BYTE>(b);
        }
    }
    if (!length) { g_out.Add("err no bytes\n"); return; }
    DoWrite(address, data, length, force);
}

void CmdWrite32(char **tok, int count, bool force, bool asFloat) {
    char err[128];
    DWORD address = 0, value = 0;
    if (count < 3 || !ParseAddress(tok[1], &address, err, sizeof(err))) {
        g_out.Add("err %s\n", count < 3 ? "usage: write32|writef <addr> <value> [force]" : err);
        return;
    }
    if (asFloat) {
        char *end = nullptr;
        float f = static_cast<float>(strtod(tok[2], &end));
        if (*end) { g_out.Add("err bad float '%s'\n", tok[2]); return; }
        memcpy(&value, &f, 4);
    } else if (!ParseNumber(tok[2], &value)) {
        g_out.Add("err bad value '%s'\n", tok[2]);
        return;
    }
    DoWrite(address, reinterpret_cast<const BYTE *>(&value), 4, force);
}

void CmdPlayer() {
    DWORD player = 0;
    if (!Read32(kPlayerPtr, &player)) { g_out.Add("err cannot read 0x%08lx\n", kPlayerPtr); return; }
    if (!player) { g_out.Add("ok none (GameTracker +0xc is 0)\n"); return; }
    float pos[3];
    if (CheckRange(player + 0x20, 12, false, false) || !ReadBytes(player + 0x20, reinterpret_cast<BYTE *>(pos), 12)) {
        g_out.Add("err player instance 0x%08lx not readable\n", player);
        return;
    }
    g_out.Add("ok instance 0x%08lx pos %.3f %.3f %.3f\n", player, static_cast<double>(pos[0]),
              static_cast<double>(pos[1]), static_cast<double>(pos[2]));
}

void AddCurrentCamera(const char *prefix) {
    DWORD camera = 0;
    if (!Read32(kCurrentCamera, &camera)) { g_out.Add("err cannot read 0x%08lx\n", kCurrentCamera); return; }
    g_out.Add("ok %scurrent 0x%08lx mode %d\n", prefix, camera, ModeOfCamera(camera));
}

void CmdCamera(char **tok, int count) {
    if (count < 2) { AddCurrentCamera(""); return; }
    const char *why = nullptr;
    if (!_stricmp(tok[1], "restore")) {
        if (!g_restoreOk) { g_out.Add("err camera restore 0x%08lx not verified (other exe?)\n", kCameraRestore); return; }
        Log(1, "camera restore (0x%08lx on the game thread)", kCameraRestore);
        why = CallOnGameThread(kKindCameraRestore, 0, 0, 0);
    } else {
        DWORD mode = 0;
        if (!ParseNumber(tok[1], &mode) || mode > 15) { g_out.Add("err usage: camera [<mode 0..15> | restore]\n"); return; }
        if (!g_cameraOk) { g_out.Add("err CAMERA_SetMode 0x%08lx not verified (other exe?)\n", kCameraSetMode); return; }
        Log(1, "CAMERA_SetMode(%lu) on the game thread", mode);
        why = CallOnGameThread(kKindCamera, mode, 0, 0);
    }
    if (why) { g_out.Add("err %s\n", why); Log(0, "camera: %s", why); return; }
    AddCurrentCamera("done, ");
}

void CmdPost(char **tok, int count) {
    char err[128];
    DWORD instance = 0, message = 0, data = 0;
    if (count < 4) { g_out.Add("err usage: post <instance> <msg> <data>\n"); return; }
    if (!ParseAddress(tok[1], &instance, err, sizeof(err))) { g_out.Add("err %s\n", err); return; }
    if (!ParseNumber(tok[2], &message) || !ParseNumber(tok[3], &data)) { g_out.Add("err bad msg / data\n"); return; }
    if (!g_postOk) { g_out.Add("err INSTANCE_Post 0x%08lx not verified (other exe?)\n", kInstancePost); return; }
    const char *why = CheckRange(instance, 0x124, false, false);
    if (why) { g_out.Add("err instance 0x%08lx: %s\n", instance, why); return; }
    DWORD handler = 0;
    Read32(instance + 0x120, &handler);
    if (!handler) { g_out.Add("err instance 0x%08lx has no message handler (+0x120 = 0)\n", instance); return; }
    Log(1, "INSTANCE_Post(0x%08lx, %lu, 0x%08lx) on the game thread (handler 0x%08lx)", instance, message, data, handler);
    why = CallOnGameThread(kKindPost, instance, message, data);
    if (why) { g_out.Add("err %s\n", why); Log(0, "post: %s", why); return; }
    g_out.Add("ok posted %lu data 0x%08lx to 0x%08lx (handler 0x%08lx, frame %lu)\n", message, data, instance, handler,
              g_job.frame);
}

void CmdObjects() {
    if (!g_tableOk) { g_out.Add("err object table code not verified (other exe?)\n"); return; }
    static BYTE table[kObjectCount * 0x24];
    if (!ReadBytes(kObjectTable, table, sizeof(table))) { g_out.Add("err access fault (caught)\n"); return; }
    int used = 0;
    for (int i = 0; i < kObjectCount; ++i)
        if (*reinterpret_cast<const WORD *>(table + i * 0x24 + 0xe)) ++used;
    g_out.Add("ok+ objects %d of %d in use (index id state object)\n", used, kObjectCount);
    for (int i = 0; i < kObjectCount; ++i) {
        const BYTE *e = table + i * 0x24;
        WORD state = *reinterpret_cast<const WORD *>(e + 0xe);
        if (!state) continue;
        g_out.Add("%d %d %u 0x%08lx\n", i, *reinterpret_cast<const SHORT *>(e + 0xc), state,
                  *reinterpret_cast<const DWORD *>(e + 8));
    }
    g_out.Add(".\n");
}

// 0.2: TruMenu items by id - "menu list" = TruMenuList(), "menu <id> [arg]" = TruMenuInvoke(id, arg). TruMenu runs
// items that touch the game on its own game-thread hook and waits up to 3 s itself, so this runs on the server thread.
typedef const char *(__cdecl *MenuListFn)();
typedef const char *(__cdecl *MenuInvokeFn)(const char *id, const char *arg);

void CmdMenu(char **tok, int count) {
    if (count < 2) { g_out.Add("err usage: menu list | menu <id> [arg]\n"); return; }
    HMODULE menu = GetModuleHandleA("TruMenu.asi");
    if (!menu) { g_out.Add("err no TruMenu\n"); return; }
    if (!_stricmp(tok[1], "list")) {
        MenuListFn list = reinterpret_cast<MenuListFn>(GetProcAddress(menu, "TruMenuList"));
        if (!list) { g_out.Add("err TruMenu has no TruMenuList export\n"); return; }
        const char *text = list();
        g_out.Add("ok+ menu items (id type value label, tab separated)\n");
        g_out.Add("%s", text ? text : "");
        g_out.Add(".\n");
        return;
    }
    MenuInvokeFn invoke = reinterpret_cast<MenuInvokeFn>(GetProcAddress(menu, "TruMenuInvoke"));
    if (!invoke) { g_out.Add("err TruMenu has no TruMenuInvoke export\n"); return; }
    char arg[512] = "";
    for (int i = 2; i < count; ++i) {                          // the rest of the line is the argument
        if (i > 2) strncat_s(arg, sizeof(arg), " ", _TRUNCATE);
        strncat_s(arg, sizeof(arg), tok[i], _TRUNCATE);
    }
    const char *answer = invoke(tok[1], arg);
    g_out.Add("%s\n", answer ? answer : "err (null)");
    Log(2, "menu %s %s -> %s", tok[1], arg, answer ? answer : "(null)");
}

// ---- 0.5.3 obj.msg <id> <msg> [<arg id>|0]: TruMenu 0.22.61's item obj.msg (it checks the game's two 0x165 call sites,
// sends through 0x5b3750 on the game thread and logs) - the same path as "menu obj.msg ..." ----
void CmdObjMsg(char **tok, int count) {
    if (count < 3) { g_out.Add("err usage: obj.msg <id> <msg> [<arg id>|0]\n"); return; }
    char *t[6] = {tok[0], const_cast<char *>("obj.msg"), tok[1], tok[2], count > 3 ? tok[3] : const_cast<char *>("0"), nullptr};
    Log(1, "obj.msg %s %s %s -> TruMenu obj.msg", tok[1], tok[2], count > 3 ? tok[3] : "0");
    CmdMenu(t, 5);
}
// ---- 0.5.1 mark.*: notes under TruMenu's labels (README "mark.note (needs TruMenu)") ----
// TruMenu 0.22.56 exports TruMenuNote(intro, text, flags) / TruMenuNoteClear(intro | 0xffffffff) / TruMenuNoteList(out,
// size); flags bit 0 = shown even when object names are off, bit 1 = kept over a level load. TruMenu locks its table, so
// the server thread calls them directly; mark.refs walks the instances and runs on the game thread (job kOpMarkRefs).
typedef int(__cdecl *NoteFn)(unsigned intro, const char *text, unsigned flags);
typedef int(__cdecl *NoteClearFn)(unsigned intro);
typedef int(__cdecl *NoteListFn)(char *out, int size);
const char kNeedsMenu[] = "needs TruMenu 0.22.56 (exports TruMenuNote / TruMenuNoteClear / TruMenuNoteList)";
bool NoteExports(NoteFn *note, NoteClearFn *clear, NoteListFn *list) {
    HMODULE menu = GetModuleHandleA("TruMenu.asi");
    *note = menu ? reinterpret_cast<NoteFn>(GetProcAddress(menu, "TruMenuNote")) : nullptr;
    *clear = menu ? reinterpret_cast<NoteClearFn>(GetProcAddress(menu, "TruMenuNoteClear")) : nullptr;
    *list = menu ? reinterpret_cast<NoteListFn>(GetProcAddress(menu, "TruMenuNoteList")) : nullptr;
    return *note && *clear && *list;
}
// printable ASCII, at most 95 characters (TruMenu copies it)
void NoteText(char **tok, int from, int count, char *out, size_t n) {
    out[0] = 0;
    for (int i = from; i < count; ++i) {
        if (i > from) strncat_s(out, n, " ", _TRUNCATE);
        strncat_s(out, n, tok[i], _TRUNCATE);
    }
    for (char *c = out; *c; ++c)
        if (static_cast<unsigned char>(*c) < 32 || static_cast<unsigned char>(*c) > 126) *c = '?';
}
bool ParseIntro(const char *s, unsigned *intro) {
    char *end = nullptr;
    const unsigned long v = strtoul(s, &end, 10);
    if (end == s || *end || !v || v == 0xffffffffUL) return false;
    *intro = static_cast<unsigned>(v);
    return true;
}
void CmdMarkRefs(char **tok, int count, bool force);   // below, after the object jobs (kOpMarkRefs)
void CmdMark(char **tok, int count, bool force) {
    NoteFn note = nullptr;
    NoteClearFn clear = nullptr;
    NoteListFn list = nullptr;
    const bool have = NoteExports(&note, &clear, &list);
    const char *cmd = tok[0];
    if (!_stricmp(cmd, "mark.refs")) {
        if (!have) { g_out.Add("err %s\n", kNeedsMenu); return; }
        if (count < 2) { g_out.Add("err usage: mark.refs <id>\n"); return; }
        CmdMarkRefs(tok, count, force);
        return;
    }
    if (!have) { g_out.Add("err %s\n", kNeedsMenu); return; }
    if (!_stricmp(cmd, "mark.list")) {
        static char buf[64 * 128];
        const int len = list(buf, static_cast<int>(sizeof(buf)));
        g_out.Add("ok+ mark.list: intro flags text (tab separated; flags 1 = always, 2 = keep over a load)\n");
        if (len > 0 && len < static_cast<int>(sizeof(buf))) g_out.Add("%s", buf);
        else if (len >= static_cast<int>(sizeof(buf))) g_out.Add("(list needs %d bytes)\n", len);
        g_out.Add(".\n");
        return;
    }
    if (!_stricmp(cmd, "mark.clear")) {
        unsigned intro = 0xffffffffu;
        if (count >= 2 && _stricmp(tok[1], "all") && !ParseIntro(tok[1], &intro)) {
            g_out.Add("err usage: mark.clear [<intro id>|all]\n");
            return;
        }
        const int removed = clear(intro);
        g_out.Add("ok mark.clear %s: %d note(s) removed\n", intro == 0xffffffffu ? "all" : tok[1], removed);
        Log(1, "mark.clear %s: %d removed", intro == 0xffffffffu ? "all" : tok[1], removed);
        return;
    }
    // mark.note <intro> [+keep] [+names] <text...>
    unsigned intro = 0;
    if (count < 3 || !ParseIntro(tok[1], &intro)) {
        g_out.Add("err usage: mark.note <intro id> [+keep] [+names] <text...>  (printable ASCII, 95 characters)\n");
        return;
    }
    unsigned flags = 1;                                        // default: shown even when object names are off
    int from = 2;
    for (; from < count; ++from) {
        if (!_stricmp(tok[from], "+keep")) flags |= 2;
        else if (!_stricmp(tok[from], "+names")) flags &= ~1u;
        else break;
    }
    char text[96];
    NoteText(tok, from, count, text, sizeof(text));
    if (!text[0]) { g_out.Add("err mark.note: no text\n"); return; }
    const int r = note(intro, text, flags);
    if (r == 1) g_out.Add("ok mark.note %u (flags %u): '%s'\n", intro, flags, text);
    else if (r == 0) g_out.Add("err mark.note: TruMenu's note table is full (64) - mark.clear\n");
    else g_out.Add("err mark.note: TruMenu refused the arguments (%d)\n", r);
    Log(1, "mark.note %u flags %u '%s' -> %d", intro, flags, text, r);
}

typedef const char *(*VersionFn)();

const char *CallVersion(FARPROC fn) {
    __try {
        const char *s = reinterpret_cast<VersionFn>(fn)();
        if (!s) return "(null)";
        volatile char first = *s;            // fault here -> caught
        (void)first;
        return s;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return "(fault)";
    }
}

void CmdModules() {
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, GetCurrentProcessId());
    if (snap == INVALID_HANDLE_VALUE) { g_out.Add("err CreateToolhelp32Snapshot failed (%lu)\n", GetLastError()); return; }
    g_out.Add("ok+ modules (.asi: name base size version)\n");
    const char *const known[] = {"TruShadowPower", "TruDlc2Player", "TruDoppelganger", "TruRockVein", "TruMenu",
                                 "TruLink"};
    bool seen[6] = {false, false, false, false, false, false};
    MODULEENTRY32 me;
    me.dwSize = sizeof(me);
    for (BOOL ok = Module32First(snap, &me); ok; ok = Module32Next(snap, &me)) {
        size_t len = strlen(me.szModule);
        if (len < 5 || _stricmp(me.szModule + len - 4, ".asi")) continue;
        char stem[MAX_PATH];
        strncpy_s(stem, sizeof(stem), me.szModule, len - 4);
        for (int k = 0; k < 6; ++k)
            if (!_stricmp(stem, known[k])) seen[k] = true;
        char exportName[MAX_PATH + 16];
        _snprintf_s(exportName, sizeof(exportName), _TRUNCATE, "%sVersion", stem);
        FARPROC fn = GetProcAddress(me.hModule, exportName);
        g_out.Add("%s 0x%08lx %lu %s\n", me.szModule, reinterpret_cast<DWORD>(me.modBaseAddr), me.modBaseSize,
                  fn ? CallVersion(fn) : "-");
    }
    CloseHandle(snap);
    for (int k = 0; k < 6; ++k)
        if (!seen[k]) g_out.Add("%s.asi not loaded\n", known[k]);
    g_out.Add(".\n");
}

// ---- 0.3: memory search (scan), watches, snapshots - all on the server thread ----
//
// scan: a Cheat-Engine-style value search. The first scan walks the game's writable memory with VirtualQuery
// (MEM_COMMIT, writable protection, no guard / no-access pages; MEM_PRIVATE plus the writable sections of the
// tru.exe image = .data / .bss) and keeps the matching addresses with their values (candidate set, two VirtualAlloc
// arrays committed on demand, at most ScanMaxCandidates). Every read is guarded (__try, 64 KB chunks); the server
// thread yields every 4 MB and keeps polling the watches, so the game thread is never blocked. Our own module, the
// candidate arrays and the server thread's stack are skipped.

enum ValueType { kTypeU8, kTypeS8, kTypeU16, kTypeS16, kTypeU32, kTypeS32, kTypeFloat, kTypeCount };
const char *const kTypeNames[kTypeCount] = {"u8", "s8", "u16", "s16", "u32", "s32", "float"};
const DWORD kTypeSizes[kTypeCount] = {1, 1, 2, 2, 4, 4, 4};

enum ScanOp { kOpEq, kOpNe, kOpGt, kOpLt, kOpRange, kOpUnknown, kOpChanged, kOpUnchanged, kOpIncreased, kOpDecreased,
              kOpIncBy, kOpDecBy };
const char *const kOpNames[] = {"eq", "ne", "gt", "lt", "range", "unknown", "changed", "unchanged", "increased",
                                "decreased", "inc_by", "dec_by"};

// options (TruLink.ini)
DWORD g_scanMaxCandidates = 4u * 1024 * 1024;
int g_scanMaxSeconds = 60;
int g_watchIntervalMs = 100;

const double kDefaultFloatTolerance = 0.001;

bool ParseType(const char *s, int *type) {
    for (int t = 0; t < kTypeCount; ++t)
        if (!_stricmp(s, kTypeNames[t])) { *type = t; return true; }
    if (!_stricmp(s, "f32")) { *type = kTypeFloat; return true; }
    return false;
}

// raw value (the low bytes of a dword) -> number
double ToNumber(int type, DWORD raw) {
    switch (type) {
    case kTypeU8: return static_cast<double>(static_cast<BYTE>(raw));
    case kTypeS8: return static_cast<double>(static_cast<signed char>(static_cast<BYTE>(raw)));
    case kTypeU16: return static_cast<double>(static_cast<WORD>(raw));
    case kTypeS16: return static_cast<double>(static_cast<SHORT>(static_cast<WORD>(raw)));
    case kTypeU32: return static_cast<double>(raw);
    case kTypeS32: return static_cast<double>(static_cast<LONG>(raw));
    default: {
        float f;
        memcpy(&f, &raw, 4);
        return static_cast<double>(f);
    }
    }
}

void FormatValue(int type, DWORD raw, char *s, size_t size) {
    if (type == kTypeFloat) _snprintf_s(s, size, _TRUNCATE, "%.7g", ToNumber(type, raw));
    else if (type == kTypeU32) _snprintf_s(s, size, _TRUNCATE, "%lu", raw);
    else _snprintf_s(s, size, _TRUNCATE, "%.0f", ToNumber(type, raw));
}

// value argument of a type: float = decimal, integers = ParseNumber (hex 0x.., negative allowed) cut to the type
bool ParseValue(int type, const char *s, double *value) {
    if (type == kTypeFloat) {
        char *end = nullptr;
        double d = strtod(s, &end);
        if (end == s || *end) return false;
        *value = d;
        return true;
    }
    DWORD raw = 0;
    if (!ParseNumber(s, &raw)) return false;
    *value = ToNumber(type, raw);
    return true;
}

// difference argument (inc_by / dec_by): any number, hex allowed
bool ParseDelta(const char *s, double *value) {
    if (s[0] == '0' && (s[1] == 'x' || s[1] == 'X')) {
        DWORD raw = 0;
        if (!ParseHex(s, &raw)) return false;
        *value = static_cast<double>(raw);
        return true;
    }
    char *end = nullptr;
    double d = strtod(s, &end);
    if (end == s || *end) return false;
    *value = d;
    return true;
}

struct Filter {
    int op;
    double a, b, tol;
    bool isFloat;
};

inline bool Match(const Filter &f, double cur, double prev) {
    switch (f.op) {
    case kOpEq: return fabs(cur - f.a) <= f.tol;
    case kOpNe: return !(fabs(cur - f.a) <= f.tol);
    case kOpGt: return cur > f.a + f.tol;
    case kOpLt: return cur < f.a - f.tol;
    case kOpRange: return cur >= f.a - f.tol && cur <= f.b + f.tol;
    case kOpUnknown: return !f.isFloat || (cur - cur == 0.0);      // floats: finite values only (no NaN / inf)
    case kOpChanged: return !(fabs(cur - prev) <= f.tol);
    case kOpUnchanged: return fabs(cur - prev) <= f.tol;
    case kOpIncreased: return cur > prev + f.tol;
    case kOpDecreased: return cur < prev - f.tol;
    case kOpIncBy: return fabs((cur - prev) - f.a) <= f.tol;
    case kOpDecBy: return fabs((prev - cur) - f.a) <= f.tol;
    }
    return false;
}

double NowMs() {
    static LARGE_INTEGER frequency = {};
    if (!frequency.QuadPart) QueryPerformanceFrequency(&frequency);
    LARGE_INTEGER t;
    QueryPerformanceCounter(&t);
    return static_cast<double>(t.QuadPart) * 1000.0 / static_cast<double>(frequency.QuadPart);
}

// committed, readable, no guard / no-access page for [address, address + length)
bool ReadableRange(DWORD address, DWORD length, DWORD *regionStart, DWORD *regionEnd) {
    MEMORY_BASIC_INFORMATION mbi;
    if (!VirtualQuery(reinterpret_cast<void *>(address), &mbi, sizeof(mbi))) return false;
    DWORD start = reinterpret_cast<DWORD>(mbi.BaseAddress);
    DWORD end = start + static_cast<DWORD>(mbi.RegionSize);
    if (regionStart) *regionStart = start;
    if (regionEnd) *regionEnd = end;
    if (mbi.State != MEM_COMMIT || (mbi.Protect & (PAGE_GUARD | PAGE_NOACCESS)) || !(mbi.Protect & kReadable))
        return false;
    return address + length > address && address + length <= end;   // values across a region end are skipped
}

void PollWatches();

// candidate set
struct ScanSet {
    bool active;
    int type;
    DWORD step;                         // alignment of the first scan
    double tol;
    DWORD *addr, *val;                  // reserved for cap entries each, committed in steps
    DWORD count, cap, committed;
    bool truncated, timedOut;
    int passes;
    double lastMs;
    char lastOp[16];
};
ScanSet g_scan;
const DWORD kCommitStep = 256 * 1024;   // entries per commit (1 MB per array)

void ScanFree() {
    if (g_scan.addr) VirtualFree(g_scan.addr, 0, MEM_RELEASE);
    if (g_scan.val) VirtualFree(g_scan.val, 0, MEM_RELEASE);
    memset(&g_scan, 0, sizeof(g_scan));
}

bool ScanReserve() {
    ScanFree();
    g_scan.cap = g_scanMaxCandidates;
    g_scan.addr = static_cast<DWORD *>(VirtualAlloc(nullptr, g_scan.cap * 4, MEM_RESERVE, PAGE_READWRITE));
    g_scan.val = static_cast<DWORD *>(VirtualAlloc(nullptr, g_scan.cap * 4, MEM_RESERVE, PAGE_READWRITE));
    if (!g_scan.addr || !g_scan.val) { ScanFree(); return false; }
    return true;
}

bool ScanGrow() {
    if (g_scan.committed >= g_scan.cap) return false;
    DWORD n = g_scan.cap - g_scan.committed;
    if (n > kCommitStep) n = kCommitStep;
    if (!VirtualAlloc(g_scan.addr + g_scan.committed, n * 4, MEM_COMMIT, PAGE_READWRITE) ||
        !VirtualAlloc(g_scan.val + g_scan.committed, n * 4, MEM_COMMIT, PAGE_READWRITE))
        return false;
    g_scan.committed += n;
    return true;
}

inline bool ScanAdd(DWORD address, DWORD raw) {
    if (g_scan.count == g_scan.committed && !ScanGrow()) {
        g_scan.truncated = true;
        return false;
    }
    g_scan.addr[g_scan.count] = address;
    g_scan.val[g_scan.count] = raw;
    ++g_scan.count;
    return true;
}

// is this region part of the searched memory?
bool ScanWanted(const MEMORY_BASIC_INFORMATION &mbi) {
    if (mbi.State != MEM_COMMIT) return false;
    if ((mbi.Protect & (PAGE_GUARD | PAGE_NOACCESS)) || !(mbi.Protect & kWritable)) return false;
    DWORD base = reinterpret_cast<DWORD>(mbi.BaseAddress);
    bool inImage = base >= g_imageStart && base < g_imageEnd;   // tru.exe .data / .bss (writable sections)
    if (!inImage && mbi.Type != MEM_PRIVATE) return false;      // other modules (incl. TruLink), mapped files
    if (mbi.AllocationBase == g_scan.addr || mbi.AllocationBase == g_scan.val) return false;
    const NT_TIB *tib = reinterpret_cast<const NT_TIB *>(NtCurrentTeb());
    DWORD end = base + static_cast<DWORD>(mbi.RegionSize);
    if (base < reinterpret_cast<DWORD>(tib->StackBase) && end > reinterpret_cast<DWORD>(tib->StackLimit))
        return false;                                            // the server thread's own stack
    return true;
}

const DWORD kChunk = 0x10000;
BYTE g_chunk[kChunk + 8];

// matches in one chunk; positions = number of start offsets that belong to this chunk; false = candidate set full
template <typename T>
bool ScanChunk(const BYTE *data, DWORD positions, DWORD length, DWORD address, DWORD step, const Filter &f) {
    for (DWORD off = 0; off < positions && off + sizeof(T) <= length; off += step) {
        T v;
        memcpy(&v, data + off, sizeof(T));
        if (!Match(f, static_cast<double>(v), 0.0)) continue;
        DWORD raw = 0;
        memcpy(&raw, &v, sizeof(T));
        if (!ScanAdd(address + off, raw)) return false;
    }
    return true;
}

bool ScanChunkTyped(int type, const BYTE *data, DWORD positions, DWORD length, DWORD address, DWORD step,
                    const Filter &f) {
    switch (type) {
    case kTypeU8: return ScanChunk<BYTE>(data, positions, length, address, step, f);
    case kTypeS8: return ScanChunk<signed char>(data, positions, length, address, step, f);
    case kTypeU16: return ScanChunk<WORD>(data, positions, length, address, step, f);
    case kTypeS16: return ScanChunk<SHORT>(data, positions, length, address, step, f);
    case kTypeU32: return ScanChunk<DWORD>(data, positions, length, address, step, f);
    case kTypeS32: return ScanChunk<LONG>(data, positions, length, address, step, f);
    default: return ScanChunk<float>(data, positions, length, address, step, f);
    }
}

struct ScanStats {
    DWORD regions, faults;
    double megabytes;
};

// walks [areaStart, areaEnd) region by region; listOnly = count / list the regions without reading them
void WalkRegions(DWORD areaStart, DWORD areaEnd, ScanStats *stats, int type, DWORD step, const Filter *f,
                 int listMax) {
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    DWORD lo = reinterpret_cast<DWORD>(si.lpMinimumApplicationAddress);
    DWORD hi = reinterpret_cast<DWORD>(si.lpMaximumApplicationAddress);
    DWORD p = areaStart > lo ? areaStart : lo;
    DWORD limit = areaEnd && areaEnd - 1 < hi ? areaEnd : hi + 1;
    DWORD size = kTypeSizes[type];
    double started = NowMs(), lastYield = 0.0;
    int listed = 0;
    while (p < limit) {
        MEMORY_BASIC_INFORMATION mbi;
        if (!VirtualQuery(reinterpret_cast<void *>(p), &mbi, sizeof(mbi))) break;
        DWORD base = reinterpret_cast<DWORD>(mbi.BaseAddress);
        DWORD end = base + static_cast<DWORD>(mbi.RegionSize);
        if (end <= p) break;
        if (ScanWanted(mbi)) {
            DWORD s = p > base ? p : base;
            DWORD e = end < limit ? end : limit;
            s = (s + step - 1) & ~(step - 1);
            if (s < e) {
                ++stats->regions;
                stats->megabytes += static_cast<double>(e - s) / (1024.0 * 1024.0);
                if (!f) {
                    if (listed < listMax) {
                        bool inImage = base >= g_imageStart && base < g_imageEnd;
                        g_out.Add("0x%08lx %8lu KB %s %s\n", s, (e - s) / 1024, inImage ? "image" : "private",
                                  (mbi.Protect & PAGE_WRITECOPY) ? "writecopy" : "readwrite");
                        ++listed;
                    }
                } else {
                    for (DWORD c = s; c < e; c += kChunk) {
                        DWORD positions = e - c < kChunk ? e - c : kChunk;
                        DWORD length = e - c < kChunk + size - 1 ? e - c : kChunk + size - 1;
                        if (!ReadBytes(c, g_chunk, length)) { ++stats->faults; continue; }
                        if (!ScanChunkTyped(type, g_chunk, positions, length, c, step, *f)) return;
                        if (((c - s) & 0x3fffff) == 0) {           // every 4 MB: yield, poll the watches, time limit
                            double now = NowMs();
                            if (now - lastYield > 20.0) { Sleep(0); PollWatches(); lastYield = now; }
                            if (now - started > g_scanMaxSeconds * 1000.0) { g_scan.timedOut = true; return; }
                        }
                        if (c + kChunk < c) break;                 // top of the address space
                    }
                }
            }
        }
        if (end >= limit || end == 0) break;
        p = end;
    }
}

// options after the values: tol <x>, align <1|2|4>, at <addr> <len>
bool ParseScanOptions(char **tok, int count, int i, double *tol, DWORD *step, DWORD *areaStart, DWORD *areaEnd,
                      bool firstScan, char *err, size_t errSize) {
    for (; i < count; ++i) {
        if (!_stricmp(tok[i], "tol") && i + 1 < count) {
            if (!ParseDelta(tok[++i], tol) || *tol < 0) { _snprintf_s(err, errSize, _TRUNCATE, "bad tol '%s'", tok[i]); return false; }
        } else if (firstScan && !_stricmp(tok[i], "align") && i + 1 < count) {
            DWORD a = 0;
            if (!ParseNumber(tok[++i], &a) || (a != 1 && a != 2 && a != 4)) { _snprintf_s(err, errSize, _TRUNCATE, "align 1 | 2 | 4"); return false; }
            *step = a;
        } else if (firstScan && !_stricmp(tok[i], "at") && i + 2 < count) {
            DWORD start = 0, length = 0;
            if (!ParseAddress(tok[i + 1], &start, err, errSize)) return false;
            if (!ParseNumber(tok[i + 2], &length) || !length || start + length < start) {
                _snprintf_s(err, errSize, _TRUNCATE, "bad length '%s'", tok[i + 2]);
                return false;
            }
            *areaStart = start;
            *areaEnd = start + length;
            i += 2;
        } else {
            _snprintf_s(err, errSize, _TRUNCATE, "unknown option '%s' (tol <x>%s)", tok[i],
                        firstScan ? ", align <1|2|4>, at <addr> <len>" : "");
            return false;
        }
    }
    return true;
}

// op and its values from tok[i]; returns the index after them or -1
int ParseScanOp(char **tok, int count, int i, int type, bool firstScan, Filter *f, char *err, size_t errSize) {
    if (i >= count) { _snprintf_s(err, errSize, _TRUNCATE, "missing op"); return -1; }
    int op = -1;
    for (int k = 0; k < static_cast<int>(sizeof(kOpNames) / sizeof(kOpNames[0])); ++k)
        if (!_stricmp(tok[i], kOpNames[k])) op = k;
    if (!_stricmp(tok[i], "inc")) op = kOpIncreased;
    if (!_stricmp(tok[i], "dec")) op = kOpDecreased;
    if (op < 0) { _snprintf_s(err, errSize, _TRUNCATE, "unknown op '%s'", tok[i]); return -1; }
    bool compares = op == kOpChanged || op == kOpUnchanged || op == kOpIncreased || op == kOpDecreased ||
                    op == kOpIncBy || op == kOpDecBy;
    if (firstScan && compares) {
        _snprintf_s(err, errSize, _TRUNCATE, "'%s' needs a previous scan (scan next ...)", kOpNames[op]);
        return -1;
    }
    if (!firstScan && op == kOpUnknown) { _snprintf_s(err, errSize, _TRUNCATE, "'unknown' is a first scan only"); return -1; }
    f->op = op;
    f->a = f->b = 0.0;
    ++i;
    int values = (op == kOpRange) ? 2 : (op <= kOpLt || op == kOpIncBy || op == kOpDecBy) ? 1 : 0;
    if (i + values > count) { _snprintf_s(err, errSize, _TRUNCATE, "'%s' needs %d value(s)", kOpNames[op], values); return -1; }
    for (int v = 0; v < values; ++v) {
        double *target = v ? &f->b : &f->a;
        bool ok = (op == kOpIncBy || op == kOpDecBy) ? ParseDelta(tok[i + v], target) : ParseValue(type, tok[i + v], target);
        if (!ok) { _snprintf_s(err, errSize, _TRUNCATE, "bad %s value '%s'", kTypeNames[type], tok[i + v]); return -1; }
    }
    if (op == kOpRange && f->b < f->a) { double t = f->a; f->a = f->b; f->b = t; }
    return i + values;
}

void AddScanSummary(const char *what, const ScanStats *stats) {
    g_out.Add("ok scan %s %s: %lu candidates", kTypeNames[g_scan.type], what, g_scan.count);
    if (stats) g_out.Add(" in %lu regions %.1f MB", stats->regions, stats->megabytes);
    g_out.Add(", %.0f ms", g_scan.lastMs);
    if (stats && stats->faults) g_out.Add(", %lu chunks faulted (skipped)", stats->faults);
    if (g_scan.truncated)
        g_out.Add(", TRUNCATED at %lu (ScanMaxCandidates) - narrow it: a value op instead of unknown, or 'at <addr> <len>'",
                  g_scan.cap);
    if (g_scan.timedOut) g_out.Add(", STOPPED after ScanMaxSeconds %d - partial set", g_scanMaxSeconds);
    g_out.Add("\n");
}

void ScanFirst(char **tok, int count) {
    char err[160];
    int type = 0;
    if (!ParseType(tok[1], &type)) { g_out.Add("err unknown type '%s' (u8 s8 u16 s16 u32 s32 float)\n", tok[1]); return; }
    Filter f;
    f.isFloat = type == kTypeFloat;
    int i = ParseScanOp(tok, count, 2, type, true, &f, err, sizeof(err));
    if (i < 0) { g_out.Add("err %s - usage: scan <type> eq|ne|gt|lt <v> | range <lo> <hi> | unknown [tol x] [align n] [at <addr> <len>]\n", err); return; }
    double tol = f.isFloat ? kDefaultFloatTolerance : 0.0;
    DWORD step = kTypeSizes[type], areaStart = 0, areaEnd = 0;
    if (!ParseScanOptions(tok, count, i, &tol, &step, &areaStart, &areaEnd, true, err, sizeof(err))) { g_out.Add("err %s\n", err); return; }
    f.tol = tol;
    if (!ScanReserve()) { g_out.Add("err VirtualAlloc of the candidate set (%lu entries) failed\n", g_scanMaxCandidates); return; }
    g_scan.type = type;
    g_scan.step = step;
    g_scan.tol = tol;
    double started = NowMs();
    ScanStats stats = {0, 0, 0.0};
    WalkRegions(areaStart, areaEnd, &stats, type, step, &f, 0);
    g_scan.lastMs = NowMs() - started;
    g_scan.active = true;
    g_scan.passes = 1;
    strncpy_s(g_scan.lastOp, sizeof(g_scan.lastOp), kOpNames[f.op], _TRUNCATE);
    char what[96];
    if (areaEnd)
        _snprintf_s(what, sizeof(what), _TRUNCATE, "%s at 0x%08lx-0x%08lx align %lu", kOpNames[f.op], areaStart,
                    areaEnd, step);
    else
        _snprintf_s(what, sizeof(what), _TRUNCATE, "%s align %lu", kOpNames[f.op], step);
    AddScanSummary(what, &stats);
    Log(1, "scan %s %s: %lu candidates, %lu regions %.1f MB, %.0f ms%s%s", kTypeNames[type], kOpNames[f.op],
        g_scan.count, stats.regions, stats.megabytes, g_scan.lastMs, g_scan.truncated ? " TRUNCATED" : "",
        g_scan.timedOut ? " TIMEOUT" : "");
}

void ScanNext(char **tok, int count) {
    char err[160];
    if (!g_scan.active) { g_out.Add("err no scan yet (scan <type> <op> ...)\n"); return; }
    Filter f;
    f.isFloat = g_scan.type == kTypeFloat;
    int i = ParseScanOp(tok, count, 2, g_scan.type, false, &f, err, sizeof(err));
    if (i < 0) {
        g_out.Add("err %s - usage: scan next eq|ne|gt|lt <v> | range <lo> <hi> | changed | unchanged | increased | "
                  "decreased | inc_by <v> | dec_by <v> [tol x]\n", err);
        return;
    }
    double tol = g_scan.tol;
    DWORD unusedStep = 0, unusedStart = 0, unusedEnd = 0;
    if (!ParseScanOptions(tok, count, i, &tol, &unusedStep, &unusedStart, &unusedEnd, false, err, sizeof(err))) { g_out.Add("err %s\n", err); return; }
    f.tol = tol;
    DWORD size = kTypeSizes[g_scan.type];
    double started = NowMs(), lastYield = started;
    DWORD before = g_scan.count, kept = 0, lost = 0, regionStart = 1, regionEnd = 0;
    bool regionOk = false;
    for (DWORD k = 0; k < g_scan.count; ++k) {
        if ((k & 0xffff) == 0xffff) {                          // every 64 K candidates: yield, poll the watches
            double now = NowMs();
            if (now - lastYield > 20.0) { Sleep(0); PollWatches(); lastYield = now; }
        }
        DWORD a = g_scan.addr[k];
        if (a < regionStart || a + size > regionEnd) regionOk = ReadableRange(a, size, &regionStart, &regionEnd);
        DWORD raw = 0;
        if (!regionOk || a + size > regionEnd || !ReadBytes(a, reinterpret_cast<BYTE *>(&raw), size)) { ++lost; continue; }
        if (!Match(f, ToNumber(g_scan.type, raw), ToNumber(g_scan.type, g_scan.val[k]))) continue;
        g_scan.addr[kept] = a;
        g_scan.val[kept] = raw;
        ++kept;
    }
    g_scan.count = kept;
    g_scan.lastMs = NowMs() - started;
    ++g_scan.passes;
    strncpy_s(g_scan.lastOp, sizeof(g_scan.lastOp), kOpNames[f.op], _TRUNCATE);
    char what[96];
    _snprintf_s(what, sizeof(what), _TRUNCATE, "next %s (pass %d, from %lu, %lu unreadable dropped)", kOpNames[f.op],
                g_scan.passes, before, lost);
    AddScanSummary(what, nullptr);
    Log(1, "scan next %s: %lu -> %lu candidates, %.0f ms", kOpNames[f.op], before, kept, g_scan.lastMs);
}

void ScanList(char **tok, int count) {
    if (!g_scan.active) { g_out.Add("err no scan yet\n"); return; }
    DWORD n = 20;
    if (count > 2 && (!ParseNumber(tok[2], &n) || !n)) { g_out.Add("err usage: scan list [n]\n"); return; }
    if (n > 500) n = 500;
    if (n > g_scan.count) n = g_scan.count;
    g_out.Add("ok+ scan list %lu of %lu %s candidates (address current previous-scan)\n", n, g_scan.count,
              kTypeNames[g_scan.type]);
    DWORD size = kTypeSizes[g_scan.type];
    for (DWORD k = 0; k < n; ++k) {
        DWORD a = g_scan.addr[k], raw = 0;
        char cur[40], prev[40];
        FormatValue(g_scan.type, g_scan.val[k], prev, sizeof(prev));
        if (ReadableRange(a, size, nullptr, nullptr) && ReadBytes(a, reinterpret_cast<BYTE *>(&raw), size))
            FormatValue(g_scan.type, raw, cur, sizeof(cur));
        else
            strncpy_s(cur, sizeof(cur), "unreadable", _TRUNCATE);
        g_out.Add("0x%08lx %s %s\n", a, cur, prev);
    }
    g_out.Add(".\n");
}

void CmdScan(char **tok, int count) {
    if (count < 2 || !_stricmp(tok[1], "status")) {
        if (!g_scan.active) { g_out.Add("ok scan none (cap %lu)\n", g_scanMaxCandidates); return; }
        g_out.Add("ok scan %s align %lu tol %g: %lu candidates, pass %d (last %s, %.0f ms)%s%s\n",
                  kTypeNames[g_scan.type], g_scan.step, g_scan.tol, g_scan.count, g_scan.passes, g_scan.lastOp,
                  g_scan.lastMs, g_scan.truncated ? " TRUNCATED" : "", g_scan.timedOut ? " PARTIAL" : "");
        return;
    }
    if (!_stricmp(tok[1], "next")) ScanNext(tok, count);
    else if (!_stricmp(tok[1], "list")) ScanList(tok, count);
    else if (!_stricmp(tok[1], "clear")) { ScanFree(); g_out.Add("ok scan cleared\n"); }
    else if (!_stricmp(tok[1], "regions")) {
        DWORD n = 40;
        if (count > 2 && !ParseNumber(tok[2], &n)) { g_out.Add("err usage: scan regions [n]\n"); return; }
        if (n > 1000) n = 1000;
        g_out.Add("ok+ scan regions (start size kind protection; first %lu)\n", n);
        ScanStats stats = {0, 0, 0.0};
        WalkRegions(0, 0, &stats, kTypeU8, 1, nullptr, static_cast<int>(n));
        g_out.Add("total %lu regions %.1f MB\n.\n", stats.regions, stats.megabytes);
    } else ScanFirst(tok, count);
}

// ---- watches ----

const int kMaxWatches = 32;
struct Watch {
    bool used, readable;
    char name[32];
    DWORD address;
    int type;
    DWORD value, changes;
};
Watch g_watches[kMaxWatches];

const DWORD kRingSize = 1024;
struct WatchEvent {
    DWORD tick, clock;
    char name[32];                      // copied: the watch may be deleted later
    DWORD address;
    int type;
    DWORD oldValue, newValue;
    char kind;                          // 'c' change, 'u' became unreadable, 'r' readable again
};
WatchEvent g_ring[kRingSize];
DWORD g_ringTotal = 0;
DWORD g_lastWatchPoll = 0;

bool ReadWatchValue(const Watch &w, DWORD *raw) {
    *raw = 0;
    DWORD size = kTypeSizes[w.type];
    return ReadableRange(w.address, size, nullptr, nullptr) && ReadBytes(w.address, reinterpret_cast<BYTE *>(raw), size);
}

void AddEvent(int index, char kind, DWORD oldValue, DWORD newValue) {
    WatchEvent &e = g_ring[g_ringTotal % kRingSize];
    e.tick = GetTickCount();
    e.clock = 0;
    ReadBytes(kGameClock, reinterpret_cast<BYTE *>(&e.clock), 4);
    const Watch &w = g_watches[index];
    strncpy_s(e.name, sizeof(e.name), w.name, _TRUNCATE);
    e.address = w.address;
    e.type = w.type;
    e.kind = kind;
    e.oldValue = oldValue;
    e.newValue = newValue;
    ++g_ringTotal;
}

void PollWatches() {
    DWORD now = GetTickCount();
    if (now - g_lastWatchPoll < static_cast<DWORD>(g_watchIntervalMs)) return;
    g_lastWatchPoll = now;
    for (int i = 0; i < kMaxWatches; ++i) {
        Watch &w = g_watches[i];
        if (!w.used) continue;
        DWORD raw = 0;
        bool ok = ReadWatchValue(w, &raw);
        if (!ok) {
            if (w.readable) {
                w.readable = false;
                AddEvent(i, 'u', w.value, 0);
                Log(1, "watch %s 0x%08lx unreadable", w.name, w.address);
            }
            continue;
        }
        if (!w.readable) {
            w.readable = true;
            AddEvent(i, 'r', w.value, raw);
            Log(1, "watch %s 0x%08lx readable again", w.name, w.address);
        } else if (raw == w.value) {
            continue;
        } else {
            char a[40], b[40];
            FormatValue(w.type, w.value, a, sizeof(a));
            FormatValue(w.type, raw, b, sizeof(b));
            AddEvent(i, 'c', w.value, raw);
            Log(1, "watch %s 0x%08lx %s %s -> %s", w.name, w.address, kTypeNames[w.type], a, b);
            ++w.changes;
        }
        w.value = raw;
    }
}

int FindWatch(const char *key) {
    for (int i = 0; i < kMaxWatches; ++i)
        if (g_watches[i].used && !_stricmp(g_watches[i].name, key)) return i;
    DWORD a = 0;
    if (key[0] == '#' && ParseNumber(key + 1, &a) && a < static_cast<DWORD>(kMaxWatches) && g_watches[a].used)
        return static_cast<int>(a);
    if (ParseHex(key, &a))
        for (int i = 0; i < kMaxWatches; ++i)
            if (g_watches[i].used && g_watches[i].address == a) return i;
    return -1;
}

void CmdWatch(char **tok, int count, bool force) {
    char err[128];
    if (count < 2) { g_out.Add("err usage: watch add <addr> <type> [name] | del <name|#i|addr|all> | list | log [n]\n"); return; }
    if (!_stricmp(tok[1], "add")) {
        DWORD address = 0;
        int type = 0;
        if (count < 4 || !ParseAddress(tok[2], &address, err, sizeof(err))) {
            g_out.Add("err %s\n", count < 4 ? "usage: watch add <addr> <type> [name] [force]" : err);
            return;
        }
        if (!ParseType(tok[3], &type)) { g_out.Add("err unknown type '%s'\n", tok[3]); return; }
        const char *why = CheckRange(address, kTypeSizes[type], false, force);
        if (why) { g_out.Add("err 0x%08lx: %s\n", address, why); return; }
        int slot = -1;
        for (int i = 0; i < kMaxWatches && slot < 0; ++i)
            if (!g_watches[i].used) slot = i;
        if (slot < 0) { g_out.Add("err all %d watches in use (watch del)\n", kMaxWatches); return; }
        Watch &w = g_watches[slot];
        memset(&w, 0, sizeof(w));
        if (count > 4) strncpy_s(w.name, sizeof(w.name), tok[4], _TRUNCATE);
        else _snprintf_s(w.name, sizeof(w.name), _TRUNCATE, "w%d", slot);
        if (FindWatch(w.name) >= 0) { g_out.Add("err watch name '%s' already used\n", w.name); return; }
        w.address = address;
        w.type = type;
        w.readable = ReadWatchValue(w, &w.value);
        w.used = true;
        char v[40];
        FormatValue(type, w.value, v, sizeof(v));
        g_out.Add("ok watch #%d %s 0x%08lx %s = %s (polled every %d ms)\n", slot, w.name, address, kTypeNames[type],
                  w.readable ? v : "unreadable", g_watchIntervalMs);
        Log(1, "watch add #%d %s 0x%08lx %s = %s", slot, w.name, address, kTypeNames[type], v);
    } else if (!_stricmp(tok[1], "del")) {
        if (count < 3) { g_out.Add("err usage: watch del <name|#i|addr|all>\n"); return; }
        if (!_stricmp(tok[2], "all")) {
            int n = 0;
            for (int i = 0; i < kMaxWatches; ++i)
                if (g_watches[i].used) { g_watches[i].used = false; ++n; }
            g_out.Add("ok %d watches removed\n", n);
            return;
        }
        int i = FindWatch(tok[2]);
        if (i < 0) { g_out.Add("err no watch '%s'\n", tok[2]); return; }
        g_watches[i].used = false;
        g_out.Add("ok watch #%d %s removed\n", i, g_watches[i].name);
    } else if (!_stricmp(tok[1], "list")) {
        g_out.Add("ok+ watches (#index name address type value changes)\n");
        for (int i = 0; i < kMaxWatches; ++i) {
            const Watch &w = g_watches[i];
            if (!w.used) continue;
            char v[40];
            FormatValue(w.type, w.value, v, sizeof(v));
            g_out.Add("#%d %s 0x%08lx %s %s %lu\n", i, w.name, w.address, kTypeNames[w.type], w.readable ? v : "unreadable",
                      w.changes);
        }
        g_out.Add(".\n");
    } else if (!_stricmp(tok[1], "log")) {
        DWORD n = 50;
        if (count > 2 && (!ParseNumber(tok[2], &n) || !n)) { g_out.Add("err usage: watch log [n]\n"); return; }
        if (n > kRingSize) n = kRingSize;
        DWORD available = g_ringTotal < kRingSize ? g_ringTotal : kRingSize;
        if (n > available) n = available;
        DWORD now = GetTickCount();
        g_out.Add("ok+ watch log %lu of %lu events (ms-ago game-clock name address old -> new)\n", n, g_ringTotal);
        for (DWORD k = g_ringTotal - n; k < g_ringTotal; ++k) {
            const WatchEvent &e = g_ring[k % kRingSize];
            char a[40], b[40];
            FormatValue(e.type, e.oldValue, a, sizeof(a));
            FormatValue(e.type, e.newValue, b, sizeof(b));
            const char *kind = e.kind == 'u' ? " (unreadable)" : e.kind == 'r' ? " (readable again)" : "";
            g_out.Add("%lu %lu %s 0x%08lx %s -> %s%s\n", now - e.tick, e.clock, e.name, e.address, a,
                      e.kind == 'u' ? "-" : b, kind);
        }
        g_out.Add(".\n");
    } else {
        g_out.Add("err usage: watch add <addr> <type> [name] | del <name|#i|addr|all> | list | log [n]\n");
    }
}

// ---- snapshots ----

const int kMaxSnapshots = 16;
const DWORD kMaxSnapshot = 4096;
struct Snapshot {
    bool used;
    char name[32];
    DWORD address, length, tick;
    BYTE data[kMaxSnapshot];
};
Snapshot g_snaps[kMaxSnapshots];
BYTE g_snapNow[kMaxSnapshot];

int FindSnapshot(const char *name) {
    for (int i = 0; i < kMaxSnapshots; ++i)
        if (g_snaps[i].used && !_stricmp(g_snaps[i].name, name)) return i;
    return -1;
}

// snapshot <name> <addr> <len> [force] | snapshot <name> (take again) | snapshot list | snapshot del <name>
void CmdSnapshot(char **tok, int count, bool force) {
    char err[128];
    if (count < 2) { g_out.Add("err usage: snapshot <name> <addr> <len> | snapshot <name> | list | del <name>\n"); return; }
    if (!_stricmp(tok[1], "list")) {
        g_out.Add("ok+ snapshots (name address length age-ms)\n");
        DWORD now = GetTickCount();
        for (int i = 0; i < kMaxSnapshots; ++i)
            if (g_snaps[i].used)
                g_out.Add("%s 0x%08lx %lu %lu\n", g_snaps[i].name, g_snaps[i].address, g_snaps[i].length, now - g_snaps[i].tick);
        g_out.Add(".\n");
        return;
    }
    if (!_stricmp(tok[1], "del")) {
        int i = count > 2 ? FindSnapshot(tok[2]) : -1;
        if (i < 0) { g_out.Add("err no snapshot '%s'\n", count > 2 ? tok[2] : ""); return; }
        g_snaps[i].used = false;
        g_out.Add("ok snapshot %s removed\n", tok[2]);
        return;
    }
    int slot = FindSnapshot(tok[1]);
    DWORD address = 0, length = 0;
    if (count >= 4) {
        if (!ParseAddress(tok[2], &address, err, sizeof(err))) { g_out.Add("err %s\n", err); return; }
        if (!ParseNumber(tok[3], &length) || !length || length > kMaxSnapshot) { g_out.Add("err len 1..%lu\n", kMaxSnapshot); return; }
    } else if (slot >= 0) {
        address = g_snaps[slot].address;
        length = g_snaps[slot].length;
    } else {
        g_out.Add("err no snapshot '%s' yet - usage: snapshot <name> <addr> <len>\n", tok[1]);
        return;
    }
    const char *why = CheckRange(address, length, false, force);
    if (why) { g_out.Add("err 0x%08lx: %s\n", address, why); return; }
    for (int i = 0; i < kMaxSnapshots && slot < 0; ++i)
        if (!g_snaps[i].used) slot = i;
    if (slot < 0) { g_out.Add("err all %d snapshots in use (snapshot del)\n", kMaxSnapshots); return; }
    Snapshot &s = g_snaps[slot];
    if (!ReadBytes(address, s.data, length)) { g_out.Add("err 0x%08lx: access fault (caught)\n", address); return; }
    strncpy_s(s.name, sizeof(s.name), tok[1], _TRUNCATE);
    s.address = address;
    s.length = length;
    s.tick = GetTickCount();
    s.used = true;
    g_out.Add("ok snapshot %s 0x%08lx %lu bytes\n", s.name, address, length);
}

// diff <name> [update]: changed dwords (offsets relative to the snapshot start) as hex, float and signed int
void CmdDiff(char **tok, int count, bool force) {
    if (count < 2) { g_out.Add("err usage: diff <name> [update]\n"); return; }
    int slot = FindSnapshot(tok[1]);
    if (slot < 0) { g_out.Add("err no snapshot '%s'\n", tok[1]); return; }
    Snapshot &s = g_snaps[slot];
    const char *why = CheckRange(s.address, s.length, false, force);
    if (why) { g_out.Add("err 0x%08lx: %s\n", s.address, why); return; }
    if (!ReadBytes(s.address, g_snapNow, s.length)) { g_out.Add("err 0x%08lx: access fault (caught)\n", s.address); return; }
    DWORD words = 0, bytes = 0;
    for (DWORD k = 0; k < s.length; ++k)
        if (s.data[k] != g_snapNow[k]) ++bytes;
    for (DWORD off = 0; off < s.length; off += 4) {
        DWORD n = s.length - off < 4 ? s.length - off : 4;
        if (memcmp(s.data + off, g_snapNow + off, n)) ++words;
    }
    g_out.Add("ok+ diff %s 0x%08lx %lu bytes: %lu dwords / %lu bytes changed after %lu ms (+offset address old new "
              "f:old f:new i:old i:new)\n", s.name, s.address, s.length, words, bytes, GetTickCount() - s.tick);
    DWORD shown = 0;
    for (DWORD off = 0; off < s.length; off += 4) {
        DWORD n = s.length - off < 4 ? s.length - off : 4;
        if (!memcmp(s.data + off, g_snapNow + off, n)) continue;
        if (++shown > 400) { g_out.Add("... more (only 400 shown)\n"); break; }
        DWORD a = 0, b = 0;
        memcpy(&a, s.data + off, n);
        memcpy(&b, g_snapNow + off, n);
        g_out.Add("+0x%04lx 0x%08lx %08lx %08lx f:%.6g f:%.6g i:%ld i:%ld\n", off, s.address + off, a, b,
                  ToNumber(kTypeFloat, a), ToNumber(kTypeFloat, b), static_cast<long>(a), static_cast<long>(b));
    }
    g_out.Add(".\n");
    if (count > 2 && !_stricmp(tok[2], "update")) {
        memcpy(s.data, g_snapNow, s.length);
        s.tick = GetTickCount();
    }
}

// ---- 0.4: live object inspection and manipulation (README "Objects (0.4)") ----
//
// All obj.* / uber.* / sticky.* / joint.* commands run as ONE job on the game thread (kKindObj, ObjRun): the server
// thread parses the line into g_oj, the game thread resolves the instance, reads / writes and fills g_out. So no read
// races the instance list, and every write happens where the game itself writes. Reads go through TlRead (VirtualQuery
// per region, guarded copy); decoders: TruLinkObj.h. Writes: obj.set pos / move / rot / yaw (instance +0x20 / +0x30),
// hide (INSTANCE_Post message 7, the game's hide / unhide), sticky.set (the store write + the game's change
// notification, as TruMenu sticky.set), uber.send (the game's command / message path 0x4d77a0 / 0x4d7680),
// joint.drive (the joint's own motor, limits untouched). Each write goes into the journal with its old value
// (obj.journal, obj.undo [all]) and into TruLink.log (LogLevel 1). collide and scale are refused: no proven field.

struct ObjJobArgs {
    int op;
    int argc;
    char argv[16][64];
    bool force;
};
enum { kOpNear = 1, kOpInfo, kOpSet, kOpUndo, kOpJournal, kOpEvents, kOpSend, kOpStGet, kOpStSet, kOpJGet, kOpJDrive,
       kOpPlace, kOpRefs, kOpJHold, kOpMarkRefs, kOpPuzzleList };   // 0.5.1: kOpMarkRefs; 0.5.2: kOpPuzzleList
ObjJobArgs g_oj;

const char *GroupWhy(int g) {
    static char why[96];
    if (g_grp[g]) return nullptr;
    _snprintf_s(why, sizeof(why), _TRUNCATE, "byte checks '%s' failed (status; other exe?)", tlobj::kGrpNames[g]);
    return why;
}
bool NeedGroups(std::initializer_list<int> groups) {
    for (int g : groups) {
        const char *why = GroupWhy(g);
        if (why) { g_out.Add("err %s\n", why); return false; }
    }
    return true;
}

// ---- journal ----
enum { kJPos = 1, kJRot, kJHide, kJSticky, kJUber, kJJoint, kJPlace };
const char *const kJNames[] = {"?", "pos", "rot", "hide", "sticky", "uber", "joint", "place"};
struct JEntry {
    int kind;
    DWORD inst, stamp, intro;
    float old[3], now[3];
    float oldRot[3], nowRot[3];              // 0.5 place: the instance rotation before / after
    DWORD oldWord, newWord;
    int stType;
    DWORD stOwner;
    WORD stKey;
    int stKind;
    bool undone;
    DWORD tick;
    char what[128];
};
const int kJMax = 256;
JEntry g_journal[kJMax];
JEntry *JournalAdd(int kind, DWORD inst) {
    if (g_jCount >= kJMax) return nullptr;
    JEntry &e = g_journal[g_jCount++];
    memset(&e, 0, sizeof(e));
    e.kind = kind;
    e.inst = inst;
    e.stamp = inst ? tlobj::D(inst + 0x44) : 0;
    e.intro = inst ? tlobj::D(inst + 0x58) : 0;
    e.tick = GetTickCount();
    return &e;
}
bool JournalRoom() {
    if (g_jCount < kJMax) return true;
    g_out.Add("err journal full (%d entries): obj.undo all, or obj.journal clear\n", kJMax);
    return false;
}
// the journaled instance still the same object (stamp +0x44 and intro id unchanged, in the list)
bool JAlive(const JEntry &e) {
    return e.inst && tlobj::D(e.inst + 0x44) == e.stamp && e.stamp && tlobj::D(e.inst + 0x58) == e.intro &&
           tlobj::ListIndex(e.inst) >= 0;
}

DWORD ObjInst(const char *arg) {
    char why[128];
    const DWORD inst = tlobj::FindInst(arg, why, sizeof(why));
    if (!inst) g_out.Add("err %s\n", why);
    return inst;
}
void InstLabel(DWORD inst, char *out, size_t n) {
    char name[64];
    tlobj::InstName(inst, name, sizeof(name));
    _snprintf_s(out, n, _TRUNCATE, "%ld %s (0x%08lx)", static_cast<LONG>(tlobj::D(inst + 0x58)), name, inst);
}
bool ParseFloat(const char *s, float *f) {
    char *end = nullptr;
    const double d = strtod(s, &end);
    if (end == s || *end || !(d > -1.0e9 && d < 1.0e9)) return false;
    *f = static_cast<float>(d);
    return true;
}
bool ParseDwordArg(const char *s, DWORD *v) { return ParseNumber(s, v); }

// ---- writes (game thread) ----
bool WriteFloats(DWORD a, const float *v, int n) {
    if (CheckRange(a, 4u * n, true, false)) return false;
    return CopyGuarded(a, reinterpret_cast<const BYTE *>(v), 4u * n);
}
void PostMsg(DWORD inst, int msg, int data) {
    reinterpret_cast<InstancePostFn>(kInstancePost)(reinterpret_cast<void *>(inst), msg, data);
}
typedef unsigned char(__fastcall *StNotifyFn)(void *store, void *edx, DWORD index, DWORD value);
typedef unsigned char(__fastcall *StNotifyFloatFn)(void *store, void *edx, DWORD index, float value);
// the store write + the game's change notification (TruMenu 0.21.1 sticky.set)
bool StWrite(const tlobj::StHit &h, DWORD raw) {
    bool ok = false;
    __try {
        if (h.type == 1) {
            volatile BYTE *bits = reinterpret_cast<volatile BYTE *>(*reinterpret_cast<volatile DWORD *>(h.store + 0x14) +
                                                                    (h.index >> 3));
            const BYTE bit = static_cast<BYTE>(1u << (h.index & 7));
            if (raw) *bits = static_cast<BYTE>(*bits | bit);
            else *bits = static_cast<BYTE>(*bits & ~bit);
            reinterpret_cast<StNotifyFn>(tlobj::kStNotify[1])(reinterpret_cast<void *>(h.store), nullptr, h.index, raw ? 1 : 0);
        } else {
            volatile DWORD *values = reinterpret_cast<volatile DWORD *>(*reinterpret_cast<volatile DWORD *>(h.store + 0x18));
            values[h.index] = raw;
            if (h.type == 0) {
                reinterpret_cast<StNotifyFn>(tlobj::kStNotify[0])(reinterpret_cast<void *>(h.store), nullptr, h.index, raw);
            } else {
                float f = 0.0f;
                memcpy(&f, &raw, 4);
                reinterpret_cast<StNotifyFloatFn>(tlobj::kStNotify[2])(reinterpret_cast<void *>(h.store), nullptr, h.index, f);
            }
        }
        ok = true;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
    }
    return ok;
}

// ---- obj.near / obj.info / uber.events / joint.get (reads) ----
void OpNear() {
    float metres = 10.0f;
    const char *filter = "";
    int max = 64;
    for (int i = 1; i < g_oj.argc; ++i) {
        if (!_stricmp(g_oj.argv[i], "max") && i + 1 < g_oj.argc) { max = atoi(g_oj.argv[++i]); continue; }
        float f = 0.0f;
        if (i == 1 && ParseFloat(g_oj.argv[i], &f)) metres = f;
        else filter = g_oj.argv[i];
    }
    if (!(metres > 0.0f && metres <= 500.0f)) { g_out.Add("err radius 0..500 m\n"); return; }
    tlobj::Near(metres * tlobj::kUnitsPerMetre, filter, max < 1 ? 1 : max > 400 ? 400 : max);
}
void OpInfo() {
    if (g_oj.argc < 2) { g_out.Add("err usage: obj.info <intro id | 0x<instance> | #<index> | player>\n"); return; }
    const DWORD inst = ObjInst(g_oj.argv[1]);
    if (inst) tlobj::Info(inst);
}
void OpEvents() {
    if (g_oj.argc < 2) { g_out.Add("err usage: uber.events <id> [all]\n"); return; }
    if (!NeedGroups({tlobj::kGrpCmd, tlobj::kGrpCheck})) return;
    const DWORD inst = ObjInst(g_oj.argv[1]);
    if (inst) tlobj::Events(inst, g_oj.argc > 2 && !_stricmp(g_oj.argv[2], "all"));
}
void OpRefs() {
    if (g_oj.argc < 2) { g_out.Add("err usage: obj.refs <id>\n"); return; }
    if (!NeedGroups({tlobj::kGrpScript, tlobj::kGrpSuper})) return;
    const DWORD inst = ObjInst(g_oj.argv[1]);
    if (inst) tlobj::Refs(inst);
}
void OpJointGet() {
    if (g_oj.argc < 3) { g_out.Add("err usage: joint.get <id> <index> (obj.info lists the joints)\n"); return; }
    if (!NeedGroups({tlobj::kGrpJoint})) return;
    const DWORD inst = ObjInst(g_oj.argv[1]);
    if (!inst) return;
    const DWORD x = tlobj::MultiOfAny(inst);
    if (!x) { g_out.Add("err %s has no multibody object (no joints)\n", g_oj.argv[1]); return; }
    const int index = atoi(g_oj.argv[2]);
    g_out.Add("ok+ joint.get %s %d (multibody X 0x%08lx of intro %lu, %d joints)\n", g_oj.argv[1], index, x,
              tlobj::D(tlobj::D(x + 0x58) + 0x58), tlobj::JointCount(x));
    tlobj::JointLine("", x, index);
    DWORD jrec = 0, joint = 0;
    if (tlobj::JointAt(x, index, &jrec, &joint)) {         // the range transitions on this joint in every linked uber
        for (int i = 0; i < tlobj::Links(x); ++i) {
            const DWORD li = tlobj::LinkInst(x, i), b = li ? tlobj::Uber(li) : 0;
            const DWORD cur = b ? tlobj::D(b + 0x84) : 0;
            for (int k = 0; b && k < tlobj::NodeCount(b); ++k) {
                const DWORD node = tlobj::NodeAddr(b, k);
                for (int j = 0; j < tlobj::TransCount(node); ++j) {
                    const DWORD t = tlobj::TransAt(node, j), c = tlobj::D(t + 0x18);
                    float lo = 0, hi = 0;
                    if ((c != 14 && c != 15) || tlobj::D(t + 0x20) != jrec || !tlobj::RangeOf(tlobj::D(t + 0x24), &lo, &hi)) continue;
                    char from[48], to[48];
                    tlobj::NodeName(b, k, from, sizeof(from));
                    tlobj::NodeName(b, static_cast<LONG>(tlobj::D(t + 4)), to, sizeof(to));
                    g_out.Add("link %d (intro %lu): node %d '%s'%s -> %lu '%s' on %s [%.2f, %.2f)\n", i, tlobj::D(li + 0x58), k,
                              from, static_cast<DWORD>(k) == cur ? " (current)" : "", tlobj::D(t + 4), to,
                              c == 14 ? "enter" : "leave", static_cast<double>(lo), static_cast<double>(hi));
                }
            }
        }
    }
    g_out.Add(".\n");
}

// ---- obj.set ----
void OpSet() {
    if (g_oj.argc < 3) {
        g_out.Add("err usage: obj.set <id> pos x y z | move dx dy dz | rot x y z (deg) | yaw deg | hide 0|1 | collide 0|1 | scale s\n");
        return;
    }
    if (!NeedGroups({tlobj::kGrpList})) return;
    const DWORD inst = ObjInst(g_oj.argv[1]);
    if (!inst) return;
    char label[96];
    InstLabel(inst, label, sizeof(label));
    const char *what = g_oj.argv[2];
    if (!_stricmp(what, "collide")) {
        g_out.Add("err collide: no proven collision switch on an instance (ENGINE.md 5.2 open) - refused; hide 1 also stops "
                  "the drawing only\n");
        return;
    }
    if (!_stricmp(what, "scale")) {
        float s[3] = {0, 0, 0};
        const DWORD irec = tlobj::D(inst + 0x100);
        if (irec) TlRead(irec + 0x40, s, 12);
        g_out.Add("err scale: no proven per-instance scale field (only the intro record +0x40 = %.3f %.3f %.3f, read at birth "
                  "?) - refused\n", static_cast<double>(s[0]), static_cast<double>(s[1]), static_cast<double>(s[2]));
        return;
    }
    if (!JournalRoom()) return;
    const DWORD x = tlobj::Multi(inst), body = tlobj::D(inst + 0x274);
    char note[160] = "";
    if (x) _snprintf_s(note, sizeof(note), _TRUNCATE, " - note: multibody placed instance (its parts are the links, obj.info)");
    else if (body) _snprintf_s(note, sizeof(note), _TRUNCATE, " - note: physics body +0x274 0x%08lx, the solver may move it back", body);
    if (!_stricmp(what, "pos") || !_stricmp(what, "move") || !_stricmp(what, "rot") || !_stricmp(what, "yaw")) {
        const bool isRot = !_stricmp(what, "rot") || !_stricmp(what, "yaw");
        const DWORD at = inst + (isRot ? 0x30 : 0x20);
        float old[3], v[3];
        if (!TlRead(at, old, 12)) { g_out.Add("err %s: +0x%x not readable\n", label, isRot ? 0x30 : 0x20); return; }
        memcpy(v, old, sizeof(v));
        if (!_stricmp(what, "yaw")) {
            float d = 0;
            if (g_oj.argc < 4 || !ParseFloat(g_oj.argv[3], &d)) { g_out.Add("err usage: obj.set <id> yaw <degrees>\n"); return; }
            v[2] = d / tlobj::kRadToDeg;
        } else {
            if (g_oj.argc < 6) { g_out.Add("err usage: obj.set <id> %s <x> <y> <z>\n", what); return; }
            for (int k = 0; k < 3; ++k) {
                float f = 0;
                if (!ParseFloat(g_oj.argv[3 + k], &f)) { g_out.Add("err bad number '%s'\n", g_oj.argv[3 + k]); return; }
                v[k] = !_stricmp(what, "move") ? old[k] + f : isRot ? f / tlobj::kRadToDeg : f;
            }
        }
        if (!WriteFloats(at, v, 3)) { g_out.Add("err %s: write failed\n", label); return; }
        JEntry *e = JournalAdd(isRot ? kJRot : kJPos, inst);
        memcpy(e->old, old, sizeof(old));
        memcpy(e->now, v, sizeof(v));
        _snprintf_s(e->what, sizeof(e->what), _TRUNCATE, "%s %s", label, isRot ? "rot" : "pos");
        if (isRot)
            g_out.Add("ok %s rot %.2f %.2f %.2f deg (was %.2f %.2f %.2f) journal #%d%s\n", label, tlobj::Deg(v[0]),
                      tlobj::Deg(v[1]), tlobj::Deg(v[2]), tlobj::Deg(old[0]), tlobj::Deg(old[1]), tlobj::Deg(old[2]), g_jCount - 1, note);
        else
            g_out.Add("ok %s pos %.2f %.2f %.2f (was %.2f %.2f %.2f) journal #%d%s\n", label, static_cast<double>(v[0]),
                      static_cast<double>(v[1]), static_cast<double>(v[2]), static_cast<double>(old[0]),
                      static_cast<double>(old[1]), static_cast<double>(old[2]), g_jCount - 1, note);
        Log(1, "obj.set %s %s %.3f %.3f %.3f (was %.3f %.3f %.3f) journal #%d", label, isRot ? "rot (rad)" : "pos",
            static_cast<double>(v[0]), static_cast<double>(v[1]), static_cast<double>(v[2]), static_cast<double>(old[0]),
            static_cast<double>(old[1]), static_cast<double>(old[2]), g_jCount - 1);
        return;
    }
    if (!_stricmp(what, "hide")) {
        if (!g_postOk || !NeedGroups({tlobj::kGrpHide})) { if (!g_postOk) g_out.Add("err INSTANCE_Post not verified\n"); return; }
        if (g_oj.argc < 4 || (strcmp(g_oj.argv[3], "0") && strcmp(g_oj.argv[3], "1"))) { g_out.Add("err usage: obj.set <id> hide 0|1\n"); return; }
        const int hide = g_oj.argv[3][0] == '1' ? 1 : 0;
        if (!tlobj::D(inst + 0x120)) { g_out.Add("err %s has no message handler (+0x120 = 0)\n", label); return; }
        // the state shown: the instance itself, for a multibody placed instance its first part (the handler hides the parts)
        const DWORD probe = x && tlobj::LinkInst(x, 0) ? tlobj::LinkInst(x, 0) : inst;
        const DWORD before = tlobj::D(probe + 0x14);
        PostMsg(inst, 7, hide);
        const DWORD after = tlobj::D(probe + 0x14);
        JEntry *e = JournalAdd(kJHide, inst);
        e->oldWord = (before & 0x800) ? 1 : 0;
        e->newWord = static_cast<DWORD>(hide);
        _snprintf_s(e->what, sizeof(e->what), _TRUNCATE, "%s hide %d", label, hide);
        g_out.Add("ok %s: INSTANCE_Post(7, %d)%s - iflags 0x%08lx -> 0x%08lx (%s) journal #%d\n", label, hide,
                  x ? " to the multibody (all parts)" : "", before, after, (after & 0x800) ? "hidden" : "shown", g_jCount - 1);
        Log(1, "obj.set %s hide %d: INSTANCE_Post(0x%08lx, 7, %d), iflags 0x%08lx -> 0x%08lx, journal #%d", label, hide,
            inst, hide, before, after, g_jCount - 1);
        return;
    }
    g_out.Add("err unknown obj.set field '%s' (pos move rot yaw hide collide scale)\n", what);
}

// ---- 0.5 obj.place: a physics object (body +0x274) through the game's own placement path ----
// The drawn pose of a body object follows its body (the sync 0x497610 writes instance +0x20 / +0x30 from the body
// every frame), so obj.set pos alone is undone at once. What the game itself does to put such an object somewhere
// (message 0x75 at 0x6c2a5c..0x6c2a91, the same at 0x6bd193..0x6bd1da; the birth placement 0x6baf8b..0x6bafc8):
// INSTANCE_SetPosition 0x5b4100 (instance +0x20, the attached parts, the body origin), optionally INSTANCE_SetRotation
// 0x5b4040 (+0x30 and the body quaternion), then 0x497740(body, inst) = the body pose from the instance pose and the
// centre of mass +0x250. TruLink adds the game's velocity setters (0x4d8df0 / 0x4d8e30: 0) and the body wake 0x4d8fd0,
// so the object falls and settles where it was put. 0.5.1: PlaceCalls / PlaceBody moved unchanged to TruLinkAct.h
// (TruMenu 0.22.56 "Gewicht zu mir" runs the same code).
using tlact::PlaceBody;
void OpPlace() {
    if (g_oj.argc < 3) {
        g_out.Add("err usage: obj.place <id> near-lara [m] | at <x> <y> <z> | onto <id> [dz]  [yaw <deg>] [force]\n");
        return;
    }
    if (!NeedGroups({tlobj::kGrpList, tlobj::kGrpPlace})) return;
    if (!JournalRoom()) return;
    const DWORD inst = ObjInst(g_oj.argv[1]);
    if (!inst) return;
    char label[96];
    InstLabel(inst, label, sizeof(label));
    if (tlobj::Multi(inst)) { g_out.Add("err %s is a multibody placed instance (its parts are links) - not placeable\n", label); return; }
    const DWORD body = tlobj::BodyOf(inst);
    if (!body) {
        g_out.Add("err %s has no physics body (+0x274 0x%08lx) - obj.set pos moves such an instance\n", label,
                  tlobj::D(inst + 0x274));
        return;
    }
    const DWORD player = tlobj::D(tlobj::kPlayer), holder = tlobj::HolderOf(inst);
    if (holder && holder == player && !g_oj.force) {
        g_out.Add("err %s: its holder handle is the player (carried?) - drop it first, or force\n", label);
        return;
    }
    float old[3] = {0, 0, 0}, oldRot[3] = {0, 0, 0}, target[3] = {0, 0, 0}, bodyOld[3] = {0, 0, 0};
    TlRead(inst + 0x20, old, 12);
    TlRead(inst + 0x30, oldRot, 12);
    TlRead(body + 0x80, bodyOld, 12);
    const char *how = g_oj.argv[2];
    int at = 3;
    char where[128];
    if (!_stricmp(how, "near-lara") || !_stricmp(how, "near")) {
        float lara[3], lrot[3], m = 1.5f;
        if (!player || !TlRead(player + 0x20, lara, 12) || !TlRead(player + 0x30, lrot, 12)) { g_out.Add("err no player\n"); return; }
        if (at < g_oj.argc && ParseFloat(g_oj.argv[at], &m)) ++at;
        if (!(m >= 0.0f && m <= 20.0f)) { g_out.Add("err distance 0..20 m\n"); return; }
        const float d = m * tlobj::kUnitsPerMetre;            // forward (-sin yaw, cos yaw): ENGINE camera rows; Lara: guess
        target[0] = lara[0] - sinf(lrot[2]) * d;
        target[1] = lara[1] + cosf(lrot[2]) * d;
        target[2] = lara[2] + 100.0f;
        _snprintf_s(where, sizeof(where), _TRUNCATE, "%.1f m in front of Lara (yaw %.1f deg), 100 units up", static_cast<double>(m),
                    tlobj::Deg(lrot[2]));
    } else if (!_stricmp(how, "at")) {
        if (g_oj.argc < 6) { g_out.Add("err usage: obj.place <id> at <x> <y> <z>\n"); return; }
        for (int k = 0; k < 3; ++k)
            if (!ParseFloat(g_oj.argv[3 + k], &target[k])) { g_out.Add("err bad number '%s'\n", g_oj.argv[3 + k]); return; }
        at = 6;
        _snprintf_s(where, sizeof(where), _TRUNCATE, "at the given point");
    } else if (!_stricmp(how, "onto")) {
        if (g_oj.argc < 4) { g_out.Add("err usage: obj.place <id> onto <id> [dz]\n"); return; }
        const DWORD other = ObjInst(g_oj.argv[3]);
        if (!other) return;
        if (other == inst) { g_out.Add("err onto itself\n"); return; }
        float dz = 150.0f;
        at = 4;
        if (at < g_oj.argc && ParseFloat(g_oj.argv[at], &dz)) ++at;
        if (!(dz >= -1000.0f && dz <= 3000.0f)) { g_out.Add("err dz -1000..3000 units\n"); return; }
        TlRead(other + 0x20, target, 12);
        target[2] += dz;
        char ol[96];
        InstLabel(other, ol, sizeof(ol));
        _snprintf_s(where, sizeof(where), _TRUNCATE, "%.0f units above the origin of %s", static_cast<double>(dz), ol);
    } else {
        g_out.Add("err '%s': near-lara | at | onto\n", how);
        return;
    }
    float rot[3] = {0, 0, 0};
    bool setRot = false;
    for (int i = at; i + 1 < g_oj.argc; ++i) {
        if (_stricmp(g_oj.argv[i], "yaw")) continue;
        float yaw = 0.0f;
        if (!ParseFloat(g_oj.argv[i + 1], &yaw)) { g_out.Add("err bad yaw '%s'\n", g_oj.argv[i + 1]); return; }
        rot[2] = yaw / tlobj::kRadToDeg;                        // upright: x = y = 0
        setRot = true;
    }
    if (!PlaceBody(inst, target, setRot ? rot : nullptr)) { g_out.Add("err %s: access fault in the game's placement path (caught)\n", label); return; }
    float now[3] = {0, 0, 0}, nowRot[3] = {0, 0, 0}, bodyNow[3] = {0, 0, 0};
    TlRead(inst + 0x20, now, 12);
    TlRead(inst + 0x30, nowRot, 12);
    TlRead(body + 0x80, bodyNow, 12);
    JEntry *e = JournalAdd(kJPlace, inst);
    memcpy(e->old, old, sizeof(old));
    memcpy(e->oldRot, oldRot, sizeof(oldRot));
    memcpy(e->now, now, sizeof(now));
    memcpy(e->nowRot, nowRot, sizeof(nowRot));
    _snprintf_s(e->what, sizeof(e->what), _TRUNCATE, "%s place", label);
    g_out.Add("ok %s placed %s: instance %.1f %.1f %.1f (was %.1f %.1f %.1f) body %.1f %.1f %.1f (was %.1f %.1f %.1f)%s, "
              "velocity 0, woken - INSTANCE_SetPosition 0x%08lx%s + body <- instance 0x%08lx; journal #%d\n", label, where,
              static_cast<double>(now[0]), static_cast<double>(now[1]), static_cast<double>(now[2]), static_cast<double>(old[0]),
              static_cast<double>(old[1]), static_cast<double>(old[2]), static_cast<double>(bodyNow[0]),
              static_cast<double>(bodyNow[1]), static_cast<double>(bodyNow[2]), static_cast<double>(bodyOld[0]),
              static_cast<double>(bodyOld[1]), static_cast<double>(bodyOld[2]), setRot ? ", upright" : "", tlobj::kSetPos,
              setRot ? " + INSTANCE_SetRotation" : "", tlobj::kBodyToInst, g_jCount - 1);
    Log(1, "obj.place %s %s: instance %.2f %.2f %.2f (was %.2f %.2f %.2f) rot z %.2f deg (was %.2f), body %.2f %.2f %.2f "
        "(was %.2f %.2f %.2f)%s, journal #%d", label, where, static_cast<double>(now[0]), static_cast<double>(now[1]),
        static_cast<double>(now[2]), static_cast<double>(old[0]), static_cast<double>(old[1]), static_cast<double>(old[2]),
        tlobj::Deg(nowRot[2]), tlobj::Deg(oldRot[2]), static_cast<double>(bodyNow[0]), static_cast<double>(bodyNow[1]),
        static_cast<double>(bodyNow[2]), static_cast<double>(bodyOld[0]), static_cast<double>(bodyOld[1]),
        static_cast<double>(bodyOld[2]), g_oj.force ? " (force)" : "", g_jCount - 1);
}

// ---- sticky.get / sticky.set ----
// owner: intro id (kind 0) or <kind>:<id>; key: a Symbol number, or a script member of the owner's instance: m<k>
// (member index, obj.info) or +<offset> (member data offset)
bool StResolve(const char *ownerArg, const char *keyArg, int *kind, DWORD *owner, WORD *key, char *label, size_t ln) {
    *kind = 0;
    char ow[64];
    strncpy_s(ow, sizeof(ow), ownerArg, _TRUNCATE);
    char *idText = ow;
    if (char *colon = strchr(ow, ':')) { *colon = 0; *kind = atoi(ow); idText = colon + 1; }
    DWORD id = 0;
    if (*kind < 0 || *kind > 2 || !ParseNumber(idText, &id)) { g_out.Add("err owner '%s': intro id or <kind 0..2>:<id>\n", ownerArg); return false; }
    *owner = id;
    if (keyArg[0] == 'm' || keyArg[0] == 'M' || keyArg[0] == '+') {
        if (*kind) { g_out.Add("err a member name needs an intro id owner (kind 0)\n"); return false; }
        if (!NeedGroups({tlobj::kGrpScript})) return false;
        const DWORD inst = tlobj::InstByIntro(id);
        const DWORD so = inst ? tlobj::ScriptObj(inst) : 0, root = so ? tlobj::ScriptRoot(so) : 0;
        if (!root) { g_out.Add("err intro %lu: no instance with a script object\n", id); return false; }
        const bool byOffset = keyArg[0] == '+';
        DWORD want = 0;
        if (!ParseNumber(keyArg + 1, &want)) { g_out.Add("err bad member '%s' (m<index> or +<offset>)\n", keyArg); return false; }
        for (int k = 0; k < tlobj::MemberCount(root); ++k) {
            tlobj::Member m;
            if (!tlobj::MemberAt(root, k, &m) || (byOffset ? m.offset != want : static_cast<DWORD>(k) != want)) continue;
            if (!tlobj::IsSticky(m)) { g_out.Add("err member %s of intro %lu is %s, not a sticky\n", keyArg, id, m.type); return false; }
            if (!tlobj::MemberKey(m, key)) { g_out.Add("err member %s: key unreadable\n", keyArg); return false; }
            *owner = tlobj::D(tlobj::ScriptOwner(inst) + 0x58);
            _snprintf_s(label, ln, _TRUNCATE, "m%d +%u %s", k, m.offset, m.type);
            return true;
        }
        g_out.Add("err intro %lu has no member %s (obj.info lists them)\n", id, keyArg);
        return false;
    }
    DWORD k = 0;
    if (!ParseNumber(keyArg, &k) || k > 0xffff) { g_out.Add("err key '%s': a u16 Symbol, m<index> or +<offset>\n", keyArg); return false; }
    *key = static_cast<WORD>(k);
    _snprintf_s(label, ln, _TRUNCATE, "key %lu", k);
    return true;
}
void OpStGet() {
    if (g_oj.argc < 3) { g_out.Add("err usage: sticky.get <owner> <key | m<index> | +<offset>>\n"); return; }
    if (!NeedGroups({tlobj::kGrpSticky})) return;
    int kind = 0;
    DWORD owner = 0;
    WORD key = 0;
    char label[64];
    if (!StResolve(g_oj.argv[1], g_oj.argv[2], &kind, &owner, &key, label, sizeof(label))) return;
    tlobj::StHit hits[3];
    char why[96];
    const int k = tlobj::StFind(kind, owner, key, hits, why, sizeof(why));
    if (k < 0) { g_out.Add("err %s\n", why); return; }
    if (!k) { g_out.Add("ok sticky %d:%lu key %u (%s): no store entry (not created yet - the script has not used it)\n", kind, owner, key, label); return; }
    for (int i = 0; i < k; ++i) {
        DWORD raw = 0;
        char v[32] = "?";
        if (tlobj::StRaw(hits[i], &raw)) tlobj::StText(hits[i].type, raw, v, sizeof(v));
        g_out.Add("ok sticky %d:%lu key %u (%s) = %s %s (index %lu)\n", kind, owner, key, label, tlobj::kStTypes[hits[i].type],
                  v, hits[i].index);
    }
}
void OpStSet() {
    int at = 1, want = -1;
    for (int t = 0; t < 3 && at < g_oj.argc; ++t)
        if (!_stricmp(g_oj.argv[at], tlobj::kStTypes[t])) { want = t; ++at; break; }
    if (g_oj.argc - at < 3) { g_out.Add("err usage: sticky.set [int|bool|float] <owner> <key | m<index> | +<offset>> <value>\n"); return; }
    if (!NeedGroups({tlobj::kGrpSticky})) return;
    if (!JournalRoom()) return;
    int kind = 0;
    DWORD owner = 0;
    WORD key = 0;
    char label[64];
    if (!StResolve(g_oj.argv[at], g_oj.argv[at + 1], &kind, &owner, &key, label, sizeof(label))) return;
    tlobj::StHit hits[3];
    char why[96];
    const int k = tlobj::StFind(kind, owner, key, hits, why, sizeof(why));
    if (k < 0) { g_out.Add("err %s\n", why); return; }
    int pick = -1;
    for (int i = 0; i < k; ++i)
        if (want < 0 || hits[i].type == want) { if (pick >= 0) { pick = -2; break; } pick = i; }
    if (pick == -2) { g_out.Add("err sticky %d:%lu key %u is in more than one store - say int / bool / float first\n", kind, owner, key); return; }
    if (pick < 0) { g_out.Add("err sticky %d:%lu key %u: no %s entry (never created - not set)\n", kind, owner, key, want >= 0 ? tlobj::kStTypes[want] : ""); return; }
    const tlobj::StHit &h = hits[pick];
    const char *text = g_oj.argv[at + 2];
    DWORD raw = 0;
    if (h.type == 2) {
        float f = 0;
        if (!ParseFloat(text, &f)) { g_out.Add("err value '%s' is not a float\n", text); return; }
        memcpy(&raw, &f, 4);
    } else if (!ParseNumber(text, &raw) || (h.type == 1 && raw > 1)) {
        g_out.Add("err value '%s' is not %s\n", text, h.type == 1 ? "0 / 1" : "an integer");
        return;
    }
    DWORD old = 0;
    if (!tlobj::StRaw(h, &old)) { g_out.Add("err the value cannot be read (index %lu)\n", h.index); return; }
    if (!StWrite(h, raw)) { g_out.Add("err access fault while setting the sticky (caught)\n"); return; }
    DWORD now = 0;
    tlobj::StRaw(h, &now);
    char a[32], b[32];
    tlobj::StText(h.type, old, a, sizeof(a));
    tlobj::StText(h.type, now, b, sizeof(b));
    JEntry *e = JournalAdd(kJSticky, 0);
    e->stType = h.type; e->stOwner = owner; e->stKey = key; e->stKind = kind; e->oldWord = old; e->newWord = now;
    _snprintf_s(e->what, sizeof(e->what), _TRUNCATE, "sticky %d:%lu key %u (%s) %s", kind, owner, key, label, tlobj::kStTypes[h.type]);
    g_out.Add("ok sticky %d:%lu key %u (%s, %s): %s -> %s (the game's set + notification 0x%08lx) journal #%d\n", kind, owner,
              key, label, tlobj::kStTypes[h.type], a, b, tlobj::kStNotify[h.type], g_jCount - 1);
    Log(1, "sticky.set %s %d:%lu key %u (%s, index %lu): %s -> %s, journal #%d", tlobj::kStTypes[h.type], kind, owner, key,
        label, h.index, a, b, g_jCount - 1);
}

// ---- uber.send ----
typedef void(__thiscall *UberMsgFn)(void *b, const void *record);
void NodeNow(DWORD b, char *out, size_t n) {
    char node[48], to[48] = "";
    tlobj::NodeName(b, static_cast<LONG>(tlobj::D(b + 0x84)), node, sizeof(node));
    const DWORD trans = tlobj::D(b + 0x80);
    if (trans) tlobj::NodeName(b, static_cast<LONG>(tlobj::D(trans + 4)), to, sizeof(to));
    _snprintf_s(out, n, _TRUNCATE, "'%s'%s%s%s", node, trans ? " -> '" : "", to, trans ? "' (transition runs)" : "");
}
void OpSend() {
    if (g_oj.argc < 4) {
        g_out.Add("err usage: uber.send <id> cmd <n> | command <c> | event <v> | broadcast <v> [link <k>] [force] "
                  "(uber.events lists them)\n");
        return;
    }
    if (!NeedGroups({tlobj::kGrpUber, tlobj::kGrpMulti, tlobj::kGrpCmd, tlobj::kGrpMsg})) return;
    if (!JournalRoom()) return;
    const DWORD inst = ObjInst(g_oj.argv[1]);
    if (!inst) return;
    char label[96];
    InstLabel(inst, label, sizeof(label));
    const char *how = g_oj.argv[2];
    DWORD value = 0;
    if (!ParseNumber(g_oj.argv[3], &value)) { g_out.Add("err bad number '%s'\n", g_oj.argv[3]); return; }
    int link = -1;
    for (int i = 4; i + 1 < g_oj.argc; ++i)
        if (!_stricmp(g_oj.argv[i], "link")) link = atoi(g_oj.argv[i + 1]);
    if (!_stricmp(how, "cmd")) {                               // the object command table: X vf+4 (0x4d77a0)
        const DWORD x = tlobj::MultiOfAny(inst);
        if (!x) { g_out.Add("err %s has no multibody object (no command table)\n", label); return; }
        if (tlobj::D(tlobj::D(x) + 4) != tlobj::kCmdExec) { g_out.Add("err X 0x%08lx vf+4 is not 0x%08lx - refused\n", x, tlobj::kCmdExec); return; }
        if (static_cast<int>(value) >= tlobj::CmdCount(x)) { g_out.Add("err cmd %lu: the table has %d entries (uber.events)\n", value, tlobj::CmdCount(x)); return; }
        DWORD rec = 0;
        int rn = 0;
        tlobj::CmdRecords(x, static_cast<int>(value), &rec, &rn);
        char before[16][96];
        for (int r = 0; r < rn && r < 16; ++r) {
            const DWORD li = tlobj::LinkInst(x, static_cast<int>(tlobj::D(rec + 12u * r))), b = li ? tlobj::Uber(li) : 0;
            if (b) NodeNow(b, before[r], sizeof(before[r])); else strcpy_s(before[r], "-");
        }
        if (!tlact::CmdExec(x, static_cast<int>(value))) {    // 0.5.1: the shared call (TruLinkAct.h, TruMenu figures)
            g_out.Add("err %s cmd %lu: access fault in X vf+4 0x%08lx (caught)\n", label, value, tlobj::kCmdExec);
            return;
        }
        JEntry *e = JournalAdd(kJUber, inst);
        _snprintf_s(e->what, sizeof(e->what), _TRUNCATE, "%s cmd %lu", label, value);
        g_out.Add("ok+ uber.send %s cmd %lu: X 0x%08lx vf+4 (0x%08lx, the object command table - as uber action 11 / a "
                  "script command) journal #%d (not undoable)\n", label, value, x, tlobj::kCmdExec, g_jCount - 1);
        for (int r = 0; r < rn && r < 16; ++r) {
            const DWORD e0 = rec + 12u * r;
            const int l = static_cast<int>(tlobj::D(e0));
            const DWORD li = tlobj::LinkInst(x, l), b = li ? tlobj::Uber(li) : 0, kind = tlobj::D(e0 + 4);
            char after[96] = "-";
            if (b) NodeNow(b, after, sizeof(after));
            g_out.Add("link %d (intro %lu) %s %lu: %s -> %s\n", l, li ? tlobj::D(li + 0x58) : 0,
                      kind <= 4 ? tlobj::kKindNames[kind] : "kind?", tlobj::D(e0 + 8), before[r], after);
            Log(1, "uber.send %s cmd %lu: link %d (intro %lu) %s %lu: %s -> %s", label, value, l, li ? tlobj::D(li + 0x58) : 0,
                kind <= 4 ? tlobj::kKindNames[kind] : "kind?", tlobj::D(e0 + 8), before[r], after);
        }
        g_out.Add(".\n");
        return;
    }
    DWORD kind = 0;
    if (!_stricmp(how, "event")) kind = 2;
    else if (!_stricmp(how, "broadcast")) kind = 3;
    else if (!_stricmp(how, "command")) kind = 4;
    else { g_out.Add("err '%s': cmd | command | event | broadcast (set node is refused: not the game's event path)\n", how); return; }
    DWORD b = tlobj::Uber(inst);
    if (!b) {                                                  // a multibody placed instance: one of its links
        const DWORD x = tlobj::Multi(inst);
        if (!x) { g_out.Add("err %s has no uber state and no multibody object\n", label); return; }
        if (link >= 0) {
            const DWORD li = tlobj::LinkInst(x, link);
            b = li ? tlobj::Uber(li) : 0;
            if (!b) { g_out.Add("err %s link %d has no uber state\n", label, link); return; }
        } else {
            int matches = 0;
            for (int i = 0; i < tlobj::Links(x); ++i) {
                const DWORD li = tlobj::LinkInst(x, i), lb = li ? tlobj::Uber(li) : 0;
                bool dropped = false;
                if (lb && tlobj::MatchNow(lb, kind, value, &dropped)) { b = lb; link = i; ++matches; }
            }
            if (matches != 1) {
                g_out.Add("err %s: %d links take %s %lu now - give 'link <k>' (uber.events)\n", label, matches, how, value);
                return;
            }
        }
    }
    bool dropped = false;
    const DWORD t = tlobj::MatchNow(b, kind, value, &dropped);
    char before[96];
    NodeNow(b, before, sizeof(before));
    if (dropped && !g_oj.force) { g_out.Add("err uber 0x%08lx node %s: the engine drops events now (transition / +0x90 & 9) - try again, or force\n", b, before); return; }
    if (!t && !g_oj.force) { g_out.Add("err uber 0x%08lx node %s has no transition on %s %lu now (uber.events) - force sends it anyway\n", b, before, how, value); return; }
    const DWORD record[3] = {0, kind, value};
    reinterpret_cast<UberMsgFn>(tlobj::kUberMsg)(reinterpret_cast<void *>(b), record);
    char after[96];
    NodeNow(b, after, sizeof(after));
    JEntry *e = JournalAdd(kJUber, inst);
    _snprintf_s(e->what, sizeof(e->what), _TRUNCATE, "%s %s %lu%s", label, how, value, link >= 0 ? " (link)" : "");
    g_out.Add("ok uber.send %s%s %s %lu: 0x%08lx (uber message kind %lu, the game's path): %s -> %s journal #%d (not undoable)\n",
              label, link >= 0 ? " link" : "", how, value, tlobj::kUberMsg, kind, before, after, g_jCount - 1);
    Log(1, "uber.send %s %s %lu (uber 0x%08lx, link %d, kind %lu%s): %s -> %s, journal #%d", label, how, value, b, link, kind,
        g_oj.force ? ", force" : "", before, after, g_jCount - 1);
}

// ---- joint.drive: the joint's own motor (velocity + force, axis 0) towards a target; the limits stay as they are ----
// 2026-11-15: TruMenu 0.22.53 joint.set (lock lo = hi = target) drove the l3_chapel shadow door rail from -0.84 to -1115
// - the lock replaced the joint's limits [0, 948.2], nothing held the body. joint.drive never touches the limits: the
// target is clamped inside them (limit on, lo < hi), the motor pushes at a ramped velocity with a bounded force, and the
// drive stops (saved motor velocity / force / enable put back) on: reached (after the hold), moving away from the target
// (one sign flip allowed - the motor sign is not proven), overshoot, a step larger than 4x the commanded one, leaving
// the limits, no progress for 1.5 s, a node change of any linked uber, 10 s, or joint.drive stop.
// 0.5.1: the Drive record, JtMotor / JtWakeBodies / LinkState, DriveStop and DriveTick moved unchanged to TruLinkAct.h
// (only the log prefix comes from the DriveCtl: "joint.drive" here); g_drv / g_driveOn are references into g_dc.
typedef double(__thiscall *JtValueFn)(void *joint);
using tlact::Drive;
using tlact::LinkState;
}  // namespace

bool TlJointValue(DWORD joint, int type, float *value) {
    if (!g_onGameThread || !g_grp[tlobj::kGrpJoint] || (type != 1 && type != 3)) return false;
    double r = 0.0;
    __try {
        r = reinterpret_cast<JtValueFn>(type == 1 ? tlobj::kJtHinge : tlobj::kJtSlider)(reinterpret_cast<void *>(joint));
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
    if (type == 1) r *= 57.29577951308232;
    if (!(r > -1.0e7 && r < 1.0e7)) return false;
    *value = static_cast<float>(r);
    return true;
}

namespace {
DWORD g_tlRegStart = 0, g_tlRegEnd = 0;        // last region TlRead found readable (one job / tick)
}  // namespace

bool TlRead(DWORD address, void *out, DWORD length) {
    if (!length || address + length < address) return false;
    DWORD p = address, end = address + length;
    while (p < end) {
        if (p >= g_tlRegStart && p < g_tlRegEnd) { p = g_tlRegEnd; continue; }
        MEMORY_BASIC_INFORMATION mbi;
        if (!VirtualQuery(reinterpret_cast<void *>(p), &mbi, sizeof(mbi))) return false;
        if (mbi.State != MEM_COMMIT || (mbi.Protect & (PAGE_GUARD | PAGE_NOACCESS)) || !(mbi.Protect & kReadable)) return false;
        const bool inImage = p >= g_imageStart && p < g_imageEnd;
        if (!inImage && mbi.Type != MEM_PRIVATE) return false;
        g_tlRegStart = reinterpret_cast<DWORD>(mbi.BaseAddress);
        g_tlRegEnd = g_tlRegStart + static_cast<DWORD>(mbi.RegionSize);
        if (g_tlRegEnd <= p) return false;
        p = g_tlRegEnd;
    }
    return ReadBytes(address, static_cast<BYTE *>(out), length);
}

// keeps 1 KB for the block end: a long answer (a big uber graph) is cut with a note, never without its "." line
void TlAdd(const char *fmt, ...) {
    static size_t cutAt = 0;
    const bool end = !strcmp(fmt, ".\n");
    if (g_out.n == 0) cutAt = 0;
    if (!end && g_out.n + 1024 >= sizeof(g_out.buf)) {
        if (!cutAt) {
            cutAt = g_out.n;
            g_out.Add("... answer cut (buffer %lu KB full)\n", static_cast<DWORD>(sizeof(g_out.buf) / 1024));
        }
        return;
    }
    va_list ap;
    va_start(ap, fmt);
    const int w = _vsnprintf_s(g_out.buf + g_out.n, sizeof(g_out.buf) - g_out.n, _TRUNCATE, fmt, ap);
    va_end(ap);
    g_out.n = w < 0 ? strlen(g_out.buf) : g_out.n + static_cast<size_t>(w);
}

// 0.5.1: TruLinkAct.h needs a log and the TlRead cache reset
void TlLog(int level, _Printf_format_string_ const char *fmt, ...) {
    char text[1024];
    va_list ap;
    va_start(ap, fmt);
    _vsnprintf_s(text, sizeof(text), _TRUNCATE, fmt, ap);
    va_end(ap);
    Log(level, "%s", text);
}
void TlReadReset() { g_tlRegStart = g_tlRegEnd = 0; }

namespace {

// the journal row of a stopped drive has nothing left to undo (0.4 behaviour, now the DriveCtl's end callback)
void DriveEnded(int journal) {
    if (journal >= 0 && journal < g_jCount) g_journal[journal].undone = true;
}
void DriveStop(const char *why) { tlact::DriveStop(g_dc, why); }
void DriveTick() { tlact::DriveTick(g_dc, *reinterpret_cast<volatile DWORD *>(kGameClock)); }
void OpJointDrive() {
    if (g_oj.argc >= 2 && !_stricmp(g_oj.argv[1], "stop")) {
        if (!g_driveOn) { g_out.Add("ok joint.drive: nothing running\n"); return; }
        DriveStop("stopped (joint.drive stop)");
        g_out.Add("ok joint.drive stopped (TruLink.log)\n");
        return;
    }
    if (g_oj.argc >= 2 && !_stricmp(g_oj.argv[1], "status")) {
        if (!g_driveOn) { g_out.Add("ok joint.drive: idle\n"); return; }
        g_out.Add("ok joint.drive %ld joint %d -> %.2f since %.1f s, last value %.2f, motor velocity %.2f %s%s%s\n",
                  g_drv.intro, g_drv.index, static_cast<double>(g_drv.target), (GetTickCount() - g_drv.start) / 1000.0,
                  static_cast<double>(g_drv.lastV), static_cast<double>(g_drv.vel), g_drv.type == 1 ? "deg/s" : "units/s",
                  g_drv.holdOff ? (g_drv.reached ? ", HOLDING until joint.hold off" : ", hold-until-off (approaching)") : "",
                  g_drv.holdOff && g_drv.corrections ? " (pushed back - see TruLink.log)" : "");
        return;
    }
    if (g_oj.argc < 4) {
        g_out.Add("err usage: joint.drive <id> <index> <target: hinge deg | rail units> [speed s] [force f] [hold s] "
                  "[through 1] | stop | status\n");
        return;
    }
    if (!NeedGroups({tlobj::kGrpMulti, tlobj::kGrpJoint, tlobj::kGrpDrive})) return;
    if (!JournalRoom()) return;
    const DWORD inst = ObjInst(g_oj.argv[1]);
    if (!inst) return;
    const DWORD x = tlobj::MultiOfAny(inst);
    if (!x) { g_out.Add("err %s has no multibody object (no joints)\n", g_oj.argv[1]); return; }
    const int index = atoi(g_oj.argv[2]);
    float target = 0.0f;
    if (!ParseFloat(g_oj.argv[3], &target)) { g_out.Add("err bad target '%s'\n", g_oj.argv[3]); return; }
    DWORD jrec = 0, joint = 0;
    if (!tlobj::JointAt(x, index, &jrec, &joint)) { g_out.Add("err no joint %d (obj.info lists %d)\n", index, tlobj::JointCount(x)); return; }
    const int type = tlobj::JointType(joint);
    if (type != 1 && type != 3) { g_out.Add("err joint %d: physics type %d - only hinge (1) / rail (3)\n", index, type); return; }
    const bool hinge = type == 1;
    float v = 0.0f, lim[2] = {0, 0}, vel = 0, force = 0;
    DWORD flags = 0;
    if (!TlJointValue(joint, type, &v) || !tlobj::RF(joint + 0xd8, &lim[0]) || !tlobj::RF(joint + 0xdc, &lim[1]) ||
        !tlobj::R32(joint + 0x174, &flags) || !tlobj::RF(joint + 0x108, &vel) || !tlobj::RF(joint + 0x10c, &force)) {
        g_out.Add("err joint %d: value / limits / motor unreadable\n", index);
        return;
    }
    Drive d;
    memset(&d, 0, sizeof(d));
    d.speed = hinge ? 30.0f : 150.0f;
    d.force = 20000.0f;
    d.hold = 2.0f;
    for (int i = 4; i < g_oj.argc; i += 2) {
        if (!_stricmp(g_oj.argv[i], "hold-until-off")) { d.holdOff = true; --i; continue; }   // 0.5: a flag, no value
        float f = 0.0f;
        if (i + 1 >= g_oj.argc) { g_out.Add("err option '%s' needs a value\n", g_oj.argv[i]); return; }
        if (!ParseFloat(g_oj.argv[i + 1], &f)) { g_out.Add("err bad number '%s'\n", g_oj.argv[i + 1]); return; }
        if (!_stricmp(g_oj.argv[i], "speed")) d.speed = f;
        else if (!_stricmp(g_oj.argv[i], "force")) d.force = f;
        else if (!_stricmp(g_oj.argv[i], "hold")) d.hold = f;
        else if (!_stricmp(g_oj.argv[i], "through")) d.through = f != 0.0f;
        else { g_out.Add("err unknown option '%s' (speed / force / hold / hold-until-off / through)\n", g_oj.argv[i]); return; }
    }
    if (!(d.speed > 0.0f && d.speed <= (hinge ? 120.0f : 600.0f))) { g_out.Add("err speed 0..%s\n", hinge ? "120 deg/s" : "600 units/s"); return; }
    if (!(d.force > 0.0f && d.force <= 1.0e6f)) { g_out.Add("err force 0..1e6\n"); return; }
    if (!(d.hold >= 0.0f && d.hold <= 30.0f)) { g_out.Add("err hold 0..30 s\n"); return; }
    d.limits = (flags & 2) && lim[0] < lim[1];
    d.lo = hinge ? lim[0] * tlobj::kRadToDeg : lim[0];
    d.hi = hinge ? lim[1] * tlobj::kRadToDeg : lim[1];
    char wrap[64] = "";                                        // 0.5.2: -180 at a stop near 180 (live 2026-11-16 21:52)
    if (hinge && d.limits) {
        const float u = tlobj::HingeUnwrap(v, d.lo, d.hi);
        if (u != v) _snprintf_s(wrap, sizeof(wrap), _TRUNCATE, "; value %.2f read as %.2f (180 / -180 wrap)",
                                static_cast<double>(v), static_cast<double>(u));
        v = u;
    }
    char clamp[160] = "";
    const float m = hinge ? 1.0f : 2.0f;                       // stay a little inside the limits
    if (d.limits && (target < d.lo + m || target > d.hi - m)) {
        const float want = target;
        target = target < d.lo + m ? d.lo + m : d.hi - m;
        _snprintf_s(clamp, sizeof(clamp), _TRUNCATE, "; target %.2f clamped into the limits -> %.2f", static_cast<double>(want),
                    static_cast<double>(target));
    }
    strncat_s(clamp, sizeof(clamp), wrap, _TRUNCATE);         // 0.5.2: the wrap note goes with the clamp note
    if (!d.limits && fabsf(target - v) > (hinge ? 180.0f : 3000.0f)) {
        g_out.Add("err joint %d has no limits (free): at most %s per drive\n", index, hinge ? "180 deg" : "3000 units");
        return;
    }
    if (g_driveOn) DriveStop("replaced by a new joint.drive");
    d.inst = inst; d.stamp = tlobj::D(inst + 0x44); d.x = x; d.joint = joint; d.jrec = jrec;
    d.intro = static_cast<LONG>(tlobj::D(inst + 0x58)); d.index = index; d.type = type; d.sign = 1;
    d.target = target; d.from = v; d.best = fabsf(target - v); d.lastV = v;
    d.saveVel = vel; d.saveForce = force; d.saveMotor = (flags & 0x10) != 0;
    d.start = d.lastBetter = GetTickCount();
    d.clock = *reinterpret_cast<volatile DWORD *>(kGameClock);
    d.links = tlobj::Links(x);
    for (int i = 0; i < d.links && i < 64; ++i) d.nodes[i] = LinkState(x, i);
    if (d.links > 64) d.links = 64;
    JEntry *e = JournalAdd(kJJoint, inst);
    e->old[0] = v;
    e->now[0] = target;
    char label[96];
    InstLabel(inst, label, sizeof(label));
    _snprintf_s(e->what, sizeof(e->what), _TRUNCATE, "%s joint %d drive %.2f -> %.2f", label, index, static_cast<double>(v),
                static_cast<double>(target));
    d.journal = g_jCount - 1;
    g_drv = d;
    InterlockedExchange(&g_driveOn, 1);
    Log(1, "joint.drive %s joint %d (%s): %.2f -> %.2f, limits [%.2f, %.2f] limit %s (kept), saved motor %s vel %.4f force "
        "%.6g (raw, per tick); speed %.1f%s force %.6g %s%s; journal #%d", label, index, tlobj::JointTypeName(type),
        static_cast<double>(v), static_cast<double>(target), static_cast<double>(d.lo), static_cast<double>(d.hi),
        (flags & 2) ? "on" : "off", d.saveMotor ? "on" : "off", static_cast<double>(vel), static_cast<double>(force),
        static_cast<double>(d.speed), hinge ? " deg/s" : " units/s", static_cast<double>(d.force),
        d.holdOff ? "hold-until-off" : "hold", clamp, d.journal);
    if (d.holdOff)
        g_out.Add("ok joint.drive %s joint %d (%s): %.2f -> %.2f, limits [%.2f, %.2f] kept%s - motor speed %.1f%s force %.6g; "
                  "HOLD UNTIL OFF: keeps the target until joint.hold off / joint.drive stop (also stops on unit change, "
                  "instance gone, leaving the limits, or 30 s without reaching it)\n", label, index, tlobj::JointTypeName(type),
                  static_cast<double>(v), static_cast<double>(target), static_cast<double>(d.lo), static_cast<double>(d.hi), clamp,
                  static_cast<double>(d.speed), hinge ? " deg/s" : " units/s", static_cast<double>(d.force));
    else
        g_out.Add("ok joint.drive %s joint %d (%s): %.2f -> %.2f, limits [%.2f, %.2f] kept%s - motor speed %.1f%s force %.6g; "
                  "stops on reach / away / overshoot / node change / 10 s (TruLink.log, joint.drive status | stop)\n", label,
                  index, tlobj::JointTypeName(type), static_cast<double>(v), static_cast<double>(target),
                  static_cast<double>(d.lo), static_cast<double>(d.hi), clamp, static_cast<double>(d.speed),
                  hinge ? " deg/s" : " units/s", static_cast<double>(d.force));
}

// ---- journal / undo ----
void OpJournal() {
    if (g_oj.argc >= 2 && !_stricmp(g_oj.argv[1], "clear")) {
        const int n = g_jCount;
        g_jCount = 0;
        g_out.Add("ok journal cleared (%d entries forgotten - nothing undone)\n", n);
        Log(1, "obj.journal clear: %d entries forgotten", n);
        return;
    }
    g_out.Add("ok+ obj.journal %d of %d entries (#n kind what old -> new state)\n", g_jCount, kJMax);
    const DWORD now = GetTickCount();
    for (int i = 0; i < g_jCount; ++i) {
        const JEntry &e = g_journal[i];
        char vals[128] = "";
        if (e.kind == kJPos || e.kind == kJRot || e.kind == kJPlace)
            _snprintf_s(vals, sizeof(vals), _TRUNCATE, "%.2f %.2f %.2f -> %.2f %.2f %.2f%s", static_cast<double>(e.old[0]),
                        static_cast<double>(e.old[1]), static_cast<double>(e.old[2]), static_cast<double>(e.now[0]),
                        static_cast<double>(e.now[1]), static_cast<double>(e.now[2]),
                        e.kind == kJRot ? " rad" : e.kind == kJPlace ? " (game placement path)" : "");
        else if (e.kind == kJHide || e.kind == kJSticky)
            _snprintf_s(vals, sizeof(vals), _TRUNCATE, "%lu -> %lu", e.oldWord, e.newWord);
        g_out.Add("#%d %s %s %s %s(%lu s ago)\n", i, kJNames[e.kind], e.what, vals, e.undone ? "UNDONE " : "", (now - e.tick) / 1000);
    }
    g_out.Add(".\n");
}
// undoes entry i; the answer line goes to g_out
void UndoOne(int i) {
    JEntry &e = g_journal[i];
    if (e.undone) return;
    switch (e.kind) {
    case kJPos:
    case kJRot: {
        if (!JAlive(e)) { g_out.Add("#%d %s: instance gone - skipped\n", i, e.what); break; }
        float cur[3];
        TlRead(e.inst + (e.kind == kJRot ? 0x30 : 0x20), cur, 12);
        if (!WriteFloats(e.inst + (e.kind == kJRot ? 0x30 : 0x20), e.old, 3)) { g_out.Add("#%d %s: write failed\n", i, e.what); break; }
        e.undone = true;
        g_out.Add("#%d %s: back to %.2f %.2f %.2f%s (was %.2f %.2f %.2f)\n", i, e.what, static_cast<double>(e.old[0]),
                  static_cast<double>(e.old[1]), static_cast<double>(e.old[2]), e.kind == kJRot ? " rad" : "",
                  static_cast<double>(cur[0]), static_cast<double>(cur[1]), static_cast<double>(cur[2]));
        Log(1, "obj.undo #%d %s: %.3f %.3f %.3f restored", i, e.what, static_cast<double>(e.old[0]),
            static_cast<double>(e.old[1]), static_cast<double>(e.old[2]));
        break;
    }
    case kJHide:
        if (!JAlive(e)) { g_out.Add("#%d %s: instance gone - skipped\n", i, e.what); break; }
        PostMsg(e.inst, 7, static_cast<int>(e.oldWord));
        e.undone = true;
        g_out.Add("#%d %s: INSTANCE_Post(7, %lu) - iflags now 0x%08lx\n", i, e.what, e.oldWord, tlobj::D(e.inst + 0x14));
        Log(1, "obj.undo #%d %s: INSTANCE_Post(0x%08lx, 7, %lu)", i, e.what, e.inst, e.oldWord);
        break;
    case kJSticky: {
        tlobj::StHit hits[3];
        char why[96];
        const int k = tlobj::StFind(e.stKind, e.stOwner, e.stKey, hits, why, sizeof(why));
        int pick = -1;
        for (int h = 0; h < k; ++h)
            if (hits[h].type == e.stType) pick = h;
        if (pick < 0 || !StWrite(hits[pick], e.oldWord)) { g_out.Add("#%d %s: store entry gone / write failed - skipped\n", i, e.what); break; }
        e.undone = true;
        g_out.Add("#%d %s: back to %lu\n", i, e.what, e.oldWord);
        Log(1, "obj.undo #%d %s: %lu restored (store write + notification)", i, e.what, e.oldWord);
        break;
    }
    case kJPlace: {                                         // 0.5: the same game path back to the old pose
        if (!JAlive(e)) { g_out.Add("#%d %s: instance gone - skipped\n", i, e.what); break; }
        if (!PlaceBody(e.inst, e.old, e.oldRot)) { g_out.Add("#%d %s: no body / access fault - skipped\n", i, e.what); break; }
        e.undone = true;
        float cur[3] = {0, 0, 0};
        TlRead(e.inst + 0x20, cur, 12);
        g_out.Add("#%d %s: placed back at %.2f %.2f %.2f rot z %.2f deg (now %.2f %.2f %.2f)\n", i, e.what,
                  static_cast<double>(e.old[0]), static_cast<double>(e.old[1]), static_cast<double>(e.old[2]),
                  tlobj::Deg(e.oldRot[2]), static_cast<double>(cur[0]), static_cast<double>(cur[1]), static_cast<double>(cur[2]));
        Log(1, "obj.undo #%d %s: placed back at %.3f %.3f %.3f", i, e.what, static_cast<double>(e.old[0]),
            static_cast<double>(e.old[1]), static_cast<double>(e.old[2]));
        break;
    }
    case kJUber:
        e.undone = true;
        g_out.Add("#%d %s: not undoable (the game's logic ran) - passed\n", i, e.what);
        break;
    case kJJoint:
        if (g_driveOn && g_drv.journal == i) DriveStop("obj.undo: drive stopped");
        e.undone = true;
        g_out.Add("#%d %s: drive %s; the joint stays where the physics left it (its motor settings were put back)\n", i, e.what,
                  "stopped");
        break;
    }
}
void OpUndo() {
    const bool all = g_oj.argc >= 2 && !_stricmp(g_oj.argv[1], "all");
    int last = -1;
    for (int i = g_jCount - 1; i >= 0; --i)
        if (!g_journal[i].undone) { last = i; break; }
    if (last < 0) { g_out.Add("ok nothing to undo (obj.journal)\n"); return; }
    g_out.Add("ok+ obj.undo%s\n", all ? " all" : "");
    for (int i = last; i >= 0; --i) {
        if (g_journal[i].undone) continue;
        UndoOne(i);
        if (!all) break;
    }
    g_out.Add(".\n");
}

// 0.5.1 mark.refs <id>: every instance obj.refs <id> finds gets the TruMenu note "<- <id> <member>" (flags 1: shown
// even with object names off); a referrer with several members gets one note naming the first
void OpMarkRefs() {
    NoteFn note = nullptr;
    NoteClearFn clear = nullptr;
    NoteListFn list = nullptr;
    if (!NoteExports(&note, &clear, &list)) { g_out.Add("err %s\n", kNeedsMenu); return; }
    const DWORD target = ObjInst(g_oj.argv[1]);
    if (!target) return;
    const DWORD intro = tlobj::D(target + 0x58);
    DWORD done[64];
    int nDone = 0, set = 0, full = 0, hits = 0;
    const int walked = tlobj::RefsEach(intro, [&](DWORD owner, int, int d, int k, const tlobj::Member &, DWORD) {
        ++hits;
        const DWORD oi = tlobj::D(owner + 0x58);
        for (int i = 0; i < nDone; ++i)
            if (done[i] == oi) return;
        if (nDone < 64) done[nDone++] = oi;
        char at[24], text[96];
        tlobj::MemberTag(d, k, at, sizeof(at));
        _snprintf_s(text, sizeof(text), _TRUNCATE, "<- %lu %s", intro, at);
        const int r = note(static_cast<unsigned>(oi), text, 1);
        if (r == 1) ++set; else ++full;
    });
    char label[96];
    InstLabel(target, label, sizeof(label));
    g_out.Add("ok mark.refs %s: %d reference(s) in %d instance(s), %d note(s) set%s (%d instances walked)\n", label, hits,
              nDone, set, full ? " - TruMenu's note table full for the rest" : "", walked);
    Log(1, "mark.refs %s: %d reference(s), %d note(s) set, %d refused", label, hits, set, full);
}
// 0.5.2 puzzle.list [de|en]: TruMenu 0.22.57's "Raetsel in der Naehe" rows (export TruMenuPuzzleList, game thread),
// one line per row: name TAB state TAB count TAB action ("-" = list only; else the TruMenu item + argument the row runs)
typedef int(__cdecl *PuzzleListFn)(char *out, int size, int lang);
void OpPuzzleList() {
    HMODULE menu = GetModuleHandleA("TruMenu.asi");
    const PuzzleListFn fn = menu ? reinterpret_cast<PuzzleListFn>(GetProcAddress(menu, "TruMenuPuzzleList")) : nullptr;
    if (!fn) { g_out.Add("err needs TruMenu 0.22.57 (export TruMenuPuzzleList)\n"); return; }
    const int lang = g_oj.argc >= 2 && !_stricmp(g_oj.argv[1], "de") ? 0 : 1;
    static char buf[32768];
    const int len = fn(buf, static_cast<int>(sizeof(buf)), lang);
    int rows = 0;
    for (const char *c = buf; len > 0 && *c; ++c) rows += *c == '\n' ? 1 : 0;
    g_out.Add("ok+ puzzle.list (%s): %d row(s) - name, state, count, action (tab separated; the action runs with "
              "menu <item> <argument>, e.g. menu puzzle.hold 4835 1)\n", lang ? "en" : "de", rows);
    if (len > 0) g_out.Add("%s", buf);
    if (len >= static_cast<int>(sizeof(buf))) g_out.Add("(list cut: %d bytes needed)\n", len);
    g_out.Add(".\n");
    Log(2, "puzzle.list: %d row(s), %d bytes", rows, len);
}
void ObjRun() {
    g_tlRegStart = g_tlRegEnd = 0;
    switch (g_oj.op) {
    case kOpNear: if (NeedGroups({tlobj::kGrpList, tlobj::kGrpUber, tlobj::kGrpMulti})) OpNear(); break;
    case kOpInfo: if (NeedGroups({tlobj::kGrpList, tlobj::kGrpUber, tlobj::kGrpMulti})) OpInfo(); break;
    case kOpSet: OpSet(); break;
    case kOpUndo: OpUndo(); break;
    case kOpJournal: OpJournal(); break;
    case kOpEvents: if (NeedGroups({tlobj::kGrpList, tlobj::kGrpUber, tlobj::kGrpMulti})) OpEvents(); break;
    case kOpSend: OpSend(); break;
    case kOpStGet: OpStGet(); break;
    case kOpStSet: OpStSet(); break;
    case kOpJGet: if (NeedGroups({tlobj::kGrpList, tlobj::kGrpMulti})) OpJointGet(); break;
    case kOpJDrive: OpJointDrive(); break;
    case kOpPlace: OpPlace(); break;
    case kOpRefs: if (NeedGroups({tlobj::kGrpList})) OpRefs(); break;
    case kOpMarkRefs: if (NeedGroups({tlobj::kGrpList})) OpMarkRefs(); break;   // 0.5.1
    case kOpPuzzleList: OpPuzzleList(); break;                                   // 0.5.2 (TruMenu checks its own rows)
    case kOpJHold:
        if (g_oj.argc >= 2 && !_stricmp(g_oj.argv[1], "off")) {
            if (!g_driveOn) { g_out.Add("ok joint.hold: nothing running\n"); break; }
            const bool held = g_drv.holdOff;
            DriveStop("joint.hold off");
            g_out.Add("ok joint.hold off: %s stopped, the joint's motor settings put back (TruLink.log)\n",
                      held ? "hold" : "drive");
        } else {
            g_out.Add("err usage: joint.hold off   (start a hold with joint.drive <id> <index> <target> hold-until-off)\n");
        }
        break;
    }
}

// server thread: tokens -> g_oj, one game-thread job
void CmdObj(int op, char **tok, int count, bool force) {
    memset(&g_oj, 0, sizeof(g_oj));
    g_oj.op = op;
    g_oj.force = force;
    for (int i = 0; i < count && i < 16; ++i) strncpy_s(g_oj.argv[i], sizeof(g_oj.argv[i]), tok[i], _TRUNCATE);
    g_oj.argc = count < 16 ? count : 16;
    if (g_grpBad < 0) { g_out.Add("err byte checks not run\n"); return; }
    if (!g_grp[tlobj::kGrpList]) { g_out.Add("err byte checks 'list' failed (status) - no object commands\n"); return; }
    const char *why = CallOnGameThread(kKindObj, 0, 0, 0);
    if (why) {
        g_out.Reset();
        g_out.Add("err %s\n", why);
        Log(0, "%s: %s", tok[0], why);
        return;
    }
    if (!g_out.n) g_out.Add("err no answer\n");
    Log(2, "%s done (%lu bytes, frame %lu)", tok[0], static_cast<DWORD>(g_out.n), g_job.frame);
}
void CmdMarkRefs(char **tok, int count, bool force) { CmdObj(kOpMarkRefs, tok, count, force); }   // 0.5.1

// one line in, answer in g_out; returns false to close the connection
bool HandleLine(char *line) {
    g_out.Reset();
    char *tok[24];
    int count = 0;
    char *context = nullptr;
    for (char *t = strtok_s(line, " \t", &context); t && count < 24; t = strtok_s(nullptr, " \t", &context))
        tok[count++] = t;
    if (!count) return true;                                   // empty line: no answer
    bool force = false;
    if (count > 1 && !_stricmp(tok[count - 1], "force")) { force = true; --count; }
    const char *cmd = tok[0];
    if (cmd[0] == '#') return true;                            // comment (script files)
    if (!_stricmp(cmd, "ping")) g_out.Add("pong TruLink %s\n", kVersion);
    else if (!_stricmp(cmd, "help")) CmdHelp();
    else if (!_stricmp(cmd, "status")) CmdStatus();
    else if (!_stricmp(cmd, "read")) CmdRead(tok, count, force);
    else if (!_stricmp(cmd, "read32")) CmdRead32(tok, count, force, false);
    else if (!_stricmp(cmd, "readf")) CmdRead32(tok, count, force, true);
    else if (!_stricmp(cmd, "write")) CmdWrite(tok, count, force);
    else if (!_stricmp(cmd, "write32")) CmdWrite32(tok, count, force, false);
    else if (!_stricmp(cmd, "writef")) CmdWrite32(tok, count, force, true);
    else if (!_stricmp(cmd, "player")) CmdPlayer();
    else if (!_stricmp(cmd, "camera")) CmdCamera(tok, count);
    else if (!_stricmp(cmd, "post")) CmdPost(tok, count);
    else if (!_stricmp(cmd, "objects")) CmdObjects();
    else if (!_stricmp(cmd, "modules")) CmdModules();
    else if (!_stricmp(cmd, "menu")) CmdMenu(tok, count);
    else if (!_stricmp(cmd, "obj.msg")) CmdObjMsg(tok, count);   // 0.5.3
    else if (!_stricmp(cmd, "scan")) CmdScan(tok, count);
    else if (!_stricmp(cmd, "watch")) CmdWatch(tok, count, force);
    else if (!_stricmp(cmd, "snapshot")) CmdSnapshot(tok, count, force);
    else if (!_stricmp(cmd, "diff")) CmdDiff(tok, count, force);
    else if (!_stricmp(cmd, "obj.near")) CmdObj(kOpNear, tok, count, force);          // 0.4
    else if (!_stricmp(cmd, "obj.info")) CmdObj(kOpInfo, tok, count, force);
    else if (!_stricmp(cmd, "obj.set")) CmdObj(kOpSet, tok, count, force);
    else if (!_stricmp(cmd, "obj.undo")) CmdObj(kOpUndo, tok, count, force);
    else if (!_stricmp(cmd, "obj.journal")) CmdObj(kOpJournal, tok, count, force);
    else if (!_stricmp(cmd, "uber.events")) CmdObj(kOpEvents, tok, count, force);
    else if (!_stricmp(cmd, "uber.send")) CmdObj(kOpSend, tok, count, force);
    else if (!_stricmp(cmd, "sticky.get")) CmdObj(kOpStGet, tok, count, force);
    else if (!_stricmp(cmd, "sticky.set")) CmdObj(kOpStSet, tok, count, force);
    else if (!_stricmp(cmd, "joint.get")) CmdObj(kOpJGet, tok, count, force);
    else if (!_stricmp(cmd, "joint.drive")) CmdObj(kOpJDrive, tok, count, force);
    else if (!_stricmp(cmd, "obj.place")) CmdObj(kOpPlace, tok, count, force);        // 0.5
    else if (!_stricmp(cmd, "obj.refs")) CmdObj(kOpRefs, tok, count, force);
    else if (!_stricmp(cmd, "joint.hold")) CmdObj(kOpJHold, tok, count, force);
    else if (!_stricmp(cmd, "puzzle.list")) CmdObj(kOpPuzzleList, tok, count, force);   // 0.5.2
    else if (!_stricmp(cmd, "mark.note") || !_stricmp(cmd, "mark.clear") || !_stricmp(cmd, "mark.list") ||
             !_stricmp(cmd, "mark.refs"))
        CmdMark(tok, count, force);                                                   // 0.5.1
    else if (!_stricmp(cmd, "log")) {
        DWORD level = 0;
        if (count < 2 || !ParseNumber(tok[1], &level) || level > 3) g_out.Add("err usage: log <0-3>\n");
        else { g_logLevel = static_cast<int>(level); g_out.Add("ok log level %d\n", g_logLevel); }
    } else if (!_stricmp(cmd, "quit") || !_stricmp(cmd, "exit") || !_stricmp(cmd, "bye")) {
        g_out.Add("ok bye\n");
        return false;
    } else {
        g_out.Add("err unknown command '%s' (help)\n", cmd);
    }
    return true;
}

// ---- server ----

bool SendAll(SOCKET s, const char *data, size_t length) {
    while (length) {
        int w = send(s, data, static_cast<int>(length > 0x10000 ? 0x10000 : length), 0);
        if (w <= 0) return false;
        data += w;
        length -= static_cast<size_t>(w);
    }
    return true;
}

DWORD WINAPI ServerThread(LPVOID) {
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) { Log(0, "WSAStartup failed - no server"); return 0; }
    SOCKET listener = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (listener == INVALID_SOCKET) { Log(0, "socket failed (%d) - no server", WSAGetLastError()); return 0; }
    BOOL exclusive = TRUE;                                     // no other process can bind the same port over us
    setsockopt(listener, SOL_SOCKET, SO_EXCLUSIVEADDRUSE, reinterpret_cast<const char *>(&exclusive), sizeof(exclusive));
    sockaddr_in address;
    memset(&address, 0, sizeof(address));
    address.sin_family = AF_INET;
    address.sin_port = htons(static_cast<u_short>(g_port));
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);          // 127.0.0.1 only - never INADDR_ANY
    if (bind(listener, reinterpret_cast<sockaddr *>(&address), sizeof(address)) == SOCKET_ERROR ||
        listen(listener, 1) == SOCKET_ERROR) {
        Log(0, "bind / listen on 127.0.0.1:%d failed (%d) - port in use? no server", g_port, WSAGetLastError());
        closesocket(listener);
        return 0;
    }
    u_long nonBlocking = 1;
    ioctlsocket(listener, FIONBIO, &nonBlocking);
    Log(1, "listening on 127.0.0.1:%d (one client at a time)", g_port);
    SOCKET client = INVALID_SOCKET;
    static char buf[8192];
    int used = 0;
    while (!g_stop) {
        fd_set readable;
        FD_ZERO(&readable);
        FD_SET(listener, &readable);
        if (client != INVALID_SOCKET) FD_SET(client, &readable);
        timeval tv = {0, static_cast<long>(g_watchIntervalMs < 250 ? g_watchIntervalMs : 250) * 1000};
        int n = select(0, &readable, nullptr, nullptr, &tv);
        PollWatches();                                         // 0.3: watches, every WatchIntervalMs
        if (n == SOCKET_ERROR) { Sleep(250); continue; }
        if (n == 0) continue;
        if (FD_ISSET(listener, &readable)) {
            sockaddr_in peer;
            int peerLength = sizeof(peer);
            SOCKET s = accept(listener, reinterpret_cast<sockaddr *>(&peer), &peerLength);
            if (s != INVALID_SOCKET) {
                u_long blocking = 0;
                ioctlsocket(s, FIONBIO, &blocking);
                DWORD sendTimeout = 5000;
                setsockopt(s, SOL_SOCKET, SO_SNDTIMEO, reinterpret_cast<const char *>(&sendTimeout), sizeof(sendTimeout));
                if ((ntohl(peer.sin_addr.s_addr) >> 24) != 127) {
                    closesocket(s);                            // cannot happen on a loopback socket - belt and braces
                } else if (client != INVALID_SOCKET) {
                    const char busy[] = "err busy: another client is connected\n";
                    SendAll(s, busy, sizeof(busy) - 1);
                    closesocket(s);
                    Log(2, "second client refused (busy)");
                } else {
                    client = s;
                    used = 0;
                    Log(1, "client connected (port %u)", ntohs(peer.sin_port));
                }
            }
        }
        if (client == INVALID_SOCKET || !FD_ISSET(client, &readable)) continue;
        int r = recv(client, buf + used, static_cast<int>(sizeof(buf)) - 1 - used, 0);
        if (r <= 0) {
            closesocket(client);
            client = INVALID_SOCKET;
            Log(1, "client disconnected");
            continue;
        }
        used += r;
        bool keep = true;
        for (;;) {
            char *newline = static_cast<char *>(memchr(buf, '\n', static_cast<size_t>(used)));
            if (!newline) break;
            *newline = 0;
            int consumed = static_cast<int>(newline - buf) + 1;
            if (newline > buf && newline[-1] == '\r') newline[-1] = 0;
            char line[sizeof(buf)];
            strcpy_s(line, sizeof(line), buf);
            memmove(buf, buf + consumed, static_cast<size_t>(used - consumed));
            used -= consumed;
            Log(2, "> %s", line);
            keep = HandleLine(line);
            if (g_out.n && !SendAll(client, g_out.buf, g_out.n)) keep = false;
            if (!keep) break;
        }
        if (keep && used >= static_cast<int>(sizeof(buf)) - 1) {
            const char tooLong[] = "err line too long\n";
            SendAll(client, tooLong, sizeof(tooLong) - 1);
            used = 0;
        }
        if (!keep) {
            closesocket(client);
            client = INVALID_SOCKET;
            Log(1, "client closed");
        }
    }
    if (client != INVALID_SOCKET) closesocket(client);
    closesocket(listener);
    return 0;
}

void ReadOptions(const char *dir) {
    char ini[MAX_PATH];
    _snprintf_s(ini, sizeof(ini), _TRUNCATE, "%sTruLink.ini", dir);
    g_enabled = GetPrivateProfileIntA("TruLink", "Enabled", 1, ini);
    g_logLevel = GetPrivateProfileIntA("TruLink", "LogLevel", 1, ini);
    g_port = GetPrivateProfileIntA("TruLink", "Port", 9265, ini);
    g_allowForce = GetPrivateProfileIntA("TruLink", "AllowForce", 1, ini);
    g_timeoutMs = GetPrivateProfileIntA("TruLink", "GameThreadTimeoutMs", 5000, ini);
    if (g_timeoutMs < 500) g_timeoutMs = 500;
    int maxCandidates = GetPrivateProfileIntA("TruLink", "ScanMaxCandidates", 4 * 1024 * 1024, ini);
    if (maxCandidates < 1024) maxCandidates = 1024;
    if (maxCandidates > 16 * 1024 * 1024) maxCandidates = 16 * 1024 * 1024;   // 128 MB at most (32-bit game)
    g_scanMaxCandidates = static_cast<DWORD>(maxCandidates);
    g_scanMaxSeconds = GetPrivateProfileIntA("TruLink", "ScanMaxSeconds", 60, ini);
    if (g_scanMaxSeconds < 1) g_scanMaxSeconds = 1;
    g_watchIntervalMs = GetPrivateProfileIntA("TruLink", "WatchIntervalMs", 100, ini);
    if (g_watchIntervalMs < 20) g_watchIntervalMs = 20;
}

void Start(HMODULE self) {
    char dir[MAX_PATH];
    DWORD len = GetModuleFileNameA(self, dir, MAX_PATH);
    while (len > 0 && dir[len - 1] != '\\' && dir[len - 1] != '/') --len;
    dir[len] = 0;
    _snprintf_s(g_logPath, sizeof(g_logPath), _TRUNCATE, "%sTruLink.log", dir);
    ReadOptions(dir);
    Log(1, "TruLink %s loaded (enabled %d, port %d, log level %d, force %d)", kVersion, g_enabled, g_port, g_logLevel,
        g_allowForce);
    if (!g_enabled) { Log(1, "disabled by TruLink.ini - no server, no hook"); return; }
    if (g_port <= 0 || g_port > 65535 || g_port == 9264) {
        Log(0, "port %d not usable (9264 is FMOD's profiler port) - no server", g_port);
        return;
    }
    HMODULE exe = GetModuleHandleA(nullptr);
    DWORD base = static_cast<DWORD>(reinterpret_cast<DWORD_PTR>(exe));
    if (base != kImageBase) { Log(0, "image base 0x%08lx, expected 0x%08lx - not started", base, kImageBase); return; }
    const IMAGE_DOS_HEADER *dos = reinterpret_cast<const IMAGE_DOS_HEADER *>(base);
    const IMAGE_NT_HEADERS *nt = reinterpret_cast<const IMAGE_NT_HEADERS *>(base + dos->e_lfanew);
    g_imageStart = base;
    g_imageEnd = base + nt->OptionalHeader.SizeOfImage;
    bool callOk = BytesAt(kCallSite, kCallBytes, sizeof(kCallBytes));
    g_cameraOk = BytesAt(kCameraSetMode, kCameraSetModeBytes, sizeof(kCameraSetModeBytes));
    g_restoreOk = BytesAt(kCameraRestore, kCameraRestoreBytes, sizeof(kCameraRestoreBytes));
    g_postOk = BytesAt(kInstancePost, kInstancePostBytes, sizeof(kInstancePostBytes));
    g_tableOk = BytesAt(kFindObject, kFindObjectBytes, sizeof(kFindObjectBytes)) &&
                BytesAt(kFindObjectLoop, kFindObjectLoopBytes, sizeof(kFindObjectLoopBytes));
    Log(1, "code checks: pad call %d, CAMERA_SetMode %d, camera restore %d, INSTANCE_Post %d, object table %d", callOk,
        g_cameraOk, g_restoreOk, g_postOk, g_tableOk);
    g_grpBad = tlobj::RunChecks(g_grp, &g_grpFirstBad, g_grpRows);   // 0.4: object commands (TruLinkObj.h rows)
    char groups[256] = "";
    for (int g = 0; g < tlobj::kGrpCount; ++g) {
        char one[40];
        _snprintf_s(one, sizeof(one), _TRUNCATE, "%s%s %d/%d", g ? ", " : "", tlobj::kGrpNames[g], g_grp[g] ? g_grpRows[g] : 0,
                    g_grpRows[g]);
        strncat_s(groups, sizeof(groups), one, _TRUNCATE);
    }
    Log(g_grpBad ? 0 : 1, "0.5 object checks: %d of %d rows bad%s (first 0x%08lx) - %s", g_grpBad, tlobj::kTlCheckCount,
        g_grpBad ? ", the affected commands answer err" : "", g_grpFirstBad, groups);
    g_jobDone = CreateEventA(nullptr, FALSE, FALSE, nullptr);
    g_tls = TlsAlloc();
    if (callOk && g_jobDone && g_tls != TLS_OUT_OF_INDEXES) {
        HANDLE hook = CreateThread(nullptr, 0, HookThread, nullptr, 0, nullptr);
        if (hook) CloseHandle(hook);
        else Log(0, "CreateThread (hook) failed (%lu)", GetLastError());
    } else {
        Log(0, "pad poll call at 0x%08lx does not match (or no event / TLS) - no game-thread commands", kCallSite);
    }
    HANDLE server = CreateThread(nullptr, 0, ServerThread, nullptr, 0, nullptr);
    if (server) CloseHandle(server);
    else Log(0, "CreateThread (server) failed (%lu)", GetLastError());
}

}  // namespace

BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(instance);
        InitializeCriticalSection(&g_logLock);
        Start(instance);
    } else if (reason == DLL_PROCESS_DETACH) {
        g_stop = 1;
    }
    return TRUE;
}

// exported so TruLink's own "modules" command and other tools can identify the plugin
extern "C" __declspec(dllexport) const char *TruLinkVersion() {
    return "TruLink 0.5 (127.0.0.1 text channel: read / write / camera / post / objects / modules / menu / scan / watch / snapshot; 0.3.1: dated log lines; 0.4: obj / uber / sticky / joint with journal + undo; 0.5: obj.place / obj.refs / base classes / object checks / hold-until-off)";
}
