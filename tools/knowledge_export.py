"""Knowledge package export (plan Spielerweg P2, 2026-11-17, workspace docs Plan-Spielerweg-ohne-Xbox-Spiel-1011.md 5.1).

The number tables the developer path learns from the Xbox <-> PC base pairs (ids, learned word classes, rules, render
tables) are copied into one versioned package folder, each with md5 / size / producer / content kind, so that a player
does not need Cache / Ids / Learn / Tables / Prep (pairs.pkl 1.45 GB, mask_table.pkl 0.78 GB, ~3 h). The learned mask
table (word class per structure key, 778 MB pickle of Counters) is replaced by its slim form: per key only the class
Table.best() returns (generic_learn.Table), as sorted 64-bit key hashes + class codes (numpy) and a JSON vocabulary -
the converter only ever calls best() on it (generic_learn.lookup), so the slim table is a drop-in when best() agrees on
every key (gate below). No source the player-path guard refuses (docs/data/playerpath_guard.json: Xbox base game and
the developer data made from it) is ever copied; this tool opens none of them except mask_table.pkl (learned classes,
no bytes) for the slim step.

Usage (from the repository root):
  ../bin/pyt -t 7200 tools/knowledge_export.py slim-mask PKG [--table work/generic/mask_table.pkl] [--report JSON]
        PKG/learn/mask_best.npz (h = sorted uint64 blake2b-8 of repr(key), c = class code) + mask_best_vocab.json;
        then the gate: for EVERY key of the full table the slim lookup = Table.best(key), no two kept keys share a
        hash; exit 1 on any difference (the files are then removed). One process, a lot of memory (the full table)
  ../bin/pyt -t 900 tools/knowledge_export.py export PKG [--version K20261117-1] [--manifest JSON]
        copies the tables of TABLES (below) into PKG/<group>/, refuses a source the guard classifies as xbox_base /
        xbox_derived / kit, writes PKG/manifest.json (and --manifest, e.g. docs/data/knowledge_manifest.json: the same
        rows, names / sizes / md5 only). PKG/learn/mask_best.* must exist (slim-mask first)
  ../bin/pyt -t 900 tools/knowledge_export.py check PKG [--manifest JSON]
        re-hashes every package file against PKG/manifest.json (and --manifest); exit 1 on a difference / missing file
  ../bin/pyt -t 900 tools/knowledge_export.py same PKG
        for every row: is the work\\ file the package was made from still byte-equal (md5)? exit 1 if not (stale)
  ../bin/pyt -t 900 tools/knowledge_export.py place PKG [--dry-run] [--force]
        player side (instead of Cache / Ids / Learn / Tables / Prep): check, then every table to the work path the
        tools read; an existing file with other content is refused unless --force (exit 1); the mask table stays in
        the package (TRUDLC_MASK_TABLE=PKG/learn/mask_best.npz)
Converter side: dlc_generic.table() loads PKG/learn/mask_best.npz when TRUDLC_MASK_TABLE names it (G3 gate run:
dlc_convert_all --out DIR with the variable set, outputs md5-equal to the full-table run). Prints counts, names and
md5 values only, never game bytes.
"""
import sys, os, json, hashlib, shutil, time, pickle

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.realpath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
SCHEMA = 1
VERSION = 'K20261117-1'
MASK_SRC = os.path.join('work', 'generic', 'mask_table.pkl')

