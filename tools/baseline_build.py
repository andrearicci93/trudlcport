#!/usr/bin/env python3
"""Costruisce una baseline identificabile da una cattura reale della VM (vm_baseline_capture.ps1).

  python3 tools/baseline_build.py --raw work/baseline/B0_raw --name B1

Produce work/baseline/<name>/:
  mods/            albero PIATTO di file reali (cp -c clone APFS): quello che la VM contiene davvero
  manifest.tsv     relpath, size, md5, origine, critico(0/1), eccezione   (ordinato; l'id e' l'md5 di questo file)
  saves/<nome>/    salvataggi congelati (water1 = Autosave+Savegame 1 della prova in acqua del 12/10)
  configs/         dgVoodoo.conf, hook, modloader, imgui.ini (dalla cattura)
  BASELINE.md, id.txt
Ogni file e' verificato contro l'md5 letto DENTRO la VM (mods.tsv): se non coincide si ferma.
"""
import argparse, hashlib, os, shutil, subprocess, sys

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(W, 'work')

# eccezioni gia' validate (tag per percorso, minuscolo): non vanno 'riparate' da una riconversione
EXC = {
    'dlc1_ei_grapple_ceiling.drm': 'ab_ring (variante confermata in VM: NON rigenerare)',
    'dlc1_ei_grapple_wall.drm': 'ab_ring (variante confermata in VM: NON rigenerare)',
    'dlc1_uo_raft_bridge_spawned.drm': 'parole 3c000000 DTP 20770 raw volute (verdict inst)',
    'generalbank.drm': 'menu DLC variante B (work/menu_dlc/B): perde QUIT nello slot condiviso',
    'dlc_caverns.drm': 'web_cutout (mods_current_webs/fix17_webs): texture 6610 ricodificata',
    'dlc_caverns_hall.drm': 'web_cutout (mods_current_webs/fix17_webs)',
    'streamgroups/dlc_water_wheel_waterwheel_main.drm': 'web_cutout + nomi streamgroup rc',
    'dlc1_uo_raft_bridge.drm': 'chainsphere: rc + sfera 21107 (+0x2e8) = b30014e8; TIPO 21106 da chainfix_min',
    'dlc1_uo_dragon_slider.drm': 'rc: TIPO punto grapple 23369 0->4; slot 21164 Xbox invariate',
    'dlc1_uo_bend_switches.drm': 'rc: materiale 21210 dal gemello PC 4767',
}
KNOWN_DEFECTS = [
    'catena sott\'acqua: la mira funziona, lo sparo NON la spezza (nessuna riga di log allo sparo)',
    'dungeon: crash 0xc0000005 EIP 0x5c019f (offset 0x1c019f) all\'ingresso (dump work/crash/rc_try2_dungeon.dmp)',
    'FMOD 0x7b92fb (offset 0x3b92fb) dopo riavvii ripetuti del livello: INFRA, non dati',
    'vetrata water_wheel renderizzata come rumore (analisi parcheggiata)',
    'anelli (grapple_ceiling) non agganciano dopo start da menu: causa ignota',
    'g_pda assente di proposito (crash noto del vecchio override)',
    '91/288 materiali DLC1 con params non risolti (colori sospetti)',
]


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def sources():
    """relpath(lower, '/') -> (abs path, origine)"""
    src = {}
    tsv = os.path.join(WORK, 'ws', 'rebuild', 'installed_effective.tsv')
    for l in list(open(tsv))[1:]:
        r = l.rstrip('\n').split('\t')
        src[r[0].lower()] = (r[4], r[2])
    rc = os.path.join(WORK, 'mods_dlc1_rc')
    for l in open(os.path.join(rc, 'md5.txt')):
        h, p = l.split(); p = p.lstrip('./')
        src[p.lower()] = (os.path.join(rc, p), 'mods_dlc1_rc')
    src['dlc1_uo_raft_bridge.drm'] = (os.path.join(WORK, 'ws', 'vmprep', 'chainsphere', 'dlc1_uo_raft_bridge.drm'), 'chainsphere')
    return src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw', required=True)
    ap.add_argument('--name', default='B1')
    a = ap.parse_args()
    raw = a.raw if os.path.isabs(a.raw) else os.path.join(W, a.raw)
    out = os.path.join(WORK, 'baseline', a.name)
    if os.path.exists(out):
        sys.exit('esiste gia\': ' + out + ' (le baseline sono immutabili: scegli un altro --name)')
    os.makedirs(os.path.join(out, 'mods'))
    vm = {}
    for l in open(os.path.join(raw, 'mods.tsv'), encoding='utf-8-sig'):
        p = l.rstrip('\r\n').split('\t')
        if len(p) == 3: vm[p[0].replace('\\', '/')] = (int(p[1]), p[2])
    src = sources()
    extra = os.path.join(raw, 'vm_extra')
    rows = []; bad = []
    for rel in sorted(vm, key=str.lower):
        size, h = vm[rel]
        key = rel.lower()
        # extra della VM (non provenienti da overlay): cartella vm_extra, nomi come in VM
        ex = os.path.join(extra, rel.replace('/', os.sep))
        if key in src and os.path.exists(src[key][0]) and md5(src[key][0]) == h:
            path, origin = src[key]
        elif os.path.exists(ex) and md5(ex) == h:
            path, origin = ex, 'vm_extra'
        else:
            bad.append(rel); continue
        dst = os.path.join(out, 'mods', rel.replace('/', os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        subprocess.run(['cp', '-c', path, dst], check=True)
        assert md5(dst) == h
        top = rel.lower().endswith(('.drm', '.tfb')) or rel.lower().startswith(('local/', 'image/'))
        rows.append((rel, size, h, origin, 1 if top else 0, EXC.get(key, '')))
    if bad:
        sys.exit('NON ricostruibili con md5 identico alla VM: %s' % bad)
    man = os.path.join(out, 'manifest.tsv')
    with open(man, 'w') as f:
        f.write('relpath\tsize\tmd5\torigin\tcritical\texception\n')
        for r in rows: f.write('\t'.join(map(str, r)) + '\n')
    bid = hashlib.md5(open(man, 'rb').read()).hexdigest()[:12]
    open(os.path.join(out, 'id.txt'), 'w').write(a.name + '-' + bid + '\n')
    # salvataggi e config
    sv = os.path.join(out, 'saves', 'water1'); os.makedirs(sv)
    for n in os.listdir(os.path.join(raw, 'saves')):
        shutil.copy2(os.path.join(raw, 'saves', n), os.path.join(sv, n))
    hall = os.path.join(out, 'saves', 'hall1'); os.makedirs(hall)
    for n in os.listdir(os.path.join(WORK, 'save', 'chain1')):
        shutil.copy2(os.path.join(WORK, 'save', 'chain1', n), os.path.join(hall, n))
    shutil.copytree(os.path.join(raw, 'configs'), os.path.join(out, 'configs'))
    for n in ('env.txt', 'gamedir.tsv'):
        shutil.copy2(os.path.join(raw, n), os.path.join(out, n))
    # BASELINE.md
    env = open(os.path.join(raw, 'env.txt')).read().splitlines()
    origins = {}
    for r in rows: origins[r[3]] = origins.get(r[3], 0) + 1
    with open(os.path.join(out, 'BASELINE.md'), 'w') as f:
        f.write('# Baseline %s-%s\n\nCatturata DENTRO la VM (vm_baseline_capture.ps1) e verificata file per file (md5) contro la ricostruzione dagli overlay.\n\n' % (a.name, bid))
        f.write('- file in mods\\: %d (critici per la verifica rapida: %d)\n- %s\n- dgVoodoo FPSLimit = 0 (verificato nel file reale)\n- tru.exe: %s\n' % (len(rows), sum(r[4] for r in rows), env[0], env[2]))
        f.write('- origini: ' + ', '.join('%s=%d' % kv for kv in sorted(origins.items())) + '\n')
        f.write('- salvataggi congelati: saves/water1 (Autosave + Savegame 1 in acqua, 12/10 22:59-23:00), saves/hall1 (work/save/chain1, parte da dlc_caverns_hall)\n\n')
        f.write('## Eccezioni validate (non rigenerare)\n')
        for k, v in sorted(EXC.items()): f.write('- `%s`: %s\n' % (k, v))
        f.write('\n## Difetti noti in questa baseline\n')
        for d in KNOWN_DEFECTS: f.write('- ' + d + '\n')
    print('baseline %s-%s: %d file in %s' % (a.name, bid, len(rows), out))


if __name__ == '__main__':
    main()
