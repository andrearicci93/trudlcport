"""refs_scan.py - static reference / shared-section audit of the INSTALLED DLC1 overlay (texture, material, mesh, name refs).

Overlay (low -> high, later wins per relative file name):
  vm_mods_expected < fix12 < fix14 < glitchfix < next < fix16 < current < current_webs < fix18 < fix18_awf_extra < fix20
  (+ chain_aim/mods_chainfix_min raft_bridge).   Non-DRM payloads (image/*.raw, local/, music, audio) are checked by name only.

Loadable universe for a DLC DRM D (what the engine can resolve an id-ref against):
  L0 D itself ; L1 D's dependency closure (names block, resolved in overlay first then PC) ; L2 other overlay DRMs ;
  L3 PC base (bigfile.000 + patch.000, patch wins by name) ; none = unresolvable.

Rules (each rule id = one reusable scan; numbers calibrated on PC base DRMs with `calibrate`):
  R01 idref_unresolved     id-ref (reloc kind A / 4) whose (type,id) is in no loadable DRM          (crash)
  R02 idref_foreign        id-ref resolved only outside D + deps closure (L2/L3 not in closure)     (visible/crash, see calib)
  R03 mat_no_shader        material (type 10) whose shader id-ref (type 9) is unresolved / not a PC-valid shader
  R04 mat_no_texture       material texture id-ref unresolved
  R05 mesh_no_material     mesh (type 12, magic) with no material id-ref / unresolved material
  R06 tex_invalid          texture header not PCD9 / fmt not DXT1,DXT3,DXT5,A8R8G8B8 / size != computed from dims+mips / mips > max
  R07 tex_xbox_left        texture still X360 header (not converted)
  R08 tex_dup_content      identical texture payload under several ids inside the overlay (memory only)
  R09 shared_conflict      same (type,id) in D and in a co-loadable DRM (closure/PC) with different content
  R10 shared_tex_mismatch  as R09 for textures, with fmt/dims/mips differing (header incoherence vs base equivalent)
  R11 dep_missing          dependency name not resolvable
  R12 name_unresolved      streamgroup / image / music / cinstream / unit name strings not in overlay nor PC
usage:
  tools/venv/bin/python -I tools/refs_scan.py cache           build work/ws/refs/cache/pcu.pkl (PC universe), ovl.pkl (overlay)
  tools/venv/bin/python -I tools/refs_scan.py calibrate       run R01/R02/R09 on PC base DRMs (expected 0 findings = rule sound)
  tools/venv/bin/python -I tools/refs_scan.py scan [--out DIR] run on overlay -> refs.json
"""
import sys, os, struct, json, hashlib, pickle, collections, zlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drm_write as DW, drm_reloc as R

ROOT = os.path.normpath(os.path.join(HERE, '..'))
WK = os.path.join(ROOT, 'work')
REFS = os.path.join(WK, 'ws', 'refs')
CACHE = os.path.join(REFS, 'cache')
OVERLAY_DIRS = ['vm_mods_expected', 'mods_fix12', 'mods_fix14', 'mods_glitchfix', 'mods_next', 'mods_fix16', 'mods_current',
                'mods_current_webs', 'mods_fix18', 'mods_fix18_awf_extra', 'mods_fix20', 'chain_aim/mods_chainfix_min',
                'menu_dlc/B']
# (dir, prefix inside mods\\, path filter)   - image/ and local/ are separate mods\\ subfolders
EXTRA_DIRS = [('dlc_images/image', 'image/'), ('dlc_images/local/mods/local', 'local/')]
OVERLAY_DIRS += [d for d in os.environ.get('REFS_EXTRA', '').split(':') if d]    # e.g. ws/refs/out to test fixes on top
NOT_INSTALLED = {'g_pda.drm'}          # vm_mods_expected/g_pda.drm was removed from the VM (crashes base game)
IMAGE_SKIP = ()
RESIDENT = ['generalbank.drm']          # always loaded (calibrated: PC texture refs to id 2.. resolve there)
TEX_FMT = {0x31545844: 'DXT1', 0x33545844: 'DXT3', 0x35545844: 'DXT5', 0x15: 'ARGB'}

def norm(rel): return rel.replace('\\', '/').lower()

