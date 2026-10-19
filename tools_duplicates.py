"""tools_duplicates.py — strukturelle Vielfalt der geloesten Genome."""
import random
import sys
from multiprocessing import Pool
from tools_selfadapt import CGP, search, IN, OPS
from tools_tasks import split_pairs

NIN = 6


def compute_fingerprint(g, cgp):
    """Structural fingerprint: alle Knoten-TTs sortiert + Operator-Counts."""
    nodes, outs = g
    sig = IN[:]
    for fn, x, y in nodes:
        sig.append(OPS[fn](sig[x], sig[y]))

    act = cgp.active(g)

    # Wahrheitstabellen der aktiven Knoten, sortiert (Permutations-invariant)
    tts = tuple(sorted(sig[NIN + i] for i in act))
    tt_hash = hash(tts)

    # Operator-Verteilung
    op_counts = tuple(sum(1 for i in act if nodes[i][0] == k) for k in range(4))

    # Tiefe (max. Distanz von Eingang zum Output)
    depth = {}
    for i in range(len(nodes)):
        if i not in act:
            continue
        _, x, y = nodes[i]
        dx = 0 if x < NIN else depth.get(x - NIN, 0) + 1
        dy = 0 if y < NIN else depth.get(y - NIN, 0) + 1
        depth[i] = max(dx, dy)
    max_depth = max(depth.values()) if depth else 0

    return {
        "tt_hash": tt_hash,
        "n_active": len(act),
        "op_counts": op_counts,
        "depth": max_depth,
    }


def one(args):
    task, budget, n_nodes, seed = args
    tr, te = split_pairs(seed=42, n_train=48)
    cgp_tr = CGP(task, n_nodes, tr)
    cgp_te = CGP(task, n_nodes, te)
    rng = random.Random(f"{task}-dup-{seed}")
    g, _ = search(cgp_tr, rng, budget)
    test_acc = cgp_te.acc(g)
    if test_acc < 0.999:
        return {"seed": seed, "solved": False}
    fp = compute_fingerprint(g, cgp_tr)
    return {
        "seed": seed,
        "solved": True,
        "test_acc": test_acc,
        "nodes": fp["n_active"],
        "tt_hash": fp["tt_hash"],
        "op_counts": fp["op_counts"],
        "depth": fp["depth"],
    }


def main():
    task = sys.argv[1] if len(sys.argv) > 1 else "add3"
    budget = int(sys.argv[2]) if len(sys.argv) > 2 else 300_000
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

    solved = [r for r in results if r["solved"]]
    print()
    print(f"Task={task}, Knoten={n_nodes}, Budget={budget}, Seeds={seeds}")
    print(f"Geloest: {len(solved)}/{seeds}")
    print()

    if not solved:
        print("Keine Loesungen, keine Struktur-Analyse moeglich.")
        return

    # Gruppierung nach tt_hash
    from collections import Counter
    hashes = Counter(r["tt_hash"] for r in solved)
    print(f"Einzigartige Strukturen (tt_hash): {len(hashes)}")
    print(f"Verteilung der Gruppengroessen: {sorted(hashes.values(), reverse=True)}")
    print()

    # Knoten-Verteilung
    nodes_dist = Counter(r["nodes"] for r in solved)
    print("Knoten-Verteilung:")
    for n in sorted(nodes_dist):
        print(f"  {n} Knoten: {nodes_dist[n]} Genome")
    print()

    # Tiefe
    depth_dist = Counter(r["depth"] for r in solved)
    print("Tiefe-Verteilung:")
    for d in sorted(depth_dist):
        print(f"  Tiefe {d}: {depth_dist[d]} Genome")
    print()

    # Operator-Counts
    print("Operator-Verteilung (AND, OR, XOR, NAND):")
    for r in solved[:10]:
        print(f"  Seed {r['seed']:>2}: {r['op_counts']}  "
              f"({r['nodes']} Knoten, Tiefe {r['depth']})")


if __name__ == "__main__":
    main()
