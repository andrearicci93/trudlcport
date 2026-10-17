import sys; sys.path.insert(0,'/path/to/trudlcport/work/ws/chainshot')
import ld,dump,struct,drm_reloc as R
D=ld.pc()
def pcsec(id,typ=7,Dx=None):
    for s in (Dx or D).sections:
        if s.type==typ and s.id==id: return s
def diff(id,Dx=None,typ=7):
    x=dump.X(id,typ); s=pcsec(id,typ,Dx); xd=x['data']; pd=s.data
    rel=R.parse(x['reloc'],'be'); ptr=set(rel.pointer_offsets())|set(rel.id_offsets())|set(dict(rel.internal))
    out=[]
    for o in range(0,len(xd),4):
        xw=xd[o:o+4]; pw=pd[o:o+4]
        if o in ptr: k='ptr'
        elif xw==pw and xw!=xw[::-1]: k='raw'
        elif xw[::-1]==pw: k='s32'
        elif bytes([xw[1],xw[0],xw[3],xw[2]])==pw: k='s16'
        elif bytes([xw[0],xw[1],xw[3],xw[2]])==pw: k='b2s16'
        elif bytes([xw[1],xw[0],xw[2],xw[3]])==pw: k='s16b2'
        else: k='other'
        out.append((o,xw.hex(),pw.hex(),k))
    return out
