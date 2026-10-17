"""Applica le classi fxdtp al DTP effetti DLC; per le parole senza regola tiene il valore attuale dell'overlay (B44).
uso: fx_apply.py NOME_CINE ID_DTP  -> stampa copertura e diff; ritorna bytes con conv_dtp()"""
import sys, os, struct, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fxdtp as F, cinepairs
sys.path.insert(0, cinepairs.T)
import drm_reloc as R
from archive import Archive
from names import crc
from convert_dlc import R as RR, PACKS
TM = {int(a): b for a, b in json.load(open(os.path.join(F.W, 'generic', 'idmap.json')))['5'].items()}

def conv_dtp(xd, xr, cur, tex_map, tab):
    """xd Xbox, cur = versione PC attuale (stessa dimensione). Ritorna (nuovi byte, statistiche, parole ignote)"""
    L = F.labels(xd, xr)
    if L is None: raise ValueError('struttura effetti non riconosciuta')
    lab, ptr, ids = L
    out = bytearray(cur); st = collections.Counter(); unk = []
    lists = {}
    for key in (('hdr', 8), ('rec', 276)):                   # regioni a liste {n, id texture}
        regs = collections.defaultdict(list)
        for o, k in lab.items():
            if k[0] == 'reg' and k[1] == key: regs[o - k[2]].append(o)
        for t, offs in regs.items():
            il = F.idlists(xd, t, max(offs) + 4)
            if il is None: raise ValueError('lista id non parse a %#x' % t)
            lists.update(dict(il))
    for o, k in lab.items():
        if k in (('rec', 272), ('rec', 336)) and o not in ptr and o not in ids: lists[o] = 'v' if k == ('rec', 272) else 'dtp'
    for o in range(0, len(xd) - 3, 4):
        if o in ptr or o in ids: st['ptr/id (reloc)'] += 1; continue
        if o in lists:
            v = struct.unpack_from('>I', xd, o)[0]
            if lists[o] == 'dtp' and v: raise ValueError('id DTP a %#x non gestito' % o)
            if lists[o] == 'v' and 0 < v < 0x10000:
                nv = tex_map(v)
                if nv is None: st['lista id ignoto (tenuto)'] += 1; continue      # id non in mappa: tieni l'overlay
            else: nv = v
            struct.pack_into('<I', out, o, nv); st['lista'] += 1; continue
        k = lab.get(o); c = F.decide(tab.get(k, {})) if k else None
        if c is None: st['ignota (tenuta B44)'] += 1; unk.append((o, k)); continue
        out[o:o + 4] = F.conv(xd[o:o + 4], c); st['regola ' + k[0]] += 1
    return bytes(out), st, unk

if __name__ == '__main__':
    nm, did = sys.argv[1], int(sys.argv[2])
    a = Archive(RR + PACKS[0], 'be')
    x = [s for s in cinepairs.secs(a.read(a.find(crc('xenon-w\\cinstream\\%s.drm' % nm))[0]), 'be') if s['id'] == did][0]
    p = [s for s in cinepairs.secs(open(os.path.join(F.W, 'baseline', 'B44', 'mods', 'cinstream', nm + '.drm'), 'rb').read(), 'le') if s['id'] == did][0]
    tab = F.learn(F.samples())
    # id texture: Xbox base -> PC base; id DLC -> come gia' rimappato dal convertitore (valore attuale nel PC)
    cur_lists = {}
    def tex_map(v): return TM.get(v, v)
    o, st, unk = conv_dtp(x['data'], x['reloc'], p['data'], tex_map, tab)
    print(dict(st))
    d = [k for k in range(0, len(o), 4) if o[k:k + 4] != p['data'][k:k + 4]]
    print('parole cambiate rispetto a B44', len(d))
    for k in d[:25]: print('   %5x %s -> %s  xbox %s  %s' % (k, p['data'][k:k + 4].hex(), o[k:k + 4].hex(), x['data'][k:k + 4].hex(), F.labels(x['data'], x['reloc'])[0].get(k)))
    print('ignote per etichetta', collections.Counter(str(k[:2]) for _, k in unk).most_common(10))
