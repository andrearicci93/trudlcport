# Analisi sola lettura dei conflitti di indice fra base Xbox, DLC1 (pack10), DLC2/TU (pack11), costumi (pack1/2).
import sys, pickle, collections, json
sys.path.insert(0, '/path/to/trudlcport/tools')
import locals as L
T = pickle.load(open('/path/to/trudlcport/work/ws/hints/tables.pkl', 'rb'))
SPECS = L.SPECS
LN = {0xfffff7e1: 'L0', 0xfffff7e2: 'L1', 0xfffff7e8: 'L2', 0xfffff7e4: 'L3', 0xfffff7f0: 'L4', 0xffffffe0: 'L5'}
def S(src, spec): return T[src][spec]['strings']
print('== identita fra sorgenti (byte) ==')
for a, b in [('tu', 'pack11'), ('pack1', 'pack2'), ('xbase', 'xbase2')]:
    print(a, b, 'identici su tutte le lingue:', all(T[a][s]['raw'] == T[b][s]['raw'] for s in SPECS))
print('== lunghezze ==')
for src in ['xbase', 'tu', 'pack10', 'pack11', 'pack1', 'pack2', 'pcpatch']:
    print(src, sorted(set(len(S(src, s)) for s in SPECS)))
print('== round-trip write() vs raw (primo byte diverso) ==')
for src in ['xbase', 'pack10']:
    for s in SPECS[:1]:
        e = 'be'; raw = T[src][s]['raw']; w = L.write(T[src][s]['lang'], S(src, s), e)
        k = next((i for i in range(min(len(raw), len(w))) if raw[i] != w[i]), None)
        print(src, LN[s], 'len raw', len(raw), 'len write', len(w), 'first diff at', k, 'raw', raw[k-4:k+8] if k else '', 'write', w[k-4:k+8] if k else '')
