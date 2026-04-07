# Campaign Launch Research Summary

*Source: 20260406-campaign-launch-research-summary.html*
*Priority: P0*

## Executive Summary

This document consolidates findings from four specialist research agents analyzing AITourPilot's marketing automation strategy against current reality (April 6, 2026). The research covered: document gap analysis, system architecture, external tool capabilities, and museum sales intelligence.

**Key conclusions:**

1. The original plan (build TouriBot 4 weeks, then campaign) is no longer viable -- the timeline has slipped 3 weeks
2. A **minimum viable platform** is needed before outreach begins -- specifically a context-rich AI assistant with memory of all business knowledge, capable of drafting deeply personalized emails
3. Instantly.ai handles mass cold outreach; the warm reactivation (31 HubSpot leads) requires **personal emails from hermann@aitourpilot.com** drafted with full business context
4. April-May is an excellent timing window for museum pitches (budgets confirmed, pre-summer decision pressure)
5. The 31 demo leads are the highest-value asset -- they need personalized, founder-sent emails, not automated sequences

---

## Two Parallel Tracks

The campaign operates on two distinct tracks with different tools, domains, and approaches:

### Track A: Warm Reactivation (High-Touch, Personal)

| Aspect | Detail |
|--------|--------|
| **Sender** | hermann@aitourpilot.com (Zoho, main domain) |
| **Recipients** | 31 HubSpot demo leads + select warm contacts |
| **Volume** | 2-3 emails/day max (protect .com domain reputation) |
| **Personalization** | Deep -- each email references specific museum, recent news, their role |
| **Tool** | AI assistant with full business context (Touri Lite) |
| **Tone** | Founder writing personally to someone who expressed interest 12 months ago |
| **Goal** | Demo bookings from warm contacts |

### Track B: Cold Outreach (Automated, Scalable)

| Aspect | Detail |
|--------|--------|
| **Sender** | hermann@aitourpilot.co (Google Workspace, outreach domain) |
| **Recipients** | New leads from LinkedIn Sales Navigator, conference lists |
| **Volume** | 10-15 emails/day (after warm-up completes) |
| **Personalization** | Semi-automated -- AI-generated hooks inserted into Instantly.ai templates |
| **Tool** | Instantly.ai sequences |
| **Tone** | Professional cold outreach with personalized opening |
| **Goal** | Pipeline building, demo bookings |

> Track A starts as soon as the platform core is ready. Track B starts when Instantly.ai warm-up reaches sufficient health score (~2-3 weeks).

---

## The Platform Requirement: Touri Lite

Before any outreach email is sent, a minimum viable AI assistant is needed that:

1. **Knows everything** -- all strategy docs, campaign history, product details, competitor analysis, pricing, La Pedrera case study, engagement response framework, email templates, objection handling
2. **Remembers conversations** -- when a museum responds, the context of that exchange persists and informs future drafts
3. **Drafts personalized emails** -- given a museum name and contact, produces deeply customized outreach incorporating all available intelligence
4. **Learns from responses** -- successful angles are reinforced; rejected approaches are avoided
5. **Can answer questions** -- acts as a knowledgeable co-pilot during the campaign

This is not the full TouriBot platform (50-70 hours). This is the **core intelligence layer** -- the part that actually writes the emails. It can be built in significantly less time by leveraging existing infrastructure (HenryBot's memory system, Claude's context capabilities).

### Build Options for Touri Lite

| Option | Effort | Persistence | Quality |
|--------|--------|------------|--------|
| **Claude Project** (claude.ai) | 2-3 hours setup | Per-project files persist; conversation memory resets | Good -- 200K context window holds all docs |
| **HenryBot fork with business docs** | 8-12 hours | Full 3-tier memory (permanent) | Excellent -- remembers everything across sessions |
| **Custom chatbot (new build)** | 20-30 hours | Custom memory | Excellent but slow to build |

**Recommended: HenryBot fork (Touri Lite)**

HenryBot already has the 3-tier memory system, multi-model support, and the architectural patterns needed. A lightweight fork that:
- Loads all AITourPilot business docs into Tier 2 memory
- Has a soul.md defining its role as an outreach co-pilot
- Remembers every email drafted and every response received
- Can be queried conversationally ("Draft a reactivation email for Lisa Witschnig at Universalmuseum Joanneum")

This gives the persistent, context-rich drafting capability needed without building the full pipeline, dashboard, or automation layers.

---

## Sending from hermann@aitourpilot.com: Domain Safety

The .com domain has been in low usage for ~2 years. Sending 10-20 personalized emails per week is safe because:

- These are genuine 1:1 emails, not bulk sends
- Recipients are real contacts who previously opted in
- The volume (2-3/day) is well within normal personal email usage
- Zoho's sending limits for business accounts are typically 100-500/day
- The emails invite replies (boosting domain reputation)

