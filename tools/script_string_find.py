"""Find the script sections (type 8) whose data hold given text, and the functions that point at it (read-only, Q1a
2026-11-17: which scripts print "ABOUT TO FADE OUT LOADING SCREEN", "special fade-in case for cine", "WaitCine" ...).

For every match: unit / file, script id, data offset, the whole NUL-terminated string at that place, and every code
word of the script whose internal relocation points at the string start (function index, code offset, opcode). The
output names script ids and game strings: it belongs in a local folder, never in the repository.

Usage (from the repository root):
  ../bin/pyt -t 900 tools/script_string_find.py TARGET[,TARGET...] TEXT [TEXT ...] [--icase] [--list WORD]
        [--log DIR] [--verbose] [--debug] [--trace]
  TARGET  a PC unit name without .drm (PC base archives through tools/puzzle_switch_scan.Source), 'generalbank', or
          a path to a PC .drm file
  TEXT    substring to look for (bytes, latin-1)
  --icase case-insensitive match
  --list WORD  also print every string of the matching scripts that contains WORD (case-insensitive)
  --at HEX,... also print the NUL-terminated text at these data offsets of the matching scripts
  --log   folder for the run log (default ../local_results/script_string_find, outside the repository)
Exit code: 0 = at least one match, 1 = nothing found, 2 = usage error.
"""
import sys, os, struct, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drm_reloc as R
import script_conv as SC
from drm import cdrm_decode, sections_with_data

LOG = {'level': 0, 'fh': None}


def log(msg, lvl=0):
    """lvl 0 = always, 1 = verbose, 2 = debug, 3 = trace; the log file gets everything up to debug (trace with --trace)"""
    if lvl <= LOG['level']:
        print(msg, flush=True)
    if LOG['fh'] and (lvl <= 2 or LOG['level'] >= 3):
        LOG['fh'].write(msg + '\n')


def load(target, src):
    if target.lower().endswith('.drm') and os.path.isfile(target):
        return sections_with_data(cdrm_decode(open(target, 'rb').read(), 'le'), 'le')[1]
    return src().drm(target)


def cstr(d, o):
    s = o
    while s > 0 and 32 <= d[s - 1] < 127:
        s -= 1
    e = d.find(b'\0', o)
    return s, d[s:e if e >= 0 else len(d)].decode('latin1')


def strings(d):
    out, o = [], 0
    while o < len(d):
        if 32 <= d[o] < 127:
            e = o
            while e < len(d) and 32 <= d[e] < 127:
                e += 1
            if e - o >= 6 and e < len(d) and d[e] == 0:
                out.append((o, d[o:e].decode('latin1')))
            o = e + 1
        else:
            o += 1
    return out


def code_refs(sec, target):
    """[(func index, code offset, opcode)] of code words whose extra word is an internal pointer to TARGET"""
    d, rel = sec['data'], R.parse(sec['reloc'], 'le')
    it = dict(rel.internal)
    out = []
    try:
        W = SC.Walk(d, rel, 'le').run()
    except Exception as ex:
        log('    walker failed for script %d: %s' % (sec['id'], ex), 1)
        return out
    for name, t, n, sz in W.arrays:
        if name != 'funcs':
            continue
        for k in range(n):
            a = t + k * sz
            ct = it.get(a + 0x18)
            if ct is None:
                continue
            cn = struct.unpack_from('<I', d, ct - 4)[0]
            for j in range(cn + 64):
                o = ct + 4 * j
                if o + 4 > len(d):
                    break
                if it.get(o) == target:
                    out.append((k, o - 4, d[o - 1]))
    return out


def main(argv):
    a = list(argv)
    for flag, lvl in (('--trace', 3), ('--debug', 2), ('--verbose', 1)):
        if flag in a:
            LOG['level'] = max(LOG['level'], lvl)
            a.remove(flag)
    icase = '--icase' in a
    if icase:
        a.remove('--icase')
    listw = None
    if '--list' in a:
        i = a.index('--list'); listw = a[i + 1].lower(); del a[i:i + 2]
    ats = []
    if '--at' in a:
        i = a.index('--at'); ats = [int(x, 16) for x in a[i + 1].split(',')]; del a[i:i + 2]
    logdir = os.path.join(HERE, '..', '..', 'local_results', 'script_string_find')
    if '--log' in a:
        i = a.index('--log'); logdir = a[i + 1]; del a[i:i + 2]
    if len(a) < 2:
        print(__doc__)
        return 2
    os.makedirs(logdir, exist_ok=True)
    LOG['fh'] = open(os.path.join(logdir, 'script_string_find_%s.log' % time.strftime('%Y%m%d_%H%M%S')), 'w',
                     encoding='utf-8')
    log('args: %s' % ' '.join(argv), 2)
    targets, texts = a[0].split(','), [t.encode('latin1') for t in a[1:]]
    cache = {}

    def src():
        if 'pc' not in cache:
            import puzzle_switch_scan as PS
            cache['pc'] = PS.Source('pc', None)
        return cache['pc']

    hits = 0
    for tg in targets:
        secs = load(tg, src)
        if not secs:
            log('%s: not found' % tg)
            continue
        scr = [s for s in secs if s['type'] == 8 and s['data']]
        log('%s: %d script sections' % (tg, len(scr)), 1)
        for s in scr:
            d = s['data']
            hay = d.lower() if icase else d
            found = []
            for t in texts:
                needle = t.lower() if icase else t
                o = hay.find(needle)
                while o >= 0:
                    found.append(o)
                    o = hay.find(needle, o + 1)
            if not found:
                continue
            for o in sorted(set(found)):
                st, txt = cstr(d, o)
                refs = code_refs(s, st)
                hits += 1
                log('%s script %d +0x%x: %r' % (tg, s['id'], st, txt))
                for k, co, op in refs:
                    log('    used by func %d code +0x%x (op%02x)' % (k, co, op))
                if not refs:
                    log('    no code word points at +0x%x' % st)
            for o in ats:
                if o < len(d):
                    log('    at +0x%x: %r' % (o, d[o:d.find(b'\0', o)].decode('latin1')))
            if listw:
                for o, txt in strings(d):
                    if listw in txt.lower():
                        log('    string +0x%x %r' % (o, txt), 0)
    log('%d match(es)' % hits)
    return 0 if hits else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
