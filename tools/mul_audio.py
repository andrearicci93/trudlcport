#!/usr/bin/env python3
"""Audio vero per i .mul (cinstream, music, audio\\streams): decodifica XMA Xbox -> IMA stereo PC, sostituito IN PLACE
negli stub di silenzio dei .mul gia' convertiti (mul_convert / music_convert), senza toccare i blocchi cine.

Formato blocco audio Xbox (verificato su 001_pro_corridor): payload = 1..N sotto-pacchetti
  {u32 BE 2048, u32 BE canale, 0, 0} + 2048 B di pacchetto XMA1 -> un flusso XMA1 MONO per canale.
Il flusso di ogni canale si decodifica avvolgendolo in un RIFF XMA1 mono (fmt come le sezioni Wave) con ffmpeg.
Blocco audio PC: {u32 nbytes, 0, 0, 0} + PRIMA tutti i blocchi IMA da 36 B (64 campioni) del canale sinistro, POI tutti
quelli del destro (verificato: correlazione 0,98 con l'audio PC vero; l'alternanza L/R per 64 campioni da' 0); il blocco i
copre i campioni [a_i, a_i + 64 * nblocchi_per_canale) e a_i e' nel campo 'a' dell'intestazione del blocco.
uso: mul_audio.py validate NOME            (work/mul/NOME.xb.mul vs .pc.mul: correlazione con l'audio PC vero)
     mul_audio.py swap XBOX.mul PC_IN.mul PC_OUT.mul
"""
import sys, os, struct, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mul_convert as M
from audio_parse import FFMPEG, ima_decode_fsb
from wave_convert import ima_encode_fsb

def xb_channels(xd):
    rate, _, total, nch = struct.unpack_from('>4I', xd, 0)
    ch = {}
    for t, a, b, p in M.blocks(xd, '>'):
        if t != 0: continue
        o = 0
        while o + 16 <= len(p):
            sz, c = struct.unpack_from('>II', p, o)
            if sz == 0 or o + 16 + sz > len(p): raise ValueError('sotto-pacchetto anomalo a %x' % o)
            ch.setdefault(c, bytearray()).extend(p[o + 16:o + 16 + sz]); o += 16 + sz
    return rate, total, nch, [bytes(ch[k]) for k in sorted(ch)]

