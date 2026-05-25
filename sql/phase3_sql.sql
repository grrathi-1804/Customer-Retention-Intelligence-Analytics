-- =============================================================================
-- PHASE 3 — SQL SEGMENTATION & CUSTOMER INTELLIGENCE
-- Project  : D2C Fashion Brand — Customer Retention Analytics
-- Tool     : SQL Server Management Studio 22
-- Input    : df_phase2_for_sql.csv  (31 columns, 3900 rows)
-- Author   : NIT Trichy — Production Engineering
-- =============================================================================


-- =============================================================================
-- STAGE A — DATABASE & TABLE SETUP
-- =============================================================================

-- STEP 1: Create a dedicated database for this project
-- Run this first, then refresh Object Explorer on the left panel.
-- You should see "fashion_analytics" appear under Databases.

CREATE DATABASE fashion_analytics;
GO

-- STEP 2: Tell SQL Server to work inside this database
-- Every table you create after this line goes into fashion_analytics.

USE fashion_analytics;
GO

-- =============================================================================
-- STEP 3: Create the table — every column mapped from your Phase 2 CSV
-- =============================================================================
-- NOTE: SQL Server uses NVARCHAR instead of VARCHAR for Unicode support.
--       This handles any special characters in location names, etc.
--       DECIMAL(p, s) → p = total digits, s = digits after decimal point.
-- =============================================================================

CREATE TABLE fashion_customers (

    -- ── Original raw columns ──────────────────────────────────────────────
    customer_id                 INT             PRIMARY KEY,
    age                         INT             NOT NULL,
    gender                      NVARCHAR(10)    NOT NULL,
    item_purchased              NVARCHAR(50)    NOT NULL,
    category                    NVARCHAR(30)    NOT NULL,
    purchase_amount_usd         INT             NOT NULL,
    location                    NVARCHAR(50)    NOT NULL,
    size                        NVARCHAR(5)     NOT NULL,
    color                       NVARCHAR(20)    NOT NULL,
    season                      NVARCHAR(10)    NOT NULL,
    review_rating               DECIMAL(3, 1)   NOT NULL,   -- e.g. 3.8, 4.5
    subscription_status         NVARCHAR(5)     NOT NULL,   -- 'Yes' / 'No'
    shipping_type               NVARCHAR(30)    NOT NULL,
    discount_applied            NVARCHAR(5)     NOT NULL,   -- 'Yes' / 'No'
    promo_code_used             NVARCHAR(5)     NOT NULL,   -- 'Yes' / 'No'
    previous_purchases          INT             NOT NULL,
    payment_method              NVARCHAR(20)    NOT NULL,
    frequency_of_purchases      NVARCHAR(20)    NOT NULL,

    -- ── Phase 1 cleaning column ───────────────────────────────────────────
    rating_missing              TINYINT         NOT NULL,   -- 1 = was null, 0 = had value

    -- ── Phase 2 engineered features ───────────────────────────────────────
    promo_dependency_score      TINYINT         NOT NULL,   -- 0, 1, or 2
    purchase_frequency_score    TINYINT         NOT NULL,   -- 1 to 7
    customer_value_index        INT             NOT NULL,   -- 20 to 700
    loyalty_score_v1            DECIMAL(6, 4)   NOT NULL,   -- 0.02 to 7.0
    loyalty_score_v1_normalized DECIMAL(6, 4)   NOT NULL,   -- 0.0 to 1.0
    loyalty_score_v2            DECIMAL(6, 4)   NOT NULL,   -- 0.408 to 3.4
    loyalty_score_v2_normalized DECIMAL(6, 4)   NOT NULL,   -- 0.12 to 1.0
    loyalty_tier                NVARCHAR(2)     NOT NULL,   -- 'A', 'B', 'C', 'D'
    high_satisfaction           TINYINT         NOT NULL,   -- 0 or 1
    at_risk_promo               TINYINT         NOT NULL,   -- 0 or 1
    tenure_band                 NVARCHAR(25)    NOT NULL,   -- e.g. 'Growing (11-25)'
    age_segment                 NVARCHAR(25)    NOT NULL,   -- e.g. 'Millennial (28-42)'

    -- ── Additional normalized score from Phase 2 ──────────────────────────
    loyalty_score_v1_normalized2 DECIMAL(6, 4)  NOT NULL    -- second normalized v1 col
    -- NOTE: Your CSV has loyalty_score_v1_normalized at position 30.
    --       We name it loyalty_score_v1_normalized2 to avoid duplicate names.
    --       When importing, map CSV column 30 → this column.
);
GO

