"""achievement_scan.py - (19/11/2026) solo lettura. Verifica del passo `achievement` del fork di Lukas
(suo tools/script_missing_native_fix.py, logica riscritta): ogni istruzione con operando (op65 = chiamata nativa) il cui
operando ha una rilocazione esterna verso uno script di tipo nativo del generalbank PC ORIGINALE (patch.000) a un offset
che NON e' l'inizio di una funzione della tabella PC = chiamata a puntatore nativo nullo (TU: achievement 21 native,
PC 16). Per op65 classifica la sequenza come il fork: dal marcatore di riga (op00) precedente fino alla chiamata, sicura
se solo push (op02..op10 senza op09). Nota: la catena exe (CATENA.md stadio dlc2data) aggiunge native NsLaraBase 70..73
e la classe dlc2data, NON native achievement: il riferimento resta la tabella PC (16).
uso: python -I -B achievement_scan.py BASELINE"""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW, drm_reloc as R, script_conv as SC, menu_dlc_probe as P
BL = sys.argv[1]
L = C.Log(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'achievement_scan_%s.log' % BL.split('_')[0]))
SAFE = {0x02, 0x03, 0x04, 0x05, 0x06, 0x08, 0x0c, 0x0d, 0x0e, 0x0f, 0x10}


def ftable(data, reloc, e):
    W = SC.Walk(data, R.parse(reloc, e), e).run()
    fa = [(t, n, sz) for nm, t, n, sz in W.arrays if nm == 'funcs']
    return {t + k * sz for t, n, sz in fa for k in range(n)}, sum(n for _, n, _ in fa)


def natives(secs, e):
    out = {}
    for s in secs:
        if s.type != 8 or not s.data: continue
        try: pkg, nat, size = P.script_info({'data': s.data, 'reloc': s.reloc}, e)
        except Exception: continue
        if nat: out[s.id] = (nat,) + ftable(s.data, s.reloc, e)
    return out


def instructions(d, rel):
    W = SC.Walk(d, rel, '<').run(); it = dict(rel.internal); res = []
    for name, t, n, sz in W.arrays:
        if name != 'funcs': continue
        for k in range(n):
            ct = it.get(t + k * sz + 0x18)
            if ct is None: continue
            cn = struct.unpack_from('<I', d, ct - 4)[0]; ins = []; j = 0
            while j < cn:
                o = ct + 4 * j; op = struct.unpack_from('<I', d, o)[0] >> 24
                ex = SC.Walk.EXTRA.get(op, 1 if op == P.PUSHF else 0)
                ins.append((o, op, ex)); j += 1 + ex
            res.append(ins)
    return res


gb, src = C.pc_generalbank()
NAT = natives(gb, 'le')
L('generalbank PC (%s): %d script nativi; achievement = %s' % (src, len(NAT), [(i, v[0], v[2]) for i, v in NAT.items() if v[0] == 'achievement']))
gb276 = DW.read(open(C.base_dir(BL) + 'generalbank.drm', 'rb').read(), 'le').sections
N276 = natives(gb276, 'le')
L('generalbank %s: achievement = %s' % (BL, [(i, v[0], v[2]) for i, v in N276.items() if v[0] == 'achievement']))
tot = collections.Counter(); files = collections.Counter(); bad_err = []
for rel, path in C.files(BL):
    try: D = DW.read(open(path, 'rb').read(), 'le')
    except Exception as ex: bad_err.append((rel, str(ex))); continue
    for s in D.sections:
        if s.type != 8 or not s.data: continue
        r = R.parse(s.reloc, 'le'); ext = {so: (si, do) for si, so, do in r.external}
        try: fl = instructions(s.data, r)
        except Exception as ex: bad_err.append((rel, s.id, str(ex))); continue
        for ins in fl:
            for i, (o, op, ex) in enumerate(ins):
                if ex < 1 or o + 4 not in ext: continue
                si, do = ext[o + 4]; t = D.sections[si]
                if t.type != 8 or t.id not in NAT: continue
                nm, fe, nf = NAT[t.id]
                if do in fe: continue
                idx = '?'
                if (do - min(fe)) % 0x1c == 0 if fe else False: idx = (do - min(fe)) // 0x1c
                tag = '%s script %d +0x%x -> %s(%d) +0x%x (indice %s, PC ha %d)' % (rel, s.id, o + 4, nm, t.id, do, idx, nf)
                if op != 0x65:
                    tot['non-chiamata op%02x %s' % (op, nm)] += 1
                    if tot['non-chiamata op%02x %s' % (op, nm)] <= 3: L('NOTE op%02x ' % op + tag)
                    continue
                j = i - 1
                while j >= 0 and ins[j][1] != 0x00: j -= 1
                ops = [q[1] for q in ins[j + 1:i]] if j >= 0 else None
                safe = 'nessun marcatore' if ops is None else 'op09 out' if 0x09 in ops else ('non-push %s' % sorted(set(ops) - SAFE)) if any(q not in SAFE for q in ops) else 'sicura'
                tot['op65 %s' % nm] += 1; tot['op65 %s %s' % (nm, safe)] += 1; files[rel, nm] += 1
                L('CALL ' + tag + ' seq=' + ' '.join('op%02x' % q for q in (ops or [])) + ' [%s]' % safe)
L('errori lettura/walk: %d %s' % (len(bad_err), bad_err[:5]))
L('file con chiamate achievement: %d (%s)' % (len({f for f, n in files if n == 'achievement'}), sorted({f for f, n in files if n == 'achievement'})))
L('TOTALE %s' % dict(sorted(tot.items())))
