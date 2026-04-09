# 20260319-person-biography-content-prompt-v1

*Source: Business Wiki / prompts/content-pipeline-v1/20260319-person-biography-content-prompt-v1.html*

## Overview

The Person Biography Content Prompt generates audio guide narration for notable people connected to a museum — artists, founders, patrons, architects, and other key figures. It is produced by `generatePersonContentPrompt` in Stage 4 (Content Write) and instructs Claude Sonnet 4.5 to write a human narrative covering the person's life, achievements, museum connection, and legacy.

**Source:** `src/lib/prompts/content.ts`
**Export/Function:** `generatePersonContentPrompt`
**Pipeline Stage:** Stage 4 — Content Write
**LLM:** Claude Sonnet 4.5

## Full Prompt Text

```
# Person Biography Content

Write audio guide biography content for **{{personName}}** ({{role}}) connected to {{museumName}}.

## Available Facts
{{facts}}

## Content Requirements

**Target length:** {{targets.target}} characters (minimum {{targets.min}}, maximum {{targets.max}})
**Mode:** {{mode}}

**Structure your content as:**
1. **Introduction** — Who this person is and why they matter here
2. **Life Story** — Key biographical details, told as a narrative
3. **Creative Vision or Achievement** — What made them remarkable
4. **Connection to Museum** — Their specific relationship to this place
5. **Legacy** — How their work continues to influence today

**Remember:**
- Tell their story as a human narrative, not an encyclopedia entry
- Include personal details that make them relatable
- Connect their story to what visitors can see or experience
- Be respectful and culturally sensitive

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
| `{{mode}}` | "light" \\\\| "standard" \\\\| "full" | Pipeline mode controlling content depth and length |

## Usage Context

This prompt is paired with the `CONTENT_WRITE_SYSTEM_PROMPT` as the system message. The function `generatePersonContentPrompt` constructs the user prompt by injecting the person's name, role, parent museum name, research facts, and mode-appropriate character targets. Person entities receive higher character targets than artifacts (e.g. 3,000 target in Light mode vs. 2,000 for artifacts) because biographical narratives require more context to be engaging.
