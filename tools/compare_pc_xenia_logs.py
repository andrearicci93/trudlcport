"""Compare a PC TruMenu.log with a TruXenia move log (B3, 2026-11-20): the [Perch] / [Vein] / [Tempo] / [Jump] / [Press]
lines of the same place played on the PC (TruMenu 0.22.65 .. 0.22.68) and in Xenia (tools/truxenia.py --movelog), laid
side by side per line kind; differences are marked.

Per tag the events of both sides are aligned by their record signature (difflib over e.g. "enter 841", "drop 841>863",
"V3 311>1477"), then the fields of each pair are compared: records exactly, z / dz within 5 u, t within 0.02, time
scales within 0.02, vectors within 0.5 per component, box record id / type / flags exactly, pointers only as "0 / set"
and "jump target == attach box". A '?' on one side (a value the Xbox side cannot read, docs/TRUXENIA.md "Move log") is
never a difference. PC-only fields of the Xbox format: TruMenu's gt+0x78 is a dword, the Xbox side the byte -> compared
as the low byte; "frame" (PC) and "sample" (Xbox) are the same step.

Usage (from the repository root):
  ../bin/pyt -t 120 tools/compare_pc_xenia_logs.py --pc <game>/TruMenu.log --xbox ../logs/truxenia/moves_<time>.log
        [--pc-since "2026-11-20 21:00:00"] [--pc-until ...] [--xbox-since ...] [--xbox-until ...]
        [--pc-session-mark REGEX | --pc-all] [--tags Perch,Vein] [--out ../logs/compare_moves.md]
        [--verbose] [--debug] [--trace] [--log PATH]
  ../bin/pyt -t 120 tools/compare_pc_xenia_logs.py --selftest      invented example lines (written only to the run's
                                                                   log folder, never to the repository)
The PC log spans days without a session cut: by default only the lines after the LAST line matching
--pc-session-mark (default 'TruMenu.*loaded') are used; --pc-all takes the whole file (the report says which).
Exit codes: 0 compared (differences are findings, not errors), 1 a side has no move lines, 2 usage.
"""
import argparse
import difflib
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
TAGS = ('Perch', 'Vein', 'Tempo', 'Jump', 'Press')
LINE = re.compile(r'^([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?) \[(%s)\] ?(.*)$' % '|'.join(TAGS))
NUM = r'([-+]?[\d.]+(?:e[-+]?\d+)?|\?)'
REC = r'(-?\d+) \[[^\]]*\]'
STEP = r'(?:frame|sample)'


class Log:
    def __init__(self, path, verbose, debug, trace):
        self.f = open(path, 'a', encoding='utf-8') if path else None
        self.verbose, self.debug, self.trace = verbose or debug or trace, debug or trace, trace

    def w(self, level, msg):
        if level == 'V' and not self.verbose:
            return
        if level == 'D' and not self.debug:
            return
        if level == 'T' and not self.trace:
            return
        line = '%s %s %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), level, msg)
        if self.f:
            self.f.write(line + '\n')
            self.f.flush()
        if level in ('I', 'E'):
            print(line)


def num(s):
    if s is None or s == '?':
        return None
    try:
        return float(s)
    except ValueError:
        return None


def box_fields(text):
    """the markup box text of TruMenu PchBoxText / B1BoxType (both sides)"""
    f = {}
    m = re.search(r'rec #(-?\d+|\?) type (-?\d+|\?) item #\S+ type (-?\d+|\?) flags 0x([0-9a-f]+)', text)
    if m:
        f['box_rec'], f['box_type'], f['item_type'], f['box_flags'] = m.group(1), m.group(2), m.group(3), m.group(4)
    m = re.search(r'matrix owner bone (ROTATED|straight) ' + NUM + ' deg', text)
    if m:
        f['box_matrix'], f['box_deg'] = m.group(1), num(m.group(2))
    if 'box gt+0xc94 0' in text:
        f['box_rec'] = 'none'
    return f


