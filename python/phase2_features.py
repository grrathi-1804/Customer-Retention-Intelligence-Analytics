# =============================================================================
# PHASE 2 — FEATURE ENGINEERING
# Project : D2C Fashion Brand — Customer Intelligence & Retention Analytics
# Author  : NIT Trichy — Production Engineering
# Input   : df_phase1_clean.csv  (output from Phase 1)
# Output  : df_phase2_features.csv  (input for Phase 3 SQL)
# =============================================================================

# ── What is Feature Engineering? ─────────────────────────────────────────
# The raw dataset has 18 columns. But it does NOT have the columns that
# answer business questions. Nobody in the raw data told you:
#   - "Is this customer loyal?"
#   - "Is this customer discount-dependent?"
#   - "What is this customer's true value to the brand?"
#
# Feature Engineering = creating those metrics from the raw data.
# Think of it as translating raw ingredients into actual dishes.
# The dishes are what the CEO, the SQL queries, and the ML model consume.
# ─────────────────────────────────────────────────────────────────────────

import warnings
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
warnings.filterwarnings('ignore')

sns.set_theme(style='whitegrid', palette='muted', font_scale=1.1)
plt.rcParams.update({'figure.dpi': 130})
BRAND_COLORS = ['#2C3E50', '#E74C3C', '#3498DB', '#2ECC71', '#F39C12',
                '#9B59B6', '#1ABC9C']

# ── Load Phase 1 output ───────────────────────────────────────────────────
df = pd.read_csv('df_phase1_clean.csv')
print(f"Loaded: {df.shape[0]} rows × {df.shape[1]} columns")
print(f"Columns: {list(df.columns)}\n")

# =============================================================================
# FEATURE 1 — PROMO DEPENDENCY SCORE (0–2)
# =============================================================================

# ── What it is ────────────────────────────────────────────────────────────
# Add: Discount_Applied (Yes=1, No=0) + Promo_Code_Used (Yes=1, No=0)
# Score 0 = Never used discount or promo   → Self-sustaining buyer
# Score 1 = Inconsistent (shouldn't exist given 100% correlation in data)
# Score 2 = Always used discount AND promo → Promotion-dependent buyer
#
# ── Business Impact ───────────────────────────────────────────────────────
# A customer with score 2 is buying BECAUSE of a deal, not because of
# brand love. If you stop offering discounts to them, they likely churn.
# These customers also have the LOWEST margin contribution — they always
# buy at reduced price. The key consulting question is:
# "Are we acquiring loyal customers, or just deal-hunters?"
# ─────────────────────────────────────────────────────────────────────────

df['promo_dependency_score'] = (
    (df['discount_applied'] == 'Yes').astype(int) +
    (df['promo_code_used'] == 'Yes').astype(int)
)

print("=" * 60)
print("  FEATURE 1: Promo Dependency Score")
print("=" * 60)
print(df['promo_dependency_score'].value_counts().sort_index())
print(f"\n  % of customers with max promo dependency (score=2): "
      f"{(df['promo_dependency_score'] == 2).mean() * 100:.1f}%")

# =============================================================================
# FEATURE 2 — PURCHASE FREQUENCY SCORE (Numerical Encoding)
# =============================================================================

# ── What it is ────────────────────────────────────────────────────────────
# Converts the 7 text categories into an ordered integer 1–7.
# The scale is ORDINAL — the gaps matter (Weekly is ~7x more frequent
# than Annual, not just 1 step higher).
#
# ── Why not just use LabelEncoder? ───────────────────────────────────────
# LabelEncoder assigns arbitrary numbers (alphabetical order).
# It might encode Annual=0, Bi-Weekly=1, Fortnightly=2, etc.
# That's WRONG because it doesn't preserve the business meaning.
# We manually assign values that reflect real-world purchase intervals.
# ─────────────────────────────────────────────────────────────────────────

