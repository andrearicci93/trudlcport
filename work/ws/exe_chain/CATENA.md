# Catena exe del port: 56d1ce2d → 2b7ee74c (14/11/2026, offline, Windows)

**Esito: catena RIPRODOTTA byte per byte su Windows.** Da `work/laa/tru_steam.exe.unpacked.exe` (56d1ce2d) rieseguendo 28 passi
(copie degli script, clang 23 di `C:\Program Files\LLVM\bin`) si ottiene `rebuild/catena/35_cs2.exe` con MD5
`2b7ee74c37394be208195efd0952cd5f`, identico all'exe installato e a `work/ws/b269_crash/tru_s8n_sap_cs2_cs.exe`.
Ogni stadio è stato anche provato isolato sul proprio ingresso di riferimento (`rebuild/solo/`, s1…s7 compresi): 35/35 MD5 identici.
Unica eccezione: lo script dello stadio **s8n** (`patch_nullfilter.py`, scratchpad Mac) non c'è più; l'ho **ricostruito dal delta**
(`tools/patch_nullfilter.py`, 76 byte, asserzioni su md5 di ingresso/uscita e byte originali).

## MD5 di riferimento
| file | md5 |
|---|---|
| `pc/tru.exe` = `work/laa/tru_steam.exe` (Steam originale) | b36da327a320eab8b5c8464b27685840 |
| `work/laa/tru_steam.exe.unpacked.exe` (Steamless `--realign`) | 56d1ce2dffa62f16354063da2df44d5a |
| `<gioco>\tru.exe` = `work/ws/b269_crash/tru_s8n_sap_cs2_cs.exe` = ricostruito | 2b7ee74c37394be208195efd0952cd5f |
| `work/ws/b269_crash/out/tru_s8n_sap_cs2_aa_cs.exe` (patch_aa_mask, NON installato, 43 B sopra 2b7ee74c) | 877b1bc5… |

Elenco completo (94 exe sotto `work/` e `pc/`): `md5_sorted.txt`; genealogia per vicinanza di byte: `lineage.txt` (`tools/lineage.py`).

**Il suffisso `_cs` non è un checksum** (il campo CheckSum PE è 0 sia nel vanilla sia nel finale): indica la
**guardia camerashakes** (`tools/camerashakes_guard.py`, 28 byte: 0x5ee94d → cave 0x83df90), aggiunta da `tru_b159_s8_fe_cs.exe`
in poi; il nome di ogni stadio successivo si inserisce prima di `_cs`. `cs2` = seconda guardia camerashakes (0x5ee9bc → 0x83dfa8).
Varianti `tuload_cs`, `s1_cs`, `s2_cs`, `s4_cs`, `s1n_log*`, `s2*`, `s4n`, `s8nh`, `logb/c/d`, `tap/probe_*` sono rami laterali (diagnostica/bisect).

## Tabella degli stadi (ordine della catena)
"in"/"out" = primi 8 caratteri dell'MD5. Script relativi a `C:\tru-port\`. Siti = VA toccati fuori dalle sezioni nuove (vedi `deltas/`).

