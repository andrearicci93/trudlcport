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
