"""engine_walk_check.py - static replicas of the tru.exe (PC, Steam unpacked) RUNTIME walkers, run over converted DLC DRM
sets, calibrated on the original PC DRMs.  Every crash so far was a mis-converted structure read only when an object ran it;
this tool walks those structures the way the engine does, before the game does.

Checks (name, engine address, what is replicated) - see CHECKS at the bottom:
  reloc      drm loader       reloc blob parse, internal/external/idref offsets inside the section, ext target inside target
  idref      resource refs    id-ref (reloc kind A/4) value = a section of that type in the SAME DRM (else resident/PC)
  evlist     0x5b26c0         anim EVENT LIST walk {u16 h, s16 frame, b4, payload[(h>>12)*4]} .. 0xffff (crash fix13);
                              Xbox source framing must equal the PC framing; kind0 sound / kind1 payload ptr slots relocated
  animinfo   0x54e200         globalaniminfo fill loop (DTP root+0xbc/+0xc0 records, (hi-lo+1)&0xff==0 = 4G fill; ng_crash)
  model      0x5b3230         model DTP HInfo counts -> alloc 8*(sum+2n) (256 MB OOM); arrays inside the section
  portal     0x5c6c80         unit portal ids (Level portal +0x82) must exist in the unit-DTP portal table (+0x9c, u16 @+8)
  script     0x57aff0 etc.    cdc ScriptType walk (script_conv.Walk LE) + instance size >= super size, own members after the
                              super instance (ng3), super / deps resolvable, opcodes known, op 0x7e script ids
  sext       0x5b9436         external relocs INTO scripts land on a structure start of the target (PC layout)
  vcall      script VM op 6a  virtual call: Prototype vtIndex < class vtableSize and the vtable slot is relocated
  sids       script natives   ids in native init blocks: objects (objectlist + loadable DRM), intro unique ids (unit intros),
                              DTP ids (section in DRM), unit ids (objlist.dat), LOC string ids (locals)
  intro      unit birth       unit Intro +0x50 objectID: objectlist + DRM loadable (+ in objlist.dat[unit])
  deps       loader           DRM dependency-name block entries loadable; unit objlist.dat objects loadable
  names      natives          script strings naming padshock effects (0x481a90 lookup replay incl. the index -1 AV),
                              music sets, cinstream streams: present in the installed set (or PC bigfile)
Sets (overlay order low -> high; later dirs win per file name):
  dlc1 = vm_mods_expected, mods_fix11, mods_fix14, mods_glitchfix, mods_fix15, mods_glitchfix2, mods_next
         (+ mods_fix13 padshock, mods_fix12 music/audio)
  dlc2 = mods_dlc2lvl (flat names 'streamgroups\\x.drm' normalised)
  --static adds work/mods_static on top.
usage:
  tools/venv/bin/python -I tools/engine_walk_check.py --set dlc1 [--set dlc2] [--static] [--json out.json] [-v]
  tools/venv/bin/python -I tools/engine_walk_check.py --calibrate-pc [--jobs 8]      (all PC bigfile DRMs -> FP signatures)
  tools/venv/bin/python -I tools/engine_walk_check.py --controls                     (known-bad historical files must flag)
  tools/venv/bin/python -I tools/engine_walk_check.py --dir DIR [DIR..]             (ad-hoc overlay)
"""
import sys, os, struct, collections, json, pickle, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW, drm_reloc as R, script_conv as S, animfx, objlists as OL

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
WK = os.path.join(ROOT, 'work')
SETS = {'dlc1': ['vm_mods_expected', 'mods_fix11', 'mods_fix14', 'mods_glitchfix', 'mods_fix15', 'mods_glitchfix2',
                 'mods_next'],      # mods_next (2026-10-10) = cumulative overlay of everything after glitchfix (see NOTES)
        'dlc2': ['mods_dlc2lvl']}
NONDRM = {'dlc1': ['mods_fix12', 'mods_fix13'], 'dlc2': ['mods_fix12', 'mods_fix13']}
CACHE = os.path.join(WK, 'engine_walk_cache')
def _drmless():
    pl = OL.read_objectlist(open(os.path.join(WK, 'generic', 'lists', 'pc_objectlist.txt'), 'rb').read())
    have = pc_name_set()
    return {n.lower() for n in pl.values() if norm(n + '.drm') not in have}

def norm(rel):
    return rel.replace('\\', '/').lower()

def overlay(dirs):
    """{normalised relative name: path}, later dirs win"""
    out = {}
    for d in dirs:
        d = d if os.path.isabs(d) else os.path.join(WK, d)
        if not os.path.isdir(d): continue
        for r, _, fs in os.walk(d):
            for f in fs:
                p = os.path.join(r, f)
                out[norm(os.path.relpath(p, d))] = p
    return out

# ------------------------------------------------------------------------------------------------ global context
class G:
    """lists, PC names, padshock table, music/cinstream availability; built once per run"""
    def __init__(self, files=None):
        L = os.path.join(WK, 'generic', 'merged', 'tr8', 'pc-w')
        self.objlist = OL.read_objectlist(open(os.path.join(L, 'objectlist.txt'), 'rb').read())      # id -> name
        recs, _ = OL.read_objlist(open(os.path.join(L, 'objlist.dat'), 'rb').read(), 'le')
        self.units = [(nm, ids) for nm, ids in recs]                                                  # 1-based unit index
        self.unit_objs = {nm.split('\\')[-1].lower(): set(ids) for nm, ids in recs}
        self.pc_names = pc_name_set()
        self.files = files or {}
        self.locals_n, self.locals_empty = locals_info()
        self.padshock = padshock_installed(self.files)
        global DRMLESS_PC, PC_OPS
        DRMLESS_PC = _drmless()
        PC_OPS = pc_ops()
        pcf = os.path.join(CACHE, 'pc_calibration.pkl')     # + opcodes of PC files outside the script pair cache (patch.000)
        if os.path.exists(pcf):
            try: PC_OPS |= {int(f['op'], 16) for f in pickle.load(open(pcf, 'rb'))['findings'] if f['code'] == 'unknown_opcode'}
            except Exception: pass

    def obj_ok(self, oid):
        """object id loadable: DRM installed / in PC, or a base object that has no DRM on PC either (script-only
        templates like music_control, tp_ping_object: PC units list them too)"""
        nm = self.objlist.get(oid)
        return nm is not None and (self.loadable(nm) or (oid <= 821 and nm.lower() in DRMLESS_PC))

    def loadable(self, name):
        """DRM name (no dir, no .drm) or relative path loadable: installed overlay or PC bigfile/patch"""
        n = norm(name if name.endswith('.drm') or '.' in name.split('/')[-1] else name + '.drm')
        return n in self.files or n in self.pc_names

def pc_name_set():
    p = os.path.join(CACHE, 'pc_names.json')
    if os.path.exists(p): return set(json.load(open(p)))
    from archive import Archive
    from names import load, L
    pcn = load(L + 'Tomb Raider Underworld (PC).txt')
    have = set()
    for f in ('bigfile.000', 'patch.000'):
        a = Archive(os.path.join(ROOT, 'pc', f), 'le')
        have |= {r['hash'] for r in a.idx}
    out = sorted(norm(n[5:]) for h, n in pcn.items() if h in have and n.lower().startswith('pc-w\\'))
    os.makedirs(CACHE, exist_ok=True); json.dump(out, open(p, 'w'))
    return set(out)

