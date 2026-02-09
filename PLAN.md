# AI Updates Daily Digest — Product & Engineering Plan

> **One-sentence definition:** Every day at a set time, deliver a personalized, citation-backed digest of what changed across AI companies AND the AI builder community (models, APIs, SDKs, pricing, docs, incidents, launches) and why it matters.

---

## 1) ASSUMPTIONS

| # | Assumption | Rationale |
|---|-----------|-----------|
| A1 | **Primary audience**: AI/ML engineers, developer-advocates, and technical PMs who build on top of foundation-model APIs. Secondary: founders, VCs, tech journalists. | Determines depth and jargon level. |
| A2 | **Initial company watchlist**: ~30 companies / ~60 product lines (see Section 3 starter list). | Covers the "must-have" ecosystem; more added in Phase 3. |
| A3 | **MVP delivery channel**: email (HTML) + static web archive page. Slack/Discord/RSS as Phase 4 add-ons. | Email has the highest reach and lowest integration cost. |
| A4 | **Language**: English first. Spanish (Latin America) as Phase 4 localization. | Matches default timezone (Argentina) and global dev audience. |
| A5 | **Team size at start**: 1 full-stack engineer + 1 part-time product/content person. | Keeps scope honest for MVP. |
| A6 | **LLM access**: We have API access to at least one frontier model (Claude, GPT-4-class) for summarization and classification. | Core to grounded summarization. |
| A7 | **Budget for external data**: $0 for MVP (public sources only). Budget for licensed news feeds evaluated in Phase 3. | Avoids licensing risk in MVP. |
| A8 | **No user accounts in Phase 1.** Digest is a public/mailing-list product. User preferences arrive in Phase 2+. | Reduces infra scope. |
| A9 | **Storage**: PostgreSQL (primary), S3-compatible object store (raw snapshots), pgvector extension added in Phase 2 for semantic dedup. | Mature, single-database simplicity. |
| A10 | **"Day" boundary**: 08:00 America/Argentina/Cordoba (UTC-3) previous day to current day. | Matches the delivery time. |

---

## 2) PRD — Product Requirements Document

### 2.1 Problem

AI builders waste 30–60 min/day scanning changelogs, Twitter/X, Hacker News, and Discord to find out what shipped, what broke, and what matters. Critical changes (deprecations, pricing hikes, outages) are often discovered too late. Community launches with real signal are drowned in noise.

### 2.2 Target Users

| Persona | Needs |
|---------|-------|
| **Builder** (ML/software engineer) | Know when APIs, SDKs, models change so code doesn't break. |
| **Tech Lead / Architect** | Evaluate new capabilities and pricing to inform stack decisions. |
| **DevRel / PM** | Stay current on competitor moves and community trends. |
| **Founder / VC** | Weekly-level awareness of ecosystem shifts and emerging tools. |

### 2.3 One-Sentence Product Definition

(Repeated for anchoring): *Every day at a set time, deliver a personalized, citation-backed digest of what changed across AI companies AND the AI builder community and why it matters.*

### 2.4 MVP Scope

**In scope (Phase 1):**
- Daily email digest at 08:00 ART with stable section structure.
- 20–40 Tier 1 sources ingested automatically.
- Manual curation layer (human review before send) for first 2 weeks, then optional.
- Community Radar with Hacker News + GitHub trending.
- Web archive of past digests (static HTML).

**Non-goals (MVP):**
- Real-time alerting / push notifications.
- User accounts, login, or personalization.
- Paid subscriptions or monetization.
- Mobile app.
- Non-English digests.
- Full-text article hosting (we link out).

### 2.5 User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-1 | As a builder, I want a daily email summarizing all AI API/SDK changes so I don't miss breaking changes. | P0 |
| US-2 | As a builder, I want each item to separate "what changed" from "why it matters" so I can skim facts fast. | P0 |
| US-3 | As a builder, I want citations (links) on every claim so I can verify before acting. | P0 |
| US-4 | As a tech lead, I want items tagged by severity (High/Med/Low) so I can triage. | P0 |
| US-5 | As a reader, I want a Community Radar section showing promising new tools with signal metrics. | P1 |
| US-6 | As a reader, I want to browse past digests on a web page. | P1 |
| US-7 | As a user, I want to follow/unfollow specific companies or categories. | P2 (Phase 2) |
| US-8 | As a user, I want a "only breaking changes" mode. | P2 (Phase 2) |
| US-9 | As a user, I want thumbs-up/down on items so the digest improves. | P2 (Phase 2) |
| US-10 | As a reader, I want the digest in Spanish. | P3 (Phase 4) |

### 2.6 Daily Digest UX — Structure

The digest is divided into **7 stable sections**, always in this order:

```
=============================================
AI DAILY DIGEST — {date}
=============================================

[OVERVIEW]  (1 paragraph, optional, generated)

---------------------------------------------
[1] TOP 5 — HIGH IMPACT
---------------------------------------------
  1. {Title} [{Severity}] [{Category}]
     Company: {name}
     What changed: {bullet(s) — facts only, with [citation]}
     Why it matters: {1-2 sentences — interpretation}
     Action items: {optional}
     Sources: {link1}, {link2}

  2. ...
  ...5 items max.

---------------------------------------------
[2] DEVELOPER CHANGES (API / SDK / Deprecations)
---------------------------------------------
  (same item template, 3-8 items)

---------------------------------------------
[3] MODELS & CAPABILITIES
---------------------------------------------
  (same item template, 3-8 items)

---------------------------------------------
[4] PRICING & LIMITS
---------------------------------------------
  (same item template, 1-5 items)

---------------------------------------------
[5] INCIDENTS & RELIABILITY
---------------------------------------------
  (same item template, 0-5 items)

---------------------------------------------
[6] COMMUNITY RADAR
---------------------------------------------
  Launch Card:
    Name: {tool name}
    What it is: {1 sentence}
    Why people like it: {snippet from comments/discussion}
    Try it: {repo URL / demo URL}
    Signals: {stars}, {upvotes}, {velocity} ({percentile})

  (3-6 cards)

---------------------------------------------
[7] EVERYTHING ELSE (SKIM)
---------------------------------------------
  - {one-liner + link} [{Category}]
  - ...
  (unlimited, compact format)

=============================================
Feedback: {thumbs link} | Preferences: {link}
=============================================
```

### 2.7 Item Template (detailed)

Each non-Radar item follows this schema:

| Field | Required | Notes |
|-------|----------|-------|
| `title` | Yes | Short, action-oriented headline. |
| `severity` | Yes | `HIGH` / `MEDIUM` / `LOW`. |
| `category` | Yes | One or more from the 30-category taxonomy. |
| `company` | Yes | Resolved entity name. |
| `product_line` | If applicable | e.g., "OpenAI / ChatGPT" vs "OpenAI / API". |
| `what_changed` | Yes | Bullet list, factual, each bullet with `[source]`. |
| `why_it_matters` | Yes | 1-2 sentences, interpretation. Labeled as opinion/analysis. |
| `action_items` | Optional | Concrete next steps for a developer. |
| `breaking_change` | Yes | Boolean flag. |
| `citations` | Yes | List of URLs. |
| `trust_tier` | Yes | Highest tier of evidence (1/2/3/4). |
| `confidence` | Yes | `confirmed` / `likely` / `unverified`. |

### 2.8 Personalization Knobs (Phase 2+)

| Knob | Type | Default |
|------|------|---------|
| Followed companies | Multi-select | All |
| Followed categories | Multi-select (from 30) | All |
| Severity filter | `all` / `medium+` / `high-only` | `all` |
| Breaking changes only | Boolean | `false` |
| Frequency | `daily` / `weekdays` / `weekly-monday` | `daily` |
| Delivery time | Time + timezone | 08:00 America/Argentina/Cordoba |
| Delivery channel | `email` / `slack` / `discord` / `rss` | `email` |

---

## 3) SOURCE REGISTRY DESIGN (Control Plane)

### 3.1 Source Registry Schema

