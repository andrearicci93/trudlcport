import sys; sys.path.insert(0,'/path/to/trudlcport/tools')
from minidump_read import Minidump
import pefile
D=Minidump('/path/to/trudlcport/work/crash/B84_texlife/fmod_B84_light4_crash.dmp')
def h(x): return 'None' if x is None else '%08x'%x
for a,n in [(0x1ae7b8,'ebp salvato'),(0x1ae7bc,'ret 7b92db->582240'),(0x1ae7c0,'[ebp+8]=local_4 passato'),(0x1ae7c4,'arg2 (*param_1)'),(0x1ae7c8,'arg3'),(0x1ae7d0,'local_c'),(0x1ae7d4,'local_8'),(0x1ae7d8,'local_4 (slot S-8)'),(0x1ae7dc,'ret 582200->587002')]:
    print(f'{a:08x} {h(D.u32(a))}  {n}')
sysp=D.u32(0xcc9f80); print('DAT_00cc9f80 (System*) =',h(sysp)); 
if sysp:
    print('  sys+0x9568 =',h(D.u32(sysp+0x9568)), ' (0 => 7bc8da ritorna errore, out=0)')
lc=D.u32(0x1ae7d0); print('local_c =',h(lc), ' uguale a System*?', lc==sysp)
esi=0x180412d0; print('esi (param_1 di 582200) =',h(esi),' [esi]=',h(D.u32(esi)),' DAT_00ccde98=',h(D.u32(0xccde98)),' DAT_00ccde94=',h(D.u32(0xccde94)),' DAT_00ccde91=',h(D.u32(0xccde91)))
# confronto codice: dump vs exe
base=0x400000
ranges=[(0x574940,0x9a),(0x582200,0x70),(0x586db0,0x280),(0x7b9000,0x1000),(0x7c4cd3,0x30),(0x7c4757,0xd9),(0x7bac01,0x1a6),(0x7bc8da,0x16b)]
for name,path in [('unpacked',"work/laa/tru_steam.exe.unpacked.exe"),('8e3800ef',"work/ws/tap/probe_light/tru_tap.exe"),('964f5714',"work/ws/tap/probe_texlife/tru_tap.exe")]:
    pe=pefile.PE('/path/to/trudlcport/'+path)
    tot=0
    for va,n in ranges:
        a=pe.get_data(va-base,n); b=D.read(va,n)
        if b is None: print(name,hex(va),'non nel dump'); continue
        d=sum(1 for x,y in zip(a,b) if x!=y); tot+=d
        if d: print(name,hex(va),'diff',d)
    print(name,'byte diversi exe-vs-dump nei range:',tot)
# exe vs exe
pu=pefile.PE('/path/to/trudlcport/work/laa/tru_steam.exe.unpacked.exe')
for name,path in [('8e3800ef',"work/ws/tap/probe_light/tru_tap.exe"),('964f5714',"work/ws/tap/probe_texlife/tru_tap.exe")]:
    pt=pefile.PE('/path/to/trudlcport/'+path); tot=0
    for va,n in ranges:
        a=pu.get_data(va-base,n);b=pt.get_data(va-base,n); tot+=sum(1 for x,y in zip(a,b) if x!=y)
    print(name,'exe-vs-unpacked nei range (file):',tot)
