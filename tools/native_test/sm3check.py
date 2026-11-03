"""Static D3D9 SM3 bytecode checker (independent decoder) + feature extraction for the 'envelope' comparison."""
import struct, collections

OPS = {0: 'nop', 1: 'mov', 2: 'add', 3: 'sub', 4: 'mad', 5: 'mul', 6: 'rcp', 7: 'rsq', 8: 'dp3', 9: 'dp4', 10: 'min', 11: 'max',
       12: 'slt', 13: 'sge', 14: 'exp', 15: 'log', 16: 'lit', 17: 'dst', 18: 'lrp', 19: 'frc', 20: 'm4x4', 21: 'm4x3', 22: 'm3x4',
       23: 'm3x3', 24: 'm3x2', 25: 'call', 26: 'callnz', 27: 'loop', 28: 'ret', 29: 'endloop', 30: 'label', 31: 'dcl', 32: 'pow',
       33: 'crs', 34: 'sgn', 35: 'abs', 36: 'nrm', 37: 'sincos', 38: 'rep', 39: 'endrep', 40: 'if', 41: 'ifc', 42: 'else',
       43: 'endif', 44: 'break', 45: 'breakc', 46: 'mova', 47: 'defb', 48: 'defi', 64: 'texcoord', 65: 'texkill', 66: 'texld',
       67: 'texbem', 68: 'texbeml', 69: 'texreg2ar', 70: 'texreg2gb', 71: 'texm3x2pad', 72: 'texm3x2tex', 73: 'texm3x3pad',
       74: 'texm3x3tex', 76: 'texm3x3spec', 77: 'texm3x3vspec', 78: 'expp', 79: 'logp', 80: 'cnd', 81: 'def', 82: 'texreg2rgb',
       83: 'texdp3tex', 84: 'texm3x2depth', 85: 'texdp3', 86: 'texm3x3', 87: 'texdepth', 88: 'cmp', 89: 'bem', 90: 'dp2add',
       91: 'dsx', 92: 'dsy', 93: 'texldd', 94: 'setp', 95: 'texldl', 96: 'breakp'}
# (has_dst, n_src) for SM3
SHAPE = {'nop': (0, 0), 'mov': (1, 1), 'add': (1, 2), 'sub': (1, 2), 'mad': (1, 3), 'mul': (1, 2), 'rcp': (1, 1), 'rsq': (1, 1),
         'dp3': (1, 2), 'dp4': (1, 2), 'min': (1, 2), 'max': (1, 2), 'slt': (1, 2), 'sge': (1, 2), 'exp': (1, 1), 'log': (1, 1),
         'lit': (1, 1), 'dst': (1, 2), 'lrp': (1, 3), 'frc': (1, 1), 'm4x4': (1, 2), 'm4x3': (1, 2), 'm3x4': (1, 2), 'm3x3': (1, 2),
         'm3x2': (1, 2), 'call': (0, 1), 'callnz': (0, 2), 'loop': (0, 2), 'ret': (0, 0), 'endloop': (0, 0), 'label': (0, 1),
         'pow': (1, 2), 'crs': (1, 2), 'sgn': (1, 3), 'abs': (1, 1), 'nrm': (1, 1), 'sincos': (1, 1), 'rep': (0, 1), 'endrep': (0, 0),
         'if': (0, 1), 'ifc': (0, 2), 'else': (0, 0), 'endif': (0, 0), 'break': (0, 0), 'breakc': (0, 2), 'mova': (1, 1),
         'texkill': (1, 0), 'texld': (1, 2), 'expp': (1, 1), 'logp': (1, 1), 'cnd': (1, 3), 'cmp': (1, 3), 'bem': (1, 2),
         'dp2add': (1, 3), 'dsx': (1, 1), 'dsy': (1, 1), 'texldd': (1, 4), 'setp': (1, 2), 'texldl': (1, 2), 'breakp': (0, 1)}
# instructions allowed per SM3 docs (IPOTESI: from MS docs memory; envelope vs PC is the measured check)
PS30 = set('abs add break breakc breakp call callnz cmp crs dcl def defb defi dp2add dp3 dp4 dsx dsy else endif endloop endrep exp '
           'frc if ifc label log loop lrp m3x2 m3x3 m3x4 m4x3 m4x4 mad max min mov mul nop nrm pow rcp rep ret rsq setp sincos sub '
           'texkill texld texldd texldl'.split())
