import sys,struct,pickle,collections
sys.path.insert(0,'tools')
import material_reslot as MR, material_convert as MC
L=MR.libs(); PM=L['PM']
mx2p=pickle.load(open('work/render/material_x2p.pkl','rb'))
mats,msh,_=MR.dlc_tables()
rows=pickle.load(open('work/ws/mat2/scratch/rows.pkl','rb'))
tsv={}
for ln in open('work/ws/mat/out/materials.tsv').read().splitlines()[1:]:
    f=ln.split('\t'); tsv[int(f[0])]=f
for r in rows:
    if r['unver'] and r['npc']>r['nx']:
        m=mats[r['mid']]; vp=MC.read_params(m['data'],m['reloc'],'<')
        bd,br=PM[mx2p[r['bm']]]; vb=MC.read_params(bd,br,'<')
        zr=[i for i in r['usedset'] if i>=r['nx']]
        bvals=[tuple(round(a,3) for a in vb[i]) for i in zr]
        print(r['mid'],tsv[r['mid']][4][:34],r['nx'],'->',r['npc'],'zero-read',zr,'base vals',bvals[:4], 'DLC vals', [tuple(vp[i]) for i in zr][:1])
