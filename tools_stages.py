"""tools_stages.py — fair comparison of search strategies on 4-bit adder.

Stages (each with same evaluation budget):
  0a: Pure random search
  1:  GA direct (no curriculum)
  2:  GA + curriculum (1->2->3->4 bit)
  3:  GA + curriculum + random restart (more randomness)
"""
import random
import sys
from tools_cgp_curriculum import GENOME_BITS, fitness_for

def mutate(g, rng, nbits=3):
    c = g
    for _ in range(nbits):
        c ^= 1 << rng.randrange(GENOME_BITS)
    return c

def stage_random(target_bits, n_evals, rng):
    best = 0.0
    for _ in range(n_evals):
        g = rng.getrandbits(GENOME_BITS)
        f = fitness_for(g, target_bits)
        if f > best:
            best = f
    return best

def stage_ga_direct(target_bits, n_evals, pop_size, rng):
    pop = [rng.getrandbits(GENOME_BITS) for _ in range(pop_size)]
    best = max(fitness_for(g, target_bits) for g in pop)
    evals = pop_size
    while evals < n_evals and best < 1.0:
        scored = sorted(((fitness_for(g, target_bits), g) for g in pop),
                        key=lambda t: t[0], reverse=True)
        evals += pop_size
        if scored[0][0] > best:
            best = scored[0][0]
        n_elite = max(2, pop_size // 4)
        elite = [g for _, g in scored[:n_elite]]
        pop = elite + [mutate(rng.choice(elite), rng, 3)
                       for _ in range(pop_size - n_elite)]
    return best

def stage_ga_curriculum(target_bits, n_evals, pop_size, rng,
                        random_restart=False, restart_after=30,
                        restart_frac=0.5):
    pop = [rng.getrandbits(GENOME_BITS) for _ in range(pop_size)]
    evals = 0
    best_target = 0.0
    for n in range(1, target_bits + 1):
        best_this = max(fitness_for(g, n) for g in pop)
        stagnation = 0
        while evals < n_evals and best_this < 1.0:
            scored = sorted(((fitness_for(g, n), g) for g in pop),
                            key=lambda t: t[0], reverse=True)
            evals += pop_size
            if scored[0][0] > best_this:
                best_this = scored[0][0]
                stagnation = 0
            else:
                stagnation += 1
            n_elite = max(2, pop_size // 4)
            elite = [g for _, g in scored[:n_elite]]
            if random_restart and stagnation >= restart_after:
                keep = max(1, int(n_elite * (1 - restart_frac)))
                elite = elite[:keep]
                fresh = [rng.getrandbits(GENOME_BITS)
                         for _ in range(pop_size - len(elite))]
                pop = elite + fresh
                stagnation = 0
            else:
                pop = elite + [mutate(rng.choice(elite), rng, 3)
                               for _ in range(pop_size - len(elite))]
        if n == target_bits:
            best_target = best_this
    return best_target

def run_all(seeds, budget, pop_size, target_bits):
    stages = [
        ("0a: Reine Zufallssuche", lambda s: stage_random(target_bits, budget, s)),
        ("1:  GA direkt (kein Curriculum)",
            lambda s: stage_ga_direct(target_bits, budget, pop_size, s)),
        ("2:  GA + Curriculum",
            lambda s: stage_ga_curriculum(target_bits, budget, pop_size, s)),
        ("3:  GA + Curriculum + Random Restart",
            lambda s: stage_ga_curriculum(target_bits, budget, pop_size, s,
                                          random_restart=True)),
    ]
    print(f"Ziel: {target_bits}-Bit-Addierer")
    print(f"Budget: {budget} Genome-Evaluationen pro Stufe")
    print(f"Population: {pop_size}, Seeds: {len(seeds)}")
    print()
    print(f"{'Stufe':<44} {'Median':<10} {'Max':<10} {'gelöst':<10}")
    print("-" * 76)
    for name, fn in stages:
        results = [fn(random.Random(s)) for s in seeds]
        results.sort()
        median = results[len(results) // 2]
        mx = results[-1]
        solved = sum(1 for r in results if r >= 0.999)
        print(f"{name:<44} {median:<10.4f} {mx:<10.4f} {solved}/{len(seeds)}")

def main():
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    budget = int(sys.argv[2]) if len(sys.argv) > 2 else 30000
    pop_size = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    n_seeds = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    run_all(list(range(1, n_seeds + 1)), budget, pop_size, target)

if __name__ == "__main__":
    main()
