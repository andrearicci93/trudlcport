"""DLC 2 sonar in the PDA (owner's wish Q6, 2026-11-17) - an OPT-IN variant of the ported g_pda, NOT Xbox-faithful.

The Xbox DLC 2 PDA (pack11 g_pda script Xbox 3207 = PC 3347, the "shadow PDA") has no sonar entry: open (f2) checks
f1 = `level tag == "dlc2"` and then shows the journal-style art +1364 and only three items: +208 OBJECTIVES / HINTS
(26427), +216 AREA INFO, +224 CONTROLS (26428) - docs/ENGINE.md "PDA main menu per level". The sonar code of tru.exe
has no DLC lock (0x6e53f0), only this menu decides. Two variants (default: none = the Xbox menu):

  entry    the shadow PDA keeps its art and its three items and gets a fourth row SONAR MAP under CONTROLS. The row is
           item +264 - the Xbox script's ninth menu item (label uitext +340, row bars uibitmap +640 / +748), which no
           branch ever adds to the menu (f2 adds +208..+256 or +208 / +216 / +224; only its two bars are shown / hidden
           with +272's at f2 +0x4294..+0x4320). Its focus (f10), lost-focus (f11) and action (f9) cases exist; this
           variant gives it the base game's sonar behaviour when f1 is true:
             W1-W3 init data: y of label +340 / bars +640 / +748 = y of the row-4 widgets +316 / +592 / +700 (the nine
                   rows are placed by their init position, x / z / size / textures of +264's widgets = +232's)
             B1  f2 +0x4474 (DLC 2 branch, after `menu.add(+224)`): label +340 = m1316 (SONAR MAP, the text the base
                 branch puts on +280) as f2 +0x4550, `menu.add(+264)` as f2 +0x4464 -> rows 1-4, navigation in that order
             B2  f9 +0x5bd0 (action, case m1048 = item +264): f1 true -> the base sonar path of case m1032 (+0x596c:
                 f28 map check, f4 = open the ping map screen 3365); else the original case
             B3  f10 +0x0c94 (focus, case +264): f1 true -> f18, m1024 = m1048 (so the action finds +264), then the
                 base game's "PING MAP ITEM CAUGHT FOCUS" statements of case +208 (+0x0800..+0x08a0, sonar texts /
                 preview, f28 decides the "not available" text), then the end of the +264 case (+0x0ce8)
             B4  f11 +0x1194 (lost focus, case +264): f1 true -> case +208's lost-focus statements (+0x1274, no f1
                 branch there - the undo of both +208 focus forms)
           Every block is reached by an op63 that replaces one op00 line marker (the generalbank ring-menu technique,
           tools/menu_ring_p14.py, live since 2026-11-10) and returns with op63 / op64; every call target is copied
           from an existing call of the same thing in 3347 (no guessed offsets); f1 / f18 / f28 by the internal
           pointer the original calls use. Outside DLC 2 (f1 false) every block falls back to the original words.
  basepda  f1 always false (+0x22b4 `04000001` -> `04000000`): DLC 2 shows the base PDA (Croft VX2 frame, 7 items
           with SONAR MAP and WEAPON SELECTION, no OBJECTIVES / CONTROLS) - the same word TruMenu's
           `[PDA] ShadowPdaAsBasePda` writes at runtime (0.22.51), here as a file

Library (tools/gpda_port.py): apply(d, r, mode, st, risk) on the built 3347 (after insert_slot31); gate(d, r) ->
(mode, exempt code offsets, problems, info) for gate 13 and the opcode gate 3.

Usage (from the repository root; nothing touches the game folder):
  ../bin/pyt -t 1800 tools/gpda_dlc2_sonar.py apply G_PDA OUT_DIR MODE
        MODE entry / basepda on an already built g_pda (tools/gpda_port.py build output, no variant) -> OUT_DIR/mods/
        g_pda.drm + OUT_DIR/dlc2_sonar_report.json; then every gpda_port gate on the written file (exit 1 = removed)
  ../bin/pyt -t 300 tools/gpda_dlc2_sonar.py status G_PDA
        read-only: which variant the file holds (none / entry / basepda / broken) and the gate-13 problems
"""
import sys, os, struct, json, hashlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW, drm_reloc as R, script_conv as SC

