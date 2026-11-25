"""uirecord_scan.py - (19/11/2026) solo lettura. Verifica del passo `uirecord` del fork (suo script_records_dlc.py +
dlc_fixes_build.fix_uirecord, logica riscritta): record elementi testo UI (16 parole) negli script DLC nuovi (Xbox tipo 8,
id >= 20000; g_pda escluso come nel fork). Regole per posizione dal record modello generalbank Xbox script 10 / PC script 9.
DEDOTTO: il fork usa lo script 10 Xbox RETAIL (layer1.000, non presente su questo PC); qui si usa la versione TU dello
store (work/generic/store.pkl xb_store (8,10), 5636 B): il suo record +0xd40 (ffb9b9b9 ff606060 ...) coincide parola per
parola con il record PC script 9 +0x670 salvo le posizioni ricavate come regole. Regola: 's32' (PC = valore Xbox),
'bytes' (byte grezzi), 'pc' (Xbox = valore modello -> costante PC del modello, altrimenti valore Xbox).
Posizione 4 (id stringa, passo uitext) e parole rilocate escluse. La posizione 3 (colore) e' anche nel passo uitext:
contata a parte.
uso: python -I -B uirecord_scan.py BASELINE"""
import sys, os, struct, collections, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW, drm_reloc as R
BL = sys.argv[1]
L = C.Log(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uirecord_scan_%s.log' % BL.split('_')[0]))
N = 16
st = pickle.load(open('/path/to/trudlcport/work/generic/store.pkl', 'rb'))
xd10 = st['xb_store'][(8, 10)]['data']; del st
S, _ = C.pc_generalbank(); pd9 = [s for s in S if s.type == 8 and s.id == 9][0].data
XO, PO = 0xd40, 0x670
rx = list(struct.unpack_from('>%dI' % N, xd10, XO)); rp = list(struct.unpack_from('<%dI' % N, pd9, PO))
assert rx[:4] == [0xffffffff, 0, 0xffb9b9b9, 0xff606060] and rp[:4] == rx[:4], (rx, rp)
bs = lambda v: int.from_bytes(v.to_bytes(4, 'big'), 'little')
rules = ['s32' if p == x else 'bytes' if p == bs(x) else 'pc' for x, p in zip(rx, rp)]
L('modello Xbox TU script10 +0x%x: %s' % (XO, ' '.join('%08x' % v for v in rx)))
L('modello PC  script9  +0x%x: %s' % (PO, ' '.join('%08x' % v for v in rp)))
L('regole: %s' % ' '.join(rules))
tot = collections.Counter(); pos = collections.Counter(); files = set(); bypack = collections.Counter()
for rel, path in C.files(BL):
    if os.path.basename(rel).lower() == 'g_pda.drm': continue
    xr = C.xbox(rel)
    if xr is None: continue
    pk = C.xpack(rel)
    X = DW.read(xr, 'be').sections; P = DW.read(open(path, 'rb').read(), 'le').sections
    prs, un = C.pair_scripts_any([x for x in X if x.type == 8 and x.id >= 20000], P)
    for x, p, m in prs:
        xd, pd = x.data, p.data; xrr = R.parse(x.reloc, 'be'); ro = set(xrr.pointer_offsets()) | set(xrr.id_offsets())
        pro = C.slots(p.reloc, 'le')
        for o in range(0, len(xd) - 4 * N + 1, 4):
            w = struct.unpack_from('>4I', xd, o)
            if not (w[0] in (0xffffffff, 0x00ffffff) and w[1] == 0 and w[3] >> 24 == 0xff and w[2] >> 24 in (0, 0xff) and w[2]): continue
            if any(m.get(o + 4 * i) != m.get(o, -99) + 4 * i for i in range(N)): tot['record non allineati'] += 1; continue
            q0 = m[o]; tot['record'] += 1; bypack[pk, 'record'] += 1; nch = 0; nch3 = 0; det = []
            for i in range(N):
                xo = o + 4 * i; q = q0 + 4 * i
                if xo in ro or i == 4: continue
                v = struct.unpack_from('>I', xd, xo)[0]
                want = bs(v) if rules[i] == 'bytes' else (rp[i] if rules[i] == 'pc' and v == rx[i] else v)
                cur = struct.unpack_from('<I', pd, q)[0]
                if cur != want:
                    if q in pro: tot['parole diverse ma rilocate sul PC'] += 1; continue
                    pos[i] += 1; det.append('w%d xbox %08x pc %08x atteso %08x' % (i, v, cur, want))
                    if i == 3:
                        w4 = struct.unpack_from('>I', xd, o + 16)[0]
                        ut = w[2] == 0xffffffff and not w4 & 0xffff and 1284 <= (w4 >> 16) <= 1406 and not any(k in ro for k in (o + 8, o + 12, o + 16))
                        if not ut: tot['parole colore w3 fuori dal pattern uitext'] += 1; bypack[pk, 'parole w3 fuori uitext'] += 1
                        nch3 += 1
                    else: nch += 1
            if nch or nch3:
                tot['parole da correggere (escl. colore w3)'] += nch; tot['parole colore w3 (anche in uitext)'] += nch3
                bypack[pk, 'parole escl. w3'] += nch; bypack[pk, 'parole w3'] += nch3
                if nch: tot['record da correggere (escl. w3)'] += 1; bypack[pk, 'record da correggere (escl. w3)'] += 1
                files.add(rel)
                L('%s script %d->%d +0x%x: %s' % (rel, x.id, p.id, o, '; '.join(det)))
L('per posizione: %s' % dict(sorted(pos.items())))
L('per pack: %s' % dict(sorted(bypack.items())))
L('file: %d %s' % (len(files), sorted(files)))
L('TOTALE %s' % dict(sorted(tot.items())))
