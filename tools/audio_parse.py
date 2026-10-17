"""Parsers for TR8 Wave (section type 6) payloads.
PC : 16B pre-header (LE) + FSB4 file (1 sample, FMOD IMA ADPCM) [+ trailing?]
XB : 16B pre-header (BE) + RIFF/WAVE with XMA1 (0x165) fmt chunk
"""
import struct
def parse_pc(d):
    freq, a, b, c = struct.unpack('<IIII', d[:16])
    f = d[16:]
    assert f[:4] == b'FSB4'
    n, shsz, dsz, ver, mode = struct.unpack('<5I', f[4:24])
    h = f[0x30:0x30+shsz]
    sz, = struct.unpack('<H', h[:2]); name = h[2:32].split(b'\0')[0]
    (length, comp, ls, le, smode, deffreq, vol, pan, pri, nch, mind, maxd) = struct.unpack('<IIIIIIHHHHff', h[32:72])
    return dict(pre=(freq, a, b, c), n=n, shsz=shsz, dsz=dsz, ver=ver, mode=mode, hash=f[0x20:0x30], name=name, length=length, comp=comp, ls=ls, le=le, smode=smode, deffreq=deffreq, vol=vol, pan=pan, pri=pri, nch=nch, mind=mind, maxd=maxd, hdr_rest=h[72:], data=f[0x30+shsz:0x30+shsz+dsz], tail=f[0x30+shsz+dsz:])
def parse_xb(d):
    pre = struct.unpack('>IIII', d[:16])
    r = d[16:]
    assert r[:4] == b'RIFF'
    return dict(pre=pre, riff=r)

import subprocess
FFMPEG = '/opt/homebrew/bin/ffmpeg'
def xma_decode(riff, rate=None):
    """Decode an Xbox RIFF/XMA blob via ffmpeg -> (int16 numpy array [n,ch], rate, ch)."""
    import numpy as np
    pr = subprocess.run([FFMPEG, '-v', 'error', '-i', 'pipe:0', '-f', 'wav', 'pipe:1'], input=riff, capture_output=True)
    w = pr.stdout
    if len(w) < 44: return None, 0, 0, pr.stderr.decode()
    ch, = struct.unpack('<H', w[22:24]); sr, = struct.unpack('<I', w[24:28])
    # find data chunk
    p = 12
    while p < len(w):
        cid = w[p:p+4]; sz, = struct.unpack('<I', w[p+4:p+8])
        if cid == b'data': a = np.frombuffer(w[p+8:p+8+sz] if sz != 0xffffffff else w[p+8:], dtype='<i2'); break
        p += 8 + sz
    return a.reshape(-1, ch), sr, ch, pr.stderr.decode()

import numpy as np
IMA_STEP = [7,8,9,10,11,12,13,14,16,17,19,21,23,25,28,31,34,37,41,45,50,55,60,66,73,80,88,97,107,118,130,143,157,173,190,209,230,253,279,307,337,371,408,449,494,544,598,658,724,796,876,963,1060,1166,1282,1411,1552,1707,1878,2066,2272,2499,2749,3024,3327,3660,4026,4428,4871,5358,5894,6484,7132,7845,8630,9493,10442,11487,12635,13899,15289,16818,18500,20350,22385,24623,27086,29794,32767]
IMA_IDX = [-1,-1,-1,-1,2,4,6,8]
def ima_decode_fsb(data, nblk_samples=64):
    """Decode mono FMOD/XBOX-style IMA: 36B blocks, hdr s16 pred + u8 index + pad, 8 dwords of nibbles. 64 samples/block: [hdr, 63 nibbles]."""
    nb = len(data) // 36
    b = np.frombuffer(data[:nb*36], dtype=np.uint8).reshape(nb, 36)
    pred = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8)); pred = np.where(pred >= 32768, pred - 65536, pred)
    idx = np.clip(b[:, 2].astype(np.int32), 0, 88)
    nib = np.empty((nb, 64), dtype=np.int32)
    nib[:, 0::2] = b[:, 4:] & 15; nib[:, 1::2] = b[:, 4:] >> 4
    out = np.empty((nb, 64), dtype=np.int32)
    out[:, 0] = pred
    step_t = np.array(IMA_STEP); idx_t = np.array(IMA_IDX)
    for i in range(63):
        n = nib[:, i]
        step = step_t[idx]
        diff = step >> 3
        diff = diff + np.where(n & 1, step >> 2, 0) + np.where(n & 2, step >> 1, 0) + np.where(n & 4, step, 0)
        pred = np.clip(pred + np.where(n & 8, -diff, diff), -32768, 32767)
        idx = np.clip(idx + idx_t[n & 7], 0, 88)
        out[:, i + 1] = pred
    return out.reshape(-1).astype(np.int16)