```
Source {
  source_id          UUID        PK
  company_slug       TEXT        -- e.g., "openai"
  company_name       TEXT        -- e.g., "OpenAI"
  product_line       TEXT        -- e.g., "API", "ChatGPT", "Platform" (nullable)
  source_name        TEXT        -- human label, e.g., "OpenAI API Changelog"
  source_url         TEXT        -- canonical URL
  fetch_method       ENUM        -- rss | html_diff | github_releases |
                                    api_poll | social_api | manual
  poll_frequency_min INT         -- minutes between fetches (default 60)
  trust_tier         INT         -- 1 (first-party) | 2 | 3 | 4
  priority           ENUM        -- critical | high | normal | low
  parse_rules        JSONB       -- CSS selectors, RSS field mappings, etc.
  health_status      ENUM        -- healthy | degraded | dead
  last_fetched_at    TIMESTAMPTZ
  last_item_at       TIMESTAMPTZ -- most recent item timestamp
  enabled            BOOLEAN     -- default true
  notes              TEXT
  created_at         TIMESTAMPTZ
  updated_at         TIMESTAMPTZ
}
```

### 3.2 Starter Source Registry (Markdown Table)

| company_slug | company_name | product_line | source_name | source_url | fetch_method | poll_freq_min | trust_tier | priority |
|---|---|---|---|---|---|---|---|---|
| openai | OpenAI | API | API Changelog | https://platform.openai.com/docs/changelog | html_diff | 60 | 1 | critical |
| openai | OpenAI | Platform | Status Page | https://status.openai.com | rss | 15 | 1 | critical |
| openai | OpenAI | — | Blog | https://openai.com/blog | rss | 120 | 1 | high |
| openai | OpenAI | API | GitHub Python SDK | https://github.com/openai/openai-python/releases | github_releases | 60 | 1 | high |
| anthropic | Anthropic | API | API Changelog | https://docs.anthropic.com/en/docs/about-claude/changelog | html_diff | 60 | 1 | critical |
| anthropic | Anthropic | — | Status Page | https://status.anthropic.com | rss | 15 | 1 | critical |
| anthropic | Anthropic | — | Blog / News | https://www.anthropic.com/news | rss | 120 | 1 | high |
| anthropic | Anthropic | API | GitHub Python SDK | https://github.com/anthropics/anthropic-sdk-python/releases | github_releases | 60 | 1 | high |
| google | Google | Gemini API | Changelog | https://ai.google.dev/changelog | html_diff | 60 | 1 | critical |
| google | Google | Vertex AI | Release Notes | https://cloud.google.com/vertex-ai/docs/release-notes | rss | 60 | 1 | critical |
| google | Google | — | AI Blog | https://blog.google/technology/ai/ | rss | 120 | 1 | high |
| meta | Meta | Llama | GitHub Releases | https://github.com/meta-llama | github_releases | 120 | 1 | high |
| meta | Meta | — | AI Blog | https://ai.meta.com/blog/ | rss | 180 | 1 | high |
| mistral | Mistral AI | API | Changelog | https://docs.mistral.ai/changelog/ | html_diff | 60 | 1 | high |
| mistral | Mistral AI | — | GitHub Releases | https://github.com/mistralai | github_releases | 120 | 1 | high |
| cohere | Cohere | API | Changelog | https://docs.cohere.com/changelog | html_diff | 60 | 1 | high |
| aws | AWS | Bedrock | What's New | https://aws.amazon.com/about-aws/whats-new/ | rss | 60 | 1 | high |
| microsoft | Microsoft | Azure OpenAI | Release Notes | https://learn.microsoft.com/en-us/azure/ai-services/openai/whats-new | html_diff | 60 | 1 | high |
| huggingface | Hugging Face | Hub | Blog | https://huggingface.co/blog | rss | 120 | 1 | high |
| langchain | LangChain | — | GitHub Releases | https://github.com/langchain-ai/langchain/releases | github_releases | 60 | 1 | high |
| llamaindex | LlamaIndex | — | GitHub Releases | https://github.com/run-llama/llama_index/releases | github_releases | 60 | 1 | high |
| vercel | Vercel | AI SDK | GitHub Releases | https://github.com/vercel/ai/releases | github_releases | 60 | 1 | high |
| stability | Stability AI | — | Blog | https://stability.ai/news | rss | 180 | 1 | normal |
| replicate | Replicate | — | Blog/Changelog | https://replicate.com/changelog | html_diff | 120 | 1 | normal |
| together | Together AI | — | Blog | https://www.together.ai/blog | rss | 180 | 1 | normal |
| groq | Groq | API | Changelog | https://console.groq.com/docs/changelog | html_diff | 60 | 1 | high |
| — | Community | HN | Hacker News Show HN | https://hn.algolia.com/api/v1/search?tags=show_hn | api_poll | 30 | 4 | normal |
| — | Community | Reddit | r/MachineLearning | https://www.reddit.com/r/MachineLearning/.rss | rss | 30 | 4 | normal |
| — | Community | Reddit | r/LocalLLaMA | https://www.reddit.com/r/LocalLLaMA/.rss | rss | 30 | 4 | normal |
| — | Community | PH | Product Hunt AI | https://www.producthunt.com/topics/artificial-intelligence | api_poll | 60 | 4 | normal |
| — | Community | GitHub | GitHub Trending ML | https://github.com/trending?since=daily | html_diff | 60 | 4 | normal |

### 3.3 Starter Source Registry (CSV)

```csv
company_slug,company_name,product_line,source_name,source_url,fetch_method,poll_freq_min,trust_tier,priority
openai,OpenAI,API,API Changelog,https://platform.openai.com/docs/changelog,html_diff,60,1,critical
openai,OpenAI,Platform,Status Page,https://status.openai.com,rss,15,1,critical
openai,OpenAI,,Blog,https://openai.com/blog,rss,120,1,high
openai,OpenAI,API,GitHub Python SDK,https://github.com/openai/openai-python/releases,github_releases,60,1,high
anthropic,Anthropic,API,API Changelog,https://docs.anthropic.com/en/docs/about-claude/changelog,html_diff,60,1,critical
anthropic,Anthropic,,Status Page,https://status.anthropic.com,rss,15,1,critical
anthropic,Anthropic,,Blog / News,https://www.anthropic.com/news,rss,120,1,high
anthropic,Anthropic,API,GitHub Python SDK,https://github.com/anthropics/anthropic-sdk-python/releases,github_releases,60,1,high
google,Google,Gemini API,Changelog,https://ai.google.dev/changelog,html_diff,60,1,critical
google,Google,Vertex AI,Release Notes,https://cloud.google.com/vertex-ai/docs/release-notes,rss,60,1,critical
google,Google,,AI Blog,https://blog.google/technology/ai/,rss,120,1,high
meta,Meta,Llama,GitHub Releases,https://github.com/meta-llama,github_releases,120,1,high
meta,Meta,,AI Blog,https://ai.meta.com/blog/,rss,180,1,high
mistral,Mistral AI,API,Changelog,https://docs.mistral.ai/changelog/,html_diff,60,1,high
mistral,Mistral AI,,GitHub Releases,https://github.com/mistralai,github_releases,120,1,high
cohere,Cohere,API,Changelog,https://docs.cohere.com/changelog,html_diff,60,1,high
aws,AWS,Bedrock,What's New,https://aws.amazon.com/about-aws/whats-new/,rss,60,1,high
microsoft,Microsoft,Azure OpenAI,Release Notes,https://learn.microsoft.com/en-us/azure/ai-services/openai/whats-new,html_diff,60,1,high
huggingface,Hugging Face,Hub,Blog,https://huggingface.co/blog,rss,120,1,high
langchain,LangChain,,GitHub Releases,https://github.com/langchain-ai/langchain/releases,github_releases,60,1,high
llamaindex,LlamaIndex,,GitHub Releases,https://github.com/run-llama/llama_index/releases,github_releases,60,1,high
vercel,Vercel,AI SDK,GitHub Releases,https://github.com/vercel/ai/releases,github_releases,60,1,high
stability,Stability AI,,Blog,https://stability.ai/news,rss,180,1,normal
replicate,Replicate,,Blog/Changelog,https://replicate.com/changelog,html_diff,120,1,normal
together,Together AI,,Blog,https://www.together.ai/blog,rss,180,1,normal
groq,Groq,API,Changelog,https://console.groq.com/docs/changelog,html_diff,60,1,high
,Community,HN,Hacker News Show HN,https://hn.algolia.com/api/v1/search?tags=show_hn,api_poll,30,4,normal
,Community,Reddit,r/MachineLearning,https://www.reddit.com/r/MachineLearning/.rss,rss,30,4,normal
,Community,Reddit,r/LocalLLaMA,https://www.reddit.com/r/LocalLLaMA/.rss,rss,30,4,normal
,Community,PH,Product Hunt AI,https://www.producthunt.com/topics/artificial-intelligence,api_poll,60,4,normal
,Community,GitHub,GitHub Trending ML,https://github.com/trending?since=daily,html_diff,60,4,normal
```

