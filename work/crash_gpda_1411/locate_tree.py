"""Read-only: find a memory block of a crash dump (cdb .writemem) in the sections of every DRM listed in a file.
Usage (repo root): ../bin/pyt -t 1800 work/crash_gpda_1411/locate_tree.py MEM.bin BASE_HEX ADDR_HEX LEN_HEX LIST.txt"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
import drm_write as DW


def main(argv):
    mem = open(argv[0], 'rb').read()
    base, addr, ln = int(argv[1], 16), int(argv[2], 16), int(argv[3], 16)
    pat = mem[addr - base:addr - base + ln]
    print('pattern %s' % pat.hex())
    for f in open(argv[4], encoding='utf-8').read().split('\n'):
        f = f.strip()
        if not f: continue
        try: S = DW.read(open(f, 'rb').read(), 'le').sections
        except Exception as e: print('skip %s: %s' % (f, e)); continue
        for s in S:
            o = s.data.find(pat)
            while o >= 0:
                print('%s: type %d id %d size 0x%x match +0x%x -> section start 0x%x' % (f, s.type, s.id, len(s.data), o, addr - o))
                o = s.data.find(pat, o + 1)


if __name__ == '__main__':
    main(sys.argv[1:])
