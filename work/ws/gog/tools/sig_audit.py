#!/usr/bin/env python3
"""sig_audit.py - static audit of the fork plugins' byte checks against a tru.exe file (read-only).

  python -I tools/sig_audit.py PLUGIN_SRC_DIR EXE [--json OUT.json] [--show-fail]

Every plugin checks engine bytes before it patches (BytesAt(addr, bytes, len) / HexBytesAt(addr, "hex")); a failed
check turns that feature off at run time. This tool extracts those checks from the C++ sources and evaluates them
against the exe *file* (VA -> file offset, image base 0x400000), predicting which features will turn on.

Extraction (best effort, reported honestly):
  * HexBytesAt(<addr>, "<hex>" | kName) and BytesAt(<addr>, kArray, sizeof(kArray) | n)
  * table rows {<addr>, "<hex>"...} (checks looped over a table)
  <addr> may be a literal, a named constant (const/constexpr DWORD/uintptr_t ...), or a simple +/- expression of those.
Results per check: match / MISMATCH (bytes differ in the file) / runtime (address in .data beyond the file's raw
data or outside the image: only checkable in the running game) / unresolved (the tool could not evaluate the
arguments). Mismatches in .data can be legitimate (values written at run time).
"""
import argparse, json, os, re, struct, sys

NUM = r'0x[0-9a-fA-F]+|\d+'


def sections(d):
    pe = struct.unpack_from('<I', d, 0x3c)[0]
    n = struct.unpack_from('<H', d, pe + 6)[0]; opt = pe + 24
    base = struct.unpack_from('<I', d, opt + 28)[0]
    so = opt + struct.unpack_from('<H', d, pe + 20)[0]
    out = []
    for i in range(n):
        name, vs, va, rs, ra = struct.unpack_from('<8sIIII', d, so + 40 * i)
        out.append((name.rstrip(b'\0').decode(), base + va, vs, ra, rs))
    return base, out


def locate(secs, va, n):
    for name, sva, vs, ra, rs in secs:
        if sva <= va < sva + max(vs, rs):
            off = va - sva
            if off + n <= rs: return name, ra + off
            return name, None          # in the image, but not backed by file bytes (bss)
    return None, None


def strip_comments(src):
    src = re.sub(r'/\*.*?\*/', ' ', src, flags=re.S)
    return re.sub(r'//[^\n]*', '', src)


def join_strings(expr):
    parts = re.findall(r'"((?:[^"\\]|\\.)*)"', expr)
    return ''.join(parts) if parts else None


def constants(src):
    nums, strs, arrs = {}, {}, {}
    for m in re.finditer(r'\b(?:static\s+)?(?:const|constexpr)\s+(?:unsigned\s+)?(?:DWORD|uintptr_t|UINT_PTR|ULONG|int|unsigned|uint32_t|size_t)\s+(?:const\s+)?(k\w+)\s*=\s*([^;]+);', src):
        nums[m.group(1)] = m.group(2).strip()
    for m in re.finditer(r'\b(?:static\s+)?(?:const|constexpr)\s+char\s*(?:\*\s*(?:const\s+)?)?(k\w+)\s*(?:\[\s*\])?\s*=\s*((?:\s*"(?:[^"\\]|\\.)*")+)\s*;', src):
        strs[m.group(1)] = join_strings(m.group(2))
    for m in re.finditer(r'\b(?:static\s+)?(?:const|constexpr)\s+(?:BYTE|unsigned\s+char|uint8_t)\s+(k\w+)\s*\[\s*\w*\s*\]\s*=\s*\{([^}]*)\}', src):
        vals = re.findall(NUM, m.group(2))
        arrs[m.group(1)] = bytes(int(v, 0) & 0xff for v in vals)
    return nums, strs, arrs


def evaluate(expr, nums, depth=0):
    expr = expr.strip()
    expr = re.sub(r'static_cast<\w+>\((.*)\)', r'\1', expr)
    expr = re.sub(r'\((?:DWORD|uintptr_t|UINT_PTR)\)', '', expr)
    if depth > 8: return None
    toks = re.findall(r'0x[0-9a-fA-F]+|\d+|k\w+|[+\-()]|\S+', expr)
    out = []
    for t in toks:
        if re.fullmatch(r'0x[0-9a-fA-F]+|\d+', t): out.append(str(int(t, 0)))
        elif t in '+-()': out.append(t)
        elif t in nums:
            v = evaluate(nums[t], nums, depth + 1)
            if v is None: return None
            out.append(str(v))
        else: return None
    try: return int(eval(''.join(out), {'__builtins__': {}}, {}))
    except Exception: return None


def hexbytes(s):
    s = re.sub(r'\s+', '', s or '')
    if not s or len(s) % 2 or not re.fullmatch(r'[0-9a-fA-F]+', s): return None
    return bytes.fromhex(s)