### 3.4 Source Onboarding Workflow

```
Step 1: SUGGEST
  - System scans known AI companies + their domains.
  - LLM generates candidate source URLs (changelog, blog, status, GitHub org).
  - Candidate list presented to operator with pre-filled fields.

Step 2: APPROVE
  - Human reviews each candidate:
    * Confirms URL is correct and reachable.
    * Sets trust_tier and priority.
    * Configures parse_rules (CSS selectors for html_diff, or accepts defaults).
    * Enables/disables.
  - Source saved to registry.

Step 3: MONITOR HEALTH
  - Scheduler fetches each source on its poll_frequency.
  - Health check logic:
    * If 3 consecutive fetches return HTTP errors → mark "degraded".
    * If 7 days with zero new items on a normally-active source → mark "degraded".
    * If 30 days degraded with no recovery → mark "dead", alert operator.
  - Weekly health report emailed to operator.
```

---

## 4) INGESTION + PIPELINE ARCHITECTURE

### 4.1 Six Stages

```
A) Source Registry
   ↓ (provides source configs)
B) Ingestion Connectors
   ↓ (raw items)
C) Normalize + Dedupe
   ↓ (canonical items)
D) Entity Resolution
   ↓ (tagged items)
E) Ranking + Impact Scoring
   ↓ (scored items)
F) Grounded Summarization
   ↓ (digest-ready items)
```

### 4.2 Data Flow Diagram (ASCII)

```
 ┌──────────────────────────────────────────────────────────────────────┐
 │                        SOURCE REGISTRY (Postgres)                   │
 │  [openai/changelog] [anthropic/status] [HN/show] [GH/trending] ... │
 └──────────────┬───────────────────────────────────────────────────────┘
                │ poll configs
                ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │                     INGESTION WORKERS (per connector type)          │
 │                                                                     │
 │  ┌──────────┐ ┌───────────┐ ┌────────────┐ ┌──────────┐ ┌────────┐│
 │  │ RSS/Atom │ │ HTML Diff │ │ GH Releases│ │ API Poll │ │Social  ││
 │  │ Fetcher  │ │ Snapshotter│ │ Fetcher   │ │ (HN/PH) │ │(Reddit)││
 │  └────┬─────┘ └─────┬─────┘ └─────┬──────┘ └────┬─────┘ └───┬────┘│
 └───────┼─────────────┼─────────────┼──────────────┼───────────┼─────┘
         │             │             │              │           │
         ▼             ▼             ▼              ▼           ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │                     RAW ITEM STORE (Postgres + S3)                  │
 │          raw_items table + S3 bucket for HTML snapshots             │
 └──────────────────────────┬───────────────────────────────────────────┘
                            │
                            ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │                  NORMALIZE + DEDUPE WORKER                          │
 │  1. Extract fields → canonical schema                               │
 │  2. Hard dedup (URL + content hash)                                 │
 │  3. Soft dedup (title similarity > 0.85 → cluster)                  │
 │  4. Store as UpdateEvent                                            │
 └──────────────────────────┬───────────────────────────────────────────┘
                            │
                            ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │                  ENTITY RESOLUTION WORKER                           │
 │  1. Rule-based: source_id → company_slug + product_line (from reg.) │
 │  2. Keyword matching: known product names in title/body             │
 │  3. LLM fallback: classify ambiguous items                          │
 │  → Tags each UpdateEvent with company, product, categories[]        │
 └──────────────────────────┬───────────────────────────────────────────┘
                            │
                            ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │                  RANKING + IMPACT SCORING WORKER                    │
 │  Computes ImpactScore per UpdateEvent (see Section 6)               │
 │  Assigns severity: HIGH / MEDIUM / LOW                              │
 │  Flags breaking_change boolean                                      │
 └──────────────────────────┬───────────────────────────────────────────┘
                            │
                            ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │                  GROUNDED SUMMARIZATION WORKER                      │
 │  LLM call per cluster (see Section 7)                               │
 │  Outputs: what_changed[], why_it_matters, citations[], confidence   │
 │  Stores result in UpdateEvent.summary                               │
 └──────────────────────────┬───────────────────────────────────────────┘
                            │
                            ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │                  DIGEST GENERATOR (daily cron)                      │
 │  08:00 ART: query scored events → allocate sections → render →     │
 │  store Digest → send email + publish web page                       │
 └──────────────────────────────────────────────────────────────────────┘
```

### 4.3 Component List

| Component | Type | Responsibility |
|-----------|------|---------------|
| **Source Registry Service** | Postgres table + admin API/UI | CRUD for sources; health tracking. |
| **Scheduler** | Cron / task queue (e.g., Celery, BullMQ, or simple pg-cron) | Enqueues fetch jobs per source at `poll_frequency`. |
| **RSS Connector** | Worker | Fetches RSS/Atom feeds, extracts entries. |
| **HTML Diff Connector** | Worker | Fetches page, diffs against last snapshot, extracts changes. |
| **GitHub Releases Connector** | Worker | Uses GitHub API (or RSS alt) to get releases. |
| **API Poll Connector** | Worker | Hits JSON APIs (HN Algolia, PH API). |
| **Social Connector** | Worker | Reddit RSS, optional X/Twitter search (API costs). |
| **Normalize+Dedupe Worker** | Worker | Canonical schema conversion, hard + soft dedup. |
| **Entity Resolution Worker** | Worker | Maps items to company/product/categories. |
| **Ranking Worker** | Worker | Computes ImpactScore, assigns severity. |
| **Summarization Worker** | Worker | LLM-powered grounded summaries. |
| **Digest Generator** | Scheduled job (08:00 ART daily) | Assembles and delivers digest. |
| **Email Sender** | Service | Sends HTML email via transactional provider (e.g., Resend, SES). |
| **Web Archive** | Static site / simple server | Hosts past digests as web pages. |
| **Health Monitor** | Scheduled job (hourly) | Checks source health, alerts on degradation. |

### 4.4 Storage Choices

| Store | Use | Notes |
|-------|-----|-------|
| **PostgreSQL 16+** | All structured data (sources, raw_items, events, clusters, digests, users, feedback). | Single database for MVP. Add read replica if needed. |
| **pgvector extension** | Semantic similarity for soft dedup + search (Phase 2). | Avoids separate vector DB. |
| **S3-compatible object store** | Raw HTML snapshots, full API responses, email templates. | Cheap, durable. MinIO for local dev. |
| **Redis (optional)** | Task queue backend, rate-limit counters, caching. | Can use Postgres-based queue (e.g., pgmq) to avoid extra infra. |

### 4.5 Operational Notes

| Concern | Approach |
|---------|----------|
| **Rate limiting** | Per-source rate limit config. GitHub: 5,000 req/hr with token. Reddit: respect `Retry-After`. HN Algolia: 10,000 req/hr. Use exponential backoff. |
| **Caching** | Store `ETag` / `Last-Modified` per source; send conditional requests. Cache raw responses in S3 with TTL metadata. |
| **Retries** | 3 retries with exponential backoff (1s, 4s, 16s). After 3 failures, mark fetch as failed, continue to next source. |
| **Monitoring** | Track: fetch success rate, items/day/source, pipeline latency (ingest→digest), LLM cost/call, email delivery rate. Alert on: source health degradation, zero items in 24h from critical source, digest generation failure. |
| **Cost control** | LLM summarization is the main variable cost. Batch items into clusters before summarizing. Cache summaries. Target < $5/day LLM cost for MVP. |
| **Idempotency** | Every raw_item has a `content_hash`. Re-fetching the same content is a no-op. Digest generation is idempotent (same inputs → same digest_id). |

---

## 5) DATA MODEL (Schemas)

### 5.1 Tables

