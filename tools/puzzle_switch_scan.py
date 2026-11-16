r"""Static scan of switch-like objects in every level unit: what each switch / lever / button / press plate / crank /
wheel (and every other placed object whose script drives an uber / multibody object) targets, which uber command it
sends, what the target is (state machine, multibody with joints, no state) and whether the target is one-shot or
cyclic. Read-only (P4, 2026-11-16; for the planned TruMenu "puzzles nearby" hints, ENGINE.md 9 "Switch -> target").

The RESULT is game data (intro ids, object names, positions) and stays local (default <workspace>/local_results/p4_switches, outside the repository);
only this tool and the general rules (ENGINE.md / TRU-Knowledge.md) belong in the repository.

Data used (all proven layouts, ENGINE.md 9 / 11 / TruLink README "Objects (0.4)"):
  * unit DTP (Level +0x74): intro records 0x90 B (+0x10 position, +0x50 u16 object id, +0x58 intro id, +0x7c script id
    of the placed instance = a type-8 section of the unit DRM)
  * instance script members (root +0x2c, 20 B {+0 tag, +4 u16 userType, +8 type script id, +0xc u16 offset, +0x10 init});
    a member whose type script is the native `instanceref` holds the target intro id in its init block (value word 0,
    a u32 in the file's byte order on Xbox and PC)
  * script code (opcode = top byte, operand = low 24 bits, extra words by script_conv.Walk.EXTRA): `op0f N` pushes the
    member at +N, a call of `instanceref` f7 / f6 binds it, `op7e` casts it to the target's script type and the next
    call of a prototype (protos array, 28 B, +6 u16 vtable index) of a script C runs C's function on the target
  * the called function of the target's class sends an uber command when it pushes an `uberobjectcommand` member /
    local (init {object id, command table entry n, 0}) and calls `uberobjectbase` f1 (native); followed on the way:
    `op7d` (enter script state <pushed number>, function = root +0x40[state]) and calls of the script's own functions
    / prototypes (depth <= 4); the override with the same vtable index in the target's script chain (parent = root
    +0x18) runs first
  * relations per (object, target): command (decoded entry n), call (a target function without an uber command),
    reads (`op14` member of the target's script), sets / gets sticky (`instanceref` f9 / f15), ref (another
    instanceref native), bind only (bound, but stored / passed on - not decoded)
  * object data DTP of the target object's DRM: +0xc8 -> uber block (magic 0x8080b00b at +4, two u16: Xbox reads
    0xb00b8080): +8 DESC count / +0xc DESC array (0x54 B; link k of the multibody = DESC k), +0x10 command table count / +0x14 entries 12 B {?, +4 record
    count, +8 records 12 B {link, message kind, value}}; DESC +4 node count / +8 nodes 28 B (+8 name, +0xc / +0x10
    transitions, +0x14 / +0x18 actions 16 B, action kind 9 = joint), +0x14 start node; transition +0 from, +4 to,
    +0x18 condition, +0x1c argument
  * message kind 1 = set node, 2 = event (fires a transition whose condition == value), 3 = broadcast (condition 13,
    argument == value), 4 = command (condition 16, argument == value)

Behaviour of a target DESC (rules in ENGINE.md 9, from the graph alone):
  one-shot      no cycle reachable from the start node (the target ends in a node without a way back)
  cyclic ring   a cycle of >= 3 stable nodes driven by ONE trigger (each use advances one position, e.g. pillars a..d)
  toggle        a cycle with 2 stable nodes and one trigger (the same use flips it back)
  repeatable    a cycle with 1 stable node and one trigger (a reaction that plays and returns, e.g. a hit animation)
  reversible    a cycle that needs two different triggers (open by command 1, close by command 0)
  auto-reset    a cycle closed by a time condition (open -> closed after n s) after one trigger
  passive       no transition at all / only internal conditions (time, immediately, object check)
  (stable node = a node without a way out on "immediately", time or a joint range; a command-table record "set node v"
  adds an edge from every node to v; "start -> ..." when the start node lies before the cycle)

Usage (from the repository root):
  ../bin/pyt -t 3600 tools/puzzle_switch_scan.py [--source pc,dlc,xbox] [--out DIR] [--dlc-dir MODS] [--units a,b]
        [--verbose] [--debug] [--trace]
  --source  pc   = PC base game (data/pc patch.000 first, then bigfile.000), units levels\*
            dlc  = PC DLC 1 + DLC 2 units (dlc\dlc_level1\*, dlc\dlc_level2\*, imf\dlc2_*) from MODS (default env
                   TRU_GAME_MODS = the installed game mods folder; objects not there from the PC base archives)
            xbox = Xbox base game (data/TombRaiderUnderworld_Patched: title update first, then layer1 / layer2), for
                   comparison with pc (pairs by unit, object name and position)
  --units   only these unit names (comma list, without .drm)
  --out     output folder (default env TRUDLC_LOCAL_OUT, else <workspace>/local_results/p4_switches): <source>_switches.csv, <source>_<level>.md,
            summary.md (+ compare_pc_xbox.md with both pc and xbox), logs\puzzle_switch_scan_<time>.log
  --verbose / --debug / --trace  more console output (the log file always gets the debug lines; trace adds every
            decoded call)
Exit code: 0 = done, 1 = a source could not be read, 2 = usage error.
"""
import sys, os, re, csv, time, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drm_reloc as R
import script_conv as SC
import menu_dlc_probe as P
import objlists as OL
from drm import cdrm_decode, sections_with_data
from archive import Archive
from names import crc

