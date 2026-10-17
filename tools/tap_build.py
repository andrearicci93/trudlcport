#!/usr/bin/env python3
"""Costruisce tru_tap.exe: exe unpacked + sezione .tap + call dei siti di log riscritte verso gli stub (M0.2).
Spec: PIANO_SONNET.md, Appendice B. Dipende da tap_stubs.py e work/ws/tap/sites.tsv (+ sites.meta.json).

  tools/venv/bin/python -I tools/tap_build.py                       # build di default (635 A fmt + 16 B)
  tools/venv/bin/python -I tools/tap_build.py --wide --exclude 0x423b19,0x432887 --only-half 1

Opzioni:
  --wide              aggiunge i siti A con kind 'args' (224)
  --exclude RET,...   ret_va esadecimali (ret = call+5) da silenziare; devono esistere in sites.tsv
  --probes FILE       JSON: lista di {"va": "0x...", "nome": "..."} (oppure {"probes": [...]}).
                      "va" = indirizzo di una call rel32 (E8) da deviare su uno stub sonda
                      (tap_stubs.stub_probe): lo stub registra gli argomenti e salta alla funzione
                      originalmente chiamata. Max 24 sonde; id = posizione nella lista.
                      Le sonde non sono influenzate da --only-half.
  --only-half 1|2     solo la prima (1) o la seconda (2) metà dei siti A+B selezionati, ordinati per
                      call_va (metà = sites[:n//2] / sites[n//2:]), per bisezione
  --out-dir DIR       default work/ws/tap

Output in out-dir: tru_tap.exe, sites_patched.tsv, build.json.
sites_patched.tsv: colonne di sites.tsv + stub_va + probe_id (chan 'P' = sonda); ordinato per call_va.
build_id = primi 4 byte dell'md5 di sites_patched.tsv, scritti a T+0x14 (u32 little-endian; hex in build.json).
Scrive SOLO rel32 delle call scelte, pe+6 (NumberOfSections 6->7), SizeOfImage (0xe36000->0xe86000),
header di sezione a 0x2e8, e appende 0x1000 byte di sezione. Verifiche prima di scrivere qualunque file.
Con --probes la coda non è uguale a raw_section(build_id) ma a raw_section con gli stub sonda sovrapposti
(T+0x300 + k*0x80): deviazione dalla spec, dichiarata in build.json.
"""
import argparse, hashlib, json, os, struct, sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)          # con -I lo script dir non è in sys.path
import capstone
import tap_stubs as ts

IB = 0x400000
IN_PATH = os.path.join(W, 'work/laa/tru_steam.exe.unpacked.exe')
SITES_DIR = os.path.join(W, 'work/ws/tap')
IN_MD5 = '56d1ce2dffa62f16354063da2df44d5a'
IN_SIZE = 0x620000
HDR_OFF = 0x2e8
SIZE_OF_HEADERS_MIN = HDR_OFF + 0x28
OLD_NSEC, NEW_NSEC = 6, 7
OLD_SIZEIMG, NEW_SIZEIMG = 0xe36000, 0xe86000
TARGET = {'A': 0x6457a0, 'B': 0x48e200}
STUB = {'A': ts.STUB_A, 'B': ts.STUB_B}
DEFAULT_KINDS = {'fmt0', 'fmt1', 'fmt2'}
TSV_COLS = ['chan', 'call_va', 'ret_va', 'kind', 'add_esp', 'fmt_arg', 'fmt']
OUT_COLS = TSV_COLS + ['stub_va', 'probe_id']

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)


def die(msg):
    print('ERRORE: ' + msg, file=sys.stderr)
    sys.exit(1)


def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def u32(b, o): return struct.unpack_from('<I', b, o)[0]
def md5hex(b): return hashlib.md5(b).hexdigest()
def align(x, a): return (x + a - 1) // a * a


def rel_target(data, call_va):
    """Target assoluto di una call/jmp rel32 a file offset call_va-IB (data = file)."""
    o = call_va - IB
    rel = struct.unpack_from('<i', data, o + 1)[0]
    return (call_va + 5 + rel) & 0xffffffff


