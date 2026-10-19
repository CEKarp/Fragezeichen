"""tools_matrix.py — Parameter-Raster, echte Aufgaben, Ergebnisse als CSV."""
import csv
import itertools
import random
import sys
from pathlib import Path
from tools_cgp_curriculum import GENOME_BITS
from tools_tasks import fitness_for_task

TASKS = ["ne3", "gt2", "gt3", "add2", "add3", "add4"]

def mutate(g, rng, nbits=3):
    c = g
    for _ in range(nbits):
        c ^= 1 << rng.randrange(GENOME_BITS)
    return c

def run_random(fn, budget, rng):
    best = 0.0
    for _ in range(budget):
        g = rng.getrandbits(GENOME_BITS)
        f = fn(g)
        if f > best:
            best = f
    return best, budget

def run_ga(fn, budget, pop_size, rng):
    pop = [rng.getrandbits(GENOME_BITS) for _ in range(pop_size)]
    best = max(fn(g) for g in pop)
    evals = pop_size
    gens = 0
    while evals < budget and best < 0.999:
        scored = sorted(((fn(g), g) for g in pop), reverse=True)
        evals += pop_size
        gens += 1
        if scored[0][0] > best:
            best = scored[0][0]
        n_elite = max(2, pop_size // 4)
        elite = [g for _, g in scored[:n_elite]]
        pop = elite + [mutate(rng.choice(elite), rng, 3)
                       for _ in range(pop_size - n_elite)]
    return best, gens

def main():
    budget = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
    pop_size = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    n_seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    rows = []
    total = len(TASKS) * 2 * n_seeds
    done = 0
    for task, strategy in itertools.product(TASKS, ["random", "ga"]):
        fn = lambda g, t=task: fitness_for_task(g, t)
        for seed in range(1, n_seeds + 1):
            rng = random.Random(f"{task}-{strategy}-{seed}")
            if strategy == "random":
                fit, gens = run_random(fn, budget, rng)
            else:
                fit, gens = run_ga(fn, budget, pop_size, rng)
            rows.append({
                "task": task, "strategy": strategy, "seed": seed,
                "fitness": round(fit, 4),
                "solved": int(fit >= 0.999),
                "gens": gens,
            })
            done += 1
            print(f"[{done}/{total}] {task:<6} {strategy:<7} seed={seed} fit={fit:.4f}",
                  file=sys.stderr)

    out = Path(f"matrix_{budget}_{pop_size}.csv")
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["task","strategy","seed","fitness","solved","gens"])
        w.writeheader()
        w.writerows(rows)
    print(f"\ngeschrieben: {out} ({len(rows)} Zeilen)")

    print()
    print(f"{'Task':<6} {'Zufall':<20} {'GA':<20}")
    print(f"{'':<6} {'Median  Max   Solved':<20} {'Median  Max   Solved':<20}")
    print("-" * 52)
    for task in TASKS:
        cells = {}
        for strategy in ["random", "ga"]:
            fits = sorted(r["fitness"] for r in rows
                          if r["task"]==task and r["strategy"]==strategy)
            solved = sum(r["solved"] for r in rows
                         if r["task"]==task and r["strategy"]==strategy)
            cells[strategy] = (fits[len(fits)//2], fits[-1], solved)
        r_med, r_max, r_sol = cells["random"]
        g_med, g_max, g_sol = cells["ga"]
        print(f"{task:<6} {r_med:.4f}  {r_max:.4f}  {r_sol}/{n_seeds}      "
              f"{g_med:.4f}  {g_max:.4f}  {g_sol}/{n_seeds}")

if __name__ == "__main__":
    main()
