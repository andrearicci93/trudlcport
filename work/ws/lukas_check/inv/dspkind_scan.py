"""dspkind_scan.py - (19/11/2026) solo lettura. Regola dal fork (tools/soundplex_dsp_kind_fix.py, passo dspkind):
nodo SoundPlex DSP (tipo 12) di dlc_caverns_hall DTP 23469, record a +0x70: u16 kind a +0x74 deve essere {u16 kind LE, u16 0}
(Xbox 00 07 00 00 -> PC 07 00 00 00); grezzo 00 07 00 00 = kind 0x0700 fuori range -> nessun DSP (effetto eco assente).
In piu': cerca in tutti i DRM nodi {u32 12, ptr rec} con rec = {ptr, u16 kind, u16 0, ptr, 0} e controlla kind 1..11.
uso: python -I -B dspkind_scan.py BASELINE"""
import sys, os, struct, collections
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm_write as DW, drm_reloc as R
B = '/path/to/trudlcport/work/baseline/%s/mods/' % sys.argv[1]
BS = chr(92); st = collections.Counter()
for root, _, fs in os.walk(B):
    for f in sorted(fs):
        if not f.endswith('.drm'): continue
        p = os.path.join(root, f); rel = os.path.relpath(p, B).replace(BS, '/')
        try: S = DW.read(open(p, 'rb').read(), 'le').sections
        except Exception as e: print('ERR', rel, e); continue
        for s in S:
            if s.type != 7 or not s.reloc: continue
            it = dict(R.parse(s.reloc, 'le').internal); d = s.data
            for o, tg in it.items():
                if o < 4 or o % 4 or struct.unpack_from('<I', d, o - 4)[0] != 12: continue
                if tg + 16 > len(d) or tg not in it or (tg + 8) not in it: continue
                kind, pad = struct.unpack_from('<HH', d, tg + 4)
                ok = 1 <= kind <= 11 and pad == 0
                st['ok' if ok else 'bad'] += 1
                if not ok or (rel == 'dlc_caverns_hall.drm' and s.id == 23469):
                    print('%s %s DTP %d nodo +0x%x rec +0x%x bytes kind %s' % ('OK ' if ok else 'BAD', rel, s.id, o - 4, tg, d[tg + 4:tg + 8].hex()))
print('nodi DSP candidati', dict(st))
