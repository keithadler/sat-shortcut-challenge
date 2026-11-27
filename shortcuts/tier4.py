"""Tier 4 instances: reduced-round SHA-256 preimages that brute force cannot reach.

Every instance fixes the full 256-bit digest of a planted message, so it is satisfiable, and leaves at
least 64 message bits unknown. Trying candidates one by one (as a nonce sweep does) would take about
2^64 hash evaluations or more: centuries at any speed. A clause-learning solver solves most of them.

Two families, three seeds each:
  free512  all 512 message bits unknown, 17 to 20 rounds   (16 rounds or fewer is excluded: the
           message words enter the rounds directly there, and solving backwards inverts it at once)
  free64   64 unknown bits scattered over the message words the rounds use, 13 to 16 rounds

Writes instances/tier4/*.cnf.xz and prints a sha256 for each. Usage: python tier4.py
check(name, model) verifies a solver's model by hashing the decoded message (see tier4_check.py).
"""
import os, random, hashlib, lzma
import sha256cnf as S

def spec():
    for r in (17, 18, 19, 20):
        for seed in (1, 2, 3):
            yield f"sha256_r{r}_free512_s{seed}", r, list(range(512)), seed
    for r in (13, 14, 15, 16):
        for seed in (1, 2, 3):
            free = random.Random(f"tier4-free64-r{r}-s{seed}").sample(range(32 * r), 64)
            yield f"sha256_r{r}_free64_s{seed}", r, free, seed

def build(name):
    for n, r, free, seed in spec():
        if n == name:
            return S.encode(r, free, range(256), seed=f"tier4-{n}")
    raise KeyError(name)

def check(name, model_true):
    _, _, meta = build(name)
    return S.check_model(model_true, meta)

if __name__ == '__main__':
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instances', 'tier4')
    os.makedirs(out, exist_ok=True)
    for name, r, free, seed in spec():
        cl, n, meta = build(name)
        body = (f"c {name}: {r}-round SHA-256, {len(meta['free'])} unknown message bits, full 256-bit digest given\n"
                f"c variable p+1 is message bit p (bit 0 = most significant bit of W[0]); planted, so satisfiable\n"
                f"p cnf {n} {len(cl)}\n" + ''.join(' '.join(map(str, c)) + ' 0\n' for c in cl)).encode()
        fn = os.path.join(out, f"{name}.cnf.xz")
        with open(fn, 'wb') as fh:
            fh.write(lzma.compress(body, preset=9))
        print(hashlib.sha256(body).hexdigest(), f"tier4/{name}.cnf", flush=True)