def btype(text):
    """B1BoxType '0x... type T flags 0xF' or '0'"""
    m = re.match(r'^0x[0-9a-f]+ type (-?\d+|\?) flags (0x[0-9a-f]+|\?)', text)
    return ('%s/%s' % (m.group(1), m.group(2))) if m else ('0' if text.strip() == '0' else '?')


def bits(text):
    m = re.match(r'^(0x[0-9a-f]+|\?)', text)
    if not m or m.group(1) == '?':
        return None
    return '0x%x' % (int(m.group(1), 16) & 0x34)     # held / pressed / released only


def parse_event(tag, rest):
    """(kind, signature, fields) or None for info lines (ring, dword diffs, fly samples)"""
    f = {}
    if tag == 'Perch':
        m = re.match(r'^enter %s \(from ([^)]*)\): Lara %s %s %s yaw %s, stick \S+ \S+, jump target gt\+0xa64 '
                     r'0x([0-9a-f]+), t gt\+0xc98 %s \| (.*)$' % (REC, NUM, NUM, NUM, NUM, NUM), rest)
        if m:
            f = {'rec': m.group(1), 'z': num(m.group(5)), 'a64': m.group(7) != '00000000', 't': num(m.group(8))}
            f.update(box_fields(m.group(9)))
            return 'enter', 'enter %s' % m.group(1), f
        m = re.match(r'^%s -> %s at \+%s s: Lara %s %s %s yaw %s, stick \S+ \S+, gt\+0xa64 0x([0-9a-f]+), t gt\+0xc98 %s '
                     r'\| (.*)$' % (REC, REC, NUM, NUM, NUM, NUM, NUM, NUM), rest)
        if m:
            f = {'from': m.group(1), 'rec': m.group(2), 'z': num(m.group(6)), 'a64': m.group(8) != '00000000',
                 't': num(m.group(9))}
            f.update(box_fields(m.group(10)))
            return 'change', 'change %s>%s' % (m.group(1), m.group(2)), f
        m = re.match(r'^leave %s -> %s after %s s, (\d+) %s\(s\): .* z %s \.\. %s, (\d+) drop\(s\)' % (
            REC, REC, NUM, STEP, NUM, NUM), rest)
        if m:
            f = {'from': m.group(1), 'rec': m.group(2), 'zmin': num(m.group(5)), 'zmax': num(m.group(6)),
                 'drops': m.group(7)}
            return 'leave', 'leave %s>%s' % (m.group(1), m.group(2)), f
        m = re.match(r'^(LIFT|DROP) z %s -> %s \(%s\) in one %s \((\d+) ms\) at \+%s s: %s -> %s' % (
            NUM, NUM, NUM, STEP, NUM, REC, REC), rest)
        if m:
            k = m.group(1).lower()
            f = {'z0': num(m.group(2)), 'z1': num(m.group(3)), 'dz': num(m.group(4)), 'from': m.group(7), 'rec': m.group(8)}
            return k, '%s %s>%s' % (k, m.group(7), m.group(8)), f
        m = re.match(r'^P1 pending \[m\+0x514\] (.*?) in %s: \[m\+0x24\] (\S+), \[m\+0x53c\] (\S+), action 52 (.*?), '
                     r'gt\+0xa64 0x([0-9a-f]+), gt\+0xc94 0x([0-9a-f]+), t %s, z %s$' % (REC, NUM, NUM), rest)
        if m:
            pt = re.match(r'^0x[0-9a-f]+ -> (\S+) kinds \[([^\]]*)\]', m.group(1))
            f = {'rec': m.group(2), 'pending': ('%s [%s]' % (pt.group(1), pt.group(2))) if pt else m.group(1),
                 'm24': m.group(3), 'm53c': m.group(4), 'bits': bits(m.group(5)), 'a64': m.group(6) != '00000000',
                 'c94': m.group(7) != '00000000', 'a64_is_c94': m.group(6) == m.group(7) and m.group(6) != '00000000',
                 't': num(m.group(8)), 'z': num(m.group(9))}
            return 'P1', 'P1 %s %s' % (m.group(2), f['pending']), f
        m = re.match(r'^P2 jump PRESSED in %s' % REC, rest)
        if m:
            return 'P2', 'P2 %s' % m.group(1), {'rec': m.group(1)}
        m = re.match(r'^P3 leave 1191 -> %s( FROM THE BUFFER| \(no buffered transition\)).*gt\+0xa64 0x([0-9a-f]+) -> '
                     r'0x([0-9a-f]+), gt\+0xc94 0x([0-9a-f]+) -> 0x([0-9a-f]+)' % REC, rest)
        if m:
            f = {'rec': m.group(1), 'buffer': 'FROM THE BUFFER' in m.group(2), 'a64_after': m.group(4) != '00000000',
                 'c94_after': m.group(6) != '00000000',
                 'a64_is_c94_after': m.group(4) == m.group(6) and m.group(4) != '00000000'}
            return 'P3', 'P3 1191>%s' % m.group(1), f
        m = re.match(r'^P4 WARNING: .* 841 from (-?\d+) with box 0x[0-9a-f]+ type (\S+) flags (0x[0-9a-f]+)', rest)
        if m:
            return 'P4', 'P4 %s' % m.group(1), {'from': m.group(1), 'box_type': m.group(2), 'box_flags': m.group(3)}
        m = re.match(r'^P5 first %s of %s: .*\(%s\);' % (STEP, REC, NUM), rest)
        if m:
            return 'P5', 'P5 %s' % m.group(1), {'rec': m.group(1), 'dz': num(m.group(2))}
        m = re.match(r'^P5 pillar point p0 \+ t \(p1 - p0\) at t %s = .*; Lara - point = %s %s dz %s' % (NUM, NUM, NUM, NUM),
                     rest)
        if m:
            return 'P5pt', 'P5pt', {'t': num(m.group(1)), 'dx': num(m.group(2)), 'dy': num(m.group(3)), 'dz': num(m.group(4))}
        return None
    if tag == 'Vein':
        m = re.match(r'^V1 %s: action 52 (.*?), raw pad A (\S+), \[m\+0x514\] (.*?), \[m\+0x53c\] (\S+), gt\+0x78 '
                     r'0x([0-9a-f]+)$' % REC, rest)
        if m:
            pt = re.match(r'^0x[0-9a-f]+ -> (\S+) kinds \[([^\]]*)\]', m.group(4))
            f = {'rec': m.group(1), 'bits': bits(m.group(2)), 'pending': ('%s [%s]' % (pt.group(1), pt.group(2))) if pt
                 else m.group(4), 'm53c': m.group(5), 'g78': str(int(m.group(6), 16) & 0xff)}
            return 'V1', 'V1 %s' % m.group(1), f
        m = re.match(r'^V2 (-?\d+) -> %s( FROM THE BUFFER)? .*power (-?\d+) .*gt\+0xa64 (.*), gt\+0xc94 (.*)$' % REC, rest)
        if m:
            f = {'from': m.group(1), 'rec': m.group(2), 'buffer': bool(m.group(3)), 'power': m.group(4),
                 'a64_type': btype(m.group(5)), 'c94_type': btype(m.group(6))}
            return 'V2', 'V2 %s>%s' % (m.group(1), m.group(2)), f
        m = re.match(r'^V3 (take-off from the ledge|docking) (-?\d+) -> (-?\d+): action 52 (.*?), raw A', rest)
        if m:
            return 'V3', 'V3 %s>%s' % (m.group(2), m.group(3)), {'bits': bits(m.group(4))}
        m = re.match(r'^watch (on|off)', rest)
        if m:
            return 'watch', 'watch %s' % m.group(1), {}
        return None
    if tag == 'Tempo':
        m = re.match(r'^power (ON|off)( \(changed\))?: world %s player %s.*?, ramp targets world %s player %s .*?slots '
                     r'(.*?), meter %s, HUD \S+, Lara (runs|stands)' % (NUM, NUM, NUM, NUM, NUM), rest)
        if m:
            f = {'power': m.group(1), 'world': num(m.group(3)), 'player': num(m.group(4)), 'ramp_world': num(m.group(5)),
                 'ramp_player': num(m.group(6)), 'slots': m.group(7), 'meter': num(m.group(8)), 'lara': m.group(9)}
            return 'tempo', 'power %s%s' % (m.group(1), ' changed' if m.group(2) else ''), f
        return None
    if tag == 'Jump':
        m = re.match(r'^(launch|drop)\+ T\+0xa20=%s %s %s' % (NUM, NUM, NUM), rest)
        if m:
            return 'launch+', '%s+' % m.group(1), {'a20': (num(m.group(2)), num(m.group(3)), num(m.group(4)))}
        m = re.match(r'^(launch|drop) via=.*? rec=%s .*target=0x([0-9a-f]+) .*? t=%s' % (REC, NUM), rest)
        if m:
            return 'launch', '%s %s' % (m.group(1), m.group(2)), {'rec': m.group(2), 'target': m.group(3) != '00000000',
                                                                   't': num(m.group(4))}
        m = re.match(r'^flight end after %s s: (\d+) re-aim' % NUM, rest)
        if m:
            return 'end', 'flight end', {'reaims': m.group(2)}
        m = re.match(r'^kind T\+0xb00 (\S+) -> (\S+), T\+0xc90 (\S+) -> (\S+)', rest)
        if m:
            return 'kind', 'kind %s' % m.group(2), {'b00': m.group(2), 'c90': m.group(4)}
        return None
    if tag == 'Press':
        m = re.match(r'^jump pressed in %s \(record the %s before (-?\d+)\): T\+0xb00 (\S+) T\+0xc90 (\S+),' % (REC, STEP),
                     rest)
        if m:
            return 'press', 'press %s' % m.group(1), {'rec': m.group(1), 'before': m.group(2), 'b00': m.group(3),
                                                       'c90': m.group(4)}
        return None
    return None


