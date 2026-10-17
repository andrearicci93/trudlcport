import sys, os, json, collections, hashlib, struct; sys.path.insert(0,'tools')
import dtp_keys as K, dtp_audit as A, drm_write as DW, drm_reloc as R
HERE='work/ws/rebuild'; OUT='work/ws/dtpkeys/out'; LW=3
eff={l.rstrip('\n').split('\t')[0]:l.rstrip('\n').split('\t')[4] for l in open(HERE+'/installed_effective.tsv') if not l.startswith('relpath')}
drift=json.load(open('work/ws/dtpkeys/drift_verdict.json'))
# 1) key findings on the effective installed overlay, tier T1 (candidates), local-evidence veto/confirm
cand={}   # (file,id,off) -> dict
for rel,path in sorted(eff.items()):
    if not rel.endswith('.drm') or not os.path.exists(path): continue
    for f in K.scan_file(rel,path,K.TIERS['T1'],K.FAMS):
        if f['owned'] or f['want'] is None: continue
        cand[(rel,f['id'],f['off'])]=f
print('candidates T1',len(cand))
# local evidence for candidates
need={}
xc={}
for (rel,sid,o),f in cand.items():
    if rel not in xc: xc[rel]=A.xsecs(rel)
    import dtpid_sweep as DS; _,ids=DS.ctx()
    x=next(x for x in xc[rel] if x['type']==7 and x['data'] is not None and ids(7,x['id'])==sid)
    d=x['data']
    if o-4*LW>=0 and o+4+4*LW<=len(d):
        w=(d[o-4*LW:o],d[o+4:o+4+4*LW])
        if sum(1 for q in range(0,len(w[0]+w[1]),4) if (w[0]+w[1])[q:q+4]!=b'\0'*4)>=2: need[(w,d[o:o+4])]=need.get((w,d[o:o+4]),[])+[f]
ev=collections.defaultdict(lambda:[0,K.ALL])
for xx,p,xb,pc,xr in A.base_pairs():
    xd,pd=xb['data'],pc['data']
    for o in range(4*LW,len(xd)-4*LW-3,4):
        k=((xd[o-4*LW:o],xd[o+4:o+4+4*LW]),xd[o:o+4])
        if k in need:
            c=A.cls(xd[o:o+4],pd[o:o+4])
            if c!=K.ALL and c!=0: e=ev[k]; e[0]+=1; e[1]&=c
for k,fl in need.items():
    e=ev.get(k)
    for f in fl:
        if e and e[0]: f['loc']=(e[1],e[0])
final={}   # (file,id,off) -> (new hex, source, certainty, detail)
vet=collections.Counter()
for key,f in cand.items():
    c=A.cls(bytes.fromhex(f['xbox']),bytes.fromhex(f['pc']))
    if 'loc' in f:
        lm,ln=f['loc']
        if lm and not c&lm: final[key]=(f['want'],'keys:%s'%f['fam'],'high' if f['n']>=100 else 'medium','local n=%d + rule n=%d d=%d'%(ln,f['n'],f['d'])); vet['accept_local']+=1
        elif lm and c&lm: vet['veto_local']+=1; f['veto']=True
        else: vet['local_mixed_skip']+=1
    else:
        if f['fam'] in ('S1','R') and f['n']>=100 and f['d']>=8: final[key]=(f['want'],'keys:%s'%f['fam'],'medium-low','rule only n=%d d=%d'%(f['n'],f['d'])); vet['accept_rule_T2']+=1
        else: vet['skip_weak']+=1
print(dict(vet))
# 2) drift verdicts: fresh certified
dc=collections.Counter()
for r in drift:
    key=(r['file'],r['id'],r['off'])
    if r['owned'] or r['verdict']!='fresh' or not r['inst_is_base']: continue
    ok = r['cert'] in ('high','medium') or (r['cert']=='medium-low' and r.get('rule') and r['rule'][0] in ('S1','R') and r['rule'][2]>=100 and r['rule'][3]>=8)
    if not ok: dc['fresh_weak']+=1; continue
    if key in final and final[key][0]!=r['fresh']: dc['conflict_with_keys']+=1; continue
    final[key]=(r['fresh'],'drift:fresh',r['cert'],'rule=%s loc=%s'%(r.get('rule'),r.get('loc'))); dc['drift_applied']+=1
