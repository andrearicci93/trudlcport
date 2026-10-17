"""Analisi di durata texture <- materiali dal solo tap della sonda probe_texlife (exe 964f5714), quando lo stack al crash manca.

Uso: tools/venv/bin/python -I work/crash/B84_r6025/texlife_nostack.py TAP.tsv BASELINE

Contratto [CODICE, DIAGNOSI.md par.3]: il materiale (tipo 10) viene creato una volta per id (prima copia vince); in quel momento la
relocation idref tipo 5 scrive nel buffer il puntatore all'oggetto texture registrato per quell'id. Il materiale non tiene
riferimenti alla texture. Quindi per ogni materiale VIVO al crash:
  violazione     = quell'oggetto ha un tex_destroy (sonda 1, ecx-4) prima del crash
                   (anche se l'id T e' stato poi ricreato: lo slot punta ancora al vecchio oggetto).
Vivo = mat_create senza mat_release0 (sonda 4, a5 = id) successivo.
Legame: oggetto dell'id T vivo alla creazione del materiale, altrimenti il primo creato dopo (relocation a fine DRM).
Riferimenti materiale -> texture letti dai DRM della baseline (tutti gli idref tipo 5; 'slot' = cade nell'array data+0x54).
Limiti: materiali non presenti nei DRM della baseline (gioco base) non hanno riferimenti noti -> contati a parte;
         con PERSI > 0 ogni conclusione per assenza e' UNKNOWN.
"""
import sys, os, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', 'tools')))
import drm, drm_reloc as R
import texlife_analyze as T


def mat_refs(B):
    """{id materiale: {id texture: (slot?, [drm])}} da tutte le copie nei DRM della baseline."""
    M = os.path.join(HERE, '..', '..', 'baseline', B, 'mods')
    out = collections.defaultdict(dict)
    for root, _, fs in os.walk(M):
        for n in fs:
            if not n.endswith('.drm'):
                continue
            p = os.path.join(root, n); rel = os.path.relpath(p, M)
            try:
                secs = drm.sections_with_data(drm.cdrm_decode(open(p, 'rb').read(), 'le'), 'le')[1]
            except Exception:
                continue
            for s in secs:
                if s['type'] != 10 or not s['data'] or not s['reloc']:
                    continue
                d = s['data']; r = R.parse(s['reloc'], 'le')
                slots = set()
                for po, tgt in r.internal:
                    b = po - 0x54
                    if b >= 0 and b + 0x53 <= len(d):
                        nn = max(d[b + 0x51], d[b + 0x52])
                        slots |= {tgt + 16 * k for k in range(nn)}
                for t, o in r.idref:
                    if t == 5:
                        tid = struct.unpack_from('<I', d, o)[0]
                        sl, ds = out[s['id']].get(tid, (False, []))
                        out[s['id']][tid] = (sl or o in slots, ds + [rel])
    return out


def main():
    tap, B = sys.argv[1], sys.argv[2]
    ev, persi = T.read_tap(tap)
    lost = sum(int(x[2].split()[-1]) for x in persi if x[2].split()[-1].isdigit())
    cap = T.capped(tap, ev)
    cnt = collections.Counter(e['pid'] for e in ev)
    print('eventi %d per sonda %s; PERSI %d; tagliati %s' % (len(ev), dict(sorted(cnt.items())), lost, cap))
    bad = [e for e in ev if (e['pid'] == 0 and e['a'][3] != 0x551f98) or (e['pid'] == 6 and e['a'][2] != 0x551e39)]
    print('creazioni non di sezione (escluse): %d' % len(bad))
    end = max(e['seq'] for e in ev)
    tex_by_id = collections.defaultdict(list)   # id -> [(seq, addr)]
    destroyed = collections.defaultdict(list)   # addr -> [seq]
    created_at = collections.defaultdict(list)  # addr -> [(seq, id)]
    mats = {}                                   # id -> seq creazione (ultima)
    mat_rel = collections.defaultdict(list)
    rel = collections.defaultdict(list)         # id -> [(seq, 'contato'|'forzato', chiamante)]
    for e in ev:
        p, a = e['pid'], e['a']
        if p == 0 and a[3] == 0x551f98:
            tex_by_id[a[9]].append((e['seq'], e['ecx'])); created_at[e['ecx']].append((e['seq'], a[9]))
        elif p == 1:
            destroyed[e['ecx'] - 4].append(e['seq'])
        elif p == 6 and a[2] == 0x551e39:
            mats[a[9]] = e['seq']
        elif p == 4:
            mat_rel[a[5]].append(e['seq'])
        elif p in (2, 3):
            rel[a[5]].append((e['seq'], 'contato' if p == 2 else 'forzato', a[4]))
    alive = {m: s for m, s in mats.items() if not any(x > s for x in mat_rel.get(m, []))}
    refs = mat_refs(B)
    known = [m for m in alive if m in refs]
    print('materiali creati %d, vivi al crash %d (con riferimenti noti nella baseline %d, base/ignoti %d)' % (
        len(mats), len(alive), len(known), len(alive) - len(known)))
    viol, unbound, nref = [], 0, 0
    bound_after = [0]
    for m in known:
        ms = alive[m]
        for tid, (slot, ds) in refs[m].items():
            nref += 1
            # oggetto legato: quello dell'id T vivo alla creazione del materiale; altrimenti il primo creato dopo
            # (le relocation del DRM sono applicate a sezioni gia' registrate, l'ordine interno al DRM non e' noto)
            live = [(s, ad) for s, ad in tex_by_id.get(tid, []) if s < ms and not any(s < x < ms for x in destroyed.get(ad, []))]
            nxt = [(s, ad) for s, ad in tex_by_id.get(tid, []) if s > ms]
            if live:
                s0, ad = live[-1]
            elif nxt:
                s0, ad = nxt[0]; bound_after[0] += 1
            else:
                unbound += 1; continue
            dd = [x for x in destroyed.get(ad, []) if x > max(s0, ms)]
            if dd:
                later = [(s, a2) for s, a2 in tex_by_id.get(tid, []) if s > dd[0]]
                viol.append((m, ms, tid, slot, ad, s0, dd[0], later[:2], rel.get(tid, [])[-3:], ds[:2]))
    print('riferimenti esaminati %d; legati a un oggetto creato dopo il materiale %d; texture mai creata nella run %d' % (nref, bound_after[0], unbound))
    print('VIOLAZIONI (oggetto texture legato al materiale vivo, distrutto prima del crash): %d' % len(viol))
    for v in sorted(viol, key=lambda v: v[6])[:60]:
        m, ms, tid, slot, ad, s0, ds_, later, rl, dr = v
        print('  mat %d (creato seq %d) -> tex %d %s obj %08x creato seq %d DISTRUTTO seq %d (crash ~%d); ricreato %s; rilasci %s; in %s' % (
            m, ms, tid, 'SLOT' if slot else 'altro', ad, s0, ds_, end, ['%d@%08x' % x for x in later],
            ['%d %s %08x' % r for r in rl], dr))
    if lost or (cap is None) or cap:
        print('ATTENZIONE: perdite/tagli presenti -> assenza di violazioni NON conclusiva')
    return 1 if viol else 0


if __name__ == '__main__':
    sys.exit(main())
