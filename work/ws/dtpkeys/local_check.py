import sys, json, collections; sys.path.insert(0,'tools')
import dtp_keys as K, dtp_audit as A, dtpid_sweep as DS, drm_reloc as R
tier=sys.argv[1]; LW=int(sys.argv[2]) if len(sys.argv)>2 else 3
fs=json.load(open('work/ws/dtpkeys/scan_%s.json'%tier))
st,ids=DS.ctx()
xcache={}
def xd_of(rel,sid):
    if rel not in xcache: xcache[rel]=A.xsecs(rel)
    for x in xcache[rel]:
        if x['type']==7 and x['data'] is not None and ids(7,x['id'])==sid: return x
want=collections.defaultdict(list)
for f in fs:
    x=xd_of(f['file'],f['id']); o=f['off']; d=x['data']
    if o-4*LW<0 or o+4+4*LW>len(d): f['win']=None; continue
    w=(d[o-4*LW:o],d[o+4:o+4+4*LW])
    if sum(1 for i in range(0,len(w[0]+w[1]),4) if (w[0]+w[1])[i:i+4]!=b'\0'*4)<2: f['win']=None; continue
    f['win']=w; want[w].append(f)
print('findings',len(fs),'with window',sum(1 for f in fs if f['win']))
ev=collections.defaultdict(lambda:[0,K.ALL])
for xx,p,xb,pc,xr in A.base_pairs():
    xd,pd=xb['data'],pc['data']
    for o in range(4*LW,len(xd)-4*LW-3,4):
        w=(xd[o-4*LW:o],xd[o+4:o+4+4*LW])
        if w in want:
            c=A.cls(xd[o:o+4],pd[o:o+4])
            # value must match too: key on xbox word
            k=(w,xd[o:o+4]); e=ev[k]; 
            if c not in (K.ALL,): e[0]+=1; e[1]&=c
res=collections.Counter(); ex=[]
for w,lst in want.items():
    for f in lst:
        e=ev.get((w,bytes.fromhex(f['xbox'])))
        if not e or e[0]==0: res['no_local']+=1; continue
        pcw=bytes.fromhex(f['pc']); xw=bytes.fromhex(f['xbox'])
        c=A.cls(xw,pcw)
        if e[1]==0: res['local_mixed']+=1
        elif c&e[1]: res['local_says_installed_ok']+=1; ex.append(f)
        else: res['local_confirms_flag']+=1
print(dict(res))
for f in ex[:15]: print(f['file'],f['id'],hex(f['off']),f['xbox'],f['pc'],f['want'],f['fam'],f['rule'])
