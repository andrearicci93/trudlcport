"""Validate dlc_generic.model_fix on all base Xbox/PC model-DTP pairs (Xbox word0 0x04c20453, same size + internal relocs):
applying the override on top of the REAL PC bytes must change nothing (every overridden field equals PC).  Then report how
many words it changes in converted DLC files.  usage: model_validate.py [converted.drm ...]"""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generic_store, dlc_generic as DG, drm_reloc as R, drm_write as DW
st = generic_store.load(); ids = DG.DlcIds(st, None)
c = collections.Counter()
for (t, x), xb in st['xb_store'].items():
    if t != 7 or xb['data'][:4] != DG.MODEL_MAGIC: continue
    pc = st['pc_store'].get((7, ids.base[7].get(x)))
    if pc is None or len(pc['data']) != len(xb['data']): c['skip_size'] += 1; continue
    rel = R.parse(xb['reloc'], 'be')
    if dict(R.parse(pc['reloc'], 'le').internal) != dict(rel.internal): c['skip_layout'] += 1; continue
    buf = bytearray(pc['data']); n = DG.model_fix(xb['data'], rel, buf)
    c['pairs'] += 1; c['pairs_changed' if n else 'pairs_exact'] += 1; c['words_changed'] += n
print('base pairs:', dict(c))
if len(sys.argv) > 1:
    from convert_dlc import raw_dlc
    from drm import cdrm_decode, sections_with_data
    for f in sys.argv[1:]:
        _, xs = sections_with_data(cdrm_decode(raw_dlc(os.path.basename(f))[0], 'be'), 'be')
        D = DW.read(open(f, 'rb').read(), 'le')
        for s, o in zip(xs, D.sections):
            if s['type'] == 7 and s['data'][:4] == DG.MODEL_MAGIC and len(o.data) == len(s['data']):
                buf = bytearray(o.data); n = DG.model_fix(s['data'], R.parse(s['reloc'], 'be'), buf)
                if n: print(os.path.basename(f), 'DTP', s['id'], 'words fixed', n)
