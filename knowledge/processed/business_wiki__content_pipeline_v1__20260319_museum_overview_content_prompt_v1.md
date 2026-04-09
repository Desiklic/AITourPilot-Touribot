# 20260319-museum-overview-content-prompt-v1

*Source: Business Wiki / prompts/content-pipeline-v1/20260319-museum-overview-content-prompt-v1.html*

## Overview

The Museum Overview Content Prompt generates the main introductory audio guide content for a museum. It is called by `generateMuseumContentPrompt` in Stage 4 (Content Write) and instructs Claude Sonnet 4.5 to produce a structured narrative covering the museum's history, architecture, collections, and cultural significance.

**Source:** `src/lib/prompts/content.ts`
**Export/Function:** `generateMuseumContentPrompt`
**Pipeline Stage:** Stage 4 — Content Write
**LLM:** Claude Sonnet 4.5

## Full Prompt Text

```
# Museum Overview Content

Write a comprehensive audio guide overview for **{{museumName}}** in {{city}}, {{country}}.

## Available Facts
{{facts}}

## Content Requirements

**Target length:** {{targets.target}} characters (minimum {{targets.min}}, maximum {{targets.max}})
**Mode:** {{mode}}

**Structure your content as:**
1. **Welcome & Hook** — An engaging opening that captures attention
2. **History & Origins** — How the museum came to be
3. **Architecture & Space** — What makes the building or space special
4. **Collections & Highlights** — What visitors will discover
5. **Cultural Significance** — Why this museum matters
6. **Visitor Experience** — What to expect and feel

**Remember:**
- Every fact must come from the provided data
- Write for audio delivery (conversational, warm, engaging)
- Create emotional connections ("Imagine standing where...")
- Use present tense for descriptions of the space
- Past tense for historical events

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

This prompt is paired with the `CONTENT_WRITE_SYSTEM_PROMPT` as the system message. The function `generateMuseumContentPrompt` constructs this user-level prompt by injecting the museum's metadata, research facts, and mode-appropriate character targets. It produces the museum's main overview — typically the first piece of content a visitor hears when starting a guide.
