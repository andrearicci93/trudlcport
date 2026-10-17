import sys,struct,pickle,collections
sys.path.insert(0,'tools')
import material_reslot as MR
L=MR.libs(); XM,PM,DM=L['XM'],L['PM'],L['DM']
mx2p=pickle.load(open('work/render/material_x2p.pkl','rb'))
mats,msh,_=MR.dlc_tables()
idx=collections.defaultdict(list)
for xm,(d,r) in XM.items(): idx[(d,r)].append(xm)
tw=0; diffs=[]
for mid,m in sorted(mats.items()):
    if m['source']!='converted': continue
    k=DM[mid]
    if k in idx:
        tw+=1
        # PC twin
        pcs=[PM[mx2p[x]] for x in idx[k] if mx2p.get(x) in PM]
        if not pcs: continue
        pd,pr=m['data'],m['reloc']
        same=any(pd==a and pr==b for a,b in pcs)
        # compare ignoring texture slot bytes? report raw
        if not same:
            d0=pcs[0][0]
            diffs.append((mid,len(pd),len(d0),[hex(i) for i in range(0,min(len(pd),len(d0)),4) if pd[i:i+4]!=d0[i:i+4]][:6]))
print('converted with byte-identical Xbox base twin',tw,'differ from twin PC',len(diffs))
for x in diffs[:40]: print(x)
