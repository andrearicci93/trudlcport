<#
.SYNOPSIS
    Client for TruLink.asi - the live read / write channel into the running tru.exe (127.0.0.1, default port 9265).

.DESCRIPTION
    TruLink.asi (src\asi\TruLink\README.md) runs a line-based text server inside the game, bound to 127.0.0.1 only.
    This script connects to it, sends commands one per line and prints the answers:
      single-line answers start with 'ok ', 'err ' or 'pong ';
      block answers start with 'ok+ ' and end with a line holding only '.'.
    Three ways to send commands:
      -Command  one or more command lines, e.g. -Command 'read32 0xe7f144'
      -Script   a text file, one command per line (empty lines and lines starting with # are skipped)
      -Interactive  a prompt (REPL); 'quit' or an empty line followed by Ctrl+C ends it
    Every run writes <workspace>\logs\Invoke-TruLink_<time>.log with every command and answer. -Verbose shows the
    connection steps, -Debug every line sent / received, -Trace adds a PowerShell line trace.
    The script changes nothing by itself - only the commands you send do (write*, camera, post, menu; TruLink 0.4:
    obj.set, obj.undo, uber.send, sticky.set, joint.drive - each journaled with its old value, obj.journal / obj.undo).
    TruLink 0.4 object commands (game thread, src\asi\TruLink\README.md "Objects (0.4)"): obj.near [m] [filter],
    obj.info <id>, uber.events <id>, joint.get <id> <index>, sticky.get <owner> <key>; <id> = intro id,
    0x<instance>, #<list index> or player.

.PARAMETER Command
    Command line(s) to send, in order.

.PARAMETER Script
    Text file with one command per line.

.PARAMETER Interactive
    Prompt for commands until 'quit' / 'exit'.

.PARAMETER Port
    TCP port on 127.0.0.1 (TruLink.ini Port, default 9265).

.PARAMETER TimeoutSeconds
    Connect / answer timeout (default 10; game-thread commands wait up to 5 s inside the game).

.PARAMETER ScanTimeoutSeconds
    Answer timeout for the memory search commands 'scan <type> ...', 'scan next ...' and 'scan regions' of TruLink 0.3
    (default 120; TruLink stops a scan itself after ScanMaxSeconds, default 60).

.PARAMETER PassThru
    Also return the answer lines (strings) to the pipeline.

.EXAMPLE
    .\scripts\windows\Invoke-TruLink.ps1 -Command 'ping', 'status'
.EXAMPLE
    .\scripts\windows\Invoke-TruLink.ps1 -Command 'read32 0xe7f144' -PassThru
.EXAMPLE
    .\scripts\windows\Invoke-TruLink.ps1 -Interactive -Verbose
.EXAMPLE
    .\scripts\windows\Invoke-TruLink.ps1 -Script .\my-checks.txt
.EXAMPLE
    .\scripts\windows\Invoke-TruLink.ps1 -Command 'scan float range 1 1000', 'scan status'
.EXAMPLE
    .\scripts\windows\Invoke-TruLink.ps1 -Command 'obj.near 15', 'obj.info 4820', 'uber.events 4835'
.EXAMPLE
    .\scripts\windows\Invoke-TruLink.ps1 -Command 'uber.send 4835 cmd 0', 'obj.journal', 'obj.undo'
#>
[CmdletBinding(DefaultParameterSetName = 'Command')]
param(
    [Parameter(ParameterSetName = 'Command', Mandatory, Position = 0)][string[]]$Command,
    [Parameter(ParameterSetName = 'Script', Mandatory)][string]$Script,
    [Parameter(ParameterSetName = 'Interactive', Mandatory)][switch]$Interactive,
    [ValidateRange(1, 65535)][int]$Port = 9265,
    [ValidateRange(1, 600)][int]$TimeoutSeconds = 10,
    [ValidateRange(1, 3600)][int]$ScanTimeoutSeconds = 120,
    [switch]$PassThru,
    [switch]$Trace
)

$ErrorActionPreference = 'Stop'
if ($PSBoundParameters.ContainsKey('Debug')) { $DebugPreference = 'Continue' }
# shared helpers: Write-Log, Set-TruLogFile, Get-TruWorkspacePath, ...
Import-Module (Join-Path $PSScriptRoot 'TruCommon.psm1') -Force -Verbose:$false

$paths   = Get-TruWorkspacePath -ScriptRoot $PSScriptRoot
New-Item -ItemType Directory -Force -Path $paths.Logs | Out-Null
$logFile = Join-Path $paths.Logs ('Invoke-TruLink_{0}_{1}.log' -f (Get-Date -Format 'yyyyMMdd_HHmmss'), $PSCmdlet.ParameterSetName)
Set-TruLogFile -Path $logFile

$hostName = '127.0.0.1'     # TruLink binds the loopback interface only
$script:errorCount = 0
$script:answerCount = 0

function Send-TruLinkLine {
    # sends one command line and returns the answer lines (empty for blank / comment lines, which get no answer)
    param(
        [System.IO.StreamWriter]$Writer,
        [System.IO.StreamReader]$Reader,
        [string]$Line
    )
    $text = $Line.Trim()
    if (!$text -or $text.StartsWith('#')) { return ,@() }
    Write-Log ('> {0}' -f $text) -Level DEBUG
    # TruLink 0.3 memory scans can take longer than a normal answer (ScanMaxSeconds, default 60): wait at least
    # $ScanTimeoutSeconds for them
    $isScan = $text -match '^scan\s+' -and $text -notmatch '^scan\s+(list|status|clear)\b'
    if ($isScan -and $client) { $client.ReceiveTimeout = [Math]::Max($TimeoutSeconds, $ScanTimeoutSeconds) * 1000 }
    $Writer.Write($text + "`n")
    $Writer.Flush()
    $answer = New-Object System.Collections.Generic.List[string]
    try { $first = $Reader.ReadLine() }
    finally { if ($isScan -and $client) { $client.ReceiveTimeout = $TimeoutSeconds * 1000 } }
    if ($null -eq $first) { throw 'TruLink closed the connection.' }
    $answer.Add($first)
    if ($first.StartsWith('ok+')) {
        while ($true) {
            $next = $Reader.ReadLine()
            if ($null -eq $next) { throw 'TruLink closed the connection inside a block answer.' }
            if ($next -eq '.') { break }
            $answer.Add($next)
        }
    }
    foreach ($a in $answer) { Write-Log ('< {0}' -f $a) -Level DEBUG }
    $script:answerCount++
    if ($first.StartsWith('err')) { $script:errorCount++ }
    return ,$answer.ToArray()
}

function Show-Answer {
    param([string]$Sent, [string[]]$Answer)
    if (!$Answer -or $Answer.Count -eq 0) { return }
    $level = if ($Answer[0].StartsWith('err')) { 'WARN' } else { 'INFO' }
    Write-Log ('{0} -> {1}' -f $Sent.Trim(), $Answer[0]) -Level $level
    for ($i = 1; $i -lt $Answer.Count; $i++) { Write-Log ('    {0}' -f $Answer[$i]) }
}

if ($Trace) { Set-PSDebug -Trace 1 }
$client = $null
try {
    Write-Log ('Invoke-TruLink mode={0} target={1}:{2} log={3}' -f $PSCmdlet.ParameterSetName, $hostName, $Port, $logFile) -Level VERBOSE
    $lines = switch ($PSCmdlet.ParameterSetName) {
        'Command' { $Command }
        'Script' {
            if (!(Test-Path -LiteralPath $Script)) { throw "Script file not found: $Script" }
            Get-Content -LiteralPath $Script
        }
        default { @() }
    }

    $client = New-Object System.Net.Sockets.TcpClient
    $pending = $client.BeginConnect($hostName, $Port, $null, $null)
    if (!$pending.AsyncWaitHandle.WaitOne($TimeoutSeconds * 1000)) {
        throw ('No answer from {0}:{1} within {2} s - is the game running with TruLink.asi (Enabled=1)?' -f $hostName, $Port, $TimeoutSeconds)
    }
    try { $client.EndConnect($pending) }
    catch { throw ('Cannot connect to {0}:{1} ({2}) - game not running, TruLink.asi not installed / disabled, or another port in TruLink.ini?' -f $hostName, $Port, $_.Exception.InnerException.Message) }
    $client.ReceiveTimeout = $TimeoutSeconds * 1000
    $client.SendTimeout = $TimeoutSeconds * 1000
    $stream = $client.GetStream()
    $encoding = New-Object System.Text.ASCIIEncoding
    $reader = New-Object System.IO.StreamReader($stream, $encoding)
    $writer = New-Object System.IO.StreamWriter($stream, $encoding)
    Write-Log 'connected' -Level VERBOSE

    if ($PSCmdlet.ParameterSetName -eq 'Interactive') {
        Write-Host "TruLink $($hostName):$Port - 'help' lists the commands, 'quit' ends."
        while ($true) {
            $line = Read-Host 'trulink'
            if ($null -eq $line) { break }
            if (!$line.Trim()) { continue }
            $answer = Send-TruLinkLine -Writer $writer -Reader $reader -Line $line
            Show-Answer -Sent $line -Answer $answer
            if ($PassThru) { $answer }
            if ($line.Trim() -match '^(quit|exit|bye)$') { break }
        }
    }
    else {
        foreach ($line in $lines) {
            $answer = Send-TruLinkLine -Writer $writer -Reader $reader -Line ([string]$line)
            Show-Answer -Sent $line -Answer $answer
            if ($PassThru) { $answer }
            if (([string]$line).Trim() -match '^(quit|exit|bye)$') { break }
        }
    }
    $summaryLevel = if ($script:errorCount) { 'WARN' } else { 'VERBOSE' }
    Write-Log ('{0} answers, {1} of them err' -f $script:answerCount, $script:errorCount) -Level $summaryLevel
}
catch {
    Write-Log "FAILED: $($_.Exception.Message)" -Level ERROR
    Write-Log ($_.ScriptStackTrace) -Level DEBUG
    throw
}
finally {
    if ($client) { $client.Close() }
    if ($Trace) { Set-PSDebug -Off }
    Write-Host "Log: $logFile"
}
