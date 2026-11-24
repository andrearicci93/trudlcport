#!/usr/bin/env python3
"""playerblock_lock_fix.py - the fork's `playerblock` repair (K-5b) for the two documented words, without the Xbox base game.

The fork (tools/player_block_fix.py) re-derives every player-block word's byte order from five Xbox *base-game*
player pairs, which needs the Xbox base archives (layer1/2). Its documented result for the DLC 2 player object
(doppelganger_casual, DTP 20212; player block = target of the DTP's relocated pointer +0xc8, 0x1034 bytes):
  +0x294  four u8 (LT lock-on time = byte +0x294 -> 0 on PC: the lock never engages, no combat ring, no melee):
          wanted = the Xbox bytes in the same order ('same', proven by the PC readers 0x72170f / 0x75e15f / ...)
  +0x25c  a u16 pair converted as one u32 (halves exchanged): wanted = each u16 byte-swapped ('u16')
This tool applies exactly these two rules. For every installed DRM with a player block it reads the Xbox original from
the owner's pack (source name / spec from the kit manifest), and changes a word only when the PC word is another
byte order of the Xbox word and differs from the wanted word. Block location and DRM I/O are the fork's own code.

  python -I work/ws/gog/tools/playerblock_lock_fix.py scan MODS
  python -I work/ws/gog/tools/playerblock_lock_fix.py fix MODS OUTDIR     (writes changed DRMs only)
"""
import argparse, hashlib, json, os, sys

WS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(WS, 'tomb-raider-underworld-dlc-pc', 'tools'))
sys.path.insert(0, os.path.join(WS, 'release', 'B270'))
import player_block_fix as PB, drm_write as DW      # noqa: E402  (fork code, unchanged)
import install_dlc as K                              # noqa: E402  (upstream B270 installer: Archive, cdrm_decode)

RULES = {0x294: (0, 1, 2, 3), 0x25c: (1, 0, 3, 2)}   # 'same', 'u16'
MANIFEST = os.path.join(WS, 'release', 'B270', 'kit', 'kit', 'manifest.json')
PACKS = {'pack10.000': os.path.join(WS, 'input', 'xbox-dlc', '9CA70CF0EDA43654D158C2E37470D301DFA850E753', 'pack10.000'),
         'pack11.000': os.path.join(WS, 'input', 'xbox-dlc', '600A12643FCDAC84003E6E0DBD0A1A8F7DAE9DD153', 'pack11.000')}


def reorder(w, order): return bytes(w[i] for i in order)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['scan', 'fix']); ap.add_argument('mods'); ap.add_argument('out', nargs='?')
    a = ap.parse_args()
    man = {f['rel'].replace('\\', '/'): f for f in json.load(open(MANIFEST, encoding='utf-8'))['files']}
    arcs = {k: K.Archive(p, 'be') for k, p in PACKS.items()}
    total = 0
    for dp, dn, fn in os.walk(a.mods):
        for f in sorted(fn):
            if not f.lower().endswith('.drm'): continue
            p = os.path.join(dp, f); rel = os.path.relpath(p, a.mods).replace('\\', '/')
            raw = open(p, 'rb').read()
            PD = DW.read(raw, 'le'); bp = PB.words(PD, 'le')
            if bp is None: continue
            src = (man.get(rel) or {}).get('source') or {}
            if src.get('archive') not in arcs:
                print('%-50s player block, but no Xbox source in the manifest - left alone' % rel); continue
            xb = arcs[src['archive']].read(src['name'], src['spec'])
            XD = DW.read(K.cdrm_decode(xb, 'be'), 'be'); bx = PB.words(XD, 'be')
            if bx is None: print('%-50s no Xbox player block - left alone' % rel); continue
            kp, tp, pw, ps = bp; kx, tx, xw, xs = bx
            changes = []
            for o, order in RULES.items():
                if o in ps or o in xs: continue
                x, pc = xw[o // 4], pw[o // 4]; want = reorder(x, order)
                if pc == want: print('%-50s +0x%03x ok      %s' % (rel, o, pc.hex())); continue
                if sorted(pc) != sorted(x): print('%-50s +0x%03x OTHER   PC %s Xbox %s - left alone' % (rel, o, pc.hex(), x.hex())); continue
                print('%-50s +0x%03x FIX     PC %s -> %s (Xbox %s)' % (rel, o, pc.hex(), want.hex(), x.hex()))
                changes.append((o, pc, want))
            if not changes or a.cmd == 'scan': total += len(changes); continue
            s = PD.sections[kp]; b = bytearray(s.data)
            for o, pc, want in changes:
                q = tp + o; assert bytes(b[q:q + 4]) == pc; b[q:q + 4] = want
            s.data = bytes(b); new = PD.write('le')
            if raw[:4] == b'CDRM': new = DW.cdrm_encode(new, 'le')
            chk = DW.read(K.cdrm_decode(new, 'le'), 'le'); cw = PB.words(chk, 'le')[2]
            for o, pc, want in changes: assert cw[o // 4] == want, 're-read check failed'
            q = os.path.join(a.out, rel); os.makedirs(os.path.dirname(q), exist_ok=True)
            open(q, 'wb').write(new); total += len(changes)
            print('%-50s written (%d words) md5 %s' % (rel, len(changes), hashlib.md5(new).hexdigest()))
    print('%s: %d word(s) %s' % (a.cmd, total, 'to fix' if a.cmd == 'scan' else 'fixed'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
