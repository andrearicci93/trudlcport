"""Nomi delle costanti MaterialParams (c100..115) nei ctab del gemello Xbox (xs) e del donatore PC (pd), per famiglia. Uso: ctab_fam.py XS PD"""
import sys
S4='/path/to/trudlcport/work/ws/shader4'; sys.path.insert(0,S4)
from f9_transplant import *
xs,pd=int(sys.argv[1]),int(sys.argv[2])
L=libs(); X,P=L['X'],L['P']
for slot in (0,):
    xb=X[xs]['entries'][X[xs]['slots'][slot&1]]['blob']; pb=P[pd]['entries'][P[pd]['slots'][slot]]['blob']
    sh=XL.parse(xb)
    print('XBOX ctab (%d entries) keys:'%len(sh.ctab), sorted(sh.ctab[0].keys()))
    for c in sh.ctab:
        if c['set']==0 or True: print('  X ',{k:c[k] for k in c if k not in ('data',)})
    print('PC ctab:')
    for t in pc_ctab(pb): print('  P ',t)
