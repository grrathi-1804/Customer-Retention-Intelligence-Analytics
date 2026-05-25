# D2C Fashion Brand — Customer Retention & Intelligence Analytics

> A end-to-end consulting analytics project built with Python, SQL Server, and Power BI.
> Identifies loyal vs discount-driven customers, engineers retention metrics, and delivers
> executive-level business recommendations for a Direct-to-Consumer fashion brand.

---

## Project Overview

A D2C fashion brand was struggling with a critical but invisible problem: they could not
distinguish between customers who were genuinely loyal to the brand and customers who only
purchased when offered a discount. Without this distinction, every marketing rupee was being
spent the same way — on loyal customers who didn't need incentives and on deal-hunters who
would churn the moment discounts stopped.

This project builds the entire analytical infrastructure to answer that question — from raw
data to executive dashboard to strategic recommendations.

---

## Business Problems Solved

| Problem | Solution Built |
|---|---|
| Cannot identify truly loyal customers | Loyalty Score v2 — multi-signal metric |
| Don't know which customers are discount-dependent | Promo Dependency Score + At-Risk Flag |
| No single metric for customer value | Customer Value Index (CVI) |
| Cannot segment customers for targeted campaigns | Loyalty Tiers A/B/C/D |
| No geographic intelligence on organic vs promo markets | SQL geo-segmentation + Power BI map |
| Subscription program effectiveness unknown | Subscription × Loyalty cross-analysis |

---

## Key Findings

- **43%** of all transactions are fully promo-dependent — above the 30% industry warning threshold
- **Tier A customers generate 4.6x more value** than Tier D (CVI: 387 vs 84)
- **902 customers (23.1%)** are flagged as high-risk promo buyers — the sunset strategy target
- **Subscription program is attracting deal-hunters** — Tier D subscribes at 31.5% vs 24.8% for Tier A
- **100% of subscribers used a promo** — subscription is functioning as a discount mechanism
- **Kansas, Arizona, Texas** are the top organic markets (lowest promo dependency)
- **Gen Z is underrepresented** in Champions (73 of 406) — future loyalty opportunity
- **406 Champion customers** identified (Tier A + High Satisfaction) — brand's most valuable segment

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3 | EDA, data cleaning, feature engineering |
| Pandas | Data manipulation and transformation |
| Matplotlib / Seaborn | EDA visualizations (12 plots) |
| SQL Server (SSMS 22) | Database setup, segmentation queries, views |
| Power BI Desktop | Executive dashboard (5 pages, 25+ visuals) |

---

## Project Architecture

```
Dataset.csv (3,900 rows × 18 columns)
        │
        ▼
Phase 1 — EDA & Business Understanding
  ├── Full diagnostic (nulls, ranges, distributions)
  ├── Discount/Promo correlation analysis
  ├── Subscriber vs non-subscriber comparison
  ├── 12 EDA plots saved as PNG
  └── Output: df_phase1_clean.csv
        │
        ▼
Phase 2 — Feature Engineering
  ├── 12 new columns engineered from raw data
  ├── Two competing Loyalty Score definitions (v1 vs v2)
  ├── Loyalty Tier segmentation (A/B/C/D)
  ├── At-Risk Promo Buyer flagging
  └── Output: df_phase2_for_sql.csv (31 columns)
        │
        ▼
Phase 3 — SQL Segmentation (SQL Server)
  ├── Database: fashion_analytics
  ├── Table: fashion_customers (3,900 rows, 31 columns)
  ├── 5 core segmentation queries
  ├── 5 bonus advanced queries
  └── 5 Power BI views created
        │
        ▼
Phase 4 — Power BI Dashboard
  ├── Page 1: Executive Overview
  ├── Page 2: Customer Segments
  ├── Page 3: Geographic Intelligence
  ├── Page 4: Promo & Subscription Analysis
  └── Page 5: Champion Customers
        │
        ▼
Phase 5 — Consulting Playbook
  ├── Executive Summary (1 page)
  ├── Three Strategic Recommendations
  ├── Loyalty v2 Justification
  └── README (this file)
```

---

## Feature Engineering Summary

All 12 features were engineered from 18 raw columns in Phase 2.

