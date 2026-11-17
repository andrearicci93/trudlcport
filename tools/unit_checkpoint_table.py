"""List the checkpoints of every PC unit from the game's own unit data and write TruMenu's optional checkpoint table
(read-only, Q11 2026-11-17, ENGINE.md section 6.4 "Player placement 0x5d40c0 (Q11)").

A checkpoint is a placed intro (unit DTP Level+0x74: +0xc count, +0x10 records of 0x90 B; +0x10 position, +0x50 object
id, +0x58 unique id) whose object is "checkpoint" or "invis_checkpoint" - the two names the player placement 0x5d40c0
looks up for its fallback. The fallback (record id 0) is the checkpoint intro at the intro index the unit's
environment block names (Level+0x70 -> +0x2b4 -> u16 +8); the tool reads it through the section relocations when it
can, else prints '?'. A unit without a player intro (object "player" or a Lara costume) would end a placement in the
fatal box "Couldn't find a player object.." - the table marks such units.

One line per checkpoint:
  <unit> <checkpoint intro id> # intro <index> <object> at x y z (unit data, before FinishLoad); default; player intro
TruMenu (spec Q11, "Kapitel ab Checkpoint") may read the file as TruMenu.checkpoints.txt next to tru.exe; it is game
data (unit names and intro ids): next to the game or in a local folder, never in the repository.

Usage (from the repository root):
  ../bin/pyt -t 1800 tools/unit_checkpoint_table.py [--out FILE] [--units U1,U2,...] [--log DIR] [--verbose]
        [--debug] [--trace]
  --out    the table file (default ../local_results/q11/TruMenu.checkpoints.txt, outside the repository)
  --units  only these units (default: every base unit of pc_unitlist.txt)
  --log    run log folder (default ../local_results/q11/logs)
Exit code: 0 = at least one checkpoint found, 1 = none, 2 = usage error.
"""
import sys, os, time, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import puzzle_switch_scan as PS
import drm_reloc as R

LOG = {'level': 0, 'fh': None}
CP_NAMES = ('checkpoint', 'invis_checkpoint')
PLAYER_NAMES = ('player',)


def log(msg, lvl=0):
    """lvl 0 = always, 1 = verbose, 2 = debug, 3 = trace; the log file gets everything up to debug (trace with --trace)"""
    if lvl <= LOG['level']:
        print(msg, flush=True)
    if LOG['fh'] and (lvl <= 2 or LOG['level'] >= 3):
        LOG['fh'].write(msg + '\n')


def default_index(secs, e):
    """u16 [[Level+0x70]+0x2b4]+8 through the relocations of section 0 (Level) and the section the pointers lead to;
    None when a pointer is not resolvable"""
    E = '>' if e == 'be' else '<'
    try:
        def target(si, off):
            rl = R.parse(bytes(secs[si]['reloc']), e)
            it = dict(rl.internal)
            if off in it:
                return si, it[off]
            for tsi, so, do in rl.external:
                if so == off:
                    return tsi, do
            return None
        t = target(0, 0x70)
        if not t:
            return None
        t2 = target(t[0], t[1] + 0x2b4)
        if not t2:
            return None
        d = bytes(secs[t2[0]]['data'])
        return struct.unpack_from(E + 'H', d, t2[1] + 8)[0]
    except Exception as ex:                   # unexpected layout: report, do not guess
        log('  default index not readable: %r' % ex, 2)
        return None


def main(argv):
    a = list(argv)
    for flag, lvl in (('--trace', 3), ('--debug', 2), ('--verbose', 1)):
        if flag in a:
            LOG['level'] = max(LOG['level'], lvl)
            a.remove(flag)
    base = os.path.join(HERE, '..', '..', 'local_results', 'q11')
    out_path = os.path.join(base, 'TruMenu.checkpoints.txt')
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
    LOG['fh'] = open(os.path.join(logdir, 'unit_checkpoint_table_%s.log' % time.strftime('%Y%m%d_%H%M%S')), 'w',
                     encoding='utf-8')
    log('# unit_checkpoint_table args: %s' % ' '.join(argv), 2)
    S = PS.Source('pc', None)
    units = only if only else [u for u, g in S.units if not g.startswith('dlc')]
    log('%d unit(s) to read' % len(units))
    lines, ncp, noplayer, t0 = [], 0, [], time.time()
    for u in units:
        secs = S.drm(u)
        if not secs:
            log('%s: not found' % u, 1)
            continue
        intros = PS.intros_of(secs, S.e, S.names) or []
        dflt = default_index(secs, S.e)
        player = [q for q in intros if q['name'].lower() in PLAYER_NAMES or q['name'].lower().startswith('lara')]
        cps = [q for q in intros if q['name'].lower() in CP_NAMES]
        if not player:
            noplayer.append(u)
        log('%s: %d intros, %d checkpoint(s), default index %s, player intro %s' % (
            u, len(intros), len(cps), dflt, ' '.join('%d:%s' % (q['uid'], q['name']) for q in player) or 'none'), 1)
        for q in cps:
            ncp += 1
            lines.append('%s %d # intro %d %s at %.1f %.1f %.1f%s%s' % (
                u, q['uid'], q['idx'], q['name'], q['pos'][0], q['pos'][1], q['pos'][2],
                '; default' if dflt == q['idx'] else '', '' if player else '; NO player intro'))
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, 'w', encoding='ascii', newline='\r\n') as fh:
        fh.write('# TruMenu.checkpoints.txt - checkpoints of the PC base units (tools/unit_checkpoint_table.py, %s)\n'
                 % time.strftime('%Y-%m-%d %H:%M:%S'))
        fh.write('# <unit> <checkpoint intro id> # intro index, object, unit-data position; default = the fallback of '
                 'record id 0 - game data: next to tru.exe, never in the repository\n')
        for ln in lines:
            fh.write(ln + '\n')
    log('%d checkpoint(s) in %d unit(s), %d unit(s) without a player intro%s, %.1f s -> %s' % (
        ncp, len(units), len(noplayer), (' (' + ' '.join(noplayer) + ')') if noplayer else '', time.time() - t0,
        out_path))
    if LOG['fh']:
        LOG['fh'].close()
    return 0 if ncp else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
