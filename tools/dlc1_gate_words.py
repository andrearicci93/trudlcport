"""dlc1_gate_words.py - gating a livello di PAROLA della riconversione fresca DLC1 (offline, nessuna VM, nessuna installazione).

Problema: riconversione fresca (work/ws/rebuild/out_fresh2) + tools/dlc1_postfix.py != pacchetto work/mods_dlc1_rc (899 parole + sezioni).
Questo tool NON modifica dlc_generic.py ne' file esistenti.  Dati: out_fresh2 (o gia' postfissato), rc, overlay installato (tutto da file,
mai da valori di rc: i valori di rifiuto vengono dall'overlay INSTALLATO / base, quelli dei layer dai layer stessi).

Passi (per file DRM, sezioni accoppiate per (type, id, occorrenza), mai per indice):
  0. postfix in-process (importa i passi di dlc1_postfix: streamname, R12, parole dtpkeys/min) da out_fresh2 -> OUT/out_post   [--src-post per riusare]
  1. LAYER non riprodotti, merge a 3 vie con la logica di overlay_merge.layer_changes (layer vs base vm_mods_expected, per indice di base):
       parola: applicata solo se la parola fresca == parola base (altrimenti: fresca == layer -> gia' presente, altro -> CONFLITTO, riportato);
       sezione intera: sostituita solo se la sezione fresca e' identica (dati+reloc+meta) a quella base.
     layer (ordine overlay installato, l'ultimo vince): mods_current_webs (web_cutout), mods_fix18 (analog_word_fix), mods_fix18_awf_extra,
     glitchfix2_ab_ring.
  2. LISTA DI RIFIUTO per parola (fresca != installata; precedenza fissa, una sola causa primaria per parola):
       r1 raft3c      raft_bridge_spawned 20770: parole 3c000000 dell'installato/base non si sostituiscono (NOTES, regola nuova)
       r2 grapple     dlc1_ei_grapple_ceiling/wall: la riconversione non li sostituisce (variante glitchfix2_ab_ring confermata in VM)
       r3 inst        drift_verdicts verdict 'inst' / 'inst(layer)' (tipo 7)
       r4 undecided   drift_verdicts verdict UNDECIDED
       r5 (solo --strict) neither / nessun verdict / fresh medium-low non applicata (nessuna evidenza a favore della parola fresca)
     la parola torna al valore dell'overlay installato.
  3. file NOT_INSTALLED (non presenti nel manifest installato, es. g_pda.drm) esclusi dall'output.
Residuo = parole/sezioni di OUT/out_gated != rc, ognuna con motivo (residual_words.tsv, residual_sections.tsv).

usage:
  tools/venv/bin/python -I tools/dlc1_gate_words.py run [--strict] [--out work/ws/gating] [--src-post DIR]
  tools/venv/bin/python -I tools/dlc1_gate_words.py selftest
API: gate_file(rel, fresh_raw, ctx) -> (new_raw, records); make_ctx(strict=False)
"""
import sys, os, re, csv, json, shutil, hashlib, collections, argparse
TOOLS = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, TOOLS)
ROOT = os.path.normpath(os.path.join(TOOLS, '..'))
WORK = os.path.join(ROOT, 'work')
WS = os.path.join(WORK, 'ws')
GATING = os.path.join(WS, 'gating')
SRC_FRESH = os.path.join(WS, 'rebuild', 'out_fresh2')
RC_MANIFEST = os.path.join(WS, 'rebuild', 'installed_rc.tsv')           # overlay installato + rc (colonna abs_path = file effettivo; PUO' essere vecchio)
RC_DIR = os.path.join(WORK, 'mods_dlc1_rc')                             # rc corrente (altri workstream lo aggiornano: vince sul manifest)
INST_MANIFEST = os.path.join(WS, 'rebuild', 'installed_effective.tsv')  # overlay installato (senza rc)
BASE_DIR = os.path.join(WORK, 'vm_mods_expected')
VERDICTS = os.path.join(WS, 'dtpkeys', 'out', 'drift_verdicts.tsv')
LAYERS = [('mods_current_webs', os.path.join(WORK, 'mods_current_webs')), ('mods_fix18', os.path.join(WORK, 'mods_fix18')),
          ('mods_fix18_awf_extra', os.path.join(WORK, 'mods_fix18_awf_extra')), ('glitchfix2_ab_ring', os.path.join(WORK, 'glitchfix2_ab_ring')),
          ('mat2_bend_switches', os.path.join(WS, 'mat2', 'out'))]
