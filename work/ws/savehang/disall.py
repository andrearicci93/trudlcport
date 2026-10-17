import sys,io
sys.path.insert(0,'tools')
import menu_dlc_probe as P
C=P.cache()
ids=[(s['id']) for s in P.secs(C,'pp') if s['type']==8 and s['data']]
import re
for sid in ids:
    out=io.StringIO()
    try: P.dis(C,'pp',sid,out=out)
    except Exception as e: out.write('ERR %s\n'%e)
    open('/private/tmp/claude-501/dis/s%d.txt'%sid,'w').write(out.getvalue())
print(len(ids))
