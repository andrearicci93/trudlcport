"""cmp.py - word-level DRM comparison. usage: cmp.py A_dir B_dir [relpath...]  -> per file: sections differing, words list"""
import sys, os, struct
sys.path.insert(0, os.path.expanduser('~/Downloads/tru-port/tools'))
import drm_write as DW
def load(p):
    raw = open(p, 'rb').read()
    return DW.read(raw, 'le')
def diff(pa, pb):
    A, B = load(pa), load(pb); out = []
    ka = [(s.type, s.id) for s in A.sections]; kb = [(s.type, s.id) for s in B.sections]
    if ka != kb: out.append(('SECTION_LIST', len(ka), len(kb)))
    for i, (a, b) in enumerate(zip(A.sections, B.sections)):
        if (a.type, a.id) != (b.type, b.id): continue
        if len(a.data) != len(b.data): out.append(('SIZE', i, a.type, a.id, len(a.data), len(b.data))); continue
        for o in range(0, len(a.data) - len(a.data) % 4, 4):
            if a.data[o:o+4] != b.data[o:o+4]: out.append(('W', i, a.type, a.id, o, a.data[o:o+4].hex(), b.data[o:o+4].hex()))
        if a.reloc != b.reloc: out.append(('RELOC', i, a.type, a.id))
        if (a.ver, a.flags, a.spec) != (b.ver, b.flags, b.spec): out.append(('META', i, a.type, a.id))
    return out
if __name__ == '__main__':
    da, db = sys.argv[1:3]
    for rel in sys.argv[3:]:
        d = diff(os.path.join(da, rel), os.path.join(db, rel))
        print(rel, len(d))
        for x in d[:60]: print('  ', x)