def locals_info():
    p = os.path.join(WK, 'generic', 'locals', 'mods', 'local', 'locals.bin_001')
    if not os.path.exists(p): return None, set()
    d = open(p, 'rb').read()
    _, n = struct.unpack_from('<II', d, 0)
    offs = struct.unpack_from('<%dI' % n, d, 8)
    return n, {i for i, o in enumerate(offs) if o == 0}

def padshock_installed(files):
    import padshock_convert as PS
    p = files.get('padshock/padshocklib.tfb')
    d = open(p, 'rb').read() if p else PS.load('pc')
    _, ents = PS.parse(d, '<')
    return d, {n.lower() for n, _ in ents}

# ------------------------------------------------------------------------------------------------ per-DRM context
class Ctx:
    def __init__(self, name, raw, g=None, xbox=None):
        self.name, self.g = name, g
        D = DW.read(raw, 'le')
        self.secs = D.sections
        self.deps = [x.decode('latin1') for x in D.names.split(b'\0') if x]
        self.rel = [R.parse(s.reloc, 'le') for s in self.secs]
        self.by = collections.defaultdict(list)
        for k, s in enumerate(self.secs): self.by[s.type, s.id].append(k)
        self.f = []
        self.xbox = xbox            # list of Xbox section dicts (positional per type) or None
        self._xmap = None
        self._walk = {}

    def add(self, check, code, k, off=None, sev='warn', **kw):
        s = self.secs[k] if k is not None else None
        self.f.append(dict(check=check, code=code, file=self.name, type=s.type if s else None, id=s.id if s else None,
                           off=off, sev=sev, **kw))

    def u32(self, k, o):
        d = self.secs[k].data
        return struct.unpack_from('<I', d, o)[0] if 0 <= o and o + 4 <= len(d) else None

    def xsec(self, k):
        """Xbox source section of converted section k: positional per type when the counts agree and sizes match,
        else the unique Xbox section of that type with the same size and reloc-blob length"""
        if self.xbox is None: return None
        if self._xmap is None:
            xs = collections.defaultdict(list); ps = collections.defaultdict(list)
            for s in self.xbox: xs[s['type']].append(s)
            for j, s in enumerate(self.secs): ps[s.type].append(j)
            self._xmap = {}
            for t in ps:
                if t in xs and len(xs[t]) == len(ps[t]):
                    for a, b in zip(ps[t], xs[t]):
                        if b['size'] == len(self.secs[a].data) and len(b['reloc']) == len(self.secs[a].reloc): self._xmap[a] = b
                fp = collections.defaultdict(list)
                for b in xs.get(t, []): fp[b['size'], len(b['reloc'])].append(b)
                for a in ps[t]:
                    if a in self._xmap: continue
                    l = fp.get((len(self.secs[a].data), len(self.secs[a].reloc)), [])
                    if len(l) == 1: self._xmap[a] = l[0]
            self._xid = {(s['type'], s['id']): s for s in self.xbox}
        return self._xmap.get(k)

    def walk(self, k):
        if k not in self._walk:
            try: self._walk[k] = S.Walk(self.secs[k].data, self.rel[k], 'le').run()
            except Exception as e: self._walk[k] = e
        return self._walk[k]

    def is_unit(self):
        return bool(self.secs) and self.secs[0].type == 0 and any(so == 0 for _, so, _ in self.rel[0].external)

# ------------------------------------------------------------------------------------------------ checks
def c_reloc(c):
    sizes = [dict(size=len(s.data)) for s in c.secs]
    for k, (s, r) in enumerate(zip(c.secs, c.rel)):
        for b in R.check(r, len(s.data), sizes): c.add('reloc', 'bounds_' + b[0], k, b[1] if b[0] != 'ext' else b[2], 'crash', detail=b)
        for o, t in r.internal:
            if o % 4: c.add('reloc', 'unaligned_int', k, o, 'crash')
        for si, so, do in r.external:
            if si < len(c.secs) and c.secs[si].type in (5, 6): c.add('reloc', 'ext_into_media', k, so, 'warn', tgt=(c.secs[si].type, c.secs[si].id))

def c_idref(c):
    for k, (s, r) in enumerate(zip(c.secs, c.rel)):
        for t, o in r.idref_a + r.idref:
            if o + 4 > len(s.data): continue
            v = struct.unpack_from('<I', s.data, o)[0]
            if (t, v) in c.by: continue
            c.add('idref', 'nonlocal_%d' % t, k, o, 'info', val=v)

def ev_walk_le(d, limit=1 << 16):
    """engine framing of 0x5b26c0 on PC bytes: [(off, h, frame, size)], terminator offset or None, problem"""
    a = 4; out = []
    while True:
        if a + 2 > len(d): return out, None, 'runs_off_section'
        h = struct.unpack_from('<H', d, a)[0]
        if h == 0xffff: return out, a, None
        sz = (h >> 12) * 4 + 8
        if a + sz > len(d): return out, None, 'record_past_end'
        out.append((a, h, struct.unpack_from('<h', d, a + 2)[0], sz)); a += sz
        if len(out) > limit: return out, None, 'runaway'

def c_evlist(c):
    for k, s in enumerate(c.secs):
        if s.type != 7 or len(s.data) < 8 or s.data[:4] != b'\0\0\0\0': continue
        r = c.rel[k]; it = dict(r.internal); ptr = set(r.pointer_offsets())
        x = c.xsec(k); xw = None
        if x is not None and x['data'] is not None:
            xw = animfx.detect(x['data'], R.parse(x['reloc'], 'be'))
        lw = animfx.walk(s.data, '<')
        if xw is None and lw is None: continue
        if xw is not None: c.add('evlist', '_list', k, None, 'info')      # every Xbox-detected list: animfx fix candidate
        recs, end, prob = ev_walk_le(s.data)
        if xw is not None:
            xr = [(a, h, fr, sz) for a, h, fr, sz in xw[0]]
            if [(a, h, sz) for a, h, fr, sz in recs] != [(a, h, sz) for a, h, fr, sz in xr] or end != xw[1]:
                c.add('evlist', 'misframed_vs_xbox', k, None, 'crash', recs_pc=len(recs), recs_xbox=len(xr), end_pc=end,
                      end_xbox=xw[1], prob=prob)
                continue
        elif prob:
            c.add('evlist', 'walk_' + prob, k, None, 'crash', recs=len(recs)); continue
        for a, h, fr, sz in recs:
            kind = h & 3
            if (kind, sz, 12) in animfx.PTR_SLOTS:
                if kind == 0 and s.data[a + 8] != 0: continue          # non-sound kind-0 payload (byte0 != 0): no pointer
                if a + 12 not in ptr:
                    c.add('evlist', 'payload_ptr_unrelocated', k, a + 12, 'crash', kind=kind, val=hex(c.u32(k, a + 12)))
                elif a + 12 in it and it[a + 12] + 12 > len(s.data):
                    c.add('evlist', 'payload_ptr_oob', k, a + 12, 'warn')
            if fr < 0: c.add('evlist', 'negative_frame', k, a, 'warn', frame=fr)