DEFAULT_OUT = os.environ.get('TRUDLC_LOCAL_OUT') or os.path.join(HERE, '..', '..', 'local_results', 'p4_switches')  # outside the repo
GAME_MODS = os.environ.get('TRU_GAME_MODS', '')        # installed game mods folder (same variable as character_anim_report)
LISTS = os.path.join(HERE, '..', 'work', 'generic', 'lists')
MERGED = os.path.join(HERE, '..', 'work', 'generic', 'merged', 'tr8', 'pc-w')
PC_ARCH = ['../data/pc/patch.000', '../data/pc/bigfile.000']
XB_ARCH = ['../data/TombRaiderUnderworld_Patched/' + f for f in ('TitleUpdate.000', 'layer1.000', 'layer2.000')]
UBER_MAGIC = 0x8080b00b
UBER_MAGIC_BE = 0xb00b8080                # the same two u16 halves read as a big-endian u32 (Xbox files)
NAME_KINDS = (('press_plate', 'press plate'), ('pressplate', 'press plate'), ('lever', 'lever'), ('button', 'button'),
              ('crank', 'crank'), ('wheel', 'wheel'), ('switch', 'switch'))
COND = {1: 'time', 2: 'event 2', 3: 'immediately', 9: 'object check', 10: 'cond 10', 11: 'flags', 12: 'flags',
        13: 'broadcast', 14: 'joint range enter', 15: 'joint range leave', 16: 'command', 17: 'damage', 18: 'damage',
        19: 'damage kind', 6: 'hit', 7: 'hit', 8: 'hit'}
INTERNAL = {1, 3, 9, 10, 11, 12, 14, 15}  # conditions the object reaches itself (time, immediately, object check, flags,
#                                           its own joint reaching a range after a node action drove the motor)
TRANSIT = {1, 3, 14, 15}                  # a node with such a way out is a passage (opening, Raise), not a stable state
SET = -1                                  # pseudo condition: a command table record "set node" (kind 1)
KIND = {1: 'set node', 2: 'event', 3: 'broadcast', 4: 'command'}

# ---------------------------------------------------------------- logging (-Verbose / -Debug / -Trace equivalents)
LOG = {'level': 0, 'fh': None}
STATS = collections.Counter()             # layout tallies, printed per source (DESC stride, object DTPs with an uber block)


def log(msg, lvl=0):
    """lvl 0 = always, 1 = verbose, 2 = debug, 3 = trace; the log file gets everything up to debug (trace with --trace)"""
    if lvl <= LOG['level']: print(msg, flush=True)
    if LOG['fh'] and (lvl <= 2 or LOG['level'] >= 3):
        LOG['fh'].write(msg + '\n')


# ---------------------------------------------------------------- data sources
class Source:
    """one game build: DRM lookup by name, object names, unit list"""

    def __init__(self, key, dlc_dir):
        self.key = key
        self.e = 'be' if key == 'xbox' else 'le'
        self.pre = 'xenon-w' if key == 'xbox' else 'pc-w'
        self.arch = [Archive(p, self.e) for p in (XB_ARCH if key == 'xbox' else PC_ARCH)]
        self.dir = dlc_dir if key == 'dlc' else None
        if key == 'xbox':
            ol, ul = os.path.join(LISTS, 'xboxtu_objectlist.txt'), os.path.join(LISTS, 'xboxtu_unitlist.txt')
        elif key == 'dlc':
            ol = os.path.join(dlc_dir, 'tr8', 'pc-w', 'objectlist.txt')
            if not os.path.isfile(ol): ol = os.path.join(MERGED, 'objectlist.txt')
            ul = os.path.join(MERGED, 'unitlist.txt')
        else:
            ol, ul = os.path.join(LISTS, 'pc_objectlist.txt'), os.path.join(LISTS, 'pc_unitlist.txt')
        self.names = OL.read_objectlist(open(ol, 'rb').read())
        self.units = []
        for line in open(ul, 'rb').read().decode('latin1').split('\r\n')[1:]:
            p = line.strip().lower()
            if not p: continue
            grp = unit_group(p)
            if grp is None: continue
            if (key == 'dlc') != grp.startswith('dlc'): continue
            self.units.append((p.split('\\')[-1], grp))
        self.cache = {}

    def drm(self, name):
        """[section dict] of NAME (without .drm) or None"""
        if name in self.cache: return self.cache[name]
        raw = None
        if self.dir:
            f = os.path.join(self.dir, name + '.drm')
            if os.path.isfile(f): raw = open(f, 'rb').read()
        if raw is None:
            h = crc(self.pre + '\\' + name + '.drm')
            for a in self.arch:
                r = [x for x in a.find(h) if x['spec'] == 0xffffffff]
                if r: raw = a.read(r[0]); break
        secs = None
        if raw is not None:
            try:
                secs = sections_with_data(cdrm_decode(raw, self.e), self.e)[1]
            except Exception as ex:
                log('  cannot read %s: %s' % (name, ex), 1)
        self.cache[name] = secs
        return secs


def unit_group(path):
    """'l3' / 'dlc1' / 'dlc2' / None (containers, cine-only units, costumes); base levels by the unit name prefix (the
    l7 units sit in the levels\\l5 folder)"""
    if path.startswith('levels\\'):
        m = re.match(r'(l\d)_', path.split('\\')[-1])
        return m.group(1) if m else 'levels'
    if path.startswith('dlc\\dlc_level1\\'): return 'dlc1'
    if path.startswith('dlc\\dlc_level2\\') or path.startswith('imf\\dlc2_'): return 'dlc2'
    return None


