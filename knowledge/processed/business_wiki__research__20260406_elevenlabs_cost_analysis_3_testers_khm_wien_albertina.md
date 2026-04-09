# 20260406-elevenlabs-cost-analysis-3-testers-khm-wien-albertina

*Source: Business Wiki / research/20260406-elevenlabs-cost-analysis-3-testers-khm-wien-albertina.html*

**Data source:** ElevenLabs Conversational AI API (detailed per-conversation billing data)
**Reference:** [Henry V2 User Testing Analysis — 68 conversations](20260405-henry-v2-user-testing-analysis-68-conversations-from-khm-wien-and-albertina.html)
**Generated:** 2026-04-06

---

## 1. Test Sessions Overview

| Session | Museum | Date | Time (CET/CEST) | Tester(s) | Agent ID |
|---------|--------|------|-----------------|-----------|----------|
| KHM-DE | Kunsthistorisches Museum Wien | 2026-03-24 | 07:52–12:24 CET | Hermann (55) + Simone (50) | agent_0301km5b6hgxfr7beak4xq9jb4yr |
| KHM-EN | Kunsthistorisches Museum Wien | 2026-03-24 | ~09:21 CET | Hermann (brief EN test) | agent_8801km58t4jeec78ee1ky6ze0df1 |
| Albertina-EN-new | Albertina | 2026-04-04 | 14:26–15:46 CEST | Mathias (22) | agent_8001kkt116kvfepbf8abwvge0vxp |
| Albertina-EN-old | Albertina | 2026-04-04 | 14:26–15:21 CEST | Mathias (22) | agent_8101khqsshfxe87b24xprf75mq8z |

**Tester profiles:**
- **Hermann** (55, male): Storytelling style, long deep conversations, frequently hits 10-min session cap
- **Simone** (50, female): Concise, practical, shorter sessions
- **Mathias** (22, male): Exploratory, quick questions, tested both old and new Albertina agent versions

---

## 2. Conversation Counts & Duration

| Group | Conversations | Total Duration | Avg Duration | Total Messages | Avg Msgs/Conv |
|-------|-------------|---------------|-------------|---------------|---------------|
| KHM-DE | 38 | 10,337s (172.3 min) | 272s (4.5 min) | 496 | 13.1 |
| KHM-EN | 2 | 67s (1.1 min) | 34s | 6 | 3.0 |
| Albertina-EN-new | 19 | 877s (14.6 min) | 46s (0.8 min) | 35 | 1.8 |
| Albertina-EN-old | 9 | 913s (15.2 min) | 101s (1.7 min) | 32 | 3.6 |
| **TOTAL** | **68** | **12,194s (203.2 min)** | **179s (3.0 min)** | **569** | **8.4** |

---

## 3. LLM Model & Token Usage

### Model Used
**GPT-5.2** — ElevenLabs' default LLM for Conversational AI agents (as of March 2026). A small amount of **Gemini 2.5 Flash** was also used (KHM-DE only, 99K input tokens — likely for language detection).

### GPT-5.2 Token Pricing (ElevenLabs pass-through rates)

| Token Type | Price per Million Tokens |
|-----------|------------------------|
| Input (new) | $1.75 |
| Input (cache read) | $0.175 |
| Output | $14.00 |

### Token Consumption by Group

| Group | Input Tokens | Cache Read | Output Tokens | Total Tokens |
|-------|-------------|-----------|--------------|-------------|
| KHM-DE | 9,741,967 | 1,302,656 | 52,675 | 11,097,298 |
| KHM-EN | 97,095 | 0 | 221 | 97,316 |
| Albertina-EN-new | 579,211 | 64,256 | 3,274 | 646,741 |
| Albertina-EN-old | 557,370 | 79,104 | 2,604 | 639,078 |
| **TOTAL** | **10,975,643** | **1,446,016** | **58,774** | **12,480,433** |

