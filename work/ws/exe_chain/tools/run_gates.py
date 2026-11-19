"""run_gates.py - versione Windows di work/ws/b253_catena/run_gates_b253.sh (+ gate b265_sap / b269_crash).
Esegue i gate di emulazione unicorn su COPIE degli script (rebuild/src, percorsi Mac -> Windows, file temporanei dentro exe_chain).
  python -I -B run_gates.py nat   coppia naturale: ingresso dello stadio -> uscita dello stadio (exe di riferimento in work/ws)
  python -I -B run_gates.py fin   ingresso dello stadio -> exe FINALE (2b7ee74c), come il modo 'fin' del .sh
  python -I -B run_gates.py fin EXE   come 'fin' ma con un exe finale diverso (es. un nuovo stadio sopra 2b7ee74c)
Log in work/ws/exe_chain/gates/<modo>/<gate>.txt. Gate che richiedono dump non presenti su questo PC: segnalati MANCA_DUMP."""
import sys, os, re, glob, shutil, subprocess, hashlib
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rebuild as RB
WS = 'C:/tru-port/work/ws/'; SRC = RB.SRC; SWS = SRC + 'work/ws/'
G = 'C:/tru-port/work/ws/exe_chain/gates/'
FINAL = WS + 'b269_crash/tru_s8n_sap_cs2_cs.exe'
LOGF = WS + 'b234/tru_s8n_logf_cs.exe'; ATT = WS + 'b236/tru_s8n_att_cs.exe'; G0 = WS + 'b236/tru_s8n_g0_cs.exe'; FX = WS + 'b236/tru_s8n_fx_cs.exe'
FX2 = WS + 'b236/tru_s8n_fx2_cs.exe'; KEEP = WS + 'b236/tru_s8n_keep_cs.exe'; GP7 = WS + 'b245_fx/tru_s8n_gp7_cs.exe'; DMG = WS + 'b245_qe/tru_s8n_dmg_cs.exe'
B245 = WS + 'b245_all/tru_s8n_b245_cs.exe'; FIN = WS + 'b245_fin/tru_s8n_fin_cs.exe'; DTPG = WS + 'b246_crash/tru_s8n_dtpg_cs.exe'
CHUNK = WS + 'b247_chunk/tru_s8n_chunk_cs.exe'; HAIR = WS + 'b262_hairdump/out/tru_s8n_hairdt_cs.exe'; SAP = WS + 'b265_sap/tru_s8n_sap_cs.exe'
# (nome, gate, ORIG, PAT naturale, json del PAT naturale o None, dump richiesti)
GATES = [
 ('att',  'b236/emu_att.py', LOGF, ATT, None, []),
 ('att3', 'b236/emu_att3.py', LOGF, ATT, None, []),
 ('g0',   'b236/emu_g0.py', ATT, G0, None, []),
 ('fx',   'b250_verifica/emu_fx_local.py', G0, FX, None, []),
 ('fx2',  'b236/emu_fx2.py', FX, FX2, None, []),
 ('keep', 'b236/emu_keep.py', FX2, KEEP, None, []),
 ('b245', 'b245_fx/emu_b245.py', KEEP, GP7, None, []),
 ('dmg',  'b245_qe/emu_dmg.py', KEEP, DMG, None, ['C:/tru-port/work/xbox_exe/tru_base.bin', 'C:/tru-port/work/xbox_exe/tru_patched.bin']),
 ('fin',  'b250_verifica/emu_fin_local.py', B245, FIN, None, []),
 ('dtpg', 'b246_crash/emu_dtpg.py', FIN, DTPG, WS + 'b246_crash/tru_s8n_dtpg_cs.json', ['C:/tru-port/work/crash/B245_lotta/tru.exe.7852.dmp']),
 ('chunk', 'b247_chunk/emu_chunk.py', DTPG, CHUNK, WS + 'b247_chunk/tru_s8n_chunk_cs.json', ['C:/tru-port/work/crash/B246_finisher/live_t43.dmp']),
]
SINGLE = [  # gate a un solo exe (patchato)
 ('sap',  'b265_sap/emu_sapctor.py', SAP),
 ('cs2',  'b269_crash/emu_guard2.py', FINAL),
]


