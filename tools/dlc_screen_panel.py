"""DLC mission screen: the title update's dark translucent panel behind preview image, text and list (Q5, 2026-11-17).

Finding: the Xbox title update added ONE data member to the mission screen script (Xbox TU script 134 = PC script 104):
member 0 at instance offset 4, name Symbol 1195, type `uibitmap` (Xbox script 89, userType 318), with an init block
and a start-function-info entry (so the engine constructs it), referenced by no code word. Its init: no texture
(+0x5c = 0), colour +0x4c / +0x54 = 0x94050505 (ARGB: alpha 0x94 = 58 %, RGB 5 / 5 / 5), position x / y / z
+0x18 / +0x1c / +0x20 = 1.0 / 0.25 / 25.0, scale +0x34 / +0x38 = 28.0 / 14.0 (screen units: 16:9 = 35.56 x 20, centre
origin, y down; 28 x 14 units = 78.8 % x 70 % of the screen, centre +1.0 / +0.25 -> 13.4-92.2 % x 16-86 %, the panel in
the Xenia reference). The PC script is the retail one (no such member) -> no panel on PC, from the pause menu and from
the main menu alike. (The other TU member, type uiexperienceadjustmentmenu at the end, is rule tu134_tailoring of
tools/generalbank_pc_build.py.)

Modes (from the repository root; nothing is written except by `build`):
  ../bin/pyt -t 600 tools/dlc_screen_panel.py scan SRC [SRC ...]
        every `uibitmap` member with an init block in every script of SRC (a PC DRM file or a script_func_list
        source: xt / xl / pp / pb / pc:NAME / xbox:NAME): member index / count, instance offset, name Symbol,
        position, scale, colours, texture word; `PANEL` = no texture and colour alpha < 0xff. Draw-order evidence:
        where such panels sit in the member list and their z against the texts of the same script.
  ../bin/pyt -t 600 tools/dlc_screen_panel.py build IN_DRM OUT_DRM [--tu TITLEUPDATE000]
        IN_DRM (PC generalbank.drm, CDRM or raw) -> OUT_DRM with the panel member added to PC script 104:
        new member at the next free instance offset (no old offset moves), its entry FIRST in the member array and
        its start-function-info entry LAST (the TU's order: panel = m0, constructed last), member entry = a copy of
        the PC's own uibitmap member entry of script 104 (type tag / userType / type id) with the PC name Symbol of
        TU 1195 (= PC 1292, the same panel name in PC scripts 33 / 119 / 268 / 269), the TU init block (240 bytes)
        byte-swapped as u32 (proof: the TU's other uibitmap inits of 134 equal the PC's of 104 word for word), its
        16 property path pointers retargeted to the target every PC uibitmap init of script 104 uses, instance size
        + 12. Members / sfi arrays are re-homed (appended copies, the old arrays stay orphaned with their
        relocations) as rule tu134_tailoring does. Refuses when the member exists already.
  ../bin/pyt -t 600 tools/dlc_screen_panel.py order SRC [SRC ...]
        read-only: how many member arrays are in ascending offset order and sfi lists in descending order
  ../bin/pyt -t 600 tools/dlc_screen_panel.py verify BEFORE AFTER [--tu TITLEUPDATE000]
        AFTER = BEFORE + exactly the panel (only script 104 differs; old words unchanged except root 0x1c / 0x2c /
        0x30; old relocations kept; new member / sfi / init decoded from AFTER against the TU) -> exit 1 on a problem
"""
import sys, os, struct, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
import drm_write as DW
import script_func_list as FL

PC_ID, TU_ID = 104, 134
TU_ARCH = '../data/TombRaiderUnderworld_Patched/TitleUpdate.000'
TU_NAME = 'xenon-w\\generalbank.drm'
TU_PANEL = dict(off=4, name=1195, init_len=0xf0)
# init data offsets (relative to the data the init's first pointer names)
F_POS, F_SCALE, F_COL, F_COL2, F_COL3, F_TEX = 0x18, 0x34, 0x4c, 0x54, 0x58, 0x5c


def md5(b):
    return hashlib.md5(bytes(b)).hexdigest()


