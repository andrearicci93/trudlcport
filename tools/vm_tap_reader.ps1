# vm_tap_reader.ps1 - lettore del 'log tap' S1 di tru.exe (PowerShell 5.1 A 32 BIT, da SysWOW64).
# Solo lettura di memoria (ReadProcessMemory). Spec: PIANO_SONNET.md Appendice C; layout ring: tools/tap_stubs.py.
#   powershell -NoProfile -ExecutionPolicy Bypass -File Z:\tru-port\tools\vm_tap_reader.ps1 -RunId r001 -Seconds 300
#   powershell -NoProfile -ExecutionPolicy Bypass -File Z:\tru-port\tools\vm_tap_reader.ps1 -SelfTest
# Output: Z:\tru-port\work\taps\<RunId>\tap.tsv (seq,t,chan,ret,tid,text), tap_summary.tsv (ret,fmt,count,primo_testo), status.txt
# Esiti (status.txt + exit code): RUNNING/DONE (0), SELFTEST (0/1), SITES_MISMATCH (3), NO_TAP (4), NO_32BIT (5), NO_PROCESS (6)
param(
    [string]$RunId = '',
    [int]$Seconds = 300,
    [int]$MaxPerSite = 200,
    [switch]$SelfTest,
    [string]$Root = 'Z:\tru-port',
    [string]$Sites = ''
)
$ErrorActionPreference = 'Stop'

$Src = @'
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Runtime.InteropServices;
using System.Text;

public interface TapMem
{
    bool Read(uint addr, byte[] buf, int n);
}

// Memoria finta per -SelfTest: segmenti (base, dati).
public sealed class TapFakeMem : TapMem
{
    private readonly List<KeyValuePair<uint, byte[]>> segs = new List<KeyValuePair<uint, byte[]>>();

    public void Add(uint baseAddr, byte[] data)
    {
        segs.Add(new KeyValuePair<uint, byte[]>(baseAddr, data));
    }

    public void AddString(uint addr, string s)
    {
        byte[] b = new byte[s.Length + 1];
        for (int i = 0; i < s.Length; i++) b[i] = (byte)s[i];
        Add(addr, b);
    }

    public bool Read(uint addr, byte[] buf, int n)
    {
        foreach (KeyValuePair<uint, byte[]> kv in segs)
        {
            if (addr < kv.Key) continue;
            ulong off = (ulong)(addr - kv.Key);
            if (off + (ulong)n > (ulong)kv.Value.Length) continue;
            Array.Copy(kv.Value, (int)off, buf, 0, n);
            return true;
        }
        return false;
    }
}

// Memoria reale: ReadProcessMemory su un processo a 32 bit.
public sealed class TapProcMem : TapMem, IDisposable
{
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool ReadProcessMemory(IntPtr h, IntPtr addr, byte[] buf, IntPtr size, out IntPtr read);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr h);

    private IntPtr h;

    public TapProcMem(uint pid)
    {
        // PROCESS_VM_READ | PROCESS_QUERY_INFORMATION
        h = OpenProcess(0x0010 | 0x0400, false, pid);
    }

    public bool IsOpen
    {
        get { return h != IntPtr.Zero; }
    }

    public bool Read(uint addr, byte[] buf, int n)
    {
        if (h == IntPtr.Zero) return false;
        IntPtr got;
        if (!ReadProcessMemory(h, new IntPtr(unchecked((int)addr)), buf, new IntPtr(n), out got)) return false;
        return got.ToInt64() == n;
    }

    public void Dispose()
    {
        if (h != IntPtr.Zero) { CloseHandle(h); h = IntPtr.Zero; }
    }
}

public sealed class TapSite
{
    public string Fmt = "";
    public int FmtArg = -1;
}

