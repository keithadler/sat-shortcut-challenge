# Unsatisfiability proofs, checked by tenet-sat and lrat-trim

The challenge asks for a checked proof behind every "no solution" answer. This file shows that pipeline working on our own instances. CaDiCaL writes a proof for every unsatisfiable instance it can finish. Two independent checkers then check it: [tenet-sat](https://github.com/keithadler/tenet-sat), a parallel LRAT checker, and [lrat-trim](https://github.com/arminbiere/lrat-trim), Armin Biere and Florian Pollitt's single-threaded checker.

Run on 27 November 2026 on an 8-core Apple M3 laptop, using:
- CaDiCaL 3.1.0 with `--lrat` (binary LRAT);
- tenet-sat at commit `e506303` on .NET 10.0.401;
- lrat-trim 0.2.1-rc3 (commit `4231949`) in its default mode, which trims the proof and then checks it backwards.

Times are wall-clock seconds. tenet-sat's include starting the .NET process, about 0.05 s. Script: [`shortcuts/proofs_tenet_sat.sh`](../shortcuts/proofs_tenet_sat.sh).

**Both checkers verified all 26 proofs.** They cover 24 Tier 1 instances and the 2 Tier 3 instances Kissat solved as unsatisfiable. The other unsatisfiable instances (Tseitin n100 and n200, pigeonhole 13/12, chessboard 14x14, 10x10 multiplier) are ones the standard solvers did not finish, so there is no proof to check yet.

| instance | CaDiCaL CPU s | proof size | tenet-sat, 1 thread | tenet-sat, 8 threads | lrat-trim |
|---|---:|---:|---:|---:|---:|
| tseitin_n20_unsat | 0.00 | 2.5 KB | 0.05 | 0.05 | 0.01 |
| tseitin_n30_unsat | 0.00 | 33 KB | 0.06 | 0.05 | 0.01 |
| tseitin_n40_unsat | 0.01 | 165 KB | 0.06 | 0.06 | 0.02 |
| tseitin_n60_unsat | 0.21 | 2.2 MB | 0.12 | 0.09 | 0.06 |
| php_8_7 | 0.03 | 312 KB | 0.07 | 0.06 | 0.01 |
| php_9_8 | 0.29 | 2.8 MB | 0.23 | 0.14 | 0.07 |
| php_10_9 | 3.90 | 28 MB | 0.63 | **0.28** | 0.55 |
| php_11_10 | 55.45 | 315 MB | 4.99 | **1.66** | 5.38 |
| cec_adder_8b_rc_vs_ks | 0.00 | 7.7 KB | 0.05 | 0.05 | 0.01 |
| cec_adder_16b_rc_vs_ks | 0.00 | 26 KB | 0.06 | 0.05 | 0.03 |
| cec_adder_32b_rc_vs_ks | 0.02 | 154 KB | 0.06 | 0.06 | 0.02 |
| cec_adder_64b_rc_vs_ks | 0.07 | 603 KB | 0.08 | 0.08 | 0.13 |
| cec_mult_5x5_arr_vs_wal | 0.02 | 259 KB | 0.06 | 0.06 | 0.01 |
| cec_mult_6x6_arr_vs_wal | 0.14 | 1.6 MB | 0.13 | 0.10 | 0.04 |
| cec_mult_8x8_arr_vs_wal | 6.57 | 47 MB | 1.13 | **0.50** | 0.68 |
| mult_target_28b_unsat | 0.00 | 25 KB | 0.05 | 0.05 | 0.04 |
| chessboard_6x6_unsat | 0.00 | 1.8 KB | 0.05 | 0.05 | 0.05 |
| chessboard_8x8_unsat | 0.00 | 25 KB | 0.05 | 0.05 | 0.01 |
| chessboard_10x10_unsat | 0.08 | 664 KB | 0.09 | 0.08 | 0.02 |
| ham_bipartite_7_8 | 0.23 | 2.5 MB | 0.18 | 0.13 | 0.06 |
| ham_bipartite_10_11 | 6.44 | 61 MB | 1.00 | 0.41 | **0.28** |
| ham_bipartite_14_15 | 10.65 | 121 MB | 1.39 | **0.69** | 1.27 |
| ham_cutvertex_15 | 0.15 | 1.4 MB | 0.14 | 0.12 | 0.01 |
| ham_cutvertex_23 | 6.87 | 72 MB | 1.04 | **0.45** | 1.38 |
| random3sat_n300_s1 (Tier 3) | 38.27 | 130 MB | 2.39 | **0.81** | 4.75 |
| random3sat_n300_s5 (Tier 3) | 41.71 | 142 MB | 2.59 | **0.90** | 3.92 |

Raw output: [proofs-checked.tsv](proofs-checked.tsv).

## What this shows

- **Two independent checkers agree on every proof.** Both accepted all 26 proofs and both rejected all 8 broken ones below. They are separate code bases in different languages, written by different people.
- **Checking is far cheaper than solving.** The two Tier 3 proofs took CaDiCaL about 40 s each to produce. tenet-sat checked each in under a second, and lrat-trim in 4 to 5 s. A solver that answers the open Tier 3 instances can be checked the same day.
- **On large proofs tenet-sat is faster; on small ones lrat-trim is.** Above 100 MB, tenet-sat at 8 threads was 1.8 to 5.9 times faster than lrat-trim: 4.4 to 5.9 times on the Tier 3 proofs and 3.2 times on the 315 MB pigeonhole proof. Below about 3 MB, lrat-trim finishes in hundredths of a second, before .NET has started. tenet-sat on one thread is roughly as fast as lrat-trim, and faster on the Tier 3 proofs. That matches tenet-sat's own finding that its speed comes from using more cores. The 8-core laptop here is a small test of that. Its published numbers use a 192-core machine and proofs of several gigabytes.
- lrat-trim's default mode also trims the proof, which is extra work tenet-sat does not do. These timings compare each tool as it is normally run.

## Negative controls

A checker that accepts everything would also print "verified", so we gave both checkers eight proofs that must fail. Both rejected all eight:

| broken input | tenet-sat | lrat-trim |
|---|---|---|
| Tier 3 proof checked against the other Tier 3 formula | NOT VERIFIED | rejected: antecedent does not produce a unit |
| pigeonhole 9/8 proof, formula with one clause removed | NOT VERIFIED | rejected: antecedent is not an original or added clause |
| the same proof cut short, never reaching the empty clause | NOT VERIFIED | rejected: unexpected end of file |
| five copies, each with one random bit flipped | NOT VERIFIED (5 of 5) | rejected (5 of 5): three parse errors, two failed unit checks |

## Not committed

The proofs total about 1 GB, so they are not in the repository. The script regenerates them.
