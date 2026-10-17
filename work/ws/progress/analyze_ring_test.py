"""analyze_ring_test.py <RunId>: unisce ringtest.log (finestre HOLD) con la sonda lists (sotto-lista di ogni anello) e stampa la tabella distanza/azimut -> indice di sotto-lista."""
import sys, re, os, collections, datetime
run = sys.argv[1]; d = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'runs', run)
log = open(os.path.join(d, 'ringtest.log')).read().splitlines()
import glob
tsvp = sorted(glob.glob(os.path.join(d, 'a*', 'probe_ext_ext_lists.tsv')), key=os.path.getmtime)[-1]
T = open(tsvp).read().splitlines()
m = re.search(r'started=(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)', T[0]); t0 = datetime.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')
snaps = []; cur = None
for l in T:
    if l.startswith('# SNAPSHOT'): cur = [float(re.search(r't=([\d.]+)', l).group(1)), {}]; snaps.append(cur)
    elif cur is not None and not l.startswith('#') and not l.startswith('list\t'):
        f = l.split('\t')
        if len(f) >= 20 and f[0] == '1' and f[5] not in ('-', ''): cur[1][f[19] if f[19] != '-1' else f[11]] = f[5]
def ts(s):
    h, mi, se = s.split(':'); sec = float(se)
    return (int(h) * 3600 + int(mi) * 60 + sec)
t0s = t0.hour * 3600 + t0.minute * 60 + t0.second
print('RECORD letti dal gioco:'); [print('  ', l[13:]) for l in log if ' RECORD ' in l]
print([l for l in log if ' LARA ' in l][:1])
win = []; cur = None
for l in log:
    mm = re.match(r'(\S+) HOLD_START az=(\S+) d=(\S+) pos=(\S+)', l)
    if mm: cur = [ts(mm.group(1)) - t0s, None, float(mm.group(2)), float(mm.group(3))]
    mm = re.match(r'(\S+) HOLD_END', l)
    if mm and cur: cur[1] = ts(mm.group(1)) - t0s; win.append(cur); cur = None
rings = ['9753', '9754', '9755', '9758', '9711']
print('\nsotto-lista per anello (moda nell\'ultima meta\' della finestra; 6 = scartato):')
print('%5s %6s | %s' % ('az', 'dist', ' '.join('%5s' % r for r in rings)))
for a, b, az, dd in win:
    sel = [s for t, s in snaps if a + (b - a) * 0.4 <= t <= b]
    row = []
    for r in rings:
        c = collections.Counter(s.get(r, '-') for s in sel); row.append(c.most_common(1)[0][0] if c else '?')
    print('%5.0f %6.0f | %s' % (az, dd, ' '.join('%5s' % x for x in row)))