# ---------------------------------------------------------------- scripts
class Script:
    """one type-8 section: members, prototypes, functions with code, locals"""

    def __init__(self, sec, secs, e):
        self.id = sec['id']; self.e = e; self.E = '>' if e == 'be' else '<'
        d = self.d = bytes(sec['data'])
        rel = R.parse(bytes(sec['reloc']), e)
        self.it = dict(rel.internal)
        self.ext = {so: (secs[si]['type'], secs[si]['id'], do) for si, so, do in rel.external if si < len(secs)}
        self.ids = rel.id_offsets()
        self.native = P.cstr(d, self.it[0x10]) if 0x10 in self.it else None
        self.parent = self.u32(0x18) if 0x18 in self.ids else None
        self.members, self.protos, self.funcs, self.state_funcs = [], {}, [], []
        try:
            W = SC.Walk(d, rel, e).run()
        except Exception:
            return
        for name, t, n, sz in W.arrays:
            if name == 'members':
                self.members = [self.member(t + k * sz) for k in range(n)]
            elif name == 'protos':
                for k in range(n):
                    a = t + k * sz
                    self.protos[a] = (k, struct.unpack_from(self.E + 'H', d, a + 6)[0])
        ns = next((n for name, t, n, sz in W.arrays if name == 'states'), 0)
        sf = self.it.get(0x40)                 # root +0x40: one function entry per script state (op7d enters it)
        self.state_funcs = [self.it.get(sf + 4 * k) for k in range(ns)] if sf is not None else []
        for name, t, n, sz in W.arrays:
            if name != 'funcs': continue
            for k in range(n):
                a = t + k * sz
                ct = self.it.get(a + 0x18)
                lt = self.it.get(a + 12)
                nl = self.u32(lt - 4) if lt is not None else 0
                self.funcs.append(dict(k=k, a=a, proto=self.it.get(a), code=ct,
                                       n=self.u32(ct - 4) if ct is not None else 0,
                                       locals=[self.member(lt + 20 * q) for q in range(nl or 0)] if lt is not None else []))

    def u32(self, o):
        return struct.unpack_from(self.E + 'I', self.d, o)[0] if 0 <= o <= len(self.d) - 4 else None

    def member(self, a):
        tag, ut = struct.unpack_from(self.E + 'IH', self.d, a)
        off = struct.unpack_from(self.E + 'H', self.d, a + 12)[0]
        tid = None
        if a + 8 in self.ids: tid = self.u32(a + 8)
        elif a + 8 in self.it and self.it[a + 8] in self.ids: tid = self.u32(self.it[a + 8])
        ini = self.it.get(a + 16)
        val = None
        if ini is not None:
            val = self.it.get(ini, ini)
        return dict(off=off, tag=tag, ut=ut, tid=tid, val=val)

    def value32(self, val, k):
        """value word k of an init block as a number: the instanceref intro id (a u32 in both byte orders; PC u16 +
        u16 0 reads the same), the uberobjectcommand object id / entry; a word > 0xffff is taken as a u16 pair"""
        if val is None: return None
        v = self.u32(val + 4 * k)
        if v is None: return None
        if v > 0xffff: v = (v >> 16) if self.e == 'be' else (v & 0xffff)
        return v

    def func_at(self, entry):
        return next((f for f in self.funcs if f['a'] == entry), None)

    def code(self, f):
        """(offset, op, arg, [extra word offsets]) of a function's code"""
        ct, n, j = f['code'], f['n'] or 0, 0
        if ct is None: return
        while j < n:
            o = ct + 4 * j
            w = self.u32(o)
            if w is None: return
            op = w >> 24; arg = w & 0xffffff
            extra = SC.Walk.EXTRA.get(op, 1 if op == P.PUSHF else 0)
            yield o, op, arg, [o + 4 * q for q in range(1, extra + 1)]
            j += 1 + extra


class Pool:
    """scripts by id for one source; looked up in the given DRM section lists, then in every DRM loaded so far"""

    def __init__(self, src):
        self.src = src; self.by_id = {}; self.secs_of = {}; self.loaded = []

    def add_drm(self, secs):
        if secs is None or any(s is secs for s in self.loaded): return
        self.loaded.append(secs)
        for s in secs:
            if s['type'] == 8 and s['data'] and s['id'] not in self.secs_of:
                self.secs_of[s['id']] = (s, secs)

    def get(self, sid, hint=None):
        if sid is None: return None
        if sid in self.by_id: return self.by_id[sid]
        if hint is not None: self.add_drm(hint)
        if sid not in self.secs_of:
            gb = self.src.drm('generalbank')
            self.add_drm(gb)
        if sid not in self.secs_of: self.by_id[sid] = None; return None
        s, secs = self.secs_of[sid]
        self.by_id[sid] = Script(s, secs, self.src.e)
        return self.by_id[sid]

    def native(self, sid, hint=None):
        sc = self.get(sid, hint)
        return sc.native if sc else None

    def chain(self, sid, hint=None):
        """the script and its parents (root +0x18), at most 8"""
        out = []
        while sid is not None and len(out) < 8:
            sc = self.get(sid, hint)
            if sc is None or sc in out: break
            out.append(sc)
            sid = sc.parent if sc.parent != sc.id else None
        return out


