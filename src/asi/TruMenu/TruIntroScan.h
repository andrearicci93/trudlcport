// TruIntroScan.h - TruMenu 0.22.66 (T2 point 2): the level-start intro table built at run time from the game's own
// archives (patch.000 / bigfile.000 next to tru.exe), a port of tools/unit_intro_table.py (Q1b, ENGINE section 11
// "Level-start unit scripts and their intro objects"). Own code, read only: files only, no game memory, no game call.
//
// Per base unit <u> (the caller's list): pc-w\<u>.drm by its name hash (CRC-32 MSB first, poly 0x04c11db7, lower case;
// tools/names.py) in patch.000, then bigfile.000 (index: u32 n, n hashes, n records {size, offset, spec, clen}; data at
// offset << 11, split into <base>.%03d parts of 0x7ff00000 bytes; spec 0xffffffff = the language-neutral record;
// clen > 0 = one zlib stream), the CDRM container (tools/drm.py: u32 n at +8, n {u32 u, u32 c} at +16, blocks
// 16-aligned, (u & 0xff) == 2 = zlib), the DRM (24-byte header {ver, name size, pad size, -, -, n}, n sections of 20 B
// {size, u8 type, u8, u16, u32 packed (reloc bytes = packed >> 8), u32 id, u32 spec}, then per section the relocation
// blob and the data; blob = tools/drm_reloc.py: u32 counts[5], internal {off, target}, external u64 {si 14 bits,
// src / 4 24 bits, dst 26 bits}, id refs A, unknown, id refs (offset = (v & 0x1ffffff) << 2)).
//   placed intros = section 0's external pointer at src 0x74 -> intro section: u32 count +0xc, array +0x10 (internal),
//     0x90 B per intro, uid u32 +0x58 (puzzle_switch_scan.intros_of)
//   level-start scripts = the type-8 sections that hold "special fade-in case for cine"; per script the chain (root
//     +0x18 parent id, at most 8) gives the instanceref members (member 20 B: +8 type id (id ref, or an internal pointer
//     to one) whose script's native name (root +0x10) is "instanceref", +12 u16 offset, +16 init -> u32 intro id); in
//     each function (root +0x38, 28 B: +0x18 code, count at code - 4) the member read last (ops 0x0c .. 0x10 with that
//     offset) before a call (ops 0x65 .. 0x71) whose extra word points at a prototype (root +0x34, 28 B, u16 vt +6)
//     with vt 57 (3523 f0 PlayCinematic) is the intro played; extra words: tools/script_conv.Walk.EXTRA + op 0x02
//   own unit = the first unit whose placed intros hold that id (the file's rule)
// Scripts are looked up in the unit's DRM, then in generalbank.drm (tools/puzzle_switch_scan.Pool keeps every DRM read
// so far; the same id holds the same script - the selftest compares the result with the Python table).
#pragma once
#include <windows.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace truintro {

struct IntroRow { DWORD intro; char unit[48]; };
struct ScanStats {
    int units = 0, read = 0, missing = 0, faults = 0, scripts = 0, intros = 0, withoutOwn = 0;
    DWORD maxDrm = 0, maxKept = 0, ms = 0;   // the largest DRM (unpacked) and the most bytes kept of one
    char err[200] = "";
};

// ---------------------------------------------------------------- growable byte buffer
struct IsBuf { unsigned char *p = nullptr; size_t n = 0, cap = 0; };
inline void BufFree(IsBuf &b) { free(b.p); b.p = nullptr; b.n = b.cap = 0; }
inline bool BufReserve(IsBuf &b, size_t want) {
    if (want <= b.cap) return true;
    size_t c = b.cap ? b.cap : 4096;
    while (c < want) {
        if (c > (static_cast<size_t>(1) << 30)) return false;   // 1 GiB: no DRM is near it
        c *= 2;
    }
    unsigned char *q = static_cast<unsigned char *>(realloc(b.p, c));
    if (!q) return false;
    b.p = q;
    b.cap = c;
    return true;
}
inline bool BufAppend(IsBuf &b, const unsigned char *s, size_t n) {
    if (!BufReserve(b, b.n + n)) return false;
    memcpy(b.p + b.n, s, n);
    b.n += n;
    return true;
}
inline DWORD U32(const unsigned char *d, size_t len, size_t o, bool *ok = nullptr) {
    if (o + 4 > len || o + 4 < o) { if (ok) *ok = false; return 0; }
    return static_cast<DWORD>(d[o]) | static_cast<DWORD>(d[o + 1]) << 8 | static_cast<DWORD>(d[o + 2]) << 16 |
           static_cast<DWORD>(d[o + 3]) << 24;
}
inline WORD U16(const unsigned char *d, size_t len, size_t o) {
    return o + 2 <= len ? static_cast<WORD>(d[o] | d[o + 1] << 8) : static_cast<WORD>(0);
}

