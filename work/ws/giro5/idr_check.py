import sys, io, contextlib
sys.path.insert(0, '/path/to/trudlcport/tools')
with contextlib.redirect_stdout(io.StringIO()):
    import dtpid_sweep as DS
    st, ids = DS.ctx()
b = ids.base.get(7, {})
print('base Xbox DTP 1039 ->', b.get(1039), '| inversa PC 1174 <- ', [k for k, v in b.items() if v == 1174], '| PC 3634 <-', [k for k, v in b.items() if v == 3634])
print('ids(7,1039) =', ids(7, 1039))
for k in (1039,):
    x = st['xb_store'].get((7, k)); print('Xbox store (7,%d):' % k, None if x is None else (len(x['data']), x['data'][:32].hex()))
for k in (1174, 3634):
    p = st['pc_store'].get((7, k)); print('PC store (7,%d):' % k, None if p is None else (len(p['data']), p['data'][:32].hex()))
