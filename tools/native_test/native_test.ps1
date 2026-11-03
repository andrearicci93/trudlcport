# native_test v3 (B269) - step 2 of the native Direct3D 9 test of the TRU DLC port. Changes nothing in the game folder or the registry.
# Creates a Direct3D 9 device with Windows' own d3d9.dll on the real GPU (same flags as the game) and tries to create every resource:
#   probes\*.bin, shaders\*.bin   CreatePixelShader / CreateVertexShader (shaders\ comes from native_extract.py; probes are synthetic)
#   decls.json                    CreateVertexDeclaration
#   textures.json + textures_installed.json   CreateTexture / CreateCubeTexture / CreateVolumeTexture (MANAGED)
#   render targets / depth        CreateTexture(RENDERTARGET) / CreateDepthStencilSurface + CheckDeviceFormat for the formats the engine uses
#   state blocks                  CreateStateBlock(ALL / PIXEL / VERTEX)
#   -Draw (optional)              draws one triangle with every pixel shader (a TDR here = the shader that breaks the driver at draw time)
# Output: native_report.txt (everything), SUMMARY.txt (short, to paste), native_progress.txt (last step reached, survives a driver crash),
#         trudlcport_native_result.zip (the three files + shaders_index.tsv + extract_summary.txt + the rejected blobs).
# Must run in the 32-bit PowerShell (the game is x86): use RUN_TEST.bat.
param([string]$Dir = '', [string]$Dll = 'system', [string]$Game = '', [switch]$Draw)
$ErrorActionPreference = 'Stop'
if (-not $Dir) { $Dir = Split-Path -Parent $MyInvocation.MyCommand.Path }
if ([IntPtr]::Size -ne 4) { Write-Host 'ERROR: needs the 32-bit PowerShell (use RUN_TEST.bat)'; exit 1 }
Add-Type -AssemblyName System.Windows.Forms
$src = @"
using System; using System.Runtime.InteropServices; using System.Text;
public static class NT {
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr LoadLibrary(string p);
  [DllImport("kernel32.dll")] static extern IntPtr GetProcAddress(IntPtr h, string n);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate IntPtr Create9(uint v);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int GetIdent(IntPtr self, uint adapter, uint flags, IntPtr id);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CheckFmt(IntPtr self, uint adapter, uint type, uint afmt, uint usage, uint rtype, uint fmt);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int GetMode(IntPtr self, uint adapter, IntPtr mode);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateDev(IntPtr self, uint adapter, uint type, IntPtr hwnd, uint flags, IntPtr pp, out IntPtr dev);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int GetCaps(IntPtr self, IntPtr caps);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateSh(IntPtr self, byte[] code, out IntPtr sh);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateDecl(IntPtr self, byte[] elems, out IntPtr decl);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateTex(IntPtr self, uint w, uint h, uint levels, uint usage, uint fmt, uint pool, out IntPtr tex, IntPtr share);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateVol(IntPtr self, uint w, uint h, uint d, uint levels, uint usage, uint fmt, uint pool, out IntPtr tex, IntPtr share);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateCube(IntPtr self, uint edge, uint levels, uint usage, uint fmt, uint pool, out IntPtr tex, IntPtr share);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateDS(IntPtr self, uint w, uint h, uint fmt, uint ms, uint q, int discard, out IntPtr surf, IntPtr share);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateSB(IntPtr self, uint type, out IntPtr sb);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int NoArg(IntPtr self);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int SetPtr(IntPtr self, IntPtr p);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int SetU(IntPtr self, uint v);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int DrawUP(IntPtr self, uint ptype, uint count, float[] data, uint stride);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int ValidateDev(IntPtr self, out uint passes);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int PresentF(IntPtr self, IntPtr a, IntPtr b, IntPtr c, IntPtr d);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int CreateQ(IntPtr self, uint type, out IntPtr q);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int QIssue(IntPtr self, uint flags);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int QGetData(IntPtr self, IntPtr data, uint size, uint flags);
  [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate uint Release(IntPtr self);
  static IntPtr VT(IntPtr obj, int i) { IntPtr vt = Marshal.ReadIntPtr(obj); return Marshal.ReadIntPtr(vt, i * IntPtr.Size); }
  static T F<T>(IntPtr obj, int i) where T : class { return Marshal.GetDelegateForFunctionPointer(VT(obj, i), typeof(T)) as T; }
  static void Rel(IntPtr p) { if (p != IntPtr.Zero) F<Release>(p, 2)(p); }
  public static IntPtr D3D, Dev, VS = IntPtr.Zero; public static string Ident = "", Caps = "", Mode = "";
  public static string Init(string dll, IntPtr hwnd) {
    IntPtr h = LoadLibrary(dll); if (h == IntPtr.Zero) return "LoadLibrary failed " + dll + " err " + Marshal.GetLastWin32Error();
    IntPtr f = GetProcAddress(h, "Direct3DCreate9"); if (f == IntPtr.Zero) return "Direct3DCreate9 missing";
    D3D = ((Create9)Marshal.GetDelegateForFunctionPointer(f, typeof(Create9)))(32);
    if (D3D == IntPtr.Zero) return "Direct3DCreate9 returned NULL";
    IntPtr id = Marshal.AllocHGlobal(1100);
    if (F<GetIdent>(D3D, 5)(D3D, 0, 0, id) >= 0) {
      long v = Marshal.ReadInt64(id, 1056);
      Ident = string.Format("gpu={0} | driver={1} {2}.{3}.{4}.{5} | vendor=0x{6:X4} device=0x{7:X4} subsys=0x{8:X8} rev={9}",
        Marshal.PtrToStringAnsi(new IntPtr(id.ToInt32() + 512)), Marshal.PtrToStringAnsi(id),
        (v >> 48) & 0xffff, (v >> 32) & 0xffff, (v >> 16) & 0xffff, v & 0xffff, Marshal.ReadInt32(id, 1064), Marshal.ReadInt32(id, 1068),
        Marshal.ReadInt32(id, 1072), Marshal.ReadInt32(id, 1076));
    }
    IntPtr m = Marshal.AllocHGlobal(16);
    if (F<GetMode>(D3D, 8)(D3D, 0, m) >= 0) Mode = string.Format("{0}x{1} {2} Hz fmt={3}", Marshal.ReadInt32(m, 0), Marshal.ReadInt32(m, 4), Marshal.ReadInt32(m, 8), Marshal.ReadInt32(m, 12));
    IntPtr pp = Marshal.AllocHGlobal(56); for (int i = 0; i < 56; i += 4) Marshal.WriteInt32(pp, i, 0);
    Marshal.WriteInt32(pp, 0, 640); Marshal.WriteInt32(pp, 4, 480); Marshal.WriteInt32(pp, 8, 0); Marshal.WriteInt32(pp, 12, 1);
    Marshal.WriteInt32(pp, 24, 1); Marshal.WriteInt32(pp, 28, hwnd.ToInt32()); Marshal.WriteInt32(pp, 32, 1);
    Marshal.WriteInt32(pp, 36, 1); Marshal.WriteInt32(pp, 40, 75);   // depth D24S8 like the game
    uint[] flags = { 0x50, 0x40, 0x20 }; string[] names = { "HAL hardware VP + pure (like the game)", "HAL hardware VP", "HAL software VP" };
    for (int k = 0; k < flags.Length; k++) {
      int hr = F<CreateDev>(D3D, 16)(D3D, 0, 1, hwnd, flags[k], pp, out Dev);
      if (hr >= 0) { ReadCaps(); return names[k]; }
    }
    return "CreateDevice failed on HAL";
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
  public static int Tex(string kind, uint w, uint h, uint dep, uint levels, uint fmt, uint usage, uint pool) {
    IntPtr t; int hr;
    if (kind == "cube") hr = F<CreateCube>(Dev, 25)(Dev, w, levels, usage, fmt, pool, out t, IntPtr.Zero);
    else if (kind == "volume") hr = F<CreateVol>(Dev, 24)(Dev, w, h, dep, levels, usage, fmt, pool, out t, IntPtr.Zero);
    else hr = F<CreateTex>(Dev, 23)(Dev, w, h, levels, usage, fmt, pool, out t, IntPtr.Zero);
    if (hr >= 0) Rel(t); return hr;
  }
  public static int Depth(uint w, uint h, uint fmt) { IntPtr s; int hr = F<CreateDS>(Dev, 29)(Dev, w, h, fmt, 0, 0, 0, out s, IntPtr.Zero); if (hr >= 0) Rel(s); return hr; }
  public static int Check(uint usage, uint rtype, uint fmt) { return F<CheckFmt>(D3D, 10)(D3D, 0, 1, 22, usage, rtype, fmt); }   // adapter fmt X8R8G8B8
  public static int StateBlock(uint type) { IntPtr sb; int hr = F<CreateSB>(Dev, 59)(Dev, type, out sb); if (hr >= 0) Rel(sb); return hr; }
  // ---- optional draw test: a vs_3_0 that writes position, texcoord0-7 and color0-1 from the vertex position
  static byte[] MakeVS() {
    var t = new System.Collections.Generic.List<uint>();
    t.Add(0xFFFE0300);
    t.Add(0x0200001F); t.Add(0x80000000); t.Add(0x900F0000);                 // dcl_position v0
    t.Add(0x0200001F); t.Add(0x80000000); t.Add(0xE00F0000);                 // dcl_position o0
    for (uint i = 0; i < 8; i++) { t.Add(0x0200001F); t.Add(0x80000005 | (i << 16)); t.Add(0xE00F0001 + i); }   // dcl_texcoordN o(1+N)
    for (uint i = 0; i < 2; i++) { t.Add(0x0200001F); t.Add(0x8000000A | (i << 16)); t.Add(0xE00F0009 + i); }   // dcl_colorN o(9+N)
    for (uint i = 0; i < 11; i++) { t.Add(0x02000001); t.Add(0xE00F0000 + i); t.Add(0x90E40000); }               // mov oN, v0
    t.Add(0x0000FFFF);
    var b = new byte[t.Count * 4]; for (int i = 0; i < t.Count; i++) BitConverter.GetBytes(t[i]).CopyTo(b, i * 4); return b;
  }
  public static int DrawInit() {
    IntPtr vs; int hr = F<CreateSh>(Dev, 91)(Dev, MakeVS(), out vs); if (hr < 0) return hr; VS = vs;
    hr = F<SetPtr>(Dev, 92)(Dev, VS); if (hr < 0) return hr;
    return F<SetU>(Dev, 89)(Dev, 0x002);   // FVF XYZ
  }
  public static string Draw(byte[] code) {   // returns "create;validate;draw;flush" HRESULTs
    IntPtr ps; int hc = F<CreateSh>(Dev, 106)(Dev, code, out ps); if (hc < 0) return string.Format("0x{0:X8};-;-;-", hc);
    F<SetPtr>(Dev, 107)(Dev, ps);
    uint passes; int hv = F<ValidateDev>(Dev, 70)(Dev, out passes);
    F<NoArg>(Dev, 41)(Dev);
    float[] tri = { -1f, -1f, 0.5f, 3f, -1f, 0.5f, -1f, 3f, 0.5f };
    int hd = F<DrawUP>(Dev, 83)(Dev, 4, 1, tri, 12);
    F<NoArg>(Dev, 42)(Dev);
    IntPtr q; int hf = F<CreateQ>(Dev, 118)(Dev, 8, out q);   // EVENT query: wait until the GPU has really run the draw
    if (hf >= 0) {
      F<QIssue>(q, 6)(q, 1);
      for (int i = 0; i < 2000; i++) { hf = F<QGetData>(q, 7)(q, IntPtr.Zero, 0, 1); if (hf != 1) break; System.Threading.Thread.Sleep(1); }
      Rel(q);
    }
    int hp = F<PresentF>(Dev, 17)(Dev, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero);
    F<SetPtr>(Dev, 107)(Dev, IntPtr.Zero); Rel(ps);
    return string.Format("0x{0:X8};0x{1:X8};0x{2:X8};0x{3:X8}", hc, hv, hd, hp < 0 ? hp : hf);
  }
}
"@
Add-Type -TypeDefinition $src
$HRNAMES = @{ 0 = 'S_OK'; 1 = 'S_FALSE'; -2005530516 = 'D3DERR_INVALIDCALL'; -2005530585 = 'D3DERR_DRIVERINTERNALERROR'; -2005530520 = 'D3DERR_DEVICELOST';
         -2005530519 = 'D3DERR_DEVICENOTRESET'; -2005530518 = 'D3DERR_NOTAVAILABLE'; -2005532292 = 'D3DERR_OUTOFVIDEOMEMORY'; -2005530522 = 'D3DERR_NOTFOUND';
         -2005530521 = 'D3DERR_MOREDATA'; -2005530512 = 'D3DERR_DEVICEREMOVED'; -2005530591 = 'D3DERR_CONFLICTINGRENDERSTATE';
         -2005530590 = 'D3DERR_UNSUPPORTEDTEXTUREFILTER'; -2005530600 = 'D3DERR_WRONGTEXTUREFORMAT'; -2005530515 = 'D3DERR_DRIVERINVALIDCALL';
         -2005532132 = 'D3DERR_WASSTILLDRAWING'; -2005530517 = 'D3DERR_INVALIDDEVICE'; -2147024882 = 'E_OUTOFMEMORY'; -2147467259 = 'E_FAIL' }
function HrName([int]$h) { if ($HRNAMES.ContainsKey($h)) { $HRNAMES[$h] } elseif ($h -ge 0) { 'success' } else { 'unknown' } }
$prog = Join-Path $Dir 'native_progress.txt'
function Progress($s) { [IO.File]::AppendAllText($prog, ("{0:HH:mm:ss.fff} {1}`r`n" -f (Get-Date), $s)) }
Set-Content -Encoding ASCII $prog "native_test v3 progress (if the PC/driver crashed, the last line is the step that was running)"

# ---- system information (works even when the device cannot be created)
function Wmi($c) { try { Get-CimInstance $c -ErrorAction Stop } catch { try { Get-WmiObject $c -ErrorAction Stop } catch { $null } } }
$os = Wmi 'Win32_OperatingSystem'
$vc = @(Wmi 'Win32_VideoController' | Where-Object { $_ })
$dllPath = if ($Dll -eq 'system') { "$env:windir\SysWOW64\d3d9.dll" } else { $Dll }
$dllVer = try { (Get-Item $dllPath).VersionInfo.FileVersion } catch { 'n/a' }
$form = New-Object System.Windows.Forms.Form
$form.ShowInTaskbar = $false; $form.Width = 640; $form.Height = 480; $form.Opacity = 0; $form.Show()
Progress "CreateDevice $dllPath"
$init = try { [NT]::Init($dllPath, $form.Handle) } catch { 'Init exception: ' + $_.Exception.Message }
$L = New-Object System.Collections.Generic.List[string]
$L.Add("native_test v3 | $(Get-Date -Format s) | dll=$dllPath ($dllVer) | device=$init | draw=$($Draw.IsPresent)")
$L.Add("os=$($os.Caption) $($os.Version) build=$($os.BuildNumber) $($os.OSArchitecture)")
foreach ($v in $vc) { $L.Add("adapter=$($v.Name) | driver=$($v.DriverVersion) date=$($v.DriverDate) | vram=$([math]::Round($v.AdapterRAM / 1MB)) MB | mode=$($v.CurrentHorizontalResolution)x$($v.CurrentVerticalResolution)@$($v.CurrentRefreshRate)Hz") }
$L.Add([NT]::Ident); $L.Add("display=" + [NT]::Mode); $L.Add([NT]::Caps)
if ($Game) {
  $wr = @('d3d9.dll', 'dxgi.dll', 'dgVoodoo.conf', 'dxvk.conf', 'ModLoader.asi', 'binkw32.dll', 'TR8-Menu-Hook.asi', 'dxwrapper.dll', 'dxwrapper.ini') | Where-Object { Test-Path (Join-Path $Game $_) }
  $L.Add("game folder: $Game | wrappers/hooks present: " + ($wr -join ', '))
}
# shaders_index.tsv (native_extract.py): lib, DRM files, static findings, suspicious instruction
$IDX = @{}
$ix = Join-Path $Dir 'shaders_index.tsv'
if (Test-Path $ix) { Import-Csv -Delimiter "`t" $ix | ForEach-Object { $IDX[$_.file] = $_ } }
$fail = 0; $tot = 0; $failRows = New-Object System.Collections.Generic.List[string]; $cat = @{}
function Row($kind, $name, $code, $extra) {
  $script:tot++; $c = $script:cat[$kind]; if (-not $c) { $c = @(0, 0); $script:cat[$kind] = $c }
  $c[0]++
  $st = if ($code -lt 0) { $script:fail++; $c[1]++; 'FAIL' } else { 'ok' }
  $line = "{0}`t{1}`t{2}`t0x{3:X8} {4}`t{5}" -f $st, $kind, $name, $code, (HrName $code), $extra
  $L.Add($line); if ($st -eq 'FAIL') { $script:failRows.Add($line) }
}
function ShaderInfo($n) {
  $i = $IDX[$n]; if (-not $i) { return '' }
  "lib=$($i.lib) slot=$($i.slot) size=$($i.size) md5=$($i.md5) ninstr=$($i.ninstr) static=$($i.findings) | $($i.first_suspicious_instruction) | drms=$($i.drms)"
}
if ($init -like 'HAL*') {
  foreach ($sub in 'probes', 'shaders') {
    $sd = Join-Path $Dir $sub
    if (Test-Path $sd) {
      foreach ($f in Get-ChildItem $sd -Filter *.bin | Sort-Object Name) {
        Progress "shader $($f.Name)"
        Row 'shader' $f.Name ([NT]::Shader([IO.File]::ReadAllBytes($f.FullName))) (ShaderInfo $f.Name)
      }
    }
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
      Progress "decl $dn"
      Row 'decl' $dn ([NT]::Decl($ms.ToArray())) ("in_pc=$($d.in_pc) types=$types ex=$($d.example)"); $k++
    }
  }
  $seen = @{}
  foreach ($tn in 'textures.json', 'textures_installed.json') {
    $tj = Join-Path $Dir $tn
    if (-not (Test-Path $tj)) { continue }
    foreach ($t in (Get-Content -Raw $tj | ConvertFrom-Json)) {
      $dep = if ($t.depth) { [uint32]$t.depth } else { [uint32]1 }
      $nm = '{0} fmt=0x{1:X} {2}x{3}x{4} lv={5}' -f $t.kind, [uint32]$t.format, $t.width, $t.height, $dep, $t.levels
      if ($seen[$nm]) { continue }; $seen[$nm] = 1
      Progress "texture $nm"
      Row 'texture' $nm ([NT]::Tex([string]$t.kind, [uint32]$t.width, [uint32]$t.height, $dep, [uint32]$t.levels, [uint32]$t.format, 0, 1)) ("$tn ex=$($t.example)")
    }
  }
  # render targets / depth buffers / format support (formats of the engine's post-processing and shadows)
  $rt = @{ 'A8R8G8B8' = 21; 'X8R8G8B8' = 22; 'R5G6B5' = 23; 'A16B16G16R16F' = 113; 'G16R16F' = 112; 'R16F' = 111; 'R32F' = 114; 'G16R16' = 34; 'A2R10G10B10' = 35 }
  foreach ($k in $rt.Keys | Sort-Object) {
    Progress "rendertarget $k"
    Row 'rendertarget' "$k 1024x1024" ([NT]::Tex('2d', 1024, 1024, 1, 1, [uint32]$rt[$k], 1, 0)) ("CheckDeviceFormat=0x{0:X8}" -f [NT]::Check(1, 3, [uint32]$rt[$k]))
  }
  $ds = @{ 'D24S8' = 75; 'D24X8' = 77; 'D16' = 80; 'INTZ' = 0x5A544E49; 'DF24' = 0x34324644 }
  foreach ($k in $ds.Keys | Sort-Object) {
    Progress "depth $k"
    Row 'depth' "$k 1024x1024" ([NT]::Depth(1024, 1024, [uint32]$ds[$k])) ("CheckDeviceFormat(DEPTHSTENCIL,SURFACE)=0x{0:X8} as texture=0x{1:X8}" -f [NT]::Check(2, 1, [uint32]$ds[$k]), [NT]::Check(2, 3, [uint32]$ds[$k]))
  }
  foreach ($sb in @(@(1, 'ALL'), @(2, 'PIXELSTATE'), @(3, 'VERTEXSTATE'))) { Progress "stateblock $($sb[1])"; Row 'stateblock' $sb[1] ([NT]::StateBlock([uint32]$sb[0])) '' }
  if ($Draw) {
    $hrInit = [NT]::DrawInit(); Row 'draw' 'init (vs_3_0 + FVF)' $hrInit ''
    if ($hrInit -ge 0) {
      foreach ($f in Get-ChildItem (Join-Path $Dir 'shaders') -Filter '*_ps_*.bin' -ErrorAction SilentlyContinue | Sort-Object Name) {
        Progress "draw $($f.Name)"
        $r = [NT]::Draw([IO.File]::ReadAllBytes($f.FullName)) -split ';'
        $worst = 0; foreach ($x in $r) { if ($x -ne '-') { $v = [Convert]::ToInt32($x, 16); if ($v -lt $worst) { $worst = $v } } }
        Row 'draw' $f.Name $worst ("create;validate;draw;flush=$($r -join ';') | " + (ShaderInfo $f.Name))
      }
    }
  }
}
$form.Close()
Progress 'end'
# ---- verdict lines
$top = New-Object System.Collections.Generic.List[string]
$top.Add("RESULT: $fail rejected out of $tot")
$neg = @($L | Where-Object { $_ -match "`tshader`t(neg_B75_|neg_ps_sampler_s16)" })
$negok = ($neg.Count -gt 0) -and -not ($neg | Where-Object { $_ -like 'ok*' })
$top.Add("TEST VALID: $negok (negative controls rejected: $(@($neg | Where-Object { $_ -like 'FAIL*' }).Count)/$($neg.Count))")
$top.Add('INSTRUCTION LIMIT: ' + ((([NT]::Caps -split ' ') | Where-Object { $_ -like 'PS30Slots=*' -or $_ -like 'VS30Slots=*' }) -join ' '))
$L | Where-Object { $_ -match "`tshader`tprobe_" } | ForEach-Object { $top.Add('  ' + $_) }
$newF = @($failRows | Where-Object { $_ -match "^FAIL`tshader`tnew_" }); $pcF = @($failRows | Where-Object { $_ -match "^FAIL`tshader`tpc_" })
$top.Add("PORT SHADERS REJECTED: new $($newF.Count), copied from the PC game $($pcF.Count)")
foreach ($k in $cat.Keys | Sort-Object) { $top.Add(("  {0,-12} {1,5} tested {2,4} rejected" -f $k, $cat[$k][0], $cat[$k][1])) }
$top.Add('')
$L.InsertRange(1, $top)
$out = Join-Path $Dir 'native_report.txt'
$L | Set-Content -Encoding UTF8 $out
# ---- short summary to paste
$S = New-Object System.Collections.Generic.List[string]
$S.Add('TRU DLC port - native D3D9 test v3 - ' + (Get-Date -Format 'yyyy-MM-dd HH:mm'))
$S.Add("OS: $($os.Caption) $($os.Version) (build $($os.BuildNumber))")
foreach ($v in $vc) { $S.Add("GPU: $($v.Name) | driver $($v.DriverVersion) ($($v.DriverDate)) | $($v.CurrentHorizontalResolution)x$($v.CurrentVerticalResolution) @ $($v.CurrentRefreshRate) Hz") }
$S.Add("d3d9.dll: $dllPath $dllVer | device: $init")
$es = Join-Path $Dir 'extract_summary.txt'
if (Test-Path $es) { $S.Add('Shaders: ' + ((Get-Content $es | Select-Object -Index 1))) } else { $S.Add('Shaders: native_extract.py not run (probes only)') }
$top | Where-Object { $_ -notmatch "^  (ok|FAIL)`tshader`tprobe_" -and $_ } | ForEach-Object { $S.Add($_) }
$S.Add("Rejected port shaders (first 25 of $($newF.Count + $pcF.Count)): file | HRESULT | lib/slot/md5 | static finding | instruction | DRM")
foreach ($r in ($newF + $pcF) | Select-Object -First 25) { $c = $r -split "`t"; $S.Add('  ' + $c[2] + ' | ' + $c[3] + ' | ' + $c[4]) }
$other = @($failRows | Where-Object { $_ -notmatch "`tshader`t(new_|pc_|neg_|probe_)" })
if ($other.Count) { $S.Add("Other rejections ($($other.Count)):"); $other | Select-Object -First 15 | ForEach-Object { $S.Add('  ' + $_) } }
if (Test-Path $es) { $S.Add(''); Get-Content $es | Select-Object -Skip 2 -First 20 | ForEach-Object { $S.Add($_) } }
$sum = Join-Path $Dir 'SUMMARY.txt'
$S | Set-Content -Encoding UTF8 $sum
# ---- zip with everything needed to diagnose (the rejected blobs come from your own installed port)
$zipDir = Join-Path $env:TEMP ('trudlcport_native_' + (Get-Date -Format 'yyyyMMdd_HHmmss')); New-Item -ItemType Directory $zipDir | Out-Null
foreach ($n in 'native_report.txt', 'SUMMARY.txt', 'native_progress.txt', 'shaders_index.tsv', 'extract_summary.txt') { $p = Join-Path $Dir $n; if (Test-Path $p) { Copy-Item $p $zipDir } }
$bd = Join-Path $zipDir 'rejected'; New-Item -ItemType Directory $bd | Out-Null
foreach ($r in $failRows) { $n = ($r -split "`t")[2]; foreach ($sub in 'shaders', 'probes') { $p = Join-Path (Join-Path $Dir $sub) $n; if (Test-Path $p) { Copy-Item $p $bd } } }
$zip = Join-Path $Dir 'trudlcport_native_result.zip'
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path (Join-Path $zipDir '*') -DestinationPath $zip
Remove-Item -Recurse -Force $zipDir
$S | ForEach-Object { Write-Host $_ }
Write-Host ''
Write-Host "Short summary: $sum"
Write-Host "Send this file: $zip"