def cstr(d, a):
    z = d.find(b'\0', a)
    return bytes(d[a:z]).decode('latin-1') if z >= 0 else ''


class Sc:
    """one script section: data, relocations, arrays (script_conv walker), members, sfi"""
    def __init__(self, d, rl, e):
        import script_conv as SC
        self.d, self.e, self.E = bytes(d), e, ('>' if e == 'be' else '<')
        self.rel = R.parse(rl, e)
        self.it = dict(self.rel.internal)
        self.ids = self.rel.id_offsets()
        self.W = SC.Walk(self.d, self.rel, e).run()
        self.arr = {n: (t, c, sz) for n, t, c, sz in self.W.arrays}

    def w(self, a): return struct.unpack_from(self.E + 'I', self.d, a)[0]
    def h(self, a): return struct.unpack_from(self.E + 'H', self.d, a)[0]
    def f(self, a): return struct.unpack_from(self.E + 'f', self.d, a)[0]

    def members(self):
        if 'members' not in self.arr: return []
        t, n, sz = self.arr['members']
        return [dict(i=j, n=n, a=t + sz * j, tag=self.w(t + sz * j), ut=self.h(t + sz * j + 4), ty=self.w(t + sz * j + 8),
                     tyref=self.ids.get(t + sz * j + 8), off=self.h(t + sz * j + 12), name=self.h(t + sz * j + 14),
                     init=self.it.get(t + sz * j + 16)) for j in range(n)]

    def sfi(self):
        if 'sfi' not in self.arr: return []
        t, n, sz = self.arr['sfi']
        return [dict(a=t + sz * j, ty=self.w(t + sz * j), tyref=self.ids.get(t + sz * j), off=self.w(t + sz * j + 4))
                for j in range(n)]

    def init_data(self, m):
        """data offset of a member's init block (the init's first word points at it)"""
        return self.it.get(m['init']) if m['init'] is not None else None


def natives(secs, e):
    out = {}
    for ty, sid, d, rl in secs:
        if ty != 8 or not d: continue
        it = dict(R.parse(rl, e).internal)
        if 0x10 in it: out[sid] = cstr(d, it[0x10])
    return out


def bitmap_rows(S, sid, nat):
    rows = []
    for m in S.members():
        if m['tyref'] != 8 or nat.get(m['ty']) != 'uibitmap' or m['init'] is None: continue
        b = S.init_data(m)
        if b is None or b + F_TEX + 4 > len(S.d): continue
        col = S.w(b + F_COL)
        tex = S.w(b + F_TEX)
        rows.append(dict(sid=sid, m=m, b=b, pos=tuple(S.f(b + F_POS + 4 * k) for k in range(3)),
                         scale=(S.f(b + F_SCALE), S.f(b + F_SCALE + 4)), col=col, col2=S.w(b + F_COL2),
                         col3=S.w(b + F_COL3), tex=tex, texref=S.ids.get(b + F_TEX),
                         panel=(tex == 0 and S.ids.get(b + F_TEX) is None and (col >> 24) not in (0, 0xff))))
    return rows


def text_z(S, nat):
    """z (+0x20) of every uitext member init of the script"""
    out = []
    for m in S.members():
        if m['tyref'] == 8 and nat.get(m['ty']) == 'uitext' and m['init'] is not None:
            b = S.init_data(m)
            if b is not None and b + 0x24 <= len(S.d): out.append(round(S.f(b + 0x20), 3))
    return out


def scan(srcs):
    for src in srcs:
        secs, e = FL.sections(src)
        nat = natives(secs, e)
        npanel = 0; nbm = 0
        print('== %s (%s, %d sections)' % (src, e, len(secs)))
        for ty, sid, d, rl in secs:
            if ty != 8 or not d: continue
            try:
                S = Sc(d, rl, e)
            except Exception as x:          # a section the walker cannot read
                print('  8:%d walker error %s' % (sid, x)); continue
            rows = bitmap_rows(S, sid, nat)
            nbm += len(rows)
            panels = [r for r in rows if r['panel']]
            if not panels: continue
            npanel += len(panels)
            tz = text_z(S, nat)
            print('  8:%d %s: %d members, %d uibitmap inits, texts z %s' % (
                sid, nat.get(sid) or '-', len(S.members()), len(rows), sorted(set(tz))[:8]))
            for r in panels:
                m = r['m']
                print('    PANEL m%d/%d off %d name %d pos (%.3g, %.3g, %.3g) scale (%.3g, %.3g) col %08x / %08x / %08x tex %d'
                      % (m['i'], m['n'], m['off'], m['name'], r['pos'][0], r['pos'][1], r['pos'][2], r['scale'][0],
                         r['scale'][1], r['col'], r['col2'], r['col3'], r['tex']))
        print('  total: %d uibitmap inits, %d panels' % (nbm, npanel))
    return 0