def cut(ts, limit):
    """the part of the stamp a --since / --until value compares with: 'HH:MM[:SS]' = the time, else date + time"""
    return ts[11:11 + len(limit)] if len(limit) <= 12 else ts[:len(limit)]


def read_log(path, since, until, mark, log):
    rows, info = [], ''
    with open(path, encoding='utf-8', errors='replace') as fh:
        lines = fh.read().splitlines()
    start = 0
    if mark:
        rx = re.compile(mark)
        hits = [i for i, ln in enumerate(lines) if rx.search(ln)]
        if hits:
            start = hits[-1] + 1
            info = 'after line %d (%s)' % (hits[-1] + 1, lines[hits[-1]][:80])
        else:
            info = 'session mark %r not found - whole file' % mark
            log.w('I', '%s: %s' % (path, info))
    for ln in lines[start:]:
        m = LINE.match(ln)
        if not m:
            continue
        ts, tag, rest = m.group(1), m.group(2), m.group(3)
        if since and cut(ts, since) < since:
            continue
        if until and cut(ts, until) > until:
            continue
        ev = parse_event(tag, rest)
        if ev:
            rows.append({'ts': ts, 'tag': tag, 'kind': ev[0], 'sig': ev[1], 'f': ev[2], 'text': rest})
    log.w('V', '%s: %d move event(s) %s' % (path, len(rows), info))
    return rows, info


