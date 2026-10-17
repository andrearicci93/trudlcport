"""Lint statico di un blob ps_3_0 (regole D3D9 che fxc rispetta): dcl prima dell'uso, input letti dichiarati, temp letti dopo scrittura (per componente),
al piu' 1 registro costante distinto per istruzione (limite prudente), sorgenti scalari con swizzle replicato, oC0 scritto in tutte le componenti,
registri c<=223, r<32, sampler dichiarati, nessun registro dst read-only."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sm3asm, sm3dis
from sm3asm import *
SCAL = {'rcp', 'rsq', 'exp', 'log', 'pow'}
def lint(bc, strict_const=True):
    p = sm3asm.decode(bc); errs = []
    if p.kind != 'ps' or (p.major, p.minor) != (3, 0): errs.append('versione')
    dcl_in = {}; samp = set(); defs = set(); written = {}; oc = set()
    for i, ins in enumerate(p.instrs()):
        if ins.op == 'dcl':
            o = ins.ops[0]
            if o.rtype == RT_INPUT: dcl_in[o.num] = o.wm
            elif o.rtype == RT_MISC: dcl_in[('m', o.num)] = o.wm
            elif o.rtype == RT_SAMPLER: samp.add(o.num)
            continue
        if ins.op == 'def': defs.add(ins.ops[0].num); continue
        if ins.op in ('defi', 'defb'): continue
        ops = ins.ops
        if ins.op in ('else', 'endif', 'nop'): continue
        isd = ins.op not in ('texkill', 'if', 'ifc')
        srcs = ops[1:] if isd else ops
        cs = set()
        for k, o in enumerate(srcs):
            if o.rtype == RT_SAMPLER:
                if o.num not in samp: errs.append('%d sampler s%d non dichiarato' % (i, o.num))
                continue
            comps = set((o.swz >> (2 * l)) & 3 for l in range(4))
            if ins.op in SCAL and len(comps) != 1: errs.append('%d sorgente scalare non replicata' % i)
            if o.rtype == RT_CONST:
                cs.add(o.num)
                if o.num > 223: errs.append('%d c%d > 223' % (i, o.num))
            elif o.rtype == RT_INPUT:
                m = dcl_in.get(o.num)
                if m is None: errs.append('%d v%d non dichiarato' % (i, o.num))
                else:
                    lanes = range(4)
                    if isd: lanes = [l for l in range(4) if ops[0].wm >> l & 1]
                    if ins.op == 'dp3': lanes = [0, 1, 2]
                    if ins.op == 'dp4': lanes = [0, 1, 2, 3]
                    if ins.op == 'dp2add': lanes = [0, 1] if k < 2 else [0]
                    if ins.op in SCAL: lanes = [0]
                    if ins.op.startswith('texld'): lanes = [0, 1] if k == 0 else lanes
                    need = set((o.swz >> (2 * l)) & 3 for l in lanes)
                    if any(not (m >> c & 1) for c in need if True): errs.append('%d v%d comp non dichiarata' % (i, o.num))
            elif o.rtype == RT_MISC:
                if ('m', o.num) not in dcl_in: errs.append('%d misc%d non dichiarato' % (i, o.num))
            elif o.rtype == RT_TEMP:
                if o.num >= 32: errs.append('%d r%d' % (i, o.num))
                # componenti lette (approssimazione: tutte quelle dello swizzle usate dalle lane scritte)
                lanes = range(4)
                if isd:
                    d = ops[0]; lanes = [l for l in range(4) if d.wm >> l & 1]
                if ins.op in ('dp3',): lanes = [0, 1, 2]
                if ins.op in ('dp4',): lanes = [0, 1, 2, 3]
                if ins.op in ('dp2add',): lanes = [0, 1] if k == 0 or k == 1 else [0]
                if ins.op in SCAL: lanes = [0]
                if ins.op.startswith('texld'): lanes = [0, 1] if k == 0 else lanes
                for l in lanes:
                    c = (o.swz >> (2 * l)) & 3
                    if c not in written.get(o.num, set()): errs.append('%d r%d.%s letto non scritto' % (i, o.num, 'xyzw'[c]))
        if strict_const and len(cs) > 1: errs.append('%d piu\' costanti' % i)
        if isd:
            d = ops[0]
            if d.rtype == RT_TEMP: written.setdefault(d.num, set()).update(c for c in range(4) if d.wm >> c & 1)
            elif d.rtype == RT_COLOROUT: oc.update((d.num, c) for c in range(4) if d.wm >> c & 1)
            else: errs.append('%d dst tipo %d' % (i, d.rtype))
    if not all((0, c) in oc for c in range(4)): errs.append('oC0 non completo: %s' % sorted(oc))
    return errs
if __name__ == '__main__':
    import pickle
    ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
    L = pickle.load(open(os.path.join(ROOT, 'work/render/shaderlibs.pkl'), 'rb'))
    # calibrazione sul base PC (strict_const=False: il base usa 2 costanti)
    import collections
    c = collections.Counter(); n = 0
    for lid, lib in list(L['P'].items()):
        if lib['kind'] != 1: continue
        for o, e in list(lib['entries'].items())[:2]:
            b = e['blob'][:sm3dis.bytecode_len(e['blob'])]
            for er in lint(b, False): c[er.split(' ', 1)[1][:25]] += 1
            n += 1
    print('calibrazione base PC su', n, 'blob:', dict(c))