#### `sources`
```
sources
────────────────────────────────────────
source_id           UUID            PK, DEFAULT gen_random_uuid()
company_slug        TEXT            NOT NULL
company_name        TEXT            NOT NULL
product_line        TEXT            NULLABLE
source_name         TEXT            NOT NULL
source_url          TEXT            NOT NULL UNIQUE
fetch_method        TEXT            NOT NULL  -- rss|html_diff|github_releases|api_poll|social_api|manual
poll_frequency_min  INT             NOT NULL DEFAULT 60
trust_tier          SMALLINT        NOT NULL CHECK (1..4)
priority            TEXT            NOT NULL DEFAULT 'normal'  -- critical|high|normal|low
parse_rules         JSONB           DEFAULT '{}'
health_status       TEXT            NOT NULL DEFAULT 'healthy'  -- healthy|degraded|dead
last_fetched_at     TIMESTAMPTZ
last_item_at        TIMESTAMPTZ
enabled             BOOLEAN         NOT NULL DEFAULT true
notes               TEXT
created_at          TIMESTAMPTZ     NOT NULL DEFAULT now()
updated_at          TIMESTAMPTZ     NOT NULL DEFAULT now()

INDEXES:
  idx_sources_company     ON (company_slug)
  idx_sources_enabled     ON (enabled, health_status)
  idx_sources_next_fetch  ON (enabled, last_fetched_at, poll_frequency_min)
```

#### `raw_items`
```
raw_items
────────────────────────────────────────
raw_item_id         UUID            PK
source_id           UUID            FK → sources
external_id         TEXT            -- source-specific ID (RSS guid, GH release id, etc.)
url                 TEXT            NOT NULL
title               TEXT
content_text        TEXT            -- extracted plain text
content_html        TEXT            -- original HTML (or null if RSS)
content_hash        TEXT            NOT NULL  -- SHA-256 of normalized content
published_at        TIMESTAMPTZ     -- original publish timestamp
fetched_at          TIMESTAMPTZ     NOT NULL DEFAULT now()
snapshot_s3_key     TEXT            -- S3 key for full snapshot (html_diff sources)
metadata            JSONB           DEFAULT '{}'  -- extra fields (stars, upvotes, etc.)
is_duplicate        BOOLEAN         NOT NULL DEFAULT false

INDEXES:
  idx_raw_items_source    ON (source_id, fetched_at DESC)
  idx_raw_items_hash      ON (content_hash)     -- for hard dedup
  idx_raw_items_url       ON (url)
  idx_raw_items_published ON (published_at DESC)

UNIQUE:
  uq_raw_items_source_ext ON (source_id, external_id)

RETENTION:
  raw content_html: 90 days, then nullify (keep metadata).
  S3 snapshots: 90 days, then archive to Glacier/delete.
```

#### `snapshots` (for html_diff sources)
```
snapshots
────────────────────────────────────────
snapshot_id         UUID            PK
source_id           UUID            FK → sources
s3_key              TEXT            NOT NULL
content_hash        TEXT            NOT NULL
fetched_at          TIMESTAMPTZ     NOT NULL DEFAULT now()
diff_from_prev      TEXT            -- text diff vs previous snapshot (nullable)
has_changes         BOOLEAN         NOT NULL DEFAULT false

INDEXES:
  idx_snapshots_source    ON (source_id, fetched_at DESC)

RETENTION:
  Keep last 30 snapshots per source. Archive older to S3 Glacier.
```

#### `update_events`
```
update_events
────────────────────────────────────────
event_id            UUID            PK
cluster_id          UUID            FK → clusters (nullable, set after clustering)
source_id           UUID            FK → sources
raw_item_id         UUID            FK → raw_items
company_slug        TEXT            NOT NULL
company_name        TEXT            NOT NULL
product_line        TEXT
title               TEXT            NOT NULL
categories          TEXT[]          NOT NULL  -- from 30-category taxonomy
trust_tier          SMALLINT        NOT NULL
severity            TEXT            NOT NULL  -- HIGH|MEDIUM|LOW
breaking_change     BOOLEAN         NOT NULL DEFAULT false
impact_score        FLOAT           NOT NULL DEFAULT 0
confidence          TEXT            NOT NULL DEFAULT 'confirmed'  -- confirmed|likely|unverified
what_changed        JSONB           -- [{text, citation_url}]
why_it_matters      TEXT
action_items        TEXT[]
citations           TEXT[]          NOT NULL
evidence_snippets   TEXT[]
summary_short       TEXT            -- 1-2 sentences
summary_medium      TEXT            -- 1 paragraph
published_at        TIMESTAMPTZ
created_at          TIMESTAMPTZ     NOT NULL DEFAULT now()
digest_id           UUID            FK → digests (nullable, set when included in digest)
digest_section      TEXT            -- which section it was placed in

INDEXES:
  idx_events_company      ON (company_slug, created_at DESC)
  idx_events_score        ON (impact_score DESC)
  idx_events_created      ON (created_at DESC)
  idx_events_digest       ON (digest_id)
  idx_events_categories   ON (categories) USING GIN
  idx_events_severity     ON (severity, created_at DESC)

RETENTION:
  Keep indefinitely (core data). Summarize older events after 1 year.
```

#### `clusters`
```
clusters
────────────────────────────────────────
cluster_id          UUID            PK
canonical_title     TEXT            NOT NULL
company_slug        TEXT
event_count         INT             NOT NULL DEFAULT 1
first_seen_at       TIMESTAMPTZ     NOT NULL
last_seen_at        TIMESTAMPTZ     NOT NULL
merged_summary      TEXT
created_at          TIMESTAMPTZ     NOT NULL DEFAULT now()

INDEXES:
  idx_clusters_company    ON (company_slug, last_seen_at DESC)
```

#### `digests`
```
digests
────────────────────────────────────────
digest_id           UUID            PK
digest_date         DATE            NOT NULL UNIQUE
overview_text       TEXT            -- generated 1-paragraph overview
sections            JSONB           NOT NULL  -- ordered list of {section_name, event_ids[]}
event_count         INT             NOT NULL
generated_at        TIMESTAMPTZ     NOT NULL
delivered_at        TIMESTAMPTZ
delivery_channels   TEXT[]          -- ['email', 'web']
html_s3_key         TEXT            -- rendered HTML stored in S3
web_url             TEXT            -- public archive URL
created_at          TIMESTAMPTZ     NOT NULL DEFAULT now()

INDEXES:
  idx_digests_date        ON (digest_date DESC)
```

#### `user_preferences` (Phase 2+)
```
user_preferences
────────────────────────────────────────
user_id             UUID            PK
email               TEXT            NOT NULL UNIQUE
display_name        TEXT
followed_companies  TEXT[]          DEFAULT '{}'  -- empty = all
followed_categories TEXT[]          DEFAULT '{}'  -- empty = all
severity_filter     TEXT            NOT NULL DEFAULT 'all'
breaking_only       BOOLEAN         NOT NULL DEFAULT false
frequency           TEXT            NOT NULL DEFAULT 'daily'
delivery_time       TIME            NOT NULL DEFAULT '08:00'
timezone            TEXT            NOT NULL DEFAULT 'America/Argentina/Cordoba'
delivery_channel    TEXT            NOT NULL DEFAULT 'email'
locale              TEXT            NOT NULL DEFAULT 'en'
created_at          TIMESTAMPTZ     NOT NULL DEFAULT now()
updated_at          TIMESTAMPTZ     NOT NULL DEFAULT now()
```

#### `feedback` (Phase 2+)
```
feedback
────────────────────────────────────────
feedback_id         UUID            PK
user_id             UUID            FK → user_preferences (nullable for anonymous)
event_id            UUID            FK → update_events
digest_id           UUID            FK → digests
feedback_type       TEXT            NOT NULL  -- thumbs_up|thumbs_down|mute_company|mute_category
comment             TEXT
created_at          TIMESTAMPTZ     NOT NULL DEFAULT now()

INDEXES:
  idx_feedback_event      ON (event_id)
  idx_feedback_user       ON (user_id, created_at DESC)
```

---

## 6) RANKING + SEVERITY RUBRIC

### 6.1 Severity Levels

| Severity | Criteria | Examples |
|----------|----------|---------|
| **HIGH** | Breaking change, major pricing increase (>20%), security incident, new foundation model, major outage (>30 min on critical provider), deprecation with deadline <90 days. | "OpenAI removes GPT-3.5-turbo endpoint in 60 days"; "Anthropic raises API prices 50%"; "Google releases Gemini 3" |
| **MEDIUM** | Non-breaking API change, new feature/capability, moderate pricing change (5-20%), model quality upgrade, new SDK major version, new modality support, rate limit change. | "Anthropic adds PDF support to Claude API"; "Mistral releases new embedding model"; "AWS Bedrock adds Llama 3 support" |
| **LOW** | Minor SDK patch, documentation update, dashboard UI change, blog post without product change, community discussion, minor bug fix, informational announcement. | "OpenAI SDK v1.23.1 patch release"; "Cohere updates Python quickstart docs"; "Hugging Face blog post on training techniques" |

