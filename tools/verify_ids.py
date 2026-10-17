"""Gap check of the DLC id remap + merged object/unit lists (all four DLC packs).

Checks
  A every section id and every reloc id-ref value in every DLC DRM (pack1/2/10/11) maps through DlcIds without
    falling back to 'unmapped identity' (base map, objlist remap or dlc_idmap.json new-id table)
  B per type the final PC ids are collision free: no two different Xbox ids -> same PC id; DLC-new PC ids not in
    the PC id universe (bigfile + patch.000)
  C object lists: every pack's objectlist (pack1/2/10/11, TU) agrees id-by-id with the merged list after remap;
    every DLC unit of every pack is in the merged unitlist and has an objlist.dat record whose ids exist
  D every Obj (type 11) section: remapped id is in the merged objectlist and its name == the DRM name
Usage: python3 -I tools/verify_ids.py [extend]   (extend: first add uncovered ids to dlc_idmap.json, keeping old entries)
"""
import sys, os, json, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R, dlc_generic as DG, generic_store, objlists as O
from archive import Archive
from names import load, L
from drm import cdrm_decode, sections_with_data
C = '/path/to/Xenia-SteveRepack/Content/534307EC/00000002/'
PACKS = {'pack10': C + '9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000', 'pack11': C + '600A12643FCDAC84003E6E0DBD0A1A8F7DAE9DD153/pack11.000',
         'pack1': C + 'E5AFB2B959A72C52120D73678AED11BD8752686753/pack1.000', 'pack2': C + '9FDDD06617D1016DE468ACF53AC663E8BA2AD41853/pack2.000'}
MERGED = os.path.join(DG.W, 'merged', 'tr8', 'pc-w')

def dlc_drms():
    xn = load(L + 'Tomb Raider Underworld (Xenon).txt')
    for pk, path in PACKS.items():
        A = Archive(path, 'be')
        for r in A.idx:
            f = A.read(r)
            if f[:4] != b'CDRM' and f[:4] != b'\0\0\0\x13': continue
            raw = cdrm_decode(f, 'be')
            h, secs = sections_with_data(raw, 'be')
            yield pk, xn.get(r['hash'], '0x%08x' % r['hash']), r['spec'], secs

def extend_table():
    """add pack1/pack2 (and any other uncovered) ids to work/generic/dlc_idmap.json"""
    store = generic_store.load(); ids = DG.DlcIds()
    want = collections.defaultdict(set)
    for pk, name, spec, secs in dlc_drms():
        for s in secs:
            want[s['type']].add(s['id'])
            if s['reloc'] and s['data']:
                r = R.parse(s['reloc'], 'be')
                for t, o in r.idref + r.idref_a:
                    v, = struct.unpack_from('>I', s['data'], o)
                    if v not in (0, 0xffffffff): want[t].add(v)
    print('extended dlc_idmap.json:', dict(ids.extend(store, want)))

def main():
    store = generic_store.load(); ids = DG.DlcIds()
    st = collections.Counter(); unm = collections.defaultdict(set)
    fwd = collections.defaultdict(dict)                      # type -> xid -> pcid
    ol = O.read_objectlist(open(os.path.join(MERGED, 'objectlist.txt'), 'rb').read())
    for pk, name, spec, secs in dlc_drms():
        st['drm', pk] += 1
        vals = []
        for s in secs:
            vals.append((s['type'], s['id']))
            if s['reloc'] and s['data']:
                r = R.parse(s['reloc'], 'be')
                for t, o in r.idref + r.idref_a:
                    v, = struct.unpack_from('>I', s['data'], o)
                    if v not in (0, 0xffffffff): vals.append((t, v))
            if s['type'] == 11:
                pid = ids(11, s['id'])
                nm = name.split('\\')[-1][:-4]
                st['obj_sections'] += 1
                st['obj_in_list'] += pid in ol
                st['obj_name_match'] += ol.get(pid) == nm
                if ol.get(pid) != nm and st['obj_mismatch_shown'] < 5:
                    st['obj_mismatch_shown'] += 1; print('  obj mismatch', pk, name, s['id'], pid, ol.get(pid))
        for t, v in vals:
            before = ids.missing[t]
            p = ids(t, v)
            if ids.missing[t] != before: unm[t].add((v, pk, name))
            fwd[t][v] = p
    print('DRMs', {k[1]: v for k, v in st.items() if k[0] == 'drm' if isinstance(k, tuple)})
    print('A unmapped (type: distinct xids):', {t: len(v) for t, v in unm.items()}, 'examples', {t: sorted(v)[:4] for t, v in unm.items()})
    pc_ids = store['pc_ids']
    for t, d in sorted(fwd.items()):
        inv = collections.defaultdict(set)
        for x, p in d.items(): inv[p].add(x)
        coll = {p: xs for p, xs in inv.items() if len(xs) > 1}
        base = ids.base.get(t, {})
        new_in_pc = sum(1 for x, p in d.items() if x not in base and t != 11 and p in pc_ids.get(t, ()))
        print('B type %2d: xids %5d, PC ids %5d, many-to-one %d %s, DLC-new ids colliding with PC universe %d' % (
            t, len(d), len(inv), len(coll), list(coll.items())[:3], new_in_pc))
    # C lists
    merged_units = O.read_unitlist(open(os.path.join(MERGED, 'unitlist.txt'), 'rb').read())
    recs, _ = O.read_objlist(open(os.path.join(MERGED, 'objlist.dat'), 'rb').read(), 'le')
    rec = dict(recs)
    remap = {int(k): v for k, v in json.load(open(os.path.join(DG.W, 'merged', 'object_id_remap_xbox_to_pc.json'))).items()}
    for prefix in ('dlc_pack1', 'dlc_pack2', 'dlc_pack10', 'dlc_pack11', 'xboxtu'):
        o, u, d = O.load(prefix)
        xol = O.read_objectlist(o)
        bad = [(x, n) for x, n in xol.items() if ol.get(remap.get(x)) != n]
        units = O.read_unitlist(u)
        miss_u = [x for x in units if x not in merged_units]
        xrecs, _ = O.read_objlist(d, 'be')
        miss_r = [n for n, _ in xrecs if n not in rec]
        diff_r = [n for n, l in xrecs if n in rec and sorted(remap[i] for i in l) != sorted(rec[n])]
        print('C %-10s objects %4d name/id mismatches %d %s | units %3d missing %d %s | objlist recs %3d missing %d, differing %d %s' % (
            prefix, len(xol), len(bad), bad[:3], len(units), len(miss_u), miss_u[:3], len(xrecs), len(miss_r), len(diff_r), diff_r[:4]))
    dang = sum(1 for n, l in recs for i in l if i not in ol)
    print('C merged objlist.dat dangling object ids:', dang)
    print('D Obj sections %d, id in merged list %d, name matches %d' % (st['obj_sections'], st['obj_in_list'], st['obj_name_match']))

if __name__ == '__main__':
    if sys.argv[1:] == ['extend']: extend_table()
    main()
