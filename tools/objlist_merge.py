"""Merged PC objectlist.txt / unitlist.txt / objlist.dat for the DLC (thin entry point over objlists.py).

Writes work/generic/merged/tr8/pc-w/{objectlist.txt,unitlist.txt,objlist.dat} (+ object_id_remap_xbox_to_pc.json)
and verifies:
  * round trip of all list formats (PC LE, Xbox BE base/TU/DLC)
  * base objects keep their PC ids, DLC objects 822..1045 appended (no clash, contiguous ids)
  * every object id referenced by objlist.dat exists in the merged objectlist
  * remap consistency: for units present on both platforms, PC's own list vs remap(Xbox TU list)
Usage: python3 -I tools/objlist_merge.py [outdir]   (install: copy tr8\\pc-w\\* to <gamedir>\\mods\\tr8\\pc-w\\)
"""
import os, sys, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import objlists as O

def verify(ol, units, recs, remap):
    pco, pcu, pcd = O.load('pc'); tuo, tuu, tud = O.load('xboxtu')
    pc_ol = O.read_objectlist(pco)
    st = collections.Counter()
    st['base_ids_kept'] = sum(1 for k, v in pc_ol.items() if ol.get(k) == v)
    st['base_ids_total'] = len(pc_ol)
    st['objects_total'] = len(ol)
    st['ids_contiguous'] = sorted(ol) == list(range(1, len(ol) + 1))
    st['units'] = len(units)
    st['objlist_records'] = len(recs)
    st['dangling_object_refs'] = sum(1 for _, l in recs for i in l if i not in ol)
    pc_recs, _ = O.read_objlist(pcd, 'le'); tu_recs, _ = O.read_objlist(tud, 'be')
    pcd_ = dict(pc_recs)
    for nm, l in tu_recs:
        if nm in pcd_:
            a, b = set(pcd_[nm]), {remap[i] for i in l}
            st['common_units'] += 1
            st['common_units_identical'] += a == b
            st['common_obj_refs_pc'] += len(a); st['common_obj_refs_agree'] += len(a & b)
    dlc = [nm for nm, _ in recs if nm not in pcd_]
    st['dlc_units_added'] = len(dlc)
    return st, dlc

if __name__ == '__main__':
    assert O.roundtrip_test()
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(O.HERE, '..', 'work', 'generic', 'merged')
    ol, units, recs, first, remap = O.merge()
    d = os.path.join(out, 'tr8', 'pc-w'); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'objectlist.txt'), 'wb').write(O.write_objectlist(ol))
    open(os.path.join(d, 'unitlist.txt'), 'wb').write(O.write_unitlist(units))
    open(os.path.join(d, 'objlist.dat'), 'wb').write(O.write_objlist(recs, 'le', first))
    json.dump({str(k): v for k, v in sorted(remap.items())}, open(os.path.join(out, 'object_id_remap_xbox_to_pc.json'), 'w'), indent=0)
    st, dlc = verify(ol, units, recs, remap)
    for k, v in st.items(): print(k, v)
    print('dlc units:', dlc[:12], '...')
