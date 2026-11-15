"""Read-only: the uibitmap texture ids gpda_port kept without a rule (risk lines 'ut 320 path [0, 92]' of a
build_report.json) - is a texture section (type 5) of that id in the built g_pda, and in the PC g_pda?
Usage (repo root): ../bin/pyt work/crash_gpda_1411/tex_risk_check.py BUILD_REPORT.json BUILT_G_PDA"""
import sys, os, re, json, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sec_hex import load


def main(argv):
    rep = json.load(open(argv[0]))
    words = sorted({m.group(1) for r in rep['risks'] for m in [re.search(r'ut 320 path \[0, 92\] \+0x[0-9a-f]+: Xbox [0-9a-f]+ converted ([0-9a-f]{8})', r)] if m})
    tb = {i for t, i, d, rl in load(argv[1])[1] if t == 5}
    tp = {i for t, i, d, rl in load('pc:g_pda.drm')[1] if t == 5}
    for w in words:
        v = struct.unpack('<I', bytes.fromhex(w))[0]
        print('converted %s = texture id %d: in built g_pda %s, in PC g_pda %s' % (w, v, v in tb, v in tp))


if __name__ == '__main__':
    main(sys.argv[1:])
