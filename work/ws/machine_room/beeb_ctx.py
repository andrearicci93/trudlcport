"""beeb_ctx.py - (19/11/2026) solo lettura. Nel base (work/generic/store.pkl, xb_store/pc_store, id Xbox->PC da idmap):
per ogni marcatore beebbeeb in un DTP, classe (s32/raw/s16/altro) delle parole da -8 a +0x24 rispetto al marcatore.
Serve a capire come il PC tiene la parola dopo beebbeeb (in dlc_fx_goo_machine_column_core DTP 26321 +0xfc e' rimasta raw)."""
import sys, pickle, collections
sys.path.insert(0, '/path/to/trudlcport/work/ws/lukas_check/inv'); import inv_common as C
S = pickle.load(open('/path/to/trudlcport/work/generic/store.pkl', 'rb')); im = C.idmap().get(7, {})
def cls(x, p):
    if x == p: return 'pal' if x == x[::-1] else 'raw'
    if p == x[::-1]: return 's32'
    if p == x[1::-1] + x[:1:-1]: return 's16'
    return 'altro'
B = bytes.fromhex('beebbeeb'); res = collections.defaultdict(collections.Counter); ex = collections.defaultdict(list); nd = 0
for (t, xid), xs in S['xb_store'].items():
    if t != 7: continue
    p = S['pc_store'].get((7, im.get(xid, xid)))
    if not p or len(p['data']) != len(xs['data']): continue
    xd, pd = xs['data'], p['data']; o = xd.find(B); hit = False
    while o >= 0:
        if o % 4 == 0:
            hit = True
            for k in range(-8, 0x28, 4):
                if 0 <= o + k and o + k + 4 <= len(xd):
                    c = cls(xd[o + k:o + k + 4], pd[o + k:o + k + 4]); res[k][c] += 1
                    if k == 4 and c != 'pal' and len(ex[c]) < 6: ex[c].append((xid, hex(o), xd[o:o + 0x20].hex(' ', 4), pd[o:o + 0x20].hex(' ', 4)))
        o = xd.find(B, o + 1)
    nd += hit
print('DTP base con beebbeeb:', nd)
for k in sorted(res): print('%+#05x' % k, dict(res[k]))
for c, l in ex.items():
    for e in l: print(c, *e)
