// TruLinkObjTest.exe - offline test of the TruLink 0.4 / 0.5 object decoders (TruLinkObj.h) on a full tru.exe minidump or
// the byte check rows against tru.exe itself. Read-only: the dump / exe is only read; no game, no process.
//
//   TruLinkObjTest.exe --dump tru.exe.N.dmp <command> [args]    decoders on the dump's memory
//   TruLinkObjTest.exe --exe tru.exe checks                      byte check rows against the exe file
// Commands: checks | near [metres] [filter] [max n] | info <id> | events <id> [all] | refs <id> | body <id> |
// joint <id> <index> | sticky <owner> <key> | puzzle <id> (TruMenu 0.22.56 TruPuzzleCore.h: switch base, plate flag,
// portable, graph kinds, the best object check with steps / commands, hinges) | swcmd <switch> <target> (TruMenu
// 0.22.57: the command entry the switch's script sends to the target, read from the loaded script data)
// (<id> as in TruLink: intro id, 0x<instance>, #<list index>, player). Joint values need the engine's getter: "n/a".
// Exit code 0 = ok, 1 = a check failed / error, 2 = usage.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include "../TruLinkObj.h"
#include "../../TruMenu/TruPuzzleCore.h"        // TruMenu 0.22.56 puzzle analysis (command 'puzzle <id>')

namespace {

struct Range { unsigned long long va, size, file; };
Range *g_ranges = nullptr;
int g_rangeCount = 0;
FILE *g_file = nullptr;

// a small page cache (file pages of 64 KB)
const DWORD kPage = 0x10000;
struct Page { long long index; BYTE data[kPage]; DWORD valid; unsigned age; };
Page g_pages[32];
unsigned g_clock = 0;

bool FileRead(unsigned long long offset, BYTE *out, DWORD length) {
    while (length) {
        const long long index = static_cast<long long>(offset / kPage);
        const DWORD at = static_cast<DWORD>(offset % kPage);
        Page *page = nullptr;
        for (Page &p : g_pages)
            if (p.index == index && p.valid) { page = &p; break; }
        if (!page) {
            page = &g_pages[0];
            for (Page &p : g_pages)
                if (!p.valid || p.age < page->age) page = &p;
            if (_fseeki64(g_file, index * static_cast<long long>(kPage), SEEK_SET)) return false;
            page->valid = static_cast<DWORD>(fread(page->data, 1, kPage, g_file));
            page->index = index;
            if (!page->valid) return false;
        }
        page->age = ++g_clock;
        DWORD n = kPage - at;
        if (n > length) n = length;
        if (at + n > page->valid) return false;
        memcpy(out, page->data + at, n);
        out += n;
        offset += n;
        length -= n;
    }
    return true;
}

}  // namespace

bool TlRead(DWORD address, void *out, DWORD length) {
    BYTE *dst = static_cast<BYTE *>(out);
    unsigned long long a = address;
    while (length) {
        int lo = 0, hi = g_rangeCount - 1, found = -1;
        while (lo <= hi) {                                     // ranges sorted by va
            const int mid = (lo + hi) / 2;
            if (g_ranges[mid].va <= a) { found = mid; lo = mid + 1; } else { hi = mid - 1; }
        }
        if (found < 0) return false;
        const Range &r = g_ranges[found];
        if (a >= r.va + r.size) return false;
        unsigned long long n = r.va + r.size - a;
        if (n > length) n = length;
        if (!FileRead(r.file + (a - r.va), dst, static_cast<DWORD>(n))) return false;
        dst += n;
        a += n;
        length -= static_cast<DWORD>(n);
    }
    return true;
}

void TlAdd(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vprintf(fmt, ap);
    va_end(ap);
}

bool TlJointValue(DWORD, int, float *) { return false; }   // the engine's getter is not available offline

