"""dtp_schema.py - EXPLICIT-TYPE schema (read Xbox BE -> write PC LE) for the DTP (type 7) structures involved in the two open DLC1 blocks.

Why: the generic Xbox->PC DTP conversion applies byte-permutation classes learned statistically per (region, offset); it produced
recurring families of errors (strings as ints, u16 pairs as u32, counts/flags, non-id words as ids).  Here every field of four
structures has an explicit type and a SOURCE (engine reader on PC and/or Xbox, or a base-pair rule with n and #DTP) and a CERTAINTY:
  alta  = engine reader on BOTH platforms agrees with the declared type
  media = one platform reader only, or a base-pair rule with >= 20 informative samples over >= 8 distinct DTPs and 0 exceptions
  bassa = rule below those thresholds / no reader: DECLARED but NEVER written by convert (words stay as in the PC bytes, marked UNKNOWN)
UNKNOWN_RAW = bytes with no evidence (always palindromic/zero in base): left untouched.

Structures (tag):
  A  DLIST  draw-call list of a mesh DTP (engine: PC 0x5c0140 == Xbox 0x82286908; called by PC 0x5c01d0 == Xbox 0x82286a00)
            data: {u32 count @0} then count records of 16 B at 4+16k: {id(12) @0, u32 flags @4, u32 one @8, u32 matIdx @0xc}.
            The engine indexes from list+8 (entry view {flags,one,matIdx,idref}); the DATA offsets are the above (matIdx of record 0 = +0x10).
            Context field used by the same reader (NOT in DTP list data): mesh ctx +0xc = ptr to material table, stride 0x50, [+0x30] = ptr
            to material, byte [ptr] & 0x10 (PC 0x5c0194/0x5c019f, Xbox 0x8228698c/0x822869b4).  Container of the table: UNKNOWN (type-12 resource).
  B  TP     model target points (model header +0x5c n, +0x60 ptr), 32 B: {u16 seg, u16 TYPE, f32 pos[3], f32 rot[3], u32 ID}
  C  HS/HB/HC  HInfo spheres 36 B / boxes 68 B / capsules 56 B (model segment +0x3c: {u32 n, ptr} x5)   [rules from base only: media/bassa]
  D  DESC/NODE/TRANS  uberobject state-graph descriptor (0x54 B), node (28 B), transition (via ptr array at node+0x10)

API
  read_xbox(data, reloc)               -> [Inst]  typed values {field name: int|float|bytes}, instance span, struct, tag
  write_pc(inst, fill=None)            -> bytes   PC layout of the instance span (declared writable fields written; other bytes from fill or 0)
  convert(xbox_bytes, xbox_reloc, pc_bytes, pc_reloc=None, tags='ABCD', min_cert='media', ids=None)
                                       -> (new_pc_bytes, log)  ONLY schema fields (cert >= min_cert) are rewritten; log lists every word
                                          touched (field, type, source, cert, old, new) plus UNKNOWN words (unchanged, status 'UNKNOWN')
CLI (python -I):  selftest | evidence | scan [--set DIR,..] | controls | fix OUT [--set DIR] | table
"""
import sys, os, struct, collections, pickle, hashlib, json, zlib
TOOLS = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, TOOLS)
W = os.path.normpath(os.path.join(TOOLS, '..', 'work'))
import drm_reloc as R

PERMS = {'s32': (3, 2, 1, 0), 's16': (1, 0, 3, 2), 'raw': (0, 1, 2, 3), 'b2s16': (0, 1, 3, 2), 's16b2': (1, 0, 2, 3)}
MAGIC = bytes.fromhex('04c20453')           # model DTP word 0 (Xbox)
MIN_N, MIN_DTP = 20, 8
SIZES = {'u8': 1, 'u16': 2, 's16': 2, 'u32': 4, 's32': 4, 'f32': 4, 'id': 4, 'ptr': 4}
CERT_RANK = {'bassa': 0, 'media': 1, 'alta': 2}


# ------------------------------------------------------------------------------------------------------------ schema tables
class Field(collections.namedtuple('Field', 'name off size type cert src n dtp')):
    __slots__ = ()

STRUCT_SIZE = {'A_HDR': 4, 'A_REC': 16, 'TP': 32, 'HS': 36, 'HB': 68, 'HC': 56, 'DESC': 0x54, 'NODE': 28, 'TRANS': 0x28}
STRUCT_TAG = {'A_HDR': 'A', 'A_REC': 'A', 'TP': 'B', 'HS': 'C', 'HB': 'C', 'HC': 'C', 'DESC': 'D', 'NODE': 'D', 'TRANS': 'D'}

