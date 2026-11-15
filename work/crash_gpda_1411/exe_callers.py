"""Read-only: every `call rel32` (E8) and `jmp rel32` (E9) in the code of a PE file that targets the given VAs.
Usage (repo root): ../bin/pyt work/crash_gpda_1411/exe_callers.py EXE VA_HEX [...]"""
import sys, struct


def main(argv):
    b = open(argv[0], 'rb').read()
    pe = struct.unpack_from('<I', b, 0x3c)[0]
    nsec = struct.unpack_from('<H', b, pe + 6)[0]; optsz = struct.unpack_from('<H', b, pe + 20)[0]
    base = struct.unpack_from('<I', b, pe + 24 + 28)[0]
    want = {int(x, 16) for x in argv[1:]}
    for k in range(nsec):
        o = pe + 24 + optsz + 40 * k
        name = b[o:o + 8].rstrip(b'\0').decode('latin1')
        vsz, va, rsz, raw, ch = struct.unpack_from('<IIII', b, o + 8) + (struct.unpack_from('<I', b, o + 36)[0],)
        if not ch & 0x20: continue          # code sections only
        sec = b[raw:raw + rsz]
        for i in range(len(sec) - 5):
            if sec[i] not in (0xe8, 0xe9): continue
            src = base + va + i
            tgt = (src + 5 + struct.unpack_from('<i', sec, i + 1)[0]) & 0xffffffff
            if tgt in want: print('%s %s 0x%x -> 0x%x' % (name, 'call' if sec[i] == 0xe8 else 'jmp', src, tgt))


if __name__ == '__main__':
    main(sys.argv[1:])