FREQ_MAP = {
    'Weekly': 7,
    'Fortnightly': 6,     # Every 2 weeks
    'Bi-Weekly': 5,       # Can mean bi-monthly in some contexts; kept at 5
    'Monthly': 4,
    'Quarterly': 3,
    'Every 3 Months': 2,
    'Annually': 1
}

df['purchase_frequency_score'] = df['frequency_of_purchases'].map(FREQ_MAP)

print("\n" + "=" * 60)
print("  FEATURE 2: Purchase Frequency Score")
print("=" * 60)
mapping_df = pd.DataFrame(list(FREQ_MAP.items()),
                          columns=['Category', 'Score']).sort_values('Score', ascending=False)
print(mapping_df.to_string(index=False))
print(f"\n  Unmapped values: {df['purchase_frequency_score'].isnull().sum()}")
print(
    f"  Score distribution:\n{df['purchase_frequency_score'].value_counts().sort_index()}")

# =============================================================================
# FEATURE 3 — CUSTOMER VALUE INDEX (CVI)
# =============================================================================

# ── What it is ────────────────────────────────────────────────────────────
# CVI = Purchase Amount (USD) × Purchase Frequency Score
#
# ── Business Impact ───────────────────────────────────────────────────────
# Example:
#   Customer A: Spends $90, buys Annually  → CVI = 90 × 1 = 90
#   Customer B: Spends $50, buys Weekly    → CVI = 50 × 7 = 350
#
# Customer B is worth ~4x more to the brand per year despite spending
# less per transaction. CVI captures this. It answers the most
# important retention question: "Who are our highest-value customers?"
#
# NOTE: CVI is a RELATIVE index, not a true dollar revenue figure,
# because frequency scores are ordinal (not actual purchase counts).
# Use it for ranking and segmentation, not absolute revenue math.
# ─────────────────────────────────────────────────────────────────────────

df['customer_value_index'] = (df['purchase_amount_usd'] *
                              df['purchase_frequency_score'])

print("\n" + "=" * 60)
print("  FEATURE 3: Customer Value Index (CVI)")
print("=" * 60)
print(df['customer_value_index'].describe().round(2).to_string())
print(f"\n  Min CVI: {df['customer_value_index'].min()} "
      f"(${df.loc[df['customer_value_index'].idxmin(), 'purchase_amount_usd']} × Annually)")
print(f"  Max CVI: {df['customer_value_index'].max()} "
      f"(${df.loc[df['customer_value_index'].idxmax(), 'purchase_amount_usd']} × Weekly)")

# =============================================================================
# FEATURE 4 — LOYALTY SCORE v1 (Frequency × Tenure)
# =============================================================================

# ── Formula ───────────────────────────────────────────────────────────────
# Loyalty_v1 = Purchase_Frequency_Score × (Previous_Purchases / 50)
#
# Component breakdown:
#   Purchase_Frequency_Score   → How often do they buy? (0–7 scale)
#   Previous_Purchases / 50    → Normalized tenure (0.02 to 1.0)
#
# The result ranges from near 0 (infrequent, new customer)
# to 7.0 (weekly buyer with 50 previous purchases).
#
# ── Limitation of v1 ─────────────────────────────────────────────────────
# v1 ignores whether the customer needs a promotion to buy.
# A customer who buys weekly but ONLY with discounts still gets a
# high v1 score. This overstates their true loyalty.
# ─────────────────────────────────────────────────────────────────────────

df['loyalty_score_v1'] = (df['purchase_frequency_score'] *
                          (df['previous_purchases'] / 50))

print("\n" + "=" * 60)
print("  FEATURE 4: Loyalty Score v1 (Frequency × Tenure)")
print("=" * 60)
print(df['loyalty_score_v1'].describe().round(4).to_string())

# =============================================================================
# FEATURE 5 — LOYALTY SCORE v2 (Multi-Signal: Best Version)
# =============================================================================

