import sys
sys.argv = [sys.argv[0]]
src = open('/path/to/trudlcport/work/ws/giro6/web_calib.py').read().replace('\nmain()\n', '\n')
exec(compile(src, 'web_calib', 'exec'))
mid = 23173
rel, secs = find(mid); s = secs[(10, mid)]
pe = C.entries(s.data, s.reloc, 'le'); prow = {e['slot']: (e['tex'], False) for e in pe}
pl = struct.unpack_from('<4I', s.data, 0x28); STRAND[0] = prow[3][0]
PPm = [np.array(v, np.float32) for v in F10.params(s, 'le')]
fn = C.frame_lib(secs[(9, pl[2])].data)
# dove viene letto c54 / c0 nello slot 0
prog = sm3asm.decode(fn['entries'][fn['slots'][0]]['bc'])
ins = list(prog.instrs())
for n, i in enumerate(ins):
    if any(o.rtype == sm3asm.RT_CONST and not o.isdst and o.num in (0, 54, 104) for o in i.ops): print(n, sm3asm.format(i) if hasattr(sm3asm, 'format') else i.op, [(o.rtype, o.num) for o in i.ops])
print('-----')
for n in range(196, len(ins)): print(n, sm3asm.fmt_instr(ins[n], 'ps'))
