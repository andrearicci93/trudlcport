#!/usr/bin/env python3
"""Install the Tomb Raider: Underworld Xbox 360 DLC port (Beneath the Ashes + Lara's Shadow) on the PC (Steam) game.

Kit format 2 (B269 and later). Every output file is rebuilt on YOUR machine from YOUR OWN files:
  * the PC game (Steam, v1.1): bigfile.000-003, patch.000 and tru.exe unpacked with Steamless (see README),
  * the Xbox 360 DLC packages: pack10.000 (Beneath the Ashes) and pack11.000 (Lara's Shadow),
  * optionally credits_DLC1.wmv / credits_DLC2.wmv (end credits; converted locally with RAD Video Tools, --credits).
How: each DRM is decompressed, its Xbox textures are converted on your PC (tex_convert.py), then a binary patch (bsdiff4)
turns that into the PC file, which is recompressed. Every source, every intermediate and every written file is checked
against the MD5 in manifest.json. Nothing is deleted: the old mods/ and tru.exe are kept, and --restore puts them back.

Requirements: Python 3.9+ and   python -m pip install bsdiff4 numpy
Usage:
  python install_dlc.py --game "<game folder>" --dlc "<folder with the Xbox DLC files>" --kit kit --check   verify only
  python install_dlc.py --game ... --dlc ... --kit kit                       install (DLC1 + DLC2)
  python install_dlc.py --game ... --dlc ... --kit kit --credits --rad "<...\\radvideo64.exe>"   + end credits (Windows);
                                                       if this build is already installed and intact, only the credits are built
  python install_dlc.py --game ... --verify                                  re-check the installed files against the record
  python install_dlc.py --game ... --restore                                 undo the last install (mods/, tru.exe, credits)
Options: --no-exe (keep tru.exe), --dlc1-only (UNTESTED: skip DLC2 files, pack11.000 not needed).
"""
import argparse, hashlib, json, os, shutil, struct, subprocess, sys, time, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ALIGN = 0x7FF00000
CDRM_BLOCK = 0x40000
RECORD = 'trudlcport_install.json'
STEAM_EXE_MD5 = 'b36da327a320eab8b5c8464b27685840'        # Steam tru.exe v1.1 (SteamStub-wrapped)
FORMAT = 2


# ------------------------------------------------------------------ archive / container helpers (shared with the kit builder)
def crc(s):
    h = 0xffffffff
    for c in s.lower():
        h ^= ord(c) << 24
        for _ in range(8):
            h = ((h << 1) ^ 0x4c11db7) & 0xffffffff if h & 0x80000000 else (h << 1) & 0xffffffff
    return ~h & 0xffffffff


class Archive:
    """cdcEngine bigfile (PC: little endian, Xbox 360: big endian)."""
    def __init__(self, path, endian):
        e = '>' if endian == 'be' else '<'
        self.path = path; self.base = os.path.splitext(path)[0]
        with open(path, 'rb') as f:
            n, = struct.unpack(e + 'I', f.read(4))
            hashes = struct.unpack(e + '%dI' % n, f.read(4 * n))
            recs = [struct.unpack(e + 'IIIi', f.read(16)) for _ in range(n)]
        self.idx = {}
        for h, r in zip(hashes, recs):
            self.idx.setdefault(h, []).append(dict(size=r[0], offset=r[1], spec=r[2], clen=r[3]))

    def read(self, name, spec):
        for r in self.idx.get(crc(name), []):
            if r['spec'] != spec: continue
            pos = r['offset'] << 11
            part, off = divmod(pos, ALIGN) if self.path.endswith('.000') else (0, pos)
            p = '%s.%03d' % (self.base, part) if self.path.endswith('.000') else self.path
            with open(p, 'rb') as f:
                f.seek(off)
                return zlib.decompress(f.read(r['clen'])) if r['clen'] > 0 else f.read(r['size'])
        return None


def md5(b): return hashlib.md5(b).hexdigest()


def md5_file(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''): h.update(blk)
    return h.hexdigest()


