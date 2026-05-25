# =============================================================================
# PHASE 1 — BUSINESS UNDERSTANDING & EXPLORATORY DATA ANALYSIS
# Project : D2C Fashion Brand — Customer Intelligence & Retention Analytics
# Author  : NIT Trichy — Production Engineering
# Stack   : Python, Pandas, Matplotlib, Seaborn
# =============================================================================

# ── Why EDA before anything else? ────────────────────────────────────────────
# A consultant never opens Excel and starts building formulas.
# They first ask: What does the data represent? What is missing?
# What is surprising? What business questions can this data answer?
# EDA is your "discovery call" with the dataset.
# ─────────────────────────────────────────────────────────────────────────────

import warnings
import seaborn as sns
import matplotlib.ticker as mticker
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
warnings.filterwarnings('ignore')

# ── Visual style ─────────────────────────────────────────────────────────────
sns.set_theme(style='whitegrid', palette='muted', font_scale=1.1)
plt.rcParams.update({'figure.dpi': 130, 'figure.figsize': (10, 5)})
BRAND_COLORS = ['#2C3E50', '#E74C3C', '#3498DB', '#2ECC71', '#F39C12',
                '#9B59B6', '#1ABC9C']

# =============================================================================
# SECTION 0 — LOAD & FIRST LOOK
# =============================================================================

df = pd.read_csv('Dataset.csv')

print("=" * 60)
print("  DATASET FIRST LOOK")
print("=" * 60)
print(f"  Rows     : {df.shape[0]:,}")
print(f"  Columns  : {df.shape[1]}")
print(f"  Memory   : {df.memory_usage(deep=True).sum() / 1024:.1f} KB")
print("=" * 60)

# ── Business interpretation ───────────────────────────────────────────────
# 3,900 customers — small enough for full analysis, large enough for
# meaningful segments. No date/timestamp column exists, which means we
# cannot do traditional time-series cohort analysis. Our proxy for
# "how long has this customer been around" will be Previous Purchases.
# ─────────────────────────────────────────────────────────────────────────

print("\n── Column Overview ──")
print(df.dtypes.to_frame(name='dtype').assign(
    sample=df.iloc[0]
).to_string())

# =============================================================================
# SECTION 1 — MISSING VALUES AUDIT
# =============================================================================

print("\n" + "=" * 60)
print("  MISSING VALUES AUDIT")
print("=" * 60)

missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(2)
missing_report = pd.DataFrame({
    'Missing Count': missing,
    'Missing %': missing_pct
}).query('`Missing Count` > 0')

print(missing_report.to_string())

# ── Business interpretation ───────────────────────────────────────────────
# Only Review Rating has 37 nulls (~0.95% of data). This is very low.
# Two options:
#   Option A — Impute with median (3.8) → Safe for models, loses nuance.
#   Option B — Add a separate flag column "Rating_Missing = 1" and impute
#              with median. This lets SQL/BI tools identify "silent"
#              customers who never left a review. That's a business signal!
#              A customer who never rates may be indifferent — a churn risk.
# We will go with Option B in Phase 2.
# ─────────────────────────────────────────────────────────────────────────

# ── PLOT 1: Missing values bar chart ──────────────────────────────────────
if not missing_report.empty:
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.barh(missing_report.index, missing_report['Missing %'],
            color='#E74C3C', edgecolor='white')
    ax.set_xlabel('Missing %')
    ax.set_title('Missing Values by Column', fontweight='bold')
    for i, v in enumerate(missing_report['Missing %']):
        ax.text(v + 0.05, i, f'{v}%', va='center', fontsize=10)
    plt.tight_layout()
    plt.savefig('plot_01_missing_values.png')
    # plt.show()
    print("  [Saved] plot_01_missing_values.png")

# =============================================================================
# SECTION 2 — DISCOUNT & PROMO CORRELATION CHECK
# =============================================================================