### 6.2 Severity Rules by Category

| Category | HIGH when... | MEDIUM when... | LOW when... |
|----------|-------------|---------------|-------------|
| 1. New foundation model release | Always HIGH | — | — |
| 2. Model upgrade | Flagship model, major capability jump | Quality/speed improvement | Minor variant |
| 3. New modality | First for that provider | Addition to existing model | Beta/preview |
| 4. Fine-tuning updates | API change or pricing change for fine-tuning | New fine-tuning feature | Docs update |
| 5. Inference & serving | >50% speed improvement or breaking runtime change | Notable speed/cost improvement | Minor optimization |
| 6. Pricing changes | >20% increase or new billing model | 5-20% change either direction | <5% or free tier only |
| 7. Rate limits/quotas | Reduction in limits | New tier or increase | Docs clarification |
| 8. Deprecations/breaking | Deadline <90 days or no migration path | Deadline 90-365 days, clear migration | >1 year or trivial |
| 9. SDK releases | Major version with breaking changes | Minor version with features | Patch/bugfix |
| 10. API changes | Breaking endpoint/schema change | New endpoint or parameter | Docs/example update |
| 11-14. Framework/tools | Major new capability | New feature | Bugfix/patch |
| 15. Evals/benchmarks | New official benchmark from major lab | New eval tool/dataset | Blog/analysis only |
| 16. Datasets | >1M samples, major licensing change | Notable new dataset | Minor update |
| 17. Safety/alignment | Policy-affecting feature | New safety tool | Research paper |
| 18. Policy/compliance | Regulatory action, mandatory change | New compliance feature | Advisory |
| 19. Security incidents | Active exploit, data breach | Vulnerability disclosed + patched | Advisory, no exploit |
| 20. Privacy changes | ToS change affecting data usage | New privacy feature | Docs clarification |
| 21. Open-source releases | Frontier-competitive model | Notable tool/library | Minor project |
| 22-23. Dev/Enterprise features | Platform-wide change | New feature | UI tweak |
| 24-25. Edge/Hardware | Major product launch | Driver/SDK update | Announcement |
| 26-27. Infra/LLMOps | Major platform change | New tool/feature | Patch |
| 28. App launches | Major consumer AI app | Notable app | Minor update |
| 29. Funding/M&A | >$500M round or major acquisition | Notable funding/partnership | Small round |
| 30. Reliability/outages | >30 min outage on critical provider | <30 min or partial outage | Maintenance window |

### 6.3 ImpactScore Formula

```
ImpactScore = w_T * Trust
            + w_S * Severity
            + w_U * UserMatch
            + w_R * Recency
            + w_B * Breadth
            + w_N * Novelty
            - w_D * SpamDupePenalty
```

**Default weights (sum to ~1.0 meaningful range):**

| Term | Weight | Range | Computation |
|------|--------|-------|-------------|
| **Trust** | w_T = 0.20 | 0–1 | Tier 1 = 1.0, Tier 2 = 0.7, Tier 3 = 0.4, Tier 4 = 0.2 |
| **Severity** | w_S = 0.25 | 0–1 | HIGH = 1.0, MEDIUM = 0.5, LOW = 0.15 |
| **UserMatch** | w_U = 0.15 | 0–1 | 1.0 if user follows company AND category; 0.5 if one matches; 0.3 default (Phase 1: always 0.5). |
| **Recency** | w_R = 0.15 | 0–1 | `exp(-lambda * hours_old)` where lambda = 0.03. Items <1h old = ~1.0; 24h old = ~0.49; 48h old = ~0.24. |
| **Breadth** | w_B = 0.10 | 0–1 | Number of independent sources reporting, normalized: `min(source_count / 3, 1.0)`. |
| **Novelty** | w_N = 0.10 | 0–1 | 1.0 if no similar event in last 7 days (by cluster); 0.3 if related cluster exists; 0.0 if exact duplicate. |
| **SpamDupePenalty** | w_D = 0.05 | 0–1 | 1.0 if flagged as spam or near-duplicate already in digest; 0.0 otherwise. |

**Final score range:** 0.0 – 1.0 (approximately).

**"Why you're seeing this" generation:**

```pseudocode
function explain_score(event):
    reasons = []
    if event.severity == "HIGH":
        reasons.append("High severity: " + severity_reason(event))
    if event.trust_tier == 1:
        reasons.append("Confirmed by first-party source")
    if event.breaking_change:
        reasons.append("Breaking change flagged")
    if user_follows(event.company):
        reasons.append("You follow " + event.company_name)
    if event.breadth_score > 0.6:
        reasons.append("Reported by multiple sources")
    if event.novelty_score > 0.8:
        reasons.append("First time this is reported")
    return "; ".join(reasons[:3])  // show top 3
```

---

## 7) SUMMARIZATION / "AI NEWSROOM" PROMPTING STRATEGY

### 7.1 Extraction Schema

The LLM summarizer must output the following JSON for each item/cluster:

```json
{
  "title": "string — short action-oriented headline, <=100 chars",
  "what_changed": [
    {
      "fact": "string — one factual statement",
      "citation_url": "string — URL backing this fact"
    }
  ],
  "why_it_matters": "string — 1-2 sentences, interpretation/analysis",
  "action_items": ["string — optional concrete next steps"],
  "citations": ["url1", "url2"],
  "evidence_snippets": ["exact quote or data point from source"],
  "tags": {
    "categories": ["category name from taxonomy"],
    "company": "string",
    "product_line": "string or null"
  },
  "breaking_change": false,
  "confidence": "confirmed | likely | unverified",
  "severity_suggestion": "HIGH | MEDIUM | LOW"
}
```

### 7.2 Tier-Based Summarization Rules

| Rule | Description |
|------|-------------|
| **R1: Tier 1 required for "Released/Updated"** | If the only evidence is Tier 2/3/4, the summary must say "reported" or "rumored," never "released" or "updated." |
| **R2: Separate facts from interpretation** | `what_changed` contains only facts extractable from sources. `why_it_matters` is labeled as analysis. |
| **R3: No invented facts** | Every `what_changed` bullet must have a `citation_url`. If a fact cannot be cited, it must be dropped. |
| **R4: Evidence snippets** | Include at least one direct quote or data point from the source for verifiability. |
| **R5: Confidence labeling** | `confirmed` = Tier 1 source. `likely` = Tier 2 + consistent signals. `unverified` = Tier 3/4 only. |
| **R6: No speculation about future** | Do not predict what a company "will likely do next." Stick to what happened. |
| **R7: Tier 4 items go to Radar only** | Tier 4 (social/community) items are never presented as confirmed updates; they appear in Community Radar or "Everything else" with appropriate caveats. |

### 7.3 Sample Summarization Prompt Template

```
SYSTEM:
You are a factual AI news summarizer. Your job is to produce structured
summaries of AI industry updates. You MUST follow these rules:

1. NEVER invent facts. Every claim in "what_changed" MUST have a citation URL.
2. Separate facts (what_changed) from interpretation (why_it_matters).
3. If the source is first-party (Tier 1), you may say "released" or "updated."
   If only Tier 2/3/4 sources exist, say "reported" or "according to [source]."
4. Include at least one verbatim evidence snippet from the source material.
5. Tag with categories from this taxonomy: [list of 30 categories].
6. Flag breaking_change = true only if the change removes existing functionality
   or requires developer action to avoid breakage.
7. Set confidence: "confirmed" if Tier 1, "likely" if Tier 2, "unverified" if Tier 3/4.
8. Keep title under 100 characters, action-oriented.
9. Keep why_it_matters to 1-2 sentences max.

OUTPUT FORMAT: JSON matching this schema exactly:
{schema from 7.1}

USER:
Summarize the following source material about an AI industry update.

Source trust tier: {tier}
Source company: {company}
Source URL: {url}
Published: {date}

--- SOURCE CONTENT START ---
{content}
--- SOURCE CONTENT END ---

Additional context from other sources (if any):
{context_items}

Produce the JSON summary.
```

### 7.4 Sample Output JSON

