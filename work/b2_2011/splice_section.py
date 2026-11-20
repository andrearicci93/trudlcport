"""B2 helper (2026-11-20): replace one marked section of src/asi/TruMenu/TruMenu.cpp by the text of a file (CRLF kept).
The section runs from the line that starts with BEGIN up to (not including) the line that starts with END; both
markers must occur exactly once. A copy of the file before the change goes to work/b2_2011/<name>.before_<tag>.
Usage (from the repository root):
  ../bin/pyt work/b2_2011/splice_section.py TAG NEW_TEXT_FILE "BEGIN" "END"
"""
import sys, os

CPP = os.path.join('src', 'asi', 'TruMenu', 'TruMenu.cpp')


def main(argv):
    if len(argv) != 4:
        print(__doc__)
        return 2
    tag, newf, begin, end = argv
    data = open(CPP, 'rb').read().decode('utf-8')
    lines = data.split('\r\n')
    b = [i for i, l in enumerate(lines) if l.startswith(begin)]
    e = [i for i, l in enumerate(lines) if l.startswith(end)]
    if len(b) != 1 or len(e) != 1 or e[0] <= b[0]:
        print('markers: begin %d hit(s), end %d hit(s) - nothing changed' % (len(b), len(e)))
        return 1
    new = open(newf, 'rb').read().decode('utf-8').replace('\r\n', '\n').rstrip('\n').split('\n')
    if any(ord(ch) > 127 for l in new for ch in l):
        print('the new text holds non-ASCII characters - nothing changed')
        return 1
    backup = os.path.join('work', 'b2_2011', 'TruMenu.cpp.before_%s' % tag)
    open(backup, 'wb').write(data.encode('utf-8'))
    out = lines[:b[0]] + new + lines[e[0]:]
    open(CPP, 'wb').write('\r\n'.join(out).encode('utf-8'))
    print('replaced lines %d .. %d (%d lines) by %d lines; backup %s' % (b[0] + 1, e[0], e[0] - b[0], len(new), backup))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
