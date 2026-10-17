#!/usr/bin/env python3
"""soundplex_guard.py - guardia sul dispatcher dei nodi SoundPlex FUN_005920b0 (AV 0x592218 `fld dword ptr [ecx]`, ecx=[edi+4]=0, prova utente B89 17/10/2026).

Fatti: FUN_005920b0(node, ...) ha un loop (LAB_005920c0) e uno switch sul tipo del nodo (u32 [edi], 0..0xd). Il campo [edi+4] e' un puntatore dati
relocato; il tipo 0 (0x5921f9) lo legge con `fld [ecx]` subito dopo l'alloc di 0x1c byte, il tipo 1 con `mov eax,[edi+4]; mov esi,[eax]` (0x5920e9),
gli altri lo passano ai costruttori 0x58dfc0/0x58def0/0x590xxx/0x587xxx che lo dereferenziano. Un nodo con dati nulli e' gia' trattato dal motore come
"nessuna emissione" solo per il tipo 2 (test esplicito) e dal ramo `return 0` (0x592123: pop edi/esi/ebp; xor eax,eax; pop ebx; ret 0x10).

Patch (hook all'inizio del dispatch, 0x5920d5, 7 byte = 3 istruzioni intere `8b 07 / 33 f6 / 83 f8 0d`):
  E9 <rel32 -> caverna> 90 90
Caverna (VA 0x83DF40, dopo le altre due guardie che occupano 0x83DE00..0x83DEDF; contatori a 0x83DF00):
  mov eax,[edi] ; xor esi,esi ; calls++
  se tipo > 0xd oppure tipo in {2, 8}                -> invariato (tipo 2 ha gia' il suo controllo; tipo 8 usa [edi+4] come id, non come puntatore)
  se [edi+4] >= 0x10000                               -> invariato
  altrimenti                                          -> hits++, last_edi=edi, last_type=tipo, jmp 0x592123 (il nodo non emette nulla, come un nodo non spawnabile)
  invariato = cmp eax,0xd ; jmp 0x5920dc (la `ja` originale)
Il nodo "nullo" non fa piu' crashare il gioco e il contatore dice quanti e quale (edi, tipo). Soglia 0x10000: l'exe e' LAA, i puntatori validi sono sempre >= 0x10000.
Contatori (8 dword) a VA 0x83DF00: 'SPG1', calls, hits, last_edi, last_type, 0, 0, 0 (stessa tecnica di light_tex_guard: .text scrivibile).
Compatibile e indipendente da fmod_init_guard.py e light_tex_guard.py (altre caverne).

Uso:  tools/venv/bin/python -I tools/soundplex_guard.py IN.exe OUT.exe      (applica, verifica byte per byte, selftest)
      tools/venv/bin/python -I tools/soundplex_guard.py --check IN.exe      (originale / patchato / DIVERSO)
      tools/venv/bin/python -I tools/soundplex_guard.py --selftest
Non scrive mai su IN.exe."""
import sys, os, struct, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import light_tex_guard as L

SITE = 0x5920D5
ORIG = bytes.fromhex('8b07 33f6 83f80d'.replace(' ', ''))
BACK = 0x5920DC             # `ja 0x5923c0` originale
RET0 = 0x592123             # epilogo `return 0`
CNT = 0x83DF00
GUARD = 0x83DF40
MAGIC = 0x31475053          # 'SPG1'
THRESH = 0x10000