RC_SOURCES = [('savehang', os.path.join(WS, 'savehang', 'out')), ('refs', os.path.join(WS, 'refs', 'out')), ('fpfloat', os.path.join(WS, 'fpfloat', 'out'))]  # layer che compongono rc (insieme a dtpkeys/min)
LAYER_ONLY = {'mat2_bend_switches': ('dlc1_uo_bend_switches.drm',)}   # layer limitati a certi file (mat2/out contiene anche dragon_slider vecchio: NON usato)
GRAPPLE = ('dlc1_ei_grapple_ceiling.drm', 'dlc1_ei_grapple_wall.drm')
RAFT3C = ('dlc1_uo_raft_bridge_spawned.drm', 20770, bytes.fromhex('3c000000'))
# parole model_point_fix gia' note come residue dello scan sull'installato (gate/NOTES_agent.md): (file, id)
MPF_KNOWN = {('dlc1_uo_raft_bridge.drm', 21107), ('dlc1_uo_dragon_slider.drm', 23369), ('dlc1_uo_dragon_slider.drm', 20461),
             ('dlc1_uo_dragon_slider.drm', 20462), ('dlc1_uo_dragon_slider.drm', 22545), ('dlc1_uo_dragon_slider.drm', 23452),
             ('dlc1_uo_pillory.drm', 20627), ('dlc1_uo_pillory.drm', 20628), ('dlc1_uo_pillory.drm', 20629), ('dlc1_uo_goo_pit_lever.drm', 23459)}

import drm_write as DW
import overlay_merge as OM
import dlc1_postfix as P


def md5(p): return hashlib.md5(open(p, 'rb').read()).hexdigest()


def read_manifest(path):
    m = {}
    for r in csv.DictReader(open(path, newline=''), delimiter='\t'):
        m[r['relpath']] = r['abs_path']
    return m


def parse(raw):
    return DW.read(raw, 'le')


def keymap(D):
    """(type, id, occurrence) -> index"""
    seen = collections.Counter(); km = {}
    for i, s in enumerate(D.sections):
        k = (s.type, s.id, seen[(s.type, s.id)]); seen[(s.type, s.id)] += 1; km[k] = i
    return km


def km_pairs(km):
    return {k[:2] for k in km}


def sec_sig(s):
    return (s.type, s.id, s.ver, s.flags, s.spec, s.pad, bytes(s.reloc), bytes(s.data))


def pattern(a, b):
    if a == b[2:] + b[:2]: return 'half_swap'
    if a == b[::-1]: return 'bswap'
    if sorted(a) == sorted(b): return 'perm'
    if a[::-1] == b[2:] + b[:2] or a == bytes([b[1], b[0], b[3], b[2]]): return 'byte_pair_swap'
    return 'other'


class Ctx:
    pass


def make_ctx(strict=False, layer_wins=False):
    c = Ctx(); c.strict = strict
    c.rc = read_manifest(RC_MANIFEST); c.inst = read_manifest(INST_MANIFEST)
    for dp, dn, fn in os.walk(RC_DIR):
        for f in fn:
            if f.lower().endswith('.drm'): c.rc[os.path.relpath(os.path.join(dp, f), RC_DIR).replace(os.sep, '/')] = os.path.join(dp, f)
    c.layer_wins = layer_wins
    c.verd = {}
    for r in csv.DictReader(open(VERDICTS, newline=''), delimiter='\t'):
        c.verd[(r['file'], int(r['dtp']), int(r['off'], 16))] = r
    c.log_words = P.load_words(P.WORDS_LOG)
    c.cache = {}
    return c


def load_cached(ctx, path):
    if path not in ctx.cache:
        ctx.cache[path] = parse(open(path, 'rb').read())
    return ctx.cache[path]


