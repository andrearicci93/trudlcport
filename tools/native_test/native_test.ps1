# Test D3D9 nativo per il port DLC di Tomb Raider: Underworld. Non tocca il gioco, non scrive nel registro.
# Crea un device D3D9 col d3d9.dll di Windows e la GPU vera, poi prova a creare ogni risorsa che il port usa:
#   shaders\*.bin   -> CreatePixelShader / CreateVertexShader (estratti da mods\ con native_extract.py)
#   probes\*.bin    -> sonde sintetiche: lunghezza, caratteristiche, controlli negativi
#   decls.json      -> CreateVertexDeclaration
#   textures.json   -> CreateTexture / CreateCubeTexture / CreateVolumeTexture (D3DPOOL_MANAGED)
# Scrive native_report.txt nella cartella dello script (GPU, driver, caps e un HRESULT per ogni risorsa; FAIL = rifiutata).
# Va lanciato con la PowerShell a 32 bit (il gioco e' x86): usare RUN_TEST.bat.
param([string]$Dir = '', [string]$Dll = 'system')
$ErrorActionPreference = 'Stop'
if (-not $Dir) { $Dir = Split-Path -Parent $MyInvocation.MyCommand.Path }
if ([IntPtr]::Size -ne 4) { Write-Host 'ERRORE: serve la PowerShell a 32 bit (usare RUN_TEST.bat)'; exit 1 }
Add-Type -AssemblyName System.Windows.Forms
$src = @"
using System; using System.Runtime.InteropServices; using System.Text;
public static class NT {
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr LoadLibrary(string p);
  [DllImport("kernel32.dll")] static extern IntPtr GetProcAddress(IntPtr h, string n);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr Create9(uint v);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int GetIdent(IntPtr self, uint adapter, uint flags, IntPtr id);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateDev(IntPtr self, uint adapter, uint type, IntPtr hwnd, uint flags, IntPtr pp, out IntPtr dev);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int GetCaps(IntPtr self, IntPtr caps);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateSh(IntPtr self, byte[] code, out IntPtr sh);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateDecl(IntPtr self, byte[] elems, out IntPtr decl);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateTex(IntPtr self, uint w, uint h, uint levels, uint usage, uint fmt, uint pool, out IntPtr tex, IntPtr share);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateVol(IntPtr self, uint w, uint h, uint d, uint levels, uint usage, uint fmt, uint pool, out IntPtr tex, IntPtr share);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateCube(IntPtr self, uint edge, uint levels, uint usage, uint fmt, uint pool, out IntPtr tex, IntPtr share);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate uint Release(IntPtr self);
  static IntPtr VT(IntPtr obj, int i) { IntPtr vt = Marshal.ReadIntPtr(obj); return Marshal.ReadIntPtr(vt, i * IntPtr.Size); }
  static T F<T>(IntPtr obj, int i) where T : class { return Marshal.GetDelegateForFunctionPointer(VT(obj, i), typeof(T)) as T; }
  static void Rel(IntPtr p) { if (p != IntPtr.Zero) F<Release>(p, 2)(p); }
  public static IntPtr D3D, Dev; public static string Ident = "", Caps = "";
  public static string Init(string dll, IntPtr hwnd) {
    IntPtr h = LoadLibrary(dll); if (h == IntPtr.Zero) return "LoadLibrary fallita " + dll + " err " + Marshal.GetLastWin32Error();
    IntPtr f = GetProcAddress(h, "Direct3DCreate9"); if (f == IntPtr.Zero) return "Direct3DCreate9 assente";
    D3D = ((Create9)Marshal.GetDelegateForFunctionPointer(f, typeof(Create9)))(32);
    if (D3D == IntPtr.Zero) return "Direct3DCreate9 ha dato NULL";
    IntPtr id = Marshal.AllocHGlobal(1100);
    if (F<GetIdent>(D3D, 5)(D3D, 0, 0, id) >= 0) {
      long v = Marshal.ReadInt64(id, 1056);
      Ident = string.Format("gpu={0} | driver={1} {2}.{3}.{4}.{5} | vendor=0x{6:X4} device=0x{7:X4}",
        Marshal.PtrToStringAnsi(new IntPtr(id.ToInt32() + 512)), Marshal.PtrToStringAnsi(id),
        (v >> 48) & 0xffff, (v >> 32) & 0xffff, (v >> 16) & 0xffff, v & 0xffff, Marshal.ReadInt32(id, 1064), Marshal.ReadInt32(id, 1068));
    }
    IntPtr pp = Marshal.AllocHGlobal(56); for (int i = 0; i < 56; i += 4) Marshal.WriteInt32(pp, i, 0);
    Marshal.WriteInt32(pp, 0, 640); Marshal.WriteInt32(pp, 4, 480); Marshal.WriteInt32(pp, 8, 0); Marshal.WriteInt32(pp, 12, 1);
    Marshal.WriteInt32(pp, 24, 1); Marshal.WriteInt32(pp, 28, hwnd.ToInt32()); Marshal.WriteInt32(pp, 32, 1);
    Marshal.WriteInt32(pp, 36, 1); Marshal.WriteInt32(pp, 40, 75);   // depth D24S8 come il gioco
    uint[] flags = { 0x50, 0x40, 0x20 }; string[] names = { "HAL hardware VP + pure (come il gioco)", "HAL hardware VP", "HAL software VP" };
    for (int k = 0; k < flags.Length; k++) {
      int hr = F<CreateDev>(D3D, 16)(D3D, 0, 1, hwnd, flags[k], pp, out Dev);
      if (hr >= 0) { ReadCaps(); return names[k]; }
    }
    return "CreateDevice fallita su HAL";
  }
  static void ReadCaps() {
    IntPtr c = Marshal.AllocHGlobal(304); F<GetCaps>(Dev, 7)(Dev, c);
    Func<int, uint> U = o => (uint)Marshal.ReadInt32(c, o);
    Caps = string.Format("MaxTexture={0}x{1} MaxVolume={2} TextureCaps=0x{3:X8} MaxPrimitiveCount={4} MaxVertexIndex={5} MaxStreams={6} MaxStreamStride={7} " +
      "VS=0x{8:X8} VSConst={9} PS=0x{10:X8} DeclTypes=0x{11:X8} NumRTs={12} VS30Slots={13} PS30Slots={14} VSInstrExec={15} PSInstrExec={16} PS20Temps={17}",
      U(88), U(92), U(96), U(60), U(180), U(184), U(188), U(192), U(196), U(200), U(204), U(236), U(240), U(296), U(300), U(288), U(292), U(272));
    Marshal.FreeHGlobal(c);
  }
  public static int Shader(byte[] code) {
    bool vs = code.Length >= 4 && code[3] == 0xFF && code[2] == 0xFE;
    IntPtr sh; int hr = F<CreateSh>(Dev, vs ? 91 : 106)(Dev, code, out sh); if (hr >= 0) Rel(sh); return hr;
  }
  public static int Decl(byte[] elems) { IntPtr d; int hr = F<CreateDecl>(Dev, 86)(Dev, elems, out d); if (hr >= 0) Rel(d); return hr; }
  public static int Tex(string kind, uint w, uint h, uint dep, uint levels, uint fmt) {
    IntPtr t; int hr;
    if (kind == "cube") hr = F<CreateCube>(Dev, 25)(Dev, w, levels, 0, fmt, 1, out t, IntPtr.Zero);
    else if (kind == "volume") hr = F<CreateVol>(Dev, 24)(Dev, w, h, dep, levels, 0, fmt, 1, out t, IntPtr.Zero);
    else hr = F<CreateTex>(Dev, 23)(Dev, w, h, levels, 0, fmt, 1, out t, IntPtr.Zero);
    if (hr >= 0) Rel(t); return hr;
  }
}
"@
Add-Type -TypeDefinition $src
$form = New-Object System.Windows.Forms.Form
$form.ShowInTaskbar = $false; $form.Width = 640; $form.Height = 480; $form.Opacity = 0; $form.Show()
$dllPath = if ($Dll -eq 'system') { "$env:windir\SysWOW64\d3d9.dll" } else { $Dll }
$init = [NT]::Init($dllPath, $form.Handle)
$os = (Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue)
$L = New-Object System.Collections.Generic.List[string]
$L.Add("native_test v2 | $(Get-Date -Format s) | dll=$dllPath | device=$init")
$L.Add("os=$($os.Caption) $($os.Version)")
$L.Add([NT]::Ident); $L.Add([NT]::Caps)
$fail = 0; $tot = 0
function Row($kind, $name, $hr, $extra) {
  $script:tot++; $st = if ($hr -lt 0) { $script:fail++; 'FAIL' } else { 'ok' }
  $L.Add(("{0}`t{1}`t{2}`t0x{3:X8}`t{4}" -f $st, $kind, $name, $hr, $extra))
}
if ($init -like 'HAL*') {
  foreach ($sub in 'probes', 'shaders') {
    $sd = Join-Path $Dir $sub
    if (Test-Path $sd) { foreach ($f in Get-ChildItem $sd -Filter *.bin | Sort-Object Name) { Row 'shader' $f.Name ([NT]::Shader([IO.File]::ReadAllBytes($f.FullName))) '' } }
  }
  $dj = Join-Path $Dir 'decls.json'
  if (Test-Path $dj) {
    $k = 0
    foreach ($d in (Get-Content -Raw $dj | ConvertFrom-Json)) {
      $ms = New-Object IO.MemoryStream; $bw = New-Object IO.BinaryWriter($ms)
      foreach ($e in $d.elements) { $bw.Write([uint16]$e.Stream); $bw.Write([uint16]$e.Offset); $bw.Write([byte]$e.Type); $bw.Write([byte]$e.Method); $bw.Write([byte]$e.Usage); $bw.Write([byte]$e.UsageIndex) }
      $bw.Write([uint16]0xFF); $bw.Write([uint16]0); $bw.Write([byte]17); $bw.Write([byte]0); $bw.Write([byte]0); $bw.Write([byte]0)
      $types = ($d.elements | ForEach-Object { $_.Type }) -join ','
      $dn = if ($d.name) { $d.name } else { "decl_{0:D3}" -f $k }
      Row 'decl' $dn ([NT]::Decl($ms.ToArray())) ("in_pc=$($d.in_pc) types=$types ex=$($d.example)"); $k++
    }
  }
  $tj = Join-Path $Dir 'textures.json'
  if (Test-Path $tj) {
    foreach ($t in (Get-Content -Raw $tj | ConvertFrom-Json)) {
      $dep = if ($t.depth) { [uint32]$t.depth } else { [uint32]1 }
      $nm = '{0} fmt={1} {2}x{3}x{4} lv={5}' -f $t.kind, $t.format, $t.width, $t.height, $dep, $t.levels
      Row 'texture' $nm ([NT]::Tex([string]$t.kind, [uint32]$t.width, [uint32]$t.height, $dep, [uint32]$t.levels, [uint32]$t.format)) ("in_pc=$($t.in_pc) ex=$($t.example)")
    }
  }
}
$form.Close()
$top = New-Object System.Collections.Generic.List[string]
$top.Add("RISULTATO: $fail rifiutate su $tot")
# banco valido: questi shader sono illegali e DEVONO essere rifiutati, altrimenti il test non dimostra nulla
$neg = @($L | Where-Object { $_ -match "`tshader`t(neg_B75_|neg_ps_sampler_s16)" })
$negok = ($neg.Count -gt 0) -and -not ($neg | Where-Object { $_ -like 'ok*' })
$top.Add("BANCO VALIDO: $negok (controlli negativi rifiutati: $(@($neg | Where-Object { $_ -like 'FAIL*' }).Count)/$($neg.Count))")
$top.Add('LIMITE ISTRUZIONI: ' + ((([NT]::Caps -split ' ') | Where-Object { $_ -like 'PS30Slots=*' -or $_ -like 'VS30Slots=*' }) -join ' '))
$L | Where-Object { $_ -match "`tshader`tprobe_" } | ForEach-Object { $top.Add('  ' + $_) }
$top.Add("SHADER DEL PORT RIFIUTATI: nuovi $(@($L | Where-Object { $_ -match "^FAIL`tshader`tnew_" }).Count), copiati dal PC $(@($L | Where-Object { $_ -match "^FAIL`tshader`tpc_" }).Count)")
$top.Add('')
$L.InsertRange(1, $top)
$out = Join-Path $Dir 'native_report.txt'
$L | Set-Content -Encoding ASCII $out
$top | ForEach-Object { Write-Host $_ }
Write-Host "Report completo: $out"
$L | Where-Object { $_ -like 'FAIL*' } | Select-Object -First 30 | ForEach-Object { Write-Host $_ }
