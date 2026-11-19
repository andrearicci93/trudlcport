"""Corregge sul PC i pixel shader del port rifiutati dal Direct3D 9 NATIVO (AMD ecc.): istruzioni con 2 registri costanti diversi.
   cmp r4, c167, r8, c222.y   ->   mov rT, c222 ; cmp r4, c167, r8, rT.y      (equivalenza bit per bit provata offline con sm3vm)
Modifica SOLO le sezioni 9 (shader) dei .drm in <gioco>\\mods; hash e id delle voci restano invariati.
Backup degli originali in <gioco>\\mods_backup_psfix (uno per file, mai sovrascritto). Annulla: --restore.
  python fix_ps.py [--game "C:\\...\\Tomb Raider Underworld"] [--dry-run] [--restore]
"""
import sys, os, struct, argparse, hashlib, shutil, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'native_test'))
import drm_write, constsplit

DEF = r'C:\Program Files (x86)\Steam\steamapps\common\Tomb Raider Underworld'


def lib_entries(d):
    kind = d[0]; tb, ds = struct.unpack_from('<II', d, 4)
    slots = list(struct.unpack_from('<%dI' % (tb // 4), d, 12)); ent = {}
    for o in set(s for s in slots if s != 0xffffffff):
        junk, size = struct.unpack_from('<II', d, 4 + o)
        ent[o] = (junk, d[4 + o + 8:4 + o + 16], d[4 + o + 16:4 + o + size])
    return kind, slots, ent


def lib_build(kind, slots, ent, repl):
    n = len(slots); tb = 4 * n; body = bytearray(); newoff = {}
    for o in sorted(ent):
        junk, h, bc = ent[o]; bc = repl.get(bc, bc)
        newoff[o] = 8 + tb + len(body)
        body += struct.pack('<II', junk, 16 + len(bc)) + h + bc
    out = bytearray(bytes([kind, 0, 0, 0]) + struct.pack('<II', tb, 0) + struct.pack('<%dI' % n, *[newoff.get(s, s) for s in slots]) + bytes(body))
    struct.pack_into('<I', out, 8, len(out) - 4)
    return bytes(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', default=DEF); ap.add_argument('--dry-run', action='store_true'); ap.add_argument('--restore', action='store_true')
    a = ap.parse_args()
    mods = os.path.join(a.game, 'mods'); bk = os.path.join(a.game, 'mods_backup_psfix')
    if not os.path.isdir(mods): print('ERRORE: manca la cartella', mods); return 2
    if a.restore:
        n = 0
        for dp, dn, fn in os.walk(bk):
            for f in fn:
                p = os.path.join(dp, f); rel = os.path.relpath(p, bk); shutil.copy2(p, os.path.join(mods, rel)); n += 1
        print('ripristinati %d file da %s' % (n, bk)); return 0
    files = []
    for dp, dn, fn in os.walk(mods):
        for f in sorted(fn):
            p = os.path.join(dp, f)
            if f.lower().endswith('.drm'):
                with open(p, 'rb') as fh:
                    if fh.read(4) == b'CDRM': files.append(p)
    print('DRM trovati: %d' % len(files))
    fixed = {}; changed = []; skipped = []; nblob = 0
    for p in sorted(files):
        raw = open(p, 'rb').read(); d = drm_write.read(raw, 'le'); touched = False
        for s in d.sections:
            if s.type != 9: continue
            kind, slots, ent = lib_entries(s.data)
            repl = {}
            for o, (junk, h, bc) in ent.items():
                if len(bc) < 8 or struct.unpack_from('<I', bc)[0] != 0xFFFF0300 or not constsplit.count_bad(bc): continue
                if bc not in fixed:
                    nb, n = constsplit.fix(bc)
                    if nb is None or constsplit.count_bad(nb): print('  NON correggibile (blob in %s)' % os.path.relpath(p, mods)); continue
                    fixed[bc] = nb
                repl[bc] = fixed[bc]
            if repl:
                if lib_build(kind, slots, ent, {}) != s.data: skipped.append((p, 'formato lib non standard')); continue
                s.data = lib_build(kind, slots, ent, repl); touched = True
        if not touched: continue
        new = drm_write.cdrm_encode(d.write('le'), 'le')
        if drm_write.cdrm_encode(drm_write.read(raw, 'le').write('le'), 'le') != raw:
            skipped.append((p, 'niente round-trip esatto: non toccato')); continue
        # verifica: riletto, nessun blob difettoso e stessa struttura
        chk = drm_write.read(new, 'le'); left = 0
        for s in chk.sections:
            if s.type != 9: continue
            _, _, ent = lib_entries(s.data)
            left += sum(1 for (j, h, bc) in ent.values() if len(bc) >= 8 and bc[:4] == b'\x00\x03\xff\xff' and constsplit.count_bad(bc))
        if left: skipped.append((p, 'blob difettosi residui dopo il fix')); continue
        changed.append((p, new))
    print('DRM da correggere: %d   blob unici corretti: %d   saltati: %d' % (len(changed), len(fixed), len(skipped)))
    for p, why in skipped: print('  SALTATO', os.path.relpath(p, mods), '-', why)
    if a.dry_run or not changed: print('(nessuna scrittura)'); return 0 if not skipped else 1
    for p, new in changed:
        rel = os.path.relpath(p, mods); b = os.path.join(bk, rel)
        if not os.path.exists(b): os.makedirs(os.path.dirname(b), exist_ok=True); shutil.copy2(p, b)
        try: os.chmod(p, 0o666)
        except OSError: pass
        tmp = p + '.psfix_tmp'; open(tmp, 'wb').write(new); os.replace(tmp, p)
    print('FATTO: %d DRM corretti. Backup in %s. Avvia un processo di gioco NUOVO.' % (len(changed), bk))
    return 0 if not skipped else 1


if __name__ == '__main__':
    sys.exit(main())
