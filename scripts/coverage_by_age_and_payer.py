"""Query weighted medication coverage by age group and payer in Spark."""


def query_coverage_by_age_and_payer(spark):
    """Return one row per age-at-medication-start group and payer ID."""
    return spark.sql("""
        WITH coverage_totals AS (
            SELECT
                age_group,
                payer_id,
                COUNT(*) AS medication_records,
                SUM(total_cost) AS total_medication_cost,
                SUM(payer_coverage) AS total_payer_coverage
            FROM fact_medications
            GROUP BY age_group, payer_id
        )
        SELECT
            totals.age_group,
            totals.payer_id,
            payers.payer_name,
            totals.medication_records,
            totals.total_medication_cost,
            totals.total_payer_coverage,
            totals.total_payer_coverage / NULLIF(totals.total_medication_cost, 0)
                AS coverage_proportion
        FROM coverage_totals AS totals
        LEFT JOIN dim_payers AS payers
            ON totals.payer_id = payers.payer_id
        ORDER BY
            CASE totals.age_group
                WHEN 'Under 18' THEN 1
                WHEN '18-29' THEN 2
                WHEN '30-44' THEN 3
                WHEN '45-59' THEN 4
                WHEN '60-74' THEN 5
                WHEN '75+' THEN 6
                ELSE 7
            END,
            totals.age_group,
            payers.payer_name,
            totals.payer_id
    """)


if __name__ == "__main__":
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.appName("Coverage by Age and Payer").getOrCreate()
    try:
        query_coverage_by_age_and_payer(spark).show(100, truncate=False)
    finally:
        spark.stop()
