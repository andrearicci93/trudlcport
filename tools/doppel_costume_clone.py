"""dlc_doppel_costume_a.drm from OUR doppelganger_casual.drm (Q23, 2026-11-11, docs Befund-Kostuem-Klon-Q23-1111.md):
the last B270 kit file that came only from the kit.

What the file is (measured on the B270 kit, `kit` mode below): the upstream author's dlc_doppel_costume_a.drm is his
converted doppelganger_casual.drm with exactly one recipe change - the object section (type 11) gets the id of
`dlc_doppel_costume_a` in the merged objectlist.txt (1031 instead of 857) and the object's own id word at data +0x14
the same value. Every other section has the same type / id / order / size / relocations; header and dependency names
are equal. (Besides the recipe his two files differ in 97 DTP words that are only other byte orders of the same 4
bytes - his clone was taken from another conversion run than his shipped doppelganger_casual; our
doppelganger_casual equals his shipped one in 95 of them.) In every object DRM of our DLC 2 tree (126) and of the
B270 kit (214) the u32 at object +0x14 is the section id and the file name is the objectlist name of that id.
pack20 lists the object (`dlc_doppel_costume_a`, merged id 1031) but no Xbox package has a DRM for it
(docs/COSTUMES.md); the loading-screen script offers it when the file exists.

  build --stack TREE [TREE ...] --out DIR [--objectlist FILE] [--report JSON] [--base LARA.drm]
      source = doppelganger_casual.drm of the LAST tree of the stack that has it (stack lowest first, e.g. the Fixes
      dlc2 tree, then the Shaders layers); ids from --objectlist (default: <first tree>/tr8/pc-w/objectlist.txt).
      Writes DIR/dlc_doppel_costume_a.drm (CDRM, 256 KiB zlib-9 blocks as tools/drm_write.py) only when the gate
      passes; report (default DIR/../doppel_costume_build.json): source path / md5 / raw md5, ids, output md5s.
      Exit 1 (nothing written) when the gate fails.
  check CLONE --stack TREE [TREE ...] [--objectlist FILE] [--report JSON] [--base LARA.drm]
      the gate on a written file: re-derives the clone from the stack's source and requires the same decompressed
      bytes, plus the structural gate below. Exit 1 on any finding.
  kit OUR_CLONE KIT_CASUAL KIT_CLONE [--report JSON]          (developer, read-only; reads B270 kit files)
      the author's recipe on his pair (kit casual -> kit clone: object id + word +0x14, other words must be pure
      byte-order permutations) and our clone against his clone per section type (identical / differing / only one
      side), drift words (his pair disagrees) split by which of his two files ours equals.

Gate (structural, no kit needed): exactly one type-11 section in the source, id = objectlist id of
doppelganger_casual, data +0x14 = that id; objectlist has dlc_doppel_costume_a; clone and source have the same header,
dependency names and section list; they differ in exactly the object section's id and its word +0x14 (old id -> new
id); flags / version / spec / relocations of every section equal - plus the two control words below, nothing else.

Controls (2026-11-14, live LT-2310: "doppelganger costume in DLC 1: the left stick fires the grapple"; workspace
docs/Status-2026-11-14.md, work/doppel_1411): the clone carries the DLC 2 player's state chart (DTP 20212). Its gear
machine holds two input transitions the DLC 2 designers bound to ACTION 0 (= the left-stick axes, generalbank DTP 47
sources 10-13) - dormant in DLC 2 (the doppelganger carries no slot-3 / slot-4 gear), live in a DLC 1 unit (gear list
A with g_grapple / g_grenade_thrower):
    {150,150,0} {2100,2101,3} {900,901,0}                                   (base lara: action 46 = X, held)
    {150,152,0} {2100,2101,4} {2100,2102,4,NOT} {2000,1021,1} {1500,1501,0} {500,532,0}   (base lara: 62 = RB)
Xbox original = our conversion (2683 / 2683 transitions equal). The recipe sets the action word of exactly these two
records to the value of the transition of the same shape in the base player chart (PC lara.drm DTP 850, read from the
PC bigfile or --base FILE); doppelganger_casual itself is not touched. Records are found by content (the whole
condition list); each must occur exactly once in the clone (action 0) and once in the base chart.

Usage (from the repository root):
  ../bin/pyt -t 600 tools/doppel_costume_clone.py build --stack work/rebuild/RUN/dlc2/mods work/rebuild/RUN/shaders/mods
        work/rebuild/RUN/shaders_rule/mods --out work/rebuild/RUN/doppel/mods
  ../bin/pyt -t 600 tools/doppel_costume_clone.py check work/rebuild/RUN/doppel/mods/dlc_doppel_costume_a.drm --stack ...
  ../bin/pyt -t 900 tools/doppel_costume_clone.py kit OUR_CLONE work/b270_kit/mods/doppelganger_casual.drm
        work/b270_kit/mods/dlc_doppel_costume_a.drm
"""
import sys, os, json, struct, hashlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW
from drm import cdrm_decode

