"""Corrected merged locals (agent dlc_images, 2026-10-12): starts from work/generic/locals/mods/local/locals.bin_NNN (tools/locals.py build)
and applies the TU text where the TU changed an Xbox base placeholder but the PC text was a *localised* placeholder that the
equality rule of locals.merged() did not recognise: found by comparing every mapped id (6 languages) -> only Spanish (spec 0xfffff7f0, suffix 016):
 PC 450 'Mision Extra 1' -> TU 'BAJO LAS CENIZAS' (DLC mission 1 title in the DLC menu), PC 93 'Traje Extra 11' -> 'Traje seco rojo',
 PC 98 'Traje Extra 16' -> 'Traje humedo azul'. German PC 93 ('Roter Trockenanzug Leicht') is a real PC text and is kept.
Output: work/dlc_images/local/mods/local/locals.bin_{001,002,004,008,016,032} + md5.txt. Run: tools/venv/bin/python -I tools/locals_fix_dlcimg.py"""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import locals as L, dlc_text_cov as C
B = '/path/to/trudlcport/'
SRCDIR = B + 'work/generic/locals/mods/local/'
OUT = B + 'work/dlc_images/local/mods/local/'
FIX = {0xfffff7f0: [(450, 453), (93, 71), (98, 76)]}     # spec -> [(pc id, Xbox TU index)]
os.makedirs(OUT, exist_ok=True)
md5 = []
for spec in L.SPECS:
    suffix = (spec & 0x1f) if spec != 0xffffffe0 else 32
    fn = 'locals.bin_%03d' % suffix
    b = open(SRCDIR + fn, 'rb').read()
    lang, st, offs = L.parse(b, 'le')
    if spec in FIX:
        tu = C.table('tu', spec)[1]
        for p, x in FIX[spec]:
            print('spec %08x pc %d: %r -> %r' % (spec, p, st[p], tu[x])); st[p] = tu[x]
        nb = L.write_pc(lang, st, offs)
        back = L.parse(nb, 'le')[1]
        assert all(back[i] == st[i] for i in range(len(st)) if offs[i] != 0 and i != 0), 'readback'
        # untouched ids identical to source
        assert all(back[i] == L.parse(b, 'le')[1][i] for i in range(len(st)) if i not in [p for p, _ in FIX[spec]] and offs[i] != 0 and i != 0)
        assert [o == 0 for o in L.parse(nb, 'le')[2]] == [o == 0 for o in offs]
        b = nb
    open(OUT + fn, 'wb').write(b)
    md5.append('%s  mods/local/%s' % (hashlib.md5(b).hexdigest(), fn))
open(B + 'work/dlc_images/local/md5.txt', 'w').write('\n'.join(md5) + '\n')
print('\n'.join(md5))
