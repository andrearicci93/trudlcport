"""R9 (2026-11-19): Lara state table, machine 1 - PC (tru.exe 0x8b0a50) vs TU (0x82757948) vs retail (found by the
same id sequence), stride 28 B {id, slot 0..5}. Prints the entries of the given state ids (read-only, addresses only).

Usage (from the repository root):
  ../bin/pyt -t 300 work/r9_1911/r9_state_table.py EXE RETAIL.bin TU.bin ID[,ID..]
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import pe_callers as PE

BASE = 0x82000000


def pe_off(secs, a):
    for s in secs:
        sva, rptr, size = s[1], s[2], s[3]
        if sva <= a < sva + size:
            return rptr + a - sva
    return None


def read_pc(exe, secs, va, n):
    o = pe_off(secs, va)
    return [struct.unpack_from('<7I', exe, o + 28 * i) for i in range(n)]


def read_x(img, va, n):
    return [struct.unpack_from('>7I', img, va - BASE + 28 * i) for i in range(n)]


def count(rows):
    k = 0
    for r in rows:
        if r[0] == 0 or r[0] > 5000:
            break
        k += 1
    return k


def main(argv):
    if len(argv) < 4:
        sys.exit(__doc__)
    exe = open(argv[0], 'rb').read()
    base, secs = PE.sections(exe)
    retail = open(argv[1], 'rb').read()
    tu = open(argv[2], 'rb').read()
    want = [int(x) for x in argv[3].split(',')]
    pc = read_pc(exe, secs, 0x8b0a50, 400)
    pc = pc[:count(pc)]
    tt = read_x(tu, 0x82757948, 400)
    tt = tt[:count(tt)]
    ids = [r[0] for r in tt[:6]]
    pat = b''.join(struct.pack('>I', i) for i in ids[:1])
    found = None
    i = retail.find(pat)
    while i >= 0:
        if i % 4 == 0 and all(struct.unpack_from('>I', retail, i + 28 * k)[0] == ids[k] for k in range(6)):
            found = BASE + i
            break
        i = retail.find(pat, i + 1)
    rt = read_x(retail, found, 400) if found else []
    rt = rt[:count(rt)]
    print('PC table 0x8b0a50 entries %d; TU 0x82757948 entries %d; retail %s entries %d'
          % (len(pc), len(tt), ('0x%08x' % found) if found else 'not found', len(rt)))
    print('id sequence equal PC / TU: %s, retail / TU: %s'
          % ([r[0] for r in pc] == [r[0] for r in tt], [r[0] for r in rt] == [r[0] for r in tt]))
    for w in want:
        for name, rows in (('PC', pc), ('TU', tt), ('retail', rt)):
            for k, r in enumerate(rows):
                if r[0] == w:
                    print('%-6s id %4d entry %3d: %s' % (name, w, k, ' '.join('0x%08x' % x for x in r[1:])))


if __name__ == '__main__':
    main(sys.argv[1:])
