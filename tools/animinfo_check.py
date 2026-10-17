"""Offline replica of tru.exe 0x54e200 (globalaniminfo fill loop): for every DTP whose root+0xc0 is an internal pointer,
read count @+0xbc, 12-byte records {u16 slot, u32 n, ptr} and 8-byte entries {float, s8 lo @+4, s8 hi @+6}; flag
(hi-lo+1)&0xff == 0 (4G-iteration fill = crash ng_crash), n > 4096, and counts > 256.  usage: animinfo_check.py FILE.drm ..."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW, drm_reloc as R
for f in sys.argv[1:]:
    raw = open(f, 'rb').read() if os.path.exists(f) else None
    if raw is None:
        from rung1 import raw_pc
        try: raw = raw_pc(f)
        except Exception: print(f, "not found"); continue
    d = DW.read(raw, 'le'); bad = []; nchk = 0
    for s in d.sections:
        if s.type != 7 or len(s.data) < 0xc4 or not s.reloc: continue
        it = dict(R.parse(s.reloc, 'le').internal)
        if 0xc0 not in it: continue
        n = struct.unpack_from('<I', s.data, 0xbc)[0]; p = it[0xc0]
        if n == 0 or n > 256: continue          # not this struct
        nchk += 1
        for k in range(n):
            o = p + 12 * k
            if o + 12 > len(s.data): bad.append((s.id, 'rec oob', k)); break
            m = struct.unpack_from('<I', s.data, o + 4)[0]; ep = it.get(o + 8)
            if m > 4096: bad.append((s.id, 'rec', k, hex(m))); continue   # e.g. 0x00010000 = BE u32 1 as u16 pair
            if ep is None: continue
            for j in range(m):
                if ep + 8 * j + 8 > len(s.data): bad.append((s.id, 'ent oob', k)); break
                lo, hi = struct.unpack_from('<bxbx', s.data, ep + 8 * j + 4)
                if lo > hi: lo, hi = hi, lo
                if ((hi - lo + 1) & 0xff) == 0: bad.append((s.id, 'wrap', k, j, lo, hi))
    print(os.path.basename(f), 'dtps with animinfo', nchk, 'BAD', bad[:8])
