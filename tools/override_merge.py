"""PC versions of BASE-GAME DRMs that the DLC overrides (g_pda.drm, camerashakes.drm), safe for the base game.

A file in <gamedir>\\mods\\ overrides the base file for the WHOLE game, so it must keep everything the PC runtime
version has (PC patch.000 fixes included) and add only the DLC edits:

  X  = Xbox base version (layer1/2)            P = PC runtime version (patch.000 if present, else bigfile)
  D  = DLC Xbox version (pack10 / pack11)       output layout = D's section order (+ PC-only sections appended)

  per D section:
    'pc_same'   identical (normalised hash) to an X section matched to a P section (generic_ids.section_matches on
                the X<->P pair, any type incl. textures/waves/shaders/materials) -> P's bytes, external relocs re-targeted
    'convert:*' changed or DLC-new -> dlc_generic.convert_drm route (pc_copy / template / learned convert; media via
                assemble_dlc.make_media: textures, material_dlc, silent waves)
  P sections that have no X counterpart (PC-patch additions, e.g. script 20091 in patch g_pda) are appended, so the PC
  patch fixes that reference them keep working.  X sections absent from D (DLC removed them) are dropped (D wins).
  Report: per-route counts + the CONFLICTS = sections changed by BOTH the PC patch (P != convert(X)) and the DLC
  (the DLC version is used, the PC fix in that section is lost).

Self-test (`selftest`): D := X  -> output must equal P section-for-section (same multiset of (type,id,data,reloc)).
Usage: tools/venv/bin/python -I tools/override_merge.py selftest|build [g_pda.drm|camerashakes.drm] [pack10|pack11] [outdir]
"""
import sys, os, collections, hashlib, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R, drm_write as DW, dlc_generic as DG, generic_store
from generic_ids import section_matches
from generic_store import norm_hash
from archive import Archive
from names import crc
from drm import cdrm_decode, sections_with_data

B = '/path/to/'
C = B + 'Xenia-SteveRepack/Content/534307EC/00000002/'
SRC = {'xl1': (B + 'TombRaiderUnderworld_Patched/layer1.000', 'be'), 'xl2': (B + 'TombRaiderUnderworld_Patched/layer2.000', 'be'),
       'tu': (B + 'TombRaiderUnderworld_Patched/TitleUpdate.000', 'be'),
       'pcpatch': (B + 'tru-port/pc/patch.000', 'le'), 'pcbig': (B + 'tru-port/pc/bigfile.000', 'le'),
       'pack10': (C + '9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000', 'be'),
       'pack11': (C + '600A12643FCDAC84003E6E0DBD0A1A8F7DAE9DD153/pack11.000', 'be')}
_A = {}

def raw(src, name):
    path, e = SRC[src]
    a = _A.setdefault(src, Archive(path, e))
    r = [x for x in a.find(crc(('pc-w\\' if e == 'le' else 'xenon-w\\') + name)) if x['spec'] == 0xffffffff]
    return a.read(r[0]) if r else None

def load(srcs, name):
    for s in srcs:
        f = raw(s, name)
        if f is not None:
            e = SRC[s][1]; d = cdrm_decode(f, e)
            return s, DW.read(d, e), sections_with_data(d, e)[1]
    raise FileNotFoundError(name)

