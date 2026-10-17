"""Task 3 - driver sui 19 materiali delle 6 famiglie rifiutate: regola di famiglia (mp_resolve) + f9m.build + registri virtuali + gate offline di f12.
Non scrive in work/ws/shader4 ne' nelle baseline. Uso: task3_run.py [ONLY=id,id,...]  -> out_task3/task3.json + .md"""
import sys, os, json, struct, collections, time
S4 = '/path/to/trudlcport/work/ws/shader4'; CF = '/path/to/trudlcport/work/ws/codefirst'; ROOT = '/path/to/trudlcport'
sys.path.insert(0, S4); sys.path.insert(0, CF)
import f9m
import f12_build_all as F12
from f12_build_all import *
import mp_resolve, struct_resolve
OUT3 = CF + '/out_task3'; os.makedirs(OUT3, exist_ok=True)
FAM19 = {20344, 21093, 21258, 22596, 22597, 23186, 23437, 24043, 21086, 21209, 23371, 23372, 21087, 23568, 20992, 23375, 20856, 20857, 21126}
DONOR_OVERRIDE = {(1409, 1038): (164, 207)}     # (1409,1038) e' una variante PC anomala: il donatore (164,207) riproduce il PC vero di tutta la classe (donor_matrix_B)


def apply_virt(T, virt, XPm):
    """registri virtuali (>=116) -> def col valore composto dai parametri Xbox del materiale (lib usata da un solo materiale)."""
    if not virt: return T, {}
    B = body(T); hdr = header(T)
    taken = {o.num for i in T.instrs() for o in i.ops if o.rtype == sm3asm.RT_CONST}
    free = [r for r in range(223, 0, -1) if r not in taken and not 100 <= r < 116]
    newdefs = []; remap = {}; info = {}
    for vr, spec in sorted(virt.items()):
        v = [0.0] * 4
        for c, src in spec.items(): v[c] = float(src[1]) if src[0] == 'k' else float(XPm[src[0] - 100][src[1]])
        r = free.pop(0); remap[vr] = r; info[vr] = (r, v)
        newdefs.append(sm3asm.parse_text('ps_3_0\ndef c%d, %s\n' % (r, ', '.join('%.9g' % x for x in v))).instrs()[0])
    for i in B:
        for o in i.ops:
            if not o.isdst and o.rtype == sm3asm.RT_CONST and o.num in remap: o.num = remap[o.num]
    return sm3asm.Program(T.kind, T.major, T.minor, hdr + newdefs + B), info


def _live_out_sets(B):
    """liveness all'indietro a livello di registro temp (prudente: scrittura parziale o dentro if non uccide). Ritorna, per ogni istruzione, i temp vivi DOPO di essa."""
    live = set(); outs = [None] * len(B); depth = 0
    for k in range(len(B) - 1, -1, -1):
        i = B[k]; outs[k] = set(live)
        if i.op == 'endif': depth += 1; continue
        if i.op in ('if', 'ifc'):
            depth -= 1
            for o in i.ops:
                if not o.isdst and o.rtype == sm3asm.RT_TEMP: live.add(o.num)
            continue
        if i.op == 'else': continue
        if i.ops and i.ops[0].isdst and i.ops[0].rtype == sm3asm.RT_TEMP and depth == 0 and i.ops[0].wm == 15 and not i.pred:
            live.discard(i.ops[0].num)
        for o in i.ops:
            if not o.isdst and o.rtype == sm3asm.RT_TEMP: live.add(o.num)
            if o.rel and o.relop is not None and o.relop.rtype == sm3asm.RT_TEMP: live.add(o.relop.num)
    return outs


def legalize_consts(T):
    """ps_3_0: una istruzione puo' leggere UN solo registro costante. Per le istruzioni con >1 registri costanti distinti
    le sorgenti extra passano da un temp scratch (mov rS, cK subito prima). Lo scratch e' un temp MAI usato dal programma, altrimenti
    (giro 3) un temp MORTO in quel punto (non vivo dopo l'istruzione e non referenziato da essa). Ritorna (prog, n_mov)."""
    hdr = header(T); B = body(T)
    used = {o.num for i in T.instrs() for o in i.ops if o.rtype == sm3asm.RT_TEMP}
    never = [r for r in range(32) if r not in used]
    lo = _live_out_sets(B)
    out = []; nmov = 0
    for k, i in enumerate(B):
        cs = [o for j, o in enumerate(i.ops) if not o.isdst and o.rtype == sm3asm.RT_CONST]
        regs = []
        for o in cs:
            if o.num not in regs: regs.append(o.num)
        if len(regs) > 1:
            extra = regs[1:]
            refd = {o.num for o in i.ops if o.rtype == sm3asm.RT_TEMP}
            dead = [r for r in range(32) if r not in lo[k] and r not in refd and r in used]
            scratch = never + dead
            if len(extra) > len(scratch): raise f9m.Fail('temp scratch insufficienti per legalizzare le costanti (servono %d, liberi %d)' % (len(extra), len(scratch)))
            m = {r: scratch[q] for q, r in enumerate(extra)}
            for r in extra:
                mv = sm3asm.parse_text('ps_3_0\nmov r%d, c%d\n' % (m[r], r)).instrs()[0]
                out.append(mv); nmov += 1
            for o in cs:
                if o.num in m:
                    o.rtype = sm3asm.RT_TEMP; o.num = m[o.num]
        out.append(i)
    return sm3asm.Program(T.kind, T.major, T.minor, hdr + out), nmov


