"""Re-run tools/param_auto.py's scan with ONE change: the microcode extraction of tools/xenos_ps.py is replaced by the container-authoritative one
(code = blob[virtualSize + Shader.physicalOffset : +Shader.size]).  Reason (found by xenos_xlat.py): xenos_ps.microcode() assumes an 8-byte
trailer after the code; shaderlib.parse() leaves the 8-byte header of the NEXT lib entry at the end of every entry except the last one of a lib,
so for the LAST entry of every lib (1445/2890 base PS blobs; 124 of the 248 DLC1 non-A/B PS blobs) the microcode is shifted by 8 bytes.
No tools/ file is modified: the replacement is a runtime monkeypatch.  Output: out/scan_fixed.json, out/scan_fixed.tsv, comparison vs work/ws/mat/out/scan.json.
usage: tools/venv/bin/python -I work/ws/xenos/rerun_param_auto_fixed.py"""
import sys, os, json, struct, collections, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools')); sys.path.insert(0, HERE)
import xenos_ps as XP
import xenos_xlat as XX

def microcode_fixed(blob):
    sh = XX.parse(blob)
    return sh.code
XP.microcode = microcode_fixed
MODE = sys.argv[1] if len(sys.argv) > 1 else 'mc+sel3'
if 'sel3' in MODE:
    _af = XP.alu_fields
    def alu_fields_fixed(d0, d1, d2):
        f = _af(d0, d1, d2)
        # mulsc/addsc/subsc: src3 is ALWAYS a float constant; bit src3Select is part of the temp-register index of the second operand
        if f['sopc'] in XP.SOP_CONST and XP.VOP_OPERANDS.get(f['vopc'], 0) < 3: f['sel3'] = 0
        return f
    XP.alu_fields = alu_fields_fixed
if 'mc' not in MODE: XP.microcode = XP.microcode.__class__ and __import__('xenos_ps').microcode
import param_auto as PA
PA._PAIR.clear()
out = os.path.join(HERE, 'out', 'scan_fixed')
rows = PA.scan(out)
old = {r['mid']: r for r in json.load(open(os.path.join(ROOT, 'work/ws/mat/out/scan.json')))}
print('new verdicts (all 587):', collections.Counter(r['verdict'] for r in rows))
print('old verdicts (all 587):', collections.Counter(r['verdict'] for r in old.values()))
d1 = [r for r in rows if r['dlc1']]
print('DLC1 new:', sorted(collections.Counter(r['verdict'] for r in d1).items()))
print('DLC1 old:', sorted(collections.Counter(old[r['mid']]['verdict'] for r in d1).items()))
SAFE = {'EXACT', 'IDENTITY-VERIFIED', 'PROVEN-MAP'}
print('DLC1 unresolved (not EXACT/IDENTITY-VERIFIED/PROVEN-MAP): old', sum(1 for r in d1 if old[r['mid']]['verdict'] not in SAFE), 'new', sum(1 for r in d1 if r['verdict'] not in SAFE))
chg = collections.Counter((old[r['mid']]['verdict'], r['verdict']) for r in rows if old[r['mid']]['verdict'] != r['verdict'])
print('transitions old->new:'); [print('   %-28s -> %-28s %d' % (a, b, n)) for (a, b), n in sorted(chg.items())]
# pass-level
po = collections.Counter(); pn = collections.Counter()
for r in rows:
    for p in old[r['mid']]['passes']: po[p[4]] += 1
    for p in r['passes']: pn[p[4]] += 1
print('pass level old', dict(po)); print('pass level new', dict(pn))
