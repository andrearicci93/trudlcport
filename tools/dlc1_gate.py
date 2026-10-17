"""dlc1_gate.py - gate di regressione statico unico per DLC1 (solo offline, nessuna VM).

1. RISOLVE l'overlay effettivo: elenco ordinato di directory (basso -> alto, l'ultima versione di ogni file vince, nome normalizzato
   minuscolo) -> directory di stage con symlink (ricostruita da zero a ogni run), con provenienza (dir sorgente + md5) per file.
   --installed = ordine di work/ws/CONVENTIONS.md (vm_mods_expected < fix12 < fix13 < fix14 < glitchfix < next < fix16 < current < current_webs
   < fix18 < fix18_awf_extra < fix20 < chain_aim/mods_chainfix_min < menu_dlc/B + dlc_images image/ e local/).
   Un argomento DIR[@PREFIX] monta DIR sotto PREFIX/ (serve per dlc_images). Solo estensioni di dati di gioco (.drm .mul .mus .sam .tfb .raw locals.bin_*).
2. ESEGUE come subprocess (mai import) tutti i check statici, ognuno in un wrapper che redirige verso work/ws/gate/sandbox/ ogni open() in
   scrittura sotto work/ (i validatori scrivono risultati/pkl), piu' una guardia mtime/size su work/ e tools/ prima/dopo (fallisce se cambia qualcosa).
   Per-overlay (scope overlay): engine_walk_check --dir, dtp_audit scan, model_point_fix scan, hinfo_audit check, animinfo_check, dlc_fix_scan, model_validate.
   Globali (scope selftests, non leggono l'overlay: regressione = numeri peggiori): material/tex/mesh/terrain/model/generic_validate, verify_ids, override_check,
   model_point_fix selftest, dtp_audit validate+controls, engine_walk_check --controls.
3. JSON: findings per file x check (+ matrice per_file con conteggi), tier di rischio crash 1..6, calibrazione PC per i finding di engine_walk_check.
   --baseline B.json --compare: segnala solo NUOVI finding (chiave non in baseline E conteggio (file,tool,check,code) aumentato), regressioni dei selftest
   e tool passati da ok a errore. Exit 1 se ci sono regressioni di tier <= --fail-tier (default 4).
Uso:
  tools/venv/bin/python -I tools/dlc1_gate.py --installed --jobs 8 --json work/ws/gate/baseline_installed.json --report work/ws/gate/BASELINE.md
  tools/venv/bin/python -I tools/dlc1_gate.py work/mods_a work/mods_b ... --baseline work/ws/gate/baseline_installed.json --compare   (overlay a scelta)
  tools/venv/bin/python -I tools/dlc1_gate.py --installed --scope overlay --baseline B.json --compare        (solo check per-overlay, ~1 min)
  tools/venv/bin/python -I tools/dlc1_gate.py --current run.json --baseline B.json --compare                  (confronta due JSON senza rieseguire)
Opzioni: --scope overlay|selftests|all (default all) --only-files a.drm,b.drm --keep-stage --no-guard --report MD --compare-json OUT
Limiti: animinfo_check stampa max 8 hit per file (conteggio troncato, segnalato); i check per-file hinfo/animinfo/model_validate saltano i file senza
sorgente Xbox (file base del gioco); tex/material non hanno un check per-overlay (solo selftest del convertitore)."""
import sys, os, re, json, ast, time, hashlib, shutil, subprocess, collections, builtins, io, types, argparse, pickle
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
TOOLS = os.path.join(ROOT, 'tools')
WORK = os.path.join(ROOT, 'work')
GATE = os.path.join(WORK, 'ws', 'gate')
SANDBOX = os.path.join(GATE, 'sandbox')
PY = os.path.join(TOOLS, 'venv', 'bin', 'python')
if not os.path.exists(PY): PY = sys.executable
SELF = os.path.abspath(__file__)
VERSION = 1

INSTALLED = ['vm_mods_expected', 'mods_fix12', 'mods_fix13', 'mods_fix14', 'mods_glitchfix', 'mods_next', 'mods_fix16', 'mods_current',
             'mods_current_webs', 'mods_fix18', 'mods_fix18_awf_extra', 'mods_fix20', 'chain_aim/mods_chainfix_min', 'menu_dlc/B',
             'dlc_images/image@image', 'dlc_images/local/mods/local@local']
DATA_EXT = ('.drm', '.mul', '.mus', '.sam', '.tfb', '.raw')


# ======================================================================================================== sandbox runner
def sandbox_main(argv):
    """python dlc1_gate.py --_sandbox SCRIPT ARGS..: esegue SCRIPT come __main__ con open() in scrittura sotto work/ rediretta in SANDBOX"""
    script = os.path.abspath(argv[0])
    _open = builtins.open
    moved = {}

    def redirect(p, mode):
        try: ap = os.path.abspath(os.fspath(p))
        except TypeError: return p
        if not ap.startswith(WORK + os.sep) or ap.startswith(GATE + os.sep): return p
        t = os.path.join(SANDBOX, os.path.relpath(ap, WORK))
        if any(c in mode for c in 'wax+'):
            os.makedirs(os.path.dirname(t), exist_ok=True); moved[ap] = t; return t
        return moved.get(ap, p)

    def sopen(f, mode='r', *a, **k): return _open(redirect(f, mode), mode, *a, **k)
    builtins.open = sopen; io.open = sopen
    import multiprocessing
    try: multiprocessing.set_start_method('fork')
    except RuntimeError: pass
    sys.argv = [script] + argv[1:]
    sys.path.insert(0, os.path.dirname(script))
    mod = types.ModuleType('__main__'); mod.__file__ = script; sys.modules['__main__'] = mod
    exec(compile(_open(script).read(), script, 'exec'), mod.__dict__)


