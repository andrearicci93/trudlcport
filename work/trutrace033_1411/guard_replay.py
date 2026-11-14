"""TruTrace 0.3.3 offline replay: what the [NullModel] guard (entry of 0x5b7430) and the [ModelInst] drawable line
would have printed for the instance of a crash dump at tru+0x1b7476. Same reads as TruTrace.cpp (ModelNull,
ModelText, DescInst, NullModelNote, DrawCtorLeave) on the dump memory; read-only.

The crash is inside 0x5b7430 after its prologue: the entry values are E[0] = [ebp+4] (return), E[1..5] = [ebp+8..],
ebx / esi unchanged since the entry (0x5b744c / 0x5b744d only push them). The birth record of a drawable exists only
in the live plugin and is not part of a dump.

Usage (from trudlcport): ../bin/pyt -t 300 work/trutrace033_1411/guard_replay.py DUMP.dmp
"""
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import minidump_read as MR  # noqa: E402

K_PLAYER, K_NAMES, K_UNIT, K_POOL = 0x00e7f094, 0x00db94d0, 0x00e7f148, 0x00d98f60
K_UNITS, K_UNITS_END, K_UNIT_SIZE = 0x00dbab40, 0x00dbc640, 0xd8
RET_A, RET_B = 0x005bbd0b, 0x005b80b4


