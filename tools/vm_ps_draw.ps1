# Come vm_ps_validate.ps1 ma DISEGNA: per ogni *.bin crea il PS, lo abbina a un VS (vs_test.vsbin nella stessa cartella),
# imposta texture 2D/cube 4x4 su s0-s15 (tipo secondo i dcl del PS), costanti/bool, disegna un triangolo, Present.
# Registra HRESULT di CreatePixelShader, DrawPrimitiveUP, EndScene, Present e TestCooperativeLevel (perdita del device).
#   C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File Z:\tru-port\tools\vm_ps_draw.ps1 -Dir <cartella> -Dll <d3d9.dll>
param([string]$Dir, [string]$Dll, [string]$Out = '', [string]$Filter = '*.bin')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
$src = @"
using System; using System.Runtime.InteropServices;
public static class PSD {
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr LoadLibrary(string p);
  [DllImport("kernel32.dll")] static extern IntPtr GetProcAddress(IntPtr h, string n);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr Create9(uint v);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateDev(IntPtr self, uint adapter, uint type, IntPtr hwnd, uint flags, IntPtr pp, out IntPtr dev);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateSh(IntPtr self, byte[] code, out IntPtr sh);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int SetPtr(IntPtr self, IntPtr p);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int Void0(IntPtr self);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate uint Release(IntPtr self);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int SetU(IntPtr self, uint v);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int Present(IntPtr self, IntPtr a, IntPtr b, IntPtr c, IntPtr d);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int DrawUP(IntPtr self, uint type, uint count, float[] data, uint stride);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int Clear(IntPtr self, uint n, IntPtr rects, uint flags, uint color, float z, uint stencil);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateTex(IntPtr self, uint w, uint h, uint levels, uint usage, uint fmt, uint pool, out IntPtr tex, IntPtr share);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateCube(IntPtr self, uint edge, uint levels, uint usage, uint fmt, uint pool, out IntPtr tex, IntPtr share);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int SetTex(IntPtr self, uint stage, IntPtr tex);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int SetConstF(IntPtr self, uint start, float[] data, uint count);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int SetConstB(IntPtr self, uint start, int[] data, uint count);
  static IntPtr VT(IntPtr obj, int i) { IntPtr vt = Marshal.ReadIntPtr(obj); return Marshal.ReadIntPtr(vt, i * IntPtr.Size); }
  static T F<T>(IntPtr obj, int i) { return (T)(object)Marshal.GetDelegateForFunctionPointer(VT(obj, i), typeof(T)); }
  public static IntPtr Dev, VS, Tex2D, TexCube;
  public static string Init(string dll, IntPtr hwnd, byte[] vs) {
    IntPtr h = LoadLibrary(dll); if (h == IntPtr.Zero) return "LoadLibrary fallita";
    IntPtr d3d = ((Create9)Marshal.GetDelegateForFunctionPointer(GetProcAddress(h, "Direct3DCreate9"), typeof(Create9)))(32);
    IntPtr pp = Marshal.AllocHGlobal(56); for (int i = 0; i < 56; i += 4) Marshal.WriteInt32(pp, i, 0);
    Marshal.WriteInt32(pp, 0, 64); Marshal.WriteInt32(pp, 4, 64); Marshal.WriteInt32(pp, 8, 21); Marshal.WriteInt32(pp, 12, 1);
    Marshal.WriteInt32(pp, 24, 1); Marshal.WriteInt32(pp, 28, hwnd.ToInt32()); Marshal.WriteInt32(pp, 32, 1);
    int hr = F<CreateDev>(d3d, 16)(d3d, 0, 1, hwnd, 0x20, pp, out Dev);
    if (hr < 0) return string.Format("CreateDevice 0x{0:X8}", hr);
    hr = F<CreateSh>(Dev, 91)(Dev, vs, out VS); if (hr < 0) return string.Format("CreateVertexShader 0x{0:X8}", hr);
    hr = F<CreateTex>(Dev, 23)(Dev, 4, 4, 1, 0, 21, 1, out Tex2D, IntPtr.Zero); if (hr < 0) return string.Format("CreateTexture 0x{0:X8}", hr);
    hr = F<CreateCube>(Dev, 25)(Dev, 4, 1, 0, 21, 1, out TexCube, IntPtr.Zero); if (hr < 0) return string.Format("CreateCubeTexture 0x{0:X8}", hr);
    return "ok";
  }
  public static string Test(byte[] ps, int[] cubeMask) {
    IntPtr p; int hrc = F<CreateSh>(Dev, 106)(Dev, ps, out p);
    if (hrc < 0) return string.Format("create=0x{0:X8}", hrc);
    F<SetU>(Dev, 89)(Dev, 0x002);                                  // FVF XYZ
    F<SetPtr>(Dev, 92)(Dev, VS); F<SetPtr>(Dev, 107)(Dev, p);
    for (uint s = 0; s < 16; s++) F<SetTex>(Dev, 65)(Dev, s, cubeMask[s] != 0 ? TexCube : Tex2D);
    float[] c = new float[224 * 4]; for (int i = 0; i < c.Length; i++) c[i] = 0.5f;
    F<SetConstF>(Dev, 109)(Dev, 0, c, 224);
    int[] b = new int[16]; for (int i = 0; i < 16; i++) b[i] = 1; F<SetConstB>(Dev, 113)(Dev, 0, b, 16);
    float[] tri = { -1f, -1f, 0.5f,  3f, -1f, 0.5f,  -1f, 3f, 0.5f };
    F<Clear>(Dev, 43)(Dev, 0, IntPtr.Zero, 1, 0, 1f, 0);
    int hb = F<Void0>(Dev, 41)(Dev);
    int hd = F<DrawUP>(Dev, 83)(Dev, 4, 1, tri, 12);
    int he = F<Void0>(Dev, 42)(Dev);
    int hp = F<Present>(Dev, 17)(Dev, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero);
    int ht = F<Void0>(Dev, 3)(Dev);
    F<SetPtr>(Dev, 107)(Dev, IntPtr.Zero);
    ((Release)Marshal.GetDelegateForFunctionPointer(VT(p, 2), typeof(Release)))(p);
    return string.Format("create=0x{0:X8} begin=0x{1:X8} draw=0x{2:X8} end=0x{3:X8} present=0x{4:X8} coop=0x{5:X8}", hrc, hb, hd, he, hp, ht);
  }
}
"@
Add-Type -TypeDefinition $src
$form = New-Object System.Windows.Forms.Form
$form.ShowInTaskbar = $false; $form.Opacity = 0; $form.Show()
if (-not $Out) { $Out = Join-Path $Dir 'draw_result.txt' }
$init = [PSD]::Init($Dll, $form.Handle, [IO.File]::ReadAllBytes((Join-Path $Dir 'vs_test.vsbin')))
$lines = @("dll=$Dll init=$init")
if ($init -eq 'ok') {
  foreach ($f in Get-ChildItem $Dir -Filter $Filter | Sort-Object Name) {
    $bytes = [IO.File]::ReadAllBytes($f.FullName)
    # tipi dei sampler dai token dcl: 0x0200001F, poi token usage (bit 27-30 tipo: 2=2D 3=cube), poi registro (tipo 10 = sampler)
    $mask = New-Object int[] 16
    for ($i = 4; $i -le $bytes.Length - 12; $i += 4) {
      if ([BitConverter]::ToUInt32($bytes, $i) -eq 0x0200001F) {
        $u = [BitConverter]::ToUInt32($bytes, $i + 4); $r = [BitConverter]::ToUInt32($bytes, $i + 8)
        $rt = (($r -shr 28) -band 7) -bor ((($r -shr 11) -band 3) -shl 3)
        if ($rt -eq 10 -and ((($u -shr 27) -band 15) -eq 3)) { $mask[$r -band 0x7FF] = 1 }
      }
    }
    $lines += ('{0}`t{1}' -f $f.Name, [PSD]::Test($bytes, $mask))
  }
}
$form.Close()
$lines | Set-Content -Encoding ASCII $Out
$lines
