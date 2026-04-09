# 20260406-content-rewrite-voice-prompts-v3

*Source: Business Wiki / prompts/content-pipeline-v3-henry/20260406-content-rewrite-voice-prompts-v3.html*

## Content Rewrite & Voice Prompts V3

**Version:** V3
**File:** `src/lib/prompts/rewrite.ts` (LEGACY — not imported)

### Status: Dead Code

The Phase 2 research confirmed that `rewrite.ts` is not imported by any pipeline stage. The `CONTENT_GENERATION_PROMPT` and `VOICE_OPTIMIZATION_PROMPT` it contains are unused.

Voice optimization in V3 happens through:
1. **The system prompt in `content.ts`** — instructs the LLM to write in Henry's voice during content generation
2. **Deterministic post-processing** — `optimizeForVoice()` in `04-content-write.ts` applies string transforms (abbreviation expansion, number formatting, whitespace cleanup)

No LLM-based rewrite pass exists. The voice quality is baked into the initial generation via the V3 system prompt's 7-layer architecture.

### Recommendation
This file can be archived or deleted in a future cleanup. It is not touched by V3 to avoid unnecessary risk.
