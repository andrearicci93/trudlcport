"""Which converted DLC DRMs need re-conversion for the 2026-10-09 fixes?  For every *.drm in the given dirs (first dir wins
per name), compares the CURRENT file with what the fixes would change:
  analog  : DLC-new DTPs that dlc_generic.analog_convert can rebuild (data differs from the current file)
  model   : model DTPs where dlc_generic.model_fix changes words
  rebase  : DLC-new / DLC-changed Scripts whose super chain grew on PC (dlc_generic.script_rebase changes words)
usage: dlc_fix_scan.py DIR [DIR..]  -> prints per file + the list of names needing re-conversion"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlc_generic as DG, generic_store, drm_write as DW, drm_reloc as R
from generic_store import norm_hash
from drm import cdrm_decode, sections_with_data
from convert_dlc import raw_dlc
st = generic_store.load(); ids = DG.DlcIds(st, None)
files = {}
for d in sys.argv[1:]:
    for r, _, fs in os.walk(d):
        for f in fs:
            if f.endswith('.drm'): files.setdefault(os.path.relpath(os.path.join(r, f), d), os.path.join(r, f))
need = []; tot = collections.Counter()
for rel_name, path in sorted(files.items()):
    raw, _ = raw_dlc(rel_name.replace('/', '\\'))
    if raw is None: raw, _ = raw_dlc(os.path.basename(rel_name))
    if raw is None: continue
    _, xs = sections_with_data(cdrm_decode(raw, 'be'), 'be')
    D = DW.read(open(path, 'rb').read(), 'le')
    ids.local = {}
    pool = collections.defaultdict(list)
    for o in D.sections: pool[o.type, o.id].append(o)
    hit = collections.Counter()
    for s in xs:
        t, x = s['type'], s['id']
        if t not in (7, 8): continue
        lst = pool.get((t, ids(t, x)))
        if not lst: hit['unmatched'] += 1; continue
        o = lst.pop(0)
        base = x in ids.base.get(t, {}) and norm_hash(s, xs, 'be') in st['xb_hash'].get((t, x), ())
        if t == 7 and x not in ids.base.get(7, {}):
            import analog_idcoin                      # same guard as the production pipeline (crash 0x5c019f): the scan must compare against what the converter now produces
            with analog_idcoin.guarded(): r = DG.analog_convert(s, xs, ids, st)
            if r is not None and r[0] != o.data: hit['analog'] += 1
        if t == 7 and s['data'][:4] == DG.MODEL_MAGIC and len(o.data) == len(s['data']):
            b = bytearray(o.data)
            if DG.model_fix(s['data'], R.parse(s['reloc'], 'be'), b): hit['model'] += 1
        if t == 8 and not base and len(s['data']) >= 0x54 and len(o.data) == len(s['data']) \
                and o.data[0x1c:0x1e] == s['data'][0x1c:0x1e][::-1]:    # still Xbox layout (idempotent; skips PC copies)
            sh = DG.script_layout_shift(int.from_bytes(s['data'][0x18:0x1c], 'big'), xs, st, ids)
            if sh is None: hit['rebase_unresolved'] += 1
            elif sh:
                b = bytearray(o.data)
                if DG.script_rebase(s['data'], R.parse(s['reloc'], 'be'), b, sh): hit['rebase'] += 1
    if hit:
        print(rel_name, dict(hit)); tot.update(hit)
        if set(hit) - {'rebase_unresolved', 'unmatched'}: need.append(rel_name)
print('TOTAL', dict(tot)); print('NEED', len(need)); print(' '.join(need))
