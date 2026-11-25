"""unitcurve_scan.py - (19/11/2026) SOLA LETTURA. Riscrittura nostra della regola `unitcurve` del fork di Lukas
(fork tools/unit_curve_fix.py, Q32 11/11): nel DTP unit (target esterno di Level +0x74) le regioni raggiunte dalla radice
sotto root/+6c o root/+1fc i cui record Xbox finiscono TUTTI col marcatore beebbeeb (passo 0xc0: curva u16[64] a +0x34,
marcatore +0xb8; passo 0xb0: curva +0x24, marcatore +0xac) hanno una curva di 64 u16 (rampa monotona sull'Xbox):
ogni parola della curva sul PC = s16 della parola Xbox (due u16 scambiati ciascuno). Regioni abbinate PC/Xbox per
etichetta di percorso-puntatori (BFS dalla radice, come typed_family_fix.labels) e dimensione; record il cui
marcatore PC manca = saltati; slot puntatore/id esclusi. DTP unit con id PC != id Xbox (base-mapped) = esclusi.
Una parola conta come "errata" solo se il PC e' un altro ordine degli stessi 4 byte (come il fork); altrimenti "kept".
In piu' (nostro): monotonia della curva PC letta come u16 LE (rampa rotta = sintomo).
uso: python -I -B unitcurve_scan.py BASELINE      log: inv/unitcurve_<BASELINE>.log"""
import sys, os, struct, collections, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/path/to/trudlcport/tools')
import faults_scan as F
import drm_write as DW, drm_reloc as R
BS = chr(92)
BEEB = b'\xbe\xeb\xbe\xeb'
LAYOUTS = ((0xc0, 0x34, 0xb8), (0xb0, 0x24, 0xac))
ROOT_LISTS = ('+6c', '+1fc')

def s16(w): return bytes((w[1], w[0], w[3], w[2]))

def unit_dtp(D, e):
    if not D.sections or D.sections[0].type != 0: return None
    for si, so, do in R.parse(bytes(D.sections[0].reloc), e).external:
        if so == 0x74 and si < len(D.sections) and D.sections[si].type == 7: return si
    return None

def intro_count(u, e, ptr):
    E = '<' if e == 'le' else '>'
    a = ptr.get(0x10)
    if a is None or len(u.data) < 0x14: return 0
    n = struct.unpack_from(E + 'I', u.data, 0xc)[0]
    return n if a + 0x90 * n <= len(u.data) else 0

def labels(data, ptr, nintro):
    T = sorted(set(ptr.values()) | {0}); T = [t for t in T if t < len(data)]
    size = {t: (T[i + 1] if i + 1 < len(T) else len(data)) - t for i, t in enumerate(T)}
    def start(o):
        i = bisect.bisect_right(T, o) - 1
        return T[i] if i >= 0 else 0
    ia = ptr.get(0x10)
    lab = {0: ('root',)}
    if ia is not None: lab[ia] = ('intros',)
    src = collections.defaultdict(list)
    for s, t in ptr.items(): src[start(s)].append((s, t))
    q = collections.deque([0] + ([ia] if ia is not None else []))
    while q:
        rs = q.popleft(); L = lab[rs]
        for s, t in sorted(src.get(rs, [])):
            if t not in size or t in lab: continue
            if L == ('intros',) and ia is not None and ia <= s < ia + 0x90 * nintro:
                k, r = divmod(s - ia, 0x90); lab[t] = ('?', 'i+%x' % r)
            else: lab[t] = L + ('+%x' % (s - rs),)
            q.append(t)
    return {t: (lab.get(t, ('unreached',)), size[t]) for t in T}

def layout(d, rs, sz, be):
    m = BEEB if be else BEEB[::-1]
    for st, co, mo in LAYOUTS:
        if sz < st or sz % st: continue
        if all(d[rs + r + mo:rs + r + mo + 4] == m for r in range(0, sz, st)): return st, co, mo
    return None

