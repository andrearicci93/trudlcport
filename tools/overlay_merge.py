#!/usr/bin/env python3
"""overlay_merge.py - fonde in un unico overlay candidato i layer di correzione DRM costruiti
sopra l'overlay installato (base = work/ws/rebuild/installed_effective.tsv, colonna relpath -> abs_path).

Per ogni file DRM presente in almeno un layer:
  - parsa base e layer (tools/drm_write.py, cross-check con tools/drm.py);
  - confronta sezione per sezione (indice) e parola per parola (4 byte) ogni layer con la base;
  - meta di sezione (type/id/ver/flags/spec/pad), reloc, dati, nomi dipendenze e header sono chiavi;
  - sezioni in coda (indice >= base) = aggiunte; sezioni con dimensione diversa = sostituzione intera;
  - stesso valore da piu' layer -> applicato una volta; valori diversi -> CONFLITTO: la chiave resta
    al valore base e finisce in CONFLITTI.md con il layer che "vincerebbe" (ultimo nell'ordine dei layer,
    stessa semantica dell'overlay: ordine basso -> alto, il piu' alto vince);
  - scrittura DRM ricostruita (stesso container della base: CDRM o raw), verifica: riparsing, sezioni non
    toccate byte-identiche alla base, cross-check indipendente con tools/drm.py.

Output (solo file cambiati): <out>/<relpath>, <out>/md5.txt, MERGE_REPORT.md, CONFLITTI.md, merge_detail.json
(in work/ws/merge/).

Uso:
  python3 -I tools/overlay_merge.py                       # layer default: savehang, refs, fpfloat
  python3 -I tools/overlay_merge.py --layer dtpkeys=work/ws/dtpkeys/out   # aggiungere un layer (in coda)
  python3 -I tools/overlay_merge.py --selftest             # solo test (base->0 parole, conflitto sintetico, roundtrip)
Opzioni: --out DIR, --merge-dir DIR, --manifest TSV. Layer da escludere per regola: mat/out/test_from_fix14.
"""
import sys, os, json, csv, hashlib, copy, argparse, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drm_write as W
import drm as D1

ROOT = os.path.normpath(os.path.join(HERE, '..'))
WS = os.path.join(ROOT, 'work', 'ws')
MERGE_DIR = os.path.join(WS, 'merge')
MANIFEST = os.path.join(WS, 'rebuild', 'installed_effective.tsv')
DEFAULT_LAYERS = [('savehang', 'savehang/out'), ('refs', 'refs/out'), ('fpfloat', 'fpfloat/out')]
META = ('type', 'id', 'ver', 'flags', 'spec', 'pad')
HDR_ENDIAN = 'le'


def rel_norm(p):
    return p.replace(os.sep, '/')


def load_manifest(path):
    m = {}
    with open(path, newline='') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            m[rel_norm(row['relpath'])] = row.get('abs_path') or row.get('path')
    return m


def parse_file(path):
    raw_file = open(path, 'rb').read()
    cdrm = raw_file[:4] == b'CDRM'
    raw = D1.cdrm_decode(raw_file, HDR_ENDIAN)
    D = W.read(raw, HDR_ENDIAN)
    return dict(path=path, file=raw_file, cdrm=cdrm, raw=raw, D=D)


def diff_bytes(a, b):
    """list of (off, new_bytes) for each 4-byte word where a != b (same length)"""
    out = []
    for off in range(0, len(a), 4):
        x, y = a[off:off + 4], b[off:off + 4]
        if x != y:
            out.append((off, y))
    return out