# ======================================================================================================== overlay
def norm(rel): return rel.replace('\\', '/').lower()

def is_data(name):
    n = name.lower()
    return n.endswith(DATA_EXT) or n.startswith('locals.bin_')

def parse_spec(s):
    path, _, prefix = s.partition('@')
    p = path
    if not os.path.isabs(p):
        p = next((c for c in (os.path.join(os.getcwd(), path), os.path.join(WORK, path), os.path.join(ROOT, path)) if os.path.isdir(c)), os.path.join(WORK, path))
    return os.path.normpath(p), prefix.strip('/')

def resolve_overlay(specs, stage):
    """-> files {normkey: dict(rel, src_path, layer)} (last layer wins), skipped list; builds symlink stage"""
    files = {}; skipped = collections.Counter()
    for specstr in specs:
        d, prefix = parse_spec(specstr)
        label = os.path.relpath(d, WORK) if d.startswith(WORK + os.sep) else d
        if not os.path.isdir(d): skipped['missing_dir:' + label] += 1; continue
        for r, _, fs in os.walk(d):
            for f in sorted(fs):
                if not is_data(f): skipped[os.path.splitext(f)[1] or f] += 1; continue
                p = os.path.join(r, f)
                rel = os.path.relpath(p, d).replace('\\', '/')
                if prefix: rel = prefix + '/' + rel
                files[norm(rel)] = dict(rel=rel, path=p, layer=label)
    if os.path.lexists(stage): shutil.rmtree(stage)
    for k, v in files.items():
        t = os.path.join(stage, v['rel']); os.makedirs(os.path.dirname(t), exist_ok=True); os.symlink(v['path'], t)
    return files, dict(skipped)

def md5_of(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


# ======================================================================================================== process helpers
def run_tool(args, jobs_env=None, timeout=3600):
    """args: [script, a..] under tools/ ; returns dict(rc, out, err, sec)"""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    t0 = time.time()
    args = [str(a) for a in args]
    cmd = [PY, '-I', SELF, '--_sandbox', os.path.join(TOOLS, args[0])] + args[1:]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env, cwd=GATE)
        return dict(rc=p.returncode, out=p.stdout, err=p.stderr, sec=round(time.time() - t0, 1), cmd=' '.join(args))
    except subprocess.TimeoutExpired as e:
        return dict(rc=-9, out='', err='timeout %ss' % timeout, sec=round(time.time() - t0, 1), cmd=' '.join(args))

def tail(s, n=6): return '\n'.join(s.strip().splitlines()[-n:])[:1200]

def F(tool, check, code, file, type=None, id=None, off=None, sev='', **detail):
    return dict(tool=tool, check=check, code=code, file=file, type=type, id=id, off=off, sev=sev, detail=detail)


# ======================================================================================================== per-overlay tools
def t_engine(stage, jobs, out_dir):
    js = os.path.join(out_dir, 'ewc.json')
    r = run_tool(['engine_walk_check.py', '--dir', stage, '--jobs', jobs, '--json', js])
    st = dict(status='ok', sec=r['sec'], cmd='engine_walk_check.py --dir <overlay> (== --static sul set risolto)')
    fl = []
    if r['rc'] != 0 or not os.path.exists(js): return dict(st, status='tool_error', error=tail(r['err'] or r['out'])), fl
    for x in json.load(open(js)).get('dir', []):
        if x['code'].startswith('_'): continue
        det = {k: v for k, v in x.items() if k not in ('check', 'code', 'file', 'type', 'id', 'off', 'sev', 'path', 'src')}
        fl.append(F('engine_walk_check', x['check'], x['code'], x['file'], x.get('type'), x.get('id'), x.get('off'), x['sev'], **det))
    m = re.search(r'overlay dir: .* -> (\d+) DRMs', r['out']); st['drm'] = int(m.group(1)) if m else None
    return st, fl

def t_dtp(stage, jobs, out_dir):
    js = os.path.join(out_dir, 'dtp.json')
    r = run_tool(['dtp_audit.py', 'scan', '--set', stage, '--json', js])
    st = dict(status='ok', sec=r['sec'], cmd='dtp_audit.py scan --set <overlay>')
    fl = []
    if r['rc'] != 0 or not os.path.exists(js): return dict(st, status='tool_error', error=tail(r['err'] or r['out'])), fl
    for x in json.load(open(js)):
        fl.append(F('dtp_audit', x['det'], x['det'], x['file'], x.get('type'), x.get('id'), x.get('off'), '', xbox=x.get('xbox'), pc=x.get('pc'),
                    want=x.get('want'), rule=x.get('rule'), text=x.get('text')))
    return st, fl