### Key Observation: Input-Heavy
Output tokens are only **0.47%** of total tokens. Conversational AI is overwhelmingly input-heavy because:
- System prompt + knowledge base context is sent with every turn
- RAG retrieval adds large document chunks to each request
- Conversation history grows with each turn
- The agent's spoken responses are relatively short (voice output)

---

## 4. LLM Cost Breakdown

### Initiated vs. Irreversible Generation

ElevenLabs tracks two types of LLM token generation:
- **Initiated (delivered):** Tokens that were successfully delivered to the user as speech
- **Irreversible (wasted):** Tokens generated but discarded (user interrupted, agent was cut off, latency timeout)

| Group | Delivered Cost | Wasted Cost | Total LLM Cost | Waste Ratio |
|-------|---------------|-------------|----------------|-------------|
| KHM-DE | $13.52 | $4.51 | $18.03 | 25.0% |
| KHM-EN | $0.12 | $0.05 | $0.17 | 29.4% |
| Albertina-EN-new | $0.74 | $0.33 | $1.07 | 30.7% |
| Albertina-EN-old | $0.51 | $0.51 | $1.03 | 50.0% |
| **TOTAL** | **$14.89** | **$5.40** | **$20.30** | **26.6%** |

> **Insight:** ~27% of LLM costs are "wasted" on interrupted generation. This is inherent to real-time voice AI — users speak over the agent, disconnect, or the agent starts generating before it's clear the user is done. The old Albertina agent had 50% waste, likely due to less optimized turn-taking behavior.

### LLM Cost per Group

| Group | Conversations | Duration | Total LLM Cost | Cost/Min | Cost/Conv |
|-------|-------------|---------|---------------|---------|----------|
| KHM-DE | 38 | 172.3 min | $18.03 | $0.105 | $0.474 |
| KHM-EN | 2 | 1.1 min | $0.17 | $0.157 | $0.087 |
| Albertina-EN-new | 19 | 14.6 min | $1.07 | $0.073 | $0.056 |
| Albertina-EN-old | 9 | 15.2 min | $1.03 | $0.067 | $0.114 |
| **TOTAL** | **68** | **203.2 min** | **$20.30** | **$0.100** | **$0.298** |

---

## 5. ElevenLabs Credit Consumption

ElevenLabs bills Conversational AI usage in credits (separate from TTS character credits).

| Group | LLM Credits | Call Credits (TTS/STT/Infra) | Total Credits |
|-------|-----------|--------------------------|-------------|
| KHM-DE | 61,437 | 58,607 | 120,044 |
| KHM-EN | 555 | 450 | 1,005 |
| Albertina-EN-new | 3,371 | 4,230 | 7,601 |
| Albertina-EN-old | 2,331 | 6,113 | 8,444 |
| **TOTAL** | **67,694** | **69,400** | **137,094** |

### Credit-to-Dollar Mapping (ElevenLabs Plans)

| Plan | Monthly Cost | Included Minutes | Cost per Minute | Credits per Minute (est.) |
|------|-------------|-----------------|----------------|--------------------------|
| Creator | $22/mo (annual) | ~100 min | $0.22/min | ~675 |
| Pro | $99/mo (annual) | ~500 min | $0.198/min | ~675 |
| Scale | $330/mo (annual) | ~2,000 min | $0.165/min | ~675 |

**Estimated total ElevenLabs platform cost for 203.2 minutes:**
- On Creator plan: **~$44.70** (2.0x monthly allocation, would need 2+ months or Pro plan)
- On Pro plan: **~$40.23** (40.6% of monthly allocation)
- On Scale plan: **~$33.53** (10.2% of monthly allocation)

---

## 6. Per-Visitor Cost Analysis

### Hermann (KHM, March 24) — Storytelling Style

Hermann's session included pre-testing (5:27 AM), early arrival testing (7:52 AM), and the main museum visit alongside Simone (~10:17 AM onward).

**Separation method:** Parallel conversation starts (<60s apart) identified two concurrent streams. The consistently longer, more-message-heavy stream is attributed to Hermann (wiki confirms his "storytelling" style).