# ---------------------------------------------------------------------------------------------------------------- gating di un file
def gate_file(rel, raw, ctx):
    """-> (new_raw, recs).  recs: list of dict(kind=layer|reject|keep|conflict, sec=(type,id), off, fresh, target, reason, ...)"""
    recs = []
    D = parse(raw); orig = parse(raw)
    km = keymap(orig)
    ipath = ctx.inst.get(rel)
    I = load_cached(ctx, ipath) if ipath else None
    ikm = keymap(I) if I else {}
    bpath = os.path.join(BASE_DIR, rel)
    B = load_cached(ctx, bpath) if os.path.exists(bpath) else None
    bkm = keymap(B) if B else {}
    binv = {i: k for k, i in bkm.items()}
    # parole che i layer sorgente di rc (savehang/refs/fpfloat) cambiano rispetto alla base: la parola fresca uguale a quella del layer non si rifiuta
    prot = {}
    if B is not None:
        for sname, sdir in RC_SOURCES:
            sp = os.path.join(sdir, rel)
            if not os.path.exists(sp): continue
            ch0, _ = OM.layer_changes(B, load_cached(ctx, sp))
            for k0, v0 in (ch0 or {}).items():
                if k0[0] == 'data': prot[(binv[k0[1]], k0[2])] = (bytes(v0), sname)
    changed = set()          # (sec idx in D, off) parole cambiate / ('sec', idx)
    # ---- passo 1: layer, 3 vie
    if B is not None:
        for lname, ldir in LAYERS:
            lp = os.path.join(ldir, rel)
            if lname in LAYER_ONLY and rel not in LAYER_ONLY[lname]: continue
            if not os.path.exists(lp): continue
            L = load_cached(ctx, lp)
            ch, st = OM.layer_changes(B, L)
            if ch is None:
                recs.append(dict(kind='conflict', reason='layer %s non applicabile: %s' % (lname, st), sec=None, off=None)); continue
            for k, v in sorted(ch.items(), key=lambda kv: (kv[0][0], kv[0][1:] if len(kv[0]) > 1 else ())):
                if k[0] not in ('data', 'sec'):
                    if k[0] != 'add' or True:
                        recs.append(dict(kind='conflict', reason='layer %s: chiave %s non gestita' % (lname, OM.key_str(k)), sec=None, off=None))
                    continue
                bs = B.sections[k[1]]
                bkey = binv[k[1]]
                j = km.get(bkey)
                if j is None:
                    recs.append(dict(kind='conflict', reason='layer %s: sezione base %s assente nel fresco' % (lname, bkey[:2]), sec=bkey[:2], off=None)); continue
                fs0 = orig.sections[j]
                if k[0] == 'data':
                    off = k[2]
                    if len(fs0.data) != len(bs.data):
                        recs.append(dict(kind='conflict', reason='layer %s: sezione %s taglia diversa' % (lname, bkey[:2]), sec=bkey[:2], off=off)); continue
                    fw = bytes(fs0.data[off:off + 4]); bw = bytes(bs.data[off:off + 4])
                    if fw == v:
                        continue                                  # gia' presente
                    if fw == bw:
                        s = D.sections[j]; s.data = s.data[:off] + v + s.data[off + 4:]; changed.add((j, off))
                        recs.append(dict(kind='layer', reason='layer:' + lname, sec=bkey[:2], off=off, fresh=fw, target=v, secidx=j))
                    elif ctx.layer_wins:
                        s = D.sections[j]; s.data = s.data[:off] + v + s.data[off + 4:]; changed.add((j, off))
                        recs.append(dict(kind='layer', reason='layer:' + lname + ':layer_wins(conflitto fresco %s/base %s)' % (fw.hex(), bw.hex()), sec=bkey[:2], off=off,
                                         fresh=fw, target=v, secidx=j))
                    else:
                        recs.append(dict(kind='conflict', reason='layer %s: parola fresca %s != base %s != layer %s' % (lname, fw.hex(), bw.hex(), bytes(v).hex()),
                                         sec=bkey[:2], off=off, fresh=fw, target=bytes(v)))
                else:   # sezione intera
                    fsg = sec_sig(fs0); bsg = sec_sig(bs); lsg = (v[0], v[1], v[2], v[3], v[4], v[5], bytes(v[6]), bytes(v[7]))
                    if fsg == lsg: continue
                    if fsg == bsg:
                        D.sections[j] = DW.Section(v[0], v[1], v[7], v[6], v[3], v[2], v[4], v[5]); changed.add(('sec', j))
                        recs.append(dict(kind='layer', reason='layer:' + lname + ':sezione', sec=bkey[:2], off=None, secidx=j,
                                         fresh=b'', target=b'', nbytes=len(v[7])))
                    else:
                        recs.append(dict(kind='conflict', reason='layer %s: sezione %s fresca != base (taglia %d vs %d)' % (lname, bkey[:2], len(fs0.data), len(bs.data)),
                                         sec=bkey[:2], off=None))
    # un conflitto di layer in una sezione => tutta la sezione torna all'installata (gruppi di slot web 0x4bc/0x4cc/0x4dc non si mescolano)
    confsec = {(r['sec']) for r in recs if r['kind'] == 'conflict' and r.get('off') is not None and r['sec'] in km_pairs(km)}
    for key in sorted(confsec, key=str):
        cand = [k for k in km if k[:2] == key]
        for kk in cand:
            j = km[kk]
            if I is None or kk not in ikm or len(I.sections[ikm[kk]].data) != len(orig.sections[j].data): continue
            isec = I.sections[ikm[kk]]
            recs[:] = [r for r in recs if not (r.get('secidx') == j and r['kind'] in ('layer', 'reject'))]
            D.sections[j] = DW.Section(isec.type, isec.id, isec.data, isec.reloc, isec.flags, isec.ver, isec.spec, isec.pad)
            changed.add(('sec', j))
            nd = sum(1 for q in range(0, len(isec.data), 4) if isec.data[q:q + 4] != orig.sections[j].data[q:q + 4])
            recs.append(dict(kind='layer', reason='section_revert_installed(conflitto layer web)', sec=kk[:2], off=None, secidx=j, fresh=b'', target=b'', nbytes=nd))
    # ---- passo 2: rifiuto per parola (fresca != installata), sulle parole non toccate dai layer
    if I is not None:
        for key, j in km.items():
            if ('sec', j) in changed or key not in ikm: continue
            fs = D.sections[j]; isec = I.sections[ikm[key]]
            if len(fs.data) != len(isec.data): continue
            for q in range(0, len(fs.data), 4):
                fw = bytes(fs.data[q:q + 4]); iw = bytes(isec.data[q:q + 4])
                if fw == iw: continue
                reason = None
                vr = ctx.verd.get((rel, fs.id, q)) if fs.type == 7 else None
                if fs.type == 7 and any(x[0] == fs.id and x[1] == q and bytes.fromhex(x[3]) == fw for x in ctx.log_words.get(rel, [])):
                    continue                                       # parola dtpkeys/min applicata dal postfix: e' nel pacchetto rc per costruzione
                if rel == RAFT3C[0] and fs.id == RAFT3C[1] and iw == RAFT3C[2]: reason = 'r1_raft3c'
                elif os.path.basename(rel) in GRAPPLE: reason = 'r2_grapple_abring'
                elif vr and vr['verdict'] == 'inst': reason = 'r3_verdict_inst'
                elif vr and vr['verdict'] == 'inst(layer)': reason = 'r3_verdict_inst_layer'
                elif vr and vr['verdict'] == 'UNDECIDED': reason = 'r4_undecided'
                elif ctx.strict and not (fs.type == 7 and (os.path.basename(rel), fs.id) in MPF_KNOWN):   # model_point_fix mirati: nemmeno --strict li scarta
                    if vr is None: reason = 'r5_no_verdict'
                    elif vr['verdict'] == 'neither': reason = 'r5_neither'
                    elif vr['verdict'] == 'fresh' and vr['applied'] != 'yes': reason = 'r5_fresh_not_applied'
                if not reason and fs.type != 7 and not vr:
                    bsec = B.sections[bkm[key]] if B is not None and key in bkm and len(B.sections[bkm[key]].data) == len(fs.data) else None
                    if bsec is not None and bytes(bsec.data[q:q + 4]) == iw:
                        if sorted(iw) == sorted(fw): reason = 'r6_perm_of_installed(%s)' % pattern(iw, fw)   # stessi 4 byte permutati: endianness non convertita
                        elif fs.type == 0: reason = 'r7_t0_keep_installed_nonperm'                           # t0 non-permutazione, installata==base (es. dlc_dungeon 0x1ac/0x26c, campo vicino alla tabella nomi)
                if reason and prot.get((key, q), (None,))[0] == fw:
                    continue                                       # parola del layer sorgente di rc (fpfloat/refs/savehang): non si rifiuta
                if reason:
                    # la parola rifiutata torna a quella installata; se dtpkeys/min la riscrive (old == installata) ci mette 'new' (stessa semantica del postfix)
                    iw0 = iw
                    mw = [x for x in ctx.log_words.get(rel, []) if fs.type == 7 and x[0] == fs.id and x[1] == q and bytes.fromhex(x[2]) == iw]
                    if mw: iw = bytes.fromhex(mw[0][3]); reason += '+min_new'
                    fs.data = fs.data[:q] + iw + fs.data[q + 4:]
                    if vr and bytes.fromhex(vr['installed']) != iw0: reason += '!verdict_installed_mismatch'
                    recs.append(dict(kind='reject', reason=reason, sec=(fs.type, fs.id), off=q, fresh=fw, target=iw, secidx=j))
    if not changed and not any(r['kind'] == 'reject' for r in recs):
        return raw, recs
    out = D.write('le')
    if raw[:4] == b'CDRM': out = DW.cdrm_encode(out, 'le')
    # verifica: le sole differenze rispetto all'originale sono quelle registrate
    O = parse(raw); N = parse(out)
    assert len(O.sections) == len(N.sections), rel
    exp = {(r['secidx'], r['off']) for r in recs if r['kind'] in ('layer', 'reject') and r.get('off') is not None}
    secrepl = {r['secidx'] for r in recs if r['kind'] == 'layer' and r.get('off') is None}
    got = set()
    for i, (a, b) in enumerate(zip(O.sections, N.sections)):
        if i in secrepl: continue
        assert (a.type, a.id, a.reloc, a.ver, a.flags) == (b.type, b.id, b.reloc, b.ver, b.flags), (rel, i)
        assert len(a.data) == len(b.data), (rel, i)
        for q in range(0, len(a.data), 4):
            if a.data[q:q + 4] != b.data[q:q + 4]: got.add((i, q))
    assert got == exp, (rel, 'differenze != registrate', len(got), len(exp))
    return out, recs


