"""Regole per parola dei DTP 'piccoli' dei DRM cinstream, imparate da TUTTE le coppie base Xbox/PC (stesso nome, DTP
accoppiati in ordine dentro il tipo, stessa dimensione). Classe per parola: s32 (swap 4), s16 (swap di due u16), raw, oppure
'id' (valore diverso: riferimento rimappato). Chiave = (famiglia = prima parola>>16 del record 0, offset modulo passo)."""
import sys, os, struct, collections, json
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm
from archive import Archive
from names import crc
def secs(d, e): return drm.sections_with_data(drm.cdrm_decode(d, e), e)[1]
def cls(x, p):
    if x[::-1] == p and x[1::-1] + x[3:1:-1] == p: return 'both'
    if x[::-1] == p: return 's32'
    if x[1::-1] + x[3:1:-1] == p: return 's16'
    if x == p: return 'raw'
    return 'other'
pcb = Archive(os.path.join(T, '..', 'pc', 'bigfile.000'), 'le')
XB = [Archive('/path/to/TombRaiderUnderworld_Patched/layer%d.000' % i, 'be') for i in (1, 2)]
names = [l.strip() for l in open(os.path.join(T, '..', 'ref', 'yura-release', 'FileLists', 'Tomb Raider Underworld (PC).txt'), errors='ignore')
         if 'cinstream' in l.lower() and l.strip().lower().endswith('.drm')]
pairs = []
for n in names:
    pr = pcb.find(crc(n)); xn = n.replace('pc-w', 'xenon-w')
    xd = next((A.read(A.find(crc(xn))[0]) for A in XB if A.find(crc(xn))), None)
    if not pr or xd is None: continue
    X = [s for s in secs(xd, 'be') if s['type'] == 7]; P = [s for s in secs(pcb.read(pr[0]), 'le') if s['type'] == 7]
    for x, p in zip(X, P):
        if x['size'] == p['size'] and x['size'] not in (12736,) and x['size'] < 4096 and x['data'][:1] in (b'\x20', b'\x28', b'\x00'):
            pairs.append((n.split('\\')[-1], x, p))
print('coppie DTP', len(pairs))
fam = collections.defaultdict(collections.Counter); ex = {}
for n, x, p in pairs:
    xd, pd = x['data'], p['data']
    f = xd[:2].hex()
    for o in range(0, len(xd) - 3, 4):
        c = cls(xd[o:o + 4], pd[o:o + 4])
        fam[(f, len(xd) % 20 == 0, o % 20)][c] += 1
for k in sorted(fam): print(k, dict(fam[k]))
json.dump({'%s|%s|%d' % k: dict(v) for k, v in fam.items()}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dtp_rules.json'), 'w'), indent=0)
print('=== per tipo di record (u16 iniziale del record da 20 B)')
rt = collections.defaultdict(collections.Counter); tails = collections.Counter()
for n, x, p in pairs:
    xd, pd = x['data'], p['data']
    if xd[:1] not in (b'\x20', b'\x28'): continue
    nrec = len(xd) // 20
    for r in range(nrec):
        o = 20 * r; t = xd[o:o + 2].hex()
        for k in range(5): rt[(t, k)][cls(xd[o + 4 * k:o + 4 * k + 4], pd[o + 4 * k:o + 4 * k + 4])] += 1
    tails[(len(xd) % 20, tuple(cls(xd[o:o + 4], pd[o:o + 4]) for o in range(20 * nrec, len(xd) - 3, 4)))] += 1
for k in sorted(rt): print(k, dict(rt[k]))
print('code', tails.most_common(10))
print('=== 2001/2005: classe parola 4 per messaggio (u16 alto di parola 3)')
m4 = collections.defaultdict(collections.Counter); bad = []
for n, x, p in pairs:
    xd, pd = x['data'], p['data']
    for r in range(len(xd) // 20):
        o = 20 * r; t = xd[o:o + 2].hex()
        if t not in ('2001', '2005'): continue
        msg = struct.unpack_from('>H', xd, o + 12)[0]
        c = cls(xd[o + 16:o + 20], pd[o + 16:o + 20])
        m4[(t, msg)][c] += 1
for k in sorted(m4): print(k, dict(m4[k]))
