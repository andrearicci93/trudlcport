"""Read the game's "last reached checkpoint" state and the checkpoints of every loaded unit from a full-memory crash
dump of the PC tru.exe 1.1 (read-only, Q11 2026-11-17, ENGINE.md section 6.4 "Checkpoint record (Q11)").

What it prints (all addresses are the static PC ones of ENGINE.md section 6):
  - main state [0xe7ed60], streamFlags [0xe7f0b8] (0x80000 = restart request, 0x1000 pause), the in-place flag
    byte [0xe7f1f1], GameTracker+0x38 start unit name (0xe7f0c0), main stream unit id [0xe7f148]
  - the checkpoint record {char unit[128]; u32 checkpoint intro id} in three places: the live game block
    [0xc59264]+0x10 / +0x90, the snapshot game block [0xc59268]+0x10 / +0x90, the player tracker [0xfadb58]+0x648 /
    +0x6c8; plus the alternative record +0x94 / +0x114 and its switch word +0x1f4
  - the object ids of the checkpoint objects (object list [0xdb94d0]: +0 count, name pointer at +8 + 8 i, id i + 1;
    the names the player placement 0x5d40c0 looks up: "checkpoint", "invis_checkpoint")
  - per stream unit slot in state 2 (table 0xdbab40, 32 x 0xd8): every placed intro (unit DTP Level+0x74: +0xc count,
    +0x10 records of 0x90 B; +0x10 position as held in memory after FinishLoad / relocation, +0x50 object id, +0x58
    unique id) whose object is a checkpoint object, its intro index, its instance position (+0x20), the unit's default checkpoint index (environment Level+0x70 -> +0x2b4 -> u16 +8, the fallback of
    0x5d40c0 when the record id is 0), and whether an instance with that id exists (INSTANCE_Find 0x5b3950 rules)

Usage (from the repository root):
  ../bin/pyt -t 600 tools/checkpoint_state_read.py DUMP.dmp [--all-intros] [--sticky KIND:ID:KEY ...] [--log DIR]
        [--verbose] [--debug] [--trace]
  --all-intros  list every intro of the loaded units, not only the checkpoints
  --sticky      an int sticky to read from the live arena and the checkpoint snapshot (save tail), e.g. 0:4318:5968 =
                the played mark of the chapter 3.1 intro; may be given several times
  --log         run log folder (default ../local_results/q11/logs, outside the repository)
Exit code: 0 = read, 1 = a required address is not in the dump, 2 = usage error.
"""
import sys, os, struct, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import minidump_read as MD

LOG = {'level': 0, 'fh': None}
CP_NAMES = ('checkpoint', 'invis_checkpoint')


def log(msg, lvl=0):
    """lvl 0 = always, 1 = verbose, 2 = debug, 3 = trace; the log file gets everything up to debug (trace with --trace)"""
    if lvl <= LOG['level']:
        print(msg, flush=True)
    if LOG['fh'] and (lvl <= 2 or LOG['level'] >= 3):
        LOG['fh'].write(msg + '\n')


class Mem:
    def __init__(self, md):
        self.md = md

    def b(self, va, n):
        return self.md.read(va, n)

    def u8(self, va):
        x = self.b(va, 1)
        return None if x is None else x[0]

    def u16(self, va):
        x = self.b(va, 2)
        return None if x is None else struct.unpack('<H', x)[0]

    def u32(self, va):
        x = self.b(va, 4)
        return None if x is None else struct.unpack('<I', x)[0]

    def f3(self, va):
        x = self.b(va, 12)
        return None if x is None else struct.unpack('<3f', x)

    def cstr(self, va, n=128):
        x = self.b(va, n)
        if x is None:
            return None
        return x.split(b'\0', 1)[0].decode('latin-1')


def record(m, va, idoff):
    name = m.cstr(va)
    cid = m.u32(va + idoff)
    return '%r cp %s' % (name, 'None' if cid is None else '%d (0x%x)' % (cid, cid))


def object_ids(m):
    """{object id: name} of every object in [0xdb94d0] and the ids of the checkpoint objects"""
    tab = m.u32(0xdb94d0)
    if not tab:
        return {}, {}
    n = m.u32(tab) or 0
    names = {}
    for i in range(n):
        p = m.u32(tab + 8 + 8 * i)
        if p:
            s = m.cstr(p, 64)
            if s is not None:
                names[i + 1] = s
    cps = {k: v for k, v in names.items() if v.lower() in CP_NAMES}
    log('object list 0x%08x: %d entries, checkpoint objects %s' % (tab, n, cps), 1)
    return names, cps


