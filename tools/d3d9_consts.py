"""Minimal D3D9 SM3 token-stream reader: float constant registers read by a shader blob (mat2 workstream).
used_consts(blob) -> (set of absolute float-const register indices read as plain sources, [(base, rel)] relative-addressed bases)"""
import struct
NODST = {40, 41, 42, 43, 44, 45, 27, 29, 14, 15, 26, 25, 30, 28, 0, 96}
def _rt(r): return ((r >> 28) & 7) | ((r >> 8) & 0x18)
def used_consts(blob):
    n = len(blob) // 4
    t = struct.unpack_from('<%dI' % n, blob, 0)
    used = set(); rel = []; i = 1
    while i < n:
        tok = t[i]; op = tok & 0xFFFF
        if op == 0xFFFE: i += 1 + ((tok >> 16) & 0x7FFF); continue
        if op == 0xFFFF: break
        ln = (tok >> 24) & 0xF
        params = t[i + 1:i + 1 + ln]
        if op in (31, 81, 82, 83): i += 1 + ln; continue          # dcl / def*
        k = 0; first = op not in NODST
        idx = 0
        while k < len(params):
            r = params[k]; k += 1
            isdst = first and idx == 0
            hasrel = (r >> 13) & 1
            if hasrel and k < len(params): k += 1                 # relative-address token follows
            if not isdst and _rt(r) in (2, 11, 12, 13):
                reg = r & 0x7FF
                if _rt(r) == 11: reg += 2048
                if hasrel: rel.append(reg)
                else: used.add(reg)
            idx += 1
        i += 1 + ln
    return used, rel
