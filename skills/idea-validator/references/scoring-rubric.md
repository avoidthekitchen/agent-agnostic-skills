# Scoring Rubric — Quick Screen

This rubric covers the three scoring dimensions used in **Quick Screen mode**.
For Deep Dive mode, this rubric still applies as the foundation. The additional
Deep Dive analysis is covered in `deep-dive-rubric.md`.

Use this rubric to score each dimension of an idea. The goal is consistency:
two different runs on the same idea should produce similar verdicts. Ground
every score in the data the scripts returned.

---

## Dimension 1: Pain Point Evidence

How much evidence is there that real people actively experience this problem?

| Rating | Criteria |
|--------|----------|
| **Strong** | 10+ Reddit posts in the last 12 months with 20+ upvotes, using frustration language ("wish there was," "looking for a tool," "does anyone know," "is there anything that"). Posts span multiple subreddits and feel specific to the problem, not tangential. |
| **Moderate** | 3-9 qualifying posts, OR the posts that exist are older than 12 months, OR engagement is mixed (some high, some low). The pain is real but the signal is weaker — could be a niche problem or one people discuss less publicly. |
| **Weak** | 0-2 qualifying posts, OR posts found are only tangentially related to the core problem (e.g., they mention the domain but not the specific pain). The problem might exist but there's little public discussion of it. |
| **None** | No qualifying posts found, OR the search failed entirely. |

**What counts as a qualifying post:**
- Posted within the last 24 months
- 20+ upvotes (or equivalent engagement in small subreddits)
- Contains frustration-indicating language — the poster is describing a problem they want solved, not just discussing the topic generally
- Directly relates to the core problem, not just the domain

**Edge cases:**
- If the target audience is non-technical and unlikely to use Reddit, downgrade confidence in this dimension. Note it in the summary.
- If posts exist but are mostly people recommending existing solutions (not complaining about gaps), that's actually a sign of a solved problem — lean toward Weak.
- If posts are concentrated in one subreddit only, that's less robust than spread across multiple communities.

---

## Dimension 2: Trend Direction

Is interest in this problem/solution space growing, stable, or declining?

| Rating | Criteria |
|--------|----------|
| **Accelerating** | 12-month interest slope is clearly positive (visibly upward trend in Google Trends data). Ideally, 5-year trend also supports growth. Seasonal spikes alone do not count — look for sustained direction. |
| **Flat** | 12-month slope is roughly flat (no clear upward or downward movement). Could be a mature, stable market or a niche that has plateaued. 5-year data helps distinguish these cases. |
| **Declining** | 12-month slope is clearly negative. Interest is fading. Even if there's a spike or two, the overall trajectory points down. |

**Interpretation guide:**
- A "Flat" trend isn't necessarily bad — many profitable businesses operate in stable markets. But it means the idea won't ride a wave of growing demand.
- "Accelerating" is exciting but consider why. Is this a genuine shift in behavior, or is it hype that could fade? Cross-reference with the pain-point evidence.
- If Google Trends data is noisy or the keywords are too niche to show meaningful trends, note this and reduce confidence in this dimension.

---

## Dimension 3: Competitor Density

How crowded is the space for a new entrant?

| Rating | Criteria |
|--------|----------|
| **Open** | 0-2 direct competitors found. Adjacent tools exist (which validates demand) but nobody is directly solving this specific problem. White space is clear. |
| **Moderate** | 3-5 direct competitors, but clear gaps remain — missing features, underserved audiences, poor UX, or high pricing. A new entrant could differentiate. |
| **Crowded** | 6+ well-funded direct competitors with full feature coverage. The space is saturated and differentiation would be difficult. |

**Categorization rules:**
- **Direct competitor:** A product that solves the same core problem for the same audience. Even if positioning differs, if a customer would choose between you and them, they're direct.
- **Adjacent tool:** A product in the same domain that partially addresses the problem. Not a direct substitute, but validates that the space has commercial activity.
- **Informational content:** Blog posts, tutorials, or reviews. Not a competitor, but signals that people are searching for information about this space.
- **Dead project:** A product that appears abandoned (no updates in 2+ years, broken website, dead links). Note these separately — they indicate past attempts that may have failed, which is informative.