// ---------------------------------------------------------------- inflate (RFC 1951; the decoder of zlib's puff.c)
struct InfState { const unsigned char *in; size_t inLen, inPos; unsigned long bitBuf; int bitCnt; bool bad; IsBuf *out; };
struct InfHuff { short count[16]; short symbol[288]; };
inline int InfBits(InfState &s, int need) {
    unsigned long val = s.bitBuf;
    while (s.bitCnt < need) {
        if (s.inPos >= s.inLen) { s.bad = true; return 0; }
        val |= static_cast<unsigned long>(s.in[s.inPos++]) << s.bitCnt;
        s.bitCnt += 8;
    }
    s.bitBuf = val >> need;
    s.bitCnt -= need;
    return static_cast<int>(val & ((1UL << need) - 1));
}
inline int InfConstruct(InfHuff &h, const short *length, int n) {
    short offs[16];
    for (int len = 0; len <= 15; ++len) h.count[len] = 0;
    for (int sym = 0; sym < n; ++sym) ++h.count[length[sym]];
    if (h.count[0] == n) return 0;
    int left = 1;
    for (int len = 1; len <= 15; ++len) {
        left <<= 1;
        left -= h.count[len];
        if (left < 0) return left;
    }
    offs[1] = 0;
    for (int len = 1; len < 15; ++len) offs[len + 1] = static_cast<short>(offs[len] + h.count[len]);
    for (int sym = 0; sym < n; ++sym)
        if (length[sym] != 0) h.symbol[offs[length[sym]]++] = static_cast<short>(sym);
    return left;
}
inline int InfDecode(InfState &s, const InfHuff &h) {
    int code = 0, first = 0, index = 0;
    for (int len = 1; len <= 15; ++len) {
        code |= InfBits(s, 1);
        if (s.bad) return -1;
        const int count = h.count[len];
        if (code - count < first) return h.symbol[index + (code - first)];
        index += count;
        first += count;
        first <<= 1;
        code <<= 1;
    }
    return -10;
}
inline int InfStored(InfState &s) {
    s.bitBuf = 0;
    s.bitCnt = 0;
    if (s.inPos + 4 > s.inLen) return 2;
    unsigned len = s.in[s.inPos] | s.in[s.inPos + 1] << 8;
    const unsigned nlen = s.in[s.inPos + 2] | s.in[s.inPos + 3] << 8;
    s.inPos += 4;
    if ((len ^ 0xffffu) != nlen) return -2;
    if (s.inPos + len > s.inLen) return 2;
    if (!BufAppend(*s.out, s.in + s.inPos, len)) return -20;
    s.inPos += len;
    return 0;
}
inline int InfCodes(InfState &s, const InfHuff &lencode, const InfHuff &distcode) {
    static const short lens[29] = {3,  4,  5,  6,  7,  8,  9,  10, 11,  13,  15,  17,  19,  23, 27,
                                   31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258};
    static const short lext[29] = {0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0};
    static const short dists[30] = {1,   2,   3,   4,   5,   7,    9,    13,   17,   25,   33,   49,   65,    97,    129,
                                    193, 257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577};
    static const short dext[30] = {0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13};
    IsBuf &o = *s.out;
    int sym;
    do {
        sym = InfDecode(s, lencode);
        if (sym < 0) return sym;
        if (sym < 256) {
            if (!BufReserve(o, o.n + 1)) return -20;
            o.p[o.n++] = static_cast<unsigned char>(sym);
        } else if (sym > 256) {
            sym -= 257;
            if (sym >= 29) return -10;
            const size_t len = static_cast<size_t>(lens[sym] + InfBits(s, lext[sym]));
            const int ds = InfDecode(s, distcode);
            if (ds < 0 || ds >= 30) return ds < 0 ? ds : -10;
            const size_t dist = static_cast<size_t>(dists[ds] + InfBits(s, dext[ds]));
            if (s.bad) return -1;
            if (dist > o.n) return -11;
            if (!BufReserve(o, o.n + len)) return -20;
            for (size_t k = 0; k < len; ++k, ++o.n) o.p[o.n] = o.p[o.n - dist];
        }
    } while (sym != 256);
    return 0;
}
inline int InfFixed(InfState &s) {
    static InfHuff lencode, distcode;
    static bool built = false;               // built once; a race builds the same tables twice
    if (!built) {
        short lengths[288];
        int sym = 0;
        for (; sym < 144; ++sym) lengths[sym] = 8;
        for (; sym < 256; ++sym) lengths[sym] = 9;
        for (; sym < 280; ++sym) lengths[sym] = 7;
        for (; sym < 288; ++sym) lengths[sym] = 8;
        InfConstruct(lencode, lengths, 288);
        for (sym = 0; sym < 30; ++sym) lengths[sym] = 5;
        InfConstruct(distcode, lengths, 30);
        built = true;
    }
    return InfCodes(s, lencode, distcode);
}
inline int InfDynamic(InfState &s) {
    static const short order[19] = {16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15};
    short lengths[316];
    InfHuff lencode, distcode;
    const int nlen = InfBits(s, 5) + 257, ndist = InfBits(s, 5) + 1, ncode = InfBits(s, 4) + 4;
    if (s.bad) return -1;
    if (nlen > 286 || ndist > 30) return -3;
    int index = 0;
    for (; index < ncode; ++index) lengths[order[index]] = static_cast<short>(InfBits(s, 3));
    for (; index < 19; ++index) lengths[order[index]] = 0;
    if (s.bad) return -1;
    if (InfConstruct(lencode, lengths, 19) != 0) return -4;
    index = 0;
    while (index < nlen + ndist) {
        int sym = InfDecode(s, lencode);
        if (sym < 0) return sym;
        if (sym < 16) {
            lengths[index++] = static_cast<short>(sym);
        } else {
            short len = 0;
            if (sym == 16) {
                if (index == 0) return -5;
                len = lengths[index - 1];
                sym = 3 + InfBits(s, 2);
            } else if (sym == 17) {
                sym = 3 + InfBits(s, 3);
            } else {
                sym = 11 + InfBits(s, 7);
            }
            if (s.bad) return -1;
            if (index + sym > nlen + ndist) return -6;
            while (sym--) lengths[index++] = len;
        }
    }
    if (lengths[256] == 0) return -9;
    int err = InfConstruct(lencode, lengths, nlen);
    if (err && (err < 0 || nlen != lencode.count[0] + lencode.count[1])) return -7;
    err = InfConstruct(distcode, lengths + nlen, ndist);
    if (err && (err < 0 || ndist != distcode.count[0] + distcode.count[1])) return -8;
    return InfCodes(s, lencode, distcode);
}
// one zlib stream (RFC 1950 header, deflate blocks; the Adler-32 is not checked) appended to out; 0 = ok
inline int ZlibInflate(const unsigned char *src, size_t n, IsBuf &out) {
    if (n < 2 || (src[0] & 0x0f) != 8 || ((src[0] << 8) | src[1]) % 31 != 0 || (src[1] & 0x20)) return -30;
    InfState s = {src, n, 2, 0, 0, false, &out};
    int last = 0, err = 0;
    do {
        last = InfBits(s, 1);
        const int type = InfBits(s, 2);
        if (s.bad) return -1;
        err = type == 0 ? InfStored(s) : type == 1 ? InfFixed(s) : type == 2 ? InfDynamic(s) : -31;
        if (err) return err;
    } while (!last);
    return 0;
}

