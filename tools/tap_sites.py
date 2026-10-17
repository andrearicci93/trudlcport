#!/usr/bin/env python3
"""Catalogo statico dei siti di log silenziati di tru.exe (S1 'log tap', vedi PIANO_SONNET.md).

  tools/venv/bin/python -I tools/tap_sites.py [--exe work/laa/tru_steam.exe.unpacked.exe] [--out work/ws/tap]

Canale A = chiamate a 0x6457a0 (corpo = solo 'ret': printf di debug svuotato, MA forse anche funzioni vuote fuse dal linker).
Canale B = chiamate a 0x48e200 (logger vero: vsprintf in 0xa035f0).
Per ogni 'call rel32' verso i due bersagli classifica:
  fmt      ultimo push imm32 prima della call punta a una stringa stampabile (.rdata/.data) = primo argomento (fmt)
  regargs  nessun fmt immediato ma 'add esp,N' (N>=4) subito dopo: argomenti sullo stack (fmt da registro/memoria?)
  noargs   nessun 'add esp' dopo la call: probabilmente NON un printf (funzione vuota fusa dal linker)
Controlla anche: riferimenti assoluti (dword) ai bersagli in .rdata/.data (vtable/puntatori), jmp rel32 verso i bersagli,
byte originali ai bersagli. Scrive <out>/sites.tsv e stampa un riepilogo breve.
"""
import argparse, collections, hashlib, os, re, struct, sys

