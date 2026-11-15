"""g_pda.drm (PDA) for DLC 2: merge the pack11 PDA into the player's PC g_pda with the replaced PC scripts PORTED the
way generalbank script 6 was (docs/WINDOWS_REBUILD.md findings 40 / 43; Q10 2026-11-11, workspace
docs/Befund-DLC2-PDA-1111.md).

Why: every DLC pack ships a complete g_pda.drm. tools/drm_merge_pc.py (finding 40) keeps the converted pack11 file and
takes the PC bytes only for sections the pack ships unchanged - so 12 PC scripts were replaced by their converted DLC
versions, and a NEW BASE GAME crashed after the opening (test 12, 2026-10-29: tru.exe +0xca260, the cdc::UIMenuWdgt
null-list crash of finding 43: member init blocks in Xbox byte order / Xbox layout of struct 351, vtables one slot
short). This tool decides per script, with a proof, and ports what has to be ported:

  recipe        sections (PC ids)                   rule                                         proof (learn)
  base-same     348 sections the pack ships as in   the PC section (tools/drm_merge_pc.py)       pack bytes = Xbox base bytes
                the Xbox base game
  keep_pc       42 changed scripts, e.g. 3361,      the PC section                               pack = Xbox base up to the
                3362, 3248, 3257 (of the 12)                                                     dependency order and the section
                                                                                                 indices of external relocations
  resident      63, 66 achievement, 72, 213         the PC section (the engine keeps the first   the PC generalbank holds the id
                larabase                            loaded copy - generalbank loads first)
  port          3347, 3360, 3365, 3367, 3368, 3384  converted pack11 section (Xbox offsets) +    DLC code / data change
                                                    external relocation targets checked by kind
                                                    and name + PC vtable slot 31 + init words
  new93         26427, 26428 (new uiscreen classes) converted + targets + slot 31 + init words
  new           24318 (derives from 90)             converted + targets (parent vtable shared)
  resident_new  90 dlcsystem                        the PC generalbank's section
  converted     5 changed DTPs, 13 changed + 4 new  the converted section (as drm_merge_pc); the
                textures, 1 new DTP                 converter gives the pack's change only
  (PC-only sections are appended, external relocation indices remapped.)
Init words of a ported / new script (members, arguments, locals): a member with a PC twin (Q55: recorded by learn -
pack entry -> Xbox base entry of the same Xbox name -> PC entry by its place in the declaration order,
tools/script_member_pairs.py; same type tag; until Q55 the PC member of the same converted name, a Symbol guess that
named neighbour entries), whose init tree has the same shape after the struct re-layout and whose init the pack did not change
(learn: Xbox base vs pack11) takes the PC words (tools/script_init_from_pc.copy_tree, struct 351 re-laid out by
copy); everything else is derived from the Xbox original word by word: UI text id (uitext 301 path [0, 92]) through
the locals map (PC prompt ids first), UI userTypes through the proven tools/ui_init_fix.py rules, the rest through
word classes learned from every Xbox base <-> PC script pair of generalbank + g_pda (key userType / tag / path, a
fallback key for chained list nodes; the list entry text id, userType 223 path [0, 0], proves as the locals class
id16a:101 = the locals map, Q48), struct 351 re-laid out by RELAYOUT; Xbox 0 / -1 stay; a float-shaped word
without a rule -> s32 (heuristic, listed); anything else keeps the converted word and is listed as a risk. Words of
structural arrays (and their count words) are never changed.

Gates (build and `gate`, exit 1 = nothing written): no section outside the ported set points into a ported script or
derives from one; every other PC section = the PC bytes (only pack-changed non-script sections may differ); every
external relocation of a ported / new script lands on the element of the Xbox target's kind and name (names: learned
base map + docs/data/sym_calibration_derived.json; TRUDLC_GPDA_SYM_EVIDENCE=FILE adds a developer evidence map; a
name only the map RULE guesses is reported as unverified, not failed); every ported / new uiscreen class: inherited
slots 0..31 = PC uiscreen 93 (slot 31 = f111), same inherited / own pattern as the PC version of the script (a PC-only
override - slot 17 "PDA menu onclicked" - is a WARN), every prototype vtIndex consistent; every struct-351 init of the
file in the PC layout; every ported / new script decodes without walker problems and its code opcodes = the Xbox
original; every text id leaf of a ported / new script = the rule word of the Xbox word (Q48: a member copied from the
PC gets its text ids by rule too - the PC re-authored some texts); relocations in bounds; read back.

Usage (from the repository root):
  ../bin/pyt -t 1800 tools/gpda_port.py analyze CONVERTED_G_PDA [--report R.json]
        developer, read-only (reads the Xbox base g_pda): classification, structure per version, references, init plan
  ../bin/pyt -t 1800 tools/gpda_port.py learn [--write]
        developer (reads the Xbox base g_pda + generalbank): recipes with proofs, members the pack changed, init rules,
        md5s of the PC / pack sections -> docs/data/gpda_port.json (no game bytes)
  ../bin/pyt -t 1800 tools/gpda_port.py build CONVERTED_G_PDA OUT_DIR [--only-safe] [--knowledge JSON]
        -> OUT_DIR/mods/g_pda.drm + OUT_DIR/build_report.json; CONVERTED_G_PDA = the pipeline's converted pack11 g_pda
        (stage 2b + fixes, e.g. work/rebuild/pipeline_check_1111b/dlc2/mods/g_pda.drm); reads the player's PC g_pda
        (patch.000, else bigfile.000), the PC generalbank (section 90), the pack11 g_pda (pack11.000) - each section
        md5-checked against the knowledge file - and the locals map (TRUDLC_LOCMAP, default
        work/rebuild/stage1/locmap_xbox_to_pc.json)
        --only-safe: the port recipes are NOT applied - their PC sections are kept (base game = PC; DLC PDA pages
        unreachable); the new scripts are still added
  ../bin/pyt -t 1800 tools/gpda_port.py gate G_PDA
        read-only: the static gates on any merged g_pda (finding 40's dlc2_merge fails 9 of them)
"""
import sys, os, json, struct, hashlib, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.realpath(os.path.join(HERE, '..'))
# Symbol maps: word rules use the converter's own map (DlcIds with its default calibration - member names and the
# Symbol paths in init data must stay alike); the NAME CHECK of relocation targets uses the learned base map + the
# base-derived calibration (exact entries only)
DERIVED = os.path.join(REPO, 'docs', 'data', 'sym_calibration_derived.json')
import drm_write as DW, drm_reloc as R, script_conv as SC
import dtp_word_classes as C

BS = chr(92)
NAME = 'g_pda.drm'
PACK = 'pack11'
UISCREEN = 93               # native uiscreen: PC has one more vtable slot (31 = f111) than the Xbox (finding 43 / 46)
SLOT = 31
# recipes by PC id (decided by `analyze`, docs/Befund-DLC2-PDA-1111.md)
KEEP_PC = (3361, 3362, 3248, 3257)
RESIDENT = (213, 66)
PORT = (3347, 3360, 3365, 3367, 3368, 3384)
NEW93 = (26427, 26428)
NEW = (24318, 90)

_IDS = None


def ids():
    global _IDS
    if _IDS is None:
        import dlc_generic as DG
        _IDS = DG.DlcIds()
    return _IDS


def symmap():
    """Xbox -> PC Symbol for exact name matching: the learned base map + the derived calibration (exact entries only)"""
    I = ids()
    import dlc_generic as DG
    m = {int(a): b for a, b in json.load(open(DERIVED))['symbols'].items()}
    extra = os.environ.get('TRUDLC_GPDA_SYM_EVIDENCE')      # developer: e.g. work/rebuild/sym_base_evidence.json
    if extra:
        d = json.load(open(extra)); m.update({int(a): b for a, b in d.get('symbols', d).items()})
    m.update(I.base.get(DG.SYM, {}))
    return m


def md5(b):
    return hashlib.md5(bytes(b)).hexdigest()


def k_(t, i):
    return '%d:%d' % (t, i)


# ------------------------------------------------------------------------------------------------ inputs
def read_pc():
    S = C.find(C.PC, 'le', 'pc-w' + BS + NAME)
    if not S: sys.exit('PC %s not found in %s' % (NAME, C.PC))
    return S


def read_pack():
    S = C.find([C.DLC_ROOT + q for q in C.PACKS if q.endswith('/%s.000' % PACK)], 'be', 'xenon-w' + BS + NAME)
    if not S: sys.exit('%s %s not found' % (PACK, NAME))
    return S


def read_xbase():
    return C.find(C.BASE, 'be', 'xenon-w' + BS + NAME)


def read_pc_generalbank():
    return C.find(C.PC, 'le', 'pc-w' + BS + 'generalbank.drm')


# ------------------------------------------------------------------------------------------------ script views
class View:
    """one script section: walker, elements by offset (kind, index, name Symbol), vtable targets, members"""
    def __init__(self, data, reloc, e):
        self.d, self.e, self.E = bytes(data), e, ('>' if e == 'be' else '<')
        self.rel = R.parse(reloc, e)
        self.it = dict(self.rel.internal)
        self.W = SC.Walk(self.d, self.rel, e).run()
        self.arr = {}
        for nm, t, n, sz in self.W.arrays:
            if nm in ('funcs', 'protos', 'members', 'sfi', 'states', 'deps', 'vtable', 'enums', 'structs'):
                self.arr.setdefault(nm, (t, n, sz))
        self.el = {}
        pn = {}
        if 'protos' in self.arr:
            t, n, sz = self.arr['protos']
            for k in range(n):
                a = t + sz * k; pn[a] = self.u16(a + 8)
                self.el[a] = ('proto', k, self.u16(a + 8))
        if 'funcs' in self.arr:
            t, n, sz = self.arr['funcs']
            for k in range(n):
                a = t + sz * k; self.el[a] = ('func', k, pn.get(self.it.get(a)))
        if 'members' in self.arr:
            t, n, sz = self.arr['members']
            for k in range(n):
                a = t + sz * k; self.el[a] = ('member', k, self.u16(a + 14))
        for nm in ('sfi', 'states', 'enums', 'structs'):
            if nm in self.arr:
                t, n, sz = self.arr[nm]
                for k in range(n): self.el.setdefault(t + sz * k, (nm, k, None))
        if 0x44 in self.it:
            self.el.setdefault(self.it[0x44], ('vtable', 0, None))
            for k, vte in self.vtable():
                if vte is not None: self.el.setdefault(vte, ('vte', k, None))

    def u32(self, o): return struct.unpack_from(self.E + 'I', self.d, o)[0]
    def u16(self, o): return struct.unpack_from(self.E + 'H', self.d, o)[0]

    def vt_size(self): return self.u16(0x3c)

    def native(self):
        """(package, native name) or None"""
        if 0x10 not in self.it: return None
        a = self.it[0x10]; z = self.d.find(b'\0', a)
        return self.d[a:z].decode('latin1')

    def vtable(self):
        """[(slot, VTE offset)]"""
        t = self.it.get(0x44)
        if t is None: return []
        return [(k, self.it.get(t + 4 * k)) for k in range(self.vt_size())]

    def vte_funcs(self, vte, S):
        """function entries a VTE points at: [(kind, section key or 'self', offset)]"""
        n = self.u32(vte)
        ext = {so: (si, do) for si, so, do in self.rel.external}
        out = []
        for j in range(1, n + 1):
            a = vte + 4 * j
            if a in self.it: out.append(('self', self.it[a]))
            elif a in ext: out.append((S[ext[a][0]], ext[a][1]))
            else: out.append(('null', None))
        return out

    def super_id(self):
        ids_ = self.rel.id_offsets()
        return self.u32(0x18) if 0x18 in ids_ else None

    def element(self, off):
        if off < 0x54: return ('root', off, None)
        return self.el.get(off)


def keys(S):
    return [(s['type'], s['id']) if isinstance(s, dict) else (s.type, s.id) for s in S]


# ------------------------------------------------------------------------------------------------ analyze
def code_equal_modulo_order(a, b):
    """pack section b = base section a up to the dependency-array order and the section index of external relocations
    (both Xbox): data with sorted dependency arrays equal, internal / id relocations equal, external relocations equal
    as (type, id) keys - a pack that only re-ordered its file"""
    return a['data'] is not None and b['data'] is not None and \
        SC.deps_normalized(a['data'], R.parse(a['reloc'], 'be'), 'be') == SC.deps_normalized(b['data'], R.parse(b['reloc'], 'be'), 'be')