def obj_roots(c):
    """DTP section indices of object data roots: Obj section (type 11) id-ref @+0 (lara.drm: Obj 8 -> DTP 850)"""
    out = []
    for k, s in enumerate(c.secs):
        if s.type != 11 or len(s.data) < 4 or 0 not in c.rel[k].id_offsets(): continue
        v = struct.unpack_from('<I', s.data, 0)[0]
        out += c.by.get((7, v), [])[:1]
    return out

def c_animinfo(c):
    roots = set(obj_roots(c))
    for k, s in enumerate(c.secs):
        if k not in roots: continue
        if s.type != 7 or len(s.data) < 0xc4 or not s.reloc: continue
        it = dict(c.rel[k].internal)
        if 0xc0 not in it: continue
        n = c.u32(k, 0xbc); p = it[0xc0]
        if n == 0 or n > 256: continue
        for j in range(n):
            o = p + 12 * j
            if o + 12 > len(s.data): c.add('animinfo', 'rec_oob', k, o, 'crash'); break
            m = c.u32(k, o + 4); ep = it.get(o + 8)
            if m > 4096:
                x = c.xsec(k)
                if x is not None and x['data'] is not None and o + 8 <= len(x['data']) and struct.unpack_from('>I', x['data'], o + 4)[0] == m:
                    continue                    # same value in the Xbox source: not this struct / not a conversion error
                c.add('animinfo', 'rec_count', k, o + 4, 'crash', n=hex(m), xbox=x is not None); continue
            if ep is None: continue
            for q in range(m):
                if ep + 8 * q + 8 > len(s.data): c.add('animinfo', 'ent_oob', k, ep, 'crash'); break
                lo, hi = struct.unpack_from('<bxbx', s.data, ep + 8 * q + 4)
                if lo > hi: lo, hi = hi, lo
                if ((hi - lo + 1) & 0xff) == 0: c.add('animinfo', 'fill_wrap', k, ep + 8 * q, 'crash', lo=lo, hi=hi)

MODEL_LE = bytes.fromhex('04c20453')[::-1]
HSTRIDE = {0: 36, 1: 68, 2: 32, 3: 56, 4: 4}
def c_model(c):
    for k, s in enumerate(c.secs):
        if s.type != 7 or s.data[:4] != MODEL_LE or len(s.data) < 0x80: continue
        it = dict(c.rel[k].internal); d = s.data
        n = c.u32(k, 4); seg = it.get(0xc)
        if seg is None: continue
        if n > 4096 or seg + 0x40 * n > len(d):
            c.add('model', 'seg_count', k, 4, 'crash', n=n); continue
        tot = 0
        for j in range(n):
            e = seg + 0x40 * j
            h = it.get(e + 0x3c)
            if h is None or d[e + 0x30] & 8: continue
            if h + 0x28 > len(d): c.add('model', 'hinfo_oob', k, e + 0x3c, 'crash'); continue
            for q in range(5):
                cnt = c.u32(k, h + 8 * q); a = it.get(h + 8 * q + 4)
                tot += cnt
                if cnt and (a is None or a + cnt * HSTRIDE[q] > len(d)):
                    c.add('model', 'hinfo_count', k, h + 8 * q, 'crash', seg=j, arr=q, n=hex(cnt), ptr=a is not None)
        if 8 * (tot + 2 * n) > 0x1000000: c.add('model', 'alloc_huge', k, None, 'crash', bytes=8 * (tot + 2 * n))

def level_portals(c):
    """(Level portal ids @+0x82 [(k, off, id)], unit-DTP portal table ids)"""
    if not c.is_unit(): return None
    r0 = c.rel[0]; ext = {so: (si, do) for si, so, do in r0.external}
    ti, _ = ext[0]
    if ti >= len(c.secs) or len(c.secs[ti].data) != 24: return None
    td = c.secs[ti].data; rt = c.rel[ti]; text = {so: (si, do) for si, so, do in rt.external}
    npor = struct.unpack_from('<h', td, 2)[0]
    lp = []
    if 4 in text:
        si, do = text[4]
        for j in range(npor):
            o = do + 0x100 * j + 0x82
            if o + 2 <= len(c.secs[si].data): lp.append((si, o, struct.unpack_from('<H', c.secs[si].data, o)[0]))
    tab = None
    if 0x74 in ext:
        di, do = ext[0x74]; s = c.secs[di]
        if s.type == 7 and len(s.data) >= 0xa0:
            ri = dict(c.rel[di].internal)
            n3 = struct.unpack_from('<I', s.data, 0x98)[0]; t3 = ri.get(0x9c)
            if t3 is not None and t3 + 0x40 * n3 <= len(s.data):
                tab = {struct.unpack_from('<H', s.data, t3 + 0x40 * j + 8)[0] for j in range(n3)}
    return lp, tab, ext

def c_portal(c):
    lp = level_portals(c)
    if not lp: return
    lp, tab, _ = lp
    if tab is None:
        if lp: c.add('portal', 'no_portal_table', 0, None, 'warn')
        return
    for si, o, v in lp:
        if v not in tab: c.add('portal', 'portal_id_missing', si, o, 'crash', portal=v, table=sorted(tab)[:8])

def unit_name(c):
    return c.name.split('/')[-1][:-4].lower()

def intros(c):
    if not c.is_unit(): return []
    ext = {so: (si, do) for si, so, do in c.rel[0].external}
    if 0x74 not in ext: return []
    di, do = ext[0x74]; s = c.secs[di]
    if s.type != 7 or len(s.data) < 0x14: return []
    ri = dict(c.rel[di].internal); n = struct.unpack_from('<I', s.data, 0xc)[0]; t = ri.get(0x10)
    if t is None or t + 0x90 * n > len(s.data): return []
    return [(di, t + 0x90 * j) for j in range(n)]

def unit_node_ids(c):
    """intro unique ids + node ids (unit DTP +0xac n, +0xb4 -> 0x40-byte records, u32 @+0x20): one global id space"""
    out = unit_intro_ids(c)
    if not c.is_unit(): return out
    ext = {so: (si, do) for si, so, do in c.rel[0].external}
    if 0x74 in ext:
        di, do = ext[0x74]; s = c.secs[di]
        if s.type == 7 and len(s.data) >= 0xb8:
            ri = dict(c.rel[di].internal); n4 = struct.unpack_from('<I', s.data, 0xac)[0]; t4 = ri.get(0xb4)
            if t4 is not None and 0 < n4 < 100000 and t4 + 0x40 * n4 <= len(s.data):
                out |= {struct.unpack_from('<I', s.data, t4 + 0x40 * j + 0x20)[0] for j in range(n4)}
    return out

