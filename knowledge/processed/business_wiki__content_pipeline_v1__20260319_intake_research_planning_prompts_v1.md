# 20260319-intake-research-planning-prompts-v1

*Source: Business Wiki / prompts/content-pipeline-v1/20260319-intake-research-planning-prompts-v1.html*

## Overview

The Intake stage (Stage 1) is the entry point of the AI Tour Pilot content pipeline. It takes a museum name and basic metadata, runs a web search, and uses an LLM to produce a structured **Research Plan** -- a classified list of artifacts, people, and exhibitions that will guide all subsequent pipeline stages. This document contains the three prompts used in this stage.

**Source:** `src/lib/prompts/intake.ts`
**Pipeline Stage:** Stage 1 -- Intake
**LLM:** Claude (via Anthropic API)

## System Prompt

**Export:** `INTAKE_SYSTEM_PROMPT`

This system prompt establishes the LLM's role as a museum research planner. It is sent as the system message for both the initial intake and the top-up expansion calls.

```
You are a museum research planner for AITourPilot, a conversational AI audio guide system.

Your task is to analyze a museum and create a comprehensive Research Plan that will guide the content creation pipeline.

Key principles:
1. Identify the most important artifacts, people, and exhibitions that define this museum's character
2. Prioritize items that have compelling stories and are essential to understanding the museum
3. For experience-based museums (like architectural sites), focus on spaces, features, and the creator's vision
4. Estimate realistic scope based on museum size and type
5. Consider what would make the best conversational audio guide content
```

## Research Planning Prompt

**Function:** `generateIntakePrompt`

This is the main user prompt for initial museum intake. It receives museum metadata and web search results, and instructs the LLM to output a structured JSON Research Plan including classification, artifacts, people, exhibitions, and scope estimates.

```
# Museum Research Planning Task

## Museum Information
- Name: {{name}}
- Location: {{city}}, {{country}}
- Type: {{type}}
- Target piece count: {{targetPieceCount}}

{{specialInstructionsBlock}}

## Web Search Results
{{webSearchResults}}

## Your Task

Based on the museum information and web search results, create a comprehensive Research Plan.

**Output a JSON object with this exact structure:**

{
  "classification": {
    "confirmedType": "ART | TECHNICAL | HISTORY | NATURAL_HISTORY | EXPERIENCE | SPECIALIZED",
    "collectionSize": "large | medium | small | unknown",
    "displaySize": "estimated number or description",
    "personality": "brief character description (2-3 sentences)",
    "specialCharacteristics": ["unique feature 1", "unique feature 2", ...]
  },
  "researchPlan": {
    "artifacts": [
      {
        "name": "artifact name",
        "importance": "major | notable | standard",
        "reason": "why this is important to research",
        "artifactType": "painting | sculpture | drawing | print | photograph | installation | textile | ceramic | furniture | manuscript | instrument | architectural_feature | mixed_media | other",
        "yearCreated": "c. 1503 | 1889 | 15th century | 1920s | null if unknown",
        "medium": "Oil on canvas | Bronze | Marble | null if unknown"
      }
    ],
    "people": [
      {
        "name": "person name",
        "role": "artist | architect | curator | patron | inventor | etc",
        "importance": "major | notable | standard"
      }
    ],
    "exhibitions": [
      {
        "name": "exhibition or space name",
        "type": "permanent | temporary"
      }
    ],
    "estimatedScope": {
      "totalEntities": <number>,
      "estimatedTokens": <number>,
      "estimatedCostUsd": <number>
    }
  }
}

## Guidelines

**For Artifacts:**
- List {{targetPieceCount}} items (can be objects, artworks, machines, spaces, architectural features)
- Prioritize: major = signature pieces, notable = important supporting pieces, standard = contextual pieces
- For experience/architectural museums, treat spaces and features as "artifacts"
- For each artifact, provide:
  - artifactType: the classification (painting, sculpture, drawing, print, photograph, installation, textile, ceramic, furniture, manuscript, instrument, architectural_feature, mixed_media, or other)
  - yearCreated: creation date as text ("c. 1503", "1889", "15th century", "1920s") or null if unknown
  - medium: material/technique ("Oil on canvas", "Bronze", "Marble") or null if unknown

**For People:**
- Include creators, architects, key historical figures, major donors/patrons
- List 3-10 people depending on museum type
- Focus on those with rich biographical stories

**For Exhibitions:**
- List permanent exhibitions, major collections, or thematic spaces
- For experience museums, list key visitor routes or themed areas
- Aim for 3-8 exhibitions

**For Estimated Scope:**
- totalEntities: total of artifacts + people + exhibitions
- estimatedTokens: rough estimate (10K-50K tokens per entity depending on mode)
- estimatedCostUsd: rough cost estimate ($5-15 for Light, $10-30 for Standard, $20-60 for Full)

**Important:** Return ONLY the JSON object, no additional text or explanation.
```

