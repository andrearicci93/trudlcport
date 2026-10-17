"""Typed DTP fixes that take the PC ANALOG record as reference (2026-10-10, mods_next):

1. dtplist  - id lists {u32 8, ptr -> +0x10, u32 n @0x10, n x {u32 DTP id, s32 key} @0x14} (Lara/costume/thrall anim-set
              DTPs 1152/1153/2492/2499/2505/.. ): every id := ids(7, id) (0 / -1 kept), key s32.  Base pairs: 16 lists,
              31/31 mapped ids remapped on PC, 36/36 keys s32 (the 1 other id has no base map: 2676 -> PC 2479).
              The DLC copies (dlc_costume_*, knight_thrall) are LONGER than the base twins (n 15 vs 3) -> learned table
              left every id raw (incl. ids of DTPs resident in other DRMs, which the same-DRM sweep cannot see).
2. align    - DLC-new DTP that is a base DTP + inserted/changed parts: segments [(dlc_lo, dlc_hi, delta)] map DLC offsets to
              the base Xbox DTP; every word whose Xbox bytes EQUAL the base Xbox word at the aligned offset (and is not a
              pointer/id-ref slot) gets the base PC bytes (same source + same layout -> same PC bytes); 'extra' gives typed
              classes for the few changed / inserted words (evidence below).
   SPECS:
   * dlc1_uo_sewer_gate 21105 = Xbox 17384 (PC 13046) + 0x60-byte block inserted at 0x7c0 (0x7b4 -> new struct 0x7c0,
     whose +0x54 ptr -> the {id 4672 ..} block that 17384 has at 0x7c0) + 3 changed words (0x4a0, 0x7b0, 0x910).
     extra: 0x2d after f32 -3.16 (c04a468e) = s32 (base window evidence 50/50, and 0x200 in the same DTP);
            the next word = {u8, u8, u16} (base: 207/207 after c04a468e,0000002d) -> 0x804 bytes 04 00 00 00.
   * goo fx particle DTPs (dlc_fx_goo_*): Xbox words 0x10.. identical to base 12197/18494/18459 (fx_goo_hel_pool_ist):
     PC re-authored the block 0x154..0x16c (one field inserted, 5 words shifted by 4: u16 pairs + DTP id 8638 -> 14242
     at 0x16c); the converter kept the Xbox layout (0x21be0000 u16 pair at 0x168, 0 at 0x16c).  Fix = base PC bytes over
     the equal run (auto-detected, GOO_BASES).
API: dtplist_fix(xd, rel, out, ids) -> words ; align_fix(xd, rel, out, spec, store, ids) -> words ; goo_fix(...)
"""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R

def _put(out, o, v):
    if bytes(out[o:o + 4]) != v: out[o:o + 4] = v; return 1
    return 0

def is_dtplist(xd, rel):
    if len(xd) < 0x14 or struct.unpack_from('>I', xd, 0)[0] != 8: return False
    if (4, 0x10) not in rel.internal: return False
    n = struct.unpack_from('>I', xd, 0x10)[0]
    return len(xd) == 0x14 + 8 * n and not rel.idref and not rel.idref_a

DTPLIST_STATS = collections.Counter()
def dtplist_fix(xd, rel, out, ids):
    if not is_dtplist(xd, rel) or len(out) != len(xd): return 0
    n = struct.unpack_from('>I', xd, 0x10)[0]; ch = 0
    ch += _put(out, 0x10, xd[0x10:0x14][::-1])
    for k in range(n):
        o = 0x14 + 8 * k
        v = struct.unpack_from('>I', xd, o)[0]
        if v not in (0, 0xffffffff):
            m = ids(7, v)
            if v not in ids.base.get(7, {}) and v not in ids.new.get(7, {}):
                DTPLIST_STATS['unmapped_id_left'] += 1          # no map (base 2543: 2676 -> PC 2479): leave the word
            else:
                ch += _put(out, o, struct.pack('<I', m))
        else:
            ch += _put(out, o, xd[o:o + 4][::-1])
        ch += _put(out, o + 4, xd[o + 4:o + 8][::-1])
    DTPLIST_STATS['lists'] += 1; DTPLIST_STATS['words'] += ch
    return ch

