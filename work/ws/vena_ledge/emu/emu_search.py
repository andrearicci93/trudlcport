"""Traccia V: esegue in emulazione (unicorn) la ricerca del candidato 0x7296c0(game+0x980, modo) sulla memoria di un dump completo.
Memoria caricata pigramente dal dump (pagine da 4 KB); pila nuova. Solo lettura del dump.
uso: python emu_search.py DUMP MODO [--trace]"""
import sys, struct
sys.path.insert(0, 'C:/tru-port/tools')
from minidump_read import Minidump
from unicorn import *
from unicorn.x86_const import *
DUMP, MODE = sys.argv[1], int(sys.argv[2])
TRACE = '--trace' in sys.argv
D = Minidump(DUMP)
mu = Uc(UC_ARCH_X86, UC_MODE_32)
PG = 0x1000; mapped = set(); missing = []
def page_bytes(pa):
    out = bytearray(PG); hit = False
    for va, sz, off in D.ranges:
        if va < pa + PG and pa < va + sz:
            a = max(va, pa); b = min(va + sz, pa + PG)
            out[a - pa:b - pa] = D.d[off + a - va:off + b - va]; hit = True
    return bytes(out), hit
def mapp(pa):
    if pa in mapped: return
    for b, e_, _ in mu.mem_regions():
        if b <= pa <= e_: mapped.add(pa); return
    data, hit = page_bytes(pa)
    mu.mem_map(pa, PG); mu.mem_write(pa, data); mapped.add(pa)
    if not hit: missing.append(pa)
def on_unmapped(uc, access, addr, size, value, ud):
    for p in range(addr & ~0xfff, (addr + max(size, 1) + 0xfff) & ~0xfff, PG): mapp(p)
    return True
mu.hook_add(UC_HOOK_MEM_READ_UNMAPPED | UC_HOOK_MEM_WRITE_UNMAPPED | UC_HOOK_MEM_FETCH_UNMAPPED, on_unmapped)
STACK = 0x7f000000; mu.mem_map(STACK - 0x100000, 0x101000)
RET = 0x7f000800
mu.mem_write(RET, b'\xf4')
# FS: TEB del thread principale non serve se non usato; diamo una pagina vuota
TEB = 0x7e000000; mu.mem_map(TEB, 0x2000)
mu.mem_write(TEB + 0x18, struct.pack('<I', TEB))
GDT = 0x7d000000; mu.mem_map(GDT, 0x1000)
def gdt_entry(base, limit, access, flags):
    return struct.pack('<Q', (limit & 0xffff) | ((base & 0xffffff) << 16) | (access << 40) | (((limit >> 16) & 0xf) << 48) | (flags << 52) | ((base >> 24) << 56))
mu.mem_write(GDT + 8 * 1, gdt_entry(0, 0xfffff, 0x9b, 0xc))      # codice
mu.mem_write(GDT + 8 * 2, gdt_entry(0, 0xfffff, 0x93, 0xc))      # dati
mu.mem_write(GDT + 8 * 3, gdt_entry(TEB, 0xfff, 0x93, 0x4))      # fs
mu.mem_write(GDT + 8 * 4, gdt_entry(0, 0xfffff, 0x97, 0xc))      # ss (ring 0)
mu.reg_write(UC_X86_REG_GDTR, (0, GDT, 0x1000, 0x0))
mu.reg_write(UC_X86_REG_FS, 3 << 3)
mu.reg_write(UC_X86_REG_SS, (4 << 3))
mu.reg_write(UC_X86_REG_DS, 2 << 3); mu.reg_write(UC_X86_REG_ES, 2 << 3)
def ens(a, n):
    for p in range(a & ~0xfff, (a + n + 0xfff) & ~0xfff, PG): mapp(p)