VS30 = set('abs add break breakc breakp call callnz crs dcl def defb defi dp3 dp4 dst else endif endloop endrep exp expp frc if '
           'ifc label lit log logp loop lrp m3x2 m3x3 m3x4 m4x3 m4x4 mad max min mov mova mul nop nrm pow rcp rep ret rsq setp sge '
           'sgn sincos slt sub texldl'.split())
# instruction slots (IPOTESI: MS docs tables for ps_3_0/vs_3_0)
SLOTS = {'dcl': 0, 'def': 0, 'defi': 0, 'defb': 0, 'label': 0, 'breakc': 3, 'breakp': 3, 'call': 2, 'callnz': 3, 'crs': 2, 'dp2add': 2,
         'dsx': 2, 'dsy': 2, 'endloop': 2, 'endrep': 2, 'if': 3, 'ifc': 3, 'loop': 3, 'lrp': 2, 'm3x2': 2, 'm3x3': 3, 'm3x4': 4,
         'm4x3': 3, 'm4x4': 4, 'nrm': 3, 'pow': 3, 'rep': 3, 'sincos': 8, 'texkill': 2, 'texldd': 3, 'texldl': 2, 'lit': 3, 'dst': 1,
         'sgn': 3, 'expp': 1, 'logp': 1, 'exp': 1, 'log': 1}
RTN = {0: 'r', 1: 'v', 2: 'c', 3: 'a/t', 4: 'rast', 5: 'attr', 6: 'o', 7: 'i', 8: 'oC', 9: 'oDepth', 10: 's', 11: 'c2', 12: 'c3',
       13: 'c4', 14: 'b', 15: 'aL', 16: 'h', 17: 'misc', 18: 'l', 19: 'p'}
USAGE = ['position', 'blendweight', 'blendindices', 'normal', 'psize', 'texcoord', 'tangent', 'binormal', 'tessfactor', 'positiont',
         'color', 'fog', 'depth', 'sample']
SMOD = {0: '', 1: 'neg', 2: 'bias', 3: 'bias_neg', 4: 'sign', 5: 'sign_neg', 6: 'comp', 7: 'x2', 8: 'x2_neg', 9: 'dz', 10: 'dw',
        11: 'abs', 12: 'abs_neg', 13: 'not'}
CMP = {0: 'n/a', 1: 'gt', 2: 'eq', 3: 'ge', 4: 'lt', 5: 'ne', 6: 'le', 7: 'n/a7'}
# register ranges
PS_MAX = {0: 32, 1: 10, 2: 224, 7: 16, 14: 16, 10: 16, 8: 4, 9: 1, 15: 1, 17: 2, 19: 1, 18: 2048}
VS_MAX = {0: 32, 1: 16, 2: 256, 3: 1, 6: 12, 7: 16, 14: 16, 10: 4, 15: 1, 19: 1, 18: 2048}
PS_TYPES = {0, 1, 2, 7, 8, 9, 10, 14, 15, 17, 18, 19}
VS_TYPES = {0, 1, 2, 3, 6, 7, 10, 14, 15, 18, 19}


def rtype(v): return ((v >> 28) & 7) | (((v >> 11) & 3) << 3)


class Op:
    __slots__ = ('rt', 'num', 'rel', 'relop', 'wm', 'mod', 'shift', 'swz', 'smod', 'dst', 'raw')

    def __init__(self, v, dst):
        self.raw = v; self.dst = dst; self.rt = rtype(v); self.num = v & 0x7FF; self.rel = bool(v >> 13 & 1); self.relop = None
        self.wm = v >> 16 & 15; self.mod = v >> 20 & 15; self.shift = v >> 24 & 15; self.swz = v >> 16 & 255; self.smod = v >> 24 & 15

    def swc(self, c): return self.swz >> (2 * c) & 3

    def name(self): return '%s%d' % (RTN.get(self.rt, '?%d' % self.rt), self.num)


class Ins:
    __slots__ = ('op', 'opn', 'ctrl', 'pred', 'predop', 'dst', 'src', 'tok', 'idx', 'usage', 'uidx', 'stype', 'imm', 'len')


