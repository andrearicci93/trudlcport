"""Read-only (doppel_1411, 2026-11-14): object ids / states in a memory copy of the object table 0xdb7400
(0xcc entries of 0x24 B: +8 object, +0xc s16 id, +0xe u16 state; TruTrace kObjectTable).
Usage (from trudlcport): ../bin/pyt -t 60 work/doppel_1411/objtable_ids.py BIN OBJECTLIST.txt [ID ..]"""
import sys, struct


def main(a):
    d = open(a[0], 'rb').read()
    names = {}
    for ln in open(a[1], encoding='latin-1').read().splitlines()[1:]:
        c = ln.split(',')
        if len(c) == 2 and c[0].strip().isdigit(): names[int(c[0])] = c[1].strip()
    want = {int(x) for x in a[2:]}
    used = []
    for k in range(len(d) // 0x24):
        obj, oid, st = struct.unpack_from('<IhH', d, k * 0x24 + 8)
        if oid > 0: used.append((k, oid, st, obj))
    print('%d entries with an id' % len(used))
    print(' '.join('%d:%s(st%d)' % (oid, names.get(oid, '?'), st) for k, oid, st, obj in used))
    for w in sorted(want):
        hit = [u for u in used if u[1] == w]
        print('id %d %s: %s' % (w, names.get(w, '?'), hit if hit else 'NOT in the table'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
