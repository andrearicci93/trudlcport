// TruCpScanTest.cpp - offline check of truintro::ScanCheckpoints (TruIntroScan.h, TruMenu 0.22.69 B4 point 1: the
// checkpoints of every unit from the game's files at run time for chapter.cp). Not part of TruMenu.asi. Build (x86, the
// same compiler as Build-TruAsi.ps1):
//   cl /nologo /O2 /MT /W4 /EHsc TruCpScanTest.cpp /Fe<out>\TruCpScanTest.exe
// Usage:
//   TruCpScanTest <game folder with patch.000 / bigfile.000 (and mods\), trailing \> <unit list (unitlist.txt form)>
//                 <object ids, comma list> <out file> [all]
// Without "all" only the "levels\..." lines of the unit list are read (the base units, as tools/unit_checkpoint_table.py);
// "all" also takes every other line's last name (the DLC units from mods\). The out file gets one line
// "<unit> <intro id> # obj <id> at x y z l80 x y z" per checkpoint and a "# stats" line;
// work/b4_2011/cp_scan_compare.py compares it with the table of tools/unit_checkpoint_table.py.
// Exit code: 0 = at least one row, 1 = none, 2 = usage / scan error.
#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../TruIntroScan.h"

int main(int argc, char **argv) {
    if (argc != 5 && argc != 6) {
        fprintf(stderr, "usage: TruCpScanTest <game folder\\> <unit list> <object ids a,b,..> <out file> [all]\n");
        return 2;
    }
    const bool all = argc == 6 && !strcmp(argv[5], "all");
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
        if (!len || (!all && strncmp(buf, "levels\\", 7) != 0)) continue;
        const char *last = strrchr(buf, '\\');
        strncpy(names[n], last ? last + 1 : buf, sizeof(names[n]) - 1);
        names[n][sizeof(names[n]) - 1] = 0;
        units[n] = names[n];
        ++n;
    }
    fclose(f);
    WORD objs[16];
    int no = 0;
    char ids[256];
    strncpy(ids, argv[3], sizeof(ids) - 1);
    ids[sizeof(ids) - 1] = 0;
    for (char *t = strtok(ids, ","); t && no < 16; t = strtok(nullptr, ",")) objs[no++] = static_cast<WORD>(atoi(t));
    static truintro::CpScanRow rows[4096];
    truintro::CpScanStats st;
    const int nr = truintro::ScanCheckpoints(argv[1], units, n, objs, no, rows, 4096, st);
    FILE *o = fopen(argv[4], "wb");
    if (!o) { fprintf(stderr, "cannot write %s\n", argv[4]); return 2; }
    for (int k = 0; k < nr; ++k) {
        const truintro::CpScanRow &r = rows[k];
        fprintf(o, "%s %lu # obj %u at %.1f %.1f %.1f l80 %.1f %.1f %.1f\r\n", units[r.unit], r.intro,
                static_cast<unsigned>(r.obj), r.pos[0], r.pos[1], r.pos[2], r.l80[0], r.l80[1], r.l80[2]);
    }
    fprintf(o, "# stats rows %d units %d read %d mods %d missing %d faults %d no_intros %d dropped %d ms %lu%s%s\r\n", nr,
            st.units, st.read, st.fromMods, st.missing, st.faults, st.noIntros, st.dropped, st.ms, st.err[0] ? " err " : "",
            st.err);
    fclose(o);
    printf("%d row(s), %d unit(s) listed, %d read (%d from mods), %d missing, %d faults, %d without intros, %lu ms%s%s\n",
           nr, n, st.read, st.fromMods, st.missing, st.faults, st.noIntros, st.ms, st.err[0] ? " - " : "", st.err);
    return nr < 0 ? 2 : nr ? 0 : 1;
}
