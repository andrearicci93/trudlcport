"""Read the scripts behind placed objects of one unit (read-only, P5 2026-11-16): intro record, the script class chain
(root +0x18 parent), every member with its type (native name of the type script) and its init block decoded, the
script states, and the code of each non-native class of the chain disassembled with annotations.

Annotations (layouts in ENGINE.md 7.1 / 9, tools/puzzle_switch_scan.py):
  * push member op0c / op0d / op0e / op10, address op0f: `m+N <type> [-> intro id]` resolved in the chain (base members
    sit at the low offsets of the one data block)
  * call words (op65 .. op71): `script S <native> fK` for a function entry, `proto K vt V` for a prototype; when the
    target is a class of this chain also the function that overrides that vtable index
  * internal string pointers, op02 float literals, type-id words (op7e cast)
The output is game data (intro ids, script code) and belongs in a local folder, never in the repository.

Usage (from the repository root):
  ../bin/pyt -t 900 tools/intro_script_read.py UNIT ID[,ID...] [--source pc|xbox] [--file DRM] [--bases N]
        [--obj] [--out DIR] [--verbose] [--debug] [--trace]
  --obj    also print the uber block of the placed object (links, nodes, transitions, command table)
  UNIT    unit name without .drm (PC base archives through tools/puzzle_switch_scan.Source)
  ID       intro ids (uniqueID +0x58) or s<script id> for a bare script of the unit / generalbank
  --file   read the unit from this DRM file instead of the archives
  --bases  disassemble this many classes of the chain (default 3: own class + 2 bases; natives are never code)
  --out    write <UNIT>_<ID>.txt per id there (default only the console); the run log goes to <out>\\logs\\
           intro_script_read_<time>.log, without --out to the system temp folder (intro_script_read_logs)
  --verbose / --debug / --trace  more console output (log file: everything up to debug, trace with --trace)
Exit code: 0 = done, 1 = unit or id not found, 2 = usage error.
"""
import sys, os, struct, time, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drm_reloc as R
import script_conv as SC
import menu_dlc_probe as P
import puzzle_switch_scan as PS
from drm import cdrm_decode, sections_with_data

LOG = {'level': 0, 'fh': None, 'out': None}
CALL_OPS = {0x65, 0x66, 0x67, 0x68, 0x69, 0x6a, 0x6b, 0x6c, 0x6d, 0x6e, 0x6f, 0x70, 0x71}
MEMBER_OPS = {0x0c: 'push m', 0x0d: 'push m', 0x0e: 'push m', 0x0f: 'addr m', 0x10: 'push m'}
LOCAL_OPS = {0x06: 'push l', 0x07: 'push l', 0x08: 'push l', 0x09: 'addr l', 0x0a: 'push l'}
# handlers read from the interpreter jump table 0x57e52c (index opcode - 1): op13 / op15 load a member of the object on
# the stack (null-safe, 0x57d029 / 0x57d06d), op14 its address (0x57d04b); op3e / op3f int add / sub (0x57d996 /
# 0x57d9a8); op43 / op44 / op45 int < / <= / == (setl / setle / sete), op46 byte == (0x57da36 .. 0x57da7e)
NAMES = {0x00: 'line', 0x01: 'pop', 0x02: 'pushf', 0x03: 'push', 0x04: 'push', 0x05: 'pushp', 0x13: 'ld-of-obj',
         0x14: 'm-of-obj', 0x15: 'ld-of-obj', 0x3e: 'add', 0x3f: 'sub',
         0x2e: 'st8', 0x2f: 'st32', 0x31: 'stfstr', 0x43: 'lt', 0x44: 'le', 0x45: 'eq', 0x46: 'eq8',
         0x4f: 'strcmp', 0x50: 'not', 0x51: 'and', 0x52: 'or', 0x63: 'jmp', 0x64: 'jz', 0x65: 'native', 0x66: 'callself',
         0x68: 'own', 0x69: 'callobj', 0x6a: 'vcallobj', 0x6b: 'waitobj', 0x7b: 'ret', 0x7d: 'state', 0x7e: 'cast',
         0x80: 'wait'}