def guard_code():
    a = L.Asm(GUARD); c = lambda i: CNT + 4 * i
    a.raw('8b 07')                                   # mov eax,[edi]
    a.raw('33 f6')                                   # xor esi,esi
    a.raw('ff 05'); a.d32(c(1))                      # inc dword [calls]
    a.raw('83 f8 0d'); a.jcc(0x77, 'done')           # cmp eax,0xd ; ja done
    a.raw('83 f8 02'); a.jcc(0x74, 'done')           # cmp eax,2   ; je done
    a.raw('83 f8 08'); a.jcc(0x74, 'done')           # cmp eax,8   ; je done
    a.raw('51')                                      # push ecx
    a.raw('8b 4f 04')                                # mov ecx,[edi+4]
    a.raw('81 f9'); a.d32(THRESH)                    # cmp ecx,0x10000
    a.raw('59')                                      # pop ecx (non altera i flag)
    a.jcc(0x73, 'done')                              # jae done
    a.raw('ff 05'); a.d32(c(2))                      # inc dword [hits]
    a.raw('89 3d'); a.d32(c(3))                      # mov [last_edi],edi
    a.raw('a3'); a.d32(c(4))                         # mov [last_type],eax
    a.raw('e9'); a.d32((RET0 - (GUARD + len(a.b) + 4)) & 0xFFFFFFFF)   # jmp RET0
    a.label('done')
    a.raw('83 f8 0d')                                # cmp eax,0xd   (flag per la `ja` originale)
    a.raw('e9'); a.d32((BACK - (GUARD + len(a.b) + 4)) & 0xFFFFFFFF)   # jmp BACK
    return a.done()


def counters_init(): return struct.pack('<8I', MAGIC, 0, 0, 0, 0, 0, 0, 0)


def site_patch(): return bytes([0xE9]) + struct.pack('<i', GUARD - (SITE + 5)) + b'\x90\x90'


def regions(d):
    g = guard_code()
    return [(L.va2off(d, SITE), 7, ORIG, site_patch()), (L.va2off(d, CNT), 32, bytes(32), counters_init()), (L.va2off(d, GUARD), len(g), bytes(len(g)), g)]


def state(d):
    r = regions(d)
    if all(d[o:o + n] == orig for o, n, orig, new in r): return 'originale'
    if all(d[o:o + n] == new for o, n, orig, new in r): return 'patchato'
    return 'DIVERSO (%s)' % ', '.join('%#x:%s' % (o, d[o:o + min(n, 8)].hex()) for o, n, _, _ in r)


def apply(d):
    if state(d) != 'originale': raise SystemExit('rifiuto: ' + state(d))
    t = L.text_hdr(d)
    assert t['ch'] & 0x80000000, '.text deve essere gia'' scrivibile (light_tex_guard applicato)'
    b = bytearray(d)
    for o, n, orig, new in regions(d): b[o:o + n] = new
    return bytes(b)


def verify(orig, new):
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    allowed = set(); [allowed.update(range(o, o + n)) for o, n, _, _ in regions(orig)]
    diff = [i for i in range(len(orig)) if orig[i] != new[i]]
    assert len(orig) == len(new) and set(diff) <= allowed, 'byte modificati fuori dalle regioni previste'
    o = L.va2off(new, SITE); ins = list(md.disasm(new[o:o + 7], SITE))
    assert ins[0].mnemonic == 'jmp' and int(ins[0].op_str, 16) == GUARD and [i.mnemonic for i in ins[1:]] == ['nop', 'nop'], ins
    pre = [(i.mnemonic, i.op_str) for i in md.disasm(orig[o:o + 7], SITE)]
    assert pre == [('mov', 'eax, dword ptr [edi]'), ('xor', 'esi, esi'), ('cmp', 'eax, 0xd')], pre
    assert new[o + 7:o + 13] == orig[o + 7:o + 13] and bytes(md.disasm(orig[o + 7:o + 13], SITE + 7).__next__().bytes)[:2] == b'\x0f\x87'
    g = guard_code(); og = L.va2off(new, GUARD)
    dis = list(md.disasm(new[og:og + len(g)], GUARD)); assert sum(i.size for i in dis) == len(g)
    for i in dis:
        if i.mnemonic in ('je', 'ja', 'jae'): assert GUARD <= int(i.op_str, 16) < GUARD + len(g), i
        if i.mnemonic == 'jmp': assert int(i.op_str, 16) in (RET0, BACK), i
    assert dis[-1].mnemonic == 'jmp' and int(dis[-1].op_str, 16) == BACK
    return len(diff), [(hex(i.address), i.mnemonic, i.op_str) for i in dis]


