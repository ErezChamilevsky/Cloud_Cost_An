"""
AWS EC2 Cost & Usage Synthetic Data Generator
Generates realistic multi-month cloud billing and utilization records
and stores them into a SQLite database.
"""

import os
import random
import sqlite3
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "finops.db")

# Realistic instance specs with on-demand hourly rates (USD)
INSTANCE_CATALOG = {
    "t3.nano": {"family": "General Purpose (Burstable)", "hourly_rate": 0.0052, "vcpus": 2, "memory_gib": 0.5},
    "t3.medium": {"family": "General Purpose (Burstable)", "hourly_rate": 0.0416, "vcpus": 2, "memory_gib": 4.0},
    "m5.large": {"family": "General Purpose", "hourly_rate": 0.096, "vcpus": 2, "memory_gib": 8.0},
    "m5.xlarge": {"family": "General Purpose", "hourly_rate": 0.192, "vcpus": 4, "memory_gib": 16.0},
    "m5.2xlarge": {"family": "General Purpose", "hourly_rate": 0.384, "vcpus": 8, "memory_gib": 32.0},
    "c5.xlarge": {"family": "Compute Optimized", "hourly_rate": 0.17, "vcpus": 4, "memory_gib": 8.0},
    "c5.2xlarge": {"family": "Compute Optimized", "hourly_rate": 0.34, "vcpus": 8, "memory_gib": 16.0},
    "r5.xlarge": {"family": "Memory Optimized", "hourly_rate": 0.252, "vcpus": 4, "memory_gib": 32.0},
    "r5.2xlarge": {"family": "Memory Optimized", "hourly_rate": 0.504, "vcpus": 8, "memory_gib": 64.0},
    "r5.4xlarge": {"family": "Memory Optimized", "hourly_rate": 1.008, "vcpus": 16, "memory_gib": 128.0},
    "p3.2xlarge": {"family": "Accelerated Computing (GPU)", "hourly_rate": 3.06, "vcpus": 8, "memory_gib": 61.0},
}

SERVICES_PROJECTS = [
    {"project_name": "checkout-service", "environment": "Production", "team": "E-Commerce", "default_pricing": "On-Demand"},
    {"project_name": "payment-gateway", "environment": "Production", "team": "Fintech", "default_pricing": "Savings Plan"},
    {"project_name": "catalog-search", "environment": "Production", "team": "Search & Recs", "default_pricing": "Reserved Instance"},
    {"project_name": "data-pipeline-etl", "environment": "Production", "team": "Data Eng", "default_pricing": "On-Demand"},
    {"project_name": "ml-training-lab", "environment": "Development", "team": "Data Science", "default_pricing": "On-Demand"},
    {"project_name": "qa-loadtest-runner", "environment": "Staging", "team": "QA", "default_pricing": "On-Demand"},
    {"project_name": "customer-portal", "environment": "Production", "team": "Web", "default_pricing": "Savings Plan"},
    {"project_name": "dev-sandbox-legacy", "environment": "Development", "team": "Legacy Ops", "default_pricing": "On-Demand"},
    {"project_name": "devops-monitoring", "environment": "Production", "team": "Infra", "default_pricing": "Reserved Instance"},
    {"project_name": "batch-processor-old", "environment": "Staging", "team": "Data Eng", "default_pricing": "On-Demand"},
]

REGIONS = ["us-east-1", "us-west-2", "eu-west-1"]

