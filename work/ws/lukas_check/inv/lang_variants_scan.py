"""lang_variants_scan.py - (19/11/2026) solo lettura. Dal fork di Lukas (tools/mul_lang_build.py):
i pack Xbox tengono ogni .mul di cine/voce una volta per lingua (spec 0xffffffe1 EN, e002 FR, e004 DE, e008 IT, e010 ES);
ModLoader carica la variante come <nome>_NNN (001 EN, 002 FR, 004 DE, 008 IT, 016 ES).
Conta, per ogni .mul della baseline, quante lingue ha l'Xbox e quante varianti _NNN abbiamo noi.
uso: python -I -B lang_variants_scan.py BASELINE"""
import sys, os, re, collections
sys.path.insert(0, '/path/to/trudlcport/tools')
from archive import Archive
from dlc_names import PACKS, fcrc
B = '/path/to/trudlcport/work/baseline/%s/mods/' % sys.argv[1]
BS = chr(92)
LANG = {0xffffffe1: 1, 0xffffe002: 2, 0xffffe004: 4, 0xffffe008: 8, 0xffffe010: 16}
A = {p: Archive(PACKS[p], 'be') for p in ('pack11', 'pack10')}
have = set()
for root, _, fs in os.walk(B):
    for f in fs: have.add(os.path.relpath(os.path.join(root, f), B).replace(BS, '/').lower())
tot = collections.Counter()
for rel in sorted(have):
    if not rel.endswith('.mul') or re.search(r'_\d{3}$', rel): continue
    h = fcrc('xenon-w' + BS + rel.replace('/', BS))
    for p, a in A.items():
        specs = sorted({r['spec'] for r in a.idx if r['hash'] == h})
        if specs: break
    else:
        print('NO XBOX', rel); continue
    langs = [LANG[s] for s in specs if s in LANG]
    if len(langs) < 2: tot['monolingua'] += 1; continue
    var = [n for n in (1, 2, 4, 8, 16) if '%s_%03d' % (rel, n) in have]
    tot['multilingua'] += 1; tot['varianti_presenti'] += len(var); tot['varianti_attese'] += len(langs)
    print('%-70s %s xbox lingue %s  nostre varianti _NNN %s' % (rel, p, langs, var or '-'))
# testo: locals.bin varianti
loc = sorted(r for r in have if 'locals.bin' in r)
print('locals.bin presenti:', loc)
print('TOTALE', dict(tot))
