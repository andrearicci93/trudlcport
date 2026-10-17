"""Oracolo base: MaterialParams PC == conversione endian pura dei MaterialParams Xbox? (coppie material_x2p, gioco base)"""
import sys,os,csv,struct,collections,pickle
S4='/path/to/trudlcport/work/ws/shader4'; sys.path.insert(0,S4)
from f9_common import *
import f9_common
L=libs(); XM,PM=L['XM'],L['PM']
mx2p=pickle.load(open('/path/to/trudlcport/work/render/material_x2p.pkl','rb'))
lit={int(r['id_xbox']) for r in csv.DictReader(open(S4+'/illuminati.tsv'),delimiter='\t')}
st=collections.defaultdict(collections.Counter); rows_eq=collections.defaultdict(list)
for mid,(d,r) in XM.items():
    mp=mx2p.get(mid)
    if mp not in PM: continue
    pd,pr=PM[mp]
    try: XP=f9_common._params(f9_common._Sec(d,r),'be'); PP=f9_common._params(f9_common._Sec(pd,pr),'le')
    except Exception: continue
    xl=struct.unpack_from('>4I',d,0x28)[2]; k='illuminato' if xl in lit else 'non-illuminato'
    same_n=len(XP)==len(PP)
    eq=same_n and all(abs(a-b)<1e-6 for xr,pr_ in zip(XP,PP) for a,b in zip(xr,pr_))
    # uguale a meno di traslazione di righe?
    shift=None
    if not eq:
        for sh in (-2,-1,1,2):
            if all(abs(XP[i][c]-PP[i+sh][c])<1e-6 for i in range(len(XP)) if 0<=i+sh<len(PP) for c in range(4)) and sum(1 for i in range(len(XP)) if 0<=i+sh<len(PP))>0: shift=sh;break
    st[k]['n']+=1; st[k]['n_righe_uguali' if same_n else 'n_righe_diverse']+=1
    st[k]['params_identici']+=eq; st[k]['traslazione_righe_%s'%shift]+=(shift is not None)
for k,v in st.items(): print(k,dict(v))

# per famiglia di donatori (xs,pd) usati da f12: ponte = tutti i materiali base con quella coppia di lib
import json
V0=json.load(open('/path/to/trudlcport/work/ws/codefirst/out_regimeA/V0.json'))
fam=collections.defaultdict(list)
for mid,r in V0.items():
    if r.get('donor'): fam[tuple(r['donor'])].append((int(mid),r['status'],r['why']))
print('\nfamiglie donatore (xs,pd): materiali DLC, stato; ponte base: n materiali, params identici, righe uguali')
tot=collections.Counter()
for (xs,pd),ms_ in sorted(fam.items()):
    br=material_pairs(xs,pd)
    ident=sum(1 for _,_,XP,PP in br if len(XP)==len(PP) and all(abs(a-b)<1e-6 for x,p in zip(XP,PP) for a,b in zip(x,p)))
    rows_eq=sum(1 for _,_,XP,PP in br if len(XP)==len(PP))
    ok=sum(1 for m in ms_ if m[1]=='costruito'); ko=len(ms_)-ok
    cls='ok' if ko==0 else 'rifiuti'
    tot[cls,'ponti']+=len(br); tot[cls,'identici']+=ident
    print(f' ({xs},{pd}) DLC ok={ok} rifiuti={ko} | ponte n={len(br)} identici={ident} stessa_lunghezza={rows_eq}')
print({k:v for k,v in tot.items()})
