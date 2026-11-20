"""Walk the state records of a player state chart DTP: which chart state owns a transition, where it leads and what
the following states hold (read-only; wall run 2026-11-01: owner / target / following states of the {610, 610, 608}
transitions of doppelganger_casual DTP 20212, why TU state 245 is never entered on PC).

State record (0x28 bytes, layout: tools/state_actlist_fix.py): 10 u16 header (+0 id, +6 parent index (s16), +0x0a
activity count, +0x0c state-id count, +0x0e transition count, +0x10 count of the +0x20 list), pointers +0x14 activities
(8-byte entries {u16 id, u16 type, 4 value bytes}), +0x18 u16 state ids, +0x1c u16 transition indices (into the
machine's transition pointer array), +0x20 u16 list.
Transition = 20-byte block {u16 target, u16 kind count, u16 condition count, u16, ptr u16 kind list, ptr conditions,
u32} as the PC machine reads it (0x787570 / 0x785920, A1 2026-11-20): kind 1 = the transition waits until
machine+0x24 == 1, kind 7 = it waits while byte machine+0x53c != 0 (kept in machine+0x514 meanwhile). Without kinds
both pointers are equal; before 2026-11-20 this tool read the conditions from +8, which for transitions with kinds
printed the kind list as "{7,0,0} {0,0,0}" and dropped the last conditions.
condition = 8 bytes {u16 key, u16 id, u16 value, u8 flags (bit 0 NOT), u8}.

Usage (from the repository root):
  ../bin/pyt -t 300 tools/chart_state_path.py DRM ENDIAN SID info
  ../bin/pyt -t 300 tools/chart_state_path.py DRM ENDIAN SID owners VALUE[,VALUE..]   states whose transitions test
        a markup value (record {610|611|612|613, *, VALUE})
  ../bin/pyt -t 300 tools/chart_state_path.py DRM ENDIAN SID state IDX|@OFFSET [--depth N]   one state record (by record
        index or file offset) with activities, state ids, transitions; --depth follows the transition targets
  ../bin/pyt -t 300 tools/chart_state_path.py DRM ENDIAN SID into TARGET[,TARGET..]   states holding transitions to TARGET
  ../bin/pyt -t 300 tools/chart_state_path.py DRM ENDIAN SID sid ID[,ID..]   records whose +0x18 list holds a state id
ENDIAN: be (Xbox original) or le (PC file).
"""
import sys, os, struct, bisect, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
import state_translist_fix as ST
import state_actlist_fix as SA


class Chart:
    def __init__(self, path, e, sid):
        _, s = ST.load(path, e, sid)
        self.f = '>' if e == 'be' else '<'
        self.d = bytes(s.data)
        self.it = dict(R.parse(bytes(s.reloc), e).internal)
        self.recs = SA.records(s, e)
        self.recs.sort()
        self.byoff = {r[0]: k for k, r in enumerate(self.recs)}
        # transition pointer array: the block whose consecutive pointers all go to 0x14-byte transition blocks
        t = sorted(set(self.it.values()) | {0})
        self.tblocks = set()
        for k, a in enumerate(t):
            end = t[k + 1] if k + 1 < len(t) else len(self.d)
            if end - a == 0x14 and (a + 8) in self.it and (a + 0xc) in self.it: self.tblocks.add(a)
        cnt = collections.Counter()
        for o, x in self.it.items():
            if x in self.tblocks:
                kb = bisect.bisect_right(t, o) - 1
                cnt[t[kb]] += 1
        self.tarr = cnt.most_common(1)[0][0] if cnt else None
        self.tlist = []
        if self.tarr is not None:
            o = self.tarr
            while o in self.it and self.it[o] in self.tblocks:
                self.tlist.append(self.it[o]); o += 4
        # record array: the pointer array [machine+4]+0xc is not in the DTP; parent index = position among records?
        self.recarr = None
        rset = set(r[0] for r in self.recs)
        cnt2 = collections.Counter()
        for o, x in self.it.items():
            if x in rset:
                kb = bisect.bisect_right(t, o) - 1
                cnt2[t[kb]] += 1
        if cnt2:
            a = cnt2.most_common(1)[0][0]; lst = []; o = a
            while o in self.it and self.it[o] in rset:
                lst.append(self.it[o]); o += 4
            self.recarr = (a, lst)

    def u16(self, o): return struct.unpack_from(self.f + 'H', self.d, o)[0]

    def trans(self, idx):
        a = self.tlist[idx]
        tg, w1, cnt, w3 = struct.unpack_from(self.f + '4H', self.d, a)
        c0 = self.it.get(a + 0xc, self.it.get(a + 8))
        conds = []
        for j in range(min(cnt, 24)):
            ky, i, v = struct.unpack_from(self.f + '3H', self.d, c0 + 8 * j)
            conds.append((ky, i, v, self.d[c0 + 8 * j + 6]))
        return a, tg, w1, cnt, w3, conds

    def kinds(self, idx):
        """u16 kind list of a transition (+8, count +2): 1 = wait for machine+0x24 == 1, 7 = wait for machine+0x53c == 0."""
        a = self.tlist[idx]
        n = struct.unpack_from(self.f + 'H', self.d, a + 2)[0]
        p = self.it.get(a + 8)
        if not n or p is None:
            return []
        return [struct.unpack_from(self.f + 'H', self.d, p + 2 * j)[0] for j in range(n)]

    def state(self, k):
        r, sid, hdr, p14, p18, p1c, p20 = self.recs[k]
        acts = []
        for j in range(hdr[5]):
            i, ty = struct.unpack_from(self.f + '2H', self.d, p14 + 8 * j)
            acts.append((i, ty, self.d[p14 + 8 * j + 4:p14 + 8 * j + 8]))
        sids = [self.u16(p18 + 2 * j) for j in range(hdr[6])]
        tr = [self.u16(p1c + 2 * j) for j in range(hdr[7])]
        l20 = [self.u16(p20 + 2 * j) for j in range(hdr[8])]
        return r, hdr, acts, sids, tr, l20

    def rec_index(self, r):
        if self.recarr and r in self.recarr[1]: return self.recarr[1].index(r)
        return None


