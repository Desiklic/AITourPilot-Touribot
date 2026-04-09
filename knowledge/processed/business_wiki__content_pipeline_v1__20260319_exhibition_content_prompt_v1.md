# 20260319-exhibition-content-prompt-v1

*Source: Business Wiki / prompts/content-pipeline-v1/20260319-exhibition-content-prompt-v1.html*

## Overview

The Exhibition Content Prompt generates audio guide narration for exhibitions (permanent galleries, temporary shows, thematic sections) within a museum. It is produced by `generateExhibitionContentPrompt` in Stage 4 (Content Write) and instructs Claude Sonnet 4.5 to write a concise narrative covering the exhibition's overview, highlights, context, and visitor tips.

**Source:** `src/lib/prompts/content.ts`
**Export/Function:** `generateExhibitionContentPrompt`
**Pipeline Stage:** Stage 4 — Content Write
**LLM:** Claude Sonnet 4.5

## Full Prompt Text

```
# Exhibition Content

Write audio guide content for the exhibition **{{exhibitionName}}** ({{exhibitionType}}) at {{museumName}}.

## Available Facts
{{facts}}

## Content Requirements

**Target length:** {{targets.target}} characters (minimum {{targets.min}}, maximum {{targets.max}})
**Mode:** {{mode}}

**Structure your content as:**
1. **Overview** — What this exhibition is about
2. **Highlights** — Key pieces or themes to look for
3. **Context** — Historical or thematic background
4. **Visitor Tips** — What to notice, how to navigate the space

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

This prompt is paired with the `CONTENT_WRITE_SYSTEM_PROMPT` as the system message. The function `generateExhibitionContentPrompt` constructs the user prompt by injecting the exhibition's name, type, parent museum name, research facts, and mode-appropriate character targets. Exhibition entities receive the lowest character targets of all entity types (e.g. 1,500 target in Light mode) because they serve as navigational context rather than deep-dive content. This is the most concise of the four content prompts, with only four structural sections compared to five or six in the other prompts.
