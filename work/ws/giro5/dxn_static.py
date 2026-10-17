"""Controllo statico (cantiere 2a, punto sollevato dal revisore): per OGNI materiale lit trapiantato (piano f12 + 19 di B87) elenca i sampler p_default* dello
shader Xbox il cui formato Xbox REALE e' DXN e verifica che la traduzione applichi la correzione 'y da alfa' (nome con _Normal_ oppure opts['dxn'])."""
import sys, io, contextlib, struct, collections
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
import texlib
texlib.set_baseline('B87_materiali19')
F14 = B.F14; C = F14.C; L = B.libs(); D, DM = L['D'], L['DM']; XL = B.XL
tree = C.read_tree(B.ROOT + '/work/baseline/B87_materiali19/mods')
plan = F14.plan_by_material()
mids = set(plan) | set()
# anche i 19 di B87: materiali che puntano a lib 2756..2774
extra = set()
for rel, d in tree.items():
    for s in d.sections:
        if s.type == 10 and s.id in DM:
            pc = struct.unpack_from('<4I', s.data, 0x28)[2]
            if 2756 <= pc <= 2774: extra.add(s.id)
mids |= extra
print('materiali lit trapiantati (piano f12 + 19 B87):', len(mids), '(piano', len(plan), ', extra B87', len(extra), ')')
bad = []; checked = 0; dxn_tot = 0
done = set()
for rel, d in sorted(tree.items()):
    for s in d.sections:
        if s.type != 10 or s.id not in mids or s.id in done: continue
        done.add(s.id)
        dl = struct.unpack_from('>4I', DM[s.id][0], 0x28)[2]
        try: slotmap, rows = F14.derive_slotmap(s.id, dl, s.data, s.reloc)
        except Exception as ex: print('mat', s.id, 'derive fallito', ex); continue
        blob = D[dl]['entries'][D[dl]['slots'][0]]['blob']
        names = {c['reg']: c['name'] for c in XL.parse(blob).ctab if c['set'] == 3}
        mo = B.material_opts(s.id)
        for r in rows:
            m = texlib.xb_mean(r['xbox_tex'])
            if m is None or m['kind'] != 'DXN': continue
            dxn_tot += 1
            n = names.get(r['xbox_reg'], '?')
            ok = ('_Normal_' in n) or n.startswith('p_default_Normal') or (slotmap[r['xbox_reg']] in mo.get('dxn', ()))
            checked += 1
            if not ok: bad.append((s.id, rel, r['xbox_reg'], n, r['xbox_tex']))
print('sampler DXN controllati:', checked, '| senza correzione dxn:', len(bad))
for b in bad[:40]: print('  mat %d (%s) reg %d nome %s xbox_tex %d' % b)
