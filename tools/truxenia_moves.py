"""TruXenia move log (B3, 2026-11-20): the Xbox side of TruMenu 0.22.65 .. 0.22.68's [Perch] / [Vein] / [Tempo] /
[Jump] / [Press] lines, read from a running Xenia (TU exe) - the same place played in Xenia and on the PC, the two logs
laid side by side with tools/compare_pc_xenia_logs.py.

Read only (ReadProcessMemory through tools/xenia_combat_sampler.py, like the rest of TruXenia). Addresses and their TU
proof words: docs/data/xenia_tu_combat_addresses.json sections move_machine, move_tracker, move_markup, move_input,
move_time (all "optional": a mismatch turns that section's values into '?', or switches the lines that need it off).
Line format = TruMenu's (time stamp "YYYY-MM-DD HH:MM:SS.mmm", then the tag and the same field names); a field the
Xbox side cannot read is '?' (pad stick / raw A: Xenia's pad is host side; HUD fraction, inst+0x2a0, item id, line
point count: no TU reader found). Differences to the PC that are not values:
  - "frame" = a CHANGED sample: TruXenia polls (default every 5 ms) and drops a sample whose tracker, machine and Lara
    blocks are byte-equal to the last one, so one logged step is one game frame when the poll is faster than the game
    (Xenia ~30 fps, unproven). Lines say "in one sample" / "sample(s)" where TruMenu says "frame".
  - [Jump] has no launch hook: "launch" = T+0xa20 written with a new value (TU launch reads it, 0x8242b010) outside a
    flight; inside a flight a new T+0xa20 is a re-aim. Flight end = z still for 0.3 s (heuristic, says so).
  - [Vein] V2 "power" is condition 1046 itself (TU 0x8246e400: doppelganger byte -> meter flags bit 0, else CM+0x1fc
    bit 21), TruMenu has the meter flag as a stand-in.
  - Villa switch (+32 / bit 0x200 / target node): not on the Xbox side (script object and node layout of the TU not
    proven) - see docs/TRUXENIA.md section "Move log".

Usage: through tools/truxenia.py --movelog [PATH] [--movelog-seconds N] [--movelog-interval S], or
  ../bin/pyt -t 120 tools/truxenia_moves.py --selftest     offline: simulated TU memory, every line kind checked
"""
import argparse
import math
import os
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xenia_combat_sampler as S  # noqa: E402

MOVE_SECTIONS = ('move_machine', 'move_tracker', 'move_markup', 'move_input', 'move_time')
W5_RECS = (1207, 1191, 849, 848, 846, 841)
TRACKER_SIZE = 0x1320                      # TU player tracker (memset 0x82413878)
MACHINE_SIZE = 0x560
LARA_BLOCK = 0x300
GT_FROM, GT_BLOCK = 0xa00, 0x300           # the [Perch] DROP dword diff, as TruMenu (gt+0xa00 .. +0xcff)
RING = 8


def stamp(t=None):
    t = time.time() if t is None else t
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t)) + '.%03d' % int((t % 1) * 1000)


def perch_rec(idx):
    return idx in (826, 840, 841, 849) or (idx is not None and 860 <= idx <= 867)


def bits_text(b):
    if b is None:
        return '?'
    return '0x%x%s%s%s' % (b, ' held' if b & 0x4 else '', ' PRESSED' if b & 0x10 else '', ' released' if b & 0x20 else '')


def to_world(h, v):
    c, s = math.cos(h), math.sin(h)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c, v[2])


def fin(*v):
    return all(x is not None and math.isfinite(x) for x in v)


class Blk:
    """one block read at `base` (one ReadProcessMemory), big-endian field access by offset"""

    def __init__(self, mem, base, n):
        self.base = base
        self.b = mem.read(base, n) if base else None
        if self.b is not None and len(self.b) < n:
            self.b = None

    def ok(self):
        return self.b is not None

    def u32(self, off):
        return struct.unpack_from('>I', self.b, off)[0] if self.b is not None and off + 4 <= len(self.b) else None

    def f32(self, off):
        return struct.unpack_from('>f', self.b, off)[0] if self.b is not None and off + 4 <= len(self.b) else None

    def u8(self, off):
        return self.b[off] if self.b is not None and off < len(self.b) else None


