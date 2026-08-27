from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


OUT = Path("outputs/ieee/figures")
OUT.mkdir(parents=True, exist_ok=True)


def save(fig, name):
    fig.savefig(OUT / name, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def pipeline():
    fig, ax = plt.subplots(figsize=(7.1, 1.9))
    ax.axis("off")
    boxes = [
        ("Golden PDFs", "5 clean\nbaselines"),
        ("Mutation", "5 structure\noperators"),
        ("Verification", "Parseable,\npage-stable"),
        ("Validators", "PAC, Acrobat,\nveraPDF"),
        ("Matrix", "Detected,\nMissed, N/A"),
    ]
    x_positions = [0.02, 0.225, 0.43, 0.635, 0.84]
    for i, (title, subtitle) in enumerate(boxes):
        x = x_positions[i]
        ax.add_patch(
            FancyBboxPatch(
                (x, 0.34),
                0.14,
                0.36,
                boxstyle="round,pad=0.012,rounding_size=0.018",
                linewidth=1,
                edgecolor="#2f5d7c",
                facecolor="#eef4fb",
                transform=ax.transAxes,
            )
        )
        ax.text(x + 0.07, 0.58, title, ha="center", va="center", fontsize=8.5, fontweight="bold", transform=ax.transAxes)
        ax.text(x + 0.07, 0.44, subtitle, ha="center", va="center", fontsize=7.2, transform=ax.transAxes)
        if i < len(boxes) - 1:
            ax.add_patch(
                FancyArrowPatch(
                    (x + 0.155, 0.52),
                    (x_positions[i + 1] - 0.015, 0.52),
                    arrowstyle="-|>",
                    mutation_scale=9,
                    linewidth=1,
                    color="#666666",
                    transform=ax.transAxes,
                )
            )
    ax.text(
        0.02,
        0.14,
        "Detection is coded only after independent mutation verification; N/A cases are excluded from denominators.",
        fontsize=7.5,
        color="#4b5563",
        transform=ax.transAxes,
    )
    save(fig, "figure1_pipeline.png")


def overall_rates():
    names = ["PAC", "Acrobat", "veraPDF"]
    rates = [17.4, 21.7, 21.7]
    counts = ["4/23", "5/23", "5/23"]
    colors = ["#4477aa", "#228833", "#66ccee"]
    fig, ax = plt.subplots(figsize=(3.5, 2.4))
    bars = ax.bar(names, rates, color=colors, width=0.58)
    ax.set_ylim(0, 25)
    ax.set_ylabel("Detection rate (%)", fontsize=8)
    ax.tick_params(axis="both", labelsize=8)
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ax.set_axisbelow(True)
    for bar, rate, count in zip(bars, rates, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, rate + 0.8, f"{rate:.1f}%", ha="center", fontsize=8, fontweight="bold")
        ax.text(bar.get_x() + bar.get_width() / 2, -3.1, count, ha="center", fontsize=7, color="#4b5563")
    save(fig, "figure2_overall_detection_rates.png")


def per_operator():
    operators = ["M01", "M02", "M03", "M04", "M05"]
    pac = [0, 0, 100, 0, 0]
    acrobat = [0, 0, 100, 20, 0]
    verapdf = [0, 0, 100, 20, 0]
    x = range(len(operators))
    width = 0.24
    fig, ax = plt.subplots(figsize=(5.2, 2.7))
    ax.bar([i - width for i in x], pac, width=width, color="#4477aa", label="PAC")
    ax.bar(list(x), acrobat, width=width, color="#228833", label="Acrobat")
    ax.bar([i + width for i in x], verapdf, width=width, color="#66ccee", label="veraPDF")
    ax.set_xticks(list(x), operators)
    ax.set_ylim(0, 110)
    ax.set_ylabel("Detection rate (%)", fontsize=8)
    ax.tick_params(axis="both", labelsize=8)
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=7, frameon=False, ncol=3)
    for idx, val in enumerate([100, 100, 100]):
        ax.text(2 + (idx - 1) * width, val + 2, "100", ha="center", fontsize=6.5)
    ax.text(3, 22, "20", ha="center", fontsize=6.5)
    ax.text(3 + width, 22, "20", ha="center", fontsize=6.5)
    save(fig, "figure3_per_operator_detection.png")


if __name__ == "__main__":
    pipeline()
    overall_rates()
    per_operator()
    for path in sorted(OUT.glob("*.png")):
        print(path)
