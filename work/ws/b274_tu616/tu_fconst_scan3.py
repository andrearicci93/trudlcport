"""Scansione v3: per ogni coppia di funzioni TU/base (TU_DIFF imm/mod, base unica, rapporto >= 0.85) confronta gli INSIEMI dei valori
float/double caricati come costanti (lis [+addi] + lfs/lfd): segnala i valori presenti solo nella TU o solo nella base. Robusto ai
riordini del compilatore (falsi positivi della v2). uso: python tu_fconst_scan3.py > tu_fconst3.tsv"""
import sys, collections, difflib, math
sys.argv = sys.argv[:1]
exec(open('tu_fconst_scan2.py', encoding='utf-8').read().split("rows = [l.rstrip")[0])
rows = [l.rstrip('\n').split('\t') for l in open(X + 'TU_DIFF.tsv')]
rows = [f for f in rows if len(f) >= 7 and f[3] in ('imm', 'mod') and f[6] not in ('-1', '')]
cnt = collections.Counter(f[6] for f in rows); n = 0
for f in rows:
    if cnt[f[6]] > 1: continue
    ta = int(f[0], 16); ba = 0x82000000 + int(f[6], 16)
    wt, lt = decode(T, ta, flen(ST, ta)); wb, lb = decode(B, ba, flen(SB, ba))
    sm = difflib.SequenceMatcher(None, [norm(x) for x in wt], [norm(x) for x in wb], autojunk=False)
    if sm.ratio() < 0.85: continue
    vt = collections.Counter((i[0], i[2]) for i in lt if i and normal(i[2]))
    vb = collections.Counter((i[0], i[2]) for i in lb if i and normal(i[2]))
    only_t = sorted(set(vt) - set(vb)); only_b = sorted(set(vb) - set(vt))
    if only_t or only_b:
        fm = lambda L: ' '.join('%s%.7g' % ('d:' if o == 50 else '', v) for o, v in L)
        print('%x\t%x\t%.3f\tsolo_base: %s\tsolo_TU: %s' % (ta, ba, sm.ratio(), fm(only_b), fm(only_t))); n += 1
print('TOTALE', n, file=sys.stderr)
