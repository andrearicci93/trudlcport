// TruThorCoreTest.cpp - offline check of TruThorCore.h (TruMenu 0.22.68 B2 point 1: Thor pillar reach from the terrain
// faces). Not part of TruMenu.asi. Build (x86, the same compiler as Build-TruAsi.ps1):
//   cl /nologo /O2 /MT /W4 /EHsc TruThorCoreTest.cpp /Fe<out>\TruThorCoreTest.exe
// Usage:
//   TruThorCoreTest <input from work/b2_2011/thor_dump.py> [foot [step]]
// Runs the same raster / distance / flood / ledge rules as TruMenu's puzzle.thor on the faces of the unit file and
// checks the proven pillar spots ("Q" lines, A3 cross-check: the exit spot over ring W982, the artifact spot over ring
// NE981): each must be valid, reachable and inside the area of a ring whose next target is the named kind.
// Prints the same counts as work/a3_2011/reach_map.py (faces used, rise bands, valid / reachable cells).
// Exit code: 0 = every Q line passes, 1 = a Q line fails, 2 = usage / input error.
#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../TruThorCore.h"

namespace {
const char *const kKindName[3] = {"exit", "artA", "artB"};
int KindOf(const char *s) {
    for (int k = 0; k < 3; ++k)
        if (!strcmp(s, kKindName[k])) return k;
    return -1;
}
}  // namespace

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: TruThorCoreTest <thor_dump.txt> [foot [step]]\n");
        return 2;
    }
    FILE *f = fopen(argv[1], "rb");
    if (!f) { fprintf(stderr, "cannot open %s\n", argv[1]); return 2; }
    thorcore::Params P;
    P.foot = argc > 2 ? static_cast<float>(atof(argv[2])) : 290.0f;
    P.step = argc > 3 ? static_cast<float>(atof(argv[3])) : 10.0f;
    std::vector<thorcore::Face> faces;
    std::vector<thorcore::Ledge> ledges;
    float art[2][3] = {{0, 0, 0}, {0, 0, 0}};
    int arts = 0;
    std::vector<float> trig;
    struct Q { char name[32]; float x, y; int kind; };
    std::vector<Q> qs;
    float sx = 0, sy = 0, bx0 = 0, bx1 = 0, by0 = 0, by1 = 0;
    static char line[8192];
    while (fgets(line, sizeof(line), f)) {
        char *t = strtok(line, " \r\n");
        if (!t) continue;
        if (!strcmp(t, "P")) {
            strtok(nullptr, " "); P.floorZ = static_cast<float>(atof(strtok(nullptr, " ")));
            strtok(nullptr, " "); sx = static_cast<float>(atof(strtok(nullptr, " "))); sy = static_cast<float>(atof(strtok(nullptr, " ")));
            strtok(nullptr, " ");
            bx0 = static_cast<float>(atof(strtok(nullptr, " "))); bx1 = static_cast<float>(atof(strtok(nullptr, " ")));
            by0 = static_cast<float>(atof(strtok(nullptr, " "))); by1 = static_cast<float>(atof(strtok(nullptr, " \r\n")));
        } else if (!strcmp(t, "F")) {
            thorcore::Face fc;
            for (int k = 0; k < 9; ++k) { const char *v = strtok(nullptr, " \r\n"); fc.v[k] = v ? static_cast<float>(atof(v)) : 0.0f; }
            faces.push_back(fc);
        } else if (!strcmp(t, "L")) {
            thorcore::Ledge l;
            memset(&l, 0, sizeof(l));
            l.id = atoi(strtok(nullptr, " "));
            l.closed = atoi(strtok(nullptr, " ")) != 0;
            const int n = atoi(strtok(nullptr, " "));
            for (int i = 0; i < n; ++i) {
                float p[3];
                for (int c = 0; c < 3; ++c) { const char *v = strtok(nullptr, " \r\n"); p[c] = v ? static_cast<float>(atof(v)) : 0.0f; }
                if (l.n < thorcore::kMaxLedgePts) { memcpy(l.pts[l.n], p, sizeof(p)); ++l.n; }
            }
            // the bands TruMenu uses: collected 1700 .. 2800 above the floor, target 1700 .. 2200
            bool in = l.n >= 2, target = l.n >= 2;
            for (int i = 0; i < l.n; ++i) {
                const float rise = l.pts[i][2] - P.floorZ;
                in = in && rise >= 1700.0f && rise <= 2800.0f;
                target = target && rise >= 1700.0f && rise <= 2200.0f;
            }
            l.target = target;
            if (in) ledges.push_back(l);
        } else if (!strcmp(t, "A")) {
            strtok(nullptr, " ");
            if (arts < 2) {
                for (int c = 0; c < 3; ++c) art[arts][c] = static_cast<float>(atof(strtok(nullptr, " \r\n")));
                ++arts;
            }
        } else if (!strcmp(t, "T")) {
            strtok(nullptr, " ");
            for (int c = 0; c < 3; ++c) trig.push_back(static_cast<float>(atof(strtok(nullptr, " \r\n"))));
        } else if (!strcmp(t, "Q")) {
            Q q;
            strncpy(q.name, strtok(nullptr, " "), sizeof(q.name) - 1);
            q.name[sizeof(q.name) - 1] = 0;
            q.x = static_cast<float>(atof(strtok(nullptr, " ")));
            q.y = static_cast<float>(atof(strtok(nullptr, " ")));
            q.kind = KindOf(strtok(nullptr, " \r\n"));
            qs.push_back(q);
        }
    }
    fclose(f);
    if (faces.empty() || ledges.empty()) { fprintf(stderr, "no faces / ledges in %s\n", argv[1]); return 2; }
    char clog[1024] = "";
    thorcore::Classify(ledges, art, arts, trig.data(), static_cast<int>(trig.size() / 3), clog, sizeof(clog));
    printf("# ledges collected %d (classify: %s)\n", static_cast<int>(ledges.size()), clog[0] ? clog : "-");
    for (const thorcore::Ledge &l : ledges) {
        const char *k = l.kind >= 0 ? kKindName[l.kind] : "none";
        if (l.closed)
            printf("  ring %d z %.0f%s -> next %d (gap %.0f, rise %.0f) = %s\n", l.id, static_cast<double>(l.zmean),
                   l.target ? "" : " (not a target)", l.next >= 0 ? ledges[static_cast<size_t>(l.next)].id : -1,
                   static_cast<double>(l.nextGap), static_cast<double>(l.nextRise), k);
        else
            printf("  edge %d z %.0f%s gallery %d kind %s\n", l.id, static_cast<double>(l.zmean), l.target ? " target" : "",
                   ledges[static_cast<size_t>(l.gal)].id, k);
    }
    thorcore::Result R;
    if (!thorcore::Build(R, P, faces.data(), static_cast<int>(faces.size()), nullptr, 0, ledges, bx0, bx1, by0, by1, sx, sy)) {
        fprintf(stderr, "Build refused the grid\n");
        return 2;
    }
    printf("# %d faces sampled, grid %d x %d cells of %.0f u, floor %.1f, step %.0f, foot %.0f\n", R.facesUsed, R.nx, R.ny,
           static_cast<double>(P.cell), static_cast<double>(P.floorZ), static_cast<double>(P.step), static_cast<double>(P.foot));
    printf("# rise 0..2 %d, 2..6 %d, 6..10 %d, 10..20 %d, 20..40 %d, 40..100 %d, 100..300 %d, >300 %d, hole %d\n", R.hist[0],
           R.hist[1], R.hist[2], R.hist[3], R.hist[4], R.hist[5], R.hist[6], R.hist[7], R.hist[8]);
    int blocked = 0;
    for (unsigned char b : R.blocked) blocked += b;
    printf("# blocked %d, valid %d, reachable from (%.0f, %.0f) %d (%.2f M u2)\n", blocked, R.validN, static_cast<double>(sx),
           static_cast<double>(sy), R.reachN, static_cast<double>(R.reachN) * P.cell * P.cell / 1e6);
    for (size_t r = 0; r < R.rings.size(); ++r) {
        int cells = 0;
        float mn = 1e30f, at[2] = {0, 0};
        const thorcore::Ledge &l = ledges[static_cast<size_t>(R.rings[r])];
        for (size_t i = 0; i < R.ringMask.size(); ++i) {
            if (!((R.ringMask[i] >> r) & 1)) continue;
            ++cells;
            const float c[3] = {R.Cx(static_cast<int>(i)), R.Cy(static_cast<int>(i)), 0};
            const float d = thorcore::LedgeDist(l, c) - P.head;
            if (d < mn) { mn = d; at[0] = c[0]; at[1] = c[1]; }
        }
        printf("  area ring %d (-> %s): %d reachable cells, min D %.0f at (%.0f, %.0f)\n", l.id,
               l.kind >= 0 ? kKindName[l.kind] : "none", cells, static_cast<double>(cells ? mn : -1.0f),
               static_cast<double>(at[0]), static_cast<double>(at[1]));
    }
    int fails = 0;
    for (const Q &q : qs) {
        const int i = R.Index(q.x, q.y);
        const bool valid = i >= 0 && R.valid[static_cast<size_t>(i)], reach = i >= 0 && R.reach[static_cast<size_t>(i)];
        int hit = -1;
        float dmin = 1e30f;
        char in[256] = "";
        for (size_t r = 0; i >= 0 && r < R.rings.size(); ++r) {
            const thorcore::Ledge &l = ledges[static_cast<size_t>(R.rings[r])];
            const float c[3] = {q.x, q.y, 0};
            const float d = thorcore::LedgeDist(l, c) - P.head;
            const size_t u = strlen(in);
            _snprintf_s(in + u, sizeof(in) - u, _TRUNCATE, "%sring %d D %.0f%s", u ? ", " : "", l.id, static_cast<double>(d),
                        ((R.ringMask[static_cast<size_t>(i)] >> r) & 1) ? " (in)" : "");
            if (((R.ringMask[static_cast<size_t>(i)] >> r) & 1) && d < dmin) { dmin = d; hit = static_cast<int>(r); }
        }
        const int kind = hit >= 0 ? ledges[static_cast<size_t>(R.rings[static_cast<size_t>(hit)])].kind : -1;
        const bool pass = valid && reach && kind == q.kind;
        float bd = 0.0f;
        R.NearestBlocked(q.x, q.y, 900.0f, &bd);
        printf("probe %-6s (%.0f, %.0f): valid %d, reachable %d, distance to blocked %.0f (nearest %.0f), %s -> %s, want %s: %s\n",
               q.name, static_cast<double>(q.x), static_cast<double>(q.y), valid ? 1 : 0, reach ? 1 : 0,
               static_cast<double>(i >= 0 ? R.dist[static_cast<size_t>(i)] : -1.0f), static_cast<double>(bd), in,
               kind >= 0 ? kKindName[kind] : "none", q.kind >= 0 ? kKindName[q.kind] : "?", pass ? "PASS" : "FAIL");
        fails += pass ? 0 : 1;
    }
    printf("%s (%d of %d probes)\n", fails ? "FAIL" : "all pass", static_cast<int>(qs.size()) - fails, static_cast<int>(qs.size()));
    return fails ? 1 : 0;
}
