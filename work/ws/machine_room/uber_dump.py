"""uber_dump.py - (20/11/2026) solo lettura. Blocco «uber» (macchina a stati delle animazioni) di un DTP oggetto: DTP +0xc8 -> U
(U+4 = 0x8080b00b), U+8 n DESC, U+0xc -> DESC (passo 0x60); DESC +4 n nodi, +8 -> nodi (28 B: +0x14 n azioni, +0x18 -> azioni 16 B);
DESC +0xc n transizioni, +0x10 -> transizioni (0x38 B). Stampa nodi/azioni/transizioni Xbox e PC fianco a fianco con la classe di
ogni parola (s32/s16/raw/altro). Struttura dal fork di Lukas (uber_words), lettura riscritta. uso: uber_dump.py BASELINE FILE.drm DTP"""
import sys, struct
sys.path.insert(0, '/path/to/trudlcport/work/ws/lukas_check/inv'); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW, drm_reloc as R
BL, F, DID = sys.argv[1], sys.argv[2], int(sys.argv[3])
p = [s for s in DW.read(open('/path/to/trudlcport/work/baseline/%s/mods/%s' % (BL, F), 'rb').read(), 'le').sections if s.type == 7 and s.id == DID][0]
x = [s for s in DW.read(C.xbox(F), 'be').sections if s.type == 7 and s.id == DID][0]
xd, pd = bytes(x.data), bytes(p.data); rx = R.parse(bytes(x.reloc), 'be'); it = dict(rx.internal)
sl = {o for o, _ in rx.internal} | {o for _, o in list(rx.idref) + list(rx.idref_a)}
U32 = lambda o: struct.unpack_from('>I', xd, o)[0]
def cls(o):
    a, b = xd[o:o + 4], pd[o:o + 4]
    if o in sl: return 'ptr/id'
    if a == b: return '=' if a == a[::-1] else 'RAW'
    if b == a[::-1]: return 's32'
    if b == a[1::-1] + a[:1:-1]: return 'S16'
    return 'ALTRO'
def row(o, n, tag):
    print('  %s @%#x: %s' % (tag, o, '  '.join('%s>%s %s' % (xd[q:q + 4].hex(), pd[q:q + 4].hex(), cls(q)) for q in range(o, o + n, 4))))
U = it[0xc8]; assert U32(U + 4) == 0x8080b00b
nd = U32(U + 8); D0 = it[U + 0xc]; print('U', hex(U), 'DESC', nd, hex(D0)); row(U, 0x10, 'U')
for m in range(nd):
    D = D0 + 0x60 * m; row(D, 0x60, 'DESC%d' % m)
    nn, N, nt, Tr = U32(D + 4), it.get(D + 8), U32(D + 0xc), it.get(D + 0x10)
    for k in range(nn if N else 0):
        nb = N + 28 * k; row(nb, 28, ' nodo%d' % k)
        na, A = U32(nb + 0x14), it.get(nb + 0x18)
        for j in range(na if A else 0): row(A + 16 * j, 16, '   azione%d.%d' % (k, j))
    for k in range(nt if Tr else 0): row(Tr + 0x38 * k, 0x38, ' trans%d' % k)