| # | stadio | script | in | out | scopo | riprodotto |
|---|---|---|---|---|---|---|
| 1 | laa | (interno: Characteristics \|= 0x20) | 56d1ce2d | bf5b1611 | flag LARGE_ADDRESS_AWARE (1 byte header) | sì |
| 2 | fmodinit | tools/fmod_init_guard.py | bf5b1611 | 40f76950 | 0x582200: azzera 3 locali dell'init FMOD (AV 0x7b92fb), cave 0x83de00 | sì |
| 3 | lighttex | tools/light_tex_guard.py | 40f76950 | 919209ca | guardia X+0x418 luce proiettata (0x50a645/0x50a683), cave 0x83de60; .text diventa RWX | sì |
| 4 | soundplex | tools/soundplex_guard.py | 919209ca | f47814ff | guardia dispatcher SoundPlex 0x5920d5, cave 0x83df40 | sì |
| 5 | reticle | work/ws/giro10/out_b117/exe/reticle_guard.py | f47814ff | 5560abac | (B117) guardia reticolo granata 0x71e710, cave 0x83dfd0 | sì |
| 6 | nullret | work/ws/dlc2_prot/attach/patch_exe_nullret.py | 5560abac | 7eda68ed | 0x4d0959 je → epilogo (risolutore anim UI ritorna NULL); exe non conservato, rigenerato | sì |
| 7 | dlc2data | work/ws/dlc2_wallvein/patch_exe_dlc2data.py (include patch_exe_wall) | 7eda68ed | 9974175d | native NsLaraBase 70..73 (0x7b5d23→0x83dc80) + classe nativa `dlc2data` (0x7ab6a3→0x83dd10) | sì |
| 8 | tuload | work/ws/dlc2_tuport/spec_load/build_tuload.py | 9974175d | 7f3dcdc5 | sezione .tuload: selezione TU lara_doppelganger→doppelganger_casual, flag game+0x1244 | sì |
| 9–16 | s1…s8 | work/ws/dlc2_tuport/exe_build/patch_exe_shadow.py `--stage N` (sempre da tuload, cumulativo) | 7f3dcdc5 | d74264f1, ce372986, e4498234, ae7b493b, 1a59c60f, 221dcb99, 573f750e, **f2889b3a** | modulo ombra S' (sezione .tuext): s1 tabelle id TU + guardia 0x785967; s2 hook per-frame 0x7228ae + cond 0x416/0x417; s3 azione 0x3fa; s4 TM 10 slot; s5 azioni di movimento; s6 markup 22/23; s7 navigazione tipo 22; s8 guardia chiave azione nulla 0x785dc6 | sì (tutti 8) |
| 17 | fmodempty | tools/fmod_empty_guard.py | f2889b3a | 1ee81820 | 0x7c497b: lista FMOD vuota (boot-crash 0x7c4984), cave 0x83de40 | sì |
| 18 | cs | tools/camerashakes_guard.py | 1ee81820 | 9cb61a7d | guardia camerashakes 0x5ee94d, cave 0x83df90 (= suffisso `_cs`) | sì |
| 19 | s8n | **exe_chain/tools/patch_nullfilter.py (RICOSTRUITO; originale perso)** | 9cb61a7d | 149d3132 | 3 guardie filtro markup nullo 0x723330/0x723380/0x7295a0 → .tuext 0x123f800.. | sì (script ricostruito) |
| 20 | log | work/ws/dlc2_tuport/animlog/patch_animlog3.py poi patch_condlog.py | 149d3132 | 268bded0 | logger animazioni (0x441fb0) + logger condizioni grafo (0x785968), solo diagnostica | sì |
| 21 | loge | work/ws/dlc2_tuport/animlog/patch_btnmap.py (v3) | 268bded0 | 7d8ccfb0 | pulsanti logici TU 141..147 dai record PC dello stesso tasto (hook 0x7820e0) | sì |
| 22 | logf | work/ws/dlc2_tuport/animlog/patch_probe.py | 7d8ccfb0 | 8693889e | logger sonda parete 0x7594c0 (diagnostica) | sì |
| 23 | att | work/ws/b236/patch_attach608.py | 8693889e | 0f0970d4 | caso 608: aggancio al markup tipo 22 (vena) nel tick azione 0xe6 (0x772f8a → .tuext 0x1240f80) | sì |
| 24 | g0 | work/ws/b236/patch_native0_guard.py | 0f0970d4 | d478d4bf | guardia native script 0 (0x448100 → cave .shad 0x10d9f00) | sì |
| 25 | fx | work/ws/b236/patch_fx.py | d478d4bf | 39052325 | sezione .tufx: FX del potere ombra (catena hook_lara 0x123e044) | sì |
| 26 | fx2 | work/ws/b236/patch_fx2.py | 39052325 | 84b3ef59 | contenimento corruzione liste istanze (0x5bc70d, .tufx+0x400) | sì |
| 27 | keep | work/ws/b236/patch_keep.py | 84b3ef59 | 030ca860 | keep-list del player sostitutivo, pozza/morte (0x5de3b5, .tufx+0x600/+0xe00) | sì |
| 28 | gp7 | work/ws/b245_fx/patch_b245.py | 030ca860 | 8c7ec513 | GlobalParams[7] TU + suoni S' (0x773bea, .tufx+0x60/+0x800) | sì |
| 29 | dmg | work/ws/b245_qe/patch_dmg.py (applicato su gp7 → `b245_all`) | 8c7ec513 | 153c64cf | tipi di danno DLC2 0x12..0x1b nel danno nemici (0x63761b, 0x6376d5) | sì |
| 30 | fin | work/ws/b245_fin/patch_fin.py (legge pack11 Xbox da C:\Xenia-SteveRepack) | 153c64cf | aa6c4c9a | sezione .tufin: finisher del doppel sui thrall + morte definitiva; maschera 0x1242020 | sì |
| 31 | dtpg | work/ws/b246_crash/patch_dtpg.py | aa6c4c9a | 1c257f71 | guardia di range id DTP nei getter 0x54df80/0x54dfa0 (.tufin+0xc00) | sì |
| 32 | chunk | work/ws/b247_chunk/patch_chunk.py | 1c257f71 | 649cc396 | niente ChunkDoll a mondo fisico bloccato (0x697067, 0x624d0b, .tufin+0xc80; maschera 0x1f→0x3f) | sì |
| 33 | hairdt | work/ws/b262_hairdump/patch_hairdt.py | 649cc396 | d114a34e | dt del cloth del player senza time-scale (0x5bbec2, .tufx+0x700) | sì |
| 34 | sap | work/ws/b265_sap/patch_sap3000.py | d114a34e | 981ea0b3 | SweepAndPrune 1000/200 → 3000/500 come TU (0x5be3a7/ac/c4) | sì |
| 35 | cs2 | work/ws/b269_crash/camerashakes_guard2.py | 981ea0b3 | **2b7ee74c** | seconda guardia camerashakes 0x5ee9bc, cave 0x83dfa8 | sì |

