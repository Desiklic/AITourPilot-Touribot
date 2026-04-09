# 20260319-discovery-module-prompts-v1

*Source: Business Wiki / prompts/content-pipeline-v1/20260319-discovery-module-prompts-v1.html*

## Overview

The **Discovery Module** is part of **Stage 2.5** of the AI Tour Pilot content pipeline. It runs after initial research (Stage 2) and before the copyright check (Stage 3). Its purpose is to generate **proprietary intellectual property** — unique insights, narratives, and connections that cannot be found in any single source.

The module contains **four prompt templates**, each targeting a different kind of discovery:

| # | Prompt | Purpose |
|---|--------|---------|
| 1 | Hidden Connections | Find non-obvious links between museum entities |
| 2 | Emotional Narrative | Create emotionally resonant spoken stories per entity |
| 3 | Cross-Museum Synthesis | Generate cross-museum insights for shared figures |
| 4 | Archive Deep Dive | Uncover forgotten or overlooked stories |

All four prompts share common design principles:

- **JSON output** — every prompt requests structured JSON for downstream pipeline processing
- **Spoken delivery format** — narratives use second person, short sentences, and emotional pauses
- **Grounded claims** — every insight must cite a reasoning chain back to provided facts
- **Confidence scoring** — each result carries a high/medium/low confidence rating

> **Source file:** `src/lib/prompts/discovery.ts` in the AITourPilot-content-factory repository.

## Hidden Connections Prompt

This prompt discovers **non-obvious, hidden connections** between entities within a museum collection. It instructs the model to act as a world-class art historian and look for relationships that typical tours overlook.

**Source:** `discovery.ts` — `generateHiddenConnectionsPrompt()` (lines 23–55)

```
You are a world-class art historian researching ${museumName}. Analyze the entities and extracted facts below to find NON-OBVIOUS, HIDDEN CONNECTIONS between them.

Look for:
- Two artworks created in response to the same world event
- An architect mentored by the same teacher as an unrelated artist
- Materials sourced from the same quarry centuries apart
- Parallel innovations happening in different rooms of the museum
- Shared patrons, studios, or techniques across seemingly unrelated works
- Personal relationships (teacher-student, rivals, lovers, collaborators)

ENTITIES:
${entitiesBlock}

EXTRACTED FACTS:
${facts}

Every claim must be grounded in the provided facts. Include a reasoningChain explaining your derivation.

Return EXACTLY a JSON array of ${targetCount} connections (fewer if insufficient data). Each object must have:
{
  "title": "A compelling visitor-friendly title",
  "entityA": "Name of first entity",
  "entityB": "Name of second entity",
  "description": "2-3 sentences describing the connection, written for spoken delivery",
  "reasoningChain": "How you derived this connection from the facts",
  "confidence": "high" | "medium" | "low"
}

- "high": documented evidence directly supports the connection
- "medium": reasonable inference from available facts
- "low": creative speculation (use sparingly)

Return ONLY valid JSON array. Return empty array [] if fewer than 2 entities exist.
```

### Template Variables

| Variable | Type | Description |
|----------|------|-------------|
| `museumName` | `string` | Name of the museum being processed |
| `entitiesBlock` | `string` | Formatted list of entities (name, type, description) |
| `facts` | `string` | All extracted facts from the research stage |
| `targetCount` | `number` | Desired number of connections to generate |

## Emotional Narrative Prompt

This prompt generates **emotionally resonant stories** for individual entities. It offers five narrative approaches and lets the model choose the best fit. The output is designed for spoken audio delivery.

**Source:** `discovery.ts` — `generateEmotionalNarrativePrompt()` (lines 67–99)

```
You are a gifted museum storyteller. Create an emotionally resonant narrative for the following ${entityType}.

ENTITY: ${entityName}
DESCRIPTION: ${description}
FACTS:
${facts}

Pick ONE narrative approach (whichever fits best):
- **The Human Moment**: What was the creator feeling? What was at stake?
- **The Witness**: Who has stood before this piece and been changed by it?
- **The Conversation**: What would this piece say if it could speak to you right now?
- **The Weight of Time**: Why did this survive when so much else was lost? What does that say?
- **The Unseen**: What detail do most visitors walk past that changes everything once you notice it?

IMPORTANT: The narrative is for SPOKEN delivery (audio guide). Rules:
- Write in second person ("You are standing in front of...")
- Short sentences. Max 60 words per sentence.
- Mark emotional pauses with "..."
- No bullet points, no visual references, no lists.
- 150-300 words total.

Every claim must be grounded in the provided facts. Include a reasoningChain explaining your derivation.

Return EXACTLY one JSON object:
{
  "title": "Short evocative title (e.g. 'The Night Gaudi Couldn't Sleep')",
  "narrativeAngle": "Which approach you chose and why (1 sentence)",
  "fullNarrative": "The 150-300 word narrative for spoken delivery",
  "reasoningChain": "Why this angle was chosen for this entity",
  "confidence": "high" | "medium"
}

Return ONLY valid JSON.
```

### Template Variables

| Variable | Type | Description |
|----------|------|-------------|
| `entityName` | `string` | Name of the entity (artwork, building, figure, etc.) |
| `entityType` | `string` | Type classification (e.g. "painting", "sculpture", "architect") |
| `description` | `string` | Brief description of the entity |
| `facts` | `string` | Extracted facts relevant to this entity |

