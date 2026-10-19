"""tools_selfadapt.py — CGP mit selbstjustierender Suche.

Bausteine:
  1. Selektorbreite waechst mit der Knotenzahl
  2. Output-Gene frei waehlbar
  3. Single-Active-Mutation
  4. 1/5-Erfolgsregel
  5. Neutrale Drift
  6. Parsimonie als Tie-Break
  7. Restart bei Stagnation
"""
import random
import sys
from tools_tasks import split_pairs, T_NE3, T_GT2, T_GT3, T_ADD2, T_ADD3, T_ADD4

M = (1 << 64) - 1
NIN = 6
IN = [sum(((i >> (3 + j)) & 1) << i for i in range(64)) for j in range(3)] + \
     [sum(((i >> j) & 1) << i for i in range(64)) for j in range(3)]
TARGETS = {"ne3": [T_NE3], "gt2": [T_GT2], "gt3": [T_GT3],
           "add2": T_ADD2, "add3": T_ADD3, "add4": T_ADD4}
OPS = (lambda a, b: a & b, lambda a, b: a | b,
       lambda a, b: a ^ b, lambda a, b: ~(a & b) & M)


class CGP:
    def __init__(self, task, n_nodes, mask, src_limit=10**9):
        self.N, self.mask, self.lim = n_nodes, mask, src_limit
        self.targets = TARGETS[task]
        self.k = len(self.targets)
        self.npos = [t & mask for t in self.targets]

    def hi(self, i):
        return min(NIN + i, self.lim)

    def random(self, rng):
        nodes = [(rng.randrange(4), rng.randrange(self.hi(i)),
                  rng.randrange(self.hi(i))) for i in range(self.N)]
        outs = [rng.randrange(NIN + self.N) for _ in range(self.k)]
        return nodes, outs

    def active(self, g):
        nodes, outs = g
        act, stack = set(), [o - NIN for o in outs if o >= NIN]
        while stack:
            i = stack.pop()
            if i in act: continue
            act.add(i)
            _, x, y = nodes[i]
            if x >= NIN: stack.append(x - NIN)
            if y >= NIN: stack.append(y - NIN)
        return act

    def acc(self, g):
        nodes, outs = g
        s = IN[:]
        for fn, x, y in nodes:
            s.append(OPS[fn](s[x], s[y]))
        m, tot = self.mask, 0.0
        npop = m.bit_count()
        for o, t in zip(outs, self.npos):
            p = s[o] & m
            P = t.bit_count()
            tp = (p & t).bit_count()
            tn = ((~p) & (~t) & m).bit_count()
            a1 = tp / P if P else 0.0
            a0 = tn / (npop - P) if npop - P else 0.0
            tot += (a0 + a1) / 2
        return tot / self.k

    def mutate(self, g, act, rng, k):
        nodes, outs = list(g[0]), list(g[1])
        n_genes = 3 * self.N + self.k
        hit = 0
        while hit < k:
            j = rng.randrange(n_genes)
            if j >= 3 * self.N:
                o = j - 3 * self.N
                r = NIN + self.N
                outs[o] = (outs[o] + 1 + rng.randrange(r - 1)) % r
                hit += 1
                continue
            i, f = divmod(j, 3)
            fn, x, y = nodes[i]
            if f == 0:
                fn = (fn + 1 + rng.randrange(3)) % 4
            else:
                r = self.hi(i)
                if r < 2: continue
                if f == 1: x = (x + 1 + rng.randrange(r - 1)) % r
                else:      y = (y + 1 + rng.randrange(r - 1)) % r
            nodes[i] = (fn, x, y)
            if i in act: hit += 1
        return nodes, outs


def key(cgp, g):
    a = round(cgp.acc(g), 9)
    return (a, -len(cgp.active(g)) if a >= 0.999999 else 0)


def search(cgp, rng, budget, lam=4, patience=4000, tail=3000):
    evals, gbest, gkey = 0, None, (-1, 0)
    while evals < budget:
        par = cgp.random(rng)
        pk = key(cgp, par); evals += 1
        mu, since, solved_at = 2.0, 0, None
        while evals < budget:
            act = cgp.active(par)
            kids = []
            for _ in range(lam):
                c = cgp.mutate(par, act, rng, max(1, int(mu + rng.random())))
                kids.append((key(cgp, c), c))
            evals += lam
            ck, c = max(kids, key=lambda t: t[0])
            if ck[0] > pk[0]:
                mu = min(8.0, mu * 1.5); since = 0
            else:
                mu = max(1.0, mu * 1.5 ** -0.25); since += lam
            if ck >= pk:
                par, pk = c, ck
            if pk[0] >= 0.999999:
                if solved_at is None: solved_at = evals
                if evals - solved_at > tail: break
            elif since > patience:
                break
        if pk > gkey:
            gbest, gkey = par, pk
        if gkey[0] >= 0.999999 and solved_at is not None:
            break
    return gbest, gkey


def main():
    from tools_matrix import run_ga
    from tools_tasks import fitness_for_task_masked
    tasks = sys.argv[1].split(",") if len(sys.argv) > 1 else ["add2", "add3"]
    budget = int(sys.argv[2]) if len(sys.argv) > 2 else 50000
    seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    n_nodes = int(sys.argv[4]) if len(sys.argv) > 4 else 18
    variants = sys.argv[5].split(",") if len(sys.argv) > 5 else ["alt", "neu16", "neu"]
    train, test = split_pairs(seed=42, n_train=48)
    med = lambda xs: sorted(xs)[len(xs) // 2]
    print(f"{'Task':<6}{'Variante':<8}{'train':>8}{'test':>8}{'gap':>8}{'geloest':>9}")
    for task in tasks:
        for v in variants:
            trs, tes = [], []
            for s in range(1, seeds + 1):
                rng = random.Random(f"{task}-{v}-{s}")
                if v == "alt":
                    f = lambda g, t=task: fitness_for_task_masked(g, t, train)
                    _, g, _, _ = run_ga(f, budget, 30, rng)
                    tr = fitness_for_task_masked(g, task, train)
                    te = fitness_for_task_masked(g, task, test)
                else:
                    lim = 16 if v == "neu16" else 10**9
                    ctr = CGP(task, n_nodes, train, lim)
                    cte = CGP(task, n_nodes, test, lim)
                    g, _ = search(ctr, rng, budget)
                    tr, te = ctr.acc(g), cte.acc(g)
                trs.append(tr); tes.append(te)
            sol = sum(t >= 0.999 for t in tes)
            print(f"{task:<6}{v:<8}{med(trs):>8.4f}{med(tes):>8.4f}"
                  f"{med(trs) - med(tes):>+8.3f}{sol:>6}/{seeds}", flush=True)


if __name__ == "__main__":
    main()