def c_intro(c):
    g = c.g; un = unit_name(c)
    uo = g.unit_objs.get(un)
    if c.is_unit(): c.f.append(dict(check='intro', code='_unit_ids', file=c.name, type=None, id=None, off=None, sev='info',
                                    ids=sorted(unit_node_ids(c))))
    for di, o in intros(c):
        d = c.secs[di].data
        oid = struct.unpack_from('<H', d, o + 0x50)[0]
        nm = g.objlist.get(oid)
        if nm is None: c.add('intro', 'object_not_in_objectlist', di, o + 0x50, 'crash', obj=oid); continue
        if not g.obj_ok(oid): c.add('intro', 'object_drm_missing', di, o + 0x50, 'crash', obj=oid, name=nm)
        if uo is not None and oid not in uo: c.add('intro', 'object_not_in_unit_objlist', di, o + 0x50, 'warn', obj=oid, name=nm)

def c_deps(c):
    g = c.g
    for dn in c.deps:
        if not g.loadable(dn): c.add('deps', 'dependency_missing', None, None, 'crash', dep=dn)
    un = unit_name(c)
    if c.is_unit() and un in g.unit_objs:
        for oid in sorted(g.unit_objs[un]):
            nm = g.objlist.get(oid)
            if nm is None: c.add('deps', 'unit_object_not_in_objectlist', None, None, 'crash', obj=oid)
            elif not g.obj_ok(oid): c.add('deps', 'unit_object_drm_missing', None, None, 'crash', obj=oid, name=nm)

# ---- scripts
def script_info(c):
    """{k: dict(self, super, size, vt, members, protos...)} of every Script section"""
    if hasattr(c, '_si'): return c._si
    out = {}
    for k, s in enumerate(c.secs):
        if s.type != 8 or len(s.data) < 0x54: continue
        d = s.data; ids = c.rel[k].id_offsets()
        out[k] = dict(self=c.u32(k, 0x14), sup=c.u32(k, 0x18) if 0x18 in ids else 0, size=struct.unpack_from('<H', d, 0x1c)[0],
                      vt=struct.unpack_from('<H', d, 0x3c)[0])
    c._si = out
    return out

def resolve_script(c, sid):
    ks = c.by.get((8, sid))
    return ks[0] if ks else None

DRMLESS_PC = set()
def pc_ops():
    """set of bytecode opcodes used by the PC base scripts (work/script/pairs_8.pkl, PC side), cached"""
    p = os.path.join(CACHE, 'pc_ops.json')
    if os.path.exists(p): return set(json.load(open(p)))
    L = pickle.load(open(os.path.join(WK, 'script', 'pairs_8.pkl'), 'rb'))
    ops = set()
    for r in L:
        W = S.Walk(r['pd'], R.parse(r['pr'], 'le'), 'le').run()
        for nm, t, n, sz in W.arrays:
            if nm == 'code':
                j = 0
                while j < n:
                    op = r['pd'][t + 4 * j + 3]; ops.add(op); j += 1 + S.Walk.EXTRA.get(op, 0)
    os.makedirs(CACHE, exist_ok=True); json.dump(sorted(ops), open(p, 'w'))
    return ops
PC_OPS = None
def c_script(c):
    si = script_info(c)
    for k, inf in si.items():
        W = c.walk(k)
        if isinstance(W, Exception): c.add('script', 'walker_exception', k, None, 'crash', err=repr(W)); continue
        for b in W.bad: c.add('script', 'walk_' + str(b[0]), k, b[2] if len(b) > 2 else None, 'crash', detail=repr(b)[:120])
        # super chain: present + instance size
        if inf['sup']:
            sk = resolve_script(c, inf['sup'])
            if sk is None: c.add('script', 'super_not_in_drm', k, 0x18, 'warn', sup=inf['sup'])
            else:
                ss = si[sk]['size'] if sk in si else None
                if ss is not None and inf['size'] < ss:
                    c.add('script', 'size_below_super', k, 0x1c, 'crash', size=inf['size'], super_size=ss, sup=inf['sup'])
                x = c.xsec(k)
                if ss is not None and x is not None and x['data'] is not None and len(x['data']) >= 0x54:
                    xsup = struct.unpack_from('>I', x['data'], 0x18)[0]
                    xs_ = c._xid.get((8, xsup))
                    sx = struct.unpack_from('>H', xs_['data'], 0x1c)[0] if xs_ is not None and xs_['data'] is not None else None
                    if sx is not None and ss > sx:          # PC super grew: own members of the Xbox layout must move (ng3)
                        for nm, t, n, sz in W.arrays:
                            if nm != 'members': continue
                            for j in range(n):
                                o = t + j * sz + 12
                                mo = struct.unpack_from('<H', c.secs[k].data, o)[0]
                                xo = struct.unpack_from('>H', x['data'], o)[0] if o + 2 <= len(x['data']) else None
                                if xo is not None and xo >= sx and mo == xo and mo < ss:
                                    c.add('script', 'member_not_rebased', k, o, 'crash', moff=mo, super_xbox=sx, super_pc=ss)
                            break
        # every SArray count of the Xbox source walk must survive conversion (u32): protos count 6 -> 0x60000 seen
        x = c.xsec(k)
        if x is not None and x['data'] is not None and len(x['data']) == len(c.secs[k].data):
            xr = R.parse(x['reloc'], 'be')
            if sorted(xr.internal) == sorted(c.rel[k].internal):
                XW = S.Walk(x['data'], xr, 'be').run()
                for nm, t, n, sz in XW.arrays:
                    if nm == 'vtable' or t < 4: continue
                    pv = struct.unpack_from('<I', c.secs[k].data, t - 4)[0]
                    if pv == n: continue
                    xb = x['data'][t - 4:t]
                    if c.secs[k].data[t - 4:t] in (xb, xb[1::-1] + xb[:1:-1]):      # raw / u16-pair copy of the BE count
                        c.add('script', 'sarray_count_byteclass', k, t - 4, 'crash', arr=nm, pc=pv, xbox=n)
                    else:
                        c.add('script', 'sarray_count_value', k, t - 4, 'warn', arr=nm, pc=pv, xbox=n)
        # code: opcodes, op 0x7e operands (script ids)
        d = c.secs[k].data
        for nm, t, n, sz in W.arrays:
            if nm != 'code': continue
            j = 0
            while j < n:
                o = t + 4 * j; w = struct.unpack_from('<I', d, o)[0]; op = w >> 24
                if PC_OPS is not None and op not in PC_OPS: c.add('script', 'unknown_opcode', k, o, 'crash', op=hex(op))
                if op == 0x7e and j + 1 < n:
                    v = struct.unpack_from('<I', d, o + 4)[0]
                    if o + 4 not in c.rel[k].id_offsets() and v and (8, v) not in c.by:
                        c.add('script', 'op7e_script_missing', k, o + 4, 'warn', sid=v)
                j += 1 + S.Walk.EXTRA.get(op, 0)

def script_starts(c, k):
    """structure starts of script section k (PC layout): 0, root fields, array elements, internal targets, vte, texts"""
    W = c.walk(k)
    st = set(range(0, 0x54, 4)) | set(dict(c.rel[k].internal).values())
    if isinstance(W, Exception): return st
    for nm, t, n, sz in W.arrays:
        st.add(t); st.add(t - 4)
        st.update(t + j * sz for j in range(n))
    for (t, kind) in W.seen: st.add(t)
    return st

