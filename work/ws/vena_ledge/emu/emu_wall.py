import sys, math
exec(open('emu_base.py', encoding='utf-8').read())
grid = {}
for z in range(-16500, -9000, 500):
    row = ''
    for x in range(-5500, 1000, 250):
        try: t, ob, p = call_ray((x, 6500, z), (x, 2500, z))
        except UcError: row += '?'; continue
        row += ('#' if abs(p[1] - 4825) < 30 else ('o' if p[1] > 4000 else '.')) if t else ' '
        grid[(x, z)] = p[1] if t else None
    print('z %6d |%s|' % (z, row))
print('x da -5500 a 1000 passo 250; # = piano y 4825, o = altro y>4000, . = colpo piu lontano')
