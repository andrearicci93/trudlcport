"""F8 - censimento degli shader PC ILLUMINATI del gioco base (gemelli PC delle lib Xbox illuminate in pos2): il blocco luci e' delimitabile?
Per ogni lib PC x slot occupato:
  - blocco luci = dal primo `if bN` di primo livello all'ultimo `endif` di primo livello (catene di if su costanti bool);
  - letture di costanti/sampler/bool LUCI fuori dal blocco (se 0: il blocco contiene tutte le luci);
  - INGRESSI del blocco = componenti di registri temp letti nel blocco prima di essere scritti nel blocco;
  - USCITE = componenti temp scritte nel blocco e lette dopo (prima di essere riscritte);
  - costanti NON luci lette nel blocco (es. c108.y potenza speculare) = ingressi da rimappare;
  - temp massimi usati (margine per superficie tradotta + blocco PC <= 32);
  - slot: occupazione PC (8) vs Xbox (2): vale "slot PC k <-> slot Xbox k&1"?
uso: tools/venv/bin/python -I work/ws/shader4/f8_pc_lit_census.py  -> f8_pc_lit_census.tsv + f8_pc_lit_census.md"""
import sys, os, re, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f3_validate import *
import sm3opt
import xenos_xlat as XL

LIGHT_PC = re.compile(r'SunLight|ShadowLight|NonShadowLight|WorldToShadowMap|ShadowDepthBias|ShadowMapSampler|LightEnabled|ModulationMap')   # luci DIRETTE
AMB_PC = re.compile(r'Irradiance|g_Ambient')   # ambiente (calcolato fuori dalla catena); AttenuationSampler = anche nebbia: non contato
LIGHT_X = re.compile(r'p_Lights|LightEnabled|p_ShadowEnabled|ParallelShadow|Irradiance|GlobalAmbientColor|ShadowMap|Attenuation')
RS_BOOL, RS_FLOAT, RS_SAMP = 0, 2, 3


def light_regs(ctab):
    f, s, b = set(), set(), set()
    for name, rs, ri, rc in ctab:
        if not LIGHT_PC.search(name): continue
        for k in range(rc):
            (f if rs == RS_FLOAT else s if rs == RS_SAMP else b if rs == RS_BOOL else set()).add(ri + k)
    return f, s, b


def analyse(blob):
    bc = blob[:sm3dis.bytecode_len(blob)]
    prog = sm3asm.decode(bc); ctab = sm3dis.ctab_of(bc) or []
    lf, ls, lb = light_regs(ctab)
    ins = [i for i in prog.instrs() if i.op not in ('dcl', 'def', 'defi', 'defb')]
    stype = {}
    for i in prog.instrs():
        if i.op == 'dcl' and i.ops[0].rtype == sm3asm.RT_SAMPLER: stype[i.ops[0].num] = (i.usage >> 27) & 15
    # blocco: if bN di primo livello
    depth = 0; start = end = None; nif = 0
    for k, i in enumerate(ins):
        if i.op == 'if':
            if depth == 0 and i.ops and i.ops[0].rtype == sm3asm.RT_CONSTBOOL:
                if start is None: start = k
                nif += 1
            depth += 1
        elif i.op == 'endif':
            depth -= 1
            if depth == 0 and start is not None: end = k
    def reads(i):
        out = []
        for j, o in enumerate(i.ops):
            if o.isdst: continue
            dm = i.ops[0].wm if i.ops and i.ops[0].isdst else 15
            st = stype.get(i.ops[2].num) if i.op.startswith('texld') and len(i.ops) > 2 else None
            try: comps, _ = sm3opt.lanes_read(i, j, dm, st)
            except Exception: comps = [0, 1, 2, 3]
            out.append((o.rtype, o.num, comps))
        return out
    def is_light(rt, n):
        return (rt == sm3asm.RT_CONST and n in lf) or (rt == sm3asm.RT_SAMPLER and n in ls) or (rt == sm3asm.RT_CONSTBOOL and n in lb)
    res = dict(n_instr=len(ins), n_if_bool=nif, has_block=start is not None)
    maxt = max([o.num for i in ins for o in i.ops if o.rtype == sm3asm.RT_TEMP] or [-1]) + 1
    res['temps'] = maxt
    if start is None:
        res['light_outside'] = sum(1 for i in ins for rt, n, _ in reads(i) if is_light(rt, n)); return res
    blk = range(start, end + 1)
    res['light_outside'] = sum(1 for k, i in enumerate(ins) if k not in blk for rt, n, _ in reads(i) if is_light(rt, n))
    amb = set()
    for name, rs, ri, rc in ctab:
        if rs == RS_FLOAT and AMB_PC.search(name): amb |= set(range(ri, ri + rc))
    res['amb_in_block'] = sum(1 for k in blk for rt, n, _ in reads(ins[k]) if rt == sm3asm.RT_CONST and n in amb)
    res['amb_outside'] = sum(1 for k, i in enumerate(ins) if k not in blk for rt, n, _ in reads(i) if rt == sm3asm.RT_CONST and n in amb)
    # ingressi: temp letti nel blocco prima di essere scritti nel blocco (approssimazione lineare, ignora rami)
    written = set(); inputs = set(); nonlight_c = set()
    for k in blk:
        i = ins[k]
        for rt, n, comps in reads(i):
            if rt == sm3asm.RT_TEMP:
                for c in comps:
                    if (n, c) not in written: inputs.add((n, c))
            if rt == sm3asm.RT_CONST and n not in lf and n not in amb: nonlight_c.add(n)
        if i.ops and i.ops[0].isdst and i.ops[0].rtype == sm3asm.RT_TEMP:
            for c in range(4):
                if i.ops[0].wm >> c & 1: written.add((i.ops[0].num, c))
    # uscite: scritte nel blocco e lette dopo prima di essere riscritte
    outputs = set(); killed = set()
    for k in range(end + 1, len(ins)):
        i = ins[k]
        for rt, n, comps in reads(i):
            if rt == sm3asm.RT_TEMP:
                for c in comps:
                    if (n, c) in written and (n, c) not in killed: outputs.add((n, c))
        if i.ops and i.ops[0].isdst and i.ops[0].rtype == sm3asm.RT_TEMP:
            for c in range(4):
                if i.ops[0].wm >> c & 1: killed.add((i.ops[0].num, c))
    res.update(n_in=len(inputs), n_out=len(outputs), nonlight_const_in_block=sorted(nonlight_c), start=start, end=end,
               pre=start, post=len(ins) - end - 1)
    return res


