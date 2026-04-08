---
name: idea-validator
description: >
  Pressure-test startup and product ideas against live market signals. Given a product
  or business idea, this skill searches Reddit for pain-point evidence, checks Google
  Trends for demand trajectory, and scans the web for competitive landscape — then
  synthesizes everything into a scorecard with a verdict. Supports two modes: a fast
  Quick Screen (scripts + structured data) and a Deep Dive (Quick Screen results +
  agent-native web_search/web_fetch for competitor profiling, market sizing, Product
  Hunt traction, and review sentiment). Use this skill whenever the user asks to
  validate, vet, evaluate, or stress-test an idea, startup concept, product
  hypothesis, or business thesis. Also trigger when the user mentions "should I
  build this," "is this a good idea," "is there demand for," "market validation,"
  "deep dive on this idea," or presents a product concept and wants an
  evidence-based assessment.
---

# Idea Validator

You are an analyst, not an oracle. Your job is to find evidence for and against
a product idea and present it honestly. Do not flatter the user's idea. Do not
dismiss it prematurely. Follow the evidence.

## Mode Selection

When the user provides an idea, ask them which analysis mode they want:

- **Quick Screen** — Fast. Runs 3 bundled Python scripts (Reddit, Google Trends,
  web scan), produces a scorecard with pain evidence, trend direction, competitor
  profile, perceptual map, and a verdict. Takes 1-2 minutes.
- **Deep Dive** — Thorough. Runs the Quick Screen first, then uses agent-native
  web_search and web_fetch to do competitor deep profiling, Product Hunt traction
  scan, G2/Capterra review sentiment analysis, and Fermi market sizing. Produces
  a full validation report. Takes 5-10 minutes depending on the number of
  competitors found.

Recommend Quick Screen for most ideas. Recommend Deep Dive when:
- The Quick Screen verdict was "Investigate Further" and the user wants more
  detail before committing time
- The user explicitly asks for a deeper analysis, market sizing, or competitor
  profiling
- The user asks "should I build this" — go straight to Deep Dive

---

## Quick Screen Pipeline

### Step 1 — Extract Keywords

From the user's idea thesis, extract four categories of terms:

- **Core problem terms:** The specific pain or need (e.g., "invoice reconciliation," "meal prep planning")
- **Audience descriptors:** Who has this problem (e.g., "freelancers," "small business owners")
- **Adjacent synonyms:** Alternative phrasings people might use (e.g., "expense tracking," "budget meals")
- **Candidate subreddits:** 5-10 subreddits where people with this problem likely congregate

Present the extracted keywords to the user briefly before proceeding, in case
they want to adjust.

### Step 2 — Gather Evidence (run all three scripts in parallel)

Run each of the bundled scripts and capture their JSON output. If a script fails
(e.g., API key missing, network blocked), note the failure and continue with
what you have.

**Script 1: Reddit pain-point search**

```bash
uv run python <skill-path>/scripts/reddit_search.py \
  --keywords "keyword1,keyword2,keyword3" \
  --subreddits "sub1,sub2,sub3"
```

**Script 2: Google Trends check**

```bash
uv run python <skill-path>/scripts/trends_check.py \
  --keywords "keyword1,keyword2,keyword3"
```

**Script 3: Web competitor scan**

```bash
uv run python <skill-path>/scripts/web_scan.py \
  --query "descriptive search query about the product space"
```

### Step 3 — Synthesize the Scorecard

Read the scoring rubric at `<skill-path>/references/scoring-rubric.md` for
detailed criteria. Produce a scorecard using this format:

```
IDEA: [user's thesis]
DATE: [current date]
MODE: Quick Screen

PAIN POINT EVIDENCE:    Strong / Moderate / Weak / None
  → [2-3 sentence summary referencing Reddit thread count, engagement, recency]

TREND DIRECTION:        Accelerating / Flat / Declining
  → [1 sentence summarizing Google Trends trajectory]

COMPETITOR DENSITY:     Open / Moderate / Crowded
  → [1 sentence naming key competitors or noting absence of competition]

QUICK VERDICT:          Investigate Further / Proceed with Caution / Kill
  → [2-3 sentence rationale tied to the evidence above]

COMPETITOR PROFILE:
  | Competitor | Target Audience | Pricing | Maturity | Key Differentiator |
  |------------|----------------|---------|----------|-------------------|
  | [name]     | [who they serve] | [free/freemium/paid] | [emerging/established/mature] | [what makes them distinct] |

PERCEPTUAL MAP:
  Axis X: [meaningful dimension 1]
  Axis Y: [meaningful dimension 2]

  [Text-based 2x2 with competitors placed and whitespace highlighted]

  [1-2 sentences explaining the whitespace]

DATA SOURCES:
  → Reddit: [status]
  → Google Trends: [status]
  → Web results: [status]
```

