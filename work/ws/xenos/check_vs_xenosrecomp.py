"""Cross-check xenos_xlat.text(style='compat') against the HLSL that underworld-xenon's modified XenosRecomp produced for the
captured TRU shaders (userdata/shadercache-v11/*.bin + *.hlsl).  Both are interpretations of the same bitfields: agreement
shows that my port reproduces their decoder, NOT that either matches the hardware.   usage: python -I check_vs_xenosrecomp.py [CACHEDIR]"""
import sys, os, re, glob, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xenos_xlat as X
cache = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/Downloads/Recomp/underworld-xenon/userdata/shadercache-v11')
SKIP = ('{', '}', 'return;', 'break;')
def norm(lines):
    out = []
    for l in lines:
        s = re.sub(r'\s+', '', l)
        if 'CubeMapData' in s: continue
        if 'SPEC_CONSTANT' not in s: s = s.replace('return;', '')
        if not s or s.startswith('//') or s in SKIP or 'SPEC_CONSTANT' in s or s.startswith('clip(oC0.w-g_AlphaThreshold') or s.startswith('oPos.xy+='): continue
        out.append(s.replace('g_CameraPosition', 'CameraPosition'))
    return out
def theirs(path):
    t = open(path).read().split('\n')
    i = max(k for k, l in enumerate(t) if l.strip() == 'float ps = 0.0;')
    body = t[i + 1:]
    return norm(body)
OPS = re.compile(r'^(r\d+\.|o\w+\.|ps=|p0=|a0=|clip\()')
stats = collections.Counter(); bad = []
for b in sorted(glob.glob(os.path.join(cache, '*.bin'))):
    h = b[:-4] + '.hlsl'
    if not os.path.exists(h): stats['no hlsl'] += 1; continue
    blob = open(b, 'rb').read()
    try: sh = X.parse(blob)
    except Exception as e: stats['parse fail'] += 1; continue
    if not sh.is_ps: stats['vs (skipped)'] += 1; continue
    stats['ps'] += 1
    try:
        mine = norm(X.text(sh, 'compat').lines); th = theirs(h)
    except Exception as e:
        stats['exception'] += 1; bad.append((b, repr(e))); continue
    if mine == th: stats['identical'] += 1
    elif sorted(l for l in mine if OPS.match(l)) == sorted(l for l in th if OPS.match(l)):
        stats['same instructions, structured control flow differs (non-simple CF: my text does not emit switch(pc))'] += 1
    else:
        stats['differ'] += 1
        n = sum(1 for a, c in zip(mine, th) if a != c)
        bad.append((os.path.basename(b), len(mine), len(th), n))
print(dict(stats))
for x in bad[:15]: print(x)
