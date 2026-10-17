import sys, os, struct
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm_write as DW, drm_reloc as R
W='/path/to/trudlcport/work'
def pc(path=W+'/ws/vmprep/chainsphere/dlc1_uo_raft_bridge.drm'):
    return DW.read(open(path,'rb').read(),'le')
def xb(rel='dlc1_uo_raft_bridge.drm'):
    from soundplex_fix import xsecs_of
    return xsecs_of(rel)
