import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst/xbox_map')
from ppcdis import *
def ctx(a, before=14, after=6):
    s = a - 4 * before
    for i in md.disasm(img[s - BASE:a + 4 * after - BASE], s):
        print('%s%08x  %-8s %s' % ('>>' if i.address == a else '  ', i.address, i.mnemonic, i.op_str))
for x in sys.argv[1:]:
    print('----', nm(int(x, 16)) if int(x,16) in by_addr else '', x); ctx(int(x, 16))