def c_sext(c):
    cache = {}
    for k, r in enumerate(c.rel):
        for si, so, do in r.external:
            if si >= len(c.secs) or c.secs[si].type != 8: continue
            if si not in cache: cache[si] = script_starts(c, si)
            if do not in cache[si]:
                c.add('sext', 'ext_dst_not_struct_start', k, so, 'crash', tgt=(8, c.secs[si].id), dst=do)

def ptr_target(c, k, o):
    """(section index, offset) of the pointer at k:o (internal or external) or None"""
    it = c._it.get(k) if hasattr(c, '_it') else None
    if it is None:
        if not hasattr(c, '_it'): c._it = {}
        it = c._it[k] = (dict(c.rel[k].internal), {so: (si, do) for si, so, do in c.rel[k].external})
    if o in it[0]: return k, it[0][o]
    return it[1].get(o)

def c_vcall(c):
    si = script_info(c)
    for k in si:
        W = c.walk(k)
        if isinstance(W, Exception): continue
        d = c.secs[k].data
        for nm, t, n, sz in W.arrays:
            if nm != 'code': continue
            j = 0
            while j < n:
                o = t + 4 * j; op = d[o + 3]
                if op == 0x6a and j + 1 < n:
                    pt = ptr_target(c, k, o + 4)
                    if pt is None: c.add('vcall', 'proto_ptr_unrelocated', k, o + 4, 'crash')
                    else:
                        pk, po = pt
                        if pk >= len(c.secs) or po + 28 > len(c.secs[pk].data):
                            c.add('vcall', 'proto_oob', k, o + 4, 'crash')
                        else:
                            pd = c.secs[pk].data
                            vti = struct.unpack_from('<H', pd, po + 6)[0]
                            cls = struct.unpack_from('<I', pd, po)[0] if po in c.rel[pk].id_offsets() else c.secs[pk].id
                            ck = resolve_script(c, cls)
                            if ck is None or ck not in si: c.add('vcall', 'class_not_in_drm', k, o + 4, 'warn', cls=cls)
                            else:
                                vts = si[ck]['vt']
                                if vti >= vts: c.add('vcall', 'vtindex_out_of_range', k, o + 4, 'crash', cls=cls, vti=vti, vtsize=vts)
                j += 1 + S.Walk.EXTRA.get(op, 0)

# native init-block userType symbols (PC symbols; Xbox -> PC: 4441->5823, 4449->5841, 4469->5861, 4878->6445, 1700->1731,
# 4485->5792, 1754->1785, 7333->7829, 7153->7649; < 216 identity), learned classes of script_table.pkl ('init', 10, 1, 0, ut)
UT_OBJ = {73, 5823, 5841, 5861, 6445}           # u16 object id (first half)
UT_INTRO = {50}                                 # u32 intro unique id
UT_DTP = {221, 1785, 7829, 7649}                # u32 DTP section id
UT_UNIT = {68, 1731}                            # u16 unit id (first half); 5792 at +4
UT_LOC = {223}                                  # u16 locals string id

def unit_intro_ids(c):
    """all intro unique ids (+node ids) of the unit DTP of this DRM"""
    out = set()
    for di, o in intros(c): out.add(struct.unpack_from('<I', c.secs[di].data, o + 0x58)[0])
    return out

def c_sids(c):
    g = c.g; si = script_info(c)
    nunits = len(g.units)
    for k in si:
        W = c.walk(k)
        if isinstance(W, Exception): continue
        d = c.secs[k].data; skip = set(c.rel[k].pointer_offsets()) | set(c.rel[k].id_offsets())
        for o, lab in W.lab.items():
            if lab[0] != 'init' or len(lab) != 5 or lab[1] != 10 or lab[2] < 1 or o in skip: continue
            ut, kk = lab[4], lab[3]
            if ut in UT_OBJ and kk == 0:
                v = struct.unpack_from('<H', d, o)[0]
                if v in (0, 0xffff): continue
                nm = g.objlist.get(v)
                if nm is None: c.add('sids', 'object_not_in_objectlist', k, o, 'crash', obj=v)
                elif not g.obj_ok(v): c.add('sids', 'object_drm_missing', k, o, 'crash', obj=v, name=nm)
                else: c.f.append(dict(check='sids', code='_objref', file=c.name, type=8, id=c.secs[k].id, off=o, sev='info', obj=v, name=nm))
            elif ut in UT_INTRO and kk == 0:
                v = struct.unpack_from('<I', d, o)[0]
                if v in (0, 0xffffffff): continue
                c.f.append(dict(check='sids', code='_introref', file=c.name, type=8, id=c.secs[k].id, off=o, sev='info', intro=v))
            elif ut in UT_DTP and kk == 0:
                v = struct.unpack_from('<I', d, o)[0]
                if v in (0, 0xffffffff): continue
                if (7, v) not in c.by: c.add('sids', 'dtp_not_in_drm', k, o, 'warn', dtp=v)
            elif ut in UT_UNIT and kk == 0:
                v = struct.unpack_from('<H', d, o)[0]
                if v in (0, 0xffff): continue
                if v > nunits: c.add('sids', 'unit_out_of_range', k, o, 'warn', unit=v)
            elif ut in UT_LOC and kk == 0 and g.locals_n:
                v = struct.unpack_from('<H', d, o)[0]
                if v in (0, 0xffff): continue
                if v >= g.locals_n: c.add('sids', 'loc_out_of_range', k, o, 'warn', loc=v)
                elif v in g.locals_empty: c.add('sids', 'loc_empty', k, o, 'info', loc=v)

def script_strings(c, k):
    W = c.walk(k)
    if isinstance(W, Exception): return []
    d = c.secs[k].data; out = []
    for (t, kind) in W.seen:
        if kind != 'text': continue
        z = d.find(b'\0', t)
        if z > t: out.append((t, d[t:z]))
    return out

def c_names(c):
    g = c.g
    import padshock_convert as PS
    tab, names = g.padshock
    for k in script_info(c):
        for o, sb in script_strings(c, k):
            s = sb.decode('latin1', 'replace')
            c.f.append(dict(check='names', code='_string', file=c.name, type=8, id=c.secs[k].id, off=o, sev='info', s=s))

def names_post(G_, findings, padshock_like):
    """cross-file string checks (run after all files): padshock names via the engine lookup replay"""
    import padshock_convert as PS
    tab, names = G_.padshock
    out = []
    for f in findings:
        if f['code'] != '_string': continue
        s = f['s']
        if s.lower() in padshock_like and s.lower() not in names:
            r = PS.lookup(tab, s.encode('latin1'))
            out.append(dict(f, code='padshock_missing' + ('_AV' if r == -1 else ''), sev='crash' if r == -1 else 'warn'))
    return out