def overlay_files(dirs=OVERLAY_DIRS, extra=EXTRA_DIRS):
    out = {}
    def walk(d, prefix):
        d = d if os.path.isabs(d) else os.path.join(WK, d)
        if not os.path.isdir(d): return
        for r, _, fs in os.walk(d):
            for f in fs:
                p = os.path.join(r, f)
                out[norm(prefix + os.path.relpath(p, d))] = p
    for d in dirs: walk(d, '')
    for d, pre in extra: walk(d, pre)
    for k in list(out):
        if k in NOT_INSTALLED or k.endswith('md5.txt') or k.endswith('.md') or k.startswith('patch_log'): out.pop(k)
    return out

# ------------------------------------------------------------------------------------------------ DRM summary
def summarize(raw, endian='le'):
    """-> dict(deps, secs=[(type,id,size,datamd5,ver,flags,spec,normhash)], refs=[(secidx, idtype, idval, off)], ext=[(secidx,tgt,so,do)],
              tex={secidx: PCD9 header tuple}, mesh=[secidx of Mesh-magic sections])
    normhash = md5(internal relocs, external relocs as (target type,id), id-refs, data): section-index independent, ver ignored."""
    D = DW.read(raw, endian)
    deps = [x.decode('latin1').lower() for x in D.names.split(b'\0') if x]
    rels = []
    for s in D.sections:
        try: rels.append(R.parse(s.reloc, endian) if s.reloc else None)
        except Exception: rels.append(None)
    secs = []; refs = []; ext = []; tex = {}; mesh = []; tex_bad = []; shader_bad = []; mats = {}; meshinfo = {}; deep_err = []
    for k, s in enumerate(D.sections):
        r = rels[k]
        e = tuple((D.sections[si].type, D.sections[si].id, so, do) for si, so, do in r.external if si < len(D.sections)) if r else ()
        nh = hashlib.md5(repr((r.internal, e, r.idref, r.idref_a) if r else (s.reloc,)).encode() + s.data).hexdigest()
        secs.append((s.type, s.id, len(s.data), hashlib.md5(s.data).hexdigest(), s.ver, s.flags, s.spec, nh))
        if r:
            for t, o in list(r.idref) + list(r.idref_a):
                if o + 4 <= len(s.data): refs.append((k, t, struct.unpack_from('<I', s.data, o)[0], o))
            for si, so, do in r.external: ext.append((k, si, so, do))
        if s.type == 5 and len(s.data) >= 24:
            tex[k] = struct.unpack_from('<4sIIIHHBBH', s.data, 0)
        if s.type == 12 and s.data[0x10:0x14] == b'Mesh': mesh.append(k)
        try: _deep(k, s, r, tex_bad, shader_bad, mats, meshinfo)
        except Exception as ex: deep_err.append((k, s.type, repr(ex)[:80]))
    return dict(deps=deps, secs=secs, refs=refs, ext=ext, tex=tex, mesh=mesh, tex_bad=tex_bad, shader_bad=shader_bad, mats=mats,
                meshinfo=meshinfo, deep_err=deep_err)


