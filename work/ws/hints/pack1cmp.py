# Indici Xbox 1284..1406: presenza e uguaglianza fra pack10 (DLC1 disc), pack1==pack2 (costumi), TU/pack11 (DLC2). Sola lettura.
import pickle, collections
T = pickle.load(open('/path/to/trudlcport/work/ws/hints/tables.pkl', 'rb'))
SPECS = [0xfffff7e1, 0xfffff7e2, 0xfffff7e8, 0xfffff7e4, 0xfffff7f0, 0xffffffe0]
def has(src, s, i):
    return i < len(T[src][s]['offs']) and T[src][s]['offs'][i] != 0
def txt(src, s, i):
    return T[src][s]['strings'][i].decode('utf8', 'replace') if has(src, s, i) else None
c = collections.Counter(); examples = collections.defaultdict(list)
for s in SPECS:
    for i in range(1284, 1407):
        p10, p1, tu = txt('pack10', s, i), txt('pack1', s, i), txt('tu', s, i)
        key = ('p10' if p10 is not None else '-') + '|p1' + ('=p10' if p1 == p10 and p1 is not None else ('=tu' if p1 == tu and p1 is not None else ('-' if p1 is None else 'other'))) + '|tu' + ('' if tu is not None else '-')
        c[key] += 1
        if len(examples[key]) < 3: examples[key].append((i, LN if False else s, p1, tu))
for k, v in sorted(c.items(), key=lambda kv: -kv[1]): print(v, k)
for k in examples:
    print(k, [(i, (x or '')[:35], (y or '')[:35]) for i, _, x, y in examples[k]])
print('--- pack1 L0 at 1288,1291-1297,1316-1330 ---')
s = SPECS[0]
for i in [1288] + list(range(1291, 1298)) + list(range(1316, 1331)):
    print(i, 'p10', (txt('pack10', s, i) or '<MISS>')[:40], '| p1', (txt('pack1', s, i) or '<MISS>')[:40], '| tu', (txt('tu', s, i) or '<MISS>')[:40])