PC_A = 'PC 0x5c0140'; XB_A = 'XBOX 0x82286908'
# explicit rows: (struct, off) -> (name, size, type, cert, source).  Overrides derived/base rows that overlap.
EXPLICIT = {
    ('A_HDR', 0): ('count', 4, 'u32', 'alta', PC_A + ' cmp dword [eax],esi (loop bound) / ' + XB_A + ' lwz r6,0(r4)'),
    ('A_REC', 0): ('idref', 4, 'id(12)', 'media', 'reloc table: idref type 12 at 4+16k on both platforms (identical layout in all 84 base lists); not read by the draw loop; verify-only'),
    ('A_REC', 4): ('flags', 4, 'u32', 'alta', PC_A + ' or dword [edx],1 (RMW u32) / ' + XB_A + ' lwz/ori 1/stw 0(r10).  NB base values are all 0 -> no informative base sample'),
    ('A_REC', 8): ('one', 4, 'u32', 'media', 'no reader in the draw loop; base rule 00000001 -> 01000000 only s32 (see evidence)'),
    ('A_REC', 12): ('matIdx', 4, 'u32', 'alta', PC_A + ' mov ecx,[edx+8]; lea ecx,[ecx*5]; shl 4 (*0x50 into [ctx+0xc] table) / ' + XB_A + ' lwz r11,8(r10); slwi 2/slwi 4.  PLAIN INDEX, NEVER an id (crash 0x5c019f: 8 -> 213)'),
    ('TP', 0): ('seg', 2, 'u16', 'media', 'PC 0x4d4e2b movzx edx,word [eax] (query 0x162: shl 6 = segment index); Xbox reader not located'),
    ('TP', 2): ('TYPE', 2, 'u16', 'alta', 'PC 0x71690d movzx eax,word [edi+2] / XBOX 0x82403954 lhz 2(r28)  (TYPE&1->0x71, &4->2, &8->4, &0x40->8)'),
    ('TP', 4): ('pos_x', 4, 'f32', 'media', 'PC 0x4d4e5f movss [eax+4]; Xbox reader not located'),
    ('TP', 8): ('pos_y', 4, 'f32', 'media', 'PC 0x4d4e4d movss [eax+8]; Xbox reader not located'),
    ('TP', 12): ('pos_z', 4, 'f32', 'media', 'PC 0x4d4e42 movss [eax+0xc]; Xbox reader not located'),
    ('TP', 0x10): ('rot_x', 4, 'f32', 'media', 'base rule (see evidence); no reader located'),
    ('TP', 0x14): ('rot_y', 4, 'f32', 'bassa', 'base rule n=3 only (same f32 vector as rot_x/rot_z, never written)'),
    ('TP', 0x18): ('rot_z', 4, 'f32', 'media', 'base rule (see evidence); no reader located'),
    ('TP', 0x1c): ('ID', 4, 'key32', 'alta', 'PC 0x716931 mov eax,[edi+0x1c] / XBOX 0x824039a4 lwz 0x1c(r28).  VALUE = per-platform enum (32 of 79 base pairs remapped) used only as an equality key inside the model (0x4d4e13): VERIFY-ONLY (never written): the installed word is kept; KEY_OK when it equals the s32 swap of the Xbox value'),
    ('DESC', 4): ('n_nodes', 4, 'u32', 'media', 'base rule; node loop reader not in 0x6d4690'),
    ('DESC', 8): ('nodes', 4, 'ptr', 'alta', 'PC 0x6d4713 mov eax,[ecx+8] / XBOX 0x823c74c0 lwz r11,8(r11)  (28-byte nodes)'),
    ('DESC', 0x10): ('trans', 4, 'ptr', 'media', 'reloc slot (internal pointer), reader not in 0x6d4690'),
    ('DESC', 0x18): ('model_idx', 1, 'u8', 'media', 'PC 0x4d4ded movzx eax,byte [edx+0x18] (edx=[sec+0x78]); Xbox reader not located; base rule raw bytes'),
    ('DESC', 0x52): ('flag_dmg', 1, 'u8', 'alta', 'PC 0x6d4699 test byte [ecx+0x52],1 / XBOX 0x823c745c lbz r10,0x52(r11); clrlwi 31.  Base: bytes 2,3 of word +0x50 never s16-swapped (ffff0100, n=32)'),
    ('NODE', 8): ('name', 4, 'ptr', 'media', 'reloc slot (char* name)'),
    ('NODE', 12): ('n_trans', 4, 'u32', 'alta', 'PC 0x6d471d cmp dword [ebp+0xc],edi / XBOX 0x823c74cc lwz r9,0xc(r30)'),
    ('NODE', 0x10): ('trans', 4, 'ptr', 'alta', 'PC 0x6d4723 mov ecx,[ebp+0x10] / XBOX 0x823c74dc lwz r11,0x10(r30) (array of ptr to transition)'),
    ('NODE', 0x18): ('act', 4, 'ptr', 'media', 'reloc slot (action list)'),
    ('TRANS', 0x18): ('cond', 4, 'u32', 'alta', 'PC 0x6d4729 cmp dword [esi+0x18],0x11 / XBOX 0x823c74e4 lwz r10,0x18(r31)'),
    ('TRANS', 0x1c): ('arg', 4, 'u32', 'alta', 'PC 0x6d4733 fld dword [esi+0x1c] (cond 0x11 f32) and 0x6d4759 cmp eax,[esi+0x1c] (cond 0x13 u32) / XBOX 0x823c74f0 lfs f0,0x1c(r31), 0x823c7520 lwz r10,0x1c(r31): 4-byte value, s32 swap'),
}
FNAME = {('HS', 0): 'flags', ('HS', 2): 'id', ('HS', 3): 'rank', ('HS', 6): 'radius', ('HS', 16): 'r2', ('HS', 20): 'mass',
         ('HB', 48): 'flags', ('HB', 50): 'id', ('HB', 51): 'rank', ('HC', 32): 'flags', ('HC', 34): 'id', ('HC', 35): 'rank'}
# --- generated by work/ws/schema/gen_rows.py (derived from the 1054 base pairs; (off, size, type, n_informative, n_dtp, n_exceptions)) ---
DERIVED = {
    'HS': [
        (0, 2, 'u16', 351, 150, 0), (2, 1, 'u8', 351, 150, 0), (3, 1, 'u8', 351, 150, 0), (4, 1, 'u8', 351, 150, 0),
        (5, 1, 'u8', 351, 150, 0), (6, 2, 'u16', 351, 150, 0), (8, 2, 'u16', 110, 56, 0), (10, 2, 'u16', 222, 71, 0),
        (12, 2, 'u16', 293, 123, 0), (14, 2, 'UNKNOWN_RAW', 0, 0, 0), (16, 4, 'u32', 351, 150, 0),
        (20, 2, 'u16', 351, 150, 0), (22, 1, 'u8', 351, 150, 0), (23, 1, 'u8', 351, 150, 0),
        (24, 1, 'u8', 323, 132, 0), (25, 1, 'u8', 323, 132, 0), (26, 1, 'u8', 323, 132, 0),
        (27, 1, 'u8', 323, 132, 0), (28, 2, 'u16', 18, 6, 0), (30, 1, 'u8', 19, 7, 0), (31, 1, 'u8', 19, 7, 0),
        (32, 1, 'u8', 2, 2, 0), (33, 1, 'u8', 2, 2, 0), (34, 2, 'UNKNOWN_RAW', 0, 0, 0),
    ],
    'HB': [
        (0, 4, 'u32', 409, 323, 0), (4, 4, 'u32', 409, 323, 0), (8, 4, 'u32', 409, 323, 0),
        (12, 4, 'UNKNOWN_RAW', 0, 0, 0), (16, 4, 'u32', 330, 262, 0), (20, 4, 'u32', 325, 257, 0),
        (24, 4, 'u32', 379, 297, 0), (28, 4, 'UNKNOWN_RAW', 0, 0, 0), (32, 4, 'u32', 44, 36, 0),
        (36, 4, 'u32', 58, 47, 0), (40, 4, 'u32', 65, 46, 0), (44, 4, 'u32', 409, 323, 0),
        (48, 2, 'u16', 407, 321, 0), (50, 1, 'u8', 409, 323, 0), (51, 1, 'u8', 409, 323, 0),
        (52, 1, 'u8', 409, 323, 0), (53, 1, 'u8', 409, 323, 0), (54, 2, 'u16', 409, 323, 0),
        (56, 1, 'u8', 119, 117, 0), (57, 1, 'u8', 119, 117, 0), (58, 1, 'u8', 119, 117, 0),
        (59, 1, 'u8', 119, 117, 0), (60, 1, 'u8', 236, 189, 0), (61, 1, 'u8', 236, 189, 0),
        (62, 2, 'u16', 21, 17, 0), (64, 1, 'u8', 20, 20, 0), (65, 1, 'u8', 20, 20, 0), (66, 1, 'u8', 20, 20, 0),
        (67, 1, 'u8', 20, 20, 0),
    ],
    'HC': [
        (0, 4, 'u32', 86, 70, 0), (4, 4, 'u32', 86, 70, 0), (8, 4, 'u32', 86, 70, 0),
        (12, 4, 'UNKNOWN_RAW', 0, 0, 0), (16, 4, 'u32', 13, 13, 0), (20, 4, 'u32', 40, 29, 0),
        (24, 4, 'u32', 8, 8, 0), (28, 4, 'u32', 86, 70, 0), (32, 2, 'u16', 86, 70, 0), (34, 1, 'u8', 86, 70, 0),
        (35, 1, 'u8', 86, 70, 0), (36, 1, 'u8', 86, 70, 0), (37, 1, 'u8', 86, 70, 0), (38, 2, 'u16', 86, 70, 0),
        (40, 2, 'u16', 86, 70, 0), (42, 2, 'u16', 86, 70, 0), (44, 1, 'u8', 31, 31, 0), (45, 1, 'u8', 31, 31, 0),
        (46, 1, 'u8', 31, 31, 0), (47, 1, 'u8', 31, 31, 0), (48, 1, 'u8', 52, 46, 0), (49, 1, 'u8', 52, 46, 0),
        (50, 2, 'u16', 5, 2, 0), (52, 1, 'u8', 15, 15, 0), (53, 1, 'u8', 15, 15, 0), (54, 2, 'UNKNOWN_RAW', 0, 0, 0),
    ],
    'TP': [
        (0, 2, 'u16', 22, 22, 0), (2, 2, 'u16', 57, 57, 0), (4, 4, 'u32', 49, 49, 0), (8, 4, 'u32', 65, 65, 0),
        (12, 4, 'u32', 77, 77, 0), (16, 4, 'u32', 78, 78, 0), (20, 4, 'u32', 3, 3, 0), (24, 4, 'u32', 79, 79, 0),
        (28, 4, 'u32', 47, 47, 32),
    ],
    'DESC': [
        (0, 4, 'UNKNOWN_RAW', 0, 0, 0), (4, 4, 'u32', 347, 204, 0), (12, 4, 'u32', 262, 176, 0),
        (20, 4, 'u32', 33, 22, 0), (24, 1, 'u8', 144, 59, 0), (25, 1, 'u8', 144, 59, 0),
        (26, 2, 'UNKNOWN_RAW', 0, 0, 0), (28, 4, 'UNKNOWN_RAW', 0, 0, 0), (32, 4, 'u32', 347, 204, 0),
        (36, 4, 'u32', 347, 204, 0), (40, 4, 'u32', 347, 204, 0), (44, 1, 'u8', 234, 126, 0),
        (45, 1, 'u8', 234, 126, 0), (46, 2, 'UNKNOWN_RAW', 0, 0, 0), (52, 4, 'u32', 48, 47, 0),
        (60, 4, 'u32', 32, 30, 0), (64, 4, 'UNKNOWN_RAW', 0, 0, 0), (68, 4, 'UNKNOWN_RAW', 0, 0, 0),
        (72, 2, 'u16', 9, 6, 0), (74, 2, 'UNKNOWN_RAW', 0, 0, 0), (76, 4, 'UNKNOWN_RAW', 0, 0, 0),
        (80, 2, 'UNKNOWN_RAW', 0, 0, 0), (82, 1, 'u8', 347, 204, 0), (83, 1, 'u8', 347, 204, 0),
    ],
    'NODE': [
        (0, 4, 'u32', 1131, 202, 0), (4, 4, 'u32', 1142, 203, 0), (12, 4, 'u32', 824, 176, 0),
        (20, 4, 'u32', 869, 195, 0),
    ],
    'TRANS': [
        (0, 4, 'u32', 788, 124, 0), (4, 4, 'u32', 1056, 175, 0), (8, 4, 'u32', 1115, 176, 0),
        (12, 4, 'UNKNOWN_RAW', 0, 0, 0), (16, 1, 'u8', 1141, 176, 0), (17, 1, 'u8', 1141, 176, 0),
        (18, 2, 'UNKNOWN_RAW', 0, 0, 0), (20, 4, 'UNKNOWN_RAW', 0, 0, 0), (24, 4, 'u32', 1141, 176, 0),
        (28, 4, 'u32', 304, 105, 0), (32, 4, 'UNKNOWN_RAW', 0, 0, 0), (36, 4, 'UNKNOWN_RAW', 0, 0, 0),
    ],
}