RX_MPF = re.compile(r'^(\S+) \[.*?\] DTP (\d+) \(xbox (\d+)\) (\w+) @0x([0-9a-f]+) \(elem 0x([0-9a-f]+)\) pc ([0-9a-f]+) -> ([0-9a-f]+) \((\w+)\)')
def t_mpf(stage, jobs, out_dir):
    r = run_tool(['model_point_fix.py', 'scan', '--set', stage])
    st = dict(status='ok', sec=r['sec'], cmd='model_point_fix.py scan --set <overlay>', no_xbox_source=[])
    fl = []
    if r['rc'] != 0: return dict(st, status='tool_error', error=tail(r['err'] or r['out'])), fl
    for ln in r['out'].splitlines():
        m = RX_MPF.match(ln)
        if m:
            f, did, xid, kind, off, el, pc, want, perm = m.groups()
            fl.append(F('model_point_fix', kind, kind, f, 7, int(did), int(off, 16), '', pc=pc, want=want, perm=perm, elem=int(el, 16)))
        elif 'no Xbox source resolved' in ln: st['no_xbox_source'].append(ln.split(')')[-1].strip())
    m = re.search(r'TOTAL words (\d+)', r['out'])
    if m and int(m.group(1)) != len(fl): st['warn'] = 'TOTAL %s vs parsed %d' % (m.group(1), len(fl))
    return st, fl

def per_file(tool, script, args_fn, parse_fn, stage, files, jobs):
    st = dict(status='ok', cmd='%s <file> (un subprocess per file)' % script, skipped={}, sec=0)
    fl = []; t0 = time.time()
    def one(rel):
        return rel, run_tool([script] + args_fn(os.path.join(stage, rel)))
    with ThreadPoolExecutor(jobs) as ex:
        for rel, r in ex.map(one, files):
            if r['rc'] != 0: st['skipped'][rel] = tail(r['err'], 1)[-160:]; continue
            fl += parse_fn(rel, r['out'])
    st['sec'] = round(time.time() - t0, 1); st['n_files'] = len(files)
    if len(st['skipped']) == len(files) and files: st['status'] = 'tool_error'; st['error'] = 'tutti i file hanno fallito: ' + next(iter(st['skipped'].values()))
    return st, fl

def p_hinfo(rel, out):
    fl = []
    for ln in out.splitlines():
        if ln.startswith('  ('):
            try: t = ast.literal_eval(ln.strip())
            except Exception: continue
            _, xid, pid, seg, arr, el, off, xw, pw, cand = t
            kind = {0: 'HS', 1: 'HB', 2: 'HM', 3: 'HC'}.get(arr, 'H%d' % arr)
            fl.append(F('hinfo_audit', 'violation', kind, rel, 7, pid, off, '', seg=seg, arr=arr, el=el, xbox=xw, pc=pw, rule=cand))
    return fl

def p_anim(rel, out):
    fl = []; trunc = False
    m = re.search(r'dtps with animinfo (\d+) BAD (\[.*\])\s*$', out, re.S)
    if not m: return fl
    try: bad = ast.literal_eval(m.group(2))
    except Exception: return fl
    if len(bad) >= 8: trunc = True
    for b in bad:
        kind = b[1]
        fl.append(F('animinfo_check', kind, kind, rel, 7, b[0], None, '', args=[str(a) for a in b[2:]], truncated=trunc))
    return fl

def p_mval(rel, out):
    fl = []
    for ln in out.splitlines():
        m = re.match(r'^(\S+) DTP (\d+) words fixed (\d+)', ln)
        if m: fl.append(F('model_validate', 'model_fix_words', 'model_fix_words', rel, 7, int(m.group(2)), None, '', words=int(m.group(3))))
    return fl

def t_fixscan(stage, jobs, out_dir):
    r = run_tool(['dlc_fix_scan.py', stage])
    st = dict(status='ok', sec=r['sec'], cmd='dlc_fix_scan.py <overlay>')
    fl = []
    if r['rc'] != 0: return dict(st, status='tool_error', error=tail(r['err'] or r['out'])), fl
    for ln in r['out'].splitlines():
        m = re.match(r'^(\S+\.drm) (\{.*\})$', ln)
        if not m: continue
        for k, n in ast.literal_eval(m.group(2)).items():
            fl.append(F('dlc_fix_scan', k, k, m.group(1).replace('\\', '/'), None, None, None, '', count=n))
    return st, fl

OVERLAY_TOOLS = ['engine_walk_check', 'dtp_audit', 'model_point_fix', 'dlc_fix_scan', 'hinfo_audit', 'animinfo_check', 'model_validate']


# ======================================================================================================== selftests (global)
HIGHER = re.compile(r'(^|[^a-z])(exact|valid|sem_|semantic|equal|same|sizeok|struct_exact|control:|pairs_exact|psnr|mapped|n$|pairs$)', re.I)
LOWER = re.compile(r'(fix_would_change|fp_flagged|words_changed|pairs_changed|error|mismatch|many-to-one|colliding|missing|differing|unmapped|size differs|non-semantic|diffbytes|unmatched|status)', re.I)

def k_in(key): return key in ('fp_covered_x1000',)

def direction(key):
    if LOWER.search(key): return 'lower'
    if k_in(key) or re.search(r'(^|[^a-z])(exact|valid|sem_|semantic|struct_exact|control:|pairs_exact|tex_byte_equal)', key, re.I) or key.endswith(('equal', 'sizeok', 'same-batching')): return 'higher'
    return 'info'

def num_dict(label, d, M):
    for k, v in d.items():
        if isinstance(v, (int, float)): M['%s.%s' % (label, k)] = v
        elif isinstance(v, (list, dict, tuple, set)) and k != 'low': M['%s.len_%s' % (label, k)] = len(v)

