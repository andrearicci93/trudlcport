# vm_watch418.ps1 - SOLA LETTURA. Osserva gli oggetti X (classe vtable 0x8494ec, copia runtime delle DTP luce, ctor 0x50b7b0)
# creati in tru.exe e registra ogni cambio di X+0 (vtable), X+0x418 (texture usata dal binding luce FUN_0050a5f0) e X+0xc54
# (texture risolta alla creazione). Gli indirizzi di X arrivano dal tap: righe 'probe7 ecx=<X>' (sonda x_create@5073e5,
# exe work/ws/tap/probe_light). Lanciare con il PowerShell a 32 bit:
#   C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File Z:\tru-port\tools\vm_watch418.ps1 -Tap Z:\tru-port\work\taps\<Tag>\tap.tsv -Out Z:\tru-port\work\live\watch418_<Tag>.tsv
# Uscita TSV: t_watch  ultimo_seq_tap  ultimo_t_tap  X  campo  vecchio  nuovo  [nuovo]  flag_c50
# -TargetPid: per il collaudo (default: primo processo 'tru').
param([string]$Tap, [string]$Out, [int]$Seconds = 10800, [int]$PollMs = 2, [int]$TargetPid = 0, [int]$WaitStartSeconds = 3600,
      [int]$MaxDumps = 0, [string]$DumpPrefix = 'C:\CrashDumps\w418')   # MaxDumps>0: dump su richiesta (ProcDump -ma) quando un X vivo prende +0x418 != +0xc54
