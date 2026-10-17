"""Build the effective DLC1 overlay as installed in the VM (see CONVENTIONS + NOTES 'STATO INSTALLATO IN VM').
Per relpath: the highest layer (in ORDER) that contains it wins. Writes installed_effective.tsv.
Also reports the 'unlisted' overlays (fix15, glitchfix2, fix17, fix17_webs, fix19, chainfix non-min) and whether
their files are identical to the winning version (so we know whether excluding them loses anything)."""
import os, hashlib, collections, sys
W = os.path.expanduser('~/Downloads/tru-port/work')
HERE = os.path.dirname(os.path.abspath(__file__))
# (layer name, directory, mods-relative prefix to strip from relpath, skip-names)
ORDER = [
 ('vm_mods_expected', 'vm_mods_expected', ''),
 ('mods_fix12', 'mods_fix12', ''),
 ('mods_fix13_padshock', 'mods_fix13', ''),
 ('mods_fix14', 'mods_fix14', ''),
 ('mods_glitchfix', 'mods_glitchfix', ''),
 ('mods_next', 'mods_next', ''),
 ('mods_fix16', 'mods_fix16', ''),
 ('mods_current', 'mods_current', ''),
 ('mods_current_webs', 'mods_current_webs', ''),
 ('mods_fix18', 'mods_fix18', ''),
 ('mods_fix18_awf_extra', 'mods_fix18_awf_extra', ''),
 ('mods_fix20', 'mods_fix20', ''),
 ('chain_mods_chainfix_min', 'chain_aim/mods_chainfix_min', ''),
 ('menu_dlc_B', 'menu_dlc/B', ''),
 ('dlc_images_image', 'dlc_images/image', 'image/'),
 ('dlc_images_local', 'dlc_images/local/mods', ''),
]
EXCLUDE_REL = {'g_pda.drm'}   # not installed in VM by design (NOTES mods_next/INSTALL.md, mods_current README)
SKIP_NAMES = {'md5.txt', 'MD5.txt', 'README.md', 'INSTALL.md', 'MANIFEST.md', 'NOTES_agent.md', 'patch_log.txt'}
UNLISTED = [
 ('mods_fix15', 'mods_fix15'), ('mods_glitchfix2', 'mods_glitchfix2'), ('mods_fix17', 'mods_fix17'),
 ('mods_fix17_webs', 'mods_fix17_webs'), ('mods_fix19', 'mods_fix19'), ('chain_mods_chainfix', 'chain_aim/mods_chainfix'),
]
def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()
def walk(d):
    root = os.path.join(W, d); out = {}
    if not os.path.isdir(root): return out
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if f in EXCLUDE_REL or f in SKIP_NAMES or dp.endswith('/check') or '/check/' in dp + '/' or '/unnamed' in dp: continue
            full = os.path.join(dp, f)
            out[os.path.relpath(full, root).replace(os.sep, '/')] = full
    return out
def layer_files(d, pref):
    fs = walk(d)
    if d == 'dlc_images/image': return {'image/' + k: v for k, v in fs.items() if k.endswith('.raw')}
    if d == 'dlc_images/local/mods': return {'local/' + k[len('mods/local/'):] if k.startswith('mods/local/') else k: v for k, v in fs.items()}
    return fs
eff = {}; src = collections.defaultdict(list)
for name, d, pref in ORDER:
    for rel, full in layer_files(d, pref).items():
        eff[rel] = (name, full); src[rel].append(name)
rows = []
for rel in sorted(eff):
    name, full = eff[rel]
    rows.append((rel, md5(full), name, ','.join(src[rel]), full))
with open(os.path.join(HERE, 'installed_effective.tsv'), 'w') as f:
    f.write('relpath\tmd5\twinning_overlay\tall_overlays_containing\tabs_path\n')
    for r in rows: f.write('\t'.join(r) + '\n')
print('effective files', len(rows), collections.Counter(r[2] for r in rows))
# unlisted overlays: compare with winner
for name, d in UNLISTED:
    fs = walk(d)
    same = diff = 0; only = []
    for rel, full in fs.items():
        if rel in eff:
            if md5(full) == md5(eff[rel][1]): same += 1
            else: diff += 1; print('  UNLISTED-DIFFERS', name, rel, '(winner', eff[rel][0] + ')')
        else: only.append(rel)
    print('%-18s files %3d  identical-to-winner %3d  differs %2d  only-here %s' % (name, len(fs), same, diff, only))
