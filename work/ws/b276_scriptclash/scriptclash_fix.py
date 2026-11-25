"""scriptclash_fix.py - (19/11/2026) DLC2: lo script base dei thrall (Xbox 8453 -> PC 12433) e' ri-scritto dal DLC2 con un
altro layout (152 byte, istanza 8 byte, 1 membro health +4) sotto l'id del gioco base. Il generalbank.drm del PC (caricato
per primo, resta residente) ha 12433 del gioco base (3300 byte, 3 membri: playersensor +4, +8, health +12): le classi DLC2
24347/22813/24545 (e 24891 via 24545) derivano dalla copia residente sbagliata. Allo scarico il membro +4 viene rilasciato
come playersensor ma contiene il puntatore all'istanza -> lista categorie corrotta, AV 0x5976a3 (visto in B139 e pozza).
Segnalazione e analisi: LukasKurthRocks (issue #5, suo finding 45; lui usa 26884, da noi occupato da DTP tipo 7).
Correzione: la copia DLC2 (solo sezioni tipo 8 id 12433 lunghe 152) prende l'id libero NEW e tutti i riferimenti id tipo 8
a 12433 nello stesso DRM passano a NEW. Copie DLC1 / generalbank (3300 byte) intatte. Verifica parola per parola + round-trip.
uso: scriptclash_fix.py --src BASELINE --out DIR [--dry]"""
import sys, os, struct, hashlib, collections
R_ = '/path/to/trudlcport/'; sys.path.insert(0, R_ + 'tools')
import drm_write as DW, drm_reloc as Rl
a = sys.argv; SRC = R_ + 'work/baseline/%s/mods/' % a[a.index('--src') + 1]; outd = a[a.index('--out') + 1]; dry = '--dry' in a
OLD, NEW, DLEN, GBLEN = 12433, 26893, 152, 3300
BS = chr(92)

def all_ids(root):
    s = set()
    for r, _, fs in os.walk(root):
        for f in fs:
            if f.endswith('.drm'):
                for x in DW.read(open(os.path.join(r, f), 'rb').read(), 'le').sections: s.add(x.id)
    return s

def t8refs(s):
    rl = Rl.parse(s.reloc, 'le') if s.reloc else Rl.Reloc()
    return sorted({o for t, o in rl.idref + rl.idref_a if t == 8})

assert NEW not in all_ids(SRC), 'id NEW gia\' usato nelle mods'
import json
for e in json.load(open(R_ + 'work/idx_pc.json')):
    if e[5]: assert all(x[1] != NEW for x in e[5]), 'id NEW nel PC'
gb = DW.read(open(SRC + 'generalbank.drm', 'rb').read(), 'le')
assert [len(x.data) for x in gb.sections if x.type == 8 and x.id == OLD] == [GBLEN], 'generalbank 12433 inatteso'
tot = collections.Counter(); outs = []
for r, _, fs in sorted(os.walk(SRC)):
    for f in sorted(fs):
        if not f.endswith('.drm'): continue
        rel = os.path.relpath(os.path.join(r, f), SRC).replace(BS, '/'); raw = open(os.path.join(r, f), 'rb').read()
        D = DW.read(raw, 'le'); own = [x for x in D.sections if x.type == 8 and x.id == OLD]
        if not own: continue
        assert len(own) == 1, rel
        if len(own[0].data) == GBLEN: tot['copia base intatta'] += 1; continue
        assert len(own[0].data) == DLEN, (rel, len(own[0].data))
        own[0].id = NEW; plan = set()
        for i, x in enumerate(D.sections):
            b = bytearray(x.data)
            for o in t8refs(x):
                if struct.unpack_from('<I', b, o)[0] == OLD: struct.pack_into('<I', b, o, NEW); plan.add((i, o))
            x.data = bytes(b)
        o_ = D.write('le')
        if raw[:4] == b'CDRM': o_ = DW.cdrm_encode(o_, 'le')
        D0 = DW.read(raw, 'le'); D2 = DW.read(o_, 'le'); ch = set()
        assert len(D0.sections) == len(D2.sections)
        for i, (x, y) in enumerate(zip(D0.sections, D2.sections)):
            assert (x.type, x.reloc, len(x.data)) == (y.type, y.reloc, len(y.data))
            assert x.id == y.id or (x.type, x.id, y.id) == (8, OLD, NEW)
            ch |= {(i, j - j % 4) for j in range(len(x.data)) if x.data[j] != y.data[j]}
            assert all(struct.unpack_from('<I', y.data, o)[0] != OLD for o in t8refs(y)), (rel, 'riferimento rimasto')
        assert ch == plan, (rel, sorted(ch ^ plan))
        rt = DW.read(o_, 'le').write('le'); rt = DW.cdrm_encode(rt, 'le') if o_[:4] == b'CDRM' else rt; assert rt == o_, 'round-trip'
        tot['DRM corretti'] += 1; tot['parole'] += len(plan)
        print('%-60s parole id %d' % (rel, len(plan))); outs.append((rel, o_))
print(dict(tot))
if not dry:
    for rel, o_ in outs:
        p = os.path.join(outd, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(o_)
    open(os.path.join(outd, 'md5.txt'), 'w').write(''.join('%s  %s\n' % (hashlib.md5(o_).hexdigest(), rel) for rel, o_ in outs))