def r32(a): ens(a, 4); return struct.unpack('<I', mu.mem_read(a, 4))[0]
def w32(a, v): ens(a, 4); mu.mem_write(a, struct.pack('<I', v & 0xffffffff))
def rf(a, n=1): ens(a, 4 * n); return struct.unpack('<%df' % n, mu.mem_read(a, 4 * n))
for p in range(0, 1): pass
mapp(0xfad000); G = r32(0xfadb58)
for p in (G & ~0xfff, (G + 0x1000) & ~0xfff, (G + 0x2000) & ~0xfff): mapp(p)
L = r32(0xe7f094)
print('game %x lara %x pos %s modo attuale %d cand %x att %x' % (G, L, rf(L + 0x20, 3), r32(G + 0xb00), r32(G + 0xa64), r32(G + 0xc94)))
w32(G + 0xb00, MODE)
if '--fixP' in sys.argv:
    ens(0x2123a570 + 0x80ee0, 4); mu.mem_write(0x2123a570 + 0x80ee0, bytes.fromhex('08151600')); print('P-lista 0x80ed0 corretta')
if '--fixlists' in sys.argv:
    DTPB = 0x2123a570
    FIX = {0x7efb0: '0e081600', 0x7f020: '1011121314160000', 0x7f060: '16000000', 0x7f5b0: '16000000', 0x7f5e0: '16000000',
           0x7f740: '02000000', 0x7ff00: '16000000', 0x800c0: '09160000', 0x801e0: '17000000'}
    for o, h in FIX.items():
        ens(DTPB + o, 8); mu.mem_write(DTPB + o, bytes.fromhex(h))
    print('liste corrette in memoria (9)')
for a_ in sys.argv:
    if a_.startswith('--pos='):
        x, y, z = map(float, a_[6:].split(','))
        ens(L + 0x20, 12); mu.mem_write(L + 0x20, struct.pack('<3f', x, y, z)); print('Lara spostata in', x, y, z)
# punti osservati
WATCH = {0x70bc40: 'add_item', 0x725b50: 'vis', 0x6fcb10: 'collide', 0x6fe040: 'estremi', 0x5d5930: 'getparams', 0x707c60: 'puntoAggancio', 0x711530: 'puntoAggancio2', 0x6fe7e0: 'normale', 0x70f300: 'collettore', 0x70ffb0: 'filtro', 0x70bc80: 'aggiungi', 0x728c30: 'scelta', 0x770240: 'scrivi_cand',
         0x770550: 'nessun_cand', 0x729420: 'filtro2', 0x76ffc0: 'vel', 0x771830: 'query', 0x724bb0: 'conv'}
hits = []
def on_code(uc, addr, size, ud):
    if addr in WATCH:
        esp = uc.reg_read(UC_X86_REG_ESP)
        args = [r32(esp + 4 * k) for k in range(1, 5)]
        hits.append((WATCH[addr], args))
        if TRACE: print('  ->', WATCH[addr], ' '.join('%x' % a for a in args))
        if WATCH[addr] == 'add_item':
            ecx = uc.reg_read(UC_X86_REG_ECX)
            it = args[0]
            print('     add_item da %x lista %x item inst %x seg %d t %s' % (r32(esp), ecx, r32(it), r32(it + 4), rf(it + 8, 2)))
        if WATCH[addr] == 'collide':
            a = [r32(esp + 4 * k) for k in range(1, 9)]
            for a2_ in sys.argv:
                if a2_.startswith('--ashift='):
                    dx, dz = map(float, a2_[9:].split(','))
                    v = rf(a[1], 3); mu.mem_write(a[1], struct.pack('<3f', v[0] + dx, v[1], v[2] + dz))
                if a2_.startswith('--pshift='):
                    dx = float(a2_[9:])
                    for q in (a[3], a[4]):
                        v = rf(q, 3); mu.mem_write(q, struct.pack('<f', v[0] + dx))
            print('     collide params %x A=%s r=%x P1=%s P2=%s n=%x %s a5=%x a6=%x' % (a[0], rf(a[1], 3), a[2], rf(a[3], 3), rf(a[4], 3), a[7], rf(a[7], 4), a[5], a[6]))
            ra = r32(esp)
            uc.hook_add(UC_HOOK_CODE, lambda uc_, a_, s_, u_: print('     collide ->', uc_.reg_read(UC_X86_REG_EAX) & 0xff), begin=ra, end=ra)
        if WATCH[addr] == 'estremi':
            ra = r32(esp); o1, o2 = args[2], args[3]
            def done(uc, a, s_, u, o1=o1, o2=o2):
                print('     estremi ->', rf(o1, 3), rf(o2, 3))
            hh = uc.hook_add(UC_HOOK_CODE, done, begin=ra, end=ra)