| Feature | Type | Formula / Logic | Business Purpose |
|---|---|---|---|
| `promo_dependency_score` | 0 / 1 / 2 | Discount + Promo (Yes=1 each) | Identifies deal-hunters |
| `purchase_frequency_score` | 1–7 integer | Text → ordered numeric scale | Enables math on frequency |
| `customer_value_index` | Continuous | Amount × Frequency Score | True customer worth |
| `loyalty_score_v1` | Continuous | Freq × (Tenure/50) | Baseline loyalty metric |
| `loyalty_score_v1_normalized` | 0–1 float | v1 / max(v1) | Comparison baseline |
| `loyalty_score_v2` | Continuous | Freq×0.4 + Tenure×0.4 + Promo Penalty×0.2 | Primary loyalty metric |
| `loyalty_score_v2_normalized` | 0–1 float | v2 / 3.4 | Dashboard-ready metric |
| `loyalty_tier` | A / B / C / D | Quartile bins on v2_normalized | Actionable segments |
| `high_satisfaction` | 0 or 1 | Rating ≥ 4.0 | Satisfaction binary flag |
| `at_risk_promo` | 0 or 1 | Promo=2 AND loyalty < median | Sunset strategy target |
| `tenure_band` | 4 categories | Cut on Previous Purchases | Dashboard-readable labels |
| `age_segment` | 4 categories | Generational bins on Age | Marketing targeting |

### Why Loyalty v2 over v1?

v1 measures frequency and tenure only. A customer who buys weekly but **always** uses a
discount scores identically to one who buys weekly without any discount. This is wrong —
the first customer is loyal to the deal, not to the brand.

v2 adds a 20% promo independence penalty. Customers who never use discounts receive a
full bonus (0.2). Customers who always use discounts receive zero bonus. This makes v2
a more complete and defensible definition of brand loyalty.

---

## SQL Segmentation Summary

**Database:** `fashion_analytics` | **Table:** `fashion_customers` | **Rows:** 3,900

### 5 Core Queries

| Query | Business Question | Key Finding |
|---|---|---|
| Q1 — Loyal vs Discount-Driven | Do loyal customers need promos? | Tier A promo dep: 0.75 vs Tier D: 0.99 |
| Q2 — Customer Profiles | What does a high-value customer look like? | Freq score drives all CVI differences |
| Q3 — Geographic Analysis | Which states are organic markets? | Kansas (0.48), Arizona (0.68) top organic |
| Q4 — Ideal Customer Profile | Who is our best customer archetype? | Gen X, Clothing, Credit Card, Subscribed |
| Q5 — Category & Season | Which categories attract loyal customers? | Footwear highest CVI (241) |

### 5 Power BI Views Created

```sql
vw_loyalty_tier_summary   -- KPI cards and tier comparisons
vw_geo_summary            -- US map visual data
vw_at_risk_segment        -- 902 at-risk customer details
vw_champions              -- 406 champion customer profiles
vw_fashion_full           -- Complete enriched dataset
```

---

## Power BI Dashboard — 5 Pages

### Page 1 — Executive Overview
Audience: CEO / Founder
Visuals: 4 KPI cards (3900 / 966 / 902 / 406) + Loyalty Tier donut + CVI by Tier bar + Promo Dependency by Tier bar

### Page 2 — Customer Segments
Audience: Marketing Team
Visuals: Loyalty Tier by Gender + CVI by Age Segment + CVI by Category + Gender & Tier slicers

### Page 3 — Geographic Intelligence
Audience: Growth Team
Visuals: 3 KPI cards + US filled map (promo dependency) + Top 10 states by CVI + Top 10 states by at-risk % + All states summary table

### Page 4 — Promo & Subscription Analysis
Audience: Finance / Product Team
Visuals: At-risk KPI cards + Subscriber count by Tier + At-risk count by Tier + At-risk customer detail table

### Page 5 — Champion Customers
Audience: CRM / Marketing Team
Visuals: 3 KPI cards + Champions by Age + Champions by Category + Champions by Payment Method + Top champion profiles table

---

## Business Recommendations