# (group, package name, source relative to the repository, producer "step: tool", kind)
# kind: ids = id / offset maps, classes = learned word classes per key, rules = learned rules / tables, render =
# render id maps / rules / hash tables. Notes on PC bytes: type0 / type7 vocabularies hold 172 constant classes
# 'K:<PC word>' (688 bytes, plan section 6).
TABLES = [
    ('ids', 'idmap.json', 'work/generic/idmap.json', 'Ids / Tables: generic_ids, script_name_match, tex_idmap', 'ids'),
    ('ids', 'dlc_idmap.json', 'work/generic/dlc_idmap.json', 'Tables / Costumes: dlc_generic, verify_ids extend', 'ids'),
    ('ids', 'unit_idmaps.json', 'work/generic/unit_idmaps.json', 'Learn: unit_ids', 'ids'),
    ('ids', 'object_id_remap_xbox_to_pc.json', 'work/generic/merged/object_id_remap_xbox_to_pc.json', 'Ids: objlist_merge', 'ids'),
    ('ids', 'locmap_xbox_to_pc.json', 'work/rebuild/stage1/locmap_xbox_to_pc.json', 'Media: locals build', 'ids'),
    ('ids', 'sym_base_evidence.json', 'work/rebuild/sym_base_evidence.json', 'outside the pipeline (symbol evidence)', 'ids'),
    ('learn', 'type0_table_slim.npz', 'work/generic/type0_table_slim.npz', 'Tables / Prep: generic_type0 save07', 'classes'),
    ('learn', 'type0_table_slim_vocab.json', 'work/generic/type0_table_slim_vocab.json', 'Tables / Prep: generic_type0 save07', 'classes'),
    ('learn', 'type7_table_slim.npz', 'work/generic/type7_table_slim.npz', 'Tables / Prep: generic_type0 save07', 'classes'),
    ('learn', 'type7_table_slim_vocab.json', 'work/generic/type7_table_slim_vocab.json', 'Tables / Prep: generic_type0 save07', 'classes'),
    ('learn', 'script_table.pkl', 'work/script/script_table.pkl', 'Tables: script_learn save', 'classes'),
    ('learn', 'script_detail.pkl', 'work/script/detail.pkl', 'Tables: script_learn save', 'classes'),
    ('learn', 'pc_vers.json', 'work/generic/pc_vers.json', 'Prep: pc_vers_build', 'rules'),
    ('learn', 'pc_vers_content.json', 'work/generic/pc_vers_content.json', 'Prep: pc_vers_build', 'rules'),
    ('learn', 'dtpid_evidence.pkl', 'work/generic/dtpid_evidence.pkl', 'Prep: dtpid_evidence', 'rules'),
    ('learn', 'model_point_rules.pkl', 'work/chain_aim/model_point_rules.pkl', 'Prep: model_point_fix learn', 'rules'),
    ('learn', 'aidata_table.pkl', 'work/generic/aidata_table.pkl', 'Prep: aidata_fix learn', 'rules'),
    ('learn', 'sf_rules.pkl', 'work/generic/sf_rules.pkl', 'outside the pipeline: soundplex_fields learn', 'rules'),
    ('learn', 'dtp_audit_rules.pkl', 'work/generic/dtp_audit_rules.pkl', 'outside the pipeline: dtp_audit learn', 'rules'),
    ('learn', 'objdata_rec_rules.pkl', 'work/generic/objdata_rec_rules.pkl', 'outside the pipeline', 'rules'),
    ('learn', 'soundplex_nodes_rules.pkl', 'work/generic/soundplex_nodes_rules.pkl', 'outside the pipeline: soundplex_nodes', 'rules'),
    ('render', 'pairnames.json', 'work/render/pairnames.json', 'Assemble: render_tables_build build', 'render'),
    ('render', 'material_x2p.pkl', 'work/render/material_x2p.pkl', 'Assemble: render_tables_build build', 'render'),
    ('render', 'shader_x2p.pkl', 'work/render/shader_x2p.pkl', 'Assemble: render_tables_build build', 'render'),
    ('render', 'param_rules.pkl', 'work/render/param_rules.pkl', 'Assemble: material_rules', 'render'),
    ('render', 'dec3n_lut.pkl', 'work/render/dec3n_lut.pkl', 'Assemble: mesh_tables_build', 'render'),
    ('render', 'terrain_yhash.pkl', 'work/render/terrain_yhash.pkl', 'Assemble: terrain_validate', 'render'),
    ('render', 'pc_vdecl_hash.pkl', 'work/render/pc_vdecl_hash.pkl', 'Assemble: mesh_tables_build', 'render'),
    ('render', 'dlc_shader_map.json', 'work/render/dlc_shader_map.json', 'Assemble: shader_map', 'render'),
    ('render', 'dlc_material_shaders.json', 'work/render/dlc_material_shaders.json', 'Assemble: shader_map', 'render'),
]
MASK_FILES = [('learn', 'mask_best.npz', 'slim-mask from ' + MASK_SRC.replace('\\', '/'), 'Learn: generic_learn save -> knowledge_export slim-mask', 'classes'),
              ('learn', 'mask_best_vocab.json', 'slim-mask from ' + MASK_SRC.replace('\\', '/'), 'Learn: generic_learn save -> knowledge_export slim-mask', 'classes')]


