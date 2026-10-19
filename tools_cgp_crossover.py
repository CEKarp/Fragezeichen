"""CGP mit Crossover: klassische Konfiguration (POP=50, uniform, neutral)."""
import random
from tools_cgp_smart import (
    N_NODES, GENOME_BITS, fitness_for
)

def crossover(ga, gb, rng, per_node=True):
    """Uniform Crossover: jeder Knoten (10 Bit) zufällig von A oder B."""
    c = 0
    for i in range(N_NODES):
        src = ga if rng.random() < 0.5 else gb
        c |= ((src >> (10*i)) & 0x3FF) << (10*i)
    return c

def mutate(g, rng, nbits):
    c = g
    for _ in range(nbits):
        c ^= 1 << rng.randrange(GENOME_BITS)
    return c

def evolve_for(fn, pop, rng, gens, target=1.0, lam=4, cx_rate=0.3):
    """(μ+λ) mit Crossover und neutraler Drift."""
    best_fit = max(fn(g) for g in pop)
    mutation_bits = 2
    stagnation = 0
    gens_used = 0
    mu = len(pop)

    for gen in range(gens):
        if best_fit >= target:
            break

        children = []
        # 1) Mutation: jedes Eltern erzeugt lam Kinder
        for parent in pop:
            pfit = fn(parent)
            for _ in range(lam):
                child = mutate(parent, rng, mutation_bits)
                cfit = fn(child)
                if cfit >= pfit:  # neutrale Drift
                    children.append((cfit, child))
        # 2) Crossover: μ/2 zufällige Paare erzeugen je 2 Kinder
        for _ in range(mu // 2):
            pa, pb = rng.sample(pop, 2)
            for _ in range(2):
                child = crossover(pa, pb, rng)
                if rng.random() < 0.5:
                    child = mutate(child, rng, mutation_bits)
                children.append((fn(child), child))

        # Selektion: beste μ, mit Diversitäts-Filter
        children.sort(key=lambda t: t[0], reverse=True)
        new_pop = []
        for fit, child in children:
            if all(bin(child ^ e).count("1") > 3 for e in new_pop):
                new_pop.append(child)
                if len(new_pop) >= mu:
                    break
        if len(new_pop) < mu:
            new_pop.extend([g for _, g in sorted(
                [(fn(g), g) for g in pop], reverse=True
            )][:mu - len(new_pop)])
        pop = new_pop

        new_best = max(fn(g) for g in pop)
        if new_best > best_fit:
            best_fit = new_best
            stagnation = 0
            mutation_bits = max(1, mutation_bits - 1)
        else:
            stagnation += 1
            if stagnation > 15:
                mutation_bits = min(6, mutation_bits + 1)
                stagnation = 0
        gens_used = gen + 1

    return best_fit, gens_used, pop

def main():
    rng = random.Random(42)
    POP = 50

    print("=== Crossover: POP=50, uniform, neutrale Drift ===")
    pop = [rng.getrandbits(GENOME_BITS) for _ in range(POP)]

    # Curriculum mit Elite-Transfer: 1->2->3->4 Bit
    for nbits in [1, 2, 3, 4]:
        fn = lambda g, n=nbits: fitness_for(g, n)
        best, gens, pop = evolve_for(fn, pop, rng, gens=300)
        # Elite auffüllen wenn Population nach Selektion zu klein
        while len(pop) < POP:
            pop.append(rng.getrandbits(GENOME_BITS))
        print(f"Bits={nbits}  fit={best:.4f}  (Gen: {gens})")

if __name__ == "__main__":
    main()
