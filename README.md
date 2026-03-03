[README.md](https://github.com/user-attachments/files/25724325/README.md)
# Behavioral Health Provider Revenue Optimizer

A Python-based revenue cycle management (RCM) analytics tool that identifies which insurance claims are at risk of late or non-payment — and flags them before they become a problem.

Built for **revenue cycle analysts** working in behavioral health settings.

---

## The Problem

Behavioral health clinics operate on thin margins. When insurance payers delay or deny payments, the clinic feels it fast — and so do patients, who end up absorbing costs that should have been covered.

The challenge is that not all payers behave the same way. Medicaid pays slower than BCBS. Self-pay patients take longest of all. Without visibility into these patterns, a revenue cycle analyst is always reacting instead of preventing.

---

## What This Tool Does

- **Flags late payment risk** by payer — based on historical days-to-payment patterns
- **Identifies denial trends** — which payers and billing codes are causing the most rejections
- **Quantifies patient cost burden** — how much patients are paying out of pocket, and where denials are making that worse
- **Tracks revenue leakage** — money lost to unrecovered denials, underpayments, and self-pay write-offs
- **Generates a full visual report** — 8 charts covering every dimension of revenue cycle performance

---

## Who It's For

A **revenue cycle analyst** at a behavioral health clinic who needs to:
- Prioritize which claims to follow up on first
- Report payer performance to clinical leadership
- Make the case for process changes that protect both clinic revenue and patient affordability

---

## Why It Matters to Patients

In behavioral health, a billing problem isn't just a financial inconvenience — it can interrupt care. When claims are denied and patients get unexpected bills, they disengage from treatment.

This tool connects financial performance directly to patient outcomes by surfacing the payer patterns and denial reasons that shift cost burden onto patients.

---

## Project Structure

```
bh_revenue_optimizer/
│
├── main.py               # Run this to execute the full analysis
├── data_generator.py     # Generates synthetic behavioral health claims data
├── rcm_analyzer.py       # Core analytics — computes all RCM metrics
├── visualizer.py         # Builds 8 matplotlib/seaborn charts
├── report_generator.py   # Assembles everything into an HTML report
│
├── claims_data.csv       # Generated claims dataset (1,200 claims)
├── monthly_trend.csv     # Month-by-month performance metrics
└── denial_reasons.csv    # Denial breakdown by reason and frequency
```

---

## How to Run It

**Requirements:** Python 3.8+, pandas, numpy, matplotlib, seaborn

```bash
# Install dependencies
pip install pandas numpy matplotlib seaborn

# Run the full analysis
python main.py
```

Opens `BH_Revenue_Optimizer_Report.html` in your browser — a self-contained report with all charts and recommendations embedded.

---

## Key Metrics Analyzed

| Metric | Why It Matters |
|---|---|
| Days to Payment by Payer | Predicts cash flow risk and late payment flags |
| Claim Denial Rate | Identifies payers and codes causing revenue loss |
| Patient Out-of-Pocket Burden | Connects billing performance to patient affordability |
| Revenue Leakage | Quantifies total recoverable revenue |
| Provider × Payer Collection Rate | Spots training needs and high-risk combinations |
| Monthly Trends | Tracks whether performance is improving over time |

---

## Built With

- Python 3
- pandas — data manipulation
- matplotlib / seaborn — data visualization
- numpy — numerical analysis

---

## Context

This project was built to apply **MIS and financial skills** to a real healthcare problem — demonstrating how data analysis tools can improve both clinic financial performance and patient outcomes in behavioral health settings.