def cdrm_decode(d, endian):
    if d[:4] not in (b'CDRM', b'MRDC'): return d
    e = '>' if endian == 'be' else '<'
    n, = struct.unpack(e + 'I', d[8:12])
    ents = [struct.unpack(e + 'II', d[16 + 8 * i:24 + 8 * i]) for i in range(n)]
    pos = (16 + 8 * n + 15) & ~15; out = bytearray()
    for u, c in ents:
        blk = d[pos:pos + c]
        out += zlib.decompress(blk) if (u & 0xff) == 2 else blk
        pos = (pos + c + 15) & ~15
    return bytes(out)


def cdrm_encode(raw, block=CDRM_BLOCK, level=9):
    """Same encoder as tools/drm_write.py (PC, little endian, zlib level 9, 256 KiB blocks)."""
    blocks = [raw[i:i + block] for i in range(0, len(raw), block)] or [b'']
    comp = [zlib.compress(b, level) for b in blocks]
    out = bytearray(struct.pack('<4sIII', b'CDRM', 0, len(blocks), 0))
    for b, c in zip(blocks, comp): out += struct.pack('<II', len(b) << 8 | 2, len(c))
    for c in comp:
        out += b'\0' * (-len(out) % 16); out += c
    return bytes(out)


def drm_sections(raw, endian):
    e = '>' if endian == 'be' else '<'
    ver, namesz, padsz, u0, u1, n = struct.unpack(e + 'iiiiii', raw[:24])
    secs, p = [], 24
    for _ in range(n):
        size, typ, pad, vid, packed, sid, spec = struct.unpack(e + 'iBBHIII', raw[p:p + 20]); p += 20
        secs.append([size, typ, packed >> 8, sid])
    p += namesz + padsz
    for s in secs:
        p += s[2]; yield s[1], s[3], raw[p:p + s[0]]; p += s[0]


def tex_aux(raw_be):
    """Xbox texture sections of the user's DRM converted to PC layout on this machine (no game data in the kit)."""
    sys.path.insert(0, HERE)
    import tex_convert as TC
    out = bytearray()
    for typ, sid, data in drm_sections(raw_be, 'be'):
        if typ == 5:
            try: out += TC.convert(data)
            except Exception: pass
    return bytes(out)


def build_old(entry, src_bytes, pc_bytes):
    """Patch source for one file (the kit builder calls the very same function)."""
    if entry['mode'] == 'cdrm':
        raw = cdrm_decode(src_bytes, 'be' if entry['source']['kind'] == 'xbox' else 'le')
        old = bytearray(raw)
        if 'tex' in entry['aux']: old += tex_aux(raw)
        if 'pc' in entry['aux'] and pc_bytes is not None: old += cdrm_decode(pc_bytes, 'le')
        return bytes(old)
    old = bytearray(src_bytes)
    if 'pc' in entry['aux'] and pc_bytes is not None: old += pc_bytes
    return bytes(old)


def finish(entry, new):
    """Patched bytes -> final file bytes. Returns (bytes, status) with status 'exact' or 'equivalent'."""
    if entry['mode'] == 'cdrm':
        if md5(new) != entry['raw_md5']: return None, 'raw MD5 mismatch'
        out = cdrm_encode(new)
        return out, 'exact' if md5(out) == entry['md5'] else 'equivalent'   # 'equivalent' = same content, other zlib build
    return (new, 'exact') if md5(new) == entry['md5'] else (None, 'result MD5 mismatch')


# ------------------------------------------------------------------ per-file work (runs in worker processes)
_W = {}


def _init_worker(pack_paths, game, kit, stage, check):
    arcs = {k: Archive(q, 'be') for k, q in pack_paths.items()}
    arcs['patch.000'] = Archive(os.path.join(game, 'patch.000'), 'le')
    arcs['bigfile.000'] = Archive(os.path.join(game, 'bigfile.000'), 'le')
    import bsdiff4
    _W.update(arcs=arcs, kit=kit, stage=stage, check=check, bsdiff4=bsdiff4)


