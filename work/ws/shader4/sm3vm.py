"""sm3vm.py - interprete D3D9 ps_3_0 / vs_3_0 vettoriale (numpy float32, N campioni in parallelo).

run(prog, inputs, consts, tex, N) -> dict
  prog    sm3asm.Program (o bytes)
  inputs  {(rtype, num): array (N,4)}  es. {(1, 0): ...} per v0; (17,0) vPos; (17,1) vFace
  consts  {indice registro float: array (4,) o (N,4)}; sovrascrive i 'def' del programma solo se assente
  tex     callable(sampler_num, coords (N,4), mode 'n'|'p'|'b'|'l'|'g') -> (N,4)
  out     {'oC0':..., 'oDepth':..., 'kill': bool(N), 'used_consts': set, 'used_samplers': set, 'outputs': {(rtype,num): (N,4)}}
Semantica: vedi commenti per istruzione. dsx/dsy = 0 (nessun vicino). Controllo di flusso: if/else/endif con maschera per campione.
Non supportati (non compaiono nel gioco base): rep/loop/call/label/breakc con salti."""
import numpy as np, struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sm3asm
from sm3asm import *

F = np.float32


def _swz(v, swz):
    idx = [(swz >> (2 * k)) & 3 for k in range(4)]
    return v[:, idx]


def _smod(v, m):
    if m == 0: return v
    if m == 1: return -v
    if m == 2: return v - F(0.5)
    if m == 3: return -(v - F(0.5))
    if m == 4: return (v - F(0.5)) * F(2)
    if m == 5: return -(v - F(0.5)) * F(2)
    if m == 6: return F(1) - v
    if m == 7: return v * F(2)
    if m == 8: return -v * F(2)
    if m == 9: return v / v[:, 2:3]
    if m == 10: return v / v[:, 3:4]
    if m == 11: return np.abs(v)
    if m == 12: return -np.abs(v)
    if m == 13: return (v == 0).astype(F)
    raise ValueError(m)


