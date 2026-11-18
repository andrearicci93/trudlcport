r"""Static scan of holders in every level unit: which pole hole / key hole / socket / pressure plate takes which
carryable object, by object type (the engine's rule) or by a script reference to one placed instance, and what the
holder or its referrers do. Read-only (R4, 2026-11-18; extends tools/puzzle_switch_scan.py, for the TruMenu
"holder rule" R1 (8); rules in ENGINE.md 9 "Holders and carryable objects" and TRU-Knowledge.md section 7).

The RESULT is game data (intro ids, object names, positions) and stays local (default
<workspace>/local_results/r4_holders, outside the repository); only this tool and the rules belong in the repository.

Data used (layouts in ENGINE.md 9):
  * component block of an object = object data DTP +0xc8 (the run-time [inst+0x50]; 0x4d0d50 tests u16 +4 == 0xb00b
    and u16 +2 == class): class 6 = interactive holder, 0x32 = portable (carryable), 0x4f = uber state machine
  * interaction record {+0 id, +4 entries, +8 count}, entries 0x8c B: +0 kind (Lara's check 0x6f3c60: holding a
    portable whose block byte +0x18 != 0 allows kind 5 only, else 3 / 5 / 7), +4 marker id, +0x10 sub kind, +0x6c u16
    object id list, +0x70 count (the entry is offered only while Lara holds an instance of a listed object, 0x6f3bb0;
    with empty hands an inventory / gear item of that object counts). Class 6: block +0x6c record count, block +0x70
    the records inline (12 B each; which one is active when there are several is not decoded). Uber: DESC +0x40
    (default) or the argument of a node action of kind 29 (set while that node runs)
  * pressure plates (multibody with joint + limit members, chapel plate base) take no list: physics presses them
  * script links to one instance: an `instanceref` member of a portable that names the holder (the chapel pole names
    its start hole), a u16 of the portable's intro data (+0x78) equal to the holder's intro id, an `instanceref` of the
    holder to a portable, and other scripts (trigger volumes) that name the portables near a plate
  * effect: the holder's own script commands (puzzle_switch_scan.uses_of) and the placed objects that reference it

Usage (from the repository root):
  ../bin/pyt -t 3600 tools/holder_scan.py [--source pc,dlc,xbox] [--out DIR] [--dlc-dir MODS] [--units a,b]
        [--verbose] [--debug] [--trace]
  --source  pc / dlc / xbox as tools/puzzle_switch_scan.py (dlc reads the installed DLC units from env TRU_GAME_MODS)
  --out     output folder (default env TRUDLC_LOCAL_OUT, else <workspace>/local_results/r4_holders):
            <source>_holders.csv, <source>_<level>.md, summary.md, logs\holder_scan_<time>.log
Exit code: 0 = done, 1 = a source could not be read, 2 = usage error.
"""
import sys, os, csv, time, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drm_reloc as R
import puzzle_switch_scan as S

DEFAULT_OUT = os.environ.get('TRUDLC_LOCAL_OUT') or os.path.join(HERE, '..', '..', 'local_results', 'r4_holders')
GAME_MODS = os.environ.get('TRU_GAME_MODS', '')
CLS_HOLDER, CLS_PORTABLE, CLS_UBER = 6, 0x32, 0x4f
ENTRY = 0x8c
log = S.log
LOG = S.LOG


