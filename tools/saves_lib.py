#!/usr/bin/env python3
"""Libreria dei save del TRU (M0.4). Legge work/saves_lib/INDEX.tsv scritto da tools/vm_save_watcher.ps1.

  tools/venv/bin/python -I tools/saves_lib.py list [--level X] [--baseline B]
  tools/venv/bin/python -I tools/saves_lib.py pick <livello> [--baseline B] [--exe8 X] [--to NOME_SCENARIO]

INDEX.tsv (una riga per file copiato): time  livello  baseline  exe_md5  file  md5
time = yyyyMMdd_HHmmss; il set e' la cartella <time>_<livello>_<exe8>_<baseline>.
pick stampa il percorso Windows del set piu' recente per quel livello (da passare al runner).
--to NOME copia i file del set in work/baseline/saves/NOME/ (rifiuta se la cartella esiste gia').
"""
import argparse
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, 'work', 'saves_lib')
INDEX = os.path.join(LIB, 'INDEX.tsv')
WIN_LIB = r'Z:\tru-port\work\saves_lib'
HDR = ['time', 'livello', 'baseline', 'exe_md5', 'file', 'md5']


def read_index():
    if not os.path.isfile(INDEX):
        return []
    rows = []
    with open(INDEX, encoding='utf-8', errors='replace') as f:
        for line in f:
            p = line.rstrip('\r\n').split('\t')
            if len(p) < 6 or p[0] == 'time':
                continue
            rows.append(dict(zip(HDR, p[:6])))
    return rows


def set_name(r):
    return '%s_%s_%s_%s' % (r['time'], r['livello'], r['exe_md5'][:8], r['baseline'])


def sets(rows):
    """Raggruppa le righe per set (cartella), in ordine di tempo."""
    out = {}
    for r in rows:
        out.setdefault(set_name(r), {'row': r, 'files': []})['files'].append(r['file'])
    return sorted(out.items(), key=lambda kv: kv[1]['row']['time'])


def cmd_list(a):
    rows = read_index()
    rows = [r for r in rows if (not a.level or r['livello'] == a.level)
            and (not a.baseline or r['baseline'] == a.baseline)]
    if not rows:
        print('nessun save in %s' % INDEX)
        return 0
    print('%-15s  %-22s  %-16s  %-8s  %s' % ('time', 'livello', 'baseline', 'exe8', 'file (n)'))
    for name, s in sets(rows):
        r = s['row']
        print('%-15s  %-22s  %-16s  %-8s  %s (%d)' % (r['time'], r['livello'], r['baseline'],
                                                   r['exe_md5'][:8], ', '.join(s['files'][:4]), len(s['files'])))
    print('set: %d  righe: %d' % (len(sets(rows)), len(rows)))
    return 0


def cmd_pick(a):
    rows = [r for r in read_index() if r['livello'] == a.level]
    if a.baseline:
        rows = [r for r in rows if r['baseline'] == a.baseline]
    if a.exe8:
        rows = [r for r in rows if r['exe_md5'][:8] == a.exe8]
    if not rows:
        print('nessun set per livello %s' % a.level, file=sys.stderr)
        return 1
    name, s = sets(rows)[-1]
    local = os.path.join(LIB, name)
    if not os.path.isdir(local):
        print('attenzione: cartella assente sul Mac: %s' % local, file=sys.stderr)
    if a.to:
        dst = os.path.join(ROOT, 'work', 'baseline', 'saves', a.to)
        if os.path.exists(dst):
            print('rifiuto: esiste gia\' %s' % dst, file=sys.stderr)
            return 2
        shutil.copytree(local, dst)
        print('copiato in %s (%d file)' % (dst, len(s['files'])), file=sys.stderr)
    print(WIN_LIB + '\\' + name)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    pl = sub.add_parser('list')
    pl.add_argument('--level', default='')
    pl.add_argument('--baseline', default='')
    pl.set_defaults(fn=cmd_list)
    pp = sub.add_parser('pick')
    pp.add_argument('level')
    pp.add_argument('--baseline', default='')
    pp.add_argument('--exe8', default='')
    pp.add_argument('--to', default='', help='copia il set in work/baseline/saves/NOME')
    pp.set_defaults(fn=cmd_pick)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == '__main__':
    sys.exit(main())
