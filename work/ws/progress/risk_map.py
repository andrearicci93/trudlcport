"""risk_map.py - parole a rischio nei DTP DLC senza precedente (modello assente nel base): per famiglia (w0 Xbox) e per file."""
import sys, os, collections, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import dtp_audit as DA, drm_write as DW, drm_reloc as R, dtpid_sweep as DS
def ph(xr): return hashlib.md5(repr(sorted(xr.internal)).encode()).hexdigest()[:10]
grp = collections.Counter()
for x, p, xb, pc, xr in DA.base_pairs(): grp[(len(xb['data']), ph(xr))] += 1
st, ids = DS.ctx(); basep = set(ids.base[7].values())
fam = collections.Counter(); famwords = collections.Counter(); famdtp = collections.Counter(); byfile = collections.Counter(); tot_risk = 0; tot_cov = 0; seen = set()
for rel, path in sorted(DA.overlay(['baseline/B32/mods'], None).items()):
    xs = DA.xsecs(rel)
    if xs is None: continue
    try: D = DW.read(open(path, 'rb').read(), 'le')
    except Exception: continue
    for x, i in DA.section_pairs(xs, D):
        sec = D.sections[i]
        if x['type'] != 7 or len(sec.data) != len(x['data']) or sec.id in basep: continue
        if (rel.split('/')[-1], sec.id) in seen: continue
        seen.add((rel.split('/')[-1], sec.id))
        xd = x['data']; xr = R.parse(x['reloc'], 'be'); sl = set(xr.pointer_offsets()) | set(xr.id_offsets())
        risk = 0
        for o in range(0, len(xd) - 3, 4):
            w = xd[o:o + 4]
            if o in sl or w == b'\0\0\0\0' or w == w[::-1]: continue
            risk += 1
        k = (len(xd), ph(xr)); covered = grp.get(k, 0) >= 2
        f = xd[:4].hex()
        if covered: tot_cov += risk
        else: tot_risk += risk; famwords[f] += risk; famdtp[f] += 1; byfile[rel] += risk
print('DTP DLC-nuovi (id non presente nel base), parole a rischio: coperte da modello', tot_cov, '| NON coperte', tot_risk)
print('--- famiglie (w0 Xbox) delle parole NON coperte')
for f, n in famwords.most_common(14): print('%8d parole  %5d DTP  w0=%s' % (n, famdtp[f], f))
print('--- file con piu parole NON coperte')
for r, n in byfile.most_common(14): print('%8d %s' % (n, r))
