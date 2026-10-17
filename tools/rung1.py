"""Rung 1: base-game round trip. Convert an Xbox base DRM with the real converters (no pc_copy/template) and diff against the real PC DRM."""
import sys, os, collections, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assemble_dlc as A, drm_write as DW, dlc_generic as DG, generic_store
from archive import Archive
from names import crc
B = '/path/to/'
def raw_xbox(name):
    for f in ('layer1.000', 'layer2.000'):
        a = Archive(B + 'TombRaiderUnderworld_Patched/' + f, 'be'); r = a.find(crc('xenon-w\\' + name))
        if r: return a.read(r[0])
def raw_pc(name):
    a = Archive(B + 'tru-port/pc/bigfile.000', 'le'); return a.read(a.find(crc('pc-w\\' + name))[0])
if __name__ == '__main__':
    name = sys.argv[1]
    store = generic_store.load(); ids = DG.DlcIds(store, None)
    P = DW.read(raw_pc(name), 'le')
    psh = {s.id: dict(data=s.data, reloc=s.reloc, ver=s.ver, flags=s.flags, spec=s.spec) for s in P.sections if s.type == 9}
    out, rep = A.assemble(raw_xbox(name), ids, store, psh.get, pc_copy=False, template=False, material='generic')
    print('routes', dict(rep['routes'])); print('bad', rep['bad']); print('shaders need', rep['need_shaders'], 'missing', rep['missing_shaders'], 'removed', rep['removed'], 'nsec', rep['nsec'], 'pc nsec', len(P.sections))
    O = DW.read(out, 'le')
    pm = {(s.type, s.id): s for s in P.sections}
    st = collections.Counter()
    for s in O.sections:
        q = pm.get((s.type, s.id))
        if q is None: st[(s.type, 'no pc counterpart')] += 1; continue
        st[(s.type, 'data exact' if q.data == s.data else 'data differs' if len(q.data) == len(s.data) else 'size differs')] += 1
        st[(s.type, 'reloc exact' if q.reloc == s.reloc else 'reloc differs')] += 1
    for k, v in sorted(st.items()): print(k, v)
    print('pc sections not produced', [(t, i) for (t, i) in pm if (t, i) not in {(s.type, s.id) for s in O.sections}][:10])
    open('/path/to/trudlcport/work/rung1_%s' % name, 'wb').write(out)