# u32 words that are plainly floats (4-byte swap either way; label only)
FLOATS = ({('DESC', o) for o in (0x20, 0x24, 0x28, 0x3c)} | {('NODE', 0), ('NODE', 4), ('TRANS', 8)} |
          {('HB', o) for o in range(0, 0x30, 4)} | {('HC', o) for o in range(0, 0x20, 4)})

# word rules (struct, word offset) -> (surviving perms = AND of the classes of all informative base samples, n, n_dtp, n_exceptions)
RULES = {
    ('DESC', 0x4): (('s32',), 347, 204, 0),
    ('DESC', 0xc): (('s32',), 262, 176, 0),
    ('DESC', 0x14): (('s32',), 33, 22, 0),
    ('DESC', 0x18): (('b2s16', 'raw'), 144, 59, 0),
    ('DESC', 0x20): (('s32',), 347, 204, 0),
    ('DESC', 0x24): (('s32',), 347, 204, 0),
    ('DESC', 0x28): (('s32',), 347, 204, 0),
    ('DESC', 0x2c): (('b2s16', 'raw'), 234, 126, 0),
    ('DESC', 0x34): (('s32',), 48, 47, 0),
    ('DESC', 0x3c): (('s32',), 32, 30, 0),
    ('DESC', 0x48): (('s16', 's16b2'), 347, 204, 0),
    ('DESC', 0x50): (('raw', 's16b2'), 347, 204, 0),
    ('HB', 0x0): (('s32',), 409, 323, 0),
    ('HB', 0x4): (('s32',), 409, 323, 0),
    ('HB', 0x8): (('s32',), 409, 323, 0),
    ('HB', 0x10): (('s32',), 330, 262, 0),
    ('HB', 0x14): (('s32',), 325, 257, 0),
    ('HB', 0x18): (('s32',), 379, 297, 0),
    ('HB', 0x20): (('s32',), 44, 36, 0),
    ('HB', 0x24): (('s32',), 58, 47, 0),
    ('HB', 0x28): (('s32',), 65, 46, 0),
    ('HB', 0x2c): (('s32',), 409, 323, 0),
    ('HB', 0x30): (('s16b2',), 409, 323, 0),
    ('HB', 0x34): (('b2s16',), 409, 323, 0),
    ('HB', 0x38): (('raw',), 119, 117, 0),
    ('HB', 0x3c): (('b2s16',), 236, 189, 0),
    ('HB', 0x40): (('raw',), 20, 20, 0),
    ('HC', 0x0): (('s32',), 86, 70, 0),
    ('HC', 0x4): (('s32',), 86, 70, 0),
    ('HC', 0x8): (('s32',), 86, 70, 0),
    ('HC', 0x10): (('s32',), 13, 13, 0),
    ('HC', 0x14): (('s32',), 40, 29, 0),
    ('HC', 0x18): (('s32',), 8, 8, 0),
    ('HC', 0x1c): (('s32',), 86, 70, 0),
    ('HC', 0x20): (('s16b2',), 86, 70, 0),
    ('HC', 0x24): (('b2s16',), 86, 70, 0),
    ('HC', 0x28): (('s16',), 86, 70, 0),
    ('HC', 0x2c): (('raw',), 31, 31, 0),
    ('HC', 0x30): (('b2s16',), 52, 46, 0),
    ('HC', 0x34): (('b2s16', 'raw'), 15, 15, 0),
    ('HS', 0x0): (('s16b2',), 351, 150, 0),
    ('HS', 0x4): (('b2s16',), 351, 150, 0),
    ('HS', 0x8): (('s16',), 230, 78, 0),
    ('HS', 0xc): (('s16', 's16b2'), 293, 123, 0),
    ('HS', 0x10): (('s32',), 351, 150, 0),
    ('HS', 0x14): (('s16b2',), 351, 150, 0),
    ('HS', 0x18): (('raw',), 323, 132, 0),
    ('HS', 0x1c): (('s16b2',), 19, 7, 0),
    ('HS', 0x20): (('b2s16', 'raw'), 2, 2, 0),
    ('NODE', 0x0): (('s32',), 1131, 202, 0),
    ('NODE', 0x4): (('s32',), 1142, 203, 0),
    ('NODE', 0xc): (('s32',), 824, 176, 0),
    ('NODE', 0x14): (('s32',), 869, 195, 0),
    ('TP', 0x0): (('s16',), 58, 58, 0),
    ('TP', 0x4): (('s32',), 49, 49, 0),
    ('TP', 0x8): (('s32',), 65, 65, 0),
    ('TP', 0xc): (('s32',), 77, 77, 0),
    ('TP', 0x10): (('s32',), 78, 78, 0),
    ('TP', 0x14): (('s32',), 3, 3, 0),
    ('TP', 0x18): (('s32',), 79, 79, 0),
    ('TP', 0x1c): (('s32',), 47, 47, 32),
    ('TRANS', 0x0): (('s32',), 788, 124, 0),
    ('TRANS', 0x4): (('s32',), 1056, 175, 0),
    ('TRANS', 0x8): (('s32',), 1115, 176, 0),
    ('TRANS', 0x10): (('b2s16', 'raw'), 1141, 176, 0),
    ('TRANS', 0x18): (('s32',), 1141, 176, 0),
    ('TRANS', 0x1c): (('s32',), 304, 105, 0),
}