def tex_expected(fmt, w, h, mips, flags):
    """PC PCD9 data size: levels = mips+1, DXT blocks of 4x4 (min 1 block), A8R8G8B8 4 B/texel; cubemap (flags 0x8000) x6."""
    bs = 8 if fmt == 0x31545844 else 16
    tot = 0
    for l in range(mips + 1):
        wl, hl = max(1, w >> l), max(1, h >> l)
        tot += 4 * wl * hl if fmt == 0x15 else bs * max(1, (wl + 3) // 4) * max(1, (hl + 3) // 4)
    return tot * (6 if flags & 0x8000 else 1)

def _deep(k, s, r, tex_bad, shader_bad, mats, meshinfo):
    d = s.data
    if s.type == 5:
        if len(d) < 24: tex_bad.append((k, 'short')); return
        mg, fmt, dsz, pal, w, h, bpp, mips, fl = struct.unpack_from('<4sIIIHHBBH', d, 0)
        if mg == b'X360' or d[:4] == b'063X': tex_bad.append((k, 'xbox_header')); return
        if mg != b'PCD9': tex_bad.append((k, 'magic_%r' % mg)); return
        if fmt not in TEX_FMT: tex_bad.append((k, 'fmt_0x%x' % fmt)); return
        if fmt == 0x33545844: tex_bad.append((k, 'dxt3'))
        if dsz != len(d) - 24: tex_bad.append((k, 'datasize_hdr'))
        if mips > max(w, h).bit_length() - 1: tex_bad.append((k, 'mips_too_many'))
        if tex_expected(fmt, w, h, mips, fl) != len(d) - 24: tex_bad.append((k, 'size_vs_dims'))
        if w == 0 or h == 0: tex_bad.append((k, 'zero_dim'))
    elif s.type == 9:
        sh = {}
        if len(d) < 12 or d[0] not in (0, 1): shader_bad.append((k, 'kind')); return
        import shaderlib
        lib = shaderlib.parse(d, '<')
        ents = lib['entries']
        if not ents: shader_bad.append((k, 'no_entries')); return
        for o, e in ents.items():
            b = e['blob']
            if len(b) < 8: shader_bad.append((k, 'blob_short')); break
            m = struct.unpack_from('<I', b, 0)[0]
            if m >> 16 not in (0xFFFE, 0xFFFF): shader_bad.append((k, 'not_d3d9_0x%08x' % m)); break
            if (m >> 16 == 0xFFFE) != (d[0] == 0): shader_bad.append((k, 'kind_vs_blob')); break
    elif s.type == 10:
        if len(d) < 0x60: mats[k] = None; return
        sh = struct.unpack_from('<4I', d, 0x28)
        mats[k] = dict(shaders=sh, ntex=d[0x52], nparams=struct.unpack_from('<I', d, 0x58)[0])
    elif s.type == 12 and d[0x10:0x14] == b'Mesh':
        import mesh_tr8
        m = mesh_tr8.Mesh(d, 'le')
        bad = [g['material'] for g in m.groups if not (0 <= g['material'] < len(m.materials))]
        meshinfo[k] = dict(nmat=len(m.materials), ntex=len(m.textures), ngroups=len(m.groups), bad_group_mat=len(bad), mats=m.materials, nverts=sum(x['numVerts'] for x in m.meshes))

def _pc_worker(a):
    path, align, i = a
    from archive import Archive
    ar = Archive(path, 'le', align)
    r = ar.idx[i]
    try:
        raw = ar.read(r)
        if raw[:4] != b'CDRM' and not (len(raw) > 24 and struct.unpack('<i', raw[:4])[0] == 19): return None
        s = summarize(raw)
        s['hash'] = r['hash']; s['spec'] = r['spec']; s['src'] = os.path.basename(path)
        return s
    except Exception as e:
        return dict(err=repr(e)[:100], hash=r['hash'], src=os.path.basename(path))

def build_pc():
    from archive import Archive
    from multiprocessing import Pool
    from names import load, L
    pcn = load(L + 'Tomb Raider Underworld (PC).txt')
    jobs = []
    for f in ('bigfile.000', 'patch.000'):
        p = os.path.join(ROOT, 'pc', f)
        a = Archive(p, 'le')
        jobs += [(p, a.align, i) for i in range(len(a.idx))]
    with Pool(8) as pool: res = pool.map(_pc_worker, jobs, chunksize=4)
    out = {}
    for s in res:
        if not s or 'err' in s: continue
        nm = norm(pcn.get(s['hash'], 'hash%08x' % s['hash']))
        if nm.startswith('pc-w/'): nm = nm[5:]
        s['name'] = nm
        key = (nm, s['spec'])
        if key not in out or s['src'] == 'patch.000': out[key] = s          # patch wins
    os.makedirs(CACHE, exist_ok=True)
    pickle.dump(out, open(os.path.join(CACHE, 'pcu.pkl'), 'wb'))
    print('PC DRMs', len(out), 'errors', sum(1 for s in res if s and 'err' in s))

def build_ovl():
    files = overlay_files()
    out = {}
    for rel, p in sorted(files.items()):
        if not rel.endswith('.drm'): continue
        raw = open(p, 'rb').read()
        s = summarize(raw); s['path'] = p; s['md5'] = hashlib.md5(raw).hexdigest(); out[rel] = s
    os.makedirs(CACHE, exist_ok=True)
    pickle.dump(out, open(os.path.join(CACHE, 'ovl.pkl'), 'wb'))
    print('overlay DRMs', len(out), 'other files', len(files) - len(out))

def load_cache():
    return (pickle.load(open(os.path.join(CACHE, 'pcu.pkl'), 'rb')), pickle.load(open(os.path.join(CACHE, 'ovl.pkl'), 'rb')))

# ------------------------------------------------------------------------------------------------ world model
def _lists(which):
    import objlists as O
    if which == 'pc':
        d = os.path.join(WK, 'generic', 'lists'); ob = open(os.path.join(d, 'pc_objectlist.txt'), 'rb').read(); od = open(os.path.join(d, 'pc_objlist.dat'), 'rb').read()
    else:
        d = os.path.join(WK, 'generic', 'merged', 'tr8', 'pc-w'); ob = open(os.path.join(d, 'objectlist.txt'), 'rb').read(); od = open(os.path.join(d, 'objlist.dat'), 'rb').read()
    obj = O.read_objectlist(ob); recs, _ = O.read_objlist(od, 'le')
    return obj, recs

class World:
    """DRM universe + co-load model.  which='pc': PC base only (calibration); 'ovl': overlay over PC with merged lists."""
    def __init__(self, which='ovl'):
        pcu, ovl = load_cache()
        self.which = which
        self.drm = {}                       # name -> summary dict (name without spec; spec variants merged)
        self.origin = {}                    # name -> 'pc' | 'ovl'
        for (nm, spec), s in pcu.items():
            if nm in self.drm:
                m = self.drm[nm]; m['secs'] = m['secs'] + s['secs']        # variants: ids from both (offsets not needed for ids)
            else: self.drm[nm] = dict(s, secs=list(s['secs']))
            self.origin[nm] = 'pc'
        self.pc_names = set(self.drm)
        if which == 'ovl':
            for nm, s in ovl.items():
                self.drm[nm] = s; self.origin[nm] = 'ovl'
        self.ids = {n: {(x[0], x[1]) for x in s['secs']} for n, s in self.drm.items()}
        self.obj, self.recs = _lists(which)
        self.unit_drm = {}                  # unit drm name -> list of object drm names
        for nm, ids in self.recs:
            u = nm.split('\\')[-1].lower() + '.drm'
            self.unit_drm[u] = [self.obj[i].lower() + '.drm' for i in ids if i in self.obj]
        # contexts: drm -> set(unit drm)
        self.ctx = collections.defaultdict(set)
        units = sorted(self.unit_drm, key=len, reverse=True)
        for u, objs in self.unit_drm.items():
            self.ctx[u].add(u)
            for o in objs: self.ctx[o].add(u)
            if u[:-4] + '_map.drm' in self.drm: self.ctx[u[:-4] + '_map.drm'].add(u)
        for n in self.drm:
            if n.startswith('streamgroups/'):
                b = n[len('streamgroups/'):-4]
                for u in units:
                    if b.startswith(u[:-4] + '_'): self.ctx[n].add(u); break
        self._clos = {}; self._load = {}
        self.resident = [r for r in RESIDENT if r in self.drm]
    def closure(self, n):
        if n in self._clos: return self._clos[n]
        seen = []; todo = [n]
        while todo:
            x = todo.pop()
            if x in seen or x not in self.drm: continue
            seen.append(x)
            for d in self.drm[x]['deps']:
                todo.append(d if d.endswith('.drm') else d + '.drm')
        self._clos[n] = seen; return seen
    def loadset(self, u):
        """all DRMs co-loaded with unit u: unit, map, streamgroups of u, object DRMs, dependency closures"""
        if u in self._load: return self._load[u]
        base = [u] + self.unit_drm.get(u, []) + [n for n, c in self.ctx.items() if u in c]
        out = set(self.resident)
        for b in base: out.update(self.closure(b))
        self._load[u] = out; return out
    def resolve(self, n, key):
        """-> (level, where): self | dep | coload(all ctx) | partial(some ctx) | elsewhere | nowhere"""
        if key in self.ids.get(n, ()): return 'self', n
        for d in self.resident:
            if key in self.ids.get(d, ()): return 'resident', d
        for d in self.closure(n)[1:]:
            if key in self.ids.get(d, ()): return 'dep', d
        cx = self.ctx.get(n, ())
        if cx:
            ok = 0; w = None
            for u in cx:
                for d in self.loadset(u):
                    if key in self.ids.get(d, ()): ok += 1; w = d; break
            if ok == len(cx): return 'coload', w
            if ok: return 'partial', w
        for d, ids in self.ids.items():
            if key in ids: return 'elsewhere', d
        return 'nowhere', None

def calibrate(which='pc'):
    """PC base: (referrer section type, referenced type) -> resolution level of unique (drm,ref) pairs"""
    W = World(which)
    st = collections.defaultdict(collections.Counter); ex = collections.defaultdict(list)
    for n in sorted(W.drm):
        if which == 'ovl' and W.origin[n] != 'pc': continue
        s = W.drm[n]; seen = set()
        for k, t, v, o in s['refs']:
            ft = s['secs'][k][0]
            if (ft, t, v) in seen: continue
            seen.add((ft, t, v))
            lv, w = W.resolve(n, (t, v))
            st[ft, t][lv] += 1
            if lv not in ('self',) and len(ex[ft, t, lv]) < 4: ex[ft, t, lv].append((n, v, w))
    print('PC base: unique (drm, referrer type, ref type, id) by resolution level')
    for k in sorted(st): print(' referrer %2d -> ref %2d' % k, dict(st[k]))
    for k, v in sorted(ex.items()): print(' ex', k, v)
    return st

# calibrated on PC base (calibrate): non-self resolution levels that occur in shipped PC DRMs, per (referrer type, referenced type)
ALLOWED = {(10, 5): {'self', 'resident', 'coload'}, (10, 9): {'self', 'coload'}, (12, 5): {'self', 'coload'}, (8, 5): {'self', 'resident'}}
# ---- R12 name strings (type 0 data): raw bytes on both platforms (calibrated: base pairs 8146/8150 name-like strings identical,
#      the 4 'diffs' are regex artefacts with a leading byte).  Xbox source DLC DRM vs installed PC DRM, same section index.
import re as _re
_RX = _re.compile(rb'[A-Za-z0-9_ .\-/\\:]{7,}\x00')
_LET = set(b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
def namelike(s):
    s = s[:-1]
    if len(s) < 9 or sum(1 for ch in s if ch in _LET) / len(s) < 0.75: return False
    return bool(_re.search(rb'[a-z]{3}', s)) and (not _re.search(rb'[A-Z]{3}', s) or (_re.fullmatch(rb'[A-Za-z0-9_]+', s) and s.count(b'_') >= 1))

def string_fixes(xd, pd, types_ok=True):
    """-> (fixed bytearray or None, list of (off, xbox_str, pc_bytes, status)).  Restores Xbox bytes over the word-aligned span of every
    name-like string whose PC bytes differ, only if the extension bytes (to word boundaries) are NUL on Xbox."""
    out = bytearray(pd); log = []; changed = False
    for m in _RX.finditer(xd):
        sx = m.group()
        if not namelike(sx): continue
        a, b = m.start(), m.end()
        if pd[a:b] == sx: continue
        a2, b2 = a & ~3, (b + 3) & ~3
        if b2 > len(xd): b2 = len(xd) & ~3
        ws = [w for w in range(a2, b2, 4) if xd[w:w + 4] != pd[w:w + 4]]
        if any(sorted(xd[w:w + 4]) != sorted(pd[w:w + 4]) for w in ws):
            log.append((a, sx[:-1].decode(), pd[a:b].split(b'\0')[0].decode('latin1'), 'manual_not_byte_permutation')); continue
        for w in ws: out[w:w + 4] = xd[w:w + 4]
        changed = True
        log.append((a, sx[:-1].decode(), pd[a:b].split(b'\0')[0].decode('latin1'), 'fixed'))
    return (out if changed else None), log

def scan_strings():
    import soundplex_fix as SF
    F = overlay_files(); res = []; fixes = {}
    for rel, p in sorted(F.items()):
        if not rel.endswith('.drm') or rel.startswith(('cinstream', 'music')): continue
        try: xs = SF.xsecs_of(rel)
        except Exception: xs = None
        if not xs: continue
        raw = open(p, 'rb').read(); D = DW.read(raw, 'le')
        if len(xs) == len(D.sections): pairs = list(zip(xs, D.sections)); mode = 'index'
        else:
            x0 = [x for x in xs if x['type'] == 0 and x['data'] is not None]; p0 = [q for q in D.sections if q.type == 0]
            if len(x0) != len(p0) or any(len(a['data']) != len(b.data) for a, b in zip(x0, p0)):
                res.append(dict(rule='R12', sev='info', file=rel, why='type0_layout_differs', nx=len(x0), npc=len(p0))); continue
            pairs = list(zip(x0, p0)); mode = 'type0_rank'
        ch = False
        for k, (x, sct) in enumerate(pairs):
            if x['data'] is None or x['type'] != sct.type or sct.type != 0 or len(x['data']) != len(sct.data): continue
            nd, log = string_fixes(x['data'], sct.data)
            for a, xs_, ps_, st in log: res.append(dict(rule='R12', sev='visible', file=rel, type=0, id=sct.id, sec=k, off=a, xbox=xs_, pc=ps_, status=st, pair=mode))
            if nd is not None: sct.data = bytes(nd); ch = True
        if ch: fixes[rel] = D
    return res, fixes

SEV_ORDER = {'crash': 0, 'visible': 1, 'cosmetic': 2, 'info': 3}
TYPE_NAME = {0: 'Data', 2: 'Anim', 5: 'Texture', 6: 'Wave', 7: 'DTP', 8: 'Script', 9: 'Shader', 10: 'Material', 11: 'Object', 12: 'Mesh/Terrain', 13: 'x13'}

def coloaded(W, n):
    """DRMs that can be in memory together with DRM n (union over its unit contexts) + resident"""
    out = set(W.resident) | set(W.closure(n))
    for u in W.ctx.get(n, ()): out |= W.loadset(u)
    out.discard(n)
    return out

def conflicts(W, names):
    """R09: (type,id) present in n and in a co-loadable DRM with another normalised content hash.  -> list of dicts"""
    idx = collections.defaultdict(dict)
    for d, s in W.drm.items():
        for x in s['secs']: idx[x[0], x[1]].setdefault(d, set()).add(x[7])
    out = []
    for n in names:
        s = W.drm[n]; co = coloaded(W, n)
        for x in s['secs']:
            key = (x[0], x[1]); mine = idx[key][n]
            if len(mine) > 1: out.append(dict(file=n, type=x[0], id=x[1], other=None, kind='dup_in_drm', n=len(mine)))
            for d, hs in idx[key].items():
                if d != n and d in co and not (hs & mine):
                    out.append(dict(file=n, type=x[0], id=x[1], other=d, kind='diff', size=x[2]))
    return out

def scan(W=None):
    W = W or World('ovl')
    F = []
    def add(rule, sev, file, **kw):
        F.append(dict(rule=rule, sev=sev, file=file, **kw))
    ovl = sorted(n for n, o in W.origin.items() if o == 'ovl')
    bad_sh = {(d, W.drm[d]['secs'][k][1]) for d in W.drm for k, _ in W.drm[d]['shader_bad']}
    for n in ovl:
        s = W.drm[n]
        # R01 / R02
        seen = {}
        for k, t, v, o in s['refs']:
            seen.setdefault((s['secs'][k][0], t, v), []).append((s['secs'][k][1], o))
        for (st, t, v), where in sorted(seen.items()):
            lv, w = W.resolve(n, (t, v))
            if lv in ALLOWED.get((st, t), {'self'}): continue
            sev = 'crash' if lv == 'nowhere' else 'visible'
            add('R01' if lv == 'nowhere' else 'R02', sev, n, ref_type=t, ref_id=v, from_type=st, from_ids=[w_[0] for w_ in where[:4]], n=len(where), level=lv, where=w)
        # R03
        for k, m in s['mats'].items():
            sid = s['secs'][k][1]
            if m is None: add('R03', 'crash', n, type=10, id=sid, why='short'); continue
            shs = [x for x in m['shaders'] if x]
            if not shs: add('R03', 'visible', n, type=10, id=sid, why='no_shader_ids'); continue
            for x in shs:
                lv, w = W.resolve(n, (9, x))
                if lv in ('nowhere',): add('R03', 'crash', n, type=10, id=sid, why='shader_unresolved', shader=x)
                elif lv not in ('self', 'resident', 'dep', 'coload'): add('R03', 'visible', n, type=10, id=sid, why='shader_' + lv, shader=x, where=w)
                elif (w, x) in bad_sh: add('R03', 'crash', n, type=10, id=sid, why='shader_not_pc_valid', shader=x)
        # R05
        for k, m in s['meshinfo'].items():
            sid = s['secs'][k][1]
            if (m['nmat'] == 0 and m['ngroups'] > 0) or m['bad_group_mat']:
                add('R05', 'crash' if m['bad_group_mat'] else 'visible', n, type=12, id=sid, nmat=m['nmat'], ngroups=m['ngroups'], bad=m['bad_group_mat'])
            for mid in m['mats']:
                lv, w = W.resolve(n, (10, mid))
                if lv != 'self': add('R05', 'crash' if lv == 'nowhere' else 'visible', n, type=12, id=sid, why='material_' + lv, material=mid)
        # R06/R07
        for k, why in s['tex_bad']:
            sev = 'crash' if why in ('xbox_header', 'datasize_hdr', 'size_vs_dims', 'mips_too_many', 'short', 'zero_dim') or why.startswith(('magic', 'fmt_')) else 'visible'
            add('R07' if why == 'xbox_header' else 'R06', sev, n, type=5, id=s['secs'][k][1], why=why)
        # R11
        for dn in s['deps']:
            dn2 = dn if dn.endswith('.drm') else dn + '.drm'
            if dn2 not in W.drm: add('R11', 'crash', n, dep=dn)
    # R08 duplicate textures (same payload md5 under several ids), inside overlay
    byh = collections.defaultdict(set)
    for n in ovl:
        for x in W.drm[n]['secs']:
            if x[0] == 5: byh[x[3]].add((n, x[1], x[2]))
    for h, v in byh.items():
        ids = {(a, b) for a, b, c in v}
        if len({b for a, b in ids}) > 1: add('R08', 'cosmetic', sorted(ids)[0][0], hash=h, ids=sorted({b for a, b in ids})[:6], nids=len({b for a, b in ids}), size=next(iter(v))[2])
    # R09 / R10
    for c in conflicts(W, ovl):
        t = c['type']
        if c['kind'] == 'dup_in_drm': add('R09', 'visible', c['file'], **{k: v for k, v in c.items() if k != 'file'}); continue
        add('R09', 'visible' if t in (5, 9, 10, 12) else 'info', c['file'], **{k: v for k, v in c.items() if k != 'file'})
    # R13 shadowing PC base DRMs
    for n in ovl:
        if n in W.pc_names: add('R13', 'info', n, note='overlay replaces PC base DRM of same name', base_units=sorted(W.ctx.get(n, ()))[:8])
    return F

def summarize_findings(F):
    c = collections.Counter((f['rule'], f['sev']) for f in F)
    return {'%s/%s' % k: v for k, v in sorted(c.items())}

if __name__ == '__main__':
    c = sys.argv[1] if len(sys.argv) > 1 else ''
    if c == 'cache': build_pc(); build_ovl()
    elif c == 'calibrate': calibrate()
    elif c == 'strings':
        res, fixes = scan_strings(); print(len(res), collections.Counter(r.get('status', r.get('why')) for r in res))
        json.dump(res, open(os.path.join(REFS, 'r12_strings.json'), 'w'), indent=1)
        out = os.path.join(REFS, 'out'); md = []
        for rel, D in sorted(fixes.items()):
            cd = DW.cdrm_encode(D.write('le'), 'le'); os.makedirs(os.path.dirname(os.path.join(out, rel)) or out, exist_ok=True)
            open(os.path.join(out, rel), 'wb').write(cd); md.append('%s  %s' % (hashlib.md5(cd).hexdigest(), rel))
        open(os.path.join(out, 'md5_strings.txt'), 'w').write('\n'.join(md) + '\n'); print('written', len(md))
    elif c == 'scan':
        F = scan(); print(summarize_findings(F)); json.dump(F, open(os.path.join(REFS, 'scan_raw.json'), 'w'), default=str)
    else: print(__doc__)