def fmt_conds(conds):
    return ' '.join('{%d,%d,%d%s}' % (c[0], c[1], c[2], ',NOT' if c[3] & 1 else '') for c in conds)


def fmt_val(f, ty, v):
    u = struct.unpack(f + 'I', v)[0]
    fl = struct.unpack(f + 'f', v)[0]
    if ty in (2, 0x2a): return 'b%s' % v.hex()
    if 1e-4 < abs(fl) < 1e7: return '%g' % fl
    return '0x%x' % u


def show(C, k, depth, seen, indent=''):
    r, hdr, acts, sids, tr, l20 = C.state(k)
    ri = C.rec_index(r)
    print('%sstate rec #%d (array idx %s) +0x%05x id %d parent %d hdr %s' % (
        indent, k, ri, r, hdr[0], struct.unpack('h', struct.pack('H', hdr[3]))[0], ' '.join('%d' % h for h in hdr)))
    print('%s  state ids (+0x18): %s' % (indent, sids))
    print('%s  activities (+0x14): %s' % (indent, ' '.join('%d/t%d=%s' % (i, ty, fmt_val(C.f, ty, v)) for i, ty, v in acts)))
    if l20: print('%s  +0x20 list: %s' % (indent, l20))
    nxt = []
    for ti in tr:
        if ti >= len(C.tlist):
            print('%s  trans %d: OUT OF RANGE' % (indent, ti)); continue
        a, tg, w1, cnt, w3, conds = C.trans(ti)
        print('%s  trans slot %4d +0x%05x -> %5d (w1 %d, w3 %d): %s%s' % (indent, ti, a, tg, w1, w3,
              'kinds %s ' % C.kinds(ti) if w1 else '', fmt_conds(conds)))
        nxt.append(tg)
    if depth > 0:
        for tg in nxt:
            for kk in targets(C, tg):
                if kk in seen: continue
                seen.add(kk)
                show(C, kk, depth - 1, seen, indent + '    ')


def targets(C, tg):
    """record number of a transition target = index into the record pointer array (record ids are mostly 65535 in
    DTP 20212 and repeat, so a target cannot be a record id; the parent field +6 is the same kind of index)"""
    out = []
    if C.recarr and tg < len(C.recarr[1]):
        k = C.byoff.get(C.recarr[1][tg])
        if k is not None and k not in out: out.append(k)
    return out


