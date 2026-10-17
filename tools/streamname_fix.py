"""Streamgroup-name string table of unit DRMs (type-0 section starting 'default\\0') damaged by the Xbox->PC word conversion
(agent savehang, 2026-10-12).  Case: dlc_watertunnel Xbox 'waterTunnel_main\\0dlc_watertunnel_waterTunnel_main\\0' -> PC
'waterTunnel_maincld\\0_watertunnel_waterTunnel_main' (word straddling NUL + next char byte-reversed).  The streamgroup name pointer then reads 'ld',
the engine requests StreamGroups\\ld.drm (never opens) -> the file-request queue head is stuck -> the save icon read behind it never completes ->
'Create new savegame' loops forever (see work/ws/savehang/NOTES_agent.md).
Rule: Xbox and PC sections are same length; tail from 'default\\0' is pure ASCII/NUL on Xbox -> copy the Xbox tail.
usage: tools/venv/bin/python -I tools/streamname_fix.py scan OVERLAY_DIR...
       tools/venv/bin/python -I tools/streamname_fix.py fix SRC_DRM OUT_DRM
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW
from soundplex_fix import xsecs_of

def fix_section(rel, raw):
    """-> (new_raw, log[(sec_index, offset, pc_bytes, xbox_bytes)])"""
    xs = xsecs_of(rel); D = DW.read(raw, 'le'); log = []
    if not xs: return raw, log
    for x in xs:
        if x['type'] != 0 or not x['data'] or b'default\0' not in x['data']: continue
        o = x['data'].find(b'default\0'); xt = x['data'][o:]
        if not all(c == 0 or 32 <= c < 127 for c in xt): continue
        for k, s in enumerate(D.sections):
            if s.type != 0 or len(s.data) != len(x['data']) or bytes(s.data)[o:o + 8] != b'default\0' and b'default\0' not in bytes(s.data): continue
            po = bytes(s.data).find(b'default\0')
            if po != o: continue
            if bytes(s.data)[o:] != xt:
                log.append((k, o, bytes(s.data)[o:], xt)); s.data = bytes(s.data)[:o] + xt
    if not log: return raw, log
    out = D.write('le')
    return (DW.cdrm_encode(out, 'le') if raw[:4] == b'CDRM' else out), log

if __name__ == '__main__':
    if sys.argv[1] == 'scan':
        for d in sys.argv[2:]:
            for f in sorted(os.listdir(d)):
                if f.lower().endswith('.drm'):
                    try: _, log = fix_section(f, open(os.path.join(d, f), 'rb').read())
                    except Exception as e: print(f, 'ERR', e); continue
                    for l in log: print(d, f, l[0], l[1], l[2][:70], '->', l[3][:70])
    else:
        src, dst = sys.argv[2], sys.argv[3]
        data, log = fix_section(os.path.basename(src), open(src, 'rb').read())
        open(dst, 'wb').write(data); print(os.path.basename(src), len(log), 'section(s) changed')