def main():
    base = sys.argv[1]
    B = '/path/to/trudlcport/work/baseline/%s/mods/' % base
    tot = collections.Counter(); files = collections.Counter(); dlc_c = collections.Counter(); rows = []; notes = []; mono = []
    for root, _, fs in os.walk(B):
        for f in sorted(fs):
            if not f.lower().endswith('.drm'): continue
            rel = os.path.relpath(os.path.join(root, f), B).replace(BS, '/')
            try: PD = DW.read(open(os.path.join(root, f), 'rb').read(), 'le')
            except Exception: continue
            kp = unit_dtp(PD, 'le')
            if kp is None: continue
            xr, pk, oth = F.xbox(rel, PD)
            if xr is None: notes.append('%s: unit senza Xbox' % rel); continue
            XD = DW.read(xr, 'be'); kx = unit_dtp(XD, 'be')
            if kx is None: notes.append('%s: Xbox senza unit DTP' % rel); continue
            u, ux = PD.sections[kp], XD.sections[kx]; dlc = F.DLC_OF[pk]
            tot['unit DTP'] += 1
            if u.id != ux.id: notes.append('%s: unit DTP %d = Xbox %d (base-mapped), escluso' % (rel, u.id, ux.id)); continue
            pp = dict(R.parse(bytes(u.reloc), 'le').internal); px = dict(R.parse(bytes(ux.reloc), 'be').internal)
            LP = labels(bytes(u.data), pp, intro_count(u, 'le', pp)); LX = labels(bytes(ux.data), px, intro_count(ux, 'be', px))
            bx = {v[0]: (t, v[1]) for t, v in LX.items() if v[0][0] == 'root'}
            bp = {v[0]: (t, v[1]) for t, v in LP.items() if v[0][0] == 'root'}
            sx, sp = F.slots(ux, 'be'), F.slots(u, 'le')
            xd, pd = bytes(ux.data), bytes(u.data)
            nwrong0 = tot['errate']
            for lab in sorted(set(bx) & set(bp)):
                (tx, sz), (tp, szp) = bx[lab], bp[lab]
                if sz != szp or len(lab) < 3 or lab[1] not in ROOT_LISTS: continue
                Lo = layout(xd, tx, sz, True)
                if Lo is None: continue
                stride, co, mo = Lo; tot['regioni'] += 1
                for r in range(0, sz, stride):
                    if pd[tp + r + mo:tp + r + mo + 4] != BEEB[::-1]: tot['record senza marcatore PC'] += 1; continue
                    tot['record'] += 1; badrec = 0
                    for q in range(co, co + 0x80, 4):
                        xo, po = tx + r + q, tp + r + q
                        if xo in sx or po in sp: tot['slot'] += 1; continue
                        xw, pw = xd[xo:xo + 4], pd[po:po + 4]; want = s16(xw)
                        tot['parole'] += 1
                        if pw == want: tot['ok'] += 1; continue
                        if sorted(xw) == sorted(pw):
                            tot['errate'] += 1; files[rel] += 1; dlc_c[dlc] += 1; badrec += 1
                            k = 'raw' if pw == xw else 's32' if pw == xw[::-1] else 'perm'
                            rows.append('%s [%s] 7:%d +0x%x %s rec +0x%x xbox %s pc %s atteso %s (%s)' % (rel, dlc, u.id, po, '/'.join(lab), r, xw.hex(), pw.hex(), want.hex(), k))
                        else:
                            tot['kept (non e\' un ordine dei byte Xbox)'] += 1
                            rows.append('%s [%s] KEPT 7:%d +0x%x %s xbox %s pc %s' % (rel, dlc, u.id, po, '/'.join(lab), xw.hex(), pw.hex()))
                    cp = struct.unpack_from('<64H', pd, tp + r + co); cx = struct.unpack_from('>64H', xd, tx + r + co)
                    xm = all(a <= b for a, b in zip(cx, cx[1:])); pm = all(a <= b for a, b in zip(cp, cp[1:]))
                    tot['curve Xbox monotone'] += xm
                    if xm and not pm: tot['curve PC rotte (Xbox monotona)'] += 1; mono.append('%s 7:%d %s rec +0x%x' % (rel, u.id, '/'.join(lab), r))
                    if badrec: tot['record con parole errate'] += 1
            if tot['errate'] > nwrong0: pass
    L = ['unitcurve su %s' % base, 'conteggi: ' + ', '.join('%s %d' % kv for kv in sorted(tot.items())),
         'errate per DLC: %s' % dict(dlc_c), 'file: ' + ', '.join('%s %d' % kv for kv in files.most_common()),
         '--- parole (%d) ---' % len(rows)] + rows + ['--- curve PC non monotone (%d) ---' % len(mono)] + mono + ['--- note ---'] + notes
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'unitcurve_%s.log' % base)
    open(p, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L[:4])); print('-> ' + p)

if __name__ == '__main__':
    main()