namespace {

int CompareRange(const void *a, const void *b) {
    const Range *x = static_cast<const Range *>(a), *y = static_cast<const Range *>(b);
    return x->va < y->va ? -1 : x->va > y->va ? 1 : 0;
}

bool LoadDump(const char *path) {
    if (fopen_s(&g_file, path, "rb") || !g_file) { printf("err cannot open %s\n", path); return false; }
    DWORD head[4];
    if (fread(head, 4, 4, g_file) != 4 || head[0] != 0x504d444d) { printf("err %s is no minidump\n", path); return false; }
    const DWORD streams = head[2], dirRva = head[3];
    int capacity = 0;
    for (DWORD i = 0; i < streams; ++i) {
        DWORD e[3];
        _fseeki64(g_file, dirRva + 12ll * i, SEEK_SET);
        if (fread(e, 4, 3, g_file) != 3) return false;
        if (e[0] == 9) {                                       // Memory64ListStream
            unsigned long long count = 0, base = 0;
            _fseeki64(g_file, e[2], SEEK_SET);
            fread(&count, 8, 1, g_file);
            fread(&base, 8, 1, g_file);
            if (count > 1000000) return false;
            g_ranges = static_cast<Range *>(realloc(g_ranges, sizeof(Range) * (capacity += static_cast<int>(count))));
            unsigned long long file = base;
            for (unsigned long long k = 0; k < count; ++k) {
                unsigned long long d[2];
                fread(d, 8, 2, g_file);
                g_ranges[g_rangeCount++] = {d[0], d[1], file};
                file += d[1];
            }
        } else if (e[0] == 5) {                                // MemoryListStream
            DWORD count = 0;
            _fseeki64(g_file, e[2], SEEK_SET);
            fread(&count, 4, 1, g_file);
            if (count > 1000000) return false;
            g_ranges = static_cast<Range *>(realloc(g_ranges, sizeof(Range) * (capacity += static_cast<int>(count))));
            for (DWORD k = 0; k < count; ++k) {
                unsigned long long va = 0;
                DWORD sz[2];
                fread(&va, 8, 1, g_file);
                fread(sz, 4, 2, g_file);
                g_ranges[g_rangeCount++] = {va, sz[0], sz[1]};
            }
        }
    }
    qsort(g_ranges, static_cast<size_t>(g_rangeCount), sizeof(Range), CompareRange);
    unsigned long long total = 0;
    for (int i = 0; i < g_rangeCount; ++i) total += g_ranges[i].size;
    printf("# dump %s: %d memory ranges, %.1f MB\n", path, g_rangeCount, static_cast<double>(total) / 1048576.0);
    return g_rangeCount > 0;
}

// the exe's sections as ranges (va = image base + section rva), header included
bool LoadExe(const char *path) {
    if (fopen_s(&g_file, path, "rb") || !g_file) { printf("err cannot open %s\n", path); return false; }
    IMAGE_DOS_HEADER dos;
    IMAGE_NT_HEADERS32 nt;
    if (fread(&dos, sizeof(dos), 1, g_file) != 1 || dos.e_magic != IMAGE_DOS_SIGNATURE) return false;
    _fseeki64(g_file, dos.e_lfanew, SEEK_SET);
    if (fread(&nt, sizeof(nt), 1, g_file) != 1 || nt.Signature != IMAGE_NT_SIGNATURE) return false;
    const int n = nt.FileHeader.NumberOfSections;
    g_ranges = static_cast<Range *>(calloc(static_cast<size_t>(n) + 1, sizeof(Range)));
    const unsigned long long base = nt.OptionalHeader.ImageBase;
    g_ranges[g_rangeCount++] = {base, nt.OptionalHeader.SizeOfHeaders, 0};
    _fseeki64(g_file, dos.e_lfanew + 4 + sizeof(IMAGE_FILE_HEADER) + nt.FileHeader.SizeOfOptionalHeader, SEEK_SET);
    for (int i = 0; i < n; ++i) {
        IMAGE_SECTION_HEADER s;
        if (fread(&s, sizeof(s), 1, g_file) != 1) return false;
        g_ranges[g_rangeCount++] = {base + s.VirtualAddress, s.SizeOfRawData, s.PointerToRawData};
    }
    qsort(g_ranges, static_cast<size_t>(g_rangeCount), sizeof(Range), CompareRange);
    printf("# exe %s: image base 0x%08llx, %d sections\n", path, base, n);
    return true;
}

int Checks() {
    bool ok[tlobj::kGrpCount];
    int rows[tlobj::kGrpCount];
    DWORD first = 0;
    const int bad = tlobj::RunChecks(ok, &first, rows);
    for (int g = 0; g < tlobj::kGrpCount; ++g) printf("check group %-10s %2d rows: %s\n", tlobj::kGrpNames[g], rows[g], ok[g] ? "ok" : "MISMATCH");
    for (int i = 0; i < tlobj::kTlCheckCount; ++i) {
        BYTE want[96], have[96];
        const int n = tlobj::HexToBytes(tlobj::kTlChecks[i].hex, want, sizeof(want));
        const bool read = TlRead(tlobj::kTlChecks[i].at, have, static_cast<DWORD>(n));
        if (!read || memcmp(want, have, static_cast<size_t>(n))) {
            printf("  BAD 0x%08lx (%s) %s: ", tlobj::kTlChecks[i].at, tlobj::kGrpNames[tlobj::kTlChecks[i].group],
                   read ? "differs" : "not readable");
            for (int k = 0; read && k < n; ++k) printf("%02x", have[k]);
            printf("\n");
        }
    }
    printf("checks: %d rows, %d bad%s\n", tlobj::kTlCheckCount, bad, bad ? "" : " - all match");
    return bad ? 1 : 0;
}

DWORD Inst(const char *arg) {
    char why[128];
    const DWORD inst = tlobj::FindInst(arg, why, sizeof(why));
    if (!inst) printf("err %s\n", why);
    return inst;
}

}  // namespace

