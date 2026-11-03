# Release kit v2 (format 2): patch bsdiff4 dai file dell'utente verso la baseline, SENZA dati di gioco letterali dove evitabile:
#  - DRM: patch tra contenuti decompressi; la sorgente e' la DRM Xbox decompressa + le sue texture convertite al formato PC
#    (tex_convert.py, eseguito anche dall'installatore) + l'eventuale DRM PC omonima; l'installatore ricomprime (CDRM zlib 9).
#  - altri file: sorgente = voce d'archivio dell'utente (+ file PC omonimo).
#  - tru.exe: patch dall'exe Steam sbustato con Steamless (md5 56d1ce2d...), non dall'exe Steam cifrato (che darebbe il codice in chiaro).
#  - niente .bik (i crediti li genera l'utente con credits_convert.py / RAD Video Tools).
# Copia parametrizzata di ../../build_patches.py (l'originale non e' toccato). Le funzioni build_old/finish sono QUELLE dell'installatore.
# uso: python -I build_patches_kit.py --baseline B269_nativo [--exe .../tru_s8n_sap_cs2_cs.exe --exe-md5 2b7ee74c...] [--only a,b] [--jobs 3]
import sys, os, json, hashlib, time, argparse, glob
T = '/Users/andrearicci/Downloads/tru-port'; sys.path.insert(0, T + '/tools')
HERE = os.path.dirname(os.path.abspath(__file__)); KIT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(KIT, 'scripts')); sys.path.insert(0, os.path.join(KIT, '..', 'scripts')); sys.path.insert(0, HERE)   # kit_B269/scripts oppure repo/scripts
import bsdiff4
import install_dlc as I
import convert_dlc as C, override_merge as OM

DEF_EXE = T + '/work/ws/b269_crash/tru_s8n_sap_cs2_cs.exe'; DEF_EXE_MD5 = '2b7ee74c37394be208195efd0952cd5f'
EXE_SRC = T + '/work/laa/tru_steam.exe.unpacked.exe'; EXE_SRC_MD5 = '56d1ce2dffa62f16354063da2df44d5a'   # Steamless(tru.exe Steam v1.1)
ARC = None

def arcs():
    global ARC
    if ARC is None:
        ARC = {p.split('/')[-1]: I.Archive(C.R + p, 'be') for p in C.PACKS[:2]}
        ARC['patch.000'] = I.Archive(OM.SRC['pcpatch'][0], 'le'); ARC['bigfile.000'] = I.Archive(OM.SRC['pcbig'][0], 'le')
    return ARC

def entry_bytes(s):
    return arcs()[s['archive']].read(s['name'], s['spec']) if s else None