def _process_file(f):
    """Rebuild one kit file. Returns dict(rel, err, st, h). The result is written straight to the stage folder."""
    arcs, kit, stage, check = _W['arcs'], _W['kit'], _W['stage'], _W['check']
    s = f['source']
    if s is None:                                     # port-authored text (MD5.txt, notes): shipped as is
        if check: return dict(rel=f['rel'], err=None)
        tb = open(os.path.join(kit, f['patch']), 'rb').read(); st = 'exact' if md5(tb) == f['md5'] else 'bad'
    else:
        sb = arcs[s['archive']].read(s['name'], s['spec']) if s['archive'] in arcs else None
        if sb is None or md5(sb) != s['md5']:
            return dict(rel=f['rel'], err='%s: source %s in %s %s' % (f['rel'], s['name'], s['archive'], 'missing' if sb is None else 'has a different MD5 (different game/DLC version?)'))
        pb = None
        if f.get('pc_also'):
            q = f['pc_also']; pb = arcs[q['archive']].read(q['name'], q['spec'])
            if pb is None or md5(pb) != q['md5']: return dict(rel=f['rel'], err='%s: PC file %s missing or different' % (f['rel'], q['name']))
        old = build_old(f, sb, pb)                       # also in --check: catches numpy/Python conversion drift before installing
        if f.get('old_md5') and md5(old) != f['old_md5']:
            why = ''
            if f.get('tex_md5') and 'tex' in f['aux']:
                why = ' (texture conversion differs: numpy %s)' % __import__('numpy').__version__ if md5(tex_aux(cdrm_decode(sb, 'be'))) != f['tex_md5'] else ' (decompression differs)'
            return dict(rel=f['rel'], err='%s: converted source differs from the kit%s. Please report your Python and numpy versions.' % (f['rel'], why or ' (numpy/python difference?)'))
        if check: return dict(rel=f['rel'], err=None)
        tb, st = finish(f, _W['bsdiff4'].patch(old, open(os.path.join(kit, f['patch']), 'rb').read()))
        if tb is None: return dict(rel=f['rel'], err='%s: %s' % (f['rel'], st))
    if st == 'bad': return dict(rel=f['rel'], err='%s: kit file damaged' % f['rel'])
    out = os.path.join(stage, f['rel']); os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'wb') as fo: fo.write(tb)
    h = md5_file(out)                                  # re-read from disk: catches disk/antivirus problems
    if h != md5(tb): return dict(rel=f['rel'], err='%s: written file differs from memory (disk problem?)' % f['rel'])
    return dict(rel=f['rel'], err=None, st=st, h=h)


def _process_safe(f):
    try: return _process_file(f)
    except Exception as e: return dict(rel=f['rel'], err='%s: unexpected error %s: %s' % (f['rel'], type(e).__name__, e))


# ------------------------------------------------------------------ install
def find_file(root, name):
    for dp, dn, fn in os.walk(root, followlinks=True):
        for f in fn:
            if f.lower() == name.lower(): return os.path.join(dp, f)
    return None


def load_record(g):
    p = os.path.join(g, RECORD)
    return json.load(open(p)) if os.path.isfile(p) else None


def verify(g, rec):
    bad = []
    for rel, h in rec['files'].items():
        p = os.path.join(g, 'mods', rel)
        if not os.path.isfile(p): bad.append('missing: mods/' + rel)
        elif md5_file(p) != h: bad.append('changed: mods/' + rel)
    for rel, h in rec.get('extra', {}).items():
        p = os.path.join(g, rel)
        if not os.path.isfile(p) or md5_file(p) != h: bad.append('missing/changed: ' + rel)
    return bad


def restore(g):
    rec = load_record(g)
    if not rec: sys.exit('No %s in %s: nothing to restore (or it was not installed with this installer).' % (RECORD, g))
    ts = time.strftime('%Y%m%d_%H%M%S')
    mods = os.path.join(g, 'mods')
    if os.path.isdir(mods):
        os.rename(mods, os.path.join(g, 'mods_removed_' + ts)); print('installed mods/ moved to mods_removed_' + ts)
    if rec.get('mods_backup') and os.path.isdir(os.path.join(g, rec['mods_backup'])):
        os.rename(os.path.join(g, rec['mods_backup']), mods); print('previous mods/ restored from', rec['mods_backup'])
    if rec.get('exe_backup'):
        bk = os.path.join(g, rec['exe_backup'])
        if os.path.isfile(bk):
            shutil.copy2(os.path.join(g, 'tru.exe'), os.path.join(g, 'tru.exe.removed_' + ts))
            shutil.copy2(bk, os.path.join(g, 'tru.exe')); print('tru.exe restored from', rec['exe_backup'])
    for rel in rec.get('credits', []):
        p = os.path.join(g, rel)
        if os.path.isfile(p): os.rename(p, p + '.removed_' + ts); print(rel, 'renamed to', os.path.basename(p) + '.removed_' + ts)
    os.rename(os.path.join(g, RECORD), os.path.join(g, RECORD + '.restored_' + ts))
    print('Restore done. Nothing was deleted: the removed files carry the suffix _%s.' % ts)


