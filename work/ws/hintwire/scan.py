"""hintwire scan (sola lettura): posizioni delle parole LOC (classe 101) nei type-8 dei DRM DLC1, via script_learn.convert strumentato.
Per ogni DRM: sorgente = work/mods_dlc1_rc se esiste, altrimenti installed_effective.tsv. Verifica che il valore nel file == risultato della conversione fresca."""
import sys, os, csv, struct, json, pickle, collections
T = '/path/to/trudlcport/'
sys.path.insert(0, T + 'tools')
import drm_write as DW, generic_learn as G, script_learn as SL, drm_reloc as R
import dtpid_sweep as DS
from soundplex_fix import xsecs_of
H = T + 'work/ws/hintwire/'
RC = T + 'work/mods_dlc1_rc/'

def sources():
    src = {}
    for r in csv.DictReader(open(T + 'work/ws/rebuild/installed_effective.tsv'), delimiter='\t'):
        if r['relpath'].lower().endswith('.drm'): src[r['relpath']] = (r['abs_path'], 'installed')
    for dp, _, fs in os.walk(RC):
        for f in fs:
            if f.lower().endswith('.drm'):
                rel = os.path.relpath(os.path.join(dp, f), RC).replace(os.sep, '/')
                src[rel] = (os.path.join(dp, f), 'rc')
    return src

class Rec:
    cur = None
    log = []
class Proxy:
    def __init__(s, ids): s.ids = ids
    def __call__(s, t, x):
        r = s.ids(t, x)
        if t == 101: Rec.log.append((Rec.cur, x, r))
        return r
    def __getattr__(s, a): return getattr(s.ids, a)

_orig = SL.apply_word
def _aw(xw, c, ids):
    Rec.cur = sys._getframe(1).f_locals.get('w')
    return _orig(xw, c, ids)
SL.apply_word = _aw

def scan(rel, path, ids, labs_cache=None):
    xs = xsecs_of(rel)
    if xs is None: return None
    D = DW.read(open(path, 'rb').read(), 'le')
    labs = None; res = []
    P = Proxy(ids)
    for k, s in enumerate(xs):
        if s['type'] != 8: continue
        if k >= len(D.sections) or D.sections[k].type != 8 or len(D.sections[k].data) != len(s['data']):
            res.append(dict(k=k, status='unpaired')); continue
        if labs is None: labs = G.drm_labels(xs, 'be')
        kmap = {w: (key, ck) for w, key, ck in G.word_keys(len(s['data']), labs[k])}
        def fb(w, xw, kmap=kmap):
            c, _ = G.lookup(SL.table(), *kmap[w]) if False else (None, None)
            return 'raw' if G.is_text(xw) and xw != xw[::-1] else 's32'
        # same fallback as dlc_generic.convert_drm (needs the generic table T)
        import dlc_generic as DG
        T7 = DG.table()
        def fb(w, xw, kmap=kmap):
            c, _ = G.lookup(T7, *kmap[w])
            return c if c is not None else ('raw' if G.is_text(xw) and xw != xw[::-1] else 's32')
        Rec.log = []; Rec.cur = None
        rel_b = R.parse(s['reloc'], 'be')
        data, W = SL.convert(s['data'], rel_b, P, SL.table(), fallback=fb)
        idt = [t for t in rel_b.id_offsets().values() if t == 101]
        pc = bytes(D.sections[k].data)
        for w, x, r in Rec.log:
            res.append(dict(k=k, sid=s['id'], w=w, x=x, loc=r, fresh=data[w:w + 4].hex(), file=pc[w:w + 4].hex(),
                            xb=s['data'][w:w + 4].hex(), match=data[w:w + 4] == pc[w:w + 4], idreloc=len(idt)))
    return res

if __name__ == '__main__':
    st, ids = DS.ctx(); ids.local = {}
    src = sources(); out = {}
    for rel in sorted(src):
        path, kind = src[rel]
        try: r = scan(rel, path, ids)
        except Exception as e: out[rel] = ('ERR', repr(e)); print(rel, 'ERR', repr(e)); continue
        if r is None: continue
        out[rel] = (kind, path, r)
        n = [x for x in r if 'w' in x]
        hit = [x for x in n if 1284 <= x['x'] <= 1375]
        print('%-55s %-9s loc words %3d  in1284-1375 %3d  unpaired %d  mismatch %d' % (rel, kind, len(n), len(hit), sum(1 for x in r if x.get('status')), sum(1 for x in n if not x['match'])))
    pickle.dump(out, open(H + 'scan.pkl', 'wb'))
