# AWS Cloud Cost Analysis & FinOps Optimization Suite

A Financial Operations (FinOps) analytics project that audits multi-month AWS EC2 compute spend, identifies idle "zombie" infrastructure, detects cost anomalies, and surfaces concrete rightsizing and Savings Plan recommendations.

---

## 🎯 The Business Problem
Modern cloud-native companies suffer from cloud sprawl: oversized development instances left running 24/7, production workloads running on uncommitted On-Demand pricing, and unexpected batch pipeline cost spikes. 

This project simulates a **FinOps Data Analyst** tasked with auditing an enterprise AWS environment to provide actionable financial recommendations to engineering leads and CFOs.

---

## 🛠️ Tech Stack & Architecture
* **Database & SQL:** Embedded SQLite engine running advanced analytical SQL queries (Window functions `LAG()`, rolling 14-day window averages, and conditional aggregation).
* **Data Processing:** Python & Pandas for automated ETL, business logic, and commitment ROI modeling.
* **Executive Deliverables:**
  * **Interactive HTML Dashboard:** Standalone responsive dashboard built with Plotly.js, metric cards, and priority alert tables.
  * **Executive Excel Report:** Multi-tab formatted `.xlsx` workbook with KPI cards, number formatting, and zebra striping.

---

## 📊 Analytical SQL Queries Included

1. **`01_monthly_spend_mom.sql`**
   * Computes monthly aggregate spend and Month-over-Month (MoM) dollar growth / percentage trajectory using `LAG() OVER (ORDER BY billing_month)`.
2. **`02_cost_by_instance_family.sql`**
   * Breaks down expenditure by EC2 family (`m5`, `c5`, `r5`, `t3`, `p3`) and computes the exact percentage of the cloud budget each consumes.
3. **`03_idle_resources_zombies.sql`**
   * Isolates "zombie" servers running with `< 10%` lifetime average CPU utilization, prioritizing development/staging instances for immediate decommission or off-hour scheduling.
4. **`04_cost_anomalies_zscore.sql`**
   * Flags cost spikes where daily service spend exceeds the 14-day rolling baseline by more than 150%, catching runaway jobs and memory leaks.
5. **`05_rightsizing_savings.sql`**
   * Analyzes stable production workloads paying full On-Demand rates and computes concrete savings from 1-Year / 3-Year Compute Savings Plans (28% savings) or downsizing over-provisioned nodes (50% savings).

---

## 🚀 Quick Start (1-Click Pipeline)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Entire Pipeline
```bash
python run_pipeline.py
```

This single command will:
1. Synthesize 180 days of realistic EC2 fleet telemetry into `data/finops.db`.
2. Execute all 5 analytical SQL queries.
3. Generate the interactive dashboard: `reports/finops_dashboard.html`.
4. Generate the formatted Excel workbook: `reports/executive_finops_report.xlsx`.

---

## 📈 Key Findings from the Simulated Audit
* **Total Fleet Spend:** ~$55,400 across 50 EC2 instances and 10 service clusters.
* **Zombie Waste Identified:** ~$26,900 in unmanaged, idle high-spec instances (such as `r5.4xlarge` machines idling in Staging/Dev environments).
* **Commitment Opportunities:** ~$16,200 in potential savings by switching baseline production pipelines to 1-Yr Compute Savings Plans and downsizing low-peak tiers.
* **Total Recoverable Budget:** **~78% potential cloud savings** identified with zero disruption to production SLAs.
