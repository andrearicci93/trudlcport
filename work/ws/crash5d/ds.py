import sys; sys.path.insert(0,'/path/to/trudlcport/work/ws/crashdungeon')
from cdis import rd, md
def dis(a,n):
    for i in md.disasm(rd(a,n),a): print(hex(i.address),i.mnemonic,i.op_str)
if __name__=='__main__': dis(int(sys.argv[1],16),int(sys.argv[2],16))
