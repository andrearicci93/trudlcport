#!/usr/bin/env python3
"""Install the Tomb Raider: Underworld Xbox 360 DLC port on the PC (Steam) game.

Builds the exact `mods/` tree, the patched `tru.exe` and `movies/credits_DLC1.bik` of the reference build from YOUR OWN files:
  * the PC game (Steam, tru.exe v1.1, bigfile.000-003, patch.000),
  * the Xbox 360 DLC content files (pack10.000 = Beneath the Ashes, required; pack11.000 = Lara's Shadow, optional;
    credits_DLC1.wmv from the Beneath the Ashes content folder).
Each output file is produced by applying a binary patch (bsdiff4) to the matching file from your copy; every source and every
result is checked against the MD5 in manifest.json. Nothing in the game folder is deleted: the old mods/ folder and the original
tru.exe are kept as backups.

Requirements: Python 3.9+ and `pip install bsdiff4`.
Usage:
  python install_dlc.py --game "C:/Program Files (x86)/Steam/steamapps/common/Tomb Raider Underworld" --dlc "D:/xbox/Content/534307EC/00000002" --kit ./kit
  python install_dlc.py ... --check        only verify inputs, write nothing
  python install_dlc.py ... --no-exe       do not patch tru.exe
"""
import argparse, hashlib, json, os, shutil, struct, sys, time, zlib

ALIGN = 0x7FF00000

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

def find_file(root, name):
    for dp, dn, fn in os.walk(root, followlinks=True):
        for f in fn:
            if f.lower() == name.lower(): return os.path.join(dp, f)
    return None

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--game', required=True, help='PC game folder (contains tru.exe, bigfile.000, patch.000)')
    ap.add_argument('--dlc', required=True, help='folder that contains the Xbox 360 DLC files (searched recursively for pack10.000, pack11.000, credits_DLC1.wmv)')
    ap.add_argument('--kit', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kit'), help='folder with manifest.json and patches/')
    ap.add_argument('--check', action='store_true', help='verify all inputs, write nothing')
    ap.add_argument('--no-exe', action='store_true', help='do not patch tru.exe')
    a = ap.parse_args()
    try:
        import bsdiff4
    except ImportError:
        sys.exit('Missing module: run   python -m pip install bsdiff4')
    man = json.load(open(os.path.join(a.kit, 'manifest.json')))
    print('Reference build:', man['build'])
    g = a.game
    for f in ('tru.exe', 'bigfile.000', 'patch.000'):
        if not os.path.isfile(os.path.join(g, f)): sys.exit('Not a TRU game folder (missing %s): %s' % (f, g))
    packs = {}
    for p in ('pack10.000', 'pack11.000'):
        q = find_file(a.dlc, p)
        if q: packs[p] = Archive(q, 'be'); print('found', p, '->', q)
    if 'pack10.000' not in packs: sys.exit('pack10.000 (Beneath the Ashes) not found under %s' % a.dlc)
    if 'pack11.000' not in packs: print('pack11.000 (Lara\'s Shadow) not found: its %d optional files (DLC2 menu images/music) will be skipped' % sum(1 for f in man['files'] if f['optional'] == 'dlc2'))
    arcs = dict(packs); arcs['patch.000'] = Archive(os.path.join(g, 'patch.000'), 'le'); arcs['bigfile.000'] = Archive(os.path.join(g, 'bigfile.000'), 'le')
    ts = time.strftime('%Y%m%d_%H%M%S')
    stage = os.path.join(g, 'mods.new_' + ts)
    ok = skip = 0; bad = []
    for f in man['files']:
        s = f['source']
        if s['archive'] not in arcs: skip += 1; continue
        sb = arcs[s['archive']].read(s['name'], s['spec'])
        if sb is None or md5(sb) != s['md5']:
            bad.append('%s: source %s in %s %s' % (f['rel'], s['name'], s['archive'], 'missing' if sb is None else 'has a different MD5 (different game/DLC version?)')); continue
        if a.check: ok += 1; continue
        tb = bsdiff4.patch(sb, open(os.path.join(a.kit, f['patch']), 'rb').read())
        if md5(tb) != f['md5']: bad.append('%s: result MD5 mismatch' % f['rel']); continue
        out = os.path.join(stage, f['rel']); os.makedirs(os.path.dirname(out), exist_ok=True); open(out, 'wb').write(tb); ok += 1
    extra_out = []
    for x in man['extra']:
        s = x['source']
        if x['rel'] == 'tru.exe':
            if a.no_exe: continue
            sp = os.path.join(g, 'tru.exe'); cur = md5(open(sp, 'rb').read())
            if cur == x['md5']: print('tru.exe is already the patched one'); continue
            bk = os.path.join(g, 'tru.exe.steam_original')
            if cur != s['md5'] and os.path.isfile(bk) and md5(open(bk, 'rb').read()) == s['md5']: sp = bk
            elif cur != s['md5']: bad.append('tru.exe: expected the Steam v1.1 exe (MD5 %s), found %s' % (s['md5'], cur)); continue
        else:
            sp = find_file(a.dlc, s['file'])
            if not sp: bad.append('%s: %s not found under --dlc' % (x['rel'], s['file'])); continue
        sb = open(sp, 'rb').read()
        if md5(sb) != s['md5']: bad.append('%s: source %s has a different MD5' % (x['rel'], sp)); continue
        if a.check: ok += 1; continue
        tb = bsdiff4.patch(sb, open(os.path.join(a.kit, x['patch']), 'rb').read())
        if md5(tb) != x['md5']: bad.append('%s: result MD5 mismatch' % x['rel']); continue
        extra_out.append((x['rel'], tb)); ok += 1
    if bad:
        print('\nPROBLEMS (nothing has been changed in the game folder):'); [print('  ' + b) for b in bad]
        if os.path.isdir(stage): shutil.rmtree(stage)
        sys.exit(1)
    if a.check:
        print('\nAll inputs OK (%d files verified, %d optional skipped). Run again without --check to install.' % (ok, skip)); return
    mods = os.path.join(g, 'mods')
    if os.path.isdir(mods): os.rename(mods, os.path.join(g, 'mods_backup_' + ts)); print('old mods/ kept as mods_backup_' + ts)
    os.rename(stage, mods)
    for rel, tb in extra_out:
        out = os.path.join(g, rel)
        if rel == 'tru.exe' and not os.path.isfile(os.path.join(g, 'tru.exe.steam_original')):
            shutil.copy2(out, os.path.join(g, 'tru.exe.steam_original')); print('original tru.exe kept as tru.exe.steam_original')
        os.makedirs(os.path.dirname(out), exist_ok=True); open(out, 'wb').write(tb)
    print('\nInstalled: %d files (%d optional skipped).' % (ok, skip))
    for need in ('ModLoader.asi', 'binkw32.dll'):
        if not os.path.isfile(os.path.join(g, need)): print('WARNING: %s not found in the game folder: install ModLoader (see README).' % need)

if __name__ == '__main__':
    main()
