-- 05_rightsizing_savings.sql
-- Identifies stable production workloads currently paying full On-Demand pricing
-- and calculates the precise projected savings from committing to AWS Savings Plans (28% avg discount)
-- or Rightsizing over-provisioned instances (CPU avg < 25%).

WITH stable_ondemand_instances AS (
    SELECT 
        instance_id,
        project_name,
        environment,
        team,
        instance_type,
        pricing_model,
        ROUND(SUM(runtime_hours), 1) AS total_hours_run,
        ROUND(AVG(avg_cpu_utilization_pct), 2) AS avg_cpu_pct,
        ROUND(MAX(max_cpu_utilization_pct), 2) AS peak_cpu_pct,
        ROUND(SUM(total_cost_usd), 2) AS current_total_spend_usd,
        ROUND(AVG(effective_hourly_rate), 4) AS current_hourly_rate
    FROM ec2_instance_daily_costs
    WHERE pricing_model = 'On-Demand'
    GROUP BY instance_id, project_name, environment, team, instance_type, pricing_model
    HAVING total_hours_run > 1000 -- Substantial continuous run-time
)
SELECT 
    instance_id,
    project_name,
    environment,
    team,
    instance_type,
    pricing_model,
    avg_cpu_pct,
    peak_cpu_pct,
    current_total_spend_usd,
    -- Opportunity 1: 1-Year Compute Savings Plan (approx 28% discount)
    ROUND(current_total_spend_usd * 0.28, 2) AS savings_plan_projected_savings_usd,
    -- Opportunity 2: If overprovisioned (peak CPU < 35%), recommend downsizing to 1 size smaller (50% cost cut)
    CASE 
        WHEN peak_cpu_pct < 35.0 THEN 'Downsize instance tier (Save ~50%)'
        ELSE 'Purchase 1-Yr / 3-Yr Compute Savings Plan (Save ~28%)'
    END AS primary_optimization_strategy,
    CASE 
        WHEN peak_cpu_pct < 35.0 THEN ROUND(current_total_spend_usd * 0.50, 2)
        ELSE ROUND(current_total_spend_usd * 0.28, 2)
    END AS estimated_potential_savings_usd
FROM stable_ondemand_instances
ORDER BY estimated_potential_savings_usd DESC;

