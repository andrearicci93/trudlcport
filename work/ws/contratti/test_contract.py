"""Test di contract.py (sintetici, solo libreria standard + moduli del progetto) e del gate f14 (integrazione sui dati di B84).
  tools/venv/bin/python -I work/ws/contratti/test_contract.py            (i test di integrazione si saltano se mancano i dati)
Non sono test del gioco: provano che i controlli segnalano i casi sbagliati e NON segnalano quelli corretti."""
import sys, os, struct, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import contract as C

END = 0x0000FFFF


def dcl(kind, reg):
    return [0x0200001F, {'2d': 0x90000000, 'cube': 0x98000000}[kind], 0xA00F0800 | reg]


def texld(reg):
    return [0x03000042, 0x800F0000, 0x90E40000, 0xA0E40800 | reg]


def comment(words):
    return [0x0000FFFE | (len(words) << 16)] + list(words)


def program(*parts):
    toks = [0xFFFF0300]
    for p in parts: toks += p
    toks.append(END)
    return struct.pack('<%dI' % len(toks), *toks)


def lib(entries, conv='record_total', metas=None):
    """Sezione ShaderLib: kind 1, una slot per entry. record_total: size = 16 + len(bc) (+ meta<<16)."""
    n = len(entries); tb = 4 * n
    body = bytearray(); slots = []
    for i, bc in enumerate(entries):
        slots.append(8 + tb + len(body))
        size = (16 + len(bc)) if conv == 'record_total' else (8 + len(bc))
        if metas: size |= metas[i] << 16
        body += struct.pack('<II', 0, size) + bytes([i + 1]) * 8 + bc
    out = bytearray(bytes([1, 0, 0, 0]) + struct.pack('<II', tb, 0) + struct.pack('<%dI' % n, *slots) + body)
    struct.pack_into('<I', out, 8, len(out) - 4)
    return bytes(out)


class Samplers(unittest.TestCase):
    def test_decl_and_use(self):
        d, u = C.bytecode_samplers(program(dcl('cube', 0), dcl('2d', 2), texld(2), texld(0)))
        self.assertEqual(d, {0: 'cube', 2: '2d'}); self.assertEqual(u, {0, 2})

    def test_declared_not_used(self):
        d, u = C.bytecode_samplers(program(dcl('cube', 0), dcl('2d', 2), texld(2)))
        self.assertEqual(u, {2}); self.assertIn(0, d)

    def test_comment_not_scanned(self):
        fake = [0x0200001F, 0x98000000, 0xA00F0805, 0x03000042, 0x800F0000, 0x90E40000, 0xA0E40805]   # sembra dcl+texld di s5
        d, u = C.bytecode_samplers(program(comment(fake), dcl('2d', 1), texld(1)))
        self.assertEqual(d, {1: '2d'}); self.assertEqual(u, {1})

    def test_def_literals_not_scanned(self):
        d_ = [0x05000051, 0xA00F0003, 0xA0E40801, 0x0200001F, 0xA0E40802]      # def c3 con letterali che sembrano token di sampler
        d, u = C.bytecode_samplers(program(d_, dcl('2d', 1), texld(1)))
        self.assertEqual(u, {1})


class Framing(unittest.TestCase):
    A = program(dcl('2d', 0), texld(0)); B = program(dcl('cube', 1), texld(1))

    def test_record_total_ok_and_meta_preserved(self):
        f = C.frame_lib(lib([self.A, self.B], metas=[0, 64]))
        self.assertEqual(f['errors'], []); self.assertEqual(f['convention'], ['record_total'])
        self.assertEqual(sorted(e['meta'] for e in f['entries'].values()), [0, 64])
        self.assertEqual(sorted(e['bc'] for e in f['entries'].values()), sorted([self.A, self.B]))

    def test_legacy_convention_recognized_separately(self):
        f = C.frame_lib(lib([self.A, self.B], conv='legacy'))
        self.assertEqual(f['convention'], ['legacy_hash_blob'])

    def test_bad_boundary_rejected(self):
        d = bytearray(lib([self.A, self.B])); off = 4 + struct.unpack_from('<I', d, 12)[0]
        struct.pack_into('<I', d, off + 4, 16 + len(self.A) + 12)          # size sbagliato
        self.assertTrue(C.frame_lib(bytes(d))['errors'])

    def test_extra_bytes_after_end_flagged(self):
        a = self.A + b'\0\0\0\0\0\0\0\0\0\0\0\0'
        f = C.frame_lib(lib([a, self.B]))
        self.assertTrue(any('extra' in e for e in f['errors']))

    def test_duplicate_hash_flagged(self):
        d = bytearray(lib([self.A, self.B]))
        o1 = 4 + struct.unpack_from('<I', d, 12)[0]; o2 = 4 + struct.unpack_from('<I', d, 16)[0]
        d[o2 + 8:o2 + 16] = d[o1 + 8:o1 + 16]
        self.assertTrue(any('hash8' in e for e in C.frame_lib(bytes(d))['errors']))