-- STEP 4: Verify the table was created correctly
-- This shows every column, its data type, and whether nulls are allowed.
-- Compare it against your CSV headers before importing.

DESCRIBE fashion_customers;
-- NOTE: DESCRIBE does not work in SQL Server. Use this instead:

EXEC sp_help 'fashion_customers';
GO


-- =============================================================================
-- STEP 5: IMPORT YOUR CSV
-- =============================================================================
-- SQL Server Management Studio — Table Data Import:
--
--   Method 1 (Recommended — Import Flat File Wizard):
--   Right-click "fashion_analytics" database in Object Explorer
--   → Tasks → Import Flat File
--   → Browse to df_phase2_for_sql.csv
--   → Preview data → set column types to match the table above
--   → Click Finish
--
--   Method 2 (BULK INSERT — run after placing CSV on your machine):
--   Update the file path below to wherever your CSV is saved.
-- =============================================================================

--BULK INSERT fashion_customers
--FROM 'C:\Users\YourName\Downloads\df_phase2_for_sql.csv'
--    -- ↑ CHANGE THIS PATH to where your CSV actually is on your computer
--WITH (
--    FIRSTROW       = 2,          -- Skip the header row
--    FIELDTERMINATOR = ',',       -- Columns separated by comma
--    ROWTERMINATOR  = '\n',       -- Rows separated by newline
--    TABLOCK                      -- Locks table during import (faster)
--);
--GO

-- =============================================================================
-- STAGE B — DATA VALIDATION
-- Run these BEFORE writing any segmentation queries.
-- A wrong row count or null in a key column will break everything downstream.
-- =============================================================================

-- STEP 6: Row count check — must return exactly 3900
SELECT COUNT(*) AS total_rows FROM fashion_customers;
GO

-- STEP 7: Preview first 5 rows — visually compare against your CSV
SELECT TOP 5 * FROM fashion_customers;
GO
USE fashion_analytics;

SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE';
SELECT COUNT(*) FROM df_phase2_for_sql;
-- Copy all data from the wizard-created table into our proper table
INSERT INTO fashion_customers
SELECT * FROM df_phase2_for_sql;

-- Verify
SELECT COUNT(*) FROM fashion_customers;  -- Must return 3900

DROP TABLE fashion_customers;

EXEC sp_rename 'df_phase2_for_sql', 'fashion_customers';


SELECT COUNT(*) FROM fashion_customers;
-- Must return 3900

SELECT TOP 5 * FROM fashion_customers;





-- STEP 8: Check nulls in all critical engineered columns
-- Expected result: every column shows 0 nulls.
-- If any column shows nulls, go back to Python and fix Phase 2.
SELECT
    SUM(CASE WHEN loyalty_score_v2            IS NULL THEN 1 ELSE 0 END) AS nulls_loyalty_v2,
    SUM(CASE WHEN loyalty_score_v2_normalized IS NULL THEN 1 ELSE 0 END) AS nulls_loyalty_v2_norm,
    SUM(CASE WHEN loyalty_tier                IS NULL THEN 1 ELSE 0 END) AS nulls_loyalty_tier,
    SUM(CASE WHEN promo_dependency_score      IS NULL THEN 1 ELSE 0 END) AS nulls_promo_dep,
    SUM(CASE WHEN customer_value_index        IS NULL THEN 1 ELSE 0 END) AS nulls_cvi,
    SUM(CASE WHEN at_risk_promo               IS NULL THEN 1 ELSE 0 END) AS nulls_at_risk,
    SUM(CASE WHEN high_satisfaction           IS NULL THEN 1 ELSE 0 END) AS nulls_high_sat,
    SUM(CASE WHEN purchase_frequency_score    IS NULL THEN 1 ELSE 0 END) AS nulls_freq_score
