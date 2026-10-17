import sys, os, struct, collections, pickle
T = os.path.expanduser('~/Downloads/tru-port'); sys.path.insert(0, T + '/tools')
import drm_reloc as R, drm_write as DW
import dtpid_sweep as DS
def ctx(): return DS.ctx()
def pc_sections(path):
    return DW.read(open(path, 'rb').read(), 'le')
def xbox_sections(rel):
    return DS.xsecs_of(rel)
def pair_file(rel, path):
    """-> list of (xbox sec dict, pc section obj) for type-7 sections"""
    xs = xbox_sections(rel); D = pc_sections(path); st, ids = ctx(); ids.local = {}
    out = []
    for s, k in DS.pairs(xs, D, ids): out.append((s, D.sections[k]))
    return out
