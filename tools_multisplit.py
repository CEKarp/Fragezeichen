"""tools_multisplit.py — mehrere Train/Test-Splits, gepoolte Erfolgsraten."""
import random
import sys
from math import sqrt
from multiprocessing import Pool
from tools_selfadapt import CGP, search
from tools_tasks import split_pairs


def one(args):
    task, budget, n_nodes, seed, split_seed = args
    tr, te = split_pairs(seed=split_seed, n_train=48)
    ctr = CGP(task, n_nodes, tr)
    cte = CGP(task, n_nodes, te)
    g, _ = search(ctr, random.Random(f"{task}-ms-{split_seed}-{seed}"), budget)
    return split_seed, ctr.acc(g), cte.acc(g)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    c = (p + z * z / (2 * n)) / denom
    m = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, c - m), min(1.0, c + m)


def main():
    task = sys.argv[1] if len(sys.argv) > 1 else "add4"
    budget = int(sys.argv[2]) if len(sys.argv) > 2 else 1_000_000
    seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 32
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 30
    split_seeds = [int(x) for x in
                   (sys.argv[5].split(",") if len(sys.argv) > 5 else ["42", "43", "44"])]

    jobs = [(task, budget, n, s, sp)
            for sp in split_seeds for s in range(seeds)]
    with Pool() as p:
        res = p.map(one, jobs)

    print(f"Task={task}, Knoten={n}, Budget={budget}, "
          f"Seeds/Split={seeds}, Splits={split_seeds}, Kerne={len(set()) or 'auto'}")
    print()
    print(f"{'Split':>6} {'geloest':>12} {'Rate':>8} {'95%-KI':>22} {'test_med':>10}")
    print("-" * 64)

    total_solved = 0
    all_tests = []
    for sp in split_seeds:
        sub = [r for r in res if r[0] == sp]
        sol = sum(1 for r in sub if r[2] >= 0.999)
        tes = sorted(r[2] for r in sub)
        med = tes[len(tes) // 2]
        lo, hi = wilson(sol, len(sub))
        print(f"{sp:>6} {sol:>9}/{len(sub):<3} {sol/len(sub):>7.1%}  "
              f"[{lo:.1%}, {hi:.1%}]       {med:>8.4f}")
        total_solved += sol
        all_tests.extend(tes)

    n_total = len(res)
    lo, hi = wilson(total_solved, n_total)
    print("-" * 64)
    print(f"{'pooled':>6} {total_solved:>9}/{n_total:<3} "
          f"{total_solved/n_total:>7.1%}  [{lo:.1%}, {hi:.1%}]")


if __name__ == "__main__":
    main()
