import sys,os
sys.path.insert(0,'/path/to/trudlcport/tools')
import dtp_audit as A, drm_write as DW
def xs(rel): return A.xsecs(rel)
def pc(path): return DW.read(open(path,'rb').read(),'le')
