# Tier 4 baseline: Kissat 4.0.4, default options

Run on 27 November 2026 with `shortcuts/tier4_baseline.py 300 4`: a 300-second wall-clock limit per instance, four at a time, on an 8-core Apple M3 laptop. Times are CPU seconds. Each model Kissat returned was checked by decoding the message bits, hashing them with a plain Python SHA-256, and comparing against the full digest. All passed.

**Solved: 18 of 24.** Not solved within the limit: the 6 instances at 19 and 20 rounds. All 24 are satisfiable, since each has a planted message.

## Why brute force is out

Every instance gives the full 256-bit digest and leaves at least 64 message bits unknown.

- **free64** (64 unknown bits, almost certainly one solution): trying candidates one at a time needs about 2^63 hash evaluations on average. At the 30 million per second Frobenius reports for its SHA-256 sweep, that is about 9,700 years on one core.
- **free512** (all 512 bits unknown): a random message matches with probability 2^-256, so enumeration is hopeless at any speed.

Kissat solves all twelve free64 instances in about a second each. It reasons about the circuit instead of sweeping candidates. That is the reverse of the nonce benchmark, where sweeping wins.

## Results

| instance | rounds | unknown bits | Kissat answer | CPU seconds |
|---|---:|---:|---|---:|
| sha256_r17_free512_s1 | 17 | 512 | SAT | 0.38 |
| sha256_r17_free512_s2 | 17 | 512 | SAT | 0.35 |
| sha256_r17_free512_s3 | 17 | 512 | SAT | 0.38 |
| sha256_r18_free512_s1 | 18 | 512 | SAT | 6.72 |
| sha256_r18_free512_s2 | 18 | 512 | SAT | 201.39 |
| sha256_r18_free512_s3 | 18 | 512 | SAT | 83.36 |
| sha256_r19_free512_s1 | 19 | 512 | not solved in 300 s | 265.68 |
| sha256_r19_free512_s2 | 19 | 512 | not solved in 300 s | 266.12 |
| sha256_r19_free512_s3 | 19 | 512 | not solved in 300 s | 258.64 |
| sha256_r20_free512_s1 | 20 | 512 | not solved in 300 s | 261.13 |
| sha256_r20_free512_s2 | 20 | 512 | not solved in 300 s | 255.41 |
| sha256_r20_free512_s3 | 20 | 512 | not solved in 300 s | 255.23 |
| sha256_r13_free64_s1 | 13 | 64 | SAT | 0.09 |
| sha256_r13_free64_s2 | 13 | 64 | SAT | 0.11 |
| sha256_r13_free64_s3 | 13 | 64 | SAT | 0.09 |
| sha256_r14_free64_s1 | 14 | 64 | SAT | 0.15 |
| sha256_r14_free64_s2 | 14 | 64 | SAT | 0.11 |
| sha256_r14_free64_s3 | 14 | 64 | SAT | 0.14 |
| sha256_r15_free64_s1 | 15 | 64 | SAT | 0.87 |
| sha256_r15_free64_s2 | 15 | 64 | SAT | 0.12 |
| sha256_r15_free64_s3 | 15 | 64 | SAT | 1.10 |
| sha256_r16_free64_s1 | 16 | 64 | SAT | 1.09 |
| sha256_r16_free64_s2 | 16 | 64 | SAT | 1.20 |
| sha256_r16_free64_s3 | 16 | 64 | SAT | 0.52 |

Raw output: [tier4-kissat.tsv](tier4-kissat.tsv).

## Notes

- **16 rounds with all bits free is left out on purpose.** Up to 16 rounds each message word goes straight into one round, so you can work backwards from the digest and choose the words. Kissat solves that case instantly (we checked) and so would any method that spots it. From round 17 on, the message expansion ties the words together.
- **The 19- and 20-round instances are the stretch goal.** We don't know how to solve them in 300 s. A solver that does, with models that pass the hash check, would be showing something.
- Calibration runs during design gave similar times: 18 rounds solved in 24 s, and 20 rounds and above not solved in 60 s.