// Formattatore printf (MSVC) su dword di argomenti. a[] = arg0..arg11 dal ring (a[fmtIdx] = puntatore al fmt).
public static class TapFmt
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    // sites.tsv scrive il fmt con \n escapato (tap_sites.py): si inverte qui.
    public static string Unescape(string s)
    {
        return s.Replace("\\n", "\n").Replace("\\t", "\t");
    }

    // Per il TSV: niente TAB/CR/LF, solo ASCII stampabile.
    public static string Escape(string s)
    {
        StringBuilder sb = new StringBuilder();
        foreach (char c in s)
        {
            if (c == '\n') sb.Append("\\n");
            else if (c == '\r') sb.Append("\\r");
            else if (c == '\t') sb.Append("\\t");
            else if (c < 32 || c > 126) sb.Append('?');
            else sb.Append(c);
        }
        return sb.ToString();
    }

    private static bool Take(uint[] a, ref int ai, out uint v)
    {
        if (ai < 0 || ai >= a.Length) { v = 0; return false; }
        v = a[ai];
        ai++;
        return true;
    }

    private static bool TakeWide(uint[] a, ref int ai, bool big, out ulong v)
    {
        uint lo;
        uint hi;
        v = 0;
        if (!Take(a, ref ai, out lo)) return false;
        if (!big) { v = lo; return true; }
        if (!Take(a, ref ai, out hi)) return false;
        v = ((ulong)hi << 32) | lo;
        return true;
    }

    // Legge una stringa C (max 'max' byte). null se il primo byte non e' leggibile.
    public static string ReadCString(TapMem mem, uint p, int max)
    {
        if (mem == null) return null;
        StringBuilder sb = new StringBuilder();
        byte[] one = new byte[1];
        for (int k = 0; k < max; k++)
        {
            if (!mem.Read(p + (uint)k, one, 1)) return sb.Length == 0 ? null : sb.ToString();
            if (one[0] == 0) break;
            sb.Append(one[0] >= 32 && one[0] < 127 ? (char)one[0] : '?');
        }
        return sb.ToString();
    }

    private static string ExpForm(double v, int prec, bool upper)
    {
        string es = v.ToString("E" + prec.ToString(Inv), Inv);
        int e = es.IndexOf('E');
        int ex = int.Parse(es.Substring(e + 1), NumberStyles.AllowLeadingSign, Inv);
        return es.Substring(0, e) + (upper ? "E" : "e") + (ex < 0 ? "-" : "+") + Math.Abs(ex).ToString("00", Inv);
    }

    // v >= 0 finito.
    private static string FormatFloat(double v, char conv, int prec)
    {
        bool upper = char.IsUpper(conv);
        char k = char.ToLowerInvariant(conv);
        if (k == 'f') return v.ToString("F" + prec.ToString(Inv), Inv);
        if (k == 'e') return ExpForm(v, prec, upper);
        int p = prec == 0 ? 1 : prec;
        string es = v.ToString("E" + (p - 1).ToString(Inv), Inv);
        int ep = es.IndexOf('E');
        int x = int.Parse(es.Substring(ep + 1), NumberStyles.AllowLeadingSign, Inv);
        if (x < p && x >= -4)
        {
            string f = v.ToString("F" + (p - 1 - x).ToString(Inv), Inv);
            if (f.IndexOf('.') >= 0) f = f.TrimEnd('0').TrimEnd('.');
            return f;
        }
        string s = ExpForm(v, p - 1, upper);
        int e = s.IndexOfAny(new char[] { 'e', 'E' });
        string m = s.Substring(0, e);
        if (m.IndexOf('.') >= 0) m = m.TrimEnd('0').TrimEnd('.');
        return m + s.Substring(e);
    }

    public static string Format(string fmt, uint[] a, int fmtIdx, TapMem mem)
    {
        StringBuilder sb = new StringBuilder();
        int ai = fmtIdx + 1;
        int i = 0;
        while (i < fmt.Length)
        {
            char c = fmt[i];
            if (c != '%') { sb.Append(c); i++; continue; }
            if (i + 1 < fmt.Length && fmt[i + 1] == '%') { sb.Append('%'); i += 2; continue; }
            int start = i;
            i++;
            string flags = "";
            while (i < fmt.Length && "-+ #0".IndexOf(fmt[i]) >= 0) { flags += fmt[i]; i++; }
            bool miss = false;
            int width = -1;
            if (i < fmt.Length && fmt[i] == '*')
            {
                uint wv;
                if (Take(a, ref ai, out wv)) width = (int)wv; else miss = true;
                i++;
            }
            else
            {
                int w0 = i;
                while (i < fmt.Length && char.IsDigit(fmt[i])) i++;
                if (i > w0) width = int.Parse(fmt.Substring(w0, i - w0), NumberStyles.None, Inv);
            }
            int prec = -1;
            if (i < fmt.Length && fmt[i] == '.')
            {
                i++;
                prec = 0;
                if (i < fmt.Length && fmt[i] == '*')
                {
                    uint pv;
                    if (Take(a, ref ai, out pv)) prec = (int)pv; else miss = true;
                    i++;
                }
                else
                {
                    int p0 = i;
                    while (i < fmt.Length && char.IsDigit(fmt[i])) i++;
                    if (i > p0) prec = int.Parse(fmt.Substring(p0, i - p0), NumberStyles.None, Inv);
                }
            }
            int hcount = 0;
            bool big = false;
            while (i < fmt.Length && "hlLqjztI".IndexOf(fmt[i]) >= 0)
            {
                char m = fmt[i];
                if (m == 'h') hcount++;
                else if (m == 'l') { if (i + 1 < fmt.Length && fmt[i + 1] == 'l') big = true; }
                else if (m == 'q' || m == 'j') big = true;
                else if (m == 'I')
                {
                    if (i + 2 < fmt.Length && fmt[i + 1] == '6' && fmt[i + 2] == '4') { big = true; i += 2; }
                    else if (i + 2 < fmt.Length && fmt[i + 1] == '3' && fmt[i + 2] == '2') { i += 2; }
                }
                i++;
            }
            if (i >= fmt.Length) { sb.Append(fmt.Substring(start)); break; }
            char conv = fmt[i];
            i++;
            if (miss) { sb.Append('?'); continue; }

            string pre = "";
            string body = "";
            bool zeroOk = true;
            switch (conv)
            {
                case 'd':
                case 'i':
                case 'u':
                case 'x':
                case 'X':
                case 'o':
                {
                    ulong uv;
                    if (!TakeWide(a, ref ai, big, out uv)) { sb.Append('?'); continue; }
                    int bits = big ? 64 : (hcount >= 2 ? 8 : (hcount == 1 ? 16 : 32));
                    if (bits < 64) uv &= (1UL << bits) - 1UL;
                    bool isSigned = conv == 'd' || conv == 'i';
                    string digits;
                    if (isSigned)
                    {
                        long sv = (long)uv;
                        if (bits < 64 && (uv & (1UL << (bits - 1))) != 0) sv = (long)uv - (1L << bits);
                        if (sv < 0) pre = "-";
                        else if (flags.IndexOf('+') >= 0) pre = "+";
                        else if (flags.IndexOf(' ') >= 0) pre = " ";
                        ulong mag = sv < 0 ? (ulong)(-(sv + 1)) + 1UL : (ulong)sv;
                        digits = mag.ToString(Inv);
                    }
                    else if (conv == 'u') digits = uv.ToString(Inv);
                    else if (conv == 'x') digits = uv.ToString("x", Inv);
                    else if (conv == 'X') digits = uv.ToString("X", Inv);
                    else digits = Convert.ToString((long)uv, 8);
                    if (prec >= 0)
                    {
                        if (prec == 0 && digits == "0") digits = "";
                        digits = digits.PadLeft(prec, '0');
                        zeroOk = false;
                    }
                    if (flags.IndexOf('#') >= 0)
                    {
                        if (conv == 'x' && uv != 0) pre += "0x";
                        else if (conv == 'X' && uv != 0) pre += "0X";
                        else if (conv == 'o' && (digits.Length == 0 || digits[0] != '0')) digits = "0" + digits;
                    }
                    body = digits;
                    break;
                }
                case 'c':
                {
                    uint cv;
                    if (!Take(a, ref ai, out cv)) { sb.Append('?'); continue; }
                    body = ((char)(cv & 0xFF)).ToString();
                    zeroOk = false;
                    break;
                }
                case 'p':
                {
                    uint pv2;
                    if (!Take(a, ref ai, out pv2)) { sb.Append('?'); continue; }
                    body = pv2.ToString("X8", Inv);
                    zeroOk = false;
                    break;
                }
                case 's':
                {
                    uint sp;
                    if (!Take(a, ref ai, out sp)) { sb.Append('?'); continue; }
                    string str;
                    if (sp == 0) str = "(null)";
                    else str = ReadCString(mem, sp, 1024) ?? ("<badptr " + sp.ToString("X8", Inv) + ">");
                    if (prec >= 0 && str.Length > prec) str = str.Substring(0, prec);
                    body = str;
                    zeroOk = false;
                    break;
                }
                case 'f':
                case 'F':
                case 'e':
                case 'E':
                case 'g':
                case 'G':
                {
                    ulong dbits;
                    if (!TakeWide(a, ref ai, true, out dbits)) { sb.Append('?'); continue; }
                    double d = BitConverter.Int64BitsToDouble((long)dbits);
                    if (d < 0) pre = "-";
                    else if (flags.IndexOf('+') >= 0) pre = "+";
                    else if (flags.IndexOf(' ') >= 0) pre = " ";
                    if (double.IsNaN(d)) body = "nan";
                    else if (double.IsInfinity(d)) body = "inf";
                    else body = FormatFloat(Math.Abs(d), conv, prec < 0 ? 6 : prec);
                    break;
                }
                default:
                    sb.Append(fmt.Substring(start, i - start));
                    continue;
            }

            string full;
            int len = pre.Length + body.Length;
            if (width > len)
            {
                int padn = width - len;
                if (flags.IndexOf('-') >= 0) full = pre + body + new string(' ', padn);
                else if (zeroOk && flags.IndexOf('0') >= 0) full = pre + new string('0', padn) + body;
                else full = new string(' ', padn) + pre + body;
            }
            else full = pre + body;
            sb.Append(full);
        }
        return sb.ToString();
    }
}

