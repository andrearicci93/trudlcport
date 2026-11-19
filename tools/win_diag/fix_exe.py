#!/usr/bin/env python3
"""Porta tru.exe allo stato del port TRU DLC (build B270_acqua), tutto in automatico.

1. se manca l'exe sbloccato giusto (MD5 56d1ce2d...), lo rifa con Steamless (--realign) dall'exe originale di Steam;
2. applica la patch binaria (tru.exe.bsdiff) e verifica l'MD5 finale (2b7ee74c...);
3. salva il backup (tru.exe.steam_original) e aggiorna trudlcport_install.json.
Non servono i file Xbox. Requisiti: Python 3.9+ e  python -m pip install bsdiff4 (lo installa da solo se c'e' internet).
  python fix_exe.py [--game "C:/.../Tomb Raider Underworld"]      applica il fix
  python fix_exe.py --restore                                      rimette l'exe com'era prima
Se la cartella del gioco richiede i diritti di amministratore, si rilancia da sola con la richiesta di elevazione.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile, time, zipfile

PATCHED = '2b7ee74c37394be208195efd0952cd5f'     # exe del port (B269/B270)
UNPACKED = '56d1ce2dffa62f16354063da2df44d5a'     # Steam v1.1 sbloccato con Steamless --realign
STEAM = 'b36da327a320eab8b5c8464b27685840'        # Steam v1.1 originale
RECORD = 'trudlcport_install.json'
DEFAULT = r'C:\Program Files (x86)\Steam\steamapps\common\Tomb Raider Underworld'
HERE = os.path.dirname(os.path.abspath(__file__))
SL_URL = 'https://github.com/atom0s/Steamless/releases/download/v3.1.0.5/Steamless.v3.1.0.5.-.by.atom0s.zip'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    try:
        o = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq tru.exe'], capture_output=True, text=True).stdout
        return 'tru.exe' in o.lower()
    except Exception:
        return False


def is_admin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return True


def writable(g):
    t = os.path.join(g, '.trudiag_write_test')
    try:
        open(t, 'w').write('x'); os.remove(t); return True
    except Exception:
        return False


def elevate():
    """rilancia questo script come amministratore in una nuova finestra (resta aperta a fine lavoro)"""
    import ctypes
    args = ' '.join('"%s"' % a for a in sys.argv[1:])
    cmd = '/c ""%s" "%s" %s & pause"' % (sys.executable, os.path.abspath(__file__), args)
    r = ctypes.windll.shell32.ShellExecuteW(None, 'runas', 'cmd.exe', cmd, None, 1)
    if r <= 32:
        sys.exit('Elevazione rifiutata. Riavvia DIAG.bat con "Esegui come amministratore".')
    print('Rilanciato come amministratore in un\'altra finestra: continua li\'.')
    sys.exit(0)


def save_record(g, extra=None, exe_backup=None):
    p = os.path.join(g, RECORD)
    if not os.path.isfile(p):
        return
    rec = json.load(open(p))
    if extra:
        rec.setdefault('extra', {}).update(extra)
    if exe_backup and not rec.get('exe_backup'):
        rec['exe_backup'] = exe_backup
    json.dump(rec, open(p, 'w'), indent=1)


def get_steamless(work):
    """restituisce il percorso di Steamless.CLI.exe pronto all'uso (zip locale, altrimenti scaricato da GitHub)"""
    z = None
    for c in (os.path.join(HERE, 'backends', 'steamless', 'sl.zip'), os.path.join(HERE, 'sl.zip')):
        if os.path.isfile(c):
            z = c; break
    if not z:
        print('Steamless non incluso: lo scarico da GitHub...')
        z = os.path.join(work, 'sl.zip')
        try:
            import urllib.request
            urllib.request.urlretrieve(SL_URL, z)
        except Exception as e:
            sys.exit('ERRORE: non riesco a scaricare Steamless (%s). Mettilo a mano in backends\\steamless\\sl.zip.' % e)
    d = os.path.join(work, 'steamless')
    zipfile.ZipFile(z).extractall(d)
    api = os.path.join(d, 'Plugins', 'Steamless.API.dll')
    if os.path.isfile(api):
        shutil.copy2(api, d)          # la CLI vuole l'API accanto all'eseguibile
    cli = os.path.join(d, 'Steamless.CLI.exe')
    if not os.path.isfile(cli):
        sys.exit('ERRORE: Steamless.CLI.exe non trovato nello zip.')
    return cli