SRC_NAME, DST_NAME = 'doppelganger_casual', 'dlc_doppel_costume_a'
OBJ_TYPE, ID_WORD = 11, 0x14
import drm_reloc as R
CHART_HDR = struct.pack('<4I', 10000, 12000, 4000, 6000)    # state-chart DTP header words 3..6 (tools/chart_transitions.py)
BASE_NAME, BASE_CHART = 'lara', 850                          # PC base player chart (lara.drm DTP 850)
# condition lists (key, id, value, NOT flag) after the input record {150, id, ACTION}: the action is taken from the base
CONTROL_SHAPES = (
    ('grapple (slot 3, held)', 150, ((2100, 2101, 3, 0), (900, 901, 0, 0))),
    ('slot-4 item (pressed)', 152, ((2100, 2101, 4, 0), (2100, 2102, 4, 1), (2000, 1021, 1, 0), (1500, 1501, 0, 0), (500, 532, 0, 0))),
)


def chart_sections(D):
    """indices of the state-chart DTPs (type 7, header words 3..6 = 10000, 12000, 4000, 6000)"""
    return [i for i, s in enumerate(D.sections) if s.type == 7 and len(s.data) >= 0x1c and bytes(s.data[0xc:0x1c]) == CHART_HDR]


def transitions(s):
    """[(transition offset, condition list offset, [(key, id, value, NOT flag)])] - 0x14-byte blocks with pointers at
    +8 and +0xc (layout tools/chart_transitions.py)"""
    d = bytes(s.data); it = dict(R.parse(bytes(s.reloc), 'le').internal)
    t = sorted(set(it.values()) | {0}); out = []
    for k, a in enumerate(t):
        end = t[k + 1] if k + 1 < len(t) else len(d)
        if end - a != 0x14 or (a + 8) not in it or (a + 0xc) not in it: continue
        cnt = struct.unpack_from('<H', d, a + 4)[0]; c0 = it[a + 8]
        if cnt > 24 or c0 + 8 * cnt > len(d): continue
        out.append((a, c0, [struct.unpack_from('<3H', d, c0 + 8 * j) + (d[c0 + 8 * j + 6] & 1,) for j in range(cnt)]))
    return out


def shape_hits(s, cid, rest):
    """[(transition offset, condition list offset, action value)] of the transitions {150, cid, action} + rest"""
    return [(a, c0, c[0][2]) for a, c0, c in transitions(s)
            if len(c) == 1 + len(rest) and tuple(c[0][:2]) == (150, cid) and c[0][3] == 0 and tuple(c[1:]) == rest]