public sealed class TapEv
{
    public uint Seq;
    public uint Ret;
    public uint Tid;
    public uint Chan;
    public uint[] A = new uint[12];
}

// Seqlock sul ring. Layout: T+4 contatore (numero di scritture iniziate); slot i a T+0x1000+64*i:
// +0 seq (0 = in scrittura, altrimenti n = 1-based), +4 ret, +8 tid, +0xC canale, +0x10.. arg0..arg11.
// Lo slot per l'evento s (1-based) e' (s-1)&0xfff.
public sealed class TapReader
{
    public const uint SlotSize = 64;
    public const uint NSlot = 4096;

    private readonly TapMem mem;
    private readonly uint tapBase;
    public ulong Last;
    public ulong Lost;

    public TapReader(TapMem m, uint tapBaseAddr)
    {
        mem = m;
        tapBase = tapBaseAddr;
    }

    private static uint U32(byte[] b, int off)
    {
        return BitConverter.ToUInt32(b, off);
    }

    // Eventi nuovi (max maxEvents). null = lettura di memoria fallita (processo morto?).
    public List<TapEv> Poll(int maxEvents)
    {
        List<TapEv> res = new List<TapEv>();
        byte[] cb = new byte[4];
        if (!mem.Read(tapBase + 4, cb, 4)) return null;
        ulong cur = U32(cb, 0);
        if (cur < Last) Last = cur;
        if (cur > Last + NSlot)
        {
            Lost += cur - NSlot - Last;
            Last = cur - NSlot;
        }
        byte[] slot = new byte[SlotSize];
        byte[] s2 = new byte[4];
        while (Last < cur && res.Count < maxEvents)
        {
            ulong s = Last + 1;
            uint addr = tapBase + 0x1000 + (uint)(((s - 1) & (NSlot - 1)) * SlotSize);
            if (!mem.Read(addr, slot, (int)SlotSize)) return null;
            ulong seq1 = U32(slot, 0);
            if (seq1 == 0 || seq1 < s) break;            // in scrittura: riprova al prossimo giro
            if (seq1 > s) { Lost++; Last = s; continue; } // sovrascritto
            if (!mem.Read(addr, s2, 4)) return null;
            ulong seq2 = U32(s2, 0);
            if (seq2 != seq1)
            {
                if (seq2 > s) { Lost++; Last = s; continue; }
                break;
            }
            TapEv e = new TapEv();
            e.Seq = (uint)s;
            e.Ret = U32(slot, 4);
            e.Tid = U32(slot, 8);
            e.Chan = U32(slot, 12);
            for (int k = 0; k < 12; k++) e.A[k] = U32(slot, 16 + 4 * k);
            res.Add(e);
            Last = s;
        }
        return res;
    }
}

