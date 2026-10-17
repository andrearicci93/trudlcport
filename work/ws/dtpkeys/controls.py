import sys, os; sys.path.insert(0,'tools')
import dtp_keys as K, dtp_audit as A
C=[('chunkdoll hdr','vm_mods_expected','knight_thrall_chunkdoll.drm',20951,(0x130,0x158)),
   ('aidata caverns pre-fix15','mods_glitchfix','dlc_caverns.drm',20872,None),
   ('sewer_gate group raw pre-fix16','mods_next','dlc1_uo_sewer_gate.drm',21104,(0x450,)),
   ('caverns_hall COUNT pre-fix18','mods_current','dlc_caverns_hall.drm',23469,(0x1e4,)),
   ('adren_trap evlist pre-fix14','vm_mods_expected','dlc1_uo_adren_trap.drm',20940,None),
   ('raft chain TIPO 21106 pre-chainfix','mods_fix20','dlc1_uo_raft_bridge.drm',21106,None),
   ('dragon_slider grapple pt 23369','mods_fix20','dlc1_uo_dragon_slider.drm',23369,None)]
for tn in ('T0','T1','T2'):
  print('==',tn)
  for lab,d,f,sid,offs in C:
    p=os.path.join(K.W,d,f)
    fs=[x for x in K.scan_file(f,p,K.TIERS[tn],K.FAMS) if x['id']==sid]
    hit=[x for x in fs if offs is None or x['off'] in offs]
    print('  %-36s DTP %d: flagged in DTP %d, at target %d %s'%(lab,sid,len(fs),len(hit),[(hex(x['off']),x['xbox'],x['pc'],x['want'],x['fam'],x['owned']) for x in hit[:3]]))
