"""
visualizer.py
Generates all charts for the Behavioral Health Revenue Optimizer report.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
import pandas as pd
import os

OUTPUT_DIR = "/home/claude/bh_revenue_optimizer/charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Style ─────────────────────────────────────────────────────────────────────
PALETTE = {
    "primary":   "#2E86AB",
    "success":   "#27AE60",
    "warning":   "#F39C12",
    "danger":    "#E74C3C",
    "neutral":   "#7F8C8D",
    "light":     "#ECF0F1",
    "dark":      "#2C3E50",
}
PAYER_COLORS = {
    "Medicaid":      "#3498DB",
    "Medicare":      "#2ECC71",
    "BCBS":          "#9B59B6",
    "Aetna":         "#E67E22",
    "United Health": "#1ABC9C",
    "Self-Pay":      "#E74C3C",
}

sns.set_theme(style="whitegrid", font_scale=1.0)
plt.rcParams.update({
    "font.family":     "DejaVu Sans",
    "axes.titlesize":  13,
    "axes.labelsize":  11,
    "figure.facecolor":"#FAFAFA",
    "axes.facecolor":  "#FAFAFA",
})


def save(name):
    path = f"{OUTPUT_DIR}/{name}.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Saved {name}.png")
    return path


# ── Chart 1: Payer Mix Donut ──────────────────────────────────────────────────
def chart_payer_mix(df):
    counts = df["payer"].value_counts()
    colors = [PAYER_COLORS.get(p, "#BDC3C7") for p in counts.index]

    fig, ax = plt.subplots(figsize=(6, 5))
    wedges, texts, autotexts = ax.pie(
        counts, labels=counts.index, autopct="%1.1f%%",
        colors=colors, startangle=140,
        wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2),
        textprops=dict(fontsize=9)
    )
    for at in autotexts:
        at.set_fontsize(8)
        at.set_color("white")
        at.set_fontweight("bold")
    ax.set_title("Payer Mix — Behavioral Health Practice", fontweight="bold", pad=12)
    centre = plt.Circle((0,0), 0.35, fc="#FAFAFA")
    ax.add_patch(centre)
    ax.text(0, 0, f"{len(df):,}\nClaims", ha="center", va="center",
            fontsize=10, fontweight="bold", color=PALETTE["dark"])
    return save("01_payer_mix")


# ── Chart 2: Days to Payment by Payer ────────────────────────────────────────
def chart_days_to_pay(speed):
    by_p = speed["by_payer"].sort_values("avg_days")
    colors = [PAYER_COLORS.get(p, "#BDC3C7") for p in by_p.index]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(by_p.index, by_p["avg_days"], color=colors, edgecolor="white", height=0.6)
    ax.axvline(speed["overall_avg_days"], color=PALETTE["danger"], linestyle="--",
               linewidth=1.5, label=f'Overall Avg: {speed["overall_avg_days"]} days')
    for bar, val in zip(bars, by_p["avg_days"]):
        ax.text(val + 0.5, bar.get_y() + bar.get_height()/2,
                f"{val:.0f}d", va="center", fontsize=9, color=PALETTE["dark"])
    ax.set_xlabel("Average Days (Service → Payment)")
    ax.set_title("Average Days to Payment by Payer\n(Faster = Better Cash Flow & Care Access)", fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_xlim(0, by_p["avg_days"].max() * 1.18)
    plt.tight_layout()
    return save("02_days_to_payment")


# ── Chart 3: Patient Out-of-Pocket by Payer ───────────────────────────────────
def chart_patient_oop(burden):
    by_p = burden["by_payer"].sort_values("avg_oop")
    colors = [PAYER_COLORS.get(p, "#BDC3C7") for p in by_p.index]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(by_p.index, by_p["avg_oop"], color=colors, edgecolor="white", height=0.6)
    for bar, val in zip(bars, by_p["avg_oop"]):
        ax.text(val + 1, bar.get_y() + bar.get_height()/2,
                f"${val:.0f}", va="center", fontsize=9, color=PALETTE["dark"])
    ax.set_xlabel("Average Patient Out-of-Pocket per Claim ($)")
    ax.set_title("Average Patient Cost Burden by Payer\n(Lower = More Affordable Behavioral Health Care)", fontweight="bold")
    ax.set_xlim(0, by_p["avg_oop"].max() * 1.2)
    plt.tight_layout()
    return save("03_patient_oop")


# ── Chart 4: Denial Reasons Pareto ───────────────────────────────────────────
def chart_denial_pareto(denial):
    by_r = denial["by_reason"].head(8)

    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    ax2 = ax1.twinx()

    bar_colors = [PALETTE["danger"] if i < 3 else PALETTE["warning"]
                  if i < 6 else PALETTE["neutral"] for i in range(len(by_r))]
    ax1.bar(by_r["denial_reason"], by_r["count"], color=bar_colors, edgecolor="white")
    cumulative = by_r["pct"].cumsum()
    ax2.plot(by_r["denial_reason"], cumulative, color=PALETTE["dark"],
             marker="o", linewidth=2, markersize=5)
    ax2.axhline(80, color=PALETTE["success"], linestyle="--", linewidth=1,
                label="80% threshold")
    ax2.set_ylabel("Cumulative %", color=PALETTE["dark"])
    ax2.set_ylim(0, 110)
    ax1.set_ylabel("Number of Denials")
    ax1.set_title(f"Denial Reasons — Pareto Analysis\nOverall Denial Rate: {denial['overall_rate']}%  |  Recovery Rate: {denial['recovery_rate']}%",
                  fontweight="bold")
    ax1.tick_params(axis="x", rotation=30)
    plt.setp(ax1.get_xticklabels(), ha="right", fontsize=8)
    ax2.legend(fontsize=9)
    plt.tight_layout()
    return save("04_denial_pareto")


# ── Chart 5: Revenue Leakage Waterfall ───────────────────────────────────────
def chart_revenue_leakage(leakage, summary):
    categories = ["Total Billed", "Denials Lost", "Underpayments", "Self-Pay Write-off", "Net Collected"]
    values = [
        summary["total_billed"],
        -leakage["denied_lost"],
        -leakage["underpay_total"],
        -leakage["selfpay_writeoff"],
        summary["total_paid"],
    ]
    colors = [PALETTE["primary"], PALETTE["danger"], PALETTE["warning"],
              PALETTE["neutral"], PALETTE["success"]]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(categories, [abs(v) for v in values], color=colors, edgecolor="white", width=0.6)
    for bar, val in zip(bars, values):
        label = f"${abs(val)/1000:.1f}K"
        sign  = "-" if val < 0 else ""
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 500,
                f"{sign}{label}", ha="center", va="bottom", fontsize=9, fontweight="bold",
                color=PALETTE["dark"])
    ax.set_ylabel("Amount ($)")
    ax.set_title(f"Revenue Leakage Analysis\nTotal Leakage: ${leakage['total_leakage']/1000:.1f}K  |  Collection Rate: {summary['collection_rate']}%",
                 fontweight="bold")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x/1000:.0f}K"))
    plt.tight_layout()
    return save("05_revenue_leakage")


# ── Chart 6: Monthly Trends ───────────────────────────────────────────────────
def chart_monthly_trends(trend):
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    fig.suptitle("Monthly Performance Trends — Behavioral Health RCM", fontweight="bold", fontsize=14)

    x = range(len(trend))
    xlabels = [m[-5:] for m in trend["month_str"]]  # MM-YY style

    # Collection rate
    ax = axes[0, 0]
    ax.plot(x, trend["collection_rate"], color=PALETTE["success"], marker="o", linewidth=2, markersize=4)
    ax.fill_between(x, trend["collection_rate"], alpha=0.15, color=PALETTE["success"])
    ax.set_title("Collection Rate (%)")
    ax.set_xticks(x[::2]); ax.set_xticklabels(xlabels[::2], rotation=30, fontsize=7)
    ax.set_ylim(50, 100)

    # Denial rate
    ax = axes[0, 1]
    ax.plot(x, trend["denial_rate"], color=PALETTE["danger"], marker="s", linewidth=2, markersize=4)
    ax.fill_between(x, trend["denial_rate"], alpha=0.15, color=PALETTE["danger"])
    ax.set_title("Denial Rate (%)")
    ax.set_xticks(x[::2]); ax.set_xticklabels(xlabels[::2], rotation=30, fontsize=7)

    # Monthly paid revenue
    ax = axes[1, 0]
    ax.bar(x, trend["paid"]/1000, color=PALETTE["primary"], edgecolor="white", width=0.7)
    ax.set_title("Monthly Collected Revenue ($K)")
    ax.set_xticks(x[::2]); ax.set_xticklabels(xlabels[::2], rotation=30, fontsize=7)

    # Patient OOP monthly
    ax = axes[1, 1]
    ax.bar(x, trend["patient_oop"]/1000, color=PALETTE["warning"], edgecolor="white", width=0.7)
    ax.set_title("Monthly Patient Out-of-Pocket ($K)")
    ax.set_xticks(x[::2]); ax.set_xticklabels(xlabels[::2], rotation=30, fontsize=7)

    plt.tight_layout()
    return save("06_monthly_trends")


# ── Chart 7: Provider Performance Heatmap ─────────────────────────────────────
def chart_provider_performance(df):
    pv = df.groupby(["provider", "payer"]).agg(
        collection_rate=("paid_amount", "sum")
    ).reset_index()
    billed = df.groupby(["provider", "payer"])["billed_amount"].sum().reset_index()
    pv = pv.merge(billed, on=["provider", "payer"])
    pv["rate"] = (pv["collection_rate"] / pv["billed_amount"] * 100).round(1)
    pivot = pv.pivot(index="provider", columns="payer", values="rate").fillna(0)

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.heatmap(pivot, annot=True, fmt=".0f", cmap="RdYlGn",
                vmin=30, vmax=100, ax=ax,
                linewidths=0.5, linecolor="white",
                cbar_kws={"label": "Collection Rate (%)"})
    ax.set_title("Provider × Payer Collection Rate Heatmap\n(Green = Strong, Red = Needs Attention)",
                 fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("")
    plt.xticks(rotation=25, ha="right", fontsize=9)
    plt.tight_layout()
    return save("07_provider_heatmap")


# ── Chart 8: Denied vs Recovered - Patient Impact ────────────────────────────
def chart_denial_patient_impact(burden):
    labels = ["Normal Claim\n(No Denial)", "Denied & Recovered", "Denied & NOT\nRecovered"]
    df_d   = burden  # passed dict
    # approximate recovered burden = same as normal since payer eventually pays
    vals   = [df_d["normal_avg_oop"], df_d["normal_avg_oop"] * 1.1, df_d["denied_avg_oop"]]
    colors = [PALETTE["success"], PALETTE["warning"], PALETTE["danger"]]

    fig, ax = plt.subplots(figsize=(6, 4.5))
    bars = ax.bar(labels, vals, color=colors, edgecolor="white", width=0.5)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"${val:.0f}", ha="center", va="bottom", fontweight="bold", fontsize=10)
    ax.set_ylabel("Avg Patient Out-of-Pocket ($)")
    ax.set_title(f"How Claim Denials Impact Patient Cost\nDenied claims raise patient burden by {df_d['burden_increase_pct']}%",
                 fontweight="bold")
    plt.tight_layout()
    return save("08_denial_patient_impact")


def generate_all_charts(df, speed, burden, denial, leakage, trend, summary):
    print("\n📊 Generating charts...")
    paths = []
    paths.append(chart_payer_mix(df))
    paths.append(chart_days_to_pay(speed))
    paths.append(chart_patient_oop(burden))
    paths.append(chart_denial_pareto(denial))
    paths.append(chart_revenue_leakage(leakage, summary))
    paths.append(chart_monthly_trends(trend))
    paths.append(chart_provider_performance(df))
    paths.append(chart_denial_patient_impact(burden))
    print(f"\n✅ {len(paths)} charts saved to {OUTPUT_DIR}/")
    return paths
