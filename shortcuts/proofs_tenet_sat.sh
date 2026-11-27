#!/bin/zsh
# Write a binary LRAT proof with CaDiCaL for every unsatisfiable instance it can finish, then check each
# proof with tenet-sat (https://github.com/keithadler/tenet-sat) at 1 and 8 threads.
# Usage: shortcuts/proofs_tenet_sat.sh PROOF_DIR TENETSAT_DLL
# Needs cadical and the .NET 10 runtime (on Homebrew: export DOTNET_ROOT=/opt/homebrew/opt/dotnet/libexec).
OUT=${1:?proof dir}; T=${2:?path to tenetsat.dll}; mkdir -p $OUT
R=${0:A:h}/../instances
list=(
 tier1/tseitin_n20_unsat tier1/tseitin_n30_unsat tier1/tseitin_n40_unsat tier1/tseitin_n60_unsat
 tier1/php_8_7 tier1/php_9_8 tier1/php_10_9 tier1/php_11_10
 tier1/cec_adder_8b_rc_vs_ks tier1/cec_adder_16b_rc_vs_ks tier1/cec_adder_32b_rc_vs_ks tier1/cec_adder_64b_rc_vs_ks
 tier1/cec_mult_5x5_arr_vs_wal tier1/cec_mult_6x6_arr_vs_wal tier1/cec_mult_8x8_arr_vs_wal
 tier1/mult_target_28b_unsat
 tier1/chessboard_6x6_unsat tier1/chessboard_8x8_unsat tier1/chessboard_10x10_unsat
 tier1/ham_bipartite_7_8 tier1/ham_bipartite_10_11 tier1/ham_bipartite_14_15
 tier1/ham_cutvertex_15 tier1/ham_cutvertex_23
 tier3/random3sat_n300_s1 tier3/random3sat_n300_s5
)
printf 'instance\tcadical_cpu_s\tproof_bytes\ttenet_sat_1_thread\twall_s\ttenet_sat_8_threads\twall_s\n'
for f in $list; do
  n=${f:t}
  s=$( { /usr/bin/time -p cadical -q -t 600 --lrat $R/$f.cnf $OUT/$n.lrat > $OUT/$n.out; } 2>&1 | awk '/^user/{print $2}')
  row="$n\t$s\t$(stat -f %z $OUT/$n.lrat 2>/dev/null || stat -c %s $OUT/$n.lrat)"
  for th in 1 8; do
    o=$( { /usr/bin/time -p dotnet $T check $R/$f.cnf $OUT/$n.lrat --threads $th; } 2>&1 )
    row="$row\t$(print -r -- "$o" | grep -E '^s ' | head -1)\t$(print -r -- "$o" | awk '/^real/{print $2}')"
  done
  print -r -- "$row"
done
