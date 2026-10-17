import sys,os,glob
sys.path.insert(0,'/path/to/trudlcport/tools')
import soundplex_fix as S
pat=bytes.fromhex(sys.argv[1])
names=[]
for p in sorted(glob.glob('/path/to/trudlcport/work/baseline/B6/mods/**/*.drm',recursive=True)):
    names.append(p.split('mods/')[1])
for n in names:
    if 'dlc_' not in n: continue
    try: xs=S.xsecs_of(n)
    except Exception as e: continue
    if not xs: continue
    for s in xs:
        d=s['data']
        if d is None: continue
        i=d.find(pat)
        while i>=0:
            print(n,'type',s['type'],'id',s['id'],hex(i),len(d)); i=d.find(pat,i+1)