def make_unpacked(g, original):
    """Steamless sull'exe originale -> exe sbloccato con MD5 UNPACKED. Restituisce il percorso nella cartella temporanea."""
    work = tempfile.mkdtemp(prefix='trudiag_')
    cli = get_steamless(work)
    for opts in (['--realign'], ['--realign', '--recalcchecksum']):
        src = os.path.join(work, 'tru.exe')
        shutil.copy2(original, src)
        out = src + '.unpacked.exe'
        if os.path.isfile(out):
            os.remove(out)
        print('Steamless %s su %s ...' % (' '.join(opts), os.path.basename(original)))
        r = subprocess.run([cli, '--quiet'] + opts + [src], capture_output=True, text=True, cwd=os.path.dirname(cli))
        if os.path.isfile(out) and md5(out) == UNPACKED:
            print('  OK: exe sbloccato con MD5 %s' % UNPACKED)
            return out
        print('  MD5 ottenuto: %s' % (md5(out) if os.path.isfile(out) else 'nessun file (%s)' % (r.stdout[-300:] + r.stderr[-300:]).strip()))
    sys.exit('ERRORE: Steamless non ha prodotto l\'exe atteso (MD5 %s). Manda il testo qui sopra.' % UNPACKED)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--game', default=DEFAULT)
    ap.add_argument('--patch', default=os.path.join(HERE, 'tru.exe.bsdiff'))
    ap.add_argument('--restore', action='store_true')
    a = ap.parse_args()
    g = a.game.rstrip('\\/')
    exe = os.path.join(g, 'tru.exe')
    if not os.path.isfile(exe):
        sys.exit('ERRORE: tru.exe non trovato in %s (usa --game)' % g)
    if running():
        sys.exit('ERRORE: tru.exe e\' in esecuzione: chiudi il gioco e riprova.')
    if not writable(g):
        if is_admin():
            sys.exit('ERRORE: cartella del gioco non scrivibile nemmeno da amministratore: %s' % g)
        print('La cartella del gioco richiede i diritti di amministratore.')
        elevate()
    cur = md5(exe)
    print('tru.exe attuale: MD5 %s' % cur)
    ts = time.strftime('%Y%m%d_%H%M%S')

    if a.restore:
        bk = os.path.join(g, 'tru.exe.steam_original')
        if not os.path.isfile(bk):
            try:
                bk = os.path.join(g, json.load(open(os.path.join(g, RECORD))).get('exe_backup') or 'tru.exe.steam_original')
            except Exception:
                pass
        if not os.path.isfile(bk):
            sys.exit('Nessun backup dell\'exe da ripristinare.')
        if cur != STEAM:
            shutil.copy2(exe, os.path.join(g, 'tru.exe.patched_%s' % ts))
        shutil.copy2(bk, exe)
        print('Ripristinato l\'exe originale (l\'exe patchato e\' salvato come tru.exe.patched_%s).' % ts)
        return

    if cur == PATCHED:
        print('OK: tru.exe e\' gia\' quello patchato del port. Niente da fare.')
        save_record(g, extra={'tru.exe': PATCHED})
        return

    if not os.path.isfile(a.patch):
        sys.exit('ERRORE: manca %s' % a.patch)
    try:
        import bsdiff4
    except ImportError:
        print('Modulo bsdiff4 mancante: provo a installarlo (serve internet)...')
        subprocess.call([sys.executable, '-m', 'pip', 'install', 'bsdiff4'])
        try:
            import bsdiff4
        except ImportError:
            sys.exit('ERRORE: installa a mano:  python -m pip install bsdiff4')

    # 1) exe sbloccato giusto
    unp = os.path.join(g, 'tru.exe.unpacked.exe')
    cands = [unp, exe, os.path.join(g, 'tru.exe.steam_original.unpacked.exe')]
    src = next((c for c in cands if os.path.isfile(c) and md5(c) == UNPACKED), None)
    if not src:
        if os.path.isfile(unp):
            print('tru.exe.unpacked.exe presente ma con MD5 %s (atteso %s): fatto senza l\'opzione --realign di Steamless.' % (md5(unp), UNPACKED))
        original = next((c for c in (exe, os.path.join(g, 'tru.exe.steam_original')) if os.path.isfile(c) and md5(c) == STEAM), None)
        if not original:
            sys.exit('ERRORE: manca un tru.exe originale di Steam (MD5 %s) da sbloccare. Usa "Verifica integrita\' dei file" di Steam e rilancia.' % STEAM)
        src = make_unpacked(g, original)
        if os.path.isfile(unp):
            shutil.copy2(unp, unp + '.old_%s' % ts)
        shutil.copy2(src, unp)
        print('Scritto %s' % unp)

    # 2) patch + verifica
    out = bsdiff4.patch(open(src, 'rb').read(), open(a.patch, 'rb').read())
    h = hashlib.md5(out).hexdigest()
    if h != PATCHED:
        sys.exit('ERRORE: risultato con MD5 %s invece di %s. Nessun file modificato.' % (h, PATCHED))

    # 3) backup, scrittura, registro
    bk = os.path.join(g, 'tru.exe.steam_original')
    if cur == STEAM and not os.path.isfile(bk):
        shutil.copy2(exe, bk); bkname = 'tru.exe.steam_original'
    elif os.path.isfile(bk):
        bkname = 'tru.exe.steam_original'
        shutil.copy2(exe, os.path.join(g, 'tru.exe.before_fix_%s' % ts))
    else:
        bkname = 'tru.exe.before_fix_%s' % ts
        shutil.copy2(exe, os.path.join(g, bkname))
    tmp = exe + '.new'
    open(tmp, 'wb').write(out)
    os.replace(tmp, exe)
    save_record(g, extra={'tru.exe': PATCHED}, exe_backup=bkname)
    print('')
    print('FATTO: tru.exe patchato (MD5 %s). Backup dell\'exe precedente: %s' % (PATCHED, bkname))
    print('Ora avvia il gioco da Steam e riprova (wall-run / pantaloni). Per annullare: python fix_exe.py --restore')
    print('NB: se Steam "verifica l\'integrita\'" dei file, rimette l\'exe originale: rilancia il fix.')


if __name__ == '__main__':
    main()
