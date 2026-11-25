"""anim_cmp.py - (20/11/2026) solo lettura. Animazioni tipo 2 di un DRM DLC: decodifica Xbox (BE) e PC (LE) con il layout di
tools/convert_generic.conv_anim e confronta testata, maschere, segmenti e valori float/u8. uso: anim_cmp.py BASELINE FILE.drm"""
import sys, struct
sys.path.insert(0, '/path/to/trudlcport/work/ws/lukas_check/inv'); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW
BL, F = sys.argv[1:3]
P = DW.read(open('/path/to/trudlcport/work/baseline/%s/mods/%s' % (BL, F), 'rb').read(), 'le'); X = DW.read(C.xbox(F), 'be')
def dec(d, e):
    E = '>' if e == 'be' else '<'; n = len(d); h = struct.unpack_from(E + '12f', d, 0)
    aid, kc, tpk = struct.unpack_from(E + 'HHH', d, 0x30); seg = d[0x36]; ml = struct.unpack_from(E + 'I', d, 0x44)[0]
    pos = min(0x44 + ml, n); mask = bytes(d[0x48:pos]); segs = []
    while pos + 4 <= n:
        t, c = struct.unpack_from(E + 'HH', d, pos); pos += 4
        if t == 0: segs.append(('k', struct.unpack_from(E + '%df' % kc, d, pos))); pos += 4 * kc
        elif t == 1: segs.append(('c', struct.unpack_from(E + 'f', d, pos))); pos += 4
        elif t == 2:
            nb = max(c - 1, 0); tb = bytes(d[pos:pos + nb]); pos += (nb + 3) // 4 * 4
            segs.append(('t', tb, struct.unpack_from(E + '%df' % c, d, pos))); pos += 4 * c
        elif t >= 0x8000: segs.append(('x', t, c))
        else: segs.append(('?', t, c)); break
    return dict(h=h, aid=aid, kc=kc, tpk=tpk, seg=seg, mask=mask, segs=segs, end=pos == n)
bad = 0
for x in X.sections:
    if x.type != 2: continue
    ps = [s for s in P.sections if s.type == 2 and len(s.data) == len(x.data)]
    p = [s for s in ps if s.id == x.id] or ps
    if not p: print('anim', x.id, 'senza coppia'); continue
    a, b = dec(bytes(x.data), 'be'), dec(bytes(p[0].data), 'le')
    diffs = [k for k in ('kc', 'tpk', 'seg', 'mask', 'end') if a[k] != b[k]]
    if a['h'] != b['h']: diffs.append('testata')
    if len(a['segs']) != len(b['segs']): diffs.append('nseg %d/%d' % (len(a['segs']), len(b['segs'])))
    else:
        for i, (s, t) in enumerate(zip(a['segs'], b['segs'])):
            if s != t: diffs.append('seg%d %s' % (i, s[0]))
    if diffs: bad += 1
    print('anim X %d PC %d %dB keys %d segs %d: %s' % (x.id, p[0].id, len(x.data), a['kc'], len(a['segs']), ', '.join(diffs[:8]) or 'uguale'))
print('anim diverse', bad)