for a in WATCH: mu.hook_add(UC_HOOK_CODE, on_code, begin=a, end=a)
def on_ret(uc, addr, size, ud):
    print('   728f00 ->', uc.reg_read(UC_X86_REG_EAX) & 0xff, 'check %x' % r32(uc.reg_read(UC_X86_REG_ESP)))
mu.hook_add(UC_HOOK_CODE, lambda uc, a, s_, u: print('   728f00 args', ' '.join('%x' % r32(uc.reg_read(UC_X86_REG_ESP) + 4 * k) for k in range(1, 5)), 'punto', rf(r32(uc.reg_read(UC_X86_REG_ESP) + 16), 3)), begin=0x728f00, end=0x728f00)
mu.hook_add(UC_HOOK_CODE, lambda uc, a, s_, u: print('   728f00 ->', uc.reg_read(UC_X86_REG_EAX) & 0xff), begin=0x7294d7, end=0x7294d7)
ninsn = [0]
def on_any(uc, addr, size, ud):
    ninsn[0] += 1
last = []
def on_block(uc, a, sz, u):
    last.append(a)
    if len(last) > 400: del last[0]
mu.hook_add(UC_HOOK_BLOCK, on_block)
for a_ in sys.argv:
    if a_.startswith('--att='):
        w32(G + 0xc94, int(a_[6:], 16)); w32(G + 0xc98, 0x40989179); print('agganciato a', a_[6:])
for a_ in sys.argv:
    if a_.startswith('--shiftvein='):
        dx = float(a_[12:]); rt = 0x18366200; pl = r32(rt + 0x58); n = r32(pl)
        for k in range(n):
            ens(pl + 0x10 + 16 * k, 16); x = rf(pl + 0x10 + 16 * k)[0]; mu.mem_write(pl + 0x10 + 16 * k, struct.pack('<f', x + dx))
        x = rf(rt + 13 * 4)[0]; mu.mem_write(rt + 13 * 4, struct.pack('<f', x + dx))
        print('vena spostata in x di', dx)
for a_ in sys.argv:
    if a_.startswith('--blk18='):
        vals = [float(v) for v in a_[8:].split(',')]
        b18 = 0x2123a570 + 0x33a10
        ens(b18 + 0x54, 12); mu.mem_write(b18 + 0x54, struct.pack('<%df' % len(vals), *vals)); print('blocco 18 +0x54 =', vals)
for a_ in sys.argv:
    if a_.startswith('--fall='):
        z0, h = map(float, a_[7:].split(',')); ens(G + 0x6dc, 8); mu.mem_write(G + 0x6dc, struct.pack('<2f', z0, h)); print('inizio caduta', z0, h)
if '--nowater' in sys.argv:
    ens(0x728990, 4); mu.mem_write(0x728990, struct.pack('<I', 0x3c19e7 & ~0x80000)); print('sonda classe: maschera senza tipo 2')
FLZ = [float(a_[9:]) for a_ in sys.argv if a_.startswith('--floorz=')]
if FLZ:   # sostituisce la quota colpita dalla sonda di classe (out a esp+0x70 in 0x728650, dopo la correzione acqua 0x6c1cd0)
    def h_fz(uc, a, s_, u):
        o = uc.reg_read(UC_X86_REG_ESP) + 0x70; print('   sonda classe: tipo %d quota %.1f -> %.1f' % (r32(o), rf(o + 0x18)[0], FLZ[0])); uc.mem_write(o + 0x18, struct.pack('<f', FLZ[0]))
    mu.hook_add(UC_HOOK_CODE, h_fz, begin=0x7289ce, end=0x7289ce)
