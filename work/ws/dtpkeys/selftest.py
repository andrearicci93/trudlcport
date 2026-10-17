import sys, os, collections, pickle, json; sys.path.insert(0,'tools')
import dtp_keys as K, dtp_audit as A, drm_write as DW, drm_reloc as R
LW=3
d=pickle.load(open(K.RULES,'rb')); full=d['rules']; folds=d['folds']
T2=K.TIERS['T2']; T1=K.TIERS['T1']; SR=('S1','R')
# in-sample: fix_section (final gating) on real PC bytes of every base pair
ch=0; dt=0; n=0
for x,p,xb,pc,xr in A.base_pairs():
    n+=1
    nb,log=K.fix_section(xb['data'],xr,pc['data'],7,None,full,SR,T2)
    nb2,log2=K.fix_section(xb['data'],xr,pc['data'],7,None,full,K.FAMS,T1)
    ch+=len(log)+len(log2); dt+= bool(log or log2)
print('in-sample selftest on %d base pairs: words changed (S1+R T2) + (ALL T1) = %d, DTPs %d'%(n,ch,dt))
# held-out: flagged words (fold rules) for gating A = S1+R T2 ; gating B = ALL T1 (needs local confirm)
cov=0; flA=0; flB=[]; inf=0; wins={}
for x,p,xb,pc,xr in A.base_pairs():
    fo=K.fold(xb['src']); xd,pd=xb['data'],pc['data']; rl=folds[1-fo]
    for o,ks in K.keys_of(xd,xr):
        c=A.cls(xd[o:o+4],pd[o:o+4])
        if c==K.ALL or c==0: continue
        inf+=1
        f,m,nn,dd=K.decide(ks,rl,SR,T2)
        if m:
            cov+=1; flA+= not c&m
        f,m,nn,dd=K.decide(ks,rl,K.FAMS,T1)
        if m and not c&m and o-4*LW>=0 and o+4+4*LW<=len(xd):
            w=(xd[o-4*LW:o],xd[o+4:o+4+4*LW])
            if sum(1 for q in range(0,len(w[0]+w[1]),4) if (w[0]+w[1])[q:q+4]!=b'\0'*4)>=2:
                flB.append((fo,x,o,(w,xd[o:o+4]),c,m))
print('held-out A (S1+R,T2): informative %d covered %d flagged %d rate %.2e'%(inf,cov,flA,flA/cov))
need=collections.defaultdict(list)
for t in flB: need[t[3]].append(t)
ev=collections.defaultdict(lambda:[[0,K.ALL],[0,K.ALL]])
for x,p,xb,pc,xr in A.base_pairs():
    fo=K.fold(xb['src']); xd,pd=xb['data'],pc['data']
    for o in range(4*LW,len(xd)-4*LW-3,4):
        k=((xd[o-4*LW:o],xd[o+4:o+4+4*LW]),xd[o:o+4])
        if k in need:
            c=A.cls(xd[o:o+4],pd[o:o+4])
            if c!=K.ALL and c!=0: e=ev[k][fo]; e[0]+=1; e[1]&=c
conf=0; withloc=0
for fo,x,o,k,c,m in flB:
    e=ev[k][1-fo]
    if e[0]:
        withloc+=1
        if e[1] and not c&e[1]: conf+=1
print('held-out B (ALL,T1 flagged with usable window %d); of those local-evidence-confirmed flags (= false positives of the local branch): %d'%(withloc,conf))
# DLC1 covered words under gating A
eff={l.rstrip('\n').split('\t')[0]:l.rstrip('\n').split('\t')[4] for l in open('work/ws/rebuild/installed_effective.tsv') if not l.startswith('relpath')}
import dtpid_sweep as DS; _,ids=DS.ctx()
dc=0; dn=0
for rel,path in sorted(eff.items()):
    if not rel.endswith('.drm') or not os.path.exists(path): continue
    xs=A.xsecs(rel)
    if xs is None: continue
    D=DW.read(open(path,'rb').read(),'le')
    for x,i in A.section_pairs(xs,D):
        s=D.sections[i]
        if x['type']!=7 or len(s.data)!=len(x['data']) or A.base_content(x): continue
        xr=R.parse(x['reloc'],'be')
        if dict(xr.internal)!=dict(R.parse(s.reloc,'le').internal): continue
        dn+=1
        for o,ks in K.keys_of(x['data'],xr):
            c=A.cls(x['data'][o:o+4],s.data[o:o+4])
            if c==K.ALL or c==0: continue
            f,m,nn,dd=K.decide(ks,full,SR,T2)
            if m: dc+=1
print('DLC1 effective overlay: scanned DTPs %d, informative words covered by gating A: %d -> expected false flags at held-out rate: %.1f'%(dn,dc,dc*flA/cov))
