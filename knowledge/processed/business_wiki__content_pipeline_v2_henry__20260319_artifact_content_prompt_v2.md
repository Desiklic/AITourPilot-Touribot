# 20260319-artifact-content-prompt-v2

*Source: Business Wiki / prompts/content-pipeline-v2-henry/20260319-artifact-content-prompt-v2.html*

## Overview

**V2 — Guided Seeing & Led Discovery.** This is the most important prompt revision. V1 structured artifact content as First Impression/Creation Story/Technical Details/Significance/Connection. V2 fundamentally restructures around **Guided Seeing** (directing the visitor's eye across the artwork) and **Led Discovery** (asking questions before revealing answers). The new structure follows the Schliesser model: what you see → what's hidden → the human story → the emotional revelation.

**Source:** `src/lib/prompts/content.ts`
**Export/Function:** `generateArtifactContentPrompt`
**Pipeline Stage:** Stage 4 — Content Write
**LLM:** Claude Sonnet 4.5
**Supersedes:** Artifact Content Prompt V1

## V1 → V2 Key Changes

| Aspect | V1 | V2 |
|--------|----|----|
| Opening | "First Impression — what catches your attention" | Guided Seeing — walk the visitor's eye across the work: colors, light, composition, textures |
| Discovery | Direct fact delivery | Led Discovery — ask questions before revealing: "Do you see the small mark near the edge?" |
| Technical details | Separate section | Woven into the visual journey — technique described through what you see |
| Voice | Generic conversational | Henry's personal wonder: "What I find most remarkable..." |
| Engagement | Not specified | Observational nudges and thought seeds (not questions); open-door invitations to go deeper |
| Structure | 5 sections (linear) | 6 sections (arc: see → discover → story → feel → invitation) |

## Full Prompt Text

```
# Artifact Content

Write audio guide content for **{{artifactName}}**{{descriptor}} at {{museumName}}. Write in Henry's voice — warm, personal, guiding the visitor to really see this piece.

## Available Facts
{{facts}}

## Content Requirements

**Target length:** {{targets.target}} characters (minimum {{targets.min}}, maximum {{targets.max}})
**Mode:** {{mode}}

**Structure your content as:**
1. **Guided Seeing** — Walk the visitor's eye across the artwork. Do not start with facts or history. Start with what they see RIGHT NOW. Use directional language: "Start at the hands. Look at how they're clasped — the knuckles white, the fingers intertwined." Move systematically: top to bottom, left to right, foreground to background — whatever serves this particular work. Describe colors, textures, light, composition, spatial relationships. Make the visitor notice what they would have walked past.
2. **The Hidden Detail** — Lead the visitor to discover something most people miss. Use an observational nudge, not a question: "See if you can spot the small figure in the background — most people walk right past it." or "Look at the bottom right corner. There's something there that changes everything about this painting." Then reveal the significance. This is the led discovery moment — guide the eye first, then fill in the meaning. The visitor does not need to speak.
3. **The Human Story** — Who made this, and what drove them? Not a biography dump, but the human moment behind the creation. What was the artist feeling? What was happening in their life? What was at stake? Tell it like Henry would — as a story, not a factsheet.
4. **What Makes This Special** — The technique, the innovation, the breakthrough — but described through what the visitor can see. "Look at how the light hits the left side of her face. Vermeer achieved this by..." Technical mastery explained through visible evidence.
5. **Why It Stays With You** — The emotional weight. Why does this piece matter? What does it do to people who stand before it? Henry's personal connection: "Every time I stand here, I notice something new..."
6. **Henry's Invitation** — End with an open door — an invitation to go deeper that does not require a verbal response. NOT a question. Instead, something like: "There's a fascinating story about how this painting almost never survived, if you'd like to hear it..." or "It makes you wonder what he was thinking in that moment." This creates a natural pause where dialogue CAN emerge — the visitor can speak, stay silent, or move on. All three are fine. Reserve genuine questions ("What strikes you most?") for at most one in every three to four artifacts.

**Remember:**
- Start with SEEING, not knowing. The visitor is standing in front of this piece right now.
- Every fact must come from the provided data
- Use sensory language: describe what the work looks like, feels like, what it evokes
- Use observational nudges ("See if you can spot...") and thought seeds ("It makes you wonder...") rather than direct questions. Visitors are in a quiet, shared space and may not want to speak aloud.
- Make technical details accessible through what's visually evident
- Henry has opinions and favorites — let his personality come through
- Write for audio delivery (conversational, warm, with natural pauses)

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
| `{{mode}}` | "light" \\| "standard" \\| "full" | Pipeline mode controlling content depth and length |

## Usage Context

This prompt is paired with the V2 `CONTENT_WRITE_SYSTEM_PROMPT` as the system message. The V2 version adds Guided Seeing as the mandatory first section, replacing the generic "First Impression." Led Discovery uses observational nudges and thought seeds rather than direct questions — visitors are in quiet, shared spaces and should not feel interrogated. "Henry's Invitation" replaces a mandatory closing question with an open-door pause point where dialogue can emerge naturally. The structure follows the arc model (see → discover → story → feel → invitation) rather than the linear model. Artifacts are the most numerous entity type — this prompt runs many times per pipeline and has the highest impact on the visitor experience.
