#!/usr/bin/env python3
"""Deriva una nuova baseline immutabile da un'esistente sostituendo file.
  python3 tools/baseline_derive.py --parent B1 --name B2 --note "testo" relpath=path/al/file [relpath=...]
Il manifest registra origine 'derived:<nome>' e l'eccezione/nota; l'id e' l'md5 del nuovo manifest.
"""
import argparse, hashlib, os, shutil, subprocess, sys
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); B = os.path.join(W, 'work', 'baseline')
def md5(p):
    h = hashlib.md5(); f = open(p, 'rb')
    for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()
ap = argparse.ArgumentParser(); ap.add_argument('--parent', required=True); ap.add_argument('--name', required=True)
ap.add_argument('--note', default=''); ap.add_argument('repl', nargs='+'); a = ap.parse_args()
src = os.path.join(B, a.parent); dst = os.path.join(B, a.name)
if os.path.exists(dst): sys.exit('esiste gia: ' + dst)
os.makedirs(dst); 
subprocess.run(['cp', '-cR', os.path.join(src, 'mods'), os.path.join(dst, 'mods')], check=True)
for d in ('saves', 'configs'): shutil.copytree(os.path.join(src, d), os.path.join(dst, d))
for n in ('env.txt', 'gamedir.tsv'): shutil.copy2(os.path.join(src, n), os.path.join(dst, n))
subprocess.run(['chmod', '-R', 'u+w', dst], check=True)
rows = [l.rstrip('\n').split('\t') for l in open(os.path.join(src, 'manifest.tsv'))]
hdr, rows = rows[0], rows[1:]; idx = {r[0].lower(): r for r in rows}
for r in a.repl:
    rel, path = r.split('=', 1); k = rel.lower()
    if k not in idx: sys.exit('non in baseline: ' + rel)
    t = os.path.join(dst, 'mods', idx[k][0].replace('/', os.sep)); os.remove(t)
    subprocess.run(['cp', '-c', path, t], check=True)
    idx[k][1] = str(os.path.getsize(t)); idx[k][2] = md5(t); idx[k][3] = 'derived:' + a.name
    idx[k][5] = (idx[k][5] + ' | ' if idx[k][5] else '') + a.name + ': ' + a.note
man = os.path.join(dst, 'manifest.tsv')
with open(man, 'w') as f:
    f.write('\t'.join(hdr) + '\n')
    for r in sorted(idx.values(), key=lambda r: r[0].lower()): f.write('\t'.join(r) + '\n')
bid = hashlib.md5(open(man, 'rb').read()).hexdigest()[:12]
open(os.path.join(dst, 'id.txt'), 'w').write(a.name + '-' + bid + '\n')
with open(os.path.join(dst, 'BASELINE.md'), 'w') as f:
    f.write('# Baseline %s-%s\n\nDerivata da %s (%s)\n\nNota: %s\n\nFile cambiati:\n' % (a.name, bid, a.parent, open(os.path.join(src, 'id.txt')).read().strip(), a.note))
    for r in a.repl: f.write('- ' + r.split('=')[0] + '\n')
    f.write('\nIl resto (eccezioni, difetti noti, salvataggi, config) e\' quello del genitore: vedi %s/BASELINE.md\n' % a.parent)
subprocess.run(['chmod', '-R', 'a-w', dst], check=True)
print(a.name + '-' + bid)
