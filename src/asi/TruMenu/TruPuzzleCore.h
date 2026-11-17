// TruPuzzleCore.h - TruMenu 0.22.56 / 0.22.57 "Raetsel in der Naehe": the pure-read puzzle analysis (switch base, plate
// flag, portable objects, P4 graph behaviour, object-check targets, ring steps, motor-closed hinges / rails; 0.22.57:
// the hold kind of a gate (timer node), switch -> command entry from the loaded scripts, "already used"), shared by TruMenu.asi
// and the offline test src\asi\TruLink\selftest\TruLinkObjTest.cpp, command `puzzle <id>` (the same code on a full
// minidump; scripts\windows\Test-TruLinkObj.ps1 -Command 'puzzle 4837'). Built on TruLink 0.5's
// decoders (src\asi\TruLink\TruLinkObj.h): every read goes through TlRead, the joint value through TlJointValue (game
// thread; false offline). Nothing here writes game memory or calls game code. Rules and sources: ENGINE section 9
// ("Switch -> target, static (P4)", "Target behaviour from the graph (P4)", the P5 rows "Chapel plates ...", "Chapel
// switches and shadow pillars", "Uber condition 9"), section 7.1 ("Switch in on reaction.").
#pragma once
#include "../TruLink/TruLinkObj.h"