DATA = os.path.exists(os.path.join(os.path.dirname(HERE), 'shader4', 'f12_plan.pkl')) and \
    os.path.exists(os.path.join(HERE, '..', '..', 'baseline', 'B84', 'mods', 'dlc_caverns_hall.drm'))


@unittest.skipUnless(DATA, 'dati del progetto assenti')
class Gate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import f14_slotmap as F
        cls.F = F
        cls.plan, cls.mods, cls.tree, cls.errs = F.prepare('B84')

    def _ctx(self, mid):
        F = self.F; m = self.plan[mid]; pe = m['_pcsec']
        slotmap, rows = F.derive_slotmap(mid, m['dlc'], pe.data, pe.reloc)
        XPm = F.F10.params(F.F10.f9_common._Sec(*F.libs()['DM'][mid]), 'be')
        return m, slotmap, rows, F.F12.material_opts(mid), XPm

    def test_parent_matches_plan(self):
        self.assertEqual(self.errs, [])

    def test_20264_fails_before_passes_after(self):
        F = self.F; m, slotmap, rows, mo, XPm = self._ctx(20264)
        self.assertEqual(slotmap, {1: 3, 2: 1, 3: 0, 0: 2, 4: 5})
        bcs = {k: b for k, b in enumerate(m['slots']) if b is not None}
        self.assertLess(min(F.contract_gate(bcs, m['dlc'], rows, mo, XPm).values()), F.TH)
        built, info = F.rebuild_material(m, slotmap, rows)
        new = {k: F.sm3asm.encode(T) for k, (T, _, _) in built.items()}
        self.assertGreaterEqual(min(F.contract_gate(new, m['dlc'], rows, mo, XPm).values()), F.TH)

    def test_wrong_permutation_is_caught(self):
        F = self.F; m, slotmap, rows, mo, XPm = self._ctx(20264)
        bad = dict(slotmap); bad[0], bad[2] = bad[2], bad[0]                 # scambio due registri: ancora 2D/cube coerente? no, ma comunque sbagliato
        built, _ = F.rebuild_material(m, bad, rows)
        new = {k: F.sm3asm.encode(T) for k, (T, _, _) in built.items()}
        self.assertLess(min(F.contract_gate(new, m['dlc'], rows, mo, XPm).values()), F.TH)

    def test_silent_2d_swap_caught_by_gate_not_by_dimension_check(self):
        """20346: scambio 2D<->2D: il controllo dimensionale non vede nulla, il gate si'."""
        F = self.F; m, slotmap, rows, mo, XPm = self._ctx(20346)
        bcs = {k: b for k, b in enumerate(m['slots']) if b is not None}
        self.assertNotEqual(slotmap, {a: a for a in slotmap})
        self.assertLess(min(F.contract_gate(bcs, m['dlc'], rows, mo, XPm).values()), F.TH)

    def test_identity_rebuild_is_byte_exact(self):
        F = self.F; m, slotmap, rows, mo, XPm = self._ctx(20321)
        self.assertEqual(slotmap, {a: a for a in slotmap})
        built, _ = F.rebuild_material(m, slotmap, rows)
        for k, (T, _, _) in built.items(): self.assertEqual(F.sm3asm.encode(T), m['slots'][k])

    def test_posthoc_permutation_equals_rebuild(self):
        F = self.F; m, slotmap, rows, mo, XPm = self._ctx(21206)
        built, _ = F.rebuild_material(m, slotmap, rows)
        perm = {a: b for a, b in slotmap.items() if a != b}
        for k, (T, _, _) in built.items():
            self.assertEqual(F.canon_text(F.permute_samplers(m['slots'][k], perm)), F.canon_text(F.sm3asm.encode(T)))

    def test_alpha1_is_remapped_with_the_slotmap_and_inert_on_20264(self):
        """20264 e' l'unico dei 35 con alpha1 (6610): l'opzione deve seguire la mappa (Xbox {1,3} -> PC {0,3}), ma nel pass
        di colore ricostruito 6610 non e' campionata, quindi il testo non cambia (rimappatura difensiva, inerte su questi dati)."""
        F = self.F; m, slotmap, rows, mo, XPm = self._ctx(20264)
        self.assertEqual(set(mo.get('alpha1', ())), {1, 3})
        _, info = F.rebuild_material(m, slotmap, rows)
        self.assertEqual(info['alpha1_pc'], sorted(slotmap[s] for s in (1, 3)))
        self.assertEqual(info['alpha1_pc'], [0, 3])
        orig = F.F12.material_opts
        F.F12.material_opts = lambda mid: {k: v for k, v in orig(mid).items() if k != 'alpha1'}
        try:
            no_a1, _ = F.rebuild_material(m, slotmap, rows)
        finally:
            F.F12.material_opts = orig
        with_a1, _ = F.rebuild_material(m, slotmap, rows)
        for k in with_a1:
            self.assertEqual(F.canon_text(F.sm3asm.encode(with_a1[k][0])), F.canon_text(F.sm3asm.encode(no_a1[k][0])))


if __name__ == '__main__':
    unittest.main(verbosity=2)
