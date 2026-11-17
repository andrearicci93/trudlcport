"""Intros of PC unit DRMs near a live point (read-only, Q1a 2026-11-17: what lies where the chapter intro put Lara).

live = intro data position (+0x10) - Level+0x80 (ENGINE.md 4.3, the frame of TruMenu / TruFight.log while the unit is
the main unit). --shift X,Y,Z adds a frame offset (a neighbour unit seen from another main unit: + the portal +0x90
difference, tools/unit_frames.py pairs). Object names from work/generic/lists/pc_objectlist.txt. The output holds game
positions and names: local folder only, never the repository.

Usage (from the repository root):
  ../bin/pyt -t 600 tools/unit_intros_near.py UNIT.drm[,UNIT.drm...] X,Y,Z[,R] [--shift DX,DY,DZ] [--log DIR]
        [--verbose] [--debug] [--trace]
  R      radius in live units (default 1500)
  --log  run log folder (default ../local_results/unit_intros_near, outside the repository)
Exit code: 0 = done, 1 = a file not readable, 2 = usage error.
"""
import sys, os, struct, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'work', 'endb270_0811'))
import drm

LOG = {'level': 0, 'fh': None}
NAMES = os.path.join(HERE, '..', 'work', 'generic', 'lists', 'pc_objectlist.txt')


def log(msg, lvl=0):
    if lvl <= LOG['level']:
        print(msg, flush=True)
    if LOG['fh'] and (lvl <= 2 or LOG['level'] >= 3):
        LOG['fh'].write(msg + '\n')


def objnames():
    out = {}
    try:
        for ln in open(NAMES, 'rb').read().decode('latin1').splitlines():
            if ',' in ln:
                i, n = ln.split(',', 1)
                if i.strip().isdigit():
                    out[int(i)] = n.strip()
    except OSError:
        log('object list not found: %s' % NAMES, 1)
    return out


def main(argv):
    a = list(argv)
    for flag, lvl in (('--trace', 3), ('--debug', 2), ('--verbose', 1)):
        if flag in a:
            LOG['level'] = max(LOG['level'], lvl)
            a.remove(flag)

    def opt(name):
        if name in a:
            i = a.index(name); v = a[i + 1]; del a[i:i + 2]; return v
        return None
    shift = opt('--shift')
    logdir = opt('--log') or os.path.join(HERE, '..', '..', 'local_results', 'unit_intros_near')
    if len(a) != 2:
        print(__doc__)
        return 2
    os.makedirs(logdir, exist_ok=True)
    LOG['fh'] = open(os.path.join(logdir, 'unit_intros_near_%s.log' % time.strftime('%Y%m%d_%H%M%S')), 'w',
                     encoding='utf-8')
    log('args: %s' % ' '.join(argv), 2)
    import unit_dtp as UD
    v = [float(t) for t in a[1].split(',')]
    pt, r = tuple(v[:3]), (v[3] if len(v) > 3 else 1500.0)
    sh = tuple(float(t) for t in shift.split(',')) if shift else (0.0, 0.0, 0.0)
    nm = objnames()
    rows = []
    for path in a[0].split(','):
        try:
            raw = open(path, 'rb').read()
            S = drm.sections_with_data(drm.cdrm_decode(raw, 'le'), 'le')[1]
            org = struct.unpack_from('<3f', S[0]['data'], 0x80)
            _, u, ptr = UD.unit(raw, 'le')
            intr = UD.intros(u, ptr, 'le')
        except (OSError, ValueError, IndexError, KeyError) as ex:
            log('%s: cannot read (%s)' % (path, ex))
            return 1
        name = os.path.splitext(os.path.basename(path))[0]
        log('%s: Level+0x80 %.1f / %.1f / %.1f, %d intros, shift %.1f / %.1f / %.1f' % ((name,) + org + (len(intr),) + sh))
        for x in intr:
            pos = struct.unpack_from('<3f', u['data'], x['o'] + 0x10)
            lv = tuple(pos[i] - org[i] + sh[i] for i in range(3))
            d = sum((lv[i] - pt[i]) ** 2 for i in range(3)) ** 0.5
            if d <= r:
                rows.append((d, name, x['uid'], x['obj'], lv))
    rows.sort()
    log('intros within %.0f of %.1f / %.1f / %.1f: %d' % ((r,) + pt + (len(rows),)))
    for d, name, uid, obj, lv in rows:
        log('  %7.1f  %-18s intro %6d obj %5d %-34s live %.1f / %.1f / %.1f' % ((d, name, uid, obj, nm.get(obj, '?')) + lv))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
