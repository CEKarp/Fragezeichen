#!/usr/bin/env python3
"""plot.py - liest results_seed*.json, zeichnet die Konvergenzkurve."""
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


def find_runs():
    files = sorted(Path(".").glob("results_seed*.json"))
    if files:
        return files
    single = Path("results.json")
    if single.exists():
        return [single]
    sys.exit("Keine results*.json gefunden — erst make laufen lassen.")


def main():
    files = find_runs()
    print(f"Lade {len(files)} Lauf/Laeufe: {[f.name for f in files]}")

    # Bei mehreren Laeufen: nur den ersten plotten (Multi-Seed kommt spaeter)
    data = json.loads(files[0].read_text())
    hist = data.get("history", [])
    if not hist:
        sys.exit("history ist leer.")

    gens   = [h["gen"] for h in hist]
    fit    = [h["fit"] for h in hist]
    levels = [h["level"] for h in hist]
    series = {t: [h.get("tasks", {}).get(t, 0.0) for h in hist] for t in TASKS}

    fig, ax = plt.subplots(figsize=(12, 6.5))

    # 1) Gesamt-Fitness - dicke schwarze Linie
    ax.plot(gens, fit, color="black", linewidth=3.2,
            label="Gesamt-Fitness", zorder=10)

    # 2) Tasks - duenne farbige Linien
    for t in TASKS:
        ax.plot(gens, series[t], color=COLORS[t], linewidth=1.1,
                alpha=0.85, label=t, zorder=3)

    # 3) Level-Wechsel - vertikale Marker
    prev = levels[0]
    for g, l in zip(gens, levels):
        if l != prev:
            ax.axvline(g - 0.5, color="grey", linestyle="--",
                       linewidth=1.0, alpha=0.7, zorder=1)
            ax.text(g - 0.55, 0.5, f" L{l} ", color="grey",
                    fontsize=9, rotation=90, va="center", ha="right")
            prev = l

    ax.set_xlabel("Generation")
    ax.set_ylabel("Fitness (0 .. 1)")
    ax.set_ylim(-0.02, 1.03)
    ax.set_xlim(min(gens), max(gens))
    ax.grid(True, alpha=0.3, zorder=0)
    ax.legend(loc="lower right", fontsize=9, ncol=2, framealpha=0.95)

    best_fit = data.get("best_fitness", fit[-1] if fit else 0.0)
    best_gen = data.get("best_genome", "?")
    ax.set_title(
        f"Enigma-Damen GA  |  best fit {best_fit:.4f}  |  genome 0x{best_gen}  "
        f"|  {len(gens)} Generationen")

    fig.tight_layout()
    fig.savefig(OUT, dpi=140, bbox_inches="tight")
    print(f"geschrieben: {OUT.resolve()}")

    print(f"  final  gesamt = {fit[-1]:.4f}  (best ever {best_fit:.4f})")
    for t in TASKS:
        print(f"  final  {t:<8} = {series[t][-1]:.4f}")
    ups = sum(1 for a, b in zip(levels, levels[1:]) if a != b)
    print(f"  Level-Upgrades: {ups}  (L{levels[0]} -> L{levels[-1]})")


if __name__ == "__main__":
    main()
