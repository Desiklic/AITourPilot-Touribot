# 20260319-content-rewrite-voice-prompts-v1

*Source: Business Wiki / prompts/content-pipeline-v1/20260319-content-rewrite-voice-prompts-v1.html*

## Overview

Stage 4 (Content Write) is where structured research becomes finished audio guide prose. This stage runs multiple prompts in sequence: first generating original content from facts, then optimizing it for spoken delivery, and finally scoring the result for conversational quality. A special anti-meta instruction is available as a retry mechanism when the LLM produces meta-commentary instead of actual content. This document covers prompts from two source files that work together in this stage.

**Sources:** `src/lib/prompts/rewrite.ts`, `src/lib/prompts/voice-optimize.ts`, `src/pipeline/stages/04-content-write.ts`
**Pipeline Stage:** Stage 4 -- Content Write (rewrite pass)
**LLM:** Claude (via Anthropic API)

## Content Generation Prompt

**Export:** `CONTENT_GENERATION_PROMPT` (from `rewrite.ts`)

This is the primary content writing prompt. It takes structured facts and discovery notes for a single entity and produces 3-5 paragraphs of original, voice-optimized audio guide content. The critical constraint is that the LLM writes from facts, never from source text.

```
You are writing original content for an AI-powered conversational museum audio guide.

CRITICAL RULES:
- Write ORIGINAL prose -- do not paraphrase any source
- You are writing from STRUCTURED FACTS, not from source text
- The content should be conversational, warm, and engaging
- Use short sentences suitable for audio delivery
- Include emotional hooks ("Imagine standing here in 1889...")
- Be factually precise -- every claim must trace to the provided facts

Entity: {{entityName}} ({{entityType}})
Museum: {{museumName}}

Structured Facts:
{{factsJson}}

Discoveries (proprietary):
{{discoveriesJson}}

Write 3-5 paragraphs of voice-optimized content for this entity.
```

## Voice Optimization Prompt

**Export:** `VOICE_OPTIMIZATION_PROMPT` (from `rewrite.ts`)

After content is generated, this prompt refines it for spoken delivery. It enforces strict sentence length limits, removes written-language patterns, and adds conversational bridges.

```
Optimize this content for conversational audio delivery.

Rules:
- Maximum 15 words per sentence
- No parenthetical asides
- Replace "the aforementioned" type language with natural references
- Add conversational bridges ("Now, here's what makes this special...")
- Ensure natural speech rhythm when read aloud

Content:
{{content}}

Return the voice-optimized version.
```

## Conversational Quality Check Prompt

**Export:** `CONVERSATIONAL_QUALITY_CHECK` (from `voice-optimize.ts`)

This scoring prompt evaluates the voice-optimized content across five dimensions, returning a structured JSON score. It is used to decide whether content meets the quality bar or needs another optimization pass.

```
Rate this content for conversational audio quality.

Criteria (1-10 each):
1. Natural speech rhythm (sounds good when read aloud)
2. Sentence length (target: 8-15 words average)
3. Engagement hooks (questions, reveals, emotional beats)
4. Jargon avoidance (accessible to general audience)
5. Flow between topics (smooth transitions)

Content:
---
{{content}}
---

Respond with JSON: { "scores": { "rhythm": number, "length": number, "engagement": number, "accessibility": number, "flow": number }, "overall": number, "suggestions": string[] }
```

## Anti-Meta Instruction (Retry Only)

**Constant:** `ANTI_META_INSTRUCTION` (from `04-content-write.ts`)

This instruction is **not** part of the initial prompt. It is appended to the user prompt only on retry, when the LLM's first response was detected as meta-commentary (e.g., "I notice the facts are limited...") instead of actual audio guide content. It forces the model to write confidently even with sparse facts.

```
CRITICAL INSTRUCTION: You MUST write actual audio guide content. Do NOT:
- Say "I notice" or "I don't have enough information"
- Apologize or hedge about missing facts
- Talk about the task itself
- Refuse to write content

Even if the facts are limited, write an engaging audio guide entry. Use the museum context, the entity name, and any available facts. Focus on what makes this entity interesting to a visitor. If you know nothing specific, describe the type of artifact/person/exhibition in the context of this museum and what a visitor might appreciate about it. Write confidently in second person ("As you stand before...").
```

> This is a user-prompt-only appendage. It is never added to the system prompt. The retry mechanism detects meta-responses by looking for phrases like "I notice", "I don't have", or "unfortunately" in the LLM output.

## Template Variables

| Variable | Prompt | Description |
|----------|--------|-------------|
| `{{entityName}}` | Content Generation | Name of the entity (artwork, person, etc.) |
| `{{entityType}}` | Content Generation | Type: museum, artifact, person, or exhibition |
| `{{museumName}}` | Content Generation | Name of the parent museum |
| `{{factsJson}}` | Content Generation | JSON array of structured fact triples from Stage 2 |
| `{{discoveriesJson}}` | Content Generation | JSON of proprietary discovery notes |
| `{{content}}` | Voice Optimization, Quality Check | The generated or optimized content text |

## Usage Context

These prompts form a three-step chain within Stage 4. First, `CONTENT_GENERATION_PROMPT` produces raw audio guide prose from structured facts. Second, `VOICE_OPTIMIZATION_PROMPT` refines it for spoken delivery. Third, `CONVERSATIONAL_QUALITY_CHECK` scores the result. If the initial generation produces meta-commentary instead of content, the `ANTI_META_INSTRUCTION` is appended and the generation is retried. The final voice-optimized content proceeds to Stage 7 (Data Structure) for ElevenLabs knowledge base formatting.
