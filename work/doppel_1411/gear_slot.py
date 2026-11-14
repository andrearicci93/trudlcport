"""Read-only (doppel_1411, 2026-11-14): weapon-manager slot of PC gear objects = object data +0xd8 (ENGINE "Weapon
manager slots": slot = gear query 0x32 result +0xd0 = object data +0xd8; g_tanks 13 as the check value) and the gear
family at +0xdc, read from the PC bigfile (../data/pc/bigfile.000, nothing written).
Usage (from trudlcport): ../bin/pyt -t 300 work/doppel_1411/gear_slot.py NAME [NAME ..]   e.g. g_grapple g_tanks"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from archive import Archive
from names import crc
from drm import cdrm_decode
import drm_write as DW
import drm_reloc as R


def main(a):
    pc = Archive('../data/pc/bigfile.000', 'le')
    for nm in a:
        hits = pc.find(crc('pc-w\\%s.drm' % nm))
        if not hits: print('%s: not in the bigfile' % nm); continue
        for r in hits:
            D = DW.read(cdrm_decode(pc.read(r), 'le'), 'le')
            # calibration-free scan: every section offset o with u32 [o] = slot candidate, [o+4] = family candidate,
            # printed when the family word is one of the 13 gear families (0..12) and the slot word is 0..14
            for si, s in enumerate(D.sections):
                d = bytes(s.data)
                for o in range(0, len(d) - 7, 4):
                    sl, fa = struct.unpack_from('<II', d, o)
                    if o == 0xd8 and sl <= 14 and fa <= 12:
                        print('    candidate: section %d (type %d, id %d) +0xd8 slot %d, +0xdc family %d'
                              % (si, s.type, s.id, sl, fa))
            obs = [s for s in D.sections if s.type == 11]
            for s in obs:
                d = bytes(s.data)
                rl = R.parse(bytes(s.reloc), 'le')
                ext = {src: (si, dst) for si, src, dst in rl.external}
                it = dict(rl.internal)
                print('%-16s object section id %d (%d B): +0x14 %s; +8 internal %s external %s'
                      % (nm, s.id, len(d), struct.unpack_from('<I', d, 0x14)[0],
                         hex(it[8]) if 8 in it else '-', ext.get(8)))
                if 8 in ext:
                    si, dst = ext[8]; t = D.sections[si]; td = bytes(t.data)
                    v = lambda o: struct.unpack_from('<I', td, dst + o)[0] if dst + o + 4 <= len(td) else None
                    print('    -> section %d (type %d, id %d) +0x%x: +0xd0 slot %s  +0xd4 family %s'
                          % (si, t.type, t.id, dst, v(0xd0), v(0xd4)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