print("\n" + "=" * 60)
print("  DISCOUNT vs PROMO CODE CORRELATION")
print("=" * 60)

cross = pd.crosstab(df['Discount Applied'], df['Promo Code Used'],
                    margins=True, margins_name='Total')
print(cross)

# Perfect alignment check
mismatch = df[df['Discount Applied'] != df['Promo Code Used']].shape[0]
print(f"\n  Rows where Discount ≠ Promo Code: {mismatch}")
print("  → These two columns are 100% correlated.")
print("  → In Phase 2 we combine them into a single Promo_Dependency_Score.")

# ── Business interpretation ───────────────────────────────────────────────
# This 1:1 match is not a coincidence — it reflects how the brand's
# system works. A discount is ALWAYS paired with a promo code and vice
# versa. This means:
#   1. We don't need both columns — one is redundant.
#   2. ~43% of transactions use a discount. That's very high for a
#      D2C brand. It suggests the brand may be over-relying on promos
#      to drive sales — a margin risk and a loyalty quality risk.
# ─────────────────────────────────────────────────────────────────────────

# ── PLOT 2: Pie chart of promo usage ─────────────────────────────────────
promo_counts = df['Discount Applied'].value_counts()
fig, ax = plt.subplots(figsize=(6, 6))
wedges, texts, autotexts = ax.pie(
    promo_counts, labels=promo_counts.index,
    autopct='%1.1f%%', startangle=90,
    colors=['#2C3E50', '#E74C3C'], explode=(0, 0.05)
)
ax.set_title('What % of Transactions Used a Discount/Promo?',
             fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig('plot_02_promo_usage_pie.png')
# plt.show()
print("  [Saved] plot_02_promo_usage_pie.png")

# =============================================================================
# SECTION 3 — PURCHASE AMOUNT DISTRIBUTION
# =============================================================================

print("\n" + "=" * 60)
print("  PURCHASE AMOUNT (USD) ANALYSIS")
print("=" * 60)
print(df['Purchase Amount (USD)'].describe().round(2).to_string())

# ── Business interpretation ───────────────────────────────────────────────
# Range: $20–$100. Mean: ~$60. This is a narrow range.
# In real e-commerce, order values span $5 to $500+. Here the brand
# sells in one price tier. This means:
#   • A single purchase value is a WEAK loyalty signal.
#   • You can't say "this customer spent $90 so they're loyal."
#     A $90 purchase could be an annual buyer who found a good deal.
#   • Loyalty must come from FREQUENCY × SPEND, not spend alone.
#   • This reinforces why the Customer Value Index (CVI) in Phase 2
#     is the right metric: CVI = Amount × Frequency Score.
# ─────────────────────────────────────────────────────────────────────────

# ── PLOT 3: Purchase Amount histogram + KDE ──────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Histogram
axes[0].hist(df['Purchase Amount (USD)'], bins=30,
             color='#3498DB', edgecolor='white', alpha=0.85)
axes[0].axvline(df['Purchase Amount (USD)'].mean(), color='#E74C3C',
                linestyle='--', linewidth=1.5,
                label=f"Mean: ${df['Purchase Amount (USD)'].mean():.1f}")
axes[0].set_xlabel('Purchase Amount (USD)')
axes[0].set_ylabel('Frequency')
axes[0].set_title('Purchase Amount Distribution', fontweight='bold')
axes[0].legend()

# By discount
df[df['Discount Applied'] == 'Yes']['Purchase Amount (USD)'].plot.kde(
    ax=axes[1], color='#E74C3C', label='Discount Applied', linewidth=2)
df[df['Discount Applied'] == 'No']['Purchase Amount (USD)'].plot.kde(
    ax=axes[1], color='#2C3E50', label='No Discount', linewidth=2)
axes[1].set_xlabel('Purchase Amount (USD)')
axes[1].set_title('Purchase Amount: Discount vs No Discount',
                  fontweight='bold')
axes[1].legend()

plt.tight_layout()
plt.savefig('plot_03_purchase_amount.png')
# plt.show()
print("  [Saved] plot_03_purchase_amount.png")

# =============================================================================
# SECTION 4 — PREVIOUS PURCHASES (TENURE PROXY)
# =============================================================================

print("\n" + "=" * 60)
print("  PREVIOUS PURCHASES — OUR TENURE PROXY")
print("=" * 60)
print(df['Previous Purchases'].describe().round(2).to_string())

# ── Business interpretation ───────────────────────────────────────────────
# Range: 1–50. Mean: ~25. Uniform-ish distribution (std ≈ 14).
# This is the closest thing we have to "how long this customer has
# been with the brand." No signup date exists. Think of it as:
#   • 1–10  = New customer (just joined or rarely returned)
#   • 11–25 = Growing customer
#   • 26–40 = Established customer
#   • 41–50 = Veteran customer
# In Phase 3, SQL will segment on this. In Loyalty formulas, it's
# normalized to 0–1 by dividing by 50 (the max).
# ─────────────────────────────────────────────────────────────────────────

# ── PLOT 4: Previous Purchases histogram ─────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(df['Previous Purchases'], bins=25,
        color='#2ECC71', edgecolor='white', alpha=0.85)
