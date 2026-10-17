"""rolefix_apply.py - applica la mappa di ruolo D->S ai MaterialParams delle sezioni tipo 10 dei DRM DLC (stessa dimensione, solo float dei params).
uso: rolefix_apply.py OUTDIR BASELINE_MODS_DIR [--only ID,ID] [--skip ID,ID]  ; scrive solo i DRM cambiati + report.tsv
controlli: la sezione deve avere params == copia D (regola corrente) altrimenti SKIP; 21118 escluso (mappa a mano)."""
import sys,os,struct,collections
sys.path.insert(0,'/path/to/trudlcport/work/ws/visual2'); sys.path.insert(0,'/path/to/trudlcport/tools')
import rolefix as RF, drm_write as DW, drm_reloc as R, dtp_audit as DA
def key(v): return [tuple(round(x,5) for x in q) for q in v]
def main():
    out=sys.argv[1]; src=sys.argv[2]; only=skip=None
    for i,a in enumerate(sys.argv):
        if a=='--only': only={int(x) for x in sys.argv[i+1].split(',')}
        if a=='--skip': skip={int(x) for x in sys.argv[i+1].split(',')}
    RF.init(); os.makedirs(out,exist_ok=True)
    plans={}
    for xmid,m in sorted(RF.MATS.items()):
        if m['source']!='converted' or xmid==21118: continue
        if only and xmid not in only: continue
        if skip and xmid in skip: continue
        r=RF.new_params(xmid)
        if r is None: continue
        cur,base,new,rule=r
        if base!=new and key(cur)==key(base): plans[xmid]=(base,new)
    print('materiali pianificati',len(plans))
    rep=[]; nfiles=0
    for rel,path in sorted(DA.overlay([src],None).items()):
        try: D=DW.read(open(path,'rb').read(),'le')
        except Exception: continue
        ch=[]
        for s in D.sections:
            if s.type!=10 or s.id not in plans: continue
            base,new=plans[s.id]
            ip=dict(R.parse(s.reloc,'le').internal); n=struct.unpack_from('<I',s.data,0x58)[0]
            cur=[struct.unpack_from('<4f',s.data,ip[0x5C]+16*i) for i in range(n)]
            if key(cur)!=key(base): rep.append((rel,s.id,'SKIP params non = copia D')); continue
            b=bytearray(s.data)
            for i,v in enumerate(new): struct.pack_into('<4f',b,ip[0x5C]+16*i,*v)
            assert len(b)==len(s.data)
            s.data=bytes(b); ch.append(s.id); rep.append((rel,s.id,'APPLY'))
        if ch:
            dst=os.path.join(out,rel); os.makedirs(os.path.dirname(dst),exist_ok=True)
            open(dst,'wb').write(DW.cdrm_encode(D.write('le'),'le')); nfiles+=1
    open(os.path.join(out,'report.tsv'),'w').write('\n'.join('\t'.join(map(str,r)) for r in rep)+'\n')
    c=collections.Counter(r[2] for r in rep); print('file scritti',nfiles,dict(c))
if __name__=='__main__': main()
