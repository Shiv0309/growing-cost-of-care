"""Save medication coverage by age and payer for the local Synthea sample."""

import argparse
import calendar
import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SAMPLE_DIR = DATA_DIR / "synthea_sample_data_csv_latest"
OUTPUT_FILE = DATA_DIR / "sample_coverage_by_age_and_payer.csv"
AGE_GROUPS = ("Under 18", "18-29", "30-44", "45-59", "60-74", "75+", "Invalid Age", "Unknown")


@dataclass
class CoverageTotals:
    records: int = 0
    cost: Decimal | None = None
    coverage: Decimal | None = None

    def add(self, medication):
        self.records += 1
        if medication["TOTALCOST"]:
            self.cost = (self.cost or Decimal(0)) + Decimal(medication["TOTALCOST"])
        if medication["PAYER_COVERAGE"]:
            self.coverage = (self.coverage or Decimal(0)) + Decimal(medication["PAYER_COVERAGE"])


def age_group(birth_date, start_date, labels=AGE_GROUPS[:6],
              cutoffs=(18, 30, 45, 60, 75)):
    if not birth_date or not start_date:
        return "Unknown"
    birth = date.fromisoformat(birth_date)
    start = date.fromisoformat(start_date[:10])
    # Match Spark add_months, which clips leap-day birthdays to February 28.
    last_day = calendar.monthrange(start.year, birth.month)[1]
    birthday = date(start.year, birth.month, min(birth.day, last_day))
    age = start.year - birth.year - (start < birthday)
    if age < 0:
        return "Invalid Age"
    for upper_bound, label in zip(cutoffs, labels):
        if age < upper_bound:
            return label
    return labels[-1]


def coverage_totals(
    sample_dir, labels=AGE_GROUPS[:6], cutoffs=(18, 30, 45, 60, 75), *,
    single_dispense_only=False,
):
    with (sample_dir / "patients.csv").open(encoding="utf-8-sig", newline="") as source:
        births = {row["Id"]: row["BIRTHDATE"] for row in csv.DictReader(source)}
    with (sample_dir / "payers.csv").open(encoding="utf-8-sig", newline="") as source:
        payers = {row["Id"]: row["NAME"] for row in csv.DictReader(source)}

    groups = defaultdict(CoverageTotals)
    with (sample_dir / "medications.csv").open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            if single_dispense_only and row["DISPENSES"] != "1":
                continue
            patient_id = row["PATIENT"]
            if patient_id in births:
                group = age_group(births[patient_id], row["START"], labels, cutoffs)
                groups[group, row["PAYER"]].add(row)

    return groups, payers


def aggregate(sample_dir, output):
    groups, payers = coverage_totals(sample_dir)
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow([
        "age_group", "payer_id", "payer_name", "medication_records",
        "total_medication_cost", "total_payer_coverage", "coverage_proportion",
    ])
    for group, payer in sorted(
        groups, key=lambda key: (AGE_GROUPS.index(key[0]), payers.get(key[1], ""), key[1])
    ):
        totals = groups[group, payer]
        proportion = None
        if totals.cost and totals.coverage is not None:
            proportion = totals.coverage / totals.cost
        writer.writerow([
            group, payer, payers.get(payer), totals.records,
            totals.cost, totals.coverage, proportion,
        ])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-dir", type=Path, default=SAMPLE_DIR)
    args = parser.parse_args()
    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as output:
        aggregate(args.sample_dir, output)
