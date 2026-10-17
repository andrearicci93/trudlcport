"""split.py - indicizza le funzioni decompilate: scrive work/ws/visual2/fn/<addr>.c (non cancella nulla) e stampa punteggio su offset materiale."""
import glob,re,os,sys,collections
OUT='/path/to/trudlcport/work/ws/visual2/fn'; os.makedirs(OUT,exist_ok=True)
fn={}
for f in sorted(glob.glob('/path/to/ghidra_out/full/f_*.c')):
    txt=open(f,errors='replace').read()
    parts=re.split(r'^//=== (\S+) @ ([0-9a-f]{8})\n',txt,flags=re.M)
    for i in range(1,len(parts),3): fn[parts[i+1]]=parts[i+2]
print(len(fn),'funzioni')
import pickle; pickle.dump(fn,open('/path/to/trudlcport/work/ws/visual2/fn.pkl','wb'))
