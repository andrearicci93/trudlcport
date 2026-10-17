"""xenos2sm3.py - traduttore Xenos (microcodice PS Xbox 360) -> D3D9 ps_3_0 (testo sm3asm), istruzione per istruzione.

Usa il parser/decodificatore di work/ws/xenos/xenos_xlat.py (validato 583/583 contro XenosRecomp). NON inventa: se qualcosa non ha
una traduzione sicura solleva Reject(motivo).
Interfaccia:
  translate(blob, consts, bools=None, samp=None, opts=None) -> Result
    consts : callable(name, index_in_array, count) -> registro PC (int) o None (=> Reject 'costante senza corrispondente PC')
    bools  : {indice bool Xbox: 0/1} valori statici per cond_exec (permutazione). Bool non presente in un cond_exec => Reject.
    samp   : callable(name, xbox_cidx) -> registro sampler PC (default: stesso registro Xbox)
  Result: .text (assemblabile con sm3asm.assemble), .consts {pcreg: (name, j)}, .defs {pcreg: (4 float)}, .samplers {pcreg: name},
          .inputs {(usage_name, index): componenti}, .ninstr, .notes
Semantica Xenos riprodotta (fonte: shader_recompiler.cpp di XenosRecomp, via xenos_xlat): vettore+scalare coemessi, ps (risultato scalare
precedente) in un temp dedicato, predicato p0 emulato con un temp float (>=0 vero) e `cmp` (nessuna istruzione predicata SM3), cond_exec su bool
risolti staticamente, kill -> texkill, vincolo SM3 di al piu' UN registro costante per istruzione rispettato con mov in temp."""
import sys, os, struct, math
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'work/ws/xenos'))
import xenos_xlat as XL
import sm3asm, sm3opt
from xenos_xlat import bits, alu_decode, operand, comp, VOP, SOP, decode_cf, EXEC_FAMILY, v_lanes, vmask_for

XYZW = 'xyzw'


class Reject(Exception):
    pass


class Result:
    pass


def _f32(x): return struct.unpack('<f', struct.pack('<f', x))[0]


