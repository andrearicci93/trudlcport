// TruIntroScanTest.cpp - offline check of TruIntroScan.h (TruMenu 0.22.66 T2 point 2: the level-start intro table from
// the game's archives at run time). Not part of TruMenu.asi. Build (x86, the same compiler as Build-TruAsi.ps1):
//   cl /nologo /O2 /MT /W4 /EHsc TruIntroScanTest.cpp /Fe<out>\TruIntroScanTest.exe
// Usage:
//   TruIntroScanTest <game folder with patch.000 / bigfile.000, trailing \> <unit list (unitlist.txt form)> <out file>
// The unit list's "levels\..." lines are the base units (as tools/puzzle_switch_scan.Source and TruMenu's kUnits rows);
// the out file gets one line "<intro id> <own unit>" per intro (the TruMenu.unitintros.txt form) and a "# stats" line.
// work/t2_1911/intro_scan_compare.py compares it with the table of tools/unit_intro_table.py.
// Exit code: 0 = at least one intro, 1 = none, 2 = usage / scan error.
#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../TruIntroScan.h"

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: TruIntroScanTest <game folder\\> <unit list> <out file>\n");
        return 2;
    }
    FILE *f = fopen(argv[2], "rb");
    if (!f) { fprintf(stderr, "cannot open %s\n", argv[2]); return 2; }
    static char names[512][64];
    const char *units[512];
    int n = 0, line = 0;
    char buf[512];
    while (fgets(buf, sizeof(buf), f) && n < 512) {
        if (line++ == 0) continue;           // the count line
        size_t len = strlen(buf);
        while (len && (buf[len - 1] == '\r' || buf[len - 1] == '\n' || buf[len - 1] == ' ')) buf[--len] = 0;
        for (size_t k = 0; k < len; ++k) buf[k] = static_cast<char>(tolower(static_cast<unsigned char>(buf[k])));
        if (strncmp(buf, "levels\\", 7) != 0) continue;
        const char *last = strrchr(buf, '\\');
        strncpy(names[n], last ? last + 1 : buf, sizeof(names[n]) - 1);
        names[n][sizeof(names[n]) - 1] = 0;
        units[n] = names[n];
        ++n;
    }
    fclose(f);
    truintro::IntroRow rows[64];
    truintro::ScanStats st;
    const int nr = truintro::ScanIntros(argv[1], units, n, rows, 64, st);
    FILE *o = fopen(argv[3], "wb");
    if (!o) { fprintf(stderr, "cannot write %s\n", argv[3]); return 2; }
    for (int k = 0; k < nr; ++k) fprintf(o, "%lu %s\r\n", rows[k].intro, rows[k].unit);
    fprintf(o, "# stats rows %d units %d read %d missing %d faults %d scripts %d intros %d without_own %d max_drm %lu ms %lu%s%s\r\n",
            nr, st.units, st.read, st.missing, st.faults, st.scripts, st.intros, st.withoutOwn, st.maxDrm, st.ms,
            st.err[0] ? " err " : "", st.err);
    fclose(o);
    printf("%d row(s), %d unit(s) listed, %d read, %d missing, %d faults, %d script(s), %lu ms, largest DRM %lu B, most "
           "kept %lu B%s%s\n", nr, n, st.read, st.missing, st.faults, st.scripts, st.ms, st.maxDrm, st.maxKept,
           st.err[0] ? " - " : "", st.err);
    return nr < 0 ? 2 : nr ? 0 : 1;
}
