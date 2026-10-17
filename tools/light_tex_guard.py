#!/usr/bin/env python3
"""light_tex_guard.py - guardia sul puntatore texture della luce proiettata in FUN_0050a5f0 (crash 0x5076fa, X+0x418).

Fatti (work/ws/codefirst/REPORT_x418.md, REPORT_task2_x418_xbox_map.md):
  X+0x418 e' scritto dal costruttore/FinalizeInitialization (0x50afb0) come  (byte X[0xc50] != 0) ? X[0xc54] : 0  (cdc::XenonLightResource::
  FinalizeInitialization sull'Xbox: lo stesso schema, e nessuno scrive il campo dall'esterno). Nei dump PC 2 luci su 36 hanno invece un puntatore P a una
  vista di render (vtable 0x849a28, [vt+0x30]==0) e FUN_005076e0 fa `mov edx,[P]; mov eax,[edx+0x30]; call eax` -> AV 0x5076fa.
  FUN_005076e0 GESTISCE gia' P==0 (usa la vista di default [ctx+0xfde4], come l'Xbox con la texture di default): il caso nullo non va aggirato.

Patch: i DUE punti che leggono il campo in FUN_0050a5f0 (0x50a645 e 0x50a683, `mov edx,[eax+0x418]` = 8B 90 18 04 00 00, eax = X) diventano
  E8 <rel32> 90   (call guardia; nop)
La guardia (caverna in coda a .text, VA 0x83DE60) restituisce in EDX il puntatore da usare e preserva tutti gli altri registri:
  edx = [X+0x418]; atteso = (byte X[0xc50] != 0) ? X[0xc54] : 0
  se edx == atteso  oppure edx == 0           -> invariato
  altrimenti valida P: vt=[P] in [0x401000,0xCD5000), [vt+0x30] e [vt+0x34] in .text [0x401000,0x83E000)
     valido  -> invariato (contatore 'valid')
     non valido -> [X+0x418] = atteso ; edx = atteso ; contatore 'fix' ; salva P e X (ultimo)
Contatori (leggibili da fuori) a VA 0x83DE20, 8 dword: 'LTG1', calls, fix, valid, last_bad_P, last_X, 0, 0.
Poiche' i contatori stanno in .text, la sezione diventa scrivibile (IMAGE_SCN_MEM_WRITE nelle characteristics di .text): stessa tecnica della sezione .tap.
Compatibile e indipendente da fmod_init_guard.py (altra caverna 0x83DE00..0x83DE0D): applicabile in qualsiasi ordine.

Uso:  tools/venv/bin/python -I tools/light_tex_guard.py IN.exe OUT.exe     (applica e verifica byte per byte)
      tools/venv/bin/python -I tools/light_tex_guard.py --check IN.exe      (originale / patchato / DIVERSO)
      tools/venv/bin/python -I tools/light_tex_guard.py --selftest           (esegue la guardia su memoria sintetica: 9 casi)
Non scrive mai su IN.exe. Rifiuta se i byte attesi non coincidono."""
import sys, struct, hashlib

IB = 0x400000
SITES = (0x50A645, 0x50A683)
ORIG = bytes.fromhex('8b9018040000')
CNT = 0x83DE20
GUARD = 0x83DE60
MAGIC = 0x3147544C            # 'LTG1'
TEXT_LO, TEXT_HI, IMG_HI = 0x401000, 0x83E000, 0xCD5000


class Asm:
    def __init__(self, base):
        self.base, self.b, self.lab, self.fix = base, bytearray(), {}, []
    def raw(self, h): self.b += bytes.fromhex(h.replace(' ', ''))
    def label(self, n): self.lab[n] = len(self.b)
    def jcc(self, op, n): self.b += bytes([op, 0]); self.fix.append((len(self.b) - 1, n))
    def d32(self, v): self.b += struct.pack('<I', v)
    def done(self):
        for pos, n in self.fix:
            rel = self.lab[n] - (pos + 1); assert -128 <= rel < 128, (n, rel); self.b[pos] = rel & 0xFF
        return bytes(self.b)