FROM fashion_customers;
GO

-- STEP 9: Check value ranges make business sense
-- Expected:
--   promo_dependency_score → only 0 or 2 (never 1, due to 100% correlation)
--   loyalty_tier           → only A, B, C, D
--   purchase_frequency_score → 1, 3, 4, 5, 6, 7
--   review_rating          → between 2.5 and 5.0

SELECT 'promo_dependency_score' AS column_name,
       MIN(promo_dependency_score) AS min_val,
       MAX(promo_dependency_score) AS max_val
FROM fashion_customers
UNION ALL
SELECT 'purchase_frequency_score',
       MIN(purchase_frequency_score),
       MAX(purchase_frequency_score)
FROM fashion_customers
UNION ALL
SELECT 'review_rating',
       MIN(review_rating),
       MAX(review_rating)
FROM fashion_customers
UNION ALL
SELECT 'loyalty_score_v2_normalized',
       MIN(loyalty_score_v2_normalized),
       MAX(loyalty_score_v2_normalized)
FROM fashion_customers
UNION ALL
SELECT 'customer_value_index',
       MIN(customer_value_index),
       MAX(customer_value_index)
FROM fashion_customers;
GO

-- STEP 10: Confirm loyalty_tier only has A, B, C, D
SELECT DISTINCT loyalty_tier FROM fashion_customers ORDER BY loyalty_tier;
GO

-- STEP 11: Confirm binary columns only have 'Yes' / 'No'
SELECT DISTINCT discount_applied  FROM fashion_customers;
SELECT DISTINCT promo_code_used   FROM fashion_customers;
SELECT DISTINCT subscription_status FROM fashion_customers;
GO


-- =============================================================================
-- STAGE C — THE 5 CORE SEGMENTATION QUERIES
-- =============================================================================
-- Each query answers one business question.
-- Read the comment above each query before running it.
-- After running, write your observation as a comment below the query.
-- =============================================================================


-- ─────────────────────────────────────────────────────────────────────────────
-- QUERY 1: Loyal vs Discount-Driven Customers
-- ─────────────────────────────────────────────────────────────────────────────
-- Business question:
--   Do our most loyal customers also depend on promotions —
--   or are they loyal WITHOUT needing incentives?
--
-- What to look for:
--   → Tier A should have the LOWEST avg_promo_dependency
--   → Tier D should have the HIGHEST avg_promo_dependency
--   → If Tier A still shows high promo dependency, that's alarming —
--     even your best customers only show up for deals
--
-- Business impact:
--   This is the foundational answer to the central business problem.
--   Tells the founder whether loyalty and discount-dependency are
--   inversely related (healthy) or not (problem).
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    loyalty_tier,
    COUNT(*)                                        AS total_customers,
    ROUND(AVG(CAST(promo_dependency_score AS FLOAT)), 2)
                                                    AS avg_promo_dependency,
    ROUND(AVG(CAST(purchase_amount_usd AS FLOAT)), 2)
                                                    AS avg_spend_usd,
    ROUND(AVG(CAST(previous_purchases AS FLOAT)), 1)
                                                    AS avg_tenure,
    ROUND(AVG(CAST(customer_value_index AS FLOAT)), 1)
                                                    AS avg_cvi,
    SUM(CASE WHEN subscription_status = 'Yes' THEN 1 ELSE 0 END)
                                                    AS subscribed_count,
    ROUND(
        100.0 * SUM(CASE WHEN subscription_status = 'Yes' THEN 1 ELSE 0 END)
        / COUNT(*), 1
    )                                               AS subscription_rate_pct
FROM fashion_customers
GROUP BY loyalty_tier
ORDER BY loyalty_tier ASC;   -- A → D order
GO