def log(msg, lvl=0):
    if lvl <= LOG['level']: print(msg, flush=True)
    if LOG['fh'] and (lvl <= 2 or LOG['level'] >= 3): LOG['fh'].write(msg + '\n')
    if LOG['out'] and lvl == 0: LOG['out'].write(msg + '\n')


def type_name(pool, sc, m, hint):
    if m['tid'] is None: return 'bt%d' % (m['tag'] & 0xf)
    n = pool.native(m['tid'], hint)
    return n if n else 'script%d' % m['tid']


def inline_inits(sc):
    """{instance offset: value} of the basic-type members whose init is the inline word at entry +0x10 (no init
    block pointer; e.g. the switch base ints, 2026-11-16: 3637 +8 = 1)"""
    out = {}
    mp = sc.it.get(0x2c)
    if mp is None: return out
    n = sc.u32(mp - 4) or 0
    for k in range(min(n, 512)):
        e = mp + 20 * k
        tag = sc.u32(e)
        if tag is None or (tag & 0xf) in (0xa, 0xb) or (e + 16) in sc.it: continue
        off = struct.unpack_from(sc.E + 'H', sc.d, e + 12)[0]
        out[off] = sc.u32(e + 16)
    return out


def init_text(pool, sc, m, hint):
    """the init block of a member: instanceref -> intro id, uberobjectcommand -> object / entry, else raw words"""
    if m['val'] is None:
        v = inline_inits(sc).get(m['off'])
        return ('inline %d' % (v - (1 << 32) if v >= 0x80000000 else v)) if v is not None else ''
    tn = type_name(pool, sc, m, hint)
    if tn == 'instanceref': return '-> intro %s' % sc.value32(m['val'], 0)
    if tn == 'uberobjectcommand': return 'object %s entry %s' % (sc.value32(m['val'], 0), sc.value32(m['val'], 1))
    ws = []
    for k in range(3):
        w = sc.u32(m['val'] + 4 * k)
        if w is None: break
        f = struct.unpack(sc.E + 'f', struct.pack(sc.E + 'I', w))[0]
        ws.append('0x%x%s' % (w, (' (%g)' % f) if w and 1e-4 < abs(f) < 1e7 else ''))
    s = P.cstr(sc.d, m['val'])
    if s and len(s) > 2 and all(32 <= ord(c) < 127 for c in s): ws.append(repr(s[:40]))
    return 'init ' + ' '.join(ws)


def member_text(pool, chain, off, hint, refs):
    for sc in chain:
        for k, m in enumerate(sc.members):
            if m['off'] == off:
                t = 'm+%d %s (class %d m%d)' % (off, type_name(pool, sc, m, hint), sc.id, k)
                if off in refs: t += ' -> intro %d' % refs[off][0]
                return t
    return 'm+%d ?' % off


def callee_text(pool, sc, x, chain, hint):
    """text for one call / pointer extra word"""
    if x in sc.it:
        tt = sc.it[x]
        f = sc.func_at(tt)
        if f is not None: return 'own f%d' % f['k']
        if tt in sc.protos:
            pk, vt = sc.protos[tt]
            return 'own proto %d vt %d' % (pk, vt)
        s = P.cstr(sc.d, tt)
        if s and all(32 <= ord(c) < 127 for c in s): return 'str %r' % s[:70]
        return 'int 0x%x' % tt
    if x in sc.ext:
        ty, tid, doff = sc.ext[x]
        if ty != 8: return 'ext type%d id %d +0x%x' % (ty, tid, doff)
        T = pool.get(tid, hint)
        if T is None: return 'script %d +0x%x (not found)' % (tid, doff)
        nm = T.native or ''
        f = T.func_at(doff)
        if f is not None:
            vt = T.protos.get(f['proto'], (None, None))[1] if f['proto'] is not None else None
            return 'script %d %s f%d%s%s' % (tid, nm, f['k'], ' vt %d' % vt if vt not in (None, 0xffff) else '',
                                             ' (native)' if f['code'] is None else '')
        if doff in T.protos:
            pk, vt = T.protos[doff]
            ov = ''
            if vt != 0xffff:
                for c in chain:
                    g = next((q for q in c.funcs if q['proto'] in c.protos and c.protos[q['proto']][1] == vt
                              and q['code'] is not None), None)
                    if g is not None: ov = ' -> runs class %d f%d' % (c.id, g['k']); break
            return 'script %d %s proto %d vt %d%s' % (tid, nm, pk, vt, ov)
        return 'script %d %s +0x%x' % (tid, nm, doff)
    if x in sc.ids: return 'type-id %d' % sc.u32(x)
    return None


