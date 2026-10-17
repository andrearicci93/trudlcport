import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import material_reslot as MR, drm_reloc as R
L=MR.libs(); XM,PM=L['XM'],L['PM']; mats,msh,mx2p=MR.dlc_tables()
def params(d,r,e):
    n=struct.unpack_from(e+'I',d,0x58)[0]; rel=R.parse(r,'le' if e=='<' else 'be'); o=dict(rel.internal).get(0x5c)
    return [struct.unpack_from(e+'4f',d,o+16*i) for i in range(n)]
st=collections.Counter(); ex=collections.defaultdict(list)
for x,p in mx2p.items():
    if x in XM and p in PM:
        xp=params(*XM[x],'>'); pp=params(*PM[p],'<')
        st[('n_pc>n_x' if len(pp)>len(xp) else 'eq' if len(pp)==len(xp) else 'n_pc<n_x')]+=1
        if len(pp)>len(xp):
            pt=struct.unpack_from('<3I',PM[p][0],0x28)
            ex[(len(xp),len(pp),pt)].append((x,p,pp[len(xp):],xp==pp[:len(xp)]))
print(st)
for k,v in sorted(ex.items(),key=lambda kv:-len(kv[1]))[:12]:
    print(k,len(v),'prefix-identical',sum(1 for t in v if t[3]))
    print('   extras sample',[[tuple(round(c,3) for c in e) for e in t[2]] for t in v[:3]])