def analyze(argv):
    rep_path = None
    if '--report' in argv: k = argv.index('--report'); rep_path = argv[k + 1]; del argv[k:k + 2]
    conv = argv[0]
    I = ids()
    xb = {(s['type'], s['id']): s for s in read_xbase()}
    PK = read_pack(); pk = {(s['type'], s['id']): s for s in PK}
    PCS = read_pc(); pc = {(s['type'], s['id']): s for s in PCS}
    gb = {(s['type'], s['id']) for s in read_pc_generalbank()}
    D = DW.read(open(conv, 'rb').read(), 'le'); cv = {(s.type, s.id): s for s in D.sections}
    out = collections.OrderedDict()
    print('%s: Xbox base %d, %s %d, PC %d, converted %d sections' % (NAME, len(xb), PACK, len(pk), len(pc), len(cv)))
    for (t, xi), s in sorted(pk.items()):
        if t != 8 or not s['data']: continue
        base = xb.get((t, xi))
        if base is not None and base['data'] == s['data']: continue
        pid = I(t, xi)
        row = dict(xbox=xi, pc=pid, cls='new' if base is None else 'changed', in_pc=(t, pid) in pc,
                   pc_generalbank=(t, pid) in gb)
        if base is not None:
            row['equal_modulo_order'] = code_equal_modulo_order(base, s)
        vx = View(s['data'], s['reloc'], 'be')
        row['pack'] = dict(len=len(s['data']), vt=vx.vt_size(), funcs=vx.arr.get('funcs', (0, 0))[1],
                           members=vx.arr.get('members', (0, 0))[1], super=vx.super_id())
        if (t, pid) in pc:
            vp = View(pc[(t, pid)]['data'], pc[(t, pid)]['reloc'], 'le')
            row['pc_layout'] = dict(len=len(vp.d), vt=vp.vt_size(), funcs=vp.arr.get('funcs', (0, 0))[1],
                                    members=vp.arr.get('members', (0, 0))[1], super=vp.super_id())
        out[k_(t, pid)] = row
        print('%-8s xbox %5d -> pc %5d  %-7s modulo-order-equal %-5s in PC g_pda %-5s in PC generalbank %-5s pack %s pc %s' % (
            k_(t, pid), xi, pid, row['cls'], row.get('equal_modulo_order'), row['in_pc'], row['pc_generalbank'],
            row['pack'], row.get('pc_layout')))
    print('changed / new NON-script sections of the pack (type:PC id  Xbox id  class  pack size / base size / PC size  '
          'words differing pack vs base  converted = PC?):')
    for (t, xi), s in sorted(pk.items()):
        if t == 8: continue
        base = xb.get((t, xi))
        if base is not None and base['data'] == s['data']: continue
        pid = I(t, xi); p = pc.get((t, pid)); c = cv.get((t, pid))
        nd = '-'
        if base is not None and len(base['data']) == len(s['data']):
            nd = sum(1 for o in range(0, len(s['data']) - 3, 4) if base['data'][o:o + 4] != s['data'][o:o + 4])
        print('   %d:%-6d %6d  %-7s %7s / %7s / %7s  %5s  %s' % (t, pid, xi, 'new' if base is None else 'changed', len(s['data']),
              len(base['data']) if base else '-', len(p['data']) if p else '-', nd,
              'PC missing' if p is None else (c is not None and c.data == p['data'])))
    # PC scripts that derive from a script we would replace, and PC sections with relocations into them
    PK_ = keys(PCS)
    repl = {pid for pid in PORT + NEW93}
    print('PC g_pda: scripts deriving from a ported script / external relocations into one:')
    for s in PCS:
        if s['type'] != 8 or not s['data']: continue
        v = View(s['data'], s['reloc'], 'le')
        if v.super_id() in repl: print('   %d derives from %d' % (s['id'], v.super_id()))
        if s['id'] in repl: continue
        into = collections.Counter(PK_[si][1] for si, so, do in v.rel.external if PK_[si][0] == 8 and PK_[si][1] in repl)
        if into: print('   %d -> %s' % (s['id'], dict(into)))
        refs = [v.u32(o) for o, t in v.rel.id_offsets().items() if t == 8 and o + 4 <= len(v.d) and v.u32(o) in repl]
        if refs: print('   %d id references to %s' % (s['id'], collections.Counter(refs)))
    # the PC slot-31 VTE of every 93 class
    print('PC slot %d of the classes deriving from %d (VTE -> target):' % (SLOT, UISCREEN))
    seen = collections.Counter()
    for s in PCS:
        if s['type'] != 8 or not s['data']: continue
        v = View(s['data'], s['reloc'], 'le')
        if v.super_id() != UISCREEN: continue
        vt = dict(v.vtable())
        vte = vt.get(SLOT)
        if vte is None: seen['no slot'] += 1; continue
        fs = v.vte_funcs(vte, PK_)
        seen[repr(fs)] += 1
    for kk, n in seen.most_common(): print('   %3d x %s' % (n, kk))
    # external relocations of the converted port / new scripts against the final layout of their targets
    final = {(s.type, s.id): (s.data, s.reloc) for s in D.sections}
    for k in KEEP_PC + RESIDENT: final[(8, k)] = (pc[(8, k)]['data'], pc[(8, k)]['reloc'])
    xl = {(8, k) for k in PORT + NEW93 + NEW}
    E = Ext(PK, final, xl, symmap())
    ck = keys(D.sections)
    inv = {(t, I(t, x)): (t, x) for (t, x) in pk}
    print('external relocations of the converted scripts (target = Xbox element by name in the final layout):')
    for pid in PORT + NEW93 + NEW:
        cs = cv[(8, pid)]; xs = pk[inv[(8, pid)]]
        res = ext_check(cs, xs, ck, E, lambda key: key)
        st = collections.Counter(r[3] for r in res)
        moved = sum(1 for r in res if r[2] is not None and r[2] != r[5])
        print('   %5d: %d relocations %s; converted offset differs from the planned one: %d' % (pid, len(res), dict(st), moved))
        for r in [r for r in res if r[3] != 'ok'][:6]:
            print('        +0x%x %s %s' % (r[0], r[3], r[4]))
        tg = collections.Counter(r[1] for r in res if r[2] is not None and r[2] != r[5])
        if tg: print('        moved per target: %s' % dict(tg))
    # init words: PC values for the paired members, rules for the DLC-only ones
    print('member / local init words (script-6 rule):')
    obs_all, xdata, tw = {}, {}, {}
    for pid in PORT:
        cs = cv[(8, pid)]; ps = pc[(8, pid)]; xs = pk[inv[(8, pid)]]
        xdata[pid] = xs['data']
        tw[pid] = twins_of(xs, xb[inv[(8, pid)]], ps)[0]
        d = bytearray(cs.data); ra = R.parse(cs.reloc, 'le'); st = collections.Counter(); log = []
        wa, ita0, wb, itb, obs = port_init(d, ra, ps['data'], ps['reloc'], xs['data'], None, st, log, pid, tw[pid])
        obs_all[pid] = (wa, ita0, wb, itb, obs, ps['data'])
        _, _, _, _, only, _ = init_pairs(bytearray(cs.data), R.parse(cs.reloc, 'le'), ps['data'], ps['reloc'], tw[pid])
        with_init = collections.Counter((k[0], k[3]) for k, la in only for a in la if (a + 16) in ita0)
        print('   %5d: %s; DLC-only with init (array, userType): %s' % (pid, dict(st), dict(with_init)))
        for l in log[:6]: print('     ' + l)
    rules, conflicts = learn_init_rules(obs_all, lambda sid: xdata[sid])
    print('   rules learned over the %d ported scripts: %d (keys with disagreeing scripts: %d)' % (len(obs_all), len(rules), conflicts))
    for pid in PORT + NEW93:
        cs = cv[(8, pid)]; xs = pk[inv[(8, pid)]]
        d = bytearray(cs.data); ra = R.parse(cs.reloc, 'le'); st = collections.Counter(); log = []
        p = pc.get((8, pid))
        port_init(d, ra, p['data'] if p else None, p['reloc'] if p else None, xs['data'], rules, st, log, pid, tw.get(pid, {}))
        print('   %5d DLC-only: %s' % (pid, {k: v for k, v in st.items() if 'TU-only' in k or 'DLC-only' in k}))
        for l in log[:6]: print('     ' + l)
    if rep_path:
        json.dump(out, open(rep_path, 'w'), indent=1)
        print('->', rep_path)


class Ext:
    """external relocation targets of a ported / new script, decided per relocation from the Xbox pack11 original:
    the Xbox target element (kind, name) and the element of the same kind and name in the FINAL target section -
    a section that keeps the Xbox layout (ported / new: the converter keeps the Xbox offsets) at the same offset, a
    PC-layout section (PC bytes) through script_conv.offset_map (elements paired by name Symbol, as
    tools/drm_put_sections.py --xbox) - then checked by kind and name"""
    def __init__(self, PK, final, xbox_layout, smap):
        self.PK, self.pk_keys = PK, keys(PK)
        self.pk = {(s['type'], s['id']): s for s in PK}
        self.final = final                  # {(type, PC id): (data, reloc)} of the final file
        self.xl = xbox_layout               # set of final keys that keep the Xbox layout
        self.smap = smap
        self.views, self.omaps = {}, {}

    def view(self, key, side):
        k = (key, side)
        if k not in self.views:
            if side == 'x': s = self.pk[key]; self.views[k] = View(s['data'], s['reloc'], 'be')
            else: d, rl = self.final[key]; self.views[k] = View(d, rl, 'le')
        return self.views[k]

    def omap(self, xkey, fkey):
        k = (xkey, fkey)
        if k not in self.omaps:
            xs = self.pk[xkey]; d, rl = self.final[fkey]
            self.omaps[k] = SC.offset_map(xs['data'], R.parse(xs['reloc'], 'be'), d, R.parse(rl, 'le'), self.smap)
        return self.omaps[k]

    def target(self, xsi, xdo, fkey):
        """(new offset, status, detail); status ok / name? (no name to compare) / FAIL..."""
        xkey = self.pk_keys[xsi]
        if (xkey[0], ids()(xkey[0], xkey[1])) != fkey:
            return None, 'FAIL section', 'Xbox %s is not %s' % (xkey, fkey)
        if xkey[0] != 8:
            return xdo, 'ok', 'non-script target'
        vx = self.view(xkey, 'x'); ex = vx.element(xdo)
        if fkey in self.xl:
            new = xdo
        elif ex is not None and ex[0] in ('vtable', 'vte'):
            # a class without own virtual functions shares its parent's vtable (24318 -> 90): the same table / slot
            vf = self.view(fkey, 'f')
            if vf.vt_size() != vx.vt_size():
                return None, 'FAIL vtable size', 'Xbox %s %d slots, %s %d' % (xkey, vx.vt_size(), fkey, vf.vt_size())
            new = vf.it.get(0x44) if ex[0] == 'vtable' else dict(vf.vtable()).get(ex[1])
            ef = vf.element(new) if new is not None else None
            if ef is None or ef[:2] != ex[:2]:
                return new, 'FAIL kind', 'Xbox %s +0x%x %s -> %s %s' % (xkey, xdo, ex, fkey, ef)
            return new, 'ok (same vtable slot)', ''
        else:
            new = self.omap(xkey, fkey).get(xdo)
            if new is None:
                return None, 'FAIL unmapped', 'Xbox %s +0x%x %s' % (xkey, xdo, ex)
        vf = self.view(fkey, 'f'); ef = vf.element(new)
        if ex is None:
            return new, 'FAIL no Xbox element', 'Xbox %s +0x%x' % (xkey, xdo)
        if ef is None or ef[0] != ex[0]:
            return new, 'FAIL kind', 'Xbox %s +0x%x %s -> %s +0x%x %s' % (xkey, xdo, ex, fkey, new, ef)
        if ex[0] in ('func', 'proto', 'member'):
            if fkey in self.xl and ex[1] == ef[1]:
                return new, 'ok', 'same index (Xbox layout)'
            if ex[2] in (None, 0, 0xffff):
                return new, 'ok' if ex[2] == ef[2] else 'FAIL name', 'unnamed %s / %s' % (ex, ef)
            exact = self.smap.get(ex[2])
            want = exact if exact is not None else ids().sym(ex[2])
            if want != ef[2]:
                if ex[0] == 'func' and ex[1] == ef[1] and vx.native() and vx.native() == vf.native() and \
                        vx.arr['funcs'][1] == vf.arr['funcs'][1]:
                    return new, 'ok (native, same index, same count)', 'Xbox name %s / PC %s' % (ex[2], ef[2])
                if exact is None:
                    return new, 'name unverified (no exact map entry; the map rule guesses another name)', \
                        'Xbox %s %s -> %s %s' % (xkey, ex, fkey, ef)
                return new, 'FAIL name', 'Xbox %s +0x%x %s (PC name %s) -> %s +0x%x %s' % (xkey, xdo, ex, want, fkey, new, ef)
            return new, 'ok' if exact is not None else 'ok (name by map rule)', ''
        return new, 'ok', ''


def ext_check(conv_sec, xsec, conv_keys, E, fkey_of):
    """[(source offset, final key, new offset, status, detail, converted target offset)] for every external
    relocation of a converted script (source offsets = Xbox offsets)"""
    xr = R.parse(xsec['reloc'], 'be')
    xext = {so: (si, do) for si, so, do in xr.external}
    out = []
    for si, so, do in R.parse(conv_sec.reloc, 'le').external:
        if so not in xext:
            out.append((so, None, None, 'FAIL no Xbox relocation', 'converted +0x%x' % so, do)); continue
        xsi, xdo = xext[so]
        fkey = fkey_of(conv_keys[si])
        new, stt, det = E.target(xsi, xdo, fkey)
        out.append((so, fkey, new, stt, det, do))
    return out


def init_pairs(d, ra, pdata, preloc, twins):
    """members / args / locals of a converted script paired with its PC version: returns (walk A, its internal map,
    walk B, its internal map, pairs [(key, a entry, b entry)], only-A keys, counts). twins = {entry offset: PC entry
    offset} (script_member_pairs.chain, Q55; until Q55 the same-name PC member - a converter name guess)"""
    import script_init_from_pc as SIP
    wa = SC.Walk(bytes(d), ra, 'le'); wa.run()
    ma = SIP.members(wa, bytes(d), 'le')
    if pdata is None:           # a new script: nothing to pair
        return wa, None, None, [], list(ma.items()), collections.Counter()
    rb = R.parse(preloc, 'le')
    wb = SC.Walk(pdata, rb, 'le'); wb.run()
    pairs, only, st = [], [], collections.Counter()
    for key, la in ma.items():
        rest = []
        for a in la:
            b = twins.get(a)
            if b is None or struct.unpack_from('<IH', pdata, b) != (key[2], key[3]): rest.append(a); continue
            pairs.append((key, a, b))
        if rest: only.append((key, rest))
    return wa, wb, rb, pairs, only, st


def twins_of(xs, xb, ps):
    """developer: {pack entry offset: PC entry offset} of one ported script (pack / Xbox base / PC section dicts)"""
    import script_member_pairs as MP
    return MP.chain(xs['data'], xs['reloc'], xb['data'], xb['reloc'], ps['data'], ps['reloc'], ids())


