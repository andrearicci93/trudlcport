#!/usr/bin/env python3
"""Stub x86 del 'log tap' S1 (vedi PIANO_SONNET.md, M0). Solo generazione + autoverifica: NON modifica file.

  tools/venv/bin/python -I tools/tap_stubs.py        # selftest: disassembla con capstone e confronta con l'atteso

Schema (sezione nuova .tap all'RVA 0xe36000 dell'exe unpacked, base fissa 0x400000, nessun reloc):
  T+0x00 'TAP1'   T+0x04 contatore (lock xadd)   T+0x08 dimensione slot (64)   T+0x0C numero slot (4096)
  T+0x10 VA ring  T+0x14 build id (u32 dal md5 di sites_patched.tsv)   T+0x18 VA stubA   T+0x1C VA stubB
  T+0x100 stubA (canale 0xA: chiamate di log che andavano al 'ret' 0x6457a0; finisce con ret)
  T+0x200 stubB (canale 0xB: chiamate al logger vero 0x48e200; finisce con jmp 0x48e200, funzione originale intatta)
  T+0x1000 ring: 4096 slot da 64 B = {+0 seq (0 = in scrittura), +4 ret (= call+5, identifica il sito), +8 tid,
           +0xC canale, +0x10 arg0, +0x14..+0x3F arg1..arg11}
Si riscrive SOLO il rel32 delle call dei siti scelti (stessa lunghezza): nessun corpo di funzione viene toccato.
0x6457a0 NON va patchato: e' una funzione vuota condivisa dal linker (649 riferimenti assoluti, 301 in .rdata = vtable).
Seqlock: seq azzerato con xchg (barriera) prima di scrivere i campi, poi seq = n con xchg (barriera).
Il lettore legge seq, slot, seq: scarta se seq e' 0 o cambiato; se il contatore avanza di piu' di 4096 tra due letture scrive 'PERSI n'.
"""
import struct

IB = 0x400000
T = IB + 0xe36000            # VA sezione .tap (= SizeOfImage attuale dell'unpacked 56d1ce2d)
RVA = 0xe36000
VSIZE = 0x50000              # ring 0x40000 + header + margine
RAWSIZE = 0x1000
SLOT, NSLOT = 64, 4096
RING = T + 0x1000
STUB_A, STUB_B = T + 0x100, T + 0x200
LOGGER_B = 0x48e200
CHAN_A, CHAN_B = 0xA, 0xB


def p32(x): return struct.pack('<I', x & 0xffffffff)


def rel32(frm, to): return p32(to - (frm + 5))


def body(chan):
    c = b''
    c += b'\x9c'                                  # pushfd
    c += b'\x60'                                  # pushad            (36 byte: ret del chiamante a [esp+0x24])
    c += b'\xfc'                                  # cld
    c += b'\xb8' + p32(1)                         # mov eax,1
    c += b'\xf0\x0f\xc1\x05' + p32(T + 4)         # lock xadd [T+4],eax   -> eax = contatore precedente
    c += b'\x8b\xd0'                              # mov edx,eax
    c += b'\x25' + p32(NSLOT - 1)                 # and eax,0xfff
    c += b'\xc1\xe0\x06'                          # shl eax,6
    c += b'\x05' + p32(RING)                      # add eax,RING      -> eax = slot
    c += b'\x31\xc9'                              # xor ecx,ecx
    c += b'\x87\x08'                              # xchg [eax],ecx    seq = 0 (barriera)
    c += b'\x8b\x4c\x24\x24'                      # mov ecx,[esp+0x24]   ret del chiamante
    c += b'\x89\x48\x04'                          # mov [eax+4],ecx
    c += b'\x64\x8b\x0d' + p32(0x24)              # mov ecx,fs:[0x24]    thread id (TEB32)
    c += b'\x89\x48\x08'                          # mov [eax+8],ecx
    c += b'\xc7\x40\x0c' + p32(chan)              # mov dword [eax+0xc],chan
    c += b'\x8b\x4c\x24\x28'                      # mov ecx,[esp+0x28]   arg0
    c += b'\x89\x48\x10'                          # mov [eax+0x10],ecx
    c += b'\x8d\x74\x24\x2c'                      # lea esi,[esp+0x2c]   arg1..
    c += b'\x8d\x78\x14'                          # lea edi,[eax+0x14]
    c += b'\xb9' + p32(11)                        # mov ecx,11
    c += b'\xf3\xa5'                              # rep movsd
    c += b'\x8d\x4a\x01'                          # lea ecx,[edx+1]
    c += b'\x87\x08'                              # xchg [eax],ecx    seq = n (commit, barriera)
    c += b'\x61'                                  # popad
    c += b'\x9d'                                  # popfd
    return c


