"""Il driver D3D9 nativo AMD rifiuta (D3DERR_INVALIDCALL) le istruzioni PS con 2+ registri costanti DIVERSI come sorgenti
(il port ne ha 3 'cmp' per shader in 500 shader). Fix: copiare le costanti oltre la prima in temporanei liberi
   cmp r4, c167, r8, c222.y   ->   mov rT, c222 ; cmp r4, c167, r8, rT.y
Ritorna (nuovi_byte, n_istruzioni_sistemate), oppure (None, -1) se non c'e' temporaneo libero / forma non gestita."""
import struct
import bisect_gen as bg

def _rt(t): return ((t >> 28) & 7) | (((t >> 11) & 3) << 3)

def fix(code):
    ver, ins = bg.parse(code)
    maxr = -1
    for op, tok, hdr, raw in ins:
        if raw or op in (0x1f, 0x51, 0x50, 0x52): continue
        for k, role in bg.operands(op, tok):
            if _rt(tok[k]) == 0: maxr = max(maxr, tok[k] & 0x7ff)
    base = maxr + 1; out = []; n = 0
    for op, tok, hdr, raw in ins:
        if raw or op in (0x1f, 0x51, 0x50, 0x52) or op in bg.NODST or len(tok) < 3:
            out.append([op, tok, hdr, raw]); continue
        opr = bg.operands(op, tok)
        cidx = [k for k, role in opr if role == 's' and _rt(tok[k]) == 2]
        regs = []
        for k in cidx:
            key = (tok[k] & 0x7ff, (tok[k] >> 13) & 1)
            if key not in regs: regs.append(key)
        if len(regs) < 2: out.append([op, tok, hdr, raw]); continue
        if any(r[1] for r in regs): return None, -1            # indirizzamento relativo: non gestito
        tk = list(tok); pre = []; nxt = base
        for key in regs[1:]:
            if nxt > 31: return None, -1
            pre.append([1, [0x800f0000 | nxt, 0xa0e40000 | key[0]], 1, False])
            for k in cidx:
                if (tk[k] & 0x7ff) == key[0]:
                    tk[k] = (tk[k] & 0x0fff0000) | 0x80000000 | nxt         # tipo temp, stesso swizzle/modificatore
            nxt += 1
        out += pre; out.append([op, tk, hdr, raw]); n += 1
    return bg.build(ver, out), n

def count_bad(code):
    ver, ins = bg.parse(code); n = 0
    for op, tok, hdr, raw in ins:
        if raw or op in (0x1f, 0x51, 0x50, 0x52) or op in bg.NODST or len(tok) < 3: continue
        s = set(tok[k] & 0x7ff for k, role in bg.operands(op, tok) if role == 's' and _rt(tok[k]) == 2)
        if len(s) >= 2: n += 1
    return n
