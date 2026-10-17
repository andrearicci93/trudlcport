import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools');sys.path.insert(0,'/path/to/trudlcport/work/ws/crash167')
import fnd, soundplex_fix as S, cal2
rel='dlc_dungeon.drm'
xs=S.xsecs_of(rel); h,secs=fnd.load('/path/to/trudlcport/work/baseline/B6/mods/'+rel)
for k in (47,51):
    xd=xs[k]['data'];pd=secs[k]['data']
    c=collections.Counter();odd=[]
    for o in range(0,len(xd),4):
        xw=xd[o:o+4];pw=pd[o:o+4]
        cl=cal2.classify(xw,pw)
        if xw==b'\0\0\0\0' : cl='zero'
        c[cl]+=1
        if cl in('u16','other','raw'): odd.append((hex(o),cl,xw.hex(),pw.hex()))
    print(k,c); print(odd[:60])
