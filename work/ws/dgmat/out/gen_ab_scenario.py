"""Genera uno scenario runner (JSON) per A/B per materiale col hook F8 > Materials > Material editor.
NON TESTATO (nessuna VM). Richiede vm_run.click.ps1 (azioni 'click' e 'type', vedi vm_run.click.diff).
Uso: python3 gen_ab_scenario.py calib > ../../../../tools/runner_scenarios/dgmat_calib.json   (dopo revisione dell'orchestratore)
     python3 gen_ab_scenario.py ab 20530:12:1,30,1,1:1,2,0,2:1,0,0,0 22581:...  > dgmat_ab.json
  voce ab = MATID:IDX_PRIMO_VEC4:v4:v4:... (indici = cN-100, vedi ab_padded_tail.tsv); valori float separati da virgola.
  La modalita' 'zero' (MATID:zero:N) azzera i primi N vec4.
Coordinate normalizzate (area client 640x480 del gioco). Menu bar misurata da work/runs/mp2/a2/shots/045s_menu_open.png:
  Render x=32 Instance 98 Frontend 170 Script 235 Materials 302 Draw 365 Log 405 Help 446, y=10  (-> /640, /480).
Le coordinate della finestra Materials (default ImGui: angolo (60,60)) e del campo filtro/lista/primo vec4 sono STIME: la corsa 'calib'
serve a misurarle da screenshot e a correggere CFG.
"""
import json,sys
CFG=dict(
  materials_menu=(302/640,10/480),
  editor_item=(330/640,32/480),      # voce 'Material editor' sotto il menu (stima)
  filter_field=(100/640,95/480),     # campo 'Material' (stima)
  first_item=(90/640,130/480),       # prima riga della lista dopo il filtro (stima)
  first_vec4=(330/640,95/480),       # primo sottocampo del primo InputFloat4 nella colonna destra (stima)
)
def base(name,desc):
    return {"name":name,"description":desc,"baseline":"B8","params":{"unit":"dlc_dungeon","load_timeout_s":150},
      "timeouts":{"total_s":900},"critical":["dlc_dungeon*.drm","streamgroups\\*dungeon*"],
      "saves":{"set":"dungeon_direct","fallback_baseline":True,"touch":["Autosave.TRUSave"]},"require_markers":[],"pass_text":"scenario completato",
      "steps":[{"id":"boot","action":"boot_resume","enter_first_s":20,"enter_every_s":8,"max_enters":6,"timeout_s":180,"settle_s":8},
        {"id":"menu_open0","action":"f8","state":"open"},
        {"id":"load","action":"load_unit","unit":"${unit}","timeout_s":"${load_timeout_s}"},
        {"id":"settle","action":"wait","seconds":15},{"id":"menu_close0","action":"f8","state":"close"},{"id":"wait0","action":"wait","seconds":3},
        {"id":"shot_ref","action":"shot","name":"ref0"}]}
def open_editor(S,tag):
    S+= [{"id":"f8_"+tag,"action":"f8","state":"open"},
         {"id":"mm_"+tag,"action":"click","nx":CFG['materials_menu'][0],"ny":CFG['materials_menu'][1]},{"id":"w1_"+tag,"action":"wait","seconds":1},
         {"id":"shot_menu_"+tag,"action":"shot","name":"menu_"+tag},
         {"id":"ed_"+tag,"action":"click","nx":CFG['editor_item'][0],"ny":CFG['editor_item'][1]},{"id":"w2_"+tag,"action":"wait","seconds":1},
         {"id":"shot_win_"+tag,"action":"shot","name":"win_"+tag}]
def select(S,mid,tag):
    S+= [{"id":"flt_"+tag,"action":"click","nx":CFG['filter_field'][0],"ny":CFG['filter_field'][1]},
         {"id":"fa_"+tag,"action":"key","key":"ctrl+a"},{"id":"fd_"+tag,"action":"key","key":"delete"},
         {"id":"ft_"+tag,"action":"type","text":str(mid)},{"id":"w3_"+tag,"action":"wait","seconds":1},
         {"id":"it_"+tag,"action":"click","nx":CFG['first_item'][0],"ny":CFG['first_item'][1]},{"id":"w4_"+tag,"action":"wait","seconds":1},
         {"id":"shot_sel_"+tag,"action":"shot","name":"sel_"+tag}]
