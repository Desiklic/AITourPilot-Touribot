# 20260319-copyright-compliance-prompts-v1

*Source: Business Wiki / prompts/content-pipeline-v1/20260319-copyright-compliance-prompts-v1.html*

## Overview

The **Copyright & Compliance** prompts power **Stage 3** of the AI Tour Pilot content pipeline. After research and discovery generate draft content, Stage 3 ensures that all output is **legally safe** — sufficiently transformative from source material, free of copied expression, and factually accurate.

The module spans **two source files** containing a total of **five prompts**:

| # | Prompt | Source File | Purpose |
|---|--------|-------------|---------|
| 1 | COPYRIGHT_SYSTEM_PROMPT | `copyright.ts` | System prompt establishing the copyright analyst role |
| 2 | generateCopyrightCheckPrompt | `copyright.ts` | Full copyright assessment of generated vs. source content |
| 3 | generateSimilarityCheckPrompt | `copyright.ts` | Textual overlap and similarity analysis |
| 4 | CC_BY_SA_CHECK_PROMPT | `copyright-check.ts` | CC-BY-SA expression derivation check |
| 5 | FACTUAL_VERIFICATION_PROMPT | `copyright-check.ts` | Factual accuracy verification |

Key design principles across all copyright prompts:

- **Traffic-light verdicts** — GREEN / YELLOW / RED classification for fast pipeline decisions
- **Quantitative thresholds** — specific percentage cutoffs (e.g., <15% textual overlap for GREEN)
- **Cautious defaults** — "when in doubt, classify as YELLOW"
- **JSON output** — structured responses for automated pipeline processing
- **Zod schemas** — TypeScript runtime validation on all LLM responses

> **Source files:** `src/lib/prompts/copyright.ts` and `src/lib/prompts/copyright-check.ts` in the AITourPilot-content-factory repository.

## Copyright System Prompt

This is the **system-level prompt** that establishes the LLM's role as a copyright compliance analyst. It is sent as the system message alongside all copyright assessment tasks.

**Source:** `copyright.ts` — `COPYRIGHT_SYSTEM_PROMPT` (lines 39–50)

```
You are a copyright compliance analyst for AITourPilot, a conversational AI audio guide system.

Your role is to assess whether generated content is sufficiently transformative from source material to avoid copyright infringement.

Key legal principles:
1. FACTS are not copyrightable. Only creative EXPRESSION is protected.
2. The CC-BY-SA firewall: structured fact extraction from Wikipedia/CC sources severs the expression chain.
3. Paraphrasing alone may not be sufficient — content must be independently created from facts.
4. Museum domain content (official websites, audio guides) requires extra caution: facts only, no expression.
5. Threshold: <15% textual similarity AND <0.50 semantic similarity required for GREEN status.

Always err on the side of caution. When in doubt, classify as YELLOW.
```

This prompt encodes the five legal principles that govern all downstream copyright decisions. Principle #2 (the CC-BY-SA firewall) is particularly important — it defines the architectural approach of extracting structured facts first, then generating original prose from those facts.

## Copyright Assessment Prompt

This prompt performs a **full copyright assessment** comparing generated content against its source material. It classifies the result as GREEN, YELLOW, or RED and recommends an action (approve, paraphrase, or block).

**Source:** `copyright.ts` — `generateCopyrightCheckPrompt()` (lines 66–103)

