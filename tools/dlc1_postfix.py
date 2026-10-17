"""dlc1_postfix.py - post-passo della pipeline DLC1 (offline, nessuna VM, nessuna installazione).

Prende una directory di DRM freschi (riconversione, default work/ws/rebuild/out_fresh2) e applica, in ordine:
  1. streamname_fix.fix_section      nomi streamgroup (tabella type0, parola a cavallo del NUL invertita)   [savehang]
  2. R12 di refs_scan.string_fixes   stringhe name-like type0 corrotte (stessa logica di refs_scan.scan_strings,
                                     per singolo file, sulla directory fresca invece che sull'overlay)       [refs]
  3. parole di work/ws/dtpkeys/out/min/log_words.tsv, applicate per (file, DTP id, offset) SOLO se il valore
     corrente e' quello 'old' del log.  Se il valore corrente e' gia' 'new' -> gia' presente (no-op).
     Qualsiasi altro valore -> saltata e contata.  Le posizioni in FORBID (unit id corrotti dell'out/full,
     vedi work/ws/dtpkeys/NOTES_agent.md) vengono rifiutate anche se comparissero nel log.

Scrive SOLO in una directory di output nuova sotto work/ws/converge/ (default work/ws/converge/out_post):
i file non toccati sono copiati identici, quelli toccati sono riscritti; md5.txt rigenerato.
Mai sopra out_fresh2 o sugli overlay.

usage:
  tools/venv/bin/python -I tools/dlc1_postfix.py [--src DIR] [--out DIR] [--no-words] [--only FILE,FILE]
Report: OUT/../postfix_report.tsv (per file: conteggi di ogni passo), riepilogo su stdout.
"""
import sys, os, re, shutil, hashlib, collections, argparse
TOOLS = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, TOOLS)
ROOT = os.path.normpath(os.path.join(TOOLS, '..'))
WS = os.path.join(ROOT, 'work', 'ws')
CONV = os.path.join(WS, 'converge')
DEF_SRC = os.path.join(WS, 'rebuild', 'out_fresh2')
DEF_OUT = os.path.join(CONV, 'out_post')
WORDS_LOG = os.path.join(WS, 'dtpkeys', 'out', 'min', 'log_words.tsv')
# unit id corrotti (out/full, NON nel min): (file, DTP id, offset) -> word [off, off+4) non si tocca mai
FORBID = {('dlc_dungeon.drm', 20258, 0x3308), ('dlc_dungeon.drm', 20258, 0x7cb8), ('dlc_dungeonhalla.drm', 20493, 0xed8)}

import drm_write as DW
import streamname_fix as SN
import refs_scan as RS
import soundplex_fix as SF


def step_streamname(rel, raw):
    """-> (new raw, n_sections_changed)"""
    new, log = SN.fix_section(rel, raw)
    return new, len(log)


def step_strings(rel, raw):
    """R12 per file, come refs_scan.scan_strings (che lavora su overlay): -> (new raw, n_fixed, n_manual)"""
    if not rel.endswith('.drm') or rel.startswith(('cinstream', 'music')): return raw, 0, 0
    try: xs = SF.xsecs_of(rel)
    except Exception: xs = None
    if not xs: return raw, 0, 0
    D = DW.read(raw, 'le')
    if len(xs) == len(D.sections): pairs = list(zip(xs, D.sections))
    else:
        x0 = [x for x in xs if x['type'] == 0 and x['data'] is not None]; p0 = [q for q in D.sections if q.type == 0]
        if len(x0) != len(p0) or any(len(a['data']) != len(b.data) for a, b in zip(x0, p0)): return raw, 0, 0
        pairs = list(zip(x0, p0))
    ch = False; nfix = 0; nman = 0
    for x, sct in pairs:
        if x['data'] is None or x['type'] != sct.type or sct.type != 0 or len(x['data']) != len(sct.data): continue
        nd, lg = RS.string_fixes(x['data'], sct.data)
        for a, xs_, ps_, st in lg:
            if st == 'fixed': nfix += 1
            else: nman += 1
        if nd is not None: sct.data = bytes(nd); ch = True
    if not ch: return raw, nfix, nman
    out = D.write('le')
    return (DW.cdrm_encode(out, 'le') if raw[:4] == b'CDRM' else out), nfix, nman


def load_words(path):
    """-> dict file -> list of (dtp, off, old_hex, new_hex, source) ; header of log_words.tsv"""
    by = collections.defaultdict(list)
    lines = open(path).read().splitlines()
    for ln in lines[1:]:
        f = ln.split('\t')
        rel, dtp, off, old, new, src = f[0], int(f[1].split()[1]), int(f[2], 16), f[3], f[4], f[5]
        by[rel].append((dtp, off, old, new, src))
    return by


