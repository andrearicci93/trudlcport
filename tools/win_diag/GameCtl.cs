// GameCtl: screenshot della finestra del gioco e invio di tasti/mouse via SendInput (scancode, funziona con DirectInput).
// Uso da PowerShell: Add-Type -Path GameCtl.cs -ReferencedAssemblies System.Drawing ; [GameCtl]::Shot("tru","C:\...\a.png")
using System;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using System.Threading;

public static class GameCtl
{
    [StructLayout(LayoutKind.Sequential)] struct RECT { public int L, T, R, B; }
    [StructLayout(LayoutKind.Sequential)] struct MOUSEINPUT { public int dx, dy; public uint data, flags, time; public IntPtr extra; }
    [StructLayout(LayoutKind.Sequential)] struct KEYBDINPUT { public ushort vk, scan; public uint flags, time; public IntPtr extra; }
    [StructLayout(LayoutKind.Explicit)] struct INPUTU { [FieldOffset(0)] public MOUSEINPUT mi; [FieldOffset(0)] public KEYBDINPUT ki; }
    [StructLayout(LayoutKind.Sequential)] struct INPUT { public uint type; public INPUTU u; }
    [DllImport("user32.dll")] static extern uint SendInput(uint n, INPUT[] inp, int size);
    [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] static extern bool PostMessage(IntPtr h, uint msg, IntPtr w, IntPtr l);

    public static IntPtr Win(string proc)
    {
        foreach (var p in Process.GetProcessesByName(proc)) if (p.MainWindowHandle != IntPtr.Zero) return p.MainWindowHandle;
        return IntPtr.Zero;
    }
    public static string Info(string proc)
    {
        IntPtr h = Win(proc); if (h == IntPtr.Zero) return "nessuna finestra";
        RECT r; GetWindowRect(h, out r);
        return string.Format("hwnd {0} rect {1},{2},{3},{4} fg {5}", h, r.L, r.T, r.R, r.B, GetForegroundWindow() == h);
    }
    public static bool Focus(string proc) { IntPtr h = Win(proc); return h != IntPtr.Zero && SetForegroundWindow(h); }
    public static string Shot(string proc, string path)
    {
        IntPtr h = Win(proc); RECT r;
        if (h == IntPtr.Zero || !GetWindowRect(h, out r)) { r.L = 0; r.T = 0; r.R = 1920; r.B = 1080; }
        int w = Math.Max(1, r.R - r.L), hh = Math.Max(1, r.B - r.T);
        using (var bmp = new Bitmap(w, hh))
        {
            using (var g = Graphics.FromImage(bmp)) g.CopyFromScreen(r.L, r.T, 0, 0, new Size(w, hh));
            bmp.Save(path, ImageFormat.Png);
        }
        return path;
    }
    static void Key(ushort scan, bool up, bool ext)
    {
        var i = new INPUT[1]; i[0].type = 1; i[0].u.ki.scan = scan;
        i[0].u.ki.flags = 0x0008u | (up ? 0x0002u : 0u) | (ext ? 0x0001u : 0u);
        SendInput(1, i, Marshal.SizeOf(typeof(INPUT)));
    }
    // tocco di un tasto per scancode (Enter 0x1C, Esc 0x01, W 0x11, S 0x1F, A 0x1E, D 0x20, frecce estese 0x48/0x50/0x4B/0x4D)
    public static void Tap(ushort scan, int holdMs, bool ext) { Key(scan, false, ext); Thread.Sleep(holdMs); Key(scan, true, ext); }
    public static void Mouse(int dx, int dy, int steps, int stepMs)
    {
        for (int k = 0; k < steps; k++)
        {
            var i = new INPUT[1]; i[0].type = 0; i[0].u.mi.dx = dx; i[0].u.mi.dy = dy; i[0].u.mi.flags = 0x0001;
            SendInput(1, i, Marshal.SizeOf(typeof(INPUT))); Thread.Sleep(stepMs);
        }
    }
    public static void Close(string proc) { IntPtr h = Win(proc); if (h != IntPtr.Zero) PostMessage(h, 0x0010, IntPtr.Zero, IntPtr.Zero); }
}