// ---------------------------------------------------------------- archives
inline DWORD NameHash(const char *s) {
    DWORD h = 0xffffffffUL;
    for (; *s; ++s) {
        h ^= static_cast<DWORD>(static_cast<unsigned char>(tolower(static_cast<unsigned char>(*s)))) << 24;
        for (int k = 0; k < 8; ++k) h = (h & 0x80000000UL) ? (h << 1) ^ 0x04c11db7UL : h << 1;
    }
    return ~h;
}
struct ArcRec { DWORD size, offset, spec; LONG clen; };
struct Archive { char base[MAX_PATH] = ""; DWORD n = 0; DWORD *hashes = nullptr; ArcRec *recs = nullptr; };
inline void ArcFree(Archive &a) { free(a.hashes); free(a.recs); a.hashes = nullptr; a.recs = nullptr; a.n = 0; }
inline bool ReadAt(const char *path, unsigned long long off, void *dst, DWORD n) {
    HANDLE f = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr, OPEN_EXISTING,
                           FILE_ATTRIBUTE_NORMAL, nullptr);
    if (f == INVALID_HANDLE_VALUE) return false;
    LARGE_INTEGER li;
    li.QuadPart = static_cast<LONGLONG>(off);
    DWORD got = 0;
    const bool ok = SetFilePointerEx(f, li, nullptr, FILE_BEGIN) && ReadFile(f, dst, n, &got, nullptr) && got == n;
    CloseHandle(f);
    return ok;
}
// path = "<dir>patch.000"; false = no file / no sane index
inline bool ArcOpen(Archive &a, const char *path) {
    DWORD n = 0;
    if (!ReadAt(path, 0, &n, 4) || !n || n > 1000000) return false;
    a.hashes = static_cast<DWORD *>(malloc(4 * static_cast<size_t>(n)));
    a.recs = static_cast<ArcRec *>(malloc(sizeof(ArcRec) * static_cast<size_t>(n)));
    if (!a.hashes || !a.recs || !ReadAt(path, 4, a.hashes, 4 * n) || !ReadAt(path, 4 + 4ULL * n, a.recs, 16 * n)) {
        ArcFree(a);
        return false;
    }
    a.n = n;
    strncpy_s(a.base, sizeof(a.base), path, _TRUNCATE);
    const size_t len = strlen(a.base);
    if (len > 4) a.base[len - 4] = 0;        // "<dir>patch" - parts are <base>.000, .001, ..
    return true;
}
// the language-neutral record of hash h into out (raw, or the inflated stream when clen > 0); 0 = none, -1 = fault
inline int ArcRead(const Archive &a, DWORD h, IsBuf &out) {
    for (DWORD k = 0; k < a.n; ++k) {
        if (a.hashes[k] != h || a.recs[k].spec != 0xffffffffUL) continue;
        const ArcRec &r = a.recs[k];
        const unsigned long long pos = static_cast<unsigned long long>(r.offset) << 11;
        const unsigned long long part = pos / 0x7ff00000ULL, off = pos % 0x7ff00000ULL;
        char path[MAX_PATH];
        _snprintf_s(path, sizeof(path), _TRUNCATE, "%s.%03u", a.base, static_cast<unsigned>(part));
        const DWORD n = r.clen > 0 ? static_cast<DWORD>(r.clen) : r.size;
        if (n > (1UL << 29)) return -1;
        out.n = 0;
        if (r.clen > 0) {
            IsBuf z;
            if (!BufReserve(z, n) || !ReadAt(path, off, z.p, n)) { BufFree(z); return -1; }
            z.n = n;
            const bool ok = BufReserve(out, r.size) && ZlibInflate(z.p, z.n, out) == 0;
            BufFree(z);
            return ok ? 1 : -1;
        }
        if (!BufReserve(out, n) || !ReadAt(path, off, out.p, n)) return -1;
        out.n = n;
        return 1;
    }
    return 0;
}
// CDRM container -> the DRM bytes (a plain DRM is copied); false = broken
inline bool CdrmDecode(const IsBuf &in, IsBuf &out) {
    out.n = 0;
    if (in.n < 16 || memcmp(in.p, "CDRM", 4) != 0) return BufAppend(out, in.p, in.n);
    const DWORD n = U32(in.p, in.n, 8);
    if (n > 100000 || 16 + 8ULL * n > in.n) return false;
    size_t pos = (16 + 8 * static_cast<size_t>(n) + 15) & ~static_cast<size_t>(15);
    for (DWORD k = 0; k < n; ++k) {
        const DWORD u = U32(in.p, in.n, 16 + 8 * k), c = U32(in.p, in.n, 20 + 8 * k);
        if (pos + c > in.n) return false;
        if ((u & 0xff) == 2) {
            if (!BufReserve(out, out.n + (u >> 8)) || ZlibInflate(in.p + pos, c, out) != 0) return false;
        } else if (!BufAppend(out, in.p + pos, c)) {
            return false;
        }
        pos = (pos + c + 15) & ~static_cast<size_t>(15);
    }
    return true;
}

// ---------------------------------------------------------------- DRM sections, relocations, scripts
struct Sec { DWORD size, id, relocOff, relocLen, dataOff; BYTE type; };
struct Pair { DWORD off, tgt; };
struct Ext { DWORD src, si, dst; };
struct Rel { Pair *in = nullptr; DWORD nIn = 0; Ext *ex = nullptr; DWORD nEx = 0; DWORD *ids = nullptr; DWORD nIds = 0; };
inline void RelFree(Rel &r) { free(r.in); free(r.ex); free(r.ids); r = Rel(); }
inline int PairCmp(const void *a, const void *b) {
    const DWORD x = static_cast<const Pair *>(a)->off, y = static_cast<const Pair *>(b)->off;
    return x < y ? -1 : x > y ? 1 : 0;
}
inline int DwCmp(const void *a, const void *b) {
    const DWORD x = *static_cast<const DWORD *>(a), y = *static_cast<const DWORD *>(b);
    return x < y ? -1 : x > y ? 1 : 0;
}
inline bool RelParse(const unsigned char *b, DWORD len, Rel &r) {
    r = Rel();
    if (!len) return true;
    if (len < 20) return false;
    DWORD c[5];
    for (int k = 0; k < 5; ++k) c[k] = U32(b, len, 4 * static_cast<size_t>(k));
    const unsigned long long need = 20ULL + 8ULL * c[0] + 8ULL * c[1] + 4ULL * (static_cast<unsigned long long>(c[2]) + c[3] + c[4]);
    if (need != len) return false;
    size_t o = 20;
    r.in = static_cast<Pair *>(malloc(sizeof(Pair) * (c[0] + 1)));
    r.ex = static_cast<Ext *>(malloc(sizeof(Ext) * (c[1] + 1)));
    r.ids = static_cast<DWORD *>(malloc(4 * (static_cast<size_t>(c[2]) + c[4] + 1)));
    if (!r.in || !r.ex || !r.ids) { RelFree(r); return false; }
    for (DWORD k = 0; k < c[0]; ++k, o += 8) { r.in[k].off = U32(b, len, o); r.in[k].tgt = U32(b, len, o + 4); }
    r.nIn = c[0];
    for (DWORD k = 0; k < c[1]; ++k, o += 8) {
        const unsigned long long v = U32(b, len, o) | static_cast<unsigned long long>(U32(b, len, o + 4)) << 32;
        r.ex[k].si = static_cast<DWORD>(v & 0x3fff);
        r.ex[k].src = static_cast<DWORD>(((v >> 14) & 0xffffff) << 2);
        r.ex[k].dst = static_cast<DWORD>(v >> 38);
    }
    r.nEx = c[1];
    for (DWORD k = 0; k < c[2]; ++k, o += 4) r.ids[r.nIds++] = (U32(b, len, o) & 0x1ffffff) << 2;
    o += 4 * static_cast<size_t>(c[3]);
    for (DWORD k = 0; k < c[4]; ++k, o += 4) r.ids[r.nIds++] = (U32(b, len, o) & 0x1ffffff) << 2;
    qsort(r.in, r.nIn, sizeof(Pair), PairCmp);
    qsort(r.ids, r.nIds, sizeof(DWORD), DwCmp);
    return true;
}
inline bool RelInt(const Rel &r, DWORD off, DWORD *tgt) {   // internal pointer at off -> target offset
    DWORD lo = 0, hi = r.nIn;
    while (lo < hi) {
        const DWORD mid = (lo + hi) / 2;
        if (r.in[mid].off < off) lo = mid + 1;
        else hi = mid;
    }
    if (lo < r.nIn && r.in[lo].off == off) { *tgt = r.in[lo].tgt; return true; }
    return false;
}
inline bool RelId(const Rel &r, DWORD off) {
    return r.nIds && bsearch(&off, r.ids, r.nIds, sizeof(DWORD), DwCmp) != nullptr;
}
inline const Ext *RelExt(const Rel &r, DWORD src) {
    for (DWORD k = 0; k < r.nEx; ++k)
        if (r.ex[k].src == src) return &r.ex[k];
    return nullptr;
}