def port_init(d, ra, pdata, preloc, xdata, rules, st, log, sid, twins=None):
    """script-6 init step on bytearray d / relocation object ra of a ported script: every paired member / arg / local
    init tree takes the PC words (struct nodes re-laid out to the PC layout, tools/script_init_from_pc.copy_tree); the
    DLC-only ones get their words from the Xbox original through `rules` (per type tag / userType / path, learned
    from the pairs of all ported scripts); returns the observation pairs (for learning) when rules is None"""
    import script_init_from_pc as SIP
    wa, wb, rb, pairs, only, c0 = init_pairs(d, ra, pdata, preloc, twins or {})
    st.update(c0)
    ita = dict(ra.internal); itb = dict(rb.internal) if rb is not None else {}; ita0 = dict(ita)
    seen, shapes, obs = set(), [], []
    for key, a, b in pairs:
        ia, ib = ita.get(a + 16), itb.get(b + 16)
        if ia is None and ib is None: continue
        if (ia is None) != (ib is None): st['init present on one side only (kept)'] += 1; continue
        st['%s with init paired' % key[0]] += 1; obs.append(((key[2], key[3]), ia, ib))
        SIP.copy_tree(d, wa, ita, pdata, wb, itb, ia, ib, st, seen, shapes)
    for x in shapes: log.append('   %d: node of another shape kept (ours 0x%x %d words, PC 0x%x %d words)' % ((sid,) + x))
    if rules is not None:
        for key, la in only:
            for a in la:
                ia = ita.get(a + 16)
                if ia is None: continue
                st['DLC-only %s with init' % key[0]] += 1
                unknown = SIP.apply_rules(d, wa, ita, xdata, ia, key[2], key[3], rules, st)
                if unknown: log.append('   %d: DLC-only %s %d (userType %d): glyph value not in the learned map' % (sid, key[0], key[1], key[3]))
    ra.internal = list(ita.items())
    return (wa, ita0, wb, itb, obs)


def learn_init_rules(obs_all, xdata_of):
    """script_init_from_pc.learn_rules over the pairs of all ported scripts: (type tag, userType, path) -> byte order
    or u16 value map; a key whose observations disagree between scripts gets no rule"""
    import script_init_from_pc as SIP
    per = collections.defaultdict(list)
    for sid, (wa, ita0, wb, itb, obs, pdata) in obs_all.items():
        r = SIP.learn_rules(wa, ita0, xdata_of(sid), pdata, wb, itb, obs)
        for k, v in r.items(): per[k].append(v)
    rules, conflicts = {}, 0
    for k, vs in per.items():
        if all(v == vs[0] for v in vs): rules[k] = vs[0]
        else: conflicts += 1
    return rules, conflicts


BASE_FILES = ('generalbank.drm', 'g_pda.drm')

# Native structs the PC re-laid out (same size, other field positions). 351 = menu widget parameters
# (cdc::UIMenuWdgt, finding 43 / test 5e): 13 base pairs (generalbank 6, 34, 40, 41, 42, 45, 46, 107 x 2; g_pda 3207,
# 3220, 3224, 34) - node 1 (31 words, behind the member's root pointer): words 0..21 in place; Xbox 22 (u32 count) ->
# PC 23; Xbox 23 = u8 flag + 3 zero bytes -> PC 24 = that u8 as u32; Xbox 24 / 25 -> PC 25 / 26; the list pointer Xbox
# 26 -> PC 27; Xbox 27..29 -> PC 28..30; Xbox 30 (always 0) dropped; PC 22 = 1 in all 13 (a PC-only field). The counts
# that differ (3207: 10 -> 11, script 6: 6 -> 5 ...) are re-authored PC values, not the rule.
RELAYOUT = {351: dict(move=dict([(k, k) for k in range(22)] + [(22, 23), (24, 25), (25, 26), (26, 27), (27, 28),
                                                              (28, 29), (29, 30)]),
                      byte=(23, 24), const={22: 1}, zero_x=(30,), words=31)}


def relayout_path(ut, path):
    """Xbox init path -> PC init path for a re-laid out struct (None: a word the rule handles itself)"""
    R_ = RELAYOUT.get(ut)
    if R_ is None or len(path) < 2 or path[0] != 0: return path
    k = path[1] // 4
    if k not in R_['move']: return None
    return (0, R_['move'][k] * 4) + tuple(path[2:])


def relayout_pc_special(ut, path):
    R_ = RELAYOUT.get(ut)
    return R_ is not None and len(path) == 2 and path[0] == 0 and path[1] // 4 in (set(R_['const']) | {R_['byte'][1]})


def relayout_special(ut, xd, W, ia, e):
    """[(PC word index in node 1, u32 value)] of the fields the rule sets itself; None when the Xbox node breaks the
    rule's assumptions (the three padding bytes of the flag word or the dropped word not 0, other node size)"""
    R_ = RELAYOUT[ut]
    n1 = W.it.get(ia)
    if n1 is None: return None
    E = '>' if e == 'be' else '<'
    if n1 + 4 * R_['words'] > len(xd): return None
    fb = xd[n1 + 4 * R_['byte'][0]:n1 + 4 * R_['byte'][0] + 4]
    flag = fb[0] if e == 'be' else fb[0]
    if any(fb[1:]): return None
    if any(struct.unpack_from(E + 'I', xd, n1 + 4 * z)[0] for z in R_['zero_x']): return None
    return [(k, v) for k, v in R_['const'].items()] + [(R_['byte'][1], flag)]


def fallback_key(ut, tag, path):
    """rule key without the full path: chained list nodes (struct 361 button lists, menu entry lists) repeat the same
    node at growing depth - (userType, tag, depth class, offset in the node)"""
    return ('fb', ut, tag, len(path) if len(path) <= 3 else 'deep', path[-1] if path else None)


def base_pairs():
    """(Xbox base script, PC script) pairs of the same name in generalbank + g_pda: yields (name, xd, xrl, pd, prl)"""
    import script_func_list as FL
    import ui_init_fix as U
    I = ids()
    for name in BASE_FILES:
        X, _ = FL.sections('xbox:' + name)
        P, _ = FL.sections('pc:' + name)
        pmap = {}
        for t, sid, d, rl in P:
            if t == 8 and d: pmap.setdefault(U.script_name(d, 'le'), []).append((sid, d, rl))
        for t, sid, xd, xrl in X:
            if t != 8 or not xd: continue
            a, b = U.script_name(xd, 'be')
            cand = pmap.get((I.sym(a), I.sym(b)))
            if not cand: continue
            yield name, sid, xd, xrl, cand[0][1], cand[0][2]


def learn_base_rules(skip_uts=()):
    """per (PC userType, type tag, path) the word class that turns every informative Xbox base word into the PC word,
    over the base script pairs of generalbank + g_pda (tools/ui_init_fix.py learn, for every userType); plus the
    struct nodes whose shape differs (pointer positions) collected per (userType, path) for the re-layout rules"""
    import ui_init_fix as U
    import script_learn as L
    import script_init_from_pc as SIP
    import script_member_pairs as MP
    I = ids()
    obs = collections.defaultdict(list); st = collections.Counter(); shapes = collections.defaultdict(list)
    for fname, sid, xd, xrl, pd, prl in base_pairs():
        Wx, rx = U.walk(xd, xrl, 'be'); Wp, rp = U.walk(pd, prl, 'le')
        nx, np_ = U.no_touch(rx), U.no_touch(rp)
        mx = SIP.members(Wx, xd, 'be')
        # Q55: PC twins by the place in the declaration order (script_member_pairs.align), not the guessed name
        twin, tst = MP.align(xd, xrl, pd, prl, I, None, Wx=Wx, Wp=Wp)
        for k, v in tst.items(): st['twins ' + k] += v
        st['base script pairs'] += 1
        for (arr, nm, tag, ut), la in mx.items():
            put = I.sym(ut)
            if put in skip_uts: continue
            for ma in la:
                mb = twin.get(ma)
                if mb is None: continue
                if struct.unpack_from('<IH', pd, mb) != (tag, put): st['twins with another userType (skipped)'] += 1; continue
                ia, ib = Wx.it.get(ma + 16), Wp.it.get(mb + 16)
                if ia is None or ib is None: continue
                lx, lp = list(SIP.leaves(Wx, Wx.it, ia)), list(SIP.leaves(Wp, Wp.it, ib))
                lxm = [(relayout_path(put, p), o) for p, o in lx]
                if put in RELAYOUT:
                    sp = relayout_special(put, xd, Wx, ia, 'be')
                    if sp is not None:
                        for pcw, val in sp:       # the re-laid out fields: rule check against the PC word
                            pw = struct.unpack_from('<I', pd, Wp.it[ib] + 4 * pcw)[0] if ib in Wp.it else None
                            st['relayout fields = PC' if pw == val else 'relayout fields: another PC value'] += 1
                    lxm = [(p, o) for p, o in lxm if p is not None]
                    lp = [(p, o) for p, o in lp if not relayout_pc_special(put, p)]
                if [p for p, _ in lxm] != [p for p, _ in lp]:
                    st['members with another init tree shape'] += 1
                    shapes[put].append((fname, sid, arr, nm, xd, Wx, ia, pd, Wp, ib))
                    continue
                st['members paired'] += 1
                for (path, ox), (_, op) in zip(lxm, lp):
                    if ox in nx or op in np_ or ox + 4 > len(xd) or op + 4 > len(pd): continue
                    o2 = (bytes(xd[ox:ox + 4]), bytes(pd[op:op + 4]))
                    obs[(put, tag, path)].append(o2)
                    obs[fallback_key(put, tag, path)].append(o2)
    votes = collections.defaultdict(collections.Counter)
    for key, Lo in obs.items():         # proof of the text id rule on the base pairs (+ the PC's own prompt ids)
        if key[0] != 'fb' and (key[0], key[2]) in TEXT_ID:
            for x, p in Lo:
                w = text_id_word(x, pc_first=False)
                st['text id rule on base pairs (locals map only): %s' % ('= PC' if w == p else 'Xbox 0' if x == b'\0\0\0\0' else
                                                                         'not mappable' if w is None else 'another PC id')] += 1
                if w is not None and w != p and x[2:] == b'\0\0': votes[struct.unpack('>H', x[:2])[0]][struct.unpack('<I', p)[0]] += 1
    TEXT_PC.clear()
    XT, PT = text_tables()
    for xi, c in votes.items():
        if len(c) != 1: st['text ids with several PC prompt ids (locals map kept)'] += 1; continue
        pid = next(iter(c))
        # Q48: a PC id is a prompt id only when it says the same as the Xbox string (button glyphs aside, Xbox 98
        # -> PC 120); the other votes are base members paired by a guessed Symbol name one entry off (Xbox 1034 ->
        # PC 1110, 1035 -> 1111 = map(1034)) or re-authored PC lists - the locals map stays
        if same_text(XT, xi, PT, pid): TEXT_PC[xi] = pid
        else: st['text ids: PC id says something else (locals map kept)'] += 1
    st['text ids: PC prompt ids learned'] = len(TEXT_PC)
    rules = {}
    for key, Lo in obs.items():
        info = []
        for x, p in Lo:
            outs = {c: L.apply_word(x, c, I) for c in L.CLASSES}
            if len(set(outs.values())) == 1 and outs['s32'] == p: continue
            cs = {c for c, v in outs.items() if v == p}
            if not cs: st['observations with another PC value'] += 1; continue
            info.append((x, p, cs))
        if not info: st['keys without information'] += 1; continue
        ok = set.intersection(*[s for _, _, s in info])
        if not ok and all('s32' in s or ('raw' in s and U.text_word(x)) for x, _, s in info):
            rules[key] = 's32text'; continue
        if not ok:
            if all(s & U.ID_CLASSES for _, _, s in info): rules[key] = 'id-mixed'; continue
            st['contradicting keys'] += 1; rules[key] = None; continue
        rules[key] = next((q for q in U.PREF if q in ok), None) or sorted(ok, key=lambda q: L.CLASSES.index(q))[0]
    for key, c in rules.items():        # proof size of every text id leaf (locals class) - needs the pipeline locals map
        if c in LOC_RULES and key[0] != 'fb':
            st['locals class %s: observations / = PC' % rkey(key)] = '%d / %d' % (
                len(obs[key]), sum(L.apply_word(x, c, I) == p for x, p in obs[key]))
    return rules, shapes, st


# ------------------------------------------------------------------------------------------------ knowledge (learn)
KNOW = os.path.join(REPO, 'docs', 'data', 'gpda_port.json')
# -2 (Q48): re-learned with the Q46 DlcIds.loc (pipeline locals map); -1 was learned while DlcIds.loc returned the Xbox
# index, so the text id leaves 223 [0, 0] / 301 [0, 92] got a coincidental unit-id class id16a:110 (5 / 4 observations)
# and the DLC list entries kept the raw Xbox string index (23 words in 3347 / 3360 / 3367, 1 in 3384)
# -3 (Q55): base rules learned on member twins by declaration order (tools/script_member_pairs.py) instead of the
# converter's guessed names; member_twins = the PC twin entry offset of every pack entry of a ported script
# -4 (E2-8, 2026-11-14): re-learned with the Q58 Symbol twins (docs/data/symbol_twins.json; -3 was learned before
# them): base script pairs 266 -> 285, init rules 786 -> 909 (123 new keys, 9 changed: s32 / id32:7 -> id-mixed,
# raw -> s32text), ui rules 181 -> 200; 3 member twins of 3347 moved one PC entry (tag-59 members Xbox userTypes 5425 /
# 5427 / 5429: 5427 = PC 4971 proven by the same-layout pair 3238 <-> 3379); recipes, md5s, changed members unchanged
VERSION = 'G20261114-4'
UI_UTS = (301, 303, 316, 320)
LOC_RULES = ('id16a:101', 'id32:101')     # locals string id classes (tools/script_learn.py; DlcIds.loc = locals map)
PH = 0xBEEBBEEB


def rkey(k):
    return '|'.join(str(x) if not isinstance(x, tuple) else 'p' + '/'.join(map(str, x)) for x in k)


def member_leaves_words(d, rl, e):
    """{(array, name, tag, userType, n-th): [(path, word)]} of every member / arg / local with init (Xbox side)"""
    import script_init_from_pc as SIP
    W = SC.Walk(d, R.parse(rl, e), e).run()
    out = {}
    for key, la in SIP.members(W, d, e).items():
        for j, a in enumerate(la):
            ia = W.it.get(a + 16)
            if ia is None: continue
            out[key + (j,)] = [(p, bytes(d[o:o + 4])) for p, o in SIP.leaves(W, W.it, ia)]
    return out