class Tr:
    def __init__(self, blob, consts, bools=None, samp=None, opts=None):
        self.sh = XL.parse(blob)
        if not self.sh.is_ps: raise Reject('non e un pixel shader')
        self.consts_fn, self.bools, self.samp_fn = consts, dict(bools or {}), samp
        self.opts = opts or {}
        self.out = []                 # righe del corpo
        self.used_c = {}              # pcreg -> (name, j)
        self.defs = {}                # pcreg -> tuple
        self.defv = {}                # valore -> pcreg (costanti scalari/vettori helper)
        self.samplers = {}            # pcreg -> name
        self.samp_dtype = {}          # pcreg -> '2d'|'cube'|'volume'
        self.inputs = {}              # (usage, index) -> set(comp)
        self.interp = {}              # reg xenos -> (usage,index)
        self.written = {}             # reg xenos -> set(comp) scritte
        self.notes = []
        self.kills = 0
        self.pred_used = False
        self.guard = None             # selettore predicato attivo ('rN.xxxx', >=0 = esegui) o None
        self.cube_of_reg = {}; self.cube_dirs = {}; self.ncube = 0
        self.regions = []             # [(cf fine esclusiva, temp selettore)] regioni saltate da cond_jmp predicati
        self.irr_tmps = []            # temp costruiti per l'irradianza Xbox, liberati a fine istruzione
        self.vpos_used = False; self.vpos_comps = set(); self.face_needed = False
        self.sign_only = self._sign_only()
        self.gather = {}
        sh = self.sh
        for i in sh.interp: self.interp[i['reg']] = (i['usage'], i['index'])
        self._scan_regs()
        self.t_ps = self.nreg; self.t_pf = self.nreg + 1; self.nscr = self.nreg + 2
        self.free = []
        self.exp_written = {}
        self.maxtemp = self.nscr
        self.resolved_pc = None

    # ------------------------------------------------------------------ analisi preliminare
    def _scan_regs(self):
        mx = -1
        for e in XL.walk(self.sh):
            if e[0] == 'alu':
                f = e[2]
                if not f['export']: mx = max(mx, f['vdest'] if f['vmask'] else -1)
                if not f['export'] or True:
                    if f['smask'] and not (f['export'] and False): mx = max(mx, f['sdest'] if not f['export'] else -1)
                scx = 42 <= f['sopc'] <= 47
                for w, k in (('v0', 1), ('v1', 2), ('v2', 3)):
                    if k == 3 and scx: continue
                    if f['sel%d' % k]: mx = max(mx, f['reg%d' % k] & 0x3F)
                if scx: mx = max(mx, (f['sopc'] & 1) | (f['sel3'] << 1) | (f['sw3'] & 0x3C))
            elif e[0] == 'fetch':
                d0 = e[2]
                mx = max(mx, bits(d0, 5, 6), bits(d0, 12, 6))
        for i in self.sh.interp: mx = max(mx, i['reg'])
        mx = max(mx, self.sh.svpos_reg if self.sh.svpos_reg < 32 else -1)
        self.nreg = mx + 1

    def _sign_only(self):
        """Euristica: la x del registro svpos (= +-vPos.x secondo la faccia) serve SOLO per il segno quando ogni sua lettura e' l'operando
        scalare di un rcp (come s0 = campo 3) il cui risultato e' poi confrontato da un `sges` successivo. In tal caso basta vFace (+-1):
        il segno e' identico perche' vPos.x > 0. (Verificato numericamente dal confronto col gemello PC in F3.)"""
        sv = self.sh.svpos_reg
        if sv >= 32 or self.sh.is_ps is False: return False
        reads = 0; ok = True; pending = False; sges_after = False
        for e in XL.walk(self.sh):
            if e[0] == 'fetch':
                d0 = e[2]
                if bits(d0, 5, 6) == sv: return False
                continue
            if e[0] != 'alu': continue
            f = e[2]
            rd = [k for k in (1, 2, 3) if f['sel%d' % k] and (f['reg%d' % k] & 0x3F) == sv]
            if rd:
                reads += 1
                if rd != [3] or SOP.get(f['sopc']) not in ('rcpc', 'rcpf', 'rcp'): return False
                if f['vmask'] and VOP[f['vopc']] in ('mad', 'cndeq', 'cndge', 'cndgt', 'dp2add'): return False
                pending = True
            elif pending and SOP.get(f['sopc']) == 'sges': sges_after = True
        return reads > 0 and sges_after

    # ------------------------------------------------------------------ temp scratch
    def tmp(self):
        if self.free: return self.free.pop()
        r = self.nscr; self.nscr += 1
        if self.nscr > 31: raise Reject('troppi temp (>31)')
        self.maxtemp = max(self.maxtemp, self.nscr)
        return r

    def tmp_fresh(self):
        """Temp mai riciclato (vive per tutto il programma: raccolta parametri nel prologo)."""
        r = self.nscr; self.nscr += 1
        if self.nscr > 31: raise Reject('troppi temp (>31)')
        self.maxtemp = max(self.maxtemp, self.nscr)
        return r

    def rel(self, r): self.free.append(r)

    def emit(self, s): self.out.append(s)

    # ------------------------------------------------------------------ costanti
    def defreg(self, vals):
        vals = tuple(_f32(float(v)) for v in vals)
        if vals in self.defv: return self.defv[vals]
        # registro libero: dall'alto
        r = 223
        while r in self.used_c or r in self.defs: r -= 1
        self.defs[r] = vals; self.defv[vals] = r
        return r

    IRR = {'X': ((1, 'w', 1), (0, 'x', 1), (0, 'y', 1), (1, 'x', 1)),
           'Y': (None, (1, 'w', -1), (0, 'z', 1), (1, 'y', 1)),
           'Z': (None, None, (0, 'w', 1), (1, 'z', 1))}

    def irradiance(self, name):
        """Ambiente SH Xbox (IrradianceState{X,Y,Z}{Red,Green,Blue}, BaseRGB) -> costanti PC (Red0/Red1.., Base).
        Stessa forma quadratica: PC E = R0.(xy,xz,yz,zz) + R1.(x,y,z,x2-y2) + Base; Xbox E = x(X.n) + y(Y.n) + z(Z.n) + BaseRGB, n=(x,y,z,1).
        X = (R1.w, R0.x, R0.y, R1.x), Y = (0, -R1.w, R0.z, R1.y), Z = (0, 0, R0.w, R1.z). Ritorna 'rN' (temp costruito) o 'cN' o None."""
        if not name.startswith('IrradianceState'): return None
        if name == 'IrradianceStateBaseRGB':
            r = self.consts_fn('IrradianceStateBase', 0, 1)
            if r is None: raise Reject('IrradianceStateBase senza registro PC')
            self.used_c[r] = ('IrradianceStateBase', 0); return 'c%d' % r
        axis, col = name[len('IrradianceState')], name[len('IrradianceState') + 1:]
        if axis not in self.IRR or col not in ('Red', 'Green', 'Blue'): raise Reject('irradianza Xbox sconosciuta: %s' % name)
        regs = []
        for k in (0, 1):
            r = self.consts_fn('IrradianceState%s%d' % (col, k), 0, 1)
            if r is None: raise Reject('IrradianceState%s%d senza registro PC' % (col, k))
            self.used_c[r] = ('IrradianceState%s%d' % (col, k), 0); regs.append(r)
        t = self.tmp(); self.irr_tmps.append(t)
        for lane, src in enumerate(self.IRR[axis]):
            if src is None: self.emit('mov r%d.%s, %s.x' % (t, XYZW[lane], self.const1(0)))
            else:
                k, comp, sign = src
                self.emit('mov r%d.%s, %sc%d.%s' % (t, XYZW[lane], '-' if sign < 0 else '', regs[k], comp))
        return 'r%d' % t

    def cconst(self, xreg, comps, needed=None):
        """Costante float Xenos xreg -> (pcreg o def). Ritorna stringa 'cN' (oppure 'rN' = temp di raccolta dei MaterialParams con pmap)."""
        sh = self.sh
        e = sh.f4.get(xreg)
        if e is not None:
            c, j = e
            irr = self.irradiance(c['name'])
            if irr is not None: return irr
            pmap = self.opts.get('pmap')
            if pmap is not None and c['name'] == 'MaterialParams':
                if j not in self.gather: self.gather[j] = (self.tmp_fresh(), set())
                t, cs = self.gather[j]
                for cc in set(needed if needed is not None else comps):
                    m = pmap.get((j, cc))
                    if m is None: raise Reject('MaterialParams[%d].%s non rappresentabile nel layout PC del materiale' % (j, 'xyzw'[cc]))
                    cs.add(cc)
                return 'r%d' % t
            pcb = self.consts_fn(c['name'], j, c['count'])
            if pcb is None: raise Reject('costante senza corrispondente PC: %s' % c['name'])
            pcr = pcb
            self.used_c[pcr] = (c['name'], j)
            return 'c%d' % pcr
        if xreg in sh.defs:
            return 'c%d' % self.defreg(sh.defs[xreg])
        # non dichiarata: zero implicito
        self.notes.append('c%d non dichiarata -> 0' % xreg)
        return 'c%d' % self.defreg((0, 0, 0, 0))

    # ------------------------------------------------------------------ operandi
    def src(self, o, comps, needed=None):
        """o: Opnd; comps: 4 indici componente (lane->comp). Ritorna (stringa, creg|None)."""
        if o.rel: raise Reject('costante a indirizzamento relativo')
        sw = ''.join(XYZW[c] for c in comps)
        if o.kind == 'r':
            base = 'r%d' % o.reg; creg = None
            nd = needed if needed is not None else comps
            if o.reg == self.sh.svpos_reg and 0 in nd and not o.abs and o.reg not in self.written:
                self.face_needed = True
            self.note_read(o.reg, nd)
        else:
            base = self.cconst(o.reg, comps, needed); creg = None if base.startswith('r') else base
        s = base + '.' + sw
        if o.abs: s += '_abs'
        if o.neg: s = '-' + s
        # il modificatore _abs va dopo lo swizzle: r0.xyzw_abs  (formato sm3asm)
        return s, creg

    def note_read(self, xreg, comps):
        w = self.written.setdefault(xreg, set())
        miss = sorted(set(c for c in comps if c not in w))
        if not miss: return
        if xreg in self.interp:
            for c in miss: self.inputs.setdefault(self.interp[xreg], set()).add(c)
        elif xreg == self.sh.svpos_reg:
            for c in miss:
                if c == 0 and self.sign_only: continue
                self.vpos_used = True
                if c < 2: self.vpos_comps.add(c)
                else: self.out.append('mov r%d.%s, %s' % (xreg, XYZW[c], self.K(0)[0])); 
        else:
            # lettura di componenti mai scritte: zero (come XenosRecomp, registri a 0)
            self.out.append('mov r%d.%s, %s' % (xreg, ''.join(XYZW[c] for c in miss), self.K(0)[0]))
            self.notes.append('r%d.%s letto prima della scrittura -> 0' % (xreg, ''.join(XYZW[c] for c in miss)))
            for c in miss: w.add(c)

    def fixc(self, srcs):
        """srcs: lista di (stringa, creg). Garantisce un solo registro costante distinto."""
        seen = None; res = []
        for s, cr in srcs:
            if cr is None: res.append(s); continue
            if seen is None or seen == cr: seen = cr; res.append(s); continue
            t = self.tmp(); self.emit('mov r%d, %s' % (t, cr));
            neg = s.startswith('-'); sw = s.split('.', 1)[1]
            res.append(('-' if neg else '') + 'r%d.%s' % (t, sw)); self.temps_to_free.append(t)
        return res

    def pcs(self, v):
        """costante float scalare/vettore helper: stringa registro con swizzle"""
        pass

    def const1(self, v):
        r = self.defreg((v, v, v, v)); return 'c%d' % r

    def K(self, v, n=1):
        r = self.const1(v)
        return ('%s.%s' % (r, 'x' * n), r)

    # ------------------------------------------------------------------ scrittura
    def mark_written(self, reg, mask):
        w = self.written.setdefault(reg, set())
        for i in range(4):
            if mask >> i & 1: w.add(i)

    def dstname(self, f, vec=True):
        pass

    def guarded(self, dst):
        if dst.startswith('oC'):
            raise Reject('export predicato')
        n = int(dst[1:])
        return n < self.nreg or n in (self.t_ps, self.t_pf)

    def psel(self, cond):
        """Temp con selettore del predicato: x >= 0 se p0 == cond (p0 tenuto in t_pf.x come 1/0)."""
        t = self.tmp(); h = self.const1(0.5)
        if cond: self.emit('add r%d.x, r%d.x, -%s.x' % (t, self.t_pf, h))
        else: self.emit('add r%d.x, -r%d.x, %s.x' % (t, self.t_pf, h))
        return t

    def emit_op(self, op, dst, srcs, sat=False, mask=None):
        """Come emit_op_raw; sotto predicato (self.guard) la scrittura diventa cmp(guard, nuovo, vecchio)."""
        if self.guard is not None and self.guarded(dst):
            g = self.tmp()
            self.emit_op_raw(op, 'r%d' % g, srcs, sat, mask)
            m = 15 if mask is None else mask
            ms = '' if m == 15 else '.' + ''.join(XYZW[i] for i in range(4) if m >> i & 1)
            self.emit('cmp %s%s, r%d.xxxx, r%d, %s' % (dst, ms, self.guard, g, dst))
            self.rel(g)
            return
        self.emit_op_raw(op, dst, srcs, sat, mask)

    def emit_op_raw(self, op, dst, srcs, sat=False, mask=None):
        """dst 'r5' o 'oC0'; mask: maschera 0-15 o None; srcs: lista di (str, creg)."""
        if op in ('sge', 'slt'):
            # sge/slt NON esistono nei pixel shader ps_3_0 (solo vs): d = (a-b >= 0) ? 1 : 0  /  (a-b < 0) ? 1 : 0 con cmp
            t = self.tmp()
            self.emit_op_raw('add', 'r%d' % t, [srcs[0], self._negsrc(srcs[1])], False, 15 if mask is None else mask)
            one, zero = self.K(1, 4), self.K(0, 4)
            self.emit_op_raw('cmp', dst, [('r%d.xyzw' % t, None), one if op == 'sge' else zero, zero if op == 'sge' else one], sat, mask)
            self.rel(t)
            return
        self.temps_to_free = []
        ss = self.fixc(srcs)
        m = '' if mask is None or mask == 15 else '.' + ''.join(XYZW[i] for i in range(4) if mask >> i & 1)
        self.emit('%s%s %s%s%s' % (op, '_sat' if sat else '', dst, m, (', ' + ', '.join(ss)) if ss else ''))
        for t in self.temps_to_free: self.rel(t)
        self.temps_to_free = []

    # ------------------------------------------------------------------ ALU
    def alu(self, f, pred):
        """Predicazione per istruzione: tutta l'istruzione (ps, p0, destinazioni) solo se p0 == predc (come XenosRecomp)."""
        saved = self.guard; held = []
        if f['ispred']:
            g = self.psel(f['predc']); held.append(g)
            if saved is not None:
                self.emit('min r%d.x, r%d.x, r%d.x' % (g, g, saved))
            self.guard = g
        try:
            self.alu_body(f, None)
        finally:
            self.guard = saved
            for t in held: self.rel(t)
            for t in self.irr_tmps: self.rel(t)
            self.irr_tmps = []

    def alu_body(self, f, pred):
        sh = self.sh
        v = VOP[f['vopc']]; sc = SOP.get(f['sopc'], '?')
        vm = f['vmask']; sm = f['smask']
        export = bool(f['export'])
        if export: vm &= ~sm
        if f['vdest_rel'] and not export: raise Reject('dest relativa')
        if v == 'maxa' or sc in ('maxas', 'maxasf'): raise Reject('a0 (maxa/maxas)')
        vws = False
        # predicazione: se ispred, la condizione e' quella dell'istruzione; altrimenti guard di clausola
        ip = pred
        if f['ispred']:
            ip = None
        # ---- scalare (calcola in ps)
        new_ps = False
        if f['sopc'] != 50:
            self.scalar(f, sc)
            new_ps = True
        # ---- vettore
        vdst = None
        if vm:
            vdst = self.vector(f, v, vm, export)
        # ---- scrittura scalare
        if sm:
            dm = sm if not export else sm & ~f['vmask']
            if dm:
                self.write_dest(f, f['sdest'], dm, [('r%d.xxxx' % self.t_ps, None)], 'mov', f['ssat'] and False, export, ip, scalar=True)
        if export:
            one = f['vmask'] & f['smask']; zero = (15 & ~(f['vmask'] | f['smask'])) if f['sdest_rel'] else 0
            for i in range(4):
                if zero & (1 << i):
                    self.write_dest(f, f['vdest'], 1 << i, [self.K(0)], 'mov', False, True, ip)
                elif one & (1 << i):
                    self.write_dest(f, f['vdest'], 1 << i, [self.K(1)], 'mov', False, True, ip)

    def expname(self, vdest):
        if vdest in (0, 1, 2, 3):
            if vdest != 0: raise Reject('export oC%d (MRT)' % vdest)
            return 'oC%d' % vdest
        if vdest == 61: raise Reject('export oDepth')
        raise Reject('export %d' % vdest)

    def write_dest(self, f, vdest, mask, srcs, op, sat, export, pred, scalar=False, tmpreg=None):
        """Emette la scrittura finale su r<vdest>/oC con maschera mask (gestisce predicazione)."""
        name = self.expname(vdest) if export else 'r%d' % vdest
        if pred is None or pred[1] is None:
            self.emit_op(op, name, srcs, sat, mask)
        else:
            raise Reject('predicazione in write_dest non gestita')
        if not export: self.mark_written(vdest, mask)
        else: self.exp_written[vdest] = self.exp_written.get(vdest, 0) | mask

    def scalar(self, f, sc):
        """ps = risultato scalare."""
        ps = 'r%d.x' % self.t_ps
        def s0():
            o = operand(f, 's0'); c = o.lanecomp(0); return self.src(o, [c] * 4)
        def s1():
            o = operand(f, 's1'); c = o.lanecomp(0); return self.src(o, [c] * 4)
        def c0():
            o = operand(f, 'sc0'); c = o.lanecomp(0); return self.src(o, [c] * 4)
        def c1():
            o = operand(f, 'sc1'); c = o.lanecomp(0); return self.src(o, [c] * 4)
        P = ('r%d.xxxx' % self.t_ps, None)
        one = None
        ssat = bool(f['ssat'])
        E = lambda op, srcs: self.emit_op(op, 'r%d' % self.t_ps, srcs, ssat, 1)
        def neg(t):
            s, cr = t
            if s.startswith('-'): return (s[1:], cr)
            return ('-' + s, cr)
        if sc == 'adds': E('add', [s0(), s1()])
        elif sc == 'adds_prev': E('add', [s0(), P])
        elif sc == 'muls': E('mul', [s0(), s1()])
        elif sc in ('muls_prev', 'muls_prev2'): E('mul', [s0(), P])
        elif sc in ('maxs',): E('max', [s0(), s1()])
        elif sc == 'mins': E('min', [s0(), s1()])
        elif sc == 'subs': E('add', [s0(), neg(s1())])
        elif sc == 'subs_prev': E('add', [s0(), neg(P)])
        elif sc == 'frcs': E('frc', [s0()])
        elif sc == 'floors':
            t = self.tmp(); self.emit_op('frc', 'r%d' % t, [s0()], False, 1)
            a = s0(); self.emit_op('add', 'r%d' % self.t_ps, [a, ('-r%d.xxxx' % t, None)], ssat, 1); self.rel(t)
        elif sc == 'truncs':
            self.trunc_scalar(s0(), ssat)
        elif sc == 'exp': E('exp', [s0()])
        elif sc in ('logc', 'log'): E('log', [s0()])
        elif sc in ('rcpc', 'rcpf', 'rcp'): E('rcp', [s0()])
        elif sc in ('rsqc', 'rsqf', 'rsq'): E('rsq', [s0()])
        elif sc == 'sqrt':
            t = self.tmp(); self.emit_op('rsq', 'r%d' % t, [s0()], False, 1)
            self.emit_op('rcp', 'r%d' % self.t_ps, [('r%d.xxxx' % t, None)], ssat, 1); self.rel(t)
        elif sc == 'sges':
            E('sge', [s0(), self.K(0)])
        elif sc == 'sgts':
            a = s0(); E('slt', [self.K(0), a])
        elif sc in ('seqs', 'snes'):
            a = s0(); t = self.tmp()
            one, zero = self.K(1), self.K(0)
            self.emit_op('cmp', 'r%d' % t, [self._negabs(a), one if sc == 'seqs' else zero, zero if sc == 'seqs' else one], False, 1)
            self.emit_op('mov', 'r%d' % self.t_ps, [('r%d.xxxx' % t, None)], ssat, 1); self.rel(t)
        elif sc in ('mulsc0', 'mulsc1'): E('mul', [c0(), c1()])
        elif sc in ('addsc0', 'addsc1'): E('add', [c0(), c1()])
        elif sc in ('subsc0', 'subsc1'): E('add', [c0(), neg(c1())])
        elif sc in ('sin', 'cos'):
            t = self.tmp()
            k = self.defreg((1.0 / (2 * math.pi), 0.5, 2 * math.pi, -math.pi))
            self.emit_op('mad', 'r%d' % t, [s0(), ('c%d.xxxx' % k, None), ('c%d.yyyy' % k, None)], False, 1)
            self.emit('frc r%d.x, r%d.x' % (t, t))
            self.emit('mad r%d.x, r%d.x, c%d.z, c%d.w' % (t, t, k, k))
            self.emit('sincos r%d.xy, r%d.x' % (t, t))
            cc = 'x' if sc == 'cos' else 'y'
            self.emit_op('mov', 'r%d' % self.t_ps, [('r%d.%s' % (t, cc * 4), None)], ssat, 1)
            self.rel(t)
        elif sc.startswith('setp_'):
            self.setp_scalar(f, sc, s0, E, ssat)
        elif sc.startswith('kills_'):
            self.kill_scalar(f, sc)
        else:
            raise Reject('scalare non supportato: %s' % sc)
        self.mark_ps = True

    def setp_scalar(self, f, sc, s0, E, ssat):
        """p0 e ps come XenosRecomp. p0 -> t_pf.x (1/0)."""
        one, zero = self.K(1), self.K(0)
        tp = self.tmp()
        if sc == 'setp_clr':
            self.emit_op_raw('mov', 'r%d' % tp, [zero], False, 1)
            E('mov', [('c%d.xxxx' % self.defreg((3.4028234e38,) * 4), None)])
        else:
            a = s0()
            if sc in ('setp_eq', 'setp_rstr'): self.emit_op_raw('cmp', 'r%d' % tp, [self._negabs(a), one, zero], False, 1)
            elif sc == 'setp_ne': self.emit_op_raw('cmp', 'r%d' % tp, [self._negabs(a), zero, one], False, 1)
            elif sc == 'setp_gt': self.emit_op_raw('cmp', 'r%d' % tp, [self._negsrc(a), zero, one], False, 1)
            elif sc == 'setp_ge': self.emit_op_raw('cmp', 'r%d' % tp, [a, one, zero], False, 1)
            elif sc in ('setp_inv', 'setp_pop'):
                u = self.tmp()
                self.emit_op_raw('add', 'r%d' % u, [a, self._negsrc(one)], False, 1)          # a - 1
                if sc == 'setp_inv': self.emit_op_raw('cmp', 'r%d' % tp, [('-r%d.xxxx_abs' % u, None), one, zero], False, 1)
                else: self.emit_op_raw('cmp', 'r%d' % tp, [('-r%d.xxxx' % u, None), one, zero], False, 1)   # a-1 <= 0
                if sc == 'setp_inv':
                    E('cmp', [self._negabs(a), one, a])                                            # a == 0 ? 1 : a
                else:
                    w = self.tmp(); self.emit('add r%d.x, -r%d.x, %s.x' % (w, tp, self.const1(0.5)))
                    E('cmp', [('r%d.xxxx' % w, None), ('r%d.xxxx' % u, None), zero]); self.rel(w)  # p0 ? 0 : a-1
                self.rel(u)
            else: raise Reject(sc)
            if sc in ('setp_eq', 'setp_ne', 'setp_gt', 'setp_ge'):
                E('add', [('-r%d.xxxx' % tp, None), one])                                          # p0 ? 0 : 1
            elif sc == 'setp_rstr':
                E('mov', [a])                                                                      # p0 ? 0 : a == a
        self.emit_op('mov', 'r%d' % self.t_pf, [('r%d.xxxx' % tp, None)], False, 1)
        self.rel(tp)

    def _negabs(self, t):
        s, cr = t
        if s.startswith('-'): s = s[1:]
        if not s.endswith('_abs'): s = s + '_abs'
        return ('-' + s, cr)

    def trunc_scalar(self, a, ssat):
        # trunc(x) = sign(x)*floor(|x|) = x - frc(x) per x>=0 ; x + frc(-x) per x<0 : usa cmp
        t = self.tmp(); u = self.tmp()
        s, cr = a
        pos = s[1:] if s.startswith('-') else s
        # |x|
        absx = (pos if pos.endswith('_abs') else pos + '_abs', cr)
        self.emit_op('frc', 'r%d' % t, [absx], False, 1)
        self.emit_op('add', 'r%d' % u, [absx, ('-r%d.xxxx' % t, None)], False, 1)
        self.emit_op('cmp', 'r%d' % self.t_ps, [a, ('r%d.xxxx' % u, None), ('-r%d.xxxx' % u, None)], ssat, 1)
        self.rel(t); self.rel(u)

    def kill_scalar(self, f, sc):
        if self.guard is not None: raise Reject('kill predicato')
        o = operand(f, 's0'); c = o.lanecomp(0)
        a = self.src(o, [c] * 4)
        t = self.tmp()
        zero, one = self.K(0), self.K(1)
        # kill se: eq: s==0 ; gt: s>0 ; ge: s>=0 ; ne: s!=0
        if sc == 'kills_gt': self.emit_op('slt', 'r%d' % t, [zero, a], False, 1)
        elif sc == 'kills_ge': self.emit_op('sge', 'r%d' % t, [a, zero], False, 1)
        elif sc in ('kills_eq', 'kills_ne'):
            self.emit_op('cmp', 'r%d' % t, [self._negabs(a), one if sc == 'kills_eq' else zero, zero if sc == 'kills_eq' else one], False, 1)
        else: raise Reject(sc)
        # ps = condizione (1/0) come XenosRecomp
        self.emit('mov r%d.x, r%d.x' % (self.t_ps, t))
        self.do_texkill(t)
        self.rel(t)

    def do_texkill(self, t):
        # t.x = 1 se kill, 0 altrimenti. texkill uccide se una componente xyz < 0: valore = 0.5 - t.x
        k = self.defreg((0.5, 0.5, 0.5, 0.5))
        self.emit('add r%d.xyz, c%d.xxx, -r%d.x' % (t, k, t))
        self.emit('texkill r%d' % t)
        self.kills += 1

    # ------------------------------------------------------------------ vettore
    def lanes_src(self, f, which, lanes=None):
        o = operand(f, which)
        lanes = v_lanes(f, which)
        cs = [comp(o.swz, l) for l in range(4)]
        first = cs[lanes[0]]
        cs2 = [cs[l] if l in lanes else first for l in range(4)]
        return self.src(o, cs2, needed=[cs[l] for l in lanes])

    def vector(self, f, v, vm, export):
        """Emette l'op vettoriale e ne scrive il risultato nella destinazione. Ritorna None."""
        sat = bool(f['vsat'])
        S = lambda w: self.lanes_src(f, w)
        dst_reg = f['vdest']
        # destinazione e predicazione
        ip = None
        name = self.expname(dst_reg) if export else 'r%d' % dst_reg
        def W(op, srcs, mask=None, sat_=sat):
            self.emit_op(op, name, srcs, sat_, vm if mask is None else mask)
        if v == 'add': W('add', [S('v0'), S('v1')])
        elif v == 'mul': W('mul', [S('v0'), S('v1')])
        elif v in ('max',): W('max', [S('v0'), S('v1')])
        elif v == 'min': W('min', [S('v0'), S('v1')])
        elif v == 'mad': W('mad', [S('v0'), S('v1'), S('v2')])
        elif v == 'frc': W('frc', [S('v0')])
        elif v == 'dp4': W('dp4', [S('v0'), S('v1')])
        elif v == 'dp3': W('dp3', [S('v0'), S('v1')])
        elif v == 'dp2add':
            o2 = operand(f, 'v2'); c2 = comp(o2.swz, 0)
            W('dp2add', [S('v0'), S('v1'), self.src(o2, [c2] * 4)])
        elif v == 'sge': W('sge', [S('v0'), S('v1')])
        elif v == 'sgt': W('slt', [S('v1'), S('v0')])
        elif v in ('seq', 'sne'):
            # a==b : -|a-b|>=0
            t = self.tmp(); self.emit_op('add', 'r%d' % t, [S('v0'), self._negsrc(S('v1'))], False, 15)
            one, zero = self.K(1, 4), self.K(0, 4)
            W('cmp', [('-r%d.xyzw_abs' % t, None), one if v == 'seq' else zero, zero if v == 'seq' else one])
            self.rel(t)
        elif v == 'floor':
            t = self.tmp(); self.emit_op('frc', 'r%d' % t, [S('v0')], False, 15)
            W('add', [S('v0'), ('-r%d.xyzw' % t, None)]); self.rel(t)
        elif v == 'trunc':
            t = self.tmp(); u = self.tmp()
            a = S('v0'); s, cr = a; pos = s[1:] if s.startswith('-') else s
            absx = (pos if pos.endswith('_abs') else pos + '_abs', cr)
            self.emit_op('frc', 'r%d' % t, [absx], False, 15)
            self.emit_op('add', 'r%d' % u, [absx, ('-r%d.xyzw' % t, None)], False, 15)
            W('cmp', [a, ('r%d.xyzw' % u, None), ('-r%d.xyzw' % u, None)]); self.rel(t); self.rel(u)
        elif v == 'cndge': W('cmp', [S('v0'), S('v1'), S('v2')])
        elif v == 'cndgt': W('cmp', [self._negsrc(S('v0')), S('v2'), S('v1')])
        elif v == 'cndeq': W('cmp', [self._negabs(S('v0')), S('v1'), S('v2')])
        elif v == 'max4':
            o = operand(f, 'v0'); cs = [comp(o.swz, l) for l in range(4)]
            a = self.src(o, cs)[0]
            base = a.split('.')[0].lstrip('-'); sw = a.split('.')[1]
            t = self.tmp()
            self.emit_op('max', 'r%d' % t, [(a.replace(sw, sw[0] + sw[0] + sw[0] + sw[0]), self.src(o, cs)[1]), self._sw1(a, 1)], False, 1)
            raise Reject('max4 non implementato')
        elif v.startswith('kill_'):
            self.kill_vector(f, v)
            # risultato: 1/0 per lane (killres); scrivi se la maschera lo richiede
            if vm: raise Reject('kill vettoriale con scrittura dest')
        elif v == 'dst': W('dst', [S('v0'), S('v1')])
        elif v == 'cube':
            # come XenosRecomp (UNDERWORLD): direzione = src0.zwx salvata a parte; risultato (0,0,0,indice); tfetchCube usa la direzione
            o = operand(f, 'v0'); cs = [comp(o.swz, l) for l in range(4)]
            k = self.ncube; self.ncube += 1
            td = self.tmp_fresh(); self.emit_op_raw('mov', 'r%d' % td, [self.src(o, [cs[2], cs[3], cs[0], cs[0]])], False, 7)
            self.cube_dirs[k] = td
            rk = self.defreg((0, 0, 0, k))
            W('mov', [('c%d.xyzw' % rk, 'c%d' % rk)])
            if not export: self.cube_of_reg[dst_reg] = k
        elif v in ('setp_eq_push', 'setp_ne_push', 'setp_gt_push', 'setp_ge_push'):
            # p0 = src0.w == 0 && src1.w <op> 0 ; risultato = p0 ? 0 : src0 + 1
            o0, o1 = operand(f, 'v0'), operand(f, 'v1')
            a = self.src(o0, [comp(o0.swz, 3)] * 4); b = self.src(o1, [comp(o1.swz, 3)] * 4)
            one, zero = self.K(1, 4), self.K(0, 4)
            t1 = self.tmp(); t2 = self.tmp()
            self.emit_op_raw('cmp', 'r%d' % t1, [self._negabs(a), one, zero], False, 1)
            if v == 'setp_eq_push': self.emit_op_raw('cmp', 'r%d' % t2, [self._negabs(b), one, zero], False, 1)
            elif v == 'setp_ne_push': self.emit_op_raw('cmp', 'r%d' % t2, [self._negabs(b), zero, one], False, 1)
            elif v == 'setp_gt_push': self.emit_op_raw('cmp', 'r%d' % t2, [self._negsrc(b), zero, one], False, 1)
            else: self.emit_op_raw('cmp', 'r%d' % t2, [b, one, zero], False, 1)
            self.emit('mul r%d.x, r%d.x, r%d.x' % (t1, t1, t2))
            t3 = self.tmp(); self.emit_op_raw('add', 'r%d' % t3, [S('v0'), one], False, 15)
            self.emit('add r%d.x, -r%d.x, %s.x' % (t2, t1, self.const1(0.5)))
            W('cmp', [('r%d.xxxx' % t2, None), ('r%d' % t3, None), zero])
            self.emit_op('mov', 'r%d' % self.t_pf, [('r%d.xxxx' % t1, None)], False, 1)
            self.rel(t1); self.rel(t2); self.rel(t3)
        else:
            raise Reject('vettoriale non supportato: %s' % v)
        if not export: self.mark_written(dst_reg, vm)
        else: self.exp_written[dst_reg] = self.exp_written.get(dst_reg, 0) | vm

    def _sw1(self, a, i): raise Reject('sw1')

    def _negsrc(self, t):
        s, cr = t
        return (s[1:] if s.startswith('-') else '-' + s, cr)

    def kill_vector(self, f, v):
        if self.guard is not None: raise Reject('kill predicato')
        a = self.lanes_src(f, 'v0'); b = self.lanes_src(f, 'v1')
        t = self.tmp(); u = self.tmp()
        zero, one = self.K(0, 4), self.K(1, 4)
        if v == 'kill_gt': self.emit_op('slt', 'r%d' % t, [b, a], False, 15)
        elif v == 'kill_ge': self.emit_op('sge', 'r%d' % t, [a, b], False, 15)
        elif v in ('kill_eq', 'kill_ne'):
            self.emit_op('add', 'r%d' % u, [a, self._negsrc(b)], False, 15)
            self.emit_op('cmp', 'r%d' % t, [('-r%d.xyzw_abs' % u, None), one if v == 'kill_eq' else zero, zero if v == 'kill_eq' else one], False, 15)
        else: raise Reject(v)
        self.emit('max r%d.x, r%d.x, r%d.y' % (t, t, t)); self.emit('max r%d.x, r%d.x, r%d.z' % (t, t, t)); self.emit('max r%d.x, r%d.x, r%d.w' % (t, t, t))
        self.do_texkill(t)
        self.rel(t); self.rel(u)

    def alu_setp(self, f, pred, v, sc):
        raise Reject('setp (predicato)')

    def need_pf(self): raise Reject('predicato p0')

    # ------------------------------------------------------------------ fetch
    def fetch(self, d0, d1, d2, pred):
        saved = self.guard; held = []
        if bits(d1, 31, 1):
            # Xenos: fetch predicato (d1 bit 31), condizione = predCondition (d2 bit 31, shader_code.h di XenosRecomp)
            g = self.psel(bits(d2, 31, 1)); held.append(g)
            if saved is not None: self.emit('min r%d.x, r%d.x, r%d.x' % (g, g, saved))
            self.guard = g
        try:
            self.fetch_body(d0, d1, d2)
        finally:
            self.guard = saved
            for t in held: self.rel(t)

    def fetch_body(self, d0, d1, d2):
        opc = bits(d0, 0, 5)
        if opc not in (1,): raise Reject('fetch opcode %d' % opc)
        src, dst, cidx = bits(d0, 5, 6), bits(d0, 12, 6), bits(d0, 20, 5)
        sw = bits(d0, 26, 6); dsw = bits(d1, 0, 12); dim = bits(d2, 14, 2)
        offx = bits(d2, 16, 5); offy = bits(d2, 21, 5)
        if dim == 2: raise Reject('fetch 3D')
        if dim == 0: raise Reject('fetch 1D')
        if offx or offy: raise Reject('offset fetch')
        if bits(d1, 29, 1): raise Reject('fetch con LOD da registro')
        c = self.sh.samplers.get(cidx)
        name = c['name'] if c else 's%d' % cidx
        pcr = self.samp_fn(name, cidx) if self.samp_fn else cidx
        if pcr is None: raise Reject('sampler senza corrispondente PC: %s' % name)
        coords = [(sw >> (2 * i)) & 3 for i in range(3)]
        dsws = [(dsw >> (3 * i)) & 7 for i in range(4)]
        t = self.tmp()
        if dim == 3:
            # tfetchCube (XenosRecomp): direzione salvata dal CUBE che ha scritto il registro sorgente
            k = self.cube_of_reg.get(src)
            if k is None:
                # il registro delle coordinate e' derivato (mad xy*1/ma+1.5): XenosRecomp legge l'indice a runtime dalla 3a coordinata;
                # qui si usa l'ultimo CUBE emesso (sempre il caso con un solo CUBE prima del fetch)
                if not self.ncube: raise Reject('fetch cube senza CUBE')
                k = self.ncube - 1
                if self.ncube > 1: self.notes.append('fetch cube: indice preso dall\'ultimo CUBE (%d CUBE)' % self.ncube)
            if self.samp_dtype.get(pcr, 'cube') != 'cube': raise Reject('sampler usato come 2D e cube')
            self.samplers[pcr] = name; self.samp_dtype[pcr] = 'cube'
            self.emit('texld r%d, r%d.xyzz, s%d' % (t, self.cube_dirs[k], pcr))
        else:
            if self.samp_dtype.get(pcr, '2d') != '2d': raise Reject('sampler usato come 2D e cube')
            self.samplers[pcr] = name; self.samp_dtype[pcr] = '2d'
            nc = 2
            self.note_read(src, coords[:nc])
            sws = ''.join(XYZW[coords[min(i, nc - 1)]] for i in range(4))
            self.emit('texld r%d, r%d.%s, s%d' % (t, src, sws, pcr))
        if dim != 3 and pcr in self.opts.get('alpha1', ()):
            # texture DXT1 su Xbox (alfa 1) ricodificata DXT5 sul PC con alfa diverso (es. web_cutout): alfa come Xbox
            self.emit('mov r%d.w, %s.x' % (t, self.const1(1)))
            self.notes.append('alfa forzato a 1 su s%d %s' % (pcr, name))
        if dim == 3: pass
        elif pcr in self.opts.get('dxn', ()):
            # texture Xbox DXN -> PC DXT5 (R = x, G = 255, B = 0, A = y): y e' nel canale alfa
            self.emit('mov r%d.y, r%d.w' % (t, t))
            self.notes.append('DXN (y da alfa) su s%d %s' % (pcr, name))
            if pcr in self.opts.get('dxn_full', ()):
                # Giro 6: lo shader legge anche .z/.w del fetch (es. mat 20323: swizzle xwy): Xbox DXN = (x, y, 0, 1) -> ripristina z = 0, w = 1
                self.emit('mov r%d.z, %s.x' % (t, self.const1(0)))
                self.emit('mov r%d.w, %s.x' % (t, self.const1(1)))
                self.notes.append('DXN completo (z=0, w=1) su s%d %s' % (pcr, name))
        elif '_Normal_' in name or name.startswith('p_default_Normal'):
            # normal map PC (DXN convertito): x = R, y = A*G (verificato sulle coppie base)
            self.emit('mul r%d.y, r%d.w, r%d.y' % (t, t, t))
            self.notes.append('normal map fix su %s' % name)
        # scrivi lane per lane secondo dsw
        groups = {}
        for i in range(4):
            s = dsws[i]
            if s <= 3: groups.setdefault('t', []).append((i, s))
            elif s == 4: groups.setdefault('0', []).append((i, 0))
            elif s == 5: groups.setdefault('1', []).append((i, 1))
        if 't' in groups:
            mask = sum(1 << i for i, s in groups['t'])
            swz = [0, 0, 0, 0]
            for i, s in groups['t']: swz[i] = s
            self.emit_op('mov', 'r%d' % dst, [('r%d.%s' % (t, ''.join(XYZW[x] for x in swz)), None)], False, mask)
            self.mark_written(dst, mask)
        for key, val in (('0', 0), ('1', 1)):
            if key in groups:
                mask = sum(1 << i for i, _ in groups[key])
                self.emit_op('mov', 'r%d' % dst, [self.K(val, 4)], False, mask)
                self.mark_written(dst, mask)
        self.rel(t)

    # ------------------------------------------------------------------ flusso
    def run(self):
        sh = self.sh
        cfs, limit = decode_cf(sh.code)
        self.emit('mov r%d.x, %s.x' % (self.t_pf, self.const1(0)))
        # regioni: [(fine_cf, attiva)] per cond_jmp statici
        skip_until = None           # indice cf fino a cui si salta (esclusivo)
        stop = False
        guard_skip = False
        self.cf_mark = {}
        for r in cfs:
            k = r['k']
            self.cf_mark.setdefault(k, len(self.out))
            if skip_until is not None and k >= skip_until: skip_until = None
            if stop: break
            op = r['op']
            if op == 0 or op == 12 or op == 15:
                continue
            if skip_until is not None:
                if op in EXEC_FAMILY and op in (2, 4, 6, 14): pass
                continue
            while self.regions and self.regions[-1][0] <= k:
                _, t = self.regions.pop(); self.rel(t)
            rg = self.regions[-1][1] if self.regions else None
            if op == 11 and r['direction']: raise Reject('cond_jmp all\'indietro (ciclo)')
            if op == 11 and r['uncond']:
                skip_until = r['addr']; continue
            if op == 11 and r['pred']:
                # salto se p0 == cond: la regione [k+1, addr) si esegue solo se p0 != cond (valutato qui)
                t = self.psel(1 - r['cond'])
                if rg is not None: self.emit('min r%d.x, r%d.x, r%d.x' % (t, t, rg))
                if self.regions and r['addr'] > self.regions[-1][0]: raise Reject('regioni predicate non annidate')
                self.regions.append((r['addr'], t)); continue
            if op == 11:
                bv = self.bools.get(r['bool'])
                if bv is None: raise Reject('bool %d non definito (cond_jmp)' % r['bool'])
                # salta alla destinazione se (bool==cond)?  in XenosRecomp: if (!(bool cond)) { regione } => la regione si esegue se bool != cond
                taken = bool(bv) == bool(r['cond'])
                if taken: skip_until = r['addr']
                continue
            if op in (7, 8, 9, 10): raise Reject('loop/call/return')
            if op in EXEC_FAMILY:
                pred_clause = None
                if op in (3, 4, 13, 14):
                    bv = self.bools.get(r['bool'])
                    if bv is None: raise Reject('bool %d non definito (cond_exec)' % r['bool'])
                    if bool(bv) != bool(r['cond']):
                        if op in (4, 14): stop = True
                        continue
                held = None
                self.guard = rg
                if op in (5, 6):
                    held = self.psel(r['pcond'])
                    if rg is not None: self.emit('min r%d.x, r%d.x, r%d.x' % (held, held, rg))
                    self.guard = held
                seq = r['seq']
                for i in range(r['count']):
                    s = r['addr'] + i
                    d0, d1, d2 = sh.code[3 * s:3 * s + 3]
                    if seq & 1: self.fetch(d0, d1, d2, None)
                    else: self.alu(alu_decode(d0, d1, d2), None)
                    seq >>= 2
                if held is not None: self.rel(held)
                self.guard = None
                if op in (2, 4, 6, 14): stop = True
        return self

    # ------------------------------------------------------------------ assemblaggio testo
    def finish(self):
        sh = self.sh
        gather_lines = []
        pm = self.opts.get('pmap')
        for j, (t, cs) in sorted(self.gather.items()):
            for cc in sorted(cs):
                m = pm[(j, cc)]
                if m[0] == 'pc':
                    gather_lines.append('mov r%d.%s, c%d.%s' % (t, XYZW[cc], 100 + m[1], XYZW[m[2]])); self.used_c[100 + m[1]] = ('MaterialParams', m[1])
                else:
                    gather_lines.append('mov r%d.%s, c%d.x' % (t, XYZW[cc], self.defreg((m[1],) * 4)))
        if self.face_needed: self.defreg((-1.0, 1.0, 0.0, 0.0))
        lines = ['ps_3_0']
        for r in sorted(self.defs):
            lines.append('def c%d, %s' % (r, ', '.join('%.9g' % x for x in self.defs[r])))
        # input: ordina color poi texcoord
        order = sorted(self.inputs, key=lambda k: (0 if k[0] == 10 else 1, k[1]))
        vreg = {}
        for n, key in enumerate(order):
            usage, idx = key
            uname = {10: 'color', 5: 'texcoord'}.get(usage)
            if uname is None: raise Reject('interpolatore usage %d non gestito' % usage)
            if uname == 'color' and idx > 1: raise Reject('color%d' % idx)
            vreg[key] = n
            comps = sorted(self.inputs[key])
            lines.append('dcl_%s%s v%d.%s' % (uname, idx if idx else '', n, ''.join(XYZW[c] for c in comps)))
        if self.face_needed and not self.sign_only: self.vpos_comps.add(0)
        if self.face_needed and self.sign_only: self.defreg((-1.0, 1.0, 0.0, 0.0))
        if self.vpos_used:
            vm_ = ''.join(XYZW[c] for c in sorted(self.vpos_comps))
            lines.append('dcl_position vPos.%s' % vm_)
        if self.face_needed: lines.append('dcl_position vFace')
        for pcr in sorted(self.samplers):
            lines.append('dcl_%s s%d' % (self.samp_dtype.get(pcr, '2d'), pcr))
        # prologo: copia gli interpolatori usati nei registri temp Xenos
        for reg, key in sorted(self.interp.items()):
            if key in self.inputs:
                comps = sorted(self.inputs[key])
                m = ''.join(XYZW[c] for c in comps)
                lines.append('mov r%d.%s, v%d.%s' % (reg, m, vreg[key], m))
        if self.face_needed and self.sign_only:
            fk = self.defreg((-1.0, 1.0, 0.0, 0.0))
            lines.append('cmp r%d.x, vFace, c%d.x, c%d.y' % (sh.svpos_reg, fk, fk))
        if self.vpos_used:
            vm_ = ''.join(XYZW[c] for c in sorted(self.vpos_comps))
            if self.face_needed and not self.sign_only:
                fk = self.defreg((-1.0, 1.0, 0.0, 0.0))
                lines.append('cmp r%d.x, vFace, c%d.x, c%d.y' % (sh.svpos_reg, fk, fk))
                lines.append('mul r%d.x, r%d.x, vPos.x' % (sh.svpos_reg, sh.svpos_reg))
                rest = vm_.replace('x', '')
                if rest: lines.append('mov r%d.%s, vPos.%s' % (sh.svpos_reg, rest, rest))
            else:
                lines.append('mov r%d.%s, vPos.%s' % (sh.svpos_reg, vm_, vm_))
        lines += gather_lines
        res_out_start = sum(1 for l in lines[1:] if l.strip())       # indice (fra le istruzioni) della prima riga di self.out
        lines += self.out
        text = '\n'.join(lines) + '\n'
        prog = sm3asm.parse_text(text)
        if not self.opts.get('noopt'):
            sm3opt.optimize(prog)
        text = sm3asm.format_program(prog)
        res = Result()
        res.prog = prog; res.text = text; res.notes = self.notes; res.ntemps = self.maxtemp
        res.cf_mark = dict(self.cf_mark); res.out_start = res_out_start; res.nout = len(self.out); res.nreg = self.nreg
        res.cfs = decode_cf(sh.code)[0]
        defs = {}
        for ins in prog.instrs():
            if ins.op == 'def': defs[ins.ops[0].num] = tuple(struct.unpack('<f', struct.pack('<I', u))[0] for u in ins.imm)
        stype = sm3opt.analyse(prog)
        used_c = set(); used_s = {}
        res.inputs = {}
        for ins in prog.instrs():
            if ins.op == 'dcl':
                o = ins.ops[0]
                if o.rtype == sm3asm.RT_INPUT: res.inputs[(ins.usage & 31, (ins.usage >> 16) & 15)] = [c for c in range(4) if o.wm >> c & 1]
                continue
            if ins.op in ('def', 'defi', 'defb'): continue
            for o in ins.ops:
                if not o.isdst and o.rtype == sm3asm.RT_CONST: used_c.add(o.num)
                if o.rtype == sm3asm.RT_SAMPLER: used_s[o.num] = self.samplers.get(o.num)
        res.consts = {r: self.used_c[r] for r in used_c if r in self.used_c}
        res.defs = {r: v for r, v in defs.items()}
        res.samplers = used_s
        res.ninstr = len([i for i in prog.instrs() if i.op not in ('dcl', 'def', 'defi', 'defb')])
        res.exports = dict(self.exp_written)
        return res


def translate(blob, consts, bools=None, samp=None, opts=None):
    t = Tr(blob, consts, bools, samp, opts)
    t.run()
    return t.finish()