ax.axvline(df['Previous Purchases'].mean(), color='#E74C3C',
           linestyle='--', linewidth=1.5,
           label=f"Mean: {df['Previous Purchases'].mean():.1f}")
ax.axvline(df['Previous Purchases'].median(), color='#F39C12',
           linestyle=':', linewidth=1.5,
           label=f"Median: {df['Previous Purchases'].median():.1f}")
ax.set_xlabel('Previous Purchases (Tenure Proxy)')
ax.set_ylabel('Number of Customers')
ax.set_title('Distribution of Previous Purchases — Tenure Proxy',
             fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig('plot_04_previous_purchases.png')
# plt.show()
print("  [Saved] plot_04_previous_purchases.png")

# =============================================================================
# SECTION 5 — FREQUENCY OF PURCHASES
# =============================================================================

print("\n" + "=" * 60)
print("  FREQUENCY OF PURCHASES")
print("=" * 60)

freq_order = ['Weekly', 'Fortnightly', 'Bi-Weekly', 'Monthly',
              'Quarterly', 'Every 3 Months', 'Annually']
freq_counts = df['Frequency of Purchases'].value_counts().reindex(freq_order)
print(freq_counts.to_string())

print(f"\n  Unique categories: {df['Frequency of Purchases'].nunique()}")
print("  → Cannot do math on text. Phase 2 will convert to a numeric scale.")
print("  → Weekly=7, Fortnightly=6, Bi-Weekly=5, Monthly=4,")
print("    Quarterly=3, Every 3 Months=2, Annually=1")

# ── Business interpretation ───────────────────────────────────────────────
# All 7 categories are roughly equally distributed (~550–560 each).
# This is actually unusual — real brands see a heavy skew toward
# monthly or quarterly buyers. The even spread here may be synthetic
# data, but it means no single frequency group dominates.
# Important for the project: frequency is the MOST important signal
# for predicting lifetime value. A weekly buyer is 52x more valuable
# per year than an annual buyer at the same spend level.
# ─────────────────────────────────────────────────────────────────────────

# ── PLOT 5: Frequency bar chart ───────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(freq_counts.index, freq_counts.values,
              color=BRAND_COLORS[:7], edgecolor='white')
ax.set_xlabel('Purchase Frequency Category')
ax.set_ylabel('Number of Customers')
ax.set_title('Purchase Frequency Distribution\n(Ordered from Highest to Lowest Frequency)',
             fontweight='bold')
for bar in bars:
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
            str(int(bar.get_height())), ha='center', fontsize=9)
plt.tight_layout()
plt.savefig('plot_05_frequency.png')
# plt.show()
print("  [Saved] plot_05_frequency.png")

