"""hintwire build: ripunta le parole LOC dei DRM DLC1 (rc, altrimenti installato) ai 77 id appesi del candidato hints.
Sola lettura sulle sorgenti; scrive solo in work/ws/hintwire/out/. Uso: tools/venv/bin/python -I work/ws/hintwire/build.py"""
import sys, os, csv, json, struct, hashlib, shutil, pickle, collections
T = '/path/to/trudlcport/'
sys.path.insert(0, T + 'tools'); sys.path.insert(0, T + 'work/ws/hintwire')
import drm_write as DW, drm as D1, generic_learn as G, script_learn as SL, drm_reloc as R, dlc_generic as DG
import dtpid_sweep as DS
from soundplex_fix import xsecs_of
import scan as SC
H = T + 'work/ws/hintwire/'; OUT = H + 'out/'
J = json.load(open(T + 'work/ws/hints/out/locmap_dlc1_xbox_to_pc.json'))
Q = {int(k): v for k, v in J['Q'].items()}; VAR = set(Q)
SH = {int(k): v for k, v in json.load(open(T + 'work/generic/locals/locmap_xbox_to_pc.json'))['map'].items()}
st, ids = DS.ctx(); ids.local = {}

class Ids2:      # same as ids but the 77 DLC1 variant indices resolve to the appended ids
    def __init__(s, ids): s.ids = ids
    def __call__(s, t, x): return Q[x] if t == 101 and x in Q else s.ids(t, x)
    def __getattr__(s, a): return getattr(s.ids, a)

def fresh(xs, k, labs, ids_, rec=None):
    s = xs[k]
    kmap = {w: (key, ck) for w, key, ck in G.word_keys(len(s['data']), labs[k])}
    T7 = DG.table()
    def fb(w, xw):
        c, _ = G.lookup(T7, *kmap[w])
        return c if c is not None else ('raw' if G.is_text(xw) and xw != xw[::-1] else 's32')
    return SL.convert(s['data'], R.parse(s['reloc'], 'be'), ids_, SL.table(), fallback=fb)[0]

def process(rel, path, kind):
    raw_file = open(path, 'rb').read()
    cdrm = raw_file[:4] == b'CDRM'
    raw = D1.cdrm_decode(raw_file, 'le') if cdrm else raw_file
    rt_ok = (DW.cdrm_encode(DW.read(raw, 'le').write('le'), 'le') if cdrm else DW.read(raw, 'le').write('le')) == raw_file
    D = DW.read(raw, 'le'); xs = xsecs_of(rel)
    if xs is None: return None
    labs = None; patches = []; sweep = []
    pcsecs = collections.defaultdict(list)
    for j, s in enumerate(D.sections): pcsecs[(s.type, len(s.data))].append(j)
    used = set()
    for k, s in enumerate(xs):
        # --- position-agnostic sweep, every type: candidate targets = same type + same length + (index k or mapped id)
        nid = ids(s['type'], s['id']) if s['type'] not in (0, 13) else None
        cands = [j for j in pcsecs.get((s['type'], len(s['data'])), []) if j == k or D.sections[j].id == nid]
        xd = s['data']
        for j in cands:
            pd = bytes(D.sections[j].data)
            for o in range(0, len(xd) - 3, 2):
                x16 = struct.unpack_from('>H', xd, o)[0]
                if 1284 <= x16 <= 1375 and x16 in SH and struct.unpack_from('<H', pd, o)[0] == (SH[x16] & 0xffff) and SH[x16] != x16:
                    sweep.append((s['type'], s['id'], j, o, '16', x16, x16 in VAR))
                if o % 4 == 0:
                    x32 = struct.unpack_from('>I', xd, o)[0]
                    if 1284 <= x32 <= 1375 and struct.unpack_from('<I', pd, o)[0] == SH[x32] and SH[x32] != x32:
                        sweep.append((s['type'], s['id'], j, o, '32', x32, x32 in VAR))
        if s['type'] != 8: continue
        if labs is None: labs = G.drm_labels(xs, 'be')
        SC.Rec.log = []; SC.Rec.cur = None
        P = SC.Proxy(ids)
        f1 = fresh(xs, k, labs, P)
        hits = [(w, x, r) for w, x, r in SC.Rec.log if x in VAR]
        if not hits: continue
        f2 = fresh(xs, k, labs, Ids2(ids))
        diffw = [w for w in range(0, len(f1), 4) if f1[w:w + 4] != f2[w:w + 4]]
        assert sorted(diffw) == sorted({w for w, _, _ in hits}), (rel, k, diffw, hits)
        tg = [j for j in cands if j not in used and all(bytes(D.sections[j].data)[w:w + 4] == f1[w:w + 4] for w in diffw)]
        full = [j for j in tg if bytes(D.sections[j].data) == f1]
        if len(tg) != 1: patches.append(dict(k=k, status='AMBIGUOUS_OR_NONE', cands=cands, tg=tg)); continue
        j = tg[0]; used.add(j)
        patches.append(dict(k=k, j=j, sid=s['id'], words=[(w, x, r, f1[w:w + 4].hex(), f2[w:w + 4].hex()) for w, x, r in hits], full_equal=bool(full), f2=f2, diffw=diffw))
    return D, raw_file, raw, cdrm, rt_ok, patches, sweep

if __name__ == '__main__':
    src = SC.sources(); res = {}; os.makedirs(OUT, exist_ok=True)
    allsweep = []; report = []
    for rel in sorted(src):
        path, kind = src[rel]
        if rel.startswith('streamgroups/') or rel.startswith('cinstream/'): pass
        r = process(rel, path, kind)
        if r is None: continue
        D, raw_file, raw, cdrm, rt_ok, patches, sweep = r
        for sw in sweep: allsweep.append((rel,) + sw)
        if not rt_ok: print('WARN roundtrip not byte-identical:', rel)
        real = [p for p in patches if p.get('j') is not None]
        bad = [p for p in patches if p.get('j') is None]
        if bad: print('PROBLEM', rel, bad)
        if not real: continue
        for p in real:
            sec = D.sections[p['j']]; b = bytearray(sec.data)
            for w in p['diffw']: b[w:w + 4] = p['f2'][w:w + 4]
            sec.data = bytes(b)
        newraw = D.write('le'); newfile = DW.cdrm_encode(newraw, 'le') if cdrm else newraw
        d = os.path.join(OUT, os.path.dirname(rel)); os.makedirs(d, exist_ok=True)
        open(OUT + rel, 'wb').write(newfile)
        # byte-identity check on decoded raw: only the patched words differ
        diff = [i for i in range(len(raw)) if raw[i] != newraw[i]] if len(raw) == len(newraw) else None
        report.append(dict(rel=rel, kind=kind, src=path, roundtrip=rt_ok, n_sections=len(real), full_equal=[p['full_equal'] for p in real],
                           sections=[(p['k'], p['j'], p['sid']) for p in real], words=[w for p in real for w in p['words']], diff_bytes=len(diff) if diff is not None else None,
                           md5_src=hashlib.md5(raw_file).hexdigest(), md5_new=hashlib.md5(newfile).hexdigest()))
        print('%-40s %-9s secs %d diff bytes %s roundtrip %s full_equal %s' % (rel, kind, len(real), report[-1]['diff_bytes'], rt_ok, report[-1]['full_equal']))
    json.dump(report, open(H + 'report.json', 'w'), indent=1, default=str)
    pickle.dump(allsweep, open(H + 'sweep.pkl', 'wb'))
    print('sweep hits (var_x or not):')
    c = collections.Counter((s[0], s[1], s[6], s[7]) for s in allsweep)
    for s in allsweep: print('  ', s)