```
# Copyright Assessment Task

## Generated Content (to check)
${generatedContent.slice(0, 3000)}

## Original Source Text
${sourceText.slice(0, 3000)}

## Source Metadata
- License: ${sourceLicense}
- Source type: ${sourceType}
- Is museum's own domain: ${isMuseumDomain ? "YES -- extra caution required, facts only" : "No"}

## Your Task

Assess whether the generated content is sufficiently transformative from the source material.

**Classification criteria:**
- **GREEN**: Content is clearly original. Uses only facts from source. No copied phrases or sentence structures. <15% textual overlap.
- **YELLOW**: Content is mostly original but has some similar phrasing or structure. Needs paraphrasing. 15-30% overlap or similar structure.
- **RED**: Content too closely mirrors source expression. Copied phrases, identical structure, or >30% overlap. Must be blocked and rewritten.

${isMuseumDomain ? "**IMPORTANT: This is museum-domain content. ONLY structured facts may be used. Any prose similarity -> RED.**" : ""}

Return a JSON object:

json
{
  "verdict": "green|yellow|red",
  "reasoning": "explanation of your assessment",
  "transformativeElements": ["list of ways the content is original"],
  "problematicElements": ["list of concerning similarities"],
  "suggestedAction": "approve|paraphrase|block",
  "confidenceScore": 0.0-1.0
}

Return ONLY the JSON object.
```

### Template Variables

| Variable | Type | Description |
|----------|------|-------------|
| `generatedContent` | `string` | The generated content to check (truncated to 3000 chars) |
| `sourceText` | `string` | The original source material (truncated to 3000 chars) |
| `sourceLicense` | `string` | License of the source (e.g., "CC-BY-SA", "All Rights Reserved") |
| `sourceType` | `string` | Type of source (e.g., "Wikipedia", "museum website", "academic paper") |
| `isMuseumDomain` | `boolean` | Whether the source is from the museum's own domain |

### Output Schema (Zod-validated)

```
{
  verdict: "green" | "yellow" | "red",
  reasoning: string,
  transformativeElements: string[],
  problematicElements: string[],
  suggestedAction: "approve" | "paraphrase" | "block",
  confidenceScore: number (0-1)
}
```

## Similarity Check Prompt

This prompt performs a **focused textual similarity analysis** between generated and source text. It is lighter-weight than the full copyright check and focuses specifically on overlap percentages and shared phrases.

**Source:** `copyright.ts` — `generateSimilarityCheckPrompt()` (lines 113–143)

```
# Similarity Analysis Task

Compare these two texts and assess their similarity.

## Text A (Generated Content)
${generatedText.slice(0, 2000)}

## Text B (Source Material)
${sourceText.slice(0, 2000)}

## Your Task

Analyze textual overlap between the two texts.

Return a JSON object:

json
{
  "textualOverlapPercent": <0-100>,
  "sharedPhrases": ["exact or near-exact phrases shared between texts"],
  "verdict": "green|yellow|red",
  "explanation": "brief explanation"
}

**Thresholds:**
- GREEN: <10% overlap, no shared phrases of 5+ words
- YELLOW: 10-15% overlap or 1-2 shared phrases
- RED: >15% overlap or 3+ shared phrases

Return ONLY the JSON object.
```

### Template Variables

| Variable | Type | Description |
|----------|------|-------------|
| `generatedText` | `string` | The generated content (truncated to 2000 chars) |
| `sourceText` | `string` | The source material (truncated to 2000 chars) |

### Output Schema (Zod-validated)

```
{
  textualOverlapPercent: number (0-100),
  sharedPhrases: string[],
  verdict: "green" | "yellow" | "red",
  explanation: string
}
```

## CC-BY-SA Expression Check

This prompt specifically checks whether generated content contains **expression derived from CC-BY-SA licensed source material**. The distinction is critical: facts from CC-BY-SA sources are freely usable, but copied *expression* (sentence structure, word choices, phrasing) triggers license obligations.

**Source:** `copyright-check.ts` — `CC_BY_SA_CHECK_PROMPT` (lines 5–20)

```
Analyze whether the generated content below contains expression derived from CC-BY-SA source material.

PASS if: content expresses facts in completely original language
FAIL if: sentence structure, word choices, or phrasing mirrors the source

Generated Content:
---
{{generatedContent}}
---

Original Source Passage (CC-BY-SA):
---
{{sourcePassage}}
---

Respond with JSON: { "passed": boolean, "flagged_phrases": string[], "explanation": string }
```

