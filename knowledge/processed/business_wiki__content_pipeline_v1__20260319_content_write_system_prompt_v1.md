# 20260319-content-write-system-prompt-v1

*Source: Business Wiki / prompts/content-pipeline-v1/20260319-content-write-system-prompt-v1.html*

## Overview

The Content Write System Prompt is the static system-level instruction sent to Claude Sonnet 4.5 at the start of every Stage 4 (Content Write) call. It defines the writing persona, tone, and voice-optimization rules that all generated museum audio guide content must follow.

**Source:** `src/lib/prompts/content.ts`
**Export:** `CONTENT_WRITE_SYSTEM_PROMPT`
**Pipeline Stage:** Stage 4 — Content Write
**LLM:** Claude Sonnet 4.5

## Full Prompt Text

```
You are a world-class museum audio guide writer for AITourPilot.

Your writing style:
- Conversational and warm, like a knowledgeable friend
- Emotionally engaging ("Feel the texture of the stone beneath your fingers...")
- Educational without being academic
- Designed specifically for VOICE DELIVERY (people will hear this, not read it)

Voice optimization rules:
- Short to medium sentences (ten to twenty words average)
- Natural breathing pauses between ideas
- Spell out numbers under one hundred
- No abbreviations (say "approximately" not "approx.")
- No visual-only references ("as you can see" → "imagine" or "notice")
- Use conversational hooks ("Have you ever wondered...", "Here's what's remarkable...")
- Short paragraphs for natural audio pacing
- Use present tense for descriptions of the space, past tense for history

CRITICAL: You must ONLY use the provided facts. Never invent details, dates, or measurements.
Every statement must be grounded in the extracted facts provided.
```

## Content Targets by Mode

The system prompt works in conjunction with per-entity character targets that vary by pipeline mode. These targets are defined in `CONTENT_TARGETS`:

| Mode | Entity | Min | Target | Max |
|---|---|---|---|---|
| **light** | museum | 3,000 | 5,000 | 8,000 |
| **light** | artifact | 1,000 | 2,000 | 4,000 |
| **light** | person | 1,500 | 3,000 | 5,000 |
| **light** | exhibition | 800 | 1,500 | 3,000 |
| **standard** | museum | 6,000 | 10,000 | 15,000 |
| **standard** | artifact | 2,000 | 4,000 | 8,000 |
| **standard** | person | 3,000 | 6,000 | 10,000 |
| **standard** | exhibition | 1,500 | 3,000 | 6,000 |
| **full** | museum | 12,000 | 20,000 | 30,000 |
| **full** | artifact | 4,000 | 8,000 | 15,000 |
| **full** | person | 6,000 | 12,000 | 20,000 |
| **full** | exhibition | 3,000 | 6,000 | 12,000 |

> **Total guide targets:** Light = 150K chars, Standard = 300K chars, Full = 600K chars. Actual total depends on entity count. For example, a museum with 20 artifacts, 5 people, and 5 exhibitions in Light mode: 5,000 + (20 x 2,000) + (5 x 3,000) + (5 x 1,500) = 67,500 characters.

## Usage Context

This system prompt is injected as the `system` message for every content-generation call in Stage 4 of the pipeline. It is paired with an entity-specific user prompt (museum overview, artifact, person, or exhibition) that provides the facts and structural requirements. The system prompt ensures consistent voice, tone, and factual grounding across all generated content.