def instance_of(m, iid):
    """INSTANCE_Find 0x5b3950: id < 0x4000 -> u16 index [0xd99000 + 2 id], instance = [0xd98f60] + (index - 1) * 0x2f0;
    else the index of the id in the 0x400 dwords at 0xda1000, instance = [0xd98f60] + index * 0x2f0; none when byte
    +0x14 & 0x20"""
    base = m.u32(0xd98f60)
    if base is None:
        return None
    if iid < 0x4000:
        ix = m.u16(0xd99000 + 2 * iid)
        if not ix:
            return 0
        inst = base + (ix - 1) * 0x2f0
    else:
        blob = m.b(0xda1000, 0x1000)
        if blob is None:
            return None
        ids = struct.unpack('<1024I', blob)
        if iid not in ids:
            return 0
        inst = base + ids.index(iid) * 0x2f0
    fl = m.u8(inst + 0x14)
    if fl is None or fl & 0x20:
        return 0
    return inst


def player_objects(m):
    """the object ids the player placement 0x5d40c0 accepts as the player intro: [0xe7f1c4], [0xe7f1c8] and the u16
    list [[0xe7ee50]+4] (+0 u16 count, +4 pointer to the u16 ids)"""
    ids = set()
    for a in (0xe7f1c4, 0xe7f1c8):
        v = m.u32(a)
        if v:
            ids.add(v & 0xffff)
    g = m.u32(0xe7ee50)
    lst = m.u32(g + 4) if g else None
    if lst:
        n, arr = m.u16(lst), m.u32(lst + 4)
        for i in range(n or 0):
            v = m.u16(arr + 2 * i)
            if v is not None:
                ids.add(v)
    log('player objects (0x5d40c0): [0xe7f1c4] %s, [0xe7f1c8] %s, list %s' % (
        m.u32(0xe7f1c4), m.u32(0xe7f1c8), sorted(ids)), 1)
    return ids


def units(m, names, cps, all_intros):
    pobj = player_objects(m)
    for k in range(32):
        e = 0xdbab40 + 0xd8 * k
        uid, st = m.u32(e), m.u8(e + 4)
        if st is None:
            log('stream slot %d: not in the dump' % k)
            continue
        if st == 0:
            continue
        fl = m.u16(e + 6)
        nm = m.cstr(e + 0xc)
        lev = m.u32(e + 8)
        log('slot %2d unit %3d %-32s state %d flags 0x%04x Level 0x%08x' % (k, uid, nm, st, fl, lev or 0))
        if st != 2 or not lev:
            continue
        dtp, env = m.u32(lev + 0x74), m.u32(lev + 0x70)
        org = m.f3(lev + 0x80)
        lflags = m.u32(lev + 0x2c)
        dflt = None
        if env:
            p = m.u32(env + 0x2b4)
            if p:
                dflt = m.u16(p + 8)
        n, arr = m.u32(dtp + 0xc), m.u32(dtp + 0x10)
        log('   Level+0x2c 0x%08x (0x100000 = the checkpoint keeps the old unit name), origin %s, %d intros at '
            '0x%08x, default checkpoint index %s' % (lflags or 0, org, n or 0, arr or 0, dflt))
        nplayer = 0
        for i in range(n or 0):
            r = arr + 0x90 * i
            obj, iid = m.u16(r + 0x50), m.u32(r + 0x58)
            pos = m.f3(r + 0x10)
            iscp = obj in cps
            if obj in pobj or iid == 0xffffffff:
                nplayer += 1
                log('   PL intro[%3d] id %d object %d %s position %s (the player intro; 0x5d40c0 sets its id to -1)' % (
                    i, iid, obj, names.get(obj, '?'), tuple(round(x, 1) for x in pos) if pos else None))
                continue
            if not (iscp or all_intros):
                continue
            inst = instance_of(m, iid) if iid is not None else None
            ipos = m.f3(inst + 0x20) if inst else None
            log('   %s intro[%3d] id %6d object %4d %-24s record position %s instance %s %s%s' % (
                'CP' if iscp else '  ', i, iid, obj, names.get(obj, '?'),
                tuple(round(x, 1) for x in pos) if pos else None,
                'None' if inst is None else ('0x%08x' % inst if inst else '-'),
                'at %s' % (tuple(round(x, 1) for x in ipos),) if ipos else '',
                '  <- default' if dflt == i else ''), 0 if iscp else 1)
        if not nplayer:
            log('   no player intro: a placement into this unit ends in the fatal box "Couldn\'t find a player object.."')