### Template Variables

| Variable | Type | Description |
|----------|------|-------------|
| `{{generatedContent}}` | `string` | The generated content to check |
| `{{sourcePassage}}` | `string` | The original CC-BY-SA source passage |

Note that this prompt uses **mustache-style** `{{variable}}` placeholders rather than JavaScript template literal interpolation, indicating it is processed by a different template engine in the pipeline.

## Factual Verification Prompt

This prompt verifies the **factual accuracy** of generated content against structured source facts. It checks for eight categories of factual errors, from incorrect dates to numerical mistakes.

**Source:** `copyright-check.ts` — `FACTUAL_VERIFICATION_PROMPT` (lines 22–42)

```
Verify the factual accuracy of this content.

Check for:
1. Incorrect dates or attributions
2. Misattributed quotes
3. Wrong provenance claims
4. Anachronistic statements
5. Conflated facts from different sources
6. Unverifiable claims presented as fact
7. Names or titles with incorrect spelling
8. Numerical errors (dimensions, dates, quantities)

Content:
---
{{content}}
---

Source Facts:
{{factsJson}}

Respond with JSON: { "passed": boolean, "errors": [{ "claim": string, "issue": string, "severity": "critical"|"major"|"minor" }] }
```

### Template Variables

| Variable | Type | Description |
|----------|------|-------------|
| `{{content}}` | `string` | The generated content to verify |
| `{{factsJson}}` | `string` | Structured JSON of source facts to check against |

The error severity levels drive pipeline behavior:
- **critical** — content is blocked and must be rewritten
- **major** — content is flagged for human review
- **minor** — content is approved with a warning annotation

## Template Variables Summary

| Prompt | Input Variables | Output Format |
|--------|----------------|---------------|
| Copyright System Prompt | *(none — static system message)* | N/A (system context) |
| Copyright Assessment | generatedContent, sourceText, sourceLicense, sourceType, isMuseumDomain | Zod-validated JSON (verdict + action) |
| Similarity Check | generatedText, sourceText | Zod-validated JSON (overlap % + verdict) |
| CC-BY-SA Check | generatedContent, sourcePassage | JSON (passed + flagged phrases) |
| Factual Verification | content, factsJson | JSON (passed + error list) |

### LLM Assignment

| Prompt | Model | Rationale |
|--------|-------|-----------|
| Copyright Assessment | Claude Haiku 4.5 | Classification task, high throughput |
| Similarity Check | Claude Haiku 4.5 | Simple comparison, fast turnaround |
| CC-BY-SA Check | Claude Sonnet 4.5 | Nuanced expression analysis |
| Factual Verification | Claude Sonnet 4.5 | Requires careful reasoning about facts |

## Usage Context

### Pipeline Position

The copyright and compliance module operates at **Stage 3** in the content pipeline:

1. **Stage 1** — Intake (museum prompt + metadata)
2. **Stage 2** — Source Discovery + Deep Research
3. **Stage 2.5** — Discovery (IP Generation)
4. **Stage 3** — **Copyright Check (this module)** — legal compliance gate
5. **Stage 4** — Content Write
6. **Stage 5+** — QA, Deploy, Translation, Reporting

### How the Prompts Work Together

The five prompts form a **layered compliance system**:

1. The **Copyright System Prompt** sets the legal framework for all assessments
2. The **Copyright Assessment** prompt performs the primary check (generated vs. source)
3. The **Similarity Check** prompt provides quantitative overlap metrics
4. The **CC-BY-SA Check** catches expression leakage from Creative Commons sources
5. The **Factual Verification** prompt ensures accuracy without introducing fabricated claims

> Stage 3 is the legal gate that all content must pass through before it can be written into final audio guide scripts. A RED verdict from any check blocks the content and triggers rewriting. This is a non-negotiable part of the pipeline — no content reaches production without passing copyright clearance.
