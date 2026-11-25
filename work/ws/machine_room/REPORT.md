# machine_room (DLC2): muro trasparente e colonne di goo incomplete (18/11 sera)

Segnalazione di Andrea: davanti alla cupola (riferimento video Xbox: zona chiusa da roccia) sul PC il muro è sempre trasparente ma non si
attraversa; le colonne di goo non hanno la parte alta. Dump `work/live/20261118_1737` m1 (muro), m2 (colonne); Lara (-2503, 6780, -13026).

## Verificato (PC B273 contro Xbox pack11)
- Render del terreno = `streamgroups/dlc2_machine_room_machine_room_all.drm` (Xbox estratto in `work/dlc2/xbox/streamgroups__…`).
  12 sezioni terreno: triangoli, lotti, vertici, record A (nodi) e Y (lotti) identici all'Xbox (285 lotti nella zona della cupola).
- Materiali della zona (23304, 25520, 23152, 24308, 26267…) usati anche fuori zona (rocce visibili): non spiegano il difetto.
  Lightmap DXT1 della zona presenti su entrambe.
- Scostamento di unità machine_room: (−1414,8, −20123,5, −37922,1). Terrain group (sez. 63, 29 record da 0x50): posizioni = mondo,
  nessuna parola anomala; blocchi per gruppo in DTP 25392 +0x221b0 (0x30 B): prima parola tenuta grezza = come nei livelli PC nativi
  (verificato su 54 livelli base: `00fc05e0 02000000` ecc.).
- Gruppo 23 (uid 696) a (−2363, 7936, −13029), davanti a Lara: ha collisione (mesh sez. 62) ma **nessun render di terreno**
  (lo streamgroup lega i render solo ai gruppi 0 e 13–22). Vicino: `reveal_object` uid 10179 (−2361, 7237, −13039),
  `dlc_fx_goo_column_displace` uid 10472, ponte lungo 11673.
- Istanze vive: niente `dlc2_uo_machine_debris` / `enemybreakwall` (nessuna intro in machine_room).

## Aperto
- Chi disegna, sull'Xbox, il guscio sopra il gruppo 23 (oggetto collegato? lotto del terreno principale escluso a runtime?).
- Colonne di goo (12 `dlc_fx_goo_column_displace` + 7 `_s`): parte alta mancante, da analizzare (FX).
- Strumento utile: cattura delle chiamate D3D9 (apitrace) per vedere se i lotti vengono disegnati. Richiede installazione (sì di Andrea).

## CAUSA del muro trasparente (18/11 sera) → B275_tgflag
- Blocchi dati dei terrain group (DTP 25392 +0x221b0, 0x30 B ciascuno), parola +0x24 = maschera del gruppo: 1 per i gruppi normali,
  **0x4000 / 0x2000 / 0x1000 per i tre livelli della struttura centrale** (gruppi 13/14/15 = render 26693/26691/26692).
  Gruppo 14: Xbox 0x00002000, PC `00002000` (byte copiati) = 0x00200000 → quel livello non viene mai disegnato, la sua collisione sì.
- Linee di vista da Lara (dump m1): davanti c'è la struttura centrale (26692 visibile = «cupola»); manca il livello 26691.
- Scansione `tgflag_scan.py` su 190 DRM DLC (DLC1+DLC2) contro pack10/11: **unico caso** (altri 4 risultati = blocchi diversi, coppie u16 corrette).
- Correzione `tgflag_fix.py` → `out_b275_tgflag` → **B275_tgflag-2f507e2c0f35** (libgate PASS). INSTALLATA 18/11 (backup work/backup_gioco/20261118_prima_di_B275).
- Colonne di goo: oracolo emettitori FX (b268) su dlc_fx_goo_column_displace(_sml) e machine_column_core: 0 disaccordi. Ipotesi:
  la parte alta mancante può appartenere al livello 26691 invisibile (da verificare in gioco con B275).

## Prova B275 (18/11 sera): NON risolto. Dump `work/live/20261118_1811` (Lara contro il muro, (−2513, 6031, −13026))
- Raggi di collisione emulati (0x493330, `emu_ray.py`/`emu_wall.py`): il muro invisibile è un **rettangolo di collisione** del terrain
  group 4 (uid 664, statico, mesh 0x1832e120): piano y = 4824,5, x −3036…−1757, z −13640…−12066 (una «porta»).
- Posizioni a runtime di tutti i 29 terrain group = statiche (nessun gruppo spostato).
- Render (tutte le 12 sezioni terreno dello streamgroup, `raygrid.py`, `render.py`): nessun triangolo vicino alla porta né in tutta la
  facciata y 4000–6500 dove c'è collisione; la «cupola» è il livello 26692 (y < 4000). Nessun vertice di nessuno streamgroup DLC2
  coincide con la porta. Nessuna intro DLC2 vicino alla porta senza istanza viva.