def dis(pool, sc, chain, hint, refs):
    log('  -- class %d (native %s, parent %s) functions %d, states %d' % (
        sc.id, sc.native, sc.parent, len(sc.funcs), len(sc.state_funcs)))
    for k, a in enumerate(sc.state_funcs):
        f = sc.func_at(a) if a is not None else None
        log('     state %d -> f%s' % (k, f['k'] if f else None))
    for f in sc.funcs:
        vt = sc.protos.get(f['proto'], (None, None))[1] if f['proto'] is not None else None
        pk = sc.protos.get(f['proto'], (None, None))[0] if f['proto'] is not None else None
        nm = struct.unpack_from(sc.E + 'H', sc.d, f['proto'] + 8)[0] if f['proto'] is not None and f['proto'] + 10 <= len(sc.d) else None
        log('\n  == class %d f%d proto %s vt %s name sym %s, %d words%s, locals %s' % (
            sc.id, f['k'], pk, vt, nm, f['n'] or 0, '' if f['code'] is not None else ' (native)',
            ['l+%d %s%s' % (m['off'], type_name(pool, sc, m, hint),
                            (' ' + init_text(pool, sc, m, hint)) if m['val'] is not None else '') for m in f['locals']]))
        cast = None
        for o, op, arg, ex in sc.code(f):
            sarg = arg if arg < 0x800000 else arg - 0x1000000
            ann = []
            if op in MEMBER_OPS: ann.append(member_text(pool, chain, arg, hint, refs))
            if op in LOCAL_OPS:
                m = next((q for q in f['locals'] if q['off'] == arg), None)
                ann.append('l+%d %s' % (arg, type_name(pool, sc, m, hint) if m else 'arg/tmp'))
            if op in (0x63, 0x64):              # 0x57de10 / 0x57de22: pc (already past the word) += 4 * s24
                ann.append('-> %04x' % (o + 4 + 4 * sarg))
            if op in (0x13, 0x14, 0x15): ann.append('member +%d of the object on the stack' % arg)
            if op == 0x7e and ex and ex[0] in sc.ids: cast = sc.u32(ex[0])
            for x in ex:
                # a virtual call on a popped object runs the override of the object's class (the last cast), a self
                # call the override in this chain
                tch = pool.chain(cast, hint) if op in (0x69, 0x6a, 0x6b, 0x6f, 0x70, 0x71) and cast else chain
                t = callee_text(pool, sc, x, tch, hint)
                if t is None:
                    w = sc.u32(x)
                    if op == P.PUSHF:
                        t = 'float %g' % struct.unpack(sc.E + 'f', struct.pack(sc.E + 'I', w))[0]
                    else:
                        t = 'raw 0x%x' % w
                ann.append(t)
            if op == 0x00:
                log('  %04x  ----- line %d' % (o, arg), 1)
                continue
            log('  %04x  op%02x %-9s %6d  %s' % (o, op, NAMES.get(op, ''), sarg, ' | '.join(ann)))