def _build():
    out = {}
    for st, size in STRUCT_SIZE.items():
        cov = {}                                   # byte offset -> Field
        for (s2, off), (nm, sz, ty, cert, src) in EXPLICIT.items():
            if s2 == st:
                f = Field(nm, off, sz, ty, cert, src, 0, 0)
                for b in range(off, off + sz): cov[b] = f
        for (off, sz, ty, n, d, exc) in DERIVED.get(st, ()):
            if any(b in cov for b in range(off, off + sz)): continue
            if ty == 'UNKNOWN_RAW':
                f = Field('unk_%02x' % off, off, sz, ty, 'bassa', 'UNKNOWN_RAW: no informative base sample (palindromic/zero in every pair)', 0, 0)
            else:
                cert = 'media' if (n >= MIN_N and d >= MIN_DTP and exc == 0) else 'bassa'
                if ty == 'u32' and (st, off) in FLOATS: ty = 'f32'
                f = Field(FNAME.get((st, off), '%s_%02x' % (st.lower(), off)), off, sz, ty, cert,
                          'BASE RULE: %d informative samples in %d DTPs, %d exceptions, only class consistent with all' % (n, d, exc), n, d)
            for b in range(off, off + sz): cov[b] = f
        fl = []; b = 0
        while b < size:
            f = cov.get(b)
            if f is None:
                e = b
                while e < size and e not in cov: e += 1
                f = Field('unk_%02x' % b, b, e - b, 'UNKNOWN_RAW', 'bassa', 'UNKNOWN_RAW: not covered by any rule/reader', 0, 0)
            fl.append(f); b = f.off + f.size
        out[st] = fl
    return out
SCHEMA = _build()

# ------------------------------------------------------------------------------------------------------------ recognizers (Xbox side)
class Inst(object):
    __slots__ = ('struct', 'tag', 'base', 'size', 'k', 'fields')
    def __init__(s, struct_, base, k=0):
        s.struct = struct_; s.tag = STRUCT_TAG[struct_]; s.base = base; s.size = STRUCT_SIZE[struct_]; s.k = k; s.fields = {}
    def __repr__(s): return 'Inst(%s@0x%x k=%d %s)' % (s.struct, s.base, s.k, s.fields)

def _u32(d, o): return struct.unpack_from('>I', d, o)[0]

def find_A(xd, rel):
    n = len(xd)
    if n < 20 or (n - 4) % 16: return []
    k = _u32(xd, 0)
    if k == 0 or n != 4 + 16 * k: return []
    ids = list(rel.idref) + list(getattr(rel, 'idref_a', []))
    if sorted(ids) != [(12, 4 + 16 * i) for i in range(k)]: return []
    return [Inst('A_HDR', 0)] + [Inst('A_REC', 4 + 16 * i, i) for i in range(k)]

def find_BC(xd, rel):
    out = []
    if xd[:4] != MAGIC or len(xd) < 0x80: return out
    it = dict(rel.internal); tg = sorted(set(it.values()) | {len(xd)})
    def nxt(a): return min([v for v in tg if v > a], default=len(xd))
    n = _u32(xd, 0x5c); a = it.get(0x60)
    if n and a is not None and nxt(a) - a == 32 * n and a + 32 * n <= len(xd):
        out += [Inst('TP', a + 32 * q, q) for q in range(n)]
    seg = it.get(0xc); ns = _u32(xd, 4)
    if seg is None or seg + 0x40 * ns > len(xd): return out
    for j in range(ns):
        h = it.get(seg + 0x40 * j + 0x3c)
        if h is None or h + 0x28 > len(xd): continue
        for k, (kind, es) in {0: ('HS', 36), 1: ('HB', 68), 3: ('HC', 56)}.items():
            c = _u32(xd, h + 8 * k); a = it.get(h + 8 * k + 4)
            if not c or a is None or nxt(a) - a != es * c: continue
            out += [Inst(kind, a + es * q, q) for q in range(c)]
    return out

def _ascii_ptr(xd, t):
    if t is None or t >= len(xd): return False
    z = xd.find(b'\0', t, t + 64)
    return z > t and all(32 <= c < 127 for c in xd[t:z])

def find_D(xd, rel):
    """uberobject graph descriptor: {+4 n, +8 ptr -> n 28-B nodes whose +8 is char*, +0x10 ptr}; nodes: n_trans<=64 with ptr array of internal ptrs"""
    out = []; it = dict(rel.internal); seen = set()
    if len(xd) < 0x54 + 28: return out
    for o8, t1 in sorted(it.items()):
        o = o8 - 8
        if o < 0 or o + 0x54 > len(xd) or (o + 0x10) not in it or xd[o:o + 4] == bytes.fromhex('beebbeeb'): continue
        n = _u32(xd, o + 4)
        if not 1 <= n <= 64 or t1 + 28 * n > len(xd): continue
        if not all(_ascii_ptr(xd, it.get(t1 + 28 * k + 8)) for k in range(n)): continue
        ok = True
        for k in range(n):
            nb = t1 + 28 * k; nt = _u32(xd, nb + 0xc); na = _u32(xd, nb + 0x14)
            if nt > 64 or na > 64 or (nt and (it.get(nb + 0x10) is None or any((it[nb + 0x10] + 4 * q) not in it for q in range(nt)))): ok = False; break
        if not ok: continue
        out.append(Inst('DESC', o))
        for k in range(n):
            nb = t1 + 28 * k
            if ('N', nb) not in seen: seen.add(('N', nb)); out.append(Inst('NODE', nb, k))
            nt = _u32(xd, nb + 0xc)
            for q in range(nt):
                tt = it.get(it[nb + 0x10] + 4 * q) if (nb + 0x10) in it else None
                if tt is not None and tt + 0x28 <= len(xd) and ('T', tt) not in seen: seen.add(('T', tt)); out.append(Inst('TRANS', tt, q))
    return out

def find_all(xd, rel, tags='ABCD'):
    out = []
    if 'A' in tags: out += find_A(xd, rel)
    if 'B' in tags or 'C' in tags: out += [i for i in find_BC(xd, rel) if i.tag in tags]
    if 'D' in tags: out += find_D(xd, rel)
    return out

def _slots(rel): return set(rel.pointer_offsets()) | set(rel.id_offsets())

# ------------------------------------------------------------------------------------------------------------ read / write
class F32(float):
    bits = 0
