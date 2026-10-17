# Candidato DLC1: parte dai locals INSTALLATI (work/dlc_images), aggiunge in coda (ids >= installed_n) i testi DLC1
# (pack1 = costumi, che contengono gli hint DLC1 1284..1375) dove TU/DLC2 scrive un testo diverso sullo stesso indice.
# Nessun id esistente viene modificato. Produce locals.bin_* + md5.txt + locmap_dlc1_xbox_to_pc.json in out/.
import sys, os, pickle, struct, hashlib, json, collections
sys.path.insert(0, '/path/to/trudlcport/tools')
import locals as L
H = '/path/to/trudlcport/work/ws/hints'
OUT = H + '/out'; INST = '/path/to/trudlcport/work/dlc_images/local/mods/local'
T = pickle.load(open(H + '/tables.pkl', 'rb'))
V = {src: {s: (T[src][s]['lang'], T[src][s]['strings']) for s in T[src]} for src in T}
L.files_cache['pcpatch'] = {s: T['pcpatch'][s]['raw'] for s in T['pcpatch']}
m, info = L.build_map(V)
SPECS = [0xfffff7e1, 0xfffff7e2, 0xfffff7e8, 0xfffff7e4, 0xfffff7f0, 0xffffffe0]
def suffix(s): return (s & 0x1f) if s != 0xffffffe0 else 32
def write_keep(lang, strings, missing):
    n = len(strings); hdr = 8 + 4 * n; body = bytearray(); offs = []; seen = {}
    for i, s in enumerate(strings):
        if i == 0 or missing[i]: offs.append(0); continue
        if s in seen: offs.append(seen[s]); continue
        offs.append(hdr + len(body)); seen[s] = offs[-1]; body += s + b'\0'
    return struct.pack('<II', lang, n) + struct.pack('<%dI' % n, *offs) + bytes(body)
# 1) installed tables
inst = {}
for s in SPECS:
    raw = open(os.path.join(INST, 'locals.bin_%03d' % suffix(s)), 'rb').read()
    lang, st, offs = L.parse(raw, 'le')
    miss = [i == 0 or offs[i] == 0 for i in range(len(st))]
    inst[s] = (lang, st, miss, raw)
N0 = len(inst[SPECS[0]][1]); assert all(len(inst[s][1]) == N0 for s in SPECS), 'installed lengths differ'
print('installed n per table', N0)
# 2) DLC1 variant indices: pack1 text present, and TU text differs (TU missing or different) in ANY language
p1 = V['pack1']; tu = V['tu']
def present(src, s, x):
    return x < len(T[src][s]['offs']) and T[src][s]['offs'][x] != 0 and x != 0
var_x = []
per_lang = collections.Counter()
for x in range(1284, len(p1[SPECS[0]][1])):
    for s in SPECS:
        if present('pack1', s, x):
            a = T['pack1'][s]['strings'][x]
            b = T['tu'][s]['strings'][x] if present('tu', s, x) else None
            if b is None or b != a:
                per_lang[suffix(s)] += 1
                if x not in var_x: var_x.append(x)
var_x.sort()
print('DLC1 variant indices (pack1 vs TU differ in >=1 lang):', len(var_x), 'per language', dict(per_lang))
# 3) new PC ids for variants, appended after the installed table
Q = {x: N0 + k for k, x in enumerate(var_x)}
newn = N0 + len(var_x)
# 4) per language: strings = installed + variants
out = {}
stats = {}
for s in SPECS:
    lang, st, miss, raw = inst[s]
    S = list(st); M = list(miss) + [False] * len(var_x)
    S += [b''] * len(var_x)
    nchg = 0
    for x in var_x:
        q = Q[x]
        if present('pack1', s, x): S[q] = T['pack1'][s]['strings'][x]
        elif present('pack10', s, x): S[q] = T['pack10'][s]['strings'][x]   # fallback DLC1 (mai TU/DLC2)
        else: M[q] = True
    out[s] = (lang, S, M)
    b = write_keep(lang, S, M)
    stats[suffix(s)] = len(b)
    fn = os.path.join(OUT, 'locals.bin_%03d' % suffix(s))
    open(fn, 'wb').write(b)
    # selftests: installed ids unchanged, missing flags unchanged, new ids as intended
    back = L.parse(b, 'le')[1]
    bmiss = [i == 0 or L.parse(b, 'le')[2][i] == 0 for i in range(len(back))]
    same_base = all(back[i] == st[i] and bmiss[i] == miss[i] for i in range(N0))
    new_ok = all(back[Q[x]] == S[Q[x]] for x in var_x)
    print('wrote', fn, 'n', len(back), 'installed ids unchanged', same_base, 'variant ids ok', new_ok, 'changed_installed_ids', sum(1 for i in range(N0) if back[i] != st[i]))
# 5) locmap DLC1: Xbox index -> PC id (variants get their own id), others as the shared map
mapd = {str(k): (Q[k] if k in Q else v) for k, v in sorted(m.items())}
json.dump({'rule': 'DLC1 pack10/pack1 data: x in var_x -> appended id Q[x] (DLC1 text); all others = locmap_xbox_to_pc',
           'var_x': var_x, 'Q': {str(k): v for k, v in Q.items()}, 'map': mapd, 'installed_n': N0, 'new_n': newn},
          open(OUT + '/locmap_dlc1_xbox_to_pc.json', 'w'), indent=0)
print('locmap_dlc1 written; new table n', newn)
# 6) md5
lines = []
for s in SPECS:
    fn = 'locals.bin_%03d' % suffix(s)
    lines.append('%s  %s' % (hashlib.md5(open(os.path.join(OUT, fn), 'rb').read()).hexdigest(), fn))
open(OUT + '/md5.txt', 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
pickle.dump({'var_x': var_x, 'Q': Q}, open(H + '/dlc1_var.pkl', 'wb'))
