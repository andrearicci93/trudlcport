"""Read-only gate: structural COUNT words of ported scripts against the Xbox original (T1, 2026-11-19).

Why: a script port keeps the Xbox layout, so every array of the Xbox script (members, sfi start list, prototypes,
functions, code, args, locals, ...) sits at the same offset in our PC script and its count word (the word before the
array start) must carry the Xbox count. tools/script_init_from_pc.py breaks that rule: script_conv.Walk labels the
members' init blocks BEFORE the later arrays (root order 0x2c members, then 0x30 sfi, 0x34 protos, 0x38 funcs), an
init block that ends right before an array runs into its count word (the count is not a pointer target, only the array
start is), and copy_tree copies the PC script's word there. Cases: generalbank 8:6 sfi count 193 -> 182 (Q7, black
loading backgrounds) and three code counts of 8:6, 8:9 sfi count 8 -> 3 (hand-fixed by the kit chain's step 18),
HUD script 37 five code counts + one sfi count (tools/script_init_guard.py). docs/Befund-T1-1911.md (workspace).

A script is compared when its twin in REF (same id, or --map XBOX=PC) keeps the layout: the PC data is at least as
long and the root array pointers (+0x20 .. +0x38, +0x48) target the same offsets. Then every array of the REF walk
(not the vtable, which has no count word) is compared at the same offset. Scripts of another layout are counted and
skipped. Exit 1 on a differing count word that is not listed with --allow.

Usage (repo root):
  ../bin/pyt -t 900 tools/script_count_gate.py DRM REF [--map 10=9,38=37] [--ids 6,9] [--allow 6:7920,6:8550]
                                               [--report JSON]
    REF    tu:PATH = the Xbox generalbank inside that TitleUpdate.000 (tu: alone = the workspace copy
           ../data/TombRaiderUnderworld_Patched/TitleUpdate.000), or a DRM (another PC file)
    --allow SID:HEXOFF  known differences that do not fail the gate (still printed, marked 'allowed')
"""
import sys, os, struct, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R, script_conv as SC

ROOT_PTRS = (0x20, 0x24, 0x28, 0x2c, 0x30, 0x34, 0x38, 0x48)
TU_ARCH = '../data/TombRaiderUnderworld_Patched/TitleUpdate.000'


def load(src):
    """[(type, id, data, reloc)], endian"""
    if src.startswith('tu:'):
        import dlc_screen_panel as DSP
        return DSP.read_tu(src[3:] or TU_ARCH), 'be'
    import script_func_list as FL
    return FL.sections(src)


def walk(d, rl, e):
    return SC.Walk(d, R.parse(rl, e), e).run()


def compare(pd, prl, xd, xrl, xe):
    """None when the layout is not kept, else [(offset, array, ref count, our word)] of the differing count words"""
    if len(pd) < len(xd): return None
    wp, wx = walk(pd, prl, 'le'), walk(xd, xrl, xe)
    if any(wp.it.get(o) != wx.it.get(o) for o in ROOT_PTRS): return None
    out = []
    for nm, t, n, sz in wx.arrays:
        if nm == 'vtable' or t < 4: continue
        cur = struct.unpack_from('<I', pd, t - 4)[0]
        if cur != n: out.append((t - 4, nm, n, cur))
    return out, sum(1 for nm, t, n, sz in wx.arrays if nm != 'vtable' and t >= 4)


def main(argv):
    def opt(name):
        if name not in argv: return None
        k = argv.index(name); v = argv[k + 1]; del argv[k:k + 2]; return v
    mp = {int(a): int(b) for a, b in (x.split('=') for x in (opt('--map') or '').split(',') if x)}
    ids = {int(x) for x in (opt('--ids') or '').split(',') if x}
    allow = {(int(a), int(b, 16)) for a, b in (x.split(':') for x in (opt('--allow') or '').split(',') if x)}
    report = opt('--report')
    if len(argv) != 2: raise SystemExit(__doc__)
    secs, e = load(argv[0]); rsecs, re_ = load(argv[1])
    if e != 'le': raise SystemExit('DRM must be a PC (little-endian) file')
    ours = {s: (d, rl) for ty, s, d, rl in secs if ty == 8 and d}
    tot = collections.Counter(); rows = []
    for ty, xs, xd, xrl in rsecs:
        if ty != 8 or not xd: continue
        pid = mp.get(xs, xs)
        if (ids and pid not in ids) or pid not in ours: continue
        try: r = compare(ours[pid][0], ours[pid][1], xd, xrl, re_)
        except Exception as x:
            tot['scripts not walked'] += 1; print('  script %d: not walked (%s)' % (pid, x)); continue
        if r is None: tot['scripts of another layout (skipped)'] += 1; continue
        diff, n = r
        tot['scripts compared'] += 1; tot['count words compared'] += n
        for o, nm, rn, cur in diff:
            ok = (pid, o) in allow
            tot['count words allowed' if ok else 'count words DIFFERENT'] += 1
            rows.append(dict(script=pid, ref_script=xs, offset='0x%x' % o, array=nm, ref=rn, ours=cur, allowed=ok))
            print('  script %5d (ref %d) +0x%05x %-7s count: ref %d, ours %d%s' % (pid, xs, o, nm, rn, cur,
                                                                                  '  (allowed)' if ok else ''))
    bad = tot['count words DIFFERENT']
    print('== %s vs %s: %s' % (argv[0], argv[1], dict(tot)))
    print('gate:', 'FAIL' if bad else 'ok')
    if report:
        os.makedirs(os.path.dirname(os.path.abspath(report)), exist_ok=True)
        with open(report, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(dict(drm=argv[0], ref=argv[1], totals=dict(tot), rows=rows, gate='FAIL' if bad else 'ok'), f, indent=1)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
