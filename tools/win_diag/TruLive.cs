// TruLive: diagnostica "a gioco aperto" del port TRU DLC. SOLA LETTURA sul processo del gioco (ReadProcessMemory + MiniDumpWriteDump su tasto).
// Non scrive nulla nel gioco, non inietta niente. Compilato da trudlcport_diag.ps1 con Add-Type (C# 5, .NET 4).
// Scrive in outDir:  live_<tag>.tsv (serie temporale), live_<tag>_eventi.txt, LIVE_SUMMARY_<tag>.txt, modules_<tag>.txt,
//                    shot_<tag>_<n>.png (tasto), dump_<tag>_<n>.dmp (tasto), engine_<tag>_pid<N>.log
// Righe TSV (campo 1 = tipo, campo 2 = ms dall'avvio dello strumento):
//   A  t  testo                          aggancio/distacco/avvisi
//   S  t  frame fps lflags f1244 vz posZ ogni 500 ms: contatore frame del gioco, fps reali (finestra 1 s), Lara+0x1fc, byte game+0x1244, vz, Z
//   X  t  12 float                       ogni 200 ms: posizione/vettori del player ([[0xE7F094]+0x0c])
//   Mk t mp dist c94 flags w2c kind ckind 24dw   markup trovato dalla ricerca (game+0xa64, tipo kind) e markup agganciato (game+0xc94, tipo ckind); la vena e' tipo 22; a ogni cambio
//   PC t 12dw + 4dw                      contatori delle patch dell'exe (.tufx @0x1241000, .tufin @0x1242bf0), a ogni cambio
//   W  t hwnd l t r b fg                 finestra del gioco, ogni 5 s
//   K  t n etichetta                     tasto-marcatore premuto dall'utente
using System;
using System.IO;
using System.Text;
using System.Diagnostics;
using System.Threading;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Drawing;
using System.Drawing.Imaging;

