"""Ingressi (dcl input) del PS nuovo vs PS vecchio surrogato, per variante: il nuovo deve leggere solo texcoord che il vecchio gia' leggeva."""
import sys, io, contextlib, json
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import build_unlit as B
C = B.F14.C; sm3asm = B.sm3asm; ROOT = B.ROOT
OUT = ROOT + '/work/ws/giro5/out_unlit'
build = json.load(open(OUT + '/build.json'))['materiali']
t_new = C.read_tree(OUT + '/mods'); t87 = C.read_tree(ROOT + '/work/baseline/B87_materiali19/mods')
def ins(bc):
    p = sm3asm.decode(bc); r = set()
    for i in p.instrs():
        if i.op == 'dcl' and i.ops[0].rtype == sm3asm.RT_INPUT: r.add((i.usage & 0x1f, (i.usage >> 16) & 15))
    return r
for mid, v in sorted(build.items(), key=lambda kv: int(kv[0])):
    if v['status'] != 'costruito': continue
    rel = v['drms'][0]
    fn = C.frame_lib({(s.type, s.id): s for s in t_new[rel].sections}[(9, v['lib'])].data)
    fo = C.frame_lib({(s.type, s.id): s for s in t87[rel].sections}[(9, v['old'])].data)
    for k in v['occs']:
        n = ins(fn['entries'][fn['slots'][k]]['bc']); o = ins(fo['entries'][fo['slots'][k]]['bc']) if fo['slots'][k] != 0xFFFFFFFF else None
        print(mid, 'var', k, 'nuovo', sorted(n), 'vecchio', None if o is None else sorted(o), 'ECCEDENZA' if o is not None and n - o else 'ok')
