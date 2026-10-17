# Valida bytecode di pixel shader con un device D3D9 reale: CreatePixelShader su ogni *.bin di una cartella.
#   -Dll  'system' = d3d9.dll di Windows (SysWOW64), oppure percorso completo di un d3d9.dll (es. quello dgVoodoo del gioco)
# Lanciare con la PowerShell a 32 bit (il d3d9 di dgVoodoo del gioco e' x86):
#   C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File Z:\tru-port\tools\vm_ps_validate.ps1 -Dir Z:\tru-port\work\ws\shader4\valid -Dll system
# Scrive <Dir>\validate_<etichetta>.txt (nome file, HRESULT esadecimale). Non tocca il gioco.
param([string]$Dir, [string]$Dll = 'system', [string]$Out = '')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
$src = @"
using System; using System.Runtime.InteropServices;
public static class PSV {
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr LoadLibrary(string p);
  [DllImport("kernel32.dll")] static extern IntPtr GetProcAddress(IntPtr h, string n);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr Create9(uint v);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateDev(IntPtr self, uint adapter, uint type, IntPtr hwnd, uint flags, IntPtr pp, out IntPtr dev);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreatePS(IntPtr self, byte[] code, out IntPtr ps);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate uint Release(IntPtr self);
  static IntPtr VT(IntPtr obj, int i) { IntPtr vt = Marshal.ReadIntPtr(obj); return Marshal.ReadIntPtr(vt, i * IntPtr.Size); }
  public static IntPtr Dev;
  public static string Init(string dll, IntPtr hwnd) {
    IntPtr h = LoadLibrary(dll); if (h == IntPtr.Zero) return "LoadLibrary fallita " + dll + " err " + Marshal.GetLastWin32Error();
    IntPtr f = GetProcAddress(h, "Direct3DCreate9"); if (f == IntPtr.Zero) return "Direct3DCreate9 assente";
    IntPtr d3d = ((Create9)Marshal.GetDelegateForFunctionPointer(f, typeof(Create9)))(32);
    if (d3d == IntPtr.Zero) return "Direct3DCreate9 ha dato NULL";
    // D3DPRESENT_PARAMETERS (x86: 14 campi da 4 byte = 56 byte)
    IntPtr pp = Marshal.AllocHGlobal(56); for (int i = 0; i < 56; i += 4) Marshal.WriteInt32(pp, i, 0);
    Marshal.WriteInt32(pp, 0, 64); Marshal.WriteInt32(pp, 4, 64); Marshal.WriteInt32(pp, 8, 21); Marshal.WriteInt32(pp, 12, 1);
    Marshal.WriteInt32(pp, 24, 1); Marshal.WriteInt32(pp, 28, hwnd.ToInt32()); Marshal.WriteInt32(pp, 32, 1);
    CreateDev cd = (CreateDev)Marshal.GetDelegateForFunctionPointer(VT(d3d, 16), typeof(CreateDev));
    int hr = cd(d3d, 0, 1, hwnd, 0x20, pp, out Dev);            // HAL, SOFTWARE_VERTEXPROCESSING
    if (hr < 0) { hr = cd(d3d, 0, 2, hwnd, 0x20, pp, out Dev); if (hr < 0) return string.Format("CreateDevice fallita 0x{0:X8}", hr); return "REF"; }
    return "HAL";
  }
  public static int Test(byte[] code) {
    CreatePS f = (CreatePS)Marshal.GetDelegateForFunctionPointer(VT(Dev, 106), typeof(CreatePS));
    IntPtr ps; int hr = f(Dev, code, out ps);
    if (hr >= 0 && ps != IntPtr.Zero) ((Release)Marshal.GetDelegateForFunctionPointer(VT(ps, 2), typeof(Release)))(ps);
    return hr;
  }
}
"@
Add-Type -TypeDefinition $src
$form = New-Object System.Windows.Forms.Form
$form.ShowInTaskbar = $false; $form.Opacity = 0; $form.Show()
$dllPath = if ($Dll -eq 'system') { "$env:windir\SysWOW64\d3d9.dll" } else { $Dll }
$label = if ($Dll -eq 'system') { 'system' } else { 'custom' }
if (-not $Out) { $Out = Join-Path $Dir "validate_$label.txt" }
$init = [PSV]::Init($dllPath, $form.Handle)
$lines = @("dll=$dllPath device=$init")
if ($init -eq 'HAL' -or $init -eq 'REF') {
  foreach ($f in Get-ChildItem $Dir -Filter *.bin | Sort-Object Name) {
    $hr = [PSV]::Test([IO.File]::ReadAllBytes($f.FullName))
    $lines += ('{0}`t0x{1:X8}' -f $f.Name, $hr)
  }
}
$form.Close()
$lines | Set-Content -Encoding ASCII $Out
$lines
