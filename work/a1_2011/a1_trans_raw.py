"""A1 (2026-11-20): one chart record's transitions read the way the engine reads them (read only).

Transition block (0x14 B) as the PC machine uses it (0x787570 / 0x785920, tru.exe 1.1):
  +0 u16 target, +2 u16 count of the u16 "kind" list at +8, +4 u16 condition count, +6 u16,
  +8 ptr u16 kind list (0x787665: kind 1 = deferred until machine+0x24 == 1; 0x787694: kind 7 = deferred while byte
  machine+0x53c != 0; the deferred transition is kept in machine+0x514 and taken first at the next selection),
  +0xc ptr condition records {u16 key, s16 id, u16 value, u8 flags (bit 0 NOT), u8} (0x785920 reads id at +2).
tools/chart_state_path.py reads the conditions from +8; for transitions with kinds (count +2 > 0) that shows the
kind list as the first "conditions". This script prints both lists from their own pointers.

Usage (from the repository root):
  ../bin/pyt -t 300 work/a1_2011/a1_trans_raw.py DRM ENDIAN SID IDX [IDX ...]
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import chart_state_path as CP


def fmt_cond(ky, i, v, fl):
    s = '{%d,%d,%d%s}' % (ky, i, v, ',NOT' if fl & 1 else '')
    return s


def dump(C, idx):
    ks = CP.targets(C, idx)
    if not ks:
        print('%d: (none)' % idx)
        return
    r, hdr, acts, sids, tr, l20 = C.state(ks[0])
    parent = hdr[3] - 0x10000 if hdr[3] & 0x8000 else hdr[3]
    print('record %d parent %d sids %s' % (idx, parent, sids))
    for ti in tr:
        a = C.tlist[ti]
        tg, nk, nc, w3 = struct.unpack_from(C.f + '4H', C.d, a)
        pk = C.it.get(a + 8)
        pc = C.it.get(a + 0xc)
        kinds = [struct.unpack_from(C.f + 'H', C.d, pk + 2 * j)[0] for j in range(nk)] if pk is not None else []
        conds = []
        if pc is not None:
            for j in range(min(nc, 24)):
                ky, i, v = struct.unpack_from(C.f + '3H', C.d, pc + 8 * j)
                conds.append(fmt_cond(ky, i, v, C.d[pc + 8 * j + 6]))
        print('  slot %4d -> %5d kinds %s conds(%d) %s  [+8 %s, +0xc %s]' % (
            ti, tg, kinds, nc, ' '.join(conds),
            '0x%x' % pk if pk is not None else '-', '0x%x' % pc if pc is not None else '-'))


def main():
    a = sys.argv[1:]
    if len(a) < 4:
        print(__doc__)
        return 2
    C = CP.Chart(a[0], a[1], int(a[2]))
    for x in a[3:]:
        dump(C, int(x))
    return 0


if __name__ == '__main__':
    sys.exit(main())
