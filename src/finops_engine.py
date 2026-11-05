"""
FinOps Engine: Runs SQL analyses, aggregates KPIs, and produces structured dataframes
for dashboard rendering and Excel exports.
"""

import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "finops.db")
SQL_DIR = os.path.join(BASE_DIR, "sql_queries")

def get_connection():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}. Please run generate_data.py first.")
    return sqlite3.connect(DB_PATH)

def load_sql_query(filename: str) -> str:
    filepath = os.path.join(SQL_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def run_finops_analysis():
    conn = get_connection()
    
    # 1. Executive Summary KPIs
    kpi_query = """
    SELECT 
        ROUND(SUM(total_cost_usd), 2) AS total_spend_usd,
        COUNT(DISTINCT instance_id) AS total_instances,
        COUNT(DISTINCT project_name) AS total_projects,
        ROUND(AVG(avg_cpu_utilization_pct), 2) AS fleet_avg_cpu,
        ROUND(SUM(runtime_hours), 1) AS total_runtime_hours
    FROM ec2_instance_daily_costs;
    """
    df_kpi = pd.read_sql_query(kpi_query, conn)
    
    # 2. Monthly Spend & MoM
    sql_monthly = load_sql_query("01_monthly_spend_mom.sql")
    df_monthly = pd.read_sql_query(sql_monthly, conn)
    
    # 3. Cost by Instance Family
    sql_family = load_sql_query("02_cost_by_instance_family.sql")
    df_family = pd.read_sql_query(sql_family, conn)
    
    # 4. Idle / Zombie Instances
    sql_idle = load_sql_query("03_idle_resources_zombies.sql")
    df_idle = pd.read_sql_query(sql_idle, conn)
    
    # 5. Cost Anomalies
    sql_anomalies = load_sql_query("04_cost_anomalies_zscore.sql")
    df_anomalies = pd.read_sql_query(sql_anomalies, conn)
    
    # 6. Rightsizing & Savings Plan Opportunities
    sql_savings = load_sql_query("05_rightsizing_savings.sql")
    df_savings = pd.read_sql_query(sql_savings, conn)
    
    # 7. Spend by Environment & Pricing Model
    env_query = """
    SELECT 
        environment,
        pricing_model,
        ROUND(SUM(total_cost_usd), 2) AS total_spend_usd,
        ROUND(AVG(avg_cpu_utilization_pct), 2) AS avg_cpu_pct
    FROM ec2_instance_daily_costs
    GROUP BY environment, pricing_model
    ORDER BY total_spend_usd DESC;
    """
    df_env_pricing = pd.read_sql_query(env_query, conn)

    # 8. Team spend breakdown
    team_query = """
    SELECT 
        team,
        ROUND(SUM(total_cost_usd), 2) AS team_spend_usd,
        ROUND((SUM(total_cost_usd) / (SELECT SUM(total_cost_usd) FROM ec2_instance_daily_costs)) * 100.0, 2) AS pct_of_budget
    FROM ec2_instance_daily_costs
    GROUP BY team
    ORDER BY team_spend_usd DESC;
    """
    df_team = pd.read_sql_query(team_query, conn)

    conn.close()
    
    # Compute high-level actionable savings
    total_spend = df_kpi["total_spend_usd"].iloc[0]
    total_idle_waste = df_idle["cumulative_waste_cost_usd"].sum() if not df_idle.empty else 0.0
    total_rightsizing_potential = df_savings["estimated_potential_savings_usd"].sum() if not df_savings.empty else 0.0
    combined_potential_savings = total_idle_waste + total_rightsizing_potential
    savings_roi_pct = round((combined_potential_savings / total_spend) * 100.0, 1)

    summary_metrics = {
        "total_spend_usd": total_spend,
        "total_instances": int(df_kpi["total_instances"].iloc[0]),
        "total_projects": int(df_kpi["total_projects"].iloc[0]),
        "fleet_avg_cpu": df_kpi["fleet_avg_cpu"].iloc[0],
        "total_idle_waste_usd": round(total_idle_waste, 2),
        "total_rightsizing_potential_usd": round(total_rightsizing_potential, 2),
        "total_potential_savings_usd": round(combined_potential_savings, 2),
        "savings_roi_pct": savings_roi_pct,
    }

    return {
        "metrics": summary_metrics,
        "monthly": df_monthly,
        "family": df_family,
        "idle": df_idle,
        "anomalies": df_anomalies,
        "savings": df_savings,
        "env_pricing": df_env_pricing,
        "team": df_team
    }

if __name__ == "__main__":
    results = run_finops_analysis()
    print("=== FinOps Analysis Engine Test Run ===")
    for k, v in results["metrics"].items():
        print(f" - {k}: {v}")
    print(f"Monthly Records: {len(results['monthly'])}")
    print(f"Zombie/Idle Instances Identified: {len(results['idle'])}")
    print(f"Cost Anomalies Flagged: {len(results['anomalies'])}")