$ErrorActionPreference = 'Stop'
if ([IntPtr]::Size -ne 4) { 'serve PowerShell a 32 bit'; exit 5 }
Add-Type @'
using System; using System.IO; using System.Text; using System.Collections.Generic; using System.Diagnostics;
using System.Runtime.InteropServices; using System.Globalization;
public static class W418 {
  [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(int a, bool b, int pid);
  [DllImport("kernel32.dll")] static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] b, int n, out int r);
  [DllImport("kernel32.dll")] static extern bool GetExitCodeProcess(IntPtr h, out int c);
  static IntPtr H; static byte[] B4 = new byte[4];
  static long U32(uint a) { int r; if (!ReadProcessMemory(H, (IntPtr)(long)a, B4, 4, out r) || r != 4) return -1; return BitConverter.ToUInt32(B4, 0); }
  static string Hx(long v) { return v < 0 ? "ILLEGGIBILE" : ((uint)v).ToString("x8"); }
  public static string Run(int pid, string tap, string outp, int seconds, int pollMs, int maxDumps, string dumpPrefix) {
    H = OpenProcess(0x0410 | 0x1000, false, pid);
    if (H == IntPtr.Zero) return "OpenProcess fallita";
    var sw = Stopwatch.StartNew(); var inv = CultureInfo.InvariantCulture;
    var xs = new List<uint>(); var last = new Dictionary<string, long>();
    string lastSeq = "-", lastT = "-"; long tapPos = 0; long iter = 0; var pend = new StringBuilder(); int nchg = 0; int ndump = 0; double nextBeat = 30;
    using (var w = new StreamWriter(outp, false, new UTF8Encoding(false))) {
      w.AutoFlush = true;
      w.WriteLine("t_watch\tseq_tap\tt_tap\tX\tcampo\tvecchio\tnuovo\tnuovo_vt\tflag_c50");
      while (sw.Elapsed.TotalSeconds < seconds) {
       try {
        if (sw.Elapsed.TotalSeconds >= nextBeat) { w.WriteLine("#VIVO t=" + sw.Elapsed.TotalSeconds.ToString("F1", inv) + " X=" + xs.Count + " seq_tap=" + lastSeq); nextBeat += 30; }
        int code; if (GetExitCodeProcess(H, out code) && code != 259) { w.WriteLine("#USCITO t=" + sw.Elapsed.TotalSeconds.ToString("F3", inv)); break; }
        if ((iter++ % 25) == 0 && File.Exists(tap)) {
          using (var fs = new FileStream(tap, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete)) {
            if (fs.Length > tapPos) {
              fs.Seek(tapPos, SeekOrigin.Begin); var buf = new byte[fs.Length - tapPos]; int n = fs.Read(buf, 0, buf.Length); tapPos += n;
              pend.Append(Encoding.UTF8.GetString(buf, 0, n)); string s = pend.ToString(); int cut = s.LastIndexOf('\n');
              if (cut >= 0) {
                foreach (var line in s.Substring(0, cut).Split('\n')) {
                  var c = line.TrimEnd('\r').Split('\t');
                  if (c.Length >= 6 && c[0].Length > 0 && char.IsDigit(c[0][0])) { lastSeq = c[0]; lastT = c[1]; }
                  int k = line.IndexOf("probe7 ecx=");
                  if (k >= 0) { uint x = Convert.ToUInt32(line.Substring(k + 11, 8), 16); if (!xs.Contains(x)) { xs.Add(x); w.WriteLine(sw.Elapsed.TotalSeconds.ToString("F4", inv) + "\t" + lastSeq + "\t" + lastT + "\t" + x.ToString("x8") + "\tNUOVO\t-\t-\t-\t-"); } }
                }
                pend.Clear(); pend.Append(s.Substring(cut + 1));
              }
            }
          }
        }
        foreach (var x in xs) {
          long[] v = { U32(x), U32(x + 0x418), U32(x + 0xc54) }; string[] nm = { "vt", "418", "c54" };
          for (int i = 0; i < 3; i++) {
            string key = x.ToString("x8") + nm[i]; long old;
            if (!last.TryGetValue(key, out old) || old != v[i]) {
              long nvt = (i > 0 && v[i] > 0) ? U32((uint)v[i]) : -2; long fl = U32(x + 0xc50);
              w.WriteLine(sw.Elapsed.TotalSeconds.ToString("F4", inv) + "\t" + lastSeq + "\t" + lastT + "\t" + x.ToString("x8") + "\t" + nm[i] + "\t" +
                (last.ContainsKey(key) ? Hx(old) : "init") + "\t" + Hx(v[i]) + "\t" + (nvt == -2 ? "-" : Hx(nvt)) + "\t" + (fl < 0 ? "?" : (fl & 0xff).ToString("x2")));
              last[key] = v[i]; nchg++;
              if (i == 1 && maxDumps > ndump && v[1] != v[2] && v[1] > 0 && last.ContainsKey(x.ToString("x8") + "vt") && last[x.ToString("x8") + "vt"] == 0x8494ec) {
                ndump++; string f = dumpPrefix + "_" + ndump + ".dmp";
                Process.Start(new ProcessStartInfo(@"C:\Tools\procdump\procdump.exe", "-accepteula -ma " + pid + " " + f) { UseShellExecute = false, CreateNoWindow = true });
                w.WriteLine("#DUMP " + f + " t=" + sw.Elapsed.TotalSeconds.ToString("F4", inv) + " X=" + x.ToString("x8") + " 418=" + Hx(v[1]));
              }
            }
          }
        }
       } catch (Exception ex) { w.WriteLine("#ERR t=" + sw.Elapsed.TotalSeconds.ToString("F3", inv) + " " + ex.GetType().Name + ": " + ex.Message.Replace('\n', ' ')); System.Threading.Thread.Sleep(50); }
        System.Threading.Thread.Sleep(pollMs);
      }
    }
    return "fine: X osservati " + xs.Count + ", righe " + nchg;
  }
}
'@
$sw = [Diagnostics.Stopwatch]::StartNew()
if ($TargetPid -eq 0) {
  while (-not (Get-Process -Name tru -ErrorAction SilentlyContinue)) { if ($sw.Elapsed.TotalSeconds -gt $WaitStartSeconds) { 'tru.exe non avviato'; exit 6 }; Start-Sleep 2 }
  $TargetPid = (Get-Process -Name tru | Select-Object -First 1).Id
}
[W418]::Run($TargetPid, $Tap, $Out, $Seconds, $PollMs, $MaxDumps, $DumpPrefix)
