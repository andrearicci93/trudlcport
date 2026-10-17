import sys,os
sys.path.insert(0,'/path/to/trudlcport/work/ws/xenos'); sys.path.insert(0,'/path/to/trudlcport/tools')
import xenos_xlat as X
L=X.load_libs(); D,Xl=L['D'],L['X']
lid=int(sys.argv[1]); slot=int(sys.argv[2]) if len(sys.argv)>2 else 0
lib=D.get(lid) or Xl[lid]
sl=[s for s in lib['slots'] if s!=0xffffffff]
print('lib',lid,'slots',len(lib['slots']),'occupied',len(sl))
s=sl[slot]; b=lib['entries'][s]['blob']
sh=X.parse(b); T=X.text(sh,'pretty')
print('PS' if sh.is_ps else 'VS',len(T.lines),'lines')
cu=[]
for reg in sorted(T.uses):
    e=sh.f4.get(reg); cu.append('c%d=%s %s'%(reg,('%s[%d]'%(e[0]['name'],e[1]) if e else ('def' if reg in sh.defs else '?')),''.join('xyzw'[c] for c in sorted(T.uses[reg]))))
print('; '.join(cu)); print('samplers',[(k[0],k[1][:40],k[2],n) for k,n in sorted(T.samp_uses.items())])
open(sys.argv[3] if len(sys.argv)>3 else '/dev/null','w').write('\n'.join(T.lines))
