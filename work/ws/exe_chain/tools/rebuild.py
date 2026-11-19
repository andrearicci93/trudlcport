"""rebuild.py - riesegue la catena exe in work/ws/exe_chain/rebuild/ usando COPIE degli script (rebuild/src/, percorsi Mac -> Windows).
Gli originali non vengono toccati; usare sempre  python -I -B  (niente __pycache__ nelle cartelle originali).
Modi:
  python -I -B rebuild.py solo    ogni stadio sul SUO exe di ingresso di riferimento (prova isolata di ciascuno script)
  python -I -B rebuild.py catena  da 56d1ce2d in avanti, ogni stadio sull'uscita ricostruita dello stadio prima;
                                  lo stadio s8n usa tools/patch_nullfilter.py, RICOSTRUITO dal delta (lo script originale e' perso).
Richiede clang (C:/Program Files/LLVM/bin) per gli script che usano asmx.py."""
import sys, os, re, json, glob, shutil, hashlib, subprocess, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from chain import CHAIN, W
T = 'C:/tru-port/'
BASE = 'C:/tru-port/work/ws/exe_chain/rebuild/'
SRC = BASE + 'src/'
PY = sys.executable
ENV = dict(os.environ); ENV['PATH'] = r'C:\Program Files\LLVM\bin;' + ENV.get('PATH', '')
# cartelle di script da copiare (solo *.py)
DIRS = ['tools', 'work/ws/giro10/out_b117/exe', 'work/ws/dlc2_prot/attach', 'work/ws/dlc2_wallvein', 'work/ws/dlc2_tuport/spec_load',
        'work/ws/dlc2_tuport/exe_build', 'work/ws/dlc2_tuport/animlog', 'work/ws/b236', 'work/ws/b245_fx', 'work/ws/b245_qe', 'work/ws/b245_fin',
        'work/ws/b246_crash', 'work/ws/b247_chunk', 'work/ws/b262_hairdump', 'work/ws/b265_sap', 'work/ws/b269_crash', 'work/ws/b274_tu616']
TOOLS_ONLY = ['fmod_init_guard.py', 'light_tex_guard.py', 'soundplex_guard.py', 'fmod_empty_guard.py', 'camerashakes_guard.py']


def md5f(p): return hashlib.md5(open(p, 'rb').read()).hexdigest()


def prepare():
    for d in DIRS:
        os.makedirs(SRC + d, exist_ok=True)
        files = [T + d + '/' + f for f in TOOLS_ONLY] if d == 'tools' else glob.glob(T + d + '/*.py')
        for f in files:
            s = open(f, encoding='utf-8', errors='surrogateescape').read()
            s = s.replace('/Users/andrearicci/Downloads/tru-port', 'C:/tru-port').replace('/Users/andrearicci/Downloads/Xenia-SteveRepack', 'C:/Xenia-SteveRepack')
            # sys.path verso le cartelle copiate -> copie in src/ (le altre restano sugli originali, importati con -B: sola lettura)
            def rp(m):
                p = m.group(2)
                rel = p[len('C:/tru-port/'):].rstrip('/')
                return m.group(1) + (SRC + rel if rel in DIRS else p) + m.group(3)
            s = re.sub(r"(sys\.path\.insert\(0,\s*')(C:/tru-port/[^']*)(')", rp, s)
            open(SRC + d + '/' + os.path.basename(f), 'w', encoding='utf-8', errors='surrogateescape', newline='').write(s)


def run(args, log):
    r = subprocess.run([PY, '-I', '-B'] + args, capture_output=True, text=True, env=ENV, cwd=BASE)
    log.write('$ %s\nrc=%d\n%s%s\n' % (' '.join(args), r.returncode, r.stdout[-3000:], r.stderr[-3000:]))
    return r.returncode, (r.stdout + r.stderr).strip().splitlines()[-1:] if (r.stdout + r.stderr).strip() else []


def laa(inp, out):
    d = bytearray(open(inp, 'rb').read()); pe = struct.unpack_from('<I', d, 0x3c)[0]
    ch = struct.unpack_from('<H', d, pe + 0x16)[0]; struct.pack_into('<H', d, pe + 0x16, ch | 0x20); open(out, 'wb').write(d)


