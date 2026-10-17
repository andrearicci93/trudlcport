"""Scansione lineare di .text: indice delle call dirette (target -> siti) e delle call indirette [reg+disp]. Cache in scan_calls.pkl"""
import pefile,capstone,pickle,os,collections,re
H=os.path.dirname(os.path.abspath(__file__)); C=H+'/scan_calls.pkl'
if os.path.exists(C): direct,indirect=pickle.load(open(C,'rb'))
else:
    pe=pefile.PE('/path/to/trudlcport/work/laa/tru_steam.exe.unpacked.exe'); b=0x400000
    t=pe.get_data(0x1000,0x43d000); md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
    direct=collections.defaultdict(list); indirect=collections.defaultdict(list)
    rx=re.compile(r'\[(\w+)(?: \+ (0x[0-9a-f]+))?\]$')
    for i in md.disasm(t,0x401000):
        if i.mnemonic=='call':
            if i.op_str.startswith('0x'): direct[int(i.op_str,16)].append(i.address)
            else:
                m=rx.search(i.op_str)
                if m and 'dword ptr' in i.op_str: indirect[int(m.group(2),16) if m.group(2) else 0].append((i.address,m.group(1)))
    pickle.dump((dict(direct),dict(indirect)),open(C,'wb'))
if __name__=='__main__':
    import sys
    print('call dirette indicizzate:',len(direct),'indirette per disp:',len(indirect))