print(dict(dc), 'total words',len(final))
# 3) write two sets
PRI=('dlc1_uo_raft_bridge_spawned','dlc1_uo_dragon_slider','dlc1_uo_bend_switches','dlc1_uo_goo_pit_lever','dlc_dungeon','dlc1_uo_pillar_of_doom_a','dlc1_uo_pillar_of_doom_b','dlc1_uo_sewer_gate')
def in_min(key,v):
    rel=key[0]
    if v[1]=='drift:fresh': return v[2]=='high' and os.path.splitext(rel)[0] in PRI
    return v[2]=='high' and v[3].startswith('local')
import dtpid_sweep as DS; _,ids=DS.ctx()
def build(OUT,sel):
    os.makedirs(OUT,exist_ok=True)
    byf=collections.defaultdict(list)
    for key,v in final.items():
        if sel(key,v): byf[key[0]].append((key[1],key[2],v))
    md5=[]; log=[]; tot=0
    for rel,lst in sorted(byf.items()):
        raw=open(eff[rel],'rb').read(); D=DW.read(raw,'le'); xs=A.xsecs(rel)
        pair={D.sections[i].id:i for x,i in A.section_pairs(xs,D) if x['type']==7}
        n=0
        for sid,o,(new,src,cert,det) in sorted(lst):
            sec=D.sections[pair[sid]]; old=sec.data[o:o+4].hex()
            b=bytearray(sec.data); b[o:o+4]=bytes.fromhex(new); sec.data=bytes(b); n+=1
            log.append('%s\tDTP %d\t%#x\t%s\t%s\t%s\t%s\t%s'%(rel,sid,o,old,new,src,cert,det))
        o2=D.write('le')
        if raw[:4]==b'CDRM': o2=DW.cdrm_encode(o2,'le')
        dst=os.path.join(OUT,rel); os.makedirs(os.path.dirname(dst),exist_ok=True); open(dst,'wb').write(o2)
        D0=DW.read(raw,'le'); D2=DW.read(o2,'le'); diff=0
        for a0,a2 in zip(D0.sections,D2.sections):
            assert (a0.type,a0.id,a0.reloc,a0.ver,a0.flags)==(a2.type,a2.id,a2.reloc,a2.ver,a2.flags)
            diff+=sum(1 for q in range(0,len(a0.data),4) if a0.data[q:q+4]!=a2.data[q:q+4])
        assert diff==n,(rel,diff,n)
        md5.append('%s  %s'%(hashlib.md5(o2).hexdigest(),rel)); tot+=n
    open(OUT+'/md5.txt','w').write('\n'.join(md5)+'\n'); open(OUT+'/log_words.tsv','w').write('file\tdtp\toff\told\tnew\tsource\tcertainty\tdetail\n'+'\n'.join(log)+'\n')
    print(OUT,len(md5),'files',tot,'words')
import shutil
for d in ('min','full'): shutil.rmtree('work/ws/dtpkeys/out/'+d,ignore_errors=True)
for f in os.listdir('work/ws/dtpkeys/out'):
    q='work/ws/dtpkeys/out/'+f
    if os.path.isdir(q) and f not in('min','full'): shutil.rmtree(q)
    elif os.path.isfile(q): os.remove(q)
build('work/ws/dtpkeys/out/min',in_min)
build('work/ws/dtpkeys/out/full',lambda k,v:True)
# verdict table for ALL drift words + EXPLAINED join
expl={}
for l in open(HERE+'/diff_sections.tsv'):
    c=l.rstrip('\n').split('\t')
    if len(c)>7 and c[1]=='7': expl[(c[0],int(c[2]))]=c[7]
with open('work/ws/dtpkeys/out/drift_verdicts.tsv','w') as fh:
    fh.write('file\tdtp\toff\txbox\tinstalled\tfresh\tinstalled_equals_base\tverdict\tcertainty\tsource_of_certainty\tapplied\tlayer_note\n')
    for r in drift:
        key=(r['file'],r['id'],r['off']); v=final.get(key)
        if not r['inst_is_base']: note='installed carries a layer fix (see diff_sections EXPLAINED: %s); fresh does not reproduce it -> keep installed'%expl.get((r['file'],r['id']),'?')
        elif r['owned']: note='owned by typed fixer'
        else: note=''
        src=('rule %s n=%s d=%s'%(r['rule'][0],r['rule'][2],r['rule'][3]) if r.get('rule') else '')+(' local n=%s'%r['loc'][1] if r.get('loc') else '')
        verdict=r['verdict'] if r['inst_is_base'] else 'inst(layer)'
        fh.write('\t'.join(str(x) for x in (r['file'],r['id'],hex(r['off']),r['xbox'],r['inst'],r['fresh'],r['inst_is_base'],verdict,r['cert'],src,'yes' if (v and v[1]=='drift:fresh') else 'no',note))+'\n')