def stub_a():
    return body(CHAN_A) + b'\xc3'                                  # ret (come il 'ret' originale di 0x6457a0)


def stub_b():
    c = body(CHAN_B)
    return c + b'\xe9' + rel32(STUB_B + len(c), LOGGER_B)          # jmp 0x48e200 (il logger originale gira e torna al chiamante)


PROBE_BASE, PROBE_STRIDE, PROBE_MAX = T + 0x300, 0x80, 24     # S1b: stub sonda k a T+0x300+k*0x80 (k < 24, fino a T+0xF00)
CHAN_PROBE = 0xC0000                                          # campo canale = 0xC0000 | id sonda


def body_probe(probe_id):
    """S1b 'punto sonda': come body() ma salva ecx/edx ORIGINALI (this/fastcall) e arg0..arg9.
    Slot: +0 seq, +4 ret, +8 tid, +0xC 0xC0000|id, +0x10 ecx, +0x14 edx, +0x18..+0x3F arg0..arg9.
    Dopo pushfd+pushad: [esp+0x18] = ecx originale, [esp+0x14] = edx originale, [esp+0x24] = ret, [esp+0x28] = arg0."""
    c = b''
    c += b'\x9c\x60\xfc'                          # pushfd; pushad; cld
    c += b'\xb8' + p32(1)                         # mov eax,1
    c += b'\xf0\x0f\xc1\x05' + p32(T + 4)         # lock xadd [T+4],eax
    c += b'\x8b\xd0'                              # mov edx,eax
    c += b'\x25' + p32(NSLOT - 1)                 # and eax,0xfff
    c += b'\xc1\xe0\x06'                          # shl eax,6
    c += b'\x05' + p32(RING)                      # add eax,RING
    c += b'\x31\xc9\x87\x08'                      # xor ecx,ecx; xchg [eax],ecx   (seq = 0)
    c += b'\x8b\x4c\x24\x24\x89\x48\x04'          # ret -> +4
    c += b'\x64\x8b\x0d' + p32(0x24) + b'\x89\x48\x08'   # tid -> +8
    c += b'\xc7\x40\x0c' + p32(CHAN_PROBE | probe_id)  # canale/id -> +0xC
    c += b'\x8b\x4c\x24\x18\x89\x48\x10'          # ecx originale -> +0x10
    c += b'\x8b\x4c\x24\x14\x89\x48\x14'          # edx originale -> +0x14
    c += b'\x8d\x74\x24\x28'                      # lea esi,[esp+0x28]   arg0..
    c += b'\x8d\x78\x18'                          # lea edi,[eax+0x18]
    c += b'\xb9' + p32(10)                        # mov ecx,10
    c += b'\xf3\xa5'                              # rep movsd
    c += b'\x8d\x4a\x01\x87\x08'                  # lea ecx,[edx+1]; xchg [eax],ecx   (commit)
    c += b'\x61\x9d'                              # popad; popfd
    return c


def stub_probe(probe_id, target):
    """Stub sonda: registra e poi jmp alla funzione ORIGINALE (si riscrivono le call rel32 verso target, oppure lo slot di vtable)."""
    assert 0 <= probe_id < PROBE_MAX
    va = PROBE_BASE + probe_id * PROBE_STRIDE
    c = body_probe(probe_id)
    c += b'\xe9' + rel32(va + len(c), target)
    assert len(c) <= PROBE_STRIDE
    return va, c


# ---- S1b' sonda "a ritorno": registra argomenti (ingresso) e valore restituito (uscita) di una funzione chiamata con call rel32.
# Funziona per funzioni cdecl o stdcall: l'indirizzo di ritorno originale e' salvato in memoria (non rientrante: una sonda per sito).
COMMON_RET = T + 0x280                     # routine comune di log (<= 0x80 byte), sopra stubB (T+0x200..T+0x25c)
RET_SAVE_BASE, RET_SAVE_STRIDE, RET_MAX = T + 0xF00, 0x20, 8   # area di salvataggio: ret, a0..a3, risultato, id (7 dword)


