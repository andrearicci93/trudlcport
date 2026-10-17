"""F2: round-trip disassembla->riassembla di 200 blob PS PC del gioco base (byte-identico). Seed fisso, un blob per lib diversa."""
import sys, os, pickle, struct, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import sm3asm, sm3dis
L = pickle.load(open(os.path.join(ROOT, 'work/render/shaderlibs.pkl'), 'rb'))
kind_want = int(sys.argv[1]) if len(sys.argv) > 1 else 1
N = int(sys.argv[2]) if len(sys.argv) > 2 else 200
pool = []
for lid in sorted(L['P']):
    lib = L['P'][lid]
    if lib['kind'] != kind_want: continue
    for o in sorted(lib['entries']):
        pool.append((lid, o))
random.seed(12345)
# un blob per lib poi riempi
bylib = {}
for lid, o in pool: bylib.setdefault(lid, []).append(o)
libs = sorted(bylib); random.shuffle(libs)
sel = []
for lid in libs[:N]: sel.append((lid, random.choice(bylib[lid])))
k = 0
while len(sel) < N:
    lid = libs[k % len(libs)]; k += 1
    c = (lid, random.choice(bylib[lid]))
    if c not in sel: sel.append(c)
ok_model = ok_text = ok_noctab = 0; bad = []
for lid, o in sel:
    b = L['P'][lid]['entries'][o]['blob']
    bl = sm3dis.bytecode_len(b); bc = b[:bl]
    try:
        p = sm3asm.decode(bc)
        e1 = sm3asm.encode(p)
        m = (e1 == bc)
        txt = sm3dis.disassemble(bc)
        e2 = sm3asm.assemble(txt)
        t = (e2 == bc)
        # senza CTAB: toglie i commenti, deve ricostruire l'identico meno i commenti
        txt2 = sm3asm.format_program(p, comments=False)
        e3 = sm3asm.assemble(txt2)
        p0 = sm3asm.decode(bc)
        p0.items = [i for i in p0.items if not isinstance(i, sm3asm.Comment)]
        n = (e3 == sm3asm.encode(p0))
    except Exception as ex:
        m = t = n = False; bad.append((lid, o, 'EXC ' + repr(ex)[:100]))
        continue
    ok_model += m; ok_text += t; ok_noctab += n
    if not (m and t and n): bad.append((lid, o, (m, t, n)))
print('kind', kind_want, 'campione', len(sel))
print('model decode->encode identico: %d/%d' % (ok_model, len(sel)))
print('testo disassembla->riassembla identico (con commenti verbatim): %d/%d' % (ok_text, len(sel)))
print('testo senza CTAB == bytecode senza CTAB: %d/%d' % (ok_noctab, len(sel)))
print('falliti', bad[:10])