def main():
    L = libs(); X, P = L['X'], L['P']
    pos = positions()
    rows = []; agg = collections.Counter(); slotrule = collections.Counter(); hist_in = collections.Counter(); hist_out = collections.Counter()
    temps = []
    for x, p in sorted(x2p().items()):
        if X[x]['kind'] != 1 or 2 not in pos.get(x, set()) or p not in P: continue
        sh0 = XL.parse(X[x]['entries'][X[x]['slots'][0]]['blob'])
        if not any(LIGHT_X.search(c['name']) for c in sh0.ctab): continue
        # slot: per ogni slot PC occupato, lo slot Xbox k&1 esiste?
        xs = [s != 0xffffffff for s in X[x]['slots']]
        for k, s in enumerate(P[p]['slots']):
            if s == 0xffffffff: continue
            slotrule['ok' if (k & 1) < len(xs) and xs[k & 1] else 'slot Xbox k&1 assente'] += 1
        for k, s in enumerate(P[p]['slots']):
            if s == 0xffffffff: continue
            try: r = analyse(P[p]['entries'][s]['blob'])
            except Exception as e: agg['errore analisi'] += 1; continue
            r.update(x=x, p=p, slot=k); rows.append(r)
            if not r['has_block']: agg['nessuna catena if bool'] += 1
            elif r['light_outside']: agg['luci dirette anche fuori dalla catena'] += 1
            else:
                agg['luci dirette tutte nella catena' + (' + ambiente fuori' if r.get('amb_outside') else '') + (' + ambiente dentro' if r.get('amb_in_block') else '')] += 1
                hist_in[min(r['n_in'] // 4 * 4, 40)] += 1; hist_out[min(r['n_out'] // 4 * 4, 40)] += 1
            temps.append(r['temps'])
    with open(os.path.join(HERE, 'f8_pc_lit_census.tsv'), 'w') as f:
        keys = ['x', 'p', 'slot', 'n_instr', 'n_if_bool', 'has_block', 'light_outside', 'amb_outside', 'amb_in_block', 'n_in', 'n_out', 'temps', 'pre', 'post', 'nonlight_const_in_block']
        f.write('\t'.join(keys) + '\n')
        for r in rows: f.write('\t'.join(str(r.get(k, '')) for k in keys) + '\n')
    nlibs = len(set(r['p'] for r in rows))
    tc = collections.Counter(min(t // 4 * 4, 32) for t in temps)
    md = ['# F8 censimento shader PC illuminati (f8_pc_lit_census.py)', '',
          'Lib PC: %d, slot PC analizzati: %d' % (nlibs, len(rows)),
          'Blocco luci: ' + ', '.join('%s %d' % kv for kv in agg.most_common()),
          'Ingressi del blocco (componenti temp, a gruppi di 4): ' + ', '.join('%d+: %d' % kv for kv in sorted(hist_in.items())),
          'Uscite del blocco (componenti temp): ' + ', '.join('%d+: %d' % kv for kv in sorted(hist_out.items())),
          'Temp usati dal PS PC (a gruppi di 4): ' + ', '.join('%d+: %d' % kv for kv in sorted(tc.items())),
          'Regola slot PC k <-> Xbox k&1: ' + ', '.join('%s %d' % kv for kv in slotrule.most_common()),
          'Costanti NON luci lette nel blocco (piu frequenti): ' + str(collections.Counter(c for r in rows for c in r.get('nonlight_const_in_block', [])).most_common(8)),
          '', 'Dettaglio: f8_pc_lit_census.tsv']
    open(os.path.join(HERE, 'f8_pc_lit_census.md'), 'w').write('\n'.join(md) + '\n')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
