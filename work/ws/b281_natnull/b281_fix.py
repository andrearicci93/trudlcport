"""b281_fix.py - (20/11/2026) B281: chiamate degli script DLC a native che il PC non ha (achievement 16 sul PC, 21 nella TU Xbox).
Regola del fork LukasKurthRocks (tools/script_missing_native_fix.py), logica riscritta: ogni op65 (chiamata nativa) il cui operando ha
una rilocazione esterna verso lo script nativo `achievement` del generalbank PC ORIGINALE a un offset che non e' una voce della sua
tabella funzioni = puntatore nativo nullo. La sequenza dal marcatore di riga (op00) precedente fino alla chiamata compresa diventa il
marcatore ripetuto (nessun effetto sullo stack); le rilocazioni di quelle parole vengono tolte. Solo sequenze di sole push
(op02..op10 senza op09). Caso decisivo: dlc2_treasure_room_cine, script 26418 del cinematic_object 12164 (050_crush) chiama
achievement indice 17 -> la seconda cutscene del finale non parte (schermo nero, 20/11). 11 chiamate (inventario B276).
Verifica: rilettura, nessun'altra chiamata nulla, cambiano solo le parole previste e le rilocazioni tolte.
uso: b281_fix.py --src BASELINE --out DIR [--dry]"""
import sys, os, struct, hashlib
R_ = '/path/to/trudlcport/'
sys.path.insert(0, R_ + 'work/ws/lukas_check/inv'); sys.path.insert(0, R_ + 'tools')
import inv_common as C, drm_write as DW, drm_reloc as R, script_conv as SC, menu_dlc_probe as P
a = sys.argv; BL = a[a.index('--src') + 1]; SRC = C.base_dir(BL); outd = a[a.index('--out') + 1]; dry = '--dry' in a
SAFE = {0x02, 0x03, 0x04, 0x05, 0x06, 0x08, 0x0c, 0x0d, 0x0e, 0x0f, 0x10}
def ftable(data, reloc):
    W = SC.Walk(data, R.parse(reloc, 'le'), 'le').run()
    return {t + k * sz for nm, t, n, sz in W.arrays if nm == 'funcs' for k in range(n)}
gb, src = C.pc_generalbank()
NAT = {}
for s in gb:
    if s.type != 8 or not s.data: continue
    try: pkg, nat, size = P.script_info({'data': s.data, 'reloc': s.reloc}, 'le')
    except Exception: continue
    if nat == 'achievement': NAT[s.id] = ftable(s.data, s.reloc)
assert len(NAT) == 1, NAT
def instructions(d, rel):
    W = SC.Walk(d, rel, '<').run(); it = dict(rel.internal); res = []
    for name, t, n, sz in W.arrays:
        if name != 'funcs': continue
        for k in range(n):
            ct = it.get(t + k * sz + 0x18)
            if ct is None: continue
            cn = struct.unpack_from('<I', d, ct - 4)[0]; ins = []; j = 0
            while j < cn:
                o = ct + 4 * j; op = struct.unpack_from('<I', d, o)[0] >> 24
                ex = SC.Walk.EXTRA.get(op, 1 if op == P.PUSHF else 0); ins.append((o, op, ex)); j += 1 + ex
            res.append(ins)
    return res
def calls(D):
    out = []
    for si, s in enumerate(D.sections):
        if s.type != 8 or not s.data: continue
        d = bytes(s.data); rel = R.parse(bytes(s.reloc), 'le'); ext = {so: (ti, do) for ti, so, do in rel.external}
        for ins in instructions(d, rel):
            for i, (o, op, ex) in enumerate(ins):
                if ex < 1 or o + 4 not in ext: continue
                ti, do = ext[o + 4]; t = D.sections[ti]
                if t.type != 8 or t.id not in NAT or do in NAT[t.id] or op != 0x65: continue
                j = i - 1
                while j >= 0 and ins[j][1] != 0x00: j -= 1
                assert j >= 0, (s.id, hex(o))
                seq = ins[j + 1:i + 1]; ops = [q[1] for q in seq[:-1]]
                assert 0x09 not in ops and all(q in SAFE for q in ops), (s.id, hex(o), ops)
                out.append((si, s.id, ins[j][0], [q[0] + 4 * e for q in seq for e in range(q[2] + 1)], do))
    return out
outs = []; total = 0
for rel_, path in C.files(BL):
    raw = open(path, 'rb').read(); D = DW.read(raw, 'le'); cs = calls(D)
    if not cs: continue
    for si, sid, mk, words, do in cs:
        s = D.sections[si]; d = bytearray(s.data); marker = struct.unpack_from('<I', d, mk)[0]; assert marker >> 24 == 0
        for w in words: struct.pack_into('<I', d, w, marker)
        r = R.parse(bytes(s.reloc), 'le'); ws = set(words)
        r.external = [x for x in r.external if x[1] not in ws]; r.internal = [x for x in r.internal if x[0] not in ws]
        r.idref = [x for x in r.idref if x[1] not in ws]; r.idref_a = [x for x in r.idref_a if x[1] not in ws]
        s.data = bytes(d); s.reloc = R.write(r, 'le')
        print('%-34s script %d: chiamata achievement +%#x neutralizzata (%d parole)' % (rel_, sid, do, len(words))); total += 1
    o_ = D.write('le')
    if raw[:4] == b'CDRM': o_ = DW.cdrm_encode(o_, 'le')
    D2 = DW.read(o_, 'le'); assert not calls(D2), rel_
    D0 = DW.read(raw, 'le'); assert len(D0.sections) == len(D2.sections)
    changed = {cs_[0] for cs_ in cs}
    for i, (x, y) in enumerate(zip(D0.sections, D2.sections)):
        if i not in changed: assert (x.type, x.id, x.data, x.reloc) == (y.type, y.id, y.data, y.reloc), (rel_, i)
        else: assert len(x.data) == len(y.data)
    outs.append((rel_, o_))
print('chiamate', total, 'file', len(outs))
if not dry:
    os.makedirs(outd, exist_ok=True)
    for rel_, o_ in outs: open(os.path.join(outd, rel_), 'wb').write(o_)
    with open(os.path.join(outd, 'md5.txt'), 'w', newline='\n') as fo:
        fo.write(''.join('%s  %s\n' % (hashlib.md5(o_).hexdigest(), rel_) for rel_, o_ in outs))
