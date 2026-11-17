"""Read-only: which members of one script are on its construction list ('sfi', script header +0x30) inside the
count the engine walks. The engine constructs exactly `count` sfi entries when it creates a script instance
(per entry the native member's construct handler; for UI widgets that is init + SetParent to the screen). A member
that has an init block but no sfi entry inside the count is created later by its first native call (lazy handle,
for uirenderimage 0x4b9b10 / 0x4b9560 / ...) - with its init block applied but WITHOUT a parent widget.

Usage (repo root):
  ../bin/pyt -t 300 tools/script_sfi_members.py DRM SCRIPT_ID [--type NATIVE_NAME] [DRM2 ...]
    DRM          a generalbank.drm (or any DRM with type-8 script sections), little- or big-endian;
                 tu:PATH = the Xbox generalbank inside that TitleUpdate.000 (e.g. tu:../data/TombRaiderUnderworld_Patched/TitleUpdate.000)
    SCRIPT_ID    the script section id (e.g. 6 = uiloading in the generalbank)
    --type NAME  only list members whose native type is NAME (e.g. uirenderimage)
Prints per member: index, offset, Symbol, native type, has init, position on the sfi list (or '-'), inside count.
Exit 1 if a native member with an init block of the selected type is not constructed (outside the count or missing).

  ../bin/pyt -t 900 tools/script_sfi_members.py --scan DRM [REF]
    every script of DRM whose sfi count word is below the entries stored after it, or differs from the same script id
    in REF (a DRM or tu:PATH); exit 1 on a finding."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import script_func_list as FL
import dlc_screen_panel as DSP


def check(path, sid, tname):
    if path.startswith('tu:'):                     # the Xbox original generalbank inside a TitleUpdate.000
        secs, e = DSP.read_tu(path[3:]), 'be'
    else:
        secs, e = FL.sections(path)
    nat = DSP.natives(secs, e)
    hit = [(d, rl) for ty, s, d, rl in secs if ty == 8 and s == sid and d]
    if len(hit) != 1:
        print('== %s: %d script sections %d' % (path, len(hit), sid)); return 2
    S = DSP.Sc(hit[0][0], hit[0][1], e)
    t30 = S.it.get(0x30)
    count = S.w(t30 - 4) if t30 is not None else 0
    sfi = [s['off'] for s in S.sfi()]
    # entries stored after the counted ones (same rule as work/q3_1711/sfi_lists.py: up to the next labelled word)
    targets = set(S.it.values())
    k = len(sfi)
    while t30 is not None and t30 + 8 * k + 8 <= len(S.d):
        a = t30 + 8 * k
        if a in targets or a in S.it: break
        cid, off = S.w(a), S.w(a + 4)
        if cid == 0 or cid > 0xffff or off > 0xffff: break
        sfi.append(off); k += 1
    pos = {}
    for j, off in enumerate(sfi):
        pos.setdefault(off, j)
    print('== %s (%s) script %d: %d members, header count %d (word +0x%x), %d sfi entries stored (%d after the count)'
          % (path, e, sid, len(S.members()), count, (t30 - 4) if t30 is not None else -1, len(sfi), len(sfi) - count))
    bad = 0
    for m in S.members():
        tn = nat.get(m['ty'], '?') if m['tyref'] == 8 else '-'
        if tname and tn != tname: continue
        p = pos.get(m['off'])
        inside = p is not None and p < count
        native = m['tyref'] == 8 and m['ty'] in nat      # only native members are built from the sfi list
        flag = '' if inside or m['init'] is None or not native else '  <-- not constructed (no parent widget)'
        if flag: bad += 1
        print('  m%-3d +0x%03x sym %5d %-16s init %-3s sfi %-4s %s%s' % (m['i'], m['off'], m['name'], tn,
              'yes' if m['init'] is not None else 'no', '-' if p is None else p, 'in' if inside else 'OUT', flag))
    print('  -> %d member(s) of the selection with an init block but no constructed sfi entry' % bad)
    return 1 if bad else 0


def stored_sfi(S):
    """(header count, stored entry offsets) of one script section"""
    t30 = S.it.get(0x30)
    if t30 is None: return 0, []
    count = S.w(t30 - 4)
    out = [s['off'] for s in S.sfi()]
    targets = set(S.it.values())
    k = len(out)
    while t30 + 8 * k + 8 <= len(S.d):
        a = t30 + 8 * k
        if a in targets or a in S.it: break
        cid, off = S.w(a), S.w(a + 4)
        if cid == 0 or cid > 0xffff or off > 0xffff: break
        out.append(off); k += 1
    return count, out


def scan(path, ref):
    """every script of DRM whose sfi header count is below its stored entries, with the reference (tu:) count"""
    secs, e = FL.sections(path)
    rcount = {}
    if ref:
        rsecs = DSP.read_tu(ref[3:]) if ref.startswith('tu:') else FL.sections(ref)[0]
        re_ = 'be' if ref.startswith('tu:') else FL.sections(ref)[1]
        for ty, s, d, rl in rsecs:
            if ty != 8 or not d: continue
            try: rcount[s] = stored_sfi(DSP.Sc(d, rl, re_))[0]
            except Exception: pass
    n = bad = 0
    for ty, s, d, rl in secs:
        if ty != 8 or not d: continue
        try: S = DSP.Sc(d, rl, e)
        except Exception as x:
            print('  script %d: not walked (%s)' % (s, x)); continue
        c, ent = stored_sfi(S); n += 1
        r = rcount.get(s)
        if len(ent) > c or (r is not None and r != c):
            bad += 1
            print('  script %5d: count %d, %d entries stored%s' % (s, c, len(ent), '' if r is None else ', reference count %d' % r))
    print('== %s: %d scripts, %d with a short / different sfi count' % (path, n, bad))
    return 1 if bad else 0


def main(argv):
    if argv and argv[0] == '--scan':
        if len(argv) < 2: raise SystemExit(__doc__)
        return scan(argv[1], argv[2] if len(argv) > 2 else None)
    tname = None
    if '--type' in argv:
        k = argv.index('--type'); tname = argv[k + 1]; argv = argv[:k] + argv[k + 2:]
    if len(argv) < 2: raise SystemExit(__doc__)
    sid = int(argv[1], 0)
    rc = 0
    for p in [argv[0]] + argv[2:]:
        rc = max(rc, check(p, sid, tname))
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
