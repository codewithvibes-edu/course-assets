# 2026 vendor sheet: data providers by quadrant

A curated list of free, paid, and synthetic data providers per quadrant
from Module 4. Pricing snapshots are 2026 Q2; URLs and availability
should be checked before signing anything.

## Vendor consolidation watch

The paid-data space has been consolidating since late 2025. Several
mid-tier news, market data, and people-data vendors have folded into
larger platforms over the last 18 months, and "no AI training" clauses
are now standard in new contracts signed after Q1 2026. The list below
churns quarterly. Treat any specific entry as a starting point for your
own research, not as a current recommendation.

A few patterns to expect when verifying:

- A vendor that was free a year ago may have introduced commercial tiers.
- A vendor that allowed unrestricted use may have added an "AI training
  prohibited" clause to new contracts (existing contracts are typically
  grandfathered, but read the renewal terms).
- A vendor's parent company may have changed; the data product may be
  rebranded or sunset within 12-24 months of an acquisition.

Every entry below has a hedged "verify active in 2026 Q2" note. If you
catch a stale entry, the source of truth is always the provider's site,
not this sheet.

---

## Q1: Your own data (tooling vendors)

These vendors do not provide the data (the data is yours); they help
you get it out of where it lives in a format you can feed to an LLM.

### Airbyte

- **What they offer:** Open-source and managed ELT connectors for 300+
  data sources (SaaS, databases, files).
- **Pricing snapshot:** Open-source self-hosted free. Cloud tier from
  about $0.025 per credit; usage-based pricing as of 2026 Q2.
- **URL:** https://airbyte.com
- **Verify active in 2026 Q2:** Yes; pricing is volume-driven, verify on
  the pricing page.

### Fivetran

- **What they offer:** Managed ELT pipelines, ~600 source connectors.
- **Pricing snapshot:** Consumption-based per "Monthly Active Rows" as
  of 2026 Q2. Starter and Standard tiers; verify per-connector pricing.
- **URL:** https://www.fivetran.com
- **Verify active in 2026 Q2:** Yes.

### Estuary Flow

- **What they offer:** Streaming + batch CDC, lower-latency than batch
  ELT competitors.
- **Pricing snapshot:** Free tier under 10 GB / month; paid tiers from
  about $1 per GB; verify.
- **URL:** https://estuary.dev
- **Verify active in 2026 Q2:** Yes; smaller vendor, monitor for
  acquisition or pricing changes.

### Unstructured.io

- **What they offer:** Parse PDFs, DOCX, emails, and other unstructured
  documents into LLM-ready chunks.
- **Pricing snapshot:** API at usage-based pricing; open-source library
  free. Hosted API rates published on the site.
- **URL:** https://unstructured.io
- **Verify active in 2026 Q2:** Yes; rapidly changing pricing model.

### LlamaParse (LlamaIndex)

- **What they offer:** PDF and complex document parsing tuned for RAG.
- **Pricing snapshot:** Free tier under 1,000 pages per day; commercial
  tiers per-page or per-document; verify.
- **URL:** https://www.llamaindex.ai/llamaparse
- **Verify active in 2026 Q2:** Yes.

---

## Q2: Public data (free providers)

### FRED (Federal Reserve Economic Data)

- **What they offer:** US economic time series. GDP, inflation, employment,
  rates, money supply, ~800K series.
- **Pricing snapshot:** Free.
- **URL:** https://fred.stlouisfed.org
- **Verify active in 2026 Q2:** Yes; stable government source.

### NOAA / National Weather Service

- **What they offer:** Weather observations, forecasts, climate data,
  satellite imagery.
- **Pricing snapshot:** Free.
- **URL:** https://www.weather.gov / https://www.ncei.noaa.gov
- **Verify active in 2026 Q2:** Yes; subject to US federal budget changes
  affecting endpoint availability.

### Open-Meteo

- **What they offer:** Free weather API with global coverage, no API key
  required for non-commercial use.
