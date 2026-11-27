"""raggi di collisione (0x493330) dalla posizione di Lara in un dump; stampa tipo, oggetto, punto, e gruppo/faccia del terreno.
uso: python emu_ray.py DUMP [maschera_hex]"""
import sys, math
sys.argv = [sys.argv[0], sys.argv[1]] + sys.argv[2:]
exec(open('emu_base.py', encoding='utf-8').read())
MASK = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x3c19e7
PT = []; HIT = {}
def h_t(uc, a, s_, u): PT.append(r32(uc.reg_read(UC_X86_REG_ESP) + 4))
def h_tr(uc, a, s_, u):
    if PT:
        o2 = PT.pop()
        if uc.reg_read(UC_X86_REG_EAX) & 0xff: HIT['t'] = (r32(o2 + 0x28), r32(o2 + 0x2c), rf(o2, 3))
mu.hook_add(UC_HOOK_CODE, h_t, begin=0x4e8fc0, end=0x4e8fc0); mu.hook_add(UC_HOOK_CODE, h_tr, begin=0x4933f9, end=0x4933f9)
Lp = rf(L + 0x20, 3)
for dz in (100, 250):
    for ang in range(0, 360, 15):
        HIT.clear()
        fr = (Lp[0], Lp[1], Lp[2] + dz); to = (fr[0] + 3000 * math.cos(math.radians(ang)), fr[1] + 3000 * math.sin(math.radians(ang)), fr[2])
        try: t, ob, p = call_ray(fr, to, MASK)
        except UcError as e: print(ang, 'errore', e, hex(mu.reg_read(UC_X86_REG_EIP))); continue
        d = math.dist(fr, p) if t else 0
        print('z+%d %3d  tipo %d dist %6.0f ogg %8x punto %s terreno %s' % (dz, ang, t, d, ob, ['%.0f' % v for v in p] if t else '', ('gruppo %x faccia %x' % HIT['t'][:2]) if 't' in HIT else ''))
