# Copia il recomp (build + dati gioco) da Z:\Downloads\Recomp a C:\Recomp (robocopy, riprendibile). Log in C:\Recomp\rc_*.log
$s = 'Z:\Downloads\Recomp'
New-Item -ItemType Directory -Force C:\Recomp | Out-Null
robocopy "$s\underworld-xenon\build" 'C:\Recomp\underworld-xenon\build' /E /NFL /NDL /NP /LOG:C:\Recomp\rc_build.log
robocopy "$s\Tomb Raider Underworld" 'C:\Recomp\Tomb Raider Underworld' /E /NFL /NDL /NP /LOG:C:\Recomp\rc_game.log
'FINITO' | Out-File C:\Recomp\rc_done.txt