def load_sites():
    meta_p = os.path.join(SITES_DIR, 'sites.meta.json')
    tsv_p = os.path.join(SITES_DIR, 'sites.tsv')
    if not os.path.exists(meta_p) or not os.path.exists(tsv_p):
        die('mancano sites.tsv / sites.meta.json in ' + SITES_DIR)
    meta = json.load(open(meta_p))
    if meta.get('exe_md5') != IN_MD5:
        die('sites.meta.json exe_md5 %s != %s' % (meta.get('exe_md5'), IN_MD5))
    raw = open(tsv_p, 'rb').read()
    if md5hex(raw) != meta.get('sites_md5'):
        die('md5 di sites.tsv diverso da sites.meta.json')
    lines = raw.decode('latin1').split('\n')
    if lines[-1] == '':
        lines.pop()
    if lines[0].split('\t') != TSV_COLS:
        die('intestazione sites.tsv inattesa: ' + lines[0])
    rows = []
    for ln in lines[1:]:
        f = ln.split('\t')
        if len(f) < 6:
            die('riga sites.tsv malformata: ' + ln)
        r = {'chan': f[0], 'call_va': int(f[1], 16), 'ret_va': int(f[2], 16), 'kind': f[3],
             'add_esp': int(f[4]), 'fmt_arg': int(f[5]), 'fmt': f[6] if len(f) > 6 else ''}
        if r['chan'] not in ('A', 'B') or r['ret_va'] != r['call_va'] + 5:
            die('riga sites.tsv incoerente: ' + ln)
        rows.append(r)
    return rows


def check_input(data):
    if len(data) != IN_SIZE:
        die('dimensione input %#x != %#x (overlay o troncamento)' % (len(data), IN_SIZE))
    if md5hex(data) != IN_MD5:
        die('md5 input %s != %s' % (md5hex(data), IN_MD5))
    pe = u32(data, 0x3c)
    if data[pe:pe + 4] != b'PE\0\0':
        die('firma PE assente')
    if u16(data, pe + 6) != OLD_NSEC:
        die('NumberOfSections != 6')
    if u32(data, pe + 0x50) != OLD_SIZEIMG:
        die('SizeOfImage != 0xe36000')
    size_hdrs = u32(data, pe + 0x54)
    if SIZE_OF_HEADERS_MIN > size_hdrs:
        die('0x2e8+0x28 > SizeOfHeaders')
    table = pe + 0x18 + u16(data, pe + 0x14)
    if table + OLD_NSEC * 40 != HDR_OFF:
        die('fine tabella sezioni %#x != 0x2e8' % (table + OLD_NSEC * 40))
    if data[HDR_OFF:HDR_OFF + 40] != bytes(40):
        die('40 byte a 0x2e8 non azzerati')
    file_align = u32(data, pe + 0x18 + 0x24)      # FileAlignment in optional header PE32
    if IN_SIZE % file_align:
        die('0x620000 non allineato a FileAlignment')
    max_raw = max_va = 0
    for i in range(OLD_NSEC):
        h = table + 40 * i
        vsz, va, rsz, rptr = struct.unpack_from('<IIII', data, h + 8)
        max_raw = max(max_raw, rptr + rsz)
        max_va = max(max_va, va + align(vsz, 0x1000))
    if max_raw != IN_SIZE:
        die('fine dati sezioni %#x != file %#x (overlay?)' % (max_raw, IN_SIZE))
    if max_va > OLD_SIZEIMG:
        die('sezioni oltre 0xe36000')
    return pe, size_hdrs, file_align


def load_probes(path):
    j = json.load(open(path))
    if isinstance(j, dict):
        j = j.get('probes')
    if not isinstance(j, list):
        die('probes.json: attesa lista di {va, nome}')
    if len(j) > ts.PROBE_MAX:
        die('probes.json: massimo %d sonde' % ts.PROBE_MAX)
    out = []
    for p in j:
        va = p['va']
        va = int(va, 0) if isinstance(va, str) else int(va)
        nome = str(p.get('nome', '')).replace('\t', ' ').replace('\n', ' ')
        kind = str(p.get('kind', 'entry'))
        if kind not in ('entry', 'ret'):
            die('probes.json: kind deve essere entry|ret')
        out.append({'va': va, 'nome': nome, 'kind': kind})
    return out