| Phase | Conversations | Duration | LLM Cost (delivered) | LLM Cost (total) |
|-------|-------------|---------|---------------------|-----------------|
| Pre-testing (5:27–5:40) | 5 | 12.6 min | $0.64 | — |
| Early arrivals (7:52–9:35) | 3 | 4.1 min | $0.26 | — |
| Setup/audio checks (10:17) | ~3 | ~1.5 min | $0.09 | — |
| Main visit (identified) | 10 | 99.0 min | $9.26 | $12.35 est. |
| **Hermann total** | **~21** | **~117 min** | **~$10.24** | **~$13.66** |

**Hermann's identified main-visit conversations:**

| Time | Duration | Messages | LLM Cost | Topic |
|------|----------|---------|------|-------|
| 10:24 | 601s | 37 | $1.12 | Art Descriptions & History |
| 10:34 | 601s | 39 | $1.40 | Art Discussion Museum |
| 10:44 | 603s | 15 | $0.59 | Maria Isabella, Maria Theresia |
| 10:52 | 602s | 30 | $0.83 | Bruegel and Holbein |
| 10:54 | 602s | 31 | $0.83 | Bruegel Gemalde Beschreibungen |
| 11:04 | 603s | 26 | $0.61 | Vermeer's "Die Malkunst" |
| 11:14 | 601s | 34 | $1.56 | Painting Details Discussion |
| 11:23 | 602s | 25 | $0.83 | Rubens Paintings Discussion |
| 11:34 | 606s | 27 | $0.98 | Rubens, Transport, De Vos |
| 11:38 | 520s | 15 | $0.52 | Art History Details |

**Pattern:** 9 out of 10 conversations hit the 10-minute session cap (600s). Deep engagement, high message count.

### Simone (KHM, March 24) — Concise Style

| Phase | Conversations | Duration | LLM Cost (delivered) |
|-------|-------------|---------|---------------------|
| Setup/audio checks | ~2 | ~1.3 min | $0.00 |
| Main visit (identified) | 5 | 26.9 min | $1.38 |
| **Simone total** | **~7** | **~28 min** | **~$1.38** |

**Simone's identified main-visit conversations:**

| Time | Duration | Messages | LLM Cost | Topic |
|------|----------|---------|------|-------|
| 10:24 | 291s | 20 | $0.32 | Artworks Description |
| 11:04 | 225s | 8 | $0.15 | Cranach painting details |
| 11:14 | 371s | 14 | $0.19 | Vermeer and Vrel Paintings |
| 11:24 | 601s | 19 | $0.54 | Rubens Paintings Discussion |
| 11:33 | 126s | 6 | $0.18 | Rubens' painting figure |

**Pattern:** Shorter sessions, fewer messages, only 1 out of 5 hit the session cap.

### Ambiguous KHM Conversations (10 conversations, ~27 min, $1.90 LLM)
These solo conversations during the main visit couldn't be reliably attributed to either visitor:
- Short interactions: Marie Antoinette (95s), Titian (140s), Hans Holbein (122s)
- Medium sessions: Art Descriptions (474s), Vermeer und Malkunst (241s)
- Brief: Rubens' Begegnung (42s), Magdalena and Martha (233s)
- Disconnects: 2 conversations with 0 messages

### Mathias (Albertina, April 4) — Exploratory Style

Mathias tested both the new (Henry V2) and old agent versions in parallel during his Albertina visit.

| Agent Version | Conversations | Duration | LLM Cost (delivered) | LLM Cost (total) |
|--------------|-------------|---------|---------------------|-----------------|
| New (Henry V2) | 19 | 14.6 min | $0.74 | $1.07 |
| Old agent | 9 | 15.2 min | $0.51 | $1.03 |
| **Mathias total** | **28** | **29.8 min** | **$1.26** | **$2.10** |

**Pattern:** Very short sessions (avg 46s new, 101s old), quick question-answer style. Many 0-message sessions (connection tests). Spent roughly equal time with old and new agents to compare.