def guard_code():
    a = Asm(GUARD); c = lambda i: CNT + 4 * i
    a.raw('8b 90 18 04 00 00')                       # mov edx,[eax+0x418]
    a.raw('ff 05'); a.d32(c(1))                      # inc dword [calls]
    a.raw('51')                                      # push ecx
    a.raw('31 c9')                                   # xor ecx,ecx
    a.raw('80 b8 50 0c 00 00 00')                    # cmp byte [eax+0xc50],0
    a.jcc(0x74, 'noc54')                             # je
    a.raw('8b 88 54 0c 00 00')                       # mov ecx,[eax+0xc54]
    a.label('noc54')
    a.raw('39 ca')                                   # cmp edx,ecx
    a.jcc(0x74, 'ok')                                # je ok
    a.raw('85 d2')                                   # test edx,edx
    a.jcc(0x74, 'ok')                                # je ok  (P nullo: lo gestisce FUN_005076e0)
    a.raw('50')                                      # push eax (X)
    a.raw('8b 02')                                   # mov eax,[edx]        vtable
    a.raw('3d'); a.d32(TEXT_LO); a.jcc(0x72, 'bad')  # cmp eax,0x401000 ; jb bad
    a.raw('3d'); a.d32(IMG_HI); a.jcc(0x73, 'bad')   # cmp eax,0xCD5000 ; jae bad
    a.raw('8b 40 30')                                # mov eax,[eax+0x30]
    a.raw('3d'); a.d32(TEXT_LO); a.jcc(0x72, 'bad')
    a.raw('3d'); a.d32(TEXT_HI); a.jcc(0x73, 'bad')
    a.raw('8b 02')                                   # mov eax,[edx]
    a.raw('8b 40 34')                                # mov eax,[eax+0x34]
    a.raw('3d'); a.d32(TEXT_LO); a.jcc(0x72, 'bad')
    a.raw('3d'); a.d32(TEXT_HI); a.jcc(0x73, 'bad')
    a.raw('58')                                      # pop eax
    a.raw('ff 05'); a.d32(c(3))                      # inc dword [valid]
    a.jcc(0xEB, 'ok')                                # jmp ok
    a.label('bad')
    a.raw('58')                                      # pop eax (X)
    a.raw('89 15'); a.d32(c(4))                      # mov [last_bad_P],edx
    a.raw('a3'); a.d32(c(5))                         # mov [last_X],eax
    a.raw('89 88 18 04 00 00')                       # mov [eax+0x418],ecx   (valore di FinalizeInitialization)
    a.raw('89 ca')                                   # mov edx,ecx
    a.raw('ff 05'); a.d32(c(2))                      # inc dword [fix]
    a.label('ok')
    a.raw('59')                                      # pop ecx
    a.raw('c3')                                      # ret
    return a.done()


def counters_init(): return struct.pack('<8I', MAGIC, 0, 0, 0, 0, 0, 0, 0)


def sec_hdrs(d):
    pe = struct.unpack_from('<I', d, 0x3c)[0]
    n = struct.unpack_from('<H', d, pe + 6)[0]; osz = struct.unpack_from('<H', d, pe + 20)[0]
    base = struct.unpack_from('<I', d, pe + 52)[0]
    out = []
    for i in range(n):
        o = pe + 24 + osz + 40 * i
        vs, va, rs, ro = struct.unpack_from('<IIII', d, o + 8)
        out.append(dict(o=o, va=base + va, vs=vs, ro=ro, rs=rs, name=d[o:o + 8].rstrip(b'\0').decode(), ch=struct.unpack_from('<I', d, o + 36)[0]))
    return out


def text_hdr(d):
    return next(s for s in sec_hdrs(d) if s['name'] == '.text')


def va2off(d, va):
    t = text_hdr(d)
    assert t['va'] <= va < t['va'] + min(t['vs'], t['rs']), hex(va)
    return t['ro'] + va - t['va']


def site_patch(site): return bytes([0xE8]) + struct.pack('<i', GUARD - (site + 5)) + b'\x90'


def regions(d):
    g = guard_code()
    return [(va2off(d, s), 6, ORIG, site_patch(s)) for s in SITES] + [(va2off(d, CNT), 32, bytes(32), counters_init()), (va2off(d, GUARD), len(g), bytes(len(g)), g)]


def state(d):
    r = regions(d); t = text_hdr(d)
    if all(d[o:o + n] == orig for o, n, orig, new in r) and not t['ch'] & 0x80000000: return 'originale'
    if all(d[o:o + n] == new for o, n, orig, new in r) and t['ch'] & 0x80000000: return 'patchato'
    return 'DIVERSO (%s)' % ', '.join('%#x:%s' % (o, d[o:o + min(n, 8)].hex()) for o, n, _, _ in r)


