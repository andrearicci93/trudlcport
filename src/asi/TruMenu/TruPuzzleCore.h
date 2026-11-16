// TruPuzzleCore.h - TruMenu 0.22.56 "Raetsel in der Naehe": the pure-read puzzle analysis (switch base, plate flag,
// portable objects, P4 graph behaviour, object-check targets, ring steps, motor-closed hinges), shared by TruMenu.asi
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
struct PzKind { int kind, n; float secs; };
inline bool PzInternal(DWORD c) { return c == 1 || c == 3 || c == 9 || c == 11 || c == 12 || c == 14 || c == 15; }
inline PzKind PzClassify(DWORD b, DWORD x, int link) {
    PzKind r = {kPkUnknown, 0, 0.0f};
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
        int u = e[i].to;
        float sum = 0.0f;
        for (int step = 0; step < 16 && u != s; ++step) {
            int next = -1;
            for (int j = 0; j < en && next < 0; ++j)
                if (e[j].from == u && (e[j].cond == 1 || e[j].cond == 3)) {
                    next = e[j].to;
                    if (e[j].cond == 1) { float f = 0.0f; memcpy(&f, &e[j].arg, 4); if (f > 0.0f && f < 1.0e5f) sum += f; }
                }
            if (next < 0) break;
            u = next;
        }
        if (u == s && e[i].to != s) { r.kind = kPkAuto; r.secs = sum; return r; }   // a trigger self-loop is no reset
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
    PzKind none = {kPkUnknown, 0, 0.0f};
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
// a motor-closed hinge: limits on, motor on, velocity != 0; value (degrees, the engine's getter), limits in degrees,
// motor speed in degrees per second (TruLink 0.5: the motor velocity is per 1/30 s tick)
inline bool PzDoorJoint(DWORD x, int i, float *v, float *lo, float *hi, float *degPerS, DWORD *joint) {
    DWORD jrec = 0, j = 0, flags = 0;
    float vel = 0.0f, lim[2] = {0.0f, 0.0f};
    if (!tlobj::JointAt(x, i, &jrec, &j) || tlobj::JointType(j) != 1 || !tlobj::R32(j + 0x174, &flags) || !(flags & 0x10) ||
        !(flags & 2) || !tlobj::RF(j + 0x108, &vel) || !tlobj::RF(j + 0xd8, &lim[0]) || !tlobj::RF(j + 0xdc, &lim[1]) ||
        !(lim[0] < lim[1]) || fabsf(vel) < 1.0e-6f || !TlJointValue(j, 1, v))
        return false;
    *lo = lim[0] * tlobj::kRadToDeg;
    *hi = lim[1] * tlobj::kRadToDeg;
    *degPerS = vel * tlobj::kRadToDeg * tlobj::kTicksPerSecond;
    *joint = j;
    return true;
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

}  // namespace pzcore