def _rd(d, o, f):
    t = f.type
    if t == 'u8': return d[o]
    if t in ('u16',): return struct.unpack_from('>H', d, o)[0]
    if t == 's16': return struct.unpack_from('>h', d, o)[0]
    if t in ('u32', 'id(12)', 'key32'): return struct.unpack_from('>I', d, o)[0]
    if t == 's32': return struct.unpack_from('>i', d, o)[0]
    if t == 'f32':
        v = F32(struct.unpack_from('>f', d, o)[0]); v.bits = struct.unpack_from('>I', d, o)[0]; return v
    return bytes(d[o:o + f.size])                    # ptr / UNKNOWN_RAW: raw bytes

def read_xbox(data, reloc, tags='ABCD'):
    """-> list of Inst with typed .fields {name: value}; reloc = parsed BE reloc or raw blob"""
    if isinstance(reloc, (bytes, bytearray)): reloc = R.parse(reloc, 'be')
    out = find_all(data, reloc, tags)
    for ins in out:
        for f in SCHEMA[ins.struct]:
            o = ins.base + f.off
            if o + f.size <= len(data): ins.fields[f.name] = _rd(data, o, f)
    return out

def _pack(f, v):
    t = f.type
    if t == 'u8': return bytes([v & 255])
    if t == 'u16': return struct.pack('<H', v)
    if t == 's16': return struct.pack('<h', v)
    if t in ('u32', 'id(12)'): return struct.pack('<I', v)
    if t == 's32': return struct.pack('<i', v)
    if t == 'f32': return struct.pack('<I', v.bits) if isinstance(v, F32) else struct.pack('<f', v)
    return bytes(v)

WRITABLE = ('u8', 'u16', 's16', 'u32', 's32', 'f32')
def write_pc(inst, fill=None, min_cert='media'):
    """PC (LE) bytes of the instance span.  Fields of type ptr / id / UNKNOWN_RAW and fields below min_cert come from `fill` (span-length
    PC bytes) or zeros: they are NOT schema-defined."""
    buf = bytearray(fill if fill is not None else bytes(inst.size))
    for f in SCHEMA[inst.struct]:
        if f.name in inst.fields and f.type in WRITABLE and CERT_RANK[f.cert] >= CERT_RANK[min_cert]:
            buf[f.off:f.off + f.size] = _pack(f, inst.fields[f.name])
    return bytes(buf)

def _determined(ins, f, xd):
    """UNKNOWN_RAW bytes inside a word that also holds declared (alta/media) fields: when every permutation that survives ALL informative base
    samples of that word gives the same bytes for THIS Xbox value, the bytes are determined by the word rule (n>=20, >=8 DTPs, 0 exceptions)."""
    wo = f.off - f.off % 4
    if f.off % 4 + f.size > 4: return None
    r = RULES.get((ins.struct, wo))
    if r is None or r[1] < MIN_N or r[2] < MIN_DTP or r[3]: return None
    if not any(g.type in WRITABLE and CERT_RANK[g.cert] >= CERT_RANK['media'] and wo <= g.off < wo + 4 for g in SCHEMA[ins.struct]): return None
    a = ins.base + wo
    if a + 4 > len(xd): return None
    xw = bytes(xd[a:a + 4]); res = set()
    for p in r[0]:
        pw = bytes(xw[j] for j in PERMS[p]); res.add(pw[f.off % 4:f.off % 4 + f.size])
    if len(res) != 1: return None
    return res.pop(), 'RULE-DETERMINED word rule {%s} n=%d dtp=%d exc=0: every surviving permutation gives these bytes for this value' % ('/'.join(r[0]), r[1], r[2])

def convert(xbox_bytes, xbox_reloc, pc_bytes, pc_reloc=None, tags='ABCD', min_cert='media', ids=None):
    """-> (new PC bytes, log).  Only schema fields (type numeric, cert >= min_cert, not on a reloc slot) are written; every other byte of
    the PC data is returned untouched.  log entries: dict(tag, struct, base, field, off, size, type, cert, src, xbox, old, new, status)
    status: CHANGED | SAME | SKIP_CERT (declared, below min_cert) | UNKNOWN (UNKNOWN_RAW bytes, unchanged) | SLOT (reloc-owned) |
    KEY (verify-only value key, e.g. TP.ID platform enum; never written) | LAYOUT
    DO NOT apply to the pc_copy / template routes of convert_drm (base-content sections already carry the real PC bytes), same guard as dtp_audit."""
    if isinstance(xbox_reloc, (bytes, bytearray)): xbox_reloc = R.parse(xbox_reloc, 'be')
    if len(pc_bytes) != len(xbox_bytes): return bytes(pc_bytes), [dict(status='LAYOUT', why='size')]
    if pc_reloc is not None:
        if isinstance(pc_reloc, (bytes, bytearray)): pc_reloc = R.parse(pc_reloc, 'le')
        if dict(pc_reloc.internal) != dict(xbox_reloc.internal): return bytes(pc_bytes), [dict(status='LAYOUT', why='internal relocs differ')]
    slots = _slots(xbox_reloc)
    out = bytearray(pc_bytes); log = []
    for ins in find_all(xbox_bytes, xbox_reloc, tags):
        for f in SCHEMA[ins.struct]:
            o = ins.base + f.off
            if o + f.size > len(xbox_bytes): continue
            e = dict(tag=ins.tag, struct=ins.struct, k=ins.k, base=ins.base, field=f.name, off=o, size=f.size, type=f.type, cert=f.cert,
                     src=f.src, xbox=bytes(xbox_bytes[o:o + f.size]).hex(), old=bytes(pc_bytes[o:o + f.size]).hex())
            det = _determined(ins, f, xbox_bytes) if f.type == 'UNKNOWN_RAW' else None
            if det is not None and CERT_RANK['media'] >= CERT_RANK[min_cert]:
                nb, why = det; e['new'] = nb.hex(); e['cert'] = 'media'; e['src'] = why; e['status'] = 'CHANGED' if nb != pc_bytes[o:o + f.size] else 'SAME'
                e['type'] = 'determined'; out[o:o + f.size] = nb
            elif f.type == 'UNKNOWN_RAW': e['status'] = 'UNKNOWN'; e['new'] = e['old']
            elif f.type == 'key32':
                e['status'] = 'KEY'; e['new'] = e['old']; e['keyok'] = bytes(reversed(xbox_bytes[o:o + 4])) == pc_bytes[o:o + 4]
            elif f.type in ('ptr', 'id(12)') or any(b in slots for b in range(o - o % 4, o + f.size)):
                e['status'] = 'SLOT'; e['new'] = e['old']
            elif CERT_RANK[f.cert] < CERT_RANK[min_cert]: e['status'] = 'SKIP_CERT'; e['new'] = e['old']
            else:
                xb = xbox_bytes[o:o + f.size]
                nb = bytes(xb) if f.size == 1 else bytes(reversed(xb))
                e['new'] = nb.hex(); e['status'] = 'CHANGED' if nb != pc_bytes[o:o + f.size] else 'SAME'
                out[o:o + f.size] = nb
            log.append(e)
    return bytes(out), log

# ------------------------------------------------------------------------------------------------------------ base pairs (independent test)
def _ctx():
    import dtpid_sweep as DS
    st, ids = DS.ctx(); ids.local = {}
    return DS, st, ids

def load_pairs():
    return pickle.load(open(os.path.join(W, 'generic', 'pairs.pkl'), 'rb'))

