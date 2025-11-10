<!--
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
-->

# Offer/Coupon Implementation Options

## Context
Display promotional offers/coupons in chat stream with:
- Manual CSV uploads + image files
- Static catalog with date ranges (valid_from, valid_to)
- Click → external redemption page (trackable)
- Multi-language support
- AI inference to suggest relevant offers

---

## Option 1: Extend Directory Service

**Implementation**: Create `coupon` entry_type using existing directory infrastructure

```yaml
# backend/config/directory_schemas/coupon.yaml
entry_type: coupon
required_fields: [coupon_code, valid_from, valid_to, image_url, redemption_url]
optional_fields: [description, terms, language, category]
tags_usage: [language, category] # e.g., "Spanish", "Food", "Retail"
```

**Pros**:
- Reuses proven architecture (JSONB, GIN indexes, FTS, CSV imports)
- Multi-tenant isolation (account-level offers)
- Schema-driven (same pattern as doctors, phone_directory)
- Date range filtering trivial: `WHERE entry_data->>'valid_to' >= NOW()`
- AI inference via existing tool (LLM selects relevant coupons)

**Cons**:
- Image storage separate (S3/filesystem, store URLs in JSONB)
- Click tracking requires new endpoint (simple addition)
- Not purpose-built for promotions (general-purpose compromise)

---

## Option 2: New Custom Tool (Python)

**Implementation**: `backend/app/agents/tools/coupon_tools.py` with dedicated database table

**Pros**:
- Purpose-built for coupons (click tracking, analytics built-in)
- Direct image handling (S3 integration)
- Custom expiration logic, redemption limits, usage tracking

**Cons**:
- Duplicates directory service logic (CSV import, search, multi-tenant)
- More code to maintain (~500 lines vs. ~50 for directory extension)
- Separate schema/migration/seeding vs. reusing proven patterns

---

## Option 3: MCP Server (NextJS/TS)

**Implementation**: Separate microservice using `@modelcontextprotocol/sdk`

**Pros**:
- Completely decoupled (independent scaling, deployment)
- Could integrate with external promo engines later
- TypeScript ecosystem for image/analytics services

**Cons**:
- Network latency (external HTTP calls per chat message)
- Overkill for static catalog (manual CSV uploads)
- More infrastructure (deployment, monitoring, auth)
- Slower development (new service vs. schema file)

---

## Recommendation: **Option 1 - Extend Directory Service**

**Rationale**:
1. **90% fit**: Static catalog + CSV imports + multi-tenant + search = directory service core strengths
2. **Fast delivery**: Schema file + mapper function (~2 hours) vs. new service (~2 days)
3. **Proven patterns**: Reuses wyckoff doctors (124 entries), phone_directory (10 entries) architecture
4. **Easy extensions**: Click tracking endpoint trivial, image storage (S3) standard pattern
5. **AI inference works**: LLM already selects from directories via `search_directory` tool

**Implementation Path** (Feature 0023-010):
1. Create `coupon.yaml` schema (standard fields + image_url, redemption_url, valid_from/to)
2. Add `coupon_mapper()` to `DirectoryImporter` (CSV → entry_data + image URL)
3. Seed coupon catalog: `seed_directory.py --mapper coupon --list coupons`
4. Add date range filter to `DirectoryService.search()`: `valid_to >= NOW()`
5. Click tracking: See "Click Tracking Options" below
6. Agent prompt: Auto-generates coupon tool docs from schema (existing `prompt_generator.py`)

**Missing pieces**: Image storage (S3 bucket + URLs), click tracking endpoint (~100 lines)

---

## Click Tracking Options

### Option A: Track Coupon Only

**Endpoint**: `POST /track/coupon/{coupon_id}/click`

**Schema**: `coupon_clicks (id, coupon_id, clicked_at, ip_address)`

**Pros**:
- Simple implementation (no session context needed)
- Privacy-friendly (minimal PII)
- Fast queries (single table, indexed by coupon_id)

**Cons**:
- No multi-tenant analytics (can't see which account's coupons perform)
- No agent attribution (can't compare chat vs. email vs. SMS channels)
- Limited business intelligence (just aggregate click counts)

---

### Option B: Track Account + Agent Instance (Recommended)

**Endpoint**: `POST /track/coupon/{coupon_id}/click` (with session_id in payload)

**Schema**: `coupon_clicks (id, coupon_id, account_id, agent_instance_id, session_id, clicked_at, ip_address)`

**Pros**:
- Multi-tenant analytics (which accounts drive redemptions → billing/value metrics)
- Agent performance tracking (A/B test agents with/without coupons)
- Channel attribution (chatbot vs. email campaigns vs. SMS)
- Revenue attribution (tie coupon ROI to specific accounts/agents)
- Funnel analysis (conversation → click → redemption)

**Cons**:
- Requires session context (frontend must pass session_id)
- More complex queries (JOIN with sessions, agents, accounts)
- Privacy considerations (tracking user journey)

---

### Recommendation: **Option B - Track Account + Agent Instance**

**Rationale**:
1. **Multi-tenant platform**: Account-level analytics essential for SaaS billing/value proposition
2. **Agent optimization**: Need data to improve coupon targeting per agent
3. **Minimal complexity**: Session context already available in frontend (chat widget has session_id)
4. **Standard pattern**: Matches existing analytics (messages, LLM requests already track account + agent)
5. **Future-proof**: Enables conversion tracking (click → redemption → revenue per account)

**Implementation**:
```python
# POST /api/coupons/{coupon_id}/track_click
{
  "session_id": "uuid",        # Frontend provides (already in chat context)
  "clicked_at": "ISO8601",
  "user_agent": "string",
  "ip_address": "string"       # Server-side capture
}

# Backend resolves: session_id → account_id + agent_instance_id (existing pattern)
```

**Privacy**: Anonymous session tracking (no user PII), retention policy (30-90 days), opt-out mechanism if needed.

**Why not Option 2/3**: Premature specialization. Use directory service until proven insufficient (if/when need dynamic pricing, inventory sync, redemption limits, then consider custom solution).

