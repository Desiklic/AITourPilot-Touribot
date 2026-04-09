# 20260319-deep-research-stage-prompts-v1

*Source: Business Wiki / prompts/content-pipeline-v1/20260319-deep-research-stage-prompts-v1.html*

## Overview

Stage 2 (Deep Research) transforms the Research Plan from Stage 1 into structured facts, metadata, narrative content, and a completeness assessment. It runs four sequential sub-passes per entity, each with its own prompt. Together, these prompts extract raw facts from source material, classify artifact metadata, synthesize facts into audio-optimized narratives, and identify research gaps.

**Source:** `src/lib/prompts/research.ts`
**Pipeline Stage:** Stage 2 -- Deep Research
**LLM:** Claude (via Anthropic API)

## Fact Extraction Prompt

**Function:** `generateFactExtractionPrompt`
**Sub-pass:** Pass 1 -- Fact Extraction

This prompt takes raw source content about an entity and extracts every discrete factual claim as a structured JSON triple (subject-predicate-object) with confidence scoring.

```
# Fact Extraction Task

Extract structured facts from the following source content about **{{entityName}}** ({{entityType}}).

## Source Content

{{sourceContent}}

## Your Task

Extract all factual information as structured JSON. Focus on:
- **Dates**: creation dates, opening dates, birth/death dates, historical events
- **Names**: people, places, organizations mentioned
- **Dimensions**: physical measurements, quantities, capacities
- **Materials**: what things are made of, techniques used
- **Relationships**: connections between entities (created by, influenced by, contains, etc.)
- **Locations**: where things are, were created, or exist
- **Events**: what happened, when, and to whom

**Important:**
- Extract facts ONLY, not opinions or interpretations
- Each fact should be atomic (one single piece of information)
- If unsure about a fact, mark confidence as "low"
- Include the source quote if the fact comes directly from the text

Return a JSON object matching this structure:

{
  "facts": [
    {
      "type": "date|name|dimension|material|relationship|location|event|other",
      "subject": "what the fact is about",
      "predicate": "the property or relationship",
      "object": "the value",
      "confidence": "high|medium|low",
      "sourceQuote": "original text (optional)"
    }
  ]
}

Return ONLY the JSON object, no additional text.
```

## Artifact Metadata Prompt

**Function:** `generateArtifactMetadataPrompt`
**Sub-pass:** Pass 1b -- Artifact Metadata Extraction

After facts are extracted, this prompt classifies each artifact by type, creation date, and medium based solely on the extracted facts. It runs only for artifact entities.

```
# Artifact Metadata Classification

Given the following extracted facts about museum artifacts, determine the type, creation date, and medium for each artifact listed below.

## Artifacts to Classify
{{artifactList}}

## Available Facts
{{factsText}}

## Your Task

For each artifact, extract:
- **type**: The artwork classification. Use one of: painting, sculpture, drawing, print, photograph, installation, textile, ceramic, furniture, manuscript, instrument, architectural_feature, mixed_media, other. Use null ONLY if you truly cannot determine the type.
- **yearCreated**: The creation date as text (e.g., "c. 1503", "1889", "15th century", "1920s"). Use null if not mentioned in the facts.
- **medium**: The primary material/technique (e.g., "Oil on canvas", "Bronze", "Graphite on paper", "Watercolor on paper"). Use null if not mentioned in the facts.

**Important:**
- Only use information present in the provided facts -- do NOT guess or hallucinate
- If a fact mentions a date like "painted in 1889", set yearCreated to "1889"
- If multiple dates exist, use the creation/completion date, not exhibition dates
- confidence should reflect how certain the classification is based on available facts

Return a JSON object with an "artifacts" array containing one entry per artifact listed above.
```

## Cross-Reference Research Prompt

**Function:** `generateCrossReferencePrompt`
**Sub-pass:** Pass 2 -- Cross-Reference Research

This prompt takes the structured facts and synthesizes them into a cohesive, audio-optimized narrative. The target length scales with the pipeline mode (light / standard / full).

