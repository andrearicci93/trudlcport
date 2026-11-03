#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
credits_convert.py - crea credits_DLC1.bik (Bink 1) dai crediti Xbox 360 del DLC1 "Beneath the Ashes".
credits_convert.py - builds credits_DLC1.bik (Bink 1) from the Xbox 360 credits movie of DLC1.

Solo libreria standard di Python 3.8+ (nessun pacchetto da installare).
Python 3.8+ standard library only (nothing to pip-install).

NON include ne' distribuisce ffmpeg, RAD Video Tools, il filmato Xbox o il .bik prodotto.
It does NOT bundle or redistribute ffmpeg, RAD Video Tools, the Xbox movie or the produced .bik.

Esito / exit code: 0 = .bik creato e validato, 1 = errore (vedi messaggio e log).
Exit code: 0 = .bik created and validated, 1 = error (see message and log).
"""
import argparse, json, os, shutil, struct, subprocess, sys, time

# parametrizzato per DLC1/DLC2 (b266): --dlc 1|2 (default 1 = comportamento originale)
PROFILES = {
    '1': dict(frames=12271, dur=409.5),
    '2': dict(frames=12181, dur=406.5),
}
DLC = '1'
SRC_NAME = 'credits_DLC1.wmv'
OUT_NAME = 'credits_DLC1.bik'
# profilo validato (confronto con credits.bik del gioco base, vedi REPORT.md)
EXPECT = dict(container='asf', vcodec='wmv3', w=1280, h=720, fps=30.0, acodec='wmav2', frames=12271, dur=409.5)
RAD_VIDEO_ARGS = ['/V100', '/F30', '/D200000', '/O']   # Bink 1, 30 fps, data rate 200000 B/s, sovrascrivi
RAD_AUDIO_LEVEL = '5'                                   # /L5 ~ 12.5-13 KB/s, come credits.bik base
URL_RAD = 'https://www.radgametools.com/bnkdown.htm (RAD Video Tools, 7z cifrato, password: RAD)'
URL_FFMPEG = 'https://www.gyan.dev/ffmpeg/builds/ (Windows) / https://evermeet.cx/ffmpeg/ (macOS) / pacchetto ffmpeg della distro'

LOG = None


def log(s):
    line = time.strftime('%H:%M:%S ') + s
    print(line, flush=True)
    if LOG:
        LOG.write(line + '\n'); LOG.flush()


def msg(it, en):
    return it + '\n          ' + en


class Fail(Exception):
    pass


def fail(it, en):
    raise Fail(msg(it, en))


# ---------------------------------------------------------------- ricerca / find
def find_source(path):
    if os.path.isfile(path):
        return path
    if not os.path.isdir(path):
        fail('ERRORE: percorso non trovato: %s' % path, 'ERROR: path not found: %s' % path)
    hits = []
    for root, _dirs, files in os.walk(path):
        for f in files:
            if f.lower() == SRC_NAME.lower():
                hits.append(os.path.join(root, f))
    if not hits:
        fail('ERRORE: %s non trovato sotto %s. Passare la cartella del contenuto Xbox del DLC1 '
             '(es. .../Content/534307EC/00000002/<id>/).' % (SRC_NAME, path),
             'ERROR: %s not found under %s. Pass the DLC1 Xbox content folder '
             '(e.g. .../Content/534307EC/00000002/<id>/).' % (SRC_NAME, path))
    hits.sort()
    if len(hits) > 1:
        log('ATTENZIONE/WARNING: piu\' copie trovate, uso la prima / several copies, using first: ' + hits[0])
    return hits[0]


def find_tool(name, explicit):
    if explicit:
        if os.path.isfile(explicit):
            return explicit
        fail('ERRORE: %s indicato ma non esiste: %s' % (name, explicit),
             'ERROR: %s given but does not exist: %s' % (name, explicit))
    return shutil.which(name)


def find_rad(explicit):
    """Cerca radvideo64.exe / radvideo32.exe (RAD Video Tools, contiene il compressore Bink 1 da riga di comando)."""
    if explicit:
        if os.path.isfile(explicit):
            return explicit
        fail('ERRORE: --rad indicato ma non esiste: %s' % explicit, 'ERROR: --rad given but does not exist: %s' % explicit)
    cands = []
    env = os.environ.get('RAD_VIDEO_TOOLS')
    if env:
        cands += [env, os.path.join(env, 'radvideo64.exe'), os.path.join(env, 'radvideo32.exe')]
    for nm in ('radvideo64.exe', 'radvideo64', 'radvideo32.exe', 'radvideo32'):
        w = shutil.which(nm)
        if w:
            cands.append(w)
    for base in (os.environ.get('ProgramFiles'), os.environ.get('ProgramFiles(x86)'), os.environ.get('LOCALAPPDATA'),
                 os.path.expanduser('~/Desktop'), os.path.expanduser('~/Downloads'), 'C:\\'):
        if not base:
            continue
        for sub in ('RADVideo', 'RAD Video Tools', 'RAD Game Tools\\RAD Video Tools', 'RAD Game Tools', 'Epic Games Tools\\RAD Video Tools', 'Bink', ''):
            for exe in ('radvideo64.exe', 'radvideo32.exe'):
                cands.append(os.path.join(base, sub, exe))
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return None


# ---------------------------------------------------------------- ffprobe / formato
def probe(ffprobe, src):
    r = subprocess.run([ffprobe, '-v', 'error', '-show_format', '-show_streams', '-of', 'json', src],
                       capture_output=True, text=True)
    if r.returncode != 0:
        fail('ERRORE: ffprobe non riesce a leggere %s:\n%s' % (src, r.stderr.strip()),
             'ERROR: ffprobe cannot read %s:\n%s' % (src, r.stderr.strip()))
    return json.loads(r.stdout)


def check_format(info, force):
    fmt = info.get('format', {})
    streams = info.get('streams', [])
    v = next((s for s in streams if s.get('codec_type') == 'video'), None)
    a = next((s for s in streams if s.get('codec_type') == 'audio'), None)
    probs = []
    if 'asf' not in fmt.get('format_name', ''):
        probs.append('container %s != asf' % fmt.get('format_name'))
    if not v:
        probs.append('nessun video / no video stream')
    else:
        if v.get('codec_name') != EXPECT['vcodec']:
            probs.append('video %s != %s' % (v.get('codec_name'), EXPECT['vcodec']))
        if (v.get('width'), v.get('height')) != (EXPECT['w'], EXPECT['h']):
            probs.append('risoluzione/resolution %sx%s != %dx%d' % (v.get('width'), v.get('height'), EXPECT['w'], EXPECT['h']))
        try:
            n, d = v.get('r_frame_rate', '0/1').split('/')
            fps = float(n) / float(d)
        except Exception:
            fps = 0.0
        if abs(fps - EXPECT['fps']) > 0.01:
            probs.append('fps %.3f != %.1f' % (fps, EXPECT['fps']))
    if not a:
        probs.append('nessun audio / no audio stream')
    elif a.get('codec_name') != EXPECT['acodec']:
        probs.append('audio %s != %s' % (a.get('codec_name'), EXPECT['acodec']))
    try:
        dur = float(fmt.get('duration', 0))
    except Exception:
        dur = 0.0
    if abs(dur - EXPECT['dur']) > 5.0:
        probs.append('durata/duration %.1f s != ~%.1f s' % (dur, EXPECT['dur']))
    if probs:
        text = '; '.join(probs)
        if force:
            log('ATTENZIONE/WARNING: formato diverso dall\'atteso (--force): ' + text)
        else:
            fail('ERRORE: formato inatteso: %s.\n          Atteso: ASF, WMV3 1280x720 30 fps, WMA2, ~%.1f s. '
                 'Se e\' il file giusto usare --force.' % (text, EXPECT['dur']),
                 'ERROR: unexpected format: %s.\n          Expected: ASF, WMV3 1280x720 30 fps, WMA2, ~%.1f s. '
                 'Use --force if it is really the right file.' % (text, EXPECT['dur']))
    return v, a, dur


# ---------------------------------------------------------------- decodifica
def run(cmd, what):
    log('> ' + ' '.join('"%s"' % c if ' ' in c else c for c in cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        fail('ERRORE: %s fallito (codice %d):\n%s' % (what, r.returncode, r.stderr[-1500:]),
             'ERROR: %s failed (code %d):\n%s' % (what, r.returncode, r.stderr[-1500:]))
    return r


def decode(ffmpeg, src, work, limit):
    png = os.path.join(work, 'png')
    os.makedirs(png, exist_ok=True)
    wav = os.path.join(work, 'credits_DLC%s.wav' % DLC)
    for f in os.listdir(png):
        if f.endswith('.png'):
            os.remove(os.path.join(png, f))
    # video -> sequenza PNG senza perdita (provata con RAD; un AVI utvideo in VM non ha prodotto output, vedi REPORT)
    vcmd = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', src, '-map', '0:v:0', '-an',
            '-start_number', '1', '-compression_level', '3']
    if limit:
        vcmd += ['-frames:v', str(limit)]
    run(vcmd + [os.path.join(png, 'f%05d.png')], 'ffmpeg video->PNG')
    acmd = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', src, '-map', '0:a:0', '-vn', '-c:a', 'pcm_s16le']
    if limit:
        acmd += ['-t', '%.3f' % (limit / 30.0)]
    run(acmd + [wav], 'ffmpeg audio->WAV')
    n = len([f for f in os.listdir(png) if f.endswith('.png')])
    if n == 0 or not os.path.isfile(wav):
        fail('ERRORE: la decodifica non ha prodotto frame/audio.', 'ERROR: decoding produced no frames/audio.')
    return png, wav, n


# ---------------------------------------------------------------- RAD (GUI con riga di comando)
def _windows_titles(pid):
    """Titoli delle finestre di primo livello del processo (solo Windows, ctypes)."""
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    titles = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _lp):
        p = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid:
            n = user32.GetWindowTextLengthW(hwnd)
            if n:
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                titles.append(buf.value)
        return True
    proc = WNDENUMPROC(cb)
    user32.EnumWindows(proc, 0)
    return titles


def run_rad(rad, args, out_file, timeout, what):
    """Lancia RADVideo (applicazione a finestra: non termina da sola, mostra 'Done!' nel titolo)."""
    if os.path.exists(out_file):
        os.remove(out_file)
    cmd = [rad] + args
    log('> ' + ' '.join('"%s"' % c if ' ' in c else c for c in cmd))
    p = subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(out_file)))
    t0 = time.time()
    last = ''
    done = False
    try:
        while time.time() - t0 < timeout:
            rc = p.poll()
            titles = _windows_titles(p.pid) if rc is None else []
            t = ' | '.join(titles)
            if t != last:
                log('  %s: %s' % (what, t))
                last = t
            if any('Done' in x for x in titles):
                done = True
                break
            if rc is not None:
                done = rc == 0
                break
            time.sleep(2)
        else:
            fail('ERRORE: %s: timeout dopo %d s.' % (what, timeout), 'ERROR: %s: timeout after %d s.' % (what, timeout))
    finally:
        if p.poll() is None:
            time.sleep(1)
            p.terminate()
            try:
                p.wait(10)
            except Exception:
                p.kill()
    if not done or not os.path.isfile(out_file) or os.path.getsize(out_file) < 1024:
        fail('ERRORE: %s non ha prodotto %s (finestra RAD chiusa o errore: controllare i percorsi, niente spazi/accenti).' % (what, out_file),
             'ERROR: %s did not produce %s (RAD window closed or error: check paths, avoid odd characters).' % (what, out_file))


# ---------------------------------------------------------------- validazione .bik
def validate_bik(path, ffmpeg, nframes, dur):
    d = open(path, 'rb').read(4096)
    magic = d[:4]
    if magic[:3] != b'BIK' or magic[3:4] not in b'fghi':
        fail('ERRORE: intestazione non Bink 1 f-i: %r (il gioco accetta solo BIKf/g/h/i).' % magic,
             'ERROR: header is not Bink 1 f-i: %r (the game only accepts BIKf/g/h/i).' % magic)
    size, frames, _largest, _f2, w, h, fn, fd, flags, ntr = struct.unpack_from('<IIIIIIIIII', d, 4)
    probs = []
    if (w, h) != (EXPECT['w'], EXPECT['h']):
        probs.append('dimensioni/size %dx%d' % (w, h))
    if frames != nframes:
        probs.append('frame %d != %d' % (frames, nframes))
    if fd == 0 or abs(fn / fd - 30.0) > 0.01:
        probs.append('fps %d/%d' % (fn, fd))
    if ntr < 1:
        probs.append('nessuna traccia audio / no audio track')
    else:
        info, = struct.unpack_from('<I', d, 44 + 4 * ntr)
        if (info & 0xffff) != 44100 or (info >> 16) != 0x7000:
            probs.append('audio rate=%d flags=0x%x (atteso 44100 / 0x7000)' % (info & 0xffff, info >> 16))
    if os.path.getsize(path) - 8 != size:
        probs.append('dimensione file incoerente con intestazione / file size mismatch')
    if probs:
        fail('ERRORE: validazione .bik fallita: ' + '; '.join(probs), 'ERROR: .bik validation failed: ' + '; '.join(probs))
    log('Intestazione/header OK: %s %dx%d %d frame %.3f fps, %d traccia/e audio, %d byte' %
        (magic.decode(), w, h, frames, fn / fd, ntr, os.path.getsize(path)))
    if ffmpeg:
        r = subprocess.run([ffmpeg, '-hide_banner', '-nostats', '-v', 'error', '-xerror', '-i', path, '-f', 'null', '-'],
                           capture_output=True, text=True)
        if r.returncode != 0:
            fail('ERRORE: ffmpeg non decodifica il .bik fino in fondo:\n' + r.stderr[-800:],
                 'ERROR: ffmpeg cannot decode the .bik to the end:\n' + r.stderr[-800:])
        log('Decodifica completa con ffmpeg OK / full ffmpeg decode OK')
    else:
        log('ATTENZIONE/WARNING: ffmpeg assente, decodifica non verificata / no ffmpeg, decode not verified')


# ---------------------------------------------------------------- main
def set_dlc(n):
    global DLC, SRC_NAME, OUT_NAME
    DLC = n
    SRC_NAME = 'credits_DLC%s.wmv' % n
    OUT_NAME = 'credits_DLC%s.bik' % n
    EXPECT.update(PROFILES[n])


def main():
    global LOG
    ap = argparse.ArgumentParser(description='Converte i crediti Xbox del DLC1 in credits_DLC1.bik (Bink 1). / '
                                 'Converts the DLC1 Xbox credits movie to credits_DLC1.bik (Bink 1).')
    ap.add_argument('xbox_content', help='cartella del contenuto Xbox del DLC1 (ricerca ricorsiva di credits_DLC1.wmv) o il file stesso / '
                    'DLC1 Xbox content folder (recursive search for credits_DLC1.wmv) or the file itself')
    ap.add_argument('-o', '--out', default='.', help='cartella di uscita (o file .bik) / output folder (or .bik file) [default: .]')
    ap.add_argument('--game-dir', help='cartella del gioco: copia anche in <game-dir>\\movies\\ / game folder: also copy to <game-dir>\\movies\\')
    ap.add_argument('--work', help='cartella di lavoro (serve ~1.5 GB liberi) / work folder (~1.5 GB free)')
    ap.add_argument('--ffmpeg'); ap.add_argument('--ffprobe')
    ap.add_argument('--rad', help='percorso di radvideo64.exe (RAD Video Tools) / path to radvideo64.exe')
    ap.add_argument('--prepare-only', action='store_true', help='solo decodifica (PNG+WAV) e istruzioni manuali RAD / decode only + manual RAD instructions')
    ap.add_argument('--force', action='store_true', help='ignora il controllo del formato / ignore the format check')
    ap.add_argument('--keep-work', action='store_true', help='non cancellare i file intermedi / keep intermediate files')
    ap.add_argument('--limit-frames', type=int, default=0, help='(solo test) converte solo i primi N frame / (test only) first N frames')
    ap.add_argument('--timeout', type=int, default=3 * 3600, help='timeout per ogni passo RAD in secondi / per-RAD-step timeout in seconds')
    ap.add_argument('--dlc', choices=sorted(PROFILES), default='1', help='quale DLC (1 o 2) / which DLC (1 or 2) [default: 1]')
    a = ap.parse_args()
    set_dlc(a.dlc)

    out = a.out
    if out.lower().endswith('.bik'):
        out_dir, out_file = os.path.dirname(os.path.abspath(out)), os.path.abspath(out)
    else:
        out_dir = os.path.abspath(out); out_file = os.path.join(out_dir, OUT_NAME)
    os.makedirs(out_dir, exist_ok=True)
    work = os.path.abspath(a.work or os.path.join(out_dir, 'credits_work'))
    os.makedirs(work, exist_ok=True)
    LOG = open(os.path.join(out_dir, 'credits_convert.log'), 'a', encoding='utf-8')
    log('=== credits_convert %s ===' % time.strftime('%Y-%m-%d %H:%M:%S'))
    try:
        src = find_source(a.xbox_content)
        log('Sorgente / source: ' + src)
        ffmpeg = find_tool('ffmpeg', a.ffmpeg)
        ffprobe = find_tool('ffprobe', a.ffprobe) or (os.path.join(os.path.dirname(ffmpeg), 'ffprobe' + ('.exe' if os.name == 'nt' else '')) if ffmpeg else None)
        if not ffmpeg or not ffprobe or not os.path.isfile(ffprobe):
            fail('ERRORE: ffmpeg/ffprobe non trovati. Scaricarli da %s e passare --ffmpeg/--ffprobe oppure metterli nel PATH.' % URL_FFMPEG,
                 'ERROR: ffmpeg/ffprobe not found. Download from %s and pass --ffmpeg/--ffprobe or add them to PATH.' % URL_FFMPEG)
        v, _a, dur = check_format(probe(ffprobe, src), a.force)
        log('Formato OK / format OK: WMV3 %sx%s, durata %.1f s' % (v.get('width'), v.get('height'), dur))
        png, wav, n = decode(ffmpeg, src, work, a.limit_frames)
        log('Decodificati %d frame + WAV / decoded %d frames + WAV' % (n, n))

        rad = find_rad(a.rad)
        if a.prepare_only or not rad or os.name != 'nt':
            manual = ('PASSI MANUALI / MANUAL STEPS (RAD Video Tools, solo Windows / Windows only):\n'
                      '  1) Scaricare/Download RAD Video Tools: %s\n'
                      '  2) Da una finestra comandi / from a command prompt, nella cartella %s:\n'
                      '     radvideo64.exe Binkc "%s" credits_DLC%s_v.bik %s\n'
                      '     (attendere "Done!" nella finestra, poi chiuderla / wait for "Done!" then close the window)\n'
                      '     radvideo64.exe BinkMix credits_DLC%s_v.bik "%s" credits_DLC%s.bik /L%s /T0 /O\n'
                      '  3) Equivale in GUI a: Bink 1 (/V100), 30 fps, data rate 200000 B/s, audio 44100 Hz stereo, livello audio %s, traccia 0.\n'
                      '  4) Copiare credits_DLC%s.bik in <cartella del gioco>\\movies\\' %
                      (URL_RAD, work, os.path.join(png, 'f?????.png*1-%d' % n), DLC, ' '.join(RAD_VIDEO_ARGS), DLC, wav, DLC, RAD_AUDIO_LEVEL, RAD_AUDIO_LEVEL, DLC))
            if a.prepare_only:
                log('Preparazione completata / preparation done.\n' + manual)
                return 0
            if not rad:
                fail('ERRORE: RAD Video Tools (radvideo64.exe) non trovato.\n' + manual,
                     'ERROR: RAD Video Tools (radvideo64.exe) not found: install it or pass --rad.\n' + manual)
            fail('ERRORE: la compressione RAD Bink funziona solo su Windows.\n' + manual,
                 'ERROR: RAD Bink compression only runs on Windows.\n' + manual)
        log('RAD Video Tools: ' + rad)
        vtmp = os.path.join(work, 'credits_DLC%s_v.bik' % DLC)
        run_rad(rad, ['Binkc', os.path.join(png, 'f?????.png*1-%d' % n), vtmp, '/V100', '/F30', '/D200000', '/O'],
                vtmp, a.timeout, 'Binkc')
        mixed = os.path.join(work, OUT_NAME)
        run_rad(rad, ['BinkMix', vtmp, wav, mixed, '/L' + RAD_AUDIO_LEVEL, '/T0', '/O'], mixed, a.timeout, 'BinkMix')
        validate_bik(mixed, ffmpeg, n, dur)
        shutil.copyfile(mixed, out_file)
        log('Creato / created: %s (%d byte)' % (out_file, os.path.getsize(out_file)))
        if a.game_dir:
            mv = os.path.join(a.game_dir, 'movies')
            if not os.path.isdir(a.game_dir):
                fail('ERRORE: --game-dir non esiste: %s' % a.game_dir, 'ERROR: --game-dir does not exist: %s' % a.game_dir)
            try:
                os.makedirs(mv, exist_ok=True)
                shutil.copyfile(out_file, os.path.join(mv, OUT_NAME))
            except OSError as e:
                fail('ERRORE: copia in %s non riuscita (%s). Il file e\' pronto in %s: copiarlo a mano in <gioco>\\movies\\ '
                     'oppure rilanciare come amministratore (le cartelle sotto Program Files sono protette).' % (mv, e, out_file),
                     'ERROR: could not copy to %s (%s). The file is ready at %s: copy it by hand to <game>\\movies\\ '
                     'or rerun as administrator (folders under Program Files are protected).' % (mv, e, out_file))
            log('Copiato in / copied to: ' + os.path.join(mv, OUT_NAME))
        if not a.keep_work:
            shutil.rmtree(png, ignore_errors=True)
            for f in (wav, vtmp):
                if os.path.exists(f):
                    os.remove(f)
        return 0
    except Fail as e:
        log(str(e))
        return 1
    except Exception as e:  # noqa
        log('ERRORE imprevisto / unexpected error: %r' % (e,))
        return 1
    finally:
        LOG.close()


if __name__ == '__main__':
    sys.exit(main())
