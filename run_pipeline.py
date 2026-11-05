"""
Master FinOps Pipeline Runner
Executes data generation, database seeding, SQL analytical queries,
and exports both the Executive Excel Workbook and the Interactive HTML Dashboard.
"""

import sys
import time
from src.generate_data import populate_database
from src.finops_engine import run_finops_analysis
from src.export_excel import generate_excel_report
from src.generate_dashboard import generate_interactive_dashboard

def main():
    print("=" * 70)
    print("  🚀 STARTING AWS CLOUD COST FINOPS PIPELINE")
    print("=" * 70)
    start_time = time.time()

    # Step 1: Synthesize Data & Seed SQLite
    print("\n[Step 1/4] Generating synthetic multi-month cloud telemetry & seeding SQLite...")
    populate_database()

    # Step 2: Execute Analytical SQL Queries & Compute FinOps Insights
    print("\n[Step 2/4] Executing SQL analytical queries & rightsizing engine...")
    finops_data = run_finops_analysis()
    m = finops_data["metrics"]
    print(f" -> Fleet Spend: ${m['total_spend_usd']:,.2f}")
    print(f" -> Identified Waste (Idle machines): ${m['total_idle_waste_usd']:,.2f}")
    print(f" -> Rightsizing / Savings Plan Potential: ${m['total_rightsizing_potential_usd']:,.2f}")
    print(f" -> Recoverable Budget ROI: {m['savings_roi_pct']}% (${m['total_potential_savings_usd']:,.2f})")

    # Step 3: Export Formatted Executive Excel Workbook
    print("\n[Step 3/4] Generating formatted multi-tab Executive Excel Report...")
    generate_excel_report(finops_data)

    # Step 4: Export Interactive HTML Dashboard
    print("\n[Step 4/4] Building interactive Plotly HTML dashboard...")
    generate_interactive_dashboard(finops_data)

    duration = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"  ✅ FINOPS PIPELINE COMPLETED SUCCESSFULLY IN {duration:.2f}s")
    print("  📁 Reports generated in reports/")
    print("     - reports/finops_dashboard.html (Interactive Browser View)")
    print("     - reports/executive_finops_report.xlsx (Formatted Excel Sheet)")
    print("=" * 70)

if __name__ == "__main__":
    main()

