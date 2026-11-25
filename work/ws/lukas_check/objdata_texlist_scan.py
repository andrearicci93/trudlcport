"""objdata_texlist_scan.py - (19/11/2026) controllo di sola lettura dalla segnalazione di Lukas (issue #5):
liste di id texture del DTP dati-oggetto (DTP nominato all'offset +8 della sezione oggetto tipo 11).
L'exe maschera gli id con 0x1fff; un conteggio di gruppo non scambiato (0x0N000000) fa scorrere il ciclo su N dword.
Logica ripresa da tools/objdata_texlist_check.py del fork LukasKurthRocks (MIT).
uso: objdata_texlist_scan.py DIR_MODS [--all]"""
import sys, os, struct
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm_write as DW, drm_reloc as R
LISTS = [(0x0c, 0x10), (0x14, 0x18), (0x1c, 0x20), (0x24, 0x28), (0x2c, 0x30), (0x54, 0x58)]
d_, show = sys.argv[1], '--all' in sys.argv
nobj = nbad = 0
for n in sorted(os.listdir(d_)):
    if not n.lower().endswith('.drm'): continue
    try: drm = DW.read(open(os.path.join(d_, n), 'rb').read(), 'le')
    except Exception as ex: print('SKIP', n, ex); continue
    by = {(s.type, s.id): s for s in drm.sections}
    for s in drm.sections:
        if s.type != 11 or len(s.data) < 12: continue
        refs = {o: t for t, o in (R.parse(s.reloc, 'le').idref if s.reloc else [])}
        if refs.get(8) != 7: continue
        did = struct.unpack_from('<I', s.data, 8)[0]; d = by.get((7, did))
        if d is None or len(d.data) < 0x6c: continue
        nobj += 1; data = d.data; ptr = dict(R.parse(d.reloc, 'le').internal) if d.reloc else {}
        msgs = []
        for co, po in LISTS:
            c = struct.unpack_from('<H', data, co)[0]
            if c and (c & 0xff) == 0 and c >= 0x100: msgs.append('BE u16 count +0x%x = 0x%04x' % (co, c))
            if c and po not in ptr: msgs.append('BAD count +0x%x = %d, +0x%x non e\' un puntatore' % (co, c, po))
        g = struct.unpack_from('<H', data, 0x64)[0]; ids = 0
        if g and 0x68 in ptr:
            p = ptr[0x68]
            for k in range(g):
                if p + 4 > len(data): msgs.append('BAD gruppo %d oltre la fine' % k); break
                c = struct.unpack_from('<I', data, p)[0]
                if c > 64 or p + 4 + 4 * c > len(data): msgs.append('%s gruppo %d count +0x%x = 0x%08x' % ('BE' if c & 0xffffff == 0 else 'BAD', k, p, c)); break
                ids += c; p += 4 + 4 * c
        elif g: msgs.append('BAD gruppi %d senza puntatore +0x68' % g)
        if msgs:
            nbad += 1; print('%s obj %d -> DTP %d gruppi %d' % (n, s.id, did, g)); [print('   ', m) for m in msgs]
        elif show: print('ok %s obj %d -> DTP %d gruppi %d ids %d' % (n, s.id, did, g, ids))
print('oggetti con DTP dati-oggetto %d, con problemi %d' % (nobj, nbad))