const int kCacheMax = 1024;
struct Drm;
struct Script {
    DWORD id = 0, n = 0, parent = 0, memT = 0, memN = 0, protoT = 0, protoN = 0, funcT = 0, funcN = 0;
    bool hasParent = false;
    const unsigned char *d = nullptr;
    const char *native = nullptr;
    Rel rel;
    Drm *owner = nullptr;
};
struct Drm {
    IsBuf raw;
    Sec *secs = nullptr;
    DWORD nSecs = 0;
    Script *cache[kCacheMax] = {};           // parsed scripts of this DRM (looked-up ids only)
    int nCache = 0;
};
inline void DrmFree(Drm &m) {
    for (int k = 0; k < m.nCache; ++k) { RelFree(m.cache[k]->rel); delete m.cache[k]; }
    free(m.secs);
    BufFree(m.raw);
    m = Drm();
}
inline bool DrmParse(Drm &m) {
    const unsigned char *d = m.raw.p;
    const size_t len = m.raw.n;
    if (len < 24) return false;
    const DWORD namesz = U32(d, len, 4), padsz = U32(d, len, 8), n = U32(d, len, 20);
    if (n > 65536 || 24 + 20ULL * n + namesz + padsz > len) return false;
    m.secs = static_cast<Sec *>(malloc(sizeof(Sec) * (n + 1)));
    if (!m.secs) return false;
    size_t p = 24;
    for (DWORD k = 0; k < n; ++k, p += 20) {
        Sec &s = m.secs[k];
        s.size = U32(d, len, p);
        s.type = d[p + 4];
        s.relocLen = U32(d, len, p + 8) >> 8;
        s.id = U32(d, len, p + 12);
    }
    p += static_cast<size_t>(namesz) + padsz;
    for (DWORD k = 0; k < n; ++k) {
        Sec &s = m.secs[k];
        s.relocOff = static_cast<DWORD>(p);
        p += s.relocLen;
        s.dataOff = static_cast<DWORD>(p);
        p += s.size;
        if (p > len) return false;
    }
    m.nSecs = n;
    return true;
}
inline Script *DrmScript(Drm &m, DWORD id) {    // the type-8 section id of m, parsed once; nullptr = not in m
    for (int k = 0; k < m.nCache; ++k)
        if (m.cache[k]->id == id) return m.cache[k];
    for (DWORD k = 0; k < m.nSecs; ++k) {
        const Sec &s = m.secs[k];
        if (s.type != 8 || s.id != id || !s.size) continue;
        if (m.nCache >= kCacheMax) return nullptr;
        Script *sc = new Script();
        sc->id = id;
        sc->d = m.raw.p + s.dataOff;
        sc->n = s.size;
        sc->owner = &m;
        if (!RelParse(m.raw.p + s.relocOff, s.relocLen, sc->rel)) sc->rel = Rel();
        DWORD t = 0;
        if (RelInt(sc->rel, 0x10, &t) && t < sc->n && memchr(sc->d + t, 0, sc->n - t))
            sc->native = reinterpret_cast<const char *>(sc->d + t);
        if (RelId(sc->rel, 0x18)) { sc->hasParent = true; sc->parent = U32(sc->d, sc->n, 0x18); }
        struct { DWORD root, size; DWORD *t, *cnt; } arr[3] = {
            {0x2c, 20, &sc->memT, &sc->memN}, {0x34, 28, &sc->protoT, &sc->protoN}, {0x38, 28, &sc->funcT, &sc->funcN}};
        for (auto &a : arr) {
            if (!RelInt(sc->rel, a.root, &t) || t < 4) continue;
            bool ok = true;
            const DWORD cnt = U32(sc->d, sc->n, t - 4, &ok);
            if (!ok || cnt > (1UL << 20) || t + static_cast<unsigned long long>(cnt) * a.size > sc->n) continue;
            *a.t = t;
            *a.cnt = cnt;
        }
        m.cache[m.nCache++] = sc;
        return sc;
    }
    return nullptr;
}
struct Pool { Drm *unit; Drm *gb; };
inline Script *PoolGet(const Pool &p, DWORD id) {
    Script *s = p.unit ? DrmScript(*p.unit, id) : nullptr;
    if (!s && p.gb) s = DrmScript(*p.gb, id);
    return s;
}
inline bool IsProto57(const Script &sc, DWORD off) {
    if (!sc.protoN || off < sc.protoT || (off - sc.protoT) % 28 || (off - sc.protoT) / 28 >= sc.protoN) return false;
    return U16(sc.d, sc.n, off + 6) == 57;
}
// the intros the level-start script sid plays (vt 57 after an instanceref member read); n = count written
inline int PlayedIntros(const Pool &pool, DWORD sid, DWORD *out, int maxOut) {
    Script *chain[8];
    int nc = 0;
    for (DWORD id = sid; nc < 8;) {
        Script *sc = PoolGet(pool, id);
        bool seen = false;
        for (int k = 0; k < nc; ++k) seen = seen || chain[k] == sc;
        if (!sc || seen) break;
        chain[nc++] = sc;
        if (!sc->hasParent || sc->parent == sc->id) break;
        id = sc->parent;
    }
    if (!nc) return 0;
    DWORD refOff[256], refVal[256];
    bool refOk[256];
    int nr = 0;
    for (int c = 0; c < nc; ++c) {
        const Script &sc = *chain[c];
        for (DWORD k = 0; k < sc.memN && nr < 256; ++k) {
            const DWORD a = sc.memT + 20 * k, off = U16(sc.d, sc.n, a + 12);
            DWORD tid = 0, t = 0, ini = 0;
            bool hasTid = false;
            if (RelId(sc.rel, a + 8)) { tid = U32(sc.d, sc.n, a + 8); hasTid = true; }
            else if (RelInt(sc.rel, a + 8, &t) && RelId(sc.rel, t)) { tid = U32(sc.d, sc.n, t); hasTid = true; }
            if (!hasTid) continue;
            Script *ts = PoolGet(pool, tid);
            if (!ts || !ts->native || strcmp(ts->native, "instanceref") != 0) continue;
            bool have = false;
            for (int q = 0; q < nr; ++q) have = have || refOff[q] == off;
            if (have) continue;
            // no init value / out of range = the Python ref None: the offset is taken (first in the chain wins) and a
            // read of it clears the last intro
            bool ok = RelInt(sc.rel, a + 16, &ini);
            DWORD val = ini, v = 0;
            if (ok) {
                RelInt(sc.rel, ini, &val);
                v = U32(sc.d, sc.n, val, &ok);
                if (v > 0xffff) v &= 0xffff;
            }
            refOff[nr] = off;
            refVal[nr] = v;
            refOk[nr] = ok;
            ++nr;
        }
    }
    static const BYTE kExtra[256] = {0, 0, 1, 0, 0, 1};   // op 0x02 (push float) / 0x05; the rest set below
    BYTE extra[256];
    memcpy(extra, kExtra, sizeof(extra));
    extra[0x34] = 1; extra[0x65] = 1; extra[0x66] = 1; extra[0x67] = 2; extra[0x68] = 1; extra[0x69] = 1;
    extra[0x6a] = 1; extra[0x6b] = 1; extra[0x77] = 1; extra[0x7e] = 1;
    const Script &sc = *chain[0];
    int no = 0;
    for (DWORD k = 0; k < sc.funcN; ++k) {
        const DWORD a = sc.funcT + 28 * k;
        DWORD ct = 0;
        if (!RelInt(sc.rel, a + 0x18, &ct) || ct < 4) continue;
        const DWORD nw = U32(sc.d, sc.n, ct - 4);
        bool hasLast = false;
        DWORD last = 0;
        for (DWORD j = 0; j < nw;) {
            const DWORD o = ct + 4 * j;
            bool ok = true;
            const DWORD w = U32(sc.d, sc.n, o, &ok);
            if (!ok) break;
            const DWORD op = w >> 24, arg = w & 0xffffff;
            const DWORD ex = extra[op];
            if (op >= 0x0c && op <= 0x10)
                for (int q = 0; q < nr; ++q)
                    if (refOff[q] == arg) { last = refVal[q]; hasLast = refOk[q]; break; }
            if (op >= 0x65 && op <= 0x71) {
                for (DWORD q = 1; q <= ex; ++q) {
                    const DWORD x = o + 4 * q;
                    DWORD tt = 0;
                    bool hit = false;
                    if (RelInt(sc.rel, x, &tt)) {
                        hit = IsProto57(sc, tt);
                    } else if (const Ext *e = RelExt(sc.rel, x)) {
                        Drm &own = *sc.owner;
                        if (e->si < own.nSecs && own.secs[e->si].type == 8) {
                            Script *T = PoolGet(pool, own.secs[e->si].id);
                            hit = T && IsProto57(*T, e->dst);
                        }
                    }
                    if (hit && hasLast && no < maxOut) out[no++] = last;
                }
            }
            j += 1 + ex;
        }
    }
    return no;
}
// placed intro uids of a unit DRM (puzzle_switch_scan.intros_of); n written, -1 = no intro section
inline int PlacedIntros(Drm &m, DWORD *out, int maxOut) {
    if (!m.nSecs) return -1;
    Rel r0;
    if (!RelParse(m.raw.p + m.secs[0].relocOff, m.secs[0].relocLen, r0)) return -1;
    DWORD si = 0xffffffffUL;
    for (DWORD k = 0; k < r0.nEx && si == 0xffffffffUL; ++k)
        if (r0.ex[k].src == 0x74) si = r0.ex[k].si;
    RelFree(r0);
    if (si >= m.nSecs) return -1;
    const Sec &s = m.secs[si];
    Rel r;
    if (!RelParse(m.raw.p + s.relocOff, s.relocLen, r)) return -1;
    const unsigned char *d = m.raw.p + s.dataOff;
    DWORD a = 0;
    const bool ok = RelInt(r, 0x10, &a) && s.size >= 0x14;
    RelFree(r);
    if (!ok) return -1;
    const DWORD n = U32(d, s.size, 0xc);
    int no = 0;
    for (DWORD k = 0; k < n && k < 8192 && no < maxOut; ++k) {
        const unsigned long long o = a + 0x90ULL * k;
        if (o + 0x90 > s.size) break;
        out[no++] = U32(d, s.size, static_cast<size_t>(o) + 0x58);
    }
    return no;
}
// ---- lean DRM read: only section 0, the scripts (type 8) and the intro section are kept; a CDRM block that holds none
// of their bytes is not even read (a unit DRM is up to 105 MB, its scripts a few MB). Block sizes: zlib blocks
// u >> 8 (checked against every inflated block - a mismatch fails the unit), stored blocks c.
struct Blk { DWORD pos, c, uoff, usize; BYTE type; };
inline bool FileRead(HANDLE f, unsigned long long off, void *dst, DWORD n) {
    LARGE_INTEGER li;
    li.QuadPart = static_cast<LONGLONG>(off);
    DWORD got = 0;
    return SetFilePointerEx(f, li, nullptr, FILE_BEGIN) && ReadFile(f, dst, n, &got, nullptr) && got == n;
}
inline bool BlkDecode(HANDLE f, unsigned long long base, const Blk &b, IsBuf &z, IsBuf &out) {
    out.n = 0;
    z.n = 0;
    if (!BufReserve(z, b.c ? b.c : 1) || !FileRead(f, base + b.pos, z.p, b.c)) return false;
    z.n = b.c;
    if (b.type != 2) return BufAppend(out, z.p, z.n);
    return BufReserve(out, b.usize) && ZlibInflate(z.p, z.n, out) == 0 && out.n == b.usize;
}
inline bool LeanCdrm(HANDLE f, unsigned long long base, DWORD recSize, Drm &m, ScanStats &st) {
    unsigned char head[16];
    if (recSize < 16 || !FileRead(f, base, head, 16)) return false;
    const DWORD nb = U32(head, 16, 8);
    if (nb == 0 || nb > 200000 || 16 + 8ULL * nb > recSize) return false;
    Blk *blk = static_cast<Blk *>(malloc(sizeof(Blk) * nb));
    unsigned char *tab = static_cast<unsigned char *>(malloc(8 * static_cast<size_t>(nb)));
    IsBuf prefix, z, tmp;
    Sec *secs = nullptr;
    bool ok = blk && tab && FileRead(f, base + 16, tab, 8 * nb);
    unsigned long long pos = (16 + 8ULL * nb + 15) & ~15ULL, total = 0;
    for (DWORD k = 0; ok && k < nb; ++k) {
        const DWORD u = U32(tab, 8 * static_cast<size_t>(nb), 8 * k), c = U32(tab, 8 * static_cast<size_t>(nb), 8 * k + 4);
        blk[k].type = static_cast<BYTE>(u & 0xff);
        blk[k].c = c;
        blk[k].pos = static_cast<DWORD>(pos);
        blk[k].usize = blk[k].type == 2 ? u >> 8 : c;
        blk[k].uoff = static_cast<DWORD>(total);
        ok = pos + c <= recSize && total + blk[k].usize < 0xffffffffULL;
        total += blk[k].usize;
        pos = (pos + c + 15) & ~15ULL;
    }
    // pass 1: whole blocks from the start until the header, the section table and section 0's relocations are in
    DWORD nSecs = 0, nextBlk = 0, introSi = 0xffffffffUL;
    size_t need = 24;
    bool table = false;
    while (ok) {
        while (ok && prefix.n < need && nextBlk < nb) {
            ok = BlkDecode(f, base, blk[nextBlk++], z, tmp) && BufAppend(prefix, tmp.p, tmp.n);
        }
        if (!ok || prefix.n < need) { ok = false; break; }
        if (!table) {
            const DWORD namesz = U32(prefix.p, prefix.n, 4), padsz = U32(prefix.p, prefix.n, 8);
            nSecs = U32(prefix.p, prefix.n, 20);
            if (nSecs == 0 || nSecs > 65536 || namesz > (1UL << 24) || padsz > (1UL << 24)) { ok = false; break; }
            const size_t tabEnd = 24 + 20 * static_cast<size_t>(nSecs) + namesz + padsz;
            if (prefix.n < tabEnd) { need = tabEnd; continue; }
            secs = static_cast<Sec *>(malloc(sizeof(Sec) * nSecs));
            if (!secs) { ok = false; break; }
            size_t p = 24;
            for (DWORD k = 0; k < nSecs; ++k, p += 20) {
                secs[k].size = U32(prefix.p, prefix.n, p);
                secs[k].type = prefix.p[p + 4];
                secs[k].relocLen = U32(prefix.p, prefix.n, p + 8) >> 8;
                secs[k].id = U32(prefix.p, prefix.n, p + 12);
            }
            unsigned long long q = tabEnd;
            for (DWORD k = 0; k < nSecs; ++k) {
                secs[k].relocOff = static_cast<DWORD>(q);
                q += secs[k].relocLen;
                secs[k].dataOff = static_cast<DWORD>(q);
                q += secs[k].size;
            }
            if (q > total) { ok = false; break; }
            table = true;
            need = static_cast<size_t>(secs[0].relocOff) + secs[0].relocLen;
            continue;
        }
        Rel r0;
        if (!RelParse(prefix.p + secs[0].relocOff, secs[0].relocLen, r0)) { ok = false; break; }
        for (DWORD k = 0; k < r0.nEx && introSi == 0xffffffffUL; ++k)
            if (r0.ex[k].src == 0x74) introSi = r0.ex[k].si;
        RelFree(r0);
        break;
    }
    // the kept sections, packed in section order
    size_t kept = 0;
    for (DWORD k = 0; ok && k < nSecs; ++k)
        if (k == 0 || k == introSi || secs[k].type == 8) kept += static_cast<size_t>(secs[k].relocLen) + secs[k].size;
    ok = ok && BufReserve(m.raw, kept ? kept : 1);
    DWORD *newOff = ok ? static_cast<DWORD *>(malloc(4 * static_cast<size_t>(nSecs))) : nullptr;
    ok = ok && newOff;
    if (ok) {
        size_t o = 0;
        for (DWORD k = 0; k < nSecs; ++k) {
            const bool want = k == 0 || k == introSi || secs[k].type == 8;
            newOff[k] = want ? static_cast<DWORD>(o) : 0xffffffffUL;
            if (want) o += static_cast<size_t>(secs[k].relocLen) + secs[k].size;
        }
        m.raw.n = kept;
    }
    // pass 2: every block that overlaps a kept section (from the prefix when it is there)
    DWORD from = 0;                          // the first kept section that can still overlap (sections are in order)
    for (DWORD b = 0; ok && b < nb; ++b) {
        const unsigned long long bs = blk[b].uoff, be = bs + blk[b].usize;
        while (from < nSecs && (newOff[from] == 0xffffffffUL ||
                                static_cast<unsigned long long>(secs[from].dataOff) + secs[from].size <= bs))
            ++from;
        bool any = false;
        for (DWORD k = from; k < nSecs && secs[k].relocOff < be && !any; ++k)
            any = newOff[k] != 0xffffffffUL && static_cast<unsigned long long>(secs[k].dataOff) + secs[k].size > bs &&
                  secs[k].relocLen + secs[k].size > 0;
        if (!any) continue;
        const unsigned char *src = nullptr;
        if (be <= prefix.n) {
            src = prefix.p + bs;
        } else {
            if (!BlkDecode(f, base, blk[b], z, tmp)) { ok = false; break; }
            src = tmp.p;
        }
        for (DWORD k = from; k < nSecs && secs[k].relocOff < be; ++k) {
            if (newOff[k] == 0xffffffffUL) continue;
            const unsigned long long s0 = secs[k].relocOff, s1 = static_cast<unsigned long long>(secs[k].dataOff) + secs[k].size;
            const unsigned long long a = s0 > bs ? s0 : bs, e = s1 < be ? s1 : be;
            if (a < e) memcpy(m.raw.p + newOff[k] + (a - s0), src + (a - bs), static_cast<size_t>(e - a));
        }
    }
    if (ok) {
        for (DWORD k = 0; k < nSecs; ++k) {
            if (newOff[k] == 0xffffffffUL) { secs[k].size = secs[k].relocLen = 0; secs[k].relocOff = secs[k].dataOff = 0; }
            else { secs[k].relocOff = newOff[k]; secs[k].dataOff = newOff[k] + secs[k].relocLen; }
        }
        m.secs = secs;
        m.nSecs = nSecs;
        secs = nullptr;
        if (total > st.maxDrm) st.maxDrm = static_cast<DWORD>(total);
        if (kept > st.maxKept) st.maxKept = static_cast<DWORD>(kept);
    }
    free(newOff);
    free(secs);
    free(blk);
    free(tab);
    BufFree(prefix);
    BufFree(z);
    BufFree(tmp);
    return ok;
}
inline bool LoadDrm(const Archive *arcs, int nArcs, const char *unit, Drm &m, ScanStats &st, int *found) {
    char name[96];
    _snprintf_s(name, sizeof(name), _TRUNCATE, "pc-w\\%s.drm", unit);
    const DWORD h = NameHash(name);
    *found = 0;
    for (int a = 0; a < nArcs; ++a) {
        for (DWORD k = 0; k < arcs[a].n; ++k) {
            if (arcs[a].hashes[k] != h || arcs[a].recs[k].spec != 0xffffffffUL) continue;
            *found = 1;
            const ArcRec &r = arcs[a].recs[k];
            if (r.clen > 0) {                // a zlib record: whole (not seen on PC; the plain way)
                IsBuf raw;
                const bool ok = ArcRead(arcs[a], h, raw) == 1 && CdrmDecode(raw, m.raw) && DrmParse(m);
                BufFree(raw);
                if (ok && m.raw.n > st.maxDrm) st.maxDrm = static_cast<DWORD>(m.raw.n);
                return ok;
            }
            const unsigned long long pos = static_cast<unsigned long long>(r.offset) << 11;
            char path[MAX_PATH];
            _snprintf_s(path, sizeof(path), _TRUNCATE, "%s.%03u", arcs[a].base, static_cast<unsigned>(pos / 0x7ff00000ULL));
            HANDLE f = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr, OPEN_EXISTING,
                                   FILE_FLAG_SEQUENTIAL_SCAN, nullptr);
            if (f == INVALID_HANDLE_VALUE) return false;
            const unsigned long long base = pos % 0x7ff00000ULL;
            char magic[4] = {};
            bool ok = FileRead(f, base, magic, 4);
            if (ok && memcmp(magic, "CDRM", 4) == 0) {
                ok = LeanCdrm(f, base, r.size, m, st);
            } else if (ok) {                 // a plain DRM: whole
                ok = BufReserve(m.raw, r.size ? r.size : 1) && FileRead(f, base, m.raw.p, r.size);
                if (ok) m.raw.n = r.size;
                ok = ok && DrmParse(m);
                if (ok && m.raw.n > st.maxDrm) st.maxDrm = static_cast<DWORD>(m.raw.n);
            }
            CloseHandle(f);
            return ok;
        }
    }
    return false;
}

