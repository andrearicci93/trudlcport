import sys,os,glob,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import dtp_audit as A, drm_write as DW, drm_reloc as R, dtpid_sweep as DS
W='/path/to/trudlcport/work/'
# DLC1 B5
res=[]; per=collections.Counter()
d=W+'baseline/B5/mods'
for p in sorted(glob.glob(d+'/**/*.drm',recursive=True)):
    rel=os.path.relpath(p,d).replace('\\','/'); xs=A.xsecs(rel)
    if xs is None: continue
    D=DW.read(open(p,'rb').read(),'le')
    for x,i in A.section_pairs(xs,D):
        sec=D.sections[i]; xd=x['data']
        if len(sec.data)!=len(xd): continue
        for o in range(0,len(xd)-0x34,4):
            if xd[o:o+4]==b'\x00\x00\x04\x03':
                ptag=struct.unpack_from('<I',sec.data,o)[0]; xv=struct.unpack_from('>I',xd,o+0x30)[0]; pv=struct.unpack_from('<I',sec.data,o+0x30)[0]
                res.append((rel,x['type'],sec.id,hex(o),hex(ptag),hex(xv),hex(pv),struct.unpack_from('>IIII',xd,o)))
print('DLC1 BE 00000403 hits',len(res))
c=collections.Counter((r[1],r[4],r[5]==r[6]) for r in res); print(c)
for r in res:
    if r[4]!='0x403' or r[5]!=r[6]: print(r)
shapes=collections.Counter(r[7] for r in res); print(shapes.most_common(5))
# base
st,ids=DS.ctx(); n=0; ok=0; bad=[]
for (t,x),xb in st['xb_store'].items():
    xd=xb['data']
    if xd is None: continue
    p=ids.base[t].get(x) if t in ids.base else None
    pc=st['pc_store'].get((t,p)) if p is not None else None
    for o in range(0,len(xd)-0x34,4):
        if xd[o:o+4]==b'\x00\x00\x04\x03':
            n+=1
            if pc and len(pc['data'])==len(xd):
                ok+= struct.unpack_from('<I',pc['data'],o)==(0x403,)
                bad.append((t,x,hex(o),xd[o:o+0x34].hex()[:40],pc['data'][o:o+4].hex()))
print('base xb hits 00000403 (all types, 4-aligned)',n,'sample',bad[:10], 'ok',ok)
