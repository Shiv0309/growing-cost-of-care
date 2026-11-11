# The Growing Cost of Care — Data Dictionary

## Project Overview

This project uses synthetic healthcare data from Synthea to explore medication utilization, recorded insurance contributions, and calculated uncovered medication costs across patient age groups and medication histories.

The data pipeline consists of:
- **Source layer:** Original Synthea tables.
- **Silver layer:** Cleaned and enriched medication records.
- **Gold layer:** Dimension tables, a medication fact table, and aggregated analytical tables designed for visualization.

### Important Methodology Notes

- The dataset is synthetic and does not represent actual patient claims or insurance outcomes.
- Calculated uncovered cost is defined as `total_cost - payer_coverage`. It should not be interpreted as verified patient out-of-pocket spending.
- Medication records span historical dates. Medication counts and distinct medication types represent available historical records, not necessarily medications taken simultaneously.
- Age groups are based on age at medication start, not current age.
- Coverage percentages are weighted: total payer coverage divided by total medication cost.
- Findings describe associations within this synthetic dataset and should not be interpreted as causal relationships.

---

# 1. Silver Layer

## 1.1 silver_medications

**Purpose:** Cleaned medication-level dataset enriched with demographic and geographic information from the patient table.

**Grain:** One row per medication record.

**Rows:** 4,227,723

**Source:** `dbo_1.medications` joined with `dbo_1.patients` using medication `PATIENT` and patient `Id`.

| Column | Description | Calculation / Source |
|---|---|---|
| patient_id | Unique patient identifier | Source patient ID |
| medication_start | Medication start date | Source `START` |
| medication_stop | Medication end date | Source `STOP` |
| payer_id | Identifier for the payer | Source `PAYER` |
| encounter_id | Associated healthcare encounter | Source `ENCOUNTER` |
| medication_code | Standardized medication code | Source `CODE` |
| medication_description | Medication name or description | Source `DESCRIPTION` |
| base_cost | Base medication cost | Source `BASE_COST` |
| payer_coverage | Amount contributed by payer | Source `PAYER_COVERAGE` |
| total_cost | Total medication cost | Source `TOTALCOST` |
| dispenses | Number of medication dispensings | Source `DISPENSES` |
| reason_code | Code describing the reason for medication | Source `REASONCODE` |
| reason_description | Description of the medication reason | Source `REASONDESCRIPTION` |
| birth_date | Patient's date of birth | Source patient `BIRTHDATE` |
| death_date | Patient's date of death, if available | Source patient `DEATHDATE` |
| gender | Patient gender | Source patient `GENDER` |
| race | Patient race | Source patient `RACE` |
| ethnicity | Patient ethnicity | Source patient `ETHNICITY` |
| city | Patient city | Source patient location |
| state | Patient state | Source patient location |
| county | Patient county | Source patient location |
| age_at_medication_start | Patient age when medication began | Calculated from birth date and medication start date |
| age_group | Age category at medication start | Derived using project-defined age ranges |
| calculated_uncovered_cost | Portion of medication cost not covered by payer | `total_cost - payer_coverage` |

**Age groups:** Under 18, 18–29, 30–44, 45–59, 60–74, and 75+.

**Data handling:** Direct identifiers such as patient names, SSNs, driver's license numbers, and full addresses were excluded.

## 1.2 silver_medications_enriched

**Purpose:** Adds payer names to the cleaned medication records to make downstream analysis and reporting easier.

**Grain:** One row per medication record.

**Rows:** 4,227,723

**Source:** `silver_medications` left joined with `dbo_1.payers` using `payer_id = Id`.

| Column | Description | Calculation / Source |
|---|---|---|
| All 24 columns from `silver_medications` | Cleaned medication, demographic, geographic, age, and cost information | Inherited from `silver_medications` |
| payer_name | Name of the insurance payer | Joined from `dbo_1.payers` |

**Note:** The payer lookup contains 10 payer records. The left join preserves medication records even if a matching payer is unavailable.

---

# 2. Gold Layer — Dimension and Fact Tables

## 2.1 dim_patients

**Purpose:** Stores patient-level demographic and geographic information for analytical joins.

**Grain:** One row per patient.

**Rows:** 124,150

**Source:** `dbo_1.patients`.

