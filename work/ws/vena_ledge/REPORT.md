# Traccia V — vena scendendo dal ledge (A1) — sessione 14/11

Stato: **causa non dimostrata; ipotesi principale H-SP; serve una prova mirata (sotto).** Tutto offline, gioco mai avviato.

## 1. Correzione di lettura della registrazione del 7/11b (verificato)

Gli assi di `X` (TruLive, `le+0x20/+0x24/+0x28`) sono **(x, y, quota)**: la quota è `le+0x28`, non `le+0x24`.
Prove: in corsa e in shimmy (88–90 s) variano i primi due e il terzo resta −5460,68; i record dei ledge (tipo 1) hanno
estensione nulla sul terzo asse, le vene (tipo 22) si estendono proprio sul terzo (`v2_markup_dump.py`).
TruLive chiama «z» `le+0x20` (riga `S`, ultima colonna) e calcola la «velocità orizzontale» su `+0x24/+0x28`: è sbagliato
(il trigger «> 2500 u/s orizzontale» in realtà scatta anche in caduta).

Conseguenze:
- Lo «scatto orizzontale di 10.000 unità in 1,7 s» del 7/11 è una **caduta libera verticale**: x e y fermi, quota da −5460 a
  −15331 con incrementi che crescono linearmente (gravità costante). Poi `lflags 0` a 104 s e ricomparsa al checkpoint di 58 s
  a 107 s: morte e ricaricamento. L'ipotesi V0 («parametro di moto fuori scala») non è sostenuta da questo episodio.