import capstone

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IB = 0x400000
EXE_MD5 = '56d1ce2dffa62f16354063da2df44d5a'      # Steamless unpacked di tru.exe Steam (b36da327)
TEXT = (0x1000, 0x43d000)                          # RVA, size (file offset == RVA: FileAlign == SectionAlign)
DATA_RANGES = [(0x43e000, 0x48e000), (0x48e000, 0x48e000 + 0x31000)]   # .rdata, .data (parte su disco)
TARGETS = {0x6457a0: 'A', 0x48e200: 'B'}
EXPECT = {0x6457a0: bytes.fromhex('c3cccccc cc'.replace(' ', '')), 0x48e200: bytes.fromhex('8b4c24048d442408')}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--exe', default=os.path.join(W, 'work/laa/tru_steam.exe.unpacked.exe'))
    ap.add_argument('--out', default=os.path.join(W, 'work/ws/tap'))
    a = ap.parse_args()
    exe = open(a.exe, 'rb').read()
    h = hashlib.md5(exe).hexdigest()
    if h != EXE_MD5:
        sys.exit('md5 exe inatteso %s (atteso %s)' % (h, EXE_MD5))

    def rd(va, n): return exe[va - IB:va - IB + n]

    def in_data(va): return any(lo <= va - IB < hi for lo, hi in DATA_RANGES)

    def cstr(va, n=240):
        if not in_data(va): return None
        s = rd(va, n).split(b'\0')[0]
        if len(s) < 3 or any(c < 9 or c > 126 for c in s): return None
        return s.decode('latin1')

    # 1) byte originali ai bersagli
    for t, e in EXPECT.items():
        got = rd(t, len(e))
        print('bytes %#x: %s %s' % (t, got.hex(), 'OK' if got == e else 'DIVERSO (atteso %s)' % e.hex()))
    tail = rd(0x6457a1, 15)
    ncc = len(tail) - len(tail.lstrip(b'\xcc'))
    print('padding dopo 0x6457a0: %s (%d byte CC consecutivi dopo il ret)' % (tail.hex(), ncc))

    # 2) riferimenti assoluti ai bersagli (vtable / puntatori a funzione) in .rdata/.data e nel .text (push imm / mov imm)
    for t in TARGETS:
        pat = struct.pack('<I', t)
        refs = [m.start() + IB for m in re.finditer(re.escape(pat), exe[0x1000:0x48e000 + 0x31000])]
        refs = [r + 0x1000 for r in refs]
        sec = collections.Counter('text' if r - IB < 0x43e000 else ('rdata' if r - IB < 0x48e000 else 'data') for r in refs)
        print('dword %#x: %d riferimenti assoluti %s; primi: %s' % (t, len(refs), dict(sec), ' '.join('%#x' % r for r in refs[:8])))

    # 3) call/jmp rel32 verso i bersagli
    text = exe[TEXT[0]:TEXT[0] + TEXT[1]]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    rows, jmps = [], collections.Counter()
    for m in re.finditer(b'[\xe8\xe9]', text):
        i = m.start()
        if i + 5 > len(text): break
        va = IB + TEXT[0] + i
        tgt = (va + 5 + struct.unpack_from('<i', text, i + 1)[0]) & 0xffffffff
        if tgt not in TARGETS: continue
        if text[i] == 0xe9:
            jmps[TARGETS[tgt]] += 1; continue
        # decodifica all'indietro una finestra che termina esattamente sulla call (x86 si risincronizza in poche istruzioni)
        prev, ok = [], False
        for back in range(48, 5, -1):
            insns = list(md.disasm(text[i - back:i + 5], va - back))
            if insns and insns[-1].address == va and insns[-1].size == 5:
                prev, ok = insns[:-1], True; break
        nxt = next(md.disasm(text[i + 5:i + 20], va + 5), None)
        clean = 0
        if nxt is not None and nxt.mnemonic == 'add' and nxt.op_str.startswith('esp, '):
            clean = int(nxt.op_str.split(', ')[1], 0)
        # argomenti = ultimi push prima della call (arg0 = ultimo push), fino a un salto/call/ret
        pushes = []
        for p in reversed(prev):
            if p.mnemonic in ('call', 'ret', 'jmp') or p.mnemonic.startswith('j') or p.mnemonic == 'int3': break
            if p.mnemonic == 'push': pushes.append(p)
            if clean and len(pushes) == clean // 4: break
        fmt, fidx = None, -1
        for k, p in enumerate(pushes[:4]):
            if p.op_str.startswith('0x'):
                s = cstr(int(p.op_str, 16))
                if s: fmt, fidx = s, k; break
        if fmt:
            kind = 'fmt%d' % fidx                                 # fmt0 = printf(fmt,..); fmt1 = printf(canale, fmt, ..)
        elif clean >= 4:
            kind = 'args'                                         # argomenti sullo stack ma fmt non immediato
        elif pushes:
            kind = 'pushes'                                       # push prima della call ma nessun 'add esp' subito dopo
        else:
            kind = 'noargs'                                       # probabile funzione vuota fusa dal linker, non un log
        if not ok: kind += '?'
        rows.append((TARGETS[tgt], va, va + 5, kind, clean, fidx, fmt or ''))
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, 'sites.tsv'), 'w') as f:
        f.write('chan\tcall_va\tret_va\tkind\tadd_esp\tfmt_arg\tfmt\n')
        for ch, va, ret, kind, clean, fidx, fmt in rows:
            f.write('%s\t%#x\t%#x\t%s\t%d\t%d\t%s\n' % (ch, va, ret, kind, clean, fidx, fmt.replace('\t', ' ').replace('\n', '\\n')))
    c = collections.Counter((r[0], r[3]) for r in rows)
    import json
    json.dump({'exe': os.path.relpath(a.exe, W), 'exe_md5': h, 'sites_md5': hashlib.md5(open(os.path.join(a.out, 'sites.tsv'), 'rb').read()).hexdigest(),
               'counts': {'%s/%s' % k: v for k, v in sorted(c.items())}, 'jmp_tail': dict(jmps),
               'note': '0x6457a0 = funzione vuota condivisa (riferimenti assoluti in .rdata/.data): NON patcharla, riscrivere solo le call dei siti fmt*'},
              open(os.path.join(a.out, 'sites.meta.json'), 'w'), indent=1)
    print('call rel32: ' + ', '.join('%s/%s=%d' % (k[0], k[1], v) for k, v in sorted(c.items())))
    print('jmp rel32 (tail call): %s' % dict(jmps))
    print('scritto %s' % os.path.join(a.out, 'sites.tsv'))


if __name__ == '__main__':
    main()