def metrics_of(name, out):
    M = {}
    for ln in out.splitlines():
        s = ln.rstrip()
        m = re.match(r'^\s*(CONTROL\s+.*?|FOUND|MISS)\s{1,}(FLAGGED|FOUND|MISS)\b', s)
        if m is None:
            m = re.match(r'^\s+(FOUND|MISS)\s+(.*?)\s{2,}\S+\.drm', s)
        if re.match(r'^CONTROL ', s):
            lab = re.sub(r'\s+(FLAGGED|MISSED|MISS|FOUND)\b.*$', '', s[8:]).strip()
            M['control:' + lab] = 0 if re.search(r'\b(MISS|MISSED)\b', s.split(lab)[-1][:12]) else 1; continue
        if re.match(r'^\s+(FOUND|MISS)\s', s):
            lab = re.sub(r'\s+\S+\.drm DTP.*$', '', s.strip()[5:]).strip()
            M['control:' + lab] = 1 if s.strip().startswith('FOUND') else 0; continue
        m = re.match(r'^(\S+)\s+(\S+)\s+(\{.*\})\s*$', s) or re.match(r'^([^{]*?)\s*(\{.*\})\s*$', s)
        if m and '{' in s:
            try:
                d = ast.literal_eval(s[s.index('{'):]); lab = s[:s.index('{')].strip(' :') or 'main'
                if isinstance(d, dict): num_dict(lab, d, M); continue
            except Exception: pass
        m = re.match(r'^\s{0,2}([A-Za-z_][^\d\n]{1,50}?)\s{2,}(\d+)\s*$', s)       # "label     123"
        if m: M[m.group(1).strip()] = int(m.group(2)); continue
        m = re.match(r'^(\S[^\n]*?\))\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+|-)\s+([\d.]+)\s+([\d.]+)$', s)    # tex rows
        if m:
            M['tex[%s].n' % m.group(1).strip()] = int(m.group(2)); M['tex[%s].exact' % m.group(1).strip()] = int(m.group(3)); continue
        m = re.match(r'^total pairs (\d+) errors (\d+)', s)
        if m: M['tex.total_pairs'] = int(m.group(1)); M['tex.errors'] = int(m.group(2)); continue
        m = re.match(r'^same dims\+mips (\d+) of (\d+)', s)
        if m: M['tex.same_dims_mips'] = int(m.group(1)); continue
        m = re.match(r'^([ABC]) (\S.*?):?\s+(.*)$', s)                                        # verify_ids
        if name == 'verify_ids' and m:
            lab = '%s %s' % (m.group(1), m.group(2)[:14])
            for k, v in re.findall(r'(many-to-one|colliding with PC universe|name/id mismatches|missing|differing)\s+(\d+)', s): M['%s %s' % (lab, k)] = int(v)
            if s.startswith('A unmapped'):
                M['A unmapped_types'] = len(ast.literal_eval(re.search(r'\): (\{.*?\}) examples', s).group(1)))
    if name == 'dtp_audit_validate':
        for pat, k in ((r'sections the fix would change (\d+)', 'fix_would_change'), (r'flagged (\d+) \(rate', 'fp_flagged_heldout'), (r'covered ([\d.]+)', 'fp_covered_x1000'),
                       (r'FP rule in-sample .*?flagged (\d+)', 'fp_flagged_insample'), (r"spans \{'STR': (\d+)", 'str_spans')):
            m = re.search(pat, out)
            if m: M[k] = int(float(m.group(1)) * (1000 if k.endswith('x1000') else 1))
    return M

SELFTESTS = [   # (name, argv, weight)  heavy first
    ('tex_validate', ['tex_validate.py'], 3), ('terrain_validate', ['terrain_validate.py'], 2), ('mesh_validate', ['mesh_validate.py'], 2),
    ('dtp_audit_validate', ['dtp_audit.py', 'validate'], 1), ('override_check', ['override_check.py'], 1), ('verify_ids', ['verify_ids.py'], 1),
    ('material_validate', ['material_validate.py'], 1), ('model_validate', ['model_validate.py'], 1), ('generic_validate', ['generic_validate.py'], 1),
    ('model_point_fix_selftest', ['model_point_fix.py', 'selftest'], 1), ('dtp_audit_controls', ['dtp_audit.py', 'controls'], 1),
    ('engine_walk_check_controls', ['engine_walk_check.py', '--controls'], 1)]

def run_selftest(item):
    name, argv, _ = item
    r = run_tool(argv)
    d = dict(sec=r['sec'], cmd=' '.join(argv))
    if r['rc'] != 0:
        d.update(status='tool_error', error=tail(r['err'] or r['out']), metrics={})
    else:
        M = metrics_of(name, r['out'])
        d.update(status='ok', metrics=M, digest=hashlib.md5(r['out'].encode()).hexdigest(), headline=[l[:200] for l in r['out'].splitlines()[:3]])
        if not M: d['warn'] = 'nessuna metrica estratta'
    return name, d


# ======================================================================================================== guard
def snapshot():
    snap = {}
    for base in (WORK,):      # tools/ non incluso: altri agenti vi aggiungono/modificano script in parallelo; i tool invocati scrivono solo via sandbox
        for r, ds, fs in os.walk(base):
            if r.startswith(os.path.join(WORK, 'ws')) and not r.startswith(GATE) and r != os.path.join(WORK, 'ws'): ds[:] = []; continue   # altri workstream concorrenti
            if r.startswith(GATE) or '__pycache__' in r or os.sep + 'venv' in r.replace(base, ''): ds[:] = []; continue
            for f in fs:
                p = os.path.join(r, f)
                try: s = os.lstat(p)
                except OSError: continue
                snap[p] = (s.st_size, int(s.st_mtime))
    return snap

