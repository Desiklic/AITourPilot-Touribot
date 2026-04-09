# 20260406-content-write-system-prompt-v3

*Source: Business Wiki / prompts/content-pipeline-v3-henry/20260406-content-write-system-prompt-v3.html*

## Content Write System Prompt V3

**Version:** V3 — 7-Layer Narrative Architecture
**File:** `src/lib/prompts/content.ts` (`CONTENT_WRITE_SYSTEM_PROMPT`)

This system prompt governs ALL content generation in Stage 04. It instructs the LLM to write in Henry's voice with the 7-layer structure: Hook, Quick Identification, Visual Journey, Human Story, Deep Thread, Wonder Moment, Connection Thread.

### Key V3 Changes
- Added Content Layer Architecture block defining all 7 layers
- Tightened sentence length target (8-15 words)
- Layers use markdown headers for ElevenLabs RAG chunk boundaries
- Prose within each layer is flowing Henry narrative

See the full prompt in `src/lib/prompts/content.ts`.