def pair_sections(xs, ps, ids):
    """[(xbox sec, pc sec)] type-7 with data.  by index when layouts align, else by remapped DTP id.  -> (pairs, n_unpaired)"""
    out = []; un = 0
    if len(xs) == len(ps) and all(a['type'] == b['type'] for a, b in zip(xs, ps)):
        for a, b in zip(xs, ps):
            if a['type'] == 7 and a['data'] is not None and b['data'] is not None: out.append((a, b, 'index'))
        return out, 0
    pm = collections.defaultdict(list)
    for b in ps:
        if b['type'] == 7 and b['data'] is not None: pm[b['id']].append(b)
    for a in xs:
        if a['type'] != 7 or a['data'] is None: continue
        l = pm.get(ids(7, a['id']))
        if l: out.append((a, l.pop(0), 'id'))
        else: un += 1
    return out, un

def _inf(xd, o, f):
    """is this field's Xbox value informative (a wrong permutation would give other bytes)?"""
    w = bytes(xd[o - o % 4:o - o % 4 + 4])
    if f.size == 4: return w[0] != w[3] or w[1] != w[2]
    if f.size == 2:
        a = o % 4; return w[a] != w[a + 1]
    a = o % 4; return any(w[m] != w[a] for m in range(4) if m != a)

def fold(name): return zlib.crc32(name.encode()) & 1

def base_test(min_cert='bassa', tags='ABCD', verbose=True):
    """apply convert (declared fields incl. low certainty so that their evidence is measured) to EVERY instance of every base pair:
    field bytes computed from the Xbox bytes only vs the real PC bytes.  -> stats dict"""
    pairs = load_pairs(); DS, st, ids = _ctx()
    S = {}                     # (struct, field) -> dict
    inst_tot = collections.Counter(); inst_ok = collections.Counter(); word_tot = collections.Counter(); word_ok = collections.Counter()
    skipped = collections.Counter(); exc = collections.defaultdict(list); id12 = collections.Counter()
    for name, ((xh, xs), (ph, ps)) in sorted(pairs.items()):
        prs, un = pair_sections(xs, ps, ids); skipped['unpaired'] += un
        for a, b, how in prs:
            xd, pd = a['data'], b['data']
            if len(xd) != len(pd): skipped['size_mismatch'] += 1; continue
            xr = R.parse(a['reloc'], 'be'); pr = R.parse(b['reloc'], 'le')
            if dict(xr.internal) != dict(pr.internal): skipped['layout_mismatch'] += 1; continue
            insts = find_all(xd, xr, tags)
            if not insts: continue
            # Xbox-only computation: start from a ZERO buffer, so matching real PC bytes cannot be trivial
            new, log = convert(xd, xr, bytes(len(xd)), pr, tags, min_cert)
            if log and log[0].get('status') == 'LAYOUT': skipped['layout_mismatch'] += 1; continue
            by_inst = collections.defaultdict(lambda: True); wordset = collections.defaultdict(lambda: True)
            for e in log:
                if e['status'] not in ('CHANGED', 'SAME', 'KEY'): continue
                o, sz = e['off'], e['size']
                ok = (new[o:o + sz] == pd[o:o + sz]) if e['status'] != 'KEY' else (bytes(reversed(xd[o:o + 4])) == bytes(pd[o:o + 4]))
                key = (e['struct'], e['field'])
                d = S.setdefault(key, dict(n=0, ok=0, ninf=0, okinf=0, dtp=set(), cert=e['cert'], type=e['type'], tag=e['tag'], inf_f=[0, 0], exc_f=[0, 0], dtp_f=[set(), set()], src=e['src']))
                ff = [f for f in SCHEMA[e['struct']] if f.name == e['field']][0]
                inf = _inf(xd, o, ff)
                d['n'] += 1; d['ok'] += ok
                if inf: d['ninf'] += 1; d['okinf'] += ok; d['dtp'].add((name, a['id'])); d['inf_f'][fold(name)] += 1; d['dtp_f'][fold(name)].add((name, a['id']))
                if not ok: d['exc_f'][fold(name)] += 1
                if not ok:
                    exc[key].append((name, a['id'], hex(o), e['xbox'], bytes(pd[o:o + sz]).hex(), bytes(new[o:o + sz]).hex()))
                by_inst[(e['struct'], e['base'])] &= ok
                for w in range(o - o % 4, o + sz, 4): wordset[(e['struct'], e['base'], w)] &= ok
            for k, v in by_inst.items(): inst_tot[k[0]] += 1; inst_ok[k[0]] += v
            for k, v in wordset.items(): word_tot[k[0]] += 1; word_ok[k[0]] += v
            if 'A' in tags:
                for ins in find_A(xd, xr):
                    if ins.struct == 'A_REC':
                        xv = struct.unpack_from('>I', xd, ins.base)[0]; pv = struct.unpack_from('<I', pd, ins.base)[0]
                        id12['n'] += 1; id12['ok'] += (ids(12, xv) == pv)
    return dict(fields=S, inst_tot=inst_tot, inst_ok=inst_ok, word_tot=word_tot, word_ok=word_ok, skipped=skipped, exc=exc, id12=id12)

def _enum_exc(key): return key == ('TP', 'ID')       # verify-only key: mismatches are platform enum remaps, not conversion errors

def real_pc_test(min_cert='media'):
    """CONVENTIONS selftest: convert(xbox, xreloc, REAL pc bytes) over every base pair must change 0 words"""
    pairs = load_pairs(); DS, st, ids = _ctx(); n = collections.Counter(); ch = []
    for name, ((xh, xs), (ph, ps)) in sorted(pairs.items()):
        prs, un = pair_sections(xs, ps, ids)
        for a, b, how in prs:
            xd, pd = a['data'], b['data']
            if len(xd) != len(pd): continue
            xr = R.parse(a['reloc'], 'be'); pr = R.parse(b['reloc'], 'le')
            if dict(xr.internal) != dict(pr.internal): continue
            new, log = convert(xd, xr, pd, pr, 'ABCD', min_cert)
            if not log: continue
            n['sections'] += 1; n['fields_checked'] += sum(e['status'] in ('SAME', 'CHANGED', 'KEY') for e in log)
            diff = [j - j % 4 for j in range(len(pd)) if new[j] != pd[j]]
            n['words_changed'] += len(set(diff))
            if diff: ch.append((name, a['id'], sorted(set(diff))[:4]))
    return n, ch

