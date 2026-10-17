"""Learn MaterialParams repacking rules per Xbox shader-id tuple from base pairs -> work/render/param_rules.pkl
and re-validate material_convert with the rules (in-sample and leave-one-out)."""
import sys, os, pickle, struct, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import material_convert as MC
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')
res = pickle.load(open(W + '/render/pairs_render.pkl', 'rb'))
mx2p = pickle.load(open(W + '/render/material_x2p.pkl', 'rb'))
sx2p = pickle.load(open(W + '/render/shader_x2p.pkl', 'rb'))
tmap = {int(k): v for k, v in json.load(open(W + '/generic/idmap.json'))['5'].items()}
mats = {}
for nm, X, P in res:
    for a, b in zip(X, P):
        if a['type'] == 10 and b['type'] == 10 and mx2p.get(a['id']) == b['id'] and a['id'] not in mats:
            mats[a['id']] = (a, b)
ex = collections.defaultdict(list)
for mid, (a, b) in mats.items():
    vx = MC.read_params(a['data'], a['reloc'], '>'); vp = MC.read_params(b['data'], b['reloc'], '<')
    ex[MC.shader_key(a['data'])].append((mid, vx, vp))
rules = {}
for k, l in ex.items():
    if any(vx != vp for _, vx, vp in l):
        r = MC.learn_rule([(vx, vp) for _, vx, vp in l])
        if r: rules[k] = r
pickle.dump(rules, open(W + '/render/param_rules.pkl', 'wb'))
st = collections.Counter()
for mid, (a, b) in mats.items():
    k = MC.shader_key(a['data'])
    for mode in ('insample', 'loo'):
        rule = rules.get(k)
        if mode == 'loo':
            others = [(vx, vp) for m, vx, vp in ex[k] if m != mid]
            need = any(vx != vp for _, vx, vp in ex[k])
            rule = MC.learn_rule(others) if (need and others) else None
        pr = (lambda v, r=rule: MC.apply_rule(r, v)) if rule else None
        pd, rl = MC.convert(a['data'], a['reloc'], lambda i: sx2p.get(i, i), lambda i: tmap.get(i, i), param_rule=pr)
        st[mode, 'exact'] += pd == b['data']
        st[mode, 'reloc_exact'] += rl == b['reloc']
        vx = MC.read_params(a['data'], a['reloc'], '>'); vp = MC.read_params(b['data'], b['reloc'], '<')
        if vx != vp:
            st[mode, 'repack-needed'] += 1
            st[mode, 'repack-params-exact'] += (MC.apply_rule(rule, vx) == vp) if rule else 0
st['n'] = len(mats); st['keys-with-rules'] = len(rules)
for k, v in sorted(st.items(), key=str): print(k, v)