**Safety rules:**
- Never exceed 3 emails/day from .com
- Always personalize -- no templates sent verbatim
- Space emails throughout the day (not all at once)
- Monitor for bounces -- verify each address before sending
- If any bounce or spam complaint occurs, pause immediately

---

## Prioritized Contact List (Weeks 1-4)

**Removed from list:** La Pedrera (declined in Feb 2026 meeting)

**Updated context:** Georgie Power (SS Great Britain) -- had a meeting ~1 year ago, seemed interested, neither party followed up. This is the warmest lead on the list.

### Week 1: Top Priority (send first, highest likelihood of engagement)

| # | Contact | Institution | Country | Why First |
|---|---------|------------|---------|----------|
| 1 | **Georgie Power** | SS Great Britain, Bristol | UK | Had a meeting -- warmest lead. "Picking up where we left off" angle. |
| 2 | **Lisa Witschnig** | Universalmuseum Joanneum | Austria | DACH home ground. Large museum complex with digital ambitions. German-language email. |
| 3 | **Nils van Keulen** | Slot Loevestein | Netherlands | Dutch castle, sophisticated museum tech market. Likely understands the space deeply. |
| 4 | **Sebastien Mathivet** | Cap Sciences | France | Science centre -- innovation-forward, expects interactivity. French market priority. |
| 5 | **Treglia-Detraz** | Musee d'art et d'histoire de Geneve | Switzerland | Premium market, strong budgets. French-language email shows respect. |

### Week 2: High Priority

| # | Contact | Institution | Country | Why |
|---|---------|------------|---------|----|
| 6 | **Asa Peterson** | Naturhistoriska riksmuseet | Sweden | Large Nordic institution, digital-mature, strong accessibility mandates. |
| 7 | **Axel Uhle** | Historisches Museum Saar | Germany | DACH market, regional history museum with storytelling potential. |
| 8 | **Jacques Engels** | Oorlogsmuseum Overloon | Netherlands | War museum -- intense storytelling needs, "ask the historical figure" use case is compelling. |
| 9 | **Francesca Crudo** | France Museums | France | Investigate role first -- if network/consultancy level, this is highest-leverage contact on the list. |
| 10 | **Rich Joynes** | Staffordshire Regiment Museum | UK | Small UK military museum. Faster decision cycle. Could be first revenue-generating pilot. |

### Week 3-4: Solid Prospects

| # | Contact | Institution | Country | Why |
|---|---------|------------|---------|----|
| 11 | **Timo Kukko** | Hunting Museum of Finland | Finland | Niche but already expressed interest. Nordic market. |
| 12 | **Mia Ulin** | Uppsala:2030 | Sweden | Urban development project -- different angle but innovation-minded. |
| 13 | **Dr. Marc Philip** | Netzwerk Industriewelt Aargau | Switzerland | Industrial heritage network -- could open multiple sites. |
| 14 | **Alexandre** | WE REV'ART | France | Research needed on institution type before outreach. |

### The 43 MailerLite Subscribers

These are lower priority than the 31 demo leads. After Week 2, segment them:
- Museum professionals: move to Track A (personal email)
- Art enthusiasts / general public: move to Track B (Instantly.ai consumer reactivation sequence)
- Notable: **Museovation (Elisa Gravil, France)** -- museum innovation consultancy, could be a referral partner. Contact personally.

---

## Museum Procurement Intelligence

### Why April-May Timing is Excellent

- 2026 budgets are confirmed and live (approved Q4 2025)
- Department heads have discretionary/innovation budget to spend before summer
- Summer freeze hits July-August (board meetings pause, staff on holiday)
- Any proposal needing board sign-off must move April-June or wait until October
- Grant-funded innovation decisions land April-June (EU Horizon, national arts councils)

### Decision-Making Structure for EUR 50K+ Deals

| Role | Function | Signing Authority |
|------|----------|------------------|
| **Champion** (Head of Digital, Innovation Lead) | Wants it, advocates internally | Cannot sign alone |
| **Economic Buyer** (Director / Deputy Director) | Approves technology contracts | EUR 25-75K range at most institutions |
| **Finance blocker** (CFO / Finance Manager) | Reviews contracts for compliance | Can delay or block |
| **Board** | Capital expenditure oversight | Only involved above EUR 100-200K or multi-year |

**Implication:** A 90-day pilot at EUR 8-12K stays below board threshold. The champion (your contact) can get Director sign-off without a formal procurement process. This is why the pilot structure is critical.

### Realistic Sales Cycle

