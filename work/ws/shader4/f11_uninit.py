"""F11 - controllo statico "lettura di registro temp non inizializzato" (regola del validatore D3D9 ps_3_0), in ordine di programma.
uso: tools/venv/bin/python -I work/ws/shader4/f11_uninit.py [baseline=B75]"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f9_common import *
import drm_write


def uninit_reads(prog):
    st = stypes(prog); init = set(); bad = []
    for k, i in enumerate(body(prog)):
        for j, o in enumerate(i.ops):
            if o.isdst or o.rtype != sm3asm.RT_TEMP: continue
            for c in lanes(i, j, st):
                if (o.num, c) not in init: bad.append((k, i.op, o.num, 'xyzw'[c]))
        if i.ops and i.ops[0].isdst and i.ops[0].rtype == sm3asm.RT_TEMP:
            for c in range(4):
                if i.ops[0].wm >> c & 1: init.add((i.ops[0].num, c))
    return bad


if __name__ == '__main__':
    L = libs(); P = L['P']; n = bad_pc = 0
    for p, lib in P.items():
        if lib['kind'] != 1: continue
        for s in set(lib['slots']) - {0xffffffff}:
            b = lib['entries'][s]['blob']; n += 1; bad_pc += bool(uninit_reads(sm3asm.decode(b[:sm3dis.bytecode_len(b)])))
    print('shader PC originali con letture non inizializzate: %d / %d' % (bad_pc, n))
    base = sys.argv[1] if len(sys.argv) > 1 else 'B75'
    rep = json.load(open(os.path.join(HERE, 'f10_build.json')))
    for l in rep['libs']:
        d = drm_write.read(open(os.path.join(ROOT, 'work/baseline', base, 'mods', l['drm']), 'rb').read(), 'le')
        s = next(s for s in d.sections if s.type == 9 and s.id == l['lib_id'])
        lib = shaderlib.parse(s.data, 'le')
        for k, e in enumerate(lib['slots']):
            if e == 0xffffffff: continue
            b = lib['entries'][e]['blob']; bad = uninit_reads(sm3asm.decode(b[:sm3dis.bytecode_len(b)]))
            print(l['drm'], l['lib_id'], 'slot', k, 'letture non inizializzate:', len(bad), bad[:4])


def decl_problems(prog):
    """registri v/misc/s letti senza dcl, dcl o def duplicati, piu' di un registro costante per istruzione."""
    out = []; dv = collections.Counter(); dd = collections.Counter()
    for i in prog.instrs():
        if i.op == 'dcl': dv[(i.ops[0].rtype, i.ops[0].num)] += 1
        if i.op in ('def', 'defi', 'defb'): dd[(i.op, i.ops[0].num)] += 1
    out += ['dcl duplicato %s' % (k,) for k, v in dv.items() if v > 1] + ['def duplicato %s' % (k,) for k, v in dd.items() if v > 1]
    for k, i in enumerate(body(prog)):
        cregs = set()
        for o in i.ops:
            if o.isdst: continue
            if o.rtype in (sm3asm.RT_INPUT, sm3asm.RT_MISC, sm3asm.RT_SAMPLER) and (o.rtype, o.num) not in dv:
                out.append('istr %d %s legge %d/%d non dichiarato' % (k, i.op, o.rtype, o.num))
            if o.rtype == sm3asm.RT_CONST: cregs.add(o.num)
        if len(cregs) > 1: out.append('istr %d %s legge %d registri costanti %s' % (k, i.op, len(cregs), sorted(cregs)))
    return out


def check_all(base='B75'):
    rep = json.load(open(os.path.join(HERE, 'f10_build.json')))
    for l in rep['libs']:
        d = drm_write.read(open(os.path.join(ROOT, 'work/baseline', base, 'mods', l['drm']), 'rb').read(), 'le')
        s = next(s for s in d.sections if s.type == 9 and s.id == l['lib_id'])
        lib = shaderlib.parse(s.data, 'le')
        for k, e in enumerate(lib['slots']):
            if e == 0xffffffff: continue
            b = lib['entries'][e]['blob']; pr = sm3asm.decode(b[:sm3dis.bytecode_len(b)])
            pb = decl_problems(pr)
            print(l['drm'], l['lib_id'], 'slot', k, len(pb), pb[:5])