# ---------------------------------------------------------------- object data (uber block)
class ObjInfo:
    """uber block of an object's data DTP: DESCs (links), nodes, transitions, joints, command table"""

    def __init__(self, secs, e):
        self.descs = []; self.cmds = []; self.dtp = None
        E = '>' if e == 'be' else '<'
        for s in secs or []:
            if s['type'] != 7 or not s['data']: continue
            d = bytes(s['data']); it = dict(R.parse(bytes(s['reloc']), e).internal)
            u = lambda o: struct.unpack_from(E + 'I', d, o)[0] if 0 <= o <= len(d) - 4 else None
            U = it.get(0xc8)
            if U is None or u(U + 4) not in (UBER_MAGIC, UBER_MAGIC_BE): continue
            nd = u(U + 8) or 0; D0 = it.get(U + 0xc)
            stride = None
            for st in (0x54, 0x60):
                if D0 is not None and nd and all(it.get(D0 + st * m + 8) is not None and 1 <= (u(D0 + st * m + 4) or 0) <= 64
                                                 for m in range(nd)):
                    stride = st; break
            STATS['desc stride 0x%x' % stride if stride else 'desc stride unknown'] += 1
            if stride is None: continue
            self.dtp = s['id']
            for m in range(nd):
                D = D0 + stride * m
                nodes = []; nn = u(D + 4); nb0 = it[D + 8]
                for q in range(nn):
                    nb = nb0 + 28 * q
                    nm = P.cstr(d, it[nb + 8]) if nb + 8 in it else '?'
                    tr = []
                    ta = it.get(nb + 0x10)
                    for j in range(u(nb + 0xc) or 0):
                        tt = it.get(ta + 4 * j) if ta is not None else None
                        if tt is None or tt + 0x20 > len(d): continue
                        c = u(tt + 0x18); a = u(tt + 0x1c)
                        if c == 1: a = round(struct.unpack_from(E + 'f', d, tt + 0x1c)[0], 2)
                        tr.append((u(tt + 4), c, a))
                    acts = []
                    ac = it.get(nb + 0x18)
                    for j in range(u(nb + 0x14) or 0):
                        if ac is not None: acts.append(u(ac + 0x10 * j))
                    nodes.append(dict(name=nm, trans=tr, acts=acts))
                self.descs.append(dict(nodes=nodes, start=u(D + 0x14)))
            cnt = u(U + 0x10) or 0; lst = it.get(U + 0x14)
            for c in range(min(cnt, 64)):
                eo = lst + 12 * c if lst is not None else None
                recs = []
                if eo is not None and eo + 12 <= len(d):
                    rn = u(eo + 4) or 0; r = it.get(eo + 8)
                    for j in range(min(rn, 32)):
                        if r is not None and r + 12 * j + 12 <= len(d):
                            recs.append(struct.unpack_from(E + 'iII', d, r + 12 * j))
                self.cmds.append(recs)
            break

    def joints(self):
        return sum(a == 9 for D in self.descs for n in D['nodes'] for a in n['acts'])

    def type_text(self):
        if not self.descs: return 'no state (script / animation only)'
        j = self.joints()
        if len(self.descs) > 1 or j:
            return 'multibody (%d links, %d joints, %d commands)' % (len(self.descs), j, len(self.cmds))
        return 'uber state machine (%d nodes, %d commands)' % (len(self.descs[0]['nodes']), len(self.cmds))

    def short_type(self):
        if not self.descs: return 'none'
        return 'multibody' if len(self.descs) > 1 or self.joints() else 'uber'


def fires(desc, kind, value):
    """[(from node, to node)] a message {kind, value} starts in this DESC (any node)"""
    out = []
    for k, n in enumerate(desc['nodes']):
        if kind == 1:
            continue
        for to, c, a in n['trans']:
            if (kind == 2 and c == value) or (kind == 3 and c == 13 and a == value) or (kind == 4 and c == 16 and a == value):
                out.append((k, to)); break
    return out


def trig(c, a, nodes=None):
    if c == SET: return 'set node %s' % (nodes[a]['name'] if nodes and a < len(nodes) else a)
    if c == 16: return 'command %s' % a
    if c == 13: return 'broadcast %s' % a
    if c in (14, 15): return COND[c]
    if c in (6, 7, 8, 17, 18, 19): return '%s (cond %d)' % (COND[c], c)
    return 'event %d' % c                 # message kind 2 value v fires a transition whose condition == v


def behaviour(desc, setnodes=()):
    """one-shot / cyclic ring / toggle / reversible / auto-reset / passive of one DESC (rules in the docstring);
    setnodes = nodes the object's command table can set directly (an edge from every node)"""
    nodes = desc['nodes']; n = len(nodes); st = desc['start'] if desc['start'] is not None and desc['start'] < n else 0
    edges = [(k, to, c, a) for k, nd in enumerate(nodes) for to, c, a in nd['trans'] if to is not None and to < n]
    edges += [(k, v, SET, v) for v in sorted(set(setnodes)) if v < n for k in range(n) if k != v]
    if not edges: return 'passive (no transition)'
    adj = collections.defaultdict(list)
    for e in edges: adj[e[0]].append(e)
    seen = {st}; todo = [st]
    while todo:
        k = todo.pop()
        for _, to, _, _ in adj[k]:
            if to not in seen: seen.add(to); todo.append(to)
    # strongly connected components (Tarjan, iterative enough for <= 64 nodes)
    index = {}; low = {}; stack = []; on = set(); comps = []; cnt = [0]

    def sc(v):
        index[v] = low[v] = cnt[0]; cnt[0] += 1; stack.append(v); on.add(v)
        for _, w, _, _ in adj[v]:
            if w not in index:
                sc(w); low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = set()
            while True:
                w = stack.pop(); on.discard(w); comp.add(w)
                if w == v: break
            comps.append(comp)
    for v in sorted(seen):
        if v not in index: sc(v)
    cyc = [c for c in comps if len(c) > 1 or any(to == next(iter(c)) for _, to, _, _ in adj[next(iter(c))])]
    ext_all = {(c, a) for _, _, c, a in edges if c not in INTERNAL}
    if not cyc:
        if not ext_all: return 'passive (internal conditions only)'
        return 'one-shot'
    comp = next((c for c in cyc if st in c), None)
    pre = ''
    if comp is None:
        comp = cyc[0]; pre = 'start -> '
    ce = [e for e in edges if e[0] in comp and e[1] in comp]
    ext = {(c, a) for _, _, c, a in ce if c not in INTERNAL}
    timer = any(c == 1 for _, _, c, _ in ce)
    stable = [k for k in comp if not any(c in TRANSIT for _, _, c, _ in adj[k])]
    names = '/'.join(nodes[k]['name'] for k in sorted(stable)) if stable else ''
    tx = lambda s: ', '.join(trig(c, a, nodes) for c, a in sorted(s))
    if not ext:
        return pre + ('loop (internal conditions only)' + (', timer' if timer else ''))
    if timer and len(stable) <= 1 + (len(ext) > 1):
        return pre + 'auto-reset (timer) after %s' % tx(ext)
    if len(ext) == 1:
        if len(stable) >= 3: return pre + 'cyclic ring (%d positions %s) on %s' % (len(stable), names, tx(ext))
        if len(stable) <= 1: return pre + 'repeatable (returns to %s) on %s' % (names or '?', tx(ext))
        return pre + 'toggle (%s) on %s' % (names, tx(ext))
    return pre + 'reversible (%s) by %s' % (names, tx(ext)) + (', timer' if timer else '')


