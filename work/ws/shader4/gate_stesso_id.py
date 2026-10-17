"""Gate statico: stessa sezione (tipo 9 lib PS, tipo 10 materiale) con lo stesso id = stessi byte in TUTTI i DRM dell'overlay.
uso: python gate_stesso_id.py BASE_MODS OVERLAY_DIR [RIFERIMENTO_MODS]
  candidato = BASE_MODS con i DRM di OVERLAY_DIR sovrapposti (stesso percorso relativo).
  Falliscono solo le divergenze NUOVE rispetto al RIFERIMENTO (default BASE_MODS): quelle gia' presenti non sono colpa del trapianto.
  Controllo aggiuntivo: ogni lib 9 nuova (id assente nel riferimento) deve stare in tutti i DRM che hanno un materiale che la usa."""
import sys, os, glob, struct, hashlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f10_build_dlc import drm_write


def load(base, overlay=None):
    files = {os.path.relpath(p, base): p for p in glob.glob(os.path.join(base, '**', '*.drm'), recursive=True)}
    if overlay: files.update({os.path.relpath(p, overlay): p for p in glob.glob(os.path.join(overlay, '**', '*.drm'), recursive=True)})
    out = {}
    for rel, p in files.items():
        try: d = drm_write.read(open(p, 'rb').read(), 'le')
        except Exception: continue
        out[rel] = {(s.type, s.id): hashlib.md5(s.data + b'|' + s.reloc).hexdigest() for s in d.sections if s.type in (9, 10)}
        out[rel]['_mat_lib'] = {s.id: struct.unpack_from('<I', s.data, 0x30)[0] for s in d.sections if s.type == 10}
    return out


def divergent(world):
    seen = collections.defaultdict(dict)
    for rel, secs in world.items():
        for k, h in secs.items():
            if k != '_mat_lib': seen[k][rel] = h
    return {k for k, v in seen.items() if len(set(v.values())) > 1}


if __name__ == '__main__':
    base, overlay = sys.argv[1], sys.argv[2]; ref = sys.argv[3] if len(sys.argv) > 3 else base
    cand, old = load(base, overlay), load(ref)
    new = sorted(divergent(cand) - divergent(old))
    for k in new: print('DIVERGE tipo %d id %d in %s' % (k[0], k[1], sorted(r for r, s in cand.items() if k in s)))
    oldlibs = {k[1] for w in old.values() for k in w if k != '_mat_lib' and k[0] == 9}
    bad = 0
    for rel, secs in cand.items():
        for mid, lib in secs['_mat_lib'].items():
            if lib not in oldlibs and (9, lib) not in secs: print('LIB MANCANTE: %s mat %d usa lib %d assente nel DRM' % (rel, mid, lib)); bad += 1
    print('divergenze nuove: %d, lib mancanti: %d, DRM: %d -> %s' % (len(new), bad, len(cand), 'OK' if not new and not bad else 'FAIL'))
    sys.exit(1 if new or bad else 0)