# ── Formula ───────────────────────────────────────────────────────────────
# Loyalty_v2 = (Freq_Score × 0.4) +
#              (Previous_Purchases/50 × 0.4) +
#              ((1 - Promo_Dependency/2) × 0.2)
#
# Weight rationale:
#   40% Frequency  — HOW OFTEN they buy is the strongest signal
#   40% Tenure     — HOW LONG they've been around
#   20% Promo Penalty — DO they buy independently of deals?
#
# The promo component works as follows:
#   Promo_Dependency = 0 → (1 - 0/2) = 1.0 → full bonus (0.2)
#   Promo_Dependency = 2 → (1 - 2/2) = 0.0 → no bonus (0.0)
#   So discount-dependent customers are penalized.
#
# ── Why v2 > v1? ─────────────────────────────────────────────────────────
# v2 is a more COMPLETE definition of loyalty. Loyalty is not just
# "how often you show up" — it's also "why you show up."
# A customer who shows up every week because of discounts is not
# truly loyal to the brand — they're loyal to the deal.
# v2 captures this nuance. In your consulting report, argue for v2
# as the primary metric. v1 is a comparison baseline.
# ─────────────────────────────────────────────────────────────────────────

df['loyalty_score_v2'] = (
    (df['purchase_frequency_score'] * 0.4) +
    ((df['previous_purchases'] / 50) * 0.4) +
    ((1 - df['promo_dependency_score'] / 2) * 0.2)
)

# Normalize v2 to 0–1 range for easier interpretation in dashboards
# Max theoretical v2: (7 × 0.4) + (1.0 × 0.4) + (1.0 × 0.2) = 3.4
v2_max = (7 * 0.4) + (1.0 * 0.4) + (1.0 * 0.2)
df['loyalty_score_v2_normalized'] = (df['loyalty_score_v2'] / v2_max).round(4)

print("\n" + "=" * 60)
print("  FEATURE 5: Loyalty Score v2 (Multi-Signal)")
print("=" * 60)
print(f"  Theoretical max v2 raw: {v2_max}")
print(f"\n  v2 Raw Stats:")
print(df['loyalty_score_v2'].describe().round(4).to_string())
print(f"\n  v2 Normalized (0–1) Stats:")
print(df['loyalty_score_v2_normalized'].describe().round(4).to_string())

# =============================================================================
# FEATURE 6 — LOYALTY TIER (A / B / C / D)
# =============================================================================

# ── What it is ────────────────────────────────────────────────────────────
# Bin loyalty_score_v2_normalized into 4 quartile-based tiers:
#   Tier A = Top 25% → Most Loyal → Protect at all costs
#   Tier B = 50–75%  → Strong     → Upsell and upgrade
#   Tier C = 25–50%  → Average    → Engage and nurture
#   Tier D = Bottom 25% → Low     → Risk of churn / re-engage
#
# We use quantile-based binning (not equal-width) because real
# customer distributions are uneven. Quartiles guarantee each tier
# always has exactly 25% of customers, making comparisons fair.
# ─────────────────────────────────────────────────────────────────────────

df['loyalty_tier'] = pd.qcut(
    df['loyalty_score_v2_normalized'],
    q=4,
    labels=['D', 'C', 'B', 'A'],
    duplicates='drop'
)

print("\n" + "=" * 60)
print("  FEATURE 6: Loyalty Tier (A–D)")
print("=" * 60)

tier_summary = df.groupby('loyalty_tier').agg(
    Count=('customer_id', 'count'),
    Avg_Loyalty_v2=('loyalty_score_v2_normalized', 'mean'),
    Avg_Spend=('purchase_amount_usd', 'mean'),
    Avg_Tenure=('previous_purchases', 'mean'),
    Promo_Rate=('promo_dependency_score', lambda x: (x == 2).mean() * 100)
).round(3)
tier_summary.columns = ['Count', 'Avg Loyalty v2',
                        'Avg Spend', 'Avg Tenure', 'Promo Dep %']
print(tier_summary.to_string())

# =============================================================================
# FEATURE 7 — HIGH SATISFACTION FLAG
# =============================================================================

