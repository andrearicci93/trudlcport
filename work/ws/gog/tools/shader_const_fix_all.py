#!/usr/bin/env python3
"""shader_const_fix_all.py - run the fork's tools/shader_const_fix.py over all PORT shader libraries (type 9).

The fork's fix (one constant register per instruction, extra constants moved through a free temp register, every
changed shader re-assembled with D3DX9) only touches libraries in shader_libs.NEW_LIBS (2173, 2720-2783). The B270 kit
has port libraries above 2783 (2789, 2810, 2811 ...) that Windows' D3D9 still rejects (native test 2026-11-18: 228
left). The rewrite changes only instructions that read two different constant registers, a form D3D9 always rejects,
so original PC shaders (all accepted) are never changed. This wrapper widens the set without editing the fork.

  python -I work/ws/gog/tools/shader_const_fix_all.py IN_MODS OUT_MODS [--fork DIR]

Writes only changed DRMs to OUT_MODS (same relative paths), like the fork tool.
"""
import argparse, os, sys

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('src'); ap.add_argument('dst')
ap.add_argument('--fork', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tomb-raider-underworld-dlc-pc'))
a = ap.parse_args()
sys.path.insert(0, os.path.join(os.path.abspath(a.fork), 'tools'))
import shader_const_fix as F                       # noqa: E402  (fork tool, unchanged)


class PortLibs:
    """The fork's port-library ids (2173, 2720-2783) plus every id above 2783 (later port libraries, e.g. B270's
    2789 / 2810 / 2811). PC libraries (below 2720, except 2173) are left alone: some of them cannot be rebuilt
    byte-identically by the fork's writer, and none of them is rejected by D3D9 anyway."""
    def __contains__(self, x): return x == 2173 or x >= 2720


F.NEW_LIBS = PortLibs()
F.main([a.src, a.dst])
