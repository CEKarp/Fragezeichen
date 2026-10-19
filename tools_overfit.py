"""tools_overfit.py — Overfitting-Test: Train auf 48 Paaren, Test auf 16."""
import random
import sys
from tools_cgp_curriculum import GENOME_BITS
from tools_tasks import (split_pairs, fitness_for_task_masked,
                         fitness_for_task)

TASKS = ["gt3", "add2", "add3", "add4"]

def mutate(g, rng, nbits=3):
    c = g
    for _ in range(nbits):
        c ^= 1 << rng.randrange(GENOME_BITS)
    return c

def run_ga(fn, budget, pop_size, rng):
    pop = [rng.getrandbits(GENOME_BITS) for _ in range(pop_size)]
    best_g = max(pop, key=fn)
    best_f = fn(best_g)
    evals = pop_size
    while evals < budget and best_f < 0.999:
        scored = sorted(((fn(g), g) for g in pop), reverse=True)
        evals += pop_size
        if scored[0][0] > best_f:
            best_f, best_g = scored[0]
        n_elite = max(2, pop_size // 4)
        elite = [g for _, g in scored[:n_elite]]
        pop = elite + [mutate(rng.choice(elite), rng, 3)
                       for _ in range(pop_size - n_elite)]
    return best_g, best_f

def main():
    budget = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
    pop_size = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    n_seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    train_mask, test_mask = split_pairs(seed=42, n_train=48)
    print(f"Train-Paare: {bin(train_mask).count('1')}, Test-Paare: {bin(test_mask).count('1')}")
    print()
    print(f"{'Task':<6} {'Seed':<5} {'Train':<8} {'Test':<8} {'Gap':<8}")
    print("-" * 40)

    for task in TASKS:
        for seed in range(1, n_seeds + 1):
            rng = random.Random(f"{task}-{seed}")
            fn_train = lambda g, t=task: fitness_for_task_masked(g, t, train_mask)
            best_g, best_train = run_ga(fn_train, budget, pop_size, rng)
            test_fit = fitness_for_task_masked(best_g, task, test_mask)
            full_fit = fitness_for_task(best_g, task)
            gap = best_train - test_fit
            print(f"{task:<6} {seed:<5} {best_train:.4f}  {test_fit:.4f}  {gap:+.4f}   "
                  f"(full={full_fit:.4f})")

if __name__ == "__main__":
    main()
