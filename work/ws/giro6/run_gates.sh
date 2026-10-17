#!/bin/bash
# Gate statici per il candidato = work/ws/giro6/compose/mods (B88b + strati). Uso: run_gates.sh TAG   -> work/ws/giro6/gates_TAG/
set -u
T=$1; R=/path/to/trudlcport; W=$R/work; PY=$R/tools/venv/bin/python
C=$W/ws/giro6/compose/mods; O=$W/ws/giro6/gates_$T; mkdir -p $O
cd $R
echo "== idref_selfcont (BLOCCANTE: solo_base e NESSUNO devono essere 0)"; $PY -I $W/ws/giro6/idref_selfcont.py $C | tee $O/idref_selfcont.txt
echo "== gate_stesso_id"; $PY -I $W/ws/shader4/gate_stesso_id.py $C $C $W/baseline/B88b_acqua/mods > $O/gate_stesso_id.txt 2>&1; tail -4 $O/gate_stesso_id.txt
echo "== tex_lifetime_check"; for s in all_resident only12; do for ty in 5 9 10; do echo "-- $s tipo $ty"; $PY -I $W/crash/B84_r6025/tex_lifetime_check.py ../ws/giro6/compose $W/ws/codefirst/gates_B87/scen_B87_$s.json --types $ty 2>&1 | head -4; done; done > $O/lifetime.txt; grep -E 'VIOLAZIONI|IGNOTE|--' $O/lifetime.txt
echo "== test_contract"; $PY -I $W/ws/contratti/test_contract.py 2>&1 | tail -3 | tee $O/test_contract.txt
echo "== dlc1_gate overlay"; $PY -I tools/dlc1_gate.py $C --scope overlay --baseline $W/ws/giro5/gates_B88b/gate_B88b.json --compare --json $O/gate.json 2>&1 | tail -6 | tee $O/dlc1_gate.txt
echo "== uid_scan (BLOCCANTE: nessun uid intro >= 16352, nessun duplicato per unita')"; $PY -I $W/ws/giro6/uid_scan.py $C > $O/uid_scan.txt; grep -v ">=16352: \[\]" $O/uid_scan.txt | head; echo "righe con uid alti: $(grep -vc '>=16352: \[\]' $O/uid_scan.txt)"
$PY -I - <<PYEOF
import sys,os,glob,struct,collections
sys.path.insert(0,'$R/tools'); import drm, unit_ids as U
bad=0
for p in sorted(glob.glob('$C/*.drm')):
    try: sc=drm.sections_with_data(drm.cdrm_decode(open(p,'rb').read(),'le'),'le')[1]; Lv=U.level_info(sc,'le')
    except Exception: continue
    if not Lv or not Lv['intros']: continue
    ids=[struct.unpack_from('<I',sc[si]['data'],o+0x58)[0] for si,o in Lv['intros']]
    dup=[k for k,v in collections.Counter(ids).items() if v>1]
    if dup: bad+=1; print('DUPLICATI',os.path.basename(p),dup)
print('unita con uid duplicati:',bad)
PYEOF
