import sys,struct,pickle
sys.path.insert(0,'tools')
import drm_write as DW, drm_reloc as R, material_reslot as MR, material_convert as MC
L=MR.libs(); XM,PM,DM=L['XM'],L['PM'],L['DM']
mx2p=pickle.load(open('work/render/material_x2p.pkl','rb'))
D=DW.read(open('work/mods_current/dlc1_uo_bend_switches.drm','rb').read(),'le')
for s in D.sections:
    if s.type==10 and s.id==21210:
        d=bytes(s.data); rel=R.parse(s.reloc,'le'); P=dict(rel.internal).get(0x5C); n=struct.unpack_from('<I',d,0x58)[0]
        print('len',len(d),'params ptr',hex(P),'n',n,'end',hex(P+16*n),'trailing bytes after n vec4',len(d)-(P+16*n),'trailing after 11',len(d)-(P+16*11))
        # what follows
        print('after params:',d[P+16*n:P+16*n+16].hex(), 'internal ptrs >= end:',[ (hex(a),hex(b)) for a,b in rel.internal if b>=P])
# whole-section compare dlc 21210 xbox vs 4405 xbox
xd,xr=DM[21210]; bd,br=XM[4405]
print(len(xd),len(bd))
diff=[i for i in range(0,min(len(xd),len(bd)),4) if xd[i:i+4]!=bd[i:i+4]]
print('xbox word diffs 21210 vs 4405',[hex(i) for i in diff])
rx=R.parse(xr,'be'); rb=R.parse(br,'be')
print('reloc equal internal',rx.internal==rb.internal,'idref',rx.idref==rb.idref, rx.idref_a==rb.idref_a)
# PC 4767 vs 21210 pc: diff
pd,pr=PM[mx2p[4405]]; print('pc4767',len(pd))
