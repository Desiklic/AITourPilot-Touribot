# 20260405-henry-remembers-cross-session-conversation-memory

*Source: Business Wiki / technical/20260405-henry-remembers-cross-session-conversation-memory.html*

## Executive Summary

Every press of the Start button creates a new ElevenLabs conversation with zero memory of prior sessions. Henry greets returning visitors as strangers -- even if they pressed Stop 30 seconds ago. This document defines the production-grade plan to give Henry persistent memory.

**Architecture:** dynamic_variables injection (ElevenLabs' recommended personalization method)
**Storage:** AsyncStorage (device-local, privacy-first, GDPR-compliant by design)
**Summarization:** Server-side Claude Haiku 4.5 via Content Factory endpoint (~$0.0001/session)

---

## The Problem

During a visit to the Kunsthistorisches Museum Wien (Mar 24, 2026), the user observed 25+ separate conversation transcripts -- many under 1 minute. Each Start/Stop creates a fresh ElevenLabs WebSocket session. The agent has no memory of prior exchanges.

This is the dominant museum visitor behavior pattern ("Code Hunting" -- stop/start per artwork, ~75% of visitors). British Museum research confirms: visitors don't use audio guides linearly. They trigger the guide at each interesting artwork, then move on.

The amnesia is not a bug -- it is the direct consequence of how ElevenLabs' stateless session architecture works. Each WebSocket is an independent server-side session. There is no API to resume a previous conversation.

---

## Architecture

### Session End Flow
```
conversationHistory (in-memory, last 20 turns)
  -> POST /api/public/summarize-visit (Content Factory)
  -> Claude Haiku 4.5 extracts structured summary (~300 chars)
  -> AsyncStorage.setItem('visitor_memory:{museumId}:{lang}', summary)
  -> Fire-and-forget (never blocks the stop flow)
```

### Session Start Flow
```
AsyncStorage.getItem('visitor_memory:{museumId}:{lang}')
  -> inject into dynamic_variables.prior_conversation_summary
  -> ElevenLabs substitutes into {{prior_conversation_summary}} placeholder
  -> Henry naturally acknowledges returning visitor
```

### Why dynamic_variables (Not prompt override)

| Factor | dynamic_variables | conversation_config_override |
|--------|-------------------|------------------------------|
| Behavior | Fills placeholder in existing prompt | REPLACES entire prompt |
| Prompt maintenance | Factory owns prompt | Must replicate Henry's full prompt client-side |
| RAG impact | None | Risk of breaking KB retrieval |
| ElevenLabs recommendation | Preferred method | For advanced scenarios only |

---

## Implementation Phases

### Phase 1: Prompt Foundation (2-3 hours)
- Add {{prior_conversation_summary}} to all agent system prompts
- Bulk-patch 140 existing agents via ElevenLabs API
- Pass empty string initially -- zero user impact

### Phase 2: Memory Storage (3-4 hours)
- New VisitorMemoryService.ts (AsyncStorage read/write, expiry)
- New Content Factory endpoint: POST /api/public/summarize-visit
- Claude Haiku 4.5 generates structured summaries

### Phase 3: Wire Lifecycle (2-3 hours)
- stopConversation() emits history via callback
- startConversation() loads memory and injects into dynamic_variables
- Fix attemptReconnect() to use dynamic_variables instead of prompt override

### Phase 4: UX Polish (1-2 hours)
- "Clear visit history" in Settings
- Memory invalidation when museum content is re-run
- Auto-expiry after 6 months

**Total: 8-12 hours of implementation**

---

## UX Design

### Greeting Behavior

| Visit | Henry's Behavior |
|-------|------------------|
| First | Standard welcome |
| Second | "Welcome back! [theme] resonated last time -- want to go deeper or explore something new?" |
| Third+ | Calibrated depth without announcement; subtly references prior interests |
| After 6+ month gap | "It's been a while! Great to have you back." |

### Guardrails
- Never quote timestamps, session counts, or verbatim from previous conversations
- Never frame memory as surveillance ("I noticed..." / "Based on your data...")
- Always frame as care ("I've been thinking about that Caravaggio we discussed...")
- Acknowledge return ONCE, then move on naturally
- Always offer the choice to start fresh

### Privacy (GDPR-First)
- On-device storage only -- no server-side PII
- No raw transcripts stored -- only LLM-compressed interest summaries
- Auto-expiry after 6 months
- "Clear visit history" option (right to erasure)

---

## Competitive Position

| Product | Cross-Session Memory | Voice AI | Museum-Specific |
|---------|---------------------|----------|------------------|
| Smartify (SAAM) | No | No | Yes |
| Bloomberg Connects | No | No | Yes |
| Google Arts & Culture | No | Experimental | Yes |
| ChatGPT Voice | Account-level only | Yes | No |
| **Henry (AITourPilot)** | **Yes** | **Yes** | **Yes** |

Henry will be the first AI museum guide with cross-session conversational memory.

---

## Technical Reference

Full implementation plan with line-by-line code references, downstream impact analysis, risk areas, and rollback approach: `docs_dev/20260405_AGENT_MEMORY_IMPLEMENTATION_PLAN.md` in the AITourPilot4 repository.