def step_words(rel, raw, rows, st):
    """apply rows of one file. st = Counter. -> new raw"""
    import dtp_audit as A
    xs = A.xsecs(rel)
    if xs is None:
        st['words_no_xbox_source'] += len(rows); return raw
    D = DW.read(raw, 'le')
    pair = {D.sections[i].id: i for x, i in A.section_pairs(xs, D) if x['type'] == 7}
    touched = []
    for dtp, off, old, new, src in rows:
        if any(r == rel and d == dtp and off <= fo < off + 4 for r, d, fo in FORBID):
            st['words_forbidden'] += 1; continue
        i = pair.get(dtp)
        if i is None: st['words_no_section'] += 1; continue
        sec = D.sections[i]
        if off + 4 > len(sec.data): st['words_out_of_range'] += 1; continue
        cur = bytes(sec.data[off:off + 4]).hex()
        if cur == old:
            b = bytearray(sec.data); b[off:off + 4] = bytes.fromhex(new); sec.data = bytes(b)
            touched.append((dtp, off)); st['words_applied'] += 1
        elif cur == new: st['words_already_new'] += 1
        else: st['words_skipped_other_value'] += 1
    if not touched: return raw
    o2 = D.write('le')
    if raw[:4] == b'CDRM': o2 = DW.cdrm_encode(o2, 'le')
    # verifica: stesse intestazioni di sezione, esattamente le parole applicate cambiate
    D0 = DW.read(raw, 'le'); D2 = DW.read(o2, 'le'); diff = 0
    assert len(D0.sections) == len(D2.sections)
    for a0, a2 in zip(D0.sections, D2.sections):
        assert (a0.type, a0.id, a0.reloc, a0.ver, a0.flags) == (a2.type, a2.id, a2.reloc, a2.ver, a2.flags), rel
        diff += sum(1 for q in range(0, len(a0.data), 4) if a0.data[q:q + 4] != a2.data[q:q + 4])
    assert diff == len(touched), (rel, diff, len(touched))
    return o2


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--src', default=DEF_SRC)
    ap.add_argument('--out', default=DEF_OUT)
    ap.add_argument('--no-words', action='store_true')
    ap.add_argument('--only', help='file relativi separati da virgola (debug)')
    a = ap.parse_args()
    src = os.path.realpath(a.src); out = os.path.realpath(a.out)
    if out == src or out.startswith(src + os.sep) or src.startswith(out + os.sep):
        ap.error('out e src non devono sovrapporsi')
    if out == os.path.realpath(DEF_SRC) or not out.startswith(os.path.realpath(CONV) + os.sep):
        ap.error('out deve stare sotto work/ws/converge/ (mai out_fresh2 ne' ' gli overlay)')
    if os.path.lexists(out): shutil.rmtree(out)
    shutil.copytree(src, out)
    rows_by = load_words(WORDS_LOG) if not a.no_words else {}
    only = set(a.only.split(',')) if a.only else None
    rep = []; tot = collections.Counter(); changed = []
    files = []
    for dp, dn, fn in os.walk(src):
        for f in fn:
            if f.lower().endswith('.drm'):
                files.append(os.path.relpath(os.path.join(dp, f), src).replace(os.sep, '/'))
    for rel in sorted(files):
        if only and rel not in only: continue
        p_src = os.path.join(src, rel); raw0 = open(p_src, 'rb').read()
        st = collections.Counter()
        r1, n1 = step_streamname(rel, raw0); st['streamname_sections'] = n1
        r2, nf, nm = step_strings(rel, r1); st['r12_fixed'] = nf; st['r12_manual'] = nm
        rows = rows_by.get(rel, [])
        r3 = step_words(rel, r2, rows, st) if rows else r2
        st['words_in_log'] = len(rows)
        tot.update(st)
        if r3 != raw0:
            open(os.path.join(out, rel), 'wb').write(r3); changed.append(rel)
            rep.append((rel, len(raw0), len(r3), dict(st)))
        elif any(st.values()):
            rep.append((rel, len(raw0), len(r3), dict(st)))
    # md5.txt rigenerato per tutti i file della directory di output (escluso md5.txt)
    md = []
    for dp, dn, fn in os.walk(out):
        for f in sorted(fn):
            if f in ('md5.txt',): continue
            q = os.path.join(dp, f); md.append('%s  %s' % (md5(q), os.path.relpath(q, out).replace(os.sep, '/')))
    open(os.path.join(out, 'md5.txt'), 'w').write('\n'.join(sorted(md, key=lambda s: s.split('  ')[1])) + '\n')
    with open(os.path.join(CONV, 'postfix_report.tsv'), 'w') as fh:
        fh.write('file\tbytes_src\tbytes_out\t' + '\t'.join(sorted(tot)) + '\n')
        for rel, b0, b1, st in rep:
            fh.write('%s\t%d\t%d\t%s\n' % (rel, b0, b1, '\t'.join(str(st.get(k, 0)) for k in sorted(tot))))
    print('files drm', len(files), 'changed', len(changed))
    for k in sorted(tot): print('  %-28s %d' % (k, tot[k]))
    print('out', out)


if __name__ == '__main__':
    main()
