"""tools_parsimony.py — skalarer Parsimonie-Gate-Test.

fitness = acc_train - lambda * n_active_nodes
Sweep ueber lambda. Wenn kein lambda den Train/Test-Gap senkt,
ist die NSGA-II-Variante wahrscheinlich auch tot.
"""
import random
import sys
from tools_cgp_curriculum import GENOME_BITS, N_NODES
from tools_tasks import split_pairs, fitness_for_task_masked

TASKS = ["add2", "add3"]
LAMBDAS = [0.0, 0.001, 0.005, 0.01, 0.05]
SEEDS = 5
BUDGET = 50000
POP = 30

def active_node_count(g, out_indices):
    """Backward slice von den Outputs. Zaehlt nur gueltige Vorwaerts-Kanten."""
    nodes = [((g >> (10*i)) & 3, (g >> (10*i+2)) & 15, (g >> (10*i+6)) & 15)
             for i in range(N_NODES)]
    active = set()
    stack = list(out_indices)
    while stack:
        i = stack.pop()
        if i in active or i < 0:
            continue
        active.add(i)
        fn, x, y = nodes[i]
        if x >= 6 and x - 6 < i:
            stack.append(x - 6)
        if y >= 6 and y - 6 < i:
            stack.append(y - 6)
    return len(active)

def mutate(g, rng, nbits=3):
    c = g
    for _ in range(nbits):
        c ^= 1 << rng.randrange(GENOME_BITS)
    return c

def run_ga(fit_fn, budget, pop_size, rng):
    pop = [rng.getrandbits(GENOME_BITS) for _ in range(pop_size)]
    best_g = max(pop, key=fit_fn)
    best = fit_fn(best_g)
    evals = pop_size
    while evals < budget and best < 0.999:
        scored = sorted(((fit_fn(g), g) for g in pop), reverse=True)
        evals += pop_size
        if scored[0][0] > best:
            best, best_g = scored[0]
        n_elite = max(2, pop_size // 4)
        elite = [g for _, g in scored[:n_elite]]
        pop = elite + [mutate(rng.choice(elite), rng, 3)
                       for _ in range(pop_size - n_elite)]
    return best_g

def main():
    train_mask, test_mask = split_pairs(seed=42, n_train=48)
    out_idx = [14, 15, 16, 17]

    print(f"{'Task':<6} {'lambda':<8} {'train':<10} {'test':<10} {'gap':<10} {'nodes':<8}")
    print("-" * 60)

    for task in TASKS:
        for lam in LAMBDAS:
            tr, te, gaps, nodes = [], [], [], []
            for seed in range(1, SEEDS + 1):
                rng = random.Random(f"{task}-pars-{lam}-{seed}")
                def fit(g, t=task, l=lam):
                    acc = fitness_for_task_masked(g, t, train_mask)
                    n = active_node_count(g, out_idx)
                    return acc - l * n
                best_g = run_ga(fit, BUDGET, POP, rng)
                tr_a = fitness_for_task_masked(best_g, task, train_mask)
                te_a = fitness_for_task_masked(best_g, task, test_mask)
                tr.append(tr_a); te.append(te_a)
                gaps.append(tr_a - te_a)
                nodes.append(active_node_count(best_g, out_idx))
            med = lambda xs: sorted(xs)[len(xs)//2]
            print(f"{task:<6} {lam:<8.3f} {med(tr):<10.4f} "
                  f"{med(te):<10.4f} {med(gaps):<+10.4f} {med(nodes):<8.1f}")

if __name__ == "__main__":
    main()
