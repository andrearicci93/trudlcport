import struct, sys
def read_index(path, endian):
    e = '>' if endian == 'be' else '<'
    with open(path, 'rb') as f:
        n, = struct.unpack(e+'I', f.read(4))
        hashes = struct.unpack(e+f'{n}I', f.read(4*n))
        recs = [struct.unpack(e+'IIIi', f.read(16)) for _ in range(n)]
    return [dict(hash=h, size=r[0], offset=r[1], spec=r[2], clen=r[3]) for h, r in zip(hashes, recs)]
if __name__ == '__main__':
    path, endian = sys.argv[1], sys.argv[2]
    idx = read_index(path, endian)
    print(path, len(idx), 'records')
    for r in idx[:12]: print({k: hex(v) if k != 'clen' else v for k, v in r.items()})
    print('offset max', hex(max(r['offset'] for r in idx)), 'size max', max(r['size'] for r in idx))
