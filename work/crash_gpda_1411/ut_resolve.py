"""Read-only: for every entry (members / args / locals) of the ported / new scripts of a built g_pda: does its userType
name a script section (built g_pda or PC generalbank) - per tag; lists the unresolved ones with the PC twin's userType.
Usage (repo root): ../bin/pyt -t 900 work/crash_gpda_1411/ut_resolve.py BUILT_G_PDA"""
import sys, os, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import gpda_port as GP
import drm_write as DW
import script_member_pairs as MP


def main(argv):
    K = GP.load_knowledge()
    S = DW.read(open(argv[0], 'rb').read(), 'le').sections
    sec = {(s.type, s.id): s for s in S}
    scripts = {s.id for s in S if s.type == 8} | {s['id'] for s in GP.read_pc_generalbank() if s['type'] == 8}
    pc = {(s['type'], s['id']): s for s in GP.read_pc()}
    pcuts = collections.Counter(); known = collections.defaultdict(set)
    for src in (list(pc.values()), GP.read_pc_generalbank()):
        for s in src:
            if s['type'] != 8 or not s['data']: continue
            for k, lst in MP.entries(s['data'], s['reloc'], 'le')[1].items():
                for q in lst:
                    pcuts[(q['tag'], q['ut'] in scripts)] += 1; known[q['tag']].add(q['ut'])
    print('PC g_pda entries by (tag, userType is a script id):', dict(sorted(pcuts.items())))
    st = collections.Counter()
    for key, r in sorted(K['recipes'].items()):
        if r not in ('port', 'new93', 'new'): continue
        t, sid = map(int, key.split(':'))
        if (t, sid) not in sec: continue
        s = sec[(t, sid)]
        tw = K['_twins'].get(key, {})
        p = pc.get((t, sid))
        for k, lst in MP.entries(s.data, s.reloc, 'le')[1].items():
            for q in lst:
                ok = q['ut'] in scripts or q['ut'] in known[q['tag']]
                st[(q['tag'], ok)] += 1
                if not ok:
                    b = tw.get(q['a'])
                    put = struct.unpack_from('<H', p['data'], b + 4)[0] if (b is not None and p) else None
                    print('%s %s #%d tag %d ut %d (no script) name 0x%x; PC twin ut %s%s' % (
                        key, k, q['k'], q['tag'], q['ut'], q['name'], put, ' (a script)' if put in scripts else ''))
    print('ported / new entries by (tag, userType is a script id):', dict(sorted(st.items())))


if __name__ == '__main__':
    main(sys.argv[1:])
