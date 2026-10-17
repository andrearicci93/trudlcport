"""Hook ablation: reconvert a list of pack10 DRMs with ONE wired fix switched off, to see which words that fix
is responsible for. Output: ablate_<HOOK>/<relpath>.drm.
usage: tools/venv/bin/python -I work/ws/rebuild/ablate.py HOOK LISTFILE   (LISTFILE: relpaths, one per line)
HOOK in: strings (dtp_audit.fix_strings), aidata, soundplex, animfx, reslot (material_dlc.RESLOT), model (model_fix)
"""
import sys, os, time
TOOLS = os.path.expanduser('~/Downloads/tru-port/tools'); sys.path.insert(0, TOOLS)
HERE = os.path.dirname(os.path.abspath(__file__))
import assemble_dlc as A, dlc_generic as DG, generic_store, material_dlc
from archive import Archive
from names import crc
sys.path.insert(0, HERE)
import convert_fresh as CF
hook, lst = sys.argv[1], sys.argv[2]
import dtp_audit, aidata_fix, animfx, soundplex_fix, soundplex_nodes
if hook == 'strings':
    dtp_audit.fix_strings = lambda xd, xr, pd, sec_type=7, kinds=None, preloc=None: (pd, [])
elif hook == 'aidata':
    aidata_fix.fix = lambda *a, **k: False
elif hook == 'soundplex':
    soundplex_fix.fix_section = lambda xd, xr, pd, *a, **k: (pd, [])
    soundplex_nodes.fix_section = lambda xd, xr, pd, *a, **k: (pd, [])
elif hook == 'animfx':
    animfx.fix = lambda *a, **k: False
elif hook == 'reslot':
    material_dlc.RESLOT = False
elif hook == 'analog':
    DG.analog_convert = lambda *a, **k: None
elif hook == 'template':
    pass   # handled by TEMPLATE env below
else:
    raise SystemExit('unknown hook ' + hook)
want = [l.strip() for l in open(lst) if l.strip()]
OUT = os.path.join(HERE, 'ablate_' + hook)
store = generic_store.load(); ids = DG.DlcIds(store, None)
arc = Archive(CF.PACK10, 'be')
names = CF.pack10_drms()
byrel = {n[len('xenon-w\\'):].replace('\\', '/'): n for n in names}
for rel in want:
    name = byrel.get(rel)
    if not name: print('not in pack10', rel, flush=True); continue
    recs = [r for r in arc.find(crc(name)) if r['spec'] == 0xffffffff]
    raw = arc.read(recs[0]); t0 = time.time()
    data, r = A.assemble(raw, ids, store, A.dlc_shader_src, wave='silence', pc_copy=True, template=(hook != 'template'), material='dlc')
    p = os.path.join(OUT, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(data)
    print(rel, 'sec %.1f' % (time.time() - t0), flush=True)
print('DONE', flush=True)