-- ─────────────────────────────────────────────────────────────────────────────
-- QUERY 2: High-Value vs Low-Value Customer Profiles
-- ─────────────────────────────────────────────────────────────────────────────
-- Business question:
--   What does a high-value customer look like versus a low-value one?
--   Demographically and behaviorally.
--
-- What to look for:
--   → Tier A likely has higher CVI, more previous purchases,
--     higher subscription rate
--   → Age may or may not vary — interesting either way
--   → Gender split per tier tells you which demographic is most loyal
--
-- Business impact:
--   Gives the marketing team a concrete description of who to target
--   with premium campaigns vs. who to try and upsell.
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    loyalty_tier,
    gender,
    COUNT(*)                                            AS customer_count,
    ROUND(AVG(CAST(age AS FLOAT)), 1)                  AS avg_age,
    ROUND(AVG(CAST(customer_value_index AS FLOAT)), 1) AS avg_cvi,
    ROUND(AVG(CAST(purchase_amount_usd AS FLOAT)), 2)  AS avg_spend,
    ROUND(AVG(CAST(purchase_frequency_score AS FLOAT)), 2)
                                                        AS avg_freq_score,
    ROUND(AVG(CAST(previous_purchases AS FLOAT)), 1)   AS avg_tenure,
    ROUND(
        100.0 * SUM(CASE WHEN subscription_status = 'Yes' THEN 1 ELSE 0 END)
        / COUNT(*), 1
    )                                                   AS subscription_rate_pct,
    ROUND(AVG(CAST(loyalty_score_v2_normalized AS FLOAT)), 4)
                                                        AS avg_loyalty_v2
FROM fashion_customers
GROUP BY loyalty_tier, gender
ORDER BY loyalty_tier ASC, avg_cvi DESC;
GO
SELECT DISTINCT subscription_status, gender, COUNT(*) as cnt
FROM fashion_customers
GROUP BY subscription_status, gender
ORDER BY gender, subscription_status;
-- ─────────────────────────────────────────────────────────────────────────────
-- QUERY 3: Geographic Opportunity Analysis
-- ─────────────────────────────────────────────────────────────────────────────
-- Business question:
--   Which states buy from us organically (without discounts),
--   and which ones ONLY engage when we offer promotions?
--
-- What to look for:
--   → Low avg_promo_dependency + decent avg_spend = priority expansion market
--   → High avg_promo_dependency = brand is weak there, stop wasting promo $
--   → HAVING COUNT(*) >= 50 removes small states with unreliable averages
--
-- Business impact:
--   Tells the founder exactly where to invest marketing budget for
--   organic growth vs. where to pull back.
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    location                                            AS state,
    COUNT(*)                                            AS total_customers,
    ROUND(AVG(CAST(promo_dependency_score AS FLOAT)), 2)
                                                        AS avg_promo_dependency,
    ROUND(AVG(CAST(purchase_amount_usd AS FLOAT)), 2)  AS avg_spend_usd,
    ROUND(AVG(CAST(customer_value_index AS FLOAT)), 1) AS avg_cvi,
    ROUND(
        100.0 * SUM(CASE WHEN loyalty_tier = 'A' THEN 1 ELSE 0 END)
        / COUNT(*), 1
    )                                                   AS tier_a_pct,
    ROUND(
        100.0 * SUM(CASE WHEN at_risk_promo = 1 THEN 1 ELSE 0 END)
        / COUNT(*), 1
    )                                                   AS at_risk_promo_pct
FROM fashion_customers
GROUP BY location
HAVING COUNT(*) >= 50           -- Only states with enough data to be reliable
ORDER BY avg_promo_dependency ASC;  -- Most organic markets at the top
GO

-- ─────────────────────────────────────────────────────────────────────────────
-- QUERY 4: Ideal Customer Profile (ICP)
-- ─────────────────────────────────────────────────────────────────────────────
-- Business question:
--   If we could clone our best customer, who exactly would that be?
--
-- What to look for:
--   → The top row by avg_cvi is your Ideal Customer Archetype
--   → Example output might be: Female | Millennial | Clothing | Credit Card
--   → This exact combination is what the marketing team targets in ads
--
-- Business impact:
--   This single query output becomes the ICP document for the
--   marketing team. It replaces guesswork with data.
-- ─────────────────────────────────────────────────────────────────────────────

