"""fndiff.py: confronta funzioni TU (tru_patched.bin) e base (tru_base.bin) con ppcdis (VMX128), normalizzando indirizzi.
uso: python fndiff.py TU_ADDR BASE_ADDR [--show]   (lunghezza = fino all'inizio della funzione successiva negli INDEX.tsv)"""
import sys, subprocess, re, difflib, bisect
X = 'C:/tru-port/work/xbox_exe/'; P = 'C:/tru-port/tools/ppcdis/ppcdis.exe'
def starts(idx):
    s = []
    for l in open(X + idx):
        try: s.append(int(l.split('\t')[0], 16))
        except ValueError: pass
    return sorted(s)
ST = {'tru_patched.bin': starts('decomp/INDEX.tsv'), 'tru_base.bin': starts('decomp_base/INDEX.tsv')}
def body(binf, a):
    s = ST[binf]; i = bisect.bisect_right(s, a); end = s[i] if i < len(s) else a + 0x400
    n = max(1, min((end - a) // 4, 3000))
    out = subprocess.run([P, X + binf, '%x' % a, str(n)], capture_output=True, text=True).stdout.splitlines()
    norm = []
    for l in out:
        ins = l[18:].strip()
        ins = re.sub(r'0x8[0-9a-f]{7}', 'ADDR', ins)
        ins = re.sub(r'\b(r1),', r'\1,', ins)
        norm.append(ins)
    return out, norm
ta, ba = int(sys.argv[1], 16), int(sys.argv[2], 16)
to, tn = body('tru_patched.bin', ta); bo, bn = body('tru_base.bin', ba)
sm = difflib.SequenceMatcher(None, tn, bn, autojunk=False)
print('TU %x (%d istr) base %x (%d istr) ratio %.3f' % (ta, len(tn), ba, len(bn), sm.ratio()))
if '--show' in sys.argv:
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal': continue
        print('---', op)
        for k in range(i1, i2): print('  TU', to[k])
        for k in range(j1, j2): print('  BA', bo[k])
