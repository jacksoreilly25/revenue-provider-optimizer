"""
report_generator.py
Generates the full HTML report with embedded charts and insights.
"""

import base64
import os
from datetime import datetime


def img_to_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def generate_html_report(summary, speed, burden, denial, leakage, trend, chart_paths, output_path):
    charts = {os.path.basename(p).replace(".png",""): img_to_b64(p) for p in chart_paths}

    def chart_tag(key, caption=""):
        if key not in charts:
            return ""
        return f"""
        <figure class="chart-figure">
          <img src="data:image/png;base64,{charts[key]}" alt="{key}" />
          {"<figcaption>" + caption + "</figcaption>" if caption else ""}
        </figure>"""

    # Top insights
    insights = []
    if denial["overall_rate"] > 10:
        insights.append(f"🚨 <strong>High Denial Rate ({denial['overall_rate']}%)</strong> — Industry benchmark is &lt;5%. Fixing the top 3 denial reasons could recover <strong>${denial['revenue_at_risk']:,.0f}</strong>.")
    if speed["pct_late_submit"] > 15:
        insights.append(f"⏱ <strong>Late Claim Submission ({speed['pct_late_submit']}% submitted after 10 days)</strong> — Delays slow cash flow and risk timely filing denials. Target same-week submission.")
    if burden["pct_high_burden"] > 20:
        insights.append(f"💸 <strong>Patient Affordability Risk ({burden['pct_high_burden']}% of patients owe >$500/year)</strong> — Consider payment plans and sliding-scale options for behavioral health equity.")
    insights.append(f"📉 <strong>Revenue Leakage: ${leakage['total_leakage']:,.0f}</strong> — ${leakage['denied_lost']:,.0f} from unrecovered denials, ${leakage['underpay_total']:,.0f} from underpayments, ${leakage['selfpay_writeoff']:,.0f} from self-pay write-offs.")
    insights.append(f"⚡ <strong>Fastest Payer: {speed['fastest_payer']}</strong> — Route care coordination to maximize insurance benefit usage where reimbursement is fastest.")

    insight_html = "\n".join(f"<li>{i}</li>" for i in insights)

    top_denials = denial["by_reason"].head(3)
    denial_rows = ""
    for _, row in top_denials.iterrows():
        denial_rows += f"<tr><td>{row['denial_reason']}</td><td>{row['count']}</td><td>{row['pct']}%</td></tr>"

    payer_rows = ""
    for payer, row in speed["by_payer"].iterrows():
        oop = burden["by_payer"].loc[payer, "avg_oop"] if payer in burden["by_payer"].index else "N/A"
        dr  = denial["by_payer"].loc[payer, "denial_rate"] * 100 if payer in denial["by_payer"].index else 0
        payer_rows += f"<tr><td>{payer}</td><td>{row['avg_days']:.0f}d</td><td>{dr:.1f}%</td><td>${oop:.0f}</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Behavioral Health Provider Revenue Optimizer</title>
