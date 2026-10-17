"""Validate dlc_generic.script_rebase on base pairs: every base Script whose super chain has a PC size delta is converted with
the Script walker (as a DLC-new script would be), then rebased with the chain of its SUPER, and compared with the real PC
section (same length only).  Prints exact counts and remaining wrong labels."""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlc_generic as DG, generic_store, drm_reloc as R, script_conv as S
st = generic_store.load(); ids = DG.DlcIds(st, None); SL = DG._SL()
c = collections.Counter(); wrong = collections.Counter()
for (t, x), xb in st['xb_store'].items():
    if t != 8 or len(xb['data']) < 0x54: continue
    sup = struct.unpack_from('>I', xb['data'], 0x18)[0]
    sh = DG.script_layout_shift(sup, [], st, ids)
    if not sh: continue
    pc = st['pc_store'].get((8, ids.base[8].get(x)))
    if pc is None or len(pc['data']) != len(xb['data']): c['skip_len'] += 1; continue
    rel = R.parse(xb['reloc'], 'be'); W = S.walk(xb['data'], rel)
    out, _ = SL.convert(xb['data'], rel, ids, SL.table(), W=W); out = bytearray(out)
    before = sum(out[w:w + 4] != pc['data'][w:w + 4] for w in range(0, len(out) // 4 * 4, 4))
    n = DG.script_rebase(xb['data'], rel, out, sh, W)
    bad = [w for w in range(0, len(out) // 4 * 4, 4) if out[w:w + 4] != pc['data'][w:w + 4]]
    for w in bad: wrong[W.lab.get(w, ('unk',))[:2]] += 1
    c['scripts'] += 1; c['words_changed'] += n; c['wrong_before'] += before; c['wrong_after'] += len(bad)
    if not [w for w in bad if W.lab.get(w, ('unk',))[0] != 'dep']: c['exact_mod_deps'] += 1
print(dict(c)); print('remaining wrong labels', wrong.most_common(10))