---

## 7. Per-Visitor Summary

| Visitor | Style | Conversations | Total Duration | LLM Cost (delivered) | LLM Cost (total) | Est. Platform Cost |
|---------|-------|-------------|---------------|---------------------|------|-------------------|
| **Hermann** | Storytelling, deep | ~21 | ~117 min | ~$10.24 | ~$13.66 | ~$25.74 |
| **Simone** | Concise, practical | ~7 | ~28 min | ~$1.38 | ~$1.84 | ~$6.16 |
| **Mathias** | Exploratory, quick | 28 | 30 min | $1.26 | $2.10 | ~$6.60 |
| **Ambiguous** | (KHM unassigned) | 10+2 | 28 min | $1.90 | ~$2.53 | ~$6.16 |
| **TOTAL** | — | **68** | **203.2 min** | **$14.89** | **$20.30** | **~$44.70** |

> **Est. Platform Cost** uses Creator plan rate of $0.22/min. Includes both LLM and TTS/STT/infrastructure costs.

---

## 8. Cost Projections for Business Model

### Cost per Visitor Type

Based on observed usage patterns:

| Visitor Type | Avg Duration/Visit | LLM Cost | Platform Cost (Creator) | Platform Cost (Scale) |
|-------------|-------------------|---------|----------------------|---------------------|
| Power user (Hermann-type) | 90–120 min | $10–14 | $20–26 | $15–20 |
| Average user (Simone-type) | 25–35 min | $1.40–2.00 | $5.50–7.70 | $4.13–5.78 |
| Casual user (Mathias-type) | 15–30 min | $0.60–1.30 | $3.30–6.60 | $2.48–4.95 |

### At-Scale Projections

Assuming a mix of 10% power users, 50% average users, 40% casual users:

| Metric | Per Visitor (weighted avg) | 100 visitors/mo | 1,000 visitors/mo |
|--------|--------------------------|----------------|-------------------|
| Avg duration | ~35 min | 3,500 min | 35,000 min |
| LLM cost | ~$2.50 | $250 | $2,500 |
| Platform cost (Creator $22) | ~$7.70 | $770 | $7,700 |
| Platform cost (Pro $99) | ~$6.93 | $693 | $6,930 |
| Platform cost (Scale $330) | ~$5.78 | $578 | $5,775 |

### ElevenLabs Plan Sizing

| Plan | Cost/mo | Included Minutes | Max Visitors @35min avg | Cost/Visitor |
|------|---------|-----------------|----------------------|-------------|
| Creator | $22 | ~100 | ~3 | $7.33 |
| Pro | $99 | ~500 | ~14 | $7.07 |
| Scale | $330 | ~2,000 | ~57 | $5.79 |
| Business | Custom | Custom | Custom | Negotiate |

> **Note:** Overage beyond included minutes is charged at a higher rate. These projections assume usage stays within plan allocations.

---

## 9. Key Insights for Business Model

### Cost Drivers (ranked by impact)
1. **Conversation duration** — the #1 cost driver. Hermann's 117 min cost 8x more than Simone's 28 min
2. **LLM input tokens** — each turn resends system prompt + KB context + history (~150K tokens for a 10-min session)
3. **Token waste from interruptions** — ~27% of LLM costs are "wasted" on interrupted output (inherent to voice AI)
4. **Session cap hit rate** — power users consistently hit the 10-min cap, restarting conversations (each restart resends the full context)

### Cost Optimization Levers
1. **Session cap management** — the 10-min cap forces context rebuilds. Raising it would reduce per-conversation setup costs but increase single-session duration
2. **Prompt/KB optimization** — reducing system prompt + KB document size directly reduces per-turn input tokens
3. **Cache hit rate** — currently ~12% of input tokens are cache reads (10x cheaper). Higher cache rates would significantly reduce costs
4. **Model selection** — GPT-5.2 is the default. A smaller/cheaper model might work for simpler queries while routing complex ones to GPT-5.2

