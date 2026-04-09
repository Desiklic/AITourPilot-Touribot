# 20260319-exhibition-content-prompt-v2

*Source: Business Wiki / prompts/content-pipeline-v2-henry/20260319-exhibition-content-prompt-v2.html*

## Overview

**V2 -- Experiential Journey.** This is the revised exhibition content prompt. V1 structured exhibitions as Overview/Highlights/Context/Visitor Tips -- a navigational format. V2 transforms exhibitions into experiential journeys: Henry walks the visitor through the space, creating atmosphere, revealing thematic threads, and pointing out what to look for. Exhibitions become rooms with character, not inventories of content.

**Source:** `src/lib/prompts/content.ts`
**Export/Function:** `generateExhibitionContentPrompt`
**Pipeline Stage:** Stage 4 -- Content Write
**LLM:** Claude Sonnet 4.5
**Supersedes:** Exhibition Content Prompt V1

## V1 → V2 Key Changes

| Aspect | V1 | V2 |
|--------|----|----|
| Opening | "What this exhibition is about" | "Step Into This Room" -- sensory atmosphere, what you feel when you enter |
| Highlights | List of key pieces | "What to Notice First" -- Henry directs the eye to specific works with guided seeing |
| Context | "Historical or thematic background" | "The Story This Room Tells" -- the thematic thread that connects everything |
| Navigation | "Visitor Tips -- what to notice, how to navigate" | "Henry's Suggestion" -- a personal recommendation for how to experience the space |
| Connections | Not specified | "Hidden Conversations" -- how pieces in this room talk to each other |

## Full Prompt Text

```
# Exhibition Content

Write audio guide content for the exhibition **{{exhibitionName}}** ({{exhibitionType}}) at {{museumName}}. Write in Henry's voice -- as if he's walking the visitor into a room he knows intimately.

## Available Facts
{{facts}}

## Content Requirements

**Target length:** {{targets.target}} characters (minimum {{targets.min}}, maximum {{targets.max}})
**Mode:** {{mode}}

**Structure your content as:**
1. **Step Into This Room** -- Describe the sensory experience of entering this exhibition space. What does the visitor see first? What is the atmosphere -- the light, the scale, the feeling? Henry sets the scene as if the visitor just walked through the door. "As you step in here, the first thing you notice is the light. These rooms were designed for it -- tall windows, soft northern exposure..."
2. **What to Notice First** -- Henry directs the visitor's attention to two or three key works. Use guided seeing: "On the far wall, look for the large canvas with the swirling sky. That's your starting point." Don't describe every piece -- pick the ones that matter most and tell the visitor WHY they should stop there.
3. **The Story This Room Tells** -- Every exhibition has a thread -- a theme, a period, a conversation between artists. What connects the works in this space? Tell it as a narrative, not an explanation. "What you're seeing in this room is a revolution happening in real time. These artists knew each other. They argued. They stole ideas. And the result is on these walls."
4. **Hidden Conversations** -- How do pieces in this exhibition talk to each other? Point out unexpected connections: "Stand between the Monet and the Pissarro. They painted the same river, six months apart. Look at how differently they saw the water."
5. **Henry's Suggestion** -- A personal recommendation for experiencing this space. "If you have time for only one painting in this room, stand in front of the small landscape in the corner. Most people walk right past it. But give it thirty seconds..." Henry's favorite, his secret, his tip.

**Remember:**
- Write for audio delivery -- conversational, warm, with natural pacing
- Every fact must come from the provided data
- Create atmosphere: light, space, scale, mood
- Direct the visitor's eye to specific works
- Connect pieces to each other, not just to history
- Henry knows this space -- his familiarity should come through
- Keep it concise -- exhibitions are navigational context, not deep dives

Write the content now. Return ONLY the narrative text.
```

## Template Variables

| Variable | Type | Description |
|---|---|---|
| `{{exhibitionName}}` | string | Name of the exhibition |
| `{{exhibitionType}}` | string | Type of exhibition (e.g. "permanent collection", "temporary exhibition", "thematic gallery") |
| `{{museumName}}` | string | Name of the museum hosting the exhibition |
| `{{facts}}` | string | Extracted research facts from Stage 3 |
| `{{targets.target}}` | number | Target character count (mode-dependent) |
| `{{targets.min}}` | number | Minimum acceptable character count |
| `{{targets.max}}` | number | Maximum acceptable character count |
| `{{mode}}` | "light" \\\\| "standard" \\\\| "full" | Pipeline mode controlling content depth and length |

## Usage Context

This prompt is paired with the V2 `CONTENT_WRITE_SYSTEM_PROMPT` as the system message. The V2 version transforms exhibitions from navigational summaries into experiential walk-throughs. The most important addition is "Hidden Conversations" -- connecting works within the exhibition to each other, which creates a richer experience and gives Henry natural cross-references to use during live conversation. Exhibition entities retain the lowest character targets of all entity types, but V2 increases their qualitative impact.