# ---------------------------------------------------------------- per-intro analysis
def intros_of(secs, e, names):
    """[dict(idx, uid, obj, name, pos, script)] of a unit DRM, or None"""
    E = '>' if e == 'be' else '<'
    if not secs: return None
    rl = R.parse(bytes(secs[0]['reloc']), e)
    tgt = [si for si, so, do in rl.external if so == 0x74]
    if not tgt: return None
    u = secs[tgt[0]]; d = bytes(u['data'])
    it = dict(R.parse(bytes(u['reloc']), e).internal)
    if 0x10 not in it or len(d) < 0x14: return None
    n = struct.unpack_from(E + 'I', d, 0xc)[0]; a = it[0x10]
    out = []
    for k in range(min(n, 8192)):
        o = a + 0x90 * k
        if o + 0x90 > len(d): break
        obj = struct.unpack_from(E + 'H', d, o + 0x50)[0]
        out.append(dict(idx=k, uid=struct.unpack_from(E + 'I', d, o + 0x58)[0], obj=obj, name=names.get(obj, '?%d' % obj),
                        pos=struct.unpack_from(E + '3f', d, o + 0x10), script=struct.unpack_from(E + 'I', d, o + 0x7c)[0]))
    return out


def name_kind(nm):
    low = nm.lower()
    for k, v in NAME_KINDS:
        if k in low: return v
    if low.startswith('triggervolume') or low.startswith('triggerplane') or 'trigger' in low:
        return 'trigger plane' if 'plane' in low else 'trigger volume'
    return None


class Unit:
    def __init__(self, name, grp, secs, intros):
        self.name, self.grp, self.secs, self.intros = name, grp, secs, intros


def refs_of(pool, unit, it_):
    """{member offset: target intro id} of the instanceref members of the intro's script (and its parents)"""
    out = {}
    for sc in pool.chain(it_['script'], unit.secs) if it_['script'] else []:
        for m in sc.members:
            if m['tid'] is None or m['off'] in out: continue
            if pool.native(m['tid'], unit.secs) != 'instanceref': continue
            v = sc.value32(m['val'], 0)
            if v not in (None, 0, 0xffff): out[m['off']] = (v, sc)
    return out


def member_at(pool, chain, off, f=None):
    """(member dict, script) at instance offset off in the chain, or the function local at frame offset off"""
    for sc in chain:
        for m in sc.members:
            if m['off'] == off: return m, sc
    return None, None


def sends_of(pool, sc, f, hint, depth=0, seen=None):
    """[(kind, text, entry n)] uber calls of a function: ('command', ..., n) for uberobjectbase f1 with an
    uberobjectcommand argument, ('uber', 'fK', None) for other uberobjectbase natives; follows calls into the same script
    (depth <= 3)"""
    seen = seen if seen is not None else set()
    if f is None or (sc.id, f['a']) in seen or depth > 4: return []
    seen.add((sc.id, f['a']))
    chain = pool.chain(sc.id, hint)
    out = []; last = None; num = None
    for o, op, arg, ex in sc.code(f):
        if op == 0x0f: last = ('m', arg)
        elif op == 0x09: last = ('l', arg)
        elif op == 0x04: num = arg
        elif op == 0x7d:                       # enter script state <pushed number>: its function runs next
            for k, sa in enumerate(sc.state_funcs):
                if sa is not None and (num is None or k == num):
                    out += sends_of(pool, sc, sc.func_at(sa), hint, depth + 1, seen)
        for x in ex:
            if x in sc.it and sc.func_at(sc.it[x]) is not None:      # call of a function of the same script
                out += sends_of(pool, sc, sc.func_at(sc.it[x]), hint, depth + 1, seen)
                continue
            if x in sc.it and sc.it[x] in sc.protos:                 # call of a prototype of the same script
                g = next((q for q in sc.funcs if q['proto'] == sc.it[x] and q['code'] is not None), None)
                out += sends_of(pool, sc, g, hint, depth + 1, seen)
                continue
            if x not in sc.ext or sc.ext[x][0] != 8: continue
            tid, doff = sc.ext[x][1], sc.ext[x][2]
            T = pool.get(tid, hint)
            if T is None: continue
            if T.native == 'uberobjectbase':
                fi = T.func_at(doff)
                k = fi['k'] if fi else None
                m = None
                if last and last[0] == 'm': m, _ = member_at(pool, chain, last[1])
                elif last and last[0] == 'l': m = next((q for q in f['locals'] if q['off'] == last[1]), None)
                mn = pool.native(m['tid'], hint) if m and m['tid'] is not None else None
                if k == 1 and mn == 'uberobjectcommand':
                    n = sc.value32(m['val'], 1); obj = sc.value32(m['val'], 0)
                    out.append(('command', 'object %s entry %s' % (obj, n), n))
                else:
                    out.append(('uber', 'uberobjectbase f%s(%s)' % (k, mn or '-'), None))
            elif T is sc or T.id in {c.id for c in chain}:
                g = T.func_at(doff)
                if g is None and doff in T.protos:
                    g = next((q for q in T.funcs if q['proto'] == doff), None)
                out += sends_of(pool, T, g, hint, depth + 1, seen)
    return out


