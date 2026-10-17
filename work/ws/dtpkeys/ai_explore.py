import sys; sys.path.insert(0,'tools')
import pickle, struct, collections, os
import aidata_fix as AF, drm_reloc as R, drm_write as DW, dtp_audit as A
T=AF.table()
print('T offsets',len(T), 'words/rec', AF.SIZE//4)
pairs=AF._pairs()
# base: values per offset across all records (Xbox)
vals=collections.defaultdict(collections.Counter); recs=0
for nm,s,rel,st,pc in AF._iter_pairs(pairs):
    for t in st:
        recs+=1
        for w in range(0,AF.SIZE,4):
            vals[w][s['data'][t+w:t+w+4].hex()]+=1
print('base recs',recs)
unseen=[w for w in range(0,AF.SIZE,4) if w not in T]
print('unseen offsets',len(unseen))
print({hex(w):dict(vals[w].most_common(4)) for w in unseen if set(vals[w])-{'00000000'}})
# DLC
files=A.overlay(A.INSTALLED+['mods_fix20'])
dl=collections.defaultdict(collections.Counter)
for rel,path in sorted(files.items()):
    xs=A.xsecs(rel)
    if xs is None: continue
    for s in xs:
        if s['type']!=7 or s['data'] is None: continue
        r=R.parse(s['reloc'],'be'); st=AF.detect(s['data'],r)
        for t in st:
            for w in unseen:
                xw=s['data'][t+w:t+w+4]
                if xw!=b'\0'*4: dl[w][xw.hex()]+=1
print('DLC nonzero at unseen offsets:')
for w in sorted(dl): print(hex(w), dict(dl[w]))
