"""Read-only: the call sites (source offsets) of one native function, found by its prototype name Symbol, in the
scripts of a g_pda ('pc:g_pda.drm' = PC archive copy).
Usage (repo root): ../bin/pyt -t 900 work/crash_gpda_1411/native_call_sites.py SPEC NAME_HEX"""
import sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from sec_hex import load
import drm_reloc as R
import native_calls_check as NC


def main(argv):
    _, S = load(argv[0]); name = int(argv[1], 16)
    ft = {}
    per = collections.defaultdict(list)
    for t, i, d, rl in S:
        if t != 8 or not d: continue
        for si, so, do in R.parse(rl, 'le').external:
            tt = S[si]
            if tt[0] != 8 or not tt[2]: continue
            ck = NC.call_kind(d, so)
            if not ck or ck[1] != 'entry': continue
            if tt[1] not in ft: ft[tt[1]] = NC.func_table(tt[2], tt[3])
            e = ft[tt[1]].get(do)
            if e and e[1] == name: per[i].append('+0x%x (-> %d f%d)' % (so, tt[1], e[0]))
    for i in sorted(per): print('%d: %d call(s) %s' % (i, len(per[i]), ' '.join(per[i][:12])))


if __name__ == '__main__':
    main(sys.argv[1:])