if '--wtrace' in sys.argv:   # quota colpita prima e dopo la correzione acqua 0x6c1cd0 (out = esp+0x78 tra i due push)
    def h_w(uc, a, s_, u):
        o = uc.reg_read(UC_X86_REG_ESP) + 0x78
        print('   %x out tipo %d ogg %x punto %s' % (a, r32(o), r32(o + 0xc), ['%.2f' % v for v in rf(o + 0x10, 3)]))
    for a__ in (0x7289c6, 0x7289cb): mu.hook_add(UC_HOOK_CODE, h_w, begin=a__, end=a__)
if '--tu628' in sys.argv:   # costante della TU (616,2975) al posto di quella base (628,9395) usata dal test di fascia 0x7260b0
    ens(0x85e4ac, 4); mu.mem_write(0x85e4ac, struct.pack('<f', -616.2974853515625)); print('costante 0x85e4ac = -616.2975 (TU)')
DEP = [float(a_[8:]) for a_ in sys.argv if a_.startswith('--depth=')]
if DEP:   # forza item+0xa8 (quota ledge - quota pavimento, scritta a 0x7289dc) al valore dato
    def h_dep(uc, a, s_, u):
        it = r32(uc.reg_read(UC_X86_REG_ESP) + 0x1c); print('   profondita item %x: %.1f -> %.1f' % (it, rf(it + 0xa8)[0], DEP[0])); uc.mem_write(it + 0xa8, struct.pack('<f', DEP[0]))
    mu.hook_add(UC_HOOK_CODE, h_dep, begin=0x7289e2, end=0x7289e2)
EXCL = [int(a_[10:], 16) for a_ in sys.argv if a_.startswith('--exclude=')]
if EXCL:
    def on_excl(uc, a, s_, u):
        sp = uc.reg_read(UC_X86_REG_ESP); inst = r32(sp + 4)
        if inst in EXCL:
            uc.reg_write(UC_X86_REG_EAX, 1); uc.reg_write(UC_X86_REG_EIP, r32(sp)); uc.reg_write(UC_X86_REG_ESP, sp + 4)
    mu.hook_add(UC_HOOK_CODE, on_excl, begin=0x6f9660, end=0x6f9660)
    print('escluso', [hex(x) for x in EXCL])
# RETHOOK: --rethook=ADDR,... stampa argomenti e valore di ritorno delle funzioni indicate quando un argomento e' la vena
RH = []
for a_ in sys.argv:
    if a_.startswith('--rethook='): RH = [int(x, 16) for x in a_[10:].split(',')]
VEIN = int([a_ for a_ in sys.argv if a_.startswith('--vein=')][0][7:],16) if any(a_.startswith('--vein=') for a_ in sys.argv) else 0x196acd80
def mk_rh(fa):
    def h(uc, a, s_, u):
        sp = uc.reg_read(UC_X86_REG_ESP); args = [r32(sp + 4 * k) for k in range(1, 6)]; ecx = uc.reg_read(UC_X86_REG_ECX)
        if VEIN in args or ecx == VEIN or (len(args) > 1 and r32(args[1]) == VEIN if args[1] > 0x10000 else False):
            ra = r32(sp)
            def done(uc2, a2, s2, u2, fa=fa, args=args, ecx=ecx):
                print('   RH %x(ecx=%x, %s) -> %x' % (fa, ecx, ' '.join('%x' % x for x in args), uc2.reg_read(UC_X86_REG_EAX)))
            uc.hook_add(UC_HOOK_CODE, done, begin=ra, end=ra)
    return h
