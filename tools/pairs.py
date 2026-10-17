import sys, json
sys.path.insert(0, '/path/to/trudlcport/tools')
from archive import Archive
from drm import cdrm_decode, sections_with_data
from names import load, L, crc
BASE = '/path/to/'
pcn = load(L + 'Tomb Raider Underworld (PC).txt'); xn = load(L + 'Tomb Raider Underworld (Xenon).txt')
pc = Archive(BASE + 'tru-port/pc/bigfile.000', 'le')
xl = [Archive(BASE + 'TombRaiderUnderworld_Patched/layer1.000', 'be'), Archive(BASE + 'TombRaiderUnderworld_Patched/layer2.000', 'be')]
def pc_drm(name):  # name like 'alister.drm'
    r = pc.find(crc('pc-w\\' + name))
    return sections_with_data(cdrm_decode(pc.read(r[0]), 'le'), 'le') if r else None
def xbox_drm(name):
    for a in xl:
        r = a.find(crc('xenon-w\\' + name))
        if r: return sections_with_data(cdrm_decode(a.read(r[0]), 'be'), 'be')
    return None