| Column | Description | Calculation / Source |
|---|---|---|
| patient_id | Unique patient identifier | Source `Id`; primary key |
| birth_date | Patient date of birth | Source `BIRTHDATE` |
| death_date | Patient date of death, if available | Source `DEATHDATE` |
| gender | Patient gender | Source `GENDER` |
| race | Patient race | Source `RACE` |
| ethnicity | Patient ethnicity | Source `ETHNICITY` |
| city | Patient city | Source location |
| state | Patient state | Source location |
| county | Patient county | Source location |

**Note:** This table includes all 124,150 patients, including patients without medication records.

## 2.2 dim_payers

**Purpose:** Stores payer information for joining payer identifiers to readable payer names.

**Grain:** One row per payer.

**Rows:** 10

**Source:** `dbo_1.payers`.

| Column | Description | Calculation / Source |
|---|---|---|
| payer_id | Unique payer identifier | Source `Id`; primary key |
| payer_name | Name of the payer | Source `NAME` |

## 2.3 fact_medications

**Purpose:** Central medication-level fact table used for analytical queries and dashboard development.

**Grain:** One row per medication record.

**Rows:** 4,227,723

**Source:** `silver_medications_enriched`.

| Column | Description | Calculation / Source |
|---|---|---|
| patient_id | Patient associated with the medication | From Silver; foreign key to `dim_patients` |
| payer_id | Payer associated with the medication | From Silver; foreign key to `dim_payers` |
| encounter_id | Associated healthcare encounter | From Silver |
| medication_code | Medication code | From Silver |
| medication_description | Medication description | From Silver |
| medication_start | Medication start date | From Silver |
| medication_stop | Medication end date | From Silver |
| age_at_medication_start | Patient age when medication began | From Silver |
| age_group | Patient age category at medication start | From Silver |
| base_cost | Base medication cost | From Silver |
| total_cost | Total medication cost | From Silver |
| payer_coverage | Recorded payer contribution | From Silver |
| calculated_uncovered_cost | Remaining calculated medication cost | `total_cost - payer_coverage` |
| dispenses | Number of medication dispensings | From Silver |
| reason_code | Reason for medication | From Silver |
| reason_description | Description of medication reason | From Silver |

**Relationships:**
- `dim_patients.patient_id` → `fact_medications.patient_id`
- `dim_payers.payer_id` → `fact_medications.payer_id`

---

# 3. Gold Layer — Aggregated Analytical Tables

## 3.1 agg_medication_by_age

**Purpose:** Analyzes medication utilization and average medication costs across age groups.

**Grain:** One row per age group.

**Rows:** 6

**Source:** `fact_medications`.

| Column | Description | Calculation |
|---|---|---|
| age_group | Patient age category at medication start | Grouped from `age_group` |
| medication_records | Total medication records in the age group | `COUNT(*)` |
| unique_patients | Number of distinct patients represented | `COUNT(DISTINCT patient_id)` |
| total_dispenses | Total number of medication dispensings | `SUM(dispenses)` |
| avg_medication_cost | Average medication cost per record | `AVG(total_cost)` |
| avg_medication_records_per_patient | Average medication records per represented patient | `COUNT(*) / COUNT(DISTINCT patient_id)` |

**Note:** A patient may appear in multiple age groups if their medication history spans multiple life stages.

## 3.2 agg_coverage_by_payer

**Purpose:** Compares recorded payer contributions and calculated uncovered medication costs across insurance payers.

**Grain:** One row per payer.

**Rows:** 10

**Source:** `fact_medications` joined with `dim_payers`.

| Column | Description | Calculation |
|---|---|---|
| payer_id | Unique payer identifier | From `dim_payers` |
| payer_name | Name of payer | From `dim_payers` |
| medication_records | Number of medication records associated with payer | `COUNT(*)` |
| unique_patients | Number of distinct patients associated with payer | `COUNT(DISTINCT patient_id)` |
| total_medication_cost | Total medication cost associated with payer | `SUM(total_cost)` |
| total_payer_coverage | Total recorded payer contributions | `SUM(payer_coverage)` |
| total_calculated_uncovered_cost | Total remaining calculated medication cost | `SUM(calculated_uncovered_cost)` |
| coverage_percentage | Percentage of total medication costs covered by payer contributions | `(SUM(payer_coverage) / SUM(total_cost)) * 100` |

**Note:** Coverage percentage is weighted across all medication records, not an average of individual record-level percentages.

## 3.3 agg_coverage_by_age

**Purpose:** Examines how recorded payer contributions and calculated uncovered costs vary across patient age groups.

