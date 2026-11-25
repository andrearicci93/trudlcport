"""trusave_reset.py - (20/11/2026) crea una COPIA di un salvataggio TRU con lo stato di una unit azzerato (come al primo ingresso):
- toglie i blocchi 3/4 con unit di nascita = UNIT e i blocchi 2/5 delle sue intro (tranne gli oggetti in --keep, es. artefatti raccolti),
  compattando l'arena e aggiornando la fine usata (0x1357f4);
- azzera i dead bits delle intro della unit (tranne --keep);
- toglie gli stickies kind 0 delle intro della unit e kind 1 della unit (tranne quelli gia' presenti nel salvataggio --ref, impostati
  prima di entrare), compattando id e valori di ogni archivio;
- imposta il checkpoint del blocco di gioco (+0x90) a --cp; con --cp-unit NOME.drm e --cp-unit-id N il checkpoint e' di un'altra unit
  (es. il corridoio prima della sala): nome unit (+0x10, stringa con zeri fino a +0x90) e unit del giocatore (+0x1a8) cambiano;
- con --only uid,uid,...: tocca SOLO quelle intro (blocchi, dead bits, stickies kind 0), niente stickies kind 1 della unit
  (salvataggio "ibrido": resto della sala com'era);
- ricalcola CRC dei dati, della tabella e della testata. Verifica: rilettura, conteggi attesi, nessun altro byte cambiato fuori
  da arena/dead bits/stickies/checkpoint.
Scrive solo il file --out (mai il salvataggio di origine). Formato: trusave.py.
uso: trusave_reset.py --save IN --out OUT --baseline BL --unit-drm U.drm --unit 116 --cp 11696 [--keep oggetto,...] [--ref SAVE]"""
import sys, struct, collections
sys.path.insert(0, '/path/to/trudlcport/tools'); sys.path.insert(0, '/path/to/trudlcport/work/ws/machine_room')
import drm, unit_ids, trusave as T
a = sys.argv
def opt(k, d=None): return a[a.index(k) + 1] if k in a else d
IN, OUT, BL, UD, UID, CP = opt('--save'), opt('--out'), opt('--baseline'), opt('--unit-drm'), int(opt('--unit')), int(opt('--cp'))
KEEP = set(filter(None, opt('--keep', '').split(','))); REF = opt('--ref'); CPU, CPUID = opt('--cp-unit'), opt('--cp-unit-id')
assert OUT and OUT != IN
names = {}
for l in open('/path/to/trudlcport/work/baseline/%s/mods/tr8/pc-w/objectlist.txt' % BL, errors='ignore'):
    p = l.split(',', 1)
    if len(p) == 2 and p[0].strip().isdigit(): names[int(p[0])] = p[1].strip()
h, S = drm.sections_with_data(drm.cdrm_decode(open('/path/to/trudlcport/work/baseline/%s/mods/%s' % (BL, UD), 'rb').read(), 'le'), 'le')
intro = {}
for si, o in unit_ids.level_info(S, 'le')['intros']:
    d_ = S[si]['data']; intro[struct.unpack_from('<I', d_, o + 0x58)[0]] = names.get(struct.unpack_from('<H', d_, o + 0x50)[0], '?')
def intros_of(ud):
    h_, S_ = drm.sections_with_data(drm.cdrm_decode(open('/path/to/trudlcport/work/baseline/%s/mods/%s' % (BL, ud), 'rb').read(), 'le'), 'le')
    return {struct.unpack_from('<I', S_[si]['data'], o + 0x58)[0]: names.get(struct.unpack_from('<H', S_[si]['data'], o + 0x50)[0], '?')
            for si, o in unit_ids.level_info(S_, 'le')['intros']}
cpin = intros_of(CPU) if CPU else intro
assert CP in cpin and cpin[CP] == 'dlc2_checkpoint', CP
keep_uid = {u for u, n in intro.items() if n in KEEP}
ONLY = set(map(int, filter(None, opt('--only', '').split(','))))
if ONLY:
    assert ONLY <= set(intro), ONLY - set(intro)
    keep_uid |= set(intro) - ONLY
src = open(IN, 'rb').read(); d = bytearray(src); base, ok = T.data_of(src); assert ok['header'] and ok['table'] and all(ok['data']), ok
ref_st = set()
if REF:
    r = open(REF, 'rb').read(); rb, _ = T.data_of(r); ref_st = {(s[0], s[2], s[3], s[4]) for s in T.stickies(r, rb)}
# 1) arena
bl, end = T.blocks(src, base)
drop = [b for b in bl if ((b[1] in (3, 4) and b[4] == UID) or (b[1] in (2, 5) and b[3] in intro)) and b[3] not in keep_uid]
dset = {b[0] for b in drop}
new = bytearray()
for p, bid, size, u, unit in bl:
    if p not in dset: new += src[base + p:base + p + size]
