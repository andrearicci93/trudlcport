"""mods\\generalbank.drm for the DLC: PC runtime generalbank + the Xbox TITLE-UPDATE version of script 6 (uiloading).

Why (2026-10-09, in-game): the PC generalbank script 6 (uiloading, 66900 B) is the PRE-TU code; the Xbox TU version (75124 B) adds
the DLC branch: DLC unit -> level num ('Loading DLC1 unit...'), loading_bg_dlc1 and, for dlc_level1_start, the broadcast
'*** DLC CINE: About to broadcast message from loading screen to dlc_level1_start script.' that dlc_level1_start script 20068
waits for before playing cine_dlc1_start_spangs.  Without it Lara stands in the start room and uiloading logs
'Could not get current level num!' for DLC units.

Output = every PC runtime section unchanged, PC script 6 replaced by convert(TU script 6) (Script walker; external relocs into
PC re-authored scripts translated by dlc_generic), plus converted TU sections that script 6 references and the PC file lacks
(script 20082).  usage: generalbank_dlc.py OUTDIR"""
import sys, os, collections, copy, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import override_merge as OM, dlc_generic as DG, generic_store, drm_write as DW, drm_reloc as R
from generic_store import norm_hash

def nop_tu_native_calls(T, conv, ids, st):
    """TU script 6 line 0x95 is a single statement 'push 0; push member 0x400; call uigamedata native #93' (Xbox symbol 19315,
    a native the TU added to uigamedata; the PC uigamedata (117 natives, bound by index in tru.exe 0x7af0c0) has no counterpart we
    can identify).  It sits just before '*** CURRENT LEVEL = ' and its result is unused -> replace the 4 code words by line-
    marker no-ops (op 0, operand 0x95, as the neighbouring line markers) and drop the external reloc of the call operand."""
    k = next(i for i, q in enumerate(T) if (q['type'], q['id']) == (8, 6))
    x = T[k]['data']; o = 0x7928
    want = bytes.fromhex('04000000' '0f000400' '65000000')
    if x[o:o + 12] != want or x[o - 4:o] != bytes.fromhex('00000095'):
        raise ValueError('TU script 6 layout not as expected at 0x7928')
    c = conv[k]; d = bytearray(c.data)
    for w in range(o, o + 16, 4): d[w:w + 4] = struct.pack('<I', 0x95)
    r = R.parse(c.reloc, 'le')
    n0 = len(r.external); r.external = [e for e in r.external if e[1] != o + 12]
    if len(r.external) != n0 - 1: raise ValueError('call operand reloc not found')
    c.data = bytes(d); c.reloc = R.write(r, 'le')

def build(want=((8, 6),)):
    _, Td, T = OM.load(('tu',), 'generalbank.drm')
    ps, Pd, P = OM.load(('pcpatch', 'pcbig'), 'generalbank.drm')
    st = generic_store.load(); ids = DG.DlcIds(st, None)
    st2 = dict(st); st2['xb_hash'] = dict(st['xb_hash'])
    for t, x in want:                         # force the converter (TU content would otherwise be 'pc_reauthored' = PC copy)
        s = next(q for q in T if (q['type'], q['id']) == (t, x))
        st2['xb_hash'][t, x] = set(st['xb_hash'].get((t, x), ())) - {norm_hash(s, T, 'be')}
    conv, rep = DG.convert_drm(T, ids, st2, None)
    nop_tu_native_calls(T, conv, ids, st)
    new_id = {k: rep[k][3] for k in range(len(T))}
    pkeys = {(p['type'], p['id']) for p in P}
    # closure: wanted sections + TU sections they reference (ext / id refs) that PC lacks
    tidx = {(q['type'], q['id']): k for k, q in enumerate(T)}
    sel = [tidx[w] for w in want]; seen = set(sel)
    while True:
        add = []
        for k in sel:
            r = R.parse(T[k]['reloc'], 'be')
            refs = [si for si, _, _ in r.external] + [tidx.get((ty, struct.unpack_from('>I', T[k]['data'], o)[0])) for ty, o in r.idref]
            for j in refs:
                if j is None or j in seen: continue
                if (T[j]['type'], new_id[j]) not in pkeys: add.append(j); seen.add(j)
        if not add: break
        sel += add
    out = [DW.Section(p['type'], p['id'], p['data'], p['reloc'], p['flags'], p['ver'], p['spec']) for p in P]
    ext_t = {k: [(P[si]['type'], P[si]['id']) for si, _, _ in R.parse(p['reloc'], 'le').external] for k, p in enumerate(P)}
    pos = {(s.type, s.id): k for k, s in enumerate(out)}
    for k in sel:
        c = conv[k]; key = (c.type, c.id)
        tg = [(T[si]['type'], new_id[si]) for si, _, _ in R.parse(c.reloc, 'le').external]
        if key in pos: out[pos[key]] = c; ext_t[pos[key]] = tg
        else: out.append(c); ext_t[len(out) - 1] = tg; pos[key] = len(out) - 1
    cnt = collections.Counter((s.type, s.id) for s in out)
    index_of = {(s.type, s.id): k for k, s in enumerate(out) if cnt[s.type, s.id] == 1}
    for k, tg in ext_t.items():
        if not tg: continue
        rl = DG.retarget_ext(out[k].reloc, tg, index_of)
        if rl is None: raise ValueError('cannot retarget %s %s' % ((out[k].type, out[k].id), [t for t in tg if t not in index_of][:5]))
        out[k].reloc = rl
    drm = DW.Drm(out, Pd.names, Pd.pad, Pd.ver, Pd.u0, Pd.u1)
    return drm, dict(src=ps, selected=[(T[k]['type'], T[k]['id'], new_id[k], rep[k][4], len(conv[k].data)) for k in sel],
                     nsec=len(out), npc=len(P), xlate=dict(DG.XLATE_STATS))

if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    drm, info = build()
    raw_pc = OM.raw('pcpatch', 'generalbank.drm') or OM.raw('pcbig', 'generalbank.drm')
    data = drm.write('le')
    if raw_pc[:4] == b'CDRM': data = DW.cdrm_encode(data, 'le')
    open(os.path.join(out, 'generalbank.drm'), 'wb').write(data)
    print(info)