TOL = {'z': 5.0, 'z0': 5.0, 'z1': 5.0, 'dz': 5.0, 'zmin': 5.0, 'zmax': 5.0, 'dx': 5.0, 'dy': 5.0, 't': 0.02,
       'world': 0.02, 'player': 0.02, 'ramp_world': 0.02, 'ramp_player': 0.02, 'meter': 1.0, 'box_deg': 0.1}
SKIP = {'meter'}                                  # meter values depend on the play, shown but not judged


def compare_fields(a, b):
    diffs = []
    for k in sorted(set(a) | set(b)):
        if k in SKIP:
            continue
        x, y = a.get(k), b.get(k)
        if x is None or y is None or x == '?' or y == '?':
            continue
        if k == 'a20':
            if any(p is not None and q is not None and abs(p - q) > 0.5 for p, q in zip(x, y)):
                diffs.append('a20 %s / %s' % (' '.join('%.2f' % v for v in x if v is not None),
                                               ' '.join('%.2f' % v for v in y if v is not None)))
            continue
        if isinstance(x, float) or isinstance(y, float):
            if abs(x - y) > TOL.get(k, 0.01):
                diffs.append('%s %g / %g' % (k, x, y))
        elif x != y:
            diffs.append('%s %s / %s' % (k, x, y))
    return diffs


