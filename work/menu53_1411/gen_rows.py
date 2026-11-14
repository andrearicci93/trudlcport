"""TruMenu 0.22.53 W11: prints the bar rows of the two sound log trees (Filter (Zeigen), Stumm / Solo) and the Paket B2
copies, for Spiel-Einstellungen / Ton / Ton-Log - the same order of kinds and sub-groups as kW8CatOrder / kW8Sub in
TruMenu.cpp. Output: work/menu53_1411/rows_w11.txt (pasted into TruMenu.cpp by hand with the Edit tool).
Usage (from trudlcport): ../bin/pyt work/menu53_1411/gen_rows.py
"""
import os

KINDS = [  # key, de, en, group key suffix
    ("lara", "Lara", "Lara", "lara"),
    ("weapons", "Waffen", "Weapons", "wp"),
    ("enemies", "Gegner", "Enemies", "en"),
    ("world", "Welt / Umgebung", "World / ambience", "wo"),
    ("objects", "Objekte & Mechanik", "Objects & mechanics", "ob"),
    ("ui", "PDA / UI", "PDA / UI", "ui"),
    ("speech", "Sprache", "Speech", "sp"),
    ("music", "Musik", "Music", "mu"),
]
SUBS = {  # kind -> [(key, de, en, groups)]
    "lara": [("lara_voice", "Stimme", "voice", "g69, DLC 2 g77"),
             ("lara_body", "K\\303\\266rper / Foley", "body / foley", "g32-42, DLC 2 g78"),
             ("lara_gear", "Ausr\\303\\274stung", "gear", "g34, g14"),
             ("lara_special", "Spezial (Herzschlag, Zeitlupe, Ziel)", "special (heartbeat, slow motion, target)", "g55"),
             ("lara_shadow", "Schattenkraft / DLC-2-Effekte", "shadow power / DLC 2 FX", "g79")],
    "weapons": [("wp_draw", "Ziehen & Spannen", "draw & cock", "g58, g59"),
                ("wp_shot", "Sch\\303\\274sse", "shots", "g62"),
                ("wp_reload", "Nachladen & Granaten", "reload & grenades", "g63"),
                ("wp_brass", "Patronenh\\303\\274lsen", "brass", "g61"),
                ("wp_impact", "Einschl\\303\\244ge & Sirren", "impacts & whiz", "g51, g52"),
                ("wp_lara14", "Laras Waffe ohne Gruppe", "Lara's weapon without a group", "g14")],
    "enemies": [("en_body", "K\\303\\266rper & Schritte", "body & movement", "g27, g28"),
                ("en_gear", "Ausr\\303\\274stung", "gear", "g29"),
                ("en_attack", "Angriffe", "attacks", "g30"),
                ("en_voice", "Rufe & Stimmen", "calls & voices", "g65, g66"),
                ("en_kraken", "Kraken", "kraken", "g67")],
    "world": [("wo_default", "Welt-Standard (ohne Gruppe)", "world default (no group)", "g14"),
              ("wo_amb", "Umgebung & Loops", "ambience & loops", "g15-19"),
              ("wo_animals", "Tiere & V\\303\\266gel", "animals & birds", "g20"),
              ("wo_fire", "Feuer", "fire", "g21"),
              ("wo_wind", "Wind & Gewitter", "wind & thunder", "g22"),
              ("wo_water", "Wasser & Unterwasser", "water & underwater", "g23, g24")],
    "objects": [("ob_mech", "Mechanik", "mechanisms", "g43, g45"),
                ("ob_debris", "Tr\\303\\274mmer", "debris", "g44"),
                ("ob_blast", "Explosionen", "explosions", "g31"),
                ("ob_traps", "Fallen & Klingen", "traps & blades", "g60, g76"),
                ("ob_vehicle", "Fahrzeuge", "vehicles", "g49"),
                ("ob_dlc2", "DLC-2-Objekte", "DLC 2 objects", "g46")],
    "ui": [("ui_hud", "HUD", "HUD", "g53"),
           ("ui_binoc", "Fernglas & Scan", "binoculars & scan", "g54"),
           ("ui_menu", "Men\\303\\274", "menu", "g56"),
           ("ui_pda", "PDA & Sonar", "PDA & sonar", "g57")],
    "speech": [("sp_cine", "Zwischensequenzen", "cutscenes", "g25"),
               ("sp_hints", "Laras Hinweise", "Lara's hints", "g70"),
               ("sp_radio", "Funk (Zip)", "radio (Zip)", "g72-75"),
               ("sp_nodes", "Stimmen-Knoten", "voice nodes", "g8, g9, g64")],
    "music": [("mu_music", "Musik", "music", "g1-3, g10-12"),
              ("mu_stinger", "Musik-Stinger", "music stingers", "g13")],
}
FLAG_LV2, FLAG_LV3 = "kQfLv2", "kQfLv3"


