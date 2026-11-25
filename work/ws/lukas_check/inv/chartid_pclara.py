"""chartid_pclara.py - (19/11/2026) SOLA LETTURA. Lato PC della tabella base del fork per chartid: legge pc-w\\lara.drm
(patch.000 se c'e', altrimenti bigfile.000) e il DTP 850 (state chart di Lara), elenca le voci attivita' di tipo 3/5
(id, tipo, valore). Lo scopo: vedere che valore ha sul PC la voce id 1114 tipo 3 (il fork: Xbox 0xd -> PC 0xc).
Confronto con doppelganger_casual DTP 20212 della baseline.
uso: python -I -B chartid_pclara.py BASELINE"""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/path/to/trudlcport/tools')
import faults_scan as F
import drm_write as DW
from archive import Archive
from dlc_names import fcrc
BS = chr(92)
L = []
def P(s): L.append(s); print(s)
h = fcrc('pc-w' + BS + 'lara.drm')
raw = None
for p in ('/path/to/trudlcport/pc/patch.000', '/path/to/trudlcport/pc/bigfile.000'):
    A = Archive(p, 'le'); rs = [r for r in A.idx if r['hash'] == h]
    if rs: raw = A.read(rs[-1]); P('lara.drm da %s (%d record)' % (p, len(rs))); break
D = DW.read(raw, 'le')
def entries(s, e):
    f = '>' if e == 'be' else '<'; out = collections.defaultdict(list)
    for r, hdr, lst in F.chart_records(s, e):
        for i in range(hdr[5]):
            eid, et = struct.unpack_from(f + 'HH', s.data, lst + 8 * i)
            if et in (3, 5): out[(eid, et)].append(struct.unpack_from(f + 'I', s.data, lst + 8 * i + 4)[0])
    return out
c850 = [s for s in D.sections if s.type == 7 and s.id == 850]
E = entries(c850[0], 'le') if c850 else {}
P('pc_lara DTP 850: voci tipo 3/5 %s' % {k: [hex(v) for v in vs] for k, vs in sorted(E.items())})
B = '/path/to/trudlcport/work/baseline/%s/mods/' % sys.argv[1]
for root, _, fs in os.walk(B):
    for f in fs:
        if f.lower() != 'doppelganger_casual.drm': continue
        PD = DW.read(open(os.path.join(root, f), 'rb').read(), 'le')
        s = [x for x in PD.sections if x.type == 7 and x.id == 20212][0]
        E2 = entries(s, 'le')
        P('B276 doppelganger_casual DTP 20212: voci tipo 3/5 %s' % {k: [hex(v) for v in vs] for k, vs in sorted(E2.items())})
        xr, pk, _ = F.xbox(os.path.relpath(os.path.join(root, f), B).replace(BS, '/'))
        XD = DW.read(xr, 'be'); xs = [x for x in XD.sections if x.type == 7 and x.id == 20212][0]
        P('Xbox (%s) DTP 20212: voci tipo 3/5 %s' % (pk, {k: [hex(v) for v in vs] for k, vs in sorted(entries(xs, 'be').items())}))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chartid_pclara_%s.log' % sys.argv[1]), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
