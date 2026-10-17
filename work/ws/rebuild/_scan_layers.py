import os, hashlib, sys, collections
W = os.path.expanduser('~/Downloads/tru-port/work')
def files(base, sub=''):
    root = os.path.join(W, base, sub)
    out = {}
    if not os.path.isdir(root): return out
    for dp, dn, fn in os.walk(root):
        for f in fn:
            full = os.path.join(dp, f)
            out[os.path.relpath(full, root).replace(os.sep, '/')] = full
    return out
layers = {
 'vm_mods_expected': files('vm_mods_expected'),
 'mods_fix12': files('mods_fix12'),
 'mods_fix13': files('mods_fix13'),
 'mods_fix14': files('mods_fix14'),
 'mods_glitchfix': files('mods_glitchfix'),
 'mods_glitchfix2': files('mods_glitchfix2'),
 'mods_fix15': files('mods_fix15'),
 'mods_next': files('mods_next'),
 'mods_fix16': files('mods_fix16'),
 'mods_current': files('mods_current'),
 'mods_current_webs': files('mods_current_webs'),
 'mods_fix17': files('mods_fix17'),
 'mods_fix17_webs': files('mods_fix17_webs'),
 'mods_fix18': files('mods_fix18'),
 'mods_fix18_awf_extra': files('mods_fix18_awf_extra'),
 'mods_fix19': files('mods_fix19'),
 'mods_fix20': files('mods_fix20'),
 'chain_mods_chainfix_min': files('chain_aim/mods_chainfix_min'),
 'chain_mods_chainfix': files('chain_aim/mods_chainfix'),
 'menu_dlc_B': files('menu_dlc/B'),
 'dlc_images_image': files('dlc_images', 'image'),
 'dlc_images_local': files('dlc_images', 'local/mods'),
}
allnames = collections.defaultdict(list)
for L, d in layers.items():
    for rel in d: allnames[rel].append(L)
for L, d in layers.items():
    print(L, len(d))
print('total distinct relpaths', len(allnames))
for rel, ls in sorted(allnames.items()):
    if len(ls) > 1: pass
# files only in non-listed overlays
listed = {'vm_mods_expected','mods_fix12','mods_fix13','mods_fix14','mods_glitchfix','mods_next','mods_fix16','mods_current','mods_current_webs','mods_fix18','mods_fix18_awf_extra','mods_fix20','chain_mods_chainfix_min','menu_dlc_B','dlc_images_image','dlc_images_local'}
for rel, ls in sorted(allnames.items()):
    if not any(x in listed for x in ls): print('ONLY-UNLISTED', rel, ls)
for rel, ls in sorted(allnames.items()):
    if any(x in ('mods_glitchfix2','mods_fix15','mods_fix17','mods_fix17_webs','mods_fix19','chain_mods_chainfix') for x in ls) : print('NOTE', rel, ls)