def base_chart(path=None):
    """the PC base player chart DTP 850 (lara.drm from --base FILE, else the PC bigfile ../data/pc/bigfile.000)"""
    if path:
        raw = cdrm_decode(open(path, 'rb').read(), 'le')
    else:
        from archive import Archive
        from names import crc
        pc = Archive(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'pc', 'bigfile.000'), 'le')
        hits = pc.find(crc('pc-w' + chr(92) + BASE_NAME + '.drm'))
        if not hits: raise SystemExit('PC bigfile has no %s.drm' % BASE_NAME)
        raw = cdrm_decode(pc.read(hits[0]), 'le')
    B = DW.read(raw, 'le')
    s = next((s for s in B.sections if s.type == 7 and s.id == BASE_CHART), None)
    if s is None: raise SystemExit('%s.drm has no chart DTP %d' % (BASE_NAME, BASE_CHART))
    return s


def control_plan(D, base):
    """[(section index, word offset, old u32, new u32, text)] of the control recipe on the source, or SystemExit"""
    ch = chart_sections(D)
    if len(ch) != 1: raise SystemExit('want exactly 1 state-chart DTP in the source, found %d' % len(ch))
    si = ch[0]; s = D.sections[si]; plan = []
    for what, cid, rest in CONTROL_SHAPES:
        b = shape_hits(base, cid, rest)
        if len(b) != 1: raise SystemExit('base chart: %d transitions of the shape "%s" (want 1)' % (len(b), what))
        h = shape_hits(s, cid, rest)
        if len(h) != 1 or h[0][2] != 0:
            raise SystemExit('source chart: shape "%s" found %s (want exactly 1 with action 0)' % (what, [(hex(x[0]), x[2]) for x in h]))
        o = h[0][1] + 4                       # u16 action at +4, u8 flags / u8 at +6: the word at +4 holds both
        old = struct.unpack_from('<I', s.data, o)[0]
        new = (old & 0xffff0000) | b[0][2]
        plan.append((si, o, old, new, '%s: DTP %d conditions +0x%x action 0 -> %d (base DTP %d transition +0x%x)' % (
            what, s.id, h[0][1], b[0][2], BASE_CHART, b[0][0])))
    return plan


def arg(argv, key, default=None):
    if key in argv:
        k = argv.index(key); v = argv[k + 1]; del argv[k:k + 2]; return v
    return default


def arg_list(argv, key):
    """--key A B C ... up to the next --option"""
    if key not in argv: return []
    k = argv.index(key); j = k + 1
    while j < len(argv) and not argv[j].startswith('--'): j += 1
    v = argv[k + 1:j]; del argv[k:j]; return v


def md5(b): return hashlib.md5(b).hexdigest()


def read_objectlist(path):
    """{name_lower: id} of a PC objectlist.txt (first line = count)"""
    out = {}
    for ln in open(path, encoding='latin-1').read().splitlines()[1:]:
        c = ln.split(',')
        if len(c) == 2 and c[0].strip().isdigit(): out[c[1].strip().lower()] = int(c[0])
    return out


def pick_source(stack):
    src = None
    for t in stack:
        p = os.path.join(t, SRC_NAME + '.drm')
        if os.path.isfile(p): src = p
    if not src: raise SystemExit('no %s.drm in the stack %s' % (SRC_NAME, stack))
    return src


def ids(stack, objectlist):
    ol = read_objectlist(objectlist or os.path.join(stack[0], 'tr8', 'pc-w', 'objectlist.txt'))
    if SRC_NAME not in ol or DST_NAME not in ol:
        raise SystemExit('objectlist lacks %s / %s' % (SRC_NAME, DST_NAME))
    return ol[SRC_NAME], ol[DST_NAME]


def obj_sections(D): return [i for i, s in enumerate(D.sections) if s.type == OBJ_TYPE]


