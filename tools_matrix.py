"""tools_matrix.py — Parameter-Raster mit Train/Test-Split."""
import csv
import itertools
import random
import sys
from pathlib import Path
from tools_cgp_curriculum import GENOME_BITS
from tools_tasks import (split_pairs, fitness_for_task_masked)

TASKS = ["ne3", "gt2", "gt3", "add2", "add3", "add4"]

def mutate(g, rng, nbits=3):
    c = g
    for _ in range(nbits):
        c ^= 1 << rng.randrange(GENOME_BITS)
    return c

def run_random(fn_train, budget, rng):
    best = 0.0
    best_g = 0
    for _ in range(budget):
        g = rng.getrandbits(GENOME_BITS)
        f = fn_train(g)
        if f > best:
            best, best_g = f, g
    return best, best_g, budget, 0

def run_ga(fn_train, budget, pop_size, rng):
    pop = [rng.getrandbits(GENOME_BITS) for _ in range(pop_size)]
    best_g = max(pop, key=fn_train)
    best = fn_train(best_g)
    evals = pop_size
    gens = 0
    while evals < budget and best < 0.999:
        scored = sorted(((fn_train(g), g) for g in pop), reverse=True)
        evals += pop_size
        gens += 1
        if scored[0][0] > best:
            best, best_g = scored[0]
        n_elite = max(2, pop_size // 4)
        elite = [g for _, g in scored[:n_elite]]
        pop = elite + [mutate(rng.choice(elite), rng, 3)
                       for _ in range(pop_size - n_elite)]
    return best, best_g, gens, evals

def main():
    budget = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
    pop_size = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    n_seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    train_mask, test_mask = split_pairs(seed=42, n_train=48)
    n_train = bin(train_mask).count("1")
    n_test = bin(test_mask).count("1")
    print(f"Split: {n_train} Train / {n_test} Test (Seed 42)")
    print()

    rows = []
    total = len(TASKS) * 2 * n_seeds
    done = 0

    for task, strategy in itertools.product(TASKS, ["random", "ga"]):
        fn_train = lambda g, t=task: fitness_for_task_masked(g, t, train_mask)
        for seed in range(1, n_seeds + 1):
            rng = random.Random(f"{task}-{strategy}-{seed}")
            if strategy == "random":
                train_f, best_g, evals, gens = run_random(fn_train, budget, rng)
            else:
                train_f, best_g, gens, evals = run_ga(fn_train, budget, pop_size, rng)
            test_f = fitness_for_task_masked(best_g, task, test_mask)
            gap = train_f - test_f
            solved = int(test_f >= 0.999)  # NUR Test zaehlt als geloest

            rows.append({
                "task": task, "strategy": strategy, "seed": seed,
                "train": round(train_f, 4),
                "test": round(test_f, 4),
                "gap": round(gap, 4),
                "solved": solved,
                "gens": gens,
            })
            done += 1
            print(f"[{done}/{total}] {task:<6} {strategy:<7} seed={seed} "
                  f"train={train_f:.4f} test={test_f:.4f} gap={gap:+.4f}",
                  file=sys.stderr)

    out = Path(f"matrix_split_{budget}_{pop_size}.csv")
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["task","strategy","seed",
                                          "train","test","gap","solved","gens"])
        w.writeheader()
        w.writerows(rows)
    print(f"\ngeschrieben: {out} ({len(rows)} Zeilen)")

    # Zusammenfassung
    print()
    print(f"{'Task':<6} {'Zufall test':<18} {'GA test':<18} {'GA gap':<10} {'GA solved':<10}")
    print(f"{'':<6} {'Median  Max':<18} {'Median  Max':<18} {'Median':<10} {'':<10}")
    print("-" * 70)
    for task in TASKS:
        cells = {}
        for strategy in ["random", "ga"]:
            subset = [r for r in rows if r["task"]==task and r["strategy"]==strategy]
            tests = sorted(r["test"] for r in subset)
            gaps = sorted(r["gap"] for r in subset)
            solved = sum(r["solved"] for r in subset)
            cells[strategy] = (tests[len(tests)//2], tests[-1],
                              gaps[len(gaps)//2], solved)
        r_med, r_max, _, _ = cells["random"]
        g_med, g_max, g_gap, g_sol = cells["ga"]
        print(f"{task:<6} {r_med:.4f}  {r_max:.4f}      "
              f"{g_med:.4f}  {g_max:.4f}      {g_gap:+.4f}   {g_sol}/{n_seeds}")

if __name__ == "__main__":
    main()