**Grain:** One row per age group.

**Rows:** 6

**Source:** `fact_medications`.

| Column | Description | Calculation |
|---|---|---|
| age_group | Patient age category at medication start | Grouped from `age_group` |
| medication_records | Number of medication records in age group | `COUNT(*)` |
| unique_patients | Number of distinct patients represented | `COUNT(DISTINCT patient_id)` |
| total_medication_cost | Total medication cost | `SUM(total_cost)` |
| total_payer_coverage | Total recorded payer contributions | `SUM(payer_coverage)` |
| total_calculated_uncovered_cost | Total remaining calculated medication cost | `SUM(calculated_uncovered_cost)` |
| coverage_percentage | Weighted percentage of medication costs covered | `(SUM(payer_coverage) / SUM(total_cost)) * 100` |
| avg_calculated_uncovered_per_patient | Average calculated uncovered cost per represented patient | `SUM(calculated_uncovered_cost) / COUNT(DISTINCT patient_id)` |

**Note:** The average is calculated within each age group's medication records. Patients may be represented in multiple age groups.

## 3.4 agg_patient_medication_burden

**Purpose:** Summarizes medication utilization and calculated medication costs at the individual patient level.

**Grain:** One row per patient with at least one medication record.

**Rows:** 95,529

**Source:** `fact_medications`.

| Column | Description | Calculation |
|---|---|---|
| patient_id | Unique patient identifier | From `fact_medications` |
| medication_records | Total medication records associated with patient | `COUNT(*)` |
| distinct_medication_count | Number of distinct medication types associated with patient | `COUNT(DISTINCT medication_code)` |
| total_medication_cost | Total medication cost across patient's records | `SUM(total_cost)` |
| total_payer_coverage | Total recorded payer contributions across patient's records | `SUM(payer_coverage)` |
| total_calculated_uncovered_cost | Total calculated uncovered cost across patient's records | `SUM(calculated_uncovered_cost)` |

**Note:** Distinct medication count is based on medication codes across the patient's available historical records, not the number of medications taken simultaneously.

## 3.5 agg_burden_by_med_count

**Purpose:** Examines the relationship between the number of distinct medication types and calculated uncovered medication costs.

**Grain:** One row per medication-count group.

**Rows:** 5

**Source:** `agg_patient_medication_burden`.

| Column | Description | Calculation |
|---|---|---|
| medication_count_group | Group representing the patient's distinct medication count | Categories: 1–2, 3–4, 5–6, 7–8, 9+ |
| unique_patients | Number of patients within group | `COUNT(*)` |
| avg_distinct_medication_count | Average number of distinct medication types | `AVG(distinct_medication_count)` |
| total_medication_cost | Total medication cost across patients in group | `SUM(total_medication_cost)` |
| total_payer_coverage | Total recorded payer contributions | `SUM(total_payer_coverage)` |
| total_calculated_uncovered_cost | Total calculated uncovered cost | `SUM(total_calculated_uncovered_cost)` |
| avg_calculated_uncovered_per_patient | Average calculated uncovered cost per patient | `SUM(total_calculated_uncovered_cost) / COUNT(*)` |
| coverage_percentage | Weighted percentage of medication costs covered | `(SUM(total_payer_coverage) / SUM(total_medication_cost)) * 100` |

**Note:** Medication-count groups are based on distinct medication codes across each patient's available historical records. The relationship between medication variety and calculated uncovered costs is descriptive and does not establish causation.

---

# 4. Table Summary

| Layer | Table | Rows | Grain |
|---|---|---:|---|
| Silver | `silver_medications` | 4,227,723 | Medication record |
| Silver | `silver_medications_enriched` | 4,227,723 | Medication record |
| Gold | `dim_patients` | 124,150 | Patient |
| Gold | `dim_payers` | 10 | Payer |
| Gold | `fact_medications` | 4,227,723 | Medication record |
| Gold | `agg_medication_by_age` | 6 | Age group |
| Gold | `agg_coverage_by_payer` | 10 | Payer |
| Gold | `agg_coverage_by_age` | 6 | Age group |
| Gold | `agg_patient_medication_burden` | 95,529 | Patient with medication records |
| Gold | `agg_burden_by_med_count` | 5 | Medication-count group |

**Project note:** Row counts reflect the current version of the synthetic dataset and may change if the source data or transformation logic is updated.
