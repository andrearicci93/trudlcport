"""Apply the validated 2026-10-09 fixes IN PLACE onto already-converted DLC DRMs (everything else byte-identical, so an
in-game A/B test isolates the fixes; a full re-conversion would also pull in later table retrains):
  analog  (dlc_generic.analog_convert: DLC-new DTP cloned from a base DTP -> PC analog data+reloc)
  model   (dlc_generic.model_fix: model-DTP typed fields, HInfo counts)
  rebase  (dlc_generic.script_rebase: Scripts deriving from PC-grown base classes: size/member/sfi/code offsets)
  cine_nowait (dlc_generic.cine_nowait: dlc_level1_start script 20068 goes to its cine state without the TU loading-screen message)
  animfx  (animfx.fix: anim event-list DTPs: {u16 h, s16 frame} record headers + terminator as u16 pairs, payload / sound
           struct fields per base-pair classes; crash fix13 0x593659, NOTES 2026-10-10)
  aidata  (aidata_fix.fix: 0x390-byte enemy AI records of level DTPs: DTP ids w/o relocs + s32 fields; crash 0x54df84)
usage: dlc_patch.py [--only=fix1,fix2] OUTDIR SRCDIR[,SRCDIR..] name.drm [streamgroups/x.drm ..]   (first SRCDIR containing
       the file wins; --only restricts the fixes, e.g. --only=animfx for a clean A/B on top of the installed files)"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlc_generic as DG, generic_store, drm_write as DW, drm_reloc as R, animfx, aidata_fix
from generic_store import norm_hash
from drm import cdrm_decode, sections_with_data
from convert_dlc import raw_dlc
st = generic_store.load(); ids = DG.DlcIds(st, None)
argv = [a for a in sys.argv[1:] if not a.startswith('--only=')]
ONLY = next((set(a[7:].split(',')) for a in sys.argv[1:] if a.startswith('--only=')), None)
def on(f): return ONLY is None or f in ONLY
out_dir, srcs = argv[0], argv[1].split(',')
for name in argv[2:]:
    path = next((os.path.join(d, name) for d in srcs if os.path.exists(os.path.join(d, name))), None)
    if path is None: print(name, 'not found in', srcs); continue
    raw_old = open(path, 'rb').read()
    raw, _ = raw_dlc(name.replace('/', '\\'))
    if raw is None: raw, _ = raw_dlc(os.path.basename(name))
    _, xs = sections_with_data(cdrm_decode(raw, 'be'), 'be')
    D = DW.read(raw_old, 'le'); ids.local = {}
    pool = collections.defaultdict(list)
    for o in D.sections: pool[o.type, o.id].append(o)
    hit = collections.Counter()
    for s in xs:
        t, x = s['type'], s['id']
        if t not in (7, 8): continue
        lst = pool.get((t, ids(t, x)))
        if not lst: continue
        o = lst.pop(0)
        base = x in ids.base.get(t, {}) and norm_hash(s, xs, 'be') in st['xb_hash'].get((t, x), ())
        if t == 7 and x not in ids.base.get(7, {}) and on('analog'):
            r = DG.analog_convert(s, xs, ids, st)
            if r is not None and (r[0], r[1]) != (o.data, o.reloc):
                o.data, o.reloc = r[0], r[1]; hit['analog'] += 1; continue
        if t == 7 and s['data'][:4] == DG.MODEL_MAGIC and len(o.data) == len(s['data']) and on('model'):
            b = bytearray(o.data)
            if DG.model_fix(s['data'], R.parse(s['reloc'], 'be'), b): o.data = bytes(b); hit['model'] += 1
        if t == 7 and len(o.data) == len(s['data']) and on('animfx'):
            b = bytearray(o.data)
            n = animfx.fix(s['data'], R.parse(s['reloc'], 'be'), b, ids)
            if n: o.data = bytes(b); hit['animfx'] += 1; hit['animfx_words'] += n
        if t == 7 and len(o.data) == len(s['data']) and on('aidata'):
            b = bytearray(o.data)
            n = aidata_fix.fix(s['data'], R.parse(s['reloc'], 'be'), b, ids)
            if n: o.data = bytes(b); hit['aidata'] += 1; hit['aidata_words'] += n
        if t == 8 and not base and len(s['data']) >= 0x54 and len(o.data) == len(s['data']) \
                and o.data[0x1c:0x1e] == s['data'][0x1c:0x1e][::-1] and on('rebase'):    # still Xbox layout (idempotent)
            sh = DG.script_layout_shift(int.from_bytes(s['data'][0x18:0x1c], 'big'), xs, st, ids)
            if sh:
                b = bytearray(o.data)
                if DG.script_rebase(s['data'], R.parse(s['reloc'], 'be'), b, sh): o.data = bytes(b); hit['rebase'] += 1
            elif sh is None: hit['rebase_unresolved'] += 1
        if t == 8 and x in DG.CINE_NOWAIT and on('cine_nowait'):
            b = bytearray(o.data)
            at = DG.CINE_NOWAIT[x]['at']
            if b[at:at + 8] != bytes.fromhex('010000040000007d') and DG.cine_nowait(x, s['data'], b):
                o.data = bytes(b); hit['cine_nowait'] += 1
    for k, o in enumerate(D.sections):          # skip the DLC1 intro cinematic (dlc_generic.CINE_SKIP)
        if o.type == 8:
            xid = next((q['id'] for q in xs if q['type'] == 8 and ids(8, q['id']) == o.id), None)
            if xid in DG.CINE_SKIP and on('cine_skip'):
                def k_of(tt, xx):
                    nid = ids(tt, xx)
                    return next((j for j, q in enumerate(D.sections) if (q.type, q.id) == (tt, nid)), None)
                rl = DG.cine_skip_reloc(xid, xs, o.reloc, k_of)
                if rl is not None: o.reloc = rl; hit['cine_skip'] += 1
    data = D.write('le')
    if raw_old[:4] == b'CDRM': data = DW.cdrm_encode(data, 'le')
    op = os.path.join(out_dir, name); os.makedirs(os.path.dirname(op), exist_ok=True)
    open(op, 'wb').write(data)
    print(name, 'from', path, dict(hit))