def work(job):
    r, B, OUT = job
    rel = r['rel']; tb = open(os.path.join(B, 'mods', rel), 'rb').read()
    pf = 'patches/' + rel.replace('/', '__') + '.bsdiff'
    e = dict(rel=rel, md5=r['md5'], size=r['size'], dlc=r['dlc'], patch=pf, source=None, pc_also=None, mode='plain', aux=[])
    if r['source'] is None:                                   # file scritto dal port (MD5.txt): copiato com'e'
        pf = 'authored/' + rel.replace('/', '__'); e['patch'] = pf
        os.makedirs(os.path.join(OUT, 'authored'), exist_ok=True); open(os.path.join(OUT, pf), 'wb').write(tb)
        return e
    sb = entry_bytes(r['source']); e['source'] = dict(r['source'], md5=hashlib.md5(sb).hexdigest())
    pb = entry_bytes(r.get('pc_also'))
    if pb is not None: e['pc_also'] = dict(r['pc_also'], md5=hashlib.md5(pb).hexdigest()); e['aux'].append('pc')
    new = tb
    if tb[:4] == b'CDRM' and sb[:4] == b'CDRM':
        raw = I.cdrm_decode(tb, 'le')
        if I.cdrm_encode(raw) == tb:
            e['mode'] = 'cdrm'; e['raw_md5'] = hashlib.md5(raw).hexdigest(); new = raw
            if r['source']['kind'] == 'xbox': e['aux'].insert(0, 'tex')
    old = I.build_old(e, sb, pb); e['old_md5'] = hashlib.md5(old).hexdigest()
    if 'tex' in e['aux']: e['tex_md5'] = hashlib.md5(I.tex_aux(I.cdrm_decode(sb, 'be'))).hexdigest()   # diagnosi deriva numpy
    d = bsdiff4.diff(old, new)
    chk, st = I.finish(e, bsdiff4.patch(old, d))
    if st != 'exact': raise RuntimeError('%s: verifica patch fallita (%s)' % (rel, st))
    with open(os.path.join(OUT, pf) + '.tmp', 'wb') as f: f.write(d)
    os.rename(os.path.join(OUT, pf) + '.tmp', os.path.join(OUT, pf))
    return e

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', required=True); ap.add_argument('--sources')
    ap.add_argument('--exe', default=DEF_EXE); ap.add_argument('--exe-md5', default=DEF_EXE_MD5)
    ap.add_argument('--out'); ap.add_argument('--only', help='solo questi rel (virgola): prova parziale')
    ap.add_argument('--jobs', type=int, default=3)
    a = ap.parse_args()
    import map_sources_kit as M
    B = M.resolve_baseline(a.baseline); name = os.path.basename(B).split('-')[0]
    SRCJ = a.sources or os.path.join(KIT, 'sources_%s.json' % name)
    if not os.path.isfile(SRCJ): sys.exit('manca %s: lanciare prima map_sources_kit.py --baseline %s' % (SRCJ, a.baseline))
    src = json.load(open(SRCJ))
    if src['baseline'] != os.path.basename(B): sys.exit('sources %s e\' di %s, non di %s' % (SRCJ, src['baseline'], os.path.basename(B)))
    OUT = a.out or os.path.join(KIT, 'out_' + name, 'kit'); os.makedirs(OUT + '/patches', exist_ok=True)
    rows = src['rows']
    if a.only: keep = set(a.only.split(',')); rows = [r for r in rows if r['rel'] in keep]
    man = dict(format=I.FORMAT, build=os.path.basename(B), files=[], exe=None,
               notes='Binary patches against the user\'s own files; no game data, no .bik. Built by build_patches_kit.py')
    t0 = time.time(); todo = sorted(rows, key=lambda r: -r['size'])
    from multiprocessing import Pool
    with Pool(a.jobs) as P:
        for k, e in enumerate(P.imap_unordered(work, [(r, B, OUT) for r in todo])):
            man['files'].append(e)
            if k % 20 == 0: print(k, e['rel'], e['mode'], e['aux'], '%.0fs' % (time.time() - t0), flush=True)
    man['files'].sort(key=lambda e: e['rel'])
    if a.exe and not a.only or (a.only and 'tru.exe' in a.only):
        tb = open(a.exe, 'rb').read(); sb = open(EXE_SRC, 'rb').read()
        if hashlib.md5(tb).hexdigest() != a.exe_md5: sys.exit('exe %s: md5 %s != atteso %s' % (a.exe, hashlib.md5(tb).hexdigest(), a.exe_md5))
        if hashlib.md5(sb).hexdigest() != EXE_SRC_MD5: sys.exit('sorgente exe Steamless con md5 inatteso')
        d = bsdiff4.diff(sb, tb); assert bsdiff4.patch(sb, d) == tb
        open(os.path.join(OUT, 'patches/tru.exe.bsdiff'), 'wb').write(d)
        man['exe'] = dict(rel='tru.exe', md5=a.exe_md5, size=len(tb), patch='patches/tru.exe.bsdiff', name=os.path.basename(a.exe),
                          source=dict(file='tru.exe (Steamless-unpacked)', md5=EXE_SRC_MD5, size=len(sb), steam_md5=I.STEAM_EXE_MD5))
    json.dump(man, open(OUT + '/manifest.json', 'w'), indent=1)
    print('fatto', len(man['files']), 'file', '+ exe' if man['exe'] else '', '%.0fs' % (time.time() - t0), '->', OUT)

if __name__ == '__main__':
    main()