def c_xid(c):
    """section ids stored WITHOUT reloc inside the structs an event list reaches (sound 'plex' nodes: wave ids id32:6, DTP ids
    id32:7 per the animfx base-pair table, e.g. fix14 'DTP 7004 not remapped to 7263'): the PC word must name a section of
    that type in this DRM.  Lists located on the Xbox source (animfx.detect), PC words read at the same offsets."""
    if c.xbox is None: return
    T = animfx.table()
    for k, sec in enumerate(c.secs):
        if sec.type != 7 or sec.data[:4] != b'\0\0\0\0': continue
        x = c.xsec(k)
        if x is None or x['data'] is None or len(x['data']) != len(sec.data): continue
        xr = R.parse(x['reloc'], 'be')
        w = animfx.detect(x['data'], xr)
        if w is None: continue
        skip = set(xr.pointer_offsets()) | set(xr.id_offsets())
        for o, key in animfx.labels(x['data'], xr, w).items():
            if o in skip or o + 4 > len(sec.data): continue
            e = T.get(key)
            cl = animfx.choose(e) if e else None
            if not cl or not cl.startswith('id32:'): continue
            t = int(cl.split(':')[1]); pv = c.u32(k, o)
            if pv in (0, 0xffffffff): continue
            if (t, pv) not in c.by: c.add('xid', 'sound_id%d_missing' % t, k, o, 'crash' if t == 7 else 'warn', pc=pv,
                                          xbox=struct.unpack_from('>I', x['data'], o)[0])

def c_splex(c):
    """SoundPlex node type 5 (walker 0x5920b0 -> 0x590ce0): data {+0 child node, +4 u32 COUNT, +8 ptr, +0xc ptr}; the engine
    allocates 16*COUNT (0x590db9). A raw Xbox count (1 -> 0x01000000) asks 256 MB: fatal 'Out of memory' (NOTES 2026-10-11)."""
    for k, s in enumerate(c.secs):
        if s.type != 7: continue
        it = dict(c.rel[k].internal); d = s.data
        for o, tg in c.rel[k].internal:
            if o < 4 or o % 4 or tg % 4 or tg + 0x10 > len(d) or struct.unpack_from('<I', d, o - 4)[0] != 5: continue
            ch = it.get(tg)
            if ch is None or ch + 8 > len(d) or struct.unpack_from('<I', d, ch)[0] > 13 or (ch + 4) not in it: continue
            if (tg + 8) not in it or (tg + 0xc) not in it: continue
            n = struct.unpack_from('<I', d, tg + 4)[0]
            if n == 0xbeebbeeb: continue          # fill pattern of unused Xbox data (same bytes swapped), not a live node
            if 16 * n > 0x1000000: c.add('splex', 'count_huge', k, tg + 4, 'crash', n=hex(n), bytes=16 * n)

CHECKS = [('reloc', 'loader', c_reloc), ('idref', 'resource refs', c_idref), ('evlist', '0x5b26c0', c_evlist),
          ('animinfo', '0x54e200', c_animinfo), ('model', '0x5b3230', c_model), ('portal', '0x5c6c80', c_portal),
          ('intro', 'unit birth', c_intro), ('deps', 'loader', c_deps), ('script', '0x57aff0', c_script),
          ('sext', '0x5b9436', c_sext), ('vcall', 'op 0x6a', c_vcall), ('sids', 'natives', c_sids), ('names', 'natives', c_names),
          ('xid', 'sound/DTP ids', c_xid), ('splex', '0x590ce0', c_splex)]

def run_file(name, raw, g, xbox=None, only=None):
    c = Ctx(name, raw, g, xbox)
    for nm, addr, fn in CHECKS:
        if only and nm not in only: continue
        try: fn(c)
        except Exception as e:
            import traceback
            c.add(nm, 'checker_exception', None, None, 'info', err=traceback.format_exc()[-400:])
    return c.f

# ------------------------------------------------------------------------------------------------ drivers
CUR_SET = None
XBOX_PACK = {('dlc2', 'g_pda.drm'): 'pack11'}     # files in mods_static built from another pack than raw_dlc's first hit
def xbox_dlc(rel):
    from convert_dlc import raw_dlc
    from drm import cdrm_decode, sections_with_data
    pk = XBOX_PACK.get((CUR_SET, rel))
    if pk:
        from override_merge import raw as ovr_raw
        return sections_with_data(cdrm_decode(ovr_raw(pk, rel), 'be'), 'be')[1]
    raw, _ = raw_dlc(rel.replace('/', '\\'))
    if raw is None: raw, _ = raw_dlc(rel.split('/')[-1])
    if raw is None: return None
    return sections_with_data(cdrm_decode(raw, 'be'), 'be')[1]

def xbox_base(name):
    from rung1 import raw_xbox
    from drm import cdrm_decode, sections_with_data
    raw = raw_xbox(name)
    if raw is None: return None
    return sections_with_data(cdrm_decode(raw, 'be'), 'be')[1]

def scan_set(files, g, only=None, xbox=True, verbose=False):
    allf = []
    for rel, path in sorted(files.items()):
        if not rel.endswith('.drm'): continue
        xs = xbox_dlc(rel) if xbox else None
        try: f = run_file(rel, open(path, 'rb').read(), g, xs, only)
        except Exception as e:
            f = [dict(check='load', code='read_error', file=rel, type=None, id=None, off=None, sev='crash', err=repr(e))]
        for x in f: x['path'] = path
        allf += f
        if verbose: print(rel, collections.Counter((x['check'], x['code']) for x in f if not x['code'].startswith('_')), flush=True)
    return allf

def _pc_worker(args):
    name, part = args
    from archive import Archive
    from names import crc
    g = _pc_worker.g
    out = []
    for f in ('patch.000', 'bigfile.000'):
        a = Archive(os.path.join(ROOT, 'pc', f), 'le'); r = a.find(crc('pc-w\\' + name.replace('/', '\\')))
        if r:
            raw = a.read(r[0]); src = f; break
    else: return []
    xs = xbox_base(name) if part else None
    try: out = run_file(name, raw, g, xs)
    except Exception as e: out = [dict(check='load', code='read_error', file=name, sev='crash', err=repr(e))]
    for x in out: x['src'] = src
    return out

def _pc_init():
    _pc_worker.g = G({})

def calibrate_pc(jobs=8, limit=None, with_xbox=True):
    from concurrent.futures import ProcessPoolExecutor
    names = sorted(n for n in pc_name_set() if n.endswith('.drm'))[:limit]
    allf = []
    with ProcessPoolExecutor(jobs, initializer=_pc_init) as ex:
        for k, f in enumerate(ex.map(_pc_worker, [(n, with_xbox) for n in names], chunksize=4)):
            allf += f
            if k % 100 == 0: print('pc', k, len(names), flush=True)
    g = G({})
    allf += post(g, allf)
    return names, allf

def summarize(allf, title, pcsig=None, nfiles=None):
    real = [f for f in allf if not f['code'].startswith('_')]
    print('== %s: %s files, %d findings' % (title, nfiles, len(real)))
    cnt = collections.Counter((f['check'], f['code'], f['sev']) for f in real)
    fil = collections.defaultdict(set)
    for f in real: fil[f['check'], f['code'], f['sev']].add(f['file'])
    for (ch, code, sev), n in sorted(cnt.items()):
        tag = ''
        if pcsig is not None:
            p = pcsig.get('%s/%s' % (ch, code))
            tag = '  [PC: %d hits in %d files]' % tuple(p) if p else '  [PC: never]'
        print('  %-8s %-34s %-5s %6d in %3d files%s' % (ch, code, sev, n, len(fil[ch, code, sev]), tag))