# ── What it is ────────────────────────────────────────────────────────────
# high_satisfaction = 1 if review_rating >= 4.0, else 0
# rating_missing   = 1 if the rating was originally null (from Phase 1)
#
# ── Business Impact ───────────────────────────────────────────────────────
# Combining satisfaction with loyalty tier answers a critical question:
#
#   Tier A + High Satisfaction = "Champions" — your brand advocates
#   Tier A + Low Satisfaction  = "At-Risk Loyals" — urgent action needed
#   Tier D + Low Satisfaction  = "About to Churn" — expensive to retain
#
# This 2x2 matrix is a standard retention consulting framework.
# ─────────────────────────────────────────────────────────────────────────

df['high_satisfaction'] = (df['review_rating'] >= 4.0).astype(int)
# Note: rating_missing column already exists from Phase 1 cleaning

print("\n" + "=" * 60)
print("  FEATURE 7: High Satisfaction Flag")
print("=" * 60)
print(f"  High Satisfaction (≥4.0) : {df['high_satisfaction'].sum():,} "
      f"({df['high_satisfaction'].mean() * 100:.1f}%)")
print(f"  Low Satisfaction  (<4.0) : {(df['high_satisfaction'] == 0).sum():,} "
      f"({(df['high_satisfaction'] == 0).mean() * 100:.1f}%)")
print(f"  Originally missing rating: {df['rating_missing'].sum():,}")

# =============================================================================
# FEATURE 8 — HIGH-RISK PROMO BUYER FLAG
# =============================================================================

# ── What it is ────────────────────────────────────────────────────────────
# at_risk_promo = 1 if:
#   • Promo Dependency Score = 2 (always uses discount)  AND
#   • Loyalty v2 Normalized < median (below average loyalty)
#
# ── Business Impact ───────────────────────────────────────────────────────
# These are the MOST DANGEROUS customers from a business perspective:
#   - They cost the brand money every transaction (discounted price)
#   - They have low loyalty (likely to churn when promos stop)
#   - They "fake" engagement metrics (high transaction count from promos)
#
# The "Sunset Strategy" from consulting: gradually reduce discounts
# for this segment and observe who stays (true brand fans) vs. who
# leaves (deal hunters). This is Phase 5's key recommendation.
# ─────────────────────────────────────────────────────────────────────────

loyalty_median = df['loyalty_score_v2_normalized'].median()
df['at_risk_promo'] = (
    (df['promo_dependency_score'] == 2) &
    (df['loyalty_score_v2_normalized'] < loyalty_median)
).astype(int)

print("\n" + "=" * 60)
print("  FEATURE 8: High-Risk Promo Buyer Flag")
print("=" * 60)
print(f"  Loyalty v2 Median (threshold): {loyalty_median:.4f}")
print(f"  High-Risk Promo Buyers: {df['at_risk_promo'].sum():,} "
      f"({df['at_risk_promo'].mean() * 100:.1f}% of all customers)")
print("  These are promo-dependent AND below-median loyalty.")

# =============================================================================
# BONUS FEATURE 9 — TENURE BAND (New / Growing / Established / Veteran)
# =============================================================================

# ── Why add this? ─────────────────────────────────────────────────────────
# Previous Purchases as a number is hard to interpret in a dashboard.
# Banding it gives executives an instant mental model.
# This also makes SQL GROUP BY queries much cleaner.
# ─────────────────────────────────────────────────────────────────────────

df['tenure_band'] = pd.cut(
    df['previous_purchases'],
    bins=[0, 10, 25, 40, 50],
    labels=['New (1–10)', 'Growing (11–25)',
            'Established (26–40)', 'Veteran (41–50)'],
    include_lowest=True
)

print("\n" + "=" * 60)
print("  BONUS FEATURE 9: Tenure Band")
print("=" * 60)
print(df['tenure_band'].value_counts().sort_index())

# =============================================================================
# BONUS FEATURE 10 — AGE SEGMENT (Gen Z / Millennial / Gen X / Boomer)
# =============================================================================

