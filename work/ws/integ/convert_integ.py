"""Reconvert every pack10 (DLC1, Beneath the Ashes) DRM from scratch with the CURRENT pipeline
(same calls as tools/convert_dlc.py: A.assemble(raw, ids, store, A.dlc_shader_src, wave='silence',
pc_copy=True, template=True, material='dlc')). Output: out_fresh/<relpath>.drm (relpath = mods-relative installed path).
Run: tools/venv/bin/python -I work/ws/rebuild/convert_fresh.py [--only substr] ; writes out_fresh/convert_report.tsv
"""
import sys, os, time, collections
TOOLS = os.path.expanduser('~/Downloads/tru-port/tools')
sys.path.insert(0, TOOLS)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), sys.argv[1])
import assemble_dlc as A, dlc_generic as DG, generic_store
from archive import Archive
from names import crc
PACK10 = os.path.expanduser('~/Downloads/Xenia-SteveRepack/Content/534307EC/00000002/9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000')
NAMES = os.path.expanduser('~/Downloads/tru-port/work/generic/dlc_names.txt')
def pack10_drms():
    seen = collections.OrderedDict()
    for line in open(NAMES, encoding='latin1'):
        f = line.split()
        if len(f) >= 6 and f[1] == 'pack10' and f[-1].endswith('.drm'):
            name = f[-1]
            seen.setdefault(name, f[0])
    return seen   # name (xenon-w\...) -> hash text
if __name__ == '__main__':
    only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
    os.makedirs(OUT, exist_ok=True)
    store = generic_store.load(); ids = DG.DlcIds(store, None)
    arc = Archive(PACK10, 'be')
    rep = open(os.path.join(OUT, 'convert_report.tsv'), 'w')
    rep.write('relpath\tstatus\tbytes\tsec\tbad\tmissing_sh\troutes\n')
    names = pack10_drms()
    print('pack10 unique DRM names', len(names), flush=True)
    for name in names:
        rel = name[len('xenon-w\\'):].replace('\\', '/')
        if only and only not in rel: continue
        recs = [r for r in arc.find(crc(name)) if r['spec'] == 0xffffffff]
        if not recs:
            rep.write('%s\tNOT_IN_PACK10\n' % rel); print(rel, 'NOT FOUND', flush=True); continue
        raw = arc.read(recs[0])
        t0 = time.time()
        try:
            data, r = A.assemble(raw, ids, store, A.dlc_shader_src, wave='silence', pc_copy=True, template=True, material='dlc')
        except Exception as e:
            rep.write('%s\tERROR %r\n' % (rel, e)); rep.flush(); print(rel, 'ERROR', repr(e), flush=True); continue
        p = os.path.join(OUT, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'wb').write(data)
        routes = ';'.join('%s:%s=%d' % (t, k, v) for (t, k), v in sorted(r['routes'].items(), key=str))
        rep.write('%s\tOK\t%d\t%.1f\t%d\t%d\t%s\n' % (rel, len(data), time.time() - t0, len(r['bad']), len(r['missing_shaders']), routes))
        rep.flush(); print(rel, 'bytes', len(data), 'sec %.1f' % (time.time() - t0), 'bad', len(r['bad']), 'missing_sh', len(r['missing_shaders']), flush=True)
    rep.close(); print('DONE', flush=True)
