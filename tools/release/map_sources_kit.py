# Release kit v2 (B269+): per ogni file finale della baseline, la sorgente nei file dell'utente (pack DLC Xbox, gioco PC) da cui
# parte la patch, piu' il DLC di appartenenza. Copia parametrizzata di ../../map_sources.py (l'originale non e' toccato).
# uso: python -I map_sources_kit.py --baseline B269_nativo [--out sources_B269_nativo.json]
#      (--baseline accetta un nome sotto work/baseline/ oppure un percorso)
import sys, os, glob, json, hashlib, argparse, collections
T = '/Users/andrearicci/Downloads/tru-port'; sys.path.insert(0, T + '/tools')
from archive import Archive
from names import crc
import convert_dlc as C, override_merge as OM

KIT_PACKS = C.PACKS[:2]          # solo pack10 (DLC1) e pack11 (DLC2): sono i file che l'utente deve avere
SKIP_EXT = ('.md', '.log')
# file senza omonimo nei file dell'utente: patch da un file donatore (stesso contenuto di partenza, clone fatto dal port)
DONORS = {'dlc_doppel_costume_a.drm': 'doppelganger_casual.drm'}

def resolve_baseline(b):
    if os.path.isdir(b): return os.path.abspath(b)
    hits = sorted(glob.glob(T + '/work/baseline/' + b + '*'))
    if not hits: sys.exit('baseline non trovata: %s (non ancora derivata?)' % b)
    return hits[-1]

def load_manifest_origin(B):
    """manifest.tsv della baseline: relpath -> origin/eccezione (serve per decidere DLC1/DLC2/condiviso)."""
    m = {}
    p = os.path.join(B, 'manifest.tsv')
    if os.path.isfile(p):
        for ln in open(p, encoding='utf-8', errors='replace').read().splitlines()[1:]:
            c = ln.split('\t')
            if len(c) >= 4: m[c[0]] = (c[3], c[5] if len(c) > 5 else '')
    return m

DLC2_HINTS = ('dlc2', 'doppel', 'natla', 'goo', 'ceremony', 'pdlc2', 'controls_dlc2')

def which_dlc(rel, src):
    low = rel.lower()
    if src and src['archive'] == 'pack10.000': return 'dlc1'
    if src and src['archive'] == 'pack11.000': return 'dlc2'
    if any(h in low for h in DLC2_HINTS): return 'dlc2'
    return 'shared'              # file del gioco PC rifatti per il port (generalbank, globalsoundinfo, locals, l3_main_bedroom ...)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--baseline', required=True); ap.add_argument('--out')
    a = ap.parse_args()
    B = resolve_baseline(a.baseline); name = os.path.basename(B).split('-')[0]
    out = a.out or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sources_%s.json' % name)
    packs = [(p.split('/')[-1], Archive(C.R + p, 'be')) for p in KIT_PACKS]
    pc = [('patch.000', Archive(OM.SRC['pcpatch'][0], 'le')), ('bigfile.000', Archive(OM.SRC['pcbig'][0], 'le'))]
    def find(arcs, nm):
        for an, ar in arcs:
            r = list(ar.find(crc(nm)))
            r1 = [x for x in r if x['spec'] == 0xffffffff] or r
            if r1: return an, r1[0]
        return None
    org = load_manifest_origin(B)
    rows, miss = [], []
    for p in sorted(glob.glob(B + '/mods/**/*', recursive=True)):
        if not os.path.isfile(p): continue
        rel = os.path.relpath(p, B + '/mods'); low = rel.lower()
        if low.endswith(SKIP_EXT): continue
        w = rel.replace('/', '\\')
        if low.startswith('tr8/'): cands = [('pc', '\\' + w), ('pc', w)]
        elif low.startswith('local/'): cands = [('pc', 'pc-w\\local\\locals.bin')]
        else: cands = [('xbox', 'xenon-w\\' + w), ('pc', 'pc-w\\' + w)]
        if low in DONORS: cands.append(('xbox', 'xenon-w\\' + DONORS[low]))
        src = None
        for kind, nm in cands:
            f = find(packs if kind == 'xbox' else pc, nm)
            if f: src = dict(kind=kind, archive=f[0], name=nm, spec=f[1]['spec'], size=f[1]['size']); break
        # sorgente PC aggiuntiva con lo stesso nome (file del gioco base rifatti dal port): entra nella sorgente della patch
        pcalso = None
        if src and src['kind'] == 'xbox':
            f = find(pc, 'pc-w\\' + w)
            if f: pcalso = dict(kind='pc', archive=f[0], name='pc-w\\' + w, spec=f[1]['spec'], size=f[1]['size'])
        tgt = open(p, 'rb').read()
        o = org.get(rel, ('', ''))
        rows.append(dict(rel=rel, size=len(tgt), md5=hashlib.md5(tgt).hexdigest(), source=src, pc_also=pcalso,
                         dlc=which_dlc(rel, src), origin=o[0]))
        if not src: miss.append(rel)
    json.dump(dict(baseline=os.path.basename(B), rows=rows), open(out, 'w'), indent=1)
    print('baseline', os.path.basename(B), '->', out)
    print('file', len(rows), 'con sorgente', len(rows) - len(miss), 'senza sorgente', len(miss))
    for m in miss: print('  SENZA SORGENTE:', m)
    print(collections.Counter((r['source'] or {}).get('archive') for r in rows))
    print(collections.Counter(r['dlc'] for r in rows))

if __name__ == '__main__':
    main()
