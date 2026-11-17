"""Build TruMenu's optional level-start intro table (read-only, Q1b 2026-11-17, TruMenu 0.22.58).

Every PC base unit is searched for scripts that hold the already-played branch ("special fade-in case for cine", the
level-start unit scripts of ENGINE.md section 11 "Level-start unit scripts and their intro objects"); in each such script
the instanceref member read last before a call of prototype vt 57 (3523 f0 PlayCinematic) names the intro it plays.
The unit whose placed intros contain that id is the intro's own unit. One line per intro:

  <intro id> <own unit or -> # script <id>; carried by <unit> <unit> ...

TruMenu 0.22.58 reads the file as TruMenu.unitintros.txt next to tru.exe (like TruMenu.weaponwaves.txt): a keep-state
load into an own unit sets that intro's played mark (sticky int 0:<intro> key 5968) to 0 first; the experimental fresh
unit start keeps the marks of the loaded own units at 1 while the loading screen is up. The file is game data (intro
ids and unit names): it belongs next to the game or in a local folder, never in the repository.

Usage (from the repository root):
  ../bin/pyt -t 1800 tools/unit_intro_table.py [--out FILE] [--units U1,U2,...] [--log DIR] [--verbose] [--debug]
        [--trace]
  --out    the table file (default ../local_results/unit_intros/TruMenu.unitintros.txt, outside the repository)
  --units  only these units (default: every base unit of pc_unitlist.txt)
  --log    run log folder (default ../local_results/unit_intros/logs)
Exit code: 0 = at least one intro found, 1 = none, 2 = usage error.
"""
import sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import puzzle_switch_scan as PS
import intro_script_read as ISR

LOG = {'level': 0, 'fh': None}
NEEDLE = b'special fade-in case for cine'
MEMBER_OPS = (0x0c, 0x0d, 0x0e, 0x0f, 0x10)
CALL_OPS = (0x65, 0x66, 0x67, 0x68, 0x69, 0x6a, 0x6b, 0x6c, 0x6d, 0x6e, 0x6f, 0x70, 0x71)


def log(msg, lvl=0):
    """lvl 0 = always, 1 = verbose, 2 = debug, 3 = trace; the log file gets everything up to debug (trace with --trace)"""
    if lvl <= LOG['level']:
        print(msg, flush=True)
    if LOG['fh'] and (lvl <= 2 or LOG['level'] >= 3):
        LOG['fh'].write(msg + '\n')


def played_intros(pool, sid, secs):
    """[(intro id, function k, code offset)] the script sid plays with a vt 57 call: the instanceref member read last
    before the call (own class functions only, as the Q1a reads of 5789 / 9502 / 11733 / 12059 / 13929 / 17775 / 17947 /
    19597)"""
    chain = pool.chain(sid, secs)
    if not chain:
        return []
    refs = {}
    for sc in chain:
        for m in sc.members:
            if m['tid'] is not None and pool.native(m['tid'], secs) == 'instanceref' and m['off'] not in refs:
                refs[m['off']] = sc.value32(m['val'], 0)
    sc = chain[0]
    out = []
    for f in sc.funcs:
        last = None
        cast = None
        for o, op, arg, ex in sc.code(f):
            if op in MEMBER_OPS and arg in refs:
                last = refs[arg]
                log('    script %d f%d +%04x: instanceref m+%d -> intro %s' % (sid, f['k'], o, arg, last), 3)
            if op == 0x7e and ex and ex[0] in sc.ids:
                cast = sc.u32(ex[0])
            if op not in CALL_OPS:
                continue
            for x in ex:
                tch = pool.chain(cast, secs) if op in (0x69, 0x6a, 0x6b, 0x6f, 0x70, 0x71) and cast else chain
                t = ISR.callee_text(pool, sc, x, tch, secs) or ''
                log('    script %d f%d +%04x: op%02x %s' % (sid, f['k'], o, op, t), 3)
                if 'proto' in t and t.split('vt ')[-1].split(' ')[0] == '57' and last is not None:
                    out.append((last, f['k'], o))
                    log('  script %d f%d +%04x: vt 57 after instanceref -> intro %d' % (sid, f['k'], o, last), 2)
    return out


