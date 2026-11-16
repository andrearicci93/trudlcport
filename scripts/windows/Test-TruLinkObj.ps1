<#
.SYNOPSIS
    Offline test of the TruLink 0.4 / 0.5 object decoders (obj.near / obj.info / uber.events / obj.refs / physics
    body / joint / sticky) on a full tru.exe minidump, and of TruLink's byte check rows against tru.exe and the dump.

.DESCRIPTION
    Builds src\asi\TruLink\selftest\TruLinkObjTest.cpp (the same decoder header TruLinkObj.h as TruLink.asi, with a
    minidump / PE reader instead of live memory) with the Visual Studio x86 toolchain, then runs it read-only:
      - 'checks' against the exe (-Exe) and against the dump's image memory,
      - each -Command line on the dump (default: near 15, near 60 uber, info player).
    Nothing is written but the build output (-OutDir) and the log <workspace>\logs\Test-TruLinkObj_<time>.log, which
    holds every answer. No game, no process is touched. -Verbose shows the steps, -Debug the tool output lines, -Trace
    adds a PowerShell line trace.

.PARAMETER Dump
    Full minidump of tru.exe (the Windows crash dump folder, file tru.exe.<pid>.dmp).

.PARAMETER Exe
    The PC tru.exe for the byte checks (default: the workspace copy work\rebuild\exe\tru.exe when it exists).

.PARAMETER Command
    Decoder commands for the dump, one string each (or several in one string, separated by ';'):
    'near [m] [filter] [max n]', 'info <id>', 'events <id> [all]', 'refs <id>', 'body <id>', 'joint <id> <index>',
    'sticky <owner> <key>'.

.EXAMPLE
    .\scripts\windows\Test-TruLinkObj.ps1 -Dump .\tru.exe.26292.dmp -Command 'near 15', 'info 4820', 'events 4835'
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Dump,
    [string]$Exe,
    [string[]]$Command = @('near 15', 'near 60 uber', 'info player'),
    [string]$OutDir,
    [string]$VsPath = (Join-Path ${env:ProgramFiles} 'Microsoft Visual Studio\2022\Community'),
    [switch]$Trace
)

$ErrorActionPreference = 'Stop'
if ($PSBoundParameters.ContainsKey('Debug')) { $DebugPreference = 'Continue' }
Import-Module (Join-Path $PSScriptRoot 'TruCommon.psm1') -Force -Verbose:$false

$paths = Get-TruWorkspacePath -ScriptRoot $PSScriptRoot
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$outDir = if ($OutDir) { $OutDir } else { Join-Path $repo 'work\asi\trulink05_test' }
$logDir = $paths.Logs
New-Item -ItemType Directory -Force -Path $outDir, $logDir | Out-Null
$logFile = Join-Path $logDir ('Test-TruLinkObj_{0}.log' -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
Set-TruLogFile -Path $logFile
if (!$Exe) { $Exe = Join-Path $repo 'work\rebuild\exe\tru.exe' }

function Invoke-Tool {
    param([string]$Path, [string[]]$Arguments)
    Write-Log ('> {0} {1}' -f (Split-Path -Leaf $Path), ($Arguments -join ' ')) -Level VERBOSE
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $lines = & $Path @Arguments 2>&1 | ForEach-Object { [string]$_ }
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previous
    }
    foreach ($line in $lines) { Write-Log $line -Level DEBUG }
    return [pscustomobject]@{ Code = $code; Lines = $lines }
}

if ($Trace) { Set-PSDebug -Trace 1 }
$failed = 0
try {
    Write-Log "Test-TruLinkObj dump=$Dump exe=$Exe log=$logFile" -Level VERBOSE
    if (!(Test-Path -LiteralPath $Dump -PathType Leaf)) { throw "Dump not found: $Dump" }
    $source = Join-Path $repo 'src\asi\TruLink\selftest\TruLinkObjTest.cpp'
    $vcvars = Join-Path $VsPath 'VC\Auxiliary\Build\vcvarsall.bat'
    if (!(Test-Path -LiteralPath $vcvars)) { throw "vcvarsall.bat not found: $vcvars (-VsPath)" }
    $exeOut = Join-Path $outDir 'TruLinkObjTest.exe'
    $obj = Join-Path $outDir 'TruLinkObjTest.obj'
    $cmd = 'call "{0}" amd64_x86 >nul && cl /nologo /O2 /MT /W4 /EHsc /DNDEBUG "{1}" /Fo"{2}" /Fe"{3}" /link /NOLOGO kernel32.lib' -f $vcvars, $source, $obj, $exeOut
    $build = Invoke-Tool -Path 'cmd.exe' -Arguments @('/c', $cmd)
    $warnings = @($build.Lines | Where-Object { $_ -match 'warning C\d+' })
    foreach ($w in $warnings) { Write-Log "build: $w" -Level WARN }
    if ($build.Code -ne 0 -or !(Test-Path -LiteralPath $exeOut)) { throw "Build failed (exit code $($build.Code)), see $logFile" }
    Write-Log ('Built {0} ({1} warnings)' -f $exeOut, $warnings.Count)

    $runs = @()
    if (Test-Path -LiteralPath $Exe -PathType Leaf) { $runs += , @('--exe', $Exe, 'checks') }
    else { Write-Log "exe not found ($Exe) - byte checks only against the dump" -Level WARN }
    $runs += , @('--dump', $Dump, 'checks')
    # -File passes an array as one string: commands may also be separated by ';'
    $commands = @($Command | ForEach-Object { $_ -split '[;,]' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    foreach ($c in $commands) { $runs += , (@('--dump', $Dump) + @($c -split '\s+' | Where-Object { $_ })) }
    foreach ($run in $runs) {
        $result = Invoke-Tool -Path $exeOut -Arguments $run
        Write-Log ('=== {0} -> exit {1}' -f ($run[2..($run.Count - 1)] -join ' '), $result.Code)
        foreach ($line in $result.Lines) { Write-Log $line }
        if ($result.Code -ne 0) { $failed++ }
    }
    Write-Log ('{0} run(s), {1} with a non-zero exit code' -f $runs.Count, $failed)
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
if ($failed) { exit 1 }
