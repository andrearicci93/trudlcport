"""Xenos (Xbox 360 R500) shader container parser + instruction-by-instruction HLSL-like translator + symbolic IR.
Written as a Python re-implementation of the SPECIFICATION embodied in XenosRecomp (hedge-dev, MIT; read only):
shader.h (container), shader_code.h (CF / ALU / fetch bitfields), constant_table.h (CTAB), shader_recompiler.cpp
(semantics), plus the UNDERWORLD_RECOMP additions of ~/Downloads/Recomp/XenosRecomp (conditional EXEC, CUBE via
operand decoding, face sign register).  Nothing is compiled; no file outside work/ws/xenos is touched.

API
  sh = parse(blob)                         container -> Shader (ctab, defs, interpolators, outputs, code words)
  text(sh, style='compat'|'pretty')        list of lines (compat = line-for-line the form XenosRecomp emits)
  summary(sh)                              features / constants used / samplers used / unsupported ops
  ir = IRBuilder(sh); roots = ir.run()     symbolic evaluation: hash-consed expression DAG of every export component
CLI
  xenos_xlat.py show   LIBID [slot]        translate lib (D/X libs from work/render/shaderlibs.pkl)
  xenos_xlat.py check                      cross-check with underworld-xenon HLSL for the captured TRU shaders
"""
import struct, sys, os, collections, math

SWZ = 'xyzw01__'

# ------------------------------------------------------------------------------------------------ container
class Shader:
    pass


def _cstr(b, o):
    e = b.find(b'\0', o)
    return b[o:e].decode('latin1')


