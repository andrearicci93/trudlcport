"""Typed walker for TR8 Script sections (DRM section type 8 = cdc::ScriptTypeStreamData + everything it owns).

Layout (TRLAU-menu-hook src/cdc/script/ScriptType.h, confirmed on 17039 unique Xbox<->PC base pairs):
  SArray<T> = pointer to the first element; the u32 element count sits at ptr-4.
  Root (ScriptTypeStreamData):
    00 u32 version(4) 04 u16,u16  08 ScriptName{sym noCase, sym case}  0c char* nativePackage  10 char* nativeName
    14 id8 self        18 id8 super  1c u16 size, u16 align
    20 SArray<ScriptName> states   24 SArray<EnumDecl> enums   28 SArray<StructDecl> structs
    2c SArray<DataMember> members  30 SArray<StartFunctionInfo>  34 SArray<Prototype>  38 SArray<Function>
    3c u16 vtableSize, u8, u8      40 ptr (usually external)      44 ptr -> vtable[vtableSize] of ptrs to VTE
    48 SArray<id8> dependencies    4c u16, sym                     50 (count of the dependency array)
  DataType (12)   : u32 tag (bits 0-3 BaseType, 4 resolved, 5 compiled, 6 genericArg, 7 compound, 8-15 arraySize),
                    sym userType + u16 pad, union (DataType* sub / EnumDecl* / StructDecl* / id8 script / Compound*)
  DataMember (20) : DataType, u16 offset, sym name, init (meaning depends on the BaseType)
  Prototype (28)  : id8 script, u8 flags, u8 callType, u16 vtIndex, ScriptName, SArray<DataMember> args, DataType ret
  Function (28)   : Prototype*, u8 flags, u8 state, u16 size, u16 align, u16 stackSize, SArray<DataMember> locals,
                    SArray<StartFunctionInfo>, u32, SArray<u32> code
  StartFunctionInfo (8): id8, u32 ;  EnumDecl (8): id8, SArray<s32> values ;  VTE: u32 n, n x Function*, ...
  code: u32 words (opcode byte << 24 | operand); pointers inside code point at NUL-terminated strings or data.
Every word gets a semantic LABEL; the Xbox->PC byte permutation per label is learned from the pairs
(script_learn.py) with the walker's prior kind as a fallback.  Words the walker cannot reach get label ('unk',).
"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# prior kinds (generic_learn class names); 'ptr'/'id' are handled from the reloc table
K_S32, K_S16, K_RAW, K_B2S16, K_S16B2 = 's32', 's16', 'raw', 'b2s16', 's16b2'
SYMAB, SYMA, SYMB = 'id16ab:100', 'id16a:100', 'id16b:100'

ROOT = {0x00: K_S32, 0x04: K_S16, 0x08: SYMAB, 0x0c: 'ptr', 0x10: 'ptr', 0x14: 'id', 0x18: 'id', 0x1c: K_S16,
        0x20: 'ptr', 0x24: 'ptr', 0x28: 'ptr', 0x2c: 'ptr', 0x30: 'ptr', 0x34: 'ptr', 0x38: 'ptr',
        0x3c: K_S16B2, 0x40: 'ptr', 0x44: 'ptr', 0x48: 'ptr', 0x4c: SYMB, 0x50: K_S32}

class Walk:
    def __init__(self, d, rel, endian='be'):
        self.d, self.n, self.e = d, len(d), ('>' if endian == 'be' else '<')
        self.it = dict(rel.internal)
        self.ptr = set(rel.pointer_offsets())
        self.ids = rel.id_offsets()
        self.lab = {}            # word offset -> label tuple
        self.prior = {}          # label -> prior kind
        self.arrays = []         # (name, start, count, elem_size)
        self.seen = set()
        self.bad = []

    def u32(self, o):
        return struct.unpack_from(self.e + 'I', self.d, o)[0] if 0 <= o and o + 4 <= self.n else None

    def mark(self, o, label, kind=None):
        if o < 0 or o + 4 > self.n or o in self.lab: return
        self.lab[o] = label
        if kind is not None: self.prior.setdefault(label, kind)

    def tgt(self, o):
        return self.it.get(o)

    def codearray(self, o):
        t = self.tgt(o)
        if t is None or (t, 'code') in self.seen: return
        self.seen.add((t, 'code'))
        n = self.u32(t - 4)
        if n is None or t + 4 * n > self.n: self.bad.append(('count', 'code', o, t, n)); return
        self.mark(t - 4, ('count', 'code'), K_S32)
        self.arrays.append(('code', t, n, 4))
        self.code(t, n)

    def sarray(self, o, name, size, fn, maxn=1 << 20):
        t = self.tgt(o)
        if t is None or (t, name) in self.seen: return
        self.seen.add((t, name))
        n = self.u32(t - 4)
        if n is None or n > maxn or t + n * size > self.n:
            self.bad.append(('count', name, o, t, n)); return
        self.mark(t - 4, ('count', name), K_S32)
        self.arrays.append((name, t, n, size))
        for k in range(n):
            fn(t + k * size)

    # ---------------------------------------------------------------- structures
    def root(self):
        for f, k in ROOT.items():
            self.mark(f, ('root', f), k if k not in ('ptr', 'id') else K_S32)
        self.string(0x0c); self.string(0x10)
        self.sarray(0x20, 'states', 4, lambda a: self.mark(a, ('state',), SYMAB))
        self.sarray(0x24, 'enums', 8, self.enum)
        self.sarray(0x28, 'structs', 4, lambda a: self.mark(a, ('struct',), K_S32))
        self.sarray(0x2c, 'members', 20, lambda a: self.member(a, 'member'))
        self.sarray(0x30, 'sfi', 8, lambda a: self.sfi(a, 'sfi'))
        self.sarray(0x34, 'protos', 28, self.proto)
        self.sarray(0x38, 'funcs', 28, self.func)
        self.vtable()
        self.sarray(0x48, 'deps', 4, lambda a: self.mark(a, ('dep',), K_S32))

    def string(self, o):
        t = self.tgt(o)
        if t is None: return
        self.text(t, 'str')

    def text(self, t, name):
        if (t, 'text') in self.seen: return
        self.seen.add((t, 'text'))
        o = t
        while o + 4 <= self.n:
            self.mark(o, (name,), K_RAW)
            if 0 in self.d[o:o + 4]: break
            o += 4

    def enum(self, a):
        self.mark(a, ('enum', 0), K_S32); self.mark(a + 4, ('enum', 4), K_S32)
        self.sarray(a + 4, 'enumvals', 4, lambda b: self.mark(b, ('enumval',), K_S32))

    def sfi(self, a, ctx):
        self.mark(a, (ctx, 0), K_S32); self.mark(a + 4, (ctx, 4), K_S32)

    def dtype(self, a, ctx):
        tag = self.u32(a)
        if tag is None: return None
        bt = tag & 0xf
        self.mark(a, ('dt.tag',), K_S32)
        self.mark(a + 4, ('dt.user', bt), SYMA)
        self.mark(a + 8, ('dt.u', bt, (tag >> 7) & 1), K_S32)
        t = self.tgt(a + 8)
        if t is not None:
            if tag & 0x80:                              # Compound {ScriptType*, DataType* sub}
                self.compound(t)
            elif bt in (6, 7, 8):                       # ARRAY / DYNARRAY / MAP -> subtype
                self.dtype_at(t)
            elif bt == 0xe or bt == 0xf:
                self.enum_ptr(t)
            else:
                self.generic(t, ('dt.ref', bt))
        return tag

    def dtype_at(self, t):
        if (t, 'dt') in self.seen: return
        self.seen.add((t, 'dt'))
        self.dtype(t, 'sub')

    def compound(self, t):
        if (t, 'cmp') in self.seen: return
        self.seen.add((t, 'cmp'))
        self.mark(t, ('cmp', 0), K_S32); self.mark(t + 4, ('cmp', 4), K_S32)
        s = self.tgt(t + 4)
        if s is not None: self.dtype_at(s)

    def enum_ptr(self, t):
        if (t, 'enumref') in self.seen: return
        self.seen.add((t, 'enumref'))
        self.enum(t)

    def generic(self, t, label):
        """unknown target: label words up to the next labelled word / pointer target (max 64 bytes)."""
        if (t, 'gen') in self.seen: return
        self.seen.add((t, 'gen'))
        if self.is_text(t): self.text(t, 'ctext'); return
        for k in range(0, 64, 4):
            if t + k in self.lab or (k and (t + k) in self.targets): break
            self.mark(t + k, label + (k,), K_S32)

    def is_text(self, t, minlen=1):
        b = self.d[t:t + 4096]
        z = b.find(b'\0')
        if z < minlen: return False
        return all(32 <= c < 127 or c in (9, 10, 13) for c in b[:z])

    def member(self, a, ctx):
        tag = self.dtype(a, ctx)
        if tag is None: return
        bt = tag & 0xf
        ut = struct.unpack_from(self.e + 'H', self.d, a + 4)[0]
        self.mark(a + 12, ('dm.off', ctx), SYMB)
        self.mark(a + 16, ('dm.init', bt, (tag >> 7) & 1, 1 if (tag >> 8) & 0xff else 0, ctx), K_S32)
        t = self.tgt(a + 16)
        if t is not None:
            self.initdata(t, bt, ut, 0)

    def initdata(self, t, bt, ut, depth):
        """member init value block (type dependent; native types: keyed by their userType symbol)"""
        if (t, 'init') in self.seen or depth > 10: return
        self.seen.add((t, 'init'))
        if depth == 0 and self.is_text(t, 4): self.text(t, 'itext'); return
        for k in range(0, 1024, 4):
            o = t + k
            if o in self.lab or (k and o in self.targets) or o + 4 > self.n: break
            self.mark(o, ('init', bt, depth, min(k, 64), ut), K_S32)
            s = self.tgt(o)
            if s is not None:
                if self.is_text(s, 4): self.text(s, 'itext')
                else: self.initdata(s, bt, ut, depth + 1)

    def proto(self, a):
        self.mark(a, ('proto', 0), K_S32); self.mark(a + 4, ('proto', 4), K_B2S16)
        self.mark(a + 8, ('proto', 8), SYMAB)
        self.sarray(a + 12, 'args', 20, lambda b: self.member(b, 'arg'))
        self.dtype(a + 16, 'ret')

    def func(self, a):
        self.mark(a, ('func', 0), K_S32); self.mark(a + 4, ('func', 4), K_B2S16)
        self.mark(a + 8, ('func', 8), K_S16)
        self.mark(a + 0x14, ('func', 0x14), K_S32)
        self.sarray(a + 12, 'locals', 20, lambda b: self.member(b, 'local'))
        self.sarray(a + 16, 'fsfi', 8, lambda b: self.sfi(b, 'fsfi'))
        self.codearray(a + 0x18)
        self.mark(a + 0xc, ('func', 0xc), K_S32); self.mark(a + 0x10, ('func', 0x10), K_S32); self.mark(a + 0x18, ('func', 0x18), K_S32)

    # bytecode: u32 words op<<24|operand; these ops take extra operand words (pointer / script id)
    EXTRA = {0x05: 1, 0x34: 1, 0x65: 1, 0x66: 1, 0x67: 2, 0x68: 1, 0x69: 1, 0x6a: 1, 0x6b: 1, 0x77: 1, 0x7e: 1}

    def code(self, t, n):
        k = 0
        while k < n:
            o = t + 4 * k
            w = self.u32(o)
            op = w >> 24
            if o in self.ptr or o in self.ids:          # should not happen with a correct decode
                self.bad.append(('code_reloc_at_op', o)); self.mark(o, ('code.op', -1), K_S32); k += 1; continue
            self.mark(o, ('code.op', op), K_S32)
            for j in range(self.EXTRA.get(op, 0)):
                a = o + 4 * (j + 1)
                if k + 1 + j >= n: self.bad.append(('code_trunc', o)); break
                self.mark(a, ('code.arg', op, j), K_S32)
                s = self.tgt(a)
                if s is not None:
                    if self.is_text(s): self.text(s, 'ctext')
                    else: self.generic(s, ('cdata', op))
            k += 1 + self.EXTRA.get(op, 0)

    def vtable(self):
        t = self.tgt(0x44)
        if t is None: return
        n = struct.unpack_from(self.e + 'H', self.d, 0x3c)[0]
        if t + 4 * n > self.n: self.bad.append(('vt', t, n)); return
        self.arrays.append(('vtable', t, n, 4))
        for k in range(n):
            self.mark(t + 4 * k, ('vt',), K_S32)
            s = self.tgt(t + 4 * k)
            if s is not None and (s, 'vte') not in self.seen:
                self.seen.add((s, 'vte'))
                c = self.u32(s)
                self.mark(s, ('vte', 0), K_S32)
                for j in range(1, 4 + max(0, (c or 0) - 1)):
                    if s + 4 * j in self.lab or (s + 4 * j) in self.targets: break
                    self.mark(s + 4 * j, ('vte', min(j, 4)), K_S32)

    def run(self):
        self.targets = set(self.it.values())
        self.root()
        return self

def walk(d, rel, endian='be'):
    return Walk(d, rel, endian).run()

# ------------------------------------------------------------------------------- cross-layout offset translation
def elements(d, rel, e):
    """{array name: [(offset, name Symbol or None)]} for funcs/protos (name via the Prototype), other arrays by index."""
    W = Walk(d, rel, e).run(); E = W.e
    out = {}
    pn = {}
    def cnt(o):
        t = W.tgt(o)
        return W.u32(t - 4) if t is not None else -1
    def u(o): return W.u32(o)
    be = E == '>'
    def b2s16(o):       # u8, u8, u16 (platform-independent decode)
        b = d[o:o + 4]
        return (b[0], b[1], struct.unpack_from(E + 'H', b, 2)[0])
    def s16(o):
        return struct.unpack_from(E + 'HH', d, o)
    def feat_p(a):      # flags/callType/vtIndex, #args, return type tag
        return (b2s16(a + 4), cnt(a + 12), u(a + 16))
    for nm, t, n, sz in W.arrays:
        if nm == 'protos':
            out[nm] = [(t + k * sz, struct.unpack_from(E + 'H', d, t + k * sz + 8)[0], feat_p(t + k * sz)) for k in range(n)]
            pn.update({a: (v, f) for a, v, f in out[nm]})
    for nm, t, n, sz in W.arrays:
        if nm == 'funcs':
            l = []
            for k in range(n):
                a = t + k * sz
                v, fp = pn.get(W.tgt(a), (None, None))
                l.append((a, v, (b2s16(a + 4), s16(a + 8), cnt(a + 12), cnt(a + 16), cnt(a + 0x18), fp)))
            out[nm] = l
        elif nm in ('sfi', 'states', 'members', 'enums'):
            out[nm] = [(t + k * sz, None, None) for k in range(n)]
    return out

def offset_map(xd, xrel, pd, prel, symmap, votes=None):
    """Xbox-layout offset -> PC-layout offset of the array elements (functions, prototypes, ...) and root fields of two
    versions of one script (PC re-authored).  Elements are aligned by name Symbol (Xbox names through the BASE symbol map
    only, unknown names never match) with difflib; equal-length unmatched runs are paired positionally (and give
    Symbol votes xsym -> psym into `votes` if given)."""
    import difflib
    ex = elements(xd, xrel, 'be'); ep = elements(pd, prel, 'le')
    m = {o: o for o in range(0, 0x54, 4)}
    for nm, xl in ex.items():
        pl = ep.get(nm)
        if not pl: continue
        if nm not in ('funcs', 'protos'):
            if len(xl) == len(pl): m.update({a: b for (a, _, _), (b, _, _) in zip(xl, pl)})
            continue
        xs = [('k', symmap[v]) if v in symmap else ('x', i) for i, (o, v, f) in enumerate(xl)]
        ps = [('k', v) if v is not None else ('p', i) for i, (o, v, f) in enumerate(pl)]
        sm = difflib.SequenceMatcher(None, xs, ps, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                pairs = list(zip(range(i1, i2), range(j1, j2)))
            elif tag == 'replace' and i2 - i1 == j2 - j1:
                pairs = list(zip(range(i1, i2), range(j1, j2)))
            elif tag == 'replace':       # unequal gap: align by structural features (sizes, counts, prototype flags)
                fx = [repr(xl[i][2]) for i in range(i1, i2)]; fp = [repr(pl[j][2]) for j in range(j1, j2)]
                pairs = []
                for t2, a1, a2, b1, b2 in difflib.SequenceMatcher(None, fx, fp, autojunk=False).get_opcodes():
                    if t2 == 'equal' or (t2 == 'replace' and a2 - a1 == b2 - b1):
                        pairs += [(i1 + a, j1 + b) for a, b in zip(range(a1, a2), range(b1, b2))]
            else:
                pairs = []
            for i, j in pairs:
                m[xl[i][0]] = pl[j][0]
                if tag != 'equal' and votes is not None and xl[i][1] is not None and pl[j][1] is not None:
                    votes[xl[i][1]][pl[j][1]] += 1
    return m

def deps_normalized(d, rel, e='le'):
    """section data with every dependency array (SArray<id8>) sorted -> order-insensitive content key"""
    W = Walk(d, rel, e).run()
    b = bytearray(d)
    for nm, t, n, sz in W.arrays:
        if nm == 'deps' and n > 1:
            ws = sorted(bytes(d[t + 4 * k:t + 4 * k + 4]) for k in range(n))
            b[t:t + 4 * n] = b''.join(ws)
    return bytes(b)