# ---------------------------------------------------------------- object component block
class Comp:
    """component block of one object: class, portable flag, interaction entries with object lists"""

    def __init__(self, secs, e):
        self.cls = None; self.flag18 = None; self.entries = []; self.dtp = None
        E = '>' if e == 'be' else '<'
        for s in secs or []:
            if s['type'] != 7 or not s['data']: continue
            d = bytes(s['data']); it = dict(R.parse(bytes(s['reloc']), e).internal)
            U = it.get(0xc8)
            if U is None or U + 8 > len(d): continue
            if struct.unpack_from(E + 'H', d, U + 4)[0] != 0xb00b: continue
            self.dtp = s['id']; self.cls = struct.unpack_from(E + 'H', d, U + 2)[0]
            u = lambda o: struct.unpack_from(E + 'I', d, o)[0] if 0 <= o <= len(d) - 4 else None
            if self.cls == CLS_PORTABLE and U + 0x19 <= len(d): self.flag18 = d[U + 0x18]
            if self.cls == CLS_HOLDER:            # block +0x6c record count, +0x70 inline records 12 B {id, entries, n}
                nr = u(U + 0x6c) or 0
                for i in range(min(nr, 16)):
                    self.record(d, it, u, E, U + 0x70 + 12 * i, 'record %d' % i)
            elif self.cls == CLS_UBER:
                nd = u(U + 8) or 0; D0 = it.get(U + 0xc)
                for m in range(min(nd, 64) if D0 is not None else 0):
                    D = D0 + 0x54 * m
                    self.record(d, it, u, E, D + 0x40, 'link %d default (DESC +0x40)' % m, ptr=True)
                    nb0 = it.get(D + 8)
                    for q in range(min(u(D + 4) or 0, 64) if nb0 is not None else 0):
                        nb = nb0 + 28 * q
                        nm = S.P.cstr(d, it[nb + 8]) if nb + 8 in it else '?'
                        ac = it.get(nb + 0x18)
                        for j in range(min(u(nb + 0x14) or 0, 64) if ac is not None else 0):
                            if u(ac + 0x10 * j) == 29:
                                self.record(d, it, u, E, ac + 0x10 * j + 4, 'link %d node %s (action 29)' % (m, nm), ptr=True)
            break

    def record(self, d, it, u, E, at, where, ptr=False):
        """read the record at `at` (or the record a pointer at `at` names)"""
        rec = it.get(at) if ptr else at
        if rec is None: return
        L = it.get(rec + 4); n = u(rec + 8) or 0
        if L is None or not 0 < n <= 32: return
        for k in range(n):
            a = L + ENTRY * k
            if a + ENTRY > len(d): break
            ids = []
            lp = it.get(a + 0x6c); c = u(a + 0x70) or 0
            if lp is not None and 0 < c <= 32:
                ids = [struct.unpack_from(E + 'H', d, lp + 2 * j)[0] for j in range(c) if lp + 2 * j + 2 <= len(d)]
            self.entries.append(dict(where='%s id %s' % (where, struct.unpack_from(E + 'i', d, rec)[0]), k=k, kind=u(a), marker=struct.unpack_from(E + 'i', d, a + 4)[0],
                                     sub=u(a + 0x10), ids=ids))

    def accepts(self):
        return sorted({i for en in self.entries for i in en['ids']})


