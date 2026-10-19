"""tools_decode.py — Genome als lesbares Pseudo-Programm."""
import sys

OPS = {0: "AND", 1: "OR", 2: "XOR", 3: "NAND"}
IN_NAMES = ["A0", "A1", "A2", "B0", "B1", "B2"]
NIN = 6


def prune(nodes, outs):
    """Entfernt tote Knoten (Backward-Slice von den Outputs)."""
    keep = set()
    stack = [o - NIN for o in outs if o >= NIN]
    while stack:
        i = stack.pop()
        if i in keep:
            continue
        keep.add(i)
        _, x, y = nodes[i]
        if x >= NIN:
            stack.append(x - NIN)
        if y >= NIN:
            stack.append(y - NIN)
    keep_sorted = sorted(keep)
    remap = {old: NIN + new for new, old in enumerate(keep_sorted)}
    new_nodes = []
    for old in keep_sorted:
        fn, x, y = nodes[old]
        nx = remap.get(x - NIN, x) if x >= NIN else x
        ny = remap.get(y - NIN, y) if y >= NIN else y
        new_nodes.append((fn, nx, ny))
    new_outs = [remap.get(o - NIN, o) if o >= NIN else o for o in outs]
    return new_nodes, new_outs


def fmt_expr(nodes, idx):
    fn, x, y = nodes[idx]
    xs = IN_NAMES[x] if x < NIN else f"k{x - NIN}"
    ys = IN_NAMES[y] if y < NIN else f"k{y - NIN}"
    return f"{OPS[fn]}({xs}, {ys})"


def decode(nodes, outs, prune_dead=True):
    if prune_dead:
        nodes, outs = prune(nodes, outs)
    lines = []
    for i in range(len(nodes)):
        lines.append(f"  k{i} = {fmt_expr(nodes, i)}")
    for j, o in enumerate(outs):
        src = IN_NAMES[o] if o < NIN else f"k{o - NIN}"
        lines.append(f"  out{j} = {src}")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("usage: tools_decode.py <task> [budget]")
        return
    task = sys.argv[1]
    budget = int(sys.argv[2]) if len(sys.argv) > 2 else 300_000
    import random
    from tools_selfadapt import CGP, search
    from tools_tasks import split_pairs
    tr, _ = split_pairs(seed=42, n_train=48)
    cgp = CGP(task, 30, tr)
    g, key = search(cgp, random.Random(0), budget)
    print(f"# {task}, evolved genome, train_acc={key[0]:.4f}")
    print(decode(g[0], g[1]))


if __name__ == "__main__":
    main()
