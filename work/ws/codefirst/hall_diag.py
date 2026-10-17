"""Diagnosi statica travi rosse: per i 6 materiali di dlc_caverns_hall cambiati da B86, tabella entry -> sampler -> texture (formato Xbox/PC)
e cosa leggeva la lib in B84 (registro Xbox usato come slot PC) contro B86 (slot PC giusto). Nessuna VM.
Uso: tools/venv/bin/python -I work/ws/codefirst/hall_diag.py"""
import sys,json,glob,os,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
from archive import Archive
from tex_convert import parse_xbox, parse_pc
T='/path/to/trudlcport/'
C=json.load(open(T+'work/ws/contratti/out/contracts.json'))['materials']
hall=[m for m,v in C.items() if 'dlc_caverns_hall.drm' in v['drms']]
# indice texture PC: B86 mods + idx_pc ; Xbox: idx_dlc + idx_xbox_base
def build_idx(path):
    d=json.load(open(path)); r={}
    for e in d:
        if not isinstance(e[5],list): continue
        for s in e[5]:
            if s[0]==5: r.setdefault(s[1],(e[0],e[1]))
    return r
IX={'dlc':build_idx(T+'work/idx_dlc.json'),'xb':build_idx(T+'work/idx_xbox_base.json'),'pc':build_idx(T+'work/idx_pc.json')}
_arch={}
def sec_from(src,tid,endian):
    path,i=IX[src][tid]
    if path not in _arch: _arch[path]=Archive(path,endian)
    a=_arch[path]; raw=cdrm_decode(a.read(a.idx[i]),endian); h,secs=sections_with_data(raw,endian)
    return [s for s in secs if s['type']==5 and s['id']==tid][0]['data']
def xtex(tid):
    for src in ('dlc','xb'):
        if tid in IX[src]: return parse_xbox(sec_from(src,tid,'be')),src
    return None,None
_pcdrm={}
def ptex(tid):
    for f in sorted(glob.glob(T+'work/baseline/B86_contratti/mods/*.drm'))[:0]: pass
    # prima: DRM del DLC (dlc_caverns_hall) poi bigfile base
    for f in ('dlc_caverns_hall.drm',):
        if f not in _pcdrm:
            raw=cdrm_decode(open(T+'work/baseline/B86_contratti/mods/'+f,'rb').read(),'le'); _pcdrm[f]=sections_with_data(raw,'le')[1]
        for s in _pcdrm[f]:
            if s['type']==5 and s['id']==tid: return parse_pc(s['data']),'hall'
    if tid in IX['pc']: return parse_pc(sec_from('pc',tid,'le')),'pc-base'
    return None,None
def pfmt(h):
    f=h['fmt']; return {0x31545844:'DXT1',0x33545844:'DXT3',0x35545844:'DXT5',0x15:'A8R8G8B8'}.get(f,hex(f))
out=[]
for mid in hall:
    v=C[mid]; rows=v['sampler_map']
    out.append(f"\n=== materiale {mid}  lib {v['lib']} (DLC lib {v['dlc_lib']}) donor {v['donor']}  identity={v['identity']}")
    byslot={r['pc_slot']:r for r in rows}; byreg={r['xbox_reg']:r for r in rows}
    for r in rows:
        xh,xs=xtex(r['xbox_tex']); ph,ps=ptex(r['pc_tex'])
        xf=xh['fmtname'] if xh else '?'; pf=pfmt(ph) if ph else '?'
        dim=(f"{ph['w']}x{ph['h']}" if ph else '?')
        cube=' CUBO' if ph and ph['flags']&0x8000 else ''
        out.append(f"  entry{r['entry']} type{r['type']} flag{r['flag']} '{r['sampler']}'  Xbox reg s{r['xbox_reg']} -> PC slot {r['pc_slot']} | tex Xbox {r['xbox_tex']}({xf},{xs}) PC {r['pc_tex']}({pf},{ps},{dim}{cube})")
    out.append('  lettura per REGISTRO del PS (cosa vede lo shader):')
    for reg in sorted(byreg):
        rx=byreg[reg]       # B86: legge lo slot PC dell'entry che ha xbox_reg==reg
        rb=byslot.get(reg)  # B84: legge lo slot PC == reg, cioe' l'entry che ha pc_slot==reg
        ok='uguale' if rb is rx else 'DIVERSO'
        out.append(f"    s{reg}: B86 -> entry{rx['entry']} tex {rx['pc_tex']} ({rx['sampler'][:34]}) | B84 -> "+(f"entry{rb['entry']} tex {rb['pc_tex']} ({rb['sampler'][:34]})" if rb else 'nessuna entry (slot vuoto)')+f"  [{ok}]")
open(T+'work/ws/codefirst/hall_diag.txt','w').write('\n'.join(out)); print('\n'.join(out))