```json
{
  "title": "Anthropic releases Claude 4.5 Haiku with 2x speed improvement",
  "what_changed": [
    {
      "fact": "Anthropic released Claude 4.5 Haiku, a faster variant of Claude 4.5 Sonnet optimized for low-latency use cases.",
      "citation_url": "https://docs.anthropic.com/en/docs/about-claude/changelog"
    },
    {
      "fact": "Claude 4.5 Haiku achieves 2x faster time-to-first-token compared to Claude 3.5 Haiku, with comparable quality on standard benchmarks.",
      "citation_url": "https://docs.anthropic.com/en/docs/about-claude/changelog"
    },
    {
      "fact": "Pricing set at $0.80/MTok input, $4/MTok output.",
      "citation_url": "https://docs.anthropic.com/en/docs/about-claude/models"
    }
  ],
  "why_it_matters": "Haiku-class models are the workhorses for high-volume, cost-sensitive production workloads. A 2x latency improvement with maintained quality makes Claude more competitive against GPT-4o-mini and Gemini Flash for real-time applications like autocomplete and chatbots.",
  "action_items": [
    "Update model parameter to 'claude-haiku-4-5-20251001' in API calls to use the new model.",
    "Review pricing: input cost increased from $0.25 to $0.80/MTok vs Claude 3.5 Haiku."
  ],
  "citations": [
    "https://docs.anthropic.com/en/docs/about-claude/changelog",
    "https://docs.anthropic.com/en/docs/about-claude/models"
  ],
  "evidence_snippets": [
    "Claude 4.5 Haiku achieves 2x faster time-to-first-token while maintaining comparable quality to Claude 3.5 Haiku across standard benchmarks."
  ],
  "tags": {
    "categories": [
      "New foundation model release",
      "Inference & serving (speed/runtimes)",
      "Pricing & billing changes"
    ],
    "company": "Anthropic",
    "product_line": "API"
  },
  "breaking_change": false,
  "confidence": "confirmed",
  "severity_suggestion": "HIGH"
}
```

---

## 8) DAILY DIGEST GENERATION WORKFLOW

### 8.1 Trigger

Cron fires at **08:00 America/Argentina/Cordoba (UTC-3)** daily.

### 8.2 Steps

```pseudocode
function generate_daily_digest(target_date):
    cutoff_start = target_date - 1 day at 08:00 ART
    cutoff_end   = target_date at 07:59:59 ART

    // 1. Gather events
    events = query update_events
        WHERE created_at BETWEEN cutoff_start AND cutoff_end
        AND digest_id IS NULL   // not yet assigned to a digest
        ORDER BY impact_score DESC

    // 2. Final cluster merge
    //    Re-run soft dedup on today's events to merge late-arriving duplicates
    clusters = merge_clusters(events)
    events = deduplicate_within_clusters(clusters)

    // 3. Allocate into sections
    sections = allocate_sections(events)

    // 4. Generate summaries (if not already generated)
    for event in events where event.summary_short IS NULL:
        event.summary_short = summarize(event, mode="short")
        event.summary_medium = summarize(event, mode="medium")

    // 5. Generate overview paragraph
    overview = generate_overview(sections.top5)

    // 6. Render digest
    digest_html = render_template("digest_email.html", {
        date: target_date,
        overview: overview,
        sections: sections
    })
    digest_web = render_template("digest_web.html", same_data)

    // 7. Store
    digest = INSERT INTO digests (
        digest_date = target_date,
        overview_text = overview,
        sections = sections_json,
        event_count = len(events),
        generated_at = now(),
        html_s3_key = upload_to_s3(digest_html)
    )

    // Mark events as assigned
    UPDATE update_events SET digest_id = digest.digest_id
        WHERE event_id IN (events.ids)

    // 8. Deliver
    send_email(digest_html, subscribers)
    publish_web_page(digest_web, target_date)
    digest.delivered_at = now()

    return digest
```

### 8.3 Section Allocation + Quotas

```pseudocode
function allocate_sections(events):
    sections = {}

    // Top 5: highest impact_score regardless of category
    sections["top5"] = events[:5]
    remaining = events[5:]

    // Developer Changes: categories 8,9,10,11,12
    dev_cats = {"Deprecations/breaking changes", "SDK releases/updates",
                "API changes", "Agents frameworks/orchestration",
                "Tool-use/function calling/integrations"}
    sections["developer"] = filter(remaining, cats in dev_cats)[:8]

    // Models & Capabilities: categories 1,2,3,4,5,14,15,21
    model_cats = {"New foundation model release", "Model upgrade",
                  "New modality", "Fine-tuning/customization updates",
                  "Inference & serving", "Embeddings & reranking",
                  "Evaluation/benchmarks/evals", "Open-source model/tool releases"}
    sections["models"] = filter(remaining, cats in model_cats)[:8]

    // Pricing & Limits: categories 6,7
    sections["pricing"] = filter(remaining, cats in {6,7})[:5]

    // Incidents & Reliability: categories 19,30
    sections["incidents"] = filter(remaining, cats in {19,30})[:5]

    // Community Radar: trust_tier == 4 items from community sources
    sections["radar"] = filter(remaining, trust_tier == 4, has_launch_signal)[:6]

    // Everything Else: all remaining
    sections["everything_else"] = remaining - assigned
    // no cap, but render as compact one-liners

    return sections
```

### 8.4 Cutoff Logic

- An event is eligible for a digest only if `digest_id IS NULL`.
- Events older than 48 hours that were never included are swept into a weekly "missed items" summary (Phase 3).
- If a cluster spans two days (e.g., initial report day 1, confirmation day 2), it appears in the day-2 digest with the merged/updated summary.

### 8.5 Localization Plan

| Phase | Language | Approach |
|-------|----------|----------|
| Phase 1-3 | English only | All summaries generated in English. |
| Phase 4 | Spanish (es-AR) | Post-generation translation pass using LLM. User preference `locale=es` triggers Spanish version. Subject lines, section headers, and UI chrome translated via i18n strings file. Summaries translated per-item with instruction to preserve technical terms. |

---

## 9) COMPLIANCE, LICENSING, AND RISK MANAGEMENT

### 9.1 Content Rights / ToS Compliance

| Principle | Implementation |
|-----------|---------------|
| **Prefer first-party sources** | Tier 1 is always the primary evidence. We link to the original. |
| **Short excerpts only** | Store <=300 characters of quoted text per item. Full content stays on the original site. This is fair use / right to quote in most jurisdictions. |
| **Link out, don't host** | Digest items always link to the original source. We never reproduce full articles. |
| **Respect robots.txt** | HTML diff fetcher checks robots.txt before scraping. If disallowed, mark source as `manual` and require operator to paste content. |
| **API ToS compliance** | GitHub API: comply with rate limits, authenticate with token. Reddit: use official RSS (no scraping). HN: use Algolia API (public, documented). Product Hunt: use official API with key if required. |

### 9.2 News Provider Licensing

| Risk | Mitigation |
|------|-----------|
| Some "free" APIs are developer-only, not for production redistribution. | Phase 1: use only first-party changelogs + public APIs. No licensed news feeds. Phase 3: evaluate licensed providers (e.g., NewsAPI, Aylien, GDELT) with explicit production-use licensing. Budget $200-500/mo. |
| Aggregating headlines from news sites may require licensing. | We do NOT aggregate news headlines. We summarize first-party changelogs. Tier 2 coverage is cited but not reproduced. |

### 9.3 Verification Rule

> **"Released/Updated" requires Tier 1 confirmation.**

- If only Tier 2/3/4 sources report a change, the digest says "Reported: ..." or "According to [source]: ..."
- The `confidence` field enforces this: only `confirmed` items (backed by Tier 1) can use definitive language.
- This rule is enforced in the summarization prompt (Rule R1) and validated post-generation.

### 9.4 Anti-Spam + Abuse Handling for Community Radar

| Threat | Mitigation |
|--------|-----------|
| Self-promotion spam on HN/Reddit | Require minimum signal thresholds: HN >=10 points, Reddit >=20 upvotes. Account age check where API allows. |
| Fake GitHub stars | Use star velocity (stars/hour) normalized against repo age. Flag repos with >100 stars but <5 commits or <2 contributors. |
| Malicious repos/tools | Do NOT auto-execute or deep-link to binaries. Link to repo page only. Add disclaimer: "Community-sourced, not verified." |
| Duplicate/bot launches on PH | Cross-reference with existing Source Registry entries. Flag if product domain matches known company. |
| Quality floor | Require at least 2 of: README with description, working demo/link, open-source license, >1 commit author. |

