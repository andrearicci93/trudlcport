# Notes from upstream (andrearicci93/trudlcport)

Hi Lukas! Andrea here, the author of the upstream project. Your fork is impressive work, and **I would really like to work
together**. I'm still actively developing my port (currently build B278, played on native D3D9). We have been solving the
same problems twice, and each of us has fixes the other one is missing.

- I opened [issue #6](https://github.com/andrearicci93/trudlcport/issues/6) to discuss joining forces, and I sent you a
  collaborator invite (push access) to trudlcport. It is still pending.
- This PR only adds this notes file. Merge it, close it or just read it, whatever suits you. Issues are disabled on your
  fork, so a PR was the only way I found to reach you here.

## Fixes upstream has that your `windows` branch did not have (checked 19/11/2026)

All of these are data (or exe) words verified against the Xbox 360 files and tested in game.

1. **Rock vein, u8 type lists (B272).** `doppelganger_casual.drm` and its clone `dlc_doppel_costume_a.drm`, DTP 20212: 9 u8
   markup-type lists in the movement-mode filters (mode +0x94/+0x9c filter, entry +0x18 count, +0x1c u8 list) were
   converted as 32/16-bit words. Type 22 (vein) ends up at the wrong byte and reads as 0, so mode 107 (state 0x439, grab
   the vein while falling) and modes 44/45/46/106/117 never accept a vein. Correct PC bytes = Xbox bytes (u8 data):

   | DTP 20212 offset | converted PC bytes | correct (= Xbox) |
   |---|---|---|
   | 0x7efb0 | 080e0016 | 0e081600 |
   | 0x7f020 | 1011121300001614 | 1011121314160000 |
   | 0x7f060 | 00000016 | 16000000 |
   | 0x7f5b0 | 00000016 | 16000000 |
   | 0x7f5e0 | 00000016 | 16000000 |
   | 0x7f740 | 00000002 | 02000000 |
   | 0x7ff00 | 00000016 | 16000000 |
   | 0x800c0 | 00001609 | 09160000 |
   | 0x801e0 | 00000017 | 17000000 |

2. **Rock vein, profile-level list (B273).** Same DTP 20212, the 19-type profile list at 0x80ed0 (fall modes 44/46/106/117,
   filter P = mode+0x94, P+0xc count, P+0x10 list). Its last word 0x80ee0 was converted as two u16:
   `15080016` -> must be `08151600`. Type 22 falls out of the list, so the drop from the ledge never finds the vein below.
   **With B272 + B273 the ledge -> vein drop in goo_room works in game (18/11).** This may be your open "ledge -> vein
   jump goes back" problem.

3. **Ledge floor threshold (B274, exe).** The "floor below the ledge" test in 0x7260b0 compares against the float at
   0x85e4ac (-628.9395, the same as the base Xbox build). The Xbox Title Update uses **-616.2975** there. The goo_room
   ledge under the vein has the eitr pool at -625.9, so the PC rejects it and the TU accepts it. Only the two `fcomp`
   uses at 0x726356 and 0x7263ed are affected.

4. **machine_room terrain group mask (B275).** `dlc2_machine_room.drm`, DTP 25392, data block of terrain group 14 at
   +0x22420, word +0x24: Xbox 0x00002000, but the converter copied the bytes instead of swapping them (PC `00002000`).
   Correct PC bytes: `00200000`. Without the fix, one level of the central structure (render section 26691) is not
   drawn while its collision is still there: a "transparent wall" in front of the dome. It is the only case in all 190
   DLC DRMs.

## Taken from your fork, with thanks

- B276: `scriptclash`, the DLC 2 thrall base script 12433 vs the resident generalbank 12433. We renumbered it to 26893,
  because 26884 is taken in our data.
- B277: `objfield`, `playerblock`, `genintro`, `idword`, `fxnode`, `exttuning` (42 words in 22 DRMs, each checked against
  the Xbox source).
- B278: `fxrelayout` (6 table-record DTPs). We proved it on 25/25 base pairs. We left out `dlc_fx_bloom`, because its n=4
  array would overrun the particle records.
- Checked on our side and already fine: objtex, seqrepeat, navraw, .mul step cap, lv90dtp, fxrecread.

## Where your eyes would help

machine_room after unlocking the moving structure: one piece of it is still missing compared with the Xbox, the blue goo
columns there look incomplete, and a doorway still looks transparent. The data and script terrain-group references match
the Xbox, the three structure tiers are enabled at runtime, and the shaders in the area show no linkage problems. If you
have seen this on your side, I'd love to hear about it.

Looking forward to working together!

Andrea (@andrearicci93)