def init_db(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ec2_instance_daily_costs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usage_date TEXT NOT NULL,
        instance_id TEXT NOT NULL,
        project_name TEXT NOT NULL,
        environment TEXT NOT NULL,
        team TEXT NOT NULL,
        region TEXT NOT NULL,
        instance_type TEXT NOT NULL,
        instance_family TEXT NOT NULL,
        pricing_model TEXT NOT NULL,
        runtime_hours REAL NOT NULL,
        avg_cpu_utilization_pct REAL NOT NULL,
        max_cpu_utilization_pct REAL NOT NULL,
        effective_hourly_rate REAL NOT NULL,
        total_cost_usd REAL NOT NULL
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON ec2_instance_daily_costs(usage_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_project ON ec2_instance_daily_costs(project_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_instance ON ec2_instance_daily_costs(instance_id);")
    conn.commit()

def generate_finops_dataset(days: int = 180):
    random.seed(42)
    start_date = datetime(2026, 5, 1) # ~6 months of continuous daily records
    
    # Pre-define a fleet of 50 instances
    fleet = []
    for i in range(1, 51):
        inst_id = f"i-0{random.randint(10000000, 99999999):x}"[:10]
        proj_meta = random.choice(SERVICES_PROJECTS)
        
        # Determine instance archetype for FinOps realism
        if proj_meta["project_name"] == "dev-sandbox-legacy" or proj_meta["project_name"] == "batch-processor-old":
            # Scenario 1: Zombie / Idle expensive machines
            inst_type = random.choice(["r5.4xlarge", "m5.2xlarge", "c5.2xlarge"])
            archetype = "zombie"
        elif proj_meta["project_name"] == "ml-training-lab":
            # Scenario 2: GPU batch with occasional huge spikes
            inst_type = "p3.2xlarge"
            archetype = "gpu_burst"
        elif proj_meta["environment"] == "Production" and proj_meta["project_name"] == "data-pipeline-etl":
            # Scenario 3: Heavy uncommitted On-Demand workload (prime for Savings Plan)
            inst_type = random.choice(["r5.2xlarge", "c5.2xlarge", "m5.xlarge"])
            archetype = "steady_ondemand"
        elif proj_meta["environment"] == "Development":
            inst_type = random.choice(["t3.medium", "m5.large"])
            archetype = "dev_normal"
        else:
            inst_type = random.choice(["t3.medium", "m5.large", "m5.xlarge", "c5.xlarge"])
            archetype = "prod_committed"

        fleet.append({
            "instance_id": inst_id,
            "project_name": proj_meta["project_name"],
            "environment": proj_meta["environment"],
            "team": proj_meta["team"],
            "region": random.choice(REGIONS),
            "instance_type": inst_type,
            "family": INSTANCE_CATALOG[inst_type]["family"],
            "pricing_model": proj_meta["default_pricing"],
            "archetype": archetype,
            "base_rate": INSTANCE_CATALOG[inst_type]["hourly_rate"],
        })

    records = []
    
    for day_offset in range(days):
        current_date = (start_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        
        # Detect anomaly period (e.g. Days 110 - 114: Cloud Anomaly / Memory Leak / Runaway ETL)
        is_incident_week = (110 <= day_offset <= 114)

        for inst in fleet:
            pricing = inst["pricing_model"]
            rate = inst["base_rate"]
            
            # Apply standard discount factors for RI & Savings Plans
            if pricing == "Reserved Instance":
                rate *= 0.65  # ~35% discount
            elif pricing == "Savings Plan":
                rate *= 0.72  # ~28% discount
            
            runtime = 24.0
            
            if inst["archetype"] == "zombie":
                # Running 24 hours a day, but CPU is completely dead (< 4%)
                avg_cpu = round(random.uniform(1.2, 4.8), 2)
                max_cpu = round(avg_cpu + random.uniform(1.0, 3.0), 2)
            
            elif inst["archetype"] == "gpu_burst":
                # Runs sporadic hours or bursts
                if random.random() < 0.4:
                    runtime = round(random.uniform(4.0, 14.0), 1)
                    avg_cpu = round(random.uniform(45.0, 85.0), 2)
                    max_cpu = round(random.uniform(85.0, 99.0), 2)
                else:
                    runtime = 0.0
                    avg_cpu = 0.0
                    max_cpu = 0.0
            
            elif inst["archetype"] == "steady_ondemand":
                # Continuous baseline production load on on-demand
                avg_cpu = round(random.uniform(45.0, 68.0), 2)
                max_cpu = round(random.uniform(70.0, 92.0), 2)
                
                # Check for anomaly injection
                if is_incident_week and inst["instance_type"] == "r5.2xlarge":
                    # Anomaly: CPU pegged at 98%, instance runs at maximum rate, duplicate charges
                    avg_cpu = 98.5
                    max_cpu = 100.0
                    rate *= 1.8  # Simulating cross-AZ transfer or premium burst addon
            
            elif inst["archetype"] == "dev_normal":
                # Dev instances run mostly during working hours (e.g. 10 hours) or 24h if forgotten
                runtime = 24.0 if random.random() < 0.3 else 10.0
                avg_cpu = round(random.uniform(8.0, 25.0), 2)
                max_cpu = round(random.uniform(25.0, 50.0), 2)
            
            else:
                # Standard production
                avg_cpu = round(random.uniform(35.0, 75.0), 2)
                max_cpu = round(random.uniform(65.0, 95.0), 2)
            
            total_cost = round(runtime * rate, 4)
            
            if runtime > 0:
                records.append((
                    current_date,
                    inst["instance_id"],
                    inst["project_name"],
                    inst["environment"],
                    inst["team"],
                    inst["region"],
                    inst["instance_type"],
                    inst["family"],
                    pricing,
                    runtime,
                    avg_cpu,
                    max_cpu,
                    round(rate, 4),
                    total_cost
                ))
                
    return records

def populate_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    
    print("Generating synthetic AWS FinOps usage & cost dataset...")
    records = generate_finops_dataset(days=180)
    
    cursor = conn.cursor()
    cursor.executemany("""
    INSERT INTO ec2_instance_daily_costs (
        usage_date, instance_id, project_name, environment, team,
        region, instance_type, instance_family, pricing_model,
        runtime_hours, avg_cpu_utilization_pct, max_cpu_utilization_pct,
        effective_hourly_rate, total_cost_usd
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)
    
    conn.commit()
    count = cursor.execute("SELECT COUNT(*) FROM ec2_instance_daily_costs").fetchone()[0]
    total_spend = cursor.execute("SELECT ROUND(SUM(total_cost_usd), 2) FROM ec2_instance_daily_costs").fetchone()[0]
    conn.close()
    
    print(f"Dataset successfully created in {DB_PATH}")
    print(f"Total Rows: {count:,} records across 180 days.")
    print(f"Total Simulated AWS Spend: ${total_spend:,.2f}")

if __name__ == "__main__":
    populate_database()

