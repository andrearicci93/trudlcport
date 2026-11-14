"""TruMenu 0.22.53: which waves the game data assigns to the weapon sound groups.

Reads work/sndgroups_0611/full3/groups_waves.tsv (tools/sound_groups.py report: group, wave id, name; one row per
wave and group it plays in - made from the own game files, not in the repo) and writes LOCAL files only (game data,
never commit them; the upload scan flags the id list):
  local/weapon_waves.txt        - per wave id: the groups it is found in, and whether it is a weapon-only wave
  local/TruMenu.weaponwaves.txt - the weapon-only wave ids for TruMenu (copy it next to tru.exe; optional)
A weapon-only wave = every group the data puts it in is one of the weapon groups (58 node, 59 weapon handling,
61 brass, 62 gunshots, 63 reload & grenades). A wave that also plays in a non-weapon group is left out (no guess).
2026-11-15 run: 4387 waves with a group, 174 weapon-only, 2 mixed.
Usage (from trudlcport): ../bin/pyt work/menu53_1411/weapon_waves.py
"""
import os
import sys

WEAPON = {58, 59, 61, 62, 63}
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "sndgroups_0611", "full3", "groups_waves.tsv")
OUT = os.path.join(HERE, "local")


def main():
    groups = {}
    with open(SRC, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline()
        if not header.startswith("group"):
            print("unexpected header: %r" % header)
            return 2
        for line in f:
            parts = line.rstrip("\r\n").split("\t")
            if len(parts) < 2 or not parts[0].strip().lstrip("-").isdigit() or not parts[1].strip().isdigit():
                continue
            groups.setdefault(int(parts[1]), set()).add(int(parts[0]))
    weapon_only = sorted(w for w, gs in groups.items() if gs and gs <= WEAPON)
    mixed = sorted(w for w, gs in groups.items() if gs & WEAPON and not gs <= WEAPON)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "weapon_waves.txt"), "w", encoding="ascii", newline="\r\n") as f:
        f.write("waves with a group: %d; weapon-only: %d; weapon + other groups: %d\n" %
                (len(groups), len(weapon_only), len(mixed)))
        for w in weapon_only:
            f.write("weapon %5d  groups %s\n" % (w, " ".join(str(g) for g in sorted(groups[w]))))
        for w in mixed:
            f.write("mixed  %5d  groups %s\n" % (w, " ".join(str(g) for g in sorted(groups[w]))))
    with open(os.path.join(OUT, "TruMenu.weaponwaves.txt"), "w", encoding="ascii", newline="\r\n") as f:
        f.write("# TruMenu 0.22.53: the %d waves the game data puts only into weapon groups (weapon_waves.py)\n"
                % len(weapon_only))
        for i in range(0, len(weapon_only), 16):
            f.write(" ".join(str(w) for w in weapon_only[i:i + 16]) + "\n")
    print("waves with a group %d, weapon-only %d, mixed %d" % (len(groups), len(weapon_only), len(mixed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
