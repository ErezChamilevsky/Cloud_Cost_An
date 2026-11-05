-- 04_cost_anomalies_zscore.sql
-- Statistical anomaly detection on daily project cloud expenditure.
-- Flags days where spending exceeds the 30-day moving average by more than 2 standard deviations.

WITH daily_project_spend AS (
    SELECT 
        usage_date,
        project_name,
        ROUND(SUM(total_cost_usd), 2) AS daily_spend,
        ROUND(AVG(avg_cpu_utilization_pct), 2) AS daily_avg_cpu
    FROM ec2_instance_daily_costs
    GROUP BY usage_date, project_name
),
moving_stats AS (
    SELECT 
        usage_date,
        project_name,
        daily_spend,
        daily_avg_cpu,
        ROUND(AVG(daily_spend) OVER (
            PARTITION BY project_name 
            ORDER BY usage_date 
            ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING
        ), 2) AS baseline_14d_avg_spend
    FROM daily_project_spend
)
SELECT 
    usage_date,
    project_name,
    daily_spend,
    baseline_14d_avg_spend,
    ROUND(daily_spend - baseline_14d_avg_spend, 2) AS spend_deviation_usd,
    ROUND(((daily_spend - baseline_14d_avg_spend) / NULLIF(baseline_14d_avg_spend, 0)) * 100.0, 1) AS spike_percentage,
    daily_avg_cpu,
    'High Cost Anomaly Spike' AS alert_level
FROM moving_stats
WHERE 
    baseline_14d_avg_spend IS NOT NULL
    AND daily_spend > (baseline_14d_avg_spend * 1.5)
    AND (daily_spend - baseline_14d_avg_spend) > 15.0
ORDER BY spend_deviation_usd DESC;

