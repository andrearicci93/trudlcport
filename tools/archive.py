import os, zlib
from bigfile import read_index
ALIGN = 0x7FF00000
class Archive:
    def __init__(self, path, endian, align=ALIGN):
        self.path, self.align = path, align
        self.idx = read_index(path, endian)
        self.base, ext = os.path.splitext(path)
    def read(self, r):
        pos = r['offset'] << 11
        part, off = divmod(pos, self.align) if self.path.endswith('.000') else (0, pos)
        p = f'{self.base}.{part:03d}' if self.path.endswith('.000') else self.path
        with open(p, 'rb') as f:
            f.seek(off)
            if r['clen'] > 0: return zlib.decompress(f.read(r['clen']))
            return f.read(r['size'])
    def find(self, h, spec=None):
        return [r for r in self.idx if r['hash'] == h and (spec is None or r['spec'] == spec)]
