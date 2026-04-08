# Deep Dive Rubric — Detailed Methodology

This rubric covers the additional analysis performed in Deep Dive mode. The
Quick Screen scoring rubric in `scoring-rubric.md` still applies — Deep Dive
layers on top of it.

---

## Section 1: Pain Point Analysis (Detailed)

Expand the Quick Screen's pain point evidence with deeper qualitative analysis.

**What to do:**
- Pull representative quotes from the top Reddit posts (use the URLs from
  reddit_search.py output)
- Note community sizes (subreddit subscriber counts) as demand signals
- Assess urgency: is this a "nice to have" pain or a "must solve" pain?
- Consider whether the target audience discusses problems publicly (Reddit
  bias toward technical audiences — non-technical audiences may not vent online)

**Scoring signal:**
- If multiple posts describe the same specific frustration in different words,
  that's strong convergent evidence
- If posts recommend existing tools but complain about specific gaps, that's
  a differentiation opportunity worth noting
- If the top posts are all about discovering the problem (not solving it), the
  market may be too early

---

## Section 2: Trend Trajectory

The Quick Screen provides slope data. The Deep Dive adds interpretation.

**What to add:**
- Acceleration vs. deceleration: is the slope steepening or flattening?
- Seasonal patterns: does interest spike at predictable times (e.g., tax season,
  new year's resolutions)?
- Cross-reference: does the trend match the pain point evidence? Growing trend +
  strong pain = good timing. Growing trend + weak pain = possibly hype.
- Compare to adjacent spaces: is this keyword growing faster or slower than
  related terms?

---

## Section 3: Search Volume & Commercial Intent

**Limitation:** Exact monthly search volume requires a paid API (Keywords
Everywhere). This section provides directional estimates from publicly
available data via web_search.

**What to search for:**
- `"[keyword] monthly search volume 2025"` or `"[keyword] search volume"`
- `"[keyword] Google Ads keyword planner"` (public snippets sometimes appear)
- `"[keyword] how many people search"` or `"[keyword] market size"`

**What to extract:**
- Any concrete numbers that surface (even if from second-hand sources)
- Whether search volume is growing, stable, or declining
- Whether high-volume keywords have high CPC (suggests commercial intent)

**Honesty requirement:**
If no useful data surfaces, say so explicitly: "No reliable search volume
data found through web search. Google Trends relative interest is the best
available signal." Don't fabricate numbers.

---

## Section 4: Competitive Landscape (Detailed)

The Quick Screen provides surface-level categorization. The Deep Dive adds
real profiling.

**Competitor profiling via web_fetch:**
For each direct competitor, visit their landing page and extract:

| Field | What to extract |
|-------|----------------|
| Pricing tiers | Exact numbers (e.g., "Free: 3 projects. Pro: $19/mo. Enterprise: contact sales") |
| Core features | Top 5-8 features listed on their homepage or features page |
| Positioning | Their hero section tagline or value proposition (in their own words) |
| Maturity signals | "Trusted by 10,000+ teams," founding year, funding mentions, social proof |
| Target audience | Who their homepage speaks to (developers, enterprises, consumers?) |
| Integration ecosystem | "Works with Slack, GitHub, Notion" etc. — network effects |

**Feature Comparison Matrix:**
After profiling, build a markdown table:

```
| Feature | Competitor A | Competitor B | Competitor C | [User's Idea] |
|---------|-------------|-------------|-------------|---------------|
| Feature X | Yes | No | Yes | Planned |
| Feature Y | No | Yes | Yes | Planned |
| ...      | ... | ... | ... | ... |
```

Only include features that actually differentiate. If everyone has the same
feature, it's table stakes — omit it and focus on what varies.

**Dead competitor analysis:**
For dead projects found in the Quick Screen, speculate on why they failed:
- Was the market too small?
- Did a bigger player crush them?
- Was the timing wrong?
- Did they run out of money?

This is speculative but useful — it highlights risks the user's idea might face.

---

## Section 5: Product Hunt & Community Traction

**Search strategy:**
- `site:producthunt.com [idea space keywords]`
- `site:producthunt.com [competitor name]`
- Also check `site:news.ycombinator.com [idea space]` for HN Show posts

**What to extract per launch:**
- Product name and tagline
- Upvote count (strong signal: 500+ means real interest)
- Review/comment count and sentiment
- Launch date (how recent?)
- Tags/categories (what space does Product Hunt think this is?)

**Assessment questions:**
- Are there multiple recent launches, or is the space dormant on Product Hunt?
- Do launches get sustained attention, or is there a spike and fade?
- Is the space trending on Product Hunt (which may predict broader interest)?

---

## Section 6: G2 / Capterra Review Sentiment

**Search strategy:**
- `site:g2.com [competitor name] reviews`
- `site:capterra.com [competitor name]`

**What to extract:**
- Overall rating (X / 5 stars) and number of reviews
- Top 3 pros (most common positive themes)
- Top 3 cons (most common complaints)
- Recent review sentiment (are recent reviews better or worse than older ones?)

**What to look for:**
- Convergent complaints across competitors (e.g., "poor customer service,"
  "steep learning curve") indicate an opportunity
- If users rate competitors 4+ stars but still complain about specific things,
  those complaints are differentiation opportunities
- If the space has no G2/Capterra presence, the market may be too small or too
  early for B2B tools

---

## Section 7: Market Size Estimate (Fermi)

This is a structured estimation exercise, not a data query. The goal is a
testable, debatable set of assumptions with transparent math.

**Format:**

```
ASSUMPTIONS:
1. [Target market size]: [number + source/reasoning]
2. [Addressable segment]: [percentage + reasoning]
3. [Willingness to pay]: [percentage + reasoning]
4. [Average annual spend]: [dollar amount + reasoning]
5. [Growth rate]: [percentage + reasoning]

CALCULATION:
TAM = [total market] × [avg spend]
    = [number] × $[number]
    = $[X billion/million]

SAM = TAM × [addressable segment]
    = $[X] × [Y%]
    = $[Z]

SOM = SAM × [realistic capture rate in years 1-3]
    = $[Z] × [W%]
    = $[V]

CONFIDENCE: [Low / Medium / High]
WEAKEST ASSUMPTION: [which assumption is most likely wrong, and why]
SENSITIVITY: [if assumption X is off by 50%, how much does the estimate change?]
```

**Rules:**
- Every number must have a stated source or reasoning. No magic numbers.
- Bottom-up is preferred (start from customer count × price) over top-down
  (start from industry report total).
- If the user's idea targets a sub-segment, size the sub-segment, not the whole market.
- Flag if you're extrapolating from one geographic market to global.
- Low confidence is fine — the point is to make assumptions visible, not to be right.

---

## Section 8: Overall Assessment

Score each dimension 1-5 with a single-sentence justification:

| Dimension | Score | Why |
|-----------|-------|-----|
| Demand strength | 1-5 | [one sentence] |
| Timing | 1-5 | [one sentence] |
| Competition intensity | 1-5 | [one sentence] |
| Distribution difficulty | 1-5 | [one sentence] |

**Verdict options:**

- **Build** — Strong demand, good timing, manageable competition. The evidence
  supports investing real time and money.
- **Explore further** — Promising but ambiguous. Run 2-3 more Deep Dives on
  adjacent ideas to compare. Talk to 5-10 potential customers.
- **Pass** — The evidence doesn't support this idea. The pain is weak, the market
  is declining, or the space is too crowded. Move on.

**Key risks and open questions:**
- List 3-5 specific risks (not generic ones like "competition might increase")
- List 2-3 open questions that could be resolved with further research

---

## Example Deep Dive Report (excerpt)

```
IDEA VALIDATION REPORT
======================
Idea:    AI-powered invoice reconciliation for freelancers
Date:    2026-04-08
MODE:    Deep Dive

QUICK SCREEN SUMMARY
  Pain Point Evidence:  Strong (23 posts, 3 subreddits, avg 87 upvotes)
  Trend Direction:      Accelerating (slope 1.29, interest 25.4/100)
  Competitor Density:   Moderate (4 direct competitors, freelancer gap)
  Quick Verdict:        Investigate Further

1. PAIN POINT ANALYSIS (DETAILED)
   - Strong convergent evidence: 12 posts independently describe manually
     matching payments to invoices as their biggest workflow pain
   - Representative: "I spend 3+ hours every month chasing down which
     payment matches which invoice. Wave doesn't auto-match partial payments."
     (r/freelance, 142 upvotes)
   - Community size: r/freelance (430K members), r/smallbusiness (320K) —
     large, active audiences
   - Urgency: moderate-high. This is a daily operational pain, not aspirational.
     However, free tools (spreadsheets) provide partial relief, which may
     reduce willingness to pay.

4. COMPETITIVE LANDSCAPE (DETAILED)
   Competitor Matrix:
   | Competitor    | Pricing         | Core Features              | Maturity | Positioning                    |
   |---------------|----------------|---------------------------|----------|-------------------------------|
   | Wave          | Free / $15/mo   | Accounting, invoicing, receipts | Mature   | "Accounting software for small business" |
   | Invoice Ninja | Free / $10/mo   | Invoicing, expenses, time tracking | Established | "Free open-source invoicing" |
   | Zoho Invoice  | Free / $9/mo    | Invoicing, automation, estimates | Mature   | "Invoicing for every business" |
   | FreshBooks    | $19/mo          | Invoicing, time tracking, proposals | Mature   | "Accounting made for freelancers" |

   Gap: No competitor specifically addresses invoice reconciliation (matching
   bank transactions to invoices). All focus on creating/sending invoices.
   The matching/ reconciliation step is handled manually or via spreadsheets.

7. MARKET SIZE ESTIMATE (FERMI)
   ASSUMPTIONS:
   1. US freelancers: ~70M (Bureau of Labor Statistics, 2024)
   2. Freelancers who do project-based work with invoicing: ~40% = 28M
   3. Of those, who experience payment matching pain: ~30% = 8.4M
   4. Would pay for a solution: ~5% = 420K
   5. Average annual willingness to pay: $120/year

   CALCULATION:
   SAM = 8.4M × $120 = $1.0B
   SOM = 420K × $120 = $50.4M (years 1-3 at 5% penetration)

   CONFIDENCE: Low (assumptions 3 and 4 are rough; no direct data on
   reconciliation-specific willingness to pay)
   WEAKEST ASSUMPTION: Assumption 4 — willingness to pay is the biggest
   unknown. Many freelancers tolerate manual reconciliation using free tools.

8. OVERALL ASSESSMENT
   Demand strength:         4/5 — Real, frequent pain with convergent evidence
   Timing:                  4/5 — Accelerating interest, no dominant solution
   Competition intensity:   3/5 — Moderate competitors but none own reconciliation
   Distribution difficulty: 3/5 — Freelancers are fragmented; word-of-mouth channel

   VERDICT: Explore further
   The freelancer invoicing space has real demand and no one owns reconciliation.
   However, willingness to pay is uncertain and the SOM is small ($50M). Next
   step: survey 20 freelancers about their reconciliation workflow and what
   they'd pay to automate it.

   Key risks:
   - Wave or FreshBooks could add auto-reconciliation as a feature (high risk)
   - Freelancers may not pay enough to sustain a business (willingness to pay)
   - The 5% SOM penetration assumes no free alternatives improve

   Open questions:
   - What is the actual time saved per month from automated reconciliation?
   - Would this work better as a feature within an existing tool than standalone?
```
