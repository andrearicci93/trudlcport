"""Traccia V: esegue in emulazione (unicorn) la ricerca del candidato 0x7296c0(game+0x980, modo) sulla memoria di un dump completo.
Memoria caricata pigramente dal dump (pagine da 4 KB); pila nuova. Solo lettura del dump.
uso: python emu_search.py DUMP MODO [--trace]"""
import sys, struct
sys.path.insert(0, 'C:/tru-port/tools')
from minidump_read import Minidump
from unicorn import *
from unicorn.x86_const import *
DUMP, MODE = sys.argv[1], 0
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
ARGS = 0x7e800000; mu.mem_map(ARGS, 0x10000)
def call_ray(fr, to, mask=0x3c19e7, ign=0):
    mu.mem_write(ARGS, struct.pack('<4f', *fr, 1.0)); mu.mem_write(ARGS + 0x10, struct.pack('<4f', *to, 1.0)); mu.mem_write(ARGS + 0x100, bytes(0x100))
    esp = STACK - 0x8000
    mu.mem_write(esp, struct.pack('<6I', RET, mask, ARGS, ARGS + 0x10, ARGS + 0x100, ign))
    mu.reg_write(UC_X86_REG_ESP, esp); mu.reg_write(UC_X86_REG_FPCW, 0x27f)
    try: mu.reg_write(UC_X86_REG_MXCSR, 0x1f80)
    except Exception: pass
    mu.emu_start(0x493330, RET, count=20_000_000)
    o = ARGS + 0x100
    return r32(o), r32(o + 0xc), rf(o + 0x10, 3)