assert len(new) == end - sum(b[2] for b in drop)
d[base:base + end] = new + bytes(end - len(new)); struct.pack_into('<I', d, base + T.ARENA_END, len(new))
# 2) dead bits
dd = [u for u in T.dead(src, base) if u in intro and u not in keep_uid]
for u in dd: d[base + T.DEAD + (u >> 3)] &= ~(1 << (u & 7)) & 0xff
# 3) stickies
removed = collections.Counter(); kept_pre = 0
for kind, (ido, vo) in T.STORES.items():
    n = struct.unpack_from('<I', src, base + ido)[0]; ents = []
    allst = [s for s in T.stickies(src, base) if s[0] == kind]
    for s in allst:
        mine = (s[4] == 0 and s[2] in intro and s[2] not in keep_uid) or (s[4] == 1 and s[2] == UID and not ONLY)
        if mine and (kind, s[2], s[3], s[4]) in ref_st: kept_pre += 1; mine = False
        if mine: removed[kind] += 1; continue
        ents.append(s)
    # riscrive id e valori compattati
    for k in range(n): d[base + ido + 4 + 12 * k:base + ido + 16 + 12 * k] = bytes(12)
    struct.pack_into('<I', d, base + ido, len(ents))
    if kind == 'bool':
        nb = (n + 7) >> 3; d[base + vo:base + vo + nb] = bytes(nb)
    else:
        d[base + vo:base + vo + 4 * n] = bytes(4 * n)
    for j, s in enumerate(ents):
        k = s[1]; d[base + ido + 4 + 12 * j:base + ido + 16 + 12 * j] = src[base + ido + 4 + 12 * k:base + ido + 16 + 12 * k]
        if kind == 'bool':
            if s[5]: d[base + vo + (j >> 3)] |= 1 << (j & 7)
        else: d[base + vo + 4 * j:base + vo + 4 * j + 4] = src[base + vo + 4 * k:base + vo + 4 * k + 4]
# 4) checkpoint
g = next(b for b in T.blocks(bytes(d), base)[0] if b[1] == 6); G = base + g[0]
assert bytes(d[G + 0x10:G + 0x10 + 18]) == b'dlc2_machine_room\0'
old_cp = struct.unpack_from('<I', d, G + 0x90)[0]; struct.pack_into('<I', d, G + 0x90, CP)
if CPU:
    nm = CPU[:-4].encode(); assert len(nm) < 0x80
    d[G + 0x10:G + 0x90] = nm + bytes(0x80 - len(nm)); struct.pack_into('<I', d, G + 0x1a8, int(CPUID))
# 5) CRC
hs, t, ents_, _ = T.container(src)
k = next(i for i, e in enumerate(ents_) if e[0] == T.DATA); size, off, _ = ents_[k]
struct.pack_into('<I', d, t + 12 * k + 8, T.crc(bytes(d[off:off + size])))
n_ = struct.unpack_from('<I', d, hs + 0x10)[0]
struct.pack_into('<I', d, hs + 0x14, T.crc(bytes(d[t:t + 12 * n_]))); struct.pack_into('<I', d, hs + 0x18, T.crc(bytes(d[hs:hs + 0x18])))
out = bytes(d)
# verifica
b2, ok2 = T.data_of(out); assert ok2['header'] and ok2['table'] and all(ok2['data']), ok2
bl2, end2 = T.blocks(out, b2); assert all(b[4] != 'ROTTO' for b in bl2)
assert len(bl2) == len(bl) - len(drop) and not [b for b in bl2 if b[1] in (3, 4) and b[4] == UID and b[3] not in keep_uid]
assert not ONLY or {b[3] for b in drop} <= ONLY
st2 = T.stickies(out, b2); assert len(st2) == len(T.stickies(src, base)) - sum(removed.values())
assert not [u for u in T.dead(out, b2) if u in intro and u not in keep_uid]
# fuori dalle zone toccate niente cambia
zones = [(base, base + end), (base + T.ARENA_END, base + T.ARENA_END + 4), (base + T.DEAD, base + T.DEAD + T.DEADLEN),
         (base + 0x135ff4, base + 0x140000), (hs + 0x14, hs + 0x1c), (t, t + 12 * n_), (G + 0x10, G + 0x94), (G + 0x1a8, G + 0x1ac)]
diff = [i for i in range(len(src)) if src[i] != out[i] and not any(lo <= i < hi for lo, hi in zones)]
assert not diff, [hex(i) for i in diff[:10]]
open(OUT, 'wb').write(out)
c = collections.Counter(intro.get(b[3], 'runtime') for b in drop)
print('blocchi tolti', len(drop), dict(c)); print('dead bits azzerati', len(dd), [(u, intro[u]) for u in dd])
print('stickies tolti', dict(removed), 'tenuti perche gia nel salvataggio di riferimento', kept_pre)
print('checkpoint', old_cp, '->', CP, 'unit', CPU or '(stessa)', '| arena', hex(end), '->', hex(end2), '| CRC ok ->', OUT)
