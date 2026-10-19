"""tools_crib.py — teilinformierter Seed: GA mit Crib (bekannte Teilfunktion)."""
import random
import sys
from tools_selfadapt import CGP, search, IN, OPS
from tools_tasks import split_pairs

M = (1 << 64) - 1
S0_TT = sum((((i >> 3) & 1) ^ (i & 1)) << i for i in range(64))


class CGPWithCrib(CGP):
    """Fitness = (base_acc + crib_bonus * crib_score) / (1 + crib_bonus).

    Normalisiert, damit max=1.0. Der GA kann ohne geloeste Schaltung
    nicht durch Crib allein auf 1.0 kommen.
    """

    def __init__(self, task, n_nodes, mask, crib_bonus=0.3, src_limit=10**9):
        super().__init__(task, n_nodes, mask, src_limit)
        self.crib_bonus = crib_bonus
        self.crib_target = S0_TT & mask

    def acc(self, g):
        nodes, outs = g
        sig = IN[:]
        for fn, x, y in nodes:
            sig.append(OPS[fn](sig[x], sig[y]))

        m = self.mask
        npop = m.bit_count()
        tot = 0.0
        for o, t in zip(outs, self.npos):
            p = sig[o] & m
            P = t.bit_count()
            tp = (p & t).bit_count()
            tn = ((~p) & (~t) & m).bit_count()
            a1 = tp / P if P else 0.0
            a0 = tn / (npop - P) if npop - P else 0.0
            tot += (a0 + a1) / 2
        base = tot / self.k

        out0 = sig[outs[0]] & m
        crib_correct = ((~(out0 ^ self.crib_target)) & m).bit_count()
        crib_score = crib_correct / npop if npop else 0.0

        return (base + self.crib_bonus * crib_score) / (1 + self.crib_bonus)


def run_variant(task, n_nodes, budget, seeds, crib_bonus, train_mask, test_mask):
    trs, tes, solved = [], [], 0
    for s in range(seeds):
        rng = random.Random(f"{task}-crib-{crib_bonus}-{s}")
        cgp = CGPWithCrib(task, n_nodes, train_mask, crib_bonus=crib_bonus)
        g, _ = search(cgp, rng, budget)
        # Reine Accuracy ohne Crib-Bonus messen
        tr_real = CGP(task, n_nodes, train_mask).acc(g)
        te_real = CGP(task, n_nodes, test_mask).acc(g)
        trs.append(tr_real)
        tes.append(te_real)
        if te_real >= 0.999:
            solved += 1
    return trs, tes, solved


def main():
    task = sys.argv[1] if len(sys.argv) > 1 else "add3"
    budget = int(sys.argv[2]) if len(sys.argv) > 2 else 300_000
    seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 32
    n_nodes = int(sys.argv[4]) if len(sys.argv) > 4 else 30

    train, test = split_pairs(seed=42, n_train=48)
    med = lambda xs: sorted(xs)[len(xs) // 2]

    print(f"Task={task}, Knoten={n_nodes}, Budget={budget}, Seeds={seeds}")
    print(f"Crib: s0 = A0 ^ B0 (bekannte Teilfunktion der Addition)")
    print()
    print(f"{'Variante':<28} {'train_med':>10} {'test_med':>10} {'geloest':>10}")
    print("-" * 60)

    variants = [
        ("blind (bonus=0.0)", 0.0),
        ("teilinformiert (0.1)", 0.1),
        ("teilinformiert (0.3)", 0.3),
        ("teilinformiert (0.5)", 0.5),
    ]
    for name, bonus in variants:
        trs, tes, sol = run_variant(task, n_nodes, budget, seeds, bonus, train, test)
        print(f"{name:<28} {med(trs):>10.4f} {med(tes):>10.4f} {sol:>7}/{seeds}")


if __name__ == "__main__":
    main()