- Quindi i dati statici (uguali all'Xbox) non contengono roccia davanti alla porta: o la roccia Xbox viene da qualcosa di dinamico non
  ancora individuato (logica dei livelli 0x1000/0x2000/0x4000 della struttura), o il riferimento Xbox è un altro punto.
- B275 resta valida: corregge un valore realmente diverso dall'Xbox.

## Cattura apitrace (19/11 notte, gioco avviato da Claude su richiesta di Andrea, «Resume»)
- `tools/win_diag/APITRACE.bat` non basta: il gioco carica d3d9.dll dinamicamente (nessuna importazione statica) → serve
  `inject.exe --mhook -D lib\wrappers\d3d9.dll tru.exe` (TRACE_FILE=…). Controllo del gioco: `tools/win_diag/GameCtl.cs` (screenshot, tasti
  SendInput a scancode, mouse).
- Traccia `work/apitrace/tru_machine.trace` (1,69 GB, 5030 fotogrammi, 28,8 M chiamate). Ultimo fotogramma 28783852–28795431, 2377 draw.
  Rigioco `d3dretrace -S <intervallo>/draw` → `work/apitrace/snap/` (2250 immagini): l'immagine finale coincide con il gioco.
- Nella zona del varco sotto l'arco: l'arco di roccia viene disegnato (≈28786757), poi dentro solo la cupola (livello 26692) e luce/post.
  **Nessun disegno copre il varco**: il PC disegna esattamente ciò che c'è nei dati (che sono uguali all'Xbox); nessuno streamgroup mancante
  (l'unico nome extra nel livello, `dlc2_mr_cube`, è una cubemap).
- Conclusione provvisoria: il rettangolo di collisione invisibile è con buona probabilità **voluto** (blocco del varco finché la struttura
  non sale); il fotogramma Xbox del video non è verificabile come stesso punto.

## 19/11 pomeriggio: test B277 in gioco + analisi struttura mobile
- Test autonomo (B277 installata, Resume): varco ancora trasparente, Lara si ferma sulla soglia (`work/live/b277_test/`).
- Andrea: la struttura è mobile ed è già sbloccata; rispetto all'Xbox manca un pezzo; colonne di liquido blu incomplete.
- Exe PC: `NtTerrainGroup::SetEnabled` (0x4ad130 -> 0x5c2440) mette i bit 0x04|0x08 nel primo byte del record del gruppo
  (DTP 25392 +0x221b0 + 0x30*i) = SPENTO; membro script {u16 unità, u32 indice} risolto da 0x4aaca0 (unità 116 = machine_room).
- Dump 18/11 18:11 (`tg_runtime.py`): spenti 1,2,4,5,6,9,10,11,17,18,20,21,22,23,24,26,27; accesi 0,3,7,8,12,13,14,15,16,19,25
  (i tre livelli 12/13/14 accesi). Strutture TerrainGroup 0x50: +0x24 indice, +0x28 uid, +0x30 record, +0x38 mesh collisione.
- Riferimenti {116, indice} negli script (25393 ne ha 27, + altri): 160 su 160 convertiti come l'Xbox (`tgref_scan.log`).
- Maschere +0x24: nei 82 livelli del gioco base solo 0/1; 0x1000/0x2000/0x4000 solo DLC2. Nessuno script usa quei valori.
- V-M4 su B277 (`work/ws/vm4/vm4_list.py`): 432 casi, solo materiali thrall/dopple (PS 655 / VS 444), niente machine_room né colonne.
- Aperto: quale pezzo manca (riferimento Xbox necessario); passi FX del fork (fxrec / fxrecread / fxrelayout) non ancora verificati
  sulle colonne.

## 19/11 sera — regole FX del fork di Lukas sulle colonne (offline, sola lettura)
- Oggetti della stanza (intro Xbox): dlc_fx_goo_column_displace x12, dlc_fx_goo_machine_column_core, dlc2_uo_machine_column,
  dlc2_uo_energy_pillar_machine x10, goo_tube_*, goo_machine(_a/_b/_c), lightray_machine x3.
- `lv90_scan.py` (DTP [Level+0x90]+0x1c tutto s32): 0 difetti in tutte le unit (machine_room 25390: 37.490 s32).
- `fxread_scan.py` (12 offset dei record 0x17c letti da 0x543f70): prova base 64.080 ok / 0 contro; baseline 24.115 ok, 5 diverse
  solo in co_dlc_knight_thrall (valore diverso, non ordine di byte).
- `fx20_block.py` (blocco puntato da +0x20 delle FX): nessuna parola fuori classe; la +0xfc raw di column_core e' normale (base raw 11/11).
- `relayout_scan.py` / `relayout_proof.py`: tabella di record a passo 0x24 lasciata dal convertitore in 7 DTP DLC2 (torce x3,
  cine_object, goo_cannonball, goo_upcolumn_pit, bloom); prova base 25/25. upcolumn_pit e' in goo_room, non in machine_room.
  Correzione pronta: `work/ws/b278_relayout/` (6 DTP, bloom escluso).
- Esito: nessun difetto nei dati FX delle colonne di machine_room con queste regole. Pezzo mancante e colonne ancora senza causa.

## 20/11 — curve u16[64] dei DTP unit rotte (unitcurve) → B279
- Andrea: la sala resta rotta con B278 (blocca la partita).
- `lukas_check/inv/unitcurve_scan.py` su B278: 283 parole di curva convertite come u32 (o lasciate grezze) invece che u16:
  **machine_room 243 parole = 10 curve** (root/+6c/+2f8/+50, +654, +6b4, +6b8/+50, +714 x2, +774, +7d4, +834), ceremony_room 29,
  DLC1 dungeon 6, caverns 5. Sul PC le rampe (monotone sull'Xbox) diventano a dente di sega.
- Prova base `curve_proof.py`: 435 rampe vere su 435 = s16 (u16 scambiati uno a uno), 0 contro.
- `work/ws/b279_unitcurve/b279_fix.py` → **B279_unitcurve-3416b69f1247** (libgate PASS). Chi legge le curve: non ancora identificato.

## 20/11 pomeriggio — dump con la struttura sbloccata (`work/live/20261120_machine/`, B279)
- Video Xbox (storyboard YouTube BEXSIHxN3ts, 25:30-26:10): dopo la cutscene degli interruttori la goo blu scende dal tubo sotto la
  cupola; a ~26:10 Lara davanti alla struttura centrale: **l'arco e' chiuso da un blocco pieno**. PC: arco vuoto, collisione presente.
- `intro_vs_live.py`: tutte le intro di machine_room vive salvo 10 `dlc2_uo_energy_pillar_machine`, 3 `dlc_fx_lightray_machine`,
  1 `machine_debris` (+ thrall). Oggetti caricati (tracker 0xdb7400 stato 2), non nel salvataggio: mai nati.
- I 3 `dlc2_uo_punch_switch` (uid 11692-11694) hanno script 25421/25422/25423 che contengono gli uid dei pilastri + 1 raggio ciascuno;
  il dispatcher 10184 (script 22898) il debris. Record di riferimento, simboli (+480 DLC), uid: = Xbox. `uidref_scan.py`.
- `column_rays.py`: in posa di riposo le mesh 25552 e 25554 di `dlc2_uo_machine_column` riempiono il varco (y fino a 5410 davanti al
  piano di collisione 4824). Mesh/ossa/skin map = Xbox; ogni mesh segue l'osso 2.
- Animazioni della colonna (`anim_cmp.py`, 19/19 = Xbox): 6482 iniziale (osso1 -11694, osso3 +19911), 6487/6488/6489 = salita a ogni
  interruttore (-11694 -> -7269 -> -2528 -> +2212; nella 6489 osso3 19911 -> 0), 6490 discesa finale.
- Ossa nei dump (18/11 18:11 e 20/11, identici): istanza principale 11688 = stato iniziale; figlia 0 (mesh 25552, quella del blocco)
  = dopo il 2o interruttore (-2528, osso3 +19911); figlie 1 e 2 = stato finale (+2212, osso3 0). **Alla figlia 0 manca l'ultima
  animazione** e con lo stesso passo mancano pilastri e raggi.
- Esclusi: uber (la colonna non ne ha), script 25504 e catene superclassi/vtableSize = Xbox (`super_chain.py`; 45 classi base hanno
  vtableSize diversa Xbox/PC ma nessuna nella catena), 134/134 chiamate a funzione degli script degli interruttori = stessa funzione
  (`callnames.py`). Causa ancora aperta: esecuzione dello script / motore (TU), non dati convertiti visibili.

## 20/11 sera — sequenza dal vivo e MarkUp della colonna → B280
- Andrea: interruttori colpiti e poi avanti senza ricaricare. Dump 18/11 17:11 (prima): tutte le istanze della colonna allo stato
  iniziale; 17:38 (dopo): figlie 1-2 finali, figlia 0 al 2o stadio. Guasto dal vivo, non nel salva/ricarica.
- `INSTANCE_IntroduceSavedInstance` retail vs TU (decompilato): stessa logica (solo allocatore inline). Scartata.
- Modelli della colonna: `model_fix` / `model_point_fix` = 0 cambi. Tabella header +0x54/+0x58 = record **MarkUp** 0x5c B
  (ENGINE.md del fork: +0x2e id, +0x30 osso, +0x33 tipo, +0x34 pos). `model58_cmp.py`: base 83 modelli/297 record: +0x2c s16
  (id rimappato), +0x30 s16b2/raw, +0x34..+0x54 s32. `markup_scan.py`: 14 parole fuori regola in 3 modelli: machine_column 25549
  (5 id letti 0 + float -1.0 a +0x48 del record 6; modello del livello 1, figlia 0), DLC1 pillar_of_doom_a 20472 (3), _b 20478 (5).
- `work/ws/b280_markup/b280_fix.py` → **B280_markup-e5b7d9ee8ed9** (libgate PASS, markup_scan 0 difetti). Gli id non compaiono negli
  script: effetto atteso sugli appigli del livello 1 (piu' MarkUp con id 0). Non spiega da solo l'animazione mancante.

## 20/11 sera — copia del salvataggio con machine_room azzerata ("tornare indietro")
- B279/B280 provate da Andrea: nessun cambiamento (stato gia' scritto nel salvataggio).
- Formato salvataggio dal fork (ENGINE.md 6.2-6.4, trusave_info/diff), lettore riscritto `trusave.py` (CRC-32/BZIP2 verificati sui due
  salvataggi). `mr_save_items.py`: Autosave = 177 blocchi tipo 4 della unit 116, 15 dead bits, 47 stickies (interruttori 11692=0,
  11693=1, 11694=1); "Savegame 1" (goo_room, 7/11) = nessun dato di machine_room (solo lo sticky del dispatcher 11425, gia' impostato).
- `trusave_reset.py` → `save_reset/Savegame 2.TRUSave`: tolti 174 blocchi (tenuti i 3 ma_rw_artifact raccolti), 15 dead bits,
  46 stickies (tenuto il 342 gia' presente prima), checkpoint 10204 (vicino all'arco) -> 11696 (ingresso in basso), CRC ricalcolati
  e verificati, nessun byte cambiato fuori dalle zone previste. Non copiato nella cartella dei salvataggi (serve il si').
- 20/11 17:02 prova di Savegame 2 (TruLive `work/live/20261120_1702`, 4 dump): sala azzerata (interruttori, colonna, pistoni allo stato
  iniziale), primo interruttore OK, poi muro invisibile verso la piattaforma rotonda. Rispetto alla visita originale (dump 18/11 17:11)
  stessi oggetti + 4 triggervolume 11757-11760 ancora vivi; terrain group diversi: 4 e 9 accesi (orig. spenti), 10 spento (orig. acceso).
  Lo stato iniziale della sala lo imposta l'ingresso dal corridoio, saltato ricomparendo al checkpoint 11696.
- `trusave_reset.py --cp-unit`: **Savegame 3** = stessa sala azzerata, ricomparsa nel corridoio dlc2_hall_goo_machine (unit 115,
  checkpoint 11596, il piu' vicino all'ingresso basso della sala, stessa quota). CRC ok. Non copiato (serve il si').
- Savegame 3 (dal corridoio): stesso muro (trigger 11757-11760 gestiti dal dispatcher 11736, script 25465, mai scattati; TG 4/9 accesi).
- **Savegame 4 (ibrido)**: Autosave originale meno i blocchi di colonna 11688 e interruttori 11692-11694 + 3 stickies degli interruttori,
  checkpoint 11696. Andrea: **la struttura compare completa** (la colonna rinasce e lo script la porta subito allo stato finale in base
  al progresso salvato). Savegame 5 = stesso, checkpoint originale 10204. Sblocca la partita; la causa del guasto dal vivo al terzo
  interruttore (figlia 0 ferma, pilastri non nati) resta aperta per chi gioca la sala da zero.
- Savegame 7 (copiati nella parte 0 anche 8 byte di stato e lo stato 0002->0001): **crash** al caricamento.
- **Savegame 8** (`trusave_colpatch.py --min`: solo i 2 byte dell'indice di animazione della parte 0, 2 -> 3 = anim 6485): **funziona**,
  Andrea prosegue oltre la struttura (20/11 sera). In alto manca uno yeti: le intro yeti 12192 / 12193 (quota -8220 / -8538) e 11770 /
  11771 non sono ne' morte ne' salvate = nascono da script; probabilmente la stessa catena dopo il 3o interruttore che non e' partita
  (pilastri, raggi, debris). Causa del guasto dal vivo ancora aperta.
