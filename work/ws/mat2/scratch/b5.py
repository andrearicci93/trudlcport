import pickle,collections
rows=pickle.load(open('work/ws/mat2/scratch/rows.pkl','rb'))
c=collections.Counter()
for r in rows:
    k=('unver' if r['unver'] else 'rule', 'n==umax' if r['npc']==r['umax'] else ('n>umax' if r['npc']>r['umax'] else 'n<umax'), 'n<nx' if r['npc']<r['nx'] else ('n>nx' if r['npc']>r['nx'] else 'n==nx'))
    c[k]+=1
for k,v in sorted(c.items()): print(k,v)
for r in rows:
    if r['npc']<r['umax']: print('SHORT',r)
    if r['mid'] in (20879,20883,20887,23403): print(r)
# xbox consistency
c2=collections.Counter()
for r in rows: c2[(r['nx']==r['xneed'], r['nx']>=r['xneed'])]+=1
print('xbox nx==xneed,>=',c2)
# unver with umax vs xneed
c3=collections.Counter()
for r in rows:
    if r['unver']: c3[(r['umax']==r['xneed'], r['umax']<r['xneed'], r['umax']>r['xneed'])]+=1
print('unver umax vs xneed (eq,lt,gt)',c3)