def clone(raw, sid, did, base=None):
    """(clone raw bytes, findings) - the recipe on a decompressed source DRM; with base (the PC lara chart section)
    also the control recipe (two action words, see the header)"""
    D = DW.read(raw, 'le'); bad = []
    plan = control_plan(D, base) if base is not None else []
    for si, o, old, new, _ in plan:
        d = bytearray(D.sections[si].data); struct.pack_into('<I', d, o, new); D.sections[si].data = bytes(d)
    if not plan and D.write('le') != raw: bad.append('source does not round-trip through drm_write')
    if plan and DW.read(raw, 'le').write('le') != raw: bad.append('source does not round-trip through drm_write')
    ob = obj_sections(D)
    if len(ob) != 1: return None, bad + ['source has %d object sections (want 1)' % len(ob)]
    s = D.sections[ob[0]]
    if s.id != sid: bad.append('object section id %d != objectlist id %d of %s' % (s.id, sid, SRC_NAME))
    if len(s.data) < ID_WORD + 4: return None, bad + ['object section too short (%d B)' % len(s.data)]
    w = struct.unpack_from('<I', s.data, ID_WORD)[0]
    if w != sid: bad.append('object word +0x%x = %d, not the object id %d' % (ID_WORD, w, sid))
    if bad: return None, bad
    d = bytearray(s.data); struct.pack_into('<I', d, ID_WORD, did)
    s.id, s.data = did, bytes(d)
    return D.write('le'), []


def gate(src_raw, out_raw, sid, did, plan=()):
    """findings of the structural gate (empty = ok); plan = control_plan of the source: in its chart section exactly
    those words may (and must) differ, old -> new"""
    A = DW.read(src_raw, 'le'); B = DW.read(out_raw, 'le'); bad = []
    allowed = collections.defaultdict(dict)
    for si, o, old, new, _ in plan: allowed[si][o] = (old, new)
    if (A.ver, A.names, A.pad, A.u0, A.u1) != (B.ver, B.names, B.pad, B.u0, B.u1): bad.append('header / dependency names differ')
    if len(A.sections) != len(B.sections): return bad + ['section count %d != %d' % (len(A.sections), len(B.sections))]
    changed = 0
    for i, (a, b) in enumerate(zip(A.sections, B.sections)):
        if (a.type, a.flags, a.ver, a.spec, a.pad, a.reloc, len(a.data)) != (b.type, b.flags, b.ver, b.spec, b.pad, b.reloc, len(b.data)):
            bad.append('section %d (%d, %d): head / relocations / size differ' % (i, a.type, a.id)); continue
        if a.type == OBJ_TYPE:
            changed += 1
            if (a.id, b.id) != (sid, did): bad.append('object section id %d -> %d (want %d -> %d)' % (a.id, b.id, sid, did))
            diff = [o for o in range(0, len(a.data) - 3, 4) if a.data[o:o + 4] != b.data[o:o + 4]]
            want = (struct.pack('<I', sid), struct.pack('<I', did))
            if diff != [ID_WORD] or (a.data[ID_WORD:ID_WORD + 4], b.data[ID_WORD:ID_WORD + 4]) != want:
                bad.append('object section data: words %s differ (want only +0x%x %d -> %d)' % ([hex(o) for o in diff], ID_WORD, sid, did))
        elif i in allowed:
            if a.id != b.id: bad.append('section %d (%d, %d): id changed to %d' % (i, a.type, a.id, b.id))
            diff = {o: (struct.unpack_from('<I', a.data, o)[0], struct.unpack_from('<I', b.data, o)[0])
                    for o in range(0, len(a.data) - 3, 4) if a.data[o:o + 4] != b.data[o:o + 4]}
            if diff != allowed[i]:
                bad.append('chart section %d (%d, %d): words %s differ (want exactly the control words %s)' % (
                    i, a.type, a.id, {hex(o): '%08x->%08x' % v for o, v in diff.items()},
                    {hex(o): '%08x->%08x' % v for o, v in allowed[i].items()}))
        elif (a.id, a.data) != (b.id, b.data):
            bad.append('section %d (%d, %d) differs' % (i, a.type, a.id))
    if changed != 1: bad.append('%d object sections (want 1)' % changed)
    return bad


