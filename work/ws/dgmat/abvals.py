import sys,struct,json
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R
L=MR.libs(); PM,XM=L['PM'],L['XM']; mats,msh,mx2p=MR.dlc_tables()
def params(d,r):
    n=struct.unpack_from('<I',d,0x58)[0]; rel=R.parse(r,'le'); o=dict(rel.internal).get(0x5c)
    return [struct.unpack_from('<4f',d,o+16*i) for i in range(n)]
import csv
rows=list(csv.DictReader(open('/path/to/trudlcport/work/ws/mat2/out/params_count.tsv'),delimiter='\t'))
out=open('out/ab_padded_tail.tsv','w'); out.write('mat\tn_xbox>n_pc\tindices_to_edit(vec4 idx = cN-100)\tbase_surrogate_mat\tsurrogate_tail_values\n')
for r in rows:
    if r['class']!='sospetto-alto': continue
    mid=int(r['material']); bm=msh[mid]['base_material']; p=mx2p.get(bm)
    if p not in PM: continue
    bp=params(*PM[p]); nx=int(r['n_xbox']); npc=int(r['n_pc'])
    tail=[tuple(round(c,4) for c in v) for v in bp[nx:npc]]
    out.write('%d\t%d>%d\t%s\t%d(pc %d)\t%s\n'%(mid,nx,npc,','.join(str(i) for i in range(nx,npc)),bm,p,' '.join(map(str,tail))))
out.close(); print(open('out/ab_padded_tail.tsv').read())
