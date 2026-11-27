"""Reduced-round SHA-256 as CNF, with a planted preimage.

encode(rounds, free_bits, digest_bits, seed) -> (clauses, nvars, meta)
  rounds       number of compression rounds, 1..64 (feed-forward of the IV is always applied)
  free_bits    message bit positions (0..511, bit 0 = MSB of W[0]) left unknown; the rest are fixed
  digest_bits  output bit positions (0..255, bit 0 = MSB of H[0]) whose value is given
  seed         picks the planted 512-bit message, so every instance is satisfiable

Message variable for position p is p + 1 (DIMACS), so a model decodes directly.
Constants are folded, rotations are renaming, additions are ripple-carry full adders,
Ch / Maj / three-way XOR are each one Tseitin gate.
"""
import random

K = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]
IV = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]
M32 = 0xFFFFFFFF

def ror(x, n): return ((x >> n) | (x << (32 - n))) & M32

def compress(words, rounds):
    """Reference: `rounds`-round SHA-256 compression of 16 words, with IV feed-forward."""
    w = list(words)
    for i in range(16, 64):
        s0 = ror(w[i-15], 7) ^ ror(w[i-15], 18) ^ (w[i-15] >> 3)
        s1 = ror(w[i-2], 17) ^ ror(w[i-2], 19) ^ (w[i-2] >> 10)
        w.append((w[i-16] + s0 + w[i-7] + s1) & M32)
    a, b, c, d, e, f, g, h = IV
    for i in range(rounds):
        t1 = (h + (ror(e, 6) ^ ror(e, 11) ^ ror(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + w[i]) & M32
        t2 = ((ror(a, 2) ^ ror(a, 13) ^ ror(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) & M32
        a, b, c, d, e, f, g, h = (t1 + t2) & M32, a, b, c, (d + t1) & M32, e, f, g
    return [(x + y) & M32 for x, y in zip((a, b, c, d, e, f, g, h), IV)]

def words_to_bits(ws): return [(ws[p // 32] >> (31 - p % 32)) & 1 for p in range(32 * len(ws))]
def bits_to_words(bs): return [sum(bs[32*i + j] << (31 - j) for j in range(32)) for i in range(len(bs) // 32)]


class CNF:
    """Bits are Python bools (constants) or nonzero ints (literals). Words are lists of 32 bits, index 0 = LSB."""
    def __init__(self, nfixed):
        self.n = nfixed; self.cl = []
    def var(self):
        self.n += 1; return self.n
    @staticmethod
    def neg(x): return (not x) if isinstance(x, bool) else -x

    def xor2(self, a, b):
        if isinstance(a, bool): return self.neg(b) if a else b
        if isinstance(b, bool): return self.neg(a) if b else a
        if a == b: return False
        if a == -b: return True
        z = self.var()
        self.cl += [[-a, -b, -z], [a, b, -z], [a, -b, z], [-a, b, z]]
        return z
    def xor3(self, a, b, c):
        if any(isinstance(x, bool) for x in (a, b, c)) or len({abs(a), abs(b), abs(c)}) < 3:
            return self.xor2(self.xor2(a, b), c)
        z = self.var()
        for sa in (1, -1):
            for sb in (1, -1):
                for sc in (1, -1):
                    par = (sa < 0) ^ (sb < 0) ^ (sc < 0)   # clause forbids a=(sa<0),b=(sb<0),c=(sc<0) with z wrong
                    self.cl.append([sa * a, sb * b, sc * c, z if par else -z])
        return z
    def and2(self, a, b):
        if isinstance(a, bool): return b if a else False
        if isinstance(b, bool): return a if b else False
        if a == b: return a
        if a == -b: return False
        z = self.var(); self.cl += [[-z, a], [-z, b], [z, -a, -b]]; return z
    def or2(self, a, b): return self.neg(self.and2(self.neg(a), self.neg(b)))
    def mux(self, s, t, f):            # s ? t : f   (this is Ch)
        if isinstance(s, bool): return t if s else f
        if isinstance(t, bool) or isinstance(f, bool) or abs(t) == abs(f):
            return self.or2(self.and2(s, t), self.and2(self.neg(s), f))
        z = self.var()
        self.cl += [[-s, -t, z], [-s, t, -z], [s, -f, z], [s, f, -z], [-t, -f, z], [t, f, -z]]
        return z
    def maj(self, a, b, c):
        if any(isinstance(x, bool) for x in (a, b, c)) or len({abs(a), abs(b), abs(c)}) < 3:
            return self.or2(self.or2(self.and2(a, b), self.and2(a, c)), self.and2(b, c))
        z = self.var()
        self.cl += [[-a, -b, z], [-a, -c, z], [-b, -c, z], [a, b, -z], [a, c, -z], [b, c, -z]]
        return z

    # word operations
    def const(self, v): return [bool((v >> i) & 1) for i in range(32)]
    def rot(self, x, n): return [x[(i + n) % 32] for i in range(32)]          # rotate right by n
    def shr(self, x, n): return [x[i + n] if i + n < 32 else False for i in range(32)]
    def wxor3(self, a, b, c): return [self.xor3(a[i], b[i], c[i]) for i in range(32)]
    def wch(self, e, f, g): return [self.mux(e[i], f[i], g[i]) for i in range(32)]
    def wmaj(self, a, b, c): return [self.maj(a[i], b[i], c[i]) for i in range(32)]
    def add(self, x, y):
        out, carry = [], False
        for i in range(32):
            out.append(self.xor3(x[i], y[i], carry))
            if i < 31: carry = self.maj(x[i], y[i], carry)
        return out
    def addn(self, *ws):
        acc = ws[0]
        for w in ws[1:]: acc = self.add(acc, w)
        return acc


def encode(rounds, free_bits, digest_bits, seed):
    rng = random.Random(seed)
    msg = [rng.getrandbits(32) for _ in range(16)]
    digest = compress(msg, rounds)
    mbits, dbits = words_to_bits(msg), words_to_bits(digest)
    free = set(free_bits)
    c = CNF(512)
    # message words, LSB-first; bit position p (MSB-first) <-> variable p+1
    W = [[(32*wi + (31 - i) + 1) if (32*wi + (31 - i)) in free else bool(mbits[32*wi + (31 - i)])
          for i in range(32)] for wi in range(16)]
    for i in range(16, max(16, rounds)):
        s0 = c.wxor3(c.rot(W[i-15], 7), c.rot(W[i-15], 18), c.shr(W[i-15], 3))
        s1 = c.wxor3(c.rot(W[i-2], 17), c.rot(W[i-2], 19), c.shr(W[i-2], 10))
        W.append(c.addn(W[i-16], s0, W[i-7], s1))
    a, b, cc, d, e, f, g, h = [c.const(v) for v in IV]
    for i in range(rounds):
        S1 = c.wxor3(c.rot(e, 6), c.rot(e, 11), c.rot(e, 25))
        t1 = c.addn(h, S1, c.wch(e, f, g), c.const(K[i]), W[i])
        S0 = c.wxor3(c.rot(a, 2), c.rot(a, 13), c.rot(a, 22))
        t2 = c.add(S0, c.wmaj(a, b, cc))
        a, b, cc, d, e, f, g, h = c.add(t1, t2), a, b, cc, c.add(d, t1), e, f, g
    out = [c.add(x, c.const(v)) for x, v in zip((a, b, cc, d, e, f, g, h), IV)]
    for q in digest_bits:
        bit = out[q // 32][31 - q % 32]; want = dbits[q]
        if isinstance(bit, bool):
            if bit != bool(want): c.cl.append([])     # cannot happen for a planted instance
        else:
            c.cl.append([bit if want else -bit])
    meta = dict(rounds=rounds, free=sorted(free), digest_bits=sorted(digest_bits),
                fixed_message=[None if p in free else mbits[p] for p in range(512)],
                digest=dbits, seed=seed)
    return c.cl, c.n, meta


def check_model(model_true, meta):
    """model_true: set of positive DIMACS variables. Rebuilds the message, hashes it, checks the given digest bits."""
    bits = [(1 if (p + 1) in model_true else 0) if meta['fixed_message'][p] is None else meta['fixed_message'][p]
            for p in range(512)]
    out = words_to_bits(compress(bits_to_words(bits), meta['rounds']))
    return all(out[q] == meta['digest'][q] for q in meta['digest_bits'])