# =============================================================================
# SECTION 6 — REVIEW RATING DISTRIBUTION
# =============================================================================

print("\n" + "=" * 60)
print("  REVIEW RATING ANALYSIS")
print("=" * 60)
print(df['Review Rating'].describe().round(3).to_string())
print(f"\n  Missing ratings: {df['Review Rating'].isnull().sum()} rows")

# ── Business interpretation ───────────────────────────────────────────────
# Mean: 3.75 / 5.0. Ratings range from 2.5 to 5.0.
# There are NO ratings below 2.5 — either the brand filters these
# (suspicious for real data) or it's a synthetic floor.
# Key insight: Rating >= 4.0 will be our "High Satisfaction" flag.
#
# The 37 nulls (~1%) represent customers who never rated.
# These "silent" customers are worth tracking — research shows
# dissatisfied customers are more likely NOT to rate than to leave
# a negative review. They just churn silently.
# ─────────────────────────────────────────────────────────────────────────

# ── PLOT 6: Review Rating histogram ──────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Overall distribution
axes[0].hist(df['Review Rating'].dropna(), bins=26,
             color='#9B59B6', edgecolor='white', alpha=0.85)
axes[0].axvline(4.0, color='#E74C3C', linestyle='--', linewidth=1.5,
                label='High Satisfaction Threshold (4.0)')
axes[0].axvline(df['Review Rating'].mean(), color='#F39C12',
                linestyle=':', linewidth=1.5,
                label=f"Mean: {df['Review Rating'].mean():.2f}")
axes[0].set_xlabel('Review Rating')
axes[0].set_ylabel('Count')
axes[0].set_title('Review Rating Distribution', fontweight='bold')
axes[0].legend(fontsize=8)

# Satisfied vs not
sat_pct = (df['Review Rating'] >= 4.0).sum() / \
    df['Review Rating'].notna().sum() * 100
axes[1].barh(['Rating ≥ 4.0\n(High Satisfaction)', 'Rating < 4.0\n(Low Satisfaction)'],
             [sat_pct, 100 - sat_pct],
             color=['#2ECC71', '#E74C3C'], edgecolor='white')
axes[1].set_xlabel('% of Customers with Ratings')
axes[1].set_title('Satisfaction Split', fontweight='bold')
for i, v in enumerate([sat_pct, 100 - sat_pct]):
    axes[1].text(v + 0.5, i, f'{v:.1f}%', va='center', fontweight='bold')

plt.tight_layout()
plt.savefig('plot_06_review_rating.png')
# plt.show()
print("  [Saved] plot_06_review_rating.png")

# =============================================================================
# SECTION 7 — CUSTOMER DEMOGRAPHICS
# =============================================================================

print("\n" + "=" * 60)
print("  CUSTOMER DEMOGRAPHICS")
print("=" * 60)

print("\nGender:")
print(df['Gender'].value_counts())
print(
    f"  → {df['Gender'].value_counts(normalize=True).mul(100).round(1)['Male']}% Male")

print("\nAge:")
print(df['Age'].describe().round(1).to_string())

# ── PLOT 7: Age distribution by gender ───────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Age histogram
axes[0].hist(df[df['Gender'] == 'Male']['Age'], bins=20,
             alpha=0.7, color='#3498DB', label='Male', edgecolor='white')
axes[0].hist(df[df['Gender'] == 'Female']['Age'], bins=20,
             alpha=0.7, color='#E74C3C', label='Female', edgecolor='white')
axes[0].set_xlabel('Age')
axes[0].set_ylabel('Count')
axes[0].set_title('Age Distribution by Gender', fontweight='bold')
axes[0].legend()

# Gender + Subscription
sub_gender = df.groupby(['Gender', 'Subscription Status']).size().unstack()
sub_gender.plot(kind='bar', ax=axes[1], color=['#2C3E50', '#2ECC71'],
                edgecolor='white', rot=0)