### 9.5 Privacy / Security

| Area | Approach |
|------|----------|
| User emails (Phase 2+) | Store hashed, encrypt at rest. Comply with CAN-SPAM / GDPR (unsubscribe link in every email). |
| API keys for sources | Store in secrets manager (e.g., environment variables / Vault). Never in source code or database. |
| LLM API calls | Do not send user PII to LLM. Only send source content for summarization. |
| Web archive | Public by default. No user-specific data on public pages. |

---

## 10) MVP ROADMAP

### Phase 1: Reliable Daily Digest (Weeks 1-4)

**Deliverables:**
- Source Registry with 20-40 Tier 1 sources (seeded from starter list).
- Ingestion pipeline: RSS + HTML diff + GitHub Releases connectors.
- Normalize + hard dedup.
- Rule-based entity resolution (source_id → company).
- Rule-based severity assignment (no ML yet).
- LLM-powered grounded summarization (single prompt, JSON output).
- Daily digest generation at 08:00 ART.
- Email delivery via transactional provider (Resend or SES).
- Static web archive of past digests.
- Manual review step before send (operator approves digest).

**Risks:**
- HTML diff parsing may be fragile for some changelog pages. *Mitigation: start with RSS-first sources; add html_diff incrementally.*
- LLM summarization may hallucinate. *Mitigation: citation-required prompt + human review in Phase 1.*
- Low subscriber count makes feedback sparse. *Mitigation: seed with team + 10-20 beta testers.*

**Exit Criteria:**
- [x] 20+ sources ingested daily with >95% fetch success rate.
- [x] Daily digest sent on time for 14 consecutive days.
- [x] Zero hallucinated facts in human-reviewed digests for 7 consecutive days.
- [x] At least 10 subscribers receiving and opening emails.

---

### Phase 2: Taxonomy + Ranking + User Prefs (Weeks 5-10)

**Deliverables:**
- LLM-powered taxonomy classifier (map events to 30 categories).
- Soft dedup with text similarity (TF-IDF or pgvector embeddings).
- ImpactScore formula implementation (all 7 terms).
- Community Radar: HN + GitHub trending + Product Hunt ingestion.
- Launch Card format for Radar items.
- User preferences: follow companies/categories, severity filter, frequency.
- Feedback mechanism: thumbs up/down, mute.
- Remove mandatory human review (make optional).

**Risks:**
- Taxonomy classifier accuracy may be <90% initially. *Mitigation: human-in-the-loop corrections feed back into few-shot examples.*
- Community Radar may surface low-quality items. *Mitigation: quality floor rules (Section 9.4).*

**Exit Criteria:**
- [x] Taxonomy classification accuracy >90% (measured on 100-item sample).
- [x] ImpactScore ranking correlates with human judgment (Kendall tau >0.6).
- [x] Community Radar surfaces 3-6 items/day with <20% "irrelevant" feedback.
- [x] 5+ users have configured personalization preferences.

---

### Phase 3: Coverage Expansion + Discovery (Weeks 11-18)

**Deliverables:**
- Expand source registry to 80-120 sources.
- Add Tier 2 sources (tech news outlets) with proper attribution.
- Evaluate and optionally integrate licensed news/dataset provider.
- Reddit connector (r/MachineLearning, r/LocalLLaMA, r/artificial).
- GitHub new repo discovery: scan for AI/ML repos with star velocity.
- Broader entity resolution: ML-assisted mapping for unknown companies.
- Weekly summary digest option.
- "Missed items" catch-up for events that fell outside the 24h window.

**Risks:**
- Tier 2 sources increase noise and licensing complexity. *Mitigation: strict Tier 2 rules (discovery only, never sole proof).*
- GitHub scanning at scale may hit rate limits. *Mitigation: use authenticated API, prioritize trending endpoint, batch queries.*

**Exit Criteria:**
- [x] 80+ sources ingested daily.
- [x] Tier 2 sources properly attributed (0 instances of Tier 2 presented as confirmed).
- [x] GitHub discovery surfaces 5+ new repos/week with genuine signal.

---

### Phase 4: Personalization + Notifications + Localization (Weeks 19-26)

**Deliverables:**
- Real-time alerts for HIGH severity / breaking changes (email or Slack/Discord).
- Slack and Discord delivery channels.
- RSS feed output.
- Spanish (es-AR) localization.
- Timeline view: browsable history of updates per company/product.
- Improved recommendation: learn from feedback to adjust ImpactScore weights per user.
- Public API for digest data (read-only).

**Risks:**
- Real-time alerts require near-real-time pipeline (<15 min latency). *Mitigation: prioritize critical sources with 15-min poll frequency.*
- Translation quality for technical content. *Mitigation: preserve technical terms, human review of first 10 translated digests.*

**Exit Criteria:**
- [x] Alert latency <15 min for HIGH severity events.
- [x] Slack/Discord delivery working for 5+ users.
- [x] Spanish digest quality rated "good" by 3+ native speakers.

---

## 11) SUCCESS METRICS (KPIs)

| # | KPI | Definition | Target (Phase 1) | Target (Phase 3+) |
|---|-----|-----------|------------------|-------------------|
| 1 | **Coverage** | % of monitored sources successfully ingested each day | >95% | >98% |
| 2 | **Freshness** | Median time from source publish → digest inclusion | <18 hours | <12 hours |
| 3 | **Signal (Engagement)** | Unique clicks or opens per digest / total subscribers | >40% open rate | >50% open rate |
| 4 | **Relevance** | Thumbs-up / (thumbs-up + thumbs-down) ratio per digest | N/A (Phase 1) | >80% |
| 5 | **Trust** | % of "Released/Updated" items backed by Tier 1 source | 100% | 100% (hard rule) |
| 6 | **Accuracy** | % of digest items with zero factual errors (human-audited weekly sample of 20 items) | >95% | >98% |
| 7 | **Completeness** | % of "notable AI events" (defined by weekly retrospective) captured in digest | >80% | >90% |
| 8 | **Subscriber Growth** | Net new subscribers per week | +5/week | +25/week |
| 9 | **Mute Rate** | % of users who mute a company or category after seeing it | <10% | <5% |
| 10 | **Pipeline Reliability** | % of days digest is generated and delivered on time (within 15 min of scheduled time) | >95% | >99% |

---

## 12) DAY-1 CHECKLIST

```
DAY-1 CHECKLIST — Start Tomorrow
═══════════════════════════════════════════

[ ] 1. TAXONOMY + SEVERITY RUBRIC
      - Copy the 30-category taxonomy into a config file / spreadsheet.
      - Copy the severity rules table (Section 6.2) into the same doc.
      - This is your classification reference for everything downstream.

[ ] 2. BUILD SOURCE REGISTRY SPREADSHEET
      - Copy the CSV from Section 3.3 into Google Sheets or Notion.
      - Verify each URL is reachable (quick manual check).
      - For each source, note: does it have RSS? GitHub releases?
        Or does it need HTML diffing?
      - Prioritize: pick 20 sources that have RSS or GitHub releases
        (easiest to ingest).

[ ] 3. CHOOSE MVP DELIVERY CHANNEL
      - Decision: email (recommended).
      - Sign up for transactional email provider (Resend free tier
        or AWS SES sandbox).
      - Create a simple mailing list (even a spreadsheet of emails
        for Phase 1).

[ ] 4. SEED INITIAL COMPANY LIST
      - Finalize the ~30 companies to track.
      - For each, identify: company_slug, company_name, product_lines.
      - Suggested starter set:
        OpenAI, Anthropic, Google (Gemini/Vertex), Meta (Llama),
        Mistral, Cohere, AWS (Bedrock), Microsoft (Azure OpenAI),
        Hugging Face, LangChain, LlamaIndex, Vercel (AI SDK),
        Stability AI, Replicate, Together AI, Groq, Perplexity,
        Fireworks AI, Anyscale, Modal, Weights & Biases, Databricks,
        Snowflake (Cortex), xAI, DeepSeek, Ollama, CrewAI,
        AutoGen (Microsoft), Pinecone, Weaviate.

[ ] 5. DEFINE DIGEST FORMAT
      - Create an HTML email template with the 7 sections.
      - Keep it stable — changing format confuses readers.
      - Use the structure from Section 2.6.
      - Test rendering in Gmail, Outlook, Apple Mail.

[ ] 6. SET UP MINIMAL INFRA
      - Provision PostgreSQL database (local or managed).
      - Create the sources and raw_items tables (Section 5).
      - Set up S3 bucket (or local MinIO) for snapshots.
      - Write first connector: RSS fetcher (simplest).

[ ] 7. WRITE FIRST SUMMARIZATION PROMPT
      - Adapt the template from Section 7.3.
      - Test with 5 real changelog entries.
      - Verify: no hallucinations, citations present,
        what_changed vs why_it_matters separated.

[ ] 8. MANUAL DRY RUN
      - Manually gather today's AI updates from your 20 sources.
      - Classify each by category and severity.
      - Write summaries using the prompt.
      - Assemble into digest format.
      - Send to yourself and 2-3 beta testers.
      - This is your ground truth for automating.

[ ] 9. SET UP MONITORING
      - Simple health check: did the pipeline run today?
      - Log: items ingested, items summarized, digest generated.
      - Alert (email to self) if daily job fails.

[ ] 10. RECRUIT 10 BETA TESTERS
       - AI engineers you know personally.
       - Ask for explicit feedback: "Was anything wrong?
         Was anything missing? What would you change?"
```

