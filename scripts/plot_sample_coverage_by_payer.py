"""Plot sample medication coverage by payer and age at medication start."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

from sample_coverage_by_age_and_payer import SAMPLE_DIR, coverage_totals

AGE_PANELS = ("<18", "18–54", "55+")


def plot_coverage(sample_dir):
    groups, payer_names = coverage_totals(
        sample_dir, AGE_PANELS, (18, 55), single_dispense_only=True,
    )
    payers = sorted(
        {payer for age, payer in groups if age in AGE_PANELS},
        key=lambda payer: (payer_names.get(payer, ""), payer),
    )
    labels = [payer_names.get(payer) or payer or "Unknown payer" for payer in payers]
    fig, axes = plt.subplots(
        1, 3, sharex=True, sharey=True,
        figsize=(14, max(3, 0.46 * len(payers) + 1.7)), layout="constrained",
    )
    for ax, age in zip(axes, AGE_PANELS):
        positions = []
        covered = []
        for index, payer in enumerate(payers):
            totals = groups.get((age, payer))
            if totals is None or not totals.cost or totals.coverage is None:
                ax.text(0.5, index, "No data", ha="center", va="center", color="#555555")
                continue
            share = float(totals.coverage / totals.cost)
            positions.append(index)
            covered.append(share)
            ax.text(1.02, index, f"{share:.2%}", va="center", fontsize=9)

        # Blue and orange from the Okabe–Ito palette.
        ax.barh(positions, covered, color="#0072B2", label="Covered")
        ax.barh(positions, [1 - share for share in covered], left=covered,
                color="#E69F00", label="Uncovered")
        ax.set_title(age)
        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)

    axes[0].set_yticks(range(len(payers)), labels)
    axes[0].set_ylim(len(payers) - 0.5, -0.5)
    axes[0].set_xticks([0, 0.25, 0.5, 0.75, 1])
    axes[0].set_xlim(0, 1.22)
    axes[0].xaxis.set_major_formatter(PercentFormatter(1))
    fig.suptitle("Synthea medication coverage by payer and age · Single-dispense records")
    fig.supxlabel("Share of medication costs")
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="outside upper right", ncol=2, frameon=False)
    return fig


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-dir", type=Path, default=SAMPLE_DIR)
    parser.add_argument("--output", type=Path, help="Save to this path instead of opening a window.")
    args = parser.parse_args()
    figure = plot_coverage(args.sample_dir)
    if args.output:
        figure.savefig(args.output, dpi=180)
    else:
        plt.show()
