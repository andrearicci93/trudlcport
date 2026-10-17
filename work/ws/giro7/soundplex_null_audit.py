"""Giro 7: audit statico dei nodi SoundPlex (walker FUN_005920b0: nodo = {u32 tipo 0..13, ptr dati}) su tutti i DRM di una dir mods.
Per ogni DTP PC con gemello Xbox (stesso id rimappato, stessa dimensione) confronta i nodi Xbox (soundplex_nodes.nodes: reloc interna a o, parola BE o-4 <= 13)
con il PC: (a) reloc interna a o presente con stesso target; (b) il tipo letto sul PC (LE) uguale; (c) per il tipo 0 il target contiene un float (nel dato);
(d) nodi PC con la stessa forma ma senza gemello Xbox. Segnala anche slot-nodo il cui target e' fuori dato. Uso: soundplex_null_audit.py MODS_DIR [nome.drm ..]"""
import sys, os, struct, collections
ROOT = '/path/to/trudlcport'; sys.path.insert(0, ROOT + '/tools')
import drm_reloc as R, drm_write as DW, dtpid_sweep as DS, soundplex_nodes as SN
from soundplex_fix import load_overlay, xsecs_of
mods = sys.argv[1]; names = set(sys.argv[2:]) or None
st, ids = DS.ctx(); ids.local = {}
tot = collections.Counter(); rows = []
for rel, path in sorted(load_overlay([mods], names).items()):
    xs = xsecs_of(rel)
    if xs is None: tot['senza_xbox'] += 1; print('SENZA XBOX', rel); continue
    raw = open(path, 'rb').read(); D = DW.read(DW.cdrm_decode(raw, 'le') if raw[:4] == b'CDRM' else raw, 'le')
    for s, i in DS.pairs(xs, D, ids):
        sec = D.sections[i]
        if len(sec.data) != len(s['data']): tot['dtp_taglia_diversa'] += 1; print('TAGLIA DIVERSA', rel, 'dtp', sec.id, len(sec.data), len(s['data'])); continue
        nd, xslots = SN.nodes(s['data'], s['reloc'])
        prel = R.parse(sec.reloc, 'le'); pit = dict(prel.internal); pslots = set(prel.pointer_offsets()) | set(prel.id_offsets())
        xrel = R.parse(s['reloc'], 'be'); xint = dict(xrel.internal)
        # nodi Xbox: (tipo, target) <- offset slot o con xint[o]=target e tipo BE a o-4
        for o, tg in xrel.internal:
            if o < 4 or o % 4 or (o - 4) in xslots: continue
            t = struct.unpack_from('>I', s['data'], o - 4)[0]
            if t > 13 or tg % 4 or tg >= len(s['data']): continue
            if SN.STRICT.get(t) and not SN.STRICT[t](s['data'], xint, tg): continue
            tot['nodi'] += 1; tot['tipo%d' % t] += 1
            prob = []
            if o not in pit: prob.append('reloc interna assente sul PC (slot %#x)' % o)
            elif pit[o] != tg: prob.append('target PC %#x != Xbox %#x' % (pit[o], tg))
            pt = struct.unpack_from('<I', sec.data, o - 4)[0]
            if pt != t: prob.append(('TIPO_PC_FUORI_RANGE' if pt > 13 else 'TIPO_PC_DIVERSO') + ' %d != Xbox %d' % (pt, t))
            xw = struct.unpack_from('>I', s['data'], o)[0]; pw = struct.unpack_from('<I', sec.data, o)[0]
            if xw != pw: prob.append('PAROLA_SLOT PC %#x != Xbox %#x (target %#x)' % (pw, xw, tg)); tot['parola_slot_diversa'] += 1
            if t == 0 and not prob and tg + 4 > len(sec.data): prob.append('float fuori dato')
            if prob:
                for pr in prob: tot['k:' + pr.split(' ')[0] + ('' if not pr.startswith('reloc') else '')] += 1
                rows.append((rel, sec.id, o, t, tg, prob))
ser=[r for r in rows if not all(p.startswith('TIPO_PC_FUORI_RANGE') for p in r[5])]
for r in ser[:80]: print(*r)
import collections as _c
print(_c.Counter(r[0] for r in rows).most_common(15))
print(_c.Counter((r[3]) for r in rows))
print('righe non banali', len(ser), 'su', len(rows))
print(dict(tot))
