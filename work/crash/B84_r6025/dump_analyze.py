"""Identita' dell'oggetto nello slot texture al crash, da un dump completo ProcDump (-ma) di tru.exe 964f5714 / 56d1ce2d.

Uso: tools/venv/bin/python -I work/crash/B84_r6025/dump_analyze.py DUMP.dmp [--hash-only]
  --hash-only: solo verifica delle hash texture/materiali (per collaudare su un dump preso a gioco vivo).

Contratto [CODICE, disassembly 56d1ce2d, DIAGNOSI.md par.2/3/8]:
  FUN_005076e0: push ebx; push esi; push edi; edi = P (arg 2); 0x5076f8 mov edx,[edi]; 0x5076fa mov eax,[edx+0x30]; call eax (ret 0x507701).
  Con B = esp dopo i tre push: [B]=edi, [B+4]=esi salvato = record dello slot (FUN_00505a90), [B+8]=ebx, [B+0xc]=R = ritorno in 505a90:
    0x505b02 ciclo b1 (P=[rec+0]), 0x505b5b ciclo b2 (P=tabella globale o [rec+0]), 0x505ba7 ciclo b3 (P=param_2[idx-1] o [rec+0]).
  Frame di 505a90 visto da R: [R+0x24] = materiale (this), [R+0x30] = param_2.
  AV a 0x5076f8/0x5076fa: B = esp. _purecall: X = parola 0x507701 sullo stack, B = X+4.
  Hash texture: H = [0xc56fdc], [H+4] bucket, [H+0xc] tabella; nodo {next,id,obj,...}.  Hash materiali: [0x8a6ebc] bucket,
  [0x8a6ec4] tabella; nodo {next,id,obj,buffer,conteggio}. Materiale: [obj+4] = buffer dati; +0x50/+0x51/+0x52 conteggi, +0x54 slot (16 B).
"""
import sys, os, struct
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'tools')))
from minidump_read import Minidump

RETS = {0x505b02: 'b1', 0x505b5b: 'b2', 0x505ba7: 'b3'}
STATE = {0x1000: 'COMMIT', 0x2000: 'RESERVE', 0x10000: 'FREE'}


def walk(m, nb, tab, label, lim=1 << 20):
    """{obj: (id, nodo)} da una hash a catene; None se illeggibile."""
    if nb is None or tab is None or not (0 < nb < 1 << 20):
        print('  %s: intestazione illeggibile (bucket=%s tabella=%s)' % (label, nb, tab)); return None
    out, bad, n = {}, 0, 0
    for i in range(nb):
        node = m.u32(tab + 4 * i); seen = 0
        while node and seen < 10000 and n < lim:
            nx, nid, obj = m.u32(node), m.u32(node + 4), m.u32(node + 8)
            if nx is None or nid is None:
                bad += 1; break
            out[obj] = (nid, node); n += 1; seen += 1; node = nx
    print('  %s: %d bucket, %d nodi, %d catene rotte' % (label, nb, len(out), bad))
    return out


def meminfo(m, va):
    if 16 not in m.streams:
        return 'MemoryInfoList assente'
    _, r = m.streams[16]
    hs, es, cnt = struct.unpack_from('<IIQ', m.d, r)
    for i in range(cnt):
        e = r + hs + es * i
        base, abase, aprot, _, size, state, prot, typ = struct.unpack_from('<QQIIQIII', m.d, e)
        if base <= va < base + size:
            return '%s prot=%x tipo=%x regione %08x+%x (alloc %08x)' % (STATE.get(state, hex(state)), prot, typ, base, size, abase)
    return 'fuori da ogni regione'


def hexw(m, va, n=8):
    b = m.read(va, 4 * n) if va else None
    return ' '.join('%08x' % x for x in struct.unpack('<%dI' % n, b)) if b else 'NON NEL DUMP'


