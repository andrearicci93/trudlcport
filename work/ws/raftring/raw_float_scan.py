"""raw_float_scan.py - cerca parole di dati DLC NON convertite (PC == Xbox, byte non palindromi) che sono float plausibili letti BE e spazzatura letti LE.
Uso: python -I work/ws/raftring/raw_float_scan.py <setdir rel. work> [--out file.tsv]"""
import sys, os, struct, math, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import dtp_audit as DA, drm_write as DW, drm_reloc as R
sd = sys.argv[1]; out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
def plaus(v): return v == v and abs(v) != float('inf') and (v == 0 or 1e-3 <= abs(v) <= 1e7)
def junk(v): return v != v or abs(v) == float('inf') or (v != 0 and (abs(v) < 1e-20 or abs(v) > 1e20))
rows = []; nfiles = 0
for rel, path in sorted(DA.overlay([sd], None).items()):
    xs = DA.xsecs(rel)
    if xs is None: continue
    nfiles += 1
    try: D = DW.read(open(path, 'rb').read(), 'le')
    except Exception: continue
    for x, i in DA.section_pairs(xs, D):
        sec = D.sections[i]
        if x['type'] not in (7,) or len(sec.data) != len(x['data']): continue
        xd, pd = x['data'], sec.data
        fr = R.parse(x['reloc'], 'be'); slots = set(fr.pointer_offsets()) | set(fr.id_offsets())
        for o in range(0, len(xd) - 3, 4):
            if o in slots: continue
            xw, pw = xd[o:o + 4], pd[o:o + 4]
            if xw != pw or xw == xw[::-1] or xw == b'\0\0\0\0': continue
            vb = struct.unpack('>f', xw)[0]; vl = struct.unpack('<f', pw)[0]
            if plaus(vb) and vb != 0 and junk(vl): rows.append((rel, sec.id, o, vb, xw.hex()))
c = collections.Counter((r[0], r[1]) for r in rows)
print('file Xbox-sourced', nfiles, '| parole float non convertite:', len(rows), '| DTP coinvolti:', len(c), '| file:', len({r[0] for r in rows}))
for (f, i), n in c.most_common(40): print('%5d  %s  DTP %d' % (n, f, i))
if out:
    open(out, 'w').write('file\tdtp\toff\tvalore\thex\n' + '\n'.join('%s\t%d\t0x%x\t%g\t%s' % r for r in rows) + '\n')
