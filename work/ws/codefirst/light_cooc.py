"""Co-occorrenza dei campi della DTP luce 21217/20674 nelle 274 DTP 0x14e4 del gioco base PC (coppie)."""
import sys,pickle,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
T='/path/to/trudlcport'
pairs=pickle.load(open(T+'/work/generic/pairs.pkl','rb'))
rows=[]
for name,((xh,xs),(ph,ps)) in pairs.items():
    if len(xs)!=len(ps): continue
    for s,p in zip(xs,ps):
        if s['type']!=7 or p['data'] is None or len(p['data'])!=0x14e4: continue
        d=p['data']; u=lambda o:struct.unpack_from('<I',d,o)[0]
        rows.append(dict(name=name,id=p['id'],typ=u(0),f41c=d[0x41c],f824=d[0x824],t828=u(0x828),f14c4=d[0x14c4],f83c=d[0x83c],f144c=d[0x144c],f18=tuple(d[0x18:0x1c])))
print('DTP base PC 0x14e4:',len(rows))
dlc=dict(f41c=1,f824=1,t828='!=0',f14c4=1)
def has(r,**k): return all((r[a]!=0 if v=='!=0' else r[a]==v) for a,v in k.items())
print('type luce (word0):',collections.Counter(r['typ'] for r in rows))
print('+0x41c==1 :',sum(has(r,f41c=1) for r in rows))
print('+0x824==1 e +0x828!=0 :',sum(has(r,f824=1,t828='!=0') for r in rows))
print('+0x14c4==1 :',sum(has(r,f14c4=1) for r in rows))
print('+0x41c==1 e +0x824==1 e +0x828!=0 :',sum(has(r,f41c=1,f824=1,t828='!=0') for r in rows))
print('COMBINAZIONE DLC (41c=1,824=1,828!=0,14c4=1) :',sum(has(r,**dlc) for r in rows))
for r in rows:
    if r['f14c4']: print('  14c4!=0:',r['name'],r['id'],'typ',r['typ'],'41c',r['f41c'],'824',r['f824'],'828',hex(r['t828']))
print('tipo (word0) per i 73 con tex:',collections.Counter(r['typ'] for r in rows if r['t828']))
