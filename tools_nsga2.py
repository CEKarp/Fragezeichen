"""tools_nsga2.py — NSGA-II mit zwei Zielen: (train_acc, -n_active_nodes)."""
import random
import sys
from tools_cgp_curriculum import GENOME_BITS
from tools_tasks import split_pairs, fitness_for_task_masked
from tools_parsimony import active_node_count

OUT_IDX = [14, 15, 16, 17]

def fast_non_dominated_sort(fitness):
    """fitness: Liste von (f1, f2). Beide werden maximiert.
    Gibt Liste von Fronts zurueck; Front[i] = Liste von Indizes."""
    n = len(fitness)
    S = [[] for _ in range(n)]
    n_dom = [0] * n
    fronts = [[]]

    for p in range(n):
        for q in range(n):
            if p == q:
                continue
            fp, fq = fitness[p], fitness[q]
            p_dom_q = all(fp[k] >= fq[k] for k in range(2)) and any(fp[k] > fq[k] for k in range(2))
            q_dom_p = all(fq[k] >= fp[k] for k in range(2)) and any(fq[k] > fp[k] for k in range(2))
            if p_dom_q:
                S[p].append(q)
            elif q_dom_p:
                n_dom[p] += 1
        if n_dom[p] == 0:
            fronts[0].append(p)

    i = 0
    while fronts[i]:
        nxt = []
        for p in fronts[i]:
            for q in S[p]:
                n_dom[q] -= 1
                if n_dom[q] == 0:
                    nxt.append(q)
        i += 1
        fronts.append(nxt)
    return fronts[:-1]

def crowding_distance(front, fitness):
    """Standard NSGA-II crowding distance."""
    if not front:
        return {}
    d = {i: 0.0 for i in front}
    for m in range(2):
        order = sorted(front, key=lambda i: fitness[i][m])
        f_min = fitness[order[0]][m]
        f_max = fitness[order[-1]][m]
        if f_max == f_min:
            continue
        d[order[0]] = float("inf")
        d[order[-1]] = float("inf")
        for k in range(1, len(order) - 1):
            d[order[k]] += (fitness[order[k+1]][m] - fitness[order[k-1]][m]) / (f_max - f_min)
    return d

def mutate(g, rng, nbits=2):
    c = g
    for _ in range(nbits):
        c ^= 1 << rng.randrange(GENOME_BITS)
    return c

def uniform_crossover(p1, p2, rng):
    """Bitweises Uniform Crossover."""
    mask = 0
    for i in range(GENOME_BITS):
        if rng.random() < 0.5:
            mask |= 1 << i
    return (p1 & mask) | (p2 & ~mask & ((1 << GENOME_BITS) - 1))

def nsga2_run(task, train_mask, test_mask, budget, pop_size, rng,
              cx_rate=0.9, mut_rate=0.1):
    def objectives(g):
        acc = fitness_for_task_masked(g, task, train_mask)
        n = active_node_count(g, OUT_IDX)
        return (acc, -float(n))

    pop = [rng.getrandbits(GENOME_BITS) for _ in range(pop_size)]
    fitness = [objectives(g) for g in pop]
    evals = pop_size
    gen = 0

    while evals < budget:
        fronts = fast_non_dominated_sort(fitness)
        crowd = {}
        for f in fronts:
            crowd.update(crowding_distance(f, fitness))
        rank = {}
        for r, f in enumerate(fronts):
            for i in f:
                rank[i] = r

        def tournament():
            i, j = rng.sample(range(pop_size), 2)
            if rank[i] != rank[j]:
                return pop[i] if rank[i] < rank[j] else pop[j]
            return pop[i] if crowd.get(i, 0) > crowd.get(j, 0) else pop[j]

        offspring = []
        for _ in range(pop_size):
            p1, p2 = tournament(), tournament()
            if rng.random() < cx_rate:
                child = uniform_crossover(p1, p2, rng)
            else:
                child = p1
            if rng.random() < mut_rate:
                child = mutate(child, rng, rng.randint(1, 3))
            offspring.append(child)

        off_fit = [objectives(g) for g in offspring]
        evals += pop_size
        gen += 1

        combined = pop + offspring
        cfit = fitness + off_fit
        cfronts = fast_non_dominated_sort(cfit)
        ccrowd = {}
        for f in cfronts:
            ccrowd.update(crowding_distance(f, cfit))

        new_pop, new_fit = [], []
        for f in cfronts:
            if len(new_pop) + len(f) <= pop_size:
                for i in f:
                    new_pop.append(combined[i])
                    new_fit.append(cfit[i])
            else:
                sorted_f = sorted(f, key=lambda i: ccrowd.get(i, 0), reverse=True)
                need = pop_size - len(new_pop)
                for i in sorted_f[:need]:
                    new_pop.append(combined[i])
                    new_fit.append(cfit[i])
                break
        pop, fitness = new_pop, new_fit

    # Final: erste Front auf Test auswerten
    fronts = fast_non_dominated_sort(fitness)
    front = fronts[0]
    results = []
    for i in front:
        g = pop[i]
        tr = fitness_for_task_masked(g, task, train_mask)
        te = fitness_for_task_masked(g, task, test_mask)
        n = active_node_count(g, OUT_IDX)
        results.append({"train": tr, "test": te, "nodes": n})
    return results, gen

def summarize(results, task, seed):
    if not results:
        return
    # Extrema
    max_train = max(results, key=lambda r: r["train"])
    min_nodes = min(results, key=lambda r: r["nodes"])
    # Knee: bester Test-Wert
    best_test = max(results, key=lambda r: r["test"])
    # Parsimonioes und gut: max test unter <= 9 Knoten
    parsimonious = [r for r in results if r["nodes"] <= 9]
    best_pars = max(parsimonious, key=lambda r: r["test"]) if parsimonious else None

    print(f"  Front-Groesse: {len(results)}")
    print(f"    max_train  : train={max_train['train']:.4f} test={max_train['test']:.4f} "
          f"nodes={max_train['nodes']}")
    print(f"    min_nodes  : train={min_nodes['train']:.4f} test={min_nodes['test']:.4f} "
          f"nodes={min_nodes['nodes']}")
    print(f"    best_test  : train={best_test['train']:.4f} test={best_test['test']:.4f} "
          f"nodes={best_test['nodes']}")
    if best_pars:
        print(f"    pars<=9    : train={best_pars['train']:.4f} test={best_pars['test']:.4f} "
              f"nodes={best_pars['nodes']}")

def main():
    budget = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
    pop_size = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    n_seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    tasks = ["add2", "add3"]

    train_mask, test_mask = split_pairs(seed=42, n_train=48)
    print(f"NSGA-II: budget={budget}, pop={pop_size}, seeds={n_seeds}")
    print(f"Ziele: (train_acc, -n_active_nodes) auf {bin(train_mask).count('1')} Train-Paaren")
    print()

    for task in tasks:
        print(f"=== {task} ===")
        for seed in range(1, n_seeds + 1):
            rng = random.Random(f"nsga2-{task}-{seed}")
            results, gens = run_until = nsga2_run(task, train_mask, test_mask,
                                                   budget, pop_size, rng)
            print(f"  Seed {seed} ({gens} Generationen):")
            summarize(results, task, seed)
            solved = sum(1 for r in results if r["test"] >= 0.999)
            print(f"    geloeste Front-Punkte (test=1.0): {solved}")
            print()

if __name__ == "__main__":
    main()