# ── Why add this? ─────────────────────────────────────────────────────────
# Age segments are useful for marketing strategy and campaign targeting.
# Gen Z responds to social media ads; Boomers prefer email.
# This feature enables demographic breakdowns in the Power BI dashboard.
# ─────────────────────────────────────────────────────────────────────────

df['age_segment'] = pd.cut(
    df['age'],
    bins=[17, 27, 42, 57, 70],
    labels=['Gen Z (18–27)', 'Millennial (28–42)',
            'Gen X (43–57)', 'Boomer (58–70)'],
    include_lowest=True
)

print("\n" + "=" * 60)
print("  BONUS FEATURE 10: Age Segment")
print("=" * 60)
print(df['age_segment'].value_counts().sort_index())

# =============================================================================
# FEATURE COMPARISON: LOYALTY v1 vs v2
# =============================================================================

print("\n" + "=" * 60)
print("  LOYALTY v1 vs v2 — WHICH IS BETTER?")
print("=" * 60)

# Normalize v1 to same 0–1 scale for fair comparison
v1_max = df['loyalty_score_v1'].max()
df['loyalty_score_v1_normalized'] = df['loyalty_score_v1'] / v1_max

correlation = df[['loyalty_score_v1_normalized',
                  'loyalty_score_v2_normalized']].corr()
print(f"  Correlation between v1 and v2: "
      f"{correlation.iloc[0, 1]:.4f}")

# Find customers where v1 and v2 disagree significantly
diff = (df['loyalty_score_v1_normalized'] -
        df['loyalty_score_v2_normalized']).abs()
significant_diff = (diff > 0.15).sum()
print(
    f"  Customers with >0.15 score gap between v1 and v2: {significant_diff}")
print(f"  → These are exactly the discount-dependent customers that v2")
print(f"    correctly PENALIZES but v1 incorrectly REWARDS.")
print(f"\n  RECOMMENDATION: Use Loyalty v2 as primary metric.")
print(f"  v2 is more complete, more defensible, and more actionable.")

# =============================================================================
# VISUALIZATIONS — FEATURE ENGINEERING RESULTS
# =============================================================================

fig, axes = plt.subplots(2, 3, figsize=(16, 10))
fig.suptitle('Phase 2 — Feature Engineering: Distributions & Insights',
             fontsize=14, fontweight='bold', y=1.01)

# Plot A: Promo Dependency Score
promo_counts = df['promo_dependency_score'].value_counts().sort_index()
axes[0, 0].bar(promo_counts.index, promo_counts.values,
               color=['#2ECC71', '#F39C12', '#E74C3C'], edgecolor='white')
axes[0, 0].set_title('Promo Dependency Score', fontweight='bold')
axes[0, 0].set_xlabel('Score (0=Never, 2=Always)')
axes[0, 0].set_ylabel('Count')
for i, v in enumerate(promo_counts.values):
    axes[0, 0].text(promo_counts.index[i], v + 10,
                    f'{v:,}', ha='center', fontsize=9)

# Plot B: CVI distribution
axes[0, 1].hist(df['customer_value_index'], bins=30,
                color='#3498DB', edgecolor='white', alpha=0.85)
axes[0, 1].axvline(df['customer_value_index'].median(), color='#E74C3C',
                   linestyle='--', linewidth=1.5,
                   label=f"Median: {df['customer_value_index'].median():.0f}")
axes[0, 1].set_title('Customer Value Index (CVI)', fontweight='bold')
axes[0, 1].set_xlabel('CVI (Amount × Frequency Score)')
axes[0, 1].legend(fontsize=8)

# Plot C: Loyalty v1 vs v2 scatter
axes[0, 2].scatter(df['loyalty_score_v1_normalized'],
                   df['loyalty_score_v2_normalized'],
                   alpha=0.3, s=8, color='#9B59B6')
axes[0, 2].plot([0, 1], [0, 1], 'r--', linewidth=1, label='Perfect agreement')
axes[0, 2].set_xlabel('Loyalty v1 (normalized)')
axes[0, 2].set_ylabel('Loyalty v2 (normalized)')
axes[0, 2].set_title('Loyalty v1 vs v2\n(Points below line = penalized by v2)',
                     fontweight='bold')