def short(ev):
    if not ev:
        return '-'
    parts = []
    for k, v in ev['f'].items():
        if isinstance(v, float):
            parts.append(('%s %.1f' if abs(v) >= 10 else '%s %.3f') % (k, v))
        elif isinstance(v, tuple):
            parts.append('%s %s' % (k, ' '.join('?' if q is None else '%.2f' % q for q in v)))
        else:
            parts.append('%s %s' % (k, v))
    return '%s %s: %s' % (ev['ts'][11:], ev['sig'], ', '.join(parts))


def align(pc, xb):
    """pairs (pc event or None, xbox event or None) aligned by signature"""
    sm = difflib.SequenceMatcher(None, [e['sig'] for e in pc], [e['sig'] for e in xb], autojunk=False)
    out = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            out += list(zip(pc[i1:i2], xb[j1:j2]))
        else:
            out += [(e, None) for e in pc[i1:i2]] + [(None, e) for e in xb[j1:j2]]
    return out


def compare(pc_rows, xb_rows, tags):
    result = {}
    for tag in tags:
        pc = [r for r in pc_rows if r['tag'] == tag]
        xb = [r for r in xb_rows if r['tag'] == tag]
        rows = []
        for a, b in align(pc, xb):
            if a and b:
                d = compare_fields(a['f'], b['f'])
                rows.append((a, b, 'DIFF: ' + '; '.join(d) if d else 'ok'))
            else:
                rows.append((a, b, 'PC only' if a else 'Xbox only'))
        result[tag] = rows
    return result


def md_cell(s):
    return s.replace('|', '/').replace('\n', ' ')


def report(res, args, pc_info, xb_info):
    out = ['# PC / Xenia move log comparison', '',
           '- PC: `%s` (%s%s%s)' % (args.pc, pc_info or 'whole file', ', since %s' % args.pc_since if args.pc_since else '',
                                    ', until %s' % args.pc_until if args.pc_until else ''),
           '- Xbox: `%s` (%s%s)' % (args.xbox, ', since %s' % args.xbox_since if args.xbox_since else 'whole file',
                                    ', until %s' % args.xbox_until if args.xbox_until else ''),
           '- made %s by tools/compare_pc_xenia_logs.py; tolerances z / dz 5 u, t 0.02, time scale 0.02, vectors 0.5; '
           '`?` = not readable on that side (never a difference)' % time.strftime('%Y-%m-%d %H:%M:%S'), '',
           '| Tag | pairs ok | pairs DIFF | PC only | Xbox only |', '|---|---|---|---|---|']
    for tag, rows in res.items():
        c = {'ok': 0, 'DIFF': 0, 'PC only': 0, 'Xbox only': 0}
        for _, _, r in rows:
            c['DIFF' if r.startswith('DIFF') else r] += 1
        out.append('| [%s] | %d | %d | %d | %d |' % (tag, c['ok'], c['DIFF'], c['PC only'], c['Xbox only']))
    for tag, rows in res.items():
        out += ['', '## [%s]' % tag, '']
        if not rows:
            out.append('(no lines on either side)')
            continue
        out += ['| # | PC | Xbox | Result |', '|---|---|---|---|']
        for i, (a, b, r) in enumerate(rows, 1):
            out.append('| %d | %s | %s | %s |' % (i, md_cell(short(a)), md_cell(short(b)), md_cell(r)))
    return '\n'.join(out) + '\n'


