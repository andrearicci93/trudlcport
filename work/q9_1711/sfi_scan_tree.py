"""Q9 (18.11.): tools/script_sfi_members.py --scan over every DRM of a whole tree (read-only).
Usage (repo root): ../bin/pyt -t 3600 work/q9_1711/sfi_scan_tree.py TREE
Prints the scan line of every DRM with a finding and a total; exit 1 when one DRM has a finding or fails to read."""
import sys, os, io, contextlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import script_sfi_members as SM


def main(tree):
    drms = scripts_seen = bad = err = 0
    for dp, dn, fn in os.walk(tree):
        dn.sort()
        for f in sorted(fn):
            if not f.lower().endswith('.drm') or 'truguard' in f.lower():
                continue
            p = os.path.join(dp, f)
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    rc = SM.scan(p, None)
            except Exception as x:
                err += 1
                print('ERROR %s: %s' % (os.path.relpath(p, tree), x))
                continue
            drms += 1
            out = buf.getvalue()
            last = [l for l in out.splitlines() if l.startswith('== ')]
            if last:
                try: scripts_seen += int(last[-1].split(': ')[1].split(' scripts')[0])
                except Exception: pass
            if rc:
                bad += 1
                print(out.rstrip())
    print('tree %s: %d DRMs, %d scripts, %d DRMs with a short / different sfi count, %d not read' % (tree, drms, scripts_seen, bad, err))
    return 1 if (bad or err) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