def apply(d):
    if state(d) != 'originale': raise SystemExit('rifiuto: ' + state(d))
    b = bytearray(d)
    for o, n, orig, new in regions(d): b[o:o + n] = new
    t = text_hdr(d); struct.pack_into('<I', b, t['o'] + 36, t['ch'] | 0x80000000)
    return bytes(b)


# ------------------------------------------------------------------------------------------------ verifica
def verify(orig, new):
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    t = text_hdr(orig)
    allowed = set(); [allowed.update(range(o, o + n)) for o, n, _, _ in regions(orig)]; allowed.update(range(t['o'] + 36, t['o'] + 40))
    diff = [i for i in range(len(orig)) if orig[i] != new[i]]
    assert len(orig) == len(new) and set(diff) <= allowed, 'byte modificati fuori dalle regioni previste'
    for s in SITES:                                   # siti: call guardia; nop ; istruzione seguente intatta
        o = va2off(new, s); ins = list(md.disasm(new[o:o + 8], s))
        assert ins[0].mnemonic == 'call' and int(ins[0].op_str, 16) == GUARD and ins[1].mnemonic == 'nop', ins
        pre = list(md.disasm(orig[o:o + 6], s)); assert (pre[0].mnemonic, pre[0].op_str) == ('mov', 'edx, dword ptr [eax + 0x418]'), pre
        assert new[o + 6:o + 8] == orig[o + 6:o + 8] and new[o - 2:o] == orig[o - 2:o]
    g = guard_code(); o = va2off(new, GUARD)
    dis = list(md.disasm(new[o:o + len(g)], GUARD))
    assert sum(i.size for i in dis) == len(g)
    # nessuna istruzione scrive registri diversi da edx/eax/ecx (questi ultimi ripristinati) e tutti i salti restano nella guardia
    for i in dis:
        if i.mnemonic in ('jmp', 'je', 'jb', 'jae'): assert GUARD <= int(i.op_str, 16) < GUARD + len(g), i
    assert dis[-1].mnemonic == 'ret' and dis[-2].mnemonic == 'pop' and dis[-2].op_str == 'ecx'
    return len(diff), [(hex(i.address), i.mnemonic, i.op_str) for i in dis]


class Mini:
    """interprete del sottoinsieme x86 usato dalla guardia (verifica funzionale offline, senza emulatore esterno)."""
    def __init__(self, mem): self.m = dict(mem); self.r = dict(eax=0, ecx=0, edx=0, esp=0x1000)
    def rd(self, a):
        if a not in self.m: raise KeyError('lettura non mappata %#x' % a)
        return self.m[a]
    def val(self, s):
        s = s.strip()
        if s.startswith('dword ptr ['): return self.rd(self.ea(s[11:-1]))
        if s.startswith('byte ptr ['): return self.rd(self.ea(s[10:-1])) & 0xFF
        if s.startswith('['): return self.rd(self.ea(s[1:-1]))
        if s in self.r: return self.r[s]
        return int(s, 0)
    def ea(self, e):
        e = e.replace(' ', '')
        for rn in ('eax', 'ecx', 'edx'):
            if e.startswith(rn): return (self.r[rn] + (int(e[len(rn) + 1:], 0) if len(e) > len(rn) else 0)) & 0xFFFFFFFF
        return int(e, 0)
    def run(self, code, base):
        import capstone
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        ins = {i.address: i for i in md.disasm(code, base)}; pc = base; stack = []; fl = None; self.r['esp'] = 0x2000
        for _ in range(500):
            i = ins[pc]; m, o = i.mnemonic, [x.strip() for x in i.op_str.split(',', 1)]; pc += i.size
            if m == 'mov':
                v = self.val(o[1])
                if o[0] in self.r: self.r[o[0]] = v
                else: self.m[self.ea(o[0].split('[', 1)[1][:-1])] = v
            elif m == 'inc': a = self.ea(o[0].split('[', 1)[1][:-1]); self.m[a] = self.m.get(a, 0) + 1
            elif m == 'push': stack.append(self.val(o[0]))
            elif m == 'pop': self.r[o[0]] = stack.pop()
            elif m == 'xor': self.r[o[0]] = self.val(o[0]) ^ self.val(o[1])
            elif m == 'cmp': fl = (self.val(o[0]), self.val(o[1]))
            elif m == 'test': fl = (self.val(o[0]) & self.val(o[1]), 0)
            elif m in ('je', 'jb', 'jae', 'jmp'):
                t = int(o[0], 16)
                a, b = fl if fl else (0, 0)
                if m == 'jmp' or (m == 'je' and a == b) or (m == 'jb' and a < b) or (m == 'jae' and a >= b): pc = t
            elif m == 'ret': return
            else: raise NotImplementedError(i)
        raise RuntimeError('troppe istruzioni')


