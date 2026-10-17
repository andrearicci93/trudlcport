import sys, os, json, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f3_validate import *
LIGHTP = ('p_Lights', 'LightEnabled', 'p_ShadowEnabled', 'ParallelShadow', 'Irradiance', 'GlobalAmbientColor')
cen = json.load(open(os.path.join(HERE, 'f4_census.json')))
D = libs()['D']
rows = []; lit = []
for e in cen:
    names = set()
    for s in set(D[e['id']]['slots']):
        if s == 0xffffffff: continue
        names |= set(c['name'] for c in XL.parse(D[e['id']]['entries'][s]['blob']).ctab)
    lightn = sorted(n for n in names if n.startswith(LIGHTP))
    pos = ','.join(map(str, e['pos'])) or '-'
    if e['kind'] == 0: cat = 'VS (non tradotto: si tiene il VS PC)'; 
    elif e['lit']: cat = 'ILLUMINATO pos%s (non tradotto: modello luci Xbox)' % pos
    elif lightn: cat = 'IRRADIANCE pos%s (non tradotto)' % pos
    elif e['pos'] in ([0], [1]): cat = 'pos%s non illuminato: si tiene la lib PC (passo depth/ombra)' % pos
    elif e['id'] == 2173: cat = 'TRADOTTO (id sezione 2173)'
    else: cat = 'RIFIUTATO: ' + ('CUBE' if any('CUBE' in (r or '') for r in e['res']) else 'altro')
    rows.append((e['id'], e['cls'], e['pc'], 'VS' if e['kind'] == 0 else 'PS', pos, ','.join(e['drm']), e['nmat'], cat))
    if cat.startswith(('ILLUMINATO', 'IRRADIANCE')): lit.append((e['id'], e['cls'], e['pc'], pos, ','.join(e['drm']), e['nmat'], ';'.join(lightn)))
open(os.path.join(HERE, 'censimento.tsv'), 'w').write('id_xbox\tclasse\tid_pc_surrogato\ttipo\tposizione\tdrm\tn_materiali_dlc\tesito\n' + '\n'.join('\t'.join(map(str, r)) for r in rows) + '\n')
open(os.path.join(HERE, 'illuminati.tsv'), 'w').write('id_xbox\tclasse\tid_pc_surrogato\tposizione\tdrm\tn_materiali_dlc\tnomi_luci\n' + '\n'.join('\t'.join(map(str, r)) for r in lit) + '\n')
print(collections.Counter(r[7].split(' ')[0] + ' ' + r[3] for r in rows))
print('illuminati', len(lit))
perdrm = collections.defaultdict(lambda: collections.Counter())
for r in rows:
    for d in r[5].split(','):
        perdrm[d]['tot'] += 1
        if r[7].startswith('TRADOTTO'): perdrm[d]['tradotte'] += 1
        if r[7].startswith('ILLUMINATO') or r[7].startswith('IRRADIANCE'): perdrm[d]['illuminate'] += 1
for d in ('dlc_caverns.drm', 'dlc_caverns_hall.drm'): print(d, dict(perdrm[d]))
cl = collections.Counter((r[1], r[7].split(' ')[0]) for r in rows); print(sorted(cl.items()))
