import sys,struct,json
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R
from drm import cdrm_decode, sections_with_data
L=MR.libs(); PM,XM,DM=L['PM'],L['XM'],L['DM']; mats,msh,mx2p=MR.dlc_tables()
F=json.load(open('out/feat.json')); C=json.load(open('out/census.json'))
T='/path/to/trudlcport/work/baseline/B8/mods/'
def params(d,r,e):
    n=struct.unpack_from(e+'I',d,0x58)[0]; rel=R.parse(r,'le' if e=='<' else 'be'); o=dict(rel.internal).get(0x5c)
    return [struct.unpack_from(e+'4f',d,o+16*i) for i in range(n)]
def fmt(v): return '('+','.join('%.4g'%x for x in v)+')'
def load(mid):
    for drm in C[str(mid)]['drm']:
        raw=cdrm_decode(open(T+drm.replace('\\','/'),'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
        for s in secs:
            if s['type']==10 and s['id']==mid: return s['data'],s['reloc'],drm
for mid in map(int,sys.argv[1:]):
    d,r,drm=load(mid); pp=params(d,r,'<'); xx=params(*DM[mid],'>') if mid in DM else []
    print('=====',mid,drm,'refs',C[str(mid)]['refs'],'pt',struct.unpack_from('<3I',d,0x28),'xt',F[str(mid)]['xt'])
    print(' msh',{k:v for k,v in msh.get(mid,{}).items() if k!='data'})
    print(' pc samplers',[n[-40:] for n in F[str(mid)]['pc_samp']]); print(' xbox samplers',[n[-40:] for n in F[str(mid)].get('x_samp',[])])
    print(' tex',F[str(mid)]['tex'])
    print(' xbox consts',F[str(mid)].get('x_const'))
    bm=msh.get(mid,{}).get('base_material'); bp=params(*PM[mx2p[bm]],'<') if bm in XM and mx2p.get(bm) in PM else []
    for i in range(max(len(pp),len(xx),len(bp))):
        print('  c%d  PC %-34s  XB %-34s  BASE-SURR %s'%(100+i,fmt(pp[i]) if i<len(pp) else '-',fmt(xx[i]) if i<len(xx) else '-',fmt(bp[i]) if i<len(bp) else '-'))