**What to look for in competitors:**
- Funding and maturity (a few funded competitors is worse than many bootstrapped ones)
- Feature coverage (do they do everything the user's idea does?)
- Pricing (is there room for a different price point?)
- Reviews and sentiment (are users unhappy with existing options?)

---

## Verdict Logic

The verdict is a judgment call, not a formula. Use these as guidelines, not
rules:

**Investigate Further:**
- At least two dimensions show Strong/Open signals
- The idea addresses a real, evidenced pain point
- Competition isn't a showstopper (Open or Moderate)
- Trends support the timing

**Proceed with Caution:**
- Mixed signals — one dimension strong, one weak, one moderate
- The pain point exists but evidence is thin
- Competition is Moderate with no clear differentiation path
- Trend is Flat but the market is stable and underserved

**Kill:**
- Pain point evidence is Weak or None — people don't seem to care
- Trend is Declining — demand is fading
- Competition is Crowded with no obvious gap
- Two or more dimensions show Weak signals
- The idea solves a problem nobody has, in a space where nobody's looking

**Anti-hedging rule:** If two dimensions clearly point one way and the third is ambiguous, go with the weight of evidence. Don't default to "Proceed with Caution" just because you're unsure — that's what the data is supposed to resolve.

---

## Example Scorecards

### Example 1: Strong Signal

```
IDEA: AI-powered invoice reconciliation for freelancers
DATE: 2025-01-15

PAIN POINT EVIDENCE:    Strong
  → Found 23 posts across r/freelance, r/smallbusiness, and r/bookkeeping
    in the last 12 months. Common themes: manually matching payments to
    invoices, lost revenue from missed invoices, frustration with existing
    accounting tools being too complex.

TREND DIRECTION:        Accelerating
  → "freelance invoicing" and "invoice automation" both show sustained
    upward slopes over 12 months. 5-year data supports continued growth.

COMPETITOR DENSITY:     Moderate
  → Found 4 direct competitors (Wave, Invoice Ninja, Zoho Invoice, FreshBooks)
    but all target small businesses broadly. None specifically optimize for
    freelancer workflows like partial payments and client reminders.

QUICK VERDICT:          Investigate Further
  → Strong pain point evidence and growing demand make this worth exploring.
    Competition is moderate but the freelancer-specific angle is underserved.
    Key risk: freelancers may be unwilling to pay for invoicing tools given
    free alternatives.

COMPETITOR PROFILE:
  | Competitor    | Target Audience     | Pricing   | Maturity   | Key Differentiator |
  |---------------|--------------------| --------- | --------- | ------------------- |
  | Wave          | Small businesses   | Free      | Mature     | Full accounting suite, free tier |
  | Invoice Ninja | Freelancers, SMBs  | Freemium  | Established| Open source, self-hostable |
  | Zoho Invoice  | Small businesses   | Freemium  | Mature     | Part of Zoho ecosystem |
  | FreshBooks    | Freelancers, agencies| Paid    | Mature     | Strong brand, time tracking |

PERCEPTUAL MAP:
  Axis X: Broad SMB accounting → Freelancer-specific
  Axis Y: Manual process → Automated reconciliation

                    Automated
                        |
                   Zoho Invoice
                        |
   Broad SMB --------+-------- Freelancer-specific
                        |
            Wave      |     Invoice Ninja
                   FreshBooks
                        |
                    Manual

  The freelancer-specific + automated reconciliation quadrant is empty.
  Invoice Ninja is closest but focuses on invoicing, not reconciliation.
  This is the whitespace.

DATA SOURCES:
  → Reddit: 23 posts across 3 subreddits (strong)
  → Google Trends: 2 keywords, both positive slopes (accelerating)
  → Web results: 4 competitors, 2 informational (brave+tavily+duckduckgo)
```

### Example 2: Kill Signal

```
IDEA: Social network for people who collect vintage thermometers
DATE: 2025-01-15

PAIN POINT EVIDENCE:    Weak
  → Found 2 posts across all searched subreddits in 24 months. Both were
    in r/thermometers (23K members) and were about buying advice, not about
    wanting a community platform.

TREND DIRECTION:        Flat
  → "vintage thermometer" shows negligible search volume with no meaningful
    trend. "thermometer collecting" is similarly flat.

COMPETITOR DENSITY:     Open
  → No direct competitors found. A few Facebook groups exist but no dedicated
    platform.

QUICK VERDICT:          Kill
  → While there's no competition, there's also no evidence of demand. Two
    Reddit posts in two years across all searched communities suggests the
    addressable audience is extremely small. A social network requires critical
    mass to be useful — this idea lacks the demand signal to get there.

COMPETITOR PROFILE:
  No direct competitors found — the competitive whitespace is open.

PERCEPTUAL MAP:
  Insufficient competitors to map. Only informal communities (Facebook groups)
    exist, with no products to position against. The absence of competitors
    here is not an opportunity — it reflects a lack of market.

DATA SOURCES:
  → Reddit: 2 posts in 24 months across 6 subreddits (weak)
  → Google Trends: Negligible volume, flat (flat)
  → Web results: 0 competitors, 3 informational (duckduckgo only)
```

### Example 3: Caution Signal

```
IDEA: Meal planning app that generates grocery lists from recipes
DATE: 2025-01-15

PAIN POINT EVIDENCE:    Moderate
  → Found 7 posts in r/mealprep and r/EatCheapAndHealthy in the last year.
    Users describe manually planning meals as tedious, but many already use
    free tools (Paprika, AnyList) or spreadsheets.

TREND DIRECTION:        Flat
  → "meal planning" interest is stable. "grocery list app" shows slight
    decline over 12 months, suggesting the space may be maturing.

COMPETITOR DENSITY:     Crowded
  → Found 8+ direct competitors (AnyList, Paprika 3, Mealime, Yummly,
    SideChef, Plan to Eat, etc.). Most are mature with established user bases.

QUICK VERDICT:          Proceed with Caution
  → The pain is real but well-addressed. Entry requires a clear
    differentiation angle against 8+ mature competitors in a flat market.
    A niche focus (e.g., dietary restrictions, budget constraints) might work,
    but the default "meal planning app" is a tough space.

COMPETITOR PROFILE:
  | Competitor  | Target Audience        | Pricing   | Maturity   | Key Differentiator |
  |-------------|----------------------| --------- | --------- | ------------------- |
  | AnyList     | General consumers     | Freemium  | Mature     | Shared lists, recipe saving |
  | Paprika 3   | Home cooks            | Paid ($5) | Mature     | Powerful recipe management |
  | Mealime     | Health-conscious       | Free      | Established| Personalized meal plans |
  | Yummly      | General consumers     | Free      | Mature     | Owned by Whirlpool, smart appliance integration |
  | SideChef    | Home cooks            | Freemium  | Established| Step-by-step cooking mode |
  | Plan to Eat | Planning-focused users | Paid      | Established| Drag-and-drop meal planner |

PERCEPTUAL MAP:
  Axis X: General recipes → Dietary-specific (keto, allergy, budget)
  Axis Y: Recipe discovery → Automated planning + shopping

               Automated Planning
                      |
                      |
                      |
   General ------Plan to Eat------ Dietary-specific
   Recipes       SideChef         Mealime
                 Paprika 3
                 AnyList          [EMPTY]
                      |
                      |
               Recipe Discovery

  The dietary-specific + automated planning quadrant is underserved.
  Mealime touches dietary preferences but is more discovery-focused.
  However, in a flat market with 8+ mature competitors, a niche entry
  would need strong execution and retention.

DATA SOURCES:
  → Reddit: 7 posts across 2 subreddits (moderate)
  → Google Trends: Stable to slight decline (flat)
  → Web results: 8+ competitors, 4 informational (brave+tavily+duckduckgo)
```