def main():
    ONLY = {int(x) for x in os.environ.get('ONLY', '').split(',') if x} or FAM19
    L = libs(); D, DM, X, P = L['D'], L['DM'], L['X'], L['P']
    lit = {int(r['id_xbox']): r for r in __import__('csv').DictReader(open(S4 + '/illuminati.tsv'), delimiter='\t')}
    rev = collections.defaultdict(list)
    for x, p in x2p().items(): rev[p].append(x)
    occ, secs = material_occurrences(SRC, DM, lambda dl: dl in lit)
    donor_cache = {}; res = {}; t0 = time.time()
    for mid, items in sorted(occ.items()):
        if mid not in ONLY: continue
        dl = struct.unpack_from('>4I', DM[mid][0], 0x28)[2]
        why = shared_problem(dl, items, secs)
        if why: res[mid] = dict(status='escluso-lifetime/regime-B', why=why); continue
        s = canonical_material(items); pc = struct.unpack_from('<4I', s.data, 0x28)[2]
        if dl not in donor_cache:
            need = {k for k, x in enumerate(P[pc]['slots']) if x != 0xffffffff} if pc in P else set(range(8))
            pref = [(x, pc) for x in rev[pc]]; ok = None
            for cand in find_donors('D', dl, 0, want=12, prefer=pref):
                have = {k for k, x in enumerate(P[cand[1]]['slots']) if x != 0xffffffff}
                if not need <= have: continue
                r1 = find_donors('D', dl, 1, want=1, prefer=[cand])
                if r1 and r1[0] == cand: ok = cand; break
            donor_cache[dl] = ok
        dn = donor_cache[dl]
        if dn is None: res[mid] = dict(status='escluso-nessun-donatore', why='nessun donatore'); continue
        dn0 = dn
        if dn in DONOR_OVERRIDE:
            alt = DONOR_OVERRIDE[dn]
            have = {k for k, x in enumerate(P[alt[1]]['slots']) if x != 0xffffffff}; need = {k for k, x in enumerate(P[pc]['slots']) if x != 0xffffffff} if pc in P else set(range(8))
            if need <= have: dn = alt
        xs, pd = dn; bridge = material_pairs(xs, pd)
        mres, ties = mp_resolve.resolve(xs, pd)
        mres, ties, snotes = struct_resolve.apply(xs, pd, mres, ties)
        XPm = params(f9_common._Sec(*DM[mid]), 'be'); PPm = params(s, 'le'); bad = None; tinfo = {}
        for k, e in enumerate(P[pd]['slots']):
            if e == 0xffffffff: continue
            xblob = D[dl]['entries'][D[dl]['slots'][k & 1]]['blob']
            try:
                mo = material_opts(mid)
                T, info = f9m.build(xblob, P[pd]['entries'][e]['blob'], X[xs]['entries'][X[xs]['slots'][k & 1]]['blob'], [(m_[2], m_[3]) for m_ in bridge], log=[], x_opts=mo, mp_res=mres)
                # pareggi: innocui solo se i valori Xbox dei candidati coincidono nel materiale
                for lane, cs in info['ties'].items():
                    vals = {round(float(XPm[c[0] - 100][c[1]]), 6) for c in cs if c[0] is not None and c[0] - 100 < len(XPm)}
                    tinfo[(slot_ := k, lane)] = sorted(vals)
                    if len(vals) > 1: raise f9m.Fail('pareggio non innocuo c%d.%s: valori Xbox dei candidati %s' % (lane[0], 'xyzw'[lane[1]], sorted(vals)))
                T, vinfo = apply_virt(T, info['virt'], XPm)
                T, binfo = bind_material(T, XPm, PPm)
                T, nleg = legalize_consts(T)
                bc, n, off, probs = offline_ok(T, xblob, XPm, opts=mo)
            except (f9m.Fail, Fail, xenos2sm3.Reject) as ex: bad = 'slot %d: %s' % (k, str(ex)[:160]); break
            except Exception as ex: bad = 'slot %d: ECCEZIONE %s' % (k, repr(ex)[:160]); break
            if probs: bad = 'slot %d: %s' % (k, probs); break
        res[mid] = dict(status='costruito' if not bad else 'escluso-offline', why=bad, donor=list(dn), donor_f12=list(dn0), pareggi=len(ties), strutturali={'c%d.%s' % (l[0], 'xyzw'[l[1]]): n for l, n in snotes.items()})
        print(mid, res[mid]['status'], bad or '', 'donatore', dn, flush=True)
    cnt = collections.Counter(r['status'] for r in res.values())
    json.dump(res, open(OUT3 + '/task3.json', 'w'), indent=1)
    open(OUT3 + '/task3.md', 'w').write('# Task 3 (19 materiali)\n' + ', '.join('%s %d' % kv for kv in cnt.items()) + '\n\n' + '\n'.join('- %d: %s %s donatore %s' % (m, r['status'], r['why'] or '', r.get('donor')) for m, r in sorted(res.items())) + '\n')
    print(dict(cnt), '%.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