def common_ret():
    """eax = puntatore all'area S = {+0 ret, +4..+0x10 a0..a3, +0x14 risultato, +0x18 id}. Conserva registri e flag.
    Slot: +4 ret, +8 tid, +0xC 0xC0000|id, +0x10 a0, +0x14 a1, +0x18 a2, +0x1C a3, +0x20 risultato."""
    c = b''
    c += b'\x9c\x60\xfc'                          # pushfd; pushad; cld
    c += b'\x8b\xf0'                              # mov esi,eax
    c += b'\xb8' + p32(1)                         # mov eax,1
    c += b'\xf0\x0f\xc1\x05' + p32(T + 4)         # lock xadd [T+4],eax
    c += b'\x8b\xd0'                              # mov edx,eax
    c += b'\x25' + p32(NSLOT - 1)                 # and eax,0xfff
    c += b'\xc1\xe0\x06'                          # shl eax,6
    c += b'\x05' + p32(RING)                      # add eax,RING
    c += b'\x31\xc9\x87\x08'                      # xor ecx,ecx; xchg [eax],ecx (seq = 0)
    c += b'\x8b\x0e\x89\x48\x04'                  # mov ecx,[esi]; mov [eax+4],ecx   (ret originale)
    c += b'\x64\x8b\x0d' + p32(0x24) + b'\x89\x48\x08'   # tid -> +8
    c += b'\x8b\x4e\x18'                          # mov ecx,[esi+0x18]  (id)
    c += b'\x81\xc9' + p32(CHAN_PROBE)            # or ecx,0xC0000
    c += b'\x89\x48\x0c'                          # mov [eax+0xc],ecx
    c += b'\x8d\x78\x10'                          # lea edi,[eax+0x10]
    c += b'\x83\xc6\x04'                          # add esi,4
    c += b'\xb9' + p32(5)                         # mov ecx,5   (a0..a3, risultato)
    c += b'\xf3\xa5'                              # rep movsd
    c += b'\x8d\x4a\x01\x87\x08'                  # lea ecx,[edx+1]; xchg [eax],ecx (commit)
    c += b'\x61\x9d\xc3'                          # popad; popfd; ret
    assert len(c) <= 0x80, len(c)
    return c


def stub_retprobe(probe_id, target):
    """Stub sonda a ritorno per la call rel32 verso `target`. Ritorna (va, code)."""
    assert 0 <= probe_id < RET_MAX
    va = PROBE_BASE + probe_id * PROBE_STRIDE
    S = RET_SAVE_BASE + probe_id * RET_SAVE_STRIDE
    c = b''
    c += b'\x58'                                   # pop eax            (ret originale)
    c += b'\xa3' + p32(S)                         # mov [S],eax
    for i in range(4):                             # a0..a3 dalla pila (valide per cdecl e stdcall con >= 4 slot leggibili)
        c += b'\x8b\x44\x24' + bytes([4 * i])       # mov eax,[esp+4i]
        c += b'\xa3' + p32(S + 4 + 4 * i)         # mov [S+4+4i],eax
    Lpos = len(c)
    c += b'\x68' + p32(0)                         # push L (da fissare)
    c += b'\xe9' + rel32(va + len(c), target)     # jmp target
    L = va + len(c)
    c = c[:Lpos + 1] + p32(L) + c[Lpos + 5:]
    c += b'\xa3' + p32(S + 0x14)                  # mov [S+0x14],eax   (risultato)
    c += b'\xc7\x05' + p32(S + 0x18) + p32(probe_id)   # mov dword [S+0x18],id
    c += b'\xb8' + p32(S)                         # mov eax,S
    c += b'\xe8' + rel32(va + len(c), COMMON_RET)  # call COMMON_RET (rel32 calcolato su va+len(c))
    c += b'\xa1' + p32(S + 0x14)                  # mov eax,[S+0x14]   (ripristina il risultato)
    c += b'\xff\x25' + p32(S)                    # jmp dword [S]       (torna al chiamante originale)
    assert len(c) <= PROBE_STRIDE, len(c)
    return va, c


def header(build_id=0):
    h = b'TAP1' + p32(0) + p32(SLOT) + p32(NSLOT) + p32(RING) + p32(build_id) + p32(STUB_A) + p32(STUB_B)
    return h


