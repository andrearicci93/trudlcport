"""Read-only: disassemble a window before each given call site of a 32-bit PE (tru.exe) and name the enclosing
function start (int3-padding heuristic of tools/pe_dis.py) - R10 jump / throw launch sites, 2026-11-18.

Usage (from the repository root):
  ../bin/pyt -t 300 work/r2_1811/call_windows.py EXE OUT.txt BEFORE_HEX SITE[,SITE..]
"""
import sys, os, io, contextlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import pe_dis
import pe_callers as PE


def main(argv):
    exe_path, out, before = argv[0], argv[1], int(argv[2], 16)
    exe = open(exe_path, 'rb').read()
    base, secs = PE.sections(exe)
    with open(out, 'w', encoding='utf-8') as f:
        for s in argv[3].split(','):
            a = int(s, 16)
            fs = pe_dis.func_start(exe, secs, a)
            lo = max(fs, a - before)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                pe_dis.main([exe_path, '%x' % lo, '%x' % (a + 5)])
            f.write('; ---- site 0x%x in function 0x%x\n' % (a, fs))
            f.write(buf.getvalue())
    print('written', out)


if __name__ == '__main__':
    main(sys.argv[1:])
