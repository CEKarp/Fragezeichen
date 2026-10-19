"""plot_breakthrough.py — das Ergebnis in einem Bild."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))

# --- Panel 1: Erfolgsrate ueber Budget ---
ax = axes[0]
add3_budget = [50_000, 300_000]
add3_rate   = [0.40, 0.969]  # 4/10, 31/32
add4_budget = [50_000, 300_000, 1_000_000, 3_000_000]
add4_rate   = [0.00, 0.156, 0.375, 0.438]

ax.plot(add3_budget, add3_rate, "o-", color="#1f77b4", linewidth=2.5,
        markersize=10, label="add3 (3-Bit-Addierer)")
ax.plot(add4_budget, add4_rate, "s-", color="#d62728", linewidth=2.5,
        markersize=10, label="add4 (4-Bit-Addierer)")
ax.set_xscale("log")
ax.set_xlabel("Evaluationsbudget (log)")
ax.set_ylabel("Erfolgsrate auf Test")
ax.set_ylim(-0.05, 1.05)
ax.axhline(1.0, color="grey", linestyle="--", linewidth=0.8, alpha=0.5)
ax.grid(True, alpha=0.3)
ax.legend(loc="lower right", fontsize=10)
ax.set_title("Panel 1: Budget vs. Erfolgsrate\n(neuer GA, 30 Knoten, Test-Split)",
             fontsize=11)

# --- Panel 2: Alt vs. Neu (Bar Chart) ---
ax = axes[1]
tasks = ["add3", "add4"]
alt_rates = [0.0, 0.0]      # alt: 0/10 bei 50k
neu_rates = [0.969, 0.438]  # neu: add3 31/32@300k, add4 14/32@3Mio
x = np.arange(len(tasks))
w = 0.35
bars1 = ax.bar(x - w/2, alt_rates, w, label="Alter GA (16 Selektoren)",
               color="#999999", edgecolor="black")
bars2 = ax.bar(x + w/2, neu_rates, w, label="Neuer GA (breit + adaptive)",
               color="#2ca02c", edgecolor="black")
for bars in (bars1, bars2):
    for b in bars:
        h = b.get_height()
        if h > 0:
            ax.text(b.get_x() + b.get_width()/2, h + 0.02, f"{h:.2f}",
                    ha="center", fontsize=10, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(tasks)
ax.set_ylabel("Erfolgsrate auf Test")
ax.set_ylim(0, 1.1)
ax.legend(loc="upper right", fontsize=9)
ax.set_title("Panel 2: Alter vs. neuer GA\n(beide 30 Knoten)",
             fontsize=11)
ax.grid(True, alpha=0.3, axis="y")

# --- Panel 3: Die zwei Fehler isoliert ---
ax = axes[2]
variants = ["alt", "neu16", "neu"]
add3_v = [0.756, 0.915, 0.934]
add4_v = [0.750, 0.815, 0.878]
x = np.arange(len(variants))
w = 0.35
ax.bar(x - w/2, add3_v, w, label="add3", color="#1f77b4", edgecolor="black")
ax.bar(x + w/2, add4_v, w, label="add4", color="#d62728", edgecolor="black")
ax.set_xticks(x)
ax.set_xticklabels(["alt\n(16 sel, alte Suche)",
                    "neu16\n(alte 16 sel, neue Suche)",
                    "neu\n(breit + neue Suche)"], fontsize=8)
ax.set_ylabel("Test-Fitness (Median)")
ax.set_ylim(0.5, 1.0)
ax.axhline(0.75, color="grey", linestyle=":", alpha=0.4)
ax.legend(loc="lower right", fontsize=9)
ax.set_title("Panel 3: Die zwei Fehler isoliert\n(50k Evals, 30 Knoten)",
             fontsize=11)
ax.grid(True, alpha=0.3, axis="y")

fig.suptitle("Fragezeichen — Selbstjustierender CGP löst Addierer, die vorher scheiterten",
             fontsize=13, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig("breakthrough.png", dpi=140, bbox_inches="tight")
print("geschrieben: breakthrough.png")