- **Pricing snapshot:** Free for non-commercial; commercial tier from
  about $29/month; verify.
- **URL:** https://open-meteo.com
- **Verify active in 2026 Q2:** Yes.

### Wikipedia / Wikidata API

- **What they offer:** Wikipedia article content, Wikidata structured
  knowledge graph (~100M items).
- **Pricing snapshot:** Free, rate-limited.
- **URL:** https://www.mediawiki.org/wiki/API:Main_page
- **Verify active in 2026 Q2:** Yes; respect the user-agent + rate-limit
  policy.

### Common Crawl

- **What they offer:** Petabyte-scale archive of web crawls; updated
  monthly. Available as WARC files on AWS S3.
- **Pricing snapshot:** Free; you pay AWS egress if you download.
- **URL:** https://commoncrawl.org
- **Verify active in 2026 Q2:** Yes; expect 1-3 months lag from "current"
  web state.

### OpenStreetMap (OSM)

- **What they offer:** Global open-data map. Roads, buildings, POIs.
- **Pricing snapshot:** Free under Open Database License (ODbL).
- **URL:** https://www.openstreetmap.org
- **Verify active in 2026 Q2:** Yes; license requires share-alike on
  derivative databases.

### data.gov

- **What they offer:** US federal open data catalog, ~300K datasets
  across agencies.
- **Pricing snapshot:** Free; quality varies wildly by agency.
- **URL:** https://www.data.gov
- **Verify active in 2026 Q2:** Yes; individual dataset URLs go stale
  often.

---

## Q3: Paid data (vendor APIs and licensed feeds)

### News and content

#### NewsAPI

- **What they offer:** Structured news headlines and article metadata
  from ~150K sources.
- **Pricing snapshot:** Free developer tier (delayed, non-commercial).
  Commercial plans from about $449/month as of 2026 Q2.
- **URL:** https://newsapi.org
- **Verify active in 2026 Q2:** Yes; check current AI-use clause in the
  commercial agreement.

#### Diffbot

- **What they offer:** Structured extraction from web pages (articles,
  products, organizations) plus a Knowledge Graph product.
- **Pricing snapshot:** Plans from about $299/month as of 2026 Q2; usage
  tiers above that.
- **URL:** https://www.diffbot.com
- **Verify active in 2026 Q2:** Yes; check AI-training clause for the
  Knowledge Graph product specifically.

### Financial and market data

#### Polygon.io

- **What they offer:** US equities, options, forex, and crypto market
  data. REST + WebSocket.
- **Pricing snapshot:** Free tier with 5 calls/minute. Paid plans from
  about $29/month (Starter) up through enterprise; verify.
- **URL:** https://polygon.io
- **Verify active in 2026 Q2:** Yes; tier names and limits change.

#### Alpha Vantage

- **What they offer:** Equities, forex, crypto, fundamentals. Smaller
  scope than Polygon but cheaper at entry.
- **Pricing snapshot:** Free tier ~25 calls/day. Premium from about
  $50/month; verify.
- **URL:** https://www.alphavantage.co
- **Verify active in 2026 Q2:** Yes.

### Identity, contacts, firmographics

#### Clearbit (now Breeze Intelligence under HubSpot)

- **What they offer:** Company and person enrichment via email or domain
  lookup.
- **Pricing snapshot:** Acquired by HubSpot in 2024 and rebranded as
  Breeze Intelligence; pricing is now bundled into HubSpot tiers as of
  2026 Q2. Verify on the HubSpot pricing page; standalone Clearbit
  pricing no longer exists.
- **URL:** https://www.hubspot.com/products/marketing/breeze-intelligence
- **Verify active in 2026 Q2:** Yes, under new branding. Older Clearbit
  API endpoints may still resolve but are not the supported product.

#### Apollo.io

- **What they offer:** B2B contact database, sales engagement.
- **Pricing snapshot:** Free tier; paid tiers from about $49/user/month
  as of 2026 Q2.
- **URL:** https://www.apollo.io
- **Verify active in 2026 Q2:** Yes.