# ---------------------------------------------------------------------------------------------------------------- confronto con rc
def compare_rc(rel, gated_raw, ctx, recs):
    """parole/sezioni di gated != rc, con motivo.  -> (words, sections)"""
    rpath = ctx.rc.get(rel)
    if not rpath: return [], []
    G = parse(gated_raw); R = parse(open(rpath, 'rb').read())
    gk, rk = keymap(G), keymap(R)
    bpath = os.path.join(BASE_DIR, rel); B = load_cached(ctx, bpath) if os.path.exists(bpath) else None
    bk = keymap(B) if B else {}
    ipath = ctx.inst.get(rel); I = load_cached(ctx, ipath) if ipath else None
    ik = keymap(I) if I else {}
    secs = []; words = []
    only_g = [k for k in gk if k not in rk]; only_r = [k for k in rk if k not in gk]
    for k in only_g: secs.append((rel, k[:2], 'solo_fresco', len(G.sections[gk[k]].data), 'sezione %s presente solo nel fresco (non in rc)' % (k[:2],)))
    for k in only_r: secs.append((rel, k[:2], 'solo_rc', len(R.sections[rk[k]].data), 'sezione presente solo in rc'))
    common = [k for k in gk if k in rk]
    if not only_g and not only_r:
        og = [k for k in gk if k in rk]; orr = [k for k in rk]
        if [k for k in sorted(gk, key=gk.get)] != [k for k in sorted(rk, key=rk.get)]:
            nmov = sum(1 for a, b in zip(sorted(gk, key=gk.get), sorted(rk, key=rk.get)) if a != b)
            secs.append((rel, None, 'ordine', nmov, 'stesso insieme di sezioni (type,id), ordine diverso in %d posizioni (shader lib tipo 9 inserite: fresco a meta'
                         ', rc in coda; refs R03)' % nmov))
    conf = {(r['sec'], r['off']): r['reason'] for r in recs if r['kind'] == 'conflict' and r.get('off') is not None}
    for k in common:
        g = G.sections[gk[k]]; r = R.sections[rk[k]]
        if len(g.data) != len(r.data):
            if os.path.basename(rel) == 'dlc1_uo_bend_switches.drm' and k[1] == 21210 and k[0] == 10:
                secs.append((rel, k[:2], 'rc_voluto', len(g.data), 'materiale 21210 sostituito in rc dal gemello PC (workstream mat2, voluto; non riprodotto dalla pipeline)')); continue
            newer = os.path.getmtime(ctx.rc[rel]) > os.path.getmtime(RC_MANIFEST)
            secs.append((rel, k[:2], 'taglia', len(g.data), 'taglia %d (fresco) vs %d (rc)%s' % (len(g.data), len(r.data),
                         '; il file rc e\' stato modificato DOPO il manifest installed_rc.tsv (altro workstream in corso)' if newer else ''))); continue
        if (g.type, g.id, g.ver, g.flags, g.spec, g.pad, bytes(g.reloc)) != (r.type, r.id, r.ver, r.flags, r.spec, r.pad, bytes(r.reloc)):
            secs.append((rel, k[:2], 'meta/reloc', len(g.data), 'meta o reloc diversi'))
        bs = B.sections[bk[k]] if B and k in bk and len(B.sections[bk[k]].data) == len(g.data) else None
        isec = I.sections[ik[k]] if I and k in ik and len(I.sections[ik[k]].data) == len(g.data) else None
        for q in range(0, len(g.data), 4):
            fw = bytes(g.data[q:q + 4]); rw = bytes(r.data[q:q + 4])
            if fw == rw: continue
            bw = bytes(bs.data[q:q + 4]) if bs else None
            iw = bytes(isec.data[q:q + 4]) if isec else None
            vr = ctx.verd.get((rel, g.id, q)) if g.type == 7 else None
            lw = [x for x in ctx.log_words.get(rel, []) if x[0] == g.id and x[1] == q] if g.type == 7 else []
            cls = 'rc==base' if bw == rw else ('rc!=base' if bw is not None else 'no_base')
            if ((g.type, g.id), q) in conf:
                why = 'conflitto_layer(' + conf[((g.type, g.id), q)] + ')'
            elif lw and bytes.fromhex(lw[0][3]) == rw and fw != bytes.fromhex(lw[0][2]):
                why = 'min_word_saltata_terza_forma(fresco %s, old %s, new %s: postfix applica solo se valore==old)' % (fw.hex(), lw[0][2], lw[0][3])
            elif vr and vr['verdict'] == 'fresh':
                why = 'fresh_supportata:%s%s (verdict dtpkeys, non nel pacchetto min; rc tiene la base)' % (vr['certainty'], '+applicata_in_full' if vr['applied'] == 'yes' else '')
            elif vr and vr['verdict'] == 'neither':
                why = 'neither:%s (ne installata ne fresca supportata)' % vr['certainty']
            elif vr:
                why = 'verdict_%s' % vr['verdict']
            elif g.type == 7 and (os.path.basename(rel), g.id) in MPF_KNOWN:
                why = 'mpf_pipeline: parola di model_point_fix (extra_fixes) che rc non applica; fresca = correzione tipata, non provata'
            elif g.type == 7:
                why = 'no_verdict_t7'
            else:
                why = 'no_verdict_t%d(%s)' % (g.type, pattern(fw, rw))
            words.append((rel, g.type, g.id, q, fw.hex(), rw.hex(), bw.hex() if bw else '', iw.hex() if iw else '', cls, why))
    return words, secs


