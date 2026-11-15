// TruLinkObjTest.exe - offline test of the TruLink 0.4 object decoders (TruLinkObj.h) on a full tru.exe minidump or
// the byte check rows against tru.exe itself. Read-only: the dump / exe is only read; no game, no process.
//
//   TruLinkObjTest.exe --dump tru.exe.N.dmp <command> [args]    decoders on the dump's memory
//   TruLinkObjTest.exe --exe tru.exe checks                      byte check rows against the exe file
// Commands: checks | near [metres] [filter] [max n] | info <id> | events <id> | joint <id> <index> | sticky <owner> <key>
// (<id> as in TruLink: intro id, 0x<instance>, #<list index>, player). Joint values need the engine's getter: "n/a".
// Exit code 0 = ok, 1 = a check failed / error, 2 = usage.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include "../TruLinkObj.h"

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
        printf("usage: TruLinkObjTest --dump <tru.dmp> checks | near [m] [filter] [max n] | info <id> | events <id> | "
               "joint <id> <index> | sticky <owner> <key>\n       TruLinkObjTest --exe <tru.exe> checks\n");
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
    if (!strcmp(cmd, "events") && argc > 4) { const DWORD i = Inst(argv[4]); if (!i) return 1; tlobj::Events(i); return 0; }
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
