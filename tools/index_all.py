import sys, json, struct
sys.path.insert(0, '/path/to/trudlcport/tools')
from archive import Archive
from drm import cdrm_decode, parse_drm
from names import load, L, crc
from multiprocessing import Pool
def work(args):
    path, endian, align, i = args
    a = Archive(path, endian, align)
    r = a.idx[i]
    try:
        raw = a.read(r)
        if raw[:4] not in (b'CDRM', b'MRDC') and not (len(raw) > 24 and struct.unpack('>i' if endian == 'be' else '<i', raw[:4])[0] == 19):
            return (path, i, r['hash'], r['spec'], len(raw), None)
        raw = cdrm_decode(raw, endian)
        h, secs, end = parse_drm(raw, endian)
        return (path, i, r['hash'], r['spec'], len(raw), [(s['type'], s['id'], s['size'], s['nreloc'], s['spec'], s['ver'], s['flags']) for s in secs], end == len(raw))
    except Exception as e:
        return (path, i, r['hash'], r['spec'], 0, 'ERR ' + repr(e)[:80])
if __name__ == '__main__':
    out, endian = sys.argv[1], sys.argv[2]
    jobs = []
    for spec in sys.argv[3:]:
        path, align = spec.split('@'); align = int(align, 16)
        a = Archive(path, endian, align)
        jobs += [(path, endian, align, i) for i in range(len(a.idx))]
    with Pool(8) as p: res = p.map(work, jobs, chunksize=8)
    json.dump(res, open(out, 'w'))
    print(out, len(res), 'files; errors', sum(1 for r in res if isinstance(r[5], str)))
