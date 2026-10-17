#!/usr/bin/env python3
"""Applica mul_audio.swap a tutti i .mul di un overlay (cinstream, music, audio\\streams) prendendo la sorgente Xbox dai
pacchetti DLC (stessa scelta di variante di music_convert: 0xffffffff, poi 0xffffffe1 = inglese, poi la prima).
uso: mul_audio_batch.py SRC_MODS_DIR OUT_DIR"""
import sys, os, json
import numpy as np
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mul_audio as MA
from archive import Archive
from names import crc
from convert_dlc import R, PACKS

def find_xb(rel):
    nm = 'xenon-w\\' + rel.replace('/', '\\')
    for p in PACKS:
        a = Archive(R + p, 'be'); rr = {x['spec']: x for x in a.find(crc(nm))}
        if rr:
            sp = 0xffffffff if 0xffffffff in rr else (0xffffffe1 if 0xffffffe1 in rr else sorted(rr)[0])
            return a.read(rr[sp]), p.split('/')[1], sp, sorted(hex(s) for s in rr)
    return None, None, None, None

def job(args):
    src, out, rel = args
    pd = open(src, 'rb').read()
    xd, pack, sp, specs = find_xb(rel)
    r = dict(file=rel, pack=pack, spec=hex(sp) if sp else None, variants=specs)
    if xd is None: r['status'] = 'SKIP sorgente Xbox non trovata'; return r
    try:
        o, info = MA.swap(xd, pd)
    except Exception as e:
        r['status'] = 'SKIP ' + str(e)[:120]; return r
    q = MA.pc_pcm(o)
    r.update(info); r['rms'] = int(np.sqrt((q.astype(float) ** 2).mean()))
    if len(o) != len(pd): r['status'] = 'SKIP dimensione'; return r
    os.makedirs(os.path.dirname(out), exist_ok=True); open(out, 'wb').write(o)
    r['status'] = 'OK'; return r

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    jobs = []
    for dp, dn, fn in os.walk(src):
        for f in fn:
            if f.endswith('.mul'):
                rel = os.path.relpath(os.path.join(dp, f), src)
                jobs.append((os.path.join(dp, f), os.path.join(dst, rel), rel))
    reps = []
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
        for r in ex.map(job, sorted(jobs)):
            reps.append(r); print('%-75s %-6s %s rms=%s campioni=%s/%s %s' % (r['file'], r['pack'], r['spec'], r.get('rms'), r.get('samples'), r.get('xb_total'), r['status']), flush=True)
    os.makedirs(dst, exist_ok=True)
    json.dump(reps, open(os.path.join(dst, 'mul_audio_report.json'), 'w'), indent=1)
    print('OK', sum(r['status'] == 'OK' for r in reps), 'di', len(reps))