def order(srcs):
    """member arrays in ascending instance offset? sfi lists in descending offset? (every script of SRC)"""
    for src in srcs:
        secs, e = FL.sections(src)
        n = up = sdown = ns = 0; odd_m, odd_s = [], []
        for ty, sid, d, rl in secs:
            if ty != 8 or not d: continue
            try:
                S = Sc(d, rl, e)
            except Exception:
                continue
            offs = [m['off'] for m in S.members()]
            if len(offs) > 1:
                n += 1
                if offs == sorted(offs): up += 1
                else: odd_m.append(sid)
            so = [x['off'] for x in S.sfi()]
            if len(so) > 1:
                ns += 1
                if so == sorted(so, reverse=True): sdown += 1
                else: odd_s.append(sid)
        print('%s: member arrays ascending %d / %d (other: %s); sfi descending %d / %d (other: %s)'
              % (src, up, n, odd_m[:12], sdown, ns, odd_s[:12]))
    return 0


# ---------------------------------------------------------------- build
def read_tu(path):
    """raw (big-endian) generalbank of the player's TitleUpdate.000"""
    import dtp_word_classes as C
    from drm import cdrm_decode, sections_with_data
    secs = C.find([path], 'be', TU_NAME)
    if secs is None: raise SystemExit('generalbank not found in ' + path)
    return [(s['type'], s['id'], s['data'], s['reloc']) for s in secs]


def tu_panel(tusecs):
    """the TU panel member: (member entry, init data bytes (BE), init relocation list, sfi entry)"""
    nat = natives(tusecs, 'be')
    sec = next(q for q in tusecs if q[0] == 8 and q[1] == TU_ID and q[2])
    T = Sc(sec[2], sec[3], 'be')
    m = [x for x in T.members() if x['off'] == TU_PANEL['off']]
    if len(m) != 1: raise SystemExit('TU script 134: no member at offset 4')
    m = m[0]
    if (m['i'], m['name'], m['tyref'], nat.get(m['ty'])) != (0, TU_PANEL['name'], 8, 'uibitmap'):
        raise SystemExit('TU script 134 m0: %s' % ((m['i'], m['name'], m['tyref'], nat.get(m['ty'])),))
    sf = [x for x in T.sfi() if x['off'] == TU_PANEL['off']]
    if len(sf) != 1 or sf[0]['tyref'] != 8 or sf[0]['ty'] != m['ty']: raise SystemExit('TU script 134: sfi of offset 4')
    lo = m['init']; hi = lo + TU_PANEL['init_len']
    # code never names the member (op0c / op0f / op10 with operand 4)
    import script_conv as SC
    ex = dict(SC.Walk.EXTRA); ex[0x02] = 1
    t, n, sz = T.arr['funcs']
    uses = 0
    for j in range(n):
        ct = T.it.get(t + sz * j + 0x18)
        if ct is None: continue
        o, end = ct, ct + 4 * T.w(ct - 4)
        while o < end:
            x = T.w(o)
            if x >> 24 in (0x0c, 0x0f, 0x10) and x & 0xffffff == TU_PANEL['off']: uses += 1
            o += 4 * (1 + ex.get(x >> 24, 0))
    rels = dict(internal=[(a, b) for a, b in T.rel.internal if lo <= a < hi],
                external=[x for x in T.rel.external if lo <= x[1] < hi],
                idref=[x for x in T.rel.idref if lo <= x[1] < hi], idref_a=[x for x in T.rel.idref_a if lo <= x[1] < hi])
    return T, m, sf[0], lo, hi, rels, uses


