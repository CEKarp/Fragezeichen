"""tools_errors.py — an welchen Test-Paaren scheitern nicht-geloeste add4-Seeds?"""
import random
import sys
from collections import Counter
from multiprocessing import Pool
from tools_selfadapt import CGP, search, IN, OPS
from tools_tasks import split_pairs, T_ADD4

NIN = 6
M = (1 << 64) - 1


def eval_per_pair(g, cgp, mask):
    """Fuer jedes der 16 Test-Paare: welche Ausgangsbits stimmen?"""
    nodes, outs = g
    sig = IN[:]
    for fn, x, y in nodes:
        sig.append(OPS[fn](sig[x], sig[y]))

    # Fuer jedes Bit-Paar (a, b) mit a, b in 0..7: welche 4 Ausgangsbits stimmen?
    pair_results = {}
    for idx in range(64):
        if not (mask & (1 << idx)):
            continue
        a, b = idx >> 3, idx & 7
        target_sum = (a + b) & 0xF
        pred_sum = 0
        for bit in range(4):
            if sig[outs[bit]] & (1 << idx):
                pred_sum |= 1 << bit
        pair_results[(a, b)] = {
            "target": target_sum,
            "pred": pred_sum,
            "correct": pred_sum == target_sum,
            "bits_wrong": [(bit, (target_sum >> bit) & 1, (pred_sum >> bit) & 1)
                           for bit in range(4)
                           if ((target_sum >> bit) & 1) != ((pred_sum >> bit) & 1)],
        }
    return pair_results


def one(args):
    task, budget, n_nodes, seed = args
    tr, te = split_pairs(seed=42, n_train=48)
    cgp_tr = CGP(task, n_nodes, tr)
    cgp_te = CGP(task, n_nodes, te)
    rng = random.Random(f"{task}-err-{seed}")
    g, _ = search(cgp_tr, rng, budget)
    test_acc = cgp_te.acc(g)
    pairs = eval_per_pair(g, cgp_te, te)
    wrong_pairs = [ab for ab, r in pairs.items() if not r["correct"]]
    return {
        "seed": seed,
        "test_acc": test_acc,
        "solved": test_acc >= 0.999,
        "wrong_pairs": wrong_pairs,
        "n_wrong": len(wrong_pairs),
        "pairs": pairs,
    }


def main():
    task = sys.argv[1] if len(sys.argv) > 1 else "add4"
    budget = int(sys.argv[2]) if len(sys.argv) > 2 else 1_000_000
    seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 32
    n_nodes = int(sys.argv[4]) if len(sys.argv) > 4 else 30

    jobs = [(task, budget, n_nodes, s) for s in range(seeds)]
    with Pool() as p:
        results = []
        total = len(jobs)
        for i, r in enumerate(p.imap_unordered(one, jobs), 1):
            results.append(r)
            if i % 8 == 0 or i == total:
                print(f"  [{i}/{total}] fertig", flush=True)

    results.sort(key=lambda r: r["seed"])
    solved = [r for r in results if r["solved"]]
    unsolved = [r for r in results if not r["solved"]]

    print()
    print(f"Task={task}, Knoten={n_nodes}, Budget={budget}, Seeds={seeds}")
    print(f"Geloest: {len(solved)}/{seeds}, nicht geloest: {len(unsolved)}/{seeds}")
    print()

    if not unsolved:
        print("Alle geloest, keine Fehleranalyse moeglich.")
        return

    # Verteilung der Fehleranzahl
    n_wrong_dist = Counter(r["n_wrong"] for r in unsolved)
    print("Fehleranzahl pro nicht-geloestem Seed:")
    for n in sorted(n_wrong_dist):
        print(f"  {n} falsche Paare: {n_wrong_dist[n]} Seeds")
    print()

    # Aggregiere: welches Test-Paar ist am haeufigsten falsch?
    pair_errors = Counter()
    for r in unsolved:
        for ab in r["wrong_pairs"]:
            pair_errors[ab] += 1

    print(f"Top-10 Test-Paare nach Fehlerhaeufigkeit "
          f"(von {len(unsolved)} nicht-geloesten Seeds):")
    for (a, b), count in pair_errors.most_common(10):
        total_sum = a + b
        print(f"  {a}+{b}={total_sum:>2}  ({a:03b}+{b:03b}): "
              f"{count}/{len(unsolved)} falsch")
    print()

    # Zufalls-Erwartung: wenn Fehler zufaellig waeren, welches Paar
    # sollte dann wie oft falsch sein?
    total_wrong = sum(r["n_wrong"] for r in unsolved)
    n_pairs = 16
    expected_uniform = total_wrong / n_pairs if n_pairs else 0
    print(f"Erwartung bei Zufall (uniform): {expected_uniform:.2f} Fehler pro Paar")
    print(f"Tatsaechliches Maximum: {pair_errors.most_common(1)[0][1] if pair_errors else 0}")
    print()

    # Detail pro nicht-geloestem Seed
    print("Detail:")
    for r in unsolved[:10]:
        print(f"  Seed {r['seed']:>2}: {r['n_wrong']} falsch "
              f"(test_acc={r['test_acc']:.4f}): {r['wrong_pairs'][:5]}")


if __name__ == "__main__":
    main()
