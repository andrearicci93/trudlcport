# vm_poke.ps1 - modifica LIVE del codice del gioco in memoria (WriteProcessMemory), con verifica dei byte originali e ripristino.
# NON tocca nessun file. Le modifiche spariscono alla chiusura del gioco. PowerShell 32 bit (SysWOW64), come vm_probe.ps1.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File Z:\tru-port\tools\vm_poke.ps1 -Do status
#   ... -Do apply  -Patch los          forza FUN_00713090 (raggio di visibilita' verso il bersaglio) a restituire 1
#   ... -Do apply  -Patch valid        forza il validatore 0x6ecca0 a restituire 1
#   ... -Do apply  -Patch cand         forza FUN_00713200 (test geometrico completo) a restituire 1
#   ... -Do revert -Patch los|valid|cand|all
#
# Sicurezza: prima di scrivere legge i byte attuali e li confronta con quelli dell'exe sul disco (originale) o con la patch gia' applicata;
# se non coincidono NON scrive. Patch = 'xor eax,eax; inc eax; ret' (31 C0 40 C3): le tre funzioni sono cdecl con 'ret' semplice (verificato).
param(
  [ValidateSet('status', 'apply', 'revert', 'read', 'write', 'cfgdump', 'trace')][string]$Do = 'status',
  [string]$Addr = '', [int]$Seconds = 60, [int]$Interval = 1000, [string]$ListIdx = '1', [string]$Len = '16', [string]$Expect = '', [string]$Hex = '',
  [string]$Patch = '',
  [string]$RunId = '',
  [string]$Exe = 'Z:\tru-port\work\laa\tru_steam.exe.unpacked.exe'
)
$ErrorActionPreference = 'Stop'
$cs = @'
using System;
using System.Runtime.InteropServices;
public static class PokeNative
{
    [DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] b, IntPtr n, out IntPtr got);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool WriteProcessMemory(IntPtr h, IntPtr a, byte[] b, IntPtr n, out IntPtr got);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool VirtualProtectEx(IntPtr h, IntPtr a, IntPtr n, uint np, out uint old);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool FlushInstructionCache(IntPtr h, IntPtr a, IntPtr n);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
    public static IntPtr Open(uint pid) { return OpenProcess(0x0008 | 0x0010 | 0x0020 | 0x0400, false, pid); }   // VM_OPERATION|VM_READ|VM_WRITE|QUERY_INFORMATION
    public static void Close(IntPtr h) { CloseHandle(h); }
    public static byte[] Read(IntPtr h, uint va, int n)
    {
        byte[] b = new byte[n]; IntPtr got;
        if (!ReadProcessMemory(h, new IntPtr(unchecked((int)va)), b, new IntPtr(n), out got) || got.ToInt64() != n) return null;
        return b;
    }
    public static bool Write(IntPtr h, uint va, byte[] b)
    {
        IntPtr a = new IntPtr(unchecked((int)va)); uint old, tmp; IntPtr got;
        if (!VirtualProtectEx(h, a, new IntPtr(b.Length), 0x40, out old)) return false;      // PAGE_EXECUTE_READWRITE
        bool ok = WriteProcessMemory(h, a, b, new IntPtr(b.Length), out got) && got.ToInt64() == b.Length;
        VirtualProtectEx(h, a, new IntPtr(b.Length), old, out tmp);
        FlushInstructionCache(h, a, new IntPtr(b.Length));
        return ok;
    }
}
'@
Add-Type -TypeDefinition $cs

$patches = @{
  los   = @{ va = 0x713090; new = '31C040C3'; note = 'FUN_00713090 raggio di visibilita'' -> 1' }
  valid = @{ va = 0x6ecca0; new = '31C040C3'; note = 'validatore 0x6ecca0 -> 1' }
  cand  = @{ va = 0x713200; new = '31C040C3'; note = 'FUN_00713200 test geometrico -> 1' }
}
function HexToBytes([string]$h) { $b = New-Object byte[] ($h.Length / 2); for ($i = 0; $i -lt $b.Length; $i++) { $b[$i] = [Convert]::ToByte($h.Substring(2 * $i, 2), 16) }; $b }
function BytesToHex([byte[]]$b) { if ($null -eq $b) { return 'NA' }; (($b | ForEach-Object { $_.ToString('X2') }) -join '') }

