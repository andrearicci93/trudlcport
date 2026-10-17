"""Convert all texture sections of an Xbox DRM (e.g. a DLC DRM) to PC PCD9 section payloads.
python -I tex_dlc.py <bigfile.000> <name e.g. xenon-w\\dlc_level1_start.drm> <outdir> [--png N]
Writes <outdir>/sec<idx>_<id>.pcd9 (PC section payload = 24B PCD9 header + data, use as the section data
of type 5 with the same reloc (none)), manifest.json, optional PNGs of base levels + contact_sheet.png."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from archive import Archive
from drm import cdrm_decode, sections_with_data
from names import crc
import tex_convert as T


def convert_drm_textures(raw):
    """raw = decompressed big-endian DRM bytes -> list of dicts (section index, id, xhdr, pc bytes or error)."""
    h, secs = sections_with_data(raw, 'be')
    out = []
    for s in secs:
        if s['type'] != 5: continue
        xh = T.parse_xbox(s['data'])
        r = dict(i=s['i'], id=s['id'], nreloc=s['nreloc'], fmt=xh['fmtname'], w=xh['w'], h=xh['h'], mips=xh['mips'],
                 flags=xh['flags'], xsize=s['size'])
        try:
            r['pc'] = T.convert(s['data'])
        except Exception as e:
            r['err'] = repr(e)
        out.append(r)
    return out


def contact_sheet(imgs, path, cell=128, cols=8):
    from PIL import Image, ImageDraw
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cell, rows * (cell + 12)), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    for n, (label, im) in enumerate(imgs):
        x, y = (n % cols) * cell, (n // cols) * (cell + 12)
        t = Image.fromarray(im).convert('RGBA')
        t.thumbnail((cell, cell))
        bg = Image.new('RGB', t.size, (128, 128, 128)); bg.paste(t, mask=t.split()[3] if label.endswith('a') else None)
        sheet.paste(bg if label.endswith('a') else t.convert('RGB'), (x, y))
        d.text((x + 2, y + cell), label[:22], fill=(255, 255, 0))
    sheet.save(path)


if __name__ == '__main__':
    big, name, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    npng = int(sys.argv[sys.argv.index('--png') + 1]) if '--png' in sys.argv else 0
    os.makedirs(outdir, exist_ok=True)
    a = Archive(big, 'be')
    r = a.find(crc(name))
    raw = cdrm_decode(a.read(r[0]), 'be')
    res = convert_drm_textures(raw)
    man = []
    imgs = []
    for r in res:
        m = {k: v for k, v in r.items() if k != 'pc'}
        if 'pc' in r:
            fn = 'sec%04d_%x.pcd9' % (r['i'], r['id'])
            open(os.path.join(outdir, fn), 'wb').write(r['pc'])
            m['file'] = fn; m['pcsize'] = len(r['pc'])
            if len(imgs) < npng:
                im = T.pc_image(r['pc'])
                lab = '%d %s %dx%d' % (r['i'], r['fmt'], r['w'], r['h'])
                imgs.append((lab, im))
                # normal maps (DXN->DXT5): show reconstructed normal (R=x, G=a=y, B=z)
                if r['fmt'] == 'DXN':
                    x = im[..., 0].astype(np.float32) / 127.5 - 1; y = im[..., 3].astype(np.float32) / 127.5 - 1
                    z = np.sqrt(np.clip(1 - x * x - y * y, 0, 1))
                    imgs[-1] = (lab, (np.stack([x, y, z], -1) * 127.5 + 127.5).clip(0, 255).astype(np.uint8))
        man.append(m)
    json.dump(man, open(os.path.join(outdir, 'manifest.json'), 'w'), indent=0)
    ok = sum('pc' in r for r in res)
    print(name, 'texture sections', len(res), 'converted', ok, 'errors', [(r['i'], r['err']) for r in res if 'err' in r][:5])
    if imgs:
        contact_sheet(imgs, os.path.join(outdir, 'contact_sheet.png'))
        print('contact sheet with', len(imgs))
