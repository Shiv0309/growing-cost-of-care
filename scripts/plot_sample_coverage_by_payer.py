"""Plot sample medication coverage by payer and age at medication start."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import PercentFormatter
from matplotlib.transforms import blended_transform_factory

from sample_coverage_by_age_and_payer import SAMPLE_DIR, coverage_totals

AGE_PANELS = ("<18", "18–54", "55+")
# Blue and orange from the Okabe–Ito palette.
COVERED_COLOR = "#0072B2"
UNCOVERED_COLOR = "#E69F00"
INK = "#182633"
MUTED = "#52616E"
BAR_HEIGHT = 0.58


def plot_coverage(sample_dir):
    groups, payer_names = coverage_totals(
        sample_dir, AGE_PANELS, (18, 55), single_dispense_only=True,
    )
    payers = sorted(
        {payer for age, payer in groups if age in AGE_PANELS},
        key=lambda payer: (payer_names.get(payer, ""), payer),
    )
    labels = [payer_names.get(payer) or payer or "Unknown payer" for payer in payers]
    payer_height = max(3, 0.40 * len(payers))
    fig = plt.figure(figsize=(12.4, payer_height + 2.2), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.22, h_pad=0.20, wspace=0.025, hspace=0.015)
    grid = fig.add_gridspec(2, 3, height_ratios=(0.29, payer_height))
    legend_ax = fig.add_subplot(grid[0, :])
    legend_ax.set_axis_off()
    first = fig.add_subplot(grid[1, 0])
    axes = [first] + [
        fig.add_subplot(grid[1, column], sharex=first, sharey=first)
        for column in (1, 2)
    ]
    summary_row = len(payers) + 0.5
    band_transform = blended_transform_factory(fig.transFigure, first.transData)
    fig.add_artist(Rectangle(
        (0, summary_row - 0.53), 1, 1.06,
        transform=band_transform, facecolor="#E8EDF1",
        edgecolor="none", zorder=-1, in_layout=False,
    ))
    for ax, age in zip(axes, AGE_PANELS):
        ax.patch.set_visible(False)
        positions = []
        covered = []
        for index, payer in enumerate(payers):
            totals = groups.get((age, payer))
            if totals is None or not totals.cost or totals.coverage is None:
                ax.text(0.5, index, "No data", ha="center", va="center", color=MUTED, fontsize=9)
                continue
            share = float(totals.coverage / totals.cost)
            positions.append(index)
            covered.append(share)
            ax.text(1.02, index, f"{share:.2%}", va="center", fontsize=9, color=INK)

        ax.barh(positions, covered, height=BAR_HEIGHT, color=COVERED_COLOR,
                label="Recorded payer coverage")
        ax.barh(positions, [1 - share for share in covered], left=covered,
                height=BAR_HEIGHT, color=UNCOVERED_COLOR, label="Remaining cost")
        ax.set_title(f"Age {age}", loc="left", pad=7, color=INK,
                     fontsize=14, fontweight="bold")
        ax.tick_params(axis="both", length=0, labelsize=10, labelcolor=MUTED, pad=5)
        ax.spines["bottom"].set_color("#CCD4DB")
        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)

        age_totals = [total for (group, _), total in groups.items() if group == age]
        cost = sum(total.cost or 0 for total in age_totals)
        coverage = [total.coverage for total in age_totals if total.coverage is not None]
        if cost and coverage:
            share = float(sum(coverage) / cost)
            ax.barh(summary_row, share, height=BAR_HEIGHT, color=COVERED_COLOR)
            ax.barh(summary_row, 1 - share, left=share, height=BAR_HEIGHT, color=UNCOVERED_COLOR)
            ax.text(1.02, summary_row, f"{share:.2%}", va="center",
                    fontsize=10, color=INK, fontweight="bold")
        else:
            ax.text(0.5, summary_row, "No data", ha="center", va="center", color=MUTED, fontsize=9)

    axes[0].set_yticks([*range(len(payers)), summary_row], [*labels, "All payer types"])
    axes[0].get_yticklabels()[-1].set_fontweight("bold")
    axes[0].set_ylim(summary_row + 0.55, -0.43)
    axes[0].get_yticklabels()[-1].set_color(INK)
    axes[0].set_xticks([0, 0.25, 0.5, 0.75, 1])
    axes[0].set_xlim(0, 1.18)
    axes[0].xaxis.set_major_formatter(PercentFormatter(1))
    for ax in axes[1:]:
        ax.tick_params(axis="y", left=False, labelleft=False)

    fig.suptitle("Medication coverage by payer and age",
                 fontsize=21, fontweight="bold", color=INK)
    fig.supxlabel("Share of medication costs · Single-dispense records in the Synthea sample",
                  fontsize=10, color=MUTED)
    handles, legend_labels = axes[0].get_legend_handles_labels()
    legend_ax.legend(handles, legend_labels, loc="center", ncol=2,
                     frameon=False, labelcolor=INK)
    return fig


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-dir", type=Path, default=SAMPLE_DIR)
    parser.add_argument("--output", type=Path, help="Save to this path instead of opening a window.")
    args = parser.parse_args()
    figure = plot_coverage(args.sample_dir)
    if args.output:
        figure.savefig(args.output, dpi=360)
    else:
        plt.show()
