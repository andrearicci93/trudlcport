# Troubleshooting (players)

## Lock the game to 60 fps

Tomb Raider: Underworld ties physics and camera to the frame rate (variable time step, one physics step per frame). Above 60 fps
boxes, ragdolls and physics puzzles can break, in the base game and even more in the DLC. Lock the game to **60 fps** with one of:

- in-game V-Sync on a 60 Hz display;
- the frame limiter of your GPU driver (NVIDIA Control Panel → *Max Frame Rate*, AMD *Frame Rate Target Control*) or RTSS;
- [dxwrapper](https://github.com/elishacloud/dxwrapper) with `LimitPerFrameFPS = 60`;
- dgVoodoo2 (see below), which also has an `FPSLimit` option.

## "A problem has occurred with your display driver"

**What happened (20-21 Oct 2026).** A player with an AMD RX 9070 XT (Windows 11, Windows' own Direct3D 9) got this box. The native test showed why: the driver refused pixel shaders that use two forms the original PC game never uses.

- `cmp` with an abs/-abs constant source, for example `cmp r0, -|c221|, ...`;
- `sincos` whose destination is also its source.

**Status.** B133 fixed the 274 shaders of B132. The converter brought the forms back from B147, and B147-B268 contain 240 of them (DLC1 and DLC2). In **B269** they are rewritten (bit-equivalent in our shader VM), the converter is fixed, and a build gate blocks them. This is verified offline only, so please run the test below once on B269 or later.

### Workaround: DXVK (or dgVoodoo2)

Both compile the shaders themselves and do not go through Windows' D3D9 validation.

- **DXVK**: from <https://github.com/doitsujin/dxvk/releases> copy `x32\d3d9.dll` next to `tru.exe`. To undo, delete it.
- **dgVoodoo2**: from <http://dege.fw.hu/> copy `MS\x86\D3D9.dll` next to `tru.exe`, plus [`tools/native_test/dgvoodoo/dgVoodoo.conf`](../tools/native_test/dgvoodoo/dgVoodoo.conf).

### Help us: run the native test v3 (2 minutes, changes nothing)

1. Download `trudlcport-native-test-v3.zip` from the latest release (or use [`tools/native_test`](../tools/native_test)) and unzip it anywhere.
2. Close the game and **move DXVK/dgVoodoo away** for the test.
3. Double-click `RUN_TEST.bat` and paste the game folder.

It reads the shaders of your installed `mods\` and creates on your GPU, with the game's device flags:

- every shader;
- every vertex layout and texture format;
- the render-target and depth formats;
- the state blocks.

It works without the game or the port too, with synthetic probes only.

Send us (GitHub issue) **`trudlcport_native_result.zip`**. `SUMMARY.txt` inside it is a short version you can paste. The zip contains:

- GPU, driver version and date, Windows build, display mode;
- every rejected shader with its lib id, source DRM, size, MD5, HRESULT and the suspicious instruction.

Also tell us **when** the box appears: at start-up, in the menu, or in the DLC (where).

If the test reports 0 rejected port shaders and the box still appears, run `RUN_DRAW_TEST.bat`.

- It also draws with every shader and can reset the screen once.
- If the driver resets, `native_progress.txt` names the shader that was being drawn.

---

## In italiano (breve)

- **Blocca il gioco a 60 fps** (V-Sync a 60 Hz, limitatore del driver NVIDIA/AMD o RTSS, dxwrapper `LimitPerFrameFPS = 60`):
  sopra i 60 fps fisica e camera si rompono.
- **"A problem has occurred with your display driver"**: in B269 sono corrette le forme di shader che il D3D9 di Windows rifiuta su AMD
  (verificato solo offline). Rimedio immediato: DXVK (`x32\d3d9.dll` accanto a `tru.exe`) o dgVoodoo2. Per aiutarci: a gioco chiuso
  lancia `RUN_TEST.bat` da `trudlcport-native-test-v3.zip` e mandaci `trudlcport_native_result.zip`.