for fa in RH: mu.hook_add(UC_HOOK_CODE, mk_rh(fa), begin=fa, end=fa)
if '--blocchi' in sys.argv:
    def h_bl(uc, a, s_, u):
        sp = uc.reg_read(UC_X86_REG_ESP); it = r32(sp + 8); ra = r32(sp); m = r32(sp + 0x14)
        uc.hook_add(UC_HOOK_CODE, lambda uc2, a2, s2, u2, it=it, m=m: print('   728320 item %x inst %x seg %d mask %x -> %d' % (it, r32(it), r32(it + 4), m & 0xffff, uc2.reg_read(UC_X86_REG_EAX) & 0xff)), begin=ra, end=ra)
    mu.hook_add(UC_HOOK_CODE, h_bl, begin=0x728320, end=0x728320)
if '--rayc' in sys.argv:
    def h_ray(uc, a, s_, u):
        sp = uc.reg_read(UC_X86_REG_ESP); ra = r32(sp); fl = r32(sp + 4); p0 = r32(sp + 8); p1 = r32(sp + 12); out = r32(sp + 16)
        if ra != 0x728999: return
        print('   ray %x da %s a %s' % (fl, ['%.0f' % v for v in rf(p0, 3)], ['%.0f' % v for v in rf(p1, 3)]))
        def done(uc2, a2, s2, u2, out=out):
            if uc2.reg_read(UC_X86_REG_EIP) != 0x728999: return
            print('      -> tipo %d  out %s' % (r32(out), bytes(uc2.mem_read(out, 0x60)).hex()))
        uc.hook_add(UC_HOOK_CODE, done, begin=ra, end=ra)
    mu.hook_add(UC_HOOK_CODE, h_ray, begin=0x493330, end=0x493330)
if '--raydeep' in sys.argv:
    RAYON = [0]
    def h_r0(uc, a, s_, u):
        sp = uc.reg_read(UC_X86_REG_ESP)
        if r32(sp) == 0x728999 and RAYON[0] == 0:
            RAYON[0] = 1; print('   [ray 0x728994 inizio]')
    mu.hook_add(UC_HOOK_CODE, h_r0, begin=0x493330, end=0x493330)
    mu.hook_add(UC_HOOK_CODE, lambda uc, a, s_, u: RAYON.__setitem__(0, 2) if RAYON[0] == 1 else None, begin=0x728999, end=0x728999)
    def h_q(uc, a, s_, u):
        if RAYON[0] != 1: return
        sp = uc.reg_read(UC_X86_REG_ESP); ecx = uc.reg_read(UC_X86_REG_ECX)
        print('   4e8fc0 this %x filtro %x p6 %x p7 %x ngruppi %d' % (ecx, r32(sp + 0x10), r32(sp + 0x14), r32(sp + 0x18), r32(ecx + 0x14)))
        o2 = r32(sp + 4); ra = r32(sp)
        def dq(uc2, a2, s2, u2, o2=o2):
            if uc2.reg_read(UC_X86_REG_EIP) != ra: return
            print('   4e8fc0 -> %d punto %s idx %d gruppo %x faccia %x' % (uc2.reg_read(UC_X86_REG_EAX) & 0xff, ['%.1f' % q for q in rf(o2, 3)], r32(o2 + 0x24), r32(o2 + 0x28), r32(o2 + 0x2c)))
        uc.hook_add(UC_HOOK_CODE, dq, begin=ra, end=ra)
    mu.hook_add(UC_HOOK_CODE, h_q, begin=0x4e8fc0, end=0x4e8fc0)
    def h_o(uc, a, s_, u):
        if RAYON[0] != 1: return
        sp = uc.reg_read(UC_X86_REG_ESP); o2 = r32(sp + 4); ra = r32(sp)
        print('   4e8ef0 da %s a %s p5 %x p6 %x p7 %x' % (['%.0f' % q for q in rf(r32(sp + 8), 3)], ['%.0f' % q for q in rf(r32(sp + 12), 3)], r32(sp + 16), r32(sp + 20), r32(sp + 24)))
        def dq(uc2, a2, s2, u2, o2=o2, ra=ra):
            if uc2.reg_read(UC_X86_REG_EIP) != ra: return
            print('   4e8ef0 -> %d punto %s colpito %x' % (uc2.reg_read(UC_X86_REG_EAX) & 0xff, ['%.1f' % q for q in rf(o2, 3)], r32(o2 + 0x30)))
        uc.hook_add(UC_HOOK_CODE, dq, begin=ra, end=ra)
    mu.hook_add(UC_HOOK_CODE, h_o, begin=0x4e8ef0, end=0x4e8ef0)
    def h_f(uc, a, s_, u):
        if RAYON[0] != 1: return
        sp = uc.reg_read(UC_X86_REG_ESP); ob = r32(sp + 4); cx = r32(sp + 8); ra = r32(sp)
        t = bytes(uc.mem_read(ob + 0x9d, 1))[0] if ob else -1
        def dq(uc2, a2, s2, u2, ob=ob, t=t, cx=cx, ra=ra):
            if uc2.reg_read(UC_X86_REG_EIP) != ra: return
            print('   filtro obj %x tipo %d maschera %x -> %d' % (ob, t, r32(cx + 0x30) if cx else 0, uc2.reg_read(UC_X86_REG_EAX) & 0xff))
        uc.hook_add(UC_HOOK_CODE, dq, begin=ra, end=ra)
    mu.hook_add(UC_HOOK_CODE, h_f, begin=0x48ebc0, end=0x48ebc0)
    def h_m(uc, a, s_, u):
        if RAYON[0] != 1: return
        sp = uc.reg_read(UC_X86_REG_ESP); ra = r32(sp); args = [r32(sp + 4 * k) for k in range(1, 6)]; ecx = uc.reg_read(UC_X86_REG_ECX)
        def done(uc2, a2, s2, u2, args=args, ecx=ecx):
            v = uc2.reg_read(UC_X86_REG_EAX)
            if v: print('      46c450 ecx %x args %s -> %x  punto %s' % (ecx, ' '.join('%x' % x for x in args), v, ['%.0f' % q for q in rf(args[0], 3)]))
        uc.hook_add(UC_HOOK_CODE, done, begin=ra, end=ra)
    pass
