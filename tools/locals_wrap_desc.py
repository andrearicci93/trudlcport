"""A-capo delle descrizioni missione DLC nel menu 'PLAY MISSION' (script PC 104, widget testo id 456/457).

Sintomo (16/10): la descrizione di 'BENEATH THE ASHES' e' su UNA riga larga ~4000 px e sborda lo schermo.
Causa: nel PC stock gli id 456..461 sono il segnaposto 'Unavailable' (11 caratteri); il widget di testo di script 104
(tipo 0x12d, nessun a-capo automatico) non va a capo, e il merge dei locals (tools/locals.py) ci ha messo il testo
Xbox da 367..456 caratteri. Le stringhe lunghe del PC stock (es. id 13, 59, 63) vanno a capo o per widget con
larghezza o per '\\n' esplicito (23 stringhe stock ne contengono).

Fix (solo dati, nessuna modifica a DRM/exe): '\\n' esplicito, a capo greedy per parole a WIDTH caratteri, sulle
stringhe degli id DESC_IDS piu' lunghe di WIDTH. Gli altri id restano byte-identici (verificato).

Uso: tools/venv/bin/python -I tools/locals_wrap_desc.py SRC_LOCAL_DIR OUT_LOCAL_DIR [WIDTH]
     SRC_LOCAL_DIR = cartella con locals.bin_001/002/004/008/016/032 (es. work/baseline/B85/mods/local)
     OUT_LOCAL_DIR = cartella NUOVA (rifiuta di sovrascrivere); scrive anche md5.txt e REPORT.txt
Installazione (decide l'utente): copiare i locals.bin_* in <gamedir>\\mods\\local\\ ; revert = rimettere i vecchi.
"""
import sys, os, struct, hashlib, textwrap
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import locals as L

DESC_IDS = (456, 457, 458, 459, 460, 461)   # descrizioni missione 1..6 (PC ids; 458..461 = 'Unavailable')
WIDTH = 52                                   # ~740 px a ~14 px/carattere: dentro la meta' destra (centro x=8, largh. ~16 unita')
FILES = ('001', '002', '004', '008', '016', '032')

def wrap(s, width):
    t = s.decode('utf-8')
    if len(t) <= width or '\n' in t:
        return s
    lines = textwrap.wrap(t, width=width, break_long_words=False, break_on_hyphens=False)
    return '\n'.join(lines).encode('utf-8')

def process(raw, width, ids=DESC_IDS):
    lang, st, offs = L.parse(raw, 'le')
    new = list(st)
    changed = []
    for i in ids:
        if i < len(st) and offs[i] != 0:
            w = wrap(st[i], width)
            if w != st[i]:
                new[i] = w; changed.append(i)
    return lang, st, offs, new, changed

def main():
    src, out = sys.argv[1], sys.argv[2]
    width = int(sys.argv[3]) if len(sys.argv) > 3 else WIDTH
    if os.path.exists(out) and os.listdir(out):
        sys.exit('OUT_LOCAL_DIR non vuota: rifiuto di sovrascrivere ' + out)
    os.makedirs(out, exist_ok=True)
    rep, md5s = [], []
    for sfx in FILES:
        raw = open(os.path.join(src, 'locals.bin_' + sfx), 'rb').read()
        lang, st, offs, new, changed = process(raw, width)
        # controllo di round-trip: stesso scrittore, nessuna modifica -> byte-identico al file di partenza
        ident = L.write_pc(lang, st, offs)
        assert ident == raw, 'write_pc non riproduce byte-exact %s: non posso garantire che gli altri id restino invariati' % sfx
        b = L.write_pc(lang, new, offs)
        back = L.parse(b, 'le')[1]
        assert len(back) == len(st)
        diff = [i for i in range(len(st)) if back[i] != st[i]]
        assert diff == changed, (sfx, diff, changed)
        assert all(back[i].replace(b'\n', b' ') == st[i] for i in changed), 'il testo cambia oltre agli a-capo'
        # nessuna riga oltre width
        mx = max((max(len(r) for r in back[i].decode('utf-8').split('\n')) for i in changed), default=0)
        open(os.path.join(out, 'locals.bin_' + sfx), 'wb').write(b)
        md5s.append('%s  locals.bin_%s' % (hashlib.md5(b).hexdigest(), sfx))
        rep.append('locals.bin_%s lang %d: id cambiati %s, righe max %d car., byte %d -> %d'
                   % (sfx, lang, changed, mx, len(raw), len(b)))
        for i in changed:
            rep.append('   id %d (%d righe):\n%s' % (i, back[i].count(b'\n') + 1,
                       '\n'.join('      | ' + r for r in back[i].decode('utf-8').split('\n'))))
    open(os.path.join(out, 'md5.txt'), 'w').write('\n'.join(md5s) + '\n')
    open(os.path.join(out, 'REPORT.txt'), 'w').write(
        'sorgente: %s\nWIDTH=%d DESC_IDS=%s\nround-trip identita\' write_pc: OK (6/6)\n' % (src, width, DESC_IDS) + '\n'.join(rep) + '\n')
    print(open(os.path.join(out, 'REPORT.txt')).read())

if __name__ == '__main__':
    main()
