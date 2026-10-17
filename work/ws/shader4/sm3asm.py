"""sm3asm.py - assemblatore D3D9 Shader Model 2/3 (ps_3_0 / vs_3_0) senza fxc.

Modello (lossless): Program(kind 'ps'|'vs', major, minor, items) con items =
  Instr(op, ctrl, pred, ops[Operand...], imm[u32...])   istruzione (dcl/def/defi/defb incluse)
  Comment(payload bytes)                                  blocco commento 0xFFFE (CTAB compreso) verbatim
  fine = token 0x0000FFFF implicito.
encode(Program) -> bytes ; parse_text(str) -> Program ; assemble(str) -> bytes.
Il testo e' quello del disassemblatore sm3dis.py (stile D3D, vedi format_program).
Token documentati (d3d9types.h): istruzione = op[0:15] | ctrl[16:23] | len[24:27] | pred[28]; param = num[0:10] | tipo-alto[11:12]
| rel[13] | riservati[14:15] | mask/swizzle[16:23] | mod[20:23 dst, 24:27 src] | shift[24:27 dst] | tipo-basso[28:30] | 1<<31."""
import struct, re

OPS = {0: 'nop', 1: 'mov', 2: 'add', 3: 'sub', 4: 'mad', 5: 'mul', 6: 'rcp', 7: 'rsq', 8: 'dp3', 9: 'dp4', 10: 'min', 11: 'max',
       12: 'slt', 13: 'sge', 14: 'exp', 15: 'log', 16: 'lit', 17: 'dst', 18: 'lrp', 19: 'frc', 20: 'm4x4', 21: 'm4x3', 22: 'm3x4',
       23: 'm3x3', 24: 'm3x2', 25: 'call', 26: 'callnz', 27: 'loop', 28: 'ret', 29: 'endloop', 30: 'label', 31: 'dcl', 32: 'pow',
       33: 'crs', 34: 'sgn', 35: 'abs', 36: 'nrm', 37: 'sincos', 38: 'rep', 39: 'endrep', 40: 'if', 41: 'ifc', 42: 'else',
       43: 'endif', 44: 'break', 45: 'breakc', 46: 'mova', 47: 'defb', 48: 'defi', 64: 'texcoord', 65: 'texkill', 66: 'texld',
       81: 'def', 88: 'cmp', 89: 'bem', 90: 'dp2add', 91: 'dsx', 92: 'dsy', 93: 'texldd', 94: 'setp', 95: 'texldl', 96: 'breakp'}
OPNUM = {v: k for k, v in OPS.items()}
OPNUM['texldp'] = OPNUM['texldb'] = 66
# operandi: stringa di ruoli: d = dst, s = src, l = label/src. Opcode senza dst elencati con solo 's'.
SIG = {}
for _o in ('mov add sub mad mul rcp rsq dp3 dp4 min max slt sge exp log lit dst lrp frc m4x4 m4x3 m3x4 m3x3 m3x2 pow crs sgn abs nrm '
           'sincos mova cmp bem dp2add dsx dsy texldd texldl texld setp texcoord').split():
    SIG[_o] = None   # d + src (numero dal campo len)
NODST = {'nop', 'ret', 'endloop', 'endrep', 'else', 'endif', 'break', 'call', 'callnz', 'loop', 'label', 'rep', 'if', 'ifc', 'breakc',
         'breakp'}
CMP = {1: 'gt', 2: 'eq', 3: 'ge', 4: 'lt', 5: 'ne', 6: 'le'}
CMPN = {v: k for k, v in CMP.items()}
USAGE = ['position', 'blendweight', 'blendindices', 'normal', 'psize', 'texcoord', 'tangent', 'binormal', 'tessfactor',
         'positiont', 'color', 'fog', 'depth', 'sample']