### RAG Usage

| Group | RAG Lookups | Lookups/Conv | Embedding Model |
|-------|-----------|-------------|----------------|
| KHM-DE | 190 | 5.0 | e5_mistral_7b_instruct |
| KHM-EN | 3 | 1.5 | e5_mistral_7b_instruct |
| Albertina-EN-new | 16 | 0.8 | e5_mistral_7b_instruct |
| Albertina-EN-old | 0 | 0.0 | — |

The old Albertina agent had **zero RAG lookups**, confirming it was not configured with the KB RAG strategy. The new agent properly uses RAG (0.8 lookups/conv for short Albertina sessions vs. 5.0 for deep KHM sessions).

---

## 10. Raw Data: Token Pricing Verification

### GPT-5.2 Price Verification (from one detailed conversation)

    Input:  152,363 tokens x $1.75/M  = $0.2666
    Cache:   58,240 tokens x $0.175/M = $0.0102
    Output:   1,956 tokens x $14.00/M = $0.0274

### Total Token Counts (All 68 Conversations)

    GPT-5.2:
      Input (new):        10,975,643 tokens   $19.207
      Input (cache read):  1,446,016 tokens   $ 0.253
      Output:                 58,774 tokens   $ 0.823
      Subtotal:                               $20.283

    Gemini 2.5 Flash (KHM-DE only, language detection):
      Input:                  99,051 tokens   $ 0.015
      Output:                    193 tokens   $ 0.000
      Subtotal:                               $ 0.015

    GRAND TOTAL LLM:                          $20.298

---

## 11. ElevenLabs Credit Detail

### Credit Breakdown per Conversation (KHM-DE Top 10 by Cost)

| Time | Dur | Msgs | LLM Credits | Call Credits | Total | LLM Cost | Topic |
|------|-----|------|------------|-------------|-------|------|-------|
| 11:14 | 601s | 34 | 7,109 | 3,598 | 10,707 | $1.56 | Painting Details Discussion |
| 10:34 | 601s | 39 | 6,379 | 3,630 | 10,009 | $1.40 | Art Discussion Museum |
| 10:24 | 601s | 37 | 5,086 | 3,914 | 9,000 | $1.12 | Art Descriptions & History |
| 11:34 | 606s | 27 | 4,430 | 2,703 | 7,133 | $0.98 | Rubens, Transport, De Vos |
| 11:23 | 602s | 25 | 3,776 | 2,767 | 6,543 | $0.83 | Rubens Paintings Discussion |
| 10:52 | 602s | 30 | 3,753 | 4,014 | 7,767 | $0.83 | Bruegel and Holbein |
| 10:54 | 602s | 31 | 3,756 | 3,723 | 7,479 | $0.83 | Bruegel Gemalde Beschreibungen |
| 11:04 | 603s | 26 | 2,751 | 3,254 | 6,005 | $0.61 | Vermeer's "Die Malkunst" |
| 10:44 | 603s | 15 | 2,696 | 3,924 | 6,620 | $0.59 | Maria Isabella, Maria Theresia |
| 10:37 | 474s | 26 | 2,538 | 2,926 | 5,464 | $0.56 | Art Descriptions |

---

## Appendix: Methodology

1. **Data Collection:** All conversation metadata and billing details fetched via ElevenLabs API (GET /v1/convai/conversations/ID) on 2026-04-06
2. **Hermann/Simone Separation:** Based on parallel conversation start times (<60s apart = different visitors) and the wiki-documented behavioral profiles (Hermann = longer, Simone = concise)
3. **10 ambiguous conversations** could not be reliably assigned and are reported separately
4. **Platform cost estimates** use ElevenLabs published plan rates divided by included minutes, which is an approximation — actual billing may vary based on credit consumption patterns
5. **"Wasted" tokens** are ElevenLabs' irreversible_generation category — tokens generated but not delivered to the user, typically due to user interruptions or agent restarts