def pc_template(P):
    """script 104's own uibitmap members: entry template + the init pointer layout (slot -> shared target)"""
    return [x for x in P.members() if x['tyref'] == 8 and x['init'] is not None]


def plan(raw_in, tusecs):
    D = DW.read(raw_in, 'le')
    ks = [j for j, s in enumerate(D.sections) if s.type == 8 and s.id == PC_ID]
    if len(ks) != 1: raise SystemExit('PC: %d script sections 104' % len(ks))
    k = ks[0]
    psecs = [(s.type, s.id, s.data, s.reloc) for s in D.sections]
    pnat = natives(psecs, 'le')
    P = Sc(D.sections[k].data, D.sections[k].reloc, 'le')
    T, tm, tsf, lo, hi, trel, uses = tu_panel(tusecs)
    tnat = natives(tusecs, 'be')
    log = ['TU script 134 m0: off %d name %d type 8:%d (%s), init +0x%x..+0x%x, sfi +0x%x, code uses %d'
           % (tm['off'], tm['name'], tm['ty'], tnat.get(tm['ty']), lo, hi, tsf['a'], uses)]
    if uses: raise SystemExit('TU code names the panel member (%d uses) - not a plain data member' % uses)
    if trel['external'] or trel['idref'] or trel['idref_a']:
        raise SystemExit('TU panel init has external / id relocations: %s' % trel)
    tb = T.it[tm['init']]
    if tb != tm['init'] + 4: raise SystemExit('TU init pointer +0x%x -> +0x%x (expected +4)' % (tm['init'], tb))
    # the TU init's pointer slots: the first word (-> data) and the property path slots (-> one shared target)
    tslots = sorted(a - lo for a, b in trel['internal'])
    ttargets = {b for a, b in trel['internal'] if a != tm['init']}
    if len(ttargets) != 1: raise SystemExit('TU init property slots point at %d targets' % len(ttargets))
    # PC: uibitmap type id and its members of script 104 (template)
    pbm = [m for m in P.members() if m['tyref'] == 8 and pnat.get(m['ty']) == 'uibitmap' and m['init'] is not None]
    if not pbm: raise SystemExit('PC script 104 has no uibitmap member')
    pty = pbm[0]['ty']
    # every PC uibitmap init of 104: same 240-byte shape, the same pointer slots, one shared property target
    ptargets = set()
    for m in pbm:
        plo = m['init']
        slots = sorted(a - plo for a, b in P.rel.internal if plo <= a < plo + TU_PANEL['init_len'])
        if slots != tslots: raise SystemExit('PC m%d init pointer slots %s differ from the TU panel %s' % (m['i'], slots, tslots))
        ptargets |= {b for a, b in P.rel.internal if plo + 4 <= a < plo + TU_PANEL['init_len']}
    if len(ptargets) != 1: raise SystemExit('PC uibitmap inits use %d property targets' % len(ptargets))
    # word form proof: the TU's other uibitmap inits of 134 (same order, offsets + 12) equal the PC's of 104 as u32
    # values in every non-pointer word -> the panel init needs only the u32 byte swap
    tbm = [m for m in T.members() if m['tyref'] == 8 and tnat.get(m['ty']) == 'uibitmap' and m['init'] is not None
           and m['off'] != TU_PANEL['off']]
    if len(tbm) != len(pbm): raise SystemExit('uibitmap inits: TU %d / PC %d' % (len(tbm), len(pbm)))
    nw = 0
    for x, y in zip(tbm, pbm):
        for q in range(0, TU_PANEL['init_len'], 4):
            if (x['init'] + q in T.it) != (y['init'] + q in P.it): raise SystemExit('pointer slot +0x%x differs' % q)
            if x['init'] + q in T.it: continue
            if T.w(x['init'] + q) != P.w(y['init'] + q):
                raise SystemExit('TU m%d / PC m%d init +0x%x: %08x / %08x' % (x['i'], y['i'], q, T.w(x['init'] + q), P.w(y['init'] + q)))
            nw += 1
    log.append('word form: %d uibitmap init pairs TU 134 / PC 104, %d non-pointer words equal as u32' % (len(pbm), nw))
    ptarget = ptargets.pop()
    # the TU shared target and the PC one hold the same shape (count 1 + pointer)
    tt = ttargets.pop()
    if (T.w(tt), P.w(ptarget)) != (1, 1): raise SystemExit('property path targets: TU %08x / PC %08x' % (T.w(tt), P.w(ptarget)))
    # the PC name Symbol of TU 1195: every other TU uibitmap member of that name, paired with the PC uibitmap members
    # whose init words are the same u32 values (pointer slots left out) -> their PC names must be one Symbol
    psecs_le = [(ty, sid, dd, rl) for ty, sid, dd, rl in psecs if ty == 8 and dd]

    def sig(S, m):
        return tuple(S.w(m['init'] + q) for q in range(0, TU_PANEL['init_len'], 4) if m['init'] + q not in S.it) \
            if m['init'] is not None and m['init'] + TU_PANEL['init_len'] <= len(S.d) else None
    tsig = {}
    for ty, sid, dd, rl in tusecs:
        if ty != 8 or not dd or sid == TU_ID: continue
        try: S = Sc(dd, rl, 'be')
        except Exception: continue
        for m in S.members():
            if m['tyref'] == 8 and tnat.get(m['ty']) == 'uibitmap' and m['name'] == tm['name']:
                g = sig(S, m)
                if g: tsig.setdefault(g, []).append('xt 8:%d m%d' % (sid, m['i']))
    names, where = set(), []
    for ty, sid, dd, rl in psecs_le:
        try: S = Sc(dd, rl, 'le')
        except Exception: continue
        for m in S.members():
            if m['tyref'] == 8 and pnat.get(m['ty']) == 'uibitmap':
                g = sig(S, m)
                if g in tsig: names.add(m['name']); where.append('pc 8:%d m%d = %s' % (sid, m['i'], tsig[g][0]))
    if len(names) != 1: raise SystemExit('PC name of TU %d: %s (%s)' % (tm['name'], sorted(names), where))
    pname = names.pop()
    if any(m['name'] == pname for m in P.members()): raise SystemExit('PC script 104 already has a member named %d - applied?' % pname)
    log.append('PC: uibitmap = 8:%d (%d members of 104 with init, shared property target +0x%x; TU +0x%x); name TU %d -> PC %d '
               '(%d TU panels of that name, %d PC twins with the same init words: %s)'
               % (pty, len(pbm), ptarget, tt, tm['name'], pname, sum(len(v) for v in tsig.values()), len(where), '; '.join(where)))
    # ---- build
    d = bytearray(P.d); r = R.parse(D.sections[k].reloc, 'le')
    old_len = len(d)
    size, align = P.h(0x1c), P.h(0x1e)
    new_off = (size + align - 1) // align * align if align else size
    msize = 12
    new_size = new_off + msize

    def pad():
        while len(d) % 4: d.append(0)

    def dup(lo_, hi_, delta):
        r.internal += [(a + delta, t) for a, t in list(r.internal) if lo_ <= a < hi_]
        r.external += [(si, a + delta, dd) for si, a, dd in list(r.external) if lo_ <= a < hi_]
        r.idref += [(t, a + delta) for t, a in list(r.idref) if lo_ <= a < hi_]
        r.idref_a += [(t, a + delta) for t, a in list(r.idref_a) if lo_ <= a < hi_]

    def retarget(a, t):
        n0 = len(r.internal)
        r.internal = [(x, y) for x, y in r.internal if x != a]
        if len(r.internal) != n0 - 1: raise SystemExit('no internal pointer at +0x%x' % a)
        r.internal.append((a, t))

    pad()
    # init block: TU words byte-swapped (all words are u32 / f32 / ARGB: checked below), pointers retargeted
    ia = len(d)
    for o in range(lo, hi, 4):
        d += struct.pack('<I', T.w(o))
    for a, b in trel['internal']:
        rel_o = a - lo
        struct.pack_into('<I', d, ia + rel_o, 0xbeebbeeb)
        r.internal.append((ia + rel_o, (ia + 4) if a == tm['init'] else ptarget))
    # members: count + the new entry FIRST (as the TU's m0) + old entries (entry = PC template's tag / userType / type,
    # new offset + name). The instance offset is the next free one (no old offset moves); the array order and the sfi
    # order below are the TU's: panel = first member, constructed last - so the result matches the Xbox whether the
    # engine draws by member order, by construction order or by z (scan: member arrays out of offset order occur in
    # 6 PC scripts, sfi lists out of order in 70)
    mt, mn, msz = P.arr['members']
    tpl = pbm[0]
    st, sn, ssz = P.arr['sfi']
    if (8, tpl['a'] + 8) not in r.idref or (8, st) not in r.idref:
        raise SystemExit('PC member / sfi type ids are not in the idref list')
    pad(); d += struct.pack('<I', mn + 1); nmt = len(d)
    na = len(d)
    d += P.d[tpl['a']:tpl['a'] + 12] + struct.pack('<HH', new_off, pname) + struct.pack('<I', 0xbeebbeeb)
    r.idref.append((8, na + 8)); r.internal.append((na + 16, ia))
    d += P.d[mt:mt + msz * mn]; dup(mt, mt + msz * mn, nmt + msz - mt)
    retarget(0x2c, nmt)
    # sfi: count + old entries + the new entry LAST (TU: the offset-4 panel is the last entry)
    d += struct.pack('<I', sn + 1); nst = len(d)
    d += P.d[st:st + ssz * sn]; dup(st, st + ssz * sn, nst - st)
    d += struct.pack('<II', pty, new_off); r.idref.append((8, nst + ssz * sn))
    retarget(0x30, nst)
    struct.pack_into('<H', d, 0x1c, new_size)
    sec = D.sections[k]
    sec.data = bytes(d)
    nrel = R.Reloc(sorted(r.internal), list(r.external), r.idref_a, r.unk3, r.idref)
    bad = R.check(nrel, len(d))
    if bad: raise SystemExit('relocation check: %s' % bad[:5])
    sec.reloc = R.write(nrel, 'le')
    log.append('script 104: %d -> %d B; instance size %d -> %d, new member m0 of %d off %d name %d (+0x%x), sfi %d -> %d '
               '(new last, +0x%x), init +0x%x (%d B)' % (old_len, len(d), size, new_size, mn + 1, new_off, pname, na, sn,
                                                       sn + 1, nst, ia, hi - lo))
    info = dict(k=k, old_len=old_len, new_off=new_off, new_size=new_size, pname=pname, pty=pty, ia=ia, na=na, nmt=nmt,
                nst=nst, ptarget=ptarget, tu=(lo, hi, tm['init']))
    return D.write('le'), info, log, T


