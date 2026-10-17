"""Analisi di una run con la sonda work/ws/tap/probe_texlife (exe 964f5714) + stack grezzo al crash.

Uso:
  tools/venv/bin/python -I work/crash/B84_r6025/texlife_analyze.py TAP.tsv STACK_RAW.tsv BASELINE

TAP.tsv        = work/taps/<RunId>/tap.tsv (vm_tap_reader.ps1 con -Sites work/ws/tap/probe_texlife/sites_patched.tsv;
                 il lettore deve stampare 10 argomenti sonda: versione 16/10, backup .bak_texlife)
STACK_RAW.tsv  = tools/vm_stackdump.ps1 -RawBytes 0x1000 preso con il processo fermo sulla finestra R6025
BASELINE       = baseline installata (per mappare id -> DRM che li contengono)

Sonde (id: va, dato) - offset verificati nel disassembly 56d1ce2d, vedi DIAGNOSI.md:
  0 tex_create   0x5071d2  ecx = nuovo oggetto texture,   a3 = 0x551f98 (controllo), a9 = id sezione tipo 5
  1 tex_destroy  0x515dd6  ecx = obj+4 (distruttore effettivo, dopo la coda differita 0x515690), a2 = ritorno nello svuotatore
  2 h_release0   0x550c62  conteggio a 0 nel gestore 0x84cb84 (tipo 5 o 12): ecx = gestore+4, a4 = chiamante, a5 = id
  3 h_forced     0x550d28  distruzione forzata (scarico di DRM a caricamento incompleto): come 2
  4 mat_release0 0x5509cf  materiale a conteggio 0: a4 = chiamante, a5 = id
  5 lib_release0 0x550e44  ShaderLib a conteggio 0: a4 = chiamante, a5 = id
  6 mat_create   0x50719d  ecx = nuovo oggetto materiale, a2 = 0x551e39 (controllo), a9 = id sezione tipo 10
Crash: frame vivo ancorato a 0x507701 (R = X+0x10) o, per l'AV, R = esp+0xc; [R] = 0x505b02; [R+8] = puntatore dello slot,
       [R+0x24] = variabile locale L0 di FUN_00505a90 = oggetto materiale (this).
"""
import sys, os, re, collections
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'tools')))
import drm

GESTORE5 = 0xc56fdc  # DAT_00c56fdc: puntatore all'istanza; ecx = istanza+4 (non noto staticamente: si riporta)
PROBE = re.compile(r'probe(\d+) ecx=([0-9a-f]{8}) edx=([0-9a-f]{8}) args((?: 0x[0-9a-f]{8})+)')


def read_tap(p):
    ev, persi, last = [], [], -1
    for line in open(p, errors='replace'):
        c = line.rstrip('\n').split('\t')
        if len(c) >= 6 and 'PERSI' in c[5]:
            persi.append((c[0], c[1], c[5], last))   # last = seq dell'ultimo evento scritto prima della perdita
        elif c[0].isdigit():
            last = int(c[0])
        if len(c) < 6:
            continue
        m = PROBE.search(c[5])
        if not m:
            continue
        a = [int(x, 16) for x in m.group(4).split()]
        ev.append(dict(seq=int(c[0]), t=c[1], ret=c[3], pid=int(m.group(1)), ecx=int(m.group(2), 16), a=a))
    return ev, persi


def capped(tap, ev):
    """Eventi sonda non scritti per il tetto -MaxPerSite (il lettore li conta solo in tap_summary.tsv): {ret: mancanti}.
    None se il riepilogo manca (allora la completezza e' ignota)."""
    p = os.path.join(os.path.dirname(os.path.abspath(tap)), 'tap_summary.tsv')
    if not os.path.exists(p):
        return None
    tot = {}
    for line in open(p, errors='replace'):
        c = line.rstrip('\n').split('\t')
        if len(c) >= 3 and c[2].isdigit():
            tot[c[0]] = int(c[2])
    wr = collections.Counter(e['ret'] for e in ev)
    return {r: tot.get(r, n) - n for r, n in wr.items() if tot.get(r, n) > n}


