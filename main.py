"""
main.py
Entry point for the Behavioral Health Provider Revenue Optimizer.
Run: python main.py
"""

import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from data_generator   import generate_claims
from rcm_analyzer     import RCMAnalyzer
from visualizer       import generate_all_charts
from report_generator import generate_html_report


def main():
    print("=" * 60)
    print("  Behavioral Health Provider Revenue Optimizer")
    print("  Focused on: Patient Cost Burden & Claims Speed")
    print("=" * 60)

    # ── Step 1: Generate / Load Data ──────────────────────────────
    print("\n📋 Step 1: Generating synthetic behavioral health claims data...")
    df = generate_claims(n=1200)
    df.to_csv("/home/claude/bh_revenue_optimizer/claims_data.csv", index=False)
    print(f"  ✓ {len(df)} claims generated | {df['patient_id'].nunique()} unique patients")

    # ── Step 2: Run Analysis ──────────────────────────────────────
    print("\n🔍 Step 2: Running RCM analysis...")
    analyzer = RCMAnalyzer(df)
    summary  = analyzer.executive_summary()
    speed    = analyzer.claims_speed_summary()
    burden   = analyzer.patient_cost_burden()
    denial   = analyzer.denial_analysis()
    leakage  = analyzer.revenue_leakage()
    trend    = analyzer.monthly_trend()

    print(f"\n  📊 Executive Summary:")
    print(f"     Total Billed:        ${summary['total_billed']:>12,.2f}")
    print(f"     Total Collected:     ${summary['total_paid']:>12,.2f}")
    print(f"     Collection Rate:     {summary['collection_rate']:>11.1f}%")
    print(f"     Denial Rate:         {summary['overall_denial_pct']:>11.1f}%")
    print(f"     Avg Days to Payment: {summary['avg_days_to_pay']:>10.1f}d")
    print(f"     Patient OOP Total:   ${summary['total_patient_oop']:>12,.2f}")
    print(f"     Revenue Leakage:     ${leakage['total_leakage']:>12,.2f}")

    print(f"\n  ⚠ Top Denial Reason:  {denial['by_reason'].iloc[0]['denial_reason']} ({denial['by_reason'].iloc[0]['pct']}%)")
    print(f"  ⚠ Slowest Payer:      {speed['slowest_payer']} ({speed['by_payer'].loc[speed['slowest_payer'], 'avg_days']:.0f} days avg)")
    print(f"  ⚠ Patient Burden:     {burden['pct_high_burden']}% of patients owe >$500/year")

    # ── Step 3: Generate Charts ───────────────────────────────────
    chart_paths = generate_all_charts(df, speed, burden, denial, leakage, trend, summary)

    # ── Step 4: Build Report ──────────────────────────────────────
    print("\n📄 Step 4: Building HTML report...")
    report_path = "/home/claude/bh_revenue_optimizer/BH_Revenue_Optimizer_Report.html"
    generate_html_report(summary, speed, burden, denial, leakage, trend, chart_paths, report_path)

    # ── Step 5: Save CSV ──────────────────────────────────────────
    print("\n💾 Step 5: Saving analysis outputs...")
    trend.to_csv("/home/claude/bh_revenue_optimizer/monthly_trend.csv", index=False)
    denial["by_reason"].to_csv("/home/claude/bh_revenue_optimizer/denial_reasons.csv", index=False)
    print("  ✓ monthly_trend.csv")
    print("  ✓ denial_reasons.csv")
    print("  ✓ claims_data.csv")

    print("\n" + "=" * 60)
    print("  ✅ Analysis complete!")
    print(f"  📁 All files in: /home/claude/bh_revenue_optimizer/")
    print("=" * 60)


if __name__ == "__main__":
    main()