def impl(pool, cls, doff, target_script, hint):
    """the function that runs for prototype doff of script cls on a target whose instance script is target_script:
    an override with the same vtable index in the target's chain first, else cls's own"""
    C = pool.get(cls, hint)
    if C is None or doff not in C.protos: return None, None
    k, vt = C.protos[doff]
    if vt != 0xffff:
        for sc in pool.chain(target_script, hint):
            for f in sc.funcs:
                p = f['proto']
                if p is not None and p in sc.protos and sc.protos[p][1] == vt and f['code'] is not None:
                    return sc, f
    f = next((q for q in C.funcs if q['proto'] == doff), None)
    return (C, f) if f is not None else (None, None)


def uses_of(pool, unit, it_, refs, intro_index):
    """{target intro: [(relation, detail, entry n or None)]} from the code of the intro's script chain"""
    out = collections.defaultdict(list)
    if not refs: return out
    for sc in pool.chain(it_['script'], unit.secs):
        for f in sc.funcs:
            bound = None; last = None; cast = None
            for o, op, arg, ex in sc.code(f):
                if op == 0x00:
                    bound = None; last = None; cast = None; continue
                if op == 0x0f: last = arg
                if op == 0x14 and bound is not None:
                    out[bound].append(('reads', 'reads member +%d of its script' % arg, None))
                for x in ex:
                    if x in sc.ids and op == 0x7e: cast = sc.u32(x)
                    if x not in sc.ext or sc.ext[x][0] != 8: continue
                    tid, doff = sc.ext[x][1], sc.ext[x][2]
                    T = pool.get(tid, unit.secs)
                    if T is None: continue
                    if T.native == 'instanceref':
                        fi = T.func_at(doff); k = fi['k'] if fi else None
                        if last in refs:
                            tgt = refs[last][0]
                            if k in (6, 7): bound = tgt
                            elif k == 9: out[tgt].append(('sets sticky', 'instanceref f9 (set sticky bool)', None))
                            elif k == 15: out[tgt].append(('gets sticky', 'instanceref f15 (get sticky bool)', None))
                            else: out[tgt].append(('ref', 'instanceref f%s' % k, None))
                        continue
                    if bound is None or T.native: continue
                    if doff not in T.protos and T.func_at(doff) is None: continue
                    tinfo = intro_index.get(bound)
                    tscript = tinfo['script'] if tinfo else cast
                    hint = tinfo['unit'].secs if tinfo else unit.secs
                    if doff in T.protos:
                        isc, fn = impl(pool, tid, doff, tscript, hint)
                        pk, vt = T.protos[doff]
                        via = 'calls proto %d (vt %d) of script %d' % (pk, vt, tid)
                    else:
                        isc, fn = T, T.func_at(doff); via = 'calls f%d of script %d' % (fn['k'], tid)
                    sends = sends_of(pool, isc, fn, hint) if isc is not None else []
                    log('    trace %s intro %d f%d: %s on %d -> %s' % (unit.name, it_['uid'], f['k'], via, bound, sends), 3)
                    if sends:
                        for kind, txt, n in sends:
                            out[bound].append(('command' if kind == 'command' else 'uber call', via + ': ' + txt, n))
                    else:
                        out[bound].append(('call', via + ' (no uber command)', None))
                    bound = None
    return out


def effect_text(oi, n):
    """'link k: a->b, ... (event 2)' for command table entry n of the object"""
    if oi is None or n is None: return ''
    if not oi.cmds: return 'no command table'
    if n >= len(oi.cmds): return 'entry %d not in the table (%d entries)' % (n, len(oi.cmds))
    parts = []
    for link, kind, value in oi.cmds[n]:
        desc = oi.descs[link] if 0 <= link < len(oi.descs) else None
        msg = '%s %d' % (KIND.get(kind, 'kind %d' % kind), value)
        if desc is None: parts.append('link %d: %s (no such link)' % (link, msg)); continue
        nd = desc['nodes']
        if kind == 1:
            tn = nd[value]['name'] if value < len(nd) else '?'
            parts.append('link %d: %s -> %s' % (link, msg, tn)); continue
        fr = fires(desc, kind, value)
        parts.append('link %d: %s -> %s' % (link, msg, ', '.join('%s>%s' % (nd[a]['name'], nd[b]['name'] if b < len(nd) else '?')
                                                                  for a, b in fr) or 'no matching transition'))
    return '; '.join(parts)


def behaviour_text(oi, n=None):
    if oi is None or not oi.descs: return 'no state'
    links = sorted({r[0] for r in oi.cmds[n]}) if n is not None and n < len(oi.cmds) else list(range(len(oi.descs)))
    out = []
    for k in links:
        if 0 <= k < len(oi.descs):
            sets = [v for recs in oi.cmds for link, kind, v in recs if link == k and kind == 1]
            out.append(('link %d ' % k if len(oi.descs) > 1 else '') + behaviour(oi.descs[k], sets))
    return '; '.join(out)