```
# Cross-Reference Research Task

Write a compelling, factual narrative about **{{entityName}}** ({{entityType}}) for an AI audio guide.

## Extracted Facts

{{facts}}

## Your Task

Write a {{targetLength}} narrative that:
1. Synthesizes the facts into a coherent, engaging story
2. Uses conversational, accessible language (avoid jargon)
3. Maintains factual accuracy - every statement should be grounded in the provided facts
4. Creates emotional connection while staying neutral and respectful
5. Is optimized for audio delivery (clear sentences, natural flow)

## Writing Guidelines

**Voice:**
- Conversational but not casual
- Educational but not academic
- Engaging but not sensational
- Respectful of all cultures and perspectives

**Structure:**
- Start with the most interesting or important aspect
- Build context progressively
- Use natural transitions between ideas
- End with something memorable

**Audio Optimization:**
- Short to medium sentences (10-20 words average)
- Avoid complex subordinate clauses
- Spell out numbers under 100, use digits sparingly
- No visual-only references ("as you can see")

**Factual Grounding:**
- Only use information from the provided facts
- If facts are limited, write what you can verify
- Don't make assumptions or add creative embellishments

Write the narrative now. Return ONLY the narrative text, no additional formatting or commentary.
```

> The `{{targetLength}}` variable is determined by pipeline mode: "2-3 paragraphs (300-500 words)" for light, "4-6 paragraphs (600-1000 words)" for standard, and "8-12 paragraphs (1200-2000 words)" for full.

## Gap Analysis Prompt

**Function:** `generateGapAnalysisPrompt`
**Sub-pass:** Pass 4 -- Gap Analysis

After all entities have been researched, this prompt evaluates overall completeness. It receives a summary of every entity's fact count and content length, and returns a prioritized list of gaps with recommended actions.

```
# Gap Analysis Task

Analyze the research completeness for the following entities:

{{entitiesList}}

## Completeness Criteria

For **{{pipelineMode}}** mode:
- Minimum facts per entity: {{minFactsPerEntity}}
- Minimum content length: {{minContentLength}} characters

## Your Task

Identify gaps in the research and prioritize follow-up actions.

Return a JSON object matching this structure:

{
  "gaps": [
    {
      "entityName": "name of entity with gap",
      "entityType": "museum|artifact|person|exhibition",
      "gapType": "missing_dates|missing_materials|insufficient_content|missing_context|missing_relationships",
      "description": "describe the gap",
      "priority": "critical|important|nice_to_have",
      "suggestedAction": "what to do about it"
    }
  ],
  "overallCompleteness": <0-100>,
  "criticalGapsCount": <number>,
  "recommendation": "overall assessment and next steps"
}

Return ONLY the JSON object, no additional text.
```

> Minimum thresholds scale with pipeline mode: light requires 5 facts / 300 chars, standard requires 10 facts / 600 chars, and full requires 15 facts / 1200 chars per entity.

## Template Variables

| Variable | Prompt | Description |
|----------|--------|-------------|
| `{{entityName}}` | Fact Extraction, Cross-Reference | Name of the entity being researched |
| `{{entityType}}` | Fact Extraction, Cross-Reference, Gap Analysis | Type: museum, artifact, person, or exhibition |
| `{{sourceContent}}` | Fact Extraction | Raw text from web sources |
| `{{artifactList}}` | Artifact Metadata | Numbered list of artifact names |
| `{{factsText}}` | Artifact Metadata | Formatted extracted facts |
| `{{facts}}` | Cross-Reference | Structured facts as text |
| `{{targetLength}}` | Cross-Reference | Word count target based on pipeline mode |
| `{{entitiesList}}` | Gap Analysis | Summary of all entities with fact/content counts |
| `{{pipelineMode}}` | Gap Analysis | "light", "standard", or "full" |
| `{{minFactsPerEntity}}` | Gap Analysis | Minimum fact threshold (5 / 10 / 15) |
| `{{minContentLength}}` | Gap Analysis | Minimum character threshold (300 / 600 / 1200) |

## Usage Context

These four prompts are called sequentially for each entity in the Research Plan. Fact Extraction runs first on every source document, then Artifact Metadata classifies the items, Cross-Reference synthesizes facts into narratives, and finally Gap Analysis evaluates overall coverage. The outputs feed directly into Stage 3 (Copyright Check) and Stage 4 (Content Write). The structured fact triples also serve as the provenance chain -- every claim in the final audio guide can be traced back to its source quote.
