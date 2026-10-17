"""Controllo di durata delle texture puntate dai materiali (classe di difetto del crash R6025 / AV 0x5076fa).

Contratto del motore (PC 56d1ce2d, verificato nel disassembly, vedi DIAGNOSI.md):
  - la cache texture e' globale per id (gestore tipo 5 = DAT_00c56fdc, vtable 0x84cb84);
  - ogni DRM che CONTIENE la sezione texture T tiene un riferimento (0x551f30: crea o conta++);
  - allo scarico il riferimento cala (0x550c20: conta--, a 0 distruttore virtuale + rimozione nodo);
  - un materiale che PUNTA a T tramite idref (gruppo reloc 4, FUN_0054ec60 -> +0x44/+0x30) NON tiene riferimenti.
  => un materiale residente e' sicuro solo se ogni texture puntata resta contenuta in almeno un DRM residente.

Uso:
  tools/venv/bin/python -I work/crash/B84_r6025/tex_lifetime_check.py BASELINE scenario.json [--selftest]
scenario.json: {"resident": [relpath mods...], "freed": [relpath mods...], "base_resident": [nomi bigfile...]}
Uscita: elenco (DRM residente, materiale, texture) la cui texture e' contenuta SOLO in DRM liberati  -> VIOLAZIONE;
        e quelle contenute in nessun DRM noto (residente o liberato)                                     -> IGNOTA.
Exit code 1 se ci sono violazioni.
"""
import sys, os, struct, json
TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools')
sys.path.insert(0, os.path.abspath(TOOLS))
import drm, drm_reloc as R


TYPES = (5,)   # --types 5,10,12 per estendere ad altri gestori con cache globale per id


def load_drm(path):
    """(contenuti, riferimenti): contenuti = {(tipo,id)}; riferimenti = [((tipo,id) sezione, [(tipo,id) puntati])]."""
    secs = drm.sections_with_data(drm.cdrm_decode(open(path, 'rb').read(), 'le'), 'le')[1]
    tex = {(s['type'], s['id']) for s in secs if s['type'] in TYPES}
    mats = []
    for s in secs:
        if not s['data'] or not s['reloc']:
            continue
        r = R.parse(s['reloc'], 'le')
        # solo il gruppo 'idref' (puntatore); 'idref_a' scrive l'id, non un puntatore (0x54ec60, gruppo puVar2[2])
        ptr = sorted({(t, struct.unpack_from('<I', s['data'], o)[0]) for t, o in r.idref if t in TYPES})
        if ptr:
            mats.append(((s['type'], s['id']), ptr))
    return tex, mats


def check(drms, resident, freed, base_tex=frozenset()):
    """drms: {nome: (tex, mats)}. Restituisce (violazioni, ignote)."""
    held_r = set(base_tex)
    for n in resident:
        held_r |= drms[n][0]
    held_f = {}
    for n in freed:
        for t in drms[n][0]:
            held_f.setdefault(t, []).append(n)
    viol, unk = [], []
    for n in resident:
        for mid, ptr in drms[n][1]:
            for t in ptr:
                if t in held_r:
                    continue
                (viol if t in held_f else unk).append((n, mid, t, held_f.get(t, [])))
    return viol, unk


def selftest():
    """Mutazione negativa sintetica: la texture 7 esiste solo nel DRM liberato -> deve risultare violazione."""
    drms = {'A': ({1}, [(100, [1, 7])]), 'B': ({7}, []), 'C': ({9}, [(200, [9])])}
    v, u = check(drms, ['A', 'C'], ['B'])
    assert v == [('A', 100, 7, ['B'])] and u == [], (v, u)
    v, u = check(drms, ['A', 'B', 'C'], [])
    assert v == [] and u == [], (v, u)
    drms['A'] = ({1}, [(100, [1, 8])])
    v, u = check(drms, ['A', 'C'], ['B'])
    assert v == [] and u == [('A', 100, 8, [])], (v, u)
    print('selftest OK')


def main():
    global TYPES
    if '--types' in sys.argv:
        i = sys.argv.index('--types'); TYPES = tuple(int(x) for x in sys.argv[i + 1].split(',')); del sys.argv[i:i + 2]
    if '--selftest' in sys.argv:
        selftest()
        return 0
    B, scen = sys.argv[1], json.load(open(sys.argv[2]))
    M = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'baseline', B, 'mods')
    names = scen['resident'] + scen['freed']
    drms = {}
    for n in names:
        p = os.path.join(M, n)
        if not os.path.exists(p):
            print('MANCANTE nella baseline:', n)
            continue
        drms[n] = load_drm(p)
    res = [n for n in scen['resident'] if n in drms]
    fre = [n for n in scen['freed'] if n in drms]
    base_tex = set(scen.get('base_tex', []))
    v, u = check(drms, res, fre, base_tex)
    print('baseline %s tipi %s: residenti %d, liberati %d, sezioni residenti con idref %d' % (
        B, TYPES, len(res), len(fre), sum(len(drms[n][1]) for n in res)))
    print('VIOLAZIONI (texture puntata contenuta solo in DRM liberati): %d' % len(v))
    for n, mid, t, h in v:
        print('  %-50s sez %-12s -> %-12s solo in %s' % (n, mid, t, h))
    print('IGNOTE (texture puntata non contenuta in nessun DRM dello scenario): %d' % len(u))
    for n, mid, t, h in u[:40]:
        print('  %-50s sez %-12s -> %s' % (n, mid, t))
    return 1 if v else 0


if __name__ == '__main__':
    sys.exit(main())