def guard_diff(a, b):
    return sorted(p for p in a if a[p] != b.get(p) and not p.endswith('dlc1_gate.py'))   # solo file preesistenti modificati/cancellati; i nuovi (altri agenti) si ignorano


# ======================================================================================================== tiers / calibration
TIERS = {1: 'R1 crash probabile (firma mai vista sui DRM PC / classe gia crashata)', 2: 'R2 crash-severity con firma presente anche su altri DRM PC (da verificare)',
         3: 'R3 rottura di gameplay (bersagli/collisioni/conversioni note da correggere)', 4: 'R4 risorse mancanti / riferimenti non risolti',
         5: 'R5 calibrato o benigno (visto uguale su PC)', 6: 'R6 euristico / solo report (probabili falsi positivi)'}

_PC = {}
def pc_cal():
    if _PC: return _PC
    p = os.path.join(WORK, 'engine_walk_cache', 'pc_calibration.pkl')
    code = collections.Counter(); files = collections.defaultdict(set); perfile = collections.Counter()
    if os.path.exists(p):
        for f in pickle.load(open(p, 'rb'))['findings']:
            if f['code'].startswith('_'): continue
            k = (f['check'], f['code']); code[k] += 1; files[k].add(f['file']); perfile[(f['file'].lower(), f['check'], f['code'])] += 1
    _PC.update(code=code, files=files, perfile=perfile, ok=bool(code)); return _PC

def tier_of(f):
    t, c, cd = f['tool'], f['check'], f['code']
    if t == 'engine_walk_check':
        pc = pc_cal(); k = (c, cd); n = pc['code'].get(k, 0); nf = pc['perfile'].get((f['file'].lower().split('/')[-1], c, cd), 0)
        nf = max(nf, pc['perfile'].get((f['file'].lower(), c, cd), 0))
        f['detail']['pc_code_hits'] = n; f['detail']['pc_code_files'] = len(pc['files'].get(k, ())); f['detail']['pc_same_file_hits'] = nf
        if f['sev'] == 'crash':
            if nf: return 5, 'crash-severity ma identico sul file PC originale (calibrato)'
            return (1, 'crash-severity, firma mai vista sui DRM PC') if n == 0 else (2, 'crash-severity, firma vista su altri file PC')
        if f['sev'] == 'warn': return (4, 'warn mai visto su PC') if n == 0 else (5, 'warn calibrato su PC')
        return 5, 'info'
    if t == 'dtp_audit':
        if c in ('STR', 'STR8', 'NODE0'): return 1, 'stringa/nodo corrotto (fix20 li aveva corretti)'
        if c == 'MAG': return 1, 'intero piccolo -> >=0x10000 (classe OOM/COUNT)'
        if c == 'IDR': return 3, 'id remap atteso (solo report, falso positivo plausibile)'
        if f['file'].lower().startswith('dlc_costume'): return 6, 'FP nei DTP grandi dei costumi (s32 vs u16 pair sistematico, attesi falsi)'
        return 3, 'FP fuori dai costumi: dato probabilmente corrotto non verificato (NOTES fix20: ~444 reali / ~15 falsi attesi; falsi 6.3e-5/parola; pattern SoundPlex float raw, u16 pair, flag s32)'
    if t == 'model_point_fix': return (3, 'punto bersaglio/mira (TP)') if c == 'TP' else (3, 'sfera/box/capsula di collisione (HInfo)')
    if t == 'hinfo_audit': return 3, 'violazione regola HInfo'
    if t == 'dlc_fix_scan': return (6, 'info scanner') if c in ('unmatched', 'rebase_unresolved') else (3, 'fix di conversione non ancora applicato')
    if t == 'model_validate': return 3, 'model_fix cambierebbe parole'
    if t == 'animinfo_check':
        return (2, 'fill loop 4G (crash ng_crash)') if c == 'wrap' else (6, 'euristica non calibrata (costume: valori ASCII/float)')
    return 6, ''

FP_NOTE = 'dtp_audit FP/MAG/IDR e hinfo_audit/model_point_fix riportano in parte le stesse parole (offset assoluti vs relativi all\'elemento): le parole distinte sono ~15, non la somma.'
RELATED = [('raft_bridge', 'catena DLC non mirabile / sparo non libera (chain_aim)'), ('grapple', 'anelli: rampino non aggancia'),
           ('dragon_slider', 'anelli / punto grapple TIPO 4 (model_point_fix)'), ('adren_trap', 'adrenaline trap (crash 0x593659 fix13/14)'),
           ('costume', 'costumi (gruppi dtp grandi)'), ('caverns', 'salvataggio in DLC blocca / OOM hall'), ('generalbank', 'menu DLC (patch B)'),
           ('pillory', 'collisioni pillory'), ('g_pda', 'merge g_pda/pack11 (script convertito)')]
def related(file):
    return sorted({d for k, d in RELATED if k in file.lower()})


