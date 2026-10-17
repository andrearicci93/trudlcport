import sys, os, struct, collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm
W='/path/to/trudlcport/work/'
def secs(p,e):
    raw=drm.cdrm_decode(open(p,'rb').read(),e); return drm.sections_with_data(raw,e)[1]
f='dlc_dungeonhallb_dungeonhallb_a.drm'
xs=secs(W+'ws/dgstatic/xbox/'+f,'be'); ps=secs(W+'baseline/B8/mods/streamgroups/'+f,'le')
x=[s for s in xs if s['type']==12 and s['id']==21266][0]; y=[s for s in ps if s['type']==12 and s['id']==21266][0]
a=x['data']; b=y['data']
print(len(a),len(b), 'reloc',len(x['reloc']),len(y['reloc']))
diff=[i for i in range(0,len(a),4) if a[i:i+4][::-1]!=b[i:i+4]]
print('words differing from 32-bit swap:',len(diff),'of',len(a)//4, 'first',diff[:10], 'last', diff[-5:])
print('head X',a[:64].hex()); print('head P',b[:64].hex())
d0=diff[0] if diff else 0
print('X@',d0,a[d0:d0+32].hex()); print('P@',d0,b[d0:d0+32].hex())
# histogram of positions mod 0x...