def load_raw(path):
    b = open(path, 'rb').read()
    return (DW.cdrm_decode(b, 'le'), True) if b[:4] == b'CDRM' else (b, False)


def verify(raw_b, raw_a, tusecs):
    """-> problems"""
    probs = []
    B, A = DW.read(raw_b, 'le'), DW.read(raw_a, 'le')
    if [(s.type, s.id) for s in B.sections] != [(s.type, s.id) for s in A.sections]: return ['section list differs']
    diff = [(s.type, s.id) for s, t in zip(B.sections, A.sections) if (s.data, s.reloc) != (t.data, t.reloc)]
    if diff != [(8, PC_ID)]: probs.append('sections differing %s (expected only 8:104)' % diff)
    plan_raw, info, _, T = plan(raw_b, tusecs)
    Q = DW.read(plan_raw, 'le')
    k = info['k']
    if (Q.sections[k].data, Q.sections[k].reloc) != (A.sections[k].data, A.sections[k].reloc):
        probs.append('script 104 is not the plan from BEFORE')
    b = Sc(B.sections[k].data, B.sections[k].reloc, 'le'); a = Sc(A.sections[k].data, A.sections[k].reloc, 'le')
    for o in range(0, info['old_len'] - info['old_len'] % 4, 4):
        if b.w(o) != a.w(o) and o != 0x1c: probs.append('+0x%x %08x -> %08x unexplained' % (o, b.w(o), a.w(o)))
    bi, ai = dict(b.rel.internal), dict(a.rel.internal)
    for o, t in bi.items():
        if o in (0x2c, 0x30): continue
        if ai.get(o) != t: probs.append('internal pointer +0x%x changed' % o)
    for nm in ('external', 'idref', 'idref_a', 'unk3'):
        if getattr(a.rel, nm)[:len(getattr(b.rel, nm))] != getattr(b.rel, nm) and nm in ('idref', 'idref_a', 'unk3'):
            probs.append('relocations %s: old entries changed' % nm)
    if a.rel.external != b.rel.external: probs.append('external relocations changed')
    ent = lambda m: (m['tag'], m['ut'], m['ty'], m['tyref'], m['off'], m['name'], m['init'])
    mb, ma = b.members(), a.members()
    if [ent(m) for m in mb] != [ent(m) for m in ma[1:]] or len(ma) != len(mb) + 1: probs.append('old member entries changed')
    nm_ = ma[0]
    if (nm_['off'], nm_['ty'], nm_['tyref'], nm_['name']) != (info['new_off'], info['pty'], 8, info['pname']):
        probs.append('new member %s' % (ent(nm_),))
    if nm_['off'] < max(m['off'] for m in mb) + 1: probs.append('new member offset inside the old instance')
    if a.h(0x1c) != info['new_size']: probs.append('instance size')
    sb, sa = b.sfi(), a.sfi()
    if [(x['ty'], x['tyref'], x['off']) for x in sa] != [(x['ty'], x['tyref'], x['off']) for x in sb] + [(info['pty'], 8, info['new_off'])]:
        probs.append('sfi list')
    # init decoded from AFTER against the TU words
    lo, hi, tinit = info['tu']
    ib = a.init_data(nm_)
    if ib != nm_['init'] + 4: probs.append('new init pointer')
    for q in range(0, hi - lo, 4):
        o = nm_['init'] + q
        if o in a.it:
            want = (nm_['init'] + 4) if q == 0 else info['ptarget']
            if a.it[o] != want: probs.append('init +0x%x pointer -> +0x%x' % (q, a.it[o]))
        elif a.w(o) != T.w(lo + q): probs.append('init +0x%x %08x, TU %08x' % (q, a.w(o), T.w(lo + q)))
    # the walker reads the new section without problems
    if a.W.bad: probs.append('walker: %s' % a.W.bad[:3])
    return probs, info


