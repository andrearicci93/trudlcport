"""SoundPlex 'properties' node (type 4) records in DTP data: typed check / fix ('soundplex').

Background (crash 0x5912a3, dump next_spiders_20_45.dmp, NOTES 2026-10-10): a sound plex is a tree of nodes {u32 type 0..13,
ptr data} walked by 0x5920b0 (jump table 0x5923cc).  Type 4 (handler 0x590970) has a 0x48-byte data record:
  +0x00 ptr child node, +0x04..+0x3c s32/f32 words, +0x40 s32 SOUND GROUP index (0 / -1 = inherit from parent params,
  copied to params+0x14 and inherited by every child type-4 that has 0/-1), +0x44 {u8 max instances, u8 live counter
  (engine increments it), u16 (byte +0x47 & 0x7f read)}.
The leaf wave node (type 2, 0x591220) indexes the 77-entry x 0x84 group table [0x8a80d8] with params+0x14 (bounds check at
0x591281 only logs via 0x6457a0) -> an unconverted group (Xbox 0x2d left raw = 0x2d000000) reads far out of the table -> AV.
The learned type-7 table left +0x40 raw and gave +0x44 a u32 swap in DLC-new sound DTPs (dlc1_uo_sewer_gate 21104).

Detection (Xbox side): internal reloc at o with BE word at o-4 == 4 -> data t; t is itself a pointer slot (child) whose
target is a node {type <= 13, ptr}; BE +0x40 in [-1, 0x4c]; no pointer slot in t+4..t+0x44.
Rule (base pairs, `calibrate`): every word t+4..t+0x40 = s32 (u32 swap), t+0x44 = {u8,u8,u16}.
CLI: tools/venv/bin/python -I tools/soundplex_fix.py calibrate
     tools/venv/bin/python -I tools/soundplex_fix.py scan DIR[,DIR..] [name.drm ..]        (dirs: later wins)
     tools/venv/bin/python -I tools/soundplex_fix.py patch OUTDIR DIR[,DIR..] name.drm ..
"""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R, drm_write as DW
import dlc_generic as DG, generic_store
from drm import cdrm_decode, sections_with_data

NGROUPS = 0x4d          # [0x8a80dc] in tru.exe (PC): number of sound groups
REC = 0x48

def want_word(xd, q, k):
    xb = xd[q:q + 4]
    if k == 0x44: return xb[0:2] + xb[3:1:-1]                # {u8, u8, u16}
    return xb[::-1]                                           # s32 / f32

def records(xd, xreloc):
    """offsets t of type-4 data records in an Xbox (BE) DTP"""
    rel = R.parse(xreloc, 'be'); ptr = dict(rel.internal)
    slots = set(rel.pointer_offsets()) | set(rel.id_offsets())
    out = []
    for o, tg in rel.internal:
        if o < 4 or o % 4 or struct.unpack_from('>I', xd, o - 4)[0] != 4: continue
        if tg % 4 or tg + REC > len(xd) or tg not in slots: continue
        ch = ptr.get(tg)
        if ch is None or ch + 8 > len(xd) or struct.unpack_from('>I', xd, ch)[0] > 13 or (ch + 4) not in ptr: continue
        if not (-1 <= struct.unpack_from('>i', xd, tg + 0x40)[0] <= NGROUPS - 1): continue
        if any(tg + k in slots for k in range(4, REC, 4)): continue
        out.append(tg)
    return sorted(set(out))

def fix_section(xd, xreloc, pd):
    """-> (new pc bytes, [(rec, k, old, new)])"""
    b = bytearray(pd); log = []
    for t in records(xd, xreloc):
        for k in range(4, REC, 4):
            w = want_word(xd, t + k, k)
            if b[t + k:t + k + 4] != w:
                log.append((t, k, bytes(b[t + k:t + k + 4]).hex(), w.hex())); b[t + k:t + k + 4] = w
    return bytes(b), log

