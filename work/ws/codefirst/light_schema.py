"""Schema DTP luce (0x14e4) derivato dall'oracolo del gioco base (coppie Xbox/PC), poi applicato alle DTP Xbox vergini del DLC.
Uso: tools/venv/bin/python -I work/ws/codefirst/light_schema.py"""
import sys,pickle,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools'); sys.path.insert(0,'/path/to/trudlcport/work/ws/codefirst')
import drm_reloc as R
T='/path/to/trudlcport'
pairs=pickle.load(open(T+'/work/generic/pairs.pkl','rb'))
def cls(xb,pb):
    if xb==pb: return 'raw'
    if xb==pb[::-1]: return 's32'
    return 'altro'
cnt=collections.defaultdict(collections.Counter); nd=0; slots_seen=set(); ex=collections.defaultdict(list)
for name,((xh,xs),(ph,ps)) in pairs.items():
    if len(xs)!=len(ps): continue
    for s,p in zip(xs,ps):
        if s['type']!=7 or s['data'] is None or p['data'] is None or len(s['data'])!=0x14e4 or len(p['data'])!=0x14e4: continue
        nd+=1; r=R.parse(s['reloc'],'be')
        ptr=set(r.pointer_offsets()); ids=set(r.id_offsets())
        for o in range(0,0x14e4,4):
            if o in ptr: cnt[o]['ptr']+=1; continue
            if o in ids: cnt[o]['id']+=1; continue
            c=cls(s['data'][o:o+4],p['data'][o:o+4]); 
            xb=s['data'][o:o+4]
            # parole palindrome/nulle: ambigue
            if xb==xb[::-1]: c='ambigua(palindroma)'
            cnt[o][c]+=1
            if c=='altro' and len(ex[o])<2: ex[o].append((name,s['id'],xb.hex(),p['data'][o:o+4].hex()))
print('DTP 0x14e4 nelle coppie base:',nd)
bad=[(o,dict(c)) for o,c in sorted(cnt.items()) if c.get('altro')]
print('offset con almeno un caso "altro" (ne' ,len(bad),'):')
for o,c in bad[:40]: print(f'  +{o:#06x} {c} es={ex[o][:1]}')
# riepilogo per classe dominante
dom=collections.Counter()
for o,c in cnt.items():
    k=[x for x,_ in c.most_common() if not x.startswith('ambigua')]
    dom[k[0] if k else 'solo-ambigua']+=1
print('classe dominante per parola:',dict(dom))
pickle.dump({o:dict(c) for o,c in cnt.items()},open(T+'/work/ws/codefirst/light_schema_counts.pkl','wb'))
