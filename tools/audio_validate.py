#!/usr/bin/env python3
"""Validate wave_convert against base-game Xbox<->PC pairs. Output: work/audio/validate.jsonl"""
import sys, json, struct, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pairs import *
from audio_parse import *
from wave_convert import *
found = json.load(open('/path/to/trudlcport/work/audio/wavepairs.json'))
lo, hi = int(sys.argv[1]), int(sys.argv[2])
out = open(f'/path/to/trudlcport/work/audio/validate_{lo}.jsonl', 'w')
def corr(a, b):
    m = min(len(a), len(b))
    if m < 64: return None
    a = a[:m].astype(np.float64); b = b[:m].astype(np.float64)
    if a.std() == 0 or b.std() == 0: return 1.0 if (a.std() == b.std()) else 0.0
    return float(np.corrcoef(a, b)[0, 1])
for n, ca, cb in found[lo:hi]:
    if ca != cb: continue
    p = [s for s in pc_drm(n)[1] if s['type'] == 6]; x = [s for s in xbox_drm(n)[1] if s['type'] == 6]
    for k, (sp, sx) in enumerate(zip(p, x)):
        r = dict(drm=n, k=k)
        try:
            q0 = parse_pc(sp['data']); o, info = xbox_wave_to_pc(sx['data'], q0['name']); q = parse_pc(o)
            ref = ima_decode_fsb(q0['data']); got = ima_decode_fsb(q['data'])
            # reference for "what is the real PC audio vs the XMA decode"
            xa, sr, ch, e = xma_decode(sx['data'][16:])
            r.update(pc_size=sp['size'], out_size=len(o), size_eq=sp['size'] == len(o), pc_len=q0['length'], out_len=q['length'],
                     pc_rate=q0['deffreq'], out_rate=q['deffreq'], pc_data=len(q0['data']), out_data=len(q['data']),
                     hdr_eq=(o[:48] == sp['data'][:48]) , pre_eq=o[:16] == sp['data'][:16],
                     corr_pc_vs_xma=corr(ref, xa[:, 0]), corr_pc_vs_conv=corr(ref, got), corr_xma_vs_conv=corr(xa[:, 0], got))
            if len(ref) == len(got):
                err = ref.astype(np.float64) - got; r['snr_db'] = float(10 * np.log10((ref.astype(np.float64) ** 2).mean() / max((err ** 2).mean(), 1e-9) + 1e-12))
            # structure of the converted section vs PC one
            r['struct_fields_eq'] = all(q[f] == q0[f] for f in ['n', 'shsz', 'ver', 'mode', 'smode', 'vol', 'pan', 'pri', 'nch', 'mind', 'maxd'])
        except Exception as ex:
            r['error'] = repr(ex)[:200]
        out.write(json.dumps(r) + '\n'); out.flush()