// Testo degli eventi: sito (ret) -> fmt + indice fmt. Canali A/B: layout identico. Probe (0xC0000|id): ecx,edx,args.
public sealed class TapText
{
    public TapMem Mem;
    private readonly Dictionary<uint, TapSite> sites = new Dictionary<uint, TapSite>();

    public void AddSite(uint ret, string fmt, int fmtArg)
    {
        TapSite s = new TapSite();
        s.Fmt = fmt;
        s.FmtArg = fmtArg;
        sites[ret] = s;
    }

    public int Count
    {
        get { return sites.Count; }
    }

    public string FmtOf(uint ret)
    {
        TapSite s;
        return sites.TryGetValue(ret, out s) ? s.Fmt : "";
    }

    private static string Hex(uint[] a, int from, int n)
    {
        StringBuilder sb = new StringBuilder();
        for (int k = from; k < from + n && k < a.Length; k++)
        {
            if (sb.Length > 0) sb.Append(' ');
            sb.Append("0x" + a[k].ToString("x8", CultureInfo.InvariantCulture));
        }
        return sb.ToString();
    }

    public string Format(TapEv e)
    {
        string text;
        if ((e.Chan & 0xFFFF0000u) == 0xC0000u)
        {
            text = "probe" + (e.Chan & 0xFFFFu).ToString(CultureInfo.InvariantCulture)
                 + " ecx=" + e.A[0].ToString("x8", CultureInfo.InvariantCulture)
                 + " edx=" + e.A[1].ToString("x8", CultureInfo.InvariantCulture)
                 + " args " + Hex(e.A, 2, 10);
        }
        else
        {
            TapSite s;
            if (!sites.TryGetValue(e.Ret, out s))
            {
                text = "[nosite] " + Hex(e.A, 0, 4);
            }
            else
            {
                string fmt = s.Fmt;
                int fa = s.FmtArg;
                if (fa >= 0 && fa < 12 && fmt.Length == 0 && Mem != null)
                {
                    fmt = TapFmt.ReadCString(Mem, e.A[fa], 512) ?? "";
                }
                if (fa < 0 || fmt.Length == 0) text = "[nofmt] " + Hex(e.A, 0, 4);
                else text = TapFmt.Format(TapFmt.Unescape(fmt), e.A, fa, Mem);
            }
        }
        return TapFmt.Escape(text);
    }
}