def edit(S,start,vals,tag):
    # click nel primo sottocampo del vec4 0, poi Tab fino al vec4 `start` (4 campi per vec4), valori separati da Tab
    S.append({"id":"v0_"+tag,"action":"click","nx":CFG['first_vec4'][0],"ny":CFG['first_vec4'][1]})
    if start: S.append({"id":"tabs_"+tag,"action":"key","key":"tab","count":4*start,"gap_ms":120})
    n=0
    for v in vals:
        S.append({"id":"e%d_%s"%(n,tag),"action":"key","key":"ctrl+a"}); S.append({"id":"t%d_%s"%(n,tag),"action":"type","text":v})
        S.append({"id":"tb%d_%s"%(n,tag),"action":"key","key":"tab"}); n+=1
    S.append({"id":"ret_"+tag,"action":"key","key":"enter"})
def main():
    mode=sys.argv[1]
    if mode=='calib':
        sc=base("dgmat_calib","calibra coordinate del menu Materials (nessuna modifica ai parametri)"); S=sc['steps']
        open_editor(S,"c"); select(S,20530,"c")
        S+=[{"id":"f8close","action":"f8","state":"close"},{"id":"tail","action":"wait","seconds":3},{"id":"shot_end","action":"shot","name":"end"}]
    else:
        sc=base("dgmat_ab","A/B per materiale via Material editor del hook"); S=sc['steps']
        # 1) controllo id: 21086 (sluice_gate, NON caricato nel dungeon) -> lista vuota; 20263 (acqua) -> 1 voce. Solo screenshot (shot_sel_idneg / shot_sel_idpos).
        open_editor(S,"idneg"); select(S,21086,"idneg")
        S+=[{"id":"clr","action":"click","nx":CFG['filter_field'][0],"ny":CFG['filter_field'][1]},{"id":"clra","action":"key","key":"ctrl+a"},{"id":"clrd","action":"key","key":"delete"}]
        select(S,20263,"idpos")
        # 2) CONTROLLO POSITIVO: acqua 20263 riga 0 = (1,0,1,0) magenta; poi imgdiff ref0 vs after_ctrl deve mostrare un cambio. Se NON cambia: i params sono bakati al load o l'id non e' quello -> i test seguenti non valgono.
        edit(S,0,['1','0','1','0'],"ctrl")
        S+=[{"id":"fc_ctrl","action":"f8","state":"close"},{"id":"ws_ctrl","action":"wait","seconds":4},{"id":"shot_after_ctrl","action":"shot","name":"after_ctrl"}]
        # 3) ripristino del controllo: riga 0 di 20263 = 0.4039,0.4902,0.3843,0 (valore originale)
        open_editor(S,"restore"); select(S,20263,"restore"); edit(S,0,['0.4039','0.4902','0.3843','0'],"restore")
        S+=[{"id":"fc_rest","action":"f8","state":"close"},{"id":"ws_rest","action":"wait","seconds":4},{"id":"shot_after_restore","action":"shot","name":"after_restore"}]
        for i,a in enumerate(sys.argv[2:]):
            p=a.split(':'); mid=int(p[0]); tag="m%d"%mid
            open_editor(S,tag); select(S,mid,tag)
            if p[1]=='zero':
                edit(S,0,['0']*(4*int(p[2])),tag)
            else:
                vals=[x for vec in p[2:] for x in vec.split(',')]; edit(S,int(p[1]),vals,tag)
            S+=[{"id":"fc_"+tag,"action":"f8","state":"close"},{"id":"ws_"+tag,"action":"wait","seconds":4},{"id":"shot_after_"+tag,"action":"shot","name":"after_"+tag}]
    json.dump(sc,sys.stdout,indent=1)
main()
