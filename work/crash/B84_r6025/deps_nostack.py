"""Durata un livello sopra le texture, dal solo tap probe_texlife: (A) materiali liberati ancora puntati da un DRM residente,
(B) ShaderLib liberate ancora puntate da un materiale vivo.

Uso: tools/venv/bin/python -I work/crash/B84_r6025/deps_nostack.py TAP.tsv BASELINE

Stesso contratto delle texture [CODICE, DIAGNOSI.md par.3]: chi PUNTA (idref, gruppo 4 di FUN_0054ec60) non tiene riferimenti;
a conteggio 0 l'oggetto e' liberato (materiale: buffer dati 0x550970; lib: 0x550e00) e il puntatore resta nel buffer di chi punta.
(A) Residenza di un DRM al tempo s = TUTTE le texture che contiene vive a s (creata, non distrutta; dal tap, non dal log).
    Violazione A = materiale M rilasciato a r (sonda 4), DRM D che punta M senza contenerlo, D residente a r e alla fine.
(B) Violazione B = lib L rilasciata a r (sonda 5), materiale vivo da prima di r fino alla fine che punta L (idref tipo 9),
    non ricreato dopo r.
Limiti: DRM senza texture -> residenza ignota (contati); PERSI > 0 -> assenza non conclusiva.
"""
import sys, os, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', 'tools')))
import drm, drm_reloc as R
import texlife_analyze as T


def index(B):
    M = os.path.join(HERE, '..', '..', 'baseline', B, 'mods')
    D = {}
    for root, _, fs in os.walk(M):
        for n in fs:
            if not n.endswith('.drm'):
                continue
            p = os.path.join(root, n); rel = os.path.relpath(p, M)
            try:
                secs = drm.sections_with_data(drm.cdrm_decode(open(p, 'rb').read(), 'le'), 'le')[1]
            except Exception:
                continue
            has = collections.defaultdict(set); refs = collections.defaultdict(set)   # tipo -> id ; tipo -> {(id puntato, sez)}
            for s in secs:
                has[s['type']].add(s['id'])
            for s in secs:
                if not s['data'] or not s['reloc']:
                    continue
                for t, o in R.parse(s['reloc'], 'le').idref:
                    if t in (9, 10):
                        refs[t].add((struct.unpack_from('<I', s['data'], o)[0], (s['type'], s['id'])))
            D[rel] = (has, refs)
    return D


def main():
    tap, B = sys.argv[1], sys.argv[2]
    ev, persi = T.read_tap(tap)
    lost = sum(int(x[2].split()[-1]) for x in persi if x[2].split()[-1].isdigit())
    end = max(e['seq'] for e in ev) + 1
    print('eventi %d PERSI %d tagliati %s' % (len(ev), lost, T.capped(tap, ev)))
    texlife = collections.defaultdict(list)  # id -> [(create_seq, destroy_seq|None)]
    addr = {}
    for e in ev:
        if e['pid'] == 0 and e['a'][3] == 0x551f98:
            addr[e['ecx']] = (e['a'][9], len(texlife[e['a'][9]])); texlife[e['a'][9]].append([e['seq'], None])
        elif e['pid'] == 1 and e['ecx'] - 4 in addr:
            i, k = addr.pop(e['ecx'] - 4); texlife[i][k][1] = e['seq']
    def tex_alive(i, s):
        return any(c < s and (d is None or d > s) for c, d in texlife.get(i, []))
    Dx = index(B)
    def resident(rel, s):
        tx = Dx[rel][0].get(5, set())
        return None if not tx else all(tex_alive(i, s) for i in tx)
    matc = collections.defaultdict(list); matr = collections.defaultdict(list)
    for e in ev:
        if e['pid'] == 6 and e['a'][2] == 0x551e39: matc[e['a'][9]].append(e['seq'])
        elif e['pid'] == 4: matr[e['a'][5]].append(e['seq'])
    libr = [(e['seq'], e['a'][5]) for e in ev if e['pid'] == 5]
    # (A)
    va, unk = [], 0
    for m, rs in matr.items():
        for r in rs:
            for rel, (has, refs) in Dx.items():
                if m in has.get(10, ()):
                    continue
                who = [sec for i, sec in refs.get(10, ()) if i == m]
                if not who:
                    continue
                a0, a1 = resident(rel, r), resident(rel, end)
                if a0 is None:
                    unk += 1; continue
                if a0 and a1:
                    again = [c for c in matc.get(m, []) if c > r]
                    va.append((r, m, rel, who[:3], again[:2]))
    print('(A) rilasci materiale %d; violazioni %d; DRM senza texture (residenza ignota) %d' % (
        sum(len(v) for v in matr.values()), len(va), unk))
    for v in sorted(va)[:40]:
        print('   seq %d mat %d rilasciato; %s RESIDENTE prima e alla fine, lo punta da %s; ricreato %s' % v)
    # (B)
    mrefs = collections.defaultdict(set)
    for rel, (has, refs) in Dx.items():
        for i, sec in refs.get(9, ()):
            if sec[0] == 10:
                mrefs[sec[1]].add(i)
    alive_end = {m for m, cs in matc.items() if not any(x > cs[-1] for x in matr.get(m, []))}
    vb = []
    for r, L in libr:
        for m in alive_end:
            c = matc[m][-1]
            if c < r and L in mrefs.get(m, ()):
                vb.append((r, L, m, c))
    print('(B) rilasci ShaderLib %d; violazioni %d' % (len(libr), len(vb)))
    for v in vb[:40]:
        print('   seq %d lib %d rilasciata; materiale %d vivo (creato seq %d, mai rilasciato) la punta' % v)
    if lost:
        print('ATTENZIONE: PERSI > 0 -> assenza non conclusiva')
    return 1 if (va or vb) else 0


if __name__ == '__main__':
    sys.exit(main())
