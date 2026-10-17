#!/usr/bin/env python3
"""Filtra e raggruppa work/taps/<RunId>/tap.tsv offline, senza versare il log intero.

  tools/venv/bin/python -I tools/tap_view.py <RunId|percorso/tap.tsv> [--ret 0x454c62,0x455e2e]
        [--regex RE] [--seq-from N] [--seq-to N] [--top N] [--limit 50] [--width 160]

Senza --top: stampa le righe filtrate (al massimo --limit) e il totale.
Con --top N: raggruppa per (ret, testo) e stampa le N combinazioni piu' frequenti.
Le righe che iniziano con '#' (#ATTACH/#DETACH) e l'intestazione vengono saltate.
"""
import argparse
import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLS = ['seq', 't', 'chan', 'ret', 'tid', 'text']


def resolve(arg):
    if arg.endswith('.tsv') or os.sep in arg:
        return arg
    return os.path.join(ROOT, 'work', 'taps', arg, 'tap.tsv')


def rows(path):
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.rstrip('\r\n')
            if not line or line.startswith('#') or line.startswith('seq\t'):
                continue
            parts = line.split('\t', 5)
            parts += [''] * (6 - len(parts))
            yield dict(zip(COLS, parts))


def to_int(s, default=None):
    try:
        return int(s, 0)
    except (ValueError, TypeError):
        return default


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('run', help='RunId (work/taps/<RunId>/tap.tsv) oppure percorso di tap.tsv')
    ap.add_argument('--ret', default='', help='ret (hex o decimale), separati da virgola')
    ap.add_argument('--regex', default='', help='regex (re.search) sul testo')
    ap.add_argument('--seq-from', type=int, default=None)
    ap.add_argument('--seq-to', type=int, default=None)
    ap.add_argument('--top', type=int, default=0, help='N gruppi piu\' frequenti (ret, testo)')
    ap.add_argument('--limit', type=int, default=50, help='max righe stampate senza --top')
    ap.add_argument('--width', type=int, default=160, help='larghezza max del testo stampato')
    a = ap.parse_args()

    path = resolve(a.run)
    if not os.path.isfile(path):
        print('manca: %s' % path, file=sys.stderr)
        return 1
    rets = {to_int(x.strip()) for x in a.ret.split(',') if x.strip()} if a.ret else None
    rx = re.compile(a.regex) if a.regex else None

    total = 0
    matched = []
    groups = collections.Counter()
    persi = 0
    for r in rows(path):
        total += 1
        seq = to_int(r['seq'], -1)
        if r['text'].startswith('PERSI '):
            persi += to_int(r['text'][6:], 0) or 0
        if rets is not None and to_int(r['ret']) not in rets:
            continue
        if a.seq_from is not None and seq < a.seq_from:
            continue
        if a.seq_to is not None and seq > a.seq_to:
            continue
        if rx is not None and not rx.search(r['text']):
            continue
        if a.top:
            groups[(r['ret'], r['text'])] += 1
        else:
            matched.append(r)

    print('file: %s  righe: %d  PERSI totali: %d' % (path, total, persi))
    if a.top:
        print('%8s  %-12s  %s' % ('count', 'ret', 'testo'))
        for (ret, text), n in groups.most_common(a.top):
            print('%8d  %-12s  %s' % (n, ret, text[:a.width]))
        print('gruppi: %d  righe filtrate: %d' % (len(groups), sum(groups.values())))
        return 0

    print('%8s %10s %5s %-12s %s' % ('seq', 't', 'chan', 'ret', 'testo'))
    for r in matched[:a.limit]:
        print('%8s %10s %5s %-12s %s' % (r['seq'], r['t'], r['chan'], r['ret'], r['text'][:a.width]))
    print('filtrate: %d  mostrate: %d' % (len(matched), min(len(matched), a.limit)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
