"""(1) Decoder comparison: tools/xenos_ps.py vs xenos_xlat.py on (a) the DLC1 shader libs (pack ack10.000) and (b) the 583 captured TRU PS of
underworld-xenon.  Output out/decoders.json + printed tables.   usage: tools/venv/bin/python -I work/ws/xenos/compare_decoders.py"""
import sys, os, json, collections, glob, struct
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import xenos_xlat as X, xenos_ps as XP
L = X.load_libs()
cen = json.load(open(os.path.join(HERE, 'out', 'census.json')))

def xp_const_refs(blob):
    """set of (slot, reg, comp) float-constant component references according to tools/xenos_ps.py"""
    s = set()
    for it in XP.instructions(blob):
        if it[0] == 'alu':
            for role, reg, lc in XP.alu_refs(it[2]):
                for l, c in lc: s.add((it[1], reg, c))
    return s

def xl_const_refs(sh):
    """same from xenos_xlat: reading the operands exactly as XenosRecomp does."""
    s = set()
    for e in X.walk(sh):
        if e[0] != 'alu': continue
        f = e[2]; slot = e[1]
        v = X.VOP[f['vopc']]
        vact = f['vmask'] != 0 or f['vopc'] in (15, 16, 17, 18, 19) or v.startswith(('setp', 'kill'))
        nv = {0: 2, 1: 2, 2: 2, 3: 2, 4: 2, 5: 2, 6: 2, 7: 2, 8: 1, 9: 1, 10: 1, 11: 3, 12: 3, 13: 3, 14: 3, 15: 2, 16: 2, 17: 3, 18: 1, 19: 1, 20: 2, 21: 2, 22: 2, 23: 2, 24: 2, 25: 2, 26: 2, 27: 2, 28: 2, 29: 1}[f['vopc']] if vact else 0
        for k, w in ((1, 'v0'), (2, 'v1'), (3, 'v2')):
            if k > nv: continue
            o = X.operand(f, w)
            if o.kind == 'c':
                for l in X.v_lanes(f, w): s.add((slot, o.reg, X.comp(o.swz, l)))
        so = f['sopc']
        if so != 50:
            if so in (42, 43, 44, 45, 46, 47):
                o = X.operand(f, 'sc0'); s.add((slot, o.reg, o.lanecomp(0)))
            else:
                o = X.operand(f, 's0')
                if o.kind == 'c': s.add((slot, o.reg, o.lanecomp(0)))
                if so in XP.SOP_TWO:
                    o = X.operand(f, 's1')
                    if o.kind == 'c': s.add((slot, o.reg, o.lanecomp(0)))
    return s

res = collections.defaultdict(collections.Counter)
featblobs = collections.defaultdict(set)
seen = set()
tot = collections.Counter(); diffrefs = []
def process(tag, blob, ident):
    h = hash(blob)
    if (tag, h) in seen: return
    seen.add((tag, h))
    try: sh = X.parse(blob)
    except Exception as e:
        res[tag]['parse fail'] += 1; return
    res[tag]['blobs'] += 1
    res[tag]['ps' if sh.is_ps else 'vs'] += 1
    try: mc = XP.microcode(blob)
    except Exception: mc = None
    if mc != sh.code: res[tag]['microcode differs (xenos_ps vs XenosRecomp extraction)'] += 1
    f = X.summary(sh)
    for k in f: res[tag]['feat:' + k] += 1; featblobs[tag, k].add(ident)
    if sh.is_ps:
        a = xp_const_refs(blob); b = xl_const_refs(sh)
        if a != b:
            res[tag]['const refs differ (xenos_ps vs xlat)'] += 1
            if len(diffrefs) < 8: diffrefs.append((tag, ident, sorted(a - b)[:4], sorted(b - a)[:4]))
        # count instructions seen
        n_xp = sum(1 for it in XP.instructions(blob) if it[0] != 'cf'); n_x = sum(1 for e in X.walk(sh) if e[0] != 'cf')
        if n_xp != n_x: res[tag]['instruction count differs'] += 1
        if sh.defs: res[tag]['has inline defs (def cN)'] += 1
        res[tag]['int/bool ctab present'] += any(c['set'] in (0, 1) for c in sh.ctab)
        res[tag]['samplers cube (CTAB)'] += any(c['type'] and c['type']['type'] == 14 for c in sh.ctab)
        res[tag]['samplers 3D (CTAB)'] += any(c['type'] and c['type']['type'] == 13 for c in sh.ctab)
        if sh.outputs is not None:
            if sh.outputs & 0x10: res[tag]['writes oDepth'] += 1
            if sh.outputs & 0xE: res[tag]['writes oC1..3 (MRT)'] += 1

for r in cen:
    lib = L['D'].get(r['id']) or L['X'].get(r['id'])
    if lib is None: continue
    grp = 'DLC1 non-A/B' if r['cls'] not in ('A', 'B') else 'DLC1 A/B'
    for s in set(lib['slots']) - {0xffffffff}:
        process(grp, lib['entries'][s]['blob'], '%d' % r['id'])
cache = os.path.expanduser('~/Downloads/Recomp/underworld-xenon/userdata/shadercache-v11')
for b in sorted(glob.glob(cache + '/*.bin')):
    process('TRU captured', open(b, 'rb').read(), os.path.basename(b)[:-4])
out = {}
for tag in res:
    print('==', tag)
    for k, v in sorted(res[tag].items()): print('   %-70s %d' % (k, v))
    out[tag] = dict(res[tag])
print('examples of const-ref disagreements', diffrefs)
json.dump(dict(counts=out, featlibs={'%s|%s' % k: sorted(v)[:200] for k, v in featblobs.items()}), open(os.path.join(HERE, 'out', 'decoders.json'), 'w'))
