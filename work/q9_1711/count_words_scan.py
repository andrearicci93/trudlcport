"""Q9 (c), coordinator note on Q3 (docs Befund-Q3-Sonar-1711.md): are structural array COUNT words of converted DLC
scripts left at another value than the Xbox count (the g_pda sonar crash: 13 -> 12 by the DTP id map)? Read-only.

For every script section (type 8) of every DRM of TREE: the Xbox original of the same DRM (pack10 / pack11, by name),
the Xbox section whose converted id (dlc_generic.DlcIds) is this id; only pairs of equal size (the converter kept the
Xbox layout: routes convert / template); script_conv.Walk on the Xbox data lists the structural arrays; the PC word at
start - 4 must equal the Xbox count (vtable has no count word). Prints counts per DRM and every differing word
(offsets and values only), exit 1 when one differs.
Usage (repo root): ../bin/pyt -t 3600 work/q9_1711/count_words_scan.py TREE --pack pack10|pack11 [--out TSV]"""
import sys, os, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import drm_write as DW, drm_reloc as R, script_conv as SC
import dtp_word_classes as C


def main(argv):
    tree = argv[0]; pack = argv[argv.index('--pack') + 1]; out = argv[argv.index('--out') + 1] if '--out' in argv else None
    import dlc_generic as DG
    I = DG.DlcIds()
    xpaths = [C.DLC_ROOT + p for p in C.PACKS if p.endswith('/%s.000' % pack)]
    tot = collections.Counter(); bad = []
    for dp, dn, fn in os.walk(tree):
        dn.sort()
        for f in sorted(fn):
            if not f.lower().endswith('.drm') or 'truguard' in f.lower(): continue
            p = os.path.join(dp, f); rel = os.path.relpath(p, tree)
            pcs = [s for s in DW.read(open(p, 'rb').read(), 'le').sections if s.type == 8 and s.data]
            if not pcs: continue
            try: X = C.find(xpaths, 'be', 'xenon-w' + C.BS + rel.replace('/', C.BS))
            except Exception as e: X = None
            if not X: tot['drm without Xbox original'] += 1; continue
            xs = {}
            for s in X:
                if s['type'] == 8 and s['data']: xs.setdefault(I(8, s['id']), s)
            tot['drms'] += 1
            for s in pcs:
                x = xs.get(s.id)
                if x is None: tot['script without Xbox twin'] += 1; continue
                if len(x['data']) != len(s.data): tot['script other size (PC layout, skipped)'] += 1; continue
                tot['scripts compared'] += 1
                try: Wx = SC.Walk(x['data'], R.parse(x['reloc'], 'be'), 'be').run()
                except Exception as e: tot['xbox walk failed'] += 1; continue
                for nm, t, n, sz in Wx.arrays:
                    if nm == 'vtable' or t < 4 or t > len(s.data): continue
                    cur = struct.unpack_from('<I', s.data, t - 4)[0]
                    tot['count words'] += 1
                    if cur == n: continue
                    tot['count words DIFFERENT'] += 1
                    bad.append((rel, s.id, t - 4, nm, n, cur))
    for b in bad[:60]: print('DIFF %s script %d +0x%x %s: Xbox count %d, PC word %d' % b)
    print('tree %s (%s):' % (tree, pack), dict(tot))
    if out:
        with open(out, 'w', encoding='utf-8', newline='\n') as f:
            f.write('file\tscript\toffset\tarray\txbox_count\tpc_word\n')
            for b in bad: f.write('%s\t%d\t0x%x\t%s\t%d\t%d\n' % b)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
