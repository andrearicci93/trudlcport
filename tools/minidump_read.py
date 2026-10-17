"""Lettore minimale di minidump x86 (ProcDump -ma / MiniDumpWriteDump), senza dipendenze.

Uso:
  tools/venv/bin/python -I tools/minidump_read.py DUMP.dmp                 riepilogo: stream, eccezione, registri del thread colpito, moduli
  tools/venv/bin/python -I tools/minidump_read.py DUMP.dmp --mem VA N      N byte a VA (hex)
Come modulo: d = Minidump(path); d.read(va, n) -> bytes|None; d.u32(va); d.exception; d.context(tid); d.threads; d.modules
Formato: documentazione pubblica MINIDUMP_* (dbghelp). Solo CONTEXT x86 (716 byte).
"""
import struct, sys

STREAMS = {3: 'ThreadList', 4: 'ModuleList', 5: 'MemoryList', 6: 'Exception', 7: 'SystemInfo', 9: 'Memory64List',
           15: 'MiscInfo', 16: 'MemoryInfoList', 17: 'ThreadInfoList', 21: 'SystemMemoryInfo', 22: 'ProcessVmCounters'}
REGS = {'edi': 0x9c, 'esi': 0xa0, 'ebx': 0xa4, 'edx': 0xa8, 'ecx': 0xac, 'eax': 0xb0, 'ebp': 0xb4, 'eip': 0xb8,
        'eflags': 0xc0, 'esp': 0xc4}


class Minidump:
    def __init__(self, path):
        self.d = d = open(path, 'rb').read()
        sig, ver, n, rva = struct.unpack_from('<IIII', d, 0)
        if sig != 0x504d444d:
            raise ValueError('non e\' un minidump (firma %08x)' % sig)
        self.streams = {}
        for i in range(n):
            t, size, r = struct.unpack_from('<III', d, rva + 12 * i)
            if t:
                self.streams.setdefault(t, (size, r))
        self.ranges = []   # (va, size, file_off)
        if 9 in self.streams:
            _, r = self.streams[9]
            cnt, base = struct.unpack_from('<QQ', d, r)
            off = base
            for i in range(cnt):
                va, sz = struct.unpack_from('<QQ', d, r + 16 + 16 * i)
                self.ranges.append((va, sz, off)); off += sz
        if 5 in self.streams:
            _, r = self.streams[5]
            cnt = struct.unpack_from('<I', d, r)[0]
            for i in range(cnt):
                va, sz, fo = struct.unpack_from('<QII', d, r + 4 + 16 * i)
                self.ranges.append((va, sz, fo))
        self.ranges.sort()
        self.threads = {}
        if 3 in self.streams:
            _, r = self.streams[3]
            cnt = struct.unpack_from('<I', d, r)[0]
            for i in range(cnt):
                e = r + 4 + 48 * i
                tid = struct.unpack_from('<I', d, e)[0]
                csz, crva = struct.unpack_from('<II', d, e + 40)
                self.threads[tid] = crva
        self.exception = None
        if 6 in self.streams:
            _, r = self.streams[6]
            tid = struct.unpack_from('<I', d, r)[0]
            code, flags, rec, addr, npar = struct.unpack_from('<IIQQI', d, r + 8)
            info = struct.unpack_from('<15Q', d, r + 8 + 32)
            csz, crva = struct.unpack_from('<II', d, r + 8 + 152)
            self.exception = dict(tid=tid, code=code, flags=flags, addr=addr, info=info[:npar], ctx=crva)
        self.modules = []
        if 4 in self.streams:
            _, r = self.streams[4]
            cnt = struct.unpack_from('<I', d, r)[0]
            for i in range(cnt):
                e = r + 4 + 108 * i
                base, size = struct.unpack_from('<QI', d, e)
                nrva = struct.unpack_from('<I', d, e + 20)[0]
                ln = struct.unpack_from('<I', d, nrva)[0]
                self.modules.append((base, size, d[nrva + 4:nrva + 4 + ln].decode('utf-16-le', 'replace')))

    def read(self, va, n):
        for rv, sz, fo in self.ranges:
            if rv <= va and va + n <= rv + sz:
                return self.d[fo + va - rv:fo + va - rv + n]
        return None

    def u32(self, va):
        b = self.read(va, 4)
        return None if b is None else struct.unpack('<I', b)[0]

    def regs(self, ctx_rva):
        return {k: struct.unpack_from('<I', self.d, ctx_rva + o)[0] for k, o in REGS.items()}

    def module_of(self, va):
        for b, s, n in self.modules:
            if b <= va < b + s:
                return '%s+%x' % (n.split('\\')[-1], va - b)
        return None


def main():
    m = Minidump(sys.argv[1])
    if '--mem' in sys.argv:
        i = sys.argv.index('--mem'); va, n = int(sys.argv[i + 1], 16), int(sys.argv[i + 2], 0)
        b = m.read(va, n); print(b.hex() if b is not None else 'NON NEL DUMP'); return 0
    print('stream:', ', '.join('%s(%d B)' % (STREAMS.get(t, t), s) for t, (s, _) in sorted(m.streams.items())))
    print('memoria: %d intervalli, %.1f MB' % (len(m.ranges), sum(s for _, s, _ in m.ranges) / 1e6))
    print('thread: %d, moduli: %d' % (len(m.threads), len(m.modules)))
    e = m.exception
    if e:
        print('ECCEZIONE thread %d codice %08x indirizzo %08x (%s) info %s' % (
            e['tid'], e['code'], e['addr'], m.module_of(e['addr']), ['%x' % x for x in e['info']]))
        r = m.regs(e['ctx'])
        print('  ' + ' '.join('%s=%08x' % kv for kv in r.items()))
        b = m.read(r['eip'], 16)
        print('  byte a eip:', b.hex() if b else 'NON NEL DUMP')
        st = m.read(r['esp'], 64)
        print('  stack:', st.hex() if st else 'NON NEL DUMP')
    else:
        print('nessuno stream Exception (dump su richiesta)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
