// TruFlashShadow.asi 0.5 - Lara's flashlight casts real-time shadows on PC (tested on the GOG tru.exe).
//
// The PC flashlight already creates the Xbox's shadow-casting spot light (g_personal_light DTP 3404, record 3407);
// four run-time gates in the PC renderer stop its shadow. This plugin opens them in memory, for the flashlight only:
//   1. cast bit PCRenderLight +0xc5 bit 2, set again before the shadow pass (call RenderShadowMaps at 0x509756);
//   2. the flashlight added to the shadow-light list of SetLights (call 0x505530 at 0x5076c2);
//   3. static batches without the cast flag registered for the flashlight only (je at 0x50fc32 / 0x50fd10 / 0x50fe2f,
//      stub at 0x504ee0);
//   4. terrain: the flashlight's bit set in every PCRenderTerrain part caster mask (vtable slot 0x8499c8 -> 0x5128b0).
// Every address and byte is checked first; on any mismatch that part is not patched. Options: TruFlashShadow.ini.
// Removing the .asi undoes everything (in-memory patches only). Full write-up: ../REPORT.md.

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>

namespace {

const DWORD kCallSite = 0x00509756;                 // call 0x5050c0 (RenderShadowMaps) in the frame function
const BYTE kCallBytes[] = {0xe8, 0x65, 0xb9, 0xff, 0xff};
const DWORD kRenderShadowMaps = 0x005050c0;
const DWORD kLightVt = 0x00849594;                  // PCRenderLight vtable
const DWORD kResVt = 0x008494ec;                    // PCLightResource vtable
// first 0x40 bytes of the flashlight light record (PC g_personal_light DTP 3407) = res+0x42c
const BYTE kFlashRecord[0x40] = {
    0x01, 0x00, 0x00, 0x00, 0x00, 0x40, 0x9c, 0x45, 0x00, 0x00, 0x00, 0x40, 0x2e, 0xe7, 0x82, 0x3f,
    0x2a, 0x74, 0xe6, 0x3f, 0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0x00, 0x00, 0x00, 0x80, 0x3f,
    0x39, 0xe1, 0x7f, 0x3f, 0xed, 0xc5, 0x7f, 0x3f, 0x06, 0xae, 0x7f, 0x3f, 0x70, 0x99, 0x7f, 0x3f,
    0x14, 0x88, 0x7f, 0x3f, 0xdc, 0x79, 0x7f, 0x3f, 0xb2, 0x6e, 0x7f, 0x3f, 0x82, 0x66, 0x7f, 0x3f};

// 0.2: the game passes the renderer two light lists per draw set: all lights and the shadow-casting lights
// (device SetLights 0x5076a0 -> scene 0x505530(list, count, shadowList, shadowCount, x) at 0x5076c2). The flashlight
// is never in the shadow list, so 0x504ee0 never registers it for the shadow pass (+0x65 stays 0, T29).
const DWORD kSetLightsCall = 0x005076c2;            // call 0x505530
const BYTE kSetLightsBytes[] = {0xe8, 0x69, 0xde, 0xff, 0xff};
const DWORD kSceneSetLights = 0x00505530;
DWORD g_shadowCopy[256];

// 0.3 diagnostics: static level geometry registers as caster through 0x504ee0(batch, x) for every light in the
// current shadow list (scene +0x1240 count / +0x1248 array); entry `mov eax,[ecx+1240h]` (6 bytes) is redirected.
const DWORD kStaticReg = 0x00504ee0;
const BYTE kStaticRegBytes[] = {0x8b, 0x81, 0x40, 0x12, 0x00, 0x00};
const DWORD kStaticRegCont = 0x00504ee6;
volatile LONG g_statCalls = 0, g_statWithFlash = 0, g_setCalls = 0, g_setWithFlash = 0, g_setForced = 0;
volatile DWORD g_flashLight = 0;          // last flashlight light seen (shadow-pass frame list)

// 0.4: static batches are registered as casters in 0x50f7c0 only when their flags have bit 2 (je at the three
// sites below). With StaticAllCast the three je are removed and the 0x504ee0 stub decides per call: flagged
// batches -> stock registration (all shadow lights); unflagged -> registered for the flashlight only.
const DWORD kJeA = 0x0050fc32, kJeB = 0x0050fd10, kJeC = 0x0050fe2f;   // 74 12 / 74 2d / 74 1a
const BYTE kJeABytes[] = {0x74, 0x12}, kJeBBytes[] = {0x74, 0x2d}, kJeCBytes[] = {0x74, 0x1a};
const DWORD kRetA = 0x0050fc46, kRetB = 0x0050fd35, kRetC = 0x0050fe43;   // return addresses of the 3 calls
const DWORD kLightInstance = 0x0050dbe0, kRegisterCaster = 0x0050b230;
volatile LONG g_statFlashOnly = 0;
// 0.5: level terrain (PCRenderTerrain, vtable slot 0x8499c8 = draw 0x5128b0(lights, count, matrix, partRecords, x)).
// Each part record (0x28 bytes) holds a 128-bit shadow-caster light mask at +0x18 (lights 0-63: +0x18 lo / +0x1c hi)
// and +0x20 / +0x24 (lights 64-127), indexing the light array passed in. The flashlight is set in every part's mask
// (and appended to the array when missing), so terrain casts into the flashlight's shadow map.
const DWORD kTerrainSlot = 0x008499c8, kTerrainDraw = 0x005128b0;
DWORD g_terrainLights[129];
volatile LONG g_terrainCalls = 0, g_terrainParts = 0, g_terrainAppended = 0;
int g_terrainCast = 1;

int g_enabled = 1, g_forceVisible = 0, g_addToShadowList = 1, g_addToAll = 1, g_staticAll = 1, g_diag = 1, g_logLevel = 1;
volatile LONG g_added = 0;
char g_logPath[MAX_PATH];
volatile LONG g_frames = 0, g_touched = 0, g_lastLogged = -1;

void Log(int level, const char *fmt, ...) {
    if (level > g_logLevel || !g_logPath[0]) return;
    char line[512];
    SYSTEMTIME t;
    GetLocalTime(&t);
    int n = _snprintf_s(line, sizeof(line), _TRUNCATE, "%04d-%02d-%02d %02d:%02d:%02d.%03d ", t.wYear, t.wMonth, t.wDay,
                        t.wHour, t.wMinute, t.wSecond, t.wMilliseconds);
    va_list ap;
    va_start(ap, fmt);
    if (n > 0) _vsnprintf_s(line + n, sizeof(line) - n, _TRUNCATE, fmt, ap);
    va_end(ap);
    FILE *f = nullptr;
    if (fopen_s(&f, g_logPath, "a") == 0 && f) {
        fputs(line, f);
        fputs("\n", f);
        fclose(f);
    }
}

bool Readable(DWORD a, size_t n) {
    __try {
        volatile BYTE x = 0;
        for (size_t i = 0; i < n; i += 64) x ^= *reinterpret_cast<volatile BYTE *>(a + i);
        x ^= *reinterpret_cast<volatile BYTE *>(a + n - 1);
        (void)x;
        return true;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

// called on the game's render thread right before RenderShadowMaps
void __stdcall BeforeShadowPass(DWORD scene) {
    LONG frame = InterlockedIncrement(&g_frames);
    if (g_diag && frame % 120 == 0) {
        Log(1, "diag frames %ld: SetLights %ld (flashlight in light list %ld, forced %ld), static caster batches %ld (flashlight in shadow list %ld), unflagged batches for the flashlight %ld; terrain draws with the flashlight %ld (parts %ld, appended %ld)",
            frame, InterlockedExchange(&g_setCalls, 0), InterlockedExchange(&g_setWithFlash, 0), InterlockedExchange(&g_setForced, 0),
            InterlockedExchange(&g_statCalls, 0), InterlockedExchange(&g_statWithFlash, 0), InterlockedExchange(&g_statFlashOnly, 0), InterlockedExchange(&g_terrainCalls, 0), InterlockedExchange(&g_terrainParts, 0), InterlockedExchange(&g_terrainAppended, 0));
    }
    if (!g_enabled || !scene) return;
    __try {
        DWORD count = *reinterpret_cast<DWORD *>(scene + 0x1020);
        if (count > 1024) return;
        int touched = 0;
        for (DWORD i = 0; i < count; ++i) {
            DWORD e = *reinterpret_cast<DWORD *>(scene + 0x20 + 4 * i);
            if (!e) continue;
            DWORD light = *reinterpret_cast<DWORD *>(e);
            if (!light || *reinterpret_cast<DWORD *>(light) != kLightVt) continue;
            DWORD res = *reinterpret_cast<DWORD *>(light + 0x1c);
            if (!res || *reinterpret_cast<DWORD *>(res) != kResVt) continue;
            if (memcmp(reinterpret_cast<const void *>(res + 0x42c), kFlashRecord, sizeof(kFlashRecord)) != 0) continue;
            g_flashLight = light;
            BYTE *c5 = reinterpret_cast<BYTE *>(light + 0xc5);
            BYTE before = *c5, vis = *reinterpret_cast<BYTE *>(e + 0x65);
            *c5 = static_cast<BYTE>(before | 4);
            if (g_forceVisible) *reinterpret_cast<BYTE *>(e + 0x65) = 1;
            ++touched;
            if (g_logLevel >= 2 || (g_logLevel >= 1 && InterlockedExchange(&g_lastLogged, static_cast<LONG>(light)) != static_cast<LONG>(light)))
                Log(1, "frame %ld: flashlight light 0x%08lx (instance 0x%08lx): +0xc5 0x%02x -> 0x%02x, +0x65 %u -> %u",
                    frame, light, e, before, *c5, vis, *reinterpret_cast<BYTE *>(e + 0x65));
        }
        if (touched) InterlockedExchangeAdd(&g_touched, touched);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        Log(0, "exception while walking the light list (scene 0x%08lx) - frame %ld", scene, frame);
    }
}

bool IsFlashlight(DWORD light) {
    if (!light || *reinterpret_cast<DWORD *>(light) != kLightVt) return false;
    DWORD res = *reinterpret_cast<DWORD *>(light + 0x1c);
    if (!res || *reinterpret_cast<DWORD *>(res) != kResVt) return false;
    return memcmp(reinterpret_cast<const void *>(res + 0x42c), kFlashRecord, sizeof(kFlashRecord)) == 0;
}

bool LightAlive(DWORD scene, DWORD L) {
    DWORD n = *reinterpret_cast<DWORD *>(scene + 0x14);
    DWORD *arr = *reinterpret_cast<DWORD **>(scene + 0x1c);
    if (!arr || n > 1024) return false;
    for (DWORD k = 0; k < n; ++k) if (arr[k] == L) return true;
    return false;
}

// args points at the 5 stack arguments of 0x505530; may replace args[2] / args[3] (shadow list / count)
void __stdcall BeforeSetLights(DWORD *args, DWORD scene) {
    if (!g_enabled || !g_addToShadowList) return;
    __try {
        DWORD *list = reinterpret_cast<DWORD *>(args[0]); DWORD n = args[1];
        DWORD *sh = reinterpret_cast<DWORD *>(args[2]); DWORD sn = args[3];
        if (!list || n > 64 || sn > 64) return;
        InterlockedIncrement(&g_setCalls);
        DWORD found = 0;
        for (DWORD i = 0; i < n && !found; ++i) if (IsFlashlight(list[i])) found = list[i];
        if (found) InterlockedIncrement(&g_setWithFlash);
        if (!found && g_addToAll && g_flashLight && LightAlive(scene, g_flashLight) && IsFlashlight(g_flashLight)) {
            DWORD L = g_flashLight;
            for (DWORD k = 0; k < sn && sh; ++k) if (sh[k] == L) return;
            for (DWORD k = 0; k < sn; ++k) g_shadowCopy[k] = sh[k];
            g_shadowCopy[sn] = L;
            args[2] = reinterpret_cast<DWORD>(g_shadowCopy);
            args[3] = sn + 1;
            InterlockedIncrement(&g_setForced);
            return;
        }
        for (DWORD i = 0; i < n; ++i) {
            DWORD L = list[i];
            if (!IsFlashlight(L)) continue;
            bool there = false;
            for (DWORD k = 0; k < sn && sh; ++k) there |= sh[k] == L;
            if (there) return;
            *reinterpret_cast<BYTE *>(L + 0xc5) |= 4;      // the shadow pass also asks CastsShadow
            for (DWORD k = 0; k < sn; ++k) g_shadowCopy[k] = sh[k];
            g_shadowCopy[sn] = L;
            args[2] = reinterpret_cast<DWORD>(g_shadowCopy);
            args[3] = sn + 1;
            if (InterlockedIncrement(&g_added) == 1 || g_logLevel >= 2)
                Log(1, "SetLights: flashlight light 0x%08lx added to the shadow list (%lu -> %lu)", L, sn, sn + 1);
            return;
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        Log(0, "exception in BeforeSetLights");
    }
}

void RegisterFor(DWORD light, DWORD batch) {
    __asm {
        mov ecx, light
        call kLightInstance
        push batch
        mov ecx, eax
        call kRegisterCaster
    }
}

// f -> the stack at 0x504ee0's entry: f[0] return address, f[1] batch, f[2] x. Returns 1 = run the stock code.
DWORD __stdcall StaticDecide(DWORD scene, DWORD *f) {
    __try {
        InterlockedIncrement(&g_statCalls);
        DWORD n = *reinterpret_cast<DWORD *>(scene + 0x1240);
        DWORD *arr = *reinterpret_cast<DWORD **>(scene + 0x1248);
        for (DWORD k = 0; k < n && k < 64 && arr; ++k)
            if (IsFlashlight(arr[k])) { InterlockedIncrement(&g_statWithFlash); break; }
        DWORD ret = f[0], flags = 2;
        if (ret == kRetA || ret == kRetC) flags = f[9];
        else if (ret == kRetB) flags = f[7];
        if ((flags & 2) || !g_staticAll) return 1;
        DWORD L = g_flashLight;
        if (L && LightAlive(scene, L) && IsFlashlight(L) && (*reinterpret_cast<BYTE *>(L + 0xc5) & 4)) {
            RegisterFor(L, f[1]);
            InterlockedIncrement(&g_statFlashOnly);
        }
        return 0;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return 0;
    }
}

__declspec(naked) void StaticRegStub() {
    __asm {
        push ecx
        lea eax, [esp + 4]
        push eax
        push ecx
        call StaticDecide
        pop ecx
        test eax, eax
        jz handled
        mov eax, dword ptr [ecx + 0x1240]
        jmp kStaticRegCont
    handled:
        ret 8
    }
}

void __stdcall TerrainPrep(DWORD self, DWORD *args) {
    if (!g_terrainCast) return;
    __try {
        DWORD L = g_flashLight;
        DWORD dev = *reinterpret_cast<DWORD *>(0x00a1407c);
        if (!L || !dev || !LightAlive(dev + 0xfdfc, L) || !IsFlashlight(L) || !(*reinterpret_cast<BYTE *>(L + 0xc5) & 4)) return;
        DWORD *lights = reinterpret_cast<DWORD *>(args[0]);
        DWORD n = args[1];
        BYTE *recs = reinterpret_cast<BYTE *>(args[3]);
        if (!recs || n > 128) return;
        DWORD idx = 0xffffffff;
        for (DWORD k = 0; k < n && lights; ++k) if (lights[k] == L) { idx = k; break; }
        if (idx == 0xffffffff) {
            if (n >= 128) return;
            for (DWORD k = 0; k < n; ++k) g_terrainLights[k] = lights[k];
            g_terrainLights[n] = L;
            args[0] = reinterpret_cast<DWORD>(g_terrainLights);
            args[1] = n + 1;
            idx = n;
            InterlockedIncrement(&g_terrainAppended);
        }
        DWORD geo = *reinterpret_cast<DWORD *>(self + 0x20);
        DWORD parts = geo ? *reinterpret_cast<DWORD *>(geo + 0x24) : 0;
        if (parts > 100000) return;
        DWORD off = idx < 32 ? 0x18 : idx < 64 ? 0x1c : idx < 96 ? 0x20 : 0x24;
        DWORD bit = 1u << (idx & 31);
        for (DWORD k = 0; k < parts; ++k) *reinterpret_cast<DWORD *>(recs + k * 0x28 + off) |= bit;
        InterlockedIncrement(&g_terrainCalls);
        InterlockedExchangeAdd(&g_terrainParts, static_cast<LONG>(parts));
    } __except (EXCEPTION_EXECUTE_HANDLER) {
    }
}

// replaces the PCRenderTerrain vtable entry 0x8499c8 (thiscall, 5 stack args)
__declspec(naked) void TerrainStub() {
    __asm {
        push ecx
        lea eax, [esp + 8]
        push eax
        push ecx
        call TerrainPrep
        pop ecx
        jmp kTerrainDraw
    }
}

// replaces `call 0x505530` at 0x5076c2 (thiscall ecx = scene, 5 stack args)
__declspec(naked) void SetLightsStub() {
    __asm {
        push ecx
        push ecx
        lea eax, [esp + 12]
        push eax
        call BeforeSetLights
        pop ecx
        jmp kSceneSetLights
    }
}

// replaces `call 0x5050c0` at 0x509756: ecx = scene, [esp+4] = RenderShadowMaps' argument
__declspec(naked) void Stub() {
    __asm {
        push ecx
        push ecx
        call BeforeShadowPass
        pop ecx
        jmp kRenderShadowMaps
    }
}

void Install() {
    char ini[MAX_PATH];
    HMODULE self = nullptr;
    GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                       reinterpret_cast<LPCSTR>(&Install), &self);
    GetModuleFileNameA(self, ini, MAX_PATH);
    char *dot = strrchr(ini, '.');
    if (dot) strcpy_s(dot, ini + MAX_PATH - dot, ".ini");
    strcpy_s(g_logPath, ini);
    dot = strrchr(g_logPath, '.');
    if (dot) strcpy_s(dot, g_logPath + MAX_PATH - dot, ".log");
    g_enabled = GetPrivateProfileIntA("FlashShadow", "Enabled", 1, ini);
    g_forceVisible = GetPrivateProfileIntA("FlashShadow", "ForceVisible", 0, ini);
    g_addToShadowList = GetPrivateProfileIntA("FlashShadow", "AddToShadowList", 1, ini);
    g_addToAll = GetPrivateProfileIntA("FlashShadow", "AddToAllShadowLists", 1, ini);
    g_staticAll = GetPrivateProfileIntA("FlashShadow", "StaticAllCast", 1, ini);
    g_terrainCast = GetPrivateProfileIntA("FlashShadow", "TerrainCast", 1, ini);
    g_diag = GetPrivateProfileIntA("FlashShadow", "Diagnostics", 1, ini);
    g_logLevel = GetPrivateProfileIntA("FlashShadow", "LogLevel", 1, ini);
    Log(0, "TruFlashShadow 0.5 (D-2 test): Enabled %d ForceVisible %d AddToShadowList %d AddToAllShadowLists %d StaticAllCast %d TerrainCast %d Diagnostics %d LogLevel %d", g_enabled, g_forceVisible, g_addToShadowList, g_addToAll, g_staticAll, g_terrainCast, g_diag, g_logLevel);
    if (!g_enabled) { Log(0, "disabled in the ini - nothing patched"); return; }
    if (!Readable(kCallSite, sizeof(kCallBytes)) || memcmp(reinterpret_cast<void *>(kCallSite), kCallBytes, sizeof(kCallBytes)) != 0) {
        Log(0, "refused: bytes at 0x%08lx are not `call 0x5050c0` - nothing patched", kCallSite);
        return;
    }
    if (!Readable(kLightVt, 0x54) || *reinterpret_cast<DWORD *>(kLightVt + 0x4c) != 0x0050a3a0) {
        Log(0, "refused: PCRenderLight vtable 0x%08lx does not match - nothing patched", kLightVt);
        return;
    }
    if (!Readable(kSetLightsCall, 5) || memcmp(reinterpret_cast<void *>(kSetLightsCall), kSetLightsBytes, 5) != 0) {
        Log(0, "refused: bytes at 0x%08lx are not `call 0x505530` - nothing patched", kSetLightsCall);
        return;
    }
    DWORD old = 0;
    if (g_addToShadowList && VirtualProtect(reinterpret_cast<void *>(kSetLightsCall), 5, PAGE_EXECUTE_READWRITE, &old)) {
        *reinterpret_cast<LONG *>(kSetLightsCall + 1) = static_cast<LONG>(reinterpret_cast<DWORD>(&SetLightsStub) - (kSetLightsCall + 5));
        VirtualProtect(reinterpret_cast<void *>(kSetLightsCall), 5, old, &old);
        FlushInstructionCache(GetCurrentProcess(), reinterpret_cast<void *>(kSetLightsCall), 5);
        Log(0, "patched: 0x%08lx call -> SetLights stub (then 0x%08lx)", kSetLightsCall, kSceneSetLights);
    }
    if (g_terrainCast) {
        DWORD o3 = 0;
        if (Readable(kTerrainSlot, 4) && *reinterpret_cast<DWORD *>(kTerrainSlot) == kTerrainDraw &&
            VirtualProtect(reinterpret_cast<void *>(kTerrainSlot), 4, PAGE_READWRITE, &o3)) {
            *reinterpret_cast<DWORD *>(kTerrainSlot) = reinterpret_cast<DWORD>(&TerrainStub);
            VirtualProtect(reinterpret_cast<void *>(kTerrainSlot), 4, o3, &o3);
            Log(0, "patched: PCRenderTerrain vtable 0x%08lx -> terrain caster-mask stub (then 0x%08lx)", kTerrainSlot, kTerrainDraw);
        } else {
            g_terrainCast = 0;
            Log(0, "TerrainCast refused: vtable 0x%08lx does not hold 0x%08lx", kTerrainSlot, kTerrainDraw);
        }
    }
    if (g_staticAll) g_diag = 1;
    if (g_diag && Readable(kStaticReg, 6) && memcmp(reinterpret_cast<void *>(kStaticReg), kStaticRegBytes, 6) == 0 &&
        VirtualProtect(reinterpret_cast<void *>(kStaticReg), 6, PAGE_EXECUTE_READWRITE, &old)) {
        BYTE *p = reinterpret_cast<BYTE *>(kStaticReg);
        p[0] = 0xe9;
        *reinterpret_cast<LONG *>(p + 1) = static_cast<LONG>(reinterpret_cast<DWORD>(&StaticRegStub) - (kStaticReg + 5));
        p[5] = 0x90;
        VirtualProtect(reinterpret_cast<void *>(kStaticReg), 6, old, &old);
        FlushInstructionCache(GetCurrentProcess(), p, 6);
        Log(0, "patched: 0x%08lx -> static caster stub", kStaticReg);
        if (g_staticAll) {
            const DWORD je[3] = {kJeA, kJeB, kJeC};
            const BYTE *jb[3] = {kJeABytes, kJeBBytes, kJeCBytes};
            bool ok = true;
            for (int k = 0; k < 3; ++k) ok = ok && memcmp(reinterpret_cast<void *>(je[k]), jb[k], 2) == 0;
            if (ok) {
                for (int k = 0; k < 3; ++k) {
                    DWORD o2 = 0;
                    VirtualProtect(reinterpret_cast<void *>(je[k]), 2, PAGE_EXECUTE_READWRITE, &o2);
                    reinterpret_cast<BYTE *>(je[k])[0] = 0x90;
                    reinterpret_cast<BYTE *>(je[k])[1] = 0x90;
                    VirtualProtect(reinterpret_cast<void *>(je[k]), 2, o2, &o2);
                    FlushInstructionCache(GetCurrentProcess(), reinterpret_cast<void *>(je[k]), 2);
                }
                Log(0, "patched: cast-flag jumps 0x%08lx / 0x%08lx / 0x%08lx removed", kJeA, kJeB, kJeC);
            } else {
                g_staticAll = 0;
                Log(0, "StaticAllCast refused: cast-flag jump bytes differ");
            }
        }
    } else if (g_diag) {
        Log(0, "static caster diagnostics not installed (bytes at 0x%08lx differ)", kStaticReg);
    }
    if (!VirtualProtect(reinterpret_cast<void *>(kCallSite), 5, PAGE_EXECUTE_READWRITE, &old)) {
        Log(0, "refused: VirtualProtect failed (%lu)", GetLastError());
        return;
    }
    *reinterpret_cast<LONG *>(kCallSite + 1) = static_cast<LONG>(reinterpret_cast<DWORD>(&Stub) - (kCallSite + 5));
    VirtualProtect(reinterpret_cast<void *>(kCallSite), 5, old, &old);
    FlushInstructionCache(GetCurrentProcess(), reinterpret_cast<void *>(kCallSite), 5);
    Log(0, "patched: 0x%08lx call -> stub 0x%08lx (then 0x%08lx)", kCallSite, reinterpret_cast<DWORD>(&Stub), kRenderShadowMaps);
}

}  // namespace

BOOL APIENTRY DllMain(HMODULE, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) Install();
    return TRUE;
}
