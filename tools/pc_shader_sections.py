"""Collect the PC ShaderLib sections (type 9, D3D9 bytecode) that converted DLC materials reference, so the DRM writer
can put them into the converted DLC DRMs in place of the Xbox (Xenos) shader sections (base PC DRMs also carry their
own copies of every shader they use; ids are global per platform).
Output: work/render/pc_shader_sections.pkl {pc_shader_id: dict(data, reloc, ver, flags, spec, from_drm)}
usage: tools/venv/bin/python -I tools/pc_shader_sections.py"""
import sys, os, pickle, json, struct
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'render')
if __name__ == '__main__':
    need = set()
    for v in json.load(open(os.path.join(W, 'dlc_shader_map.json'))).values(): need.add(v['pc'])
    mats = pickle.load(open(os.path.join(W, 'dlc_materials_pc.pkl'), 'rb'))
    for m in mats.values():
        need.update(struct.unpack_from('<4I', m['data'], 0x28))
    need.discard(0)
    res = pickle.load(open(os.path.join(W, 'pairs_render.pkl'), 'rb'))
    out = {}
    for nm, X, P in res:
        for b in P:
            if b['type'] == 9 and b['id'] in need and b['id'] not in out:
                out[b['id']] = dict(data=b['data'], reloc=b['reloc'], ver=b['ver'], flags=b['flags'], spec=b['spec'], from_drm=nm)
    pickle.dump(out, open(os.path.join(W, 'pc_shader_sections.pkl'), 'wb'))
    print('referenced PC shader ids', len(need), 'found', len(out), 'missing', sorted(need - set(out))[:20],
          'total MB %.1f' % (sum(len(v['data']) for v in out.values()) / 1e6))