axes[0, 2].legend(fontsize=8)

# Plot D: Loyalty Tier Distribution
tier_counts = df['loyalty_tier'].value_counts().sort_index(ascending=False)
bars = axes[1, 0].bar(tier_counts.index, tier_counts.values,
                      color=['#2ECC71', '#3498DB', '#F39C12', '#E74C3C'],
                      edgecolor='white')
axes[1, 0].set_title('Loyalty Tier Distribution', fontweight='bold')
axes[1, 0].set_xlabel('Loyalty Tier (A=Best, D=Worst)')
axes[1, 0].set_ylabel('Count')
for bar in bars:
    axes[1, 0].text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 5,
                    str(int(bar.get_height())), ha='center', fontsize=9)

# Plot E: CVI by Loyalty Tier (Box Plot)
tier_order = ['A', 'B', 'C', 'D']
data_to_plot = [df[df['loyalty_tier'] == t]['customer_value_index'].values
                for t in tier_order]
bp = axes[1, 1].boxplot(data_to_plot, labels=tier_order,
                        patch_artist=True,
                        medianprops=dict(color='white', linewidth=2))
colors = ['#2ECC71', '#3498DB', '#F39C12', '#E74C3C']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.8)
axes[1, 1].set_title('CVI Distribution by Loyalty Tier', fontweight='bold')
axes[1, 1].set_xlabel('Loyalty Tier')
axes[1, 1].set_ylabel('Customer Value Index')

# Plot F: At-Risk Promo Buyers by Loyalty Tier
risk_by_tier = df.groupby('loyalty_tier')['at_risk_promo'].mean() * 100
axes[1, 2].bar(risk_by_tier.index, risk_by_tier.values,
               color=['#2ECC71', '#3498DB', '#F39C12', '#E74C3C'],
               edgecolor='white')
axes[1, 2].set_title('At-Risk Promo Buyers by Tier (%)', fontweight='bold')
axes[1, 2].set_xlabel('Loyalty Tier')
axes[1, 2].set_ylabel('% Flagged as High-Risk Promo')
for i, v in enumerate(risk_by_tier.values):
    axes[1, 2].text(i, v + 0.5, f'{v:.1f}%', ha='center', fontsize=9)

plt.tight_layout()
plt.savefig('plot_phase2_features.png')
# plt.show()
print("\n  [Saved] plot_phase2_features.png")

# =============================================================================
# LOYALTY TIER × SATISFACTION 2×2 MATRIX
# =============================================================================

print("\n" + "=" * 60)
print("  LOYALTY TIER × SATISFACTION MATRIX")
print("  (Consulting Framework: Know which customers to prioritize)")
print("=" * 60)

matrix = pd.crosstab(
    df['loyalty_tier'], df['high_satisfaction'],
    values=df['customer_id'], aggfunc='count',
    margins=True
)
matrix.columns = [
    'Low Satisfaction (<4.0)', 'High Satisfaction (≥4.0)', 'Total']
print(matrix.to_string())

print("\n  INTERPRETATION:")
print("  ► Tier A + High Satisfaction = Champions → Protect, give VIP perks")
print("  ► Tier A + Low Satisfaction  = At-Risk   → Immediate intervention")
print("  ► Tier D + Low Satisfaction  = Dormant   → Low-cost re-engagement")
print("  ► Tier D + High Satisfaction = Dormant Happy → Easy upsell targets")

# Heatmap of the matrix
pivot = df.groupby(['loyalty_tier', 'high_satisfaction']).size().unstack()
pivot.columns = ['Low Sat.', 'High Sat.']
fig, ax = plt.subplots(figsize=(6, 4))
sns.heatmap(pivot, annot=True, fmt='d', cmap='YlOrRd', ax=ax,
            linewidths=0.5, cbar_kws={'label': 'Customer Count'})
ax.set_title('Loyalty Tier × Satisfaction Matrix\n(Consulting Prioritization Grid)',
             fontweight='bold')