def _cls(w, c):
    if c == 's32': return w[::-1]
    if c == 'u16': return w[1::-1] + w[:1:-1]
    if c == 'raw': return bytes(w)
    if c == 'u8u8u16': return w[0:2] + w[3:4] + w[2:3]
    raise ValueError(c)

SPECS = {
    ('dlc1_uo_sewer_gate.drm', 21105): dict(base=17384, pc=13046, segs=[(0, 0x7c0, 0), (0x820, 0x9a4, -0x60)],
                                            extra={0x4a0: 's32', 0x910: 's32', 0x800: 's32', 0x804: 'u8u8u16'}),
}

def align_fix(xd, rel, out, spec, store, ids=None):
    """returns (#words changed, #aligned equal words, #extra)"""
    bx = store['xb_store'][7, spec['base']]['data']; bp = store['pc_store'][7, spec['pc']]['data']
    if len(bx) != len(bp) or len(out) != len(xd): return 0, 0, 0
    skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
    ch = eq = 0
    for lo, hi, d in spec['segs']:
        for o in range(lo, min(hi, len(xd)) - 3, 4):
            a = o + d
            if o in skip or a < 0 or a + 4 > len(bx): continue
            if xd[o:o + 4] != bx[a:a + 4]: continue
            eq += 1; ch += _put(out, o, bp[a:a + 4])
    for o, c in spec.get('extra', {}).items():
        if o not in skip: ch += _put(out, o, _cls(xd[o:o + 4], c))
    return ch, eq, len(spec.get('extra', {}))

GOO_BASES = (12197, 18494, 18459)
GOO_BLOCK = (0x154, 0x170)          # PC re-authored block (base mismatch offsets 0x154..0x16c)
def goo_fix(xd, rel, out, store, ids=None):
    """particle DTPs whose Xbox words around the goo block equal a GOO_BASES base at the SAME offsets (no reloc in the
    block): block := base PC bytes.  Also handles the block shifted by +0x20 (dlc_fx_goo_upcolumn_pit 0x188) by searching
    the base Xbox block bytes in the DLC data.  Returns words changed."""
    for b in GOO_BASES:
        bx = store['xb_store'][7, b]['data']; bp = store['pc_store'][7, ids.base[7][b]]['data']
        blk = bx[0x100:GOO_BLOCK[1]]                 # 0x100..0x170: header of the emitter sub-record + the block
        i = xd.find(blk)
        if i < 0 or i % 4: continue
        d = i - 0x100
        skip = set(rel.pointer_offsets()) | set(rel.id_offsets())
        if any(o + d in skip for o in range(GOO_BLOCK[0], GOO_BLOCK[1], 4)): return 0
        ch = 0
        for o in range(GOO_BLOCK[0], GOO_BLOCK[1], 4):
            ch += _put(out, o + d, bp[o:o + 4])
        return ch
    return 0

def validate(store, ids):
    """sanity on base pairs: dtplist_fix / align on the REAL PC bytes from the Xbox base source must change 0 words"""
    import dtpid_sweep as S
    st = collections.Counter()
    for x, bx, bp in S.base_pairs(store, ids):
        rel = R.parse(store['xb_store'][7, x]['reloc'], 'be')
        if is_dtplist(bx, rel):
            b = bytearray(bp); st['dtplist_lists'] += 1; st['dtplist_changed_words'] += dtplist_fix(bx, rel, b, ids)
        if x in GOO_BASES:
            b = bytearray(bp); st['goo_bases'] += 1; st['goo_changed_words'] += goo_fix(bx, rel, b, store, ids)
    for (nm, sec), sp in SPECS.items():
        bx = store['xb_store'][7, sp['base']]['data']; bp = store['pc_store'][7, sp['pc']]['data']
        b = bytearray(bp)
        n, eq, _ = align_fix(bx, R.parse(store['xb_store'][7, sp['base']]['reloc'], 'be'), b,
                             dict(sp, segs=[(0, len(bx), 0)], extra={}), store, ids)
        st['align_base_selftest_changed'] += n
    return st

if __name__ == '__main__':
    import dtpid_sweep as S
    store, ids = S.ctx()
    print('validate (PC bytes must stay unchanged):', dict(validate(store, ids)), dict(DTPLIST_STATS))