def selftest():
    code = guard_code(); VT_OK, VT_RV, FN = 0x850000, 0x849a28, 0x500000
    def world(p, c50, c54, field):
        mem = {}
        X = 0x30000000
        mem[X + 0x418] = field; mem[X + 0xc50] = c50; mem[X + 0xc54] = c54
        mem.update({CNT + 4 * k: (MAGIC if k == 0 else 0) for k in range(8)})
        mem[VT_OK + 0x30] = FN; mem[VT_OK + 0x34] = FN + 0x10                      # vtable texture valida
        mem[VT_RV + 0x30] = 0; mem[VT_RV + 0x34] = FN                              # RenderView: [vt+0x30]==0
        mem[0x18a47030] = VT_RV; mem[0x185c9000] = VT_OK; mem[0x40000000] = 0x1234 # P=RV ; texture legittima ; P con vtable fuori immagine
        mem[0x41000000] = VT_OK + 0x1000; mem[VT_OK + 0x1000 + 0x30] = FN; mem[VT_OK + 0x1000 + 0x34] = 0   # [vt+0x34]==0
        return X, mem
    cases = [  # (nome, field, c50, c54, atteso edx, fix, valid)
        ('invariante rispettata (flag 1)', 0x185c9000, 1, 0x185c9000, 0x185c9000, 0, 0),
        ('invariante rispettata (flag 0, campo 0)', 0, 0, 0x185c9000, 0, 0, 0),
        ('P nullo con flag 1: invariato (lo gestisce FUN_005076e0)', 0, 1, 0x185c9000, 0, 0, 0),
        ('P = RenderView (vt+0x30==0), flag 1 -> ripristino', 0x18a47030, 1, 0x185c9000, 0x185c9000, 1, 0),
        ('P = RenderView, flag 0 -> ripristino a 0', 0x18a47030, 0, 0x185c9000, 0, 1, 0),
        ('P con vtable fuori immagine -> ripristino', 0x40000000, 1, 0x185c9000, 0x185c9000, 1, 0),
        ('P con [vt+0x34]==0 -> ripristino', 0x41000000, 1, 0x185c9000, 0x185c9000, 1, 0),
        ('P diverso ma valido -> invariato, contato', 0x185c9000, 1, 0, 0x185c9000, 0, 1),
    ]
    for name, field, c50, c54, want, nfix, nval in cases:
        X, mem = world(0, c50, c54, field); mi = Mini(mem); mi.r.update(eax=X, ecx=0xCAFE, edx=0xBEEF); mi.run(code, GUARD)
        assert mi.r['edx'] == want and mi.m[X + 0x418] == (want if nfix else field), (name, hex(mi.r['edx']))
        assert mi.r['eax'] == X and mi.r['ecx'] == 0xCAFE and mi.r['esp'] == 0x2000, (name, 'registri non preservati')
        assert mi.m[CNT + 8] == nfix and mi.m[CNT + 12] == nval and mi.m[CNT + 4] == 1, (name, mi.m[CNT + 8], mi.m[CNT + 12])
        if nfix: assert mi.m[CNT + 16] == field and mi.m[CNT + 20] == X
        print('  OK  %s' % name)
    print('selftest: %d casi OK, guardia %d byte' % (len(cases), len(code)))


def main():
    a = sys.argv[1:]
    if a and a[0] == '--selftest': selftest(); return
    if a and a[0] == '--check': print(state(open(a[1], 'rb').read())); return
    if len(a) != 2: raise SystemExit(__doc__)
    d = open(a[0], 'rb').read(); n = apply(d); nd, dis = verify(d, n)
    selftest()
    open(a[1], 'wb').write(n)
    print('scritto %s: %d byte modificati (+4 di characteristics .text); in md5 %s out md5 %s' % (a[1], nd, hashlib.md5(d).hexdigest()[:8], hashlib.md5(n).hexdigest()[:8]))
    for x in dis: print('  %s  %-5s %s' % x)


if __name__ == '__main__':
    main()