def parse(blob):
    s = Shader(); s.blob = blob
    flags, vsize, psize, fc, ctoff, deftoff, shoff = struct.unpack_from('>7I', blob, 0)
    s.flags, s.vsize, s.psize, s.ctoff, s.deftoff, s.shoff = flags, vsize, psize, ctoff, deftoff, shoff
    s.is_ps = (flags & 1) == 0
    assert (flags & 0xFFFFFF00) == 0x102A1100, hex(flags)
    # ---- CTAB (D3DXSHADER_CONSTANTTABLE, base = ctoff+4)
    s.ctab = []
    if ctoff:
        base = ctoff + 4
        size, creator, version, n, cinfo, cflags, target = struct.unpack_from('>7I', blob, base)
        for k in range(n):
            no, rs, ri, rc, _r, ti, dv = struct.unpack_from('>IHHHHII', blob, base + cinfo + 20 * k)
            ty = None
            if ti:
                pc, pt, rows, cols, el, sm, smi = struct.unpack_from('>6HI', blob, base + ti)
                ty = dict(cls=pc, type=pt, rows=rows, cols=cols, elements=el)
            s.ctab.append(dict(name=_cstr(blob, base + no), set=rs, reg=ri, count=rc, type=ty))
    s.f4 = {}                    # float register -> (ctab entry, index inside entry)
    s.samplers = {}              # sampler register -> ctab entry
    for c in s.ctab:
        if c['set'] == 2:
            for j in range(c['count']): s.f4[c['reg'] + j] = (c, j)
        elif c['set'] == 3:
            s.samplers[c['reg']] = c
    # ---- inline float definitions (def cN)
    s.defs = {}
    if deftoff:
        d = deftoff + 20
        words = lambda o: struct.unpack_from('>I', blob, o)[0]
        while words(d) != 0:
            reg, cnt, phys = struct.unpack_from('>HHI', blob, d)
            vals = struct.unpack_from('>%df' % (4 * ((cnt + 3) // 4)), blob, vsize + phys)
            for i in range((cnt + 3) // 4):
                s.defs[reg + i - (256 if s.is_ps else 0)] = tuple(vals[4 * i:4 * i + 4])
            d += 8
    # ---- Shader struct
    phys, size, f8, fC, f10, interp = struct.unpack_from('>6I', blob, shoff)
    s.size = size; s.svpos_reg = (fC >> 8) & 0xFF; s.ninterp = (interp >> 5) & 0x1F
    s.code = struct.unpack_from('>%dI' % (size // 4), blob, vsize + phys)
    s.interp = []
    if s.is_ps:
        f18, outputs = struct.unpack_from('>2I', blob, shoff + 0x18)
        s.outputs = outputs
        for i in range(s.ninterp):
            v = struct.unpack_from('>I', blob, shoff + 0x20 + 4 * i)[0]
            s.interp.append(dict(usage=(v >> 4) & 15, index=v & 15, reg=(v >> 8) & 15))
    else:
        f18, vcount, f20 = struct.unpack_from('>3I', blob, shoff + 0x18)
        s.outputs = None
        arr = lambda i: struct.unpack_from('>I', blob, shoff + 0x24 + 4 * i)[0]
        s.vtx = []
        for i in range(vcount):
            v = arr(f18 + i); s.vtx.append(dict(address=v & 0xFFF, usage=(v >> 12) & 15, index=(v >> 16) & 15))
        for i in range(s.ninterp):
            v = arr(f18 + vcount + i); s.interp.append(dict(index=v & 15, usage=(v >> 4) & 15, reg=(v >> 8) & 15))
    return s


USAGE = ['Position', 'BlendWeight', 'BlendIndices', 'Normal', 'PointSize', 'TexCoord', 'Tangent', 'Binormal', 'TessFactor',
         'PositionT', 'Color', 'Fog', 'Depth', 'Sample']

# ------------------------------------------------------------------------------------------------ control flow
CF_NAMES = {0: 'nop', 1: 'exec', 2: 'exec_end', 3: 'cond_exec', 4: 'cond_exec_end', 5: 'cond_exec_pred', 6: 'cond_exec_pred_end', 7: 'loop_start',
            8: 'loop_end', 9: 'cond_call', 10: 'return', 11: 'cond_jmp', 12: 'alloc', 13: 'cond_exec_pred_clean', 14: 'cond_exec_pred_clean_end', 15: 'mark_vs_fetch_done'}
EXEC_FAMILY = (1, 2, 3, 4, 5, 6, 13, 14)


def bits(v, lo, n): return (v >> lo) & ((1 << n) - 1)


def decode_cf(code):
    """Returns (list of cf dict in program order, instruction area start in 3-dword units). Same stop rule as XenosRecomp:
    the CF area ends at the lowest exec address."""
    cfs = []
    limit = len(code) // 3
    i = 0
    while i < limit:
        d0, d1, d2 = code[3 * i:3 * i + 3]
        for half in range(2):
            c = (d0 | ((d1 & 0xFFFF) << 32)) if half == 0 else ((d1 >> 16) | (d2 << 16))
            op = bits(c, 44, 4)
            r = dict(k=len(cfs), op=op, name=CF_NAMES[op], raw=c)
            if op in EXEC_FAMILY:
                r.update(addr=bits(c, 0, 12), count=bits(c, 12, 3), yld=bits(c, 15, 1), seq=bits(c, 16, 12))
                if op in (3, 4, 13, 14):          # XenosRecomp reads boolAddress/condition for 13/14 too (Xenia: pred-clean uses the Pred layout)
                    r.update(bool=bits(c, 34, 8), cond=bits(c, 42, 1))
                if op in (5, 6, 13, 14):
                    r.update(pcond=bits(c, 42, 1), clean=bits(c, 41, 1))
                if r['addr'] != 0: limit = min(limit, r['addr'])
            elif op == 7:
                r.update(addr=bits(c, 0, 13), repeat=bits(c, 13, 1), loopid=bits(c, 16, 5))
            elif op == 8:
                r.update(addr=bits(c, 0, 13), loopid=bits(c, 16, 5), pbreak=bits(c, 21, 1), cond=bits(c, 42, 1))
            elif op == 9:
                r.update(addr=bits(c, 0, 13), uncond=bits(c, 13, 1), pred=bits(c, 14, 1), bool=bits(c, 34, 8), cond=bits(c, 42, 1))
            elif op == 11:
                r.update(addr=bits(c, 0, 13), uncond=bits(c, 13, 1), pred=bits(c, 14, 1), direction=bits(c, 33, 1), bool=bits(c, 34, 8), cond=bits(c, 42, 1))
            elif op == 12:
                r.update(size=bits(c, 0, 3), alloc_type=bits(c, 41, 2))
            cfs.append(r)
        i += 1
    return cfs, limit


# ------------------------------------------------------------------------------------------------ ALU decode
VOP = ['add', 'mul', 'max', 'min', 'seq', 'sgt', 'sge', 'sne', 'frc', 'trunc', 'floor', 'mad', 'cndeq', 'cndge', 'cndgt', 'dp4', 'dp3', 'dp2add',
       'cube', 'max4', 'setp_eq_push', 'setp_ne_push', 'setp_gt_push', 'setp_ge_push', 'kill_eq', 'kill_gt', 'kill_ge', 'kill_ne', 'dst', 'maxa']
SOP = {0: 'adds', 1: 'adds_prev', 2: 'muls', 3: 'muls_prev', 4: 'muls_prev2', 5: 'maxs', 6: 'mins', 7: 'seqs', 8: 'sgts', 9: 'sges', 10: 'snes',
       11: 'frcs', 12: 'truncs', 13: 'floors', 14: 'exp', 15: 'logc', 16: 'log', 17: 'rcpc', 18: 'rcpf', 19: 'rcp', 20: 'rsqc', 21: 'rsqf', 22: 'rsq',
       23: 'maxas', 24: 'maxasf', 25: 'subs', 26: 'subs_prev', 27: 'setp_eq', 28: 'setp_ne', 29: 'setp_gt', 30: 'setp_ge', 31: 'setp_inv', 32: 'setp_pop',
       33: 'setp_clr', 34: 'setp_rstr', 35: 'kills_eq', 36: 'kills_gt', 37: 'kills_ge', 38: 'kills_ne', 39: 'kills_one', 40: 'sqrt', 42: 'mulsc0',
       43: 'mulsc1', 44: 'addsc0', 45: 'addsc1', 46: 'subsc0', 47: 'subsc1', 48: 'sin', 49: 'cos', 50: 'retain_prev'}


def alu_decode(d0, d1, d2):
    f = dict(vdest=bits(d0, 0, 6), vdest_rel=bits(d0, 6, 1), absc=bits(d0, 7, 1), sdest=bits(d0, 8, 6), sdest_rel=bits(d0, 14, 1), export=bits(d0, 15, 1),
             vmask=bits(d0, 16, 4), smask=bits(d0, 20, 4), vsat=bits(d0, 24, 1), ssat=bits(d0, 25, 1), sopc=bits(d0, 26, 6),
             sw3=bits(d1, 0, 8), sw2=bits(d1, 8, 8), sw1=bits(d1, 16, 8), neg3=bits(d1, 24, 1), neg2=bits(d1, 25, 1), neg1=bits(d1, 26, 1),
             predc=bits(d1, 27, 1), ispred=bits(d1, 28, 1), addr_a0=bits(d1, 29, 1), c1rel=bits(d1, 30, 1), c0rel=bits(d1, 31, 1),
             reg3=bits(d2, 0, 8), reg2=bits(d2, 8, 8), reg1=bits(d2, 16, 8), vopc=bits(d2, 24, 5), sel3=bits(d2, 29, 1), sel2=bits(d2, 30, 1), sel1=bits(d2, 31, 1))
    return f


def comp(sw, lane): return ((sw >> (2 * lane)) + lane) & 3


class Opnd:
    """One decoded ALU operand. kind 'r' (temp) or 'c' (float constant). lanes: output lane -> source component."""
    __slots__ = ('kind', 'reg', 'neg', 'abs', 'rel', 'swz', 'which')

    def lanecomp(self, lane):
        if self.which in ('v0', 'v1', 'v2'): return comp(self.swz, lane)
        if self.which in ('s0', 'sc0'): return (((self.swz >> 6) + 3) & 3)
        return self.swz & 3


def operand(f, which):
    o = Opnd(); o.which = which
    if which == 'sc0':
        o.reg, o.swz, o.kind, o.neg, o.abs = f['reg3'], f['sw3'], 'c', f['neg3'], f['absc']
    elif which == 'sc1':
        o.reg = (f['sopc'] & 1) | (f['sel3'] << 1) | (f['sw3'] & 0x3C); o.swz = f['sw3']; o.kind = 'r'; o.neg = f['neg3']; o.abs = f['absc']
    else:
        k = {'v0': 1, 'v1': 2, 'v2': 3, 's0': 3, 's1': 3}[which]
        reg, swz, sel, neg = f['reg%d' % k], f['sw%d' % k], f['sel%d' % k], f['neg%d' % k]
        o.swz, o.neg = swz, neg
        if sel: o.kind, o.abs, o.reg = 'r', (reg & 0x80) != 0, reg & 0x3F
        else: o.kind, o.abs, o.reg = 'c', f['absc'], reg
    o.rel = None
    if o.kind == 'c':
        # const0Relative applies to... XenosRecomp uses const0Relative for every constant operand; keep that.
        if f['c0rel']: o.rel = 'a0' if f['addr_a0'] else 'aL'
    return o


def vmask_for(f):
    v = f['vopc']
    if v == 17: return None            # dp2add: v0,v1 -> xy, v2 -> x
    if v == 16: return 0b111
    if v in (15, 19, 18): return 0b1111
    return f['vmask'] if f['vmask'] else 1


def v_lanes(f, which):
    v = f['vopc']
    if v == 17: return [0] if which == 'v2' else [0, 1]
    m = vmask_for(f)
    return [i for i in range(4) if (m >> i) & 1]


# ------------------------------------------------------------------------------------------------ text back-end
class Text:
    def __init__(self, sh, style='compat'):
        self.sh = sh; self.style = style; self.lines = []; self.ind = 1; self.uses = collections.defaultdict(set); self.samp_uses = collections.Counter()
        self.unsup = collections.Counter()

    def emit(self, s): self.lines.append('\t' * self.ind + s)

    def cname(self, o, comps_txt):
        sh = self.sh
        if o.kind == 'r': return 'r%d' % o.reg
        e = sh.f4.get(o.reg)
        if e is None:
            return 'c%d' % o.reg
        c, j = e
        if c['count'] > 1:
            return '%s(%d%s)' % (c['name'], j, (' + a0' if o.rel == 'a0' else ' + aL') if o.rel else '') if self.style == 'compat' else '%s[%d%s]' % (c['name'], j, (' + a0' if o.rel == 'a0' else ' + aL') if o.rel else '')
        return c['name']

    def op(self, f, which):
        o = operand(f, which)
        if which in ('v0', 'v1', 'v2'):
            lanes = v_lanes(f, which)
            comps = [comp(o.swz, l) for l in lanes]
        else:
            comps = [o.lanecomp(0)]
        if o.kind == 'c': self.uses[o.reg].update(comps)
        s = ''
        if o.neg: s += '-'
        if o.abs: s += 'abs('
        s += self.cname(o, '') + '.' + ''.join(SWZ[c] for c in comps)
        if o.abs: s += ')'
        return s

    def alu(self, f):
        sh = self.sh
        if f['ispred']:
            self.emit('if (%sp0)' % ('' if f['predc'] else '!')); self.emit('{'); self.ind += 1
        op = lambda w: self.op(f, w)
        v = VOP[f['vopc']]
        if v.startswith('kill_'):
            sym = {'kill_eq': '==', 'kill_gt': '>', 'kill_ge': '>=', 'kill_ne': '!='}[v]
            self.emit('clip(any(%s %s %s) ? -1 : 1);' % (op('v0'), sym, op('v1')))
        exp = ''
        if f['export']:
            if sh.is_ps:
                exp = {0: 'oC0', 1: 'oC1', 2: 'oC2', 3: 'oC3', 61: 'oDepth'}.get(f['vdest'], 'oX%d' % f['vdest'])
            else:
                exp = 'oPos' if f['vdest'] == 62 else 'oI%d' % f['vdest']
        if v.startswith('setp_'):
            sym = {'setp_eq': '==', 'setp_ne': '!=', 'setp_gt': '>', 'setp_ge': '>='}[v[:-5]]
            self.emit('p0 = %s == 0.0 && %s %s 0.0;' % (op('v0'), op('v1'), sym))
        elif v == 'maxa':
            self.emit('a0 = (int)clamp(floor((%s).w + 0.5), -256.0, 255.0);' % op('v0'))
        vm = f['vmask']
        if f['export']: vm &= ~f['smask']

        def vec():
            if not vm: return
            dst = (exp if exp else 'r%d' % f['vdest']) + '.' + ''.join(SWZ[i] for i in range(4) if (vm >> i) & 1)
            sat = f['vsat']
            if v == 'add': e = '%s + %s' % (op('v0'), op('v1'))
            elif v == 'mul': e = '%s * %s' % (op('v0'), op('v1'))
            elif v in ('max', 'maxa'): e = 'max(%s, %s)' % (op('v0'), op('v1'))
            elif v == 'min': e = 'min(%s, %s)' % (op('v0'), op('v1'))
            elif v in ('seq', 'sgt', 'sge', 'sne'):
                e = '%s %s %s' % (op('v0'), {'seq': '==', 'sgt': '>', 'sge': '>=', 'sne': '!='}[v], op('v1'))
            elif v == 'frc': e = 'frac(%s)' % op('v0')
            elif v == 'trunc': e = 'trunc(%s)' % op('v0')
            elif v == 'floor': e = 'floor(%s)' % op('v0')
            elif v == 'mad': e = '%s * %s + %s' % (op('v0'), op('v1'), op('v2'))
            elif v in ('cndeq', 'cndge', 'cndgt'):
                e = 'select(%s %s 0.0, %s, %s)' % (op('v0'), {'cndeq': '==', 'cndge': '>=', 'cndgt': '>'}[v], op('v1'), op('v2'))
            elif v in ('dp4', 'dp3'): e = 'dot(%s, %s)' % (op('v0'), op('v1'))
            elif v == 'dp2add': e = 'dot(%s, %s) + %s' % (op('v0'), op('v1'), op('v2'))
            elif v == 'cube': e = 'cube(float4((%s).zwx, 0.0), cubeMapData)' % op('v0')
            elif v == 'max4': e = 'max4(%s)' % op('v0')
            elif v.startswith('setp_'): e = 'p0 ? 0.0 : %s + 1.0' % op('v0')
            elif v.startswith('kill_'):
                e = 'any(%s %s %s)' % (op('v0'), {'kill_eq': '==', 'kill_gt': '>', 'kill_ge': '>=', 'kill_ne': '!='}[v], op('v1'))
            elif v == 'dst': e = 'dst(%s, %s)' % (op('v0'), op('v1'))
            else: e = '?'
            if sat: e = 'saturate(%s)' % e
            self.emit('%s = %s;' % (dst, e))

        sopn = SOP.get(f['sopc'], '?')

        def sca():
            if f['sopc'] == 50: return
            sc = sopn
            if sc.startswith('setp_') and sc != 'setp_pop' or sc in ('setp_pop',):
                if sc == 'setp_eq': self.emit('p0 = %s == 0.0;' % op('s0'))
                elif sc == 'setp_ne': self.emit('p0 = %s != 0.0;' % op('s0'))
                elif sc == 'setp_gt': self.emit('p0 = %s > 0.0;' % op('s0'))
                elif sc == 'setp_ge': self.emit('p0 = %s >= 0.0;' % op('s0'))
                elif sc == 'setp_inv': self.emit('p0 = %s == 1.0;' % op('s0'))
                elif sc == 'setp_pop': self.emit('p0 = %s - 1.0 <= 0.0;' % op('s0'))
                elif sc == 'setp_clr': self.emit('p0 = false;')
                elif sc == 'setp_rstr': self.emit('p0 = %s == 0.0;' % op('s0'))
            if sc == 'adds': e = '%s + %s' % (op('s0'), op('s1'))
            elif sc == 'adds_prev': e = '%s + ps' % op('s0')
            elif sc == 'muls': e = '%s * %s' % (op('s0'), op('s1'))
            elif sc in ('muls_prev', 'muls_prev2'): e = '%s * ps' % op('s0')
            elif sc in ('maxs', 'maxas', 'maxasf'): e = 'max(%s, %s)' % (op('s0'), op('s1'))
            elif sc == 'mins': e = 'min(%s, %s)' % (op('s0'), op('s1'))
            elif sc == 'seqs': e = '%s == 0.0' % op('s0')
            elif sc == 'sgts': e = '%s > 0.0' % op('s0')
            elif sc == 'sges': e = '%s >= 0.0' % op('s0')
            elif sc == 'snes': e = '%s != 0.0' % op('s0')
            elif sc == 'frcs': e = 'frac(%s)' % op('s0')
            elif sc == 'truncs': e = 'trunc(%s)' % op('s0')
            elif sc == 'floors': e = 'floor(%s)' % op('s0')
            elif sc == 'exp': e = 'exp2(%s)' % op('s0')
            elif sc in ('logc', 'log'): e = 'clamp(log2(%s), FLT_MIN, FLT_MAX)' % op('s0')
            elif sc in ('rcpc', 'rcpf', 'rcp'): e = 'clamp(rcp(%s), FLT_MIN, FLT_MAX)' % op('s0')
            elif sc in ('rsqc', 'rsqf', 'rsq'): e = 'clamp(rsqrt(%s), FLT_MIN, FLT_MAX)' % op('s0')
            elif sc == 'subs': e = '%s - %s' % (op('s0'), op('s1'))
            elif sc == 'subs_prev': e = '%s - ps' % op('s0')
            elif sc in ('setp_eq', 'setp_ne', 'setp_gt', 'setp_ge'): e = 'p0 ? 0.0 : 1.0'
            elif sc == 'setp_inv': e = '%s == 0.0 ? 1.0 : %s' % (op('s0'), op('s0'))
            elif sc == 'setp_pop': e = 'p0 ? 0.0 : (%s - 1.0)' % op('s0')
            elif sc == 'setp_clr': e = 'FLT_MAX'
            elif sc == 'setp_rstr': e = 'p0 ? 0.0 : %s' % op('s0')
            elif sc == 'kills_eq': e = '%s == 0.0' % op('s0')
            elif sc == 'kills_gt': e = '%s > 0.0' % op('s0')
            elif sc == 'kills_ge': e = '%s >= 0.0' % op('s0')
            elif sc == 'kills_ne': e = '%s != 0.0' % op('s0')
            elif sc == 'kills_one': e = '%s == 1.0' % op('s0')
            elif sc == 'sqrt': e = 'sqrt(%s)' % op('s0')
            elif sc in ('mulsc0', 'mulsc1'): e = '%s * %s' % (op('sc0'), op('sc1'))
            elif sc in ('addsc0', 'addsc1'): e = '%s + %s' % (op('sc0'), op('sc1'))
            elif sc in ('subsc0', 'subsc1'): e = '%s - %s' % (op('sc0'), op('sc1'))
            elif sc == 'sin': e = 'sin(%s)' % op('s0')
            elif sc == 'cos': e = 'cos(%s)' % op('s0')
            else: e = '?'; self.unsup['sop ' + sc] += 1
            if f['ssat']: e = 'saturate(%s)' % e
            self.emit('ps = %s;' % e)
            if sc == 'maxas': self.emit('a0 = (int)clamp(floor(%s + 0.5), -256.0, 255.0);' % op('s0'))
            elif sc == 'maxasf': self.emit('a0 = (int)clamp(floor(%s), -256.0, 255.0);' % op('s0'))

        vws = v.startswith('setp_') or v == 'maxa'
        sws = 27 <= f['sopc'] <= 34 or f['sopc'] in (23, 24)
        if vws or sws: vec(); sca()
        else: sca(); vec()
        sm = f['smask']
        if f['export']: sm &= ~f['vmask']
        if sm:
            dst = (exp if exp else 'r%d' % f['sdest']) + '.' + ''.join(SWZ[i] for i in range(4) if (sm >> i) & 1)
            self.emit('%s = ps;' % dst)
        if f['export']:
            zero = (0b1111 & ~(f['vmask'] | f['smask'])) if f['sdest_rel'] else 0
            one = f['vmask'] & f['smask']
            for i in range(4):
                if zero & (1 << i): self.emit('%s.%s = 0.0;' % (exp, SWZ[i]))
                elif one & (1 << i): self.emit('%s.%s = 1.0;' % (exp, SWZ[i]))
        if 35 <= f['sopc'] <= 39: self.emit('clip(ps != 0.0 ? -1 : 1);')
        if f['ispred']:
            self.ind -= 1; self.emit('}')

    def fetch(self, d0, d1, d2, slot):
        sh = self.sh
        opc = bits(d0, 0, 5)
        if opc == 0:
            self.unsup['vfetch in PS'] += 1; return
        if opc not in (1, 19):
            self.unsup['fetch opcode %d' % opc] += 1
            self.emit('// UNSUPPORTED fetch opcode %d (dropped by XenosRecomp too): %08x %08x %08x' % (opc, d0, d1, d2)); return
        src, dst, cidx = bits(d0, 5, 6), bits(d0, 12, 6), bits(d0, 20, 5)
        denorm, sw = bits(d0, 25, 1), bits(d0, 26, 6)
        dsw = bits(d1, 0, 12)
        pred = bits(d1, 31, 1)
        dim = bits(d2, 14, 2)
        offx = bits(d2, 16, 5); offy = bits(d2, 21, 5)
        sg = lambda v, n: v - (1 << n) if v >> (n - 1) else v
        offx, offy = sg(offx, 5), sg(offy, 5)
        pcond = bits(d2, 31, 1)
        c = sh.samplers.get(cidx)
        name = c['name'] if c else 's%d' % cidx
        self.samp_uses[(cidx, name, ('1D', '2D', '3D', 'Cube')[dim])] += 1
        self.emit('// TFETCH slot=%d mag=%d min=%d mip=%d aniso=%d computedLod=%d registerLod=%d sampleLocation=%d' % (
            cidx, bits(d1, 12, 2), bits(d1, 14, 2), bits(d1, 16, 2), bits(d1, 18, 3), bits(d1, 28, 1), bits(d1, 29, 1), bits(d2, 1, 1)))
        if pred:
            self.emit('if (%sp0)' % ('' if pcond else '!')); self.emit('{'); self.ind += 1
        dsws = [(dsw >> (3 * i)) & 7 for i in range(4)]
        dl = ''.join(SWZ[i] for i in range(4) if dsws[i] <= 3)
        dr = ''.join(SWZ[dsws[i]] for i in range(4) if dsws[i] <= 3)
        dimn = ('1D', '2D', '3D', 'Cube')[dim]; nc = (1, 2, 3, 3)[dim]
        fn = 'tfetch' if opc == 1 else 'getWeights'
        extra = ''
        if dim == 1: extra = ', float2(%g, %g)' % (offx * 0.5, offy * 0.5)
        elif dim == 3: extra = ', cubeMapData'
        den = 'Denorm' if denorm and dim == 1 and opc == 1 else ''
        self.emit('r%d.%s = %s%s%s(%s_Texture%sDescriptorIndex, %s_SamplerDescriptorIndex, r%d.%s%s).%s;' % (
            dst, dl, fn, dimn, den, name, dimn, name, src, ''.join(SWZ[(sw >> (2 * i)) & 3] for i in range(nc)), extra, dr))
        for i in range(4):
            if dsws[i] == 4: self.emit('r%d.%s = 0.0;' % (dst, SWZ[i]))
            elif dsws[i] == 5: self.emit('r%d.%s = 1.0;' % (dst, SWZ[i]))
        if pred:
            self.ind -= 1; self.emit('}')


def walk(sh):
    """Yield events in program order: ('cf', rec, closing_info), ('alu', slot, f, raw), ('fetch', slot, d0, d1, d2) -- the same
    traversal as XenosRecomp (CF slots in order; exec clauses run `count` instructions from `addr`, kind per `seq` bit pairs)."""
    cfs, limit = decode_cf(sh.code)
    out = []
    for r in cfs:
        if r['k'] * 3 // 2 >= limit * 2 and False: break
        out.append(('cf', r))
        if r['op'] in EXEC_FAMILY:
            seq = r['seq']
            for i in range(r['count']):
                s = r['addr'] + i
                if 3 * s + 3 > len(sh.code): continue
                d0, d1, d2 = sh.code[3 * s:3 * s + 3]
                if seq & 1: out.append(('fetch', s, d0, d1, d2))
                else: out.append(('alu', s, alu_decode(d0, d1, d2), (d0, d1, d2)))
                seq >>= 2
    return out


def text(sh, style='compat'):
    """HLSL-like translation. Structured control flow is emitted as XenosRecomp does for the 'simple' case; if the shader has
    unconditional/backward jumps, calls or returns inside, the CF is reported as comments (not structured)."""
    T = Text(sh, style)
    cfs, limit = decode_cf(sh.code)
    # simple control flow check as in XenosRecomp
    simple = True; endl = collections.Counter()
    for r in cfs:
        if r['op'] == 11:
            if r['uncond'] or r['direction']: simple = False
            else: endl[r['addr']] += 1
    pc = 0
    for r in cfs:
        for _ in range(endl.get(pc, 0) if simple else 0):
            T.ind -= 1; T.emit('}')
        pc += 1
        op = r['op']; close = False
        if op in (3, 4, 13, 14):
            T.emit('if (g_Boolean(%d) %s= 0)' % (r['bool'], '!' if r['cond'] else '=')); T.emit('{'); T.ind += 1; close = True
        elif op == 7:
            T.emit('for (aL = 0; aL < i%d.x; aL++)' % r['loopid']); T.emit('{'); T.ind += 1
        elif op == 8:
            T.ind -= 1; T.emit('}')
        elif op == 11:
            if r['uncond']: T.emit('// goto %d (unconditional jump: non-structured control flow)' % r['addr'])
            else:
                cond = ('%sp0' % ('' if r['cond'] ^ simple else '!')) if r['pred'] else 'g_Boolean(%d) %s= 0' % (r['bool'], '!' if r['cond'] ^ simple else '=')
                T.emit('if (%s)' % cond); T.emit('{'); T.ind += 1
        elif op == 9:
            T.emit('// call %d (bool %d)' % (r['addr'], r.get('bool', 0)))
        elif op in (10, 12, 0, 15):
            if op != 0: T.emit('// cf %s' % r['name'])
        if op in EXEC_FAMILY:
            seq = r['seq']
            for i in range(r['count']):
                s = r['addr'] + i
                if 3 * s + 3 > len(sh.code): continue
                d0, d1, d2 = sh.code[3 * s:3 * s + 3]
                if seq & 1: T.fetch(d0, d1, d2, s)
                else: T.alu(alu_decode(d0, d1, d2))
                seq >>= 2
            if r['op'] in (2, 4, 6, 14):
                T.emit('return;' if simple else 'break;')
            if close:
                T.ind -= 1; T.emit('}')
    return T


# ------------------------------------------------------------------------------------------------ summary
def summary(sh):
    """Features of one shader (for the decoder-comparison tables)."""
    cfs, limit = decode_cf(sh.code)
    feats = collections.Counter()
    for r in cfs:
        if r['op'] != 0: feats['cf:' + r['name']] += 1
    ev = walk(sh)
    for e in ev:
        if e[0] == 'alu':
            f = e[2]
            v = VOP[f['vopc']]; s = SOP.get(f['sopc'], '?')
            if f['vmask'] or v in ('dp4', 'dp3', 'dp2add', 'cube', 'max4') or v.startswith(('setp', 'kill')):
                feats['v:' + v] += 1
            if f['sopc'] != 50: feats['s:' + s] += 1
            if f['ispred']: feats['predicated alu'] += 1
            if f['export']: feats['export alu'] += 1
            for w in ('v0', 'v1', 'v2'):
                pass
            if f['c0rel'] or f['c1rel']: feats['const relative'] += 1
            if f['vdest_rel'] or f['sdest_rel'] and not f['export']: feats['dest relative'] += 1
            if f['sopc'] in (42, 43, 44, 45, 46, 47) and f['sel3']: feats['scalar-const with sel3=1 (xenos_ps misses const ref)'] += 1
            if f['absc']: feats['abs const'] += 1
        elif e[0] == 'fetch':
            _, s, d0, d1, d2 = e
            opc = bits(d0, 0, 5)
            dim = bits(d2, 14, 2)
            feats['fetch op%d' % opc] += 1
            if opc in (1, 19): feats['tfetch dim' + ('1D', '2D', '3D', 'Cube')[dim]] += 1
            if bits(d1, 31, 1): feats['predicated fetch'] += 1
            if bits(d0, 25, 1): feats['tfetch denorm'] += 1
            if bits(d1, 29, 1): feats['tfetch register lod'] += 1
            if bits(d2, 0, 1): feats['tfetch register gradients'] += 1
    return feats


# ================================================================================================ symbolic IR
class IR:
    """Hash-consed expression DAG. node id -> tuple(kind, ...)."""
    def __init__(self):
        self.tab = {}; self.nodes = []

    def mk(self, *key):
        i = self.tab.get(key)
        if i is None:
            i = len(self.nodes); self.tab[key] = i; self.nodes.append(key)
        return i

    def k(self, v):
        v = float(v)
        if v == 0: v = 0.0
        return self.mk('k', round(v, 6))

    def isk(self, n): return self.nodes[n][0] == 'k'
    def kv(self, n): return self.nodes[n][1]

    # n-ary commutative normal forms ---------------------------------------------------------
    def add(self, *xs):
        flat = []
        for x in xs:
            if self.nodes[x][0] == 'add': flat.extend(self.nodes[x][1:])
            else: flat.append(x)
        c = 0.0; rest = []
        for x in flat:
            if self.isk(x): c += self.kv(x)
            else: rest.append(x)
        if c != 0 or not rest: rest.append(self.k(c))
        if len(rest) == 1: return rest[0]
        return self.mk('add', *sorted(rest))

    def mul(self, *xs):
        flat = []
        for x in xs:
            if self.nodes[x][0] == 'mul': flat.extend(self.nodes[x][1:])
            else: flat.append(x)
        c = 1.0; rest = []
        for x in flat:
            if self.isk(x): c *= self.kv(x)
            else: rest.append(x)
        if c == 0: return self.k(0)
        if c != 1 or not rest: rest.append(self.k(c))
        if len(rest) == 1: return rest[0]
        return self.mk('mul', *sorted(rest))

    def neg(self, x): return self.mul(self.k(-1), x)
    def sub(self, a, b): return self.add(a, self.neg(b))

    def op2c(self, name, a, b):          # commutative binary
        if a == b and name in ('max', 'min'): return a        # max(a,a) is the Xenos idiom for MOV
        a, b = sorted((a, b)); return self.mk(name, a, b)

    def op(self, name, *xs): return self.mk(name, *xs)


class IRBuilder:
    """Symbolic execution of a pixel shader (straight line; boolean EXEC clauses are treated as 'taken' or recorded as guards).
    Registers hold per-component node ids. Leaves: ('k',v) literal / inline def; ('P',idx,comp) MaterialParams; ('C',name,idx,comp) any
    other CTAB constant; ('V',usage,index,comp) interpolator; ('U',reg,comp) uninitialised temp; ('T',cidx,dim,flags,coords..) fetch,
    ('TC',T,comp)."""

    def __init__(self, sh, param_name='MaterialParams', bool_policy='record'):
        self.sh = sh; self.ir = IR(); self.param_name = param_name
        self.reg = {}; self.ps = None; self.p0 = None; self.exports = collections.OrderedDict(); self.kills = []
        self.guard = []          # active cond-exec guards (bool idx, expect) -- recorded, values are NOT conditioned on them
        self.notes = collections.Counter(); self.fetches = []
        ir = self.ir
        self.ps = ir.k(0)
        for i in sh.interp:
            for c in range(4):
                self.reg[(i['reg'], c)] = ir.mk('V', i['usage'], i['index'], c)
        self.p0 = ir.k(0)

    def r(self, reg, c):
        v = self.reg.get((reg, c))
        if v is None: v = self.ir.mk('U', reg, c)
        return v

    def const(self, o, c):
        ir = self.ir; sh = self.sh
        e = sh.f4.get(o.reg)
        if o.rel: self.notes['relative const'] += 1
        if e is not None:
            ent, j = e
            if ent['name'] == self.param_name:
                n = ir.mk('P', j, c)
            else:
                n = ir.mk('C', ent['name'], j, c)
        elif o.reg in sh.defs:
            n = ir.k(sh.defs[o.reg][c])
        else:
            n = ir.mk('C', None, o.reg, c)
        return n

    def val(self, o, lane_or_comp, scalar=False):
        c = o.lanecomp(lane_or_comp) if not scalar else o.lanecomp(0)
        n = self.r(o.reg, c) if o.kind == 'r' else self.const(o, c)
        ir = self.ir
        if o.abs: n = ir.op('abs', n)
        if o.neg: n = ir.neg(n)
        return n

    def write(self, dst, mask, vals, export, pred):
        for l in range(4):
            if (mask >> l) & 1:
                v = vals[l]
                old = (self.exports.get((dst, l)) if export else self.reg.get((dst, l)))
                if pred is not None:
                    if old is None: old = self.ir.mk('U', dst, l)
                    v = self.ir.op('psel', pred[0], pred[1], v, old)
                for gn, gf in reversed(self.guard):          # boolean EXEC / forward-jump regions: value merges with the previous one (phi)
                    if old is None: old = self.ir.mk('U', dst, l)
                    v = self.ir.op('psel', gn, gf, v, old)
                if export: self.exports[(dst, l)] = v
                else: self.reg[(dst, l)] = v

    def alu(self, f):
        ir = self.ir; sh = self.sh
        pred = (self.p0, f['predc']) if f['ispred'] else None
        if pred: pred = (ir.op('p', self.p0), ir.k(f['predc']))
        v = VOP[f['vopc']]
        vo = lambda w: operand(f, w)
        lv = lambda w, lane: self.val(operand(f, w), lane)
        vm = f['vmask']; sm = f['smask']
        if f['export']: vm &= ~sm
        expn = f['vdest'] if f['export'] else None
        vals = {}
        sat = lambda x: ir.op('sat', x) if f['vsat'] else x
        ssat = lambda x: ir.op('sat', x) if f['ssat'] else x
        # scalar first unless state-writing (same order as XenosRecomp)
        sc = SOP.get(f['sopc'], '?')
        vws = v.startswith('setp_') or v == 'maxa'
        sws = 27 <= f['sopc'] <= 34 or f['sopc'] in (23, 24)
        new_ps = None
        s0 = lambda: self.val(operand(f, 's0'), 0, True)
        s1 = lambda: self.val(operand(f, 's1'), 0, True)
        c0 = lambda: self.val(operand(f, 'sc0'), 0, True)
        c1 = lambda: self.val(operand(f, 'sc1'), 0, True)

        def do_vec():
            if v.startswith('kill_'):
                a = [lv('v0', l) for l in range(4)]; b = [lv('v1', l) for l in range(4)]
                cmp_ = {'kill_eq': 'eq', 'kill_gt': 'gt', 'kill_ge': 'ge', 'kill_ne': 'ne'}[v]
                self.kills.append(ir.op('anyk_' + cmp_, *a, *b))
            if v.startswith('setp_'):
                a = lv('v0', 0); b = lv('v1', 0)
                self.p0 = ir.op('setp_' + v[5:-5], a, b)   # p0 = (a == 0 && b cmp 0)
            elif v == 'maxa':
                self.notes['a0 write'] += 1
            for l in range(4):
                if not (vm >> l) & 1: continue
                if v == 'add': x = ir.add(lv('v0', l), lv('v1', l))
                elif v == 'mul': x = ir.mul(lv('v0', l), lv('v1', l))
                elif v in ('max', 'maxa'): x = ir.op2c('max', lv('v0', l), lv('v1', l))
                elif v == 'min': x = ir.op2c('min', lv('v0', l), lv('v1', l))
                elif v in ('seq', 'sne'): x = ir.op2c(v, lv('v0', l), lv('v1', l))
                elif v in ('sgt', 'sge'): x = ir.op(v, lv('v0', l), lv('v1', l))
                elif v in ('frc', 'trunc', 'floor'): x = ir.op(v, lv('v0', l))
                elif v == 'mad': x = ir.add(ir.mul(lv('v0', l), lv('v1', l)), lv('v2', l))
                elif v in ('cndeq', 'cndge', 'cndgt'): x = ir.op(v, lv('v0', l), lv('v1', l), lv('v2', l))
                elif v in ('dp4', 'dp3'):
                    n = 4 if v == 'dp4' else 3
                    x = ir.add(*[ir.mul(lv('v0', i), lv('v1', i)) for i in range(n)])
                elif v == 'dp2add':
                    # operands read lanes 0,1 of v0/v1 and lane 0 of v2 (swizzle lane 0)
                    x = ir.add(ir.mul(lv('v0', 0), lv('v1', 0)), ir.mul(lv('v0', 1), lv('v1', 1)), lv('v2', 0))
                elif v == 'cube':
                    # CUBE: opaque node of the 3 direction components src.zwx as XenosRecomp does (cube(float4(op.zwx,0)))
                    o0 = operand(f, 'v0'); d = [self.val(o0, 2), self.val(o0, 3), self.val(o0, 0)]
                    x = ir.op('cube', *d, ir.k(l))
                elif v == 'max4': x = ir.op('max4', *[lv('v0', i) for i in range(4)])
                elif v.startswith('setp_'): x = ir.op('setp_push', self.p0, lv('v0', l))
                elif v.startswith('kill_'): x = ir.op('killres', lv('v0', l), lv('v1', l))
                elif v == 'dst': x = ir.op('dst', l, lv('v0', l), lv('v1', l)) if False else ir.op('dst%d' % l, lv('v0', l), lv('v1', l))
                else: x = ir.op('unk_' + v)
                vals[l] = sat(x)

        def do_sca():
            nonlocal new_ps
            if f['sopc'] == 50: return
            if sc == 'adds': x = ir.add(s0(), s1())
            elif sc == 'adds_prev': x = ir.add(s0(), self.ps)
            elif sc == 'muls': x = ir.mul(s0(), s1())
            elif sc in ('muls_prev', 'muls_prev2'): x = ir.mul(s0(), self.ps)
            elif sc in ('maxs', 'maxas', 'maxasf'): x = ir.op2c('max', s0(), s1())
            elif sc == 'mins': x = ir.op2c('min', s0(), s1())
            elif sc in ('seqs', 'sgts', 'sges', 'snes', 'frcs', 'truncs', 'floors', 'exp', 'logc', 'log', 'rcpc', 'rcpf', 'rcp', 'rsqc', 'rsqf', 'rsq', 'sqrt', 'sin', 'cos'):
                nm = {'logc': 'log', 'rcpc': 'rcp', 'rcpf': 'rcp', 'rsqc': 'rsq', 'rsqf': 'rsq'}.get(sc, sc)
                x = ir.op(nm, s0())
            elif sc == 'subs': x = ir.sub(s0(), s1())
            elif sc == 'subs_prev': x = ir.sub(s0(), self.ps)
            elif sc.startswith('setp_'):
                a = s0() if sc != 'setp_clr' else ir.k(0)
                self.p0 = ir.op(sc, a); x = ir.op('setp_ps', self.p0, a)
            elif sc.startswith('kills_'):
                x = ir.op(sc, s0()); self.kills.append(x)
            elif sc in ('mulsc0', 'mulsc1'): x = ir.mul(c0(), c1())
            elif sc in ('addsc0', 'addsc1'): x = ir.add(c0(), c1())
            elif sc in ('subsc0', 'subsc1'): x = ir.sub(c0(), c1())
            else: x = ir.op('unk_' + sc)
            new_ps = ssat(x)
            if sc in ('maxas', 'maxasf'): self.notes['a0 write'] += 1

        if vws or sws: do_vec(); do_sca()
        else: do_sca(); do_vec()
        if vm and vals: self.write(expn if f['export'] else f['vdest'], vm, vals, f['export'], pred)
        if new_ps is not None:
            nv = new_ps if pred is None else ir.op('psel', pred[0], pred[1], new_ps, self.ps)
            for gn, gf in reversed(self.guard): nv = ir.op('psel', gn, gf, nv, self.ps)
            self.ps = nv
        if sm:
            self.write(expn if f['export'] else f['sdest'], sm if not f['export'] else sm & ~f['vmask'], {l: self.ps for l in range(4)}, f['export'], pred)

        if f['export']:
            one = f['vmask'] & f['smask']; zero = (0b1111 & ~(f['vmask'] | f['smask'])) if f['sdest_rel'] else 0
            for i in range(4):
                if zero & (1 << i): self.exports[(expn, i)] = ir.k(0)
                elif one & (1 << i): self.exports[(expn, i)] = ir.k(1)

    def fetch(self, d0, d1, d2):
        ir = self.ir
        opc = bits(d0, 0, 5)
        if opc not in (1, 19):
            self.notes['fetch op%d dropped' % opc] += 1; return
        src, dst, cidx = bits(d0, 5, 6), bits(d0, 12, 6), bits(d0, 20, 5)
        sw = bits(d0, 26, 6); dsw = bits(d1, 0, 12); dim = bits(d2, 14, 2)
        nc = (1, 2, 3, 3)[dim]
        coords = [self.r(src, (sw >> (2 * i)) & 3) for i in range(nc)]
        sg = lambda v, n: v - (1 << n) if v >> (n - 1) else v
        flags = (opc, bits(d0, 25, 1), sg(bits(d2, 16, 5), 5), sg(bits(d2, 21, 5), 5), bits(d1, 29, 1), bits(d1, 28, 1), bits(d2, 0, 1))
        t = ir.mk('T', cidx, dim, flags, *coords)
        self.fetches.append((cidx, dim, t))
        pred = None
        if bits(d1, 31, 1): pred = (ir.op('p', self.p0), ir.k(bits(d2, 31, 1)))
        for i in range(4):
            s = (dsw >> (3 * i)) & 7
            if s <= 3: v = ir.mk('TC', t, s)
            elif s == 4: v = ir.k(0)
            elif s == 5: v = ir.k(1)
            else: continue
            self.write(dst, 1 << i, {i: v}, False, pred)

    def run(self):
        """Structured control flow is modelled as in XenosRecomp's 'simple' case: a boolean EXEC clause guards its own instructions; a forward
        cond_jmp opens a region closed at the CF slot it targets; both merge written values with the previous value (psel = phi).
        Unconditional / backward jumps, calls and loops are only COUNTED (notes), not modelled."""
        sh = self.sh; ir = self.ir
        regions = []                    # end cf index for forward-jump regions (their guard sits in self.guard)
        exec_guard = False
        for e in walk(sh):
            if e[0] == 'cf':
                r = e[1]; k = r['k']
                if exec_guard: self.guard.pop(); exec_guard = False
                while regions and regions[-1] <= k:
                    regions.pop(); self.guard.pop()
                if r['op'] in (3, 4, 13, 14):
                    self.notes['cond_exec(bool)'] += 1
                    self.guard.append((ir.mk('B', r['bool']), ir.k(r['cond']))); exec_guard = True
                elif r['op'] == 11:
                    self.notes['cf cond_jmp'] += 1
                    if r['uncond'] or r['direction']: self.notes['NON-STRUCTURED CF'] += 1
                    else:
                        gn = ir.op('p', self.p0) if r['pred'] else ir.mk('B', r['bool'])
                        self.guard.append((gn, ir.k(1 - r['cond']))); regions.append(r['addr'])
                elif r['op'] in (7, 8, 9, 10):
                    self.notes['cf ' + r['name']] += 1
            elif e[0] == 'alu': self.alu(e[2])
            else: self.fetch(e[2], e[3], e[4])
        return self.exports


# ------------------------------------------------------------------------------------------------ printing of IR
def ir_str(ir, n, depth=0, maxd=6):
    nd = ir.nodes[n]; k = nd[0]
    if k == 'k': return '%g' % nd[1]
    if k == 'P': return 'P%d.%s' % (nd[1], SWZ[nd[2]])
    if k == 'C': return '%s[%s].%s' % (nd[1], nd[2], SWZ[nd[3]])
    if k == 'V': return '%s%d.%s' % (USAGE[nd[1]], nd[2], SWZ[nd[3]])
    if k == 'U': return 'undef_r%d.%s' % (nd[1], SWZ[nd[2]])
    if k == 'B': return 'bool%d' % nd[1]
    if k == 'T': return 'tex%s#%d(%s)' % (('1D', '2D', '3D', 'Cube')[nd[2]], nd[1], ','.join(ir_str(ir, c, depth + 1, maxd) for c in nd[4:]))
    if k == 'TC': return '%s.%s' % (ir_str(ir, nd[1], depth + 1, maxd), SWZ[nd[2]])
    if depth >= maxd: return '..'
    sym = {'add': ' + ', 'mul': ' * '}.get(k)
    if sym: return '(' + sym.join(ir_str(ir, c, depth + 1, maxd) for c in nd[1:]) + ')'
    return '%s(%s)' % (k, ', '.join(ir_str(ir, c, depth + 1, maxd) if isinstance(c, int) else str(c) for c in nd[1:]))


# ------------------------------------------------------------------------------------------------ CLI
def load_libs():
    import pickle
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    return pickle.load(open(os.path.join(ROOT, 'work', 'render', 'shaderlibs.pkl'), 'rb'))


def lib_blob(L, lid, slot=None):
    lib = L['D'].get(lid) or L['X'].get(lid)
    ss = [s for s in lib['slots'] if s != 0xffffffff]
    s = ss[0] if slot is None else lib['slots'][slot]
    return lib['entries'][s]['blob']


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'show':
        L = load_libs(); lid = int(sys.argv[2]); slot = int(sys.argv[3]) if len(sys.argv) > 3 else None
        sh = parse(lib_blob(L, lid, slot))
        print('// ps' if sh.is_ps else '// vs', 'ctab', [(c['name'], c['set'], c['reg'], c['count']) for c in sh.ctab])
        print('// interp', sh.interp, 'outputs', sh.outputs, 'defs', sh.defs)
        T = text(sh, 'pretty')
        print('\n'.join(T.lines))
        print('// summary', dict(summary(sh)))
