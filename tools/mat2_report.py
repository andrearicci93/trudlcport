"""mat2 (B): classification table of DLC1 materials -> work/ws/mat2/out/params_count.tsv  (input: rows.pkl from mat2_params_count scan)."""
import sys, os, pickle, collections
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'ws')
rows = pickle.load(open(os.path.join(ROOT, 'mat2', 'scratch', 'rows.pkl'), 'rb'))
tsv = {}
for ln in open(os.path.join(ROOT, 'mat', 'out', 'materials.tsv')).read().splitlines()[1:]:
    f = ln.split('\t'); tsv[int(f[0])] = dict(verdict=f[1], units=f[4], meshes=f[5])
out = []; st = collections.Counter()
for r in rows:
    t = tsv.get(r['mid'], {}); units = t.get('units', '')
    n, nx, um, ul = r['npc'], r['nx'], r['umax'], r['umin']
    fed = min(n, nx); zero_reads = [i for i in r['usedset'] if i >= nx] if n > nx else []
    unver = r['unver']
    if n < ul: cc, why = 'rotto', 'n_pc<%d: ogni permutazione legge oltre la fine' % ul
    elif n < um: cc, why = 'rotto-parziale', 'n_pc=%d, alcune permutazioni PS leggono fino a c%d (%d vec4)' % (n, 100 + um - 1, um)
    elif unver and zero_reads: cc, why = 'sospetto-alto', 'UNVERIFIED padded %d->%d: PS legge %d vec4 senza sorgente Xbox (azzerati): c%s' % (nx, n, len(zero_reads), ','.join(str(100 + i) for i in zero_reads))
    elif unver: cc, why = 'sospetto', ('UNVERIFIED troncato %d->%d' % (nx, n) if n < nx else 'UNVERIFIED %d->%d' % (nx, n)) + ': conteggio coerente col bytecode, layout non verificato'
    else: cc, why = 'OK', 'n_pc==bytecode (%d)%s' % (um, '' if n == nx else ' (rule/identita: %d->%d)' % (nx, n))
    risk = {'OK': 'nessuno', 'sospetto-alto': 'nessun crash (letture entro il conteggio); i vec4 azzerati letti dal PS (scale/esponenti?) possono dare superficie nera/collassata: visivo', 'sospetto': 'nessun crash (letture entro il conteggio); rischio solo visivo (colore/luce)', 'rotto-parziale': 'c110 oltre il conteggio: se il motore carica n_pc, c110 stantio; se carica il conteggio CTAB, legge 16 B dopo il blocco ma DENTRO la sezione (21210: 80 B seguono) => nessuna lettura fuori sezione; layout params comunque sbagliato (visivo)', 'rotto': 'letture oltre la fine'}[cc]
    out.append((r['mid'], units, t.get('meshes', ''), t.get('verdict', ''), nx, n, um, ul, r['bpn'] if r['bpn'] is not None else '', 'U' if unver else '', cc, why, risk))
    st[(bool(units), cc)] += 1
hdr = 'material\tdlc1_units\tmeshes\tmat_verdict\tn_xbox\tn_pc\tbytecode_need_max\tbytecode_need_min\tsurrogate_base_n\tunverified\tclass\treason\tcrash_risk'
open(os.path.join(ROOT, 'mat2', 'out', 'params_count.tsv'), 'w').write(hdr + '\n' + '\n'.join('\t'.join(str(x) for x in o) for o in out) + '\n')
for k, v in sorted(st.items()): print(k, v)
