"""Read-only (crash 5, 2026-11-15 22:35): members of the ported g_pda scripts whose userType differs from their PC
twin (gpda_port knowledge '_twins': converted entry offset -> PC entry offset), with tag / name / instance offset of
both sides. Usage (repo root): ../bin/pyt -t 900 work/crash_gpda_1411/twin_types.py BUILT_G_PDA"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import gpda_port as GP
import drm_write as DW


def main(argv):
    K = GP.load_knowledge()
    pc = {(s['type'], s['id']): s for s in GP.read_pc()}
    sec = {(s.type, s.id): s for s in DW.read(open(argv[0], 'rb').read(), 'le').sections}
    n = 0
    for key, tw in sorted(K['_twins'].items()):
        t, sid = map(int, key.split(':'))
        if (t, sid) not in sec or (t, sid) not in pc: continue
        d, p = sec[(t, sid)].data, pc[(t, sid)]['data']
        for a, b in sorted(tw.items()):
            tag, ut = struct.unpack_from('<IH', d, a); off, nm = struct.unpack_from('<HH', d, a + 12)
            ptag, put = struct.unpack_from('<IH', p, b); poff, pnm = struct.unpack_from('<HH', p, b + 12)
            if ut != put:
                n += 1
                print('%s entry +0x%x tag %d ut %d off 0x%x name 0x%x | PC +0x%x tag %d ut %d off 0x%x name 0x%x' % (
                    key, a, tag, ut, off, nm, b, ptag, put, poff, pnm))
    print('userType differs from the PC twin: %d' % n)


if __name__ == '__main__':
    main(sys.argv[1:])