def cmd_selftest():
    r = base_test('bassa')
    print('== BASE PAIRS (work/generic/pairs.pkl): schema applied to the Xbox bytes of every instance, compared with the REAL PC bytes')
    print('skipped:', dict(r['skipped']))
    print('%-6s %9s %9s %9s %9s' % ('struct', 'inst', 'inst_ok', 'words', 'words_ok'))
    for s in ('A_HDR', 'A_REC', 'TP', 'HS', 'HB', 'HC', 'DESC', 'NODE', 'TRANS'):
        print('%-6s %9d %9d %9d %9d' % (s, r['inst_tot'][s], r['inst_ok'][s], r['word_tot'][s], r['word_ok'][s]))
    ex_other = {k: len(v) for k, v in r['exc'].items() if not _enum_exc(k)}
    print('TP instances with exceptions only in ID (KEY verify-only, platform enum remap, never written): %d of %d; exceptions in any other field: %s'
          % (len(r['exc'].get(('TP', 'ID'), ())), r['inst_tot']['TP'], ex_other or 0))
    print('A_REC idref (id 12) remap check ids(12,x)==pc:', dict(r['id12']))
    print('2-fold by DRM (crc32 of the base file name): per field informative samples per fold are listed when < 5 in one fold')
    print('%-6s %-10s %-5s %-6s %6s %6s %6s %6s %5s  exc' % ('struct', 'field', 'type', 'cert', 'n', 'ok', 'n_inf', 'ok_inf', 'dtp'))
    bad = 0
    for key in sorted(r['fields']):
        d = r['fields'][key]
        ex = len(r['exc'].get(key, ()))
        print('%-6s %-10s %-5s %-6s %6d %6d %6d %6d %5d  %d%s' % (key[0], key[1], d['type'], d['cert'], d['n'], d['ok'], d['ninf'], d['okinf'], len(d['dtp']), ex,
              '  (KEY verify-only: platform enum remap, never written)' if _enum_exc(key) and ex else ''))
        if ex and not _enum_exc(key): bad += 1
        rd = ('PC 0x' in d['src'] or 'XBOX 0x' in d['src'] or d['type'] == 'determined')
        if d['cert'] in ('alta', 'media') and not rd and (d['ninf'] < MIN_N or len(d['dtp']) < MIN_DTP):
            print('   !! CERT_CHECK: declared %s without reader but only %d informative samples / %d DTPs' % (d['cert'], d['ninf'], len(d['dtp'])))
        if d['cert'] in ('alta', 'media') and not rd and min(d['inf_f']) < 5:
            print('   (fold-thin: informative samples per DRM-fold %s)' % d['inf_f'])
    for key, l in sorted(r['exc'].items()):
        print('EXCEPTIONS', key, len(l)); [print('   ', x) for x in l[:6]]
    print()
    print('== FOLD STABILITY (declaration derived from ONE fold only): base-rule fields declared media that would fall below n>=%d informative samples or >=%d DTPs' % (MIN_N, MIN_DTP))
    for key in sorted(r['fields']):
        d = r['fields'][key]
        if d['cert'] != 'media' or 'BASE RULE' not in d['src']: continue
        for fo in (0, 1):
            if d['inf_f'][fo] < MIN_N or len(d['dtp_f'][fo]) < MIN_DTP:
                print('   %s.%s: fold %d alone has %d informative samples / %d DTPs (full set %d / %d)' % (key[0], key[1], fo, d['inf_f'][fo], len(d['dtp_f'][fo]), d['ninf'], len(d['dtp'])))
    print()
    n, ch = real_pc_test()
    print('== REAL-PC SELFTEST (CONVENTIONS): convert(xbox, xreloc, REAL pc bytes) on all base pairs: %s -> words changed %d' % (dict(n), n['words_changed']))
    for c in ch[:10]: print('   CHANGED', c)
    print('NOTE: base-rule fields were derived from the same 1054 pairs they are tested on: in-sample consistency (AND of classes, 0 exceptions), NOT independent proof.')
    print('      Independent evidence = engine readers (alta) only.')
    return r

def cmd_evidence():
    r = base_test('bassa')
    f = r['fields']; rows = []
    for key in sorted(f):
        d = f[key]; rows.append(dict(struct=key[0], field=key[1], type=d['type'], cert=d['cert'], n=d['n'], ok=d['ok'], n_inf=d['ninf'], ok_inf=d['okinf'], dtp=len(d['dtp'])))
    json.dump(rows, open(os.path.join(W, 'ws', 'schema', 'evidence.json'), 'w'), indent=1)
    print('written evidence.json (%d fields)' % len(rows))

# ------------------------------------------------------------------------------------------------------------ DLC scan / fix
def _overlay(dirs, names=None):
    import dtp_audit as A
    return A.overlay(dirs, names)

def _file_sections(rel, raw):
    """-> (D, [(xbox sec, pc section index, base_content)]) or None when no Xbox source resolves"""
    import dtp_audit as A, drm_write as DW
    xs = A.xsecs(rel)
    if xs is None: return None
    D = DW.read(raw, 'le')
    return D, [(x, i, A.base_content(x)) for x, i in A.section_pairs(xs, D) if x['type'] == 7]

def perm_names(xw, pw):
    n = [k for k, p in PERMS.items() if bytes(xw[j] for j in p) == pw]
    return '/'.join(n) if n else 'none'

def word_candidates(x, sec, log, new, bc, rel):
    """aggregate CHANGED field entries into 4-byte words.  Each candidate word: file, ids, offset, xbox/installed/schema words, fields, class."""
    by = collections.OrderedDict()
    for e in log:
        if e['status'] != 'CHANGED': continue
        by.setdefault(e['off'] - e['off'] % 4, []).append(e)
    out = []
    for w, es in by.items():
        xw = bytes(x['data'][w:w + 4]); ow = bytes(sec.data[w:w + 4]); nw = bytes(new[w:w + 4])
        cls = 'installed=%s schema=%s' % (perm_names(xw, ow), perm_names(xw, nw))
        if all(e['type'] == 'f32' for e in es) and len(es) == 1:
            fo = struct.unpack('<f', ow)[0]; fn = struct.unpack('<f', nw)[0]
            if fn == 0.0 and abs(fo) < 1e-30: cls = 'equiv_zero (-0.0 left raw: 0x80000000 vs denormal)'
        out.append(dict(file=rel, pc_id=sec.id, xbox_id=x['id'], off=w, xbox=xw.hex(), old=ow.hex(), new=nw.hex(), cls=cls, base_content=bc,
                        tags=sorted({e['tag'] for e in es}), cert=min((e['cert'] for e in es), key=lambda c: CERT_RANK[c]),
                        fields=[(e['struct'], e['k'], e['field'], e['type'], e['cert'], e['src']) for e in es], entries=es))
    return out

def scan_file(rel, path, tags='ABCD', min_cert='media', raw=None):
    raw = raw if raw is not None else open(path, 'rb').read()
    fs = _file_sections(rel, raw)
    if fs is None: return None, None, []
    D, prs = fs; cands = []; stat = collections.Counter()
    for x, i, bc in prs:
        sec = D.sections[i]
        if len(sec.data) != len(x['data']): stat['size_mismatch'] += 1; continue
        xr = R.parse(x['reloc'], 'be')
        new, log = convert(x['data'], xr, sec.data, sec.reloc, tags, min_cert)
        if log and log[0].get('status') == 'LAYOUT': stat['layout_mismatch'] += 1; continue
        for e in log: stat['field_' + e['status']] += 1
        cands += word_candidates(x, sec, log, new, bc, rel)
    return D, stat, cands

def _fmt(c):
    return '%s DTP %d(x%d) @0x%x xbox=%s installed=%s -> schema=%s [%s] %s%s' % (
        c['file'], c['pc_id'], c['xbox_id'], c['off'], c['xbox'], c['old'], c['new'], c['cls'],
        ','.join('%s.%s[%d]:%s/%s' % (f[0], f[2], f[1], f[3], f[4]) for f in c['fields']), ' (base_content)' if c['base_content'] else '')

def cmd_scan(dirs, tags='ABCD', names=None, out_json=None, verbose=True):
    allc = []; tot = collections.Counter(); skipped = []
    for rel, path in sorted(_overlay(dirs, names).items()):
        D, stat, cands = scan_file(rel, path, tags)
        if D is None: skipped.append(rel); continue
        tot.update(stat); allc += cands
    by = collections.Counter((tuple(sorted({f[0] + '.' + f[2] for f in c['fields']})), c['cls'], c['base_content']) for c in allc)
    print('scan dirs=%s tags=%s: %d candidate WORDS' % (dirs, tags, len(allc)))
    print('field statuses:', dict(tot)); print('no Xbox source (files not scanned):', skipped)
    for k, n in sorted(by.items(), key=lambda t: str(t)): print('  ', n, k)
    if verbose:
        for c in allc: print('  ', _fmt(c))
    if out_json: json.dump([{k: v for k, v in c.items() if k != 'entries'} for c in allc], open(out_json, 'w'), indent=0)
    return allc

