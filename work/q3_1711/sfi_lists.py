"""Read-only: the script header +0x30 list ('sfi' in tools/script_conv.py: u32 count, then count x {u32 class script id,
u32 member offset}) of every ported / new g_pda script in four versions: the Xbox original (pack11, be), the converted
input, the PC g_pda (ported scripts only) and a built file. The engine walks exactly `count` entries when it creates a
script instance (0x57c1e0: per entry handler vt+0x24 = construct the native member, e.g. a UI widget that adds itself
to the screen) - an entry past the count is never constructed.
Usage (repo root): ../bin/pyt -t 900 work/q3_1711/sfi_lists.py CONVERTED_G_PDA BUILT_G_PDA [SCRIPT_ID ...]"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
import gpda_port as GP
import drm_write as DW, drm_reloc as R


def sfi(d, rl, e):
    """(count, [(class id, offset)] up to the next labelled word) or None"""
    E = '>' if e == 'be' else '<'
    it = dict(R.parse(rl, e).internal)
    t = it.get(0x30)
    if t is None: return None
    n = struct.unpack_from(E + 'I', d, t - 4)[0]
    out = []
    targets = set(it.values())
    k = 0
    while t + 8 * k + 8 <= len(d) and k < max(n, 64):
        a = t + 8 * k
        if k >= n and (a in targets or a in it): break
        cid, off = struct.unpack_from(E + 'II', d, a)
        if k >= n and (cid == 0 or cid > 0xffff or off > 0xffff): break
        out.append((cid, off)); k += 1
    return t, n, out


def main(argv):
    conv, built = argv[0], argv[1]
    only = {int(x) for x in argv[2:]}
    K = GP.load_knowledge(); I = GP.ids()
    pk = {(s['type'], s['id']): s for s in GP.read_pack()}
    inv = {(t, I(t, x)): (t, x) for (t, x) in pk}
    pc = {(s['type'], s['id']): s for s in GP.read_pc()}
    C = {(s.type, s.id): s for s in DW.read(open(conv, 'rb').read(), 'le').sections}
    B = {(s.type, s.id): s for s in DW.read(open(built, 'rb').read(), 'le').sections}
    bad = 0
    for key, r in sorted(K['recipes'].items(), key=lambda q: int(q[0].split(':')[1])):
        if r not in ('port', 'new93', 'new'): continue
        t, sid = map(int, key.split(':'))
        if t != 8 or (only and sid not in only): continue
        rows = []
        xs = pk.get(inv.get((t, sid)))
        if xs is not None: rows.append(('xbox %d' % inv[(t, sid)][1], sfi(xs['data'], xs['reloc'], 'be')))
        if (t, sid) in C: rows.append(('converted', sfi(C[(t, sid)].data, C[(t, sid)].reloc, 'le')))
        if r == 'port' and (t, sid) in pc: rows.append(('pc', sfi(pc[(t, sid)]['data'], pc[(t, sid)]['reloc'], 'le')))
        if (t, sid) in B: rows.append(('built', sfi(B[(t, sid)].data, B[(t, sid)].reloc, 'le')))
        print('== %s (%s)' % (key, r))
        xn = rows[0][1][1] if rows and rows[0][0].startswith('xbox') and rows[0][1] else None
        for nm, v in rows:
            if v is None: print('   %-10s no +0x30 list' % nm); continue
            a, n, L = v
            flag = ''
            if nm in ('converted', 'built') and xn is not None and n != xn:
                flag = '  <-- count %d != Xbox count %d' % (n, xn)
                if nm == 'built': bad += 1
            print('   %-10s +0x%x count %d%s' % (nm, a, n, flag))
            print('              %s' % ' '.join('%d@0x%x%s' % (c, o, '' if k < n else '(past count)') for k, (c, o) in enumerate(L)))
    print('built scripts whose +0x30 count differs from the Xbox count: %d' % bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
