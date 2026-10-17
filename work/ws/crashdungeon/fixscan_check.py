import sys,runpy
sys.path.insert(0,'/path/to/trudlcport/tools')
import analog_idcoin as AI
mode=sys.argv[1]
sys.argv=['dlc_fix_scan.py','/path/to/trudlcport/work/ws/crashdungeon/out']
if mode=='guarded':
    with AI.guarded(): runpy.run_path('/path/to/trudlcport/tools/dlc_fix_scan.py',run_name='__main__')
else: runpy.run_path('/path/to/trudlcport/tools/dlc_fix_scan.py',run_name='__main__')
