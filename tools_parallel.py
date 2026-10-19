"""tools_parallel.py — Seeds parallel auf allen Kernen."""
import os
import random
import sys
from multiprocessing import Pool
from tools_selfadapt import CGP, search
from tools_tasks import split_pairs


def one(args):
    task, budget, n_nodes, seed = args
    tr, te = split_pairs(seed=42, n_train=48)
    ctr = CGP(task, n_nodes, tr)
    cte = CGP(task, n_nodes, te)
    g, _ = search(ctr, random.Random(f"{task}-par-{seed}"), budget)
    return ctr.acc(g), cte.acc(g)


def main():
    task = sys.argv[1]
    budget = int(sys.argv[2])
    seeds = int(sys.argv[3])
    n = int(sys.argv[4])
    with Pool() as p:
        res = p.map(one, [(task, budget, n, s) for s in range(seeds)])
    med = lambda xs: sorted(xs)[len(xs) // 2]
    trs = [r[0] for r in res]
    tes = [r[1] for r in res]
    print(f"{task}, {n} Knoten, {budget} Evals, {seeds} Seeds, {os.cpu_count()} Kerne")
    print(f"train {med(trs):.4f}  test {med(tes):.4f}  "
          f"geloest(Test) {sum(t >= 0.999 for t in tes)}/{seeds}")


if __name__ == "__main__":
    main()