### 1. Promo Sunset Strategy
Target the 902 at-risk promo buyers (at_risk_promo = 1) with a 3-month gradual discount
reduction — 20% less each month. Customers who stay are true brand fans worth investing in.
Customers who leave were purely deal-driven and were costing the brand margin every transaction.
**Expected impact:** 15–20% margin improvement on this segment.

### 2. Champion Protection Program
Launch a VIP tier for the 406 Champion customers (Tier A + High Satisfaction). Offer early
access, free shipping, personalized styling — no additional discounts needed. These customers
already buy without incentives. Recognition and exclusivity is what retains them.
**Expected impact:** Reduce champion churn risk, increase avg tenure by 20%.

### 3. Subscription Program Redesign
100% of current subscribers use promos. The program is functioning as a discount delivery
mechanism, not a loyalty builder. Gate the premium subscription to Tier A and B customers only.
Replace discount access with value-added benefits: early access, free returns, styling advice.
**Expected impact:** Subscription base becomes loyalty-correlated, reducing overall promo dependency.

---

## Project Files

```
📁 Project Root
├── Dataset.csv                    ← Raw data (3,900 rows × 18 columns)
├── phase1_eda.py                  ← EDA and data cleaning script
├── phase2_features.py             ← Feature engineering script
├── phase3_sql.sql                 ← SQL Server setup, queries, views
├── df_phase1_clean.csv            ← Phase 1 output (cleaned data)
├── df_phase2_features.csv         ← Phase 2 output (31 columns)
├── df_phase2_for_sql.csv          ← SQL-ready import file
├── power bi.pbix                  ← Power BI dashboard file
├── plot_01_missing_values.png     ← EDA plot 1
├── plot_02_promo_usage_pie.png    ← EDA plot 2
├── plot_03_purchase_amount.png    ← EDA plot 3
├── plot_04_previous_purchases.png ← EDA plot 4
├── plot_05_frequency.png          ← EDA plot 5
├── plot_06_review_rating.png      ← EDA plot 6
├── plot_07_demographics.png       ← EDA plot 7
├── plot_08_category_analysis.png  ← EDA plot 8
├── plot_09_seasonality.png        ← EDA plot 9
├── plot_10_correlation_heatmap.png← EDA plot 10
├── plot_11_subscriber_comparison.png ← EDA plot 11
├── plot_12_payment_shipping.png   ← EDA plot 12
├── plot_phase2_features.png       ← Feature engineering plots
└── README.md                      ← This file
```

---

## How to Run

### Phase 1 — EDA
```bash
pip install pandas numpy matplotlib seaborn
python phase1_eda.py
# Output: df_phase1_clean.csv + 12 PNG plots
```

### Phase 2 — Feature Engineering
```bash
python phase2_features.py
# Input:  df_phase1_clean.csv
# Output: df_phase2_for_sql.csv (31 columns)
```

### Phase 3 — SQL
```
1. Open SQL Server Management Studio 22
2. Open phase3_sql.sql
3. Run Stage A (database + table creation)
4. Import df_phase2_for_sql.csv using Import Flat File wizard
5. Run Stage B (validation — all checks must pass)
6. Run Stage C (5 core queries)
7. Run Stage D (5 bonus queries)
8. Run Stage E (create 5 views)
```

### Phase 4 — Power BI
```
1. Open Power BI Desktop
2. Get Data → SQL Server → localhost → fashion_analytics
3. Select all 5 views
4. Load → build 5 dashboard pages
```

---

## Dataset

- **Source:** Kaggle — Shopping Trends Dataset
- **Size:** 3,900 rows × 18 columns
- **Type:** Synthetic D2C fashion retail data
- **Key columns:** Customer ID, Age, Gender, Item Purchased, Category,
  Purchase Amount, Location, Season, Review Rating, Subscription Status,
  Discount Applied, Promo Code Used, Previous Purchases, Frequency of Purchases

---

## About

Built as a consulting analytics portfolio project by a Production Engineering student
at NIT Trichy. Designed to demonstrate end-to-end data analytics skills across
Python, SQL, and Power BI in a business consulting context.

**Skills demonstrated:**
- Exploratory Data Analysis with business interpretation
- Feature Engineering with justifiable business logic
- SQL database design and segmentation queries
- Power BI dashboard design for executive audiences
- Consulting-style recommendation writing
- Data storytelling and project documentation
