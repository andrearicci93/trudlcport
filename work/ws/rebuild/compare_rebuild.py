"""Section- and word-level comparison of the fresh reconversion (out_fresh/) against the installed effective overlay.

Matching: sections keyed by (type, id, occurrence). Header per section (ver, spec, flags) and per DRM (namesz, padsz) are
compared too (content vs container).
Attribution (words, LE u32, only for sections with equal size): for each word where fresh != installed, the version chain
of that word over the layers that contain the file (CHRONO order, vm_mods_expected first) is consulted:
  EXPLAINED:<L>        fresh value == value at an earlier layer j; the installed value first appears at a later layer L
                       (L = the fix that moved the word from the fresh state to the installed state)
  HOOK_NOT_FIRING:<L>  as EXPLAINED, but L is a fix that IS wired in the pipeline and fresh == its immediate predecessor
  DRIFT                fresh value is in no layer, installed value == base (vm_mods_expected): pipeline changed something
                       no installed fix ever touched
  RESID                anything else (fresh value in no layer, installed value not explained)
Sections with different size or reloc blob are classified at section level (SIZE / RELOC_*), using the same chain logic.
Writes diff_sections.tsv and _summary.json.
Usage: tools/venv/bin/python -I work/ws/rebuild/compare_rebuild.py
"""
import sys, os, json, collections
TOOLS = os.path.expanduser('~/Downloads/tru-port/tools'); sys.path.insert(0, TOOLS)
import numpy as np
import drm as D
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.expanduser('~/Downloads/tru-port/work')
SKIP = {'md5.txt', 'MD5.txt', 'README.md', 'INSTALL.md', 'MANIFEST.md', 'NOTES_agent.md', 'patch_log.txt'}
# chronological layers: (name, dir relative to work, fix label, wired-in-pipeline fixes)
CHRONO = [
 ('vm_mods_expected', 'vm_mods_expected', 'base', ()),
 ('mods_fix14', 'mods_fix14', 'animfx', ('animfx',)),
 ('mods_glitchfix', 'mods_glitchfix', 'reslot', ('reslot',)),
 ('mods_fix15', 'mods_fix15', 'aidata', ('aidata',)),
 ('mods_glitchfix2', 'mods_glitchfix2', 'reslot-fallback', ('reslot',)),
 ('next_s1_cavhall', 'next_stage/s1_cavhall', 'aidata(hall)', ('aidata',)),
 ('next_s2_dtpid', 'next_stage/s2_dtpid', 'dtpid/dtplist/align/goo', ()),
 ('next_s3_static', 'next_stage/s3_static/dir', 'static/sarray', ()),
 ('mods_next', 'mods_next', 'next(=s3)', ()),
 ('mods_fix16', 'mods_fix16', 'soundplex', ('soundplex',)),
 ('mods_fix16_ab_webs_all', 'mods_fix16_ab_webs_all', 'web_occluder(ab_all)', ()),
 ('mods_bridgefix', 'mods_bridgefix', 'web_occluder', ()),
 ('glitchfix2_ab_ring', 'glitchfix2_ab_ring', 'ab_ring', ()),
 ('mods_fix17', 'mods_fix17', 'param_remap', ()),
 ('mods_fix17_webs', 'mods_fix17_webs', 'web_cutout(fix17)', ()),
 ('mods_current', 'mods_current', 'current(consolidation)', ()),
 ('mods_current_webs', 'mods_current_webs', 'web_cutout', ()),
 ('mods_fix18', 'mods_fix18', 'analog_word/soundplex-t5', ('soundplex',)),
 ('mods_fix18_awf_extra', 'mods_fix18_awf_extra', 'awf', ()),
 ('mods_fix19', 'mods_fix19', 'name_string', ()),
 ('mods_fix20', 'mods_fix20', 'dtp_audit', ('dtp_audit',)),
 ('chain_mods_chainfix_min', 'chain_aim/mods_chainfix_min', 'model_point', ()),
]
LABEL = {n: l for n, _, l, _ in CHRONO}
WIRED = {n: w for n, _, _, w in CHRONO if w}
def walk(d):
    root = os.path.join(W, d); out = {}
    if not os.path.isdir(root): return out
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if f in SKIP or '/check' in dp or '/unnamed' in dp: continue
            out[os.path.relpath(os.path.join(dp, f), root).replace(os.sep, '/')] = os.path.join(dp, f)
    return out
def load(path, want=None):
    """sections dict key -> dict(size,data,reloc,meta); want = optional set of keys to keep data for"""
    raw = D.cdrm_decode(open(path, 'rb').read(), 'le')
    h, secs, end = D.parse_drm(raw, 'le')
    out = collections.OrderedDict(); occ = collections.Counter(); order = []
    for s in secs:
        k0 = (s['type'], s['id']); k = (s['type'], s['id'], occ[k0]); occ[k0] += 1
        order.append(k)
        keep = want is None or k in want
        out[k] = dict(size=s['size'], meta=(s['ver'], s['spec'], s['flags']),
                      data=raw[s['data_off']:s['data_off'] + s['size']] if keep else None,
                      reloc=raw[s['reloc_off']:s['reloc_off'] + s['reloc_bytes']] if keep else None)
    return out, order, (h['namesz'], h['padsz'], h['ver'])