def selftest(log, folder):
    """invented example lines in both formats (written to the run's log folder only)"""
    os.makedirs(folder, exist_ok=True)
    d = '2026-11-20 '
    pc = [d + '20:00:00.000 [Perch] enter 841 [] (from 1191 [236]): Lara 0.0 0.0 2469.9 yaw 0.000, stick 0 0, jump target '
               'gt+0xa64 0x11110000, t gt+0xc98 0.023 | box 0x11110000 rec #2170 type 15 item #-1 type -1 flags 0x00000010 '
               '(PILLAR) owner 0x22220000 intro 4711 \'x\' | matrix owner bone ROTATED 7.00 deg (row2 0 0 1, row3 0 0 0)',
          d + '20:59:00.000 TruMenu 0.22.68 loaded (example session mark)',
          d + '21:00:00.000 [Perch] enter 841 [] (from 1191 [236]): Lara 0.0 0.0 2469.9 yaw 0.000, stick 0 0, jump target '
               'gt+0xa64 0x11110000, t gt+0xc98 0.023 | box 0x11110000 rec #2170 type 15 item #3 type -1 flags 0x00000010 '
               '(PILLAR) owner 0x22220000 intro 4711 \'x\' | matrix owner bone ROTATED 7.00 deg (row2 0 0 1, row3 0 0 0)',
          d + '21:00:00.100 [Perch] DROP z 2469.9 -> 2128.3 (-341.6) in one frame (16 ms) at +0.100 s: 841 [] -> 863 [420 '
               '603], Lara 1.0 2.0, yaw 0.000 -> 0.000, stick 0 0, gt+0xa64 0x11110000, t gt+0xc98 0.023 | box 0x11110000',
          d + '21:00:00.100 [Perch]   last 2 frame(s) before (oldest first): | -16ms 841 z 2469.9',
          d + '21:00:00.120 [Perch] P3 leave 1191 -> 841 [] FROM THE BUFFER (pending the frame before 0x1 -> 841 kinds [1]), '
               'gt+0xa64 0x00000000 -> 0x11110000, gt+0xc94 0x00000000 -> 0x11110000',
          d + '21:00:01.000 [Vein] V1 311 []: action 52 0x14 held PRESSED, raw pad A 1, [m+0x514] 0, [m+0x53c] 1, gt+0x78 '
               '0x3f800001',
          d + '21:00:01.100 [Vein] V2 311 -> 1477 [2102] FROM THE BUFFER (pending the frame before 0x1 -> 1477 kinds [7]), '
               'stick 0 0, power 1 (meter flag, condition 1046 x), gt+0xa64 0, gt+0xc94 0x1 type 3 flags 0x0',
          d + '21:00:02.000 [Tempo] power ON (changed): world 0.30 player 1.20, ramp targets world 0.30 player 1.20 (0x8abeb4 '
               '/ 0x8abe94 x), slots 0:1.20/0.30, meter 900.0, HUD 0.900, Lara runs (step 6.1 u / frame x, stick 0 32767) '
               'in 1477 [2102]',
          d + '21:00:03.000 [Jump] launch+ T+0xa20=0.00 -39.91 42.54 T+0xaa0=0.00 0.00 0.00 T+0x610=0x00000000 dt=1.000',
          d + '21:00:03.000 [Jump] launch via=0x0073f0d3 (aimed) who=Lara rec=913 [606] p0=0 0 0 v=0.00 0.00 0.00 u/frame '
               'world (...) g=5.724 target=0x00000000 aim=0 0 0 (before this call) t=14.86',
          d + '21:00:04.000 [Press] jump pressed in 1191 [236] (record the frame before 1191): T+0xb00 19 T+0xc90 0, kind A',
          ]
    xb = [d + '21:10:00.000 [Perch] enter 841 [] (from 1191 [236]): Lara 0.0 0.0 2460.0 yaw 0.000, stick ? ?, jump target '
               'gt+0xa64 0x00000000, t gt+0xc98 0.023 | box 0x45000000 rec #2170 type 15 item #? type -1 flags 0x00000010 '
               '(PILLAR) owner 0x46000000 intro ? \'x\' | matrix owner bone ROTATED 7.00 deg (row2 0 0 1, row3 0 0 0)',
          d + '21:10:00.300 [Perch] P3 leave 1191 -> 841 [] FROM THE BUFFER (pending the sample before 0x1 -> 841 kinds '
               '[1]), gt+0xa64 0x00000000 -> 0x45000000, gt+0xc94 0x00000000 -> 0x45000000',
          d + '21:10:00.500 [Perch] LIFT z 2466.0 -> 2600.0 (+134.0) in one sample (33 ms) at +0.500 s: 841 [] -> 841 [], Lara '
               '0.0 0.0, stick ? ? (not a drop: upwards)',
          d + '21:10:01.000 [Vein] V1 311 []: action 52 0x14 held PRESSED, raw pad A ?, [m+0x514] 0, [m+0x53c] 1, gt+0x78 '
               '0x00000001',
          d + '21:10:01.100 [Vein] V2 311 -> 1477 [2102] FROM THE BUFFER (pending the sample before 0x1 -> 1477 kinds [7]), '
               'stick ? ?, power 0 (condition 1046 TU 0x8246e400), gt+0xa64 0, gt+0xc94 0x2 type 3 flags 0x0',
          d + '21:10:02.000 [Tempo] power ON (changed): world 0.30 player 1.20, ramp targets world 0.30 player 1.20 '
               '(0x827754cc / 0x827754ac), slots 0:1.20/0.30, meter 1000.0, HUD ?, Lara runs (step 9.0 u / sample, 270 u/s, '
               'stick ? ?) in 1477 [2102]',
          d + '21:10:03.000 [Jump] launch+ T+0xa20=0.00 -39.91 42.54 T+0xaa0=? ? ? T+0x610=? dt=?',
          d + '21:10:03.000 [Jump] launch via=? (xbox: T+0xa20 written) who=Lara rec=913 [606] p0=0 0 0 T+0xa20 world 0 0 0 '
               '(local) target=0x00000000 (0) t=14.86 T+0xb00 19 T+0xc90 0',
          d + '21:10:04.000 [Press] jump pressed in 1191 [236] (record the sample before 1191): T+0xb00 19 T+0xc90 0, kind A',
          ]
    pcp, xbp = os.path.join(folder, 'pc_example.log'), os.path.join(folder, 'xbox_example.log')
    open(pcp, 'w', encoding='utf-8').write('\n'.join(pc) + '\n')
    open(xbp, 'w', encoding='utf-8').write('\n'.join(xb) + '\n')
    a = argparse.Namespace(pc=pcp, xbox=xbp, pc_since=None, pc_until=None, xbox_since=None, xbox_until=None)
    pr, pinfo = read_log(pcp, None, None, r'TruMenu.*loaded', log)
    xr, xinfo = read_log(xbp, None, None, None, log)
    res = compare(pr, xr, TAGS)
    md = report(res, a, pinfo, xinfo)
    outp = os.path.join(folder, 'compare_example.md')
    open(outp, 'w', encoding='utf-8').write(md)
    ok = True

    def need(cond, what):
        nonlocal ok
        if not cond:
            ok = False
            log.w('E', 'compare selftest: %s' % what)

    def find(tag, sig):
        return [r for r in res[tag] if (r[0] or r[1])['sig'] == sig]

    need(len([r for r in pr if r['tag'] == 'Perch' and r['kind'] == 'enter']) == 1, 'session cut: the old enter line used')
    e = find('Perch', 'enter 841')
    need(len(e) == 1 and e[0][0] and e[0][1] and 'z 2469.9 / 2460' in e[0][2] and 'a64 True / False' in e[0][2]
         and 'box_rec' not in e[0][2], 'enter pair: z / a64 difference expected, box equal: %r' % (e and e[0][2]))
    need(any(r[2] == 'PC only' and r[0]['sig'] == 'drop 841>863' for r in find('Perch', 'drop 841>863')), 'PC-only DROP')
    need(any(r[2] == 'Xbox only' for r in find('Perch', 'lift 841>841')), 'Xbox-only LIFT')
    p3 = find('Perch', 'P3 1191>841')
    need(len(p3) == 1 and p3[0][2] == 'ok', 'P3 pair ok (pointers compared as set / equal): %r' % (p3 and p3[0][2]))
    v1 = find('Vein', 'V1 311')
    need(len(v1) == 1 and v1[0][2] == 'ok', 'V1: gt+0x78 dword low byte = Xbox byte, raw A ? ignored: %r' % (v1 and v1[0][2]))
    v2 = find('Vein', 'V2 311>1477')
    need(len(v2) == 1 and 'power 1 / 0' in v2[0][2], 'V2 power difference: %r' % (v2 and v2[0][2]))
    tp = find('Tempo', 'power ON changed')
    need(len(tp) == 1 and tp[0][2] == 'ok', 'Tempo equal (meter not judged, HUD ?): %r' % (tp and tp[0][2]))
    lp = find('Jump', 'launch+')
    need(len(lp) == 1 and lp[0][2] == 'ok', 'launch+ a20 equal: %r' % (lp and lp[0][2]))
    ln = find('Jump', 'launch 913')
    need(len(ln) == 1 and ln[0][2] == 'ok', 'launch rec / target / t equal: %r' % (ln and ln[0][2]))
    ps = find('Press', 'press 1191')
    need(len(ps) == 1 and ps[0][2] == 'ok', 'press equal: %r' % (ps and ps[0][2]))
    need('| [Perch] |' in md and '## [Vein]' in md, 'report sections')
    log.w('I', 'compare selftest %s (%s)' % ('PASSED' if ok else 'FAILED', outp))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description='PC TruMenu.log vs TruXenia move log ([Perch] / [Vein] / [Tempo] / [Jump] / '
                                             '[Press])')
    ap.add_argument('--pc')
    ap.add_argument('--xbox')
    ap.add_argument('--pc-since')
    ap.add_argument('--pc-until')
    ap.add_argument('--xbox-since')
    ap.add_argument('--xbox-until')
    ap.add_argument('--pc-session-mark', default=r'TruMenu.*loaded')
    ap.add_argument('--pc-all', action='store_true')
    ap.add_argument('--tags', default=','.join(TAGS))
    ap.add_argument('--out')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--log')
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--debug', action='store_true')
    ap.add_argument('--trace', action='store_true')
    a = ap.parse_args()
    logdir = os.path.join(ROOT, 'logs', 'compare_moves')
    os.makedirs(logdir, exist_ok=True)
    st = time.strftime('%Y%m%d_%H%M%S')
    log = Log(a.log or os.path.join(logdir, 'compare_%s%s.log' % (st, '_selftest' if a.selftest else '')), a.verbose,
              a.debug, a.trace)
    log.w('I', 'compare_pc_xenia_logs start (%s)' % ' '.join(sys.argv[1:]))
    if a.selftest:
        return selftest(log, os.path.join(logdir, 'selftest_%s' % st))
    if not a.pc or not a.xbox:
        ap.print_usage()
        return 2
    tags = [t for t in a.tags.split(',') if t in TAGS]
    pr, pinfo = read_log(a.pc, a.pc_since, a.pc_until, None if a.pc_all else a.pc_session_mark, log)
    xr, xinfo = read_log(a.xbox, a.xbox_since, a.xbox_until, None, log)
    md = report(compare(pr, xr, tags), a, pinfo, xinfo)
    outp = a.out or os.path.join(logdir, 'compare_%s.md' % st)
    open(outp, 'w', encoding='utf-8').write(md)
    log.w('I', 'PC %d event(s), Xbox %d event(s) -> %s' % (len(pr), len(xr), outp))
    return 0 if pr and xr else 1


if __name__ == '__main__':
    sys.exit(main())