<style>
  :root {{
    --primary: #2E86AB; --success: #27AE60; --warning: #F39C12;
    --danger: #E74C3C; --dark: #2C3E50; --light: #ECF0F1; --bg: #F8F9FA;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--dark); }}
  header {{
    background: linear-gradient(135deg, var(--primary), #1a5276);
    color: white; padding: 2rem 2.5rem;
  }}
  header h1 {{ font-size: 1.8rem; margin-bottom: 0.3rem; }}
  header p  {{ opacity: 0.85; font-size: 0.95rem; }}
  .badge {{ display: inline-block; background: rgba(255,255,255,0.2);
             padding: 0.2rem 0.7rem; border-radius: 12px; font-size: 0.8rem; margin-top: 0.5rem; }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 1.5rem; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 1.5rem 0; }}
  .kpi {{ background: white; border-radius: 10px; padding: 1.2rem; box-shadow: 0 2px 8px rgba(0,0,0,.06);
           border-left: 4px solid var(--primary); }}
  .kpi.danger {{ border-color: var(--danger); }}
  .kpi.success {{ border-color: var(--success); }}
  .kpi.warning {{ border-color: var(--warning); }}
  .kpi-value {{ font-size: 1.8rem; font-weight: 700; color: var(--primary); }}
  .kpi.danger .kpi-value {{ color: var(--danger); }}
  .kpi.success .kpi-value {{ color: var(--success); }}
  .kpi.warning .kpi-value {{ color: var(--warning); }}
  .kpi-label {{ font-size: 0.8rem; color: #666; margin-top: 0.2rem; }}
  .section {{ background: white; border-radius: 10px; padding: 1.5rem;
               box-shadow: 0 2px 8px rgba(0,0,0,.06); margin-bottom: 1.5rem; }}
  .section h2 {{ font-size: 1.1rem; color: var(--dark); border-bottom: 2px solid var(--light);
                  padding-bottom: 0.5rem; margin-bottom: 1rem; }}
  .section h2 span {{ font-size: 1.3rem; margin-right: 0.4rem; }}
  .insights {{ list-style: none; }}
  .insights li {{ padding: 0.7rem 0.9rem; margin-bottom: 0.5rem; border-radius: 6px;
                   background: #fef9f0; border-left: 4px solid var(--warning); font-size: 0.92rem; line-height: 1.5; }}
  .chart-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem; }}
  .chart-grid.single {{ grid-template-columns: 1fr; }}
  .chart-figure {{ text-align: center; }}
  .chart-figure img {{ width: 100%; border-radius: 8px; border: 1px solid #eee; }}
  figcaption {{ font-size: 0.78rem; color: #888; margin-top: 0.4rem; font-style: italic; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
  th {{ background: var(--primary); color: white; padding: 0.6rem 0.8rem; text-align: left; }}
  td {{ padding: 0.5rem 0.8rem; border-bottom: 1px solid var(--light); }}
  tr:hover td {{ background: #f0f8ff; }}
  .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem; }}
  .rec-list {{ list-style: none; }}
  .rec-list li {{ padding: 0.6rem 0.8rem; margin-bottom: 0.4rem; background: #f0fff4;
                   border-left: 4px solid var(--success); border-radius: 5px; font-size: 0.88rem; line-height: 1.5; }}
  footer {{ text-align: center; padding: 1.5rem; color: #999; font-size: 0.8rem; }}
  @media(max-width: 700px) {{
    .kpi-grid {{ grid-template-columns: 1fr 1fr; }}
    .chart-grid, .two-col {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<header>
  <h1>🏥 Behavioral Health Provider Revenue Optimizer</h1>
  <p>Revenue Cycle Management Analysis — Patient-Centered Financial Performance</p>
  <span class="badge">Analysis Period: 12 Months</span>
  <span class="badge">Generated: {datetime.today().strftime('%B %d, %Y')}</span>
  <span class="badge">{summary['total_claims']:,} Claims Analyzed</span>
</header>

<div class="container">

  <!-- KPI Banner -->
  <div class="kpi-grid">
    <div class="kpi success">
      <div class="kpi-value">${summary['total_paid']/1000:.0f}K</div>
      <div class="kpi-label">Total Revenue Collected</div>
    </div>
    <div class="kpi {'danger' if summary['overall_denial_pct'] > 10 else 'warning'}">
      <div class="kpi-value">{summary['overall_denial_pct']}%</div>
      <div class="kpi-label">Overall Claim Denial Rate</div>
    </div>
    <div class="kpi">
      <div class="kpi-value">{summary['avg_days_to_pay']:.0f}d</div>
      <div class="kpi-label">Avg Days to Payment</div>
    </div>
    <div class="kpi warning">
      <div class="kpi-value">${summary['total_patient_oop']/1000:.0f}K</div>
      <div class="kpi-label">Total Patient Out-of-Pocket</div>
    </div>
    <div class="kpi">
      <div class="kpi-value">{summary['collection_rate']}%</div>
      <div class="kpi-label">Collection Rate</div>
    </div>
    <div class="kpi danger">
      <div class="kpi-value">${leakage['total_leakage']/1000:.0f}K</div>
      <div class="kpi-label">Revenue Leakage</div>
    </div>
    <div class="kpi">
      <div class="kpi-value">{summary['unique_patients']:,}</div>
      <div class="kpi-label">Unique Patients Served</div>
    </div>
    <div class="kpi success">
      <div class="kpi-value">{denial['recovery_rate']}%</div>
      <div class="kpi-label">Denial Recovery Rate</div>
    </div>
  </div>

  <!-- Key Insights -->
  <div class="section">
    <h2><span>💡</span>Key Findings & Optimization Opportunities</h2>
    <ul class="insights">{insight_html}</ul>
  </div>

  <!-- Payer Analysis -->
  <div class="section">
    <h2><span>📊</span>Payer Mix & Performance Matrix</h2>
    <div class="two-col">
      {chart_tag("01_payer_mix", "Distribution of claims by insurance payer")}
      <div>
        <table>
          <thead><tr><th>Payer</th><th>Avg Days to Pay</th><th>Denial Rate</th><th>Avg Patient OOP</th></tr></thead>
          <tbody>{payer_rows}</tbody>
        </table>
        <p style="font-size:0.8rem;color:#888;margin-top:0.5rem;">
          OOP = Out-of-Pocket patient responsibility per claim
        </p>
      </div>
    </div>
  </div>

  <!-- Claims Speed & Access to Care -->
  <div class="section">
    <h2><span>⚡</span>Claims Speed — Impact on Patient Care Access</h2>
    <p style="font-size:0.88rem;color:#555;margin-bottom:1rem;">
      Faster claim resolution means providers can focus on care, not collections — and patients avoid billing confusion that disrupts ongoing behavioral health treatment.
    </p>
    {chart_tag("02_days_to_payment", "Slower payers create cash flow pressure that can limit provider capacity and patient scheduling")}
  </div>

  <!-- Patient Cost Burden -->
  <div class="section">
    <h2><span>💰</span>Patient Affordability Analysis</h2>
    <div class="chart-grid">
      {chart_tag("03_patient_oop", "Average out-of-pocket cost per claim — behavioral health affordability by payer")}
      {chart_tag("08_denial_patient_impact", "How claim denials shift cost burden to patients — a key equity issue in behavioral health")}
    </div>
    <div style="background:#fff3cd;padding:0.8rem;border-radius:6px;font-size:0.88rem;margin-top:1rem;border-left:4px solid var(--warning)">
      <strong>Patient Equity Note:</strong> {burden['pct_high_burden']}% of patients face >$500/year in out-of-pocket costs for behavioral health.
      Denied claims increase average patient burden by <strong>{burden['burden_increase_pct']}%</strong> — making timely claim resolution a direct patient welfare issue, not just a financial one.
    </div>
  </div>

  <!-- Denial Analysis -->
  <div class="section">
    <h2><span>🚫</span>Denial Analysis & Root Causes</h2>
    <div class="two-col">
      {chart_tag("04_denial_pareto", "Pareto chart: top denial reasons account for 80%+ of all denials — fix these first")}
      <div>
        <h3 style="font-size:0.95rem;margin-bottom:0.5rem;">Top 3 Denial Reasons</h3>
        <table>
          <thead><tr><th>Reason</th><th>Count</th><th>% of All Denials</th></tr></thead>
          <tbody>{denial_rows}</tbody>
        </table>
        <br>
        <h3 style="font-size:0.95rem;margin-bottom:0.5rem;">Revenue at Risk</h3>
        <p style="font-size:0.88rem;line-height:1.6;">
          Unrecovered denied claims represent <strong style="color:var(--danger)">${denial['revenue_at_risk']:,.0f}</strong>
          in lost revenue. At the current {denial['recovery_rate']}% recovery rate, 
          improving appeals processes could meaningfully recover this.
        </p>
      </div>
    </div>
  </div>

  <!-- Revenue Leakage -->
  <div class="section">
    <h2><span>📉</span>Revenue Leakage Breakdown</h2>
    <div class="chart-grid single">
      {chart_tag("05_revenue_leakage", "Where revenue is lost between billing and collection")}
    </div>
  </div>

  <!-- Provider Heatmap -->
  <div class="section">
    <h2><span>👩‍⚕️</span>Provider × Payer Performance</h2>
    {chart_tag("07_provider_heatmap", "Collection rates by provider and payer — identify training needs and high-performing combinations")}
  </div>

  <!-- Monthly Trends -->
  <div class="section">
    <h2><span>📈</span>Monthly Performance Trends</h2>
    <div class="chart-grid single">
      {chart_tag("06_monthly_trends", "12-month view of collection rate, denial rate, revenue, and patient out-of-pocket costs")}
    </div>
  </div>

  <!-- Recommendations -->
  <div class="section">
    <h2><span>✅</span>Actionable Recommendations</h2>
    <div class="two-col">
      <div>
        <h3 style="font-size:0.9rem;margin-bottom:0.5rem;color:var(--primary)">🏥 For Patient Benefit</h3>
        <ul class="rec-list">
          <li>Implement real-time eligibility verification at scheduling — prevents most "Patient Not Eligible" denials that shift cost to patients</li>
          <li>Offer sliding-scale fees and payment plans for self-pay behavioral health patients to reduce care avoidance</li>
          <li>Train front desk staff on obtaining prior authorizations — #1 denial reason in behavioral health</li>
          <li>Create a denial appeal workflow with standard letter templates for common behavioral health denial codes</li>
        </ul>
      </div>
      <div>
        <h3 style="font-size:0.9rem;margin-bottom:0.5rem;color:var(--primary)">💼 For Revenue Optimization</h3>
        <ul class="rec-list">
          <li>Submit claims within 3 days of service — reduces timely filing denials and improves cash flow by ~{int(speed['avg_submit_lag'] * 2)} days</li>
          <li>Audit underpayments quarterly — {leakage['underpay_rate']}% of claims are paid below contracted rate</li>
          <li>Track payer-specific denial trends monthly — Medicaid requires different documentation than commercial payers</li>
          <li>Invest in coding education for highest-denial CPT codes to reduce "Incorrect Billing Code" denials</li>
        </ul>
      </div>
    </div>
  </div>

</div>

<footer>
  Behavioral Health Provider Revenue Optimizer | Python-based RCM Analytics |
  Built for MIS & Financial Skills Application | Data is synthetic/simulated for educational purposes
</footer>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)
    print(f"\n✅ HTML report saved: {output_path}")
    return output_path
