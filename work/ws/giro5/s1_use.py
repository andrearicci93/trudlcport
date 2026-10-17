import sys, io, contextlib
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
with contextlib.redirect_stdout(io.StringIO()):
    import web_eval2 as W
C = W.C; sm3asm = W.sm3asm; tree = W.tree
secs = {(x.type, x.id): x for x in tree['dlc_caverns.drm'].sections}
fn = C.frame_lib(secs[(9, 242)].data)
prog = sm3asm.decode(fn['entries'][fn['slots'][0]]['bc'])
try: txt = sm3asm.format_program(prog, comments=False)
except Exception:
    import sm3dis
    txt = sm3dis.disasm(fn['entries'][fn['slots'][0]]['bc'])
lines = txt.splitlines()
print(len(lines), 'righe')
for i, l in enumerate(lines):
    if 's1' in l.split(',')[-1] or ' s1' in l:
        print('\n'.join('%3d %s' % (j, lines[j]) for j in range(max(0, i - 3), min(len(lines), i + 14)))); break
print('-----')
for i, l in enumerate(lines):
    if l.strip().endswith(', s1'):
        print('\n'.join('%3d %s' % (j, lines[j]) for j in range(max(0, i - 4), min(len(lines), i + 16)))); break
