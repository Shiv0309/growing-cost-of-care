"""Compare payer coverage shares for ages under 18 and 55+."""

from pathlib import Path
from statistics import correlation

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

from plot_sample_coverage_by_payer import AGE_PANELS, COVERED_COLOR, SAMPLE_DIR
from sample_coverage_by_age_and_payer import coverage_totals


def main():
    groups, names = coverage_totals(
        SAMPLE_DIR, AGE_PANELS, (18, 55), single_dispense_only=True,
    )
    young, _, older = AGE_PANELS
    shares = {
        (age, payer): float(total.coverage / total.cost)
        for (age, payer), total in groups.items()
        if total.cost and total.coverage is not None
    }
    pairs = [
        (names.get(payer, payer), share, shares[older, payer])
        for (age, payer), share in shares.items()
        if age == young and (older, payer) in shares
    ]
    labels, x, y = zip(*pairs)
    r = correlation(x, y)
    insured = [(a, b) for name, a, b in pairs if name != "NO_INSURANCE"]
    insured_r = correlation(*zip(*insured))
    fig, ax = plt.subplots(figsize=(6.5, 6.5), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.3, h_pad=0.3)
    ax.set_box_aspect(1)
    ax.plot([0, 1], [0, 1], linestyle="--", color="#9AA7B2", linewidth=1, zorder=2)
    ax.scatter(x, y, color=COVERED_COLOR, s=46, edgecolors="white", linewidths=0.7, zorder=3)
    for label, a, b in pairs:
        align_right = label in {"Medicare", "Medicaid", "UnitedHealthcare"}
        vertical_offset = {"Anthem": 15, "NO_INSURANCE": 0}.get(label, 5)
        ax.annotate(
            "No insurance" if label == "NO_INSURANCE" else label, (a, b),
            xytext=(-7 if align_right else 7, vertical_offset), textcoords="offset points",
            ha="right" if align_right else "left",
            va="center" if label == "NO_INSURANCE" else "baseline",
            fontsize=9, color="#182633",
        )
    ax.set(
        xlim=(-0.04, 1), ylim=(-0.04, 1),
        xlabel=f"Recorded coverage share · Age {young}",
    )
    ax.set_ylabel(f"Recorded\ncoverage share\nAge {older}", rotation=0,
                  ha="center", va="center", labelpad=42)
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_ticks([0, 0.25, 0.5, 0.75, 1])
        axis.set_major_formatter(PercentFormatter(1))
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["bottom", "left"]].set_color("#CCD4DB")
    ax.tick_params(length=0, pad=5, colors="#52616E")
    ax.grid(color="#E8EDF1", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title(
        f"Correlation in medication coverage\nAges {young} and {older}",
        loc="center", y=1.055, pad=8,
        fontsize=17, fontweight="bold", color="#182633",
    )
    ax.set_title(f"Single-dispense records · Pearson r = {r:.2f}",
                 loc="left", x=0.5, y=1, ha="center", fontsize=10, color="#52616E", pad=8)
    output = Path(__file__).resolve().parents[1] / "sample_coverage_age_correlation.png"
    fig.savefig(output, dpi=360)
    print(f"Pearson r = {r:.4f} (n={len(pairs)})")
    print(f"Excluding NO_INSURANCE: r = {insured_r:.4f} (n={len(insured)})")
    print(", ".join(labels))


if __name__ == "__main__":
    main()