def main(argv):
    depth = 0
    if '--depth' in argv: k = argv.index('--depth'); depth = int(argv[k + 1]); del argv[k:k + 2]
    C = Chart(argv[0], argv[1], int(argv[2]))
    mode = argv[3]
    if mode == 'info':
        ids = collections.Counter(rr[2][0] for rr in C.recs)
        print('%d state records, %d distinct ids (min %d max %d), %d transitions in the array at +0x%x' % (
            len(C.recs), len(ids), min(ids), max(ids), len(C.tlist), C.tarr or 0))
        if C.recarr: print('record pointer array at +0x%x: %d entries' % (C.recarr[0], len(C.recarr[1])))
        print('ids used more than once: %s' % [(i, n) for i, n in ids.most_common(10) if n > 1])
        for k in range(min(12, len(C.recs))):
            r, hdr, acts, sids, tr, l20 = C.state(k)
            print('  #%d +0x%05x arr %s id %d parent %d sids %s ntr %d' % (k, r, C.rec_index(r), hdr[0],
                  struct.unpack('h', struct.pack('H', hdr[3]))[0], sids[:6], len(tr)))
        return
    if mode == 'owners':
        vals = set(int(x) for x in argv[4].split(','))
        for k in range(len(C.recs)):
            r, hdr, acts, sids, tr, l20 = C.state(k)
            for ti in tr:
                if ti >= len(C.tlist): continue
                a, tg, w1, cnt, w3, conds = C.trans(ti)
                if any(c[1] in (610, 611, 612, 613) and c[2] in vals for c in conds):
                    print('rec #%d +0x%05x id %d sids %s: slot %d -> %d %s' % (k, r, hdr[0], sids, ti, tg, fmt_conds(conds)))
        return
    if mode == 'into':
        tgs = set(int(x) for x in argv[4].split(','))
        for k in range(len(C.recs)):
            r, hdr, acts, sids, tr, l20 = C.state(k)
            for ti in tr:
                if ti >= len(C.tlist): continue
                a, tg, w1, cnt, w3, conds = C.trans(ti)
                if tg in tgs:
                    print('rec #%d +0x%05x id %d sids %s: slot %d -> %d %s' % (k, r, hdr[0], sids, ti, tg, fmt_conds(conds)))
        return
    if mode == 'sid':
        ids = set(int(x) for x in argv[4].split(','))
        for k in range(len(C.recs)):
            r, hdr, acts, sids, tr, l20 = C.state(k)
            if ids & set(sids):
                print('rec #%d +0x%05x id %d parent %d sids %s acts %s ntr %d' % (k, r, hdr[0],
                      struct.unpack('h', struct.pack('H', hdr[3]))[0], sids,
                      ' '.join('%d/t%d=%s' % (i, ty, fmt_val(C.f, ty, v)) for i, ty, v in acts[:12]), len(tr)))
        return
    if mode == 'range':
        # range FROM TO: one block per record-array index (compact)
        for ai in range(int(argv[4]), int(argv[5]) + 1):
            k = C.byoff[C.recarr[1][ai]]
            r, hdr, acts, sids, tr, l20 = C.state(k)
            p = struct.unpack('h', struct.pack('H', hdr[3]))[0]
            print('%d (+0x%05x) parent %d sids %s acts %s' % (ai, r, p, sids,
                  ' '.join('%d/t%d=%s' % (i, ty, fmt_val(C.f, ty, v)) for i, ty, v in acts)))
            for ti in tr:
                a, tg, w1, cnt, w3, conds = C.trans(ti)
                print('      -> %d [slot %d%s] %s' % (tg, ti, ', kinds %s' % C.kinds(ti) if w1 else '', fmt_conds(conds)))
        return
    if mode == 'children':
        par = set(int(x) for x in argv[4].split(','))
        for k in range(len(C.recs)):
            r, hdr, acts, sids, tr, l20 = C.state(k)
            p = struct.unpack('h', struct.pack('H', hdr[3]))[0]
            if p in par:
                print('rec #%d +0x%05x parent %d sids %s acts %s ntr %d' % (k, r, p, sids,
                      ' '.join('%d/t%d=%s' % (i, ty, fmt_val(C.f, ty, v)) for i, ty, v in acts[:12]), len(tr)))
        return
    if mode == 'state':
        a = argv[4]
        if a.startswith('@'): k = C.byoff[int(a[1:], 16)]
        elif a.startswith('a'): k = C.byoff[C.recarr[1][int(a[1:])]]   # by record-array index (= transition target)
        else: k = int(a)
        show(C, k, depth, {k})
        return
    raise SystemExit(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