def md5_file(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def khash(k):
    """the key hash of tools/slim2np.py and dlc_generic._SlimTable (blake2b-8 of repr(key), little endian)"""
    return int.from_bytes(hashlib.blake2b(repr(k).encode(), digest_size=8).digest(), 'little')


def opt(argv, k, d=None):
    return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d


def write_json(p, d):
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f: json.dump(d, f, indent=1, sort_keys=False)
    os.replace(tmp, p)


class SlimMask:
    """the converter-side lookup (same as dlc_generic._SlimTable, vocabulary from JSON)"""
    def __init__(self, npz):
        import numpy as np
        z = np.load(npz, allow_pickle=False)
        self.h, self.c, self.np = z['h'], z['c'], np
        with open(npz[:-4] + '_vocab.json', encoding='utf-8') as f: self.vocab = json.load(f)

    def best(self, key):
        hv = self.np.uint64(khash(key))
        i = int(self.np.searchsorted(self.h, hv))
        if i < len(self.h) and self.h[i] == hv: return self.vocab[int(self.c[i])]
        return None


def cmd_slim_mask(argv):
    import numpy as np
    import generic_learn as G
    pkg = argv[0]; src = opt(argv, '--table', MASK_SRC); rep = opt(argv, '--report')
    out = os.path.join(pkg, 'learn'); os.makedirs(out, exist_ok=True)
    npz, voc = os.path.join(out, 'mask_best.npz'), os.path.join(out, 'mask_best_vocab.json')
    t0 = time.time()
    src_md5 = md5_file(src)
    print('slim-mask: loading %s (%d bytes, md5 %s)' % (src, os.path.getsize(src), src_md5), flush=True)
    with open(src, 'rb') as f: v, n = pickle.load(f)
    del n
    T = G.Table(); T.v.update(v); del v
    print('slim-mask: %d keys loaded in %.0f s' % (len(T.v), time.time() - t0), flush=True)
    keys, cls = [], []
    for k in T.v:
        b = T.best(k)
        if b is not None: keys.append(k); cls.append(b)
    vocab = sorted(set(cls), key=repr)
    bad = [x for x in vocab if not isinstance(x, str)]
    if bad: raise SystemExit('slim-mask: %d vocabulary entries are not strings (JSON vocabulary impossible)' % len(bad))
    code = {x: i for i, x in enumerate(vocab)}
    dt = np.uint8 if len(vocab) <= 256 else np.uint16
    h = np.fromiter((khash(k) for k in keys), dtype=np.uint64, count=len(keys))
    c = np.fromiter((code[x] for x in cls), dtype=dt, count=len(cls))
    o = np.argsort(h, kind='stable'); h = h[o]; c = c[o]
    coll = int((h[1:] == h[:-1]).sum())
    np.savez(npz, h=h, c=c)
    with open(voc, 'w', encoding='utf-8', newline='\n') as f: json.dump(vocab, f)
    print('slim-mask: kept %d of %d keys, vocabulary %d, hash collisions %d, written in %.0f s'
          % (len(keys), len(T.v), len(vocab), coll, time.time() - t0), flush=True)
    del keys, cls, h, c, o
    # gate: the slim lookup must give Table.best() for every key of the full table (also the keys best() drops: None)
    S = SlimMask(npz); diff = 0; checked = 0; none_hit = 0
    for k in T.v:
        a, b = T.best(k), S.best(k); checked += 1
        if a != b:
            diff += 1
            if a is None: none_hit += 1
    ok = diff == 0 and coll == 0
    res = dict(tool='knowledge_export slim-mask', date=time.strftime('%Y-%m-%d %H:%M:%S'), source=src.replace('\\', '/'),
               source_md5=src_md5, keys=len(T.v), kept=len(S.h), vocabulary=len(vocab), code_dtype=str(np.dtype(dt)),
               collisions=coll, checked=checked, differences=diff, absent_key_hits=none_hit, ok=ok,
               npz_md5=md5_file(npz), npz_size=os.path.getsize(npz), vocab_md5=md5_file(voc), seconds=round(time.time() - t0))
    print('slim-mask gate: %d keys checked, %d differences (%d of them keys best() drops), collisions %d -> %s'
          % (checked, diff, none_hit, coll, 'ok' if ok else 'FAIL'), flush=True)
    if rep: write_json(rep, res)
    write_json(os.path.join(out, 'mask_best_gate.json'), res)
    if not ok:
        for p in (npz, voc): os.remove(p)
        print('slim-mask: files removed (gate failed)', flush=True)
        return 1
    return 0


def refused(rules, path):
    r = rules.classify(path)
    if r and r[0] in ('xbox_base', 'xbox_derived', 'kit'): return r
    return None


def cmd_export(argv):
    import player_guard
    pkg = argv[0]; ver = opt(argv, '--version', VERSION); man2 = opt(argv, '--manifest')
    rules = player_guard.Rules()
    gate = os.path.join(pkg, 'learn', 'mask_best_gate.json')
    if not os.path.exists(gate): raise SystemExit('export: %s missing - run slim-mask first' % gate)
    with open(gate, encoding='utf-8') as f: g = json.load(f)
    if not g.get('ok'): raise SystemExit('export: slim-mask gate not ok')
    rows, errs = [], 0
    for grp, name, src, prod, kind in TABLES:
        sp = os.path.join(REPO, src)
        r = refused(rules, sp)
        if r: print('REFUSED %s (%s: %s)' % (src, r[0], r[2])); errs += 1; continue
        if not os.path.exists(sp): print('MISSING %s' % src); errs += 1; continue
        dp = os.path.join(pkg, grp, name); os.makedirs(os.path.dirname(dp), exist_ok=True)
        shutil.copyfile(sp, dp)
        m = md5_file(dp)
        if m != md5_file(sp): print('COPY DIFFERS %s' % src); errs += 1; continue
        rows.append(dict(file='%s/%s' % (grp, name), size=os.path.getsize(dp), md5=m, source=src,
                         source_mtime=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(sp))),
                         producer=prod, kind=kind))
    for grp, name, src, prod, kind in MASK_FILES:
        dp = os.path.join(pkg, grp, name)
        rows.append(dict(file='%s/%s' % (grp, name), size=os.path.getsize(dp), md5=md5_file(dp), source=src,
                         source_md5=g['source_md5'], producer=prod, kind=kind))
    total = sum(r['size'] for r in rows)
    big = [r['file'] for r in rows if r['size'] > 100 * 1024 * 1024]
    man = dict(schema=SCHEMA, version=ver, generated=time.strftime('%Y-%m-%d %H:%M:%S'),
               about='Knowledge package (plan Spielerweg P2): the number tables the developer path learns from the '
                     'Xbox <-> PC base pairs - ids, learned word classes, rules, render tables - by name, size and md5. '
                     'Written by tools/knowledge_export.py export; gate tools/knowledge_export.py check. No game bytes '
                     'except the 172 constant classes K:<PC word> of the type0 / type7 vocabularies (688 bytes, plan 6).',
               mask_gate=dict((k, g[k]) for k in ('source_md5', 'keys', 'kept', 'vocabulary', 'collisions', 'checked',
                                                   'differences', 'ok')),
               files=rows, total_size=total, over_100mb=big,
               open=['pickles (.pkl) should become JSON / npz before a player loads them (pickle runs code)',
                     'type0_table_slim.npz (118 MB) and mask_best.npz exceed the 100 MB GitHub file limit: release '
                     'attachment or keys cut to the ones the DLC inputs use (plan P7)',
                     'store.pkl without xb_store (P3 / P8): Convert still needs the developer store'])
    write_json(os.path.join(pkg, 'manifest.json'), man)
    if man2: write_json(man2, man)
    print('export %s: %d files, %d bytes (%.1f MB), over 100 MB: %s, errors %d'
          % (ver, len(rows), total, total / 1048576.0, ', '.join(big) or '-', errs), flush=True)
    return 1 if errs else 0