def main(argv):
    a = list(argv)
    for flag, lvl in (('--trace', 3), ('--debug', 2), ('--verbose', 1)):
        if flag in a:
            LOG['level'] = max(LOG['level'], lvl)
            a.remove(flag)
    base = os.path.join(HERE, '..', '..', 'local_results', 'unit_intros')
    out_path = os.path.join(base, 'TruMenu.unitintros.txt')
    logdir = os.path.join(base, 'logs')
    only = None
    try:
        if '--out' in a:
            i = a.index('--out'); out_path = a[i + 1]; del a[i:i + 2]
        if '--log' in a:
            i = a.index('--log'); logdir = a[i + 1]; del a[i:i + 2]
        if '--units' in a:
            i = a.index('--units'); only = [u.strip().lower() for u in a[i + 1].split(',') if u.strip()]; del a[i:i + 2]
    except IndexError:
        print(__doc__)
        return 2
    if a:
        print(__doc__)
        return 2
    os.makedirs(logdir, exist_ok=True)
    LOG['fh'] = open(os.path.join(logdir, 'unit_intro_table_%s.log' % time.strftime('%Y%m%d_%H%M%S')), 'w',
                     encoding='utf-8')
    log('# unit_intro_table args: %s' % ' '.join(argv), 2)
    S = PS.Source('pc', None)
    units = only if only else [u for u, g in S.units if not g.startswith('dlc')]
    log('%d unit(s) to read' % len(units))
    pool = PS.Pool(S)
    own = {}                                  # intro -> its own unit
    carriers = {}                             # intro -> {unit}
    script_of = {}                            # intro -> {script}
    t0 = time.time()
    for u in units:
        secs = S.drm(u)
        if not secs:
            log('%s: not found' % u, 1)
            continue
        pool.add_drm(secs)
        placed = set(q['uid'] for q in (PS.intros_of(secs, S.e, S.names) or []))
        scr = [s for s in secs if s['type'] == 8 and s['data'] and NEEDLE in bytes(s['data'])]
        log('%s: %d placed intros, %d script(s) with the already-played branch%s' % (
            u, len(placed), len(scr), (': ' + ' '.join(str(s['id']) for s in scr)) if scr else ''), 1)
        for s in scr:
            hits = played_intros(pool, s['id'], secs)
            if not hits:
                log('%s: script %d holds the branch but no vt 57 call after an instanceref was found' % (u, s['id']))
            for intro, k, o in hits:
                carriers.setdefault(intro, set()).add(u)
                script_of.setdefault(intro, set()).add(s['id'])
                if intro in placed:
                    if intro in own and own[intro] != u:
                        log('intro %d placed in %s and %s - the first is kept' % (intro, own[intro], u))
                    else:
                        own[intro] = u
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, 'w', encoding='ascii', newline='\r\n') as fh:
        fh.write('# TruMenu.unitintros.txt - level-start intros of the PC base units (tools/unit_intro_table.py, %s)\n'
                 % time.strftime('%Y-%m-%d %H:%M:%S'))
        fh.write('# <intro id> <own unit> # script; carried by ... - game data: next to tru.exe, never in the repository\n')
        for intro in sorted(carriers):
            fh.write('%d %s # script %s; carried by %s\n' % (intro, own.get(intro, '-'),
                                                           ' '.join(str(x) for x in sorted(script_of[intro])),
                                                           ' '.join(sorted(carriers[intro]))))
    for intro in sorted(carriers):
        log('intro %d own %s scripts %s carriers %d' % (intro, own.get(intro, '-'), sorted(script_of[intro]),
                                                       len(carriers[intro])))
    log('%d intro(s), %d with an own unit, %d unit(s) read in %.1f s -> %s' % (
        len(carriers), len(own), len(units), time.time() - t0, out_path))
    if LOG['fh']:
        LOG['fh'].close()
    return 0 if carriers else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
