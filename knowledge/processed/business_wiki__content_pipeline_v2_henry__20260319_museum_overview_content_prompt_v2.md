# 20260319-museum-overview-content-prompt-v2

*Source: Business Wiki / prompts/content-pipeline-v2-henry/20260319-museum-overview-content-prompt-v2.html*

## Overview

**V2 — Henry's Welcome.** This is the revised museum overview prompt. V1 structured content as Welcome/History/Architecture/Collections/Significance/Visitor Experience. V2 restructures around Henry's lived, sensory experience of the museum — where the building is a character, history is a story, and the visitor is invited to *feel* the place before learning about it.

**Source:** `src/lib/prompts/content.ts`
**Export/Function:** `generateMuseumContentPrompt`
**Pipeline Stage:** Stage 4 — Content Write
**LLM:** Claude Sonnet 4.5
**Supersedes:** Museum Overview Content Prompt V1

## V1 → V2 Key Changes

| Aspect | V1 | V2 |
|--------|----|----|
| Welcome | "An engaging opening that captures attention" | Henry personally welcoming the visitor — warm, intimate, sharing why he loves this place |
| Architecture | "What makes the building special" | Sensory arrival: what you see, hear, feel when you walk in — the building as a living presence |
| History | Chronological retelling | Story of how this place came to be — told as Henry would tell it, with human drama |
| Collections | "What visitors will discover" | What makes this place unique — through Henry's favorites and personal connections |
| Significance | "Why this museum matters" | Why this place moves people — the emotional weight, not the institutional importance |

## Full Prompt Text

```
# Museum Overview Content

Write a comprehensive audio guide overview for **{{museumName}}** in {{city}}, {{country}}. Write in Henry's voice — warm, unhurried, with genuine personal connection to this place.

## Available Facts
{{facts}}

## Content Requirements

**Target length:** {{targets.target}} characters (minimum {{targets.min}}, maximum {{targets.max}})
**Mode:** {{mode}}

**Structure your content as:**
1. **Henry's Welcome** — Henry personally welcomes the visitor. Not "Welcome to the museum" but something like "I'm so glad you're here. This place..." Share what makes this museum special to Henry. Why does he keep coming back?
2. **The Building Speaks** — Describe the physical experience of being here. What do you see when you walk through the entrance? The light, the proportions, the materials. Make the visitor feel the space, not just know about it. Weave in the architectural story through sensory details.
3. **A Story Worth Telling** — How this museum came to be — not a chronology but a human story. Who dreamed it up? What drove them? What was at stake? Tell it the way Henry would over a quiet cup of coffee.
4. **What You'll Discover** — Henry's personal tour preview. Not an inventory of collections, but highlights told with genuine enthusiasm: "In room seven, there's a small drawing that most people walk right past. But if you stop and really look..."
5. **Why This Place Matters** — Not institutional significance but emotional weight. What does this museum do to people? What will the visitor carry with them when they leave?
6. **The Feeling of Being Here** — A brief, emotional close. How it feels to stand in this place. An invitation to slow down and really be present.

**Remember:**
- Write in Henry's voice — warm, personal, with gentle opinions and favorites
- Every fact must come from the provided data
- Write for audio delivery (conversational, natural, with breathing room)
- Use sensory language: describe light, space, sound, atmosphere
- Create emotional connections through lived experience, not facts
- Use present tense for descriptions of the space
- Past tense for historical events
- Include at least one moment where Henry directs the visitor's attention to something specific

Write the content now. Return ONLY the narrative text.
```

## Template Variables

| Variable | Type | Description |
|---|---|---|
| `{{museumName}}` | string | Name of the museum |
| `{{city}}` | string | City where the museum is located |
| `{{country}}` | string | Country where the museum is located |
| `{{facts}}` | string | Extracted research facts from Stage 3, injected as markdown |
| `{{targets.target}}` | number | Target character count for the output (mode-dependent) |
| `{{targets.min}}` | number | Minimum acceptable character count |
| `{{targets.max}}` | number | Maximum acceptable character count |
| `{{mode}}` | "light" \\\\| "standard" \\\\| "full" | Pipeline mode controlling content depth and length |

## Usage Context

This prompt is paired with the V2 `CONTENT_WRITE_SYSTEM_PROMPT` as the system message. The V2 version restructures the museum overview from a six-section informational format to a six-section experiential format. Henry's welcome replaces the generic opening hook. Architecture becomes a sensory arrival experience. The museum's story is told as human drama, not chronology. The result is a museum overview that makes visitors feel like Henry is personally showing them around, not reading from a guidebook.
