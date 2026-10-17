"""Estrae le DTP luce (0x14e4) 21217/20674: Xbox vergine (BE) vs PC baseline B86 (LE). Uso: python -I light_dtp.py"""
import sys,struct,glob,os
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, parse_drm, sections_with_data
from archive import Archive
R='/path/to/trudlcport/'
XB='/path/to/Xenia-SteveRepack/Content/534307EC/00000002/9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000'
def xbox(i,sid):
    a=Archive(XB,'be',0x7FF00000); raw=cdrm_decode(a.read(a.idx[i]),'be')
    h,secs=sections_with_data(raw,'be'); return [s for s in secs if s['type']==7 and s['id']==sid][0]
def pc(sid):
    out=[]
    for f in sorted(glob.glob(R+'work/baseline/B86_contratti/mods/*.drm')):
        raw=open(f,'rb').read()
        try: raw=cdrm_decode(raw,'le'); h,secs=sections_with_data(raw,'le')
        except Exception: continue
        for s in secs:
            if s['type']==7 and s['id']==sid: out.append((os.path.basename(f),s))
    return out
if __name__=='__main__':
    for sid,i in ((21217,56),(20674,215)):
        x=xbox(i,sid); p=pc(sid)
        print('== DTP',sid,'xbox size',x['size'],'nreloc',x['nreloc'],'; PC copie:',[(n,s['size'],s['nreloc']) for n,s in p][:4])

def cmp(sid,i):
    x=xbox(i,sid); ps=pc(sid)
    xd=x['data']; 
    xr=struct.unpack('>%dI'%(len(x['reloc'])//4),x['reloc']) if x['reloc'] else ()
    for name,p in ps:
        pd=p['data']; diffs=[]
        for o in range(0,len(xd),4):
            xb=struct.unpack_from('>I',xd,o)[0]; pl=struct.unpack_from('<I',pd,o)[0]
            if xb!=pl: diffs.append((o,xb,pl))
        print(f'-- {sid} {name}: parole diverse (BE xbox vs LE pc) = {len(diffs)}; reloc xbox={len(x["reloc"])}B pc={len(p["reloc"])}B')
        for o,xb,pl in diffs[:60]: print(f'   +{o:#06x} (X+{o+0x42c:#06x}) xbox={xb:#010x} pc={pl:#010x}')
    # campi chiave
    d=ps[0][1]['data']
    print(f'   PC campi: type@0={struct.unpack_from("<I",d,0)[0]:#x} @4={struct.unpack_from("<I",d,4)[0]:#x} @8={struct.unpack_from("<I",d,8)[0]:#x} @c={struct.unpack_from("<I",d,0xc)[0]:#x} @10={struct.unpack_from("<I",d,0x10)[0]:#x}  flag@0x824={d[0x824]:#x} (u32 @0x824={struct.unpack_from("<I",d,0x824)[0]:#x}) tex@0x828={struct.unpack_from("<I",d,0x828)[0]:#x}')
    print(f'   XBX campi: type@0={struct.unpack_from(">I",xd,0)[0]:#x} @4={struct.unpack_from(">I",xd,4)[0]:#x} @8={struct.unpack_from(">I",xd,8)[0]:#x} @c={struct.unpack_from(">I",xd,0xc)[0]:#x} @10={struct.unpack_from(">I",xd,0x10)[0]:#x} flag@0x824={xd[0x824]:#x} (u32 BE @0x824={struct.unpack_from(">I",xd,0x824)[0]:#x}) tex@0x828={struct.unpack_from(">I",xd,0x828)[0]:#x}')
    print('   reloc xbox offsets(words):',[hex(v) for v in xr][:30])
    return x,ps
if __name__=='__main__':
    for sid,i in ((21217,56),(20674,215)): cmp(sid,i)