if '--rectest' in sys.argv:
    ARR = r32(0x2123a570 + 0x32f70 + 0x90)
    for fa in (0x7260b0, 0x728500):
        def h_rt(uc, a, s_, u, fa=fa):
            sp = uc.reg_read(UC_X86_REG_ESP); rec = r32(sp + 4); ra = r32(sp)
            k = (rec - ARR) // 0x14 if ARR <= rec < ARR + 16 * 0x14 else -1
            def dq(uc2, a2, s2, u2, k=k, ra=ra, fa=fa):
                if uc2.reg_read(UC_X86_REG_EIP) != ra: return
                print('   %x record %d -> %d' % (fa, k, uc2.reg_read(UC_X86_REG_EAX) & 0xff))
            uc.hook_add(UC_HOOK_CODE, dq, begin=ra, end=ra)
        mu.hook_add(UC_HOOK_CODE, h_rt, begin=fa, end=fa)
if '--clear' in sys.argv:
    PEND = []
    def h_c(uc, a, s_, u):
        sp = uc.reg_read(UC_X86_REG_ESP)
        if r32(sp) != 0x493619: return
        PEND.append((rf(r32(sp + 8), 3), rf(r32(sp + 12), 3), r32(sp + 16)))
    def h_cr(uc, a, s_, u):
        if not PEND: return
        fr, to, out = PEND.pop()
        t = r32(out)
        print('   spazio %s -> %s : colpo %d %s ogg %x' % (['%.0f' % v for v in fr], ['%.0f' % v for v in to], t, ['%.1f' % v for v in rf(out + 0x10, 3)] if t else '', r32(out + 0xc) if t else 0))
    mu.hook_add(UC_HOOK_CODE, h_c, begin=0x493330, end=0x493330)
    mu.hook_add(UC_HOOK_CODE, h_cr, begin=0x493619, end=0x493619)