def attribute_words(rel_key, fdat, idat, layers_vals, base_name, out_cnt, cat_cnt):
    """fdat/idat: bytes of fresh/installed; layers_vals: list of (name, bytes or None) in chain order (vm first)"""
    if len(fdat) != len(idat): return {}, np.array([],int), np.array([],int)
    n = len(fdat)//4*4
    f = np.frombuffer(fdat[:n], '<u4'); i = np.frombuffer(idat[:n], '<u4')
    idx = np.nonzero(f != i)[0]
    if idx.size == 0: return {}, idx, idx
    names = []; M = []
    for name, b in layers_vals:
        if b is None or len(b) != len(fdat): continue
        names.append(name); M.append(np.frombuffer(b[:n], '<u4')[idx])
    res = collections.Counter()
    if not names:
        cat_cnt['RESID_no_layer_source'] += idx.size; return {'RESID_no_layer_source': int(idx.size)}, idx, np.array([], dtype=int)
    M = np.stack(M); fv = f[idx]; iv = i[idx]; L = len(names)
    lastj = np.full(idx.size, -1); eqF = (M == fv)
    for l in range(L): lastj = np.where(eqF[l], l, lastj)
    eqI = (M == iv)
    firstc = np.full(idx.size, L)
    for l in range(L - 1, -1, -1): firstc = np.where(eqI[l] & (l > lastj), l, firstc)
    unexpl = []
    for n in range(idx.size):
        j = lastj[n]; c = firstc[n]
        if j < 0:
            if M[0, n] == iv[n]: cat = 'DRIFT'          # installed = base, fresh changed a word no installed fix touched
            elif eqI[:, n].any(): cat = 'RESID_fresh_novel'
            else: cat = 'RESID_mixed'
            res[cat] += 1; unexpl.append(n)
        elif c >= L:
            res['RESID_installed_unexplained'] += 1; unexpl.append(n)
        else:
            Lc = names[c]
            if j == c - 1 and WIRED.get(Lc): res['HOOK_NOT_FIRING:' + Lc] += 1
            else: res['EXPLAINED:' + Lc] += 1
    for k, v in res.items():
        out_cnt[k] += v
    return dict(res), idx, idx[np.array(unexpl, dtype=int)] if unexpl else np.array([], dtype=int)


