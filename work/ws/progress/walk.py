"""walk.py - percorso guidato del DLC1 unita' per unita' (offline): composizione, finding del gate, float non convertiti, confronto intro Xbox/PC.
Uso: python -I work/ws/progress/walk.py <baseline> (default B14)"""
import sys, os, json, struct, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import drm, unit_ids as U, objlists as OL
from convert_dlc import raw_dlc
BL = sys.argv[1] if len(sys.argv) > 1 else 'B14'
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..') + '/'
MODS = W + 'baseline/%s/mods/' % BL
gate = json.load(open(W + 'ws/raftring/gate/%s.json' % BL))
GF = collections.defaultdict(list)
for x in gate['findings']: GF[x['file']].append(x)
PO = OL.read_objectlist(open(MODS + 'tr8/pc-w/objectlist.txt', 'rb').read()) if os.path.exists(MODS + 'tr8/pc-w/objectlist.txt') else {}
XO = OL.read_objectlist(open(W + 'dlc1/objectlist.txt', 'rb').read())
UNITS = ['dlc_level1_start', 'dlc_caverns', 'dlc_caverns_hall', 'dlc_water_wheel', 'dlc_watertunnel', 'dlc_pillory', 'dlc_dungeon']
allf = {}
for r, _, fs in os.walk(MODS):
    for f in fs:
        if f.lower().endswith('.drm'): allf[os.path.relpath(os.path.join(r, f), MODS).replace('\\', '/')] = os.path.join(r, f)
def secs(path, e): return drm.sections_with_data(drm.cdrm_decode(open(path, 'rb').read(), e), e)[1]
def intros(sc, e):
    L = U.level_info(sc, e); E = '>' if e == 'be' else '<'; out = {}
    if not L: return out
    for si, o in L['intros']:
        d = sc[si]['data']
        out[struct.unpack_from(E + 'I', d, o + 0x58)[0]] = (struct.unpack_from(E + 'H', d, o + 0x50)[0], struct.unpack_from(E + '4f', d, o), struct.unpack_from(E + '4f', d, o + 0x10))
    return out
out = ['# Percorso guidato DLC1 (%s) - offline\n' % BL]
seen_obj = set()
for u in UNITS:
    out.append('\n## Unita\' `%s`\n' % u)
    ufile = u + '.drm'
    files = [f for f in allf if f == ufile or f.startswith('streamgroups/' + u + '_') or os.path.basename(f).startswith(u + '_')]
    # oggetti dalle intro dell'unita'
    objs = collections.Counter(); icmp = None
    if ufile in allf:
        try:
            ps = secs(allf[ufile], 'le'); pi = intros(ps, 'le')
            for uid, (oid, rot, pos) in pi.items(): objs[PO.get(oid, '?%d' % oid)] += 1
            raw, _ = raw_dlc(ufile)
            if raw is not None:
                xi = intros(secs_x := drm.sections_with_data(drm.cdrm_decode(raw, 'be'), 'be')[1], 'be')
                nd = sum(1 for uid, x in xi.items() if uid in pi and (max(abs(a - b) for a, b in zip(x[2], pi[uid][2])) > 1e-3 or max(abs(a - b) for a, b in zip(x[1], pi[uid][1])) > 1e-3 or XO.get(x[0]) != PO.get(pi[uid][0])))
                only_x = [uid for uid in xi if uid not in pi]; only_p = [uid for uid in pi if uid not in xi]
                icmp = (len(xi), len(pi), nd, len(only_x), len(only_p))
        except Exception as ex: icmp = ('errore', str(ex)[:60])
    out.append('- file dell\'unita\': %d (%s)' % (len(files), ', '.join(sorted(os.path.basename(f) for f in files))[:300]))
    out.append('- intro: Xbox/PC/diversi/solo-Xbox/solo-PC = %s' % (icmp,))
    ob = []
    for n, c in objs.most_common(): 
        cand = [f for f in allf if os.path.basename(f) == n + '.drm']
        ob.append('%s x%d%s' % (n, c, '' if cand else ' [DRM assente nel set]'))
    out.append('- oggetti nelle intro (%d tipi): %s' % (len(objs), '; '.join(ob)[:900]))
    # finding gate sui file dell'unita' + sui DRM degli oggetti
    objfiles = [f for n in objs for f in allf if os.path.basename(f) == n + '.drm']
    scope = sorted(set(files) | set(objfiles) | {f for f in allf if os.path.basename(f) in [os.path.basename(g) for g in files + objfiles]})
    tot = collections.Counter(); crit = []
    for f in scope:
        for x in GF.get(f, []):
            tot[x['tier']] += 1
            if x['tier'] <= 4: crit.append(x)
    out.append('- finding del gate su %d file dell\'unita\' e dei suoi oggetti: per tier %s' % (len(scope), dict(sorted(tot.items()))))
    cc = collections.Counter((x['tier'], x['tool'], x['check'], x['code'], x['file']) for x in crit)
    for k, v in sorted(cc.items())[:25]: out.append('    - tier %d %s/%s/%s %s x%d' % (k[0], k[1], k[2], k[3], k[4], v))
open(W + 'ws/progress/REPORT_WALK_%s.md' % BL, 'w').write('\n'.join(out) + '\n')
print('\n'.join(out)[:6000])