def stickies(m, wanted):
    """int stickies (kind, id, key) in the live SaveInfo arena [0xc59258] and the checkpoint snapshot [0xc5925c] (save
    tail of tools/trusave_diff.py: int values +0x13e1f8 (0x200 x s32), int ids +0x13e9f8 = u32 count + count x {u32 id,
    u16 key, u8 kind, u8 0}); the tail is what SAVE_SaveGame copied, the run-time store is StickyManager [0xa13f18]"""
    for tag, ptr in (('live', 0xc59258), ('snapshot', 0xc5925c)):
        base = m.u32(ptr)
        if not base:
            log('%s arena: no pointer' % tag)
            continue
        n = m.u32(base + 0x13e9f8)
        ids = m.b(base + 0x13e9f8 + 4, 8 * min(n or 0, 0x200))
        if ids is None:
            log('%s arena 0x%08x: int ids not in the dump' % (tag, base))
            continue
        found = {}
        for k in range(len(ids) // 8):
            sid, key, kind, pad = struct.unpack_from('<IHBB', ids, 8 * k)
            if (kind, sid, key) in wanted:
                v = m.b(base + 0x13e1f8 + 4 * k, 4)
                found[(kind, sid, key)] = (k, struct.unpack('<i', v)[0] if v else None)
        for w in wanted:
            log('%-8s arena 0x%08x: int sticky %d:%d key %d -> %s' % (
                tag, base, w[0], w[1], w[2], 'index %d value %s' % found[w] if w in found else 'not stored'))


def main(argv):
    if not argv or argv[0].startswith('-'):
        print(__doc__)
        return 2
    path = argv[0]
    all_intros = '--all-intros' in argv
    LOG['level'] = 3 if '--trace' in argv else 2 if '--debug' in argv else 1 if '--verbose' in argv else 0
    logdir = os.path.join(HERE, '..', '..', 'local_results', 'q11', 'logs')
    if '--log' in argv:
        logdir = argv[argv.index('--log') + 1]
    os.makedirs(logdir, exist_ok=True)
    LOG['fh'] = open(os.path.join(logdir, 'checkpoint_state_read_%s.log' % time.strftime('%Y%m%d_%H%M%S')), 'w',
                     encoding='utf-8')
    t0 = time.time()
    log('# checkpoint_state_read %s' % os.path.basename(path))
    m = Mem(MD.Minidump(path))
    need = [0xe7ed60, 0xc59264, 0xc59268, 0xfadb58, 0xdbab40]
    miss = [a for a in need if m.u32(a) is None]
    if miss:
        log('not in the dump: %s' % ', '.join('0x%x' % a for a in miss))
        return 1
    log('main state %d, streamFlags 0x%08x, [0xe7f1f1] %d, GameTracker+0x38 %r, main unit id %d, '
        'level change pending %d' % (m.u32(0xe7ed60), m.u32(0xe7f0b8), m.u8(0xe7f1f1), m.cstr(0xe7f0c0),
                                     m.u32(0xe7f148), m.u8(0xe7f141)))
    live, snap = m.u32(0xc59264), m.u32(0xc59268)
    for tag, gb in (('live', live), ('snapshot', snap)):
        log('%-8s game block 0x%08x: version 0x%04x, record %s, +0x1f4 %d, alternative +0x94 %s, chapter +0x1f2 %d'
            % (tag, gb, m.u16(gb + 0xa), record(m, gb + 0x10, 0x80), m.u16(gb + 0x1f4), record(m, gb + 0x94, 0x80),
               m.u16(gb + 0x1f2)))
    p = m.u32(0xfadb58)
    log('player tracker 0x%08x: record +0x648 %s' % (p, record(m, p + 0x648, 0x80) if p else '-'))
    pl = m.u32(0xe7f094)
    if pl:
        pp = m.f3(pl + 0x20)
        log('player instance 0x%08x at %s, stream unit +0xe0 %s' % (
            pl, tuple(round(x, 1) for x in pp) if pp else None, m.u32(pl + 0xe0)))
    names, cps = object_ids(m)
    log('checkpoint objects: %s' % ', '.join('%d %s' % kv for kv in sorted(cps.items())))
    units(m, names, cps, all_intros)
    wanted = []
    k = 0
    while '--sticky' in argv[k:]:
        k = argv.index('--sticky', k) + 1
        kind, sid, key = (int(x, 0) for x in argv[k].split(':'))
        wanted.append((kind, sid, key))
    if wanted:
        stickies(m, wanted)
    log('# done in %.1f s' % (time.time() - t0), 1)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
