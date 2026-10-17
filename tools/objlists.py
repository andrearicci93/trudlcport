"""objectlist.txt / unitlist.txt / objlist.dat: parse, write, merge (PC base + Xbox DLC objects/units).

Formats (verified by byte-exact round trip on PC + Xbox base, TU and DLC versions):
  objectlist.txt : "N\\r\\n" then "id,name\\r\\n" * N   (ids 1..N, must end with a line break)
  unitlist.txt   : "N\\r\\n" then "path\\r\\n" * N      (alphabetical)
  objlist.dat    : u32 N ; char name[N][132] (record 0 is empty) ;
                   then for each record 1..N-1: u16 count, u16 objectId[count] (sorted ascending)
                   platform endian (LE on PC, BE on Xbox).  Lists the objects each unit needs.
Object ids: PC base and Xbox base have the same 821 names but different ids (35 equal).  Xbox TU/DLC
lists keep Xbox ids 1..821 and append 822..1045 (224 DLC objects: 204 in pack10 + 20 more in pack11).
Merged PC list = PC ids 1..821 unchanged + Xbox DLC ids 822..1045 kept as-is (PC max is 821, so no clash).
remap(xbox_id) = pc_id_by_name for base objects, identity for >= 822.

Usage: python3 -I tools/objlists.py [outdir]   -> writes merged tr8/pc-w/{objectlist.txt,unitlist.txt,objlist.dat}
"""
import struct, os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
LISTS = os.path.join(HERE, '..', 'work', 'generic', 'lists')

def read_objectlist(b):
    L = b.decode('latin1').split('\r\n')
    n = int(L[0]); d = {}
    for l in L[1:]:
        if l:
            a, s = l.split(',', 1); d[int(a)] = s
    assert len(d) == n
    return d

def write_objectlist(d):
    return (('%d\r\n' % len(d)) + ''.join('%d,%s\r\n' % (k, d[k]) for k in sorted(d))).encode('latin1')

def read_unitlist(b):
    L = [l for l in b.decode('latin1').split('\r\n') if l]
    assert int(L[0]) == len(L) - 1
    return L[1:]

def write_unitlist(u):
    return (('%d\r\n' % len(u)) + ''.join(x + '\r\n' for x in u)).encode('latin1')

def read_objlist(b, endian):
    e = '>' if endian == 'be' else '<'
    n, = struct.unpack_from(e + 'I', b, 0)
    raw = [b[4 + 132 * i:4 + 132 * (i + 1)] for i in range(n)]
    names = [r.split(b'\0')[0].decode('latin1') for r in raw]
    assert all(r == names[i].encode('latin1').ljust(132, b'\0') for i, r in enumerate(raw)), 'garbage after names'
    p = 4 + 132 * n; lists = []
    for i in range(n - 1):
        c, = struct.unpack_from(e + 'H', b, p); p += 2
        lists.append(list(struct.unpack_from(e + '%dH' % c, b, p))); p += 2 * c
    assert p == len(b)
    return [(names[i + 1], lists[i]) for i in range(n - 1)], names[0]

def write_objlist(recs, endian, first=''):
    e = '>' if endian == 'be' else '<'
    out = bytearray(struct.pack(e + 'I', len(recs) + 1))
    out += first.encode('latin1').ljust(132, b'\0')
    for nm, _ in recs: out += nm.encode('latin1').ljust(132, b'\0')
    for _, l in recs: out += struct.pack(e + 'H', len(l)) + struct.pack(e + '%dH' % len(l), *l)
    return bytes(out)

def load(prefix):
    f = lambda n: open(os.path.join(LISTS, prefix + '_' + n), 'rb').read()
    return f('objectlist.txt'), f('unitlist.txt'), f('objlist.dat')

def roundtrip_test():
    ok = True
    for prefix, e in (('pc', 'le'), ('xbox', 'be'), ('xboxtu', 'be'), ('dlc_pack10', 'be'), ('dlc_pack11', 'be'), ('dlc_pack1', 'be')):
        o, u, d = load(prefix)
        r = [write_objectlist(read_objectlist(o)) == o, write_unitlist(read_unitlist(u)) == u,
             write_objlist(*read_objlist(d, e)[::-1][1:] or [], e) if False else None]
        recs, first = read_objlist(d, e)
        r[2] = write_objlist(recs, e, first) == d
        print('roundtrip', prefix, r); ok &= all(r)
    return ok

def build_remap(pc_ol, x_ol):
    byname = {v: k for k, v in pc_ol.items()}
    base_max = max(pc_ol)
    m = {}
    for xid, nm in x_ol.items():
        if nm in byname: m[xid] = byname[nm]
        else:
            assert xid > base_max, (xid, nm)      # new DLC objects keep their Xbox id
            m[xid] = xid
    return m

def merge(keep_pc_container=True):
    pco, pcu, pcd = load('pc'); tuo, tuu, tud = load('xboxtu')
    pc_ol, x_ol = read_objectlist(pco), read_objectlist(tuo)
    remap = build_remap(pc_ol, x_ol)
    merged_ol = dict(pc_ol)
    for xid, nm in x_ol.items():
        if remap[xid] == xid and xid > max(pc_ol): merged_ol[xid] = nm
    assert sorted(merged_ol) == list(range(1, len(merged_ol) + 1))
    pcunits, tuunits = read_unitlist(pcu), read_unitlist(tuu)
    units = list(tuunits)                                   # TU list is alphabetical and a superset
    for u in pcunits:
        if u not in units: units.append(u)
    pc_recs, first = read_objlist(pcd, 'le'); tu_recs, _ = read_objlist(tud, 'be')
    have = {n for n, _ in pc_recs}
    recs = list(pc_recs)
    for nm, l in tu_recs:
        if nm in have:
            if not keep_pc_container and nm.startswith('container'):
                recs[[n for n, _ in recs].index(nm)] = (nm, sorted(remap[i] for i in l))
            continue
        recs.append((nm, sorted(remap[i] for i in l)))
    return merged_ol, units, recs, first, remap

if __name__ == '__main__':
    assert roundtrip_test()
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'work', 'generic', 'merged')
    ol, units, recs, first, remap = merge()
    d = os.path.join(out, 'tr8', 'pc-w'); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'objectlist.txt'), 'wb').write(write_objectlist(ol))
    open(os.path.join(d, 'unitlist.txt'), 'wb').write(write_unitlist(units))
    open(os.path.join(d, 'objlist.dat'), 'wb').write(write_objlist(recs, 'le', first))
    json.dump({str(k): v for k, v in sorted(remap.items())}, open(os.path.join(out, 'object_id_remap_xbox_to_pc.json'), 'w'), indent=0)
    print('merged: objects %d, units %d, objlist records %d -> %s' % (len(ol), len(units), len(recs) + 1, d))
