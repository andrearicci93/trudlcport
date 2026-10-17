"""hintwire verify (sola lettura): locals (id nuovi in 6 lingue, 0 id installati cambiati), DRM (solo i byte previsti), testo risolto."""
import sys, os, json, struct, hashlib, glob
T = '/path/to/trudlcport/'
sys.path.insert(0, T + 'tools')
import locals as L, drm_write as DW, drm as D1
H = T + 'work/ws/hintwire/'; OUT = H + 'out/'
J = json.load(open(T + 'work/ws/hints/out/locmap_dlc1_xbox_to_pc.json')); Q = {int(k): v for k, v in J['Q'].items()}
SH = {int(k): v for k, v in json.load(open(T + 'work/generic/locals/locmap_xbox_to_pc.json'))['map'].items()}
rep = json.load(open(H + 'report.json'))
LANG = {1: 'EN', 2: 'FR', 4: 'DE', 8: 'IT', 16: 'ES', 32: 'NL?'}
ok = True
print('== locals')
for suf in (1, 2, 4, 8, 16, 32):
    new = L.parse(open(OUT + 'local/locals.bin_%03d' % suf, 'rb').read(), 'le')
    old = L.parse(open(T + 'work/dlc_images/local/mods/local/locals.bin_%03d' % suf, 'rb').read(), 'le')
    n0 = len(old[1]); same = all(new[1][i] == old[1][i] and (new[2][i] == 0) == (old[2][i] == 0) for i in range(n0))
    miss = [x for x, q in Q.items() if new[2][q] == 0 or not new[1][q]]
    print('lang %2d n_old %d n_new %d installed ids unchanged %s | new ids present %d/77 (missing/empty: %s)' % (suf, n0, len(new[1]), same, 77 - len(miss), miss))
    ok &= same and n0 + 77 == len(new[1])
print('== DRM')
for r in rep:
    srcraw = D1.cdrm_decode(open(r['src'], 'rb').read(), 'le'); newraw = D1.cdrm_decode(open(OUT + r['rel'], 'rb').read(), 'le')
    d = [i for i in range(len(srcraw)) if srcraw[i] != newraw[i]]
    Dn = DW.read(newraw, 'le'); Do = DW.read(srcraw, 'le')
    other = sum(1 for a, b in zip(Do.sections, Dn.sections) if (a.type, a.id, a.ver, a.flags, a.spec, a.pad, a.reloc) != (b.type, b.id, b.ver, b.flags, b.spec, b.pad, b.reloc))
    hdr = (Do.hdr if hasattr(Do, 'hdr') else None, Do.names, Do.pad) == (None if not hasattr(Dn, 'hdr') else Dn.hdr, Dn.names, Dn.pad)
    exp = {}
    off = 0
    # decoded file offset of each changed byte -> (section, word)
    print('%-26s src=%-9s changed bytes %d  meta/reloc diffs %d  header/names same %s  words %s' % (r['rel'], r['kind'], len(d), other, hdr, [(w[0], w[1], w[2], w[4]) for w in r['words']]))
    ok &= other == 0 and len(d) == r['n_sections']
print('ALL OK' if ok else 'PROBLEMS')
print('== testo risolto (prima = id condiviso, dopo = id DLC1)')
for x in (1290, 1291, 1326):
    for suf in (1, 2, 4, 8, 16, 32):
        new = L.parse(open(OUT + 'local/locals.bin_%03d' % suf, 'rb').read(), 'le')[1]
        old = L.parse(open(T + 'work/dlc_images/local/mods/local/locals.bin_%03d' % suf, 'rb').read(), 'le')[1]
        print('x=%d [%s] prima id %d: %r | dopo id %d: %r' % (x, LANG[suf], SH[x], old[SH[x]][:70].decode(), Q[x], new[Q[x]][:90].decode()))