# ---------------------------------------------------------------------------------------------------------------- run
def run(out_root, strict=False, src_post=None, src=SRC_FRESH, layer_wins=False):
    out_root = os.path.realpath(out_root)
    if not (out_root == os.path.realpath(GATING) or out_root.startswith(os.path.realpath(GATING) + os.sep)):
        raise SystemExit('out deve stare sotto work/ws/gating/')
    os.makedirs(out_root, exist_ok=True)
    ctx = make_ctx(strict, layer_wins)
    out_post = os.path.join(out_root, 'out_post'); out_gated = os.path.join(out_root, 'out_gated')
    # 0. postfix in-process
    if src_post:
        post = os.path.realpath(src_post)
    else:
        if os.path.lexists(out_post): shutil.rmtree(out_post)
        shutil.copytree(src, out_post)
        post = out_post
        tot = collections.Counter()
        for dp, dn, fn in os.walk(src):
            for f in fn:
                if not f.lower().endswith('.drm'): continue
                rel = os.path.relpath(os.path.join(dp, f), src).replace(os.sep, '/')
                raw0 = open(os.path.join(src, rel), 'rb').read(); st = collections.Counter()
                r1, n1 = P.step_streamname(rel, raw0); st['streamname_sections'] = n1
                r2, nf, nm = P.step_strings(rel, r1); st['r12_fixed'] = nf; st['r12_manual'] = nm
                rows = ctx.log_words.get(rel, [])
                r3 = P.step_words(rel, r2, rows, st) if rows else r2
                tot.update(st)
                if r3 != raw0: open(os.path.join(post, rel), 'wb').write(r3)
        print('postfix in-process:', dict(tot))
    # 1-3. gating
    if os.path.lexists(out_gated): shutil.rmtree(out_gated)
    os.makedirs(out_gated)
    allrecs = []; words = []; secs = []; skipped = []; nfiles = 0; changed_files = []
    for dp, dn, fn in os.walk(post):
        for f in sorted(fn):
            p = os.path.join(dp, f); rel = os.path.relpath(p, post).replace(os.sep, '/')
            if f == 'md5.txt' or f == 'convert_report.tsv': continue
            if rel not in ctx.rc and rel.endswith('.drm'):
                skipped.append(rel); continue                       # NOT_INSTALLED (es. g_pda.drm)
            raw = open(p, 'rb').read(); dst = os.path.join(out_gated, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
            if rel.endswith('.drm'):
                new, recs = gate_file(rel, raw, ctx); nfiles += 1
                for r in recs: r['file'] = rel
                allrecs += recs
                w, s = compare_rc(rel, new, ctx, recs); words += w; secs += s
                if new != raw: changed_files.append(rel)
                open(dst, 'wb').write(new)
            else:
                shutil.copyfile(p, dst)
    md = []
    for dp, dn, fn in os.walk(out_gated):
        for f in sorted(fn):
            q = os.path.join(dp, f); md.append('%s  %s' % (md5(q), os.path.relpath(q, out_gated).replace(os.sep, '/')))
    open(os.path.join(out_gated, 'md5.txt'), 'w').write('\n'.join(sorted(md, key=lambda s: s.split('  ')[1])) + '\n')
    # report
    def hx(b): return b.hex() if isinstance(b, (bytes, bytearray)) else ''
    last = {}
    for r in allrecs:
        if r['kind'] == 'layer': last[(r['file'], r['secidx'], r.get('off'))] = r
    allrecs = [r for r in allrecs if r['kind'] != 'layer' or last[(r['file'], r['secidx'], r.get('off'))] is r]
    with open(os.path.join(out_root, 'reject_words.tsv'), 'w') as fh:
        fh.write('file\tsec_type\tsec_id\toff\tfresh\ttarget\tkind\treason\n')
        for r in allrecs:
            if r['kind'] in ('reject', 'layer'):
                fh.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (r['file'], r['sec'][0], r['sec'][1], hex(r['off']) if r.get('off') is not None else 'SEZIONE',
                                                              hx(r.get('fresh')), hx(r.get('target')), r['kind'], r['reason']))
    with open(os.path.join(out_root, 'conflicts.tsv'), 'w') as fh:
        fh.write('file\tsec\toff\treason\n')
        for r in allrecs:
            if r['kind'] == 'conflict': fh.write('%s\t%s\t%s\t%s\n' % (r['file'], r['sec'], hex(r['off']) if r.get('off') is not None else '', r['reason']))
    with open(os.path.join(out_root, 'residual_words.tsv'), 'w') as fh:
        fh.write('file\tsec_type\tsec_id\toff\tgated\trc\tbase\tinstalled\trc_vs_base\treason\n')
        for w in words: fh.write('%s\t%d\t%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (w[0], w[1], w[2], hex(w[3]), w[4], w[5], w[6], w[7], w[8], w[9]))
    with open(os.path.join(out_root, 'residual_sections.tsv'), 'w') as fh:
        fh.write('file\tsection\tkind\tvalue\treason\n')
        for s in secs: fh.write('%s\t%s\t%s\t%s\t%s\n' % (s[0], s[1], s[2], s[3], s[4]))
    cnt = collections.Counter(':'.join((r['reason'].split(':') + [''])[:2]).rstrip(':') if r['kind'] == 'layer' else r['reason'] for r in allrecs if r['kind'] in ('reject', 'layer'))
    rcnt = collections.Counter(re.sub(r'\(.*', '', w[9]).split(' (')[0] for w in words)
    summ = dict(strict=strict, layer_wins=layer_wins, rc_md5_txt=md5(os.path.join(RC_DIR, 'md5.txt')), files_gated=nfiles, files_changed_by_gating=len(changed_files), skipped_not_installed=skipped,
                applied=dict(cnt), n_conflicts=sum(1 for r in allrecs if r['kind'] == 'conflict'), residual_words=len(words),
                residual_by_reason=dict(rcnt), residual_sections=len(secs), residual_sections_by_kind=dict(collections.Counter(s[2] for s in secs)),
                residual_unexplained=sum(1 for w in words if w[9].startswith('no_verdict_')), residual_unexplained_secs=sum(1 for x in secs if x[2] in ('taglia', 'meta/reloc', 'solo_rc')))
    json.dump(summ, open(os.path.join(out_root, 'summary%s.json' % ('_strict' if strict else '')), 'w'), indent=1)
    print(json.dumps(summ, indent=1))
    return summ


# ---------------------------------------------------------------------------------------------------------------- selftest
def selftest():
    ctx = make_ctx(False); bad = 0; n = 0; nw = 0
    # 1) base/installato come input: 0 parole cambiate (layer e rifiuti non devono toccare cio' che e' gia' installato)
    for rel, ip in sorted(ctx.inst.items()):
        if not rel.endswith('.drm'): continue
        raw = open(ip, 'rb').read(); new, recs = gate_file(rel, raw, ctx); n += 1
        ch = [r for r in recs if r['kind'] in ('reject', 'layer')]
        ch = [r for r in ch if 'mat2_bend_switches' not in r['reason']]   # voluto: l'installato non ha ancora il materiale 21210 PC (e' nel solo rc)
        if ch: bad += 1; nw += len(ch); print('  CAMBIA su installato:', rel, len(ch), collections.Counter(r['reason'] for r in ch).most_common(3))
    print('selftest 1 (installato come fresco): %d file, %d con cambi, %d parole  (atteso 0)' % (n, bad, nw))
    # 2) idempotenza su un campione dei fresh (dopo postfix gia' presente in gating/out_post se esiste)
    post = os.path.join(GATING, 'out_post'); idem = 0; tested = 0
    if os.path.isdir(post):
        for rel in ('dlc_caverns.drm', 'dlc1_uo_raft_bridge_spawned.drm', 'cinstream/pdlc1_010_intro.drm', 'dlc_dungeon.drm', 'dlc_fx_waterfall_cvn_ist.drm',
                    'streamgroups/dlc_water_wheel_waterwheel_main.drm', 'knight_thrall_chunkdoll.drm'):
            p = os.path.join(post, rel)
            if not os.path.exists(p): continue
            raw = open(p, 'rb').read(); a, _ = gate_file(rel, raw, ctx); b, r2 = gate_file(rel, a, ctx); tested += 1
            if a == b: idem += 1
            else: print('  NON idempotente', rel, len([r for r in r2 if r['kind'] in ('reject', 'layer')]))
        print('selftest 2 (idempotenza): %d/%d' % (idem, tested))
    ok = bad == 0 and idem == tested
    print('selftest:', 'OK' if ok else 'FAIL')
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['run', 'selftest'])
    ap.add_argument('--out', default=GATING)
    ap.add_argument('--strict', action='store_true')
    ap.add_argument('--layer-wins', action='store_true', help='nei conflitti pipeline/layer (parola fresca != base != layer) vince il layer')
    ap.add_argument('--src-post', help='usa questa directory gia\' postfissata invece di rieseguire il postfix su out_fresh2')
    a = ap.parse_args()
    if a.cmd == 'selftest': sys.exit(0 if selftest() else 1)
    run(a.out, a.strict, a.src_post, layer_wins=a.layer_wins)


if __name__ == '__main__':
    main()
