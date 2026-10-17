"""Giro 6 L4: attenua le ragnatele (mat 20673 20676 23173 23329 20876, tupla PC 240-243 = PS 242) scalando c104.x (moltiplicatore dell'albedo nel PS 242:
`mul r1.xyz, r1, c104.x`) di un fattore K, IDENTICO in tutti i DRM che contengono il materiale (gate_stesso_id). Altro invariato (alfa/cutout/blend).
Giro 7: campo selezionabile (argv[4]): c104x (default, offset 16*4+0) oppure c100w (alfa, offset 12). K per materiale da web_lever.py (c104.x lineare sull'RGB, alfa invariata).
Uso: l4_webs.py SRC_MODS OUT_MODS K|mid=K,mid=K [c104x|c100w]   (copia in OUT_MODS solo i DRM cambiati, con stessi relpath)"""
import sys, os, struct, hashlib
ROOT = '/path/to/trudlcport'; sys.path.insert(0, ROOT + '/tools')
import drm_write as DW, drm_reloc as R
WEBS = {20673, 20676, 23173, 23329, 20876}
src, out = sys.argv[1], sys.argv[2]
KS = {int(a.split('=')[0]): float(a.split('=')[1]) for a in sys.argv[3].split(',')} if '=' in sys.argv[3] else {m: float(sys.argv[3]) for m in WEBS}   # K unico oppure 'mid=K,mid=K' (materiali non elencati invariati)
FIELD = sys.argv[4] if len(sys.argv) > 4 else 'c104x'
OFF = {'c104x': 16 * 4, 'c100w': 12}[FIELD]
for dp, _, fs in sorted(os.walk(src)):
    for f in sorted(fs):
        if not f.endswith('.drm'): continue
        p = os.path.join(dp, f); rel = os.path.relpath(p, src); raw = open(p, 'rb').read()
        if not any(str(i).encode() for i in ()): pass
        try: d = DW.read(DW.cdrm_decode(raw, 'le') if raw[:4] == b'CDRM' else raw, 'le')
        except Exception: continue
        hit = [s for s in d.sections if s.type == 10 and s.id in WEBS and s.id in KS]
        if not hit: continue
        before = {(s.type, s.id): s.data for s in d.sections}
        for s in hit:
            ip = dict(R.parse(s.reloc, 'le').internal); n = struct.unpack_from('<I', s.data, 0x58)[0]; po = ip[0x5C]
            assert n >= 5
            x = struct.unpack_from('<f', s.data, po + OFF)[0]
            assert abs(x - 1.0) < 1e-6, (rel, s.id, x)           # valore atteso dal web_cutout (c104 = 1,1,1,5)
            b = bytearray(s.data); struct.pack_into('<f', b, po + OFF, KS[s.id]); s.data = bytes(b)
        enc = DW.cdrm_encode(d.write('le'), 'le')
        a2 = {(s.type, s.id): s for s in DW.read(DW.cdrm_decode(enc, 'le'), 'le').sections}
        ch = {k for k in before if a2[k].data != before[k]}
        assert ch == {(10, s.id) for s in hit}, (rel, ch)
        q = os.path.join(out, rel); os.makedirs(os.path.dirname(q), exist_ok=True); open(q, 'wb').write(enc)
        print(rel, 'mat', sorted(s.id for s in hit), FIELD, '->', {x.id: KS[x.id] for x in hit}, hashlib.md5(enc).hexdigest()[:8])