SELECT TOP 15
    age_segment,
    gender,
    category,
    payment_method,
    subscription_status,
    COUNT(*)                                                    AS customer_count,
    ROUND(AVG(CAST(customer_value_index AS FLOAT)), 1)         AS avg_cvi,
    ROUND(AVG(CAST(previous_purchases AS FLOAT)), 1)           AS avg_tenure,
    ROUND(AVG(CAST(review_rating AS FLOAT)), 2)                AS avg_rating,
    ROUND(AVG(CAST(loyalty_score_v2_normalized AS FLOAT)), 4)  AS avg_loyalty_v2,
    ROUND(AVG(CAST(promo_dependency_score AS FLOAT)), 2)       AS avg_promo_dep
FROM fashion_customers
WHERE loyalty_tier = 'A'       -- Only look at the most loyal customers
GROUP BY age_segment, gender, category, payment_method, subscription_status
HAVING COUNT(*) >= 5           -- Ignore combinations with too few customers
ORDER BY avg_cvi DESC;         -- Highest-value profile at the top
GO

-- ─────────────────────────────────────────────────────────────────────────────
-- QUERY 5: Category & Season Retention Analysis
-- ─────────────────────────────────────────────────────────────────────────────
-- Business question:
--   Which product categories attract loyal, long-tenure customers
--   vs new or one-time buyers? Which seasons?
--
-- What to look for:
--   → High avg_tenure + low promo dependency = loyalty anchor category
--   → Low avg_tenure + high promo dependency = acquisition/deal category
--
-- Business impact:
--   Tells the product team which categories to anchor loyalty programs
--   to, and which seasons to run new-customer onboarding campaigns.
-- ─────────────────────────────────────────────────────────────────────────────

-- Part A: By Category
SELECT
    category,
    COUNT(*)                                                    AS total_customers,
    ROUND(AVG(CAST(previous_purchases AS FLOAT)), 1)           AS avg_tenure,
    ROUND(AVG(CAST(promo_dependency_score AS FLOAT)), 2)       AS avg_promo_dependency,
    ROUND(AVG(CAST(customer_value_index AS FLOAT)), 1)         AS avg_cvi,
    ROUND(
        100.0 * SUM(CASE WHEN loyalty_tier = 'A' THEN 1 ELSE 0 END)
        / COUNT(*), 1
    )                                                           AS tier_a_pct,
    ROUND(
        100.0 * SUM(CASE WHEN high_satisfaction = 1 THEN 1 ELSE 0 END)
        / COUNT(*), 1
    )                                                           AS high_sat_pct
FROM fashion_customers
GROUP BY category
ORDER BY avg_tenure DESC;
GO

-- Part B: By Season
SELECT
    season,
    COUNT(*)                                                    AS total_customers,
    ROUND(AVG(CAST(previous_purchases AS FLOAT)), 1)           AS avg_tenure,
    ROUND(AVG(CAST(promo_dependency_score AS FLOAT)), 2)       AS avg_promo_dependency,
    ROUND(AVG(CAST(customer_value_index AS FLOAT)), 1)         AS avg_cvi,
    ROUND(
        100.0 * SUM(CASE WHEN loyalty_tier = 'A' THEN 1 ELSE 0 END)
        / COUNT(*), 1
    )                                                           AS tier_a_pct
FROM fashion_customers
GROUP BY season
ORDER BY avg_tenure DESC;
GO

-- Part C: Category × Season Combined (cross-cut analysis)
SELECT
    category,
    season,
    COUNT(*)                                                    AS total_customers,
    ROUND(AVG(CAST(customer_value_index AS FLOAT)), 1)         AS avg_cvi,
    ROUND(AVG(CAST(previous_purchases AS FLOAT)), 1)           AS avg_tenure,
    ROUND(AVG(CAST(promo_dependency_score AS FLOAT)), 2)       AS avg_promo_dependency
FROM fashion_customers
GROUP BY category, season
ORDER BY category, avg_cvi DESC;
GO


