"""Stack euristico da minidump full (x86): per ogni thread, Eip/Esp/Ebp dal CONTEXT e scansione dello stack per indirizzi di
ritorno in tru.exe preceduti da una CALL. Uso: stack.py <dump> [n]"""
import sys, struct, bisect, mmap
sys.path.insert(0, '/private/tmp/claude-501/-Users-user-Downloads-tru-port/c1b946b9-5e3a-4d2e-94dc-3cbd87d194dc/scratchpad')
import pe as PE
f = open(sys.argv[1], 'rb'); m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
N = int(sys.argv[2]) if len(sys.argv) > 2 else 40
sig, ver, ns, sdir = struct.unpack_from('<IIII', m, 0)
streams = {}
for i in range(ns):
    t, sz, rva = struct.unpack_from('<III', m, sdir + 12 * i); streams[t] = (sz, rva)
# memory64 list
mem = []
sz, rva = streams[9]; n, base = struct.unpack_from('<QQ', m, rva); off = base
for i in range(n):
    a, l = struct.unpack_from('<QQ', m, rva + 16 + 16 * i); mem.append((a, l, off)); off += l
mem.sort(); starts = [a for a, _, _ in mem]
def rd(a, k):
    i = bisect.bisect_right(starts, a) - 1
    if i < 0: return None
    s, l, o = mem[i]
    if a + k > s + l: return None
    return m[o + a - s:o + a - s + k]
rows = [l.split('\t') for l in open('/path/to/ghidra_out/full/INDEX.tsv') if l.strip()]
A = [int(r[0], 16) for r in rows]
def fn(v):
    i = bisect.bisect_right(A, v) - 1; return '%s+%x' % (rows[i][1], v - A[i])
def is_ret(v):
    if not (0x401000 <= v < 0x840000): return False
    b = rd(v - 7, 7)
    if b is None: return False
    return b[2] == 0xe8 or b[5] == 0xff and (b[6] & 0x38) == 0x10 or b[1] == 0xff and (b[2] & 0x38) == 0x10 or b[4] == 0xff and (b[5] & 0x38) == 0x10
sz, rva = streams[3]; nt = struct.unpack_from('<I', m, rva)[0]
for i in range(nt):
    tid, sc, pc, pri, teb, sst, ssz, srva, csz, crva = struct.unpack_from('<IIIIQQIIII', m, rva + 4 + 48 * i)
    ctx = m[crva:crva + csz]
    eip, = struct.unpack_from('<I', ctx, 0xb8); esp, = struct.unpack_from('<I', ctx, 0xc4); ebp, = struct.unpack_from('<I', ctx, 0xb4)
    rets = []
    for a in range(esp, min(esp + 0x6000, sst + ssz), 4):
        b = rd(a, 4)
        if b is None: break
        v = struct.unpack('<I', b)[0]
        if is_ret(v): rets.append((a, v))
    if not rets: continue
    print('== thread %d eip %08x esp %08x ebp %08x  ritorni in tru.exe: %d' % (tid, eip, esp, ebp, len(rets)))
    for a, v in rets[:N]: print('   [%08x] %08x  %s' % (a, v, fn(v)))