axes[1].set_title('Subscription Status by Gender', fontweight='bold')
axes[1].set_xlabel('Gender')
axes[1].set_ylabel('Count')
axes[1].legend(title='Subscribed')

plt.tight_layout()
plt.savefig('plot_07_demographics.png')
# plt.show()
print("  [Saved] plot_07_demographics.png")

# ── Business interpretation ───────────────────────────────────────────────
# 68% Male, 32% Female. The brand's audience skews strongly male.
# Age: 18–70, mean ~44. This is broad — the brand is not age-targeted.
# Subscription rate: ~27% overall. Subscribers are the most valuable
# segment — they've opted in for a long-term relationship.
# ─────────────────────────────────────────────────────────────────────────

# =============================================================================
# SECTION 8 — CATEGORY & ITEM ANALYSIS
# =============================================================================

print("\n" + "=" * 60)
print("  CATEGORY & PRODUCT ANALYSIS")
print("=" * 60)
print(df['Category'].value_counts())

# ── PLOT 8: Category revenue breakdown ────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Category count
cat_counts = df['Category'].value_counts()
axes[0].bar(cat_counts.index, cat_counts.values,
            color=BRAND_COLORS[:4], edgecolor='white')
axes[0].set_title('Transactions by Category', fontweight='bold')
axes[0].set_ylabel('Count')

# Category average spend
cat_avg = df.groupby('Category')[
    'Purchase Amount (USD)'].mean().sort_values(ascending=False)
axes[1].bar(cat_avg.index, cat_avg.values,
            color=BRAND_COLORS[:4], edgecolor='white')
axes[1].set_title('Average Purchase Amount by Category', fontweight='bold')
axes[1].set_ylabel('Avg Purchase (USD)')
for i, (v, c) in enumerate(zip(cat_avg.values, cat_avg.index)):
    axes[1].text(i, v + 0.5, f'${v:.1f}', ha='center', fontsize=9)

plt.tight_layout()
plt.savefig('plot_08_category_analysis.png')
# plt.show()
print("  [Saved] plot_08_category_analysis.png")

# =============================================================================
# SECTION 9 — SEASONALITY ANALYSIS
# =============================================================================

print("\n" + "=" * 60)
print("  SEASONALITY ANALYSIS")
print("=" * 60)

season_stats = df.groupby('Season').agg(
    Transactions=('Customer ID', 'count'),
    Avg_Spend=('Purchase Amount (USD)', 'mean'),
    Promo_Rate=('Discount Applied', lambda x: (x == 'Yes').mean() * 100)
).round(2)
print(season_stats.to_string())

# ── Business interpretation ───────────────────────────────────────────────
# All seasons are roughly equally distributed (~950 each) — another
# indicator of synthetic data. In real D2C fashion, Fall/Winter would
# have higher transaction counts. However, the promo rate per season
# is an interesting signal — if one season has higher promo dependency,
# that informs the brand's promotional calendar strategy.
# ─────────────────────────────────────────────────────────────────────────

# ── PLOT 9: Season breakdown ──────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
season_order = ['Spring', 'Summer', 'Fall', 'Winter']

bars1 = axes[0].bar(season_order,
                    [season_stats.loc[s, 'Transactions']
                        for s in season_order],
                    color=BRAND_COLORS[:4], edgecolor='white')
axes[0].set_title('Transactions by Season', fontweight='bold')
axes[0].set_ylabel('Number of Transactions')

bars2 = axes[1].bar(season_order,
                    [season_stats.loc[s, 'Promo_Rate'] for s in season_order],
                    color=BRAND_COLORS[:4], edgecolor='white')
axes[1].set_title('Promo Usage Rate by Season (%)', fontweight='bold')
axes[1].set_ylabel('Promo Usage (%)')
axes[1].set_ylim(0, 60)
for bar in bars2:
    axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                 f'{bar.get_height():.1f}%', ha='center', fontsize=9)

plt.tight_layout()
plt.savefig('plot_09_seasonality.png')
# plt.show()
print("  [Saved] plot_09_seasonality.png")

