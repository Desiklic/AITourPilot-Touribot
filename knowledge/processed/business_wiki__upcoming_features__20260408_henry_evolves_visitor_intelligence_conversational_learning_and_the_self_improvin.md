# 20260408-henry-evolves-visitor-intelligence-conversational-learning-and-the-self-improvin

*Source: Business Wiki / upcoming-features/20260408-henry-evolves-visitor-intelligence-conversational-learning-and-the-self-improvin.html*

> **Execution order: 2 of 2** -- This document **depends on** [Phase 2: Scaling Beyond Native RAG](20260408-phase-2-scaling-beyond-native-rag.html). The Visitor Profile DB requires Phase 6's Session Context API. Henry's Notebook requires Phase 7's RAG Gateway. The Adaptation Dashboard and circular content loop require Phase 8's Content Optimization Flywheel. Implement Phase 2 infrastructure first.

---

## Why This Document Exists

During the first real-world validation of Henry V3 at the Belvedere (April 2026), three Kunstkenner test sessions revealed that Henry adapts brilliantly to an art connoisseur -- matching vocabulary, dropping visual guidance when asked, offering deep art-historical analysis. But when asked to recall what was discussed, Henry hallucinated: he claimed conversations about Schiele, Kokoschka, and Lassnig that never happened. The memory was fabricated from KB content, not from actual conversation history.

This exposed a fundamental gap: **Henry has no structured memory of who visitors are or what they've experienced.** The `{{prior_conversation_summary}}` dynamic variable is a text blob with no verification, no structured data, and no connection to a persistent visitor identity. Henry adapts in real-time within a session (V3 does this well), but across sessions he is blind.

At the same time, a whiteboard session months earlier had sketched a broader vision: a system where visitor conversations flow back into content creation, where questions become content harvests, where patterns detected across thousands of conversations make the system smarter for everyone. The Q&A loop feeds the content engine. The content engine feeds Henry. Henry feeds the visitors. The visitors feed the Q&A loop.

This document connects the Belvedere findings with the whiteboard vision and the Phase 2 scaling architecture into a unified path forward.

---

## The Whiteboard Vision (Early 2026)

Hermann's whiteboard sketched a circular system with two poles:

**Pole A -- Output (AITourPilot):** What visitors receive:
- **Stories** (entertainment)
- **Information** (lesser-known stuff, secrets)
- **Community** (what others say)