def layer_changes(base, lay):
    """key -> value for every difference of lay against base. Returns (changes, stats) or (None, error)."""
    bs, ls = base.sections, lay.sections
    if len(ls) < len(bs):
        return None, 'layer rimuove sezioni (%d < %d): non supportato' % (len(ls), len(bs))
    ch = {}
    st = dict(words=0, reloc_words=0, meta=0, replaced=[], added=0, names=False)
    if base.names != lay.names:
        ch[('names',)] = lay.names
        st['names'] = True
    if base.pad != lay.pad:
        ch[('pad',)] = lay.pad
    if (base.ver, base.u0, base.u1) != (lay.ver, lay.u0, lay.u1):
        ch[('hdr',)] = (lay.ver, lay.u0, lay.u1)
    for i in range(len(bs)):
        b, l = bs[i], ls[i]
        if len(b.data) != len(l.data) or len(b.reloc) != len(l.reloc):
            ch[('sec', i)] = (l.type, l.id, l.ver, l.flags, l.spec, l.pad, l.reloc, l.data)
            st['replaced'].append(i)
            continue
        for f in META:
            if getattr(b, f) != getattr(l, f):
                ch[('meta', i, f)] = getattr(l, f)
                st['meta'] += 1
        for off, v in diff_bytes(b.data, l.data):
            ch[('data', i, off)] = v
            st['words'] += 1
        for off, v in diff_bytes(b.reloc, l.reloc):
            ch[('reloc', i, off)] = v
            st['reloc_words'] += 1
    for k, l in enumerate(ls[len(bs):]):
        ch[('add', k)] = (l.type, l.id, l.ver, l.flags, l.spec, l.pad, l.reloc, l.data)
        st['added'] += 1
    return ch, st


def key_str(k):
    if k[0] == 'data' or k[0] == 'reloc':
        return '%s[sec %d, +0x%x]' % (k[0], k[1], k[2])
    if k[0] == 'meta':
        return 'meta[sec %d].%s' % (k[1], k[2])
    if k[0] == 'sec':
        return 'sezione intera[%d]' % k[1]
    if k[0] == 'add':
        return 'sezione aggiunta[+%d]' % k[1]
    return '/'.join(str(x) for x in k)


def base_value(base, k):
    if k[0] == 'data':
        return base.sections[k[1]].data, k[2]
    if k[0] == 'reloc':
        return base.sections[k[1]].reloc, k[2]
    return None, None


INST_CORRECT = ('inst', 'inst(layer)')


def load_log_words(path):
    rows = {}
    with open(path, newline='') as f:
        rd = csv.DictReader(f, delimiter='\t')
        for r in rd:
            rows.setdefault(rel_norm(r['file']), []).append(
                (int(r['dtp'].split()[-1]), int(r['off'], 16), r['old'], r['new']))
    return rows