def decode(b):
    """returns (kind, ver, items, errors, info). items: list of Ins (comments skipped)."""
    errs = []; info = {}
    if len(b) % 4: errs.append('lunghezza blob non multipla di 4 (%d)' % len(b))
    n = len(b) // 4
    t = struct.unpack('<%dI' % n, b[:n * 4])
    vt = t[0]
    kind = {0xFFFF: 'ps', 0xFFFE: 'vs'}.get(vt >> 16)
    ver = (vt >> 8 & 255, vt & 255)
    if kind is None: errs.append('version token %08x' % vt); return None, ver, [], errs, info
    i = 1; items = []; end = None; ncom = 0
    while i < n:
        tok = t[i]; op = tok & 0xFFFF
        if op == 0xFFFF:
            if tok != 0x0000FFFF: errs.append('END token non canonico %08x' % tok)
            end = i; break
        if op == 0xFFFE:
            ln = tok >> 16 & 0x7FFF; ncom += 1
            if tok >> 31: errs.append('comment bit31')
            if i + 1 + ln > n: errs.append('commento oltre fine blob'); break
            i += 1 + ln; continue
        if op == 0xFFFD: errs.append('phase in SM3'); i += 1; continue
        ln = tok >> 24 & 15
        if tok >> 31: errs.append('instr %d: bit31 settato' % len(items))
        if tok >> 29 & 1: errs.append('instr %d: bit29 (riservato) settato' % len(items))
        if tok >> 30 & 1: errs.append('instr %d: coissue in SM3' % len(items))
        if i + 1 + ln > n: errs.append('istruzione oltre fine blob'); break
        body = t[i + 1:i + 1 + ln]
        x = Ins(); x.opn = op; x.op = OPS.get(op, 'op%d' % op); x.ctrl = tok >> 16 & 0xFF; x.pred = bool(tok >> 28 & 1); x.predop = None
        x.dst = None; x.src = []; x.tok = tok; x.idx = len(items); x.usage = x.uidx = x.stype = None; x.imm = (); x.len = ln
        for k, v in enumerate(body):
            if not v >> 31 and x.op not in ('def', 'defi', 'defb', 'dcl'):
                errs.append('instr %d %s: token parametro %d senza bit31 (%08x)' % (x.idx, x.op, k, v))
        if x.op == 'dcl':
            if ln != 2: errs.append('dcl lunghezza %d' % ln)
            d = body[0]; x.usage = d & 31; x.uidx = d >> 16 & 15; x.stype = d >> 27 & 15
            if not d >> 31: errs.append('dcl token senza bit31')
            x.dst = Op(body[1], True)
        elif x.op in ('def', 'defi', 'defb'):
            x.dst = Op(body[0], True); x.imm = body[1:]
            want = 2 if x.op == 'defb' else 5
            if ln != want: errs.append('%s lunghezza %d' % (x.op, ln))
        elif x.op in SHAPE:
            hd, ns = SHAPE[x.op]
            if x.op == 'sincos' and ln >= 1: pass
            ops = []; j = 0
            while j < len(body):
                v = body[j]; o = Op(v, False); j += 1
                if o.rel:
                    if j >= len(body): errs.append('instr %d: token relativo mancante' % x.idx); break
                    o.relop = Op(body[j], False); j += 1
                ops.append(o)
            if hd:
                if not ops: errs.append('instr %d %s senza operandi' % (x.idx, x.op))
                else:
                    d = ops.pop(0); x.dst = Op(d.raw, True); x.dst.relop = d.relop
            if x.pred:
                if ops: x.predop = ops.pop(0)
                else: errs.append('instr %d predicata senza token predicato' % x.idx)
            x.src = ops
            if x.op == 'texkill':
                pass
            elif len(x.src) != ns and not (x.op in ('sincos', 'sgn')):
                errs.append('instr %d %s: %d sorgenti (attese %d)' % (x.idx, x.op, len(x.src), ns))
        else:
            errs.append('opcode sconosciuto %d' % op)
        items.append(x)
        i += 1 + ln
    if end is None: errs.append('token END assente')
    else:
        info['trail_bytes'] = len(b) - (end + 1) * 4
    info['ncomments'] = ncom
    return kind, ver, items, errs, info