## Cross-Museum Synthesis Prompt

This prompt generates **cross-museum insights** for figures or artists that appear in multiple museum collections. It gives visitors "insider knowledge" connecting their current experience to the broader art world.

**Source:** `discovery.ts` — `generateCrossMuseumPrompt()` (lines 114–135)

```
You are a curator specializing in cross-museum narratives. The artist/figure "${personName}" appears in multiple museums.

AT ${thisMuseum.name} (current museum):
${thisMuseum.context}

AT OTHER MUSEUMS:
${otherMuseumsBlock}

What insight can you offer a visitor at ${thisMuseum.name} that draws on what we know from the other museums? The visitor should feel like they're getting insider knowledge that connects their experience here to the broader world.

Every claim must be grounded in the provided facts. Include a reasoningChain explaining your derivation.

Return EXACTLY one JSON object:
{
  "title": "A compelling title for the cross-museum insight",
  "description": "2-3 sentences explaining the connection",
  "visitorNarrative": "100-200 word spoken narrative a guide could share. Written for audio delivery: second person, short sentences, no bullet points.",
  "reasoningChain": "Evidence and logic for this connection",
  "confidence": "high" | "medium" | "low"
}

Return ONLY valid JSON.
```

### Template Variables

| Variable | Type | Description |
|----------|------|-------------|
| `personName` | `string` | Name of the shared artist or figure |
| `thisMuseum.name` | `string` | Name of the current museum |
| `thisMuseum.context` | `string` | Context about this person at the current museum |
| `otherMuseumsBlock` | `string` | Formatted list of other museums and their context |

## Archive Deep Dive Prompt

This prompt uncovers **forgotten or overlooked stories** within a museum's collection. It explicitly steers away from major highlights and searches for fascinating but typically missed narratives.

**Source:** `discovery.ts` — `generateArchiveDeepDivePrompt()` (lines 149–178)

```
You are a museum researcher at ${museumName} specializing in finding forgotten stories. Below are ALL extracted facts about this museum and its collection. Most tour guides focus on the major highlights listed below. Your job: find ${targetCount} stories that are fascinating but typically overlooked.

MAJOR HIGHLIGHTS (already well-covered):
${highlightsBlock}

ALL EXTRACTED FACTS:
${allFacts}

Look for:
- Construction mishaps or engineering feats
- Personal feuds between artists, architects, or patrons
- Near-destruction events (fires, wars, demolition plans)
- Bizarre coincidences or forgotten rituals
- Things that were hidden and discovered later
- Minor figures who played crucial roles

IMPORTANT: Stories must be grounded in the available facts. The reasoningChain must cite which facts support the story. Do NOT fabricate historical events. If the facts don't support interesting stories, return fewer discoveries rather than inventing fiction.

Every claim must be grounded in the provided facts. Include a reasoningChain explaining your derivation.

Return EXACTLY a JSON array of up to ${targetCount} objects (fewer if insufficient data). Each object must have:
{
  "title": "A compelling title for the forgotten story",
  "description": "1-2 sentence summary",
  "forgottenStory": "200-400 word narrative written for spoken delivery. Second person, short sentences, emotional pauses marked with '...'. No bullet points or visual references.",
  "reasoningChain": "Which facts support this story and how you connected them",
  "confidence": "high" | "medium" | "low"
}

Return ONLY valid JSON array.
```

### Template Variables

| Variable | Type | Description |
|----------|------|-------------|
| `museumName` | `string` | Name of the museum being processed |
| `highlightsBlock` | `string` | Formatted list of major highlights to avoid |
| `allFacts` | `string` | Complete set of extracted facts for the museum |
| `targetCount` | `number` | Maximum number of stories to discover |

## Template Variables Summary

All four prompts share a common pattern of injecting dynamic data via template variables. Here is the consolidated reference:

| Prompt | Input Variables | Output Format |
|--------|----------------|---------------|
| Hidden Connections | museumName, entities[], facts, targetCount | JSON array of connection objects |
| Emotional Narrative | entityName, entityType, facts, description | Single JSON object |
| Cross-Museum Synthesis | personName, thisMuseum, otherMuseums[] | Single JSON object |
| Archive Deep Dive | museumName, allFacts, majorHighlights[], targetCount | JSON array of story objects |

All outputs include:
- A human-readable **title**
- A **reasoningChain** grounding the claim in source facts
- A **confidence** score (high / medium / low)

## Usage Context

### Pipeline Position

The discovery module sits at **Stage 2.5** in the content pipeline:

1. **Stage 1** — Intake (museum prompt + metadata)
2. **Stage 2** — Source Discovery + Deep Research
3. **Stage 2.5** — **Discovery (this module)** — generates proprietary IP
4. **Stage 3** — Copyright Check
5. **Stage 4+** — Content Write, QA, Deploy

### Why This Matters

The discovery prompts are the primary mechanism for generating **original intellectual property**. While Stages 1-2 gather publicly available facts, Stage 2.5 synthesizes those facts into novel insights, narratives, and connections that:

- Cannot be found on Wikipedia or museum websites
- Are grounded in verifiable facts (not hallucinated)
- Are formatted for spoken audio delivery
- Carry confidence ratings for downstream quality filtering

> The content produced by these prompts is what makes AI Tour Pilot's guides genuinely unique — it is the core differentiator between our product and a simple text-to-speech reading of Wikipedia articles.