SID = 3347
PH = 0xBEEBBEEB
MODES = ('entry', 'basepda')
EXTRA = dict(SC.Walk.EXTRA); EXTRA[0x02] = 1          # op02 push float literal: 1 extra word (menu_dlc_probe.PUSHF)
JUMPS = (0x63, 0x64)
F1_TRUE = (0x22b4, 0x04000001, 0x04000000,             # basepda: f1's "return 1" byte push
           {0x22a8: 0x64000005, 0x22b0: 0x08000000, 0x22b8: 0x2e000000, 0x22c8: 0x04000000, 0x22cc: 0x2e000000})
# W: (word, old, new, source of the new value) - row 8 (+264's widgets) -> row 4 (+232's)
WORDS = ((0x8540, 0x40600000, 0xbfa66666, 0x8320, 'label uitext +340 y (row 8 -> row 4 = label +316)'),
         (0x9df0, 0x406ccccd, 0xbf8ccccd, 0x9920, 'bar uibitmap +640 y (= +592, row 4 highlight)'),
         (0xa750, 0x4059999a, 0xbfb33333, 0xa2a0, 'bar uibitmap +748 y (= +700, row 4 underline)'))
# the widget pairs whose init heads must be equal apart from y (and the uitext id leaf): (member, twin, node, twin node)
TWINS = ((340, 316, 0x8524, 0x8304), (640, 592, 0x9dd4, 0x9904), (748, 700, 0xa734, 0xa284))
HEAD = 0x3c                                             # bytes of the compared init head (flags .. scale, colours)


def op(o, n=0):
    return ((o & 0xff) << 24) | (n & 0xffffff)


def s24(v):
    v &= 0xffffff
    return v - (1 << 24) if v & 0x800000 else v


class Refuse(Exception):
    """the input is not the expected 3347 - nothing is written"""


class Sec:
    """script 3347 of a built (PC, little-endian) g_pda: words, relocations, function code ranges"""
    def __init__(self, d, r):
        self.d, self.r = d, r
        self.it = dict(r.internal)
        self.ext = {so: (si, do) for si, so, do in r.external}
        self.W = SC.Walk(bytes(d), r, 'le').run()
        self.code = []
        for nm, t, n, sz in self.W.arrays:
            if nm == 'funcs':
                for j in range(n):
                    ct = self.it.get(t + sz * j + 0x18)
                    if ct is not None: self.code.append((j, ct, ct + 4 * self.w(ct - 4)))
        ft = [(t, n, sz) for nm, t, n, sz in self.W.arrays if nm == 'funcs'][0]
        self.proto_of = {j: self.it.get(ft[0] + ft[2] * j) for j in range(ft[1])}

    def w(self, a): return struct.unpack_from('<I', self.d, a)[0]

    def func_of(self, a):
        return next((j for j, lo, hi in self.code if lo <= a < hi), None)

    def instrs(self, lo, hi):
        o = lo
        while o < hi:
            w = self.w(o); n = EXTRA.get(w >> 24, 0)
            yield o, w >> 24, w
            o += 4 * (1 + n)

    def jump_targets(self):
        jt = {}
        for j, lo, hi in self.code:
            for o, opc, w in self.instrs(lo, hi):
                if opc in JUMPS: jt.setdefault(o + 4 + 4 * s24(w), []).append(o)
        return jt

    def trigrams(self, lo, hi, cut_last=False):
        """opcode 3-grams without op00 markers, cut after every jump (tools/menu_ring_p14.trigrams)"""
        out, run = [], []
        for o, opc, w in self.instrs(lo, hi):
            if opc == 0x00: continue
            run.append(opc)
            if opc in JUMPS:
                out += [tuple(run[k:k + 3]) for k in range(len(run) - 2)]; run = []
        out += [tuple(run[k:k + 3]) for k in range(len(run) - 2)]
        return out