NOWRITE = ('equiv_zero',)
def write_policy(c):
    """a word is written only when every field in it is alta/media, the section is DLC-new (not a base copy) and it is not an equivalence"""
    return (all(CERT_RANK[f[4]] >= CERT_RANK['media'] for f in c['fields']) and not c['base_content']
            and not c['cls'].startswith(NOWRITE))

D_RAFT_FILES = ('dlc1_uo_raft_bridge.drm',)      # mandate for tag D: the raft_bridge shot->event->state path; other D words are opt-in ('extra')

def _dscope_ok(c, dscope):
    if 'D' not in c['tags']: return True
    inraft = os.path.basename(c['file']) in D_RAFT_FILES
    return dscope == 'all' or (dscope == 'raft' and inraft) or (dscope == 'extra' and not inraft)

def _note(c):
    certs = {f[4] for f in c['fields']}
    if len(c['fields']) > 1 and 'alta' in certs and 'media' in certs:
        return 'word written whole: alta field(s) backed by readers on both platforms, the other bytes by the base word rule - writing only the reader-backed byte would leave a hybrid of two permutations that no platform has'
    return ''

def cmd_fix(out, dirs, tags='ABCD', names=None, dscope='raft'):
    import drm_write as DW
    os.makedirs(out, exist_ok=True); md5 = []; allc = []
    for rel, path in sorted(_overlay(dirs, names).items()):
        raw = open(path, 'rb').read()
        D, stat, cands = scan_file(rel, path, tags, raw=raw)
        if D is None: continue
        todo = [c for c in cands if write_policy(c) and _dscope_ok(c, dscope)]
        if not todo: continue
        for c in todo:
            sec = [s for s in D.sections if s.type == 7 and s.id == c['pc_id']][0]
            b = bytearray(sec.data); w = c['off']
            assert bytes(b[w:w + 4]).hex() == c['old']
            b[w:w + 4] = bytes.fromhex(c['new']); sec.data = bytes(b)
        o = D.write('le')
        if raw[:4] == b'CDRM': o = DW.cdrm_encode(o, 'le')
        dst = os.path.join(out, rel); os.makedirs(os.path.dirname(dst), exist_ok=True); open(dst, 'wb').write(o)
        _, _, again = scan_file(rel, dst, tags)                      # idempotence: nothing left to write
        left = [c for c in again if write_policy(c) and _dscope_ok(c, dscope)]
        D0 = DW.read(raw, 'le'); D2 = DW.read(open(dst, 'rb').read(), 'le')
        assert D0.names == D2.names and len(D0.sections) == len(D2.sections)
        changed = set()
        for a0, a2 in zip(D0.sections, D2.sections):
            assert (a0.type, a0.id, a0.reloc, a0.ver, a0.flags) == (a2.type, a2.id, a2.reloc, a2.ver, a2.flags)
            if a0.data != a2.data: changed |= {(a0.id, j - j % 4) for j in range(len(a0.data)) if a0.data[j] != a2.data[j]}
        logged = {(c['pc_id'], c['off']) for c in todo}
        assert changed == logged, (sorted(changed ^ logged)[:5])
        h = hashlib.md5(o).hexdigest(); md5.append('%s  %s' % (h, rel))
        print(rel, 'words written', len(todo), 'words changed', len(changed), 'recheck left', len(left), 'md5', h)
        allc += todo
    open(os.path.join(out, 'md5.txt'), 'w').write('\n'.join(md5) + '\n')
    with open(os.path.join(out, 'words.tsv'), 'w') as f:
        f.write('file\tpc_dtp\txbox_dtp\ttag\tstruct[k]\tfield\ttype\tcert\toffset\txbox\tinstalled\tnew\tclass\tsource\tnote\n')
        for c in allc:
            for (st_, k, fld, ty, cert, src) in c['fields']:
                f.write('\t'.join(str(x) for x in (c['file'], c['pc_id'], c['xbox_id'], STRUCT_TAG[st_], '%s[%d]' % (st_, k), fld, ty, cert, hex(c['off']),
                        c['xbox'], c['old'], c['new'], c['cls'], src, _note(c))) + '\n')
    with open(os.path.join(out, 'diff.txt'), 'w') as f:
        for c in allc: f.write(_fmt(c) + '\n')
    print('written', len(allc), 'words in', len(md5), 'files ->', out)
    return md5

def cmd_coverage(dirs, tags='ABCD'):
    """DLC sections the schema CANNOT check: PC size != Xbox size (analog / re-authored route): structures found on their Xbox side"""
    import dtp_audit as A
    n = 0; lines = []
    for rel, path in sorted(_overlay(dirs).items()):
        raw = open(path, 'rb').read(); fs = _file_sections(rel, raw)
        if fs is None: lines.append('%s: NO XBOX SOURCE (not scanned at all)' % rel); continue
        D, prs = fs
        for x, i, bc in prs:
            sec = D.sections[i]
            if len(sec.data) == len(x['data']): continue
            n += 1
            ins = find_all(x['data'], R.parse(x['reloc'], 'be'), tags)
            st = collections.Counter(i.struct for i in ins)
            lines.append('%s DTP pc=%d xbox=%d size xbox=%d pc=%d base_content=%s structures(Xbox side)=%s' % (rel, sec.id, x['id'], len(x['data']), len(sec.data), bc, dict(st) or 'none'))
    print('\n'.join(lines)); print('size-mismatch DLC type-7 sections:', n)

def cmd_table():
    for st in ('A_HDR', 'A_REC', 'TP', 'HS', 'HB', 'HC', 'DESC', 'NODE', 'TRANS'):
        print('== %s (tag %s, %d bytes)' % (st, STRUCT_TAG[st], STRUCT_SIZE[st]))
        print('  %-5s %-4s %-12s %-10s %-6s %s' % ('off', 'size', 'field', 'type', 'cert', 'source'))
        for f in SCHEMA[st]: print('  0x%02x  %-4d %-12s %-10s %-6s %s' % (f.off, f.size, f.name, f.type, f.cert, f.src))

if __name__ == '__main__':
    a = sys.argv[1:]
    sets = None; tags = 'ABCD'
    if '--set' in a: i = a.index('--set'); sets = a[i + 1]; del a[i:i + 2]
    if '--tags' in a: i = a.index('--tags'); tags = a[i + 1]; del a[i:i + 2]
    dscope = 'raft'
    if '--dscope' in a: i = a.index('--dscope'); dscope = a[i + 1]; del a[i:i + 2]
    if not a: print(__doc__); sys.exit(0)
    dirs = [d if os.path.isabs(d) else os.path.join(W, d) for d in sets.split(',')] if sets else [os.path.join(W, 'baseline', 'B2', 'mods')]
    if a[0] == 'selftest': cmd_selftest()
    elif a[0] == 'evidence': cmd_evidence()
    elif a[0] == 'table': cmd_table()
    elif a[0] == 'coverage': cmd_coverage(dirs, tags)
    elif a[0] == 'scan': cmd_scan(dirs, tags, set(a[1:]) or None, verbose=True)
    elif a[0] == 'fix': cmd_fix(a[1] if os.path.isabs(a[1]) else os.path.join(W, a[1]), dirs, tags, set(a[2:]) or None, dscope)