if '--terrhit' in sys.argv:
    PT = []
    def h_t(uc, a, s_, u):
        sp = uc.reg_read(UC_X86_REG_ESP); PT.append(r32(sp + 4))
    def h_tr(uc, a, s_, u):
        if not PT: return
        o2 = PT.pop()
        if uc.reg_read(UC_X86_REG_EAX) & 0xff:
            print('   terreno: punto %s gruppo %x faccia %x idx %d' % (['%.1f' % q for q in rf(o2, 3)], r32(o2 + 0x28), r32(o2 + 0x2c), r32(o2 + 0x24)))
    mu.hook_add(UC_HOOK_CODE, h_t, begin=0x4e8fc0, end=0x4e8fc0)
    mu.hook_add(UC_HOOK_CODE, h_tr, begin=0x4933f9, end=0x4933f9)
if '--classi' in sys.argv:
    def h_cl(uc, a, s_, u):
        sp = uc.reg_read(UC_X86_REG_ESP); it = r32(sp + 8); ra = r32(sp)
        uc.hook_add(UC_HOOK_CODE, lambda uc2, a2, s2, u2, it=it: print('   classe item %x inst %x seg %d -> %d' % (it, r32(it), r32(it + 4), uc2.reg_read(UC_X86_REG_EAX))), begin=ra, end=ra)
    mu.hook_add(UC_HOOK_CODE, h_cl, begin=0x728650, end=0x728650)
esp = STACK - 0x8000
SOFF = 0xb10 if '--S=b10' in sys.argv else 0x980
mu.mem_write(esp, struct.pack('<III', RET, G + SOFF, MODE))
mu.reg_write(UC_X86_REG_ESP, esp)
mu.reg_write(UC_X86_REG_FPCW, 0x27f)
try: mu.reg_write(UC_X86_REG_MXCSR, 0x1f80)
except Exception as e: print('mxcsr', e)
print('fpcw %x' % mu.reg_read(UC_X86_REG_FPCW))
err = None
try:
    mu.emu_start(0x7296c0, RET, count=50_000_000)
except UcError as e:
    err = '%s @%x' % (e, mu.reg_read(UC_X86_REG_EIP))
print('fine:', err or 'ok', 'eip %x' % mu.reg_read(UC_X86_REG_EIP)); print('ultimi blocchi', ' '.join('%x' % a for a in last[-200:] if a < 0x821000 or a > 0x830000))
print('pagine senza dati nel dump:', ['%x' % p for p in missing[:20]], len(missing))
n = r32(0xfae350); lst = r32(0xfae358)
print('collettore: %d markup' % n)
for k in range(min(n, 60)):
    e = lst + 0xe0 * k
    inst = r32(e); seg = r32(e + 4)
    print('  [%d] inst %x seg %d raw %s classe %d f_a4 %.1f f_a8 %.1f' % (k, inst, seg, bytes(mu.mem_read(e, 0x20)).hex(), r32(e + 0xac), rf(e + 0xa4)[0], rf(e + 0xa8)[0]))
if '--itemdump' in sys.argv:  # ITEMDUMP
    e = lst
    for k in range(0, 0xe0, 16):
        print('   item +%02x %s %s' % (k, bytes(mu.mem_read(e + k, 16)).hex(), ['%.2f' % x for x in rf(e + k, 4)]))
print('liste: fae2f0 n=%d fae2d4 n=%d' % (r32(0xfae2f0), r32(0xfae2d4)))
cb = r32(0xfae2dc)
for k in range(min(r32(0xfae2d4), 8)):
    e = cb + 0xd0 * k
    print('   cand %d inst %x seg %d +c0 %d +b0..: %s' % (k, r32(e), r32(e + 4), r32(e + 0xc0), ' '.join('%x' % r32(e + o) for o in range(0xa0, 0xd0, 4))))
print('dopo: cand %x (game+0xa64)  bf4 %x  modo %d' % (r32(G + 0xa64), r32(G + 0xbf4), r32(G + 0xb00)))
from collections import Counter
print('chiamate:', Counter(h[0] for h in hits))
import pickle; pickle.dump(hits, open(DUMP + '.emu_hits.pkl', 'wb')) if False else None
