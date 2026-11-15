"""Read-only (crash 5, 2026-11-15 22:35): which native functions does a script call - built g_pda vs the PC g_pda?
Per script: calls (op65 / op66 / op69 / op71 ... = tools/native_calls_check.call_kind 'entry') into native type
scripts of the same file, as (native script id, function index, name Symbol) with counts; prints what only one side
calls. Usage (repo root): ../bin/pyt -t 900 work/crash_gpda_1411/native_call_diff.py BUILT_G_PDA SCRIPT_ID[,...]"""
import sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from sec_hex import load
import drm_reloc as R
import native_calls_check as NC


def calls(S, sid):
    secs = [(t, i, d, rl) for t, i, d, rl in S]
    s = [x for x in secs if x[0] == 8 and x[1] == sid][0]
    d, rl = s[2], s[3]
    ft_cache = {}
    out = collections.Counter()
    for si, so, do in R.parse(rl, 'le').external:
        t = secs[si]
        if t[0] != 8 or not t[2]: continue
        ck = NC.call_kind(d, so)
        if not ck or ck[1] != 'entry': continue
        if t[1] not in ft_cache: ft_cache[t[1]] = NC.func_table(t[2], t[3])
        e = ft_cache[t[1]].get(do)
        out[(t[1], e[0] if e else None, e[1] if e else None, 'native' if e and e[2] else 'script')] += 1
    return out


def main(argv):
    _, B = load(argv[0]); _, P = load('pc:g_pda.drm')
    for sid in map(int, argv[1].split(',')):
        b, p = calls(B, sid), calls(P, sid)
        print('== %d: built %d calls (%d kinds), PC %d calls (%d kinds)' % (sid, sum(b.values()), len(b), sum(p.values()), len(p)))
        for k in sorted(set(b) | set(p), key=lambda k: (k[0], k[1] if k[1] is not None else -1)):
            if b[k] != p[k]:
                print('   script %d f%s name %s (%s): built %d, PC %d' % (k[0], k[1], k[2], k[3], b[k], p[k]))


if __name__ == '__main__':
    main(sys.argv[1:])