USAGEN = {v: i for i, v in enumerate(USAGE)}
SAMP = {2: '2d', 3: 'cube', 4: 'volume'}
SAMPN = {v: k for k, v in SAMP.items()}
SMOD = {0: '', 1: 'neg', 2: 'bias', 3: 'bias_neg', 4: 'sign', 5: 'sign_neg', 6: 'comp', 7: 'x2', 8: 'x2_neg', 9: 'dz', 10: 'dw',
        11: 'abs', 12: 'abs_neg', 13: 'not'}
RT_TEMP, RT_INPUT, RT_CONST, RT_ADDR, RT_RAST, RT_ATTR, RT_TEXOUT, RT_CONSTINT, RT_COLOROUT, RT_DEPTHOUT, RT_SAMPLER = range(11)
RT_CONST2, RT_CONST3, RT_CONST4, RT_CONSTBOOL, RT_LOOP, RT_TEMPF16, RT_MISC, RT_LABEL, RT_PRED = 11, 12, 13, 14, 15, 16, 17, 18, 19


class Operand:
    __slots__ = ('rtype', 'num', 'rel', 'relop', 'wm', 'mod', 'shift', 'swz', 'smod', 'resv', 'isdst')

    def __init__(self, rtype, num, isdst=False, rel=False, relop=None, wm=15, mod=0, shift=0, swz=0xE4, smod=0, resv=0):
        self.rtype, self.num, self.isdst, self.rel, self.relop = rtype, num, isdst, rel, relop
        self.wm, self.mod, self.shift, self.swz, self.smod, self.resv = wm, mod, shift, swz, smod, resv

    def key(self):
        return (self.rtype, self.num, self.isdst, self.rel, self.relop.key() if self.relop else None, self.wm, self.mod, self.shift,
                self.swz, self.smod, self.resv)

    def __eq__(self, o): return isinstance(o, Operand) and self.key() == o.key()

    def __hash__(self): return hash(self.key())

    def tokens(self):
        t = (self.num & 0x7FF) | (((self.rtype >> 3) & 3) << 11) | ((1 if self.rel else 0) << 13) | (self.resv << 14) \
            | ((self.rtype & 7) << 28) | (1 << 31)
        if self.isdst:
            t |= (self.wm << 16) | (self.mod << 20) | ((self.shift & 15) << 24)
        else:
            t |= (self.swz << 16) | (self.smod << 24)
        out = [t]
        if self.rel:
            out += self.relop.tokens()
        return out


class Instr:
    __slots__ = ('op', 'ctrl', 'pred', 'ops', 'imm', 'usage')

    def __init__(self, op, ops=(), ctrl=0, pred=False, imm=(), usage=0):
        self.op, self.ops, self.ctrl, self.pred, self.imm, self.usage = op, list(ops), ctrl, pred, list(imm), usage

    def tokens(self):
        body = []
        if self.op == 'dcl':
            body = [self.usage | (1 << 31)] + self.ops[0].tokens()
        elif self.op in ('def', 'defi', 'defb'):
            body = self.ops[0].tokens() + list(self.imm)
        else:
            for o in self.ops: body += o.tokens()
        opn = OPNUM[self.op]
        return [opn | (self.ctrl << 16) | (len(body) << 24) | ((1 << 28) if self.pred else 0)] + body


