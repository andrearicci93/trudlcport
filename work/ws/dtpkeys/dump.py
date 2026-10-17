import sys; sys.path.insert(0,'tools')
import dtpid_sweep as DS, drm_reloc as R, struct
st,ids=DS.ctx()
x=int(sys.argv[1]); xb=st['xb_store'][(7,x)]; p=ids.base[7][x]; pc=st['pc_store'][(7,p)]
xr=R.parse(xb['reloc'],'be'); ptr=set(xr.pointer_offsets()); idl=set(xr.id_offsets()); it=dict(xr.internal)
print(xb['src'],'pc id',p,len(xb['data']),len(pc['data']))
lo=int(sys.argv[2],0) if len(sys.argv)>2 else 0; hi=int(sys.argv[3],0) if len(sys.argv)>3 else len(xb['data'])
for o in range(lo,hi,4):
    xw=xb['data'][o:o+4]; pw=pc['data'][o:o+4]
    print('%04x %s %s %s %s'%(o,xw.hex(),pw.hex(),'P->%x'%it[o] if o in it else 'P' if o in ptr else 'I' if o in idl else '', repr(xw) if all(32<=c<127 for c in xw) else ''))