**Pole B -- Content Creation:** Adapted and highly valuable content, created from:
- **Questions to Visitors** that harvest answers (Henry's questions aren't just engagement -- they're data collection)
- A decision filter: **Is this valuable for the community?**
  - **Yes** --> General DB (patterns, insights, popular topics)
  - **No** (highly personal) --> Users DB (individual preferences, private context)
- **Pattern Detection** across the General DB:
  - What's inspirational to others?
  - What's interesting to many?
  - What does the majority think?
- These patterns feed back into **adapted, highly valuable content** (Pole B --> Pole A)

**The Rating insight:** Content rating (star ratings, thumbs up) is cumbersome -- most visitors don't do it. The whiteboard asks: **Can this be avoided by asking questions? Or a hybrid of Q&A + rating?** Henry's Rare Genuine Questions (Type 3) are the answer: they serve both the visitor experience AND data collection simultaneously.

**The Conversational Design reference:** Erica Hall's work on conversational design -- getting patterns and ideas from how humans naturally exchange information in dialogue.

---

## Four System Expansions

### 1. Visitor Profile Database

A persistent, privacy-first record of who visits and how they engage.

**Schema concept:**

| Table | Key Fields | Purpose |
|-------|-----------|---------|
| VisitorProfile | deviceIdHash, profileType (Kunstkenner/casual/family/student), interests[], preferredDepth (shallow/medium/deep), preferredLanguage, visitCount, firstSeenAt, lastSeenAt | Persistent identity across sessions |
| VisitSession | visitorId, museumId, agentId, languageCode, startedAt, durationSecs, artworksDiscussed[], visitorType, adaptationApplied, summaryText | Per-visit structured record |

**Privacy:** No PII stored. The deviceIdHash is a one-way hash of the mobile device ID -- enough to recognize a returning device, impossible to reverse into identity. Summaries contain behavioral patterns ("prefers art-historical depth"), not personal data.

**Connection to the whiteboard:** This IS the "Users DB" from the whiteboard -- the private, individual context that stays personal. The profileType field ("Kunstkenner") would have prevented the Belvedere hallucination because Henry would read "discussed: Klimt Buchenwald, Klimt Tod und Leben" from structured data, not from a vague text summary.

**Connection to Phase 2:** The VisitorProfile feeds directly into Phase 6's Session Context API (`GET /api/public/museums/{id}/session-context?lang=de`). Instead of just returning language overrides, it returns the full visitor context: returning visitor, Kunstkenner, prefers depth, discussed Buchenwald last time.

### 2. Background Classification Agent ("Henry's Notebook")

A lightweight AI agent that processes conversations in the background without interrupting Henry's flow.

**How it works:**
1. After each conversation ends, ElevenLabs sends the transcript via webhook
2. Henry's Notebook processes the transcript with a classification LLM call
3. It extracts structured data: visitor type, artworks discussed, questions asked, engagement level, depth preference, what made the visitor say "wow"
4. It writes to VisitorProfile (individual) and a ConversationInsight table (aggregate)

**What it classifies:**
- **Visitor type:** Kunstkenner, casual tourist, family with children, student, romantic couple, reflective/quiet
- **Artworks discussed:** Exact names, with context (asked about technique? emotionally moved? just browsing?)
- **Questions asked:** What did the visitor want to know? (Maps to the whiteboard's "Questions to Visitors --> MDS Harvests Answers")
- **Adaptation effectiveness:** Did Henry match the visitor's register? Did the visitor stay engaged or disengage?

**What it does NOT do:**
- Does not interrupt Henry during the conversation
- Does not inject data in real-time (that's the VisitorProfile's job at session START)
- Does not store PII (transcripts are processed and discarded; only structured insights persist)

**Connection to the whiteboard:** This is the "MDS Harvests Answers" engine. Henry's questions (especially Type 3 Genuine Questions like "What strikes you most about this one?") produce answers that Henry's Notebook classifies into community-valuable insights vs. personal preferences.

**Connection to Phase 2:** This feeds directly into Phase 8's Content Optimization Flywheel. The three analysis passes (Gap Detection, Interest Detection, Pattern Aggregation) are exactly what Henry's Notebook produces. The difference: Phase 8 described batch processing of transcripts. Henry's Notebook makes it event-driven -- each conversation is processed immediately after it ends.

### 3. Henry Reads the Profile at Start

The bridge between stored knowledge and real-time adaptation.

**Current flow (V3):**
1. Visitor opens app, starts conversation
2. Mobile app sends `{{prior_conversation_summary}}` (text blob from local storage)
3. Henry reads it and adapts

**Enhanced flow:**
1. Visitor opens app
2. Mobile app sends deviceIdHash to Session Context API
3. Factory looks up VisitorProfile: returning Kunstkenner, 4th visit, last discussed Klimt Buchenwald and Tod und Leben, prefers art-historical depth, doesn't want visual guidance
4. Factory returns structured context that goes into `{{prior_conversation_summary}}`
5. Henry reads structured, verified data -- no hallucination possible

**The anti-hallucination benefit:** Instead of "The visitor is interested in Viennese Modernism" (which the LLM expands into fabricated specifics), Henry receives "Discussed: Klimt Buchenwald (art-historical context, modernism trajectory), Klimt Tod und Leben (mentioned, not explored). Visitor type: Kunstkenner. Preference: depth over guided seeing."

**Connection to Phase 2:** This enhances Phase 6's Session Context API. The original spec returns language and voice overrides. The enhanced version also returns the visitor profile, making Henry's adaptation evidence-based from the first word.

### 4. Adaptation Verification Dashboard

How we know Henry is actually adapting -- not just anecdotally, but statistically.

**What it shows:**

| Metric | Source | Value |
|--------|--------|-------|
| Visitor type distribution | Henry's Notebook | 40% casual, 25% Kunstkenner, 20% family, 15% other |
| Avg session duration by type | VisitSession | Kunstkenner: 8min, casual: 3min, family: 5min |
| Adaptation match rate | Henry's Notebook | 85% of sessions where detected type matches response register |
| Top artworks by engagement | VisitSession | Klimt The Kiss (discussed 340 times), Schiele Death and the Maiden (180 times) |
| Content gaps | Gap Detection | "Visitors ask about Baroque collection but content is thin" |
| Questions that produced insights | ConversationInsight | "What strikes you most?" generated 120 community-valuable responses |

**Connection to the whiteboard:** This is the "Detect Patterns" box -- the system that finds what's inspirational to others, what's interesting to many, what the majority thinks. The dashboard makes these patterns visible to the operator.

**Connection to Phase 2:** Feeds directly into Phase 8's flywheel. The dashboard is the human-readable view of what the automated system is already doing: detecting gaps, prioritizing content, measuring engagement.

---

## The Circular System (Whiteboard + Phase 2 + V3 Unified)

The whiteboard's two poles become a concrete architecture:

**Pole A (Output)** = Henry V3 with adaptive personality + structured visitor profile + anti-hallucination memory

**Pole B (Content Creation)** = Content Factory pipeline + Henry's Notebook + Content Optimization Flywheel

**The loop:**
1. Henry talks to visitors (Pole A)
2. Transcripts flow to Henry's Notebook (background)
3. Notebook classifies: visitor profile (Users DB) + community insights (General DB)
4. Pattern Detection finds gaps and popular topics
5. Content Factory enriches content based on patterns (Pole B)
6. Enriched content feeds back to Henry's KB
7. Henry delivers better, more adapted content (back to Pole A)

**The rating question answered:** The whiteboard asked whether manual ratings can be replaced by asking questions. YES. Henry's Type 3 Genuine Questions ("What strikes you most about this one?") simultaneously:
- Deepen the visitor's experience (Henry V3 design principle)
- Produce answers that Henry's Notebook classifies as community-valuable or personal
- Feed the content flywheel without any friction (no stars, no thumbs, no surveys)

This is the "hybrid of Q&A + rating" the whiteboard envisioned -- except it's not a hybrid. It's pure conversation. The rating happens invisibly through the classification agent.

---

## Implementation Priority

| Priority | What | Depends on | Effort |
|----------|------|-----------|--------|
| **Now** | Anti-hallucination guard in returning visitor prompt | None (done) | Done |
| **Phase 6** | Session Context API + VisitorProfile table | Phase 4/5 V3 rollout | 2-3 weeks |
| **Phase 8** | Henry's Notebook + ConversationInsight table | Phase 7 (RAG Gateway) | 3-4 weeks |
| **Phase 8b** | Adaptation Verification Dashboard | Henry's Notebook | 1-2 weeks |
| **Phase 8c** | Circular content improvement loop | Dashboard + Pattern Detection | 2-3 weeks |

The visitor profile can be implemented alongside Phase 6 (Dynamic Agent Architecture) since both modify the Session Context API. Henry's Notebook is naturally part of Phase 8 (Content Optimization Flywheel) since both process conversation transcripts.

---

## References

- [Henry V3 Adaptive Personality System](../strategy/20260320-henrys-adaptive-personality-system.html) -- The 9 invariants, 6 adaptive dimensions, and progressive visitor profiling that this expansion builds on
- [Henry V3 Implementation Roadmap](../strategy/20260402-henry-v3-adaptive-personality-implementation-roadmap.html) -- The phased implementation plan (Phases 1-5)
- [Phase 2: Scaling Beyond Native RAG](20260408-phase-2-scaling-beyond-native-rag.html) -- The infrastructure scaling plan (Phases 6-9) that these expansions integrate with
- [User Testing Analysis: 68 Conversations](../research/20260405-henry-v2-user-testing-analysis-68-conversations-from-khm-wien-and-albertina.html) -- The empirical evidence that drove V3's design
- [Henry Remembers: Cross-Session Memory](20260405-henry-remembers-cross-session-conversation-memory.html) -- The current returning visitor implementation (V1 text-blob approach)

*The whiteboard vision and Phase 2 architecture describe the same system from different angles. The whiteboard sees the human experience loop. Phase 2 sees the technical infrastructure. This document connects them into one path forward.*
