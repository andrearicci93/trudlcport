"""dtp_descfix.py - uberobject graph-descriptor (DESC, 0x54 B) words left wrong by the learned type-7 table; NARROW hook over dtp_schema.

Corrections (both proven in game / by engine code, work/ws/rigid + NOTES 'RISULTATO CATENA'):
  * DESC+0x18 word, byte 0 = model_idx (PC 0x4d4ded movzx eax,byte [edx+0x18]): dragon_slider DTP 20457 +0x10a0  Xbox 02000000, table gave
    00020000 (b2s16-like) -> model 0 = empty -> 'UberObject: failed to create rigid body'.
  * DESC+0x50 word, byte +2 = flag_dmg (PC 0x6d4699 test byte [ecx+0x52],1; Xbox 0x823c745c): raft_bridge DTP 20765 +0x414 Xbox ffff0100, table gave
    ffff0001 -> the Shot node never fired, chain unbreakable.
The conversion itself is dtp_schema.convert(tags='D', min_cert='media'); this module keeps ONLY the log entries whose word is in ALLOWED_WORDS
(fixed list below).  NOT written (by design): TRANS fields (+0x10 01000000 read s32, no reader found), every other DESC/NODE word, and the
tag-C fields (spheres/boxes/capsules, not proven).  Idempotent (writes only when the PC bytes differ).
UNCERTAINTY: DESC discovery is heuristic (find_D: ptr+0x8 -> 28-B nodes whose +8 is char*, n<=64); model_idx / flag bytes are 'media'/'alta'
(see dtp_schema EXPLICIT); the bytes next to them in the same word (desc+0x19..0x1b, +0x50/51/53) are RULE-DETERMINED (word rule n>=20, >=8 DTP, 0 exceptions).
Usage (python -I): tools/venv/bin/python -I tools/dtp_descfix.py selftest | scan [DIR]
Hook: fix_section(xd, xreloc, pd, preloc=None) -> (bytes, [(off, old_hex, new_hex)])   (dlc_generic.convert_drm, extra_fixes, type 7 convert/template)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')
ALLOWED_STRUCT = 'DESC'
ALLOWED_WORDS = (0x18, 0x50)                 # DESC-relative word offsets (model_idx word; flag word +0x50..0x53 holding flag_dmg at +0x52)

def fix_section(xd, xreloc, pd, preloc=None):
    import dtp_schema as S
    if len(pd) != len(xd): return bytes(pd), []
    nb, lg = S.convert(xd, xreloc, pd, preloc, 'D', 'media')
    out = bytearray(pd); log = []
    for e in lg:
        if e.get('status') != 'CHANGED' or e.get('struct') != ALLOWED_STRUCT: continue
        rel = e['off'] - e['base']
        if rel - rel % 4 not in ALLOWED_WORDS: continue
        o, n = e['off'], bytes.fromhex(e['new'])
        if bytes(out[o:o + len(n)]) != n: log.append((o, bytes(out[o:o + len(n)]).hex(), n.hex())); out[o:o + len(n)] = n
    return bytes(out), log

def selftest():
    import dtp_audit as A, dtp_schema as S
    n = ch = nd = nsame = 0
    for x, p, xb, pc, xr in A.base_pairs():
        pr = R.parse(pc['reloc'], 'le')
        nb, lg = fix_section(xb['data'], xr, pc['data'], pr); n += 1; ch += len(lg)
        # coverage: DESC instances found and allowed words examined (SAME = schema agrees with the real PC bytes)
        _, full = S.convert(xb['data'], xr, pc['data'], pr, 'D', 'media')
        nd += sum(1 for e in full if e.get('struct') == 'DESC' and e['off'] - e['base'] == 0x18)
        nsame += sum(1 for e in full if e.get('struct') == 'DESC' and e['off'] - e['base'] in (0x18, 0x52) and e['status'] == 'SAME')
    print('base pairs', n, 'DESC instances', nd, 'allowed-field entries SAME', nsame, 'bytes changed', ch)
    return ch

def scan(d):
    import glob, drm_write as DW, dtp_audit as A
    tot = 0
    for p in sorted(glob.glob(d + '/**/*.drm', recursive=True)):
        rel = os.path.relpath(p, d).replace('\\', '/'); xs = A.xsecs(rel)
        if xs is None: continue
        D = DW.read(open(p, 'rb').read(), 'le')
        for x, i in A.section_pairs(xs, D):
            if x['type'] != 7 or len(D.sections[i].data) != len(x['data']): continue
            _, lg = fix_section(x['data'], x['reloc'], D.sections[i].data, D.sections[i].reloc)
            for o, a, b in lg: print(rel, D.sections[i].id, hex(o), a, '->', b); tot += 1
    print('bytes', tot)

if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'selftest': selftest()
    elif a[0] == 'scan': scan(a[1] if len(a) > 1 else os.path.join(W, 'baseline', 'B2', 'mods'))
