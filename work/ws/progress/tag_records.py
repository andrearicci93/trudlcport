"""tag_records.py - record DTP con tag 0x400..0x40f ({tag, campi}): regola per (tag, offset) dalle coppie base (>=5 campioni, una permutazione), verifica sui DLC.
Uso: python -I tag_records.py <setdir rel. work> [--out cand.tsv]"""
import sys, os, struct, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import dtp_audit as DA, drm_write as DW, drm_reloc as R
TAGS = {struct.pack('>I', t): t for t in range(0x400, 0x410)}
REC = 0x30
st = collections.defaultdict(lambda: [0, DA.ALL]); nrec = collections.Counter()
for x, p, xb, pc, xr in DA.base_pairs():
    xd, pd = xb['data'], pc['data']; sl = set(xr.pointer_offsets()) | set(xr.id_offsets())
    for o in range(0, len(xd) - REC, 4):
        t = TAGS.get(xd[o:o + 4])
        if t is None or o in sl: continue
        nrec[t] += 1
        for k in range(4, REC, 4):
            if o + k in sl: continue
            c = DA.cls(xd[o + k:o + k + 4], pd[o + k:o + k + 4])
            if c in (0, DA.ALL): continue
            s = st[(t, k)]; s[0] += 1; s[1] &= c
rules = {key: s[1] for key, s in st.items() if s[0] >= 5 and bin(s[1]).count('1') == 1}
print('record base per tag:', {hex(t): n for t, n in sorted(nrec.items())})
print('regole (tag,off)->perm:', len(rules))
for key in sorted(rules)[:40]: print('  tag %#x +%#x %s (n=%d)' % (key[0], key[1], DA.NAMES[rules[key].bit_length() - 1], st[key][0]))
sd = sys.argv[1]; out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
cand = []; checked = 0
for rel, path in sorted(DA.overlay([sd], None).items()):
    xs = DA.xsecs(rel)
    if xs is None: continue
    try: D = DW.read(open(path, 'rb').read(), 'le')
    except Exception: continue
    for x, i in DA.section_pairs(xs, D):
        sec = D.sections[i]
        if x['type'] != 7 or len(sec.data) != len(x['data']): continue
        xd, pd = x['data'], sec.data; xr = R.parse(x['reloc'], 'be'); sl = set(xr.pointer_offsets()) | set(xr.id_offsets())
        for o in range(0, len(xd) - REC, 4):
            t = TAGS.get(xd[o:o + 4])
            if t is None or o in sl: continue
            for k in range(4, REC, 4):
                r = rules.get((t, k))
                if r is None or o + k in sl: continue
                checked += 1
                c = DA.cls(xd[o + k:o + k + 4], pd[o + k:o + k + 4])
                if c == 0 or (c & r): continue
                cand.append((rel, sec.id, o + k, xd[o + k:o + k + 4].hex(), pd[o + k:o + k + 4].hex(), DA.NAMES[r.bit_length() - 1], t))
print('parole di record controllate nei DLC:', checked, '| difetti:', len(cand))
for c in cand[:40]: print('  ', c[0], 'DTP', c[1], hex(c[2]), 'xbox', c[3], 'pc', c[4], '-> regola', c[5], 'tag', hex(c[6]))
if out: open(out, 'w').write('file\tdtp\toff\txbox\tpc\tregola\n' + '\n'.join('%s\t%d\t0x%x\t%s\t%s\t%s' % c[:6] for c in cand) + '\n')
