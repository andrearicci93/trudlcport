import sys, os, pickle, struct
sys.path.insert(0, os.path.expanduser('~/Downloads/tru-port/tools'))
import generic_type0 as G0, generic_learn as G
from drm import cdrm_decode, sections_with_data
from archive import Archive
from names import crc
PACK10 = os.path.expanduser('~/Downloads/Xenia-SteveRepack/Content/534307EC/00000002/9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000')
arc = Archive(PACK10, 'be')
raw = arc.read([r for r in arc.find(crc('xenon-w\\dlc_dungeon.drm')) if r['spec'] == 0xffffffff][0])
h, xs = sections_with_data(cdrm_decode(raw, 'be'), 'be')
labs = G0.labels(xs, 'be')
T0v = pickle.load(open(os.path.expanduser('~/Downloads/tru-port/work/generic/type0_table.pkl'), 'rb'))
T0 = G0.Table0(); T0.v.update(T0v)
SL = G0.table0()
def show(k): print('   ', repr(k)[:150], dict(T0.v.get(k, {})), '-> best', T0.best(k))
for k, offs in ((47, [0x114, 0x594, 0x5d4, 0x714]), (51, [0x114]), (47, [0x54, 0x94, 0x154, 0x194])):
    kmap = {w: (key, ck) for w, key, ck in G.word_keys(len(xs[k]['data']), labs[k])}
    for w in offs:
        key, ck = kmap[w]; xw = xs[k]['data'][w:w+4]
        c, src = G0.lookup(SL, None, key, ck, xw)
        print('sec', k, hex(w), xw.hex(), 'shape', G0.shape(xw), '->', c, src)
        sh = G0.shape(xw)
        for kk in (('S', key, sh), ('SC',) + ck + (sh,), key, G.mid(key), ('C',) + ck, ('SG', sh), ('R', key[0])): show(kk)
