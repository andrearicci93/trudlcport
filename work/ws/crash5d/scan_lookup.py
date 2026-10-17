"""Meccanismo: parole type-7 DLC convertite da convert_section0 con shape B3 (Xbox 0x000000XX, XX!=0) la cui classe viene da label/mid/coarse/region (NESSUN voto per la shape) e classe != s32.
Confronto con i byte PC reali installati (B5)."""
import sys,os,glob,struct,collections,json
sys.path.insert(0,'/path/to/trudlcport/tools')
import dtpid_sweep as DS, dlc_generic as DG, drm_reloc as R, dtp_audit as A, generic_type0 as G0, drm_write as DW
W='/path/to/trudlcport/work/'
st,ids=DS.ctx(); T=DG.table(); T7=G0.table7()
d=W+'baseline/B5/mods'; rows=[]; nfile=0; nwords=0; srcc=collections.Counter()
for p in sorted(glob.glob(d+'/**/*.drm',recursive=True)):
    rel=os.path.relpath(p,d).replace('\\','/'); xs=A.xsecs(rel)
    if xs is None: continue
    nfile+=1; ids.local={}
    D=DW.read(open(p,'rb').read(),'le')
    pairs={id(x):i for x,i in A.section_pairs(xs,D)}
    try: labs0=G0.labels(xs,'be')
    except Exception as e: print('labels fail',rel,e); continue
    for k,s in enumerate(xs):
        if s['type']!=7 or s['data'] is None or id(s) not in pairs or A.base_content(s): continue
        sec=D.sections[pairs[id(s)]]
        if len(sec.data)!=len(s['data']): continue
        rl=R.parse(s['reloc'],'be'); skip=set(rl.pointer_offsets())|set(rl.id_offsets())
        x=s['data']
        for w,key,ck in G0.G.word_keys(len(x),labs0[k]):
            if w in skip: continue
            xw=x[w:w+4]
            if G0.shape(xw)!='B3': continue
            c,src=G0.lookup(T7,T,key,ck,xw); nwords+=1; srcc[(src,c)]+=1
            if src not in ('shape','shape-coarse') and c!='s32':
                rows.append(dict(file=rel,id=sec.id,xid=s['id'],off=w,xbox=xw.hex(),pc=sec.data[w:w+4].hex(),cls=c,src=src))
print('files',nfile,'B3 words',nwords,'by (src,class) top',srcc.most_common(10))
print('flagged (B3, no shape votes, class!=s32):',len(rows))
c=collections.Counter((r['cls'],r['src'],r['xbox']) for r in rows); print(c.most_common(25))
json.dump(rows,open(W+'ws/crash5d/scan_lookup.json','w'),indent=0)
