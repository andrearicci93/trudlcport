"""Giro 6 task 2: uid intro >= 16352 in tutti i DRM livello della baseline/dir + lettura riferimenti noti. Uso: uid_scan.py MODS_DIR"""
import sys, os, glob, struct, collections, json
ROOT='/path/to/trudlcport'; sys.path.insert(0, ROOT+'/tools')
import drm, unit_ids as U
R=sys.argv[1]; hi={}; allids=collections.defaultdict(set)
for p in sorted(glob.glob(R+'/**/*.drm', recursive=True)):
    try: sc=drm.sections_with_data(drm.cdrm_decode(open(p,'rb').read(),'le'),'le')[1]; Lv=U.level_info(sc,'le')
    except Exception: continue
    if not Lv or not Lv['intros']: continue
    rel=os.path.relpath(p,R)
    ids=[struct.unpack_from('<I', sc[si]['data'], o+0x58)[0] for si,o in Lv['intros']]
    allids[rel]=set(ids)
    h=sorted(i for i in ids if i>=16352)
    print('%-52s intro %4d  max uid %6d  >=16352: %s' % (rel, len(ids), max(ids), h))
    if h: hi[rel]=h
json.dump(hi, open(ROOT+'/work/ws/giro6/uid_hi.json','w'))