def load_verdicts(path):
    v = {}
    with open(path, newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            v[(rel_norm(r['file']), int(r['dtp']), int(r['off'], 16))] = r['verdict']
    return v


def make_dtp_filter(rel, logrows, verdicts):
    """keep only the words listed in log_words.tsv (new value must match), drop installed-correct ones,
    report everything else the layer changes (extra) and listed words not changed (missing)."""
    def flt(base, ch):
        expect = {}
        st = dict(log=0, excluded_inst=0, old_mismatch=[], unmapped=[], missing=[], extra=[], kept=0)
        idmap = {}
        for i, sec in enumerate(base.sections):
            if sec.type == 7:
                idmap.setdefault(sec.id, []).append(i)
        excl = set()
        for dtp, off, old, new in logrows.get(rel, []):
            st['log'] += 1
            idx = idmap.get(dtp)
            if not idx or len(idx) != 1:
                st['unmapped'].append((dtp, off)); continue
            i = idx[0]
            if verdicts.get((rel, dtp, off)) in INST_CORRECT:
                st['excluded_inst'] += 1; excl.add(('data', i, off)); continue
            if base.sections[i].data[off:off + 4].hex() != old:
                st['old_mismatch'].append((dtp, off))
            expect[('data', i, off)] = bytes.fromhex(new)
        kept = {}
        for k, v in ch.items():
            if k in excl:
                continue
            if k in expect and v == expect[k]:
                kept[k] = v
            else:
                st['extra'].append(k)
        st['missing'] = [k for k in expect if k not in kept]
        st['kept'] = len(kept)
        return kept, st
    return flt


def merge_drm(rel, base_p, layers, layer_order):
    """base_p: parsed base dict; layers: list of (layer_name, parsed layer dict).
    returns dict with new raw bytes (or None if unchanged), report info, conflicts."""
    base = base_p['D']
    per_layer = {}
    errors = []
    for name, lp in layers:
        ch, st = layer_changes(base, lp['D'])
        if ch is None:
            errors.append((name, st))
            continue
        if lp.get('filter') is not None:
            ch, fst = lp['filter'](base, ch)
            st['filter'] = fst
        per_layer[name] = (ch, st)

    keys = {}
    for name in layer_order:
        if name not in per_layer:
            continue
        for k, v in per_layer[name][0].items():
            keys.setdefault(k, {})[name] = v

    applied = {}      # key -> (value, [layers contributing])
    conflicts = []    # dicts
    for k, vals in keys.items():
        uniq = []
        for v in vals.values():
            if v not in uniq:
                uniq.append(v)
        contributors = [n for n in layer_order if n in vals]
        if len(uniq) == 1:
            applied[k] = (uniq[0], contributors)
        else:
            bv, boff = base_value(base, k)
            c = dict(key=k, vals=vals, contributors=contributors, base=None, overlap=False)
            if bv is not None:
                c['base'] = bv[boff:boff + len(next(iter(vals.values())))]
                # byte positions changed by 2+ layers
                pos = {}
                for n, v in vals.items():
                    for j in range(len(v)):
                        if v[j] != bv[boff + j]:
                            pos.setdefault(boff + j, set()).add(n)
                c['overlap'] = any(len(s) > 1 for s in pos.values())
            c['winner'] = contributors[-1]
            conflicts.append(c)

    # section-level conflicts: a replaced section with any other key of the same section from another layer
    sec_repl = {k[1] for k in applied if k[0] == 'sec'}
    for k in list(applied):
        if k[0] in ('data', 'reloc', 'meta') and k[1] in sec_repl:
            conflicts.append(dict(key=k, vals={applied[k][1][0]: applied[k][0]}, contributors=applied[k][1],
                                  base=None, overlap=False, winner=applied[k][1][-1],
                                  note='sezione sostituita intera da altro layer'))
            del applied[k]

    # additions: must be a contiguous prefix
    adds = sorted(k[1] for k in list(keys) if k[0] == 'add')
    conflict_adds = {c['key'][1] for c in conflicts if c['key'][0] == 'add'}
    keep_adds = []
    for a in adds:
        if a in conflict_adds:
            break
        keep_adds.append(a)
    for a in adds:
        if a not in keep_adds and ('add', a) in applied:
            v = applied.pop(('add', a))
            conflicts.append(dict(key=('add', a), vals={}, contributors=v[1], base=None, overlap=False,
                                  winner=v[1][-1], note='append non applicato: prefisso in conflitto'))

    # ---- build new Drm
    bs = base.sections
    patches = {}
    for k, (v, _) in applied.items():
        if k[0] in ('data', 'reloc'):
            patches.setdefault((k[0], k[1]), []).append((k[2], v))
    new_secs = []
    touched = set()
    for i, s in enumerate(bs):
        if ('sec', i) in applied:
            v = applied[('sec', i)][0]
            ns = W.Section(v[0], v[1], v[7], v[6], v[3], v[2], v[4], v[5])
            touched.add(i)
        else:
            ns = W.Section(s.type, s.id, bytearray(s.data), bytes(s.reloc), s.flags, s.ver, s.spec, s.pad)
            for f in META:
                if ('meta', i, f) in applied:
                    setattr(ns, f, applied[('meta', i, f)][0])
                    touched.add(i)
            for off, v in patches.get(('data', i), []):
                ns.data = ns.data[:off] + bytearray(v) + ns.data[off + len(v):]
                touched.add(i)
            for off, v in patches.get(('reloc', i), []):
                ns.reloc = ns.reloc[:off] + bytearray(v) + ns.reloc[off + len(v):]
                touched.add(i)
            ns.data = bytes(ns.data)
            ns.reloc = bytes(ns.reloc)
        new_secs.append(ns)
    for a in keep_adds:
        if ('add', a) in applied:
            v = applied[('add', a)][0]
            new_secs.append(W.Section(v[0], v[1], v[7], v[6], v[3], v[2], v[4], v[5]))
            touched.add(len(bs) + a)
    names = base.names
    pad = base.pad
    ver, u0, u1 = base.ver, base.u0, base.u1
    if ('names',) in applied:
        names = applied[('names',)][0]
    if ('pad',) in applied:
        pad = applied[('pad',)][0]
    if ('hdr',) in applied:
        ver, u0, u1 = applied[('hdr',)][0]
    D2 = W.Drm(new_secs, names, pad, ver, u0, u1)
    raw2 = D2.write(HDR_ENDIAN)
    return dict(raw2=raw2, D2=D2, applied=applied, conflicts=conflicts, per_layer=per_layer,
                errors=errors, touched=touched, keep_adds=keep_adds)


def count_changed_bytes(a, b):
    n = min(len(a), len(b))
    cnt = sum(1 for i in range(n) if a[i] != b[i]) if a != b else 0
    return cnt + abs(len(a) - len(b))


def verify(base_p, raw2, D2, touched, cdrm_out_bytes):
    """re-parse the written file; check untouched sections byte-identical to base; cross-check with drm.py"""
    res = dict(ok=True, msgs=[])
    D3 = W.read(raw2, HDR_ENDIAN)
    if len(D3.sections) != len(D2.sections):
        res['ok'] = False; res['msgs'].append('numero sezioni diverso dopo riparsing')
    for i, (a, b) in enumerate(zip(D2.sections, D3.sections)):
        if (a.data, a.reloc) != (b.data, b.reloc) or any(getattr(a, f) != getattr(b, f) for f in META):
            res['ok'] = False; res['msgs'].append('sezione %d diversa dopo riparsing' % i); break
    bs = base_p['D'].sections
    untouched_ok = 0
    for i in range(min(len(bs), len(D3.sections))):
        if i in touched:
            continue
        s, t = bs[i], D3.sections[i]
        if s.data == t.data and s.reloc == t.reloc and all(getattr(s, f) == getattr(t, f) for f in META):
            untouched_ok += 1
        else:
            res['ok'] = False; res['msgs'].append('sezione non toccata %d non identica alla base' % i)
            break
    res['untouched_identical'] = untouched_ok
    # independent parse with tools/drm.py
    try:
        h, secs = D1.sections_with_data(raw2, HDR_ENDIAN)
        if len(secs) != len(D3.sections):
            res['ok'] = False; res['msgs'].append('drm.py: numero sezioni diverso')
        else:
            for s, t in zip(secs, D3.sections):
                if s['data'] != t.data or s['reloc'] != t.reloc or s['type'] != t.type or s['id'] != t.id:
                    res['ok'] = False; res['msgs'].append('drm.py: sezione %d diversa' % s['i']); break
    except Exception as e:
        res['ok'] = False; res['msgs'].append('drm.py: errore %r' % (e,))
    if cdrm_out_bytes is not None:
        if D1.cdrm_decode(cdrm_out_bytes, HDR_ENDIAN) != raw2:
            res['ok'] = False; res['msgs'].append('CDRM roundtrip diverso')
    return res


def selftest(base_map, files):
    lines = []
    ok_all = True
    # 1) writer fidelity on every base file used
    n = nb = ncd = ncd_ok = 0
    for rel in files:
        if rel not in base_map:
            continue
        p = parse_file(base_map[rel])
        n += 1
        w = p['D'].write(HDR_ENDIAN)
        if w != p['raw']:
            nb += 1
        if p['cdrm']:
            ncd += 1
            if W.cdrm_encode(w, HDR_ENDIAN) == p['file']:
                ncd_ok += 1
    lines.append('writer roundtrip raw: %d file, %d diversi' % (n, nb))
    lines.append('CDRM re-encode byte-identico: %d/%d' % (ncd_ok, ncd))
    if nb:
        ok_all = False
    # 2) base as layer -> 0 changed words
    zero_fail = []
    for rel in files:
        if rel not in base_map:
            continue
        p = parse_file(base_map[rel])
        ch, st = layer_changes(p['D'], p['D'])
        if ch:
            zero_fail.append(rel)
    lines.append('base-come-layer: %d file con differenze (atteso 0)' % len(zero_fail))
    if zero_fail:
        ok_all = False
    # 3) synthetic conflicts on one dungeon file
    rel = next((r for r in files if r in base_map), None)
    if rel:
        bp = parse_file(base_map[rel])
        B = bp['D']
        A = copy.deepcopy(B); Bb = copy.deepcopy(B); C = copy.deepcopy(B)
        idx = next(i for i, s in enumerate(B.sections) if len(s.data) >= 8)
        d = bytearray(B.sections[idx].data)
        d[0:4] = bytes([d[0] ^ 1, d[1], d[2], d[3]]); A.sections[idx].data = bytes(d)
        d2 = bytearray(B.sections[idx].data); d2[0:4] = bytes([d2[0] ^ 2, d2[1], d2[2], d2[3]]); Bb.sections[idx].data = bytes(d2)
        C.sections[idx].data = bytes(d)  # same as A -> no conflict
        C.sections.append(copy.deepcopy(B.sections[idx]))
        layers = [('a', dict(D=A)), ('b', dict(D=Bb)), ('c', dict(D=C))]
        r = merge_drm(rel, dict(D=B), layers, ['a', 'b', 'c'])
        nconf = sum(1 for c in r['conflicts'] if c['key'][0] == 'data' and c['key'][1] == idx)
        nadd = len([k for k in r['applied'] if k[0] == 'add'])
        lines.append('sintetico %s: conflitti attesi 1 -> %d; append applicato (atteso 1) -> %d' % (rel, nconf, nadd))
        if nconf != 1 or nadd != 1:
            ok_all = False
    lines.append('selftest: %s' % ('OK' if ok_all else 'FAIL'))
    return ok_all, lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--layer', action='append', default=[], help='NOME=DIR (ordine = precedenza crescente)')
    ap.add_argument('--out', default=os.path.join(MERGE_DIR, 'out'))
    ap.add_argument('--merge-dir', default=MERGE_DIR)
    ap.add_argument('--manifest', default=MANIFEST)
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--tag', default='', help='suffisso per i report (es. _full)')
    a = ap.parse_args()

    base_map = load_manifest(a.manifest)
    layer_specs = []
    if a.layer:
        for s in a.layer:
            name, _, d = s.partition('=')
            layer_specs.append((name, d if os.path.isabs(d) else os.path.join(ROOT, d)))
    else:
        layer_specs = [(n, os.path.join(WS, d)) for n, d in DEFAULT_LAYERS]
    # ordine = precedenza crescente (l'ultimo vince nel campo 'vincerebbe'). Priorita' richiesta:
    # savehang > refs > fpfloat > dtpkeys  => in CLI passare dtpkeys per primo, savehang per ultimo.
    for name, d in layer_specs:
        if 'test_from_fix14' in d or os.path.join('mat', 'out') in d:
            sys.exit('layer vietato: %s' % d)
        if not os.path.isdir(d):
            sys.exit('layer mancante: %s' % d)
    layer_order = [n for n, _ in layer_specs]
    dtp_logs, dtp_verdicts = {}, {}
    for name, d in layer_specs:
        if name.startswith('dtpkeys'):
            dtp_logs[name] = load_log_words(os.path.join(d, 'log_words.tsv'))
            dtp_verdicts[name] = load_verdicts(os.path.join(WS, 'dtpkeys', 'out', 'drift_verdicts.tsv'))

    # collect layer files
    layer_files = {}   # rel -> [(name, path)]
    for name, d in layer_specs:
        for r, _, fs in os.walk(d):
            for f in sorted(fs):
                if not f.lower().endswith('.drm'):
                    continue
                p = os.path.join(r, f)
                rel = rel_norm(os.path.relpath(p, d))
                layer_files.setdefault(rel, []).append((name, p))

    lines = []
    ok, st_lines = selftest(base_map, list(layer_files))
    lines += ['SELFTEST'] + ['  ' + s for s in st_lines]
    print('\n'.join(lines))
    if a.selftest:
        return

    out_dir = a.out
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    os.makedirs(a.merge_dir, exist_ok=True)

    all_conf = []
    detail = {}
    per_file = []
    skipped = []
    for rel in sorted(layer_files):
        if rel not in base_map:
            skipped.append((rel, 'nessuna base nel manifest (file nuovo: fuori scope)'))
            continue
        bpath = base_map[rel]
        if not os.path.isfile(bpath):
            skipped.append((rel, 'base non trovata su disco: %s' % bpath))
            continue
        bp = parse_file(bpath)
        layers = []
        for name, p in layer_files[rel]:
            lp = parse_file(p)
            if name in dtp_logs:
                lp['filter'] = make_dtp_filter(rel, dtp_logs[name], dtp_verdicts[name])
            layers.append((name, lp))
        # layers in layer_order
        layers.sort(key=lambda t: layer_order.index(t[0]))
        r = merge_drm(rel, bp, layers, layer_order)
        raw2 = r['raw2']
        changed = raw2 != bp['raw']
        rec = dict(rel=rel, base=bpath, layers=[n for n, _ in layers], changed=changed, words=0,
                   bytes=0, conflicts=len(r['conflicts']), replaced=0, added=0, errors=r['errors'])
        rec['per_layer'] = {}
        for name, (ch, st) in r['per_layer'].items():
            rec['per_layer'][name] = dict(words=st['words'], reloc_words=st['reloc_words'], meta=st['meta'],
                                          replaced=len(st['replaced']), added=st['added'],
                                          filter=st.get('filter'))
        applied_layers = {}
        for k, (v, contrib) in r['applied'].items():
            for n in contrib:
                applied_layers[n] = applied_layers.get(n, 0) + 1
            if k[0] == 'data':
                rec['words'] += 1
            if k[0] == 'sec':
                rec['replaced'] += 1
            if k[0] == 'add':
                rec['added'] += 1
        rec['applied_keys_per_layer'] = applied_layers
        rec['bytes'] = sum(len(v) for k, (v, _) in r['applied'].items() if k[0] in ('data', 'reloc'))
        for c in r['conflicts']:
            c['rel'] = rel
            c['base_section'] = None
            k = c['key']
            if k[0] in ('data', 'reloc', 'meta', 'sec'):
                s = bp['D'].sections[k[1]]
                c['base_section'] = (k[1], s.type, s.id, len(s.data))
            elif k[0] == 'add':
                c['base_section'] = ('+%d' % k[1], None, None, None)
            all_conf.append(c)
        rec['touched'] = sorted(r['touched'])
        if changed:
            cdrm_bytes = W.cdrm_encode(raw2, HDR_ENDIAN) if bp['cdrm'] else None
            if cdrm_bytes is not None and D1.cdrm_decode(cdrm_bytes, HDR_ENDIAN) != raw2:
                raise SystemExit('CDRM encode roundtrip fallito: %s' % rel)
            outb = cdrm_bytes if cdrm_bytes is not None else raw2
            v = verify(bp, raw2, r['D2'], set(r['touched']), cdrm_bytes)
            rec['verify'] = v
            if not v['ok']:
                raise SystemExit('verifica fallita %s: %s' % (rel, v['msgs']))
            op = os.path.join(out_dir, rel)
            os.makedirs(os.path.dirname(op), exist_ok=True)
            with open(op, 'wb') as f:
                f.write(outb)
            rec['md5'] = hashlib.md5(outb).hexdigest()
            rec['size'] = len(outb)
        else:
            rec['verify'] = None
        per_file.append(rec)
        detail[rel] = dict(rec)
    # outputs
    with open(os.path.join(out_dir, 'md5.txt'), 'w') as f:
        for rec in per_file:
            if rec['changed']:
                f.write('%s  %s\n' % (rec['md5'], rec['rel']))
    json.dump(dict(per_file=per_file, conflicts=[dict(c, key=list(map(str, c['key']))) for c in all_conf],
                   skipped=skipped, layers=layer_specs), open(os.path.join(a.merge_dir, 'merge_detail%s.json' % a.tag), 'w'),
              indent=1, default=str)
    write_reports(a, per_file, all_conf, skipped, layer_specs, lines + st_lines)
    changed = [r for r in per_file if r['changed']]
    print('files=%d changed=%d conflicts=%d skipped=%d' % (len(per_file), len(changed), len(all_conf), len(skipped)))


def hx(b):
    if b is None:
        return '-'
    if isinstance(b, tuple):
        return 'sezione(type=%s,id=%s,data=%d)' % (b[0], b[1], len(b[7]))
    return b.hex()


def write_reports(a, per_file, all_conf, skipped, layer_specs, st_lines):
    L = []
    L.append('# MERGE_REPORT - overlay_merge.py')
    L.append('')
    L.append('Base: `%s` (relpath -> abs_path, overlay installato effettivo).' % os.path.relpath(a.manifest, ROOT))
    L.append('Layer (ordine di precedenza crescente, l\'ultimo vince nel "vincerebbe"):')
    for n, d in layer_specs:
        L.append('- `%s` = `%s`' % (n, os.path.relpath(d, ROOT)))
    L.append('- NON inclusi: `work/ws/mat/out/test_from_fix14` (vietato), `work/ws/dtpkeys/out` (da aggiungere con `--layer dtpkeys=...`).')
    L.append('')
    L.append('## Selftest')
    L.append('```')
    L.extend(st_lines)
    L.append('```')
    L.append('')
    L.append('## Totali')
    changed = [r for r in per_file if r['changed']]
    tw = sum(r['words'] for r in per_file)
    tb = sum(r['bytes'] for r in changed)  # byte dentro le sezioni (l'aggiunta di sezioni sposta il layout: non si conta a file)
    L.append('- file DRM con layer: %d; file cambiati (scritti in out/): %d' % (len(per_file), len(changed)))
    L.append('- parole (4 byte) cambiate applicate: %d; byte di parole cambiate (dentro le sezioni): %d' % (tw, tb))
    L.append('- conflitti (non applicati): %d' % len(all_conf))
    L.append('- file saltati: %d' % len(skipped))
    L.append('')
    L.append('## Per file')
    L.append('| file | layer presenti | parole applicate | sezioni sostituite | sezioni aggiunte | conflitti | cambiato | verifica |')
    L.append('|---|---|---|---|---|---|---|---|')
    for r in per_file:
        ver = 'n/a' if r['verify'] is None else ('OK, sezioni non toccate identiche: %d' % r['verify']['untouched_identical'] if r['verify']['ok'] else 'FAIL')
        L.append('| %s | %s | %d | %d | %d | %d | %s | %s |' % (
            r['rel'], ', '.join(r['layers']), r['words'], r['replaced'], r['added'], r['conflicts'],
            'si' if r['changed'] else 'no', ver))
    L.append('')
    L.append('## Dettaglio per layer (chiavi che il layer differisce dalla base, prima dei conflitti)')
    L.append('| file | layer | parole diverse | parole reloc | meta | sezioni sostituite | sezioni aggiunte | chiavi applicate |')
    L.append('|---|---|---|---|---|---|---|---|')
    for r in per_file:
        for n in r['layers']:
            pl = r['per_layer'].get(n)
            if pl is None:
                L.append('| %s | %s | (errore/saltato: vedi errors nel detail) | | | | | |' % (r['rel'], n))
                continue
            L.append('| %s | %s | %d | %d | %d | %d | %d | %d |' % (
                r['rel'], n, pl['words'], pl['reloc_words'], pl['meta'], pl['replaced'], pl['added'],
                r['applied_keys_per_layer'].get(n, 0)))
    for r in per_file:
        if r['errors']:
            L.append('')
            L.append('ERRORI %s: %s' % (r['rel'], r['errors']))
    if skipped:
        L.append('')
        L.append('## File saltati')
        for rel, why in skipped:
            L.append('- `%s`: %s' % (rel, why))
    L.append('')
    L.append('Nota: "parole" = parole a 4 byte (granularita\' del confronto). Nulla e\' installato; nessuna VM; file esistenti non modificati.')
    L.append('')
    L.append('## Verifica layer dtpkeys (filtro log_words.tsv)')
    L.append('Il layer dtpkeys entra SOLO con le parole di log_words.tsv (new deve combaciare); parole marcate installato-corretto (verdict inst / inst(layer)) escluse (vince la base installata); tutto il resto che il layer cambia = EXTRA (scartato e segnalato).')
    L.append('| file | parole in log | applicate | escluse installato-corretto | non mappate | old diverso dalla base | mancanti nel layer | EXTRA (cambi fuori log) |')
    L.append('|---|---|---|---|---|---|---|---|')
    anyextra = False
    for r in per_file:
        for n, pl in r['per_layer'].items():
            f = pl.get('filter')
            if not f:
                continue
            L.append('| %s | %d | %d | %d | %d | %d | %d | %d |' % (r['rel'], f['log'], f['kept'], f['excluded_inst'],
                     len(f['unmapped']), len(f['old_mismatch']), len(f['missing']), len(f['extra'])))
            if f['extra'] or f['missing'] or f['old_mismatch'] or f['unmapped']:
                anyextra = True
    L.append('')
    L.append('ESITO: %s' % ('tutto coerente con log_words.tsv' if not anyextra else 'SEGNALAZIONI: vedi righe con valori > 0'))
    open(os.path.join(a.merge_dir, 'MERGE_REPORT%s.md' % a.tag), 'w').write('\n'.join(L) + '\n')

    C = []
    C.append('# CONFLITTI - overlay_merge.py')
    C.append('')
    C.append('Parole/chiavi con valori DIVERSI da layer diversi sulla stessa posizione. NON applicate: il file resta al valore base in quella posizione.')
    C.append('"Vincerebbe" = layer ultimo nell\'ordine di precedenza (nominale, da decidere a mano).')
    C.append('"Byte sovrapposti" = almeno un byte modificato da 2+ layer (conflitto reale); altrimenti i layer toccano byte diversi della stessa parola (conflitto solo a livello parola).')
    C.append('')
    C.append('Totale conflitti: %d' % len(all_conf))
    C.append('')
    C.append('| file | sezione (idx, type, id, size) | chiave | base | valori per layer | vincerebbe | byte sovrapposti | nota |')
    C.append('|---|---|---|---|---|---|---|---|')
    for c in all_conf:
        vals = '; '.join('%s=%s' % (n, hx(v) if not isinstance(v, tuple) else hx(v)) for n, v in c['vals'].items()) or '-'
        k = c['key']
        ks = key_str(k)
        if k[0] in ('data', 'reloc'):
            ks += ' @0x%x' % k[2]
        bs = c['base_section']
        bsec = '%s,%s,%s,%s' % bs if bs else '-'
        C.append('| %s | %s | %s | %s | %s | %s | %s | %s |' % (
            c['rel'], bsec, ks, hx(c['base']) if c.get('base') is not None else '-', vals, c.get('winner', '-'),
            'si' if c.get('overlap') else 'no', c.get('note', '')))
    open(os.path.join(a.merge_dir, 'CONFLITTI%s.md' % a.tag), 'w').write('\n'.join(C) + '\n')


if __name__ == '__main__':
    main()