public static class TruLive
{
    [DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr OpenProcess(uint acc, bool inh, int pid);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] buf, int n, out int rd);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
    [DllImport("user32.dll")] static extern short GetAsyncKeyState(int vk);
    [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] static extern bool SetProcessDPIAware();
    [DllImport("winmm.dll")] static extern uint timeBeginPeriod(uint ms);
    [DllImport("dbghelp.dll", SetLastError = true)] static extern bool MiniDumpWriteDump(IntPtr h, uint pid, IntPtr f, int type, IntPtr e, IntPtr u, IntPtr c);
    [DllImport("psapi.dll", SetLastError = true)] static extern bool EnumProcessModulesEx(IntPtr h, IntPtr[] mods, int cb, out int needed, uint filter);
    [DllImport("psapi.dll", CharSet = CharSet.Unicode, SetLastError = true)] static extern int GetModuleFileNameEx(IntPtr h, IntPtr mod, StringBuilder sb, int n);
    [DllImport("kernel32.dll")] static extern int VirtualQueryEx(IntPtr h, IntPtr a, out MBI m, int len);
    [DllImport("xinput1_4.dll")] static extern int XInputGetState(int idx, out XSTATE st);
    [StructLayout(LayoutKind.Sequential)] struct XSTATE { public uint Pkt; public ushort Btn; public byte LT, RT; public short LX, LY, RX, RY; }

    // registro grezzo (raw_<tag>.bin): record di 7964 byte = 7 uint32 (magic 'RAW1', t_ms, frame, game, lara, player, flag ok bit0/1/2) + 0x1300 byte da game + 0x800 da Lara (game+0x504) + 0x400 dal player ([0xE7F094])
    const int RAW_G = 0x1300, RAW_L = 0x800, RAW_P = 0x400;
    static FileStream rawFs; static long lastRaw = -1000, lastI = -1000, lastTrig = -1000, lastH = 0, lastTrigDump = -1000000;
    static long burstUntil = 0, dumpAt = 0, rawBytes = 0;
    static int rawOk = 0, rawFail = 0, nTrig = 0, nTrigDumps = 0, errCount = 0, nInput = 0;
    static int dashRun = 0; static float pX, pY; static long pT = -1;
    static string lastIKey = ""; static long lastIWrite = -1000; static bool xiOff = false, gameFg = false;
    static string lastLfHex = "";
    static readonly int[] KEYS = new int[] { 0x20, 0xA0, 0xA1, 0xA2, 0xA3, 0x57, 0x41, 0x53, 0x44, 0x25, 0x26, 0x27, 0x28, 0x45, 0x51, 0x0D, 0x09, 0x1B, 0x01, 0x02, 0x04, 0x46, 0x52, 0x43, 0x56, 0x58, 0x5A, 0x31, 0x32, 0x33, 0x34 };

    [StructLayout(LayoutKind.Sequential)] struct RECT { public int L, T, R, B; }
    [StructLayout(LayoutKind.Sequential)] struct MBI { public IntPtr Base, AllocBase; public uint AllocProt; public IntPtr Size; public uint State, Protect, Type; }

    // indirizzi (exe v1.1 unpacked, base 0x400000): validi anche nell'exe originale, non dipendono dalle patch
    // (sovrascrivibili con le variabili d'ambiente TRULIVE_A_FRAME/_GAME/_PLAYER, in esadecimale: solo per collaudare lo strumento su un finto processo)
    static uint Ov(string n, uint d) { string s = Environment.GetEnvironmentVariable(n); uint v; if (!string.IsNullOrEmpty(s) && uint.TryParse(s, System.Globalization.NumberStyles.HexNumber, null, out v)) return v; return d; }
    static readonly uint A_FRAME = Ov("TRULIVE_A_FRAME", 0x8c7000);     // contatore frame/tick del loop principale
    static readonly uint A_GAME = Ov("TRULIVE_A_GAME", 0xFADB58);      // puntatore al "game"
    static readonly uint A_PLAYER = Ov("TRULIVE_A_PLAYER", 0xE7F094);    // puntatore all'oggetto player (posizione a +0x0c..)
    const uint A_TUFX = 0x1241000, A_TUFIN = 0x1242bf0;   // contatori patch (solo exe del port)

    static IntPtr h = IntPtr.Zero;
    static Process proc;
    static int pid;
    static Stopwatch sw;
    static StreamWriter tsv, ev;
    static string outDir, tag;
    static volatile bool stopReq;
    static Dictionary<string, string> info = new Dictionary<string, string>();

    // statistiche
    static long[] fpsBucketMs = new long[7];   // 0 fermo, <30, 30-58, 58-62, 62-75, 75-100, >100
    static string[] bucketName = new string[] { "fermo/caricamento (<1 fps)", "1-30 fps", "30-58 fps", "58-62 fps (ok)", "62-75 fps", "75-100 fps", ">100 fps" };
    static double fpsMax = 0;
    static List<double> fpsSamples = new List<double>();
    static int nMkFound = 0, nAttached = 0, nVeinFound = 0, nVeinAtt = 0, nMk = 0, nMarks = 0, nDumps = 0, nShots = 0;
    static HashSet<uint> mkKinds = new HashSet<uint>();
    static string lastMkKey = "";
    static uint lastFrame = 0; static long lastFrameMs = 0; static long stalledMs = 0;
    static Queue<long> qT = new Queue<long>(); static Queue<uint> qF = new Queue<uint>();
    static double fpsNow = 0;
    static string patchState = "n/d";
    static string exePath = "";
    static string lastModKey = "";
    static int dumpSeq = 0;
    static HashSet<int> crashDumped = new HashSet<int>();
    static string exitInfo = "";

    // indirizzi a 32 bit senza overflow di IntPtr (il gioco e' LAA: puntatori anche sopra 0x80000000), sia da PowerShell a 32 che a 64 bit
    static IntPtr PL(long a) { return IntPtr.Size == 4 ? new IntPtr(unchecked((int)(uint)a)) : new IntPtr(a); }
    static long SzOf(IntPtr p) { return IntPtr.Size == 4 ? (long)unchecked((uint)p.ToInt32()) : p.ToInt64(); }
    static uint KindOf(uint p) { uint q; byte[] kb = new byte[1]; if (p != 0 && U32(p + 0x24, out q) && q != 0 && Rd(q + 0x4d, kb)) return kb[0]; return 0xff; }
    static bool Exited() { try { return proc.HasExited; } catch { return false; } }
    static bool Rd(uint a, byte[] b) { int r; if (h == IntPtr.Zero) return false; try { return ReadProcessMemory(h, PL(a), b, b.Length, out r) && r == b.Length; } catch { return false; } }
    static bool U32(uint a, out uint v) { byte[] b = new byte[4]; v = 0; if (!Rd(a, b)) return false; v = BitConverter.ToUInt32(b, 0); return true; }
    static float F32(uint a) { byte[] b = new byte[4]; if (!Rd(a, b)) return 0; return BitConverter.ToSingle(b, 0); }
    static string T() { return sw.ElapsedMilliseconds.ToString(); }
    static void Log(string s) { try { tsv.WriteLine(s); } catch { } }
    static void Ev(string s) { string l = DateTime.Now.ToString("HH:mm:ss") + "  " + s; Console.WriteLine(l); try { ev.WriteLine(l); ev.Flush(); } catch { } }
    static string G(float f) { return f.ToString("G6", System.Globalization.CultureInfo.InvariantCulture); }

    public static string Run(string outputDir, string runTag, int markVk, int dumpVk, string dumpMode, string stopFile, int idleExitSec)
    {
        outDir = outputDir; tag = runTag; sw = Stopwatch.StartNew();
        try { SetProcessDPIAware(); } catch { }
        try { timeBeginPeriod(1); } catch { }
        tsv = new StreamWriter(new FileStream(Path.Combine(outDir, "live_" + tag + ".tsv"), FileMode.Create, FileAccess.Write, FileShare.ReadWrite), new UTF8Encoding(false)); tsv.NewLine = "\n";
        ev = new StreamWriter(new FileStream(Path.Combine(outDir, "live_" + tag + "_eventi.txt"), FileMode.Create, FileAccess.Write, FileShare.ReadWrite), new UTF8Encoding(false));
        Log("# trudlcport live " + DateTime.Now.ToString("s") + " ptr=" + IntPtr.Size * 8 + "bit");
        ConsoleCancelEventHandler cancel = delegate(object s, ConsoleCancelEventArgs e) { e.Cancel = true; stopReq = true; };
        Console.CancelKeyPress += cancel;
        long lastS = -1000, lastX = -1000, lastPC = -1000, lastW = -1000, lastStat = 0, lastLog = 0, lastWer = 0, lastFlush = 0, lastSeen = 0, tAttach = 0, lastWait = 0;
        bool markDown = false, dumpDown = false, everAttached = false; int modStage = 0;
        burstUntil = 0; dumpAt = 0; errCount = 0;
        try { rawFs = new FileStream(Path.Combine(outDir, "raw_" + tag + ".bin"), FileMode.Create, FileAccess.Write, FileShare.ReadWrite); } catch (Exception e) { Ev("raw non apribile: " + e.Message); rawFs = null; }
        Ev("REGISTRAZIONE AUTOMATICA: non serve premere nulla. Dump automatici quando Lara entra nello stato di scivolata (lflags 0x25d8000) o supera 2500 u/s in orizzontale. Facoltativi: '+' = marcatore, 'e grave' = dump tra 1,5 s. Ctrl+C = fine.");
        try
        {
            while (!stopReq && !File.Exists(stopFile))
            {
                long now = sw.ElapsedMilliseconds;
                try {
                if (h == IntPtr.Zero)
                {
                    if (!Attach()) { if (now - lastWait > 15000) { lastWait = now; Console.WriteLine("  ... in attesa che tru.exe sia in esecuzione"); } if (everAttached && now - lastSeen > idleExitSec * 1000L) { Ev("Gioco chiuso da oltre " + idleExitSec + " s: fine registrazione."); break; } Thread.Sleep(300); continue; }
                    everAttached = true; modStage = 0; tAttach = now; lastSeen = now;
                }
                if (Exited())
                {
                    int code = 0; try { code = proc.ExitCode; } catch { }
                    exitInfo = "uscita processo pid " + pid + " exit code 0x" + code.ToString("x8");
                    Ev("Il gioco si e' chiuso: " + exitInfo + (code != 0 ? "   <-- USCITA ANOMALA (0xC0000005 = access violation)" : ""));
                    Log("A\t" + T() + "\t" + exitInfo);
                    CloseHandle(h); h = IntPtr.Zero; lastSeen = now; qT.Clear(); qF.Clear(); fpsNow = 0; continue;
                }
                lastSeen = now;
                // tasti-marcatore (fronte di salita)
                bool md = (GetAsyncKeyState(markVk) & 0x8000) != 0, dd = (GetAsyncKeyState(dumpVk) & 0x8000) != 0;
                if (md && !markDown) { Mark(false, dumpMode); burstUntil = now + 20000; Ev("   campionamento fitto per 20 s: prova adesso"); }
                if (dd && !dumpDown && dumpAt == 0) { dumpAt = now + 1500; burstUntil = now + 20000; Ev("DUMP ARMATO: parte tra 1,5 s (2 beep, poi uno lungo)."); try { Console.Beep(500, 150); Console.Beep(500, 150); } catch { } }
                if (dumpAt != 0 && now >= dumpAt) { dumpAt = 0; try { Console.Beep(400, 300); } catch { } Mark(true, dumpMode); }
                markDown = md; dumpDown = dd;
                // moduli caricati (d3d9 vero usato dal gioco): a 3 s, 20 s, 60 s dall'aggancio
                if ((modStage == 0 && now - tAttach > 3000) || (modStage == 1 && now - tAttach > 20000) || (modStage == 2 && now - tAttach > 60000)) { DumpModules(); modStage++; }
                bool burst = now < burstUntil;
                if (now - lastS >= (burst ? 50 : 100)) { lastS = now; SampleS(now); }
                if (now - lastX >= (burst ? 25 : 50)) { lastX = now; SampleX(); }
                if (now - lastRaw >= (burst ? 25 : 50)) { lastRaw = now; SampleRaw(now); }
                if (now - lastI >= 25) { lastI = now; SampleInput(now); }
                if (now - lastTrig >= 25) { lastTrig = now; CheckTrig(now, dumpMode); }
                if (now - lastH >= 5000) { lastH = now; SampleHealth(); }
                SampleMk(false);
                if (now - lastPC >= 1000) { lastPC = now; SamplePC(false); }
                if (now - lastW >= 5000) { lastW = now; SampleW(); }
                // crash: WerFault compare mentre il gioco e' ancora vivo (congelato) -> dump completo + log del motore
                if (now - lastWer >= 1000)
                {
                    lastWer = now;
                    try { if (Process.GetProcessesByName("WerFault").Length > 0 && !crashDumped.Contains(pid) && !Exited()) { crashDumped.Add(pid); Ev("CRASH rilevato (WerFault attivo): dump completo e log motore..."); Log("A\t" + T() + "\tcrash WerFault"); TakeDump("crash", "Full"); ScanLog("crash"); } } catch { }
                }
                if (now - lastLog >= 120000) { lastLog = now; ScanLog("auto"); }
                if (now - lastStat >= 1000) { lastStat = now; PrintStatus(); }   // 1 s (14/11): prova vena da appesa
                if (now - lastFlush > 400) { try { tsv.Flush(); } catch { } lastFlush = now; }
                Thread.Sleep(15);
                } catch (Exception ex) { errCount++; if (errCount <= 20) Ev("Errore nel ciclo (continuo): " + ex.Message); Thread.Sleep(50); }
            }
        }
        catch (Exception e) { Ev("Errore interno: " + e.Message); }
        finally { Console.CancelKeyPress -= cancel; }
        string sum = Summary();
        try { tsv.Flush(); tsv.Close(); ev.Flush(); ev.Close(); } catch { }
        try { if (rawFs != null) { rawFs.Flush(); rawFs.Close(); } } catch { }
        if (h != IntPtr.Zero) { CloseHandle(h); h = IntPtr.Zero; }
        return sum;
    }

    static bool Attach()
    {
        Process[] ps = Process.GetProcessesByName("tru"); if (ps.Length == 0) return false;
        Process p = ps[0];
        IntPtr hh = OpenProcess(0x0410, false, p.Id); if (hh == IntPtr.Zero) { Ev("tru.exe trovato ma non apribile (errore " + Marshal.GetLastWin32Error() + "): avvia lo strumento con lo stesso utente del gioco, non da amministratore se il gioco non lo e'."); Thread.Sleep(2000); return false; }
        h = hh; proc = p; pid = p.Id; lastMkKey = ""; lastFrame = 0; qT.Clear(); qF.Clear();
        StringBuilder sb = new StringBuilder(520); try { GetModuleFileNameEx(h, IntPtr.Zero, sb, 520); } catch { }
        exePath = sb.ToString();
        // l'exe in memoria e' quello patchato dal port?
        byte[] hook = new byte[5], att = new byte[15], sec = new byte[4];
        bool okHook = Rd(0x441fb0, hook) && hook[0] == 0xE9;
        bool okAtt = Rd(0x1240f80, att) && att[0] == 0x8d && att[1] == 0x83 && att[2] == 0xa7 && att[3] == 0xfd;
        uint tx; bool okExt = U32(0x1237000, out tx) && tx == 0x0a;
        byte[] fx = new byte[4]; bool okFx = Rd(A_TUFX, fx);
        patchState = "hook441fb0=" + (okHook ? "ok" : "ASSENTE") + " cave_attach=" + (okAtt ? "ok" : "ASSENTE") + " tuext=" + (okExt ? "ok" : "ASSENTE") + " tufx=" + (okFx ? "ok" : "ASSENTE");
        Ev("Agganciato a tru.exe pid " + pid + "  " + exePath);
        Ev("Exe IN MEMORIA: " + patchState + (okAtt && okExt ? "" : "   <-- l'exe in esecuzione NON e' quello patchato del port (wall-run impossibile)"));
        Log("A\t" + T() + "\tattach pid=" + pid + " exe=" + exePath + " " + patchState);
        return true;
    }

    static void DumpModules()
    {
        try
        {
            IntPtr[] mods = new IntPtr[1024]; int needed;
            if (!EnumProcessModulesEx(h, mods, mods.Length * IntPtr.Size, out needed, 3)) { Ev("Elenco moduli non disponibile"); return; }
            int n = Math.Min(mods.Length, needed / IntPtr.Size);
            List<string> names = new List<string>();
            for (int i = 0; i < n; i++) { StringBuilder sb = new StringBuilder(520); if (GetModuleFileNameEx(h, mods[i], sb, 520) > 0) names.Add(sb.ToString()); }
            names.Sort(StringComparer.OrdinalIgnoreCase);
            string key = string.Join("|", names.ToArray());
            if (key == lastModKey) return; lastModKey = key;
            File.WriteAllLines(Path.Combine(outDir, "modules_" + tag + ".txt"), names.ToArray());
            List<string> hits = new List<string>();
            foreach (string m in names)
            {
                string l = m.ToLowerInvariant(); string f = Path.GetFileName(l);
                if (f == "d3d9.dll" || f == "d3d9on12.dll" || f == "d3d12.dll" || f == "d3d11.dll" || f == "dxgi.dll" || f.StartsWith("dxvk") || f.Contains("dgvoodoo") || f.Contains("reshade") || f.Contains("specialk") || f.Contains("nvd3dum") || f.Contains("nvwgf2um") || f.Contains("atiumd") || f.Contains("amdxc") || f.Contains("aticfx") || f.Contains("ig9icd") || f.Contains("igd10") || f.Contains("igdumd") || f.Contains("igdrcl") || f.Contains("ddraw") || f.Contains("rtss") || f.Contains("overlay") || f.EndsWith(".asi") || f == "modloader.dll")
                    hits.Add(m);
            }
            Ev("MODULI RILEVANTI (" + names.Count + " totali, elenco completo in modules_" + tag + ".txt):");
            foreach (string m in hits) Ev("    " + m);
            Log("A\t" + T() + "\tmoduli " + names.Count + " d3d9=" + (hits.Exists(delegate(string x) { return Path.GetFileName(x).ToLowerInvariant() == "d3d9.dll"; }) ? hits.Find(delegate(string x) { return Path.GetFileName(x).ToLowerInvariant() == "d3d9.dll"; }) : "?"));
        }
        catch (Exception e) { Ev("Errore elenco moduli: " + e.Message); }
    }

    static void SampleS(long now)
    {
        uint frame = 0; U32(A_FRAME, out frame);
        qT.Enqueue(now); qF.Enqueue(frame);
        while (qT.Count > 2 && now - qT.Peek() > 1200) { qT.Dequeue(); qF.Dequeue(); }
        if (qT.Count >= 2)
        {
            long dt = now - qT.Peek(); uint df = frame - qF.Peek();
            if (dt >= 400) fpsNow = df * 1000.0 / dt;
        }
        int b = fpsNow < 1 ? 0 : fpsNow < 30 ? 1 : fpsNow < 58 ? 2 : fpsNow <= 62.5 ? 3 : fpsNow <= 75 ? 4 : fpsNow <= 100 ? 5 : 6;
        fpsBucketMs[b] += 500; if (fpsNow > fpsMax) fpsMax = fpsNow; if (fpsNow >= 1) fpsSamples.Add(fpsNow);
        uint g = 0, L = 0, lf = 0, le = 0; byte[] f1244 = new byte[1]; float vz = 0, z = 0;
        U32(A_GAME, out g);
        if (g != 0) { U32(g + 0x504, out L); Rd(g + 0x1244, f1244); vz = F32(g + 0x1f0); }
        if (L != 0) U32(L + 0x1fc, out lf);
        U32(A_PLAYER, out le); if (le != 0) z = F32(le + 0x20);
        Log("S\t" + T() + "\t" + frame + "\t" + fpsNow.ToString("F1", System.Globalization.CultureInfo.InvariantCulture) + "\t" + lf.ToString("x") + "\t" + f1244[0] + "\t" + G(vz) + "\t" + G(z));
        lastFrame = frame; lastFrameMs = now;
    }

    static void SampleX()
    {
        uint le = 0; U32(A_PLAYER, out le); if (le == 0) return;
        byte[] xb = new byte[0x30]; if (!Rd(le + 0x0c, xb)) return;
        StringBuilder sx = new StringBuilder("X\t" + T());
        for (int i = 0; i < 12; i++) sx.Append("\t" + G(BitConverter.ToSingle(xb, 4 * i)));
        Log(sx.ToString());
    }

    // markup (vena) trovato dalla ricerca del gioco e markup agganciato: sono i due passaggi del wall-run
    static void SampleMk(bool force)
    {
        uint g = 0; U32(A_GAME, out g); if (g == 0) return;
        uint mp = 0, mt = 0, mf = 0, mw = 0, kind = 0xff; float dist = 0;
        U32(g + 0xa64, out mp); U32(g + 0xc94, out mt); dist = F32(g + 0xa68);
        if (mp != 0) { U32(mp + 0x28, out mf); U32(mp + 0x2c, out mw); kind = KindOf(mp); }
        uint ckind = mt != 0 ? KindOf(mt) : 0xff;
        string key = mp.ToString("x") + "|" + mt.ToString("x") + "|" + mf.ToString("x") + "|" + kind + "|" + ckind;
        if (!force && key == lastMkKey) return;
        lastMkKey = key; nMk++;
        if (mp != 0) { nMkFound++; mkKinds.Add(kind); if (kind == 22) nVeinFound++; }
        if (mt != 0) { nAttached++; if (ckind == 22) nVeinAtt++; }
        StringBuilder sb = new StringBuilder("Mk\t" + T() + "\t" + mp.ToString("x") + "\t" + G(dist) + "\t" + mt.ToString("x") + "\t" + mf.ToString("x") + "\t" + mw.ToString("x") + "\t" + (kind == 0xff ? "-" : kind.ToString()) + "\t" + (ckind == 0xff ? "-" : ckind.ToString()));
        byte[] mb = new byte[0x60]; if (mp != 0 && Rd(mp, mb)) for (int i = 0; i < 24; i++) sb.Append("\t" + BitConverter.ToUInt32(mb, 4 * i).ToString("x"));
        Log(sb.ToString());
    }

    static string lastPC = "";
    static void SamplePC(bool force)
    {
        byte[] a = new byte[0x30], b = new byte[0x10];
        if (!Rd(A_TUFX, a)) return; Rd(A_TUFIN, b);
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 12; i++) sb.Append((i > 0 ? "\t" : "") + BitConverter.ToUInt32(a, 4 * i).ToString("x"));
        for (int i = 0; i < 4; i++) sb.Append("\t" + BitConverter.ToUInt32(b, 4 * i).ToString("x"));
        string s = sb.ToString(); if (!force && s == lastPC) return; lastPC = s;
        Log("PC\t" + T() + "\t" + s);
    }

    static void SampleW()
    {
        try
        {
            proc.Refresh(); IntPtr hw = proc.MainWindowHandle; RECT r = new RECT();
            if (hw != IntPtr.Zero) GetWindowRect(hw, out r);
            gameFg = hw != IntPtr.Zero && GetForegroundWindow() == hw;
            Log("W\t" + T() + "\t" + hw.ToString() + "\t" + r.L + "\t" + r.T + "\t" + r.R + "\t" + r.B + "\t" + (GetForegroundWindow() == hw ? "fg" : "bg"));
        }
        catch { }
    }

    static void SampleRaw(long now)
    {
        if (rawFs == null) return;
        uint g = 0, L = 0, le = 0, fr = 0; U32(A_GAME, out g); if (g != 0) U32(g + 0x504, out L); U32(A_PLAYER, out le); U32(A_FRAME, out fr);
        byte[] bg = new byte[RAW_G], bl = new byte[RAW_L], bp = new byte[RAW_P];
        uint ok = 0;
        if (g != 0 && Rd(g, bg)) ok |= 1; else bg = new byte[RAW_G];
        if (L != 0 && Rd(L, bl)) ok |= 2; else bl = new byte[RAW_L];
        if (le != 0 && Rd(le, bp)) ok |= 4; else bp = new byte[RAW_P];
        if (ok == 0) { rawFail++; return; }
        rawOk++;
        try
        {
            byte[] hd = new byte[28];
            Array.Copy(BitConverter.GetBytes(0x31574152u), 0, hd, 0, 4); Array.Copy(BitConverter.GetBytes((uint)now), 0, hd, 4, 4); Array.Copy(BitConverter.GetBytes(fr), 0, hd, 8, 4);
            Array.Copy(BitConverter.GetBytes(g), 0, hd, 12, 4); Array.Copy(BitConverter.GetBytes(L), 0, hd, 16, 4); Array.Copy(BitConverter.GetBytes(le), 0, hd, 20, 4); Array.Copy(BitConverter.GetBytes(ok), 0, hd, 24, 4);
            rawFs.Write(hd, 0, hd.Length); rawFs.Write(bg, 0, bg.Length); rawFs.Write(bl, 0, bl.Length); rawFs.Write(bp, 0, bp.Length);
            rawBytes += hd.Length + bg.Length + bl.Length + bp.Length;
        }
        catch { }
    }

    // tastiera + mouse (GetAsyncKeyState, globale) e gamepad XInput; riga I a ogni cambio e comunque ogni 500 ms
    static void SampleInput(long now)
    {
        uint mask = 0;
        for (int i = 0; i < KEYS.Length && i < 32; i++) if ((GetAsyncKeyState(KEYS[i]) & 0x8000) != 0) mask |= 1u << i;
        XSTATE st = new XSTATE(); int xr = 1;
        if (!xiOff) { try { xr = XInputGetState(0, out st); } catch { xiOff = true; xr = 1; } }
        string key = mask.ToString("x") + "|" + (xr == 0 ? st.Btn + "," + st.LT + "," + st.RT + "," + (st.LX / 4096) + "," + (st.LY / 4096) + "," + (st.RX / 4096) + "," + (st.RY / 4096) : "-");
        if (key == lastIKey && now - lastIWrite < 500) return;
        lastIKey = key; lastIWrite = now; nInput++;
        Log("I\t" + T() + "\t" + mask.ToString("x") + "\t" + (xr == 0 ? st.Btn.ToString("x") + "\t" + st.LT + "\t" + st.RT + "\t" + st.LX + "\t" + st.LY + "\t" + st.RX + "\t" + st.RY : "-\t-\t-\t-\t-\t-\t-") + "\t" + (gameFg ? "fg" : "bg"));
    }

    // stato corrente del grafo di Lara (18/11, Traccia V): controllore = [game+0xf10], record stato = [ctrl+0x510];
    // indice = posizione del record nella tabella stati del DTP 20212 (base DTP = [[player+0x50]+0x584] - 0x32f70, tabella a +0x34a90, 1518 voci).
    // Riga "G <ms> <indice hex> <ptr record>" a ogni cambio; indice "?" se il record non e' nella tabella (DTP diverso, es. Lara base).
    static uint lastStatePtr = 0, stTabBase = 0; static uint[] stTab = null;
    static void LogState(uint g, uint le)
    {
        uint ctrl, sp, obj, b1;
        if (g == 0 || !U32(g + 0xf10, out ctrl) || ctrl == 0 || !U32(ctrl + 0x510, out sp) || sp == lastStatePtr) return;
        lastStatePtr = sp;
        string idx = "?";
        if (le != 0 && U32(le + 0x50, out obj) && obj != 0 && U32(obj + 0x584, out b1) && b1 > 0x32f70)
        {
            uint tab = b1 - 0x32f70 + 0x34a90;
            if (stTab == null || stTabBase != tab)
            {
                byte[] raw = new byte[1518 * 4];
                if (Rd(tab, raw)) { stTab = new uint[1518]; for (int i = 0; i < 1518; i++) stTab[i] = BitConverter.ToUInt32(raw, 4 * i); stTabBase = tab; }
            }
            if (stTab != null) { int k = Array.IndexOf(stTab, sp); if (k >= 0) idx = k.ToString("x"); }
        }
        Log("G\t" + T() + "\t" + idx + "\t" + sp.ToString("x"));
    }

    // trigger automatici: stato di scivolata (Lara+0x1fc == 0x25d8000) o velocita' orizzontale > 2500 u/s per 3 campioni; max 4 dump, 45 s di pausa
    static void CheckTrig(long now, string dumpMode)
    {
        uint g = 0, L = 0, lf = 0, le = 0; U32(A_GAME, out g); if (g != 0) U32(g + 0x504, out L); if (L != 0) U32(L + 0x1fc, out lf);
        U32(A_PLAYER, out le);
        float x = 0, y = 0; bool okp = false;
        if (le != 0) { byte[] pb = new byte[12]; if (Rd(le + 0x20, pb)) { x = BitConverter.ToSingle(pb, 4); y = BitConverter.ToSingle(pb, 8); okp = true; } }
        string lfh = lf.ToString("x");
        if (lfh != lastLfHex) { lastLfHex = lfh; Log("L\t" + T() + "\t" + lfh); }
        LogState(g, le);
        double v = 0;
        if (okp && pT >= 0 && now - pT >= 15 && now - pT <= 200) { double dx = x - pX, dy = y - pY; v = Math.Sqrt(dx * dx + dy * dy) * 1000.0 / (now - pT); }
        if (okp) { pX = x; pY = y; pT = now; } else pT = -1;
        if (v > 2500 && v < 40000) dashRun++; else dashRun = 0;
        string why = null;
        if (lf == 0x25d8000) why = "stato 0x25d8000 (scivolata)"; else if (dashRun >= 3) why = "velocita' orizzontale " + v.ToString("F0") + " u/s";
        if (why == null) return;
        if (now - lastTrigDump < 45000) return;
        nTrig++; burstUntil = now + 20000; lastTrigDump = now; dashRun = 0;
        Log("K\t" + T() + "\t" + (1000 + nTrig) + "\ttrigger " + why);
        Ev("TRIGGER " + nTrig + ": " + why + "  fps=" + fpsNow.ToString("F0"));
        if (dumpMode != "None" && nTrigDumps < 4) { nTrigDumps++; try { Console.Beep(700, 100); } catch { } Mark(true, dumpMode); }
    }

    static void SampleHealth()
    {
        uint g = 0, L = 0, le = 0; U32(A_GAME, out g); if (g != 0) U32(g + 0x504, out L); U32(A_PLAYER, out le);
        Log("H\t" + T() + "\tgame=" + g.ToString("x") + " lara=" + L.ToString("x") + " player=" + le.ToString("x") + " rawOk=" + rawOk + " rawFail=" + rawFail + " rawMB=" + (rawBytes >> 20) + " input=" + nInput + " trig=" + nTrig + " dump=" + nDumps + " err=" + errCount + " fg=" + gameFg);
    }

    static void PrintStatus()
    {
        uint g = 0, L = 0, lf = 0, mp = 0, mt = 0; U32(A_GAME, out g);
        if (g != 0) { U32(g + 0x504, out L); U32(g + 0xa64, out mp); U32(g + 0xc94, out mt); }
        uint mk = KindOf(mp), ck = KindOf(mt);
        if (L != 0) U32(L + 0x1fc, out lf);
        string fl = fpsNow < 1 ? "fermo/caricamento" : (fpsNow > 62.5 ? "SOPRA 60 <-- limita a 60" : "ok");
        Console.WriteLine("  [" + (sw.ElapsedMilliseconds / 1000) + "s] fps=" + fpsNow.ToString("F0") + " (" + fl + ")  vena(tipo 22) trovata=" + (mk == 22 ? "SI" : (mp != 0 ? "no (altro markup tipo " + mk + ")" : "no")) + "  agganciata=" + (ck == 22 ? "SI" : (mt != 0 ? "altro markup" : "no")) + "  marcatori=" + nMarks);
    }

    static void Mark(bool heavy, string dumpMode)
    {
        nMarks++; int n = nMarks;
        Ev("MARCATORE " + n + (heavy ? " (con screenshot e dump: il gioco si blocchera' per qualche secondo)" : "") + "  fps=" + fpsNow.ToString("F0"));
        try { Console.Beep(heavy ? 600 : 900, 120); } catch { }
        Log("K\t" + T() + "\t" + n + "\t" + (heavy ? "dump" : "marcatore"));
        SampleS(sw.ElapsedMilliseconds); SampleX(); SampleMk(true); SamplePC(true); SampleW();
        if (heavy) Screenshot(n);
        if (heavy)
        {
            ScanLog("marcatore" + n);
            if (dumpMode != "None") TakeDump("m" + n, dumpMode);
        }
        try { tsv.Flush(); } catch { }
    }

    static void Screenshot(int n)
    {
        try
        {
            proc.Refresh(); IntPtr hw = proc.MainWindowHandle; RECT r = new RECT(); bool ok = false;
            if (hw != IntPtr.Zero && GetWindowRect(hw, out r) && r.R - r.L > 100 && r.B - r.T > 100 && r.L > -10000) ok = true;
            if (!ok) { r.L = 0; r.T = 0; r.R = System.Windows.Forms.Screen.PrimaryScreen.Bounds.Width; r.B = System.Windows.Forms.Screen.PrimaryScreen.Bounds.Height; }
            using (Bitmap bmp = new Bitmap(r.R - r.L, r.B - r.T))
            {
                using (Graphics gr = Graphics.FromImage(bmp)) gr.CopyFromScreen(r.L, r.T, 0, 0, bmp.Size);
                string p = Path.Combine(outDir, "shot_" + tag + "_" + n + ".png"); bmp.Save(p, ImageFormat.Png); nShots++;
                Ev("  screenshot: " + Path.GetFileName(p) + (ok ? "" : " (schermo intero: finestra non trovata)"));
            }
        }
        catch (Exception e) { Ev("  screenshot non riuscito: " + e.Message); }
    }

    static void TakeDump(string label, string mode)
    {
        try
        {
            dumpSeq++;
            string p = Path.Combine(outDir, "dump_" + tag + "_" + dumpSeq + "_" + label + ".dmp");
            long free = 0; try { free = new DriveInfo(Path.GetPathRoot(Path.GetFullPath(p))).AvailableFreeSpace; } catch { }
            string m = mode;
            if (m == "Full" && free > 0 && free < 7L * 1024 * 1024 * 1024) { m = "Mini"; Ev("  spazio libero scarso (" + (free >> 20) + " MB): dump ridotto"); }
            int type = m == "Full" ? 0x1006 : 0x1065;
            Ev("  dump " + m + " in corso (puo' richiedere 10-60 s)...");
            Stopwatch s2 = Stopwatch.StartNew();
            FileStream fs = File.Create(p); bool ok;
            IntPtr dh = h; try { dh = proc.Handle; } catch { }
            try { ok = MiniDumpWriteDump(dh, (uint)pid, fs.SafeFileHandle.DangerousGetHandle(), type, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero); } finally { fs.Close(); }
            long sz = new FileInfo(p).Length; if (ok) nDumps++;
            Ev("  dump " + (ok ? "OK" : "FALLITO (err " + Marshal.GetLastWin32Error() + ")") + ": " + Path.GetFileName(p) + "  " + (sz >> 20) + " MB in " + (s2.ElapsedMilliseconds / 1000) + " s");
            Log("A\t" + T() + "\tdump " + Path.GetFileName(p) + " ok=" + ok + " " + sz);
        }
        catch (Exception e) { Ev("  dump non riuscito: " + e.Message); }
    }

    // log del motore (buffer ImGui dell'hook ModLoader): cerca in memoria la stringa iniziale e copia il testo piu' lungo
    static void ScanLog(string why)
    {
        try
        {
            byte[] pat = Encoding.ASCII.GetBytes("cdc::JobChainImplWithThreads::StartSystem");
            string best = null; long addr = 0x10000; byte[] buf = new byte[1 << 20];
            while (addr < 0xFFFF0000L)
            {
                MBI m; if (VirtualQueryEx(h, PL(addr), out m, Marshal.SizeOf(typeof(MBI))) == 0) break;
                long size = SzOf(m.Size); if (size <= 0) break;
                if (m.State == 0x1000 && (m.Protect == 0x04 || m.Protect == 0x40) && m.Type == 0x20000)
                {
                    for (long off = 0; off < size; off += buf.Length - 64)
                    {
                        int want = (int)Math.Min(buf.Length, size - off), got;
                        if (!ReadProcessMemory(h, PL(addr + off), buf, want, out got) || got < pat.Length) continue;
                        for (int i = 0; i <= got - pat.Length; i++)
                        {
                            if (buf[i] != pat[0]) continue; int k = 1; while (k < pat.Length && buf[i + k] == pat[k]) k++;
                            if (k != pat.Length) continue;
                            List<byte> sb = new List<byte>(); long p = addr + off + i; byte[] one = new byte[65536];
                            while (sb.Count < (16 << 20))
                            {
                                int r; if (!ReadProcessMemory(h, PL(p), one, one.Length, out r) || r == 0) break;
                                int z = Array.IndexOf(one, (byte)0, 0, r); if (z >= 0) { for (int j = 0; j < z; j++) sb.Add(one[j]); break; }
                                for (int j = 0; j < r; j++) sb.Add(one[j]); p += r;
                            }
                            string s = Encoding.GetEncoding(1252).GetString(sb.ToArray());
                            if (best == null || s.Length > best.Length) best = s;
                        }
                    }
                }
                addr += size;
            }
            if (best != null) { File.WriteAllText(Path.Combine(outDir, "engine_" + tag + "_pid" + pid + ".log"), best, Encoding.UTF8); if (why != "auto") Ev("  log del motore salvato (" + best.Length + " car.)"); }
            else if (why != "auto") Ev("  log del motore non trovato (ModLoader/hook assente?)");
        }
        catch (Exception e) { if (why != "auto") Ev("  lettura log motore non riuscita: " + e.Message); }
    }

    static string Summary()
    {
        StringBuilder s = new StringBuilder();
        long tot = 0; for (int i = 0; i < 7; i++) tot += fpsBucketMs[i];
        s.AppendLine("RIEPILOGO LIVE (" + tag + ")  durata " + (sw.ElapsedMilliseconds / 1000) + " s   exe in memoria: " + patchState);
        if (exePath != "") s.AppendLine("Exe: " + exePath);
        if (exitInfo != "") s.AppendLine("Fine: " + exitInfo);
        s.AppendLine("");
        s.AppendLine("FPS reali (variazione del contatore frame del gioco; il gioco va bloccato a 60):");
        for (int i = 0; i < 7; i++) s.AppendLine("  " + bucketName[i].PadRight(28) + (tot > 0 ? (100.0 * fpsBucketMs[i] / tot).ToString("F0").PadLeft(4) + " %" : "  n/d"));
        if (fpsSamples.Count > 0)
        {
            fpsSamples.Sort(); s.AppendLine("  mediana " + fpsSamples[fpsSamples.Count / 2].ToString("F0") + "  p95 " + fpsSamples[(int)(fpsSamples.Count * 0.95)].ToString("F0") + "  max " + fpsMax.ToString("F0"));
            double above = 0; foreach (double d in fpsSamples) if (d > 62.5) above++;
            if (above / fpsSamples.Count > 0.2) s.AppendLine("  >>> SOPRA 60 fps per il " + (100 * above / fpsSamples.Count).ToString("F0") + " % del tempo: fisica, camera e wall-run NON sono affidabili cosi'. Blocca a 60 e riprova.");
            else s.AppendLine("  fps compatibili con il blocco a 60.");
        }
        else s.AppendLine("  nessun campione fps (il gioco e' rimasto fermo/in caricamento o il contatore non avanza).");
        s.AppendLine("");
        s.AppendLine("WALL-RUN (ricerca markup del gioco, game+0xa64 / agganciato game+0xc94):");
        s.AppendLine("  variazioni registrate: " + nMk + "   markup di qualsiasi tipo trovato: " + nMkFound + " volte, agganciato: " + nAttached + " volte");
        s.AppendLine("  VENA (tipo 22): trovata " + nVeinFound + " volte, agganciata " + nVeinAtt + " volte");
        string kinds = ""; foreach (uint k in mkKinds) kinds += (kinds == "" ? "" : ",") + (k == 0xff ? "?" : k.ToString());
        s.AppendLine("  tipi di markup visti: " + (kinds == "" ? "nessuno" : kinds) + "   (la vena e' di tipo 22)");
        if (nVeinFound == 0) s.AppendLine("  >>> nessuna vena (markup tipo 22) e' mai stata TROVATA dalla ricerca del gioco" + (nMarks == 0 ? " (e non hai premuto il marcatore: se non hai provato la vena e' normale)" : "") + ": problema a monte (dati markup/posizione/stato/fps).");
        else if (nVeinAtt == 0) s.AppendLine("  >>> la vena e' stata trovata ma mai AGGANCIATA: manca il passaggio di attach (patch del caso 608) o la condizione non scatta.");
        else s.AppendLine("  la vena e' stata trovata e agganciata almeno una volta.");
        s.AppendLine("");
        s.AppendLine("Marcatori: " + nMarks + "   screenshot: " + nShots + "   dump: " + nDumps + "   trigger automatici: " + nTrig);
        s.AppendLine("Registro grezzo: " + rawOk + " campioni validi, " + rawFail + " falliti, " + (rawBytes >> 20) + " MB;  righe input: " + nInput + ";  errori nel ciclo: " + errCount);
        if (rawOk == 0) s.AppendLine("  >>> il registro grezzo e' VUOTO: gli indirizzi del gioco non rispondono (gioco in menu/caricamento per tutto il tempo, o exe diverso).");
        string res = s.ToString();
        try { File.WriteAllText(Path.Combine(outDir, "LIVE_SUMMARY_" + tag + ".txt"), res, new UTF8Encoding(false)); } catch { }
        return res;
    }
}
