#!/usr/bin/env python3
"""Check that your PC game folder matches the files this project was built against (sizes always, md5 with --md5).
usage: python3 scripts/check_inputs.py "C:/.../Tomb Raider Underworld" [--md5]
The game files are NOT part of this repository; docs/data/pc_game_files.tsv lists the expected size/md5."""
import sys, os, hashlib
here = os.path.dirname(os.path.abspath(__file__))
game = sys.argv[1]; full = '--md5' in sys.argv
bad = 0
for l in list(open(os.path.join(here, '..', 'docs', 'data', 'pc_game_files.tsv')))[1:]:
    name, size, md5 = l.rstrip('\n').split('\t'); p = os.path.join(game, name)
    if not os.path.exists(p): print('MISSING ', name); bad += 1; continue
    if os.path.getsize(p) != int(size): print('SIZE    ', name, os.path.getsize(p), '!=', size); bad += 1; continue
    if full:
        h = hashlib.md5()
        with open(p, 'rb') as f:
            for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
        if h.hexdigest() != md5: print('MD5     ', name); bad += 1; continue
    print('ok      ', name)
print('problems:', bad)
sys.exit(1 if bad else 0)
