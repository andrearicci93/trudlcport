"""B4 helper (2026-11-20): insert the text of a file into src/asi/TruMenu/TruMenu.cpp right after the one line that
starts with MARKER (CRLF kept, ASCII only). A copy of the file before the change goes to
work/b4_2011/TruMenu.cpp.before_<tag>.
Usage (from the repository root):
  ../bin/pyt work/b4_2011/insert_after.py TAG NEW_TEXT_FILE "MARKER"
Exit code: 0 = inserted, 1 = marker not unique / non-ASCII text (nothing changed), 2 = usage.
"""
import sys, os

CPP = os.path.join('src', 'asi', 'TruMenu', 'TruMenu.cpp')


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    tag, newf, marker = argv
    data = open(CPP, 'rb').read().decode('utf-8')
    lines = data.split('\r\n')
    hits = [i for i, l in enumerate(lines) if l.startswith(marker)]
    if len(hits) != 1:
        print('marker: %d hit(s) - nothing changed' % len(hits))
        return 1
    new = open(newf, 'rb').read().decode('utf-8').replace('\r\n', '\n').rstrip('\n').split('\n')
    if any(ord(ch) > 127 for l in new for ch in l):
        print('the new text holds non-ASCII characters - nothing changed')
        return 1
    backup = os.path.join('work', 'b4_2011', 'TruMenu.cpp.before_%s' % tag)
    open(backup, 'wb').write(data.encode('utf-8'))
    at = hits[0] + 1
    out = lines[:at] + new + lines[at:]
    open(CPP, 'wb').write('\r\n'.join(out).encode('utf-8'))
    print('inserted %d lines after line %d; backup %s' % (len(new), at, backup))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
