import sys, io, contextlib
import numpy as np
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
import texlib
texlib.set_baseline('B87_materiali19')
TC = texlib.TC
tid = int(sys.argv[1]) if len(sys.argv) > 1 else 6610
d, src = texlib.pc_sec(tid); pc = TC.pc_image(d, 0, 0).astype(float)
xd, xs = texlib.xb_sec(tid); h, res, _ = TC.xbox_levels(xd)
name = h['fmtname']; xb = TC.blocks_to_image(res[0][0], {'DXT1':'DXT1','DXT4_5':'DXT5','DXT2_3':'DXT3'}[name], h['w'], h['h']).astype(float)
print('PC', pc.shape, 'Xbox', xb.shape, name)
for lab, im in (('PC', pc), ('Xbox', xb)):
    a = im[..., 3] / 255.
    L = im[..., :3].mean(-1) / 255.
    print(lab, 'RGB medio', np.round(im[..., :3].reshape(-1, 3).mean(0) / 255, 3), 'alfa medio', round(a.mean(), 3), 'frac alfa>.5', round((a > .5).mean(), 3),
          'lum p50/p90/p99/max', np.round(np.percentile(L, [50, 90, 99, 100]), 3))
a = pc[..., 3] / 255.; m = a > .5
print('PC: RGB dove alfa>.5', np.round(pc[m][:, :3].mean(0) / 255, 3), ' Xbox RGB nelle stesse posizioni', np.round(xb[m][:, :3].mean(0) / 255, 3))
Lx = xb[..., :3].mean(-1) / 255.
print('corr(alfa PC, lum Xbox)', round(float(np.corrcoef(a.ravel(), Lx.ravel())[0, 1]), 3))
print('PC dove alfa<.5: RGB', np.round(pc[~m][:, :3].mean(0) / 255, 3))
