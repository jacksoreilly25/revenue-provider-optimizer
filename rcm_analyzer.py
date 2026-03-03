"""
rcm_analyzer.py
Core analysis engine — computes all RCM KPIs and optimization insights.
"""

import pandas as pd
import numpy as np


class RCMAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.paid   = df[~df["denied"] | df["recovered"]]
        self.denied = df[df["denied"]]

    # ── 1. Claims Speed ──────────────────────────────────────────────────────
    def claims_speed_summary(self) -> dict:
        paid = self.df[self.df["paid_amount"] > 0].copy()
        by_payer = (paid.groupby("payer")["days_to_close"]
                       .agg(["mean","median","count"])
                       .rename(columns={"mean":"avg_days","median":"med_days","count":"n_claims"})
                       .round(1)
                       .sort_values("avg_days"))

        submit_lag = self.df["submit_lag_days"]
        late_submit = (submit_lag > 10).mean()

        return {
            "by_payer":          by_payer,
            "overall_avg_days":  round(paid["days_to_close"].mean(), 1),
            "avg_submit_lag":    round(submit_lag.mean(), 1),
            "pct_late_submit":   round(late_submit * 100, 1),
            "fastest_payer":     by_payer["avg_days"].idxmin(),
            "slowest_payer":     by_payer["avg_days"].idxmax(),
        }

    # ── 2. Patient Cost Burden ────────────────────────────────────────────────
    def patient_cost_burden(self) -> dict:
        df = self.df.copy()
        by_payer = (df.groupby("payer")["patient_resp"]
                      .agg(["mean","sum","count"])
                      .rename(columns={"mean":"avg_oop","sum":"total_oop","count":"claims"})
                      .round(2)
                      .sort_values("avg_oop"))

        # patients with multiple claims (estimate)
        patient_annual = (df.groupby("patient_id")["patient_resp"]
                            .sum()
                            .describe()
                            .round(2))

        high_burden = (df.groupby("patient_id")["patient_resp"]
                         .sum()
                         .gt(500)
                         .mean()) * 100

        denied_burden = df[df["denied"] & ~df["recovered"]]["patient_resp"].mean()
        normal_burden = df[~df["denied"]]["patient_resp"].mean()

        return {
            "by_payer":           by_payer,
            "patient_annual_oop": patient_annual,
            "pct_high_burden":    round(high_burden, 1),
            "denied_avg_oop":     round(denied_burden, 2),
            "normal_avg_oop":     round(normal_burden, 2),
            "burden_increase_pct":round((denied_burden / normal_burden - 1) * 100, 1),
        }

    # ── 3. Denial Analysis ────────────────────────────────────────────────────
    def denial_analysis(self) -> dict:
        df = self.df.copy()
        overall_rate = df["denied"].mean()

        by_payer = (df.groupby("payer")["denied"]
                      .agg(["mean","sum","count"])
                      .rename(columns={"mean":"denial_rate","sum":"denied_claims","count":"total_claims"})
                      .sort_values("denial_rate", ascending=False)
                      .round(3))

        by_reason = (df[df["denied"]]
                       .groupby("denial_reason")
                       .size()
                       .sort_values(ascending=False)
                       .reset_index(name="count"))
        by_reason["pct"] = (by_reason["count"] / by_reason["count"].sum() * 100).round(1)

        by_cpt = (df.groupby("cpt_code")["denied"]
                    .mean()
                    .sort_values(ascending=False)
                    .round(3))

        revenue_at_risk = df[df["denied"] & ~df["recovered"]]["allowed_amount"].sum()
        recovery_rate   = df[df["denied"]]["recovered"].mean()

        return {
            "overall_rate":    round(overall_rate * 100, 1),
            "by_payer":        by_payer,
            "by_reason":       by_reason,
            "by_cpt":          by_cpt,
            "revenue_at_risk": round(revenue_at_risk, 2),
            "recovery_rate":   round(recovery_rate * 100, 1),
        }

    # ── 4. Revenue Leakage ────────────────────────────────────────────────────
    def revenue_leakage(self) -> dict:
        df = self.df.copy()

        # Underpayment: paid < 90% of allowed (excluding self-pay & denials)
        billable = df[(df["payer"] != "Self-Pay") & (~df["denied"])]
        billable = billable.copy()
        billable["pay_ratio"]     = billable["paid_amount"] / billable["allowed_amount"]
        billable["underpaid"]     = billable["pay_ratio"] < 0.88
        billable["underpay_gap"]  = (billable["allowed_amount"] - billable["paid_amount"]).clip(lower=0)

        underpay_total = billable[billable["underpaid"]]["underpay_gap"].sum()
        denied_lost    = df[df["denied"] & ~df["recovered"]]["allowed_amount"].sum()

        # Write-off from self-pay
        sp_billed = df[df["payer"] == "Self-Pay"]["billed_amount"].sum()
        sp_paid   = df[df["payer"] == "Self-Pay"]["paid_amount"].sum()
        selfpay_writeoff = sp_billed - sp_paid

        total_leakage = underpay_total + denied_lost + selfpay_writeoff

        by_provider = (df.groupby("provider")
                         .agg(billed=("billed_amount","sum"),
                              paid=("paid_amount","sum"))
                         .assign(collection_rate=lambda x: (x["paid"]/x["billed"]*100).round(1))
                         .sort_values("collection_rate"))

        return {
            "underpay_total":    round(underpay_total, 2),
            "denied_lost":       round(denied_lost, 2),
            "selfpay_writeoff":  round(selfpay_writeoff, 2),
            "total_leakage":     round(total_leakage, 2),
            "by_provider":       by_provider,
            "underpay_rate":     round(billable["underpaid"].mean() * 100, 1),
        }

    # ── 5. Monthly Trend ──────────────────────────────────────────────────────
    def monthly_trend(self) -> pd.DataFrame:
        trend = (self.df.groupby("month")
                        .agg(claims       =("claim_id","count"),
                             billed       =("billed_amount","sum"),
                             paid         =("paid_amount","sum"),
                             denials      =("denied","sum"),
                             patient_oop  =("patient_resp","sum"))
                        .reset_index())
        trend["denial_rate"]      = (trend["denials"] / trend["claims"] * 100).round(1)
        trend["collection_rate"]  = (trend["paid"] / trend["billed"] * 100).round(1)
        trend["month_str"]        = trend["month"].astype(str)
        return trend

    # ── 6. Executive Summary ──────────────────────────────────────────────────
    def executive_summary(self) -> dict:
        df = self.df
        return {
            "total_claims":      len(df),
            "total_billed":      round(df["billed_amount"].sum(), 2),
            "total_paid":        round(df["paid_amount"].sum(), 2),
            "total_patient_oop": round(df["patient_resp"].sum(), 2),
            "collection_rate":   round(df["paid_amount"].sum() / df["billed_amount"].sum() * 100, 1),
            "overall_denial_pct":round(df["denied"].mean() * 100, 1),
            "avg_days_to_pay":   round(df["days_to_close"].dropna().mean(), 1),
            "unique_patients":   df["patient_id"].nunique(),
        }


if __name__ == "__main__":
    from data_generator import generate_claims
    df = generate_claims()
    a  = RCMAnalyzer(df)
    s  = a.executive_summary()
    for k, v in s.items():
        print(f"  {k:<25}: {v}")
