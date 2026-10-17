"""Coppie base Xbox/PC dei DRM cinstream e accesso ai DTP (con reloc). Cache in work/ws/cine/pairs.pkl"""
import sys, os, pickle
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm
from archive import Archive
from names import crc
C = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pairs.pkl')
def secs(d, e): return drm.sections_with_data(drm.cdrm_decode(d, e), e)[1]
def load():
    if os.path.exists(C): return pickle.load(open(C, 'rb'))
    pcb = Archive(os.path.join(T, '..', 'pc', 'bigfile.000'), 'le')
    XB = [Archive('/path/to/TombRaiderUnderworld_Patched/layer%d.000' % i, 'be') for i in (1, 2)]
    names = [l.strip() for l in open(os.path.join(T, '..', 'ref', 'yura-release', 'FileLists', 'Tomb Raider Underworld (PC).txt'), errors='ignore')
             if 'cinstream' in l.lower() and l.strip().lower().endswith('.drm')]
    out = []
    for n in names:
        pr = pcb.find(crc(n)); xn = n.replace('pc-w', 'xenon-w')
        xd = next((A.read(A.find(crc(xn))[0]) for A in XB if A.find(crc(xn))), None)
        if not pr or xd is None: continue
        X = secs(xd, 'be'); P = secs(pcb.read(pr[0]), 'le')
        out.append((n.split('\\')[-1], X, P))
    pickle.dump(out, open(C, 'wb')); return out
