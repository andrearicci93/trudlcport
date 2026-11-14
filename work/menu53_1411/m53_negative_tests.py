r"""0.22.53 (2026-11-15): negative tests of trumenu_ini_check.check_02253 - each case breaks one rule in a copy of
TruMenu.cpp (read_cpp is replaced in memory) or of TruMenu.switches.txt (a mutated copy in _archiv\ next to this script,
overwritten per case and kept) and must yield at least one problem; the unchanged sources none. Every pattern must occur
exactly once (else the case counts as failed).

Usage (from the repository root):
  ../bin/pyt -t 300 work/menu53_1411/m53_negative_tests.py
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import trumenu_ini_check as T

SRC = T.read_cpp()
SW = T.SWITCHES
SW_TEXT = open(SW, encoding='utf-8').read()
CPP_CASES = [
    ('version', 'const char *const kVersion = "TruMenu 0.22.53 (sound log trees',
     'const char *const kVersion = "TruMenu 0.22.53 (sound trees'),
    # W11 kinds / sub-groups
    ('no weapons kind', '{"lara", "enemies", "world", "objects", "ui", "speech", "music", "weapons"};',
     '{"lara", "enemies", "world", "objects", "ui", "speech", "music", "guns"};'),
    ('g78 not Lara', 'kW8sLaraVoice, kW8sLaraBody, kW8sLaraShadow};', 'kW8sLaraVoice, kW8sWoDefault, kW8sLaraShadow};'),
    ('g62 not Waffen', 'kW8sObTraps, kW8sWpBrass, kW8sWpShot, kW8sWpReload,', 'kW8sObTraps, kW8sWpBrass, kW8sLaraBody, kW8sWpReload,'),
    ('waves unsorted', '    qsort(g_w8WeaponWaves, static_cast<size_t>(g_w8WeaponN), sizeof(WORD), W8WaveCmp);\n', ''),
    ('waves unloaded', '    W8WeaponWavesLoad(dir);', '    // W8WeaponWavesLoad(dir);'),
    ('sub dropped', '    {"ob_dlc2", ', '    {"ob_dlc3", '),
    ('no source', 'if (group != 14 || cat == kSnMusic || cat == kSnSpeech) return sub;', 'return sub;'),
    ('gear = Lara only', 'return own == 2 || W8WeaponWave(wave) ? kW8sWpLara14 : kW8sLaraGear;', 'return kW8sLaraGear;'),
    ('no +0x54', 'if (inst != player && !(ReadDword(inst + 0x54, &parent) && parent == player)) return 0;',
     'if (inst != player && !(ReadDword(inst + 0x58, &parent) && parent == player)) return 0;'),
    ('no follow', '    if (g_w8FollowMute && tree) return false;\n', ''),
    ('no sub filter', '    if (sub >= 0 && sub < kW8Subs && (g_w8DrawHide & (1ull << sub))) return false;\n', ''),
    ('no publish', '    W8PublishMute();                         // 0.22.53 W11\n', ''),
    ('cache unfinal', 'if (rec && final) rec->sub = v.sub;', 'if (rec) rec->sub = v.sub;'),
    ('no sub groups', 'wn += W8CatPureGroups(static_cast<int>(g_w6Rules[i].value), want + wn, kW6CgMax - wn, true);',
     'wn += 0;'),
    # layout
    ('no heading', '{"Schnell-H', '{"Schnell h'),
    ('hear first rows', '    {"Hall folgt Stumm", "Reverb follows mute", "snd.reverbmute", "", kQbBool, -1, kQcNone, 0, kQbSound, 0},\n'
     '    {"Hall aus", "Reverb off", "snd.reverboff", "", kQbBool, -1, kQcNone, 0, kQbSound, 0},\n    {"Lara", "Lara", "-", "tls_lara"',
     '    {"Lara", "Lara", "-", "tls_lara"'),
    ('kind open', '"tls_ui", "tls_sp", "tls_mu"};', '"tls_ui", "tls_sp"};'),
    ('level 3 lost', 'return (r.flags & kQfLv3) ? 3 : (r.flags & kQfLv2) ? 2 : (r.flags & kQfSub) ? 1 : 0;',
     'return (r.flags & kQfSub) ? 1 : 0;'),
    # S7
    ('S7 row changed', '{0x006e5657, "8b0dac00ed00 85c9 7452"},', '{0x006e5657, "8b0dac00ed00 85c9 7453"},'),
    ('S7 check order', '    S7Check();                                // 0.22.53', '    // S7Check();'),
    ('S7 no shutdown', '        S7Shutdown();                                 // 0.22.53', '        // S7Shutdown'),
    ('S7 open write', '    if (mode == 0) {\n        const bool want = S7Scope() != 0 && g_soOnC;',
     '    if (mode != 9) {\n        const bool want = S7Scope() != 0 && g_soOnC;'),
    ('S7 no pause gate', 'if (!ReadByte(kS7Pause, &pause) || pause != 6) { g_s7Gate |= 1; return; }', 'ReadByte(kS7Pause, &pause);'),
    ('S7 no heap gate', 'if (!ReadDword(kS7MapHeap, &heap) || heap) { g_s7Gate |= 2; return; }', 'ReadDword(kS7MapHeap, &heap);'),
    ('S7 no unit cap', 'if (g_s7Extra >= g_s7Max) { g_s7Capped |= 1; return; }', 'g_s7Capped |= 0;'),
    ('S7 rule skipped', '    __try { reinterpret_cast<S7RuleFn>(kS7Rule)(u); }\n    __except (EXCEPTION_EXECUTE_HANDLER) { ++g_s7Faults; return; }\n    S7Extend(u);',
     '    S7Extend(u);'),
    # markup
    ('markup fixed', '        memcpy(v.m, sonarM, sizeof(sonarM));\n', ''),
]
SW_CASES = [
    ('loadall restart', 'TruMenu | Sonar | LoadAllConnected | bool | Sonar: alles Verbundene laden | Sonar: load everything '
     'connected | live | 0 |', 'TruMenu | Sonar | LoadAllConnected | bool | Sonar: alles Verbundene laden | Sonar: load '
     'everything connected | restart | 0 |'),
    ('follow default', 'TruMenu | Sound | LogFollowMute | bool | Filter folgt Stumm | Filter follows mute | live | 1 |',
     'TruMenu | Sound | LogFollowMute | bool | Filter folgt Stumm | Filter follows mute | live | 0 |'),
]


def main():
    bad = 0
    T.read_cpp = lambda: SRC
    p, _ = T.check_02253(SW)
    print('positive (unchanged sources): %d problem(s) %s' % (len(p), 'ok' if not p else 'FAIL ' + '; '.join(p)))
    bad += 1 if p else 0
    for name, old, new in CPP_CASES:
        if SRC.count(old) != 1:
            print('case %-18s: pattern found %d times (need 1) - FAIL' % (name, SRC.count(old))); bad += 1; continue
        mutated = SRC.replace(old, new, 1)
        T.read_cpp = lambda m=mutated: m
        p, _ = T.check_02253(SW)
        ok = len(p) > 0
        bad += 0 if ok else 1
        print('case %-18s: %d problem(s) %s%s' % (name, len(p), 'ok' if ok else 'FAIL', (' - ' + p[0]) if p else ''))
    T.read_cpp = lambda: SRC
    os.makedirs(os.path.join(HERE, '_archiv'), exist_ok=True)
    copy = os.path.join(HERE, '_archiv', 'm53_switches_mutated.txt')
    for name, old, new in SW_CASES:
        if SW_TEXT.count(old) != 1:
            print('case %-18s: pattern found %d times (need 1) - FAIL' % (name, SW_TEXT.count(old))); bad += 1; continue
        with open(copy, 'w', encoding='utf-8', newline='') as f:
            f.write(SW_TEXT.replace(old, new, 1))
        p, _ = T.check_02253(copy)
        ok = len(p) > 0
        bad += 0 if ok else 1
        print('case %-18s: %d problem(s) %s%s' % (name, len(p), 'ok' if ok else 'FAIL', (' - ' + p[0]) if p else ''))
    n = len(CPP_CASES) + len(SW_CASES)
    print('%d cases + 1 positive, %d failed' % (n, bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
