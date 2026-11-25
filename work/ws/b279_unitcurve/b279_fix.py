"""b279_fix.py - (20/11/2026) B279: curve u16[64] dei record curva nei DTP unit (regola `unitcurve` del fork LukasKurthRocks,
logica riscritta in work/ws/lukas_check/inv/unitcurve_scan.py). Il convertitore ha scambiato le parole della curva come u32:
sul PC la rampa (monotona sull'Xbox) diventa a dente di sega. Giusto = s16 della parola Xbox (due u16 scambiati uno a uno).
Prova base (work/ws/machine_room/curve_proof.py): 435 rampe vere su 435 = s16, 0 contro.
Parole dal log della scansione sulla baseline sorgente (unitcurve_<BASELINE>.log, righe senza KEPT): 283 parole, machine_room 243
(10 curve), ceremony_room 29, dungeon 6 e caverns 5 (DLC1). Ogni parola: valore Xbox atteso, valore PC attuale = s32 della parola
Xbox (280) o grezzo (3, machine_room), nuovo = s16; nessun altro byte cambia (verifica parola per parola + round-trip).
uso: b279_fix.py --src BASELINE --out DIR [--dry]"""
import sys, os, re, hashlib, collections
R_ = '/path/to/trudlcport/'
sys.path.insert(0, R_ + 'work/ws/lukas_check/inv'); sys.path.insert(0, R_ + 'tools')
import inv_common as C, drm_write as DW
a = sys.argv; BL = a[a.index('--src') + 1]; SRC = R_ + 'work/baseline/%s/mods/' % BL; outd = a[a.index('--out') + 1]; dry = '--dry' in a
LOG = R_ + 'work/ws/lukas_check/inv/unitcurve_%s.log' % BL
RX = re.compile(r'^(\S+) \[(DLC\d)\] 7:(\d+) \+0x([0-9a-f]+) \S+ rec \+0x[0-9a-f]+ xbox ([0-9a-f]{8}) pc ([0-9a-f]{8}) atteso ([0-9a-f]{8}) \((\w+)\)$')
by = collections.defaultdict(list)
for l in open(LOG, encoding='utf-8'):
    if ' KEPT ' in l: sys.exit('parola KEPT nel log: ' + l)
    m = RX.match(l.strip())
    if m: by[m.group(1)].append((int(m.group(3)), int(m.group(4), 16), m.group(5), m.group(6), m.group(7), m.group(8)))
assert sum(map(len, by.values())) == 283, sum(map(len, by.values()))
outs = []
for f, ws in sorted(by.items()):
    raw = open(SRC + f, 'rb').read(); D = DW.read(raw, 'le'); X = DW.read(C.xbox(f), 'be'); plan = set()
    for d, o, xh, oh, nh, k in ws:
        assert (k == 's32' and bytes.fromhex(oh) == bytes.fromhex(xh)[::-1]) or (k == 'raw' and oh == xh), (f, hex(o), k)
        x = bytes.fromhex(xh); assert bytes.fromhex(nh) == bytes((x[1], x[0], x[3], x[2])), (f, hex(o))
        hs = [i for i, s in enumerate(D.sections) if s.type == 7 and s.id == d]; assert len(hs) == 1, (f, d)
        xs = [s for s in X.sections if s.type == 7 and s.id == d]; assert len(xs) == 1 and xs[0].data[o:o + 4].hex() == xh, (f, d, hex(o), 'xbox')
        s = D.sections[hs[0]]; b = bytearray(s.data); assert b[o:o + 4].hex() == oh, (f, d, hex(o), 'pc', b[o:o + 4].hex())
        b[o:o + 4] = bytes.fromhex(nh); s.data = bytes(b); plan.add((hs[0], o))
    o_ = D.write('le')
    if raw[:4] == b'CDRM': o_ = DW.cdrm_encode(o_, 'le')
    D0, D2 = DW.read(raw, 'le'), DW.read(o_, 'le'); ch = set()
    assert len(D0.sections) == len(D2.sections)
    for i, (x, y) in enumerate(zip(D0.sections, D2.sections)):
        assert (x.type, x.id, x.reloc, len(x.data)) == (y.type, y.id, y.reloc, len(y.data))
        ch |= {(i, j - j % 4) for j in range(len(x.data)) if x.data[j] != y.data[j]}
    assert ch == plan, (f, sorted(ch ^ plan))
    rt = DW.read(o_, 'le').write('le'); rt = DW.cdrm_encode(rt, 'le') if o_[:4] == b'CDRM' else rt; assert rt == o_, 'round-trip'
    print('%-28s parole %d' % (f, len(plan))); outs.append((f, o_))
if not dry:
    os.makedirs(outd, exist_ok=True)
    for rel, o_ in outs: open(os.path.join(outd, rel), 'wb').write(o_)
    with open(os.path.join(outd, 'md5.txt'), 'w', newline='\n') as fo:
        fo.write(''.join('%s  %s\n' % (hashlib.md5(o_).hexdigest(), rel) for rel, o_ in outs))
print('file', len(outs), 'scritti' if not dry else '(dry)')
