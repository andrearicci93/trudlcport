"""Restore ASCII name strings whose first bytes were swapped by the converter (u16-pair rule applied to text).

Case found 2026-10-12 (user VM test: underwater chain of the raft bridge could not be shot/released):
dlc1_uo_raft_bridge DTP 20765 +1312 Xbox 'chain_free' -> PC 'hcian_free' (first 4 bytes swapped as two u16).  The DTP is the
raft anim/state table ('Initial','chain_fall','float_up','chain_free','free_raft','idle'); a name that no state lookup matches
would keep the platform from being released.  Not proven in the engine; hypothesis to be tested in the VM.
Targeted list only (a generic ASCII rule would also touch binary data that looks like text and the rebuilt sig_* name streams).
usage: tools/venv/bin/python -I tools/name_string_fix.py SRC_DRM OUT_DRM
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW
from soundplex_fix import xsecs_of

FIXES = {'dlc1_uo_raft_bridge.drm': [(20765, 1312, 10)]}      # (PC DTP id, offset, length)

def fix(rel, raw):
    xs = xsecs_of(rel); D = DW.read(raw, 'le'); log = []
    for sid, off, n in FIXES[rel]:
        x = next(s for s in xs if s['type'] == 7 and s['id'] == sid)       # Xbox DTP with the same id (raft: 20765 on both)
        sec = next(s for s in D.sections if s.type == 7 and s.id == sid)
        assert len(x['data']) == len(sec.data) and x['data'][off:off + n].isascii()
        if sec.data[off:off + n] != x['data'][off:off + n]:
            log.append((sid, off, bytes(sec.data[off:off + n]), bytes(x['data'][off:off + n])))
            sec.data = sec.data[:off] + x['data'][off:off + n] + sec.data[off + n:]
    out = D.write('le')
    return (DW.cdrm_encode(out, 'le') if raw[:4] == b'CDRM' else out), log

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    data, log = fix(os.path.basename(src), open(src, 'rb').read())
    open(dst, 'wb').write(data); print(os.path.basename(src), log)
