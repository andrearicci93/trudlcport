import sys, io, contextlib, struct, hashlib
sys.path.insert(0,'/path/to/trudlcport/work/ws/contratti'); sys.path.insert(0,'/path/to/trudlcport/tools')
import contract as C, tex_convert as TC
t=C.read_tree('/path/to/trudlcport/work/ws/giro6/compose/mods')
W={20673,20676,23173,23329,20876,20264}; TX={6610,6611,6743,6744,6745,6752,6753,6754,255,121,119}
rows={}
for rel,d in sorted(t.items()):
    for s in d.sections:
        if (s.type==10 and s.id in W) or (s.type==5 and s.id in TX):
            k=(s.type,s.id); h=hashlib.md5(s.data).hexdigest()[:8]
            extra=''
            if s.type==5:
                try: hh=TC.parse_pc(s.data); extra=TC.pc_kind(hh['fmt'])+' %dx%d'%(hh['w'],hh['h'])
                except Exception as e: extra='?'
            rows.setdefault(k,[]).append((rel.split('/')[-1],h,extra,len(s.data)))
for k,v in sorted(rows.items()):
    hs={x[1] for x in v}
    print(k, 'VARIANTI' if len(hs)>1 else 'uguali', ' | '.join('%s:%s%s'%(a[:28],h,(' '+e) if e else '') for a,h,e,_ in v))