// Autotest senza processo: formattatore + seqlock su memoria finta. Restituisce gli errori (vuoto = OK).
public static class TapSelfTest
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    private static uint[] Dbl(double d)
    {
        long bits = BitConverter.DoubleToInt64Bits(d);
        return new uint[] { (uint)(bits & 0xFFFFFFFFL), (uint)((ulong)bits >> 32) };
    }

    private static void Case(List<string> errs, TapMem mem, string fmt, string exp, params object[] parts)
    {
        List<uint> vals = new List<uint>();
        foreach (object p in parts)
        {
            if (p is uint) vals.Add((uint)p);
            else if (p is int) vals.Add(unchecked((uint)(int)p));
            else if (p is uint[]) vals.AddRange((uint[])p);
            else errs.Add("parte non valida nel caso " + fmt);
        }
        uint[] a = new uint[12];
        a[0] = 0xA;
        a[1] = 0x1000;
        for (int k = 0; k < vals.Count && k + 2 < 12; k++) a[k + 2] = vals[k];
        string got = TapFmt.Format(fmt, a, 1, mem);
        if (got != exp) errs.Add("FMT [" + fmt + "] ottenuto [" + got + "] atteso [" + exp + "]");
    }

    private static void Put32(byte[] b, int off, uint v)
    {
        byte[] t = BitConverter.GetBytes(v);
        Array.Copy(t, 0, b, off, 4);
    }

    private static void Slot(byte[] seg, ulong s, uint ret, uint chan, uint arg0)
    {
        int off = 0x1000 + (int)(((s - 1) & 0xFFF) * 64);
        Put32(seg, off, (uint)s);
        Put32(seg, off + 4, ret);
        Put32(seg, off + 8, 77);
        Put32(seg, off + 12, chan);
        Put32(seg, off + 16, arg0);
    }

    private static void RingTests(List<string> errs)
    {
        const uint T = 0x1236000;

        // A: 3 eventi validi, con un canale B
        byte[] segA = new byte[0x41000];
        Put32(segA, 4, 3);
        Slot(segA, 1, 0x454c62, 0xA, 11);
        Slot(segA, 2, 0x454c62, 0xA, 22);
        Slot(segA, 3, 0x454c62, 0xB, 33);
        TapFakeMem memA = new TapFakeMem();
        memA.Add(T, segA);
        TapReader rA = new TapReader(memA, T);
        List<TapEv> evA = rA.Poll(100000);
        if (evA == null || evA.Count != 3 || evA[2].A[0] != 33 || evA[2].Chan != 0xB || rA.Lost != 0)
            errs.Add("ring A: eventi " + (evA == null ? "null" : evA.Count.ToString(Inv)));

        // B: 4100 scritture, nessun slot letto prima -> 4 persi, 4096 letti (s=5..4100)
        byte[] segB = new byte[0x41000];
        Put32(segB, 4, 4100);
        for (ulong s = 5; s <= 4100; s++) Slot(segB, s, 0x454c62, 0xA, (uint)s);
        TapFakeMem memB = new TapFakeMem();
        memB.Add(T, segB);
        TapReader rB = new TapReader(memB, T);
        List<TapEv> evB = rB.Poll(100000);
        if (evB == null || evB.Count != 4096 || rB.Lost != 4 || evB[0].Seq != 5 || evB[4095].Seq != 4100)
            errs.Add("ring B (persi): eventi " + (evB == null ? "null" : evB.Count.ToString(Inv)) + " persi " + rB.Lost.ToString(Inv));

        // C: slot 2 ancora in scrittura (seq 0): si ferma, poi riprende quando e' committato
        byte[] segC = new byte[0x41000];
        Put32(segC, 4, 2);
        Slot(segC, 1, 0x454c62, 0xA, 1);
        Put32(segC, 0x1000 + 64, 0);
        TapFakeMem memC = new TapFakeMem();
        memC.Add(T, segC);
        TapReader rC = new TapReader(memC, T);
        List<TapEv> evC1 = rC.Poll(100);
        Slot(segC, 2, 0x454c62, 0xA, 2);
        List<TapEv> evC2 = rC.Poll(100);
        if (evC1 == null || evC1.Count != 1 || evC2 == null || evC2.Count != 1 || evC2[0].Seq != 2)
            errs.Add("ring C (in scrittura)");
    }

    private static void TextTests(List<string> errs)
    {
        TapFakeMem mem = new TapFakeMem();
        mem.AddString(0x2000, "ab");
        TapText tt = new TapText();
        tt.Mem = mem;
        tt.AddSite(0x454c62, "CONTENT MISMATCH in intro %d (%s%d) - found %d bones, expected %d\\n", 1);
        TapEv e = new TapEv();
        e.Ret = 0x454c62;
        e.Chan = 0xA;
        e.A = new uint[] { 0xA, 0x1000, 1, 0x2000, 2, 3, 4, 0, 0, 0, 0, 0 };
        string got = tt.Format(e);
        string exp = "CONTENT MISMATCH in intro 1 (ab2) - found 3 bones, expected 4\\n";
        if (got != exp) errs.Add("TapText [" + got + "]");
        e.Ret = 0x999999;
        if (!tt.Format(e).StartsWith("[nosite]")) errs.Add("TapText nosite");
    }

    public static List<string> Run()
    {
        List<string> errs = new List<string>();
        TapFakeMem mem = new TapFakeMem();
        mem.AddString(0x1000, "abc");
        mem.AddString(0x2000, "ab");

        Case(errs, mem, "%d", "-5", -5);
        Case(errs, mem, "%u", "4294967295", 0xFFFFFFFFu);
        Case(errs, mem, "%x", "deadbeef", 0xDEADBEEFu);
        Case(errs, mem, "%08X", "0000002A", 0x2Au);
        Case(errs, mem, "0x%08x", "0x001c019f", 0x1C019Fu);
        Case(errs, mem, "%5d|%-5d|", "   42|42   |", 42, 42);
        Case(errs, mem, "%s", "abc", 0x1000u);
        Case(errs, mem, "%g", "1.5", Dbl(1.5));
        Case(errs, mem, "%f", "1.500000", Dbl(1.5));
        Case(errs, mem, "%g", "1e-05", Dbl(0.00001));
        Case(errs, mem, "%g", "1.23457e+08", Dbl(123456789.0));
        Case(errs, mem, "%.2f", "3.14", Dbl(3.14159));
        Case(errs, mem, "%lld", "-1", 0xFFFFFFFFu, 0xFFFFFFFFu);
        Case(errs, mem, "%%%c", "%A", 65);
        Case(errs, mem, "%p", "00001000", 0x1000u);
        Case(errs, mem, "%d%d%d%d%d%d%d%d%d%d%d", "1000000000?", 1);
        Case(errs, mem, "%hd", "-1", 0xFFFFu);
        Case(errs, mem, "%e", "1.500000e+00", Dbl(1.5));
        Case(errs, mem, "%i|%+d|% d", "3|+3| 3", 3, 3, 3);
        Case(errs, mem, "%03d", "007", 7);
        Case(errs, mem, "%.3d", "007", 7);
        Case(errs, mem, "%c", "A", 65);
        Case(errs, mem, "%g", "0", Dbl(0.0));
        Case(errs, mem, "%g", "-2.5", Dbl(-2.5));
        Case(errs, mem, "%lu", "4294967295", 0xFFFFFFFFu);
        Case(errs, mem, "CONTENT MISMATCH in intro %d (%s%d) - found %d bones, expected %d", "CONTENT MISMATCH in intro 1 (ab2) - found 3 bones, expected 4", 1, 0x2000u, 2, 3, 4);
        if (TapFmt.Unescape("a\\nb") != "a\nb") errs.Add("Unescape");

        RingTests(errs);
        TextTests(errs);
        return errs;
    }
}
'@