def select(rows, opts):
    cand = [r for r in rows if (r['chan'] == 'B') or
            (r['chan'] == 'A' and (r['kind'] in DEFAULT_KINDS or (opts.wide and r['kind'] == 'args')))]
    if opts.exclude:
        ex = set()
        for s in opts.exclude.split(','):
            s = s.strip()
            if not s:
                continue
            v = int(s, 16)
            if not any(r['ret_va'] == v for r in rows):
                die('--exclude %#x non presente in sites.tsv' % v)
            ex.add(v)
    else:
        ex = set()
    excluded = [r for r in cand if r['ret_va'] in ex]
    sel = [r for r in cand if r['ret_va'] not in ex]
    sel.sort(key=lambda r: r['call_va'])
    if opts.only_half:
        h = len(sel) // 2
        sel = sel[:h] if opts.only_half == 1 else sel[h:]
    return sel, excluded


def build_bytes(exe, sel, probes, build_id):
    """Ritorna (exe_out, tail_expected, patches) con i soli byte scritti; nessuna dipendenza da stato globale."""
    out = bytearray(exe)
    pe = u32(exe, 0x3c)
    patches = []   # (call_va, target_va, kind)
    for r in sel:
        o = r['call_va'] - IB
        if exe[o] != 0xe8:
            die('call_va %#x non è E8' % r['call_va'])
        if rel_target(exe, r['call_va']) != TARGET[r['chan']]:
            die('call %#x (%s) non va a %#x' % (r['call_va'], r['chan'], TARGET[r['chan']]))
        stub = STUB[r['chan']]
        struct.pack_into('<i', out, o + 1, stub - (r['call_va'] + 5))
        patches.append((r['call_va'], stub, r['chan']))
    tail = bytearray(ts.raw_section(build_id))
    probe_rows = []
    for k, p in enumerate(probes):
        o = p['va'] - IB
        if exe[o] != 0xe8:
            die('sonda %d: %#x non è una call rel32 (E8)' % (k, p['va']))
        callee = rel_target(exe, p['va'])
        if p['kind'] == 'ret':
            if k >= ts.RET_MAX:
                die('sonda %d: le sonde a ritorno sono ammesse solo per id < %d' % (k, ts.RET_MAX))
            pva, code = ts.stub_retprobe(k, callee)
            cr = ts.common_ret()
            tail[ts.COMMON_RET - ts.T: ts.COMMON_RET - ts.T + len(cr)] = cr
        else:
            pva, code = ts.stub_probe(k, callee)
        tail[pva - ts.T: pva - ts.T + len(code)] = code
        struct.pack_into('<i', out, o + 1, pva - (p['va'] + 5))
        patches.append((p['va'], pva, 'P'))
        probe_rows.append({'chan': 'P', 'call_va': p['va'], 'ret_va': p['va'] + 5, 'kind': ('retprobe' if p['kind'] == 'ret' else 'probe'),
                           'add_esp': 0, 'fmt_arg': -1, 'fmt': p['nome'], 'stub_va': pva, 'probe_id': k,
                           'callee': callee})
    # (a) header: NumberOfSections, SizeOfImage, section header a 0x2e8
    struct.pack_into('<H', out, pe + 6, NEW_NSEC)
    struct.pack_into('<I', out, pe + 0x50, NEW_SIZEIMG)
    out[HDR_OFF:HDR_OFF + 40] = ts.section_header()
    out += tail
    return bytes(out), bytes(tail), patches, probe_rows


def tsv_bytes(sel, probe_rows):
    recs = []
    for r in sel:
        stub = STUB[r['chan']]
        recs.append((r['call_va'], [r['chan'], '%#x' % r['call_va'], '%#x' % r['ret_va'], r['kind'],
                                   str(r['add_esp']), str(r['fmt_arg']), r['fmt'], '%#x' % stub, '']))
    for pr in probe_rows:
        recs.append((pr['call_va'], ['P', '%#x' % pr['call_va'], '%#x' % pr['ret_va'], pr['kind'],
                                    '0', '-1', pr['fmt'], '%#x' % pr['stub_va'], str(pr['probe_id'])]))
    recs.sort(key=lambda t: (t[0], t[1][0]))
    lines = ['\t'.join(OUT_COLS)] + ['\t'.join(c) for _, c in recs]
    return ('\n'.join(lines) + '\n').encode('latin1')