# ---------------------------------------------------------------- scan
def scan(src, only_units):
    pool = Pool(src)
    units = []
    log('[%s] reading %d units' % (src.key, len(src.units)))
    for name, grp in src.units:
        if only_units and name not in only_units: continue
        secs = src.drm(name)
        its = intros_of(secs, src.e, src.names) if secs else None
        if its is None:
            log('  %s: no unit DRM / no intro list' % name, 1); continue
        units.append(Unit(name, grp, secs, its))
        log('  %s (%s): %d intros' % (name, grp, len(its)), 1)
    index = {}
    for U in units:
        for it_ in U.intros:
            q = dict(it_); q['unit'] = U
            index.setdefault(it_['uid'], q)
    # pass 1: instance references of every placed instance (reverse index = obj.refs)
    refs = {}; back = collections.defaultdict(list)
    for U in units:
        pool.add_drm(U.secs)
        for it_ in U.intros:
            r = refs_of(pool, U, it_) if it_['script'] else {}
            refs[(U.name, it_['idx'])] = r
            for off, (t, _) in r.items():
                back[t].append(it_['uid'])
    objcache = {}

    def objinfo(nm):
        if nm not in objcache:
            secs = src.drm(nm)
            pool.add_drm(secs)
            objcache[nm] = ObjInfo(secs, src.e) if secs else None
        return objcache[nm]

    def refs_text(uid, skip):
        rows = []
        for r in sorted(set(back.get(uid, []))):
            if r == skip: continue
            q = index.get(r)
            nm = q['name'] if q else '?'
            rows.append('%d %s%s' % (r, nm, ' (trigger)' if q and (name_kind(nm) or '').startswith('trigger') else ''))
        return rows

    rows = []
    for U in units:
        for it_ in U.intros:
            r = refs.get((U.name, it_['idx']), {})
            kind = name_kind(it_['name'])
            uses = uses_of(pool, U, it_, r, index) if r else {}
            targets = {}
            for off, (t, _) in sorted(r.items()):
                targets.setdefault(t, off)
            drives = False
            for t in targets:
                q = index.get(t)
                oi = objinfo(q['name']) if q else None
                if oi is not None and oi.cmds and any(u[0] == 'command' for u in uses.get(t, [])): drives = True
            named = kind in ('press plate', 'lever', 'button', 'crank', 'wheel', 'switch')
            if not named and not drives: continue
            own = objinfo(it_['name'])
            base = dict(source=src.key, level=U.grp, unit=U.name, intro=it_['uid'], object=it_['name'],
                        kind=kind or 'script object', named='yes' if named else 'no',
                        pos='%.1f %.1f %.1f' % it_['pos'], script=it_['script'],
                        own_type=own.short_type() if own else 'none',
                        own_behaviour=behaviour_text(own) if own and own.descs else '',
                        switch_referrers=' | '.join(refs_text(it_['uid'], None)))
            if not targets:
                rows.append(dict(base, target='', target_object='', target_unit='', target_type='', relation='no target',
                                 detail='', command='', effect='', behaviour='', target_referrers=''))
                continue
            for t, off in targets.items():
                q = index.get(t)
                oi = objinfo(q['name']) if q else None
                us = uses.get(t) or [('bind only', 'instanceref, no call found', None)]
                seen = set()
                for rel, det, n in us:
                    key = (rel, det, n)
                    if key in seen: continue
                    seen.add(key)
                    rows.append(dict(base, target=t, target_object=q['name'] if q else '(not in a unit of this source)',
                                     target_unit=q['unit'].name if q else '', target_type=oi.type_text() if oi else
                                     ('no state (script / animation only)' if q else ''),
                                     relation=rel, detail=det, command='' if n is None else n,
                                     effect=effect_text(oi, n) if rel == 'command' else '',
                                     behaviour=behaviour_text(oi, n if rel == 'command' else None) if oi else 'no state',
                                     target_referrers=' | '.join(refs_text(t, it_['uid']))))
    log('[%s] %d units, %d intros, %d rows; objects read %d, with an uber block %d; %s' % (
        src.key, len(units), sum(len(U.intros) for U in units), len(rows), len(objcache),
        sum(1 for o in objcache.values() if o is not None and o.descs), dict(STATS)))
    STATS.clear()
    return rows, units


COLS = ['source', 'level', 'unit', 'intro', 'object', 'kind', 'named', 'pos', 'script', 'own_type', 'own_behaviour', 'target',
        'target_object', 'target_unit', 'target_type', 'relation', 'detail', 'command', 'effect', 'behaviour',
        'target_referrers', 'switch_referrers']


def write_md(path, title, rows):
    with open(path, 'w', encoding='utf-8-sig', newline='\r\n') as fh:
        fh.write('# %s\n\nLocal result of tools/puzzle_switch_scan.py (game data - not for the repository).\n\n' % title)
        by_unit = collections.defaultdict(list)
        for r in rows: by_unit[r['unit']].append(r)
        for u in sorted(by_unit):
            rs = by_unit[u]
            sw = sorted({(r['intro'], r['object'], r['kind']) for r in rs})
            fh.write('## %s (%d switch-like objects)\n\n' % (u, len(sw)))
            fh.write('| intro | object | kind | target | target object / type | relation | cmd | effect | behaviour | '
                     'triggers / other referrers of the target |\n|---|---|---|---|---|---|---|---|---|---|\n')
            done = set()
            for r in sorted(rs, key=lambda r: (r['intro'], str(r['target']), str(r['command']))):
                k = (r['intro'], r['target'], r['relation'], r['command'])
                if r['relation'] in ('ref',) or k in done: continue
                done.add(k)
                fh.write('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |\n' % (
                    r['intro'], r['object'], r['kind'], r['target'] or '-',
                    ('%s (%s) - %s' % (r['target_object'], r['target_unit'], r['target_type'])) if r['target'] else '-',
                    r['relation'], r['command'], r['effect'].replace('|', '/'), r['behaviour'],
                    r['target_referrers'].replace(' | ', ', ')))
            fh.write('\n')


