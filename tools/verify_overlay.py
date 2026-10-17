"""Byte-level check that a cumulative overlay (work/mods_next) contains EVERY correction set that was built before it.

For each fix set S (ordered, see SETS) and each file f that S produced: delta(S, f) = every data byte / reloc blob of every
section (type, id, occurrence) where S's output differs from S's input (the file S was built on).  For the final file F:
  present     F has S's output value at that byte
  superseded  F differs, but a LATER set that also rebuilt f has exactly F's value there (e.g. glitchfix2 re-ran the
              reslot rule from the base and replaced some glitchfix slot bytes)
  MISSING     anything else  -> error
Also: the A/B webs variant must differ from the main dlc_caverns only inside the index buffer of terrain section 20869.
usage: tools/venv/bin/python -I tools/verify_overlay.py [FINAL_DIR=work/mods_next]
"""
import sys, os, collections, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW
WK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')

def top(name, dirs):
    for d in reversed(dirs):
        p = os.path.join(WK, d, name)
        if os.path.exists(p): return p
    return None

def gf2_inputs():
    m = {}
    for ln in open(os.path.join(WK, 'glitchfix2_logs', 'inputs.txt')):
        ln = ln.strip()
        if not ln: continue
        rel = ln.split('/work/', 1)[1].split('/', 1)
        m[rel[1]] = os.path.join(WK, *ln.split('/work/', 1)[1].split('/'))
    return m

BASE = ['vm_mods_expected', 'mods_fix14', 'mods_glitchfix']
SETS = [  # (name, output dir, input resolver)
    ('fix14 animfx', 'mods_fix14', lambda n: top(n, ['vm_mods_expected'])),
    ('glitchfix reslot', 'mods_glitchfix', lambda n: top(n, ['vm_mods_expected', 'mods_fix14'])),
    ('glitchfix2 reslot2', 'mods_glitchfix2', lambda n: gf2_inputs().get(n)),
    ('fix15 aidata', 'mods_fix15', lambda n: top(n, BASE)),
    ('static(old) sarray', 'mods_static/dlc1', lambda n: top(n, BASE)),
    ('s1 aidata on gf2', 'next_stage/s1_cavhall', lambda n: top(n, ['mods_glitchfix2'])),
    ('s2 dtpid/dtplist/align/goo', 'next_stage/s2_dtpid', lambda n: top(n, BASE + ['mods_fix15', 'mods_glitchfix2', 'next_stage/s1_cavhall'])),
    ('s3 static sarray', 'next_stage/s3_static/dir', lambda n: top(n, BASE + ['mods_fix15', 'mods_glitchfix2', 'next_stage/s1_cavhall', 'next_stage/s2_dtpid'])),
]
SKIP = {'g_pda.drm'}

_C = {}
def secs(p):
    if p not in _C:
        D = DW.read(open(p, 'rb').read(), 'le'); occ = collections.Counter(); out = {}
        for s in D.sections:
            k = (s.type, s.id, occ[s.type, s.id]); occ[s.type, s.id] += 1
            out[k] = (s.data, s.reloc)
        _C[p] = out
    return _C[p]

def delta(pin, pout):
    a, b = secs(pin), secs(pout); d = {}
    for k, (data, rel) in b.items():
        if k not in a: d[(k, 'new')] = (data, rel); continue
        da, ra = a[k]
        if len(da) != len(data): d[(k, 'size')] = data; continue
        if da != data:
            for i in range(len(data)):
                if da[i] != data[i]: d[(k, i)] = data[i]
        if ra != rel: d[(k, 'reloc')] = rel
    return d

def val(S, key):
    k, i = key
    if k not in S: return None
    if i == 'reloc': return S[k][1]
    if i in ('new',): return S[k]
    if i == 'size': return S[k][0]
    return S[k][0][i] if i < len(S[k][0]) else None

def verify(final_dir):
    files = sorted(os.path.relpath(os.path.join(r, f), final_dir) for r, _, fs in os.walk(final_dir) for f in fs if f.endswith('.drm'))
    rep = {}; errors = 0
    for n in files:
        F = secs(os.path.join(final_dir, n)); rows = []
        built = [(nm, os.path.join(WK, od, n), fn(n)) for nm, od, fn in SETS if os.path.exists(os.path.join(WK, od, n)) and n not in SKIP]
        for j, (nm, pout, pin) in enumerate(built):
            if pin is None: rows.append((nm, 'NO INPUT', 0, 0, 0)); errors += 1; continue
            d = delta(pin, pout); pres = sup = miss = 0
            later = [secs(q[1]) for q in built[j + 1:]]
            for key, v in d.items():
                fv = val(F, key)
                if fv == v: pres += 1
                elif any(val(L, key) == fv for L in later): sup += 1
                else: miss += 1
            errors += miss
            rows.append((nm, os.path.relpath(pin, WK), len(d), pres, sup, miss))
        rep[n] = rows
    return rep, errors

def webs_check(main, variant):
    import terrain_convert as TC
    a, b = secs(main), secs(variant)
    diff = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
    if [k[:2] for k in diff] != [(12, 20869)]: return False, 'sections differ: %r' % diff
    k = diff[0]; da, db = a[k][0], b[k][0]
    if len(da) != len(db) or a[k][1] != b[k][1]: return False, 'size/reloc differ'
    T = TC.parse(bytearray(da), '<'); lo = T['H'] + T['offIdx']; hi = lo + 2 * T['nIdx']
    bad = [i for i in range(len(da)) if da[i] != db[i] and not lo <= i < hi]
    nb = sum(1 for i in range(lo, hi) if da[i] != db[i])
    return not bad, 'index buffer [%#x,%#x): %d bytes differ, outside: %d' % (lo, hi, nb, len(bad))

if __name__ == '__main__':
    fd = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WK, 'mods_next')
    rep, errors = verify(fd)
    for n, rows in rep.items():
        print(n, hashlib.md5(open(os.path.join(fd, n), 'rb').read()).hexdigest())
        for r in rows:
            print('   %-28s in=%-45s delta %6d  present %6d  superseded %5d  MISSING %d' % r if len(r) == 6 else '   %s %s' % r[:2])
    print('TOTAL MISSING', errors)
    for v in ('mods_next_ab_webs', 'mods_next_ab_webs_all'):
        p = os.path.join(WK, v, 'dlc_caverns.drm')
        if os.path.exists(p):
            ok, msg = webs_check(os.path.join(fd, 'dlc_caverns.drm'), p)
            print('webs variant', v, 'OK' if ok else 'FAIL', msg, hashlib.md5(open(p, 'rb').read()).hexdigest())
