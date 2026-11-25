"""anim_targets.py - (19/11/2026) SOLA LETTURA. Punti precisi che il fork cita per animlist (finding 44):
 - DTP 1581 dei dlc_costume_* / lara_doppelganger: 19 parole payload kind-0 che per il fork vanno come coppie u16;
 - fx_waterwheel_fsfx: una parola (float 1.0 come u32 secondo il fork, B138 meta' scambiate);
 - le 4 fx DLC2 presenti sia in pack11 che in pack10 (dlc_fx_cine_thrall_death, dlc_fx_goo_dun_ist, _tres_ist,
   _tres_line_ist): confronto delle due fonti Xbox e di B276 sulle parole payload delle liste anim.
Elenca ogni parola payload (non strutturale, non puntatore) delle liste anim abbinate per posizione dove PC != Xbox
grezzo, con la forma (raw/u16/u32/other).
uso: python -I -B anim_targets.py BASELINE"""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/path/to/trudlcport/tools')
import faults_scan as F
import drm_write as DW
from dlc_names import fcrc
BS = chr(92)
B = '/path/to/trudlcport/work/baseline/%s/mods/' % sys.argv[1]
L = []
def P(s): L.append(s); print(s)

def find(name):
    for root, _, fs in os.walk(B):
        for f in fs:
            if f.lower() == name: return os.path.join(root, f), os.path.relpath(os.path.join(root, f), B).replace(BS, '/')
    return None, None

def xb(rel, pack):
    h = fcrc('xenon-w' + BS + rel.replace('/', BS))
    rs = [r for r in F.arch(pack).idx if r['hash'] == h]
    return DW.read(F.arch(pack).read(rs[0]), 'be') if rs else None

def anim_payload(x, p, only=None):
    out = []
    w = F.an_walk(x.data, '>')
    if w is None or len(x.data) != len(p.data): return None
    sk = F.slots(x, 'be')
    for a, h, fr, sz in w[0]:
        for q in range(1, sz // 4):
            o = a + 4 * q
            if o in sk: continue
            x4 = bytes(x.data[o:o + 4]); p4 = bytes(p.data[o:o + 4])
            out.append((o, a, h & 3, sz // 4 - 2, q, x.data[a + 8], x4, p4, F.how(x4, p4, b'')))
    return out

# 1) DTP 1581
for n in ('dlc_costume_b', 'dlc_costume_c', 'dlc_costume_e', 'dlc_costume_f', 'dlc_costume_j', 'dlc_costume_o', 'lara_doppelganger'):
    path, rel = find(n + '.drm')
    if path is None: P('%s: assente' % n); continue
    xr, pk, oth = F.xbox(rel)
    if xr is None: P('%s: senza Xbox' % n); continue
    XD = DW.read(xr, 'be'); PD = DW.read(open(path, 'rb').read(), 'le')
    for k, x, p in F.pairs_by_position(XD, PD):
        if p.type != 7 or p.id != 1581: continue
        rows = anim_payload(x, p)
        if rows is None: P('%s 7:1581 (Xbox %d): non lista anim / dim diversa' % (n, x.id)); continue
        c = collections.Counter(r[-1] for r in rows if r[2] == 0)
        P('%s [%s] 7:1581 (Xbox %d) payload kind-0: %s' % (n, pk, x.id, dict(c)))
        for r in rows:
            if r[2] == 0 and r[-1] not in ('raw',) and r[6] != r[7]:
                P('   +0x%x rec +0x%x kind %d nw %d w%d b0 %d xbox %s pc %s %s' % (r[0], r[1], r[2], r[3], r[4], r[5], r[6].hex(), r[7].hex(), r[8]))
        o = 0xa6c
        P('   +0xa6c xbox %s pc %s' % (x.data[o:o + 4].hex(), p.data[o:o + 4].hex()))

# 2) waterwheel
path, rel = find('fx_waterwheel_fsfx.drm')
if path:
    xr, pk, oth = F.xbox(rel); XD = DW.read(xr, 'be'); PD = DW.read(open(path, 'rb').read(), 'le')
    for k, x, p in F.pairs_by_position(XD, PD):
        rows = anim_payload(x, p) if x.type == 7 else None
        if not rows: continue
        for r in rows:
            if r[6] != r[6][::-1] and r[-1] in ('u16', 'other'):
                P('fx_waterwheel_fsfx [%s] 7:%d +0x%x rec +0x%x kind %d nw %d w%d b0 %d xbox %s pc %s %s' % (pk, p.id, r[0], r[1], r[2], r[3], r[4], r[5], r[6].hex(), r[7].hex(), r[8]))

# 3) le 4 fx in due pack
for n in ('dlc_fx_cine_thrall_death', 'dlc_fx_goo_dun_ist', 'dlc_fx_goo_tres_ist', 'dlc_fx_goo_tres_line_ist'):
    path, rel = find(n + '.drm')
    if path is None: P('%s assente' % n); continue
    X11, X10 = xb(rel, 'pack11'), xb(rel, 'pack10'); PD = DW.read(open(path, 'rb').read(), 'le')
    same = X11 is not None and X10 is not None and [(s.type, s.id, s.data, s.reloc) for s in X11.sections] == [(s.type, s.id, s.data, s.reloc) for s in X10.sections]
    P('%s: pack11 %s, pack10 %s, identici %s' % (n, X11 is not None, X10 is not None, same))
    for tag, XD in (('pack11', X11), ('pack10', X10)):
        if XD is None: continue
        c = collections.Counter(); ex = []
        for k, x, p in F.pairs_by_position(XD, PD):
            rows = anim_payload(x, p) if x.type == 7 else None
            if not rows: continue
            for r in rows:
                c[r[-1]] += 1
                if r[2] == 1 and r[4] == 1 and r[-1] != 'u16' and len(ex) < 20: ex.append('7:%d +0x%x xbox %s pc %s %s' % (p.id, r[0], r[6].hex(), r[7].hex(), r[8]))
        P('   vs %s: payload %s; kind1 parola1 non-u16: %s' % (tag, dict(c), ex))
    if X11 is not None and X10 is not None and not same:
        d = collections.Counter()
        for a, b in zip(X11.sections, X10.sections):
            if (a.type, a.id) != (b.type, b.id): d['sezioni diverse'] += 1; continue
            if a.data != b.data:
                d['dati diversi tipo %d' % a.type] += 1
                if a.type == 7 and len(a.data) == len(b.data):
                    ws = [o for o in range(0, len(a.data) - 3, 4) if a.data[o:o + 4] != b.data[o:o + 4]]
                    P('   7:%d diverse %d parole: %s' % (a.id, len(ws), ['+0x%x %s/%s' % (o, a.data[o:o + 4].hex(), b.data[o:o + 4].hex()) for o in ws[:6]]))
        P('   differenze pack11/pack10: %s (sezioni %d/%d)' % (dict(d), len(X11.sections), len(X10.sections)))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'anim_targets_%s.log' % sys.argv[1]), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
