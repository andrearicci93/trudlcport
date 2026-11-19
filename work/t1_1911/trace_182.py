"""T1 (b), read-only: where does the 182 in generalbank 8:6 +0x11b20 come from?

Part 1 (trace): re-runs the pairing + copy_tree of tools/script_init_from_pc.py exactly as kit chain step 6 did
(IN = steps/05_vtable.drm, REF = steps/01_menu/generalbank.drm, script 6, --xbox generalbank.drm) and records every
init node that contains an array COUNT word of IN's walk (count = the word before an array start): IN offset,
array, walk label, member key, PC node offset, value before / after. Output DRM to work/rebuild/t1_1911 (md5 printed,
compared with steps/06_init.drm when --expect is given).

Part 2 (labels): for every script of DRM, every array count word whose walk label is NOT ('count', ...) - the count
word was labelled by an earlier walk (member init block, generic data) that ran into it.

Usage (repo root):
  ../bin/pyt -t 900 work/t1_1911/trace_182.py trace IN REF OUT SID [--xbox NAME] [--expect DRM]
  ../bin/pyt -t 900 work/t1_1911/trace_182.py labels DRM [SID ...]
"""
import sys, os, struct, collections, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import drm_write as DW, drm_reloc as R, script_conv as SC
import script_init_from_pc as SIP


def counts(w):
    return {t - 4: nm for nm, t, n, sz in w.arrays if nm != 'vtable' and t >= 4}


def trace(argv):
    exp = None
    if '--expect' in argv: k = argv.index('--expect'); exp = argv[k + 1]; del argv[k:k + 2]
    src, ref, out, sid = argv[0], argv[1], argv[2], argv[3]
    D = DW.read(open(src, 'rb').read(), 'le')
    s = next(x for x in D.sections if x.type == 8 and x.id == int(sid))
    wa = SC.Walk(s.data, R.parse(s.reloc, 'le'), 'le').run()
    cin = counts(wa)
    hits = []
    orig = SIP.copy_tree

    def wrapped(d, wa_, ita, pd, wb, itb, a, b, st, seen, shapes):
        if (a, b) not in seen:
            na, nb = SIP.node(wa_, ita, a), SIP.node(wb, itb, b)
            if na and len(na) == len(nb):
                cpc = counts(wb)
                for oa, ob in zip(na, nb):
                    if oa in cin:
                        hits.append((oa, cin[oa], wa_.lab.get(oa), a, len(na), ob, cpc.get(ob),
                                     struct.unpack_from('<I', d, oa)[0], struct.unpack_from('<I', pd, ob)[0]))
        return orig(d, wa_, ita, pd, wb, itb, a, b, st, seen, shapes)
    SIP.copy_tree = wrapped
    SIP.main([src, ref, out, sid] + argv[4:])
    for h in hits:
        print('COUNT WORD IN INIT NODE: +0x%x (%s count), label %s; node +0x%x (%d words); PC word +0x%x (PC: %s); '
              'IN %d -> PC %d%s' % (h[0], h[1], h[2], h[3], h[4], h[5], ('%s count' % h[6]) if h[6] else 'no count',
                                   h[7], h[8], '  CHANGED' if h[7] != h[8] else ''))
    print('count words inside copied init nodes: %d (%d changed)' % (len(hits), sum(h[7] != h[8] for h in hits)))
    m = hashlib.md5(open(out, 'rb').read()).hexdigest()
    print('out md5', m)
    if exp:
        e = hashlib.md5(open(exp, 'rb').read()).hexdigest()
        print('expect md5', e, 'EQUAL' if e == m else 'DIFFERENT')
        return 0 if e == m else 1
    return 0


def labels(argv):
    path = argv[0]; want = {int(x) for x in argv[1:]}
    raw = open(path, 'rb').read()
    D = DW.read(raw, 'le')
    tot = collections.Counter()
    for s in D.sections:
        if s.type != 8 or not s.data or (want and s.id not in want): continue
        try: w = SC.Walk(s.data, R.parse(s.reloc, 'le'), 'le').run()
        except Exception: tot['walk failed'] += 1; continue
        tot['scripts'] += 1
        for o, nm in sorted(counts(w).items()):
            tot['count words'] += 1
            lab = w.lab.get(o)
            if lab is not None and lab[0] == 'count': continue
            tot['count words labelled %s' % (lab[0] if lab else None)] += 1
            print('script %5d +0x%05x %-8s count %8d  label %s' % (s.id, o, nm, struct.unpack_from('<I', s.data, o)[0], lab))
    print(path, dict(tot))
    return 0


if __name__ == '__main__':
    a = sys.argv[1:]
    sys.exit(trace(a[1:]) if a and a[0] == 'trace' else labels(a[1:]) if a and a[0] == 'labels' else print(__doc__))