def cmd_check(argv):
    pkg = argv[0]; man2 = opt(argv, '--manifest')
    with open(os.path.join(pkg, 'manifest.json'), encoding='utf-8') as f: man = json.load(f)
    bad = 0
    if man2:
        with open(man2, encoding='utf-8') as f: m2 = json.load(f)
        if [(r['file'], r['md5'], r['size']) for r in m2['files']] != [(r['file'], r['md5'], r['size']) for r in man['files']]:
            print('MANIFEST DIFFERS %s' % man2); bad += 1
    for r in man['files']:
        p = os.path.join(pkg, r['file'])
        if not os.path.exists(p): print('MISSING %s' % r['file']); bad += 1; continue
        if os.path.getsize(p) != r['size'] or md5_file(p) != r['md5']: print('DIFFERENT %s' % r['file']); bad += 1
    print('check %s: %d files, %d bad -> %s' % (man['version'], len(man['files']), bad, 'ok' if not bad else 'FAIL'))
    return 1 if bad else 0


def cmd_same(argv):
    pkg = argv[0]
    with open(os.path.join(pkg, 'manifest.json'), encoding='utf-8') as f: man = json.load(f)
    stale = 0
    for r in man['files']:
        src = r['source']
        if src.startswith('slim-mask from '):
            sp = os.path.join(REPO, src[len('slim-mask from '):]); want = r['source_md5']
        else:
            sp = os.path.join(REPO, src); want = r['md5']
        if not os.path.exists(sp): print('SOURCE MISSING %s' % src); stale += 1; continue
        if md5_file(sp) != want: print('STALE %s (source changed since the export)' % r['file']); stale += 1
    print('same %s: %d files, %d stale -> %s' % (man['version'], len(man['files']), stale, 'ok' if not stale else 'FAIL'))
    return 1 if stale else 0


