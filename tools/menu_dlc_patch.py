"""Build the PC main-menu 'DOWNLOADABLE CONTENT' A/B kit (generalbank.drm byte patch, agent menu_dlc 2026-10-12).

Source: PC patch.000 pc-w\\generalbank.drm (runtime-authoritative), decompressed. Only bytes of Script section id 7
(UIPause = the shared main/pause ring menu) change; section sizes / reloc blob lengths are unchanged.

Findings this relies on (see work/menu_dlc/README.txt):
  corebase (Script 230 on PC) native f15 (Function @0x218) = 0x79eb10 -> 0x60d630 'xor al,al; ret'  (always FALSE on PC)
  corebase native f17 (Function @0x250)                    = 0x795f80 -> 0x68ac90 'mov al,1; ret'   (always TRUE on PC)
  The ring-menu code is the same on Xbox TU and PC; at slot 7 it takes the 'quit/exit' branch when f17() is true,
  the 'DOWNLOADABLE CONTENT' branch when it is false (Xbox).  Retargeting the call to f15 (same BOOL() prototype,
  global call op 0x66) makes PC take the Xbox branch at that call site only.

Patches (script 7, PC offsets):
  P1 0x6294  op66 call at 0x6290 in func 27 (vt 49, slot-7 highlight icon: 0x738 door vs 0x72c download)   f17 -> f15
  P2 0x9694  op66 call at 0x9690 in func 35 (vt 57, PositionMenuItems case 7: QUIT text+door vs DLC text+icon) f17 -> f15
  P3 0x25934 init word of member 0xc4c (sym 958, uilocalstr) 163 'EXIT' -> 130 'DOWNLOADABLE CONTENT': func 1 @0x4174
             relabels the DLC text widget 0x39c with it whenever uigamedata.f37() (= in front end) is true.
  P4 0x188e8 op66 call at 0x188e4 in func 8 (vt 17, click on ring item 0x138 = slot 7): f17 -> f15, i.e. open the
             slot-7 sub-ring (PLAY MISSION / COMMUNITY INFO / DOWNLOAD CONTENT) instead of the PC quit dialog (8,128).
Variant A = P1+P2+P3 (display only), variant B = P1+P2+P3+P4.
Usage: tools/venv/bin/python -I tools/menu_dlc_patch.py   -> work/menu_dlc/{A,B}/generalbank.drm (+ md5.txt, patch_log.txt)
"""
import sys, os, struct, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archive import Archive
from names import crc
from drm import cdrm_decode, parse_drm
import drm_reloc as R
import drm_write as DW

B = '/path/to/trudlcport/'
OUT = B + 'work/menu_dlc/'
F15, F17 = 0x218, 0x250
CALLS = {'P1': 0x6294, 'P2': 0x9694, 'P4': 0x188e8}
TEXT = ('P3', 0x25934, 163, 130)
VARIANTS = {'A': ['P1', 'P2', 'P3'], 'B': ['P1', 'P2', 'P3', 'P4']}

def load():
    a = Archive(B + 'pc/patch.000', 'le')
    r = a.find(crc('pc-w\\generalbank.drm'))
    assert len(r) == 1, 'expected exactly one generalbank record in patch.000'
    stored = a.read(r[0])
    return stored, cdrm_decode(stored, 'le')

