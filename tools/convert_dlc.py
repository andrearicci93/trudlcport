"""Convert DLC Xbox DRMs (from pack10/pack11/pack1/pack2) to PC with the full DLC pipeline.
usage: tools/venv/bin/python -I tools/convert_dlc.py OUTDIR name1.drm name2.drm ..."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assemble_dlc as A, dlc_generic as DG, generic_store, drm_write as DW
from archive import Archive
from names import crc
R = '/path/to/Xenia-SteveRepack/Content/534307EC/00000002/'
PACKS = ['9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000', '600A12643FCDAC84003E6E0DBD0A1A8F7DAE9DD153/pack11.000',
         'E5AFB2B959A72C52120D73678AED11BD8752686753/pack1.000', '9FDDD06617D1016DE468ACF53AC663E8BA2AD41853/pack2.000']
def raw_dlc(name):
    for p in PACKS:
        a = Archive(R + p, 'be'); r = [x for x in a.find(crc('xenon-w\\' + name)) if x['spec'] == 0xffffffff]
        if r: return a.read(r[0]), p
    return None, None
if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    store = generic_store.load(); ids = DG.DlcIds(store, None)
    for name in sys.argv[2:]:
        raw, pk = raw_dlc(name)
        if raw is None: print(name, 'NOT FOUND'); continue
        t0 = time.time()
        data, rep = A.assemble(raw, ids, store, A.dlc_shader_src, wave='silence', pc_copy=True, template=True, material='dlc')
        open(os.path.join(out, name), 'wb').write(data)
        print(name, pk.split('/')[1], 'bytes', len(data), 'sec %.1f' % (time.time() - t0), 'routes', dict(rep['routes']), 'bad', rep['bad'],
              'missing_sh', rep['missing_shaders'], 'names', rep['names'], flush=True)
