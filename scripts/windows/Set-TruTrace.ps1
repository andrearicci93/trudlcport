<#
.SYNOPSIS
    Installs or removes TruTrace.asi (log-only diagnostics: sound start / end, teleport + chart state, 0x1f4 / 0x1f5
    receivers, spawn requests, object 858, TimeVector) next to tru.exe.

.DESCRIPTION
    -Install copies TruTrace.asi (built by Build-TruAsi.ps1 -Name TruTrace -OutDir ...) and its sample .ini from
             -SourceDir (default <workspace>\work\asi) into the game folder; the Ultimate ASI Loader the game ships as
             binkw32.dll loads every *.asi there.
    -Remove  deletes them again - only if they are ours: the same SHA-256 as a TruTrace.asi / .ini built anywhere below
             <workspace>\work\asi (e.g. work\asi\trace01) or one of our released builds listed in $earlierBuilds; a
             foreign file of the same name is never overwritten or removed. TruTrace.log is left in place. Nothing
             installed = nothing to do (no error), so the test harness may call -Remove for every profile.
    -Install over an earlier build of ours replaces it (update); an .ini the owner edited is not ours and is kept
             (the plugin's built-in defaults cover options it lacks).
    The plugin changes nothing in the game (hooks log and continue). It must load after the other Tru*.asi
    (alphabetical order of the loader): TruShadowPower and TruMenu byte-check sites TruTrace hooks at their own load
    (docs\Befund-TruTrace-0411b.md section 3). The game must not be running. Every run writes
    <workspace>\logs\Set-TruTrace_<time>.log. -Verbose shows the steps, -Debug the hashes, -Trace adds a PowerShell
    line trace.

.PARAMETER GamePath
    Game folder; default: found through the Steam libraries.

.PARAMETER SourceDir
    Folder with the built TruTrace.asi / .ini (default <workspace>\work\asi).

.EXAMPLE
    .\Set-TruTrace.ps1 -Install -SourceDir ..\..\work\asi\trace01 -Verbose
    .\Set-TruTrace.ps1 -Remove
#>
[CmdletBinding(DefaultParameterSetName = 'Install')]
param(
    [Parameter(ParameterSetName = 'Install', Mandatory)][switch]$Install,
    [Parameter(ParameterSetName = 'Remove', Mandatory)][switch]$Remove,
    [string]$GamePath,
    [string]$SourceDir,
    [switch]$Trace
)

$ErrorActionPreference = 'Stop'
if ($PSBoundParameters.ContainsKey('Debug')) { $DebugPreference = 'Continue' }
# shared helpers: Write-Log, Set-TruLogFile, Get-TruWorkspacePath, Find-TruGamePath, ...
Import-Module (Join-Path $PSScriptRoot 'TruCommon.psm1') -Force -Verbose:$false

$paths   = Get-TruWorkspacePath -ScriptRoot $PSScriptRoot
$repo    = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$asiRoot = Join-Path $repo 'work\asi'
$built   = if ($SourceDir) { $SourceDir } else { $asiRoot }
$names   = 'TruTrace.asi', 'TruTrace.ini'
# released builds of ours (SHA-256), recognised even when their output folder below work\asi is gone
$earlierBuilds = @{
    'TruTrace.asi' = @('41104b543c26932a4c593b596af8aa3b4e74bb26b31687860aff0b9061e7227b',    # 0.1 (work\asi\trace01)
                       '6f9bc97bcf55b85af75ec3d56d5972c7033b587a95c29ee34a82c834974b9fed',    # 0.3 (work\asi\trace03, installed 2026-11-05; its export still said 0.2)
                       '8456a9895fa9eac3e9a68aea7f9809b6e2c798952eaa62f902136c86fb58c86a',    # 0.3.1 dated log lines (work\asi\i_1211\TruTrace)
                       '60ecf445a5bb30abed853ab34fa504b41bbd642ed5da157656305c51a328b634',    # 0.3.2 ProgressFilter, stale machines, ground (work\asi\trace032)
                       'eb3a3b4433683ffa9f825dd0534752b832d76d2377e3e7d61ec6dc5a254ee123')    # 0.3.3 ModelInst, NullModel guard (work\asi\trutrace033, current)
    'TruTrace.ini' = @('c30ca6d7674de028a2673812c0ea2963276b8e08a3d11aa4d4680b50e55c8e0a',    # 0.1 sample .ini
                       '2c45862aefef18be0418c6dc3f993287a47c0a0f6cc216e44e0dd44ba13bd661',    # sample .ini of 0.3 / 0.3.1
                       '1c815eef07a4dee4d9b25c42417cf2a3357e5afdea6b121e6123fed08d4921a3',    # sample .ini of 0.3.2
                       '832dcef1377b425e0a33dff8bae76b25443864bfa4f491af95cd9b7b60074fe0')    # sample .ini of 0.3.3
}
$logDir  = $paths.Logs
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir ('Set-TruTrace_{0}_{1}.log' -f (Get-Date -Format 'yyyyMMdd_HHmmss'), $PSCmdlet.ParameterSetName)
Set-TruLogFile -Path $logFile

function Get-Sha256 {
    param([string]$Path)
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLower()
}

# SHA-256 of every build of ours: the released ones in $earlierBuilds and every build below work\asi, per file name
function Get-OwnHashes {
    param([string]$Name)
    $hashes = @($earlierBuilds[$Name])
    if (Test-Path -LiteralPath $asiRoot) {
        foreach ($f in @(Get-ChildItem -LiteralPath $asiRoot -Recurse -File -Filter $Name -ErrorAction SilentlyContinue)) {
            $hashes += Get-Sha256 $f.FullName
            Write-Log "own build $($f.FullName)" -Level DEBUG
        }
    }
    return , $hashes
}

if ($Trace) { Set-PSDebug -Trace 1 }
try {
    Write-Log "Set-TruTrace mode=$($PSCmdlet.ParameterSetName) log=$logFile" -Level VERBOSE
    if (Get-Process -Name 'tru' -ErrorAction SilentlyContinue) { throw 'Tomb Raider: Underworld is running. Please close it first.' }
    if (!$GamePath) { $GamePath = Find-TruGamePath }
    if (!$GamePath -or !(Test-Path -LiteralPath (Join-Path $GamePath 'tru.exe'))) { throw "Game folder not found (-GamePath): $GamePath" }
    Write-Log "Game folder: $GamePath" -Level VERBOSE

    foreach ($name in $names) {
        $source = Join-Path $built $name
        $target = Join-Path $GamePath $name
        $targetHash = if (Test-Path -LiteralPath $target) { Get-Sha256 $target } else { $null }
        if ($targetHash) { Write-Log "$name installed sha256 $targetHash" -Level DEBUG }
        if ($Remove) {
            if (!$targetHash) { Write-Log "$name not in the game folder." -Level VERBOSE; continue }
            $own = Get-OwnHashes $name
            if ($own -notcontains $targetHash) { Write-Log "$target is not a build of ours - left untouched." -Level WARN; continue }
            Remove-Item -LiteralPath $target
            Write-Log "$name removed from $GamePath."
            continue
        }
        if (!(Test-Path -LiteralPath $source)) { throw "$source not found (run Build-TruAsi.ps1 -Name TruTrace first)." }
        $sourceHash = Get-Sha256 $source
        Write-Log "$name built sha256 $sourceHash" -Level DEBUG
        if ($targetHash -eq $sourceHash) { Write-Log "$name already installed."; continue }
        $isOwn = $targetHash -and ((Get-OwnHashes $name) -contains $targetHash)
        if ($targetHash -and !$isOwn) {
            if ($name -like '*.ini') { Write-Log "$target was edited (not a build of ours) - kept." -Level WARN; continue }
            throw "$target exists and is not a build of ours - left untouched."
        }
        Copy-Item -LiteralPath $source -Destination $target -Force
        if ($isOwn) { Write-Log "$name updated in $GamePath (earlier build replaced)." }
        else { Write-Log "$name copied to $target." }
    }
}
catch {
    Write-Log "FAILED: $($_.Exception.Message)" -Level ERROR
    Write-Log ($_.ScriptStackTrace) -Level DEBUG
    throw
}
finally {
    if ($Trace) { Set-PSDebug -Off }
    Write-Host "Log: $logFile"
}
