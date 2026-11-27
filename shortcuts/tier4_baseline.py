"""Kissat on the Tier 4 instances: answer, CPU seconds, and a hash check of every model.
Usage: tier4_baseline.py [limit seconds] [parallel jobs]"""
import sys, os, subprocess, glob
from concurrent.futures import ThreadPoolExecutor
import tier4
LIM = int(sys.argv[1]) if len(sys.argv) > 1 else 300; JOBS = int(sys.argv[2]) if len(sys.argv) > 2 else 4
HERE = os.path.dirname(os.path.abspath(__file__))
def run(fn):
    name = os.path.basename(fn).replace('.cnf.xz', '')
    p = subprocess.Popen(['kissat', '-q', f'--time={LIM}', fn], stdout=subprocess.PIPE, text=True)
    out = p.stdout.read(); _, _, ru = os.wait4(p.pid, 0)
    if 's SATISFIABLE' in out:
        model = {int(x) for l in out.splitlines() if l.startswith('v') for x in l.split()[1:] if int(x) > 0}
        ans = 'SAT (hash verified)' if tier4.check(name, model) else 'SAT (MODEL FAILED HASH CHECK)'
    else:
        ans = 'UNSAT (impossible: planted)' if 's UNSATISFIABLE' in out else f'not solved in {LIM} s'
    return name, ans, ru.ru_utime
order = lambda f: ('free64' in f, int(f.split('_r')[1].split('_')[0]), f)
with ThreadPoolExecutor(JOBS) as ex:
    for name, ans, t in ex.map(run, sorted(glob.glob(os.path.join(HERE, '..', 'instances', 'tier4', '*.cnf.xz')), key=order)):
        print(f"{name}\t{ans}\t{t:.2f}", flush=True)
