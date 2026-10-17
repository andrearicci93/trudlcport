"""find_flag.py - istruzioni nel .text dell'exe spacchettato con immediato 0x20000000 / 0xdfffffff (set/clear/test del bit f18&0x20000000)."""
import sys, os, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
exe = open(os.path.expanduser('~/Downloads/tru-port/work/laa/tru_steam.exe.unpacked.exe'), 'rb').read()
pe = struct.unpack_from('<I', exe, 0x3c)[0]; nsec = struct.unpack_from('<H', exe, pe + 6)[0]; opt = struct.unpack_from('<H', exe, pe + 20)[0]
base = struct.unpack_from('<I', exe, pe + 52)[0]
secs = []
for i in range(nsec):
    o = pe + 24 + opt + 40 * i
    nm = exe[o:o + 8].rstrip(b'\0').decode(); vs, va, rs, ro = struct.unpack_from('<IIII', exe, o + 8)
    secs.append((nm, va, vs, ro, rs))
text = [s for s in secs if s[0] == '.text'][0]
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False
data = exe[text[3]:text[3] + text[4]]; addr = base + text[1]
want = {0x20000000, 0xdfffffff, -0x20000001}
hits = []
for ins in md.disasm(data, addr):
    s = ins.op_str
    if ('0x20000000' in s or '0xdfffffff' in s) and any(m in ins.mnemonic for m in ('or', 'and', 'test', 'mov', 'cmp')):
        hits.append((ins.address, ins.mnemonic, s))
for h in hits: print('0x%x %s %s' % h)
print(len(hits), 'hit')