def riff_xma1_mono(data, rate):
    fmt = struct.pack('<HHHHBBBx', 0x165, 16, 0x10d6, 0, 1, 0, 2)   # tag, bits, encOpts, largestSkip, nStreams, loop, ver
    fmt += struct.pack('<IIIIBBH', rate * 2 // 3, rate, 0, 0, 0, 1, 1)    # bytes/s (indicativo), rate, loop, subframe, ch, mask
    body = b'WAVE' + b'fmt ' + struct.pack('<I', len(fmt)) + fmt + b'data' + struct.pack('<I', len(data)) + data
    return b'RIFF' + struct.pack('<I', len(body)) + body

def decode_mono(data, rate):
    pr = subprocess.run([FFMPEG, '-v', 'error', '-i', 'pipe:0', '-f', 's16le', '-ac', '1', 'pipe:1'],
                        input=riff_xma1_mono(data, rate), capture_output=True)
    if not pr.stdout: raise ValueError('ffmpeg: ' + pr.stderr.decode()[:200])
    return np.frombuffer(pr.stdout, dtype='<i2').astype(np.int32)

def xb_pcm(xd):
    rate, total, nch, chans = xb_channels(xd)
    pcm = [decode_mono(c, rate) for c in chans]
    n = max(len(p) for p in pcm)
    out = np.zeros((n, len(pcm)), dtype=np.int32)
    for k, p in enumerate(pcm): out[:len(p), k] = p
    return rate, total, out

def pc_audio_blocks(pd):
    return [(t, a, p) for t, a, b, p in M.blocks(pd, '<') if t == 0]

def pc_pcm(pd):
    seg = []
    for t, a, p in pc_audio_blocks(pd):
        nbytes = struct.unpack_from('<I', p, 0)[0]
        d = p[16:16 + nbytes]; h = len(d) // 2
        L = ima_decode_fsb(d[:h]); R = ima_decode_fsb(d[h:])
        seg.append((a, np.stack([L, R], 1)))
    n = max(a + len(s) for a, s in seg)
    out = np.zeros((n, 2), dtype=np.int32)
    for a, s in seg: out[a:a + len(s)] = s
    return out

def encode_stereo(pcm):
    """pcm [n,2] -> (L [nblk,36], R [nblk,36]) blocchi IMA da 64 campioni per canale"""
    L, nb = ima_encode_fsb(pcm[:, 0]); R, _ = ima_encode_fsb(pcm[:, 1] if pcm.shape[1] > 1 else pcm[:, 0])
    return np.frombuffer(L, dtype=np.uint8).reshape(nb, 36), np.frombuffer(R, dtype=np.uint8).reshape(nb, 36)

def swap(xd, pd):
    """sostituisce i dati IMA dei blocchi audio di pd (stub di silenzio) con l'audio Xbox decodificato; stessa dimensione"""
    rate, total, pcm = xb_pcm(xd)
    n = max(a + (struct.unpack_from('<I', p, 0)[0] // 72) * 64 for t, a, p in pc_audio_blocks(pd))
    if len(pcm) < n: pcm = np.vstack([pcm, np.zeros((n - len(pcm), pcm.shape[1]), dtype=np.int32)])
    EL, ER = encode_stereo(pcm[:n])
    out = bytearray(pd); o = 0x800; nsw = 0
    while o + 16 <= len(out):
        t, sz, a, b = struct.unpack_from('<4I', out, o)
        if t == 0:
            nbytes = struct.unpack_from('<I', out, o + 16)[0]
            k0, nb = a // 64, nbytes // 72
            assert a % 64 == 0 and nbytes % 72 == 0 and 16 + nbytes <= sz
            out[o + 32:o + 32 + nbytes] = EL[k0:k0 + nb].tobytes() + ER[k0:k0 + nb].tobytes(); nsw += 1
        o += 16 + sz
    assert o == len(out) and len(out) == len(pd)
    return bytes(out), dict(rate=rate, xb_total=total, samples=len(pcm), blocks=nsw)

def corr(a, b, maxs=44100 * 8):
    """correlazione normalizzata massima (FFT) e ritardo, sui primi maxs campioni"""
    n = min(len(a), len(b), maxs); u = a[:n].astype(float); v = b[:n].astype(float)
    u -= u.mean(); v -= v.mean(); N = 1 << int(np.ceil(np.log2(2 * n)))
    c = np.fft.irfft(np.fft.rfft(u, N) * np.conj(np.fft.rfft(v, N)), N)
    k = int(np.argmax(c)); den = np.linalg.norm(u) * np.linalg.norm(v)
    return (c[k] / den if den else 0.0), (k if k < N // 2 else k - N)

if __name__ == '__main__':
    if sys.argv[1] == 'validate':
        W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'mul')
        for name in sys.argv[2:]:
            xd = open(os.path.join(W, name + '.xb.mul'), 'rb').read(); pd = open(os.path.join(W, name + '.pc.mul'), 'rb').read()
            rate, total, x = xb_pcm(xd); p = pc_pcm(pd)
            print(name, 'xb rate', rate, 'total', total, 'decodificati', len(x), '| pc campioni', len(p),
                  'corr L', '%.3f lag %d' % corr(x[:, 0], p[:, 0]), 'corr R', '%.3f lag %d' % corr(x[:, -1], p[:, 1]),
                  'rms xb', int(np.sqrt((x.astype(float) ** 2).mean())), 'rms pc', int(np.sqrt((p.astype(float) ** 2).mean())))
            # prova di swap: il .mul PC con l'audio sostituito deve avere la stessa dimensione
            out, info = swap(xd, pd); q = pc_pcm(out)
            print('   swap', info, 'corr(ricodificato, pc) L %.3f' % corr(q[:, 0], p[:, 0])[0])
    elif sys.argv[1] == 'swap':
        xd = open(sys.argv[2], 'rb').read(); pd = open(sys.argv[3], 'rb').read()
        out, info = swap(xd, pd); open(sys.argv[4], 'wb').write(out); print(info)