- A19 («teletrasporto» tra ledge con l'ombra) resta aperto ma **non** coincide con questo episodio.

## 2. Geometria (verificato su registrazione + dump)

Episodi (`v1_episodi.py`): Lara sale un pozzo alternando vene (`24c8000`) e ledge (`65c0000`/`6580000`) da quota −14.976
a −5.460. Caso fallito: shimmy sul ledge `196ae1c0` (da (16074,−4672) a (19553,−3724), quota −4967) fino a
x=16235,7, appesa ferma 5 s **senza ombra** (righe PC 1,0/1,0; contatore che si ricarica fino a 1000), nessun candidato;
al distacco ombra ON (1,2/0,3) e stato `0x25d8000` = caduta.

Sotto l'estremo sinistro del ledge c'è la vena `196acd80` (record `0x1838bb50`): segmento 0 verticale in x=16074,
y=−4528, quota da −5607 a −8089 (poi tratto corto a y=−4212). Distanza 3D 295, sommità 147 sotto Lara.

Agganci riusciti da appesa (`v3_geometria.py`): 7 su 7 la vena candidata è **interamente sopra** Lara (estremo
inferiore da +421 a +1126). Nella sessione non è mai stata proposta una vena sotto Lara.

Riferimento Xbox (walkthrough, non verificato in gioco): la mossa esiste, es. Stella, Refinery: «Climb to the right as
far as possible. Then drop to grab the rock vein below. Slide down and drop to grab the handhold below the vein.»;
«hanging on the next square support column with a rock vein below her. Drop and grab the vein» (tombraiders.net,
laras_shadow.html; tombraiderchronicles.com, laras-shadow/walkthrough/level01.html).

## 3. Codice (verificato dal subagente, dettagli in `sel/`)

- Il candidato `game+0xa64` da appeso è scritto da `FUN_00770240` (0x7702df), via azione 0x1a7 → `0x7296c0(S, modo=game+0xb00)`.
  Accettazione = lista dei tipi del modo (`0x7232e0`, DTP 20212) ∩ arco balistico del modo che interseca il segmento.
  Nessun test esplicito «markup sotto: scarta».
- Ricerca TU `0x8241e520` identica alla base Xbox (solo rilocazioni); handler TU di 0x1a7 solo immediati; tutte le 19 clausole
  tipo 22/23 della SPEC risultano nell'exe installato. Unica differenza non portata: tipo velocità 5 in `0x76ffc0`
  (TU 0x82452870), non usato da nessun modo dell'857 nel dump.
- Liste dei modi nel DTP 20212 Xbox identiche al PC; blocco 18 (tipo 22) identico con le regole di swap.
- In caduta libera (stato 0x26a, padre 0x26c) non gira alcuna ricerca né su PC né su TU. Lo stato 0x439 (modo 107, ammette
  il 22) si raggiunge da 0x40f/0x42c/0x43d solo con la condizione 608 già vera, cioè con la vena già candidata.
- Modi: quelli dei salti da ledge (79–91) non ammettono il 22; lo ammettono 45, 56, 107 e i modi con lista di esclusione vuota.
  La famiglia di stati ombra 0x40e–0x43f ha modo 44 (non ammette il 22) salvo 0x427/0x428 (modo 45) e 0x439 (107).

## 4. Ipotesi

| # | Ipotesi | Stato |
|---|---|---|
| H-SP | Su Xbox la vena sotto diventa candidata solo **tenendo l'ombra da appesa** (stato ombra con modo che ammette il 22, poi discesa 0x439). Nel caso fallito l'ombra è stata premuta solo al distacco: il PC si è comportato come il TU | da provare (prova sotto) |
| H-POS | Lara non era sulla verticale della vena (fermata a 161 unità dall'estremo del ledge) e l'arco della discesa non interseca il segmento | da provare (stessa prova) |
| H-GRAFO | Transizione hang+ombra → stato con modo 45/107 assente o diversa sul PC per una condizione TU stub (V3) | offline, se la prova smentisce H-SP |
| V0 | moto fuori scala | non sostenuta dal 7/11b |
| V1 | dati del record della vena | non sostenuta: record equivalente a una vena che funziona |
| V2 | ricerca cambiata nel TU | smentita sul codice (identica) |

## 5. Prova mirata per Andrea (una sola sessione, ~10 minuti)

Strumento: `tools\win_diag\LIVE.bat` (registra già input ogni 25 ms e memoria di game/Lara ogni 50 ms: candidato, modo, stato).
1. Doppio clic su LIVE.bat, poi avvia il gioco e carica DLC2 nel punto del pozzo (checkpoint in basso), risali come il 7/11.
2. Sul ledge in alto, shimmy **a sinistra fino in fondo** (finché Lara non si ferma da sola).
3. Premi `+` (marcatore). **Tieni premuta l'ombra mentre sei appesa**, senza lasciare: guarda la finestra di TruLive per 2–3 s
   (riga di stato ogni secondo: `vena(tipo 22) trovata=SI` o `no`; l'ombra dura circa 5 s, non aspettare oltre). Poi, sempre tenendo l'ombra, lasciati cadere dal ledge.
4. Se muori: ripeti 2–3 con una variante: ombra tenuta + salto all'indietro (direzione opposta al muro + salto). Prima di ogni
   tentativo premi `+`.
5. Dimmi per ogni tentativo: cosa vedi (Lara afferra la vena? cade?) e cosa diceva TruLive su «vena trovata».

Esiti attesi: «trovata=SI» da appesa con ombra e aggancio dopo la discesa → H-SP confermata, nessun difetto del port (va solo
scritto nelle istruzioni). «trovata=no» anche con ombra tenuta ed esattamente all'estremo → difetto vero: dalla registrazione si
leggono modo e stato e si passa a H-GRAFO offline.

## 6. File

`v1_episodi.py` (episodi per stato), `v2_markup_dump.py` (markup nel dump vicino al punto), `v3_geometria.py` (geometria
candidati), `sel/` (analisi del selettore: script e `stati_modo.txt`, `diff_collettore.txt`).

## 7. Prova del 18/11 (registrazione `work/live/20261118_1124`, gioco ancora aperto durante l'analisi)

Lette con `v1_episodi.py` e il registro grezzo (game+0xa64/+0xc94/+0xb00, Lara+0x1fc, campioni ogni 25–50 ms).
- Stesso punto del 7/11: appesa al ledge `196ae1c0` in (16235,7; −4410,7; −5460,7) da 101,8 a 127,3 s, modo 87, candidato 0.
- Ingressi (tastiera, nessun pad): nessun tasto premuto durante l'appeso fino a 126,96 s; gioco in secondo piano 106,6–116,5 s.
  LShift (ombra) a 126,96 s, LShift+LCtrl a 127,29 s, distacco a 127,33 s. **Ombra attiva da appesa solo 0,33 s**, non 2–3 s.
  In quei 0,33 s modo resta 87 e candidato 0. Al distacco: modo 44, lflags `25d8020`, caduta lungo la vena (screenshot 4), morte
  a 143,6 s, ricomparsa al checkpoint a 146,8 s. Nessun altro tentativo dopo (fino a 397 s fermo al checkpoint).
- H-SP quindi **non ancora provata** (ombra troppo breve); dato nuovo: con l'ombra appena premuta lo stato da appesa non cambia modo.
- **Correzione al §3**: con modo 87 (salto da ledge) il gioco ha accettato candidati tipo 22 (70,9 s, 83,2 s; Mk 22/1):
  o `game+0xb00` non è il modo passato alla ricerca nel momento della scelta, o la lista del modo 87 ammette il 22. Da ricontrollare.
- Lo screenshot conferma la posizione: Lara cade lungo la fessura della vena (H-POS poco probabile).
- Dump `dump_..._2_m4.dmp` preso a 127,9 s durante la caduta (stato di Lara leggibile offline).

### 7bis. Prova 2 del 18/11 (stessa registrazione)
- **A (546,9–555,5 s)**: appesa nello stesso punto (16235,7; −4410,7; −5460,7), LShift tenuto da 552,33 a 555,45 s (3,1 s; energia
  ombra da 1000 a 309, riga PC a1 = 1,2). Per tutto l'appeso modo 87 e candidato 0. LShift+LCtrl a 555,55 s → modo 44,
  `25d8000`, caduta e morte (565,8 s).
- **B (608,7–614,6 s)**: appesa nello stesso punto, nessuna ombra, solo LCtrl a 614,57 s → modo 44, caduta di 9.945 unità, morte.
- Esito: **H-SP smentita** (anche con l'ombra tenuta 3 s da appesa la vena sotto non diventa candidata). Il distacco porta al modo 44
  con o senza ombra: il 44 non è un modo «dell'ombra» ma quello della caduta dal ledge. Nessuna ricerca trova la vena né da appesa
  né in caduta. Il prossimo passo è **H-GRAFO offline**: cosa fa il TU sull'azione «lasciati cadere» da appesa con una vena sotto
  (transizione dallo stato di appeso, ricerca verso il basso, modo usato), confrontato con il PC.

## 8. H-GRAFO offline (18/11): il difetto non c'è, è la posizione (H-POS, nuova lettura)

- Grafo DTP 20212: da appesa (famiglia 0x1b2/0x1b3), «lasciati cadere» = transizione 849 (c263(0)) → 0x417 (modo 44, azione di
  ricerca 0x1a7) → 0x438, che con candidato tipo 22 (c262(608)) va a 0x43c. Il percorso «cadi e afferra la vena» quindi esiste ed
  è lo stesso su Xbox e PC (stessi dati).
- Modo 44 nel dump m7 ha tabella prese `(1), (3, 505.69)`: l'id 3 è proprio quello del blocco vene (P+0xa0, ids [3]); il modo 87
  ha (1),(3) e infatti accetta le vene. La correzione del §3 è confermata: i «modi senza 22» del 14/11 erano letti male.
- Dati confrontati con l'Xbox (DTP 20212 di doppelganger_casual): blocchi parametri 1–19 (+0x98..+0x9e) e i 111 record dei modi
  identici a meno della conversione d'endianness. Il collettore TU (0x823fa8c0) ha in più solo un filtro di distanza (scarta di
  più, non di meno): non spiega il caso.
- **Geometria vera del ledge `196ae1c0`** (polilinea di 6 punti, dump m7): l'ultimo tratto p4→p5 è la faccia x=16074,5 della
  colonna, y da −4671,7 a −4331,7. La vena `196acd80` è su **quella stessa faccia**, y=−4528,4 (polilinea (16074,5; −4528,4)
  quota −5607 → −8089). Lara, «a sinistra fino in fondo», è appesa al tratto p4→p5 a y=−4410,7 = p5 − 79 (estensione 79 del
  blocco ledge 1): cioè **118 unità oltre la vena**, all'estremo opposto della faccia. Margine utile della faccia: y da −4592,7 a
  −4410,7; la vena è a 64 unità dall'inizio (lato angolo).
- Conclusione: le istruzioni della prova (mie) la mandavano oltre la vena. Walkthrough: «hanging on the next square support column
  with a rock vein below her. Drop and grab the vein». Prova 3: appena girato l'angolo della colonna, fermarsi sopra la fessura e
  lasciarsi cadere (LCtrl).

## 9. Dati confrontati con l'Xbox (18/11, dopo «non va in nessun modo») e nuova pista: ombra accesa IN CADUTA

Confronti (memoria del dump m7 = ciò che il gioco usa davvero, contro i file Xbox originali):
- DTP 20212 (grafo di Lara/doppelganger): 2480 transizioni identiche (destinazione, condizioni, parametri, negazioni); stati con
  differenze solo di conversione (u16 a coppie, bool, puntatori) e ~21 id animazione rimappati (tipi 3/5); 111 modi e blocchi 1–19
  identici.
- DTP 24993 di dlc2_goo_room (markup del livello) PC installato contro Xbox: nessuna differenza nella zona dei markup2 (record della
  vena id 2593 e polilinea identici); le sole 275 differenze sono id rimappati in altre tabelle.
Conclusione: il grafo e i markup non sono diversi dall'Xbox. [F]

Nuova lettura del grafo (in caduta, famiglia 0x40e/0x40f/0x418/0x438):
- 0x40f -t2214-> 0x439 con `c416(3) & c14(markup 343) & !c262(608)`. Il parametro 3 di una condizione-wrapper è il **fronte di
  salita** (SPEC_COND 1.4: 0→!v, 1→v, 2→discesa, 3→salita): 0x416 = ombra attiva (PC: cave 0x123e049, come il TU: flag G+0x1244 →
  S'+4 bit0). Quindi: **in aria, nel momento in cui l'ombra si accende**, Lara passa a 0x439 (modo 107: cerca solo prese id 3 =
  vene) e con la vena candidata va a 0x5c5 `wall_run_jump_attach` (t880).
- Nessuna delle prove ha prodotto un fronte di salita in aria: 7/11 e prova 1 ombra premuta da appesa (≤0,33 s prima del distacco),
  prova A ombra tenuta da appesa 3 s, prova B nessuna ombra. [F registrazioni]
- c14 (id 20, parametro letto dal markup di stato 343) non è stato decodificato: potrebbe imporre un tempo/una distanza minima in aria.
Prova 4: distacco con solo LCtrl, poi premere LShift **mentre cade**, accanto alla vena (subito e, se non basta, dopo ~mezzo secondo).
- 18/11: Andrea dice di aver già provato l'ombra in caduta (prove non registrate: nella registrazione 1124 non c'è nessun tentativo
  dopo 616 s). c14 = cond id 20 (PC 0x783b70): `(int)Ctrl+0x508 >= valore tipizzato[343]` (0x782b40, modo ≥); soglia non letta.
  Diagnosi binaria con UNA prova registrata: se in caduta, dopo LShift, `game+0xb00` passa a 107 → t2214 è scattata e il problema è
  la ricerca (geometria/raccolta); se resta 44 → t2214 bloccata (c14 o c416) → leggere Ctrl+0x508 e la soglia.

## 10. Prova registrata 18/11 12:01 (`work/live/20261118_1201`): t2214 SCATTA, la ricerca non trova la vena

- Appesa a (16235,7; −4448,4) (80 u dalla vena lungo la faccia), LCtrl a 78,83 s, ombra accesa in aria ~0,13 s dopo (energia 980,7
  a 79,05). Il dump automatico (trigger 0x25d8000) ha congelato il gioco 79,05→~85 s: nessun campione grezzo in caduta.
- Controllore di stato = `[game+0xf10]` (0x18532e80); stato corrente = puntatore a record di stato in Ctrl+0x510: nel dump a 79,05 =
  **0x43b** (figlio di 0x42c ← 0x418 ← 0x40f). c14 = `(int)Ctrl+0x508 >= tabella tipizzata[343]`; [343] = int 3 (= Xbox; le 400 voci
  della tabella tipizzata sono identiche all'Xbox), Ctrl+0x508 = 41,7 → vera.
- Anello di traccia delle condizioni nell'exe (0x1240b20, 16 voci da 0x20, contatore 0x1240b10 = 0x1d4d; voce = id|gruppo,
  parametro|inversione, Ctrl, fn, esito, cache, rec): in ordine cronologico `c416(3)=1, c14(343)=1, !c262(608)=1` (rec
  0x212a8dc0/dc8/dd0 = t2214) → **t2214 vera**; poi `c262(608)=0` (rec 0x212a5790 = t880 di 0x439 verso 0x5c5) → nessuna vena
  candidata; poi Lara in 0x43b (t2215 c1).
- Quindi sul PC il percorso TU «ombra in aria → 0x439 (modo 107) → cerca la vena» funziona fino alla ricerca: è **la ricerca 0x1a7 con
  il modo 107** a non trovare la vena (o la trova e la scarta). Prossimo passo: eseguire in emulazione 0x7296c0(modo 107) sulla memoria
  del dump m3 e vedere dove la vena 196acd80 viene scartata (raccolta 0x70f300 / filtro 0x70ffb0 / scelta 0x728c30).

## 11. CAUSA nei dati (18/11): liste di tipi u8 dei filtri dei modi convertite come parole

- Emulazione (`emu/emu_search.py DUMP MODO [--fixlists] [--pos=x,y,z]`, unicorn sulla memoria del dump m3 di 12:01): 0x7296c0(game+0x980,
  107) → il collettore 0x70f300 trova **la vena 196acd80**; poi 0x729670 → 0x729540 → filtro per tipo 0x723330 la **scarta**.
- 0x723330: voce del filtro {+0x14 flag (bit0 = esclusione, bit4 = attivo), +0x18 n, +0x1c lista u8} confrontata byte per byte con
  TypeOf. Nel DTP 20212 installato 9 liste su 117 hanno i byte rigirati come u32/u16: Xbox `16 00 00 00` (tipo 22) → PC `00 00 00 16`,
  letto come tipo 0. Coinvolti: modo 107 (stato 0x439, vena in caduta), modi 44/45/46/106/117 (cadute), 56/111, 3, 1/2/6/20/26/43
  (tipo 2). Stesse 9 liste in `doppelganger_casual.drm` e `dlc_doppel_costume_a.drm` (unici file con DTP 20212; DLC1 non coinvolto).
  I miei confronti precedenti (§9) accettavano la parola rigirata come «u32 corretto»: per questo non l'avevano vista.
- Correzione: `work/ws/dlc2_tuport/data_fix/typelist_fix.py` (9 liste = byte Xbox; controllo dei vecchi byte, round-trip DRM, nessun
  altro byte cambiato) → `out_b272_typelist` → **baseline B272_typelist-4d778386d147** (gate libgate PASS; dlc_offline_check non
  eseguibile su Windows per `work/render/shaderlibs.pkl` mancante, stesso esito con B271).
- Emulazione con la correzione: la vena supera il filtro per tipo e arriva al controllo geometrico 0x729420 → sotto-controllo
  0x728f00 «check 0» (0x2125f2e0, parametri = Xbox) che la scarta; il punto passato vale (0,0,0): probabile artefatto del dump (Lara
  già 6.000 unità più in basso e in piena velocità). Non verificato: serve la prova in gioco con B272.
- Strumento: `tools\win_diag\LIVE_NODUMP.bat` = LIVE senza dump automatici (non congela il gioco in caduta).

## 12. Prova con B272 (18/11 12:34, `work/live/20261118_1234`) ed emulazione con la correzione

- In memoria del gioco (lettura ReadProcessMemory, pid 19672) le 9 liste sono quelle Xbox: la correzione è caricata.
- Due cadute dal ledge della colonna, entrambe dall'estremo (16235,7; −4410,7). Prova 1 (135,7 s): LShift+LCtrl insieme da appesa
  (nessun fronte di salita in aria). Prova 2 (207,49 s): LCtrl, poi LShift premuto tra 207,49 e 207,78 s, cioè con Lara tra quota
  −5461 e −5666. Modo 107 mai visto nel registro (0x439 dura un solo fotogramma: t2215 c1(1) → 0x43b).
- Emulazione (dump 12:01, liste corrette, Lara spostata): ricerca modo 107 → **vena trovata e scritta come candidato** (0x770240)
  con Lara a quota −5800 e −7500, sia allineata alla vena (y −4528) sia all'estremo del ledge (y −4410,7, −4448, −4490); **non trovata**
  a −5470…−5750 e a −8000…−8300; **mai trovata senza correzione**. Finestra utile ≈ quota −5800 … −7500 (vena da −5607 a −8089).
- Tempi della caduta (prova 2): −5800 a ~0,36 s dal distacco, −7500 a ~0,8 s. L'ombra va accesa (pressione nuova, non tenuta) in
  quella finestra: nella prova 2 è stata premuta ~0,1 s troppo presto.
- Conclusione: con B272 il PC si comporta come previsto dal grafo TU; resta la prova con il tempo giusto. Mossa: lasciarsi cadere
  (LCtrl, senza ombra) e premere LShift circa mezzo secondo dopo, mentre Lara scorre accanto alla vena.

## 13. «Su Xbox premi e si attacca subito» (18/11 pomeriggio): seconda ricerca da appesa e controllo di visibilità

- Walkthrough Xbox (Stella, Chronicles): «Drop and grab the vein» senza tasti; Shadow Power = LB/RB. Nessuna istruzione di accendere
  l'ombra in caduta.
- Da appesa gira una seconda ricerca: `0x7296c0(game+0xb10, [game+0xc90])`, candidato in `game+0xbf4`. Sul ledge della colonna
  c90 = 8, bf4 = 0 per tutto l'appeso (registrazioni 12:34).
- Emulazione modo 8 con S=game+0xb10, Lara appesa all'estremo (−4410,7; quota −5460,7):
  - con `game+0xc94` = 0 (non agganciata): **bf4 = vena 196acd80** (con e senza correzione delle liste);
  - con `game+0xc94` = ledge 196ae1c0 (com'è davvero da appesa): **bf4 = 0**. La vena è raccolta; la voce del modo 8 con lista [22]
    (0x2125db6c) la scarta nel controllo 0x2125f2e0 di tipo 10 = `0x725b50`: due punti (id 0xd e 4, da 0x723ab0) spostati con gli s16
    di Lara obj+0xfd8/+0xfda (5 e 2, = Xbox) e test di collisione `0x6fcb10` tra i due. Cioè un controllo di visibilità/spazio libero
    tra Lara e la vena, che da appesa fallisce.
- Modo 44 (ricerca al distacco, 0x417): la vena non viene nemmeno raccolta (traiettoria verticale parallela alla vena).
- Verifica a tappeto delle parole rigirate nel DTP 20212 (B272 contro Xbox): 788 parole u32 rigirate con valore non plausibile né come
  intero né come float; molte simmetriche (innocue), altre no, ad es. Lara obj+0x294 `08 00 05 00` → `00 05 00 08`, tabelle u8 a
  0x22030–0x2224c, campi a 0x26754–0x26900. Stessa classe di errore delle liste di tipi: da verificare con l'oracolo PC 850 (lara base).
- Stato: la correzione delle liste è necessaria (verificata) ma non sufficiente; prossimo passo = capire perché il controllo di
  visibilità 0x725b50 fallisce da appesa (punti 0xd/4, collisione) e completare l'audit delle parole rigirate.
- 18/11 sera: emulazione del controllo 0x725b50 da appesa (dump in caduta + ledge forzato come agganciato): punto A = (16200,9;
  −4448,4; −4966,85) (quota del ledge, 126 u fuori dal muro), punto vena P = (16074,48; −4528,36; −5765,38) sul piano del muro;
  `0x6fcb10` → bloccato. Spostare P fuori dal muro di 2/10/47,4 u non cambia l'esito. Con Lara non agganciata A = (16074,5; −4410,7;
  −5298) e il test passa. Il dump in caduta non è coerente con lo stato «appesa» (A usa posizione/ossa dell'istanza, non sovrascritte):
  serve un dump preso **da appesa** sul ledge della colonna per emulare con stato coerente.

## 14. Dump da appesa (18/11 13:09, `work/live/20261118_1308` m2 = estremo, m3 = 40 u dalla vena)

- Stato reale: appesa (lflags 65c0000), c94 = ledge 196ae1c0, b00 = 87/38, c90 = 8/7, a64 = bf4 = 0. Liste B272 in memoria = Xbox.
- Emulazione ricerca da appesa `0x7296c0(game+0xb10, 8)` (e 7 su m3): la vena è **raccolta**; la voce del modo con lista [22]
  (0x2125db6c) la scarta nel controllo 0x2125f2e0 (tipo 10 → 0x725b50 → **0x6fcb10**).
- 0x6fcb10 non è un test di collisione ma una **verifica di portata**: punto mani A (+ scostamenti del blocco parametri) contro il
  segmento della vena, con finestra di altezza blocco+0x54 e raggio blocco+0x58 (+ param 0, come nel TU). Blocco 18 (vena):
  +0x40 = −118,52, +0x54 = 0, +0x58 = 513,59, +0x5c = 316,06 (= Xbox; puntatori obj+0x584..+0x5c4 = Xbox).
- A = arco(ctx+0xa0, t = item+8) + item+0x90; per la vena item+8 = **0** (per i ledge raccolti t > 0), item+0x90 = (63,21; 0; 474,08)
  dal modo (+0x58/+0x5c = −474,08/−63,21, = Xbox) → A = (16200,9; y; −4966,85), cioè all'altezza delle mani sul ledge, ~800 u dalla
  cima utile della vena (−5765). Abbassando A di 300–600 u in emulazione la vena viene scelta (bf4 = 196acd80). Allargare il blocco
  18 (+0x54/+0x58 fino a 700) non basta.
- TU: dispatcher 0x8241cfb0 (= 0x728f00, stessa tabella), caso 10 → 0x8241fb10 (= 0x725b50, stessa struttura, parametri 0,0), portata
  0x823fa370 «same» rispetto alla base; caso 0xd del punto (0x8241cb08) è VMX non decodificato. Il collettore TU ha in più solo il
  blocco VMX per markup su oggetti mobili (obj+0x2d8). Nessuna differenza di dati trovata.
- Aperto: perché sul TU la vena sotto è raggiungibile da appesa (o quale altro percorso usa). Serve la verità Xbox nello stesso punto
  (Xenia: item della vena, t, punto A, bf4) oppure decodifica VMX128 del caso 0xd TU.

## 15. Decodifica del codice TU con le istruzioni VMX128 (18/11 sera)

- Ghidra 12.1.4 (C:\TRL\tools) non ha VMX128 (solo AltiVec): è il motivo dei «pcode error / bad instruction» della decompilazione TU.
  Costruito `tools/ppcdis/ppcdis.exe` (driver C sul disassemblatore binutils di XenonRecomp, dialetto «cell» con VMX_128, clang)
  e `tools/ppcdis/fndiff.py` (diff TU/base normalizzato).
- Punto mani (caso 0xd, TU 0x8241cb08): `A = p0 + v·t + (0,0,½·g·t²) + item+0x90` con t = item+8, p0/v/g = ctx+0xa0/+0xb0/+0xc0 —
  **uguale al PC** (0x723fb2 + 0x697220).
- Collettore TU 0x823fa8c0 contro base 0x823f8178: stesse 35 chiamate nello stesso ordine; unica aggiunta TU (+20 istr.) = per i markup
  agganciati a un oggetto (inst+0x20, inst+0xc, obj+0x2d8 ≠ 0) scarta se |distanza| > 500,0 (costante 0x82000d98). Non riguarda la
  vena (inst+0xc = 0). Le 17 funzioni chiamate hanno la stessa lunghezza TU/base salvo 0x823f6b08 (+6 istr., differenze di registri).
- Ricerche da appesa per direzione (grafo 0x1b3: c195 450–453): modi 84/85/9/10/110 emulati sui dump da appesa → nessuno sceglie la
  vena; da ferma (0x1c2) non gira alcuna ricerca. Il distacco (849 → 0x417, modo 44) non raccoglie la vena.
- Quindi il codice coinvolto è equivalente al TU; l'unico percorso che aggancia la vena è quello in caduta con l'ombra: fronte di
  salita di 0x416 in aria → 0x439 (modo 107, ricerca di un fotogramma) → 0x5c5, che con B272 in emulazione riesce con Lara tra quota
  −5800 e −7500 (§12). Ogni nuova pressione in aria ripete la ricerca (0x42c/0x43d hanno anche t2214).

## 16. Indizio di Andrea (18/11 sera): su Xbox, con l'ombra attiva, il salto ledge→ledge è «una sorta di teletrasporto»

- Coincide con il sistema dell'ombra «a bersaglio» del TU: Target Manager a 10 slot (slot 6 = bersaglio vena/ombra, 8/9 nuovi),
  cond 0x7d5/0x7d6/0x7dd/0x418/0x420, stati 0x2ed/0x2f4 → 0x2fb/0x2fc/0x2fd/0x301/0x305, azioni 0x3f9/0x3fb/0x3fc/0xf3/0xf4/0xf5 che
  scrivono il «warp record» del controller dell'animazione (spec: `dlc2_tuport/spec_S/SPEC_MOVE.txt`, `spec_cond/SPEC_TM.txt`,
  `exe_build/RAPPORTO_exe_build.txt`). Portato sul PC negli stadi s1–s5 dell'exe (24/10), **mai verificato in gioco**; allora restavano
  aperti: riempimento/selezione dello slot 6, 0x418 = sempre vera, P/H (oggetto 858, DTP 22497) assente sul PC → cfg slot 8 = 0,
  parti VMX delle azioni non decodificate (ora decodificabili con `tools/ppcdis`).
- Dump da appesa (m2/m3): TM con 10 slot, 7 candidati registrati per slot (8 per lo slot 8), **nessun bersaglio selezionato** in
  nessuno slot; cfg slot 8 = 0, slot 9 = 0x1242040.
- `dlc2_uo_jump_target` (id 1042) e `dlc2_uo_breakledge_*` (951–954) non sono istanziati in nessuna unit DLC2 (intros_p11): non sono loro
  i bersagli.
- Ipotesi di lavoro: sia il teletrasporto ledge→ledge (A19) sia l'aggancio immediato alla vena passano dal ramo «ombra a bersaglio».
  Piano offline: (1) quali transizioni portano a 0x2ed/0x2f4 da appesa/salto con l'ombra e quali condizioni falliscono sullo stato del
  dump (c416, c98(147), c420 energia ≥ 75 %, 0x7d5/0x7dd); (2) selezione lazy dello slot 6 emulata sul dump; (3) decodifica VMX delle
  azioni TU 0x3fb/0x3f9 (8245f2a8, 82457b28) e confronto con s5.

## 17. Pista «teletrasporto» (18/11 notte)

- Header degli stati nel DTP 20212 convertito: stesso formato della Lara PC nativa (DTP 850, campi u16): nessun errore.
- AttachStart/AttachedUpdate/Release del modulo S' (TU 823d8978/8d18/9210, «posiziona Lara sul bersaglio dello slot 5») sono usati
  dall'azione **0x3f6** (riga 28 B a 0x827589b0: f1 = 8245fd70, f3 = 8245fdc0, f4 = 8245fd98; smistatori `game+0x1244 ? S' : Lara
  base`). Sul PC l'azione 0x3f6 chiama sempre le funzioni base. Ma 0x3f6 compare in **un solo stato, 0x335** (famiglia combattimento
  0x2c7, ingresso t1464 con c96(146) e bersagli c7d1/c7db): non è il salto tra ledge né la vena.
- Ingressi nella famiglia 0x2e5–0x30a: solo da stati a terra/combattimento con c98(142/143) (pulsanti), non da appesa o in salto.
- Tempo dell'ombra: il porting (stadio fx, FX1) scrive gli slot PC 0x8abe94 (→ 0xe7f1d4) e 0x8abeb4 (→ 0xe7f1a0, che moltiplica i dt
  globali 0xe7f194/0xe7f188) con L0 = (1,2; 0,3); StartShadow (L3, 0,1) richiede Lara+0x1fc bit 9/10/24/30, mai visti nei flag
  registrati. Nella prova 12:34 la caduta con l'ombra (1,8 s) è durata quanto senza (1,9 s): sul PC l'ombra non rallenta la caduta.
- Aperto: che cosa produce il «teletrasporto» su Xbox. Candidati: (a) scala dei tempi (mondo rallentato, Lara veloce) diversa o non
  applicata sul PC; (b) un'altra azione/stato non ancora individuato. Serve la descrizione di Andrea di cosa si vede con l'ombra sul PC
  e su Xbox (mondo rallentato? Lara accelerata?).

## 18. Salto tra ledge con l'ombra: stati dedicati senza animazione; TruLive registra lo stato (18/11 notte)

- Andrea: con l'ombra il mondo rallenta sia su Xbox sia su PC (la scala dei tempi funziona).
- Grafo: da appesa, con l'ombra (c416(1)) lo spostamento laterale passa a 0x1be/0x1bf (invece di 0x1b5/0x1b4); da lì i salti oltre un
  vuoto (lookahead 643/644, c1(1) = sempre vera, PC 0x782700) vanno a **0x1d7/0x1d9 e 0x1d5/0x1d3**, che **non hanno animazione**
  (x = 0xffff) e hanno i parametri 0x21a = 1, 0x65 = 1, 0xe1 = 1,4; le versioni senza ombra 0x1d8/0x1da/0x1d6/0x1d4 usano
  «flair finish» / «rolling jump». Probabile origine del «teletrasporto». Le funzioni che leggono 0x21a/0xe1 (TU 0x8242d748, 0x8244d0b8,
  0x82461a30, 0x82478c80) hanno la stessa lunghezza della base (differenze di indirizzi).
- TruLive: nuova riga `G <ms> <indice stato> <ptr>` a ogni cambio di stato del grafo (controllore [game+0xf10], record [ctrl+0x510],
  indice nella tabella del DTP 20212); verificata sui dump (m2/m3 = 0x1c2 appesa, m4 = 0x43b caduta). Compilazione con le stesse
  opzioni del lanciatore: OK. Con la prossima prova si vedrà la sequenza di stati del salto con l'ombra e della caduta accanto alla vena.

## 19. Prova 13:52 con la riga G (stati del grafo)

- Sequenze lette: risalita vene ok (0x137 → 0x5c5 → 0x5d4/0x5de/0x5ce …); shimmy con l'ombra = **0x1bf** (ramo ombra preso dal PC).
- Salto verso la colonna (63,5–65,8 s): 0x1bf → 0x1b4 a 64,84 s per t631 (!c416) perché l'**energia dell'ombra si è esaurita**
  (172,6 a 63,9 s → 59,8 a 64,9 s, LShift ancora premuto), poi salto normale **0x1d6** («flair finish»). Nessuno stato-ombra di salto
  (0x1d3/0x1d5/0x1d7/0x1d9) visto: il caso «teletrasporto» non è stato ancora provato con energia sufficiente.
- Caduta dalla colonna (79,04 s): 0x42c → 0x43b, **nessun 0x439**. LShift tenuto da prima del distacco (78,28) fino a ~79,98 (nessun
  fronte in aria nella finestra quota −5800…−7500 = 79,31–79,76 s), ripremuto a 80,04 s con Lara a ~−9300 (sotto la vena).
- Osservazione: sul PC l'energia scende a ~200/s in tempo reale (1000 → 309 in 3,1 s il 18/11 12:34) anche con il mondo rallentato.
  Il TU drena `dt·(1/30)·P.f14`: se sull'Xbox dt è quello rallentato (×0,3), l'ombra dura ~3 volte di più. Da verificare (codice
  stadio 2 del porting: quale dt usa) e da chiedere ad Andrea (durata dell'ombra su Xbox).

## 20. SECONDA CAUSA nei dati: lista di tipi del profilo di caduta (18/11 sera)

- Andrea: i test erano corretti; su Xbox si tiene l'ombra, ci si stacca e la vena si aggancia subito. Prova 13:52: 0x43b raggiunto solo via
  0x439 (stato di un fotogramma non campionato), quindi la ricerca in aria con l'ombra ripremuta parte davvero; il caso da riprodurre è il
  **distacco** con l'ombra già attiva.
- Emulazione del distacco sul dump da appesa (m2: c94 = 0, ledge escluso, modo 44): il collettore non raccoglie nemmeno la vena.
  Causa: primo filtro del collettore `0x7232e0(inst, P = modo+0x94)` = lista u8 a livello di profilo (P+8 flag, P+0xc n, P+0x10 lista).
  Su 55 liste di profilo, 1 errata: **0x80ed0** (modi 44/46/106/117), n = 19, ultima parola Xbox `08 15 16 00` → PC `15 08 00 16`
  (convertita come due u16): il 22 finisce al 20° byte, fuori lista.
- Con la parola corretta in emulazione: candidato `game+0xa64` = **vena 196acd80** al distacco (quota −5462/−5470/−5520, dall'estremo
  del ledge); senza correzione mai.
- Correzione: `data_fix/typelist_fix2.py` (1 parola, sopra B272) → `out_b273_typelist2` → **B273_typelist2-0814702a92b5** (libgate PASS).
  Non installata.

## 21. ESITO 18/11 pomeriggio: vena RISOLTA con B273 (Andrea: «risolto, sono riuscito a proseguire»)

- Registrazione 14:03: a 68,5 s **0x43c → 0x5c5** (aggancio alla vena dalla caduta, percorso t2216 di 0x438). Traccia V chiusa per la vena
  della colonna; cause = due liste u8 di tipi del DTP 20212 convertite come parole (B272: 9 liste di voce; B273: 1 lista di profilo).
- Teletrasporto (A19) ancora assente. Nella stessa registrazione 6 salti oltre un vuoto, tutti nella versione normale (0x1d4/0x1d6/0x1d8),
  mai 0x1d3/0x1d5/0x1d7/0x1d9: in nessuno l'ombra era attiva al momento del salto (61,1–62,2 s: ombra con energia 197 → 7, finita 1,2 s
  prima del salto delle 63,3; 74–75 s e 112–113 s: LShift non premuto). L'energia viene consumata risalendo le vene (~200/s) e ricaricata
  ~400/s da agganciata. Il ramo «salto con l'ombra» (0x1be/0x1bf → t651/653/649/655 → 0x1d7/0x1d5/0x1d9/0x1d3) è automatico quando, in
  shimmy con l'ombra, il lookahead trova un vuoto saltabile: serve arrivarci con l'ombra attiva.

## 22. Teletrasporto (A19): il salto «premendo il tasto» con l'ombra (18/11 sera)

- Andrea: con l'ombra attiva salta da appeso (tasto), il PC fa «un salto lungo ma normale», l'Xbox un teletrasporto.
- Registrazione 14:03: salto da shimmy-ombra = 0x1bf → 0x1c7 → 0x104 → 0x137 (stessi stati di un salto normale, ombra attiva).
  Nel grafo i salti da appeso non hanno varianti con c416: la differenza, se c'è, è nel codice o in un'altra mossa.
- Candidato: azione 0x3f6 (AttachStart/AttachedUpdate/Release del modulo S', «posiziona Lara sul bersaglio») nello stato 0x335, ingresso
  t1464 = `c21a(1) & c7d1(1) & c7db(1) & c2bd(0) & c5de(0) & c8fe(1) & c96(146) & c416(1)`: ombra attiva + pulsante 146 + bersaglio
  (c7db = slot 9 con flag). Sul PC 0x3f6 esegue le funzioni base (AttachStart non portato) e la transizione t1464 non ha stati sorgente
  nella tabella (transizione globale da verificare).
- Funzioni di Lara modificate dal TU che leggono S' (823dca00, dd580, dd8f8, ddc28, ded18, dee58, defa8): 823ddc28 è la gestione
  adrenalina/mira (contatori game+0x588/+0x58c), non il salto; le altre da leggere con `tools/ppcdis`.
- Serve da Andrea: tasti esatti su Xbox per il teletrasporto e com'è (Lara sparisce e riappare? c'è un bersaglio evidenziato?).

## 23. Nuovo caso (18/11): ledge sotto la vena 196acdc0, la doppelganger non lo afferra scendendo dalla vena

- Registrazione 14:03 (tre tentativi 171 s, 365 s, 387 s): 0x43c → 0x5c5 (aggancio alla vena 196acdc0, x 10078, y −4040, quota −10317 →
  −12784) → 0x5d5 (discesa con S+LShift) → 0x5df (fondo vena, quota Lara −13205,5) → rilascio LShift → 0x42c caduta → morte (−15203).
  Ledge sotto: 196ad0c0 (tipo 1) a quota −14448, ~1240 sotto Lara. game+0x6dc/+0x6e0 (inizio caduta) al fondo vena = −13205,5 / 0.
- Emulazione (dump 13:08 m2 + Lara al fondo vena, inizio caduta corretto, vena esclusa, modo 117 = caduta dalla vena): il ledge viene
  raccolto, passa tutti i 9 controlli della voce 0x2125d894, entra nella lista dei candidati, ma ha **classe di aggancio 3** e il
  0x7296c0 scarta i candidati con classe 3 (`local_480 == 3` → 0x770550). Classe calcolata da 0x728650: primo record (16, a 0x14 B)
  della tabella del blocco parametri del ledge (blocco 1, +0x90/+0x94, = Xbox) i cui test 0x7260b0/0x728500 passano; i test usano una
  sonda di collisione nel mondo (0x493330, maschera 0x3c19e7) sotto/intorno al ledge (item+0xa8 = quota del pavimento).
- Ipotesi: la sonda di collisione restituisce sul PC un risultato diverso dall'Xbox (dati di collisione del livello convertiti, non il DTP
  20212). Da verificare: argomenti/risultato reali di 0x493330 (il primo aggancio nell'emulatore ha letto argomenti sbagliati).
- 18/11 sera, dettaglio: la classe viene dalla quota del «pavimento» sotto il ledge (item+0xa8 = quota ledge − quota colpita). Sonda
  `0x493330(0x3c19e7, da (x,y,−14417), a (x,y,−298930), out, …)` chiamata da 0x728994: colpisce **tipo 2 a quota −15074,2**, normale
  (0,0,1), oggetto 0x1fda9200 → pavimento 626 u sotto il ledge → nessun record «aggancio» valido → classe 3 (riserva) → candidato scartato.
  Ma Lara ha attraversato quella quota ed è morta a −15203: non è un pavimento solido. Walkthrough Xbox (Stella): «hang from the long
  handhold just above the round eitr pool … drop to grab the rock vein below. Slide down and drop to grab the handhold below the vein» →
  la superficie è quasi certamente la **pozza di eitr**. Ipotesi: sul PC la superficie della pozza è nella collisione del livello con flag
  materiale che la sonda (maschera 0x3c19e7) considera pavimento; sull'Xbox è esclusa. Prossimo: flag del materiale della faccia colpita
  (dati di collisione del livello convertiti, sezione terreno) contro Xbox.

- 18/11 sera, **confronto completo della collisione** di `dlc2_goo_room.drm` (Xbox `work/dlc2/xbox` contro B273 installata): 7 mesh di
  collisione (intestazioni 0x58 in sez. 23, vertici sez. 2-8 = 6129 float4, facce sez. 9-15 = 10484 record da 20 byte, nodi KD sez.
  16-22 = 11190 record da 16 byte). Con il layout di `tools/generic_type0.py` (faccia: 3 u32 + u8,u8,u16 + 4 byte grezzi; nodo: 3 u32 +
  4 byte grezzi; vertexType/height u16) **0 byte diversi**, code parziali comprese; sez. 0/1/24-26/28/30 solo parole scambiate e u16 a
  coppie, coerenti; sez. 29 (76620 byte, già little-endian anche su Xbox, probabile Umbra) identica. **La collisione del livello è
  uguale all'Xbox.**
- Sonde ricostruite (dump m3, modo 117): il test di spazio dei record 5/6 lancia raggi orizzontali a quota ledge+252 (z −14196) da 100 u
  davanti al muro a 139 u dietro: verifica che **sopra il ledge non ci sia muro** (spazio per salirci sopra); qui il muro della vena
  continua sopra il ledge → fallisce. I record di sola presa richiedono una profondità del pavimento diversa (pozza a 626 u, terreno a
  1375 u). Con dati, codice e collisione uguali all'Xbox, lo stesso calcolo sull'Xbox darebbe lo stesso risultato: o l'originale non
  afferra quel ledge cadendo dalla vena (percorso diverso), o la differenza sta in un ingresso non ancora confrontato (stato/posizione
  di Lara al distacco, quota d'inizio caduta).

- 18/11 sera, Andrea: **sull'Xbox la doppelganger lascia la vena e cadendo si appende al ledge sotto**.
- Correzione: `--nowater` non escludeva la pozza (la sonda la colpiva comunque); le conclusioni «escludere l'acqua non cambia» erano
  sbagliate. Tabella classi del ledge (DTP 20212 +0x33bc0, = Xbox): record {classe, fascia min, fascia max, tipo test, w4}; fascia =
  quota colpita − quota ledge. Record 6 (classe 7, −635…−474) chiede spazio sopra il ledge (fallisce: muro); record 12 (classe 12,
  −284450…−632,1) no. Pozza: −626 → solo record 6 → classe 3. Emulazione con la quota colpita forzata (`--floorz`, scritta a 0x7289ce):
  −15090 (−642), −15200, −15823 (terreno) → **ledge accettato, candidato scritto in game+0xa64**. Bastano 6,2 unità.
- Il volume colpito è l'istanza 0x2d12 = oggetto 7 `watervolume` (intro in DTP 24993 +0x4dc0, posizione file (−21399, −9114, −4344),
  semiassi (28533, 10586, 2770,27) a +0xa814, script 25079 con stati «down»/«up»). In memoria l'istanza (pool statico 0xd25e70) sta a
  (−2480,25, 2964,2, −17844,5): **spostata a runtime** (dallo script/stato su-giù?). Tetto del volume −15074,2, cioè 2770 sopra il centro
  e 750 sopra il terreno sotto il ledge (−15823). La superficie visibile (`dlc2_goo_room_watersurface`, stessa matrice, mesh locale
  z 0,35…568) starebbe a ~−17844…−17276, sotto il pavimento: lì l'eitr non si vede, ma c'è il volume.
- Codice della classe Xbox (TU 0x82420728 = base 0x8241d698, solo costanti) usa la stessa maschera 0x3c19e7.
- Ipotesi di lavoro: sull'Xbox in quel momento il volume è più in basso (stato «down» o posizione diversa) e la sonda trova il terreno.
  Da verificare: chi sposta l'istanza e con quali valori.

- 18/11 notte, Andrea: sull'Xbox l'eitr è alla stessa altezza. Verificato: nessuno spostamento a runtime; tutte le istanze di goo_room
  hanno lo stesso scostamento di unità (+18918,9, +12078,9, −13500,2), pozza compresa. La correzione «quota della superficie»
  (0x6c1cd0 → 0x6ad010, W+0x58) dà −15074,23 come il tetto; le onde (W+0x7c bit 1, dato u16 a +0x4a) sono spente anche nei dati Xbox.
- **CAUSA: costante ritoccata dalla TU.** Il test di fascia 0x7260b0, per i record di tipo 3/4 (classe 0, presa), chiede
  quota_colpita − quota_ledge ≤ costante: PC 0x85e4ac = base Xbox (FUN_8241d148, 0x8207df68) = **−628,9395**; TU (FUN_824201d8,
  0x8207e7d8) = **−616,2975**. Qui −625,9: PC scarta, TU accetta. Emulazione (`--tu628`, dump m3): ledge classe 0, candidato scritto,
  modi 117 e 44.
- Correzione exe **B274** = stadio `tu616` (`work/ws/b274_tu616/patch_tu616.py`): 4 byte in .rdata (3 diversi), riferimenti alla
  costante solo i due fcomp di 0x7260b0 (asserito). Exe `tru_s8n_sap_cs2_tu616_cs.exe` md5 eee91f78…; catena ricostruita da zero
  fino a 36_tu616 (`rebuild.py catena`, MD5 identico). Vale per tutto il gioco, come la TU sull'Xbox. Non installato.
- Scansione costanti float TU≠base (`b274_tu616/tu_fconst_scan.py` → `tu_fconst.tsv`): 28 righe, quasi tutte coppie di funzioni
  abbinate male; candidate vere oltre a questa da verificare: 0x8251bec8 (16→8), 0x824ab5d8.

- 18/11 notte: **B274 INSTALLATO** (sì di Andrea): `tru.exe` = eee91f78; backup del precedente (2b7ee74c) in
  `work/backup_gioco/20261118_prima_di_B274/`. Da provare in gioco.
- Scansione costanti decimali TU≠base, v3 (`work/ws/b274_tu616/tu_fconst_scan3.py` → `tu_fconst3.tsv`): insiemi dei valori lis(+addi)+lfs/lfd
  per 6315 coppie di funzioni (imm/mod, base unica, rapporto ≥ 0,85), tracciamento registri corretto (mr/ori/rlwinm, bl). **Unico valore
  cambiato: −628,94 → −616,30 (già in B274).** Il resto: funzioni dove la TU *aggiunge codice* con costanti nuove — 0x8240a430 (switch
  esteso da 121 a 129 casi, costante −1), 0x823fa8b0 (+500, 1268 istr.), 0x821717b8/0x825609c0/0x824959d8 (0/1); 0x82509948 = coppia
  abbinata male. Non scansionati: immediati interi (tipo SAP 1000→3000) e le funzioni senza coppia base.

## 24. Teletrasporto: tasti dai walkthrough (18/11 sera)

- Walkthrough (Stella, Chronicles) rilette: nessuna descrizione di teletrasporto, bersagli evidenziati o «salto a bersaglio». Tasti Xbox:
  LB/RB tenuto = Shadow Power (velocità/rallentamento, presa su vene e roccia crepata), LB/RB + A = salto con l'ombra (salto normale tenendo
  l'ombra, per afferrare vene/roccia), LB/RB + X = Shadow Strike, LB/RB + Y = Shadow Blast, RT = Shadow Fire, LT = mira. Andrea: nel video
  originale il teletrasporto «non lo fa sempre»; la doppelganger sparisce da un ledge e ricompare su quello di arrivo.
- Coerente con il grafo: il salto con LB+A è un salto normale (stati 0x1c7/0x104/0x137, come sul PC); la mossa senza animazione (0x1d3/
  0x1d5/0x1d7/0x1d9) scatta solo in shimmy con l'ombra (0x1be/0x1bf) quando il lookahead trova un vuoto saltabile (643/644): cioè non
  sempre, solo su certi ledge. Nelle registrazioni PC non è mai capitato con l'ombra attiva. Prova utile: shimmy (senza premere salto)
  verso un vuoto tra due ledge tenendo LShift con barra piena.
- 18/11 sera, approfondimento (emulazione modo 44 = quello reale, inizio caduta −13205,5):
  - La superficie a −15074,2 è un **volume d'acqua** (pozza di eitr): proxy di collisione 0x1fda9200, forma box (centro −17844,5,
    semialtezza 2770,3), tipo 2 (byte +0x9d) impostato da costante nel codice (PC 0x69d495 `push 2`; TU 0x823bb074 `li r10,2`, uguale
    alla base); la sonda di classe (maschera 0x3c19e7, uguale in TU e base; funzione sonda TU 0x82137818 = base) lo include. Il terreno
    vero è a −15823 (gruppo 0x1832c300).
  - Escludere l'acqua dalla sonda (maschera senza 0x80000) **non cambia** l'esito: classe sempre 3.
  - Tabella classi del blocco ledge: i record 5/6 (fascia pavimento −635…−474, classi 10/7) passano il test di fascia 0x7260b0 ma
    falliscono 0x728500 caso 0 = `0x737d60` + `0x727bf0` (test di spazio con la collisione del mondo); gli altri non passano la fascia;
    resta il record 15 (classe 3, riserva) → candidato scartato.
  - Codice coinvolto = Xbox (TU = base) e dati DTP = Xbox: la differenza residua più probabile sono i **dati di collisione del livello**
    convertiti (terreno/oggetti), su cui lavorano 0x727bf0 e le sonde. Verità di riferimento possibile solo con l'Xbox (Xenia) o con un
    confronto della collisione del livello convertita.
- 18/11 sera: test di spazio 0x727bf0 = 4 sonde `0x4935f0(0x2c19e7, segmento)` da (ledge + misure corpo obj+0x6e8/+0x6ea/+0x6f0 = 252/94/142,
  = Xbox) verso il muro: colpiscono il muro sopra il ledge a y −4039,6 (geometria normale, stesso piano della vena). Misure del corpo =
  Xbox (la Lara nativa ha 189/94 a +0x6ea/+0x6f0, diverse per progetto).
- Sul PC al fondo della vena Lara è in **0x5df** (figlio di 0x5dd, azioni 0x1a7/0x203/0x1a9: salto dalla vena con direzione, ricerca
  game+0xb10 col modo c90 115) tenendo S+LShift; poi LShift rilasciato → caduta. Le ricerche simulate da qui usano lo stato del dump preso
  sulla colonna (Lara agganciata altrove) e non sono affidabili: serve un **dump preso in fondo alla vena 196acdc0**.
- 18/11 sera, dump in fondo alla vena (`work/live/20261118_1429` m3: stato 0x5db = distacco dalla vena, b00 117, c90 115, c94 = vena,
  inizio caduta −13205,5): emulazione **con lo stato reale** → stesso esito, ledge 196ad0c0 classe 3, scartato (modi 117 e 44; il salto
  c90 115 non raccoglie nulla).
- Faccia colpita dal test di spazio: terreno, gruppo 0x1832c300, faccia 0x2018aaa0 = `dlc2_goo_room.drm` sezione 9 (tipo 0, collisione)
  offset 0xe60. Record faccia = 3 indici u32 + (u8, u8, u16) + u32: PC e Xbox coerenti (u8 invariati, u16 scambiati correttamente, es.
  Xbox `30 03 00 80` → PC `30 03 80 00`). Nessun errore di conversione visibile su questa faccia.
- Stato: codice (TU = base) e dati confrontati (DTP 20212, markup, faccia di collisione) uguali all'Xbox, eppure sul PC il ledge risulta
  non afferrabile dalla caduta. Restano: (a) verità dall'Xbox con Xenia; (b) confronto completo della collisione del livello (vertici e
  facce del gruppo 0x1832c300); (c) correzione di gioco mirata (accettare la classe 3 per i ledge raggiunti in caduta da una vena).