# ---------------------------------------------------------------- units
def intro_data(secs, e):
    """{intro index: [u16 halves of the intro data words]} of a unit (intro +0x78 -> data, size = next relocation)"""
    E = '>' if e == 'be' else '<'
    rl = R.parse(bytes(secs[0]['reloc']), e)
    tgt = [si for si, so, do in rl.external if so == 0x74]
    if not tgt: return {}
    u = secs[tgt[0]]; d = bytes(u['data']); it = dict(R.parse(bytes(u['reloc']), e).internal)
    if 0x10 not in it: return {}
    n = struct.unpack_from(E + 'I', d, 0xc)[0]; a = it[0x10]
    targets = sorted(set(it.values()))
    out = {}
    for k in range(min(n, 8192)):
        o = a + 0x90 * k
        if o + 0x90 > len(d): break
        dp = it.get(o + 0x78)
        if dp is None: continue
        nxt = next((t for t in targets if t > dp), len(d))
        halves = []
        for q in range(min((nxt - dp) // 4, 16)):
            w = dp + 4 * q
            if w in it: continue
            halves += list(struct.unpack_from(E + 'HH', d, w))
        out[k] = halves
    return out


def holder_kind(accepted_names):
    """kind by the accepted objects' names (g_* = Thor's gear in the inventory, not a placed carryable)"""
    low = ' '.join(accepted_names).lower()
    if any(n.startswith('g_') for n in accepted_names): return 'gear socket (inventory)'
    for word, kind in (('pole', 'pole hole'), ('key', 'key socket'), ('gem', 'gem socket'), ('weight', 'weight socket')):
        if word in low: return kind
    return 'part socket'


def plate_like(pool, unit, q):
    """a pressure plate: 'plate' in the object name (not an fx_ object) and a class of the chain with multibody,
    joint and limit members (the chapel plate base: a joint range = pressed / released)"""
    low = q['name'].lower()
    if 'plate' not in low or low.startswith('fx_'): return False
    for sc in pool.chain(q['script'], unit.secs) if q['script'] else []:
        nat = {pool.native(m['tid'], unit.secs) for m in sc.members if m['tid'] is not None}
        if {'multibody', 'joint', 'limit'} <= nat: return True
    return 'press' in low                  # a named press plate without that script shape (physics or animation only)


# ---------------------------------------------------------------- scan
def scan(src, only_units):
    pool = S.Pool(src)
    units = []
    log('[%s] reading %d units' % (src.key, len(src.units)))
    for name, grp in src.units:
        if only_units and name not in only_units: continue
        secs = src.drm(name)
        its = S.intros_of(secs, src.e, src.names) if secs else None
        if its is None:
            log('  %s: no unit DRM / no intro list' % name, 1); continue
        U = S.Unit(name, grp, secs, its); U.data = intro_data(secs, src.e)
        units.append(U); pool.add_drm(secs)
        log('  %s (%s): %d intros' % (name, grp, len(its)), 1)
    index = {}
    for U in units:
        for q in U.intros:
            x = dict(q); x['unit'] = U
            index.setdefault(q['uid'], x)
    comps = {}

    def comp(nm):
        if nm not in comps:
            secs = src.drm(nm)
            pool.add_drm(secs)
            comps[nm] = Comp(secs, src.e) if secs else None
        return comps[nm]
    refs = {}; back = collections.defaultdict(list)
    for U in units:
        for q in U.intros:
            r = S.refs_of(pool, U, q) if q['script'] else {}
            refs[(U.name, q['idx'])] = r
            for off, (t, _) in r.items(): back[t].append(q['uid'])
    # portables per level group / unit
    port_by_obj = collections.defaultdict(list)
    for U in units:
        for q in U.intros:
            c = comp(q['name'])
            if c is not None and c.cls == CLS_PORTABLE:
                port_by_obj[(U.grp, q['obj'])].append((U.name, q['uid']))
    rows = []; entry_kinds = collections.Counter(); portable_flags = collections.Counter()
    for (g, o), lst in port_by_obj.items():
        c = comp(src.names.get(o, ''))
        portable_flags[(c.flag18 if c else None)] += len(lst)
    for U in units:
        for q in U.intros:
            c = comp(q['name'])
            is_holder = c is not None and any(en['ids'] for en in c.entries)
            is_plate = not is_holder and plate_like(pool, U, q)
            if not is_holder and not is_plate: continue
            uid = q['uid']
            accepted = c.accepts() if is_holder else []
            kind = holder_kind([src.names.get(o, '?') for o in accepted]) if is_holder else 'pressure plate'
            if is_holder: kind += ' (class %d)' % c.cls
            if is_holder:
                for en in c.entries: entry_kinds[(c.cls, en['kind'])] += 1
            # instances of the accepted objects: same unit / same level
            same_unit, same_level = [], []
            for o in accepted:
                for un, pu in port_by_obj.get((U.grp, o), []):
                    (same_unit if un == U.name else same_level).append(pu)
            # script links to single instances
            specific = []
            for r in sorted(set(back.get(uid, []))):
                x = index.get(r)
                if x is None: continue
                xc = comp(x['name'])
                if xc is not None and xc.cls == CLS_PORTABLE:
                    specific.append('%d %s instanceref -> this holder' % (r, x['name']))
            for x in U.intros:
                xc = comp(x['name'])
                if xc is None or xc.cls != CLS_PORTABLE: continue
                if uid in U.data.get(x['idx'], []):
                    specific.append('%d %s intro data names this holder (start in it)' % (x['uid'], x['name']))
            for off, (t, _) in sorted(refs.get((U.name, q['idx']), {}).items()):
                x = index.get(t)
                if x is not None and comp(x['name']) is not None and comp(x['name']).cls == CLS_PORTABLE:
                    specific.append('holder script +%d instanceref -> %d %s' % (off, t, x['name']))
            counters = []
            if is_plate:                   # scripts of the unit that name portables (weight counters, objectives)
                for x in U.intros:
                    xc = comp(x['name'])
                    if xc is None or xc.cls != CLS_PORTABLE: continue
                    for r in sorted(set(back.get(x['uid'], []))):
                        y = index.get(r)
                        if y is None or (comp(y['name']) is not None and comp(y['name']).cls == CLS_PORTABLE): continue
                        counters.append('%d %s -> %d %s' % (r, y['name'], x['uid'], x['name']))
                counters = sorted(set(counters))
            # effect: own commands, referrers
            uses = S.uses_of(pool, U, q, refs.get((U.name, q['idx']), {}), index) if q['script'] else {}
            eff = []
            for t, us in sorted(uses.items()):
                x = index.get(t)
                for rel, det, n in us:
                    if rel in ('command', 'call', 'uber call'):
                        eff.append('%s %d %s: %s%s' % (rel, t, x['name'] if x else '?', det,
                                                       (' = entry %s' % n) if n is not None else ''))
            eff = sorted(set(eff))
            referrers = []
            for r in sorted(set(back.get(uid, []))):
                x = index.get(r)
                if x is None: continue
                xc = comp(x['name'])
                if xc is not None and xc.cls == CLS_PORTABLE: continue
                referrers.append('%d %s' % (r, x['name']))
            rule = ('type: object list %s' % ', '.join('%d %s' % (o, src.names.get(o, '?')) for o in accepted)) if is_holder \
                else 'physics: any body heavy enough (no list)'
            entries = '; '.join('%s e%d kind %s marker %s sub %s ids %s' % (en['where'], en['k'], en['kind'], en['marker'],
                                                                          en['sub'], en['ids']) for en in (c.entries if c else []))
            rows.append(dict(source=src.key, level=U.grp, unit=U.name, intro=uid, object=q['name'], kind=kind,
                             pos='%.1f %.1f %.1f' % q['pos'], component=('class %d' % c.cls) if c and c.cls is not None else 'none',
                             rule=rule, entries=entries, accepted_in_unit=len(same_unit), accepted_in_level=len(same_level),
                             accepted_instances=' '.join(str(v) for v in sorted(same_unit + same_level)),
                             specific=' | '.join(specific), counters=' | '.join(counters),
                             effect=' | '.join(eff), referrers=' | '.join(referrers),
                             binding='specific (script)' if specific or counters else 'type only'))
    log('[%s] %d units, %d holder rows; entry kinds (class, kind) %s; portable flag +0x18 %s' % (
        src.key, len(units), len(rows), dict(entry_kinds), dict(portable_flags)))
    return rows, entry_kinds, portable_flags


COLS = ['source', 'level', 'unit', 'intro', 'object', 'kind', 'pos', 'component', 'rule', 'entries', 'accepted_in_unit',
        'accepted_in_level', 'accepted_instances', 'specific', 'counters', 'binding', 'effect', 'referrers']


def write_md(path, title, rows):
    with open(path, 'w', encoding='utf-8-sig', newline='\r\n') as fh:
        fh.write('# %s\n\nLocal result of tools/holder_scan.py (game data - not for the repository).\n\n' % title)
        by_unit = collections.defaultdict(list)
        for r in rows: by_unit[r['unit']].append(r)
        for u in sorted(by_unit):
            fh.write('## %s\n\n| intro | object | kind | rule | in unit / level | specific links | counters | effect | '
                     'referrers |\n|---|---|---|---|---|---|---|---|---|\n' % u)
            for r in sorted(by_unit[u], key=lambda r: r['intro']):
                fh.write('| %s | %s | %s | %s | %s / %s (%s) | %s | %s | %s | %s |\n' % (
                    r['intro'], r['object'], r['kind'], r['rule'], r['accepted_in_unit'], r['accepted_in_level'],
                    r['accepted_instances'], r['specific'].replace(' | ', '; '), r['counters'].replace(' | ', '; '),
                    r['effect'].replace('|', '/'), r['referrers'].replace(' | ', ', ')))
            fh.write('\n')


def main(argv):
    a = list(argv)

    def opt(k, dflt=None):
        if k in a:
            i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return v
        return dflt
    if '-h' in a or '--help' in a: print(__doc__); return 0
    LOG['level'] = 3 if '--trace' in a else 2 if '--debug' in a else 1 if '--verbose' in a else 0
    a = [x for x in a if x not in ('--trace', '--debug', '--verbose')]
    sources = opt('--source', 'pc,dlc,xbox').split(',')
    out = opt('--out', DEFAULT_OUT); dlc_dir = opt('--dlc-dir', GAME_MODS)
    only = set(opt('--units', '').split(',')) - {''}
    if a or any(s not in ('pc', 'dlc', 'xbox') for s in sources): print(__doc__); return 2
    if 'dlc' in sources and not dlc_dir:
        print('usage: source dlc needs --dlc-dir <game mods folder> or env TRU_GAME_MODS'); return 2
    os.makedirs(os.path.join(out, 'logs'), exist_ok=True)
    LOG['fh'] = open(os.path.join(out, 'logs', 'holder_scan_%s.log' % time.strftime('%Y%m%d_%H%M%S')), 'w', encoding='utf-8')
    log('holder_scan %s sources %s out %s units %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), sources, out, sorted(only) or 'all'))
    t0 = time.time(); allrows = {}; rc = 0
    for s in sources:
        try:
            src = S.Source(s, dlc_dir)
        except Exception as ex:
            log('[%s] cannot open the source: %s' % (s, ex)); rc = 1; continue
        rows, ek, pf = scan(src, only)
        allrows[s] = (rows, ek, pf)
        with open(os.path.join(out, '%s_holders.csv' % s), 'w', encoding='utf-8-sig', newline='') as fh:
            w = csv.DictWriter(fh, COLS); w.writeheader(); w.writerows(rows)
        for g in sorted({r['level'] for r in rows}):
            write_md(os.path.join(out, '%s_%s.md' % (s, g)), '%s %s holders' % (s, g), [r for r in rows if r['level'] == g])
    with open(os.path.join(out, 'summary.md'), 'w', encoding='utf-8-sig', newline='\r\n') as fh:
        fh.write('# Holder scan summary (%s)\n\nLocal result of tools/holder_scan.py.\n\n' % time.strftime('%Y-%m-%d %H:%M'))
        fh.write('| source | level | kind | holders | type only | specific (script) | no accepted instance in the level |\n'
                 '|---|---|---|---|---|---|---|\n')
        for s, (rows, ek, pf) in allrows.items():
            for key in sorted({(r['level'], r['kind']) for r in rows}):
                rs = [r for r in rows if (r['level'], r['kind']) == key]
                fh.write('| %s | %s | %s | %d | %d | %d | %d |\n' % (
                    s, key[0], key[1], len(rs), sum(r['binding'] == 'type only' for r in rs),
                    sum(r['binding'] != 'type only' for r in rs),
                    sum(r['kind'] != 'pressure plate' and r['accepted_in_unit'] + r['accepted_in_level'] == 0 for r in rs)))
        for s, (rows, ek, pf) in allrows.items():
            fh.write('\n%s: interaction entries (class, kind) %s; portables by block byte +0x18 %s\n' % (s, dict(ek), dict(pf)))
    log('done in %.0f s' % (time.time() - t0))
    LOG['fh'].close()
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