# =============================================================================
# SECTION 10 — CORRELATION HEATMAP (NUMERICAL COLUMNS)
# =============================================================================

print("\n" + "=" * 60)
print("  CORRELATION MATRIX (NUMERICAL COLUMNS)")
print("=" * 60)

num_cols = df.select_dtypes(include='number').drop(columns='Customer ID')
corr = num_cols.corr().round(3)
print(corr.to_string())

# ── PLOT 10: Heatmap ──────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 5))
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm',
            linewidths=0.5, ax=ax, cbar_kws={'shrink': 0.8})
ax.set_title('Correlation Heatmap — Numerical Features', fontweight='bold')
plt.tight_layout()
plt.savefig('plot_10_correlation_heatmap.png')
# plt.show()
print("  [Saved] plot_10_correlation_heatmap.png")

# ── Business interpretation ───────────────────────────────────────────────
# Most numerical columns show weak correlation — confirming that no
# single number tells the full story. This is WHY feature engineering
# matters: we need to CREATE the metrics that capture customer value.
# ─────────────────────────────────────────────────────────────────────────

# =============================================================================
# SECTION 11 — SUBSCRIPTION VS NON-SUBSCRIPTION COMPARISON
# =============================================================================

print("\n" + "=" * 60)
print("  SUBSCRIBER vs NON-SUBSCRIBER ANALYSIS")
print("=" * 60)

sub_comparison = df.groupby('Subscription Status').agg(
    Count=('Customer ID', 'count'),
    Avg_Spend=('Purchase Amount (USD)', 'mean'),
    Avg_Previous_Purchases=('Previous Purchases', 'mean'),
    Avg_Rating=('Review Rating', 'mean'),
    Promo_Rate=('Discount Applied', lambda x: (x == 'Yes').mean() * 100)
).round(2)
print(sub_comparison.to_string())

# ── Business interpretation ───────────────────────────────────────────────
# This comparison is gold for the executive dashboard.
# If subscribers have higher tenure and lower promo dependency,
# that tells the brand: "Your subscription program IS working."
# If subscribers have similar promo rates as non-subscribers,
# that means subscriptions aren't reducing discount dependency —
# a problem worth flagging in your consulting recommendations.
# ─────────────────────────────────────────────────────────────────────────

# ── PLOT 11: Subscriber comparison ────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 5))
metrics = ['Avg_Spend', 'Avg_Previous_Purchases', 'Promo_Rate']
labels = ['Avg Spend (USD)', 'Avg Previous Purchases', 'Promo Usage Rate (%)']
colors = [['#2C3E50', '#3498DB'], [
    '#2ECC71', '#1ABC9C'], ['#E74C3C', '#F39C12']]

for ax, metric, label, color in zip(axes, metrics, labels, colors):
    ax.bar(sub_comparison.index, sub_comparison[metric],
           color=color, edgecolor='white', width=0.5)
    ax.set_title(label, fontweight='bold')
    ax.set_xlabel('Subscription Status')
    for i, v in enumerate(sub_comparison[metric]):
        ax.text(i, v + 0.3, f'{v:.1f}', ha='center', fontsize=9)

