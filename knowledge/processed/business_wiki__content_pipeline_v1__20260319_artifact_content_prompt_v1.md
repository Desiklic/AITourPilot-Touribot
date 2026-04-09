# 20260319-artifact-content-prompt-v1

*Source: Business Wiki / prompts/content-pipeline-v1/20260319-artifact-content-prompt-v1.html*

## Overview

The Artifact Content Prompt generates audio guide narration for individual artifacts, artworks, or features within a museum. It is produced by `generateArtifactContentPrompt` in Stage 4 (Content Write) and instructs Claude Sonnet 4.5 to write a structured narrative covering first impressions, creation story, technical details, significance, and visitor connection.

**Source:** `src/lib/prompts/content.ts`
**Export/Function:** `generateArtifactContentPrompt`
**Pipeline Stage:** Stage 4 — Content Write
**LLM:** Claude Sonnet 4.5

## Full Prompt Text

```
# Artifact Content

Write audio guide content for **{{artifactName}}**{{descriptor}} at {{museumName}}.

## Available Facts
{{facts}}

## Content Requirements

**Target length:** {{targets.target}} characters (minimum {{targets.min}}, maximum {{targets.max}})
**Mode:** {{mode}}

**Structure your content as:**
1. **First Impression** — What catches your attention
2. **Creation Story** — Who made it, when, why
3. **Technical Details** — Materials, techniques, dimensions woven into narrative
4. **Significance** — Why this piece matters
5. **Connection** — Relate it to the visitor's experience or broader context

**Remember:**
- Ground every statement in provided facts
- Make technical details accessible and interesting
- Create a sense of wonder and discovery
- Use sensory language where appropriate

Write the content now. Return ONLY the narrative text.
```

> **Note on the descriptor:** The `{{descriptor}}` is dynamically built from the artifact's type, year created, and medium. For example, an artifact of type "painting" created in "1889" with medium "oil on canvas" would produce the descriptor ` (painting, 1889, oil on canvas)`. If the type is "unknown", it is omitted. If no metadata is available, the descriptor is empty.

## Template Variables

| Variable | Type | Description |
|---|---|---|
| `{{artifactName}}` | string | Name of the artifact or artwork |
| `{{descriptor}}` | string | Auto-built from type + yearCreated + medium, e.g. `(painting, 1889, oil on canvas)` |
| `{{museumName}}` | string | Name of the museum housing the artifact |
| `{{facts}}` | string | Extracted research facts from Stage 3 |
| `{{targets.target}}` | number | Target character count (mode-dependent) |
| `{{targets.min}}` | number | Minimum acceptable character count |
| `{{targets.max}}` | number | Maximum acceptable character count |
| `{{mode}}` | "light" \\\\| "standard" \\\\| "full" | Pipeline mode controlling content depth and length |

## Usage Context

This prompt is paired with the `CONTENT_WRITE_SYSTEM_PROMPT` as the system message. The function `generateArtifactContentPrompt` constructs the user prompt by injecting the artifact's name, a dynamically-built descriptor string, the parent museum name, research facts, and mode-appropriate character targets. Artifacts are the most numerous entity type in a typical museum guide, so this prompt is called many times per pipeline run.