if ($SelfTest) {
    if (-not ('TapSelfTest' -as [type])) { Add-Type -TypeDefinition $Src -Language CSharp }
    $errs = [TapSelfTest]::Run()
    foreach ($x in $errs) { Write-Output ('FAIL ' + $x) }
    if ($errs.Count -eq 0) { Write-Output 'SELFTEST PASS'; exit 0 }
    Write-Output 'SELFTEST FAIL'
    exit 1
}

if ([IntPtr]::Size -ne 4) { Write-Output 'NO_32BIT: eseguire con C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe'; exit 5 }
if (-not $RunId) { Write-Output 'manca -RunId'; exit 2 }
if (-not ('TapReader' -as [type])) { Add-Type -TypeDefinition $Src -Language CSharp }

$T = [uint32]0x1236000
$inv = [Globalization.CultureInfo]::InvariantCulture
$utf8 = New-Object System.Text.UTF8Encoding $false
$outDir = Join-Path $Root ("work\taps\" + $RunId)
$tapPath = Join-Path $outDir 'tap.tsv'
if (Test-Path -LiteralPath $tapPath) { Write-Output ('RunId gia usato: ' + $outDir + ' (scegli un altro -RunId)'); exit 2 }
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

function Write-Status([string]$s) {
    [IO.File]::WriteAllText((Join-Path $outDir 'status.txt'), ($s + "`r`n"), $utf8)
    Write-Output $s
}

# Build id = primi 4 byte dell'md5 di sites_patched.tsv (scritti a T+0x14 da tap_stubs).
$sitesPath = Join-Path $Root 'work\ws\tap\sites_patched.tsv'
if ($Sites -ne '') { $sitesPath = $Sites }
if (-not (Test-Path -LiteralPath $sitesPath)) { Write-Status ('NO_SITES: manca ' + $sitesPath); exit 3 }
$hex = (Get-FileHash -LiteralPath $sitesPath -Algorithm MD5).Hash
$expect = New-Object byte[] 4
for ($k = 0; $k -lt 4; $k++) { $expect[$k] = [Convert]::ToByte($hex.Substring(2 * $k, 2), 16) }
$expectHex = (($expect | ForEach-Object { $_.ToString('x2') }) -join '')

# Tabella siti: ret_va -> fmt, fmt_arg (colonne per nome).
$txt = New-Object TapText
$hdr = $null
foreach ($line in [IO.File]::ReadAllLines($sitesPath)) {
    if ($line -eq '') { continue }
    $cols = $line -split "`t"
    if ($null -eq $hdr) { $hdr = $cols; continue }
    $iRet = [array]::IndexOf($hdr, 'ret_va')
    $iArg = [array]::IndexOf($hdr, 'fmt_arg')
    $iFmt = [array]::IndexOf($hdr, 'fmt')
    $rv = [Convert]::ToUInt32($cols[$iRet].Substring(2), 16)
    $fa = [int]$cols[$iArg]
    $f = ''
    if ($cols.Count -gt $iFmt) { $f = $cols[$iFmt] }
    $txt.AddSite([uint32]$rv, $f, $fa)
}

$sum = @{}
$wrote = @{}
function Write-Summary {
    $rows = @($sum.Values | Sort-Object -Property @{ Expression = 'count'; Descending = $true })
    $lines = New-Object 'System.Collections.Generic.List[string]'
    $lines.Add("ret`tfmt`tcount`tprimo_testo")
    foreach ($o in $rows) { $lines.Add(("{0}`t{1}`t{2}`t{3}" -f $o.ret, $o.fmt, $o.count, $o.first)) }
    [IO.File]::WriteAllLines((Join-Path $outDir 'tap_summary.tsv'), $lines.ToArray(), $utf8)
}

New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$wr = New-Object IO.StreamWriter($tapPath, $false, $utf8)
$wr.AutoFlush = $true
$wr.WriteLine("seq`tt`tchan`tret`ttid`ttext")
$sw = [Diagnostics.Stopwatch]::StartNew()
$swd = [Diagnostics.Stopwatch]::StartNew()   # cronometro: immune ai salti dell orologio della VM
$lastSum = Get-Date
$status = 'NO_PROCESS'
$exitCode = 6
$noTap = 0
$nAttach = 0
$mem = $null
try {
    Write-Status ('RUNNING sites=' + $txt.Count + ' build_md5=' + $expectHex + ' seconds=' + $Seconds)
    while ($swd.Elapsed.TotalSeconds -lt $Seconds) {
        $p = Get-Process -Name tru -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -eq $p) { Start-Sleep -Milliseconds 500; continue }
        $mem = New-Object TapProcMem -ArgumentList ([uint32]$p.Id)
        if (-not $mem.IsOpen) { $mem.Dispose(); $mem = $null; Start-Sleep -Milliseconds 500; continue }
        $memi = [TapMem]$mem
        $txt.Mem = $memi   # senza questa riga %s dava sempre <badptr> (ReadCString con mem null)
        $buf = New-Object byte[] 24
        if (-not $memi.Read($T, $buf, 24)) { $mem.Dispose(); $mem = $null; Start-Sleep -Milliseconds 500; continue }
        $sig = [Text.Encoding]::ASCII.GetString($buf, 0, 4)
        if ($sig -ne 'TAP1') {
            $mem.Dispose(); $mem = $null
            $noTap++
            if ($noTap -ge 20) { $status = 'NO_TAP'; $exitCode = 4; break }
            Start-Sleep -Milliseconds 500
            continue
        }
        $got = (($buf[20..23] | ForEach-Object { $_.ToString('x2') }) -join '')
        if ($got -ne $expectHex) {
            $status = ('SITES_MISMATCH read=' + $got + ' expect=' + $expectHex + ' (LE u32 letto=0x' + ([BitConverter]::ToUInt32($buf, 20)).ToString('x8') + ')')
            $exitCode = 3
            $mem.Dispose(); $mem = $null
            break
        }
        $noTap = 0
        $nAttach++
        $status = 'ATTACHED'
        $reader = New-Object TapReader -ArgumentList @($memi, [uint32]$T)
        $wr.WriteLine('#ATTACH pid=' + $p.Id + ' n=' + $nAttach + ' t=' + $sw.Elapsed.TotalSeconds.ToString('F3', $inv))
        $lastLost = [int64]0
        while (-not $p.HasExited -and $swd.Elapsed.TotalSeconds -lt $Seconds) {
            $evs = $reader.Poll(4096)
            if ($null -eq $evs) { break }
            foreach ($ev in $evs) {
                $k = [string]$ev.Ret
                $fmtS = $txt.FmtOf($ev.Ret)
                $text = $txt.Format($ev)
                if (-not $sum.ContainsKey($k)) {
                    $sum[$k] = [pscustomobject]@{ ret = ('0x{0:x}' -f $ev.Ret); fmt = $fmtS; count = 0; first = $text }
                }
                $o = $sum[$k]
                $o.count = $o.count + 1
                if (-not $wrote.ContainsKey($k)) { $wrote[$k] = 0 }
                if ($wrote[$k] -lt $MaxPerSite) {
                    $wrote[$k] = $wrote[$k] + 1
                    $tt = $sw.Elapsed.TotalSeconds.ToString('F3', $inv)
                    $wr.WriteLine(("{0}`t{1}`t{2}`t{3}`t{4}`t{5}" -f $ev.Seq, $tt, ('{0:X}' -f $ev.Chan), ('0x{0:x}' -f $ev.Ret), $ev.Tid, $text))
                }
            }
            $newLost = [int64]$reader.Lost
            if ($newLost -gt $lastLost) {
                $wr.WriteLine(("-1`t{0}`t-`t-`t-`tPERSI {1}" -f $sw.Elapsed.TotalSeconds.ToString('F3', $inv), ($newLost - $lastLost)))
                $lastLost = $newLost
            }
            if ((Get-Date) -gt $lastSum.AddSeconds(5)) { Write-Summary; $lastSum = Get-Date }
            Start-Sleep -Milliseconds 10
        }
        $wr.WriteLine('#DETACH pid=' + $p.Id + ' t=' + $sw.Elapsed.TotalSeconds.ToString('F3', $inv))
        $mem.Dispose(); $mem = $null
        $status = 'DETACHED'
        $exitCode = 0
    }
    if ($status -eq 'ATTACHED' -or $status -eq 'DETACHED') { $status = 'DONE' }
}
finally {
    if ($null -ne $mem) { $mem.Dispose() }
    Write-Summary
    $wr.Close()
    Write-Status ($status + ' attach=' + $nAttach + ' lost=' + $(if ($null -ne $reader) { $reader.Lost } else { 0 }))
}
exit $exitCode
