import sys, os, json, collections, struct; sys.path.insert(0,'tools')
import dtp_keys as K, dtp_audit as A, drm_write as DW, drm_reloc as R
HERE='work/ws/rebuild'
eff={l.rstrip('\n').split('\t')[0]:l.rstrip('\n').split('\t')[4] for l in open(HERE+'/installed_effective.tsv') if not l.startswith('relpath')}
rules=K.load_rules(); LW=3
rows=[]; wins=collections.defaultdict(list)
for rel in sorted(eff):
    if not rel.endswith('.drm'): continue
    fp=os.path.join(HERE,'out_fresh',rel); vp=os.path.join(K.W,'vm_mods_expected',rel)
    if not (os.path.exists(fp) and os.path.exists(vp)): continue
    xs=A.xsecs(rel)
    if xs is None: continue
    di=DW.read(open(eff[rel],'rb').read(),'le'); df=DW.read(open(fp,'rb').read(),'le'); dv=DW.read(open(vp,'rb').read(),'le')
    if len(di.sections)!=len(df.sections) or len(di.sections)!=len(dv.sections): continue
    for x,i in A.section_pairs(xs,di):
        if x['type']!=7: continue
        a,b,v=di.sections[i].data,df.sections[i].data,dv.sections[i].data
        if a==b or len(a)!=len(b) or len(a)!=len(x['data']): continue
        xr=R.parse(x['reloc'],'be'); xd=x['data']
        ks=dict(K.keys_of(xd,xr)); own=K.owned_words(xd,xr)
        for o in range(0,len(a)-3,4):
            if a[o:o+4]==b[o:o+4]: continue
            xw=xd[o:o+4]
            r=dict(file=rel,id=di.sections[i].id,off=o,xbox=xw.hex(),inst=a[o:o+4].hex(),fresh=b[o:o+4].hex(),base=v[o:o+4].hex(),
                   inst_is_base=a[o:o+4]==v[o:o+4], owned=(own is None) or (o in own), slot=o not in ks)
            r['ci']=A.cls(xw,a[o:o+4]); r['cf']=A.cls(xw,b[o:o+4])
            if o in ks:
                for tn in ('T0','T1','T2'):
                    f,m,n,d=K.decide(ks[o],rules,K.FAMS,K.TIERS[tn])
                    if m: r['rule']=(f,m,n,d,tn); break
                if o-4*LW>=0 and o+4+4*LW<=len(xd):
                    w=(xd[o-4*LW:o],xd[o+4:o+4+4*LW])
                    if sum(1 for q in range(0,len(w[0]+w[1]),4) if (w[0]+w[1])[q:q+4]!=b'\0'*4)>=2:
                        r['win']=w; wins[(w,xw)].append(r)
            rows.append(r)
print('drift words',len(rows),'with window',sum(1 for r in rows if 'win' in r))
ev=collections.defaultdict(lambda:[0,K.ALL,set()])
for xx,p,xb,pc,xr in A.base_pairs():
    xd,pd=xb['data'],pc['data']
    for o in range(4*LW,len(xd)-4*LW-3,4):
        w=(xd[o-4*LW:o],xd[o+4:o+4+4*LW]); k=(w,xd[o:o+4])
        if k in wins:
            c=A.cls(xd[o:o+4],pd[o:o+4])
            if c!=K.ALL and c!=0: e=ev[k]; e[0]+=1; e[1]&=c; e[2].add(xx)
for r in rows:
    if 'win' in r:
        e=ev.get((r['win'],bytes.fromhex(r['xbox'])))
        if e and e[0]: r['loc']=(e[1],e[0],len(e[2]))
        del r['win']
json.dump(rows,open('work/ws/dtpkeys/drift_rows.json','w'))