**Scoring principles:**

- Each dimension (pain, trend, competition) is scored independently.
- The verdict follows from the weight of evidence, not a formula.
- If a data source failed, say so explicitly and note how that affects confidence.
- Do not hedge every statement. If the evidence clearly points one way, say so.

**Perceptual map guidance:**

- Choose axes derived from the idea's value proposition and competitors found.
  "Price vs. quality" is too generic. Better: "breadth of coverage vs. depth of
  analysis," "DIY tool vs. managed service."
- If fewer than 2 direct competitors, note "Insufficient competitors to map."
- Place competitors based on what can be inferred from titles, descriptions, and URLs.
- Always highlight the whitespace.

**Competitor profile guidance:**

For each direct competitor, extract from the web scan results (don't visit sites):
- **Target audience:** Who they serve (infer from description)
- **Pricing:** "Free," "Freemium," "Paid," or "Unknown"
- **Maturity:** "Emerging," "Established," or "Mature"
- **Key differentiator:** What sets them apart (one line)

### Step 4 — Offer Follow-Up

After presenting the scorecard, ask the user if they want to:
- **Run a Deep Dive** on this idea (competitor profiling, market sizing, traction)
- Run a **Feature Comparison Matrix** (deeper competitor extraction)
- **Save results** as a markdown file
- Validate a different idea

---

## Deep Dive Pipeline

The Deep Dive runs the Quick Screen first, then layers on additional analysis
using agent-native web_search and web_fetch. The Quick Screen provides the
foundation; the Deep Dive adds depth for ideas worth investigating further.

### Step 1 — Run the Quick Screen

Execute the full Quick Screen pipeline (Steps 1-3 above). The Deep Dive builds
on these results.

### Step 2 — Competitor Deep Profiling

For each direct competitor identified in the Quick Screen, use web_fetch to
visit their landing page and pricing page. Extract:

- **Pricing tiers** (exact numbers: free tier limits, pro price, enterprise price)
- **Core features** (top 5-8 features listed on their site)
- **Positioning language** (how they describe themselves in their hero section)
- **Maturity signals** (founding year if shown, "trusted by X users," social proof)
- **Review sentiment** (if testimonials or review scores are visible)

If there are 6+ competitors, profile the top 5 by relevance and note the rest
summarily.

### Step 3 — Product Hunt Traction Scan

Use web_search to find recent launches in the same space:
- Search: `site:producthunt.com [idea space keywords]`
- For each relevant launch found, use web_fetch to get upvote count, tagline,
  review count, and launch date
- Assess: is this space active on Product Hunt? Are recent launches getting
  traction?

### Step 4 — G2 / Capterra Review Sentiment

For the top 2-3 competitors, use web_search to find their G2 or Capterra
listing, then web_fetch to read reviews:
- Search: `site:g2.com [competitor name]` or `site:capterra.com [competitor name]`
- Extract: overall rating, number of reviews, top complaints, top praises
- Look for patterns: do users consistently ask for something that doesn't exist?

### Step 5 — Search Volume Estimation

Use web_search to find search volume data from publicly available sources:
- Search for "[keyword] search volume" or "[keyword] monthly searches"
- Check Google Ads Keyword Planner snippets that sometimes appear in results
- Cross-reference with the Google Trends data from the Quick Screen

Note: exact search volume requires a paid API (Keywords Everywhere). This step
provides directional estimates, not precise numbers. Be transparent about this
limitation.

### Step 6 — Fermi Market Sizing

Produce a back-of-envelope market size estimate using the LLM's reasoning.
This is not data-driven — it's a structured estimation exercise. The prompt
forces you to:

1. State every assumption explicitly (market size, pricing, penetration rate,
   growth rate)
2. Show the math step by step (bottom-up from a realistic customer count)
3. Provide TAM / SAM / SOM estimates
4. Assign a confidence level: Low / Medium / High
5. Flag the weakest assumptions (these are where the estimate could be most wrong)

Be specific with numbers. "The market is probably big" is useless. "There are
~15M freelancers in the US, 30% use invoicing tools, average annual spend is
$120, suggesting a $540M SAM" is useful even if the assumptions are rough.

### Step 7 — Synthesize the Deep Dive Report

Read the deep dive rubric at `<skill-path>/references/deep-dive-rubric.md`.
Produce a report using this format:

```
IDEA VALIDATION REPORT
======================
Idea:    [thesis]
Date:    [current date]
MODE:    Deep Dive

QUICK SCREEN SUMMARY
  Pain Point Evidence:  [rating from quick screen]
  Trend Direction:      [rating from quick screen]
  Competitor Density:   [rating from quick screen]
  Quick Verdict:        [verdict from quick screen]

1. PAIN POINT ANALYSIS (DETAILED)
   - Expanded evidence summary with representative quotes/threads and URLs
   - Community size and activity metrics
   - Assessment: is this pain acute enough to pay for?

2. TREND TRAJECTORY
   - Google Trends data (12mo + 5yr) with acceleration/deceleration notes
   - Search volume estimates and commercial intent signals
   - Seasonal patterns if detected

3. SEARCH VOLUME & COMMERCIAL INTENT
   - Estimated search volume for top keywords
   - Volume trajectory (growing/shrinking)
   - Commercial intent assessment based on available data
   - Limitation note: exact volume requires paid API

4. COMPETITIVE LANDSCAPE (DETAILED)
   - Competitor matrix: name, pricing tiers, core features, maturity, positioning
   - Identified gaps (features/audiences no one serves well)
   - Dead competitors and why they may have failed
   - Saturation assessment: growing niche vs. mature market
   - Feature Comparison Matrix (if available from profiling)

5. PRODUCT HUNT & COMMUNITY TRACTION
   - Recent launches in the space
   - Upvote counts, review counts, community engagement
   - Assessment: is this space getting attention from early adopters?

6. G2 / CAPTERRA REVIEW SENTIMENT
   - Top competitors: ratings, review counts, top complaints and praises
   - Common unmet needs across reviews
   - Assessment: are users unhappy with existing options in fixable ways?

7. MARKET SIZE ESTIMATE (FERMI)
   - Stated assumptions
   - TAM / SAM / SOM with math shown
   - Confidence level: Low / Medium / High
   - Weakest assumptions flagged

8. OVERALL ASSESSMENT
   - Demand strength:         [1-5 with justification]
   - Timing:                  [1-5 with justification]
   - Competition intensity:   [1-5 with justification]
   - Distribution difficulty: [1-5 with justification]
   - VERDICT:                 Build / Explore further / Pass
   - Key risks and open questions
   - Recommended next steps

DATA SOURCES:
  → Quick Screen: [script results summary]
  → Competitor profiling: [X competitors visited via web_fetch]
  → Product Hunt: [X launches found, or "none found"]
  → G2/Capterra: [X listings found, or "none found"]
  → Search volume: [directional estimates from web_search, or "no data"]
  → Market sizing: [Fermi estimate, confidence: X]
```

### Step 8 — Offer Follow-Up

After presenting the report, ask the user if they want to:
- **Save results** as a markdown file
- Explore a specific section in more detail
- Validate a different idea

---

## Saving Results

After either mode completes, ask the user:

"Would you like me to save these results as a markdown file?"

If yes, write to the current working directory using this naming convention:

```
[YEAR]-[MONTH]-[DAY]_[MODE]_[SHORT-DESCRIPTION].md
```

Examples:
- `2026-04-08_quick-screen_ai-invoice-reconciliation.md`
- `2026-04-08_deep-dive_prediction-market-divergence.md`

The file should contain the full scorecard or report as rendered in the
conversation, with the raw data section included. Prepend a one-line header:

```
<!-- Generated by idea-validator skill on 2026-04-08T14:30:00 -->
```

---

## Dependencies

The project uses `uv` for dependency management. Run `uv sync` to install.
The `uv run` prefix ensures scripts use the project's virtual environment.

**Quick Screen scripts:**
- `web_scan.py` tries DuckDuckGo (no key), Tavily (`TAVILY_API_KEY`), and
  Brave (`BRAVE_API_KEY`) in parallel. At least DuckDuckGo works with no config.
- `trends_check.py` uses trendspy. No API key needed.
- `reddit_search.py` uses public Reddit JSON endpoints. No API key needed.

**Deep Dive tools:**
- Agent-native `web_search` and `web_fetch` (available in Claude Code, Codex,
  OpenCode, and similar agents). No additional setup required.
- No paid APIs needed. Search volume estimation uses publicly available data
  with a directional-accuracy caveat.

**What you don't need:**
- No database (each run is self-contained)
- No paid API keys (optional Brave/Tavily for better quick screen coverage)
- No deployment (runs inside the agent conversation)
