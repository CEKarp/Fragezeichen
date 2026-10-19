"""CGP mit adaptiver Mutation, neutraler Drift und Diversitäts-Erhalt."""
import random

N_NODES = 18
GENOME_BITS = 10 * N_NODES
M = (1 << 64) - 1

IN = [sum(((i >> (3+j)) & 1) << i for i in range(64)) for j in range(3)] + \
     [sum(((i >> j) & 1) << i for i in range(64)) for j in range(3)]

def fn_op(fn, a, b):
    if fn == 0: return a & b
    if fn == 1: return a | b
    if fn == 2: return a ^ b
    return ~(a & b) & M

def eval_genome(g):
    s = IN[:]
    for i in range(N_NODES):
        fn = (g >> (10*i)) & 3
        x  = (g >> (10*i + 2)) & 15
        y  = (g >> (10*i + 6)) & 15
        a = s[x] if x < 6 + i else 0
        b = s[y] if y < 6 + i else 0
        s.append(fn_op(fn, a, b))
    return s[14], s[15], s[16], s[17]

def fitness_for(g, nbits):
    outs = eval_genome(g)
    total, count = 0.0, 0
    for bp in range(nbits):
        tgt = sum((((idx >> 3) + (idx & 7)) >> bp & 1) << idx for idx in range(64))
        pred = outs[bp]
        ones = bin(tgt).count("1")
        zeros = 64 - ones
        if ones == 0 or zeros == 0:
            continue
        tp = bin(pred & tgt).count("1")
        tn = bin((~pred) & (~tgt) & M).count("1")
        total += (tp / ones + tn / zeros) / 2
        count += 1
    return total / count if count > 0 else 0.0

def mutate(g, rng, nbits):
    c = g
    for _ in range(nbits):
        c ^= 1 << rng.randrange(GENOME_BITS)
    return c

def hamming(g1, g2):
    return bin(g1 ^ g2).count("1")

def evolve_for(fn, pop, rng, gens, target=1.0, lam=6):
    """Adaptive (1+λ) mit neutraler Drift und Diversitäts-Erhalt."""
    best_fit = max(fn(g) for g in pop)
    mutation_bits = 3        # startet breit
    stagnation = 0
    history = []

    for gen in range(gens):
        if best_fit >= target:
            break
        # Jedes Elternteil erzeugt λ Kinder
        children = []
        for parent in pop:
            parent_fit = fn(parent)
            for _ in range(lam):
                child = mutate(parent, rng, mutation_bits)
                child_fit = fn(child)
                # Neutrale Drift: Kind akzeptiert wenn >= Elternteil
                if child_fit >= parent_fit:
                    children.append((child_fit, child, parent))
        # Sortiere nach Fitness, dann nach Diversität
        children.sort(key=lambda t: t[0], reverse=True)
        # Nimm beste, aber nur wenn divers genug
        new_pop = []
        for fit, child, parent in children:
            if all(hamming(child, existing) > 2 for existing in new_pop):
                new_pop.append(child)
                if len(new_pop) >= len(pop):
                    break
        # Fallback: Elite behalten
        if len(new_pop) < len(pop):
            new_pop.extend([best for _, best in sorted(
                [(fn(g), g) for g in pop], reverse=True
            )][:len(pop) - len(new_pop)])
        pop = new_pop

        # Adaptiv: stagniert seit 10 Gen?
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
        history.append(best_fit)
    return best_fit, history, pop

def main():
    rng = random.Random(42)
    POP = 20

    # Curriculum: 1 Bit, dann 2, 3, 4 — jeweils mit Elite-Transfer
    pop = [rng.getrandbits(GENOME_BITS) for _ in range(POP)]
    for nbits in [1, 2, 3, 4]:
        fn = lambda g, n=nbits: fitness_for(g, n)
        best, hist, pop = evolve_for(fn, pop, rng, gens=100)
        print(f"Bits={nbits}  fit={best:.4f}  (Gen bis Konvergenz: {len(hist)})")

if __name__ == "__main__":
    main()