def raw_section(build_id=0):
    """0x1000 byte del contenuto su disco della sezione .tap (il ring sta nella parte virtuale azzerata)."""
    r = bytearray(RAWSIZE)
    h = header(build_id); r[0:len(h)] = h
    a, b = stub_a(), stub_b()
    r[0x100:0x100 + len(a)] = a
    r[0x200:0x200 + len(b)] = b
    return bytes(r)


def section_header():
    """IMAGE_SECTION_HEADER (40 byte) per .tap: raw a 0x620000 (= fine del file unpacked), RWX + codice + dati inizializzati."""
    return (b'.tap\0\0\0\0' + p32(VSIZE) + p32(RVA) + p32(RAWSIZE) + p32(0x620000) +
            p32(0) + p32(0) + struct.pack('<HH', 0, 0) + p32(0xE0000060))


EXPECTED = [
    'pushfd', 'pushal', 'cld', 'mov eax, 1', 'lock xadd dword ptr [%#x], eax' % (T + 4), 'mov edx, eax', 'and eax, 0xfff',
    'shl eax, 6', 'add eax, %#x' % RING, 'xor ecx, ecx', 'xchg dword ptr [eax], ecx', 'mov ecx, dword ptr [esp + 0x24]',
    'mov dword ptr [eax + 4], ecx', 'mov ecx, dword ptr fs:[0x24]', 'mov dword ptr [eax + 8], ecx',
    'mov dword ptr [eax + 0xc], %s', 'mov ecx, dword ptr [esp + 0x28]', 'mov dword ptr [eax + 0x10], ecx',
    'lea esi, [esp + 0x2c]', 'lea edi, [eax + 0x14]', 'mov ecx, 0xb', 'rep movsd dword ptr es:[edi], dword ptr [esi]',
    'lea ecx, [edx + 1]', 'xchg dword ptr [eax], ecx', 'popal', 'popfd']


def selftest(verbose=True):
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    for name, code, va, chan, tail in (('stubA', stub_a(), STUB_A, '0xa', ['ret']),
                                       ('stubB', stub_b(), STUB_B, '0xb', ['jmp %#x' % LOGGER_B])):
        got = [(i.mnemonic + ' ' + i.op_str).strip() for i in md.disasm(code, va)]
        exp = [e % chan if '%s' in e else e for e in EXPECTED] + tail
        assert sum(i.size for i in md.disasm(code, va)) == len(code), name + ': decodifica incompleta'
        assert got == exp, '%s diverso:\n%s' % (name, '\n'.join('%-50s %s' % (g, e) for g, e in zip(got, exp) if g != e))
        if verbose: print('%s @%#x: %d byte, %d istruzioni OK  %s' % (name, va, len(code), len(got), code.hex()))
    # S1b: stub sonda di esempio (id 3 verso 0x6ecca0 = validazione rampino)
    va, code = stub_probe(3, 0x6ecca0)
    got = [(i.mnemonic + ' ' + i.op_str).strip() for i in md.disasm(code, va)]
    assert sum(i.size for i in md.disasm(code, va)) == len(code), 'probe: decodifica incompleta'
    must = ['mov ecx, dword ptr [esp + 0x18]', 'mov dword ptr [eax + 0x10], ecx', 'mov ecx, dword ptr [esp + 0x14]',
            'mov dword ptr [eax + 0x14], ecx', 'lea esi, [esp + 0x28]', 'lea edi, [eax + 0x18]', 'mov ecx, 0xa',
            'mov dword ptr [eax + 0xc], %#x' % (CHAN_PROBE | 3), 'popal', 'popfd', 'jmp 0x6ecca0']
    assert all(m in got for m in must) and got[-3:] == ['popal', 'popfd', 'jmp 0x6ecca0'], 'probe diverso: %s' % got
    if verbose: print('probe id3 @%#x -> jmp 0x6ecca0: %d byte, %d istruzioni OK' % (va, len(code), len(got)))
    rs = raw_section()
    assert rs[:4] == b'TAP1' and len(rs) == RAWSIZE and len(section_header()) == 40
    assert RING + SLOT * NSLOT <= T + VSIZE
    if verbose: print('layout: T=%#x ring=%#x..%#x vsize=%#x raw=%#x @file 0x620000; SizeOfImage nuovo=%#x' % (
        T, RING, RING + SLOT * NSLOT, VSIZE, RAWSIZE, RVA + VSIZE))
    return True


if __name__ == '__main__':
    selftest()