ax.set_xlabel('Satisfaction Level')
ax.set_ylabel('Loyalty Tier')
plt.tight_layout()
plt.savefig('plot_phase2_loyalty_satisfaction_matrix.png')
# plt.show()
print("  [Saved] plot_phase2_loyalty_satisfaction_matrix.png")

# =============================================================================
# FINAL FEATURE SUMMARY & EXPORT
# =============================================================================

print("\n" + "=" * 60)
print("  FEATURE ENGINEERING COMPLETE — ALL NEW COLUMNS")
print("=" * 60)

new_features = [
    ('promo_dependency_score', '0–2 integer', 'Promo/discount reliance'),
    ('purchase_frequency_score', '1–7 integer', 'Ordinal frequency encoding'),
    ('customer_value_index', 'Continuous', 'Amount × Frequency Score'),
    ('loyalty_score_v1', 'Continuous', 'Freq × Tenure (simple baseline)'),
    ('loyalty_score_v1_normalized', '0–1 float', 'Normalized v1 for comparison'),
    ('loyalty_score_v2', 'Continuous', 'Freq × Tenure × Promo penalty'),
    ('loyalty_score_v2_normalized', '0–1 float', 'Normalized v2 (primary metric)'),
    ('loyalty_tier', 'A/B/C/D', 'Quartile-based tier'),
    ('high_satisfaction', '0 or 1 binary', 'Rating ≥ 4.0'),
    ('at_risk_promo', '0 or 1 binary', 'Promo-dep. AND below-median loyalty'),
    ('tenure_band', '4 categories', 'New / Growing / Established / Veteran'),
    ('age_segment', '4 categories', 'Gen Z / Millennial / Gen X / Boomer'),
]

print(f"  {'Feature':<35} {'Type':<20} {'Business Meaning'}")
print("  " + "-" * 85)
for feature, dtype, meaning in new_features:
    print(f"  {feature:<35} {dtype:<20} {meaning}")

print(f"\n  Total columns after Phase 2: {df.shape[1]}")

# Export for Phase 3 (SQL)
df.to_csv('df_phase2_features.csv', index=False)
print("\n  [Saved] df_phase2_features.csv  ← Input for Phase 3 SQL")

# Export a lightweight version for SQL import (convert categoricals to str)
df_sql = df.copy()
for col in df_sql.select_dtypes(include='category').columns:
    df_sql[col] = df_sql[col].astype(str)
df_sql.to_csv('df_phase2_for_sql.csv', index=False)
print("  [Saved] df_phase2_for_sql.csv   ← SQL-ready (no categorical dtype)")

print("\n" + "=" * 60)
print("  PHASE 2 COMPLETE. READY FOR PHASE 3 SQL SEGMENTATION.")
print("=" * 60)

# =============================================================================
# KEY NUMBERS TO REMEMBER (for your consulting presentation)
# =============================================================================

print("\n" + "=" * 60)
print("  KEY NUMBERS — SHARE IN YOUR PRESENTATION")
print("=" * 60)

at_risk_count = df['at_risk_promo'].sum()
total = len(df)
tier_a = (df['loyalty_tier'] == 'A').sum()
tier_d = (df['loyalty_tier'] == 'D').sum()
champions = ((df['loyalty_tier'] == 'A') & (
    df['high_satisfaction'] == 1)).sum()
promo_dep_pct = (df['promo_dependency_score'] == 2).mean() * 100

print(f"\n  → {promo_dep_pct:.1f}% of customers are fully promo-dependent")
print(f"  → {at_risk_count:,} customers ({at_risk_count/total*100:.1f}%) are HIGH-RISK promo buyers")
print(f"  → {tier_a:,} Tier A (Most Loyal) customers — protect these")
print(f"  → {tier_d:,} Tier D (Least Loyal) customers — churn risk")
print(f"  → {champions:,} 'Champion' customers (Tier A + High Satisfaction)")
print(
    f"  → {df['rating_missing'].sum()} customers never left a review (silent risk)")