plt.suptitle('Subscriber vs Non-Subscriber Comparison', fontsize=13,
             fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('plot_11_subscriber_comparison.png')
# plt.show()
print("  [Saved] plot_11_subscriber_comparison.png")

# =============================================================================
# SECTION 12 — PAYMENT METHOD & SHIPPING PREFERENCES
# =============================================================================

# ── PLOT 12: Payment + Shipping ───────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

pay_counts = df['Payment Method'].value_counts()
axes[0].barh(pay_counts.index, pay_counts.values,
             color=BRAND_COLORS[:6], edgecolor='white')
axes[0].set_title('Payment Method Distribution', fontweight='bold')
axes[0].set_xlabel('Count')

ship_counts = df['Shipping Type'].value_counts()
axes[1].barh(ship_counts.index, ship_counts.values,
             color=BRAND_COLORS[:6], edgecolor='white')
axes[1].set_title('Shipping Type Distribution', fontweight='bold')
axes[1].set_xlabel('Count')

plt.tight_layout()
plt.savefig('plot_12_payment_shipping.png')
# plt.show()
print("  [Saved] plot_12_payment_shipping.png")

# =============================================================================
# SECTION 13 — CLEAN DATA EXPORT FOR PHASE 2
# =============================================================================

print("\n" + "=" * 60)
print("  DATA CLEANING FOR PHASE 2")
print("=" * 60)

df_clean = df.copy()

# Step 1: Strip whitespace from all string columns
str_cols = df_clean.select_dtypes(include='object').columns
for col in str_cols:
    df_clean[col] = df_clean[col].str.strip()

# Step 2: Standardize column names (lowercase, underscores)
df_clean.columns = (df_clean.columns
                    .str.lower()
                    .str.replace(' ', '_', regex=False)
                    .str.replace('(', '', regex=False)
                    .str.replace(')', '', regex=False))

# Step 3: Add Rating_Missing flag BEFORE imputing
df_clean['rating_missing'] = df_clean['review_rating'].isnull().astype(int)
# Business rationale: silent customers (never rated) may be
# disengaged. Track them separately instead of hiding the null.

# Step 4: Impute Review Rating with median (for rows that had nulls)
median_rating = df_clean['review_rating'].median()
df_clean['review_rating'] = df_clean['review_rating'].fillna(median_rating)
print(f"  Review Rating nulls imputed with median: {median_rating}")

print(f"\n  Cleaned columns: {list(df_clean.columns)}")
print(f"  Shape after cleaning: {df_clean.shape}")
print(f"  Any remaining nulls: {df_clean.isnull().sum().sum()}")

df_clean.to_csv('df_phase1_clean.csv', index=False)
print("\n  [Saved] df_phase1_clean.csv  ← Input for Phase 2")

# =============================================================================
# SECTION 14 — EDA SUMMARY: BUSINESS OBSERVATIONS
# =============================================================================

print("\n" + "=" * 60)
print("  PHASE 1 — EDA BUSINESS OBSERVATIONS SUMMARY")
print("=" * 60)

observations = [
    ("1. Promo Dependency is HIGH",
     f"~{promo_counts.get('Yes', 0) / len(df) * 100:.0f}% of all transactions use a discount/promo. "
     "For a D2C brand, anything above 30% is a margin warning."),
    ("2. Purchase Amount alone is a weak loyalty signal",
     "The $20-$100 range is narrow. High spend in one transaction does NOT "
     "mean the customer is loyal. We need Frequency × Spend (CVI) instead."),
    ("3. No timestamps — Previous Purchases is our tenure proxy",
     "With a 1-50 range and mean ~25, we treat this as a normalized "
     "tenure signal. Customers near 50 are veterans."),
    ("4. Review Rating skewed positive with 37 silent reviewers",
     "Mean 3.75/5.0. 37 customers never rated — these 'silent' customers "
     "will be flagged separately as a potential disengagement signal."),
    ("5. Frequency categories need numerical conversion",
     "7 categories from Weekly to Annually. Math cannot operate on text. "
     "Phase 2 encodes these: Weekly=7 down to Annually=1."),
    ("6. Subscriber base is small (~27%)",
     "Only 1,053 of 3,900 customers subscribe. The brand should study what "
     "drives subscription upgrades — that's a retention lever."),
    ("7. Discount and Promo Code are perfectly correlated",
     "100% match. One column is redundant. Combined into Promo_Dependency_Score in Phase 2."),
]

for title, insight in observations:
    print(f"\n  ► {title}")
    print(f"    {insight}")

print("\n" + "=" * 60)
print("  ALL PHASE 1 OUTPUTS SAVED. READY FOR PHASE 2.")
print("=" * 60)