def calibrate():
    st = generic_store.load(); ids = DG.DlcIds(st, None)
    n = nrec = 0; bad = collections.Counter(); ex = []
    for (t, x), xb in st['xb_store'].items():
        if t != 7: continue
        p = ids.base[7].get(x); pc = st['pc_store'].get((7, p)) if p is not None else None
        if pc is None or len(pc['data']) != len(xb['data']): continue
        recs = records(xb['data'], xb['reloc'])
        if not recs: continue
        n += 1; nrec += len(recs)
        _, log = fix_section(xb['data'], xb['reloc'], pc['data'])
        for r, k, old, new in log:
            bad[k] += 1
            if len(ex) < 10: ex.append((x, hex(r), hex(k), old, new))
    print('base DTPs with type-4 records', n, 'records', nrec, 'words the fix would change on PC bytes', sum(bad.values()),
          {hex(k): v for k, v in sorted(bad.items())}, ex)

def xsecs_of(name):
    from convert_dlc import raw_dlc
    raw, _ = raw_dlc(name.replace('/', '\\'))
    if raw is None: raw, _ = raw_dlc(os.path.basename(name))
    if raw is None: return None
    return sections_with_data(cdrm_decode(raw, 'be'), 'be')[1]

def load_overlay(dirs, names=None):
    files = {}
    for d in dirs:
        for r, _, fs in os.walk(d):
            for f in fs:
                if f.lower().endswith('.drm'):
                    files[os.path.relpath(os.path.join(r, f), d).replace('\\', '/')] = os.path.join(r, f)
    if names: files = {k: v for k, v in files.items() if k in names or os.path.basename(k) in names}
    return files

def process(rel, path):
    """-> (new raw or None, [(sec id, rec, k, old, new)], nrec)"""
    xs = xsecs_of(rel)
    if xs is None: return None, [], 0
    raw = open(path, 'rb').read()
    D = DW.read(raw, 'le')
    import dtpid_sweep as DS                                   # Xbox<->PC section pairing by remapped DTP id
    _, ids = DS.ctx(); ids.local = {}
    logs = []; nrec = 0
    for s, i in DS.pairs(xs, D, ids):
        sec = D.sections[i]
        if len(sec.data) != len(s['data']): continue
        nrec += len(records(s['data'], s['reloc']))
        new, log = fix_section(s['data'], s['reloc'], sec.data)
        if log:
            sec.data = new; logs += [(sec.id,) + l for l in log]
    if not logs: return None, [], nrec
    out = D.write('le')
    if raw[:4] == b'CDRM': out = DW.cdrm_encode(out, 'le')
    return out, logs, nrec

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'calibrate': calibrate()
    elif cmd == 'scan':
        tot = collections.Counter()
        for rel, path in sorted(load_overlay(sys.argv[2].split(','), set(sys.argv[3:]) or None).items()):
            _, logs, nrec = process(rel, path)
            tot['records'] += nrec
            if logs:
                tot['files'] += 1; tot['words'] += len(logs)
                g40 = [l for l in logs if l[2] == 0x40]
                print(rel, '<-', path, 'words', len(logs), 'group(+0x40)', len(g40),
                      sorted(collections.Counter(l[0] for l in logs).items()), logs[:6])
        print('TOTAL', dict(tot))
    elif cmd == 'patch':
        import hashlib
        out_dir, dirs, names = sys.argv[2], sys.argv[3].split(','), sys.argv[4:]
        files = load_overlay(dirs)
        for name in names:
            path = files.get(name)
            if path is None: print(name, 'not found'); continue
            new, logs, nrec = process(name, path)
            if new is None: print(name, 'unchanged'); continue
            # idempotence + self-check: re-run on the output must change nothing
            dst = os.path.join(out_dir, name); os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, 'wb').write(new)
            _, again, _ = process(name, dst)
            print(name, '<-', path, 'words', len(logs), 'recheck', len(again), hashlib.md5(new).hexdigest())
            for l in logs: print('   DTP %d rec %#x +%#x %s -> %s' % l)
