"""Minimal Xenos (Xbox 360 / R500) pixel-shader microcode decoder, ONLY what is needed to align two compiles of
the same shader graph and read which MaterialParams components every instruction uses (tools/param_auto.py).
Encodings (ALU / CF / fetch) as in the public Xenia / freedreno a2xx documentation; every choice that matters was
checked against the hand-derived 2299 -> 1201 MaterialParams map of NOTES.md (see param_auto.py `oracle`).

Container (Xbox blob of a ShaderLib permutation): u32 magic 0x102A1100 ... header word[6] -> {u32 ?, u32 ucode size};
the microcode is the last `size` bytes before an 8-byte trailer. Program = 96-bit CF pairs (two 48-bit CF per 3
dwords) followed by 96-bit ALU / fetch instruction slots addressed in units of 3 dwords.
"""
import struct

EXEC_OPS = (1, 2, 3, 4, 5, 6, 13, 14)       # exec, exec_end, cond_exec(_end), cond_pred_exec(_end), cond_exec_pred_clean(_end)
VOP_NAMES = {0: 'add', 1: 'mul', 2: 'max', 3: 'min', 4: 'sete', 5: 'setgt', 6: 'setgte', 7: 'setne', 8: 'frac', 9: 'trunc',
             10: 'floor', 11: 'muladd', 12: 'cnde', 13: 'cndgte', 14: 'cndgt', 15: 'dot4', 16: 'dot3', 17: 'dot2add', 18: 'cube',
             19: 'max4', 20: 'pred_sete_push', 21: 'pred_setne_push', 22: 'pred_setgt_push', 23: 'pred_setgte_push',
             24: 'kille', 25: 'killgt', 26: 'killgte', 27: 'killne', 28: 'dst', 29: 'mova'}
# number of vector operands and the lanes of each operand that influence the result (None = lanes of the write mask)
VOP_OPERANDS = {0: 2, 1: 2, 2: 2, 3: 2, 4: 2, 5: 2, 6: 2, 7: 2, 8: 1, 9: 1, 10: 1, 11: 3, 12: 3, 13: 3, 14: 3, 15: 2, 16: 2,
                17: 3, 18: 2, 19: 1, 20: 2, 21: 2, 22: 2, 23: 2, 24: 2, 25: 2, 26: 2, 27: 2, 28: 2, 29: 1}
SOP_NOP = 50
SOP_CONST = (42, 43, 44, 45, 46, 47)        # mul/add/sub_const_0/1: src3 const (letter 4) with a temp (letter 1)
# scalar ops that read TWO components of src3 (letters 1 and 4): add, add_prev, mul, mul_prev, mul_prev2, max, min, sete, setgt,
# setgte, setne, sub, sub_prev, pred_set*, kill*; the others read a single component
SOP_TWO = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 25, 26, 27, 28, 29, 30, 35, 36, 37, 38, 39}