def main(argv):
    def flag(k):
        if k in argv: argv.remove(k); return True
        return False

    def opt(k, d=None):
        if k in argv:
            i = argv.index(k); v = argv[i + 1]; del argv[i:i + 2]; return v
        return d
    if flag('--trace'): LOG['level'] = 3
    elif flag('--debug'): LOG['level'] = 2
    elif flag('--verbose'): LOG['level'] = 1
    show_obj = flag('--obj')
    src_key = opt('--source', 'pc'); fpath = opt('--file'); bases = int(opt('--bases', '3')); out = opt('--out')
    if len(argv) < 2:
        print(__doc__); return 2
    unit, ids = argv[0].lower(), argv[1].split(',')
    logdir = os.path.join(out, 'logs') if out else os.path.join(tempfile.gettempdir(), 'intro_script_read_logs')
    os.makedirs(logdir, exist_ok=True)
    LOG['fh'] = open(os.path.join(logdir, 'intro_script_read_%s.log' % time.strftime('%Y%m%d_%H%M%S')), 'w',
                     encoding='utf-8')
    log('# intro_script_read %s %s source %s file %s' % (unit, ','.join(ids), src_key, fpath), 2)
    S = PS.Source(src_key, None)
    if fpath:
        secs = sections_with_data(cdrm_decode(open(fpath, 'rb').read(), S.e), S.e)[1]
    else:
        secs = S.drm(unit)
    if not secs:
        log('unit %s not found' % unit); return 1
    intros = PS.intros_of(secs, S.e, S.names) or []
    log('unit %s: %d intros, %d script sections' % (unit, len(intros), sum(1 for s in secs if s['type'] == 8)), 1)
    pool = PS.Pool(S); pool.add_drm(secs)
    rc = 0
    for s in ids:
        if out: LOG['out'] = open(os.path.join(out, '%s_%s.txt' % (unit, s)), 'w', encoding='utf-8')
        if s.startswith('s'):
            sid = int(s[1:]); it_ = None
            log('# script %d (unit %s)' % (sid, unit))
        else:
            it_ = next((q for q in intros if q['uid'] == int(s)), None)
            if it_ is None:
                log('# intro %s: not in unit %s' % (s, unit)); rc = 1; continue
            sid = it_['script']
            log('# intro %d idx %d object %d %s pos %.1f %.1f %.1f script %d' % (
                it_['uid'], it_['idx'], it_['obj'], it_['name'], it_['pos'][0], it_['pos'][1], it_['pos'][2], sid))
        chain = pool.chain(sid, secs)
        if not chain:
            log('  script %d not found' % sid); rc = 1; continue
        refs = {}
        for sc in chain:
            for m in sc.members:
                if m['tid'] is not None and pool.native(m['tid'], secs) == 'instanceref' and m['off'] not in refs:
                    refs[m['off']] = (sc.value32(m['val'], 0), sc)
        for d, sc in enumerate(chain):
            log('  chain %d: class %d native %s, %d members, %d functions (%d with code)' % (
                d, sc.id, sc.native, len(sc.members), len(sc.funcs), sum(1 for f in sc.funcs if f['code'] is not None)))
            for k, m in enumerate(sc.members):
                log('     m%d +%d %s %s' % (k, m['off'], type_name(pool, sc, m, secs), init_text(pool, sc, m, secs)))
        if it_ is not None and show_obj:
            oi = PS.ObjInfo(S.drm(it_['name']), S.e)
            log('  object %s: %s (DTP %s)' % (it_['name'], oi.type_text(), oi.dtp))
            for k, D in enumerate(oi.descs):
                log('   link %d start node %s' % (k, D['start']))
                for q, nd in enumerate(D['nodes']):
                    log('     node %d %s actions %s' % (q, nd['name'], nd['acts']))
                    for to, c, a in nd['trans']:
                        log('       -> %s (%s) on %s' % (
                            to, D['nodes'][to]['name'] if to is not None and to < len(D['nodes']) else '?',
                            PS.trig(c, a, D['nodes'])))
            for n, recs in enumerate(oi.cmds):
                log('   command entry %d: %s' % (n, ['link %d %s %d' % (r[0], PS.KIND.get(r[1], r[1]), r[2]) for r in recs]))
        for sc in chain[:bases]:
            if sc.native and s.startswith('s') is False: continue      # native classes only when asked for directly
            dis(pool, sc, chain, secs, refs)
        if LOG['out']: LOG['out'].close(); LOG['out'] = None
    if LOG['fh']: LOG['fh'].close()
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
