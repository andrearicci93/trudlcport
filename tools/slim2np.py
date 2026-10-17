"""One-off: mask_table_best.pkl (19.5M python keys) -> compact numpy index work/generic/mask_best.npz (sorted uint64 hashes + uint8 class codes)."""
import sys, os, pickle, hashlib, numpy as np
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic')
def khash(k):
    return int.from_bytes(hashlib.blake2b(repr(k).encode(), digest_size=8).digest(), 'little')
if __name__ == '__main__':
    best = pickle.load(open(os.path.join(W, 'mask_table_best.pkl'), 'rb'))
    vocab = sorted({v for v in best.values()}, key=repr)
    code = {v: i for i, v in enumerate(vocab)}
    h = np.fromiter((khash(k) for k in best), dtype=np.uint64, count=len(best))
    c = np.fromiter((code[v] for v in best.values()), dtype=np.uint8, count=len(best))
    o = np.argsort(h); h = h[o]; c = c[o]
    np.savez(os.path.join(W, 'mask_best.npz'), h=h, c=c)
    pickle.dump(vocab, open(os.path.join(W, 'mask_best_vocab.pkl'), 'wb'))
    print('keys', len(h), 'vocab', vocab, 'collisions', int((h[1:] == h[:-1]).sum()), flush=True)
