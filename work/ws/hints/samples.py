# Stampa i testi in conflitto (indice, base, DLC1 pack10, TU/DLC2 pack11) per lingua. Sola lettura.
import pickle
T = pickle.load(open('/path/to/trudlcport/work/ws/hints/tables.pkl', 'rb'))
SPECS = [0xfffff7e1, 0xfffff7e2, 0xfffff7e8, 0xfffff7e4, 0xfffff7f0, 0xffffffe0]
LN = {0xfffff7e1: 'L0', 0xfffff7e2: 'L1', 0xfffff7e8: 'L2', 0xfffff7e4: 'L3', 0xfffff7f0: 'L4', 0xffffffe0: 'L5'}
def g(src, s, i):
    st = T[src][s]['strings']
    return st[i].decode('utf-8', 'replace') if i < len(st) else '<none>'
for i in [1288, 1289, 1291, 1292, 1294, 1296, 1316, 1317, 1373, 1374, 1375, 135, 410, 454, 460]:
    print('--- idx', i)
    for s in [0xfffff7e1, 0xfffff7f0]:
        print('  %s base=%r | dlc1=%r | tu/dlc2=%r' % (LN[s], g('xbase', s, i)[:60], g('pack10', s, i)[:60], g('tu', s, i)[:60]))