Esiti macchina: `rebuild/catena/esito_catena.tsv`, `rebuild/solo/esito_solo.tsv`, log completi `rebuild/*/rebuild_*.log`.
Gli exe dei rami laterali (nullret_cs/gold B231, b157_wall_nat, tuload_flag11, s8nh, logb/c/d…) NON sono nella catena.

## File prodotti
- `PATCHES.tsv`: 212 intervalli contigui di byte diversi 56d1ce2d→2b7ee74c nelle sezioni originali + header (VA, offset file, lunghezza,
  sezione, byte originali/nuovi troncati a 32 B, stadio responsabile = ultimo stadio che ha scritto quei byte), più una riga per ciascuna
  delle 4 sezioni nuove (.tuload, .tuext, .tufx, .tufin: VA, dimensione, md5, stadi che vi scrivono). 25 014 byte diversi in tutto.
- `deltas/NN_stadio.json`: differenza byte esatta di ogni anello (offset file → byte nuovi), con md5 di ingresso/uscita.
- `tools/chain.py` (definizione catena), `tools/chain_diff.py` (verifica md5 + delta + PATCHES.tsv), `tools/rebuild.py` (ricostruzione),
  `tools/patch_nullfilter.py` (stadio s8n ricostruito), `tools/run_gates.py` (gate su Windows), `tools/freespace.py` (spazio libero), `tools/lineage.py`.
- `rebuild/src/`: copie degli script con percorsi `/Users/andrearicci/Downloads/...` → `C:/tru-port` e `C:/Xenia-SteveRepack`; i `sys.path` puntano
  alle copie. Originali mai modificati (verificato: nessun file nuovo fuori da exe_chain; cartella del gioco solo letta).
- Spazio: `rebuild/solo` 222 MB, `rebuild/catena` 179 MB (exe intermedi; si possono eliminare, si rigenerano in ~1 min ciascuno).

