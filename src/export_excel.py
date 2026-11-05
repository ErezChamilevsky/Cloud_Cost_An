"""
Executive Excel Report Generator
Generates a multi-tab formatted Excel report with summary KPIs, styled tables,
and conditional highlighting for business stakeholders.
"""

import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
REPORT_PATH = os.path.join(BASE_DIR, "reports", "executive_finops_report.xlsx")

def style_header(cell):
    cell.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

def style_kpi_card(ws, start_row, start_col, label, value, note=None, is_alert=False):
    card_fill = PatternFill(start_color="FFF2CC" if is_alert else "D9E1F2", fill_type="solid")
    border_side = Side(style="thin", color="B0B0B0")
    box_border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)
    
    # Label cell
    cell_lbl = ws.cell(row=start_row, column=start_col, value=label)
    cell_lbl.font = Font(name="Calibri", size=9, bold=True, color="595959")
    cell_lbl.alignment = Alignment(horizontal="center")
    cell_lbl.fill = card_fill
    cell_lbl.border = box_border
    
    # Value cell
    cell_val = ws.cell(row=start_row + 1, column=start_col, value=value)
    cell_val.font = Font(name="Calibri", size=16, bold=True, color="C00000" if is_alert else "1F4E79")
    cell_val.alignment = Alignment(horizontal="center")
    cell_val.fill = card_fill
    cell_val.border = box_border
    
    if note:
        cell_note = ws.cell(row=start_row + 2, column=start_col, value=note)
        cell_note.font = Font(name="Calibri", size=8, italic=True, color="7F7F7F")
        cell_note.alignment = Alignment(horizontal="center")
        cell_note.fill = card_fill
        cell_note.border = box_border

def write_dataframe_to_sheet(ws, df, start_row=1):
    thin_border = Border(
        left=Side(style='thin', color='E0E0E0'),
        right=Side(style='thin', color='E0E0E0'),
        top=Side(style='thin', color='E0E0E0'),
        bottom=Side(style='thin', color='E0E0E0')
    )
    
    # Header
    for col_idx, col_name in enumerate(df.columns, 1):
        cell = ws.cell(row=start_row, column=col_idx, value=col_name.replace('_', ' ').title())
        style_header(cell)
    
    # Rows
    for row_idx, row_data in enumerate(df.values, start_row + 1):
        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = Font(name="Calibri", size=10)
            cell.border = thin_border
            
            # Format numbers
            if isinstance(val, (int, float)):
                if "pct" in df.columns[col_idx - 1] or "percent" in df.columns[col_idx - 1]:
                    cell.number_format = '0.0"%"'
                elif "usd" in df.columns[col_idx - 1] or "spend" in df.columns[col_idx - 1] or "cost" in df.columns[col_idx - 1]:
                    cell.number_format = '$#,##0.00'
                else:
                    cell.number_format = '#,##0.0'
            
            # Zebra striping
            if row_idx % 2 == 0:
                cell.fill = PatternFill(start_color="F9FAFB", fill_type="solid")

    # Column width adjustment
    for col_idx, col_name in enumerate(df.columns, 1):
        col_letter = get_column_letter(col_idx)
        max_len = max(len(str(col_name)), max((len(str(v or '')) for v in df.iloc[:, col_idx - 1]), default=0))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

