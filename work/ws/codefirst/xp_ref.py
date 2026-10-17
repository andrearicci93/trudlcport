"""Riferimento Xbox a luci accese: traduzione diretta della lib Xbox xs (translate_x) con parametri XP vs lib PC pd con parametri PP."""
import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
import numpy as np, copy
from task3_validate import *
import mp_family_rule as MF

def ref_pair(xs, pd):
    sprog, s0, s1, pprog, p0, p1 = MF.load(xs, pd)
    return sprog, pprog, material_pairs(xs, pd)

if __name__ == '__main__':
    xs, pd = int(sys.argv[1]), int(sys.argv[2])
    sprog, pprog, mats = ref_pair(xs, pd)
    for mx, mp, XP, PP in mats[:2]:
        for lab, bl in (('on', ALLB), ('off', {}), ('mix', {0: True, 3: True, 6: True})):
            print(xs, pd, 'mat', mx, mp, lab, '%.3f' % compare2(sprog, pprog, XP, PP, bools=bl))