### Security and vulnerability

#### GitHub Advanced Security

- **What they offer:** CVE feed, secret scanning, code scanning, and
  Dependabot alerts.
- **Pricing snapshot:** Per-active-committer; verify current per-seat
  pricing on the GitHub pricing page.
- **URL:** https://github.com/security/advanced-security
- **Verify active in 2026 Q2:** Yes.

#### Snyk

- **What they offer:** Vulnerability database, SCA, container scanning.
- **Pricing snapshot:** Free tier; team and enterprise tiers; verify.
- **URL:** https://snyk.io
- **Verify active in 2026 Q2:** Yes.

### Web search and crawling APIs

#### Brave Search API

- **What they offer:** Web search API with explicit terms for AI use.
- **Pricing snapshot:** Free tier (~2K queries/month); paid plans from
  about $5 per 1K queries as of 2026 Q2; verify.
- **URL:** https://brave.com/search/api
- **Verify active in 2026 Q2:** Yes; rapidly evolving AI-training terms.

#### Exa (formerly Metaphor)

- **What they offer:** Search API designed for LLM use, semantic search
  over the web.
- **Pricing snapshot:** Usage-based, verify; free tier for development.
- **URL:** https://exa.ai
- **Verify active in 2026 Q2:** Yes.

#### Tavily

- **What they offer:** Search API tuned for agentic workflows, returns
  cleaned, summarized results.
- **Pricing snapshot:** Free tier; paid tiers usage-based; verify.
- **URL:** https://tavily.com
- **Verify active in 2026 Q2:** Yes; smaller vendor, watch for changes.

---

## Q4: Synthetic data (generators and tooling)

### General-purpose synthetic data via frontier APIs

Frontier model APIs (Anthropic, OpenAI, Google) are the most common
synthetic data generators. They are not "vendors" in the data sense;
they are tools you point at a prompt to produce structured output.

- **Anthropic API:** https://www.anthropic.com/api. Verify per-token
  pricing on the pricing page.
- **OpenAI API:** https://platform.openai.com. Verify pricing.
- **Google Gemini API:** https://ai.google.dev. Verify pricing.

For eval set seed generation, budget $5-$20 of API spend per use case.
For larger synthetic training corpora, model the cost against your token
projection (see `assets/m3-routing/cost-model.csv`).

### Synthetic data platforms

#### Gretel.ai

- **What they offer:** Synthetic structured data generation with privacy
  guarantees (differential privacy options).
- **Pricing snapshot:** Free tier; paid plans usage-based as of 2026 Q2.
- **URL:** https://gretel.ai
- **Verify active in 2026 Q2:** Yes; competitive landscape is volatile.

#### Mostly AI

- **What they offer:** Synthetic data generation for tabular and time-series
  data, GDPR-aligned use cases.
- **Pricing snapshot:** Community edition free; commercial plans from
  enterprise contact pricing as of 2026 Q2.
- **URL:** https://mostly.ai
- **Verify active in 2026 Q2:** Yes.

#### Tonic.ai

- **What they offer:** De-identified production-like data for staging
  and testing.
- **Pricing snapshot:** Commercial only; contact for pricing as of 2026 Q2.
- **URL:** https://www.tonic.ai
- **Verify active in 2026 Q2:** Yes.

---

## Notes on this list

1. Every "Pricing snapshot" entry is from 2026 Q2 (May 2026). Vendor
   pricing pages are the source of truth; treat this sheet as a starting
   point for your own search.
2. Open-source startup churn is real. Some of the smaller Q4 vendors
   listed here may be acquired, pivoted, or sunset between now and the
   next quarter. If you commit to a vendor in this category, prefer the
   ones with an open-source backbone you could self-host as a fallback.
3. "Free tier" usually has hard rate limits, no SLA, and no commercial
   use rights. Read the terms before assuming a free tier is a viable
   production posture.
4. For every paid vendor, run the 10-question due-diligence checklist
   in `license-checklist.md` before signing.