-- =============================================================================
-- STAGE D — ADVANCED / BONUS QUERIES (Portfolio Differentiators)
-- =============================================================================


-- ─────────────────────────────────────────────────────────────────────────────
-- BONUS QUERY 1: Subscription × Promo Dependency
-- ─────────────────────────────────────────────────────────────────────────────
-- Business question:
--   Is the subscription program building genuine loyalty,
--   or is it just another incentive mechanism?
--
-- What to look for:
--   → If subscribers show LOWER promo dependency → subscription works
--   → If subscribers show EQUAL or HIGHER promo dependency → redesign needed
--   → We already know from EDA that 100% of subscribers used promos —
--     confirm this here and quantify the CVI difference
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    subscription_status,
    COUNT(*)                                                    AS total_customers,
    ROUND(AVG(CAST(promo_dependency_score AS FLOAT)), 2)       AS avg_promo_dependency,
    ROUND(AVG(CAST(customer_value_index AS FLOAT)), 1)         AS avg_cvi,
    ROUND(AVG(CAST(previous_purchases AS FLOAT)), 1)           AS avg_tenure,
    ROUND(AVG(CAST(loyalty_score_v2_normalized AS FLOAT)), 4)  AS avg_loyalty_v2,
    ROUND(
        100.0 * SUM(CASE WHEN loyalty_tier = 'A' THEN 1 ELSE 0 END)
        / COUNT(*), 1
    )                                                           AS tier_a_pct,
    ROUND(
        100.0 * SUM(CASE WHEN at_risk_promo = 1 THEN 1 ELSE 0 END)
        / COUNT(*), 1
    )                                                           AS at_risk_pct
FROM fashion_customers
GROUP BY subscription_status
ORDER BY subscription_status;
GO

-- ─────────────────────────────────────────────────────────────────────────────
-- BONUS QUERY 2: The At-Risk Promo Buyer Deep Dive
-- ─────────────────────────────────────────────────────────────────────────────
-- Business question:
--   Who exactly are the customers we're giving discounts unnecessarily?
--   Who is most at risk of churning if we stop discounts tomorrow?
--
-- What to look for:
--   → Tier C/D + promo dependent + low tenure = most fragile customers
--   → They came for the deal, haven't developed brand attachment yet
--   → These are the "sunset strategy" targets in Phase 5
-- ─────────────────────────────────────────────────────────────────────────────

-- Part A: At-risk segment summary by loyalty tier
SELECT
    loyalty_tier,
    tenure_band,
    COUNT(*)                                                    AS at_risk_customers,
    ROUND(AVG(CAST(previous_purchases AS FLOAT)), 1)           AS avg_tenure,
    ROUND(AVG(CAST(customer_value_index AS FLOAT)), 1)         AS avg_cvi,
    ROUND(AVG(CAST(review_rating AS FLOAT)), 2)                AS avg_rating,
    ROUND(AVG(CAST(loyalty_score_v2_normalized AS FLOAT)), 4)  AS avg_loyalty_v2
FROM fashion_customers
WHERE at_risk_promo = 1
GROUP BY loyalty_tier, tenure_band
ORDER BY loyalty_tier DESC, avg_tenure ASC;  -- Worst tier + newest customers first
GO

-- Part B: Individual at-risk customer list (for targeted intervention)
-- These are the exact customers a CRM team would contact
SELECT TOP 20
    customer_id,
    age,
    gender,
    location,
    category,
    loyalty_tier,
    tenure_band,
    previous_purchases,
    customer_value_index,
    loyalty_score_v2_normalized,
    review_rating
FROM fashion_customers
WHERE at_risk_promo = 1
  AND loyalty_tier IN ('C', 'D')
ORDER BY previous_purchases ASC,       -- Newest at-risk customers first
         loyalty_score_v2_normalized ASC;  -- Least loyal within those
GO