def lanes_read(x, k, o):
    """components (0..3) read from source operand k of instr x (after swizzle)."""
    op = x.op; wm = x.dst.wm if x.dst is not None else 15
    if op in ('dp3', 'nrm', 'crs'): comps = [0, 1, 2]
    elif op in ('dp4',): comps = [0, 1, 2, 3]
    elif op == 'dp2add': comps = [0, 1] if k < 2 else [0]
    elif op in ('rcp', 'rsq', 'exp', 'log', 'expp', 'logp', 'pow', 'sincos', 'ifc', 'breakc', 'if', 'callnz', 'loop', 'rep'):
        comps = [0]
    elif op in ('m4x4', 'm4x3'): comps = [0, 1, 2, 3]
    elif op in ('m3x4', 'm3x3', 'm3x2'): comps = [0, 1, 2]
    elif op in ('texld', 'texldl', 'texldd'):
        comps = [0, 1, 2, 3] if k == 0 else []
    elif op == 'lit': comps = [0, 1, 3]
    elif op == 'dst': comps = [1, 2] if k == 0 else [1, 3]
    else: comps = [c for c in range(4) if wm >> c & 1]
    return sorted(set(o.swc(c) for c in comps))


def analyze(b, platform_kind=None):
    """returns dict with counts, errors (rule violations), features (set of strings)."""
    kind, ver, items, errs, info = decode(b)
    R = dict(kind=kind, ver=ver, errs=list(errs), feats=set(), info=info)
    if kind is None: return R
    F = R['feats']; E = R['errs']
    ps = kind == 'ps'
    allowed = PS30 if ps else VS30
    MAX = PS_MAX if ps else VS_MAX; TYPES = PS_TYPES if ps else VS_TYPES
    if ver != (3, 0): E.append('versione %d.%d' % ver)
    nins = 0; slots = 0; seen_ins = False; dcls = collections.Counter(); defs = collections.Counter()
    declared = {}; defined = set(); init = set(); uninit = []; depth_if = depth_loop = 0; max_if = max_loop = 0
    maxreg = collections.defaultdict(int); max_consts = 0; outwrites = collections.defaultdict(int); oc_masks = collections.defaultdict(set)
    tex_samplers = set(); def_after = 0; dcl_after = 0; in_flow = 0
    for x in items:
        F.add('op:' + x.op)
        if x.op not in allowed: E.append('istr %d: opcode %s non ammesso in %s_3_0' % (x.idx, x.op, kind))
        if x.op in ('def', 'defi', 'defb'):
            if seen_ins: def_after += 1
            defs[(x.dst.rt, x.dst.num)] += 1; defined.add((x.dst.rt, x.dst.num))
            F.add('def:%s' % RTN.get(x.dst.rt)); maxreg[x.dst.rt] = max(maxreg[x.dst.rt], x.dst.num)
            if x.dst.wm != 15: F.add('def_partial_mask')
            continue
        if x.op == 'dcl':
            if seen_ins: dcl_after += 1
            r = x.dst; key = (r.rt, r.num); dcls[key] += 1
            if r.rt == 10:
                F.add('dcl:s:%s' % {2: '2d', 3: 'cube', 4: 'volume'}.get(x.stype, 'tt%d' % x.stype))
                declared[key] = ('sampler', x.stype)
            elif r.rt == 17:
                F.add('dcl:misc%d' % r.num); declared[key] = ('misc',)
            else:
                u = USAGE[x.usage] if x.usage < len(USAGE) else 'u%d' % x.usage
                F.add('dcl:%s:%s%d' % (RTN.get(r.rt), u, x.uidx)); F.add('dclusage:%s:%s' % (RTN.get(r.rt), u))
                F.add('dclmask:%s:%x' % (RTN.get(r.rt), r.wm))
                if r.mod: F.add('dclmod:%s:%x' % (RTN.get(r.rt), r.mod))
                declared[key] = (u, x.uidx, r.wm)
            if r.num >= MAX.get(r.rt, 0): E.append('dcl %s fuori range' % r.name())
            maxreg[r.rt] = max(maxreg[r.rt], r.num)
            continue
        seen_ins = True
        if x.op != 'label': nins += 1
        slots += SLOTS.get(x.op, 1)
        if x.pred: F.add('predicated'); F.add('pred:' + x.op)
        if x.ctrl and x.op not in ('texld',): F.add('ctrl:%s:%s' % (x.op, CMP.get(x.ctrl, x.ctrl)))
        if x.op == 'texld': F.add('texld_ctrl:%d' % x.ctrl)
        if x.op in ('if', 'ifc'): depth_if += 1; max_if = max(max_if, depth_if)
        if x.op == 'endif': depth_if -= 1
        if x.op in ('loop', 'rep'): depth_loop += 1; max_loop = max(max_loop, depth_loop)
        if x.op in ('endloop', 'endrep'): depth_loop -= 1
        flow = depth_if + depth_loop
        cregs = set()
        for k, o in enumerate(x.src):
            if o.rt not in TYPES: E.append('istr %d %s: tipo registro sorgente %s non ammesso' % (x.idx, x.op, RTN.get(o.rt, o.rt)))
            if o.num >= MAX.get(o.rt, 99999): E.append('istr %d %s: sorgente %s fuori range' % (x.idx, x.op, o.name()))
            maxreg[o.rt] = max(maxreg[o.rt], o.num)
            F.add('src:%s' % RTN.get(o.rt, o.rt)); F.add('srcop:%s:%s' % (x.op, RTN.get(o.rt, o.rt)))
            if o.smod: F.add('smod:%s' % SMOD.get(o.smod, o.smod)); F.add('smodop:%s:%s' % (x.op, SMOD.get(o.smod, o.smod)))
            if o.smod not in (0, 1, 11, 12) and not (o.smod == 13 and o.rt in (14, 19)):
                E.append('istr %d %s: modificatore sorgente %s non ammesso in SM3' % (x.idx, x.op, SMOD.get(o.smod, o.smod)))
            if o.rel:
                F.add('rel:%s[%s]' % (RTN.get(o.rt), RTN.get(o.relop.rt)))
                if ps and not (o.rt in (2, 1) and o.relop.rt == 15):
                    E.append('istr %d: indirizzamento relativo %s[%s] non ammesso in ps_3_0' % (x.idx, RTN.get(o.rt), RTN.get(o.relop.rt)))
            if o.rt in (2, 11, 12, 13): cregs.add(o.num)
            swz = o.swz
            rep = swz in (0x00, 0x55, 0xAA, 0xFF)
            if x.op in ('rcp', 'rsq', 'exp', 'log', 'pow', 'sincos', 'expp', 'logp') or (x.op == 'dp2add' and k == 2) or x.op in ('ifc', 'breakc'):
                F.add('scalarsrc:%s:%s' % (x.op, 'rep' if rep else 'norep'))
                if not rep and ps: E.append('istr %d %s: sorgente %d senza replicate swizzle (%02x)' % (x.idx, x.op, k, swz))
            if o.rt == 10:
                tex_samplers.add(o.num)
                if swz != 0xE4: E.append('istr %d %s: sampler con swizzle %02x' % (x.idx, x.op, swz))
                if o.smod: E.append('istr %d: sampler con modificatore' % x.idx)
            if swz != 0xE4: F.add('swz_nonident:%s' % RTN.get(o.rt))
            # declared?
            if (ps and o.rt in (1, 10, 17)) or (not ps and o.rt in (1, 10)):
                if (o.rt, o.num) not in declared: E.append('istr %d %s: %s usato senza dcl' % (x.idx, x.op, o.name()))
            if o.rt in (2, 7, 14) and not o.rel:
                pass
            if o.rt == 0:
                ln_ = lanes_read(x, k, o)
                if x.op in ('texld', 'texldl', 'texldd') and k == 0:
                    st_ = declared.get((10, x.src[1].num), ('sampler', 2))[1] if len(x.src) > 1 else 2
                    cc = [0, 1] if st_ == 2 else [0, 1, 2]
                    if x.op == 'texldl' or (x.op == 'texld' and x.ctrl in (1, 2)): cc = cc + [3]
                    ln_ = sorted(set(o.swc(c) for c in cc))
                if x.op == 'texldd' and k >= 2:
                    st_ = declared.get((10, x.src[1].num), ('sampler', 2))[1]
                    ln_ = sorted(set(o.swc(c) for c in ([0, 1] if st_ == 2 else [0, 1, 2])))
                for c in ln_:
                    if (o.num, c) not in init: uninit.append((x.idx, x.op, o.num, 'xyzw'[c]))
            if x.op in ('texld', 'texldl', 'texldd') and k == 1 and o.rt != 10:
                E.append('istr %d %s: src1 non e\' un sampler' % (x.idx, x.op))
        if len(cregs) > max_consts: max_consts = len(cregs)
        if x.predop is not None:
            F.add('predop_swz:%02x' % x.predop.swz)
        d = x.dst
        if d is not None:
            if d.rt not in TYPES: E.append('istr %d %s: tipo registro dest %s non ammesso' % (x.idx, x.op, RTN.get(d.rt, d.rt)))
            if d.num >= MAX.get(d.rt, 99999): E.append('istr %d %s: dest %s fuori range' % (x.idx, x.op, d.name()))
            maxreg[d.rt] = max(maxreg[d.rt], d.num)
            F.add('dst:%s' % RTN.get(d.rt, d.rt)); F.add('dstop:%s:%s' % (x.op, RTN.get(d.rt, d.rt)))
            if d.mod: F.add('rmod:%x' % d.mod); F.add('rmodop:%s:%x' % (x.op, d.mod))
            if d.mod & 4 and x.op != 'dcl': E.append('istr %d: _centroid su istruzione' % x.idx)
            if d.shift: E.append('istr %d %s: shift %d non ammesso in SM3' % (x.idx, x.op, d.shift)); F.add('shift')
            if d.wm == 0: E.append('istr %d %s: write mask vuota' % (x.idx, x.op))
            if d.rel: F.add('dstrel:%s' % RTN.get(d.rt))
            if d.rt in (8, 9, 6):
                outwrites[(d.rt, d.num)] += 1; oc_masks[(d.rt, d.num)].add(d.wm)
                F.add('outmask:%s%d:%x' % (RTN.get(d.rt), d.num, d.wm)); F.add('outop:%s:%s' % (x.op, RTN.get(d.rt)))
                if flow: F.add('outwrite_in_flow:%s' % RTN.get(d.rt))
                if x.pred: F.add('outwrite_pred')
                if not ps and (d.rt, d.num) not in declared: E.append('istr %d: o%d scritto senza dcl' % (x.idx, d.num))
            if x.op in ('sincos',) and ps and d.wm not in (1, 2, 3): E.append('istr %d sincos: mask %x' % (x.idx, d.wm))
            if x.op == 'nrm': F.add('nrm_mask:%x' % d.wm)
            if x.op in ('texld', 'texldl', 'texldd') and d.rt != 0: E.append('istr %d %s: dest non temp' % (x.idx, x.op))
            if x.op in ('texld', 'texldl', 'texldd'): F.add('texmask:%x' % d.wm)
            if x.op == 'setp' and d.rt != 19: E.append('istr %d setp: dest non p0' % x.idx)
            if d.rt == 19 and x.op != 'setp': E.append('istr %d %s scrive p0' % (x.idx, x.op))
            if x.op in ('m3x3', 'm4x3', 'm3x2', 'm3x4', 'm4x4') and x.src and x.src[0].rt == d.rt and x.src[0].num == d.num:
                E.append('istr %d %s: dest == src0' % (x.idx, x.op))
            if d.rt == 0:
                for c in range(4):
                    if d.wm >> c & 1: init.add((d.num, c))
        if x.op == 'texkill':
            F.add('texkill')
    if depth_if or depth_loop: E.append('if/loop non bilanciati (%d,%d)' % (depth_if, depth_loop))
    for k, v in dcls.items():
        if v > 1: E.append('dcl duplicato %s%d' % (RTN.get(k[0]), k[1]))
    for k, v in defs.items():
        if v > 1: E.append('def duplicato %s%d' % (RTN.get(k[0]), k[1]))
    # duplicate usage on inputs
    us = collections.Counter((v[0], v[1]) for kk, v in declared.items() if kk[0] in (1, 6) and len(v) == 3)
    for k, v in us.items():
        if v > 1: F.add('dcl_usage_shared');
    if def_after: E.append('%d def dopo istruzioni' % def_after); F.add('def_after_instr')
    if dcl_after: E.append('%d dcl dopo istruzioni' % dcl_after); F.add('dcl_after_instr')
    if uninit: F.add('uninit_read')
    for s in tex_samplers:
        st = declared.get((10, s))
        if st is None: E.append('sampler s%d usato senza dcl' % s)
    if ps and not any(k[0] == 8 for k in outwrites): F.add('no_oC_write')
    if ps and (8, 0) in oc_masks and 15 not in oc_masks[(8, 0)]: F.add('oC0_never_full')
    if not ps and not any(v[0] == 'position' for kk, v in declared.items() if kk[0] == 6): F.add('vs_no_position_out')
    unused_samp = [k[1] for k, v in declared.items() if k[0] == 10 and k[1] not in tex_samplers]
    if unused_samp: F.add('dcl_sampler_unused')
    R.update(nins=nins, slots=slots, uninit=uninit, maxreg=dict(maxreg), max_consts=max_consts, max_if=max_if, max_loop=max_loop,
             nsamp=len(tex_samplers), declared=declared, outwrites=dict(outwrites))
    return R
