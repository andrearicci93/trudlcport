"""Read-only (doppel_1411, 2026-11-14): Xbox base and pack11 words of g_pda sections given by PC id, next to the PC
g_pda and a built g_pda (tools/gpda_port.py readers + DlcIds map; nothing written).
Usage (from trudlcport): ../bin/pyt -t 900 work/doppel_1411/gpda_xbox_words.py BUILT.drm TYPE:PCID[@OFF,OFF..] [...]
Without @OFF all words are printed (small DTPs only)."""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import gpda_port as G
import drm_write as DW, drm_reloc as R


def main(a):
    I = G.ids()
    PK = G.read_pack(); XB = G.read_xbase(); PC = G.read_pc()
    BU = DW.read(open(a[0], 'rb').read(), 'le').sections
    def by_pc(S, t, pid, xbox):
        for s in S:
            if s['type'] == t and (I(t, s['id']) if xbox else s['id']) == pid: return s
        return None
    for spec in a[1:]:
        offs = None
        if '@' in spec: spec, o = spec.split('@'); offs = [int(x, 16) for x in o.split(',')]
        t, pid = (int(x) for x in spec.split(':'))
        xp, xb, pc = by_pc(PK, t, pid, True), by_pc(XB, t, pid, True), by_pc(PC, t, pid, False)
        bu = next((s for s in BU if (s.type, s.id) == (t, pid)), None)
        print('== PC %d:%d  pack11 xbox id %s size %s | xbox base id %s size %s | PC size %s | built size %s' % (
            t, pid, xp and xp['id'], xp and hex(len(xp['data'])), xb and xb['id'], xb and hex(len(xb['data'])),
            pc and hex(len(pc['data'])), bu and hex(len(bu.data))))
        n = max(len(x['data']) if isinstance(x, dict) else len(x.data) for x in (xp, xb, pc, bu) if x is not None)
        for o in (offs if offs else range(0, n - 3, 4)):
            def w(x, e):
                if x is None: return '--------'
                d = x['data'] if isinstance(x, dict) else x.data
                return '%08x' % struct.unpack_from(e + 'I', d, o)[0] if o + 4 <= len(d) else '--------'
            row = (w(xb, '>'), w(xp, '>'), w(pc, '<'), w(bu, '<'))
            print('  +0x%04x xbox-base %s pack11 %s PC %s built %s%s' % ((o,) + row + ('' if row[0] == row[1] and row[2] == row[3] else '   *',)))
        for nm, x, e in (('pack11', xp, 'be'), ('xbox-base', xb, 'be'), ('PC', pc, 'le')):
            if x is None: continue
            r = R.parse(bytes(x['reloc']), e)
            print('  %s relocs: internal %s external %s idref %s' % (nm, sorted(r.internal)[:12], r.external[:6],
                                                                    sorted(r.idref + r.idref_a)[:12]))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