if __name__ == '__main__':
    eff = {}
    for line in open(os.path.join(HERE, 'installed_effective.tsv')):
        f = line.rstrip('\n').split('\t')
        if f[0] == 'relpath': continue
        eff[f[0]] = f[4]
    fresh = {}
    fdir = os.path.join(HERE, 'out_fresh')
    for dp, dn, fn in os.walk(fdir):
        for f in fn:
            if f.endswith('.drm'):
                fresh[os.path.relpath(os.path.join(dp, f), fdir).replace(os.sep, '/')] = os.path.join(dp, f)
    layer_files = {name: walk(d) for name, d, _, _ in CHRONO}
    WIDE_INDEX = collections.defaultdict(list)   # basename -> all .drm paths under work/ (overlays, builds, stages)
    for dp, dn, fn in os.walk(W):
        if '/ws' in dp or '/__pycache__' in dp: continue
        for f in fn:
            if f.endswith('.drm') and f not in SKIP: WIDE_INDEX[f].append(os.path.join(dp, f))
    print('wide index basenames', len(WIDE_INDEX), flush=True)
    word_cat = collections.Counter(); per_file = collections.OrderedDict(); rows = []; hdr = collections.Counter()
    common = sorted(r for r in (set(eff) & set(fresh)) if r.endswith('.drm'))
    print('compared', len(common), 'installed-not-fresh', sum(1 for k in eff if k.endswith('.drm') and k not in fresh), flush=True)
    for rel in common:
        ins, iord, ihdr = load(eff[rel]); frs, ford, fhdr = load(fresh[rel])
        st = collections.Counter(); st['sec_installed'] = len(ins); st['sec_fresh'] = len(frs)
        st['order_same'] = int(iord == ford); st['hdr_drm_same'] = int(ihdr == fhdr)
        if ihdr != fhdr: hdr['drm_header_differs'] += 1
        keys = list(dict.fromkeys(list(ins) + list(frs)))
        # phase 1: which sections differ (need data for both)
        ins, _, _ = load(eff[rel], want=set(keys)); frs, _, _ = load(fresh[rel], want=set(keys))
        diffk = []
        for k in keys:
            a, b = ins.get(k), frs.get(k)
            if a is None or b is None: diffk.append((k, 'ONLY_FRESH' if a is None else 'ONLY_INST')); continue
            if a['meta'] != b['meta']: st['meta_diff'] += 1; hdr['section_meta_differs'] += 1
            if a['data'] == b['data'] and a['reloc'] == b['reloc']: st['same'] += 1; continue
            kind = ('D' if a['data'] != b['data'] else '') + ('R' if a['reloc'] != b['reloc'] else '')
            diffk.append((k, kind))
        st['diff_sections'] = len(diffk)
        # phase 2: chain
        need = {k for k, _ in diffk}
        chain = []
        for name, _, _, _ in CHRONO:
            p = layer_files[name].get(rel)
            if p:
                cs, _, _ = load(p, want=need)
                chain.append((name, cs))
        for k, kind in diffk:
            ta = k[0]
            if kind in ('ONLY_FRESH', 'ONLY_INST'):
                present = [name for name, cs in chain if k in cs]
                if kind == 'ONLY_FRESH':
                    cat = ('EXPLAINED_REMOVED:' + present[-1]) if present else 'RESID_fresh_only'
                    size = frs[k]['size']
                else:
                    cat = ('EXPLAINED_ADDED:' + present[0]) if present else 'RESID_installed_only'
                    size = ins[k]['size']
                st['sec_' + kind] += 1
                rows.append((rel, k, size, kind, cat, '', ''))
                word_cat[cat.split(':')[0]] += 1
                continue
            a, b = ins[k], frs[k]
            if a['data'] != b['data']:
                if a['size'] != b['size']:
                    cat = 'SIZE'
                    lay = [n for n, cs in chain if k in cs and cs[k]['size'] == a['size']][-1:] or ['-']
                    word_cat['SIZE'] += 1; rows.append((rel, k, a['size'], 'D(size)', 'SIZE', lay[0], '')); st['size_diff'] += 1
                else:
                    cnt, _, un = attribute_words(k, b['data'], a['data'], [(n, cs[k]['data'] if k in cs else None) for n, cs in chain],
                                                 'vm_mods_expected', word_cat, word_cat)
                    cnt = dict(cnt)
                    if un.size:   # wide search: does another overlay/build in work/ hold the fresh value at these words?
                        fv = np.frombuffer(b['data'][:len(b['data'])//4*4], '<u4')[un]
                        found = collections.Counter(); left = un.size
                        for cp in WIDE_INDEX.get(os.path.basename(rel), []):
                            if not cp.endswith('/' + rel) or cp == eff[rel] or cp == fresh[rel]: continue
                            cs2, _, _ = load(cp, want={k})
                            if k not in cs2 or cs2[k]['size'] != a['size']: continue
                            cw = np.frombuffer(cs2[k]['data'][:len(cs2[k]['data'])//4*4], '<u4')[un]
                            m = (cw == fv)
                            if m.any():
                                tag = 'WIDE:' + os.path.relpath(cp[:-len(rel) - 1], W)
                                found[tag] += int(m.sum())
                        fv = None
                        for t_, v_ in found.items(): cnt[t_] = cnt.get(t_, 0) + v_
                        cnt['RESID_after_wide'] = int(un.size - min(sum(found.values()), un.size))
                    summ = ';'.join('%s=%d' % kv for kv in sorted(cnt.items(), key=lambda x: -x[1]))
                    st['words_diff'] += int(sum(cnt.values()))
                    rows.append((rel, k, a['size'], 'D', 'WORDS', summ, ''))
            if a['reloc'] != b['reloc']:
                seq = [(n, cs[k]['reloc']) for n, cs in chain if k in cs]
                vals = [v for _, v in seq]
                j = max([i for i, v in enumerate(vals) if v == b['reloc']], default=-1)
                c = next((i for i, v in enumerate(vals) if i > j and v == a['reloc']), None)
                cat = ('RELOC_EXPLAINED:' + seq[c][0]) if (c is not None and j >= 0) else 'RELOC_RESID'
                st['reloc_diff'] += 1
                rows.append((rel, k, a['size'], 'R', cat, '', ''))
                word_cat[cat.split(':')[0]] += 1
        per_file[rel] = dict(st)
    with open(os.path.join(HERE, 'diff_sections.tsv'), 'w') as f:
        f.write('relpath\tsec_type\tsec_id\tocc\tsize\tkind\tcategory\tlayers_or_words\tnote\n')
        for rel, k, size, kind, cat, lay, note in rows:
            f.write('%s\t%d\t%d\t%d\t%d\t%s\t%s\t%s\t%s\n' % (rel, k[0], k[1], k[2], size or 0, kind, cat, lay, note))
    json.dump(dict(per_file=per_file, word_cat=dict(word_cat), hdr=dict(hdr),
                   installed_not_fresh=sorted(k for k in eff if k.endswith('.drm') and k not in fresh),
                   fresh_only=sorted(set(fresh) - set(eff))), open(os.path.join(HERE, '_summary.json'), 'w'), indent=1)
    print('WORD/SECTION CATEGORIES', dict(word_cat)); print('HDR', dict(hdr))
