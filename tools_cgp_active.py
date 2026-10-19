"""Aktive-Knoten-Mutation: nur relevante Knoten mutieren."""
import random
from tools_cgp_smart import (
    N_NODES, GENOME_BITS, fitness_for, eval_genome
)

def active_nodes(g, out_indices):
    """Backward slice: welche Knoten tragen zu out_indices bei?"""
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
        # Selektoren zeigen auf Quellen: 0-5 = Eingaben, 6+i = ki
        if x >= 6:
            stack.append(x - 6)
        if y >= 6:
            stack.append(y - 6)
    return active

def active_bit_mask(g, out_indices):
    """Bitmaske über GENOME_BITS: 1 = mutierbar, 0 = neutral."""
    active = active_nodes(g, out_indices)
    mask = 0
    for i in active:
        mask |= 0x3FF << (10 * i)  # 10 Bit pro Knoten
    return mask

def mutate_active(g, rng, nbits, out_indices):
    c = g
    mask = active_bit_mask(g, out_indices)
    if mask == 0:
        return mutate_active(g, rng, nbits, out_indices)
    for _ in range(nbits):
        # Zufälliges Bit innerhalb der aktiven Maske
        while True:
            pos = rng.randrange(GENOME_BITS)
            if mask & (1 << pos):
                c ^= 1 << pos
                break
    return c

# Import von mutate aus smart nachbauen
def mutate_uniform(g, rng, nbits):
    c = g
    for _ in range(nbits):
        c ^= 1 << rng.randrange(GENOME_BITS)
    return c

def evolve_for(fn, pop, rng, gens, out_indices, target=1.0, lam=6,
               active=True):
    mutate = (lambda g, r: mutate_active(g, r, 3, out_indices)) if active \
             else (lambda g, r: mutate_uniform(g, r, 3))
    best_fit = max(fn(g) for g in pop)
    mutation_bits = 3
    stagnation = 0
    gens_used = 0

    for gen in range(gens):
        if best_fit >= target:
            break
        children = []
        for parent in pop:
            parent_fit = fn(parent)
            for _ in range(lam):
                child = mutate(parent, rng)
                child_fit = fn(child)
                if child_fit >= parent_fit:
                    children.append((child_fit, child))
        children.sort(key=lambda t: t[0], reverse=True)
        new_pop = []
        for fit, child in children:
            if all(bin(child ^ e).count("1") > 2 for e in new_pop):
                new_pop.append(child)
                if len(new_pop) >= len(pop):
                    break
        if len(new_pop) < len(pop):
            new_pop.extend([g for _, g in sorted(
                [(fn(g), g) for g in pop], reverse=True
            )][:len(pop) - len(new_pop)])
        pop = new_pop

        new_best = max(fn(g) for g in pop)
        if new_best > best_fit:
            best_fit = new_best
            stagnation = 0
            mutation_bits = max(1, mutation_bits - 1)
        else:
            stagnation += 1
            if stagnation > 10:
                mutation_bits = min(8, mutation_bits + 2)
                stagnation = 0
        gens_used = gen + 1
    return best_fit, gens_used, pop

def main():
    rng = random.Random(42)
    POP = 20
    pop = [rng.getrandbits(GENOME_BITS) for _ in range(POP)]

    # Out-Indices: s[-4..-1] = 14, 15, 16, 17
    out_all = [14, 15, 16, 17]

    print("=== Aktive-Knoten-Mutation ===")
    for nbits in [1, 2, 3, 4]:
        out_idx = out_all[:nbits] if nbits <= 3 else [14, 15, 16, 17]
        # Bei nbits<4 nutzen wir nur die relevanten Outputs
        if nbits == 1: out_idx = [14]
        elif nbits == 2: out_idx = [14, 15]
        elif nbits == 3: out_idx = [14, 15, 16]
        else: out_idx = [14, 15, 16, 17]
        fn = lambda g, n=nbits: fitness_for(g, n)
        best, gens, pop = evolve_for(fn, pop, rng, gens=200,
                                     out_indices=out_idx, active=True)
        print(f"Bits={nbits}  fit={best:.4f}  (Gen: {gens})")

if __name__ == "__main__":
    main()