def read_stack(p):
    """{(thread, indirizzo): valore} e {thread: esp} dalle righe CTX."""
    w, ctx = {}, {}
    for line in open(p, errors='replace'):
        c = line.rstrip('\n').split('\t')
        if len(c) >= 5 and c[0].startswith('T') and c[4] == 'CTX':
            ctx[c[0]] = int(c[2], 16)
        elif len(c) >= 3 and c[0].startswith('T'):
            try:
                w[(c[0], int(c[1], 16))] = int(c[2], 16)
            except ValueError:
                pass
    return w, ctx


def anchor(w, ctx):
    """R = indirizzo del ritorno 0x505b02 del frame VIVO di FUN_005076e0.
    _purecall: X = parola 0x507701 (ritorno di 'call eax' a 0x5076ff) vicino a esp, R = X+0x10.
    AV a 0x5076fa (prima della call): R = esp+0xc. In entrambi i casi [R] deve valere 0x505b02."""
    out = []
    for th, esp in ctx.items():
        for a in range(esp, esp + 0x1000, 4):
            if w.get((th, a)) == 0x507701 and w.get((th, a + 0x10)) == 0x505b02:
                out.append((th, a + 0x10, 'purecall')); break
        else:
            if w.get((th, esp + 0xc)) == 0x505b02:
                out.append((th, esp + 0xc, 'AV'))
    return out


def holders(B, typ, ids):
    M = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'baseline', B, 'mods')
    out = collections.defaultdict(list)
    for root, _, fs in os.walk(M):
        for n in fs:
            if not n.endswith('.drm'):
                continue
            p = os.path.join(root, n)
            try:
                secs = drm.sections_with_data(drm.cdrm_decode(open(p, 'rb').read(), 'le'), 'le')[1]
            except Exception:
                continue
            for s in secs:
                if s['type'] == typ and s['id'] in ids:
                    out[s['id']].append(os.path.relpath(p, M))
    return out


