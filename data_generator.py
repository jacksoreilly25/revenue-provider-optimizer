"""
data_generator.py
Generates realistic synthetic behavioral health claims data for RCM analysis.
"""

import numpy as np
import pandas as pd
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

# ── Behavioral Health CPT Codes ──────────────────────────────────────────────
CPT_CATALOG = {
    "90837": {"desc": "Psychotherapy 60 min",       "allowed": 175, "typical": 150},
    "90834": {"desc": "Psychotherapy 45 min",       "allowed": 130, "typical": 110},
    "90832": {"desc": "Psychotherapy 30 min",       "allowed": 90,  "typical": 75},
    "90847": {"desc": "Family Therapy w/ patient",  "allowed": 155, "typical": 130},
    "90853": {"desc": "Group Therapy",              "allowed": 65,  "typical": 55},
    "90792": {"desc": "Psychiatric Eval w/ medical","allowed": 310, "typical": 260},
    "99213": {"desc": "Office Visit Level 3",       "allowed": 115, "typical": 100},
    "H0001": {"desc": "Alcohol/Drug Assessment",    "allowed": 200, "typical": 170},
    "H2019": {"desc": "Therapeutic Behavioral Svc","allowed": 80,  "typical": 65},
    "T1017": {"desc": "Case Management",            "allowed": 70,  "typical": 55},
}

# ── Payers ────────────────────────────────────────────────────────────────────
PAYERS = {
    "Medicaid":        {"share": 0.32, "pay_rate": 0.72, "days_to_pay": 28, "denial_rate": 0.14},
    "Medicare":        {"share": 0.18, "pay_rate": 0.85, "days_to_pay": 18, "denial_rate": 0.08},
    "BCBS":            {"share": 0.20, "pay_rate": 0.90, "days_to_pay": 14, "denial_rate": 0.07},
    "Aetna":           {"share": 0.12, "pay_rate": 0.88, "days_to_pay": 16, "denial_rate": 0.09},
    "United Health":   {"share": 0.10, "pay_rate": 0.86, "days_to_pay": 20, "denial_rate": 0.11},
    "Self-Pay":        {"share": 0.08, "pay_rate": 0.38, "days_to_pay": 60, "denial_rate": 0.00},
}

DENIAL_REASONS = [
    "Missing/Invalid Auth",
    "Timely Filing Exceeded",
    "Duplicate Claim",
    "Patient Not Eligible",
    "Service Not Covered",
    "Incorrect Billing Code",
    "Coordination of Benefits",
    "Incomplete Documentation",
]

PROVIDERS = ["Dr. Rivera", "Dr. Chen", "Dr. Patel", "NP Williams", "LCSW Thompson", "LMFT Garcia"]

def random_date(start_days_ago=365):
    base = datetime.today() - timedelta(days=start_days_ago)
    return base + timedelta(days=random.randint(0, start_days_ago))

def generate_claims(n=1200):
    rows = []
    payer_names = list(PAYERS.keys())
    payer_weights = [PAYERS[p]["share"] for p in payer_names]
    cpt_codes = list(CPT_CATALOG.keys())

    for i in range(n):
        payer = random.choices(payer_names, weights=payer_weights)[0]
        cpt   = random.choices(cpt_codes, weights=[3,3,2,2,2,1,2,1,1,1])[0]
        p     = PAYERS[payer]
        c     = CPT_CATALOG[cpt]

        svc_date    = random_date(365)
        submit_lag  = random.randint(1, 20)   # days from service to submission
        submit_date = svc_date + timedelta(days=submit_lag)

        denied = random.random() < p["denial_rate"]
        if denied:
            denial_reason = random.choice(DENIAL_REASONS)
            paid_amount   = 0.0
            pay_date      = None
            days_to_close = None
            resubmitted   = random.random() < 0.55  # 55% resubmission rate
            recovered     = resubmitted and (random.random() < 0.70)
        else:
            denial_reason = None
            resubmitted   = False
            recovered     = False
            pay_days      = int(np.random.normal(p["days_to_pay"], 5))
            pay_date      = submit_date + timedelta(days=max(1, pay_days))
            paid_amount   = round(c["allowed"] * p["pay_rate"] * random.uniform(0.92, 1.0), 2)
            days_to_close = (pay_date - svc_date).days

        billed_amount = round(c["allowed"] * random.uniform(1.05, 1.30), 2)  # charge master markup

        # Patient responsibility
        if payer == "Self-Pay":
            patient_resp = round(billed_amount * random.uniform(0.30, 0.50), 2)
        elif denied and not recovered:
            patient_resp = round(billed_amount * random.uniform(0.40, 0.80), 2)
        else:
            copay = random.choice([20, 30, 40, 50, 0])
            deductible_applied = random.uniform(0, 60)
            patient_resp = round(copay + deductible_applied, 2)

        rows.append({
            "claim_id":        f"CLM{10000+i}",
            "patient_id":      f"PT{random.randint(1000,3999)}",
            "provider":        random.choice(PROVIDERS),
            "cpt_code":        cpt,
            "service_desc":    c["desc"],
            "payer":           payer,
            "service_date":    svc_date,
            "submit_date":     submit_date,
            "submit_lag_days": submit_lag,
            "pay_date":        pay_date,
            "days_to_close":   days_to_close,
            "billed_amount":   billed_amount,
            "allowed_amount":  c["allowed"],
            "paid_amount":     paid_amount,
            "patient_resp":    patient_resp,
            "denied":          denied,
            "denial_reason":   denial_reason,
            "resubmitted":     resubmitted,
            "recovered":       recovered,
        })

    df = pd.DataFrame(rows)
    df["service_date"] = pd.to_datetime(df["service_date"])
    df["submit_date"]  = pd.to_datetime(df["submit_date"])
    df["pay_date"]     = pd.to_datetime(df["pay_date"])
    df["month"]        = df["service_date"].dt.to_period("M")
    return df

if __name__ == "__main__":
    df = generate_claims()
    df.to_csv("/home/claude/bh_revenue_optimizer/claims_data.csv", index=False)
    print(f"Generated {len(df)} claims | Denial rate: {df['denied'].mean():.1%}")
    print(df.head(3).to_string())