def split_args(s):
    depth, cur, out = 0, '', []
    for ch in s:
        if ch in '([{': depth += 1
        if ch in ')]}':
            if depth == 0: break
            depth -= 1
        if ch == ',' and depth == 0: out.append(cur); cur = ''; continue
        cur += ch
    out.append(cur)
    return [a.strip() for a in out]


def extract(path):
    src = strip_comments(open(path, encoding='utf-8', errors='replace').read())
    nums, strs, arrs = constants(src)
    checks = []
    for m in re.finditer(r'\b(Hex)?BytesAt\(', src):
        line = src.count('\n', 0, m.start()) + 1
        args = split_args(src[m.end():m.end() + 600])
        if args and args[0].startswith(('DWORD ', 'const ')): continue        # the definition itself
        rec = {'line': line, 'call': src[m.start():m.end() + 80].split(')')[0][:100] + ')'}
        addr = evaluate(args[0], nums) if args else None
        data = None
        if m.group(1):
            a1 = args[1] if len(args) > 1 else ''
            data = hexbytes(join_strings(a1)) if '"' in a1 else hexbytes(strs.get(a1.strip()))
        elif len(args) >= 2:
            name = args[1].strip()
            if name in arrs:
                data = arrs[name]
                if len(args) > 2 and not args[2].startswith('sizeof'):
                    n = evaluate(args[2], nums)
                    if n is not None: data = data[:n]
        rec.update(addr=addr, data=data)
        checks.append(rec)
    # table rows {0x00xxxxxx, "hex" ...}
    for m in re.finditer(r'\{\s*(0x00[4-9a-fA-F][0-9a-fA-F]{5})\s*,\s*"([0-9a-fA-F ]{4,})"', src):
        checks.append({'line': src.count('\n', 0, m.start()) + 1, 'call': 'table row', 'addr': int(m.group(1), 16),
                       'data': hexbytes(m.group(2))})
    return checks


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src'); ap.add_argument('exe'); ap.add_argument('--json'); ap.add_argument('--show-fail', action='store_true')
    a = ap.parse_args()
    d = open(a.exe, 'rb').read()
    base, secs = sections(d)
    known_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'targets', 'sig_audit_explained.json')
    known = json.load(open(known_path, encoding='utf-8'))['entries'] if os.path.isfile(known_path) else {}
    report, total = {}, {'match': 0, 'explained': 0, 'MISMATCH': 0, 'runtime': 0, 'unresolved': 0}
    for plugin in sorted(os.listdir(a.src)):
        p = os.path.join(a.src, plugin, plugin + '.cpp')
        if not os.path.isfile(p): continue
        rows, cnt = [], {k: 0 for k in total}
        seen = set()
        for c in extract(p):
            if c['addr'] is None or c['data'] is None: st, sec = 'unresolved', None
            else:
                key = (c['addr'], c['data'])
                if key in seen: continue
                seen.add(key)
                sec, off = locate(secs, c['addr'], len(c['data']))
                if off is None: st = 'runtime'
                else: st = 'match' if d[off:off + len(c['data'])] == c['data'] else 'MISMATCH'
                if st == 'MISMATCH':
                    c['file_bytes'] = d[off:off + len(c['data'])].hex()
                    k = known.get('%s@%s' % (plugin, hex(c['addr'])))
                    if k and k['kind'] == 'alt-form': st, c['why'] = 'explained', k['reason']
                    elif k and k['kind'] == 'ret-site':
                        s2, o2 = locate(secs, c['addr'] - 6, len(c['data']))
                        if o2 is not None and d[o2:o2 + len(c['data'])] == c['data']: st, c['why'] = 'explained', k['reason'] + ' (ok at addr-6)'
            cnt[st] += 1; total[st] += 1
            rows.append({'line': c['line'], 'status': st, 'section': sec,
                         'addr': hex(c['addr']) if c['addr'] is not None else None,
                         'expected': c['data'].hex() if c['data'] else None, 'file_bytes': c.get('file_bytes'),
                         'why': c.get('why'), 'call': c['call']})
        report[plugin] = {'counts': cnt, 'checks': rows}
        print('%-16s match %4d  explained %2d  MISMATCH %3d  runtime %3d  unresolved %3d' % (plugin, cnt['match'], cnt['explained'], cnt['MISMATCH'], cnt['runtime'], cnt['unresolved']))
        if a.show_fail:
            for r in rows:
                if r['status'] == 'MISMATCH':
                    print('    L%-6d %s %-6s expected %s  file %s' % (r['line'], r['addr'], r['section'], r['expected'][:40], r['file_bytes'][:40]))
    print('%-16s match %4d  explained %2d  MISMATCH %3d  runtime %3d  unresolved %3d' % ('TOTAL', total['match'], total['explained'], total['MISMATCH'], total['runtime'], total['unresolved']))
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f: json.dump({'exe': os.path.abspath(a.exe), 'totals': total, 'plugins': report}, f, indent=1)
    return 1 if total['MISMATCH'] else 0


if __name__ == '__main__':
    sys.exit(main())