def learn(argv):
    """developer: decide the recipes with proofs, learn the init rules, record md5s (no game bytes) -> knowledge"""
    write = '--write' in argv
    I = ids()
    XB = read_xbase(); xb = {(s['type'], s['id']): s for s in XB}
    PK = read_pack(); pk = {(s['type'], s['id']): s for s in PK}
    PCS = read_pc(); pc = {(s['type'], s['id']): s for s in PCS}
    gb = {(s['type'], s['id']) for s in read_pc_generalbank()}
    rec, base_same, why = {}, {}, {}
    for (t, xi), s in pk.items():
        pid = I(t, xi); key = k_(t, pid); b = xb.get((t, xi))
        if b is not None and b['data'] == s['data'] and b['reloc'] == s['reloc']:
            if (t, pid) in pc: base_same[key] = md5(s['data'] + s['reloc'])
            continue
        if t != 8 or not s['data']: rec[key] = 'converted'; why[key] = 'non-script, changed / new by the pack'; continue
        if b is None:
            v = View(s['data'], s['reloc'], 'be')
            if (t, pid) in gb: rec[key] = 'resident_new'; why[key] = 'new in g_pda, resident in the PC generalbank'
            elif v.super_id() == UISCREEN: rec[key] = 'new93'; why[key] = 'new DLC class of uiscreen 93'
            else: rec[key] = 'new'; why[key] = 'new DLC script'
            continue
        if code_equal_modulo_order(b, s):
            rec[key] = 'keep_pc'; why[key] = 'pack = Xbox base up to dependency order / section indices'; continue
        if (t, pid) in gb:
            rec[key] = 'resident'; why[key] = 'resident in the PC generalbank (the engine keeps the first loaded copy)'; continue
        rec[key] = 'port'; why[key] = 'DLC code / data change'
    want = dict([(k_(8, p), 'port') for p in PORT] + [(k_(8, p), 'new93') for p in NEW93])
    bad = [k for k, v in want.items() if rec.get(k) != v]
    if bad: sys.exit('recipes differ from the expected ones: %s' % [(k, rec.get(k)) for k in bad])
    # paired members whose init the pack changed against the Xbox base: their words come from the rules, not the PC
    inv = {(t, I(t, x)): (t, x) for (t, x) in pk}
    changed_members = {}
    for key, r in rec.items():
        if r != 'port': continue
        t, pid = map(int, key.split(':')); xk = inv[(t, pid)]
        a = member_leaves_words(xb[xk]['data'], xb[xk]['reloc'], 'be')
        b = member_leaves_words(pk[xk]['data'], pk[xk]['reloc'], 'be')
        ch = sorted({k[:4] for k in b if k in a and a[k] != b[k]})
        changed_members[key] = [[x[0], x[1], x[2], x[3]] for x in ch]
    # Q55: the PC twin of every member / arg / local of a ported script: pack entry -> Xbox base entry (same Xbox
    # Symbols) -> PC entry (place in the declaration order, script_member_pairs) - entry offsets only
    twins, twin_stats = {}, {}
    for key, r in rec.items():
        if r != 'port': continue
        t, pid = map(int, key.split(':')); xk = inv[(t, pid)]
        m, s_ = twins_of(pk[xk], xb[xk], pc[(t, pid)])
        twins[key] = sorted([a, b] for a, b in m.items())
        twin_stats[key] = dict(s_)
        print('twins %s: %s' % (key, {k: v for k, v in s_.items() if 'members' in k or k.startswith('pack entries')}))
    rules, shapes, st = learn_base_rules()
    import ui_init_fix as U
    urules, ust, ucontra = U.learn()
    if ucontra: sys.exit('ui_init_fix rules have contradictions')
    K = dict(version=VERSION, about='tools/gpda_port.py knowledge: recipes per g_pda section (PC ids), md5 of the pack11 '
             'sections they were decided on, members whose init the pack changed, init word rules learned from the '
             'base game (Xbox base <-> PC script pairs of generalbank + g_pda) - no game bytes',
             recipes=rec, reasons=why, base_same=base_same,
             pack_md5={k_(t, I(t, x)): md5(s['data'] + s['reloc']) for (t, x), s in pk.items()},
             pc_md5={k_(t, i): md5(s['data'] + s['reloc']) for (t, i), s in pc.items()},
             changed_members=changed_members,
             member_twins=twins, member_twin_stats=twin_stats,
             rules={rkey(k): v for k, v in rules.items()},
             ui_rules={rkey(k): [v[1], v[3]] for k, v in urules.items()},
             text_id_pc={str(k): v for k, v in sorted(TEXT_PC.items())},
             learn_stats=dict(st), ui_learn_stats={k: v for k, v in ust.items() if isinstance(v, int)})
    cnt = collections.Counter(rec.values())
    print('recipes: %s' % dict(cnt))
    for k in sorted(rec, key=lambda q: (rec[q], int(q.split(':')[0]), int(q.split(':')[1]))):
        if rec[k] != 'converted': print('   %-9s %-12s %s' % (k, rec[k], why[k]))
    print('base-same sections: %d; paired members the pack changed: %s' % (len(base_same), {k: len(v) for k, v in changed_members.items()}))
    print('init rules: %d (%s); learn %s' % (len(rules), collections.Counter(map(str, rules.values())).most_common(8), dict(st)))
    print('ui_init_fix rules: %d' % len(urules))
    if write:
        json.dump(K, open(KNOW, 'w'), indent=0, sort_keys=True)
        print('->', KNOW)


def load_knowledge(path=KNOW):
    K = json.load(open(path))
    def pk(s):
        out = []
        for part in s.split('|'):
            if part.startswith('p'): out.append(tuple(int(x) for x in part[1:].split('/') if x != ''))
            elif part.lstrip('-').isdigit(): out.append(int(part))
            else: out.append(part)
        return tuple(out)
    K['_rules'] = {pk(k): v for k, v in K['rules'].items()}
    K['_ui'] = {pk(k): v for k, v in K['ui_rules'].items()}
    if 'member_twins' not in K: sys.exit('knowledge %s has no member_twins (learned before Q55) - run learn --write' % path)
    K['_twins'] = {key: {a: b for a, b in v} for key, v in K['member_twins'].items()}
    TEXT_PC.clear(); TEXT_PC.update({int(k): v for k, v in K.get('text_id_pc', {}).items()})
    # text id leaves: the UI text element + every leaf whose learned rule is the locals class (223 [0, 0], Q48)
    K['_text'] = set(TEXT_ID) | {(k[0], k[2]) for k, v in K['_rules'].items() if v == 'id16a:101' and k[0] != 'fb'}
    TEXT_KEYS.clear(); TEXT_KEYS.update(K['_text'])
    return K


# ------------------------------------------------------------------------------------------------ build steps
# UI text element string id (uitext 301, init path [0, 92]; the record `ffffffff 0 colour colour | id w1 w2 w3`): the
# Xbox word holds the locals string index in its high u16 (`0161 0000` = 353 "BACK"), the PC word the PC string id as
# u32 (`75010000` = 375). The converter has no locals map (dlc_generic.DlcIds.loc reads work/generic/locals/, which the
# pipeline does not write) and mapped the index as a Symbol (353 -> 355); the base rule learner even finds a
# coincidental id class. Rule = tools/script_uitext_fix.py: PC id from locmap_xbox_to_pc.json (tools/locals.py build).
TEXT_ID = {(301, (0, 92))}
_LOCMAP = None


def locmap():
    global _LOCMAP
    if _LOCMAP is None:
        p = os.environ.get('TRUDLC_LOCMAP') or os.path.join(REPO, 'work', 'rebuild', 'stage1', 'locmap_xbox_to_pc.json')
        if os.path.isdir(p): p = os.path.join(p, 'locmap_xbox_to_pc.json')
        if not os.path.exists(p): sys.exit('locals map not found: %s (TRUDLC_LOCMAP)' % p)
        raw = open(p, 'rb').read()
        _LOCMAP = ({int(k): v for k, v in json.loads(raw)['map'].items()}, os.path.relpath(p), md5(raw))
    return _LOCMAP


TEXT_PC = {}        # Xbox index -> PC id the PC's own base menus use for the same prompt (learn: base pairs, unanimous,
                    # same text up to the button glyphs - Q48)
TWINS = []          # build: text ids of members copied from the PC that the rules replaced (another text in the PC)
TEXT_KEYS = set()   # (userType, path) of the text id leaves (load_knowledge)


def text_id_word(xw, pc_first=True):
    """PC word of a UI text id from the Xbox word, or None (not the index-in-high-half form / not in the map). Button
    prompts: where the PC base menus show another string for the same Xbox prompt (Xbox 98 "[A] SELECT" -> PC 120,
    115 / 116 -> 45 / 46 ...: the PC rewords controls, docs Befund-Tasten-Symbol-1111.md), that PC id wins"""
    hi, lo = struct.unpack('>HH', xw)
    if lo != 0: return None
    if hi == 0: return b'\0\0\0\0'
    v = TEXT_PC.get(hi) if pc_first else None
    if v is None: v = locmap()[0].get(hi)
    return None if v is None else struct.pack('<I', v)


def text_tables():
    """developer (learn): (Xbox TU English strings, PC strings) - the PC table is the pipeline's locals.bin_001 next to
    the locals map (work/rebuild/stage1/mods/local/), i.e. the PC original table + the appended DLC strings"""
    import locals as LC
    p = os.path.join(os.path.dirname(os.path.abspath(locmap()[1])), 'mods', 'local', 'locals.bin_001')
    if not os.path.exists(p): sys.exit('PC string table not found: %s' % p)
    tu, e = LC.files('tu')
    return LC.parse(tu[0xfffff7e1], e)[1], LC.parse(open(p, 'rb').read(), 'le')[1]


def same_text(XT, xi, PT, pid):
    """the Xbox string xi and the PC string pid say the same - button glyphs (U+1800..U+18FF) and spacing aside"""
    if not (0 <= xi < len(XT) and 0 <= pid < len(PT)): return False
    norm = lambda b: ' '.join(''.join(ch for ch in b.decode('utf-8', 'replace') if not 0x1800 <= ord(ch) <= 0x18ff).split())
    return norm(XT[xi]) == norm(PT[pid])


def text_rule_word(ut, pp, xw):
    """the PC word the rules give a text id leaf (UI text element: proven prompt id, else the locals map; list entry:
    the locals map); None when the Xbox word is not an index (low half set) or the index is not in the map"""
    if (ut, pp) in TEXT_ID: return text_id_word(xw)
    hi, lo = struct.unpack('>HH', xw)
    if lo: return None
    if hi in (0, 0xffff): return xw[:2][::-1] + b'\0\0'
    v = locmap()[0].get(hi)
    return None if v is None else struct.pack('<I', v)


def text_after_copy(d, xd, Wx, ia, ut, K, st, sid, label):
    """Q48: after a member was copied from the same-name PC member, every text id leaf gets the word the rules derive
    from the Xbox word (locals map; UI text: proven prompt id first) - the text names the entry and the ported code is
    the Xbox code. Member names of ported scripts are the converter's Symbol guesses (dlc_generic.DlcIds.sym
    'guess_lower', off by 1..8 entries in several g_pda ranges), so a same-name PC member can be a neighbour entry, and
    the PC re-authored some lists; the other words of the member stay the PC copy (listed in TWINS)"""
    import script_init_from_pc as SIP
    for p, o in SIP.leaves(Wx, Wx.it, ia):
        pp = relayout_path(ut, p)
        if pp is None or (ut, pp) not in K['_text']: continue
        xw = bytes(xd[o:o + 4]); want = text_rule_word(ut, pp, xw)
        if want is None or bytes(d[o:o + 4]) == want: continue
        TWINS.append('%d %s ut %d path %s +0x%x: Xbox %s, PC copy %s -> %s' % (sid, label, ut, list(pp), o, xw.hex(),
                                                                             bytes(d[o:o + 4]).hex(), want.hex()))
        d[o:o + 4] = want
        st['text ids: the same-name PC member holds another text id -> rule word (ut %d)' % ut] += 1
        st['init words changed'] += 1


def L_apply(xw, cls):
    import script_learn as L
    return L.apply_word(xw, cls, ids())


def word_by_rule(xw, cls, I):
    import script_learn as L
    import ui_init_fix as U
    if cls == 's32text': return xw if U.text_word(xw) else L.apply_word(xw, 's32', I)
    return L.apply_word(xw, cls, I)


