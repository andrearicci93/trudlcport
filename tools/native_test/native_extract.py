#!/usr/bin/env python3
"""native_extract v3 (B269) - step 1 of the native Direct3D 9 test of the TRU DLC port. Standard library only. Writes nothing in the game folder.

Reads the installed port (<game>/mods/**/*.drm) and writes, next to this script:
  shaders/<new|pc>_<ps|vs>_<lib>_<slot>_<md5_8>.bin   every unique shader blob (new_ = made by the port, pc_ = identical to a PC-game shader)
  shaders_index.tsv      one row per blob: lib id, slot, DRM files it comes from, size, md5, instruction count, static findings,
                         and the disassembly of the first suspicious instruction (native_test.ps1 joins this to the HRESULTs)
  textures_installed.json  every texture format/size/mip/cube combination used by the installed DRMs (for CreateTexture tests)
  extract_summary.txt    counts + static findings, readable without Windows

Static findings (the D3D9 runtime only returns an HRESULT, never the failing line, so the line comes from here):
  ABS_CONST   source modifier abs/-abs on a constant register (cmp r0, -|c221|, ...): rejected by the native D3D9 (found 20/10)
  SINCOS_SAME sincos with destination == source register: rejected by the native D3D9
  LONG        more than 512 instruction slots (accepted only if the GPU reports PS30/VS30 slots >= that)
  NEW_FORM    an opcode/register/modifier combination never used by the 5000+ shaders of the PC game (pc_features.txt)
  ERR         a rule of the ps_3_0/vs_3_0 spec broken (sm3check.py)
Without --game (no game or no port installed) it does nothing and the test runs the synthetic probes only.
Usage: python native_extract.py --game "C:/Program Files (x86)/Steam/steamapps/common/Tomb Raider Underworld"
"""
import argparse, collections, hashlib, json, os, struct, sys, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sm3check as S   # noqa: E402

LIMIT = 512


def cdrm_decode(d):
    if d[:4] not in (b'CDRM', b'MRDC'): return d
    n, = struct.unpack('<I', d[8:12])
    ents = [struct.unpack('<II', d[16 + 8 * i:24 + 8 * i]) for i in range(n)]
    pos = (16 + 8 * n + 15) & ~15; out = bytearray()
    for u, c in ents:
        blk = d[pos:pos + c]
        out += zlib.decompress(blk) if (u & 0xff) == 2 else blk
        pos = (pos + c + 15) & ~15
    return bytes(out)


def sections(raw):
    ver, namesz, padsz, u0, u1, n = struct.unpack('<iiiiii', raw[:24])
    secs, p = [], 24
    for _ in range(n):
        size, typ, pad, vid, packed, sid, spec = struct.unpack('<iBBHIII', raw[p:p + 20]); p += 20
        secs.append((size, typ, packed >> 8, sid))
    p += namesz + padsz
    for size, typ, nreloc, sid in secs:
        p += nreloc
        yield typ, sid, raw[p:p + size]
        p += size