namespace pzcore {

// the switch base of P5 (base script 3637, recognised by its shape - no id): a class of the chain whose member 0 is a
// 'modifiable' at +4 followed by seven ints at +8 .. +32; +16 off, +20 on, +24 disabled, +32 current state
struct PzSw { DWORD data; LONG cur, off, on, dis; };
inline bool PzSwitchOf(DWORD inst, PzSw *s) {
    const DWORD so = tlobj::ScriptObj(inst);
    if (!so) return false;
    DWORD roots[16];
    const int depth = tlobj::ClassChain(so, roots, 16);
    for (int d = 0; d < depth; ++d) {
        if (tlobj::MemberCount(roots[d]) < 8) continue;
        tlobj::Member m;
        if (!tlobj::MemberAt(roots[d], 0, &m) || strcmp(m.type, "modifiable") || m.offset != 4) continue;
        bool ints = true;
        for (int k = 1; k < 8 && ints; ++k)
            ints = tlobj::MemberAt(roots[d], k, &m) && (m.tag & 0xf) == 2 && m.offset == 4 + 4 * k;
        if (!ints) continue;
        s->data = tlobj::D(so + 0xc);
        s->off = static_cast<LONG>(tlobj::D(s->data + 16));
        s->on = static_cast<LONG>(tlobj::D(s->data + 20));
        s->dis = static_cast<LONG>(tlobj::D(s->data + 24));
        s->cur = static_cast<LONG>(tlobj::D(s->data + 32));
        return s->data != 0;
    }
    return false;
}
// 0 off, 1 on, 2 disabled, 3 other
inline int PzSwState(const PzSw &s) { return s.cur == s.dis ? 2 : s.cur == s.on ? 1 : s.cur == s.off ? 0 : 3; }
// 0.22.57: "pulled once" = instance +0x1c bit 0x200 (live 2026-11-16 V3: villa switches 4617 / 4525 0 -> 0x200 at the
// first pull while +32 stays 0 before and after; ENGINE 5.2: the bit is the "has been animated" entity bit - the marker
// we can see, not the game's own guard against a second pull, which is not found)
inline bool PzSwUsed(DWORD inst) { return (tlobj::D(inst + 0x1c) & 0x200) != 0; }
// 0.22.57: the open flag of a door without a state graph (P5 house door 4520, super 12171: stickybool +8 = 1 and
// modifiable f4(0) on open; live 16.11. V3b +8 0 -> 1): the first stickybool of a chain class that also has a
// 'modifiable' member; false = no such class / unreadable
inline bool PzOpenFlagRead(DWORD inst, int *flag) {
    const DWORD so = tlobj::ScriptObj(inst);
    if (!so) return false;
    DWORD roots[16];
    const int depth = tlobj::ClassChain(so, roots, 16);
    const DWORD owner = tlobj::D(tlobj::ScriptOwner(inst) + 0x58);
    for (int d = 0; d < depth; ++d) {
        bool mod = false;
        int sticky = -1;
        tlobj::Member m;
        for (int k = 0; k < tlobj::MemberCount(roots[d]); ++k) {
            if (!tlobj::MemberAt(roots[d], k, &m)) continue;
            if (!strcmp(m.type, "modifiable")) mod = true;
            else if (sticky < 0 && !strcmp(m.type, "stickybool")) sticky = k;
        }
        if (!mod || sticky < 0 || !tlobj::MemberAt(roots[d], sticky, &m)) continue;
        WORD key = 0;
        tlobj::StHit hits[3];
        char why[96];
        DWORD raw = 0;
        if (!tlobj::MemberKey(m, &key) || tlobj::StFind(0, owner, key, hits, why, sizeof(why)) <= 0 || !tlobj::StRaw(hits[0], &raw))
            return false;
        *flag = raw ? 1 : 0;
        return true;
    }
    return false;
}
// the plate base's stickybool (P5: +92 = pressed) - the chain class whose member 0 is a 'multibody'; the value from the
// sticky store (owner = the script owner's intro id)
inline bool PzPlateFlagRead(DWORD inst, int *flag) {
    const DWORD so = tlobj::ScriptObj(inst);
    if (!so) return false;
    DWORD roots[16];
    const int depth = tlobj::ClassChain(so, roots, 16);
    const DWORD owner = tlobj::D(tlobj::ScriptOwner(inst) + 0x58);
    for (int d = 0; d < depth; ++d) {
        tlobj::Member m;
        if (!tlobj::MemberAt(roots[d], 0, &m) || strcmp(m.type, "multibody")) continue;
        for (int k = 1; k < tlobj::MemberCount(roots[d]); ++k) {
            WORD key = 0;
            if (!tlobj::MemberAt(roots[d], k, &m) || strcmp(m.type, "stickybool") || !tlobj::MemberKey(m, &key)) continue;
            tlobj::StHit hits[3];
            char why[96];
            DWORD raw = 0;
            if (tlobj::StFind(0, owner, key, hits, why, sizeof(why)) <= 0 || !tlobj::StRaw(hits[0], &raw)) return false;
            *flag = raw ? 1 : 0;
            return true;
        }
    }
    return false;
}
inline bool PzIsPortable(DWORD inst) {       // a native class 'portablebase' in the chain (chapel weights, poles)
    const DWORD so = tlobj::ScriptObj(inst);
    if (!so) return false;
    DWORD roots[16];
    const int depth = tlobj::ClassChain(so, roots, 16);
    for (int d = 0; d < depth; ++d) {
        char name[32];
        if (tlobj::RStr(tlobj::D(roots[d] + 0x10), name, sizeof(name)) && !strcmp(name, "portablebase")) return true;
    }
    return false;
}
inline bool PzNameHas(const char *name, const char *part) {
    char low[64];
    strncpy_s(low, sizeof(low), name, _TRUNCATE);
    _strlwr_s(low, sizeof(low));
    return strstr(low, part) != nullptr;
}
// the P4 behaviour of one uber graph (+ the "set node" records of X's command table for link): per DESC from its start
// node (+0x14); stable node = no way out on time / immediately / joint range; triggers = command / broadcast / event /
// set node; auto-reset = a stable node whose one trigger leads back to it on time / immediately alone (time summed);
// no reachable cycle = one-shot; two or more triggers = reversible; else the stable nodes on a cycle: >= 3 ring n,
// 2 toggle, 1 repeatable
enum { kPkUnknown = 0, kPkOneShot, kPkRing, kPkToggle, kPkRepeat, kPkReverse, kPkAuto };
// 0.22.57: link = the link of X the kind was read from (-1 = the instance's own graph); holdNode / holdSecs = for an
// auto-reset graph the node on the way back whose time condition is the longest (DLC 1 dlc_caverns_hall gates: "open",
// 25 s) - the node a timer hold keeps (-1 = none)
struct PzKind { int kind, n; float secs; int link, holdNode; float holdSecs; };
inline bool PzInternal(DWORD c) { return c == 1 || c == 3 || c == 9 || c == 11 || c == 12 || c == 14 || c == 15; }
inline PzKind PzClassify(DWORD b, DWORD x, int link) {
    PzKind r = {kPkUnknown, 0, 0.0f, link, -1, 0.0f};
    const int nn = tlobj::NodeCount(b);
    if (nn <= 0) return r;
    struct E { int from, to; DWORD cond, arg; };
    static E e[384];
    int en = 0;
    for (int k = 0; k < nn; ++k) {
        const DWORD node = tlobj::NodeAddr(b, k);
        for (int j = 0; node && j < tlobj::TransCount(node) && en < 384; ++j) {
            const DWORD t = tlobj::TransAt(node, j), to = tlobj::D(t + 4);
            if (t && to < static_cast<DWORD>(nn)) e[en++] = {k, static_cast<int>(to), tlobj::D(t + 0x18), tlobj::D(t + 0x1c)};
        }
    }
    for (int c = 0; x && link >= 0 && c < tlobj::CmdCount(x); ++c) {   // "set node v" records: an edge from every node
        DWORD rec = 0;
        int rn = 0;
        if (!tlobj::CmdRecords(x, c, &rec, &rn)) continue;
        for (int q = 0; q < rn; ++q) {
            const DWORD e0 = rec + 12u * static_cast<DWORD>(q), v = tlobj::D(e0 + 8);
            if (static_cast<int>(tlobj::D(e0)) != link || tlobj::D(e0 + 4) != 1 || v >= static_cast<DWORD>(nn)) continue;
            for (int k = 0; k < nn && en < 384; ++k) e[en++] = {k, static_cast<int>(v), 0x100, v};
        }
    }
    bool stable[64];
    static BYTE reach[64][64];
    memset(reach, 0, sizeof(reach));
    for (int k = 0; k < nn; ++k) stable[k] = true;
    for (int i = 0; i < en; ++i) {
        reach[e[i].from][e[i].to] = 1;
        if (e[i].cond == 1 || e[i].cond == 3 || e[i].cond == 14 || e[i].cond == 15) stable[e[i].from] = false;
    }
    for (int m = 0; m < nn; ++m)
        for (int i = 0; i < nn; ++i)
            if (reach[i][m])
                for (int j = 0; j < nn; ++j)
                    if (reach[m][j]) reach[i][j] = 1;
    DWORD start = tlobj::D(tlobj::D(b + 0x78) + 0x14);
    if (start >= static_cast<DWORD>(nn)) start = 0;
    bool inR[64];
    for (int k = 0; k < nn; ++k) inR[k] = k == static_cast<int>(start) || reach[start][k];
    DWORD keys[8];
    int kn = 0;
    bool cycle = false;
    for (int k = 0; k < nn; ++k) cycle = cycle || (inR[k] && reach[k][k]);
    for (int i = 0; i < en; ++i) {
        if (!inR[e[i].from] || PzInternal(e[i].cond)) continue;
        const DWORD key = (e[i].cond == 13 || e[i].cond == 16 || e[i].cond == 0x100) ? (e[i].cond << 16) ^ e[i].arg
                                                                                     : e[i].cond << 16;
        bool seen = false;
        for (int q = 0; q < kn; ++q) seen = seen || keys[q] == key;
        if (!seen && kn < 8) keys[kn++] = key;
    }
    // auto-reset: a stable node, one trigger out, back to it on time / immediately alone
    for (int i = 0; i < en; ++i) {
        const int s = e[i].from;
        if (!inR[s] || !stable[s] || PzInternal(e[i].cond)) continue;
        int u = e[i].to, hold = -1;
        float sum = 0.0f, longest = 0.0f;
        for (int step = 0; step < 16 && u != s; ++step) {
            int next = -1;
            for (int j = 0; j < en && next < 0; ++j)
                if (e[j].from == u && (e[j].cond == 1 || e[j].cond == 3)) {
                    next = e[j].to;
                    if (e[j].cond == 1) {
                        float f = 0.0f;
                        memcpy(&f, &e[j].arg, 4);
                        if (f > 0.0f && f < 1.0e5f) {
                            sum += f;
                            if (f > longest) { longest = f; hold = u; }   // 0.22.57: the node the timer hold keeps
                        }
                    }
                }
            if (next < 0) break;
            u = next;
        }
        if (u == s && e[i].to != s) {        // a trigger self-loop is no reset
            r.kind = kPkAuto;
            r.secs = sum;
            r.holdNode = hold;
            r.holdSecs = longest;
            return r;
        }
    }
    if (!cycle) { r.kind = kPkOneShot; return r; }
    if (kn >= 2) { r.kind = kPkReverse; return r; }
    int ring = 0;
    for (int k = 0; k < nn; ++k) ring += (inR[k] && reach[k][k] && stable[k]) ? 1 : 0;
    r.n = ring;
    r.kind = ring >= 3 ? kPkRing : ring == 2 ? kPkToggle : kPkRepeat;
    return r;
}
inline void PzKindText(const PzKind &k, bool de, char *o, size_t n) {
    switch (k.kind) {
    case kPkOneShot: _snprintf_s(o, n, _TRUNCATE, "%s", de ? "einmalig" : "one-shot"); break;
    case kPkRing: _snprintf_s(o, n, _TRUNCATE, de ? "Ring %d" : "ring %d", k.n); break;
    case kPkToggle: _snprintf_s(o, n, _TRUNCATE, "%s", de ? "Umschalter" : "toggle"); break;
    case kPkRepeat: _snprintf_s(o, n, _TRUNCATE, "%s", de ? "wiederholbar" : "repeatable"); break;
    case kPkReverse: _snprintf_s(o, n, _TRUNCATE, "%s", de ? "umkehrbar" : "reversible"); break;
    case kPkAuto:
        _snprintf_s(o, n, _TRUNCATE, de ? "setzt sich nach %.0f s zur\303\274ck" : "resets itself after %.0f s",
                    static_cast<double>(k.secs));
        break;
    default: _snprintf_s(o, n, _TRUNCATE, "%s", "?"); break;
    }
}
// the kind of a target instance: its own uber graph, or (multibody anchor) the links its single-record commands drive
// (the most frequent kind)
inline PzKind PzTargetKind(DWORD inst) {
    PzKind none = {kPkUnknown, 0, 0.0f, -1, -1, 0.0f};
    const DWORD b = tlobj::Uber(inst);
    if (b) return PzClassify(b, tlobj::MultiOfAny(inst), -1);
    const DWORD x = tlobj::Multi(inst);
    if (!x) return none;
    PzKind best = none;
    int votes[8] = {0};
    for (int c = 0; c < tlobj::CmdCount(x); ++c) {
        DWORD rec = 0;
        int rn = 0;
        if (!tlobj::CmdRecords(x, c, &rec, &rn) || rn != 1) continue;
        const int l = static_cast<int>(tlobj::D(rec));
        const DWORD lb = tlobj::Uber(tlobj::LinkInst(x, l));
        if (!lb) continue;
        const PzKind k = PzClassify(lb, x, l);
        if (k.kind > 0 && k.kind < 8 && ++votes[k.kind] > (best.kind ? votes[best.kind] : 0)) best = k;
    }
    return best;
}
// a motor-closed joint (0.22.56: hinge; 0.22.57: hinge or rail): limit bit on with lo < hi, motor on with a velocity
// != 0. v = the engine's value (hinge degrees taken over the 180 / -180 wrap, rail units), lo / hi the limits, perS the
// motor speed per second (TruLink 0.5: the motor velocity is per 1/30 s tick), end = the limit the motor drives to (the
// closed end), open = the other limit; part = the link the joint moves = joint record +8 (B), +4 (A) when B is the world
// (-1) - chapel shadow door hinge 1: A -1, B 2 = the turning pedestal (dump 26292)
struct PzDoor { DWORD joint, jrec; int index, type, part; float v, lo, hi, perS, end, open; };
inline bool PzDoorOf(DWORD x, int i, PzDoor *d) {
    memset(d, 0, sizeof(*d));
    DWORD flags = 0;
    float vel = 0.0f, lim[2] = {0.0f, 0.0f};
    if (!tlobj::JointAt(x, i, &d->jrec, &d->joint)) return false;
    d->type = tlobj::JointType(d->joint);
    if ((d->type != 1 && d->type != 3) || !tlobj::R32(d->joint + 0x174, &flags) || !(flags & 0x10) || !(flags & 2) ||
        !tlobj::RF(d->joint + 0x108, &vel) || !tlobj::RF(d->joint + 0xd8, &lim[0]) || !tlobj::RF(d->joint + 0xdc, &lim[1]) ||
        !(lim[0] < lim[1]) || fabsf(vel) < 1.0e-6f || !TlJointValue(d->joint, d->type, &d->v))
        return false;
    const float k = d->type == 1 ? tlobj::kRadToDeg : 1.0f;
    d->lo = lim[0] * k;
    d->hi = lim[1] * k;
    d->perS = vel * k * tlobj::kTicksPerSecond;
    if (d->type == 1) d->v = tlobj::HingeUnwrap(d->v, d->lo, d->hi);
    d->end = d->perS < 0.0f ? d->lo : d->hi;
    d->open = d->perS < 0.0f ? d->hi : d->lo;
    const LONG a = static_cast<LONG>(tlobj::D(d->jrec + 4)), b = static_cast<LONG>(tlobj::D(d->jrec + 8));
    d->part = b >= 0 && b < 64 ? b : a >= 0 && a < 64 ? a : -1;
    d->index = i;
    return true;
}
// open = farther than 5 degrees / 10 units from the closed end
inline bool PzDoorIsOpen(const PzDoor &d) { return fabsf(d.v - d.end) > (d.type == 1 ? 5.0f : 10.0f); }
// the hold target: 8 degrees / 20 units inside the open limit (live 16.11. K11b: 170 degrees with the upper limit ~178
// held; at the stop the hinge reads -180), at most the middle of the range
inline float PzDoorHoldTarget(const PzDoor &d) {
    const float in = d.type == 1 ? 8.0f : 20.0f, mid = (d.lo + d.hi) * 0.5f;
    const float t = d.open > d.end ? d.open - in : d.open + in;
    return d.open > d.end ? (t < mid ? mid : t) : (t > mid ? mid : t);
}
// the object check with the most entries of X's links (chapel: preSolve -> solved, all four on position_a)
struct PzCheck { int holder, n, link[16], want[16]; };
inline bool PzBestCheck(DWORD x, PzCheck *c) {
    memset(c, 0, sizeof(*c));
    c->holder = -1;
    for (int i = 0; i < tlobj::Links(x); ++i) {
        const DWORD b = tlobj::Uber(tlobj::LinkInst(x, i));
        for (int k = 0; b && k < tlobj::NodeCount(b); ++k) {
            const DWORD node = tlobj::NodeAddr(b, k);
            for (int j = 0; node && j < tlobj::TransCount(node); ++j) {
                const DWORD t = tlobj::TransAt(node, j);
                if (tlobj::D(t + 0x18) != 9) continue;
                const DWORD rec = tlobj::D(t + 0x1c), n = rec ? tlobj::D(rec + 4) : 0, e = rec ? tlobj::D(rec + 8) : 0;
                if (!e || n > 16 || static_cast<int>(n) <= c->n) continue;
                int m = 0;
                for (DWORD q = 0; q < n; ++q)
                    if (tlobj::D(e + 12 * q + 4) == 1) {
                        c->link[m] = static_cast<int>(tlobj::D(e + 12 * q));
                        c->want[m++] = static_cast<int>(tlobj::D(e + 12 * q + 8));
                    }
                if (m <= c->n) continue;
                c->n = m;
                c->holder = i;
            }
        }
    }
    return c->n > 0;
}
// steps along the trigger edges (the first non-internal transition of each node) from the link's node to want, -1 = no way
inline int PzSteps(DWORD lb, int want) {
    LONG u = static_cast<LONG>(tlobj::D(lb + 0x84));
    if (u < 0) return -1;
    for (int s = 0; s < 16; ++s) {
        if (u == want) return s;
        const DWORD node = tlobj::NodeAddr(lb, u);
        LONG next = -1;
        for (int j = 0; node && j < tlobj::TransCount(node) && next < 0; ++j) {
            const DWORD t = tlobj::TransAt(node, j);
            if (!PzInternal(tlobj::D(t + 0x18))) next = static_cast<LONG>(tlobj::D(t + 4));
        }
        if (next < 0) return -1;
        u = next;
    }
    return -1;
}
// the command entry that steps exactly this link: one record, message kind 2 (event) to it; -1 = none
inline int PzLinkCmd(DWORD x, int link) {
    for (int c = 0; c < tlobj::CmdCount(x); ++c) {
        DWORD rec = 0;
        int rn = 0;
        if (tlobj::CmdRecords(x, c, &rec, &rn) && rn == 1 && static_cast<int>(tlobj::D(rec)) == link && tlobj::D(rec + 4) == 2)
            return c;
    }
    return -1;
}

// ---- 0.22.57: switch -> command entry from the loaded scripts (the rule of tools/puzzle_switch_scan.py, ENGINE 9
// "Switch -> target, static (P4)", read from the relocated script data in memory instead of the files) ----
// Root (ScriptTypeStreamData, script_conv.py): +0x10 native name, +0x18 base (runtime ScriptType), +0x20 states,
// +0x2c members (20 B), +0x34 prototypes (28 B: +6 u16 vtable index), +0x38 functions (28 B: +0 Prototype*, +0xc
// locals (20 B members), +0x18 code), +0x40 the function per state; an array pointer holds its count at -4. Code: u32
// words op << 24 | operand, then the op's extra words (script_conv.Walk.EXTRA + op02 float); a call names its function by
// pointer (an entry of the called script's function array, or a prototype entry).
//   switch side: op0f N pushes member +N; an instanceref member holding the target's intro id followed by a call of
//   instanceref f6 / f7 binds it; the next call of a function / prototype of a class of the TARGET's chain runs that
//   function on the target (override by the prototype's vtable index first, most derived class first);
//   target side: an 'uberobjectcommand' member (op0f) / local (op09) pushed before a call of uberobjectbase f1 sends
//   command entry n = value word 1 of its init block {object id, n, 0}; script states (op04 n, op7d) and calls into
//   the chain are followed (depth 4).
inline bool &PzTrace() { static bool on = false; return on; }   // offline test: every decision through TlAdd
inline DWORD PzArr(DWORD field, DWORD *n) {          // array pointer + count at -4 (at most 4096)
    const DWORD p = tlobj::D(field);
    const DWORD c = p ? tlobj::D(p - 4) : 0;
    *n = p && c <= 4096 ? c : 0;
    return *n ? p : 0;
}
inline int PzExtra(DWORD op) {
    switch (op) {
    case 0x02: case 0x05: case 0x34: case 0x65: case 0x66: case 0x68: case 0x69: case 0x6a: case 0x6b: case 0x77: case 0x7e:
        return 1;
    case 0x67: return 2;
    default: return 0;
    }
}
inline DWORD PzBaseRoot(DWORD root) {                // the base class's root (0 = end)
    const DWORD t = tlobj::D(root + 0x18);
    return t && tlobj::D(t) == tlobj::kScriptTypeVt ? tlobj::D(t + 8) : 0;
}
// a member / local entry (20 B, as tlobj::MemberAt) and the root of its script type (instanceref, uberobjectcommand ...)
struct PzVar { DWORD tag, uni, init, typeRoot; WORD offset; };
inline bool PzVarAt(DWORD e, PzVar *v) {
    memset(v, 0, sizeof(*v));
    if (!tlobj::R32(e, &v->tag) || !tlobj::R32(e + 8, &v->uni) || !tlobj::R16(e + 0xc, &v->offset) || !tlobj::R32(e + 0x10, &v->init))
        return false;
    const DWORD bt = v->tag & 0xf;
    if ((bt == 0xa || bt == 0xb) && v->uni) {
        const DWORD st = (v->tag & 0x80) ? tlobj::D(v->uni) : v->uni;
        v->typeRoot = st && tlobj::D(st) == tlobj::kScriptTypeVt ? tlobj::D(st + 8) : 0;
    }
    return true;
}
inline bool PzRootIs(DWORD root, const char *native) {
    char name[32];
    return root && tlobj::RStr(tlobj::D(root + 0x10), name, sizeof(name)) && !strcmp(name, native);
}
// index of function entry ptr in the function array of the class named `native` in the chain of root (-1 = none)
inline int PzNativeFunc(DWORD root, const char *native, DWORD ptr) {
    for (int guard = 0; root && guard < 12; ++guard, root = PzBaseRoot(root)) {
        if (!PzRootIs(root, native)) continue;
        DWORD n = 0;
        const DWORD f = PzArr(root + 0x38, &n);
        return f && ptr >= f && ptr < f + 28 * n && (ptr - f) % 28 == 0 ? static_cast<int>((ptr - f) / 28) : -1;
    }
    return -1;
}
inline bool PzMemberOff(const DWORD *roots, int depth, DWORD off, PzVar *v) {
    for (int d = 0; d < depth; ++d) {
        DWORD n = 0;
        const DWORD m = PzArr(roots[d] + 0x2c, &n);
        for (DWORD k = 0; m && k < n && k < 256; ++k)
            if (PzVarAt(m + 20 * k, v) && v->offset == off) return true;
    }
    return false;
}
inline bool PzLocalOff(DWORD func, DWORD off, PzVar *v) {
    DWORD n = 0;
    const DWORD l = PzArr(func + 0xc, &n);
    for (DWORD k = 0; l && k < n && k < 256; ++k)
        if (PzVarAt(l + 20 * k, v) && v->offset == off) return true;
    return false;
}
// value word k of an init block (in memory {pointer to the next word, values ...}; a word > 0xffff = a u16 pair)
inline DWORD PzInitWord(DWORD init, int k) {
    DWORD p = tlobj::D(init);
    if (p != init + 4) p = init;
    const DWORD v = tlobj::D(p + 4u * static_cast<DWORD>(k));
    return v > 0xffff ? (v & 0xffff) : v;
}
// the function a call pointer names in a chain: a function entry of a class of it, or a prototype entry -> the
// function with the same vtable index (most derived first), else the function of that very prototype; *root = its class
inline DWORD PzFuncByPtr(const DWORD *roots, int depth, DWORD ptr, DWORD *root) {
    for (int d = 0; d < depth; ++d) {
        DWORD n = 0;
        const DWORD f = PzArr(roots[d] + 0x38, &n);
        if (f && ptr >= f && ptr < f + 28 * n && (ptr - f) % 28 == 0) { *root = roots[d]; return ptr; }
    }
    int pd = -1;
    for (int d = 0; d < depth && pd < 0; ++d) {
        DWORD n = 0;
        const DWORD p = PzArr(roots[d] + 0x34, &n);
        if (p && ptr >= p && ptr < p + 28 * n && (ptr - p) % 28 == 0) pd = d;
    }
    if (pd < 0) return 0;
    WORD vt = 0xffff;
    tlobj::R16(ptr + 6, &vt);
    for (int pass = 0; pass < 2; ++pass)
        for (int d = 0; d < depth; ++d) {
            DWORD n = 0, pn = 0;
            const DWORD f = PzArr(roots[d] + 0x38, &n), p = PzArr(roots[d] + 0x34, &pn);
            for (DWORD k = 0; f && k < n && k < 512; ++k) {
                const DWORD proto = tlobj::D(f + 28 * k);
                WORD pv = 0xffff;
                const bool mine = p && proto >= p && proto < p + 28 * pn;
                if (pass == 0 && vt != 0xffff && mine && tlobj::R16(proto + 6, &pv) && pv == vt && tlobj::D(f + 28 * k + 0x18)) {
                    *root = roots[d];
                    return f + 28 * k;
                }
                if (pass == 1 && proto == ptr && tlobj::D(f + 28 * k + 0x18)) { *root = roots[d]; return f + 28 * k; }
            }
        }
    return 0;
}
// the command entries a function of class root sends (target side, see above); returns the new count in out
inline int PzSends(const DWORD *roots, int depth, DWORD root, DWORD func, int *out, int n, int max, int level) {
    if (!func || level > 4 || n >= max) return n;
    DWORD cn = 0;
    const DWORD code = PzArr(func + 0x18, &cn);
    PzVar last = {};
    bool have = false;
    LONG num = -1;
    for (DWORD j = 0; code && j < cn && n < max;) {
        const DWORD w = tlobj::D(code + 4 * j), op = w >> 24, arg = w & 0xffffff;
        const int ex = PzExtra(op);
        if (op == 0x0f) have = PzMemberOff(roots, depth, arg, &last);
        else if (op == 0x09) have = PzLocalOff(func, arg, &last);
        else if (op == 0x04) num = static_cast<LONG>(arg);
        if (PzTrace()) {
            char tn[32] = "";
            if (have && last.typeRoot) tlobj::RStr(tlobj::D(last.typeRoot + 0x10), tn, sizeof(tn));
            TlAdd("    L%d f 0x%08lx @%lu op %02lx arg %lu ex %d%s%s\n", level, func, j, op, arg, ex, have ? " var " : "", tn);
        }
        else if (op == 0x7d) {                           // enter script state <num>: its function runs next
            DWORD sn = 0;
            PzArr(root + 0x20, &sn);
            const DWORD sf = tlobj::D(root + 0x40);
            for (DWORD k = 0; sf && k < sn && k < 64; ++k)
                if (num < 0 || static_cast<DWORD>(num) == k) n = PzSends(roots, depth, root, tlobj::D(sf + 4 * k), out, n, max, level + 1);
        }
        for (int q = 1; q <= ex && j + q < cn && n < max; ++q) {
            const DWORD p = tlobj::D(code + 4 * (j + q));
            if (PzTrace()) {
                DWORD fr0 = 0;
                TlAdd("       word 0x%08lx: uberobjectbase f %d, chain func 0x%08lx\n", p,
                      have && last.typeRoot ? PzNativeFunc(last.typeRoot, "uberobjectbase", p) : -9,
                      PzFuncByPtr(roots, depth, p, &fr0));
            }
            DWORD fr = 0;
            const DWORD f = PzFuncByPtr(roots, depth, p, &fr);
            const bool cmd = have && last.typeRoot && PzRootIs(last.typeRoot, "uberobjectcommand");
            // uberobjectbase f1: the class may sit in the target's own chain (chapel pillars) or in the member type's
            if (cmd && (PzNativeFunc(last.typeRoot, "uberobjectbase", p) == 1 ||
                        (f && f == p && PzRootIs(fr, "uberobjectbase") && PzNativeFunc(fr, "uberobjectbase", p) == 1))) {
                out[n++] = static_cast<int>(PzInitWord(last.init, 1));
                continue;
            }
            if (f && f != func) n = PzSends(roots, depth, fr, f, out, n, max, level + 1);
        }
        j += 1 + static_cast<DWORD>(ex);
    }
    return n;
}
// the object command entry switch instance sw sends to target instance tgt (-1 = none found), *calls = how many sends
// were found (several equal ones are one answer; different ones: the first, *calls tells)
inline int PzSwitchEntry(DWORD sw, DWORD tgt, int *calls) {
    *calls = 0;
    const DWORD so = tlobj::ScriptObj(sw), tso = tlobj::ScriptObj(tgt);
    if (!so || !tso) return -1;
    const DWORD data = tlobj::D(so + 0xc), want = tlobj::D(tgt + 0x58);
    DWORD roots[16], troots[16];
    const int depth = tlobj::ClassChain(so, roots, 16), tdepth = tlobj::ClassChain(tso, troots, 16);
    int out[8], n = 0;
    for (int d = 0; d < depth && !n; ++d) {
        DWORD fn = 0;
        const DWORD funcs = PzArr(roots[d] + 0x38, &fn);
        for (DWORD k = 0; funcs && k < fn && k < 512 && !n; ++k) {
            DWORD cn = 0;
            const DWORD code = PzArr(funcs + 28 * k + 0x18, &cn);
            bool ref = false, bound = false;
            PzVar irv = {};
            for (DWORD j = 0; code && j < cn && !n;) {
                const DWORD w = tlobj::D(code + 4 * j), op = w >> 24, arg = w & 0xffffff;
                const int ex = PzExtra(op);
                if (op == 0x00) ref = bound = false;
                if (op == 0x0f)
                    ref = PzMemberOff(roots, depth, arg, &irv) && PzRootIs(irv.typeRoot, "instanceref") &&
                          data && tlobj::D(data + arg) == want;
                if (PzTrace())
                    TlAdd("  sw d%d f%lu @%lu op %02lx arg %lu ex %d%s%s\n", d, k, j, op, arg, ex, ref ? " REF" : "", bound ? " BOUND" : "");
                for (int q = 1; q <= ex && j + q < cn && !n; ++q) {
                    const DWORD p = tlobj::D(code + 4 * (j + q));
                    if (PzTrace()) {
                        DWORD fr0 = 0;
                        TlAdd("     word 0x%08lx: ir-f %d, target func 0x%08lx\n", p,
                              irv.typeRoot ? PzNativeFunc(irv.typeRoot, "instanceref", p) : -9, PzFuncByPtr(troots, tdepth, p, &fr0));
                    }
                    if (ref) {
                        const int f = PzNativeFunc(irv.typeRoot, "instanceref", p);
                        if (f == 6 || f == 7) { bound = true; continue; }
                    }
                    if (!bound) continue;
                    DWORD fr = 0;
                    const DWORD f = PzFuncByPtr(troots, tdepth, p, &fr);
                    if (!f) continue;
                    n = PzSends(troots, tdepth, fr, f, out, 0, 8, 0);
                    bound = false;
                }
                j += 1 + static_cast<DWORD>(ex);
            }
        }
    }
    *calls = n;
    return n ? out[0] : -1;
}
// the single link an object command entry steps (one record, any kind) - -1 = none / several
inline int PzEntryLink(DWORD x, int entry) {
    DWORD rec = 0;
    int rn = 0;
    return entry >= 0 && tlobj::CmdRecords(x, entry, &rec, &rn) && rn == 1 ? static_cast<int>(tlobj::D(rec)) : -1;
}

}  // namespace pzcore