| Stage | Warm Leads (31 HubSpot) | Cold Leads |
|-------|------------------------|------------|
| Contact to first demo | 1-2 weeks | 4-8 weeks |
| Demo to pilot proposal | 2-4 weeks | 2-4 weeks |
| Proposal to signed agreement | 4-12 weeks | 4-12 weeks |
| **Total** | **7-18 weeks** | **10-24 weeks** |

For the warmest leads (Georgie Power, Lisa Witschnig), a pilot signature by July-August 2026 is realistic. The 60-day close target is achievable only for the most committed prospects.

---

## Recommended Pilot Structure

**Duration:** 90 days

**Scope:** 1-2 exhibition rooms or one thematic collection (not the whole museum)

**Content delivery:** Live AI guide built on museum's existing documentation within 14 days of signing

**Pricing options:**

| Option | Structure | Best For |
|--------|-----------|----------|
| **Paid Pilot** | EUR 8,000-12,000 for 90 days (setup + 2 languages + support). Full implementation fee waived if converting to annual license within 30 days. | Museums with confirmed innovation budget |
| **Success-Share** | No upfront fee. EUR 1.50-2.00 per active session, capped at EUR 5,000. | Hesitant prospects -- removes procurement committee entirely |

**Pre-agreed success metrics:**
1. Activation rate (% visitors who start a conversation) -- target: 15-30%
2. Average conversation turns -- target: 5+ turns
3. Dwell time delta (piloted rooms vs control)
4. Visitor satisfaction (3-question survey) -- target: 4.0/5.0
5. Staff feedback (qualitative)

---

## Key Event: Museum AI Summit (May 27-28, Virtual)

MuseumNext's Museum AI Summit -- 4,000+ delegates from institutions including Tate, Rijksmuseum, AMNH, Louvre Abu Dhabi. Virtual format, ~EUR 200-300.

**Strategy:**
1. Register immediately
2. Time first outreach wave to land in inboxes May 18-22 (before the summit)
3. Post LinkedIn content before, during, and after the summit
4. Engage with speakers in comments -- establish presence
5. Follow up with new connections made at the summit in Week 8-9

---

## Document Updates Needed

### Precision Partner Acquisition Engine
- Remove La Pedrera from active targets (declined Feb 2026)
- Update Instantly.ai pricing ($47/mo, not EUR 30)
- Fix inter-document links (all docs are in marketing-platform/ folder)
- Recalibrate timeline from April 6 reality
- Add note: Georgie Power (SS Great Britain) had a meeting ~1 year ago

### TouriBot Architecture
- Revise Architecture Decision 6: "Campaign first, platform enhances" (not "build first, campaign after")
- Revise Architecture Decision 2: Reactivation from .com (Zoho), cold outreach from .co (Instantly.ai)
- Add "Touri Lite" as Phase 0.5 -- the minimum viable AI assistant
- Fix model name: gemini-3.1-pro-preview does not exist
- Resolve Telegram contradiction (Phase 1 milestone vs Decision 7)

### Outreach Infrastructure Blueprint
- Update warm-up start date to April 4 (not March 20)
- Add .dk exception documentation
- Update Instantly.ai pricing
- Recalibrate execution timeline
- Note DMARC tightening due April 18 - May 2

---

## Revised Phased Plan

### Phase 0: Touri Lite (Days 1-5, ~10-12 hours)

Build the core intelligence layer -- an AI assistant with full business context and persistent memory. Fork from HenryBot or create a Claude Project loaded with all strategy docs, product overview, email templates, lead data, and the engagement response framework.

**Milestone:** Can have a dialogue like: "Draft a reactivation email for Georgie Power at SS Great Britain. We had a meeting about a year ago. She seemed interested but we both didn't follow up."

### Phase 1: First Outreach Wave (Days 5-14, ~15 hours)

Using Touri Lite, draft personalized reactivation emails for the top 5 contacts. Send from hermann@aitourpilot.com (2-3/day). Post LinkedIn award announcement.

### Phase 2: Expand Outreach (Days 14-30, ~15 hours)

Contacts 6-14 from the prioritized list. Begin cold lead research for Track B (Instantly.ai). Process responses via Touri Lite (maintains memory of all interactions).

### Phase 3: Pipeline Management + TouriBot Build (Days 30-60)

Conduct demo calls. Prepare pilot proposals. Begin building the full TouriBot platform (informed by real operational needs from Phases 1-2).

---

*Based on: Multi-agent research (4 specialists: Document Investigator, Architect Analyst, External Researcher, Museum Sales Specialist). Sources: Instantly.ai documentation, MuseumNext event calendar, Lemlist/Woodpecker/Hunter.io best practices, museum procurement research, B2B reactivation benchmarks, Apify/Clay.com tool analysis.*

*Compiled: April 6, 2026*
