import sys, os, numpy as np
sys.path.insert(0, os.path.expanduser('~/Downloads/tru-port/work/ws/rebuild')); sys.path.insert(0, os.path.expanduser('~/Downloads/tru-port/tools'))
import compare_rebuild as C
rel, t, i = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
W = C.W
eff = {l.rstrip('\n').split('\t')[0]: l.rstrip('\n').split('\t')[4] for l in open(os.path.join(C.HERE, 'installed_effective.tsv')) if not l.startswith('relpath')}
ins, _, _ = C.load(eff[rel], want=None); fr, _, _ = C.load(os.path.join(C.HERE, 'out_fresh', rel), want=None)
vm = C.load(os.path.join(W, 'vm_mods_expected', rel), want=None)[0] if os.path.exists(os.path.join(W, 'vm_mods_expected', rel)) else {}
k = [x for x in ins if x[0] == t and x[1] == i][0]
f = np.frombuffer(fr[k]['data'], '<u4'); a = np.frombuffer(ins[k]['data'], '<u4')
v = np.frombuffer(vm[k]['data'], '<u4') if k in vm else None
d = np.nonzero(f != a)[0]
print('section', k, 'size', ins[k]['size'], 'words diff', len(d), 'vm present', v is not None)
for w in d[:10]:
    print('word@0x%x fresh=%08x inst=%08x vm=%s' % (w*4, f[w], a[w], '%08x' % v[w] if v is not None else '-'))
print('eff path', eff[rel])