Comandi (PowerShell o Git Bash, da `C:\tru-port\work\ws\exe_chain`):
```
python -I -B tools/rebuild.py catena     # 56d1ce2d -> 2b7ee74c, ~1 min
python -I -B tools/rebuild.py solo       # ogni stadio sul suo ingresso di riferimento
python -I -B tools/chain_diff.py         # rigenera deltas/ e PATCHES.tsv
python -I -B tools/run_gates.py nat|fin [EXE]
```
Sempre `-B` (gli script importano moduli dagli originali in sola lettura: niente `__pycache__`). Serve clang (`C:\Program Files\LLVM\bin`,
aggiunto al PATH da rebuild.py) per tutti gli stadi che usano `asmx.py` (s1…s8, log*, fx*, keep, gp7, fin, dtpg, chunk, hairdt).

## Aggiungere un NUOVO stadio sopra 2b7ee74c
1. **Script** `patch_xxx.py IN.exe OUT.exe` sul modello di `work/ws/b247_chunk/patch_chunk.py`: `assert md5(IN) == '2b7ee74c…'`; mappa VA→offset
   dalle sezioni; `pat(va, old, new)` che asserisce i byte originali e la stessa lunghezza; codice in Intel syntax assemblato con
   `asmx.assemble(ASM, CODE_VA, SYMS)` (clang i386); manifest `OUT.json` (siti, etichette, dati); nome `tru_s8n_sap_cs2_<nuovo>_cs.exe`.
   Poi aggiungere la riga in `tools/chain.py` e verificare con `rebuild.py catena`.
2. **Dove mettere il codice** (`freespace_2b7ee74c.txt`, corse di zeri senza riferimenti assoluti né call/jmp rel32 verso di esse):
   - **.tufin 0x1242d0a..0x1243000 (758 B, RWX)**: subito dopo il codice chunk (0x1242c80, 138 B). È la scelta naturale (stessa logica di chunk/dtpg).
   - .tufin 0x12420f1..0x1242200 (271 B) è senza riferimenti ma sta nella zona dati di fin (0..0x200): evitarla.
   - .tuext ha corse libere tra le tabelle estese (es. 0x123bcaf..0x123c000 849 B, 0x1237e03..0x1238000 509 B, 0x123d9b8..0x123db00 328 B,
     0x123f785..0x123f800 123 B): sono code di tabelle/dati di s1–s8, usarle solo dopo averne verificato il layout in RAPPORTO_exe_build.txt.
     La grande corsa 0x123f9e2..0x1240e00 NON è libera (ring dei logger animazioni/condizioni/sonda, scritti a runtime).
   - .tufx: la coda 0x1241bac..0x1242000 contiene la keep-list a .tufx+0xe00: non è libera per intero.
   - .text: la coda storica 0x83dc5f..0x83e000 è **piena** (wall, dlc2data, fmod×2, lighttex, soundplex, cs, cs2, reticle fino a 0x83dffc).
   - .shad 0x10d9e0e..0x10d9f00 (242 B, RX, prima della cave g0): non scrivibile, solo codice.
   - Alternativa pulita: **nuova sezione** come fin/fx (`patch_fin.py` righe 36–47): c'è posto nell'header (10 sezioni, tabella finisce a
     0x388, zeri fino a 0x1000); nuova VA 0x1243000, raw 0x62d000 (= fine file), aggiornare NumberOfSections e SizeOfImage.
3. **Interruttori**: le guardie recenti sono condizionate da bit della maschera fin a 0x1242020 (oggi 0x3f: bit0–4 fin F1–F5, bit5 chunk):
   un nuovo stadio può usare bit6 (0x40) per poterlo spegnere a runtime. Per agganciarsi al frame del player si concatena `hook_lara`
   (0x123e044 → gp7 0x1241800 → fx2 → fx → shadow_update 0x123df0c), mai sostituirlo.