> The `{{specialInstructionsBlock}}` is conditionally inserted when the operator provides special instructions. It overrides default assumptions in the Research Plan.

## Content Expansion Prompt

**Function:** `generateTopUpIntakePrompt`

This prompt is used when expanding an existing museum's content with additional artifacts. It includes an exclusion list of already-covered items to prevent duplication, and instructs the LLM to find complementary, lesser-known pieces.

```
# Museum Content Expansion Task

## Museum Information
- Name: {{name}}
- Location: {{city}}, {{country}}
- Type: {{type}}
- Target new pieces: {{additionalPieceCount}}

{{specialInstructionsBlock}}

## EXISTING Artifacts (DO NOT include any of these -- they are already covered)
{{exclusionBlock}}

## Web Search Results
{{webSearchResults}}

## Your Task

This museum already has content in our system. We want to EXPAND it with {{additionalPieceCount}} NEW artifacts that complement the existing collection coverage.

**Rules:**
1. Do NOT repeat any artifact from the exclusion list above
2. Focus on lesser-known, hidden gems, and complementary pieces
3. Think about what's missing -- different time periods, styles, or gallery areas not yet covered
4. For experience/architectural museums, consider spaces, features, or details not yet documented

**Output a JSON object with this exact structure:**

{
  "artifacts": [
    {
      "name": "artifact name",
      "importance": "major | notable | standard",
      "reason": "why this complements the existing content",
      "artifactType": "painting | sculpture | drawing | print | photograph | installation | textile | ceramic | furniture | manuscript | instrument | architectural_feature | mixed_media | other",
      "yearCreated": "c. 1503 | 1889 | 15th century | 1920s | null if unknown",
      "medium": "Oil on canvas | Bronze | Marble | null if unknown"
    }
  ]
}

## Guidelines

- List exactly {{additionalPieceCount}} NEW items (objects, artworks, machines, spaces, architectural features)
- Prioritize: major = signature pieces not yet covered, notable = important supporting pieces, standard = contextual pieces
- Each artifact name must be DIFFERENT from every item in the exclusion list above
- For experience/architectural museums, treat spaces and features as "artifacts"
- For each artifact, provide:
  - artifactType: the classification (painting, sculpture, drawing, print, photograph, installation, textile, ceramic, furniture, manuscript, instrument, architectural_feature, mixed_media, or other)
  - yearCreated: creation date as text ("c. 1503", "1889", "15th century", "1920s") or null if unknown
  - medium: material/technique ("Oil on canvas", "Bronze", "Marble") or null if unknown

**Important:** Return ONLY the JSON object, no additional text or explanation.
```

## Template Variables

| Variable | Prompt | Description |
|----------|--------|-------------|
| `{{name}}` | Both | Museum name |
| `{{city}}` | Both | City location |
| `{{country}}` | Both | Country location |
| `{{type}}` | Both | Museum type (ART, TECHNICAL, etc.) |
| `{{webSearchResults}}` | Both | Raw web search results text |
| `{{targetPieceCount}}` | Research Planning | Number of artifacts to identify (default: 20) |
| `{{specialInstructionsBlock}}` | Both | Optional operator instructions (conditionally inserted) |
| `{{additionalPieceCount}}` | Content Expansion | Number of new artifacts to add |
| `{{exclusionBlock}}` | Content Expansion | Formatted list of existing artifact names to skip |

## Usage Context

The intake prompts are called at the very beginning of the pipeline. The system prompt is shared across both the initial intake and the top-up flow. The Research Planning Prompt produces the master plan that drives Stage 2 (Deep Research) and all downstream stages. The Content Expansion Prompt is used for incremental museum updates -- adding new artifacts without re-running the full pipeline for already-covered content.