int main(int argc, char **argv) {
    if (argc < 4 || (strcmp(argv[1], "--dump") && strcmp(argv[1], "--exe"))) {
        printf("usage: TruLinkObjTest --dump <tru.dmp> checks | near [m] [filter] [max n] | info <id> | events <id> [all] | "
               "refs <id> | body <id> | joint <id> <index> | sticky <owner> <key>\n       TruLinkObjTest --exe <tru.exe> checks\n");
        return 2;
    }
    for (Page &p : g_pages) { p.index = -1; p.valid = 0; p.age = 0; }
    const bool dump = !strcmp(argv[1], "--dump");
    if (!(dump ? LoadDump(argv[2]) : LoadExe(argv[2]))) { printf("err cannot load %s\n", argv[2]); return 1; }
    const char *cmd = argv[3];
    if (!strcmp(cmd, "checks")) return Checks();
    if (!dump) { printf("err with --exe only 'checks'\n"); return 2; }
    if (!strcmp(cmd, "near")) {
        float metres = 10.0f;
        const char *filter = "";
        int max = 64;
        for (int i = 4; i < argc; ++i) {
            if (!strcmp(argv[i], "max") && i + 1 < argc) { max = atoi(argv[++i]); continue; }
            char *end = nullptr;
            const double v = strtod(argv[i], &end);
            if (end && !*end && i == 4) metres = static_cast<float>(v);
            else filter = argv[i];
        }
        tlobj::Near(metres * tlobj::kUnitsPerMetre, filter, max < 1 ? 1 : max > 400 ? 400 : max);
        return 0;
    }
    if (!strcmp(cmd, "info") && argc > 4) { const DWORD i = Inst(argv[4]); if (!i) return 1; tlobj::Info(i); return 0; }
    if (!strcmp(cmd, "events") && argc > 4) {
        const DWORD i = Inst(argv[4]);
        if (!i) return 1;
        tlobj::Events(i, argc > 5 && !strcmp(argv[5], "all"));
        return 0;
    }
    if (!strcmp(cmd, "refs") && argc > 4) { const DWORD i = Inst(argv[4]); if (!i) return 1; tlobj::Refs(i); return 0; }
    if (!strcmp(cmd, "swcmd") && argc > 5) {                   // TruMenu 0.22.57: switch -> command entry from the scripts
        const DWORD s = Inst(argv[4]), t = Inst(argv[5]);
        if (!s || !t) return 1;
        pzcore::PzTrace() = argc > 6 && !strcmp(argv[6], "trace");
        int calls = 0;
        const int e = pzcore::PzSwitchEntry(s, t, &calls);
        const DWORD x = tlobj::Multi(t);
        printf("swcmd %lu -> %lu: entry %d (%d send(s) found), link %d, used bit 0x200 %d\n", tlobj::D(s + 0x58),
               tlobj::D(t + 0x58), e, calls, x ? pzcore::PzEntryLink(x, e) : -1, pzcore::PzSwUsed(s) ? 1 : 0);
        return e >= 0 ? 0 : 1;
    }
    if (!strcmp(cmd, "puzzle") && argc > 4) {                  // TruMenu 0.22.56 TruPuzzleCore.h on the dump
        const DWORD i = Inst(argv[4]);
        if (!i) return 1;
        char name[64], kt[64];
        tlobj::InstName(i, name, sizeof(name));
        printf("puzzle %lu %s\n", tlobj::D(i + 0x58), name);
        pzcore::PzSw sw;
        if (pzcore::PzSwitchOf(i, &sw))
            printf("  switch base: +32 cur %ld, +16 off %ld, +20 on %ld, +24 disabled %ld -> state %d (0 off, 1 on, 2 "
                   "disabled, 3 other)\n", sw.cur, sw.off, sw.on, sw.dis, pzcore::PzSwState(sw));
        else printf("  switch base: none\n");
        int flag = -1;
        printf("  plate flag: %s %d\n", pzcore::PzPlateFlagRead(i, &flag) ? "read" : "none", flag);
        printf("  portable: %d, body 0x%08lx\n", pzcore::PzIsPortable(i) ? 1 : 0, tlobj::BodyOf(i));
        const pzcore::PzKind k = pzcore::PzTargetKind(i);
        pzcore::PzKindText(k, false, kt, sizeof(kt));
        printf("  target kind: %d (%s) n %d secs %.1f link %d hold node %d (%.1f s)\n", k.kind, kt, k.n,
               static_cast<double>(k.secs), k.link, k.holdNode, static_cast<double>(k.holdSecs));
        int open = -1;
        if (pzcore::PzOpenFlagRead(i, &open)) printf("  open flag (modifiable + stickybool class): %d\n", open);
        const DWORD x = tlobj::Multi(i);
        for (int l = 0; x && l < tlobj::Links(x); ++l) {
            const DWORD lb = tlobj::Uber(tlobj::LinkInst(x, l));
            if (!lb) continue;
            const pzcore::PzKind lk = pzcore::PzClassify(lb, x, l);
            pzcore::PzKindText(lk, false, kt, sizeof(kt));
            char node[48];
            tlobj::NodeName(lb, static_cast<LONG>(tlobj::D(lb + 0x84)), node, sizeof(node));
            printf("  link %d: node '%s', kind %s, steps-cmd %d\n", l, node, kt, pzcore::PzLinkCmd(x, l));
        }
        pzcore::PzCheck chk;
        if (x && pzcore::PzBestCheck(x, &chk)) {
            printf("  best object check: holder link %d, %d entries\n", chk.holder, chk.n);
            for (int q = 0; q < chk.n; ++q) {
                const DWORD lb = tlobj::Uber(tlobj::LinkInst(x, chk.link[q]));
                char now[48] = "-", want[48] = "-";
                if (lb) {
                    tlobj::NodeName(lb, static_cast<LONG>(tlobj::D(lb + 0x84)), now, sizeof(now));
                    tlobj::NodeName(lb, chk.want[q], want, sizeof(want));
                }
                printf("    link %d: now '%s' want '%s' steps %d via cmd %d\n", chk.link[q], now, want,
                       lb ? pzcore::PzSteps(lb, chk.want[q]) : -1, pzcore::PzLinkCmd(x, chk.link[q]));
            }
        }
        for (int j = 0; x && j < tlobj::JointCount(x); ++j) {
            DWORD jrec = 0, jt = 0, flags = 0;
            float vel = 0.0f, lim[2] = {0, 0};
            if (!tlobj::JointAt(x, j, &jrec, &jt) || tlobj::JointType(jt) != 1) continue;
            tlobj::R32(jt + 0x174, &flags);
            tlobj::RF(jt + 0x108, &vel);
            tlobj::RF(jt + 0xd8, &lim[0]);
            tlobj::RF(jt + 0xdc, &lim[1]);
            printf("  hinge %d: motor %s, limit %s [%.1f, %.1f] deg, motor %.3f deg/s (value: engine getter, n/a offline)\n", j,
                   (flags & 0x10) ? "on" : "off", (flags & 2) ? "on" : "off", static_cast<double>(lim[0] * tlobj::kRadToDeg),
                   static_cast<double>(lim[1] * tlobj::kRadToDeg),
                   static_cast<double>(vel * tlobj::kRadToDeg * tlobj::kTicksPerSecond));
        }
        return 0;
    }
    if (!strcmp(cmd, "body") && argc > 4) {
        const DWORD i = Inst(argv[4]);
        if (!i) return 1;
        if (!tlobj::D(i + 0x274)) { printf("no physics body (+0x274 = 0)\n"); return 0; }
        tlobj::BodyLine(i, "");
        // the instance pose the game derives from the body (0x497610: pos = body pos - R(body) x COM): check value
        float p[4], q[4], com[3], ip[3];
        TlRead(tlobj::D(i + 0x274) + 0x80, p, 16);
        TlRead(tlobj::D(i + 0x274) + 0x90, q, 16);
        TlRead(i + 0x250, com, 12);
        TlRead(i + 0x20, ip, 12);
        const double x = q[0], y = q[1], z = q[2], w = q[3];
        const double r[3][3] = {{1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)},
                                {2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)},
                                {2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)}};
        for (int k = 0; k < 2; ++k) {                          // column- and row-vector convention
            double o[3];
            for (int a = 0; a < 3; ++a)
                o[a] = p[a] - (k ? r[0][a] * com[0] + r[1][a] * com[1] + r[2][a] * com[2]
                                 : r[a][0] * com[0] + r[a][1] * com[1] + r[a][2] * com[2]);
            printf("body pos - R x COM (%s): %.2f %.2f %.2f; instance +0x20 %.2f %.2f %.2f\n", k ? "row vector" : "column vector",
                   o[0], o[1], o[2], static_cast<double>(ip[0]), static_cast<double>(ip[1]), static_cast<double>(ip[2]));
        }
        return 0;
    }
    if (!strcmp(cmd, "joint") && argc > 5) {
        const DWORD i = Inst(argv[4]);
        if (!i) return 1;
        const DWORD x = tlobj::MultiOfAny(i);
        if (!x) { printf("err no multibody object\n"); return 1; }
        tlobj::JointLine("", x, atoi(argv[5]));
        return 0;
    }
    if (!strcmp(cmd, "sticky") && argc > 5) {
        tlobj::StHit hits[3];
        char why[96];
        const int k = tlobj::StFind(0, strtoul(argv[4], nullptr, 0), static_cast<WORD>(strtoul(argv[5], nullptr, 0)), hits,
                                    why, sizeof(why));
        if (k < 0) { printf("err %s\n", why); return 1; }
        for (int i = 0; i < k; ++i) {
            DWORD raw = 0;
            char v[32] = "?";
            if (tlobj::StRaw(hits[i], &raw)) tlobj::StText(hits[i].type, raw, v, sizeof(v));
            printf("sticky 0:%s key %s = %s %s (index %lu)\n", argv[4], argv[5], tlobj::kStTypes[hits[i].type], v, hits[i].index);
        }
        if (!k) printf("no entry\n");
        return 0;
    }
    printf("err unknown command '%s'\n", cmd);
    return 2;
}
