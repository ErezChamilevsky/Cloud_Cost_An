-- 02_cost_by_instance_family.sql
-- Aggregates AWS spend by instance family and type, calculating proportion of overall cloud budget.

WITH total_budget AS (
    SELECT SUM(total_cost_usd) AS overall_spend FROM ec2_instance_daily_costs
)
SELECT 
    c.instance_family,
    c.instance_type,
    COUNT(DISTINCT c.instance_id) AS distinct_instances,
    ROUND(SUM(c.runtime_hours), 1) AS total_hours_billed,
    ROUND(SUM(c.total_cost_usd), 2) AS total_cost_usd,
    ROUND(AVG(c.avg_cpu_utilization_pct), 2) AS fleet_avg_cpu_pct,
    ROUND((SUM(c.total_cost_usd) / (SELECT overall_spend FROM total_budget)) * 100.0, 2) AS pct_of_total_spend
FROM ec2_instance_daily_costs c
GROUP BY c.instance_family, c.instance_type
ORDER BY total_cost_usd DESC;

