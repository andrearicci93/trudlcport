"""Convert all DLC terrain sections (type 12 without 'Mesh' magic) and check validity, Y-hash coverage and
vertex element types.  usage: tools/venv/bin/python -I tools/terrain_dlc.py -> work/render/terrain_dlc.txt"""
import sys, os, pickle, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import terrain_convert as TC, terrain_validate as TV
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')
if __name__ == '__main__':
    dlc = pickle.load(open(W + '/render/dlc_render.pkl', 'rb'))
    ym = TC.yhash_map()
    st = collections.Counter(); seen = set(); bad = []; unk = collections.Counter(); per_drm = collections.defaultdict(list)
    for path, i, h, secs in dlc:
        for s in secs or []:
            if s['type'] != 12 or not TC.is_terrain(s['data']): continue
            name = os.path.basename(os.path.dirname(path)) + ':%08x' % h
            per_drm[name].append(s['id'])
            if s['id'] in seen: continue
            seen.add(s['id'])
            info = {}
            try:
                pd, pr = TC.convert(s['data'], s['reloc'], None, info)
            except Exception as e:
                st['error'] += 1; bad.append((name, s['id'], repr(e)[:100])); continue
            st['n'] += 1
            ok = TV.valid(pd, '<'); st['valid'] += ok
            if not ok: bad.append((name, s['id'], 'invalid'))
            T = TC.parse(s['data'])
            for k in range(T['nY']):
                r = T['H'] + T['offY'] + 32 * k
                hx = bytes(s['data'][r + 8:r + 12]); st['Y records'] += 1
                if hx in ym: st['Y hash known'] += 1
                else: unk[hx] += 1
            for vf in T['vfs']:
                for sem, eo, typ, _ in vf['elems']:
                    st['vtype %x' % typ] += 1
            for k, v in info.items(): st[k] += v
            st['tris'] += T['nIdx'] // 3
    lines = ['DLC terrain sections unique: %d' % len(seen)] + ['  %-24s %d' % kv for kv in sorted(st.items())]
    lines.append('unknown Y hashes: %d distinct %s' % (len(unk), [(k.hex(), v) for k, v in unk.most_common(20)]))
    lines += ['problems:'] + ['  ' + repr(b) for b in bad]
    txt = '\n'.join(lines); print(txt); open(W + '/render/terrain_dlc.txt', 'w').write(txt + '\n')
