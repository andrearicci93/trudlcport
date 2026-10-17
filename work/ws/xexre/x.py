import sys,struct
from capstone import *
PE='/path/to/trudlcport/work/ws/xex/default.pe'
D=open(PE,'rb').read()
BASE=0x82000000
md=Cs(CS_ARCH_PPC,CS_MODE_32|CS_MODE_BIG_ENDIAN)
def u32(va): return struct.unpack('>I',D[va-BASE:va-BASE+4])[0]
def dis(va,n=40,show=True):
    out=[]
    for i in md.disasm(D[va-BASE:va-BASE+4*n],va):
        out.append("%08x  %s %s"%(i.address,i.mnemonic,i.op_str))
    return out
def find_hi_lo(target,lo=0x820A0000,hi=0x826B4C5C,win=40):
    h=(target+0x8000)>>16 &0xffff; l=target&0xffff
    res=[]
    for va in range(lo,hi,4):
        w=u32(va)
        # lis rD,imm = addis rD,0,imm : opcode 15, ra=0
        if w>>26==15 and ((w>>16)&31)==0 and (w&0xffff)==h:
            rd=(w>>21)&31
            for k in range(1,win):
                w2=u32(va+4*k)
                if (w2>>26 in (14,24)) and ((w2>>16)&31)==rd and (w2&0xffff)==l:
                    res.append((va,va+4*k));break
    return res
if __name__=='__main__':
    print([(hex(a),hex(b)) for a,b in find_hi_lo(int(sys.argv[1],16))])
def func_start(va):
    # .pdata: entries (begin, info) at 0x8207E800..0x8209A610 sorted
    import bisect
    global _pd
    try: _pd
    except NameError:
        _pd=[]
        for a in range(0x8207E800,0x8209A610,8):
            b=u32(a)
            if b: _pd.append((b,u32(a+4)))
    i=bisect.bisect_right([p[0] for p in _pd],va)-1
    b,inf=_pd[i]
    return b,(inf>>8)&0x3fffff
def callers(target,lo=0x820A0000,hi=0x826B4C5C):
    r=[]
    for va in range(lo,hi,4):
        w=u32(va)
        if w>>26==18 and (w&3)==1:
            off=w&0x03fffffc
            if off&0x2000000: off-=0x4000000
            if (va+off)&0xffffffff==target: r.append(va)
    return r
def ptr_refs(target):
    return [a for a in range(0x82000600,0x83210000,4) if u32(a)==target]
def mem_refs(addr,lo=0x820A0000,hi=0x826B4C5C):
    """loads/stores d(rX) whose rX was set by lis in the previous 12 instrs to hi part"""
    h=((addr+0x8000)>>16)&0xffff; l=addr&0xffff
    res=[]
    for va in range(lo,hi,4):
        w=u32(va)
        if (w>>26) in (32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,12,14,24) and (w&0xffff)==l:
            ra=(w>>16)&31
            for k in range(1,14):
                w2=u32(va-4*k)
                if w2>>26==15 and ((w2>>21)&31)==ra and (w2&0xffff)==h and ((w2>>16)&31)==0:
                    res.append((va,w>>26));break
    return res
