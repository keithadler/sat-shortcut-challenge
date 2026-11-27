"""Check a Tier 4 answer: decode the message bits from a solver's model, hash them, compare with the digest.
Usage: python tier4_check.py INSTANCE_NAME SOLVER_OUTPUT   (DIMACS 'v' lines, or one integer literal per token)"""
import sys, tier4
name, path = sys.argv[1].split('/')[-1].replace('.cnf.xz', '').replace('.cnf', ''), sys.argv[2]
toks = [t for line in open(path) if line.startswith('v') or line[:1].lstrip('-').isdigit()
        for t in line.split() if t.lstrip('-').isdigit()]
model = {int(t) for t in toks if int(t) > 0}
ok = tier4.check(name, model)
print(f"{name}: {'VERIFIED: the decoded message hashes to the given digest' if ok else 'FAILED'}")
sys.exit(0 if ok else 1)