def main():
    tap, stk, B = sys.argv[1:4]
    ev, persi = read_tap(tap)
    print('eventi sonda %d; righe PERSI %d %s' % (len(ev), len(persi), persi[:3]))
    cnt = collections.Counter(e['pid'] for e in ev)
    print('per sonda:', dict(sorted(cnt.items())))
    # controlli degli offset (se falliscono, ogni conclusione e' UNKNOWN)
    bad0 = [e for e in ev if e['pid'] == 0 and e['a'][3] != 0x551f98]
    bad6 = [e for e in ev if e['pid'] == 6 and e['a'][2] != 0x551e39]
    good0 = cnt[0] - len(bad0); good6 = cnt[6] - len(bad6)
    print('tex_create: %d di sezione (a3==0x551f98), %d da altri chiamanti; mat_create: %d di sezione (a2==0x551e39), %d altri' % (
        good0, len(bad0), good6, len(bad6)))
    if good0 == 0 or good6 == 0:
        print('ESITO: UNKNOWN (nessun evento di creazione di sezione valido: offset sonda non confermati o sonde mute)')
        return 2
    lost = sum(int(x[2].split()[-1]) for x in persi if x[2].split()[-1].isdigit())
    cap = capped(tap, ev)
    if cap is None:
        print('tap_summary.tsv assente: completezza rispetto al tetto per sito ignota -> conclusioni per assenza UNKNOWN')
        lost += 1
    elif cap:
        print('TAGLIATI dal tetto -MaxPerSite (non in tap.tsv): %s -> conclusioni per assenza UNKNOWN' % cap)
        lost += sum(cap.values())
    life = collections.defaultdict(list)   # indirizzo -> [(seq, 'create'|'destroy', id|None, info)]
    for e in ev:
        if e['pid'] == 0:
            life[e['ecx']].append((e['seq'], 'create', e['a'][9] if e['a'][3] == 0x551f98 else None, 'tex' if e['a'][3] == 0x551f98 else 'tex_runtime ret %08x' % e['a'][3]))
        elif e['pid'] == 6:
            life[e['ecx']].append((e['seq'], 'create', e['a'][9] if e['a'][2] == 0x551e39 else None, 'mat' if e['a'][2] == 0x551e39 else 'mat_runtime ret %08x' % e['a'][2]))
        elif e['pid'] == 1:
            life[e['ecx'] - 4].append((e['seq'], 'destroy', None, 'svuotatore %08x' % e['a'][2]))
    for k in life: life[k].sort()
    W, ctx = read_stack(stk)
    anc = anchor(W, ctx)
    if not anc:
        print('ESITO: UNKNOWN (nessun frame vivo FUN_005076e0 ancorato a 0x507701/esp+0xc: crash altrove o RawBytes insufficiente)')
        return 2
    def state(addr):
        h = life.get(addr, [])
        cr = [x for x in h if x[1] == 'create']; de = [x for x in h if x[1] == 'destroy']
        if not cr: return 'mai_creato', None, h
        if de and de[-1][0] > cr[-1][0]: return 'distrutto', cr[-1], h
        if de: return 'ricreato', cr[-1], h
        return 'vivo', cr[-1], h
    for th, R, kind in anc:
        P, MO = W.get((th, R + 8)), W.get((th, R + 0x24))
        print('\n%s frame %s, R=%08x: texture slot P=%s  materiale obj=%s' % (th, kind, R,
              '%08x' % P if P is not None else '?', '%08x' % MO if MO is not None else '?'))
        if P is None or MO is None:
            print('  ESITO: UNKNOWN (parole R+8/R+0x24 assenti dal dump grezzo)'); continue
        sp, cp, hp = state(P); sm, cm, hm = state(MO)
        print('  storia P: %s' % hp[-6:]); print('  storia materiale: %s' % hm[-4:])
        T = cp[2] if cp else None; Mid = cm[2] if cm else None
        for e in ev:
            if e['pid'] in (2, 3) and T is not None and e['a'][5] == T:
                print('  rilascio id %d: %s seq %d chiamante %08x gestore+4 %08x' % (
                    T, 'FORZATO (0x550d28)' if e['pid'] == 3 else 'conteggio 0 (0x550c62)', e['seq'], e['a'][4], e['ecx']))
        if T is not None:
            print('  DRM che contengono texture %d: %s' % (T, holders(B, 5, {T}).get(T)))
        if Mid is not None:
            print('  DRM che contengono materiale %d: %s' % (Mid, holders(B, 10, {Mid}).get(Mid)))
        incerto = lost > 0
        if sp == 'distrutto':
            # anche 'distrutto' poggia su un'assenza: nessuna nuova creazione allo stesso indirizzo dopo la distruzione
            dseq = hp[-1][0]
            dopo = sum(int(x[2].split()[-1]) for x in persi if x[3] >= dseq and x[2].split()[-1].isdigit())
            capc = cap is None or any(e['pid'] in (0, 6) and e['ret'] in cap for e in ev)
            if dopo or capc:
                print('  ATTENZIONE: dopo la distruzione %d eventi persi%s: una ricreazione allo stesso indirizzo non e\' esclusa '
                      '-> esito DA CONFERMARE (non prova)' % (dopo, ', creazioni tagliate dal tetto o riepilogo assente' if capc else ''))
            forz = any(e['pid'] == 3 and T is not None and e['a'][5] == T for e in ev)
            print('  ESITO: P (%s) distrutto a seq %d dopo la creazione e ancora nello slot del materiale %s -> violazione di durata (%s)' % (
                cp[3], hp[-1][0], Mid, 'percorso forzato' if forz else 'percorso contato o non visto'))
        elif sp == 'ricreato':
            print('  ESITO: indirizzo P distrutto e poi riusato da una nuova creazione (%s): lo slot puo\' puntare a un oggetto '
                  'diverso da quello risolto; %s' % (cp, 'UNKNOWN per PERSI' if incerto else 'da esaminare con la sequenza completa'))
        elif sp == 'vivo':
            print('  ESITO: %s' % ('UNKNOWN (P vivo secondo il tap, ma PERSI=%d: la distruzione puo\' essere persa)' % lost if incerto
                  else 'P vivo -> non e\' la durata della texture: guardare dati/binding dello slot'))
        else:
            print('  ESITO: %s' % ('UNKNOWN (P mai visto creare, PERSI=%d)' % lost if incerto
                  else 'P non creato come texture: altra classe di oggetto nello slot'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