$p = Get-Process -Name tru -ErrorAction SilentlyContinue | Select-Object -First 1
if ($null -eq $p) { Write-Output 'NO_PROCESS: tru non e'' in esecuzione'; exit 2 }
if ($p.MainModule.FileVersionInfo -and $p.MainModule.BaseAddress.ToInt64() -ne 0x400000) { Write-Output ('BASE_INATTESA ' + $p.MainModule.BaseAddress); exit 3 }
$disk = [IO.File]::ReadAllBytes($Exe)
$h = [PokeNative]::Open([uint32]$p.Id)
if ($h -eq [IntPtr]::Zero) { Write-Output 'OPENPROCESS_FALLITO'; exit 4 }
$log = $null
if ($RunId -ne '') { $log = ('Z:\tru-port\work\runs\{0}\poke.log' -f $RunId) }
function Say([string]$m) { $line = ('{0:HH:mm:ss.fff} {1}' -f (Get-Date), $m); Write-Output $line; if ($log) { try { Add-Content -LiteralPath $log -Value $line } catch {} } }
try {
  if ($Do -eq 'trace') {
    # Traccia la posizione di Lara (+0x20 dell'oggetto [0xe7f094]) e la distanza dall'anello 9755 (world fisso -268.2,5087,-13712): una riga ogni -Interval ms per -Seconds s.
    $ring = @(-268.2, 5086.6, -13712.1); $t0 = Get-Date
    while (((Get-Date) - $t0).TotalSeconds -lt $Seconds) {
      $lp = [PokeNative]::Read($h, 0xe7f094, 4)
      if ($null -ne $lp) {
        $ptr = [BitConverter]::ToUInt32($lp, 0); $pp = if ($ptr -ne 0) { [PokeNative]::Read($h, $ptr + 0x20, 12) } else { $null }
        if ($null -ne $pp) {
          $x = [BitConverter]::ToSingle($pp, 0); $y = [BitConverter]::ToSingle($pp, 4); $z = [BitConverter]::ToSingle($pp, 8)
          $d = [Math]::Sqrt([Math]::Pow($x - $ring[0], 2) + [Math]::Pow($y - $ring[1], 2) + [Math]::Pow($z - $ring[2], 2))
          Say ('LARA {0:F1} {1:F1} {2:F1} dist_anello={3:F0}' -f $x, $y, $z, $d)
        }
      }
      Start-Sleep -Milliseconds $Interval
      if ($null -eq (Get-Process -Id $p.Id -ErrorAction SilentlyContinue)) { Say 'tru terminato'; break }
    }
    return
  }
  if ($Do -eq 'cfgdump') {
    # Tabella dei filtri di mira della lista -ListIdx (default 1 = rampino): mgr=[0xfadfac]; L=[mgr+4*i]; cfg=[L+0x34]; N=[cfg+4];
    # gruppo k=[cfg+8+4k] (+4 = n condizioni, +8 byte); condizione j=[gruppo+0xc+4j]: u16 tipo @0, float soglia @+4, poi 0x20 byte grezzi.
    function RU([uint32]$a) { $b = [PokeNative]::Read($h, $a, 4); if ($null -eq $b) { return [uint32]0 }; [BitConverter]::ToUInt32($b, 0) }
    function RF([uint32]$a) { $b = [PokeNative]::Read($h, $a, 4); if ($null -eq $b) { return [single]::NaN }; [BitConverter]::ToSingle($b, 0) }
    $mgr = RU 0xfadfac; $L = RU ($mgr + 4 * [int]$ListIdx); $cfg = RU ($L + 0x34)
    Say ('mgr={0:X} lista{1}={2:X} cfg={3:X}' -f $mgr, $ListIdx, $L, $cfg)
    if ($cfg -eq 0) { Say 'cfg nullo'; return }
    $N = RU ($cfg + 4); Say ('N filtri (sotto-liste valutate) = {0}' -f $N)
    for ($k = 0; $k -lt [Math]::Min($N, 16); $k++) {
      $g = RU ($cfg + 8 + 4 * $k); $nc = RU ($g + 4); $gb = [PokeNative]::Read($h, $g + 8, 1)
      Say ('  gruppo {0} @{1:X}: n condizioni={2} byte8={3}' -f $k, $g, $nc, $gb[0])
      for ($j = 0; $j -lt [Math]::Min($nc, 12); $j++) {
        $c = RU ($g + 0xc + 4 * $j); $tb = [PokeNative]::Read($h, $c, 2); $type = [BitConverter]::ToUInt16($tb, 0)
        Say ('    cond {0} @{1:X} tipo={2} soglia(float @+4 = {3:X})={4}  raw={5}' -f $j, $c, $type, ($c + 4), (RF ($c + 4)), (BytesToHex ([PokeNative]::Read($h, $c, 0x20))))
      }
    }
    return
  }
  if ($Do -eq 'read' -or $Do -eq 'write') {
    # lettura/scrittura DATI mirata: -Addr 0x... [-Len n] ; write: -Expect <hex attuale atteso> -Hex <nuovo>. Rifiuta se i byte attuali non coincidono con Expect.
    $va = [Convert]::ToUInt32($Addr.Replace('0x', ''), 16)
    if ($Do -eq 'read') { $n = [int]$Len; Say ('READ @{0:X} {1}' -f $va, (BytesToHex ([PokeNative]::Read($h, $va, $n)))); return }
    if ($Expect -eq '' -or $Hex -eq '' -or $Expect.Length -ne $Hex.Length) { Say 'write richiede -Expect e -Hex della stessa lunghezza'; exit 5 }
    $cur = [PokeNative]::Read($h, $va, $Hex.Length / 2)
    if ((BytesToHex $cur) -ne $Expect.ToUpper()) { Say ('WRITE @{0:X} RIFIUTATO: attuale {1} != atteso {2}' -f $va, (BytesToHex $cur), $Expect.ToUpper()); exit 6 }
    $ok = [PokeNative]::Write($h, $va, (HexToBytes $Hex)); $chk = [PokeNative]::Read($h, $va, $Hex.Length / 2)
    Say ('WRITE @{0:X} {1} -> {2}: write={3} verifica={4}' -f $va, $Expect.ToUpper(), $Hex.ToUpper(), $ok, (BytesToHex $chk)); return
  }
  $names = @($patches.Keys | Sort-Object)
  if ($Patch -ne '' -and $Patch -ne 'all') { $names = @($Patch -split ',') }
  foreach ($n in $names) {
    if (-not $patches.ContainsKey($n)) { Say ('PATCH_SCONOSCIUTA ' + $n); continue }
    $pt = $patches[$n]; $va = [uint32]$pt.va; $new = HexToBytes $pt.new; $len = $new.Length
    $orig = New-Object byte[] $len; [Array]::Copy($disk, [int]($va - 0x400000), $orig, 0, $len)
    $cur = [PokeNative]::Read($h, $va, $len)
    $state = if ($null -eq $cur) { 'ILLEGGIBILE' } elseif ((BytesToHex $cur) -eq (BytesToHex $orig)) { 'ORIGINALE' } elseif ((BytesToHex $cur) -eq (BytesToHex $new)) { 'PATCHATO' } else { 'DIVERSO' }
    if ($Do -eq 'status') { Say ('{0,-6} @{1:X} {2} (attuale {3}, originale {4}) - {5}' -f $n, $va, $state, (BytesToHex $cur), (BytesToHex $orig), $pt.note); continue }
    if ($state -eq 'DIVERSO' -or $state -eq 'ILLEGGIBILE') { Say ('{0} @{1:X} STATO {2}: NON scrivo (attuale {3})' -f $n, $va, $state, (BytesToHex $cur)); continue }
    $want = if ($Do -eq 'apply') { $new } else { $orig }
    if ((BytesToHex $cur) -eq (BytesToHex $want)) { Say ('{0} gia'' {1}' -f $n, $(if ($Do -eq 'apply') { 'PATCHATO' } else { 'ORIGINALE' })); continue }
    $ok = [PokeNative]::Write($h, $va, $want)
    $chk = [PokeNative]::Read($h, $va, $len)
    Say ('{0} {1} @{2:X}: write={3} verifica={4} ({5})' -f $Do.ToUpper(), $n, $va, $ok, $(if ((BytesToHex $chk) -eq (BytesToHex $want)) { 'OK' } else { 'KO' }), (BytesToHex $chk))
  }
}
finally { [PokeNative]::Close($h) }