class Comment:
    __slots__ = ('payload',)

    def __init__(self, payload): self.payload = bytes(payload)

    def tokens(self):
        p = self.payload + b'\0' * (-len(self.payload) % 4)
        return [0xFFFE | ((len(p) // 4) << 16)] + list(struct.unpack('<%dI' % (len(p) // 4), p))


class Program:
    def __init__(self, kind, major, minor, items):
        self.kind, self.major, self.minor, self.items = kind, major, minor, items

    def version_token(self):
        return (0xFFFF0000 if self.kind == 'ps' else 0xFFFE0000) | (self.major << 8) | self.minor

    def instrs(self): return [i for i in self.items if isinstance(i, Instr)]


def encode(p):
    out = [p.version_token()]
    for it in p.items: out += it.tokens()
    out.append(0xFFFF)
    return struct.pack('<%dI' % len(out), *out)


# ------------------------------------------------------------------------------------------------ decodifica
def _rtype(t): return ((t >> 28) & 7) | (((t >> 11) & 3) << 3)


def decode_operand(t, i, isdst):
    """t: lista token, i: indice del token param. Ritorna (Operand, nuovo i)."""
    v = t[i]; i += 1
    rel = bool((v >> 13) & 1)
    o = Operand(_rtype(v), v & 0x7FF, isdst=isdst, rel=rel, resv=(v >> 14) & 3)
    if isdst: o.wm, o.mod, o.shift = (v >> 16) & 15, (v >> 20) & 15, (v >> 24) & 15
    else: o.swz, o.smod = (v >> 16) & 255, (v >> 24) & 15
    if rel:
        o.relop, i = decode_operand(t, i, False)
    return o, i


def decode(b):
    n = len(b) // 4
    t = struct.unpack('<%dI' % n, b[:n * 4])
    vt = t[0]
    kind = 'ps' if (vt >> 16) == 0xFFFF else 'vs'
    assert (vt >> 16) in (0xFFFF, 0xFFFE), hex(vt)
    prog = Program(kind, (vt >> 8) & 255, vt & 255, [])
    i = 1; end = None
    while i < n:
        tok = t[i]; op = tok & 0xFFFF
        if op == 0xFFFF:
            end = i + 1; break
        if op == 0xFFFE:
            ln = (tok >> 16) & 0x7FFF
            prog.items.append(Comment(struct.pack('<%dI' % ln, *t[i + 1:i + 1 + ln]))); i += 1 + ln; continue
        ln = (tok >> 24) & 15
        name = OPS.get(op)
        if name is None: raise ValueError('opcode sconosciuto %d @%d' % (op, i))
        ctrl = (tok >> 16) & 255; pred = bool((tok >> 28) & 1)
        j = i + 1; stop = i + 1 + ln
        ins = Instr(name, ctrl=ctrl, pred=pred)
        if name == 'dcl':
            ins.usage = t[j]; assert ins.usage >> 31 == 1; o, j = decode_operand(t, j + 1, True); ins.ops = [o]
        elif name in ('def', 'defi', 'defb'):
            o, j = decode_operand(t, j, True); ins.ops = [o]; ins.imm = list(t[j:stop]); j = stop
        else:
            first = name not in NODST and name != 'texkill'
            if name == 'texkill': first = True
            k = 0
            while j < stop:
                if pred and j == stop - 1:       # predicato in coda
                    o, j = decode_operand(t, j, False); ins.ops.append(o); break
                isd = (k == 0 and first)
                o, j = decode_operand(t, j, isd); ins.ops.append(o); k += 1
        assert j == stop, (name, i, j, stop)
        prog.items.append(ins); i = stop
    prog.nend = end
    if end is not None and end != n:
        prog.trailing = b[end * 4:]
    else:
        prog.trailing = b''
    return prog


# ------------------------------------------------------------------------------------------------ testo: formato
def _fmt_f(u):
    f = struct.unpack('<f', struct.pack('<I', u))[0]
    if f != f or f in (float('inf'), float('-inf')): return '0x%08x' % u
    s = '%.9g' % f
    if struct.pack('<f', float(s)) != struct.pack('<I', u): return '0x%08x' % u
    if s == '-0': return '-0'   # preserva segno
    return s


def reg_name(kind, rtype, num, major=3):
    if rtype == RT_TEMP: return 'r%d' % num
    if rtype == RT_INPUT: return 'v%d' % num
    if rtype == RT_CONST: return 'c%d' % num
    if rtype == RT_CONST2: return 'c%d' % (num + 2048)
    if rtype == RT_CONST3: return 'c%d' % (num + 4096)
    if rtype == RT_CONST4: return 'c%d' % (num + 6144)
    if rtype == RT_ADDR: return ('a%d' % num) if kind == 'vs' else ('t%d' % num)
    if rtype == RT_RAST: return {0: 'oPos', 1: 'oFog', 2: 'oPts'}.get(num, 'oRast%d' % num)
    if rtype == RT_ATTR: return 'oD%d' % num
    if rtype == RT_TEXOUT: return ('o%d' % num) if (kind == 'vs' and major >= 3) else 'oT%d' % num
    if rtype == RT_CONSTINT: return 'i%d' % num
    if rtype == RT_COLOROUT: return 'oC%d' % num
    if rtype == RT_DEPTHOUT: return 'oDepth'
    if rtype == RT_SAMPLER: return 's%d' % num
    if rtype == RT_CONSTBOOL: return 'b%d' % num
    if rtype == RT_LOOP: return 'aL'
    if rtype == RT_TEMPF16: return 'h%d' % num
    if rtype == RT_MISC: return {0: 'vPos', 1: 'vFace'}.get(num, 'vMisc%d' % num)
    if rtype == RT_LABEL: return 'l%d' % num
    if rtype == RT_PRED: return 'p%d' % num
    return 'R%d_%d' % (rtype, num)


COMP = 'xyzw'


def fmt_swz(swz):
    c = [(swz >> (2 * k)) & 3 for k in range(4)]
    while len(c) > 1 and c[-1] == c[-2]: c.pop()
    if c == [0, 1, 2, 3]: return ''
    return '.' + ''.join(COMP[x] for x in c)


def fmt_mask(m):
    if m == 15: return ''
    return '.' + ''.join(COMP[k] for k in range(4) if m >> k & 1)


def fmt_operand(o, kind, major=3):
    if o.isdst:
        return reg_name(kind, o.rtype, o.num, major) + (('[' + fmt_operand(o.relop, kind, major) + ']') if o.rel else '') + fmt_mask(o.wm)
    base = reg_name(kind, o.rtype, o.num, major)
    if o.rel:
        r = o.relop
        if r.rtype == RT_LOOP: rs = 'aL'
        else: rs = reg_name(kind, r.rtype, r.num, major) + fmt_swz(r.swz)
        if o.rtype in (RT_CONST, RT_CONST2, RT_CONST3, RT_CONST4):
            pre, off = 'c', o.num + {RT_CONST: 0, RT_CONST2: 2048, RT_CONST3: 4096, RT_CONST4: 6144}[o.rtype]
        elif o.rtype == RT_TEXOUT: pre, off = ('o' if (kind == 'vs' and major >= 3) else 'oT'), o.num
        elif o.rtype == RT_INPUT: pre, off = 'v', o.num
        else: pre, off = re.sub(r'\d+$', '', base), o.num
        s = pre + '[' + rs + ('+%d' % off if off else '') + ']'
    else:
        s = base
    s += fmt_swz(o.swz)
    m = SMOD[o.smod]
    if m == '': return s
    if m == 'neg': return '-' + s
    if m == 'comp': return '1-' + s
    if m == 'not': return '!' + s
    if m == 'abs_neg': return '-' + s + '_abs'
    if m == 'bias_neg': return '-' + s + '_bias'
    if m == 'sign_neg': return '-' + s + '_bx2'
    if m == 'x2_neg': return '-' + s + '_x2'
    if m == 'sign': return s + '_bx2'
    return s + '_' + m


SHIFT = {0: '', 1: '_x2', 2: '_x4', 3: '_x8', 15: '_d2', 14: '_d4', 13: '_d8'}


def fmt_instr(ins, kind, major=3):
    n = ins.op
    if n == 'dcl':
        o = ins.ops[0]
        msfx = ('_sat' if o.mod & 1 else '') + ('_pp' if o.mod & 2 else '') + ('_centroid' if o.mod & 4 else '')
        if o.rtype == RT_SAMPLER:
            return 'dcl_%s%s %s' % (SAMP.get((ins.usage >> 27) & 15, 'type%d' % ((ins.usage >> 27) & 15)), msfx, fmt_operand(o, kind, major))
        u = ins.usage & 31; ix = (ins.usage >> 16) & 15
        extra = ins.usage & ~((31) | (15 << 16) | (1 << 31))
        s = 'dcl_' + USAGE[u] + (str(ix) if ix else '')
        if extra: s += '{%x}' % extra
        return s + msfx + ' ' + fmt_operand(o, kind, major)
    if n == 'def':
        return 'def %s, %s' % (fmt_operand(ins.ops[0], kind, major), ', '.join(_fmt_f(x) for x in ins.imm))
    if n == 'defi':
        return 'defi %s, %s' % (fmt_operand(ins.ops[0], kind, major), ', '.join(str(struct.unpack('<i', struct.pack('<I', x))[0]) for x in ins.imm))
    if n == 'defb':
        return 'defb %s, %s' % (fmt_operand(ins.ops[0], kind, major), 'true' if ins.imm[0] else 'false')
    mn = n
    if n == 'texld': mn = {0: 'texld', 1: 'texldp', 2: 'texldb'}.get(ins.ctrl, 'texld{%d}' % ins.ctrl)
    elif n in ('ifc', 'breakc', 'setp'): mn = n + '_' + CMP.get(ins.ctrl, '%d' % ins.ctrl)
    elif ins.ctrl: mn += '{ctrl%d}' % ins.ctrl
    ops = ins.ops
    pred = ''
    if ins.pred:
        pred = '(' + fmt_operand(ops[-1], kind, major) + ') '
        ops = ops[:-1]
    if ops and ops[0].isdst:
        d = ops[0]
        sfx = ''
        if d.shift: sfx += SHIFT.get(d.shift, '_s%d' % d.shift)
        if d.mod & 1: sfx += '_sat'
        if d.mod & 2: sfx += '_pp'
        if d.mod & 4: sfx += '_centroid'
        if d.mod & 8: sfx += '_m8'
        mn += sfx
    s = pred + mn
    if ops: s += ' ' + ', '.join(fmt_operand(o, kind, major) for o in ops)
    return s


def format_program(p, comments=True):
    L = ['%s_%d_%d' % (p.kind, p.major, p.minor)]
    for it in p.items:
        if isinstance(it, Comment):
            if comments: L.append('comment ' + it.payload.hex())
        else:
            L.append(fmt_instr(it, p.kind, p.major))
    if getattr(p, 'trailing', b''): L.append('trailing ' + p.trailing.hex())
    return '\n'.join(L) + '\n'


# ------------------------------------------------------------------------------------------------ testo: parse
_REG = re.compile(r'^(?:(?P<neg>-)|(?P<comp>1-)|(?P<not>!))?(?P<reg>[A-Za-z]+)(?P<num>\d*)(?:\[(?P<rel>[^\]]*)\])?(?P<swz>\.[xyzw]+)?(?:_(?P<mod>abs|bias|bx2|x2|dz|dw))?$')


def _parse_reg(name, kind, major, num=None, isdst=False):
    """name 'r', num 3 -> (rtype, num)"""
    if name == 'r': return RT_TEMP, num
    if name == 'v': return RT_INPUT, num
    if name == 'c':
        if num < 2048: return RT_CONST, num
        if num < 4096: return RT_CONST2, num - 2048
        if num < 6144: return RT_CONST3, num - 4096
        return RT_CONST4, num - 6144
    if name == 'a': return RT_ADDR, num
    if name == 't': return RT_ADDR, num
    if name == 'oPos': return RT_RAST, 0
    if name == 'oFog': return RT_RAST, 1
    if name == 'oPts': return RT_RAST, 2
    if name == 'oD': return RT_ATTR, num
    if name == 'oT': return RT_TEXOUT, num
    if name == 'o': return RT_TEXOUT, num
    if name == 'i': return RT_CONSTINT, num
    if name == 'oC': return RT_COLOROUT, num
    if name == 'oDepth': return RT_DEPTHOUT, 0
    if name == 's': return RT_SAMPLER, num
    if name == 'b': return RT_CONSTBOOL, num
    if name == 'aL': return RT_LOOP, 0
    if name == 'h': return RT_TEMPF16, num
    if name == 'vPos': return RT_MISC, 0
    if name == 'vFace': return RT_MISC, 1
    if name == 'l': return RT_LABEL, num
    if name == 'p': return RT_PRED, num
    raise ValueError('registro sconosciuto ' + name)


def _swz_parse(s):
    if not s: return 0xE4
    c = [COMP.index(ch) for ch in s[1:]]
    while len(c) < 4: c.append(c[-1])
    return sum(c[k] << (2 * k) for k in range(4))


def _mask_parse(s):
    if not s: return 15
    m = 0
    for ch in s[1:]: m |= 1 << COMP.index(ch)
    return m


def parse_operand(txt, kind, major, isdst):
    txt = txt.strip()
    m = re.match(r'^(-|1-|!)?(oDepth|oPos|oFog|oPts|vPos|vFace|aL|[A-Za-z]+)(\d*)(?:\[([^\]]*)\])?(\.[xyzw]+)?(?:_(abs|bias|bx2|x2|dz|dw))?$', txt)
    if not m: raise ValueError('operando non valido: %r' % txt)
    pre, nm, num, rel, swz, mod = m.groups()
    num = int(num) if num != '' else 0
    relop = None
    if rel is not None:
        mm = re.match(r'^\s*(aL|a0|[a-z]+\d*)(\.[xyzw])?\s*(?:\+\s*(\d+))?\s*$', rel)
        if not mm: raise ValueError('rel non valido: ' + rel)
        rn, rswz, add = mm.groups()
        add = int(add) if add else 0
        if rn == 'aL': relop = Operand(RT_LOOP, 0, swz=0xE4)
        else:
            mr = re.match(r'^([a-z]+)(\d*)$', rn)
            rt, rnum = _parse_reg(mr.group(1), kind, major, int(mr.group(2) or 0))
            relop = Operand(rt, rnum, swz=_swz_parse(rswz))
        # nome 'c' + [..] : indirizzo base = add
        if nm == 'c': rt, rnum = _parse_reg('c', kind, major, add)
        else: rt, rnum = _parse_reg(nm, kind, major, add if nm in ('v', 'o', 'oT') else num)
        o = Operand(rt, rnum, isdst=isdst, rel=True, relop=relop)
    else:
        rt, rnum = _parse_reg(nm, kind, major, num)
        o = Operand(rt, rnum, isdst=isdst)
    if isdst:
        o.wm = _mask_parse(swz)
    else:
        o.swz = _swz_parse(swz)
        sm = {'': 0, 'abs': 11, 'bias': 2, 'bx2': 4, 'x2': 7, 'dz': 9, 'dw': 10}[mod or '']
        if pre == '-':
            sm = {0: 1, 2: 3, 4: 5, 7: 8, 11: 12}.get(sm, None)
            if sm is None: raise ValueError('neg+mod non supportato: ' + txt)
        elif pre == '1-': sm = 6
        elif pre == '!': sm = 13
        o.smod = sm
    return o


def _split_args(s):
    out = []; depth = 0; cur = ''
    for ch in s:
        if ch == '[': depth += 1
        if ch == ']': depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur); cur = ''
        else: cur += ch
    if cur.strip(): out.append(cur)
    return [x.strip() for x in out]


def _imm_f(x):
    x = x.strip()
    if x.startswith('0x'): return int(x, 16)
    return struct.unpack('<I', struct.pack('<f', float(x)))[0]


def parse_text(text):
    lines = [l.split(';')[0].split('//')[0].strip() for l in text.splitlines()]
    lines = [l for l in lines if l]
    m = re.match(r'^(ps|vs)_(\d)_(\d)$', lines[0])
    kind, major, minor = m.group(1), int(m.group(2)), int(m.group(3))
    prog = Program(kind, major, minor, []); prog.trailing = b''
    for ln in lines[1:]:
        if ln.startswith('comment '):
            prog.items.append(Comment(bytes.fromhex(ln.split()[1]))); continue
        if ln.startswith('trailing '):
            prog.trailing = bytes.fromhex(ln.split()[1]); continue
        pred = False
        pm = re.match(r'^\(([^)]*)\)\s*(.*)$', ln)
        predop = None
        if pm:
            pred = True; predop = parse_operand(pm.group(1), kind, major, False); ln = pm.group(2)
        parts = ln.split(None, 1)
        mn = parts[0]; rest = parts[1] if len(parts) > 1 else ''
        # modificatori di destinazione e controlli
        shift = 0; mod = 0; ctrl = 0
        mnb = mn
        extra_ctrl = re.search(r'\{ctrl(\d+)\}', mnb)
        if extra_ctrl: ctrl = int(extra_ctrl.group(1)); mnb = mnb.replace(extra_ctrl.group(0), '')
        if mnb.startswith('dcl_'):
            u = mnb[4:]
            dm = 0
            for sf, bit in (('_sat', 1), ('_pp', 2), ('_centroid', 4)):
                if sf in u: dm |= bit; u = u.replace(sf, '')
            xm = re.search(r'\{([0-9a-f]+)\}$', u); xtra = 0
            if xm: xtra = int(xm.group(1), 16); u = u[:xm.start()]
            if u in SAMPN:
                usage = (SAMPN[u] << 27) | (1 << 31)
            else:
                mu = re.match(r'^([a-z]+)(\d*)$', u)
                usage = USAGEN[mu.group(1)] | (int(mu.group(2) or 0) << 16) | xtra | (1 << 31)
            o = parse_operand(rest, kind, major, True); o.mod = dm
            ins = Instr('dcl', [o], usage=usage); prog.items.append(ins); continue
        if mnb in ('def', 'defi', 'defb'):
            a = _split_args(rest); o = parse_operand(a[0], kind, major, True)
            if mnb == 'def': imm = [_imm_f(x) for x in a[1:]]
            elif mnb == 'defi': imm = [struct.unpack('<I', struct.pack('<i', int(x)))[0] for x in a[1:]]
            else: imm = [1 if a[1] == 'true' else 0]
            prog.items.append(Instr(mnb, [o], imm=imm)); continue
        # suffissi
        tokens = mnb.split('_')
        base = tokens[0]; sfx = tokens[1:]
        if base in ('ifc', 'breakc', 'setp'):
            ctrl = CMPN[sfx[0]]; sfx = sfx[1:]
        for s in list(sfx):
            if s == 'sat': mod |= 1
            elif s == 'pp': mod |= 2
            elif s == 'centroid': mod |= 4
            elif s == 'm8': mod |= 8
            elif s in ('x2', 'x4', 'x8', 'd2', 'd4', 'd8'):
                shift = {'x2': 1, 'x4': 2, 'x8': 3, 'd2': 15, 'd4': 14, 'd8': 13}[s]
            elif re.match(r's\d+$', s): shift = int(s[1:])
            else: raise ValueError('suffisso sconosciuto %s in %s' % (s, mn))
        if base in ('texldp', 'texldb'): ctrl = 1 if base == 'texldp' else 2; base = 'texld'
        if base not in OPNUM: raise ValueError('mnemonico sconosciuto ' + base)
        args = _split_args(rest) if rest else []
        ops = []
        first = base not in NODST
        for k, a in enumerate(args):
            isd = (k == 0 and first)
            o = parse_operand(a, kind, major, isd)
            if isd: o.mod, o.shift = mod, shift
            ops.append(o)
        if pred: ops.append(predop)
        prog.items.append(Instr(base, ops, ctrl=ctrl, pred=pred))
    return prog


def assemble(text):
    p = parse_text(text)
    return encode(p) + getattr(p, 'trailing', b'')


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('uso: sm3asm.py in.asm out.bin'); sys.exit(1)
    open(sys.argv[2], 'wb').write(assemble(open(sys.argv[1]).read()))