def apply_delta(inp, out, stage):
    dl = json.load(open(glob.glob('C:/tru-port/work/ws/exe_chain/deltas/*_%s.json' % stage)[0]))
    assert md5f(inp) == dl['input_md5'], 'ingresso delta diverso'
    d = bytearray(open(inp, 'rb').read()); d += bytes(max(0, dl['output_size'] - len(d))); d = d[:dl['output_size']]
    for off, hx in dl['ranges']: b = bytes.fromhex(hx); d[off:off + len(b)] = b
    open(out, 'wb').write(d)


def stage(nm, inp, out, log):
    """esegue lo stadio nm: ritorna (metodo, rc, ultima riga)"""
    sc = {c[0]: c for c in CHAIN}[nm]; script, extra = sc[3], sc[4]
    if script.startswith('BUILTIN:laa'): laa(inp, out); return 'builtin', 0, []
    if script.startswith('MISSING'): apply_delta(inp, out, nm); return 'DELTA (script mancante)', 0, []
    if script.startswith('work/ws/exe_chain/'): return ('script ricostruito',) + run([T + script, inp, out], log)
    if nm == 'log':
        tmp = out + '.animlog3.exe'
        rc, l = run([SRC + 'work/ws/dlc2_tuport/animlog/patch_animlog3.py', inp, tmp], log)
        if rc: return 'script', rc, l
        return ('script',) + run([SRC + 'work/ws/dlc2_tuport/animlog/patch_condlog.py', tmp, out], log)
    return ('script',) + run([SRC + script] + [inp, out] + extra, log)


def main(mode):
    os.makedirs(BASE + mode, exist_ok=True); prepare()
    log = open(BASE + mode + '/rebuild_%s.log' % mode, 'w', encoding='utf-8')
    names = [c[0] for c in CHAIN]; res = []
    prev_out = W + CHAIN[0][2]; ref_prev = W + CHAIN[0][2]
    for i, (nm, m, ref, script, extra) in enumerate(CHAIN):
        if i == 0: continue
        if nm.startswith('s') and nm[1:].isdigit() and nm != 's8': continue   # s1..s7: inclusi cumulativamente in --stage 8 (provati a parte in 'solo')
        inp = prev_out if mode == 'catena' else ref_prev
        if mode == 'solo' and nm == 's8':
            pass
        out = BASE + mode + '/%02d_%s.exe' % (i, nm)
        log.write('\n=== %s  in %s (%s)\n' % (nm, inp, md5f(inp)))
        try:
            how, rc, last = stage(nm, inp, out, log)
        except Exception as e:
            how, rc, last = 'eccezione', 1, [repr(e)]
        got = md5f(out) if os.path.exists(out) and rc == 0 else '-'
        ok = got.startswith(m)
        res.append((nm, how, md5f(inp)[:8], got[:8], m[:8], 'SI' if ok else 'NO', (last[0] if last else '')[:150]))
        log.write('-> %s rc=%d out=%s atteso=%s %s\n' % (how, rc, got, m, 'OK' if ok else 'DIVERSO'))
        if mode == 'catena':
            if not ok:
                break
            prev_out = out
        ref_prev = W + ref if ref else out   # nullret non ha exe di riferimento: si usa l'uscita ricostruita
    if mode == 'solo':
        # stadi s1..s7 separatamente (stesso script, --stage N, ingresso tuload)
        tl = W + {c[0]: c for c in CHAIN}['tuload'][2]
        for c in CHAIN:
            if c[0] in ('s1', 's2', 's3', 's4', 's5', 's6', 's7'):
                out = BASE + 'solo/%s.exe' % c[0]
                rc, last = run([SRC + c[3], tl, out] + c[4], log)
                got = md5f(out) if rc == 0 and os.path.exists(out) else '-'
                res.append((c[0], 'script', md5f(tl)[:8], got[:8], c[1][:8], 'SI' if got.startswith(c[1]) else 'NO', (last[0] if last else '')[:150]))
    log.close()
    with open(BASE + mode + '/esito_%s.tsv' % mode, 'w', encoding='utf-8', newline='\n') as f:
        f.write('stadio\tmetodo\tin\tout\tatteso\triprodotto\tultima_riga\n')
        for r in res: f.write('\t'.join(r) + '\n')
    for r in res: print('\t'.join(r))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'solo')
