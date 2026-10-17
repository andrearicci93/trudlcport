"""Iterate texture section pairs (Xbox base DRM vs PC DRM, position-parallel).
Usage as lib: pair_names() -> list of drm names; tex_pairs(name) -> list of (k, xbox_sec, pc_sec)."""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from names import load, L, crc
from pairs import pc, xl, pc_drm, xbox_drm

def pair_names():
    pcn = load(L + 'Tomb Raider Underworld (PC).txt')
    pch = {r['hash'] for r in pc.idx}
    xh = set()
    for a in xl: xh |= {r['hash'] for r in a.idx}
    out = []
    for h, n in pcn.items():
        if not n.lower().startswith('pc-w\\') or not n.lower().endswith('.drm') or h not in pch: continue
        rest = n[5:]
        if crc('xenon-w\\' + rest) in xh: out.append(rest)
    return sorted(out)

def tex_pairs(name):
    p = pc_drm(name); x = xbox_drm(name)
    if not p or not x: return []
    ps = [s for s in p[1] if s['type'] == 5]; xs = [s for s in x[1] if s['type'] == 5]
    return [(k, a, b) for k, (a, b) in enumerate(zip(xs, ps))]

if __name__ == '__main__':
    n = pair_names(); print(len(n)); print(n[:10])
