"""Convert several BASE-game Xbox DRMs (by name) with the real converters (no pc_copy/template) into mods-ready PC files.
usage: tools/venv/bin/python -I tools/convert_many.py OUTDIR name1.drm name2.drm ... [--pccopy] [--no-reauthored]
  --no-reauthored: also convert the base Scripts/DTPs that PC re-authored (default: take them from PC, see NOTES)"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assemble_dlc as A, drm_write as DW, dlc_generic as DG, generic_store
from rung1 import raw_xbox, raw_pc
args = [a for a in sys.argv[1:] if not a.startswith('--')]; PCCOPY = '--pccopy' in sys.argv; NOREAUTH = '--no-reauthored' in sys.argv
out = args[0]; os.makedirs(out, exist_ok=True)
t0 = time.time(); store = generic_store.load(); ids = DG.DlcIds(store, None)
print('loaded', time.time() - t0, flush=True)
for name in args[1:]:
    P = DW.read(raw_pc(name), 'le')
    psh = {s.id: dict(data=s.data, reloc=s.reloc, ver=s.ver, flags=s.flags, spec=s.spec) for s in P.sections if s.type == 9}
    data, rep = A.assemble(raw_xbox(name), ids, store, psh.get, pc_copy=PCCOPY, template=PCCOPY, material='generic',
                          reauthored=not NOREAUTH)
    open(os.path.join(out, name), 'wb').write(data)
    print(name, 'bytes', len(data), 'routes', dict(rep['routes']), 'bad', rep['bad'], 'missing_sh', rep['missing_shaders'], flush=True)
