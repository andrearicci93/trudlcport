# vm_probe_raft_lib.ps1 - reusable read-only probe functions for the running 32-bit tru.exe (TRU DLC1 raft/chain-shot diagnosis).
# (Renamed from vm_probe_lib.ps1, which now belongs to the runner.) Dot-source it:  . Z:\tru-port\tools\vm_probe_raft_lib.ps1
# then:  $rc = @(Invoke-TruProbe -Mode raft -Seconds 120 -RunId r1)[-1]
# Use with the 32-bit PowerShell (C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe); also works from 64-bit.
# READ ONLY: OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION = 0x0410) + ReadProcessMemory. Nothing is ever written into the process.
# Spec: work/ws/chainshot/INSTRUMENT_SPEC.md. Offsets/addresses are from that spec (static analysis, NOT yet verified in-game).
# Exit codes of Invoke-TruProbe: 0 ok/clean end (also when the process dies), 1 fatal, 2 no tru process, 3 OpenProcess failed, 4 image check failed, 5 mode lists: no aim-list manager.

$script:ProbeVersion = '1'

function Initialize-TruProbeNative {
  if ('TruProbeNative' -as [type]) { return }
  $src = @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public class TruProbeNative {
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr OpenProcess(uint a, bool i, uint pid);
  [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool ReadProcessMemory(IntPtr h, UIntPtr a, byte[] b, UIntPtr n, out UIntPtr r);
  IntPtr H = IntPtr.Zero;
  Dictionary<long,long> defCache = new Dictionary<long,long>();
  public long[] Out = new long[0];
  public long LastCount = 0;
  public bool Open(int pid) { H = OpenProcess(0x0410, false, (uint)pid); return H != IntPtr.Zero; }
  public void Close() { if (H != IntPtr.Zero) { CloseHandle(H); H = IntPtr.Zero; } }
  public void ClearCache() { defCache.Clear(); }
  public byte[] Read(long a, int n) {
    if (H == IntPtr.Zero || a < 0x10000 || a + n > 0x100000000L) return null;
    byte[] b = new byte[n]; UIntPtr r;
    if (!ReadProcessMemory(H, new UIntPtr((ulong)a), b, new UIntPtr((uint)n), out r)) return null;
    if (r.ToUInt64() != (ulong)n) return null;
    return b;
  }
  // all readers return -1 on failure (valid u32 values are 0..0xFFFFFFFF, so -1 is unambiguous)
  public long U32(long a) { byte[] b = Read(a, 4); if (b == null) return -1; return (long)BitConverter.ToUInt32(b, 0); }
  public long U16(long a) { byte[] b = Read(a, 2); if (b == null) return -1; return (long)BitConverter.ToUInt16(b, 0); }
  public long U8(long a) { byte[] b = Read(a, 1); if (b == null) return -1; return (long)b[0]; }
  public string F32s(long a) {
    byte[] b = Read(a, 4); if (b == null) return "NA";
    float f = BitConverter.ToSingle(b, 0);
    return f.ToString("R", System.Globalization.CultureInfo.InvariantCulture);
  }
  public string Ascii(long a, int max) {
    StringBuilder sb = new StringBuilder();
    for (int i = 0; i < max; i++) {
      byte[] b = Read(a + i, 1);
      if (b == null || b[0] == 0) break;
      if (b[0] < 32 || b[0] > 126) return null;
      sb.Append((char)b[0]);
    }
    if (sb.Length == 0) return null;
    return sb.ToString();
  }
  // MSVC RTTI: [inst]=vtable, [vtable-4]=COL, [COL+12]=TypeDescriptor, TD+8 = ".?AVname@@"
  public string Rtti(long inst) {
    long vt = U32(inst); if (vt <= 4) return null;
    long col = U32(vt - 4); if (col <= 0) return null;
    long td = U32(col + 12); if (td <= 0) return null;
    string s = Ascii(td + 8, 100);
    if (s == null || !s.StartsWith(".?A")) return null;
    return s;
  }
  // Walk the global instance list (head cell address, next=+8, def=+0x10, def->uniqueID=+0x14).
  // Results in Out as triples (inst, def, objUniqueID); returns the number of triples. LastCount = nodes visited.
  public int Walk(long head, int max, long uidA, long uidB, bool all) {
    List<long> res = new List<long>();
    long p = U32(head); int c = 0;
    while (p > 0 && c < max) {
      byte[] b = Read(p, 0x18); if (b == null) break;
      long next = (long)BitConverter.ToUInt32(b, 8);
      long def = (long)BitConverter.ToUInt32(b, 0x10);
      long uid = -1;
      if (def > 0) { if (!defCache.TryGetValue(def, out uid)) { uid = U32(def + 0x14); defCache[def] = uid; } }
      if (all || uid == uidA || uid == uidB) { res.Add(p); res.Add(def); res.Add(uid); }
      p = next; c++;
    }
    LastCount = c; Out = res.ToArray();
    return res.Count / 3;
  }
  // Aim list i of the manager array (as work/ws/aim/lists.py). Out = septuples (headIdx, node, inst, serial, id, act, valid).
  // Returns number of nodes, or -1 if the list pointer is null/unreadable.
  public int ListNodes(long mgr, int i, int cap) {
    List<long> res = new List<long>(); Out = new long[0];
    long L = U32(mgr + 4 * i); if (L <= 0) return -1;
    long c34 = U32(L + 0x34); long n = 0;
    if (c34 > 0) { long nb = U8(c34 + 4); if (nb > 0) n = nb; }
    if (n > 16) n = 16;
    long basep = U32(L + 0x38);
    for (int k = 0; k <= n; k++) {
      long nd;
      if (k < n) nd = (basep > 0) ? U32(basep + 20 * k) : 0; else nd = U32(L + 0x3c);
      int c = 0;
      while (nd > 0 && c < cap) {
        long ins = U32(nd + 8), ser = U32(nd + 12), id = U32(nd + 0x14), act = U32(nd + 0x18);
        long valid = 0;
        if (ins > 0) { long s2 = U32(ins + 0x44); if (s2 >= 0 && s2 == ser) valid = 1; }
        res.Add(k); res.Add(nd); res.Add(ins); res.Add(ser); res.Add(id); res.Add(act); res.Add(valid);
        nd = U32(nd + 4); c++;
      }
    }
    Out = res.ToArray();
    return res.Count / 7;
  }
}
'@
  Add-Type -TypeDefinition $src -Language CSharp
}

function TruHex($v) { if ($v -lt 0) { return 'NA' } return ('0x{0:x}' -f $v) }

function Get-TruImageInfo {
  # Verifies MZ/PE header at the module base of the target (must be a 32-bit PE).
  param($N, $proc)
  $info = @{ Ok = $false; Base = 0x400000L; BaseSrc = 'assumed'; PreferredBase = -1L; Machine = -1L; Msg = '' }
  try { $info.Base = [long]$proc.MainModule.BaseAddress.ToInt64(); $info.BaseSrc = 'MainModule' } catch { $info.BaseSrc = 'assumed(MainModule failed)' }
  $b = $info.Base
  $mz = $N.U16($b)
  if ($mz -ne 0x5a4d) { $info.Msg = ('no MZ at base {0}: got {1}' -f (TruHex $b), (TruHex $mz)); return $info }
  $lf = $N.U32($b + 0x3c)
  if ($lf -le 0 -or $lf -gt 0x1000) { $info.Msg = ('bad e_lfanew {0}' -f (TruHex $lf)); return $info }
  $sig = $N.U32($b + $lf)
  if ($sig -ne 0x00004550) { $info.Msg = ('no PE signature at {0}: got {1}' -f (TruHex ($b + $lf)), (TruHex $sig)); return $info }
  $info.Machine = $N.U16($b + $lf + 4)
  $magic = $N.U16($b + $lf + 0x18)
  $info.PreferredBase = $N.U32($b + $lf + 0x34)
  if ($info.Machine -ne 0x14c -or $magic -ne 0x10b) { $info.Msg = ('not PE32/i386: machine={0} optmagic={1}' -f (TruHex $info.Machine), (TruHex $magic)); return $info }
  $info.Ok = $true
  $info.Msg = ('MZ/PE ok, i386, PE32, header ImageBase={0}' -f (TruHex $info.PreferredBase))
  return $info
}

function Get-TruProcess {
  param([int]$ProcId, [int]$WaitSec)
  $t0 = Get-Date
  while ($true) {
    $p = $null
    if ($ProcId -gt 0) { $p = Get-Process -Id $ProcId -ErrorAction SilentlyContinue }
    else { $p = Get-Process -Name tru -ErrorAction SilentlyContinue | Select-Object -First 1 }
    if ($p) { return $p }
    if (((Get-Date) - $t0).TotalSeconds -ge $WaitSec) { return $null }
    Start-Sleep -Milliseconds 500
  }
}

function New-TruProbeWriter {
  param([string]$Path)
  $dir = Split-Path $Path
  if ($dir -and -not (Test-Path $dir)) { [void](New-Item -ItemType Directory -Force $dir) }
  $fs = New-Object System.IO.FileStream($Path, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
  $w = New-Object System.IO.StreamWriter($fs, (New-Object System.Text.UTF8Encoding($false)))
  $w.AutoFlush = $true
  return $w
}

function Get-TruRtti {
  param($ctx, $inst)
  $N = $ctx.N
  $vt = $N.U32($inst)
  if ($vt -le 0) { return '?' }
  $k = [string]$vt
  if ($ctx.RttiCache.ContainsKey($k)) { return $ctx.RttiCache[$k] }
  $s = $N.Rtti($inst)
  if ($s) { $s = $s -replace '^\.\?A[VU]', '' -replace '@@$', '' } else { $s = '?' }
  $ctx.RttiCache[$k] = $s
  return $s
}

function Get-TruRaftSnapshot {
  # Resolves, from the live process: the raft_bridge instances (uniqueID 844), bullets (uniqueID 59), the 3 section objects.
  param($ctx)
  $N = $ctx.N
  $snap = @{ Rafts = @(); Bullets = @(); Walked = 0; Slots = @($null, $null, $null); Fail = @(); SlotBy = 'mi' }
  [void]$N.Walk($ctx.AHead, 6000, 844, 59, $false)
  $snap.Walked = $N.LastCount
  $arr = @($N.Out)
  if ($snap.Walked -le 0) { $snap.Fail += 'global instance list empty/unreadable' }
  if ($snap.Walked -ge 6000) { $snap.Fail += 'instance walk truncated at 6000' }
  $rafts = @()
  for ($i = 0; $i + 2 -lt $arr.Length; $i += 3) {
    if ($arr[$i + 2] -eq 844) {
      $p = $arr[$i]
      $r = @{ P = $p; Uid = $N.U32($p + 0x58); Serial = $N.U32($p + 0x44); Parent = $N.U32($p + 0x4c); Kind = 'nochain'; Sec = 0L; Desc = 0L; Mi = -1L }
      $a = $N.U32($p + 0x2d0)
      $b = -1L; $c = -1L
      if ($a -gt 0) { $b = $N.U32($a) }
      if ($b -gt 0) { $c = $N.U32($b + 0x2ec) }
      if ($c -gt 0x20) {
        $sec = $c - 0x10
        $r.Sec = $sec
        $mg = $N.U32($sec + 0x70)
        if ($mg -eq 0xf0012345L) {
          $r.Kind = 'Section'
          $r.Desc = $N.U32($sec + 0x78)
          if ($r.Desc -gt 0) { $r.Mi = $N.U8($r.Desc + 0x18) }
        } elseif ($N.U32($c - 4 + 0x54) -eq 0xfea51b1eL) {
          $r.Kind = 'Composite'
        } else { $r.Kind = 'nomagic' }
      }
      $rafts += $r
    } elseif ($arr[$i + 2] -eq 59) {
      $snap.Bullets += $arr[$i]
    }
  }
  $snap.Rafts = $rafts
  $secs = @($rafts | Where-Object { $_.Kind -eq 'Section' })
  if ($rafts.Count -eq 0) { $snap.Fail += 'no raft_bridge instance (uniqueID 844): unit not loaded yet?' }
  elseif (@($rafts | Where-Object { $_.Uid -eq 9789 -or $_.Kind -eq 'Composite' }).Count -eq 0) { $snap.Fail += 'parent Composite (uid 9789) not found' }
  if ($rafts.Count -gt 0 -and $secs.Count -lt 3) { $snap.Fail += ('only {0}/3 Section objects resolved' -f $secs.Count) }
  # slot assignment: model index [DESC+0x18] 0=raft(zattera) 1=Shot block 2=chain; fallback: order by instance uid
  $mis = @($secs | ForEach-Object { $_.Mi })
  $okmi = ($secs.Count -gt 0) -and (@($mis | Where-Object { $_ -ge 0 -and $_ -le 2 }).Count -eq $secs.Count) -and (@($mis | Select-Object -Unique).Count -eq $secs.Count)
  if ($okmi) { foreach ($s in $secs) { $snap.Slots[[int]$s.Mi] = $s } }
  else {
    $snap.SlotBy = 'uid-order'
    $sorted = @($secs | Sort-Object { $_.Uid })
    for ($k = 0; $k -lt $sorted.Count -and $k -lt 3; $k++) { $snap.Slots[$k] = $sorted[$k] }
  }
  return $snap
}

function Get-TruMembership {
  # aim lists -> sizes string + per-instance membership. Returns hashtable.
  param($ctx)
  $N = $ctx.N
  $res = @{ M = -1L; Sizes = 'NA'; Lists = @{}; Ids = @{} }
  $mgr = $N.U32($ctx.AMgr)
  $res.M = $mgr
  if ($mgr -le 0) { return $res }
  $sz = @()
  for ($i = 0; $i -lt 7; $i++) {
    $cnt = $N.ListNodes($mgr, $i, 400)
    if ($cnt -lt 0) { $sz += 'null'; continue }
    $arr = @($N.Out)
    $val = 0
    for ($j = 0; $j + 6 -lt $arr.Length; $j += 7) {
      if ($arr[$j + 6] -eq 1) {
        $val++
        $key = [string]$arr[$j + 2]
        if (-not $res.Lists.ContainsKey($key)) { $res.Lists[$key] = ','; $res.Ids[$key] = '' }
        $res.Lists[$key] += ([string]$i + ',')
        if ($res.Ids[$key] -ne '') { $res.Ids[$key] += ',' }
        $res.Ids[$key] += ('{0}:{1}' -f $i, $arr[$j + 4])
      }
    }
    $sz += ('{0}/{1}' -f $cnt, $val)
  }
  $res.Sizes = ($sz -join ';')
  return $res
}

function Get-TruSlotFields {
  # 10 fields: inst uid node idx life s80 sd0 s90 d52 lists
  param($ctx, $r, $memb)
  $N = $ctx.N
  if ($r -eq $null) { return @('NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', '-') }
  $sec = $r.Sec; $desc = $r.Desc
  $raw = $N.U32($sec + 0x84)
  $idx = 'NA'; $name = 'NA'
  if ($raw -ge 0) {
    $iv = $raw; if ($iv -ge 2147483648) { $iv -= 4294967296 }
    $idx = [string]$iv
    if ($iv -eq -1) { $name = '(trans)' }
    elseif ($iv -ge 0 -and $iv -lt 64 -and $desc -gt 0) {
      $np = $N.U32($desc + 8)
      $nm = -1L
      if ($np -gt 0) { $nm = $N.U32($np + 28 * $iv + 8) }
      if ($nm -gt 0) {
        $k = [string]$nm
        if (-not $ctx.NameCache.ContainsKey($k)) { $s = $N.Ascii($nm, 48); if ($s) { $ctx.NameCache[$k] = $s } else { $ctx.NameCache[$k] = '?' } }
        $name = $ctx.NameCache[$k]
      }
    }
  }
  $d52 = 'NA'
  if ($desc -gt 0) { $v = $N.U8($desc + 0x52); if ($v -ge 0) { $d52 = ('0x{0:x2}' -f $v) } }
  $ik = [string]$r.P
  $ls = '-'
  if ($memb.Ids.ContainsKey($ik)) { $ls = $memb.Ids[$ik] }
  return @((TruHex $r.P), [string]$r.Uid, $name, $idx, $N.F32s($sec + 0xdc), (TruHex $N.U32($sec + 0x80)), (TruHex $N.U32($sec + 0xd0)), (TruHex $N.U32($sec + 0x90)), $d52, $ls)
}

function Get-TruNodeNames {
  param($ctx, $desc)
  $N = $ctx.N
  if ($desc -le 0) { return 'NA' }
  $cnt = $N.U32($desc + 4); $np = $N.U32($desc + 8)
  if ($cnt -lt 0 -or $cnt -gt 64 -or $np -le 0) { return ('nodes?cnt={0}' -f $cnt) }
  $o = @()
  for ($k = 0; $k -lt $cnt; $k++) {
    $nm = $N.U32($np + 28 * $k + 8); $s = $null
    if ($nm -gt 0) { $s = $N.Ascii($nm, 48) }
    if (-not $s) { $s = '?' }
    $o += $s
  }
  return ($o -join '/')
}

function Write-TruRaftResolution {
  param($w, $ctx, $snap, [string]$label, $memb)
  $N = $ctx.N
  $w.WriteLine(('# {0} walked={1} raft(uid844)={2} sections={3} slotBy={4} bullets_now={5}' -f $label, $snap.Walked, $snap.Rafts.Count, @($snap.Rafts | Where-Object { $_.Kind -eq 'Section' }).Count, $snap.SlotBy, $snap.Bullets.Count))
  foreach ($r in $snap.Rafts) {
    $d50 = 'NA'; $d52 = 'NA'; $d2c = 'NA'; $nn = 'NA'; $ml = 'n/a'
    if ($memb -and $memb.Ids.ContainsKey([string]$r.P)) { $ml = $memb.Ids[[string]$r.P] }
    if ($r.Desc -gt 0) { $d50 = TruHex ($N.U32($r.Desc + 0x50)); $d52 = TruHex ($N.U8($r.Desc + 0x52)); $d2c = TruHex ($N.U8($r.Desc + 0x2c)); $nn = Get-TruNodeNames $ctx $r.Desc }
    $w.WriteLine(('#   RAFT_INST inst={0} instuid={1} serial={2} parent={3} kind={4} sec={5} desc={6} desc+0x50={7} desc+0x52={8} desc+0x2c={9} modelIdx={10} class={11} nodes=[{12}] aimlists(id)={13}' -f (TruHex $r.P), $r.Uid, (TruHex $r.Serial), (TruHex $r.Parent), $r.Kind, (TruHex $r.Sec), (TruHex $r.Desc), $d50, $d52, $d2c, $r.Mi, (Get-TruRtti $ctx $r.P), $nn, $ml))
  }
  for ($k = 0; $k -lt 3; $k++) {
    if ($snap.Slots[$k] -ne $null) {
      $hasShot = ((Get-TruNodeNames $ctx $snap.Slots[$k].Desc) -split '/') -contains 'Shot'
      $flag = ''
      if ($k -eq 1 -and -not $hasShot) { $flag = ' MISMATCH: slot1 graph has no Shot node (slot mapping suspect)' }
      if ($k -ne 1 -and $hasShot) { $flag = ' MISMATCH: slot ' + $k + ' graph contains Shot (slot mapping suspect)' }
      $w.WriteLine(('#   SLOT {0} = inst {1} (0=zattera/raft, 1=blocco col punto Shot, 2=catena){2}' -f $k, (TruHex $snap.Slots[$k].P), $flag))
    }
    else { $w.WriteLine(('#   SLOT {0} = NOT RESOLVED' -f $k)) }
  }
}

function Test-TruGlobals {
  param($ctx)
  $N = $ctx.N
  $f = @()
  $head = $N.U32($ctx.AHead)
  if ($head -lt 0) { $f += ('instance list head cell {0} unreadable' -f (TruHex $ctx.AHead)) } elseif ($head -eq 0) { $f += 'instance list empty (head=0)' }
  return $f
}

function Invoke-TruProbe {
  param(
    [ValidateSet('raft', 'lists')][string]$Mode = 'raft',
    [string]$Out,
    [string]$RunId,
    [int]$Seconds = 60,
    [int]$IntervalMs = 100,
    [int]$HeartbeatSec = 5,
    [int]$WaitProcess = 20,
    [int]$ProcId = 0
  )
  Initialize-TruProbeNative
  if (-not $RunId) { $RunId = (Get-Date).ToString('yyyyMMdd_HHmmss') }
  if (-not $Out) { $Out = ('Z:\tru-port\work\runs\{0}\probe_{1}.tsv' -f $RunId, $Mode) }
  $w = New-TruProbeWriter $Out
  $N = New-Object TruProbeNative
  $rows = 0
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    $w.WriteLine(('# vm_probe v{0} mode={1} runid={2} started={3} out={4} intervalMs={5} heartbeatSec={6} seconds={7}' -f $script:ProbeVersion, $Mode, $RunId, (Get-Date).ToString('yyyy-MM-dd HH:mm:ss'), $Out, $IntervalMs, $HeartbeatSec, $Seconds))
    $w.WriteLine(('# host: PowerShell {0}, 64bit-process={1}' -f $PSVersionTable.PSVersion, [Environment]::Is64BitProcess))
    $proc = Get-TruProcess -ProcId $ProcId -WaitSec $WaitProcess
    if (-not $proc) { $w.WriteLine('# RESOLVE: FAIL no tru process (waited ' + $WaitProcess + 's)'); $w.WriteLine('# END reason=no_process'); return 2 }
    if (-not $N.Open($proc.Id)) { $w.WriteLine(('# RESOLVE: FAIL OpenProcess(0x0410) pid={0} win32err={1}' -f $proc.Id, [Runtime.InteropServices.Marshal]::GetLastWin32Error())); $w.WriteLine('# END reason=open_failed'); return 3 }
    $img = Get-TruImageInfo $N $proc
    $w.WriteLine(('# process pid={0} name={1} image: base={2} (src {3}) {4}' -f $proc.Id, $proc.ProcessName, (TruHex $img.Base), $img.BaseSrc, $img.Msg))
    if (-not $img.Ok) { $w.WriteLine('# RESOLVE: FAIL image check (is this the 32-bit unpacked tru.exe?)'); $w.WriteLine('# END reason=bad_image'); return 4 }
    $delta = $img.Base - 0x400000L
    if ($delta -ne 0) { $w.WriteLine(('# WARNING: base != 0x400000, applying delta {0} to every absolute global address' -f $delta)) }
    $ctx = @{ N = $N; Delta = $delta; AHead = 0xd98d54L + $delta; AMgr = 0xfadfacL + $delta; AX = 0xfadb58L + $delta; ALara = 0xe7f094L + $delta; NameCache = @{}; RttiCache = @{} }
    $w.WriteLine(('# globals: instHead[0xd98d54]->{0} aimMgr[0xfadfac]->{1} wpnPtr[0xfadb58]->{2} Lara[0xe7f094]->{3}' -f (TruHex $ctx.AHead), (TruHex $ctx.AMgr), (TruHex $ctx.AX), (TruHex $ctx.ALara)))
    if ($Mode -eq 'lists') {
      # istantanee ripetute (ogni max(IntervalMs,1000) ms per $Seconds s); con Seconds <= 0 un solo dump. Si ferma se il dump fallisce (es. processo morto).
      $t0 = Get-Date; $rcl = 0
      do {
        $w.WriteLine(('# SNAPSHOT t={0:0.0}' -f ((Get-Date) - $t0).TotalSeconds))
        $rcl = Invoke-TruListsDump $w $ctx $proc
        if ($rcl -ne 0 -or $Seconds -le 0) { break }
        $w.Flush()
        Start-Sleep -Milliseconds ([Math]::Max($IntervalMs, 1000))
      } while (((Get-Date) - $t0).TotalSeconds -lt $Seconds)
      return $rcl
    }

    # ---------------- Mode raft ----------------
    $cols = @('t_wall', 't_ms', 'ev', 'res', 'nraft', 'bul_n', 'bul_inst', 'latch', 'lara', 'aimmgr', 'list_sizes(tot/valid x7)')
    foreach ($k in 0, 1, 2) { foreach ($c in 'inst', 'uid', 'node', 'idx', 'life', 'f80', 'fd0', 'f90', 'd52', 'lists(id)') { $cols += ('s{0}_{1}' -f $k, $c) } }
    $cols += 's1_in5'; $cols += 's1_in1'; $cols += 'par_lists(id)'; $cols += 'W'; $cols += 'wflag_raw'
    $first = $true; $lastSig = ''; $lastKey = $null; $lastWrite = -1000000L; $errs = 0; $lastClear = 0L
    $deadReason = ''
    while ($true) {
      $t0 = $sw.ElapsedMilliseconds
      if ($Seconds -gt 0 -and $t0 -ge ($Seconds * 1000)) { $deadReason = 'duration_elapsed'; break }
      $gone = $false
      try { $proc.Refresh(); if ($proc.HasExited) { $gone = $true } } catch { $gone = ($null -eq (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue)) }
      if ($gone) { $deadReason = 'process_exited'; break }
      try {
        if (($t0 - $lastClear) -gt 5000) { $N.ClearCache(); $lastClear = $t0 }
        $snap = Get-TruRaftSnapshot $ctx
        $memb = Get-TruMembership $ctx
        # weapon/aim latch: [[[0xfadb58]+0x504]+0x1fc] & 0x1000000
        $X = $N.U32($ctx.AX); $wp = -1L; $wr = -1L; $latch = 'NA'; $wrs = 'NA'
        if ($X -gt 0) { $wp = $N.U32($X + 0x504) }
        if ($wp -gt 0) { $wr = $N.U32($wp + 0x1fc) }
        if ($wr -ge 0) { $latch = [string][int](($wr -band 0x1000000) -ne 0); $wrs = TruHex $wr }
        $lara = $N.U32($ctx.ALara)
        $sig = ($snap.Rafts | ForEach-Object { '{0}/{1}/{2}' -f $_.P, $_.Kind, $_.Sec }) -join '|'
        $sig = '{0}#{1}' -f $sig, $snap.Fail.Count
        if ($first) {
          $failAll = @(Test-TruGlobals $ctx) + @($snap.Fail)
          if ($memb.M -le 0) { $failAll += ('aim manager [0xfadfac] is {0} (null = not created yet)' -f (TruHex $memb.M)) }
          if ($wp -le 0) { $failAll += ('weapon object chain [[0xfadb58]+0x504] unresolved (X={0} W={1})' -f (TruHex $X), (TruHex $wp)) }
          Write-TruRaftResolution $w $ctx $snap 'RESOLUTION' $memb
          $w.WriteLine(('# globals resolved: instHead->{0} lara={1} aimMgr={2} X={3} W={4}' -f (TruHex $N.U32($ctx.AHead)), (TruHex $lara), (TruHex $memb.M), (TruHex $X), (TruHex $wp)))
          if ($failAll.Count -eq 0) { $w.WriteLine('# RESOLVE: OK all targets found') } else { $w.WriteLine('# RESOLVE: PARTIAL/FAIL (probe keeps retrying every tick) -> ' + ($failAll -join ' ; ')) }
          $w.WriteLine('# res column: ok | comma-joined failure codes: noraft noparent sec<3 noaim nowpn nohead')
          $w.WriteLine(($cols -join "`t"))
          $lastSig = $sig; $first = $false
        } elseif ($sig -ne $lastSig) {
          Write-TruRaftResolution $w $ctx $snap ('RE-RESOLVED at t_ms=' + $t0) $memb
          $lastSig = $sig
        }
        $codes = @()
        if ($snap.Walked -le 0) { $codes += 'nohead' }
        if ($snap.Rafts.Count -eq 0) { $codes += 'noraft' }
        elseif (@($snap.Rafts | Where-Object { $_.Uid -eq 9789 -or $_.Kind -eq 'Composite' }).Count -eq 0) { $codes += 'noparent' }
        if ($snap.Rafts.Count -gt 0 -and @($snap.Rafts | Where-Object { $_.Kind -eq 'Section' }).Count -lt 3) { $codes += 'sec<3' }
        if ($memb.M -le 0) { $codes += 'noaim' }
        if ($wp -le 0) { $codes += 'nowpn' }
        $res = 'ok'; if ($codes.Count -gt 0) { $res = $codes -join ',' }
        $bl = @($snap.Bullets)
        $bul = '-'
        if ($bl.Count -gt 0) { $bul = (@($bl | Select-Object -First 4 | ForEach-Object { TruHex $_ }) -join ';') }
        $key = @($res, [string]$snap.Rafts.Count, [string]$bl.Count, $bul, $latch, (TruHex $lara), (TruHex $memb.M), $memb.Sizes)
        foreach ($k in 0, 1, 2) { $key += @(Get-TruSlotFields $ctx $snap.Slots[$k] $memb) }
        $in5 = 'NA'; $in1 = 'NA'
        if ($snap.Slots[1] -ne $null) {
          $l1 = ','; $ik = [string]$snap.Slots[1].P
          if ($memb.Lists.ContainsKey($ik)) { $l1 = $memb.Lists[$ik] }
          $in5 = [string][int]($l1 -like '*,5,*'); $in1 = [string][int]($l1 -like '*,1,*')
        }
        $parl = '-'
        foreach ($rr in $snap.Rafts) { if ($rr.Kind -eq 'Composite' -or $rr.Uid -eq 9789) { $pk = [string]$rr.P; if ($memb.Ids.ContainsKey($pk)) { $parl = $memb.Ids[$pk] } } }
        $key += $in5; $key += $in1; $key += $parl; $key += (TruHex $wp)
        $keyStr = $key -join "`t"
        $ev = $null
        if ($lastKey -eq $null) { $ev = 'INIT' }
        elseif ($keyStr -ne $lastKey) { $ev = 'CHG' }
        elseif (($t0 - $lastWrite) -ge ($HeartbeatSec * 1000)) { $ev = 'HB' }
        if ($ev) {
          $line = ((Get-Date).ToString('HH:mm:ss.fff')) + "`t" + $t0 + "`t" + $ev + "`t" + $keyStr + "`t" + $wrs
          $w.WriteLine($line)
          $rows++; $lastKey = $keyStr; $lastWrite = $t0
        }
        $errs = 0
      } catch {
        $errs++
        $w.WriteLine(('# ERR tick t_ms={0}: {1}' -f $t0, ($_.Exception.Message -replace '[\r\n]+', ' ')))
        if ($errs -ge 50) { $deadReason = 'too_many_errors'; break }
      }
      $left = $IntervalMs - ($sw.ElapsedMilliseconds - $t0)
      if ($left -gt 0) { Start-Sleep -Milliseconds $left }
    }
    $w.WriteLine(('# END reason={0} rows={1} elapsed_ms={2}' -f $deadReason, $rows, $sw.ElapsedMilliseconds))
    return 0
  } catch {
    try { $w.WriteLine(('# FATAL {0}' -f ($_.Exception.Message -replace '[\r\n]+', ' '))); $w.WriteLine('# END reason=fatal') } catch {}
    return 1
  } finally {
    $N.Close()
    try { $w.Close() } catch {}
  }
}

function Invoke-TruListsDump {
  # One-shot dump of the 7 aim lists and their elements (compare with work/ws/aim/lists.py).
  param($w, $ctx, $proc)
  $N = $ctx.N
  $mgr = $N.U32($ctx.AMgr)
  $lara = $N.U32($ctx.ALara)
  $w.WriteLine(('# lists: aimMgr={0} lara={1}' -f (TruHex $mgr), (TruHex $lara)))
  if ($mgr -le 0) {
    $w.WriteLine(('# RESOLVE: FAIL aim manager [0xfadfac]={0} (null: not created yet, or wrong base)' -f (TruHex $mgr)))
    $w.WriteLine('# END reason=no_aim_manager')
    return 5
  }
  $w.WriteLine('# RESOLVE: OK')
  $w.WriteLine(((@('list', 'list_addr', 'list_idx', 'mask', 'nsub', 'head', 'node', 'inst', 'valid', 'def', 'def_uniqueID', 'inst_uid', 'serial', 'node_id', 'node_act', 'class', 'f18', 'f1c', 'par_inst', 'par_uid', 'node10', 'node18', 'h11c')) -join "`t"))
  $total = 0
  for ($i = 0; $i -lt 7; $i++) {
    $lst = $N.U32($mgr + 4 * $i)
    if ($lst -le 0) { $w.WriteLine(('{0}' -f $i) + "`t" + (TruHex $lst) + "`t-`t-`t-`t-`t-`t-`t-`t-`t-`t-`t-`t-`t-`tNULL_LIST"); continue }
    $c34 = $N.U32($lst + 0x34); $nsub = -1
    if ($c34 -gt 0) { $nsub = $N.U8($c34 + 4) }
    $cnt = $N.ListNodes($mgr, $i, 400)
    $arr = @($N.Out)
    $lines = @(("{0}`t{1}`t{2}`t{3}`t{4}`t-`t-`t-`t-`t-`t-`t-`t-`t-`t-`tLIST_HEADER nodes={5}" -f $i, (TruHex $lst), $N.U32($lst), (TruHex $N.U32($lst + 4)), $nsub, $cnt))
    for ($j = 0; $j + 6 -lt $arr.Length; $j += 7) {
      $ins = $arr[$j + 2]
      $def = -1L; $duid = -1L; $iuid = -1L; $cls = '?'
      $f18 = -1L; $f1c = -1L; $par = 0L; $puid = -1L; $n10 = -1L; $n18 = -1L; $h11c = -1L
      if ($arr[$j + 6] -eq 1) {
        $def = $N.U32($ins + 0x10)
        if ($def -gt 0) { $duid = $N.U32($def + 0x14) }
        $iuid = $N.U32($ins + 0x58)
        $f18 = $N.U32($ins + 0x18); $f1c = $N.U32($ins + 0x1c); $par = $N.U32($ins + 0x4c); if ($par -gt 0) { $puid = $N.U32($par + 0x58) }
        $n10 = $N.U32($arr[$j + 1] + 0x10); $n18 = $N.U32($arr[$j + 1] + 0x18)
        $h11c = $N.U32($ins + 0x11c)
        $cls = Get-TruRtti $ctx $ins
      } else { $cls = 'STALE' }
      $lines += ("{0}`t{1}`t-`t-`t-`t{2}`t{3}`t{4}`t{5}`t{6}`t{7}`t{8}`t{9}`t{10}`t{11}`t{12}`t{13}`t{14}`t{15}`t{16}`t{17}`t{18}`t{19}" -f $i, (TruHex $lst), $arr[$j], (TruHex $arr[$j + 1]), (TruHex $ins), $arr[$j + 6], (TruHex $def), $duid, $iuid, (TruHex $arr[$j + 3]), $arr[$j + 4], $arr[$j + 5], $cls, (TruHex $f18), (TruHex $f1c), (TruHex $par), $puid, (TruHex $n10), (TruHex $n18), (TruHex $h11c))
      $total++
    }
    foreach ($ln in $lines) { $w.WriteLine($ln) }
  }
  $w.WriteLine(('# END reason=done nodes={0}' -f $total))
  return 0
}
