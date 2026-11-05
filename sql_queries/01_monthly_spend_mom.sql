-- 01_monthly_spend_mom.sql
-- Computes monthly total spend, active instance count, and Month-over-Month (MoM) growth percentage using LAG().

WITH monthly_summary AS (
    SELECT 
        SUBSTR(usage_date, 1, 7) AS billing_month,
        COUNT(DISTINCT instance_id) AS active_instances,
        ROUND(SUM(runtime_hours), 1) AS total_runtime_hours,
        ROUND(SUM(total_cost_usd), 2) AS monthly_spend_usd
    FROM ec2_instance_daily_costs
    GROUP BY SUBSTR(usage_date, 1, 7)
),
mom_calculation AS (
    SELECT
        billing_month,
        active_instances,
        total_runtime_hours,
        monthly_spend_usd,
        LAG(monthly_spend_usd, 1) OVER (ORDER BY billing_month) AS prev_month_spend_usd
    FROM monthly_summary
)
SELECT 
    billing_month,
    active_instances,
    total_runtime_hours,
    monthly_spend_usd,
    COALESCE(prev_month_spend_usd, 0.0) AS prev_month_spend_usd,
    ROUND(monthly_spend_usd - COALESCE(prev_month_spend_usd, monthly_spend_usd), 2) AS mom_dollar_change,
    ROUND(
        CASE 
            WHEN prev_month_spend_usd IS NULL OR prev_month_spend_usd = 0 THEN 0.0
            ELSE ((monthly_spend_usd - prev_month_spend_usd) / prev_month_spend_usd) * 100.0
        END, 2
    ) AS mom_growth_pct
FROM mom_calculation
ORDER BY billing_month ASC;

