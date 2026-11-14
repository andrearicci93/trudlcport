"""TruMenu 0.22.53 sonar-load research helper (read only).

Usage (from trudlcport):
  ../bin/pyt work/menu53_1411/sonar/s53_find.py EXE fscalls SLOT     call 0x472b50 (GetFS) followed within 8
                                                                     instructions by a vtable slot SLOT (hex) read
  ../bin/pyt work/menu53_1411/sonar/s53_find.py EXE callers VA [...]  call rel32 sites to VA with the function start
Output goes to stdout; nothing is written. Uses work/ledge18a_0811/qol_pe.py and work/sonar_1411/sonar_dis.py.
"""
import os
import sys
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'work', 'ledge18a_0811'))
sys.path.insert(0, os.path.join(ROOT, 'work', 'sonar_1411'))
import qol_pe as P  # noqa: E402
import sonar_dis as S  # noqa: E402


def main(a):
    d, base, secs, pe = P.load(a[0])
    code, va = P.text(d, secs)
    mode = a[1]
    if mode == 'fscalls':
        slot = int(a[2], 16)
        md = P.cs()
        getfs = 0x472b50
        for i in range(len(code) - 5):
            if code[i] != 0xe8:
                continue
            t = (va + i + 5 + struct.unpack_from('<i', code, i + 1)[0]) & 0xffffffff
            if t != getfs:
                continue
            site = va + i
            n = 0
            for ins in md.disasm(code[i + 5:i + 5 + 64], site + 5):
                n += 1
                if ('+ 0x%x]' % slot) in ins.op_str:
                    print('%08x  fn %08x  then %08x %s %s' % (site, S.fstart(code, va, site), ins.address,
                                                             ins.mnemonic, ins.op_str))
                    break
                if n >= 8 or ins.mnemonic == 'ret':
                    break
    elif mode == 'callers':
        want = set(int(x, 16) for x in a[2:])
        for i in range(len(code) - 5):
            if code[i] in (0xe8, 0xe9):
                t = (va + i + 5 + struct.unpack_from('<i', code, i + 1)[0]) & 0xffffffff
                if t in want:
                    print('%08x  fn %08x  %s -> %08x' % (va + i, S.fstart(code, va, va + i),
                                                         'call' if code[i] == 0xe8 else 'jmp', t))
    elif mode == 'raw':
        # raw HEX: every occurrence of the byte string in every section, with the section name
        want = bytes.fromhex(a[2])
        for name, sva, vs, off, size in secs:
            blob = d[off:off + size]
            i = blob.find(want)
            while i >= 0:
                print('%-8s %08x' % (name, sva + i))
                i = blob.find(want, i + 1)
    else:
        raise SystemExit('unknown mode ' + mode)


if __name__ == '__main__':
    main(sys.argv[1:])
