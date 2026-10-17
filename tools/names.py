def crc(s):
    h = 0xffffffff
    for c in s.lower():
        h ^= ord(c) << 24
        for _ in range(8):
            h = ((h << 1) ^ 0x4c11db7) & 0xffffffff if h & 0x80000000 else (h << 1) & 0xffffffff
    return ~h & 0xffffffff
def load(path):
    d = {}
    for l in open(path, encoding='utf8', errors='ignore'):
        l = l.rstrip('\r\n')
        if l: d[crc(l)] = l
    return d
L = '/path/to/trudlcport/ref/yura-release/FileLists/'
