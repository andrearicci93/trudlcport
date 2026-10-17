import sys,struct,pickle,collections,json
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import drm_reloc as R, material_reslot as MR, tex_convert as T
L=MR.libs(); X,D,P,PM,DM=L['X'],L['D'],L['P'],L['PM'],L['DM']
mats,msh,mx2p=MR.dlc_tables()
tex=pickle.load(open('tex_table.pkl','rb'))
rows=[l.rstrip('\n').split('\t') for l in open('../rebuild/installed_effective.tsv')][1:]
seen={}
res=[]
for r in rows:
    if not r[0].endswith('.drm') or r[0]=='generalbank.drm': continue
    raw=cdrm_decode(open(r[4],'rb').read(),'le'); _,ps=sections_with_data(raw,'le')
    for s in ps:
        if s['type']!=10 or s['id'] in seen: continue
        m=mats.get(s['id'])
        if m is None or m['source']!='converted' or s['id'] not in DM: continue
        xd,xr=DM[s['id']]; pd=s['data']
        xt=struct.unpack_from('>4I',xd,0x28); pt=struct.unpack_from('<4I',pd,0x28)
        XL=lambda q: D.get(q,X.get(q)) if q else None
        xreg=MR.union_regs([XL(q) for q in xt[:3]],'x',[('x',q) for q in xt[:3]])
        preg=MR.union_regs([P.get(q) if q else None for q in pt[:3]],'p',[('p',q) for q in pt[:3]])
        xe=MR.tex_entries(xd,R.parse(xr,'be'),'>'); pe=MR.tex_entries(pd,R.parse(s['reloc'],'le'),'<')
        seen[s['id']]=r[0]
        if len(xe)!=len(pe): continue
        for (xo,xtid,xty,xslot),(po,ptid,pty,pslot) in zip(xe,pe):
            xn=xreg.get(xslot,set())-MR.ENGINE; pn=preg.get(pslot,set())-MR.ENGINE
            t=tex.get(ptid)
            res.append((s['id'],r[0],ptid,xty,xslot,pslot,sorted(xn)[:1],sorted(pn)[:1],bool(xn&pn) if xn and pn else None,t[1:5] if t and len(t)>3 else None))
pickle.dump(res,open('misbind.pkl','wb'))
c=collections.Counter(x[8] for x in res); print(c, len(seen))
bad=[x for x in res if x[8] is False]
mm=collections.defaultdict(list)
for x in bad: mm[x[0]].append(x)
print(len(mm),'materials with mismatch')
for k,v in sorted(mm.items()):
    if 'water_wheel' in v[0][1] or 'hall' in v[0][1]:
        for x in v: print(k,x[1][-40:],'tex',x[2],x[9],'xty',x[3],'slot',x[4],'->',x[5],x[6],'vs',x[7])