def build(raw, which, log):
    hdr, secs, end = parse_drm(raw, 'le')
    assert end == len(raw)
    out = bytearray(raw)
    k7 = [s for s in secs if s['type'] == 8 and s['id'] == 7]
    kc = [s for s in secs if s['type'] == 8 and s['id'] == 230]
    assert len(k7) == 1 and len(kc) == 1
    s7, sc = k7[0], kc[0]
    d7 = raw[s7['data_off']:s7['data_off'] + s7['size']]
    blob = raw[s7['reloc_off']:s7['reloc_off'] + s7['reloc_bytes']]
    rel = R.parse(blob, 'le')
    # corebase Function structs @0x218 / @0x250 must be BOOL() globals: check Function array position (28-byte stride)
    dc = raw[sc['data_off']:sc['data_off'] + sc['size']]
    rc = dict(R.parse(raw[sc['reloc_off']:sc['reloc_off'] + sc['reloc_bytes']], 'le').internal)
    ft = rc[0x38]
    assert (F15 - ft) % 28 == 0 and (F17 - ft) % 28 == 0 and (F15 - ft) // 28 == 15 and (F17 - ft) // 28 == 17
    for fo in (F15, F17):
        pr = rc[fo]
        assert rc.get(pr + 12) is None or struct.unpack_from('<I', dc, rc[pr + 12] - 4)[0] == 0   # no args
        assert struct.unpack_from('<I', dc, pr + 16)[0] & 15 == 1                                  # returns BOOL
    nint = len(rel.internal)
    for p in which:
        if p == TEXT[0]:
            _, off, old, new = TEXT
            assert struct.unpack_from('<I', d7, off)[0] == old and struct.unpack_from('<I', d7, off - 0x10)[0] == 131
            assert struct.unpack_from('<I', d7, off - 4)[0] == 0xbeebbeeb and struct.unpack_from('<I', d7, off - 0x14)[0] == 0xbeebbeeb
            a = s7['data_off'] + off
            struct.pack_into('<I', out, a, new)
            log.append('%s data  sec#%d (8,7)+0x%x  file 0x%x: %08x -> %08x' % (p, s7['i'], off, a, old, new))
            continue
        src = CALLS[p]
        assert struct.unpack_from('<I', d7, src - 4)[0] == 0x66000000, 'not an op66 global call'
        hits = [k for k, (si, so, do) in enumerate(rel.external) if so == src]
        assert len(hits) == 1
        k = hits[0]; si, so, do = rel.external[k]
        assert si == sc['i'] and do == F17, (si, do)
        pos = s7['reloc_off'] + 20 + 8 * nint + 8 * k
        oldq = struct.unpack_from('<Q', out, pos)[0]
        assert R.unpack_ext(oldq) == (si, so, do)
        newq = R.pack_ext(si, so, F15)
        struct.pack_into('<Q', out, pos, newq)
        log.append('%s reloc sec#%d (8,7) ext#%d src 0x%x -> (8,230)+0x%x => +0x%x  file 0x%x: %016x -> %016x'
                   % (p, s7['i'], k, src, F17, F15, pos, oldq, newq))
    # verification: re-parse, only intended bytes changed
    h2, secs2, end2 = parse_drm(bytes(out), 'le')
    assert end2 == len(out) and [(s['type'], s['id'], s['size'], s['reloc_bytes']) for s in secs2] == \
        [(s['type'], s['id'], s['size'], s['reloc_bytes']) for s in secs]
    r2 = R.parse(bytes(out[s7['reloc_off']:s7['reloc_off'] + s7['reloc_bytes']]), 'le')
    exp = {CALLS[p] for p in which if p in CALLS}
    for (a, b) in zip(rel.external, r2.external):
        assert a == b or (a[1] in exp and b == (a[0], a[1], F15))
    assert r2.internal == rel.internal and r2.idref == rel.idref
    diff = [i for i in range(len(raw)) if raw[i] != out[i]]
    log.append('changed bytes: %d at %s' % (len(diff), sorted({hex(i & ~3) for i in diff})))
    return bytes(out)

def main():
    stored, raw = load()
    for v, which in VARIANTS.items():
        log = ['variant %s = %s' % (v, '+'.join(which)),
               'source: pc/patch.000 pc-w\\generalbank.drm stored %d B md5 %s, raw %d B md5 %s'
               % (len(stored), hashlib.md5(stored).hexdigest(), len(raw), hashlib.md5(raw).hexdigest())]
        new = build(raw, which, log)
        enc = DW.cdrm_encode(new, 'le')
        assert cdrm_decode(enc, 'le') == new
        d = OUT + v + '/'
        os.makedirs(d, exist_ok=True)
        open(d + 'generalbank.drm', 'wb').write(enc)
        log.append('output %sgeneralbank.drm CDRM %d B md5 %s (raw md5 %s)' % (d, len(enc), hashlib.md5(enc).hexdigest(),
                                                                          hashlib.md5(new).hexdigest()))
        open(d + 'patch_log.txt', 'w').write('\n'.join(log) + '\n')
        open(d + 'md5.txt', 'w').write('%s  generalbank.drm\n' % hashlib.md5(enc).hexdigest())
        print('\n'.join(log)); print()

if __name__ == '__main__':
    main()
