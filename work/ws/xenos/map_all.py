"""Run xenos_map (symbolic unification) over every DLC1 PS lib pair (DLC lib -> surrogate Xbox lib of work/render/dlc_shader_map.json) of class C1/C2/C3/D.
Per pair: S param components referenced, unanimous (strong or weak votes, no conflict), conflict, no-vote; per material the same aggregated
over its passes.  Output out/map_all.json + out/map_all.tsv.   usage: tools/venv/bin/python -I work/ws/xenos/map_all.py [nproc]"""
import sys, os, json, collections, multiprocessing as mp
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import xenos_xlat as X, case_study as CS

def work(a):
    dl, sl = a
    try:
        out, table, cls = CS.run(dl, sl, None, write=False)
        n_roots = [l for l in out if l.startswith('permutation pairs')][0]
        ident = sum(1 for s, c, b, e, r in table if b and b[0] != 'k' and b[0] == s and c != 'CONFLICT')
        nonid = sum(1 for s, c, b, e, r in table if b and c != 'CONFLICT' and b[0] != 'k' and b != s)
        return dict(dl=dl, sl=sl, cls=dict(cls), n=len(table), ident=ident, nonident=nonid, hdr=n_roots,
                    table=[(s, c, b, str(e)) for s, c, b, e, r in table])
    except Exception as e:
        return dict(dl=dl, sl=sl, error=repr(e)[:200])

if __name__ == '__main__':
    smap = {int(k): v for k, v in json.load(open(os.path.join(ROOT, 'work/render/dlc_shader_map.json'))).items()}
    cen = json.load(open(os.path.join(HERE, 'out', 'census.json')))
    L = X.load_libs()
    jobs = []
    for r in cen:
        if r['cls'] in ('A', 'B') or r['kind'] != 1: continue
        m = smap[r['id']]
        if L['D'][r['id']]['kind'] != 1: continue
        jobs.append((r['id'], m['surrogate']))
    print('pairs', len(jobs)); sys.stdout.flush()
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    res = []
    with mp.Pool(n) as p:
        for i, r in enumerate(p.imap_unordered(work, jobs)):
            res.append(r)
            if i % 10 == 0: print(i, len(jobs)); sys.stdout.flush()
    json.dump(res, open(os.path.join(HERE, 'out', 'map_all.json'), 'w'))
    print('done')