def pc_signatures(allf):
    c = collections.Counter(); fs = collections.defaultdict(set)
    for f in allf:
        if f['code'].startswith('_'): continue
        k = '%s/%s' % (f['check'], f['code']); c[k] += 1; fs[k].add(f['file'])
    return {k: (c[k], len(fs[k])) for k in c}

def post(g, allf):
    """cross-file checks: padshock-like strings, object references per unit (spawn), intro refs"""
    out = []
    import padshock_convert as PS
    known = set()
    for which in ('pc', 'tu', 'l1'):
        try: known |= {n.lower() for n, _ in PS.parse(PS.load(which), '<' if which == 'pc' else '>')[1]}
        except Exception: pass
    out += names_post(g, allf, known)
    music = {f.split('/')[1] for f in g.files if f.startswith('music/')} | {n.split('/')[1] for n in g.pc_names if n.startswith('music/')}
    cin = {f.split('/')[1].rsplit('.', 1)[0] for f in g.files if f.startswith('cinstream/') and f.endswith('.mul')} | \
          {n.split('/')[1].rsplit('.', 1)[0] for n in g.pc_names if n.startswith('cinstream/') and n.endswith('.mul')}
    for f in allf:
        if f['code'] != '_string': continue
        s = f['s'].lower()
        if ('_mus_' in s or s.startswith('dlc2_') and s.endswith('_mus')) and ' ' not in s and s not in music:
            out.append(dict(f, check='names', code='music_missing', sev='warn'))
        if s.startswith('pdlc') and ' ' not in s and s not in cin:
            out.append(dict(f, check='names', code='cinstream_missing', sev='warn'))
        if '\\' in s and ' ' not in s and s.split('\\')[0] in STREAM_DIRS and not s.endswith('\\'):
            n = norm('audio/streams/' + s + '.mul')
            if n not in g.files and n not in g.pc_names:
                out.append(dict(f, check='names', code='stream_missing', sev='warn'))
    for rel in g.files:                         # cinstream .drm installed without its .mul stream
        if rel.startswith('cinstream/') and rel.endswith('.drm'):
            m = rel[:-4] + '.mul'
            if m not in g.files and m not in g.pc_names:
                out.append(dict(check='names', code='cinstream_mul_missing', file=rel, type=None, id=None, off=None, sev='warn'))
    # spawn: objects referenced by script native init blocks must be in the objlist.dat entry of every unit that loads the
    # referencing file (the engine births only loaded objects: 'Not birthing X, object does not exist')
    files = {f['file'] for f in allf}
    units_here = {r.split('/')[-1][:-4] for r in files} & set(g.unit_objs)
    name2id = {v.lower(): k for k, v in g.objlist.items()}
    loaders = collections.defaultdict(set)
    for u in units_here:
        for oid in g.unit_objs[u]:
            nm = g.objlist.get(oid)
            if nm: loaders[nm.lower()].add(u)
    unit_ids = {f['file'].split('/')[-1][:-4]: set(f['ids']) for f in allf if f['code'] == '_unit_ids'}
    for f in allf:
        base = f['file'].split('/')[-1][:-4]
        us = ({base} & units_here) | loaders.get(base, set())
        if f['code'] == '_objref':
            if f['obj'] == name2id.get(base): continue
            for u in sorted(us):
                if f['obj'] not in g.unit_objs[u]:
                    out.append(dict(f, check='sids', code='spawn_obj_not_in_unit', sev='warn', unit=u))
        elif f['code'] == '_introref' and us and unit_ids:
            if not any(f['intro'] in unit_ids.get(u, ()) for u in us) and not any(f['intro'] in v for v in unit_ids.values()):
                out.append(dict(f, check='sids', code='intro_ref_missing', sev='warn', units=sorted(us)))
    return out
STREAM_DIRS = {'music', 'vo', 'env', 'event_triggered', 'animation', 'sfx', 'ambience', 'creatures', 'cine', 'foley', 'ui'}

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--set', action='append', default=[])
    ap.add_argument('--dir', nargs='*', default=[])
    ap.add_argument('--static', action='store_true')
    ap.add_argument('--calibrate-pc', action='store_true')
    ap.add_argument('--controls', action='store_true')
    ap.add_argument('--jobs', type=int, default=8)
    ap.add_argument('--limit', type=int)
    ap.add_argument('--only')
    ap.add_argument('--json')
    ap.add_argument('--no-xbox', action='store_true')
    ap.add_argument('-v', action='store_true')
    ap.add_argument('--fix', help='write fixed copies of files with fixable crash findings to DIR/<set>/ (only changed files)')
    ap.add_argument('--validate-fixes', action='store_true')
    a = ap.parse_args()
    only = set(a.only.split(',')) if a.only else None
    os.makedirs(CACHE, exist_ok=True)
    pcf = os.path.join(CACHE, 'pc_calibration.pkl')
    if a.calibrate_pc:
        names, allf = calibrate_pc(a.jobs, a.limit)
        pickle.dump(dict(names=names, findings=allf), open(pcf, 'wb'))
        summarize(allf, 'PC calibration', None, len(names))
    pcsig = pc_signatures(pickle.load(open(pcf, 'rb'))['findings']) if os.path.exists(pcf) else None
    report = {}
    runs = [(s, SETS[s] + (['mods_static/' + s] if a.static else []), NONDRM.get(s, [])) for s in a.set]
    if a.dir: runs.append(('dir', a.dir, []))
    global CUR_SET
    for title, dirs, nd in runs:
        CUR_SET = title
        files = overlay(nd + dirs)
        g = G(files)
        print('overlay %s: %s -> %d DRMs' % (title, ' < '.join(nd + dirs), sum(1 for f in files if f.endswith('.drm'))))
        allf = scan_set(files, g, only, not a.no_xbox, a.v)
        allf += post(g, allf)
        summarize(allf, title, pcsig, sum(1 for f in files if f.endswith('.drm')))
        report[title] = allf
        if a.fix:
            od = os.path.join(a.fix if os.path.isabs(a.fix) else os.path.join(WK, a.fix), title)
            byf = collections.defaultdict(list)
            for f in allf:
                if (f['check'], f['code']) in FIXES: byf[f['file']].append(f)
            for rel, fl in sorted(byf.items()):
                out, st = fix_file(rel, files[rel], g, fl)
                if out is None: continue
                op = os.path.join(od, rel); os.makedirs(os.path.dirname(op), exist_ok=True)
                open(op, 'wb').write(out)
                print('  fix', rel, '<-', files[rel], dict(st), hashlib.md5(out).hexdigest())
    if a.controls: controls(pcsig)
    if a.validate_fixes: validate_fixes(a.limit)
    if a.json:
        json.dump({k: [f for f in v if not f['code'].startswith('_string')] for k, v in report.items()}, open(a.json, 'w'), default=str, indent=0)

