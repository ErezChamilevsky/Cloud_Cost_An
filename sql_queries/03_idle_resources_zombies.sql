-- 03_idle_resources_zombies.sql
-- Detects "Zombie" instances: instances running continuously with average CPU utilization under 10%.
-- High-priority candidates for termination or scheduled shut-down.

WITH idle_aggregates AS (
    SELECT 
        instance_id,
        project_name,
        environment,
        team,
        instance_type,
        pricing_model,
        COUNT(DISTINCT usage_date) AS active_days,
        ROUND(SUM(runtime_hours), 1) AS total_hours_run,
        ROUND(AVG(avg_cpu_utilization_pct), 2) AS lifetime_avg_cpu_pct,
        ROUND(MAX(max_cpu_utilization_pct), 2) AS lifetime_peak_cpu_pct,
        ROUND(SUM(total_cost_usd), 2) AS cumulative_waste_cost_usd,
        ROUND(AVG(effective_hourly_rate) * 24 * 30, 2) AS estimated_monthly_waste_usd
    FROM ec2_instance_daily_costs
    GROUP BY 
        instance_id, project_name, environment, team, instance_type, pricing_model
    HAVING 
        AVG(avg_cpu_utilization_pct) < 10.0
        AND SUM(runtime_hours) >= 200
)
SELECT 
    instance_id,
    project_name,
    environment,
    team,
    instance_type,
    pricing_model,
    active_days,
    total_hours_run,
    lifetime_avg_cpu_pct,
    lifetime_peak_cpu_pct,
    cumulative_waste_cost_usd,
    estimated_monthly_waste_usd,
    CASE 
        WHEN environment IN ('Development', 'Staging') THEN 'Immediate Termination / Schedule Off-Hours'
        WHEN lifetime_peak_cpu_pct < 15.0 THEN 'Downsize to Burstable (t3/t4g)'
        ELSE 'Review with Service Owner'
    END AS recommendation_action
FROM idle_aggregates
ORDER BY cumulative_waste_cost_usd DESC;