def row(de, en, item, arg, kind, val="0", colour="kQbSound", flags="0"):
    one = '    {"%s", "%s", "%s", "%s", %s, -1, kQcNone, %s, %s, %s},' % (de, en, item, arg, kind, val, colour, flags)
    if len(one) <= 120:
        return one
    return '    {"%s", "%s",\n     "%s", "%s", %s, -1, kQcNone, %s, %s, %s},' % (de, en, item, arg, kind, val, colour, flags)


def tree(out, show):
    for key, de, en, g in KINDS:
        gk = ("tlf_" if show else "tls_") + g
        out.append(row(de, en, "-", gk, "kQbGroup", colour="kQbSound", flags=FLAG_LV3))
        if show:
            out.append(row("%s (ganze Art)" % de, "%s (whole kind)" % en, "snd.logcat", key, "kQbBool"))
        else:
            out.append(row("%s (ganze Art)" % de, "%s (whole kind)" % en, "snd.hear", key, "kQbValue", "kQvHear"))
        for sk, sde, sen, grp in SUBS[key]:
            if show:
                out.append(row("%s (%s)" % (sde, grp), "%s (%s)" % (sen, grp), "snd.logsub", sk, "kQbBool"))
            else:
                out.append(row("%s (%s)" % (sde, grp), "%s (%s)" % (sen, grp), "snd.hear", sk, "kQbValue", "kQvHear"))


def main():
    out = ["    // ---- Filter (Zeigen): the log display only (a hidden kind stays audible) ----",
           row("Filter (Zeigen)", "Filter (show)", "-", "ton_log_filter", "kQbGroup", flags=FLAG_LV2),
           row("Filter folgt Stumm", "Filter follows mute", "snd.logfollow", "", "kQbBool")]
    tree(out, True)
    out += ["    // ---- Schnell-Hoeren (plain heading) and Stumm / Solo: the sound only (a muted kind stays in the log",
            "    // unless 'Filter folgt Stumm' or a filter hides it) ----",
            row("Schnell-H\\303\\266ren", "Quick hearing", "-", "", "kQbLabel", colour="kQbSound", flags=FLAG_LV2),
            row("Stumm / Solo", "Mute / solo", "-", "ton_log_hear", "kQbGroup", flags=FLAG_LV2),
            row("Alles zur\\303\\274ck (jeder Ton-Schalter)", "Everything back (every sound switch)", "snd.mute", "all 0",
                "kQbAction", colour="kQbGrey"),
            row("Neuester Ton solo (oberste Zeile)", "Newest sound solo (top line)", "snd.solonew", "", "kQbAction"),
            row("Hall folgt Stumm", "Reverb follows mute", "snd.reverbmute", "", "kQbBool"),
            row("Hall aus", "Reverb off", "snd.reverboff", "", "kQbBool")]
    tree(out, False)
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "rows_w11.txt"), "w", encoding="ascii", newline="\r\n") as f:
        f.write("\n".join(out) + "\n")
    print("rows %d" % len(out))


if __name__ == "__main__":
    main()
