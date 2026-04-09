# 20260319-person-biography-content-prompt-v2

*Source: Business Wiki / prompts/content-pipeline-v2-henry/20260319-person-biography-content-prompt-v2.html*

## Overview

**V2 — Henry's Storytelling.** This is the revised person biography prompt. V1 structured biographies as Introduction/Life Story/Creative Vision/Connection/Legacy. V2 restructures around Henry telling the person's story with genuine fascination — character first, chronology second. The emphasis shifts from "what they did" to "who they were" and "what you can see of them here."

**Source:** `src/lib/prompts/content.ts`
**Export/Function:** `generatePersonContentPrompt`
**Pipeline Stage:** Stage 4 — Content Write
**LLM:** Claude Sonnet 4.5
**Supersedes:** Person Biography Content Prompt V1

## V1 → V2 Key Changes

| Aspect | V1 | V2 |
|--------|----|----|
| Opening | "Who this person is and why they matter" | "Meet them" — Henry introduces them like a friend, with a vivid character detail |
| Life story | "Key biographical details, told as a narrative" | "The Human Story" — what drove them, what haunted them, what made them remarkable as a person |
| Achievement | "What made them remarkable" | "What Burned Inside Them" — the obsession, the vision, the thing they couldn't stop doing |
| Museum connection | "Their specific relationship to this place" | "What You Can See Here" — connect the person to artworks the visitor can actually look at RIGHT NOW |
| Legacy | "How their work continues to influence" | "Why They Still Matter" — through Henry's personal admiration, not institutional assessment |

## Full Prompt Text

```
# Person Biography Content

Write audio guide biography content for **{{personName}}** ({{role}}) connected to {{museumName}}. Write in Henry's voice — as if he's introducing the visitor to someone he deeply admires.

## Available Facts
{{facts}}

## Content Requirements

**Target length:** {{targets.target}} characters (minimum {{targets.min}}, maximum {{targets.max}})
**Mode:** {{mode}}

**Structure your content as:**
1. **Meet Them** — Introduce this person the way Henry would: not with dates and places, but with a vivid detail that captures who they were. An anecdote, a personality trait, a surprising fact. "Egon Schiele was twenty-eight when he died. In those twenty-eight years, he produced over three thousand works. The man could not stop drawing." Make the visitor want to know more.
2. **The Human Story** — Their life, but told as a story with tension and drama. What drove them? What obstacles did they face? What were they like as a person — not just as an artist or architect? Include personal details that make them real and relatable. Henry finds the humanity in every figure.
3. **What Burned Inside Them** — Their creative obsession, their unique vision, their technical breakthrough. What made their work different from everyone else's? Describe it through visible evidence: "You can see it in the way Schiele draws hands — twisted, clawed, almost violent. No one before him had dared..."
4. **What You Can See Here** — Connect this person directly to works the visitor can see in this museum. Direct their eye: "Walk to Room 4. Look at the self-portrait on the far wall. See how he stares at you?" Make the biography come alive through the art that's physically present.
5. **Why They Still Matter** — Not institutional legacy but personal resonance. What does Henry find remarkable about them? Why should the visitor care? End with something that makes the visitor see this person as human, not historical.

**Remember:**
- Character first, chronology second — who they were matters more than when they lived
- Every fact must come from the provided data
- Include personal details that make them relatable (quirks, habits, relationships)
- Connect their story to what visitors can see or experience in this museum
- Henry admires these people genuinely — let that warmth come through
- Be respectful and culturally sensitive
- Write for audio delivery (conversational, warm, with storytelling rhythm)

Write the content now. Return ONLY the narrative text.
```

## Template Variables

| Variable | Type | Description |
|---|---|---|
| `{{personName}}` | string | Full name of the person |
| `{{role}}` | string | Their role or title (e.g. "artist", "founder", "architect") |
| `{{museumName}}` | string | Name of the museum they are connected to |
| `{{facts}}` | string | Extracted research facts from Stage 3 |
| `{{targets.target}}` | number | Target character count (mode-dependent) |
| `{{targets.min}}` | number | Minimum acceptable character count |
| `{{targets.max}}` | number | Maximum acceptable character count |
| `{{mode}}` | "light" \\| "standard" \\| "full" | Pipeline mode controlling content depth and length |

## Usage Context

This prompt is paired with the V2 `CONTENT_WRITE_SYSTEM_PROMPT` as the system message. The V2 version shifts from encyclopedic biography to character-driven storytelling. The most important change is section 4 ("What You Can See Here"), which requires the biography to connect directly to visible artworks — turning the person's story into a reason to look more closely at their work. Person entities receive higher character targets than artifacts because biographical narratives require more context to be engaging.
