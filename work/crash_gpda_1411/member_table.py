"""Read-only: the 20-byte member / arg / local entries of one script (kind, index, tag, userType, instance offset,
name, init pointer, first init words) in a g_pda ('pc:g_pda.drm' = PC archive copy).
Usage (repo root): ../bin/pyt work/crash_gpda_1411/member_table.py SPEC SCRIPT_ID [members|args|locals]"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from sec_hex import load
import drm_reloc as R
import script_member_pairs as MP


def main(argv):
    _, S = load(argv[0]); sid = int(argv[1]); kinds = argv[2:] or ['members']
    d, rl = [(x[2], x[3]) for x in S if x[0] == 8 and x[1] == sid][0]
    it = dict(R.parse(rl, 'le').internal)
    _, E = MP.entries(d, rl, 'le')
    for k in kinds:
        for q in E[k]:
            n1 = it.get(q['init']) if q['init'] is not None else None
            words = ' '.join(d[n1 + 4 * j:n1 + 4 * j + 4].hex() + ('*' if (n1 + 4 * j) in it else '') for j in range(8)) if n1 is not None and n1 + 32 <= len(d) else '-'
            print('%s #%d tag %d ut %d off 0x%x name 0x%x entry +0x%x init %s | %s' % (
                k, q['k'], q['tag'], q['ut'], q['off'], q['name'], q['a'], '+0x%x' % q['init'] if q['init'] is not None else '-', words))


if __name__ == '__main__':
    main(sys.argv[1:])
