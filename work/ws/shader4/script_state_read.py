"""Legge le fotografie di vm_script_state.ps1 e mostra i membri degli script (offset, valore, NULL/ptr) e le differenze tra due fotografie.
uso: python script_state_read.py work/live/script_state_prima.json [work/live/script_state_dopo.json]"""
import sys,json,struct
pat=json.load(open(__file__.rsplit('/',1)[0]+'/script_state_patterns.json'))
def load(p):
    d=json.load(open(p,encoding='utf-8-sig')); out={}
    for s in d['scripts']:
        for t in (s['types'] if isinstance(s['types'],list) else [s['types']]):
            objs=t['objects'] if isinstance(t['objects'],list) else [t['objects']]
            for o in objs: out[(s['script'],o['obj'])]=(o['inst'],bytes.fromhex(o['hex']))
    return d,out
d1,a=load(sys.argv[1]); print(sys.argv[1],'pid',d1['pid'],d1['time'],'oggetti',len(a))
b=None
if len(sys.argv)>2: d2,b=load(sys.argv[2]); print(sys.argv[2],'pid',d2['pid'],d2['time'],'oggetti',len(b))
for (sid,obj),(inst,data) in sorted(a.items()):
    print(f'\nscript {sid} oggetto 0x{obj:x} istanza 0x{inst:x} ({len(data)} byte)')
    for m in pat[str(sid)]['members']:
        o=m['off']; v=struct.unpack_from('<I',data,o)[0]
        line=f"  +0x{o:02x} tipo {m['tag']:2d} sym {m['sym']:5d}  {v:08x} {'NULL' if v==0 else ''}"
        if b is not None and (sid,obj) in b:
            w=struct.unpack_from('<I',b[(sid,obj)][1],o)[0]
            if w!=v: line+=f'   ->  {w:08x} {"NULL" if w==0 else ""}   CAMBIATO'
        print(line)