class Mini:
    """interprete del sottoinsieme x86 usato dalla guardia (nessun emulatore esterno)."""
    REGS = ('eax', 'ecx', 'edx', 'esi', 'edi')
    def __init__(self, mem): self.m = dict(mem); self.r = dict(eax=0, ecx=0, edx=0, esi=0, edi=0)
    def rd(self, a):
        if a not in self.m: raise KeyError('lettura non mappata %#x' % a)
        return self.m[a]
    def ea(self, e):
        e = e.replace(' ', '')
        for rn in self.REGS:
            if e.startswith(rn): return (self.r[rn] + (int(e[len(rn) + 1:], 0) if len(e) > len(rn) else 0)) & 0xFFFFFFFF
        return int(e, 0)
    def val(self, s):
        s = s.strip()
        if s.startswith('dword ptr ['): return self.rd(self.ea(s[11:-1]))
        if s in self.r: return self.r[s]
        return int(s, 0)
    def run(self, code, base):
        import capstone
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        ins = {i.address: i for i in md.disasm(code, base)}; pc = base; stack = []; fl = (0, 0)
        for _ in range(200):
            if pc not in ins: return pc
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
            elif m in ('je', 'ja', 'jae', 'jmp'):
                t = int(o[0], 16); a, b = fl
                if m == 'jmp' or (m == 'je' and a == b) or (m == 'ja' and a > b) or (m == 'jae' and a >= b): pc = t
            else: raise NotImplementedError(i)
        raise RuntimeError('troppe istruzioni')


def selftest():
    code = guard_code(); NODE = 0x20000000
    def run(typ, data, extra=None):
        mem = {NODE: typ, NODE + 4: data, **{CNT + 4 * k: (MAGIC if k == 0 else 0) for k in range(8)}}
        mi = Mini(mem); mi.r.update(edi=NODE, ecx=0xCAFE, eax=0x1111, esi=0x2222, edx=0xBEEF); end = mi.run(code, GUARD)
        return mi, end
    cases = [  # nome, tipo, dati, uscita attesa, hits
        ('tipo 0 dati nulli -> return 0', 0, 0, RET0, 1),
        ('tipo 1 dati nulli -> return 0', 1, 0, RET0, 1),
        ('tipo 0 dati sotto soglia (0xFFFF) -> return 0', 0, 0xFFFF, RET0, 1),
        ('tipo 0 dati validi -> invariato', 0, 0x185c9000, BACK, 0),
        ('tipo 5 dati validi -> invariato', 5, 0x30000000, BACK, 0),
        ('tipo 5 dati nulli -> return 0', 5, 0, RET0, 1),
        ('tipo 2 dati nulli -> invariato (controllo proprio del motore)', 2, 0, BACK, 0),
        ('tipo 8 id piccolo -> invariato (e\' un id)', 8, 7, BACK, 0),
        ('tipo 0xd dati nulli -> return 0', 13, 0, RET0, 1),
        ('tipo 14 (fuori range) -> invariato (il default dello switch ritorna nullo)', 14, 0, BACK, 0),
        ('dati >= 0x80000000 (LAA) -> invariato', 0, 0xA0000000, BACK, 0),
    ]
    for name, typ, data, want_end, hits in cases:
        mi, end = run(typ, data)
        assert end == want_end, (name, hex(end))
        assert mi.r['ecx'] == 0xCAFE and mi.r['edx'] == 0xBEEF and mi.r['edi'] == NODE, (name, 'registri non preservati')
        assert mi.r['esi'] == 0 and mi.r['eax'] == typ, (name, 'esi/eax devono essere come dopo le istruzioni originali')
        assert mi.m[CNT + 4] == 1 and mi.m[CNT + 8] == hits, (name, mi.m[CNT + 4], mi.m[CNT + 8])
        if hits: assert mi.m[CNT + 12] == NODE and mi.m[CNT + 16] == typ
        if end == BACK:                      # le flag devono essere quelle di `cmp eax,0xd` per la `ja` originale
            a, b = (typ, 0xd); assert (a > b) == (typ > 13)
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
    print('scritto %s: %d byte modificati; in md5 %s out md5 %s' % (a[1], nd, hashlib.md5(d).hexdigest()[:8], hashlib.md5(n).hexdigest()[:8]))
    for x in dis: print('  %s  %-5s %s' % x)


if __name__ == '__main__':
    main()