class VM:
    def __init__(self, prog, N, inputs, consts, tex, bools=None, seed_dtype=F):
        if isinstance(prog, (bytes, bytearray)): prog = sm3asm.decode(bytes(prog))
        self.p, self.N, self.tex = prog, N, tex
        self.reg = {}
        for k, v in (inputs or {}).items(): self.reg[k] = np.asarray(v, F).reshape(N, 4).copy()
        self.consts = {}
        for ins in prog.items:
            if isinstance(ins, Instr) and ins.op == 'def':
                o = ins.ops[0]
                self.consts[o.num + {RT_CONST: 0, RT_CONST2: 2048}.get(o.rtype, 0)] = np.broadcast_to(
                    np.array([struct.unpack('<f', struct.pack('<I', u))[0] for u in ins.imm], F), (N, 4))
        self.defs = set(self.consts)
        for r, v in (consts or {}).items():
            if r in self.defs: continue
            self.consts[r] = np.broadcast_to(np.asarray(v, F).reshape(-1, 4) if np.ndim(v) > 1 else np.asarray(v, F).reshape(1, 4), (N, 4))
        self.bools = dict(bools or {})
        self.ints = {}
        for ins in prog.items:
            if isinstance(ins, Instr) and ins.op == 'defb': self.bools[ins.ops[0].num] = bool(ins.imm[0])
            if isinstance(ins, Instr) and ins.op == 'defi': self.ints[ins.ops[0].num] = [struct.unpack('<i', struct.pack('<I', u))[0] for u in ins.imm]
        self.stype = {}
        for ins in prog.items:
            if isinstance(ins, Instr) and ins.op == 'dcl' and ins.ops[0].rtype == RT_SAMPLER:
                self.stype[ins.ops[0].num] = (ins.usage >> 27) & 15
        self.used_consts = set(); self.used_samplers = set()
        self.kill = np.zeros(N, bool)
        self.pred = np.zeros((N, 4), bool)
        self.writes = {}

    # lettura registro
    def read(self, o):
        N = self.N
        t, n = o.rtype, o.num
        if o.rel:
            ro = o.relop
            if ro.rtype == RT_LOOP: raise NotImplementedError('aL')
            a = self.reg.get((RT_ADDR, ro.num), np.zeros((N, 4), F))
            comp = (ro.swz) & 3
            off = a[:, comp].astype(np.int64)
            base = n + {RT_CONST: 0, RT_CONST2: 2048, RT_CONST3: 4096, RT_CONST4: 6144}.get(t, 0)
            if t in (RT_CONST, RT_CONST2, RT_CONST3, RT_CONST4):
                v = np.zeros((N, 4), F)
                for i in range(N):
                    r = base + int(off[i]); self.used_consts.add(r)
                    c = self.consts.get(r)
                    v[i] = c[i] if c is not None else 0
                return _smod(_swz(v, o.swz), o.smod)
            raise NotImplementedError('rel su registro tipo %d' % t)
        if t in (RT_CONST, RT_CONST2, RT_CONST3, RT_CONST4):
            r = n + {RT_CONST: 0, RT_CONST2: 2048, RT_CONST3: 4096, RT_CONST4: 6144}[t]
            self.used_consts.add(r)
            v = np.array(self.consts[r], F) if r in self.consts else np.zeros((N, 4), F)
        elif t == RT_CONSTBOOL:
            v = np.full((N, 4), 1.0 if self.bools.get(n, False) else 0.0, F)
        else:
            v = self.reg.get((t, n))
            if v is None:
                v = np.zeros((N, 4), F)
        return _smod(_swz(v, o.swz), o.smod)

    def write(self, o, val, mask):
        """o: dst Operand, val (N,4), mask: (N,) bool maschera di flusso"""
        t, n = o.rtype, o.num
        val = np.asarray(val, F)
        if o.mod & 1: val = np.clip(np.nan_to_num(val, nan=0.0), 0, 1) if False else np.minimum(np.maximum(val, F(0)), F(1))
        sh = o.shift
        if sh:
            s = sh if sh < 8 else sh - 16
            val = val * F(2.0 ** s)
        key = (t, n)
        old = self.reg.get(key)
        if old is None: old = np.zeros((self.N, 4), F)
        new = old.copy()
        for c in range(4):
            if o.wm >> c & 1:
                sel = mask
                if sel is None: new[:, c] = val[:, c]
                else: new[sel, c] = val[sel, c]
        self.reg[key] = new

    def exec(self):
        N = self.N
        stack = []              # pila di maschere (cur, parent, taken)
        cur = np.ones(N, bool)
        for it in self.p.items:
            if not isinstance(it, Instr): continue
            op = it.op
            ops = it.ops
            if op in ('dcl', 'def', 'defi', 'defb'): continue
            if op == 'if':
                c = self.read(ops[0])[:, 0] != 0
                stack.append((cur, c)); cur = cur & c; continue
            if op == 'ifc':
                a = self.read(ops[0])[:, 0]; b = self.read(ops[1])[:, 0]
                c = self._cmp(it.ctrl, a, b)
                stack.append((cur, c)); cur = cur & c; continue
            if op == 'else':
                parent, c = stack[-1]; cur = parent & ~c; continue
            if op == 'endif':
                parent, c = stack.pop(); cur = parent; continue
            if op == 'texkill':
                v = self.read(ops[0].__class__(ops[0].rtype, ops[0].num, swz=0xE4)) if False else self.reg.get((ops[0].rtype, ops[0].num), np.zeros((N, 4), F))
                self.kill |= cur & np.any(v[:, :3] < 0, axis=1); continue
            if op in ('nop',): continue
            if op in ('breakc', 'break', 'rep', 'endrep', 'loop', 'endloop', 'call', 'callnz', 'label', 'ret', 'breakp'):
                raise NotImplementedError(op)
            if op == 'setp':
                a = self.read(ops[1]); b = self.read(ops[2])
                r = self._cmp(it.ctrl, a, b)
                old = self.pred.copy()
                for c in range(4):
                    if ops[0].wm >> c & 1: old[:, c] = np.where(cur, r[:, c], old[:, c])
                self.pred = old; continue
            d = ops[0]
            srcs = [self.read(o) for o in (ops[1:-1] if it.pred else ops[1:])]
            val = self._alu(it, srcs)
            m = cur
            self.write(d, val, m)
        return self

    @staticmethod
    def _cmp(c, a, b):
        return {1: a > b, 2: a == b, 3: a >= b, 4: a < b, 5: a != b, 6: a <= b}[c]

    def _tex(self, num, coords, mode):
        c = np.array(coords, F)
        if self.stype.get(num, 2) == 2: c[:, 2:] = 0
        return np.asarray(self.tex(num, c, mode), F)

    def _alu(self, it, s):
        op = it.op
        N = self.N
        with np.errstate(all='ignore'):
            if op == 'mov': return s[0]
            if op == 'mova': return np.floor(s[0] + F(0.5))
            if op == 'add': return s[0] + s[1]
            if op == 'sub': return s[0] - s[1]
            if op == 'mul': return s[0] * s[1]
            if op == 'mad': return s[0] * s[1] + s[2]
            if op == 'rcp':
                x = s[0][:, 3:4] if False else s[0][:, 0:1]
                return np.repeat(F(1) / x, 4, axis=1)
            if op == 'rsq':
                x = np.abs(s[0][:, 0:1])
                return np.repeat(F(1) / np.sqrt(x), 4, axis=1)
            if op == 'dp3': return np.repeat(np.sum(s[0][:, :3] * s[1][:, :3], axis=1, keepdims=True, dtype=F), 4, axis=1)
            if op == 'dp4': return np.repeat(np.sum(s[0] * s[1], axis=1, keepdims=True, dtype=F), 4, axis=1)
            if op == 'min': return np.minimum(s[0], s[1])
            if op == 'max': return np.maximum(s[0], s[1])
            if op == 'slt': return (s[0] < s[1]).astype(F)
            if op == 'sge': return (s[0] >= s[1]).astype(F)
            if op == 'exp': return np.repeat(np.exp2(s[0][:, 0:1]), 4, axis=1)
            if op == 'log':
                x = np.abs(s[0][:, 0:1])
                return np.repeat(np.log2(x), 4, axis=1)
            if op == 'lrp': return s[0] * (s[1] - s[2]) + s[2]
            if op == 'frc': return s[0] - np.floor(s[0])
            if op == 'pow':
                return np.repeat(np.power(np.abs(s[0][:, 0:1]), s[1][:, 0:1]), 4, axis=1)
            if op == 'abs': return np.abs(s[0])
            if op == 'sgn': return np.sign(s[0])
            if op == 'cmp': return np.where(s[0] >= 0, s[1], s[2])
            if op == 'dp2add':
                r = s[0][:, 0:1] * s[1][:, 0:1] + s[0][:, 1:2] * s[1][:, 1:2] + s[2][:, 0:1]
                return np.repeat(r, 4, axis=1)
            if op == 'nrm':
                l = np.sum(s[0][:, :3] * s[0][:, :3], axis=1, keepdims=True, dtype=F)
                return s[0] * (F(1) / np.sqrt(l))
            if op == 'crs':
                a, b = s[0], s[1]; r = np.zeros((N, 4), F)
                r[:, 0] = a[:, 1] * b[:, 2] - a[:, 2] * b[:, 1]
                r[:, 1] = a[:, 2] * b[:, 0] - a[:, 0] * b[:, 2]
                r[:, 2] = a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]
                return r
            if op == 'sincos':
                x = s[0][:, 0:1]; r = np.zeros((N, 4), F)
                r[:, 0:1] = np.cos(x); r[:, 1:2] = np.sin(x)
                return r
            if op == 'lit':
                x = s[0]; r = np.ones((N, 4), F)
                r[:, 1] = np.maximum(x[:, 0], 0)
                p = np.clip(x[:, 3], -127.9961, 127.9961)
                r[:, 2] = np.where(x[:, 0] > 0, np.power(np.maximum(x[:, 1], 0), p), 0)
                return r
            if op == 'dst':
                a, b = s[0], s[1]
                return np.stack([np.ones(N, F), a[:, 1] * b[:, 1], a[:, 2], b[:, 3]], axis=1)
            if op in ('dsx', 'dsy'): return np.zeros((N, 4), F)
            if op == 'texld':
                smp = it.ops[2]
                self.used_samplers.add(smp.num)
                mode = {0: 'n', 1: 'p', 2: 'b'}.get(it.ctrl, 'n')
                return self._tex(smp.num, s[0], mode)
            if op == 'texldl':
                smp = it.ops[2]
                self.used_samplers.add(smp.num)
                return self._tex(smp.num, s[0], 'l')
            if op == 'texldd':
                smp = it.ops[2]; self.used_samplers.add(smp.num)
                return self._tex(smp.num, s[0], 'g')
        raise NotImplementedError(op)


def run(prog, inputs, consts, tex, N, bools=None):
    vm = VM(prog, N, inputs, consts, tex, bools)
    vm.exec()
    out = {}
    for (t, n), v in vm.reg.items():
        if t == RT_COLOROUT: out['oC%d' % n] = v
        elif t == RT_DEPTHOUT: out['oDepth'] = v
    out['kill'] = vm.kill
    out['regs'] = vm.reg
    out['used_consts'] = vm.used_consts
    out['used_samplers'] = vm.used_samplers
    return out


def det_tex(sampler_key):
    """Funzione di texture deterministica e liscia: dipende da una chiave del sampler (nome o registro) e dalle coordinate."""
    import zlib
    def f(smp, coords, mode):
        key = sampler_key(smp) if callable(sampler_key) else smp
        h = zlib.crc32(repr(key).encode())
        rng = np.random.RandomState(h)
        a = rng.uniform(-3, 3, (4, 3)).astype(F); ph = rng.uniform(0, 6.28, 4).astype(F)
        c = coords[:, :3]
        out = np.stack([F(0.5) + F(0.5) * np.sin(c @ a[k] + ph[k]) for k in range(4)], axis=1).astype(F)
        return out
    return f