def build(argv):
    stack = arg_list(argv, '--stack'); out = arg(argv, '--out'); ol = arg(argv, '--objectlist'); rep = arg(argv, '--report')
    bp = arg(argv, '--base')
    if not stack or not out: raise SystemExit('build needs --stack TREE [TREE ...] and --out DIR')
    sid, did = ids(stack, ol); src = pick_source(stack)
    sb = open(src, 'rb').read(); raw = cdrm_decode(sb, 'le')
    base = base_chart(bp); plan = control_plan(DW.read(raw, 'le'), base)
    for p in plan: print('  control:', p[4])
    cr, bad = clone(raw, sid, did, base)
    if cr is not None: bad += gate(raw, cr, sid, did, plan)
    r = dict(source=src.replace('\\', '/'), source_md5=md5(sb), source_raw_md5=md5(raw), source_id=sid, clone_id=did,
             stack=[t.replace('\\', '/') for t in stack], base=(bp or 'PC bigfile pc-w/%s.drm' % BASE_NAME).replace('\\', '/'),
             base_chart_md5=md5(bytes(base.data)), controls=[p[4] for p in plan], findings=bad, ok=not bad)
    if not bad:
        enc = DW.cdrm_encode(cr, 'le')
        if md5(cdrm_decode(enc, 'le')) != md5(cr): bad.append('CDRM encode does not decode to the clone')
    if not bad:
        os.makedirs(out, exist_ok=True)
        q = os.path.join(out, DST_NAME + '.drm')
        open(q, 'wb').write(enc)
        back = open(q, 'rb').read()
        if md5(cdrm_decode(back, 'le')) != md5(cr): bad.append('written file does not decode to the clone')
        r.update(out=q.replace('\\', '/'), out_md5=md5(back), out_raw_md5=md5(cr), out_size=len(back))
    r['findings'], r['ok'] = bad, not bad
    rep = rep or os.path.join(os.path.dirname(os.path.abspath(out)), 'doppel_costume_build.json')
    os.makedirs(os.path.dirname(os.path.abspath(rep)), exist_ok=True)
    json.dump(r, open(rep, 'w', encoding='utf-8'), indent=1)
    print('source %s (md5 %s, raw %s), object id %d -> %d' % (src, r['source_md5'], r['source_raw_md5'], sid, did))
    for b in bad: print('  FINDING:', b)
    if bad: print('build FAILED (%d findings), report %s' % (len(bad), rep)); return 1
    print('wrote %s (%d B, md5 %s, raw md5 %s); gate ok; report %s' % (r['out'], r['out_size'], r['out_md5'], r['out_raw_md5'], rep))
    return 0


def check(argv):
    stack = arg_list(argv, '--stack'); ol = arg(argv, '--objectlist'); rep = arg(argv, '--report')
    bp = arg(argv, '--base')
    f = argv[0]
    sid, did = ids(stack, ol); src = pick_source(stack)
    sb = open(src, 'rb').read(); raw = cdrm_decode(sb, 'le')
    fb = open(f, 'rb').read(); fr = cdrm_decode(fb, 'le')
    base = base_chart(bp); plan = control_plan(DW.read(raw, 'le'), base)
    bad = gate(raw, fr, sid, did, plan)
    cr, b2 = clone(raw, sid, did, base); bad += b2
    if cr is not None and md5(cr) != md5(fr): bad.append('file is not the clone of the current source (stale or edited)')
    if os.path.getmtime(src) > os.path.getmtime(f): bad.append('source is newer than the clone')
    r = dict(file=f.replace('\\', '/'), md5=md5(fb), raw_md5=md5(fr), source=src.replace('\\', '/'), source_md5=md5(sb),
             source_raw_md5=md5(raw), source_id=sid, clone_id=did, findings=bad, ok=not bad)
    rep = rep or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(f))), 'doppel_costume_check.json')
    json.dump(r, open(rep, 'w', encoding='utf-8'), indent=1)
    for b in bad: print('  FINDING:', b)
    print('check %s: %s (source %s, id %d -> %d), report %s' % (f, 'ok' if not bad else 'FAILED (%d)' % len(bad), src, sid, did, rep))
    return 1 if bad else 0


def keyed(D, remap):
    occ = collections.Counter(); out = {}
    for s in D.sections:
        k = (s.type, remap.get((s.type, s.id), s.id)); out[k + (occ[k],)] = s; occ[k] += 1
    return out


