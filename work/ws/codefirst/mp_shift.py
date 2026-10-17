"""Per ogni famiglia di ponte rifiutata: relazione righe PC vs Xbox (traslazione -2..+2, valori) sui materiali base."""
import sys
S4='/path/to/trudlcport/work/ws/shader4'; sys.path.insert(0,S4)
from f9_common import *
fams=[(1431,1060),(981,1531),(111,225),(164,207),(1409,1038),(300,356)]
def rowtxt(r): return '['+' '.join('%.3g'%v for v in r)+']'
for xs,pd in fams:
    br=material_pairs(xs,pd)
    print(f'\n=== famiglia ({xs},{pd}): {len(br)} materiali ponte')
    for mx,mp,XP,PP in br[:3]:
        print(f'  mat Xbox {mx} / PC {mp}: righe Xbox {len(XP)}, PC {len(PP)}')
        for sh in (-2,-1,0,1,2):
            ok=tot=0
            for i,xr in enumerate(XP):
                j=i+sh
                if 0<=j<len(PP):
                    tot+=1; ok+= all(abs(a-b)<1e-6 for a,b in zip(xr,PP[j]))
            print(f'     traslazione PC=Xbox+{sh:+d}: {ok}/{tot} righe uguali')
        if len(br)==1 or mx==br[0][0]:
            for i in range(max(len(XP),len(PP))):
                print(f'     riga {100+i}: Xbox {rowtxt(XP[i]) if i<len(XP) else "-":42s} PC {rowtxt(PP[i]) if i<len(PP) else "-"}')