# ---- the plan: sites, expected words, blocks (words: (value, reloc, why); reloc ('ext', ref) / ('int', ref) copies
# the relocation of the reference word ref of the same section, ('jmp', target) / ('jz', target) are op63 / op64)
def ref_call(member, ref, why):
    return [(op(0x0f, member), None, 'push member +%d' % member), (op(0x65), None, 'native call'),
            (PH, ('ext', ref), why)]


def own_call(ref, why):
    return [(op(0x68), None, 'own function call'), (PH, ('int', ref), why)]


def f1_test(local, back):
    return ([(op(0x09, local), None, 'push &local %d (byte result)' % local)] +
            own_call(0x595c, 'f1 (level tag == "dlc2"), pointer as f9 +0x5958') +
            [(op(0x06, local), None, 'push local %d' % local), (None, ('jz', back), 'op64: not DLC 2 -> the original words')])


SITES = [
    dict(key='B1', func=2, site=0x4474, marker=66, back_word=op(0, 67), note='f2 DLC 2 branch after menu.add(+224)',
         ctx={0x4464: op(0x0f, 224), 0x4468: op(0x0f, 188), 0x446c: op(0x65), 0x4480: op(0x63, 74),
              0x4404: op(0x0f, 1308), 0x4408: op(0x0f, 280)},
         code=lambda: ([(op(0x0f, 1316), None, 'push m1316 (localstr SONAR MAP, as f2 +0x4550)'),
                        (op(0x0f, 340), None, 'push label uitext +340'), (op(0x65), None, 'native call'),
                        (PH, ('ext', 0x455c), 'uitext f39 (set text), as f2 +0x4558')] +
                       [(op(0x0f, 264), None, 'push item +264'), (op(0x0f, 188), None, 'push uimenu +188'),
                        (op(0x65), None, 'native call'), (PH, ('ext', 0x4470), 'uimenu f25 (add item), as f2 +0x446c')] +
                       [(None, ('jmp', 0x4478), 'op63 back')])),
    dict(key='B2', func=9, site=0x5bd0, marker=268, back_word=op(0, 269), note='f9 action, case m1048 (item +264)',
         ctx={0x5bc0: op(0x08, 40), 0x5bc4: op(0x0e, 1048), 0x5bc8: op(0x45), 0x596c: op(0, 228),
              0x5954: op(0x09, 44), 0x5958: op(0x68), 0x5974: op(0x09, 45), 0x598c: op(0x68)},
         code=lambda: f1_test(44, 0x5bd4) + [(None, ('jmp', 0x596c), 'op63 to the base sonar path of case m1032 '
                                                                     '(f28 check, f4 = open ping map 3365)')]),
    dict(key='B3', func=10, site=0x0c94, marker=507, back_word=op(0, 508), note='f10 focus, case item +264',
         ctx={0x0c70: op(0x0f, 264), 0x0c9c: op(0x68), 0x0ca8: op(0x0f, 1024), 0x0cac: op(0x0e, 1048),
              0x0ce8: op(0, 514), 0x0c90: op(0x64, 21), 0x07f0: op(0x0f, 1024), 0x07f4: op(0x0e, 1032), 0x0830: op(0x09, 13)},
         code=lambda: (f1_test(12, 0x0c98) +
                       own_call(0x0ca0, 'f18, as the case\'s own +0x0c9c') +
                       [(op(0x0f, 1024), None, 'push &m1024 (focused item id)'), (op(0x0e, 1048), None, 'push m1048'),
                        (op(0x2f), None, 'store (m1024 = m1048, as +0x0ca8)')] +
                       ref_call(1352, 0x0808, 'uitext f4, as +0x0804') +
                       ref_call(436, 0x0818, 'uibitmap f4, as +0x0814') +
                       ref_call(808, 0x0828, 'uitext f3, as +0x0824') +
                       [(op(0x09, 13), None, 'push &local 13')] + own_call(0x0838, 'f28 (sonar allowed here), as +0x0834') +
                       [(op(0x06, 13), None, 'push local 13'), (None, ('jz', 'ELSE'), 'not allowed -> else')] +
                       ref_call(904, 0x0854, 'uitext f3, as +0x0850') +
                       ref_call(1012, 0x0864, 'uitext f4, as +0x0860') +
                       [(None, ('jmp', 0x0ce8), 'op63 to the end of the +264 case')] +
                       [('ELSE', None, '')] +
                       ref_call(1012, 0x0880, 'uitext f3, as +0x087c') +
                       ref_call(904, 0x0890, 'uitext f4, as +0x088c') +
                       ref_call(1068, 0x08a0, 'uitext f4, as +0x089c') +
                       [(None, ('jmp', 0x0ce8), 'op63 to the end of the +264 case')])),
    dict(key='B4', func=11, site=0x1194, marker=566, back_word=op(0, 567), note='f11 lost focus, case item +264',
         ctx={0x1170: op(0x0f, 264), 0x1274: op(0, 582), 0x1250: op(0x0f, 208), 0x127c: op(0x0f, 436),
              0x10e4: op(0x09, 20), 0x10e8: op(0x68)},
         code=lambda: f1_test(20, 0x1198) + [(None, ('jmp', 0x1274), 'op63 to case +208\'s lost-focus statements')]),
]