def verify(exe, out, tail_exp, patches, sel, probe_rows, build_id, pe, file_align):
    # (a) diff: solo rel32 scelti, pe+6, pe+0x50, header di sezione
    allowed = set()
    for call_va, _, _ in patches:
        o = call_va - IB
        allowed.update(range(o + 1, o + 5))
    allowed.update({pe + 6, pe + 7})
    allowed.update(range(pe + 0x50, pe + 0x54))
    allowed.update(range(HDR_OFF, HDR_OFF + 40))
    changed = [i for i in range(len(exe)) if exe[i] != out[i]]
    bad = [i for i in changed if i not in allowed]
    if bad:
        die('byte cambiati fuori dalle aree previste: ' + ' '.join('%#x' % i for i in bad[:10]))
    if u16(out, pe + 6) != NEW_NSEC or u32(out, pe + 0x50) != NEW_SIZEIMG:
        die('NumberOfSections/SizeOfImage non aggiornati')
    if bytes(out[HDR_OFF:HDR_OFF + 40]) != ts.section_header():
        die('header di sezione .tap diverso da section_header()')
    # (b) coda
    if len(out) != IN_SIZE + ts.RAWSIZE:
        die('lunghezza output inattesa')
    if bytes(out[IN_SIZE:]) != tail_exp:
        die('coda appesa diversa dalla raw_section attesa')
    if tail_exp[0x14:0x18] != build_id.to_bytes(4, 'little') or tail_exp[:4] != b'TAP1':
        die('build id / magic non a T+0x14 / T+0')
    # ridisassemblaggio
    for call_va, target, chan in patches:
        ins = list(MD.disasm(bytes(out[call_va - IB: call_va - IB + 5]), call_va))
        if len(ins) != 1 or ins[0].size != 5 or ins[0].mnemonic != 'call':
            die('sito %#x non ridisassembla come call a 5 byte' % call_va)
        if int(ins[0].op_str, 16) != target:
            die('sito %#x (%s) va a %s, atteso %#x' % (call_va, chan, ins[0].op_str, target))
    return len(changed)