def words(a, b): return [o for o in range(0, min(len(a), len(b)) - 3, 4) if a[o:o + 4] != b[o:o + 4]]


def kit(argv):
    rep = arg(argv, '--report')
    O, KC, KL = (DW.read(cdrm_decode(open(p, 'rb').read(), 'le'), 'le') for p in argv[:3])
    r = collections.OrderedDict()
    # 1. the author's recipe: his casual -> his clone
    ob = obj_sections(KC); ol = obj_sections(KL)
    sid, did = KC.sections[ob[0]].id, KL.sections[ol[0]].id
    same_list = [(s.type, did if (s.type, s.id) == (OBJ_TYPE, sid) else s.id) for s in KC.sections] == [(s.type, s.id) for s in KL.sections]
    rec = collections.Counter(); dsec = []; perm = 0; nonperm = []
    for a, b in zip(KC.sections, KL.sections):
        if a.reloc != b.reloc or len(a.data) != len(b.data) or (a.flags, a.ver, a.spec) != (b.flags, b.ver, b.spec): rec['head_or_reloc_or_size'] += 1
        w = words(a.data, b.data)
        if a.type == OBJ_TYPE:
            rec['object_words'] = len(w); rec['object_word_offsets'] = ','.join(hex(o) for o in w)
            continue
        if not w: continue
        dsec.append((a.type, a.id, len(w)))
        for o in w:
            if sorted(a.data[o:o + 4]) == sorted(b.data[o:o + 4]): perm += 1
            else: nonperm.append((a.type, a.id, o))
    r['recipe'] = dict(object_id=[sid, did], section_list_equal=same_list, header_equal=(KC.names, KC.pad) == (KL.names, KL.pad),
                       head_reloc_size_diffs=rec['head_or_reloc_or_size'], object_words=rec['object_words'],
                       object_word_offsets=rec['object_word_offsets'], other_sections=len(dsec),
                       other_words=sum(x[2] for x in dsec), other_words_byte_order_only=perm, other_words_not_permutation=len(nonperm),
                       other_section_ids=['%d:%d' % x[:2] for x in dsec])
    # 2. our clone vs his clone, his casual as the drift reference
    o = keyed(O, {}); kc = keyed(KC, {(OBJ_TYPE, sid): did}); kl = keyed(KL, {})
    per = collections.defaultdict(collections.Counter); drift = collections.Counter()
    for k in sorted(set(o) & set(kl)):
        a, b = o[k], kl[k]; c = kc.get(k)
        per[k[0]]['shared'] += 1
        if (a.data, a.reloc, a.flags, a.ver, a.spec) == (b.data, b.reloc, b.flags, b.ver, b.spec): per[k[0]]['identical'] += 1
        else: per[k[0]]['differ'] += 1
        # drift = words his own pair disagrees in, without the recipe word of the object section
        if c is None or len(c.data) != len(b.data) or k[0] == OBJ_TYPE: continue
        for off in words(c.data, b.data):
            x = a.data[off:off + 4] if off + 4 <= len(a.data) else b''
            drift['ours=kit_clone' if x == b.data[off:off + 4] else ('ours=kit_casual' if x == c.data[off:off + 4] else 'neither')] += 1
    for k in set(o) - set(kl): per[k[0]]['only_ours'] += 1
    for k in set(kl) - set(o): per[k[0]]['only_kit'] += 1
    r['ours_vs_kit_clone'] = {str(t): dict(per[t]) for t in sorted(per)}
    r['drift_words'] = dict(drift)
    r['sections'] = dict(ours=len(O.sections), kit_casual=len(KC.sections), kit_clone=len(KL.sections))
    print(json.dumps(r, indent=1))
    if rep: json.dump(r, open(rep, 'w', encoding='utf-8'), indent=1)
    return 0


def main(argv):
    if not argv or argv[0] not in ('build', 'check', 'kit'): print(__doc__); return 2
    return {'build': build, 'check': check, 'kit': kit}[argv[0]](argv[1:])


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
