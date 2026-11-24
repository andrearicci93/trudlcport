#!/usr/bin/env python3
"""light_monitor.py - READ-ONLY monitor of the scene's PCRenderLights in a running tru.exe (D-2 flashlight shadows).

Every --interval seconds it reads the scene light array and logs, for each light near Lara (< --near units):
light address, type +0xc0, flags +0xc5 (bit 2 = cast shadow), resource kind +0x42c, res+0x1878, CastsShadow, distance.
A line is written only when something changes (new light, light gone, any field changed), so short flips are caught.

Addresses (fork docs/ENGINE.md "Scene light list" / "Shadow caster gate"; TruMenu light.list uses the same):
  device [0xa1407c]; scene = device + 0xfdfc; count [scene+0x14]; array [scene+0x1c]; light vtable 0x849594;
  light +0x1c = PCLightResource; position: light matrix +0x20, translation row at +0x50 (as TruMenu reads it).
  Lara: game tracker 0xe7f088 +0xc = instance, +0x20 = position.
Access: OpenProcess(PROCESS_VM_READ | QUERY_LIMITED) + ReadProcessMemory only.

  python -I tru-pc/tools/light_monitor.py --out FILE [--seconds 300] [--interval 0.01] [--near 3000]
"""
import argparse, ctypes, ctypes.wintypes as wt, math, struct, subprocess, sys, time

DEV, SCENE_OFF, LT_VT = 0x00a1407c, 0xfdfc, 0x00849594
GT = 0x00e7f088


class Mem:
    def __init__(self):
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq tru.exe', '/FO', 'CSV', '/NH'], capture_output=True, text=True).stdout
        if 'tru.exe' not in out: sys.exit('tru.exe is not running')
        pid = int(out.split('","')[1])
        k = ctypes.WinDLL('kernel32', use_last_error=True); k.OpenProcess.restype = wt.HANDLE
        self.k, self.h = k, k.OpenProcess(0x10 | 0x1000, False, pid)
        if not self.h: sys.exit('OpenProcess refused (%d)' % ctypes.get_last_error())
        self.pid = pid

    def raw(self, a, n):
        b = ctypes.create_string_buffer(n); got = ctypes.c_size_t(0)
        ok = self.k.ReadProcessMemory(self.h, ctypes.c_void_p(a), b, n, ctypes.byref(got))
        return b.raw[:n] if ok and got.value == n else None

    def u32(self, a):
        b = self.raw(a, 4) if a else None
        return struct.unpack('<I', b)[0] if b else 0

    def u8(self, a):
        b = self.raw(a, 1) if a else None
        return b[0] if b else 0

    def f3(self, a):
        b = self.raw(a, 12) if a else None
        return struct.unpack('<3f', b) if b else None


def snap(m, near):
    dev = m.u32(DEV); scene = dev + SCENE_OFF if dev else 0
    n = m.u32(scene + 0x14) if scene else 0; arr = m.u32(scene + 0x1c) if scene else 0
    inst = m.u32(GT + 0xc); lara = m.f3(inst + 0x20) if inst else None
    out = {}
    for i in range(min(n, 256)):
        L = m.u32(arr + 4 * i)
        if not L or m.u32(L) != LT_VT: continue
        pos = m.f3(L + 0x50)
        d = math.dist(pos, lara) if pos and lara else -1.0
        if near and (d < 0 or d > near): continue
        res = m.u32(L + 0x1c)
        c5 = m.u8(L + 0xc5); kind = m.u32(res + 0x42c) if res else -1; r78 = m.u8(res + 0x1878) if res else 0
        out[L] = (m.u8(L + 0xc0), c5, kind, r78, int(bool(c5 & 4) and bool(r78)), round(d))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', required=True); ap.add_argument('--seconds', type=float, default=300)
    ap.add_argument('--interval', type=float, default=0.01); ap.add_argument('--near', type=float, default=3000)
    a = ap.parse_args()
    m = Mem(); f = open(a.out, 'w', encoding='utf-8')
    f.write('# tru.exe pid %d, near %.0f u; fields: type c5 kind res1878 casts dist\n' % (m.pid, a.near)); f.flush()
    prev = {}; end = time.time() + a.seconds; samples = 0
    while time.time() < end:
        cur = snap(m, a.near); samples += 1
        t = time.strftime('%H:%M:%S') + '.%03d' % (int(time.time() * 1000) % 1000)
        for L, v in cur.items():
            p = prev.get(L)
            if p is None: f.write('%s NEW  0x%08x type %d c5 0x%02x kind %d r1878 %d casts %d dist %d\n' % ((t, L) + v))
            elif p[:5] != v[:5]: f.write('%s CHG  0x%08x type %d c5 0x%02x kind %d r1878 %d casts %d dist %d (was c5 0x%02x casts %d)\n' % ((t, L) + v + (p[1], p[4])))
        for L in prev:
            if L not in cur: f.write('%s GONE 0x%08x\n' % (t, L))
        if cur != prev: f.flush()
        prev = cur
        time.sleep(a.interval)
        if samples % 500 == 0 and not m.raw(DEV, 4): break
    f.write('# done, %d samples\n' % samples); f.close()


if __name__ == '__main__':
    main()