// ---- TruMenu 0.22.69 (B4 point 1, chapter.cp): the checkpoints of every unit from the same files (a port of
// tools/unit_checkpoint_table.py) - placed intros whose object id is one of the caller's checkpoint objects (resolved by
// name in the game's object list: checkpoint, invis_checkpoint, dlc2_checkpoint, checkpoint_l1_going_*), with the
// unit-data position (+0x10, before FinishLoad) and section 0's vector Level+0x80 (FinishLoad 0x5d1cd0 subtracts it from
// every intro position, ENGINE 4.2 step 6). A unit is read from <dir>mods\<unit>.drm when that file exists (the DLC
// units, an own base-unit file), else from patch.000 / bigfile.000.
struct CpScanRow { DWORD intro; WORD obj; WORD unit; float pos[3]; float l80[3]; };
struct CpScanStats {
    int units = 0, read = 0, fromMods = 0, missing = 0, faults = 0, noIntros = 0, rows = 0, dropped = 0;
    DWORD ms = 0;
    char err[200] = "";
};
// a DRM file (CDRM container or a plain DRM) through the lean read; false = no file / broken
inline bool LoadDrmFile(const char *path, Drm &m, ScanStats &st, int *found) {
    *found = 0;
    HANDLE f = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr, OPEN_EXISTING,
                           FILE_FLAG_SEQUENTIAL_SCAN, nullptr);
    if (f == INVALID_HANDLE_VALUE) return false;
    *found = 1;
    LARGE_INTEGER size;
    char magic[4] = {};
    bool ok = GetFileSizeEx(f, &size) && size.QuadPart >= 24 && size.QuadPart < 0x7fffffffLL && FileRead(f, 0, magic, 4);
    if (ok && memcmp(magic, "CDRM", 4) == 0) {
        ok = LeanCdrm(f, 0, static_cast<DWORD>(size.QuadPart), m, st);
    } else if (ok) {
        const DWORD n = static_cast<DWORD>(size.QuadPart);
        ok = BufReserve(m.raw, n) && FileRead(f, 0, m.raw.p, n);
        if (ok) m.raw.n = n;
        ok = ok && DrmParse(m);
    }
    CloseHandle(f);
    return ok;
}
// the placed intros of a unit DRM with object id and position (puzzle_switch_scan.intros_of); -1 = no intro section
struct IntroRec { DWORD uid; WORD obj; float pos[3]; };
inline float F32(const unsigned char *d, size_t len, size_t o) {
    const DWORD v = U32(d, len, o);
    float f;
    memcpy(&f, &v, 4);
    return f;
}
inline int IntroRecords(Drm &m, IntroRec *out, int maxOut) {
    if (!m.nSecs) return -1;
    Rel r0;
    if (!RelParse(m.raw.p + m.secs[0].relocOff, m.secs[0].relocLen, r0)) return -1;
    DWORD si = 0xffffffffUL;
    for (DWORD k = 0; k < r0.nEx && si == 0xffffffffUL; ++k)
        if (r0.ex[k].src == 0x74) si = r0.ex[k].si;
    RelFree(r0);
    if (si >= m.nSecs) return -1;
    const Sec &s = m.secs[si];
    Rel r;
    if (!RelParse(m.raw.p + s.relocOff, s.relocLen, r)) return -1;
    const unsigned char *d = m.raw.p + s.dataOff;
    DWORD a = 0;
    const bool ok = RelInt(r, 0x10, &a) && s.size >= 0x14;
    RelFree(r);
    if (!ok) return -1;
    const DWORD n = U32(d, s.size, 0xc);
    int no = 0;
    for (DWORD k = 0; k < n && k < 8192 && no < maxOut; ++k) {
        const size_t o = static_cast<size_t>(a) + 0x90 * static_cast<size_t>(k);
        if (o + 0x90 > s.size) break;
        IntroRec &q = out[no++];
        q.uid = U32(d, s.size, o + 0x58);
        q.obj = U16(d, s.size, o + 0x50);
        for (int c = 0; c < 3; ++c) q.pos[c] = F32(d, s.size, o + 0x10 + 4 * static_cast<size_t>(c));
    }
    return no;
}
// rows for every unit of units (names without .drm); -1 = no archive and no mods folder (st.err), else the row count
inline int ScanCheckpoints(const char *gameDir, const char *const *units, int nUnits, const WORD *objs, int nObjs,
                           CpScanRow *rows, int maxRows, CpScanStats &cs) {
    const DWORD t0 = GetTickCount();
    Archive arcs[2];
    int nArcs = 0;
    const char *files[2] = {"patch.000", "bigfile.000"};
    for (const char *f : files) {
        char path[MAX_PATH];
        _snprintf_s(path, sizeof(path), _TRUNCATE, "%s%s", gameDir, f);
        if (ArcOpen(arcs[nArcs], path)) ++nArcs;
    }
    IntroRec *recs = static_cast<IntroRec *>(malloc(sizeof(IntroRec) * 8192));
    if (!recs) {
        for (int k = 0; k < nArcs; ++k) ArcFree(arcs[k]);
        _snprintf_s(cs.err, sizeof(cs.err), _TRUNCATE, "no memory for the intro list");
        return -1;
    }
    ScanStats st;
    int nr = 0;
    for (int u = 0; u < nUnits; ++u) {
        ++cs.units;
        Drm m;
        char path[MAX_PATH];
        _snprintf_s(path, sizeof(path), _TRUNCATE, "%smods\\%s.drm", gameDir, units[u]);
        int found = 0;
        bool ok = LoadDrmFile(path, m, st, &found);
        if (found) {
            if (ok) ++cs.fromMods;
        } else {
            ok = nArcs > 0 && LoadDrm(arcs, nArcs, units[u], m, st, &found);
        }
        if (!ok) {
            if (found) ++cs.faults;
            else ++cs.missing;
            DrmFree(m);
            continue;
        }
        ++cs.read;
        float l80[3] = {0.0f, 0.0f, 0.0f};
        if (m.nSecs && m.secs[0].size >= 0x8c)
            for (int c = 0; c < 3; ++c) l80[c] = F32(m.raw.p + m.secs[0].dataOff, m.secs[0].size, 0x80 + 4 * static_cast<size_t>(c));
        const int ni = IntroRecords(m, recs, 8192);
        if (ni < 0) ++cs.noIntros;
        for (int k = 0; k < ni; ++k) {
            bool cp = false;
            for (int q = 0; q < nObjs && !cp; ++q) cp = objs[q] && recs[k].obj == objs[q];
            if (!cp) continue;
            if (nr >= maxRows) { ++cs.dropped; continue; }
            CpScanRow &r = rows[nr++];
            r.intro = recs[k].uid;
            r.obj = recs[k].obj;
            r.unit = static_cast<WORD>(u);
            for (int c = 0; c < 3; ++c) { r.pos[c] = recs[k].pos[c]; r.l80[c] = l80[c]; }
        }
        DrmFree(m);
    }
    free(recs);
    for (int k = 0; k < nArcs; ++k) ArcFree(arcs[k]);
    cs.rows = nr;
    cs.ms = GetTickCount() - t0;
    if (!cs.read) {
        _snprintf_s(cs.err, sizeof(cs.err), _TRUNCATE, "no unit readable (%d archives, %d units listed)", nArcs, nUnits);
        return -1;
    }
    return nr;
}