---

## APPENDIX A: EXAMPLE DIGEST

```
=====================================================================
AI DAILY DIGEST — February 9, 2026
=====================================================================

Today: Google ships Gemini 2.5 with native audio output. Anthropic
deprecates Claude 3.0 models with 60-day deadline. Two promising
open-source launches caught the community's attention.

---------------------------------------------------------------------
[1] TOP 5 — HIGH IMPACT
---------------------------------------------------------------------

1. Google releases Gemini 2.5 Pro with native audio generation
   [HIGH] [New foundation model release] [New modality]
   Company: Google (Gemini API)
   What changed:
   - Google released Gemini 2.5 Pro, a multimodal model with native
     audio output (text-to-speech and sound effects). [1]
   - Available via Gemini API and Vertex AI. Context window: 2M tokens. [1]
   - Pricing: $1.25/MTok input, $5.00/MTok output (same tier as 2.0 Pro). [2]
   Why it matters: Native audio generation in a frontier model removes
   the need for separate TTS pipelines, enabling lower-latency voice
   applications and reducing integration complexity for developers.
   Action items: Model ID "gemini-2.5-pro" is live. Update your model
   parameter to access new capabilities. Audio output requires
   response_modalities=["AUDIO"] in the API request.
   Sources: [1] ai.google.dev/changelog [2] ai.google.dev/pricing
   Confidence: confirmed | Tier 1

2. Anthropic deprecates Claude 3.0 Opus, Sonnet, Haiku — 60-day deadline
   [HIGH] [Deprecations/breaking changes]
   Company: Anthropic (API)
   What changed:
   - Anthropic announced end-of-life for all Claude 3.0 models
     (Opus, Sonnet, Haiku) effective April 10, 2026. [1]
   - Migration guide published recommending Claude 3.5 Sonnet as
     replacement for most use cases. [1]
   - After April 10, API calls to claude-3-* model IDs will return
     400 errors. [1]
   Why it matters: Teams still using Claude 3.0 models in production
   have 60 days to migrate. Claude 3.5 Sonnet offers better quality
   at lower cost, but output behavior differences may require
   prompt adjustments and regression testing.
   Action items: Audit all API calls for claude-3-opus, claude-3-sonnet,
   claude-3-haiku model IDs. Test with claude-3-5-sonnet-20241022
   and update before April 10.
   Sources: [1] docs.anthropic.com/en/docs/about-claude/changelog
   Confidence: confirmed | Tier 1

   ... (items 3-5 omitted for brevity)

---------------------------------------------------------------------
[2] DEVELOPER CHANGES
---------------------------------------------------------------------

1. OpenAI Python SDK v2.8.0: adds streaming support for Responses API
   [MEDIUM] [SDK releases/updates]
   Company: OpenAI (API)
   What changed:
   - openai-python v2.8.0 released with native streaming support
     for the new Responses API endpoint. [1]
   - New `client.responses.create(stream=True)` method. [1]
   Why it matters: Developers using the Responses API can now stream
   partial results, improving UX for chat applications.
   Sources: [1] github.com/openai/openai-python/releases/tag/v2.8.0
   Confidence: confirmed | Tier 1

   ... (more developer items)

---------------------------------------------------------------------
[6] COMMUNITY RADAR
---------------------------------------------------------------------

  ┌─────────────────────────────────────────────────┐
  │ promptlab — visual prompt engineering workbench │
  │                                                 │
  │ What it is: Open-source desktop app for         │
  │ building, testing, and versioning LLM prompts   │
  │ with side-by-side model comparison.             │
  │                                                 │
  │ Why people like it: "Finally a prompt tool that │
  │ doesn't require a cloud account. The diff view  │
  │ between prompt versions is killer." — HN user   │
  │                                                 │
  │ Try it: github.com/user/promptlab               │
  │ Signals: 342 stars (launched 18h ago)            │
  │          94th percentile star velocity (daily)   │
  │          HN: 187 points, 43 comments             │
  └─────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────┐
  │ embedrank — fast hybrid search library          │
  │                                                 │
  │ What it is: Python library combining BM25 +     │
  │ embedding reranking in a single API. Runs       │
  │ locally, no external dependencies.              │
  │                                                 │
  │ Why people like it: "Replaced my Elasticsearch  │
  │ + Cohere reranker setup with 3 lines of code.   │
  │ Retrieval quality is comparable." — Reddit user  │
  │                                                 │
  │ Try it: github.com/user/embedrank               │
  │ Signals: 128 stars (launched 22h ago)            │
  │          87th percentile star velocity (daily)   │
  │          Reddit r/LocalLLaMA: 94 upvotes         │
  └─────────────────────────────────────────────────┘

---------------------------------------------------------------------
[7] EVERYTHING ELSE (SKIM)
---------------------------------------------------------------------
  - Hugging Face adds GGUF quantization selector to model cards [LOW]
    [Open-source model/tool releases] — huggingface.co/blog
  - Weights & Biases launches Weave 2.0 for LLM tracing [MEDIUM]
    [LLMOps/monitoring/tracing] — wandb.ai/changelog
  - Together AI reduces Llama 3.1 70B inference price by 15% [LOW]
    [Pricing & billing changes] — together.ai/blog
  - Pinecone adds namespace-level RBAC in Enterprise tier [LOW]
    [Enterprise features] — docs.pinecone.io/changelog

=====================================================================
Was this useful?  [Thumbs Up]  [Thumbs Down]  |  [Preferences]
=====================================================================
```

---

## APPENDIX B: 30-CATEGORY TAXONOMY (Verbatim Reference)

| # | Category |
|---|---------|
| 1 | New foundation model release |
| 2 | Model upgrade (quality/latency/context) |
| 3 | New modality (vision/audio/video/3D) |
| 4 | Fine-tuning/customization updates |
| 5 | Inference & serving (speed/runtimes) |
| 6 | Pricing & billing changes |
| 7 | Rate limits/quotas/tiers |
| 8 | Deprecations/breaking changes |
| 9 | SDK releases/updates |
| 10 | API changes (endpoints/auth/schemas) |
| 11 | Agents frameworks/orchestration |
| 12 | Tool-use/function calling/integrations |
| 13 | RAG/retrieval tooling |
| 14 | Embeddings & reranking |
| 15 | Evaluation/benchmarks/evals |
| 16 | Datasets (new/updated/licensing) |
| 17 | Safety/alignment features |
| 18 | Policy/compliance/governance |
| 19 | Security incidents/vuln disclosures |
| 20 | Privacy changes |
| 21 | Open-source model/tool releases |
| 22 | New developer products (dashboards/playgrounds) |
| 23 | Enterprise features (SSO/RBAC/audit logs) |
| 24 | Edge/on-device AI |
| 25 | Hardware accelerators/drivers |
| 26 | Training infrastructure/distributed systems |
| 27 | LLMOps/monitoring/tracing |
| 28 | App launches (consumer/prosumer) |
| 29 | Funding/M&A/partnerships |
| 30 | Reliability/outages/status updates |

---

*End of Plan Document.*
*Generated: 2026-02-09*