def lib_blobs(d):
    """ShaderLib section: u8 kind, 3 pad, u32 tableBytes, u32 dataSize, u32 slot[]; entry @4+off: u32 junk, u32 size, u64 hash, bytecode."""
    tb, = struct.unpack_from('<I', d, 4)
    for slot, off in enumerate(struct.unpack_from('<%dI' % (tb // 4), d, 12)):
        if off == 0xffffffff: continue
        size, = struct.unpack_from('<I', d, 4 + off + 4)
        code = d[4 + off + 16:4 + off + 8 + size]
        for i in range(0, len(code) - 3, 4):   # cut at the END token
            if code[i:i + 4] == b'\xff\xff\x00\x00': code = code[:i + 4]; break
        yield slot, code


# ------------------------------------------------------------------ disassembly of one instruction (enough to show the culprit)
def _reg(o):
    n = S.RTN.get(o.rt, '?%d' % o.rt)
    s = '%s%d' % (n, o.num)
    if o.rel and o.relop is not None: s = '%s[%s%d]' % (n, S.RTN.get(o.relop.rt, '?'), o.relop.num) if o.num == 0 else '%s[%s%d + %d]' % (n, S.RTN.get(o.relop.rt, '?'), o.relop.num, o.num)
    return s


def _swz(o):
    c = ''.join('xyzw'[o.swc(i)] for i in range(4))
    if c == 'xyzw': return ''
    if len(set(c)) == 1: return '.' + c[0]
    return '.' + c


def _src(o):
    r = _reg(o) + _swz(o)
    m = o.smod
    return {0: r, 1: '-' + r, 11: '|%s|' % r, 12: '-|%s|' % r, 13: '!' + r}.get(m, '%s(%s)' % (S.SMOD.get(m, m), r))


def _dst(o):
    m = ''.join(c for i, c in enumerate('xyzw') if o.wm >> i & 1)
    mods = ('_sat' if o.mod & 1 else '') + ('_pp' if o.mod & 2 else '') + ('_centroid' if o.mod & 4 else '')
    return mods, _reg(o) + ('' if m == 'xyzw' else '.' + m)


def ins_text(x):
    if x.op in ('def', 'defi', 'defb'):
        v = ['%g' % struct.unpack('<f', struct.pack('<I', w))[0] for w in x.imm] if x.op == 'def' else [str(w) for w in x.imm]
        return '%s %s, %s' % (x.op, _reg(x.dst), ', '.join(v))
    if x.op == 'dcl':
        return 'dcl %s' % _reg(x.dst)
    mods, d = _dst(x.dst) if x.dst is not None else ('', '')
    op = x.op + (('_' + S.CMP.get(x.ctrl, str(x.ctrl))) if x.ctrl and x.op in ('ifc', 'breakc', 'setp') else '') + mods
    args = ([d] if d else []) + [_src(s) for s in x.src]
    return '%s%s %s' % ('(p) ' if x.pred else '', op, ', '.join(args))


def extra_feats(items):
    """combinations used for the 'never seen in the PC game' check: (op, register type, source modifier) and sincos dst==src."""
    F = set()
    for x in items:
        for s in x.src:
            F.add('src:%s:%s:%s' % (x.op, S.RTN.get(s.rt, s.rt), S.SMOD.get(s.smod, s.smod) or '-'))
        if x.dst is not None and x.op not in ('dcl', 'def', 'defi', 'defb'):
            F.add('dst:%s:%s:%x' % (x.op, S.RTN.get(x.dst.rt, x.dst.rt), x.dst.mod))
        if x.op == 'sincos' and x.dst is not None and any(s.rt == x.dst.rt and s.num == x.dst.num for s in x.src):
            F.add('sincos_dst_eq_src')
    return F


def analyze(code, pc_feats):
    R = S.analyze(code)
    kind, ver, items, errs, info = S.decode(code)
    findings, first = [], ''
    for x in items:
        hit = None
        for s in x.src:
            if s.rt == 2 and s.smod in (11, 12): hit = 'ABS_CONST'
        if x.op == 'sincos' and x.dst is not None and any(s.rt == x.dst.rt and s.num == x.dst.num for s in x.src): hit = 'SINCOS_SAME'
        if hit:
            findings.append(hit)
            if not first: first = 'instr %d: %s' % (x.idx, ins_text(x))
    nins = sum(1 for x in items if x.op not in ('dcl', 'def', 'defi', 'defb'))
    if nins > LIMIT: findings.append('LONG')
    ef = extra_feats(items)                      # narrow forms (op, register type, modifier): the broad sm3check features are too noisy
    new = sorted(ef - pc_feats) if pc_feats else []
    if new:
        findings.append('NEW_FORM')
        if not first:
            for x in items:
                if extra_feats([x]) - pc_feats: first = 'instr %d: %s' % (x.idx, ins_text(x)); break
    if R['errs']:
        findings.append('ERR')
        if not first: first = 'spec: ' + R['errs'][0]
    return dict(kind=kind or '?', ver='%d.%d' % ver, nins=nins, findings=sorted(set(findings)), first=first, new=new[:8],
                errs=R['errs'][:3], feats=ef)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', help='game folder (the one with tru.exe and mods)')
    ap.add_argument('--mods', help='or directly a mods folder')
    ap.add_argument('--out', default=HERE)
    a = ap.parse_args()
    mods = a.mods or (os.path.join(a.game, 'mods') if a.game else None)
    if not mods or not os.path.isdir(mods):
        print('No installed port found (%s): only the synthetic probes will be tested.' % mods); return 2
    pcm = set(); pcf = set()
    p = os.path.join(HERE, 'pc_shader_md5.txt')
    if os.path.isfile(p): pcm = set(open(p).read().split())
    p = os.path.join(HERE, 'pc_features.txt')
    if os.path.isfile(p): pcf = set(open(p).read().splitlines())
    sd = os.path.join(a.out, 'shaders'); os.makedirs(sd, exist_ok=True)
    for f in os.listdir(sd):
        if f.endswith('.bin'): os.remove(os.path.join(sd, f))
    blobs = {}; tex = collections.Counter(); texex = {}; ndrm = 0; bad = []
    for dp, dn, fn in os.walk(mods):
        for f in sorted(fn):
            if not f.lower().endswith('.drm'): continue
            ndrm += 1; rel = os.path.relpath(os.path.join(dp, f), mods).replace('\\', '/')
            try:
                raw = cdrm_decode(open(os.path.join(dp, f), 'rb').read())
                for typ, sid, data in sections(raw):
                    if typ == 9:
                        for slot, code in lib_blobs(data):
                            md = hashlib.md5(code).hexdigest()
                            b = blobs.setdefault(md, dict(code=code, refs=[], libs=set()))
                            b['refs'].append(rel); b['libs'].add((sid, slot))
                    elif typ == 5 and data[:4] == b'PCD9':
                        fmt, size, pal, w, h, b14, mips, flags = struct.unpack_from('<IIIHHBBH', data, 4)
                        k = ('cube' if flags & 0x8000 else '2d', fmt, w, h, 1, mips + 1)
                        tex[k] += 1; texex.setdefault(k, '%s/%d' % (rel, sid))
            except Exception as e:
                bad.append('%s: %r' % (rel, e))
    rows = []; forms = collections.Counter(); cnt = collections.Counter(); byflag = collections.defaultdict(list)
    for md, b in blobs.items():
        code = b['code']; kind = 'vs' if code[2:4] == b'\xfe\xff' else 'ps'
        cls = 'pc' if md in pcm else 'new'
        lib, slot = sorted(b['libs'])[0]
        name = '%s_%s_%d_%d_%s.bin' % (cls, kind, lib, slot, md[:8])
        open(os.path.join(sd, name), 'wb').write(code)
        r = analyze(code, pcf)
        drms = sorted(set(b['refs']))
        rows.append([name, kind, cls, str(lib), str(slot), str(len(code)), md, r['ver'], str(r['nins']), ','.join(r['findings']) or '-',
                     r['first'] or '-', ' '.join(r['new']) or '-', '%d:%s' % (len(drms), ' '.join(drms[:6]))])
        cnt[(cls, kind)] += 1
        for fl in r['findings']: byflag[fl].append((cls, lib, slot, name, r['first'], drms[:3]))
        for f_ in r['new']: forms[f_] += 1
    rows.sort()
    hdr = ['file', 'kind', 'class', 'lib', 'slot', 'size', 'md5', 'ver', 'ninstr', 'findings', 'first_suspicious_instruction', 'new_forms', 'drms']
    with open(os.path.join(a.out, 'shaders_index.tsv'), 'w', encoding='utf-8') as fo:
        fo.write('\t'.join(hdr) + '\n')
        for r in rows: fo.write('\t'.join(c.replace('\t', ' ') for c in r) + '\n')
    tj = [dict(kind=k[0], format=k[1], width=k[2], height=k[3], depth=1, levels=k[5], count=n, example=texex[k], source='installed')
          for k, n in sorted(tex.items(), key=lambda kv: (kv[0][0], kv[0][1], -kv[0][2] * kv[0][3], kv[0][5]))]
    json.dump(tj, open(os.path.join(a.out, 'textures_installed.json'), 'w'), indent=1)
    S_ = ['native_extract v3 | mods=%s' % mods,
          'DRM read: %d (unreadable: %d)   unique shaders: %d   new PS %d  new VS %d  PC PS %d  PC VS %d   texture combos: %d' % (
              ndrm, len(bad), len(blobs), cnt[('new', 'ps')], cnt[('new', 'vs')], cnt[('pc', 'ps')], cnt[('pc', 'vs')], len(tj)),
          'PC reference tables: %s' % ('yes (%d md5, %d forms)' % (len(pcm), len(pcf)) if pcm else 'MISSING (all shaders count as new)'),
          'Static findings (the D3D9 runtime will very likely reject ABS_CONST and SINCOS_SAME):']
    for fl in ('ABS_CONST', 'SINCOS_SAME', 'LONG', 'NEW_FORM', 'ERR'):
        L = byflag.get(fl, [])
        S_.append('  %-12s %4d blobs (%d in new shaders)' % (fl, len(L), sum(1 for x in L if x[0] == 'new')))
        for x in L[:5]: S_.append('      lib %d slot %d %s | %s | from %s' % (x[1], x[2], x[3], x[4] or '-', ', '.join(x[5])))
    S_.append('NEW_FORM detail (form: blobs). Only ABS_CONST (src:cmp/add/mad:c:abs*) and SINCOS_SAME were rejected on the AMD test of 20/10;')
    S_.append('  rsq/rcp with |r| and the other forms below passed there: they are listed only to compare with a new rejection.')
    for f_, n_ in forms.most_common(): S_.append('  %-28s %5d' % (f_, n_))
    for b in bad[:10]: S_.append('  unreadable: ' + b)
    open(os.path.join(a.out, 'extract_summary.txt'), 'w', encoding='utf-8').write('\n'.join(S_) + '\n')
    print('\n'.join(S_))
    return 0


if __name__ == '__main__':
    sys.exit(main())
