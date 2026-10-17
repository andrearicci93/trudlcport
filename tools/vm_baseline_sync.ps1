# Allinea mods\ della VM a una baseline congelata, in modo RIPETIBILE.
#   -Mode dryrun  (default) non cambia nulla: elenca differenze
#   -Mode verify  come dryrun, ma md5 di TUTTI i file (lento) e exit code 1 se differisce
#   -Mode apply   copia i file mancanti/diversi dalla baseline; i file in piu' in mods\ vengono SPOSTATI in
#                 <gioco>\mods_quarantine\<timestamp>\ (mai cancellati); poi verifica md5 dei file critici
#   -RestoreSave <nome>  copia saves\<nome>\* della baseline in Documents\Eidos\Tomb Raider - Underworld (backup prima)
# uso: powershell -NoProfile -ExecutionPolicy Bypass -File Z:\tru-port\tools\vm_baseline_sync.ps1 -Baseline B1 -Mode dryrun
param([string]$Baseline = 'B1', [ValidateSet('dryrun', 'verify', 'apply')][string]$Mode = 'dryrun', [string]$RestoreSave = '')
$ErrorActionPreference = 'Stop'
$g = 'C:\Program Files (x86)\Steam\steamapps\common\Tomb Raider Underworld'
$mods = "$g\mods"
$b = "Z:\tru-port\work\baseline\$Baseline"
if (-not (Test-Path "$b\manifest.tsv")) { throw "baseline non trovata: $b" }
$id = (Get-Content "$b\id.txt" -Raw).Trim()
$man = Get-Content "$b\manifest.tsv" | Select -Skip 1 | % { $p = $_ -split "`t"; [pscustomobject]@{ rel = $p[0]; size = [int64]$p[1]; md5 = $p[2]; crit = ($p[4] -eq '1') } }
function Md5($f) { (Get-FileHash $f -Algorithm MD5).Hash.ToLower() }
$missing = @(); $diff = @(); $ok = 0
$want = @{}
foreach ($m in $man) {
    $want[$m.rel.ToLower().Replace('/', '\')] = $true
    $f = Join-Path $mods ($m.rel.Replace('/', '\'))
    if (-not (Test-Path $f)) { $missing += $m.rel; continue }
    if ((Get-Item $f).Length -ne $m.size) { $diff += $m.rel; continue }
    if ($Mode -eq 'verify' -or $m.crit) { if ((Md5 $f) -ne $m.md5) { $diff += $m.rel; continue } }
    $ok++
}
$extra = @()
Get-ChildItem $mods -Recurse -File -Force | % { $r = $_.FullName.Substring($mods.Length + 1); if (-not $want.ContainsKey($r.ToLower())) { $extra += $r } }
"baseline $id  modo=$Mode  ok=$ok mancanti=$($missing.Count) diversi=$($diff.Count) extra=$($extra.Count)"
$missing | % { "  MANCA   $_" }; $diff | % { "  DIVERSO $_" }; $extra | % { "  EXTRA   $_" }
if ($Mode -eq 'apply') {
    $q = "$g\mods_quarantine\$(Get-Date -Format yyyyMMdd_HHmmss)"
    foreach ($e in $extra) { $t = Join-Path $q $e; New-Item -ItemType Directory -Force (Split-Path $t) | Out-Null; Move-Item (Join-Path $mods $e) $t }
    foreach ($r in ($missing + $diff)) {
        $t = Join-Path $mods ($r.Replace('/', '\')); New-Item -ItemType Directory -Force (Split-Path $t) | Out-Null
        Copy-Item (Join-Path "$b\mods" ($r.Replace('/', '\'))) $t -Force
    }
    $bad = 0
    foreach ($m in $man) { if ($m.crit) { $f = Join-Path $mods ($m.rel.Replace('/', '\')); if (-not (Test-Path $f) -or (Md5 $f) -ne $m.md5) { $bad++; "  POST-VERIFICA FALLITA $($m.rel)" } } }
    "apply fatto: copiati=$($missing.Count + $diff.Count) in quarantena=$($extra.Count) verifica critici fallita=$bad"
    if ($bad) { exit 2 }
    New-Item -ItemType Directory -Force -Path 'C:\TRU_state' | Out-Null; Set-Content -LiteralPath 'C:\TRU_state\baseline.txt' -Value $id -Encoding ASCII
}
if ($RestoreSave) {
    $sv = "$env:USERPROFILE\Documents\Eidos\Tomb Raider - Underworld"
    $src = "$b\saves\$RestoreSave"; if (-not (Test-Path $src)) { throw "save non trovato: $src" }
    $bk = "Z:\tru-port\work\runs\_save_backups\$(Get-Date -Format yyyyMMdd_HHmmss)"; New-Item -ItemType Directory -Force $bk | Out-Null
    if (Test-Path $sv) { Copy-Item "$sv\*" $bk -Recurse -Force }
    if ($Mode -eq 'dryrun') { "save: DRYRUN: copierei $src -> $sv (backup in $bk)" } else {
        Copy-Item "$src\*" $sv -Force; "save $RestoreSave ripristinato (backup attuale in $bk)" }
}
if ($Mode -eq 'verify' -and ($missing.Count + $diff.Count + $extra.Count)) { exit 1 }