def merge(name, dlc_src, ids=None, store=None, selftest=False, media=None):
    xs_name, Xd, X = load(('tu', 'xl1', 'xl2'), name)
    ps_name, Pd, P = load(('pcpatch', 'pcbig'), name)
    if selftest: ds_name, Dd, D = xs_name, Xd, X
    else: ds_name, Dd, D = load((dlc_src,), name)
    ids = ids or DG.DlcIds(); store = store or generic_store.load()
    m = section_matches(X, P, ids.base)
    x2p = {i: j for i, j, _ in m if X[i]['type'] != 5}
    # textures: positional matches mis-pair reordered textures -> use the content-based id map (tools/tex_idmap.py)
    # sections the PC patch edited (size/reloc changed) are not fingerprint-matched: match them by the id map
    pidx = collections.Counter((p['type'], p['id']) for p in P)
    pby = {(p['type'], p['id']): j for j, p in enumerate(P) if pidx[p['type'], p['id']] == 1}
    used = set(x2p.values())
    for i, s in enumerate(X):
        if i in x2p: continue
        j = pby.get((s['type'], ids.base.get(s['type'], {}).get(s['id'])))
        if j is not None and j not in used and P[j]['type'] == s['type']:
            x2p[i] = j; used.add(j)
    xh = {}
    for i, s in enumerate(X):
        if i in x2p: xh.setdefault((s['type'], s['id'], norm_hash(s, X, 'be')), x2p[i])
    st = collections.Counter(); conflicts = []
    out = [None] * len(D); ext_targets = {}; route = {}
    todo = []
    for k, s in enumerate(D):
        j = xh.get((s['type'], s['id'], norm_hash(s, D, 'be')))
        if j is not None:
            p = P[j]
            out[k] = DW.Section(p['type'], p['id'], p['data'], p['reloc'], p['flags'], p['ver'], p['spec'])
            r = R.parse(p['reloc'], 'le')
            ext_targets[k] = [(P[si]['type'], P[si]['id']) for si, _, _ in r.external]
            route[k] = 'pc_same'
        else:
            todo.append(k)
    PB = None
    if ps_name == 'pcpatch' and raw('pcbig', name) is not None:
        PBs = sections_with_data(cdrm_decode(raw('pcbig', name), 'le'), 'le')[1]
        PB = {(q['type'], q['id']): norm_hash(q, PBs, 'le') for q in PBs}
    if todo:
        import assemble_dlc as A
        conv, rep = DG.convert_drm(D, ids, store, media or A.make_media('silence', 'dlc'))
        for k in todo:
            out[k] = conv[k]; route[k] = 'convert:' + rep[k][4]
            s = D[k]
            # conflict: section with a base id that the PC patch changed relative to the PC bigfile version
            xi = [i for i, x in enumerate(X) if (x['type'], x['id']) == (s['type'], s['id'])]
            if xi and xi[0] in x2p and PB is not None:
                pj = P[x2p[xi[0]]]
                if PB.get((pj['type'], pj['id'])) != norm_hash(pj, P, 'le'):
                    conflicts.append((s['type'], s['id'], pj['id']))
    have = {(s.type, s.id) for s in out}
    pmatched = set(x2p.values())
    extra = [j for j, p in enumerate(P) if j not in pmatched and (p['type'], p['id']) not in have]
    for j in extra:
        p = P[j]
        k = len(out)
        out.append(DW.Section(p['type'], p['id'], p['data'], p['reloc'], p['flags'], p['ver'], p['spec']))
        ext_targets[k] = [(P[si]['type'], P[si]['id']) for si, _, _ in R.parse(p['reloc'], 'le').external]
        route[k] = 'pc_only_appended'
    cnt = collections.Counter((s.type, s.id) for s in out)
    index_of = {(s.type, s.id): k for k, s in enumerate(out) if cnt[s.type, s.id] == 1}
    for k, tg in ext_targets.items():
        if not tg: continue
        rl = DG.retarget_ext(out[k].reloc, tg, index_of)
        if rl is None: raise ValueError('cannot retarget external relocs of section %d %s' % (k, tg))
        out[k].reloc = rl
    # shader libraries: assemble_dlc drops Xenos libs for converted materials; here every lib of D that was not
    # copied from P is a converted placeholder -> must not exist (D shaders are all identical to base in g_pda/camerashakes)
    for k, s in enumerate(out):
        st[(s.type, route[k])] += 1
    names = Dd.names.replace(b'xenon-w', b'pc-w')
    drm = DW.Drm(out, names, Dd.pad, Dd.ver, Dd.u0, Dd.u1)
    return drm, dict(route=route, routes=st, conflicts=conflicts, src=(xs_name, ps_name, ds_name), nsec=len(out), extra=len(extra), P=P)

def selftest(name):
    drm, rep = merge(name, None, selftest=True)
    P = rep['P']
    key = lambda t, i, d, r: hashlib.md5(bytes([t]) + i.to_bytes(4, 'little') + d + b'|' + r).hexdigest()
    a = collections.Counter(key(s.type, s.id, s.data, R.write(R.Reloc(*[getattr(R.parse(s.reloc, 'le'), f) if f != 'external' else
                                                                           [(0, so, do) for _, so, do in R.parse(s.reloc, 'le').external]
                                                                           for f in R.Reloc.__slots__]), 'le')) for s in drm.sections)
    b = collections.Counter(key(p['type'], p['id'], p['data'], R.write(R.Reloc(*[getattr(R.parse(p['reloc'], 'le'), f) if f != 'external' else
                                                                               [(0, so, do) for _, so, do in R.parse(p['reloc'], 'le').external]
                                                                               for f in R.Reloc.__slots__]), 'le')) for p in P)
    # external targets compared by (type,id)
    def ext_ids(secs, get):
        return collections.Counter((t, i, tuple(get(r))) for t, i, r in secs)
    ea = ext_ids([(s.type, s.id, s.reloc) for s in drm.sections],
                 lambda r: [(drm.sections[si].type, drm.sections[si].id, so, do) for si, so, do in R.parse(r, 'le').external])
    eb = ext_ids([(p['type'], p['id'], p['reloc']) for p in P],
                 lambda r: [(P[si]['type'], P[si]['id'], so, do) for si, so, do in R.parse(r, 'le').external])
    print(name, 'selftest: output %d sections, PC %d; content multiset equal: %s; ext targets equal: %s; routes %s' % (
        len(drm.sections), len(P), a == b, ea == eb, dict(rep['routes'])))
    return a == b and ea == eb

if __name__ == '__main__':
    mode = sys.argv[1]
    names = [a for a in sys.argv[2:] if a.endswith('.drm')] or ['g_pda.drm', 'camerashakes.drm']
    if mode == 'selftest':
        for n in names: selftest(n)
    else:
        packs = [a for a in sys.argv[2:] if a.startswith('pack')] or ['pack11']
        outdir = ([a for a in sys.argv[2:] if '/' in a] or [os.path.join(DG.W, 'overrides')])[0]
        os.makedirs(outdir, exist_ok=True)
        for n in names:
            for pk in packs:
                try:
                    drm, rep = merge(n, pk)
                except FileNotFoundError:
                    print(n, pk, 'not in pack'); continue
                data = DW.cdrm_encode(drm.write('le'), 'le')
                fn = os.path.join(outdir, pk + '_' + n)
                open(fn, 'wb').write(data)
                print(n, pk, 'src', rep['src'], 'sections', rep['nsec'], 'pc_only appended', rep['extra'], 'bytes', len(data))
                for k, v in sorted(rep['routes'].items(), key=str): print('   ', k, v)
                print('    CONFLICTS (changed by PC patch AND DLC; DLC version used):', rep['conflicts'])
