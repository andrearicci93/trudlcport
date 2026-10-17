"""padshock\\padshocklib.tfb (controller rumble library, NtPadshock*) Xbox -> PC.

Why: the DLC scripts play rumble effects BY NAME (dlc_caverns Script 20914 -> 'dlc1_adren_bridge', the adrenaline
trap bridge).  The name only exists in the Xbox TITLE-UPDATE padshocklib.tfb (33 entries); base Xbox layer1/2 and PC
ship 32.  tru.exe 0x481a90 (lookup) is a binary search that underflows when the name is missing and sorts before
entry 0: index -1 -> reads the count word (0x20) as an entry pointer -> stricmp(name, 0x28) -> AV at 0x82eb22
(crash fix12_menu, 'adrenaline start').  The file is loaded once at boot (0x483760 -> 0x481ba0 'padshocklib.tfb',
path '%spadshock\\%s' = PC-W\\padshock\\) -> install as mods\\padshock\\padshocklib.tfb (real dir).

Format (both platforms, platform endian):
  u32 version (0x1f), u32 n, n x {u32 size, u32 offset} (sorted by name, stricmp), then the entries:
  entry: 'PHI!' (raw bytes), u32 version, char name[64] (raw; build-tool garbage after the NUL), then u32/float words.
Conversion: header u32 swap; entry word 0 raw, word 1 swap, bytes 8..0x48 raw, rest u32 swap.
Validation (python3 -I tools/padshock_convert.py check): convert(Xbox layer1) vs PC = byte-exact except 1 garbage
byte inside the name buffer of entry 0 (b7 vs 00).

Build (python3 -I tools/padshock_convert.py build OUTDIR): TU layout (33 sorted entries); the 32 base entries are
copied byte-for-byte from the PC file (TU base entries == layer1 except name-buffer garbage), only new TU entries
are converted.
"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

B = '/path/to/'
PC_BIG = B + 'tru-port/pc/bigfile.000'
XB = {'l1': B + 'TombRaiderUnderworld_Patched/layer1.000', 'tu': B + 'TombRaiderUnderworld_Patched/TitleUpdate.000'}
NAME_PC = 'pc-w\\padshock\\padshocklib.tfb'
NAME_XB = 'xenon-w\\padshock\\padshocklib.tfb'
NAME0, NAME1 = 8, 0x48   # raw name buffer inside an entry


def load(which):
    from archive import Archive
    from names import crc
    if which == 'pc':
        a = Archive(PC_BIG, 'le'); r = a.find(crc(NAME_PC))
    else:
        a = Archive(XB[which], 'be'); r = a.find(crc(NAME_XB))
    assert r, which
    return a.read(r[0])


def parse(d, e):
    ver, n = struct.unpack_from(e + 'II', d, 0)
    ents = []
    for i in range(n):
        sz, off = struct.unpack_from(e + 'II', d, 8 + 8 * i)
        blob = d[off:off + sz]
        assert blob[:4] == b'PHI!', (i, blob[:4])
        ents.append((blob[NAME0:NAME1].split(b'\0')[0], blob))
    return ver, ents


def sw(b):
    assert len(b) % 4 == 0
    return b''.join(b[i:i + 4][::-1] for i in range(0, len(b), 4))


def conv_entry(x):
    return x[:4] + sw(x[4:8]) + x[NAME0:NAME1] + sw(x[NAME1:])


def build(ver, ents):
    """ents: [(name, LE entry blob)] in file order -> LE file."""
    out = bytearray(struct.pack('<II', ver, len(ents)))
    off = 8 + 8 * len(ents)
    for _, b in ents:
        out += struct.pack('<II', len(b), off); off += len(b)
    for _, b in ents:
        out += b
    return bytes(out)


def convert(xbox, pc_ref=None):
    ver, xe = parse(xbox, '>')
    pce = dict(parse(pc_ref, '<')[1]) if pc_ref else {}
    ents = [(nm, pce.get(nm) or conv_entry(b)) for nm, b in xe]
    for nm, b in xe:
        if nm in pce: assert len(pce[nm]) == len(b), nm
    return build(ver, ents)


def lookup(d, name):
    """Replay of tru.exe 0x481a90 (after the loader's offset fixup).  Returns index, -1 = AV (entry -1 read)."""
    ver, n = struct.unpack_from('<II', d, 0)
    def ent_name(i):
        if i < 0: return None   # engine reads table+4 (count) as a pointer -> crash
        off = struct.unpack_from('<I', d, 8 + 8 * i + 4)[0]
        return d[off + NAME0:off + NAME1].split(b'\0')[0]
    def cmp(a, b): a, b = a.lower(), b.lower(); return (a > b) - (a < b)
    lo, hi = 0, n - 1
    mid = hi >> 1
    while True:
        en = ent_name(mid)
        if en is None: return -1
        c = cmp(name, en)
        if c == 0: return mid
        if c > 0: lo = mid + 1
        else: hi = mid - 1
        new = (hi + lo) >> 1
        if new == mid: return None   # not found (engine returns 0)
        mid = new


def check():
    pc, l1, tu = load('pc'), load('l1'), load('tu')
    c = convert(l1)                  # pure conversion, no PC reference
    diff = [i for i in range(len(pc)) if c[i] != pc[i]]
    print('l1 -> PC: size', len(c), len(pc), 'differing bytes', len(diff), [hex(i) for i in diff[:8]])
    _, le = parse(pc, '<'); _, xe = parse(l1, '>'); _, te = parse(tu, '>')
    xd = dict(xe)
    for nm, b in te:
        if nm in xd:
            dw = [o for o in range(0, len(b), 4) if b[o:o + 4] != xd[nm][o:o + 4]]
            if dw: print('TU vs l1', nm, 'diff word offsets', [hex(o) for o in dw],
                         'all in name buffer:', all(NAME0 <= o < NAME1 for o in dw))
        else:
            print('TU new entry', nm, len(b))
    return pc, tu


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    pc, tu = check()
    new = convert(tu, pc)
    names = [nm for nm, _ in parse(new, '<')[1]]
    print('new file', len(new), 'entries', len(names), 'sorted', names == sorted(names, key=bytes.lower))
    for nm in names + [b'dlc1_adren_bridge', b'long_vol5_breakableprim', b'sinking_ship_tilt']:
        r = lookup(new, nm)
        if r is None or r < 0 or names[r] != nm: print('LOOKUP FAIL', nm, r)
    print('all names found in new file; old PC file lookup of dlc1_adren_bridge ->', lookup(pc, b'dlc1_adren_bridge'))
    if cmd == 'build':
        od = os.path.join(sys.argv[2], 'padshock'); os.makedirs(od, exist_ok=True)
        open(os.path.join(od, 'padshocklib.tfb'), 'wb').write(new)
        print('wrote', os.path.join(od, 'padshocklib.tfb'))