-- ─────────────────────────────────────────────────────────────────────────────
-- BONUS QUERY 3: Payment Method × Loyalty Analysis
-- ─────────────────────────────────────────────────────────────────────────────
-- Business question:
--   Do customers who use credit cards or bank transfers show higher loyalty
--   than cash or Venmo users? Financial commitment often correlates with
--   purchase intentionality.
--
-- What to look for:
--   → Credit card / bank transfer users → higher avg_loyalty_v2?
--   → Cash users → higher promo dependency? (deal-seekers pay cash)
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    payment_method,
    COUNT(*)                                                    AS total_customers,
    ROUND(AVG(CAST(loyalty_score_v2_normalized AS FLOAT)), 4)  AS avg_loyalty_v2,
    ROUND(AVG(CAST(customer_value_index AS FLOAT)), 1)         AS avg_cvi,
    ROUND(AVG(CAST(previous_purchases AS FLOAT)), 1)           AS avg_tenure,
    ROUND(AVG(CAST(promo_dependency_score AS FLOAT)), 2)       AS avg_promo_dependency,
    ROUND(
        100.0 * SUM(CASE WHEN loyalty_tier = 'A' THEN 1 ELSE 0 END)
        / COUNT(*), 1
    )                                                           AS tier_a_pct
FROM fashion_customers
GROUP BY payment_method
ORDER BY avg_loyalty_v2 DESC;
GO

-- ─────────────────────────────────────────────────────────────────────────────
-- BONUS QUERY 4: Champion Customers — Tier A + High Satisfaction
-- ─────────────────────────────────────────────────────────────────────────────
-- Business question:
--   Who are our absolute best customers — loyal AND satisfied?
--   These are the brand advocates. What do they look like?
--
-- Business impact:
--   These 406 customers are your referral program targets.
--   A happy + loyal customer is far more likely to recommend the brand.
-- ─────────────────────────────────────────────────────────────────────────────

-- ─────────────────────────────────────────────────────────────────────────────
-- BONUS QUERY 5: Loyalty v1 vs v2 Disagreement Analysis
-- ─────────────────────────────────────────────────────────────────────────────
-- Business question:
--   Which customers does v1 OVERRATE that v2 correctly penalizes?
--   These are the customers who look loyal on frequency/tenure alone
--   but are actually discount-dependent — v2 catches them.
--
-- Business impact:
--   Justifies using v2 as your primary metric in the presentation.
--   These are the "false loyals" — the brand's blind spot.
-- ─────────────────────────────────────────────────────────────────────────────

SELECT TOP 20
    customer_id,
    loyalty_tier,
    promo_dependency_score,
    purchase_frequency_score,
    previous_purchases,
    ROUND(loyalty_score_v1_normalized, 4)                       AS v1_score,
    ROUND(loyalty_score_v2_normalized, 4)                       AS v2_score,
    ROUND(loyalty_score_v1_normalized - loyalty_score_v2_normalized, 4)
                                                                AS v1_overrates_by
FROM fashion_customers
WHERE promo_dependency_score = 2     -- Always uses discounts
ORDER BY v1_overrates_by DESC;       -- Biggest gap = most "false loyal"
GO


-- =============================================================================
-- STAGE E — VIEWS (Save queries for Power BI to connect to directly)
-- =============================================================================
-- A VIEW is a saved query. Instead of rerunning SQL in Power BI,
-- you connect Power BI to the view and it fetches fresh data automatically.
-- Create one view per major segment — Power BI will import each as a table.
-- =============================================================================

-- View 1: Loyalty Tier Summary (for KPI cards and bar charts in Power BI)
CREATE VIEW vw_loyalty_tier_summary AS
SELECT
    loyalty_tier,
    COUNT(*)                                                    AS total_customers,
    ROUND(AVG(CAST(promo_dependency_score AS FLOAT)), 2)       AS avg_promo_dependency,
    ROUND(AVG(CAST(customer_value_index AS FLOAT)), 1)         AS avg_cvi,
    ROUND(AVG(CAST(previous_purchases AS FLOAT)), 1)           AS avg_tenure,
    ROUND(AVG(CAST(loyalty_score_v2_normalized AS FLOAT)), 4)  AS avg_loyalty_v2,
    SUM(CASE WHEN at_risk_promo = 1 THEN 1 ELSE 0 END)         AS at_risk_count,
    SUM(CASE WHEN high_satisfaction = 1 THEN 1 ELSE 0 END)     AS satisfied_count,
    SUM(CASE WHEN subscription_status = 'Yes' THEN 1 ELSE 0 END) AS subscriber_count
