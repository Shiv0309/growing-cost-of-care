# The Growing Cost of Care — Methodology

## 1. Project Overview

*The Growing Cost of Care* examines medication utilization, recorded insurance coverage, and calculated uncovered medication costs using synthetic healthcare data.

The central analytical question is:

> As medication utilization increases across age groups and patients use a greater variety of medications, how does recorded insurance coverage compare with the remaining medication costs?

The project uses a medallion architecture to transform source healthcare records into validated, dashboard-ready analytical tables. The pipeline was developed in Microsoft Fabric using PySpark and SQL, with the resulting Gold-layer aggregations intended for visualization in Power BI.

## 2. Data Source and Scope

The project uses synthetic healthcare records generated through the [Synthea Synthetic Patient Population Simulator](https://synthetichealth.github.io/synthea/).

The source data includes patient demographics, medication records, and payer information.

The initial source tables contain:

| Source Table | Records |
|---|---:|
| Patients | 124,150 |
| Medications | 4,227,723 |
| Payers | 10 |

Medication records contain information used to examine medication utilization and associated financial amounts, including medication costs and recorded payer contributions.

The dataset includes historical records spanning multiple decades. Consequently, the analysis represents cumulative historical records rather than annualized healthcare spending.

## 3. Data Architecture

The pipeline follows a medallion architecture with three primary layers: Bronze, Silver, and Gold.

### 3.1 Bronze Layer — Source Data

The Bronze layer contains the original source tables loaded into the `ConnectedCare` Microsoft Fabric Lakehouse.

The source tables provide the foundation for subsequent transformations:

- Patient records
- Medication records
- Payer records

Initial exploration and quality assessment were conducted to understand record counts, date ranges, missing values, duplicate identifiers, referential integrity, and financial data consistency.

### 3.2 Silver Layer — Cleaning and Enrichment

The Silver layer transforms the source medication records into an analysis-ready structure.

Two principal tables were created:

**`silver_medications`**

- Joins medication records with patient demographic information.
- Calculates patient age at medication start.
- Assigns records to age groups.
- Calculates the remaining medication cost after recorded payer coverage.

**`silver_medications_enriched`**

- Builds on the Silver medication table.
- Joins payer information to medication records.
- Adds descriptive payer names for downstream analysis.

The enrichment process preserves the original medication record count.

### 3.3 Gold Layer — Analytical Modeling

The Gold layer contains dimension tables, a medication fact table, and aggregated analytical tables designed to support dashboard development.

**Dimension tables**

- `dim_patients`: Patient-level demographic information.
- `dim_payers`: Payer identifiers and descriptive names.

**Fact table**

- `fact_medications`: Medication-level records enriched with relevant patient, age-group, payer, and financial information.

**Analytical aggregation tables**

| Table | Analytical Purpose |
|---|---|
| `agg_medication_by_age` | Medication utilization across age groups |
| `agg_coverage_by_payer` | Recorded coverage and calculated uncovered costs by payer |
| `agg_coverage_by_age` | Recorded coverage and calculated uncovered costs by age group |
| `agg_patient_medication_burden` | Patient-level summary of distinct medication types and financial burden |
| `agg_burden_by_med_count` | Medication burden grouped by number of distinct medication types |

These Gold tables provide the summarized data needed for the Power BI dashboard.

## 4. Data Transformations and Analytical Definitions

### 4.1 Age at Medication Start

Patient age is calculated using the patient's date of birth and the medication start date.

Age is evaluated at the time the medication record begins rather than using the patient's current age.

The resulting age is assigned to one of six groups:

- Under 18
- 18–29
- 30–44
- 45–59
- 60–74
- 75+

This allows medication utilization and financial measures to be compared across age groups.

### 4.2 Medication Utilization

Medication utilization is examined using medication record counts, distinct patient counts, total dispenses, and average medication records per represented patient.

The average medication records per patient is calculated as:

```text
Average medication records per patient =
Medication records / Distinct patients
```

This is a historical record-based measure and should not be interpreted as the number of medications a patient takes concurrently.

### 4.3 Recorded Payer Coverage and Calculated Uncovered Cost

The project uses three primary financial measures:

**Total medication cost**

The sum of medication costs across the relevant records.

**Total recorded payer coverage**

The sum of payer contributions recorded in the medication data.

**Calculated uncovered cost**

```text
Calculated uncovered cost =
Total medication cost - Payer coverage
```

This measure represents the portion of recorded medication cost not covered by the recorded payer contribution.

It is not a verified measure of actual patient out-of-pocket spending. It may include amounts that are not directly attributable to patient payments.

### 4.4 Weighted Coverage Percentage

Coverage percentage is calculated using aggregate financial totals:

```text
Coverage percentage =
(Total payer coverage / Total medication cost) × 100
```

This weighted calculation is used instead of averaging individual record-level coverage percentages.

It measures the proportion of aggregate medication costs represented by recorded payer contributions.

### 4.5 Average Calculated Uncovered Cost per Patient

For each analytical group:

```text
Average calculated uncovered cost per patient =
Total calculated uncovered cost / Distinct patients
```

This metric is used to compare the average calculated uncovered amount across age groups and medication-burden groups.

### 4.6 Medication Burden

Medication burden is evaluated using the number of distinct medication types associated with each patient across their historical medication records.

Patients are grouped into the following categories:

- 1–2 distinct medication types
- 3–4 distinct medication types
- 5–6 distinct medication types
- 7–8 distinct medication types
- 9 or more distinct medication types

The aggregated results compare patient counts, average distinct medication counts, total medication costs, recorded payer coverage, calculated uncovered costs, and average calculated uncovered cost per patient.

## 5. Data Quality and Validation

Multiple validation checks were performed throughout the pipeline to assess data completeness, consistency, and referential integrity.

### 5.1 Source Data Validation

Initial checks included:

- Source record counts and date ranges.
- Missing-value assessments.
- Duplicate patient identifier checks.
- Medication-to-patient referential integrity.
- Medication-to-payer referential integrity.
- Financial input and cost consistency checks.

Results confirmed that medication records had matching patient identifiers and payer identifiers, with no duplicate patient identifiers detected in the tested source records.

The initial financial validation identified no missing cost inputs, negative total costs, or cases where recorded payer coverage exceeded medication cost.

### 5.2 Silver Layer Validation

The Silver tables were checked for:

- Successful age calculations.
- Valid age-group assignments.
- Missing demographic values.
- Missing or negative financial values.
- Consistency of calculated uncovered costs.

Payer enrichment was also checked to confirm that payer names were populated and that the medication record count was preserved.

### 5.3 Gold Layer Validation and Reconciliation

The Gold layer was validated by comparing aggregated totals with the underlying medication fact records.

The final reconciliation confirmed:

- Distinct patients represented in the medication fact table: **95,529**.
- Patient-level burden summary rows: **95,529**.
- Patients represented across medication burden groups: **95,529**.
- Unknown medication burden groups: **0**.

Financial totals were also reconciled:

- Medication fact total cost: approximately **$11.19 billion**.
- Grouped medication total cost: approximately **$11.19 billion**.
- Medication fact calculated uncovered cost: approximately **$10.77 billion**.
- Grouped medication calculated uncovered cost: approximately **$10.77 billion**.

These checks confirmed consistency between the fact table and its corresponding analytical aggregations.

## 6. Technology Stack

| Technology | Purpose |
|---|---|
| Microsoft Fabric Lakehouse | Data storage and lakehouse architecture |
| PySpark | Data transformation, joins, and processing |
| SQL | Data exploration, aggregation, and validation |
| Python | Exporting dashboard-ready CSV files |
| GitHub | Version control and project documentation |
| Power BI | Dashboard visualization |

## 7. Analytical Limitations

The results should be interpreted within the limitations of the dataset and methodology.

1. **Synthetic data:** The records are generated healthcare data and should not be treated as representative of actual patient populations, insurance plans, or healthcare spending.

2. **Calculated uncovered cost:** The difference between medication cost and recorded payer coverage is not verified patient out-of-pocket spending.

3. **Historical records:** The dataset spans multiple decades. Financial totals are cumulative across the available records and are not annualized.

4. **Historical medication burden:** Distinct medication types reflect historical records and do not establish how many medications a patient was taking simultaneously.

5. **Age-group representation:** Patients may appear in multiple age groups if they have medication records at different ages. Therefore, patient counts across age groups are not mutually exclusive.

6. **Associational analysis:** Observed relationships between medication variety, age, coverage, and calculated uncovered costs are descriptive associations. They do not establish causation.

7. **Synthetic payer values:** Recorded payer contributions may contain artificial or highly uneven patterns. Coverage comparisons should not be generalized to real-world insurance products.

## 8. Reproducibility

The transformation and analytical workflow is documented in the project's Fabric notebook:

`notebooks/Growing_Cost_of_Care_Pipeline.ipynb`

The four primary dashboard-ready Gold aggregation tables are available in:

`data/gold/`

The notebook documents the source exploration, transformations, analytical modeling, and validation steps used to produce the final Gold-layer outputs.
