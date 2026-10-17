import sys, struct
sys.path.insert(0, '/path/to/trudlcport/tools')
import engine_walk_check as E
dirs = ['vm_mods_expected','mods_fix12','mods_fix13','mods_fix14','mods_glitchfix','mods_next','mods_fix16','mods_current','mods_current_webs','mods_fix18','mods_fix18_awf_extra','mods_fix20','chain_aim/mods_chainfix_min','menu_dlc/B','mods_dlc1_rc']
ov = E.overlay(dirs)
import glob
for name in ['dlc_dungeon','dlc_watertunnel','dlc_water_wheel','dlc_treasureroom','dlc_caverns','dlc_caverns_hall','dlc_dungeonhalla','dlc_dungeonhallb','dlc_pillory']:
    p = ov.get(name + '.drm')
    if not p: print(name, 'NOT in overlay'); continue
    c = E.Ctx(name, open(p, 'rb').read())
    its = E.intros(c); hits = []
    for di, o in its:
        d = c.secs[di].data
        oid = struct.unpack_from('<I', d, o + 0x50)[0]
        if (oid & 0xffff) == 828:
            fl = struct.unpack_from('<4f', d, o + 0x10) if False else None
            hits.append((o, struct.unpack_from('<I', d, o + 0x58)[0], d[o:o+0x90], oid))
    print(name, p.split('work/')[-1], 'intros', len(its), 'dragon_slider(828) intros', len(hits))
    for o, uid, raw, oid in hits:
        print('   off 0x%x oidfield 0x%x uid %d floats:' % (o, oid, uid), [round(x, 1) for x in struct.unpack('<36f', raw)[:12]])
