// TruLinkObj.h - TruLink 0.4 object inspection: the pure-memory decoders of the obj.* / uber.* / sticky.* / joint.*
// commands, shared by TruLink.asi (live, on the game thread) and the offline test TruLinkObjTest.exe (full minidump).
//
// The includer provides three functions:
//   bool TlRead(DWORD address, void *out, DWORD length);   guarded read, false = not readable
//   void TlAdd(const char *fmt, ...);                      appends to the answer
//   bool TlJointValue(DWORD joint, int type, float *v);     the engine's joint getter (game thread; false offline)
// Nothing here writes game memory or calls game code; every layout is a byte check row below (kTlChecks) or a fact of
// docs/ENGINE.md (sections 5, 6.3, 7.1, 9) re-checked on the dump of 2026-11-15 20:07 (l3_chapel).
#pragma once
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

bool TlRead(DWORD address, void *out, DWORD length);
void TlAdd(const char *fmt, ...);
bool TlJointValue(DWORD joint, int type, float *value);

namespace tlobj {

// ---- addresses (tru.exe PC 1.1, image base 0x400000) ----
const DWORD kInstanceList = 0x00d98d54;   // first instance, next = +8 (writer 0x5b2ec6, walk 0x5d467d)
const DWORD kPlayer = 0x00e7f094;         // GameTracker +0xc
const DWORD kObjNames = 0x00db94d0;       // [ ]: +0 count, name of object id n at +n*8 (lookup 0x5bf770)
const DWORD kUnits = 0x00dbab40;          // stream unit table, 32 x 0xd8: +0 id, +4 state (2 loaded), +0xc name
const DWORD kUnitSize = 0xd8;
const int kUnitCount = 32;
const DWORD kUberMagic = 0xf0012345;      // uber state b = u - 0x10, [b+0x70]
const DWORD kMultiMagic = 0xfea51b1e;     // multibody X = u - 4, [X+0x54]
const DWORD kMultiVt = 0x00847f70, kMultiVtSub = 0x0085d55c;   // X vtables (ctor 0x4d7d5a, subclass 0x6d5fb7)
const DWORD kCmdExec = 0x004d77a0;        // X vf+4: run entry n of the object command table (thiscall X, n)
const DWORD kUberMsg = 0x004d7680;        // uber message (thiscall b, record {?, kind +4, value +8}), ret 4
const DWORD kScriptTypeVt = 0x0084e4d4;   // runtime ScriptType (ctor 0x5784e0: +8 = the stream root)
const DWORD kStImpl = 0x00a13f18;         // StickyManager impl: int [+0], bool [+4], float [+8]
const DWORD kStNotify[3] = {0x004af740, 0x004af6d0, 0x004af7b0};   // change notification int, bool, float
const DWORD kJtHinge = 0x004e1ef0, kJtSlider = 0x004e1ea0;          // joint value getters (thiscall J, st0)
const DWORD kJtLimitOn = 0x004d9f50, kJtMotorOn = 0x004da0c0, kJtMotorVel = 0x004da160, kJtMotorForce = 0x004da190,
            kJtWake = 0x004d8fd0;
const float kUnitsPerMetre = 290.0f;      // ENGINE 4.3: ~290 units per metre (280..310, not proven exactly)
const float kRadToDeg = 57.29577951308232f;

// ---- byte checks: every layout / function the commands rely on ----
enum { kGrpList, kGrpUber, kGrpMulti, kGrpCmd, kGrpMsg, kGrpJoint, kGrpDrive, kGrpSticky, kGrpScript, kGrpHide,
       kGrpCount };
const char *const kGrpNames[kGrpCount] = {"list", "uber", "multibody", "command", "message", "joint", "drive",
                                          "sticky", "script", "hide"};
struct Check { DWORD at; const char *hex; int group; };
const Check kTlChecks[] = {
    // instance list, object names, units, handles (TruMenu g_instOk / kLfChecks / kRkChecks rows)
    {0x005b2ec6, "890d548dd900", kGrpList},                                           // [0xd98d54] = first instance
    {0x005d467d, "8b35548dd900 85f6 7410 56 e8e377feff 8b7608", kGrpList},            // walk: next = +8
    {0x005bf770, "8b0dd094db00 56 33f6 3931 57 7e27 8b7c240c 8b44f108", kGrpList},    // names: +0 count, id*8
    {0x005ba880, "8b442428 894e38 8b550c 894658", kGrpList},                          // +0x58 unique (intro) id
    {0x005ba915, "8b44242c 898ed8000000 8b550c 8b4c2430 8996dc000000 8b5620 8996f0000000 8b562c 898600010000 "
                 "8b4624 898e04010000", kGrpList},                                    // +0x100 intro, +0x104 intro data
    {0x005bd37b, "8996e4000000 897e54", kGrpList},                                    // +0x54 parent (BirthObject)
    {0x005b3a56, "899fe0000000", kGrpList},                                           // +0xe0 stream unit id
    {0x005c1b50, "56 8b742408 33c0 33d2 b940abdb00 8bff 80790402 7504 3931 7413 81c1d8000000", kGrpList},   // units
    {0x005b39d0, "8b4c2404 85c9 740e 8b01 85c0 7408 8b5044 3b5104 7402 33c0 c3", kGrpList},   // handle {inst, stamp}
    // uber read path (TruMenu 0.21.7 kUbChecks)
    {0x004d5d59, "8b87d0020000 85c0 0f84ab000000 8b00 8b80ec020000 85c0 0f849b000000 8d48f0 85c9 0f8490000000 "
                 "817970452301f0", kGrpUber},
    {0x004d4b60, "53 55 57 8bf9 8b8784000000 8b5778 8d0cc500000000 2bc8 8b4208 8d1c88 33ed 396b0c 7657 56 8b4b10 8b34a9",
     kGrpUber},
    {0x004d31e0, "56 8b742408 8b5618 83c2ff 32c0 83fa0b 0f8780000000 0fb69294324d00 ff24957c324d00 d98188000000 d9461c",
     kGrpUber},
    {0x004d327c, "04324d00", kGrpUber},
    {0x004d3294, "00", kGrpUber},
    {0x004d7607, "8b8e80000000 85c9 7434 8b868c000000 a801", kGrpUber},
    {0x004d762d, "83be8c00000000 7526 8b4904", kGrpUber},
    {0x004d764c, "d98688000000 d8442408 d99e88000000", kGrpUber},
    // multibody object X (Q106 + 2026-11-15)
    {0x004d7d5a, "c706707f8400 c7467400000000 8b5f50", kGrpMulti},                     // vtable, joint list +0x74
    {0x004d7d6f, "8d6e04", kGrpMulti}, {0x004d7d7e, "89a8ec020000", kGrpMulti},        // [..+0x2ec] = X + 4
    {0x004d7d9c, "c746541e1ba5fe", kGrpMulti}, {0x004d7dbc, "897e58", kGrpMulti},       // magic +0x54, instance +0x58
    {0x006d5fb7, "c7065cd58500", kGrpMulti},                                          // subclass vtable
    {0x004d14a0, "8b81ec020000 85c0 740e 83c0fc 7409 8178541e1ba5fe", kGrpMulti},      // X of an instance
    {0x004d12d0, "8b442404 85c0 7c17 3b4170 7d12 8b496c 8d14c1 52 e8e7260e00", kGrpMulti},   // links +0x6c / +0x70
    {0x004d7a22, "894e7c", kGrpMulti},                                                // uber b+0x7c = X
    // object command table: X vf+4 = 0x4d77a0, what uber action 11 calls (0x4d886d)
    {0x004d77a0, "53 55 8be9 8b4558 8b4850 8b44240c 33db 3bc3 0f8c89000000 3b4110 0f8380000000 8d1440 8b4114 "
                 "395c9004 57 8d3c90", kGrpCmd},                                      // data +0x10 count, +0x14 12 B
    {0x004d77d6, "8b7708 8b041e 8b4d70 03f3 3bc1", kGrpCmd},                           // records +8: link index
    {0x004d7826, "56 e854feffff 8b442414 83c001 83c30c 3b4704", kGrpCmd},              // -> 0x4d7680, 12 B records
    {0x00847f74, "a0774d00", kGrpCmd}, {0x0085d560, "a0774d00", kGrpCmd},              // vf+4 of both vtables
    {0x004d886d, "8bce e80ca7ffff 8b4f04 8b10 8b5204 51 8bc8 ffd2", kGrpCmd},          // action 11: X->vf+4(n)
    // uber message kinds 2 / 3 / 4 (event / broadcast / command) and their drop tests
    {0x004d7680, "56 57 8b7c240c 8b4704 83c0ff 83f803 8bf1 0f87a9000000 ff248548774d00", kGrpMsg},
    {0x004d7748, "9e764d00 b5764d00 e5764d00 15774d00", kGrpMsg},
    {0x004d76d5, "8b4708 50 8bce e800d5ffff", kGrpMsg},                                // kind 2 -> 0x4d4be0
    {0x004d7705, "8b4708 50 8bce e820e4ffff", kGrpMsg},                                // kind 3 -> 0x4d5b30
    {0x004d7735, "8b4708 50 8bce e870e4ffff 5f 5e c20400", kGrpMsg},                   // kind 4 -> 0x4d5bb0
    {0x004d4be0, "55 8be9 83bd8000000000 756a f6859000000009 7561", kGrpMsg},
    {0x004d4c2a, "395318 750d", kGrpMsg},                                             // cond == value
    {0x004d5b30, "55 8be9 83bd8000000000 7570 f6859000000009 7567", kGrpMsg},
    {0x004d5b76, "837e180d 7516 8b542414 39561c", kGrpMsg},                           // cond 13, arg == value
    {0x004d5bb0, "55 8be9 83bd8000000000 7570 f6859000000009 7567", kGrpMsg},
    {0x004d5bf6, "837e1810 7516 8b542414 39561c", kGrpMsg},                           // cond 16, arg == command
    // joints (TruMenu 0.22.31 kJtChecks, read part)
    {0x004d7d60, "c7467400000000", kGrpJoint},
    {0x004d5c30, "8b542404 8b4a74", kGrpJoint},
    {0x004d710a, "8b401c", kGrpJoint},
    {0x004d11e0, "8b442404 0fb608 83f907 7719 ff248d38124d00 d94004", kGrpJoint},
    {0x004d9b10, "0fb68178010000 c3", kGrpJoint},
    {0x0048f2db, "e8102c0500 dc0da8528400", kGrpJoint},
    {0x0048f2c5, "8bcf e8d42b0500", kGrpJoint},
    {0x008452a8, "25cf030ddca54c40", kGrpJoint},
    {0x004e1ea0, "e9bb85ffff", kGrpJoint}, {0x004e1ef0, "e93b8affff", kGrpJoint},
    {0x004da930, "558bec 83e4f0 83ec5c 56 8bf1 8b865c010000", kGrpJoint},
    {0x004da460, "558bec 83e4f0 83ec4c a1e8d78b00", kGrpJoint},
    {0x004d9fc0, "8b442404 d9442408 c1e004 03c1 d998d8000000 d944240c d998dc000000 c20c00", kGrpJoint},
    {0x004d9f50, "8bd1 8b4c2404 8a8278010000 e84ff8ffff 84c0 741f b802000000 d3e0 807c240800 7409 098274010000 c20800 "
                 "f7d0 218274010000 c20800", kGrpJoint},
    // joint.drive: motor velocity / force / enable, body wake
    {0x004da0c0, "53 8bd1 8a9a78010000 56 8b74240c 8bce 8ac3 e839f7ffff 84c0 744b 8bb274010000 b810000000 d3e0 "
                 "807c241000 741d", kGrpDrive},
    {0x004da10c, "85f0 7416 80fb06 7407 808279010000ff f7d0 23c6 898274010000", kGrpDrive},
    {0x004da160, "d9442408 8b442404 d99cc108010000 c20800", kGrpDrive},              // velocity J+0x108+8a
    {0x004da190, "d9442408 8b442404 d99cc10c010000 c20800", kGrpDrive},              // force J+0x10c+8a
    {0x004d8fd0, "d98108010000 83a15c010000fe d99960010000 c3", kGrpDrive},
    // sticky store (TruMenu 0.21.1 kStChecks)
    {0x004b1458, "a3183fa100", kGrpSticky},
    {0x004ad560, "a1183fa100 8b00 8b481c 8b5018", kGrpSticky},
    {0x004ab040, "a1183fa100 8b4004 8b4818 8b5014", kGrpSticky},
    {0x004ad580, "a1183fa100 8b4008 8b481c 8b5018", kGrpSticky},
    {0x004aee30, "53 668b5c240c 55 56 8bf1 33ed 392e 57 764e 8b4608", kGrpSticky},
    {0x004aee50, "66395804 752f 8a4806 3a4c241a 7526 84c9 7405 80f901 7508 8b10 3b542414 744b", kGrpSticky},
    {0x004aee85, "83c501 83c00c 3b2e 72c1 3b6e0c", kGrpSticky},
    {0x004b17f7, "8b4c2404 8b7118 8b442414 8b542408 890496 5e 83c408 89442408 89542404 e926dfffff", kGrpSticky},
    {0x004b0941, "8b7e14 8b54241c 8bc8 c1e903 03f9 8bc8 83e107 b301 d2e3 84d2 7414 081f 52 50 8bce e869edffff",
     kGrpSticky},
    {0x004b18a5, "d9442410 8b0c24 8b442404 8b5118 51 d91482 d91c24 50 e8f0deffff", kGrpSticky},
    {0x004af6d0, "8b442404 53 56 8d3440 57 03f6 8bf9 8b4708 03f6 8b5c3008 85db 744b", kGrpSticky},
    {0x004af733, "c20800", kGrpSticky},
    {0x004af740, "8b442404 53 56 8d3440 57 03f6 8bf9 8b4708 03f6 8b5c3008 85db 744b", kGrpSticky},
    {0x004af7a3, "c20800", kGrpSticky},
    {0x004af7b0, "8b442404 53 56 8d3440 57 03f6 8bf9 8b4708 03f6 8b5c3008 85db 744e", kGrpSticky},
    {0x004af816, "c20800", kGrpSticky},
    // script objects: runtime ScriptType (vtable, +8 stream root)
    {0x005784f0, "c706d4e48400 894610 894614 884618 884619 8b442408 50 e834c4ffff 894608", kGrpScript},
    // hide / unhide = message 7 (data != 0 hides): default handler and the multibody handler (all parts)
    {0x005b4110, "8b442408 833807 752b 83780400 8b442404 7411 81481800000020 81481400080400", kGrpHide},
    {0x004d1508, "83f807 7445", kGrpHide},
};
const int kTlCheckCount = static_cast<int>(sizeof(kTlChecks) / sizeof(kTlChecks[0]));

inline int HexToBytes(const char *hex, BYTE *out, int max) {
    int n = 0;
    for (const char *p = hex; *p && n < max;) {
        if (*p == ' ') { ++p; continue; }
        char pair[3] = {p[0], p[1], 0};
        out[n++] = static_cast<BYTE>(strtoul(pair, nullptr, 16));
        p += 2;
    }
    return n;
}

// runs every row through TlRead: ok[group] = all rows of the group match; returns the number of bad rows, the first
// bad address in *firstBad (0 = none)
inline int RunChecks(bool *ok, DWORD *firstBad, int *rows) {
    int bad = 0;
    *firstBad = 0;
    for (int g = 0; g < kGrpCount; ++g) { ok[g] = true; rows[g] = 0; }
    for (int i = 0; i < kTlCheckCount; ++i) {
        BYTE want[96], have[96];
        const int n = HexToBytes(kTlChecks[i].hex, want, sizeof(want));
        ++rows[kTlChecks[i].group];
        if (!TlRead(kTlChecks[i].at, have, static_cast<DWORD>(n)) || memcmp(want, have, static_cast<size_t>(n))) {
            ok[kTlChecks[i].group] = false;
            if (!bad++) *firstBad = kTlChecks[i].at;
        }
    }
    return bad;
}

// ---- reads ----
inline bool R32(DWORD a, DWORD *v) { return a && TlRead(a, v, 4); }
inline bool RF(DWORD a, float *v) { return a && TlRead(a, v, 4); }
inline bool R16(DWORD a, WORD *v) { return a && TlRead(a, v, 2); }
inline bool R8(DWORD a, BYTE *v) { return a && TlRead(a, v, 1); }
inline DWORD D(DWORD a) { DWORD v = 0; return R32(a, &v) ? v : 0; }
// a printable 0-terminated string (at most n - 1 chars); false = unreadable / not printable / empty
inline bool RStr(DWORD a, char *out, size_t n) {
    out[0] = 0;
    if (!a || n < 2) return false;
    size_t i = 0;
    for (; i + 1 < n; ++i) {
        BYTE c = 0;
        if (!R8(a + static_cast<DWORD>(i), &c)) { out[0] = 0; return false; }
        if (!c) break;
        if (c < 32 || c > 126) { out[0] = 0; return false; }
        out[i] = static_cast<char>(c);
    }
    out[i] = 0;
    return i > 0;
}
inline double Deg(float rad) { return static_cast<double>(rad * kRadToDeg); }

// ---- instances ----
inline bool ObjName(int id, char *out, size_t n) {
    out[0] = 0;
    const DWORD table = D(kObjNames);
    const DWORD count = table ? D(table) : 0;
    if (id <= 0 || !table || id > static_cast<int>(count) || count > 8192) return false;
    return RStr(D(table + static_cast<DWORD>(id) * 8), out, n);
}
inline int ObjectId(DWORD inst) {
    const DWORD object = D(inst + 0x10);
    return object ? static_cast<int>(D(object + 0x14) & 0xffff) : 0;
}
inline void InstName(DWORD inst, char *out, size_t n) {
    const int id = ObjectId(inst);
    if (!ObjName(id, out, n)) _snprintf_s(out, n, _TRUNCATE, "obj%d", id);
}
inline bool UnitName(DWORD id, char *out, size_t n) {
    out[0] = 0;
    for (int i = 0; i < kUnitCount; ++i) {
        const DWORD e = kUnits + static_cast<DWORD>(i) * kUnitSize;
        BYTE state = 0;
        if (D(e) == id && R8(e + 4, &state) && state == 2) return RStr(e + 0xc, out, n);
    }
    return false;
}
// handle {instance, stamp}: valid while [instance+0x44] == stamp (0x5b39d0)
inline DWORD HandleInst(DWORD handle) {
    DWORD inst = 0, stamp = 0, now = 0;
    if (!R32(handle, &inst) || !inst || !R32(handle + 4, &stamp) || !R32(inst + 0x44, &now) || now != stamp) return 0;
    return inst;
}
// u = [[inst+0x2d0]]+0x2ec (0x4d5d59 / 0x4d14a0)
inline DWORD SlotU(DWORD inst) {
    const DWORD p = D(inst + 0x2d0);
    const DWORD a = p ? D(p) : 0;
    return a ? D(a + 0x2ec) : 0;
}
inline DWORD Uber(DWORD inst) {
    const DWORD u = SlotU(inst);
    if (u < 0x10) return 0;
    return D(u - 0x10 + 0x70) == kUberMagic ? u - 0x10 : 0;
}
inline bool IsMulti(DWORD x) {
    const DWORD vt = D(x);
    return x && D(x + 0x54) == kMultiMagic && (vt == kMultiVt || vt == kMultiVtSub);
}
inline DWORD Multi(DWORD inst) {
    const DWORD u = SlotU(inst);
    return u >= 4 && IsMulti(u - 4) ? u - 4 : 0;
}
// the multibody object of an instance: its own (placed intro) or the one its uber state belongs to (b+0x7c)
inline DWORD MultiOfAny(DWORD inst) {
    const DWORD x = Multi(inst);
    if (x) return x;
    const DWORD b = Uber(inst);
    const DWORD bx = b ? D(b + 0x7c) : 0;
    return IsMulti(bx) ? bx : 0;
}
inline int Links(DWORD x) {
    const DWORD n = D(x + 0x70);
    return n <= 64 ? static_cast<int>(n) : 0;
}
inline DWORD LinkInst(DWORD x, int i) { return i >= 0 && i < Links(x) ? HandleInst(D(x + 0x6c) + 8u * i) : 0; }

// walks the list; fn(inst, index) returns false to stop; returns the count walked (guard 4096)
template <typename F> int ForInstances(F fn) {
    DWORD inst = D(kInstanceList);
    int i = 0;
    for (; inst && i < 4096; ++i) {
        if (!fn(inst, i)) return i + 1;
        if (!R32(inst + 8, &inst)) break;
    }
    return i;
}
// "player" / "lara", "#<list index>", "0x<instance>" (must be in the list), "<intro id>" -> instance (0 = none, why)
inline DWORD FindInst(const char *arg, char *why, size_t wn) {
    why[0] = 0;
    if (!arg || !arg[0]) { _snprintf_s(why, wn, _TRUNCATE, "give an instance: intro id, 0x<address>, #<index> or player"); return 0; }
    if (!_stricmp(arg, "player") || !_stricmp(arg, "lara")) {
        const DWORD p = D(kPlayer);
        if (!p) _snprintf_s(why, wn, _TRUNCATE, "no player (GameTracker +0xc is 0)");
        return p;
    }
    DWORD found = 0;
    char *end = nullptr;
    if (arg[0] == '#') {
        const long want = strtol(arg + 1, &end, 10);
        if (*end || want < 0) { _snprintf_s(why, wn, _TRUNCATE, "bad list index '%s'", arg); return 0; }
        ForInstances([&](DWORD inst, int i) { if (i == want) { found = inst; return false; } return true; });
    } else if (arg[0] == '0' && (arg[1] == 'x' || arg[1] == 'X')) {
        const DWORD want = strtoul(arg, &end, 16);
        if (*end) { _snprintf_s(why, wn, _TRUNCATE, "bad address '%s'", arg); return 0; }
        ForInstances([&](DWORD inst, int) { if (inst == want) { found = inst; return false; } return true; });
    } else {
        const unsigned long want = strtoul(arg, &end, 10);
        if (*end) { _snprintf_s(why, wn, _TRUNCATE, "'%s' is no intro id / 0x<address> / #<index> / player", arg); return 0; }
        ForInstances([&](DWORD inst, int) { if (D(inst + 0x58) == want) { found = inst; return false; } return true; });
    }
    if (!found) _snprintf_s(why, wn, _TRUNCATE, "no instance '%s' in the instance list [0x%08lx]", arg, kInstanceList);
    return found;
}
inline int ListIndex(DWORD want) {
    int at = -1;
    ForInstances([&](DWORD inst, int i) { if (inst == want) { at = i; return false; } return true; });
    return at;
}
inline DWORD InstByIntro(DWORD intro) {
    DWORD found = 0;
    if (intro) ForInstances([&](DWORD inst, int) { if (D(inst + 0x58) == intro) { found = inst; return false; } return true; });
    return found;
}

// ---- uber graph ----
inline int NodeCount(DWORD b) {
    const DWORD desc = D(b + 0x78);
    const DWORD n = desc ? D(desc + 4) : 0;
    return n <= 64 ? static_cast<int>(n) : 0;
}
inline DWORD NodeAddr(DWORD b, LONG k) {
    const DWORD desc = D(b + 0x78);
    const DWORD nodes = desc ? D(desc + 8) : 0;
    return nodes && k >= 0 && k < NodeCount(b) ? nodes + 28u * static_cast<DWORD>(k) : 0;
}
inline void NodeName(DWORD b, LONG k, char *out, size_t n) {
    const DWORD node = NodeAddr(b, k);
    if (!node || !RStr(D(node + 8), out, n)) _snprintf_s(out, n, _TRUNCATE, "%s", k < 0 ? "-" : "?");
}
inline int TransCount(DWORD node) {
    const DWORD n = node ? D(node + 0xc) : 0;
    return n <= 64 ? static_cast<int>(n) : 0;
}
inline DWORD TransAt(DWORD node, int j) {
    const DWORD arr = D(node + 0x10);
    return arr && j >= 0 && j < TransCount(node) ? D(arr + 4u * static_cast<DWORD>(j)) : 0;
}
// how a transition is fired: the uber.send form when there is one
inline void CondText(DWORD t, char *out, size_t n) {
    const DWORD cond = D(t + 0x18), arg = D(t + 0x1c);
    float f = 0.0f;
    memcpy(&f, &arg, 4);
    switch (cond) {
    case 1: _snprintf_s(out, n, _TRUNCATE, "time in node >= %.2f s", static_cast<double>(f)); break;
    case 3: _snprintf_s(out, n, _TRUNCATE, "immediately"); break;
    case 6: case 7: case 8: _snprintf_s(out, n, _TRUNCATE, "hit force %lu > %.1f (message 0x2b)", cond, static_cast<double>(f)); break;
    case 9: _snprintf_s(out, n, _TRUNCATE, "object check (linked parts in nodes)"); break;
    case 11: case 12: _snprintf_s(out, n, _TRUNCATE, "flags +0x90 & 6 == %d", cond == 11 ? 2 : 4); break;
    case 13: _snprintf_s(out, n, _TRUNCATE, "broadcast %lu  [uber.send <id> broadcast %lu]", arg, arg); break;
    case 14: case 15: _snprintf_s(out, n, _TRUNCATE, "joint range %s", cond == 14 ? "entered" : "left"); break;
    case 16: _snprintf_s(out, n, _TRUNCATE, "command %lu  [uber.send <id> command %lu]", arg, arg); break;
    case 17: _snprintf_s(out, n, _TRUNCATE, "damage >= %.1f", static_cast<double>(f)); break;
    case 18: _snprintf_s(out, n, _TRUNCATE, "damage threshold (subclass)"); break;
    case 19: _snprintf_s(out, n, _TRUNCATE, "damage kind %lu", arg); break;
    default: _snprintf_s(out, n, _TRUNCATE, "event %lu (arg 0x%08lx)  [uber.send <id> event %lu]", cond, arg, cond); break;
    }
}

// ---- joints (X+0x74 list, node +8 record, +0x1c physics joint J) ----
inline int JointCount(DWORD x) {
    const DWORD s = D(x + 0x74);
    DWORD node = s ? D(s) : 0;
    int i = 0;
    while (node && node != s && i < 64) { ++i; node = D(node); }
    return i;
}
inline bool JointAt(DWORD x, int index, DWORD *jrec, DWORD *joint) {
    const DWORD s = D(x + 0x74);
    DWORD node = s ? D(s) : 0;
    for (int i = 0; node && node != s && i < 64; ++i) {
        if (i == index) { *jrec = D(node + 8); *joint = D(node + 0x1c); return *joint != 0; }
        node = D(node);
    }
    return false;
}
inline int JointIndexOf(DWORD x, DWORD jrec) {
    const DWORD s = D(x + 0x74);
    DWORD node = s ? D(s) : 0;
    for (int i = 0; node && node != s && i < 64; ++i) {
        if (D(node + 8) == jrec) return i;
        node = D(node);
    }
    return -1;
}
inline int JointType(DWORD joint) {
    BYTE t = 0;
    return R8(joint + 0x178, &t) ? t : -1;
}
inline const char *JointTypeName(int type) { return type == 1 ? "hinge" : type == 3 ? "rail" : "other"; }
// range record type 0 / 2 (hinge / rail, axis 0): [min, max) at +4 / +8 (0x4d11e0)
inline bool RangeOf(DWORD rrec, float *lo, float *hi) {
    BYTE t = 0xff;
    return R8(rrec, &t) && (t == 0 || t == 2) && RF(rrec + 4, lo) && RF(rrec + 8, hi);
}
// one joint line (value through TlJointValue: live on the game thread, "n/a" offline)
inline void JointLine(const char *prefix, DWORD x, int index) {
    DWORD jrec = 0, joint = 0;
    if (!JointAt(x, index, &jrec, &joint)) { TlAdd("%sjoint %d: not in the list of X 0x%08lx\n", prefix, index, x); return; }
    const int type = JointType(joint);
    BYTE recType = 0xff, motors = 0;
    R8(jrec, &recType);
    R8(joint + 0x179, &motors);
    float lim[2] = {0, 0}, vel = 0, force = 0, v = 0;
    DWORD flags = 0;
    RF(joint + 0xd8, &lim[0]);
    RF(joint + 0xdc, &lim[1]);
    R32(joint + 0x174, &flags);
    RF(joint + 0x108, &vel);
    RF(joint + 0x10c, &force);
    const bool hinge = type == 1;
    char value[48];
    if ((type == 1 || type == 3) && TlJointValue(joint, type, &v))
        _snprintf_s(value, sizeof(value), _TRUNCATE, "%.2f %s", static_cast<double>(v), hinge ? "deg" : "units");
    else
        _snprintf_s(value, sizeof(value), _TRUNCATE, "%s", type == 1 || type == 3 ? "n/a (offline / unreadable)" : "-");
    TlAdd("%sjoint %d: %s (phys %d, record 0x%08lx type %u, A %ld B %ld) J 0x%08lx value %s limits [%.2f, %.2f]%s "
          "limit %s motor %s (vel %.3f%s force %.6g, motors %u)\n", prefix, index, JointTypeName(type), type, jrec,
          recType, static_cast<LONG>(D(jrec + 4)), static_cast<LONG>(D(jrec + 8)), joint, value,
          hinge ? Deg(lim[0]) : static_cast<double>(lim[0]), hinge ? Deg(lim[1]) : static_cast<double>(lim[1]),
          hinge ? " deg" : "", (flags & 2) ? "on" : "off", (flags & 0x10) ? "on" : "off",
          hinge ? Deg(vel) : static_cast<double>(vel), hinge ? " deg/s" : "", static_cast<double>(force), motors);
}

// ---- script object [inst+0x60]: +8 ScriptType (vtable 0x84e4d4, +8 root), +0xc data, +0x20 owner instance;
//      root +0x2c members (count at ptr-4), 20 B {+0 tag (base type = low 4 bits, bit 7 compound), +4 u16 user type,
//      +8 union (ScriptType* or Compound {ScriptType*, sub}), +0xc u16 offset, +0xe u16 name Symbol, +0x10 init} ----
struct Member { DWORD tag, uni, init; WORD user, offset, name; char type[32]; };
inline DWORD ScriptObj(DWORD inst) { return D(inst + 0x60); }
inline DWORD ScriptRoot(DWORD so) {
    const DWORD t = D(so + 8);
    return t && D(t) == kScriptTypeVt ? D(t + 8) : 0;
}
inline int MemberCount(DWORD root) {
    const DWORD m = D(root + 0x2c);
    const DWORD n = m ? D(m - 4) : 0;
    return m && n <= 256 ? static_cast<int>(n) : 0;
}
inline bool MemberAt(DWORD root, int k, Member *m) {
    memset(m, 0, sizeof(*m));
    const DWORD base = D(root + 0x2c);
    if (!base || k < 0 || k >= MemberCount(root)) return false;
    const DWORD e = base + 20u * static_cast<DWORD>(k);
    if (!R32(e, &m->tag) || !R16(e + 4, &m->user) || !R32(e + 8, &m->uni) || !R16(e + 0xc, &m->offset) ||
        !R16(e + 0xe, &m->name) || !R32(e + 0x10, &m->init))
        return false;
    const DWORD bt = m->tag & 0xf;
    if ((bt == 0xa || bt == 0xb) && m->uni) {             // a script type: its native name (stickybool, instanceref ...)
        const DWORD st = (m->tag & 0x80) ? D(m->uni) : m->uni;
        const DWORD r = st && D(st) == kScriptTypeVt ? D(st + 8) : 0;
        if (!r || !RStr(D(r + 0x10), m->type, sizeof(m->type))) _snprintf_s(m->type, sizeof(m->type), _TRUNCATE, "type%u", m->user);
    } else {
        _snprintf_s(m->type, sizeof(m->type), _TRUNCATE, "bt%lu", bt);
    }
    return true;
}
inline bool IsSticky(const Member &m) { return !strncmp(m.type, "sticky", 6); }
// the sticky key of a member: first value word of its init block (in memory {ptr = init + 4, value ...})
inline bool MemberKey(const Member &m, WORD *key) {
    if (!m.init) return false;
    DWORD p = D(m.init);
    if (p != m.init + 4) p = m.init;
    return R16(p, key);
}
// the instance that owns the script object (sticky owner; runtime uber parts share the placed one's script)
inline DWORD ScriptOwner(DWORD inst) {
    const DWORD so = ScriptObj(inst);
    const DWORD owner = so ? D(so + 0x20) : 0;
    return owner && D(owner + 0x60) == so ? owner : inst;
}

// ---- sticky store (ENGINE 6.3; TruMenu sticky.get) ----
const char *const kStTypes[3] = {"int", "bool", "float"};
struct StHit { int type; DWORD store, index; };
inline int StFind(int kind, DWORD owner, WORD key, StHit *hits, char *why, size_t wn) {
    why[0] = 0;
    const DWORD impl = D(kStImpl);
    if (!impl) { _snprintf_s(why, wn, _TRUNCATE, "no sticky store yet ([0xa13f18] = 0: title screen?)"); return -1; }
    int found = 0;
    for (int t = 0; t < 3; ++t) {
        const DWORD store = D(impl + 4u * static_cast<DWORD>(t));
        DWORD count = 0, entries = 0, max = 0;
        if (!store || !R32(store, &count) || !R32(store + 8, &entries) || !R32(store + 0xc, &max) || !entries ||
            count > max || max > 0x1000)
            continue;
        for (DWORD i = 0; i < count; ++i) {
            BYTE e[8];
            if (!TlRead(entries + i * 12, e, 7)) break;
            DWORD id = 0;
            WORD k = 0;
            memcpy(&id, e, 4);
            memcpy(&k, e + 4, 2);
            if (k == key && e[6] == kind && id == owner) {
                hits[found].type = t;
                hits[found].store = store;
                hits[found++].index = i;
                break;
            }
        }
    }
    return found;
}
inline bool StRaw(const StHit &h, DWORD *raw) {
    DWORD base = 0, size = 0;
    if (h.type == 1) {
        BYTE b = 0;
        if (!R32(h.store + 0x14, &base) || !R32(h.store + 0x18, &size) || (h.index >> 3) >= size || !R8(base + (h.index >> 3), &b))
            return false;
        *raw = (b >> (h.index & 7)) & 1;
        return true;
    }
    return R32(h.store + 0x18, &base) && R32(h.store + 0x1c, &size) && h.index * 4 < size && R32(base + h.index * 4, raw);
}
inline void StText(int type, DWORD raw, char *out, size_t n) {
    if (type == 2) {
        float f = 0.0f;
        memcpy(&f, &raw, 4);
        _snprintf_s(out, n, _TRUNCATE, "%g", static_cast<double>(f));
    } else {
        _snprintf_s(out, n, _TRUNCATE, "%ld", static_cast<LONG>(raw));
    }
}

// the value text of a member in data (instanceref: intro id + name; sticky: key + store value; else raw)
inline void MemberValue(const Member &m, DWORD data, DWORD ownerIntro, char *out, size_t n) {
    out[0] = 0;
    const DWORD at = data + m.offset;
    if (!strcmp(m.type, "instanceref")) {
        const DWORD intro = D(at);
        char name[64] = "";
        const DWORD inst = InstByIntro(intro);
        if (inst) InstName(inst, name, sizeof(name));
        _snprintf_s(out, n, _TRUNCATE, "-> intro %lu %s", intro, inst ? name : "(no instance)");
    } else if (IsSticky(m)) {
        WORD key = 0;
        if (!MemberKey(m, &key)) { _snprintf_s(out, n, _TRUNCATE, "key unreadable"); return; }
        StHit hits[3];
        char why[96];
        const int k = StFind(0, ownerIntro, key, hits, why, sizeof(why));
        DWORD raw = 0;
        char v[32] = "-";
        if (k > 0 && StRaw(hits[0], &raw)) StText(hits[0].type, raw, v, sizeof(v));
        const DWORD dOwner = D(at);
        WORD dKey = 0;
        R16(at + 4, &dKey);
        _snprintf_s(out, n, _TRUNCATE, "key %u owner 0:%lu = %s%s%s%s", key, ownerIntro, k > 0 ? kStTypes[hits[0].type] : "",
                    k > 0 ? " " : "", k > 0 ? v : k < 0 ? why : "(no store entry yet)",
                    dOwner == ownerIntro && dKey == key ? "" : " (member data owner / key differ!)");
    } else {
        DWORD raw = D(at);
        float f = 0.0f;
        memcpy(&f, &raw, 4);
        _snprintf_s(out, n, _TRUNCATE, "raw 0x%08lx (%ld / %g)", raw, static_cast<LONG>(raw), static_cast<double>(f));
    }
}

// ---- answers ----
// obj.near: instances within radius (units) of Lara, nearest first; filter: "" all, "uber", "multi", or a name part
struct NearRow { DWORD inst; float d2; int index; };
inline void Near(float radius, const char *filter, int maxRows) {
    const DWORD player = D(kPlayer);
    float lara[3] = {0, 0, 0};
    if (!player || !TlRead(player + 0x20, lara, 12)) { TlAdd("err no player (needs a level)\n"); return; }
    static NearRow rows[1024];
    int count = 0, walked = 0, inRadius = 0;
    char low[64] = "";
    if (filter) { strncpy_s(low, sizeof(low), filter, _TRUNCATE); _strlwr_s(low, sizeof(low)); }
    const float r2 = radius * radius;
    walked = ForInstances([&](DWORD inst, int i) {
        float p[3];
        if (!TlRead(inst + 0x20, p, 12)) return true;
        const float dx = p[0] - lara[0], dy = p[1] - lara[1], dz = p[2] - lara[2], d2 = dx * dx + dy * dy + dz * dz;
        if (!(d2 <= r2)) return true;
        ++inRadius;
        if (low[0]) {
            if (!strcmp(low, "uber")) { if (!Uber(inst)) return true; }
            else if (!strcmp(low, "multi")) { if (!Multi(inst)) return true; }
            else {
                char name[64];
                InstName(inst, name, sizeof(name));
                _strlwr_s(name, sizeof(name));
                if (!strstr(name, low)) return true;
            }
        }
        if (count < 1024) { rows[count].inst = inst; rows[count].d2 = d2; rows[count].index = i; ++count; }
        return true;
    });
    for (int a = 1; a < count; ++a) {                        // insertion sort, nearest first
        NearRow r = rows[a];
        int b = a;
        while (b > 0 && rows[b - 1].d2 > r.d2) { rows[b] = rows[b - 1]; --b; }
        rows[b] = r;
    }
    const int shown = count < maxRows ? count : maxRows;
    TlAdd("ok+ obj.near %.1f m (%.0f units) filter '%s': %d of %d in radius shown (%d instances walked); "
          "#index instance intro object unit pos distance [uber node] [multibody links] [flags]\n",
          static_cast<double>(radius / kUnitsPerMetre), static_cast<double>(radius), filter ? filter : "", shown,
          inRadius, walked);
    for (int k = 0; k < shown; ++k) {
        const DWORD inst = rows[k].inst;
        float p[3] = {0, 0, 0};
        TlRead(inst + 0x20, p, 12);
        char name[64], unit[64], extra[192] = "";
        InstName(inst, name, sizeof(name));
        const DWORD uid = D(inst + 0xe0);
        if (!UnitName(uid, unit, sizeof(unit))) _snprintf_s(unit, sizeof(unit), _TRUNCATE, "?");
        size_t used = 0;
        const DWORD b = Uber(inst), x = Multi(inst), fl = D(inst + 0x14), parent = D(inst + 0x54);
        if (b) {
            char node[48], to[48] = "";
            NodeName(b, static_cast<LONG>(D(b + 0x84)), node, sizeof(node));
            const DWORD trans = D(b + 0x80);
            if (trans) NodeName(b, static_cast<LONG>(D(trans + 4)), to, sizeof(to));
            used += _snprintf_s(extra + used, sizeof(extra) - used, _TRUNCATE, " uber '%s'%s%s", node, trans ? " -> " : "",
                                to);
        }
        if (x && used < sizeof(extra)) used += _snprintf_s(extra + used, sizeof(extra) - used, _TRUNCATE, " multibody links %d", Links(x));
        if ((fl & 0x800) && used < sizeof(extra)) used += _snprintf_s(extra + used, sizeof(extra) - used, _TRUNCATE, " hidden");
        if ((fl & 0x20) && used < sizeof(extra)) used += _snprintf_s(extra + used, sizeof(extra) - used, _TRUNCATE, " kill");
        if (parent && parent != player && used < sizeof(extra))
            _snprintf_s(extra + used, sizeof(extra) - used, _TRUNCATE, " parent %lu", D(parent + 0x58));
        const float d = sqrtf(rows[k].d2);
        TlAdd("#%d 0x%08lx intro %ld obj %d %s unit %ld %s pos %.1f %.1f %.1f dist %.0f (%.1f m)%s\n", rows[k].index, inst,
              static_cast<LONG>(D(inst + 0x58)), ObjectId(inst), name, static_cast<LONG>(uid), unit, static_cast<double>(p[0]),
              static_cast<double>(p[1]), static_cast<double>(p[2]), static_cast<double>(d),
              static_cast<double>(d / kUnitsPerMetre), extra);
    }
    if (count > shown) TlAdd("... %d more (obj.near <m> <filter> max <n>, at most 400)\n", count - shown);
    TlAdd(".\n");
}

// the command table of a multibody object: [[X+0x58]+0x50] +0x10 count, +0x14 entries {?, n +4, records +8},
// record 12 B {link index, kind, value} - what X vf+4 (0x4d77a0) delivers through 0x4d7680
inline int CmdCount(DWORD x) {
    const DWORD data = D(D(x + 0x58) + 0x50);
    const DWORD n = data ? D(data + 0x10) : 0;
    return n <= 64 ? static_cast<int>(n) : 0;
}
inline bool CmdRecords(DWORD x, int c, DWORD *records, int *n) {
    const DWORD data = D(D(x + 0x58) + 0x50);
    const DWORD entries = data ? D(data + 0x14) : 0;
    if (!entries || c < 0 || c >= CmdCount(x)) return false;
    const DWORD rn = D(entries + 12u * static_cast<DWORD>(c) + 4);
    *records = D(entries + 12u * static_cast<DWORD>(c) + 8);
    *n = rn <= 32 ? static_cast<int>(rn) : 0;
    return *records != 0 || *n == 0;
}
const char *const kKindNames[5] = {"?", "set node", "event", "broadcast", "command"};
// would message {kind, value} start a transition of b now? (the engine's own matching, 0x4d4be0 / 0x4d5b30 /
// 0x4d5bb0): returns the transition or 0; *dropped = the engine drops events now (+0x80 / +0x90 & 9)
inline DWORD MatchNow(DWORD b, DWORD kind, DWORD value, bool *dropped) {
    *dropped = D(b + 0x80) != 0 || (D(b + 0x90) & 9) != 0;
    const DWORD node = NodeAddr(b, static_cast<LONG>(D(b + 0x84)));
    for (int j = 0; node && j < TransCount(node); ++j) {
        const DWORD t = TransAt(node, j), cond = D(t + 0x18), arg = D(t + 0x1c);
        if ((kind == 2 && cond == value) || (kind == 3 && cond == 13 && arg == value) || (kind == 4 && cond == 16 && arg == value))
            return t;
    }
    return 0;
}
inline void CommandTable(DWORD x, const char *prefix) {
    const int cn = CmdCount(x);
    TlAdd("%scommand table: %d entr%s  [uber.send <placed intro> cmd <n>]\n", prefix, cn, cn == 1 ? "y" : "ies");
    for (int c = 0; c < cn; ++c) {
        DWORD rec = 0;
        int rn = 0;
        if (!CmdRecords(x, c, &rec, &rn)) { TlAdd("%s  cmd %d: unreadable\n", prefix, c); continue; }
        for (int r = 0; r < rn; ++r) {
            const DWORD e = rec + 12u * static_cast<DWORD>(r);
            const LONG link = static_cast<LONG>(D(e));
            const DWORD kind = D(e + 4), value = D(e + 8);
            const DWORD li = LinkInst(x, link);
            const DWORD b = li ? Uber(li) : 0;
            char now[48] = "-", effect[96] = "";
            if (b) {
                NodeName(b, static_cast<LONG>(D(b + 0x84)), now, sizeof(now));
                if (kind == 1) {
                    char to[48];
                    NodeName(b, static_cast<LONG>(value), to, sizeof(to));
                    _snprintf_s(effect, sizeof(effect), _TRUNCATE, " -> set node %lu '%s'", value, to);
                } else if (kind >= 2 && kind <= 4) {
                    bool dropped = false;
                    const DWORD t = MatchNow(b, kind, value, &dropped);
                    char to[48] = "";
                    if (t) NodeName(b, static_cast<LONG>(D(t + 4)), to, sizeof(to));
                    _snprintf_s(effect, sizeof(effect), _TRUNCATE, "%s%s%s%s", dropped ? " (dropped now: transition running)" : "",
                                t ? " -> '" : " (no transition in this node now)", t ? to : "", t ? "'" : "");
                }
            }
            TlAdd("%s  cmd %d.%d: link %ld (intro %lu, node '%s') %s %lu%s\n", prefix, c, r, link, li ? D(li + 0x58) : 0,
                  now, kind <= 4 ? kKindNames[kind] : "kind?", value, effect);
        }
    }
}
// current node of b: its transitions and how to fire them
inline void NodeEvents(DWORD b, DWORD x, const char *prefix) {
    const LONG k = static_cast<LONG>(D(b + 0x84));
    const DWORD trans = D(b + 0x80), flags = D(b + 0x90);
    char name[48];
    NodeName(b, k, name, sizeof(name));
    float t = 0.0f;
    RF(b + 0x88, &t);
    TlAdd("%snode %ld '%s' time %.2f s flags +0x90 0x%lx%s%s\n", prefix, k, name, static_cast<double>(t), flags,
          trans ? " - a transition runs: events are dropped now" : "", (flags & 9) ? " - events dropped (+0x90 & 9)" : "");
    const DWORD node = NodeAddr(b, k);
    for (int j = 0; node && j < TransCount(node); ++j) {
        const DWORD tr = TransAt(node, j);
        char cond[96], to[48];
        CondText(tr, cond, sizeof(cond));
        NodeName(b, static_cast<LONG>(D(tr + 4)), to, sizeof(to));
        const DWORD c = D(tr + 0x18);
        char joint[128] = "";
        if ((c == 14 || c == 15) && x) {
            float lo = 0, hi = 0, v = 0;
            const DWORD jrec = D(tr + 0x20);
            const int index = JointIndexOf(x, jrec);
            DWORD jr = 0, j2 = 0;
            const bool val = index >= 0 && JointAt(x, index, &jr, &j2) && TlJointValue(j2, JointType(j2), &v);
            if (RangeOf(D(tr + 0x24), &lo, &hi))
                _snprintf_s(joint, sizeof(joint), _TRUNCATE, " joint %d [%.2f, %.2f) value %s%.2f  [joint.drive <id> %d <target>]",
                            index, static_cast<double>(lo), static_cast<double>(hi), val ? "" : "n/a ", static_cast<double>(v), index);
        }
        TlAdd("%s  -> %lu '%s' on %s%s\n", prefix, D(tr + 4), to, cond, joint);
    }
}
inline void Events(DWORD inst) {
    char name[64];
    InstName(inst, name, sizeof(name));
    const DWORD b = Uber(inst), x = MultiOfAny(inst);
    TlAdd("ok+ uber.events 0x%08lx intro %lu %s%s\n", inst, D(inst + 0x58), name,
          !b && !x ? ": no uber state and no multibody object" : "");
    if (b) NodeEvents(b, x, "");
    if (Multi(inst)) {
        for (int i = 0; i < Links(x); ++i) {
            const DWORD li = LinkInst(x, i), lb = li ? Uber(li) : 0;
            if (!lb) { TlAdd("link %d: %s\n", i, li ? "no uber state" : "gone"); continue; }
            TlAdd("link %d (intro %lu):\n", i, D(li + 0x58));
            NodeEvents(lb, x, "  ");
        }
        CommandTable(x, "");
    } else if (x) {
        TlAdd("multibody X 0x%08lx of intro %lu: uber.events %lu lists its links and commands\n", x, D(D(x + 0x58) + 0x58),
              D(D(x + 0x58) + 0x58));
    }
    TlAdd(".\n");
}
inline void Graph(DWORD b, DWORD x) {
    const int nodes = NodeCount(b);
    const DWORD cur = D(b + 0x84);
    for (int k = 0; k < nodes; ++k) {
        char name[48];
        NodeName(b, k, name, sizeof(name));
        const DWORD node = NodeAddr(b, k);
        TlAdd("  node %d '%s'%s: %d transition(s), %lu action(s)\n", k, name, static_cast<DWORD>(k) == cur ? " (current)" : "",
              TransCount(node), D(node + 0x14));
        for (int j = 0; j < TransCount(node); ++j) {
            const DWORD tr = TransAt(node, j);
            char cond[96], to[48];
            CondText(tr, cond, sizeof(cond));
            NodeName(b, static_cast<LONG>(D(tr + 4)), to, sizeof(to));
            char extra[96] = "";
            const DWORD c = D(tr + 0x18);
            float lo = 0, hi = 0;
            if ((c == 14 || c == 15) && RangeOf(D(tr + 0x24), &lo, &hi))
                _snprintf_s(extra, sizeof(extra), _TRUNCATE, " joint %d [%.2f, %.2f)", x ? JointIndexOf(x, D(tr + 0x20)) : -1,
                            static_cast<double>(lo), static_cast<double>(hi));
            TlAdd("    -> %lu '%s' on %s%s\n", D(tr + 4), to, cond, extra);
        }
    }
}
inline void Info(DWORD inst) {
    char name[64], unit[64], birth[64];
    InstName(inst, name, sizeof(name));
    const DWORD intro = D(inst + 0x58), irec = D(inst + 0x100), uid = D(inst + 0xe0), buid = D(inst + 0xe4);
    const bool placed = irec && D(irec + 0x58) == intro;
    if (!UnitName(uid, unit, sizeof(unit))) _snprintf_s(unit, sizeof(unit), _TRUNCATE, "?");
    if (!UnitName(buid, birth, sizeof(birth))) _snprintf_s(birth, sizeof(birth), _TRUNCATE, "?");
    TlAdd("ok+ obj.info 0x%08lx\n", inst);
    char kind[64];
    if (placed) _snprintf_s(kind, sizeof(kind), _TRUNCATE, "placed");
    else if (irec) _snprintf_s(kind, sizeof(kind), _TRUNCATE, "runtime, carries the intro record of %lu", D(irec + 0x58));
    else _snprintf_s(kind, sizeof(kind), _TRUNCATE, "runtime, no intro record");
    TlAdd("intro %ld (%s) object %d %s list #%d stamp %lu\n", static_cast<LONG>(intro), kind, ObjectId(inst), name,
          ListIndex(inst), D(inst + 0x44));
    TlAdd("unit %ld %s, birth unit +0xe4 %ld %s\n", static_cast<LONG>(uid), unit, static_cast<LONG>(buid), birth);
    float p[3] = {0, 0, 0}, r[3] = {0, 0, 0}, old[3] = {0, 0, 0};
    TlRead(inst + 0x20, p, 12);
    TlRead(inst + 0x30, r, 12);
    TlRead(inst + 0xc0, old, 12);
    TlAdd("pos %.2f %.2f %.2f (+0x20; start of frame +0xc0: %.2f %.2f %.2f)\n", static_cast<double>(p[0]),
          static_cast<double>(p[1]), static_cast<double>(p[2]), static_cast<double>(old[0]), static_cast<double>(old[1]),
          static_cast<double>(old[2]));
    TlAdd("rot %.4f %.4f %.4f rad = %.2f %.2f %.2f deg (+0x30, z = yaw)\n", static_cast<double>(r[0]),
          static_cast<double>(r[1]), static_cast<double>(r[2]), Deg(r[0]), Deg(r[1]), Deg(r[2]));
    const DWORD f14 = D(inst + 0x14);
    TlAdd("iflags +0x14 0x%08lx (%s%s%s) +0x18 0x%08lx +0x1c 0x%08lx no-draw +0x23c 0x%08lx +0x240 0x%08lx\n", f14,
          (f14 & 0x800) ? "hidden " : "", (f14 & 0x20) ? "kill " : "", (f14 & 0x200) ? "drawn" : "not drawn this frame",
          D(inst + 0x18), D(inst + 0x1c), D(inst + 0x23c), D(inst + 0x240));
    if (irec) {
        float ip[3] = {0, 0, 0}, ir[3] = {0, 0, 0}, is[3] = {0, 0, 0};
        TlRead(irec + 0x10, ip, 12);
        TlRead(irec, ir, 12);
        TlRead(irec + 0x40, is, 12);
        TlAdd("intro record 0x%08lx: pos %.2f %.2f %.2f rot z %.2f deg scale %.3f %.3f %.3f object %u unique %lu data 0x%08lx\n",
              irec, static_cast<double>(ip[0]), static_cast<double>(ip[1]), static_cast<double>(ip[2]), Deg(ir[2]),
              static_cast<double>(is[0]), static_cast<double>(is[1]), static_cast<double>(is[2]), D(irec + 0x50) & 0xffff,
              D(irec + 0x58), D(irec + 0x78));
    }
    const DWORD parent = D(inst + 0x54), child = D(inst + 0x218), sibling = D(inst + 0x21c);
    TlAdd("intro data +0x104 0x%08lx; parent +0x54 0x%08lx (intro %lu); first child +0x218 0x%08lx, sibling +0x21c "
          "0x%08lx; link parent id +0x228 %lu\n", D(inst + 0x104), parent, parent ? D(parent + 0x58) : 0, child, sibling,
          D(inst + 0x228));
    const DWORD object = D(inst + 0x10);
    WORD models = 0;
    BYTE curModel = 0;
    R16(object + 0x3a, &models);
    R8(inst + 0x235, &curModel);
    TlAdd("object 0x%08lx models %u (+0x3a, DTPs +0x40 0x%08lx) current model +0x235 %u; process +0x110 0x%08lx, "
          "message +0x120 0x%08lx, object data +0x50 0x%08lx\n", object, models, D(object + 0x40), curModel,
          D(inst + 0x110), D(inst + 0x120), D(inst + 0x50));
    // script
    const DWORD so = ScriptObj(inst), root = so ? ScriptRoot(so) : 0;
    if (so) {
        const DWORD data = D(so + 0xc), owner = ScriptOwner(inst), ownerIntro = D(owner + 0x58);
        const int mc = root ? MemberCount(root) : 0;
        TlAdd("script object 0x%08lx type 0x%08lx root 0x%08lx data 0x%08lx owner intro %ld: %d member(s) of its own "
              "type (base class members not listed)\n", so, D(so + 8), root, data, static_cast<LONG>(ownerIntro), mc);
        for (int k = 0; k < mc; ++k) {
            Member m;
            if (!MemberAt(root, k, &m)) break;
            char v[160];
            MemberValue(m, data, ownerIntro, v, sizeof(v));
            TlAdd("  m%d +%u %s (name sym %u, user %u): %s\n", k, m.offset, m.type, m.name, m.user, v);
        }
    } else {
        TlAdd("script object: none (+0x60 = 0)\n");
    }
    // multibody
    const DWORD x = Multi(inst);
    if (x) {
        TlAdd("multibody X 0x%08lx (vtable 0x%08lx): %d link(s), %d joint(s)\n", x, D(x), Links(x), JointCount(x));
        for (int i = 0; i < Links(x); ++i) {
            const DWORD li = LinkInst(x, i), lb = li ? Uber(li) : 0;
            char ln[64] = "", node[48] = "-";
            if (li) InstName(li, ln, sizeof(ln));
            if (lb) NodeName(lb, static_cast<LONG>(D(lb + 0x84)), node, sizeof(node));
            TlAdd("  link %d: 0x%08lx intro %lu %s%s%s%s\n", i, li, li ? D(li + 0x58) : 0, ln, lb ? " uber node '" : "",
                  lb ? node : (li ? " (no uber state)" : " (gone)"), lb ? "'" : "");
        }
        for (int j = 0; j < JointCount(x); ++j) JointLine("  ", x, j);
        CommandTable(x, "  ");
    }
    const DWORD b = Uber(inst);
    if (b) {
        const DWORD bx = D(b + 0x7c), trans = D(b + 0x80);
        char node[48], to[48] = "";
        NodeName(b, static_cast<LONG>(D(b + 0x84)), node, sizeof(node));
        if (trans) NodeName(b, static_cast<LONG>(D(trans + 4)), to, sizeof(to));
        float t = 0;
        RF(b + 0x88, &t);
        TlAdd("uber state 0x%08lx DESC 0x%08lx: node %lu '%s'%s%s time %.2f s wait +0x8c 0x%lx flags +0x90 0x%lx; "
              "multibody X 0x%08lx (intro %lu); %d node(s):\n", b, D(b + 0x78), D(b + 0x84), node, trans ? " -> " : "",
              to, static_cast<double>(t), D(b + 0x8c), D(b + 0x90), bx, IsMulti(bx) ? D(D(bx + 0x58) + 0x58) : 0,
              NodeCount(b));
        Graph(b, IsMulti(bx) ? bx : 0);
    }
    TlAdd(".\n");
}

}  // namespace tlobj
