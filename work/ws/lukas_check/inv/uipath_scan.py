"""uipath_scan.py - (19/11/2026) solo lettura. Verifica del passo `uipath` del fork (suo script_u16array_fix.py,
logica riscritta): array u16 inline negli script DLC nuovi (Xbox tipo 8, id >= 20000): {u32 n (1..64), ptr interno ->
parola successiva, u16[n]}, ristretti a liste di voci (il conteggio e' bersaglio di un puntatore interno, o segue
direttamente l'array precedente), nessun puntatore nei dati, elementi Xbox non nulli.
Classi (parole PC): ok_sym = ordine Xbox, u16 LE, ogni elemento = Symbol PC (idmap.json tipo 100) = cio' che il fork scrive;
ok_altro_map = ordine Xbox, u16 LE, ma qualche elemento con altro valore (es. il nostro fix usa la mappa dei DataMember
per il primo elemento); DIFETTO_s32 = PC = scambio a 32 bit delle parole Xbox (forma non mappata del convertitore, quella
che il fork corregge); altro = nessuna delle precedenti.
uso: python -I -B uipath_scan.py BASELINE [--show]"""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW, drm_reloc as R
BL = sys.argv[1]; SHOW = '--show' in sys.argv
L = C.Log(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uipath_scan_%s.log' % BL.split('_')[0]))
SYM = C.idmap()[100]


def members(d, reloc, e):
    """Symbol dei DataMember (array a root+0x2c, passo 20, parola +12: nome) dello script"""
    E = '>' if e == 'be' else '<'; it = dict(R.parse(reloc, e).internal)
    if 0x2c not in it: return set()
    a = it[0x2c]; n = struct.unpack_from(E + 'I', d, a - 4)[0]; out = set()
    for i in range(n):
        if a + 20 * i + 16 > len(d): break
        w = struct.unpack_from(E + 'I', d, a + 20 * i + 12)[0]
        out.add(w & 0xffff if e == 'be' else w >> 16)
    return out


def arrays(xd, xr):
    out = []
    for o, t in xr.internal:
        if t != o + 4 or o < 4 or o > len(xd): continue
        n = struct.unpack_from('>I', xd, o - 4)[0]
        if not 1 <= n <= 64: continue
        words = (2 * n + 3) // 4
        if t + 4 * words > len(xd): continue
        out.append((o - 4, n, t, words))
    return out


def entry_lists(xd, xr):
    """[(count off, n, data off, words)] liste di voci come nel fork"""
    ptrs = set(xr.pointer_offsets()); targets = {t for _, t in xr.internal}; ends = set(); out = []
    for co, n, t, words in sorted(arrays(xd, xr)):
        if any(t + 4 * k in ptrs for k in range(words)): continue
        if co not in targets and co not in ends: continue
        xv = list(struct.unpack_from('>%dH' % (2 * words), xd, t))
        if not all(xv[:n]): continue
        ends.add(t + 4 * words); out.append((co, n, t, words))
    return out


if __name__ == '__main__':
    tot = collections.Counter(); per = collections.Counter()
    for rel, path in C.files(BL):
        xr = C.xbox(rel)
        if xr is None: continue
        X = DW.read(xr, 'be').sections; P = DW.read(open(path, 'rb').read(), 'le').sections
        prs, un = C.pair_scripts_any([x for x in X if x.type == 8 and x.id >= 20000], P)
        tot['script Xbox >=20000 non accoppiati'] += len(un)
        for x, p, m in prs:
            tot['script accoppiati'] += 1
            if len(x.data) != len(p.data): tot['script accoppiati di lunghezza diversa (allineati)'] += 1
            xd, pd = x.data, p.data; xrr = R.parse(x.reloc, 'be')
            for co, n, t, words in entry_lists(xd, xrr):
                q = m.get(t)
                if q is None or any(m.get(t + 4 * k) != q + 4 * k for k in range(words)):
                    tot['array non allineabili'] += 1; L('NONALLINEATO %s script %d +0x%x' % (rel, x.id, t)); continue
                if q != t: tot['array spostati (lunghezza diversa)'] += 1
                xw = xd[t:t + 4 * words]; pw = pd[q:q + 4 * words]
                xv = list(struct.unpack_from('>%dH' % (2 * words), xd, t)); pv = list(struct.unpack_from('<%dH' % (2 * words), pd, q))
                want = [SYM.get(v, v) if k < n else v for k, v in enumerate(xv)]
                s32 = b''.join(xw[k:k + 4][::-1] for k in range(0, len(xw), 4))
                if pv[:n] == want[:n]: c = 'ok_sym'
                elif pw == s32 and pv[:n] != want[:n]: c = 'DIFETTO_s32'
                elif all(pv[k] == want[k] for k in range(1, n)) and pv[0] != want[0]: c = 'ok_altro_map(primo elemento)'
                else: c = 'altro'
                tot[c] += 1; per[rel, c] += 1
                pm = members(pd, p.reloc, 'le'); xm = members(xd, x.reloc, 'be')
                tot['primo el. Xbox tra i membri Xbox: %s' % (xv[0] in xm)] += 1
                tot['primo el. PC tra i membri PC: %s' % (pv[0] in pm)] += 1
                tot['primo el. atteso_fork tra i membri PC: %s' % (want[0] in pm)] += 1
                if c != 'ok_sym' and (SHOW or c in ('DIFETTO_s32', 'altro')):
                    L('%s %s script %d->%d +0x%x(pc +0x%x) n=%d xbox %s pc %s atteso_fork %s' % (c, rel, x.id, p.id, t, q, n,
                      ' '.join('%04x' % v for v in xv[:n]), ' '.join('%04x' % v for v in pv[:n]), ' '.join('%04x' % v for v in want[:n])))
    fl = collections.Counter();
    for (rel, c), v in per.items(): fl[c] += 1
    L('file per classe: %s' % dict(fl))
    L('file con DIFETTO_s32: %s' % sorted({r for (r, c) in per if c == 'DIFETTO_s32'}))
    L('TOTALE %s' % dict(sorted(tot.items())))
