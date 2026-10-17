#!/usr/bin/env python3
"""Sostituisce IN PLACE gli stub di silenzio delle sezioni Wave (tipo 6) di un overlay PC con l'audio vero
convertito dal DRM Xbox d'origine (XMA1 -> FMOD IMA ADPCM, wave_convert.xbox_wave_to_pc).

Perche' in place: la riconversione fresca NON riproduce l'overlay installato (CONOSCENZE: 899 parole divergenti),
quindi si tocca SOLO il payload delle Wave; ogni altro byte del DRM resta identico.

Accoppiamento: k-esima Wave del file PC <-> k-esima Wave del DRM Xbox (ordine dentro il tipo; la conversione
conserva l'ordine). Verifiche per coppia (se una fallisce il FILE viene saltato, nessuna stima):
  - lo stub PC e' silenzio (dati IMA quasi tutti zero) e il suo header (rate, n campioni) == decodifica XMA Xbox;
  - il payload convertito ha la STESSA lunghezza dello stub (IMA a rapporto fisso) -> nessun offset/reloc cambia.
uso: wave_swap.py SRC_MODS_DIR OUT_DIR [nome.drm ...]   (senza nomi: tutti i .drm di SRC con Wave mute)
"""
import sys, os, struct, json
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm, drm_write as DW, wave_convert as WC
from convert_dlc import raw_dlc as _raw_dlc
from archive import Archive
from names import crc
XB_BASE = ['/path/to/TombRaiderUnderworld_Patched/' + f for f in ('layer1.000', 'layer2.000')]

def raw_dlc(name):
    """sorgente Xbox: pacchetti DLC, poi (per i file del gioco base presenti nell'overlay) i layer Xbox base"""
    r, p = _raw_dlc(name)
    if r is not None: return r, p
    for lp in XB_BASE:
        a = Archive(lp, 'be'); rr = [x for x in a.find(crc('xenon-w\\' + name)) if x['spec'] == 0xffffffff]
        if rr: return a.read(rr[0]), lp
    return None, None

HDR = 16 + 0x30 + 0x50                      # pre-header + FSB4 header + sample header

def pc_wave_info(p):
    rate = struct.unpack_from('<I', p, 0)[0]
    length, comp = struct.unpack_from('<II', p, 16 + 0x30 + 0x20)
    return rate, length, comp

def is_silent(p):
    d = p[HDR:]
    return len(d) > 0 and d.count(0) >= 0.97 * len(d)

def swap_file(args):
    src, out = args
    name = os.path.basename(src)
    rep = dict(file=name, waves=0, swapped=0, status='')
    blob = open(src, 'rb').read()
    cd = blob[:4] == b'CDRM'
    raw = drm.cdrm_decode(blob, 'le')
    _, sp = drm.sections_with_data(raw, 'le')
    pw = [s for s in sp if s['type'] == 6]
    rep['waves'] = len(pw)
    if not pw or not any(is_silent(s['data']) for s in pw):
        rep['status'] = 'nessuna wave muta'; return rep
    xr, pack = raw_dlc(name)
    if xr is None:
        rep['status'] = 'SKIP sorgente Xbox non trovata'; return rep
    _, sx = drm.sections_with_data(drm.cdrm_decode(xr, 'be'), 'be')
    xw = [s for s in sx if s['type'] == 6]
    if len(xw) != len(pw):
        rep['status'] = 'SKIP numero wave diverso xbox=%d pc=%d' % (len(xw), len(pw)); return rep
    buf = bytearray(raw)
    errs = []
    for k, (p, x) in enumerate(zip(pw, xw)):
        if not is_silent(p['data']):
            continue                                # gia' audio vero: non toccare
        rate, length, comp = pc_wave_info(p['data'])
        try:
            new, info = WC.xbox_wave_to_pc(x['data'], name=b'silence.wav')
        except Exception as e:
            errs.append('k%d decodifica: %s' % (k, str(e)[:80])); continue
        if info['rate'] != rate or max(info['samples'], 64) != length:
            errs.append('k%d header stub (%d,%d) != xbox (%d,%d)' % (k, rate, length, info['rate'], info['samples'])); continue
        if len(new) != len(p['data']):
            errs.append('k%d dimensione %d != %d' % (k, len(new), len(p['data']))); continue
        buf[p['data_off']:p['data_off'] + p['size']] = new
        rep['swapped'] += 1
    if errs:
        rep['status'] = 'SKIP %d coppie non verificate: %s' % (len(errs), '; '.join(errs[:4])); rep['swapped'] = 0
        return rep
    assert len(buf) == len(raw)
    _, chk = drm.sections_with_data(bytes(buf), 'le')
    assert [(s['type'], s['id'], s['size']) for s in chk] == [(s['type'], s['id'], s['size']) for s in sp]
    # tutto cio' che non e' payload Wave deve restare identico
    for a, b in zip(sp, chk):
        if a['type'] != 6: assert a['data'] == b['data'] and a['reloc'] == b['reloc']
    data = DW.cdrm_encode(bytes(buf), 'le') if cd else bytes(buf)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'wb').write(data)
    rep['status'] = 'OK'
    return rep

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    names = sys.argv[3:] or sorted(f for f in os.listdir(src) if f.endswith('.drm'))
    jobs = [(os.path.join(src, n), os.path.join(dst, n)) for n in names]
    reps = []
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
        for r in ex.map(swap_file, jobs):
            reps.append(r)
            if r['waves']: print('%-50s wave=%4d sostituite=%4d  %s' % (r['file'], r['waves'], r['swapped'], r['status']), flush=True)
    os.makedirs(dst, exist_ok=True)
    json.dump(reps, open(os.path.join(dst, 'wave_swap_report.json'), 'w'), indent=1)
    print('TOTALE sostituite', sum(r['swapped'] for r in reps), 'file OK', sum(r['status'] == 'OK' for r in reps))