4. **Gate di emulazione** (modello: `b269_crash/emu_guard2.py`, `b265_sap/emu_sapctor.py` per i semplici; `b247_chunk/emu_chunk.py`,
   `b246_crash/emu_dtpg.py` per i completi): unicorn `UC_MODE_32`, si mappa 0x400000 e si copia `.text` (o tutte le sezioni) dal file
   (`fmod_init_guard.va2off`), si mappano stack e memoria finta (o la memoria di un minidump), si mette un indirizzo sentinella come
   ritorno e si esegue `emu_start(sito, sentinella)` su ORIG e su NEW confrontando eax/esp/memoria scritta e le chiamate (hook
   `UC_HOOK_CODE`). I gate completi controllano anche: NEW riproducibile da ORIG + script, byte cambiati solo nei siti dichiarati,
   decodifica capstone del codice nuovo. Aggiungere il gate in `tools/run_gates.py` (liste GATES/SINGLE).

## I gate girano su Windows?
- `work/ws/b253_catena/run_gates_b253.sh` **no, così com'è**: è zsh (`#!/bin/zsh`, `typeset -A`), con `cd /Users/...` e il venv Mac; zsh qui non c'è.
  Chiama solo script Python (`emu_att`, `emu_att3`, `emu_g0`, `b250_verifica/emu_fx_local`, `emu_fx2`, `emu_keep`, `emu_b245`, `emu_dmg`,
  `b250_verifica/emu_fin_local`, `emu_dtpg`, `emu_chunk`) con argomenti `ORIG PAT`. Sostituito da `tools/run_gates.py` (stesse coppie, + sap e cs2).
- Esito su Windows (`gates/nat/ESITO.txt`, coppie naturali): att PASS 6, att3 PASS 9, g0 PASS 30, fx PASS 43, fx2 PASS 18, keep PASS 15,
  b245 PASS 32, dmg PASS 13, fin PASS 59, sap 3000 box prima di NULL, cs2 4 casi ok ret. **dtpg e chunk NON eseguibili**: mancano i dump
  `work/crash/B245_lotta/tru.exe.7852.dmp` e `work/crash/B246_finisher/live_t43.dmp`; anche `b262_hairdump/emu_hairdt.py` richiede i
  dump `hair_*.dmp` (B262_hair contiene solo keydump.log).
- Modo `fin` (ingresso dello stadio → 2b7ee74c, `gates/fin/`): att/att3/g0 PASS; fx, fx2, keep, b245, dmg, fin danno FAIL **solo nei controlli
  strutturali** (riproducibilità NEW = ORIG+script, "byte cambiati solo nei siti", hook_lara rediretto dagli stadi successivi), con gli stessi
  FAIL dei log Mac `b253_catena/logs_ref/*_fin.txt` (fatti contro chunk); differenza in più: b245 "codice fx/fx2/keep in .tufx invariati" ora
  FAIL perché hairdt ha scritto in .tufx+0x700 (atteso). I controlli funzionali in emulazione sono tutti OK.

**Nota (scrittura fuori da exe_chain):** al primo giro di `run_gates.py fin` il gate `emu_fin_local` ha rilanciato `patch_fin.py` con
`python -I` senza `-B`, e Python ha scritto 3 file di cache bytecode in `C:\tru-port\tools\__pycache__\` (`archive`, `bigfile`,
`names.cpython-312.pyc`, ore 15:12). Sono solo cache (nessun effetto sul contenuto). Non li ho cancellati. Corretto: ora `run_gates.py`
aggiunge `-B` nelle copie; un nuovo giro completo non ha scritto più nulla.

## Incertezze residue
- s8n: lo script è ricostruito dai byte (non è il sorgente originale); semantica dedotta dal disassemblato + MEMORIA (guardie <0x10000).
- Nessuna prova runtime (offline): la ricostruzione dimostra solo l'identità dei byte, non il comportamento in gioco.
- Riproduzione dipendente da clang: ottenuta con clang 23.1.5; un'altra versione potrebbe codificare diversamente qualche istruzione.
- "Spazio libero" = zeri senza riferimenti statici: aree scritte solo tramite registro+offset non sono rilevabili così; controllare il layout dichiarato dagli script.
