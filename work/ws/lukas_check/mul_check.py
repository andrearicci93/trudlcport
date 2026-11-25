"""mul_check.py - (19/11/2026) solo lettura, dalla segnalazione di Lukas (issue #5): i .mul di una baseline non ricodificati
da audio_crackle/a12 (decoder del gioco FUN_005957a0, passo limitato a 8191, nibble 0 ignorato). Per file: SNR per canale del
file installato decodificato col modello del gioco contro la sorgente Xbox, nibble 0 non nulli, e SNR della ricodifica a12
(calcolata in memoria, niente scritto).
uso: python -I -B mul_check.py BASELINE"""
import sys, os, struct, json, hashlib
import numpy as np
from concurrent.futures import ProcessPoolExecutor
T = '/path/to/trudlcport'
sys.path.insert(0, T + '/tools'); sys.path.insert(0, T + '/work/ws/audio_crackle')
import a12_reencode_mul as A, mul_convert as M
BS = chr(92)
def nib0(o):
    return sum(int((np.frombuffer(p[16:16 + struct.unpack_from('<I', p, 0)[0]], dtype=np.uint8).reshape(-1, 36)[:, 4] & 15 != 0).sum()) for t, a, b, p in M.blocks(o, '<') if t == 0)
def job(a):
    p, rel = a
    import mul_audio_batch as MB
    try:
        pd = open(p, 'rb').read(); xd = MB.find_xb(rel)[0]
        if xd is None: return dict(file=rel, status='SKIP xbox')
        o, x, info = A.swap(xd, pd)
        q0, q1 = A.game_pcm(pd), A.game_pcm(o)
        s0 = [round(A.snr_ch(q0[:, k], x[:, k]), 1) for k in range(info['nch'])]
        s1 = [round(A.snr_ch(q1[:, k], x[:, k]), 1) for k in range(info['nch'])]
        return dict(file=rel, status='OK', snr_installato=s0, snr_a12=s1, nib0_installato=nib0(pd), nib0_a12=nib0(o), identico_a12=(o == pd))
    except Exception as e: return dict(file=rel, status='ERR %r' % e)
if __name__ == '__main__':
    B = T + '/work/baseline/%s/mods/' % sys.argv[1]
    done = set(l.split(None, 1)[1].strip().replace(BS, '/') for l in open(T + '/work/ws/audio_crackle/out/mods/md5.txt'))
    jobs = sorted((os.path.join(r, f), os.path.relpath(os.path.join(r, f), B).replace(BS, '/')) for r, _, fs in os.walk(B) for f in fs if f.lower().endswith('.mul'))
    jobs = [j for j in jobs if j[1] not in done]
    reps = []
    with ProcessPoolExecutor(max_workers=max(1, (os.cpu_count() or 2) // 2)) as ex:
        for r in ex.map(job, jobs):
            reps.append(r); print('%-75s %s inst %s a12 %s nib0 %s/%s identico %s' % (r['file'], r['status'], r.get('snr_installato'), r.get('snr_a12'), r.get('nib0_installato'), r.get('nib0_a12'), r.get('identico_a12')), flush=True)
    json.dump(reps, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mul_check_%s.json' % sys.argv[1]), 'w'), indent=1)
