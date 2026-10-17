import sys,csv
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import *
ids=set(int(x) for x in sys.argv[1:])
for r in csv.DictReader(open('/path/to/trudlcport/work/ws/rebuild/installed_effective.tsv'),delimiter='\t'):
    if not r['relpath'].endswith('.drm'): continue
    raw=cdrm_decode(open(r['abs_path'],'rb').read(),'le')
    try: h,secs=sections_with_data(raw,'le')
    except Exception as e: print('ERR',r['relpath'],e); continue
    for s in secs:
        if s['id'] in ids: print(r['relpath'],r['winning_overlay'],'sec',s['i'],'type',s['type'],'id',s['id'],'size',hex(s['size']),'nreloc',s['nreloc'])
