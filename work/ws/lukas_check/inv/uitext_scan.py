"""uitext_scan.py - (19/11/2026) solo lettura. Verifica del passo `uitext` del fork (suo script_uitext_fix.py, logica
riscritta) negli script DLC nuovi (Xbox tipo 8, id >= 20000; il fork include anche script base di rotta 'convert', qui NO).
A (elemento testo UI): Xbox ffffffff, colore (alpha 0xff), parola id con u16 bassa 0 e u16 alta = indice stringa DLC
   1284..1406; nessuno slot di rilocazione; parola id non dentro un array u16 inline. Atteso PC: colore = s32 del colore
   Xbox, id = stringa PC (work/generic/locals/locmap_xbox_to_pc.json) come u32.
B (lista hint): parola dopo un puntatore (Xbox), non slot, u16 bassa 0, u16 alta 1284..1406, non in array u16. Atteso PC:
   u32 = stringa PC.
Script di lunghezza diversa: offset allineati parola per parola (inv_common.align).
uso: python -I -B uitext_scan.py BASELINE"""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW, drm_reloc as R
from uipath_scan import arrays
BL = sys.argv[1]
L = C.Log(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uitext_scan_%s.log' % BL.split('_')[0]))
LOC = C.locmap(); SYM = C.idmap()[100]
LO, HI = 1284, 1406
tot = collections.Counter(); ids = collections.Counter(); bad_files = set()
for rel, path in C.files(BL):
    xr = C.xbox(rel)
    if xr is None: continue
    X = DW.read(xr, 'be').sections; P = DW.read(open(path, 'rb').read(), 'le').sections
    prs, un = C.pair_scripts_any([x for x in X if x.type == 8 and x.id >= 20000], P)
    tot['script non accoppiati'] += len(un)
    for x, p, m in prs:
        xd, pd = x.data, p.data; xrr = R.parse(x.reloc, 'be')
        sl = set(xrr.pointer_offsets()) | set(xrr.id_offsets()); ptrs = set(xrr.pointer_offsets())
        arr = set(k for c, n, t, w in arrays(xd, xrr) for k in range(c, t + 4 * w, 4))
        for o in range(0, len(xd) - 11, 4):
            a, col, w = struct.unpack_from('>III', xd, o)
            if a != 0xffffffff or col >> 24 != 0xff or w & 0xffff or not LO <= (w >> 16) <= HI: continue
            if any(k in sl for k in (o, o + 4, o + 8)): continue
            if o + 8 in arr: tot['A in array u16 (saltati)'] += 1; continue
            q = m.get(o + 4)
            if q is None or m.get(o + 8) != q + 4: tot['A non allineati'] += 1; continue
            xid = w >> 16; pid = LOC.get(xid)
            pc_col, pc_id = struct.unpack_from('<II', pd, q)
            tot['A elementi'] += 1; ids[xid] += 1
            okc = pc_col == col; oki = pc_id == pid
            k = 'A ok' if okc and oki else 'A DIFETTO ' + ('colore ' if not okc else '') + ('id' if not oki else '')
            tot[k] += 1
            if not (okc and oki):
                bad_files.add(rel)
                L('%s %s script %d +0x%x: colore xbox %08x pc %08x; stringa xbox %d -> atteso %s, pc %d%s' % (k, rel, x.id, o + 4, col, pc_col, xid, pid, pc_id,
                  ' (= Symbol idmap100 di %d)' % xid if SYM.get(xid) == pc_id and pc_id != pid else ''))
        for o in range(4, len(xd) - 3, 4):
            if o - 4 not in ptrs or o in sl: continue
            w = struct.unpack_from('>I', xd, o)[0]
            if w & 0xffff or not LO <= (w >> 16) <= HI: continue
            if o in arr: tot['B in array u16 (saltati)'] += 1; continue
            q = m.get(o)
            if q is None: tot['B non allineati'] += 1; continue
            xid = w >> 16; pid = LOC.get(xid); pc = struct.unpack_from('<I', pd, q)[0]
            tot['B voci hint'] += 1; ids[xid] += 1
            if pc == pid: tot['B ok'] += 1
            else:
                tot['B DIFETTO'] += 1; bad_files.add(rel)
                L('B DIFETTO %s script %d +0x%x: stringa xbox %d -> atteso %s, pc %08x' % (rel, x.id, o, xid, pid, pc))
L('indici stringa Xbox visti: %s' % dict(sorted(ids.items())))
L('file con difetti: %d %s' % (len(bad_files), sorted(bad_files)))
L('TOTALE %s' % dict(sorted(tot.items())))