def main():
    m = Minidump(sys.argv[1])
    print('dump: %d intervalli memoria, %d thread' % (len(m.ranges), len(m.threads)))
    tm = m.u32(0xc56fdc)
    H = tm   # verificato sul dump B84_light: [G+4] bucket, [G+0xc] tabella (0x551270 viene chiamata con ecx = G)
    tex = walk(m, m.u32(H + 4) if H else None, m.u32(H + 0xc) if H else None, 'hash texture (gestore %s)' % (
        '%08x' % tm if tm else '?'))
    mat = walk(m, m.u32(0x8a6ebc), m.u32(0x8a6ec4), 'hash materiali')
    if '--hash-only' in sys.argv:
        if tex:
            vt = {}
            for o in list(tex)[:2000]:
                v = m.u32(o); vt[v] = vt.get(v, 0) + 1
            print('  vtable degli oggetti texture registrati:', {('%08x' % k if k else None): v for k, v in vt.items()})
        if mat:
            vt = {}
            for o in list(mat)[:2000]:
                v = m.u32(o); vt[v] = vt.get(v, 0) + 1
            print('  vtable degli oggetti materiale registrati:', {('%08x' % k if k else None): v for k, v in vt.items()})
        return 0
    frames = []
    e = m.exception
    if e and e['code'] == 0xc0000005:
        r = m.regs(e['ctx'])
        print('ECCEZIONE %08x a %08x info %s thread %d' % (e['code'], e['addr'], ['%x' % x for x in e['info']], e['tid']))
        print('  ' + ' '.join('%s=%08x' % kv for kv in r.items()))
        if r['eip'] in (0x5076f8, 0x5076fa):
            frames.append(('AV', e['tid'], r['esp'], r['edi']))
    for tid, crva in m.threads.items():   # _purecall / dump su richiesta: ancora 0x507701 su ogni stack
        rr = m.regs(crva)
        for a in range(rr['esp'], rr['esp'] + 0x3000, 4):
            if m.u32(a) == 0x507701 and m.u32(a + 0x10) in RETS:
                frames.append(('purecall', tid, a + 4, m.u32(a + 4))); break
    if not frames:
        print('ESITO: UNKNOWN (nessun frame FUN_005076e0 riconosciuto: crash altrove)'); return 2
    for kind, tid, B, edi in frames:
        R = B + 0xc; ret = m.u32(R); rec = m.u32(B + 4); mo = m.u32(R + 0x24); p2 = m.u32(R + 0x30)
        print('\n%s thread %d: B=%08x R=%08x [R]=%s ciclo %s' % (kind, tid, B, R, '%08x' % ret if ret else '?', RETS.get(ret, '?')))
        P = edi if kind == 'AV' else m.u32(R + 8)
        print('  P=%08x  [P]=%s  regione di P: %s' % (P, hexw(m, P, 4), meminfo(m, P)))
        vt = m.u32(P)
        if vt is not None:
            print('  [P] (vtable?) in %s; [[P]+0x30]=%s' % (m.module_of(vt), '%08x' % m.u32(vt + 0x30) if m.u32(vt + 0x30) is not None else 'illeggibile'))
        print('  P registrato come texture: %s' % (('id %d nodo %08x' % tex[P]) if tex and P in tex else 'NO'))
        print('  materiale obj=%s: %s' % ('%08x' % mo if mo else '?', ('id %d nodo %08x' % mat[mo]) if mat and mo in mat else 'NON registrato'))
        if mo:
            buf = m.u32(mo + 4)
            print('  materiale: vtable %s, [obj+4]=buffer %s, regione %s' % (
                '%08x' % m.u32(mo) if m.u32(mo) else '?', '%08x' % buf if buf else '?', meminfo(m, buf) if buf else '-'))
            if buf:
                hb = m.read(buf + 0x50, 8)
                if hb:
                    n50, n51, n52 = hb[0], hb[1], hb[2]; sl = struct.unpack('<I', hb[4:8])[0]
                    print('  conteggi n50=%d n51=%d n52=%d slot=%08x; rec=%s -> indice %s' % (
                        n50, n51, n52, sl, '%08x' % rec if rec else '?', (rec - sl) // 16 if rec and sl and (rec - sl) % 16 == 0 else '?'))
                    for k in range(min(n52 + n50, 32)):
                        rv = m.read(sl + 16 * k, 16)
                        if not rv:
                            print('    rec %d NON NEL DUMP' % k); continue
                        q = struct.unpack('<I', rv[:4])[0]
                        print('    rec %2d %s q=%08x idx=%d reg=%d %s%s' % (k, 'b1' if k < n51 else ('b2' if k < n52 else 'b3'), q, rv[0xc], rv[0xd],
                              ('tex id %d' % tex[q][0]) if tex and q in tex else ('NON registrato' if q else '0'),
                              '   <== rec del crash' if rec == sl + 16 * k else ''))
        if RETS.get(ret) == 'b3' and p2:
            print('  param_2 (array del chiamante): %s' % hexw(m, p2 - 4, 8))
    return 0


if __name__ == '__main__':
    sys.exit(main())
