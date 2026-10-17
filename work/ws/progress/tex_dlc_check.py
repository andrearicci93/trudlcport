"""tex_dlc_check.py - per ogni texture (tipo 5) dei DRM DLC: rigenera da Xbox con tex_convert.convert e confronta con quella installata.
Uso: python -I work/ws/progress/tex_dlc_check.py <setdir rel. work>"""
import sys, os, collections, traceback
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import tex_convert as T, dtp_audit as DA, drm_write as DW
sd = sys.argv[1]
tot = collections.Counter(); bad = []; fmts = collections.Counter(); per_file = collections.defaultdict(collections.Counter)
for rel, path in sorted(DA.overlay([sd], None).items()):
    xs = DA.xsecs(rel)
    if xs is None: continue
    try: D = DW.read(open(path, 'rb').read(), 'le')
    except Exception: continue
    for x, i in DA.section_pairs(xs, D):
        if x['type'] != 5: continue
        sec = D.sections[i]; pd = bytes(sec.data); xd = bytes(x['data'])
        tot['tot'] += 1; per_file[rel]['tot'] += 1
        try:
            xh = T.parse_xbox(xd); ph = T.parse_pc(pd)
            fmts[(xh['fmtname'], T.pc_kind(ph['fmt']) if ph['fmt'] in (0x15, *T.FOURCC.values()) else hex(ph['fmt']))] += 1
            _, _, need = T.xbox_levels(xd)
            if need != len(xd) - 24: tot['xbox_size_anomalo'] += 1; bad.append((rel, sec.id, 'xbox_size', len(xd) - 24, need)); per_file[rel]['bad'] += 1; continue
            out = T.convert(xd)
        except Exception as e:
            tot['errore'] += 1; bad.append((rel, sec.id, 'errore', repr(e)[:80])); per_file[rel]['bad'] += 1; continue
        if out == pd: tot['esatta'] += 1
        else:
            tot['diversa'] += 1; per_file[rel]['bad'] += 1
            bad.append((rel, sec.id, 'diversa', len(out), len(pd), (xh['w'], xh['h'], xh['mips']), (ph['w'], ph['h'], ph['mips']), xh['fmtname']))
print('TOTALE', dict(tot))
print('formati (xbox -> pc):', dict(fmts.most_common(10)))
bf = sorted(((v['bad'], k) for k, v in per_file.items() if v['bad']), reverse=True)
print('file con texture non esatte:', len(bf))
for n, f in bf[:15]: print('  %4d/%d %s' % (n, per_file[f]['tot'], f))
for b in bad[:25]: print('  ', b)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex_dlc_check_%s.txt' % os.path.basename(os.path.dirname(sd.rstrip('/')))), 'w').write('\n'.join(map(str, bad)))