def generate_excel_report(finops_data: dict):
    wb = Workbook()
    
    # --- Tab 1: Executive Overview ---
    ws_exec = wb.active
    ws_exec.title = "Executive Summary"
    ws_exec.views.sheetView[0].showGridLines = True
    
    # Title Banner
    ws_exec.merge_cells("A1:G1")
    title_cell = ws_exec["A1"]
    title_cell.value = "AWS Cloud Cost & FinOps Optimization Report"
    title_cell.font = Font(name="Calibri", size=18, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="1F4E79", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws_exec.row_dimensions[1].height = 40
    
    # Subtitle
    ws_exec["A2"] = "Automated audit of EC2 compute fleet, idle waste analysis, and rightsizing opportunities"
    ws_exec["A2"].font = Font(name="Calibri", size=10, italic=True, color="595959")
    
    # KPI Cards
    m = finops_data["metrics"]
    style_kpi_card(ws_exec, start_row=4, start_col=1, label="TOTAL FLEET SPEND", value=f"${m['total_spend_usd']:,.2f}", note="Analyzed period")
    style_kpi_card(ws_exec, start_row=4, start_col=3, label="ZOMBIE / IDLE WASTE", value=f"${m['total_idle_waste_usd']:,.2f}", note="Avg CPU < 10%", is_alert=True)
    style_kpi_card(ws_exec, start_row=4, start_col=5, label="SAVINGS PLAN POTENTIAL", value=f"${m['total_rightsizing_potential_usd']:,.2f}", note="1-3 Yr commitment")
    style_kpi_card(ws_exec, start_row=4, start_col=7, label="TOTAL SAVINGS ROI", value=f"{m['savings_roi_pct']}%", note="Total recoverable waste", is_alert=True)
    
    # Embed Monthly Trends in Executive tab
    ws_exec.cell(row=8, column=1, value="Monthly Spend & MoM Trajectory").font = Font(name="Calibri", size=13, bold=True, color="1F4E79")
    write_dataframe_to_sheet(ws_exec, finops_data["monthly"], start_row=9)
    
    # --- Tab 2: Idle & Zombie Machines ---
    ws_idle = wb.create_sheet("Zombie & Idle Resources")
    ws_idle.views.sheetView[0].showGridLines = True
    ws_idle.cell(row=1, column=1, value="Underutilized Servers (Avg CPU < 10% - High Priority Waste)").font = Font(name="Calibri", size=13, bold=True, color="C00000")
    write_dataframe_to_sheet(ws_idle, finops_data["idle"], start_row=3)
    
    # --- Tab 3: Rightsizing & Savings Plans ---
    ws_savings = wb.create_sheet("Rightsizing & Savings Plans")
    ws_savings.views.sheetView[0].showGridLines = True
    ws_savings.cell(row=1, column=1, value="On-Demand Optimization & Commitment Recommendations").font = Font(name="Calibri", size=13, bold=True, color="1F4E79")
    write_dataframe_to_sheet(ws_savings, finops_data["savings"], start_row=3)
    
    # --- Tab 4: Cost Anomalies ---
    ws_anomalies = wb.create_sheet("Cost Anomalies")
    ws_anomalies.views.sheetView[0].showGridLines = True
    ws_anomalies.cell(row=1, column=1, value="Spikes Exceeding 14-Day Baseline (> 150% threshold)").font = Font(name="Calibri", size=13, bold=True, color="C00000")
    write_dataframe_to_sheet(ws_anomalies, finops_data["anomalies"], start_row=3)
    
    # --- Tab 5: Breakdown by Family & Team ---
    ws_breakdown = wb.create_sheet("Family & Team Breakdown")
    ws_breakdown.views.sheetView[0].showGridLines = True
    ws_breakdown.cell(row=1, column=1, value="Spend by Instance Family").font = Font(name="Calibri", size=13, bold=True, color="1F4E79")
    write_dataframe_to_sheet(ws_breakdown, finops_data["family"], start_row=3)
    
    start_team_row = len(finops_data["family"]) + 6
    ws_breakdown.cell(row=start_team_row, column=1, value="Spend by Team / Business Unit").font = Font(name="Calibri", size=13, bold=True, color="1F4E79")
    write_dataframe_to_sheet(ws_breakdown, finops_data["team"], start_row=start_team_row + 2)

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    wb.save(REPORT_PATH)
    print(f"Executive Excel Workbook created at: {REPORT_PATH}")

if __name__ == "__main__":
    from finops_engine import run_finops_analysis
    data = run_finops_analysis()
    generate_excel_report(data)
