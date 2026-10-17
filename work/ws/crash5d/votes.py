import sys,pickle
sys.path.insert(0,'/path/to/trudlcport/tools')
import generic_type0 as G0, generic_learn as G
T7=pickle.load(open('/path/to/trudlcport/work/generic/type7_table.pkl','rb'))
key1=(('LVL',), (('x', 7, 116), 16, 1128)), 48
key0=(('LVL',), (('x', 7, 116), 16, 984)), 48
ck1=(('LVL',), (1128,), 48)
for nm,k in (('1128 label',key1[0]+(48,) if False else key1),('984',key0)):
    pass
K1=(('LVL',), (('x', 7, 116), 16, 1128)),48
import itertools
def show(k):
    print(repr(k)[:140], dict(T7.get(k,{})))
lab1=((('LVL',), (('x', 7, 116), 16, 1128)), 48)
show(lab1); show(('S',)+lab1+('B3',))
show(G.mid(lab1)); show(('C',)+ck1); show(('SC',)+ck1+('B3',))
lab0=((('LVL',), (('x', 7, 116), 16, 984)), 48)
show(lab0); show(('S',)+lab0+('B3',)); show(('SC',)+(('LVL',), (984,), 48)+('B3',))
