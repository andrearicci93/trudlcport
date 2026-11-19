# Native Direct3D 9 test v3 (TRU DLC port, build B269)

Checks whether your GPU driver and Windows' own Direct3D 9 accept every graphics resource of the installed DLC port, and tells exactly which one is refused and why. It changes nothing in the game folder or in the registry, and it contains no game data: the shaders it tests are read from your own installed `mods\` folder.

## How to run it (about 2 minutes)

1. Close the game. Unzip this folder anywhere (for example on the Desktop).
2. Double-click `RUN_TEST.bat`.
3. When it asks, paste your game folder (the one with `tru.exe` and `mods`), for example
   `C:\Program Files (x86)\Steam\steamapps\common\Tomb Raider Underworld`, and press Enter.
   - If you just press Enter, the test still runs, but only with the synthetic probe shaders.
   - Python 3 is needed only to read the port's shaders. You already have it if you used the installer.
4. Send back **`trudlcport_native_result.zip`** (in this folder). `SUMMARY.txt` is a short version you can paste in a chat.

### Optional second test

Run `RUN_DRAW_TEST.bat` only if the first test reports **0 rejected port shaders** and the game still shows *"A problem has occurred with your display driver"*.

- It also draws one triangle with every pixel shader, which is closer to what the game does.
- It can trigger the same short driver reset as the game. Save your work first.
- If the screen resets or the PC freezes, open `native_progress.txt`: its last line names the shader that was being drawn. Send that file too.

## What is in the result

| File | Content |
|---|---|
| `SUMMARY.txt` | Windows version, GPU, driver version and date, display mode, d3d9.dll version, totals per test, the first 25 rejected shaders with lib id, md5, HRESULT, static finding, suspicious instruction and source DRM |
| `native_report.txt` | One line per resource: `ok`/`FAIL`, HRESULT code and name (`D3DERR_INVALIDCALL`, ...), plus the GPU caps (`PS30Slots`, `VS30Slots`, ...) |
| `shaders_index.tsv` | Every shader of your install: lib id, slot, size, md5, instruction count, the DRM files that contain it, static findings, and the disassembly of the first suspicious instruction |
| `extract_summary.txt` | Static findings on the shaders, readable without Windows |
| `native_progress.txt` | The last step reached, which survives a driver crash |
| `rejected\` | The rejected shader blobs, taken from your own installed port, so they can be reproduced |

**Why the instruction text comes from a static scan.** `CreatePixelShader` only returns an HRESULT, never the failing line. The suspicious instruction therefore comes from `native_extract.py`. It flags these cases:

- `ABS_CONST`: abs or -abs on a constant, for example `cmp r0, -|c221|, ...`.
- `SINCOS_SAME`: `sincos` whose destination is also its source.
- `LONG`: more than 512 instruction slots.
- `NEW_FORM`: a form that none of the 5594 shaders of the original PC game uses.
- `ERR`: a ps_3_0/vs_3_0 rule is broken.

`ABS_CONST` and `SINCOS_SAME` are the two forms an AMD driver refused on 20 Oct 2026. They are fixed in B269_nativo, where the expected count is 0.

## Tests performed

- `CreatePixelShader` / `CreateVertexShader` on the probes, then on every port shader (`new_*` = made by the port, `pc_*` = identical to a PC-game shader).
- Probes: length 511 … 32769 slots, single features, and negative controls that must be rejected (`TEST VALID: True` means the test is meaningful).
- `CreateVertexDeclaration` on the engine's vertex formats (`decls.json`).
- `CreateTexture` / `CreateCubeTexture` for every format/size/mip combination of your install (`textures_installed.json`) and of the B269 reference list (`textures.json`).
- Render targets (A8R8G8B8, X8R8G8B8, R5G6B5, A16B16G16R16F, G16R16F, R16F, R32F, G16R16, A2R10G10B10), depth buffers (D24S8, D24X8, D16, INTZ, DF24) with `CheckDeviceFormat`, and state blocks (ALL, PIXEL, VERTEX).
- The device is created the way the game creates it: HAL, hardware vertex processing plus pure device, D24S8. It falls back to plain hardware VP, then software VP.

## dgVoodoo2 / DXVK

If the game shows the driver error, it usually runs through a wrapper that compiles the shaders itself:

- **DXVK**: copy `x32\d3d9.dll` next to `tru.exe`.
- **dgVoodoo2** (<http://dege.fw.hu/>): copy `MS\x86\D3D9.dll` next to `tru.exe`, plus `dgvoodoo\dgVoodoo.conf` from this folder.

To undo either one, delete the copied files. Run this test **without** them, because it must test Windows' own d3d9.dll.
