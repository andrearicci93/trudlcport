#!/usr/bin/env python3
"""fmod_init_guard.py - azzera le tre uscite locali di FUN_00582200 (init audio) per evitare l'AV 0x7b92fb quando FMOD System::init fallisce.

Causa (work/ws/codefirst/REPORT_crash_7b92fb.md): FUN_00582200 passa &local_c/&local_8/&local_4 a funzioni FMOD che NON scrivono l'uscita se
l'handle e' nullo / l'init e' fallita; local_4 resta con il residuo dello stack (0x586fe6 = ritorno di `call 0x574940`), il validatore 7c4cd3
controlla solo != 0 e `call [[local_4]+0x1c]` va in AV. Con le tre locali a 0 i validatori (7c4cd3/7bac01/7c4757) ritornano "handle non valido"
e le chiamate vengono saltate.

Patch (6 byte nell'originale + caverna nella coda zero di .text, VA 0x83de00):
  0x582200: 83 EC 0C 56 8B F1          sub esp,0xc ; push esi ; mov esi,ecx
        ->  E9 <rel32> 90              jmp cave ; nop
  cave   : 6A 00 6A 00 6A 00           push 0 x3        (stesso spazio di sub esp,0xc, ma azzerato)
           56                          push esi
           8B F1                       mov esi,ecx
           E9 <rel32>                  jmp 0x582206     (mov ecx,[esi] ...)
Layout dello stack e registri identici all'originale (eax/ecx/edx/esi invariati; solo i flag, mai letti prima della prossima scrittura).

Uso:  tools/venv/bin/python -I tools/fmod_init_guard.py IN.exe OUT.exe      (applica e verifica)
      tools/venv/bin/python -I tools/fmod_init_guard.py --check IN.exe      (dice se e' originale / gia' patchato)
Va applicato DOPO tap_build.py (che richiede l'exe unpacked intatto) oppure all'exe unpacked/LAA; la regione toccata e' identica in tutti.
Non scrive mai su IN.exe. Rifiuta se i byte attesi non coincidono."""
import sys, struct, hashlib

IB = 0x400000
ENTRY = 0x582200
RESUME = 0x582206
CAVE = 0x83DE00
ORIG = bytes.fromhex('83ec0c568bf1')
CAVE_CODE_PRE = bytes.fromhex('6a006a006a00' '56' '8bf1')      # 9 byte; poi jmp rel32


def sec_map(d):
    pe = struct.unpack_from('<I', d, 0x3c)[0]
    n = struct.unpack_from('<H', d, pe + 6)[0]; osz = struct.unpack_from('<H', d, pe + 20)[0]
    base = struct.unpack_from('<I', d, pe + 52)[0]
    out = []
    for i in range(n):
        o = pe + 24 + osz + 40 * i
        vs, va, rs, ro = struct.unpack_from('<IIII', d, o + 8)
        out.append((base + va, vs, ro, rs, d[o:o + 8].rstrip(b'\0').decode()))
    return out


def va2off(d, va):
    for v, vs, ro, rs, nm in sec_map(d):
        if v <= va < v + min(vs, rs) and nm == '.text': return ro + va - v
    raise ValueError('VA %#x non in .text' % va)


def patched_bytes():
    e = bytes([0xE9]) + struct.pack('<i', CAVE - (ENTRY + 5)) + b'\x90'
    c = CAVE_CODE_PRE + bytes([0xE9]) + struct.pack('<i', RESUME - (CAVE + len(CAVE_CODE_PRE) + 5))
    return e, c


def state(d):
    oe, oc = va2off(d, ENTRY), va2off(d, CAVE)
    e, c = patched_bytes()
    cur_e, cur_c = d[oe:oe + 6], d[oc:oc + len(c)]
    if cur_e == ORIG and cur_c == bytes(len(c)): return 'originale'
    if cur_e == e and cur_c == c: return 'patchato'
    return 'DIVERSO (entry %s, caverna %s)' % (cur_e.hex(), cur_c.hex())


def apply(d):
    if state(d) != 'originale': raise SystemExit('rifiuto: ' + state(d))
    b = bytearray(d); e, c = patched_bytes()
    oe, oc = va2off(d, ENTRY), va2off(d, CAVE)
    b[oe:oe + 6] = e; b[oc:oc + len(c)] = c
    return bytes(b)


def verify(orig, new):
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    diff = [i for i in range(len(orig)) if orig[i] != new[i]]
    e, c = patched_bytes()
    oe, oc = va2off(orig, ENTRY), va2off(orig, CAVE)
    allowed = set(range(oe, oe + 6)) | set(range(oc, oc + len(c)))
    assert len(orig) == len(new) and set(diff) <= allowed, 'byte modificati fuori dalle due regioni'
    # 1) entry: jmp cave; nop; il byte successivo (mov ecx,[esi]) e' intatto
    ins = list(md.disasm(new[oe:oe + 8], ENTRY))
    assert ins[0].mnemonic == 'jmp' and int(ins[0].op_str, 16) == CAVE and ins[1].mnemonic == 'nop', ins
    assert new[oe + 6:oe + 8] == bytes.fromhex('8b0e'), 'istruzione a 0x582206 alterata'
    # 2) caverna: effetto sullo stack/registri uguale all'originale
    cav = list(md.disasm(new[oc:oc + len(c)], CAVE))
    txt = [(i.mnemonic, i.op_str) for i in cav]
    assert txt[:3] == [('push', '0')] * 3 and txt[3] == ('push', 'esi') and txt[4] == ('mov', 'esi, ecx') and txt[5][0] == 'jmp' and int(txt[5][1], 16) == RESUME, txt
    o_ins = list(md.disasm(ORIG, ENTRY)); assert [(i.mnemonic, i.op_str) for i in o_ins] == [('sub', 'esp, 0xc'), ('push', 'esi'), ('mov', 'esi, ecx')]
    # stack delta: originale -0xc -4 ; nuovo 3*(-4) -4  => uguale; registri scritti: solo esi (in entrambi)
    assert 0xc + 4 == 3 * 4 + 4
    return len(diff), txt


def main():
    a = sys.argv[1:]
    if a and a[0] == '--check':
        print(state(open(a[1], 'rb').read())); return
    if len(a) != 2: raise SystemExit(__doc__)
    d = open(a[0], 'rb').read(); n = apply(d)
    nd, txt = verify(d, n)
    open(a[1], 'wb').write(n)
    print('scritto %s: %d byte modificati; caverna %s; in md5 %s out md5 %s' % (a[1], nd, txt, hashlib.md5(d).hexdigest()[:8], hashlib.md5(n).hexdigest()[:8]))


if __name__ == '__main__':
    main()
