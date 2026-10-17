#!/usr/bin/env python3
"""Xbox 360 TR8 Wave section (type 6) -> PC Wave section payload.

PC payload  = 16B LE pre-header [rate, 0, pre2, pre3] + FSB4 (1 sample, mono FMOD IMA ADPCM, 36B/64-sample blocks)
Xbox payload= 16B BE pre-header [rate, 0, pre2, pre3] + RIFF/WAVE, fmt 0x165 (XMA1), mono 
Pipeline: strip pre-header -> ffmpeg decodes XMA1 -> PCM s16 -> IMA encode -> FSB4 wrap.
Usage (library): xbox_wave_to_pc(payload) ; make_silence_wave(nsamples, rate)
"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from audio_parse import xma_decode, IMA_STEP, IMA_IDX, parse_pc, parse_xb

_ST = np.array(IMA_STEP, dtype=np.int32); _IX = np.array(IMA_IDX, dtype=np.int32)

def _enc_step(s, pred, idx):
    step = _ST[idx]
    d = s - pred
    sign = d < 0
    d = np.abs(d)
    nib = np.zeros_like(d)
    vp = step >> 3
    m = d >= step; nib |= m * 4; d = d - m * step; vp = vp + m * step
    st = step >> 1
    m = d >= st; nib |= m * 2; d = d - m * st; vp = vp + m * st
    st = step >> 2
    m = d >= st; nib |= m * 1; vp = vp + m * st
    pred = np.clip(pred + np.where(sign, -vp, vp), -32768, 32767)
    idx = np.clip(idx + _IX[nib & 7], 0, 88)
    return pred, idx, nib | (sign * 8)

def ima_encode_fsb(pcm):
    """pcm: int16 1-D. Returns (data bytes, nblocks). Pads to a multiple of 64 repeating the last sample."""
    pcm = np.asarray(pcm, dtype=np.int32)
    n = len(pcm); nb = max(1, -(-n // 64))
    x = np.empty(nb * 64, dtype=np.int32); x[:n] = pcm; x[n:] = pcm[-1] if n else 0
    x = x.reshape(nb, 64)
    # index warm-up: run the previous block through the codec from idx 0
    idx = np.zeros(nb, dtype=np.int32)
    if nb > 1:
        pred = x[:-1, 0].copy(); i2 = np.zeros(nb - 1, dtype=np.int32)
        for j in range(1, 64):
            pred, i2, _ = _enc_step(x[:-1, j], pred, i2)
        idx[1:] = i2
    pred = x[:, 0].copy()
    out = np.zeros((nb, 36), dtype=np.uint8)
    p16 = pred.astype(np.int16).view(np.uint16)
    out[:, 0] = p16 & 255; out[:, 1] = p16 >> 8; out[:, 2] = idx
    nibs = np.zeros((nb, 64), dtype=np.uint8)
    for j in range(63):
        pred, idx, nb_ = _enc_step(x[:, j + 1], pred, idx)
        nibs[:, j] = nb_
    out[:, 4:] = nibs[:, 0::2] | (nibs[:, 1::2] << 4)
    return out.tobytes(), nb

def build_pc_wave(pcm, rate, name=b'converted.wav', pre2=0, pre3=100, hash16=None, nsamples=None):
    data, nb = ima_encode_fsb(pcm)
    data += b'\0' * (-len(data) % 32)  # PC FSB data size is padded to 32 bytes (verified on base game)
    length = nsamples if nsamples is not None else len(pcm)
    if hash16 is None:
        import hashlib; hash16 = hashlib.md5(name + data[:256]).digest()
    sh = struct.pack('<H', 0x50) + name[:30].ljust(30, b'\0')
    sh += struct.pack('<IIIIIIHHHHff', length, len(data), 0, max(length - 1, 0), 0x00400020, rate, 255, 128, 128, 1, 1.0, 10000.0)
    sh += b'\0' * 8
    assert len(sh) == 0x50
    fsb = b'FSB4' + struct.pack('<5I', 1, 0x50, len(data), 0x00040000, 0x22) + b'\0' * 8 + hash16 + sh + data
    return struct.pack('<IIII', rate, 0, pre2, pre3) + fsb

def xbox_wave_to_pc(payload, name=b'converted.wav'):
    """Returns (pc_payload, info). Rate/pre2/pre3 taken from the Xbox pre-header; length = decoded sample count."""
    rate, z, pre2, pre3 = struct.unpack('>IIII', payload[:16])
    a, sr, ch, err = xma_decode(payload[16:])
    if a is None: raise ValueError('xma decode failed: ' + err[:200])
    if ch != 1: a = a[:, 0:1]  # PC waves are all mono (stereo/XMA2 not seen in base game)
    pcm = a[:, 0]
    if sr != rate: rate = sr
    return build_pc_wave(pcm, rate, name, pre2, pre3), dict(rate=rate, channels=ch, samples=len(pcm))

def make_silence_wave(nsamples, rate=44100, name=b'silence.wav', pre3=100):
    """Minimal valid PC wave section payload: digital silence of nsamples (rounded up to 64-sample blocks in data)."""
    return build_pc_wave(np.zeros(max(nsamples, 64), dtype=np.int16), rate, name, 0, pre3, hash16=b'\0' * 16, nsamples=max(nsamples, 64))

def silence_for_xbox_wave(payload, name=b'silence.wav'):
    """Silence stub with the same rate/length as an Xbox wave (length from XMA decode; falls back to data size estimate)."""
    rate, z, pre2, pre3 = struct.unpack('>IIII', payload[:16])
    a, sr, ch, err = xma_decode(payload[16:])
    n = len(a) if a is not None else 44100
    return make_silence_wave(n, sr or rate, name, pre3)

if __name__ == '__main__':
    import json
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    d = open(sys.argv[1], 'rb').read()
    out, info = xbox_wave_to_pc(d)
    open(sys.argv[2], 'wb').write(out); print(info, len(out))
