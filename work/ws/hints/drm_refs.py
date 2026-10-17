# Conta candidati record Script {u32 ptr, u16 BE strId, u16 0} in DRM DLC (dlc_drms.pkl, sola lettura). Euristica, da validare.
import pickle, collections, struct
d = pickle.load(open('/path/to/trudlcport/work/generic/dlc_drms.pkl', 'rb'))
out = {}
for pack in ('ack10.000', 'ack11.000'):
    hist = collections.Counter(); nsec = 0; secs_with = collections.Counter()
    for k, v in d.items():
        if k[0] != pack: continue
        for sec in v[1]:
            if sec.get('type') != 8: continue
            data = sec.get('data'); n = len(data); nsec += 1
            seen = set()
            for o in range(0, n - 8, 4):
                ptr = struct.unpack_from('>I', data, o)[0]
                if ptr >= n: continue
                sid, z = struct.unpack_from('>HH', data, o + 4)
                if z == 0 and 1 <= sid < 5000:
                    hist[sid] += 1; seen.add(sid)
            for s in seen: secs_with[s] += 1
    out[pack] = (hist, secs_with)
    print(pack, 'script sections', nsec, 'total cand', sum(hist.values()))
    for lo, hi, name in [(1202, 1208, 'ar_rw_shard band 1202-1208'), (1284, 1287, '1284-1287'), (1288, 1288, '1288'), (1289, 1290, '1289-90'), (1291, 1297, '1291-1297'), (1298, 1315, '1298-1315'), (1316, 1375, '1316-1375'), (1376, 1406, '1376-1406')]:
        print('   %-26s records %6d  distinct sids %3d' % (name, sum(hist[s] for s in range(lo, hi + 1)), sum(1 for s in range(lo, hi + 1) if hist[s])))
    print('   top sids:', hist.most_common(12))
import pickle as P
P.dump({k: (dict(v[0]), dict(v[1])) for k, v in out.items()}, open('/path/to/trudlcport/work/ws/hints/drm_script_strid_hist.pkl', 'wb'))
