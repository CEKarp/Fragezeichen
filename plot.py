#!/usr/bin/env python3
"""plot.py — vergleicht mini_alu (echtes DUT) und blind_seed (Negativkontrolle)."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path("convergence.png")

TASKS = ["calc", "mem", "cmp", "cmp_hard", "cipher"]
COLORS = {
    "calc":     "#1f77b4",
    "mem":      "#2ca02c",
    "cmp":      "#ff7f0e",
    "cmp_hard": "#d62728",
    "cipher":   "#9467bd",
}

RUNS = [
    ("mini_alu",    Path("results_seed1.json"),        "black"),
    ("blind_seed",  Path("results_blind_seed1.json"),  "grey"),
]


def load(path):
    if not path.exists():
        sys.exit(f"{path} fehlt — erst make laufen lassen.")
    return json.loads(path.read_text())


def draw_panel(ax, data, title, color_main):
    hist   = data["history"]
    gens   = [h["gen"] for h in hist]
    fit    = [h["fit"] for h in hist]
    levels = [h["level"] for h in hist]

    # Task-Linien
    for t in TASKS:
        vals = [h.get("tasks", {}).get(t, 0.0) for h in hist]
        ax.plot(gens, vals, color=COLORS[t], linewidth=1.0,
                alpha=0.75, label=t, zorder=3)

    # Gesamt-Fitness dick
    ax.plot(gens, fit, color=color_main, linewidth=3.0,
            label="Gesamt", zorder=10)

    # Level-Wechsel
    prev = levels[0]
    for g, l in zip(gens, levels):
        if l != prev:
            ax.axvline(g - 0.5, color="grey", linestyle="--",
                       linewidth=0.9, alpha=0.7, zorder=1)
            ax.text(g - 0.55, 0.5, f" L{l} ", color="grey",
                    fontsize=8, rotation=90, va="center", ha="right")
            prev = l

    ax.set_xlabel("Generation")
    ax.set_ylabel("Fitness (0 .. 1)")
    ax.set_ylim(-0.02, 1.03)
    ax.set_xlim(min(gens), max(gens))
    ax.grid(True, alpha=0.3, zorder=0)
    ax.legend(loc="lower right", fontsize=7, ncol=2, framealpha=0.9)
    ax.set_title(title)


def main():
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), sharey=True)

    for ax, (name, path, col) in zip(axes, RUNS):
        data = load(path)
        bf = data.get("best_fitness", 0.0)
        bg = data.get("best_genome", "?")
        title = f"{name}\nbest {bf:.4f} | genome 0x{bg[:8]}..."
        draw_panel(ax, data, title, color_main=col)

    fig.suptitle(
        "Enigma-Damen GA — mini_alu (links, Gradient vorhanden) "
        "vs. blind_seed (rechts, kein Gradient)",
        fontsize=12, y=0.99)

    fig.tight_layout()
    fig.savefig(OUT, dpi=140, bbox_inches="tight")
    print(f"geschrieben: {OUT.resolve()}")

    for name, path, _ in RUNS:
        d = load(path)
        hist = d["history"]
        final = hist[-1]["fit"]
        print(f"  {name:<11} | final {final:.4f} | best {d['best_fitness']:.4f}")


if __name__ == "__main__":
    main()
