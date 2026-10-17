"""DIAGNOSTICO (non un fix): azzera indexCount delle draw entry dei terreni il cui materiale e' in --mats.
usage: hide_mats.py SRC.drm OUT.drm --mats 20268,21214 [--terrains 24024,24026]"""
import sys,struct,argparse
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm_write as DW, drm_reloc as R, terrain_convert as TC
ap=argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--mats',required=True); ap.add_argument('--terrains',default='')
a=ap.parse_args(); M=set(map(int,a.mats.split(','))); TT=set(map(int,a.terrains.split(','))) if a.terrains else None
D=DW.read(open(a.src,'rb').read(),'le'); assert D.write('le')==DW.cdrm_decode(open(a.src,'rb').read(),'le')
tot=0
for s in D.sections:
    if s.type!=12 or s.data[0x10:0x14] in (b'hseM',b'Mesh'): continue
    if TT is not None and s.id not in TT: continue
    d=bytearray(s.data); I=dict(R.parse(s.reloc,'le').internal)
    mo=I[0xC]; nm=struct.unpack_from('<I',d,mo)[0]; mats=struct.unpack_from('<%dI'%nm,d,mo+4)
    T=TC.parse(bytes(d),'<'); H=T['H']; z0=H+T['offZ']; n_h=0
    for k in range(T['nA']):
        t=struct.unpack_from('<I',d,z0+4*k)[0]
        if not t: continue
        L=H+t; n,seq=struct.unpack_from('<HH',d,L)
        for j in range(n):
            o=L+4+8*j; y,cnt,st=struct.unpack_from('<HHI',d,o)
            if y<T['nY'] and T['Y'][y][0]<nm and mats[T['Y'][y][0]] in M and cnt:
                struct.pack_into('<H',d,o+2,0); n_h+=1; tot+=cnt
    print('terrain',s.id,'entries hidden',n_h); s.data=bytes(d)
print('indices hidden',tot)
open(a.out,'wb').write(DW.cdrm_encode(D.write('le'),'le'))
