import sys, json, collections; sys.path.insert(0,'tools')
import dtp_keys as K, dtp_audit as A, dtpid_sweep as DS, analog_word_fix as AW, drm_write as DW, drm_reloc as R
tier=sys.argv[1] if len(sys.argv)>1 else 'T1'
fs=json.load(open('work/ws/dtpkeys/scan_%s.json'%tier))
st,ids=DS.ctx()
by=collections.defaultdict(list)
for f in fs: by[(f['file'],f['id'])].append(f)
res=collections.Counter(); bad=[]
for (rel,sid),lst in by.items():
    xs=A.xsecs(rel)
    for x in xs:
        if x['type']==7 and x['data'] is not None and ids(7,x['id'])==sid: break
    else: continue
    ax=AW.best_analog(x,st,ids)
    if ax is None: res['no_analog']+=len(lst); continue
    xb=st['xb_store'][(7,ax)]['data']; pc=st['pc_store'][(7,ids.base[7][ax])]['data']
    if len(pc)!=len(xb): res['no_analog']+=len(lst); continue
    for f in lst:
        o=f['off']; xw=bytes.fromhex(f['xbox'])
        if xb[o:o+4]!=xw: res['analog_differs_here']+=1; continue
        if not AW.perm_ok(xb[o:o+4],pc[o:o+4]): res['analog_reauth']+=1; continue
        if f['want'] is None: res['want_none']+=1; continue
        if pc[o:o+4].hex()==f['want']: res['AGREE']+=1
        elif pc[o:o+4].hex()==f['pc']: res['DISAGREE(analog==installed)']+=1; bad.append((rel,sid,hex(o),f))
        else: res['other']+=1
print(dict(res))
for b in bad[:20]: print(b[0],b[1],b[2],b[3]['xbox'],b[3]['pc'],b[3]['want'],b[3]['fam'],b[3]['key'])