def expected(sec, site, block):
    """the planned words of one site's block at address block: [(addr, value, reloc (kind, si, dst) / ('jump',) or
    None, why)]; the first word is the replaced op00 marker"""
    raw = [(op(0, site['marker']), None, 'the replaced line marker op00 %d' % site['marker'])] + site['code']()
    labels, a = {}, block
    for v, rl, why in raw:
        if v == 'ELSE': labels['ELSE'] = a; continue
        a += 4
    out, a = [], block
    for v, rl, why in raw:
        if v == 'ELSE': continue
        rel = None
        if rl and rl[0] in ('jmp', 'jz'):
            t = labels[rl[1]] if isinstance(rl[1], str) else rl[1]
            v = op(0x63 if rl[0] == 'jmp' else 0x64, (t - (a + 4)) // 4); rel = ('jump',)
        elif rl and rl[0] == 'ext':
            if rl[1] not in sec.ext: raise Refuse('%s: reference +0x%x has no external relocation' % (site['key'], rl[1]))
            si, do = sec.ext[rl[1]]; rel = ('ext', si, do); v = sec.w(rl[1])
        elif rl and rl[0] == 'int':
            if rl[1] not in sec.it: raise Refuse('%s: reference +0x%x has no internal pointer' % (site['key'], rl[1]))
            rel = ('int', None, sec.it[rl[1]]); v = sec.w(rl[1])
        out.append((a, v, rel, why)); a += 4
    return out


def check_input(sec, site, jt, original=True):
    """the site and its context are the expected words of the built 3347 (original: the site still op00)"""
    a = site['site']
    if sec.func_of(a) != site['func']: raise Refuse('%s: +0x%x is not in function %d' % (site['key'], a, site['func']))
    if original and sec.w(a) != op(0, site['marker']):
        raise Refuse('%s: +0x%x is %08x, expected op00 %d' % (site['key'], a, sec.w(a), site['marker']))
    if a in sec.it or a in sec.ext: raise Refuse('%s: +0x%x is a pointer word' % (site['key'], a))
    if sec.w(a + 4) != site['back_word']: raise Refuse('%s: +0x%x is %08x, expected %08x' % (
        site['key'], a + 4, sec.w(a + 4), site['back_word']))
    for o, want in site['ctx'].items():
        if sec.w(o) != want: raise Refuse('%s: context +0x%x is %08x, expected %08x' % (site['key'], o, sec.w(o), want))
    for t in (a, a + 4):
        if t in jt: raise Refuse('%s: jumps from %s land on +0x%x' % (site['key'], ['+0x%x' % x for x in jt[t]], t))


def jump_ok(sec, site, rows):
    """every jump of the block lands inside the block or on an op00 marker of the site's own function"""
    lo, hi = rows[0][0], rows[-1][0] + 4
    bad = []
    for a, v, rel, why in rows:
        if rel == ('jump',):
            t = a + 4 + 4 * s24(v)
            if lo <= t < hi: continue
            if sec.func_of(t) != site['func'] or sec.w(t) >> 24 != 0:
                bad.append('%s +0x%x -> +0x%x (func %s, word %08x)' % (site['key'], a, t, sec.func_of(t), sec.w(t)))
    return bad


def apply(d, r, mode, st, risk):
    """d: bytearray of the built 3347 (PC layout, after insert_slot31), r: its Reloc - changed in place"""
    if mode not in MODES: raise Refuse('mode %s (want %s)' % (mode, '/'.join(MODES)))
    sec = Sec(d, r)
    if mode == 'basepda':
        o, old, new, ctx = F1_TRUE
        if sec.func_of(o) != 1 or sec.w(o) != old or any(sec.w(a) != v for a, v in ctx.items()):
            raise Refuse('f1 +0x%x is %08x (want %08x with its context)' % (o, sec.w(o), old))
        struct.pack_into('<I', d, o, new)
        st['dlc2 sonar basepda: f1 always false'] += 1
        risk.append('%d +0x%x: f1 "return 1" %08x -> %08x (variant basepda, not Xbox-faithful)' % (SID, o, old, new))
        return dict(mode=mode, words={o: (old, new)})
    jt = sec.jump_targets()
    for s in SITES: check_input(sec, s, jt)
    for o, old, new, src, why in WORDS:
        if sec.w(o) != old or sec.w(src) != new: raise Refuse('%s: +0x%x %08x (want %08x), source +0x%x %08x' % (
            why, o, sec.w(o), old, src, sec.w(src)))
    probs = twin_heads(sec, before=True)
    if probs: raise Refuse('row widgets: %s' % probs)
    info = dict(mode=mode, blocks={}, words={})
    while len(d) % 4: d.append(0)
    for s in SITES:
        block = len(d)
        rows = expected(sec, s, block)
        bad = jump_ok(sec, s, rows)
        if bad: raise Refuse('jumps: %s' % bad)
        for a, v, rel, why in rows:
            d += struct.pack('<I', v)
            if rel and rel[0] == 'ext': r.external.append((rel[1], a, rel[2]))
            elif rel and rel[0] == 'int': r.internal.append((a, rel[2]))
        struct.pack_into('<I', d, s['site'], op(0x63, (block - (s['site'] + 4)) // 4))
        info['blocks'][s['key']] = dict(site=s['site'], block=block, words=len(rows), note=s['note'])
        st['dlc2 sonar entry: block %s (%d words)' % (s['key'], len(rows))] += 1
        risk.append('%d +0x%x: op00 %d -> op63 to block %s +0x%x (variant entry, not Xbox-faithful)' % (
            SID, s['site'], s['marker'], s['key'], block))
    for o, old, new, src, why in WORDS:
        struct.pack_into('<I', d, o, new); info['words'][o] = (old, new)
        st['dlc2 sonar entry: init words'] += 1
        risk.append('%d +0x%x: %s %08x -> %08x' % (SID, o, why, old, new))
    return info


def twin_heads(sec, before):
    """+264's three widgets = +232's apart from y (and the uitext text id): init heads compared word by word"""
    probs = []
    for m, tw, n, tn in TWINS:
        for k in range(0, HEAD, 4):
            if (n + k) in sec.it or (tn + k) in sec.it: continue
            a, b = sec.w(n + k), sec.w(tn + k)
            if k == 0x1c and before: continue                # y: differs before, equal after
            if a != b: probs.append('+%d node +0x%x = %08x, +%d %08x' % (m, k, a, tw, b))
    return probs


def gate(d, r):
    """gate 13 on a built 3347: (mode, {code offset: reason} exempt from the opcode gate, problems, info).
    mode none = no site changed (and f1 as built); entry / basepda = that variant complete and as planned"""
    sec = Sec(bytearray(d), r)
    probs, exempt, info = [], {}, {}
    o, old, new, ctx = F1_TRUE
    f1 = sec.w(o)
    hooks = {s['key']: sec.w(s['site']) for s in SITES}
    is_hook = {k: v >> 24 == 0x63 for k, v in hooks.items()}
    yw = {x[0]: sec.w(x[0]) for x in WORDS}
    if not any(is_hook.values()) and f1 == old and all(yw[x[0]] == x[1] for x in WORDS):
        return 'none', exempt, probs, dict(f1='%08x' % f1)
    if f1 == new and not any(is_hook.values()) and all(yw[x[0]] == x[1] for x in WORDS):
        if any(sec.w(a) != v for a, v in ctx.items()): probs.append('basepda: f1 context changed')
        return 'basepda', exempt, probs, dict(f1='%08x' % f1)
    mode = 'entry'
    if f1 != old: probs.append('entry: f1 +0x%x is %08x, want %08x' % (o, f1, old))
    for x in WORDS:
        if yw[x[0]] != x[2]: probs.append('entry: %s is %08x, want %08x' % (x[4], yw[x[0]], x[2]))
        if sec.w(x[3]) != x[2]: probs.append('entry: source +0x%x is %08x, want %08x' % (x[3], sec.w(x[3]), x[2]))
    probs += ['entry: ' + p for p in twin_heads(sec, before=False)]
    known = set()
    for j, lo, hi in sec.code: known.update(sec.trigrams(lo, hi))
    jt = sec.jump_targets()
    added_ext, added_int = set(), set()
    for s in SITES:
        a = s['site']
        if not is_hook[s['key']]: probs.append('entry: %s site +0x%x is %08x, not op63' % (s['key'], a, hooks[s['key']])); continue
        block = a + 4 + 4 * s24(hooks[s['key']])
        try:
            check_input(sec, s, {t: v for t, v in jt.items() if t not in (a, a + 4)}, original=False)
            rows = expected(sec, s, block)
        except Refuse as e:
            probs.append('entry: %s' % e); continue
        if block < max(hi for j, lo, hi in sec.code) or block + 4 * len(rows) > len(sec.d):
            probs.append('entry: %s block +0x%x not in the appended area' % (s['key'], block)); continue
        for ra, v, rel, why in rows:
            if sec.w(ra) != v: probs.append('entry: %s +0x%x is %08x, planned %08x (%s)' % (s['key'], ra, sec.w(ra), v, why))
            if rel and rel[0] == 'ext':
                if sec.ext.get(ra) != (rel[1], rel[2]): probs.append('entry: %s +0x%x external %s, planned %s' % (
                    s['key'], ra, sec.ext.get(ra), (rel[1], rel[2])))
                added_ext.add(ra)
            elif rel and rel[0] == 'int':
                if sec.it.get(ra) != rel[2]: probs.append('entry: %s +0x%x internal %s, planned %s' % (
                    s['key'], ra, sec.it.get(ra), rel[2]))
                added_int.add(ra)
            elif ra in sec.it or ra in sec.ext: probs.append('entry: %s +0x%x unplanned pointer' % (s['key'], ra))
        probs += ['entry: ' + x for x in jump_ok(sec, s, rows)]
        # shape: every opcode 3-gram of the block (without its final structural jump) occurs in 3347's own code
        for g in sec.trigrams(block, rows[-1][0]):
            if g not in known: probs.append('entry: %s opcode sequence %s not in the original code' % (
                s['key'], ' '.join('op%02x' % x for x in g)))
        exempt[a] = '%s: op00 %d -> op63' % (s['key'], s['marker'])
        info[s['key']] = dict(site='+0x%x' % a, block='+0x%x' % block, words=len(rows))
    return mode, exempt, probs, info


# ------------------------------------------------------------------------------------------------ CLI
def md5(b): return hashlib.md5(bytes(b)).hexdigest()


def safe_rel(p):
    try: return os.path.relpath(p)
    except ValueError: return os.path.abspath(p)


def main(a):
    if len(a) >= 2 and a[0] == 'status':
        D = DW.read(open(a[1], 'rb').read(), 'le')
        s = next(x for x in D.sections if x.type == 8 and x.id == SID)
        mode, ex, probs, info = gate(s.data, R.parse(s.reloc, 'le'))
        print('dlc2 sonar variant: %s %s' % (mode, info))
        for p in probs: print('  problem: %s' % p)
        if mode == 'entry' and '--dump' in a:
            sec = Sec(bytearray(s.data), R.parse(s.reloc, 'le'))
            for st_ in SITES:
                blk = st_['site'] + 4 + 4 * s24(sec.w(st_['site']))
                print('%s %s: site +0x%x -> block +0x%x' % (st_['key'], st_['note'], st_['site'], blk))
                for ra, v, rel, why in expected(sec, st_, blk):
                    tgt = ' -> +0x%x (func %s, %08x)' % (ra + 4 + 4 * s24(v), sec.func_of(ra + 4 + 4 * s24(v)),
                                                          sec.w(ra + 4 + 4 * s24(v))) if rel == ('jump',) else ''
                    ptr = ' ext %s' % (sec.ext.get(ra),) if ra in sec.ext else ' int +0x%x' % sec.it[ra] if ra in sec.it else ''
                    print('   +0x%x %08x op%02x%s%s  %s' % (ra, sec.w(ra), sec.w(ra) >> 24, tgt, ptr, why))
        return 1 if probs else 0
    if len(a) >= 4 and a[0] == 'apply':
        src, out, mode = a[1], a[2], a[3]
        raw = open(src, 'rb').read()
        D = DW.read(raw, 'le')
        s = next(x for x in D.sections if x.type == 8 and x.id == SID)
        m0 = gate(s.data, R.parse(s.reloc, 'le'))[0]
        if m0 != 'none': print('FAIL: %s already holds variant %s' % (src, m0)); return 1
        d = bytearray(s.data); r = R.parse(s.reloc, 'le'); st = collections.Counter(); risk = []
        try:
            info = apply(d, r, mode, st, risk)
        except Refuse as e:
            print('FAIL (nothing written): %s' % e); return 1
        s.data, s.reloc = bytes(d), R.write(r, 'le')
        blob = DW.cdrm_encode(D.write('le'), 'le') if raw[:4] == b'CDRM' else D.write('le')
        os.makedirs(os.path.join(out, 'mods'), exist_ok=True)
        fn = os.path.join(out, 'mods', 'g_pda.drm')
        open(fn, 'wb').write(blob)
        import gpda_port as GP
        K = GP.load_knowledge(); I = GP.ids()
        PCS = GP.read_pc(); pc = {(x['type'], x['id']): x for x in PCS}
        PK = GP.read_pack(); pk = {(x['type'], x['id']): x for x in PK}
        inv = {(t, I(t, x)): (t, x) for (t, x) in pk}
        E2 = DW.read(open(fn, 'rb').read(), 'le')
        others = [k for k, (x, y) in enumerate(zip(DW.read(raw, 'le').sections, E2.sections))
                  if (x.type, x.id) != (y.type, y.id) or ((x.type, x.id) != (8, SID) and (x.data != y.data or x.reloc != y.reloc))]
        targets = [k for k, rr in K['recipes'].items() if rr in ('port', 'new93', 'new')]
        g = GP.gate_sections(E2.sections, pc, PCS, pk, inv, K['recipes'], targets, K)
        g.append(('FAIL ' if others else 'ok   ') + 'every section except 8:%d byte-identical to the input: %s' % (
            SID, others or 'yes'))
        for x in g: print('gate: %s' % x)
        rc = 1 if any(x.startswith('FAIL') for x in g) else 0
        rep = dict(tool='tools/gpda_dlc2_sonar.py apply', input=safe_rel(src), input_md5=md5(raw), mode=mode,
                   out=safe_rel(fn), md5=md5(blob), stats=dict(st), risks=risk, gates=g,
                   info={k: (v if k != 'words' else {'+0x%x' % o: ['%08x' % x for x in ov] for o, ov in v.items()})
                         for k, v in info.items()})
        json.dump(rep, open(os.path.join(out, 'dlc2_sonar_report.json'), 'w'), indent=1)
        if rc: os.remove(fn); print('FAIL: gate - %s removed' % fn); return 1
        print('written %s (%s): md5 %s, %s' % (fn, mode, md5(blob), dict(st)))
        return 0
    sys.exit(__doc__)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
