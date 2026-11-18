"""Read-only: count CRLF and bare LF line ends and a leading BOM of text files (R2 doc edits, 2026-11-18).

Usage (from the repository root):
  ../bin/pyt -t 60 work/r2_1811/eol_check.py FILE [FILE ...]
"""
import sys


def main(argv):
    for p in argv:
        b = open(p, 'rb').read()
        crlf = b.count(b'\r\n')
        print('%s: bom %s, crlf %d, bare lf %d' % (p, b.startswith(b'\xef\xbb\xbf'), crlf, b.count(b'\n') - crlf))


if __name__ == '__main__':
    main(sys.argv[1:])
