# Audit "nessun dato di gioco copiato" sulle patch bsdiff4 di un kit.
# Per ogni patch: byte del file finale che arrivano dal blocco EXTRA (= copiati alla lettera nella patch, non ricavati dalla sorgente
# dell'utente) e byte dal blocco DIFF (= sorgente + delta). Se --pc e' dato, controlla anche se i run EXTRA lunghi compaiono
# alla lettera in un file PC (cioe' la patch trasporta byte del gioco PC).
# uso: python -I patch_audit.py KIT_DIR [--top 30] [--json out.json]
import sys, os, json, bz2, struct, argparse, collections

def offtin(b):
    y = int.from_bytes(b[:7] + bytes([b[7] & 0x7f]), 'little')
    return -y if b[7] & 0x80 else y

def parse(p):
    d = open(p, 'rb').read()
    if d[:8] != b'BSDIFF40': raise ValueError('non bsdiff4: ' + p)
    lc, ld, nsz = offtin(d[8:16]), offtin(d[16:24]), offtin(d[24:32])
    ctrl = bz2.decompress(d[32:32 + lc]); diff = bz2.decompress(d[32 + lc:32 + lc + ld]); extra = bz2.decompress(d[32 + lc + ld:])
    tri = [(offtin(ctrl[i:i + 8]), offtin(ctrl[i + 8:i + 16]), offtin(ctrl[i + 16:i + 24])) for i in range(0, len(ctrl), 24)]
    return dict(new=nsz, diff_bytes=sum(t[0] for t in tri), extra_bytes=sum(t[1] for t in tri), patch=len(d),
                diff_nonzero=len(diff) - diff.count(0), extra=extra, tri=tri)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('kit'); ap.add_argument('--top', type=int, default=25); ap.add_argument('--json')
    a = ap.parse_args()
    man = json.load(open(os.path.join(a.kit, 'manifest.json')))
    rows = []; by = collections.defaultdict(lambda: [0, 0, 0, 0])
    ents = man['files'] + man.get('extra', []) + ([man['exe']] if man.get('exe') else [])
    auth = [e for e in ents if not e['patch'].endswith('.bsdiff')]
    if auth: print('file scritti dal port, copiati com\'e\' (non dati di gioco):', ', '.join('%s (%d B)' % (e['rel'], e['size']) for e in auth))
    for e in ents:
        if e in auth: continue
        r = parse(os.path.join(a.kit, e['patch'])); ext = os.path.splitext(e['rel'])[1].lower() or e['rel']
        lit = r['extra_bytes'] + r['diff_nonzero']          # byte "nuovi": copiati (extra) + delta non nulli (diff)
        rows.append(dict(rel=e['rel'], new=r['new'], extra=r['extra_bytes'], diff_nonzero=r['diff_nonzero'], patch=r['patch'],
                         extra_pct=100.0 * r['extra_bytes'] / max(1, r['new']), new_pct=100.0 * lit / max(1, r['new'])))
        b = by[ext]; b[0] += r['new']; b[1] += r['extra_bytes']; b[2] += r['diff_nonzero']; b[3] += 1
    T = sum(r['new'] for r in rows); X = sum(r['extra'] for r in rows); Z = sum(r['diff_nonzero'] for r in rows)
    print('kit %s  file %d  byte finali %d  da EXTRA (letterali) %d = %.1f%%  delta non nulli %d = %.1f%%' % (
        man.get('build'), len(rows), T, X, 100.0 * X / T, Z, 100.0 * Z / T))
    print('\nper estensione: n  MB_finali  %extra  %delta')
    for k, (n, x, z, c) in sorted(by.items(), key=lambda kv: -kv[1][0]):
        print('  %-8s %4d %9.1f %6.1f %6.1f' % (k, c, n / 1e6, 100.0 * x / max(1, n), 100.0 * z / max(1, n)))
    print('\npiu\' "letterali" (extra%%):')
    for r in sorted(rows, key=lambda r: -r['extra'])[:a.top]:
        print('  %6.1f%%  %10d  %s' % (r['extra_pct'], r['extra'], r['rel']))
    if a.json: json.dump(dict(total=T, extra=X, diff_nonzero=Z, rows=rows), open(a.json, 'w'), indent=1)

if __name__ == '__main__':
    main()