# ======================================================================================================== run
def build_result(args, specs):
    t_start = time.time()
    run_dir = os.path.join(GATE, '.run', '%d' % os.getpid()); os.makedirs(run_dir, exist_ok=True)
    stage = os.path.join(GATE, '.stage', 'run%d' % os.getpid())
    os.makedirs(os.path.dirname(stage), exist_ok=True)
    snap0 = snapshot() if not args.no_guard else None
    files, skipped = resolve_overlay(specs, stage)
    only = set(x.lower() for x in args.only_files.split(',')) if args.only_files else None
    prov = {}
    with ThreadPoolExecutor(args.jobs) as ex:
        sums = list(ex.map(lambda v: md5_of(v['path']), files.values()))
    for (k, v), m in zip(files.items(), sums): prov[v['rel']] = dict(src=v['layer'], md5=m, size=os.path.getsize(v['path']))
    drms = sorted(v['rel'] for v in files.values() if v['rel'].lower().endswith('.drm') and (not only or v['rel'].lower() in only or os.path.basename(v['rel']).lower() in only))
    res = dict(version=VERSION, created=time.strftime('%Y-%m-%d %H:%M:%S'), overlay=dict(specs=specs, n_files=len(files), n_drm=len(drms), skipped=skipped, files=prov),
               scope=args.scope, tools={}, findings=[], selftests={})
    fl = []
    if args.scope in ('overlay', 'all'):
        J = args.jobs
        jobs = [('engine_walk_check', lambda: t_engine(stage, J, run_dir)), ('dtp_audit', lambda: t_dtp(stage, J, run_dir)),
                ('model_point_fix', lambda: t_mpf(stage, J, run_dir)), ('dlc_fix_scan', lambda: t_fixscan(stage, J, run_dir)),
                ('hinfo_audit', lambda: per_file('hinfo_audit', 'hinfo_audit.py', lambda p: ['check', p], p_hinfo, stage, drms, max(2, J // 2))),
                ('animinfo_check', lambda: per_file('animinfo_check', 'animinfo_check.py', lambda p: [p], p_anim, stage, drms, max(2, J // 2))),
                ('model_validate', lambda: per_file('model_validate', 'model_validate.py', lambda p: [p], p_mval, stage, drms, max(2, J // 2)))]
        with ThreadPoolExecutor(3) as ex:
            futs = [(n, ex.submit(f)) for n, f in jobs]
            for n, fu in futs:
                try: st, x = fu.result()
                except Exception as e: st, x = dict(status='tool_error', error=repr(e)), []
                res['tools'][n] = st; fl += x
                print('  %-18s %-10s %5.1fs  %d finding' % (n, st['status'], st.get('sec', 0), len(x)), flush=True)
    if only:   # filtro anche sui finding degli strumenti che girano sull'intero overlay
        fl = [f for f in fl if f['file'].lower() in only or os.path.basename(f['file']).lower() in only]
    cnt = collections.Counter()
    for f in fl:
        f['tier'], f['why'] = tier_of(f)
        f['file'] = f['file'].replace('\\', '/')
        base = '%s|%s|%s|%s|%s|%s|%s' % (f['tool'], f['check'], f['code'], f['file'].lower(), f['type'], f['id'], f['off'])
        cnt[base] += 1; f['key'] = base if cnt[base] == 1 else '%s#%d' % (base, cnt[base])
    res['findings'] = fl
    pf = collections.defaultdict(collections.Counter)
    for f in fl: pf[f['file']]['%s:%s/%s' % (f['tool'], f['check'], f['code'])] += 1
    res['per_file'] = {k: dict(v) for k, v in sorted(pf.items())}
    if args.scope in ('selftests', 'all'):
        items = SELFTESTS
        with ThreadPoolExecutor(max(1, min(3, args.jobs // 2))) as ex:
            for name, d in ex.map(run_selftest, items):
                res['selftests'][name] = d
                print('  selftest %-28s %-10s %6.1fs  %d metriche' % (name, d['status'], d['sec'], len(d['metrics'])), flush=True)
    if snap0 is not None:
        # i tool scrivono solo in sandbox: ogni differenza fuori da ws/gate e' una violazione
        ch = guard_diff(snap0, snapshot())
        res['guard'] = dict(changed=ch, ok=not ch)
        print('  guard: %s' % ('OK nessun file modificato fuori da ws/gate' if not ch else 'VIOLAZIONE %d file: %s' % (len(ch), ch[:5])), flush=True)
    res['seconds'] = round(time.time() - t_start, 1)
    if not args.keep_stage: shutil.rmtree(stage, ignore_errors=True)
    shutil.rmtree(run_dir, ignore_errors=True)
    return res


# ======================================================================================================== compare
def group_counts(res):
    c = collections.Counter()
    for f in res['findings']: c[(f['file'].lower(), f['tool'], f['check'], f['code'])] += 1
    return c

def compare(base, cur, fail_tier):
    out = dict(new=[], moved=[], increased=[], fixed_groups=[], selftest=[], tool_regressions=[], changed_files=[], missing_in_current=[])
    bkeys = {f['key'] for f in base['findings']}
    bc, cc = group_counts(base), group_counts(cur)
    scope_tools = set(cur['tools'])
    for f in cur['findings']:
        if f['key'] in bkeys: continue
        g = (f['file'].lower(), f['tool'], f['check'], f['code'])
        if cc[g] > bc.get(g, 0): out['new'].append(f)
        else: out['moved'].append(f)
    for g, n in cc.items():
        if n > bc.get(g, 0) and bc.get(g, 0) > 0: out['increased'].append(dict(group=g, base=bc[g], cur=n))
    for g, n in bc.items():
        if g[1] in scope_tools and cc.get(g, 0) < n: out['fixed_groups'].append(dict(group=g, base=n, cur=cc.get(g, 0)))
    for n, st in cur['tools'].items():
        b = base['tools'].get(n)
        if b and b['status'] == 'ok' and st['status'] != 'ok': out['tool_regressions'].append(dict(tool=n, error=st.get('error')))
    for n, d in cur.get('selftests', {}).items():
        b = base.get('selftests', {}).get(n)
        if not b: continue
        if b['status'] == 'ok' and d['status'] != 'ok': out['selftest'].append(dict(test=n, kind='tool_error', detail=d.get('error'))); continue
        for k, v in d['metrics'].items():
            bv = b['metrics'].get(k)
            if bv is None or bv == v: continue
            dr = direction(k)
            worse = (dr == 'higher' and v < bv) or (dr == 'lower' and v > bv)
            out['selftest'].append(dict(test=n, metric=k, base=bv, cur=v, kind='regression' if worse else ('improved' if dr != 'info' else 'changed')))
        for k, bv in b['metrics'].items():
            if k not in d['metrics'] and direction(k) == 'higher' and bv: out['selftest'].append(dict(test=n, metric=k, base=bv, cur=None, kind='regression'))
    bf, cf = base['overlay']['files'], cur['overlay']['files']
    for k, v in cf.items():
        if k not in bf: out['changed_files'].append(dict(file=k, change='added', src=v['src']))
        elif bf[k]['md5'] != v['md5']: out['changed_files'].append(dict(file=k, change='modified', src=v['src'], base_src=bf[k]['src']))
    if cur['scope'] != 'selftests':
        for k in bf:
            if k not in cf and (not cur['overlay'].get('only') or True): out['missing_in_current'].append(k)
    out['regressions'] = sorted([f for f in out['new'] if f['tier'] <= fail_tier], key=lambda f: (f['tier'], f['file'], f['key']))
    out['n_selftest_regressions'] = sum(1 for s in out['selftest'] if s['kind'] in ('regression', 'tool_error'))
    out['fail'] = bool(out['regressions'] or out['tool_regressions'] or out['n_selftest_regressions'])
    return out

def print_compare(c, fail_tier):
    print('== COMPARE vs baseline: %d NUOVI finding (%d con tier <= %d), %d spostati (stesso conteggio), %d gruppi aumentati, %d gruppi migliorati' % (
        len(c['new']), len(c['regressions']), fail_tier, len(c['moved']), len(c['increased']), len(c['fixed_groups'])))
    for f in sorted(c['new'], key=lambda f: (f['tier'], f['file'], f['key'])):
        print('  NEW R%d %-18s %-12s %-26s %s id=%s off=%s %s' % (f['tier'], f['tool'], f['check'], f['code'], f['file'], f['id'],
                                                              hex(f['off']) if isinstance(f['off'], int) else f['off'], ' / '.join(related(f['file']))))
    for s in c['selftest']: print('  SELFTEST %-10s %s %s' % (s['kind'], s['test'], {k: v for k, v in s.items() if k not in ('kind', 'test')}))
    for t in c['tool_regressions']: print('  TOOL ERROR', t)
    for f in c['changed_files']: print('  file %s: %s (%s)' % (f['change'], f['file'], f['src']))
    if c['missing_in_current']: print('  file nella baseline e non nell\'overlay corrente:', len(c['missing_in_current']), c['missing_in_current'][:6])
    print('  ESITO:', 'REGRESSIONE' if c['fail'] else 'OK (nessun nuovo finding di tier <= %d, selftest invariati)' % fail_tier)


# ======================================================================================================== report
def write_report(res, path, title='Baseline gate DLC1'):
    fl = res['findings']; L = []
    A = L.append
    A('# %s\n' % title)
    A('Generato %s da `tools/dlc1_gate.py` (scope %s, %.0f s). Overlay: %d file (%d DRM), specs: `%s`.\n' % (
        res['created'], res['scope'], res.get('seconds', 0), res['overlay']['n_file' + 's' if False else 'n_files'], res['overlay']['n_drm'], ' < '.join(res['overlay']['specs'])))
    A('Ordine dei problemi aperti = rischio di crash a runtime (R1 piu\' alto). Nessuna di queste voci e\' stata provata in gioco: sono risultati di analisi statica; '
      '`calibrato` = la stessa firma esce sui DRM PC originali (150k finding di engine_walk_check_cache/pc_calibration.pkl).\n')
    A('Limiti noti: (1) locals/objlist/pc_names sono letti da work/generic (engine_walk_check non legge i locals dell\'overlay; md5 locals.bin_001 uguale a dlc_images, ma regressioni dei locals dell\'overlay NON sono viste); '
      '(2) i finding R1 di g_pda.drm (script walk_count/sarray_count/sext) esistono gia\' in engine_walk_cache/installed.json del 2026-10-10: noti, nel percorso PDA, mai associati a un crash visto; '
      '(3) g_pda.drm: sorgente Xbox presa dal primo pack (pack10), XBOX_PACK del tool vale solo per dlc2; (4) animinfo_check tronca a 8 hit per file; (5) %s\n' % FP_NOTE)
    A('## Stato strumenti\n')
    A('| strumento | stato | s | finding | note |\n|---|---|---|---|---|')
    byt = collections.Counter(f['tool'] for f in fl)
    for n, s in res['tools'].items():
        note = s.get('error', '') or ('%d file saltati (no sorgente Xbox)' % len(s['skipped']) if s.get('skipped') else '')
        A('| %s | %s | %s | %d | %s |' % (n, s['status'], s.get('sec'), byt[n], note.replace('\n', ' ')[:200]))
    g = res.get('guard')
    if g: A('\nGuardia scritture: %s.' % ('nessun file modificato in work/ (fuori da ws/gate) o tools/' if g['ok'] else 'VIOLAZIONE ' + str(g['changed'][:10])))
    A('\n## Riepilogo per tier\n')
    A('| tier | descrizione | finding | file |\n|---|---|---|---|')
    for t in range(1, 7):
        x = [f for f in fl if f['tier'] == t]
        A('| R%d | %s | %d | %d |' % (t, TIERS[t].replace("''", "'"), len(x), len({f['file'] for f in x})))
    for t in range(1, 7):
        x = [f for f in fl if f['tier'] == t]
        if not x: continue
        A('\n## R%d - %s\n' % (t, TIERS[t].replace("''", "'")))
        grp = collections.defaultdict(list)
        for f in x: grp[(f['tool'], f['check'], f['code'], f['why'])].append(f)
        for (tool, ch, cd, why), lst in sorted(grp.items(), key=lambda kv: -len(kv[1])):
            d0 = lst[0]['detail']
            cal = ''
            if tool == 'engine_walk_check': cal = ' PC: %d hit in %d file' % (d0.get('pc_code_hits', 0), d0.get('pc_code_files', 0)) if d0.get('pc_code_hits') else ' PC: mai'
            A('### %s `%s/%s` - %d finding, %d file (%s;%s)\n' % (tool, ch, cd, len(lst), len({f['file'] for f in lst}), why, cal))
            byf = collections.defaultdict(list)
            for f in lst: byf[f['file']].append(f)
            A('| file | n | esempi (DTP id @off) | collegato a |\n|---|---|---|---|')
            rows = sorted(byf.items(), key=lambda kv: -len(kv[1]))
            for fn, fs in rows[:25]:
                ex = ', '.join('%s@%s' % (f['id'], hex(f['off']) if isinstance(f['off'], int) else f['off']) for f in fs[:3])
                A('| %s | %d | %s | %s |' % (fn, len(fs), ex, '; '.join(related(fn))))
            if len(rows) > 25: A('| ... altri %d file | %d | | |' % (len(rows) - 25, sum(len(v) for _, v in rows[25:])))
            A('')
    if res.get('selftests'):
        A('\n## Selftest globali dei convertitori (indipendenti dall\'overlay)\n')
        A('| test | stato | s | metriche | intestazione |\n|---|---|---|---|---|')
        for n, d in res['selftests'].items():
            A('| %s | %s | %s | %d | %s |' % (n, d['status'], d['sec'], len(d['metrics']), (d.get('error') or ' / '.join(d.get('headline', [])[:1])).replace('\n', ' ').replace('|', '/')[:150]))
    A('\n## File dell\'overlay per provenienza\n')
    cnt = collections.Counter(v['src'] for v in res['overlay']['files'].values())
    A(', '.join('%s: %d' % kv for kv in cnt.items()))
    A('\nSaltati (non dati di gioco): %s' % res['overlay']['skipped'])
    open(path, 'w').write('\n'.join(L) + '\n')


# ======================================================================================================== main
def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--_sandbox': return sandbox_main(sys.argv[2:])
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('dirs', nargs='*', help='overlay ordinato basso->alto: DIR[@PREFIX] (relativi a work/ o assoluti)')
    ap.add_argument('--installed', action='store_true', help='overlay installato in VM (ordine CONVENTIONS)')
    ap.add_argument('--scope', choices=['overlay', 'selftests', 'all'], default='all')
    ap.add_argument('--jobs', type=int, default=8)
    ap.add_argument('--only-files', help='nomi DRM separati da virgola')
    ap.add_argument('--json', help='scrive il risultato')
    ap.add_argument('--report', help='scrive il rapporto markdown')
    ap.add_argument('--baseline')
    ap.add_argument('--compare', action='store_true')
    ap.add_argument('--current', help='usa un JSON gia\' prodotto invece di rieseguire')
    ap.add_argument('--compare-json')
    ap.add_argument('--fail-tier', type=int, default=4)
    ap.add_argument('--keep-stage', action='store_true')
    ap.add_argument('--no-guard', action='store_true')
    a = ap.parse_args()
    specs = INSTALLED if a.installed else list(a.dirs)
    if a.current: cur = json.load(open(a.current))
    else:
        if not specs: ap.error('serve --installed o almeno una directory')
        bad = [x for x in specs if not os.path.isdir(parse_spec(x)[0])]
        if bad: ap.error('directory inesistenti: %s' % bad)
        os.makedirs(GATE, exist_ok=True)
        print('overlay: %s' % ' < '.join(specs), flush=True)
        cur = build_result(a, specs)
        n = collections.Counter(f['tier'] for f in cur['findings'])
        print('== %d finding in %d file (tier: %s) in %.0f s' % (len(cur['findings']), len(cur['per_file']), dict(sorted(n.items())), cur['seconds']))
    if a.json: json.dump(cur, open(a.json, 'w'), indent=1, default=str); print('scritto', a.json)
    if a.report: write_report(cur, a.report); print('scritto', a.report)
    rc = 0
    if cur.get('guard') and not cur['guard']['ok']: rc = 3
    if a.compare:
        if not a.baseline: ap.error('--compare richiede --baseline')
        base = json.load(open(a.baseline))
        c = compare(base, cur, a.fail_tier)
        print_compare(c, a.fail_tier)
        if a.compare_json: json.dump(c, open(a.compare_json, 'w'), indent=1, default=str)
        if c['fail']: rc = rc or 1
    sys.exit(rc)

if __name__ == '__main__':
    main()
