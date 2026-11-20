"""B4 2011: the byte-check tables kCcChecks + kCrChecks of src/asi/TruMenu/TruMenu.cpp must equal the rows of
work/b4_2011/precheck_02269.txt (same order, same bytes; the file is run against the PC exe by tools/pe_bytes_check.py).
Usage (from trudlcport): ../bin/pyt work/b4_2011/cc_checks_match.py
Exit code: 0 = equal, 1 = different (listed), 2 = a table / the file not found.
"""
import os, re, sys

CPP = os.path.join('src', 'asi', 'TruMenu', 'TruMenu.cpp')
PRE = os.path.join('work', 'b4_2011', 'precheck_02269.txt')


def table(src, name):
    at = src.find('const ChCheck %s[] = {' % name)
    if at < 0:
        return None
    body = src[at:src.find('\n};', at)]
    return [(int(a, 16), h.replace(' ', '').lower()) for a, h in re.findall(r'\{0x([0-9a-fA-F]+), "([0-9a-fA-F ]+)"\}', body)]


def main():
    src = open(CPP, encoding='utf-8').read()
    cc, cr = table(src, 'kCcChecks'), table(src, 'kCrChecks')
    if cc is None or cr is None or not os.path.exists(PRE):
        print('kCcChecks / kCrChecks / precheck file missing')
        return 2
    rows = []
    for line in open(PRE, encoding='utf-8'):
        line = line.split('#')[0].strip()
        if line:
            w = line.split()
            rows.append((int(w[0], 16), ''.join(w[1:]).lower()))
    code = cc + cr
    bad = 0
    for i in range(max(len(code), len(rows))):
        a = code[i] if i < len(code) else None
        b = rows[i] if i < len(rows) else None
        if a != b:
            bad += 1
            print('row %d: code %s / file %s' % (i + 1, a, b))
    print('%d code rows (kCcChecks %d + kCrChecks %d), %d file rows, %d difference(s)' % (len(code), len(cc), len(cr),
                                                                                       len(rows), bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
