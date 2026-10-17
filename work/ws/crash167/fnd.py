import sys,glob,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm
def load(p):
    raw=drm.cdrm_decode(open(p,'rb').read(),'le')
    return drm.sections_with_data(raw,'le')
def allsecs(base='B6'):
    for p in sorted(glob.glob('/path/to/trudlcport/work/baseline/%s/mods/**/*.drm'%base,recursive=True)):
        try: h,secs=load(p)
        except Exception as e: continue
        for s in secs: yield p.split('mods/')[1],s
if __name__=='__main__':
    pat=bytes.fromhex(sys.argv[1])
    for f,s in allsecs():
        i=s['data'].find(pat)
        while i>=0:
            print(f,'sec',s['i'],'id',s['id'],'type',s['type'],hex(i),len(s['data'])); i=s['data'].find(pat,i+1)
