# Verifiche richieste dall'advisor (sola lettura). Nessun file esistente modificato.
import sys, pickle, struct, collections, hashlib
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm
G = '/path/to/trudlcport/work/'
d = pickle.load(open(G + 'generic/dlc_drms.pkl', 'rb'))
def sec(pack, name, sid):
    for k, v in d.items():
        if k[0] == pack and k[1].endswith(name):
            for s in v[1]:
                if s['type'] == 8 and s['id'] == sid: return s['data']
# 1) sezione 74 identica tra DRM e tra pack?
h = collections.Counter()
for k, v in d.items():
    if k[0] in ('ack10.000', 'ack11.000'):
        for s in v[1]:
            if s['type'] == 8 and s['id'] == 74: h[hashlib.md5(s['data']).hexdigest()] += 1
print('sez74 DRM: distinct payloads', len(h), 'copies', sum(h.values()), 'top', h.most_common(3))
# 2a) record beebbeeb in sezione 3527 di dlc_caverns, DRM convertiti installati
for p in ['mods_next', 'mods_current']:
    raw = open(G + p + '/dlc_caverns.drm', 'rb').read()
    _, secs = drm.sections_with_data(drm.cdrm_decode(raw, 'le'), 'le')
    s = [x for x in secs if x['type'] == 8 and x['id'] == 3527][0]['data']
    o = s.find(bytes.fromhex('beebbeeb'))
    print(p, 'beebbeeb at', o, 'next 8 bytes', s[o:o+8].hex(' ') if o >= 0 else None)
    if o >= 0: print('   u16 at +4 LE/BE:', struct.unpack_from('<H', s, o+4)[0], struct.unpack_from('>H', s, o+4)[0])
# 2b) pattern beebbeeb + u16 + 0000 over pack10/pack11 (excl. sez 74)
for pack in ['ack10.000', 'ack11.000']:
    cnt = collections.Counter(); files = collections.Counter()
    for k, v in d.items():
        if k[0] != pack: continue
        for s in v[1]:
            if s['type'] != 8 or s['id'] == 74: continue
            b = s['data']; i = 0
            while True:
                i = b.find(bytes.fromhex('beebbeeb'), i)
                if i < 0: break
                if i + 8 <= len(b) and b[i+6:i+8] == b'\0\0':
                    sid = struct.unpack_from('>H', b, i+4)[0]
                    cnt[sid] += 1
                i += 4
    print(pack, 'beebbeeb records', sum(cnt.values()), 'distinct', len(cnt))
    print('  1202 count', cnt[1202], '| 1284..1406 used:', sorted(x for x in cnt if 1284 <= x <= 1406))
    print('  top', cnt.most_common(8))
pickle.dump(None, open('/dev/null', 'wb'))