def run_credits(a, g):
    """End credits: credits_convert.py (ffmpeg + RAD Video Tools, Windows). The .bik is never shipped: it is made here."""
    made = []
    conv = os.path.join(HERE, 'credits_convert.py')
    if not os.path.isfile(conv): print('credits_convert.py missing next to install_dlc.py: credits skipped'); return made
    for n in ('1', '2'):
        if n == '2' and a.dlc1_only: continue
        out = os.path.join(g, 'movies', 'credits_DLC%s.bik' % n)
        if os.path.isfile(out) and not a.redo_credits: print('movies/credits_DLC%s.bik already there (use --redo-credits to rebuild)' % n); continue
        cmd = [sys.executable, conv, '--dlc', n, a.dlc, '-o', os.path.join(g, 'trudlcport_credits'), '--game-dir', g]
        for k in ('rad', 'ffmpeg', 'ffprobe'):
            if getattr(a, k): cmd += ['--' + k, getattr(a, k)]
        print('\n> credits DLC%s (5-20 min, ~1.5 GB free space needed)' % n)
        r = subprocess.call(cmd)
        if r == 0 and os.path.isfile(out): made.append('movies/credits_DLC%s.bik' % n)
        else: print('Credits DLC%s FAILED (see trudlcport_credits/credits_convert.log). The DLC still installs, but WITHOUT this movie the '
                    'game hangs on a black screen after the final cutscene.' % n)
    return made


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--game', required=True, help='PC game folder (contains tru.exe, bigfile.000, patch.000)')
    ap.add_argument('--dlc', help='folder with the Xbox 360 DLC files (searched recursively for pack10.000, pack11.000, credits_DLC*.wmv)')
    ap.add_argument('--kit', default=os.path.join(HERE, 'kit'), help='folder with manifest.json and patches/')
    ap.add_argument('--check', action='store_true', help='verify all inputs, write nothing')
    ap.add_argument('--no-exe', action='store_true', help='do not patch tru.exe')
    ap.add_argument('--exe-source', help='Steamless output of your tru.exe (default: <game>/tru.exe.unpacked.exe or an already unpacked tru.exe)')
    ap.add_argument('--dlc1-only', action='store_true', help='UNTESTED: skip the Lara\'s Shadow files (pack11.000 not needed)')
    ap.add_argument('--credits', action='store_true', help='also build movies/credits_DLC1.bik and credits_DLC2.bik (Windows, ffmpeg + RAD Video Tools)')
    ap.add_argument('--redo-credits', action='store_true'); ap.add_argument('--rad'); ap.add_argument('--ffmpeg'); ap.add_argument('--ffprobe')
    ap.add_argument('--jobs', '-j', type=int, default=0, help='parallel worker processes (default: CPU cores, max 8; 1 = sequential). Lower it if the PC runs out of RAM')
    ap.add_argument('--reinstall', action='store_true', help='install again even if the same build is installed and intact')
    ap.add_argument('--verify', action='store_true', help='re-check the installed files against the install record')
    ap.add_argument('--restore', action='store_true', help='undo the last install (old mods/, tru.exe; credits renamed)')
    a = ap.parse_args()
    g = a.game
    if a.restore: return restore(g)
    if a.verify:
        rec = load_record(g)
        if not rec: sys.exit('No install record (%s) in %s' % (RECORD, g))
        bad = verify(g, rec)
        print('Installed build %s: %d files checked, %s' % (rec['build'], len(rec['files']) + len(rec.get('extra', {})), 'all OK' if not bad else '%d problems' % len(bad)))
        for b in bad[:50]: print('  ' + b)
        sys.exit(1 if bad else 0)
    if not a.dlc: sys.exit('--dlc is required to install')
    try:
        import bsdiff4
    except ImportError:
        sys.exit('Missing module: run   python -m pip install bsdiff4 numpy')
    man = json.load(open(os.path.join(a.kit, 'manifest.json')))
    if man.get('format') != FORMAT: sys.exit('This installer needs a kit of format %d (this kit: %s). Use the install_dlc.py that came with the kit.' % (FORMAT, man.get('format')))
    if any('tex' in f['aux'] for f in man['files']):
        try:
            import numpy  # noqa: F401  (tex_convert.py)
        except ImportError:
            sys.exit('Missing module: run   python -m pip install numpy')
    print('Reference build:', man['build'])
    rec = load_record(g)
    if a.credits and rec and rec.get('build') == man['build'] and not a.check and not a.reinstall:
        bad = verify(g, rec)
        if not bad:                                      # same build already installed and intact: only (re)build the credits
            print('Build %s is already installed and intact: only the credits are built (use --reinstall to install again).' % man['build'])
            rec['credits'] = sorted(set(rec.get('credits', []) + run_credits(a, g)))
            json.dump(rec, open(os.path.join(g, RECORD), 'w'), indent=1); return
        print('Installed files differ from the record (%d problems): installing again.' % len(bad))
    for f in ('tru.exe', 'bigfile.000', 'patch.000'):
        if not os.path.isfile(os.path.join(g, f)): sys.exit('Not a TRU game folder (missing %s): %s' % (f, g))
    packs = {}
    for p in ('pack10.000', 'pack11.000'):
        q = find_file(a.dlc, p)
        if q: packs[p] = q; print('found', p, '->', q)
    if 'pack10.000' not in packs: sys.exit('pack10.000 (Beneath the Ashes) not found under %s' % a.dlc)
    if 'pack11.000' not in packs and not a.dlc1_only:
        sys.exit('pack11.000 (Lara\'s Shadow) not found under %s.\nThe shared files of this build are made for both DLCs; '
                 'use --dlc1-only to install without it (UNTESTED).' % a.dlc)
    ts = time.strftime('%Y%m%d_%H%M%S'); stage = os.path.join(g, 'mods.new_' + ts)
    ok = skip = 0; bad = []; equiv = []; res = {}
    todo = [f for f in man['files'] if not (a.dlc1_only and f['dlc'] == 'dlc2')]
    skip = len(man['files']) - len(todo)
    jobs = a.jobs if a.jobs > 0 else min(os.cpu_count() or 1, 8)
    jobs = max(1, min(jobs, len(todo) or 1))
    print('Processing %d files with %d worker process%s' % (len(todo), jobs, '' if jobs == 1 else 'es'), flush=True)
    t0 = time.time(); done = 0
    initargs = (packs, g, a.kit, stage, a.check)
    def note(r):
        nonlocal done
        done += 1; res[r['rel']] = r
        if done % 25 == 0 or done == len(todo): print('  %d/%d  %.0fs' % (done, len(todo), time.time() - t0), flush=True)
    if jobs == 1:
        _init_worker(*initargs)
        for f in todo: note(_process_safe(f))
    else:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=jobs, initializer=_init_worker, initargs=initargs) as ex:
            for fu in as_completed([ex.submit(_process_safe, f) for f in todo]): note(fu.result())
    written = {}
    for f in todo:                                         # manifest order, so messages and the record are deterministic
        r = res[f['rel']]
        if r['err']: bad.append(r['err']); continue
        ok += 1
        if not a.check:
            written[f['rel']] = r['h']
            if r['st'] == 'equivalent': equiv.append(f['rel'])
    exe_out = None
    x = man.get('exe')
    if x and not a.no_exe:
        cur = md5_file(os.path.join(g, 'tru.exe'))
        if cur == x['md5']: print('tru.exe is already the patched one')
        else:
            cands = [a.exe_source] if a.exe_source else [os.path.join(g, n) for n in (
                'tru.exe.unpacked.exe', 'tru.exe', 'tru.exe.steam_original.unpacked.exe', 'tru.exe.steamless_original')]
            sp = next((c for c in cands if c and os.path.isfile(c) and md5_file(c) == x['source']['md5']), None)
            if not sp and os.path.isfile(os.path.join(g, 'tru.exe.steam_original')) and cur != STEAM_EXE_MD5:
                bad.append('tru.exe: your tru.exe was patched by an older build of this port (MD5 %s). Run Steamless (default options) on '
                           'tru.exe.steam_original: it writes tru.exe.steam_original.unpacked.exe (MD5 %s), then start again.' % (cur, x['source']['md5']))
            elif not sp:
                bad.append('tru.exe: need the Steamless-unpacked v1.1 exe (MD5 %s). Your tru.exe is %s%s. Run Steamless on tru.exe '
                           'with default options (it writes tru.exe.unpacked.exe next to it) and start again, or use --no-exe.' % (
                               x['source']['md5'], cur, ' (the Steam original, as expected)' if cur == STEAM_EXE_MD5 else ''))
            elif not a.check:
                tb = bsdiff4.patch(open(sp, 'rb').read(), open(os.path.join(a.kit, x['patch']), 'rb').read())
                if md5(tb) != x['md5']: bad.append('tru.exe: result MD5 mismatch')
                else: exe_out = tb
            else: ok += 1
    if bad:
        print('\nPROBLEMS (nothing has been changed in the game folder):'); [print('  ' + b) for b in bad]
        if os.path.isdir(stage): shutil.rmtree(stage)
        sys.exit(1)
    if a.check:
        print('\nAll inputs OK (%d files verified, %d DLC2 files skipped). Run again without --check to install.' % (ok, skip)); return
    rec = dict(build=man['build'], kit_format=FORMAT, time=ts, files=written, extra={}, mods_backup=None, exe_backup=None, credits=[],
               equivalent=equiv, dlc1_only=a.dlc1_only)
    mods = os.path.join(g, 'mods')
    if os.path.isdir(mods):
        rec['mods_backup'] = 'mods_backup_' + ts; os.rename(mods, os.path.join(g, rec['mods_backup'])); print('old mods/ kept as', rec['mods_backup'])
    os.rename(stage, mods)
    if exe_out:
        bk = 'tru.exe.before_trudlcport_' + ts
        shutil.copy2(os.path.join(g, 'tru.exe'), os.path.join(g, bk)); rec['exe_backup'] = bk
        if not os.path.isfile(os.path.join(g, 'tru.exe.steam_original')) and md5_file(os.path.join(g, 'tru.exe')) == STEAM_EXE_MD5:
            shutil.copy2(os.path.join(g, 'tru.exe'), os.path.join(g, 'tru.exe.steam_original'))
        with open(os.path.join(g, 'tru.exe'), 'wb') as fo: fo.write(exe_out)
        if md5_file(os.path.join(g, 'tru.exe')) != x['md5']: print('WARNING: tru.exe on disk differs after writing (antivirus?)')
        rec['extra']['tru.exe'] = x['md5']; print('tru.exe patched (previous one kept as %s)' % bk)
    json.dump(rec, open(os.path.join(g, RECORD), 'w'), indent=1)
    if a.credits:
        rec['credits'] = run_credits(a, g)
        json.dump(rec, open(os.path.join(g, RECORD), 'w'), indent=1)
    print('\nInstalled: %d files (%d DLC2 files skipped).%s' % (ok, skip, (' %d DRM are content-identical but recompressed by a different '
          'zlib build: fine.' % len(equiv)) if equiv else ''))
    bad2 = verify(g, rec)
    print('Final check of the installed files:', 'OK' if not bad2 else '%d problems: %s' % (len(bad2), bad2[:5]))
    for n in ('1', '2'):
        if n == '2' and a.dlc1_only: continue
        if not os.path.isfile(os.path.join(g, 'movies', 'credits_DLC%s.bik' % n)):
            print('NOTE: movies/credits_DLC%s.bik is missing. It is REQUIRED to finish the DLC (without it the game stays on a black screen '
                  'after the final cutscene). Build it with --credits (Windows, RAD Video Tools) - see README.' % n)
    for need in ('ModLoader.asi', 'binkw32.dll'):
        if not os.path.isfile(os.path.join(g, need)): print('WARNING: %s not found in the game folder: install ModLoader (see README).' % need)
    print('Undo at any time with:  python install_dlc.py --game "%s" --restore' % g)


if __name__ == '__main__':
    main()