CONTROLS = [  # (description, dir, file, check, code, section id) - historical crash files that must be flagged
    ('ng_crash costume_f animinfo', 'mods_dlc2', 'dlc_costume_f.drm', 'animinfo', None, 23617),
    ('OOM 0x10000078 adren model', 'mods_dlc2', 'ma_ani_adren_trap.drm', 'model', None, 20965),
    ('fix13 adren event list', 'vm_mods_expected', 'dlc1_uo_adren_trap.drm', 'evlist', None, 20940),
    ('ng3 caverns script size', 'mods_fix2', 'dlc_caverns.drm', 'script', None, None),
]
def controls(pcsig):
    g = G(overlay(SETS['dlc1'] + NONDRM['dlc1']))
    for desc, d, fn, ch, code, sid in CONTROLS:
        p = os.path.join(WK, d, fn)
        if not os.path.exists(p): print('CONTROL', desc, 'MISSING FILE', p); continue
        f = run_file(fn, open(p, 'rb').read(), g, xbox_dlc(fn), {ch})
        hit = [x for x in f if x['check'] == ch and not x['code'].startswith('_') and x['sev'] == 'crash' and (sid is None or x['id'] == sid)]
        print('CONTROL %-32s %s  %s' % (desc, 'FLAGGED' if hit else 'NOT FLAGGED', [(x['code'], x['id'], x['off']) for x in hit[:4]]))
    import padshock_convert as PS
    r = PS.lookup(PS.load('pc'), b'dlc1_adren_bridge')
    print('CONTROL %-32s %s' % ('fix12 padshock PC table', 'FLAGGED (index -1 AV)' if r == -1 else 'NOT FLAGGED %r' % r))


# ------------------------------------------------------------------------------------------------ fixes (word-level, on top of
# the installed file; every fix validated on base Xbox/PC pairs = applied on the real PC bytes it changes nothing)
def fix_sarray(c, k, x, buf):
    """script SArray counts (u32 @ptr-4) := Xbox count, when the converted word is a raw / u16-pair copy of it"""
    if x is None or x['data'] is None or len(x['data']) != len(buf): return 0
    xr = R.parse(x['reloc'], 'be')
    if sorted(xr.internal) != sorted(c.rel[k].internal): return 0
    n = 0
    for nm, t, cnt, sz in S.Walk(x['data'], xr, 'be').run().arrays:
        if nm == 'vtable' or t < 4: continue
        xb = x['data'][t - 4:t]
        if bytes(buf[t - 4:t]) in (xb, xb[1::-1] + xb[:1:-1]) and xb[::-1] != bytes(buf[t - 4:t]):
            buf[t - 4:t] = xb[::-1]; n += 1
    return n

def fix_animinfo(c, k, x, buf):
    """object-root animinfo table (0x54e200): root+0xbc u32; records {u16,u16 @0, u32 n @4, ptr @8}; entries {f32, s8 lo,
    pad, s8 hi, pad as u16 pair}.  Classes: 11 base object roots with tables, 100% consistent (u16/u32/u32/u16)."""
    if x is None or x['data'] is None or len(x['data']) != len(buf) or len(buf) < 0xc4: return 0
    xd = x['data']; it = dict(c.rel[k].internal); xi = dict(R.parse(x['reloc'], 'be').internal)
    if 0xc0 not in it or xi.get(0xc0) != it[0xc0]: return 0
    ch = [0]
    def put(o, u16=False):
        w = xd[o:o + 4]; v = (w[1::-1] + w[:1:-1]) if u16 else w[::-1]
        if bytes(buf[o:o + 4]) != v: buf[o:o + 4] = v; ch[0] += 1
    put(0xbc)
    n = struct.unpack_from('>I', xd, 0xbc)[0]; p = it[0xc0]
    if not 0 < n <= 256 or p + 12 * n > len(xd): return ch[0]
    for j in range(n):
        o = p + 12 * j
        if it.get(o + 8) != xi.get(o + 8): continue
        put(o, True); put(o + 4)
        m = struct.unpack_from('>I', xd, o + 4)[0]; ep = it.get(o + 8)
        if ep is None or m > 4096 or ep + 8 * m > len(xd): continue
        for q in range(m):
            put(ep + 8 * q); put(ep + 8 * q + 4, True)
    return ch[0]

_IDS = None
def fix_evlist(c, k, x, buf):
    """anim event lists: tools/animfx.py typed override (validated 13483 base lists, crash fix13)"""
    global _IDS
    if x is None or x['data'] is None or len(x['data']) != len(buf): return 0
    if _IDS is None:
        import dlc_generic as DG, generic_store
        _IDS = DG.DlcIds(generic_store.load(), None)
    _IDS.local = {}
    return animfx.fix(x['data'], R.parse(x['reloc'], 'be'), buf, _IDS)

FIXES = {('script', 'sarray_count_byteclass'): fix_sarray, ('animinfo', 'rec_count'): fix_animinfo,
         ('animinfo', 'fill_wrap'): fix_animinfo, ('animinfo', 'ent_oob'): fix_animinfo,
         ('evlist', 'misframed_vs_xbox'): fix_evlist, ('evlist', '_list'): fix_evlist}

def fix_file(rel, path, g, findings):
    """apply the FIXES for the crash findings of one file; returns (new bytes or None, {fix: words})"""
    raw = open(path, 'rb').read()
    xs = xbox_dlc(rel)
    c = Ctx(rel, raw, g, xs)
    D = DW.read(raw, 'le')
    todo = collections.defaultdict(set)
    for f in findings:
        fn = FIXES.get((f['check'], f['code']))
        if fn is None or f['type'] is None: continue
        for k in c.by.get((f['type'], f['id']), []): todo[k].add(fn)
    st = collections.Counter()
    for k, fns in todo.items():
        buf = bytearray(D.sections[k].data)
        for fn in fns:
            n = fn(c, k, c.xsec(k), buf)
            st[fn.__name__] += n
        D.sections[k].data = bytes(buf)
    if not sum(st.values()): return None, st
    out = D.write('le')
    if raw[:4] == b'CDRM': out = DW.cdrm_encode(out, 'le')
    return out, st

def validate_fixes(limit=None):
    """apply the typed fixes on the REAL PC bytes of base pairs (Xbox source = base Xbox file): must change 0 words"""
    from rung1 import raw_pc
    names = sorted(n for n in pc_name_set() if n.endswith('.drm') and '/' not in n)[:limit]
    st = collections.Counter()
    for n in names:
        xs = xbox_base(n)
        if xs is None: continue
        try: c = Ctx(n, raw_pc(n), None, xs)
        except Exception: continue
        roots = set(obj_roots(c))
        for k, s in enumerate(c.secs):
            if s.type not in (7, 8): continue
            x = c.xsec(k)
            if x is None: continue
            buf = bytearray(s.data)
            if s.type == 8:
                st['sarray_sections'] += 1; st['sarray_changed_words'] += fix_sarray(c, k, x, buf)
            elif k in roots:
                st['animinfo_roots'] += 1; st['animinfo_changed_words'] += fix_animinfo(c, k, x, buf)
    print('fix validation on base pairs (PC bytes must stay unchanged):', dict(st))

if __name__ == '__main__':
    main()
