r"""0.22.54 (2026-11-15 evening): negative tests of trumenu_ini_check.check_02254 - each case breaks one rule in a copy of
TruMenu.cpp (read_cpp is replaced in memory) or of TruMenu.switches.txt (a mutated copy in _archiv\ next to this script,
overwritten per case and kept) and must yield at least one problem; the unchanged sources none. Every pattern must occur
exactly once (else the case counts as failed). The two crash fixes (kHow per rule kind, S7FreshEntry) are covered by
their own cases; the format annotations by the cases 'Log bare' .. 'auto forward' (the /analyze check itself has its
own negative probe in work\fmt_1511\Test-TruMenuFormats.ps1).

Usage (from the repository root):
  ../bin/pyt -t 300 work/menu54_1511/m54_negative_tests.py
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import trumenu_ini_check as T

SRC = T.read_cpp()
SW = T.SWITCHES
SW_TEXT = open(SW, encoding='utf-8').read()
CPP_CASES = [
    ('version', '"TruMenu 0.22.54 (two crash fixes', '"TruMenu 0.22.55 (two crash fixes'),
    # (2) crash 1: kHow per rule kind
    ('kHow unchecked', 'how >= 0 && how < kW6Kinds ? kHow[how] : "?"', 'kHow[r.kind]'),
    ('no static_assert', '    static_assert(sizeof(kHow) / sizeof(kHow[0]) == kW6Kinds, "snd.mute: one kHow text per rule kind");\n',
     ''),
    ('no kind count', '       kW6Kinds };', '       };'),
    ('Log bare', 'void Log(int level, _Printf_format_string_ const char *fmt, ...) {', 'void Log(int level, const char *fmt, ...) {'),
    ('Out bare', 'void Out(char *out, size_t size, _Printf_format_string_ const char *fmt, ...) {',
     'void Out(char *out, size_t size, const char *fmt, ...) {'),
    ('lambda bare', 'auto add = [&](_Printf_format_string_ const char *fmt, ...) {', 'auto add = [&](const char *fmt, ...) {'),
    ('auto forward', 'auto add = [&](_Printf_format_string_ const char *fmt, ...) {', 'auto add = [&](const char *fmt, auto... a) {'),
    # (3) crash 2: the new list entry of the find
    ('S7 no fresh', '            if (!S7FreshEntry(nb)) { ++g_s7Faults; return; }\n', ''),
    ('S7 fresh no +0x88', '        *reinterpret_cast<volatile DWORD *>(nb + 0x88) = 0;\n', ''),
    ('S7 count loose', 'after == before + 1', 'after >= before'),
    ('S7 not last', '            ReadDword(arr + (after - 1) * 4, &last) && last == nb) {',
     '            ReadDword(arr + (after - 1) * 4, &last)) {'),
    ('S7 row dropped', '    {0x006dd7be, "8b8688000000 3bc3 8dbe88000000 743b 50 e87c18e7ff 83c404 84c0 57 7525 e8df2de7ff"},\n', ''),
    # (4) reset at start
    ('reset not called', '    SndResetAtStart(ini);                    // 0.22.54', '    // SndResetAtStart'),
    ('reset filter too', '{"Sound", "ReverbOff"}};', '{"Sound", "ReverbOff"}, {"Sound", "LogFollowMute"}};'),
    ('reset no INI', 'WritePrivateProfileStringA(k[0], k[1], "0", ini)', 'true'),
    ('reset per reload', 'static bool done = false;                // once per game start',
     'bool done = false;                // once per game start'),
    ('reset default 0', '{"Sound", "ResetAtStart", "1",', '{"Sound", "ResetAtStart", "0",'),
    ('reset row kind', '"Reset sound switches at start", "snd.resetatstart", "", kQbBool',
     '"Reset sound switches at start", "snd.resetatstart", "", kQbAction'),
    ('reset no log', 'Log(1, "0.22.54 sound switches at start: %s"', 'Log(1, "sound switches: %s"'),
    # (5) Menue-Musik
    ('g1 not menu', 'kW8sWoDefault, kW8sMuMenu, kW8sMuMusic, kW8sMuMusic,', 'kW8sWoDefault, kW8sMuMusic, kW8sMuMusic, kW8sMuMusic,'),
    ('g1 by slider', 'group == 1 ? kW8sMuMenu : ', ''),
    ('mu_menu no row', '"snd.logsub", "mu_menu"', '"snd.logsub", "mu_menux"'),
    # (6) heading
    ('heading back', '    {"Stumm / Solo", "Mute / solo", "-", "ton_log_hear"',
     '    {"Schnell-H\\303\\266ren", "Quick hearing", "-", "", kQbLabel, -1, kQcNone, 0, kQbSound, kQfLv2},\n'
     '    {"Stumm / Solo", "Mute / solo", "-", "ton_log_hear"'),
    # (7) joint.set drive
    ('drive target', 'const float t = d.type == 1 ? d.lock * 0.017453292519943295f : d.lock;',
     'const float t = d.type == 1 ? d.target * 0.017453292519943295f : d.target;'),
    ('no limit guard', '        if (g_jt.limits && (v < g_jt.limLo - margin || v > g_jt.limHi + margin))\n',
     '        if (false)\n'),
    ('no away guard', '        else if (dist > g_jt.best + away)\n', '        else if (false)\n'),
    ('no lead', '        if (val && next > v + lead) next = v + lead;\n', ''),
    ('no clamp', '    d.limits = d.saveLimit && lim[0] < lim[1];', '    d.limits = false;'),
    ('solve again', '&& usable && !tried)', '&& usable)'),
    ('no tick log', 'g_jt.lines < 400', 'g_jt.lines < 0'),
]
SW_CASES = [
    ('reset live', '| Reset sound switches at start | restart | 1 |', '| Reset sound switches at start | live | 1 |'),
    ('reset row 0.22.53', 'mute / solo as the game | TruMenu 0.22.54', 'mute / solo as the game | TruMenu 0.22.53'),
]


def main():
    bad = 0
    T.read_cpp = lambda: SRC
    p, _ = T.check_02254(SW)
    print('positive (unchanged sources): %d problem(s) %s' % (len(p), 'ok' if not p else 'FAIL ' + '; '.join(p)))
    bad += 1 if p else 0
    for name, old, new in CPP_CASES:
        if SRC.count(old) != 1:
            print('case %-18s: pattern found %d times (need 1) - FAIL' % (name, SRC.count(old))); bad += 1; continue
        mutated = SRC.replace(old, new, 1)
        T.read_cpp = lambda m=mutated: m
        p, _ = T.check_02254(SW)
        ok = len(p) > 0
        bad += 0 if ok else 1
        print('case %-18s: %d problem(s) %s%s' % (name, len(p), 'ok' if ok else 'FAIL', (' - ' + p[0]) if p else ''))
    T.read_cpp = lambda: SRC
    os.makedirs(os.path.join(HERE, '_archiv'), exist_ok=True)
    copy = os.path.join(HERE, '_archiv', 'm54_switches_mutated.txt')
    for name, old, new in SW_CASES:
        if SW_TEXT.count(old) != 1:
            print('case %-18s: pattern found %d times (need 1) - FAIL' % (name, SW_TEXT.count(old))); bad += 1; continue
        with open(copy, 'w', encoding='utf-8', newline='') as f:
            f.write(SW_TEXT.replace(old, new, 1))
        p, _ = T.check_02254(copy)
        ok = len(p) > 0
        bad += 0 if ok else 1
        print('case %-18s: %d problem(s) %s%s' % (name, len(p), 'ok' if ok else 'FAIL', (' - ' + p[0]) if p else ''))
    n = len(CPP_CASES) + len(SW_CASES)
    print('%d cases + 1 positive, %d failed' % (n, bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