def main(path):
    m = MR.Minidump(path)
    D = lambda a: (m.u32(a) or 0) if a else 0      # noqa: E731  guarded read as D(): 0 when unreadable
    W = lambda a: D(a) & 0xffff                     # noqa: E731
    F = lambda a: struct.unpack('<f', struct.pack('<I', D(a)))[0]   # noqa: E731

    def cstr(a):
        b = m.read(a, 96) if a else None
        if not b:
            return '?'
        s = b.split(b'\0')[0]
        return s.decode('ascii') if s and all(32 <= c <= 126 for c in s) else '?'

    def obj_name(i):
        t = D(K_NAMES)
        cnt = D(t) if t else 0
        return cstr(D(t + i * 8)) if t and 0 < i <= cnt <= 8192 else '?'

    def looks_inst(v):
        pool = D(K_POOL)
        return bool(pool) and v >= pool and (v - pool) % 0x2f0 == 0 and (v - pool) // 0x2f0 < 0x1000

    def inst_obj(i):
        o = D(i + 0x10) if i else 0
        return D(o + 0x14) & 0xffff if o else 0

    def desc(i):
        oid = inst_obj(i)
        intro = D(i + 0x58)
        intro = intro - (1 << 32) if intro & 0x80000000 else intro
        return 'inst 0x%08x obj %d %s intro %d%s' % (i, oid, obj_name(oid), intro, ' (player)' if i == D(K_PLAYER) else '')

    def model_null(md):
        bt = D(md + 0x68) if md else 0
        seg = D(bt + 4) if bt else (D(md + 0xc) if md else 0)
        return (not md or not seg), bt, seg

    def model_text(i, md, rmi):
        nul, bt, seg = model_null(md)
        rm = D(md + 0x64) if md else 0
        s = '%s[%d] DTP 0x%08x (word0 0x%08x, %d segments, +0xc 0x%08x, bone table +0x68 0x%08x' % (
            '; ' if i else '', i, md, D(md), D(md + 4), D(md + 0xc), bt)
        if bt:
            s += ' {count %d, segments 0x%08x}' % (D(bt), D(bt + 4))
        s += ') PCRenderModel 0x%08x (render serial %d, not an id) instance 0x%08x%s' % (
            rm, D(rm + 8) if rm else 0, rmi, ' - NULL SEGMENTS: a draw (0x5b7430) reads [0+0x20]' if nul else '')
        return s

    def unit_name(uid):
        for e in range(K_UNITS, K_UNITS_END, K_UNIT_SIZE):
            if (D(e + 4) & 0xff) == 2 and D(e) == uid:
                return cstr(e + 0xc)
        return '?'

    exc = m.exception
    r = m.regs(exc['ctx'])
    print('dump %s: exception 0x%08x at 0x%08x, eax 0x%08x ecx 0x%08x ebx 0x%08x esi 0x%08x ebp 0x%08x' % (
        os.path.basename(path), exc['code'], exc['addr'], r['eax'], r['ecx'], r['ebx'], r['esi'], r['ebp']))
    E = [D(r['ebp'] + 4 + 4 * k) for k in range(6)]
    md = E[1]
    nul, bt, seg = model_null(md)
    print('guard condition (DTP 0, or +0x68 set and [+0x68]+4 == 0, or +0x68 0 and +0xc 0): %s - DTP 0x%08x, +0x68 '
          '0x%08x, segments 0x%08x, +0xc 0x%08x' % ('TRUE' if nul else 'false', md, bt, seg, D(md + 0xc)))
    ret = E[0]
    drawable = r['ebx'] if ret == RET_A else r['esi'] if ret == RET_B else 0
    inst = D(drawable + 4) if drawable else 0
    d = desc(inst) if inst and looks_inst(inst) else 'instance ? (drawable +4 0x%08x, caller 0x%08x)' % (inst, ret)
    obj = D(inst + 0x10) if looks_inst(inst) else 0
    lst = D(obj + 0x40) if obj else 0
    n = W(obj + 0x3a) if obj else 0
    n = n - 0x10000 if n & 0x8000 else n
    index = next((i for i in range(min(n, 64)) if D(lst + 4 * i) == md), -1)
    mt = model_text(max(index, 0), md, D(D(drawable + 0x10) + 4 * index) if index >= 0 else 0)
    wm = E[2]
    unit = unit_name(D(K_UNIT))
    print()
    print('[%s] nullmodel: NULL MODEL DRAW ahead: 0x5b7430 called from 0x%08x for %s, model %d of %d: %s; bone table '
          'words %s; drawable 0x%08x (vtable 0x%08x), world matrix 0x%08x (pos %.0f %.0f %.0f), arg 3 0x%08x, arg 4 '
          '0x%08x, arg 5 0x%08x; <birth record: live plugin only>; the game reads [0+0x20] next - crash expected '
          '(SkipNullModelDraw=0)' % (unit, ret, d, index, n, mt, ' '.join('%08x' % D(bt + 4 * k) for k in range(8)),
                                     drawable, D(drawable), wm, F(wm + 0x30), F(wm + 0x34), F(wm + 0x38), E[3], E[4],
                                     E[5]))
    # the [ModelInst] line of this drawable (models as they are now; the builder / birth part needs the live hook)
    models = '; '.join(model_text(i, D(lst + 4 * i), D(D(drawable + 0x10) + 4 * i))[2 if i else 0:]
                       for i in range(min(n, 16)))
    print()
    print('[%s] modelinst: drawable 0x%08x (vtable 0x%08x) for %s at %.0f %.0f %.0f (+0x54 0x%08x); built by <live '
          'plugin only>; %d model(s): %s' % (unit, drawable, D(drawable), d, F(inst + 0x20), F(inst + 0x24),
                                            F(inst + 0x28), D(inst + 0x54), n, models or 'none'))
    print()
    print('extra (not in the log line): unit id %d, player 0x%08x, inst +0x54 %s, inst +0x244 0x%08x (= drawable: %s), '
          'object 0x%08x +0x3a %d, DTP +0x40 bytes %s' % (
              D(K_UNIT), D(K_PLAYER), desc(D(inst + 0x54)) if looks_inst(D(inst + 0x54)) else '0x%08x' % D(inst + 0x54),
              D(inst + 0x244), D(inst + 0x244) == drawable, obj, n, (m.read(md, 0x70) or b'').hex()))
    return 0 if nul else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
