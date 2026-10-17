"""Controllo inverso degli slot texture dei materiali (tipo 10).

FUN_00505a90 (0x505ad4..0x505b07) legge per ogni record dell'array puntato da data+0x54 (passo 16 B, primi byte data+0x51
record; secondo blocco fino a byte data+0x52) il puntatore [rec+0] e lo passa a FUN_005076e0, che lo dereferenzia se != 0.
Quindi ogni [rec+0] non nullo DEVE essere un campo rilocato (internal / external / idref): altrimenti e' un puntatore spazzatura.
La struttura e' cercata come: offset p con puntatore interno, base = p - 0x54.

Uso: tools/venv/bin/python -I work/crash/B84_r6025/slot_cover_check.py (BASELINE | --base N)
Exit 1 se ci sono voci non nulle non rilocate.
"""
import sys, os, struct, collections
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'tools')))
import drm, drm_reloc as R


def scan_section(d, reloc):
    r = R.parse(reloc, 'le')
    intern = dict(r.internal)
    covered = set(intern) | {s for _, s, _ in r.external} | {o for _, o in r.idref} | {o for _, o in r.idref_a}
    out = []
    for p, tgt in intern.items():
        base = p - 0x54
        if base < 0 or base + 0x53 > len(d):
            continue
        n1, n2 = d[base + 0x51], d[base + 0x52]
        n = max(n1, n2)
        if n == 0 or tgt + 16 * n > len(d):
            continue
        for k in range(n):
            e = tgt + 16 * k
            v = struct.unpack_from('<I', d, e)[0]
            if v and e not in covered:
                out.append((base, k, n1, n2, e, v))
    return out


def scan_raw(raw):
    secs = drm.sections_with_data(drm.cdrm_decode(raw, 'le'), 'le')[1]
    res, nmat = [], 0
    for s in secs:
        if s['type'] != 10 or not s['data'] or not s['reloc']:
            continue
        nmat += 1
        for x in scan_section(s['data'], s['reloc']):
            res.append((s['id'],) + x)
    return nmat, res


def main():
    viol = collections.Counter(); ex = []; nm = 0
    if sys.argv[1] == '--base':
        from archive import Archive
        lim = int(sys.argv[2]); A = Archive(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'pc', 'bigfile.000'), 'le'); k = 0
        for r in A.idx:
            try: d = A.read(r)
            except Exception: continue
            if d[:4] != b'CDRM': continue
            try: n, res = scan_raw(d)
            except Exception: continue
            k += 1; nm += n
            for x in res:
                viol['base'] += 1
                if len(ex) < 12: ex.append((hex(r['hash']),) + x)
            if k >= lim: break
        label = 'base %d DRM' % k
    else:
        B = sys.argv[1]; M = os.path.join(os.path.dirname(__file__), '..', '..', 'baseline', B, 'mods')
        for root, _, fs in os.walk(M):
            for n in fs:
                if not n.endswith('.drm'): continue
                p = os.path.join(root, n)
                try: c, res = scan_raw(open(p, 'rb').read())
                except Exception: continue
                nm += c
                for x in res:
                    viol[os.path.relpath(p, M)] += 1
                    if len(ex) < 40: ex.append((os.path.relpath(p, M),) + x)
        label = B
    print('%s: materiali %d, voci slot non nulle NON rilocate: %d' % (label, nm, sum(viol.values())))
    for k, v in viol.most_common(20): print('  %-60s %d' % (k, v))
    for x in ex: print('   ', x[0], 'mat', x[1], 'base %#x rec %d n51=%d n52=%d off %#x val %#010x' % x[2:])
    return 1 if viol else 0


if __name__ == '__main__':
    sys.exit(main())
