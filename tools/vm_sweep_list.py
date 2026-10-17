#!/usr/bin/env python3
"""Build the unit / object lists for the in-game F8 sweep (tools/vm_sweep_plan.md).  Pure local, no VM.

  python3 -I tools/vm_sweep_list.py [--mods work/vm_mods_expected] [--out work/sweep]

Inputs (all under work/):
  generic/merged/tr8/pc-w/{unitlist,objectlist}.txt   merged lists installed in the game (PC base + DLC)
  generic/lists/pc_{unitlist,objectlist}.txt          PC BASE lists (what is NOT new)
  vm_mods_expected/                                    the DRM set installed in the VM mods\\ folder

Outputs (work/sweep/):
  units.txt        one bare unit name per line, exactly what is typed in the F8 'Unit' field (basename of the unitlist path;
                   the hook passes it straight to CheckDataFile(<name>) = PC-W\\<name>.drm and GAMELOOP_RequestLevelChangeByName)
  objects.txt      one object name per line, exactly what is typed in the F8 'Object' field (<= 63 chars, ImGui buffer is 64)
  units.tsv / objects.tsv   sidecars: name, id/path, drm size, extra columns (ctx, accept-alt for units)
  excluded.txt     everything left out with the reason

Selection rules
  units  : in merged unitlist, NOT in PC base unitlist, path under 'dlc\\dlc_level*\\' (real levels), and <name>.drm is installed
           in mods (top level).  Containers (dlc\\container*, dlc\\dlc_costume_containers, imf\\*) are not levels -> excluded.
  objects: in merged objectlist, NOT (by name) in PC base objectlist, and <name>.drm installed in mods (top level).  fx_*/co_*/pr_*/wp_*
           are KEPT here.  A listed name without an installed DRM makes the hook log 'Not birthing X, object does not exists'
           (CheckDataFile fails) so it cannot be tested -> excluded.txt.
  Cross-check: new-by-name must equal new-by-id (id > number of PC base objects); mismatch is printed as WARN.
"""
import argparse, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rd(path):
    return open(path, 'rb').read().decode('cp1252').replace('\r\n', '\n').split('\n')


def read_units(path):
    L = [x.strip() for x in rd(path) if x.strip()]
    return L[1:]  # first line = count


def read_objects(path):
    L = [x.strip() for x in rd(path) if x.strip()]
    out = []
    for x in L[1:]:
        i, _, n = x.partition(',')
        out.append((int(i), n))
    return out


def ctx_of(name):
    """Advisory host context: objects whose scripts/DTPs only make sense inside the DLC1 levels."""
    n = name.lower()
    if n.startswith(('dlc1_', 'ma_ani_', 'ma_ei_grapple', 'knight_thrall', 'fx_dlc1', 'fx_ma_', 'fx_waterwheel', 'fx_drips_pillory',
                     'co_dlc_knight', 'co_dlc_eitr', 'cine_dlc1')) or 'dungn' in n or 'pillory' in n:
        return 'dlc1'
    return 'any'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mods', default=os.path.join(ROOT, 'work', 'vm_mods_expected'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'work', 'sweep'))
    a = ap.parse_args()
    W = os.path.join(ROOT, 'work', 'generic')
    mu = read_units(os.path.join(W, 'merged', 'tr8', 'pc-w', 'unitlist.txt'))
    bu = set(x.lower() for x in read_units(os.path.join(W, 'lists', 'pc_unitlist.txt')))
    mo = read_objects(os.path.join(W, 'merged', 'tr8', 'pc-w', 'objectlist.txt'))
    bo = read_objects(os.path.join(W, 'lists', 'pc_objectlist.txt'))
    base_names = set(n.lower() for _, n in bo)
    nbase = max(i for i, _ in bo)
    mods = {f.lower(): os.path.getsize(os.path.join(a.mods, f)) for f in os.listdir(a.mods) if os.path.isfile(os.path.join(a.mods, f))}
    os.makedirs(a.out, exist_ok=True)
    excl = []

    # ---- units
    units = []
    for p in mu:
        if p.lower() in bu:
            continue
        name = p.replace('\\', '/').split('/')[-1]
        low = p.lower()
        if not low.startswith('dlc\\dlc_level'):
            excl.append(('unit', name, 'not a level unit (%s)' % p))
            continue
        sz = mods.get(name.lower() + '.drm')
        if sz is None:
            excl.append(('unit', name, 'no %s.drm in mods (not installed / not converted)' % name))
            continue
        units.append((name, p, sz, os.path.exists(os.path.join(a.mods, name + '_map.drm'))))
    # control first: dlc_level1_start is the only unit proven to load (log: CURRENT LEVEL = dlc_caverns after the warp)
    units.sort(key=lambda u: (u[0].lower() != 'dlc_level1_start', u[0].lower()))
    alt = {'dlc_level1_start': 'dlc_caverns'}  # accepted alternative CURRENT LEVEL (script warps)

    # ---- objects
    new_by_name = [(i, n) for i, n in mo if n.lower() not in base_names]
    new_by_id = [(i, n) for i, n in mo if i > nbase]
    if set(new_by_name) != set(new_by_id):
        print('WARN: new-by-name (%d) != new-by-id (%d); using by-name' % (len(new_by_name), len(new_by_id)), file=sys.stderr)
    objs = []
    for i, n in new_by_name:
        if len(n) > 63:
            excl.append(('object', n, 'name > 63 chars (Object buffer is 64)'))
            continue
        sz = mods.get(n.lower() + '.drm')
        if sz is None:
            excl.append(('object', n, 'no %s.drm in mods -> hook would log "Not birthing"' % n))
            continue
        objs.append((n, i, sz, ctx_of(n)))

    def w(fn, lines):
        with open(os.path.join(a.out, fn), 'w', newline='\n') as f:
            f.write('\n'.join(lines) + ('\n' if lines else ''))
    w('units.txt', [u[0] for u in units])
    w('units.tsv', ['\t'.join([u[0], u[1], str(u[2]), 'map' if u[3] else 'NOMAP', alt.get(u[0].lower(), '')]) for u in units])
    w('objects.txt', [o[0] for o in objs])
    w('objects.tsv', ['\t'.join([o[0], str(o[1]), str(o[2]), o[3]]) for o in objs])
    w('excluded.txt', ['%s\t%s\t%s' % e for e in excl])

    print('units  : %d (merged unitlist %d, base %d, dlc-new %d)' % (len(units), len(mu), len(bu), len([p for p in mu if p.lower() not in bu])))
    print('objects: %d (merged %d, PC base %d, new %d, new w/o installed drm %d)' % (
        len(objs), len(mo), nbase, len(new_by_name), len([e for e in excl if e[0] == 'object' and 'no ' in e[2]])))
    print('  ctx dlc1: %d  any: %d' % (sum(o[3] == 'dlc1' for o in objs), sum(o[3] == 'any' for o in objs)))
    print('excluded: %d units, %d objects -> %s' % (sum(e[0] == 'unit' for e in excl), sum(e[0] == 'object' for e in excl),
                                                     os.path.join(a.out, 'excluded.txt')))
    # installed DRMs that are neither unit, nor object, nor _map (info only)
    used = set(u[0].lower() + '.drm' for u in units) | set(o[0].lower() + '.drm' for o in objs)
    rest = sorted(f for f in mods if f.endswith('.drm') and f not in used and not f.endswith('_map.drm'))
    print('installed top-level non-map DRMs not covered (not loadable by name): %d' % len(rest))
    w('uncovered_drms.txt', rest)


if __name__ == '__main__':
    main()