def prepare():
    RB.prepare()
    extra = ['work/ws/b250_verifica']
    for d in extra:
        os.makedirs(SRC + d + '/tmp', exist_ok=True)
        for f in glob.glob('C:/tru-port/' + d + '/*.py'):
            s = open(f, encoding='utf-8').read().replace('/Users/andrearicci/Downloads/tru-port', 'C:/tru-port')
            open(SRC + d + '/' + os.path.basename(f), 'w', encoding='utf-8', newline='').write(s)
    for d in ('b250_verifica', 'b245_fin'): shutil.copy(WS + 'b245_fin/tru_s8n_fin_cs.json', SWS + d + '/tru_s8n_fin_cs.json')
    # nelle copie: ogni riferimento a uno script/cartella copiata -> la copia (cosi' nessun gate scrive o importa dagli originali)
    for f in glob.glob(SRC + 'work/ws/**/*.py', recursive=True) + glob.glob(SRC + 'tools/*.py'):
        s = open(f, encoding='utf-8', errors='surrogateescape').read(); s0 = s
        def rp(m):
            p = m.group(0); rel = p[len('C:/tru-port/'):]
            if os.path.exists(SRC + rel) or rel.startswith('work/ws/b250_verifica/tmp'): return SRC + rel
            return p
        s = s.replace("[sys.executable, '-I',", "[sys.executable, '-I', '-B',")   # i gate rilanciano gli script con -I: senza -B scriverebbero __pycache__ negli originali
        s = re.sub(r"C:/tru-port/(?:work/ws/(?:b236|b245_fx|b245_qe|b245_fin|b246_crash|b247_chunk|b250_verifica|b262_hairdump|b265_sap|b269_crash|dlc2_tuport/exe_build|dlc2_wallvein)|tools)(?:/[A-Za-z0-9_.]+)*", rp, s)
        if s != s0: open(f, 'w', encoding='utf-8', errors='surrogateescape', newline='').write(s)


def run1(name, args, cwd, mode):
    env = dict(RB.ENV); env['PYTHONDONTWRITEBYTECODE'] = '1'
    try:
        r = subprocess.run([sys.executable, '-I', '-B'] + args, capture_output=True, text=True, env=env, cwd=cwd, timeout=900)
        out, rc = r.stdout + r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        out, rc = 'TIMEOUT 900 s', -1
    open(G + mode + '/' + name + '.txt', 'w', encoding='utf-8').write('$ ' + ' '.join(args) + '\n' + out)
    last = out.strip().splitlines()[-1] if out.strip() else ''
    return '%-6s rc=%d %s' % (name, rc, last[:200])


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'nat'
    final = sys.argv[2] if len(sys.argv) > 2 else FINAL
    os.makedirs(G + mode, exist_ok=True); prepare()
    jobs = []
    for name, g, orig, pat, js, dumps in GATES:
        miss = [x for x in dumps if not os.path.exists(x)]
        if miss: jobs.append((name, None, 'MANCA_DUMP ' + ' '.join(miss))); continue
        p = pat if mode == 'nat' else final
        if mode != 'nat' and js:   # il gate legge <NEW>.json: copia del finale accanto al json dello stadio
            p = G + mode + '/final_%s.exe' % name; shutil.copy(final, p); shutil.copy(js, os.path.splitext(p)[0] + '.json')
        jobs.append((name, ([SWS + g, orig, p], os.path.dirname(SWS + g)), None))
    for name, g, exe in SINGLE:
        jobs.append((name, ([SWS + g, exe if mode == 'nat' else final], os.path.dirname(SWS + g)), None))
    with ThreadPoolExecutor(6) as ex:
        futs = [(n, ex.submit(run1, n, a[0], a[1], mode)) if a else (n, msg) for n, a, msg in jobs]
        res = [(f.result() if not isinstance(f, str) else '%-6s %s' % (n, f)) for n, f in futs]
    open(G + mode + '/ESITO.txt', 'w', encoding='utf-8').write('modo %s, finale %s md5 %s\n' % (mode, final, hashlib.md5(open(final, 'rb').read()).hexdigest()) + '\n'.join(res) + '\n')
    print('\n'.join(res))


if __name__ == '__main__':
    main()
