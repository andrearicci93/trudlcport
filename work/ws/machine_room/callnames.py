"""callnames.py - (20/11/2026) solo lettura. Per gli script indicati di un DRM DLC: ogni istruzione con operando la cui parola ha
una rilocazione esterna verso un altro script (chiamata a funzione: l'operando punta a una voce Function di 28 B) -> nome della
funzione chiamata (Function+0 -> Prototype, Prototype+8 = simbolo del nome) sul PC e sull'Xbox. Il simbolo Xbox e' tradotto con
la mappa simboli (idmap 100, poi spostamento DLC +480 oltre 16348): se il nome PC != nome Xbox tradotto la chiamata va a
un'altra funzione. Allinea le istruzioni PC/Xbox per posizione (stessa sezione, stessa taglia).
uso: callnames.py BASELINE FILE.drm SID..."""
import sys, struct, json, collections
sys.path.insert(0, '/path/to/trudlcport/work/ws/lukas_check/inv'); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW, drm_reloc as R, script_conv as SC, menu_dlc_probe as P
BL, F = sys.argv[1:3]; SIDS = list(map(int, sys.argv[3:]))
SYM = {int(k): v for k, v in json.load(open('/path/to/trudlcport/work/generic/idmap.json'))['100'].items()}
def xsym(s): return SYM.get(s, s + 480 if s > 16348 else None)
PD = DW.read(open('/path/to/trudlcport/work/baseline/%s/mods/%s' % (BL, F), 'rb').read(), 'le'); XD = DW.read(C.xbox(F), 'be')
def instr(sec, e):
    E = '>' if e == 'be' else '<'; d = bytes(sec.data); r = R.parse(bytes(sec.reloc), e)
    W = SC.Walk(d, r, e).run(); out = []
    for nm, t, n, sz in W.arrays:
        if nm != 'code': continue
        j = 0
        while j < n:
            o = t + 4 * j; op = struct.unpack_from(E + 'I', d, o)[0] >> 24
            ex = SC.Walk.EXTRA.get(op, 1 if op == P.PUSHF else 0); out.append((o, op, ex)); j += 1 + ex
    return out
def fname(D, si, do, e):
    E = '>' if e == 'be' else '<'; t = D.sections[si]; d = bytes(t.data); it = dict(R.parse(bytes(t.reloc), e).internal)
    pr = it.get(do)
    if pr is None: return (t.id, do, None)
    return (t.id, do, struct.unpack_from(E + 'H', d, pr + 8)[0])
tot = collections.Counter()
for sid in SIDS:
    p = next(s for s in PD.sections if s.type == 8 and s.id == sid); x = next(s for s in XD.sections if s.type == 8 and s.id == sid)
    ip, ix = instr(p, 'le'), instr(x, 'be')
    ep = {so: (si, do) for si, so, do in R.parse(bytes(p.reloc), 'le').external}; ex_ = {so: (si, do) for si, so, do in R.parse(bytes(x.reloc), 'be').external}
    print('== script', sid, 'istruzioni PC/Xbox', len(ip), len(ix))
    for (o, op, e), (o2, op2, e2) in zip(ip, ix):
        if e < 1 or o + 4 not in ep: continue
        a = fname(PD, *ep[o + 4], 'le'); b = fname(XD, *ex_[o2 + 4], 'be') if o2 + 4 in ex_ else None
        want = xsym(b[2]) if b and b[2] is not None else None
        ok = a[2] is not None and want == a[2]
        tot['ok' if ok else 'DIVERSO'] += 1
        print('  %s +%#06x op%02x -> PC script %d +%#x sym %s | Xbox script %s +%s sym %s (atteso PC %s)' % ('  ' if ok else '!!', o, op, a[0], a[1], a[2], b and b[0], b and hex(b[1]), b and b[2], want))
print(dict(tot))