def compare(pc_rows, xb_rows, path):
    """pairs switch rows of PC base and Xbox base by unit + object name + rounded position"""
    def key(r):
        x, y, z = (float(v) for v in r['pos'].split())
        return (r['unit'], r['object'], round(x / 4), round(y / 4), round(z / 4))

    def sig(rs):
        return sorted({(r['target_object'], r['relation'], str(r['command']), r['behaviour']) for r in rs if r['relation'] != 'ref'})
    P_, X_ = collections.defaultdict(list), collections.defaultdict(list)
    for r in pc_rows: P_[key(r)].append(r)
    for r in xb_rows: X_[key(r)].append(r)
    st = collections.Counter(); diffs = []
    for k in sorted(set(P_) | set(X_)):
        if k not in X_: st['pc_only'] += 1; diffs.append(('PC only', k, sig(P_[k]), None)); continue
        if k not in P_: st['xbox_only'] += 1; diffs.append(('Xbox only', k, None, sig(X_[k]))); continue
        st['paired'] += 1
        if sig(P_[k]) == sig(X_[k]): st['same'] += 1
        else: st['different'] += 1; diffs.append(('differs', k, sig(P_[k]), sig(X_[k])))
    with open(path, 'w', encoding='utf-8-sig', newline='\r\n') as fh:
        fh.write('# PC base vs Xbox base switch rows\n\nLocal result of tools/puzzle_switch_scan.py.\n\n%s\n\n' % dict(st))
        for what, k, a, b in diffs:
            fh.write('- %s %s %s: PC %s / Xbox %s\n' % (what, k[0], k[1], a, b))
    return st


def main(argv):
    a = list(argv)

    def opt(k, dflt=None):
        if k in a:
            i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return v
        return dflt
    if '-h' in a or '--help' in a: print(__doc__); return 0
    LOG['level'] = 3 if '--trace' in a else 2 if '--debug' in a else 1 if '--verbose' in a else 0
    a = [x for x in a if x not in ('--trace', '--debug', '--verbose')]
    sources = opt('--source', 'pc,dlc,xbox').split(',')
    out = opt('--out', DEFAULT_OUT); dlc_dir = opt('--dlc-dir', GAME_MODS)
    only = set(opt('--units', '').split(',')) - {''}
    if a or any(s not in ('pc', 'dlc', 'xbox') for s in sources): print(__doc__); return 2
    if 'dlc' in sources and not dlc_dir:
        print('usage: source dlc needs --dlc-dir <game mods folder> or env TRU_GAME_MODS'); return 2
    os.makedirs(os.path.join(out, 'logs'), exist_ok=True)
    LOG['fh'] = open(os.path.join(out, 'logs', 'puzzle_switch_scan_%s.log' % time.strftime('%Y%m%d_%H%M%S')), 'w',
                     encoding='utf-8')
    log('puzzle_switch_scan %s sources %s out %s dlc-dir %s units %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), sources,
                                                                        out, dlc_dir, sorted(only) or 'all'))
    t0 = time.time(); allrows = {}; rc = 0
    for s in sources:
        try:
            src = Source(s, dlc_dir)
        except Exception as ex:
            log('[%s] cannot open the source: %s' % (s, ex)); rc = 1; continue
        rows, units = scan(src, only)
        allrows[s] = rows
        with open(os.path.join(out, '%s_switches.csv' % s), 'w', encoding='utf-8-sig', newline='') as fh:
            w = csv.DictWriter(fh, COLS); w.writeheader(); w.writerows(rows)
        for g in sorted({r['level'] for r in rows}):
            write_md(os.path.join(out, '%s_%s.md' % (s, g)), '%s %s switch-like objects' % (s, g),
                     [r for r in rows if r['level'] == g])
    with open(os.path.join(out, 'summary.md'), 'w', encoding='utf-8-sig', newline='\r\n') as fh:
        fh.write('# Switch scan summary (%s)\n\nLocal result of tools/puzzle_switch_scan.py.\n\n' % time.strftime('%Y-%m-%d %H:%M'))
        fh.write('Counts: objects = placed instances; behaviour columns = distinct (object, target) pairs with a '
                 'decoded uber command.\n\n')
        fh.write('| source | level | units | switch-like objects | named | with targets | command rows | one-shot | cyclic ring | toggle | reversible | auto-reset | repeatable |\n')
        fh.write('|---|---|---|---|---|---|---|---|---|---|---|---|---|\n')
        for s, rows in allrows.items():
            for g in sorted({r['level'] for r in rows}):
                rs = [r for r in rows if r['level'] == g]
                objs = {(r['unit'], r['intro']) for r in rs}
                cmd = [r for r in rs if r['relation'] == 'command']
                b = lambda word: len({(r['unit'], r['intro'], r['target']) for r in cmd if word in r['behaviour']})
                fh.write('| %s | %s | %d | %d | %d | %d | %d | %d | %d | %d | %d | %d | %d |\n' % (
                    s, g, len({r['unit'] for r in rs}), len(objs), len({(r['unit'], r['intro']) for r in rs if r['named'] == 'yes'}),
                    len({(r['unit'], r['intro']) for r in rs if r['target'] != ''}), len(cmd), b('one-shot'),
                    b('cyclic ring'), b('toggle'), b('reversible'), b('auto-reset'), b('repeatable')))
    if 'pc' in allrows and 'xbox' in allrows:
        st = compare(allrows['pc'], allrows['xbox'], os.path.join(out, 'compare_pc_xbox.md'))
        log('compare pc / xbox: %s' % dict(st))
    log('done in %.0f s' % (time.time() - t0))
    LOG['fh'].close()
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