def main(argv):
    if not argv: sys.exit(__doc__)
    if argv[0] == 'scan': return scan(argv[1:])
    if argv[0] == 'order': return order(argv[1:])
    tu = TU_ARCH
    if '--tu' in argv: j = argv.index('--tu'); tu = argv[j + 1]; del argv[j:j + 2]
    if argv[0] == 'build' and len(argv) == 3:
        raw, was_cdrm = load_raw(argv[1])
        tusecs = read_tu(tu)
        out, info, log, _ = plan(raw, tusecs)
        probs, _ = verify(raw, out, tusecs)
        if probs: print('\n'.join(log)); raise SystemExit('verify refused: %s' % '; '.join(probs[:10]))
        b = DW.cdrm_encode(out, 'le') if was_cdrm else out
        if was_cdrm and DW.cdrm_decode(b, 'le') != out: raise SystemExit('CDRM round trip')
        os.makedirs(os.path.dirname(os.path.abspath(argv[2])), exist_ok=True)
        open(argv[2], 'wb').write(b)
        log += ['input  %s md5 %s' % (argv[1], md5(open(argv[1], 'rb').read())),
                'output %s md5 %s (%d B, %s)' % (argv[2], md5(b), len(b), 'CDRM' if was_cdrm else 'raw'),
                'verify ok (only script 104; old words unchanged except root 0x1c / members / sfi pointers; init = TU words)']
        print('\n'.join(log))
        return 0
    if argv[0] == 'verify' and len(argv) == 3:
        rb, _ = load_raw(argv[1]); ra, _ = load_raw(argv[2])
        probs, info = verify(rb, ra, read_tu(tu))
        print('verify %s: %s' % ('ok' if not probs else 'FAILED', '; '.join(probs[:20]) or 'only script 104, the planned panel'))
        return 1 if probs else 0
    sys.exit(__doc__)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