class MoveLog:
    def __init__(self, mem, A, log, path, optional_ok=None, interval=0.005):
        self.mem, self.A, self.log, self.path = mem, A, log, path
        ok = optional_ok or {}
        self.ok = {s: bool(ok.get(s)) for s in MOVE_SECTIONS}
        self.out = open(path, 'a', encoding='utf-8') if path else None
        self.lines = []                                  # every line written (selftest, link)
        self.interval = interval
        self.arrays = {}
        self.cnt = {'perch': 0, 'drops': 0, 'p': 0, 'vein': 0, 'tempo': 0, 'jump': 0, 'press': 0}
        self.prev_sig = None
        self.samples = 0
        # [Perch]
        self.pin = False
        self.p_rec, self.p_idx, self.p_txt = None, None, '?'
        self.p_prev_idx, self.p_prev_txt = None, '?'
        self.p_in_at, self.p_frames, self.p_in_drops = 0.0, 0, 0
        self.p_yaw0, self.p_zmin, self.p_zmax = 0.0, 0.0, 0.0
        self.p_prev_z, self.p_prev_yaw, self.p_prev_t = 0.0, 0.0, 0.0
        self.ring = []
        self.blk_ring = []                               # (gt block, Lara block) of the last 3 changed samples
        # B1 chart (P1-P5, V1-V3)
        self.c = None
        # [Tempo]
        self.tp_active, self.tp_at, self.tp_prev = None, 0.0, None
        # [Jump] / [Press]
        self.j_a20, self.j_on, self.j_start, self.j_reaims, self.j_samples = None, False, 0.0, 0, 0
        self.j_last_reaim_log, self.j_last_fly, self.j_still_since, self.j_z = 0.0, 0.0, None, None
        self.j_kind = None
        self.pr_bits = None
        self.idx_last_frame = None
        for s in MOVE_SECTIONS:
            if not self.ok[s]:
                self.w('[Moves] section %s: proof words differ or not checked - its values are ?' % s)
        if not (self.ok['move_machine'] and self.ok['move_tracker']):
            self.w('[Moves] move_machine / move_tracker not proven - no [Perch] / [Vein] / [Jump] / [Press] lines')

    # -- output
    def w(self, text, t=None):
        line = '%s %s' % (stamp(t), text)
        self.lines.append(line)
        if self.out:
            self.out.write(line + '\n')
            self.out.flush()
        self.log.w('D', 'move %s' % text)

    def lim(self, key, cap):
        self.cnt[key] += 1
        return self.cnt[key] <= cap

    # -- reads
    def u32(self, a):
        return S.u32(self.mem, a) if a else None

    def f32(self, a):
        return S.f32(self.mem, a) if a else None

    def u8(self, a):
        b = self.mem.read(a, 1) if a else None
        return b[0] if b else None

    def s16(self, a):
        b = self.mem.read(a, 2) if a else None
        return struct.unpack('>h', b)[0] if b and len(b) == 2 else None

    def s8(self, a):
        v = self.u8(a)
        return None if v is None else (v - 256 if v > 127 else v)

    def vec(self, a, n=3):
        b = self.mem.read(a, 4 * n) if a else None
        return struct.unpack('>%df' % n, b) if b and len(b) == 4 * n else None

    def record_index(self, mac, rec):
        lr = self.A['lara_record']
        chart = self.u32(mac + S.h(lr['chart_offset'])) if mac else None
        arr = self.u32(chart + S.h(lr['record_array_offset'])) if chart else None
        if not arr or not rec:
            return None
        words = self.arrays.get(arr)
        if words is None:
            raw = b''
            for k in range(8):
                b = self.mem.read(arr + k * 4096, 4096)
                if not b or len(b) < 4096:
                    break
                raw += b
            words = struct.unpack('>%dI' % (len(raw) // 4), raw) if raw else ()
            self.arrays[arr] = words
        try:
            return words.index(rec)
        except ValueError:
            return None

    def record_text(self, rec, idx):
        """TruMenu FwRecordText: 'index [up to 8 state ids]'"""
        lr = self.A['lara_record']
        ids = []
        n = self.s16(rec + S.h(lr['record_state_count_offset'])) if rec else None
        lst = self.u32(rec + S.h(lr['record_state_list_offset'])) if rec else None
        if n and lst and 0 < n <= 64:
            for i in range(min(n, 8)):
                v = self.s16(lst + 2 * i)
                if v is None:
                    break
                ids.append(str(v & 0xffff))
        return '%s [%s]' % (idx if idx is not None else -1, ' '.join(ids))

    def record_has(self, rec, a, b):
        lr = self.A['lara_record']
        n = self.s16(rec + S.h(lr['record_state_count_offset'])) if rec else None
        lst = self.u32(rec + S.h(lr['record_state_list_offset'])) if rec else None
        if not n or not lst or n < 0:
            return False
        for i in range(min(n, 64)):
            v = self.s16(lst + 2 * i)
            if v is None:
                break
            if (v & 0xffff) in (a, b):
                return True
        return False

    def obj_name(self, inst):
        ob = self.A['object']
        obj = self.u32(inst + S.h(ob['instance_object_offset']))
        return S.cstr(self.mem, self.u32(obj + S.h(ob['object_name_ptr_offset']))) if obj else ''

    def pend_text(self, p):
        """TruMenu B1PendText: '0x... -> <target> kinds [k k]'"""
        if not p:
            return '0'
        mm = self.A['move_machine']
        tg = self.s16(p + S.h(mm['pending_target']))
        nk = self.s16(p + S.h(mm['pending_kind_count'])) or 0
        kl = self.u32(p + S.h(mm['pending_kind_list']))
        ks = []
        for i in range(min(max(nk, 0), 6)):
            k = self.s16(kl + 2 * i) if kl else None
            if k is None:
                break
            ks.append(str(k & 0xffff))
        return '0x%08x -> %s kinds [%s]' % (p, (tg & 0xffff) if tg is not None else '?', ' '.join(ks))

    def box_type(self, box):
        """TruMenu B1BoxType"""
        if not box:
            return '0'
        if not self.ok['move_markup']:
            return '0x%08x type ? flags ?' % box
        mk = self.A['move_markup']
        rec = self.u32(box + S.h(mk['record']))
        fl = self.u32(box + S.h(mk['flags']))
        tb = self.s8(rec + S.h(mk['record_type'])) if rec else 0
        return '0x%08x type %d flags 0x%x' % (box, tb if tb is not None else 0, fl or 0)

    def box_text(self, box):
        """TruMenu PchBoxText for the attach box gt+0xc94 (item id and point count '?', see the module text)"""
        if not box:
            return 'box gt+0xc94 0'
        if not self.ok['move_markup']:
            return 'box 0x%08x ? (move_markup proof mismatch)' % box
        mk = self.A['move_markup']
        rec = self.u32(box + S.h(mk['record']))
        item = self.u32(box + S.h(mk['item']))
        flags = self.u32(box + S.h(mk['flags'])) or 0
        owner = self.u32(box + S.h(mk['owner']))
        rid = self.s16(rec + S.h(mk['record_id'])) if rec else -1
        rtype = self.s8(rec + S.h(mk['record_type'])) if rec else -1
        itype = self.s8(item + S.h(mk['item_type'])) if item else -1
        perch, pillar = bool(flags & 0x20000), bool(flags & 0x10)
        o = 'box 0x%08x rec #%s type %s item #%s type %s flags 0x%08x (%s%s%s)' % (
            box, rid if rid is not None else '?', rtype if rtype is not None else '?', '?' if item else -1,
            itype if itype is not None else '?', flags, 'PERCH' if perch else '', '+' if perch and pillar else '',
            'PILLAR' if pillar else '' if perch else 'no perch / pillar bit')
        if owner:
            o += " owner 0x%08x intro ? '%s'" % (owner, self.obj_name(owner))
            bone = self.s16(rec + S.h(mk['record_bone'])) if rec else None
            base = self.u32(owner + S.h(mk['owner_bones']))
            m = self.vec(base + bone * S.h(mk['bone_stride']), 16) if base and bone is not None else None
            if m and fin(*m):
                r2 = math.sqrt(m[8] ** 2 + m[9] ** 2 + m[10] ** 2)
                c = max(-1.0, min(1.0, m[10] / r2 if r2 > 1e-6 else 1.0))
                ang = math.degrees(math.acos(c))
                o += ' | matrix owner bone %s %.2f deg (row2 %.3f %.3f %.4f, row3 %.1f %.1f %.1f)' % (
                    'ROTATED' if ang > 0.05 else 'straight', ang, m[8], m[9], m[10], m[12], m[13], m[14])
            else:
                o += ' | matrix not readable'
        else:
            o += ' owner - (unit markup) | matrix ? (item / default path not proven on the TU)'
        line = self.u32(rec + S.h(mk['record_line'])) if rec else None
        if line:
            o += ' | ? point(s)'
            for i in range(2):
                p = self.vec(line + S.h(mk['line_point0']) + S.h(mk['point_stride']) * i)
                if p and fin(*p):
                    o += ' p%d %.1f %.1f %.1f' % (i, p[0], p[1], p[2])
        return o

    def action52(self):
        if not self.ok['move_input']:
            return None
        mi = self.A['move_input']
        mgr = self.u32(S.h(mi['manager_ptr']))
        st = self.u32(mgr + S.h(mi['action_set_offset'])) if mgr else None
        base = self.u32(st) if st else None
        return self.u32(base + mi['jump_action'] * S.h(mi['action_stride'])) if base else None

    def power1046(self, tb):
        """condition 1046 as the TU predicate 0x8246e400 evaluates it"""
        mt = self.A['move_tracker']
        dop = tb.u8(S.h(mt['doppelganger_flag']))
        if dop is None:
            return -1
        if dop:
            meter = tb.u32(S.h(self.A['player_tracker']['meter_object']))
            fl = self.u32(meter + S.h(self.A['meter']['flags'])) if meter else None
            return -1 if fl is None else fl & 1
        cm = tb.u32(S.h(self.A['player_tracker']['combat_manager']))
        bits = self.u32(cm + 0x1fc) if cm else None
        return -1 if bits is None else (bits >> 21) & 1

    # -- one sample
    def tick(self, now=None):
        now = time.time() if now is None else now
        lc = self.A['lara_chart']
        trk = self.u32(S.h(lc['player_tracker_ptr']))
        gt = S.h(self.A['game_tracker']['address'])
        lara = self.u32(gt + S.h(self.A['game_tracker']['player_instance']))
        if not trk or not lara:
            self.pin = False
            self.c = None
            return False
        tb = Blk(self.mem, trk, TRACKER_SIZE)
        lb = Blk(self.mem, lara, LARA_BLOCK)
        m = tb.u32(S.h(self.A['move_machine']['machine_offset'])) if tb.ok() else None
        mb = Blk(self.mem, m, MACHINE_SIZE) if m else None
        if not tb.ok() or not lb.ok() or not mb or not mb.ok():
            self.pin = False
            self.c = None
            return False
        self.tempo(now, tb, lb)                          # [Tempo] has its own once-a-second rule
        sig = (tb.b, mb.b, lb.b)
        if sig == self.prev_sig:
            return False                                 # no new game frame since the last sample
        self.prev_sig = sig
        self.samples += 1
        if not (self.ok['move_machine'] and self.ok['move_tracker']):
            return True
        rec = mb.u32(S.h(lc['record_offset']))
        if rec != self.p_rec:
            self.p_rec = rec
            self.p_idx = self.record_index(m, rec)
            self.p_txt = self.record_text(rec, self.p_idx)
        pos = (lb.f32(0x20), lb.f32(0x24), lb.f32(0x28))
        yaw = lb.f32(S.h(self.A['camera']['lara_yaw']))
        self.blk_ring = (self.blk_ring + [(tb.b[GT_FROM:GT_FROM + GT_BLOCK], lb.b[:LARA_BLOCK])])[-3:]
        self.perch(now, tb, rec, pos, yaw)
        self.chart(now, m, mb, tb, pos)
        self.jump(now, tb, pos, yaw)
        self.press(now, tb)
        return True

    # -- [Perch] (TruMenu PchTick)
    def perch(self, now, tb, rec, pos, yaw):
        mt = self.A['move_tracker']
        box, jt, t = tb.u32(S.h(mt['attach_box'])), tb.u32(S.h(mt['jump_target_box'])), tb.f32(S.h(mt['attach_t']))
        active = perch_rec(self.p_idx) or self.record_has(rec, 420, 603)
        if not active:
            if self.pin and self.lim('perch', 4000):
                self.w('[Perch] leave %s -> %s after %.2f s, %d sample(s): Lara %.1f %.1f %.1f yaw %.3f (first %.3f), z %.1f .. '
                       '%.1f, %d drop(s) | %s' % (self.p_prev_txt, self.p_txt, now - self.p_in_at, self.p_frames, pos[0], pos[1],
                                                  pos[2], yaw, self.p_yaw0, self.p_zmin, self.p_zmax, self.p_in_drops,
                                                  self.box_text(box)), now)
            self.pin = False
            self.p_prev_idx, self.p_prev_txt = self.p_idx, self.p_txt
            return
        if not self.pin:
            self.pin, self.p_in_at, self.p_frames, self.p_in_drops, self.ring = True, now, 0, 0, []
            self.p_yaw0, self.p_zmin, self.p_zmax = yaw, pos[2], pos[2]
            if self.lim('perch', 4000):
                self.w('[Perch] enter %s (from %s): Lara %.1f %.1f %.1f yaw %.3f, stick ? ?, jump target gt+0xa64 0x%08x, t '
                       'gt+0xc98 %.3f | %s' % (self.p_txt, self.p_prev_txt if self.p_prev_idx is not None else '?', pos[0],
                                               pos[1], pos[2], yaw, jt or 0, t, self.box_text(box)), now)
        else:
            if self.p_idx != self.p_prev_idx and self.lim('perch', 4000):
                self.w('[Perch] %s -> %s at +%.3f s: Lara %.1f %.1f %.1f yaw %.3f, stick ? ?, gt+0xa64 0x%08x, t gt+0xc98 '
                       '%.3f | %s' % (self.p_prev_txt, self.p_txt, now - self.p_in_at, pos[0], pos[1], pos[2], yaw, jt or 0,
                                      t, self.box_text(box)), now)
            dz = pos[2] - self.p_prev_z
            ms = int((now - self.p_prev_t) * 1000)
            if dz > 100.0 and self.lim('perch', 4000):
                self.w('[Perch] LIFT z %.1f -> %.1f (%+.1f) in one sample (%d ms) at +%.3f s: %s -> %s, Lara %.1f %.1f, stick '
                       '? ? (not a drop: upwards)' % (self.p_prev_z, pos[2], dz, ms, now - self.p_in_at, self.p_prev_txt,
                                                      self.p_txt, pos[0], pos[1]), now)
            if dz < -100.0:
                self.p_in_drops += 1
                if self.lim('drops', 200):
                    self.w('[Perch] DROP z %.1f -> %.1f (%+.1f) in one sample (%d ms) at +%.3f s: %s -> %s, Lara %.1f %.1f, yaw '
                           '%.3f -> %.3f, stick ? ?, gt+0xa64 0x%08x, t gt+0xc98 %.3f | %s' % (
                               self.p_prev_z, pos[2], dz, ms, now - self.p_in_at, self.p_prev_txt, self.p_txt, pos[0],
                               pos[1], self.p_prev_yaw, yaw, jt or 0, t, self.box_text(box)), now)
                    ring = ''.join(' | -%dms %s z %.1f yaw %.3f t %.3f box %08x jt %08x st ? ?' % (
                        int((now - r[0]) * 1000), r[1], r[2], r[3], r[4], r[5], r[6]) for r in self.ring)
                    self.w('[Perch]   last %d sample(s) before (oldest first):%s' % (len(self.ring), ring), now)
                    br = self.blk_ring
                    if len(br) >= 3:
                        self.diff('gt+0xa00.. sample -2 -> -1', GT_FROM, br[0][0], br[1][0], now)
                        self.diff('Lara +0x000.. sample -2 -> -1', 0, br[0][1], br[1][1], now)
                    if len(br) >= 2:
                        self.diff('gt+0xa00.. sample -1 -> drop', GT_FROM, br[-2][0], br[-1][0], now)
                        self.diff('Lara +0x000.. sample -1 -> drop', 0, br[-2][1], br[-1][1], now)
        self.p_frames += 1
        self.p_zmin, self.p_zmax = min(self.p_zmin, pos[2]), max(self.p_zmax, pos[2])
        self.ring = (self.ring + [(now, self.p_idx if self.p_idx is not None else -1, pos[2], yaw, t or 0.0, box or 0,
                                   jt or 0)])[-RING:]
        self.p_prev_z, self.p_prev_yaw, self.p_prev_t = pos[2], yaw, now
        self.p_prev_idx, self.p_prev_txt = self.p_idx, self.p_txt

    def diff(self, tag, base, a, b, now):
        """TruMenu PchDiff: the big-endian dwords that changed (floats when they look like one), up to 40"""
        o, changed, shown = '', 0, 0
        for off in range(0, min(len(a), len(b)) - 3, 4):
            x, y = a[off:off + 4], b[off:off + 4]
            if x == y:
                continue
            changed += 1
            if shown >= 40:
                continue
            shown += 1
            fx, fy = struct.unpack('>f', x)[0], struct.unpack('>f', y)[0]
            ux, uy = struct.unpack('>I', x)[0], struct.unpack('>I', y)[0]
            fl = fin(fx, fy) and (ux == 0 or 1e-4 < abs(fx) < 1e7) and (uy == 0 or 1e-4 < abs(fy) < 1e7)
            o += (' +0x%x %.4g>%.4g' % (base + off, fx, fy)) if fl else (' +0x%x %08x>%08x' % (base + off, ux, uy))
        self.w('[Perch]   %s: %d dword(s) changed%s%s' % (tag, changed, ' (first 40)' if changed > shown else '', o), now)

    # -- P1-P5 / V1-V3 (TruMenu B1ChartTick)
    def chart(self, now, m, mb, tb, pos):
        mm, mt = self.A['move_machine'], self.A['move_tracker']
        idx, rt = self.p_idx, self.p_txt
        pend = mb.u32(S.h(mm['pending']))
        m24 = mb.u32(S.h(mm['wait_word']))
        b54c = mb.u8(S.h(mm['input_lock_byte']))
        a64, c94 = tb.u32(S.h(mt['jump_target_box'])), tb.u32(S.h(mt['attach_box']))
        g78 = tb.u8(S.h(mt['lock_mirror_byte']))
        tt = tb.f32(S.h(mt['attach_t'])) or 0.0
        bits = self.action52()
        c = self.c
        if c is None or c['m'] != m:
            self.c = {'m': m, 'idx': idx, 'pend': pend, 'bits': bits, 'b54c': b54c, 'g78': g78, 'a64': a64, 'c94': c94,
                      'in1191': 0.0, 'vn': False, 'vn_until': 0.0, 'pos': pos}
            return
        bt = bits_text(bits)
        if idx in W5_RECS and pend != c['pend'] and self.lim('p', 3000):                       # P1
            self.w('[Perch] P1 pending [m+0x514] %s in %s: [m+0x24] %s, [m+0x53c] %s, action 52 %s, gt+0xa64 0x%08x, '
                   'gt+0xc94 0x%08x, t %.3f, z %.1f' % (self.pend_text(pend), rt, m24, b54c, bt, a64 or 0, c94 or 0, tt,
                                                         pos[2]), now)
        if idx == 1191 and c['idx'] != 1191:
            c['in1191'] = now
        if idx in (1207, 1191) and bits is not None and bits & 0x10 and self.lim('p', 3000):     # P2
            self.w('[Perch] P2 jump PRESSED in %s at +%.3f s in 1191, [m+0x24] %s, [m+0x514] 0x%08x, raw A ?' % (
                rt, now - c['in1191'] if idx == 1191 and c['in1191'] else 0.0, m24, pend or 0), now)
        if c['idx'] == 1191 and idx != 1191 and self.lim('p', 3000):                              # P3
            self.w('[Perch] P3 leave 1191 -> %s%s (pending the sample before %s), gt+0xa64 0x%08x -> 0x%08x, gt+0xc94 '
                   '0x%08x -> 0x%08x' % (rt, ' FROM THE BUFFER' if c['pend'] else ' (no buffered transition)',
                                         self.pend_text(c['pend']), c['a64'] or 0, a64 or 0, c['c94'] or 0, c94 or 0), now)
        if idx == 841 and c['idx'] != 841 and c94 and self.ok['move_markup']:                     # P4
            mk = self.A['move_markup']
            brec = self.u32(c94 + S.h(mk['record']))
            fl = self.u32(c94 + S.h(mk['flags'])) or 0
            ty = self.s8(brec + S.h(mk['record_type'])) if brec else 0
            if fl & 0x10 or ty == 15:
                self.w('[Perch] P4 WARNING: pillar box held on the perch stand (hop path) - 841 from %s with box 0x%08x '
                       'type %s flags 0x%x; the next turn sets Lara onto the pillar line' % (c['idx'], c94, ty, fl), now)
        if idx is not None and 860 <= idx <= 867 and not (c['idx'] is not None and 860 <= c['idx'] <= 867):   # P5
            p0 = p1 = None
            if c94 and self.ok['move_markup']:
                mk = self.A['move_markup']
                brec = self.u32(c94 + S.h(mk['record']))
                line = self.u32(brec + S.h(mk['record_line'])) if brec else None
                if line:
                    p0 = self.vec(line + S.h(mk['line_point0']))
                    p1 = self.vec(line + S.h(mk['line_point0']) + S.h(mk['point_stride']))
            pts = bool(p0 and p1 and fin(*p0) and fin(*p1))
            pp = c['pos']
            if self.lim('p', 3000):
                self.w('[Perch] P5 first sample of %s: Lara %.1f %.1f %.1f -> %.1f %.1f %.1f (%+.1f); %s' % (
                    rt, pp[0], pp[1], pp[2], pos[0], pos[1], pos[2], pos[2] - pp[2],
                    '' if pts else 'box gt+0xc94 has no 2-point line'), now)
            if pts and self.lim('p', 3000):
                q = [p0[k] + tt * (p1[k] - p0[k]) for k in range(3)]
                self.w('[Perch] P5 pillar point p0 + t (p1 - p0) at t %.3f = %.1f %.1f %.1f; Lara - point = %.1f %.1f dz '
                       '%+.1f (W5 expected -316.1)' % (tt, q[0], q[1], q[2], pos[0] - q[0], pos[1] - q[1], pos[2] - q[2]),
                       now)
        # [Vein]
        in_range = idx is not None and 1460 <= idx <= 1517
        if idx == 455 or in_range:
            if not c['vn']:
                self.w('[Vein] watch on at %s' % rt, now)
            c['vn'], c['vn_until'] = True, now + 3.0
        if c['vn'] and not in_range and idx != 455 and now > c['vn_until']:
            c['vn'] = False
            self.w('[Vein] watch off (3 s after the vein records)', now)
        if c['vn'] and self.lim('vein', 4000):
            if bits != c['bits'] or pend != c['pend'] or b54c != c['b54c'] or g78 != c['g78'] or idx != c['idx']:   # V1
                self.w('[Vein] V1 %s: action 52 %s, raw pad A ?, [m+0x514] %s, [m+0x53c] %s, gt+0x78 0x%08x' % (
                    rt, bt, self.pend_text(pend), b54c, g78 or 0), now)
            c_in = c['idx'] is not None and 1460 <= c['idx'] <= 1517
            if idx != c['idx'] and (in_range or c_in):                                             # V2
                self.w('[Vein] V2 %s -> %s%s (pending the sample before %s), stick ? ?, power %d (condition 1046 TU '
                       '0x8246e400), gt+0xa64 %s, gt+0xc94 %s' % (c['idx'], rt, ' FROM THE BUFFER' if c['pend'] else '',
                                                                 self.pend_text(c['pend']), self.power1046(tb),
                                                                 self.box_type(a64), self.box_type(c94)), now)
            if (c['idx'] == 455 and idx == 260) or (c['idx'] == 311 and idx == 1477):             # V3
                self.w('[Vein] V3 %s %s -> %s: action 52 %s, raw A ?, [m+0x514] %s' % (
                    'take-off from the ledge' if idx == 260 else 'docking', c['idx'], idx, bt, self.pend_text(pend)), now)
        c.update({'idx': idx, 'pend': pend, 'bits': bits, 'b54c': b54c, 'g78': g78, 'a64': a64, 'c94': c94, 'pos': pos})

    # -- [Tempo] (TruMenu B1TempoTick; once a second while the power is on and on each change)
    def tempo(self, now, tb, lb):
        meter = tb.u32(S.h(self.A['player_tracker']['meter_object']))
        fl =self.u32(meter + S.h(self.A['meter']['flags'])) if meter else None
        if fl is None:
            return
        act = fl & 1
        pos = (lb.f32(0x20), lb.f32(0x24), lb.f32(0x28))
        step, speed = 0.0, 0.0
        if self.tp_prev and fin(*pos):
            dt = max(now - self.tp_prev[0], 1e-3)
            step = math.hypot(pos[0] - self.tp_prev[1][0], pos[1] - self.tp_prev[1][1])
            speed = step / dt
        if self.tp_prev is None or pos != self.tp_prev[1]:
            self.tp_prev = (now, pos)
        if act == self.tp_active and (not act or now - self.tp_at < 1.0):
            return
        change = act != self.tp_active
        self.tp_active, self.tp_at = act, now
        if not self.lim('tempo', 3000):
            return
        gt = S.h(self.A['game_tracker']['address'])
        mtm, mr = self.A['move_time'], self.A['meter_requests']
        if self.ok['move_time']:
            ws = '%.2f' % self.f32(gt + S.h(mtm['world_time_scale']))
            ps = '%.2f' % self.f32(gt + S.h(mtm['player_time_scale']))
        else:
            ws = ps = '?'
        wt, pt = self.f32(S.h(mr['ramp_world'])), self.f32(S.h(mr['ramp_player']))
        slots = []
        for i in range(int(mr['slots'])):
            s = self.vec(meter + S.h(mr['offset']) + S.h(mr['stride']) * i, 2)
            if s and ((s[0] or 0) > 0.0 or (s[1] or 0) > 0.0):
                slots.append('%d:%.2f/%.2f' % (i, s[0], s[1]))
        val = self.f32(meter + S.h(self.A['meter']['value']))
        self.w('[Tempo] power %s%s: world %s player %s%s, ramp targets world %.2f player %.2f (0x827754cc / 0x827754ac), '
               'slots %s, meter %.1f, HUD ?, Lara %s (step %.1f u / sample, %.0f u/s, stick ? ?) in %s' % (
                   'ON' if act else 'off', ' (changed)' if change else '', ws, ps,
                   '' if self.ok['move_time'] else ' (move_time proof mismatch)', wt or 0.0, pt or 0.0,
                   ' '.join(slots) if slots else 'none', val if val is not None else -1.0, 'runs' if step > 3.0 else 'stands',
                   step, speed, self.p_txt), now)

    # -- [Jump] (no launch hook on the Xbox side: T+0xa20 written = launch / re-aim)
    def jump(self, now, tb, pos, yaw):
        mt = self.A['move_tracker']
        a20 = tuple(tb.f32(S.h(mt['launch_velocity']) + 4 * k) for k in range(3))
        tf = tb.f32(S.h(mt['flight_time']))
        tgt = tb.u32(S.h(mt['jump_target_box']))
        kind = (tb.u32(S.h(mt['kind_a_id'])), tb.u32(S.h(mt['kind_b_id'])))
        if self.j_kind is not None and kind != self.j_kind and self.lim('jump', 2000):
            self.w('[Jump] kind T+0xb00 %s -> %s, T+0xc90 %s -> %s in %s' % (self.j_kind[0], kind[0], self.j_kind[1], kind[1],
                                                                          self.p_txt), now)
        self.j_kind = kind
        new = self.j_a20 is not None and fin(*a20) and any(abs(a20[k] - self.j_a20[k]) > 0.005 for k in range(3)) and \
            any(abs(v) > 0.005 for v in a20)
        self.j_a20 = a20
        if new and not self.j_on:
            self.j_on, self.j_start, self.j_reaims, self.j_samples = True, now, 0, 0
            self.j_still_since, self.j_z, self.j_last_fly = None, pos[2], 0.0
            wv = to_world(yaw, a20)
            if self.lim('jump', 2000):
                self.w('[Jump] launch+ T+0xa20=%.2f %.2f %.2f T+0xaa0=? ? ? T+0x610=? dt=?' % a20, now)
            if self.lim('jump', 2000):
                self.w('[Jump] launch via=? (xbox: T+0xa20 written) who=Lara rec=%s p0=%.0f %.0f %.0f T+0xa20 world %.2f '
                       '%.2f %.2f (local %.2f %.2f %.2f turned by the yaw %.1f deg; flight heading %.1f deg) target=0x%08x '
                       '(%s) t=%.2f T+0xb00 %s T+0xc90 %s' % (
                           self.p_txt, pos[0], pos[1], pos[2], wv[0], wv[1], wv[2], a20[0], a20[1], a20[2], math.degrees(yaw),
                           math.degrees(math.atan2(wv[0], -wv[1])) if math.hypot(wv[0], wv[1]) > 0.5 else math.degrees(yaw),
                           tgt or 0, self.box_type(tgt), tf if tf is not None else -1.0, kind[0], kind[1]), now)
            return
        if not self.j_on:
            return
        self.j_samples += 1
        if new:
            self.j_reaims += 1
            if now - self.j_last_reaim_log >= 0.333 and self.lim('jump', 2000):
                self.j_last_reaim_log = now
                self.w('[Jump] re-aim #%d via=? p=%.0f %.0f %.0f v=%.2f %.2f %.2f' % (
                    self.j_reaims, pos[0], pos[1], pos[2], a20[0], a20[1], a20[2]), now)
        if now - self.j_last_fly >= 0.1 and self.lim('jump', 2000):
            self.j_last_fly = now
            self.w('[Jump] fly f=%d p=%.1f %.1f %.1f inst+0x2a0=? ? ? T+0x77c=%.3f dt=?' % (
                self.j_samples, pos[0], pos[1], pos[2], tf if tf is not None else -1.0), now)
        if self.j_z is not None and abs(pos[2] - self.j_z) < 0.5:
            self.j_still_since = self.j_still_since or now
        else:
            self.j_still_since = None
        self.j_z = pos[2]
        if (self.j_still_since and now - self.j_still_since >= 0.3) or now - self.j_start > 5.0:
            self.j_on = False
            self.w('[Jump] flight end after %.2f s: %d re-aim(s), %d sample(s) (xbox: %s)' % (
                now - self.j_start, self.j_reaims, self.j_samples,
                'z still for 0.3 s' if now - self.j_start <= 5.0 else 'stop after 5 s'), now)

    # -- [Press] (the rising pressed bit 0x10 of action 52)
    def press(self, now, tb):
        bits = self.action52()
        if bits is None:
            return
        rise = bool(bits & 0x10) and not (self.pr_bits is not None and self.pr_bits & 0x10)
        prev_idx = self.idx_last_frame
        self.pr_bits = bits
        self.idx_last_frame = self.p_idx
        if rise and self.lim('press', 2000):
            mt = self.A['move_tracker']
            self.w('[Press] jump pressed in %s (record the sample before %s): T+0xb00 %s T+0xc90 %s, kind A mode X+0xa0 ? '
                   'catch X+0xac ?, stick ?, C+0xb0 ?, camera yaw ? deg, T+0xa60 ?, yaw ? deg' % (
                       self.p_txt, prev_idx if prev_idx is not None else -1, tb.u32(S.h(mt['kind_a_id'])),
                       tb.u32(S.h(mt['kind_b_id']))), now)

    def close(self):
        if self.out:
            self.out.close()
            self.out = None


def run(mem, A, log, path, seconds, interval, optional_ok, once=False):
    ml = MoveLog(mem, A, log, path, optional_ok, interval)
    log.w('I', 'move log %s: %.0f s every %.3f s (stop with Ctrl+C)' % (path, seconds, interval))
    end = time.time() + seconds
    try:
        while time.time() < end:
            if not mem.alive():
                log.w('I', 'Xenia exited - stop')
                break
            ml.tick()
            if once:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    ml.close()
    log.w('I', 'move log end: %d changed sample(s), %d line(s) in %s' % (ml.samples, len(ml.lines), path))
    return ml


# ------------------------------------------------------------------------------------------------------------- selftest
class FakeMem:
    """a small TU-shaped memory (big endian): player tracker, chart machine with a record array, Lara, game tracker,
    meter, the input action set, a pillar box with an owner and a 2-point line. The values are invented test values."""

    def __init__(self, A):
        self.m = {}
        self.A = A
        for sec, v in A.items():
            if isinstance(v, dict):
                for a, w in v.get('proof', {}).items():
                    self.w32(S.h(a), S.h(w))
        self.trk, self.mac, self.lara, self.meter = 0x43000000, 0x43100000, 0x43400000, 0x43300000
        self.chart, self.arr, self.box = 0x45000000, 0x45100000, 0x49000000
        lc = A['lara_chart']
        self.zero(self.trk, TRACKER_SIZE); self.zero(self.mac, MACHINE_SIZE); self.zero(self.lara, LARA_BLOCK + 0x100)
        self.w32(S.h(lc['player_tracker_ptr']), self.trk)
        self.w32(self.trk + 0xf10, self.mac)
        self.w32(self.mac + 4, self.chart); self.w32(self.chart + 0xc, self.arr)
        self.zero(self.arr, 8 * 4096)
        self.rec = {}
        for idx in (1, 260, 311, 455, 827, 841, 863, 1191, 1207, 1477, 1480):
            r = 0x46000000 + idx * 0x40
            self.zero(r, 0x40)
            self.w32(self.arr + 4 * idx, r)
            ids = {863: (420, 603), 1191: (236,), 1477: (2102,)}.get(idx, ())
            self.w16(r + 0xc, len(ids)); self.w32(r + 0x18, r + 0x30)
            for k, sid in enumerate(ids):
                self.w16(r + 0x30 + 2 * k, sid)
            self.rec[idx] = r
        gt = S.h(A['game_tracker']['address'])
        self.gt = gt
        self.zero(gt, 0x200)
        self.w32(gt + 0xc, self.lara); self.wf(gt + 0x118, 1.0); self.wf(gt + 0x150, 1.0)
        self.w32(self.trk + 0x508, self.meter); self.zero(self.meter, 0x80)
        self.w32(self.trk + 0x504, 0x43500000); self.zero(0x43500000, 0x200)
        self.wf(self.meter + 8, 1000.0)
        for a in (S.h(A['meter_requests']['ramp_world']), S.h(A['meter_requests']['ramp_player'])):
            self.wf(a, 1.0)
        mgr, st, acts = 0x4a000000, 0x4a001000, 0x4a002000
        self.w32(S.h(A['move_input']['manager_ptr']), mgr); self.zero(mgr, 0x40); self.w32(mgr + 0x18, st)
        self.w32(st, acts); self.zero(acts, 0x1000)
        # pillar box: record (id 2170, type 15), flags PILLAR, owner with a 7 deg rotated bone, line p0 / p1
        rec, line, owner, bones = 0x49100000, 0x49200000, 0x49300000, 0x49400000
        self.zero(self.box, 0x40); self.zero(rec, 0x80); self.zero(line, 0x40); self.zero(owner, 0x100); self.zero(bones, 0x100)
        self.w32(self.box + 0x20, rec); self.w32(self.box + 0x28, 0x10); self.w32(self.box + 0xc, owner)
        self.w16(rec + 0x2e, 2170); self.m[rec + 0x33] = 15; self.w16(rec + 0x30, 1); self.w32(rec + 0x58, line)
        self.w32(owner + 0x90, bones)
        a = math.radians(7.0)
        for k, v in enumerate((1, 0, 0, 0, 0, math.cos(a), math.sin(a), 0, 0, -math.sin(a), math.cos(a), 0, -265.0, 10180.0,
                               2400.0, 1)):
            self.wf(bones + 0x40 + 4 * k, v)
        for k, v in enumerate((-265.0, 10179.0, 2444.0)):
            self.wf(line + 0x10 + 4 * k, v)
        for k, v in enumerate((-265.0, 10200.0, 3444.0)):
            self.wf(line + 0x20 + 4 * k, v)
        self.w32(owner + 0x10, 0x49500000); self.zero(0x49500000, 0x80); self.w32(0x49500000 + 0x60, 0x49600000)
        for k, ch in enumerate(b'dlc_pillar_test\0'):
            self.m[0x49600000 + k] = ch
        self.set_rec(1); self.set_pos(0.0, 0.0, 2469.9)

    def zero(self, a, n):
        for i in range(n):
            self.m.setdefault(a + i, 0)

    def w32(self, a, v):
        for i, b in enumerate(struct.pack('>I', v & 0xffffffff)):
            self.m[a + i] = b

    def w16(self, a, v):
        for i, b in enumerate(struct.pack('>H', v & 0xffff)):
            self.m[a + i] = b

    def wf(self, a, f):
        for i, b in enumerate(struct.pack('>f', f)):
            self.m[a + i] = b

    def set_rec(self, idx):
        self.w32(self.mac + 0x520, self.rec[idx])

    def set_pos(self, x, y, z):
        self.wf(self.lara + 0x20, x); self.wf(self.lara + 0x24, y); self.wf(self.lara + 0x28, z)

    def read(self, guest, n):
        if not guest or guest not in self.m:
            return None
        return bytes(self.m.get(guest + i, 0) for i in range(n))

    def alive(self):
        return True


class NullLog:
    def __init__(self, path=None):
        self.f = open(path, 'a', encoding='utf-8') if path else None

    def w(self, level, msg):
        if self.f:
            self.f.write('%s %s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), level, msg))
        if level in ('I', 'E'):
            print('%s %s' % (level, msg))


def selftest(A, log, path):
    fm = FakeMem(A)
    ml = MoveLog(fm, A, log, path, {s: True for s in MOVE_SECTIONS})
    t = [1000.0]

    def step(fn=None, dt=0.033):
        if fn:
            fn()
        t[0] += dt
        ml.tick(t[0])

    trk, mac = fm.trk, fm.mac
    acts = 0x4a002000 + 52 * 0x30
    step()
    step(lambda: fm.set_rec(1207))
    step(lambda: fm.set_rec(1191))
    step(lambda: (fm.w32(acts, 0x14), fm.w32(mac + 0x524, 0x4b000000), fm.zero(0x4b000000, 0x20),
                  fm.w16(0x4b000000, 841), fm.w16(0x4b000002, 1), fm.w32(0x4b000008, 0x4b000010), fm.w16(0x4b000010, 1)))
    step(lambda: fm.w32(acts, 0x4))
    step(lambda: (fm.set_rec(841), fm.w32(trk + 0xc94, fm.box), fm.w32(trk + 0xa64, fm.box), fm.wf(trk + 0xc98, 0.023),
                  fm.w32(mac + 0x524, 0), fm.w32(acts, 0)))
    step(lambda: fm.set_pos(0.0, 0.0, 2600.0))                     # LIFT +130
    step(lambda: (fm.set_rec(863), fm.set_pos(-265.5, 10179.6, 2128.3)))   # DROP -471.7 and P5 dz -316.1
    step(lambda: fm.set_pos(-265.5, 10179.6, 2128.4))
    step(lambda: fm.set_rec(827))                                   # leave
    # vein: 455 -> 260 take-off, 311 -> 1477 docking with a buffered input
    step(lambda: fm.set_rec(455))
    step(lambda: (fm.set_rec(260), fm.w32(acts, 0x10)))
    step(lambda: (fm.set_rec(311), fm.w32(acts, 0x4), fm.m.__setitem__(mac + 0x54c, 1), fm.m.__setitem__(trk + 0x78, 1)))
    step(lambda: (fm.set_rec(1477), fm.m.__setitem__(trk + 0x1244, 1), fm.w32(fm.meter + 4, 1)))
    step(lambda: (fm.set_rec(1480), fm.m.__setitem__(mac + 0x54c, 0), fm.m.__setitem__(trk + 0x78, 0)))
    # tempo: power on (meter flags bit 0 set above), world 0.30, player 1.20, slot 0
    step(lambda: (fm.wf(fm.gt + 0x118, 0.3), fm.wf(fm.gt + 0x150, 1.2), fm.wf(fm.meter + 0x40, 1.2), fm.wf(fm.meter + 0x44, 0.3),
                  fm.wf(S.h(A['meter_requests']['ramp_world']), 0.3), fm.wf(S.h(A['meter_requests']['ramp_player']), 1.2)))
    step(lambda: fm.set_pos(-265.5, 10190.0, 2128.4), dt=1.1)
    # jump: T+0xa20 written, re-aim, flight, landing (z still)
    step(lambda: (fm.set_rec(1), fm.wf(trk + 0xa20, 0.0), fm.wf(trk + 0xa24, -39.91), fm.wf(trk + 0xa28, 42.54),
                  fm.wf(trk + 0x77c, 14.86), fm.w32(trk + 0xb00, 19), fm.w32(trk + 0xa64, 0)))
    for k in range(6):
        step(lambda k=k: (fm.set_pos(-265.5, 10190.0 - 40 * k, 2128.4 + 30 * k - 3 * k * k), fm.wf(trk + 0x77c, 13.0 - k),
                          fm.wf(trk + 0xa24, -39.0 - k * 0.1) if k == 3 else None))
    for k in range(14):
        step(lambda k=k: (fm.set_pos(-265.5, 9900.0, 2100.0), fm.m.__setitem__(trk + 0x200 + (k % 4), k)))
    ml.close()
    text = '\n'.join(ml.lines)
    ok = True

    def need(cond, what):
        nonlocal ok
        if not cond:
            ok = False
            log.w('E', 'moves selftest: %s' % what)

    need('[Perch] P1 pending [m+0x514] 0x4b000000 -> 841 kinds [1] in 1191 [236]' in text, 'P1 pending text')
    need('[Perch] P2 jump PRESSED in 1191 [236]' in text, 'P2 pressed')
    need('[Perch] P3 leave 1191 -> 841 [] FROM THE BUFFER' in text, 'P3 from the buffer')
    need('[Perch] P4 WARNING: pillar box held on the perch stand' in text, 'P4 pillar box warning')
    need('[Perch] enter 1207' not in text, '1207 is no perch record, no enter line expected')
    need('[Perch] enter 841 [] (from 1191 [236])' in text, 'perch enter 841')
    need("rec #2170 type 15 item #-1 type -1 flags 0x00000010 (PILLAR) owner 0x49300000 intro ? 'dlc_pillar_test' | "
         "matrix owner bone ROTATED 7.00 deg" in text, 'box text (record, flags, owner, rotated matrix)')
    need('p0 -265.0 10179.0 2444.0 p1 -265.0 10200.0 3444.0' in text, 'box line points')
    need('[Perch] LIFT z 2469.9 -> 2600.0 (+130.1) in one sample' in text, 'LIFT')
    need('[Perch] DROP z 2600.0 -> 2128.3 (-471.7) in one sample' in text, 'DROP')
    need('[Perch]   last ' in text and 'gt+0xa00.. sample -1 -> drop' in text, 'DROP ring / dword diff')
    need('[Perch] P5 pillar point p0 + t (p1 - p0) at t 0.023 = -265.0 10179.5 2467.0; Lara - point = -0.5 0.1 dz -338.7'
         in text, 'P5 pillar point / dz')
    need('[Perch] leave 863 [420 603] -> 827 []' in text and '1 drop(s)' in text, 'perch leave summary')
    need('[Vein] watch on at 455 []' in text, 'vein watch on')
    need('[Vein] V3 take-off from the ledge 455 -> 260: action 52 0x10 PRESSED' in text, 'V3 take-off')
    need('[Vein] V3 docking 311 -> 1477' in text, 'V3 docking')
    need('[Vein] V1 311 []: action 52 0x4 held, raw pad A ?, [m+0x514] 0, [m+0x53c] 1, gt+0x78 0x00000001' in text,
         'V1 bits / lock byte / gt+0x78 byte')
    need('[Vein] V2 1477 -> 1480 [] (pending the sample before 0), stick ? ?, power 1 (condition 1046' in text,
         'V2 with condition 1046 (doppelganger -> meter flag)')
    need('[Tempo] power ON (changed): world ' in text, 'tempo on')
    need('[Tempo] power ON: world 0.30 player 1.20, ramp targets world 0.30 player 1.20 (0x827754cc / 0x827754ac), '
         'slots 0:1.20/0.30, meter 1000.0, HUD ?, Lara runs' in text, 'tempo values once a second')
    need('[Jump] launch+ T+0xa20=0.00 -39.91 42.54 T+0xaa0=? ? ? T+0x610=? dt=?' in text, 'jump launch+')
    need('target=0x00000000 (0) t=14.86 T+0xb00 19' in text, 'jump target / flight time / kind')
    need('[Jump] kind T+0xb00 0 -> 19' in text, 'kind change')
    need('[Jump] re-aim #1' in text, 're-aim')
    need('[Jump] fly f=' in text and 'T+0x77c=' in text, 'fly lines')
    need('[Jump] flight end after' in text and 'z still for 0.3 s' in text, 'flight end')
    need(text.count('[Press] jump pressed in') == 2, 'two presses (P2 and the ledge take-off), got %d' %
         text.count('[Press] jump pressed in'))
    # a section with a proof mismatch: box values '?', no action bits
    ml2 = MoveLog(fm, A, log, None, {'move_machine': True, 'move_tracker': True, 'move_markup': False,
                                     'move_input': False, 'move_time': False})
    need(ml2.box_text(fm.box).endswith('? (move_markup proof mismatch)') and ml2.action52() is None,
         'unproven sections not shown as ?')
    ml3 = MoveLog(fm, A, log, None, {})
    need(any('no [Perch] / [Vein] / [Jump] / [Press] lines' in x for x in ml3.lines), 'missing proofs not reported')
    log.w('I', 'moves selftest %s (%d lines, %s)' % ('PASSED' if ok else 'FAILED', len(ml.lines), path))
    return 0 if ok else 1


def main():
    import json
    ap = argparse.ArgumentParser(description='TruXenia move log (the Xbox side of TruMenu [Perch] / [Vein] / [Tempo] / [Jump])')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--log')
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--debug', action='store_true')
    ap.add_argument('--trace', action='store_true')
    a = ap.parse_args()
    if not a.selftest:
        print('run the move log through tools/truxenia.py --movelog (this file alone has only --selftest)')
        return 2
    root = os.path.normpath(os.path.join(HERE, '..', '..'))
    logdir = os.path.join(root, 'logs', 'truxenia')
    os.makedirs(logdir, exist_ok=True)
    st = time.strftime('%Y%m%d_%H%M%S')
    a.log = a.log or os.path.join(logdir, 'moves_selftest_%s.log' % st)
    log = S.Log(a.log, a.verbose, a.debug, a.trace)
    A = json.load(open(os.path.join(HERE, '..', 'docs', 'data', 'xenia_tu_combat_addresses.json'), encoding='utf-8'))
    return selftest(A, log, os.path.join(logdir, 'moves_selftest_%s_lines.log' % st))


if __name__ == '__main__':
    sys.exit(main())
