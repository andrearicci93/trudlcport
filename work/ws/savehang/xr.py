import sys,struct,re,pefile
fn='work/laa/tru_steam.exe.unpacked.exe'
pe=pefile.PE(fn); data=open(fn,'rb').read()
def off2va(o):
    for s in pe.sections:
        if s.PointerToRawData<=o<s.PointerToRawData+s.SizeOfRawData:
            return 0x400000+s.VirtualAddress+o-s.PointerToRawData
for pat in sys.argv[1:]:
    for mm in re.finditer(re.escape(pat.encode()),data):
        va=off2va(mm.start())
        refs=[off2va(x.start()) for x in re.finditer(re.escape(struct.pack('<I',va)),data)]
        print(pat,hex(va),[hex(r) for r in refs if r])
