"""Read-only (doppel_1411, 2026-11-14): native function calls (entry operands, as tools/native_calls_check.py) per
(calling script, native type, function index / name Symbol) of two DRMs, and the difference. 'pc:NAME' as sec_list.py.
Usage (from trudlcport): ../bin/pyt -t 900 work/doppel_1411/native_diff.py A.drm B.drm REF_GENERALBANK.drm [TYPE ..]
TYPE = native type script ids to report (default: all)."""
import sys, os, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW, drm_reloc as R
import native_calls_check as N
from sec_list import raw_of


def calls(D, native, want):
    c = collections.Counter()
    for s in D.sections:
        if s.type != 8 or not s.data: continue
        for si, so, do in R.parse(s.reloc, 'le').external:
            t = D.sections[si]
            if t.type != 8 or t.id not in native or (want and t.id not in want): continue
            ck = N.call_kind(s.data, so)
            if not ck or ck[1] != 'entry': continue
            ft = native[t.id][1]
            e = ft.get(do)
            c[(s.id, t.id, native[t.id][0], e[0] if e else None, e[1] if e else None)] += 1
    return c


def main(a):
    want = {int(x) for x in a[3:]}
    REF = {s.id: s for s in DW.read(open(a[2], 'rb').read(), 'le').sections if s.type == 8 and s.data}
    native = {}
    for sid, s in REF.items():
        info = N.P.script_info({'data': s.data, 'reloc': s.reloc}, 'le')[:2]
        if info[0]: native[sid] = (info[1], N.func_table(s.data, s.reloc))
    CA = calls(DW.read(raw_of(a[0]), 'le'), native, want)
    CB = calls(DW.read(raw_of(a[1]), 'le'), native, want)
    print('A %s: %d calls; B %s: %d calls' % (a[0], sum(CA.values()), a[1], sum(CB.values())))
    for k in sorted(set(CA) | set(CB), key=lambda k: (k[1], k[3] if k[3] is not None else -1, k[0])):
        if CA[k] != CB[k]:
            print('  caller %5d -> %3d %-14s f%s (name sym %s): A %d  B %d' % (k[0], k[1], k[2], k[3], k[4], CA[k], CB[k]))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
