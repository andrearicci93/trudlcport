import sys,io,contextlib
sys.path.insert(0,'/path/to/trudlcport/work/ws/codefirst')
with contextlib.redirect_stdout(io.StringIO()):
    import hall_diag as H
for a in sys.argv[1:]:
    kind,tid=a.split(':'); tid=int(tid)
    if kind=='x':
        h,src=H.xtex(tid); print('Xbox tex',tid,src,{k:h[k] for k in h if k!='data'} if h else None)
    else:
        h,src=H.ptex(tid); print('PC tex',tid,src,{k:h[k] for k in h if k!='data'} if h else None)
