# Riproduce il build attuale di tools/locals.py (solo in memoria) e lo confronta con i file gia' prodotti.
import sys, pickle, os, json, hashlib
sys.path.insert(0, '/path/to/trudlcport/tools')
import locals as L
T = pickle.load(open('/path/to/trudlcport/work/ws/hints/tables.pkl', 'rb'))
V = {src: {s: (T[src][s]['lang'], T[src][s]['strings']) for s in T[src]} for src in T}
L.files_cache['pcpatch'] = {s: T['pcpatch'][s]['raw'] for s in T['pcpatch']}
m, info = L.build_map(V)
print('build_map info', info)
ref_dir = '/path/to/trudlcport/work/generic/locals/mods/local'
for spec in L.SPECS:
    lang, strings, st = L.merged(V, spec, m)
    b = L.write_pc(lang, strings, T['pcpatch'][spec]['offs'])
    suffix = (spec & 0x1f) if spec != 0xffffffe0 else 32
    fn = os.path.join(ref_dir, 'locals.bin_%03d' % suffix)
    ref = open(fn, 'rb').read() if os.path.exists(fn) else None
    print('spec %08x suffix %03d stats %s  identical_to_existing %s' % (spec, suffix, dict(st), (ref == b) if ref is not None else 'NO REF FILE'))
