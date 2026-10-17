# Verified technical findings

Compact reference of facts the project established. "Verified" = checked against base-game Xbox↔PC pairs, against decompiled engine code, or in a running game.

## Containers and ids
* DRM = list of typed sections; CDRM = compressed DRM. Xbox is big-endian, PC little-endian. Section types seen: 2/7/8/11 generic (7 = DTP, 8 = script, 11 = object), 5 texture, 6 wave, 9 shader lib, 10 material, 12 mesh/terrain, 13 map, 100 symbols.
* Relocations: *internal* (pointer inside a section) and *external* (section-index references). `idref`s resolve by (type,id) across the loaded set. Writing a DRM requires external-reloc section indices to be remapped when sections are added/removed; appending a section at the end is safe only if no existing external reloc targets an index ≥ the old count.
* The engine keeps **one global texture cache keyed by id with a per-DRM refcount**. A material may point to a texture that is not in its own DRM, but then that texture must be contained in at least one *resident* DRM, otherwise it dangles when the container unloads → `R6025`. Check: `work/crash/B84_r6025/tex_lifetime_check.py`.
* Same material id ⇒ the engine must see identical shader-lib bytes in every DRM (gate `gate_stesso_id`); each translated material gets its own lib id (2756–2774, 2775–2781, 2782; 975/976 are VS/PS donors copied into streamgroups).
* The engine has **16352 "dead bits"** (unique-id bits); uids ≥ 16352 are no-ops for set and read as alive. DLC ids were shifted by +20000 for 5 intro uids.

## Materials
* Header: `+0x28..0x37` tuple of 4 shader lib ids (PS pass 0, PS pass 1, lit PS, VS); `+0x38` blend type (5 = alpha-blend additive `SRCALPHA/ONE`, 6 = reverse-subtract variant, 2–4 and 7–9 other modes; via `FUN_00527a80`); `+0x40` bits 3/7 (`0x88`) = translucent sort class only; `+0x4c..0x53` per-pass bytes (`+0x50..0x52` index the 16-byte MaterialParams records); MaterialParams at the internal reloc `0x5C`, count at `+0x58`, registers start at `c100`.
* PC and Xbox MaterialParams layouts differ per shader family; the mapping is a per-lib-pair permutation/compaction, derived by role signatures (`param_rules`, `work/ws/visual2/rolefix*.py`, `work/ws/contratti`). Blindly scaling them (B41) produced neon-green planks and red tints.
* Xbox DXN (2-channel normal) textures become PC DXT5 with `x` in R, `y` in A; the translator has an option `dxn` for materials whose normal sampler isn't named `*_Normal_`.

## Shaders
* Xbox pixel shaders are lit with a light model different from PC's; "transplant" copies the PC light block into the translated Xbox shader using numerically matched inputs/outputs (oracle: base-game pairs, 300/300 self-test).
* PC stock lit lib 242 has 8 slots (which slot the engine selects for a given draw was not established); the final colour is `lerp(color, c0, fog)` with `fog = tex(s15, (v4.w, c54.z)).x` (the Xbox shaders do the same with their `AttenuationSampler`/s15 read); a harness must return 0 for that fog read.
* Harness caveats: constants are random unless set; light attenuation sampler `s15` ('ATT' sentinel `c54.z = 0.987654`); Xbox `p_Lights` uses 13 registers per light; direct-light share is only 50 %/33 %, so results about direct lighting are weak.
* Shader acceptance: a lib with a sampler `dcl` ≥ s16 made the video driver fail at start-up (B75); stay within s0–s15 and check with `vm_ps_validate.ps1` + `vm_ps_draw.ps1`.

## Engine functions and crashes (PC `tru.exe` 1.1, unpacked)
| Address | What | Crash / fix |
|---|---|---|
| `FUN_00582200` | audio init | FMOD `System::init` failure leaves three locals uninitialised → AV `0x7b92fb`; `fmod_init_guard` zeroes them |
| `FUN_0050a5f0` / `FUN_005076e0` | projected light binding | `X+0x418` sometimes holds a pointer to a render view instead of the texture → AV `0x5076fa`; `light_tex_guard` restores it when it differs from the invariant of `FinalizeInitialization` |
| `FUN_005920b0` | SoundPlex node walker (jump table `0x5923cc`, 14 node types) | type 0 reads a float via `[edi+4]`; null data → AV `0x592218`; `soundplex_guard` hooks `0x5920D5` and returns NULL for null-data nodes (not for types 2 and 8, which handle it) |
| `FUN_007c493d` | D3D device creation | boot crash `0x3c4984` = infrastructure (driver/VM), not data |
| `FUN_004d7680`, `FUN_004d4be0`, `FUN_004d4a00` | UberObject command list / transition | used to trace gate/bridge logic |
| `FUN_0057ce50` (PC) / `FUN_82223398` (Xbox) | script interpreter, 133 cases | same structure on both |

## Cutscenes, audio, physics
* Cutscene command lists are records `{u16 type, u16 frame}{u32 uid}{u16,u8,u8}{u16 msg, u16 par}[extra]`; `length = 12 + 4*(type>>12)` (format A) or `8 + ...` (B, with initial DTP id); terminator `ffff0000`. Converting them as plain u32 words swaps type/frame and the cinematic never gets `Cine_Start`.
* Audio: all DLC audio was initially emitted as silence on purpose; real audio = Xbox XMA decoded and re-encoded as IMA ADPCM into the same-size Wave sections / `.mul` streams.
* Physics records for custom-range grapple rings (tag `0x404`): the enable byte at `+4` must stay raw.
* u16-swapped type words in PC SoundPlex nodes (e.g. `0xB0000`) fall to the walker's default case and return NULL harmlessly (costume DTPs, knight_thrall, adren_trap).
