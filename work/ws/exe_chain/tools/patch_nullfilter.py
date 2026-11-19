#!/usr/bin/env python3
"""patch_nullfilter.py IN.exe OUT.exe -- RICOSTRUZIONE (14/11, da delta binario) dello stadio s8n: 3 guardie "filtro markup nullo".
L'originale (scratchpad Mac, 27/10) e' andato perso; questo script riscrive ESATTAMENTE i 76 byte di differenza
tru_b159_s8_fe_cs.exe (9cb61a7d) -> tru_s8n_cs.exe (149d3132), con asserzione su md5 di ingresso/uscita e sui byte originali.
Contesto (MEMORIA project-gold-standard-b231, TEST VM 27/10): s1 = AV 0x723335 (arg2 filtro markup nullo in 0x723330, chiamato dal
ciclo 0x7295a0 che scorre [esi+0x18]). Guardia: puntatore < 0x10000 trattato come "nessun filtro".
  0x723330 (5B push esi; mov esi,[esp+8]) -> jmp G1 0x123f800: push esi; mov esi,[esp+0xc]; cmp esi,0x10000; jae ->0x723335; mov al,1; pop esi; ret
  0x723380 (5B, gemello)                  -> jmp G2 0x123f820: push esi; mov esi,[esp+0xc]; cmp esi,0x10000; jb 0x7233cf; jmp 0x723385
  0x7295a0 (7B mov edx,[ebx+ebp*4]; mov eax,[esp+0x10]) -> jmp G3 0x123f840 + 2 nop: mov edx,[ebx+ebp*4]; cmp edx,0x10000; jb 0x729648;
           mov eax,[esp+0x10]; jmp 0x7295a7
Cave in .tuext 0x123f800..0x123f857 (zero in IN). Non scrive mai su IN."""
import sys, hashlib
IN_MD5 = '9cb61a7d02d25d08febfaaee0ac0e234'; OUT_MD5 = '149d31325078f4427b1fd4359482d442'
TUEXT_VA, TUEXT_RAW = 0x1237000, 0x621000
P = [  # (va, byte originali, byte nuovi)
    (0x723330, '568b74240c', 'e9cbc4b100'),
    (0x723380, '568b74240c', 'e99bc4b100'),
    (0x7295a0, '8b14ab8b442410', 'e99b62b1009090'),
    (0x123f800, '00' * 22, '568b74240c81fe000001007304b0015ec3e91f3b4eff'),
    (0x123f820, '00' * 22, '568b74240c81fe000001000f829e3b4effe94f3b4eff'),
    (0x123f840, '00' * 24, '8b14ab81fa000001000f82f99d4eff8b442410e94f9d4eff'),
]


def off(va): return va - TUEXT_VA + TUEXT_RAW if va >= TUEXT_VA else va - 0x400000   # .text: raw == rva (exe realign)


def main():
    src, dst = sys.argv[1:3]
    d = bytearray(open(src, 'rb').read())
    assert hashlib.md5(d).hexdigest() == IN_MD5, 'IN non e\' tru_b159_s8_fe_cs.exe (9cb61a7d)'
    for va, o, n in P:
        o, n = bytes.fromhex(o), bytes.fromhex(n); f = off(va)
        assert len(o) == len(n) and d[f:f + len(o)] == o, (hex(va), d[f:f + len(o)].hex())
        d[f:f + len(n)] = n
    m = hashlib.md5(d).hexdigest(); assert m == OUT_MD5, m
    open(dst, 'wb').write(d); print('ok', dst, m)


if __name__ == '__main__':
    main()
