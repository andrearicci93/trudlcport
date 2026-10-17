"""Classify DRIFT words (fresh != installed, installed == vm_mods_expected base word, fresh changed by no installed fix)."""
import sys, os, collections, struct
sys.path.insert(0, os.path.expanduser('~/Downloads/tru-port/work/ws/rebuild')); sys.path.insert(0, os.path.expanduser('~/Downloads/tru-port/tools'))
import numpy as np, compare_rebuild as C
W = C.W; HERE = C.HERE
eff = {l.rstrip('\n').split('\t')[0]: l.rstrip('\n').split('\t')[4] for l in open(os.path.join(HERE, 'installed_effective.tsv')) if not l.startswith('relpath')}
cnt = collections.Counter(); per = collections.Counter(); ex = {}
for rel in sorted(eff):
    if not rel.endswith('.drm') or rel not in [os.path.relpath(p, os.path.join(HERE,'out_fresh')) for p in []] and not os.path.exists(os.path.join(HERE,'out_fresh',rel)): continue
    vmp = os.path.join(W, 'vm_mods_expected', rel)
    if not os.path.exists(vmp): continue
    ins, _, _ = C.load(eff[rel]); fr, _, _ = C.load(os.path.join(HERE, 'out_fresh', rel)); vm, _, _ = C.load(vmp)
    for k in ins:
        if k not in fr or k not in vm: continue
        a, b, v = ins[k]['data'], fr[k]['data'], vm[k]['data']
        if a is None or b is None or v is None or len(a) != len(b) or a == b: continue
        if len(a) % 4: a = a[:len(a)//4*4]; b = b[:len(b)//4*4]; v = v[:len(v)//4*4]
        A = np.frombuffer(a, '<u4'); Bf = np.frombuffer(b, '<u4'); V = np.frombuffer(v, '<u4')
        for w in np.nonzero(A != Bf)[0]:
            fi, fb, vb = int(A[w]), int(Bf[w]), int(V[w])
            if fi != vb: cnt['installed_not_base'] += 1; continue   # some installed fix touched it -> not this class
            fbE = struct.unpack('<I', struct.pack('>I', fb))[0]
            if fb == struct.unpack('<I', struct.pack('>I', fi))[0]: c = 'fresh=bswap32(inst)'
            elif fb == ((fi & 0xffff) << 16 | (fi >> 16)): c = 'fresh=u16halves_swapped(inst)'
            elif fi == struct.unpack('>I', struct.pack('<I', fb))[0]: c = 'inst=bswap32(fresh)'
            elif fi == ((fb & 0xffff) << 16 | (fb >> 16)): c = 'inst=u16halves_swapped(fresh)'
            else: c = 'other'
            cnt[c] += 1; per[rel] += 1
            ex.setdefault(c, (rel, k, int(w)*4, '%08x'%fi, '%08x'%fb))
print('DRIFT words (inst == base, fresh differs):', dict(cnt))
print('files with drift:', len(per)); print('examples', ex)
for r, n in per.most_common(25): print(' ', n, r)