def cmd_place(argv):
    """player side: every package table to the work path the tools read (the mask table stays in the package, the
    converter takes it through TRUDLC_MASK_TABLE). An existing file with other content is not replaced unless --force;
    with --dry-run only the plan is printed"""
    pkg = argv[0]; force = '--force' in argv; dry = '--dry-run' in argv
    if cmd_check([pkg]): raise SystemExit('place: package check failed')
    with open(os.path.join(pkg, 'manifest.json'), encoding='utf-8') as f: man = json.load(f)
    n = {}
    for r in man['files']:
        if r['source'].startswith('slim-mask from '): continue
        sp, dp = os.path.join(pkg, r['file']), os.path.join(REPO, r['source'])
        state = 'missing' if not os.path.exists(dp) else 'same' if md5_file(dp) == r['md5'] else 'DIFFERENT'
        act = 'keep' if state == 'same' else 'write' if state == 'missing' or force else 'REFUSED (other content, --force)'
        n[act] = n.get(act, 0) + 1
        if act != 'keep': print('%-8s %-34s -> %s (%s)' % (act, r['file'], r['source'], state))
        if act == 'write' and not dry:
            os.makedirs(os.path.dirname(dp), exist_ok=True); shutil.copyfile(sp, dp)
    print('place %s%s: %s; mask table: set TRUDLC_MASK_TABLE=%s'
          % (man['version'], ' (dry run)' if dry else '', n, os.path.join(pkg, 'learn', 'mask_best.npz')))
    return 1 if any(k.startswith('REFUSED') for k in n) else 0


def main(argv):
    cmds = {'slim-mask': cmd_slim_mask, 'export': cmd_export, 'check': cmd_check, 'same': cmd_same, 'place': cmd_place}
    if not argv or argv[0] not in cmds or len(argv) < 2:
        print(__doc__); return 2
    return cmds[argv[0]](argv[1:])


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
