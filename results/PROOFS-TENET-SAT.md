# Unsatisfiability proofs, checked by tenet-sat

The challenge asks for a checked proof behind every "no solution" answer. This file shows that pipeline working on our own instances. CaDiCaL writes a proof for every unsatisfiable instance it can finish, and [tenet-sat](https://github.com/keithadler/tenet-sat), a parallel LRAT proof checker, checks it.

Run on 27 November 2026 on an 8-core Apple M3 laptop, using CaDiCaL 3.1.0 (`--lrat`, binary LRAT) and tenet-sat at commit `e506303` on .NET 10.0.401. Times are wall-clock seconds and include starting the .NET process, which is about 0.05 s. Script: [`shortcuts/proofs_tenet_sat.sh`](../shortcuts/proofs_tenet_sat.sh).

**All 26 proofs verified**, at 1 thread and at 8 threads. They cover 24 Tier 1 instances and the 2 Tier 3 instances Kissat solved as unsatisfiable. The other unsatisfiable instances (Tseitin n100 and n200, pigeonhole 13/12, chessboard 14x14, 10x10 multiplier) are ones the standard solvers did not finish, so there is no proof to check yet.

| instance | CaDiCaL CPU s | proof size | tenet-sat, 1 thread | tenet-sat, 8 threads |
|---|---:|---:|---:|---:|
| tseitin_n20_unsat | 0.00 | 2.5 KB | 0.05 | 0.05 |
| tseitin_n30_unsat | 0.00 | 33 KB | 0.06 | 0.05 |
| tseitin_n40_unsat | 0.01 | 165 KB | 0.06 | 0.06 |
| tseitin_n60_unsat | 0.21 | 2.2 MB | 0.12 | 0.09 |
| php_8_7 | 0.03 | 312 KB | 0.07 | 0.06 |
| php_9_8 | 0.29 | 2.8 MB | 0.23 | 0.14 |
| php_10_9 | 3.90 | 28 MB | 0.63 | 0.28 |
| php_11_10 | 55.45 | 315 MB | 4.99 | **1.66** |
| cec_adder_8b_rc_vs_ks | 0.00 | 7.7 KB | 0.05 | 0.05 |
| cec_adder_16b_rc_vs_ks | 0.00 | 26 KB | 0.06 | 0.05 |
| cec_adder_32b_rc_vs_ks | 0.02 | 154 KB | 0.06 | 0.06 |
| cec_adder_64b_rc_vs_ks | 0.07 | 603 KB | 0.08 | 0.08 |
| cec_mult_5x5_arr_vs_wal | 0.02 | 259 KB | 0.06 | 0.06 |
| cec_mult_6x6_arr_vs_wal | 0.14 | 1.6 MB | 0.13 | 0.10 |
| cec_mult_8x8_arr_vs_wal | 6.57 | 47 MB | 1.13 | 0.50 |
| mult_target_28b_unsat | 0.00 | 25 KB | 0.05 | 0.05 |
| chessboard_6x6_unsat | 0.00 | 1.8 KB | 0.05 | 0.05 |
| chessboard_8x8_unsat | 0.00 | 25 KB | 0.05 | 0.05 |
| chessboard_10x10_unsat | 0.08 | 664 KB | 0.09 | 0.08 |
| ham_bipartite_7_8 | 0.23 | 2.5 MB | 0.18 | 0.13 |
| ham_bipartite_10_11 | 6.44 | 61 MB | 1.00 | 0.41 |
| ham_bipartite_14_15 | 10.65 | 121 MB | 1.39 | 0.69 |
| ham_cutvertex_15 | 0.15 | 1.4 MB | 0.14 | 0.12 |
| ham_cutvertex_23 | 6.87 | 72 MB | 1.04 | 0.45 |
| random3sat_n300_s1 (Tier 3) | 38.27 | 130 MB | 2.39 | **0.81** |
| random3sat_n300_s5 (Tier 3) | 41.71 | 142 MB | 2.59 | **0.90** |

Raw output: [proofs-tenet-sat.tsv](proofs-tenet-sat.tsv).

## What this shows

- **Checking is far cheaper than solving.** The two Tier 3 proofs took CaDiCaL about 40 s each to produce and tenet-sat under a second to check. A solver that answers the open Tier 3 instances can be checked the same day.
- **Threads help once proofs reach tens of megabytes.** At 8 threads, checking was 2 to 3 times faster than at 1 thread on the proofs over 25 MB. Below that, process start-up dominates.

## Negative controls

A checker that accepts everything would also print "verified", so we gave tenet-sat eight proofs that must fail. It rejected all eight:

- a Tier 3 proof checked against the other Tier 3 formula;
- the pigeonhole 9/8 proof checked against the formula with one clause removed;
- the same proof cut short, so it never reaches the empty clause;
- five copies of the same proof, each with one bit flipped at a random position.

## Not done

- **No second checker.** We meant to run lrat-trim alongside tenet-sat as a reference, but building it was not cleared in this session. tenet-sat's own testing compares it against lrat-check, lrat-trim and cake_lpr on 77 real proofs and 1,600 corrupted ones (see its repository). Anyone submitting results may use any of these checkers.
- Proofs are not committed; they total about 1 GB. The script regenerates them.
