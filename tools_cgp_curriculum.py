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
    return s[-4], s[-3], s[-2], s[-1]

def fitness_for(g, nbits):
    outs = eval_genome(g)
    mask = (1 << 64) - 1  # alle 64 Paare
    total, count = 0.0, 0
    for bp in range(nbits):
        tgt = 0
        for idx in range(64):
            a, b = idx >> 3, idx & 7
            tgt |= (((a + b) >> bp) & 1) << idx
        pred = outs[bp]
        ones = bin(tgt).count("1")
        zeros = 64 - ones
        if ones == 0 or zeros == 0:
            continue
        tp = bin(pred & tgt).count("1")
        tn = bin((~pred) & (~tgt) & mask).count("1")
        total += (tp / ones + tn / zeros) / 2
        count += 1
    return total / count if count > 0 else 0.0

def mutate(g, rng):
    c = g
    for _ in range(rng.randint(1, 3)):
        c ^= 1 << rng.randrange(GENOME_BITS)
    return c

def main():
    POP, GENS = 20, 30
    rng = random.Random(42)
    pop = [rng.getrandbits(GENOME_BITS) for _ in range(POP)]
    for nbits in [1, 2, 3, 4]:
        best = 0.0
        for _ in range(GENS):
            scored = sorted(((fitness_for(g, nbits), g) for g in pop), reverse=True)
            if scored[0][0] > best: best = scored[0][0]
            elite = [g for _, g in scored[:5]]
            pop = elite + [mutate(rng.choice(elite), rng) for _ in range(POP - 5)]
        print(f"Bits={nbits}  fit={best:.4f}")

if __name__ == "__main__":
    main()