FROM fashion_customers
GROUP BY loyalty_tier;
GO

-- View 2: Geographic Summary (for map visual in Power BI)
CREATE VIEW vw_geo_summary AS
SELECT
    location                                                    AS state,
    COUNT(*)                                                    AS total_customers,
    ROUND(AVG(CAST(promo_dependency_score AS FLOAT)), 2)       AS avg_promo_dependency,
    ROUND(AVG(CAST(customer_value_index AS FLOAT)), 1)         AS avg_cvi,
    ROUND(
        100.0 * SUM(CASE WHEN loyalty_tier = 'A' THEN 1 ELSE 0 END)
        / COUNT(*), 1
    )                                                           AS tier_a_pct,
    ROUND(
        100.0 * SUM(CASE WHEN at_risk_promo = 1 THEN 1 ELSE 0 END)
        / COUNT(*), 1
    )                                                           AS at_risk_pct
FROM fashion_customers
GROUP BY location;
GO

-- View 3: At-Risk Promo Buyer Segment (for Phase 5 sunset strategy)
CREATE VIEW vw_at_risk_segment AS
SELECT
    customer_id,
    age,
    gender,
    location,
    category,
    loyalty_tier,
    tenure_band,
    age_segment,
    previous_purchases,
    customer_value_index,
    promo_dependency_score,
    loyalty_score_v2_normalized,
    review_rating,
    subscription_status
FROM fashion_customers
WHERE at_risk_promo = 1;
GO

-- View 4: Champion Customers Segment
CREATE VIEW vw_champions AS
SELECT
    customer_id,
    age,
    gender,
    location,
    category,
    payment_method,
    loyalty_tier,
    tenure_band,
    age_segment,
    previous_purchases,
    customer_value_index,
    loyalty_score_v2_normalized,
    review_rating,
    subscription_status
FROM fashion_customers
WHERE loyalty_tier = 'A'
  AND high_satisfaction = 1;
GO

-- View 5: Full enriched table (Power BI's main data source)
CREATE VIEW vw_fashion_full AS
SELECT * FROM fashion_customers;
GO

SELECT TABLE_NAME AS view_name
FROM INFORMATION_SCHEMA.VIEWS
WHERE TABLE_CATALOG = 'fashion_analytics';




-- =============================================================================
-- QUICK REFERENCE: KEY NUMBERS TO VERIFY AFTER IMPORT
-- =============================================================================
-- Run these after importing. Cross-check against your Phase 2 Python output.
-- If any number doesn't match, your import has a problem.

SELECT
    COUNT(*)                                                        AS total_rows,          -- Expected: 3900
    SUM(CASE WHEN loyalty_tier = 'A' THEN 1 ELSE 0 END)            AS tier_a,              -- Expected: ~966
    SUM(CASE WHEN loyalty_tier = 'D' THEN 1 ELSE 0 END)            AS tier_d,              -- Expected: ~982
    SUM(CASE WHEN at_risk_promo = 1 THEN 1 ELSE 0 END)             AS at_risk_buyers,      -- Expected: ~902
    SUM(CASE WHEN loyalty_tier='A' AND high_satisfaction=1 THEN 1 ELSE 0 END)
                                                                    AS champions,           -- Expected: ~406
    SUM(CASE WHEN promo_dependency_score = 2 THEN 1 ELSE 0 END)    AS fully_promo_dep,     -- Expected: ~1677
    SUM(CASE WHEN rating_missing = 1 THEN 1 ELSE 0 END)            AS silent_reviewers     -- Expected: 37
FROM fashion_customers;
GO

-- =============================================================================
-- END OF PHASE 3 SQL
-- Next step: Connect SQL Server to Power BI Desktop using
-- "Get Data → SQL Server" and import the 5 views created above.
-- =============================================================================
