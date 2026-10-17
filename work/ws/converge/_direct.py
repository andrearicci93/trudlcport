"""direct word-level diff: fresh (out_fresh2 / out_post) vs rc package (installed_rc.tsv); split by base."""
import sys, os, collections, json
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm_write as DW
W='/path/to/trudlcport/work/'
eff={}
for l in open(W+'ws/rebuild/installed_rc.tsv'):
    f=l.rstrip('\n').split('\t')
    if f[0]!='relpath': eff[f[0]]=f[4]
def secs(p):
    return DW.read(open(p,'rb').read(),'le').sections
res={}
for label,fd in (('fresh2',W+'ws/rebuild/out_fresh2/'),('post',W+'ws/converge/out_post/')):
    cnt=collections.Counter(); per=collections.Counter(); rows=[]
    for rel,rc in sorted(eff.items()):
        if not rel.endswith('.drm') or not os.path.exists(fd+rel): continue
        A=secs(fd+rel); B=secs(rc)
        if len(A)!=len(B) or [(a.type,a.id) for a in A]!=[(b.type,b.id) for b in B]:
            cnt['layout_or_size_diff_files']+=1; per[rel+' (layout)']+=1; continue
        base=W+'vm_mods_expected/'+rel
        Bs=secs(base) if os.path.exists(base) else None
        for k,(a,b) in enumerate(zip(A,B)):
            if len(a.data)!=len(b.data): cnt['size']+=1; continue
            for q in range(0,len(a.data),4):
                fa=bytes(a.data[q:q+4]); fb=bytes(b.data[q:q+4])
                if fa==fb: continue
                cnt['words']+=1
                bv=None
                if Bs is not None and k<len(Bs) and (Bs[k].type,Bs[k].id)==(a.type,a.id) and len(Bs[k].data)==len(a.data):
                    bv=bytes(Bs[k].data[q:q+4])
                kind='rc==base(fresh-only change)' if bv==fb else ('rc!=base(rc layer change)' if bv is not None else 'no base section')
                cnt[kind]+=1; per[rel]+=1
                rows.append((rel,a.type,a.id,hex(q),fa.hex(),fb.hex(),kind))
    res[label]=(cnt,per,rows)
    print(label, dict(cnt)); print('  top files', per.most_common(12))
json.dump({k:v[2] for k,v in res.items()}, open(W+'ws/converge/_direct_rows.json','w'))
