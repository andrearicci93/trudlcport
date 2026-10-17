# Carica tutte le tabelle locals (sola lettura) in tables.pkl. Usa tools/locals.py come libreria, senza modificarla.
import sys, os, pickle
sys.path.insert(0, '/path/to/trudlcport/tools')
import locals as L
T = {}
for s in L.SRC:
    f, e = L.files(s)
    T[s] = {}
    for spec, b in f.items():
        lang, st, offs = L.parse(b, e)
        T[s][spec] = {'lang': lang, 'strings': st, 'offs': list(offs), 'raw': b}
pickle.dump(T, open('/path/to/trudlcport/work/ws/hints/tables.pkl', 'wb'))
print({s: len(T[s]) for s in T})