def rule_member(d, ita, xd, Wx, ia, ut, tag, K, st, risk, sid, label):
    """the init words of one member / arg / local from the Xbox original by rule (re-laid out structs included);
    pointer words and relocation slots are never written; words without a rule keep the converted value"""
    import script_init_from_pc as SIP
    import ui_init_fix as U
    I = ids()
    n1 = Wx.it.get(ia)
    moved = {}
    if ut in RELAYOUT:
        R_ = RELAYOUT[ut]
        sp = relayout_special(ut, xd, Wx, ia, 'be')
        if sp is None or n1 is None or ita.get(ia) != n1:
            risk.append('%d %s: struct %d node breaks the re-layout rule - kept converted' % (sid, label, ut))
            st['re-layout refused'] += 1; return
        # move the pointer slots of node 1 (pop all first: old and new slots may overlap)
        ptrs = [(k, ita.pop(n1 + 4 * k)) for k in range(R_['words']) if (n1 + 4 * k) in ita]
        for k, tg in ptrs:
            if k not in R_['move']:
                risk.append('%d %s: pointer at a dropped struct word' % (sid, label)); st['re-layout refused'] += 1; return
            ita[n1 + 4 * R_['move'][k]] = tg; d[n1 + 4 * R_['move'][k]:n1 + 4 * R_['move'][k] + 4] = struct.pack('<I', PH)
        for k, v in sp: d[n1 + 4 * k:n1 + 4 * k + 4] = struct.pack('<I', v); moved[n1 + 4 * k] = True
        st['structs re-laid out (%d)' % ut] += 1
    for path, o in SIP.leaves(Wx, Wx.it, ia):
        pp = relayout_path(ut, path)
        if pp is None: continue
        ot = o
        if ut in RELAYOUT and len(path) == 2 and path[0] == 0:
            ot = n1 + 4 * RELAYOUT[ut]['move'][path[1] // 4]
        if ot in ita: continue
        xw = bytes(xd[o:o + 4]); cw = bytes(d[ot:ot + 4])
        new = None
        if (ut, pp) in TEXT_ID:
            new = text_id_word(xw)
            if new is None:
                new = cw; risk.append('%d %s +0x%x: text id word %s not mappable (kept %s)' % (sid, label, ot, xw.hex(), cw.hex()))
            st['text ids by the locals map'] += 1
        elif ut in UI_UTS and (ut, tag, pp) in K['_ui']:
            c, zr = K['_ui'][(ut, tag, pp)]
            if zr and xw == b'\0\0\0\0': new = bytes.fromhex(zr)
            elif c is None or c == 'id-mixed' or c in U.ID_CLASSES: new = None if c is None else cw
            else: new = word_by_rule(xw, c, I)
            if new is not None: st['words by ui_init_fix rule'] += 1
        if new is None:
            c = K['_rules'].get((ut, tag, pp))
            if c is None: c = K['_rules'].get(fallback_key(ut, tag, pp))
            if c == 'id-mixed': new = cw; st['words id-mixed (converted kept)'] += 1
            elif c is not None:
                new = word_by_rule(xw, c, I); st['words by base rule'] += 1
                hi, lo = struct.unpack('>HH', xw)
                if c == 'id16a:101' and not lo and hi not in (0, 0xffff):
                    st['text ids by base rule (locals map, ut %d path %s)' % (ut, list(pp))] += 1
                    if hi not in locmap()[0]:       # DlcIds.loc would silently keep the Xbox index
                        new = cw; risk.append('%d %s ut %d path %s +0x%x: text index %d not in the locals map (kept %s)' % (
                            sid, label, ut, list(pp), ot, hi, cw.hex()))
        if new is None:
            if xw in (b'\0\0\0\0', b'\xff\xff\xff\xff'): new = xw; st['words without a rule, 0 / -1'] += 1
            elif C.plaus(xw):
                # a float pattern (dtp_word_classes.plaus: finite, 1e-3..1e5, plausible exponent and mantissa): a 32-bit
                # float is s32 on the PC in every learned rule; listed as a heuristic in the report
                new = L_apply(xw, 's32'); st['words without a rule, float-shaped -> s32 (heuristic)'] += 1
                if new != cw: risk.append('%d %s ut %d path %s +0x%x: float-shaped Xbox %s -> %s (converted %s; heuristic)' % (
                    sid, label, ut, list(pp), ot, xw.hex(), new.hex(), cw.hex()))
            else:
                new = cw; st['words without a rule (converted kept)'] += 1
                risk.append('%d %s ut %d path %s +0x%x: Xbox %s converted %s kept (no rule)' % (sid, label, ut, list(pp), ot, xw.hex(), cw.hex()))
        if new != cw: d[ot:ot + 4] = new; st['init words changed'] += 1


def port_init2(d, ra, conv_data, pc_sec, xs, K, key, st, risk):
    """members / args / locals of a ported (pc_sec) or new (pc_sec None) script: PC words where the member is paired
    with the PC script, has the same init shape (after the struct re-layout) and the pack did not change it;
    everything else by rule from the Xbox original (xs, same offsets as the converted section)"""
    import script_init_from_pc as SIP
    sid = int(key.split(':')[1])
    rel0 = R.parse(R.write(ra, 'le'), 'le')
    wa = SC.Walk(bytes(conv_data), rel0, 'le').run()
    ita = dict(ra.internal)
    xd = xs['data']; Wx = SC.Walk(xd, R.parse(xs['reloc'], 'be'), 'be').run()
    if len(xd) != len(conv_data): sys.exit('%s: converted and Xbox section differ in size' % key)
    ma = SIP.members(wa, bytes(conv_data), 'le')
    xkey_at = {a: k for k, la in SIP.members(Wx, xd, 'be').items() for a in la}     # same entry offsets (Xbox layout)
    wb, itb = None, {}
    tw = K['_twins'].get(key, {}) if pc_sec is not None else {}
    if pc_sec is not None:
        rb = R.parse(pc_sec['reloc'], 'le'); wb = SC.Walk(pc_sec['data'], rb, 'le').run(); itb = dict(rb.internal)
    changed = {tuple(x) for x in K['changed_members'].get(key, [])}
    seen = set()
    for mk, la in ma.items():
        for j, a in enumerate(la):
            ia = ita.get(a + 16)
            if ia is None: continue
            label = '%s %d #%d' % (mk[0], mk[1], j)
            xk = xkey_at.get(a)
            if xk is None or Wx.it.get(a + 16) != ia or xk[0] != mk[0] or xk[2] != mk[2]:
                risk.append('%d %s: no Xbox member at the same offset - kept converted' % (sid, label)); st['members without Xbox twin'] += 1
                continue
            # Q55: the PC twin recorded by learn (place in the declaration order via the Xbox base), not the PC member
            # of the same converted name (a DlcIds.sym guess that named neighbour entries); same type tag required
            b = tw.get(a)
            if b is not None and struct.unpack_from('<I', pc_sec['data'], b)[0] != mk[2]:
                st['twins with another type tag (by rule)'] += 1; b = None
            if b is not None and struct.unpack_from('<H', pc_sec['data'], b + 4)[0] != mk[3]:
                st['twins whose userType differs from the converted one'] += 1
            if b is not None and struct.unpack_from('<H', pc_sec['data'], b + 14)[0] != mk[1]:
                st['twins whose PC name differs from the converted (guessed) name'] += 1
            ib = itb.get(b + 16) if b is not None else None
            if ib is not None and tuple(xk) not in changed:
                lx = [(relayout_path(mk[3], p), o) for p, o in SIP.leaves(Wx, Wx.it, ia)]
                lx = [p for p, o in lx if p is not None]
                lp = [p for p, o in SIP.leaves(wb, itb, ib) if not relayout_pc_special(mk[3], p)]
                if lx == lp:
                    st0 = collections.Counter(); shapes = []
                    SIP.copy_tree(d, wa, ita, pc_sec['data'], wb, itb, ia, ib, st0, seen, shapes)
                    if not shapes:
                        st['%s from the PC' % mk[0]] += 1
                        st['init words changed'] += st0['words changed']
                        st['structs re-laid out (PC copy)'] += st0['nodes re-laid out to the PC struct layout']
                        text_after_copy(d, xd, Wx, ia, mk[3], K, st, sid, label)
                        continue
                    risk.append('%d %s: copy found another node shape after the check (%s)' % (sid, label, shapes[:2]))
                st['%s by rule (PC init has another shape)' % mk[0]] += 1
            elif ib is not None:
                st['%s by rule (the pack changed it)' % mk[0]] += 1
            else:
                st['%s by rule (DLC-only)' % mk[0]] += 1
            rule_member(d, ita, xd, Wx, ia, mk[3], mk[2], K, st, risk, sid, label)
    # the walker labels init words up to the next known element, so an init block right before an array can swallow
    # that array's count word (structures are labelled after the members): never change a word of a structural array
    # or its count word, and never put a relocation there
    prot = protected_offsets(wa)
    restored = 0
    for o in prot:
        if o + 4 <= len(conv_data) and d[o:o + 4] != conv_data[o:o + 4]:
            d[o:o + 4] = conv_data[o:o + 4]; restored += 1
    if restored:
        st['structural words restored (init walk overran)'] += restored
        risk.append('%d: %d structural words (array counts / elements) were reached by the init walk and restored' % (sid, restored))
    old_rel = {a for a, _ in rel0.internal}
    bad = sorted(a for a in ita if a not in old_rel and a in prot)
    if bad: sys.exit('%s: a moved relocation lands on a structural word (%s) - nothing written' % (key, ['0x%x' % a for a in bad[:6]]))
    ra.internal = list(ita.items())


def path_words(d, rel, xd, xrl):
    """Symbol path words {member name, property} in the init leaves of a ported script (Q55): the high u16 of the Xbox
    word is a member name of the same Xbox script and the low u16 a non-zero base-range Symbol (a native property; as
    an integer or a float such a word would be 0x13xx0000..0x17xx0000 = 3e8 / 1e-26 - none in these scripts).
    The engine resolves such paths BY NAME (tru.exe 0x4d08e0: per path element the DataMember of that name, 0x4c8420
    over ScriptType+0x2c, else a function of that name up the class chain, 0x4d0850). -> [(offset, target entry offset,
    Xbox property Symbol)] - offsets of the converted section = the Xbox offsets"""
    import script_member_pairs as MP
    import script_init_from_pc as SIP
    xmax = ids().xs_max
    _, ex = MP.entries(xd, xrl, 'be')
    at = {}
    for q in ex['members']: at.setdefault(q['name'], q['a'])
    W, eb = MP.entries(bytes(d), R.write(rel, 'le') if not isinstance(rel, (bytes, bytearray)) else rel, 'le')
    out, seen = [], set()
    for kind in MP.KINDS:
        for q in eb[kind]:
            if q['init'] is None: continue
            for p, o in SIP.leaves(W, W.it, q['init']):
                if o in seen or o + 4 > len(xd): continue
                seen.add(o)
                xh, xl = struct.unpack_from('>HH', xd, o)
                if xh in at and 0 < xl <= xmax: out.append((o, at[xh], xl))
    return out


def twin_names(d, rel, xs, pc_sec, K, key, st, risk):
    """Q55: every member of a ported script with a PC twin takes the twin's PC name (the converter's name is a DlcIds.sym
    guess that differs from the PC name in most g_pda members); every Symbol path word {member, property} names the
    final name of the member the Xbox path names (property: the learned base map). Paths are resolved by name at run
    time (path_words), so a path copied from the PC twin (PC names) and the member names must agree."""
    import script_member_pairs as MP
    I = ids()
    sid = int(key.split(':')[1])
    tw = K['_twins'].get(key, {})
    _, eb = MP.entries(bytes(d), R.write(rel, 'le'), 'le')
    taken = set()
    for q in eb['members']:
        b = tw.get(q['a'])
        if b is None: continue
        pn = struct.unpack_from('<H', pc_sec['data'], b + 14)[0]
        taken.add(pn)
        if pn != q['name']:
            d[q['a'] + 14:q['a'] + 16] = struct.pack('<H', pn); st['member names -> PC twin name'] += 1
        else: st['member names = PC twin name already'] += 1
    xname = {q['a']: q['name'] for q in MP.entries(xs['data'], xs['reloc'], 'be')[1]['members']}
    for q in eb['members']:
        # a member without a PC twin (DLC-only) whose guessed name is a twin's PC name: DlcIds' collision rule 40000 + Xbox
        if q['a'] not in tw and q['name'] in taken:
            nn = 40000 + xname[q['a']]
            d[q['a'] + 14:q['a'] + 16] = struct.pack('<H', nn); st['member names without twin moved off a twin name (40000 + Xbox)'] += 1
    names = collections.Counter(struct.unpack_from('<H', d, q['a'] + 14)[0] for q in eb['members'])
    dup = sorted(n for n, c in names.items() if c > 1)
    if dup:
        risk.append('%d: member names used twice: %s' % (sid, dup[:8])); st['member names used twice'] += len(dup)
    for o, ta, xl in path_words(d, rel, xs['data'], xs['reloc']):
        fin = struct.unpack_from('<H', d, ta + 14)[0]
        n0, p0 = struct.unpack_from('<HH', d, o)
        # property: the PC copy's where the word already names the final member (copied from the PC twin), else the map
        want = struct.pack('<HH', fin, p0 if n0 == fin else I.sym(xl))
        if bytes(d[o:o + 4]) == want: st['path words already right'] += 1; continue
        d[o:o + 4] = want; st['path words -> final member name'] += 1; st['init words changed'] += 1


def u16_path_arrays(xd, xrl, d, rel):
    """the inline u16 arrays {u32 n, internal pointer -> the next word, u16[n]} of a ported / new script whose first
    Xbox element is a member name of the Xbox script: UI target paths (tru.exe 0x4c9410 walks records {u32 n entries,
    entries *, path {u32 n, u16 *}} of a UI member's init and resolves each path with 0x4d08e0: element 0 = the
    DataMember of that name in the screen's own ScriptType, 0x4c8420 over ScriptType+0x2c, else a function up the class
    chain, 0x4d0850). -> (arrays [(data offset, n, words, Xbox u16 values incl. padding, Xbox member entry offset of
    element 0)], counter of the arrays left out); offsets of the converted section = the Xbox offsets"""
    import script_member_pairs as MP
    from script_u16array_check import arrays
    xr = R.parse(xrl, 'be')
    xptr = set(xr.pointer_offsets())
    r = rel if isinstance(rel, R.Reloc) else R.parse(rel, 'le')
    bptr = set(r.pointer_offsets())
    xby = collections.defaultdict(list)
    for q in MP.entries(xd, xrl, 'be')[1]['members']: xby[q['name']].append(q['a'])
    out, left = [], collections.Counter()
    for co, n, t, words in sorted(arrays(xd, xr)):
        if t + 4 * words > len(d): left['beyond the section'] += 1; continue
        if any((t + 4 * k) in xptr or (t + 4 * k) in bptr for k in range(words)): left['a pointer word inside'] += 1; continue
        xv = list(struct.unpack_from('>%dH' % (2 * words), xd, t))
        if xv[0] not in xby: left['element 0 is no Xbox member name'] += 1; continue
        if len(xby[xv[0]]) != 1: left['element 0 names several Xbox members'] += 1; continue
        out.append((t, n, words, xv, xby[xv[0]][0]))
    return out, left


def u16_paths(d, rel, xs, st, risk, sid):
    """crash 2026-11-14 20:33 (new base game after the intro, tru.exe +0xc94ac, docs Befund-Absturz-gpda-NeuesSpiel-1411):
    the converter swaps the words of these u16 path arrays as s32 and keeps the Xbox values (finding 43); the stage-2b
    fix `uipath` only touches new scripts (id >= 20000) and entry lists, and rule_member keeps the converted word for
    the id classes of the UI userTypes (ui_init_fix assumes the converter mapped them) - so 3384's one-element path
    {0x14f6} stayed (0x0000, 0x14f6): element 0 = 0 names no member, 0x4d08e0 returns the address of a zeroed local
    and 0x4c9410 calls slot 2 of a NULL vtable. Rule: member element -> the FINAL name of that member (same entry
    offset, after twin_names), any other element -> the converter's PC Symbol (DlcIds.sym, as `uipath`), Xbox order,
    u16 little-endian, the padding u16 unchanged. A path whose element 0 already is the final member name stays (PC copy /
    path_words); one naming another member of this script stays and is listed as a risk."""
    import script_member_pairs as MP
    from script_u16array_check import arrays
    I = ids()
    # crash 2 (2026-11-14 21:50, OBJECTIVES screen, tru.exe 0x4ca2a0 -> 0x5a4ce0 -> call 0x02000000): the COUNT word of
    # such an array (a record {u32 a, u32 n, u16 *path, u16[n]} of a widget list, 3347 member #20 userType 361) kept the
    # Xbox byte order in 6 records (n = 2 read as 0x02000000; the converter swapped only the first record of the list,
    # the pointer target) - 0x4d08e0 then walks past the path. Every array count = the Xbox count, little-endian.
    xd = xs['data']; xr = R.parse(xs['reloc'], 'be'); xptr = set(xr.pointer_offsets()); bptr = set(rel.pointer_offsets())
    for co, n, t, words in arrays(xd, xr):
        if co in xptr or co in bptr or co + 4 > len(d): continue
        cur = struct.unpack_from('<I', d, co)[0]
        if cur == n: st['u16 array counts right'] += 1; continue
        if bytes(d[co:co + 4]) == xd[co:co + 4]:
            struct.pack_into('<I', d, co, n); st['u16 array counts: Xbox byte order -> little-endian'] += 1; st['init words changed'] += 1
        else:
            risk.append('%d +0x%x: u16 array count %d, built word %s - kept' % (sid, co, n, bytes(d[co:co + 4]).hex()))
            st['u16 array counts with another value (kept)'] += 1
    paths, left = u16_path_arrays(xs['data'], xs['reloc'], bytes(d), rel)
    for k, v in left.items(): st['u16 arrays left (%s)' % k] += v
    final = {q['a']: q['name'] for q in MP.entries(bytes(d), R.write(rel, 'le'), 'le')[1]['members']}
    built = set(final.values())
    for t, n, words, xv, xa in paths:
        pv = list(xv)
        pv[0] = final[xa]
        for k in range(1, n):
            if xv[k] not in (0, 0xffff): pv[k] = I.sym(xv[k])
        if max(pv) > 0xffff:
            risk.append('%d +0x%x: u16 path %s maps above 0xffff - kept' % (sid, t, xv[:n])); st['u16 paths not mappable (kept)'] += 1; continue
        want = struct.pack('<%dH' % len(pv), *pv)
        cur = bytes(d[t:t + 4 * words])
        c0 = struct.unpack_from('<H', cur, 0)[0]
        if cur == want: st['u16 paths already right'] += 1; continue
        if c0 == pv[0]: st['u16 paths: element 0 = final member name, other elements kept'] += 1; continue
        if c0 in built:
            risk.append('%d +0x%x: u16 path names member %d, the Xbox path names %d (final name) - kept' % (sid, t, c0, pv[0]))
            st['u16 paths naming another member (kept)'] += 1; continue
        d[t:t + 4 * words] = want
        st['u16 paths -> final member names (element 0 named no member)'] += 1; st['init words changed'] += words


def protected_offsets(W):
    """word offsets of every structural array (members, functions, code, vtable, ...) and of its count word"""
    out = set()
    for nm, t, n, sz in W.arrays:
        out.add(t - 4)
        for o in range(t, t + n * sz, 4): out.add(o)
    return out


def insert_slot31(d, r, idx93, f111):
    """the PC parent's extra vtable slot 31 (uiscreen 93 f111) into a 93 class that keeps the Xbox layout:
    tools/script_vtable_insert.py rule (new table appended: old slots 0..30, a VTE {1, -> 93 f111}, old 31..; root
    0x3c +1, 0x44 -> new table, prototype vtIndex >= 31 +1); the VTE is the one all 21 PC 93 classes of g_pda hold"""
    import script_vtable_insert as VI
    it = dict(r.internal)
    size = struct.unpack_from('<H', d, 0x3c)[0]; old = it[0x44]
    ext = {so: (si, do) for si, so, do in r.external}
    slots = []
    for k in range(size):
        a = old + 4 * k
        if a in it: slots.append(it[a])
        else: sys.exit('vtable slot %d is not an internal pointer - not handled' % k)
    while len(d) % 4: d.append(0)
    at = len(d)
    blk, table, ints, exts = VI.appended(at, slots, SLOT, struct.pack('<II', 1, PH), [(idx93, 4, f111)])
    d += blk
    r.internal = [(a, b) for a, b in r.internal if a != 0x44] + ints
    struct.pack_into('<I', d, 0x44, PH)
    r.external += exts
    struct.pack_into('<H', d, 0x3c, size + 1)
    shifted = 0
    for a, v, f in SC.elements(bytes(d), r, 'le').get('protos', []):
        vi = struct.unpack_from('<H', d, a + 6)[0]
        if vi != 0xffff and vi >= SLOT: struct.pack_into('<H', d, a + 6, vi + 1); shifted += 1
    return size, size + 1, shifted


def pc_equal_but_pointers(s, p, skeys, pkeys):
    """(crash 4, 2026-11-14 23:19, tru.exe +0x1b7476) a converted non-script section that is the PC section except for
    the TARGET OFFSETS of external relocations: same data bytes, same internal pointers and id references, the same
    external sources pointing at the same sections (by type:id) - only the destination offsets differ. Returns the
    list of (src, converted dst, PC dst, target key) that differ, [] when the section equals the PC one, None when it
    differs in anything else (then it is a real pack change and stays converted).
    Proof case: DTP 3359 (Xbox 3219, the PDA model-instance template; Xbox base = pack11 up to the dependency index of
    its one external relocation) +0x68 -> mesh 12:3373: converter +0x8158 (a zero record past the bone-set list),
    PC +0x8138 (the list {count 1, ptr}); the runtime copy of 3359 is the object the PDA's draw 0x5b7430 reads
    ([obj+0x68]+4)."""
    if s.data != p['data']: return None
    ra, rb = R.parse(s.reloc, 'le'), R.parse(p['reloc'], 'le')
    if sorted(ra.internal) != sorted(rb.internal) or sorted(ra.idref) != sorted(rb.idref) \
            or sorted(ra.idref_a) != sorted(rb.idref_a) or sorted(ra.unk3) != sorted(rb.unk3):
        return None
    ea = {so: (skeys[si], do) for si, so, do in ra.external}
    eb = {so: (pkeys[si], do) for si, so, do in rb.external}
    if set(ea) != set(eb) or any(ea[so][0] != eb[so][0] for so in ea): return None
    return [(so, ea[so][1], eb[so][1], ea[so][0]) for so in sorted(ea) if ea[so][1] != eb[so][1]]


def build(argv):
    only_safe = '--only-safe' in argv; argv = [a for a in argv if a != '--only-safe']
    know = KNOW
    if '--knowledge' in argv: k = argv.index('--knowledge'); know = argv[k + 1]; del argv[k:k + 2]
    conv, out = argv[0], argv[1]
    K = load_knowledge(know)
    I = ids()
    PCS = read_pc(); pc = {(s['type'], s['id']): s for s in PCS}; pc_keys = keys(PCS)
    PK = read_pack(); pk = {(s['type'], s['id']): s for s in PK}
    inv = {(t, I(t, x)): (t, x) for (t, x) in pk}
    gbS = read_pc_generalbank(); gb = {(s['type'], s['id']): s for s in gbS}; gb_keys = keys(gbS)
    D = DW.read(open(conv, 'rb').read(), 'le')
    log, risk, st = [], [], collections.Counter()
    L = lambda *a: (log.append(' '.join(str(x) for x in a)), print(*a))
    # inputs = the ones the knowledge was learned on
    for (t, i), s in pc.items():
        if K['pc_md5'].get(k_(t, i)) != md5(s['data'] + s['reloc']): sys.exit('PC g_pda section %d:%d differs from the knowledge' % (t, i))
    for (t, x), s in pk.items():
        if K['pack_md5'].get(k_(t, I(t, x))) != md5(s['data'] + s['reloc']): sys.exit('pack section %d:%d differs from the knowledge' % (t, x))
    rec = K['recipes']
    # ---- 1 merge (tools/drm_merge_pc.py rule + recipes)
    from_pc = []
    dkeys = keys(D.sections)
    for s in D.sections:
        key = k_(s.type, s.id); r = rec.get(key)
        # crash 4 (2026-11-14 23:19): a 'converted' section that is the PC section up to external target offsets is no
        # pack change - the converter mis-mapped the pointer target (DTP 3359 -> mesh 3373 +0x8158 instead of +0x8138);
        # the PC section is the PC's own translation of the same Xbox section -> take it (as keep_pc does for scripts)
        if r == 'converted' and s.type != 8 and (s.type, s.id) in pc:
            dp = pc_equal_but_pointers(s, pc[(s.type, s.id)], dkeys, pc_keys)
            if dp is not None:
                p = pc[(s.type, s.id)]
                s.data, s.reloc = p['data'], p['reloc']; from_pc.append((s, 'pc'))
                st['sections from the PC g_pda (converted = PC up to pointer targets)'] += 1
                for so, a_, b_, tk in dp:
                    L('pointer target: %s +0x%x -> %d:%d converted +0x%x, PC +0x%x - PC section taken' % (key, so, tk[0], tk[1], a_, b_))
                continue
        if key in K['base_same'] or r in ('keep_pc', 'resident') or (only_safe and r == 'port'):
            p = pc[(s.type, s.id)]
            s.data, s.reloc = p['data'], p['reloc']; from_pc.append((s, 'pc')); st['sections from the PC g_pda (%s)' % (r or 'base-same')] += 1
        elif r == 'resident_new':
            g = gb[(s.type, s.id)]
            s.data, s.reloc = g['data'], g['reloc']; from_pc.append((s, 'gb')); st['sections from the PC generalbank (resident_new)'] += 1
        elif r is None and (s.type, s.id) in pc:
            sys.exit('section %s: in the PC file, not base-same and no recipe' % key)
        else:
            st['sections converted (%s)' % (r or 'pack-only')] += 1
    have = {(s.type, s.id) for s in D.sections}
    for p in PCS:
        if (p['type'], p['id']) in have: continue
        n = DW.Section(p['type'], p['id'], p['data'], p['reloc'], flags=p.get('flags', 0), ver=p.get('ver', 0), spec=p.get('spec', 0xffffffff))
        D.sections.append(n); from_pc.append((n, 'pc')); st['PC-only sections appended'] += 1
    idx = {(s.type, s.id): i for i, s in enumerate(D.sections)}
    for s, src in from_pc:
        r = R.parse(s.reloc, 'le')
        if not r.external: continue
        kk = pc_keys if src == 'pc' else gb_keys
        try:
            r.external = [(idx[kk[si]], a, b) for si, a, b in r.external]
        except KeyError as e:
            sys.exit('section %d:%d refers to %s, which the merged file lacks' % (s.type, s.id, e))
        s.reloc = R.write(r, 'le')
    L('merge: %s' % dict(st))
    fk = keys(D.sections)
    # ---- 2 ported / new scripts
    targets = [k for k, r in rec.items() if r in ('port', 'new93', 'new') and not (only_safe and r == 'port')]
    final = {(s.type, s.id): (s.data, s.reloc) for s in D.sections}
    xl = {tuple(map(int, k.split(':'))) for k in targets}
    E = Ext(PK, final, xl, symmap())
    p93 = View(pc[(8, UISCREEN)]['data'], pc[(8, UISCREEN)]['reloc'], 'le')
    vte31 = dict(p93.vtable())[SLOT]
    f111 = p93.it[vte31 + 4]
    if p93.u32(vte31) != 1: sys.exit('PC 93 slot 31 VTE is not a single function')
    per = {}
    KNOWN_UT = None
    for key in sorted(targets, key=lambda q: int(q.split(':')[1])):
        t, sid = map(int, key.split(':'))
        s = D.sections[idx[(t, sid)]]; xs = pk[inv[(t, sid)]]
        sst = collections.Counter(); srisk = []
        # a) external relocation targets: decided from the Xbox original, checked by kind and name
        res = ext_check(s, xs, fk, E, lambda q: q)
        fails = [r_ for r_ in res if r_[3].startswith('FAIL')]
        moved = [r_ for r_ in res if r_[2] is not None and r_[2] != r_[5]]
        sst.update('ext ' + r_[3] for r_ in res)
        if fails:
            for r_ in fails[:10]: L('   %s +0x%x %s %s' % (key, r_[0], r_[3], r_[4]))
            sys.exit('%s: %d external relocations fail the name / kind check - nothing written' % (key, len(fails)))
        if moved:
            r0 = R.parse(s.reloc, 'le')
            want = {r_[0]: r_[2] for r_ in res}
            r0.external = [(si, so, want.get(so, do)) for si, so, do in r0.external]
            s.reloc = R.write(r0, 'le'); sst['ext targets moved'] += len(moved)
        # b) init words
        d = bytearray(s.data); r = R.parse(s.reloc, 'le')
        port_init2(d, r, s.data, pc.get((t, sid)) if rec[key] == 'port' else None, xs, K, key, sst, srisk)
        if rec[key] == 'port': twin_names(d, r, xs, pc[(t, sid)], K, key, sst, srisk)
        if rec[key] == 'port':
            if KNOWN_UT is None: KNOWN_UT = known_user_types([q for q in D.sections if q.type == 8])
            twin_types(d, r, pc[(t, sid)], K, key, sst, srisk, KNOWN_UT)
        u16_paths(d, r, xs, sst, srisk, sid)          # after twin_names: paths name the final member names
        # c) PC vtable slot 31 for the uiscreen classes
        v0 = View(s.data, s.reloc, 'le')
        if v0.super_id() == UISCREEN:
            a, b, sh = insert_slot31(d, r, idx[(8, UISCREEN)], f111)
            sst['vtable %d -> %d, prototypes vtIndex+1: %d' % (a, b, sh)] += 1
        s.data = bytes(d); s.reloc = R.write(r, 'le')
        per[key] = dict(stats=dict(sst), risks=srisk)
        L('%s (%s): %s' % (key, rec[key], dict(sst)))
        for x in srisk[:8]: L('     risk: ' + x)
        risk += srisk
    # ---- 3 write, read back, gates
    raw = D.write('le')
    E2 = DW.read(DW.cdrm_encode(raw, 'le'), 'le')
    infos = [dict(size=len(x.data)) for x in E2.sections]
    bad = sum(bool(R.check(R.parse(x.reloc, 'le'), len(x.data), infos)) for x in E2.sections)
    if bad: sys.exit('%d sections with relocations out of bounds - nothing written' % bad)
    gates = gate_sections(E2.sections, pc, PCS, pk, inv, rec, targets, K)
    for g in gates: L('gate: %s' % g)
    if any(g.startswith('FAIL') for g in gates): sys.exit('gate failed - nothing written')
    os.makedirs(os.path.join(out, 'mods'), exist_ok=True)
    fn = os.path.join(out, 'mods', NAME)
    blob = DW.cdrm_encode(raw, 'le')
    open(fn, 'wb').write(blob)
    rep = dict(tool='tools/gpda_port.py build', knowledge=K['version'], converted=os.path.relpath(conv), only_safe=only_safe,
               out=os.path.relpath(fn), md5=md5(blob), sections=len(E2.sections), per_script=per, gates=gates,
               risks=risk, text_twins_refused=TWINS, locmap=locmap()[1:], log=log)
    json.dump(rep, open(os.path.join(out, 'build_report.json'), 'w'), indent=1)
    L('written %s: %d sections, md5 %s, relocations out of bounds 0, risks %d' % (fn, len(E2.sections), md5(blob), len(risk)))


def vt_sig(v, S, own):
    """[(slot, tuple of the VTE's functions: ('fn', owner script key, function offset, name or None) / ('null',))];
    own = this script's key (VTE pointers inside the section)"""
    out = []
    for k, vte in v.vtable():
        if vte is None: out.append((k, ())); continue
        sig = []
        for where, off in v.vte_funcs(vte, S):
            if where == 'self':
                e = v.element(off); sig.append(('fn', own, off, e[2] if e and e[0] == 'func' else None))
            elif where == 'null': sig.append(('null',))
            else: sig.append(('fn', tuple(where), off, None))
        out.append((k, tuple(sig)))
    return out


def gate_sections(S, pc, PCS, pk, inv, rec, targets, K=None):
    """static gates on the written sections (list of DW.Section, PC layout); returns lines, 'FAIL ...' on a failure"""
    import script_init_from_pc as SIP
    out = []
    Sk = keys(S); idx = {k: i for i, k in enumerate(Sk)}
    tset = {tuple(map(int, k.split(':'))) for k in targets}
    vcache = {}
    def view(key):
        if key not in vcache:
            s = S[idx[key]] if key in idx else None
            vcache[key] = View(s.data, s.reloc, 'le') if s is not None and s.type == 8 and s.data else None
        return vcache[key]
    # (1) base game callers: no section outside the ported / new set points into one (relocations, derivation)
    into, derive = [], []
    for s in S:
        if s.type != 8 or not s.data or (s.type, s.id) in tset: continue
        r = R.parse(s.reloc, 'le')
        n = sum(1 for si, so, do in r.external if Sk[si] in tset)
        if n: into.append('%d:%d (%d)' % (s.type, s.id, n))
        v = view((s.type, s.id))
        if v and v.super_id() is not None and (8, v.super_id()) in tset: derive.append('%d -> %d' % (s.id, v.super_id()))
    out.append(('FAIL ' if into or derive else 'ok   ') + 'base callers: sections with relocations into ported / new scripts: %s; '
               'scripts deriving from one: %s' % (into or 'none', derive or 'none'))
    # (1b) every other section that the PC file has = the PC bytes (data; relocations up to section indices), except
    # the non-script sections the pack changed (recipe 'converted'); and every PC section is present
    same, other = 0, collections.Counter()
    for s in S:
        k = (s.type, s.id)
        if k in tset or k not in pc: continue
        if s.data == pc[k]['data']: same += 1
        else: other[rec.get(k_(*k), 'base')] += 1
    absent = [k_(*k) for k in pc if k not in set(Sk)]
    bad1 = {r: n for r, n in other.items() if r != 'converted'}
    out.append(('FAIL ' if bad1 or absent else 'ok   ') + 'PC sections: %d of the non-ported ones = PC bytes; differing: %s '
               '(only pack-changed non-script sections may differ); PC sections missing: %s' % (same, dict(other) or 'none', absent or 'none'))
    # (2) the uiscreen slots 0..31 of every ported / new 93 class = the PC's (function names per slot)
    p93 = view((8, UISCREEN)); n93 = p93.vt_size()
    ref93 = dict(vt_sig(p93, Sk, (8, UISCREEN)))
    pS = keys(PCS)
    m93 = lambda sig: tuple(e[:3] for e in sig)       # owner + offset (names of 93's own functions not compared)
    detail, warn = [], []
    for key in sorted(tset):
        v = view(key)
        if v is None or v.super_id() != UISCREEN: continue
        mine = dict(vt_sig(v, Sk, key))
        # an inherited slot (VTE -> another script) must hold the uiscreen 93 function of that slot; an own one overrides
        # ... and the PC-only slot 31 (no Xbox class can override it) must be uiscreen's own f111
        diff = [k for k in range(n93) if (k == SLOT or any(e[0] == 'fn' and e[1] != key for e in mine.get(k, ())))
                and m93(mine.get(k, ())) != m93(ref93.get(k, ()))]
        missing = [k for k in range(n93) if k not in mine or mine[k] == ()]
        pcv, names = None, []
        if key in pc:       # the PC version of this script: same inherited / own pattern below its own slots
            pv = View(pc[key]['data'], pc[key]['reloc'], 'le'); pcs_ = dict(vt_sig(pv, pS, key))
            kind = lambda sig: tuple('own' if e[0] == 'fn' and e[1] == key else (e[1], e[2]) if e[0] == 'fn' else e[0] for e in sig)
            pcv = [k for k in range(n93) if kind(mine.get(k, ())) != kind(pcs_.get(k, ()))]
            names = [k for k in range(n93) if [e[3] for e in mine.get(k, ()) if e[1] == key] !=
                     [e[3] for e in pcs_.get(k, ()) if e[1] == key]]
            # the PC version overrides a uiscreen slot the Xbox / DLC version inherits (Crystal's PC mouse handlers,
            # e.g. slot 17 = 525 "PDA menu onclicked"): the slot keeps a valid function (the uiscreen default) - a
            # behaviour difference, not a layout one; reported, not a failure
            lost = [k for k in pcv if kind(pcs_.get(k, ())) == ('own',) and m93(mine.get(k, ())) == m93(ref93.get(k, ()))]
            for k in lost:
                warn.append('%d:%d slot %d: the PC version overrides it (function %s), ours inherits the uiscreen default'
                            % (key[0], key[1], k, [e[3] for e in pcs_.get(k, ())]))
            pcv = [k for k in pcv if k not in lost]
            for k in pcv: detail.append('%d:%d slot %d ours %s / PC %s' % (key[0], key[1], k, mine.get(k), pcs_.get(k)))
        # self-consistency: every own prototype's vtIndex slot holds a VTE with that prototype's function
        protos = [(a, v.u16(a + 6), v.u16(a + 8)) for a, (kind_, k, nm) in v.el.items() if kind_ == 'proto']
        incons = []
        for a, vi, nm in protos:
            if vi == 0xffff: continue
            if vi >= v.vt_size(): incons.append('proto %d vtIndex %d >= %d' % (nm, vi, v.vt_size())); continue
            if not any(e[0] == 'fn' and e[1] == key and e[3] == nm for e in mine.get(vi, ())):
                incons.append('proto %d slot %d holds %s' % (nm, vi, mine.get(vi)))
        ok = not diff and not missing and not pcv and not incons
        out.append(('ok   ' if ok else 'FAIL ') + '%d:%d vtable %d slots; inherited slots 0..%d = PC uiscreen 93: %s; '
                   'inherited / own pattern and inherited targets = the PC version of this script: %s; prototype vtIndex '
                   'consistent: %s; own slots below %d whose function name differs from the PC version (naming only): %s' % (
                       key[0], key[1], v.vt_size(), n93 - 1, 'yes' if not diff and not missing else 'NO %s %s' % (diff[:8], missing[:8]),
                       'n/a (new)' if pcv is None else ('yes' if not pcv else 'NO %s' % pcv[:8]),
                       'yes (%d)' % len(protos) if not incons else 'NO %s' % incons[:4], n93, names or 'none'))
    out += ['info ' + x for x in detail[:20]]
    out += ['WARN ' + x for x in warn]
    # (2b) every struct-351 init in the file (PC scripts included) has the PC layout: list pointer at node word 27,
    # nothing pointing from words 22..26 / 28..30, word 22 = 0 / 1 (1 in all 13 base pairs, 0 in PC-only 3385 m5500)
    lay = collections.Counter(); badl = []
    for s in S:
        if s.type != 8 or not s.data: continue
        v = view((s.type, s.id))
        if v is None: continue
        for kk, la in SIP.members(v.W, v.d, 'le').items():
            if kk[3] not in RELAYOUT: continue
            for a in la:
                ia = v.it.get(a + 16)
                if ia is None: continue
                n1 = v.it.get(ia)
                ptr = [k for k in range(22, 31) if n1 is not None and (n1 + 4 * k) in v.it]
                w22 = v.u32(n1 + 88) if n1 is not None else None
                good = n1 is not None and ptr == [27] and w22 in (0, 1)       # PC 3385 m5500 holds 0 (PC-only field)
                lay['PC layout' if good else 'NOT PC layout'] += 1
                if good: lay['word 22 = %d' % w22] += 1
                if not good: badl.append('%d:%d %s %d: pointers at %s, word 22 = %s' % (s.type, s.id, kk[0], kk[1], ptr, w22))
    out.append(('ok   ' if not badl else 'FAIL ') + 'struct 351 (menu widget) inits in the whole file: %s %s' % (dict(lay), badl[:6]))
    # (3) code opcodes of every ported / new script = the Xbox original (the port never touches code)
    for key in sorted(tset):
        v = view(key); xs = pk[inv[key]]
        if v is None: continue
        vx = View(xs['data'], xs['reloc'], 'be')
        codes = [(t, n) for nm, t, n, sz in v.W.arrays if nm == 'code']
        xcodes = [(t, n) for nm, t, n, sz in vx.W.arrays if nm == 'code']
        same = codes == xcodes and all(struct.unpack_from('<I', v.d, t + 4 * j)[0] >> 24 ==
                                       struct.unpack_from('>I', vx.d, t + 4 * j)[0] >> 24 for t, n in codes for j in range(n))
        out.append(('ok   ' if same and not v.W.bad else 'FAIL ') + '%d:%d decodes (walker problems %d%s), %d code arrays, opcodes = Xbox: %s' % (
            key[0], key[1], len(v.W.bad), (' ' + repr(v.W.bad[:4])) if v.W.bad else '', len(codes), same))
    # (4) text ids (Q48): every text id leaf of a ported / new script (list entry 223 [0, 0], UI text 301 [0, 92]) holds
    # the word the rules derive from the Xbox word at the same offset (locals map; UI text: proven PC prompt id first)
    tst = collections.Counter(); badt = []
    for key in sorted(tset):
        v = view(key); xs = pk[inv[key]]
        if v is None: continue
        for mk, la in SIP.members(v.W, v.d, 'le').items():
            for a in la:
                ia = v.W.it.get(a + 16)
                if ia is None: continue
                for p, o in SIP.leaves(v.W, v.W.it, ia):
                    if (mk[3], tuple(p)) not in TEXT_KEYS: continue
                    want = text_rule_word(mk[3], tuple(p), bytes(xs['data'][o:o + 4]))
                    if want is None: tst['not judgeable (index not in the map / no index)'] += 1; continue
                    if bytes(v.d[o:o + 4]) == want: tst['= rule'] += 1; continue
                    badt.append('%d:%d +0x%x %s' % (key[0], key[1], o, bytes(v.d[o:o + 4]).hex()))
    out.append(('ok   ' if not badt else 'FAIL ') + 'text ids of the ported / new scripts: %s, other %d %s' % (
        dict(tst), len(badt), badt[:6]))
    # (5) Symbol paths (Q55): every path word {member name, property} of a ported script names exactly one member of
    # the script, the one the Xbox path names (the engine resolves paths by name, path_words)
    pst = collections.Counter(); badp = []
    for key in sorted(tset):
        if rec.get(k_(*key)) != 'port': continue
        v = view(key); xs = pk[inv[key]]
        if v is None: continue
        names = collections.defaultdict(list)
        for kk, la in SIP.members(v.W, v.d, 'le').items():
            if kk[0] == 'members':
                for a in la: names[kk[1]].append(a)
        for o, ta, xl in path_words(v.d, v.rel, xs['data'], xs['reloc']):
            n0 = struct.unpack_from('<H', v.d, o)[0]
            if names.get(n0) == [ta]: pst['resolve to the Xbox target'] += 1
            else: badp.append('%d:%d +0x%x name %d -> %s (target +0x%x)' % (key[0], key[1], o, n0, names.get(n0), ta))
    out.append(('ok   ' if not badp else 'FAIL ') + 'Symbol paths of the ported scripts: %s, other %d %s' % (
        dict(pst), len(badp), badp[:6]))
    # (6) u16 UI target paths (crash 2026-11-14 20:33, tru.exe +0xc94ac): element 0 of every u16 path array of a ported
    # / new script resolves like tru.exe 0x4d08e0 does it - a DataMember of that name in the script itself (0x4c8420),
    # else a prototype (function) of that name up the class chain (0x4d0850) - and it is the member the Xbox path names
    # (its final name); not found = the engine returns the address of a zeroed local and calls through a NULL vtable
    ust = collections.Counter(); badu = []
    for key in sorted(tset):
        v = view(key); xs = pk[inv[key]]
        if v is None: continue
        fin = {}; mem = collections.Counter()
        for kk, la in SIP.members(v.W, v.d, 'le').items():
            if kk[0] == 'members':
                for a in la: fin[a] = kk[1]; mem[kk[1]] += 1
        fn_names, cls, hops = set(), v, 0
        while cls is not None and hops < 16:
            fn_names |= {nm for a, (kind_, k, nm) in cls.el.items() if kind_ == 'proto'}
            sup = cls.super_id(); cls = view((8, sup)) if sup is not None else None; hops += 1
        paths, left = u16_path_arrays(xs['data'], xs['reloc'], v.d, v.rel)
        for k, c in left.items(): ust['left (%s)' % k] += c
        for t, n, words, xv, xa in paths:
            e0 = struct.unpack_from('<H', v.d, t)[0]
            if struct.unpack_from('<I', v.d, t - 8)[0] != n:     # {u32 n, u16 *path -> t, u16[n]}
                badu.append('%d:%d +0x%x n=%d: count word %s is not %d little-endian' % (key[0], key[1], t, n, v.d[t - 8:t - 4].hex(), n)); continue
            if mem[e0] == 1 and fin.get(xa) == e0: ust['element 0 = the Xbox-named member'] += 1; continue
            why = ('names no member / function: 0x4d08e0 returns a stack address' if not mem[e0] and e0 not in fn_names else
                   'resolves to a function, not the member' if not mem[e0] else
                   'several members of that name' if mem[e0] > 1 else 'names another member (final name %s)' % fin.get(xa))
            badu.append('%d:%d +0x%x n=%d Xbox %s built %s: %s' % (key[0], key[1], t, n, ' '.join('%04x' % x for x in xv[:n]),
                                                                  v.d[t:t + 4 * words].hex(), why))
    out.append(('ok   ' if not badu else 'FAIL ') + 'u16 UI target paths of the ported / new scripts: %s, other %d %s' % (
        dict(ust), len(badu), badu[:8]))
    # (7) Xbox byte order left in place (crash 2, 2026-11-14 21:50: list record counts 2 read as 0x02000000): every
    # non-pointer word of a ported / new script whose built bytes = the Xbox bytes while the Xbox word is a small
    # integer 1..0xffff (little-endian that reads as >= 0x01000000) - allowed only for an init leaf whose learned base
    # rule is 'raw' (byte fields, proven on the base pairs, e.g. userType 779 [0, 4])
    if K is None: K = load_knowledge()
    bst = collections.Counter(); badb = []
    for key in sorted(tset):
        v = view(key); xs = pk[inv[key]]
        if v is None: continue
        xd = xs['data']; xr = R.parse(xs['reloc'], 'be'); xptr = set(xr.pointer_offsets()); bptr = set(v.rel.pointer_offsets())
        cand = [w for w in range(0, min(len(xd), len(v.d)) - 3, 4) if w not in xptr and w not in bptr and
                v.d[w:w + 4] == xd[w:w + 4] and 1 <= struct.unpack_from('>I', xd, w)[0] <= 0xffff]
        if not cand: continue
        raw = set()
        for mk, la in SIP.members(v.W, v.d, 'le').items():
            for a in la:
                ia = v.W.it.get(a + 16)
                if ia is None: continue
                for p, o in SIP.leaves(v.W, v.W.it, ia):
                    if o in cand and K['_rules'].get((mk[3], mk[2], tuple(p))) == 'raw': raw.add(o)
        for w in cand:
            if w in raw: bst['raw byte fields (base rule)'] += 1
            else: badb.append('%d:%d +0x%x Xbox %s kept' % (key[0], key[1], w, xd[w:w + 4].hex()))
    out.append(('ok   ' if not badb else 'FAIL ') + 'Xbox byte order left in small integers of the ported / new scripts: %s, other %d %s' % (
        dict(bst), len(badb), badb[:8]))
    # (8) replay of tru.exe 0x4ca2a0 (widget list, [w+0x21c] count / [w+0x220] records, crash 2) and (9) of 0x4c9410
    # (uitext transition groups, crash 1) over every ported / new script: list records {a, n, u16 *path -> next word,
    # u16[n]} at stride (2n + 0xf) & ~3 with n <= 64; every path's element 0 resolves (member, else function up the chain)
    rbad, rst = [], collections.Counter()
    for key in sorted(tset):
        v = view(key)
        if v is None: continue
        d, it = v.d, v.it
        u32 = lambda o: struct.unpack_from('<I', d, o)[0]
        mem = collections.Counter()
        for kk, la in SIP.members(v.W, d, 'le').items():
            if kk[0] == 'members': mem[kk[1]] += len(la)
        fns, cls, hops = set(), v, 0
        while cls is not None and hops < 16:
            fns |= {nm for a, (kind_, k, nm) in cls.el.items() if kind_ == 'proto'}
            sup = cls.super_id(); cls = view((8, sup)) if sup is not None else None; hops += 1
        ok_ = lambda o: mem[struct.unpack_from('<H', d, o)[0]] > 0 or struct.unpack_from('<H', d, o)[0] in fns
        seen = set()
        for kk, la in SIP.members(v.W, d, 'le').items():
            for a in la:
                ia = v.W.it.get(a + 16)
                n1 = it.get(ia) if ia is not None else None
                if n1 is None or n1 in seen: continue
                seen.add(n1)
                # (8) {u32 count, records *} node whose first record has the record shape
                if n1 + 8 <= len(d):
                    cnt, rec = u32(n1), it.get(n1 + 4)
                    if 1 <= cnt <= 256 and rec is not None and rec + 12 <= len(d) and it.get(rec + 8) == rec + 12:
                        rst['widget lists'] += 1; p = rec
                        for k in range(cnt):
                            if p + 12 > len(d): rbad.append('%d:%d list +0x%x record %d beyond the section' % (key[0], key[1], n1, k)); break
                            rn = u32(p + 4); rst['list records'] += 1
                            if rn > 64: rbad.append('%d:%d list +0x%x record %d +0x%x: path count %s' % (key[0], key[1], n1, k, p, d[p + 4:p + 8].hex())); break
                            if rn and (it.get(p + 8) != p + 12 or not ok_(p + 12)):
                                rbad.append('%d:%d list +0x%x record %d +0x%x: path unresolved' % (key[0], key[1], n1, k, p))
                            p += (2 * rn + 0xf) & ~3
                # (9) uitext descriptor: 8 groups {count, records *} at node +0x7c .. +0xb8, records 0x10 bytes
                if kk[3] == 301 and n1 + 0xb8 <= len(d):
                    for co in range(0x7c, 0xb8, 8):
                        n, recs = u32(n1 + co), it.get(n1 + co + 4)
                        if not n or recs is None: continue
                        if n > 64: rbad.append('%d:%d uitext +0x%x group +0x%x count %d' % (key[0], key[1], n1, co, n)); continue
                        for k in range(n):
                            r0 = recs + 0x10 * k; rst['uitext records'] += 1
                            pn, pp = u32(r0 + 8), it.get(r0 + 12)
                            if pn > 64 or (pn and (pp is None or not ok_(pp))):
                                rbad.append('%d:%d uitext +0x%x group +0x%x record %d: path unresolved / count %d' % (key[0], key[1], n1, co, k, pn))
                            en, ep = u32(r0), it.get(r0 + 4)
                            for j in range(en if ep is not None and en <= 64 else 0):
                                an, ap = u32(ep + 8 * j), it.get(ep + 8 * j + 4)
                                rst['uitext entry paths'] += 1
                                if an > 64 or (an and (ap is None or not ok_(ap))):
                                    rbad.append('%d:%d uitext +0x%x group +0x%x record %d entry %d: path unresolved / count %d' % (
                                        key[0], key[1], n1, co, k, j, an))
    out.append(('ok   ' if not rbad else 'FAIL ') + 'replay of the UI list walks (tru.exe 0x4ca2a0 widget lists, 0x4c9410 uitext groups): %s, bad %d %s' % (
        dict(rst), len(rbad), rbad[:8]))
    # (10) external pointer targets into PC sections (crash 4, 2026-11-14 23:19, tru.exe +0x1b7476 `mov esi,[eax+20h]`
    # with eax = [[obj+0x68]+4] = 0: DTP 3359 +0x68 -> mesh 3373 +0x8158 instead of the PC's +0x8138): for every
    # non-ported section the PC file also has, each external relocation whose target section holds the PC bytes and
    # which the PC version has at the same source offset into the same section must land on the PC's offset
    pkeys = keys(PCS); xst = collections.Counter(); xbad = []
    for s in S:
        k = (s.type, s.id)
        if k in tset or k not in pc: continue
        rb = R.parse(pc[k]['reloc'], 'le'); eb = {so: (pkeys[si], do) for si, so, do in rb.external}
        for si, so, do in R.parse(s.reloc, 'le').external:
            tk = Sk[si]
            if tk not in pc or S[si].data != pc[tk]['data']: xst['into non-PC sections (not compared)'] += 1; continue
            if so not in eb or eb[so][0] != tk: xst['no PC counterpart (not compared)'] += 1; continue
            xst['compared'] += 1
            if eb[so][1] != do:
                xbad.append('%d:%d +0x%x -> %d:%d +0x%x, PC +0x%x' % (k[0], k[1], so, tk[0], tk[1], do, eb[so][1]))
    out.append(('ok   ' if not xbad else 'FAIL ') + 'external pointer targets into PC sections = the PC targets: %s, bad %d %s' % (
        dict(xst), len(xbad), xbad[:8]))
    # (11) entry userTypes (crash 5, 2026-11-15 22:35, l3_chapel PDA, tru.exe +0x1a775c): every member / arg / local
    # of a ported / new script has a userType the PC knows - a script id, or a userType the PC g_pda / generalbank
    # use with the same tag; one with a PC twin must not keep an unknown one (FAIL), a DLC-only one is listed (WARN)
    known = known_user_types([s for s in S if s.type == 8])
    tst = collections.Counter(); tbad, twarn = [], []
    import script_member_pairs as MP
    for key in sorted(tset):
        v = view(key)
        if v is None: continue
        tw = K['_twins'].get(k_(*key), {})
        for kind, lst in MP.entries(v.d, R.write(v.rel, 'le'), 'le')[1].items():
            for q in lst:
                if user_type_known(known, q['tag'], q['ut']): tst['known'] += 1; continue
                line = '%d:%d %s #%d tag %d userType %d name 0x%x' % (key[0], key[1], kind, q['k'], q['tag'], q['ut'], q['name'])
                (tbad if q['a'] in tw else twarn).append(line)
    out.append(('ok   ' if not tbad else 'FAIL ') + 'entry userTypes of the ported / new scripts known to the PC: %s, unknown with a PC twin %d %s' % (
        dict(tst), len(tbad), tbad[:8]))
    out += ['WARN userType unknown to the PC (DLC-only entry): ' + x for x in twarn]
    return out


def known_user_types(script_sections):
    """({script ids}, {tag: {userTypes}}) of the PC: script sections of the given (built) file + the PC g_pda +
    the PC generalbank; userTypes per tag as the PC g_pda / generalbank entries use them"""
    import script_member_pairs as MP
    sids = {s.id for s in script_sections}
    per = collections.defaultdict(set)
    for src in (read_pc(), read_pc_generalbank()):
        for s in src:
            if s['type'] != 8 or not s['data']: continue
            sids.add(s['id'])
            for k, lst in MP.entries(s['data'], s['reloc'], 'le')[1].items():
                for q in lst: per[q['tag']].add(q['ut'])
    return sids, per


def user_type_known(known, tag, ut):
    return ut in known[0] or ut in known[1].get(tag, ())


def twin_types(d, rel, pc_sec, K, key, st, risk, known):
    """crash 5 (2026-11-15 22:35, base game l3_chapel, PDA opened: tru.exe +0x1a775c `cmp [ecx+8],ebx`, ecx =
    [screen+0x230] = 0): 3365 member #0 (the ping map widget, name 0x149a) kept the converter's userType 5272 - no
    script, no PC type; the PC twin has 5275 = generalbank script 5275. The screen's child / focus list
    (ScriptUIScreen +0x228 / +0x230, filled by slot 2 -> 0x5a76d0 for focusable children) stayed empty, and the Xbox
    code's SetFocus (uiscreen 93 f73 -> 0x5a7730) on that widget read the null list. The converter guesses userTypes
    like names (DlcIds.sym, 40000 + Xbox for DLC-new ones); Q55 twins carry the PC one. Rule: an entry with a PC twin
    (same tag, same name) whose userType the PC does not know takes the twin's userType when the PC knows that one;
    a known userType is left alone (e.g. 3368 518 / 526 on different names)"""
    import script_member_pairs as MP
    sid = int(key.split(':')[1])
    tw = K['_twins'].get(key, {})
    for kind, lst in MP.entries(bytes(d), R.write(rel, 'le'), 'le')[1].items():
        for q in lst:
            b = tw.get(q['a'])
            if b is None or user_type_known(known, q['tag'], q['ut']): continue
            ptag, put = struct.unpack_from('<IH', pc_sec['data'], b)
            pnm = struct.unpack_from('<H', pc_sec['data'], b + 14)[0]
            if ptag != q['tag'] or pnm != q['name'] or not user_type_known(known, ptag, put):
                risk.append('%d %s #%d: userType %d unknown to the PC, twin tag %d / name 0x%x / userType %d - kept' % (
                    sid, kind, q['k'], q['ut'], ptag, pnm, put)); st['userTypes unknown, no usable twin (kept)'] += 1; continue
            struct.pack_into('<H', d, q['a'] + 4, put)
            st['userTypes unknown to the PC -> the PC twin userType'] += 1


def gate_cli(argv):
    """read-only: the static gates on any merged g_pda (e.g. finding 40's dlc2_merge, which crashed a new base game)"""
    fn = argv[0]
    K = load_knowledge()
    I = ids()
    PCS = read_pc(); pc = {(s['type'], s['id']): s for s in PCS}
    PK = read_pack(); pk = {(s['type'], s['id']): s for s in PK}
    inv = {(t, I(t, x)): (t, x) for (t, x) in pk}
    S = DW.read(open(fn, 'rb').read(), 'le').sections
    targets = [k for k, r in K['recipes'].items() if r in ('port', 'new93', 'new')]
    g = gate_sections(S, pc, PCS, pk, inv, K['recipes'], targets, K)
    for x in g: print('gate: %s' % x)
    sys.exit(1 if any(x.startswith('FAIL') for x in g) else 0)


def main(argv):
    if not argv: sys.exit(__doc__)
    cmd = argv[0]
    if cmd == 'analyze': analyze(argv[1:])
    elif cmd == 'learn': learn(argv[1:])
    elif cmd == 'build': build(argv[1:])
    elif cmd == 'gate': gate_cli(argv[1:])
    else: sys.exit('unknown command %s' % cmd)


if __name__ == '__main__':
    main(sys.argv[1:])
