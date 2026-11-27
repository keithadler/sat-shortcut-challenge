# SHA-256 nonce scaling: brute force alongside Frobenius

The claim (27 Nov 2026): "In the exponential limit, at solving SHA256 preimage nonces", Frobenius is 38,000x faster than CaDiCaL, 41,200x faster than dense-solver, 61,400x faster than Kissat, and 1.6 to 2.17 million times faster than CryptoMiniSat. The benchmark is [lukehutch/SAT-benchmarks/sha256-64r-nonce-scaling](https://github.com/lukehutch/SAT-benchmarks/tree/main/sha256-64r-nonce-scaling).

## The instance

Full 64-round SHA-256 on one padded block. All 512 message bits are known except the low `k` bits of word `W[0]`. The 256-bit digest is given. `k` runs from 1 to 32, so the largest instance has 2^32 candidates (about 4.3 billion).

## The textbook baseline

[`shortcuts/nonce_bruteforce.c`](../shortcuts/nonce_bruteforce.c) is a 150-line C program. It rebuilds the instance exactly as the benchmark's `src/main.rs` does, then tries every value of the unknown bits in ascending order and hashes each one until the digest matches. There is no SAT and no circuit analysis. The target digest it rebuilds, `e43badc8…17b3321e`, matches Python `hashlib`.

One core of an Apple M3:

| k | Engine | Candidates tried | Time | Rate |
|---|---|---|---|---|
| 32 | ARMv8 SHA-256 instructions | 2,654,435,770 | **47.0 s** | 56.5M/s |
| 32 | plain portable C | 2,654,435,770 | 471.6 s | 5.6M/s |
| 24 | ARMv8 SHA-256 instructions | 3,635,642 | 0.063 s | 57.9M/s |
| 20 | ARMv8 SHA-256 instructions | 489,914 | 0.009 s | 56.8M/s |

Frobenius, as reported in the benchmark README (one core of a Ryzen 9 5950X): **87.2 s** at k = 32 from `.aig` (30.3M evaluations per second) and 106.6 s from `.cnf`.

Kissat 4.0.4 on the same `.cnf` files, as a check that our machine agrees with theirs: k = 10 took 6.6 s, k = 12 took 20.2 s (their table: 21.9 s at k = 12).

## What this shows

1. **Frobenius solves this benchmark by brute force.** Its README describes the method: compiled AVX2 code that evaluates SHA-256 on every candidate ("`BitSliceJit`", "`WordDag` AVX2 JIT"), at 22M to 30M evaluations per second. Testing 0.616 × 2^32 candidates at 30M/s takes about 87 s, which is the reported time.

2. **A plain loop is about as fast.** The loop using the chip's SHA instructions finished k = 32 in 47 s, about 1.9 times faster than Frobenius's reported time. Different CPUs, so the exact ratio means little. The main point is that a short program of a kind used since the early days of Bitcoin mining performs in the same range. The portable-C loop, with no hardware help, is about 5 times slower than Frobenius. That is the gain from a well-built bitsliced evaluator, which is good engineering but not a new solving method.

3. **CDCL solvers are known to be poor at this.** A clause-learning solver does not hash 4 billion candidates quickly. It works through a 280,000-clause encoding one decision at a time, and on a full-round hash it learns little that carries over from one candidate to the next. Exhaustive search beating CDCL on hash preimages is long-established, which is why Bitcoin miners do not use SAT solvers.

4. **The headline ratios are throughput ratios, extrapolated.** The README says it directly: every solver scales as 2^k, and the "exponential-limit speedup" is the constant ratio of time per candidate. No CDCL solver was run past k ≈ 17, so every multi-thousand figure is a straight-line extrapolation out to k = 32 or beyond. Nothing changes asymptotically: Frobenius and the brute-force loop both double in time with each extra bit.

## Verdict

The measured numbers look honest. The CDCL times match ours, and Frobenius really does solve k = 32 in under two minutes. But the claim amounts to "brute force evaluates SHA-256 faster than CDCL solvers do", and a 150-line loop matches it. This is a textbook case of the point in the main README: the problem has a known shortcut (here, just evaluating the function), and the solver uses that shortcut.

What would change this: a k well beyond 32 (say 48 or 64) solved faster than 2^k candidate evaluations allow, or any instance where the unknown bits sit somewhere a forward sweep cannot reach, such as unknown digest bits combined with a partly known message.

## Reproduce

```bash
clang -O3 -mcpu=native -o nonce_bruteforce shortcuts/nonce_bruteforce.c
./nonce_bruteforce 32 hw     # ARMv8 SHA instructions
./nonce_bruteforce 32 c      # portable C
```

On x86 only the `c` engine is built in. Run 27 Nov 2026.