def microcode(blob):
    h = struct.unpack_from('>16I', blob, 0)
    p = h[6]
    _, sz = struct.unpack_from('>II', blob, p)
    uc = blob[len(blob) - 8 - sz:len(blob) - 8]
    return struct.unpack('>%dI' % (len(uc) // 4), uc)


def cf_list(w):
    out = []
    for i in range(0, len(w) - 2, 3):
        d0, d1, d2 = w[i:i + 3]
        out.append(d0 | ((d1 & 0xffff) << 32))
        out.append((d1 >> 16) | (d2 << 16))
    return out


def program(blob):
    """Returns (w, [cf records]) where an exec record is dict(op, addr, n, seq, raw). Stops where the instruction area
    starts (first exec address)."""
    w = microcode(blob)
    C = cf_list(w)
    recs = []
    lim = 10 ** 9
    for k, c in enumerate(C):
        if k >= 2 * lim: break
        op = (c >> 44) & 15
        if op in EXEC_OPS:
            a = c & 0xfff
            lim = min(lim, a)
            recs.append(dict(k=k, op=op, addr=a, n=(c >> 12) & 7, seq=(c >> 16) & 0xfff, raw=c))
        else:
            recs.append(dict(k=k, op=op, addr=None, n=0, seq=0, raw=c))
    return w, recs


def comp(sw, lane):
    """Relative Xenos swizzle: letter of output lane `lane`."""
    return ((sw >> (2 * lane)) + lane) & 3


def alu_fields(d0, d1, d2):
    f = dict(
        vdest=d0 & 63, vrel=(d0 >> 6) & 1, absc=(d0 >> 7) & 1, sdest=(d0 >> 8) & 63, srel=(d0 >> 14) & 1, export=(d0 >> 15) & 1,
        vmask=(d0 >> 16) & 15, smask=(d0 >> 20) & 15, vclamp=(d0 >> 24) & 1, sclamp=(d0 >> 25) & 1, sopc=(d0 >> 26) & 63,
        sw3=d1 & 255, sw2=(d1 >> 8) & 255, sw1=(d1 >> 16) & 255, neg3=(d1 >> 24) & 1, neg2=(d1 >> 25) & 1, neg1=(d1 >> 26) & 1,
        predc=(d1 >> 27) & 1, ispred=(d1 >> 28) & 1, addrabs=(d1 >> 29) & 1, c1rel=(d1 >> 30) & 1, c0rel=(d1 >> 31) & 1,
        reg3=d2 & 255, reg2=(d2 >> 8) & 255, reg1=(d2 >> 16) & 255, vopc=(d2 >> 24) & 31,
        sel3=(d2 >> 29) & 1, sel2=(d2 >> 30) & 1, sel1=(d2 >> 31) & 1)
    return f


def vec_lanes(f, k):
    """Lanes (0..3) of vector operand k (1..3) that influence the result."""
    v = f['vopc']; m = f['vmask']
    wl = [i for i in range(4) if (m >> i) & 1]
    if v == 15: return [0, 1, 2, 3] if k <= 2 else []        # dot4
    if v == 16: return [0, 1, 2] if k <= 2 else []           # dot3
    if v == 17: return [0, 1] if k <= 2 else [0]             # dot2add (src3.x)
    if v in (18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28): return [0, 1, 2, 3]
    return wl


def alu_refs(f):
    """Constant references of an ALU instruction: list of (role, reg_byte, [(lane, component)]) for every operand that is a
    float constant. role = 'v1','v2','v3' (vector) or 's3' (scalar src3)."""
    out = []
    nops = VOP_OPERANDS.get(f['vopc'], 0)
    vector_active = f['vmask'] != 0 or f['vopc'] in (15, 16, 17, 18, 19)
    for k in (1, 2, 3):
        if k > nops or not vector_active: continue
        if f['sel%d' % k] == 0:
            sw = f['sw%d' % k]
            out.append(('v%d' % k, f['reg%d' % k], [(l, comp(sw, l)) for l in vec_lanes(f, k)]))
    so = f['sopc']
    if so != SOP_NOP and f['sel3'] == 0:
        sw = f['sw3']
        if so in SOP_CONST: lanes = [3]
        elif so in SOP_TWO: lanes = [0, 3]
        else: lanes = [3]
        out.append(('s3', f['reg3'], [(l, comp(sw, l)) for l in lanes]))
    return out


def fetch_fields(d0, d1, d2):
    return dict(op=d0 & 31, src=(d0 >> 5) & 63, dst=(d0 >> 12) & 63, cidx=(d0 >> 20) & 31)


def instructions(blob):
    """Program-order list of instruction records: ('cf', rec) / ('alu', slot, fields) / ('fetch', slot, d0, d1, d2)."""
    w, recs = program(blob)
    out = []
    for r in recs:
        out.append(('cf', r))
        if r['addr'] is None: continue
        for j in range(r['n']):
            s = r['addr'] + j
            if 3 * s + 3 > len(w): continue
            d0, d1, d2 = w[3 * s:3 * s + 3]
            if (r['seq'] >> (2 * j)) & 1:
                out.append(('fetch', s, d0, d1, d2))
            else:
                out.append(('alu', s, alu_fields(d0, d1, d2), (d0, d1, d2)))
    return out
