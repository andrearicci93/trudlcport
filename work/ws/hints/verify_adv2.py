# Record beebbeeb (sez 3527 dlc_caverns, offset 1124) nel DRM convertito e pattern su pack10/pack11 (sola lettura).
import sys, pickle, struct, collections
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm
G = '/path/to/trudlcport/work/'
d = pickle.load(open(G + 'generic/dlc_drms.pkl', 'rb'))
xk = [k for k in d if k[0] == 'ack10.000' and k[1].endswith('dlc_caverns.drm')][0]
xs = [s for s in d[xk][1] if s['type'] == 8 and s['id'] == 3527][0]['data']
print('xbox 3527 len', len(xs), 'beebbeeb offsets', [i for i in range(len(xs)-3) if xs[i:i+4] == bytes.fromhex('beebbeeb')][:5])
print('xbox ctx 1124:', xs[1124:1132].hex(' '))
for p in ['mods_next', 'mods_current']:
    raw = open(G + p + '/dlc_caverns.drm', 'rb').read()
    _, secs = drm.sections_with_data(drm.cdrm_decode(raw, 'le'), 'le')
    ids = sorted({s['id'] for s in secs if s['type'] == 8})
    print(p, 'has sec 3527?', 3527 in ids, ' n script secs', len(ids))
    # locate same section by its position/size in the converted file
    cand = [s for s in secs if s['type'] == 8 and s['size'] == len(xs)]
    print('  script secs with xbox size', len(xs), ':', [(c['id'], c['size']) for c in cand][:3])
    for c in cand[:1]:
        o = c['data'].find(bytes.fromhex('beebbeeb'))
        print('  beebbeeb at', o, 'ctx', c['data'][o:o+8].hex(' ') if o >= 0 else None)
        if o >= 0: print('  u16 BE at +4 =', struct.unpack_from('>H', c['data'], o+4)[0], ' LE =', struct.unpack_from('<H', c['data'], o+4)[0])
