"""mul_selfcheck.py - (19/11/2026) solo lettura, senza sorgente Xbox (manca ffmpeg su Windows): per ogni .mul di una baseline
non ricodificato da audio_crackle/a12, SNR fra il file decodificato col modello del gioco (imamul.decode_mul: FUN_005957a0,
passo limitato a 8191, nibble 0 ignorato) e col decoder standard FSB per cui la pipeline lo ha codificato; blocchi con
errore massimo > 4096 e nibble 0 non nulli. Un SNR basso = il gioco sente un segnale diverso da quello codificato.
uso: python -I -B mul_selfcheck.py BASELINE"""
import sys, os, struct
import numpy as np
T = '/path/to/trudlcport'
sys.path.insert(0, T + '/tools'); sys.path.insert(0, T + '/work/ws/audio_crackle')
import mul_convert as M
from audio_parse import ima_decode_fsb
from imamul import decode_mul
BS = chr(92)
B = T + '/work/baseline/%s/mods/' % sys.argv[1]
done = set(l.split(None, 1)[1].strip().replace(BS, '/') for l in open(T + '/work/ws/audio_crackle/out/mods/md5.txt'))
for r, _, fs in sorted(os.walk(B)):
    for f in sorted(fs):
        if not f.lower().endswith('.mul'): continue
        rel = os.path.relpath(os.path.join(r, f), B).replace(BS, '/'); pd = open(os.path.join(r, f), 'rb').read()
        nch = struct.unpack_from('<4I', pd, 0)[3]; e2 = s2 = 0.0; nbad = nblk = z0 = 0
        for t, a, b, p in M.blocks(pd, '<'):
            if t: continue
            nb = struct.unpack_from('<I', p, 0)[0]; c = nb // nch
            for k in range(nch):
                d = p[16 + k * c:16 + (k + 1) * c]
                g = np.asarray(decode_mul(d), dtype=np.float64); s = np.asarray(ima_decode_fsb(d), dtype=np.float64); m = min(len(g), len(s))
                err = (g[:m] - s[:m]); e2 += (err ** 2).sum(); s2 += (s[:m] ** 2).sum()
                eb = np.abs(err[:m // 64 * 64]).reshape(-1, 64).max(1) if m >= 64 else np.zeros(0); nbad += int((eb > 4096).sum()); nblk += len(eb)
                z0 += int((np.frombuffer(d, dtype=np.uint8).reshape(-1, 36)[:, 4] & 15 != 0).sum())
        snr = 10 * np.log10(max(s2, 1) / max(e2, 1e-9))
        print('%-8s %-78s SNR gioco/standard %6.1f dB  blocchi err>4096 %5d/%-6d nib0!=0 %d' % ('a12' if rel in done else 'pipeline', rel, snr, nbad, nblk, z0))
