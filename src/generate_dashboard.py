"""
Interactive HTML FinOps Dashboard Generator
Builds a standalone, responsive, interactive HTML dashboard combining KPI cards,
Plotly charts, and actionable recommendation tables.
"""

import os
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DASHBOARD_PATH = os.path.join(BASE_DIR, "reports", "finops_dashboard.html")

def generate_interactive_dashboard(finops_data: dict):
    m = finops_data["metrics"]
    df_monthly = finops_data["monthly"]
    df_family = finops_data["family"]
    df_idle = finops_data["idle"]
    df_anomalies = finops_data["anomalies"]
    df_team = finops_data["team"]
    df_env = finops_data["env_pricing"]

    # 1. Chart 1: Monthly Spend & MoM Growth
    fig_monthly = make_subplots(specs=[[{"secondary_y": True}]])
    fig_monthly.add_trace(
        go.Bar(
            x=df_monthly["billing_month"],
            y=df_monthly["monthly_spend_usd"],
            name="Monthly Spend ($)",
            marker_color="#1E40AF"
        ),
        secondary_y=False
    )
    fig_monthly.add_trace(
        go.Scatter(
            x=df_monthly["billing_month"],
            y=df_monthly["mom_growth_pct"],
            name="MoM Growth (%)",
            mode="lines+markers+text",
            text=[f"{v:+.1f}%" for v in df_monthly["mom_growth_pct"]],
            textposition="top center",
            line=dict(color="#DC2626", width=3)
        ),
        secondary_y=True
    )
    fig_monthly.update_layout(
        title="<b>Monthly Cloud Spend & MoM Trajectory</b>",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig_monthly.update_yaxes(title_text="Total Spend ($)", secondary_y=False)
    fig_monthly.update_yaxes(title_text="MoM Growth (%)", secondary_y=True)

    # 2. Chart 2: Spend by Instance Family (Donut Chart)
    fig_family = px.pie(
        df_family,
        names="instance_family",
        values="total_cost_usd",
        hole=0.45,
        title="<b>Spend Breakdown by Instance Family</b>",
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    fig_family.update_traces(textposition='inside', textinfo='percent+label')
    fig_family.update_layout(margin=dict(l=20, r=20, t=50, b=20))

    # 3. Chart 3: Spend by Team (Horizontal Bar)
    fig_team = px.bar(
        df_team.sort_values("team_spend_usd", ascending=True),
        x="team_spend_usd",
        y="team",
        orientation="h",
        text="team_spend_usd",
        title="<b>Cloud Spend by Engineering Team</b>",
        color="team_spend_usd",
        color_continuous_scale="Blues"
    )
    fig_team.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
    fig_team.update_layout(
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis_title="Total Spend ($)",
        yaxis_title="",
        coloraxis_showscale=False
    )

    # 4. Chart 4: Pricing Model Distribution by Environment
    fig_env = px.bar(
        df_env,
        x="environment",
        y="total_spend_usd",
        color="pricing_model",
        barmode="stack",
        title="<b>Pricing Model by Environment (Commitment Coverage)</b>",
        color_discrete_map={
            "On-Demand": "#EF4444",
            "Savings Plan": "#10B981",
            "Reserved Instance": "#3B82F6",
            "Spot": "#F59E0B"
        }
    )
    fig_env.update_layout(margin=dict(l=40, r=40, t=50, b=40), yaxis_title="Total Spend ($)")

    # Prepare Top Idle table rows
    idle_table_rows = ""
    for _, row in df_idle.head(8).iterrows():
        idle_table_rows += f"""
        <tr>
            <td style="font-family: monospace; font-weight: 600;">{row['instance_id']}</td>
            <td>{row['project_name']}</td>
            <td><span class="badge {row['environment'].lower()}">{row['environment']}</span></td>
            <td>{row['instance_type']}</td>
            <td style="color: #dc2626; font-weight: 600;">{row['lifetime_avg_cpu_pct']:.1f}%</td>
            <td style="font-weight: 600;">${row['cumulative_waste_cost_usd']:,.2f}</td>
            <td style="font-size: 0.85rem; color: #4b5563;">{row['recommendation_action']}</td>
        </tr>
        """

    # Prepare Top Anomalies table rows
    anomaly_table_rows = ""
    for _, row in df_anomalies.head(6).iterrows():
        anomaly_table_rows += f"""
        <tr>
            <td>{row['usage_date']}</td>
            <td><strong>{row['project_name']}</strong></td>
            <td>${row['daily_spend']:,.2f}</td>
            <td>${row['baseline_14d_avg_spend']:,.2f}</td>
            <td style="color: #dc2626; font-weight: 700;">+{row['spend_deviation_usd']:,.2f} (+{row['spike_percentage']}%)</td>
            <td>{row['daily_avg_cpu']:.1f}%</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS Cloud Cost Optimization & FinOps Analytics Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        :root {{
            --primary: #1e3a8a;
            --primary-light: #3b82f6;
            --success: #059669;
            --danger: #dc2626;
            --warning: #d97706;
            --bg-gray: #f8fafc;
            --card-bg: #ffffff;
            --text-dark: #0f172a;
            --text-muted: #64748b;
            --border: #e2e8f0;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-gray);
            color: var(--text-dark);
            line-height: 1.5;
            padding-bottom: 60px;
        }}
        header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
            color: #ffffff;
            padding: 30px 40px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        header h1 {{ font-size: 1.8rem; font-weight: 700; margin-bottom: 6px; }}
        header p {{ color: #93c5fd; font-size: 0.95rem; }}
        .container {{ max-width: 1400px; margin: -25px auto 0; padding: 0 25px; }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .kpi-card {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 22px;
            border: 1px solid var(--border);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
            position: relative;
            overflow: hidden;
        }}
        .kpi-card::before {{
            content: '';
            position: absolute;
            left: 0; top: 0; bottom: 0; width: 5px;
            background-color: var(--primary-light);
        }}
        .kpi-card.alert::before {{ background-color: var(--danger); }}
        .kpi-card.success::before {{ background-color: var(--success); }}
        .kpi-card .label {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); font-weight: 600; margin-bottom: 8px; }}
        .kpi-card .value {{ font-size: 1.8rem; font-weight: 700; color: var(--text-dark); }}
        .kpi-card.alert .value {{ color: var(--danger); }}
        .kpi-card.success .value {{ color: var(--success); }}
        .kpi-card .subtext {{ font-size: 0.85rem; color: var(--text-muted); margin-top: 6px; }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
            gap: 24px;
            margin-bottom: 30px;
        }}
        .chart-box {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
            min-height: 400px;
        }}
        
        .section-title {{
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-dark);
            margin: 30px 0 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .table-card {{
            background: var(--card-bg);
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
            overflow-x: auto;
            margin-bottom: 30px;
        }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; }}
        th {{
            background-color: #f1f5f9;
            color: #334155;
            font-weight: 600;
            padding: 12px 18px;
            border-bottom: 1px solid var(--border);
        }}
        td {{ padding: 14px 18px; border-bottom: 1px solid var(--border); }}
        tr:hover {{ background-color: #f8fafc; }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .badge.production {{ background-color: #dbeafe; color: #1e40af; }}
        .badge.staging {{ background-color: #fef3c7; color: #b45309; }}
        .badge.development {{ background-color: #e0e7ff; color: #4338ca; }}
    </style>
</head>
<body>
    <header>
        <h1>AWS Cloud Financial Operations (FinOps) Intelligence</h1>
        <p>Enterprise EC2 Usage Analytics, Anomaly Detection & Rightsizing Opportunities</p>
    </header>

    <div class="container">
        <!-- KPI Row -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="label">Total Fleet Spend (6 Mo)</div>
                <div class="value">${m['total_spend_usd']:,.2f}</div>
                <div class="subtext">50 EC2 instances across 10 service clusters</div>
            </div>
            <div class="kpi-card alert">
                <div class="label">Zombie / Idle Resource Waste</div>
                <div class="value">${m['total_idle_waste_usd']:,.2f}</div>
                <div class="subtext">Instances running at &lt; 10% average CPU</div>
            </div>
            <div class="kpi-card success">
                <div class="label">Savings Plan & Rightsizing</div>
                <div class="value">${m['total_rightsizing_potential_usd']:,.2f}</div>
                <div class="subtext">Identified On-Demand conversion potential</div>
            </div>
            <div class="kpi-card success">
                <div class="label">Actionable Recoverable Budget</div>
                <div class="value">{m['savings_roi_pct']}%</div>
                <div class="subtext">${m['total_potential_savings_usd']:,.2f} in projected savings</div>
            </div>
        </div>

        <!-- Charts Grid 1 -->
        <div class="charts-grid">
            <div class="chart-box" id="chart_monthly"></div>
            <div class="chart-box" id="chart_family"></div>
        </div>

        <!-- Charts Grid 2 -->
        <div class="charts-grid">
            <div class="chart-box" id="chart_env"></div>
            <div class="chart-box" id="chart_team"></div>
        </div>

        <!-- Table 1: Zombie / Idle Resources -->
        <h2 class="section-title">🛑 High Priority: Top Zombie & Idle Compute Fleet</h2>
        <div class="table-card">
            <table>
                <thead>
                    <tr>
                        <th>Instance ID</th>
                        <th>Project / Service</th>
                        <th>Environment</th>
                        <th>Type</th>
                        <th>Avg CPU %</th>
                        <th>Accumulated Waste</th>
                        <th>FinOps Recommendation</th>
                    </tr>
                </thead>
                <tbody>
                    {idle_table_rows}
                </tbody>
            </table>
        </div>

        <!-- Table 2: Cost Anomalies -->
        <h2 class="section-title">⚡ Detected Cost Anomalies & Spikes (&gt; 150% Baseline)</h2>
        <div class="table-card">
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Impacted Service</th>
                        <th>Daily Spend</th>
                        <th>14-Day Baseline</th>
                        <th>Deviation ($ / %)</th>
                        <th>Day CPU %</th>
                    </tr>
                </thead>
                <tbody>
                    {anomaly_table_rows}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const figMonthly = {fig_monthly.to_json()};
        const figFamily = {fig_family.to_json()};
        const figEnv = {fig_env.to_json()};
        const figTeam = {fig_team.to_json()};

        Plotly.newPlot('chart_monthly', figMonthly.data, figMonthly.layout, {{responsive: true}});
        Plotly.newPlot('chart_family', figFamily.data, figFamily.layout, {{responsive: true}});
        Plotly.newPlot('chart_env', figEnv.data, figEnv.layout, {{responsive: true}});
        Plotly.newPlot('chart_team', figTeam.data, figTeam.layout, {{responsive: true}});
    </script>
</body>
</html>
"""
    os.makedirs(os.path.dirname(DASHBOARD_PATH), exist_ok=True)
    with open(DASHBOARD_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Interactive HTML FinOps Dashboard generated at: {DASHBOARD_PATH}")

if __name__ == "__main__":
    from finops_engine import run_finops_analysis
    data = run_finops_analysis()
    generate_interactive_dashboard(data)