def check_disasm_input(exe, sel):
    for r in sel:
        ins = list(MD.disasm(exe[r['call_va'] - IB: r['call_va'] - IB + 5], r['call_va']))
        if not ins or ins[0].mnemonic != 'call' or int(ins[0].op_str, 16) != TARGET[r['chan']]:
            die('input: %#x non è call a %#x' % (r['call_va'], TARGET[r['chan']]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--wide', action='store_true')
    ap.add_argument('--exclude', default='')
    ap.add_argument('--probes', default='')
    ap.add_argument('--only-half', type=int, choices=[1, 2], default=0)
    ap.add_argument('--out-dir', default=SITES_DIR)
    opts = ap.parse_args()

    ts.selftest(verbose=True)
    exe = open(IN_PATH, 'rb').read()
    pe, size_hdrs, file_align = check_input(exe)
    rows = load_sites()
    sel, excluded = select(rows, opts)
    if not opts.wide and not opts.exclude and not opts.only_half and not opts.probes:
        nA = sum(1 for r in sel if r['chan'] == 'A')
        nB = sum(1 for r in sel if r['chan'] == 'B')
        if (nA, nB) != (635, 16):
            die('default: attesi 635 A e 16 B, trovati %d/%d' % (nA, nB))
    check_disasm_input(exe, sel)
    probes = load_probes(opts.probes) if opts.probes else []
    if probes:
        sel_vas = {r['call_va'] for r in sel}
        for p in probes:
            if p['va'] in sel_vas:
                die('sonda %#x coincide con un sito di log' % p['va'])
        if len({p['va'] for p in probes}) != len(probes):
            die('sonde duplicate')

    # build_id dal sites_patched.tsv (che non dipende dal build_id)
    _, _, _, probe_rows = build_bytes(exe, sel, probes, 0)
    tsv = tsv_bytes(sel, probe_rows)
    digest = hashlib.md5(tsv).digest()
    build_id = int.from_bytes(digest[:4], 'little')

    out1, tail1, patches, probe_rows = build_bytes(exe, sel, probes, build_id)
    out2, _, _, _ = build_bytes(exe, sel, probes, build_id)
    if md5hex(out1) != md5hex(out2):
        die('build non deterministica')
    n_changed = verify(exe, out1, tail1, patches, sel, probe_rows, build_id, pe, file_align)
    if probes:
        dev = 'coda = raw_section(build_id) con stub sonda sovrapposti (deviazione dalla spec)'
    else:
        if tail1 != bytes(ts.raw_section(build_id)):
            die('coda != raw_section(build_id)')
        dev = None

    os.makedirs(opts.out_dir, exist_ok=True)
    exe_p = os.path.join(opts.out_dir, 'tru_tap.exe')
    tsv_p = os.path.join(opts.out_dir, 'sites_patched.tsv')
    json_p = os.path.join(opts.out_dir, 'build.json')
    open(tsv_p, 'wb').write(tsv)
    if md5hex(open(tsv_p, 'rb').read()) != digest.hex():
        die('sites_patched.tsv riletto con md5 diverso')
    open(exe_p, 'wb').write(out1)
    if md5hex(open(exe_p, 'rb').read()) != md5hex(out1):
        die('tru_tap.exe riletto diverso')
    n = {c: sum(1 for r in sel if r['chan'] == c) for c in 'AB'}
    n['P'] = len(probes)
    info = {
        'in_md5': IN_MD5,
        'out_md5': md5hex(out1),
        'n_siti': n,
        'n_siti_A_per_kind': {k: sum(1 for r in sel if r['chan'] == 'A' and r['kind'] == k)
                              for k in sorted({r['kind'] for r in sel if r['chan'] == 'A'})},
        'build_id': '0x%08x' % build_id,
        'build_id_bytes_T14': digest[:4].hex(),
        'build_id_nota': 'bytes a T+0x14 = primi 4 byte di md5(sites_patched.tsv), u32 little-endian; u32 = build_id',
        'sites_patched_md5': digest.hex(),
        'esclusi': [{'chan': r['chan'], 'call_va': '%#x' % r['call_va'], 'ret_va': '%#x' % r['ret_va']} for r in excluded],
        'changed_bytes_in_file': n_changed,
        'probes': [{'id': p['probe_id'], 'va': '%#x' % p['call_va'], 'nome': p['fmt'],
                    'callee': '%#x' % p['callee'], 'stub_va': '%#x' % p['stub_va']} for p in probe_rows],
        'deviazioni': [dev] if dev else [],
        'opzioni': {'wide': opts.wide, 'exclude': opts.exclude, 'probes': opts.probes or None,
                    'only_half': opts.only_half, 'out_dir': opts.out_dir},
        'checks': {'input_md5_size_overlay': True, 'stub_selftest': True, 'diff_a': True, 'tail_b': True,
                   'disasm': True, 'deterministic': True, 'tsv_md5': True, 'header_0x2e8_zero': True,
                   'size_of_headers': size_hdrs},
    }
    open(json_p, 'w').write(json.dumps(info, indent=1, sort_keys=True) + '\n')
    print('out_md5 %s' % info['out_md5'])
    print('siti A %d (per kind %s) / B %d / sonde %d; esclusi %d' % (
        n['A'], info['n_siti_A_per_kind'], n['B'], n['P'], len(excluded)))
    print('build_id %s ; modifiche byte nel file originale %d' % (info['build_id'], n_changed))
    print('controlli: input OK, selftest OK, diff(a) OK, coda(b) OK, disasm OK, deterministico OK, tsv md5 OK')
    if dev:
        print('ATTENZIONE: ' + dev)
    print('scritti: %s, %s, %s' % (exe_p, tsv_p, json_p))


if __name__ == '__main__':
    main()
