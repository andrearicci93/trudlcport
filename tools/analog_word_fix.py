"""analog_word_fix.py - DLC DTPs converted by the generic 'convert' route (learned type-7 table) that are near-clones of a
base Xbox DTP (same size + same Xbox reloc layout, >= MIN_SAME of the words identical): every NON-reloc word whose Xbox DLC
bytes equal the analog's Xbox bytes must equal the analog's PC bytes (same source value -> same PC value), unless PC
re-authored that DTP.  Words where our converted bytes differ are byte-class errors of the learned table (example:
knight_thrall_chunkdoll DTP 20951 +0x130/+0x158 = {u8,u8,u16} record header converted as {u16,u16}: 02 00 00 0f -> ours
00 02 0f 00, PC viking 14553 02 00 0f 00).
Guard against PC re-authoring: the analog's own Xbox->PC pair must be 'class-consistent' at that word (PC bytes are a byte
permutation of the Xbox bytes: u32/u16u16/u8u8u16/u16u8u8/raw), and the base pair must differ in < MAX_PAIR_REAUTH words.
usage:
  tools/venv/bin/python -I tools/analog_word_fix.py scan DIR[,DIR..] [names..]          (overlay low->high, report only)
  tools/venv/bin/python -I tools/analog_word_fix.py fix OUTDIR DIR[,DIR..] names..      (write patched DRMs to OUTDIR)"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW, drm_reloc as R, dlc_generic as DG, dtpid_sweep as DS
from soundplex_fix import load_overlay, xsecs_of

MIN_SAME = 0.90
PERMS = {'u32': (3, 2, 1, 0), 'u16u16': (1, 0, 3, 2), 'u8u8u16': (0, 1, 3, 2), 'u16u8u8': (1, 0, 2, 3), 'raw': (0, 1, 2, 3)}

def perm_ok(xw, pw):
    return any(bytes(xw[i] for i in pm) == pw for pm in PERMS.values())

def best_analog(s, st, ids):
    cands = DG.analog_index(st, ids).get((7, len(s['data']), DG._reloc_sig(s['reloc'], 'be')), ())
    best = None
    for ax in cands:
        xd = st['xb_store'][(7, ax)]['data']
        same = sum(1 for k in range(0, len(xd) - 3, 4) if xd[k:k + 4] == s['data'][k:k + 4])
        if best is None or same > best[0]: best = (same, ax)
    if best is None or best[0] < MIN_SAME * (len(s['data']) // 4): return None
    return best[1]

def fix_section(s, ours, st, ids):
    ax = best_analog(s, st, ids)
    if ax is None: return None, []
    xb = st['xb_store'][(7, ax)]['data']; pid = ids.base[7][ax]; pc = st['pc_store'][(7, pid)]
    pd = pc['data']
    if len(pd) != len(xb) or dict(R.parse(pc['reloc'], 'le').internal) != dict(R.parse(st['xb_store'][(7, ax)]['reloc'], 'be').internal):
        return None, []
    it = dict(R.parse(s['reloc'], 'be').internal)
    new = bytearray(ours); log = []
    for k in range(0, len(xb) - 3, 4):
        if k in it: continue
        xw, aw, pw, ow = s['data'][k:k + 4], xb[k:k + 4], pd[k:k + 4], bytes(ours[k:k + 4])
        if xw != aw or ow == pw: continue
        if not perm_ok(aw, pw): log.append((ax, pid, k, ow.hex(), pw.hex(), 'SKIP_reauthored')); continue
        new[k:k + 4] = pw; log.append((ax, pid, k, ow.hex(), pw.hex(), 'fix'))
    return bytes(new), log

def process(rel, path, st, ids):
    xs = xsecs_of(rel)
    if xs is None: return None, []
    raw = open(path, 'rb').read(); D = DW.read(raw, 'le'); logs = []
    for s, i in DS.pairs(xs, D, ids):
        sec = D.sections[i]
        if len(sec.data) != len(s['data']): continue
        new, log = fix_section(s, sec.data, st, ids)
        if log: logs += [(sec.id,) + l for l in log]
        if new is not None and new != sec.data and any(l[-1] == 'fix' for l in log): sec.data = new
    if not any(l[-1] == 'fix' for l in logs): return None, logs
    out = D.write('le')
    if raw[:4] == b'CDRM': out = DW.cdrm_encode(out, 'le')
    return out, logs

if __name__ == '__main__':
    st, ids = DS.ctx(); ids.local = {}
    cmd = sys.argv[1]
    if cmd == 'scan':
        files = load_overlay(sys.argv[2].split(','), set(sys.argv[3:]) or None); tot = collections.Counter()
        for rel, path in sorted(files.items()):
            _, logs = process(rel, path, st, ids)
            if logs:
                c = collections.Counter(l[-1] for l in logs); tot.update(c)
                print(rel, dict(c), [(l[0], l[1], hex(l[3]), l[4], l[5]) for l in logs[:6]])
        print('TOTAL', dict(tot))
    elif cmd == 'fix':
        out = sys.argv[2]; os.makedirs(out, exist_ok=True)
        files = load_overlay(sys.argv[3].split(','), set(sys.argv[4:]))
        for rel, path in sorted(files.items()):
            new, logs = process(rel, path, st, ids)
            for l in logs: print(rel, 'DTP', l[0], 'analog xb', l[1], 'pc', l[2], hex(l[3]), l[4], '->', l[5], l[6])
            if new is not None:
                dst = os.path.join(out, rel); os.makedirs(os.path.dirname(dst) or out, exist_ok=True)
                open(dst, 'wb').write(new); print('wrote', dst)