// the table: rows of {intro, own unit} for the base units in units (names without .drm); -1 = no archive / no
// generalbank (st.err says which), else the number of rows (intros without an own unit are counted in st.withoutOwn)
inline int ScanIntros(const char *gameDir, const char *const *units, int nUnits, IntroRow *rows, int maxRows,
                      ScanStats &st) {
    const DWORD t0 = GetTickCount();
    Archive arcs[2];
    int nArcs = 0;
    const char *files[2] = {"patch.000", "bigfile.000"};    // tools/puzzle_switch_scan.PC_ARCH order
    for (const char *f : files) {
        char path[MAX_PATH];
        _snprintf_s(path, sizeof(path), _TRUNCATE, "%s%s", gameDir, f);
        if (ArcOpen(arcs[nArcs], path)) ++nArcs;
    }
    if (!nArcs) {
        _snprintf_s(st.err, sizeof(st.err), _TRUNCATE, "no patch.000 / bigfile.000 in %s", gameDir);
        return -1;
    }
    Drm gb;
    int found = 0;
    if (!LoadDrm(arcs, nArcs, "generalbank", gb, st, &found)) {
        _snprintf_s(st.err, sizeof(st.err), _TRUNCATE, "generalbank.drm %s", found ? "unreadable" : "not in the archives");
        DrmFree(gb);
        for (int k = 0; k < nArcs; ++k) ArcFree(arcs[k]);
        return -1;
    }
    struct Own { DWORD intro; int unit; };
    Own own[256];
    DWORD seen[256];
    int nOwn = 0, nSeen = 0;
    static const char kNeedle[] = "special fade-in case for cine";
    const size_t needleN = sizeof(kNeedle) - 1;
    DWORD *placed = static_cast<DWORD *>(malloc(4 * 8192));
    for (int u = 0; u < nUnits && placed; ++u) {
        ++st.units;
        Drm m;
        if (!LoadDrm(arcs, nArcs, units[u], m, st, &found)) {
            if (found) ++st.faults;
            else ++st.missing;
            DrmFree(m);
            continue;
        }
        ++st.read;
        const int np = PlacedIntros(m, placed, 8192);
        const Pool pool = {&m, &gb};
        for (DWORD k = 0; k < m.nSecs; ++k) {
            const Sec &s = m.secs[k];
            if (s.type != 8 || s.size < needleN) continue;
            const unsigned char *d = m.raw.p + s.dataOff;
            bool has = false;
            for (DWORD q = 0; q + needleN <= s.size && !has; ++q)
                has = d[q] == 's' && memcmp(d + q, kNeedle, needleN) == 0;
            if (!has) continue;
            ++st.scripts;
            DWORD hits[64];
            const int nh = PlayedIntros(pool, s.id, hits, 64);
            for (int h = 0; h < nh; ++h) {
                bool known = false;
                for (int q = 0; q < nSeen; ++q) known = known || seen[q] == hits[h];
                if (!known && nSeen < 256) seen[nSeen++] = hits[h];
                bool isPlaced = false;
                for (int q = 0; q < np && !isPlaced; ++q) isPlaced = placed[q] == hits[h];
                bool have = false;
                for (int q = 0; q < nOwn; ++q) have = have || own[q].intro == hits[h];
                if (isPlaced && !have && nOwn < 256) own[nOwn++] = {hits[h], u};   // the first own unit is kept
            }
        }
        DrmFree(m);
    }
    free(placed);
    DrmFree(gb);
    for (int k = 0; k < nArcs; ++k) ArcFree(arcs[k]);
    // sorted by intro id (the file's order)
    for (int a = 1; a < nOwn; ++a)
        for (int b = a; b > 0 && own[b - 1].intro > own[b].intro; --b) { const Own t = own[b]; own[b] = own[b - 1]; own[b - 1] = t; }
    int nr = 0;
    for (int k = 0; k < nOwn && nr < maxRows; ++k, ++nr) {
        rows[nr].intro = own[k].intro;
        strncpy_s(rows[nr].unit, sizeof(rows[nr].unit), units[own[k].unit], _TRUNCATE);
    }
    st.intros = nSeen;
    st.withoutOwn = nSeen - nOwn;
    st.ms = GetTickCount() - t0;
    return nr;
}

}   // namespace truintro
