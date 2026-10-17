import sys,os,glob,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm_write as DW
W='/path/to/trudlcport/work/baseline/'
def secs(p):
    D=DW.read(open(p,'rb').read(),'le'); return {(s.type,s.id):(s.data,s.reloc) for s in D.sections}
chg=[]
for p in sorted(glob.glob(W+'B10/mods/**/*.drm',recursive=True)):
    r=p[len(W+'B10/mods/'):]; q=W+'B8/mods/'+r
    if not os.path.exists(q): continue
    if open(p,'rb').read()==open(q,'rb').read(): continue
    a=secs(q); b=secs(p)
    dif=collections.Counter(k[0] for k in a if a[k]!=b.get(k))
    print(r,dict(dif), 'sec added/removed',set(a)^set(b))
